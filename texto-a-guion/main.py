"""
Generador de Guiones y Videos para YouTube con Google Gemini
=============================================================
Este script genera guiones estructurados para videos de YouTube
basados en un tema proporcionado por el usuario.
Incluye:
- Generación de guiones con Gemini
- Audio con Gemini TTS (voz de IA de Google)
- Imágenes con Imagen 4.0
- Video final con FFmpeg
- Publicación automática en YouTube
"""

import os
import json
import wave
import subprocess
import base64
import pickle
import httplib2
from datetime import datetime
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes necesarios para YouTube
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def configurar_gemini():
    """Configura la API de Gemini con la clave de entorno."""
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
    """Carga la estructura del guión desde el archivo de configuración."""
    config_path = os.path.join(os.path.dirname(__file__), "config_estructura.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"No se encontró el archivo de configuración: {config_path}"
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Error al parsear el archivo de configuración: {e}")


def generar_guion(client, tema: str, cantidad_palabras: int, estructura: dict) -> dict:
    """
    Genera un guión estructurado basado en el tema proporcionado.

    Args:
        client: Cliente de Gemini configurado
        tema: El tema o texto base para el guión
        cantidad_palabras: Número aproximado de palabras para el guión
        estructura: Diccionario con la estructura del guión

    Returns:
        El guión generado como diccionario JSON
    """

    # Construir la descripción de las secciones
    secciones_desc = []
    for seccion in estructura["estructura_guion"]:
        secciones_desc.append(f"""
    {{
      "seccion": "{seccion["seccion"]}",
      "duracion_aprox_segundos": {seccion["duracion_aprox_segundos"]},
      "audio_narracion": "{seccion["descripcion_audio"]}",
      "instrucciones_visuales": "{seccion["descripcion_visual"]}"
    }}""")

    secciones_json = ",".join(secciones_desc)

    prompt = f"""Eres un guionista experto en contenido viral para YouTube, especializado en misterios, historias intrigantes y narrativas cautivadoras.

TEMA/HISTORIA BASE: {tema}

INSTRUCCIONES:
1. Genera un guión completo de aproximadamente {cantidad_palabras} palabras en TOTAL (sumando todo el audio_narracion)
2. El guión debe seguir EXACTAMENTE la estructura JSON que te proporciono
3. Cada sección debe tener contenido real y específico basado en el tema
4. El tono debe ser misterioso, intrigante y mantener al espectador enganchado
5. Las instrucciones visuales deben ser específicas y cinematográficas
6. El título debe ser clickbait pero honesto
7. Las etiquetas deben ser relevantes para SEO

IMPORTANTE: Responde ÚNICAMENTE con el JSON válido, sin texto adicional, sin markdown, sin ```json.

El formato JSON que DEBES seguir estrictamente:

{{
  "titulo_sugerido": "Un Título de YouTube Corto, Viral y con Enganche",
  "descripcion_sugerida": "Una breve descripción optimizada para SEO que resuma el misterio o la historia.",
  "etiquetas_sugeridas": "lista,de,palabras,clave,separadas,por,comas",
  "estructura_guion": [{secciones_json}
  ]
}}

Genera el guión completo ahora:"""

    try:
        respuesta = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        texto_respuesta = respuesta.text.strip()

        # Limpiar posibles marcadores de código
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:]
        if texto_respuesta.startswith("```"):
            texto_respuesta = texto_respuesta[3:]
        if texto_respuesta.endswith("```"):
            texto_respuesta = texto_respuesta[:-3]

        texto_respuesta = texto_respuesta.strip()

        # Parsear el JSON
        guion = json.loads(texto_respuesta)
        return guion

    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Error al parsear la respuesta de Gemini como JSON: {e}\nRespuesta: {texto_respuesta[:500]}..."
        )
    except Exception as e:
        raise RuntimeError(f"Error al generar el guión: {e}") from e


