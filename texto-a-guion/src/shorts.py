"""
Extractor de Shorts desde videos de YouTube
"""

import os
import re
import json
import subprocess
import tempfile
import base64
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from google.genai import types

from .config import obtener_modelo, PROYECTOS_DIR


def extraer_video_id(url: str) -> str:
    """
    Extrae el ID del video de una URL de YouTube.

    Args:
        url: URL del video de YouTube

    Returns:
        ID del video
    """
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError(f"No se pudo extraer el ID del video de: {url}")


def obtener_transcripcion(video_id: str, idiomas: list = None) -> list:
    """
    Obtiene la transcripción de un video de YouTube.

    Args:
        video_id: ID del video
        idiomas: Lista de idiomas preferidos (default: ['es', 'en'])

    Returns:
        Lista de segmentos con 'text', 'start', 'duration'
    """
    if idiomas is None:
        idiomas = ["es", "en"]

    # Crear instancia de la API (nueva versión)
    ytt_api = YouTubeTranscriptApi()

    try:
        transcript = ytt_api.fetch(video_id, languages=idiomas)
        # Convertir a lista de diccionarios
        return [
            {"text": item.text, "start": item.start, "duration": item.duration}
            for item in transcript
        ]
    except NoTranscriptFound:
        # Intentar obtener cualquier transcripción disponible
        try:
            transcript_list = ytt_api.list(video_id)
            # Buscar transcripción generada automáticamente
            for transcript in transcript_list:
                fetched = transcript.fetch()
                return [
                    {"text": item.text, "start": item.start, "duration": item.duration}
                    for item in fetched
                ]
        except Exception as e:
            raise RuntimeError(f"No se encontró transcripción: {e}") from e
    except TranscriptsDisabled as exc:
        raise RuntimeError(
            "Las transcripciones están deshabilitadas para este video"
        ) from exc
    except Exception as e:
        raise RuntimeError(f"Error al obtener transcripción: {e}") from e


def formatear_transcripcion(transcript: list) -> str:
    """
    Formatea la transcripción con timestamps para el análisis.

    Args:
        transcript: Lista de segmentos de transcripción

    Returns:
        Texto formateado con timestamps
    """
    lines = []
    for seg in transcript:
        tiempo = seg["start"]
        minutos = int(tiempo // 60)
        segundos = int(tiempo % 60)
        timestamp = f"[{minutos:02d}:{segundos:02d}]"
        lines.append(f"{timestamp} {seg['text']}")

    return "\n".join(lines)


def analizar_momentos_virales(client, transcripcion: str, num_shorts: int = 3) -> list:
    """
    Usa Gemini para analizar la transcripción y encontrar momentos virales.

    Args:
        client: Cliente de Gemini
        transcripcion: Transcripción formateada con timestamps
        num_shorts: Número de shorts a generar

    Returns:
        Lista de diccionarios con los clips sugeridos
    """
    prompt = f"""Eres un experto en contenido viral de YouTube Shorts. Analiza esta transcripción y encuentra los {num_shorts} mejores momentos para crear Shorts virales.

TRANSCRIPCIÓN:
{transcripcion}

CRITERIOS PARA SELECCIONAR MOMENTOS:
1. Ganchos impactantes que capturen atención en 2 segundos
2. Datos sorprendentes o contraintuitivos
3. Momentos emocionales o dramáticos
4. Frases memorables o quotes potentes
5. Revelaciones o plot twists
6. Contenido que genere curiosidad

REGLAS:
- Cada clip debe durar entre 30 y 60 segundos
- El inicio debe ser un gancho fuerte (no puede empezar aburrido)
- Debe tener sentido por sí solo (no requerir contexto previo)

Responde ÚNICAMENTE con un JSON válido, sin texto adicional:

{{
  "shorts": [
    {{
      "numero": 1,
      "timestamp_inicio": "MM:SS",
      "timestamp_fin": "MM:SS",
      "titulo_sugerido": "Título viral y clickbait (máx 50 chars)",
      "descripcion": "Breve descripción del contenido",
      "gancho": "La frase de gancho de los primeros 3 segundos",
      "porque_es_viral": "Por qué este momento funcionará como Short"
    }}
  ]
}}"""

    try:
        response = client.models.generate_content(
            model=obtener_modelo("texto"), contents=prompt
        )
        texto = response.text.strip()

        # Limpiar marcadores de código
        if texto.startswith("```json"):
            texto = texto[7:]
        if texto.startswith("```"):
            texto = texto[3:]
        if texto.endswith("```"):
            texto = texto[:-3]

        resultado = json.loads(texto.strip())
        return resultado.get("shorts", [])

    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error al parsear respuesta de Gemini: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Error al analizar momentos: {e}") from e


def timestamp_a_segundos(timestamp: str) -> float:
    """Convierte timestamp MM:SS a segundos."""
    partes = timestamp.split(":")
    if len(partes) == 2:
        return int(partes[0]) * 60 + int(partes[1])
    elif len(partes) == 3:
        return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2])
    return 0


