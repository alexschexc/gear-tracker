import pytest
import tempfile
from pathlib import Path
from src.repository import (
    Database,
    FirearmRepository,
    GearRepository,
    ConsumableRepository,
)


class TestLoadoutService:
    def test_loadout_validation_result(self):
        from src.services.loadout import LoadoutValidationResult

        result = LoadoutValidationResult(
            can_checkout=True,
            warnings=["Warning 1"],
            critical_issues=[],
        )
        assert result.can_checkout is True
        assert len(result.warnings) == 1

    def test_loadout_service_initialization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)

            from src.services.loadout import LoadoutService
            from src.repository import LoadoutRepository, CheckoutRepository

            loadout_repo = LoadoutRepository(db)
            firearm_repo = FirearmRepository(db)
            gear_repo = GearRepository(db)
            consumable_repo = ConsumableRepository(db)
            checkout_repo = CheckoutRepository(db)

            service = LoadoutService(
                loadout_repo, firearm_repo, gear_repo, consumable_repo, checkout_repo
            )
            assert service is not None


class TestMaintenanceService:
    def test_maintenance_service_initialization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)

            from src.services.maintenance import MaintenanceService
            from src.repository import CheckoutRepository

            checkout_repo = CheckoutRepository(db)
            firearm_repo = FirearmRepository(db)

            service = MaintenanceService(checkout_repo, firearm_repo)
            assert service is not None


class TestCheckoutService:
    def test_checkout_service_initialization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)

            from src.services.checkout import CheckoutService
            from src.repository import CheckoutRepository

            checkout_repo = CheckoutRepository(db)
            firearm_repo = FirearmRepository(db)
            gear_repo = GearRepository(db)

            service = CheckoutService(checkout_repo, firearm_repo, gear_repo)
            assert service is not None

    def test_is_item_checked_out(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)

            from src.services.checkout import CheckoutService
            from src.repository import CheckoutRepository
            from src.models import Firearm

            checkout_repo = CheckoutRepository(db)
            firearm_repo = FirearmRepository(db)
            gear_repo = GearRepository(db)

            service = CheckoutService(checkout_repo, firearm_repo, gear_repo)

            fw = Firearm(
                id="test-fw-3",
                name="Test Shotgun",
                caliber="12 gauge",
                serial_number="SN003",
                purchase_date=__import__("datetime").datetime.now(),
            )
            firearm_repo.add(fw)

            result = service.is_item_checked_out("test-fw-3")
            assert result is False
