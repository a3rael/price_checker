import csv
import pathlib

import price_checker.models as models
import typer


class RowValidationError(Exception):
    pass


def parse_row_data(row) -> dict[str, str | float]:
    try:
        sku = row["sku"]
        name = row["name"]
        old_price = float(row["old_price"])
        new_price = float(row["new_price"])
    except KeyError as e:
        raise RowValidationError(f"Отсутствует обязательное поле: {e}")
    except ValueError:
        raise RowValidationError("Цена должна быть числом")

    return {
        "sku": sku,
        "name": name,
        "old_price": old_price,
        "new_price": new_price,
    }


def validate_row_data(
    *, sku: str, name: str, old_price: float, new_price: float
) -> None:
    if not sku:
        raise RowValidationError("SKU не может быть пустым")

    if not name:
        raise RowValidationError("Название товара не может быть пустым")

    if old_price < 0:
        raise RowValidationError("old_price не может быть отрицательной")

    if old_price == 0:
        raise RowValidationError("old_price не может быть равен 0")

    if new_price < 0:
        raise RowValidationError("new_price не может быть отрицательной")


def parse_row(row) -> models.PriceItem:
    parsed_data = parse_row_data(row)
    validate_row_data(**parsed_data)

    return models.PriceItem(
        sku=parsed_data["sku"],
        name=parsed_data["name"],
        old_price=parsed_data["old_price"],
        new_price=parsed_data["new_price"],
    )


def load_items(
    csv_path: pathlib.Path,
) -> tuple[list[models.PriceItem], int]:
    items: list[models.PriceItem] = []
    skipped_count = 0

    try:
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for index, row in enumerate(reader, start=2):
                try:
                    item = parse_row(row)
                except RowValidationError as e:
                    typer.echo(f"Строка {index} пропущена: {e}")
                    skipped_count += 1
                    continue

                items.append(item)
    except FileNotFoundError:
        typer.echo(f"Файл не найден: {csv_path}")
        return []

    return items, skipped_count
