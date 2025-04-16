#!/usr/bin/env bash

# Exits immediately if any command returns a non-zero exit status
set -e

echo "🚀 Running backend API unit tests..."

uv sync --group test --no-dev

DIR="$( cd "$( dirname "$0" )/../tests" && pwd )"

python -m pytest "${DIR}" -W ignore::DeprecationWarning -v

echo "✅ Backend API unit tests passed!"
