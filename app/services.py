import os
import uuid
import aiofiles
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STATIC_FILES_DIR = os.getenv("STATIC_FILES_DIR", "static")  # Directorio base para estáticos
IMAGES_SUBDIR = os.getenv("IMAGES_SUBDIR", "images")  # Subdirectorio para imágenes

if not OPENAI_API_KEY:
    print("Advertencia: OPENAI_API_KEY no está configurada. La generación de imágenes fallará.")
    # raise ValueError("No OPENAI_API_KEY set") # Opcional: lanzar error si es crítico

# Asegurarse de que el directorio de imágenes exista
IMAGES_SAVE_PATH = os.path.join(STATIC_FILES_DIR, IMAGES_SUBDIR)
os.makedirs(IMAGES_SAVE_PATH, exist_ok=True)


class OpenAIImageGenerator:
    def __init__(self):
        if OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        else:
            self.client = None  # No se puede operar sin API key

    async def generate_image(self, name: str, age: int, content: str, future_viewing_id: uuid.UUID) -> str | None:
        if not self.client:
            print("Cliente OpenAI no inicializado debido a falta de API key.")
            return None

        prompt = f"Imagen para {name} de {age} años que se imagina el futuro de la siguiente forma: {content}"
        print(f"Generando imagen con prompt: {prompt}")
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",  # o "hd"
                n=1,
                response_format="b64_json"  # Obtener bytes codificados en base64
            )

            image_b64 = response.data[0].b64_json
            if not image_b64:
                raise Exception("OpenAI no devolvió datos de imagen b64_json.")

            import base64
            image_bytes = base64.b64decode(image_b64)

            file_name = f"{str(future_viewing_id)}.png"
            file_path = os.path.join(IMAGES_SAVE_PATH, file_name)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(image_bytes)

            # Devolver la URL relativa para ser almacenada en la BD
            # Esta URL será usada por el cliente para acceder a la imagen
            # Asumimos que los archivos estáticos se sirven desde /static/
            # Si tu servidor sirve `static/images` como `/images`, entonces sería:
            # image_url = f"/images/{file_name}"
            image_url = f"/{STATIC_FILES_DIR}/{IMAGES_SUBDIR}/{file_name}"
            print(f"Imagen guardada en: {file_path}, URL relativa: {image_url}")
            return image_url

        except Exception as e:
            print(f"Error generando imagen para {future_viewing_id}: {e}")
            # En el C# original, se maneja ClientResultException de forma específica.
            # La nueva biblioteca 'openai' puede lanzar openai. APIError y sus subclases.
            # Ej: openai.RateLimitError, openai. APIConnectionError, etc.
            # Deberías agregar manejo más específico si es necesario.
            return None


# Instancia global o inyectada donde se necesite
image_generator = OpenAIImageGenerator()