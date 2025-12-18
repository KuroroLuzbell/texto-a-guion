"""
Generador de Videos - Modo Menú Avanzado
=========================================
Permite retomar proyectos y ejecutar pasos individuales.

Uso: python main_menu.py
"""

import os
from src import (
    configurar_gemini,
    cargar_estructura,
    cargar_modelos,
    obtener_modelo,
    obtener_opciones_modelos,
    guardar_modelos,
    generar_nombre_proyecto,
    crear_estructura_proyecto,
    crear_metadata_proyecto,
    actualizar_metadata_proyecto,
    cargar_proyecto,
    listar_proyectos,
    generar_guion,
    guardar_guion,
    mostrar_guion,
    generar_audio,
    obtener_duracion_audio,
    generar_imagenes,
    verificar_ffmpeg,
    subir_video_youtube,
    crear_video_desde_audio,
    listar_videos_disponibles,
)
from src.guion import cargar_guion
from src.audio import (
    mostrar_opciones_voz, 
    obtener_voz,
    mostrar_opciones_estilo,
    obtener_estilo,
    obtener_voz_recomendada,
)
from src.video import crear_video_desde_proyecto
from src.youtube import mostrar_opciones_privacidad, obtener_privacidad
from src.shorts import generar_shorts_desde_url


def mostrar_menu_principal():
    """Muestra el menú principal."""
    print("\n" + "=" * 50)
    print("🎬 GENERADOR DE VIDEOS - MODO AVANZADO")
    print("=" * 50)
    print("\n¿Qué deseas hacer?\n")
    print("[1] 🚀 Crear proyecto NUEVO (flujo completo)")
    print()
    print("[2] 📝 Solo generar GUIÓN")
    print("[3] 🔊 Generar AUDIO (requiere guión)")
    print("[4] 🖼️  Generar IMÁGENES (requiere audio)")
    print("[5] 🎥 Crear VIDEO (requiere audio + imágenes)")
    print("[6] 📤 Subir a YOUTUBE (requiere video)")
    print()
    print("[7] 📂 Ver proyectos existentes")
    print("[8] 🔄 Retomar proyecto incompleto")
    print("[9] ⚙️  Configurar modelos de IA")
    print()
    print("[10] 📱 Extraer SHORTS desde YouTube")
    print()
    print("[0] ❌ Salir")
    print()


def seleccionar_proyecto() -> tuple:
    """Muestra los proyectos y permite seleccionar uno."""
    proyectos = listar_proyectos()

    if not proyectos:
        print("\n❌ No hay proyectos existentes.")
        return None, None

    print("\n📂 PROYECTOS DISPONIBLES:\n")
    for i, p in enumerate(proyectos, 1):
        estado_emoji = {
            "completado": "✅",
            "iniciado": "🆕",
            "guion_generado": "📝",
            "audio_generado": "🔊",
            "imagenes_generadas": "🖼️",
            "video_generado": "🎥",
        }.get(p["estado"], "❓")

        print(f"   [{i}] {estado_emoji} {p['nombre']}")
        print(f"       Tema: {p['tema'][:50]}...")
        print(f"       Estado: {p['estado']}")
        print()

    print("   [0] Cancelar")

    try:
        opcion = int(input("\nSelecciona un proyecto > ").strip())
        if opcion == 0:
            return None, None
        if 1 <= opcion <= len(proyectos):
            nombre = proyectos[opcion - 1]["nombre"]
            return cargar_proyecto(nombre)
    except (ValueError, FileNotFoundError):
        pass

    print("❌ Selección inválida")
    return None, None


def flujo_completo(client, estructura):
    """Ejecuta el flujo completo de creación."""
    # Importar main y ejecutar
    from main import main

    main()


