"""Pruebas para servicios de aplicación de institución, docentes y catálogos."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.application.services.catalog_service import CatalogService
from src.application.services.institution_service import InstitutionService
from src.application.services.teacher_service import TeacherService
from src.infrastructure.persistence.db import initialize_database


class TestApplicationServices(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = tmp.name
        tmp.close()
        self.connection = initialize_database(self.db_path)

        self.institution_service = InstitutionService(self.connection)
        self.teacher_service = TeacherService(self.connection)
        self.catalog_service = CatalogService(self.connection)

    def tearDown(self) -> None:
        self.connection.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_institucion_crear_y_leer(self) -> None:
        self.institution_service.crear_o_actualizar("UEEH", "Matutina")
        inst = self.institution_service.obtener_actual()

        self.assertIsNotNone(inst)
        self.assertEqual(inst["nombre"], "UEEH")
        self.assertEqual(inst["jornada"], "Matutina")

    def test_docentes_crear_listar_actualizar_activar_inactivar(self) -> None:
        self.teacher_service.crear_docente(
            {
                "id_docente": "D1",
                "nombres": "Ana",
                "apellidos": "Perez",
                "identificacion": "123",
            }
        )

        docentes = self.teacher_service.listar_docentes()
        self.assertEqual(len(docentes), 1)
        self.assertEqual(docentes[0]["id_docente"], "D1")

        self.teacher_service.actualizar_docente("D1", {"nombres": "Ana Maria"})
        docente = self.teacher_service.obtener_docente("D1")
        self.assertEqual(docente["nombres"], "Ana Maria")

        self.teacher_service.inactivar_docente("D1")
        docente = self.teacher_service.obtener_docente("D1")
        self.assertEqual(docente["activo"], 0)

        self.teacher_service.activar_docente("D1")
        docente = self.teacher_service.obtener_docente("D1")
        self.assertEqual(docente["activo"], 1)

    def test_catalogos_crear_y_listar(self) -> None:
        self.catalog_service.crear_curso(
            {"id_curso": "C1", "nombre": "Primero", "nivel": "Basica"}
        )
        self.catalog_service.crear_paralelo({"id_paralelo": "P1", "nombre": "A"})
        self.catalog_service.crear_asignatura(
            {"id_asignatura": "A1", "nombre": "Matemática", "codigo": "MAT"}
        )
        self.catalog_service.crear_periodo_lectivo(
            {
                "id_periodo": "2025-2026",
                "anio_inicio": 2025,
                "anio_fin": 2026,
                "fecha_inicio": None,
                "fecha_fin": None,
            }
        )

        self.assertEqual(len(self.catalog_service.listar_cursos()), 1)
        self.assertEqual(len(self.catalog_service.listar_paralelos()), 1)
        self.assertEqual(len(self.catalog_service.listar_asignaturas()), 1)
        self.assertEqual(len(self.catalog_service.listar_periodos_lectivos()), 1)

    def test_docentes_importa_id_y_identificacion_texto(self) -> None:
        csv_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8", newline="")
        try:
            csv_file.write("ID docente,nombres,apellidos,cedula\n")
            csv_file.write("DOC-001,Ana,Perez,105370365\n")
            csv_file.close()
            result = self.teacher_service.importar_desde_excel(csv_file.name)
            self.assertEqual(result["importados"], 1)
            docente = self.teacher_service.obtener_docente("DOC-001")
            self.assertIsNotNone(docente)
            self.assertEqual(docente["identificacion"], "0105370365")
        finally:
            path = Path(csv_file.name)
            if path.exists():
                path.unlink()


if __name__ == "__main__":
    unittest.main()
