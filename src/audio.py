"""Generación de audio con Gemini TTS"""

import os
import wave
from google.genai import types
from .config import obtener_modelo


# Estilos de narración disponibles según género
ESTILOS_NARRACION = {
    "1": {
        "nombre": "Terror/Horror",
        "emoji": "👻",
        "descripcion": "Voz tétrica, susurros, pausas dramáticas",
        "instrucciones": "[Habla con voz grave y tétrica, haciendo pausas dramáticas. Usa un tono misterioso y escalofriante, como si contaras una historia de terror alrededor de una fogata. Susurra en los momentos más intensos.]",
        "voz_recomendada": "Charon"
    },
    "2": {
        "nombre": "Misterio/Suspenso",
        "emoji": "🔍",
        "descripcion": "Tono intrigante, pausas de suspenso",
        "instrucciones": "[Habla con tono intrigante y misterioso. Haz pausas estratégicas para crear suspenso. Tu voz debe generar curiosidad y mantener al oyente enganchado, como un detective revelando pistas.]",
        "voz_recomendada": "Charon"
    },
    "3": {
        "nombre": "Romance/Drama",
        "emoji": "💕",
        "descripcion": "Voz suave, emotiva y cálida",
        "instrucciones": "[Habla con voz suave, cálida y emotiva. Transmite sentimientos profundos con tu tono. En momentos románticos, habla más lento y dulce. En momentos dramáticos, añade intensidad emocional.]",
        "voz_recomendada": "Aoede"
    },
    "4": {
        "nombre": "Acción/Épico",
        "emoji": "⚔️",
        "descripcion": "Voz enérgica, épica y emocionante",
        "instrucciones": "[Habla con energía y emoción épica. Tu voz debe transmitir la intensidad de la acción. Acelera en momentos de tensión y usa un tono heroico y grandioso.]",
        "voz_recomendada": "Puck"
    },
    "5": {
        "nombre": "Documental/Informativo",
        "emoji": "📚",
        "descripcion": "Voz clara, profesional y educativa",
        "instrucciones": "[Habla con voz clara, profesional y bien articulada. Como un narrador de documentales, transmite información de manera interesante y accesible. Mantén un ritmo constante.]",
        "voz_recomendada": "Kore"
    },
    "6": {
        "nombre": "Comedia/Entretenimiento",
        "emoji": "😄",
        "descripcion": "Voz animada, divertida y expresiva",
        "instrucciones": "[Habla con tono animado, divertido y expresivo. Varía tu entonación para dar vida a la historia. Añade énfasis cómico donde corresponda y mantén un ritmo dinámico.]",
        "voz_recomendada": "Puck"
    },
    "7": {
        "nombre": "Neutro/Sin estilo",
        "emoji": "🎙️",
        "descripcion": "Narración normal sin instrucciones especiales",
        "instrucciones": "",
        "voz_recomendada": "Kore"
    }
}


def guardar_audio_wav(audio_data: bytes, filepath: str, sample_rate: int = 24000):
    """Guarda datos de audio PCM como archivo WAV."""
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)


def concatenar_audios_wav(archivos_entrada: list, archivo_salida: str):
    """
    Concatena múltiples archivos WAV en uno solo usando FFmpeg.
    Normaliza todos los audios al mismo formato para evitar pérdida de calidad.
    
    Args:
        archivos_entrada: Lista de rutas a archivos WAV
        archivo_salida: Ruta del archivo WAV resultante
    """
    import subprocess
    import tempfile
    
    # Primero, normalizar todos los archivos al mismo formato
    archivos_normalizados = []
    for i, archivo in enumerate(archivos_entrada):
        archivo_norm = archivo.replace('.wav', '_norm.wav')
        cmd_norm = [
            'ffmpeg', '-y',
            '-i', archivo,
            '-acodec', 'pcm_s16le',
            '-ar', '24000',
            '-ac', '1',
            archivo_norm
        ]
        subprocess.run(cmd_norm, capture_output=True, text=True)
        archivos_normalizados.append(archivo_norm)
    
    # Crear archivo de lista para FFmpeg
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        lista_path = f.name
        for archivo in archivos_normalizados:
            archivo_escaped = archivo.replace("'", "'\\''")
            f.write(f"file '{archivo_escaped}'\n")
    
    try:
        # Concatenar los archivos normalizados
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', lista_path,
            '-acodec', 'pcm_s16le',
            '-ar', '24000',
            '-ac', '1',
            archivo_salida
        ]
        
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    finally:
        # Limpiar archivos temporales
        try:
            os.remove(lista_path)
        except OSError:
            pass
        
        # Limpiar archivos normalizados
        for archivo_norm in archivos_normalizados:
            try:
                os.remove(archivo_norm)
            except OSError:
                pass


# Límite de caracteres por llamada a Gemini TTS (conservador)
MAX_CARACTERES_TTS = 7000


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
            model=obtener_modelo("tts"),
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


