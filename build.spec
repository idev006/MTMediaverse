# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MediaVerse
Run: pyinstaller build.spec
"""

import os
import sys

block_cipher = None

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(SPEC))
APP_DIR = os.path.join(BASE_DIR, 'app')

# Collect all app modules
app_datas = [
    # Config files (external)
    (os.path.join(BASE_DIR, 'config'), 'config'),
]

# Hidden imports for dynamic loading
hidden_imports = [
    'app.core',
    'app.core.database',
    'app.core.event_bus',
    'app.core.message_envelope',
    'app.core.message_orchestrator',
    'app.core.log_orchestrator',
    'app.core.error_orchestrator',
    'app.core.config',
    'app.core.platform_managers',
    'app.core.platform_managers.base',
    'app.core.platform_managers.youtube',
    'app.core.platform_managers.tiktok',
    'app.core.platform_managers.facebook',
    'app.core.platform_managers.shopee',
    'app.viewmodels',
    'app.viewmodels.media_vm',
    'app.viewmodels.order_vm',
    'app.viewmodels.product_vm',
    'app.viewmodels.order_builder',
    'app.api',
    'app.api.main',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'starlette',
    'pydantic',
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
]

a = Analysis(
    ['main.py'],
    pathex=[BASE_DIR],
    binaries=[],
    datas=app_datas,
    hiddenimports=hidden_imports,
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
    name='MediaVerse',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to False for GUI-only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MediaVerse',
)
