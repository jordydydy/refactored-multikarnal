import imaplib
import email
import time
import requests
import logging
from email.header import decode_header
from app.core.config import settings
from app.adapters.email.utils import sanitize_email_body
from app.repositories.message import MessageRepository

logger = logging.getLogger("email.listener")
repo = MessageRepository() # Instance untuk deduplikasi

def decode_str(header_val):
    if not header_val: return ""
    decoded_list = decode_header(header_val)
    text = ""
    for content, encoding in decoded_list:
        if isinstance(content, bytes):
            text += content.decode(encoding or "utf-8", errors="ignore")
        else:
            text += str(content)
    return text

def start_email_listener():
    """Loop utama polling email."""
    if not settings.EMAIL_USER or not settings.EMAIL_PASS:
        logger.warning("Email credentials not set. Listener stopped.")
        return

    logger.info(f"Starting IMAP Listener on {settings.EMAIL_HOST}...")
    
    while True:
        try:
            # 1. Connect IMAP
            mail = imaplib.IMAP4_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT)
            mail.login(settings.EMAIL_USER, settings.EMAIL_PASS)
            mail.select("INBOX")
            
            # 2. Search Unread
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            if email_ids:
                logger.info(f"Found {len(email_ids)} new emails.")
                
            for e_id in email_ids:
                # 3. Fetch Data
                _, msg_data = mail.fetch(e_id, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                msg_id = msg.get("Message-ID", "")
                
                # 4. Deduplikasi (Cek DB)
                if repo.is_processed(msg_id, "email"):
                    continue
                
                # 5. Parsing Content
                subject = decode_str(msg.get("Subject"))
                sender = decode_str(msg.get("From"))
                sender_email = sender.split('<')[-1].replace('>', '').strip() if '<' in sender else sender
                
                # Skip system emails
                if "mailer-daemon" in sender_email.lower() or "noreply" in sender_email.lower():
                    continue

                text_plain, html = "", ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            text_plain = part.get_payload(decode=True).decode(errors='ignore')
                        elif part.get_content_type() == "text/html":
                            html = part.get_payload(decode=True).decode(errors='ignore')
                else:
                    text_plain = msg.get_payload(decode=True).decode(errors='ignore')

                clean_body = sanitize_email_body(text_plain, html)
                if not clean_body: continue

                # 6. Kirim ke API Internal (Cara paling aman masuk ke Orchestrator)
                payload = {
                    "platform_unique_id": sender_email,
                    "query": clean_body,
                    "platform": "email",
                    "metadata": {
                        "subject": subject,
                        "in_reply_to": msg_id,
                        "references": msg.get("References", ""),
                        "sender_name": sender.split('<')[0].strip()
                    }
                }
                
                # Kirim ke localhost
                try:
                    # Asumsi server jalan di port 9798 sesuai Dockerfile lama
                    api_url = f"http://127.0.0.1:9798/api/messages/process" 
                    requests.post(api_url, json=payload, timeout=5)
                    logger.info(f"Email from {sender_email} processed.")
                except Exception as req_err:
                    logger.error(f"Failed to push email to API: {req_err}")

            mail.close()
            mail.logout()

        except Exception as e:
            logger.error(f"IMAP Loop Error: {e}")
        
        time.sleep(settings.EMAIL_POLL_INTERVAL_SECONDS)