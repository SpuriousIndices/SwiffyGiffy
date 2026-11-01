# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all
import imageio_ffmpeg

# Resolve relative to repo root dynamically on whichever machine runs the build
SPECPATH_DIR = Path(SPECPATH).resolve()

datas = [
    (str(SPECPATH_DIR / 'templates'), 'templates'),
    (str(SPECPATH_DIR / 'static'), 'static'),
]

# Discover ffmpeg binary dynamically from the installed imageio_ffmpeg package
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
binaries = [
    (ffmpeg_exe, 'imageio_ffmpeg/binaries'),
]

hiddenimports = ['yt_dlp']

# Collect imageio_ffmpeg metadata and assets
tmp_ret = collect_all('imageio_ffmpeg')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    [str(SPECPATH_DIR / 'app.py')],
    pathex=[str(SPECPATH_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='SwiffyGiffy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
