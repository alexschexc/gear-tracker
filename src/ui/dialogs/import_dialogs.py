from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTextEdit,
    QProgressBar,
)
from PyQt6.QtCore import Qt
from dataclasses import dataclass
from typing import Optional


@dataclass
class DuplicateResolution:
    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME = "rename"
    CANCEL = "cancel"


class DuplicateResolutionDialog(QDialog):
    def __init__(self, parent, entity_type: str, existing, imported):
        super().__init__(parent)
        self.setWindowTitle(f"Duplicate {entity_type}")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        warning = QLabel(f"A duplicate {entity_type} was detected:")
        warning.setStyleSheet("font-weight: bold; color: #B22222;")
        layout.addWidget(warning)

        existing_group = QGroupBox("Existing in database:")
        existing_layout = QVBoxLayout()
        existing_text = self._format_item(existing)
        existing_label = QLabel(existing_text)
        existing_label.setStyleSheet("background-color: #f0f0f0; padding: 10px;")
        existing_label.setWordWrap(True)
        existing_layout.addWidget(existing_label)
        existing_group.setLayout(existing_layout)
        layout.addWidget(existing_group)

        imported_group = QGroupBox("Imported from CSV:")
        imported_layout = QVBoxLayout()
        imported_text = self._format_item(imported)
        imported_label = QLabel(imported_text)
        imported_label.setStyleSheet("background-color: #f0fff0; padding: 10px;")
        imported_label.setWordWrap(True)
        imported_layout.addWidget(imported_label)
        imported_group.setLayout(imported_layout)
        layout.addWidget(imported_group)

        layout.addWidget(QLabel("\nWhat would you like to do?"))

        btn_layout = QHBoxLayout()

        self.skip_btn = QPushButton("Skip (keep existing)")
        self.skip_btn.clicked.connect(lambda: self.done(DuplicateResolution.SKIP))
        btn_layout.addWidget(self.skip_btn)

        self.overwrite_btn = QPushButton("Overwrite (replace existing)")
        self.overwrite_btn.clicked.connect(
            lambda: self.done(DuplicateResolution.OVERWRITE)
        )
        btn_layout.addWidget(self.overwrite_btn)

        self.rename_btn = QPushButton("Import as new (rename)")
        self.rename_btn.clicked.connect(lambda: self.done(DuplicateResolution.RENAME))
        btn_layout.addWidget(self.rename_btn)

        self.cancel_btn = QPushButton("Cancel Import")
        self.cancel_btn.clicked.connect(lambda: self.done(DuplicateResolution.CANCEL))
        self.cancel_btn.setStyleSheet("background-color: #6B2020; color: white;")
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self._result = None

    def _format_item(self, item) -> str:
        lines = []

        if hasattr(item, "name"):
            lines.append(f"Name: {item.name}")
        if hasattr(item, "serial_number") and item.serial_number:
            lines.append(f"Serial: {item.serial_number}")
        if hasattr(item, "caliber") and item.caliber:
            lines.append(f"Caliber: {item.caliber}")
        if hasattr(item, "category") and item.category:
            lines.append(f"Category: {item.category}")
        if hasattr(item, "brand") and item.brand:
            lines.append(f"Brand: {item.brand}")
        if hasattr(item, "cartridge") and item.cartridge:
            lines.append(f"Cartridge: {item.cartridge}")
        if hasattr(item, "email") and item.email:
            lines.append(f"Email: {item.email}")
        if hasattr(item, "phone") and item.phone:
            lines.append(f"Phone: {item.phone}")

        return "\n".join(lines) if lines else str(item)

    def done(self, result):
        self._result = result
        super().done(result)

    @property
    def result(self) -> str:
        return self._result


class ImportProgressDialog(QDialog):
    def __init__(self, parent, total_rows: int):
        super().__init__(parent)
        self.setWindowTitle("Importing Data")
        self.setMinimumWidth(450)

        layout = QVBoxLayout()

        self.status_label = QLabel("Starting import...")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
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

    def update_progress(self, current: int, total: int, entity_type: str, message: str):
        percent = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"{entity_type}: {message}")
        from PyQt6.QtWidgets import QApplication

        QApplication.processEvents()

    def add_error(self, error_text: str):
        if error_text:
            self.errors_text.append(error_text)

    def finish(self):
        self.continue_btn.setEnabled(True)
        self.status_label.setText("Import complete!")
