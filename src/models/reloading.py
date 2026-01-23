from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReloadBatch:
    id: str
    cartridge: str
    firearm_id: str | None
    date_created: datetime
    bullet_maker: str
    bullet_model: str
    bullet_weight_gr: int | None
    powder_name: str
    powder_charge_gr: float | None
    powder_lot: str = ""
    primer_maker: str = ""
    primer_type: str = ""
    case_brand: str = ""
    case_times_fired: int | None = None
    case_prep_notes: str = ""
    coal_in: float | None = None
    crimp_style: str = ""
    test_date: datetime | None = None
    avg_velocity: int | None = None
    es: int | None = None
    sd: int | None = None
    group_size_inches: float | None = None
    group_distance_yards: int | None = None
    intended_use: str = ""
    status: str = "WORKUP"
    notes: str = ""
