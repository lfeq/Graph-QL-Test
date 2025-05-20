# Usa una imagen base de Python oficial
FROM python:3.10-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de requerimientos primero para aprovechar el cache de Docker
COPY requirements.txt requirements.txt

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos de la aplicación al directorio de trabajo
COPY . .

# Crea el directorio para imágenes estáticas si no existe
# (Aunque docker-compose lo montará, es bueno tenerlo en la imagen)
RUN mkdir -p /app/static/images

# Expone el puerto en el que la aplicación correrá
EXPOSE 8000

# El comando para ejecutar la aplicación será especificado en docker-compose.yml
# para facilitar el desarrollo con --reload. Para producción, podrías tenerlo aquí:
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]