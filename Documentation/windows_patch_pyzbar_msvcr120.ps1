param(
    [string]$VenvPath = ".venv",
    [string]$SourceDll = ""
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pyzbarDir = Join-Path $repoRoot "$VenvPath\Lib\site-packages\pyzbar"
$targetDll = Join-Path $pyzbarDir "msvcr120.dll"

if (-not (Test-Path $pyzbarDir)) {
    throw "pyzbar package directory not found: $pyzbarDir"
}

if (-not $SourceDll) {
    $candidates = @(
        "$env:SystemRoot\System32\msvcr120.dll",
        "C:\Program Files\Microsoft Visual Studio 12.0\VC\redist\x64\Microsoft.VC120.CRT\msvcr120.dll",
        "C:\Program Files\Maxon Cinema 4D 2025\resource\libs\win64\msvcr120.dll"
    )

    $SourceDll = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (-not $SourceDll -or -not (Test-Path $SourceDll)) {
    throw "Could not locate msvcr120.dll. Provide -SourceDll <full path to msvcr120.dll>."
}

Copy-Item -Path $SourceDll -Destination $targetDll -Force
Write-Host "Copied msvcr120.dll to: $targetDll"

$pythonExe = Join-Path $repoRoot "$VenvPath\Scripts\python.exe"
if (Test-Path $pythonExe) {
    & $pythonExe -c "from pyzbar import pyzbar; print('pyzbar import ok')"
    if ($LASTEXITCODE -ne 0) {
        throw "pyzbar import check failed after patch."
    }
}

Write-Host "Done. You can now run:"
Write-Host "  .\\$VenvPath\\Scripts\\python -m pytest tests\\test_flows_seed.py -k 'codex32_backup'"
