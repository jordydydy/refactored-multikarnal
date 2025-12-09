from psycopg_pool import ConnectionPool
from contextlib import contextmanager
from app.core.config import settings
import logging

logger = logging.getLogger("db")

class Database:
    _pool: ConnectionPool = None

    @classmethod
    def initialize(cls):
        if cls._pool is None:
            logger.info("Initializing Database Connection Pool...")
            cls._pool = ConnectionPool(
                conninfo=(
                    f"dbname={settings.DB_NAME} "
                    f"user={settings.DB_USER} "
                    f"password={settings.DB_PASS} "
                    f"host={settings.DB_HOST} "
                    f"port={settings.DB_PORT}"
                ),
                min_size=1,
                max_size=10,
                timeout=30
            )

    @classmethod
    def close(cls):
        if cls._pool:
            cls._pool.close()

    @classmethod
    @contextmanager
    def get_connection(cls):
        if cls._pool is None:
            cls.initialize()
        
        with cls._pool.connection() as conn:
            yield conn

# Global function to be used by dependencies
def get_db_connection():
    with Database.get_connection() as conn:
        yield conn