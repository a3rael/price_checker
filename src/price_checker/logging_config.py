import logging

from price_checker.config import DEFAULT_LOG_LEVEL


def setup_logging(level: str = DEFAULT_LOG_LEVEL) -> None:
    logging.basicConfig(
        filename="price_checker.log",
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )
