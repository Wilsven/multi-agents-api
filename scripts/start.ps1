Write-Host "⏳ Loading azd .env file from current environment..."

# Read environment values from `azd env get-values`.
$azdOutput = azd env get-values
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to load environment variables from azd environment."
    exit $LASTEXITCODE
}

foreach ($line in $azdOutput) {
    if ($line -match "([^=]+)=(.*)") {
        $key = $matches[1]
        $value = $matches[2] -replace '^"|"$'
        Set-Item -Path "env:\$key" -Value $value
    }
}

Write-Host "✅ Environment variables set!"

# Check if 'uv' is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
Write-Output "📦 'uv' not installed. Installing..."
$installScript = (New-Object System.Net.WebClient).DownloadString('https://astral.sh/uv/install.ps1')
if (-not $?) {
    Write-Error "❌ Failed to download 'uv' install script."
    exit 1
}
Invoke-Expression $installScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Failed to install 'uv'."
    exit $LASTEXITCODE
}
# Ensure the newly installed location is in PATH for this session
$env:Path += ";C:\Users\$env:USERNAME\.local\bin"
}

Write-Output "🛠️ Creating virtual environment..."
uv venv
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Failed to create virtual environment."
    exit $LASTEXITCODE
}

Write-Host "⚙️ Activating virtual environment..."
& ./.venv/Scripts/Activate
# Because 'Activate' is usually a script, we check $?
if (-not $?) {
    Write-Error "❌ Failed to activate virtual environment."
    exit 1
}

Write-Host "🔄 Syncing dependencies..."
uv sync --no-dev
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Failed to sync dependencies."
    exit $LASTEXITCODE
}

Write-Output "✅ Environment setup complete!"

Write-Output "🚀 Starting server..."

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000