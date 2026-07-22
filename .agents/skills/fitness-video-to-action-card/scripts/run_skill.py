from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def find_repository_root(start: Path) -> Path:
    for directory in (start, *start.parents):
        if (directory / "backend" / "ai" / "pyproject.toml").is_file():
            return directory
    raise FileNotFoundError("找不到包含 backend/ai/pyproject.toml 的 GoFit 仓库。")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the GoFit FitnessVideoToActionCardSkill."
    )
    parser.add_argument(
        "--mode",
        choices=["aligned-evidence", "raw-video"],
        default="aligned-evidence",
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repository_root = find_repository_root(Path(__file__).resolve())
    ai_root = repository_root / "backend" / "ai"
    input_path = args.input if args.input.is_absolute() else repository_root / args.input
    output_path = args.output if args.output.is_absolute() else repository_root / args.output

    command = (
        "process-video" if args.mode == "raw-video" else "build-action-card"
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.cli",
            command,
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        cwd=ai_root,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
