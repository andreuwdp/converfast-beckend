import asyncio
import time
import os
from pathlib import Path
from config import TEMP_DIR, FILE_EXPIRY_HOURS

async def cleanup_old_files():
    """Elimina i file temporanei più vecchi di FILE_EXPIRY_HOURS ore."""
    now = time.time()
    expiry_seconds = FILE_EXPIRY_HOURS * 3600
    deleted = 0

    for f in TEMP_DIR.iterdir():
        if f.is_file():
            age = now - f.stat().st_mtime
            if age > expiry_seconds:
                try:
                    f.unlink()
                    deleted += 1
                except Exception:
                    pass

    if deleted:
        print(f"[Cleanup] Eliminati {deleted} file temporanei")

async def start_cleanup_scheduler():
    """Esegue la pulizia ogni 30 minuti."""
    while True:
        await asyncio.sleep(1800)  # 30 minuti
        await cleanup_old_files()
