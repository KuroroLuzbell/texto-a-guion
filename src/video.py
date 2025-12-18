"""
Creación de video con FFmpeg
"""

import os
import json
import random
import subprocess
from .audio import obtener_duracion_audio


# Ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cargar_config_videos() -> dict:
    """Carga la configuración de videos base."""
    config_path = os.path.join(BASE_DIR, "config_videos.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "carpeta_videos": "videos_base",
        "categorias": {},
        "categoria_default": "paisaje",
        "modo_seleccion": "aleatorio"
    }


def obtener_video_base(categoria: str = None) -> str:
    """
    Obtiene un video base según la categoría.
    
    Args:
        categoria: Nombre de la categoría (ej: 'paisaje', 'terror')
                  Si es None, usa la categoría default
    
    Returns:
        Ruta completa al video seleccionado
    """
    config = cargar_config_videos()
    carpeta = os.path.join(BASE_DIR, config["carpeta_videos"])
    
    # Usar categoría default si no se especifica
    if categoria is None:
        categoria = config.get("categoria_default", "paisaje")
    
    # Obtener archivos de la categoría
    if categoria in config.get("categorias", {}):
        archivos = config["categorias"][categoria].get("archivos", [])
    else:
        # Si no existe la categoría, buscar todos los mp4 en la carpeta
        archivos = [f for f in os.listdir(carpeta) if f.endswith(".mp4")]
    
    if not archivos:
        raise RuntimeError(f"No se encontraron videos en la categoría '{categoria}'")
    
    # Seleccionar según modo
    modo = config.get("modo_seleccion", "aleatorio")
    if modo == "aleatorio":
        archivo = random.choice(archivos)
    else:
        archivo = archivos[0]
    
    video_path = os.path.join(carpeta, archivo)
    
    if not os.path.exists(video_path):
        raise RuntimeError(f"Video no encontrado: {video_path}")
    
    return video_path


def listar_videos_disponibles() -> dict:
    """Lista todos los videos disponibles por categoría."""
    config = cargar_config_videos()
    carpeta = os.path.join(BASE_DIR, config["carpeta_videos"])
    
    resultado = {}
    for cat_nombre, cat_info in config.get("categorias", {}).items():
        archivos = cat_info.get("archivos", [])
        existentes = [f for f in archivos if os.path.exists(os.path.join(carpeta, f))]
        resultado[cat_nombre] = {
            "descripcion": cat_info.get("descripcion", ""),
            "total": len(existentes),
            "archivos": existentes
        }
    
    return resultado


def crear_video_con_loop(video_base: str, audio_path: str, output_path: str) -> str:
    """
    Crea un video repitiendo el video base hasta cubrir la duración del audio.
    
    Args:
        video_base: Ruta del video base a repetir (loop)
        audio_path: Ruta del archivo de audio
        output_path: Ruta donde guardar el video final
    
    Returns:
        Ruta del video generado
    """
    if not verificar_ffmpeg():
        raise RuntimeError(
            "FFmpeg no está instalado. Instálalo con:\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu: sudo apt install ffmpeg\n"
            "  Windows: choco install ffmpeg"
        )
    
    if not os.path.exists(video_base):
        raise RuntimeError(f"Video base no encontrado: {video_base}")
    
    if not os.path.exists(audio_path):
        raise RuntimeError(f"Audio no encontrado: {audio_path}")
    
    duracion_audio = obtener_duracion_audio(audio_path)
    print(f"   📹 Video base: {os.path.basename(video_base)}")
    print(f"   🔊 Duración del audio: {duracion_audio:.1f}s")
    
    # Comando FFmpeg para loop del video + audio
    # -stream_loop -1: repite el video infinitamente
    # -shortest: corta cuando termina el audio
    cmd = [
        "ffmpeg",
        "-y",  # Sobrescribir sin preguntar
        "-stream_loop", "-1",  # Loop infinito del video
        "-i", video_base,  # Video de entrada
        "-i", audio_path,  # Audio de entrada
        "-map", "0:v",  # Usar video del primer input
        "-map", "1:a",  # Usar audio del segundo input
        "-c:v", "libx264",  # Codec de video
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",  # Codec de audio
        "-b:a", "192k",
        "-shortest",  # Terminar cuando acabe el audio
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    
    try:
        print("   🔄 Procesando video con loop...")
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"   ✅ Video generado: {os.path.basename(output_path)}")
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error al crear video con FFmpeg: {e.stderr}") from e