def descargar_clip(url: str, inicio: str, fin: str, output_path: str) -> str:
    """
    Descarga un segmento específico del video.

    Args:
        url: URL del video
        inicio: Timestamp de inicio (MM:SS)
        fin: Timestamp de fin (MM:SS)
        output_path: Ruta de salida

    Returns:
        Ruta del archivo descargado
    """
    # Convertir timestamps
    inicio_sec = timestamp_a_segundos(inicio)
    fin_sec = timestamp_a_segundos(fin)

    # Formato para yt-dlp
    section = f"*{inicio_sec}-{fin_sec}"

    cmd = [
        "yt-dlp",
        "--download-sections",
        section,
        "-f",
        "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format",
        "mp4",
        "-o",
        output_path,
        "--no-playlist",
        url,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error al descargar clip: {e.stderr}") from e


def convertir_a_vertical(
    input_path: str, output_path: str, metodo: str = "blur"
) -> str:
    """
    Convierte un video horizontal (16:9) a vertical (9:16).

    Args:
        input_path: Ruta del video horizontal
        output_path: Ruta de salida
        metodo: 'blur' (fondo difuminado) o 'crop' (recortar centro)

    Returns:
        Ruta del video convertido
    """
    if metodo == "blur":
        # Video pequeño arriba con fondo blur
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
            "split[fg][bg];"
            "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=20:20[blurred];"
            "[blurred][fg]overlay=(W-w)/2:(H-h)/2"
        )
    else:  # crop
        # Recortar el centro
        filter_complex = "scale=1920:1080,crop=607:1080:(in_w-607)/2:0,scale=1080:1920"

    cmd = [
        "ffmpeg",
        "-i",
        input_path,
        "-filter_complex",
        filter_complex,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-y",
        output_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error al convertir video: {e.stderr}") from e


def extraer_frames(video_path: str, num_frames: int = 5) -> list:
    """
    Extrae frames del video para análisis.

    Args:
        video_path: Ruta del video
        num_frames: Número de frames a extraer

    Returns:
        Lista de rutas de frames
    """
    temp_dir = tempfile.mkdtemp()

    # Obtener duración del video
    cmd_duration = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd_duration, capture_output=True, text=True)
    duration = float(result.stdout.strip())

    frames = []
    interval = duration / (num_frames + 1)

    for i in range(1, num_frames + 1):
        timestamp = interval * i
        frame_path = os.path.join(temp_dir, f"frame_{i:02d}.jpg")

        cmd = [
            "ffmpeg",
            "-ss",
            str(timestamp),
            "-i",
            video_path,
            "-vframes",
            "1",
            "-q:v",
            "2",
            "-y",
            frame_path,
        ]
        subprocess.run(cmd, capture_output=True)

        if os.path.exists(frame_path):
            frames.append(frame_path)

    return frames


