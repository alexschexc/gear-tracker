from datetime import datetime
from src.models import SoftGear, NFAItem, NFAItemType, Attachment, CheckoutStatus


class GearRepository:
    def __init__(self, db):
        self.db = db

    def add_soft_gear(self, gear: SoftGear) -> None:
        conn = self.db.connect()
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
                gear.status.value
                if isinstance(gear.status, CheckoutStatus)
                else gear.status,
            ),
        )
        conn.commit()
        conn.close()

    def get_all_soft_gear(self) -> list[SoftGear]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM soft_gear ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        return [
            SoftGear(
                id=row[0],
                name=row[1],
                category=row[2],
                brand=row[3] or "",
                purchase_date=datetime.fromtimestamp(row[4]),
                notes=row[5] or "",
                status=CheckoutStatus(row[6]).value if row[6] else "AVAILABLE",
            )
            for row in rows
        ]

    def delete_soft_gear(self, gear_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM maintenance_logs WHERE item_id = ?", (gear_id,))
        cursor.execute("DELETE FROM checkouts WHERE item_id = ?", (gear_id,))
        cursor.execute("DELETE FROM soft_gear WHERE id = ?", (gear_id,))
        conn.commit()
        conn.close()

    def update_soft_gear_status(self, gear_id: str, status: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE soft_gear SET status = ? WHERE id = ?", (status, gear_id)
        )
        conn.commit()
        conn.close()

    def update_soft_gear(self, gear: SoftGear) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE soft_gear SET name = ?, category = ?, brand = ?, purchase_date = ?, notes = ?, status = ? WHERE id = ?",
            (
                gear.name,
                gear.category,
                gear.brand,
                int(gear.purchase_date.timestamp()),
                gear.notes,
                gear.status,
                gear.id,
            ),
        )
        conn.commit()
        conn.close()

    def add_nfa_item(self, item: NFAItem) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO nfa_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item.id,
                item.name,
                item.nfa_type.value
                if isinstance(item.nfa_type, NFAItemType)
                else item.nfa_type,
                item.manufacturer,
                item.serial_number,
                item.tax_stamp_id,
                item.caliber_bore,
                int(item.purchase_date.timestamp()),
                item.form_type,
                item.trust_name,
                item.notes,
                item.status.value
                if isinstance(item.status, CheckoutStatus)
                else item.status,
            ),
        )
        conn.commit()
        conn.close()

    def get_all_nfa_items(self) -> list[NFAItem]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM nfa_items ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        return [
            NFAItem(
                id=row[0],
                name=row[1],
                nfa_type=NFAItemType(row[2]) if row[2] else NFAItemType.SUPPRESSOR,
                manufacturer=row[3] or "",
                serial_number=row[4] or "",
                tax_stamp_id=row[5],
                caliber_bore=row[6] or "",
                purchase_date=datetime.fromtimestamp(row[7]),
                form_type=row[8] or "",
                trust_name=row[9] or "",
                notes=row[10] or "",
                status=CheckoutStatus(row[11]).value if row[11] else "AVAILABLE",
            )
            for row in rows
        ]

    def delete_nfa_item(self, item_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM maintenance_logs WHERE item_id = ?", (item_id,))
        cursor.execute("DELETE FROM checkouts WHERE item_id = ?", (item_id,))
        cursor.execute("DELETE FROM nfa_items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    def add_maintenance_log(self, log) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO maintenance_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                log.id,
                log.item_id,
                log.item_type,
                log.log_type,
                int(log.date.timestamp()) if log.date else None,
                log.details,
                log.ammo_count,
                log.photo_path,
            ),
        )
        conn.commit()
        conn.close()

    def get_maintenance_logs(self, item_id: str) -> list:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM maintenance_logs WHERE item_id = ? ORDER BY date DESC",
            (item_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        from dataclasses import dataclass
        from datetime import datetime

        @dataclass
        class MaintenanceLog:
            id: str
            item_id: str
            item_type: str
            log_type: str
            date: datetime
            details: str
            ammo_count: int
            photo_path: str

        return [
            MaintenanceLog(
                id=row[0],
                item_id=row[1],
                item_type=row[2],
                log_type=row[3],
                date=datetime.fromtimestamp(row[4]) if row[4] else None,
                details=row[5] or "",
                ammo_count=row[6],
                photo_path=row[7],
            )
            for row in rows
        ]

    def update_nfa_status(self, item_id: str, status: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE nfa_items SET status = ? WHERE id = ?", (status, item_id)
        )
        conn.commit()
        conn.close()

    def add_attachment(self, attachment: Attachment) -> None:
        conn = self.db.connect()
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
        conn = self.db.connect()
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
        conn = self.db.connect()
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
        conn = self.db.connect()
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
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
        conn.commit()
        conn.close()

    def update_attachment_firearm(
        self, attachment_id: str, firearm_id: str | None
    ) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE attachments SET mounted_on_firearm_id = ? WHERE id = ?",
            (firearm_id, attachment_id),
        )
        conn.commit()
        conn.close()
