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
    # Credenciales para la base de datos PostgreSQL (deben coincidir con docker-compose.yml)
    POSTGRES_USER=graphql_workshop
    POSTGRES_PASSWORD=secret
    POSTGRES_DB=graphql_workshop
    POSTGRES_HOST=graphql-workshop-postgres # Nombre del servicio de postgres en docker-compose
    POSTGRES_PORT=5432

    # Clave API de OpenAI
    OPENAI_API_KEY="tu_clave_api_de_openai"

    # Directorio para datos de la aplicación (opcional, para configurar rutas si es necesario)
    # APP_DATA_DIR="app/images" 

    DATABASE_URL="postgresql+asyncpg://graphql_workshop:secret@graphql-workshop-postgres:5432/graphql_workshop
    ```
    **Importante**: Reemplaza `"tu_clave_api_de_openai"` con tu clave API real de OpenAI.

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
