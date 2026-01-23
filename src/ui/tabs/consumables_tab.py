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


class ConsumablesTab(BaseTab):
    def __init__(self, repo, refresh_callback=None):
        super().__init__(repo, refresh_callback)
        self.setup_buttons_and_table()

    def setup_buttons_and_table(self):
        layout = self.layout()
        layout.addWidget(
            QLabel(
                "<b>Track ammunition, batteries, medical supplies, and other consumables.</b>"
            )
        )

        self.create_table(["Name", "Category", "Unit", "Quantity", "Min Qty", "Status"])

        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("Add Consumable")
        btn_layout.addWidget(self.add_btn)

        self.add_stock_btn = QPushButton("Add Stock")
        btn_layout.addWidget(self.add_stock_btn)

        self.use_stock_btn = QPushButton("Use Stock")
        btn_layout.addWidget(self.use_stock_btn)

        self.history_btn = QPushButton("View History")
        btn_layout.addWidget(self.history_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet("background-color: #6B2020;")
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

    def refresh(self):
        self.table.setRowCount(0)
        consumables = self.repo.get_all_consumables()

        for i, cons in enumerate(consumables):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(cons.name))
            self.table.setItem(i, 1, QTableWidgetItem(cons.category))
            self.table.setItem(i, 2, QTableWidgetItem(cons.unit))
            self.table.setItem(i, 3, QTableWidgetItem(str(cons.quantity)))

            qty_item = QTableWidgetItem(str(cons.min_quantity))
            if cons.quantity <= cons.min_quantity:
                qty_item.setBackground(QColor(255, 200, 100))
            self.table.setItem(i, 4, qty_item)

            status = "LOW" if cons.quantity <= cons.min_quantity else "OK"
            status_item = QTableWidgetItem(status)
            if status == "LOW":
                status_item.setBackground(QColor(255, 150, 150))
            self.table.setItem(i, 5, status_item)

    def get_selected_consumable(self, row):
        consumables = self.repo.get_all_consumables()
        if 0 <= row < len(consumables):
            return consumables[row]
        return None

    def connect_signals(self, add, add_stock, use_stock, history, delete):
        self.add_btn.clicked.connect(add)
        self.add_stock_btn.clicked.connect(add_stock)
        self.use_stock_btn.clicked.connect(use_stock)
        self.history_btn.clicked.connect(history)
        self.delete_btn.clicked.connect(delete)
