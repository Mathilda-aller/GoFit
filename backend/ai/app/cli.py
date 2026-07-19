from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pydantic import ValidationError

from app.errors import SkillError, contract_validation_error, request_id_from_body
from app.models.action_card import ActionCardBuildRequest
from app.providers.fake import FixedFixtureActionCardGenerator
from app.skills.fitness_video_to_action_card import FitnessVideoToActionCardSkill


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GoFit AI command line")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser(
        "build-action-card",
        help="Build one action card from aligned evidence JSON.",
    )
    build.add_argument("--input", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        request = ActionCardBuildRequest.model_validate(raw)
        skill = FitnessVideoToActionCardSkill(FixedFixtureActionCardGenerator())
        result = skill.execute(request)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                result.model_dump(by_alias=True, mode="json"),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return 0
    except ValidationError as exc:
        error = contract_validation_error(
            exc,
            request_id=request_id_from_body(locals().get("raw")),
        )
    except SkillError as exc:
        error = exc
    except (OSError, json.JSONDecodeError):
        error = SkillError(
            "OUTPUT_VALIDATION_FAILED",
            "无法读取输入文件或输入不是有效 JSON。",
        )

    print(
        json.dumps(error.as_response(), ensure_ascii=False),
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

