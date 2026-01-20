# README.md

## Project Status: Pre-Alpha

This project is currently in a Pre-Alpha state. It is quickly moving towards a Minimal Viable Product. The intent is for this software to run offline forever. This is partly because I don't want to be responsible for people's data, partly to respect your privacy as an end user, and partly because that's not what I'm experimenting with in this project.

## Data storage & privacy

GearTracker stores all data in a single local SQLite database file.
By default, the database is created at:

- Linux/macOS: `~/.gear_tracker/tracker.db`
- Windows: `C:\Users\<username>\.gear_tracker\tracker.db`

No data is ever sent to any remote server. The developer does not operate any backend service and never has access to your inventory, NFA records, or logs.

If you want additional protection, you can move the `.gear_tracker` folder onto an encrypted volume (e.g., LUKS, VeraCrypt, BitLocker, FileVault) and then symlink it back into your home directory.

**Backups:** To back up your data, close GearTracker and copy `tracker.db` to a safe location, for example:

```bash
cp ~/.gear_tracker/tracker.db ~/.gear_tracker/tracker.db.backup
```

## Run time instructions for testing the current source code

to run these files as they sit you first need to install the PyQt6 library to your environment:

```bash
pip install PyQt6
```

then run it like this:

```bash
python ui.py
```

Once MVP is achieved we'll have a published single file Binary. Currently I am only supporting Linux. Windows and MacOS support are coming in the immediate future.

## If you're enjoying or benefitting from this software leave me a tip

<https://paypal.me/ASchexnayder296>
