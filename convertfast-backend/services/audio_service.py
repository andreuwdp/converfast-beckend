from pathlib import Path
from fastapi import HTTPException
import subprocess

AUDIO_CODECS = {
    "mp3":  {"codec": "libmp3lame", "ext": "mp3"},
    "wav":  {"codec": "pcm_s16le",  "ext": "wav"},
    "flac": {"codec": "flac",       "ext": "flac"},
    "aac":  {"codec": "aac",        "ext": "aac"},
    "ogg":  {"codec": "libvorbis",  "ext": "ogg"},
    "m4a":  {"codec": "aac",        "ext": "m4a"},
    "opus": {"codec": "libopus",    "ext": "opus"},
}

QUALITY_BITRATES = {
    "low":     "64k",
    "medium":  "128k",
    "high":    "192k",
    "maximum": "320k",
}


def _run_ffmpeg(args: list, timeout: int = 120):
    """Esegue ffmpeg con gli argomenti specificati."""
    cmd = ["ffmpeg", "-y"] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            raise Exception(result.stderr[-500:] if result.stderr else "Errore ffmpeg")
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ffmpeg non trovato sul server.")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Conversione timeout.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore ffmpeg: {str(e)}")


def convert_audio(
    input_path: Path,
    output_path: Path,
    target_format: str = "mp3",
    quality: str = "high",
    channels: int = 2,
    sample_rate: int = 44100
) -> Path:
    """
    Converte un file audio in qualsiasi formato supportato.
    quality: low | medium | high | maximum
    """
    fmt_info = AUDIO_CODECS.get(target_format.lower())
    if not fmt_info:
        raise HTTPException(status_code=400, detail=f"Formato audio non supportato: {target_format}")

    bitrate = QUALITY_BITRATES.get(quality, "192k")
    codec = fmt_info["codec"]

    args = [
        "-i", str(input_path),
        "-acodec", codec,
        "-ab", bitrate,
        "-ac", str(channels),
        "-ar", str(sample_rate),
        str(output_path)
    ]

    # WAV e FLAC: lossless, non serve bitrate
    if target_format in ("wav", "flac"):
        args = [
            "-i", str(input_path),
            "-acodec", codec,
            "-ac", str(channels),
            "-ar", str(sample_rate),
            str(output_path)
        ]

    _run_ffmpeg(args)
    return output_path


def extract_audio_from_video(
    input_path: Path,
    output_path: Path,
    target_format: str = "mp3",
    quality: str = "high"
) -> Path:
    """
    Estrae la traccia audio da un file video.
    Usato per MP4→MP3, MOV→MP3, ecc.
    """
    fmt_info = AUDIO_CODECS.get(target_format.lower())
    if not fmt_info:
        raise HTTPException(status_code=400, detail=f"Formato audio non supportato: {target_format}")

    bitrate = QUALITY_BITRATES.get(quality, "192k")
    codec = fmt_info["codec"]

    args = [
        "-i", str(input_path),
        "-vn",              # rimuovi video
        "-acodec", codec,
        "-ab", bitrate,
        "-ar", "44100",
        "-ac", "2",
        str(output_path)
    ]

    if target_format in ("wav", "flac"):
        args = [
            "-i", str(input_path),
            "-vn",
            "-acodec", codec,
            str(output_path)
        ]

    _run_ffmpeg(args)
    return output_path


def trim_audio(
    input_path: Path,
    output_path: Path,
    start_seconds: float = 0,
    end_seconds: float = None
) -> Path:
    """Ritaglia un file audio tra start e end secondi."""
    args = ["-i", str(input_path), "-ss", str(start_seconds)]
    if end_seconds:
        duration = end_seconds - start_seconds
        args += ["-t", str(duration)]
    args += ["-acodec", "copy", str(output_path)]
    _run_ffmpeg(args)
    return output_path