def analizar_posicion_sujeto(client, frames: list) -> dict:
    """
    Usa Gemini para analizar los frames y detectar la posición del sujeto.

    Args:
        client: Cliente de Gemini
        frames: Lista de rutas de frames

    Returns:
        Diccionario con la posición recomendada del crop
    """
    # Codificar frames en base64
    images_data = []
    for frame_path in frames[:3]:  # Usar máximo 3 frames para no exceder límites
        with open(frame_path, "rb") as f:
            image_bytes = f.read()
            images_data.append(
                {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode(),
                }
            )

    prompt = """Analiza estas imágenes de un video. Necesito convertir este video de formato horizontal (16:9) a vertical (9:16).

Identifica dónde está el sujeto principal o punto de interés en las imágenes.

Responde ÚNICAMENTE con un JSON:
{
  "posicion_horizontal": "izquierda" | "centro" | "derecha",
  "hay_persona": true | false,
  "descripcion": "breve descripción de qué hay en el video"
}

Si hay una persona hablando, indica dónde está. Si no hay persona clara, indica dónde está la acción principal."""

    try:
        # Construir el contenido con imágenes
        contents = [prompt]
        for img in images_data:
            contents.append(
                types.Part.from_bytes(
                    data=base64.b64decode(img["data"]), mime_type=img["mime_type"]
                )
            )

        response = client.models.generate_content(
            model=obtener_modelo("texto"), contents=contents
        )

        texto = response.text.strip()
        if texto.startswith("```json"):
            texto = texto[7:]
        if texto.startswith("```"):
            texto = texto[3:]
        if texto.endswith("```"):
            texto = texto[:-3]

        resultado = json.loads(texto.strip())

        # Asegurar que sea un diccionario
        if isinstance(resultado, list):
            resultado = resultado[0] if resultado else {}
        if not isinstance(resultado, dict):
            resultado = {"posicion_horizontal": "centro", "hay_persona": False}

        return resultado

    except Exception as e:
        print(f"      ⚠️ Error analizando frames: {e}")
        return {"posicion_horizontal": "centro", "hay_persona": False}


def convertir_a_vertical_smart(client, input_path: str, output_path: str) -> str:
    """
    Convierte video a vertical usando IA para detectar el sujeto.

    Args:
        client: Cliente de Gemini
        input_path: Ruta del video horizontal
        output_path: Ruta de salida

    Returns:
        Ruta del video convertido
    """
    print("      🧠 Analizando contenido del video con IA...")

    # 1. Extraer frames
    frames = extraer_frames(input_path, num_frames=3)

    if not frames:
        print("      ⚠️ No se pudieron extraer frames, usando crop centro")
        return convertir_a_vertical(input_path, output_path, "crop")

    # 2. Analizar con Gemini
    analisis = analizar_posicion_sujeto(client, frames)
    print(
        f"      📍 Posición detectada: {analisis.get('posicion_horizontal', 'centro')}"
    )
    if analisis.get("descripcion"):
        print(f"      📝 Contenido: {analisis['descripcion'][:60]}...")

    # 3. Calcular crop basado en posición
    posicion = analisis.get("posicion_horizontal", "centro")

    # Para video 1920x1080 → queremos 607px de ancho para 9:16
    # crop=607:1080:X:0 donde X depende de la posición
    if posicion == "izquierda":
        crop_x = "0"  # Empezar desde la izquierda
    elif posicion == "derecha":
        crop_x = "in_w-607"  # Desde la derecha
    else:  # centro
        crop_x = "(in_w-607)/2"  # Centro

    filter_complex = f"scale=1920:1080:force_original_aspect_ratio=increase,crop=607:1080:{crop_x}:0,scale=1080:1920"

    cmd = [
        "ffmpeg",
        "-i",
        input_path,
        "-vf",
        filter_complex,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-y",
        output_path,
    ]

    # Limpiar frames temporales
    for frame in frames:
        try:
            os.remove(frame)
            os.rmdir(os.path.dirname(frame))
        except:
            pass

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error al convertir video: {e.stderr}") from e


def crear_estructura_shorts(video_id: str) -> dict:
    """
    Crea la estructura de carpetas para el proyecto de shorts.

    Args:
        video_id: ID del video de YouTube

    Returns:
        Diccionario con las rutas
    """
    from .config import BASE_DIR

    # Carpeta shorts al mismo nivel que proyectos
    shorts_base_dir = os.path.join(BASE_DIR, "shorts")
    proyecto_dir = os.path.join(shorts_base_dir, f"shorts_{video_id}")

    rutas = {
        "base": proyecto_dir,
        "clips_originales": os.path.join(proyecto_dir, "clips_originales"),
        "shorts": os.path.join(proyecto_dir, "shorts"),
    }

    for ruta in rutas.values():
        os.makedirs(ruta, exist_ok=True)

    return rutas


