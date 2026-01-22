# README.md

## Project Status: MVP Complete ✅

**Version:** v0.1.0-alpha (Minimum Viable Product)

GearTracker has reached MVP status with all planned core features complete. The software runs completely offline with local SQLite storage, ensuring privacy and data ownership.

**Platform Support:**

- ✅ Linux (Currently Supported)
- 🚧 Windows (Coming Soon)
- 🚧 macOS (Coming Soon)

## Features

### Core Inventory Management

**Firearms & Gear Tracking:**

- Complete firearm inventory with maintenance tracking
- NFA item management (suppressors, SBRs, SBSs, etc.)
- Soft gear tracking (armor, vests, backpacks, boots)
- Attachments management with firearm mounting
- Automatic maintenance reminders based on:
  - Rounds fired
  - Time since last cleaning
  - Time since last oiling
  - Custom maintenance conditions (e.g., rain exposure, corrosive ammo use)
- Maintenance logging with multiple event types

**Loadout System:**

- Pre-configured gear sets for specific activities (hunting, range days, competitions)
- Loadout checkout with validation:
  - Validates all items are available
  - Checks maintenance status before allowing checkout
  - Validates consumable stock levels
  - Prevents checkout if critical issues found
- One-click loadout return with automatic round count logging per firearm
- Rain exposure tracking per firearm
- Ammo type recording for maintenance needs
- Automatic consumable deduction and restocking
- Duplicate loadouts for quick setup

**Checkout Management:**

- Item-level checkout for firearms, soft gear, and NFA items
- Borrower management with contact info
- Add/delete borrowers with validation (prevents deletion if active checkouts exist)
- Automatic status updates when items are checked out/returned
- Checkout history with return dates

**Reloader's Log Book:**

- Complete reload batch tracking
- Component-level data (bullet, powder, primer, case, etc.)
- Test results logging (velocity, ES, SD, group size)
- Case prep tracking (times fired, tumbling, etc.)
- Multiple batches per cartridge with different firearm assignments

**Consumables Management:**

- Inventory tracking (ammo, medical supplies, etc.)
- Low stock alerts when quantity drops below threshold
- Transaction history (add, use, adjust operations)
- Units of measure support (rounds, count, ounces, etc.)

**Maintenance Logging:**

- Comprehensive maintenance event tracking
- Event types: Cleaning, Lubrication, Repair, Zeroing, Hunting, Inspection
- Special event tracking:
  - Rounds fired
  - Rain exposure
  - Corrosive ammo use
  - Lead ammo use
  - Oil application
- Photo attachment support for maintenance events
- Maintenance history per item with last cleaned date tracking

**Attachments System:**

- Optics, lights, stocks, rails, triggers, etc.
- Track which firearm each attachment is mounted on
- Zero data tracking (distance, notes)
- Mount position tracking (top rail, scout mount, etc.)

### Private Sales Records

**Firearm Transfer Tracking:**

