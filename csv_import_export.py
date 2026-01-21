"""
CSV Import/Export UI Module

This module provides UI components for CSV import/export functionality.
Integrate into main UI by importing and using create_import_export_tab().
"""

from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QComboBox,
    QTextEdit,
    QProgressBar,
    QFormLayout,
    QApplication,
)
from PyQt6.QtCore import Qt

from datetime import datetime
from pathlib import Path
import os


class DuplicateResolutionDialog(QDialog):
    """Dialog for handling duplicate items during import."""

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
        """Format item details for display."""
        lines = []

        if hasattr(item, "name"):
            lines.append(f"Name: {item.name}")
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
        """Get the user's chosen action."""
        return self.action


class ImportProgressDialog(QDialog):
    """Progress dialog for CSV import operations."""

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
        """Update progress bar and status message."""
        self.progress_bar.setValue(current)
        self.status_label.setText(message)
        QApplication.processEvents()

    def add_error(self, error_text: str):
        """Add error message to error display."""
        if error_text:
            self.errors_text.append(error_text)

    def finish(self):
        """Enable continue button and show completion status."""
        self.continue_btn.setEnabled(True)
        self.status_label.setText("Import complete!")


def create_import_export_tab(repo, message_box_class, qfiledialog_class):
    """
    Create the Import/Export tab widget.

    Args:
        repo: GearRepository instance
        message_box_class: QMessageBox class for dialogs
        qfiledialog_class: QFileDialog class for file dialogs

    Returns:
        QWidget: Configured import/export tab
    """
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
    export_btn.clicked.connect(
        lambda: export_all_data(repo, message_box_class, qfiledialog_class)
    )
    export_layout.addWidget(export_btn)

    export_group.setLayout(export_layout)
    layout.addWidget(export_group)

    import_group = QGroupBox("Import Data")
    import_layout = QVBoxLayout()

    preview_btn = QPushButton("Preview CSV (Dry Run)")
    preview_btn.clicked.connect(
        lambda: preview_csv_import(repo, message_box_class, qfiledialog_class)
    )
    import_layout.addWidget(preview_btn)

    import_btn = QPushButton("Import from CSV")
    import_btn.clicked.connect(
        lambda: import_csv_data(
            repo,
            message_box_class,
            qfiledialog_class,
            DuplicateResolutionDialog,
            ImportProgressDialog,
        )
    )
    import_layout.addWidget(import_btn)

    import_group.setLayout(import_layout)
    layout.addWidget(import_group)

    template_group = QGroupBox("Templates")
    template_layout = QVBoxLayout()

    full_template_btn = QPushButton("Generate Complete Template")
    full_template_btn.clicked.connect(
        lambda: generate_full_template(repo, message_box_class, qfiledialog_class)
    )
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
        lambda: generate_single_template(
            repo, message_box_class, qfiledialog_class, template_combo.currentText()
        )
    )
    single_template_layout.addWidget(single_template_btn)

    template_layout.addLayout(single_template_layout)

    template_group.setLayout(template_layout)
    layout.addWidget(template_group)

    results_group = QGroupBox("Import Results")
    results_group.setVisible(False)
    results_layout = QVBoxLayout()

    results_label = QLabel()
    results_label.setWordWrap(True)
    results_layout.addWidget(results_label)

    details_text = QTextEdit()
    details_text.setReadOnly(True)
    details_text.setMaximumHeight(200)
    results_layout.addWidget(details_text)

    results_group.setLayout(results_layout)
    layout.addWidget(results_group)

    layout.addStretch()
    widget.setLayout(layout)

    # Store widgets for updating
    widget.import_results_group = results_group
    widget.import_results_label = results_label
    widget.import_details_text = details_text

    return widget


def export_all_data(repo, message_box_class, qfiledialog_class):
    """Export all data to CSV file."""
    default_name = f"geartracker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    file_path, _ = qfiledialog_class.getSaveFileName(
        None,
        "Export All Data",
        str(Path.home() / "Documents" / default_name),
        "CSV Files (*.csv)",
    )

    if file_path:
        try:
            repo.export_complete_csv(Path(file_path))
            message_box_class.information(
                None, "Export Complete", f"Data exported to:\n{file_path}"
            )
        except Exception as e:
            message_box_class.critical(
                None, "Export Error", f"Failed to export:\n{str(e)}"
            )


