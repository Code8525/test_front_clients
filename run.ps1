Set-Location $PSScriptRoot
if (Test-Path .venv\Scripts\Activate.ps1) {
    .\.venv\Scripts\Activate.ps1
}
uvicorn src.main:app --reload
