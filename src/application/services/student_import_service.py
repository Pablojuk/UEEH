"""Servicio de importación de estudiantes desde Excel/CSV."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.services.student_service import StudentService
from src.infrastructure.importers.excel_students_importer import ExcelStudentsImporter


@dataclass
class ImportPreview:
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
            return ImportPreview(rows=[], mapping={}, errors=["No se encontraron filas de datos"]) 

        mapping, mapping_errors = self._detect_mapping(raw_rows[0].keys())
        if mapping_errors:
            return ImportPreview(rows=[], mapping=mapping, errors=mapping_errors)

        normalized_rows = [self._normalize_row(row, mapping) for row in raw_rows]
        cleaned_rows = [row for row in normalized_rows if row.get("nombres") and row.get("apellidos")]

        return ImportPreview(rows=cleaned_rows, mapping=mapping, errors=[])

    def import_file(self, file_path: str) -> dict:
        preview = self.generate_preview(file_path)
        summary = {
            "total_leidos": len(preview.rows),
            "validos": 0,
            "importados": 0,
            "omitidos": 0,
            "duplicados": 0,
            "errores": list(preview.errors),
        }

        if preview.errors:
            return summary

        for row in preview.rows:
            summary["validos"] += 1
            try:
                created, message = self.student_service.crear_estudiante(row)
                if created:
                    summary["importados"] += 1
                else:
                    summary["omitidos"] += 1
                    if "Duplicado" in message:
                        summary["duplicados"] += 1
                    summary["errores"].append(message)
            except Exception as exc:  # noqa: BLE001
                summary["omitidos"] += 1
                summary["errores"].append(str(exc))

        return summary

    @staticmethod
    def _detect_mapping(columns: list[str] | tuple[str, ...] | object) -> tuple[dict[str, str], list[str]]:
        aliases = {
            "nombres": {"nombres", "nombre", "estudiante", "nombre_estudiante"},
            "apellidos": {"apellidos", "apellido", "apellidos_estudiante"},
            "identificacion": {"cedula", "identificacion", "dni"},
            "codigo": {"codigo", "codigo_estudiante"},
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
            return text or None

        return {
            "nombres": value("nombres") or "",
            "apellidos": value("apellidos") or "",
            "identificacion": value("identificacion"),
            "codigo": value("codigo"),
            "curso": value("curso"),
            "paralelo": value("paralelo"),
        }