def preview_csv_import(repo, message_box_class, qfiledialog_class):
    """Preview CSV import without applying changes."""
    file_path, _ = qfiledialog_class.getOpenFileName(
        None, "Select CSV File", str(Path.home() / "Documents"), "CSV Files (*.csv)"
    )

    if file_path:
        try:
            result = repo.preview_import(Path(file_path))
            _show_import_results(message_box_class, "Preview Results", result)
        except Exception as e:
            message_box_class.critical(
                None, "Preview Error", f"Failed to preview:\n{str(e)}"
            )


def import_csv_data(
    repo, message_box_class, qfiledialog_class, dialog_class, progress_dialog_class
):
    """Import CSV data into database."""
    file_path, _ = qfiledialog_class.getOpenFileName(
        None, "Select CSV File", str(Path.home() / "Documents"), "CSV Files (*.csv)"
    )

    if not file_path:
        return

    try:
        # First, preview to show what will be imported
        preview_result = repo.preview_import(Path(file_path))

        if preview_result.errors:
            message_box_class.warning(
                None,
                "Import Validation Failed",
                f"CSV has {len(preview_result.errors)} errors.\n\nImport may fail or have unexpected results.",
            )
            _show_import_results(message_box_class, "Preview Results", preview_result)
            return

        # Confirm with user
        msg = f"Import will process {preview_result.total_rows} rows.\n"
        msg += "\n\nContinue?"

        reply = message_box_class.question(
            None,
            "Confirm Import",
            msg,
            message_box_class.StandardButton.Yes | message_box_class.StandardButton.No,
        )

        if reply == message_box_class.StandardButton.No:
            return

        # Create progress dialog
        progress_dialog = progress_dialog_class(None, preview_result.total_rows)

        # Define progress callback
        def progress_callback(current, total, entity_type, message):
            progress_dialog.update_progress(current, f"Importing {entity_type}...")
            if message:
                progress_dialog.add_error(message)

        # Define duplicate handler
        def duplicate_handler(entity_type, existing, imported):
            dialog = dialog_class(None, entity_type, existing, imported)
            if dialog.exec() == dialog.DialogCode.Accepted:
                return dialog.get_action()
            else:
                return "cancel"

        # Actual import
        result = repo.import_complete_csv(
            Path(file_path),
            dry_run=False,
            duplicate_callback=duplicate_handler,
            progress_callback=progress_callback,
        )

        progress_dialog.finish()

        # Show results
        _show_import_results(message_box_class, "Import Results", result)

        # Note: UI refresh should be handled by caller
        return result

    except Exception as e:
        message_box_class.critical(None, "Import Error", f"Failed to import:\n{str(e)}")
        return None


def generate_full_template(repo, message_box_class, qfiledialog_class):
    """Generate complete CSV template."""
    default_name = f"geartracker_template_{datetime.now().strftime('%Y%m%d')}.csv"
    file_path, _ = qfiledialog_class.getSaveFileName(
        None,
        "Save Template",
        str(Path.home() / "Documents" / default_name),
        "CSV Files (*.csv)",
    )

    if file_path:
        try:
            repo.generate_csv_template(Path(file_path), entity_type=None)
            message_box_class.information(
                None, "Template Created", f"Template saved to:\n{file_path}"
            )
        except Exception as e:
            message_box_class.critical(
                None, "Template Error", f"Failed to generate template:\n{str(e)}"
            )


def generate_single_template(
    repo, message_box_class, qfiledialog_class, entity_type: str
):
    """Generate single-entity CSV template."""
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
        message_box_class.warning(
            None, "Template Error", f"Unknown entity type: {entity_type}"
        )
        return

    default_name = (
        f"geartracker_template_{csv_entity}_{datetime.now().strftime('%Y%m%d')}.csv"
    )
    file_path, _ = qfiledialog_class.getSaveFileName(
        None,
        "Save Template",
        str(Path.home() / "Documents" / default_name),
        "CSV Files (*.csv)",
    )

    if file_path:
        try:
            repo.generate_csv_template(Path(file_path), entity_type=csv_entity)
            message_box_class.information(
                None, "Template Created", f"Template saved to:\n{file_path}"
            )
        except Exception as e:
            message_box_class.critical(
                None, "Template Error", f"Failed to generate template:\n{str(e)}"
            )


def _show_import_results(message_box_class, title: str, result):
    """Show import results in a message box."""
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
    message_box_class.information(None, title, full_message)
