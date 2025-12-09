import logging
from app.core.config import settings

def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Suppress noisy loggers if needed
    logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger("multikarnal")