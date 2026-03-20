from pathlib import Path

import typer

from price_checker.parser import load_items
from price_checker.pricing import price_change_pct

app = typer.Typer(help="Утилита для проверки прайс-листов в CSV")


@app.callback()
def main() -> None:
    pass


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

    items, skipped_count = load_items(csv_path)

    typer.echo("Проверка прайс-листа")
    typer.echo(f"Файл: {csv_path}")
    typer.echo(f"Порог: {threshold:.2f}%")
    typer.echo(f"Минимальная цена: {min_price:.2f}")
    typer.echo("-" * 60)

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


if __name__ == "__main__":
    app()
