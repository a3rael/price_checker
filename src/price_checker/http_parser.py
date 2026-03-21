from collections.abc import Mapping
from typing import Any

import requests
import typer

import price_checker.models as models
from price_checker.parser import RowValidationError, parse_row


class HTTPDataError(Exception):
    pass


# Выполняет HTTP GET-запрос и возвращает уже разобранный JSON-ответ.
def fetch_json(url: str, timeout: float = 10.0) -> Any:
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPDataError(f"Ошибка HTTP-запроса: {e}") from e

    try:
        return response.json()
    except ValueError as e:
        raise HTTPDataError("Ответ сервера не содержит корректный JSON") from e


# Приводит JSON к единому виду: список объектов с данными товаров.
def extract_items(data: Any) -> list[Mapping[str, object]]:
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            items = data["items"]
        else:
            items = [data]
    else:
        raise HTTPDataError("JSON должен быть объектом или списком объектов")

    normalized_items: list[Mapping[str, object]] = []

    for item in items:
        if not isinstance(item, Mapping):
            raise HTTPDataError("Каждый элемент JSON должен быть объектом")
        normalized_items.append(item)

    return normalized_items


# Загружает данные по URL, валидирует элементы и превращает их в PriceItem.
def load_http_items(
    url: str, timeout: float = 10.0
) -> tuple[list[models.PriceItem], int]:
    items: list[models.PriceItem] = []
    skipped_count = 0

    try:
        data = fetch_json(url, timeout=timeout)
        raw_items = extract_items(data)
    except HTTPDataError as e:
        typer.echo(e)
        return [], 0

    for index, row in enumerate(raw_items, start=1):
        try:
            item = parse_row(row)
        except RowValidationError as e:
            typer.echo(f"Элемент {index} пропущен: {e}")
            skipped_count += 1
            continue

        items.append(item)

    return items, skipped_count
