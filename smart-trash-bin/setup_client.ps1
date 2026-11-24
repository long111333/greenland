$ErrorActionPreference = 'Stop'
$clientPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $clientPython)) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $bootstrapPython = $pythonCommand.Source
    } else {
        $bootstrapPython = Join-Path $env:USERPROFILE '.platformio\penv\Scripts\python.exe'
    }
    if (-not (Test-Path -LiteralPath $bootstrapPython)) { throw 'Install Python 3.10+ or PlatformIO first.' }
    & $bootstrapPython -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment.' }
}
& $clientPython -m pip install -r (Join-Path $PSScriptRoot 'raspberry\hardware\requirements.txt')
exit $LASTEXITCODE
