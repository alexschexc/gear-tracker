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
    Attachment,
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
        self.tabs.addTab(self.create_soft_gear_tab(), "🎒 Soft Gear")
        self.tabs.addTab(self.create_consumables_tab(), "📦 Consumables")
        self.tabs.addTab(self.create_checkouts_tab(), "📋 Checkouts")
        self.tabs.addTab(self.create_borrowers_tab(), "👥 Borrowers")
        self.tabs.addTab(self.create_nfa_items_tab(), "🔇 NFA Items")
        self.tabs.addTab(self.create_transfers_tab(), "📋 Transfers")
        # Refresh all on startup
        self.refresh_all()

    # ============== FIREARMS TAB ==============

    def create_firearms_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.firearm_table = QTableWidget()
        self.firearm_table.setColumnCount(6)
        self.firearm_table.setHorizontalHeaderLabels(
            ["Name", "Caliber", "Serial", "Status", "Last Cleaned", "Notes"]
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
            self.firearm_table.setItem(i, 3, status_item)

            last_clean = self.repo.last_cleaning_date(fw.id)
            clean_text = last_clean.strftime("%Y-%m-%d") if last_clean else "Never"
            clean_item = QTableWidgetItem(clean_text)
            if last_clean and (datetime.now() - last_clean).days > 90:
                clean_item.setBackground(QColor(255, 255, 150))  # Yellow warning
            self.firearm_table.setItem(i, 4, clean_item)

            self.firearm_table.setItem(i, 5, QTableWidgetItem(fw.notes))

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

        consumables = self.rep.get_all_consumables()
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

        reply = QMessageBox.question(
            self,
            "Confirm Return",
            f"Mark '{item_name}' as returned?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.repo.return_item(checkout.id)
            self.refresh_all()

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
            log = MaintenanceLog(
                id=str(uuid.uuid4()),
                item_id=selected.id,
                item_type=item_type,
                log_type=MaintenanceType(type_combo.currentText()),
                date=datetime.now(),
                details=details_input.toPlainText(),
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

    def refresh_all(self):
        self.refresh_firearms()
        self.refresh_attachments()
        self.refresh_soft_gear()
        self.refresh_consumables()
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


if __name__ == "__main__":
    main()
