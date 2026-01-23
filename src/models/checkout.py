from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CheckoutStatus(Enum):
    AVAILABLE = "AVAILABLE"
    CHECKED_OUT = "CHECKED_OUT"
    LOST = "LOST"
    RETIRED = "RETIRED"


@dataclass
class Checkout:
    id: str
    item_id: str
    item_type: str
    borrower_name: str
    checkout_date: datetime
    expected_return: datetime | None
    actual_return: datetime | None = None
    notes: str = ""


@dataclass
class Borrower:
    id: str
    name: str
    phone: str = ""
    email: str = ""
    notes: str = ""
