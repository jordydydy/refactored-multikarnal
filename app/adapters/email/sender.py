import smtplib
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid
from app.core.config import settings
from app.adapters.base import BaseAdapter

logger = logging.getLogger("adapters.email")

class EmailAdapter(BaseAdapter):
    def send_typing_on(self, recipient_id: str):
        pass # Email tidak punya typing indicator

    def send_typing_off(self, recipient_id: str):
        pass

    def send_message(self, recipient_id: str, text: str, **kwargs):
        subject = kwargs.get("subject", "Re: Your Inquiry")
        in_reply_to = kwargs.get("in_reply_to")
        references = kwargs.get("references")
        
        # Format Body
        html_body = text.replace('\n', '<br>')
        formatted_body = (
            f"Dear Bapak/Ibu,<br><br>{html_body}<br><br>"
            "Regards,<br>Kementerian Investasi dan Hilirisasi/BKPM"
        )

        if settings.EMAIL_PROVIDER == "azure_oauth2":
            return self._send_via_graph(recipient_id, subject, formatted_body, in_reply_to)
        else:
            return self._send_via_smtp(recipient_id, subject, formatted_body, in_reply_to, references)

    def _send_via_smtp(self, to_email, subject, html_body, in_reply_to, references):
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USERNAME or settings.EMAIL_USER
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Message-ID'] = make_msgid()
            
            if in_reply_to: msg['In-Reply-To'] = in_reply_to
            if references: msg['References'] = references

            msg.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_USER, settings.EMAIL_PASS)
                server.send_message(msg)
            
            return {"sent": True, "message_id": msg['Message-ID']}
        except Exception as e:
            logger.error(f"SMTP Error: {e}")
            return {"sent": False, "error": str(e)}

    def _send_via_graph(self, to_email, subject, html_body, in_reply_to):
        # Implementasi Graph API Sender (disederhanakan)
        # Anda perlu memanggil 'get_oauth_token' dari utils jika ingin implementasi penuh
        # Untuk mempersingkat, saya beri kerangka logikanya:
        logger.warning("Graph API sending not fully implemented in this refactor snippet yet.")
        return {"sent": False, "error": "Graph API logic pending token implementation"}