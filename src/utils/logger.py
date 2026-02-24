import logging
from rich.logging import RichHandler

# Configure rich logger
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=True)]
)

logger = logging.getLogger("fivecross")
