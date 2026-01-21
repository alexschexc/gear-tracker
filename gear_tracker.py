from dataclasses import dataclass, field
from datetime import datetime
from os import curdir, name
from pathlib import Path
from enum import Enum
import sqlite3
import uuid

# ============== ENUMS ==============


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


class CheckoutStatus(Enum):
    AVAILABLE = "AVAILABLE"
    CHECKED_OUT = "CHECKED_OUT"
    LOST = "LOST"
    RETIRED = "RETIRED"


class NFAItemType(Enum):
    SUPPRESSOR = "SUPPRESSOR"
    SBR = "SBR"
    SBS = "SBS"
    AOW = "AOW"
    DD = "DD"


class NFAFirearmType(Enum):
    SBR = "SBR"
    SBS = "SBS"


class TransferStatus(Enum):
    OWNED = "OWNED"
    TRANSFERRED = "TRANSFERRED"


# ============== DATA CLASSES ==============


@dataclass
class Firearm:
    id: str
    name: str
    caliber: str
    serial_number: str
    purchase_date: datetime
    notes: str = ""
    status: CheckoutStatus = CheckoutStatus.AVAILABLE
    # NFA fields:
    is_nfa: bool = False
    nfa_type: NFAFirearmType | None = None
    tax_stamp_id: str = ""
    form_type: str = ""
    barrel_length: str = ""
    trust_name: str = ""
    # Transfer field:
    transfer_status: TransferStatus = TransferStatus.OWNED
    # Maintenance tracking:
    rounds_fired: int = 0
    clean_interval_rounds: int = 500
    oil_interval_days: int = 90
    needs_maintenance: bool = False
    maintenance_conditions: str = ""


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
    status: CheckoutStatus = CheckoutStatus.AVAILABLE


@dataclass
class SoftGear:
    id: str
    name: str
    category: str  # chest_rig, backpack, chaps, gloves, boots, etc.
    brand: str
    purchase_date: datetime
    notes: str = ""
    status: CheckoutStatus = CheckoutStatus.AVAILABLE


@dataclass
class Consumable:
    id: str
    name: str
    category: str  # ammo, batteries, hygiene, medical, etc.
    unit: str  # rounds, count, oz, etc.
    quantity: int
    min_quantity: int  # alert threshold
    notes: str = ""


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


@dataclass
class ConsumableTransaction:
    id: str
    consumable_id: str
    transaction_type: str  # ADD, USE, ADJUST
    quantity: int  # positive for add, negative for use
    date: datetime
    notes: str = ""


@dataclass
class Checkout:
    id: str
    item_id: str
    item_type: GearCategory
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


@dataclass
class Attachment:
    id: str
    name: str
    category: str  # optic, light, stock, rail, trigger, etc.
    brand: str
    model: str
    purchase_date: datetime | None
    serial_number: str = ""
    mounted_on_firearm_id: str | None = None
    mount_position: str = ""  # top rail, scout mount, etc.
    zero_distance_yards: int | None = None
    zero_notes: str = ""
    notes: str = ""


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
    item_type: GearCategory
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


@dataclass
class ImportResult:
    success: bool
    total_rows: int
    imported: int
    skipped: int
    overwritten: int
    errors: list[str]
    warnings: list[str]
    entity_stats: dict[str, int]


@dataclass
class ValidationError:
    row_number: int
    entity_type: str
    field_name: str
    error_type: str
    message: str
    severity: str


@dataclass
class ImportRowResult:
    row_number: int
    entity_type: str
    action: str
    error_message: str | None = None


# ============== REPOSITORY ==============


