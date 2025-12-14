"""Generación de guiones con Gemini"""

import os
import json
import re
from .config import obtener_modelo


def limpiar_json_gemini(texto: str) -> str:
    """
    Limpia caracteres de control problemáticos en respuestas JSON de Gemini.

    Args:
        texto: String JSON potencialmente con caracteres de control

    Returns:
        String JSON limpio
    """
    # Reemplazar caracteres de control dentro de strings JSON
    # Esto maneja saltos de línea, tabs, etc. que Gemini a veces incluye
    resultado = []
    dentro_string = False
    escape = False

    for char in texto:
        if escape:
            resultado.append(char)
            escape = False
            continue

        if char == "\\":
            escape = True
            resultado.append(char)
            continue

        if char == '"':
            dentro_string = not dentro_string
            resultado.append(char)
            continue

        if dentro_string:
            # Dentro de un string, reemplazar caracteres de control
            if char == "\n":
                resultado.append(" ")  # Reemplazar salto de línea por espacio
            elif char == "\r":
                continue  # Ignorar retorno de carro
            elif char == "\t":
                resultado.append(" ")  # Reemplazar tab por espacio
            elif ord(char) < 32:
                continue  # Ignorar otros caracteres de control
            else:
                resultado.append(char)
        else:
            resultado.append(char)

    return "".join(resultado)


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
            model=obtener_modelo("texto"), contents=prompt
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

        # Limpiar caracteres de control problemáticos dentro de strings JSON
        # Reemplazar saltos de línea literales dentro de valores por espacios
        texto_respuesta = limpiar_json_gemini(texto_respuesta)

        # Parsear el JSON
        guion = json.loads(texto_respuesta)
        return guion

    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Error al parsear la respuesta de Gemini como JSON: {e}\nRespuesta: {texto_respuesta[:500]}..."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Error al generar el guión: {e}") from e


def guardar_guion(guion: dict, rutas: dict) -> str:
    """
    Guarda el guión en la carpeta del proyecto.

    Args:
        guion: Diccionario con el guión
        rutas: Diccionario con las rutas del proyecto

    Returns:
        Ruta del archivo guardado
    """
    filepath = os.path.join(rutas["guion"], "guion.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(guion, f, ensure_ascii=False, indent=2)

    return filepath


def cargar_guion(rutas: dict) -> dict:
    """
    Carga el guión desde la carpeta del proyecto.

    Args:
        rutas: Diccionario con las rutas del proyecto

    Returns:
        Diccionario con el guión
    """
    filepath = os.path.join(rutas["guion"], "guion.json")

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def parsear_duracion(valor) -> int:
    """Convierte un valor de duración a entero, manejando formatos inesperados."""
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float):
        return int(valor)
    if isinstance(valor, str):
        numeros = re.findall(r"\d+", valor)
        if numeros:
            return int(numeros[0])
    return 30


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
    """
    Extrae todo el texto de narración del guión para convertirlo a audio.

    Args:
        guion: Diccionario con el guión

    Returns:
        Texto completo de narración
    """
    textos = []
    for seccion in guion["estructura_guion"]:
        textos.append(seccion["audio_narracion"])
    return "\n\n".join(textos)
