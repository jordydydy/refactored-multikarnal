from fastapi import APIRouter, Depends, BackgroundTasks, Request, Query, Response, HTTPException
from app.core.config import settings
from app.schemas.models import IncomingMessage
from app.api.dependencies import get_orchestrator
from app.services.orchestrator import MessageOrchestrator
from app.services.parsers import parse_whatsapp_payload, parse_instagram_payload
import logging

logger = logging.getLogger("api.routes")
router = APIRouter()

# --- Verifikasi Webhook ---
@router.get("/whatsapp/webhook")
def verify_whatsapp(mode: str = Query(..., alias="hub.mode"), token: str = Query(..., alias="hub.verify_token"), challenge: str = Query(..., alias="hub.challenge")):
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.get("/instagram/webhook")
def verify_instagram(mode: str = Query(..., alias="hub.mode"), token: str = Query(..., alias="hub.verify_token"), challenge: str = Query(..., alias="hub.challenge")):
    if mode == "subscribe" and token == settings.INSTAGRAM_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

# --- Ingestion ---
@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request, bg_tasks: BackgroundTasks, orchestrator: MessageOrchestrator = Depends(get_orchestrator)):
    data = await request.json()
    msg = parse_whatsapp_payload(data)
    
    if msg:
        # Cek apakah ini feedback event?
        if msg.metadata and msg.metadata.get("is_feedback"):
            # Logic handle feedback (bisa tambah method di orchestrator)
            logger.info(f"Feedback received: {msg.metadata['payload']}")
            # orchestrator.handle_feedback(msg) # Implement if needed
        else:
            bg_tasks.add_task(orchestrator.process_message, msg)
            
    return {"status": "ok"}

@router.post("/instagram/webhook")
async def instagram_webhook(request: Request, bg_tasks: BackgroundTasks, orchestrator: MessageOrchestrator = Depends(get_orchestrator)):
    data = await request.json()
    msg = parse_instagram_payload(data)
    
    if msg:
        if msg.metadata and msg.metadata.get("is_feedback"):
            logger.info(f"Feedback received: {msg.metadata['payload']}")
        else:
            bg_tasks.add_task(orchestrator.process_message, msg)
            
    return {"status": "ok"}

# --- Internal Process Endpoint (Dipanggil oleh Email Listener) ---
@router.post("/api/messages/process")
async def process_message_internal(msg: IncomingMessage, bg_tasks: BackgroundTasks, orchestrator: MessageOrchestrator = Depends(get_orchestrator)):
    bg_tasks.add_task(orchestrator.process_message, msg)
    return {"status": "queued"}