def guardar_guion(guion: dict, tema: str) -> str:
    """Guarda el guión en un archivo JSON."""
    # Crear carpeta de salida si no existe
    output_dir = os.path.join(os.path.dirname(__file__), "guiones_generados")
    os.makedirs(output_dir, exist_ok=True)

    # Generar nombre de archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tema_limpio = (
        "".join(c if c.isalnum() or c == " " else "" for c in tema[:30])
        .strip()
        .replace(" ", "_")
    )
    filename = f"guion_{tema_limpio}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(guion, f, ensure_ascii=False, indent=2)

    return filepath


def parsear_duracion(valor) -> int:
    """Convierte un valor de duración a entero, manejando formatos inesperados."""
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float):
        return int(valor)
    if isinstance(valor, str):
        # Extraer solo los números del string
        import re

        numeros = re.findall(r"\d+", valor)
        if numeros:
            return int(numeros[0])
    return 30  # Valor por defecto si no se puede parsear


def mostrar_guion(guion: dict):
    """Muestra el guión de forma legible en consola."""
    print("\n" + "=" * 60)
    print(f"🎬 TÍTULO: {guion['titulo_sugerido']}")
    print("=" * 60)

    print(f"\n📝 DESCRIPCIÓN:\n{guion['descripcion_sugerida']}")
    print(f"\n🏷️  ETIQUETAS: {guion['etiquetas_sugeridas']}")

    print("\n" + "-" * 60)
    print("📋 ESTRUCTURA DEL GUIÓN:")
    print("-" * 60)

    total_palabras = 0
    total_segundos = 0

    for i, seccion in enumerate(guion["estructura_guion"], 1):
        duracion = parsear_duracion(seccion["duracion_aprox_segundos"])
        print(f"\n🎯 [{i}] {seccion['seccion']}")
        print(f"   ⏱️  Duración: ~{duracion} segundos")
        print("\n   🎙️  NARRACIÓN:")
        print(f"   {seccion['audio_narracion']}")
        print("\n   🎥 VISUAL:")
        print(f"   {seccion['instrucciones_visuales']}")
        print("-" * 60)

        total_palabras += len(seccion["audio_narracion"].split())
        total_segundos += duracion

    print("\n📊 ESTADÍSTICAS:")
    print(f"   - Palabras totales (narración): ~{total_palabras}")
    print(
        f"   - Duración total estimada: ~{total_segundos} segundos ({total_segundos // 60}:{total_segundos % 60:02d} min)"
    )


def extraer_texto_narracion(guion: dict) -> str:
    """Extrae todo el texto de narración del guión para convertirlo a audio."""
    textos = []
    for seccion in guion["estructura_guion"]:
        textos.append(seccion["audio_narracion"])
    return "\n\n".join(textos)


def guardar_audio_wav(audio_data: bytes, filepath: str, sample_rate: int = 24000):
    """Guarda datos de audio PCM como archivo WAV."""
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)


def generar_audio_gemini(client, texto: str, filepath: str, voz: str = "Kore") -> str:
    """
    Genera audio usando Gemini TTS (voz de IA de Google).

    Voces disponibles para español:
    - Kore: Voz femenina, clara y profesional
    - Charon: Voz masculina, profunda
    - Puck: Voz masculina, juvenil
    - Aoede: Voz femenina, suave
    """
    print(f"   Usando Gemini TTS con voz '{voz}'...")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=texto,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voz,
                        )
                    )
                ),
            ),
        )

        # Extraer datos de audio
        audio_data = response.candidates[0].content.parts[0].inline_data.data

        # Guardar como WAV
        guardar_audio_wav(audio_data, filepath)

        return filepath

    except Exception as e:
        raise RuntimeError(f"Error al generar audio con Gemini TTS: {e}") from e


