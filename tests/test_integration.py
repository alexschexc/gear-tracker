import pytest


def test_models_available():
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

    assert Firearm is not None
    assert Transfer is not None
    assert SoftGear is not None
    assert NFAItem is not None


def test_repository_available():
    from src.repository import (
        Database,
        FirearmRepository,
        TransferRepository,
        GearRepository,
        ConsumableRepository,
        CheckoutRepository,
        MaintenanceRepository,
        LoadoutRepository,
        ReloadRepository,
    )

    assert Database is not None
    assert FirearmRepository is not None
    assert GearRepository is not None


def test_services_available():
    from src.services import (
        LoadoutService,
        MaintenanceService,
        CheckoutService,
    )

    assert LoadoutService is not None
    assert MaintenanceService is not None
    assert CheckoutService is not None


def test_ui_available():
    from src.ui import (
        GearTrackerMainWindow,
        BaseTab,
        FirearmsTab,
        LoadoutsTab,
        ConsumablesTab,
        BorrowersTab,
        CheckoutsTab,
    )

    assert GearTrackerMainWindow is not None
    assert FirearmsTab is not None
    assert LoadoutsTab is not None