def configurar_modelos_ia():
    """Permite configurar los modelos de IA a usar."""
    print("\n⚙️  CONFIGURAR MODELOS DE IA")
    print("-" * 40)

    modelos_actuales = cargar_modelos()
    opciones = obtener_opciones_modelos()

    print("\n📋 Modelos actuales:")
    print(f"   📝 Texto: {modelos_actuales['texto']}")
    print(f"   🔊 TTS:   {modelos_actuales['tts']}")
    print(f"   🎨 Imagen: {modelos_actuales['imagen']}")

    print("\n¿Qué modelo deseas cambiar?\n")
    print("[1] 📝 Modelo de texto (guiones y prompts)")
    print("[2] 🔊 Modelo TTS (voz)")
    print("[3] 🎨 Modelo de imágenes")
    print("[0] ↩️  Volver al menú")

    opcion = input("\n> ").strip()

    if opcion == "1":
        print("\n📝 MODELO DE TEXTO")
        print("Opciones disponibles:")
        for i, modelo in enumerate(opciones.get("texto", []), 1):
            actual = " (actual)" if modelo == modelos_actuales["texto"] else ""
            print(f"   [{i}] {modelo}{actual}")

        try:
            sel = int(input("\nSelecciona > ").strip())
            if 1 <= sel <= len(opciones["texto"]):
                nuevo_modelo = opciones["texto"][sel - 1]
                guardar_modelos({"texto": nuevo_modelo})
                print(f"✅ Modelo de texto cambiado a: {nuevo_modelo}")
            else:
                print("❌ Selección inválida")
        except ValueError:
            print("❌ Entrada inválida")

    elif opcion == "2":
        print("\n🔊 MODELO TTS")
        print("Opciones disponibles:")
        for i, modelo in enumerate(opciones.get("tts", []), 1):
            actual = " (actual)" if modelo == modelos_actuales["tts"] else ""
            print(f"   [{i}] {modelo}{actual}")

        try:
            sel = int(input("\nSelecciona > ").strip())
            if 1 <= sel <= len(opciones["tts"]):
                nuevo_modelo = opciones["tts"][sel - 1]
                guardar_modelos({"tts": nuevo_modelo})
                print(f"✅ Modelo TTS cambiado a: {nuevo_modelo}")
            else:
                print("❌ Selección inválida")
        except ValueError:
            print("❌ Entrada inválida")

    elif opcion == "3":
        print("\n🎨 MODELO DE IMÁGENES")
        print("Opciones disponibles:")
        for i, modelo in enumerate(opciones.get("imagen", []), 1):
            actual = " (actual)" if modelo == modelos_actuales["imagen"] else ""
            print(f"   [{i}] {modelo}{actual}")

        try:
            sel = int(input("\nSelecciona > ").strip())
            if 1 <= sel <= len(opciones["imagen"]):
                nuevo_modelo = opciones["imagen"][sel - 1]
                guardar_modelos({"imagen": nuevo_modelo})
                print(f"✅ Modelo de imágenes cambiado a: {nuevo_modelo}")
            else:
                print("❌ Selección inválida")
        except ValueError:
            print("❌ Entrada inválida")

    elif opcion == "0":
        return
    else:
        print("❌ Opción no válida")


def extraer_shorts_menu(client):
    """Extrae shorts desde un video de YouTube."""
    print("\n📱 EXTRAER SHORTS DESDE YOUTUBE")
    print("-" * 40)

    # Pedir URL
    print("\n🔗 Ingresa la URL del video de YouTube:")
    url = input("> ").strip()

    if not url:
        print("❌ URL no puede estar vacía")
        return

    # Pedir número de shorts
    print("\n🔢 ¿Cuántos shorts quieres generar? (1-5, default: 3)")
    try:
        num_input = input("> ").strip()
        num_shorts = int(num_input) if num_input else 3
        num_shorts = max(1, min(5, num_shorts))
    except ValueError:
        num_shorts = 3

    # Método de conversión
    print("\n📱 ¿Cómo convertir a formato vertical?")
    print("   [1] 🤖 Smart (IA detecta sujeto) - Recomendado")
    print("   [2] 🌫️  Blur (fondo difuminado)")
    print("   [3] ✂️  Crop (recortar centro)")

    metodo_input = input("> ").strip()
    if metodo_input == "2":
        metodo = "blur"
    elif metodo_input == "3":
        metodo = "crop"
    else:
        metodo = "smart"

    # Ejecutar
    resultado = generar_shorts_desde_url(client, url, num_shorts, metodo)

    if "error" in resultado:
        print(f"\n❌ Error: {resultado['error']}")
    elif resultado.get("cancelado"):
        print("\n👋 Proceso cancelado")
    else:
        print("\n🎉 ¡Shorts generados exitosamente!")


