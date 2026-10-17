# -*- mode: python ; coding: utf-8 -*-
import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules

spec_root = os.path.dirname(os.path.abspath(SPEC))
sys.path.insert(0, spec_root)

datas = []
binaries = []
hiddenimports = []

for package in ('django', 'django_quill', 'mailer', 'messenger', 'config', 'utils'):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

hiddenimports += collect_submodules('django.core.management.commands')

excludes = [
    'pytest',
    'pytest_django',
    'pytest_cov',
    'coverage',
    'mailer.tests',
    'messenger.tests',
    'utils.tests',
    'conftest',
]

a = Analysis(
    ['run.py'],
    pathex=[spec_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='bulk_emailer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