- Complete sale documentation
- Buyer information (name, address, DL#, LTC#)
- FFL dealer records (if used)
- Sale price tracking
- CSV export for transfer records
- Automatic firearm status updates (sets to TRANSFERRED)

**NFA Registry Integration:**

- Track all NFA items in one place
- Tax stamp ID tracking
- Form type recording (Form 1, Form 4, etc.)
- Trust name association
- Manufacturer and serial number tracking
- Integration with maintenance and checkout systems

### Data Import/Export (NEW in Phase 4)

**CSV Export:**

- Full database backup to CSV format
- Exports all 14 entity types in single file
- Preserves all relationships and IDs
- Sectioned format with `=== SECTION ===` headers
- ISO 8601 date format (YYYY-MM-DD)
- Automatic backup before import
- Export metadata with version info

**CSV Import:**

- Import from complete backup or single-entity templates
- Validate data before importing (dry-run mode)
- Duplicate detection with user choice:
  - Skip existing item
  - Overwrite existing item
  - Import as new (rename)
  - Cancel import
- Progress tracking with real-time updates
- Import in dependency order to maintain relationships
- Skip rows with errors, continue with valid data
- Template generation for manual data entry

**Templates:**

- Complete template with all 14 entity types
- Single-entity templates (firearms, consumables, etc.)
- Example data rows for reference
- Validation comments with field requirements
- Enum value documentation

## Data Storage & Privacy

GearTracker stores all data in a single local SQLite database file.
By default, the database is created at:

- Linux/macOS: `~/.gear_tracker/tracker.db`
- Windows: `C:\Users\<username>\.gear_tracker\tracker.db`

No data is ever sent to any remote server. The developer does not operate any backend service and never has access to your inventory, NFA records, or logs.

If you want additional protection, you can move the `.gear_tracker` folder onto an encrypted volume (e.g., LUKS, VeraCrypt, BitLocker, FileVault) and then symlink it back into your home directory.
(this has not been tested by the developer yet. This should work in theory, I will leave an update note confirming if this is the case)

**Backups:** To back up your data, close GearTracker and copy `tracker.db` to a safe location, for example:

```bash
cp ~/.gear_tracker/tracker.db ~/.gear_tracker/tracker.db.backup
```

## Installation & Running

**Requirements:**

- Python 3.14+
- PyQt6

Install dependencies and run:

```bash
pip install PyQt6
python ui.py
```

**Single-File Binary:**
Coming soon - PyInstaller spec file included for building standalone executables. Currently only tested on Linux; Windows and macOS support planned for beta releases.

## If you're enjoying or benefitting from this software leave me a tip

<https://paypal.me/ASchexnayder296>

---

## Version History

### v0.1.0-alpha (MVP) - Current Release ✅

**Completed Features:**

- ✅ Full inventory management (firearms, soft gear, NFA items, attachments, consumables)
- ✅ Reload/handload tracking with batch management
- ✅ Round count tracking per firearm with maintenance thresholds
- ✅ Visual maintenance alerts (red/yellow status indicators)
- ✅ Comprehensive maintenance logging (10 event types)
- ✅ Borrower management with add/delete functionality
- ✅ Item-level checkout and return system
- ✅ Loadout system (build, checkout, return with automatic maintenance logging)
- ✅ Private sales/transfer tracking with CSV export
- ✅ CSV import/export with validation, duplicate handling, and templates
- ✅ Complete offline data storage (local SQLite)

**Bug Fixes:**

- Maintenance flag not clearing after CLEANING
- Loadout checkouts not appearing in checkouts tab
- NFA item checkout crash
- Loadout return only returning first item
- App crash on startup (timestamp type errors)
- Firearms showing incorrect maintenance status

---

### Development Phases Completed

**Phase 1:** Reload/Handload Log
**Phase 2:** Round Count & Maintenance Thresholds
**Phase 3:** Loadouts System
**Phase 4:** CSV Import/Export System
**Phase 5:** Borrower Management Enhancements (Delete functionality)

---

## Upcoming Features (Post-MVP)

### ALPHA (we are here)

- **Polish:** UI refinements, performance optimizations, error handling improvements
- Codebase Refactor: need to do this now before the codebase gets too big otherwise future maintenance and expansion will become _impossible_
- **Windows Support:** Testing and packaging for Windows
- **macOS Support:** Testing and packaging for macOS

### BETA (all versions will be marked 0.x.y where x > 1)

The Beta phase focuses on **additional offline‑only features** that respect user privacy and do not require any hosted infrastructure.

| Feature | Goal | Notes (Offline‑First Design) | Target Beta Window |
| --- | --- | --- | --- |
| **Multi‑profile “vault” system** | Cleanly separate personal, parish, and test data into independent profiles, similar in feel to Obsidian’s vault picker but for GearTracker databases. | Each profile is just a different `.db` file (e.g., `personal.db`, `parish.db`), selected from a startup screen. No cross‑profile querying; switching profiles simply opens a different local database. | Beta 1 |
| **QR / barcode labels & scanning** | Speed up opening items and logging maintenance/checkouts, especially for larger inventories, inspired by QR‑centric workflows in other gear apps.[web:40][web:37] | GearTracker generates printable QR codes that encode local item IDs. A webcam or USB scanner decodes the code and focuses the corresponding record—no online lookup, no cloud registry. | Beta 1 |
| **Trip / expedition manifests (extended loadouts)** | Turn existing loadouts into “trip manifests” for hunts and range days so you can see exactly what left the house, what came back, and how it was used.[attached_file:2][web:148] | New Trip/Manifest entity built on top of current loadouts: per‑trip gear list, consumable quantities, and simple status (Planned / In Progress / Complete). Manifests are saved locally and exportable to Markdown/CSV for printing and archiving. | Beta 1 |
| **Richer maintenance photos & galleries** | Make it easy to visually track wear, damage, and targets over time without storing any images off‑device.[attached_file:2] | Store only file paths to photos; add gallery views per item and per maintenance event, plus quick open‑in‑viewer. No upload, no embedded cloud library. | Beta 1–2 |
| **Chronograph & target helper** | Provide basic ES/SD calculations and target tracking comparable to popular shooting/reloading apps, but entirely offline.[web:149][web:151] | Add “Range Session” records that store shot strings, computed stats, conditions, and links to target photos. Sessions tie to firearms and reload batches already in the database.[attached_file:2] | Beta 2 |
| **Summary report exports** | Generate human‑readable summaries like “current inventory,” “maintenance due,” or “season usage recap” for printing, sharing, or personal records.[attached_file:2][web:151] | Reports are generated from local data and exported as Markdown, HTML, or CSV into a user‑chosen folder; users can then print or convert to PDF using their own tools. Nothing is sent to any remote service. | Beta 2 |
| **Local data visualization** | Offer simple charts for round counts, maintenance load over time, and range‑session volume to help users understand how their gear is used.[web:149] | Charts are rendered inside GearTracker from the local SQLite database only. No external analytics libraries that phone home, and no online dashboards. | Beta 2–3 |
| **Advanced search & filtering** | Let users quickly answer questions like “.45‑70 reloads used last season on this rifle where rain exposure was logged” using a unified search interface.[attached_file:2] | Implement a local query builder across firearms, NFA items, soft gear, reload batches, maintenance logs, checkouts, and trips. Results can be exported as CSV/Markdown but never leave the machine by default. | Beta 3 |
| **Manual location tagging for hunts & range sessions** | Capture meaningful location context without continuous GPS tracking or map‑based telemetry, avoiding the privacy concerns common in cloud hunting apps.[web:73][web:138][web:79] | Optional, text‑only fields (e.g., “Sam Houston NF – Unit 3”) or manually entered UTM/lat‑long on trips and range sessions. No live GPS requirement, no online map tiles, and no location sharing. | Beta 3 |
| **User settings & preferences** | Centralize configuration without accounts: paths, defaults, and behavior tuning that stays on the user’s machine.[attached_file:2] | Store a small config file alongside the database with UI theme, default export directories, maintenance threshold defaults, and profile metadata. No remote sync, telemetry, or feature flags. | Beta 3 |

All Beta work continues the core guarantees of the MVP release: **no accounts, no ads, no tracking, and no cloud‑hosted infrastructure—just local data the user controls and can back up or export as they see fit.**[attached_file:2][web:79]
