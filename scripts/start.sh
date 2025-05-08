#!/usr/bin/env bash

# Recommended for safer scripting:
set -Eeuo pipefail

echo "⏳ Loading azd .env file from current environment..."

# Read environment values from `azd env get-values`.
# If `azd` or this command fails, the script will exit due to `set -Eeuo pipefail`.
while IFS='=' read -r key value; do
    # Remove surrounding quotes from the value if present
    value="$(echo "$value" | sed 's/^"//;s/"$//')"
    export "$key=$value"
done <<EOF
$(azd env get-values)
EOF

echo "✅ Environment variables set!"

# Check if 'uv' is installed
if ! command -v uv >/dev/null 2>&1; then
    echo -e "📦 'uv' not installed. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || {
        echo -e "❌ Failed to install 'uv'."
        return 1
    }
    source "$HOME/.cargo/env"
fi

echo -e "💪 Creating virtual environment..."
if ! uv venv; then
    echo -e "❌ Failed to create virtual environment."
    return 1
fi

echo -e "⚙️ Activating virtual environment..."
if ! source .venv/bin/activate; then
    echo -e "❌ Failed to activate virtual environment."
    return 1
fi

echo -e "🔄 Syncing dependencies..."
if ! uv sync --no-dev; then
    echo -e "❌ Failed to sync dependencies."
    return 1
fi

echo "✅ Environment setup complete!"

echo -e "🚀 Starting server..."

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
