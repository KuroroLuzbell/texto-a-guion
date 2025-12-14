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

# Modelos por defecto (se sobrescriben con config_modelos.json)
MODELOS = {
    "texto": "gemini-2.5-flash",
    "tts": "gemini-2.5-flash-preview-tts",
    "imagen": "imagen-4.0-generate-001",
}


def cargar_modelos():
    """
    Carga la configuración de modelos desde el archivo JSON.

    Returns:
        Diccionario con los modelos configurados
    """
    global MODELOS
    config_path = os.path.join(BASE_DIR, "config_modelos.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            MODELOS = {
                "texto": config["modelos"]["texto"]["modelo"],
                "tts": config["modelos"]["tts"]["modelo"],
                "imagen": config["modelos"]["imagen"]["modelo"],
            }
    except FileNotFoundError:
        print("⚠️  No se encontró config_modelos.json, usando modelos por defecto")

    return MODELOS


def obtener_modelo(tipo: str) -> str:
    """
    Obtiene el nombre del modelo para un tipo específico.

    Args:
        tipo: Tipo de modelo ('texto', 'tts', 'imagen')

    Returns:
        Nombre del modelo configurado
    """
    return MODELOS.get(tipo, "")


def obtener_opciones_modelos() -> dict:
    """
    Obtiene las opciones disponibles de modelos.

    Returns:
        Diccionario con las opciones disponibles para cada tipo
    """
    config_path = os.path.join(BASE_DIR, "config_modelos.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("opciones_disponibles", {})
    except FileNotFoundError:
        return {
            "texto": ["gemini-2.5-flash"],
            "tts": ["gemini-2.5-flash-preview-tts"],
            "imagen": ["imagen-4.0-generate-001"],
        }


def guardar_modelos(modelos: dict):
    """
    Guarda la configuración de modelos en el archivo JSON.

    Args:
        modelos: Diccionario con los modelos a guardar
    """
    global MODELOS
    config_path = os.path.join(BASE_DIR, "config_modelos.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"modelos": {}, "opciones_disponibles": {}}

    # Actualizar modelos
    for tipo, modelo in modelos.items():
        if tipo in config["modelos"]:
            config["modelos"][tipo]["modelo"] = modelo
        else:
            config["modelos"][tipo] = {"modelo": modelo, "descripcion": ""}

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    MODELOS.update(modelos)


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
