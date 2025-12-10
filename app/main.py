import threading
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.repositories.base import Database
from app.api.routes import router as api_router
from app.adapters.email.listener import start_email_listener
from app.services.scheduler import run_scheduler # [BARU] Import

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Database.initialize()
    
    if settings.EMAIL_PROVIDER != "unknown":
        email_thread = threading.Thread(target=start_email_listener, daemon=True)
        email_thread.start()

    scheduler_task = asyncio.create_task(run_scheduler())
    
    yield
    
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
        
    Database.close()

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/health")
def health():
    return {"status": "ok"}