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
    mount_postion: str = ""  # top rail, scout mount, etc.
    zero_distance_yards: int | None = None
    zero_notes: str = ""
    notes: str = ""


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
                mount_postion TEXT,
                zero_distance_yards INTEGER,
                zero_notes TEXT,
                notes TEXT,
                FOREIGN KEY(mounted_on_firearm_id) REFERENCES firearms(id)
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
            "INSERT INTO firearms VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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

    def update_firearm(self, firearm_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # delete releated logs
        cursor.execute("DELETE FROM maintenance_logs WHERE item_id = ?", (firearm_id,))
        # delete checkouts
        cursor.execute("DELETE FROM checkouts WHERE item_id = ?", (firearm_id,))
        # delete the firearm
        cursor.execute("DELETE FROM firearms WHERE id = ?", (firearm_id,))
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
                attachment.mount_postion,
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
                mount_postion=row[8] or "",
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
                mount_postion=row[8] or "",
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
        SET name = ?, category = ?, brand = ?, model = ?, serial_number = ?, purchase_date = ?, mounted_on_firearm_id = ?, mount_postion = ?, zero_distance_yards = ?, zero_notes = ?, notes = ?
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
                attachment.mount_postion,
                attachment.zero_distance_yards,
                attachment.zero_notes,
                attachment.notes,
                attachment.id,
            ),
        )
        conn.commit()
        conn.close()

    def update_attachment(self, attachment_id: str) -> None:
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
                    "SELECT name FROM nfa_items where id = ?", (checkout.item_id)
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
                    notes=row[7] or "",
                ),
                row[8],
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
