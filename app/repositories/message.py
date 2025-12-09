from typing import Optional, Dict
from app.repositories.base import Database
import logging

logger = logging.getLogger("repo.message")

class MessageRepository:
    def is_processed(self, message_id: str, platform: str) -> bool:
        """
        Mengecek apakah pesan sudah pernah diproses sebelumnya (Deduplikasi).
        Returns: True jika SUDAH diproses (skip), False jika BELUM (proses).
        """
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Pastikan tabel ada
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS bkpm.processed_messages (
                            message_id TEXT NOT NULL,
                            platform TEXT NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (message_id, platform)
                        );
                    """)
                    
                    # Coba insert. Jika konflik (sudah ada), return True (is processed)
                    cursor.execute(
                        """
                        INSERT INTO bkpm.processed_messages (message_id, platform)
                        VALUES (%s, %s)
                        ON CONFLICT (message_id, platform) DO NOTHING
                        """,
                        (message_id, platform)
                    )
                    
                    # Jika rowcount > 0, berarti insert sukses (pesan baru -> belum diproses)
                    is_new = cursor.rowcount > 0
                    conn.commit()
                    return not is_new  # Return True jika SUDAH ada

        except Exception as e:
            logger.error(f"Deduplication check failed for {message_id}: {e}")
            return False  # Fail-open: kalau DB error, anggap pesan baru agar tetap diproses

    def save_email_metadata(self, conversation_id: str, subject: str, in_reply_to: str, references: str, thread_key: str):
        """Menyimpan metadata email agar reply bot masuk ke thread yang benar."""
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO bkpm.email_metadata (conversation_id, subject, in_reply_to, "references", thread_key)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (conversation_id) DO NOTHING
                        """,
                        (conversation_id, subject, in_reply_to, references, thread_key)
                    )
                    conn.commit()
        except Exception as e:
            logger.error(f"Failed to save email metadata: {e}")

    def get_email_metadata(self, conversation_id: str) -> Optional[Dict[str, str]]:
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT subject, in_reply_to, "references", thread_key
                        FROM bkpm.email_metadata
                        WHERE conversation_id = %s
                        LIMIT 1
                        """,
                        (conversation_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        return {
                            "subject": row[0],
                            "in_reply_to": row[1],
                            "references": row[2],
                            "thread_key": row[3]
                        }
            return None
        except Exception as e:
            logger.error(f"Failed to get email metadata: {e}")
            return None

    def get_latest_answer_id(self, conversation_id: str) -> Optional[int]:
        """Mengambil ID jawaban terakhir chatbot untuk keperluan feedback."""
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id
                        FROM bkpm.chat_history
                        WHERE session_id = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (conversation_id,)
                    )
                    row = cursor.fetchone()
                    return int(row[0]) if row else None
        except Exception as e:
            logger.warning(f"No answer history found for {conversation_id}: {e}")
            return None