param(
    [ValidateSet('console', 'probe', 'guided', 'ports', 'self-test')]
    [string]$Mode = 'console',
    [string]$Port = ''
)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$clientPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $clientPython)) {
    throw 'Project Python environment missing. Run setup_client.ps1 first.'
}
if ($Mode -eq 'self-test') {
    & $clientPython -m unittest discover -s (Join-Path $projectRoot 'raspberry\hardware') -p 'test_*.py' -v
    exit $LASTEXITCODE
}
$clientArgs = @((Join-Path $projectRoot 'raspberry\hardware\test_serial.py'))
if ($Port) { $clientArgs += @('--port', $Port) }
switch ($Mode) {
    'ports' { $clientArgs += '--list-ports' }
    'probe' { $clientArgs += '--probe' }
    'guided' { $clientArgs += @('--guided', '--report', (Join-Path $projectRoot 'test-reports\manual-test.json')) }
}
if ($Mode -ne 'ports') {
    $clientArgs += @('--log-file', (Join-Path $projectRoot 'test-reports\serial.log'))
}
& $clientPython @clientArgs
exit $LASTEXITCODE
