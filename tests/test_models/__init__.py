import pytest
from datetime import datetime
from src.models import (
    Firearm,
    Transfer,
    TransferStatus,
    NFAFirearmType,
    SoftGear,
    NFAItem,
    NFAItemType,
    Attachment,
    Consumable,
    ConsumableTransaction,
    MaintenanceLog,
    MaintenanceType,
    GearCategory,
    Checkout,
    Borrower,
    CheckoutStatus,
    Loadout,
    LoadoutItem,
    LoadoutConsumable,
    LoadoutCheckout,
    ReloadBatch,
)


class TestFirearmModel:
    def test_firearm_creation(self):
        fw = Firearm(
            id="test-id",
            name="Test Rifle",
            caliber="5.56",
            serial_number="SN123",
            purchase_date=datetime.now(),
            notes="Test firearm",
        )
        assert fw.id == "test-id"
        assert fw.name == "Test Rifle"
        assert fw.caliber == "5.56"
        assert fw.status == "AVAILABLE"
        assert fw.is_nfa is False

    def test_firearm_with_nfa(self):
        fw = Firearm(
            id="test-id",
            name="SBR Test",
            caliber="5.56",
            serial_number="SN456",
            purchase_date=datetime.now(),
            is_nfa=True,
            nfa_type=NFAFirearmType.SBR,
        )
        assert fw.is_nfa is True
        assert fw.nfa_type == NFAFirearmType.SBR


class TestTransferModel:
    def test_transfer_creation(self):
        transfer = Transfer(
            id="transfer-1",
            firearm_id="fw-1",
            transfer_date=datetime.now(),
            buyer_name="John Doe",
            buyer_address="123 Main St",
            buyer_dl_number="DL12345",
        )
        assert transfer.id == "transfer-1"
        assert transfer.firearm_id == "fw-1"
        assert transfer.transfer_status == TransferStatus.OWNED


class TestGearModels:
    def test_soft_gear_creation(self):
        gear = SoftGear(
            id="gear-1",
            name="Tactical Vest",
            category="BODY_ARMOR",
            brand="BrandX",
            purchase_date=datetime.now(),
        )
        assert gear.name == "Tactical Vest"
        assert gear.category == "BODY_ARMOR"

    def test_nfa_item_creation(self):
        item = NFAItem(
            id="nfa-1",
            name="Suppressor",
            nfa_type=NFAItemType.SUPPRESSOR,
            manufacturer="SureFire",
            serial_number="SF123",
            tax_stamp_id="TAX123",
            caliber_bore=".30 cal",
            purchase_date=datetime.now(),
        )
        assert item.nfa_type == NFAItemType.SUPPRESSOR

    def test_attachment_creation(self):
        att = Attachment(
            id="att-1",
            name="Red Dot",
            category="OPTIC",
            brand="Aimpoint",
            model="CompM4",
            purchase_date=datetime.now(),
        )
        assert att.mounted_on_firearm_id is None


class TestConsumableModel:
    def test_consumable_creation(self):
        cons = Consumable(
            id="cons-1",
            name="9mm Ammo",
            category="AMMUNITION",
            unit="rounds",
            quantity=500,
            min_quantity=100,
        )
        assert cons.quantity == 500


class TestMaintenanceModel:
    def test_maintenance_log_creation(self):
        log = MaintenanceLog(
            id="log-1",
            item_id="fw-1",
            item_type=GearCategory.FIREARM,
            log_type=MaintenanceType.CLEANING,
            date=datetime.now(),
            details="Full clean and oil",
        )
        assert log.log_type == MaintenanceType.CLEANING


class TestCheckoutModel:
    def test_checkout_creation(self):
        checkout = Checkout(
            id="co-1",
            item_id="fw-1",
            item_type=GearCategory.FIREARM,
            borrower_name="John Doe",
            checkout_date=datetime.now(),
            expected_return=None,
        )
        assert checkout.actual_return is None

    def test_borrower_creation(self):
        borrower = Borrower(
            id="b-1",
            name="John Doe",
            phone="555-1234",
            email="john@example.com",
        )
        assert borrower.name == "John Doe"


class TestLoadoutModel:
    def test_loadout_creation(self):
        loadout = Loadout(
            id="lo-1",
            name="Hunting Trip",
            description="Deer hunting loadout",
        )
        assert loadout.name == "Hunting Trip"

    def test_loadout_item_creation(self):
        item = LoadoutItem(
            id="li-1",
            loadout_id="lo-1",
            item_id="fw-1",
            item_type=GearCategory.FIREARM,
        )
        assert item.loadout_id == "lo-1"


class TestReloadModel:
    def test_reload_batch_creation(self):
        batch = ReloadBatch(
            id="batch-1",
            cartridge=".308 Win",
            firearm_id="fw-1",
            date_created=datetime.now(),
            bullet_maker="Hornady",
            bullet_model="BTHP",
            bullet_weight_gr=168,
            powder_name="H4350",
            powder_charge_gr=43.5,
        )
        assert batch.cartridge == ".308 Win"
        assert batch.bullet_weight_gr == 168
