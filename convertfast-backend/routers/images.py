from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from utils.files import save_upload, generate_output_path, file_response
from services.image_service import convert_image, compress_image, resize_image

router = APIRouter()

ALLOWED_EXTS = {"jpg", "jpeg", "png", "webp", "gif", "bmp", "tiff", "tif"}


@router.post("/convert")
async def api_convert_image(
    file: UploadFile = File(...),
    target_format: str = Form("png"),
    quality: int = Form(85)
):
    """
    Converte un'immagine nel formato target.
    - target_format: jpg | png | webp | gif | bmp | tiff
    - quality: 1-100 (usato per JPEG e WebP)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Formato non supportato: .{ext}")

    input_path = await save_upload(file)
    output_path = generate_output_path(target_format)

    try:
        convert_image(input_path, output_path, target_format, quality)
        return file_response(output_path, file.filename, target_format)
    finally:
        if input_path.exists():
            input_path.unlink()


@router.post("/compress")
async def api_compress_image(
    file: UploadFile = File(...),
    quality: int = Form(80)
):
    """
    Comprime un'immagine JPG o PNG.
    - quality: 1-100 (80 = bilanciato, 60 = massima compressione)
    Risponde con il file compresso + info sul risparmio.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"jpg", "jpeg", "png"}:
        raise HTTPException(status_code=400, detail="Comprimi supporta solo JPG e PNG.")

    input_path = await save_upload(file)
    output_path = generate_output_path(ext)

    try:
        stats = compress_image(input_path, output_path, quality)
        # Aggiungi le stats come header
        response = file_response(output_path, file.filename, ext)
        response.headers["X-Original-Size"] = str(stats["original_size_bytes"])
        response.headers["X-Compressed-Size"] = str(stats["compressed_size_bytes"])
        response.headers["X-Saved-Percent"] = str(stats["saved_percent"])
        return response
    finally:
        if input_path.exists():
            input_path.unlink()


@router.post("/resize")
async def api_resize_image(
    file: UploadFile = File(...),
    width: int = Form(None),
    height: int = Form(None),
    keep_ratio: bool = Form(True)
):
    """
    Ridimensiona un'immagine.
    Specifica width e/o height in pixel.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")

    if not width and not height:
        raise HTTPException(status_code=400, detail="Specifica almeno width o height.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    input_path = await save_upload(file)
    output_path = generate_output_path(ext)

    try:
        resize_image(input_path, output_path, width, height, keep_ratio)
        return file_response(output_path, file.filename, ext)
    finally:
        if input_path.exists():
            input_path.unlink()
