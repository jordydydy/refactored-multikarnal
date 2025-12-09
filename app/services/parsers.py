from typing import Dict, Any, Optional, Tuple
from app.schemas.models import IncomingMessage

def parse_whatsapp_payload(data: Dict[str, Any]) -> Optional[IncomingMessage]:
    """Ekstrak pesan dari JSON WhatsApp Cloud API."""
    try:
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        
        # Cek jika ini pesan (bukan status update)
        if "messages" not in value:
            return None
            
        message = value["messages"][0]
        msg_type = message.get("type")
        sender_id = message.get("from")
        
        # Handle Text Message
        if msg_type == "text":
            return IncomingMessage(
                platform_unique_id=sender_id,
                query=message["text"]["body"],
                platform="whatsapp",
                metadata={"phone": sender_id}
            )
            
        # Handle Button Reply (Feedback)
        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                btn_id = interactive["button_reply"]["id"]
                # Format ID: feedback_good-123
                return IncomingMessage(
                    platform_unique_id=sender_id,
                    query=f"FEEDBACK_EVENT:{btn_id}", # Query khusus untuk ditangkap logic nanti
                    platform="whatsapp",
                    metadata={"is_feedback": True, "payload": btn_id}
                )
                
    except (IndexError, KeyError, AttributeError):
        pass
    return None

def parse_instagram_payload(data: Dict[str, Any]) -> Optional[IncomingMessage]:
    """Ekstrak pesan dari JSON Instagram Webhook."""
    try:
        entry = data.get("entry", [])[0]
        messaging = entry.get("messaging", [])[0]
        
        sender_id = messaging.get("sender", {}).get("id")
        message = messaging.get("message", {})
        
        # Handle Text
        if "text" in message:
            return IncomingMessage(
                platform_unique_id=sender_id,
                query=message["text"],
                platform="instagram"
            )
            
        # Handle Quick Reply (Feedback)
        if "quick_reply" in message:
            payload = message["quick_reply"].get("payload")
            return IncomingMessage(
                platform_unique_id=sender_id,
                query=f"FEEDBACK_EVENT:{payload}",
                platform="instagram",
                metadata={"is_feedback": True, "payload": payload}
            )
            
    except (IndexError, KeyError, AttributeError):
        pass
    return None