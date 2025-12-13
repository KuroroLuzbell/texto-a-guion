"""
Configuración y conexión con APIs
"""

import os
import json
from dotenv import load_dotenv
import google.genai as genai

# Rutas base
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROYECTOS_DIR = os.path.join(BASE_DIR, "proyectos")


def configurar_gemini():
    """
    Configura la API de Gemini con la clave de entorno.

    Returns:
        Cliente de Gemini configurado
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "No se encontró la API key. "
            "Asegúrate de crear un archivo .env con GEMINI_API_KEY=tu_clave"
        )

    client = genai.Client(api_key=api_key)
    return client


def cargar_estructura():
    """
    Carga la estructura del guión desde el archivo de configuración.

    Returns:
        Diccionario con la estructura del guión
    """
    config_path = os.path.join(BASE_DIR, "config_estructura.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"No se encontró el archivo de configuración: {config_path}"
        ) from exc
    except json.JSONDecodeError as e:
        raise ValueError(f"Error al parsear el archivo de configuración: {e}") from e
