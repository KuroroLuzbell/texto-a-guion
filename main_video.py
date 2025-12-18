"""
Generador de Videos con Video Base (Loop)
==========================================
Usa un video de fondo que se repite + audio narrado

Flujo: Tema → Guión → Audio → Video Base Loop → YouTube

Uso: python main_video_loop.py
"""

import os
from src import (
    configurar_gemini,
    cargar_estructura,
    cargar_modelos,
    generar_nombre_proyecto,
    crear_estructura_proyecto,
    crear_metadata_proyecto,
    actualizar_metadata_proyecto,
    generar_guion,
    guardar_guion,
    mostrar_guion,
    generar_audio,
    verificar_ffmpeg,
    crear_video_desde_audio,
    listar_videos_disponibles,
    subir_video_youtube,
)
from src.audio import (
    mostrar_opciones_voz, 
    obtener_voz,
    mostrar_opciones_estilo,
    obtener_estilo,
    obtener_voz_recomendada,
)


def mostrar_videos_disponibles():
    """Muestra los videos disponibles por categoría."""
    videos = listar_videos_disponibles()
    
    print("\n📹 VIDEOS BASE DISPONIBLES:")
    print("-" * 40)
    
    if not videos:
        print("   ⚠️  No hay videos configurados")
        print("   Agrega videos a la carpeta 'videos_base/'")
        return None
    
    categorias = list(videos.keys())
    for i, (cat, info) in enumerate(videos.items(), 1):
        print(f"   {i}. {cat.capitalize()} ({info['total']} videos)")
        if info['descripcion']:
            print(f"      └─ {info['descripcion']}")
    
    return categorias


def main():
    """Función principal - Generación con video base en loop."""
    print("=" * 60)
    print("🎬 GENERADOR DE VIDEOS CON VIDEO BASE (LOOP) 🎬")
    print("=" * 60)
    print("📌 Este modo usa un video de fondo que se repite")
    print("   en lugar de generar imágenes con IA")
    print("=" * 60)

    # =========================================================
    # VERIFICACIONES INICIALES
    # =========================================================

    modelos = cargar_modelos()
    print("✅ Modelos cargados:")
    print(f"   📝 Texto: {modelos['texto']}")
    print(f"   🔊 TTS: {modelos['tts']}")

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
        return

    print("✅ FFmpeg disponible")

    # Verificar videos disponibles
    categorias = mostrar_videos_disponibles()
    if not categorias:
        print("\n❌ No hay videos base disponibles")
        print("   Descarga videos y guárdalos en 'videos_base/'")
        return

    # =========================================================
    # CONFIGURACIÓN
    # =========================================================

    print("\n" + "=" * 60)
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

    # 3. Estilo de narración
    mostrar_opciones_estilo()
    estilo_opcion = input("> ").strip()
    estilo = obtener_estilo(estilo_opcion)
    print(f"   → Estilo: {estilo['emoji']} {estilo['nombre']}")
    
    # 4. Voz (con recomendación basada en estilo)
    voz_recomendada = obtener_voz_recomendada(estilo)
    print(f"\n💡 Voz recomendada para {estilo['nombre']}: {voz_recomendada}")
    mostrar_opciones_voz()
    print("   [Enter] Usar voz recomendada")
    voz_input = input("> ").strip()
    if voz_input:
        voz = obtener_voz(voz_input)
    else:
        voz = voz_recomendada

    # 5. Categoría de video
    print(f"\n📹 Selecciona categoría de video [1-{len(categorias)}]:")
    for i, cat in enumerate(categorias, 1):
        print(f"   {i}. {cat.capitalize()}")
    
    try:
        opcion = int(input("> ").strip())
        if 1 <= opcion <= len(categorias):
            categoria_video = categorias[opcion - 1]
        else:
            categoria_video = categorias[0]
    except ValueError:
        categoria_video = categorias[0]
    
    print(f"   → Usando: {categoria_video}")

    # =========================================================
    # RESUMEN Y CONFIRMACIÓN
    # =========================================================

    print("\n" + "=" * 60)
    print("📋 RESUMEN DE CONFIGURACIÓN")
    print("=" * 60)
    print(f"   📝 Tema: {tema[:50]}{'...' if len(tema) > 50 else ''}")
    print(f"   🔢 Palabras: ~{cantidad_palabras}")
    print(f"   � Estilo: {estilo['emoji']} {estilo['nombre']}")
    print(f"   �🎤 Voz: {voz}")
    print(f"   📹 Video base: {categoria_video}")
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
        "estilo": estilo["nombre"],
        "modo": "video_loop",
        "categoria_video": categoria_video,
    }
    crear_metadata_proyecto(rutas, tema, config)

    print(f"\n📁 Proyecto creado: {nombre_proyecto}")
    print("\n" + "=" * 60)
    print("🚀 INICIANDO GENERACIÓN...")
    print("=" * 60)

    # =========================================================
    # PASO 1: GUIÓN
    # =========================================================

    print(f"\n📝 [1/3] GENERANDO GUIÓN (~{cantidad_palabras} palabras)...")

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

    print(f"\n🔊 [2/3] GENERANDO AUDIO (voz: {voz}, estilo: {estilo['nombre']})...")

    try:
        audio_path = generar_audio(client, guion, rutas, voz, estilo)

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
    # PASO 3: VIDEO CON LOOP
    # =========================================================

    print(f"\n🎥 [3/3] CREANDO VIDEO (loop de {categoria_video})...")

    try:
        video_path = os.path.join(rutas["video"], "video_final.mp4")
        crear_video_desde_audio(audio_path, video_path, categoria_video)

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
