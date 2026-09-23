# -*- mode: python ; coding: utf-8 -*-
"""
Configuration PyInstaller pour B-NDEKE Comptability One
Avec DLLs explicites pour Miniconda
"""
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# ============================================================
# DLLs MINICONDA A INCLURE EXPLICITEMENT
# ============================================================
MINICONDA_LIB = r"C:\ProgramData\miniconda3\Library\bin"

binaries = []

dlls_a_inclure = [
    # === Base de donnees ===
    "sqlite3.dll",
    # === Interface graphique (CustomTkinter / Tk) ===
    "tcl86t.dll",
    "tk86t.dll",
    # === Compression ===
    "zlib1.dll",
    "liblzma.dll",
    "libbz2.dll",
    # === Cryptographie (SSL/HTTPS pour email) ===
    "libcrypto-3-x64.dll",
    "libssl-3-x64.dll",
    # === _ctypes (ESSENTIEL pour CustomTkinter) ===
    "ffi-8.dll",
    "ffi-7.dll",
    "ffi.dll",
    # === Autres ===
    "libexpat.dll",
]

for dll in dlls_a_inclure:
    chemin_dll = os.path.join(MINICONDA_LIB, dll)
    if os.path.exists(chemin_dll):
        binaries.append((chemin_dll, "."))
        print(f"[OK] DLL incluse : {dll}")
    else:
        print(f"[SKIP] DLL introuvable : {dll}")

# ============================================================
# FICHIERS DE DONNEES
# ============================================================
datas = [
    ('data', 'data'),
]
datas += collect_data_files('customtkinter')

hiddenimports = [
    'customtkinter',
    'PIL',
    'PIL._tkinter_finder',
    'reportlab',
    'reportlab.platypus',
    'reportlab.pdfbase',
    'reportlab.pdfbase._fontdata',
    'bcrypt',
    'openpyxl',
    'fitz',
    'pymupdf',
    'win32print',
    'win32ui',
    'smtplib',
    'sqlite3',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.base',
    'ctypes',
    'ctypes.wintypes',
]

icon_path = 'data/bndeke.ico' if os.path.exists('data/bndeke.ico') else None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='B-NDEKE Comptability One',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # <-- CHANGE : plus de console noire
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='B-NDEKE Comptability One',
)