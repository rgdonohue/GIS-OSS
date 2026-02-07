# Copilot Coding Agent Instructions

Follow repository guidance in `AGENTS.md` and scoped `AGENTS.md` files.

Priority order:
1. Security and governance controls
2. Grounding and provenance correctness
3. Backward-compatible API changes
4. Developer ergonomics

Always run and report:
- `ruff check src tests scripts/generate_project_status.py`
- `mypy src`
- `pytest -q`
- `python scripts/generate_project_status.py --check`