def solo_guion(client, estructura):
    """Genera solo el guión para un proyecto nuevo o existente."""
    print("\n📝 GENERAR GUIÓN")
    print("-" * 30)

    print("\n[1] Crear proyecto nuevo")
    print("[2] Regenerar guión de proyecto existente")

    opcion = input("> ").strip()

    if opcion == "1":
        print("\n📝 Ingresa el tema:")
        tema = input("> ").strip()
        if not tema:
            print("❌ El tema no puede estar vacío")
            return

        print("\n🔢 ¿Cuántas palabras? (500-2000)")
        try:
            palabras = int(input("> "))
            palabras = max(200, min(5000, palabras))
        except ValueError:
            palabras = 500

        nombre_proyecto = generar_nombre_proyecto(tema)
        rutas = crear_estructura_proyecto(nombre_proyecto)
        config = {"palabras": palabras, "voz": None, "segundos_por_imagen": None}
        crear_metadata_proyecto(rutas, tema, config)

    elif opcion == "2":
        metadata, rutas = seleccionar_proyecto()
        if not metadata:
            return
        tema = metadata["tema"]
        palabras = metadata.get("configuracion", {}).get("palabras", 500)

    else:
        return

    print(f"\n⏳ Generando guión...")

    try:
        guion = generar_guion(client, tema, palabras, estructura)
        mostrar_guion(guion)
        guardar_guion(guion, rutas)

        actualizar_metadata_proyecto(
            rutas,
            {"estado": "guion_generado", "archivos": {"guion": "guion/guion.json"}},
        )

        print(f"\n✅ Guión guardado en: {rutas['guion']}")

    except RuntimeError as e:
        print(f"❌ {e}")


def solo_audio(client):
    """Genera audio para un proyecto existente con guión."""
    print("\n🔊 GENERAR AUDIO")
    print("-" * 30)

    metadata, rutas = seleccionar_proyecto()
    if not metadata:
        return

    # Verificar que tiene guión
    guion_path = os.path.join(rutas["guion"], "guion.json")
    if not os.path.exists(guion_path):
        print("❌ Este proyecto no tiene guión. Genera primero el guión.")
        return

    guion = cargar_guion(rutas)

    # Seleccionar estilo de narración
    mostrar_opciones_estilo()
    estilo_opcion = input("> ").strip()
    estilo = obtener_estilo(estilo_opcion)
    print(f"   → Estilo: {estilo['emoji']} {estilo['nombre']}")

    # Seleccionar voz con recomendación
    voz_recomendada = obtener_voz_recomendada(estilo)
    print(f"\n💡 Voz recomendada para {estilo['nombre']}: {voz_recomendada}")
    mostrar_opciones_voz()
    print("   [Enter] Usar voz recomendada")
    voz_input = input("> ").strip()
    if voz_input:
        voz = obtener_voz(voz_input)
    else:
        voz = voz_recomendada

    print(f"\n⏳ Generando audio con voz '{voz}' y estilo '{estilo['nombre']}'...")

    try:
        audio_path = generar_audio(client, guion, rutas, voz, estilo)
        print(f"\n✅ Audio guardado en: {audio_path}")

        actualizar_metadata_proyecto(
            rutas,
            {
                "estado": "audio_generado",
                "configuracion": {"voz": voz, "estilo": estilo["nombre"]},
                "archivos": {"audio": "audio/narracion.wav"},
            },
        )

    except RuntimeError as e:
        print(f"❌ {e}")


def solo_imagenes(client):
    """Genera imágenes para un proyecto existente con audio."""
    print("\n🖼️ GENERAR IMÁGENES")
    print("-" * 30)

    metadata, rutas = seleccionar_proyecto()
    if not metadata:
        return

    # Verificar que tiene audio
    audio_path = os.path.join(rutas["audio"], "narracion.wav")
    if not os.path.exists(audio_path):
        print("❌ Este proyecto no tiene audio. Genera primero el audio.")
        return

    guion = cargar_guion(rutas)
    tema = metadata["tema"]

    print("\n⏱️ ¿Cada cuántos segundos una imagen? (10-120)")
    try:
        segundos = int(input("> ").strip())
        segundos = max(10, min(120, segundos))
    except ValueError:
        segundos = 30

    duracion = obtener_duracion_audio(audio_path)
    print(f"\n🎨 Generando imágenes...")

    try:
        imagenes = generar_imagenes(client, guion, rutas, tema, duracion, segundos)
        imagenes_ok = [img for img in imagenes if img]
        print(f"\n✅ {len(imagenes_ok)} imágenes generadas")

        imagenes_relativas = [
            f"imagenes/imagen_{i:02d}.png" for i, img in enumerate(imagenes, 1) if img
        ]
        actualizar_metadata_proyecto(
            rutas,
            {
                "estado": "imagenes_generadas",
                "configuracion": {"segundos_por_imagen": segundos},
                "archivos": {"imagenes": imagenes_relativas},
            },
        )

    except RuntimeError as e:
        print(f"❌ {e}")


