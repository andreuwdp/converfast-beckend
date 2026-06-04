from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from utils.cleanup import start_cleanup_scheduler
from routers import images, documents, audio, video

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Avvia pulizia automatica file temp ogni 30 minuti
    task = asyncio.create_task(start_cleanup_scheduler())
    yield
    task.cancel()

app = FastAPI(
    title="ConvertFast API",
    description="API per conversione file online — PDF, immagini, video, audio, documenti",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione: metti il tuo dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router per ogni categoria
app.include_router(images.router,    prefix="/api/images",    tags=["Immagini"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documenti"])
app.include_router(audio.router,     prefix="/api/audio",     tags=["Audio"])
app.include_router(video.router,     prefix="/api/video",     tags=["Video"])

@app.get("/")
def root():
    return {"status": "ok", "message": "ConvertFast API attiva"}

@app.get("/health")
def health():
    return {"status": "healthy"}