def generar_audio(client, guion: dict, tema: str, voz: str = "Kore") -> str:
    """
    Genera un archivo de audio a partir del guión usando Gemini TTS.

    Args:
        client: Cliente de Gemini configurado
        guion: Diccionario con el guión generado
        tema: Tema del guión (para nombrar el archivo)
        voz: Nombre de la voz a usar (Kore, Charon, Puck, Aoede)

    Returns:
        Ruta del archivo de audio generado
    """
    # Crear carpeta de salida si no existe
    output_dir = os.path.join(os.path.dirname(__file__), "audios_generados")
    os.makedirs(output_dir, exist_ok=True)

    # Generar nombre de archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tema_limpio = (
        "".join(c if c.isalnum() or c == " " else "" for c in tema[:30])
        .strip()
        .replace(" ", "_")
    )
    filename = f"audio_{tema_limpio}_{timestamp}.wav"
    filepath = os.path.join(output_dir, filename)

    # Extraer texto de narración
    texto = extraer_texto_narracion(guion)

    print(f"   Texto a convertir: {len(texto)} caracteres")

    # Generar audio con Gemini TTS
    return generar_audio_gemini(client, texto, filepath, voz)


def dividir_texto_en_segmentos(
    texto: str, duracion_audio: float, segundos_por_segmento: int = 30
) -> list:
    """
    Divide el texto de narración en segmentos basados en la duración del audio.

    Args:
        texto: Texto completo de la narración
        duracion_audio: Duración total del audio en segundos
        segundos_por_segmento: Duración de cada segmento (default 30s)

    Returns:
        Lista de segmentos de texto
    """
    import math

    # Calcular número de segmentos
    num_segmentos = math.ceil(duracion_audio / segundos_por_segmento)

    # Dividir el texto por palabras
    palabras = texto.split()
    palabras_por_segmento = len(palabras) // num_segmentos

    segmentos = []
    for i in range(num_segmentos):
        inicio = i * palabras_por_segmento
        if i == num_segmentos - 1:
            # Último segmento: tomar todas las palabras restantes
            fin = len(palabras)
        else:
            fin = (i + 1) * palabras_por_segmento

        segmento = " ".join(palabras[inicio:fin])
        segmentos.append(segmento)

    return segmentos


def generar_prompt_visual(
    client, segmento_texto: str, tema: str, num_segmento: int
) -> str:
    """
    Genera un prompt visual basado en el contenido del segmento de texto.

    Args:
        client: Cliente de Gemini configurado
        segmento_texto: Texto del segmento de narración
        tema: Tema general de la historia
        num_segmento: Número del segmento

    Returns:
        Prompt optimizado para generación de imagen
    """
    prompt_generador = f"""Eres un experto en crear prompts para generación de imágenes.

Tema de la historia: {tema}

Texto de narración de este momento (segundos {(num_segmento - 1) * 30}-{num_segmento * 30}):
"{segmento_texto}"

Genera UN prompt corto (máximo 100 palabras) para crear una imagen que represente visualmente este momento de la narración.
El prompt debe ser:
- En inglés (para mejor calidad de imagen)
- Descriptivo y visual
- Estilo cinematográfico, dramático
- Sin texto ni palabras en la imagen
- Formato 16:9 horizontal

Responde SOLO con el prompt, sin explicaciones adicionales."""

    try:
        respuesta = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt_generador
        )
        return respuesta.text.strip()
    except Exception as e:
        # Fallback: prompt genérico basado en el tema
        return f"Cinematic scene, dramatic lighting, {tema}, mysterious atmosphere, 4K quality, film still"


def generar_imagen(client, prompt: str, filepath: str) -> str:
    """
    Genera una imagen usando Imagen 4.0 de Google.

    Args:
        client: Cliente de Gemini configurado
        prompt: Descripción de la imagen a generar
        filepath: Ruta donde guardar la imagen

    Returns:
        Ruta del archivo de imagen generado
    """
    try:
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",  # Formato YouTube
                safety_filter_level="BLOCK_LOW_AND_ABOVE",
            ),
        )

        # Guardar la imagen
        if response.generated_images:
            image_data = response.generated_images[0].image.image_bytes
            with open(filepath, "wb") as f:
                f.write(image_data)
            return filepath
        else:
            raise RuntimeError("No se generó ninguna imagen")

    except Exception as e:
        raise RuntimeError(f"Error al generar imagen: {e}") from e


