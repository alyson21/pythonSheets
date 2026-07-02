@echo off
setlocal EnableExtensions

set "SOURCE_SFX=%~1"
set "PACKAGE_ROOT=%~dp0"
set "APP_DIR=%PACKAGE_ROOT%app"
set "FALLBACK_TARGET=0"
call :resolve_source_sfx
set "TARGET_DIR="
if not "%SOURCE_SFX%"=="" (
    for %%I in ("%SOURCE_SFX%") do set "TARGET_DIR=%%~dpI"
)
if "%TARGET_DIR%"=="" (
    set "TARGET_DIR=%USERPROFILE%\Desktop\Automacao\"
    set "FALLBACK_TARGET=1"
)
set "RUNTIME_ROOT=%LocalAppData%\AutomacaoPlanilhas"
set "RUNTIME_DATA_DIR=%RUNTIME_ROOT%\dados"
set "LOG_DIR=%TEMP%\AutomacaoInstalador"
set "LOG=%LOG_DIR%\instalador.log"
set "PYTHON_VERSION=3.12.9"
set "PYTHON_INSTALLER=python-%PYTHON_VERSION%-amd64.exe"
set "PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_INSTALLER%"
set "PYTHON_TMP=%TEMP%\%PYTHON_INSTALLER%"
set "PYTHON_LAUNCHER="
set "PYTHON_ARGS="

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo [%date% %time%] Iniciando instalador.bat > "%LOG%"
echo [%date% %time%] SOURCE_SFX=%SOURCE_SFX% >> "%LOG%"
echo [%date% %time%] TARGET_DIR=%TARGET_DIR% >> "%LOG%"
echo [%date% %time%] RUNTIME_DATA_DIR=%RUNTIME_DATA_DIR% >> "%LOG%"
echo [%date% %time%] FALLBACK_TARGET=%FALLBACK_TARGET% >> "%LOG%"

if "%FALLBACK_TARGET%"=="1" (
    echo Aviso: nao foi possivel localizar o caminho do instalador original.
    echo Os arquivos finais serao salvos em "%TARGET_DIR%".
)

if not exist "%APP_DIR%" (
    echo ERRO: pasta app nao encontrada em "%PACKAGE_ROOT%".
    echo [%date% %time%] ERRO: pasta app nao encontrada. >> "%LOG%"
    pause
    exit /b 1
)

pushd "%APP_DIR%" >nul

if not exist GerarExe.bat (
    echo ERRO: GerarExe.bat nao encontrado em "%APP_DIR%".
    echo [%date% %time%] ERRO: GerarExe.bat nao encontrado. >> "%LOG%"
    popd >nul
    pause
    exit /b 1
)

call :ensure_python
if errorlevel 1 (
    echo ERRO: nao foi possivel preparar o Python automaticamente. Veja "%LOG%".
    popd >nul
    pause
    exit /b 1
)

if not exist automacao.exe (
    echo automacao.exe nao encontrado. Gerando executavel local...
    echo [%date% %time%] Chamando GerarExe.bat. >> "%LOG%"
    call GerarExe.bat /nopause >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo ERRO: falha ao gerar automacao.exe. Veja "%LOG%" e "%APP_DIR%\logs\GerarExe.log".
        echo [%date% %time%] ERRO: falha ao gerar automacao.exe. >> "%LOG%"
        popd >nul
        pause
        exit /b 1
    )
)

call :sync_runtime_data
if errorlevel 1 (
    echo ERRO: nao foi possivel preparar os dados de runtime. Veja "%LOG%".
    popd >nul
    pause
    exit /b 1
)

call :publish_artifacts
if errorlevel 1 (
    echo ERRO: nao foi possivel copiar os arquivos finais para "%TARGET_DIR%". Veja "%LOG%".
    popd >nul
    pause
    exit /b 1
)

if not exist automacao.exe (
    echo ERRO: automacao.exe nao existe apos o build.
    echo [%date% %time%] ERRO: automacao.exe nao existe apos o build. >> "%LOG%"
    popd >nul
    pause
    exit /b 1
)

