from pathlib import Path
from datetime import datetime
import sqlite3


class Database:
    def __init__(self, db_path: Path = Path.home() / ".gear_tracker" / "tracker.db"):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.migrate_if_needed()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def close(self, conn):
        conn.close()

    def _init_db(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS firearms (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                caliber TEXT NOT NULL,
                serial_number TEXT UNIQUE,
                purchase_date INTEGER NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'AVAILABLE',
                is_nfa INTEGER DEFAULT 0,
                nfa_type TEXT,
                tax_stamp_id TEXT DEFAULT '',
                form_type TEXT DEFAULT '',
                barrel_length TEXT DEFAULT '',
                trust_name TEXT DEFAULT '',
                transfer_status TEXT DEFAULT 'OWNED',
                rounds_fired INTEGER DEFAULT 0,
                clean_interval_rounds INTEGER DEFAULT 500,
                oil_interval_days INTEGER DEFAULT 90,
                needs_maintenance INTEGER DEFAULT 0,
                maintenance_conditions TEXT DEFAULT ''
            )
        """)

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

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS borrowers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                notes TEXT
            )
        """)

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

        conn.commit()
        conn.close()

    def migrate_if_needed(self):
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(attachments)")
        attachments_columns = {row[1] for row in cursor.fetchall()}

        if "mount_postion" in attachments_columns:
            cursor.execute(
                "ALTER TABLE attachments RENAME COLUMN mount_postion TO mount_position"
            )

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
            "attachments": [
                ("mount_position", "TEXT", ""),
                ("zero_distance_yards", "INTEGER", None),
                ("zero_notes", "TEXT", ""),
            ],
        }

        for table_name, columns_to_add in desired_schema.items():
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}

            for col_name, col_type, default_value in columns_to_add:
                if col_name not in existing_columns:
                    if default_value is not None:
                        cursor.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} DEFAULT '{default_value}'"
                        )
                    else:
                        cursor.execute(
                            f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                        )

        conn.commit()
        conn.close()
