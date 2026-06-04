import os
from pathlib import Path

# Directory file temporanei
TEMP_DIR = Path(__file__).parent.parent / "temp_files"
TEMP_DIR.mkdir(exist_ok=True)

# Limite dimensione file (100 MB default)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Ore prima che i file vengano eliminati
FILE_EXPIRY_HOURS = int(os.getenv("FILE_EXPIRY_HOURS", "1"))

# Formati accettati per categoria
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "image/gif", "image/bmp", "image/tiff"
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/quicktime", "video/x-msvideo",
    "video/x-matroska", "video/webm", "video/x-ms-wmv"
}

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg", "audio/wav", "audio/flac",
    "audio/aac", "audio/ogg", "audio/x-m4a"
}

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