def generar_imagenes_por_tiempo(
    client, guion: dict, tema: str, duracion_audio: float, segundos_por_imagen: int = 30
) -> tuple:
    """
    Genera imágenes cada X segundos, con contenido relacionado a ese momento de la narración.

    Args:
        client: Cliente de Gemini configurado
        guion: Diccionario con el guión generado
        tema: Tema del guión
        duracion_audio: Duración del audio en segundos
        segundos_por_imagen: Cada cuántos segundos generar una imagen (default 30)

    Returns:
        Tupla con (lista de rutas de imágenes, directorio de salida)
    """
    import math

    # Crear carpeta de salida
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tema_limpio = (
        "".join(c if c.isalnum() or c == " " else "" for c in tema[:30])
        .strip()
        .replace(" ", "_")
    )
    output_dir = os.path.join(
        os.path.dirname(__file__), "imagenes_generadas", f"{tema_limpio}_{timestamp}"
    )
    os.makedirs(output_dir, exist_ok=True)

    # Extraer texto completo de narración
    texto_completo = extraer_texto_narracion(guion)

    # Dividir texto en segmentos según duración
    segmentos = dividir_texto_en_segmentos(
        texto_completo, duracion_audio, segundos_por_imagen
    )

    num_imagenes = len(segmentos)
    print(f"   Duración del audio: {duracion_audio:.1f}s")
    print(f"   Imágenes a generar: {num_imagenes} (una cada {segundos_por_imagen}s)")

    imagenes = []

    for i, segmento in enumerate(segmentos, 1):
        tiempo_inicio = (i - 1) * segundos_por_imagen
        tiempo_fin = min(i * segundos_por_imagen, duracion_audio)

        print(
            f"\n   📸 Imagen {i}/{num_imagenes} [{tiempo_inicio}s - {tiempo_fin:.0f}s]"
        )
        print(
            f'      Texto: "{segmento[:80]}..."'
            if len(segmento) > 80
            else f'      Texto: "{segmento}"'
        )

        # Generar prompt visual contextual usando Gemini
        print(f"      Generando prompt visual...")
        prompt = generar_prompt_visual(client, segmento, tema, i)
        print(
            f'      Prompt: "{prompt[:100]}..."'
            if len(prompt) > 100
            else f'      Prompt: "{prompt}"'
        )

        filepath = os.path.join(output_dir, f"imagen_{i:02d}.png")

        try:
            print(f"      Generando imagen...")
            generar_imagen(client, prompt, filepath)
            imagenes.append(filepath)
            print(f"      ✅ Imagen generada")
        except RuntimeError as e:
            print(f"      ⚠️ Error: {e}")
            imagenes.append(None)

    return imagenes, output_dir


