# Exit if any command fails
$ErrorActionPreference = "Stop"

Write-Output "🚀 Running backend API unit tests..."

uv sync --group test --no-dev

$DIR = Resolve-Path "$PSScriptRoot/../tests"

python -m pytest "$DIR" -W ignore::DeprecationWarning -v

Write-Output "✅ Backend API unit tests passed!"