popd >nul

echo Build concluido. Arquivos finais em "%TARGET_DIR%".
call :launch_app
call :delete_source_sfx
echo [%date% %time%] Finalizado com sucesso. >> "%LOG%"
exit /b 0

:publish_artifacts
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

if exist "%TARGET_DIR%automacao.exe" del /q "%TARGET_DIR%automacao.exe" >> "%LOG%" 2>&1
copy /y "automacao.exe" "%TARGET_DIR%automacao.exe" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [%date% %time%] ERRO: falha ao copiar automacao.exe para TARGET_DIR. >> "%LOG%"
    exit /b 1
)

echo [%date% %time%] automacao.exe copiado para TARGET_DIR. >> "%LOG%"
exit /b 0

:sync_runtime_data
if not exist "%RUNTIME_ROOT%" mkdir "%RUNTIME_ROOT%" >> "%LOG%" 2>&1
if not exist "%RUNTIME_DATA_DIR%" mkdir "%RUNTIME_DATA_DIR%" >> "%LOG%" 2>&1

xcopy "dados" "%RUNTIME_DATA_DIR%\" /E /I /Y /Q >> "%LOG%" 2>&1
if errorlevel 2 (
    echo [%date% %time%] ERRO: falha ao copiar dados para RUNTIME_DATA_DIR. >> "%LOG%"
    exit /b 1
)

echo [%date% %time%] Dados de runtime sincronizados em RUNTIME_DATA_DIR. >> "%LOG%"
exit /b 0

:launch_app
if not exist "%TARGET_DIR%automacao.exe" (
    echo [%date% %time%] ERRO: automacao.exe nao encontrado para iniciar em TARGET_DIR. >> "%LOG%"
    exit /b 1
)

echo [%date% %time%] Iniciando aplicacao: %TARGET_DIR%automacao.exe >> "%LOG%"
start "" /D "%TARGET_DIR%" "%TARGET_DIR%automacao.exe"
exit /b 0

:delete_source_sfx
set "DELETE_CANDIDATE=%SOURCE_SFX%"
if "%DELETE_CANDIDATE%"=="" set "DELETE_CANDIDATE=%TARGET_DIR%instalador.exe"
if "%DELETE_CANDIDATE%"=="" exit /b 0
if not exist "%DELETE_CANDIDATE%" exit /b 0

echo [%date% %time%] DELETE_CANDIDATE=%DELETE_CANDIDATE% >> "%LOG%"
echo [%date% %time%] Agendando remocao do instalador original: %DELETE_CANDIDATE% >> "%LOG%"
set "CLEANUP_CMD=%LOG_DIR%\cleanup-installer.cmd"
> "%CLEANUP_CMD%" echo @echo off
>> "%CLEANUP_CMD%" echo set "TARGET=%DELETE_CANDIDATE%"
>> "%CLEANUP_CMD%" echo for /l %%%%N in ^(1,1,60^) do ^(
>> "%CLEANUP_CMD%" echo     del /f /q "%%TARGET%%" ^>nul 2^>nul
>> "%CLEANUP_CMD%" echo     if not exist "%%TARGET%%" exit /b 0
>> "%CLEANUP_CMD%" echo     timeout /t 1 /nobreak ^>nul
>> "%CLEANUP_CMD%" echo ^)
start "" /min "%CLEANUP_CMD%"
exit /b 0

:resolve_source_sfx
if not "%SOURCE_SFX%"=="" (
    if exist "%SOURCE_SFX%" exit /b 0
)

set "SOURCE_SFX="
where powershell >nul 2>nul
if errorlevel 1 exit /b 0

