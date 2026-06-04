from PIL import Image
from pathlib import Path
from fastapi import HTTPException

def convert_image(input_path: Path, output_path: Path, target_format: str, quality: int = 85) -> Path:
    """
    Converte un'immagine nel formato target.
    Supporta: jpg, jpeg, png, webp, gif, bmp, tiff
    """
    fmt_map = {
        "jpg": "JPEG", "jpeg": "JPEG",
        "png": "PNG", "webp": "WEBP",
        "gif": "GIF", "bmp": "BMP",
        "tiff": "TIFF", "tif": "TIFF"
    }

    pil_format = fmt_map.get(target_format.lower())
    if not pil_format:
        raise HTTPException(status_code=400, detail=f"Formato non supportato: {target_format}")

    try:
        img = Image.open(input_path)

        # Converti RGBA → RGB per JPEG (non supporta trasparenza)
        if pil_format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif pil_format != "JPEG" and img.mode == "P":
            img = img.convert("RGBA")

        save_kwargs = {}
        if pil_format == "JPEG":
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif pil_format == "WEBP":
            save_kwargs["quality"] = quality
            save_kwargs["method"] = 6
        elif pil_format == "PNG":
            save_kwargs["optimize"] = True

        img.save(output_path, format=pil_format, **save_kwargs)
        return output_path

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore conversione immagine: {str(e)}")


def compress_image(input_path: Path, output_path: Path, quality: int = 80) -> dict:
    """
    Comprime un'immagine JPG o PNG.
    Ritorna info su dimensioni originali e compresse.
    """
    original_size = input_path.stat().st_size

    try:
        img = Image.open(input_path)
        fmt = img.format or "JPEG"

        if fmt == "PNG":
            # PNG: comprimi con ottimizzazione lossless
            img.save(output_path, format="PNG", optimize=True, compress_level=9)
        else:
            # JPEG: comprimi con qualità ridotta
            if img.mode in ("RGBA", "LA", "P"):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = bg
            img.save(output_path, format="JPEG", quality=quality, optimize=True)

        compressed_size = output_path.stat().st_size
        saved_pct = round((1 - compressed_size / original_size) * 100, 1)

        return {
            "original_size_bytes": original_size,
            "compressed_size_bytes": compressed_size,
            "saved_percent": max(0, saved_pct),
            "original_size_mb": round(original_size / (1024*1024), 2),
            "compressed_size_mb": round(compressed_size / (1024*1024), 2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore compressione: {str(e)}")


def resize_image(input_path: Path, output_path: Path,
                 width: int = None, height: int = None,
                 keep_ratio: bool = True) -> Path:
    """Ridimensiona un'immagine."""
    try:
        img = Image.open(input_path)
        orig_w, orig_h = img.size

        if keep_ratio:
            if width and not height:
                ratio = width / orig_w
                height = int(orig_h * ratio)
            elif height and not width:
                ratio = height / orig_h
                width = int(orig_w * ratio)

        if not width or not height:
            raise HTTPException(status_code=400, detail="Specifica almeno width o height.")

        img_resized = img.resize((width, height), Image.LANCZOS)
        fmt = img.format or "JPEG"
        save_kwargs = {"quality": 90} if fmt == "JPEG" else {}
        img_resized.save(output_path, format=fmt, **save_kwargs)
        return output_path

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ridimensionamento: {str(e)}")
