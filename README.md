## Resumen ejecutivo

El servicio se basa en **ASP.NET 8 + Hot Chocolate GraphQL**, almacena datos en **PostgreSQL** y utiliza un **worker en
segundo plano** para generar imágenes con la API de OpenAI. Se provee un *docker-compose* para la base de datos y se
centralizan las credenciales en un archivo **`.env`**. Con los pasos descritos, un desarrollador sin experiencia previa
en C# o GraphQL podrá clonar, configurar y poner en marcha la aplicación de forma reproducible.

---

## 1. Prerrequisitos

| Software                                             | Versión mínima                                                             | Instalación                                                                       |
|------------------------------------------------------|----------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **.NET SDK**                                         | 8 LTS                                                                      | Descarga e instala desde la página oficial de .NET 8                              |
| **Docker Desktop** (incluye Docker Engine + Compose) | 4.x                                                                        | Instalador oficial para Windows, macOS o Linux                                    |
| **PostgreSQL**                                       | 15 +                                                                       | Se desplegará automáticamente con *docker-compose*; no requiere instalación local |
| **IDE recomendado**                                  | Visual Studio 2022 Community (Windows) o JetBrains Rider Community Edition | VS Community: descarga gratuita  · Rider: descarga multiplataforma                |
| **Git**                                              | Última estable                                                             | https://git-scm.com                                                               |

> **Nota:** si utilizas WSL 2 o Linux nativo, las mismas versiones de SDK y Docker son válidas.

---

## 2. Descarga del proyecto

```bash
git clone https://github.com/lfeq/Graph-QL-Test.git
cd Graph-QL-Test
```

---

## 3. Configuración de variables de entorno

Crea un archivo **`.env`** en la raíz del proyecto (mismo nivel que `docker-compose.yml`) con el siguiente contenido de
ejemplo:

```dotenv
# Clave de OpenAI: indispensable para generar imágenes
OPENAI_API_KEY=sk-**********************
```

La librería **DotNetEnv** cargará automáticamente estas variables en tiempo de ejecución .

---

## 4. Puesta en marcha de la base de datos

```bash
docker compose up -d
```

El comando levanta el contenedor `graphql-workshop-postgres`, expuesto en el puerto 5432 con las credenciales definidas
en el *compose* .

---

## 5. Restaurar dependencias y compilar

### Opción A — Línea de comandos

```bash
dotnet restore          # descarga paquetes NuGet
dotnet build -c Release # compila la solución
```

### Opción B — IDE

1. Abrir la carpeta del proyecto en Visual Studio o Rider.
2. Esperar a que se complete la restauración automática de NuGet.
3. Seleccionar configuración **Release** y compilar.

---

## 6. Ejecución del servicio

```bash
dotnet run -c Release
```

Por defecto la API escucha en `http://localhost:5000`. Hot Chocolate expone la interfaz gráfica **Nitro (antes Banana
Cake Pop)** en `http://localhost:5000/graphql`, donde es posible explorar el esquema y ejecutar consultas o mutaciones
sin herramientas externas .

---

## 7. Prueba rápida

1. Navega a `http://localhost:5000/graphql`.

2. Para generar una imagen, usa la mutación:

```graphql
mutation {
  addFutureViewing(input:{
    name: "María López"
    age: 28
    content: "Retrato estilo acuarela con tonos pastel"
  }) {
    futureViewing {
      id
      status
    }
  }
}
```
El **worker en segundo plano** tomará el trabajo de la cola y, tras unos segundos, actualizará el registro a
`status: Completed` y guardará la imagen en `wwwroot/images/{id}.png`.

3. Para ver las imagenes puedes hacer la consulta:

```graphql
query {
  futureViewings(page: 1, pageSize: 10) { # You can also override the default pageSize
    id
    name
    createdAt
    age
    imageUrl
    content
    status
  }
}
```

### Pruebas usando otra cosa que no es localhost

Puedes correr `ipconfig` en la terminal para ver tu IP local.
e ir a `http://<tu-ip>:5000/graphql` para acceder a la API.

---

## 8. Costos de operación

- Cada imagen de 1024×1024 píxeles generada con DALL·E 3 tiene un costo aproximado de **USD $0.04** .
- El servicio hace una llamada por mutación, por lo que el costo está directamente relacionado con el número de
  solicitudes.

---

## 9. Detención y mantenimiento

```bash
# Apagar la API (Ctrl-C) y la base de datos
docker compose down
```

Para aplicar migraciones de Entity Framework (si las añades más adelante):

```bash
dotnet ef migrations add NombreMigracion
dotnet ef database update
```

(Instala la herramienta EF CLI con `dotnet tool install --global dotnet-ef` si fuera necesario).

---

## 10. Solución de problemas comunes

| Síntoma                                 | Posible causa                                             | Acción sugerida                                                               |
|-----------------------------------------|-----------------------------------------------------------|-------------------------------------------------------------------------------|
| Error al resolver `OPENAI_API_KEY`      | `.env` no cargado o clave vacía                           | Verifica el archivo `.env` y reinicia la API                                  |
| `Cannot connect to host 127.0.0.1:5432` | Docker no está corriendo o el contenedor falla al iniciar | Ejecuta `docker compose ps -a` y revisa los logs con `docker compose logs -f` |
| `status: Failed` en la imagen           | Clave de OpenAI inválida o cuota agotada                  | Confirma la validez de la clave y el estado de tu cuenta                      |

---