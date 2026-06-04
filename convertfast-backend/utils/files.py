import uuid
import os
from pathlib import Path
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from config import TEMP_DIR, MAX_FILE_SIZE_BYTES

def generate_output_path(extension: str) -> Path:
    """Genera un percorso univoco per il file di output."""
    filename = f"{uuid.uuid4().hex}.{extension.lstrip('.')}"
    return TEMP_DIR / filename

async def save_upload(file: UploadFile) -> Path:
    """Salva il file uploadato in temp_files e ritorna il percorso."""
    content = await file.read()

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File troppo grande. Massimo {MAX_FILE_SIZE_BYTES // (1024*1024)} MB."
        )

    ext = Path(file.filename).suffix or ".tmp"
    input_path = TEMP_DIR / f"{uuid.uuid4().hex}_input{ext}"
    input_path.write_bytes(content)
    return input_path

def file_response(output_path: Path, original_name: str, new_ext: str) -> FileResponse:
    """Ritorna il file convertito come download."""
    stem = Path(original_name).stem
    download_name = f"{stem}_convertfast.{new_ext.lstrip('.')}"
    return FileResponse(
        path=str(output_path),
        filename=download_name,
        media_type="application/octet-stream"
    )

def validate_extension(filename: str, allowed: set) -> str:
    """Valida l'estensione del file."""
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Formato non supportato: .{ext}. Formati accettati: {', '.join(sorted(allowed))}"
        )
    return ext
