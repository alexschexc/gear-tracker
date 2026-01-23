from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TransferStatus(Enum):
    OWNED = "OWNED"
    TRANSFERRED = "TRANSFERRED"


class NFAFirearmType(Enum):
    SBR = "SBR"
    SBS = "SBS"


@dataclass
class Firearm:
    id: str
    name: str
    caliber: str
    serial_number: str
    purchase_date: datetime
    notes: str = ""
    status: str = "AVAILABLE"
    is_nfa: bool = False
    nfa_type: NFAFirearmType | None = None
    tax_stamp_id: str = ""
    form_type: str = ""
    barrel_length: str = ""
    trust_name: str = ""
    transfer_status: TransferStatus = TransferStatus.OWNED
    rounds_fired: int = 0
    clean_interval_rounds: int = 500
    oil_interval_days: int = 90
    needs_maintenance: bool = False
    maintenance_conditions: str = ""


@dataclass
class Transfer:
    id: str
    firearm_id: str
    transfer_date: datetime
    buyer_name: str
    buyer_address: str
    buyer_dl_number: str
    buyer_ltc_number: str = ""
    sale_price: float = 0.0
    ffl_dealer: str = ""
    ffl_license: str = ""
    notes: str = ""
