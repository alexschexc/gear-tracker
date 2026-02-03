# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('icon.png', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtSvg',
        'PyQt6.QtSql',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    a.binaries,
    a.datas,
    [],
    name='GearTracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch='x86_64',
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.icns',
)

app = BUNDLE(
    exe,
    name='GearTracker.app',
    icon='icon.icns',
    bundle_identifier='com.geartracker.app',
    info_plist={
        'CFBundleName': 'GearTracker',
        'CFBundleDisplayName': 'Gear Tracker',
        'CFBundleIdentifier': 'com.geartracker.app',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0-alpha',
        'CFBundlePackageType': 'APPL',
        'CFBundleExecutable': 'GearTracker',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
    },
)