for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; $result=''; $temp=[System.IO.Path]::GetFullPath($env:TEMP); $pidNow=$PID; for($i=0;$i -lt 12;$i++){ $p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$pidNow); if(-not $p){break}; $pidNow=$p.ParentProcessId; if(-not $pidNow){break}; $a=Get-CimInstance Win32_Process -Filter ('ProcessId='+$pidNow); if(-not $a){break}; $exe=$a.ExecutablePath; if(-not $exe){continue}; $name=(''+$a.Name).ToLowerInvariant(); if(@('cmd.exe','powershell.exe','pwsh.exe','conhost.exe') -contains $name){continue}; $full=[System.IO.Path]::GetFullPath($exe); if($full.StartsWith($temp,[System.StringComparison]::OrdinalIgnoreCase)){continue}; if(Test-Path $full){$result=$full; break}}; if(-not $result){$roots=@($env:USERPROFILE+'\\Desktop',$env:USERPROFILE+'\\Downloads',$env:USERPROFILE+'\\Documents'); $hits=foreach($r in $roots){if(Test-Path $r){Get-ChildItem -Path $r -Filter '*.exe' -Recurse -File -ErrorAction SilentlyContinue ^| Where-Object { $_.FullName -notlike ($env:TEMP+'*') -and $_.Name -ne 'automacao.exe' }}}; $f=$hits ^| Sort-Object LastWriteTime -Descending ^| Select-Object -First 1; if($f){$result=$f.FullName}}; if($result){$result}"`) do set "SOURCE_SFX=%%I"

if not "%SOURCE_SFX%"=="" (
    if not exist "%SOURCE_SFX%" set "SOURCE_SFX="
)
exit /b 0

:ensure_python
call :detect_python
if not "%PYTHON_LAUNCHER%"=="" (
    echo Python encontrado: %PYTHON_LAUNCHER% %PYTHON_ARGS%
    echo [%date% %time%] Python encontrado: %PYTHON_LAUNCHER% %PYTHON_ARGS% >> "%LOG%"
    exit /b 0
)

echo Python nao encontrado. Iniciando instalacao automatica...
echo [%date% %time%] Python nao encontrado. Instalacao automatica iniciada. >> "%LOG%"

call :install_python
if errorlevel 1 exit /b 1

call :detect_python
if "%PYTHON_LAUNCHER%"=="" (
    echo [%date% %time%] ERRO: Python nao encontrado apos instalacao automatica. >> "%LOG%"
    exit /b 1
)

echo [%date% %time%] Instalacao automatica do Python concluida. >> "%LOG%"
exit /b 0

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

:install_python
where powershell >nul 2>nul
if errorlevel 1 (
    echo ERRO: PowerShell nao encontrado no Windows.
    echo [%date% %time%] ERRO: PowerShell nao encontrado para baixar Python. >> "%LOG%"
    exit /b 1
)

echo Baixando Python %PYTHON_VERSION%...
echo [%date% %time%] Download de Python iniciado: %PYTHON_URL% >> "%LOG%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri '%PYTHON_URL%' -OutFile '%PYTHON_TMP%'" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo ERRO: falha no download do instalador Python.
    echo [%date% %time%] ERRO: falha no download do Python. >> "%LOG%"
    exit /b 1
)

if not exist "%PYTHON_TMP%" (
    echo ERRO: instalador Python nao foi baixado para "%PYTHON_TMP%".
    echo [%date% %time%] ERRO: arquivo do instalador Python nao encontrado apos download. >> "%LOG%"
    exit /b 1
)

echo Instalando Python automaticamente...
echo [%date% %time%] Instalacao silenciosa do Python iniciada. >> "%LOG%"
"%PYTHON_TMP%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_test=0 Include_tcltk=1 >> "%LOG%" 2>&1
if errorlevel 1 (
    echo ERRO: falha na instalacao do Python.
    echo [%date% %time%] ERRO: falha na instalacao silenciosa do Python. >> "%LOG%"
    exit /b 1
)

if exist "%PYTHON_TMP%" del /q "%PYTHON_TMP%" >> "%LOG%" 2>&1
echo [%date% %time%] Instalador temporario removido. >> "%LOG%"
exit /b 0
