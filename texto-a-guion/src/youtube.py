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

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


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

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024,
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
