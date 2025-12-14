"""Generación de imágenes con Imagen 4.0"""

import os
import math
from google.genai import types
from .config import obtener_modelo


def dividir_texto_en_segmentos(
    texto: str, duracion_audio: float, segundos_por_segmento: int = 30
) -> list:
    """
    Divide el texto de narración en segmentos basados en la duración del audio.

    Args:
        texto: Texto completo de la narración
        duracion_audio: Duración total del audio en segundos
        segundos_por_segmento: Duración de cada segmento

    Returns:
        Lista de segmentos de texto
    """
    num_segmentos = math.ceil(duracion_audio / segundos_por_segmento)
    palabras = texto.split()
    palabras_por_segmento = len(palabras) // num_segmentos

    segmentos = []
    for i in range(num_segmentos):
        inicio = i * palabras_por_segmento
        if i == num_segmentos - 1:
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
            model=obtener_modelo("texto"), contents=prompt_generador
        )
        return respuesta.text.strip()
    except Exception:
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
            model=obtener_modelo("imagen"),
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                safety_filter_level="BLOCK_LOW_AND_ABOVE",
            ),
        )

        if response.generated_images:
            image_data = response.generated_images[0].image.image_bytes
            with open(filepath, "wb") as f:
                f.write(image_data)
            return filepath
        else:
            raise RuntimeError("No se generó ninguna imagen")

    except Exception as e:
        raise RuntimeError(f"Error al generar imagen: {e}") from e


def generar_imagenes(
    client,
    guion: dict,
    rutas: dict,
    tema: str,
    duracion_audio: float,
    segundos_por_imagen: int = 30,
) -> list:
    """
    Genera imágenes cada X segundos, con contenido relacionado a ese momento.

    Args:
        client: Cliente de Gemini configurado
        guion: Diccionario con el guión generado
        rutas: Diccionario con las rutas del proyecto
        tema: Tema del guión
        duracion_audio: Duración del audio en segundos
        segundos_por_imagen: Cada cuántos segundos generar una imagen

    Returns:
        Lista de rutas de imágenes generadas
    """
    from .guion import extraer_texto_narracion

    texto_completo = extraer_texto_narracion(guion)
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
        texto_preview = segmento[:80] + "..." if len(segmento) > 80 else segmento
        print(f'      Texto: "{texto_preview}"')

        print("      Generando prompt visual...")
        prompt = generar_prompt_visual(client, segmento, tema, i)
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        print(f'      Prompt: "{prompt_preview}"')

        filepath = os.path.join(rutas["imagenes"], f"imagen_{i:02d}.png")

        try:
            print("      Generando imagen...")
            generar_imagen(client, prompt, filepath)
            imagenes.append(filepath)
            print("      ✅ Imagen generada")
        except RuntimeError as e:
            print(f"      ⚠️ Error: {e}")
            imagenes.append(None)

    return imagenes
