@echo off
echo ========================================
echo Budowanie aplikacji do pliku .exe
echo ========================================
echo.

python -m PyInstaller --name="AplikacjaPrzetwarzaniaObrazow" ^
    --onefile ^
    --windowed ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=PIL ^
    --hidden-import=PIL.Image ^
    --hidden-import=ppm_loader ^
    --hidden-import=image_filters ^
    main.py

echo.
echo ========================================
if exist "dist\AplikacjaPrzetwarzaniaObrazow.exe" (
    echo SUKCES! Plik .exe utworzony w katalogu dist\
    echo Plik: dist\AplikacjaPrzetwarzaniaObrazow.exe
) else (
    echo Blad! Plik .exe nie zostal utworzony.
)
echo ========================================
pause