def generar_shorts_desde_url(
    client, url: str, num_shorts: int = 3, metodo_conversion: str = "blur"
) -> dict:
    """
    Flujo completo: URL → Shorts listos.

    Args:
        client: Cliente de Gemini
        url: URL del video de YouTube
        num_shorts: Número de shorts a generar
        metodo_conversion: 'blur' o 'crop'

    Returns:
        Diccionario con resultados
    """
    print("\n📱 GENERADOR DE SHORTS DESDE YOUTUBE")
    print("=" * 50)

    # 1. Extraer video ID
    print("\n🔗 Extrayendo ID del video...")
    video_id = extraer_video_id(url)
    print(f"   ID: {video_id}")

    # 2. Crear estructura
    print("\n📁 Creando estructura de carpetas...")
    rutas = crear_estructura_shorts(video_id)
    print(f"   Carpeta: {rutas['base']}")

    # 3. Obtener transcripción
    print("\n📝 Obteniendo transcripción...")
    try:
        transcript = obtener_transcripcion(video_id)
        print(f"   ✅ {len(transcript)} segmentos obtenidos")
    except RuntimeError as e:
        print(f"   ❌ {e}")
        return {"error": str(e)}

    # 4. Formatear transcripción
    transcripcion_formateada = formatear_transcripcion(transcript)

    # 5. Analizar con Gemini
    print(f"\n🧠 Analizando contenido para encontrar {num_shorts} momentos virales...")
    try:
        momentos = analizar_momentos_virales(
            client, transcripcion_formateada, num_shorts
        )
        print(f"   ✅ {len(momentos)} momentos identificados")
    except RuntimeError as e:
        print(f"   ❌ {e}")
        return {"error": str(e)}

    # 6. Mostrar momentos encontrados
    print("\n📋 MOMENTOS VIRALES DETECTADOS:")
    print("-" * 50)
    for i, momento in enumerate(momentos, 1):
        print(f"\n   🎬 Short #{i}")
        print(f"      ⏱️  {momento['timestamp_inicio']} → {momento['timestamp_fin']}")
        print(f"      📌 {momento['titulo_sugerido']}")
        print(f'      🎯 Gancho: "{momento["gancho"]}"')
        print(f"      💡 {momento['porque_es_viral']}")

    # 7. Confirmar antes de descargar
    print("\n" + "-" * 50)
    confirmar = input("¿Descargar y procesar estos clips? (s/n) > ").strip().lower()
    if confirmar != "s":
        print("❌ Operación cancelada")
        return {"momentos": momentos, "cancelado": True}

    # 8. Descargar y convertir cada clip
    shorts_generados = []

    for i, momento in enumerate(momentos, 1):
        print(f"\n🎬 Procesando Short #{i}...")

        # Descargar clip original
        clip_original = os.path.join(
            rutas["clips_originales"], f"clip_{i:02d}_original.mp4"
        )
        print(
            f"   📥 Descargando clip {momento['timestamp_inicio']}-{momento['timestamp_fin']}..."
        )

        try:
            descargar_clip(
                url,
                momento["timestamp_inicio"],
                momento["timestamp_fin"],
                clip_original,
            )
            print("   ✅ Clip descargado")
        except RuntimeError as e:
            print(f"   ❌ Error: {e}")
            continue

        # Convertir a vertical
        nombre_safe = re.sub(r"[^\w\s-]", "", momento["titulo_sugerido"])[:30]
        short_final = os.path.join(rutas["shorts"], f"short_{i:02d}_{nombre_safe}.mp4")

        print(f"   📱 Convirtiendo a formato vertical ({metodo_conversion})...")
        try:
            if metodo_conversion == "smart":
                convertir_a_vertical_smart(client, clip_original, short_final)
            else:
                convertir_a_vertical(clip_original, short_final, metodo_conversion)
            print("   ✅ Short generado")
            shorts_generados.append(
                {
                    "archivo": short_final,
                    "titulo": momento["titulo_sugerido"],
                    "descripcion": momento["descripcion"],
                }
            )
        except RuntimeError as e:
            print(f"   ❌ Error: {e}")
            continue

    # 9. Guardar metadata
    metadata = {
        "video_id": video_id,
        "url_original": url,
        "momentos_detectados": momentos,
        "shorts_generados": shorts_generados,
    }

    metadata_path = os.path.join(rutas["base"], "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # 10. Resumen final
    print("\n" + "=" * 50)
    print("✅ SHORTS GENERADOS")
    print("=" * 50)
    print(f"\n📁 Ubicación: {rutas['shorts']}")
    print(f"📊 Shorts creados: {len(shorts_generados)}/{len(momentos)}")

    for short in shorts_generados:
        print(f"\n   🎬 {os.path.basename(short['archivo'])}")
        print(f"      📌 {short['titulo']}")

    return {
        "rutas": rutas,
        "momentos": momentos,
        "shorts": shorts_generados,
        "metadata_path": metadata_path,
    }
