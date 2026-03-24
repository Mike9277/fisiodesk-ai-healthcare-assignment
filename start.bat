@echo off
chcp 65001 >nul
echo.
echo ================================================
echo   FisioDesk AI Query System - Launch
echo ================================================
echo.

:: Verifica che Docker sia in esecuzione
echo [*] Verifica Docker in corso...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRORE] Docker non e' in esecuzione.
    echo Avvia Docker Desktop e riprova.
    pause
    exit /b 1
)
echo [OK] Docker e' in esecuzione

:: Verifica che le porte non siano occupate
echo.
echo [*] Verifica porte di sistema...
netstat -ano | findstr ":5000" >nul
if %errorlevel% equ 0 (
    echo [ATTENZIONE] La porta 5000 e' gia' in uso. L'API potrebbe non avviarsi.
)
netstat -ano | findstr ":27017" >nul
if %errorlevel% equ 0 (
    echo [ATTENZIONE] La porta 27017 e' gia' in uso. MongoDB potrebbe non avviarsi.
)
netstat -ano | findstr ":8081" >nul
if %errorlevel% equ 0 (
    echo [ATTENZIONE] La porta 8081 e' gia' in uso. MongoDB Express potrebbe non avviarsi.
)

:: Chiedi azione
echo.
echo ================================================
echo   Seleziona azione:
echo   [1] Avvia tutto (docker-compose up)
echo   [2] Riavvia tutto da zero (docker-compose down + up)
echo   [3] Ferma tutto (docker-compose down)
echo   [4] Verifica status servizi
echo   [5] Apri interfacce web
echo   [0] Esci
echo ================================================
echo.

set /p choice="Scelta: "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto rebuild
if "%choice%"=="3" goto stop
if "%choice%"=="4" goto status
if "%choice%"=="5" goto open
if "%choice%"=="0" goto end

echo Scelta non valida!
goto end

:start
echo.
echo [*] Avvio servizi in background...
docker-compose up -d
echo.
echo [*] Attesa avvio servizi (20 secondi)...
timeout /t 20 /nobreak >nul
echo.
echo [*] Import dati in MongoDB...
docker run --rm --network fisiodesk-ai-healthcare-assignment_fisiodesk-network -v "%%cd%%/data:/data" mongo:7.0 mongoimport --uri=mongodb://fisiodesk-mongodb:27017/fisiodesk --collection=pazienti --file=/data/pazienti.json --jsonArray --drop 2>nul
docker run --rm --network fisiodesk-ai-healthcare-assignment_fisiodesk-network -v "%%cd%%/data:/data" mongo:7.0 mongoimport --uri=mongodb://fisiodesk-mongodb:27017/fisiodesk --collection=schede_valutazione --file=/data/schede_valutazione.json --jsonArray --drop 2>nul
docker run --rm --network fisiodesk-ai-healthcare-assignment_fisiodesk-network -v "%%cd%%/data:/data" mongo:7.0 mongoimport --uri=mongodb://fisiodesk-mongodb:27017/fisiodesk --collection=diario_trattamenti --file=/data/diario_trattamenti.json --jsonArray --drop 2>nul
docker run --rm --network fisiodesk-ai-healthcare-assignment_fisiodesk-network -v "%%cd%%/data:/data" mongo:7.0 mongoimport --uri=mongodb://fisiodesk-mongodb:27017/fisiodesk --collection=eventi_calendario --file=/data/eventi_calendario.json --jsonArray --drop 2>nul
echo [OK] Dati importati
echo.
goto status_display

:rebuild
echo.
echo [*] Ferma e rimuovi servizi esistenti...
docker-compose down -v
echo.
echo [*] Avvio con rebuild completo...
docker-compose up -d --build
echo.
echo [*] Attesa avvio servizi (60 secondi)...
timeout /t 60 /nobreak >nul
goto status_display

:stop
echo.
echo [*] Ferma tutti i servizi...
docker-compose down
echo [OK] Servizi fermati
goto end

:status
:status_display
echo.
echo ================================================
echo   STATUS SERVIZI
echo ================================================
echo.
docker-compose ps
echo.
echo ================================================
echo   URL SERVIZI
echo ================================================
echo.
echo   API Flask:        http://localhost:5000
echo   Frontend HTML:    http://localhost:5000/index.html
echo   MongoDB Express:  http://localhost:8081
echo   MongoDB:          localhost:27017
echo.
goto end

:open
echo.
echo [*] Apertura interfacce nel browser...
start http://localhost:5000/index.html
start http://localhost:8081
echo [OK] Apertura completata
goto end

:end
echo.
echo ================================================
echo   Operazione completata
echo ================================================
echo.
pause
