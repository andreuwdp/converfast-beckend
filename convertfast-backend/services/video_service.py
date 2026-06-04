from pathlib import Path
from fastapi import HTTPException
import subprocess

VIDEO_PRESETS = {
    "mp4":  {"vcodec": "libx264",  "acodec": "aac",        "ext": "mp4"},
    "webm": {"vcodec": "libvpx",   "acodec": "libvorbis",  "ext": "webm"},
    "mov":  {"vcodec": "libx264",  "acodec": "aac",        "ext": "mov"},
    "avi":  {"vcodec": "libx264",  "acodec": "aac",        "ext": "avi"},
    "mkv":  {"vcodec": "libx264",  "acodec": "aac",        "ext": "mkv"},
    "gif":  {"vcodec": None,       "acodec": None,         "ext": "gif"},
}

COMPRESS_CRF = {
    "low":    "28",   # più compresso
    "medium": "23",   # bilanciato (default ffmpeg)
    "high":   "18",   # alta qualità
}


def _run_ffmpeg(args: list, timeout: int = 300):
    cmd = ["ffmpeg", "-y"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            raise Exception(result.stderr[-800:] if result.stderr else "Errore ffmpeg")
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ffmpeg non trovato.")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Conversione timeout. File troppo grande.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore conversione video: {str(e)}")


def convert_video(
    input_path: Path,
    output_path: Path,
    target_format: str = "mp4",
    quality: str = "medium"
) -> Path:
    """Converte un video in un altro formato."""
    preset = VIDEO_PRESETS.get(target_format.lower())
    if not preset:
        raise HTTPException(status_code=400, detail=f"Formato video non supportato: {target_format}")

    crf = COMPRESS_CRF.get(quality, "23") if quality in COMPRESS_CRF else "23"

    if target_format == "gif":
        # GIF: palette ottimizzata
        palette = input_path.parent / "palette.png"
        _run_ffmpeg(["-i", str(input_path), "-vf", "fps=10,scale=480:-1:flags=lanczos,palettegen", str(palette)])
        _run_ffmpeg([
            "-i", str(input_path), "-i", str(palette),
            "-filter_complex", "fps=10,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse",
            str(output_path)
        ])
        if palette.exists():
            palette.unlink()
    else:
        args = [
            "-i", str(input_path),
            "-vcodec", preset["vcodec"],
            "-acodec", preset["acodec"],
            "-crf", crf,
            "-preset", "fast",
            "-movflags", "+faststart",
            str(output_path)
        ]
        _run_ffmpeg(args)

    return output_path


def compress_video(
    input_path: Path,
    output_path: Path,
    quality: str = "medium",
    resolution: str = None
) -> dict:
    """
    Comprime un video riducendo dimensione.
    resolution: None | "720p" | "480p" | "1080p"
    """
    original_size = input_path.stat().st_size
    crf = COMPRESS_CRF.get(quality, "23")

    vf_filters = []
    if resolution:
        res_map = {"1080p": "1920:1080", "720p": "1280:720", "480p": "854:480"}
        scale = res_map.get(resolution)
        if scale:
            vf_filters.append(f"scale={scale}:force_original_aspect_ratio=decrease")

    args = ["-i", str(input_path), "-vcodec", "libx264", "-acodec", "aac",
            "-crf", crf, "-preset", "fast", "-movflags", "+faststart"]

    if vf_filters:
        args += ["-vf", ",".join(vf_filters)]

    args.append(str(output_path))
    _run_ffmpeg(args)

    compressed_size = output_path.stat().st_size
    saved_pct = round((1 - compressed_size / original_size) * 100, 1)

    return {
        "original_size_bytes": original_size,
        "compressed_size_bytes": compressed_size,
        "saved_percent": max(0, saved_pct),
        "original_size_mb": round(original_size / (1024*1024), 2),
        "compressed_size_mb": round(compressed_size / (1024*1024), 2),
    }


def trim_video(
    input_path: Path,
    output_path: Path,
    start_seconds: float = 0,
    end_seconds: float = None
) -> Path:
    """Ritaglia un video tra start e end secondi."""
    args = ["-i", str(input_path), "-ss", str(start_seconds)]
    if end_seconds:
        args += ["-t", str(end_seconds - start_seconds)]
    args += ["-c", "copy", str(output_path)]
    _run_ffmpeg(args)
    return output_path
