FROM python:3.11-slim

# Installa ffmpeg e LibreOffice
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libreoffice \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia codice
COPY . .

# Crea cartella file temporanei
RUN mkdir -p temp_files

# Espone porta 8000
EXPOSE 8000

# Avvia il server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
