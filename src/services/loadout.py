from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from src.models import (
    Loadout,
    LoadoutItem,
    LoadoutConsumable,
    LoadoutCheckout,
    GearCategory,
    CheckoutStatus,
    Firearm,
    SoftGear,
    NFAItem,
    Consumable,
)


@dataclass
class LoadoutValidationResult:
    can_checkout: bool
    warnings: list[str]
    critical_issues: list[str]


class LoadoutService:
    def __init__(
        self,
        loadout_repo,
        firearm_repo,
        gear_repo,
        consumable_repo,
        checkout_repo,
    ):
        self.loadout_repo = loadout_repo
        self.firearm_repo = firearm_repo
        self.gear_repo = gear_repo
        self.consumable_repo = consumable_repo
        self.checkout_repo = checkout_repo

    def validate_checkout(self, loadout_id: str) -> LoadoutValidationResult:
        loadout_items = self.loadout_repo.get_items(loadout_id)
        loadout_consumables = self.loadout_repo.get_consumables(loadout_id)

        warnings = []
        critical_issues = []

        firearms = self.firearm_repo.get_all()
        firearm_dict = {f.id: f for f in firearms}

        soft_gear = self.gear_repo.get_all_soft_gear()
        soft_gear_dict = {g.id: g for g in soft_gear}

        nfa_items = self.gear_repo.get_all_nfa_items()
        nfa_dict = {n.id: n for n in nfa_items}

        consumables = self.consumable_repo.get_all()
        consumable_dict = {c.id: c for c in consumables}

        for item in loadout_items:
            if item.item_type == GearCategory.FIREARM.value:
                if item.item_id in firearm_dict:
                    fw = firearm_dict[item.item_id]
                    status = (
                        fw.status if isinstance(fw.status, str) else fw.status.value
                    )
                    if status != CheckoutStatus.AVAILABLE.value:
                        critical_issues.append(
                            f"Firearm '{fw.name}' is not available (status: {status})"
                        )
                    if fw.needs_maintenance:
                        critical_issues.append(
                            f"Firearm '{fw.name}' needs maintenance before checkout"
                        )
            elif item.item_type == GearCategory.SOFT_GEAR.value:
                if item.item_id in soft_gear_dict:
                    gear = soft_gear_dict[item.item_id]
                    status = (
                        gear.status
                        if isinstance(gear.status, str)
                        else gear.status.value
                    )
                    if status != CheckoutStatus.AVAILABLE.value:
                        critical_issues.append(
                            f"Soft gear '{gear.name}' is not available (status: {status})"
                        )
            elif item.item_type == GearCategory.NFA_ITEM.value:
                if item.item_id in nfa_dict:
                    nfa = nfa_dict[item.item_id]
                    status = (
                        nfa.status if isinstance(nfa.status, str) else nfa.status.value
                    )
                    if status != CheckoutStatus.AVAILABLE.value:
                        critical_issues.append(
                            f"NFA item '{nfa.name}' is not available (status: {status})"
                        )

        for item in loadout_consumables:
            if item.consumable_id in consumable_dict:
                cons = consumable_dict[item.consumable_id]
                stock_after = cons.quantity - item.quantity
                if stock_after < 0:
                    warnings.append(
                        f"Consumable '{cons.name}': Will go negative ({stock_after} {cons.unit})"
                    )
                elif stock_after < cons.min_quantity:
                    warnings.append(
                        f"Consumable '{cons.name}': Will be below minimum ({stock_after} < {cons.min_quantity} {cons.unit})"
                    )

        return LoadoutValidationResult(
            can_checkout=len(critical_issues) == 0,
            warnings=warnings,
            critical_issues=critical_issues,
        )

    def checkout(
        self,
        loadout_id: str,
        borrower_name: str,
        expected_return: Optional[datetime] = None,
    ) -> tuple[str, list[str]]:
        import uuid

        validation = self.validate_checkout(loadout_id)
        if not validation.can_checkout:
            return ("", validation.critical_issues + validation.warnings)

        loadout_items = self.loadout_repo.get_items(loadout_id)
        loadout_consumables = self.loadout_repo.get_consumables(loadout_id)

        borrower = self.checkout_repo.get_borrower_by_name(borrower_name)
        if not borrower:
            return ("", [f"Borrower not found: {borrower_name}"])

        checkout_ids = []

        for item in loadout_items:
            checkout_id = str(uuid.uuid4())
            from src.models import Checkout

            checkout = Checkout(
                id=checkout_id,
                item_id=item.item_id,
                item_type=item.item_type,
                borrower_name=borrower_name,
                checkout_date=datetime.now(),
                expected_return=expected_return,
            )
            self.checkout_repo.add_checkout(checkout)

            item_type_val = (
                item.item_type.value
                if hasattr(item.item_type, "value")
                else item.item_type
            )

            if item_type_val == GearCategory.FIREARM.value:
                self.firearm_repo.update_status(
                    item.item_id, CheckoutStatus.CHECKED_OUT.value
                )
            elif item_type_val == GearCategory.SOFT_GEAR.value:
                self.gear_repo.update_soft_gear_status(
                    item.item_id, CheckoutStatus.CHECKED_OUT.value
                )
            elif item_type_val == GearCategory.NFA_ITEM.value:
                self.gear_repo.update_status(
                    item.item_id, CheckoutStatus.CHECKED_OUT.value
                )

            checkout_ids.append(checkout_id)

        consumables = self.consumable_repo.get_all()
        consumable_dict = {c.id: c for c in consumables}

        for item in loadout_consumables:
            if item.consumable_id in consumable_dict:
                cons = consumable_dict[item.consumable_id]
                self.consumable_repo.update_quantity(
                    item.consumable_id,
                    -item.quantity,
                    "USE",
                    f"Loadout checkout",
                )

        main_checkout_id = checkout_ids[0] if checkout_ids else ""

        loadout_checkout = LoadoutCheckout(
            id=str(uuid.uuid4()),
            loadout_id=loadout_id,
            checkout_id=main_checkout_id,
        )
        self.loadout_repo.checkout(loadout_checkout)

        return (main_checkout_id, validation.warnings)

    def return_loadout(
        self,
        loadout_checkout_id: str,
        rounds_fired_dict: dict,
        rain_exposure: bool = False,
        ammo_type: str = "",
        notes: str = "",
    ):
        import uuid as uuid_lib
        from src.models import MaintenanceLog, MaintenanceType

        checkout = self.loadout_repo.get_checkouts(loadout_checkout_id)
        if not checkout:
            return

        loadout_id = checkout[0].loadout_id
        main_checkout_id = checkout[0].checkout_id

        self.loadout_repo.return_items(loadout_id, main_checkout_id)

        loadout_items = self.loadout_repo.get_items(loadout_id)

        for item in loadout_items:
            existing_checkout = self.checkout_repo.get_checkout_by_item(item.item_id)
            if existing_checkout:
                self.checkout_repo.return_item(existing_checkout.id)

            item_type_val = (
                item.item_type.value
                if hasattr(item.item_type, "value")
                else item.item_type
            )

            if item_type_val == GearCategory.FIREARM.value:
                self.firearm_repo.update_status(
                    item.item_id, CheckoutStatus.AVAILABLE.value
                )
            elif item_type_val == GearCategory.SOFT_GEAR.value:
                self.gear_repo.update_soft_gear_status(
                    item.item_id, CheckoutStatus.AVAILABLE.value
                )
            elif item_type_val == GearCategory.NFA_ITEM.value:
                self.gear_repo.update_status(
                    item.item_id, CheckoutStatus.AVAILABLE.value
                )

        for item in loadout_items:
            if (
                item.item_type == GearCategory.FIREARM.value
                and item.item_id in rounds_fired_dict
            ):
                self.firearm_repo.update_rounds(
                    item.item_id, rounds_fired_dict[item.item_id]
                )

        for item in loadout_items:
            if (
                item.item_type == GearCategory.FIREARM.value
                and item.item_id in rounds_fired_dict
            ):
                log = MaintenanceLog(
                    id=str(uuid_lib.uuid4()),
                    item_id=item.item_id,
                    item_type=GearCategory.FIREARM,
                    log_type=MaintenanceType.FIRED_ROUNDS,
                    date=datetime.now(),
                    details=f"Rounds fired: {rounds_fired_dict[item.item_id]}",
                )
                self.checkout_repo.add_log(log)

                if rain_exposure:
                    rain_log = MaintenanceLog(
                        id=str(uuid_lib.uuid4()),
                        item_id=item.item_id,
                        item_type=GearCategory.FIREARM,
                        log_type=MaintenanceType.RAIN_EXPOSURE,
                        date=datetime.now(),
                        details="Rain exposure during hunt/trip",
                    )
                    self.checkout_repo.add_log(rain_log)

                if ammo_type:
                    ammo_log = MaintenanceLog(
                        id=str(uuid_lib.uuid4()),
                        item_id=item.item_id,
                        item_type=GearCategory.FIREARM,
                        log_type=MaintenanceType.CORROSIVE_AMMO
                        if "corrosive" in ammo_type.lower()
                        else MaintenanceType.LEAD_AMMO,
                        date=datetime.now(),
                        details=f"Ammo type: {ammo_type}",
                    )
                    self.checkout_repo.add_log(ammo_log)

    def get_loadout_with_details(self, loadout_id: str) -> dict:
        loadout = self.loadout_repo.get_by_id(loadout_id)
        if not loadout:
            return {}

        items = self.loadout_repo.get_items(loadout_id)
        consumables = self.loadout_repo.get_consumables(loadout_id)

        firearms = self.firearm_repo.get_all()
        firearm_dict = {f.id: f for f in firearms}

        soft_gear = self.gear_repo.get_all_soft_gear()
        soft_gear_dict = {g.id: g for g in soft_gear}

        nfa_items = self.gear_repo.get_all_nfa_items()
        nfa_dict = {n.id: n for n in nfa_items}

        consumables_all = self.consumable_repo.get_all()
        consumable_dict = {c.id: c for c in consumables_all}

        item_details = []
        for item in items:
            item_type = (
                item.item_type.value
                if hasattr(item.item_type, "value")
                else item.item_type
            )
            if item_type == GearCategory.FIREARM.value and item.item_id in firearm_dict:
                fw = firearm_dict[item.item_id]
                item_details.append(
                    {
                        "type": "FIREARM",
                        "name": fw.name,
                        "details": f"{fw.caliber}",
                    }
                )
            elif (
                item_type == GearCategory.SOFT_GEAR.value
                and item.item_id in soft_gear_dict
            ):
                gear = soft_gear_dict[item.item_id]
                item_details.append(
                    {
                        "type": "SOFT_GEAR",
                        "name": gear.name,
                        "details": gear.category,
                    }
                )
            elif item_type == GearCategory.NFA_ITEM.value and item.item_id in nfa_dict:
                nfa = nfa_dict[item.item_id]
                item_details.append(
                    {
                        "type": "NFA_ITEM",
                        "name": nfa.name,
                        "details": nfa.nfa_type.value
                        if hasattr(nfa.nfa_type, "value")
                        else nfa.nfa_type,
                    }
                )

        consumable_details = []
        for cons in consumables:
            if cons.consumable_id in consumable_dict:
                c = consumable_dict[cons.consumable_id]
                consumable_details.append(
                    {
                        "name": c.name,
                        "quantity": cons.quantity,
                        "unit": c.unit,
                    }
                )

        return {
            "loadout": loadout,
            "items": item_details,
            "consumables": consumable_details,
        }
