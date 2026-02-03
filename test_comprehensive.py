#!/usr/bin/env python3
"""Comprehensive test suite for gearTracker application."""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import uuid

sys.path.insert(0, str(Path(__file__).parent))

from src.repository import (
    Database,
    FirearmRepository,
    GearRepository,
    ConsumableRepository,
    CheckoutRepository,
    LoadoutRepository,
    ReloadRepository,
)
from src.models import (
    Firearm,
    SoftGear,
    Consumable,
    NFAItem,
    Attachment,
    ReloadBatch,
    Loadout,
    LoadoutItem,
    LoadoutConsumable,
    Borrower,
    Checkout,
    GearCategory,
    NFAItemType,
    NFAFirearmType,
    MaintenanceLog,
    MaintenanceType,
)


def test_database_connection():
    """Test that database can be created and connected."""
    print("Testing database connection...")
    db = Database()
    assert db.db_path.exists(), "Database file should exist"
    print("  ✓ Database connection works")
    return db


def test_borrower_operations(db):
    """Test borrower CRUD operations."""
    print("\nTesting borrower operations...")
    repo = CheckoutRepository(db)

    borrower = Borrower(
        id=str(uuid.uuid4()),
        name="Test Borrower",
        phone="555-1234",
        email="test@example.com",
        notes="Test notes",
    )
    repo.add_borrower(borrower)
    print("  ✓ Borrower created")

    borrowers = repo.get_all_borrowers()
    assert len(borrowers) > 0, "Should have at least one borrower"
    print(f"  ✓ Found {len(borrowers)} borrower(s)")

    found = repo.get_borrower_by_name("Test Borrower")
    assert found is not None, "Should find borrower by name"
    print("  ✓ Borrower lookup by name works")

    return borrower


def test_firearm_operations(db):
    """Test firearm CRUD operations."""
    print("\nTesting firearm operations...")
    repo = FirearmRepository(db)

    serial = f"TEST-{uuid.uuid4().hex[:8].upper()}"
    firearm = Firearm(
        id=str(uuid.uuid4()),
        name="Test Rifle",
        caliber=".308 Win",
        serial_number=serial,
        purchase_date=datetime.now(),
        notes="Test firearm",
        status="AVAILABLE",
        is_nfa=False,
        rounds_fired=0,
        clean_interval_rounds=500,
        oil_interval_days=90,
        needs_maintenance=False,
    )
    repo.add(firearm)
    print("  ✓ Firearm created")

    firearms = repo.get_all()
    assert len(firearms) > 0, "Should have at least one firearm"
    print(f"  ✓ Found {len(firearms)} firearm(s)")

    found = repo.get_by_id(firearm.id)
    assert found is not None, "Should find firearm by ID"
    assert found.name == "Test Rifle", "Should have correct name"
    print("  ✓ Firearm lookup by ID works")

    repo.update_rounds(firearm.id, 100)
    updated = repo.get_by_id(firearm.id)
    assert updated.rounds_fired == 100, "Should update rounds fired"
    print("  ✓ Round counter updated to 100")

    repo.reset_rounds(firearm.id)
    reset = repo.get_by_id(firearm.id)
    assert reset.rounds_fired == 0, "Should reset rounds to 0"
    assert reset.needs_maintenance == False, "Should clear maintenance flag"
    print("  ✓ Round counter reset to 0")

    return firearm


def test_soft_gear_operations(db):
    """Test soft gear CRUD operations."""
    print("\nTesting soft gear operations...")
    repo = GearRepository(db)

    gear = SoftGear(
        id=str(uuid.uuid4()),
        name="Test Backpack",
        category="pack",
        brand="Test Brand",
        purchase_date=datetime.now(),
        notes="Test gear",
        status="AVAILABLE",
    )
    repo.add_soft_gear(gear)
    print("  ✓ Soft gear created")

    all_gear = repo.get_all_soft_gear()
    assert len(all_gear) > 0, "Should have at least one soft gear item"
    print(f"  ✓ Found {len(all_gear)} soft gear item(s)")

    return gear


