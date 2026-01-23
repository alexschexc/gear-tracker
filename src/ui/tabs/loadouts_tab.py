from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
    QHeaderView,
    QLabel,
)
from PyQt6.QtGui import QColor
from src.ui.tabs.base_tab import BaseTab


class LoadoutsTab(BaseTab):
    def __init__(self, repo, refresh_callback=None):
        super().__init__(repo, refresh_callback)
        self.setup_buttons_and_table()

    def setup_buttons_and_table(self):
        layout = self.layout()
        layout.addWidget(
            QLabel("<b>Hunt/Trip loadout profiles for one-click checkout.</b>")
        )

        self.create_table(["Name", "Description", "Items", "Consumables", "Created"])

        btn_layout = QHBoxLayout()

        self.create_btn = QPushButton("Create Loadout")
        btn_layout.addWidget(self.create_btn)

        self.edit_btn = QPushButton("Edit Loadout")
        btn_layout.addWidget(self.edit_btn)

        self.duplicate_btn = QPushButton("Duplicate Loadout")
        btn_layout.addWidget(self.duplicate_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet("background-color: #6B2020;")
        btn_layout.addWidget(self.delete_btn)

        self.checkout_btn = QPushButton("Checkout Loadout")
        self.checkout_btn.setStyleSheet("background-color: #20206B; font-weight: bold;")
        btn_layout.addWidget(self.checkout_btn)

        layout.addLayout(btn_layout)

    def refresh(self):
        self.table.setRowCount(0)
        loadouts = self.repo.get_all_loadouts()

        for i, lo in enumerate(loadouts):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(lo.name))
            self.table.setItem(i, 1, QTableWidgetItem(lo.description or ""))

            items = self.repo.get_loadout_items(lo.id)
            item_names = [item.item_id for item in items]
            self.table.setItem(i, 2, QTableWidgetItem(f"{len(items)} items"))

            consumables = self.repo.get_loadout_consumables(lo.id)
            self.table.setItem(
                i, 3, QTableWidgetItem(f"{len(consumables)} consumables")
            )

            created = (
                lo.created_date.strftime("%Y-%m-%d") if lo.created_date else "Unknown"
            )
            self.table.setItem(i, 4, QTableWidgetItem(created))

    def get_selected_loadout(self, row):
        loadouts = self.repo.get_all_loadouts()
        if 0 <= row < len(loadouts):
            return loadouts[row]
        return None

    def connect_signals(self, create, edit, duplicate, delete, checkout):
        self.create_btn.clicked.connect(create)
        self.edit_btn.clicked.connect(edit)
        self.duplicate_btn.clicked.connect(duplicate)
        self.delete_btn.clicked.connect(delete)
        self.checkout_btn.clicked.connect(checkout)
