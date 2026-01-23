import sys
import uuid
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QDateEdit,
    QTabWidget,
    QHeaderView,
    QMessageBox,
    QFormLayout,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QFileDialog,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

from src.repository import (
    Database,
    FirearmRepository,
    GearRepository,
    ConsumableRepository,
    CheckoutRepository,
    LoadoutRepository,
    ReloadRepository,
    TransferRepository,
    MaintenanceRepository,
)
from src.services.import_export import ImportExportService
from src.models import (
    Firearm,
    SoftGear,
    Consumable,
    MaintenanceLog,
    Borrower,
    NFAItem,
    GearCategory,
    MaintenanceType,
    CheckoutStatus,
    NFAItemType,
    NFAFirearmType,
    TransferStatus,
    Transfer,
    Attachment,
    ReloadBatch,
    Loadout,
    LoadoutItem,
    LoadoutConsumable,
    LoadoutCheckout,
    Checkout,
)


class GearTrackerMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.firearm_repo = FirearmRepository(self.db)
        self.gear_repo = GearRepository(self.db)
        self.consumable_repo = ConsumableRepository(self.db)
        self.checkout_repo = CheckoutRepository(self.db)
        self.loadout_repo = LoadoutRepository(self.db)
        self.reload_repo = ReloadRepository(self.db)
        self.transfer_repo = TransferRepository(self.db)
        self.maint_repo = MaintenanceRepository(self.db)
        self.import_export_svc = ImportExportService(self.db)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Gear Tracker")
        self.setGeometry(100, 100, 1200, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self.create_firearms_tab(), "🔫 Firearms")
        self.tabs.addTab(self.create_attachments_tab(), "🔧 Attachments")
        self.tabs.addTab(self.create_reloading_tab(), "🧪 Reloading")
        self.tabs.addTab(self.create_soft_gear_tab(), "🎒 Soft Gear")
        self.tabs.addTab(self.create_consumables_tab(), "📦 Consumables")
        self.tabs.addTab(self.create_loadouts_tab(), "🎒 Loadouts")
        self.tabs.addTab(self.create_checkouts_tab(), "📋 Checkouts")
        self.tabs.addTab(self.create_borrowers_tab(), "👥 Borrowers")
        self.tabs.addTab(self.create_nfa_items_tab(), "🔇 NFA Items")
        self.tabs.addTab(self.create_transfers_tab(), "📋 Transfers")
        self.tabs.addTab(self.create_import_export_tab(), "📁 Import/Export")

        self.refresh_all()

    def refresh_all(self):
        self.refresh_firearms()
        self.refresh_attachments()
        self.refresh_reloading()
        self.refresh_soft_gear()
        self.refresh_consumables()
        self.refresh_loadouts()
        self.refresh_checkouts()
        self.refresh_borrowers()
        self.refresh_nfa_items()
        self.refresh_transfers()

    # ============== FIREARMS TAB ==============

    def create_firearms_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.firearm_table = QTableWidget()
        self.firearm_table.setColumnCount(7)
        self.firearm_table.setHorizontalHeaderLabels(
            ["Name", "Caliber", "Serial", "Status", "Rounds", "Last Cleaned", "Notes"]
        )
        self.firearm_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.firearm_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Firearm")
        add_btn.clicked.connect(self.open_add_firearm_dialog)
        btn_layout.addWidget(add_btn)

        log_btn = QPushButton("Log Maintenance")
        log_btn.clicked.connect(lambda: self.open_log_dialog(GearCategory.FIREARM))
        btn_layout.addWidget(log_btn)

        history_btn = QPushButton("View History")
        history_btn.clicked.connect(
            lambda: self.view_item_history(GearCategory.FIREARM)
        )
        btn_layout.addWidget(history_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_selected_firearm)
        btn_layout.addWidget(delete_btn)

        transfer_btn = QPushButton("Transfer/Sell")
        transfer_btn.setStyleSheet("background-color: #6B6B20;")
        transfer_btn.clicked.connect(self.open_transfer_dialog)
        btn_layout.addWidget(transfer_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_firearms(self):
        self.firearm_table.setRowCount(0)
        firearms = self.firearm_repo.get_all()

        for i, fw in enumerate(firearms):
            self.firearm_table.insertRow(i)
            self.firearm_table.setItem(i, 0, QTableWidgetItem(fw.name))
            self.firearm_table.setItem(i, 1, QTableWidgetItem(fw.caliber))
            self.firearm_table.setItem(i, 2, QTableWidgetItem(fw.serial_number))

            status = fw.status.value if hasattr(fw.status, "value") else str(fw.status)
            status_item = QTableWidgetItem(status)

            if status == "CHECKED_OUT":
                status_item.setBackground(QColor(255, 200, 200))
            if fw.needs_maintenance:
                status_item.setBackground(QColor(255, 100, 100))
                status_item.setForeground(QColor(255, 255, 255))

            self.firearm_table.setItem(i, 3, status_item)

            rounds_item = QTableWidgetItem(str(fw.rounds_fired))
            if fw.needs_maintenance:
                rounds_item.setBackground(QColor(255, 150, 150))
            self.firearm_table.setItem(i, 4, rounds_item)

            last_clean = self.maint_repo.get_last_cleaning_date(fw.id)
            clean_text = last_clean.strftime("%Y-%m-%d") if last_clean else "Never"
            self.firearm_table.setItem(i, 5, QTableWidgetItem(clean_text))

            self.firearm_table.setItem(i, 6, QTableWidgetItem(fw.notes))

    def delete_selected_firearm(self):
        row = self.firearm_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a firearm to delete")
            return

        firearms = self.firearm_repo.get_all()
        selected = firearms[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete '{selected.name}'?\n\nThis will also delete all maintenance logs and checkout history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.firearm_repo.delete(selected.id)
            self.refresh_firearms()
            QMessageBox.information(
                self, "Deleted", f"'{selected.name}' has been deleted."
            )

    def open_add_firearm_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Firearm")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit()
        layout.addRow("Name:", name_input)

        caliber_input = QLineEdit()
        layout.addRow("Caliber:", caliber_input)

        serial_input = QLineEdit()
        layout.addRow("Serial #:", serial_input)

        clean_interval_spin = QSpinBox()
        clean_interval_spin.setRange(0, 10000)
        clean_interval_spin.setValue(500)
        clean_interval_spin.setSuffix(" rounds")
        layout.addRow("Clean Interval:", clean_interval_spin)

        oil_interval_spin = QSpinBox()
        oil_interval_spin.setRange(0, 365)
        oil_interval_spin.setValue(90)
        oil_interval_spin.setSuffix(" days")
        layout.addRow("Oil Interval:", oil_interval_spin)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        layout.addRow("Notes:", notes_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            fw = Firearm(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                caliber=caliber_input.text(),
                serial_number=serial_input.text(),
                purchase_date=datetime.now(),
                notes=notes_input.toPlainText(),
                clean_interval_rounds=clean_interval_spin.value(),
                oil_interval_days=oil_interval_spin.value(),
            )
            self.firearm_repo.add(fw)
            self.refresh_firearms()

    def open_transfer_dialog(self):
        row = self.firearm_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a firearm to transfer")
            return

        firearms = self.firearm_repo.get_all()
        selected = firearms[row]

        status = (
            selected.status.value
            if hasattr(selected.status, "value")
            else str(selected.status)
        )
        if status == "CHECKED_OUT":
            QMessageBox.warning(self, "Error", "Cannot transfer a checked-out firearm")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Transfer: {selected.name}")
        dialog.setMinimumWidth(500)

        layout = QFormLayout()

        info_group = QGroupBox("Firearm Being Transferred")
        info_layout = QFormLayout()
        info_layout.addRow("Name:", QLabel(selected.name))
        info_layout.addRow("Caliber:", QLabel(selected.caliber))
        info_layout.addRow("Serial #:", QLabel(selected.serial_number))
        info_group.setLayout(info_layout)
        layout.addRow(info_group)

        buyer_group = QGroupBox("Buyer Information")
        buyer_layout = QFormLayout()

        buyer_name_input = QLineEdit()
        buyer_layout.addRow("Name*:", buyer_name_input)

        buyer_address_input = QTextEdit()
        buyer_address_input.setMaximumHeight(60)
        buyer_layout.addRow("Address*:", buyer_address_input)

        buyer_dl_input = QLineEdit()
        buyer_layout.addRow("DL Number*:", buyer_dl_input)

        buyer_ltc_input = QLineEdit()
        buyer_layout.addRow("LTC Number:", buyer_ltc_input)

        buyer_group.setLayout(buyer_layout)
        layout.addRow(buyer_group)

        price_spin = QSpinBox()
        price_spin.setRange(0, 100000)
        price_spin.setPrefix("$")
        layout.addRow("Sale Price:", price_spin)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(60)
        layout.addRow("Notes:", notes_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if (
                not buyer_name_input.text()
                or not buyer_address_input.toPlainText()
                or not buyer_dl_input.text()
            ):
                QMessageBox.warning(
                    dialog, "Error", "Buyer name, address, and DL number are required"
                )
                return

            transfer = Transfer(
                id=str(uuid.uuid4()),
                firearm_id=selected.id,
                transfer_date=datetime.now(),
                buyer_name=buyer_name_input.text(),
                buyer_address=buyer_address_input.toPlainText(),
                buyer_dl_number=buyer_dl_input.text(),
                buyer_ltc_number=buyer_ltc_input.text(),
                sale_price=float(price_spin.value()),
                notes=notes_input.toPlainText(),
            )
            self.transfer_repo.add(transfer)
            self.transfer_repo.update_firearm_status(selected.id, "TRANSFERRED")
            self.refresh_firearms()
            self.refresh_transfers()

    # ============== ATTACHMENTS TAB ==============

    def create_attachments_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.attachment_table = QTableWidget()
        self.attachment_table.setColumnCount(5)
        self.attachment_table.setHorizontalHeaderLabels(
            ["Name", "Category", "Brand", "Mounted On", "Serial"]
        )
        self.attachment_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.attachment_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Attachment")
        add_btn.clicked.connect(self.open_add_attachment_dialog)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit / Reassign")
        edit_btn.clicked.connect(self.edit_attachment)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_attachment)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_attachments(self):
        self.attachment_table.setRowCount(0)
        attachments = self.gear_repo.get_all_attachments()

        firearms = self.firearm_repo.get_all()
        firearm_dict = {f.id: f.name for f in firearms}

        for i, att in enumerate(attachments):
            self.attachment_table.insertRow(i)
            self.attachment_table.setItem(i, 0, QTableWidgetItem(att.name))
            self.attachment_table.setItem(i, 1, QTableWidgetItem(att.category))
            self.attachment_table.setItem(i, 2, QTableWidgetItem(att.brand))

            mounted_on = ""
            if att.mounted_on_firearm_id:
                firearm_name = firearm_dict.get(att.mounted_on_firearm_id, "Unknown")
                if att.mount_position:
                    mounted_on = f"{firearm_name} ({att.mount_position})"
                else:
                    mounted_on = firearm_name
            self.attachment_table.setItem(i, 3, QTableWidgetItem(mounted_on))
            self.attachment_table.setItem(i, 4, QTableWidgetItem(att.serial_number))

    def open_add_attachment_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Attachment")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit()
        layout.addRow("Name:", name_input)

        category_input = QLineEdit()
        category_input.setPlaceholderText("optic, light, stock, rail, trigger...")
        layout.addRow("Category:", category_input)

        brand_input = QLineEdit()
        layout.addRow("Brand:", brand_input)

        model_input = QLineEdit()
        layout.addRow("Model:", model_input)

        serial_input = QLineEdit()
        layout.addRow("Serial #:", serial_input)

        firearms = self.firearm_repo.get_all()
        firearm_combo = QComboBox()
        firearm_combo.addItem("Unassigned")
        for fw in firearms:
            firearm_combo.addItem(fw.name, fw.id)
        layout.addRow("Mounted on:", firearm_combo)

        mount_pos_input = QLineEdit()
        mount_pos_input.setPlaceholderText("e.g., top rail, scout mount")
        layout.addRow("Mount position:", mount_pos_input)

        zero_spin = QSpinBox()
        zero_spin.setRange(0, 1000)
        zero_spin.setValue(0)
        layout.addRow("Zero distance (yd):", zero_spin)

        zero_notes_input = QTextEdit()
        zero_notes_input.setMaximumHeight(60)
        layout.addRow("Zero notes:", zero_notes_input)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(60)
        layout.addRow("Notes:", notes_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not name_input.text():
                QMessageBox.warning(dialog, "Error", "Name is required")
                return

            mounted_id = None
            idx = firearm_combo.currentIndex()
            if idx > 0:
                mounted_id = firearms[idx - 1].id

            zero_distance = zero_spin.value() if zero_spin.value() > 0 else None

            att = Attachment(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                category=category_input.text() or "other",
                brand=brand_input.text(),
                model=model_input.text(),
                purchase_date=datetime.now(),
                serial_number=serial_input.text(),
                mounted_on_firearm_id=mounted_id,
                mount_position=mount_pos_input.text(),
                zero_distance_yards=zero_distance,
                zero_notes=zero_notes_input.toPlainText(),
                notes=notes_input.toPlainText(),
            )
            self.gear_repo.add_attachment(att)
            self.refresh_attachments()

    def edit_attachment(self):
        row = self.attachment_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an attachment to edit")
            return

        attachments = self.gear_repo.get_all_attachments()
        selected = attachments[row]

        firearms = self.firearm_repo.get_all()
        firearm_dict = {f.id: f.name for f in firearms}

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Attachment: {selected.name}")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit(selected.name)
        layout.addRow("Name:", name_input)

        category_input = QLineEdit(selected.category)
        category_input.setPlaceholderText("optic, light, stock, rail, trigger...")
        layout.addRow("Category:", category_input)

        brand_input = QLineEdit(selected.brand)
        layout.addRow("Brand:", brand_input)

        model_input = QLineEdit(selected.model)
        layout.addRow("Model:", model_input)

        serial_input = QLineEdit(selected.serial_number)
        layout.addRow("Serial #:", serial_input)

        firearm_combo = QComboBox()
        firearm_combo.addItem("Unassigned", None)
        for fw in firearms:
            firearm_combo.addItem(fw.name, fw.id)
        if selected.mounted_on_firearm_id:
            idx = firearm_combo.findData(selected.mounted_on_firearm_id)
            if idx >= 0:
                firearm_combo.setCurrentIndex(idx)
        layout.addRow("Mounted on:", firearm_combo)

        mount_pos_input = QLineEdit(selected.mount_position)
        mount_pos_input.setPlaceholderText("e.g., top rail, scout mount")
        layout.addRow("Mount position:", mount_pos_input)

        zero_spin = QSpinBox()
        zero_spin.setRange(0, 1000)
        zero_spin.setValue(selected.zero_distance_yards or 0)
        layout.addRow("Zero distance (yd):", zero_spin)

        zero_notes_input = QTextEdit()
        zero_notes_input.setMaximumHeight(60)
        zero_notes_input.setPlainText(selected.zero_notes or "")
        layout.addRow("Zero notes:", zero_notes_input)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(60)
        notes_input.setPlainText(selected.notes or "")
        layout.addRow("Notes:", notes_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if not name_input.text():
                QMessageBox.warning(dialog, "Error", "Name is required")
                return

            mounted_id = firearm_combo.currentData()

            zero_distance = zero_spin.value() if zero_spin.value() > 0 else None

            att = Attachment(
                id=selected.id,
                name=name_input.text(),
                category=category_input.text() or "other",
                brand=brand_input.text(),
                model=model_input.text(),
                purchase_date=selected.purchase_date,
                serial_number=serial_input.text(),
                mounted_on_firearm_id=mounted_id,
                mount_position=mount_pos_input.text(),
                zero_distance_yards=zero_distance,
                zero_notes=zero_notes_input.toPlainText(),
                notes=notes_input.toPlainText(),
            )
            self.gear_repo.update_attachment(att)
            self.refresh_attachments()

    def delete_attachment(self):
        row = self.attachment_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an attachment to delete")
            return

        attachments = self.gear_repo.get_all_attachments()
        selected = attachments[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete '{selected.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.gear_repo.delete_attachment(selected.id)
            self.refresh_attachments()

    # ============== RELOADING TAB ==============

    def create_reloading_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.reload_table = QTableWidget()
        self.reload_table.setColumnCount(6)
        self.reload_table.setHorizontalHeaderLabels(
            ["Cartridge", "Bullet", "Powder", "Created", "Test Date", "Status"]
        )
        self.reload_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.reload_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Batch")
        add_btn.clicked.connect(self.open_add_reload_dialog)
        btn_layout.addWidget(add_btn)

        view_btn = QPushButton("View Details")
        view_btn.clicked.connect(self.view_reload_details)
        btn_layout.addWidget(view_btn)

        duplicate_btn = QPushButton("Duplicate Batch")
        duplicate_btn.clicked.connect(self.duplicate_reload_batch)
        btn_layout.addWidget(duplicate_btn)

        edit_btn = QPushButton("Edit Batch")
        edit_btn.clicked.connect(self.edit_reload_batch)
        btn_layout.addWidget(edit_btn)

        log_btn = QPushButton("Log Results")
        log_btn.clicked.connect(self.open_log_reload_results_dialog)
        btn_layout.addWidget(log_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_reload_batch)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_reloading(self):
        self.reload_table.setRowCount(0)
        batches = self.reload_repo.get_all()

        for i, batch in enumerate(batches):
            self.reload_table.insertRow(i)
            self.reload_table.setItem(i, 0, QTableWidgetItem(batch.cartridge))
            self.reload_table.setItem(
                i, 1, QTableWidgetItem(f"{batch.bullet_maker} {batch.bullet_model}")
            )
            self.reload_table.setItem(
                i,
                2,
                QTableWidgetItem(f"{batch.powder_name} {batch.powder_charge_gr}gr"),
            )
            self.reload_table.setItem(
                i, 3, QTableWidgetItem(batch.date_created.strftime("%Y-%m-%d"))
            )
            test_date = batch.test_date.strftime("%Y-%m-%d") if batch.test_date else ""
            self.reload_table.setItem(i, 4, QTableWidgetItem(test_date))
            self.reload_table.setItem(i, 5, QTableWidgetItem(batch.status))

    def open_add_reload_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Reload Batch")
        dialog.setMinimumWidth(450)

        layout = QFormLayout()

        cartridge_input = QLineEdit()
        layout.addRow("Cartridge:", cartridge_input)

        bullet_maker_input = QLineEdit()
        layout.addRow("Bullet Maker:", bullet_maker_input)

        bullet_model_input = QLineEdit()
        layout.addRow("Bullet Model:", bullet_model_input)

        weight_spin = QSpinBox()
        weight_spin.setRange(0, 1000)
        layout.addRow("Bullet Weight (gr):", weight_spin)

        powder_name_input = QLineEdit()
        layout.addRow("Powder:", powder_name_input)

        charge_spin = QSpinBox()
        charge_spin.setRange(0, 200)
        layout.addRow("Charge (gr):", charge_spin)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            batch = ReloadBatch(
                id=str(uuid.uuid4()),
                cartridge=cartridge_input.text(),
                date_created=datetime.now(),
                bullet_maker=bullet_maker_input.text(),
                bullet_model=bullet_model_input.text(),
                bullet_weight_gr=weight_spin.value(),
                powder_name=powder_name_input.text(),
                powder_charge_gr=charge_spin.value(),
                status="WORKUP",
            )
            self.reload_repo.add_batch(batch)
            self.refresh_reloading()

    def view_reload_details(self):
        row = self.reload_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a batch to view")
            return

        batches = self.reload_repo.get_all()
        selected = batches[row]

        QMessageBox.information(
            self,
            "Reload Details",
            f"Cartridge: {selected.cartridge}\n"
            f"Bullet: {selected.bullet_maker} {selected.bullet_model} {selected.bullet_weight_gr}gr\n"
            f"Powder: {selected.powder_name} {selected.powder_charge_gr}gr\n"
            f"Status: {selected.status}\n"
            f"Notes: {selected.notes}",
        )

    def _get_selected_reload_batch(self):
        row = self.reload_table.currentRow()
        if row < 0:
            return None
        batches = self.reload_repo.get_all()
        if row >= len(batches):
            return None
        return batches[row]

    def duplicate_reload_batch(self):
        batch = self._get_selected_reload_batch()
        if not batch:
            QMessageBox.warning(self, "Error", "Select a batch to duplicate")
            return

        reply = QMessageBox.question(
            self,
            "Duplicate Batch",
            f"Create a copy of '{batch.cartridge}' batch for further development?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            new_batch = ReloadBatch(
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
                test_date=None,
                avg_velocity=None,
                es=None,
                sd=None,
                group_size_inches=None,
                group_distance_yards=None,
                intended_use=batch.intended_use,
                status="WORKUP",
                notes=f"(DUP from {batch.date_created.strftime('%Y-%m-%d')}) {batch.notes or ''}",
            )
            self.reload_repo.add_batch(new_batch)
            self.refresh_reloading()
            QMessageBox.information(
                self,
                "Duplicated",
                f"'{batch.cartridge}' batch duplicated for further development.",
            )

    def edit_reload_batch(self):
        batch = self._get_selected_reload_batch()
        if not batch:
            QMessageBox.warning(self, "Error", "Select a batch to edit")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Batch: {batch.cartridge}")
        dialog.setMinimumWidth(500)

        layout = QFormLayout()

        cartridge_input = QLineEdit(batch.cartridge)
        layout.addRow("Cartridge:", cartridge_input)

        firearms = self.firearm_repo.get_all()
        firearm_combo = QComboBox()
        firearm_combo.addItem("None", None)
        for fw in firearms:
            firearm_combo.addItem(fw.name, fw.id)
        if batch.firearm_id:
            idx = firearm_combo.findData(batch.firearm_id)
            if idx >= 0:
                firearm_combo.setCurrentIndex(idx)
        layout.addRow("Firearm:", firearm_combo)

        bullet_maker_input = QLineEdit(batch.bullet_maker or "")
        layout.addRow("Bullet Maker:", bullet_maker_input)

        bullet_model_input = QLineEdit(batch.bullet_model or "")
        layout.addRow("Bullet Model:", bullet_model_input)

        bullet_weight_spin = QSpinBox()
        bullet_weight_spin.setRange(0, 1000)
        bullet_weight_spin.setValue(batch.bullet_weight_gr or 0)
        layout.addRow("Bullet Weight (gr):", bullet_weight_spin)

        powder_name_input = QLineEdit(batch.powder_name or "")
        layout.addRow("Powder:", powder_name_input)

        powder_charge_spin = QSpinBox()
        powder_charge_spin.setRange(0, 200)
        powder_charge_spin.setValue(
            int(batch.powder_charge_gr) if batch.powder_charge_gr else 0
        )
        layout.addRow("Powder Charge (gr):", powder_charge_spin)

        powder_lot_input = QLineEdit(batch.powder_lot or "")
        layout.addRow("Powder Lot:", powder_lot_input)

        primer_maker_input = QLineEdit(batch.primer_maker or "")
        layout.addRow("Primer:", primer_maker_input)

        primer_type_input = QLineEdit(batch.primer_type or "")
        layout.addRow("Primer Type:", primer_type_input)

        case_brand_input = QLineEdit(batch.case_brand or "")
        layout.addRow("Case Brand:", case_brand_input)

        case_times_fired_spin = QSpinBox()
        case_times_fired_spin.setRange(0, 100)
        case_times_fired_spin.setValue(batch.case_times_fired or 0)
        layout.addRow("Case Times Fired:", case_times_fired_spin)

        coal_input = QLineEdit(str(batch.coal_in) if batch.coal_in else "")
        layout.addRow("COAL:", coal_input)

        crimp_style_input = QLineEdit(batch.crimp_style or "")
        layout.addRow("Crimp Style:", crimp_style_input)

        intended_use_input = QLineEdit(batch.intended_use or "")
        layout.addRow("Intended Use:", intended_use_input)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        notes_input.setPlainText(batch.notes or "")
        layout.addRow("Notes:", notes_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                coal_val = float(coal_input.text()) if coal_input.text() else None
            except ValueError:
                QMessageBox.warning(dialog, "Error", "COAL must be a number")
                return

            batch.cartridge = cartridge_input.text()
            batch.firearm_id = firearm_combo.currentData()
            batch.bullet_maker = bullet_maker_input.text()
            batch.bullet_model = bullet_model_input.text()
            batch.bullet_weight_gr = bullet_weight_spin.value()
            batch.powder_name = powder_name_input.text()
            batch.powder_charge_gr = powder_charge_spin.value()
            batch.powder_lot = powder_lot_input.text()
            batch.primer_maker = primer_maker_input.text()
            batch.primer_type = primer_type_input.text()
            batch.case_brand = case_brand_input.text()
            batch.case_times_fired = case_times_fired_spin.value()
            batch.coal_in = coal_val
            batch.crimp_style = crimp_style_input.text()
            batch.intended_use = intended_use_input.text()
            batch.notes = notes_input.toPlainText()

            self.reload_repo.update(batch)
            self.refresh_reloading()

    def open_log_reload_results_dialog(self):
        batch = self._get_selected_reload_batch()
        if not batch:
            QMessageBox.warning(self, "Error", "Select a batch to log results for")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Log Results: {batch.cartridge}")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        test_date_edit = QDateEdit()
        test_date_edit.setCalendarPopup(True)
        test_date_edit.setDate(QDate.currentDate())
        layout.addRow("Test date:", test_date_edit)

        avg_vel_spin = QSpinBox()
        avg_vel_spin.setRange(0, 10000)
        layout.addRow("Avg velocity (fps):", avg_vel_spin)

        es_spin = QSpinBox()
        es_spin.setRange(0, 1000)
        layout.addRow("ES:", es_spin)

        sd_spin = QSpinBox()
        sd_spin.setRange(0, 1000)
        layout.addRow("SD:", sd_spin)

        group_size_input = QLineEdit()
        group_size_input.setPlaceholderText("e.g., 1.5")
        layout.addRow("Group size (in):", group_size_input)

        group_dist_spin = QSpinBox()
        group_dist_spin.setRange(0, 1000)
        group_dist_spin.setValue(100)
        layout.addRow("Group distance (yd):", group_dist_spin)

        status_combo = QComboBox()
        status_combo.addItems(["WORKUP", "APPROVED", "REJECTED"])
        status_combo.setCurrentText(batch.status or "WORKUP")
        layout.addRow("Status:", status_combo)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        notes_input.setPlainText(batch.notes or "")
        layout.addRow("Notes:", notes_input)

        save_btn = QPushButton("Save results")

        def save():
            try:
                group_size = (
                    float(group_size_input.text()) if group_size_input.text() else None
                )
            except ValueError:
                QMessageBox.warning(
                    dialog, "Error", "Group size must be a number (e.g., 1.5)"
                )
                return

            test_dt = datetime(
                test_date_edit.date().year(),
                test_date_edit.date().month(),
                test_date_edit.date().day(),
            )

            batch.test_date = test_dt
            batch.avg_velocity = avg_vel_spin.value() or None
            batch.es = es_spin.value() or None
            batch.sd = sd_spin.value() or None
            batch.group_size_inches = group_size
            batch.group_distance_yards = group_dist_spin.value() or None
            batch.status = status_combo.currentText()
            batch.notes = notes_input.toPlainText()

            self.reload_repo.update(batch)
            self.refresh_reloading()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def delete_reload_batch(self):
        row = self.reload_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a batch to delete")
            return

        batches = self.reload_repo.get_all()
        selected = batches[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete this reload batch?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.reload_repo.delete(selected.id)
            self.refresh_reloading()

    # ============== SOFT GEAR TAB ==============

    def create_soft_gear_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.soft_gear_table = QTableWidget()
        self.soft_gear_table.setColumnCount(5)
        self.soft_gear_table.setHorizontalHeaderLabels(
            ["Name", "Category", "Brand", "Status", "Notes"]
        )
        self.soft_gear_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.soft_gear_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(self.open_add_soft_gear_dialog)
        btn_layout.addWidget(add_btn)

        update_btn = QPushButton("Update Item")
        update_btn.clicked.connect(self.edit_soft_gear)
        btn_layout.addWidget(update_btn)

        log_btn = QPushButton("Log Maintenance")
        log_btn.clicked.connect(self.open_log_maintenance_dialog)
        btn_layout.addWidget(log_btn)

        history_btn = QPushButton("View History")
        history_btn.clicked.connect(self.view_soft_gear_history)
        btn_layout.addWidget(history_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_soft_gear)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_soft_gear(self):
        self.soft_gear_table.setRowCount(0)
        items = self.gear_repo.get_all_soft_gear()

        for i, item in enumerate(items):
            self.soft_gear_table.insertRow(i)
            self.soft_gear_table.setItem(i, 0, QTableWidgetItem(item.name))
            self.soft_gear_table.setItem(i, 1, QTableWidgetItem(item.category))
            self.soft_gear_table.setItem(i, 2, QTableWidgetItem(item.brand))
            self.soft_gear_table.setItem(i, 3, QTableWidgetItem(item.status))
            self.soft_gear_table.setItem(i, 4, QTableWidgetItem(item.notes))

    def open_add_soft_gear_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Soft Gear")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit()
        layout.addRow("Name:", name_input)

        category_input = QLineEdit()
        layout.addRow("Category:", category_input)

        brand_input = QLineEdit()
        layout.addRow("Brand:", brand_input)

        notes_input = QTextEdit()
        layout.addRow("Notes:", notes_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            gear = SoftGear(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                category=category_input.text(),
                brand=brand_input.text(),
                purchase_date=datetime.now(),
                notes=notes_input.toPlainText(),
            )
            self.gear_repo.add_soft_gear(gear)
            self.refresh_soft_gear()

    def edit_soft_gear(self):
        row = self.soft_gear_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an item to edit")
            return

        items = self.gear_repo.get_all_soft_gear()
        selected = items[row]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Soft Gear: {selected.name}")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit(selected.name)
        layout.addRow("Name:", name_input)

        category_input = QLineEdit(selected.category)
        layout.addRow("Category:", category_input)

        brand_input = QLineEdit(selected.brand)
        layout.addRow("Brand:", brand_input)

        status_combo = QComboBox()
        status_combo.addItems(["AVAILABLE", "CHECKED_OUT", "MAINTENANCE", "RETIRED"])
        status_combo.setCurrentText(selected.status)
        layout.addRow("Status:", status_combo)

        notes_input = QTextEdit()
        notes_input.setPlainText(selected.notes or "")
        layout.addRow("Notes:", notes_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected.name = name_input.text()
            selected.category = category_input.text()
            selected.brand = brand_input.text()
            selected.status = status_combo.currentText()
            selected.notes = notes_input.toPlainText()
            self.gear_repo.update_soft_gear(selected)
            self.refresh_soft_gear()

    def delete_soft_gear(self):
        row = self.soft_gear_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an item to delete")
            return

        items = self.gear_repo.get_all_soft_gear()
        selected = items[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete '{selected.name}'?\n\nThis will also delete all maintenance logs and checkout history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.gear_repo.delete_soft_gear(selected.id)
            self.refresh_soft_gear()

    def open_log_maintenance_dialog(self):
        items = self.gear_repo.get_all_soft_gear()

        if not items:
            QMessageBox.warning(
                self, "Error", "No soft gear items to log maintenance for"
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Log Maintenance")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        item_combo = QComboBox()
        for item in items:
            item_combo.addItem(item.name, item.id)
        layout.addRow("Item:", item_combo)

        type_combo = QComboBox()
        type_combo.addItems(["CLEANING", "REPAIR", "INSPECTION", "OTHER"])
        layout.addRow("Type:", type_combo)

        details_input = QTextEdit()
        details_input.setMaximumHeight(80)
        layout.addRow("Details:", details_input)

        ammo_spin = QSpinBox()
        ammo_spin.setRange(0, 100000)
        layout.addRow("Rounds fired:", ammo_spin)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_id = items[item_combo.currentIndex()].id
            from dataclasses import dataclass
            from datetime import datetime

            @dataclass
            class MaintenanceLog:
                id: str
                item_id: str
                item_type: str
                log_type: str
                date: datetime
                details: str
                ammo_count: int
                photo_path: str

            log = MaintenanceLog(
                id=str(uuid.uuid4()),
                item_id=selected_id,
                item_type=GearCategory.SOFT_GEAR.value,
                log_type=type_combo.currentText(),
                date=datetime.now(),
                details=details_input.toPlainText(),
                ammo_count=ammo_spin.value() if ammo_spin.value() > 0 else None,
                photo_path=None,
            )
            self.gear_repo.add_maintenance_log(log)
            self.refresh_soft_gear()

    def view_soft_gear_history(self):
        row = self.soft_gear_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an item first")
            return

        items = self.gear_repo.get_all_soft_gear()
        selected = items[row]

        logs = self.gear_repo.get_maintenance_logs(selected.id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"History: {selected.name}")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        hist_table = QTableWidget()
        hist_table.setColumnCount(4)
        hist_table.setHorizontalHeaderLabels(["Date", "Type", "Details", "Rounds"])
        hist_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        for i, log in enumerate(logs):
            hist_table.insertRow(i)
            hist_table.setItem(
                i,
                0,
                QTableWidgetItem(
                    log.date.strftime("%Y-%m-%d %H:%M") if log.date else ""
                ),
            )
            hist_table.setItem(i, 1, QTableWidgetItem(log.log_type))
            hist_table.setItem(i, 2, QTableWidgetItem(log.details or ""))
            hist_table.setItem(
                i, 3, QTableWidgetItem(str(log.ammo_count) if log.ammo_count else "")
            )

        layout.addWidget(hist_table)
        dialog.setLayout(layout)
        dialog.exec()

    # ============== CONSUMABLES TAB ==============

    def create_consumables_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.consumable_table = QTableWidget()
        self.consumable_table.setColumnCount(5)
        self.consumable_table.setHorizontalHeaderLabels(
            ["Name", "Category", "Quantity", "Min Qty", "Status"]
        )
        self.consumable_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.consumable_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Item")
        add_btn.clicked.connect(self.open_add_consumable_dialog)
        btn_layout.addWidget(add_btn)

        add_stock_btn = QPushButton("Add Stock")
        add_stock_btn.clicked.connect(self.add_consumable_stock)
        btn_layout.addWidget(add_stock_btn)

        use_btn = QPushButton("Use Stock")
        use_btn.clicked.connect(self.use_consumable_stock)
        btn_layout.addWidget(use_btn)

        history_btn = QPushButton("View History")
        history_btn.clicked.connect(self.view_consumable_history)
        btn_layout.addWidget(history_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_consumable)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_consumables(self):
        self.consumable_table.setRowCount(0)
        items = self.consumable_repo.get_all()

        for i, item in enumerate(items):
            self.consumable_table.insertRow(i)
            self.consumable_table.setItem(i, 0, QTableWidgetItem(item.name))
            self.consumable_table.setItem(i, 1, QTableWidgetItem(item.category))
            self.consumable_table.setItem(
                i, 2, QTableWidgetItem(f"{item.quantity} {item.unit}")
            )
            self.consumable_table.setItem(
                i, 3, QTableWidgetItem(str(item.min_quantity))
            )

            status = "LOW" if item.quantity <= item.min_quantity else "OK"
            status_item = QTableWidgetItem(status)
            if status == "LOW":
                status_item.setBackground(QColor(255, 150, 150))
            self.consumable_table.setItem(i, 4, status_item)

    def open_add_consumable_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Consumable")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit()
        name_input.setPlaceholderText("e.g., .45-70 Govt 405gr")
        layout.addRow("Name:", name_input)

        category_combo = QComboBox()
        category_combo.setEditable(True)
        category_combo.addItems(
            ["ammo", "batteries", "hygiene", "medical", "cleaning", "other"]
        )
        layout.addRow("Category:", category_combo)

        unit_combo = QComboBox()
        unit_combo.setEditable(True)
        unit_combo.addItems(["rounds", "count", "oz", "pairs", "boxes"])
        layout.addRow("Unit:", unit_combo)

        qty_spin = QSpinBox()
        qty_spin.setRange(0, 100000)
        layout.addRow("Initial Qty:", qty_spin)

        min_qty_spin = QSpinBox()
        min_qty_spin.setRange(0, 100000)
        min_qty_spin.setValue(20)
        layout.addRow("Min Qty (alert):", min_qty_spin)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(60)
        layout.addRow("Notes:", notes_input)

        save_btn = QPushButton("Save")

        def save():
            if not name_input.text():
                QMessageBox.warning(dialog, "Error", "Name is required")
                return
            cons = Consumable(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                category=category_combo.currentText(),
                unit=unit_combo.currentText(),
                quantity=qty_spin.value(),
                min_quantity=min_qty_spin.value(),
                notes=notes_input.toPlainText(),
            )
            self.consumable_repo.add(cons)
            self.refresh_consumables()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def add_consumable_stock(self):
        row = self.consumable_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an item")
            return

        items = self.consumable_repo.get_all()
        selected = items[row]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Add Stock: {selected.name}")
        layout = QFormLayout()

        qty_spin = QSpinBox()
        qty_spin.setRange(1, 10000)
        layout.addRow("Quantity to Add:", qty_spin)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.consumable_repo.update_quantity(
                selected.id, qty_spin.value(), "RESTOCK"
            )
            self.refresh_consumables()

    def use_consumable_stock(self):
        row = self.consumable_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an item")
            return

        items = self.consumable_repo.get_all()
        selected = items[row]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Use Stock: {selected.name}")
        layout = QFormLayout()

        qty_spin = QSpinBox()
        qty_spin.setRange(1, selected.quantity)
        layout.addRow("Quantity to Use:", qty_spin)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.consumable_repo.update_quantity(selected.id, -qty_spin.value(), "USE")
            self.refresh_consumables()

    def delete_consumable(self):
        row = self.consumable_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an item to delete")
            return

        items = self.consumable_repo.get_all()
        selected = items[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete '{selected.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.consumable_repo.delete(selected.id)
            self.refresh_consumables()

    def view_consumable_history(self):
        row = self.consumable_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a consumable first")
            return

        consumables = self.consumable_repo.get_all()
        selected = consumables[row]
        history = self.consumable_repo.get_history(selected.id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"History: {selected.name}")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "Type", "Qty", "Notes"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for i, tx in enumerate(history):
            table.insertRow(i)
            table.setItem(i, 0, QTableWidgetItem(tx.date.strftime("%Y-%m-%d %H:%M")))
            table.setItem(i, 1, QTableWidgetItem(tx.transaction_type))

            qty_text = f"+{tx.quantity}" if tx.quantity > 0 else str(tx.quantity)
            table.setItem(i, 2, QTableWidgetItem(qty_text))
            table.setItem(i, 3, QTableWidgetItem(tx.notes))

        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.exec()

    # ============== LOADOUTS TAB ==============

    def create_loadouts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.loadout_table = QTableWidget()
        self.loadout_table.setColumnCount(5)
        self.loadout_table.setHorizontalHeaderLabels(
            ["Name", "Description", "Items", "Consumables", "Created"]
        )
        self.loadout_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.loadout_table)

        btn_layout = QHBoxLayout()

        create_btn = QPushButton("Create Loadout")
        create_btn.clicked.connect(lambda: self.open_create_loadout_dialog(None))
        btn_layout.addWidget(create_btn)

        edit_btn = QPushButton("Edit Loadout")
        edit_btn.clicked.connect(self.open_edit_loadout_dialog)
        btn_layout.addWidget(edit_btn)

        duplicate_btn = QPushButton("Duplicate Loadout")
        duplicate_btn.clicked.connect(self.duplicate_loadout)
        btn_layout.addWidget(duplicate_btn)

        checkout_btn = QPushButton("Checkout Loadout")
        checkout_btn.setStyleSheet("background-color: #20206B; font-weight: bold;")
        checkout_btn.clicked.connect(self.checkout_loadout)
        btn_layout.addWidget(checkout_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_loadout)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_loadouts(self):
        self.loadout_table.setRowCount(0)
        loadouts = self.loadout_repo.get_all()

        firearms = {f.id: f.name for f in self.firearm_repo.get_all()}
        soft_gear = {g.id: g.name for g in self.gear_repo.get_all_soft_gear()}
        nfa_items = {n.id: n.name for n in self.gear_repo.get_all_nfa_items()}

        all_consumables = self.consumable_repo.get_all()
        consumable_dict = {c.id: c for c in all_consumables}

        for i, lo in enumerate(loadouts):
            self.loadout_table.insertRow(i)
            self.loadout_table.setItem(i, 0, QTableWidgetItem(lo.name))

            description_text = lo.description if lo.description else ""
            self.loadout_table.setItem(i, 1, QTableWidgetItem(description_text))

            items = self.loadout_repo.get_items(lo.id)
            item_names = []
            for item in items:
                if item.item_type == GearCategory.FIREARM.value:
                    item_names.append(f"🔫 {firearms.get(item.item_id, 'Unknown')}")
                elif item.item_type == GearCategory.SOFT_GEAR.value:
                    item_names.append(f"🎒 {soft_gear.get(item.item_id, 'Unknown')}")
                elif item.item_type == GearCategory.NFA_ITEM.value:
                    item_names.append(f"🔇 {nfa_items.get(item.item_id, 'Unknown')}")

            self.loadout_table.setItem(i, 2, QTableWidgetItem(", ".join(item_names)))

            consumables = self.loadout_repo.get_consumables(lo.id)
            cons_names = []
            for cons in consumables:
                c = consumable_dict.get(cons.consumable_id)
                if c:
                    cons_names.append(f"{c.name} ({cons.quantity} {c.unit})")

            self.loadout_table.setItem(i, 3, QTableWidgetItem(", ".join(cons_names)))

            created_text = (
                lo.created_date.strftime("%Y-%m-%d") if lo.created_date else "Never"
            )
            self.loadout_table.setItem(i, 4, QTableWidgetItem(created_text))

    def open_create_loadout_dialog(self, loadout=None):
        is_edit = loadout is not None
        dialog = QDialog(self)
        title = "Edit Loadout: " + loadout.name if is_edit else "Create Loadout"
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)

        form_layout = QFormLayout()

        name_input = QLineEdit()
        if is_edit:
            name_input.setText(loadout.name)
        form_layout.addRow("Name:", name_input)

        description_input = QLineEdit()
        if is_edit:
            description_input.setText(loadout.description or "")
        form_layout.addRow("Description:", description_input)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        if is_edit:
            notes_input.setText(loadout.notes or "")
        form_layout.addRow("Notes:", notes_input)

        layout.addLayout(form_layout)

        tabs = QTabWidget()

        firearms_tab = QWidget()
        firearms_layout = QVBoxLayout()

        info_label = QLabel(
            "Select firearms - their mounted attachments will be automatically included."
        )
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        firearms_layout.addWidget(info_label)

        available_firearms = self.firearm_repo.get_all()
        if not available_firearms:
            firearms_layout.addWidget(QLabel("No firearms available."))
        else:
            firearms_list = QWidget()
            firearms_list_layout = QVBoxLayout()
            firearms_list_layout.setContentsMargins(0, 0, 0, 0)

            selected_firearm_ids = set()
            if is_edit:
                for item in self.loadout_repo.get_items(loadout.id):
                    if item.item_type == GearCategory.FIREARM.value:
                        selected_firearm_ids.add(item.item_id)

            for fw in available_firearms:
                checkbox = QCheckBox(f"🔫 {fw.name}")
                checkbox.setProperty("item_id", fw.id)
                if is_edit and fw.id in selected_firearm_ids:
                    checkbox.setChecked(True)
                firearms_list_layout.addWidget(checkbox)

                attachments = self.gear_repo.get_attachments_for_firearm(fw.id)
                if attachments:
                    for att in attachments:
                        att_label = QLabel(f"    🔧 {att.name} ({att.category})")
                        att_label.setStyleSheet(
                            "color: #888; font-size: 11px; margin-left: 20px;"
                        )
                        firearms_list_layout.addWidget(att_label)

            firearms_list.setLayout(firearms_list_layout)
            firearms_layout.addWidget(firearms_list)

        firearms_tab.setLayout(firearms_layout)
        tabs.addTab(firearms_tab, "🔫 Firearms")

        soft_gear_tab = QWidget()
        soft_gear_layout = QVBoxLayout()

        info_label = QLabel("Select soft gear items to include in this loadout.")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        soft_gear_layout.addWidget(info_label)

        available_soft_gear = self.gear_repo.get_all_soft_gear()
        selected_soft_gear_ids = set()
        if is_edit:
            for item in self.loadout_repo.get_items(loadout.id):
                if item.item_type == GearCategory.SOFT_GEAR.value:
                    selected_soft_gear_ids.add(item.item_id)

        for gear in available_soft_gear:
            checkbox = QCheckBox(f"🎒 {gear.name} ({gear.category})")
            checkbox.setProperty("item_id", gear.id)
            if is_edit and gear.id in selected_soft_gear_ids:
                checkbox.setChecked(True)
            soft_gear_layout.addWidget(checkbox)

        soft_gear_tab.setLayout(soft_gear_layout)
        tabs.addTab(soft_gear_tab, "🎒 Soft Gear")

        nfa_tab = QWidget()
        nfa_layout = QVBoxLayout()

        info_label = QLabel("Select NFA items to include in this loadout.")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        nfa_layout.addWidget(info_label)

        available_nfa = self.gear_repo.get_all_nfa_items()
        selected_nfa_ids = set()
        if is_edit:
            for item in self.loadout_repo.get_items(loadout.id):
                if item.item_type == GearCategory.NFA_ITEM.value:
                    selected_nfa_ids.add(item.item_id)

        for nfa in available_nfa:
            checkbox = QCheckBox(f"🔇 {nfa.name} ({nfa.nfa_type.value})")
            checkbox.setProperty("item_id", nfa.id)
            if is_edit and nfa.id in selected_nfa_ids:
                checkbox.setChecked(True)
            nfa_layout.addWidget(checkbox)

        nfa_tab.setLayout(nfa_layout)
        tabs.addTab(nfa_tab, "🔇 NFA Items")

        consumables_tab = QWidget()
        cons_layout = QVBoxLayout()

        info_label = QLabel("Select consumables and quantities for this loadout.")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        cons_layout.addWidget(info_label)

        consumables_table = QTableWidget()
        consumables_table.setColumnCount(4)
        consumables_table.setHorizontalHeaderLabels(
            ["Name", "Category", "Unit", "Quantity"]
        )
        consumables_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        consumables_table.setMinimumHeight(200)

        all_consumables = self.consumable_repo.get_all()
        selected_consumables = {}
        if is_edit:
            for lc in self.loadout_repo.get_consumables(loadout.id):
                selected_consumables[lc.consumable_id] = lc.quantity

        for i, cons in enumerate(all_consumables):
            consumables_table.insertRow(i)
            consumables_table.setItem(i, 0, QTableWidgetItem(cons.name))
            consumables_table.setItem(i, 1, QTableWidgetItem(cons.category))

            cons_cell = QTableWidgetItem(f"{cons.quantity} {cons.unit}")
            cons_cell.setData(Qt.ItemDataRole.UserRole, cons.id)
            consumables_table.setItem(i, 2, cons_cell)

            qty_spinbox = QSpinBox()
            qty_spinbox.setMinimum(0)
            qty_spinbox.setMaximum(9999)
            if is_edit and cons.id in selected_consumables:
                qty_spinbox.setValue(selected_consumables[cons.id])
            else:
                qty_spinbox.setValue(0)
            qty_spinbox.setProperty("consumable_id", cons.id)
            consumables_table.setCellWidget(i, 3, qty_spinbox)

        cons_layout.addWidget(consumables_table)

        selected_cons_list_label = QLabel("Selected Consumables:")
        selected_cons_list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        cons_layout.addWidget(selected_cons_list_label)

        selected_consumables_list = QListWidget()
        selected_consumables_list.setMaximumHeight(120)
        if is_edit:
            for lc in self.loadout_repo.get_consumables(loadout.id):
                cons = next(
                    (c for c in all_consumables if c.id == lc.consumable_id), None
                )
                if cons:
                    selected_consumables_list.addItem(
                        f"{cons.name}: {lc.quantity} {cons.unit}"
                    )
        cons_layout.addWidget(selected_consumables_list)

        consumables_tab.setLayout(cons_layout)
        tabs.addTab(consumables_tab, "📦 Consumables")

        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save Loadout")
        save_btn.setStyleSheet("background-color: #202060; font-weight: bold;")

        def save_loadout():
            if is_edit:
                loadout.name = name_input.text()
                loadout.description = description_input.text()
                loadout.notes = notes_input.toPlainText()
                self.loadout_repo.update(loadout)
                current_loadout_id = loadout.id
            else:
                new_loadout = Loadout(
                    id=str(uuid.uuid4()),
                    name=name_input.text(),
                    description=description_input.text(),
                    notes=notes_input.toPlainText(),
                    created_date=datetime.now(),
                )
                self.loadout_repo.create(new_loadout)
                current_loadout_id = new_loadout.id

            self.loadout_repo.delete_items(current_loadout_id)
            self.loadout_repo.delete_consumables(current_loadout_id)

            for i in range(firearms_list_layout.count()):
                item = firearms_list_layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), QCheckBox):
                    checkbox = item.widget()
                    if checkbox.isChecked():
                        fw_id = checkbox.property("item_id")
                        item_obj = LoadoutItem(
                            id=str(uuid.uuid4()),
                            loadout_id=current_loadout_id,
                            item_id=fw_id,
                            item_type=GearCategory.FIREARM.value,
                        )
                        self.loadout_repo.add_item(item_obj)

            for i in range(soft_gear_layout.count()):
                item = soft_gear_layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), QCheckBox):
                    checkbox = item.widget()
                    if checkbox.isChecked():
                        gear_id = checkbox.property("item_id")
                        item_obj = LoadoutItem(
                            id=str(uuid.uuid4()),
                            loadout_id=current_loadout_id,
                            item_id=gear_id,
                            item_type=GearCategory.SOFT_GEAR.value,
                        )
                        self.loadout_repo.add_item(item_obj)

            for i in range(nfa_layout.count()):
                item = nfa_layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), QCheckBox):
                    checkbox = item.widget()
                    if checkbox.isChecked():
                        nfa_id = checkbox.property("item_id")
                        item_obj = LoadoutItem(
                            id=str(uuid.uuid4()),
                            loadout_id=current_loadout_id,
                            item_id=nfa_id,
                            item_type=GearCategory.NFA_ITEM.value,
                        )
                        self.loadout_repo.add_item(item_obj)

            for i in range(consumables_table.rowCount()):
                qty_spinbox = consumables_table.cellWidget(i, 3)
                if qty_spinbox and qty_spinbox.value() > 0:
                    cons_id = qty_spinbox.property("consumable_id")
                    cons_obj = LoadoutConsumable(
                        id=str(uuid.uuid4()),
                        loadout_id=current_loadout_id,
                        consumable_id=cons_id,
                        quantity=qty_spinbox.value(),
                    )
                    self.loadout_repo.add_consumable(cons_obj)

            self.refresh_loadouts()
            dialog.accept()
            QMessageBox.information(
                dialog,
                "Success",
                "Loadout saved successfully.",
            )

        save_btn.clicked.connect(save_loadout)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        dialog.setLayout(layout)
        dialog.exec()

    def _get_selected_loadout(self) -> Loadout | None:
        row = self.loadout_table.currentRow()
        if row < 0:
            return None
        loadouts = self.loadout_repo.get_all()
        if row >= len(loadouts):
            return None
        return loadouts[row]

    def open_edit_loadout_dialog(self):
        loadout = self._get_selected_loadout()
        if not loadout:
            QMessageBox.warning(
                self, "No Selection", "Please select a loadout to edit."
            )
            return

        self.open_create_loadout_dialog(loadout)

    def duplicate_loadout(self):
        loadout = self._get_selected_loadout()
        if not loadout:
            QMessageBox.warning(
                self, "No Selection", "Please select a loadout to duplicate."
            )
            return

        items = self.loadout_repo.get_items(loadout.id)
        consumables = self.loadout_repo.get_consumables(loadout.id)

        new_loadout = Loadout(
            id=str(uuid.uuid4()),
            name=f"{loadout.name} (Copy)",
            description=loadout.description,
            created_date=datetime.now(),
            notes=loadout.notes,
        )
        self.loadout_repo.create(new_loadout)

        for item in items:
            new_item = LoadoutItem(
                id=str(uuid.uuid4()),
                loadout_id=new_loadout.id,
                item_id=item.item_id,
                item_type=item.item_type,
                notes=item.notes,
            )
            self.loadout_repo.add_item(new_item)

        for cons in consumables:
            new_cons = LoadoutConsumable(
                id=str(uuid.uuid4()),
                loadout_id=new_loadout.id,
                consumable_id=cons.consumable_id,
                quantity=cons.quantity,
                notes=cons.notes,
            )
            self.loadout_repo.add_consumable(new_cons)

        self.refresh_loadouts()
        QMessageBox.information(
            self,
            "Duplicated",
            f"Loadout '{loadout.name}' duplicated successfully as '{new_loadout.name}'.",
        )

    def checkout_loadout(self):
        row = self.loadout_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a loadout to checkout.")
            return

        loadouts = self.loadout_repo.get_all()
        if row >= len(loadouts):
            return
        loadout = loadouts[row]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Checkout Loadout: {loadout.name}")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout(dialog)

        info_group = QGroupBox("Loadout Details")
        info_layout = QFormLayout()

        name_label = QLabel(loadout.name)
        info_layout.addRow("Name:", name_label)

        desc_label = QLabel(loadout.description if loadout.description else "None")
        info_layout.addRow("Description:", desc_label)

        firearms = {f.id: f.name for f in self.firearm_repo.get_all()}
        soft_gear = {g.id: g.name for g in self.gear_repo.get_all_soft_gear()}
        nfa_items = {n.id: n.name for n in self.gear_repo.get_all_nfa_items()}

        items = self.loadout_repo.get_items(loadout.id)
        item_summary = []
        for item in items:
            if item.item_type == GearCategory.FIREARM.value:
                item_summary.append(f"🔫 {firearms.get(item.item_id, 'Unknown')}")
            elif item.item_type == GearCategory.SOFT_GEAR.value:
                item_summary.append(f"🎒 {soft_gear.get(item.item_id, 'Unknown')}")
            elif item.item_type == GearCategory.NFA_ITEM.value:
                item_summary.append(f"🔇 {nfa_items.get(item.item_id, 'Unknown')}")

        items_text = ", ".join(item_summary) if item_summary else "None"
        items_label = QLabel(items_text)
        items_label.setWordWrap(True)
        info_layout.addRow("Items:", items_label)

        all_consumables = self.consumable_repo.get_all()
        cons_dict = {c.id: c for c in all_consumables}
        consumables = self.loadout_repo.get_consumables(loadout.id)
        cons_summary = []
        for cons in consumables:
            c = cons_dict.get(cons.consumable_id)
            if c:
                cons_summary.append(f"{c.name} ({cons.quantity} {c.unit})")

        consumables_text = ", ".join(cons_summary) if cons_summary else "None"
        consumables_label = QLabel(consumables_text)
        consumables_label.setWordWrap(True)
        info_layout.addRow("Consumables:", consumables_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        form_layout = QFormLayout()

        borrower_combo = QComboBox()
        borrowers = self.checkout_repo.get_all_borrowers()
        for borrower in borrowers:
            borrower_combo.addItem(borrower.name, borrower.id)

        if not borrowers:
            borrower_combo.addItem("No borrowers available", "")
        form_layout.addRow("Borrower:", borrower_combo)

        return_date_edit = QDateEdit()
        return_date_edit.setDate(QDate.currentDate().addDays(7))
        return_date_edit.setCalendarPopup(True)
        form_layout.addRow("Expected Return:", return_date_edit)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        form_layout.addRow("Notes:", notes_input)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()

        checkout_btn = QPushButton("🚀 Checkout Loadout")
        checkout_btn.setStyleSheet("background-color: #202060; font-weight: bold;")

        def perform_checkout():
            if not borrowers:
                QMessageBox.warning(dialog, "Error", "No borrowers available")
                return

            borrower_idx = borrower_combo.currentIndex()
            if borrower_idx < 0 or not borrowers[borrower_idx].id:
                QMessageBox.warning(dialog, "Error", "Select a valid borrower")
                return

            borrower = borrowers[borrower_idx]
            expected_return = datetime(
                return_date_edit.date().year(),
                return_date_edit.date().month(),
                return_date_edit.date().day(),
            )

            checkout_id, messages = self.loadout_repo.checkout_loadout(
                loadout.id, borrower.id, expected_return
            )

            if checkout_id:
                message = f"Loadout '{loadout.name}' checked out to {borrower.name}!"
                self.refresh_all()
                dialog.accept()
            else:
                error_message = "Failed to checkout loadout.\n\n"
                if messages:
                    error_message += "Errors:\n" + "\n".join(f"• {m}" for m in messages)
                QMessageBox.critical(dialog, "Checkout Failed", error_message)

        checkout_btn.clicked.connect(perform_checkout)
        btn_layout.addWidget(checkout_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def delete_loadout(self):
        row = self.loadout_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a loadout")
            return

        loadouts = self.loadout_repo.get_all()
        selected = loadouts[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete loadout '{selected.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.loadout_repo.delete(selected.id)
            self.refresh_loadouts()

    # ============== CHECKOUTS TAB ==============

    def create_checkouts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.checkout_table = QTableWidget()
        self.checkout_table.setColumnCount(5)
        self.checkout_table.setHorizontalHeaderLabels(
            ["Item", "Type", "Borrower", "Checkout Date", "Notes"]
        )
        self.checkout_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.checkout_table)

        btn_layout = QHBoxLayout()

        checkout_btn = QPushButton("Checkout Item")
        checkout_btn.clicked.connect(self.open_checkout_item_dialog)
        btn_layout.addWidget(checkout_btn)

        return_btn = QPushButton("Return Selected")
        return_btn.setStyleSheet("background-color: #206B20;")
        return_btn.clicked.connect(self.return_checkout)
        btn_layout.addWidget(return_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_checkouts(self):
        self.checkout_table.setRowCount(0)
        checkouts = self.checkout_repo.get_active_checkouts()

        firearms = {f.id: f.name for f in self.firearm_repo.get_all()}
        soft_gear = {g.id: g.name for g in self.gear_repo.get_all_soft_gear()}
        nfa_items = {n.id: n.name for n in self.gear_repo.get_all_nfa_items()}

        for i, c in enumerate(checkouts):
            self.checkout_table.insertRow(i)

            item_type = (
                c.item_type.value if hasattr(c.item_type, "value") else c.item_type
            )

            if item_type == GearCategory.FIREARM.value:
                item_name = f"🔫 {firearms.get(c.item_id, c.item_id)}"
            elif item_type == GearCategory.SOFT_GEAR.value:
                item_name = f"🎒 {soft_gear.get(c.item_id, c.item_id)}"
            elif item_type == GearCategory.NFA_ITEM.value:
                item_name = f"🔇 {nfa_items.get(c.item_id, c.item_id)}"
            else:
                item_name = c.item_id

            self.checkout_table.setItem(i, 0, QTableWidgetItem(item_name))
            self.checkout_table.setItem(i, 1, QTableWidgetItem(item_type))
            self.checkout_table.setItem(i, 2, QTableWidgetItem(c.borrower_name))
            self.checkout_table.setItem(
                i, 3, QTableWidgetItem(c.checkout_date.strftime("%Y-%m-%d"))
            )
            self.checkout_table.setItem(i, 4, QTableWidgetItem(c.notes or ""))

    def open_checkout_item_dialog(self):
        borrowers = self.checkout_repo.get_all_borrowers()
        if not borrowers:
            QMessageBox.warning(self, "Error", "Add a borrower first (Borrowers tab)")
            return

        firearms = [f for f in self.firearm_repo.get_all() if f.status == "AVAILABLE"]
        soft_gear = [
            g for g in self.gear_repo.get_all_soft_gear() if g.status == "AVAILABLE"
        ]

        if not firearms and not soft_gear:
            QMessageBox.warning(self, "Error", "No available items to checkout")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Checkout Item")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        item_combo = QComboBox()
        items_data = []
        for f in firearms:
            item_combo.addItem(f"🔫 {f.name}")
            items_data.append((f.id, GearCategory.FIREARM.value))
        for g in soft_gear:
            item_combo.addItem(f"🎒 {g.name}")
            items_data.append((g.id, GearCategory.SOFT_GEAR.value))
        layout.addRow("Item:", item_combo)

        borrower_combo = QComboBox()
        for b in borrowers:
            borrower_combo.addItem(b.name)
        layout.addRow("Borrower:", borrower_combo)

        return_date = QDateEdit()
        return_date.setDate(QDate.currentDate().addDays(7))
        return_date.setCalendarPopup(True)
        layout.addRow("Expected Return:", return_date)

        notes_input = QLineEdit()
        layout.addRow("Notes:", notes_input)

        checkout_btn = QPushButton("Checkout")

        def save():
            idx = item_combo.currentIndex()
            item_id, item_type = items_data[idx]
            borrower = borrowers[borrower_combo.currentIndex()]

            exp_return = datetime(
                return_date.date().year(),
                return_date.date().month(),
                return_date.date().day(),
            )

            checkout = Checkout(
                id=str(uuid.uuid4()),
                item_id=item_id,
                item_type=item_type,
                borrower_name=borrower.name,
                checkout_date=datetime.now(),
                expected_return=exp_return,
                actual_return=None,
                notes=notes_input.text(),
            )
            self.checkout_repo.add_checkout(checkout)
            self.refresh_checkouts()
            dialog.accept()

        checkout_btn.clicked.connect(save)
        layout.addRow(checkout_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def return_checkout(self):
        row = self.checkout_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a checkout first")
            return

        checkouts = self.checkout_repo.get_active_checkouts()
        if row >= len(checkouts):
            return
        selected = checkouts[row]

        loadout_checkout = self.loadout_repo.get_loadout_checkout(selected.id)

        if loadout_checkout:
            self.open_return_loadout_dialog(selected, loadout_checkout)
        else:
            self.open_return_item_dialog(selected)

    def open_return_item_dialog(self, checkout):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Return: {checkout.item_id}")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        info_group = QGroupBox("Return Information")
        info_layout = QFormLayout()

        item_label = QLabel(checkout.item_id)
        info_layout.addRow("Item:", item_label)

        borrower_label = QLabel(checkout.borrower_name)
        info_layout.addRow("Borrower:", borrower_label)

        checkout_date = checkout.checkout_date.strftime("%Y-%m-%d")
        info_layout.addRow("Checked Out:", checkout_date)

        if checkout.expected_return:
            info_layout.addRow(
                "Expected Return:", checkout.expected_return.strftime("%Y-%m-%d")
            )

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        rounds_group = QGroupBox("Round Count (if firearm)")
        rounds_layout = QFormLayout()

        is_firearm = checkout.item_type == GearCategory.FIREARM.value

        if is_firearm:
            self.return_rounds_spinbox = QSpinBox()
            self.return_rounds_spinbox.setMinimum(0)
            self.return_rounds_spinbox.setMaximum(9999)
            self.return_rounds_spinbox.setValue(0)
            rounds_layout.addRow("Rounds Fired:", self.return_rounds_spinbox)
        else:
            self.return_rounds_spinbox = None
            rounds_layout.addRow(QLabel("N/A for this item type"))

        rounds_group.setLayout(rounds_layout)
        layout.addWidget(rounds_group)

        ammo_group = QGroupBox("Ammunition Details")
        ammo_layout = QFormLayout()

        ammo_type_combo = QComboBox()
        ammo_type_combo.addItems(["Normal", "Corrosive", "Lead", "Custom"])
        ammo_type_combo.setCurrentText("Normal")
        ammo_layout.addRow("Ammo Type:", ammo_type_combo)

        self.return_custom_ammo = QLineEdit()
        self.return_custom_ammo.setPlaceholderText("Enter custom ammo type")
        self.return_custom_ammo.setVisible(False)
        ammo_layout.addRow("Custom Type:", self.return_custom_ammo)

        ammo_type_combo.currentTextChanged.connect(
            lambda text: self.return_custom_ammo.setVisible(text == "Custom")
        )

        ammo_group.setLayout(ammo_layout)
        layout.addWidget(ammo_group)

        rain_checkbox = QCheckBox("Exposed to rain during use?")
        layout.addWidget(rain_checkbox)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        notes_input.setPlaceholderText("Additional notes about this checkout...")
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(notes_input)

        btn_layout = QHBoxLayout()

        return_btn = QPushButton("✅ Return Item")
        return_btn.setStyleSheet("background-color: #206B20; font-weight: bold;")

        def perform_return():
            rounds_fired = (
                self.return_rounds_spinbox.value() if self.return_rounds_spinbox else 0
            )

            ammo_type = ammo_type_combo.currentText()
            if ammo_type == "Custom":
                ammo_type = self.return_custom_ammo.text() or "Unknown"

            notes = notes_input.toPlainText()

            self.checkout_repo.return_item(checkout.id)

            if is_firearm and rounds_fired > 0:
                self.firearm_repo.update_rounds(checkout.item_id, rounds_fired)
                log = MaintenanceLog(
                    id=str(uuid.uuid4()),
                    item_id=checkout.item_id,
                    item_type=GearCategory.FIREARM.value,
                    log_type=MaintenanceType.FIRED_ROUNDS.value,
                    date=datetime.now(),
                    details=f"Rounds fired: {rounds_fired}",
                    ammo_count=rounds_fired,
                    photo_path=None,
                )
                self.gear_repo.add_maintenance_log(log)

            if rain_checkbox.isChecked():
                log = MaintenanceLog(
                    id=str(uuid.uuid4()),
                    item_id=checkout.item_id,
                    item_type=GearCategory.FIREARM.value,
                    log_type=MaintenanceType.RAIN_EXPOSURE.value,
                    date=datetime.now(),
                    details="Rain exposure during use",
                    ammo_count=None,
                    photo_path=None,
                )
                self.gear_repo.add_maintenance_log(log)

            if ammo_type and ammo_type not in ["Normal", "Unknown"]:
                log = MaintenanceLog(
                    id=str(uuid.uuid4()),
                    item_id=checkout.item_id,
                    item_type=GearCategory.FIREARM.value,
                    log_type=MaintenanceType.CORROSIVE_AMMO.value
                    if "corrosive" in ammo_type.lower()
                    else MaintenanceType.LEAD_AMMO.value,
                    date=datetime.now(),
                    details=f"Ammo type: {ammo_type}",
                    ammo_count=None,
                    photo_path=None,
                )
                self.gear_repo.add_maintenance_log(log)

            self.refresh_all()
            dialog.accept()

        return_btn.clicked.connect(perform_return)
        btn_layout.addWidget(return_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def open_return_loadout_dialog(self, checkout, loadout_checkout: LoadoutCheckout):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Return Loadout: {checkout.item_id}")
        dialog.setMinimumSize(700, 600)

        layout = QVBoxLayout(dialog)

        info_group = QGroupBox("Loadout Return Information")
        info_layout = QFormLayout()

        loadout = None
        all_loadouts = self.loadout_repo.get_all()
        for lo in all_loadouts:
            if lo.id == loadout_checkout.loadout_id:
                loadout = lo
                break

        if loadout:
            name_label = QLabel(loadout.name)
            info_layout.addRow("Loadout:", name_label)

            desc_label = QLabel(loadout.description if loadout.description else "None")
            info_layout.addRow("Description:", desc_label)

        loadout_items = self.loadout_repo.get_items(loadout_checkout.loadout_id)
        firearms_in_loadout = [
            item
            for item in loadout_items
            if item.item_type == GearCategory.FIREARM.value
        ]

        self.firearm_ammo_inputs = {}
        all_firearms = self.firearm_repo.get_all()
        firearm_dict = {f.id: f for f in all_firearms}

        loadout_consumables = self.loadout_repo.get_consumables(
            loadout_checkout.loadout_id
        )
        all_consumables = self.consumable_repo.get_all()
        consumable_dict = {c.id: c for c in all_consumables}

        if firearms_in_loadout:
            ammo_section = QLabel("<b>Firearms & Ammunition Used:</b>")
            ammo_section.setStyleSheet("margin-top: 10px;")
            info_layout.addRow(ammo_section)

            for item in firearms_in_loadout:
                firearm = firearm_dict.get(item.item_id)
                if firearm:
                    fw_label = QLabel(f"{firearm.name}:")

                    ammo_combo = QComboBox()
                    ammo_combo.addItem("None", None)
                    ammo_combo.addItem("Unknown - Select ammo", "")
                    for lc in loadout_consumables:
                        cons = consumable_dict.get(lc.consumable_id)
                        if cons:
                            ammo_combo.addItem(
                                f"{cons.name} ({lc.quantity} {cons.unit})",
                                lc.consumable_id,
                            )

                    rounds_spinbox = QSpinBox()
                    rounds_spinbox.setMinimum(0)
                    rounds_spinbox.setMaximum(9999)
                    rounds_spinbox.setValue(0)

                    self.firearm_ammo_inputs[firearm.id] = (ammo_combo, rounds_spinbox)

                    ammo_row = QHBoxLayout()
                    ammo_row.addWidget(fw_label)
                    ammo_row.addWidget(ammo_combo)
                    ammo_row.addWidget(QLabel("Rounds:"))
                    ammo_row.addWidget(rounds_spinbox)
                    ammo_row.addStretch()

                    info_layout.addRow("", QWidget())
                    info_layout.addRow(fw_label, ammo_combo)
                    info_layout.addRow("Rounds fired:", rounds_spinbox)

        rain_checkbox = QCheckBox("Exposed to rain during use?")
        info_layout.addRow("", rain_checkbox)

        custom_ammo_input = QLineEdit()
        custom_ammo_input.setPlaceholderText(
            "Enter custom ammo type (if not in loadout)"
        )
        info_layout.addRow("Custom Ammo Type:", custom_ammo_input)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(100)
        notes_input.setPlaceholderText("Additional notes about this trip...")
        info_layout.addRow("Notes:", notes_input)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        if loadout_checkout.loadout_id:
            consumables_group = QGroupBox("Consumables - Return Unused Items")
            cons_box = QVBoxLayout()

            info_text = QLabel("Adjust quantities below for any unused items:")
            info_text.setStyleSheet(
                "color: #888; font-style: italic; margin-bottom: 10px;"
            )
            cons_box.addWidget(info_text)

            self.restock_inputs = {}
            for lc in loadout_consumables:
                cons = consumable_dict.get(lc.consumable_id)
                if cons:
                    row_layout = QHBoxLayout()
                    checkbox = QCheckBox(f"{cons.name}:")
                    checkbox.setChecked(True)
                    checkbox.setProperty("consumable_id", lc.consumable_id)

                    spinbox = QSpinBox()
                    spinbox.setMinimum(0)
                    spinbox.setMaximum(100000)
                    spinbox.setValue(lc.quantity)

                    row_layout.addWidget(checkbox)
                    row_layout.addWidget(spinbox)
                    row_layout.addWidget(QLabel(f"{cons.unit}"))
                    row_layout.addStretch()

                    self.restock_inputs[lc.consumable_id] = (checkbox, spinbox)
                    cons_box.addLayout(row_layout)

            consumables_group.setLayout(cons_box)
            layout.addWidget(consumables_group)

        btn_layout = QHBoxLayout()

        return_btn = QPushButton("✅ Return Loadout")
        return_btn.setStyleSheet("background-color: #206B20; font-weight: bold;")

        def perform_return():
            ammo_used_per_consumable = {}
            rounds_fired_dict = {}

            for fw_id, (ammo_combo, rounds_spinbox) in self.firearm_ammo_inputs.items():
                rounds = rounds_spinbox.value()
                rounds_fired_dict[fw_id] = rounds

                cons_id = ammo_combo.currentData()
                if cons_id and rounds > 0:
                    if cons_id in ammo_used_per_consumable:
                        ammo_used_per_consumable[cons_id] += rounds
                    else:
                        ammo_used_per_consumable[cons_id] = rounds

            ammo_type = (
                custom_ammo_input.text() if custom_ammo_input.text() else "Normal"
            )
            notes = notes_input.toPlainText()

            loadout_items = self.loadout_repo.get_items(loadout_checkout.loadout_id)

            for item in loadout_items:
                existing_checkout = self.checkout_repo.get_checkout_by_item(
                    item.item_id
                )
                if existing_checkout:
                    self.checkout_repo.return_item(existing_checkout.id)

                item_type = (
                    item.item_type.value
                    if hasattr(item.item_type, "value")
                    else item.item_type
                )
                if item_type == GearCategory.FIREARM.value:
                    self.firearm_repo.update_status(item.item_id, "AVAILABLE")
                elif item_type == GearCategory.SOFT_GEAR.value:
                    self.gear_repo.update_soft_gear_status(item.item_id, "AVAILABLE")
                elif item_type == GearCategory.NFA_ITEM.value:
                    self.gear_repo.update_nfa_status(item.item_id, "AVAILABLE")

            self.loadout_repo.return_from_trip(
                loadout_checkout.loadout_id,
                checkout.id,
                rounds_fired_dict,
                rain_checkbox.isChecked(),
                ammo_type,
                notes,
                [],
            )

            for fw_id, rounds in rounds_fired_dict.items():
                if rounds > 0:
                    self.firearm_repo.update_rounds(fw_id, rounds)
                    log = MaintenanceLog(
                        id=str(uuid.uuid4()),
                        item_id=fw_id,
                        item_type=GearCategory.FIREARM.value,
                        log_type=MaintenanceType.FIRED_ROUNDS.value,
                        date=datetime.now(),
                        details=f"Rounds fired: {rounds}",
                        ammo_count=rounds,
                        photo_path=None,
                    )
                    self.gear_repo.add_maintenance_log(log)

                    if rain_checkbox.isChecked():
                        rain_log = MaintenanceLog(
                            id=str(uuid.uuid4()),
                            item_id=fw_id,
                            item_type=GearCategory.FIREARM.value,
                            log_type=MaintenanceType.RAIN_EXPOSURE.value,
                            date=datetime.now(),
                            details="Rain exposure during hunt/trip",
                            ammo_count=None,
                            photo_path=None,
                        )
                        self.gear_repo.add_maintenance_log(rain_log)

                    if ammo_type and ammo_type not in ["Normal", ""]:
                        ammo_log = MaintenanceLog(
                            id=str(uuid.uuid4()),
                            item_id=fw_id,
                            item_type=GearCategory.FIREARM.value,
                            log_type=MaintenanceType.CORROSIVE_AMMO.value
                            if "corrosive" in ammo_type.lower()
                            else MaintenanceType.LEAD_AMMO.value,
                            date=datetime.now(),
                            details=f"Ammo type: {ammo_type}",
                            ammo_count=None,
                            photo_path=None,
                        )
                        self.gear_repo.add_maintenance_log(amo_log)

            if hasattr(self, "restock_inputs"):
                for cons_id, (checkbox, spinbox) in self.restock_inputs.items():
                    if checkbox.isChecked():
                        returned_qty = spinbox.value()
                        if returned_qty > 0:
                            self.consumable_repo.update_quantity(
                                cons_id, returned_qty, "RESTOCK", "Loadout return"
                            )

            self.refresh_all()
            dialog.accept()

        return_btn.clicked.connect(perform_return)
        btn_layout.addWidget(return_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()

    # ============== BORROWERS TAB ==============

    def create_borrowers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.borrower_table = QTableWidget()
        self.borrower_table.setColumnCount(4)
        self.borrower_table.setHorizontalHeaderLabels(
            ["Name", "Phone", "Email", "Notes"]
        )
        self.borrower_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.borrower_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Borrower")
        add_btn.clicked.connect(self.open_add_borrower_dialog)
        btn_layout.addWidget(add_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_borrower)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_borrowers(self):
        self.borrower_table.setRowCount(0)
        borrowers = self.checkout_repo.get_all_borrowers()

        for i, b in enumerate(borrowers):
            self.borrower_table.insertRow(i)
            self.borrower_table.setItem(i, 0, QTableWidgetItem(b.name))
            self.borrower_table.setItem(i, 1, QTableWidgetItem(b.phone or ""))
            self.borrower_table.setItem(i, 2, QTableWidgetItem(b.email or ""))
            self.borrower_table.setItem(i, 3, QTableWidgetItem(b.notes or ""))

    def open_add_borrower_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Borrower")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit()
        layout.addRow("Name:", name_input)

        phone_input = QLineEdit()
        layout.addRow("Phone:", phone_input)

        email_input = QLineEdit()
        layout.addRow("Email:", email_input)

        notes_input = QTextEdit()
        layout.addRow("Notes:", notes_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            borrower = Borrower(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                phone=phone_input.text(),
                email=email_input.text(),
                notes=notes_input.toPlainText(),
            )
            self.checkout_repo.add_borrower(borrower)
            self.refresh_borrowers()

    def delete_borrower(self):
        row = self.borrower_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a borrower")
            return

        borrowers = self.checkout_repo.get_all_borrowers()
        selected = borrowers[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete borrower '{selected.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.checkout_repo.delete_borrower(selected.id)
            self.refresh_borrowers()

    # ============== NFA ITEMS TAB ==============

    def create_nfa_items_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.nfa_table = QTableWidget()
        self.nfa_table.setColumnCount(5)
        self.nfa_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Serial", "Tax Stamp", "Status"]
        )
        self.nfa_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.nfa_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add NFA Item")
        add_btn.clicked.connect(self.open_add_nfa_dialog)
        btn_layout.addWidget(add_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_nfa_item)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_nfa_items(self):
        self.nfa_table.setRowCount(0)
        items = self.gear_repo.get_all_nfa_items()

        for i, item in enumerate(items):
            self.nfa_table.insertRow(i)
            self.nfa_table.setItem(i, 0, QTableWidgetItem(item.name))
            self.nfa_table.setItem(
                i,
                1,
                QTableWidgetItem(
                    item.nfa_type.value
                    if hasattr(item.nfa_type, "value")
                    else str(item.nfa_type)
                ),
            )
            self.nfa_table.setItem(i, 2, QTableWidgetItem(item.serial_number))
            self.nfa_table.setItem(i, 3, QTableWidgetItem(item.tax_stamp_id))
            self.nfa_table.setItem(i, 4, QTableWidgetItem(item.status))

    def open_add_nfa_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add NFA Item")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit()
        layout.addRow("Name:", name_input)

        type_combo = QComboBox()
        for nfa_type in NFAItemType:
            type_combo.addItem(nfa_type.value, nfa_type)
        layout.addRow("NFA Type:", type_combo)

        manufacturer_input = QLineEdit()
        layout.addRow("Manufacturer:", manufacturer_input)

        serial_input = QLineEdit()
        layout.addRow("Serial #:", serial_input)

        tax_stamp_input = QLineEdit()
        layout.addRow("Tax Stamp ID:", tax_stamp_input)

        caliber_input = QLineEdit()
        layout.addRow("Caliber/Bore:", caliber_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            item = NFAItem(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                nfa_type=type_combo.currentData(),
                manufacturer=manufacturer_input.text(),
                serial_number=serial_input.text(),
                tax_stamp_id=tax_stamp_input.text(),
                caliber_bore=caliber_input.text(),
                purchase_date=datetime.now(),
            )
            self.gear_repo.add_nfa_item(item)
            self.refresh_nfa_items()

    def delete_nfa_item(self):
        row = self.nfa_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an item")
            return

        items = self.gear_repo.get_all_nfa_items()
        selected = items[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete '{selected.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.gear_repo.delete_nfa_item(selected.id)
            self.refresh_nfa_items()

    # ============== TRANSFERS TAB ==============

    def create_transfers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.transfer_table = QTableWidget()
        self.transfer_table.setColumnCount(5)
        self.transfer_table.setHorizontalHeaderLabels(
            ["Firearm", "Buyer", "Date", "Price", "Notes"]
        )
        self.transfer_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.transfer_table)

        btn_layout = QHBoxLayout()

        view_btn = QPushButton("View Details")
        view_btn.clicked.connect(self.view_transfer_details)
        btn_layout.addWidget(view_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_transfers(self):
        self.transfer_table.setRowCount(0)
        transfers = self.transfer_repo.get_all()

        firearms = self.firearm_repo.get_all()
        firearm_dict = {f.id: f.name for f in firearms}

        for i, t in enumerate(transfers):
            self.transfer_table.insertRow(i)
            name = firearm_dict.get(t.firearm_id, t.firearm_id)
            self.transfer_table.setItem(i, 0, QTableWidgetItem(name))
            self.transfer_table.setItem(i, 1, QTableWidgetItem(t.buyer_name))
            self.transfer_table.setItem(
                i, 2, QTableWidgetItem(t.transfer_date.strftime("%Y-%m-%d"))
            )
            price = f"${t.sale_price:.2f}" if t.sale_price else ""
            self.transfer_table.setItem(i, 3, QTableWidgetItem(price))
            self.transfer_table.setItem(i, 4, QTableWidgetItem(t.notes or ""))

    def view_transfer_details(self):
        row = self.transfer_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a transfer")
            return

        transfers = self.transfer_repo.get_all()
        selected = transfers[row]

        QMessageBox.information(
            self,
            "Transfer Details",
            f"Buyer: {selected.buyer_name}\n"
            f"Address: {selected.buyer_address}\n"
            f"DL: {selected.buyer_dl_number}\n"
            f"Date: {selected.transfer_date.strftime('%Y-%m-%d')}\n"
            f"Price: ${selected.sale_price:.2f}\n"
            f"Notes: {selected.notes}",
        )

    # ============== MAINTENANCE LOGGING ==============

    def open_log_dialog(self, item_type):
        dialog = QDialog(self)
        dialog.setWindowTitle("Log Maintenance")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        type_combo = QComboBox()
        for mtype in MaintenanceType:
            type_combo.addItem(mtype.value, mtype)
        layout.addRow("Type:", type_combo)

        details_input = QTextEdit()
        layout.addRow("Details:", details_input)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            log = MaintenanceLog(
                id=str(uuid.uuid4()),
                item_id="",
                item_type=item_type,
                log_type=type_combo.currentData(),
                date=datetime.now(),
                details=details_input.toPlainText(),
            )
            self.checkout_repo.add_log(log)

    def view_item_history(self, item_type):
        QMessageBox.information(
            self, "History", "View history feature - select an item in the table first"
        )

    def create_import_export_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel(
            "Import/Export all inventory data to CSV format for backups or migration.\n"
            "Exports preserve IDs and relationships. Import validates data before applying changes."
        )
        info_label.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        export_group = QGroupBox("Export Data")
        export_layout = QVBoxLayout()

        export_btn = QPushButton("Export All Data to CSV")
        export_btn.clicked.connect(self.export_all_data)
        export_layout.addWidget(export_btn)

        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

        import_group = QGroupBox("Import Data")
        import_layout = QVBoxLayout()

        preview_btn = QPushButton("Preview CSV (Dry Run)")
        preview_btn.clicked.connect(self.preview_import)
        import_layout.addWidget(preview_btn)

        import_btn = QPushButton("Import from CSV")
        import_btn.clicked.connect(self.import_csv_data)
        import_layout.addWidget(import_btn)

        import_group.setLayout(import_layout)
        layout.addWidget(import_group)

        template_group = QGroupBox("Templates")
        template_layout = QVBoxLayout()

        full_template_btn = QPushButton("Generate Complete Template")
        full_template_btn.clicked.connect(self.generate_full_template)
        template_layout.addWidget(full_template_btn)

        single_template_layout = QHBoxLayout()
        template_combo = QComboBox()
        template_combo.addItems(
            [
                "Firearms",
                "NFA Items",
                "Soft Gear",
                "Attachments",
                "Consumables",
                "Reload Batches",
                "Loadouts",
                "Borrowers",
            ]
        )
        single_template_layout.addWidget(QLabel("Entity Type:"))
        single_template_layout.addWidget(template_combo)

        single_template_btn = QPushButton("Generate")
        single_template_btn.clicked.connect(
            lambda: self.generate_single_template(template_combo.currentText())
        )
        single_template_layout.addWidget(single_template_btn)

        template_layout.addLayout(single_template_layout)
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def export_all_data(self):
        from pathlib import Path

        default_name = (
            f"geartracker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export All Data",
            str(Path.home() / "Documents" / default_name),
            "CSV Files (*.csv)",
        )
        if file_path:
            try:
                self.import_export_svc.export_complete_csv(Path(file_path))
                QMessageBox.information(
                    self, "Export Complete", f"Data exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export:\n{str(e)}"
                )

    def preview_import(self):
        from pathlib import Path

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", str(Path.home() / "Documents"), "CSV Files (*.csv)"
        )
        if file_path:
            try:
                result = self.import_export_svc.preview_import(Path(file_path))
                self._show_import_results("Preview Results", result)
            except Exception as e:
                QMessageBox.critical(
                    self, "Preview Error", f"Failed to preview:\n{str(e)}"
                )

    def import_csv_data(self):
        from pathlib import Path

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", str(Path.home() / "Documents"), "CSV Files (*.csv)"
        )
        if file_path:
            try:
                result = self.import_export_svc.import_complete_csv(Path(file_path))
                self._show_import_results("Import Results", result)
                self.refresh_all()
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Error", f"Failed to import:\n{str(e)}"
                )

    def generate_full_template(self):
        from pathlib import Path

        default_name = f"geartracker_template_{datetime.now().strftime('%Y%m%d')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Template",
            str(Path.home() / "Documents" / default_name),
            "CSV Files (*.csv)",
        )
        if file_path:
            try:
                self.import_export_svc.generate_csv_template(Path(file_path), None)
                QMessageBox.information(
                    self, "Template Created", f"Template saved to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Template Error", f"Failed to generate template:\n{str(e)}"
                )

    def generate_single_template(self, entity_type: str):
        from pathlib import Path

        entity_map = {
            "Firearms": "firearms",
            "NFA Items": "nfa_items",
            "Soft Gear": "soft_gear",
            "Attachments": "attachments",
            "Consumables": "consumables",
            "Reload Batches": "reload_batches",
            "Loadouts": "loadouts",
            "Borrowers": "borrowers",
        }
        csv_entity = entity_map.get(entity_type)
        if not csv_entity:
            QMessageBox.warning(
                self, "Template Error", f"Unknown entity type: {entity_type}"
            )
            return
        default_name = (
            f"geartracker_template_{csv_entity}_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Template",
            str(Path.home() / "Documents" / default_name),
            "CSV Files (*.csv)",
        )
        if file_path:
            try:
                self.import_export_svc.generate_csv_template(
                    Path(file_path), csv_entity
                )
                QMessageBox.information(
                    self, "Template Created", f"Template saved to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Template Error", f"Failed to generate template:\n{str(e)}"
                )

    def _show_import_results(self, title: str, result):
        summary = f"Total rows: {result.total_rows}\n"
        summary += f"Imported: {result.imported}\n"
        summary += f"Skipped: {result.skipped}\n"
        summary += f"Overwritten: {result.overwritten}\n"
        summary += f"Errors: {len(result.errors)}\n"
        summary += f"Warnings: {len(result.warnings)}"

        details = ""
        if result.entity_stats:
            details += "\n=== Entity Statistics ===\n"
            for entity, count in result.entity_stats.items():
                details += f"{entity}: {count}\n"
        if result.errors:
            details += "\n=== Errors ===\n"
            for error in result.errors:
                details += f"• {error}\n"
        if result.warnings:
            details += "\n=== Warnings ===\n"
            for warning in result.warnings:
                details += f"• {warning}\n"

        full_message = summary + "\n\n" + details
        QMessageBox.information(self, title, full_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GearTrackerMainWindow()
    window.show()
    sys.exit(app.exec())
