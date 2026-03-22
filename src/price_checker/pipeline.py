import sqlite3
from datetime import datetime
import logging

import typer

from price_checker.config import DEFAULT_DB_PATH
from price_checker.http_parser import load_http_items
from price_checker.models import PipelineResult, PriceItem, ProductRecord
from price_checker.pricing import count_suspicious_items, price_change_pct
from price_checker.storage import (
    count_products,
    create_products_table,
    load_product_records,
    save_items,
)

logger = logging.getLogger(__name__)


def run_pipeline(
    url: str, timeout: float, db_path: str = DEFAULT_DB_PATH
) -> PipelineResult:
    logger.info("Начинаем выполнение пайплайна")
    items, skipped_count = load_http_items(url, timeout)
    logger.info("Получено валидных %s строк, пропущено %s строк", len(items), skipped_count)

    conn = sqlite3.connect(db_path)
    try:
        logger.info("Подключение к БД установлено: %s", db_path)
        create_products_table(conn)
        logger.info("Таблица products готова")

        saved_count = save_items(conn, items)
        total_in_db = count_products(conn)
    finally:
        conn.close()
        logger.info("Соединение с БД закрыто")

    suspicious_count = count_suspicious_items(items)

    result = PipelineResult(
        received_count=len(items),
        valid_count=len(items),
        skipped_count=skipped_count,
        saved_count=saved_count,
        total_in_db=total_in_db,
        suspicious_count=suspicious_count,
    )
    logger.info("Пайплайн завершен успешно: %s", result)

    return result


def load_db_records(db_path: str = DEFAULT_DB_PATH) -> list[ProductRecord]:
    logger.info("Загружаем записи из БД %s", db_path)
    conn = sqlite3.connect(db_path)
    try:
        records = load_product_records(conn)
    finally:
        conn.close()

    logger.info("Записи из БД загружены: %s", len(records))
    return records


def format_timestamp(timestamp: str) -> str:
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        logger.warning("Не удалось преобразовать timestamp: %s", timestamp)
        return timestamp

    timezone_name = parsed.tzname() or "UTC"
    return parsed.strftime("%Y-%m-%d %H:%M:%S ") + timezone_name


def show_pipeline_summary(result: PipelineResult, threshold: float) -> None:
    logger.info("Показываем сводку пайплайна")
    typer.echo("Результат запуска пайплайна")
    typer.echo("-" * 40)
    typer.echo(f"Порог подозрительности: {threshold:.2f}%")
    typer.echo(f"Получено элементов: {result.received_count}")
    typer.echo(f"Валидных элементов: {result.valid_count}")
    typer.echo(f"Пропущено элементов: {result.skipped_count}")
    typer.echo(f"Сохранено элементов: {result.saved_count}")
    typer.echo(f"Всего записей в БД: {result.total_in_db}")
    typer.echo(f"Подозрительных изменений: {result.suspicious_count}")
    typer.echo("-" * 40)


def show_report(
    *,
    items: list[PriceItem],
    threshold: float,
    only_suspicious: bool,
    min_price: float,
) -> int:
    shown_count = 0
    logger.info("Формируем отчет по %s товарам", len(items))

    for item in items:
        change = price_change_pct(item.old_price, item.new_price)
        suspicious = abs(change) >= threshold

        if only_suspicious and not suspicious:
            continue
        if item.new_price < min_price:
            continue

        mark = " !!!" if suspicious else ""

        typer.echo(
            f"{item.sku} | {item.name} | "
            f"{item.old_price:.2f} -> {item.new_price:.2f} | "
            f"{change:.2f}%{mark}"
        )

        shown_count += 1

    typer.echo("-" * 60)
    typer.echo(f"Корректных строк: {len(items)}")
    typer.echo(f"Показано строк: {shown_count}")

    logger.info("Отчет по товарам сформирован, показано %s строк", shown_count)
    return shown_count


def show_db_report(
    *,
    records: list[ProductRecord],
    threshold: float,
    only_suspicious: bool,
    min_price: float,
) -> int:
    shown_count = 0
    logger.info("Формируем отчет по %s записям БД", len(records))

    for record in records:
        change = price_change_pct(record.old_price, record.new_price)
        suspicious = abs(change) >= threshold

        if only_suspicious and not suspicious:
            continue
        if record.new_price < min_price:
            continue

        mark = " !!!" if suspicious else ""

        typer.echo(
            f"{record.sku} | {record.name} | "
            f"{record.old_price:.2f} -> {record.new_price:.2f} | "
            f"{change:.2f}%{mark} | "
            f"Создано={format_timestamp(record.created_at)} | "
            f"Обновлено={format_timestamp(record.updated_at)}"
        )

        shown_count += 1

    typer.echo("-" * 60)
    typer.echo(f"Записей в БД: {len(records)}")
    typer.echo(f"Показано строк: {shown_count}")

    logger.info("Отчет по записям БД сформирован, показано %s строк", shown_count)
    return shown_count
