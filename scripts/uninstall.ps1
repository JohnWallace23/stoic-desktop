# Removes Stoic Desktop for the current Windows user. Your wallpaper stays as it is; change it in
# Windows Settings > Personalization > Background if you like.

$AppName = 'Stoic Desktop'
$Dest    = Join-Path $env:LOCALAPPDATA 'StoicDesktop'

Write-Host ""
Write-Host "  ===== Removing $AppName =====" -ForegroundColor Yellow

Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*stoic_desktop.py*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 500

Remove-Item (Join-Path ([Environment]::GetFolderPath('Startup')) "$AppName.lnk") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path ([Environment]::GetFolderPath('Programs')) $AppName) -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item 'HKCU:\Software\StoicDesktop' -Recurse -Force -ErrorAction SilentlyContinue   # its saved position and timing
foreach ($f in 'stoic_wallpaper_A.jpg', 'stoic_wallpaper_B.jpg') {
    Remove-Item (Join-Path $env:TEMP $f) -Force -ErrorAction SilentlyContinue
}
if (Test-Path $Dest) {
    Remove-Item $Dest -Recurse -Force -ErrorAction SilentlyContinue
}

if (Test-Path $Dest) {
    Write-Host "  Almost done: close any open Stoic Desktop window and run this again to finish." -ForegroundColor Red
} else {
    Write-Host "  $AppName is removed." -ForegroundColor Green
}
