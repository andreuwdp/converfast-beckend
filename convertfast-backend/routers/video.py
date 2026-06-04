from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from utils.files import save_upload, generate_output_path, file_response
from services.video_service import convert_video, compress_video, trim_video

router = APIRouter()

VIDEO_EXTS    = {"mp4", "mov", "avi", "mkv", "webm", "wmv", "flv", "3gp", "m4v", "mpeg", "mpg"}
TARGET_FMTS   = {"mp4", "mov", "avi", "mkv", "webm", "gif"}
QUALITIES     = {"low", "medium", "high"}
RESOLUTIONS   = {None, "480p", "720p", "1080p"}


@router.post("/convert")
async def api_convert_video(
    file: UploadFile = File(...),
    target_format: str = Form("mp4"),
    quality: str = Form("medium")
):
    """
    Converte un video in un altro formato.
    - target_format: mp4 | mov | avi | mkv | webm | gif
    - quality: low | medium | high
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in VIDEO_EXTS:
        raise HTTPException(status_code=400, detail=f"Formato video non supportato: .{ext}")

    if target_format not in TARGET_FMTS:
        raise HTTPException(status_code=400, detail=f"Formato output non valido: {target_format}")

    input_path = await save_upload(file)
    output_path = generate_output_path(target_format)

    try:
        convert_video(input_path, output_path, target_format, quality)
        return file_response(output_path, file.filename, target_format)
    finally:
        if input_path.exists():
            input_path.unlink()


@router.post("/compress")
async def api_compress_video(
    file: UploadFile = File(...),
    quality: str = Form("medium"),
    resolution: str = Form(None)
):
    """
    Comprime un video.
    - quality: low (più compresso) | medium | high
    - resolution: None | 480p | 720p | 1080p
    Risponde con il file + stats risparmio negli header.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in VIDEO_EXTS:
        raise HTTPException(status_code=400, detail=f"Formato video non supportato: .{ext}")

    if resolution and resolution not in {"480p", "720p", "1080p"}:
        resolution = None

    input_path = await save_upload(file)
    output_path = generate_output_path("mp4")  # output sempre MP4

    try:
        stats = compress_video(input_path, output_path, quality, resolution)
        response = file_response(output_path, file.filename, "mp4")
        response.headers["X-Original-Size"]    = str(stats["original_size_bytes"])
        response.headers["X-Compressed-Size"]  = str(stats["compressed_size_bytes"])
        response.headers["X-Saved-Percent"]    = str(stats["saved_percent"])
        return response
    finally:
        if input_path.exists():
            input_path.unlink()


@router.post("/trim")
async def api_trim_video(
    file: UploadFile = File(...),
    start_seconds: float = Form(0),
    end_seconds: float = Form(None)
):
    """Ritaglia un video tra start_seconds e end_seconds."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in VIDEO_EXTS:
        raise HTTPException(status_code=400, detail=f"Formato video non supportato: .{ext}")

    input_path = await save_upload(file)
    output_path = generate_output_path(ext)

    try:
        trim_video(input_path, output_path, start_seconds, end_seconds)
        return file_response(output_path, file.filename, ext)
    finally:
        if input_path.exists():
            input_path.unlink()
