"""
Subida de videos a YouTube
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .config import BASE_DIR

# Scopes necesarios: subir videos + leer info de canales
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

# Canal seleccionado para la sesión actual
_canal_seleccionado = None


def obtener_credenciales_youtube():
    """
    Obtiene las credenciales de YouTube.
    La primera vez abrirá el navegador para autorizar.

    Returns:
        Credenciales de YouTube
    """
    credentials = None
    token_path = os.path.join(BASE_DIR, "youtube_token.pickle")

    # Buscar el archivo client_secret
    client_secret_path = None
    for archivo in os.listdir(BASE_DIR):
        if archivo.startswith("client_secret") and archivo.endswith(".json"):
            client_secret_path = os.path.join(BASE_DIR, archivo)
            break

    if not client_secret_path:
        raise FileNotFoundError(
            "No se encontró el archivo client_secret*.json\n"
            "Descárgalo desde Google Cloud Console y colócalo en la carpeta del proyecto."
        )

    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_path, YOUTUBE_SCOPES
            )
            credentials = flow.run_local_server(port=0)

        with open(token_path, "wb") as token:
            pickle.dump(credentials, token)

    return credentials


def obtener_canales_disponibles(youtube):
    """
    Obtiene la lista de canales disponibles para el usuario autenticado.

    Returns:
        Lista de diccionarios con info de cada canal
    """
    request = youtube.channels().list(part="snippet,contentDetails", mine=True)
    response = request.execute()

    canales = []
    for item in response.get("items", []):
        canales.append(
            {
                "id": item["id"],
                "titulo": item["snippet"]["title"],
                "descripcion": item["snippet"].get("description", "")[:50],
            }
        )

    return canales


def seleccionar_canal(youtube):
    """
    Permite al usuario seleccionar en qué canal publicar.

    Returns:
        ID del canal seleccionado o None para usar el predeterminado
    """
    global _canal_seleccionado

    # Si ya seleccionó un canal en esta sesión, preguntar si quiere mantenerlo
    if _canal_seleccionado:
        print(f"\n📺 Canal actual: {_canal_seleccionado['titulo']}")
        respuesta = input("   ¿Usar este canal? (s/n): ").strip().lower()
        if respuesta != "n":
            return _canal_seleccionado["id"]

    print("\n📺 SELECCIONAR CANAL DE YOUTUBE")
    print("   Obteniendo tus canales...")

    canales = obtener_canales_disponibles(youtube)

    if not canales:
        print("   ⚠️ No se encontraron canales. Se usará el predeterminado.")
        return None

    if len(canales) == 1:
        print(f"   Solo tienes un canal: {canales[0]['titulo']}")
        _canal_seleccionado = canales[0]
        return canales[0]["id"]

    print("\n   Canales disponibles:")
    for i, canal in enumerate(canales, 1):
        print(f"   [{i}] {canal['titulo']}")

    while True:
        try:
            opcion = input(f"\n   Selecciona el canal (1-{len(canales)}): ").strip()
            indice = int(opcion) - 1
            if 0 <= indice < len(canales):
                _canal_seleccionado = canales[indice]
                print(f"   ✅ Seleccionado: {canales[indice]['titulo']}")
                return canales[indice]["id"]
            else:
                print("   ⚠️ Opción no válida")
        except ValueError:
            print("   ⚠️ Ingresa un número válido")


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

    credentials = obtener_credenciales_youtube()
    youtube = build("youtube", "v3", credentials=credentials)

    # Permitir seleccionar el canal donde publicar
    canal_id = seleccionar_canal(youtube)

    titulo = guion.get("titulo_sugerido", "Video generado con IA")[:100]
    descripcion = guion.get("descripcion_sugerida", "")
    etiquetas = guion.get("etiquetas_sugeridas", "").split(",")
    etiquetas = [tag.strip() for tag in etiquetas if tag.strip()][:500]

    descripcion += (
        "\n\n---\n🤖 Video generado automáticamente con IA (Gemini + Imagen 4.0)"
    )

    body = {
        "snippet": {
            "title": titulo,
            "description": descripcion,
            "tags": etiquetas,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": privacidad,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Si se seleccionó un canal específico, agregarlo al snippet
    if canal_id:
        body["snippet"]["channelId"] = canal_id

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024,
    )

    # Usar onBehalfOfContentOwner si hay canal específico
    request = youtube.videos().insert(
        part=",".join(body.keys()), body=body, media_body=media
    )

    response = None
    print("   Subiendo...")
    if _canal_seleccionado:
        print(f"   📺 Canal destino: {_canal_seleccionado['titulo']}")

    while response is None:
        status, response = request.next_chunk()
        if status:
            progreso = int(status.progress() * 100)
            print(f"   Progreso: {progreso}%")

    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    print("   ✅ Video subido exitosamente!")

    return video_url


# Opciones de privacidad
PRIVACIDAD_OPCIONES = {
    "1": ("private", "PRIVADO (solo tú lo verás)"),
    "2": ("unlisted", "NO LISTADO (solo con link)"),
    "3": ("public", "PÚBLICO"),
}


def mostrar_opciones_privacidad():
    """Muestra las opciones de privacidad disponibles."""
    print("\n📤 ¿Deseas subir el video a YouTube?")
    for key, (_, desc) in PRIVACIDAD_OPCIONES.items():
        print(f"   [{key}] Sí, subir como {desc}")
    print("   [4] No, no subir")


def obtener_privacidad(opcion: str) -> str:
    """Obtiene el nivel de privacidad según la opción seleccionada."""
    if opcion in PRIVACIDAD_OPCIONES:
        return PRIVACIDAD_OPCIONES[opcion][0]
    return None
