import asyncio
from typing import Dict
from app.schemas.models import IncomingMessage
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.services.chatbot import ChatbotClient
from app.adapters.base import BaseAdapter
import logging

logger = logging.getLogger("service.orchestrator")

class MessageOrchestrator:
    def __init__(
        self, 
        repo_conv: ConversationRepository,
        repo_msg: MessageRepository,
        chatbot: ChatbotClient,
        adapters: Dict[str, BaseAdapter]
    ):
        self.repo_conv = repo_conv
        self.repo_msg = repo_msg
        self.chatbot = chatbot
        self.adapters = adapters

    async def process_message(self, msg: IncomingMessage):
        """Alur utama pemrosesan pesan."""
        
        # 1. Pilih Adapter
        adapter = self.adapters.get(msg.platform)
        if not adapter:
            logger.warning(f"No adapter found for platform: {msg.platform}")
            return

        # 2. Cek Duplikasi (Idempotency) - Khusus Email biasanya penting
        # Untuk WA/IG, kadang webhook dikirim ulang oleh Meta jika timeout
        # Implementasi logic deduplikasi pesan spesifik di sini jika perlu.
        
        # 3. Typing Indicator
        try:
            adapter.send_typing_on(msg.platform_unique_id)
        except Exception:
            pass

        # 4. Resolve Conversation ID
        if not msg.conversation_id:
            msg.conversation_id = self.repo_conv.get_active_id(msg.platform_unique_id, msg.platform)

        # 5. Kirim ke Chatbot (dengan Timeout handling manual jika perlu feedback cepat)
        # Kita pakai task terpisah untuk timeout message "Mohon menunggu..."
        
        chatbot_task = asyncio.create_task(
            self.chatbot.ask(msg.query, msg.conversation_id, msg.platform, msg.platform_unique_id)
        )
        
        try:
            # Tunggu respon AI max 60 detik (atau setting lain)
            response = await chatbot_task
        except Exception as e:
            logger.error(f"Critical error during chatbot processing: {e}")
            response = None

        # 6. Matikan Typing Indicator
        try:
            adapter.send_typing_off(msg.platform_unique_id)
        except Exception:
            pass

        if not response or not response.answer:
            return # Silent fail atau kirim pesan error generic

        # 7. Kirim Balasan ke User
        # Khusus Email: Perlu metadata subject & reply chain
        send_kwargs = {}
        if msg.platform == "email":
            # Ambil metadata dari pesan masuk atau DB
            meta = self.repo_msg.get_email_metadata(response.conversation_id or msg.conversation_id)
            if meta:
                send_kwargs = meta
            # Fallback ke metadata pesan masuk jika DB kosong (session baru)
            elif msg.metadata:
                send_kwargs = {
                    "subject": msg.metadata.get("subject"),
                    "in_reply_to": msg.metadata.get("in_reply_to"),
                    "references": msg.metadata.get("references")
                }

        # Kirim!
        adapter.send_message(msg.platform_unique_id, response.answer, **send_kwargs)

        # 8. Feedback Buttons (Khusus WA/IG)
        # Cek apakah respon ini butuh feedback (misal ada answer_id valid)
        raw_data = response.raw.get("data", {}) if response.raw else {}
        answer_id = raw_data.get("answer_id")
        
        if answer_id:
            adapter.send_feedback_request(msg.platform_unique_id, answer_id)
            
        # 9. Simpan Metadata Email Baru (jika ada conversation_id baru dari AI)
        if msg.platform == "email" and response.conversation_id and msg.metadata:
            self.repo_msg.save_email_metadata(
                response.conversation_id,
                msg.metadata.get("subject", ""),
                msg.metadata.get("in_reply_to", ""),
                msg.metadata.get("references", ""),
                msg.metadata.get("thread_key", "")
            )