# GearTracker v0.1.0-alpha.2 - Pre-Alpha Release Notes

**Release Date:** January 20, 2026
**Version Tag:** v0.1.0-alpha.2

---

## ⚠️ Important Notices

- **This is a pre-alpha release** - expect bugs and potential crashes
- May experience **critical core dumps** in edge cases
- Data is stored locally in SQLite database - keep regular backups!
- **No data is ever sent to any remote server**
- Report issues with steps to reproduce when possible

---

## 🚀 What's New

### Loadouts System (Phase 3)

**Create & Manage Loadouts:**
- Build custom loadouts with firearms, soft gear, NFA items, and consumables
- Tabbed builder interface (Firearms, Soft Gear, NFA Items, Consumables)
- Visual display of mounted attachments on firearms
- Quantity selection for consumables
- Duplicate loadouts for quick variations

**Checkout Loadouts:**
- One-click checkout of entire loadout to borrower
- Automatic status validation:
  - Blocks checkout if items are unavailable
  - Blocks checkout if firearms need maintenance
  - Warns if consumable stock will go negative or below minimum
- Automatic consumable deduction from inventory

**Return Loadouts:**
- Return entire loadout as a single unit (no partial returns)
- **Per-firearm round count input** for each firearm in loadout
- Rain exposure checkbox
- Ammo type selection:
  - Normal
  - Corrosive (triggers CORROSIVE_AMMO maintenance log)
  - Lead (triggers LEAD_AMMO maintenance log)
  - Custom
- Option to restock unused consumables
- **Automatic maintenance logging:**
  - FIRED_ROUNDS for each firearm with round count > 0
  - RAIN_EXPOSURE if rain exposure checked
  - CORROSIVE_AMMO if corrosive ammo selected
  - LEAD_AMMO if lead ammo selected

---

## 🔧 Existing Features

### Inventory Management (Phase 1)

**Firearms:**
- Name, caliber, serial number, purchase date
- Notes and status tracking
- Attachment mounting
- Round count tracking
- Maintenance intervals (round-based & time-based)

**NFA Items (Suppressors, SBRs, etc.):**
- Full NFA compliance tracking
- Tax stamp ID tracking
- Form types (Form 1, Form 4)
- Trust association
- Transfer status tracking (OWNED/TRANSFERRED)
- Barrel length
- Purchase date and notes

**Soft Gear:**
- Clothing, optics, accessories
- Categories and descriptions
- Status tracking

**Consumables:**
- Name, category, unit of measure
- Current quantity tracking
- Minimum quantity alerts
- Transaction history (add/use transactions)

**Attachments:**
- Scopes, lights, suppressors, optics
- Mount to firearms
- Displayed in loadout builder (read-only)

**Reload/Handload Log:**
- Track reload batches
- Caliber, powder, primer, bullet info
- Quantity tracking
- Notes

### Maintenance System (Phase 2)

**Round Count Tracking:**
- Track rounds fired per firearm
- Configurable clean interval (default 500 rounds)
- Configurable oil interval (default 90 days)
- Auto-flag maintenance when thresholds exceeded

**Maintenance Status:**
- Visual indicators in firearms table:
  - **Red background:** Firearm needs maintenance
  - **Yellow background:** Approaching threshold (80%+)
- Tooltips showing detailed reasons for maintenance

**Maintenance Types:**
- CLEANING - Resets round counter, clears maintenance flag
- LUBRICATION - Time-based oiling
- REPAIR - General repairs
- ZEROING - Scope/sight zeroing
- HUNTING - Hunting trips
- INSPECTION - Periodic inspections
- FIRED_ROUNDS - Auto-logged on loadout return
- OILING - For loadout integration
- RAIN_EXPOSURE - Auto-logged if rain exposure checked
- CORROSIVE_AMMO - Auto-logged if corrosive ammo selected
- LEAD_AMMO - Auto-logged if lead ammo selected

### Checkout System

**Borrower Management:**
- Add borrowers with name, phone, email, notes
- Track checkouts per borrower

**Checkouts:**
- Checkout items to borrowers
- Set expected return dates
- Overdue detection (red highlighting in table)
- Return individual items
- Return entire loadouts with usage data

