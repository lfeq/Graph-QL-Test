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
                    task_queue.task_done() # Add this
                else:
                    # This case is when image_generator.generate_image returns None/empty but doesn't raise an exception
                    await update_future_viewing_status(db_session, future_viewing_id, ProcessingStatus.FAILED)
                    print(
                        f"Falló la generación de imagen para FutureViewing ID: {future_viewing_id}. Estado actualizado a FAILED.")
                    task_queue.task_done() # Add this

        except Exception as e:
            fv_id_for_error_logging = future_viewing_id if 'future_viewing_id' in locals() else 'tarea desconocida'
            print(f"Error during image generation for FutureViewing ID: {fv_id_for_error_logging}: {e}")
            try:
                if 'future_viewing_id' in locals(): # Check if we have an ID to update status
                    async with AsyncSessionLocal() as db_session_for_error:
                        await update_future_viewing_status(db_session_for_error, future_viewing_id, ProcessingStatus.FAILED)
                        print(f"Successfully set status to FAILED for FutureViewing ID: {future_viewing_id} after generation error.")
                        task_queue.task_done() # Task is done (failure recorded)
                else:
                    # If we don't even have an ID, we can't update status.
                    # Decide if this specific type of error means the task from queue should be considered "done" or if it's a worker issue.
                    # For now, assume if we can't get an ID, the task might be malformed, so mark done to avoid blockage.
                    # This part might need more nuanced handling depending on how an ID could be missing.
                    if not task_queue.empty(): # Check if queue is not empty before calling task_done
                         task_queue.task_done()
                    print(f"Could not update status to FAILED for {fv_id_for_error_logging} as ID was not available.")

            except Exception as db_error:
                print(f"CRITICAL: Failed to update status to FAILED for FutureViewing ID: {fv_id_for_error_logging} after an initial error. DB Error: {db_error}. Task will NOT be marked as done.")
                # DO NOT call task_queue.task_done() here, so the task remains in queue for potential retry.
            
            await asyncio.sleep(5) # Wait before trying to get a new task