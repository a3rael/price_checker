import csv
import logging
import pathlib

import price_checker.models as models

logger = logging.getLogger(__name__)


class RowValidationError(Exception):
    pass


# Достаёт поля из строки CSV и приводит цены к числам.
def parse_row_data(row) -> dict[str, str | float]:
    logger.debug("Разбираем строку CSV: %s", row)
    try:
        sku = row["sku"]
        name = row["name"]
        old_price = float(row["old_price"])
        new_price = float(row["new_price"])
    except KeyError as e:
        logger.warning("Отсутствует обязательное поле в CSV: %s", e)
        raise RowValidationError(f"Отсутствует обязательное поле: {e}")
    except ValueError:
        logger.warning("Цена в CSV не является числом: %s", row)
        raise RowValidationError("Цена должна быть числом")

    return {
        "sku": sku,
        "name": name,
        "old_price": old_price,
        "new_price": new_price,
    }


# Проверяет бизнес-правила для одной строки с ценами.
def validate_row_data(
    *, sku: str, name: str, old_price: float, new_price: float
) -> None:
    logger.debug("Валидируем строку товара sku=%s", sku)
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


# Объединяет разбор и валидацию строки, затем создаёт PriceItem.
def parse_row(row) -> models.PriceItem:
    parsed_data = parse_row_data(row)
    validate_row_data(**parsed_data)
    logger.debug("PriceItem успешно создан для sku=%s", parsed_data["sku"])

    return models.PriceItem(
        sku=parsed_data["sku"],
        name=parsed_data["name"],
        old_price=parsed_data["old_price"],
        new_price=parsed_data["new_price"],
    )


# Читает CSV-файл целиком, пропуская невалидные строки и считая их количество.
def load_csv_items(
    csv_path: pathlib.Path,
) -> tuple[list[models.PriceItem], int]:
    items: list[models.PriceItem] = []
    skipped_count = 0
    logger.info("Начинаем загрузку CSV из %s", csv_path)

    try:
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for index, row in enumerate(reader, start=2):
                try:
                    item = parse_row(row)
                except RowValidationError as e:
                    logger.warning("Строка %s пропущена: %s", index, e)
                    skipped_count += 1
                    continue

                items.append(item)
    except FileNotFoundError:
        logger.error("CSV-файл не найден: %s", csv_path)
        return [], 0

    logger.info(
        "Загрузка CSV завершена: валидных=%s, пропущено=%s",
        len(items),
        skipped_count,
    )

    return items, skipped_count
