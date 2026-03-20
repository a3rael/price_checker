from dataclasses import dataclass


@dataclass
class PriceItem:
    sku: str
    name: str
    old_price: float
    new_price: float
