"""
Módulos del Generador de Videos para YouTube con Gemini
"""

from .config import (
    configurar_gemini,
    cargar_estructura,
    PROYECTOS_DIR,
    BASE_DIR,
    cargar_modelos,
    obtener_modelo,
    obtener_opciones_modelos,
    guardar_modelos,
    MODELOS,
)
from .proyecto import (
    generar_nombre_proyecto,
    crear_estructura_proyecto,
    crear_metadata_proyecto,
    actualizar_metadata_proyecto,
    cargar_proyecto,
    listar_proyectos,
)
from .guion import generar_guion, guardar_guion, mostrar_guion, extraer_texto_narracion
from .audio import (
    generar_audio, 
    obtener_duracion_audio,
    mostrar_opciones_estilo,
    obtener_estilo,
    obtener_voz_recomendada,
    aplicar_estilo_texto,
    ESTILOS_NARRACION,
)
from .imagenes import generar_imagenes
from .video import (
    crear_video,
    verificar_ffmpeg,
    crear_video_con_loop,
    crear_video_desde_audio,
    obtener_video_base,
    listar_videos_disponibles,
    cargar_config_videos,
)
from .youtube import subir_video_youtube
from .shorts import generar_shorts_desde_url, extraer_video_id, obtener_transcripcion

__all__ = [
    # Config
    "configurar_gemini",
    "cargar_estructura",
    "PROYECTOS_DIR",
    "BASE_DIR",
    "cargar_modelos",
    "obtener_modelo",
    "obtener_opciones_modelos",
    "guardar_modelos",
    "MODELOS",
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
    "mostrar_opciones_estilo",
    "obtener_estilo",
    "obtener_voz_recomendada",
    "aplicar_estilo_texto",
    "ESTILOS_NARRACION",
    # Imagenes
    "generar_imagenes",
    # Video
    "crear_video",
    "verificar_ffmpeg",
    "crear_video_con_loop",
    "crear_video_desde_audio",
    "obtener_video_base",
    "listar_videos_disponibles",
    "cargar_config_videos",
    # YouTube
    "subir_video_youtube",
    # Shorts
    "generar_shorts_desde_url",
    "extraer_video_id",
    "obtener_transcripcion",
]
