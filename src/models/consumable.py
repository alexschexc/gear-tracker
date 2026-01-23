from dataclasses import dataclass
from datetime import datetime


@dataclass
class Consumable:
    id: str
    name: str
    category: str
    unit: str
    quantity: int
    min_quantity: int
    notes: str = ""


@dataclass
class ConsumableTransaction:
    id: str
    consumable_id: str
    transaction_type: str
    quantity: int
    date: datetime
    notes: str = ""
