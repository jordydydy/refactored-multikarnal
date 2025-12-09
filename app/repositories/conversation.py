from typing import Optional
from app.repositories.base import Database
from app.core.exceptions import DatabaseError
import logging

logger = logging.getLogger("repo.conversation")

class ConversationRepository:
    def get_active_id(self, platform_id: str, platform: str) -> Optional[str]:
        """
        Mencari conversation_id yang masih aktif (end_timestamp IS NULL).
        Menggantikan get_active_whatsapp/instagram_conversation_id.
        """
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, end_timestamp
                        FROM bkpm.conversations
                        WHERE platform_unique_id = %s AND platform = %s
                        ORDER BY start_timestamp DESC
                        LIMIT 1
                        """,
                        (platform_id, platform)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        conversation_id, end_timestamp = row
                        # Hanya kembalikan jika sesi belum berakhir
                        if end_timestamp is None:
                            return str(conversation_id)
            return None
        except Exception as e:
            logger.error(f"Error fetching active conversation: {e}")
            raise DatabaseError("Failed to fetch conversation")

    def get_latest_id(self, platform_id: str, platform: str) -> Optional[str]:
        """
        Mencari conversation_id terakhir, tidak peduli aktif/selesai.
        Digunakan untuk feedback.
        """
        try:
            with Database.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id
                        FROM bkpm.conversations
                        WHERE platform_unique_id = %s AND platform = %s
                        ORDER BY start_timestamp DESC
                        LIMIT 1
                        """,
                        (platform_id, platform)
                    )
                    row = cursor.fetchone()
                    return str(row[0]) if row else None
        except Exception as e:
            logger.error(f"Error fetching latest conversation: {e}")
            return None