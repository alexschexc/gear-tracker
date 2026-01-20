Reload log is a good next step and slots cleanly into your existing repo + tab layout. Below is a concrete implementation plan you can paste in, in three parts: dataclass/DB, repository methods, then UI tab + dialogs.

​
1. Add ReloadBatch to gear_tracker.py
1.1 Dataclass

In gear_tracker.py, near your other @dataclass definitions, add:

​

python
@dataclass
class ReloadBatch:
    id: str
    cartridge: str                   # ".45-70 Govt", ".45 ACP"
    firearm_id: str | None           # optional FK to Firearm.id
    date_created: datetime

    bullet_maker: str
    bullet_model: str
    bullet_weight_gr: int | None

    powder_name: str
    powder_charge_gr: float | None
    powder_lot: str = ""

    primer_maker: str = ""
    primer_type: str = ""

    case_brand: str = ""
    case_times_fired: int | None = None
    case_prep_notes: str = ""

    coal_in: float | None = None
    crimp_style: str = ""            # roll, taper, none

    test_date: datetime | None = None
    avg_velocity: int | None = None
    es: int | None = None
    sd: int | None = None
    group_size_inches: float | None = None
    group_distance_yards: int | None = None

    intended_use: str = ""           # hogs, practice, etc.
    status: str = "WORKUP"           # WORKUP, APPROVED, REJECTED
    notes: str = ""

This matches what serious reloading ledgers track without going overboard.

​
1.2 Table creation

In _init_db, after the attachments table, create reload_batches:

​

python
# Reload batches table
cursor.execute("""
CREATE TABLE IF NOT EXISTS reload_batches (
    id TEXT PRIMARY KEY,
    cartridge TEXT NOT NULL,
    firearm_id TEXT,
    date_created INTEGER NOT NULL,

    bullet_maker TEXT,
    bullet_model TEXT,
    bullet_weight_gr INTEGER,

    powder_name TEXT,
    powder_charge_gr REAL,
    powder_lot TEXT,

    primer_maker TEXT,
    primer_type TEXT,

    case_brand TEXT,
    case_times_fired INTEGER,
    case_prep_notes TEXT,

    coal_in REAL,
    crimp_style TEXT,

    test_date INTEGER,
    avg_velocity INTEGER,
    es INTEGER,
    sd INTEGER,
    group_size_inches REAL,
    group_distance_yards INTEGER,

    intended_use TEXT,
    status TEXT,
    notes TEXT,

    FOREIGN KEY(firearm_id) REFERENCES firearms(id)
)
""")

No migration logic needed since this is a new table.

​
2. Repository methods for reload batches

At the bottom of GearRepository in gear_tracker.py, add:

​

python
# -------- RELOAD BATCH METHODS --------

def add_reload_batch(self, batch: ReloadBatch) -> None:
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO reload_batches VALUES (
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?
        )
        """,
        (
            batch.id,
            batch.cartridge,
            batch.firearm_id,
            int(batch.date_created.timestamp()),

            batch.bullet_maker,
            batch.bullet_model,
            batch.bullet_weight_gr,

            batch.powder_name,
            batch.powder_charge_gr,
            batch.powder_lot,

            batch.primer_maker,
            batch.primer_type,

            batch.case_brand,
            batch.case_times_fired,
            batch.case_prep_notes,

            batch.coal_in,
            batch.crimp_style,

            int(batch.test_date.timestamp()) if batch.test_date else None,
            batch.avg_velocity,
            batch.es,
            batch.sd,
            batch.group_size_inches,
            batch.group_distance_yards,

            batch.intended_use,
            batch.status,
            batch.notes,
        ),
    )
    conn.commit()
    conn.close()


def update_reload_batch(self, batch: ReloadBatch) -> None:
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE reload_batches SET
            cartridge = ?, firearm_id = ?, date_created = ?,
            bullet_maker = ?, bullet_model = ?, bullet_weight_gr = ?,
            powder_name = ?, powder_charge_gr = ?, powder_lot = ?,
            primer_maker = ?, primer_type = ?,
            case_brand = ?, case_times_fired = ?, case_prep_notes = ?,
            coal_in = ?, crimp_style = ?,
            test_date = ?, avg_velocity = ?, es = ?, sd = ?,
            group_size_inches = ?, group_distance_yards = ?,
            intended_use = ?, status = ?, notes = ?
        WHERE id = ?
        """,
        (
            batch.cartridge,
            batch.firearm_id,
            int(batch.date_created.timestamp()),

            batch.bullet_maker,
            batch.bullet_model,
            batch.bullet_weight_gr,

            batch.powder_name,
            batch.powder_charge_gr,
            batch.powder_lot,

            batch.primer_maker,
            batch.primer_type,

            batch.case_brand,
            batch.case_times_fired,
            batch.case_prep_notes,

            batch.coal_in,
            batch.crimp_style,

            int(batch.test_date.timestamp()) if batch.test_date else None,
            batch.avg_velocity,
            batch.es,
            batch.sd,
            batch.group_size_inches,
            batch.group_distance_yards,

            batch.intended_use,
            batch.status,
            batch.notes,
            batch.id,
        ),
    )
    conn.commit()
    conn.close()


