#!/bin/bash

# WikiArchitect Professional macOS Build Script
# This requires Nuitka: pip install nuitka

echo "🚀 Starting Professional macOS Build for WikiArchitect..."

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Run Nuitka Build
# --macos-create-app-bundle: Creates the .app structure
# --macos-app-name: The name in the Finder and Menu Bar
# --macos-app-display-name: The human-readable name
# --onefile: Bundle everything into a single executable
# --enable-plugin=pylint-warnings: Optional but good for QA
# --standalone: Include Python runtime

uv run python -m nuitka \
    --standalone \
    --macos-create-app-bundle \
    --macos-app-name="WikiArchitect" \
    --macos-app-display-name="WikiArchitect" \
    --macos-app-version="0.1.3" \
    --include-data-dir=docs=docs \
    --include-data-dir=schema=schema \
    --output-dir=build \
    src/main.py

echo "✅ Build Complete! You can find the app in build/WikiArchitect.app"