def verificar_ffmpeg() -> bool:
    """Verifica si FFmpeg está instalado."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def obtener_duracion_audio(audio_path: str) -> float:
    """Obtiene la duración de un archivo de audio WAV en segundos."""
    with wave.open(audio_path, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def crear_video(
    imagenes: list, audio_path: str, output_path: str, duracion_imagen: int = 10
) -> str:
    """
    Crea un video a partir de imágenes y audio usando FFmpeg.

    Args:
        imagenes: Lista de rutas de imágenes
        audio_path: Ruta del archivo de audio
        output_path: Ruta donde guardar el video
        duracion_imagen: Duración de cada imagen en segundos

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

    # Filtrar imágenes válidas
    imagenes_validas = [img for img in imagenes if img and os.path.exists(img)]

    if not imagenes_validas:
        raise RuntimeError("No hay imágenes válidas para crear el video")

    # Obtener duración del audio
    duracion_audio = obtener_duracion_audio(audio_path)

    # Calcular duración por imagen basada en el audio
    duracion_por_imagen = duracion_audio / len(imagenes_validas)

    print(f"   Duración del audio: {duracion_audio:.1f}s")
    print(f"   Imágenes: {len(imagenes_validas)}")
    print(f"   Duración por imagen: {duracion_por_imagen:.1f}s")

    # Método más confiable: usar slideshow con loop en cada imagen
    # Crear video con imágenes usando input múltiple

    # Construir los inputs de imágenes
    inputs = []
    filter_parts = []

    for i, img in enumerate(imagenes_validas):
        inputs.extend(["-loop", "1", "-t", str(duracion_por_imagen), "-i", img])
        # Escalar cada imagen y agregar fade in/out
        fade_in = 0
        fade_out = duracion_por_imagen - 0.5
        filter_parts.append(
            f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,"
            f"fade=t=in:st=0:d=0.5,fade=t=out:st={fade_out}:d=0.5[v{i}]"
        )

    # Concatenar todos los videos
    concat_inputs = "".join([f"[v{i}]" for i in range(len(imagenes_validas))])
    filter_complex = (
        ";".join(filter_parts)
        + f";{concat_inputs}concat=n={len(imagenes_validas)}:v=1:a=0[outv]"
    )

    # Índice del audio (después de todas las imágenes)
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
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error al crear video con FFmpeg: {e.stderr}") from e


def generar_video_completo(
    client, guion: dict, audio_path: str, tema: str, segundos_por_imagen: int = 30
) -> str:
    """
    Genera el video completo: imágenes + audio.
    Las imágenes se generan cada X segundos con contenido contextual.

    Args:
        client: Cliente de Gemini configurado
        guion: Diccionario con el guión
        audio_path: Ruta del archivo de audio
        tema: Tema del guión
        segundos_por_imagen: Cada cuántos segundos generar una imagen (default 30)

    Returns:
        Ruta del video generado
    """
    # Obtener duración del audio primero
    duracion_audio = obtener_duracion_audio(audio_path)

    print("\n🎨 GENERANDO IMÁGENES (una cada {}s)...".format(segundos_por_imagen))
    imagenes, img_dir = generar_imagenes_por_tiempo(
        client, guion, tema, duracion_audio, segundos_por_imagen
    )

    imagenes_ok = [img for img in imagenes if img]
    print(f"\n   ✅ {len(imagenes_ok)}/{len(imagenes)} imágenes generadas")

    if not imagenes_ok:
        raise RuntimeError("No se pudieron generar imágenes")

    # Crear video
    print("\n🎥 CREANDO VIDEO...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tema_limpio = (
        "".join(c if c.isalnum() or c == " " else "" for c in tema[:30])
        .strip()
        .replace(" ", "_")
    )

    output_dir = os.path.join(os.path.dirname(__file__), "videos_generados")
    os.makedirs(output_dir, exist_ok=True)

    video_path = os.path.join(output_dir, f"video_{tema_limpio}_{timestamp}.mp4")

    crear_video(imagenes, audio_path, video_path)

    return video_path


def obtener_credenciales_youtube():
    """
    Obtiene las credenciales de YouTube, usando caché si está disponible.
    La primera vez abrirá el navegador para autorizar.
    """
    credentials = None
    token_path = os.path.join(os.path.dirname(__file__), "youtube_token.pickle")

    # Buscar el archivo client_secret
    client_secret_path = None
    for archivo in os.listdir(os.path.dirname(__file__)):
        if archivo.startswith("client_secret") and archivo.endswith(".json"):
            client_secret_path = os.path.join(os.path.dirname(__file__), archivo)
            break

    if not client_secret_path:
        raise FileNotFoundError(
            "No se encontró el archivo client_secret*.json\n"
            "Descárgalo desde Google Cloud Console y colócalo en la carpeta del proyecto."
        )

    # Cargar credenciales guardadas si existen
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            credentials = pickle.load(token)

    # Si no hay credenciales válidas, obtener nuevas
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_path, YOUTUBE_SCOPES
            )
            credentials = flow.run_local_server(port=0)

        # Guardar credenciales para futuras ejecuciones
        with open(token_path, "wb") as token:
            pickle.dump(credentials, token)

    return credentials


