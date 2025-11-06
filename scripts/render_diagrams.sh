#!/usr/bin/env bash
# Render D2 architecture diagrams to SVG
# Usage: bash scripts/render_diagrams.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIAGRAMS_DIR="$PROJECT_ROOT/docs/diagrams"

echo "🎨 Rendering GIS-OSS architecture diagrams..."

# Check if D2 is installed
if ! command -v d2 &> /dev/null; then
    echo "❌ Error: D2 is not installed."
    echo ""
    echo "Install D2:"
    echo "  macOS:  brew install d2"
    echo "  Linux:  curl -fsSL https://d2lang.com/install.sh | sh -s --"
    echo ""
    echo "Or visit: https://d2lang.com/tour/install"
    exit 1
fi

# Render technical architecture diagram
echo "  → Rendering architecture.d2..."
d2 "$DIAGRAMS_DIR/architecture.d2" "$DIAGRAMS_DIR/architecture.svg" \
    --theme=200 \
    --dark-theme=200 \
    --pad=40 \
    --sketch=false

# Optional: Render dark mode version
echo "  → Rendering architecture-dark.d2 (dark mode)..."
d2 "$DIAGRAMS_DIR/architecture.d2" "$DIAGRAMS_DIR/architecture-dark.svg" \
    --theme=200 \
    --dark-theme=200 \
    --pad=40 \
    --sketch=false

echo ""
echo "✅ Diagrams rendered successfully!"
echo ""
echo "Output files:"
echo "  - $DIAGRAMS_DIR/architecture.svg"
echo "  - $DIAGRAMS_DIR/architecture-dark.svg"
echo ""
echo "Note: Excalidraw diagrams must be manually exported from https://excalidraw.com"
echo "      1. Open conceptual-flow.excalidraw in Excalidraw"
echo "      2. File → Export image → SVG"
echo "      3. Save as conceptual-flow.svg"

