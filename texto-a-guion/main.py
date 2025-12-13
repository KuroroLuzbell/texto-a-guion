"""
Generador de Videos para YouTube con Google Gemini
==================================================
Flujo completo automático: Tema → Guión → Audio → Imágenes → Video → YouTube

Uso: python main.py
"""

import os
from src import (
    configurar_gemini,
    cargar_estructura,
    generar_nombre_proyecto,
    crear_estructura_proyecto,
    crear_metadata_proyecto,
    actualizar_metadata_proyecto,
    generar_guion,
    guardar_guion,
    mostrar_guion,
    generar_audio,
    obtener_duracion_audio,
    generar_imagenes,
    crear_video,
    verificar_ffmpeg,
    subir_video_youtube,
)
from src.audio import mostrar_opciones_voz, obtener_voz


def main():
    """Función principal - Flujo completo automático."""
    print("=" * 60)
    print("🎬 GENERADOR DE VIDEOS PARA YOUTUBE CON GEMINI 🎬")
    print("=" * 60)

    # =========================================================
    # VERIFICACIONES INICIALES
    # =========================================================

    try:
        estructura = cargar_estructura()
        print("✅ Estructura de guión cargada")
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}")
        return

    try:
        client = configurar_gemini()
        print("✅ Conexión con Gemini establecida")
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        return

    if not verificar_ffmpeg():
        print("❌ FFmpeg no está instalado.")
        print("   macOS: brew install ffmpeg")
        print("   Ubuntu: sudo apt install ffmpeg")
        return

    print("✅ FFmpeg disponible\n")

    # =========================================================
    # TODAS LAS PREGUNTAS AL INICIO
    # =========================================================

    print("=" * 60)
    print("📋 CONFIGURACIÓN DEL VIDEO")
    print("=" * 60)

    # 1. Tema
    print("\n📝 Ingresa el tema o historia base:")
    tema = input("> ").strip()
    if not tema:
        print("❌ El tema no puede estar vacío")
        return

    # 2. Cantidad de palabras
    print("\n🔢 ¿Cuántas palabras aproximadas? (recomendado: 500-2000)")
    try:
        cantidad_palabras = int(input("> "))
        cantidad_palabras = max(200, min(5000, cantidad_palabras))
    except ValueError:
        print("❌ Por favor ingresa un número válido")
        return

    # 3. Voz
    mostrar_opciones_voz()
    voz = obtener_voz(input("> ").strip())

    # 4. Segundos por imagen
    print("\n⏱️ ¿Cada cuántos segundos una imagen? (recomendado: 20-40)")
    try:
        segundos_por_imagen = int(input("> ").strip())
        segundos_por_imagen = max(10, min(120, segundos_por_imagen))
    except ValueError:
        segundos_por_imagen = 30

    # =========================================================
    # RESUMEN Y CONFIRMACIÓN
    # =========================================================

    print("\n" + "=" * 60)
    print("📋 RESUMEN DE CONFIGURACIÓN")
    print("=" * 60)
    print(f"   📝 Tema: {tema[:50]}{'...' if len(tema) > 50 else ''}")
    print(f"   🔢 Palabras: ~{cantidad_palabras}")
    print(f"   🎤 Voz: {voz}")
    print(f"   🖼️  Imagen cada: {segundos_por_imagen} segundos")
    print(f"   📤 YouTube: Subida automática (privado)")
    print("=" * 60)

    print("\n¿Iniciar generación? [s/n]")
    if input("> ").strip().lower() != "s":
        print("❌ Cancelado")
        return

    # =========================================================
    # CREAR PROYECTO
    # =========================================================

    nombre_proyecto = generar_nombre_proyecto(tema)
    rutas = crear_estructura_proyecto(nombre_proyecto)
    config = {
        "palabras": cantidad_palabras,
        "voz": voz,
        "segundos_por_imagen": segundos_por_imagen,
    }
    crear_metadata_proyecto(rutas, tema, config)

    print(f"\n📁 Proyecto creado: {nombre_proyecto}")
    print("\n" + "=" * 60)
    print("🚀 INICIANDO GENERACIÓN AUTOMÁTICA...")
    print("=" * 60)

    # =========================================================
    # PASO 1: GUIÓN
    # =========================================================

    print(f"\n📝 [1/4] GENERANDO GUIÓN (~{cantidad_palabras} palabras)...")

    try:
        guion = generar_guion(client, tema, cantidad_palabras, estructura)
        mostrar_guion(guion)
        guardar_guion(guion, rutas)

        actualizar_metadata_proyecto(
            rutas,
            {"estado": "guion_generado", "archivos": {"guion": "guion/guion.json"}},
        )
        print("✅ Guión generado y guardado")

    except RuntimeError as e:
        print(f"❌ Error en guión: {e}")
        actualizar_metadata_proyecto(rutas, {"estado": "error_guion"})
        return

    # =========================================================
    # PASO 2: AUDIO
    # =========================================================

    print(f"\n🔊 [2/4] GENERANDO AUDIO (voz: {voz})...")

    try:
        audio_path = generar_audio(client, guion, rutas, voz)

        actualizar_metadata_proyecto(
            rutas,
            {"estado": "audio_generado", "archivos": {"audio": "audio/narracion.wav"}},
        )
        print(f"✅ Audio generado: {audio_path}")

    except RuntimeError as e:
        print(f"❌ Error en audio: {e}")
        actualizar_metadata_proyecto(rutas, {"estado": "error_audio"})
        return

    # =========================================================
    # PASO 3: IMÁGENES + VIDEO
    # =========================================================

    print(f"\n🖼️ [3/4] GENERANDO IMÁGENES (cada {segundos_por_imagen}s)...")

    try:
        duracion_audio = obtener_duracion_audio(audio_path)
        imagenes = generar_imagenes(
            client, guion, rutas, tema, duracion_audio, segundos_por_imagen
        )

        imagenes_ok = [img for img in imagenes if img]
        print(f"\n✅ {len(imagenes_ok)}/{len(imagenes)} imágenes generadas")

        if not imagenes_ok:
            raise RuntimeError("No se pudieron generar imágenes")

        imagenes_relativas = [
            f"imagenes/imagen_{i:02d}.png" for i, img in enumerate(imagenes, 1) if img
        ]
        actualizar_metadata_proyecto(
            rutas,
            {
                "estado": "imagenes_generadas",
                "archivos": {"imagenes": imagenes_relativas},
            },
        )

        # Crear video
        print("\n🎥 [3/4] CREANDO VIDEO...")
        video_path = os.path.join(rutas["video"], "video_final.mp4")
        crear_video(imagenes, audio_path, video_path)

        actualizar_metadata_proyecto(
            rutas,
            {
                "estado": "video_generado",
                "archivos": {"video": "video/video_final.mp4"},
            },
        )
        print(f"✅ Video generado: {video_path}")

    except RuntimeError as e:
        print(f"❌ Error en video: {e}")
        actualizar_metadata_proyecto(rutas, {"estado": "error_video"})
        return

    # =========================================================
    # PASO 4: YOUTUBE (automático, privado)
    # =========================================================

    print("\n📤 [4/4] SUBIENDO A YOUTUBE (privado)...")

    try:
        video_url = subir_video_youtube(video_path, guion, "private")

        actualizar_metadata_proyecto(
            rutas,
            {
                "estado": "completado",
                "youtube": {"subido": True, "url": video_url, "privacidad": "private"},
            },
        )

    except Exception as e:
        print(f"❌ Error en YouTube: {e}")
        actualizar_metadata_proyecto(rutas, {"estado": "error_youtube"})
        print(f"\n⚠️ Video guardado localmente: {video_path}")

    # =========================================================
    # FIN
    # =========================================================

    print("\n" + "=" * 60)
    print("🎉 ¡PROCESO COMPLETADO!")
    print("=" * 60)
    print(f"📁 Proyecto: {rutas['raiz']}")
    print(f"🎬 Video: {video_path}")
    if "video_url" in dir():
        print(f"📺 YouTube: {video_url}")
    print("=" * 60)


if __name__ == "__main__":
    main()