def solo_video():
    """Crea video para un proyecto (con imágenes o video base loop)."""
    print("\n🎥 CREAR VIDEO")
    print("-" * 30)

    if not verificar_ffmpeg():
        print("❌ FFmpeg no está instalado.")
        print("   macOS: brew install ffmpeg")
        return

    metadata, rutas = seleccionar_proyecto()
    if not metadata:
        return

    # Verificar que tiene audio
    audio_path = os.path.join(rutas["audio"], "narracion.wav")
    if not os.path.exists(audio_path):
        print("❌ Este proyecto no tiene audio.")
        return

    # Detectar el modo del proyecto
    modo = metadata.get("configuracion", {}).get("modo", "imagenes")
    
    if modo == "video_loop":
        # Modo video base (loop)
        categoria_video = metadata.get("configuracion", {}).get("categoria_video", None)
        
        if not categoria_video:
            # Preguntar categoría si no está definida
            videos = listar_videos_disponibles()
            if not videos:
                print("❌ No hay videos base disponibles")
                return
            
            print("\n📹 Selecciona categoría de video base:")
            categorias = list(videos.keys())
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
        
        print(f"\n🎥 Creando video con loop de '{categoria_video}'...")
        
        try:
            video_path = os.path.join(rutas["video"], "video_final.mp4")
            crear_video_desde_audio(audio_path, video_path, categoria_video)
            print(f"\n✅ Video guardado en: {video_path}")

            actualizar_metadata_proyecto(
                rutas,
                {
                    "estado": "video_generado",
                    "archivos": {"video": "video/video_final.mp4"},
                },
            )

        except RuntimeError as e:
            print(f"❌ {e}")
    
    else:
        # Modo imágenes generadas
        imagenes_dir = rutas["imagenes"]
        if not os.path.exists(imagenes_dir) or not os.listdir(imagenes_dir):
            print("❌ Este proyecto no tiene imágenes.")
            print("   Este proyecto usa modo 'imágenes'. Genera las imágenes primero.")
            return

        print("\n🎥 Creando video con imágenes...")

        try:
            video_path = crear_video_desde_proyecto(rutas)
            print(f"\n✅ Video guardado en: {video_path}")

            actualizar_metadata_proyecto(
                rutas,
                {
                    "estado": "video_generado",
                    "archivos": {"video": "video/video_final.mp4"},
                },
            )

        except RuntimeError as e:
            print(f"❌ {e}")


def solo_youtube():
    """Sube video a YouTube."""
    print("\n📤 SUBIR A YOUTUBE")
    print("-" * 30)

    metadata, rutas = seleccionar_proyecto()
    if not metadata:
        return

    video_path = os.path.join(rutas["video"], "video_final.mp4")
    if not os.path.exists(video_path):
        print("❌ Este proyecto no tiene video.")
        return

    guion = cargar_guion(rutas)

    mostrar_opciones_privacidad()
    privacidad = obtener_privacidad(input("> ").strip())

    if not privacidad:
        print("Subida cancelada.")
        return

    try:
        video_url = subir_video_youtube(video_path, guion, privacidad)
        print(f"\n🎉 Video disponible en: {video_url}")

        actualizar_metadata_proyecto(
            rutas,
            {
                "estado": "completado",
                "youtube": {"subido": True, "url": video_url, "privacidad": privacidad},
            },
        )

    except Exception as e:
        print(f"❌ {e}")


def ver_proyectos():
    """Muestra todos los proyectos."""
    proyectos = listar_proyectos()

    if not proyectos:
        print("\n📂 No hay proyectos todavía.")
        return

    print("\n📂 PROYECTOS:")
    print("-" * 50)

    for p in proyectos:
        estado_emoji = {
            "completado": "✅",
            "iniciado": "🆕",
            "guion_generado": "📝",
            "audio_generado": "🔊",
            "imagenes_generadas": "🖼️",
            "video_generado": "🎥",
            "error_guion": "❌",
            "error_audio": "❌",
            "error_video": "❌",
            "error_youtube": "❌",
        }.get(p["estado"], "❓")

        print(f"\n{estado_emoji} {p['nombre']}")
        print(f"   Tema: {p['tema'][:60]}{'...' if len(p['tema']) > 60 else ''}")
        print(f"   Estado: {p['estado']}")
        print(f"   Fecha: {p['fecha']}")


