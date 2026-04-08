import sys

from PySide6.QtWidgets import QApplication

from gestion_academica.views.ventana_principal import VentanaPrincipal


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ventana = VentanaPrincipal()
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
