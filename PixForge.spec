# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for PixForge."""

import os
import glob
import site
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# Locate site-packages to safely collect pillow_heif C-extensions and bundled libheif DLLs
sp_dirs = site.getsitepackages()
site_packages = None
for p in sp_dirs:
    if "site-packages" in p:
        site_packages = p
        break
if site_packages is None:
    import pillow_heif
    site_packages = os.path.dirname(os.path.dirname(pillow_heif.__file__))

# Data files: application resources (icons, assets) and package data
datas = [
    ('app/resources/icons/*', 'app/resources/icons'),
]
datas += collect_data_files('pillow_heif')

# Binary dynamic libraries: explicitly gather libheif DLLs and _pillow_heif .pyd
binaries = []
binaries += collect_dynamic_libs('pillow_heif')

# Also grab any libheif DLLs directly located in site-packages
for dll in glob.glob(os.path.join(site_packages, "libheif*.dll")):
    binaries.append((dll, '.'))

for pyd in glob.glob(os.path.join(site_packages, "_pillow_heif*.pyd")):
    binaries.append((pyd, '.'))

# Hidden imports: ensure all pillow plugins and pillow_heif modules are packaged
hiddenimports = [
    'PIL',
    'PIL.Image',
    'PIL.JpegImagePlugin',
    'PIL.PngImagePlugin',
    'PIL.WebPImagePlugin',
    'PIL.BmpImagePlugin',
    'PIL.TiffImagePlugin',
    'PIL.GifImagePlugin',
    'pillow_heif',
    'pillow_heif.HeifImagePlugin',
    'pillow_heif.as_plugin',
    'pillow_heif.constants',
    'pillow_heif.options',
    'pillow_heif._lib_info',
    'pillow_heif._deffered_error',
    '_pillow_heif',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
]
hiddenimports += collect_submodules('pillow_heif')
hiddenimports += collect_submodules('app')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PixForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/resources/icons/PixForge.ico',
)
