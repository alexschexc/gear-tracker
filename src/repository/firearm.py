from datetime import datetime
from typing import Optional
from src.models import Firearm, Transfer, TransferStatus, NFAFirearmType, CheckoutStatus


class FirearmRepository:
    def __init__(self, db):
        self.db = db

    def add(self, firearm: Firearm) -> None:
        conn = self.db.connect()
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
                firearm.status.value
                if isinstance(firearm.status, CheckoutStatus)
                else firearm.status,
                1 if firearm.is_nfa else 0,
                firearm.nfa_type.value if firearm.nfa_type else None,
                firearm.tax_stamp_id,
                firearm.form_type,
                firearm.barrel_length,
                firearm.trust_name,
                firearm.transfer_status.value
                if isinstance(firearm.transfer_status, TransferStatus)
                else firearm.transfer_status,
                firearm.rounds_fired,
                firearm.clean_interval_rounds,
                firearm.oil_interval_days,
                1 if firearm.needs_maintenance else 0,
                firearm.maintenance_conditions,
            ),
        )
        conn.commit()
        conn.close()

    def get_all(self) -> list[Firearm]:
        conn = self.db.connect()
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
                status=CheckoutStatus(row[6]).value if row[6] else "AVAILABLE",
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

    def get_by_id(self, firearm_id: str) -> Optional[Firearm]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM firearms WHERE id = ?", (firearm_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Firearm(
            id=row[0],
            name=row[1],
            caliber=row[2],
            serial_number=row[3],
            purchase_date=datetime.fromtimestamp(row[4]),
            notes=row[5] or "",
            status=CheckoutStatus(row[6]).value if row[6] else "AVAILABLE",
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

    def update_status(self, firearm_id: str, status: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE firearms SET status = ? WHERE id = ?", (status, firearm_id)
        )
        conn.commit()
        conn.close()

    def delete(self, firearm_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM maintenance_logs WHERE item_id = ?", (firearm_id,))
        cursor.execute("DELETE FROM checkouts WHERE item_id = ?", (firearm_id,))
        cursor.execute("DELETE FROM firearms WHERE id = ?", (firearm_id,))
        conn.commit()
        conn.close()

    def update_rounds(self, firearm_id: str, rounds: int) -> None:
        conn = self.db.connect()
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
        conn = self.db.connect()
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
        self, firearm_id: str, maintenance_type: str, details: str = ""
    ) -> None:
        from src.models import MaintenanceLog, GearCategory, MaintenanceType
        from datetime import datetime
        import uuid as uuid_lib

        conn = self.db.connect()
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

        if maintenance_type == MaintenanceType.CLEANING.value:
            new_rounds = 0
            cursor.execute(
                "UPDATE firearms SET rounds_fired = ?, needs_maintenance = 0 WHERE id = ?",
                (new_rounds, firearm_id),
            )

        log = MaintenanceLog(
            id=str(uuid_lib.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType(maintenance_type),
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


class TransferRepository:
    def __init__(self, db):
        self.db = db

    def add(self, transfer: Transfer) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()

    def get_all(self) -> list[Transfer]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transfers ORDER BY transfer_date DESC")
        rows = cursor.fetchall()
        conn.close()

        return [
            Transfer(
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
            for row in rows
        ]

    def get_by_firearm(self, firearm_id: str) -> list[Transfer]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transfers WHERE firearm_id = ?", (firearm_id,))
        rows = cursor.fetchall()
        conn.close()

        return [
            Transfer(
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
            for row in rows
        ]

    def update_firearm_status(self, firearm_id: str, status: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE firearms SET transfer_status = ? WHERE id = ?",
            (status, firearm_id),
        )
        conn.commit()
        conn.close()
