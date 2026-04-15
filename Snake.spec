# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['Snake.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('v1_1/audio/assets/sounds', 'audio/assets/sounds'),
        ('snake.ico', '.'),
    ],
    hiddenimports=['pygame'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pex = PYZ(a.pure)

exe = EXE(
    pex,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Snake',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='snake.ico',
)
