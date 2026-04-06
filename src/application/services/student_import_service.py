"""Servicio de importación de estudiantes desde Excel/CSV."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from src.application.services.student_service import StudentService
from src.infrastructure.importers.excel_students_importer import ExcelStudentsImporter


@dataclass
class ImportPreview:
    raw_total: int
    rows: list[dict]
    mapping: dict[str, str]
    errors: list[str]


class StudentImportService:
    def __init__(self, student_service: StudentService, importer: ExcelStudentsImporter | None = None) -> None:
        self.student_service = student_service
        self.importer = importer or ExcelStudentsImporter()

    def generate_preview(self, file_path: str) -> ImportPreview:
        raw_rows = self.importer.read_rows(file_path)
        if not raw_rows:
            return ImportPreview(raw_total=0, rows=[], mapping={}, errors=["No se encontraron filas de datos"])

        mapping, mapping_errors = self._detect_mapping(raw_rows[0].keys())
        if mapping_errors:
            return ImportPreview(raw_total=len(raw_rows), rows=[], mapping=mapping, errors=mapping_errors)

        normalized_rows = [self._normalize_row(row, mapping) for row in raw_rows]
        cleaned_rows = [row for row in normalized_rows if row.get("nombres") and row.get("apellidos")]

        return ImportPreview(raw_total=len(raw_rows), rows=cleaned_rows, mapping=mapping, errors=[])

    def import_file(self, file_path: str) -> dict:
        preview = self.generate_preview(file_path)
        summary = {
            "total_leidos": preview.raw_total,
            "validos": 0,
            "importados": 0,
            "omitidos": 0,
            "duplicados": 0,
            "errores": list(preview.errors),
        }

        if preview.errors:
            return summary

        identificaciones_archivo: set[str] = set()
        codigos_archivo: set[str] = set()

        for index, row in enumerate(preview.rows, start=2):
            summary["validos"] += 1
            identificacion = row.get("identificacion")
            codigo = row.get("codigo")
            if identificacion and identificacion in identificaciones_archivo:
                summary["omitidos"] += 1
                summary["duplicados"] += 1
                summary["errores"].append(f"Fila {index}: Duplicado por identificación dentro del archivo")
                continue
            if codigo and codigo in codigos_archivo:
                summary["omitidos"] += 1
                summary["duplicados"] += 1
                summary["errores"].append(f"Fila {index}: Duplicado por código dentro del archivo")
                continue
            try:
                created, message = self.student_service.crear_estudiante(row)
                if created:
                    summary["importados"] += 1
                    if identificacion:
                        identificaciones_archivo.add(identificacion)
                    if codigo:
                        codigos_archivo.add(codigo)
                else:
                    summary["omitidos"] += 1
                    if "Duplicado" in message:
                        summary["duplicados"] += 1
                    summary["errores"].append(f"Fila {index}: {message}")
            except Exception as exc:  # noqa: BLE001
                summary["omitidos"] += 1
                error_text = str(exc).lower()
                if isinstance(exc, sqlite3.IntegrityError) and "estudiantes.codigo" in error_text:
                    summary["duplicados"] += 1
                    summary["errores"].append(f"Fila {index}: Duplicado por código")
                    continue
                if isinstance(exc, sqlite3.IntegrityError) and "estudiantes.identificacion" in error_text:
                    summary["duplicados"] += 1
                    summary["errores"].append(f"Fila {index}: Duplicado por identificación")
                    continue
                summary["errores"].append(f"Fila {index}: {exc}")

        return summary

    @staticmethod
    def _detect_mapping(columns: list[str] | tuple[str, ...] | object) -> tuple[dict[str, str], list[str]]:
        aliases = {
            "nombres": {"nombres", "nombre", "estudiante", "nombre_estudiante"},
            "apellidos": {"apellidos", "apellido", "apellidos_estudiante"},
            "identificacion": {"cedula", "cédula", "identificacion", "identificación", "dni"},
            "codigo": {"codigo", "codigo_estudiante", "codigo estudiante"},
            "curso": {"curso"},
            "paralelo": {"paralelo"},
        }

        normalized = {str(col).strip().lower(): str(col) for col in columns}
        mapping: dict[str, str] = {}

        for target, options in aliases.items():
            for option in options:
                if option in normalized:
                    mapping[target] = normalized[option]
                    break

        errors: list[str] = []
        if "nombres" not in mapping:
            errors.append("No se detectó columna de nombres")
        if "apellidos" not in mapping:
            errors.append("No se detectó columna de apellidos")

        return mapping, errors

    @staticmethod
    def _normalize_row(raw: dict, mapping: dict[str, str]) -> dict:
        def value(key: str) -> str | None:
            source = mapping.get(key)
            if not source:
                return None
            raw_value = raw.get(source)
            if raw_value is None:
                return None
            text = str(raw_value).strip()
            if not text or text.lower() in {"nan", "none", "null"}:
                return None
            if text.endswith(".0"):
                base = text[:-2]
                if base.isdigit():
                    text = base
            return text

        return {
            "nombres": value("nombres") or "",
            "apellidos": value("apellidos") or "",
            "identificacion": value("identificacion"),
            "codigo": value("codigo"),
            "curso": value("curso"),
            "paralelo": value("paralelo"),
        }
