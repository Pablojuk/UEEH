"""Utilidades de seguridad para manejo de clave maestra."""

from __future__ import annotations

import hashlib
import hmac
import secrets


PBKDF2_ITERATIONS = 120_000
KEY_LENGTH = 32
ALGORITHM = "sha256"


def generar_salt(longitud: int = 16) -> str:
    """Genera un salt aleatorio en formato hexadecimal."""
    if longitud <= 0:
        raise ValueError("La longitud del salt debe ser mayor a cero")
    return secrets.token_hex(longitud)


def hash_clave(clave: str, salt_hex: str, iteraciones: int = PBKDF2_ITERATIONS) -> str:
    """Genera hash PBKDF2-HMAC de una clave usando salt hexadecimal."""
    if not clave:
        raise ValueError("La clave no puede estar vacía")
    if not salt_hex:
        raise ValueError("El salt no puede estar vacío")

    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac(
        ALGORITHM,
        clave.encode("utf-8"),
        salt,
        iteraciones,
        dklen=KEY_LENGTH,
    )
    return digest.hex()


def verificar_clave(
    clave_plana: str,
    salt_hex: str,
    hash_esperado: str,
    iteraciones: int = PBKDF2_ITERATIONS,
) -> bool:
    """Verifica una clave plana contra hash esperado en tiempo constante."""
    hash_calculado = hash_clave(clave_plana, salt_hex, iteraciones=iteraciones)
    return hmac.compare_digest(hash_calculado, hash_esperado)
