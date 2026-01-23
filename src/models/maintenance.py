from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class GearCategory(Enum):
    FIREARM = "FIREARM"
    SOFT_GEAR = "SOFT_GEAR"
    CONSUMABLE = "CONSUMABLE"
    NFA_ITEM = "NFA_ITEM"


class MaintenanceType(Enum):
    CLEANING = "CLEANING"
    LUBRICATION = "LUBRICATION"
    REPAIR = "REPAIR"
    ZEROING = "ZEROING"
    HUNTING = "HUNTING"
    INSPECTION = "INSPECTION"
    FIRED_ROUNDS = "FIRED_ROUNDS"
    OILING = "OILING"
    RAIN_EXPOSURE = "RAIN_EXPOSURE"
    CORROSIVE_AMMO = "CORROSIVE_AMMO"
    LEAD_AMMO = "LEAD_AMMO"


@dataclass
class MaintenanceLog:
    id: str
    item_id: str
    item_type: GearCategory
    log_type: MaintenanceType
    date: datetime
    details: str
    ammo_count: int | None = None
    photo_path: str | None = None
