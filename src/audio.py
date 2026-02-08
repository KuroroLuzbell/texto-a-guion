"""
Generación de audio con Gemini TTS

Fuente oficial de voces Gemini TTS:
https://cloud.google.com/vertex-ai/docs/generative-ai/learn/tts-voices
Todas las voces recomendadas en los estilos deben estar en VOCES_OFICIALES.
"""

import os
import wave
from google.genai import types
from .config import obtener_modelo


# Lista oficial de voces Gemini TTS (nombre, descripción, género)
VOCES_OFICIALES = [
    ("achernar", "Femenina, cálida y clara", "Femenina"),
    ("achird", "Femenina, suave y amigable", "Femenina"),
    ("algenib", "Masculina, profunda y calmada", "Masculina"),
    ("algieba", "Femenina, juvenil y brillante", "Femenina"),
    ("alnilam", "Masculina, clara y narrativa", "Masculina"),
    ("aoede", "Femenina, suave y emotiva", "Femenina"),
    ("autonoe", "Femenina, expresiva y dinámica", "Femenina"),
    ("callirrhoe", "Femenina, cálida y maternal", "Femenina"),
    ("charon", "Masculina, grave y misteriosa", "Masculina"),
    ("despina", "Femenina, clara y profesional", "Femenina"),
    ("enceladus", "Masculina, juvenil y energética", "Masculina"),
    ("erinome", "Femenina, dulce y suave", "Femenina"),
    ("fenrir", "Masculina, fuerte y épica", "Masculina"),
    ("gacrux", "Masculina, cálida y amigable", "Masculina"),
    ("iapetus", "Masculina, profunda y narrativa", "Masculina"),
    ("kore", "Femenina, clara y profesional", "Femenina"),
    ("laomedeia", "Femenina, juvenil y alegre", "Femenina"),
    ("leda", "Femenina, suave y calmada", "Femenina"),
    ("orus", "Masculina, grave y pausada", "Masculina"),
    ("puck", "Masculina, juvenil y animada", "Masculina"),
    ("pulcherrima", "Femenina, elegante y clara", "Femenina"),
    ("rasalgethi", "Masculina, profunda y serena", "Masculina"),
    ("sadachbia", "Femenina, clara y científica", "Femenina"),
    ("sadaltager", "Masculina, narrativa y cálida", "Masculina"),
    ("schedar", "Femenina, suave y narrativa", "Femenina"),
    ("sulafat", "Femenina, expresiva y musical", "Femenina"),
    ("umbriel", "Masculina, calmada y profunda", "Masculina"),
    ("vindemiatrix", "Femenina, clara y amigable", "Femenina"),
    ("zephyr", "Masculina, juvenil y fresca", "Masculina"),
    ("zubenelgenubi", "Femenina, cálida y narrativa", "Femenina"),
]


def voz_oficial_or_default(voz):
    """Valida que una voz esté en la lista oficial, sino devuelve 'Kore'."""
    nombres_oficiales = [n.lower() for n, _, _ in VOCES_OFICIALES]
    return voz if voz.lower() in nombres_oficiales else "Kore"


