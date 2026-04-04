"""Pruebas de importación de estudiantes."""

from __future__ import annotations

import csv
import os
import tempfile
import unittest

from src.application.services.student_import_service import StudentImportService
from src.application.services.student_service import StudentService
from src.infrastructure.persistence.db import initialize_database


class TestStudentImportService(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = tmp.name
        tmp.close()
        self.connection = initialize_database(self.db_path)
        self.student_service = StudentService(self.connection)
        self.import_service = StudentImportService(self.student_service)

    def tearDown(self) -> None:
        self.connection.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_csv(self, headers: list[str], rows: list[list[str]]) -> str:
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", newline="", encoding="utf-8")
        writer = csv.writer(tmp)
        writer.writerow(headers)
        writer.writerows(rows)
        tmp.close()
        return tmp.name

    def test_detecta_columnas_validas(self) -> None:
        path = self._create_csv(["nombres", "apellidos", "cedula"], [["Ana", "Perez", "123"]])
        preview = self.import_service.generate_preview(path)
        self.assertFalse(preview.errors)
        self.assertEqual(len(preview.rows), 1)
        os.remove(path)

    def test_rechaza_estructura_invalida(self) -> None:
        path = self._create_csv(["foo", "bar"], [["x", "y"]])
        preview = self.import_service.generate_preview(path)
        self.assertTrue(preview.errors)
        os.remove(path)

    def test_importacion_con_duplicados(self) -> None:
        path = self._create_csv(
            ["nombres", "apellidos", "identificacion"],
            [["Ana", "Perez", "123"], ["Ana", "Perez", "123"]],
        )
        result = self.import_service.import_file(path)
        self.assertEqual(result["importados"], 1)
        self.assertEqual(result["duplicados"], 1)
        os.remove(path)

    def test_importacion_valida_sin_codigo_estudiante(self) -> None:
        path = self._create_csv(["nombres", "apellidos"], [["Luis", "Mora"]])
        result = self.import_service.import_file(path)
        self.assertEqual(result["importados"], 1)
        os.remove(path)
