"""
Generación de audio con Gemini TTS
"""

import os
import wave
from google.genai import types


def guardar_audio_wav(audio_data: bytes, filepath: str, sample_rate: int = 24000):
    """Guarda datos de audio PCM como archivo WAV."""
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)


def generar_audio_gemini(client, texto: str, filepath: str, voz: str = "Kore") -> str:
    """
    Genera audio usando Gemini TTS.

    Args:
        client: Cliente de Gemini configurado
        texto: Texto a convertir en audio
        filepath: Ruta donde guardar el audio
        voz: Nombre de la voz (Kore, Charon, Puck, Aoede)

    Returns:
        Ruta del archivo de audio generado
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

        audio_data = response.candidates[0].content.parts[0].inline_data.data
        guardar_audio_wav(audio_data, filepath)
        return filepath

    except Exception as e:
        raise RuntimeError(f"Error al generar audio con Gemini TTS: {e}") from e


def generar_audio(client, guion: dict, rutas: dict, voz: str = "Kore") -> str:
    """
    Genera un archivo de audio a partir del guión usando Gemini TTS.

    Args:
        client: Cliente de Gemini configurado
        guion: Diccionario con el guión generado
        rutas: Diccionario con las rutas del proyecto
        voz: Nombre de la voz a usar

    Returns:
        Ruta del archivo de audio generado
    """
    from .guion import extraer_texto_narracion

    filepath = os.path.join(rutas["audio"], "narracion.wav")
    texto = extraer_texto_narracion(guion)

    print(f"   Texto a convertir: {len(texto)} caracteres")

    return generar_audio_gemini(client, texto, filepath, voz)


def obtener_duracion_audio(audio_path: str) -> float:
    """
    Obtiene la duración de un archivo de audio WAV en segundos.

    Args:
        audio_path: Ruta del archivo de audio

    Returns:
        Duración en segundos
    """
    with wave.open(audio_path, "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


# Voces disponibles
VOCES_DISPONIBLES = {
    "1": ("Kore", "Voz femenina, clara y profesional"),
    "2": ("Charon", "Voz masculina, profunda"),
    "3": ("Puck", "Voz masculina, juvenil"),
    "4": ("Aoede", "Voz femenina, suave"),
}


def mostrar_opciones_voz():
    """Muestra las opciones de voz disponibles."""
    print("\n🎤 Selecciona la voz para la narración:")
    for key, (nombre, desc) in VOCES_DISPONIBLES.items():
        print(f"   [{key}] {nombre} - {desc}")


def obtener_voz(opcion: str) -> str:
    """Obtiene el nombre de la voz según la opción seleccionada."""
    if opcion in VOCES_DISPONIBLES:
        return VOCES_DISPONIBLES[opcion][0]
    return "Kore"  # Default
