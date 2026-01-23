from datetime import datetime
from src.models import (
    Loadout,
    LoadoutItem,
    LoadoutConsumable,
    LoadoutCheckout,
    GearCategory,
)


class LoadoutRepository:
    def __init__(self, db):
        self.db = db

    def create(self, loadout: Loadout) -> None:
        conn = self.db.connect()
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

    def get_all(self) -> list[Loadout]:
        conn = self.db.connect()
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

    def get_by_id(self, loadout_id: str) -> Loadout | None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loadouts WHERE id = ?", (loadout_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Loadout(
            id=row[0],
            name=row[1],
            description=row[2] or "",
            created_date=datetime.fromtimestamp(row[3]) if row[3] else None,
            notes=row[4] or "",
        )

    def update(self, loadout: Loadout) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE loadouts SET name = ?, description = ?, notes = ? WHERE id = ?",
            (loadout.name, loadout.description, loadout.notes, loadout.id),
        )
        conn.commit()
        conn.close()

    def delete(self, loadout_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM loadout_consumables WHERE loadout_id = ?", (loadout_id,)
        )
        cursor.execute("DELETE FROM loadout_items WHERE loadout_id = ?", (loadout_id,))
        cursor.execute(
            "DELETE FROM loadout_checkouts WHERE loadout_id = ?", (loadout_id,)
        )
        cursor.execute("DELETE FROM loadouts WHERE id = ?", (loadout_id,))
        conn.commit()
        conn.close()

    def add_item(self, item: LoadoutItem) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO loadout_items VALUES (?, ?, ?, ?, ?)",
            (
                item.id,
                item.loadout_id,
                item.item_id,
                item.item_type,
                item.notes,
            ),
        )
        conn.commit()
        conn.close()

    def get_items(self, loadout_id: str) -> list[LoadoutItem]:
        conn = self.db.connect()
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
                item_type=row[3],
                notes=row[4] or "",
            )
            for row in rows
        ]

    def delete_items(self, loadout_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM loadout_items WHERE loadout_id = ?", (loadout_id,))
        conn.commit()
        conn.close()

    def remove_item(self, item_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM loadout_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    def update_item(self, item: LoadoutItem) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE loadout_items SET item_id = ?, item_type = ?, notes = ? WHERE id = ?",
            (item.item_id, item.item_type, item.notes, item.id),
        )
        conn.commit()
        conn.close()

    def add_consumable(self, cons: LoadoutConsumable) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO loadout_consumables VALUES (?, ?, ?, ?, ?)",
            (cons.id, cons.loadout_id, cons.consumable_id, cons.quantity, cons.notes),
        )
        conn.commit()
        conn.close()

    def get_consumables(self, loadout_id: str) -> list[LoadoutConsumable]:
        conn = self.db.connect()
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

    def delete_consumables(self, loadout_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM loadout_consumables WHERE loadout_id = ?", (loadout_id,)
        )
        conn.commit()
        conn.close()

    def remove_consumable(self, consumable_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM loadout_consumables WHERE id = ?", (consumable_id,))
        conn.commit()
        conn.close()

    def update_consumable_quantity(self, consumable_id: str, quantity: int) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE loadout_consumables SET quantity = ? WHERE id = ?",
            (quantity, consumable_id),
        )
        conn.commit()
        conn.close()

    def checkout(self, checkout: LoadoutCheckout) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO loadout_checkouts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                checkout.id,
                checkout.loadout_id,
                checkout.checkout_id,
                None,
                checkout.rounds_fired,
                1 if checkout.rain_exposure else 0,
                checkout.ammo_type,
                checkout.notes,
            ),
        )
        conn.commit()
        conn.close()

    def get_checkouts(self, loadout_id: str) -> list[LoadoutCheckout]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM loadout_checkouts WHERE loadout_id = ?", (loadout_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            LoadoutCheckout(
                id=row[0],
                loadout_id=row[1],
                checkout_id=row[2],
                return_date=datetime.fromtimestamp(row[3]) if row[3] else None,
                rounds_fired=row[4],
                rain_exposure=bool(row[5]),
                ammo_type=row[6] or "",
                notes=row[7] or "",
            )
            for row in rows
        ]

    def return_items(self, loadout_id: str, checkout_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE loadout_checkouts SET return_date = ? WHERE loadout_id = ? AND checkout_id = ?",
            (int(datetime.now().timestamp()), loadout_id, checkout_id),
        )
        conn.commit()
        conn.close()

    def get_active_checkout(self, loadout_id: str) -> LoadoutCheckout | None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM loadout_checkouts WHERE loadout_id = ? AND return_date IS NULL",
            (loadout_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return LoadoutCheckout(
            id=row[0],
            loadout_id=row[1],
            checkout_id=row[2],
            return_date=None,
            rounds_fired=row[4],
            rain_exposure=bool(row[5]),
            ammo_type=row[6] or "",
            notes=row[7] or "",
        )

    def get_loadout_checkout(self, checkout_id: str) -> LoadoutCheckout | None:
        conn = self.db.connect()
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

    def checkout_loadout(
        self,
        loadout_id: str,
        borrower_id: str,
        expected_return: datetime | None,
    ) -> tuple[str, list[str]]:
        import uuid

        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM borrowers WHERE id = ?", (borrower_id,))
        borrower_result = cursor.fetchone()
        if not borrower_result:
            conn.close()
            return ("", ["Borrower not found"])

        borrower_name = borrower_result[0]

        loadout_items = self.get_items(loadout_id)
        loadout_consumables = self.get_consumables(loadout_id)

        checkout_ids = []

        for item in loadout_items:
            checkout_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO checkouts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    checkout_id,
                    item.item_id,
                    item.item_type,
                    borrower_id,
                    int(datetime.now().timestamp()),
                    int(expected_return.timestamp()) if expected_return else None,
                    None,
                    "",
                ),
            )
            checkout_ids.append(checkout_id)

        main_checkout_id = checkout_ids[0] if checkout_ids else ""

        loadout_checkout_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO loadout_checkouts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                loadout_checkout_id,
                loadout_id,
                main_checkout_id,
                None,
                0,
                0,
                "",
                "",
            ),
        )

        for lc in loadout_consumables:
            cursor.execute(
                "UPDATE consumables SET quantity = quantity - ? WHERE id = ?",
                (lc.quantity, lc.consumable_id),
            )

        conn.commit()
        conn.close()

        return (main_checkout_id, [])

    def return_from_trip(
        self,
        loadout_id: str,
        checkout_id: str,
        rounds_fired_dict: dict,
        rain_exposure: bool,
        ammo_type: str,
        notes: str,
        consumable_restock_list: list[tuple[str, int]],
    ) -> None:
        import uuid as uuid_lib
        from datetime import datetime

        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE loadout_checkouts SET return_date = ?, rounds_fired = ?, rain_exposure = ?, ammo_type = ?, notes = ? WHERE loadout_id = ? AND checkout_id = ?",
            (
                int(datetime.now().timestamp()),
                sum(rounds_fired_dict.values()) if rounds_fired_dict else 0,
                1 if rain_exposure else 0,
                ammo_type,
                notes,
                loadout_id,
                checkout_id,
            ),
        )

        conn.commit()
        conn.close()

    def update_firearm_rounds(self, firearm_id: str, rounds: int) -> None:
        from src.repository.firearm import FirearmRepository

        fr = FirearmRepository(self.db)
        fr.update_rounds(firearm_id, rounds)

    def log_maintenance(self, log) -> None:
        from src.repository.checkout import MaintenanceRepository

        mr = MaintenanceRepository(self.db)
        mr.add_log(log)

    def restock_consumable(self, consumable_id: str, quantity: int) -> None:
        from src.repository.consumable import ConsumableRepository

        cr = ConsumableRepository(self.db)
        cr.update_quantity(consumable_id, quantity, "RESTOCK", "Loadout return restock")

    def return_item(self, checkout_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE checkouts SET actual_return = ? WHERE id = ?",
            (int(datetime.now().timestamp()), checkout_id),
        )
        conn.commit()
        conn.close()
