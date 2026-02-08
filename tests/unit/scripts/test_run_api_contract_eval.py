from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "run_api_contract_eval.py"
CASES_PATH = ROOT / "evals" / "api_contract_cases.json"


def test_run_api_contract_eval_default_cases_pass():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Summary: passed=" in result.stdout
    assert "failed=0" in result.stdout


def test_run_api_contract_eval_reports_failures(tmp_path: Path):
    broken_cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    broken_cases[0]["expect"]["status"] = "completed"

    broken_path = tmp_path / "broken_api_cases.json"
    broken_path.write_text(json.dumps(broken_cases), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--cases", str(broken_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "[FAIL]" in result.stdout
    assert "failed=" in result.stdout
