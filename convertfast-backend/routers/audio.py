from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from utils.files import save_upload, generate_output_path, file_response
from services.audio_service import convert_audio, extract_audio_from_video, trim_audio

router = APIRouter()

AUDIO_EXTS  = {"mp3", "wav", "flac", "aac", "ogg", "m4a", "wma", "opus", "aiff", "amr"}
VIDEO_EXTS  = {"mp4", "mov", "avi", "mkv", "webm", "wmv", "flv", "3gp", "m4v"}
TARGET_FMTS = {"mp3", "wav", "flac", "aac", "ogg", "m4a", "opus"}
QUALITIES   = {"low", "medium", "high", "maximum"}


@router.post("/convert")
async def api_convert_audio(
    file: UploadFile = File(...),
    target_format: str = Form("mp3"),
    quality: str = Form("high"),
    channels: int = Form(2),
    sample_rate: int = Form(44100)
):
    """
    Converte un file audio in un altro formato.
    - target_format: mp3 | wav | flac | aac | ogg | m4a
    - quality: low | medium | high | maximum
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in AUDIO_EXTS:
        raise HTTPException(status_code=400, detail=f"Formato non supportato: .{ext}")

    if target_format not in TARGET_FMTS:
        raise HTTPException(status_code=400, detail=f"Formato output non valido: {target_format}")

    if quality not in QUALITIES:
        quality = "high"

    input_path = await save_upload(file)
    output_path = generate_output_path(target_format)

    try:
        convert_audio(input_path, output_path, target_format, quality, channels, sample_rate)
        return file_response(output_path, file.filename, target_format)
    finally:
        if input_path.exists():
            input_path.unlink()


@router.post("/extract-from-video")
async def api_extract_audio(
    file: UploadFile = File(...),
    target_format: str = Form("mp3"),
    quality: str = Form("high")
):
    """
    Estrae la traccia audio da un video.
    Supporta: MP4, MOV, AVI, MKV, WebM, WMV
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in VIDEO_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato video non supportato: .{ext}. Formati accettati: {', '.join(sorted(VIDEO_EXTS))}"
        )

    if target_format not in TARGET_FMTS:
        raise HTTPException(status_code=400, detail=f"Formato audio non valido: {target_format}")

    input_path = await save_upload(file)
    output_path = generate_output_path(target_format)

    try:
        extract_audio_from_video(input_path, output_path, target_format, quality)
        return file_response(output_path, file.filename, target_format)
    finally:
        if input_path.exists():
            input_path.unlink()


@router.post("/trim")
async def api_trim_audio(
    file: UploadFile = File(...),
    start_seconds: float = Form(0),
    end_seconds: float = Form(None)
):
    """Ritaglia un file audio tra start_seconds e end_seconds."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    input_path = await save_upload(file)
    output_path = generate_output_path(ext)

    try:
        trim_audio(input_path, output_path, start_seconds, end_seconds)
        return file_response(output_path, file.filename, ext)
    finally:
        if input_path.exists():
            input_path.unlink()
