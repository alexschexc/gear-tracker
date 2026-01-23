from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QColorDialog,
)
from PyQt6.QtGui import QColor
from datetime import datetime
from src.ui.tabs.base_tab import BaseTab


class FirearmsTab(BaseTab):
    def __init__(self, repo, refresh_callback=None):
        super().__init__(repo, refresh_callback)
        self.setup_buttons_and_table()

    def setup_buttons_and_table(self):
        layout = self.layout()
        layout.addWidget(
            QLabel("<b>Manage firearms, track maintenance, and handle transfers.</b>")
        )

        self.create_table(
            ["Name", "Caliber", "Serial", "Status", "Rounds", "Last Cleaned", "Notes"]
        )

        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("Add Firearm")
        btn_layout.addWidget(self.add_btn)

        self.log_btn = QPushButton("Log Maintenance")
        btn_layout.addWidget(self.log_btn)

        self.history_btn = QPushButton("View History")
        btn_layout.addWidget(self.history_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet("background-color: #6B2020;")
        btn_layout.addWidget(self.delete_btn)

        self.transfer_btn = QPushButton("Transfer/Sell")
        self.transfer_btn.setStyleSheet("background-color: #6B6B20;")
        btn_layout.addWidget(self.transfer_btn)

        layout.addLayout(btn_layout)

    def refresh(self):
        self.table.setRowCount(0)
        firearms = self.repo.get_all_firearms()

        for i, fw in enumerate(firearms):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(fw.name))
            self.table.setItem(i, 1, QTableWidgetItem(fw.caliber))
            self.table.setItem(i, 2, QTableWidgetItem(fw.serial_number))

            status = fw.status.value if hasattr(fw.status, "value") else str(fw.status)
            status_item = QTableWidgetItem(status)

            if fw.status.value == "CHECKED_OUT":
                status_item.setBackground(QColor(255, 200, 200))

            self.table.setItem(i, 3, status_item)
            self.table.setItem(i, 4, QTableWidgetItem(str(fw.rounds_fired)))

            last_clean = self.repo.last_cleaning_date(fw.id)
            clean_text = last_clean.strftime("%Y-%m-%d") if last_clean else "Never"
            self.table.setItem(i, 5, QTableWidgetItem(clean_text))
            self.table.setItem(i, 6, QTableWidgetItem(fw.notes))

    def get_selected_firearm(self, row):
        firearms = self.repo.get_all_firearms()
        if 0 <= row < len(firearms):
            return firearms[row]
        return None

    def connect_signals(self, open_dialog, view_history, delete, transfer):
        self.add_btn.clicked.connect(open_dialog)
        self.log_btn.clicked.connect(lambda: open_dialog("FIREARM"))
        self.history_btn.clicked.connect(view_history)
        self.delete_btn.clicked.connect(delete)
        self.transfer_btn.clicked.connect(transfer)