def generar_audio(client, guion: dict, rutas: dict, voz: str = "Kore", estilo: dict = None) -> str:
    """
    Genera un archivo de audio a partir del guión usando Gemini TTS.
    Si el texto es muy largo, lo divide en secciones y concatena los audios.

    Args:
        client: Cliente de Gemini configurado
        guion: Diccionario con el guión generado
        rutas: Diccionario con las rutas del proyecto
        voz: Nombre de la voz a usar
        estilo: Diccionario con el estilo de narración (opcional)

    Returns:
        Ruta del archivo de audio generado
    """
    filepath = os.path.join(rutas["audio"], "narracion.wav")
    
    # Obtener textos por sección del guión
    secciones = guion.get("estructura_guion", [])
    
    # Preparar instrucciones de estilo
    instrucciones_estilo = ""
    if estilo:
        instrucciones_estilo = estilo.get("instrucciones", "")
        print(f"   🎭 Estilo aplicado: {estilo.get('nombre', 'Neutro')}")
    
    # Calcular el texto total para mostrar estadísticas
    texto_total = "\n\n".join([s["audio_narracion"] for s in secciones])
    total_caracteres = len(texto_total)
    print(f"   📝 Texto total: {total_caracteres} caracteres (~{len(texto_total.split())} palabras)")
    
    # Si el texto es corto, generarlo de una sola vez
    if total_caracteres <= MAX_CARACTERES_TTS:
        print(f"   ✅ Texto dentro del límite, generando en una sola llamada...")
        texto_con_estilo = f"{instrucciones_estilo}\n\n{texto_total}" if instrucciones_estilo else texto_total
        return generar_audio_gemini(client, texto_con_estilo, filepath, voz)
    
    # Si es largo, dividir por secciones del guión
    print(f"   ⚠️  Texto excede el límite ({MAX_CARACTERES_TTS} chars)")
    print(f"   🔄 Generando audio por secciones...")
    
    archivos_temp = []
    total_secciones = len(secciones)
    
    for i, seccion in enumerate(secciones, 1):
        texto_seccion = seccion["audio_narracion"]
        nombre_seccion = seccion.get("seccion", f"Sección {i}")
        
        print(f"\n   [{i}/{total_secciones}] {nombre_seccion}")
        print(f"       Caracteres: {len(texto_seccion)}")
        
        # Aplicar estilo a cada sección
        if instrucciones_estilo:
            texto_seccion = f"{instrucciones_estilo}\n\n{texto_seccion}"
        
        # Si una sección individual es muy larga, dividirla en párrafos
        if len(texto_seccion) > MAX_CARACTERES_TTS:
            print(f"       ⚠️  Sección muy larga, dividiendo en partes...")
            partes = dividir_texto_largo(texto_seccion, MAX_CARACTERES_TTS)
            
            for j, parte in enumerate(partes, 1):
                archivo_temp = os.path.join(rutas["audio"], f"temp_{i}_{j}.wav")
                print(f"       Parte {j}/{len(partes)}: {len(parte)} caracteres")
                generar_audio_gemini(client, parte, archivo_temp, voz)
                archivos_temp.append(archivo_temp)
        else:
            archivo_temp = os.path.join(rutas["audio"], f"temp_{i}.wav")
            generar_audio_gemini(client, texto_seccion, archivo_temp, voz)
            archivos_temp.append(archivo_temp)
    
    # Concatenar todos los audios
    print(f"\n   🔗 Concatenando {len(archivos_temp)} archivos de audio...")
    concatenar_audios_wav(archivos_temp, filepath)
    
    # Limpiar archivos temporales
    for archivo_temp in archivos_temp:
        try:
            os.remove(archivo_temp)
        except OSError:
            pass
    
    print(f"   ✅ Audio final generado: {filepath}")
    return filepath


def dividir_texto_largo(texto: str, max_chars: int) -> list:
    """
    Divide un texto largo en partes más pequeñas respetando los párrafos.
    
    Args:
        texto: Texto a dividir
        max_chars: Máximo de caracteres por parte
    
    Returns:
        Lista de partes del texto
    """
    # Dividir por párrafos (doble salto de línea o punto seguido de espacio)
    parrafos = texto.split('\n\n')
    if len(parrafos) == 1:
        # Si no hay párrafos, dividir por oraciones
        import re
        parrafos = re.split(r'(?<=[.!?])\s+', texto)
    
    partes = []
    parte_actual = ""
    
    for parrafo in parrafos:
        if len(parte_actual) + len(parrafo) + 2 <= max_chars:
            if parte_actual:
                parte_actual += "\n\n" + parrafo
            else:
                parte_actual = parrafo
        else:
            if parte_actual:
                partes.append(parte_actual)
            parte_actual = parrafo
    
    if parte_actual:
        partes.append(parte_actual)
    
    return partes


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


def mostrar_opciones_estilo():
    """Muestra las opciones de estilo de narración disponibles."""
    print("\n🎭 Selecciona el ESTILO de narración:")
    for key, estilo in ESTILOS_NARRACION.items():
        print(f"   [{key}] {estilo['emoji']} {estilo['nombre']} - {estilo['descripcion']}")
        print(f"       └─ Voz recomendada: {estilo['voz_recomendada']}")


def obtener_estilo(opcion: str) -> dict:
    """Obtiene el estilo de narración según la opción seleccionada."""
    if opcion in ESTILOS_NARRACION:
        return ESTILOS_NARRACION[opcion]
    return ESTILOS_NARRACION["7"]  # Neutro por defecto


def obtener_voz_recomendada(estilo: dict) -> str:
    """Obtiene la voz recomendada para un estilo."""
    return estilo.get("voz_recomendada", "Kore")


def aplicar_estilo_texto(texto: str, estilo: dict) -> str:
    """
    Aplica las instrucciones de estilo al texto para TTS.
    
    Args:
        texto: Texto original de la narración
        estilo: Diccionario con el estilo seleccionado
    
    Returns:
        Texto con instrucciones de estilo prepended
    """
    instrucciones = estilo.get("instrucciones", "")
    if instrucciones:
        return f"{instrucciones}\n\n{texto}"
    return texto
