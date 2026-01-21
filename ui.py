import sys
import uuid
import sqlite3
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
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QPalette

from gear_tracker import (
    GearRepository,
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
)

from csv_import_export import (
    create_import_export_tab,
    DuplicateResolutionDialog,
    ImportProgressDialog,
)


class GearTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.repo = GearRepository()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Gear Tracker")
        self.setGeometry(100, 100, 1200, 700)

        # Main tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create tabs
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
        # Refresh all on startup
        self.refresh_all()

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

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_selected_firearm)
        btn_layout.addWidget(delete_btn)

        transfer_btn = QPushButton("📤 Transfer/Sell")
        transfer_btn.setStyleSheet("background-color: #6B6B20;")  # Dark yellow/gold
        transfer_btn.clicked.connect(self.open_transfer_dialog)
        btn_layout.addWidget(transfer_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_firearms(self):
        self.firearm_table.setRowCount(0)
        firearms = self.repo.get_all_firearms()

        for i, fw in enumerate(firearms):
            self.firearm_table.insertRow(i)
            self.firearm_table.setItem(i, 0, QTableWidgetItem(fw.name))
            self.firearm_table.setItem(i, 1, QTableWidgetItem(fw.caliber))
            self.firearm_table.setItem(i, 2, QTableWidgetItem(fw.serial_number))

            status_item = QTableWidgetItem(fw.status.value)
            if fw.status == CheckoutStatus.CHECKED_OUT:
                status_item.setBackground(QColor(255, 200, 200))
            if fw.needs_maintenance:
                status_item.setBackground(QColor(255, 100, 100))
                status_item.setForeground(QColor(255, 255, 255))
            self.firearm_table.setItem(i, 3, status_item)

            rounds_item = QTableWidgetItem(str(fw.rounds_fired))
            maint_status = self.repo.get_maintenance_status(fw.id)
            if maint_status["needs_maintenance"]:
                rounds_item.setBackground(QColor(255, 150, 150))
                rounds_item.setToolTip("\n".join(maint_status["reasons"]))
            else:
                if fw.clean_interval_rounds:
                    pct = fw.rounds_fired / fw.clean_interval_rounds
                    if pct >= 0.8:
                        rounds_item.setBackground(QColor(255, 255, 150))
                        rounds_item.setToolTip(
                            f"{int(pct * 100)}% to clean interval ({fw.clean_interval_rounds} rounds)"
                        )
            self.firearm_table.setItem(i, 4, rounds_item)

            last_clean = self.repo.last_cleaning_date(fw.id)
            clean_text = last_clean.strftime("%Y-%m-%d") if last_clean else "Never"
            clean_item = QTableWidgetItem(clean_text)
            if fw.oil_interval_days and last_clean:
                days_since_clean = (datetime.now() - last_clean).days
                if days_since_clean >= fw.oil_interval_days:
                    clean_item.setBackground(QColor(255, 200, 100))
                    clean_item.setToolTip(
                        f"Needs oil ({days_since_clean} days since last clean, interval: {fw.oil_interval_days})"
                    )
            self.firearm_table.setItem(i, 5, clean_item)

            self.firearm_table.setItem(i, 6, QTableWidgetItem(fw.notes))

    def delete_selected_firearm(self):
        row = self.firearm_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a firearm to delete")
            return

        firearms = self.repo.get_all_firearms()
        selected = firearms[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Permanently delete '{selected.name}'?\n\nThis will also delete maintenance logs and checkout history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_firearm(selected.id)
            self.refresh_firearms()
            QMessageBox.information(
                self, "Deleted", f"'{selected.name}' has been deleted."
            )

    def open_transfer_dialog(self):
        row = self.firearm_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a firearm to transfer")
            return

        firearms = self.repo.get_all_firearms()
        selected = firearms[row]

        # Check if checked out
        if selected.status == CheckoutStatus.CHECKED_OUT:
            QMessageBox.warning(
                self, "Error", "Cannot transfer a checked-out firearm. Return it first."
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Transfer: {selected.name}")
        dialog.setMinimumWidth(500)

        layout = QFormLayout()

        # Firearm info (read-only)
        info_group = QGroupBox("Firearm Being Transferred")
        info_layout = QFormLayout()
        info_layout.addRow("Name:", QLabel(selected.name))
        info_layout.addRow("Caliber:", QLabel(selected.caliber))
        info_layout.addRow("Serial #:", QLabel(selected.serial_number))
        info_group.setLayout(info_layout)
        layout.addRow(info_group)

        # Buyer info
        buyer_group = QGroupBox("Buyer Information (Required)")
        buyer_layout = QFormLayout()

        buyer_name_input = QLineEdit()
        buyer_name_input.setPlaceholderText("Full legal name")
        buyer_layout.addRow("Name*:", buyer_name_input)

        buyer_address_input = QTextEdit()
        buyer_address_input.setMaximumHeight(60)
        buyer_address_input.setPlaceholderText("Full address (verify TX residency)")
        buyer_layout.addRow("Address*:", buyer_address_input)

        buyer_dl_input = QLineEdit()
        buyer_dl_input.setPlaceholderText("TX DL# (e.g., 12345678)")
        buyer_layout.addRow("DL Number*:", buyer_dl_input)

        buyer_ltc_input = QLineEdit()
        buyer_ltc_input.setPlaceholderText("Optional - TX LTC number")
        buyer_layout.addRow("LTC Number:", buyer_ltc_input)

        buyer_group.setLayout(buyer_layout)
        layout.addRow(buyer_group)

        # Optional fields
        optional_group = QGroupBox("Optional Information")
        optional_layout = QFormLayout()

        price_spin = QSpinBox()
        price_spin.setRange(0, 100000)
        price_spin.setPrefix("$")
        optional_layout.addRow("Sale Price:", price_spin)

        ffl_dealer_input = QLineEdit()
        ffl_dealer_input.setPlaceholderText("If using FFL dealer")
        optional_layout.addRow("FFL Dealer:", ffl_dealer_input)

        ffl_license_input = QLineEdit()
        ffl_license_input.setPlaceholderText("FFL license number")
        optional_layout.addRow("FFL License:", ffl_license_input)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(60)
        notes_input.setPlaceholderText(
            "e.g., Bill of sale signed, private sale, friend from church"
        )
        optional_layout.addRow("Notes:", notes_input)

        optional_group.setLayout(optional_layout)
        layout.addRow(optional_group)

        # Warning
        warning = QLabel(
            "⚠️ WARNING: This will mark the firearm as TRANSFERRED and move it to the Transfers tab.\n"
            "This action cannot be undone. Maintain this record as required by law."
        )
        warning.setStyleSheet(
            "color: #FF6B6B; font-weight: bold; padding: 10px; background-color: #3C2020;"
        )
        warning.setWordWrap(True)
        layout.addRow(warning)

        # Buttons
        btn_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        transfer_btn = QPushButton("Record Transfer")
        transfer_btn.setStyleSheet("background-color: #6B6B20; font-weight: bold;")

        def save_transfer():
            if (
                not buyer_name_input.text()
                or not buyer_address_input.toPlainText()
                or not buyer_dl_input.text()
            ):
                QMessageBox.warning(
                    dialog, "Error", "Buyer name, address, and DL number are required"
                )
                return

            reply = QMessageBox.question(
                dialog,
                "Confirm Transfer",
                f"Record transfer of '{selected.name}' to {buyer_name_input.text()}?\n\n"
                "This will move the firearm to the Transfers tab and cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                transfer = Transfer(
                    id=str(uuid.uuid4()),
                    firearm_id=selected.id,
                    transfer_date=datetime.now(),
                    buyer_name=buyer_name_input.text(),
                    buyer_address=buyer_address_input.toPlainText(),
                    buyer_dl_number=buyer_dl_input.text(),
                    buyer_ltc_number=buyer_ltc_input.text(),
                    sale_price=float(price_spin.value()),
                    ffl_dealer=ffl_dealer_input.text(),
                    ffl_license=ffl_license_input.text(),
                    notes=notes_input.toPlainText(),
                )

                self.repo.transfer_firearm(transfer)
                self.refresh_all()
                QMessageBox.information(
                    dialog,
                    "Transfer Recorded",
                    f"'{selected.name}' has been transferred to {buyer_name_input.text()}.\n\n"
                    "Record saved in Transfers tab.",
                )
                dialog.accept()

        transfer_btn.clicked.connect(save_transfer)
        btn_layout.addWidget(transfer_btn)

        layout.addRow(btn_layout)

        dialog.setLayout(layout)
        dialog.exec()

    def open_add_firearm_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Firearm")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit()
        name_input.setPlaceholderText("e.g., S&W 1854 .45-70")
        layout.addRow("Name:", name_input)

        caliber_input = QLineEdit()
        caliber_input.setPlaceholderText("e.g., .45-70 Govt")
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

        save_btn = QPushButton("Save")

        def save():
            if not name_input.text() or not caliber_input.text():
                QMessageBox.warning(dialog, "Error", "Name and caliber are required")
                return
            firearm = Firearm(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                caliber=caliber_input.text(),
                serial_number=serial_input.text(),
                purchase_date=datetime.now(),
                notes=notes_input.toPlainText(),
                rounds_fired=0,
                clean_interval_rounds=clean_interval_spin.value(),
                oil_interval_days=oil_interval_spin.value(),
            )
            self.repo.add_firearm(firearm)
            self.refresh_firearms()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

        # ============== ATTACHMENTS TAB ==============

    def create_attachments_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel(
            "Non‑regulated attachments: optics, lights, stocks, rails, triggers, etc."
        )
        info_label.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        self.attachment_table = QTableWidget()
        self.attachment_table.setColumnCount(6)
        self.attachment_table.setHorizontalHeaderLabels(
            ["Name", "Category", "Brand/Model", "Mounted On", "Zero", "Notes"]
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
        edit_btn.clicked.connect(self.open_edit_attachment_dialog)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_selected_attachment)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_attachments(self):
        self.attachment_table.setRowCount(0)
        attachments = self.repo.get_all_attachments()
        firearms = {f.id: f for f in self.repo.get_all_firearms()}

        for i, att in enumerate(attachments):
            self.attachment_table.insertRow(i)
            self.attachment_table.setItem(i, 0, QTableWidgetItem(att.name))
            self.attachment_table.setItem(i, 1, QTableWidgetItem(att.category))
            brand_model = f"{att.brand} {att.model}".strip()
            self.attachment_table.setItem(i, 2, QTableWidgetItem(brand_model))

            mounted_name = ""
            if att.mounted_on_firearm_id and att.mounted_on_firearm_id in firearms:
                fw = firearms[att.mounted_on_firearm_id]
                mounted_name = fw.name
                if att.mount_position:
                    mounted_name += f" ({att.mount_position})"
            self.attachment_table.setItem(i, 3, QTableWidgetItem(mounted_name))

            zero_text = ""
            if att.zero_distance_yards:
                zero_text = f"{att.zero_distance_yards} yd"
            self.attachment_table.setItem(i, 4, QTableWidgetItem(zero_text))

            self.attachment_table.setItem(i, 5, QTableWidgetItem(att.notes or ""))

    def _get_selected_attachment(self):
        row = self.attachment_table.currentRow()
        if row < 0:
            return None

        attachments = self.repo.get_all_attachments()
        if row >= len(attachments):
            return None
        return attachments[row]

    def open_add_attachment_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Attachment")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit()
        layout.addRow("Name:", name_input)

        category_input = QLineEdit()
        category_input.setPlaceholderText("optic, light, stock, rail, trigger…")
        layout.addRow("Category:", category_input)

        brand_input = QLineEdit()
        layout.addRow("Brand:", brand_input)

        model_input = QLineEdit()
        layout.addRow("Model:", model_input)

        serial_input = QLineEdit()
        layout.addRow("Serial #:", serial_input)

        # Mounted on firearm
        firearms = self.repo.get_all_firearms()
        firearm_combo = QComboBox()
        firearm_combo.addItem("Unassigned")
        for fw in firearms:
            firearm_combo.addItem(fw.name)
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

        save_btn = QPushButton("Save")

        def save():
            if not name_input.text():
                QMessageBox.warning(dialog, "Error", "Name is required")
                return

            mounted_id = None
            idx = firearm_combo.currentIndex()
            if idx > 0:
                mounted_id = firearms[idx - 1].id

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
                zero_distance_yards=zero_spin.value() or None,
                zero_notes=zero_notes_input.toPlainText(),
                notes=notes_input.toPlainText(),
            )
            self.repo.add_attachment(att)
            self.refresh_attachments()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def open_edit_attachment_dialog(self):
        selected = self._get_selected_attachment()
        if not selected:
            QMessageBox.warning(self, "Error", "Select an attachment to edit")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Attachment: {selected.name}")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit(selected.name)
        layout.addRow("Name:", name_input)

        category_input = QLineEdit(selected.category)
        layout.addRow("Category:", category_input)

        brand_input = QLineEdit(selected.brand)
        layout.addRow("Brand:", brand_input)

        model_input = QLineEdit(selected.model)
        layout.addRow("Model:", model_input)

        serial_input = QLineEdit(selected.serial_number)
        layout.addRow("Serial #:", serial_input)

        firearms = self.repo.get_all_firearms()
        firearm_combo = QComboBox()
        firearm_combo.addItem("Unassigned")
        current_index = 0
        for i, fw in enumerate(firearms, start=1):
            firearm_combo.addItem(fw.name)
            if selected.mounted_on_firearm_id == fw.id:
                current_index = i
        firearm_combo.setCurrentIndex(current_index)
        layout.addRow("Mounted on:", firearm_combo)

        mount_pos_input = QLineEdit(selected.mount_position)
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

        save_btn = QPushButton("Save changes")

        def save():
            if not name_input.text():
                QMessageBox.warning(dialog, "Error", "Name is required")
                return

            mounted_id = None
            idx = firearm_combo.currentIndex()
            if idx > 0:
                mounted_id = firearms[idx - 1].id

            updated = Attachment(
                id=selected.id,
                name=name_input.text(),
                category=category_input.text() or "other",
                brand=brand_input.text(),
                model=model_input.text(),
                purchase_date=selected.purchase_date or datetime.now(),
                serial_number=serial_input.text(),
                mounted_on_firearm_id=mounted_id,
                mount_position=mount_pos_input.text(),
                zero_distance_yards=zero_spin.value() or None,
                zero_notes=zero_notes_input.toPlainText(),
                notes=notes_input.toPlainText(),
            )
            self.repo.update_attachment(updated)
            self.refresh_attachments()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def delete_selected_attachment(self):
        selected = self._get_selected_attachment()
        if not selected:
            QMessageBox.warning(self, "Error", "Select an attachment to delete")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Permanently delete attachment '{selected.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_attachment(selected.id)
            self.refresh_attachments()
            QMessageBox.information(
                self, "Deleted", f"Attachment '{selected.name}' has been deleted."
            )

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

        add_btn = QPushButton("Add Soft Gear")
        add_btn.clicked.connect(self.open_add_soft_gear_dialog)
        btn_layout.addWidget(add_btn)

        log_btn = QPushButton("Log Maintenance")
        log_btn.clicked.connect(lambda: self.open_log_dialog(GearCategory.SOFT_GEAR))
        btn_layout.addWidget(log_btn)

        history_btn = QPushButton("View History")
        history_btn.clicked.connect(
            lambda: self.view_item_history(GearCategory.SOFT_GEAR)
        )
        btn_layout.addWidget(history_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_selected_soft_gear)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_soft_gear(self):
        self.soft_gear_table.setRowCount(0)
        gear_list = self.repo.get_all_soft_gear()

        for i, gear in enumerate(gear_list):
            self.soft_gear_table.insertRow(i)
            self.soft_gear_table.setItem(i, 0, QTableWidgetItem(gear.name))
            self.soft_gear_table.setItem(i, 1, QTableWidgetItem(gear.category))
            self.soft_gear_table.setItem(i, 2, QTableWidgetItem(gear.brand))

            status_item = QTableWidgetItem(gear.status.value)
            if gear.status == CheckoutStatus.CHECKED_OUT:
                status_item.setBackground(QColor(255, 200, 200))
            self.soft_gear_table.setItem(i, 3, status_item)

            self.soft_gear_table.setItem(i, 4, QTableWidgetItem(gear.notes))

    def delete_selected_soft_gear(self):
        row = self.soft_gear_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a soft gear item to delete")
            return

        gear_list = self.repo.get_all_soft_gear()
        selected = gear_list[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Permanently delete '{selected.name}'?\n\nThis will also delete all maintenance logs and checkout history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_soft_gear(selected.id)
            self.refresh_soft_gear()
            QMessageBox.information(
                self, "Deleted", f"'{selected.name}' has been deleted."
            )

    def open_add_soft_gear_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Soft Gear")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit()
        name_input.setPlaceholderText("e.g., Haley D3CRX Chest Rig")
        layout.addRow("Name:", name_input)

        category_combo = QComboBox()
        category_combo.setEditable(True)
        category_combo.addItems(
            [
                "chest_rig",
                "backpack",
                "chaps",
                "gloves",
                "boots",
                "gaiters",
                "belt",
                "holster",
                "sling",
                "case",
                "other",
            ]
        )
        layout.addRow("Category:", category_combo)

        brand_input = QLineEdit()
        brand_input.setPlaceholderText("e.g., Haley Strategic")
        layout.addRow("Brand:", brand_input)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        layout.addRow("Notes:", notes_input)

        save_btn = QPushButton("Save")

        def save():
            if not name_input.text():
                QMessageBox.warning(dialog, "Error", "Name is required")
                return
            gear = SoftGear(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                category=category_combo.currentText(),
                brand=brand_input.text(),
                purchase_date=datetime.now(),
                notes=notes_input.toPlainText(),
            )
            self.repo.add_soft_gear(gear)
            self.refresh_soft_gear()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    # ============== CONSUMABLES TAB ==============

    def create_consumables_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Low stock warning
        self.low_stock_label = QLabel()
        self.low_stock_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.low_stock_label)

        self.consumable_table = QTableWidget()
        self.consumable_table.setColumnCount(5)
        self.consumable_table.setHorizontalHeaderLabels(
            ["Name", "Category", "Quantity", "Unit", "Min Qty"]
        )
        self.consumable_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.consumable_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Consumable")
        add_btn.clicked.connect(self.open_add_consumable_dialog)
        btn_layout.addWidget(add_btn)

        add_stock_btn = QPushButton("➕ Add Stock")
        add_stock_btn.clicked.connect(lambda: self.adjust_consumable_qty(positive=True))
        btn_layout.addWidget(add_stock_btn)

        use_stock_btn = QPushButton("➖ Use Stock")
        use_stock_btn.clicked.connect(
            lambda: self.adjust_consumable_qty(positive=False)
        )
        btn_layout.addWidget(use_stock_btn)

        history_btn = QPushButton("View History")
        history_btn.clicked.connect(self.view_consumable_history)
        btn_layout.addWidget(history_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_selected_consumable)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_consumables(self):
        self.consumable_table.setRowCount(0)
        consumables = self.repo.get_all_consumables()
        low_stock = self.repo.get_low_stock_consumables()

        if low_stock:
            names = ", ".join([c.name for c in low_stock])
            self.low_stock_label.setText(f"⚠️ LOW STOCK: {names}")
        else:
            self.low_stock_label.setText("")

        for i, c in enumerate(consumables):
            self.consumable_table.insertRow(i)
            self.consumable_table.setItem(i, 0, QTableWidgetItem(c.name))
            self.consumable_table.setItem(i, 1, QTableWidgetItem(c.category))

            qty_item = QTableWidgetItem(str(c.quantity))
            if c.quantity <= c.min_quantity:
                qty_item.setBackground(QColor(255, 150, 150))
            self.consumable_table.setItem(i, 2, qty_item)

            self.consumable_table.setItem(i, 3, QTableWidgetItem(c.unit))
            self.consumable_table.setItem(i, 4, QTableWidgetItem(str(c.min_quantity)))

    def delete_selected_consumable(self):
        row = self.consumable_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a consumable to delete.")
            return

        consumables = self.repo.get_all_consumables()
        selected = consumables[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Permanently Delete '{selected.name}'?\n\nThis will also delete all transaction history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_consumable(selected.id)
            self.refresh_consumables()
            QMessageBox.information(
                self, "Deleted", f"'{selected.name}' has been deleted."
            )

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
            consumable = Consumable(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                category=category_combo.currentText(),
                unit=unit_combo.currentText(),
                quantity=qty_spin.value(),
                min_quantity=min_qty_spin.value(),
                notes=notes_input.toPlainText(),
            )
            self.repo.add_consumable(consumable)
            self.refresh_consumables()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def adjust_consumable_qty(self, positive: bool):
        row = self.consumable_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a consumable first")
            return

        consumables = self.repo.get_all_consumables()
        selected = consumables[row]

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Stock" if positive else "Use Stock")

        layout = QFormLayout()

        layout.addRow("Item:", QLabel(selected.name))
        layout.addRow("Current:", QLabel(f"{selected.quantity} {selected.unit}"))

        qty_spin = QSpinBox()
        qty_spin.setRange(1, 10000)
        qty_spin.setValue(1 if not positive else 20)
        layout.addRow("Amount:", qty_spin)

        notes_input = QLineEdit()
        notes_input.setPlaceholderText("e.g., Range session, Purchased at Cabelas")
        layout.addRow("Notes:", notes_input)

        save_btn = QPushButton("Save")

        def save():
            delta = qty_spin.value() if positive else -qty_spin.value()
            tx_type = "ADD" if positive else "USE"
            self.repo.update_consumable_quantity(
                selected.id, delta, tx_type, notes_input.text()
            )
            self.refresh_consumables()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def view_consumable_history(self):
        row = self.consumable_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a consumable first")
            return

        consumables = self.repo.get_all_consumables()
        selected = consumables[row]
        history = self.repo.get_consumable_history(selected.id)

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

        info_label = QLabel(
            "Hunt/Trip loadout profiles for one-click checkout of gear and consumables."
        )
        info_label.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

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

        add_btn = QPushButton("Create Loadout")
        add_btn.clicked.connect(self.open_create_loadout_dialog)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit Loadout")
        edit_btn.clicked.connect(self.open_edit_loadout_dialog)
        btn_layout.addWidget(edit_btn)

        duplicate_btn = QPushButton("Duplicate Loadout")
        duplicate_btn.clicked.connect(self.duplicate_loadout)
        btn_layout.addWidget(duplicate_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_selected_loadout)
        btn_layout.addWidget(delete_btn)

        checkout_btn = QPushButton("🚀 Checkout Loadout")
        checkout_btn.setStyleSheet("background-color: #20206B; font-weight: bold;")
        checkout_btn.clicked.connect(self.open_checkout_loadout_dialog)
        btn_layout.addWidget(checkout_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_loadouts(self):
        self.loadout_table.setRowCount(0)
        loadouts = self.repo.get_all_loadouts()

        for i, lo in enumerate(loadouts):
            self.loadout_table.insertRow(i)
            self.loadout_table.setItem(i, 0, QTableWidgetItem(lo.name))

            description_text = lo.description if lo.description else ""
            self.loadout_table.setItem(i, 1, QTableWidgetItem(description_text))

            items = self.repo.get_loadout_items(lo.id)
            item_names = []
            for item in items:
                if item.item_type == GearCategory.FIREARM:
                    firearms = {f.id: f.name for f in self.repo.get_all_firearms()}
                    item_names.append(f"🔫 {firearms.get(item.item_id, 'Unknown')}")
                elif item.item_type == GearCategory.SOFT_GEAR:
                    soft_gear = {g.id: g.name for g in self.repo.get_all_soft_gear()}
                    item_names.append(f"🎒 {soft_gear.get(item.item_id, 'Unknown')}")
                elif item.item_type == GearCategory.NFA_ITEM:
                    nfa_items = {n.id: n.name for n in self.repo.get_all_nfa_items()}
                    item_names.append(f"🔇 {nfa_items.get(item.item_id, 'Unknown')}")

            self.loadout_table.setItem(i, 2, QTableWidgetItem(", ".join(item_names)))

            consumables = self.repo.get_loadout_consumables(lo.id)
            cons_names = []
            for cons in consumables:
                all_cons = self.repo.get_all_consumables()
                cons_dict = {c.id: c for c in all_cons}
                c = cons_dict.get(cons.consumable_id)
                if c:
                    cons_names.append(f"{c.name} ({cons.quantity} {c.unit})")

            self.loadout_table.setItem(i, 3, QTableWidgetItem(", ".join(cons_names)))

            created_text = (
                lo.created_date.strftime("%Y-%m-%d") if lo.created_date else "Never"
            )
            self.loadout_table.setItem(i, 4, QTableWidgetItem(created_text))

    def _get_selected_loadout(self) -> Loadout | None:
        row = self.loadout_table.currentRow()
        if row < 0:
            return None
        loadouts = self.repo.get_all_loadouts()
        if row >= len(loadouts):
            return None
        return loadouts[row]

    def delete_selected_loadout(self):
        loadout = self._get_selected_loadout()
        if not loadout:
            QMessageBox.warning(
                self, "No Selection", "Please select a loadout to delete."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete loadout '{loadout.name}'?\n\n"
            "This will also delete all associated items, consumables, and checkout records.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_loadout(loadout.id)
            self.refresh_loadouts()
            QMessageBox.information(
                self, "Deleted", f"Loadout '{loadout.name}' deleted successfully."
            )

    def duplicate_loadout(self):
        loadout = self._get_selected_loadout()
        if not loadout:
            QMessageBox.warning(
                self, "No Selection", "Please select a loadout to duplicate."
            )
            return

        # Get existing items and consumables
        items = self.repo.get_loadout_items(loadout.id)
        consumables = self.repo.get_loadout_consumables(loadout.id)

        # Create new loadout
        new_loadout = Loadout(
            id=str(uuid.uuid4()),
            name=f"{loadout.name} (Copy)",
            description=loadout.description,
            created_date=datetime.now(),
            notes=loadout.notes,
        )
        self.repo.create_loadout(new_loadout)

        # Copy items with new IDs
        for item in items:
            new_item = LoadoutItem(
                id=str(uuid.uuid4()),
                loadout_id=new_loadout.id,
                item_id=item.item_id,
                item_type=item.item_type,
                notes=item.notes,
            )
            self.repo.add_loadout_item(new_item)

        # Copy consumables with new IDs
        for cons in consumables:
            new_cons = LoadoutConsumable(
                id=str(uuid.uuid4()),
                loadout_id=new_loadout.id,
                consumable_id=cons.consumable_id,
                quantity=cons.quantity,
                notes=cons.notes,
            )
            self.repo.add_loadout_consumable(new_cons)

        self.refresh_loadouts()
        QMessageBox.information(
            self,
            "Duplicated",
            f"Loadout '{loadout.name}' duplicated successfully as '{new_loadout.name}'.",
        )

    def open_create_loadout_dialog(self, loadout=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Loadout" if loadout is None else "Edit Loadout")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)

        # Form fields
        form_layout = QFormLayout()

        name_input = QLineEdit()
        if loadout:
            name_input.setText(loadout.name)
        form_layout.addRow("Name:", name_input)

        description_input = QLineEdit()
        if loadout:
            description_input.setText(loadout.description)
        form_layout.addRow("Description:", description_input)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        if loadout:
            notes_input.setText(loadout.notes)
        form_layout.addRow("Notes:", notes_input)

        layout.addLayout(form_layout)

        # Track selected items
        self.selected_firearms = []
        self.selected_soft_gear = []
        self.selected_nfa_items = []
        self.selected_consumables = {}

        # Tab widget for item selection
        tabs = QTabWidget()

        # Firearms tab
        firearms_tab = QWidget()
        firearms_layout = QVBoxLayout()

        info_label = QLabel(
            "Select firearms - their mounted attachments will be automatically included."
        )
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        firearms_layout.addWidget(info_label)

        available_firearms = [
            f
            for f in self.repo.get_all_firearms()
            if f.status == CheckoutStatus.AVAILABLE
        ]
        if not available_firearms:
            firearms_layout.addWidget(QLabel("No available firearms to add."))
        else:
            firearms_list = QWidget()
            firearms_list_layout = QVBoxLayout()
            firearms_list_layout.setContentsMargins(0, 0, 0, 0)

            for fw in available_firearms:
                checkbox = QCheckBox(f"🔫 {fw.name}")
                checkbox.setProperty("item_id", fw.id)
                if loadout:
                    existing_items = self.repo.get_loadout_items(loadout.id)
                    if any(
                        item.item_id == fw.id and item.item_type == GearCategory.FIREARM
                        for item in existing_items
                    ):
                        checkbox.setChecked(True)
                firearms_list_layout.addWidget(checkbox)

                # Show mounted attachments
                attachments = self.repo.get_attachments_for_firearm(fw.id)
                if attachments:
                    for att in attachments:
                        att_label = QLabel(f"    🔧 {att.name} ({att.category})")
                        att_label.setStyleSheet(
                            "color: #888; font-size: 10px; margin-left: 20px;"
                        )
                        firearms_list_layout.addWidget(att_label)

            firearms_list.setLayout(firearms_list_layout)
            firearms_layout.addWidget(firearms_list)

        firearms_tab.setLayout(firearms_layout)
        tabs.addTab(firearms_tab, "🔫 Firearms")

        # Soft Gear tab
        soft_gear_tab = QWidget()
        soft_gear_layout = QVBoxLayout()

        info_label = QLabel("Select soft gear items to include in this loadout.")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        soft_gear_layout.addWidget(info_label)

        available_soft_gear = [
            g
            for g in self.repo.get_all_soft_gear()
            if g.status == CheckoutStatus.AVAILABLE
        ]
        if not available_soft_gear:
            soft_gear_layout.addWidget(QLabel("No available soft gear to add."))
        else:
            for gear in available_soft_gear:
                checkbox = QCheckBox(f"🎒 {gear.name} ({gear.category})")
                checkbox.setProperty("item_id", gear.id)
                if loadout:
                    existing_items = self.repo.get_loadout_items(loadout.id)
                    if any(
                        item.item_id == gear.id
                        and item.item_type == GearCategory.SOFT_GEAR
                        for item in existing_items
                    ):
                        checkbox.setChecked(True)
                soft_gear_layout.addWidget(checkbox)

        soft_gear_tab.setLayout(soft_gear_layout)
        tabs.addTab(soft_gear_tab, "🎒 Soft Gear")

        # NFA Items tab
        nfa_tab = QWidget()
        nfa_layout = QVBoxLayout()

        info_label = QLabel("Select NFA items to include in this loadout.")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        nfa_layout.addWidget(info_label)

        available_nfa = [
            n
            for n in self.repo.get_all_nfa_items()
            if n.status == CheckoutStatus.AVAILABLE
        ]
        if not available_nfa:
            nfa_layout.addWidget(QLabel("No available NFA items to add."))
        else:
            for nfa in available_nfa:
                checkbox = QCheckBox(f"🔇 {nfa.name} ({nfa.nfa_type.value})")
                checkbox.setProperty("item_id", nfa.id)
                if loadout:
                    existing_items = self.repo.get_loadout_items(loadout.id)
                    if any(
                        item.item_id == nfa.id
                        and item.item_type == GearCategory.NFA_ITEM
                        for item in existing_items
                    ):
                        checkbox.setChecked(True)
                nfa_layout.addWidget(checkbox)

        nfa_tab.setLayout(nfa_layout)
        tabs.addTab(nfa_tab, "🔇 NFA Items")

        # Consumables tab
        consumables_tab = QWidget()
        consumables_layout = QVBoxLayout()

        info_label = QLabel("Select consumables and quantities for this loadout.")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        consumables_layout.addWidget(info_label)

        consumables_table = QTableWidget()
        consumables_table.setColumnCount(4)
        consumables_table.setHorizontalHeaderLabels(
            ["Name", "Category", "Unit", "Quantity"]
        )
        consumables_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        all_consumables = self.repo.get_all_consumables()
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
            qty_spinbox.setValue(0)
            qty_spinbox.setProperty("consumable_id", cons.id)

            if loadout:
                existing_cons = self.repo.get_loadout_consumables(loadout.id)
                for lc in existing_cons:
                    if lc.consumable_id == cons.id:
                        qty_spinbox.setValue(lc.quantity)
                        break

            consumables_table.setCellWidget(i, 3, qty_spinbox)

        consumables_layout.addWidget(consumables_table)

        add_cons_btn = QPushButton("Add Selected Consumables")
        add_cons_btn.clicked.connect(
            lambda: self.add_consumable_to_loadout(consumables_table)
        )
        consumables_layout.addWidget(add_cons_btn)

        # Show currently selected consumables
        self.selected_consumables_list = QListWidget()
        self.selected_consumables_list.setMaximumHeight(150)
        cons_list_label = QLabel("Selected Consumables:")
        cons_list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        consumables_layout.addWidget(cons_list_label)
        consumables_layout.addWidget(self.selected_consumables_list)

        consumables_tab.setLayout(consumables_layout)
        tabs.addTab(consumables_tab, "📦 Consumables")

        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save Loadout")
        save_btn.setStyleSheet("background-color: #202060; font-weight: bold;")
        save_btn.clicked.connect(
            lambda: self.save_loadout(
                dialog,
                name_input.text(),
                description_input.text(),
                notes_input.toPlainText(),
                tabs,
                loadout,
            )
        )
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def add_consumable_to_loadout(self, consumables_table):
        """Helper to add selected consumables to temporary list"""
        for row in range(consumables_table.rowCount()):
            qty_widget = consumables_table.cellWidget(row, 3)
            if qty_widget and qty_widget.value() > 0:
                consumable_id = consumables_table.item(row, 0).data(
                    Qt.ItemDataRole.UserRole
                )
                if consumable_id:
                    self.selected_consumables[consumable_id] = {
                        "id": consumable_id,
                        "quantity": qty_widget.value(),
                    }

        # Update list widget
        self.selected_consumables_list.clear()
        all_cons = self.repo.get_all_consumables()
        cons_dict = {c.id: c for c in all_cons}

        for cons_id, data in self.selected_consumables.items():
            cons = cons_dict.get(cons_id)
            if cons:
                item_text = f"{cons.name} ({data['quantity']} {cons.unit})"
                self.selected_consumables_list.addItem(item_text)

    def save_loadout(self, dialog, name, description, notes, tabs, loadout=None):
        """Save or update loadout"""
        # Validate
        if not name.strip():
            QMessageBox.warning(dialog, "Validation Error", "Loadout name is required.")
            return

        # Get selected items from tabs
        selected_firearms = []
        selected_soft_gear = []
        selected_nfa_items = []

        # Firearms tab (widget at index 0)
        firearms_widget = tabs.widget(0)
        if firearms_widget:
            for child in firearms_widget.findChildren(QCheckBox):
                if child.isChecked():
                    item_id = child.property("item_id")
                    if item_id:
                        selected_firearms.append(item_id)

        # Soft Gear tab (widget at index 1)
        soft_gear_widget = tabs.widget(1)
        if soft_gear_widget:
            for child in soft_gear_widget.findChildren(QCheckBox):
                if child.isChecked():
                    item_id = child.property("item_id")
                    if item_id:
                        selected_soft_gear.append(item_id)

        # NFA Items tab (widget at index 2)
        nfa_widget = tabs.widget(2)
        if nfa_widget:
            for child in nfa_widget.findChildren(QCheckBox):
                if child.isChecked():
                    item_id = child.property("item_id")
                    if item_id:
                        selected_nfa_items.append(item_id)

        # Check if at least one item is selected
        if not (
            selected_firearms
            or selected_soft_gear
            or selected_nfa_items
            or self.selected_consumables
        ):
            QMessageBox.warning(
                dialog,
                "Validation Error",
                "Please select at least one item or consumable.",
            )
            return

        if loadout:
            # Update existing loadout
            loadout.name = name
            loadout.description = description
            loadout.notes = notes
            self.repo.update_loadout(loadout)

            # Clear old items and consumables
            old_items = self.repo.get_loadout_items(loadout.id)
            for item in old_items:
                self.repo.remove_loadout_item(item.id)

            old_consumables = self.repo.get_loadout_consumables(loadout.id)
            for cons in old_consumables:
                self.repo.remove_loadout_consumable(cons.id)

            # Add new items and consumables
            for fw_id in selected_firearms:
                loadout_item = LoadoutItem(
                    id=str(uuid.uuid4()),
                    loadout_id=loadout.id,
                    item_id=fw_id,
                    item_type=GearCategory.FIREARM,
                )
                self.repo.add_loadout_item(loadout_item)

            for sg_id in selected_soft_gear:
                loadout_item = LoadoutItem(
                    id=str(uuid.uuid4()),
                    loadout_id=loadout.id,
                    item_id=sg_id,
                    item_type=GearCategory.SOFT_GEAR,
                )
                self.repo.add_loadout_item(loadout_item)

            for nfa_id in selected_nfa_items:
                loadout_item = LoadoutItem(
                    id=str(uuid.uuid4()),
                    loadout_id=loadout.id,
                    item_id=nfa_id,
                    item_type=GearCategory.NFA_ITEM,
                )
                self.repo.add_loadout_item(loadout_item)

            for cons_id, data in self.selected_consumables.items():
                loadout_cons = LoadoutConsumable(
                    id=str(uuid.uuid4()),
                    loadout_id=loadout.id,
                    consumable_id=cons_id,
                    quantity=data["quantity"],
                )
                self.repo.add_loadout_consumable(loadout_cons)

            QMessageBox.information(
                dialog, "Success", f"Loadout '{name}' updated successfully."
            )
        else:
            # Create new loadout
            new_loadout = Loadout(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                created_date=datetime.now(),
                notes=notes,
            )
            self.repo.create_loadout(new_loadout)

            # Add items
            for fw_id in selected_firearms:
                loadout_item = LoadoutItem(
                    id=str(uuid.uuid4()),
                    loadout_id=new_loadout.id,
                    item_id=fw_id,
                    item_type=GearCategory.FIREARM,
                )
                self.repo.add_loadout_item(loadout_item)

            for sg_id in selected_soft_gear:
                loadout_item = LoadoutItem(
                    id=str(uuid.uuid4()),
                    loadout_id=new_loadout.id,
                    item_id=sg_id,
                    item_type=GearCategory.SOFT_GEAR,
                )
                self.repo.add_loadout_item(loadout_item)

            for nfa_id in selected_nfa_items:
                loadout_item = LoadoutItem(
                    id=str(uuid.uuid4()),
                    loadout_id=new_loadout.id,
                    item_id=nfa_id,
                    item_type=GearCategory.NFA_ITEM,
                )
                self.repo.add_loadout_item(loadout_item)

            # Add consumables
            for cons_id, data in self.selected_consumables.items():
                loadout_cons = LoadoutConsumable(
                    id=str(uuid.uuid4()),
                    loadout_id=new_loadout.id,
                    consumable_id=cons_id,
                    quantity=data["quantity"],
                )
                self.repo.add_loadout_consumable(loadout_cons)

            QMessageBox.information(
                dialog, "Success", f"Loadout '{name}' created successfully."
            )

        # Clear temp selections
        self.selected_consumables = {}
        self.selected_firearms = []
        self.selected_soft_gear = []
        self.selected_nfa_items = []

        self.refresh_loadouts()
        dialog.accept()

    def open_edit_loadout_dialog(self):
        loadout = self._get_selected_loadout()
        if not loadout:
            QMessageBox.warning(
                self, "No Selection", "Please select a loadout to edit."
            )
            return
        self.open_create_loadout_dialog(loadout)

    def open_checkout_loadout_dialog(self):
        loadout = self._get_selected_loadout()
        if not loadout:
            QMessageBox.warning(
                self, "No Selection", "Please select a loadout to checkout."
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Checkout Loadout: {loadout.name}")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout(dialog)

        # Loadout info
        info_group = QGroupBox("Loadout Details")
        info_layout = QFormLayout()

        name_label = QLabel(loadout.name)
        info_layout.addRow("Name:", name_label)

        desc_label = QLabel(loadout.description if loadout.description else "None")
        info_layout.addRow("Description:", desc_label)

        # Show items
        items = self.repo.get_loadout_items(loadout.id)
        item_summary = []
        for item in items:
            if item.item_type == GearCategory.FIREARM:
                firearms = {f.id: f.name for f in self.repo.get_all_firearms()}
                item_summary.append(f"🔫 {firearms.get(item.item_id, 'Unknown')}")
            elif item.item_type == GearCategory.SOFT_GEAR:
                soft_gear = {g.id: g.name for g in self.repo.get_all_soft_gear()}
                item_summary.append(f"🎒 {soft_gear.get(item.item_id, 'Unknown')}")
            elif item.item_type == GearCategory.NFA_ITEM:
                nfa_items = {n.id: n.name for n in self.repo.get_all_nfa_items()}
                item_summary.append(f"🔇 {nfa_items.get(item.item_id, 'Unknown')}")

        items_text = ", ".join(item_summary) if item_summary else "None"
        items_label = QLabel(items_text)
        items_label.setWordWrap(True)
        info_layout.addRow("Items:", items_label)

        # Show consumables
        consumables = self.repo.get_loadout_consumables(loadout.id)
        cons_summary = []
        all_cons = self.repo.get_all_consumables()
        cons_dict = {c.id: c for c in all_cons}

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

        # Checkout form
        form_layout = QFormLayout()

        # Borrower dropdown
        borrower_combo = QComboBox()
        borrowers = self.repo.get_all_borrowers()
        for borrower in borrowers:
            borrower_combo.addItem(borrower.name, borrower.id)

        if not borrowers:
            borrower_combo.addItem("No borrowers available", "")
            form_layout.addRow("Borrower:", borrower_combo)
        else:
            form_layout.addRow("Borrower:", borrower_combo)

        # Expected return date
        return_date_edit = QDateEdit()
        return_date_edit.setDate(QDate.currentDate().addDays(7))
        return_date_edit.setCalendarPopup(True)
        form_layout.addRow("Expected Return:", return_date_edit)

        # Notes
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        form_layout.addRow("Notes:", notes_input)

        layout.addLayout(form_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        checkout_btn = QPushButton("🚀 Checkout Loadout")
        checkout_btn.setStyleSheet("background-color: #202060; font-weight: bold;")
        checkout_btn.clicked.connect(
            lambda: self.perform_loadout_checkout(
                dialog, loadout, borrower_combo, return_date_edit, notes_input
            )
        )
        btn_layout.addWidget(checkout_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def perform_loadout_checkout(
        self,
        dialog,
        loadout: Loadout,
        borrower_combo: QComboBox,
        return_date_edit: QDateEdit,
        notes_input: QTextEdit,
    ):
        """Execute loadout checkout with validation"""
        borrower_id = borrower_combo.currentData()
        if not borrower_id:
            QMessageBox.warning(
                dialog,
                "No Borrower",
                "Please create a borrower first before checking out items.",
            )
            return

        return_date = datetime(
            return_date_edit.date().year(),
            return_date_edit.date().month(),
            return_date_edit.date().day(),
        )
        notes = notes_input.toPlainText()

        # Validate loadout checkout
        validation = self.repo.validate_loadout_checkout(loadout.id)

        if validation["critical_issues"]:
            # Show critical issues dialog
            critical_text = "\n".join(
                f"• {issue}" for issue in validation["critical_issues"]
            )
            QMessageBox.critical(
                dialog,
                "Cannot Checkout Loadout",
                f"The following critical issues must be resolved:\n\n{critical_text}",
            )
            return

        if validation["warnings"]:
            # Show warnings dialog with option to proceed
            warning_text = "\n".join(f"• {w}" for w in validation["warnings"])
            reply = QMessageBox.question(
                dialog,
                "Checkout Warnings",
                f"The following warnings exist:\n\n{warning_text}\n\nDo you want to proceed with checkout?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                return

        # Perform checkout
        checkout_id, messages = self.repo.checkout_loadout(
            loadout.id,
            borrower_id,
            return_date,
        )

        if checkout_id:
            message = f"Loadout '{loadout.name}' checked out successfully!\n\n"
            if messages:
                message += "Notes:\n" + "\n".join(f"• {m}" for m in messages)
            QMessageBox.information(dialog, "Checkout Successful", message)
            self.refresh_all()
            dialog.accept()
        else:
            error_message = "Failed to checkout loadout.\n\n"
            if messages:
                error_message += "Errors:\n" + "\n".join(f"• {m}" for m in messages)
            QMessageBox.critical(dialog, "Checkout Failed", error_message)
            return

    # ============== CHECKOUTS TAB ==============

    def create_checkouts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Active Checkouts:"))

        self.checkout_table = QTableWidget()
        self.checkout_table.setColumnCount(5)
        self.checkout_table.setHorizontalHeaderLabels(
            ["Item", "Type", "Borrower", "Checkout Date", "Expected Return"]
        )
        self.checkout_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.checkout_table)

        btn_layout = QHBoxLayout()

        checkout_btn = QPushButton("Checkout Item")
        checkout_btn.clicked.connect(self.open_checkout_dialog)
        btn_layout.addWidget(checkout_btn)

        return_btn = QPushButton("Return Item")
        return_btn.clicked.connect(self.return_selected_item)
        btn_layout.addWidget(return_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_checkouts(self):
        self.checkout_table.setRowCount(0)
        checkouts = self.repo.get_active_checkouts()

        for i, (checkout, borrower, item_name) in enumerate(checkouts):
            self.checkout_table.insertRow(i)
            self.checkout_table.setItem(i, 0, QTableWidgetItem(item_name))
            self.checkout_table.setItem(
                i, 1, QTableWidgetItem(checkout.item_type.value)
            )
            self.checkout_table.setItem(i, 2, QTableWidgetItem(borrower.name))
            self.checkout_table.setItem(
                i, 3, QTableWidgetItem(checkout.checkout_date.strftime("%Y-%m-%d"))
            )

            exp_return = ""
            if checkout.expected_return:
                exp_return = checkout.expected_return.strftime("%Y-%m-%d")
                if checkout.expected_return < datetime.now():
                    item = QTableWidgetItem(exp_return + " (OVERDUE)")
                    item.setBackground(QColor(255, 150, 150))
                    self.checkout_table.setItem(i, 4, item)
                    continue
            self.checkout_table.setItem(i, 4, QTableWidgetItem(exp_return))

    def open_checkout_dialog(self):
        borrowers = self.repo.get_all_borrowers()
        if not borrowers:
            QMessageBox.warning(self, "Error", "Add a borrower first (Borrowers tab)")
            return

        # Get available items
        firearms = [
            f
            for f in self.repo.get_all_firearms()
            if f.status == CheckoutStatus.AVAILABLE
        ]
        soft_gear = [
            g
            for g in self.repo.get_all_soft_gear()
            if g.status == CheckoutStatus.AVAILABLE
        ]

        if not firearms and not soft_gear:
            QMessageBox.warning(self, "Error", "No available items to checkout")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Checkout Item")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        # Item selection
        item_combo = QComboBox()
        items_data = []
        for f in firearms:
            item_combo.addItem(f"🔫 {f.name}")
            items_data.append((f.id, GearCategory.FIREARM))
        for g in soft_gear:
            item_combo.addItem(f"🎒 {g.name}")
            items_data.append((g.id, GearCategory.SOFT_GEAR))
        layout.addRow("Item:", item_combo)

        # Borrower selection
        borrower_combo = QComboBox()
        for b in borrowers:
            borrower_combo.addItem(b.name)
        layout.addRow("Borrower:", borrower_combo)

        # Expected return
        return_date = QDateEdit()
        return_date.setDate(QDate.currentDate().addDays(7))
        return_date.setCalendarPopup(True)
        layout.addRow("Expected Return:", return_date)

        notes_input = QLineEdit()
        layout.addRow("Notes:", notes_input)

        save_btn = QPushButton("Checkout")

        def save():
            idx = item_combo.currentIndex()
            item_id, item_type = items_data[idx]
            borrower = borrowers[borrower_combo.currentIndex()]

            exp_return = datetime(
                return_date.date().year(),
                return_date.date().month(),
                return_date.date().day(),
            )

            self.repo.checkout_item(
                item_id, item_type, borrower.id, exp_return, notes_input.text()
            )
            self.refresh_all()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def return_selected_item(self):
        row = self.checkout_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a checkout first")
            return

        checkouts = self.repo.get_active_checkouts()
        checkout, _, item_name = checkouts[row]

        # Check if this checkout is from a loadout
        loadout_checkout = self.repo.get_loadout_checkout(checkout.id)

        if loadout_checkout:
            # Loadout checkout - show enhanced return dialog
            self.open_return_loadout_dialog(checkout, loadout_checkout)
        else:
            # Regular checkout - show simple return dialog
            reply = QMessageBox.question(
                self,
                "Confirm Return",
                f"Mark '{item_name}' as returned?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.repo.return_item(checkout.id)
                self.refresh_all()

    def open_return_loadout_dialog(self, checkout, loadout_checkout: LoadoutCheckout):
        """Enhanced return dialog for loadouts with round counts and maintenance data"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Return Loadout: {checkout.item_id}")
        dialog.setMinimumSize(700, 600)

        layout = QVBoxLayout(dialog)

        # Loadout info
        info_group = QGroupBox("Loadout Return Information")
        info_layout = QFormLayout()

        # Get loadout details
        loadout = None
        all_loadouts = self.repo.get_all_loadouts()
        for lo in all_loadouts:
            if lo.id == loadout_checkout.loadout_id:
                loadout = lo
                break

        if loadout:
            name_label = QLabel(loadout.name)
            info_layout.addRow("Loadout:", name_label)

            desc_label = QLabel(loadout.description if loadout.description else "None")
            info_layout.addRow("Description:", desc_label)

        # Get firearms in loadout
        loadout_items = self.repo.get_loadout_items(loadout_checkout.loadout_id)
        firearms_in_loadout = [
            item for item in loadout_items if item.item_type == GearCategory.FIREARM
        ]

        if firearms_in_loadout:
            info_layout.addRow(QLabel("<b>Round Counts (Per Firearm):</b>"))

            # Create per-firearm round count inputs
            self.firearm_rounds_inputs = {}
            all_firearms = self.repo.get_all_firearms()
            firearm_dict = {f.id: f for f in all_firearms}

            for item in firearms_in_loadout:
                firearm = firearm_dict.get(item.item_id)
                if firearm:
                    round_label = QLabel(f"{firearm.name}:")
                    round_spinbox = QSpinBox()
                    round_spinbox.setMinimum(0)
                    round_spinbox.setMaximum(9999)
                    round_spinbox.setValue(0)
                    round_spinbox.setProperty("firearm_id", firearm.id)

                    self.firearm_rounds_inputs[firearm.id] = round_spinbox

                    round_layout = QHBoxLayout()
                    round_layout.addWidget(round_label)
                    round_layout.addWidget(round_spinbox)
                    round_layout.addStretch()

                    info_layout.addRow("", round_layout)

        # Rain exposure
        rain_checkbox = QCheckBox("Exposed to rain during use?")
        info_layout.addRow("", rain_checkbox)

        # Ammo type
        ammo_layout = QHBoxLayout()
        ammo_label = QLabel("Ammo Type:")
        ammo_combo = QComboBox()
        ammo_combo.addItems(["Normal", "Corrosive", "Lead", "Custom"])
        ammo_combo.setCurrentText("Normal")
        ammo_layout.addWidget(ammo_label)
        ammo_layout.addWidget(ammo_combo)
        info_layout.addRow("", ammo_layout)

        # Custom ammo type input (hidden by default)
        custom_ammo_input = QLineEdit()
        custom_ammo_input.setPlaceholderText("Enter custom ammo type")
        custom_ammo_input.setVisible(False)
        info_layout.addRow("", custom_ammo_input)

        # Show custom input if "Custom" selected
        ammo_combo.currentTextChanged.connect(
            lambda text: custom_ammo_input.setVisible(text == "Custom")
        )

        # Notes
        notes_input = QTextEdit()
        notes_input.setMaximumHeight(100)
        notes_input.setPlaceholderText("Additional notes about this trip...")
        info_layout.addRow("Notes:", notes_input)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Consumables section - Auto-restock
        if loadout_checkout.loadout_id:
            consumables_layout = QGroupBox("Consumables - Auto-Restock Unused Items")
            cons_box = QVBoxLayout()

            info_text = QLabel(
                "Check items below to add unused quantities back to inventory:"
            )
            info_text.setStyleSheet(
                "color: #888; font-style: italic; margin-bottom: 10px;"
            )
            cons_box.addWidget(info_text)

            # Get loadout consumables
            loadout_consumables = self.repo.get_loadout_consumables(
                loadout_checkout.loadout_id
            )
            all_consumables = self.repo.get_all_consumables()
            consumable_dict = {c.id: c for c in all_consumables}

            # Create checkboxes for each consumable
            self.restock_checkboxes = {}
            for lc in loadout_consumables:
                cons = consumable_dict.get(lc.consumable_id)
                if cons:
                    checkbox = QCheckBox(
                        f"{cons.name} - Add back all unused ({lc.quantity} {cons.unit})"
                    )
                    checkbox.setChecked(True)  # Default to checked
                    checkbox.setProperty("consumable_id", lc.consumable_id)
                    checkbox.setProperty("original_qty", lc.quantity)

                    self.restock_checkboxes[lc.consumable_id] = checkbox
                    cons_box.addWidget(checkbox)

            restock_btn = QPushButton("🔄 Add Selected Items Back to Inventory")
            restock_btn.setStyleSheet("background-color: #206020;")
            restock_btn.clicked.connect(
                lambda: self.restock_unused_consumables(loadout_checkout.loadout_id)
            )
            cons_box.addWidget(restock_btn)

            consumables_layout.setLayout(cons_box)
            layout.addWidget(consumables_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        return_btn = QPushButton("✅ Return Loadout")
        return_btn.setStyleSheet("background-color: #202060; font-weight: bold;")
        return_btn.clicked.connect(
            lambda: self.perform_loadout_return(
                dialog,
                checkout,
                loadout_checkout,
                self.firearm_rounds_inputs,
                rain_checkbox,
                ammo_combo,
                custom_ammo_input,
                notes_input,
            )
        )
        btn_layout.addWidget(return_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def restock_unused_consumables(self, loadout_id: str):
        """Add unused consumables back to inventory"""
        added_count = 0
        restocked_items = []

        all_consumables = self.repo.get_all_consumables()
        consumable_dict = {c.id: c for c in all_consumables}

        for cons_id, checkbox in self.restock_checkboxes.items():
            if checkbox.isChecked():
                original_qty = checkbox.property("original_qty")
                cons = consumable_dict.get(cons_id)

                if cons:
                    # Add back to inventory
                    new_qty = cons.quantity + original_qty

                    # Update consumable quantity
                    conn = sqlite3.connect(self.repo.db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE consumables SET quantity = ? WHERE id = ?",
                        (new_qty, cons_id),
                    )

                    # Record transaction
                    tx_id = str(uuid.uuid4())
                    cursor.execute(
                        "INSERT INTO consumable_transactions VALUES (?, ?, ?, ?, ?)",
                        (
                            tx_id,
                            cons_id,
                            "RESTOCK",
                            original_qty,
                            int(datetime.now().timestamp()),
                        ),
                    )
                    conn.commit()
                    conn.close()

                    restocked_items.append(f"{cons.name} (+{original_qty} {cons.unit})")
                    added_count += 1

        if added_count > 0:
            message = f"Added {added_count} item(s) back to inventory:\n\n" + "\n".join(
                f"• {item}" for item in restocked_items
            )
            QMessageBox.information(self, "Restock Successful", message)
        else:
            QMessageBox.information(
                self, "No Items", "No items were selected for restocking."
            )

    def perform_loadout_return(
        self,
        dialog: QDialog,
        checkout,
        loadout_checkout: LoadoutCheckout,
        rounds_inputs: dict,
        rain_checkbox: QCheckBox,
        ammo_combo: QComboBox,
        custom_ammo_input: QLineEdit,
        notes_input: QTextEdit,
    ):
        """Execute loadout return with round counts and maintenance data"""
        # Build rounds_fired_dict
        rounds_fired_dict = {}
        total_rounds = 0

        for firearm_id, spinbox in rounds_inputs.items():
            rounds = spinbox.value()
            if rounds > 0:
                rounds_fired_dict[firearm_id] = rounds
                total_rounds += rounds

        # If no rounds entered, ask for confirmation
        if total_rounds == 0:
            reply = QMessageBox.question(
                dialog,
                "No Rounds Entered",
                "No round counts were entered. Mark all firearms as 0 rounds fired?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if reply == QMessageBox.StandardButton.No:
                return

        # Get maintenance data
        rain_exposure = rain_checkbox.isChecked()
        ammo_type = ammo_combo.currentText()

        if ammo_type == "Custom":
            ammo_type = custom_ammo_input.text().strip()
            if not ammo_type:
                QMessageBox.warning(
                    dialog, "Custom Ammo", "Please enter a custom ammo type."
                )
                return

        notes = notes_input.toPlainText()

        rounds_fired_dict["total"] = total_rounds

        # Call repo return_loadout
        self.repo.return_loadout(
            loadout_checkout.id,
            rounds_fired_dict,
            rain_exposure,
            ammo_type,
            notes,
        )

        # Success message
        message = f"Loadout returned successfully!\n\n"
        message += f"Total Rounds Fired: {total_rounds}\n"
        if rain_exposure:
            message += f"Rain Exposure: Yes\n"
        if ammo_type and ammo_type != "Normal":
            message += f"Ammo Type: {ammo_type}\n"

        QMessageBox.information(dialog, "Return Successful", message)
        self.refresh_all()
        dialog.accept()

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

        add_btn = QPushButton("Add Borrower")
        add_btn.clicked.connect(self.open_add_borrower_dialog)
        layout.addWidget(add_btn)

        widget.setLayout(layout)
        return widget

    def refresh_borrowers(self):
        self.borrower_table.setRowCount(0)
        borrowers = self.repo.get_all_borrowers()

        for i, b in enumerate(borrowers):
            self.borrower_table.insertRow(i)
            self.borrower_table.setItem(i, 0, QTableWidgetItem(b.name))
            self.borrower_table.setItem(i, 1, QTableWidgetItem(b.phone))
            self.borrower_table.setItem(i, 2, QTableWidgetItem(b.email))
            self.borrower_table.setItem(i, 3, QTableWidgetItem(b.notes))

    def delete_selected_borrower(self):
        row = self.borrower_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a borrower to delete.")
            return

        borrowers = self.repo.get_all_borrowers()
        selected = borrowers[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Permanently delete borrower '{selected.name}'?\n\nThis will also delete all checkout history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.repo.delete_borrower(selected.id)
                self.refresh_borrowers()
                QMessageBox.information(
                    self, "Deleted", f"Borrower '{selected.name}' has been deleted"
                )
            except ValueError as e:
                QMessageBox.warning(self, "Cannot Delete", str(e))

    def open_add_borrower_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Borrower")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        name_input = QLineEdit()
        layout.addRow("Name:", name_input)

        phone_input = QLineEdit()
        phone_input.setPlaceholderText("(555) 123-4567")
        layout.addRow("Phone:", phone_input)

        email_input = QLineEdit()
        layout.addRow("Email:", email_input)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(60)
        notes_input.setPlaceholderText("e.g., Parish member, hunting buddy")
        layout.addRow("Notes:", notes_input)

        save_btn = QPushButton("Save")

        def save():
            if not name_input.text():
                QMessageBox.warning(dialog, "Error", "Name is required")
                return
            borrower = Borrower(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                phone=phone_input.text(),
                email=email_input.text(),
                notes=notes_input.toPlainText(),
            )
            self.repo.add_borrower(borrower)
            self.refresh_borrowers()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_selected_borrower)
        layout.addWidget(delete_btn)

        dialog.setLayout(layout)
        dialog.exec()

    # ============== NFA ITEMS TAB ===============

    def create_nfa_items_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel("NFA Items: Suppressors, SBRs, SBSs AOWs, DDs")
        info_label.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        self.nfa_table = QTableWidget()
        self.nfa_table.setColumnCount(8)
        self.nfa_table.setHorizontalHeaderLabels(
            [
                "Name",
                "Type",
                "Manufacturer",
                "Serial",
                "Tax Stamp",
                "Bore/Cal",
                "Form",
                "Status",
            ]
        )

        self.nfa_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.nfa_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add NFA Item")
        add_btn.clicked.connect(self.open_add_nfa_item_dialog)
        btn_layout.addWidget(add_btn)

        log_btn = QPushButton("Log Maintenance")
        log_btn.clicked.connect(lambda: self.view_item_history(GearCategory.NFA_ITEM))
        btn_layout.addWidget(log_btn)

        history_btn = QPushButton("View History")
        history_btn.clicked.connect(
            lambda: self.view_item_history(GearCategory.NFA_ITEM)
        )
        btn_layout.addWidget(history_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_selected_nfa_item)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_nfa_items(self):
        self.nfa_table.setRowCount(0)
        items = self.repo.get_all_nfa_items()

        for i, item in enumerate(items):
            self.nfa_table.insertRow(i)
            self.nfa_table.setItem(i, 0, QTableWidgetItem(item.name))
            self.nfa_table.setItem(i, 1, QTableWidgetItem(item.nfa_type.value))
            self.nfa_table.setItem(i, 2, QTableWidgetItem(item.manufacturer))
            self.nfa_table.setItem(i, 3, QTableWidgetItem(item.serial_number))

            tax_item = QTableWidgetItem(item.tax_stamp_id)
            tax_item.setBackground(QColor(60, 100, 60))
            self.nfa_table.setItem(i, 4, tax_item)

            self.nfa_table.setItem(i, 5, QTableWidgetItem(item.caliber_bore))
            self.nfa_table.setItem(i, 6, QTableWidgetItem(item.form_type))

            status_item = QTableWidgetItem(item.status.value)
            if item.status == CheckoutStatus.CHECKED_OUT:
                status_item.setBackground(QColor(100, 40, 40))
            self.nfa_table.setItem(i, 7, status_item)

    def delete_selected_nfa_item(self):
        row = self.nfa_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an NFA item to delete")
            return

        items = self.repo.get_all_nfa_items()
        selected = items[row]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Permanently delete '{selected.name}'?\n\nThis will also delete all maintenance logs and checkout history.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_nfa_item(selected.id)
            self.refresh_nfa_items()
            QMessageBox.information(
                self, "Deleted", f"'{selected.name}' has been deleted"
            )

    def open_add_nfa_item_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add NFA Item")
        dialog.setMinimumWidth(500)

        layout = QFormLayout()

        name_input = QLineEdit()
        name_input.setPlaceholderText("e.g., Dead Air Primal")
        layout.addRow("Name:", name_input)

        type_combo = QComboBox()
        type_combo.addItems([t.value for t in NFAItemType])
        layout.addRow("NFA Type:", type_combo)

        mfg_input = QLineEdit()
        mfg_input.setPlaceholderText("Manufacturer serial number")
        layout.addRow("Manufacturer:", mfg_input)

        serial_input = QLineEdit()
        serial_input.setPlaceholderText("Manufacturer Serial Number")
        layout.addRow("Serial #:", serial_input)

        tax_stamp_input = QLineEdit()
        tax_stamp_input.setPlaceholderText("ATF Form 1/4 serial (e.g., 2024123456789)")
        tax_stamp_input.setStyleSheet(
            "background-color: #3C5C3C; border: 2px solid #5C8C5C;"
        )
        layout.addRow("Tax Stamp ID*:", tax_stamp_input)

        caliber_input = QLineEdit()
        caliber_input.setPlaceholderText("e.g., .45 cal, 9mm, multi-cal")
        layout.addRow("Caliiber/Bore:", caliber_input)

        form_combo = QComboBox()
        form_combo.addItems(["Form 1", "Form 4"])
        layout.addRow("Form Type:", form_combo)

        trust_input = QLineEdit()
        trust_input.setPlaceholderText("Trust name (if applicable)")
        layout.addRow("Trust Name:", trust_input)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(60)
        notes_input.setPlaceholderText("e.g. Rated for .45-70, full-auto rated")
        layout.addRow("Notes:", notes_input)

        # Warning Label
        warning = QLabel("⚠️ Keep tax stamp copy with NFA item when transporting.")
        warning.setStyleSheet("color: #FF6B6B; font-weight: bold; padding: 10px;")
        layout.addRow(warning)

        save_btn = QPushButton("Save")

        def save():
            if not name_input.text() or not tax_stamp_input.text():
                QMessageBox.warning(
                    dialog, "Error", "Name and tax stamp ID are required"
                )
                return

            item = NFAItem(
                id=str(uuid.uuid4()),
                name=name_input.text(),
                nfa_type=NFAItemType(type_combo.currentText()),
                manufacturer=mfg_input.text(),
                serial_number=serial_input.text(),
                tax_stamp_id=tax_stamp_input.text(),
                caliber_bore=caliber_input.text(),
                purchase_date=datetime.now(),
                form_type=form_combo.currentText(),
                trust_name=trust_input.text(),
                notes=notes_input.toPlainText(),
            )
            self.repo.add_nfa_item(item)
            self.refresh_nfa_items()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    # ============== TRANSFER METHODS ==============
    def create_transfers_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel("Record of all firearms sold/transferred")
        info_label.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["Date", "Firearm", "Caliber", "Serial", "Buyer", "DL #", "Price"]
        )

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)
        self.transfers_table = table

        btn_layout = QHBoxLayout()

        view_btn = QPushButton("View Details")
        view_btn.clicked.connect(self.view_transfer_details)
        btn_layout.addWidget(view_btn)

        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_transfers)
        btn_layout.addWidget(export_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_transfers(self):
        self.transfers_table.setRowCount(0)
        transfers = self.repo.get_all_transfers()

        for i, (transfer, firearm) in enumerate(transfers):
            self.transfers_table.insertRow(i)
            self.transfers_table.setItem(
                i, 0, QTableWidgetItem(transfer.transfer_date.strftime("%Y-%m-%d"))
            )
            self.transfers_table.setItem(i, 1, QTableWidgetItem(firearm.name))
            self.transfers_table.setItem(i, 2, QTableWidgetItem(firearm.caliber))
            self.transfers_table.setItem(i, 3, QTableWidgetItem(firearm.serial_number))
            self.transfers_table.setItem(i, 4, QTableWidgetItem(transfer.buyer_name))
            self.transfers_table.setItem(
                i, 5, QTableWidgetItem(transfer.buyer_dl_number)
            )

            price_text = (
                f"${transfer.sale_price:.2f}" if transfer.sale_price > 0 else "N/A"
            )
            self.transfers_table.setItem(i, 6, QTableWidgetItem(price_text))

    def create_import_export_tab(self):
        """Create Import/Export tab using CSV import/export module."""
        widget = create_import_export_tab(
            repo=self.repo, message_box_class=QMessageBox, qfiledialog_class=QFileDialog
        )
        return widget

    def view_transfer_details(self):
        row = self.transfers_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a transfer to view details")
            return

        transfers = self.repo.get_all_transfers()
        transfer, firearm = transfers[row]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Transfer Details: {firearm.name}")
        dialog.setMinimumWidth(500)

        layout = QFormLayout()

        # Firearm info
        layout.addRow(QLabel("=== FIREARM INFORMATION ==="))
        layout.addRow("Name:", QLabel(firearm.name))
        layout.addRow("Caliber:", QLabel(firearm.caliber))
        layout.addRow("Serial #:", QLabel(firearm.serial_number))

        layout.addRow(QLabel(""))  # Spacer

        # Transfer info
        layout.addRow(QLabel("=== TRANSFER INFORMATION ==="))
        layout.addRow(
            "Transfer Date:", QLabel(transfer.transfer_date.strftime("%Y-%m-%d"))
        )
        layout.addRow("Buyer Name:", QLabel(transfer.buyer_name))
        layout.addRow("Buyer Address:", QLabel(transfer.buyer_address))
        layout.addRow("DL Number:", QLabel(transfer.buyer_dl_number))

        if transfer.buyer_ltc_number:
            layout.addRow("LTC Number:", QLabel(transfer.buyer_ltc_number))

        if transfer.sale_price > 0:
            layout.addRow("Sale Price:", QLabel(f"${transfer.sale_price:.2f}"))

        if transfer.ffl_dealer:
            layout.addRow(QLabel(""))  # Spacer
            layout.addRow(QLabel("=== FFL INFORMATION ==="))
            layout.addRow("FFL Dealer:", QLabel(transfer.ffl_dealer))
            layout.addRow("FFL License:", QLabel(transfer.ffl_license))

        if transfer.notes:
            layout.addRow(QLabel(""))  # Spacer
            layout.addRow("Notes:", QLabel(transfer.notes))

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addRow(close_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def export_transfers(self):
        from pathlib import Path

        output_path = (
            Path.home()
            / "Documents"
            / f"firearm_transfers_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        import csv

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Transfer Date",
                    "Firearm Name",
                    "Caliber",
                    "Serial Number",
                    "Buyer Name",
                    "Buyer Address",
                    "Buyer DL#",
                    "Buyer LTC#",
                    "Sale Price",
                    "FFL Dealer",
                    "FFL License",
                    "Notes",
                ]
            )

            transfers = self.repo.get_all_transfers()
            for transfer, firearm in transfers:
                writer.writerow(
                    [
                        transfer.transfer_date.strftime("%Y-%m-%d"),
                        firearm.name,
                        firearm.caliber,
                        firearm.serial_number,
                        transfer.buyer_name,
                        transfer.buyer_address,
                        transfer.buyer_dl_number,
                        transfer.buyer_ltc_number,
                        f"${transfer.sale_price:.2f}"
                        if transfer.sale_price > 0
                        else "",
                        transfer.ffl_dealer,
                        transfer.ffl_license,
                        transfer.notes,
                    ]
                )

        QMessageBox.information(
            self, "Exported", f"Transfer records exported to:\n{output_path}"
        )

    # ============== SHARED METHODS ==============

    def open_log_dialog(self, item_type: GearCategory):
        if item_type == GearCategory.FIREARM:
            items = self.repo.get_all_firearms()
            item_names = [f.name for f in items]
        else:
            items = self.repo.get_all_soft_gear()
            item_names = [g.name for g in items]

        if not items:
            QMessageBox.warning(self, "Error", "No items to log maintenance for")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Log Maintenance")
        dialog.setMinimumWidth(400)

        layout = QFormLayout()

        item_combo = QComboBox()
        item_combo.addItems(item_names)
        layout.addRow("Item:", item_combo)

        type_combo = QComboBox()
        type_combo.addItems([t.value for t in MaintenanceType])
        layout.addRow("Type:", type_combo)

        details_input = QTextEdit()
        details_input.setMaximumHeight(80)
        layout.addRow("Details:", details_input)

        ammo_spin = QSpinBox()
        ammo_spin.setRange(0, 10000)
        layout.addRow("Rounds fired:", ammo_spin)

        save_btn = QPushButton("Save")

        def save():
            selected = items[item_combo.currentIndex()]
            log_type = MaintenanceType(type_combo.currentText())
            details = details_input.toPlainText()

            if item_type == GearCategory.FIREARM:
                self.repo.mark_maintenance_done(selected.id, log_type, details)
            else:
                log = MaintenanceLog(
                    id=str(uuid.uuid4()),
                    item_id=selected.id,
                    item_type=item_type,
                    log_type=log_type,
                    date=datetime.now(),
                    details=details,
                    ammo_count=ammo_spin.value() if ammo_spin.value() > 0 else None,
                )
                self.repo.log_maintenance(log)
            self.refresh_all()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def view_item_history(self, item_type: GearCategory):
        if item_type == GearCategory.FIREARM:
            table = self.firearm_table
            items = self.repo.get_all_firearms()
        else:
            table = self.soft_gear_table
            items = self.repo.get_all_soft_gear()

        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an item first")
            return

        selected = items[row]
        logs = self.repo.get_logs_for_item(selected.id)

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
                i, 0, QTableWidgetItem(log.date.strftime("%Y-%m-%d %H:%M"))
            )
            hist_table.setItem(i, 1, QTableWidgetItem(log.log_type.value))
            hist_table.setItem(i, 2, QTableWidgetItem(log.details or ""))
            hist_table.setItem(
                i, 3, QTableWidgetItem(str(log.ammo_count) if log.ammo_count else "")
            )

        layout.addWidget(hist_table)
        dialog.setLayout(layout)
        dialog.exec()

    # ============== RELOADING TAB ==============

    def create_reloading_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        info_label = QLabel(
            "Personal reload log: batches of handloads with components and results."
        )
        info_label.setStyleSheet("color: #888; font-style: italic; padding: 5px;")
        layout.addWidget(info_label)

        self.reload_table = QTableWidget()
        self.reload_table.setColumnCount(8)
        self.reload_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Cartridge",
                "Firearm",
                "Bullet",
                "Powder/Charge",
                "COAL",
                "Vel/Group",
                "Status",
            ]
        )
        self.reload_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.reload_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Batch")
        add_btn.clicked.connect(self.open_add_reload_batch_dialog)
        btn_layout.addWidget(add_btn)

        duplicate_btn = QPushButton("Duplicate Batch")
        duplicate_btn.clicked.connect(self.duplicate_reload_batch)
        btn_layout.addWidget(duplicate_btn)

        log_btn = QPushButton("Log Results")
        log_btn.clicked.connect(self.open_log_reload_results_dialog)
        btn_layout.addWidget(log_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("background-color: #6B2020;")
        delete_btn.clicked.connect(self.delete_selected_reload_batch)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)
        widget.setLayout(layout)
        return widget

    def refresh_reloads(self):
        self.reload_table.setRowCount(0)
        batches = self.repo.get_all_reload_batches()
        firearms = {f.id: f for f in self.repo.get_all_firearms()}

        for i, b in enumerate(batches):
            self.reload_table.insertRow(i)

            self.reload_table.setItem(
                i, 0, QTableWidgetItem(b.date_created.strftime("%Y-%m-%d"))
            )
            self.reload_table.setItem(i, 1, QTableWidgetItem(b.cartridge))

            fw_name = ""
            if b.firearm_id and b.firearm_id in firearms:
                fw_name = firearms[b.firearm_id].name
            self.reload_table.setItem(i, 2, QTableWidgetItem(fw_name))

            bullet_text = f"{b.bullet_weight_gr or ''}gr {b.bullet_maker} {b.bullet_model}".strip()
            self.reload_table.setItem(i, 3, QTableWidgetItem(bullet_text))

            powder_text = b.powder_name
            if b.powder_charge_gr:
                powder_text = f"{b.powder_charge_gr} gr {b.powder_name}"
            self.reload_table.setItem(i, 4, QTableWidgetItem(powder_text))

            coal_text = f'{b.coal_in:.3f}"' if b.coal_in else ""
            self.reload_table.setItem(i, 5, QTableWidgetItem(coal_text))

            vel_group = ""
            if b.avg_velocity:
                vel_group = f"{b.avg_velocity} fps"
            if b.group_size_inches and b.group_distance_yards:
                group_str = f'{b.group_size_inches}" @ {b.group_distance_yards} yd'
                vel_group = f"{vel_group}, {group_str}" if vel_group else group_str
            self.reload_table.setItem(i, 6, QTableWidgetItem(vel_group))

            self.reload_table.setItem(i, 7, QTableWidgetItem(b.status))

    def _get_selected_reload_batch(self) -> ReloadBatch | None:
        row = self.reload_table.currentRow()
        if row < 0:
            return None
        batches = self.repo.get_all_reload_batches()
        if row >= len(batches):
            return None
        return batches[row]

    def open_add_reload_batch_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Reload Batch")
        dialog.setMinimumWidth(500)

        layout = QFormLayout()

        cartridge_input = QLineEdit()
        cartridge_input.setPlaceholderText(".45-70 Govt, .45 ACP, etc.")
        layout.addRow("Cartridge*:", cartridge_input)

        firearms = self.repo.get_all_firearms()
        firearm_combo = QComboBox()
        firearm_combo.addItem("Unassigned")
        for fw in firearms:
            firearm_combo.addItem(fw.name)
        layout.addRow("Firearm:", firearm_combo)

        bullet_maker_input = QLineEdit()
        layout.addRow("Bullet maker:", bullet_maker_input)

        bullet_model_input = QLineEdit()
        layout.addRow("Bullet model:", bullet_model_input)

        bullet_weight_spin = QSpinBox()
        bullet_weight_spin.setRange(0, 1000)
        layout.addRow("Bullet weight (gr):", bullet_weight_spin)

        powder_name_input = QLineEdit()
        layout.addRow("Powder name:", powder_name_input)

        powder_charge_input = QLineEdit()
        powder_charge_input.setPlaceholderText("e.g., 54.0")
        layout.addRow("Charge (gr):", powder_charge_input)

        powder_lot_input = QLineEdit()
        layout.addRow("Powder lot:", powder_lot_input)

        primer_maker_input = QLineEdit()
        layout.addRow("Primer maker:", primer_maker_input)

        primer_type_input = QLineEdit()
        primer_type_input.setPlaceholderText("LP, LPM, LR, etc.")
        layout.addRow("Primer type:", primer_type_input)

        case_brand_input = QLineEdit()
        layout.addRow("Case brand:", case_brand_input)

        case_times_spin = QSpinBox()
        case_times_spin.setRange(0, 50)
        layout.addRow("Times fired:", case_times_spin)

        case_prep_input = QTextEdit()
        case_prep_input.setMaximumHeight(60)
        case_prep_input.setPlaceholderText("Trimmed, annealed, neck turned, etc.")
        layout.addRow("Case prep:", case_prep_input)

        coal_input = QLineEdit()
        coal_input.setPlaceholderText("e.g., 2.535")
        layout.addRow("COAL (in):", coal_input)

        crimp_input = QLineEdit()
        crimp_input.setPlaceholderText("roll, taper, none")
        layout.addRow("Crimp:", crimp_input)

        intended_use_combo = QComboBox()
        intended_use_combo.addItems(["DEFENSE", "HUNTING", "COMPETITION", "TRAINING"])
        layout.addRow("Intended Use:", intended_use_combo)

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(80)
        layout.addRow("Notes:", notes_input)

        save_btn = QPushButton("Save")

        def save():
            if not cartridge_input.text():
                QMessageBox.warning(dialog, "Error", "Cartridge is required")
                return

            firearm_id = None
            idx = firearm_combo.currentIndex()
            if idx > 0:
                firearm_id = firearms[idx - 1].id

            try:
                charge = (
                    float(powder_charge_input.text())
                    if powder_charge_input.text()
                    else None
                )
            except ValueError:
                QMessageBox.warning(
                    dialog, "Error", "Charge must be a number (e.g., 54.0)"
                )
                return

            try:
                coal = float(coal_input.text()) if coal_input.text() else None
            except ValueError:
                QMessageBox.warning(
                    dialog, "Error", "COAL must be a number (e.g., 2.535)"
                )
                return

            batch = ReloadBatch(
                id=str(uuid.uuid4()),
                cartridge=cartridge_input.text(),
                firearm_id=firearm_id,
                date_created=datetime.now(),
                bullet_maker=bullet_maker_input.text(),
                bullet_model=bullet_model_input.text(),
                bullet_weight_gr=bullet_weight_spin.value() or None,
                powder_name=powder_name_input.text(),
                powder_charge_gr=charge,
                powder_lot=powder_lot_input.text(),
                primer_maker=primer_maker_input.text(),
                primer_type=primer_type_input.text(),
                case_brand=case_brand_input.text(),
                case_times_fired=case_times_spin.value() or None,
                case_prep_notes=case_prep_input.toPlainText(),
                coal_in=coal,
                crimp_style=crimp_input.text(),
                intended_use=intended_use_combo.currentText(),
                status="WORKUP",
                notes=notes_input.toPlainText(),
            )
            self.repo.add_reload_batch(batch)
            self.refresh_reloads()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def duplicate_reload_batch(self):
        batch = self._get_selected_reload_batch()
        if not batch:
            QMessageBox.warning(self, "Error", "Select a batch to duplicate")
            return

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
            notes=f"(DUP from {batch.date_created.strftime('%Y-%m-%d')}) {batch.notes}",
        )
        self.repo.add_reload_batch(new_batch)
        self.refresh_reloads()
        QMessageBox.information(
            self,
            "Duplicated",
            f"'{batch.cartridge}' batch duplicated for further development.",
        )

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

            updated = ReloadBatch(
                id=batch.id,
                cartridge=batch.cartridge,
                firearm_id=batch.firearm_id,
                date_created=batch.date_created,
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
                test_date=test_dt,
                avg_velocity=avg_vel_spin.value() or None,
                es=es_spin.value() or None,
                sd=sd_spin.value() or None,
                group_size_inches=group_size,
                group_distance_yards=group_dist_spin.value() or None,
                intended_use=batch.intended_use,
                status=status_combo.currentText(),
                notes=notes_input.toPlainText(),
            )
            self.repo.update_reload_batch(updated)
            self.refresh_reloads()
            dialog.accept()

        save_btn.clicked.connect(save)
        layout.addRow(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def delete_selected_reload_batch(self):
        batch = self._get_selected_reload_batch()
        if not batch:
            QMessageBox.warning(self, "Error", "Select a batch to delete")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Permanently delete reload batch '{batch.cartridge}' from log?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.repo.delete_reload_batch(batch.id)
            self.refresh_reloads()
            QMessageBox.information(
                self, "Deleted", "Reload batch has been deleted from log."
            )

    def refresh_all(self):
        self.refresh_firearms()
        self.refresh_attachments()
        self.refresh_reloads()
        self.refresh_soft_gear()
        self.refresh_consumables()
        self.refresh_loadouts()
        self.refresh_checkouts()
        self.refresh_borrowers()
        self.refresh_nfa_items()
        self.refresh_transfers()


def main():
    app = QApplication(sys.argv)

    # Apply Dark Mode
    app.setStyle("Fusion")

    # Create dark palette
    palette = QPalette()

    # Base Colors
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    app.setPalette(palette)

    window = GearTrackerApp()
    window.show()
    sys.exit(app.exec())


class DuplicateResolutionDialog(QDialog):
    def __init__(self, parent, entity_type: str, existing, imported):
        super().__init__(parent)
        self.setWindowTitle("Duplicate Detected")
        self.setMinimumWidth(600)

        layout = QVBoxLayout()

        warning = QLabel(f"A duplicate {entity_type} was detected:")
        warning.setStyleSheet("font-weight: bold; color: #B22222;")
        layout.addWidget(warning)

        existing_group = QGroupBox("Existing in database:")
        existing_layout = QVBoxLayout()
        existing_text = self._format_item(existing)
        existing_label = QLabel(existing_text)
        existing_label.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        existing_layout.addWidget(existing_label)
        existing_group.setLayout(existing_layout)
        layout.addWidget(existing_group)

        imported_group = QGroupBox("Imported from CSV:")
        imported_layout = QVBoxLayout()
        imported_text = self._format_item(imported)
        imported_label = QLabel(imported_text)
        imported_label.setStyleSheet("background-color: #f0fff0; padding: 10px;")
        imported_layout.addWidget(imported_label)
        imported_group.setLayout(imported_layout)
        layout.addWidget(imported_group)

        layout.addWidget(QLabel("\nWhat would you like to do?"))

        btn_layout = QHBoxLayout()

        self.skip_btn = QPushButton("Skip (keep existing)")
        self.skip_btn.clicked.connect(lambda: self.done("skip"))
        btn_layout.addWidget(self.skip_btn)

        self.overwrite_btn = QPushButton("Overwrite (replace existing)")
        self.overwrite_btn.clicked.connect(lambda: self.done("overwrite"))
        btn_layout.addWidget(self.overwrite_btn)

        self.rename_btn = QPushButton("Import as new (rename)")
        self.rename_btn.clicked.connect(lambda: self.done("rename"))
        btn_layout.addWidget(self.rename_btn)

        self.cancel_btn = QPushButton("Cancel Import")
        self.cancel_btn.clicked.connect(lambda: self.done("cancel"))
        self.cancel_btn.setStyleSheet("background-color: #6B2020;")
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.action = None

    def _format_item(self, item) -> str:
        if hasattr(item, "name"):
            lines = [f"Name: {item.name}"]
        if hasattr(item, "serial_number"):
            lines.append(f"Serial: {item.serial_number}")
        if hasattr(item, "caliber"):
            lines.append(f"Caliber: {item.caliber}")
        if hasattr(item, "category"):
            lines.append(f"Category: {item.category}")
        if hasattr(item, "brand"):
            lines.append(f"Brand: {item.brand}")
        if hasattr(item, "email"):
            lines.append(f"Email: {item.email}")
        if hasattr(item, "phone"):
            lines.append(f"Phone: {item.phone}")

        return "\n".join(lines)

    def get_action(self) -> str:
        return self.action


class ImportProgressDialog(QDialog):
    def __init__(self, parent, total_rows: int):
        super().__init__(parent)
        self.setWindowTitle("Importing Data")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        self.status_label = QLabel("Starting import...")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(total_rows)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.errors_text = QTextEdit()
        self.errors_text.setReadOnly(True)
        self.errors_text.setMaximumHeight(150)
        self.errors_text.setPlaceholderText("Any errors will appear here...")
        layout.addWidget(self.errors_text)

        btn_layout = QHBoxLayout()

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setEnabled(False)
        self.continue_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.continue_btn)

        self.cancel_btn = QPushButton("Cancel Import")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def update_progress(self, current: int, message: str):
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
        QApplication.processEvents()

    def add_error(self, error_text: str):
        if error_text:
            self.errors_text.append(error_text)

    def finish(self):
        self.continue_btn.setEnabled(True)
        self.status_label.setText("Import complete!")

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
                self.repo.export_complete_csv(Path(file_path))
                QMessageBox.information(
                    self, "Export Complete", f"Data exported to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error", f"Failed to export:\n{str(e)}"
                )

    def preview_csv_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", str(Path.home() / "Documents"), "CSV Files (*.csv)"
        )

        if file_path:
            try:
                result = self.repo.preview_import(Path(file_path))
                self.show_import_results("Preview Results", result)
            except Exception as e:
                QMessageBox.critical(
                    self, "Preview Error", f"Failed to preview:\n{str(e)}"
                )

    def import_csv_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", str(Path.home() / "Documents"), "CSV Files (*.csv)"
        )

        if not file_path:
            return

        # First, preview to show what will be imported
        try:
            preview_result = self.repo.preview_import(Path(file_path))

            if preview_result.errors:
                QMessageBox.warning(
                    self,
                    "Import Validation Failed",
                    f"CSV has {len(preview_result.errors)} errors.\n\nImport may fail or have unexpected results.",
                )
                self.show_import_results("Preview Results", preview_result)
                return

            # Confirm with user
            msg = f"Import will process {preview_result.total_rows} rows.\n"
            if preview_result.total_rows > 0:
                msg += f"\n\nEstimated:\n"
                msg += f"  • Import: {preview_result.imported} rows\n"
                msg += f"  • Skip: {preview_result.skipped} rows\n"
            msg += "\n\nContinue?"

            reply = QMessageBox.question(
                self,
                "Confirm Import",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                return

            # Create progress dialog
            progress_dialog = ImportProgressDialog(self, preview_result.total_rows)

            # Define progress callback
            def progress_callback(current, total, entity_type, message):
                progress_dialog.update_progress(current, f"Importing {entity_type}...")
                if message:
                    progress_dialog.add_error(message)

            # Define duplicate handler
            def duplicate_handler(entity_type, existing, imported):
                dialog = DuplicateResolutionDialog(
                    self, entity_type, existing, imported
                )
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    return dialog.get_action()
                else:
                    return "cancel"

            # Actual import
            result = self.repo.import_complete_csv(
                Path(file_path),
                dry_run=False,
                duplicate_callback=duplicate_handler,
                progress_callback=progress_callback,
            )

            progress_dialog.finish()

            # Show results
            self.show_import_results("Import Results", result)

            # Refresh UI if any rows were imported
            if result.imported > 0 or result.overwritten > 0:
                self.refresh_all()

        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import:\n{str(e)}")

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
                self.repo.generate_csv_template(Path(file_path), entity_type=None)
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
                self.repo.generate_csv_template(Path(file_path), entity_type=csv_entity)
                QMessageBox.information(
                    self, "Template Created", f"Template saved to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Template Error", f"Failed to generate template:\n{str(e)}"
                )

    def show_import_results(self, title: str, result):
        self.import_results_group.setTitle(title)
        self.import_results_group.setVisible(True)

        summary = f"Total rows: {result.total_rows}\n"
        summary += f"Imported: {result.imported}\n"
        summary += f"Skipped: {result.skipped}\n"
        summary += f"Overwritten: {result.overwritten}\n"
        summary += f"Errors: {len(result.errors)}\n"
        summary += f"Warnings: {len(result.warnings)}"

        self.import_results_label.setText(summary)

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

        self.import_details_text.setText(details)


if __name__ == "__main__":
    main()
