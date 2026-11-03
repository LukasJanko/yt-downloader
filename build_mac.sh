#!/usr/bin/env bash
# Builds "YouTube to MP4.app" and a .dmg installer. Run on macOS.
set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-.venv/bin/python}
"$PY" -m pip install -r requirements.txt -r requirements-build.txt

rm -rf build dist
"$PY" -m PyInstaller --noconfirm --windowed --name "YouTube to MP4" \
  --osx-bundle-identifier com.local.ytmp4 \
  --add-data "templates:templates" \
  --collect-all yt_dlp --collect-all imageio_ffmpeg --collect-all certifi \
  launcher.py

# Drag-to-Applications disk image
rm -rf dist/dmg && mkdir dist/dmg
cp -R "dist/YouTube to MP4.app" dist/dmg/
ln -s /Applications dist/dmg/Applications
hdiutil create -volname "YouTube to MP4" -srcfolder dist/dmg -ov -format UDZO "dist/YouTube-to-MP4-mac.dmg"
rm -rf dist/dmg
echo "Done: dist/YouTube-to-MP4-mac.dmg"
