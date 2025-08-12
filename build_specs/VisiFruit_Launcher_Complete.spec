# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\\visifruit_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('start_sistema_completo.bat', '.'), ('start_sistema_completo.ps1', '.'), ('start_backend.bat', '.'), ('start_frontend.bat', '.')],
    hiddenimports=['tkinter', 'customtkinter', 'requests'],
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
    a.binaries,
    a.datas,
    [],
    name='VisiFruit_Launcher_Complete',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
