import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .db import AsyncSessionLocal
from .services import image_generator
from .crud import update_future_viewing_image, update_future_viewing_status
from .models import ProcessingStatus

# Una cola simple en memoria para las tareas de generación de imágenes
# En producción, podrías considerar Celery, RQ, o ARQ con Redis.
task_queue = asyncio.Queue()


async def enqueue_image_generation(future_viewing_id: str, name: str, age: int, content: str):
    await task_queue.put((future_viewing_id, name, age, content))
    print(f"Tarea de generación de imagen encolada para FutureViewing ID: {future_viewing_id}")


async def image_generation_worker():
    print("Iniciando worker de generación de imágenes...")
    while True:
        try:
            future_viewing_id, name, age, content = await task_queue.get()
            print(f"Procesando tarea para FutureViewing ID: {future_viewing_id}")

            async with AsyncSessionLocal() as db_session:  # Nueva sesión para esta tarea
                image_url = await image_generator.generate_image(name, age, content, future_viewing_id)

                if image_url:
                    await update_future_viewing_image(db_session, future_viewing_id, image_url,
                                                      ProcessingStatus.COMPLETED)
                    print(f"Imagen generada y FutureViewing ID: {future_viewing_id} actualizado con URL: {image_url}")
                else:
                    await update_future_viewing_status(db_session, future_viewing_id, ProcessingStatus.FAILED)
                    print(
                        f"Falló la generación de imagen para FutureViewing ID: {future_viewing_id}. Estado actualizado a FAILED.")

            task_queue.task_done()
        except Exception as e:
            # Manejo básico de errores en el worker.
            # Considera un logging más robusto y reintentos si es necesario.
            print(
                f"Error en image_generation_worker procesando {future_viewing_id if 'future_viewing_id' in locals() else 'tarea desconocida'}: {e}")
            # No hacer task_done() si la tarea debe reintentarse o ser manejada de otra forma.
            # Si la tarea falló catastróficamente, task_done() puede ser apropiado para evitar que bloquee la cola.
            if task_queue.empty() == False:  # Solo si aun quedan tareas
                task_queue.task_done()  # Marca como hecha para que no se bloquee la cola ante un error grave.
            await asyncio.sleep(5)  # Esperar un poco antes de reintentar obtener una nueva tarea