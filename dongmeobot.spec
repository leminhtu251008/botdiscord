# dongmeobot.spec
import sys
from PyInstaller.utils.hooks import collect_submodules

hidden_imports = collect_submodules('yt_dlp') + collect_submodules('pynacl')

a = Analysis(
    ['dongmeobot.py'],
    pathex=['.'],
    binaries=[
        ('D:\\bot_discord\\ffmpeg.exe', '.'),  # Include FFmpeg
        ('D:\\bot_discord\\libopus.dll', '.')  # Include libopus.dll
    ],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='dongmeobot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True
)
