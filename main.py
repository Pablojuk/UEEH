import sys
from PySide6.QtWidgets import QApplication
from views.ventana_principal import VentanaPrincipal


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
