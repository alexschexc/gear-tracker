from datetime import datetime
from src.models import ReloadBatch


class ReloadRepository:
    def __init__(self, db):
        self.db = db

    def add_batch(self, batch: ReloadBatch) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reload_batches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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

    def get_all(self) -> list[ReloadBatch]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reload_batches ORDER BY date_created DESC")
        rows = cursor.fetchall()
        conn.close()

        return [
            ReloadBatch(
                id=row[0],
                cartridge=row[1],
                firearm_id=row[2],
                date_created=datetime.fromtimestamp(row[3]),
                bullet_maker=row[4] or "",
                bullet_model=row[5] or "",
                bullet_weight_gr=row[6],
                powder_name=row[7] or "",
                powder_charge_gr=row[8],
                powder_lot=row[9] or "",
                primer_maker=row[10] or "",
                primer_type=row[11] or "",
                case_brand=row[12] or "",
                case_times_fired=row[13],
                case_prep_notes=row[14] or "",
                coal_in=row[15],
                crimp_style=row[16] or "",
                test_date=datetime.fromtimestamp(row[17]) if row[17] else None,
                avg_velocity=row[18],
                es=row[19],
                sd=row[20],
                group_size_inches=row[21],
                group_distance_yards=row[22],
                intended_use=row[23] or "",
                status=row[24] or "WORKUP",
                notes=row[25] or "",
            )
            for row in rows
        ]

    def get_by_id(self, batch_id: str) -> ReloadBatch | None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reload_batches WHERE id = ?", (batch_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return ReloadBatch(
            id=row[0],
            cartridge=row[1],
            firearm_id=row[2],
            date_created=datetime.fromtimestamp(row[3]),
            bullet_maker=row[4] or "",
            bullet_model=row[5] or "",
            bullet_weight_gr=row[6],
            powder_name=row[7] or "",
            powder_charge_gr=row[8],
            powder_lot=row[9] or "",
            primer_maker=row[10] or "",
            primer_type=row[11] or "",
            case_brand=row[12] or "",
            case_times_fired=row[13],
            case_prep_notes=row[14] or "",
            coal_in=row[15],
            crimp_style=row[16] or "",
            test_date=datetime.fromtimestamp(row[17]) if row[17] else None,
            avg_velocity=row[18],
            es=row[19],
            sd=row[20],
            group_size_inches=row[21],
            group_distance_yards=row[22],
            intended_use=row[23] or "",
            status=row[24] or "WORKUP",
            notes=row[25] or "",
        )

    def get_by_firearm(self, firearm_id: str) -> list[ReloadBatch]:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM reload_batches WHERE firearm_id = ? ORDER BY date_created DESC",
            (firearm_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            ReloadBatch(
                id=row[0],
                cartridge=row[1],
                firearm_id=row[2],
                date_created=datetime.fromtimestamp(row[3]),
                bullet_maker=row[4] or "",
                bullet_model=row[5] or "",
                bullet_weight_gr=row[6],
                powder_name=row[7] or "",
                powder_charge_gr=row[8],
                powder_lot=row[9] or "",
                primer_maker=row[10] or "",
                primer_type=row[11] or "",
                case_brand=row[12] or "",
                case_times_fired=row[13],
                case_prep_notes=row[14] or "",
                coal_in=row[15],
                crimp_style=row[16] or "",
                test_date=datetime.fromtimestamp(row[17]) if row[17] else None,
                avg_velocity=row[18],
                es=row[19],
                sd=row[20],
                group_size_inches=row[21],
                group_distance_yards=row[22],
                intended_use=row[23] or "",
                status=row[24] or "WORKUP",
                notes=row[25] or "",
            )
            for row in rows
        ]

    def update(self, batch: ReloadBatch) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE reload_batches SET
                cartridge = ?,
                firearm_id = ?,
                bullet_maker = ?,
                bullet_model = ?,
                bullet_weight_gr = ?,
                powder_name = ?,
                powder_charge_gr = ?,
                powder_lot = ?,
                primer_maker = ?,
                primer_type = ?,
                case_brand = ?,
                case_times_fired = ?,
                case_prep_notes = ?,
                coal_in = ?,
                crimp_style = ?,
                test_date = ?,
                avg_velocity = ?,
                es = ?,
                sd = ?,
                group_size_inches = ?,
                group_distance_yards = ?,
                intended_use = ?,
                status = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                batch.cartridge,
                batch.firearm_id,
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

    def delete(self, batch_id: str) -> None:
        conn = self.db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reload_batches WHERE id = ?", (batch_id,))
        conn.commit()
        conn.close()
