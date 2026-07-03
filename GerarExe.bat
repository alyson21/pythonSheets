@echo off
setlocal EnableExtensions

pushd "%~dp0" >nul

if not exist logs mkdir logs
set "LOG=logs\GerarExe.log"
set "PYTHON_LAUNCHER="
set "PYTHON_ARGS="

echo [%date% %time%] Iniciando build do automacao.exe > "%LOG%"

call :detect_python
if "%PYTHON_LAUNCHER%"=="" (
    echo ERRO: Python nao encontrado no PATH. Rode instalador.bat para instalacao automatica.
    echo [%date% %time%] ERRO: Python nao encontrado no PATH. >> "%LOG%"
    set "EXIT_CODE=1"
    goto :end
)

if not exist main.py (
    echo ERRO: main.py nao encontrado em "%CD%".
    echo [%date% %time%] ERRO: main.py nao encontrado. >> "%LOG%"
    set "EXIT_CODE=1"
    goto :end
)

if not exist requirements.txt (
    echo ERRO: requirements.txt nao encontrado em "%CD%".
    echo [%date% %time%] ERRO: requirements.txt nao encontrado. >> "%LOG%"
    set "EXIT_CODE=1"
    goto :end
)

echo Instalando dependencias...
"%PYTHON_LAUNCHER%" %PYTHON_ARGS% -m pip install -r requirements.txt --quiet >> "%LOG%" 2>&1
if errorlevel 1 (
    echo ERRO: falha ao instalar dependencias. Veja "%LOG%".
    set "EXIT_CODE=1"
    goto :end
)

"%PYTHON_LAUNCHER%" %PYTHON_ARGS% -m pip install pyinstaller xlrd --quiet >> "%LOG%" 2>&1
if errorlevel 1 (
    echo ERRO: falha ao instalar PyInstaller. Veja "%LOG%".
    set "EXIT_CODE=1"
    goto :end
)

echo Gravando versao...
set "SHA="
for /f "delims=" %%i in ('git rev-parse HEAD 2^>nul') do set "SHA=%%i"
if "%SHA%"=="" set "SHA=dev"
> automacao\_version.py echo VERSION = "%SHA%"

echo Gerando automacao.exe...
"%PYTHON_LAUNCHER%" %PYTHON_ARGS% -m PyInstaller --onefile --windowed --name automacao --icon automacao\assets\factus.ico --splash automacao\assets\factus_splash.png --add-data "automacao\assets;automacao\assets" main.py >> "%LOG%" 2>&1
if errorlevel 1 (
    echo ERRO: falha ao compilar com PyInstaller. Veja "%LOG%".
    set "EXIT_CODE=1"
    goto :end
)

if exist automacao.exe del /q automacao.exe >> "%LOG%" 2>&1
if exist dist\automacao.exe move /y dist\automacao.exe automacao.exe >> "%LOG%" 2>&1

if exist build rmdir /s /q build >> "%LOG%" 2>&1
if exist automacao.spec del /q automacao.spec >> "%LOG%" 2>&1
if exist dist rmdir /s /q dist >> "%LOG%" 2>&1

if not exist automacao.exe (
    echo ERRO: automacao.exe nao foi criado. Veja "%LOG%".
    set "EXIT_CODE=1"
    goto :end
)

echo [%date% %time%] Build concluido com sucesso. >> "%LOG%"
echo automacao.exe gerado com sucesso.
set "EXIT_CODE=0"

:end
popd >nul
if /I not "%~1"=="/nopause" pause
exit /b %EXIT_CODE%

:detect_python
set "PYTHON_LAUNCHER="
set "PYTHON_ARGS="

python -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_LAUNCHER=python"
    exit /b 0
)

py -3 -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_LAUNCHER=py"
    set "PYTHON_ARGS=-3"
    exit /b 0
)

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"
    set "PYTHON_LAUNCHER=%LocalAppData%\Programs\Python\Python312\python.exe"
    exit /b 0
)

if exist "%ProgramFiles%\Python312\python.exe" (
    set "PATH=%ProgramFiles%\Python312;%ProgramFiles%\Python312\Scripts;%PATH%"
    set "PYTHON_LAUNCHER=%ProgramFiles%\Python312\python.exe"
    exit /b 0
)

exit /b 0
