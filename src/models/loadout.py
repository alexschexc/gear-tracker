from dataclasses import dataclass
from datetime import datetime


@dataclass
class Loadout:
    id: str
    name: str
    description: str = ""
    created_date: datetime | None = None
    notes: str = ""


@dataclass
class LoadoutItem:
    id: str
    loadout_id: str
    item_id: str
    item_type: str
    notes: str = ""


@dataclass
class LoadoutConsumable:
    id: str
    loadout_id: str
    consumable_id: str
    quantity: int
    notes: str = ""


@dataclass
class LoadoutCheckout:
    id: str
    loadout_id: str
    checkout_id: str
    return_date: datetime | None = None
    rounds_fired: int = 0
    rain_exposure: bool = False
    ammo_type: str = ""
    notes: str = ""
