"""
Extractor de Shorts desde YouTube
=================================
Analiza videos de YouTube y genera shorts automáticamente.

Uso: python main_shorts.py
"""

from src import configurar_gemini, cargar_modelos
from src.shorts import generar_shorts_desde_url


def main():
    """Función principal del extractor de shorts."""
    print("=" * 60)
    print("📱 EXTRACTOR DE SHORTS DESDE YOUTUBE 📱")
    print("=" * 60)

    # Inicializar
    try:
        modelos = cargar_modelos()
        print("\n✅ Modelos cargados:")
        print(f"   📝 Texto: {modelos['texto']}")

        client = configurar_gemini()
        print("✅ Conexión con Gemini establecida")
    except Exception as e:
        print(f"❌ Error de inicialización: {e}")
        return

    # Pedir URL
    print("\n" + "-" * 60)
    print("🔗 Ingresa la URL del video de YouTube:")
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
    print("\n" + "=" * 60)
    resultado = generar_shorts_desde_url(client, url, num_shorts, metodo)

    if "error" in resultado:
        print(f"\n❌ Error: {resultado['error']}")
    elif resultado.get("cancelado"):
        print("\n👋 Proceso cancelado por el usuario")
    else:
        print("\n🎉 ¡Proceso completado!")
        print(f"   Revisa tus shorts en: {resultado['rutas']['shorts']}")


if __name__ == "__main__":
    main()
