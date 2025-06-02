# Proyecto GraphQL con Python y PostgreSQL

Este repositorio contiene una aplicación Python que utiliza GraphQL con Ariadne, SQLAlchemy para la interacción con una base de datos PostgreSQL, y OpenAI para la generación de imágenes. La aplicación está contenerizada utilizando Docker.
La aplicación ahora incluye funcionalidades para **visualización en múltiples pantallas**, permitiendo que diferentes clientes (pantallas) muestren imágenes generadas sin repeticiones en la misma pantalla y gestionando el estado de visualización de forma independiente para cada una.

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

4.  **Ejecuta la aplicación con Docker Compose:**
    Este comando construirá las imágenes de Docker (si no existen) y levantará los servicios definidos en `docker-compose.yml` (la aplicación Python y la base de datos PostgreSQL).
    ```bash
    docker-compose up
    ```
    Si deseas forzar la reconstrucción de las imágenes (por ejemplo, si has cambiado el `Dockerfile` o las dependencias en `requirements.txt`):
    ```bash
    docker-compose up --build
    ```

    La aplicación Python estará disponible en `http://localhost:8000`. La interfaz de GraphQL (GraphiQL) debería estar accesible en `http://localhost:8000/graphql`.

5.  **Acceso a la base de datos:**
    La base de datos PostgreSQL estará accesible en el puerto `5432` de tu máquina local, utilizando las credenciales definidas en el archivo `.env` y `docker-compose.yml`.

## Multi-Screen Viewing & Screen Registration

Para gestionar la visualización de imágenes en múltiples pantallas de forma independiente y evitar repeticiones en una misma pantalla, se han introducido los siguientes cambios y conceptos:

*   **Eliminación de `has_been_viewed`**: El campo booleano `has_been_viewed` que existía anteriormente en el modelo `FutureViewing` ha sido eliminado. El estado de visualización ya no es global para una imagen, sino específico para cada pantalla.
*   **Nuevos Modelos de Datos**:
    *   **`Screens`**: Esta tabla registra cada pantalla o cliente que interactúa con el sistema. Cada pantalla obtiene un ID único al registrarse.
        *   `id`: UUID, identificador único de la pantalla.
        *   `name`: String (opcional), nombre descriptivo para la pantalla (ej. "Lobby Izquierdo").
        *   `created_at`: DateTime, fecha y hora de registro.
    *   **`ScreenViewings`**: Esta tabla actúa como un registro de qué `FutureViewing` (imagen) ha sido mostrada en qué `Screen`. Cada vez que una pantalla obtiene una imagen a través de la query `recentFutureViewings`, se crea una entrada aquí.
        *   `id`: UUID, identificador único del evento de visualización.
        *   `future_viewing_id`: UUID, referencia a la imagen mostrada.
        *   `screen_id`: UUID, referencia a la pantalla donde se mostró.
        *   `viewed_at`: DateTime, fecha y hora de la visualización.
    Esto permite que cada pantalla consulte las imágenes que aún no ha mostrado, independientemente de otras pantallas.

## Ejemplos de Operaciones GraphQL

Puedes interactuar con la API GraphQL usando herramientas como Postman, Insomnia, o la interfaz GraphiQL que Ariadne proporciona en `http://localhost:8000/graphql`.

### Mutation: `registerScreen`

Esta mutación permite a un nuevo cliente/pantalla registrarse en el sistema para obtener un `screenId` único. Este ID es **esencial** para luego solicitar imágenes.

*   **Propósito**: Registrar una nueva pantalla/cliente.
*   **Input**: `RegisterScreenInput { name: String }` (el campo `name` es opcional).
*   **Output**: `RegisterScreenPayload { screen: Screen { id: ID!, name: String, createdAt: DateTime! } }`. El `id` devuelto en `screen.id` debe ser guardado por el cliente para usarlo como `screenId` en la query `recentFutureViewings`.

**Ejemplo (con nombre):**
```graphql
mutation {
  registerScreen(input: {name: "Lobby Principal"}) {
    screen {
      id
      name
      createdAt
    }
  }
}
```

**Ejemplo (sin nombre):**
```graphql
mutation {
  registerScreen(input: {}) { # El nombre es opcional
    screen {
      id
      createdAt 
    }
  }
}
```
**Respuesta Esperada (Ejemplo con nombre):**
```json
{
  "data": {
    "registerScreen": {
      "screen": {
        "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", // Este es el screenId a usar
        "name": "Lobby Principal",
        "createdAt": "YYYY-MM-DDTHH:MM:SS.ffffff"
      }
    }
  }
}
```

### Query: `recentFutureViewings` (Actualizada)

Esta query recupera una lista paginada de "future viewings" recientes que están completados y que **no han sido mostrados previamente en la pantalla especificada por `screenId`**.

*   **Propósito**: Obtener imágenes nuevas para una pantalla específica.
*   **Argumentos**:
    *   `screenId: ID!` (Obligatorio): El ID único de la pantalla (obtenido de la mutación `registerScreen`).
    *   `page: Int` (Opcional, por defecto: 1).
    *   `pageSize: Int` (Opcional, por defecto: 20).
*   **Output**: `[FutureViewing!]!` (Lista de objetos `FutureViewing`).

**Ejemplo:**
```graphql
query {
  recentFutureViewings(screenId: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", pageSize: 5) {
    id
    name
    imageUrl
    status # Debería ser COMPLETED
    createdAt
    # hasBeenViewed ya no existe
  }
}
```

**Respuesta Esperada (Ejemplo):**
```json
{
  "data": {
    "recentFutureViewings": [
      {
        "id": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
        "name": "Paisaje Futurista",
        "imageUrl": "/static/images/yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy.png",
        "status": "COMPLETED",
        "createdAt": "YYYY-MM-DDTHH:MM:SS.ffffff"
      }
      // ... más resultados si los hay
    ]
  }
}
```

