from datetime import datetime
from typing import Optional
from src.models import Checkout, GearCategory, CheckoutStatus
import uuid


class CheckoutService:
    def __init__(self, checkout_repo, firearm_repo, gear_repo):
        self.checkout_repo = checkout_repo
        self.firearm_repo = firearm_repo
        self.gear_repo = gear_repo

    def checkout_item(
        self,
        item_id: str,
        item_type: str,
        borrower_name: str,
        expected_return: Optional[datetime] = None,
        notes: str = "",
    ) -> tuple[bool, str]:
        borrower = self.checkout_repo.get_borrower_by_name(borrower_name)
        if not borrower:
            return (False, f"Borrower not found: {borrower_name}")

        item_type_val = item_type.value if hasattr(item_type, "value") else item_type

        if item_type_val == GearCategory.FIREARM.value:
            firearm = self.firearm_repo.get_by_id(item_id)
            if not firearm:
                return (False, "Firearm not found")
            status = (
                firearm.status
                if isinstance(firearm.status, str)
                else firearm.status.value
            )
            if status != CheckoutStatus.AVAILABLE.value:
                return (False, f"Firearm is not available (status: {status})")
            if firearm.needs_maintenance:
                return (False, "Firearm needs maintenance before checkout")

        checkout = Checkout(
            id=str(uuid.uuid4()),
            item_id=item_id,
            item_type=item_type,
            borrower_name=borrower_name,
            checkout_date=datetime.now(),
            expected_return=expected_return,
            notes=notes,
        )

        try:
            self.checkout_repo.add_checkout(checkout)
        except ValueError as e:
            return (False, str(e))

        if item_type_val == GearCategory.FIREARM.value:
            self.firearm_repo.update_status(item_id, CheckoutStatus.CHECKED_OUT.value)
        elif item_type_val == GearCategory.SOFT_GEAR.value:
            self.gear_repo.update_soft_gear_status(
                item_id, CheckoutStatus.CHECKED_OUT.value
            )
        elif item_type_val == GearCategory.NFA_ITEM.value:
            self.gear_repo.update_status(item_id, CheckoutStatus.CHECKED_OUT.value)

        return (True, checkout.id)

    def return_item(self, checkout_id: str) -> bool:
        checkout = self.checkout_repo.get_checkout_by_id(checkout_id)
        if not checkout:
            return False

        self.checkout_repo.return_item(checkout_id)

        item_type = (
            checkout.item_type.value
            if hasattr(checkout.item_type, "value")
            else checkout.item_type
        )
        item_id = checkout.item_id

        if item_type == GearCategory.FIREARM.value:
            self.firearm_repo.update_status(item_id, CheckoutStatus.AVAILABLE.value)
        elif item_type == GearCategory.SOFT_GEAR.value:
            self.gear_repo.update_soft_gear_status(
                item_id, CheckoutStatus.AVAILABLE.value
            )
        elif item_type == GearCategory.NFA_ITEM.value:
            self.gear_repo.update_status(item_id, CheckoutStatus.AVAILABLE.value)

        return True

    def get_active_checkouts(self) -> list[Checkout]:
        return self.checkout_repo.get_active_checkouts()

    def get_checkout_history(self) -> list[Checkout]:
        return self.checkout_repo.get_checkout_history()

    def get_checkout_by_id(self, checkout_id: str) -> Optional[Checkout]:
        return self.checkout_repo.get_checkout_by_id(checkout_id)

    def is_item_checked_out(self, item_id: str) -> bool:
        return self.checkout_repo.get_checkout_by_item(item_id) is not None

    def get_checkout_for_item(self, item_id: str) -> Optional[Checkout]:
        return self.checkout_repo.get_checkout_by_item(item_id)
