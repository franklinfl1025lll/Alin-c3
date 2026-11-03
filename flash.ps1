# Flash the Alin C3 firmware (merged-binary.bin) and open the serial monitor.
#
#   .\flash.ps1                 # auto-detect the port, flash, then monitor
#   .\flash.ps1 -Port COM5      # force a port
#   .\flash.ps1 -Build          # rebuild first, then flash
#   .\flash.ps1 -NoMonitor      # flash only
param(
    [string]$Port = "",
    [switch]$Build,
    [switch]$NoMonitor
)
$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot
$idfRoot = "D:/Espressif/frameworks/esp-idf-v5.5.6"
$py = "D:/Espressif/python_env/idf5.5_py3.11_env/Scripts/python.exe"
$merged = Join-Path $repo "build/merged-binary.bin"

function Get-EspPort {
    # Bluetooth virtual ports are BTHENUM devices: never flash those.
    $devices = Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "\(COM\d+\)" -and $_.PNPDeviceID -notmatch "^BTHENUM" }
    if (-not $devices) { return "" }
    # Espressif USB-JTAG (303A), CH34x (1A86), CP210x (10C4), FTDI (0403)
    $preferred = $devices | Where-Object { $_.PNPDeviceID -match "VID_303A|VID_1A86|VID_10C4|VID_0403" }
    $pick = if ($preferred) { $preferred | Select-Object -First 1 } else { $devices | Select-Object -First 1 }
    if ($pick.Name -match "\((COM\d+)\)") { return $Matches[1] }
    return ""
}

if ($Build) {
    Write-Host "== building alin-c3 ==" -ForegroundColor Cyan
    Push-Location $repo
    & $py "scripts/build.py" alin-c3
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw "build failed" }
    Pop-Location
}

if (-not (Test-Path $merged)) { throw "build/merged-binary.bin not found - run: python scripts/build.py alin-c3" }

if (-not $Port) {
    $Port = Get-EspPort
    if (-not $Port) {
        Write-Host "No USB serial port found." -ForegroundColor Yellow
        Write-Host "1) Plug the board into a USB data port (not a charge-only cable)."
        Write-Host "2) In Device Manager > Ports you should see: USB JTAG/serial debug unit (COMx)"
        Write-Host "   or USB-SERIAL CH340 (COMx) which needs the CH340 driver."
        Write-Host "3) Then run: .\flash.ps1 -Port COM5"
        exit 1
    }
}

Write-Host ("== flashing " + $merged + " to " + $Port + " ==") -ForegroundColor Cyan
& $py -m esptool --chip esp32c3 -p $Port -b 460800 --before default_reset --after hard_reset write_flash 0x0 $merged
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Flash failed. Try these in order:" -ForegroundColor Yellow
    Write-Host "  1) Hold BOOT, tap RESET, release BOOT, then run again."
    Write-Host "  2) Close anything else using the port (Arduino IDE, another monitor, VS Code)."
    Write-Host "  3) Lower the baud rate: change -b 460800 to -b 115200."
    throw "flash failed"
}

if (-not $NoMonitor) {
    Write-Host "== opening monitor (Ctrl+] to quit) ==" -ForegroundColor Cyan
    if (-not $env:IDF_PATH) {
        $env:PATH = "D:/Espressif/python_env/idf5.5_py3.11_env/Scripts;" + $env:PATH
        . "$idfRoot/export.ps1" *> $null
    }
    & $py "$env:IDF_PATH/tools/idf.py" -p $Port monitor
}