### Mutation: `addFutureViewing`

Esta mutación crea un nuevo registro de "future viewing" y encola la generación de una imagen asociada.

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
      # hasBeenViewed ya no existe
    }
  }
}
```

**Respuesta Esperada (Ejemplo):**
```json
{
  "data": {
    "addFutureViewing": {
      "futureViewing": {
        "id": "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz",
        "name": "Robot Atardecer",
        "age": 1,
        "content": "Un robot melancólico observando un atardecer en un planeta alienígena, estilo cyberpunk",
        "createdAt": "YYYY-MM-DDTHH:MM:SS.ffffff",
        "status": "PENDING", // Inicialmente PENDING
        "imageUrl": null
      }
    }
  }
}
```
_(El `imageUrl` será `null` inicialmente y el `status` será `PENDING`. Se actualizarán cuando la imagen se genere y guarde correctamente)._

### Query: `futureViewings` (General)
Esta query recupera una lista paginada de todos los "future viewings", sin considerar el estado de visualización por pantalla. Puede ser útil para administración o una vista general.

```graphql
query {
  futureViewings(page: 1, pageSize: 5) {
    id
    name
    status
    imageUrl
    createdAt
    # hasBeenViewed ya no existe
  }
}
```

**Respuesta Esperada (Ejemplo):**
```json
{
  "data": {
    "futureViewings": [
      {
        "id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "name": "Robot Atardecer",
        "status": "COMPLETED",
        "imageUrl": "/static/images/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.png",
        "createdAt": "YYYY-MM-DDTHH:MM:SS.ffffff"
      }
      // ... más resultados
    ]
  }
}
```

## Flujo de Trabajo del Cliente (Pantalla)

1.  **Inicio de la Aplicación Cliente (Pantalla)**: La aplicación que mostrará las imágenes se inicia.
2.  **Registro de la Pantalla**:
    *   Al primer inicio, o si no tiene un `screenId` guardado, el cliente llama a la mutación `registerScreen`.
    *   Puede proporcionar un nombre opcional (ej. "Pantalla Lobby Puerta Norte").
    *   El cliente **debe guardar de forma persistente** el `screen.id` recibido en la respuesta. Este es su identificador único.
3.  **Solicitud de Imágenes**:
    *   El cliente utiliza el `screen.id` guardado para llamar periódicamente a la query `recentFutureViewings(screenId: "su-id-guardado", ...)`.
    *   El servidor devolverá una lista de imágenes que esta pantalla específica aún no ha mostrado.
    *   Internamente, el servidor registrará estas imágenes como "vistas" por esta pantalla en la tabla `ScreenViewings`.
4.  **Visualización**: El cliente muestra las imágenes recibidas.
Este flujo asegura que cada pantalla opere de manera independiente, mostrando un carrusel de imágenes sin repetir contenido ya mostrado en esa misma pantalla, y sin ser afectada por lo que otras pantallas hayan mostrado.

## Migraciones de Base de Datos (Alembic)

Este proyecto utiliza Alembic para gestionar y versionar los cambios en el esquema de la base de datos PostgreSQL.
### ¿Qué son las migraciones?

Las migraciones permiten:

- Crear y modificar tablas y columnas de manera controlada y reproducible.
- Mantener sincronizados todos los entornos (desarrollo, pruebas, producción) con la misma estructura de base de datos.
- Llevar un historial de todos los cambios realizados al esquema.

### ¿Cuándo crear una migración?

Cada vez que cambies tus modelos (por ejemplo, agregar/quitar campos o tablas), debes generar una nueva migración para reflejar esos cambios en la base de datos.

---

#### Resetear la Base y Crear una Migración Inicial

Si necesitas borrar toda la base (por ejemplo, para empezar de cero o porque la migración inicial está vacía o incorrecta), sigue estos pasos:
1. Borra todas las tablas de la base de datos

Esto elimina todo el esquema (¡y los datos!).

```bash
docker-compose exec graphql-workshop-postgres psql -U graphql_workshop -d graphql_workshop -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

2. Elimina las migraciones viejas

Esto borra los archivos de migraciones existentes (¡no borres la carpeta alembic/versions/, solo sus archivos!):

```bash
rm alembic/versions/*.py
```

3. Crea la migración inicial (detecta todas las tablas actuales de tus modelos)

```bash
alembic revision --autogenerate -m "migracion inicial"
```

4. Verifica que el archivo generado SÍ tenga instrucciones para crear tablas

Abre el archivo generado en alembic/versions/ y asegúrate de que contiene comandos como op.create_table(...), no solo pass.

```bash
cat alembic/versions/*.py
```

5. Aplica la migración

Esto creará todas las tablas en la base:

```bash
alembic upgrade head
```

6. Verifica las tablas en la base

Comprueba que la base ahora tiene las tablas correctas:

```bash
docker-compose exec graphql-workshop-postgres psql -U graphql_workshop -d graphql_workshop -c "\dt"
```

### 🚨 Notas importantes

- Solo elimina todo y vuelve a crear la migración inicial si NO tienes datos importantes que quieras conservar.

- Si ya existe historial de migraciones y datos en producción, nunca borres la base sin hacer respaldo.

- Si colaboras en equipo, versiona siempre tu carpeta alembic/versions/ en git.

### 🛠️ Migraciones en desarrollo

Cuando solo quieras agregar cambios nuevos (no reiniciar todo):

1. Modifica tus modelos.

2. Crea una migración:
```bash
alembic revision --autogenerate -m "describe tu cambio"
```
3. Aplica la migración:

```bash
alembic upgrade head
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
