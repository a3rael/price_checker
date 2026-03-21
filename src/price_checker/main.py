from pathlib import Path

import typer

from price_checker.http_parser import load_http_items
from price_checker.models import PriceItem
from price_checker.parser import load_csv_items
from price_checker.pricing import price_change_pct

app = typer.Typer(help="Утилита для проверки прайс-листов из CSV и JSON по HTTP")


@app.callback()
def main() -> None:
    pass


# Выводит итоговый отчёт по товарам с учётом фильтров и порога подозрительности.
def show_report(
    *,
    items: list[PriceItem],
    skipped_count: int,
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
    typer.echo(f"Пропущено строк: {skipped_count}")
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
        skipped_count=skipped_count,
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
    items, skipped_count = load_http_items(url, timeout=timeout)

    typer.echo("Проверка прайс-листа")
    typer.echo(f"URL: {url}")
    typer.echo(f"Порог: {threshold:.2f}%")
    typer.echo(f"Минимальная цена: {min_price:.2f}")
    typer.echo(f"Таймаут: {timeout:.2f} сек")
    typer.echo("-" * 60)

    show_report(
        items=items,
        skipped_count=skipped_count,
        threshold=threshold,
        only_suspicious=only_suspicious,
        min_price=min_price,
    )


if __name__ == "__main__":
    app()
