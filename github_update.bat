@echo off
echo ================================
echo    GitHub Guncelleme Scripti
echo ================================
echo.

cd /d "C:\Users\ASUS\Desktop\Python with AI\timer"

echo Durum kontrol ediliyor...
git status
echo.

echo Tum degisiklikler ekleniyor...
git add .
echo.

set /p message="Commit mesaji girin (Enter'a basarak 'Update' kullanabilirsiniz): "
if "%message%"=="" set message=Update

echo Commit yapiliyor: %message%
git commit -m "%message%"
echo.

echo GitHub'a gonderiliyor...
git push origin main
echo.

echo ================================
echo    Guncelleme tamamlandi!
echo ================================
pause