def subir_video_youtube(
    video_path: str, guion: dict, privacidad: str = "private"
) -> str:
    """
    Sube un video a YouTube.

    Args:
        video_path: Ruta del archivo de video
        guion: Diccionario con el guión (para título, descripción, etiquetas)
        privacidad: 'public', 'private', o 'unlisted'

    Returns:
        URL del video subido
    """
    print("\n📤 SUBIENDO VIDEO A YOUTUBE...")

    # Obtener credenciales
    credentials = obtener_credenciales_youtube()

    # Crear servicio de YouTube
    youtube = build("youtube", "v3", credentials=credentials)

    # Preparar metadata del video
    titulo = guion.get("titulo_sugerido", "Video generado con IA")[
        :100
    ]  # Max 100 chars
    descripcion = guion.get("descripcion_sugerida", "")
    etiquetas = guion.get("etiquetas_sugeridas", "").split(",")
    etiquetas = [tag.strip() for tag in etiquetas if tag.strip()][:500]  # Max 500 tags

    # Agregar info al final de la descripción
    descripcion += (
        "\n\n---\n🤖 Video generado automáticamente con IA (Gemini + Imagen 4.0)"
    )

    body = {
        "snippet": {
            "title": titulo,
            "description": descripcion,
            "tags": etiquetas,
            "categoryId": "22",  # People & Blogs (puedes cambiar)
        },
        "status": {
            "privacyStatus": privacidad,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Subir video
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024,  # 1MB chunks
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()), body=body, media_body=media
    )

    response = None
    print("   Subiendo...")

    while response is None:
        status, response = request.next_chunk()
        if status:
            progreso = int(status.progress() * 100)
            print(f"   Progreso: {progreso}%")

    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    print(f"   ✅ Video subido exitosamente!")

    return video_url


