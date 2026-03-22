from pathlib import Path
import logging

import typer

from price_checker.config import DEFAULT_LOG_LEVEL
from price_checker.logging_config import setup_logging
from price_checker.parser import load_csv_items
from price_checker.pipeline import (
    load_db_records,
    run_pipeline,
    show_db_report,
    show_report,
)

logger = logging.getLogger(__name__)
app = typer.Typer(help="Утилита для проверки прайс-листов из CSV и JSON по HTTP")


@app.callback()
def main(
    log_level: str = typer.Option(
        DEFAULT_LOG_LEVEL,
        "--log-level",
        help="Уровень логирования: DEBUG, INFO, WARNING, ERROR",
    ),
) -> None:
    setup_logging(log_level)
    logger.info("CLI запущен с уровнем логирования %s", log_level.upper())


# Загружает прайс из локального CSV-файла и показывает отчёт в консоли.
@app.command()
def check(
    path: str = typer.Argument(
        "data/prices.csv",
        help="Путь к CSV-файлу с данными о ценах",
    ),
    threshold: float = typer.Option(
        20.0,
        "--threshold",
        "-t",
        help="Пороговое значение для обнаружения подозрительных изменений",
    ),
    only_suspicious: bool = typer.Option(
        False,
        "--only-suspicious",
        help="Отображать только подозрительные изменения",
    ),
    min_price: float = typer.Option(
        0.0,
        "--min-price",
        help="Минимальная цена для отображения",
    ),
) -> None:
    csv_path = Path(path)
    logger.info("Запущена команда check для файла %s", csv_path)

    if not csv_path.exists():
        logger.error("Файл не найден: %s", csv_path)
        raise typer.Exit(code=1)

    items, skipped_count = load_csv_items(csv_path)

    typer.echo("Проверка прайс-листа")
    typer.echo(f"Файл: {csv_path}")
    typer.echo(f"Порог: {threshold:.2f}%")
    typer.echo(f"Минимальная цена: {min_price:.2f}")
    typer.echo("-" * 60)

    show_report(
        items=items,
        threshold=threshold,
        only_suspicious=only_suspicious,
        min_price=min_price,
    )


# Загружает прайс из JSON по URL и показывает такой же отчёт, как для CSV.
@app.command("check-url")
def check_url(
    url: str = typer.Argument(..., help="URL JSON-источника с данными о ценах"),
    threshold: float = typer.Option(
        20.0,
        "--threshold",
        "-t",
        help="Пороговое значение для обнаружения подозрительных изменений",
    ),
    only_suspicious: bool = typer.Option(
        False,
        "--only-suspicious",
        help="Отображать только подозрительные изменения",
    ),
    min_price: float = typer.Option(
        0.0,
        "--min-price",
        help="Минимальная цена для отображения",
    ),
    timeout: float = typer.Option(
        10.0,
        "--timeout",
        help="Таймаут HTTP-запроса в секундах",
    ),
) -> None:
    logger.info("Запущена команда check-url для %s", url)
    run_pipeline(url, timeout=timeout)
    records = load_db_records()
    typer.echo("Проверка прайс-листа")
    typer.echo(f"URL: {url}")
    typer.echo(f"Порог: {threshold:.2f}%")
    typer.echo(f"Минимальная цена: {min_price:.2f}")
    typer.echo(f"Таймаут: {timeout:.2f} сек")
    typer.echo("-" * 60)

    show_db_report(
        records=records,
        threshold=threshold,
        only_suspicious=only_suspicious,
        min_price=min_price,
    )


if __name__ == "__main__":
    app()
