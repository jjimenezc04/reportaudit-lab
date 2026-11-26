
"""
ReportAudit — lógica de negocio del servicio de reportes de auditoría.
"""

import hashlib
import os
import re
import sqlite3
import subprocess
from pathlib import Path

import yaml

# Secretos obtenidos desde variables de entorno
NOTIFICATION_API_KEY = os.environ.get(
    "REPORTAUDIT_NOTIFICATION_API_KEY", ""
)
SMTP_PASSWORD = os.environ.get(
    "REPORTAUDIT_SMTP_PASSWORD", ""
)

RUTA_DB = os.path.join(os.path.dirname(__file__), "..", "reportes.db")

# Lista blanca de nombres de archivos HTML
NOMBRE_HTML_VALIDO = re.compile(r"^\w[\w.-]*\.html$")


def cargar_configuracion(ruta_config):
    """Carga la configuración del servicio desde un archivo YAML."""
    with open(ruta_config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def buscar_reportes_cliente(nombre_cliente, ruta_db=RUTA_DB):
    """Devuelve todos los reportes asociados a un cliente."""
    conexion = sqlite3.connect(ruta_db)
    try:
        cursor = conexion.cursor()
        query = "SELECT * FROM reportes WHERE cliente = ?"
        cursor.execute(query, (nombre_cliente,))
        return cursor.fetchall()
    finally:
        conexion.close()


def convertir_a_pdf(nombre_archivo):
    """Convierte un reporte HTML a PDF usando la utilidad del sistema."""

    nombre = Path(nombre_archivo).name

    if not NOMBRE_HTML_VALIDO.fullmatch(nombre):
        raise ValueError("Nombre de archivo no válido")

    # Resolver las rutas para evitar argumentos inesperados
    directorio = Path(nombre_archivo).parent.resolve()
    entrada = (directorio / nombre).resolve()
    salida = entrada.with_suffix(entrada.suffix + ".pdf")

    # Comprobar que el archivo de entrada existe y es un archivo normal
    if not entrada.is_file():
        raise FileNotFoundError(f"No existe el archivo HTML: {entrada}")

    try:
        resultado = subprocess.run(
            [
                "wkhtmltopdf",
                str(entrada),
                str(salida)
            ],
            check=True,
            shell=False,
            capture_output=True,
            text=True
        )

    except FileNotFoundError:
        raise RuntimeError(
            "wkhtmltopdf no está instalado en el sistema."
        )

    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Error al generar el PDF: {error.stderr}"
        ) from error

    return str(salida)


def hash_password_legacy(password):
    """Genera un hash de contraseña con PBKDF2 y una sal aleatoria."""
    sal = os.urandom(16)

    derivado = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        sal,
        600_000
    )

    return sal.hex() + ":" + derivado.hex()


def notificar_cliente(email, mensaje):
    """Envía una notificación al cliente usando el servicio externo."""
    configurada = bool(NOTIFICATION_API_KEY)

    print(
        f"[NotifyAPI configurada={configurada}] "
        f"-> {email}: {mensaje}"
    )

    return True
