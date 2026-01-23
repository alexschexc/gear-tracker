from datetime import datetime
from src.models import (
    Checkout,
    Borrower,
    MaintenanceLog,
    MaintenanceType,
    GearCategory,
)


class CheckoutRepository:
    def __init__(self, db):
        self.db = db

    def add_borrower(self, borrower: Borrower) -> None:
        conn = self.db.connect()
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
        conn = self.db.connect()
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
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM checkouts WHERE borrower_id = ? AND actual_return IS NULL",
            (borrower_id,),
        )
        count = cursor.fetchone()[0]
        conn.close()

        if count > 0:
            raise ValueError("Cannot delete borrower with active checkouts")

        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM checkouts WHERE borrower_id = ?", (borrower_id,))
        cursor.execute("DELETE FROM borrowers WHERE id = ?", (borrower_id,))
        conn.commit()
        conn.close()

    def get_borrower_by_name(self, name: str) -> Borrower | None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM borrowers WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Borrower(
            id=row[0],
            name=row[1],
            phone=row[2] or "",
            email=row[3] or "",
            notes=row[4] or "",
        )

    def add_checkout(self, checkout: Checkout) -> str:
        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM borrowers WHERE name = ?", (checkout.borrower_name,)
        )
        borrower_result = cursor.fetchone()
        if not borrower_result:
            conn.close()
            raise ValueError(f"Borrower not found: {checkout.borrower_name}")

        borrower_id = borrower_result[0]

        cursor.execute(
            "INSERT INTO checkouts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                checkout.id,
                checkout.item_id,
                checkout.item_type,
                borrower_id,
                int(checkout.checkout_date.timestamp()),
                int(checkout.expected_return.timestamp())
                if checkout.expected_return
                else None,
                None,
                checkout.notes,
            ),
        )

        conn.commit()
        conn.close()
        return checkout.id

    def get_active_checkouts(self) -> list[Checkout]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*, b.name as borrower_name
            FROM checkouts c
            JOIN borrowers b ON c.borrower_id = b.id
            WHERE c.actual_return IS NULL
            ORDER BY c.checkout_date DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            Checkout(
                id=row[0],
                item_id=row[1],
                item_type=row[2],
                borrower_name=row[8],
                checkout_date=datetime.fromtimestamp(row[4]),
                expected_return=datetime.fromtimestamp(row[5]) if row[5] else None,
                actual_return=None,
                notes=row[7] or "",
            )
            for row in rows
        ]

    def get_checkout_history(self) -> list[Checkout]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*, b.name as borrower_name
            FROM checkouts c
            JOIN borrowers b ON c.borrower_id = b.id
            WHERE c.actual_return IS NOT NULL
            ORDER BY c.actual_return DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            Checkout(
                id=row[0],
                item_id=row[1],
                item_type=row[2],
                borrower_name=row[8],
                checkout_date=datetime.fromtimestamp(row[4]),
                expected_return=datetime.fromtimestamp(row[5]) if row[5] else None,
                actual_return=datetime.fromtimestamp(row[6]) if row[6] else None,
                notes=row[7] or "",
            )
            for row in rows
        ]

    def return_item(self, checkout_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE checkouts SET actual_return = ? WHERE id = ?",
            (int(datetime.now().timestamp()), checkout_id),
        )
        conn.commit()
        conn.close()

    def get_checkout_by_item(self, item_id: str) -> Checkout | None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*, b.name as borrower_name
            FROM checkouts c
            JOIN borrowers b ON c.borrower_id = b.id
            WHERE c.item_id = ? AND c.actual_return IS NULL
            """,
            (item_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Checkout(
            id=row[0],
            item_id=row[1],
            item_type=row[2],
            borrower_name=row[8],
            checkout_date=datetime.fromtimestamp(row[4]),
            expected_return=datetime.fromtimestamp(row[5]) if row[5] else None,
            actual_return=None,
            notes=row[7] or "",
        )


class MaintenanceRepository:
    def __init__(self, db):
        self.db = db

    def add_log(self, log: MaintenanceLog) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO maintenance_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                log.id,
                log.item_id,
                log.item_type.value
                if hasattr(log.item_type, "value")
                else log.item_type,
                log.log_type.value if hasattr(log.log_type, "value") else log.log_type,
                int(log.date.timestamp()),
                log.details,
                log.ammo_count,
                log.photo_path,
            ),
        )
        conn.commit()
        conn.close()

    def get_logs_for_item(self, item_id: str) -> list[MaintenanceLog]:
        conn = self.db.connect()
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
                details=row[5] or "",
                ammo_count=row[6],
                photo_path=row[7],
            )
            for row in rows
        ]

    def get_last_cleaning_date(self, item_id: str):
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT MAX(date) FROM maintenance_logs
            WHERE item_id = ? AND log_type = ?
            """,
            (item_id, MaintenanceType.CLEANING.value),
        )
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            return datetime.fromtimestamp(result[0])
        return None

    def get_logs_by_type(
        self, item_id: str, log_type: MaintenanceType
    ) -> list[MaintenanceLog]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM maintenance_logs WHERE item_id = ? AND log_type = ? ORDER BY date DESC",
            (item_id, log_type.value),
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
                details=row[5] or "",
                ammo_count=row[6],
                photo_path=row[7],
            )
            for row in rows
        ]
