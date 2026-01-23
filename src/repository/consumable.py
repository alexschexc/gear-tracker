from datetime import datetime
from src.models import Consumable, ConsumableTransaction


class ConsumableRepository:
    def __init__(self, db):
        self.db = db

    def add(self, consumable: Consumable) -> None:
        conn = self.db.connect()
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

    def get_all(self) -> list[Consumable]:
        conn = self.db.connect()
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

    def update_quantity(
        self,
        consumable_id: str,
        delta: int,
        transaction_type: str,
        notes: str = "",
    ) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT quantity FROM consumables WHERE id = ?", (consumable_id,)
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            return

        new_quantity = result[0] + delta

        cursor.execute(
            "UPDATE consumables SET quantity = ? WHERE id = ?",
            (new_quantity, consumable_id),
        )

        transaction = ConsumableTransaction(
            id=str(uuid.uuid4()),
            consumable_id=consumable_id,
            transaction_type=transaction_type,
            quantity=delta,
            date=datetime.now(),
            notes=notes,
        )

        cursor.execute(
            "INSERT INTO consumable_transactions VALUES (?, ?, ?, ?, ?, ?)",
            (
                transaction.id,
                transaction.consumable_id,
                transaction.transaction_type,
                transaction.quantity,
                int(transaction.date.timestamp()),
                transaction.notes,
            ),
        )

        conn.commit()
        conn.close()

    def get_history(self, consumable_id: str) -> list[ConsumableTransaction]:
        conn = self.db.connect()
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

    def delete(self, consumable_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM consumable_transactions WHERE consumable_id = ?",
            (consumable_id,),
        )
        cursor.execute("DELETE FROM consumables WHERE id = ?", (consumable_id,))
        conn.commit()
        conn.close()

    def get_low_stock(self) -> list[Consumable]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM consumables WHERE quantity <= min_quantity ORDER BY name"
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


import uuid
