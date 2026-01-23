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
from src.ui.tabs.base_tab import BaseTab


class CheckoutsTab(BaseTab):
    def __init__(self, repo, refresh_callback=None):
        super().__init__(repo, refresh_callback)
        self.setup_buttons_and_table()

    def setup_buttons_and_table(self):
        layout = self.layout()
        layout.addWidget(QLabel("<b>View active checkouts and return items.</b>"))

        self.create_table(
            ["Item", "Type", "Borrower", "Checkout Date", "Expected Return", "Notes"]
        )

        btn_layout = QHBoxLayout()

        self.checkout_btn = QPushButton("Checkout Item")
        btn_layout.addWidget(self.checkout_btn)

        self.return_btn = QPushButton("Return Selected")
        self.return_btn.setStyleSheet("background-color: #206B20;")
        btn_layout.addWidget(self.return_btn)

        layout.addLayout(btn_layout)

    def refresh(self):
        self.table.setRowCount(0)
        checkouts = self.repo.get_active_checkouts()

        for i, c in enumerate(checkouts):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(c.item_id))
            self.table.setItem(i, 1, QTableWidgetItem(c.item_type))
            self.table.setItem(i, 2, QTableWidgetItem(c.borrower_name))
            self.table.setItem(
                i, 3, QTableWidgetItem(c.checkout_date.strftime("%Y-%m-%d"))
            )

            expected = (
                c.expected_return.strftime("%Y-%m-%d") if c.expected_return else ""
            )
            self.table.setItem(i, 4, QTableWidgetItem(expected))
            self.table.setItem(i, 5, QTableWidgetItem(c.notes or ""))

    def get_selected_checkout(self, row):
        checkouts = self.repo.get_active_checkouts()
        if 0 <= row < len(checkouts):
            return checkouts[row]
        return None

    def connect_signals(self, checkout, return_item):
        self.checkout_btn.clicked.connect(checkout)
        self.return_btn.clicked.connect(return_item)
