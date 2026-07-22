import json
import subprocess
import sys
from pathlib import Path


def test_repository_skill_script_matches_expected(
    tmp_path,
    expected_payload: dict,
) -> None:
    ai_root = Path(__file__).resolve().parents[1]
    repository_root = ai_root.parents[1]
    script = (
        repository_root
        / ".agents"
        / "skills"
        / "fitness-video-to-action-card"
        / "scripts"
        / "run_skill.py"
    )
    output = tmp_path / "repository-skill-output.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--input",
            "backend/ai/fixtures/lateral_raise/input.json",
            "--output",
            str(output),
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(output.read_text(encoding="utf-8")) == expected_payload
