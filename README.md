# 🎭 Generador de Historias con Gemini

Proyecto en Python que genera historias creativas usando la API de Google Gemini. Tú proporcionas el tema y la cantidad de palabras, y Gemini crea una historia completa.

## 🚀 Requisitos

- Python 3.9 o superior
- API Key de Google Gemini

## 📦 Instalación

1. **Clona o descarga el proyecto**

2. **Crea un entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En macOS/Linux
   # o en Windows: venv\Scripts\activate
   ```

3. **Instala las dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura tu API Key**
   - Ve a [Google AI Studio](https://aistudio.google.com/app/apikey) y obtén tu API key
   - Crea un archivo `.env` en la raíz del proyecto:
     ```
     GEMINI_API_KEY=tu_api_key_aqui
     ```

## 🎮 Uso

Ejecuta el programa:
```bash
python main.py
```

El programa te pedirá:
1. **Tema**: El texto o tema base para tu historia
2. **Cantidad de palabras**: Cuántas palabras aproximadamente debe tener

## 📝 Ejemplo

```
================================================
🎭 GENERADOR DE HISTORIAS CON GEMINI 🎭
================================================
✅ Conexión con Gemini establecida

Ingresa el tema o texto para tu historia:
> Un astronauta que descubre vida en Marte

¿Cuántas palabras debe tener la historia?
> 500

⏳ Generando historia de ~500 palabras...
--------------------------------------------------

📖 TU HISTORIA:

[Historia generada por Gemini...]
```

## 🔧 Personalización

Puedes modificar el prompt en la función `generar_historia()` en `main.py` para cambiar el estilo de las historias generadas.

## 📄 Licencia

MIT License
