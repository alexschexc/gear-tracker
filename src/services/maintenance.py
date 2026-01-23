from datetime import datetime
from typing import Optional
from src.models import MaintenanceType


class MaintenanceService:
    def __init__(self, maintenance_repo, firearm_repo):
        self.maintenance_repo = maintenance_repo
        self.firearm_repo = firearm_repo

    def log_cleaning(self, firearm_id: str, details: str = "") -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        self.firearm_repo.mark_maintenance_done(
            firearm_id, MaintenanceType.CLEANING.value, details
        )

    def log_fired_rounds(self, firearm_id: str, rounds: int, details: str = "") -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.FIRED_ROUNDS,
            date=datetime.now(),
            details=details or f"Rounds fired: {rounds}",
            ammo_count=rounds,
        )
        self.maintenance_repo.add_log(log)

        self.firearm_repo.update_rounds(firearm_id, rounds)

    def log_lubrication(self, firearm_id: str, details: str = "") -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.LUBRICATION,
            date=datetime.now(),
            details=details,
        )
        self.maintenance_repo.add_log(log)

    def log_repair(self, firearm_id: str, details: str = "") -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.REPAIR,
            date=datetime.now(),
            details=details,
        )
        self.maintenance_repo.add_log(log)

    def log_inspection(self, firearm_id: str, details: str = "") -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.INSPECTION,
            date=datetime.now(),
            details=details,
        )
        self.maintenance_repo.add_log(log)

    def log_hunting(self, firearm_id: str, details: str = "") -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.HUNTING,
            date=datetime.now(),
            details=details,
        )
        self.maintenance_repo.add_log(log)

    def log_rain_exposure(self, firearm_id: str, details: str = "") -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.RAIN_EXPOSURE,
            date=datetime.now(),
            details=details or "Rain exposure - thorough cleaning recommended",
        )
        self.maintenance_repo.add_log(log)

    def log_corrosive_ammo(
        self, firearm_id: str, ammo_type: str = "", details: str = ""
    ) -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.CORROSIVE_AMMO,
            date=datetime.now(),
            details=details or f"Corrosive ammo used: {ammo_type}",
        )
        self.maintenance_repo.add_log(log)

    def log_lead_ammo(self, firearm_id: str, details: str = "") -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.LEAD_AMMO,
            date=datetime.now(),
            details=details or "Lead ammo used - barrel cleaning recommended",
        )
        self.maintenance_repo.add_log(log)

    def log_oiling(self, firearm_id: str, details: str = "") -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.OILING,
            date=datetime.now(),
            details=details,
        )
        self.maintenance_repo.add_log(log)

    def log_zeroing(self, firearm_id: str, distance: int, notes: str = "") -> None:
        from src.models import MaintenanceLog, GearCategory
        import uuid

        log = MaintenanceLog(
            id=str(uuid.uuid4()),
            item_id=firearm_id,
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.ZEROING,
            date=datetime.now(),
            details=f"Zeroed at {distance} yards" + (f": {notes}" if notes else ""),
        )
        self.maintenance_repo.add_log(log)

    def get_maintenance_history(self, item_id: str) -> list:
        return self.maintenance_repo.get_logs_for_item(item_id)

    def get_maintenance_status(self, firearm_id: str) -> dict:
        return self.firearm_repo.get_maintenance_status(firearm_id)

    def get_last_cleaning_date(self, item_id: str) -> Optional[datetime]:
        return self.maintenance_repo.get_last_cleaning_date(item_id)

    def needs_maintenance_soon(self, firearm_id: str) -> tuple[bool, list[str]]:
        status = self.firearm_repo.get_maintenance_status(firearm_id)
        return (status["needs_maintenance"], status["reasons"])

    def get_firearms_needing_maintenance(self) -> list:
        firearms = self.firearm_repo.get_all()
        result = []
        for fw in firearms:
            status = self.firearm_repo.get_maintenance_status(fw.id)
            if status["needs_maintenance"]:
                result.append((fw, status["reasons"]))
        return result