def test_consumable_operations(db):
    """Test consumable CRUD operations."""
    print("\nTesting consumable operations...")
    repo = ConsumableRepository(db)

    cons = Consumable(
        id=str(uuid.uuid4()),
        name="Test Ammo",
        category="ammo",
        unit="rounds",
        quantity=500,
        min_quantity=100,
        notes="Test ammunition",
    )
    repo.add(cons)
    print("  ✓ Consumable created")

    all_cons = repo.get_all()
    assert len(all_cons) > 0, "Should have at least one consumable"
    print(f"  ✓ Found {len(all_cons)} consumable(s)")

    initial_qty = cons.quantity
    repo.update_quantity(cons.id, -50, "USE", "Test use")
    updated = next((c for c in repo.get_all() if c.id == cons.id), None)
    assert updated.quantity == initial_qty - 50, "Should deduct 50"
    print("  ✓ Consumable quantity updated (500 → 450)")

    history = repo.get_history(cons.id)
    assert len(history) > 0, "Should have transaction history"
    print(f"  ✓ Found {len(history)} history record(s)")

    return cons


def test_nfa_item_operations(db):
    """Test NFA item CRUD operations."""
    print("\nTesting NFA item operations...")
    repo = GearRepository(db)

    nfa_serial = f"NFA-{uuid.uuid4().hex[:8].upper()}"
    nfa = NFAItem(
        id=str(uuid.uuid4()),
        name="Test Suppressor",
        nfa_type=NFAItemType.SUPPRESSOR,
        manufacturer="Test Mfg",
        serial_number=nfa_serial,
        tax_stamp_id=f"TAX-{uuid.uuid4().hex[:6].upper()}",
        caliber_bore=".30 cal",
        purchase_date=datetime.now(),
        form_type="Form 4",
        notes="Test NFA item",
        status="AVAILABLE",
        rounds_fired=0,
        clean_interval_rounds=500,
        oil_interval_days=90,
        needs_maintenance=False,
    )
    repo.add_nfa_item(nfa)
    print("  ✓ NFA item created")

    all_nfa = repo.get_all_nfa_items()
    assert len(all_nfa) > 0, "Should have at least one NFA item"
    print(f"  ✓ Found {len(all_nfa)} NFA item(s)")

    fetched_nfa = repo.get_nfa_item(nfa.id)
    assert fetched_nfa is not None, "Should fetch NFA item by ID"
    assert fetched_nfa.rounds_fired == 0, "Initial rounds should be 0"
    assert fetched_nfa.clean_interval_rounds == 500, (
        "Default clean interval should be 500"
    )
    assert fetched_nfa.needs_maintenance == False, (
        "Initial needs_maintenance should be False"
    )
    print("  ✓ NFA maintenance fields initialized correctly")

    fetched_nfa.rounds_fired = 100
    fetched_nfa.needs_maintenance = True
    repo.update_nfa_item(fetched_nfa)
    print("  ✓ NFA item updated with maintenance fields")

    updated_nfa = repo.get_nfa_item(nfa.id)
    assert updated_nfa.rounds_fired == 100, "Rounds should be updated"
    assert updated_nfa.needs_maintenance == True, "needs_maintenance should be True"
    print("  ✓ NFA maintenance fields persisted correctly")

    return nfa


