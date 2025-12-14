"""
Gestión de proyectos - crear, actualizar, listar
"""

import os
import json
from datetime import datetime
from .config import PROYECTOS_DIR


def generar_nombre_proyecto(tema: str) -> str:
    """
    Genera un nombre de proyecto limpio basado en el tema.

    Args:
        tema: Tema o título del proyecto

    Returns:
        Nombre del proyecto con timestamp
    """
    tema_limpio = "".join(c if c.isalnum() or c == " " else "" for c in tema[:40])
    tema_limpio = tema_limpio.strip().replace(" ", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{tema_limpio}_{timestamp}"


def crear_estructura_proyecto(nombre_proyecto: str) -> dict:
    """
    Crea la estructura de carpetas para un nuevo proyecto.

    Args:
        nombre_proyecto: Nombre del proyecto

    Returns:
        Diccionario con las rutas del proyecto
    """
    proyecto_dir = os.path.join(PROYECTOS_DIR, nombre_proyecto)

    rutas = {
        "raiz": proyecto_dir,
        "guion": os.path.join(proyecto_dir, "guion"),
        "audio": os.path.join(proyecto_dir, "audio"),
        "imagenes": os.path.join(proyecto_dir, "imagenes"),
        "video": os.path.join(proyecto_dir, "video"),
    }

    for ruta in rutas.values():
        os.makedirs(ruta, exist_ok=True)

    return rutas


def crear_metadata_proyecto(rutas: dict, tema: str, config: dict) -> str:
    """
    Crea el archivo proyecto.json con la metadata del proyecto.

    Args:
        rutas: Diccionario con las rutas del proyecto
        tema: Tema del proyecto
        config: Configuración (palabras, voz, segundos_por_imagen)

    Returns:
        Ruta del archivo proyecto.json
    """
    metadata = {
        "nombre": os.path.basename(rutas["raiz"]),
        "tema": tema,
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "estado": "iniciado",
        "configuracion": config,
        "archivos": {"guion": None, "audio": None, "imagenes": [], "video": None},
        "youtube": {"subido": False, "url": None, "privacidad": None},
    }

    metadata_path = os.path.join(rutas["raiz"], "proyecto.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return metadata_path


def actualizar_metadata_proyecto(rutas: dict, actualizaciones: dict):
    """
    Actualiza el archivo proyecto.json con nuevos datos.

    Args:
        rutas: Diccionario con las rutas del proyecto
        actualizaciones: Diccionario con los campos a actualizar
    """
    metadata_path = os.path.join(rutas["raiz"], "proyecto.json")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    def actualizar_dict(original, updates):
        for key, value in updates.items():
            if isinstance(value, dict) and key in original:
                actualizar_dict(original[key], value)
            else:
                original[key] = value

    actualizar_dict(metadata, actualizaciones)

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def cargar_proyecto(nombre_proyecto: str) -> tuple:
    """
    Carga un proyecto existente.

    Args:
        nombre_proyecto: Nombre del proyecto a cargar

    Returns:
        Tupla con (metadata, rutas)
    """
    proyecto_dir = os.path.join(PROYECTOS_DIR, nombre_proyecto)
    metadata_path = os.path.join(proyecto_dir, "proyecto.json")

    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"No se encontró el proyecto: {nombre_proyecto}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    rutas = {
        "raiz": proyecto_dir,
        "guion": os.path.join(proyecto_dir, "guion"),
        "audio": os.path.join(proyecto_dir, "audio"),
        "imagenes": os.path.join(proyecto_dir, "imagenes"),
        "video": os.path.join(proyecto_dir, "video"),
    }

    return metadata, rutas


def listar_proyectos() -> list:
    """
    Lista todos los proyectos existentes.

    Returns:
        Lista de diccionarios con info de cada proyecto
    """
    if not os.path.exists(PROYECTOS_DIR):
        return []

    proyectos = []
    for nombre in os.listdir(PROYECTOS_DIR):
        proyecto_dir = os.path.join(PROYECTOS_DIR, nombre)
        metadata_path = os.path.join(proyecto_dir, "proyecto.json")

        if os.path.isdir(proyecto_dir) and os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                proyectos.append(
                    {
                        "nombre": nombre,
                        "tema": metadata.get("tema", "Sin tema"),
                        "estado": metadata.get("estado", "desconocido"),
                        "fecha": metadata.get("fecha_creacion", ""),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue

    # Ordenar por fecha (más reciente primero)
    proyectos.sort(key=lambda x: x["fecha"], reverse=True)
    return proyectos