def main():
    """Función principal del programa."""
    print("=" * 60)
    print("🎬 GENERADOR DE VIDEOS PARA YOUTUBE CON GEMINI 🎬")
    print("=" * 60)

    # Cargar estructura
    try:
        estructura = cargar_estructura()
        print("✅ Estructura de guión cargada desde config_estructura.json")
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}")
        return

    # Configurar Gemini
    try:
        client = configurar_gemini()
        print("✅ Conexión con Gemini establecida\n")
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        return

    # Solicitar el tema
    print("📝 Ingresa el tema o historia base para tu guión:")
    tema = input("> ").strip()

    if not tema:
        print("❌ El tema no puede estar vacío")
        return

    # Solicitar cantidad de palabras
    try:
        print(
            "\n🔢 ¿Cuántas palabras aproximadas debe tener el guión? (recomendado: 500-2000)"
        )
        cantidad_palabras = int(input("> "))

        if cantidad_palabras < 200:
            print("⚠️ Se recomienda un mínimo de 200 palabras. Usando 200.")
            cantidad_palabras = 200
        elif cantidad_palabras > 5000:
            print("⚠️ Máximo recomendado: 5000 palabras. Usando 5000.")
            cantidad_palabras = 5000

    except ValueError:
        print("❌ Por favor ingresa un número válido")
        return

    # Generar guión
    print(f"\n⏳ Generando guión de ~{cantidad_palabras} palabras...")
    print("   Esto puede tomar unos segundos...")

    try:
        guion = generar_guion(client, tema, cantidad_palabras, estructura)

        # Mostrar guión
        mostrar_guion(guion)

        # Guardar guión
        filepath = guardar_guion(guion, tema)
        print(f"\n💾 Guión guardado en: {filepath}")

        print("\n" + "=" * 60)
        print("✅ ¡Guión generado exitosamente!")
        print("=" * 60)

        # Preguntar si desea generar audio
        print(
            "\n🔊 ¿Deseas generar el audio de la narración con Gemini TTS (voz de IA)?"
        )
        print("   [1] Sí")
        print("   [2] No, solo el guión")
        opcion_audio = input("> ").strip()

        if opcion_audio == "1":
            # Seleccionar voz
            print("\n🎤 Selecciona la voz para la narración:")
            print("   [1] Kore - Voz femenina, clara y profesional")
            print("   [2] Charon - Voz masculina, profunda")
            print("   [3] Puck - Voz masculina, juvenil")
            print("   [4] Aoede - Voz femenina, suave")
            opcion_voz = input("> ").strip()

            voces = {"1": "Kore", "2": "Charon", "3": "Puck", "4": "Aoede"}
            voz = voces.get(opcion_voz, "Kore")

            print(f"\n⏳ Generando audio con voz '{voz}'...")
            print("   Esto puede tomar unos segundos...")

            audio_path = None
            try:
                audio_path = generar_audio(client, guion, tema, voz)
                print(f"\n🔊 Audio guardado en: {audio_path}")
            except RuntimeError as e:
                print(f"❌ {e}")
                audio_path = None

            # Preguntar si desea generar video
            video_path = None
            if audio_path:
                print("\n🎥 ¿Deseas generar el video completo con imágenes IA?")
                print("   [1] Sí, generar video con imágenes")
                print("   [2] No, solo audio")
                opcion_video = input("> ").strip()

                if opcion_video == "1":
                    # Verificar FFmpeg
                    if not verificar_ffmpeg():
                        print("\n⚠️ FFmpeg no está instalado.")
                        print("   Para generar videos, instala FFmpeg:")
                        print("   macOS: brew install ffmpeg")
                        print("   Ubuntu: sudo apt install ffmpeg")
                    else:
                        # Preguntar cada cuántos segundos generar imagen
                        print("\n⏱️ ¿Cada cuántos segundos quieres una imagen nueva?")
                        print("   (Ejemplo: 30 = una imagen cada 30 segundos)")
                        print("   Recomendado: 20-40 segundos")
                        try:
                            segundos_por_imagen = int(input("> ").strip())
                            if segundos_por_imagen < 10:
                                print("   ⚠️ Mínimo 10 segundos. Usando 10.")
                                segundos_por_imagen = 10
                            elif segundos_por_imagen > 120:
                                print("   ⚠️ Máximo 120 segundos. Usando 120.")
                                segundos_por_imagen = 120
                        except ValueError:
                            print(
                                "   ⚠️ Valor inválido. Usando 30 segundos por defecto."
                            )
                            segundos_por_imagen = 30

                        try:
                            video_path = generar_video_completo(
                                client, guion, audio_path, tema, segundos_por_imagen
                            )
                            print(f"\n🎬 Video guardado en: {video_path}")
                        except RuntimeError as e:
                            print(f"❌ {e}")
                            video_path = None

                # Preguntar si desea subir a YouTube
                if video_path:
                    print("\n📤 ¿Deseas subir el video a YouTube?")
                    print("   [1] Sí, subir como PRIVADO (solo tú lo verás)")
                    print("   [2] Sí, subir como NO LISTADO (solo con link)")
                    print("   [3] Sí, subir como PÚBLICO")
                    print("   [4] No, no subir")
                    opcion_youtube = input("> ").strip()

                    if opcion_youtube in ["1", "2", "3"]:
                        privacidad_map = {
                            "1": "private",
                            "2": "unlisted",
                            "3": "public",
                        }
                        privacidad = privacidad_map[opcion_youtube]

                        try:
                            video_url = subir_video_youtube(
                                video_path, guion, privacidad
                            )
                            print(f"\n🎉 Video disponible en: {video_url}")
                        except Exception as e:
                            print(f"❌ Error al subir a YouTube: {e}")

        print("\n" + "=" * 60)
        print("🎉 ¡Proceso completado!")
        print("=" * 60)

    except RuntimeError as e:
        print(f"❌ {e}")


if __name__ == "__main__":
    main()
