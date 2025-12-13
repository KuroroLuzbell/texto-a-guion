"""
Creación de video con FFmpeg
"""

import os
import subprocess
from .audio import obtener_duracion_audio


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