def crear_video_desde_audio(audio_path: str, output_path: str, categoria: str = None) -> str:
    """
    Crea un video usando un video base en loop + el audio proporcionado.
    
    Args:
        audio_path: Ruta del archivo de audio
        output_path: Ruta donde guardar el video final
        categoria: Categoría de video a usar (ej: 'paisaje')
    
    Returns:
        Ruta del video generado
    """
    video_base = obtener_video_base(categoria)
    return crear_video_con_loop(video_base, audio_path, output_path)


def verificar_ffmpeg() -> bool:
    """Verifica si FFmpeg está instalado."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def crear_video(imagenes: list, audio_path: str, output_path: str) -> str:
    """
    Crea un video a partir de imágenes y audio usando FFmpeg.

    Args:
        imagenes: Lista de rutas de imágenes
        audio_path: Ruta del archivo de audio
        output_path: Ruta donde guardar el video

    Returns:
        Ruta del video generado
    """
    if not verificar_ffmpeg():
        raise RuntimeError(
            "FFmpeg no está instalado. Instálalo con:\n"
            "  macOS: brew install ffmpeg\n"
            "  Ubuntu: sudo apt install ffmpeg\n"
            "  Windows: choco install ffmpeg"
        )

    imagenes_validas = [img for img in imagenes if img and os.path.exists(img)]

    if not imagenes_validas:
        raise RuntimeError("No hay imágenes válidas para crear el video")

    duracion_audio = obtener_duracion_audio(audio_path)
    duracion_por_imagen = duracion_audio / len(imagenes_validas)

    print(f"   Duración del audio: {duracion_audio:.1f}s")
    print(f"   Imágenes: {len(imagenes_validas)}")
    print(f"   Duración por imagen: {duracion_por_imagen:.1f}s")

    # Construir los inputs de imágenes
    inputs = []
    filter_parts = []

    for i, img in enumerate(imagenes_validas):
        inputs.extend(["-loop", "1", "-t", str(duracion_por_imagen), "-i", img])
        fade_out = duracion_por_imagen - 0.5
        filter_parts.append(
            f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"fade=t=in:st=0:d=0.5,fade=t=out:st={fade_out}:d=0.5[v{i}]"
        )

    concat_inputs = "".join([f"[v{i}]" for i in range(len(imagenes_validas))])
    filter_complex = (
        ";".join(filter_parts)
        + f";{concat_inputs}concat=n={len(imagenes_validas)}:v=1:a=0[outv]"
    )

    audio_index = len(imagenes_validas)

    cmd = [
        "ffmpeg",
        "-y",
        *inputs,
        "-i",
        audio_path,
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-map",
        f"{audio_index}:a",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error al crear video con FFmpeg: {e.stderr}") from e


def crear_video_desde_proyecto(rutas: dict) -> str:
    """
    Crea el video usando los archivos del proyecto.

    Args:
        rutas: Diccionario con las rutas del proyecto

    Returns:
        Ruta del video generado
    """
    # Buscar imágenes
    imagenes = []
    imagenes_dir = rutas["imagenes"]
    if os.path.exists(imagenes_dir):
        for archivo in sorted(os.listdir(imagenes_dir)):
            if archivo.endswith((".png", ".jpg", ".jpeg")):
                imagenes.append(os.path.join(imagenes_dir, archivo))

    # Buscar audio
    audio_path = os.path.join(rutas["audio"], "narracion.wav")
    if not os.path.exists(audio_path):
        raise RuntimeError("No se encontró el archivo de audio")

    # Ruta de salida
    output_path = os.path.join(rutas["video"], "video_final.mp4")

    return crear_video(imagenes, audio_path, output_path)
