import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

from src.repository import (
    Database,
    FirearmRepository,
    GearRepository,
    ConsumableRepository,
    CheckoutRepository,
    LoadoutRepository,
    ReloadRepository,
    TransferRepository,
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
    NFAItemType,
    CheckoutStatus,
    NFAFirearmType,
    TransferStatus,
    GearCategory,
)


@dataclass
class ImportResult:
    success: bool
    total_rows: int
    imported: int
    skipped: int
    overwritten: int
    errors: list[str]
    warnings: list[str]
    entity_stats: dict[str, int]


@dataclass
class ValidationError:
    row_number: int
    entity_type: str
    field_name: str
    error_type: str
    message: str
    severity: str


class ImportExportService:
    def __init__(self, db: Database):
        self.db = db
        self.firearm_repo = FirearmRepository(db)
        self.gear_repo = GearRepository(db)
        self.consumable_repo = ConsumableRepository(db)
        self.checkout_repo = CheckoutRepository(db)
        self.loadout_repo = LoadoutRepository(db)
        self.reload_repo = ReloadRepository(db)
        self.transfer_repo = TransferRepository(db)

    def parse_sectioned_csv(self, input_path: Path) -> dict[str, list[dict[str, str]]]:
        result = {}
        current_section = None
        section_headers = []
        row_number = 0

        try:
            with open(input_path, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.reader(f)

                for row_number, row in enumerate(reader, start=1):
                    if not row:
                        continue

                    first_cell = row[0].strip()

                    if first_cell.startswith("===") and first_cell.endswith("==="):
                        current_section = first_cell.replace("=", "").strip().upper()
                        result[current_section] = []
                        section_headers = []
                        continue

                    if first_cell.startswith("#"):
                        continue

                    if current_section is None:
                        continue

                    if section_headers:
                        row_dict = {}
                        for i, header in enumerate(section_headers):
                            value = row[i] if i < len(row) else ""
                            row_dict[header.strip()] = value.strip()
                        result[current_section].append(row_dict)
                    else:
                        section_headers = [cell.strip() for cell in row]

        except Exception as e:
            raise Exception(f"Error parsing CSV at row {row_number}: {str(e)}")

        return result

    def validate_csv_data(self, parsed_data: dict) -> list[ValidationError]:
        errors = []
        row_num = 0

        for section_name, rows in parsed_data.items():
            for row in rows:
                row_num += 1
                if section_name == "FIREARMS":
                    errors.extend(self._validate_firearm_row(row, row_num))
                elif section_name == "NFA ITEMS":
                    errors.extend(self._validate_nfa_item_row(row, row_num))
                elif section_name == "SOFT GEAR":
                    errors.extend(self._validate_soft_gear_row(row, row_num))
                elif section_name == "ATTACHMENTS":
                    errors.extend(self._validate_attachment_row(row, row_num))
                elif section_name == "CONSUMABLES":
                    errors.extend(self._validate_consumable_row(row, row_num))
                elif section_name == "RELOAD BATCHES":
                    errors.extend(self._validate_reload_batch_row(row, row_num))
                elif section_name == "BORROWERS":
                    errors.extend(self._validate_borrower_row(row, row_num))
                elif section_name == "LOADOUTS":
                    errors.extend(self._validate_loadout_row(row, row_num))
                elif section_name == "LOADOUT ITEMS":
                    errors.extend(self._validate_loadout_item_row(row, row_num))
                elif section_name == "LOADOUT CONSUMABLES":
                    errors.extend(self._validate_loadout_consumable_row(row, row_num))

        return errors

    def _validate_firearm_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name", "caliber", "purchase_date"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "purchase_date" in row and row["purchase_date"]:
            try:
                datetime.fromisoformat(row["purchase_date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        "purchase_date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        if "status" in row and row["status"]:
            valid_statuses = [s.value for s in CheckoutStatus]
            if row["status"] not in valid_statuses:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        "status",
                        "invalid_enum",
                        f"Status must be one of: {', '.join(valid_statuses)}",
                        "error",
                    )
                )

        if "is_nfa" in row and row["is_nfa"]:
            if row["is_nfa"].upper() not in ["TRUE", "FALSE", "1", "0"]:
                errors.append(
                    ValidationError(
                        row_num,
                        "FIREARM",
                        "is_nfa",
                        "invalid_type",
                        "is_nfa must be TRUE/FALSE or 1/0",
                        "error",
                    )
                )

        return errors

    def _validate_nfa_item_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name", "nfa_type", "tax_stamp_id", "purchase_date"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "NFA_ITEM",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        if "purchase_date" in row and row["purchase_date"]:
            try:
                datetime.fromisoformat(row["purchase_date"])
            except ValueError:
                errors.append(
                    ValidationError(
                        row_num,
                        "NFA_ITEM",
                        "purchase_date",
                        "invalid_format",
                        "Date must be ISO format (YYYY-MM-DD)",
                        "error",
                    )
                )

        return errors

    def _validate_soft_gear_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name", "category", "purchase_date"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "SOFT_GEAR",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        return errors

    def _validate_attachment_row(
        self, row: dict, row_num: int
    ) -> list[ValidationError]:
        errors = []
        required = ["name", "category"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "ATTACHMENT",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        return errors

    def _validate_consumable_row(
        self, row: dict, row_num: int
    ) -> list[ValidationError]:
        errors = []
        required = ["name", "category", "unit"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "CONSUMABLE",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        return errors

    def _validate_reload_batch_row(
        self, row: dict, row_num: int
    ) -> list[ValidationError]:
        errors = []
        required = ["cartridge", "date_created"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "RELOAD_BATCH",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        return errors

    def _validate_borrower_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "BORROWER",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        return errors

    def _validate_loadout_row(self, row: dict, row_num: int) -> list[ValidationError]:
        errors = []
        required = ["name"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "LOADOUT",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        return errors

    def _validate_loadout_item_row(
        self, row: dict, row_num: int
    ) -> list[ValidationError]:
        errors = []
        required = ["loadout_id", "item_id", "item_type"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "LOADOUT_ITEM",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        return errors

    def _validate_loadout_consumable_row(
        self, row: dict, row_num: int
    ) -> list[ValidationError]:
        errors = []
        required = ["loadout_id", "consumable_id", "quantity"]

        for field in required:
            if field not in row or not row[field]:
                errors.append(
                    ValidationError(
                        row_num,
                        "LOADOUT_CONSUMABLE",
                        field,
                        "required",
                        f"'{field}' is required",
                        "error",
                    )
                )

        return errors

    def get_entity_import_order(self) -> list[str]:
        return [
            "BORROWERS",
            "FIREARMS",
            "NFA ITEMS",
            "SOFT GEAR",
            "ATTACHMENTS",
            "CONSUMABLES",
            "RELOAD BATCHES",
            "LOADOUTS",
            "LOADOUT ITEMS",
            "LOADOUT CONSUMABLES",
        ]

    def export_complete_csv(self, output_path: Path) -> None:
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            writer.writerow(["=== METADATA ==="])
            writer.writerow(["Export Date", "Version", "Export Type", "Dry Run"])
            writer.writerow(
                [datetime.now().strftime("%Y-%m-%d"), "1.0-refactor", "FULL", "FALSE"]
            )
            writer.writerow([])

            self._export_firearms(writer)
            self._export_nfa_items(writer)
            self._export_soft_gear(writer)
            self._export_attachments(writer)
            self._export_consumables(writer)
            self._export_reload_batches(writer)
            self._export_loadouts(writer)
            self._export_loadout_items(writer)
            self._export_loadout_consumables(writer)
            self._export_borrowers(writer)

    def _export_firearms(self, writer):
        writer.writerow(["=== FIREARMS ==="])
        writer.writerow(
            [
                "id",
                "name",
                "caliber",
                "serial_number",
                "purchase_date",
                "notes",
                "status",
                "is_nfa",
                "nfa_type",
                "tax_stamp_id",
                "form_type",
                "barrel_length",
                "trust_name",
                "transfer_status",
                "rounds_fired",
                "clean_interval_rounds",
                "oil_interval_days",
                "needs_maintenance",
                "maintenance_conditions",
            ]
        )
        for fw in self.firearm_repo.get_all():
            writer.writerow(
                [
                    fw.id,
                    fw.name,
                    fw.caliber,
                    fw.serial_number,
                    fw.purchase_date.strftime("%Y-%m-%d"),
                    fw.notes,
                    fw.status.value if hasattr(fw.status, "value") else str(fw.status),
                    1 if fw.is_nfa else 0,
                    fw.nfa_type.value if fw.nfa_type else "",
                    fw.tax_stamp_id,
                    fw.form_type,
                    fw.barrel_length,
                    fw.trust_name,
                    fw.transfer_status.value
                    if hasattr(fw.transfer_status, "value")
                    else str(fw.transfer_status),
                    fw.rounds_fired,
                    fw.clean_interval_rounds,
                    fw.oil_interval_days,
                    1 if fw.needs_maintenance else 0,
                    fw.maintenance_conditions,
                ]
            )
        writer.writerow([])

    def _export_nfa_items(self, writer):
        writer.writerow(["=== NFA ITEMS ==="])
        writer.writerow(
            [
                "id",
                "name",
                "nfa_type",
                "manufacturer",
                "serial_number",
                "tax_stamp_id",
                "caliber_bore",
                "purchase_date",
                "form_type",
                "trust_name",
                "notes",
                "status",
            ]
        )
        for item in self.gear_repo.get_all_nfa_items():
            writer.writerow(
                [
                    item.id,
                    item.name,
                    item.nfa_type.value
                    if hasattr(item.nfa_type, "value")
                    else str(item.nfa_type),
                    item.manufacturer,
                    item.serial_number,
                    item.tax_stamp_id,
                    item.caliber_bore,
                    item.purchase_date.strftime("%Y-%m-%d"),
                    item.form_type,
                    item.trust_name,
                    item.notes,
                    item.status.value
                    if hasattr(item.status, "value")
                    else str(item.status),
                ]
            )
        writer.writerow([])

    def _export_soft_gear(self, writer):
        writer.writerow(["=== SOFT GEAR ==="])
        writer.writerow(
            ["id", "name", "category", "brand", "purchase_date", "notes", "status"]
        )
        for gear in self.gear_repo.get_all_soft_gear():
            writer.writerow(
                [
                    gear.id,
                    gear.name,
                    gear.category,
                    gear.brand,
                    gear.purchase_date.strftime("%Y-%m-%d"),
                    gear.notes,
                    gear.status.value
                    if hasattr(gear.status, "value")
                    else str(gear.status),
                ]
            )
        writer.writerow([])

    def _export_attachments(self, writer):
        writer.writerow(["=== ATTACHMENTS ==="])
        writer.writerow(
            [
                "id",
                "name",
                "category",
                "brand",
                "model",
                "serial_number",
                "purchase_date",
                "mounted_on_firearm_id",
                "mount_position",
                "zero_distance_yards",
                "zero_notes",
                "notes",
            ]
        )
        for att in self.gear_repo.get_all_attachments():
            writer.writerow(
                [
                    att.id,
                    att.name,
                    att.category,
                    att.brand,
                    att.model,
                    att.serial_number,
                    att.purchase_date.strftime("%Y-%m-%d") if att.purchase_date else "",
                    att.mounted_on_firearm_id or "",
                    att.mount_position,
                    att.zero_distance_yards or "",
                    att.zero_notes,
                    att.notes,
                ]
            )
        writer.writerow([])

    def _export_consumables(self, writer):
        writer.writerow(["=== CONSUMABLES ==="])
        writer.writerow(
            ["id", "name", "category", "unit", "quantity", "min_quantity", "notes"]
        )
        for cons in self.consumable_repo.get_all():
            writer.writerow(
                [
                    cons.id,
                    cons.name,
                    cons.category,
                    cons.unit,
                    cons.quantity,
                    cons.min_quantity,
                    cons.notes,
                ]
            )
        writer.writerow([])

    def _export_reload_batches(self, writer):
        writer.writerow(["=== RELOAD BATCHES ==="])
        writer.writerow(
            [
                "id",
                "cartridge",
                "firearm_id",
                "date_created",
                "bullet_maker",
                "bullet_model",
                "bullet_weight_gr",
                "powder_name",
                "powder_charge_gr",
                "powder_lot",
                "primer_maker",
                "primer_type",
                "case_brand",
                "case_times_fired",
                "case_prep_notes",
                "coal_in",
                "crimp_style",
                "test_date",
                "avg_velocity",
                "es",
                "sd",
                "group_size_inches",
                "group_distance_yards",
                "intended_use",
                "status",
                "notes",
            ]
        )
        for batch in self.reload_repo.get_all():
            writer.writerow(
                [
                    batch.id,
                    batch.cartridge,
                    batch.firearm_id or "",
                    batch.date_created.strftime("%Y-%m-%d"),
                    batch.bullet_maker,
                    batch.bullet_model,
                    batch.bullet_weight_gr or "",
                    batch.powder_name,
                    batch.powder_charge_gr or "",
                    batch.powder_lot,
                    batch.primer_maker,
                    batch.primer_type,
                    batch.case_brand,
                    batch.case_times_fired or "",
                    batch.case_prep_notes,
                    batch.coal_in or "",
                    batch.crimp_style,
                    batch.test_date.strftime("%Y-%m-%d") if batch.test_date else "",
                    batch.avg_velocity or "",
                    batch.es or "",
                    batch.sd or "",
                    batch.group_size_inches or "",
                    batch.group_distance_yards or "",
                    batch.intended_use,
                    batch.status,
                    batch.notes,
                ]
            )
        writer.writerow([])

    def _export_loadouts(self, writer):
        writer.writerow(["=== LOADOUTS ==="])
        writer.writerow(["id", "name", "description", "created_date", "notes"])
        for lo in self.loadout_repo.get_all():
            writer.writerow(
                [
                    lo.id,
                    lo.name,
                    lo.description or "",
                    lo.created_date.strftime("%Y-%m-%d") if lo.created_date else "",
                    lo.notes or "",
                ]
            )
        writer.writerow([])

    def _export_loadout_items(self, writer):
        writer.writerow(["=== LOADOUT ITEMS ==="])
        writer.writerow(["id", "loadout_id", "item_id", "item_type", "notes"])
        for lo in self.loadout_repo.get_all():
            for item in self.loadout_repo.get_items(lo.id):
                writer.writerow(
                    [
                        item.id,
                        item.loadout_id,
                        item.item_id,
                        item.item_type,
                        item.notes,
                    ]
                )
        writer.writerow([])

    def _export_loadout_consumables(self, writer):
        writer.writerow(["=== LOADOUT CONSUMABLES ==="])
        writer.writerow(["id", "loadout_id", "consumable_id", "quantity", "notes"])
        for lo in self.loadout_repo.get_all():
            for lc in self.loadout_repo.get_consumables(lo.id):
                writer.writerow(
                    [lc.id, lc.loadout_id, lc.consumable_id, lc.quantity, lc.notes]
                )
        writer.writerow([])

    def _export_borrowers(self, writer):
        writer.writerow(["=== BORROWERS ==="])
        writer.writerow(["id", "name", "phone", "email", "notes"])
        for borrower in self.checkout_repo.get_all_borrowers():
            writer.writerow(
                [
                    borrower.id,
                    borrower.name,
                    borrower.phone or "",
                    borrower.email or "",
                    borrower.notes or "",
                ]
            )
        writer.writerow([])

    def preview_import(self, file_path: Path) -> ImportResult:
        try:
            parsed_data = self.parse_sectioned_csv(file_path)
            validation_errors = self.validate_csv_data(parsed_data)

            total_rows = sum(len(rows) for rows in parsed_data.values())
            entity_stats = {}
            for section_name, rows in parsed_data.items():
                entity_stats[section_name] = len(rows)

            critical_errors = [e for e in validation_errors if e.severity == "error"]

            return ImportResult(
                success=len(critical_errors) == 0,
                total_rows=total_rows,
                imported=0,
                skipped=0,
                overwritten=0,
                errors=[e.message for e in validation_errors if e.severity == "error"],
                warnings=[
                    e.message for e in validation_errors if e.severity == "warning"
                ],
                entity_stats=entity_stats,
            )

        except Exception as e:
            return ImportResult(
                success=False,
                total_rows=0,
                imported=0,
                skipped=0,
                overwritten=0,
                errors=[f"Preview failed: {str(e)}"],
                warnings=[],
                entity_stats={},
            )

    def import_complete_csv(
        self,
        file_path: Path,
        dry_run: bool = False,
        duplicate_callback: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
    ) -> ImportResult:
        result = ImportResult(
            success=False,
            total_rows=0,
            imported=0,
            skipped=0,
            overwritten=0,
            errors=[],
            warnings=[],
            entity_stats={},
        )

        try:
            parsed_data = self.parse_sectioned_csv(file_path)
            validation_errors = self.validate_csv_data(parsed_data)

            critical_errors = [e for e in validation_errors if e.severity == "error"]

            if critical_errors:
                result.errors.extend([e.message for e in critical_errors])
                result.total_rows = sum(len(rows) for rows in parsed_data.values())
                for section_name, rows in parsed_data.items():
                    result.entity_stats[section_name] = len(rows)
                return result

            if dry_run:
                result.total_rows = sum(len(rows) for rows in parsed_data.values())
                result.errors = [
                    e.message for e in validation_errors if e.severity == "error"
                ]
                result.warnings = [
                    e.message for e in validation_errors if e.severity == "warning"
                ]
                for section_name, rows in parsed_data.items():
                    result.entity_stats[section_name] = len(rows)
                result.success = True
                return result

            import_order = self.get_entity_import_order()
            total_entities = len(import_order)

            for entity_idx, entity_type in enumerate(import_order):
                if entity_type not in parsed_data:
                    continue

                rows = parsed_data[entity_type]
                if not rows:
                    result.entity_stats[entity_type] = 0
                    continue

                entity_result = self._import_entity_type(
                    entity_type=entity_type,
                    rows=rows,
                    duplicate_callback=duplicate_callback,
                    progress_callback=progress_callback,
                    current_progress=entity_idx * 100 // total_entities,
                )

                result.imported += entity_result["imported"]
                result.skipped += entity_result["skipped"]
                result.overwritten += entity_result["overwritten"]
                result.errors.extend(entity_result["errors"])
                result.warnings.extend(entity_result["warnings"])
                result.entity_stats[entity_type] = entity_result["total"]

            result.total_rows = sum(len(rows) for rows in parsed_data.values())
            result.success = len(result.errors) == 0 or result.imported > 0

            return result

        except Exception as e:
            result.errors.append(f"Import failed: {str(e)}")
            result.success = False
            return result

    def _import_entity_type(
        self,
        entity_type: str,
        rows: list[dict],
        duplicate_callback: Optional[Callable],
        progress_callback: Optional[Callable],
        current_progress: int,
    ) -> dict:
        result = {
            "imported": 0,
            "skipped": 0,
            "overwritten": 0,
            "errors": [],
            "warnings": [],
            "total": len(rows),
        }

        conn = None
        try:
            conn = self.db.connect()
            cursor = conn.cursor()

            for row_idx, row in enumerate(rows):
                try:
                    existing = self._check_entity_duplicate(entity_type, row)

                    if existing:
                        action = "skip"
                        if duplicate_callback:
                            action = duplicate_callback(entity_type, existing, row)

                        if action == "cancel":
                            raise Exception("Import cancelled by user")
                        elif action == "skip":
                            result["skipped"] += 1
                            continue
                        elif action == "overwrite":
                            self._update_entity(entity_type, existing, row, cursor)
                            result["overwritten"] += 1
                        elif action == "rename":
                            self._create_entity(entity_type, row, cursor, rename=True)
                            result["imported"] += 1
                    else:
                        self._create_entity(entity_type, row, cursor)
                        result["imported"] += 1

                    if progress_callback:
                        pct = current_progress + ((row_idx + 1) * 100 // len(rows))
                        progress_callback(
                            pct,
                            100,
                            entity_type.upper(),
                            f"Importing {entity_type} {row_idx + 1}/{len(rows)}",
                        )

                except ValueError as e:
                    result["errors"].append(str(e))
                    result["skipped"] += 1
                except Exception as e:
                    result["errors"].append(f"Row {row_idx + 1}: {str(e)}")
                    result["skipped"] += 1

            conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            result["errors"].append(f"Entity type {entity_type} failed: {str(e)}")
        finally:
            if conn:
                conn.close()

        return result

    def _detect_duplicate_firearm(self, serial_number: str) -> Optional[Firearm]:
        for fw in self.firearm_repo.get_all():
            if fw.serial_number == serial_number:
                return fw
        return None

    def _detect_duplicate_nfa_item(self, name: str) -> Optional[NFAItem]:
        for item in self.gear_repo.get_all_nfa_items():
            if item.name == name:
                return item
        return None

    def _detect_duplicate_soft_gear(self, name: str) -> Optional[SoftGear]:
        for gear in self.gear_repo.get_all_soft_gear():
            if gear.name == name:
                return gear
        return None

    def _detect_duplicate_attachment(self, name: str) -> Optional[Attachment]:
        for att in self.gear_repo.get_all_attachments():
            if att.name == name:
                return att
        return None

    def _detect_duplicate_consumable(self, name: str) -> Optional[Consumable]:
        for cons in self.consumable_repo.get_all():
            if cons.name == name:
                return cons
        return None

    def _detect_duplicate_reload_batch(
        self, cartridge: str, bullet_model: str
    ) -> Optional[ReloadBatch]:
        for batch in self.reload_repo.get_all():
            if batch.cartridge == cartridge and batch.bullet_model == bullet_model:
                return batch
        return None

    def _detect_duplicate_borrower(self, name: str) -> Optional[Borrower]:
        for borrower in self.checkout_repo.get_all_borrowers():
            if borrower.name == name:
                return borrower
        return None

    def _detect_duplicate_loadout(self, name: str) -> Optional[Loadout]:
        for lo in self.loadout_repo.get_all():
            if lo.name == name:
                return lo
        return None

    def _detect_duplicate_firearm(self, serial_number: str) -> Firearm | None:
        for fw in self.firearm_repo.get_all():
            if fw.serial_number == serial_number:
                return fw
        return None

    def _detect_duplicate_nfa_item(self, name: str) -> NFAItem | None:
        for item in self.gear_repo.get_all_nfa_items():
            if item.name == name:
                return item
        return None

    def _detect_duplicate_soft_gear(self, name: str) -> SoftGear | None:
        for gear in self.gear_repo.get_all_soft_gear():
            if gear.name == name:
                return gear
        return None

    def _detect_duplicate_attachment(self, name: str) -> Attachment | None:
        for att in self.gear_repo.get_all_attachments():
            if att.name == name:
                return att
        return None

    def _detect_duplicate_consumable(self, name: str) -> Consumable | None:
        for cons in self.consumable_repo.get_all():
            if cons.name == name:
                return cons
        return None

    def _detect_duplicate_reload_batch(
        self, cartridge: str, bullet_model: str
    ) -> ReloadBatch | None:
        for batch in self.reload_repo.get_all():
            if batch.cartridge == cartridge and batch.bullet_model == bullet_model:
                return batch
        return None

    def _detect_duplicate_borrower(self, name: str) -> Borrower | None:
        for borrower in self.checkout_repo.get_all_borrowers():
            if borrower.name == name:
                return borrower
        return None

    def _detect_duplicate_loadout(self, name: str) -> Loadout | None:
        for lo in self.loadout_repo.get_all():
            if lo.name == name:
                return lo
        return None

    def _create_entity(
        self, entity_type: str, row: dict, cursor, rename: bool = False
    ) -> str:
        import uuid

        entity_type_upper = entity_type.upper().replace(" ", "_")
        entity_id = row.get("id", str(uuid.uuid4()))

        if rename:
            entity_id = str(uuid.uuid4())

        if entity_type_upper == "FIREARMS":
            self._create_firearm(row, cursor, entity_id)
        elif entity_type_upper == "NFA_ITEMS":
            self._create_nfa_item(row, cursor, entity_id)
        elif entity_type_upper == "SOFT_GEAR":
            self._create_soft_gear(row, cursor, entity_id)
        elif entity_type_upper == "ATTACHMENTS":
            self._create_attachment(row, cursor, entity_id)
        elif entity_type_upper == "CONSUMABLES":
            self._create_consumable(row, cursor, entity_id)
        elif entity_type_upper == "RELOAD_BATCHES":
            self._create_reload_batch(row, cursor, entity_id)
        elif entity_type_upper == "BORROWERS":
            self._create_borrower(row, cursor, entity_id)
        elif entity_type_upper == "LOADOUTS":
            self._create_loadout(row, cursor, entity_id)
        elif entity_type_upper == "LOADOUT_ITEMS":
            self._create_loadout_item(row, cursor, entity_id)
        elif entity_type_upper == "LOADOUT_CONSUMABLES":
            self._create_loadout_consumable(row, cursor, entity_id)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")

        return entity_id

    def _create_firearm(self, row: dict, cursor, entity_id: str) -> None:
        name = row["name"]
        caliber = row["caliber"]
        serial_number = row.get("serial_number", "")
        purchase_date = self._parse_date_str(row["purchase_date"])
        notes = row.get("notes", "")
        status = row.get("status", "AVAILABLE")
        is_nfa = row.get("is_nfa", "FALSE").upper() in ["TRUE", "1"]
        nfa_type = None
        if is_nfa:
            nfa_type_str = row.get("nfa_type", "")
            if nfa_type_str:
                nfa_type = NFAFirearmType(nfa_type_str)
        tax_stamp_id = row.get("tax_stamp_id", "")
        form_type = row.get("form_type", "")
        barrel_length = row.get("barrel_length", "")
        trust_name = row.get("trust_name", "")
        transfer_status = TransferStatus(row.get("transfer_status", "OWNED"))
        rounds_fired = self._parse_int_str(row.get("rounds_fired", "0")) or 0
        clean_interval_rounds = (
            self._parse_int_str(row.get("clean_interval_rounds", "500")) or 500
        )
        oil_interval_days = (
            self._parse_int_str(row.get("oil_interval_days", "90")) or 90
        )
        needs_maintenance = row.get("needs_maintenance", "FALSE").upper() in [
            "TRUE",
            "1",
        ]
        maintenance_conditions = row.get("maintenance_conditions", "")

        firearm = Firearm(
            id=entity_id,
            name=name,
            caliber=caliber,
            serial_number=serial_number,
            purchase_date=purchase_date,
            notes=notes,
            status=status,
            is_nfa=is_nfa,
            nfa_type=nfa_type,
            tax_stamp_id=tax_stamp_id,
            form_type=form_type,
            barrel_length=barrel_length,
            trust_name=trust_name,
            transfer_status=transfer_status,
            rounds_fired=rounds_fired,
            clean_interval_rounds=clean_interval_rounds,
            oil_interval_days=oil_interval_days,
            needs_maintenance=needs_maintenance,
            maintenance_conditions=maintenance_conditions,
        )

        self.firearm_repo.add(firearm)

    def _create_nfa_item(self, row: dict, cursor, entity_id: str) -> None:
        name = row["name"]
        nfa_type = NFAItemType(row["nfa_type"])
        manufacturer = row.get("manufacturer", "")
        serial_number = row.get("serial_number", "")
        tax_stamp_id = row["tax_stamp_id"]
        caliber_bore = row.get("caliber_bore", "")
        purchase_date = self._parse_date_str(row["purchase_date"])
        form_type = row.get("form_type", "")
        trust_name = row.get("trust_name", "")
        notes = row.get("notes", "")
        status = CheckoutStatus(row.get("status", "AVAILABLE"))

        item = NFAItem(
            id=entity_id,
            name=name,
            nfa_type=nfa_type,
            manufacturer=manufacturer,
            serial_number=serial_number,
            tax_stamp_id=tax_stamp_id,
            caliber_bore=caliber_bore,
            purchase_date=purchase_date,
            form_type=form_type,
            trust_name=trust_name,
            notes=notes,
            status=status,
        )

        self.gear_repo.add_nfa_item(item)

    def _create_soft_gear(self, row: dict, cursor, entity_id: str) -> None:
        name = row["name"]
        category = row["category"]
        brand = row.get("brand", "")
        purchase_date = self._parse_date_str(row["purchase_date"])
        notes = row.get("notes", "")
        status = CheckoutStatus(row.get("status", "AVAILABLE"))

        gear = SoftGear(
            id=entity_id,
            name=name,
            category=category,
            brand=brand,
            purchase_date=purchase_date,
            notes=notes,
            status=status,
        )

        self.gear_repo.add_soft_gear(gear)

    def _create_attachment(self, row: dict, cursor, entity_id: str) -> None:
        name = row["name"]
        category = row["category"]
        brand = row.get("brand", "")
        model = row.get("model", "")
        serial_number = row.get("serial_number", "")
        purchase_date = self._parse_date_str(row.get("purchase_date", ""))
        mounted_on_firearm_id = row.get("mounted_on_firearm_id") or None
        mount_position = row.get("mount_position", "")
        zero_distance_yards = self._parse_int_str(row.get("zero_distance_yards", ""))
        zero_notes = row.get("zero_notes", "")
        notes = row.get("notes", "")

        attachment = Attachment(
            id=entity_id,
            name=name,
            category=category,
            brand=brand,
            model=model,
            serial_number=serial_number,
            purchase_date=purchase_date if purchase_date else None,
            mounted_on_firearm_id=mounted_on_firearm_id,
            mount_position=mount_position,
            zero_distance_yards=zero_distance_yards if zero_distance_yards else None,
            zero_notes=zero_notes,
            notes=notes,
        )

        self.gear_repo.add_attachment(attachment)

    def _create_consumable(self, row: dict, cursor, entity_id: str) -> None:
        name = row["name"]
        category = row["category"]
        unit = row["unit"]
        quantity = self._parse_int_str(row.get("quantity", "0"))
        min_quantity = self._parse_int_str(row.get("min_quantity", "0"))
        notes = row.get("notes", "")

        consumable = Consumable(
            id=entity_id,
            name=name,
            category=category,
            unit=unit,
            quantity=quantity,
            min_quantity=min_quantity,
            notes=notes,
        )

        self.consumable_repo.add(consumable)

    def _create_reload_batch(self, row: dict, cursor, entity_id: str) -> None:
        cartridge = row["cartridge"]
        firearm_id = row.get("firearm_id") or None
        date_created = self._parse_date_str(row["date_created"])
        bullet_maker = row.get("bullet_maker", "")
        bullet_model = row.get("bullet_model", "")
        bullet_weight_gr = self._parse_int_str(row.get("bullet_weight_gr", ""))
        powder_name = row.get("powder_name", "")
        powder_charge_gr = self._parse_float_str(row.get("powder_charge_gr", ""))
        powder_lot = row.get("powder_lot", "")
        primer_maker = row.get("primer_maker", "")
        primer_type = row.get("primer_type", "")
        case_brand = row.get("case_brand", "")
        case_times_fired = self._parse_int_str(row.get("case_times_fired", ""))
        case_prep_notes = row.get("case_prep_notes", "")
        coal_in = self._parse_float_str(row.get("coal_in", ""))
        crimp_style = row.get("crimp_style", "")
        test_date = self._parse_date_str(row.get("test_date", ""))
        avg_velocity = self._parse_int_str(row.get("avg_velocity", ""))
        es = self._parse_int_str(row.get("es", ""))
        sd = self._parse_int_str(row.get("sd", ""))
        group_size_inches = self._parse_float_str(row.get("group_size_inches", ""))
        group_distance_yards = self._parse_int_str(row.get("group_distance_yards", ""))
        intended_use = row.get("intended_use", "")
        status = row.get("status", "WORKUP")
        notes = row.get("notes", "")

        batch = ReloadBatch(
            id=entity_id,
            cartridge=cartridge,
            firearm_id=firearm_id,
            date_created=date_created,
            bullet_maker=bullet_maker,
            bullet_model=bullet_model,
            bullet_weight_gr=bullet_weight_gr,
            powder_name=powder_name,
            powder_charge_gr=powder_charge_gr,
            powder_lot=powder_lot,
            primer_maker=primer_maker,
            primer_type=primer_type,
            case_brand=case_brand,
            case_times_fired=case_times_fired,
            case_prep_notes=case_prep_notes,
            coal_in=coal_in,
            crimp_style=crimp_style,
            test_date=test_date,
            avg_velocity=avg_velocity,
            es=es,
            sd=sd,
            group_size_inches=group_size_inches,
            group_distance_yards=group_distance_yards,
            intended_use=intended_use,
            status=status,
            notes=notes,
        )

        self.reload_repo.add_batch(batch)

    def _create_borrower(self, row: dict, cursor, entity_id: str) -> None:
        name = row["name"]
        phone = row.get("phone", "")
        email = row.get("email", "")
        notes = row.get("notes", "")

        borrower = Borrower(
            id=entity_id,
            name=name,
            phone=phone,
            email=email,
            notes=notes,
        )

        self.checkout_repo.add_borrower(borrower)

    def _create_loadout(self, row: dict, cursor, entity_id: str) -> None:
        name = row["name"]
        description = row.get("description", "")
        created_date = self._parse_date_str(row.get("created_date", ""))
        notes = row.get("notes", "")

        loadout = Loadout(
            id=entity_id,
            name=name,
            description=description,
            created_date=created_date if created_date else datetime.now(),
            notes=notes,
        )

        self.loadout_repo.create(loadout)

    def _create_loadout_item(self, row: dict, cursor, entity_id: str) -> None:
        loadout_id = row["loadout_id"]
        item_id = row["item_id"]
        item_type = row["item_type"]
        notes = row.get("notes", "")

        item = LoadoutItem(
            id=entity_id,
            loadout_id=loadout_id,
            item_id=item_id,
            item_type=item_type,
            notes=notes,
        )

        self.loadout_repo.add_item(item)

    def _create_loadout_consumable(self, row: dict, cursor, entity_id: str) -> None:
        loadout_id = row["loadout_id"]
        consumable_id = row["consumable_id"]
        quantity = self._parse_int_str(row.get("quantity", "0"))
        notes = row.get("notes", "")

        cons = LoadoutConsumable(
            id=entity_id,
            loadout_id=loadout_id,
            consumable_id=consumable_id,
            quantity=quantity,
            notes=notes,
        )

        self.loadout_repo.add_consumable(cons)

    def _update_entity(
        self, entity_type: str, existing: object, row: dict, cursor
    ) -> None:
        entity_type_upper = entity_type.upper().replace(" ", "_")

        if entity_type_upper == "FIREARMS":
            self._update_firearm(existing, row, cursor)
        elif entity_type_upper == "NFA_ITEMS":
            self._update_nfa_item(existing, row, cursor)
        elif entity_type_upper == "SOFT_GEAR":
            self._update_soft_gear(existing, row, cursor)
        elif entity_type_upper == "ATTACHMENTS":
            self._update_attachment(existing, row, cursor)
        elif entity_type_upper == "CONSUMABLES":
            self._update_consumable(existing, row, cursor)
        elif entity_type_upper == "RELOAD_BATCHES":
            self._update_reload_batch(existing, row, cursor)
        elif entity_type_upper == "BORROWERS":
            self._update_borrower(existing, row, cursor)
        elif entity_type_upper == "LOADOUTS":
            self._update_loadout(existing, row, cursor)

    def _update_firearm(self, existing: Firearm, row: dict, cursor) -> None:
        name = row.get("name", existing.name)
        caliber = row.get("caliber", existing.caliber)
        serial_number = row.get("serial_number", existing.serial_number)
        purchase_date = self._parse_date_str(row.get("purchase_date", ""))
        notes = row.get("notes", existing.notes)
        status = CheckoutStatus(
            row.get(
                "status",
                existing.status.value
                if hasattr(existing.status, "value")
                else str(existing.status),
            )
        )
        is_nfa = row.get("is_nfa", str(existing.is_nfa)).upper() in ["TRUE", "1"]
        nfa_type = existing.nfa_type
        if is_nfa and row.get("nfa_type"):
            nfa_type = NFAFirearmType(row["nfa_type"])
        tax_stamp_id = row.get("tax_stamp_id", existing.tax_stamp_id)
        form_type = row.get("form_type", existing.form_type)
        barrel_length = row.get("barrel_length", existing.barrel_length)
        trust_name = row.get("trust_name", existing.trust_name)
        transfer_status = TransferStatus(
            row.get(
                "transfer_status",
                existing.transfer_status.value
                if hasattr(existing.transfer_status, "value")
                else str(existing.transfer_status),
            )
        )
        rounds_fired = self._parse_int_str(
            row.get("rounds_fired", str(existing.rounds_fired))
        )
        clean_interval_rounds = self._parse_int_str(
            row.get("clean_interval_rounds", str(existing.clean_interval_rounds))
        )
        oil_interval_days = self._parse_int_str(
            row.get("oil_interval_days", str(existing.oil_interval_days))
        )
        needs_maintenance = row.get(
            "needs_maintenance", str(existing.needs_maintenance)
        ).upper() in ["TRUE", "1"]
        maintenance_conditions = row.get(
            "maintenance_conditions", existing.maintenance_conditions
        )

        firearm = Firearm(
            id=existing.id,
            name=name,
            caliber=caliber,
            serial_number=serial_number,
            purchase_date=purchase_date if purchase_date else existing.purchase_date,
            notes=notes,
            status=status,
            is_nfa=is_nfa,
            nfa_type=nfa_type,
            tax_stamp_id=tax_stamp_id,
            form_type=form_type,
            barrel_length=barrel_length,
            trust_name=trust_name,
            transfer_status=transfer_status,
            rounds_fired=rounds_fired,
            clean_interval_rounds=clean_interval_rounds,
            oil_interval_days=oil_interval_days,
            needs_maintenance=needs_maintenance,
            maintenance_conditions=maintenance_conditions,
        )

        self.firearm_repo.add(firearm)

    def _update_nfa_item(self, existing: NFAItem, row: dict, cursor) -> None:
        item = NFAItem(
            id=existing.id,
            name=row.get("name", existing.name),
            nfa_type=NFAItemType(
                row.get(
                    "nfa_type",
                    existing.nfa_type.value
                    if hasattr(existing.nfa_type, "value")
                    else str(existing.nfa_type),
                )
            ),
            manufacturer=row.get("manufacturer", existing.manufacturer),
            serial_number=row.get("serial_number", existing.serial_number),
            tax_stamp_id=row.get("tax_stamp_id", existing.tax_stamp_id),
            caliber_bore=row.get("caliber_bore", existing.caliber_bore),
            purchase_date=self._parse_date_str(row.get("purchase_date", ""))
            or existing.purchase_date,
            form_type=row.get("form_type", existing.form_type),
            trust_name=row.get("trust_name", existing.trust_name),
            notes=row.get("notes", existing.notes),
            status=CheckoutStatus(
                row.get(
                    "status",
                    existing.status.value
                    if hasattr(existing.status, "value")
                    else str(existing.status),
                )
            ),
        )
        self.gear_repo.add_nfa_item(item)

    def _update_soft_gear(self, existing: SoftGear, row: dict, cursor) -> None:
        gear = SoftGear(
            id=existing.id,
            name=row.get("name", existing.name),
            category=row.get("category", existing.category),
            brand=row.get("brand", existing.brand),
            purchase_date=self._parse_date_str(row.get("purchase_date", ""))
            or existing.purchase_date,
            notes=row.get("notes", existing.notes),
            status=CheckoutStatus(
                row.get(
                    "status",
                    existing.status.value
                    if hasattr(existing.status, "value")
                    else str(existing.status),
                )
            ),
        )
        self.gear_repo.add_soft_gear(gear)

    def _update_attachment(self, existing: Attachment, row: dict, cursor) -> None:
        attachment = Attachment(
            id=existing.id,
            name=row.get("name", existing.name),
            category=row.get("category", existing.category),
            brand=row.get("brand", existing.brand),
            model=row.get("model", existing.model),
            serial_number=row.get("serial_number", existing.serial_number),
            purchase_date=self._parse_date_str(row.get("purchase_date", ""))
            or existing.purchase_date,
            mounted_on_firearm_id=row.get("mounted_on_firearm_id")
            or existing.mounted_on_firearm_id,
            mount_position=row.get("mount_position", existing.mount_position),
            zero_distance_yards=self._parse_int_str(
                row.get("zero_distance_yards", str(existing.zero_distance_yards))
            )
            if existing.zero_distance_yards
            else None,
            zero_notes=row.get("zero_notes", existing.zero_notes),
            notes=row.get("notes", existing.notes),
        )
        self.gear_repo.add_attachment(attachment)

    def _update_consumable(self, existing: Consumable, row: dict, cursor) -> None:
        consumable = Consumable(
            id=existing.id,
            name=row.get("name", existing.name),
            category=row.get("category", existing.category),
            unit=row.get("unit", existing.unit),
            quantity=self._parse_int_str(row.get("quantity", str(existing.quantity))),
            min_quantity=self._parse_int_str(
                row.get("min_quantity", str(existing.min_quantity))
            ),
            notes=row.get("notes", existing.notes),
        )
        self.consumable_repo.add(consumable)

    def _update_reload_batch(self, existing: ReloadBatch, row: dict, cursor) -> None:
        batch = ReloadBatch(
            id=existing.id,
            cartridge=row.get("cartridge", existing.cartridge),
            firearm_id=row.get("firearm_id") or existing.firearm_id,
            date_created=self._parse_date_str(row.get("date_created", ""))
            or existing.date_created,
            bullet_maker=row.get("bullet_maker", existing.bullet_maker),
            bullet_model=row.get("bullet_model", existing.bullet_model),
            bullet_weight_gr=self._parse_int_str(
                row.get("bullet_weight_gr", str(existing.bullet_weight_gr))
            )
            if existing.bullet_weight_gr
            else None,
            powder_name=row.get("powder_name", existing.powder_name),
            powder_charge_gr=self._parse_float_str(
                row.get("powder_charge_gr", str(existing.powder_charge_gr))
            )
            if existing.powder_charge_gr
            else None,
            powder_lot=row.get("powder_lot", existing.powder_lot),
            primer_maker=row.get("primer_maker", existing.primer_maker),
            primer_type=row.get("primer_type", existing.primer_type),
            case_brand=row.get("case_brand", existing.case_brand),
            case_times_fired=self._parse_int_str(
                row.get("case_times_fired", str(existing.case_times_fired))
            )
            if existing.case_times_fired
            else None,
            case_prep_notes=row.get("case_prep_notes", existing.case_prep_notes),
            coal_in=self._parse_float_str(row.get("coal_in", str(existing.coal_in)))
            if existing.coal_in
            else None,
            crimp_style=row.get("crimp_style", existing.crimp_style),
            test_date=self._parse_date_str(row.get("test_date", ""))
            or existing.test_date,
            avg_velocity=self._parse_int_str(
                row.get("avg_velocity", str(existing.avg_velocity))
            )
            if existing.avg_velocity
            else None,
            es=self._parse_int_str(row.get("es", str(existing.es)))
            if existing.es
            else None,
            sd=self._parse_int_str(row.get("sd", str(existing.sd)))
            if existing.sd
            else None,
            group_size_inches=self._parse_float_str(
                row.get("group_size_inches", str(existing.group_size_inches))
            )
            if existing.group_size_inches
            else None,
            group_distance_yards=self._parse_int_str(
                row.get("group_distance_yards", str(existing.group_distance_yards))
            )
            if existing.group_distance_yards
            else None,
            intended_use=row.get("intended_use", existing.intended_use),
            status=row.get("status", existing.status),
            notes=row.get("notes", existing.notes),
        )
        self.reload_repo.add_batch(batch)

    def _update_borrower(self, existing: Borrower, row: dict, cursor) -> None:
        borrower = Borrower(
            id=existing.id,
            name=row.get("name", existing.name),
            phone=row.get("phone", existing.phone),
            email=row.get("email", existing.email),
            notes=row.get("notes", existing.notes),
        )
        self.checkout_repo.add_borrower(borrower)

    def _update_loadout(self, existing: Loadout, row: dict, cursor) -> None:
        loadout = Loadout(
            id=existing.id,
            name=row.get("name", existing.name),
            description=row.get("description", existing.description),
            created_date=self._parse_date_str(row.get("created_date", ""))
            or existing.created_date,
            notes=row.get("notes", existing.notes),
        )
        self.loadout_repo.update(loadout)

    def _parse_date_str(self, date_str: str) -> datetime | None:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None

    def _parse_int_str(self, val: str) -> int | None:
        if not val:
            return None
        try:
            return int(val)
        except ValueError:
            return None

    def _parse_float_str(self, val: str) -> float | None:
        if not val:
            return None
        try:
            return float(val)
        except ValueError:
            return None

    def generate_csv_template(
        self, output_path: Path, entity_type: str | None = None
    ) -> None:
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            if entity_type is None:
                self._write_full_template(writer)
            else:
                self._write_single_template(writer, entity_type)

    def _write_full_template(self, writer) -> None:
        writer.writerow(["=== FIREARMS TEMPLATE ==="])
        writer.writerow(
            [
                "id",
                "name",
                "caliber",
                "serial_number",
                "purchase_date",
                "notes",
                "status",
                "is_nfa",
                "nfa_type",
                "tax_stamp_id",
                "form_type",
                "barrel_length",
                "trust_name",
                "transfer_status",
                "rounds_fired",
                "clean_interval_rounds",
                "oil_interval_days",
                "needs_maintenance",
                "maintenance_conditions",
            ]
        )
        writer.writerow([])
        writer.writerow(["=== NFA ITEMS TEMPLATE ==="])
        writer.writerow(
            [
                "id",
                "name",
                "nfa_type",
                "manufacturer",
                "serial_number",
                "tax_stamp_id",
                "caliber_bore",
                "purchase_date",
                "form_type",
                "trust_name",
                "notes",
                "status",
            ]
        )
        writer.writerow([])
        writer.writerow(["=== SOFT GEAR TEMPLATE ==="])
        writer.writerow(
            ["id", "name", "category", "brand", "purchase_date", "notes", "status"]
        )
        writer.writerow([])
        writer.writerow(["=== ATTACHMENTS TEMPLATE ==="])
        writer.writerow(
            [
                "id",
                "name",
                "category",
                "brand",
                "model",
                "serial_number",
                "purchase_date",
                "mounted_on_firearm_id",
                "mount_position",
                "zero_distance_yards",
                "zero_notes",
                "notes",
            ]
        )
        writer.writerow([])
        writer.writerow(["=== CONSUMABLES TEMPLATE ==="])
        writer.writerow(
            ["id", "name", "category", "unit", "quantity", "min_quantity", "notes"]
        )
        writer.writerow([])
        writer.writerow(["=== RELOAD BATCHES TEMPLATE ==="])
        writer.writerow(
            [
                "id",
                "cartridge",
                "firearm_id",
                "date_created",
                "bullet_maker",
                "bullet_model",
                "bullet_weight_gr",
                "powder_name",
                "powder_charge_gr",
                "powder_lot",
                "primer_maker",
                "primer_type",
                "case_brand",
                "case_times_fired",
                "case_prep_notes",
                "coal_in",
                "crimp_style",
                "test_date",
                "avg_velocity",
                "es",
                "sd",
                "group_size_inches",
                "group_distance_yards",
                "intended_use",
                "status",
                "notes",
            ]
        )
        writer.writerow([])
        writer.writerow(["=== LOADOUTS TEMPLATE ==="])
        writer.writerow(["id", "name", "description", "created_date", "notes"])
        writer.writerow([])
        writer.writerow(["=== LOADOUT ITEMS TEMPLATE ==="])
        writer.writerow(["id", "loadout_id", "item_id", "item_type", "notes"])
        writer.writerow([])
        writer.writerow(["=== LOADOUT CONSUMABLES TEMPLATE ==="])
        writer.writerow(["id", "loadout_id", "consumable_id", "quantity", "notes"])
        writer.writerow([])
        writer.writerow(["=== BORROWERS TEMPLATE ==="])
        writer.writerow(["id", "name", "phone", "email", "notes"])
        writer.writerow([])

    def _write_single_template(self, writer, entity_type: str) -> None:
        if entity_type == "firearms":
            writer.writerow(
                [
                    "id",
                    "name",
                    "caliber",
                    "serial_number",
                    "purchase_date",
                    "notes",
                    "status",
                    "is_nfa",
                    "nfa_type",
                    "tax_stamp_id",
                    "form_type",
                    "barrel_length",
                    "trust_name",
                    "transfer_status",
                    "rounds_fired",
                    "clean_interval_rounds",
                    "oil_interval_days",
                    "needs_maintenance",
                    "maintenance_conditions",
                ]
            )
        elif entity_type == "nfa_items":
            writer.writerow(
                [
                    "id",
                    "name",
                    "nfa_type",
                    "manufacturer",
                    "serial_number",
                    "tax_stamp_id",
                    "caliber_bore",
                    "purchase_date",
                    "form_type",
                    "trust_name",
                    "notes",
                    "status",
                ]
            )
        elif entity_type == "soft_gear":
            writer.writerow(
                ["id", "name", "category", "brand", "purchase_date", "notes", "status"]
            )
        elif entity_type == "attachments":
            writer.writerow(
                [
                    "id",
                    "name",
                    "category",
                    "brand",
                    "model",
                    "serial_number",
                    "purchase_date",
                    "mounted_on_firearm_id",
                    "mount_position",
                    "zero_distance_yards",
                    "zero_notes",
                    "notes",
                ]
            )
        elif entity_type == "consumables":
            writer.writerow(
                ["id", "name", "category", "unit", "quantity", "min_quantity", "notes"]
            )
        elif entity_type == "reload_batches":
            writer.writerow(
                [
                    "id",
                    "cartridge",
                    "firearm_id",
                    "date_created",
                    "bullet_maker",
                    "bullet_model",
                    "bullet_weight_gr",
                    "powder_name",
                    "powder_charge_gr",
                    "powder_lot",
                    "primer_maker",
                    "primer_type",
                    "case_brand",
                    "case_times_fired",
                    "case_prep_notes",
                    "coal_in",
                    "crimp_style",
                    "test_date",
                    "avg_velocity",
                    "es",
                    "sd",
                    "group_size_inches",
                    "group_distance_yards",
                    "intended_use",
                    "status",
                    "notes",
                ]
            )
        elif entity_type == "loadouts":
            writer.writerow(["id", "name", "description", "created_date", "notes"])
        elif entity_type == "borrowers":
            writer.writerow(["id", "name", "phone", "email", "notes"])