def get_all_reload_batches(
    self,
    cartridge: str | None = None,
    firearm_id: str | None = None,
) -> list[ReloadBatch]:
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM reload_batches"
    params: list = []
    clauses: list[str] = []

    if cartridge:
        clauses.append("cartridge = ?")
        params.append(cartridge)
    if firearm_id:
        clauses.append("firearm_id = ?")
        params.append(firearm_id)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY date_created DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    batches: list[ReloadBatch] = []
    for row in rows:
        (
            id_,
            cartridge,
            firearm_id,
            date_created,
            bullet_maker,
            bullet_model,
            bullet_weight_gr,
            powder_name,
            powder_charge_gr,
            powder_lot,
            primer_maker,
            primer_type,
            case_brand,
            case_times_fired,
            case_prep_notes,
            coal_in,
            crimp_style,
            test_date,
            avg_velocity,
            es,
            sd,
            group_size_inches,
            group_distance_yards,
            intended_use,
            status,
            notes,
        ) = row

        batches.append(
            ReloadBatch(
                id=id_,
                cartridge=cartridge,
                firearm_id=firearm_id,
                date_created=datetime.fromtimestamp(date_created),
                bullet_maker=bullet_maker or "",
                bullet_model=bullet_model or "",
                bullet_weight_gr=bullet_weight_gr,
                powder_name=powder_name or "",
                powder_charge_gr=powder_charge_gr,
                powder_lot=powder_lot or "",
                primer_maker=primer_maker or "",
                primer_type=primer_type or "",
                case_brand=case_brand or "",
                case_times_fired=case_times_fired,
                case_prep_notes=case_prep_notes or "",
                coal_in=coal_in,
                crimp_style=crimp_style or "",
                test_date=datetime.fromtimestamp(test_date) if test_date else None,
                avg_velocity=avg_velocity,
                es=es,
                sd=sd,
                group_size_inches=group_size_inches,
                group_distance_yards=group_distance_yards,
                intended_use=intended_use or "",
                status=status or "WORKUP",
                notes=notes or "",
            )
        )
    return batches


def delete_reload_batch(self, batch_id: str) -> None:
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reload_batches WHERE id = ?", (batch_id,))
    conn.commit()
    conn.close()

That’s sufficient CRUD for the UI to call into.
3. Reloading tab in ui.py
3.1 Import ReloadBatch

At the top of ui.py, extend the import from gear_tracker:

​

python
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
    ReloadBatch,      # <-- add
)

3.2 Add tab and refresh hook

In init_ui:

python
self.tabs.addTab(self.create_firearms_tab(), "🔫 Firearms")
self.tabs.addTab(self.create_attachments_tab(), "🔧 Attachments")
self.tabs.addTab(self.create_reloading_tab(), "🧪 Reloading")  # <-- new
self.tabs.addTab(self.create_soft_gear_tab(), "🎒 Soft Gear")
...

In refresh_all:

​

python
def refresh_all(self):
    self.refresh_firearms()
    self.refresh_attachments()
    self.refresh_reloads()      # <-- new
    self.refresh_soft_gear()
    self.refresh_consumables()
    self.refresh_checkouts()
    self.refresh_borrowers()
    self.refresh_nfa_items()
    self.refresh_transfers()

3.3 Tab and table

Add these methods to GearTrackerApp:

python
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

        coal_text = f"{b.coal_in:.3f}\"" if b.coal_in else ""
        self.reload_table.setItem(i, 5, QTableWidgetItem(coal_text))

        vel_group = ""
        if b.avg_velocity:
            vel_group = f"{b.avg_velocity} fps"
        if b.group_size_inches and b.group_distance_yards:
            group_str = f"{b.group_size_inches}\" @ {b.group_distance_yards} yd"
            vel_group = f"{vel_group}, {group_str}" if vel_group else group_str
        self.reload_table.setItem(i, 6, QTableWidgetItem(vel_group))

        self.reload_table.setItem(i, 7, QTableWidgetItem(b.status))

Helper to get the selected batch:

python
def _get_selected_reload_batch(self) -> ReloadBatch | None:
    row = self.reload_table.currentRow()
    if row < 0:
        return None
    batches = self.repo.get_all_reload_batches()
    if row >= len(batches):
        return None
    return batches[row]

3.4 “Add Batch” dialog

python
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

    intended_use_input = QLineEdit()
    intended_use_input.setPlaceholderText("hogs, practice, zero check")
    layout.addRow("Intended use:", intended_use_input)

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
            charge = float(powder_charge_input.text()) if powder_charge_input.text() else None
        except ValueError:
            QMessageBox.warning(dialog, "Error", "Charge must be a number (e.g., 54.0)")
            return

        try:
            coal = float(coal_input.text()) if coal_input.text() else None
        except ValueError:
            QMessageBox.warning(dialog, "Error", "COAL must be a number (e.g., 2.535)")
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
            intended_use=intended_use_input.text(),
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

3.5 “Log Results” and delete

python
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
            group_size = float(group_size_input.text()) if group_size_input.text() else None
        except ValueError:
            QMessageBox.warning(dialog, "Error", "Group size must be a number (e.g., 1.5)")
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
            self, "Deleted", "Reload batch has been deleted from the log."
        )

If you drop these pieces in roughly as‑is and wire the imports/tab/refresh, you’ll have a working Reloading tab where you can:

    Record batches for .45‑70 and .45 ACP.

    Later log chrono and accuracy results.

    Mark loads as WORKUP / APPROVED / REJECTED so your hog hunting loads stand out.