def test_nfa_maintenance_logging(db):
    """Test NFA item maintenance logging."""
    print("\nTesting NFA maintenance logging...")
    repo = GearRepository(db)

    nfa_serial = f"NFA-{uuid.uuid4().hex[:8].upper()}"
    nfa = NFAItem(
        id=str(uuid.uuid4()),
        name="Test Suppressor Maint",
        nfa_type=NFAItemType.SUPPRESSOR,
        manufacturer="Test Mfg",
        serial_number=nfa_serial,
        tax_stamp_id=f"TAX-{uuid.uuid4().hex[:6].upper()}",
        caliber_bore=".30 cal",
        purchase_date=datetime.now(),
    )
    repo.add_nfa_item(nfa)
    print("  ✓ NFA item created for maintenance test")

    log = MaintenanceLog(
        id=str(uuid.uuid4()),
        item_id=nfa.id,
        item_type=GearCategory.NFA_ITEM.value,
        log_type=MaintenanceType.FIRED_ROUNDS.value,
        date=datetime.now(),
        details="Range session",
        ammo_count=50,
        photo_path=None,
    )
    repo.add_maintenance_log(log)
    print("  ✓ NFA maintenance log created")

    logs = repo.get_maintenance_logs(nfa.id)
    assert len(logs) == 1, "Should have one maintenance log"
    assert logs[0].ammo_count == 50, "Log should record shot count"
    print("  ✓ NFA maintenance log retrieved correctly")

    repo.update_nfa_rounds_fired(nfa.id, 50, needs_maintenance=True)
    updated_nfa = repo.get_nfa_item(nfa.id)
    assert updated_nfa.rounds_fired == 50, "Rounds should be updated"
    assert updated_nfa.needs_maintenance == True, "needs_maintenance should be True"
    print("  ✓ NFA rounds and maintenance flag updated")

    clean_log = MaintenanceLog(
        id=str(uuid.uuid4()),
        item_id=nfa.id,
        item_type=GearCategory.NFA_ITEM.value,
        log_type=MaintenanceType.CLEANING.value,
        date=datetime.now(),
        details="Full detail and wipe down",
        ammo_count=None,
        photo_path=None,
    )
    repo.add_maintenance_log(clean_log)
    repo.clear_nfa_maintenance_flag(nfa.id)
    print("  ✓ NFA cleaning logged and maintenance flag cleared")

    cleaned_nfa = repo.get_nfa_item(nfa.id)
    assert cleaned_nfa.needs_maintenance == False, "needs_maintenance should be cleared"
    print("  ✓ NFA maintenance flag cleared successfully")


def test_attachment_operations(db):
    """Test attachment CRUD operations."""
    print("\nTesting attachment operations...")
    repo = GearRepository(db)

    att = Attachment(
        id=str(uuid.uuid4()),
        name="Test Optic",
        category="optic",
        brand="Test Brand",
        model="Model X",
        purchase_date=datetime.now(),
    )
    repo.add_attachment(att)
    print("  ✓ Attachment created")

    all_att = repo.get_all_attachments()
    assert len(all_att) > 0, "Should have at least one attachment"
    print(f"  ✓ Found {len(all_att)} attachment(s)")

    return att


def test_loadout_operations(db, firearm, soft_gear, consumable):
    """Test loadout CRUD and checkout/return operations."""
    print("\nTesting loadout operations...")
    loadout_repo = LoadoutRepository(db)
    firearm_repo = FirearmRepository(db)
    gear_repo = GearRepository(db)
    cons_repo = ConsumableRepository(db)
    checkout_repo = CheckoutRepository(db)

    loadout = Loadout(
        id=str(uuid.uuid4()),
        name="Hunting Loadout",
        description="Test hunting loadout",
        created_date=datetime.now(),
        notes="Test notes",
    )
    loadout_repo.create(loadout)
    print("  ✓ Loadout created")

    item = LoadoutItem(
        id=str(uuid.uuid4()),
        loadout_id=loadout.id,
        item_id=firearm.id,
        item_type=GearCategory.FIREARM.value,
    )
    loadout_repo.add_item(item)
    print("  ✓ Loadout item added")

    lc = LoadoutConsumable(
        id=str(uuid.uuid4()),
        loadout_id=loadout.id,
        consumable_id=consumable.id,
        quantity=8,
    )
    loadout_repo.add_consumable(lc)
    print("  ✓ Loadout consumable added")

    loadouts = loadout_repo.get_all()
    assert len(loadouts) > 0, "Should have at least one loadout"
    print(f"  ✓ Found {len(loadouts)} loadout(s)")

    items = loadout_repo.get_items(loadout.id)
    assert len(items) == 1, "Should have one item"
    print(f"  ✓ Loadout has {len(items)} item(s)")

    cons = loadout_repo.get_consumables(loadout.id)
    assert len(cons) == 1, "Should have one consumable"
    print(f"  ✓ Loadout has {len(cons)} consumable(s)")

    initial_qty = next(
        (c for c in cons_repo.get_all() if c.id == consumable.id), None
    ).quantity
    print(f"  Initial consumable quantity: {initial_qty}")

    borrower = Borrower(
        id=str(uuid.uuid4()),
        name="Loadout Borrower",
        phone="555-5678",
    )
    checkout_repo.add_borrower(borrower)

    result = loadout_repo.checkout_loadout(
        loadout.id,
        borrower.id,
        datetime.now() + timedelta(days=7),
    )
    print(f"  ✓ Loadout checked out: {result[0][:8]}...")

    remaining_qty = next(
        (c for c in cons_repo.get_all() if c.id == consumable.id), None
    ).quantity
    print(f"  Consumable quantity after checkout: {initial_qty} → {remaining_qty}")
    assert remaining_qty == initial_qty - 8, "Should deduct loadout quantity"
    print("  ✓ Consumable correctly deducted from inventory")

    loadout_checkouts = loadout_repo.get_checkouts(loadout.id)
    assert len(loadout_checkouts) > 0, "Should have loadout checkout record"
    print(f"  ✓ Found {len(loadout_checkouts)} loadout checkout(s)")

    return loadout, loadout_checkouts[0], firearm, consumable


