# Installs (or updates) Stoic Desktop for the current Windows user. No administrator rights needed.
# Run it through install.cmd. Everything goes in %LOCALAPPDATA%\StoicDesktop.

$ErrorActionPreference = 'Continue'
$AppName = 'Stoic Desktop'
$Source  = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Dest    = Join-Path $env:LOCALAPPDATA 'StoicDesktop'
$Venv    = Join-Path $Dest 'venv'
$Programs = [Environment]::GetFolderPath('Programs')
$Startup  = [Environment]::GetFolderPath('Startup')

function Say($text)  { Write-Host "  $text" }
function Step($text) { Write-Host ""; Write-Host "> $text" -ForegroundColor Cyan }
function Fail($text) {
    Write-Host ""
    Write-Host "  Something went wrong: $text" -ForegroundColor Red
    Write-Host "  Nothing else was changed. Fix that, then double-click install.cmd again."
    exit 1
}

function Test-Python($exe) {
    try {
        $out = & $exe -c "import sys; print(sys.version_info >= (3, 10))" 2>$null
        return ($LASTEXITCODE -eq 0 -and "$out".Trim() -eq 'True')
    } catch { return $false }
}

function Find-Python {
    $candidates = @()
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        try { $p = & $launcher.Source -3 -c "import sys; print(sys.executable)" 2>$null; if ($p) { $candidates += "$p".Trim() } } catch {}
    }
    # Skip the Microsoft Store placeholder "python.exe", which only opens the Store.
    $candidates += Get-Command python.exe -All -ErrorAction SilentlyContinue |
        Where-Object { $_.Source -notlike '*\WindowsApps\*' } | ForEach-Object { $_.Source }
    $candidates += Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe", "$env:ProgramFiles\Python3*\python.exe" `
        -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | ForEach-Object { $_.FullName }
    foreach ($p in $candidates) {
        if ($p -and (Test-Path $p) -and (Test-Python $p)) { return $p }
    }
    return $null
}

function New-Shortcut($path, $target, $arguments, $workdir, $description) {
    $shell = New-Object -ComObject WScript.Shell
    $s = $shell.CreateShortcut($path)
    $s.TargetPath = $target
    $s.Arguments = $arguments
    $s.WorkingDirectory = $workdir
    $s.Description = $description
    $s.Save()
}

Write-Host ""
Write-Host "  ===== Installing $AppName =====" -ForegroundColor Yellow

# 1. Python 3.10 or newer
Step "Looking for Python 3.10 or newer..."
$Python = Find-Python
if (-not $Python) {
    if (Get-Command winget.exe -ErrorAction SilentlyContinue) {
        Say "Python isn't installed. Installing it from Microsoft's package manager (a minute or two)..."
        winget install --id Python.Python.3.13 --exact --scope user --silent --accept-package-agreements --accept-source-agreements
        $Python = Find-Python
    }
    if (-not $Python) {
        Say "Please install Python from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'),"
        Say "then double-click install.cmd again."
        Start-Process 'https://www.python.org/downloads/'
        Fail "Python 3.10 or newer wasn't found."
    }
}
Say "Using $Python"

# 2. Close a copy that's already running (this also updates an existing install)
Step "Closing Stoic Desktop if it's running..."
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*stoic_desktop.py*' -or $_.CommandLine -like '*motivational_quotes.py*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
# Startup files made by hand from the old instructions would start a second, older copy.
Get-ChildItem $Startup -Filter '*.cmd' -ErrorAction SilentlyContinue |
    Where-Object { (Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue) -match 'motivational_quotes\.py' } |
    ForEach-Object { Remove-Item $_.FullName -Force; Say "Removed the old startup file $($_.Name)" }

# 3. Copy the app
Step "Copying the app to $Dest ..."
New-Item -ItemType Directory -Force -Path (Join-Path $Dest 'scripts') | Out-Null
foreach ($f in 'stoic_desktop.py', 'requirements.txt', 'LICENSE', 'README.md') {
    Copy-Item (Join-Path $Source $f) (Join-Path $Dest $f) -Force -ErrorAction Stop
}
foreach ($f in 'uninstall.ps1', 'pip.txt') {
    Copy-Item (Join-Path $Source "scripts\$f") (Join-Path $Dest "scripts\$f") -Force -ErrorAction Stop
}

# 4. A private Python environment with the exact, fingerprint-checked PyQt6
Step "Setting up the app's own Python environment (first time: a minute or two)..."
if (-not (Test-Path (Join-Path $Venv 'Scripts\python.exe'))) {
    & $Python -m venv $Venv
    if ($LASTEXITCODE -ne 0) { Fail "couldn't create the Python environment." }
}
$VenvPython = Join-Path $Venv 'Scripts\python.exe'
$VenvPythonw = Join-Path $Venv 'Scripts\pythonw.exe'
& $VenvPython -m pip install --disable-pip-version-check --quiet --require-hashes --only-binary ':all:' -r (Join-Path $Dest 'scripts\pip.txt')
if ($LASTEXITCODE -ne 0) { Fail "couldn't update pip (is the internet connected?)." }
& $VenvPython -m pip install --disable-pip-version-check --quiet --require-hashes --only-binary ':all:' -r (Join-Path $Dest 'requirements.txt')
if ($LASTEXITCODE -ne 0) { Fail "couldn't download PyQt6 (is the internet connected?)." }
Say "PyQt6 installed."

# 5. Shortcuts: Start menu, start with Windows, and an uninstaller
Step "Adding shortcuts..."
$Script = Join-Path $Dest 'stoic_desktop.py'
$MenuDir = Join-Path $Programs $AppName
New-Item -ItemType Directory -Force -Path $MenuDir | Out-Null
New-Shortcut (Join-Path $MenuDir "$AppName.lnk") $VenvPythonw "`"$Script`"" $Dest 'Stoic quotes on your desktop'
New-Shortcut (Join-Path $MenuDir "Uninstall $AppName.lnk") "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" `
    "-NoProfile -ExecutionPolicy Bypass -File `"$(Join-Path $Dest 'scripts\uninstall.ps1')`"" $Dest "Remove $AppName"
New-Shortcut (Join-Path $Startup "$AppName.lnk") $VenvPythonw "`"$Script`"" $Dest 'Stoic quotes on your desktop'
Say "Start menu: $AppName"
Say "Starts by itself when you sign in to Windows (right-click the quote to turn that off)."

# 6. Start it
Step "Starting $AppName..."
Start-Process -FilePath $VenvPythonw -ArgumentList "`"$Script`"" -WorkingDirectory $Dest

Write-Host ""
Write-Host "  Done! The quote is on your desktop now; a new wallpaper follows in a few seconds." -ForegroundColor Green
Write-Host "  Drag the quote to move it. Right-click it for the menu."
