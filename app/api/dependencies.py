from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.services.chatbot import ChatbotClient
from app.services.orchestrator import MessageOrchestrator
from app.adapters.whatsapp import WhatsAppAdapter
from app.adapters.instagram import InstagramAdapter
from app.adapters.email.sender import EmailAdapter

# Singleton Instances
_wa_adapter = WhatsAppAdapter()
_ig_adapter = InstagramAdapter()
_email_adapter = EmailAdapter()
_chatbot_client = ChatbotClient()
_repo_conv = ConversationRepository()
_repo_msg = MessageRepository()

def get_orchestrator() -> MessageOrchestrator:
    adapters = {
        "whatsapp": _wa_adapter,
        "instagram": _ig_adapter,
        "email": _email_adapter
    }
    return MessageOrchestrator(
        repo_conv=_repo_conv,
        repo_msg=_repo_msg,
        chatbot=_chatbot_client,
        adapters=adapters
    )