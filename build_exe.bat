@echo off
REM Build GeMoney.exe portable (single file) ke folder GeMoney_Portable.
REM Butuh: pip install pyinstaller

setlocal
cd /d "%~dp0"

python -m PyInstaller --noconfirm --onefile --windowed ^
  --name GeMoney ^
  --distpath "%~dp0GeMoney_Portable" ^
  --workpath "%~dp0build_pyinstaller" ^
  --specpath "%~dp0build_pyinstaller" ^
  main.py

echo.
echo Selesai. File ada di: %~dp0GeMoney_Portable\GeMoney.exe
endlocal
