# Proyecto GraphQL con Python y PostgreSQL

Este repositorio contiene una aplicación Python que utiliza GraphQL con Ariadne, SQLAlchemy para la interacción con una base de datos PostgreSQL, y OpenAI para la generación de imágenes. La aplicación está contenerizada utilizando Docker.

## Requisitos Previos

Asegúrate de tener instalados los siguientes componentes en tu sistema:

*   **Python 3.10** (Aunque la aplicación se ejecuta en Docker, tener Python 3.10 localmente puede ser útil para desarrollo o pruebas).
*   **Docker**: [Instrucciones de instalación de Docker](https://docs.docker.com/engine/install/)
*   **Docker Compose**: Generalmente se instala junto con Docker. [Instrucciones](https://docs.docker.com/compose/install/)

## Configuración y Ejecución

Sigue estos pasos para configurar y ejecutar el proyecto:

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/lfeq/Graph-QL-Test.git
    cd Graph-QL-Test
    ```

2.  **Crea un archivo `.env`:**
    En la raíz del proyecto, crea un archivo llamado `.env` con las siguientes variables de entorno. Este archivo será utilizado por `docker-compose.yml` para configurar la aplicación y la base de datos.

    ```env
    OPENAI_API_KEY=<tu_clave_api_de_openai>
    DATABASE_URL="postgresql+asyncpg://graphql_workshop:secret@graphql-workshop-postgres:5432/graphql_workshop"
    STATIC_FILES_DIR="static"
    IMAGES_SUBDIR="images"
    ```
    **Importante**: Reemplaza `<tu_clave_api_de_openai>` con tu clave API real de OpenAI.

3.  **Verifica los requisitos de Python (Opcional - para desarrollo local):**
    Si planeas desarrollar o ejecutar la aplicación fuera de Docker, asegúrate de tener un entorno virtual y de instalar las dependencias:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
    Las dependencias principales incluyen:
    *   `ariadne[asgi-starlette]`
    *   `uvicorn[standard]`
    *   `SQLAlchemy[asyncpg]`
    *   `alembic`
    *   `python-dotenv`
    *   `openai`
    *   `aiofiles`
    *   `Pillow`
    *   `psycopg2-binary` (o `asyncpg` que ya está listado)

4.  **Ejecuta la aplicación con Docker Compose:**
    Este comando construirá las imágenes de Docker (si no existen) y levantará los servicios definidos en `docker-compose.yml` (la aplicación Python y la base de datos PostgreSQL).
    ```bash
    docker-compose up
    ```
    Si deseas forzar la reconstrucción de las imágenes (por ejemplo, si has cambiado el `Dockerfile` o las dependencias en `requirements.txt`):
    ```bash
    docker-compose up --build
    ```

    La aplicación Python estará disponible en `http://localhost:8000`. La interfaz de GraphQL (GraphiQL o similar, dependiendo de la configuración de Ariadne) debería estar accesible en `http://localhost:8000/graphql` (o la ruta que hayas configurado).

5.  **Acceso a la base de datos:**
    La base de datos PostgreSQL estará accesible en el puerto `5432` de tu máquina local, utilizando las credenciales definidas en el archivo `.env` y `docker-compose.yml`.

    ## Ejemplos de Operaciones GraphQL

Puedes interactuar con la API GraphQL usando herramientas como Postman, Insomnia, o la interfaz GraphiQL que Ariadne podría proporcionar en `http://localhost:8000/graphql`.

### Mutation: Añadir un nuevo "Future Viewing"

Esta mutación crea un nuevo registro y encola la generación de una imagen.

```graphql
mutation {
  addFutureViewing(
    input: {
      name: "Robot Atardecer"
      age: 1
      content: "Un robot melancólico observando un atardecer en un planeta alienígena, estilo cyberpunk"
    }
  ) {
    futureViewing {
      id
      name
      age
      content
      createdAt
      status
      imageUrl
      hasBeenViewed
    }
  }
}
```

#### **Respuesta Esperada (Ejemplo):**
```json
{
  "data": {
    "addFutureViewing": {
      "futureViewing": {
        "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "name": "Robot Atardecer",
        "age": 1,
        "content": "Un robot melancólico observando un atardecer en un planeta alienígena, estilo cyberpunk",
        "createdAt": "YYYY-MM-DDTHH:MM:SS.ffffff",
        "status": "PENDING",
        "imageUrl": null,
        "hasBeenViewed": false
      }
    }
  }
}

```
_(El `imageUrl` será `null` inicialmente y el `status` será `PENDING`. Se actualizarán cuando la imagen se genere y guarde correctamente)._

### Query: Obtener "Future Viewings"
Esta query recupera una lista paginada de los "future viewings".

```graphql
query {
  futureViewings(page: 1, pageSize: 5) {
    id
    name
    status
    imageUrl
    createdAt
    hasBeenViewed
  }
}

```

**Respuesta Esperada (Ejemplo):**
``` json
{
  "data": {
    "futureViewings": [
      {
        "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "name": "Robot Atardecer",
        "status": "COMPLETED", // O PENDING/FAILED dependiendo del estado
        "imageUrl": "/static/images/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.png", // Si se completó
        "createdAt": "YYYY-MM-DDTHH:MM:SS.ffffff",
        "hasBeenViewed": false
      }
      // ... más resultados
    ]
  }
}
```


## Solución de Problemas (Troubleshooting)

*   **Problemas con contenedores desactualizados o dependencias:**
    Si encuentras problemas relacionados con versiones antiguas de los contenedores o conflictos de dependencias, el siguiente comando puede ser muy útil. Este comando fuerza la reconstrucción de las imágenes, recrea los contenedores (incluso si ya existen y están actualizados) y no intenta iniciar dependencias que no estén explícitamente definidas para ser reconstruidas.
    ```bash
    docker-compose up --build --force-recreate --no-deps
    ```

*   **Verificar logs:**
    Si la aplicación no se inicia correctamente, revisa los logs de los contenedores:
    ```bash
    docker-compose logs graphql-python-app
    docker-compose logs graphql-workshop-postgres
    ```

*   **Detener la aplicación:**
    Para detener los contenedores, presiona `Ctrl+C` en la terminal donde ejecutaste `docker-compose up`. Para detener y eliminar los contenedores:
    ```bash
    docker-compose down
    ```
    Si también quieres eliminar los volúmenes (¡esto borrará los datos de la base de datos!):
    ```bash
    docker-compose down -v
    ```

## Script de Limpieza de Imágenes

El script `app/cleanup_images.py` está diseñado para gestionar el espacio en disco del servidor eliminando automáticamente las imágenes antiguas.

**Propósito:**
Este script revisa el directorio `static/images/` y elimina cualquier imagen que tenga más de 14 días de antigüedad. Esto ayuda a prevenir que el disco se llene con imágenes que ya no son relevantes o necesarias.

**Ejecución Manual:**
Para ejecutar el script manualmente, navega a la raíz del proyecto en tu terminal y ejecuta:
```bash
python3 app/cleanup_images.py
```
Si estás utilizando un entorno virtual específico y `python3` no apunta a él directamente, asegúrate de usar el intérprete de Python de tu entorno virtual (por ejemplo, `venv/bin/python app/cleanup_images.py` si tu entorno está en una carpeta `venv`).

### Programación de Ejecución Diaria

Para asegurar que las imágenes antiguas se limpien regularmente, se recomienda programar la ejecución automática del script.

**Linux/macOS (usando `cron`):**
Puedes añadir una tarea cron para ejecutar el script diariamente. Por ejemplo, para ejecutarlo todos los días a medianoche:

1.  Abre tu crontab para editarlo:
    ```bash
    crontab -e
    ```
2.  Añade una de las siguientes líneas, adaptándola a tu configuración y rutas:

    *   **Ejemplo general (si `python3` está en el PATH y es el intérprete correcto):**
        Reemplaza `/ruta/completa/a/tu/proyecto/` con la ruta absoluta a la raíz de este proyecto. Se recomienda también redirigir la salida a un archivo de log.
        ```cron
        0 0 * * * cd /ruta/completa/a/tu/proyecto/ && /usr/bin/python3 app/cleanup_images.py >> /ruta/completa/a/tu/proyecto/logs/cleanup.log 2>&1
        ```

    *   **Ejemplo usando un entorno virtual (común si usas `venv`):**
        Reemplaza `/ruta/completa/a/tu/proyecto/` con la ruta absoluta a la raíz de este proyecto.
        ```cron
        0 0 * * * cd /ruta/completa/a/tu/proyecto/ && /ruta/completa/a/tu/proyecto/venv/bin/python app/cleanup_images.py >> /ruta/completa/a/tu/proyecto/logs/cleanup.log 2>&1
        ```
        Este ejemplo asume que tu entorno virtual se llama `venv` y está en la raíz del proyecto. También redirige la salida estándar y los errores a un archivo de log llamado `cleanup.log` (asegúrate de que la carpeta `logs` exista o ajusta la ruta).

**Windows (usando el Programador de Tareas):**
1.  Busca "Programador de Tareas" en el menú de inicio.
2.  Crea una nueva tarea básica.
3.  Configura el desencadenador para que se ejecute diariamente a la hora deseada.
4.  Para la acción, configura "Iniciar un programa":
    *   En "Programa/script": la ruta completa a tu intérprete de Python (ej. `C:\ruta\a\tu\proyecto\venv\Scripts\python.exe`).
    *   En "Agregar argumentos (opcional)": la ruta completa al script (`app\cleanup_images.py`).
    *   En "Iniciar en (opcional)": la ruta completa a la raíz de tu proyecto (`C:\ruta\a\tu\proyecto\`).
Esto asegurará que el script se ejecute con las rutas correctas.
