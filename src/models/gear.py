from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class NFAItemType(Enum):
    SUPPRESSOR = "SUPPRESSOR"
    SBR = "SBR"
    SBS = "SBS"
    AOW = "AOW"
    DD = "DD"


@dataclass
class SoftGear:
    id: str
    name: str
    category: str
    brand: str
    purchase_date: datetime
    notes: str = ""
    status: str = "AVAILABLE"


@dataclass
class NFAItem:
    id: str
    name: str
    nfa_type: NFAItemType
    manufacturer: str
    serial_number: str
    tax_stamp_id: str
    caliber_bore: str
    purchase_date: datetime
    form_type: str = ""
    trust_name: str = ""
    notes: str = ""
    status: str = "AVAILABLE"


@dataclass
class Attachment:
    id: str
    name: str
    category: str
    brand: str
    model: str
    purchase_date: datetime | None
    serial_number: str = ""
    mounted_on_firearm_id: str | None = None
    mount_position: str = ""
    zero_distance_yards: int | None = None
    zero_notes: str = ""
    notes: str = ""
