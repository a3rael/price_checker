import sqlite3
from datetime import datetime
from pathlib import Path

import typer

from price_checker.http_parser import load_http_items
from price_checker.models import PriceItem, ProductRecord
from price_checker.parser import load_csv_items
from price_checker.pricing import count_suspicious_items, price_change_pct
from price_checker.storage import (
    count_products,
    create_products_table,
    load_product_records,
    save_items,
)


app = typer.Typer(help="Утилита для проверки прайс-листов из CSV и JSON по HTTP")


def run_pipeline(url, timeout) -> None:
    items, skipped_count = load_http_items(url, timeout)

    conn = sqlite3.connect("data/prices.db")
    try:
        create_products_table(conn)
        saved_count = save_items(conn, items)
        total_in_db = count_products(conn)
    finally:
        conn.close()

    suspicious_count = count_suspicious_items(items)

    typer.echo("Результат обработки")
    typer.echo("-" * 40)
    typer.echo(f"Получено элементов: {len(items)}")
    typer.echo(f"Изменено элементов: {saved_count}")
    typer.echo(f"Пропущено элементов: {skipped_count}")
    typer.echo(f"Всего элементов в БД: {total_in_db}")
    typer.echo(f"Подозрительных изменений: {suspicious_count}")


@app.callback()
def main() -> None:
    pass


def format_timestamp(timestamp: str) -> str:
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return timestamp

    timezone_name = parsed.tzname() or "UTC"
    return parsed.strftime("%Y-%m-%d %H:%M:%S ") + timezone_name


# Выводит итоговый отчёт по товарам с учётом фильтров и порога подозрительности.
def show_report(
    *,
    items: list[PriceItem],
    threshold: float = typer.Option(
        20.0,
    ),
    only_suspicious: bool = typer.Option(
        False,
    ),
    min_price: float = typer.Option(
        0.0,
    ),
) -> int:
    shown_count = 0

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

    return shown_count


def show_db_report(
    *,
    records: list[ProductRecord],
    threshold: float,
    only_suspicious: bool,
    min_price: float,
) -> int:
    shown_count = 0

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
            f"{change:.2f}%{mark}"
        )
        typer.echo(
            "created_at="
            f"{format_timestamp(record.created_at)} | "
            f"updated_at={format_timestamp(record.updated_at)}"
        )

        shown_count += 1

    typer.echo("-" * 60)
    typer.echo(f"Записей в БД: {len(records)}")
    typer.echo(f"Показано строк: {shown_count}")

    return shown_count


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

    if not csv_path.exists():
        typer.echo(f"Файл не найден: {csv_path}")
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
    run_pipeline(url, timeout=timeout)
    conn = sqlite3.connect("data/prices.db")
    try:
        records = load_product_records(conn)
    finally:
        conn.close()

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
