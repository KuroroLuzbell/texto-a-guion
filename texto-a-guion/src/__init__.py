"""
Módulos del Generador de Videos para YouTube con Gemini
"""

from .config import configurar_gemini, cargar_estructura, PROYECTOS_DIR, BASE_DIR
from .proyecto import (
    generar_nombre_proyecto,
    crear_estructura_proyecto,
    crear_metadata_proyecto,
    actualizar_metadata_proyecto,
    cargar_proyecto,
    listar_proyectos,
)
from .guion import generar_guion, guardar_guion, mostrar_guion, extraer_texto_narracion
from .audio import generar_audio, obtener_duracion_audio
from .imagenes import generar_imagenes
from .video import crear_video, verificar_ffmpeg
from .youtube import subir_video_youtube

__all__ = [
    # Config
    "configurar_gemini",
    "cargar_estructura",
    "PROYECTOS_DIR",
    "BASE_DIR",
    # Proyecto
    "generar_nombre_proyecto",
    "crear_estructura_proyecto",
    "crear_metadata_proyecto",
    "actualizar_metadata_proyecto",
    "cargar_proyecto",
    "listar_proyectos",
    # Guion
    "generar_guion",
    "guardar_guion",
    "mostrar_guion",
    "extraer_texto_narracion",
    # Audio
    "generar_audio",
    "obtener_duracion_audio",
    # Imagenes
    "generar_imagenes",
    # Video
    "crear_video",
    "verificar_ffmpeg",
    # YouTube
    "subir_video_youtube",
]