# Estilos de narración disponibles según género
ESTILOS_NARRACION = {
    "1": {
        "nombre": "Terror/Horror",
        "emoji": "👻",
        "descripcion": "Voz tétrica, susurros, pausas dramáticas",
        "instrucciones": "[Habla con voz grave y tétrica, haciendo pausas dramáticas. Usa un tono misterioso y escalofriante, como si contaras una historia de terror alrededor de una fogata. Susurra en los momentos más intensos.]",
        "voz_recomendada": voz_oficial_or_default("Charon"),
    },
    "2": {
        "nombre": "Misterio/Suspenso",
        "emoji": "🔍",
        "descripcion": "Tono intrigante, pausas de suspenso",
        "instrucciones": "[Habla con tono intrigante y misterioso. Haz pausas estratégicas para crear suspenso. Tu voz debe generar curiosidad y mantener al oyente enganchado, como un detective revelando pistas.]",
        "voz_recomendada": voz_oficial_or_default("Charon"),
    },
    "3": {
        "nombre": "Romance/Drama",
        "emoji": "💕",
        "descripcion": "Voz suave, emotiva y cálida",
        "instrucciones": "[Habla con voz suave, cálida y emotiva. Transmite sentimientos profundos con tu tono. En momentos románticos, habla más lento y dulce. En momentos dramáticos, añade intensidad emocional.]",
        "voz_recomendada": voz_oficial_or_default("Aoede"),
    },
    "4": {
        "nombre": "Acción/Épico",
        "emoji": "⚔️",
        "descripcion": "Voz enérgica, épica y emocionante",
        "instrucciones": "[Habla con energía y emoción épica. Tu voz debe transmitir la intensidad de la acción. Acelera en momentos de tensión y usa un tono heroico y grandioso.]",
        "voz_recomendada": voz_oficial_or_default("Atlas"),
    },
    "5": {
        "nombre": "Documental/Informativo",
        "emoji": "📚",
        "descripcion": "Voz clara, profesional y educativa",
        "instrucciones": "[Habla con voz clara, profesional y bien articulada. Como un narrador de documentales, transmite información de manera interesante y accesible. Mantén un ritmo constante.]",
        "voz_recomendada": voz_oficial_or_default("Kore"),
    },
    "6": {
        "nombre": "Comedia/Entretenimiento",
        "emoji": "😄",
        "descripcion": "Voz animada, divertida y expresiva",
        "instrucciones": "[Habla con tono animado, divertido y expresivo. Varía tu entonación para dar vida a la historia. Añade énfasis cómico donde corresponda y mantén un ritmo dinámico.]",
        "voz_recomendada": voz_oficial_or_default("Puck"),
    },
    "7": {
        "nombre": "Neutro/Sin estilo",
        "emoji": "🎙️",
        "descripcion": "Narración normal sin instrucciones especiales",
        "instrucciones": "",
        "voz_recomendada": voz_oficial_or_default("Kore"),
    },
    "8": {
        "nombre": "Narrativo/Cálido",
        "emoji": "📖",
        "descripcion": "Narración cálida y envolvente",
        "instrucciones": "[Habla con voz cálida y envolvente, como si contaras una historia a un amigo. Mantén un ritmo amigable y cercano.]",
        "voz_recomendada": voz_oficial_or_default("Calliope"),
    },
    "9": {
        "nombre": "Narrativo/Masculino",
        "emoji": "🧔",
        "descripcion": "Narración masculina y cálida",
        "instrucciones": "[Habla con voz masculina, cálida y narrativa. Mantén un tono amigable y cercano.]",
        "voz_recomendada": voz_oficial_or_default("Orpheus"),
    },
    "10": {
        "nombre": "Alegre/Expresivo",
        "emoji": "😃",
        "descripcion": "Narración alegre y expresiva",
        "instrucciones": "[Habla con voz alegre y expresiva, transmitiendo entusiasmo y energía positiva.]",
        "voz_recomendada": voz_oficial_or_default("Thalia"),
    },
    "11": {
        "nombre": "Dramático/Profundo",
        "emoji": "🎭",
        "descripcion": "Narración dramática y profunda",
        "instrucciones": "[Habla con voz dramática y profunda, transmitiendo intensidad emocional en cada frase.]",
        "voz_recomendada": voz_oficial_or_default("Melpomene"),
    },
    "12": {
        "nombre": "Musical/Melódico",
        "emoji": "🎶",
        "descripcion": "Narración musical y melódica",
        "instrucciones": "[Habla con voz melódica y musical, como si estuvieras cantando una canción suave.]",
        "voz_recomendada": voz_oficial_or_default("Euterpe"),
    },
    "13": {
        "nombre": "Romántico/Suave",
        "emoji": "💖",
        "descripcion": "Narración romántica y suave",
        "instrucciones": "[Habla con voz romántica y suave, transmitiendo ternura y dulzura.]",
        "voz_recomendada": voz_oficial_or_default("Erato"),
    },
    "14": {
        "nombre": "Solemne/Espiritual",
        "emoji": "🕊️",
        "descripcion": "Narración solemne y espiritual",
        "instrucciones": "[Habla con voz solemne y espiritual, transmitiendo paz y profundidad.]",
        "voz_recomendada": voz_oficial_or_default("Polyhymnia"),
    },
    "15": {
        "nombre": "Dinámico/Rítmico",
        "emoji": "💃",
        "descripcion": "Narración dinámica y rítmica",
        "instrucciones": "[Habla con voz dinámica y rítmica, como si estuvieras narrando una coreografía.]",
        "voz_recomendada": voz_oficial_or_default("Terpsichore"),
    },
    "16": {
        "nombre": "Científico/Claro",
        "emoji": "🔬",
        "descripcion": "Narración científica y clara",
        "instrucciones": "[Habla con voz clara y científica, transmitiendo precisión y objetividad.]",
        "voz_recomendada": voz_oficial_or_default("Urania"),
    },
    "17": {
        "nombre": "Histórico/Narrativo",
        "emoji": "🏛️",
        "descripcion": "Narración histórica y narrativa",
        "instrucciones": "[Habla con voz histórica y narrativa, como si relataras hechos importantes del pasado.]",
        "voz_recomendada": voz_oficial_or_default("Clio"),
    },
    "18": {
        "nombre": "Sabio/Calmado",
        "emoji": "🧘",
        "descripcion": "Narración sabia y calmada",
        "instrucciones": "[Habla con voz sabia y calmada, transmitiendo serenidad y reflexión.]",
        "voz_recomendada": voz_oficial_or_default("Mnemosyne"),
    },
    "19": {
        "nombre": "Maternal/Suave",
        "emoji": "🤱",
        "descripcion": "Narración maternal y suave",
        "instrucciones": "[Habla con voz maternal y suave, transmitiendo protección y cariño.]",
        "voz_recomendada": voz_oficial_or_default("Dione"),
    },
    "20": {
        "nombre": "Juvenil/Brillante",
        "emoji": "🧒",
        "descripcion": "Narración juvenil y brillante",
        "instrucciones": "[Habla con voz juvenil y brillante, transmitiendo energía y frescura.]",
        "voz_recomendada": voz_oficial_or_default("Phoebe"),
    },
    "21": {
        "nombre": "Inspirador/Profundo",
        "emoji": "🌟",
        "descripcion": "Narración inspiradora y profunda",
        "instrucciones": "[Habla con voz inspiradora y profunda, transmitiendo motivación y fuerza.]",
        "voz_recomendada": voz_oficial_or_default("Prometheus"),
    },
    "22": {
        "nombre": "Ágil/Expresivo",
        "emoji": "🏃",
        "descripcion": "Narración ágil y expresiva",
        "instrucciones": "[Habla con voz ágil y expresiva, transmitiendo dinamismo y rapidez.]",
        "voz_recomendada": voz_oficial_or_default("zephyr"),
    },
    "23": {
        "nombre": "Cálido/Claro",
        "emoji": "☀️",
        "descripcion": "Narración cálida y clara",
        "instrucciones": "[Habla con voz cálida y clara, transmitiendo calidez y transparencia en cada palabra.]",
        "voz_recomendada": voz_oficial_or_default("achernar"),
    },
    "24": {
        "nombre": "Amigable/Suave",
        "emoji": "🤗",
        "descripcion": "Narración suave y amigable",
        "instrucciones": "[Habla con voz suave y amigable, creando un ambiente acogedor y cercano.]",
        "voz_recomendada": voz_oficial_or_default("achird"),
    },
    "25": {
        "nombre": "Profundo/Calmado",
        "emoji": "🌊",
        "descripcion": "Narración profunda y calmada",
        "instrucciones": "[Habla con voz profunda y calmada, transmitiendo paz y estabilidad.]",
        "voz_recomendada": voz_oficial_or_default("algenib"),
    },
    "26": {
        "nombre": "Juvenil/Expresivo",
        "emoji": "✨",
        "descripcion": "Narración juvenil y expresiva",
        "instrucciones": "[Habla con voz juvenil y expresiva, transmitiendo vitalidad y entusiasmo.]",
        "voz_recomendada": voz_oficial_or_default("algieba"),
    },
    "27": {
        "nombre": "Narrativo/Claro",
        "emoji": "📻",
        "descripcion": "Narración clara y precisa",
        "instrucciones": "[Habla con voz clara y narrativa, transmitiendo información de forma precisa y comprensible.]",
        "voz_recomendada": voz_oficial_or_default("alnilam"),
    },
    "28": {
        "nombre": "Dinámico/Expresivo",
        "emoji": "⚡",
        "descripcion": "Narración dinámica y vibrante",
        "instrucciones": "[Habla con voz dinámica y expresiva, transmitiendo energía vibrante en cada frase.]",
        "voz_recomendada": voz_oficial_or_default("autonoe"),
    },
    "29": {
        "nombre": "Maternal/Cálido",
        "emoji": "🌸",
        "descripcion": "Narración maternal y cálida",
        "instrucciones": "[Habla con voz maternal y cálida, transmitiendo protección y ternura.]",
        "voz_recomendada": voz_oficial_or_default("callirrhoe"),
    },
    "30": {
        "nombre": "Profesional/Claro",
        "emoji": "💼",
        "descripcion": "Narración profesional y clara",
        "instrucciones": "[Habla con voz profesional y clara, transmitiendo autoridad y precisión.]",
        "voz_recomendada": voz_oficial_or_default("despina"),
    },
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
        archivo_norm = archivo.replace(".wav", "_norm.wav")
        cmd_norm = [
            "ffmpeg",
            "-y",
            "-i",
            archivo,
            "-acodec",
            "pcm_s16le",
            "-ar",
            "24000",
            "-ac",
            "1",
            archivo_norm,
        ]
        subprocess.run(cmd_norm, capture_output=True, text=True)
        archivos_normalizados.append(archivo_norm)

    # Crear archivo de lista para FFmpeg
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        lista_path = f.name
        for archivo in archivos_normalizados:
            archivo_escaped = archivo.replace("'", "'\\''")
            f.write(f"file '{archivo_escaped}'\n")

    try:
        # Concatenar los archivos normalizados
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            lista_path,
            "-acodec",
            "pcm_s16le",
            "-ar",
            "24000",
            "-ac",
            "1",
            archivo_salida,
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
MAX_CARACTERES_TTS = 4000


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


def generar_audio(
    client, guion: dict, rutas: dict, voz: str = "Kore", estilo: dict = None
) -> str:
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
    print(
        f"   📝 Texto total: {total_caracteres} caracteres (~{len(texto_total.split())} palabras)"
    )

    # Si el texto es corto, generarlo de una sola vez
    if total_caracteres <= MAX_CARACTERES_TTS:
        print(f"   ✅ Texto dentro del límite, generando en una sola llamada...")
        texto_con_estilo = (
            f"{instrucciones_estilo}\n\n{texto_total}"
            if instrucciones_estilo
            else texto_total
        )
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
    parrafos = texto.split("\n\n")
    if len(parrafos) == 1:
        # Si no hay párrafos, dividir por oraciones
        import re

        parrafos = re.split(r"(?<=[.!?])\s+", texto)

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


## Eliminada definición duplicada de VOCES_OFICIALES (ya está al inicio del archivo)

# Generar VOCES_DISPONIBLES dinámicamente
VOCES_DISPONIBLES = {
    str(i + 1): (nombre, desc) for i, (nombre, desc, _) in enumerate(VOCES_OFICIALES)
}


def mostrar_opciones_voz():
    """Muestra las opciones de voz disponibles."""
    print("\n🎤 Selecciona la voz para la narración:")
    for key, (nombre, desc) in VOCES_DISPONIBLES.items():
        # Buscar género en VOCES_OFICIALES
        genero = next((g for n, _, g in VOCES_OFICIALES if n == nombre), "")
        icono = "👰‍♀️" if genero == "Femenina" else "🤵" if genero == "Masculina" else ""
        print(f"   [{key}] {nombre}: {desc} {icono}")


def obtener_voz(opcion: str) -> str:
    """Obtiene el nombre de la voz según la opción seleccionada."""
    if opcion in VOCES_DISPONIBLES:
        return VOCES_DISPONIBLES[opcion][0]
    return "Kore"  # Default


def mostrar_opciones_estilo():
    """Muestra las opciones de estilo de narración disponibles."""
    print("\n🎭 Selecciona el ESTILO de narración:")
    # Mapeo de género por voz recomendada (basado en la lista oficial)
    genero_voz = {
        # Femeninas
        "achernar": "👰‍♀️ Femenina",
        "achird": "👰‍♀️ Femenina",
        "algieba": "👰‍♀️ Femenina",
        "aoede": "👰‍♀️ Femenina",
        "autonoe": "👰‍♀️ Femenina",
        "callirrhoe": "👰‍♀️ Femenina",
        "clio": "👰‍♀️ Femenina",
        "despina": "👰‍♀️ Femenina",
        "erinome": "👰‍♀️ Femenina",
        "kore": "👰‍♀️ Femenina",
        "laomedeia": "👰‍♀️ Femenina",
        "leda": "👰‍♀️ Femenina",
        "pulcherrima": "👰‍♀️ Femenina",
        "sadachbia": "👰‍♀️ Femenina",
        "schedar": "👰‍♀️ Femenina",
        "sulafat": "👰‍♀️ Femenina",
        "vindemiatrix": "👰‍♀️ Femenina",
        "zubenelgenubi": "👰‍♀️ Femenina",
        # Masculinas
        "algenib": "🤵 Masculina",
        "alnilam": "🤵 Masculina",
        "charon": "🤵 Masculina",
        "enceladus": "🤵 Masculina",
        "fenrir": "🤵 Masculina",
        "gacrux": "🤵 Masculina",
        "iapetus": "🤵 Masculina",
        "orus": "🤵 Masculina",
        "puck": "🤵 Masculina",
        "rasalgethi": "🤵 Masculina",
        "sadaltager": "🤵 Masculina",
        "umbriel": "🤵 Masculina",
        "zephyr": "🤵 Masculina",
    }
    for key, estilo in ESTILOS_NARRACION.items():
        voz = estilo["voz_recomendada"]
        genero = genero_voz.get(voz.lower(), "?")
        print(
            f"   [{key}] {estilo['emoji']} {estilo['nombre']} - {estilo['descripcion']}"
        )
        print(f"       └─ Voz recomendada: {voz} ({genero})")


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
