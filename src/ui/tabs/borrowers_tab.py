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


class BorrowersTab(BaseTab):
    def __init__(self, repo, refresh_callback=None):
        super().__init__(repo, refresh_callback)
        self.setup_buttons_and_table()

    def setup_buttons_and_table(self):
        layout = self.layout()
        layout.addWidget(QLabel("<b>Manage borrowers who can checkout gear.</b>"))

        self.create_table(["Name", "Phone", "Email", "Notes"])

        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("Add Borrower")
        btn_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet("background-color: #6B2020;")
        btn_layout.addWidget(self.delete_btn)

        layout.addLayout(btn_layout)

    def refresh(self):
        self.table.setRowCount(0)
        borrowers = self.repo.get_all_borrowers()

        for i, b in enumerate(borrowers):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(b.name))
            self.table.setItem(i, 1, QTableWidgetItem(b.phone or ""))
            self.table.setItem(i, 2, QTableWidgetItem(b.email or ""))
            self.table.setItem(i, 3, QTableWidgetItem(b.notes or ""))

    def get_selected_borrower(self, row):
        borrowers = self.repo.get_all_borrowers()
        if 0 <= row < len(borrowers):
            return borrowers[row]
        return None

    def connect_signals(self, add, delete):
        self.add_btn.clicked.connect(add)
        self.delete_btn.clicked.connect(delete)