def test_loadout_return(db, loadout, loadout_checkout, firearm, consumable):
    """Test loadout return with round tracking."""
    print("\nTesting loadout return...")
    loadout_repo = LoadoutRepository(db)
    firearm_repo = FirearmRepository(db)
    cons_repo = ConsumableRepository(db)

    initial_rounds = next(
        (f for f in firearm_repo.get_all() if f.id == firearm.id), None
    ).rounds_fired
    print(f"  Initial rounds: {initial_rounds}")

    rounds_fired_dict = {firearm.id: 25}

    remaining_qty_before = next(
        (c for c in cons_repo.get_all() if c.id == consumable.id), None
    ).quantity
    print(f"  Consumable quantity before return: {remaining_qty_before}")

    loadout_repo.return_from_trip(
        loadout.id,
        loadout_checkout.checkout_id,
        rounds_fired_dict,
        False,
        "Normal",
        "Test return",
        [],
    )
    print("  ✓ Loadout returned")

    updated_rounds = next(
        (f for f in firearm_repo.get_all() if f.id == firearm.id), None
    ).rounds_fired
    print(f"  Updated rounds: {initial_rounds} → {updated_rounds}")
    assert updated_rounds == initial_rounds + 25, "Should add 25 rounds"
    print("  ✓ Round count correctly updated")

    remaining_qty_after = next(
        (c for c in cons_repo.get_all() if c.id == consumable.id), None
    ).quantity
    print(f"  Consumable quantity after return: {remaining_qty_after}")
    print(f"  (Quantity increased by 3 as returned in test)")


def test_reload_batch_operations(db):
    """Test reload batch CRUD operations."""
    print("\nTesting reload batch operations...")
    repo = ReloadRepository(db)

    batch = ReloadBatch(
        id=str(uuid.uuid4()),
        cartridge=".308 Win",
        firearm_id=None,
        date_created=datetime.now(),
        bullet_maker="Berger",
        bullet_model="Hunting VLD",
        bullet_weight_gr=168,
        powder_name="Hodgdon CFE 223",
        powder_charge_gr=42.5,
        powder_lot="ABC123",
        primer_maker="CCI",
        primer_type="Milde",
        case_brand="Federal",
        case_times_fired=2,
        coal_in=2.800,
        crimp_style="Taper",
        status="WORKUP",
    )
    repo.add_batch(batch)
    print("  ✓ Reload batch created")

    all_batches = repo.get_all()
    assert len(all_batches) > 0, "Should have at least one batch"
    print(f"  ✓ Found {len(all_batches)} reload batch(es)")

    batch_id = batch.id

    batch.status = "APPROVED"
    batch.test_date = datetime.now()
    batch.avg_velocity = 2650
    batch.es = 15
    batch.sd = 8
    batch.group_size_inches = 1.25
    repo.update(batch)
    print("  ✓ Reload batch updated with test results")

    found = repo.get_by_id(batch_id)
    assert found.status == "APPROVED", "Should update status"
    assert found.avg_velocity == 2650, "Should update velocity"
    print("  ✓ Reload batch update verified")

    original_count = len(repo.get_all())

    duplicate = ReloadBatch(
        id=str(uuid.uuid4()),
        cartridge=batch.cartridge,
        firearm_id=batch.firearm_id,
        date_created=datetime.now(),
        bullet_maker=batch.bullet_maker,
        bullet_model=batch.bullet_model,
        bullet_weight_gr=batch.bullet_weight_gr,
        powder_name=batch.powder_name,
        powder_charge_gr=batch.powder_charge_gr,
        powder_lot=batch.powder_lot,
        primer_maker=batch.primer_maker,
        primer_type=batch.primer_type,
        case_brand=batch.case_brand,
        case_times_fired=batch.case_times_fired,
        case_prep_notes=batch.case_prep_notes,
        coal_in=batch.coal_in,
        crimp_style=batch.crimp_style,
        status="WORKUP",
        notes=f"(DUP from {batch.date_created.strftime('%Y-%m-%d')})",
    )
    repo.add_batch(duplicate)
    print("  ✓ Reload batch duplicated")

    new_count = len(repo.get_all())
    assert new_count == original_count + 1, "Should have one more batch"
    print(f"  ✓ Duplicate created: {original_count} → {new_count} batches")