---

## 📊 Feature Status

| Feature | Status |
|----------|--------|
| Firearms Management | ✅ Complete |
| Soft Gear Management | ✅ Complete |
| NFA Items & Compliance | ✅ Complete |
| Consumables Tracking | ✅ Complete |
| Attachments System | ✅ Complete |
| Reload/Handload Log | ✅ Complete |
| Borrower Management | ✅ Complete |
| Checkout/Return System | ✅ Complete |
| Loadouts System | ✅ Complete |
| Round Count Tracking | ✅ Complete |
| Maintenance Thresholds | ✅ Complete |
| Maintenance Logging | ✅ Complete |
| Automatic Maintenance Logging | ✅ Complete |
| CSV Export | 🚧 Next Release |
| CSV Import | 🚧 Next Release |

---

## 🐛 Known Issues

- Loadout checkout validation may not catch all edge cases
- NFA item display in certain dialogs may have minor formatting issues
- Performance may degrade with very large inventories (>1000 items)
- Database migrations should be tested before upgrading from previous versions
- **Core dumps may occur with certain operations** - please report if you experience crashes
- Some UI transitions may have minor visual glitches

---

## 🔜 Coming in v0.1.0-beta.1 (MVP Release)

### CSV Import/Export System (Phase 4)

**CSV Export:**
- Export all inventory data to CSV files
- Per-entity export (firearms, soft gear, NFA items, consumables, loadouts)
- Generate CSV templates for easy data entry
- One-click "Export All" to backup directory

**CSV Import:**
- Bulk import from CSV files
- Validation and error reporting with row-level details
- Duplicate detection options (skip/overwrite/merge)
- Dry-run mode to preview changes before committing
- Progress dialogs for large imports

**Milestone:**
- **v0.1.0-beta.1 will constitute Minimum Viable Product (MVP)**
- After MVP: Slow down for polishing before Beta

---

## 💾 Backup Instructions

**CRITICAL: Always backup before upgrading:**

```bash
# Close GearTracker, then:
cp ~/.gear_tracker/tracker.db ~/.gear_tracker/tracker.db.backup
```

Or copy `tracker.db` to your preferred backup location.

---

## 📝 Installation

**Requirements:**
- Python 3.14+
- PyQt6

```bash
pip install PyQt6
python ui.py
```

**Platform Support:**
- Linux: ✅ Currently Supported
- Windows: 🚧 Coming Soon
- macOS: 🚧 Coming Soon

---

## 📄 Changelog

### v0.1.0-alpha.2 (Current)
- ✅ Loadout builder with multi-category item selection
- ✅ One-click checkout with comprehensive validation
- ✅ Loadout return with per-firearm round counts
- ✅ Automatic maintenance logging on return
- ✅ Full NFA item support in loadouts
- 🐛 Fixed: Maintenance flag not clearing after CLEANING
- 🐛 Fixed: Loadout checkouts not appearing in checkouts tab
- 🐛 Fixed: NFA item checkout crash (36 bindings error)
- 🐛 Fixed: Loadout return only returning first item
- 🐛 Fixed: App crash on startup (last_clean_date type error)
- 🐛 Fixed: Firearms showing wrong maintenance status and round counts

### v0.1.0-alpha.1
- ✅ Round counting per firearm
- ✅ Configurable maintenance thresholds
- ✅ Visual maintenance alerts (red/yellow backgrounds)
- ✅ Maintenance history logging
- 🐛 Fixed: Various UI issues with loadout dialogs

### v0.1.0-alpha.0
- ✅ Initial inventory management
- ✅ Firearms, soft gear, NFA items, consumables
- ✅ Attachments system
- ✅ Reload/Handload log
- ✅ Borrower management
- ✅ Checkout/return system

---

## 🤝 Support

- **Report bugs:** Please include steps to reproduce and error messages if possible
- **Feature requests:** Feedback welcome on what would make this more useful
- **Donations:** If you're benefiting from this software: https://paypal.me/ASchexnayder296

---

**Thank you for testing GearTracker!** 🦌
