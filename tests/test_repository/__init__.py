import pytest
import tempfile
from pathlib import Path
from src.repository import Database, FirearmRepository, GearRepository


class TestDatabase:
    def test_database_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='firearms'"
            )
            result = cursor.fetchone()
            conn.close()
            assert result is not None

    def test_firearm_crud(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            repo = FirearmRepository(db)

            from src.models import Firearm

            fw = Firearm(
                id="test-fw-1",
                name="Test Rifle",
                caliber="5.56",
                serial_number="SN001",
                purchase_date=__import__("datetime").datetime.now(),
            )

            repo.add(fw)
            all_firearms = repo.get_all()
            assert len(all_firearms) == 1
            assert all_firearms[0].name == "Test Rifle"

            fetched = repo.get_by_id("test-fw-1")
            assert fetched is not None
            assert fetched.serial_number == "SN001"

            repo.update_status("test-fw-1", "CHECKED_OUT")
            updated = repo.get_by_id("test-fw-1")
            assert updated.status == "CHECKED_OUT"

            repo.delete("test-fw-1")
            deleted = repo.get_by_id("test-fw-1")
            assert deleted is None

    def test_soft_gear_crud(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            repo = GearRepository(db)

            from src.models import SoftGear

            gear = SoftGear(
                id="test-gear-1",
                name="Plate Carrier",
                category="BODY_ARMOR",
                brand="BrandX",
                purchase_date=__import__("datetime").datetime.now(),
            )

            repo.add_soft_gear(gear)
            all_gear = repo.get_all_soft_gear()
            assert len(all_gear) == 1

            repo.delete_soft_gear("test-gear-1")
            all_gear = repo.get_all_soft_gear()
            assert len(all_gear) == 0

    def test_nfa_items_crud(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            repo = GearRepository(db)

            from src.models import NFAItem, NFAItemType

            item = NFAItem(
                id="test-nfa-1",
                name="Suppressor",
                nfa_type=NFAItemType.SUPPRESSOR,
                manufacturer="SureFire",
                serial_number="SF001",
                tax_stamp_id="TAX001",
                caliber_bore=".30 cal",
                purchase_date=__import__("datetime").datetime.now(),
            )

            repo.add_nfa_item(item)
            all_items = repo.get_all_nfa_items()
            assert len(all_items) == 1
            assert all_items[0].name == "Suppressor"


class TestMaintenanceRepository:
    def test_maintenance_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            repo = FirearmRepository(db)

            from src.models import Firearm

            fw = Firearm(
                id="test-fw-2",
                name="Test Pistol",
                caliber="9mm",
                serial_number="SN002",
                purchase_date=__import__("datetime").datetime.now(),
            )
            repo.add(fw)

            status = repo.get_maintenance_status("test-fw-2")
            assert "needs_maintenance" in status
            assert "reasons" in status
