"""Worker asíncrono para el envío de correos electrónicos de recuperación."""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from PySide6.QtCore import QThread, Signal

# ==============================================================================
# CONFIGURACIÓN SMTP (Modificar para producción)
# ==============================================================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # SSL Estándar
SMTP_USER = "soporte.ueeh@gmail.com"       # <-- Cuenta emisora de soporte
SMTP_PASSWORD = "aaaa-bbbb-cccc-dddd"       # <-- Contraseña de aplicación de Gmail / Servidor
# ==============================================================================


class EmailSendWorker(QThread):
    """Hilo secundario para enviar correos SMTP sin congelar la interfaz."""

    success = Signal(str)
    failure = Signal(str)

    def __init__(self, recipient_email: str, new_password: str, parent=None) -> None:
        super().__init__(parent)
        self.recipient_email = recipient_email
        self.new_password = new_password

    def run(self) -> None:
        if not self.recipient_email:
            self.failure.emit("No se ha registrado ningún correo de recuperación.")
            return

        subject = "Recuperación de Clave Maestra - Sistema Académico UEEH"
        body = (
            "Estimado Docente,\n\n"
            "Se ha solicitado la recuperación de su contraseña de acceso al Sistema Académico UEEH.\n"
            "Por motivos de seguridad (PBKDF2-HMAC), no es posible desencriptar su clave anterior.\n\n"
            "Se ha generado la siguiente clave maestra temporal de acceso:\n"
            f"-->  {self.new_password}  <--\n\n"
            "Inicie sesión con esta nueva clave y, si lo desea, cámbiela desde el menú de Configuración.\n\n"
            "Atentamente,\n"
            "Soporte de Sistemas UEEH"
        )

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = self.recipient_email

        try:
            # Conexión SSL segura a través del puerto 465
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, self.recipient_email, msg.as_string())
            
            self.success.emit(f"Correo de recuperación enviado con éxito a: {self.recipient_email}")
        except smtplib.SMTPAuthenticationError:
            self.failure.emit("Fallo de autenticación en el servidor de correo. Revise credenciales SMTP.")
        except smtplib.SMTPConnectError:
            self.failure.emit("No se pudo establecer conexión con el servidor de correo. Revise host/puerto.")
        except Exception as e:
            self.failure.emit(f"Error de red al enviar el correo: {str(e)}")