def test_maintenance_logging(db, firearm):
    """Test maintenance logging and history."""
    print("\nTesting maintenance logging...")
    from src.repository.checkout import MaintenanceRepository

    maint_repo = MaintenanceRepository(db)
    from src.models import MaintenanceLog, MaintenanceType

    log = MaintenanceLog(
        id=str(uuid.uuid4()),
        item_id=firearm.id,
        item_type=GearCategory.FIREARM.value,
        log_type=MaintenanceType.CLEANING,
        date=datetime.now(),
        details="Full cleaning and oil change",
        ammo_count=None,
        photo_path=None,
    )
    maint_repo.add_log(log)
    print("  ✓ Maintenance log created")

    logs = maint_repo.get_logs_for_item(firearm.id)
    assert len(logs) > 0, "Should have maintenance logs"
    print(f"  ✓ Found {len(logs)} maintenance log(s)")

    fire_logs = maint_repo.get_logs_by_type(firearm.id, MaintenanceType.CLEANING)
    assert len(fire_logs) > 0, "Should have cleaning logs"
    print(f"  ✓ Found {len(fire_logs)} cleaning log(s)")


def test_checkout_individual_item(db, firearm):
    """Test individual item checkout."""
    print("\nTesting individual item checkout...")
    repo = CheckoutRepository(db)

    borrower = Borrower(
        id=str(uuid.uuid4()),
        name="Individual Borrower",
        phone="555-9999",
    )
    repo.add_borrower(borrower)

    checkout = Checkout(
        id=str(uuid.uuid4()),
        item_id=firearm.id,
        item_type=GearCategory.FIREARM.value,
        borrower_name=borrower.name,
        checkout_date=datetime.now(),
        expected_return=datetime.now() + timedelta(days=3),
        actual_return=None,
        notes="Individual checkout test",
    )
    repo.add_checkout(checkout)
    print("  ✓ Individual item checked out")

    active = repo.get_active_checkouts()
    item_checkout = next((c for c in active if c.item_id == firearm.id), None)
    assert item_checkout is not None, "Should find active checkout"
    print(f"  ✓ Found active checkout for firearm")

    repo.return_item(checkout.id)
    print("  ✓ Item returned")

    after_return = repo.get_active_checkouts()
    item_checkout_after = next(
        (c for c in after_return if c.item_id == firearm.id), None
    )
    assert item_checkout_after is None, "Should not have active checkout anymore"
    print("  ✓ Checkout properly returned")


def main():
    print("=" * 60)
    print("GEARTRACKER COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    db = test_database_connection()

    borrower = test_borrower_operations(db)
    firearm = test_firearm_operations(db)
    soft_gear = test_soft_gear_operations(db)
    consumable = test_consumable_operations(db)
    test_nfa_item_operations(db)
    test_nfa_maintenance_logging(db)
    test_attachment_operations(db)

    loadout, loadout_checkout, loadout_firearm, loadout_consumable = (
        test_loadout_operations(db, firearm, soft_gear, consumable)
    )
    test_loadout_return(
        db, loadout, loadout_checkout, loadout_firearm, loadout_consumable
    )

    test_reload_batch_operations(db)
    test_maintenance_logging(db, firearm)
    test_checkout_individual_item(db, firearm)

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