def retomar_proyecto(client, estructura):
    """Retoma un proyecto incompleto desde donde quedó."""
    print("\n🔄 RETOMAR PROYECTO")
    print("-" * 30)

    metadata, rutas = seleccionar_proyecto()
    if not metadata:
        return

    estado = metadata.get("estado", "iniciado")
    tema = metadata["tema"]

    print(f"\n📊 Estado actual: {estado}")

    # Determinar siguiente paso
    if estado in ["iniciado", "error_guion"]:
        print("➡️ Siguiente paso: Generar guión")
        confirmar = input("¿Continuar? [s/n] > ").strip().lower()
        if confirmar == "s":
            palabras = metadata.get("configuracion", {}).get("palabras", 500)
            guion = generar_guion(client, tema, palabras, estructura)
            mostrar_guion(guion)
            guardar_guion(guion, rutas)
            actualizar_metadata_proyecto(
                rutas,
                {"estado": "guion_generado", "archivos": {"guion": "guion/guion.json"}},
            )
            print("✅ Guión generado")

    elif estado in ["guion_generado", "error_audio"]:
        print("➡️ Siguiente paso: Generar audio")
        confirmar = input("¿Continuar? [s/n] > ").strip().lower()
        if confirmar == "s":
            guion = cargar_guion(rutas)
            mostrar_opciones_voz()
            voz = obtener_voz(input("> ").strip())
            generar_audio(client, guion, rutas, voz)
            actualizar_metadata_proyecto(
                rutas,
                {
                    "estado": "audio_generado",
                    "configuracion": {"voz": voz},
                    "archivos": {"audio": "audio/narracion.wav"},
                },
            )
            print("✅ Audio generado")

    elif estado in ["audio_generado", "error_video"]:
        print("➡️ Siguiente paso: Generar imágenes y video")
        confirmar = input("¿Continuar? [s/n] > ").strip().lower()
        if confirmar == "s":
            guion = cargar_guion(rutas)
            audio_path = os.path.join(rutas["audio"], "narracion.wav")
            duracion = obtener_duracion_audio(audio_path)

            print("\n⏱️ ¿Segundos por imagen? (default: 30)")
            try:
                segundos = int(input("> ").strip())
            except ValueError:
                segundos = 30

            imagenes = generar_imagenes(client, guion, rutas, tema, duracion, segundos)
            video_path = os.path.join(rutas["video"], "video_final.mp4")

            from src.video import crear_video

            crear_video(imagenes, audio_path, video_path)

            actualizar_metadata_proyecto(
                rutas,
                {
                    "estado": "video_generado",
                    "archivos": {"video": "video/video_final.mp4"},
                },
            )
            print("✅ Video generado")

    elif estado in ["imagenes_generadas"]:
        print("➡️ Siguiente paso: Crear video")
        confirmar = input("¿Continuar? [s/n] > ").strip().lower()
        if confirmar == "s":
            crear_video_desde_proyecto(rutas)
            actualizar_metadata_proyecto(
                rutas,
                {
                    "estado": "video_generado",
                    "archivos": {"video": "video/video_final.mp4"},
                },
            )
            print("✅ Video generado")

    elif estado in ["video_generado", "error_youtube"]:
        print("➡️ Siguiente paso: Subir a YouTube")
        confirmar = input("¿Continuar? [s/n] > ").strip().lower()
        if confirmar == "s":
            guion = cargar_guion(rutas)
            video_path = os.path.join(rutas["video"], "video_final.mp4")
            mostrar_opciones_privacidad()
            privacidad = obtener_privacidad(input("> ").strip())
            if privacidad:
                url = subir_video_youtube(video_path, guion, privacidad)
                actualizar_metadata_proyecto(
                    rutas,
                    {
                        "estado": "completado",
                        "youtube": {
                            "subido": True,
                            "url": url,
                            "privacidad": privacidad,
                        },
                    },
                )
                print(f"✅ Subido: {url}")

    elif estado == "completado":
        print("✅ Este proyecto ya está completado.")

    else:
        print(f"❓ Estado desconocido: {estado}")


def main():
    """Función principal del menú."""
    # Inicializar
    try:
        modelos = cargar_modelos()
        print("✅ Modelos cargados:")
        print(f"   📝 Texto: {modelos['texto']}")
        print(f"   🔊 TTS: {modelos['tts']}")
        print(f"   🎨 Imagen: {modelos['imagen']}")

        client = configurar_gemini()
        estructura = cargar_estructura()
    except Exception as e:
        print(f"❌ Error de inicialización: {e}")
        return

    while True:
        mostrar_menu_principal()
        opcion = input("Selecciona una opción > ").strip()

        if opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break
        elif opcion == "1":
            flujo_completo(client, estructura)
        elif opcion == "2":
            solo_guion(client, estructura)
        elif opcion == "3":
            solo_audio(client)
        elif opcion == "4":
            solo_imagenes(client)
        elif opcion == "5":
            solo_video()
        elif opcion == "6":
            solo_youtube()
        elif opcion == "7":
            ver_proyectos()
        elif opcion == "8":
            retomar_proyecto(client, estructura)
        elif opcion == "9":
            configurar_modelos_ia()
        elif opcion == "10":
            extraer_shorts_menu(client)
        else:
            print("❌ Opción no válida")


if __name__ == "__main__":
    main()
