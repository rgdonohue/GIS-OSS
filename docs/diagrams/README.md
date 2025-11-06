# Diagram Assets

This directory contains source files and rendered outputs for GIS-OSS architecture diagrams.

## Files

- **`architecture.d2`** — Technical architecture diagram source (D2 format)
- **`architecture.svg`** — Rendered technical diagram (auto-generated)
- **`conceptual-flow.excalidraw`** — Conceptual workflow diagram (Excalidraw format)
- **`conceptual-flow.svg`** — Rendered conceptual diagram

## Editing Diagrams

### Technical Architecture (D2)

1. Edit `architecture.d2` using any text editor
2. Render locally (requires [D2](https://d2lang.com/tour/install)):
   ```bash
   d2 architecture.d2 architecture.svg --theme=200 --pad=40
   ```
3. Or run the convenience script from repo root:
   ```bash
   bash scripts/render_diagrams.sh
   ```

### Conceptual Flow (Excalidraw)

1. Visit [Excalidraw](https://excalidraw.com)
2. Open `conceptual-flow.excalidraw` via File → Open
3. Edit the diagram
4. Export as SVG: File → Export image → SVG → Save as `conceptual-flow.svg`

## Offline/Air-gapped Rendering

For deployments without internet access:

1. **Install D2 on connected machine:**
   ```bash
   # macOS
   brew install d2
   
   # Linux (binary)
   curl -fsSL https://d2lang.com/install.sh | sh -s --
   ```

2. **Pre-render all diagrams:**
   ```bash
   bash scripts/render_diagrams.sh
   ```

3. **Transfer entire project** including rendered SVGs to air-gapped environment

The rendered SVGs are committed to the repository so forks and offline users can view diagrams without needing to install D2.

## GitHub Action

The `.github/workflows/render-diagrams.yml` workflow automatically re-renders diagrams when `.d2` files are modified. This keeps rendered outputs in sync with source files.

To disable auto-rendering (for offline-first workflows), simply don't push the workflow file.

## Accessibility

All diagrams include descriptive alt text in the README. When exporting:
- Use descriptive filenames
- Ensure SVG exports include title/desc elements
- Test with screen readers when possible

## Design Principles

- **Sovereignty-aligned**: Self-hosted rendering, no external dependencies
- **Culturally appropriate**: Clean, professional without corporate aesthetics
- **Offline-compatible**: All tools work without internet access
- **Git-friendly**: Text-based sources are diffable and reviewable

