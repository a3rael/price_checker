from price_checker.models import PriceItem


def price_change_pct(old_price: float, new_price: float) -> float:
    if old_price == 0:
        raise ValueError("old_price не может быть равен 0")
    return (new_price - old_price) / old_price * 100


def is_suspicious_change(item: PriceItem, threshold_pct: float = 20.0) -> bool:
    change = price_change_pct(item.old_price, item.new_price)
    return abs(change) >= threshold_pct


def count_suspicious_items(items: list[PriceItem], threshold: float = 20.0) -> int:
    suspicious_count = 0

    for item in items:
        change = price_change_pct(item.old_price, item.new_price)
        if abs(change) >= threshold:
            suspicious_count += 1

    return suspicious_count