class GearRepository:
    def __init__(self, db_path: Path = Path.home() / ".gear_tracker" / "tracker.db"):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Firearms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS firearms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                caliber TEXT NOT NULL,
                serial_number TEXT UNIQUE,
                purchase_date INTEGER NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'AVAILABLE'
            )
        """)

        # Soft gear table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS soft_gear (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                brand TEXT,
                purchase_date INTEGER NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'AVAILABLE'
            )
        """)

        # Consumables table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consumables (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                min_quantity INTEGER NOT NULL DEFAULT 0,
                notes TEXT
            )
        """)

        # Consumable transactions (for history)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consumable_transactions (
                id TEXT PRIMARY KEY,
                consumable_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                date INTEGER NOT NULL,
                notes TEXT,
                FOREIGN KEY(consumable_id) REFERENCES consumables(id)
            )
        """)

        # Maintenance logs (polymorphic - works for firearms and soft gear)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_logs (
                id TEXT PRIMARY KEY,
                item_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                log_type TEXT NOT NULL,
                date INTEGER NOT NULL,
                details TEXT,
                ammo_count INTEGER,
                photo_path TEXT
            )
        """)

        # Borrowers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS borrowers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                notes TEXT
            )
        """)

        # Checkouts (polymorphic - works for firearms and soft gear)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkouts (
                id TEXT PRIMARY KEY,
                item_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                borrower_id TEXT NOT NULL,
                checkout_date INTEGER NOT NULL,
                expected_return INTEGER,
                actual_return INTEGER,
                notes TEXT,
                FOREIGN KEY(borrower_id) REFERENCES borrowers(id)
            )
        """)
        # NFA_ITEM table creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nfa_items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                nfa_type TEXT NOT NULL,
                manufacturer TEXT,
                serial_number TEXT,
                tax_stamp_id TEXT NOT NULL,
                caliber_bore TEXT,
                purchase_date INTEGER NOT NULL,
                form_type TEXT,
                trust_name TEXT,
                notes TEXT,
                status TEXT DEFAULT 'AVAILABLE'
            )
        """)
        # Transfers table creation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
               id TEXT PRIMARY KEY,
                firearm_id TEXT NOT NULL,
                transfer_date INTEGER NOT NULL,
                buyer_name TEXT NOT NULL,
                buyer_address TEXT NOT NULL,
                buyer_dl_number TEXT NOT NULL,
                buyer_ltc_number TEXT,
                sale_price REAL,
                ffl_dealer TEXT,
                ffl_license TEXT,
                notes TEXT,
                FOREIGN KEY(firearm_id) REFERENCES firearms(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attachments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                brand TEXT,
                model TEXT,
                serial_number TEXT,
                purchase_date INTEGER,
                mounted_on_firearm_id TEXT,
                mount_position TEXT,
                zero_distance_yards INTEGER,
                zero_notes TEXT,
                notes TEXT,
                FOREIGN KEY(mounted_on_firearm_id) REFERENCES firearms(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reload_batches (
                id TEXT PRIMARY KEY,
                cartridge TEXT NOT NULL,
                firearm_id TEXT,
                date_created INTEGER NOT NULL,

                bullet_maker TEXT,
                bullet_model TEXT,
                bullet_weight_gr INTEGER,

                powder_name TEXT,
                powder_charge_gr REAL,
                powder_lot TEXT,

                primer_maker TEXT,
                primer_type TEXT,

                case_brand TEXT,
                case_times_fired INTEGER,
                case_prep_notes TEXT,

                coal_in REAL,
                crimp_style TEXT,

                test_date INTEGER,
                avg_velocity INTEGER,
                es INTEGER,
                sd INTEGER,
                group_size_inches REAL,
                group_distance_yards INTEGER,

                intended_use TEXT,
                status TEXT,
                notes TEXT,

                FOREIGN KEY(firearm_id) REFERENCES firearms(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loadouts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_date INTEGER NOT NULL,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loadout_items (
                id TEXT PRIMARY KEY,
                loadout_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY(loadout_id) REFERENCES loadouts(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loadout_consumables (
                id TEXT PRIMARY KEY,
                loadout_id TEXT NOT NULL,
                consumable_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                notes TEXT,
                FOREIGN KEY(loadout_id) REFERENCES loadouts(id),
                FOREIGN KEY(consumable_id) REFERENCES consumables(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loadout_checkouts (
                id TEXT PRIMARY KEY,
                loadout_id TEXT NOT NULL,
                checkout_id TEXT NOT NULL,
                return_date INTEGER,
                rounds_fired INTEGER DEFAULT 0,
                rain_exposure INTEGER DEFAULT 0,
                ammo_type TEXT,
                notes TEXT,
                FOREIGN KEY(loadout_id) REFERENCES loadouts(id),
                FOREIGN KEY(checkout_id) REFERENCES checkouts(id)
            )
        """)

        # fixing maintenance_logs table
        cursor.execute("PRAGMA table_info(maintenance_logs)")
        maint_columns = {row[1] for row in cursor.fetchall()}

        # if table exists but doesn't have item_id, drop and recreate
        if maint_columns and "item_id" not in maint_columns:
            cursor.execute("DROP TABLE maintenance_logs")
            print("✓ Dropped old maintenance_logs table (incompatible schema)")

            cursor.execute("""
            CREATE TABLE maintenance_logs (
                id TEXT PRIMARY KEY,
                item_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                log_type TEXT NOT NULL,
                date INTEGER NOT NULL,
                details TEXT,
                ammo_count INTEGER,
                photo_path TEXT
                )
            """)
            print("✓ Recreated maintenance_logs table with correct schema")

        # migration logic
        desired_schema = {
            "firearms": [
                ("status", "TEXT", "AVAILABLE"),
                ("is_nfa", "INTEGER", 0),
                ("nfa_type", "TEXT", None),
                ("tax_stamp_id", "TEXT", ""),
                ("form_type", "TEXT", ""),
                ("barrel_length", "TEXT", ""),
                ("trust_name", "TEXT", ""),
                ("transfer_status", "TEXT", "OWNED"),
                ("rounds_fired", "INTEGER", 0),
                ("clean_interval_rounds", "INTEGER", 500),
                ("oil_interval_days", "INTEGER", 90),
                ("needs_maintenance", "INTEGER", 0),
                ("maintenance_conditions", "TEXT", ""),
            ],
            "soft_gear": [
                ("status", "TEXT", "AVAILABLE"),
            ],
            "maintenance_logs": [
                ("item_id", "TEXT", None),
                ("item_type", "TEXT", None),
                ("log_type", "TEXT", None),
                ("date", "INTEGER", None),
                ("details", "TEXT", None),
                ("ammo_count", "INTEGER", None),
                ("photo_path", "TEXT", None),
            ],
        }
        # Auto migration loop to add missing columns during development
        for table_name, columns_to_add in desired_schema.items():
            # Get list of existing columns for this table
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}

            # Check each desired column
            for col_name, col_type, default_value in columns_to_add:
                if col_name not in existing_columns:
                    # Column is missing, add it
                    if default_value is not None:
                        cursor.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} DEFAULT '{default_value}'"
                        )
                    else:
                        cursor.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                        )
                    print(f"✓ Migrated '{table_name}': added '{col_name}' column")

        conn.commit()
        conn.close()

    # -------- FIREARM METHODS --------

    def add_firearm(self, firearm: Firearm) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO firearms VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                firearm.id,
                firearm.name,
                firearm.caliber,
                firearm.serial_number,
                int(firearm.purchase_date.timestamp()),
                firearm.notes,
                firearm.status.value,
                1 if firearm.is_nfa else 0,
                firearm.nfa_type.value if firearm.nfa_type else None,
                firearm.tax_stamp_id,
                firearm.form_type,
                firearm.barrel_length,
                firearm.trust_name,
                firearm.transfer_status.value,
                firearm.rounds_fired,
                firearm.clean_interval_rounds,
                firearm.oil_interval_days,
                1 if firearm.needs_maintenance else 0,
                firearm.maintenance_conditions,
            ),
        )
        conn.commit()
        conn.close()

    def get_all_firearms(self) -> list[Firearm]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM firearms WHERE transfer_status = 'OWNED' or transfer_status IS NULL ORDER BY name"
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            Firearm(
                id=row[0],
                name=row[1],
                caliber=row[2],
                serial_number=row[3],
                purchase_date=datetime.fromtimestamp(row[4]),
                notes=row[5] or "",
                status=CheckoutStatus(row[6]) if row[6] else CheckoutStatus.AVAILABLE,
                is_nfa=bool(row[7]) if len(row) > 7 else False,
                nfa_type=NFAFirearmType(row[8]) if len(row) > 8 and row[8] else None,
                tax_stamp_id=row[9] if len(row) > 9 else "",
                form_type=row[10] if len(row) > 10 else "",
                barrel_length=row[11] if len(row) > 11 else "",
                trust_name=row[12] if len(row) > 12 else "",
                transfer_status=TransferStatus(row[13])
                if len(row) > 13 and row[13]
                else TransferStatus.OWNED,
                rounds_fired=row[14] if len(row) > 14 else 0,
                clean_interval_rounds=row[15] if len(row) > 15 else 500,
                oil_interval_days=row[16] if len(row) > 16 else 90,
                needs_maintenance=bool(row[17]) if len(row) > 17 else False,
                maintenance_conditions=row[18] if len(row) > 18 else "",
            )
            for row in rows
        ]

    def update_firearm_status(self, firearm_id: str, status: CheckoutStatus) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE firearms SET status = ? WHERE id = ?", (status.value, firearm_id)
        )
        conn.commit()
        conn.close()

    def delete_firearm(self, firearm_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM maintenance_logs WHERE item_id = ?", (firearm_id,))
        cursor.execute("DELETE FROM checkouts WHERE item_id = ?", (firearm_id,))
        cursor.execute("DELETE FROM firearms WHERE id = ?", (firearm_id,))
        conn.commit()
        conn.close()

    def update_firearm_rounds(self, firearm_id: str, rounds: int) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT rounds_fired, clean_interval_rounds FROM firearms WHERE id = ?",
            (firearm_id,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return

        current_rounds, clean_interval = result
        new_rounds = current_rounds + rounds

        cursor.execute(
            "UPDATE firearms SET rounds_fired = ? WHERE id = ?",
            (new_rounds, firearm_id),
        )

        if clean_interval and new_rounds >= clean_interval:
            cursor.execute(
                "UPDATE firearms SET needs_maintenance = 1 WHERE id = ?",
                (firearm_id,),
            )

        conn.commit()
        conn.close()

    def get_maintenance_status(self, firearm_id: str) -> dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                f.rounds_fired,
                f.clean_interval_rounds,
                f.oil_interval_days,
                f.needs_maintenance,
                f.maintenance_conditions,
                MAX(m.date) as last_clean_date
            FROM firearms f
            LEFT JOIN maintenance_logs m ON f.id = m.item_id
                AND m.log_type = 'CLEANING'
            WHERE f.id = ?
            GROUP BY f.id
            """,
            (firearm_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return {"needs_maintenance": False, "reasons": []}

        (
            rounds_fired,
            clean_interval,
            oil_interval,
            needs_maintenance,
            maintenance_conditions,
            last_clean_date,
        ) = row

        reasons = []

        if clean_interval and rounds_fired >= clean_interval:
            reasons.append(
                f"Rounds fired ({rounds_fired}) exceeds clean interval ({clean_interval})"
            )

        if last_clean_date:
            last_clean_dt = datetime.fromtimestamp(last_clean_date)
            days_since_clean = (datetime.now() - last_clean_dt).days
            if oil_interval and days_since_clean >= oil_interval:
                reasons.append(
                    f"Last cleaned {days_since_clean} days ago (interval: {oil_interval} days)"
                )

        if maintenance_conditions:
            reasons.extend(maintenance_conditions.split(","))

        status = needs_maintenance or len(reasons) > 0

        return {
            "needs_maintenance": status,
            "rounds_fired": rounds_fired,
            "last_clean_date": last_clean_date,
            "reasons": reasons,
        }

    def mark_maintenance_done(
        self, firearm_id: str, maintenance_type: MaintenanceType, details: str = ""
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT rounds_fired, clean_interval_rounds FROM firearms WHERE id = ?",
            (firearm_id,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return

        current_rounds, clean_interval = result

        if maintenance_type == MaintenanceType.CLEANING:
            new_rounds = 0
            cursor.execute(
                "UPDATE firearms SET rounds_fired = ?, needs_maintenance = 0 WHERE id = ?",
                (new_rounds, firearm_id),
            )

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=maintenance_type,
            date=datetime.now(),
            details=details,
        )

        cursor.execute(
            "INSERT INTO maintenance_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                log.id,
                log.item_id,
                log.item_type.value,
                log.log_type.value,
                int(log.date.timestamp()),
                log.details,
                log.ammo_count,
                log.photo_path,
            ),
        )

        conn.commit()
        conn.close()

    # -------- ATTACHMENT METHODS --------
    def add_attachment(self, attachment: Attachment) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO attachments VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                attachment.id,
                attachment.name,
                attachment.category,
                attachment.brand,
                attachment.model,
                attachment.serial_number,
                int(attachment.purchase_date.timestamp())
                if attachment.purchase_date
                else None,
                attachment.mounted_on_firearm_id,
                attachment.mount_position,
                attachment.zero_distance_yards,
                attachment.zero_notes,
                attachment.notes,
            ),
        )
        conn.commit()
        conn.close()

    def get_all_attachments(self) -> list[Attachment]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attachments ORDER BY category, name")
        rows = cursor.fetchall()
        conn.close()
        return [
            Attachment(
                id=row[0],
                name=row[1],
                category=row[2],
                brand=row[3] or "",
                model=row[4] or "",
                serial_number=row[5] or "",
                purchase_date=datetime.fromtimestamp(row[6]) if row[6] else None,
                mounted_on_firearm_id=row[7],
                mount_position=row[8] or "",
                zero_distance_yards=row[9],
                zero_notes=row[10] or "",
                notes=row[11] or "",
            )
            for row in rows
        ]

    def get_attachments_for_firearm(self, firearm_id: str) -> list[Attachment]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM attachments WHERE mounted_on_firearm_id = ? ORDER BY category, name",
            (firearm_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [
            Attachment(
                id=row[0],
                name=row[1],
                category=row[2],
                brand=row[3] or "",
                model=row[4] or "",
                serial_number=row[5] or "",
                purchase_date=datetime.fromtimestamp(row[6]) if row[6] else None,
                mounted_on_firearm_id=row[7],
                mount_position=row[8] or "",
                zero_distance_yards=row[9],
                zero_notes=row[10] or "",
                notes=row[11] or "",
            )
            for row in rows
        ]

    def update_attachment(self, attachment: Attachment) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
        UPDATE attachments
        SET name = ?, category = ?, brand = ?, model = ?, serial_number = ?, purchase_date = ?, mounted_on_firearm_id = ?, mount_position = ?, zero_distance_yards = ?, zero_notes = ?, notes = ?
        WHERE id = ?
        """,
            (
                attachment.name,
                attachment.category,
                attachment.brand,
                attachment.model,
                attachment.serial_number,
                int(attachment.purchase_date.timestamp())
                if attachment.purchase_date
                else None,
                attachment.mounted_on_firearm_id,
                attachment.mount_position,
                attachment.zero_distance_yards,
                attachment.zero_notes,
                attachment.notes,
                attachment.id,
            ),
        )
        conn.commit()
        conn.close()

    def delete_attachment(self, attachment_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
        conn.commit()
        conn.close()

    # -------- TRANSFER METHODS --------
    def transfer_firearm(self, transfer: Transfer) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Add transfer record
        cursor.execute(
            "INSERT INTO transfers VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                transfer.id,
                transfer.firearm_id,
                int(transfer.transfer_date.timestamp()),
                transfer.buyer_name,
                transfer.buyer_address,
                transfer.buyer_dl_number,
                transfer.buyer_ltc_number,
                transfer.sale_price,
                transfer.ffl_dealer,
                transfer.ffl_license,
                transfer.notes,
            ),
        )

        cursor.execute(
            "UPDATE firearms SET transfer_status = ? WHERE id = ?",
            (TransferStatus.TRANSFERRED.value, transfer.firearm_id),
        )

        conn.commit()
        conn.close()

    def get_all_transfers(self) -> list[tuple[Transfer, Firearm]]:
        """Returns list of (transfer, firearm) tuples"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.*, f.name, f.caliber, f.serial_number
            FROM transfers t
            JOIN firearms f ON t.firearm_id = f.id
            ORDER BY t.transfer_date DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            transfer = Transfer(
                id=row[0],
                firearm_id=row[1],
                transfer_date=datetime.fromtimestamp(row[2]),
                buyer_name=row[3],
                buyer_address=row[4],
                buyer_dl_number=row[5],
                buyer_ltc_number=row[6] or "",
                sale_price=row[7] or 0.0,
                ffl_dealer=row[8] or "",
                ffl_license=row[9] or "",
                notes=row[10] or "",
            )

            firearm = Firearm(
                id=row[1],
                name=row[11],
                caliber=row[12],
                serial_number=row[13],
                purchase_date=datetime.now(),
            )

            results.append((transfer, firearm))

        return results

    # -------- NFA ITEM METHODS --------

    def add_nfa_item(self, item: NFAItem) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO nfa_items VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                item.id,
                item.name,
                item.nfa_type.value,
                item.manufacturer,
                item.serial_number,
                item.tax_stamp_id,
                item.caliber_bore,
                int(item.purchase_date.timestamp()),
                item.form_type,
                item.trust_name,
                item.notes,
                item.status.value,
            ),
        )
        conn.commit()
        conn.close()

    def get_all_nfa_items(self) -> list[NFAItem]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM nfa_items ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        return [
            NFAItem(
                id=row[0],
                name=row[1],
                nfa_type=NFAItemType(row[2]),
                manufacturer=row[3] or "",
                serial_number=row[4] or "",
                tax_stamp_id=row[5] or "",
                caliber_bore=row[6] or "",
                purchase_date=datetime.fromtimestamp(row[7]),
                form_type=row[8] or "",
                trust_name=row[9] or "",
                notes=row[10] or "",
                status=CheckoutStatus(row[11]) if row[11] else CheckoutStatus.AVAILABLE,
            )
            for row in rows
        ]

    def update_nfa_item_status(self, item_id: str, status: CheckoutStatus) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE nfa_items SET status = ? WHERE id = ?", (status.value, item_id)
        )
        conn.commit()
        conn.close()

    def delete_nfa_item(self, item_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM maintenance_logs WHERE item_id = ?", (item_id,))
        cursor.execute("DELETE FROM checkouts WHERE item_id = ?", (item_id,))
        cursor.execute("DELETE FROM nfa_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    # -------- SOFT GEAR METHODS --------

    def add_soft_gear(self, gear: SoftGear) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO soft_gear VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                gear.id,
                gear.name,
                gear.category,
                gear.brand,
                int(gear.purchase_date.timestamp()),
                gear.notes,
                gear.status.value,
            ),
        )
        conn.commit()
        conn.close()

    def get_all_soft_gear(self) -> list[SoftGear]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM soft_gear ORDER BY category, name")
        rows = cursor.fetchall()
        conn.close()

        return [
            SoftGear(
                id=row[0],
                name=row[1],
                category=row[2],
                brand=row[3],
                purchase_date=datetime.fromtimestamp(row[4]),
                notes=row[5] or "",
                status=CheckoutStatus(row[6]) if row[6] else CheckoutStatus.AVAILABLE,
            )
            for row in rows
        ]

    def update_soft_gear_status(self, gear_id: str, status: CheckoutStatus) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE soft_gear SET status = ? WHERE id = ?", (status.value, gear_id)
        )
        conn.commit()
        conn.close()

    def delete_soft_gear(self, gear_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM maintenance_logs WHERE item_id = ?", (gear_id))
        cursor.execute("DELETE FROM checkouts WHERE item_id = ?", (gear_id))
        cursor.execute("DELETE FROM soft_gear WHERE id = ?", (gear_id))
        conn.commit()
        conn.close()

    # -------- CONSUMABLE METHODS --------

    def add_consumable(self, consumable: Consumable) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO consumables VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                consumable.id,
                consumable.name,
                consumable.category,
                consumable.unit,
                consumable.quantity,
                consumable.min_quantity,
                consumable.notes,
            ),
        )
        conn.commit()
        conn.close()

    def get_all_consumables(self) -> list[Consumable]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM consumables ORDER BY category, name")
        rows = cursor.fetchall()
        conn.close()

        return [
            Consumable(
                id=row[0],
                name=row[1],
                category=row[2],
                unit=row[3],
                quantity=row[4],
                min_quantity=row[5],
                notes=row[6] or "",
            )
            for row in rows
        ]

    def get_low_stock_consumables(self) -> list[Consumable]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM consumables WHERE quantity <= min_quantity ORDER BY category, name"
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            Consumable(
                id=row[0],
                name=row[1],
                category=row[2],
                unit=row[3],
                quantity=row[4],
                min_quantity=row[5],
                notes=row[6] or "",
            )
            for row in rows
        ]

    def update_consumable_quantity(
        self, consumable_id: str, delta: int, transaction_type: str, notes: str = ""
    ) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update quantity
        cursor.execute(
            "UPDATE consumables SET quantity = quantity + ? WHERE id = ?",
            (delta, consumable_id),
        )

        # Log transaction
        tx_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO consumable_transactions VALUES (?, ?, ?, ?, ?, ?)",
            (
                tx_id,
                consumable_id,
                transaction_type,
                delta,
                int(datetime.now().timestamp()),
                notes,
            ),
        )

        conn.commit()
        conn.close()

    def get_consumable_history(self, consumable_id: str) -> list[ConsumableTransaction]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM consumable_transactions WHERE consumable_id = ? ORDER BY date DESC",
            (consumable_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            ConsumableTransaction(
                id=row[0],
                consumable_id=row[1],
                transaction_type=row[2],
                quantity=row[3],
                date=datetime.fromtimestamp(row[4]),
                notes=row[5] or "",
            )
            for row in rows
        ]

    def delete_consumable(self, consumable_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM consumable_transactions WHERE consumable_id = ?",
            (consumable_id,),
        )
        cursor.execute("DELETE FROM consumables WHERE id = ?", (consumable_id,))
        conn.commit()
        conn.close()

    # -------- BORROWER METHODS --------

    def add_borrower(self, borrower: Borrower) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO borrowers VALUES (?, ?, ?, ?, ?)",
            (
                borrower.id,
                borrower.name,
                borrower.phone,
                borrower.email,
                borrower.notes,
            ),
        )
        conn.commit()
        conn.close()

    def get_all_borrowers(self) -> list[Borrower]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM borrowers ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        return [
            Borrower(
                id=row[0],
                name=row[1],
                phone=row[2] or "",
                email=row[3] or "",
                notes=row[4] or "",
            )
            for row in rows
        ]

    def delete_borrower(self, borrower_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Check if borrower has active checkouts
        cursor.execute(
            "SELECT COUNT(*) FROM checkouts WHERE borrower_id = ? AND actual_return IS NULL",
            (borrower_id,),
        )
        count = cursor.fetchone()[0]
        conn.close()

        if count > 0:
            raise ValueError("Cannot delete borrower with active checkouts")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM checkouts WHERE borrower_id = ?", (borrower_id,))
        cursor.execute("DELETE FROM borrowers WHERE id = ?", (borrower_id,))
        conn.commit()
        conn.close()

    # -------- CHECKOUT METHODS --------

    def checkout_item(
        self,
        item_id: str,
        item_type: GearCategory,
        borrower_id: str,
        expected_return: datetime | None = None,
        notes: str = "",
    ) -> str:
        checkout_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO checkouts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                checkout_id,
                item_id,
                item_type.value,
                borrower_id,
                int(datetime.now().timestamp()),
                int(expected_return.timestamp()) if expected_return else None,
                None,
                notes,
            ),
        )

        # Update item status
        if item_type == GearCategory.FIREARM:
            cursor.execute(
                "UPDATE firearms SET status = ? WHERE id = ?",
                (CheckoutStatus.CHECKED_OUT.value, item_id),
            )
        elif item_type == GearCategory.SOFT_GEAR:
            cursor.execute(
                "UPDATE soft_gear SET status = ? WHERE id = ?",
                (CheckoutStatus.CHECKED_OUT.value, item_id),
            )
        elif item_type == GearCategory.NFA_ITEM:
            cursor.execute(
                "UPDATE nfa_items SET status = ? WHERE id = ?",
                (CheckoutStatus.CHECKED_OUT.value, item_id),
            )

        conn.commit()
        conn.close()
        return checkout_id

    def return_item(self, checkout_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get checkout info
        cursor.execute(
            "SELECT item_id, item_type FROM checkouts WHERE id = ?", (checkout_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return

        item_id, item_type = row[0], GearCategory(row[1])

        # Mark returned
        cursor.execute(
            "UPDATE checkouts SET actual_return = ? WHERE id = ?",
            (int(datetime.now().timestamp()), checkout_id),
        )

        # Update item status
        if item_type == GearCategory.FIREARM:
            cursor.execute(
                "UPDATE firearms SET status = ? WHERE id = ?",
                (CheckoutStatus.AVAILABLE.value, item_id),
            )
        elif item_type == GearCategory.SOFT_GEAR:
            cursor.execute(
                "UPDATE soft_gear SET status = ? WHERE id = ?",
                (CheckoutStatus.AVAILABLE.value, item_id),
            )
        elif item_type == GearCategory.NFA_ITEM:
            cursor.execute(
                "UPDATE nfa_items SET status = ? WHERE id = ?",
                (CheckoutStatus.AVAILABLE.value, item_id),
            )

        conn.commit()
        conn.close()

    def get_active_checkouts(self) -> list[tuple[Checkout, Borrower, str]]:
        """Returns list of (checkout, borrower, item_name) for active checkouts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.*, b.name as borrower_name, b.phone, b.email
            FROM checkouts c
            JOIN borrowers b ON c.borrower_id = b.id
            WHERE c.actual_return IS NULL
            ORDER BY c.checkout_date DESC
        """)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            checkout = Checkout(
                id=row[0],
                item_id=row[1],
                item_type=GearCategory(row[2]),
                borrower_name=row[8],
                checkout_date=datetime.fromtimestamp(row[4]),
                expected_return=datetime.fromtimestamp(row[5]) if row[5] else None,
                actual_return=None,
                notes=row[7] or "",
            )

            # Get item name
            if checkout.item_type == GearCategory.FIREARM:
                cursor.execute(
                    "SELECT name FROM firearms WHERE id = ?", (checkout.item_id,)
                )
            elif checkout.item_type == GearCategory.SOFT_GEAR:
                cursor.execute(
                    "SELECT name FROM soft_gear WHERE id = ?", (checkout.item_id,)
                )
            elif checkout.item_type == GearCategory.NFA_ITEM:
                cursor.execute(
                    "SELECT name FROM nfa_items where id = ?", (checkout.item_id,)
                )

            item_row = cursor.fetchone()
            item_name = item_row[0] if item_row else "Unknown"

            borrower = Borrower(
                id=row[3], name=row[8], phone=row[9] or "", email=row[10] or ""
            )
            results.append((checkout, borrower, item_name))

        conn.close()
        return results

    def get_checkout_history(self, item_id: str) -> list[tuple[Checkout, str]]:
        """Returns checkout history for an item with borrower names"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT c.*, b.name as borrower_name
            FROM checkouts c
            JOIN borrowers b ON c.borrower_id = b.id
            WHERE c.item_id = ?
            ORDER BY c.checkout_date DESC
        """,
            (item_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            (
                Checkout(
                    id=row[0],
                    item_id=row[1],
                    item_type=GearCategory(row[2]),
                    borrower_name=row[8],
                    checkout_date=datetime.fromtimestamp(row[4]),
                    expected_return=datetime.fromtimestamp(row[5]) if row[5] else None,
                    actual_return=datetime.fromtimestamp(row[6]) if row[6] else None,
                    notes=row[7],
                ),
                row[8],
            )
            for row in rows
        ]

    def get_all_checkout_history(self) -> list[Checkout]:
        """Returns all checkout history with borrower names"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT c.*, b.name as borrower_name
            FROM checkouts c
            JOIN borrowers b ON c.borrower_id = b.id
            ORDER BY c.checkout_date DESC
        """
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            Checkout(
                id=row[0],
                item_id=row[1],
                item_type=GearCategory(row[2]),
                borrower_name=row[8],
                checkout_date=datetime.fromtimestamp(row[4]),
                expected_return=datetime.fromtimestamp(row[5]) if row[5] else None,
                actual_return=datetime.fromtimestamp(row[6]) if row[6] else None,
                notes=row[7],
            )
            for row in rows
        ]

    # -------- MAINTENANCE LOG METHODS --------

    def log_maintenance(self, log: MaintenanceLog) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO maintenance_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                log.id,
                log.item_id,
                log.item_type.value,
                log.log_type.value,
                int(log.date.timestamp()),
                log.details,
                log.ammo_count,
                log.photo_path,
            ),
        )
        conn.commit()
        conn.close()

    def get_logs_for_item(self, item_id: str) -> list[MaintenanceLog]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM maintenance_logs WHERE item_id = ? ORDER BY date DESC",
            (item_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            MaintenanceLog(
                id=row[0],
                item_id=row[1],
                item_type=GearCategory(row[2]),
                log_type=MaintenanceType(row[3]),
                date=datetime.fromtimestamp(row[4]),
                details=row[5],
                ammo_count=row[6],
                photo_path=row[7],
            )
            for row in rows
        ]

    def get_all_maintenance_logs(self) -> list[MaintenanceLog]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maintenance_logs ORDER BY date DESC")
        rows = cursor.fetchall()
        conn.close()

        return [
            MaintenanceLog(
                id=row[0],
                item_id=row[1],
                item_type=GearCategory(row[2]),
                log_type=MaintenanceType(row[3]),
                date=datetime.fromtimestamp(row[4]),
                details=row[5],
                ammo_count=row[6],
                photo_path=row[7],
            )
            for row in rows
        ]

    def last_cleaning_date(self, item_id: str) -> datetime | None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT date FROM maintenance_logs WHERE item_id = ? AND log_type = 'CLEANING' ORDER BY date DESC LIMIT 1",
            (item_id,),
        )
        result = cursor.fetchone()
        conn.close()
        return datetime.fromtimestamp(result[0]) if result else None

    # -------- RELOAD BATCH METHODS --------

    def add_reload_batch(self, batch: ReloadBatch) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO reload_batches VALUES (
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?
            )
            """,
            (
                batch.id,
                batch.cartridge,
                batch.firearm_id,
                int(batch.date_created.timestamp()),
                batch.bullet_maker,
                batch.bullet_model,
                batch.bullet_weight_gr,
                batch.powder_name,
                batch.powder_charge_gr,
                batch.powder_lot,
                batch.primer_maker,
                batch.primer_type,
                batch.case_brand,
                batch.case_times_fired,
                batch.case_prep_notes,
                batch.coal_in,
                batch.crimp_style,
                int(batch.test_date.timestamp()) if batch.test_date else None,
                batch.avg_velocity,
                batch.es,
                batch.sd,
                batch.group_size_inches,
                batch.group_distance_yards,
                batch.intended_use,
                batch.status,
                batch.notes,
            ),
        )
        conn.commit()
        conn.close()

    def update_reload_batch(self, batch: ReloadBatch) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE reload_batches SET
                cartridge = ?, firearm_id = ?, date_created = ?,
                bullet_maker = ?, bullet_model = ?, bullet_weight_gr = ?,
                powder_name = ?, powder_charge_gr = ?, powder_lot = ?,
                primer_maker = ?, primer_type = ?,
                case_brand = ?, case_times_fired = ?, case_prep_notes = ?,
                coal_in = ?, crimp_style = ?,
                test_date = ?, avg_velocity = ?, es = ?, sd = ?,
                group_size_inches = ?, group_distance_yards = ?,
                intended_use = ?, status = ?, notes = ?
            WHERE id = ?
            """,
            (
                batch.cartridge,
                batch.firearm_id,
                int(batch.date_created.timestamp()),
                batch.bullet_maker,
                batch.bullet_model,
                batch.bullet_weight_gr,
                batch.powder_name,
                batch.powder_charge_gr,
                batch.powder_lot,
                batch.primer_maker,
                batch.primer_type,
                batch.case_brand,
                batch.case_times_fired,
                batch.case_prep_notes,
                batch.coal_in,
                batch.crimp_style,
                int(batch.test_date.timestamp()) if batch.test_date else None,
                batch.avg_velocity,
                batch.es,
                batch.sd,
                batch.group_size_inches,
                batch.group_distance_yards,
                batch.intended_use,
                batch.status,
                batch.notes,
                batch.id,
            ),
        )
        conn.commit()
        conn.close()

    def get_all_reload_batches(
        self,
        cartridge: str | None = None,
        firearm_id: str | None = None,
    ) -> list[ReloadBatch]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM reload_batches"
        params: list = []
        clauses: list[str] = []

        if cartridge:
            clauses.append("cartridge = ?")
            params.append(cartridge)
        if firearm_id:
            clauses.append("firearm_id = ?")
            params.append(firearm_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY date_created DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        batches: list[ReloadBatch] = []
        for row in rows:
            (
                id_,
                cartridge,
                firearm_id,
                date_created,
                bullet_maker,
                bullet_model,
                bullet_weight_gr,
                powder_name,
                powder_charge_gr,
                powder_lot,
                primer_maker,
                primer_type,
                case_brand,
                case_times_fired,
                case_prep_notes,
                coal_in,
                crimp_style,
                test_date,
                avg_velocity,
                es,
                sd,
                group_size_inches,
                group_distance_yards,
                intended_use,
                status,
                notes,
            ) = row

            batches.append(
                ReloadBatch(
                    id=id_,
                    cartridge=cartridge or "",
                    firearm_id=firearm_id,
                    date_created=datetime.fromtimestamp(date_created),
                    bullet_maker=bullet_maker or "",
                    bullet_model=bullet_model or "",
                    bullet_weight_gr=bullet_weight_gr,
                    powder_name=powder_name or "",
                    powder_charge_gr=powder_charge_gr,
                    powder_lot=powder_lot or "",
                    primer_maker=primer_maker or "",
                    primer_type=primer_type or "",
                    case_brand=case_brand or "",
                    case_times_fired=case_times_fired,
                    case_prep_notes=case_prep_notes or "",
                    coal_in=coal_in,
                    crimp_style=crimp_style or "",
                    test_date=datetime.fromtimestamp(test_date) if test_date else None,
                    avg_velocity=avg_velocity,
                    es=es,
                    sd=sd,
                    group_size_inches=group_size_inches,
                    group_distance_yards=group_distance_yards,
                    intended_use=intended_use or "",
                    status=status or "WORKUP",
                    notes=notes or "",
                )
            )
        return batches

    def delete_reload_batch(self, batch_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reload_batches WHERE id = ?", (batch_id,))
        conn.commit()
        conn.close()

    # -------- LOADOUT METHODS --------

    def create_loadout(self, loadout: Loadout) -> None:
        """Create new loadout profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO loadouts VALUES (?, ?, ?, ?, ?)",
            (
                loadout.id,
                loadout.name,
                loadout.description,
                int(loadout.created_date.timestamp())
                if loadout.created_date
                else int(datetime.now().timestamp()),
                loadout.notes,
            ),
        )
        conn.commit()
        conn.close()

    def get_all_loadouts(self) -> list[Loadout]:
        """Get all loadout profiles"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loadouts ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        return [
            Loadout(
                id=row[0],
                name=row[1],
                description=row[2] or "",
                created_date=datetime.fromtimestamp(row[3]) if row[3] else None,
                notes=row[4] or "",
            )
            for row in rows
        ]

    def update_loadout(self, loadout: Loadout) -> None:
        """Update loadout details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE loadouts SET name = ?, description = ?, created_date = ?, notes = ? WHERE id = ?",
            (
                loadout.name,
                loadout.description,
                int(loadout.created_date.timestamp())
                if loadout.created_date
                else int(datetime.now().timestamp()),
                loadout.notes,
                loadout.id,
            ),
        )
        conn.commit()
        conn.close()

    def delete_loadout(self, loadout_id: str) -> None:
        """Delete loadout and all associated items/consumables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM loadout_items WHERE loadout_id = ?", (loadout_id,))
        cursor.execute(
            "DELETE FROM loadout_consumables WHERE loadout_id = ?", (loadout_id,)
        )
        cursor.execute(
            "DELETE FROM loadout_checkouts WHERE loadout_id = ?", (loadout_id,)
        )
        cursor.execute("DELETE FROM loadouts WHERE id = ?", (loadout_id,))
        conn.commit()
        conn.close()

    def add_loadout_item(self, item: LoadoutItem) -> None:
        """Add item to loadout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO loadout_items VALUES (?, ?, ?, ?, ?)",
            (item.id, item.loadout_id, item.item_id, item.item_type.value, item.notes),
        )
        conn.commit()
        conn.close()

    def get_loadout_items(self, loadout_id: str) -> list[LoadoutItem]:
        """Get all items in loadout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM loadout_items WHERE loadout_id = ?", (loadout_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            LoadoutItem(
                id=row[0],
                loadout_id=row[1],
                item_id=row[2],
                item_type=GearCategory(row[3]),
                notes=row[4] or "",
            )
            for row in rows
        ]

    def remove_loadout_item(self, item_id: str) -> None:
        """Remove item from loadout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM loadout_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    def add_loadout_consumable(self, item: LoadoutConsumable) -> None:
        """Add consumable to loadout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO loadout_consumables VALUES (?, ?, ?, ?, ?)",
            (item.id, item.loadout_id, item.consumable_id, item.quantity, item.notes),
        )
        conn.commit()
        conn.close()

    def get_loadout_consumables(self, loadout_id: str) -> list[LoadoutConsumable]:
        """Get all consumables in loadout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM loadout_consumables WHERE loadout_id = ?", (loadout_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            LoadoutConsumable(
                id=row[0],
                loadout_id=row[1],
                consumable_id=row[2],
                quantity=row[3],
                notes=row[4] or "",
            )
            for row in rows
        ]

    def update_loadout_consumable_qty(self, item_id: str, qty: int) -> None:
        """Update consumable quantity in loadout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE loadout_consumables SET quantity = ? WHERE id = ?", (qty, item_id)
        )
        conn.commit()
        conn.close()

    def remove_loadout_consumable(self, item_id: str) -> None:
        """Remove consumable from loadout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM loadout_consumables WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    def validate_loadout_checkout(self, loadout_id: str) -> dict:
        """Validate loadout before checkout - returns warnings and critical issues"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        loadout_items = self.get_loadout_items(loadout_id)
        loadout_consumables = self.get_loadout_consumables(loadout_id)

        warnings = []
        critical_issues = []

        # Get current state
        firearms = self.get_all_firearms()
        firearm_dict = {f.id: f for f in firearms}
        soft_gear = self.get_all_soft_gear()
        soft_gear_dict = {g.id: g for g in soft_gear}
        nfa_items = self.get_all_nfa_items()
        nfa_dict = {n.id: n for n in nfa_items}
        consumables = self.get_all_consumables()
        consumable_dict = {c.id: c for c in consumables}

        # Validate items
        for item in loadout_items:
            if item.item_type == GearCategory.FIREARM:
                if item.item_id in firearm_dict:
                    fw = firearm_dict[item.item_id]
                    if fw.status != CheckoutStatus.AVAILABLE:
                        critical_issues.append(
                            f"Firearm '{fw.name}' is not available (status: {fw.status.value})"
                        )
                    if fw.needs_maintenance:
                        critical_issues.append(
                            f"Firearm '{fw.name}' needs maintenance before checkout"
                        )
            elif item.item_type == GearCategory.SOFT_GEAR:
                if item.item_id in soft_gear_dict:
                    gear = soft_gear_dict[item.item_id]
                    if gear.status != CheckoutStatus.AVAILABLE:
                        critical_issues.append(
                            f"Soft gear '{gear.name}' is not available (status: {gear.status.value})"
                        )
            elif item.item_type == GearCategory.NFA_ITEM:
                if item.item_id in nfa_dict:
                    nfa = nfa_dict[item.item_id]
                    if nfa.status != CheckoutStatus.AVAILABLE:
                        critical_issues.append(
                            f"NFA item '{nfa.name}' is not available (status: {nfa.status.value})"
                        )

        # Validate consumables
        for item in loadout_consumables:
            if item.consumable_id in consumable_dict:
                cons = consumable_dict[item.consumable_id]
                stock_after = cons.quantity - item.quantity
                if stock_after < 0:
                    warnings.append(
                        f"Consumable '{cons.name}': Will go negative ({stock_after} {cons.unit}) - indicates restock needed"
                    )
                elif stock_after < cons.min_quantity:
                    warnings.append(
                        f"Consumable '{cons.name}': Will be below minimum ({stock_after} < {cons.min_quantity} {cons.unit})"
                    )

        conn.close()

        can_checkout = len(critical_issues) == 0
        return {
            "can_checkout": can_checkout,
            "warnings": warnings,
            "critical_issues": critical_issues,
        }

    def checkout_loadout(
        self, loadout_id: str, borrower_id: str, expected_return: datetime
    ) -> tuple[str, list[str]]:
        """One-click checkout of entire loadout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Validate first
        validation = self.validate_loadout_checkout(loadout_id)
        if not validation["can_checkout"]:
            conn.close()
            checkout_id = ""
            return (checkout_id, validation["critical_issues"] + validation["warnings"])

        loadout_items = self.get_loadout_items(loadout_id)
        loadout_consumables = self.get_loadout_consumables(loadout_id)

        checkout_ids = []

        # Create checkouts for each item
        for item in loadout_items:
            checkout_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO checkouts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    checkout_id,
                    item.item_id,
                    item.item_type.value,
                    borrower_id,
                    int(datetime.now().timestamp()),
                    int(expected_return.timestamp()) if expected_return else None,
                    None,
                    "",
                ),
            )

            # Update item status
            if item.item_type == GearCategory.FIREARM:
                cursor.execute(
                    "UPDATE firearms SET status = ? WHERE id = ?",
                    (CheckoutStatus.CHECKED_OUT.value, item.item_id),
                )
            elif item.item_type == GearCategory.SOFT_GEAR:
                cursor.execute(
                    "UPDATE soft_gear SET status = ? WHERE id = ?",
                    (CheckoutStatus.CHECKED_OUT.value, item.item_id),
                )
            elif item.item_type == GearCategory.NFA_ITEM:
                cursor.execute(
                    "UPDATE nfa_items SET status = ? WHERE id = ?",
                    (CheckoutStatus.CHECKED_OUT.value, item.item_id),
                )

            checkout_ids.append(checkout_id)

        # Deduct consumables
        all_consumables = self.get_all_consumables()
        consumable_dict = {c.id: c for c in all_consumables}

        for item in loadout_consumables:
            if item.consumable_id in consumable_dict:
                current_qty = consumable_dict[item.consumable_id].quantity
                new_qty = current_qty - item.quantity
                cursor.execute(
                    "UPDATE consumables SET quantity = ? WHERE id = ?",
                    (new_qty, item.consumable_id),
                )

                # Record transaction
                tx_id = str(uuid.uuid4())
                cursor.execute(
                    "INSERT INTO consumable_transactions VALUES (?, ?, ?, ?, ?)",
                    (
                        tx_id,
                        item.consumable_id,
                        "USE",
                        -item.quantity,
                        int(datetime.now().timestamp()),
                    ),
                )

        all_messages = validation["warnings"]
        conn.commit()
        conn.close()

        main_checkout_id = checkout_ids[0] if checkout_ids else ""

        # Create loadout_checkout record
        loadout_checkout_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO loadout_checkouts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                loadout_checkout_id,
                loadout_id,
                main_checkout_id,
                None,  # return_date
                0,  # rounds_fired
                0,  # rain_exposure
                "",  # ammo_type
                "",  # notes
            ),
        )
        conn.commit()
        conn.close()

        return (main_checkout_id, all_messages)

    def get_loadout_checkout(self, checkout_id: str) -> LoadoutCheckout | None:
        """Get loadout checkout record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM loadout_checkouts WHERE checkout_id = ?",
            (checkout_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return LoadoutCheckout(
            id=row[0],
            loadout_id=row[1],
            checkout_id=row[2],
            return_date=datetime.fromtimestamp(row[3]) if row[3] else None,
            rounds_fired=row[4],
            rain_exposure=bool(row[5]),
            ammo_type=row[6] or "",
            notes=row[7] or "",
        )

    def return_loadout(
        self,
        loadout_checkout_id: str,
        rounds_fired_dict: dict,
        rain_exposure: bool = False,
        ammo_type: str = "",
        notes: str = "",
    ) -> None:
        """Return loadout with usage data - updates round counts and creates maintenance logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get loadout info
        cursor.execute(
            "SELECT loadout_id, checkout_id FROM loadout_checkouts WHERE id = ?",
            (loadout_checkout_id,),
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return

        loadout_id, checkout_id = result

        # Update loadout checkout record
        cursor.execute(
            "UPDATE loadout_checkouts SET return_date = ?, rounds_fired = ?, rain_exposure = ?, ammo_type = ?, notes = ? WHERE id = ?",
            (
                int(datetime.now().timestamp()),
                rounds_fired_dict.get("total", 0),
                1 if rain_exposure else 0,
                ammo_type,
                notes,
                loadout_checkout_id,
            ),
        )

        # Get items and update status
        loadout_items = self.get_loadout_items(loadout_id)

        for item in loadout_items:
            # Get the checkout_id for this specific item
            cursor.execute(
                "SELECT id FROM checkouts WHERE item_id = ? AND actual_return IS NULL",
                (item.item_id,),
            )
            result = cursor.fetchone()

            if result:
                item_checkout_id = result[0]
                # Update checkout return date
                cursor.execute(
                    "UPDATE checkouts SET actual_return = ? WHERE id = ?",
                    (int(datetime.now().timestamp()), item_checkout_id),
                )

            # Update item status back to AVAILABLE
            if item.item_type == GearCategory.FIREARM:
                cursor.execute(
                    "UPDATE firearms SET status = ? WHERE id = ?",
                    (CheckoutStatus.AVAILABLE.value, item.item_id),
                )
            elif item.item_type == GearCategory.SOFT_GEAR:
                cursor.execute(
                    "UPDATE soft_gear SET status = ? WHERE id = ?",
                    (CheckoutStatus.AVAILABLE.value, item.item_id),
                )
            elif item.item_type == GearCategory.NFA_ITEM:
                cursor.execute(
                    "UPDATE nfa_items SET status = ? WHERE id = ?",
                    (CheckoutStatus.AVAILABLE.value, item.item_id),
                )

        # Update round counts per firearm
        for item in loadout_items:
            if (
                item.item_type == GearCategory.FIREARM
                and item.item_id in rounds_fired_dict
            ):
                self.update_firearm_rounds(
                    item.item_id, rounds_fired_dict[item.item_id]
                )

        # Create maintenance logs for each firearm in loadout
        for item in loadout_items:
            if (
                item.item_type == GearCategory.FIREARM
                and item.item_id in rounds_fired_dict
            ):
                rounds = rounds_fired_dict[item.item_id]
                firearm_id = item.item_id

                # FIRED_ROUNDS log
                if rounds > 0:
                    log = MaintenanceLog(
                        id=str(uuid.uuid4()),
                        item_id=firearm_id,
                        item_type=GearCategory.FIREARM,
                        log_type=MaintenanceType.FIRED_ROUNDS,
                        date=datetime.now(),
                        details=f"Rounds fired: {rounds}",
                        ammo_count=rounds,
                    )
                    cursor.execute(
                        "INSERT INTO maintenance_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            log.id,
                            log.item_id,
                            log.item_type.value,
                            log.log_type.value,
                            int(log.date.timestamp()),
                            log.details,
                            log.ammo_count,
                            log.photo_path,
                        ),
                    )

                # RAIN_EXPOSURE log
                if rain_exposure:
                    log = MaintenanceLog(
                        id=str(uuid.uuid4()),
                        item_id=firearm_id,
                        item_type=GearCategory.FIREARM,
                        log_type=MaintenanceType.RAIN_EXPOSURE,
                        date=datetime.now(),
                        details="Exposed to rain during use",
                    )
                    cursor.execute(
                        "INSERT INTO maintenance_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            log.id,
                            log.item_id,
                            log.item_type.value,
                            log.log_type.value,
                            int(log.date.timestamp()),
                            log.details,
                            log.ammo_count,
                            log.photo_path,
                        ),
                    )

                # CORROSIVE_AMMO log
                if "corrosive" in ammo_type.lower():
                    log = MaintenanceLog(
                        id=str(uuid.uuid4()),
                        item_id=firearm_id,
                        item_type=GearCategory.FIREARM,
                        log_type=MaintenanceType.CORROSIVE_AMMO,
                        date=datetime.now(),
                        details=f"Fired corrosive ammo ({ammo_type})",
                    )
                    cursor.execute(
                        "INSERT INTO maintenance_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            log.id,
                            log.item_id,
                            log.item_type.value,
                            log.log_type.value,
                            int(log.date.timestamp()),
                            log.details,
                            log.ammo_count,
                            log.photo_path,
                        ),
                    )

                # LEAD_AMMO log
                if "lead" in ammo_type.lower():
                    log = MaintenanceLog(
                        id=str(uuid.uuid4()),
                        item_id=firearm_id,
                        item_type=GearCategory.FIREARM,
                        log_type=MaintenanceType.LEAD_AMMO,
                        date=datetime.now(),
                        details=f"Fired lead ammo ({ammo_type})",
                    )
                    cursor.execute(
                        "INSERT INTO maintenance_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            log.id,
                            log.item_id,
                            log.item_type.value,
                            log.log_type.value,
                            int(log.date.timestamp()),
                            log.details,
                            log.ammo_count,
                            log.photo_path,
                        ),
                    )

        conn.commit()
        conn.close()

    # -------- EXPORT METHODS --------

    def export_full_inventory_csv(self, output_path: Path) -> None:
        import csv

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Firearms section
            writer.writerow(["=== FIREARMS ==="])
            writer.writerow(
                ["Name", "Caliber", "Serial", "Status", "Last Cleaned", "Notes"]
            )
            for fw in self.get_all_firearms():
                last_clean = self.last_cleaning_date(fw.id)
                writer.writerow(
                    [
                        fw.name,
                        fw.caliber,
                        fw.serial_number,
                        fw.status.value,
                        last_clean.strftime("%Y-%m-%d") if last_clean else "Never",
                        fw.notes,
                    ]
                )

            writer.writerow([])

            # Soft gear section
            writer.writerow(["=== SOFT GEAR ==="])
            writer.writerow(["Name", "Category", "Brand", "Status", "Notes"])
            for gear in self.get_all_soft_gear():
                writer.writerow(
                    [
                        gear.name,
                        gear.category,
                        gear.brand,
                        gear.status.value,
                        gear.notes,
                    ]
                )

            writer.writerow([])

            # Consumables section
            writer.writerow(["=== CONSUMABLES ==="])
            writer.writerow(
                ["Name", "Category", "Quantity", "Unit", "Min Qty", "Low Stock?"]
            )
            for c in self.get_all_consumables():
                low = "YES" if c.quantity <= c.min_quantity else ""
                writer.writerow(
                    [c.name, c.category, c.quantity, c.unit, c.min_quantity, low]
                )

            writer.writerow([])

            # Active checkouts
            writer.writerow(["=== ACTIVE CHECKOUTS ==="])
            writer.writerow(["Item", "Borrower", "Checkout Date", "Expected Return"])
            for checkout, borrower, item_name in self.get_active_checkouts():
                writer.writerow(
                    [
                        item_name,
                        borrower.name,
                        checkout.checkout_date.strftime("%Y-%m-%d"),
                        checkout.expected_return.strftime("%Y-%m-%d")
                        if checkout.expected_return
                        else "TBD",
                    ]
                )

    def parse_sectioned_csv(self, input_path: Path) -> dict[str, list[dict[str, str]]]:
        """
        Parses CSV file with === SECTION === headers.
        Returns dict mapping section names to list of row dicts.
        """
        import csv

        result = {}
        current_section = None
        section_headers = []
        row_number = 0

        try:
            with open(input_path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)

                for row_number, row in enumerate(reader, start=1):
                    if not row:
                        continue

                    first_cell = row[0].strip()

                    if first_cell.startswith("===") and first_cell.endswith("==="):
                        current_section = first_cell.replace("=", "").strip().upper()
                        result[current_section] = []
                        section_headers = []
                        continue

                    if first_cell.startswith("#"):
                        continue

                    if current_section is None:
                        continue

                    if section_headers:
                        row_dict = {}
                        for i, header in enumerate(section_headers):
                            value = row[i] if i < len(row) else ""
                            row_dict[header.strip()] = value.strip()
                        result[current_section].append(row_dict)
                    else:
                        section_headers = [cell.strip() for cell in row]

        except Exception as e:
            raise Exception(f"Error parsing CSV at row {row_number}: {str(e)}")

        return result

    def validate_firearm_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name", "caliber", "purchase_date"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "name" in row and len(row["name"]) > 200:
            errors.append(
                ValidationError(
                    row_num,
                    "FIREARM",
                    "name",
                    "invalid_length",
                    "Name exceeds 200 characters",
                    "warning",
                )
            )

        if "purchase_date" in row and row["purchase_date"]:
            try:
                datetime.fromisoformat(row["purchase_date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        "purchase_date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        if "status" in row and row["status"]:
            valid_statuses = [s.value for s in CheckoutStatus]
            if row["status"] not in valid_statuses:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        "status",
                        "invalid_enum",
                        f"Status must be one of: {', '.join(valid_statuses)}",
                        "error",
                    )
                )

        if "is_nfa" in row and row["is_nfa"]:
            if row["is_nfa"].upper() not in ["TRUE", "FALSE", "1", "0"]:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        "is_nfa",
                        "invalid_type",
                        "is_nfa must be TRUE/FALSE or 1/0",
                        "error",
                    )
                )

        if "rounds_fired" in row and row["rounds_fired"]:
            try:
                int(row["rounds_fired"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        "rounds_fired",
                        "invalid_type",
                        "rounds_fired must be an integer",
                        "error",
                    )
                )

        if "clean_interval_rounds" in row and row["clean_interval_rounds"]:
            try:
                int(row["clean_interval_rounds"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        "clean_interval_rounds",
                        "invalid_type",
                        "clean_interval_rounds must be an integer",
                        "error",
                    )
                )

        if "oil_interval_days" in row and row["oil_interval_days"]:
            try:
                int(row["oil_interval_days"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        "oil_interval_days",
                        "invalid_type",
                        "oil_interval_days must be an integer",
                        "error",
                    )
                )

        if "transfer_status" in row and row["transfer_status"]:
            valid_statuses = [s.value for s in TransferStatus]
            if row["transfer_status"] not in valid_statuses:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        "transfer_status",
                        "invalid_enum",
                        f"transfer_status must be one of: {', '.join(valid_statuses)}",
                        "error",
                    )
                )

        return errors

    def validate_nfa_item_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = [
            "name",
            "nfa_type",
            "serial_number",
            "tax_stamp_id",
            "purchase_date",
        ]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "NFA_ITEM",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "nfa_type" in row and row["nfa_type"]:
            valid_types = [t.value for t in NFAItemType]
            if row["nfa_type"] not in valid_types:
                errors.append(
                    ValidationError(
                        row_num,
                        "NFA_ITEM",
                        "nfa_type",
                        "invalid_enum",
                        f"nfa_type must be one of: {', '.join(valid_types)}",
                        "error",
                    )
                )

        if "status" in row and row["status"]:
            valid_statuses = [s.value for s in CheckoutStatus]
            if row["status"] not in valid_statuses:
                errors.append(
                    ValidationError(
                        row_num,
                        "NFA_ITEM",
                        "status",
                        "invalid_enum",
                        f"Status must be one of: {', '.join(valid_statuses)}",
                        "error",
                    )
                )

        if "purchase_date" in row and row["purchase_date"]:
            try:
                datetime.fromisoformat(row["purchase_date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "NFA_ITEM",
                        "purchase_date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        return errors

    def validate_soft_gear_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name", "category", "purchase_date"]
        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "SOFT_GEAR",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "status" in row and row["status"]:
            valid_statuses = [s.value for s in CheckoutStatus]
            if row["status"] not in valid_statuses:
                errors.append(
                    ValidationError(
                        row_num,
                        "SOFT_GEAR",
                        "status",
                        "invalid_enum",
                        f"Status must be one of: {', '.join(valid_statuses)}",
                        "error",
                    )
                )

        if "purchase_date" in row and row["purchase_date"]:
            try:
                datetime.fromisoformat(row["purchase_date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "SOFT_GEAR",
                        "purchase_date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        return errors

    def validate_attachment_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name", "category", "brand", "model"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "ATTACHMENT",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "zero_distance_yards" in row and row["zero_distance_yards"]:
            try:
                int(row["zero_distance_yards"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "ATTACHMENT",
                        "zero_distance_yards",
                        "invalid_type",
                        "zero_distance_yards must be an integer",
                        "error",
                    )
                )

        if "purchase_date" in row and row["purchase_date"]:
            try:
                datetime.fromisoformat(row["purchase_date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "ATTACHMENT",
                        "purchase_date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        return errors

    def validate_consumable_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name", "category", "unit", "quantity"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "CONSUMABLE",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "quantity" in row:
            try:
                qty = int(row["quantity"])
                if qty < 0:
                    errors.append(
                        ValidationError(
                            row_num,
                            "CONSUMABLE",
                            "quantity",
                            "invalid_value",
                            "quantity must be >= 0",
                            "error",
                        )
                    )
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "CONSUMABLE",
                        "quantity",
                        "invalid_type",
                        "quantity must be an integer",
                        "error",
                    )
                )

        if "min_quantity" in row:
            try:
                min_qty = int(row["min_quantity"])
                if min_qty < 0:
                    errors.append(
                        ValidationError(
                            row_num,
                            "CONSUMABLE",
                            "min_quantity",
                            "invalid_value",
                            "min_quantity must be >= 0",
                            "error",
                        )
                    )
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "CONSUMABLE",
                        "min_quantity",
                        "invalid_type",
                        "min_quantity must be an integer",
                        "error",
                    )
                )

        return errors

    def validate_reload_batch_row(
        self, row: dict, row_num: int
    ) -> list[ValidationError]:
        errors = []
        required = ["cartridge", "date_created", "bullet_maker", "bullet_model"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "RELOAD_BATCH",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "date_created" in row and row["date_created"]:
            try:
                datetime.fromisoformat(row["date_created"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "RELOAD_BATCH",
                        "date_created",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        if "test_date" in row and row["test_date"]:
            try:
                datetime.fromisoformat(row["test_date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "RELOAD_BATCH",
                        "test_date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        numeric_fields = [
            "bullet_weight_gr",
            "powder_charge_gr",
            "coal_in",
            "avg_velocity",
            "es",
            "sd",
            "group_size_inches",
        ]
        for field in numeric_fields:
            if field in row and row[field]:
                try:
                    float(row[field])
                except ValueError:
                    errors.append(
                        ValidationError(
                            row_num,
                            "RELOAD_BATCH",
                            field,
                            "invalid_type",
                            f"{field} must be a number",
                            "error",
                        )
                    )

        return errors

    def validate_loadout_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "LOADOUT",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "created_date" in row and row["created_date"]:
            try:
                datetime.fromisoformat(row["created_date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "LOADOUT",
                        "created_date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        return errors

    def validate_loadout_item_row(
        self, row: dict, row_num: int
    ) -> list[ValidationError]:
        errors = []
        required = ["loadout_id", "item_id", "item_type"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "LOADOUT_ITEM",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "item_type" in row and row["item_type"]:
            valid_types = [t.value for t in GearCategory]
            if row["item_type"] not in valid_types:
                errors.append(
                    ValidationError(
                        row_num,
                        "LOADOUT_ITEM",
                        "item_type",
                        "invalid_enum",
                        f"item_type must be one of: {', '.join(valid_types)}",
                        "error",
                    )
                )

        return errors

    def validate_loadout_consumable_row(
        self, row: dict, row_num: int
    ) -> list[ValidationError]:
        errors = []
        required = ["loadout_id", "consumable_id", "quantity"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "LOADOUT_CONSUMABLE",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "quantity" in row:
            try:
                qty = int(row["quantity"])
                if qty < 0:
                    errors.append(
                        ValidationError(
                            row_num,
                            "LOADOUT_CONSUMABLE",
                            "quantity",
                            "invalid_value",
                            "quantity must be >= 0",
                            "error",
                        )
                    )
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "LOADOUT_CONSUMABLE",
                        "quantity",
                        "invalid_type",
                        "quantity must be an integer",
                        "error",
                    )
                )

        return errors

    def validate_borrower_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "BORROWER",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        return errors

    def validate_checkout_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["item_id", "item_type", "borrower_name", "checkout_date"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "CHECKOUT",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "item_type" in row and row["item_type"]:
            valid_types = [t.value for t in GearCategory]
            if row["item_type"] not in valid_types:
                errors.append(
                    ValidationError(
                        row_num,
                        "CHECKOUT",
                        "item_type",
                        "invalid_enum",
                        f"item_type must be one of: {', '.join(valid_types)}",
                        "error",
                    )
                )

        if "checkout_date" in row and row["checkout_date"]:
            try:
                datetime.fromisoformat(row["checkout_date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "CHECKOUT",
                        "checkout_date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        if "expected_return" in row and row["expected_return"]:
            try:
                datetime.fromisoformat(row["expected_return"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "CHECKOUT",
                        "expected_return",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        if "actual_return" in row and row["actual_return"]:
            try:
                datetime.fromisoformat(row["actual_return"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "CHECKOUT",
                        "actual_return",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        return errors

    def validate_maintenance_log_row(
        self, row: dict, row_num: int
    ) -> list[ValidationError]:
        errors = []
        required = ["item_id", "item_type", "log_type", "date"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "MAINTENANCE_LOG",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "item_type" in row and row["item_type"]:
            valid_types = [t.value for t in GearCategory]
            if row["item_type"] not in valid_types:
                errors.append(
                    ValidationError(
                        row_num,
                        "MAINTENANCE_LOG",
                        "item_type",
                        "invalid_enum",
                        f"item_type must be one of: {', '.join(valid_types)}",
                        "error",
                    )
                )

        if "log_type" in row and row["log_type"]:
            valid_types = [t.value for t in MaintenanceType]
            if row["log_type"] not in valid_types:
                errors.append(
                    ValidationError(
                        row_num,
                        "MAINTENANCE_LOG",
                        "log_type",
                        "invalid_enum",
                        f"log_type must be one of: {', '.join(valid_types)}",
                        "error",
                    )
                )

        if "date" in row and row["date"]:
            try:
                datetime.fromisoformat(row["date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "MAINTENANCE_LOG",
                        "date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        if "ammo_count" in row and row["ammo_count"]:
            try:
                int(row["ammo_count"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "MAINTENANCE_LOG",
                        "ammo_count",
                        "invalid_type",
                        "ammo_count must be an integer",
                        "error",
                    )
                )

        return errors

    def validate_transfer_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = [
            "firearm_id",
            "transfer_date",
            "buyer_name",
            "buyer_address",
            "buyer_dl_number",
        ]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "TRANSFER",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "transfer_date" in row and row["transfer_date"]:
            try:
                datetime.fromisoformat(row["transfer_date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "TRANSFER",
                        "transfer_date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        if "sale_price" in row and row["sale_price"]:
            try:
                price = float(row["sale_price"])
                if price < 0:
                    errors.append(
                        ValidationError(
                            row_num,
                            "TRANSFER",
                            "sale_price",
                            "invalid_value",
                            "sale_price must be >= 0",
                            "error",
                        )
                    )
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "TRANSFER",
                        "sale_price",
                        "invalid_type",
                        "sale_price must be a number",
                        "error",
                    )
                )

        return errors

    def validate_csv_data(self, parsed_data: dict) -> list[ValidationError]:
        all_errors = []
        validators = {
            "FIREARMS": self.validate_firearm_row,
            "NFA ITEMS": self.validate_nfa_item_row,
            "SOFT GEAR": self.validate_soft_gear_row,
            "ATTACHMENTS": self.validate_attachment_row,
            "CONSUMABLES": self.validate_consumable_row,
            "RELOAD BATCHES": self.validate_reload_batch_row,
            "LOADOUTS": self.validate_loadout_row,
            "LOADOUT ITEMS": self.validate_loadout_item_row,
            "LOADOUT CONSUMABLES": self.validate_loadout_consumable_row,
            "BORROWERS": self.validate_borrower_row,
            "CHECKOUT HISTORY": self.validate_checkout_row,
            "MAINTENANCE LOGS": self.validate_maintenance_log_row,
            "TRANSFERS": self.validate_transfer_row,
        }

        for section_name, rows in parsed_data.items():
            if section_name in validators:
                validator = validators[section_name]
                for i, row in enumerate(rows, start=1):
                    errors = validator(row, i)
                    all_errors.extend(errors)

        return all_errors

    def detect_duplicate_firearm(self, serial_number: str) -> Firearm | None:
        if not serial_number:
            return None
        firearms = self.get_all_firearms()
        for fw in firearms:
            if fw.serial_number == serial_number:
                return fw
        return None

    def detect_duplicate_nfa_item(self, name: str) -> NFAItem | None:
        if not name:
            return None
        nfa_items = self.get_all_nfa_items()
        for item in nfa_items:
            if item.name == name:
                return item
        return None

    def detect_duplicate_soft_gear(self, name: str) -> SoftGear | None:
        if not name:
            return None
        gear_items = self.get_all_soft_gear()
        for gear in gear_items:
            if gear.name == name:
                return gear
        return None

    def detect_duplicate_attachment(self, name: str) -> Attachment | None:
        if not name:
            return None
        attachments = self.get_all_attachments()
        for att in attachments:
            if att.name == name:
                return att
        return None

    def detect_duplicate_consumable(self, name: str) -> Consumable | None:
        if not name:
            return None
        consumables = self.get_all_consumables()
        for cons in consumables:
            if cons.name == name:
                return cons
        return None

    def detect_duplicate_reload_batch(
        self, cartridge: str, bullet_model: str
    ) -> ReloadBatch | None:
        if not cartridge or not bullet_model:
            return None
        batches = self.get_all_reload_batches()
        for batch in batches:
            if batch.cartridge == cartridge and batch.bullet_model == bullet_model:
                return batch
        return None

    def detect_duplicate_borrower(self, name: str, email: str) -> Borrower | None:
        if not name:
            return None
        borrowers = self.get_all_borrowers()
        for borrower in borrowers:
            if borrower.name == name and borrower.email == email:
                return borrower
        return None

    def detect_duplicate_loadout(self, name: str) -> Loadout | None:
        if not name:
            return None
        loadouts = self.get_all_loadouts()
        for loadout in loadouts:
            if loadout.name == name:
                return loadout

    def export_complete_csv(self, output_path: Path) -> None:
        import csv

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            writer.writerow(["=== METADATA ==="])
            writer.writerow(
                ["Export Date", "GearTracker Version", "Export Type", "Dry Run"]
            )
            writer.writerow(
                [datetime.now().strftime("%Y-%m-%d"), "0.1.0-alpha.2", "FULL", "FALSE"]
            )
            writer.writerow([])

            writer.writerow(["=== FIREARMS ==="])
            writer.writerow(
                [
                    "id",
                    "name",
                    "caliber",
                    "serial_number",
                    "purchase_date",
                    "notes",
                    "status",
                    "is_nfa",
                    "nfa_type",
                    "tax_stamp_id",
                    "form_type",
                    "barrel_length",
                    "trust_name",
                    "transfer_status",
                    "rounds_fired",
                    "clean_interval_rounds",
                    "oil_interval_days",
                    "needs_maintenance",
                    "maintenance_conditions",
                ]
            )
            for fw in self.get_all_firearms():
                writer.writerow(
                    [
                        fw.id,
                        fw.name,
                        fw.caliber,
                        fw.serial_number,
                        fw.purchase_date.strftime("%Y-%m-%d"),
                        fw.notes,
                        fw.status.value,
                        1 if fw.is_nfa else 0,
                        fw.nfa_type.value if fw.nfa_type else "",
                        fw.tax_stamp_id,
                        fw.form_type,
                        fw.barrel_length,
                        fw.trust_name,
                        fw.transfer_status.value,
                        fw.rounds_fired,
                        fw.clean_interval_rounds,
                        fw.oil_interval_days,
                        1 if fw.needs_maintenance else 0,
                        fw.maintenance_conditions,
                    ]
                )
            writer.writerow([])

            writer.writerow(["=== NFA ITEMS ==="])
            writer.writerow(
                [
                    "id",
                    "name",
                    "nfa_type",
                    "manufacturer",
                    "serial_number",
                    "tax_stamp_id",
                    "caliber_bore",
                    "purchase_date",
                    "form_type",
                    "trust_name",
                    "notes",
                    "status",
                ]
            )
            for nfa in self.get_all_nfa_items():
                writer.writerow(
                    [
                        nfa.id,
                        nfa.name,
                        nfa.nfa_type.value,
                        nfa.manufacturer,
                        nfa.serial_number,
                        nfa.tax_stamp_id,
                        nfa.caliber_bore,
                        nfa.purchase_date.strftime("%Y-%m-%d"),
                        nfa.form_type,
                        nfa.trust_name,
                        nfa.notes,
                        nfa.status.value,
                    ]
                )
            writer.writerow([])

            writer.writerow(["=== SOFT GEAR ==="])
            writer.writerow(
                ["id", "name", "category", "brand", "purchase_date", "notes", "status"]
            )
            for gear in self.get_all_soft_gear():
                writer.writerow(
                    [
                        gear.id,
                        gear.name,
                        gear.category,
                        gear.brand,
                        gear.purchase_date.strftime("%Y-%m-%d"),
                        gear.notes,
                        gear.status.value,
                    ]
                )
            writer.writerow([])

            writer.writerow(["=== ATTACHMENTS ==="])
            writer.writerow(
                [
                    "id",
                    "name",
                    "category",
                    "brand",
                    "model",
                    "purchase_date",
                    "serial_number",
                    "mounted_on_firearm_id",
                    "mount_position",
                    "zero_distance_yards",
                    "zero_notes",
                    "notes",
                ]
            )
            for att in self.get_all_attachments():
                writer.writerow(
                    [
                        att.id,
                        att.name,
                        att.category,
                        att.brand,
                        att.model,
                        att.purchase_date.strftime("%Y-%m-%d")
                        if att.purchase_date
                        else "",
                        att.serial_number,
                        att.mounted_on_firearm_id or "",
                        att.mount_position,
                        att.zero_distance_yards or "",
                        att.zero_notes,
                        att.notes,
                    ]
                )
            writer.writerow([])

            writer.writerow(["=== CONSUMABLES ==="])
            writer.writerow(
                ["id", "name", "category", "unit", "quantity", "min_quantity", "notes"]
            )
            for cons in self.get_all_consumables():
                writer.writerow(
                    [
                        cons.id,
                        cons.name,
                        cons.category,
                        cons.unit,
                        cons.quantity,
                        cons.min_quantity,
                        cons.notes,
                    ]
                )
            writer.writerow([])

            writer.writerow(["=== RELOAD BATCHES ==="])
            writer.writerow(
                [
                    "id",
                    "cartridge",
                    "firearm_id",
                    "date_created",
                    "bullet_maker",
                    "bullet_model",
                    "bullet_weight_gr",
                    "powder_name",
                    "powder_charge_gr",
                    "powder_lot",
                    "primer_maker",
                    "primer_type",
                    "case_brand",
                    "case_times_fired",
                    "case_prep_notes",
                    "coal_in",
                    "crimp_style",
                    "test_date",
                    "avg_velocity",
                    "es",
                    "sd",
                    "group_size_inches",
                    "group_distance_yards",
                    "notes",
                ]
            )
            for batch in self.get_all_reload_batches():
                writer.writerow(
                    [
                        batch.id,
                        batch.cartridge,
                        batch.firearm_id or "",
                        batch.date_created.strftime("%Y-%m-%d"),
                        batch.bullet_maker,
                        batch.bullet_model,
                        batch.bullet_weight_gr or "",
                        batch.powder_name,
                        batch.powder_charge_gr or "",
                        batch.powder_lot,
                        batch.primer_maker,
                        batch.primer_type,
                        batch.case_brand,
                        batch.case_times_fired or "",
                        batch.case_prep_notes,
                        batch.coal_in or "",
                        batch.crimp_style,
                        batch.test_date.strftime("%Y-%m-%d") if batch.test_date else "",
                        batch.avg_velocity or "",
                        batch.es or "",
                        batch.sd or "",
                        batch.group_size_inches or "",
                        batch.group_distance_yards or "",
                        batch.notes,
                    ]
                )
            writer.writerow([])

            writer.writerow(["=== LOADOUTS ==="])
            writer.writerow(["id", "name", "description", "created_date", "notes"])
            for loadout in self.get_all_loadouts():
                writer.writerow(
                    [
                        loadout.id,
                        loadout.name,
                        loadout.description,
                        loadout.created_date.strftime("%Y-%m-%d")
                        if loadout.created_date
                        else "",
                        loadout.notes,
                    ]
                )
            writer.writerow([])

            writer.writerow(["=== LOADOUT ITEMS ==="])
            writer.writerow(["id", "loadout_id", "item_id", "item_type", "notes"])
            for li in self.get_all_loadouts():
                for item in self.get_loadout_items(li.id):
                    writer.writerow(
                        [
                            item.id,
                            item.loadout_id,
                            item.item_id,
                            item.item_type.value,
                            item.notes,
                        ]
                    )
            writer.writerow([])

            writer.writerow(["=== LOADOUT CONSUMABLES ==="])
            writer.writerow(["id", "loadout_id", "consumable_id", "quantity", "notes"])
            for loadout in self.get_all_loadouts():
                for lc in self.get_loadout_consumables(loadout.id):
                    writer.writerow(
                        [lc.id, lc.loadout_id, lc.consumable_id, lc.quantity, lc.notes]
                    )
            writer.writerow([])

            writer.writerow(["=== BORROWERS ==="])
            writer.writerow(["id", "name", "phone", "email", "notes"])
            for borrower in self.get_all_borrowers():
                writer.writerow(
                    [
                        borrower.id,
                        borrower.name,
                        borrower.phone,
                        borrower.email,
                        borrower.notes,
                    ]
                )
            writer.writerow([])

            writer.writerow(["=== CHECKOUT HISTORY ==="])
            writer.writerow(
                [
                    "id",
                    "item_id",
                    "item_type",
                    "borrower_name",
                    "checkout_date",
                    "expected_return",
                    "actual_return",
                    "notes",
                ]
            )
            for checkout in self.get_all_checkout_history():
                writer.writerow(
                    [
                        checkout.id,
                        checkout.item_id,
                        checkout.item_type.value,
                        checkout.borrower_name,
                        checkout.checkout_date.strftime("%Y-%m-%d"),
                        checkout.expected_return.strftime("%Y-%m-%d")
                        if checkout.expected_return
                        else "",
                        checkout.actual_return.strftime("%Y-%m-%d")
                        if checkout.actual_return
                        else "",
                        checkout.notes,
                    ]
                )
            writer.writerow([])

            writer.writerow(["=== MAINTENANCE LOGS ==="])
            writer.writerow(
                [
                    "id",
                    "item_id",
                    "item_type",
                    "log_type",
                    "date",
                    "details",
                    "ammo_count",
                    "photo_path",
                ]
            )
            for log in self.get_all_maintenance_logs():
                writer.writerow(
                    [
                        log.id,
                        log.item_id,
                        log.item_type.value,
                        log.log_type.value,
                        log.date.strftime("%Y-%m-%d"),
                        log.details,
                        log.ammo_count or "",
                        log.photo_path or "",
                    ]
                )
            writer.writerow([])

            writer.writerow(["=== TRANSFERS ==="])
            writer.writerow(
                [
                    "id",
                    "firearm_id",
                    "transfer_date",
                    "buyer_name",
                    "buyer_address",
                    "buyer_dl_number",
                    "buyer_ltc_number",
                    "sale_price",
                    "ffl_dealer",
                    "ffl_license",
                    "notes",
                ]
            )
            for transfer, _ in self.get_all_transfers():
                writer.writerow(
                    [
                        transfer.id,
                        transfer.firearm_id,
                        transfer.transfer_date.strftime("%Y-%m-%d"),
                        transfer.buyer_name,
                        transfer.buyer_address,
                        transfer.buyer_dl_number,
                        transfer.buyer_ltc_number,
                        transfer.sale_price,
                        transfer.ffl_dealer,
                        transfer.ffl_license,
                        transfer.notes,
                    ]
                )

    def get_entity_import_order(self) -> list[str]:
        """
        Returns entity types in dependency order for import.
        Entities with no dependencies first, then dependent entities.
        """
        return [
            "BORROWERS",  # No dependencies
            "FIREARMS",  # No dependencies
            "NFA ITEMS",  # No dependencies
            "SOFT GEAR",  # No dependencies
            "ATTACHMENTS",  # Depends on: firearms (optional)
            "CONSUMABLES",  # No dependencies
            "RELOAD BATCHES",  # Depends on: firearms (optional)
            "LOADOUTS",  # No dependencies
            "LOADOUT ITEMS",  # Depends on: loadouts + firearms/nfa/soft_gear
            "LOADOUT CONSUMABLES",  # Depends on: loadouts + consumables
            "CHECKOUT HISTORY",  # Depends on: items + borrowers
            "MAINTENANCE LOGS",  # Depends on: items (firearms/nfa/soft_gear)
            "TRANSFERS",  # Depends on: firearms
        ]

    def generate_csv_template(self, output_path: Path, entity_type: str | None = None) -> None:
        """
        Generates CSV template with validation comments.
        If entity_type is None, generates complete template.
        Otherwise, generates single entity template.
        """
        import csv

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            if entity_type is None:
                self._write_full_template(writer)
            else:
                self._write_single_template(writer, entity_type)

    def _write_full_template(self, writer) -> None:
        """Writes complete CSV template with all sections."""
        writer.writerow(["=== METADATA ==="])
        writer.writerow(["Export Date,GearTracker Version,Export Type,Dry Run"])
        writer.writerow(["# Enter export date in YYYY-MM-DD format"])
        writer.writerow(["# Version: e.g., 0.1.0-alpha.2"])
        writer.writerow(["# Export Type: FULL or BACKUP"])
        writer.writerow(["2026-01-21,0.1.0-alpha.2,FULL,FALSE"])
        writer.writerow([])

        writer.writerow(["=== FIREARMS ==="])
        writer.writerow([
            "# Required: name, caliber, purchase_date",
            "# Optional: serial_number (leave blank if none)",
            "# Status values: AVAILABLE, CHECKED_OUT, LOST, RETIRED",
            "# is_nfa: TRUE or FALSE",
            "# nfa_type (if is_nfa=TRUE): SBR, SBS",
            "# transfer_status: OWNED or TRANSFERRED",
            "# Dates format: YYYY-MM-DD",
            "id,name,caliber,serial_number,purchase_date,notes",
            "status,is_nfa,nfa_type,tax_stamp_id,form_type",
            "barrel_length,trust_name,transfer_status,rounds_fired",
            "clean_interval_rounds,oil_interval_days,needs_maintenance,maintenance_conditions"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,S&W 1854,.45-70 Govt,ABC123,2025-01-15,My favorite lever gun",
            "AVAILABLE,FALSE,,,,,OWNED,0,500,90,FALSE,"
        ])
        writer.writerow([])

        writer.writerow(["=== NFA ITEMS ==="])
        writer.writerow([
            "# Required: name, nfa_type, manufacturer, serial_number, tax_stamp_id, purchase_date",
            "# NFA type values: SUPPRESSOR, SBR, SBS, AOW, DD",
            "# Status values: AVAILABLE, CHECKED_OUT, LOST, RETIRED",
            "# Dates format: YYYY-MM-DD",
            "id,name,nfa_type,manufacturer,serial_number,tax_stamp_id",
            "caliber_bore,purchase_date,form_type,trust_name,notes,status"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,Suppressor X,SUPPRESSOR,Manufacturer,1234,STAMP123,.30,2025-01-15,Form 1,My Trust,,AVAILABLE"
        ])
        writer.writerow([])

        writer.writerow(["=== SOFT GEAR ==="])
        writer.writerow([
            "# Required: name, category, brand, purchase_date",
            "# Status values: AVAILABLE, CHECKED_OUT, LOST, RETIRED",
            "# Dates format: YYYY-MM-DD",
            "id,name,category,brand,purchase_date,notes,status"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,Tactical Vest,Armor,Brand X,2025-01-15,,AVAILABLE"
        ])
        writer.writerow([])

        writer.writerow(["=== ATTACHMENTS ==="])
        writer.writerow([
            "# Required: name, category, brand, model",
            "# Optional: mounted_on_firearm_id (leave blank if unmounted)",
            "# zero_distance_yards: integer in yards",
            "# Dates format: YYYY-MM-DD",
            "id,name,category,brand,model,purchase_date,serial_number",
            "mounted_on_firearm_id,mount_position,zero_distance_yards,zero_notes,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,Red Dot Sight,optic,Brand,Model X,2025-01-15,,,,100,Zeroed at 100 yards,"
        ])
        writer.writerow([])

        writer.writerow(["=== CONSUMABLES ==="])
        writer.writerow([
            "# Required: name, category, unit, quantity",
            "# quantity and min_quantity: integers >= 0",
            "id,name,category,unit,quantity,min_quantity,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,.308 Ammo,Ammunition,rounds,500,50,"
        ])
        writer.writerow([])

        writer.writerow(["=== RELOAD BATCHES ==="])
        writer.writerow([
            "# Required: cartridge, date_created, bullet_maker, bullet_model",
            "# Optional: firearm_id (leave blank if none)",
            "# bullet_weight_gr, powder_charge_gr, coal_in: numbers",
            "# Dates format: YYYY-MM-DD",
            "id,cartridge,firearm_id,date_created,bullet_maker,bullet_model",
            "bullet_weight_gr,powder_name,powder_charge_gr,powder_lot",
            "primer_maker,primer_type,case_brand,case_times_fired,case_prep_notes",
            "coal_in,crimp_style,test_date,avg_velocity,es,sd",
            "group_size_inches,group_distance_yards,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,.308,,2025-01-15,Hornady,ELD-X,178,",
            "Varget,46.0,,,,2.800,crimp,,2025-01-20,2750,35,12,1.5,100,"
        ])
        writer.writerow([])

        writer.writerow(["=== LOADOUTS ==="])
        writer.writerow([
            "# Required: name",
            "# Optional: description, created_date, notes",
            "# Dates format: YYYY-MM-DD",
            "id,name,description,created_date,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,Hunting Loadout,Full kit for hunting,,"
        ])
        writer.writerow([])

        writer.writerow(["=== LOADOUT ITEMS ==="])
        writer.writerow([
            "# Required: loadout_id, item_id, item_type",
            "# item_type values: FIREARM, SOFT_GEAR, NFA_ITEM, CONSUMABLE",
            "id,loadout_id,item_id,item_type,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,[LOADOUT_ID],[ITEM_ID],FIREARM,"
        ])
        writer.writerow([])

        writer.writerow(["=== LOADOUT CONSUMABLES ==="])
        writer.writerow([
            "# Required: loadout_id, consumable_id, quantity",
            "# quantity: integer >= 0",
            "id,loadout_id,consumable_id,quantity,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,[LOADOUT_ID],[CONSUMABLE_ID],20,"
        ])
        writer.writerow([])

        writer.writerow(["=== BORROWERS ==="])
        writer.writerow([
            "# Required: name",
            "# Optional: phone, email, notes",
            "id,name,phone,email,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,John Doe,555-123-4567,john@example.com,"
        ])
        writer.writerow([])

        writer.writerow(["=== CHECKOUT HISTORY ==="])
        writer.writerow([
            "# Required: item_id, item_type, borrower_name, checkout_date",
            "# item_type values: FIREARM, SOFT_GEAR, NFA_ITEM, CONSUMABLE",
            "# Dates format: YYYY-MM-DD",
            "id,item_id,item_type,borrower_name,checkout_date",
            "expected_return,actual_return,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,[ITEM_ID],FIREARM,John Doe,2025-01-15,2025-01-20,,"
        ])
        writer.writerow([])

        writer.writerow(["=== MAINTENANCE LOGS ==="])
        writer.writerow([
            "# Required: item_id, item_type, log_type, date",
            "# item_type values: FIREARM, SOFT_GEAR, NFA_ITEM, CONSUMABLE",
            "# log_type values: CLEANING, LUBRICATION, REPAIR, ZEROING, HUNTING, INSPECTION,",
            "#                FIRED_ROUNDS, OILING, RAIN_EXPOSURE, CORROSIVE_AMMO, LEAD_AMMO",
            "# ammo_count: integer (optional)",
            "# Dates format: YYYY-MM-DD",
            "id,item_id,item_type,log_type,date,details,ammo_count,photo_path"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,[ITEM_ID],FIREARM,CLEANING,2025-01-15,Cleaned after hunting,0,"
        ])
        writer.writerow([])

        writer.writerow(["=== TRANSFERS ==="])
        writer.writerow([
            "# Required: firearm_id, transfer_date, buyer_name, buyer_address, buyer_dl_number",
            "# sale_price: number >= 0",
            "# Dates format: YYYY-MM-DD",
            "id,firearm_id,transfer_date,buyer_name,buyer_address",
            "buyer_dl_number,buyer_ltc_number,sale_price,ffl_dealer,ffl_license,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,[FIREARM_ID],2025-01-15,Jane Smith,123 Main St,DL123,,500.00,,,,"
        ])

    def _write_single_template(self, writer, entity_type: str) -> None:
        """Writes single entity template."""
        templates = {
            'firearms': self._firearm_template,
            'nfa_items': self._nfa_item_template,
            'soft_gear': self._soft_gear_template,
            'attachments': self._attachment_template,
            'consumables': self._consumable_template,
            'reload_batches': self._reload_batch_template,
            'loadouts': self._loadout_template,
            'borrowers': self._borrower_template,
        }

        if entity_type.lower() in templates:
            templates[entity_type.lower()](writer)

    def _firearm_template(self, writer) -> None:
        writer.writerow(["=== FIREARMS ==="])
        writer.writerow([
            "# Required: name, caliber, purchase_date",
            "# Status values: AVAILABLE, CHECKED_OUT, LOST, RETIRED",
            "# is_nfa: TRUE or FALSE",
            "# transfer_status: OWNED or TRANSFERRED",
            "# Dates format: YYYY-MM-DD",
            "id,name,caliber,serial_number,purchase_date,notes",
            "status,is_nfa,nfa_type,tax_stamp_id,form_type",
            "barrel_length,trust_name,transfer_status,rounds_fired",
            "clean_interval_rounds,oil_interval_days,needs_maintenance,maintenance_conditions"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,S&W 1854,.45-70 Govt,ABC123,2025-01-15,,AVAILABLE,FALSE,,,,,OWNED,0,500,90,FALSE,"
        ])

    def _nfa_item_template(self, writer) -> None:
        writer.writerow(["=== NFA ITEMS ==="])
        writer.writerow([
            "# Required: name, nfa_type, manufacturer, serial_number, tax_stamp_id, purchase_date",
            "# NFA type values: SUPPRESSOR, SBR, SBS, AOW, DD",
            "# Status values: AVAILABLE, CHECKED_OUT, LOST, RETIRED",
            "# Dates format: YYYY-MM-DD",
            "id,name,nfa_type,manufacturer,serial_number,tax_stamp_id",
            "caliber_bore,purchase_date,form_type,trust_name,notes,status"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,Suppressor X,SUPPRESSOR,Manufacturer,1234,STAMP123,.30,2025-01-15,Form 1,My Trust,,AVAILABLE"
        ])

    def _soft_gear_template(self, writer) -> None:
        writer.writerow(["=== SOFT GEAR ==="])
        writer.writerow([
            "# Required: name, category, brand, purchase_date",
            "# Status values: AVAILABLE, CHECKED_OUT, LOST, RETIRED",
            "# Dates format: YYYY-MM-DD",
            "id,name,category,brand,purchase_date,notes,status"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,Tactical Vest,Armor,Brand X,2025-01-15,,AVAILABLE"
        ])

    def _attachment_template(self, writer) -> None:
        writer.writerow(["=== ATTACHMENTS ==="])
        writer.writerow([
            "# Required: name, category, brand, model",
            "# Optional: mounted_on_firearm_id (leave blank if unmounted)",
            "# zero_distance_yards: integer in yards",
            "# Dates format: YYYY-MM-DD",
            "id,name,category,brand,model,purchase_date,serial_number",
            "mounted_on_firearm_id,mount_position,zero_distance_yards,zero_notes,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,Red Dot Sight,optic,Brand,Model X,2025-01-15,,,,100,Zeroed at 100 yards,"
        ])

    def _consumable_template(self, writer) -> None:
        writer.writerow(["=== CONSUMABLES ==="])
        writer.writerow([
            "# Required: name, category, unit, quantity",
            "# quantity and min_quantity: integers >= 0",
            "id,name,category,unit,quantity,min_quantity,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,.308 Ammo,Ammunition,rounds,500,50,"
        ])

    def _reload_batch_template(self, writer) -> None:
        writer.writerow(["=== RELOAD BATCHES ==="])
        writer.writerow([
            "# Required: cartridge, date_created, bullet_maker, bullet_model",
            "# Optional: firearm_id (leave blank if none)",
            "# bullet_weight_gr, powder_charge_gr, coal_in: numbers",
            "# Dates format: YYYY-MM-DD",
            "id,cartridge,firearm_id,date_created,bullet_maker,bullet_model",
            "bullet_weight_gr,powder_name,powder_charge_gr,powder_lot",
            "primer_maker,primer_type,case_brand,case_times_fired,case_prep_notes",
            "coal_in,crimp_style,test_date,avg_velocity,es,sd",
            "group_size_inches,group_distance_yards,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,.308,,2025-01-15,Hornady,ELD-X,178,",
            "Varget,46.0,,,,2.800,crimp,,2025-01-20,2750,35,12,1.5,100,"
        ])

    def _loadout_template(self, writer) -> None:
        writer.writerow(["=== LOADOUTS ==="])
        writer.writerow([
            "# Required: name",
            "# Optional: description, created_date, notes",
            "# Dates format: YYYY-MM-DD",
            "id,name,description,created_date,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,Hunting Loadout,Full kit for hunting,,"
        ])

    def _borrower_template(self, writer) -> None:
        writer.writerow(["=== BORROWERS ==="])
        writer.writerow([
            "# Required: name",
            "# Optional: phone, email, notes",
            "id,name,phone,email,notes"
        ])
        writer.writerow([
            "#550e8400-e29b-41d4-a716-4466554400000,John Doe,555-123-4567,john@example.com,"
        ])

    def _parse_date_str(self, date_str: str) -> datetime | None:
        """Parse ISO date string (YYYY-MM-DD) to datetime."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")

    def _parse_bool_str(self, bool_str: str) -> bool:
        """Parse boolean string (TRUE/FALSE/1/0) to bool."""
        if not bool_str:
            return False
        bool_str = bool_str.strip().upper()
        if bool_str in ['TRUE', '1']:
            return True
        elif bool_str in ['FALSE', '0']:
            return False
        else:
            raise ValueError(f"Invalid boolean value: {bool_str}. Use TRUE/FALSE or 1/0.")

    def _parse_int_str(self, int_str: str, allow_empty: bool = False) -> int | None:
        """Parse integer string to int."""
        if not int_str and allow_empty:
            return None
        try:
            return int(int_str)
        except ValueError:
            raise ValueError(f"Invalid integer value: {int_str}")

    def _parse_float_str(self, float_str: str, allow_empty: bool = False) -> float | None:
        """Parse float string to float."""
        if not float_str and allow_empty:
            return None
        try:
            return float(float_str)
        except ValueError:
            raise ValueError(f"Invalid float value: {float_str}")

    def _parse_enum_str(self, enum_str: str, enum_class) -> str:
        """Validate and return enum string value."""
        valid_values = [e.value for e in enum_class]
        if enum_str not in valid_values:
            raise ValueError(f"Invalid enum value: {enum_str}. Valid values: {', '.join(valid_values)}")
        return enum_str

    def _backup_database(self, backup_path: Path) -> None:
        """Create backup of database before import."""
        import shutil
        shutil.copy2(self.db_path, backup_path)

    def preview_import(self, input_path: Path) -> tuple[dict, ImportResult]:
        """
        Preview import without modifying database.
        Returns (parsed_data, ImportResult) for review.
        """
        try:
            parsed_data = self.parse_sectioned_csv(input_path)
            validation_errors = self.validate_csv_data(parsed_data)
            
            total_rows = sum(len(rows) for rows in parsed_data.values())
            entity_stats = {}
            for section_name, rows in parsed_data.items():
                entity_stats[section_name] = len(rows)
            
            critical_errors = [e for e in validation_errors if e.severity == 'error']
            
            result = ImportResult(
                success=len(critical_errors) == 0,
                total_rows=total_rows,
                imported=0,
                skipped=0,
                overwritten=0,
                errors=[e.message for e in validation_errors if e.severity == 'error'],
                warnings=[e.message for e in validation_errors if e.severity == 'warning'],
                entity_stats=entity_stats
            )
            
            return (parsed_data, result)
            
        except Exception as e:
            result = ImportResult(
                success=False,
                total_rows=0,
                imported=0,
                skipped=0,
                overwritten=0,
                errors=[f"Preview failed: {str(e)}"],
                warnings=[],
                entity_stats={}
            )
            return ({}, result)

    def import_complete_csv(self, input_path: Path, dry_run: bool = False, 
                         duplicate_callback: callable | None = None,
                         progress_callback: callable | None = None) -> ImportResult:
        """
        Import CSV data with validation and duplicate handling.
        
        Args:
            input_path: Path to CSV file
            dry_run: If True, only validate and preview (don't import)
            duplicate_callback: Called when duplicate found, receives (entity_type, existing, imported)
                             Returns: 'skip', 'overwrite', 'rename', 'cancel'
            progress_callback: Called during import for updates
                             Receives: (current, total, entity_type, message)
        
        Returns:
            ImportResult with statistics
        """
        result = ImportResult(
            success=False,
            total_rows=0,
            imported=0,
            skipped=0,
            overwritten=0,
            errors=[],
            warnings=[],
            entity_stats={}
        )
        
        try:
            # Step 1: Create backup before import
            if not dry_run:
                backup_path = self.db_path.parent / f"{self.db_path.name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if progress_callback:
                    progress_callback(0, 100, "BACKUP", f"Creating backup: {backup_path.name}")
                self._backup_database(backup_path)
                result.warnings.append(f"Database backed up to: {backup_path.name}")
            
            # Step 2: Parse and validate CSV
            if progress_callback:
                progress_callback(10, 100, "PARSING", "Parsing CSV file...")
            
            parsed_data = self.parse_sectioned_csv(input_path)
            validation_errors = self.validate_csv_data(parsed_data)
            
            critical_errors = [e for e in validation_errors if e.severity == 'error']
            
            if critical_errors:
                result.errors.extend([e.message for e in critical_errors])
                result.total_rows = sum(len(rows) for rows in parsed_data.values())
                for section_name, rows in parsed_data.items():
                    result.entity_stats[section_name] = len(rows)
                return result
            
            # Step 3: Dry run - return early without importing
            if dry_run:
                if progress_callback:
                    progress_callback(100, 100, "DRY RUN", "Preview complete - no changes made")
                
                result.total_rows = sum(len(rows) for rows in parsed_data.values())
                result.errors = [e.message for e in validation_errors if e.severity == 'error']
                result.warnings = [e.message for e in validation_errors if e.severity == 'warning']
                for section_name, rows in parsed_data.items():
                    result.entity_stats[section_name] = len(rows)
                result.success = True
                return result
            
            # Step 4: Actual import
            if progress_callback:
                progress_callback(20, 100, "PREPARING", "Preparing import...")
            
            import_order = self.get_entity_import_order()
            total_entities = len(import_order)
            
            # Track imported items for foreign key resolution
            imported_borrowers = {}
            imported_firearms = {}
            imported_nfa_items = {}
            imported_soft_gear = {}
            imported_attachments = {}
            imported_consumables = {}
            imported_reload_batches = {}
            imported_loadouts = {}
            
            # Process each entity type
            for entity_idx, entity_type in enumerate(import_order):
                if entity_type not in parsed_data:
                    continue
                
                rows = parsed_data[entity_type]
                if not rows:
                    result.entity_stats[entity_type] = 0
                    continue
                
                entity_result = self._import_entity_type(
                    entity_type=entity_type,
                    rows=rows,
                    duplicate_callback=duplicate_callback,
                    progress_callback=progress_callback,
                    current_progress=20 + (entity_idx * 60 // total_entities),
                    imported_borrowers=imported_borrowers,
                    imported_firearms=imported_firearms,
                    imported_nfa_items=imported_nfa_items,
                    imported_soft_gear=imported_soft_gear,
                    imported_attachments=imported_attachments,
                    imported_consumables=imported_consumables,
                    imported_reload_batches=imported_reload_batches,
                    imported_loadouts=imported_loadouts
                )
                
                result.imported += entity_result['imported']
                result.skipped += entity_result['skipped']
                result.overwritten += entity_result['overwritten']
                result.errors.extend(entity_result['errors'])
                result.warnings.extend(entity_result['warnings'])
                result.entity_stats[entity_type] = entity_result['total']
            
            result.total_rows = sum(len(rows) for rows in parsed_data.values())
            result.success = len(result.errors) == 0 or result.imported > 0
            
            if progress_callback:
                progress_callback(100, 100, "COMPLETE", "Import complete")
            
            return result
            
        except Exception as e:
            result.errors.append(f"Import failed: {str(e)}")
            result.success = False
            return result

    def _import_entity_type(self, entity_type: str, rows: list[dict],
                           duplicate_callback: callable, progress_callback: callable,
                           current_progress: int,
                           imported_borrowers: dict, imported_firearms: dict,
                           imported_nfa_items: dict, imported_soft_gear: dict,
                           imported_attachments: dict, imported_consumables: dict,
                           imported_reload_batches: dict, imported_loadouts: dict) -> dict:
        """
        Import a single entity type with transaction handling.
        
        Returns dict with:
            {'imported': int, 'skipped': int, 'overwritten': int,
             'errors': list, 'warnings': list, 'total': int}
        """
        result = {
            'imported': 0,
            'skipped': 0,
            'overwritten': 0,
            'errors': [],
            'warnings': [],
            'total': len(rows)
        }
        
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for row_idx, row in enumerate(rows):
                try:
                    # Duplicate check
                    existing = self._check_entity_duplicate(entity_type, row)
                    
                    if existing:
                        action = 'skip'
                        if duplicate_callback:
                            action = duplicate_callback(entity_type, existing, row)
                        
                        if action == 'cancel':
                            raise Exception("Import cancelled by user")
                        elif action == 'skip':
                            result['skipped'] += 1
                            continue
                        elif action == 'overwrite':
                            self._update_entity(entity_type, existing, row, cursor)
                            result['overwritten'] += 1
                        elif action == 'rename':
                            self._create_entity(entity_type, row, cursor, rename=True)
                            result['imported'] += 1
                    else:
                        # No duplicate - import new
                        self._create_entity(entity_type, row, cursor)
                        result['imported'] += 1
                    
                    # Track imported items for foreign key resolution
                    self._track_imported_item(entity_type, row, cursor,
                                          imported_borrowers, imported_firearms,
                                          imported_nfa_items, imported_soft_gear,
                                          imported_attachments, imported_consumables,
                                          imported_reload_batches, imported_loadouts)
                    
                    if progress_callback:
                        pct = current_progress + ((row_idx + 1) * 40 // len(rows))
                        progress_callback(pct, 100, entity_type.upper(), 
                                       f"Importing {entity_type} {row_idx + 1}/{len(rows)}")
                
                except ValueError as e:
                    result['errors'].append(str(e))
                    result['skipped'] += 1
                except Exception as e:
                    result['errors'].append(f"Row {row_idx + 1}: {str(e)}")
                    result['skipped'] += 1
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            result['errors'].append(f"Entity type {entity_type} failed: {str(e)}")
        
        return result

    def _check_entity_duplicate(self, entity_type: str, row: dict) -> object | None:
        """Check if entity already exists."""
        entity_type = entity_type.upper().replace(' ', '_')
        
        if entity_type == 'FIREARMS':
            serial = row.get('serial_number', '')
            if serial:
                return self.detect_duplicate_firearm(serial)
        elif entity_type == 'NFA_ITEMS':
            name = row.get('name', '')
            if name:
                return self.detect_duplicate_nfa_item(name)
        elif entity_type == 'SOFT_GEAR':
            name = row.get('name', '')
            if name:
                return self.detect_duplicate_soft_gear(name)
        elif entity_type == 'ATTACHMENTS':
            name = row.get('name', '')
            if name:
                return self.detect_duplicate_attachment(name)
        elif entity_type == 'CONSUMABLES':
            name = row.get('name', '')
            if name:
                return self.detect_duplicate_consumable(name)
        elif entity_type == 'RELOAD_BATCHES':
            cartridge = row.get('cartridge', '')
            bullet_model = row.get('bullet_model', '')
            if cartridge and bullet_model:
                return self.detect_duplicate_reload_batch(cartridge, bullet_model)
        elif entity_type == 'BORROWERS':
            name = row.get('name', '')
            email = row.get('email', '')
            if name:
                return self.detect_duplicate_borrower(name, email)
        elif entity_type == 'LOADOUTS':
            name = row.get('name', '')
            if name:
                return self.detect_duplicate_loadout(name)
        
        return None

    def _create_entity(self, entity_type: str, row: dict, cursor, rename: bool = False) -> str:
        """Create entity from CSV row, returns entity ID."""
        entity_type_upper = entity_type.upper().replace(' ', '_')
        entity_id = row.get('id', str(uuid.uuid4()))
        
        if rename:
            entity_id = str(uuid.uuid4())
        
        if entity_type_upper == 'FIREARMS':
            self._create_firearm(row, cursor, entity_id)
        elif entity_type_upper == 'NFA_ITEMS':
            self._create_nfa_item(row, cursor, entity_id)
        elif entity_type_upper == 'SOFT_GEAR':
            self._create_soft_gear(row, cursor, entity_id)
        elif entity_type_upper == 'ATTACHMENTS':
            self._create_attachment(row, cursor, entity_id)
        elif entity_type_upper == 'CONSUMABLES':
            self._create_consumable(row, cursor, entity_id)
        elif entity_type_upper == 'RELOAD_BATCHES':
            self._create_reload_batch(row, cursor, entity_id)
        elif entity_type_upper == 'BORROWERS':
            self._create_borrower(row, cursor, entity_id)
        elif entity_type_upper == 'LOADOUTS':
            self._create_loadout(row, cursor, entity_id)
        elif entity_type_upper == 'LOADOUT_ITEMS':
            self._create_loadout_item(row, cursor, entity_id)
        elif entity_type_upper == 'LOADOUT_CONSUMABLES':
            self._create_loadout_consumable(row, cursor, entity_id)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        return entity_id

    def _create_firearm(self, row: dict, cursor, entity_id: str) -> None:
        name = row['name']
        caliber = row['caliber']
        serial_number = row.get('serial_number', '')
        purchase_date = self._parse_date_str(row['purchase_date'])
        notes = row.get('notes', '')
        status = CheckoutStatus(self._parse_enum_str(row.get('status', 'AVAILABLE'), CheckoutStatus))
        is_nfa = self._parse_bool_str(row.get('is_nfa', 'FALSE'))
        nfa_type = None
        if is_nfa:
            nfa_type_str = row.get('nfa_type', '')
            if nfa_type_str:
                nfa_type = NFAFirearmType(self._parse_enum_str(nfa_type_str, NFAFirearmType))
        tax_stamp_id = row.get('tax_stamp_id', '')
        form_type = row.get('form_type', '')
        barrel_length = row.get('barrel_length', '')
        trust_name = row.get('trust_name', '')
        transfer_status = TransferStatus(self._parse_enum_str(row.get('transfer_status', 'OWNED'), TransferStatus))
        rounds_fired = self._parse_int_str(row.get('rounds_fired', '0'))
        clean_interval_rounds = self._parse_int_str(row.get('clean_interval_rounds', '500'))
        oil_interval_days = self._parse_int_str(row.get('oil_interval_days', '90'))
        needs_maintenance = self._parse_bool_str(row.get('needs_maintenance', 'FALSE'))
        maintenance_conditions = row.get('maintenance_conditions', '')
        
        cursor.execute(
            'INSERT INTO firearms VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (entity_id, name, caliber, serial_number,
             int(purchase_date.timestamp()), notes, status.value,
             1 if is_nfa else 0, nfa_type.value if nfa_type else None,
             tax_stamp_id, form_type, barrel_length, trust_name, transfer_status.value,
             rounds_fired, clean_interval_rounds, oil_interval_days,
             1 if needs_maintenance else 0, maintenance_conditions)
        )

    def _create_nfa_item(self, row: dict, cursor, entity_id: str) -> None:
        name = row['name']
        nfa_type = NFAItemType(self._parse_enum_str(row['nfa_type'], NFAItemType))
        manufacturer = row['manufacturer']
        serial_number = row['serial_number']
        tax_stamp_id = row['tax_stamp_id']
        caliber_bore = row['caliber_bore']
        purchase_date = self._parse_date_str(row['purchase_date'])
        form_type = row.get('form_type', '')
        trust_name = row.get('trust_name', '')
        notes = row.get('notes', '')
        status = CheckoutStatus(self._parse_enum_str(row.get('status', 'AVAILABLE'), CheckoutStatus))
        
        cursor.execute(
            'INSERT INTO nfa_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (entity_id, name, nfa_type.value, manufacturer, serial_number,
             tax_stamp_id, caliber_bore, int(purchase_date.timestamp()),
             form_type, trust_name, notes, status.value)
        )

    def _create_soft_gear(self, row: dict, cursor, entity_id: str) -> None:
        name = row['name']
        category = row['category']
        brand = row['brand']
        purchase_date = self._parse_date_str(row['purchase_date'])
        notes = row.get('notes', '')
        status = CheckoutStatus(self._parse_enum_str(row.get('status', 'AVAILABLE'), CheckoutStatus))
        
        cursor.execute(
            'INSERT INTO soft_gear VALUES (?, ?, ?, ?, ?, ?, ?)',
            (entity_id, name, category, brand,
             int(purchase_date.timestamp()), notes, status.value)
        )

    def _create_attachment(self, row: dict, cursor, entity_id: str) -> None:
        name = row['name']
        category = row['category']
        brand = row['brand']
        model = row['model']
        purchase_date = self._parse_date_str(row['purchase_date'], allow_empty=True)
        serial_number = row.get('serial_number', '')
        mounted_on_firearm_id = row.get('mounted_on_firearm_id', '')
        mount_position = row.get('mount_position', '')
        zero_distance_yards = self._parse_int_str(row.get('zero_distance_yards', ''), allow_empty=True)
        zero_notes = row.get('zero_notes', '')
        notes = row.get('notes', '')
        
        cursor.execute(
            'INSERT INTO attachments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (entity_id, name, category, brand, model,
             int(purchase_date.timestamp()) if purchase_date else None,
             serial_number, mounted_on_firearm_id if mounted_on_firearm_id else None,
             mount_position, zero_distance_yards, zero_notes, notes)
        )

    def _create_consumable(self, row: dict, cursor, entity_id: str) -> None:
        name = row['name']
        category = row['category']
        unit = row['unit']
        quantity = self._parse_int_str(row['quantity'])
        min_quantity = self._parse_int_str(row.get('min_quantity', '0'))
        notes = row.get('notes', '')
        
        cursor.execute(
            'INSERT INTO consumables VALUES (?, ?, ?, ?, ?, ?, ?)',
            (entity_id, name, category, unit, quantity, min_quantity, notes)
        )

    def _create_reload_batch(self, row: dict, cursor, entity_id: str) -> None:
        cartridge = row['cartridge']
        firearm_id = row.get('firearm_id', '')
        date_created = self._parse_date_str(row['date_created'])
        bullet_maker = row['bullet_maker']
        bullet_model = row['bullet_model']
        bullet_weight_gr = self._parse_int_str(row.get('bullet_weight_gr', ''), allow_empty=True)
        powder_name = row['powder_name']
        powder_charge_gr = self._parse_float_str(row.get('powder_charge_gr', ''), allow_empty=True)
        powder_lot = row.get('powder_lot', '')
        primer_maker = row.get('primer_maker', '')
        primer_type = row.get('primer_type', '')
        case_brand = row.get('case_brand', '')
        case_times_fired = self._parse_int_str(row.get('case_times_fired', ''), allow_empty=True)
        case_prep_notes = row.get('case_prep_notes', '')
        coal_in = self._parse_float_str(row.get('coal_in', ''), allow_empty=True)
        crimp_style = row.get('crimp_style', '')
        test_date = self._parse_date_str(row.get('test_date', ''), allow_empty=True)
        avg_velocity = self._parse_int_str(row.get('avg_velocity', ''), allow_empty=True)
        es = self._parse_int_str(row.get('es', ''), allow_empty=True)
        sd = self._parse_int_str(row.get('sd', ''), allow_empty=True)
        group_size_inches = self._parse_float_str(row.get('group_size_inches', ''), allow_empty=True)
        group_distance_yards = self._parse_int_str(row.get('group_distance_yards', ''), allow_empty=True)
        notes = row.get('notes', '')
        
        cursor.execute(
            'INSERT INTO reload_batches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (entity_id, cartridge, firearm_id if firearm_id else None,
             int(date_created.timestamp()), bullet_maker, bullet_model, bullet_weight_gr,
             powder_name, powder_charge_gr, powder_lot, primer_maker, primer_type,
             case_brand, case_times_fired, case_prep_notes, coal_in, crimp_style,
             int(test_date.timestamp()) if test_date else None, avg_velocity, es, sd,
             group_size_inches, group_distance_yards, notes)
        )

    def _create_borrower(self, row: dict, cursor, entity_id: str) -> None:
        name = row['name']
        phone = row.get('phone', '')
        email = row.get('email', '')
        notes = row.get('notes', '')
        
        cursor.execute(
            'INSERT INTO borrowers VALUES (?, ?, ?, ?, ?)',
            (entity_id, name, phone, email, notes)
        )

    def _create_loadout(self, row: dict, cursor, entity_id: str) -> None:
        name = row['name']
        description = row.get('description', '')
        created_date = self._parse_date_str(row.get('created_date', ''), allow_empty=True)
        notes = row.get('notes', '')
        
        cursor.execute(
            'INSERT INTO loadouts VALUES (?, ?, ?, ?, ?)',
            (entity_id, name, description,
             int(created_date.timestamp()) if created_date else None, notes)
        )

    def _create_loadout_item(self, row: dict, cursor, entity_id: str) -> None:
        loadout_id = row['loadout_id']
        item_id = row['item_id']
        item_type = GearCategory(self._parse_enum_str(row['item_type'], GearCategory))
        notes = row.get('notes', '')
        
        cursor.execute(
            'INSERT INTO loadout_items VALUES (?, ?, ?, ?, ?)',
            (entity_id, loadout_id, item_id, item_type.value, notes)
        )

    def _create_loadout_consumable(self, row: dict, cursor, entity_id: str) -> None:
        loadout_id = row['loadout_id']
        consumable_id = row['consumable_id']
        quantity = self._parse_int_str(row['quantity'])
        notes = row.get('notes', '')
        
        cursor.execute(
            'INSERT INTO loadout_consumables VALUES (?, ?, ?, ?, ?)',
            (entity_id, loadout_id, consumable_id, quantity, notes)
        )

    def _update_entity(self, entity_type: str, existing: object, row: dict, cursor) -> None:
        """Update existing entity from CSV row."""
        entity_type_upper = entity_type.upper().replace(' ', '_')
        
        if entity_type_upper == 'FIREARMS':
            self._update_firearm(existing, row, cursor)
        elif entity_type_upper == 'NFA_ITEMS':
            self._update_nfa_item(existing, row, cursor)
        elif entity_type_upper == 'SOFT_GEAR':
            self._update_soft_gear(existing, row, cursor)
        elif entity_type_upper == 'ATTACHMENTS':
            self._update_attachment(existing, row, cursor)
        elif entity_type_upper == 'CONSUMABLES':
            self._update_consumable(existing, row, cursor)
        elif entity_type_upper == 'RELOAD_BATCHES':
            self._update_reload_batch(existing, row, cursor)
        elif entity_type_upper == 'BORROWERS':
            self._update_borrower(existing, row, cursor)
        elif entity_type_upper == 'LOADOUTS':
            self._update_loadout(existing, row, cursor)

    def _update_firearm(self, existing: Firearm, row: dict, cursor) -> None:
        updates = []
        values = []
        
        if 'name' in row and row['name']:
            updates.append('name = ?')
            values.append(row['name'])
        if 'caliber' in row and row['caliber']:
            updates.append('caliber = ?')
            values.append(row['caliber'])
        if 'notes' in row:
            updates.append('notes = ?')
            values.append(row.get('notes', ''))
        if 'status' in row and row['status']:
            updates.append('status = ?')
            values.append(self._parse_enum_str(row['status'], CheckoutStatus))
        if 'rounds_fired' in row:
            updates.append('rounds_fired = ?')
            values.append(self._parse_int_str(row.get('rounds_fired', '0')))
        if 'clean_interval_rounds' in row:
            updates.append('clean_interval_rounds = ?')
            values.append(self._parse_int_str(row.get('clean_interval_rounds', '500')))
        if 'oil_interval_days' in row:
            updates.append('oil_interval_days = ?')
            values.append(self._parse_int_str(row.get('oil_interval_days', '90')))
        if 'needs_maintenance' in row:
            updates.append('needs_maintenance = ?')
            values.append(1 if self._parse_bool_str(row.get('needs_maintenance', 'FALSE')) else 0)
        if 'maintenance_conditions' in row:
            updates.append('maintenance_conditions = ?')
            values.append(row.get('maintenance_conditions', ''))
        
        if updates:
            values.append(existing.id)
            sql = 'UPDATE firearms SET ' + ', '.join(updates) + ' WHERE id = ?'
            cursor.execute(sql, values)

    def _update_nfa_item(self, existing: NFAItem, row: dict, cursor) -> None:
        updates = []
        values = []
        
        if 'name' in row and row['name']:
            updates.append('name = ?')
            values.append(row['name'])
        if 'notes' in row:
            updates.append('notes = ?')
            values.append(row.get('notes', ''))
        if 'status' in row and row['status']:
            updates.append('status = ?')
            values.append(self._parse_enum_str(row['status'], CheckoutStatus))
        
        if updates:
            values.append(existing.id)
            sql = 'UPDATE nfa_items SET ' + ', '.join(updates) + ' WHERE id = ?'
            cursor.execute(sql, values)

    def _update_soft_gear(self, existing: SoftGear, row: dict, cursor) -> None:
        updates = []
        values = []
        
        if 'name' in row and row['name']:
            updates.append('name = ?')
            values.append(row['name'])
        if 'notes' in row:
            updates.append('notes = ?')
            values.append(row.get('notes', ''))
        if 'status' in row and row['status']:
            updates.append('status = ?')
            values.append(self._parse_enum_str(row['status'], CheckoutStatus))
        
        if updates:
            values.append(existing.id)
            sql = 'UPDATE soft_gear SET ' + ', '.join(updates) + ' WHERE id = ?'
            cursor.execute(sql, values)

    def _update_attachment(self, existing: Attachment, row: dict, cursor) -> None:
        updates = []
        values = []
        
        if 'name' in row and row['name']:
            updates.append('name = ?')
            values.append(row['name'])
        if 'notes' in row:
            updates.append('notes = ?')
            values.append(row.get('notes', ''))
        
        if updates:
            values.append(existing.id)
            sql = 'UPDATE attachments SET ' + ', '.join(updates) + ' WHERE id = ?'
            cursor.execute(sql, values)

    def _update_consumable(self, existing: Consumable, row: dict, cursor) -> None:
        updates = []
        values = []
        
        if 'name' in row and row['name']:
            updates.append('name = ?')
            values.append(row['name'])
        if 'notes' in row:
            updates.append('notes = ?')
            values.append(row.get('notes', ''))
        if 'quantity' in row:
            updates.append('quantity = ?')
            values.append(self._parse_int_str(row['quantity']))
        if 'min_quantity' in row:
            updates.append('min_quantity = ?')
            values.append(self._parse_int_str(row.get('min_quantity', '0')))
        
        if updates:
            values.append(existing.id)
            sql = 'UPDATE consumables SET ' + ', '.join(updates) + ' WHERE id = ?'
            cursor.execute(sql, values)

    def _update_reload_batch(self, existing: ReloadBatch, row: dict, cursor) -> None:
        updates = []
        values = []
        
        updatable_fields = ['notes', 'test_date', 'avg_velocity', 'es', 'sd', 
                          'group_size_inches', 'group_distance_yards']
        
        for field in updatable_fields:
            if field in row:
                updates.append(f'{field} = ?')
                if field in ['test_date']:
                    values.append(int(self._parse_date_str(row[field]).timestamp()) 
                               if row[field] else None)
                elif field in ['avg_velocity', 'es', 'sd', 'group_distance_yards']:
                    values.append(self._parse_int_str(row.get(field, ''), allow_empty=True))
                elif field in ['group_size_inches']:
                    values.append(self._parse_float_str(row.get(field, ''), allow_empty=True))
                else:
                    values.append(row.get(field, ''))
        
        if updates:
            values.append(existing.id)
            sql = 'UPDATE reload_batches SET ' + ', '.join(updates) + ' WHERE id = ?'
            cursor.execute(sql, values)

    def _update_borrower(self, existing: Borrower, row: dict, cursor) -> None:
        updates = []
        values = []
        
        if 'name' in row and row['name']:
            updates.append('name = ?')
            values.append(row['name'])
        if 'phone' in row:
            updates.append('phone = ?')
            values.append(row.get('phone', ''))
        if 'email' in row:
            updates.append('email = ?')
            values.append(row.get('email', ''))
        if 'notes' in row:
            updates.append('notes = ?')
            values.append(row.get('notes', ''))
        
        if updates:
            values.append(existing.id)
            sql = 'UPDATE borrowers SET ' + ', '.join(updates) + ' WHERE id = ?'
            cursor.execute(sql, values)

    def _update_loadout(self, existing: Loadout, row: dict, cursor) -> None:
        updates = []
        values = []
        
        if 'name' in row and row['name']:
            updates.append('name = ?')
            values.append(row['name'])
        if 'description' in row:
            updates.append('description = ?')
            values.append(row.get('description', ''))
        if 'notes' in row:
            updates.append('notes = ?')
            values.append(row.get('notes', ''))
        
        if updates:
            values.append(existing.id)
            sql = 'UPDATE loadouts SET ' + ', '.join(updates) + ' WHERE id = ?'
            cursor.execute(sql, values)

    def _track_imported_item(self, entity_type: str, row: dict, cursor,
                             imported_borrowers: dict, imported_firearms: dict,
                             imported_nfa_items: dict, imported_soft_gear: dict,
                             imported_attachments: dict, imported_consumables: dict,
                             imported_reload_batches: dict, imported_loadouts: dict) -> None:
        """Track imported items for foreign key resolution."""
        entity_type_upper = entity_type.upper().replace(' ', '_')
        entity_id = row.get('id', '')
        
        if entity_type_upper == 'BORROWERS' and entity_id:
            name = row.get('name', '')
            imported_borrowers[name] = entity_id
        elif entity_type_upper == 'FIREARMS' and entity_id:
            serial = row.get('serial_number', '')
            imported_firearms[serial] = entity_id
        elif entity_type_upper == 'NFA_ITEMS' and entity_id:
            name = row.get('name', '')
            imported_nfa_items[name] = entity_id
        elif entity_type_upper == 'SOFT_GEAR' and entity_id:
            name = row.get('name', '')
            imported_soft_gear[name] = entity_id
        elif entity_type_upper == 'ATTACHMENTS' and entity_id:
            name = row.get('name', '')
            imported_attachments[name] = entity_id
        elif entity_type_upper == 'CONSUMABLES' and entity_id:
            name = row.get('name', '')
            imported_consumables[name] = entity_id
        elif entity_type_upper == 'RELOAD_BATCHES' and entity_id:
            cartridge = row.get('cartridge', '')
            imported_reload_batches[cartridge] = entity_id
        elif entity_type_upper == 'LOADOUTS' and entity_id:
            name = row.get('name', '')
            imported_loadouts[name] = entity_id

    def _create_checkout(self, row: dict, cursor, entity_id: str) -> None:
        item_id = row['item_id']
        item_type = GearCategory(self._parse_enum_str(row['item_type'], GearCategory))
        borrower_name = row['borrower_name']
        checkout_date = self._parse_date_str(row['checkout_date'])
        expected_return = self._parse_date_str(row.get('expected_return', ''), allow_empty=True)
        actual_return = self._parse_date_str(row.get('actual_return', ''), allow_empty=True)
        notes = row.get('notes', '')
        
        # Find borrower ID
        cursor.execute('SELECT id FROM borrowers WHERE name = ?', (borrower_name,))
        borrower_result = cursor.fetchone()
        if not borrower_result:
            raise ValueError(f"Borrower not found: {borrower_name}")
        borrower_id = borrower_result[0]
        
        cursor.execute(
            'INSERT INTO checkouts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (entity_id, item_id, item_type.value, borrower_id,
             int(checkout_date.timestamp()),
             int(expected_return.timestamp()) if expected_return else None,
             int(actual_return.timestamp()) if actual_return else None, notes)
        )

    def _create_maintenance_log(self, row: dict, cursor, entity_id: str) -> None:
        item_id = row['item_id']
        item_type = GearCategory(self._parse_enum_str(row['item_type'], GearCategory))
        log_type = MaintenanceType(self._parse_enum_str(row['log_type'], MaintenanceType))
        date = self._parse_date_str(row['date'])
        details = row.get('details', '')
        ammo_count = self._parse_int_str(row.get('ammo_count', ''), allow_empty=True)
        photo_path = row.get('photo_path', '')
        
        cursor.execute(
            'INSERT INTO maintenance_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (entity_id, item_id, item_type.value, log_type.value,
             int(date.timestamp()), details, ammo_count, photo_path)
        )

    def _create_transfer(self, row: dict, cursor, entity_id: str) -> None:
        firearm_id = row['firearm_id']
        transfer_date = self._parse_date_str(row['transfer_date'])
        buyer_name = row['buyer_name']
        buyer_address = row['buyer_address']
        buyer_dl_number = row['buyer_dl_number']
        buyer_ltc_number = row.get('buyer_ltc_number', '')
        sale_price = self._parse_float_str(row.get('sale_price', '0.0'))
        ffl_dealer = row.get('ffl_dealer', '')
        ffl_license = row.get('ffl_license', '')
        notes = row.get('notes', '')
        
        cursor.execute(
            'INSERT INTO transfers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (entity_id, firearm_id, int(transfer_date.timestamp()),
             buyer_name, buyer_address, buyer_dl_number, buyer_ltc_number,
             sale_price, ffl_dealer, ffl_license, notes)
        )

    def _create_consumable_transaction(self, row: dict, cursor, entity_id: str) -> None:
        consumable_id = row['consumable_id']
        transaction_type = row['transaction_type']
        quantity = self._parse_int_str(row['quantity'])
        date = self._parse_date_str(row['date'])
        notes = row.get('notes', '')
        
        cursor.execute(
            'INSERT INTO consumable_transactions VALUES (?, ?, ?, ?, ?, ?)',
            (entity_id, consumable_id, transaction_type, quantity, int(date.timestamp()), notes)
        )
