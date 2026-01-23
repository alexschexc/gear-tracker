from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QHeaderView


class BaseTab(QWidget):
    def __init__(self, repo, refresh_callback=None):
        super().__init__()
        self.repo = repo
        self.refresh_callback = refresh_callback
        self.table = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(0)
        self.table.setHorizontalHeaderLabels([])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)
        self.setLayout(layout)

    def create_table(self, columns):
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

    def refresh(self):
        pass

    def setup_buttons(self, layout, buttons):
        pass
