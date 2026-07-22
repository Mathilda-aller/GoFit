import json

from app.cli import main


def test_cli_matches_expected_fixture(
    tmp_path,
    expected_payload: dict,
) -> None:
    output = tmp_path / "action-card.json"
    exit_code = main(
        [
            "build-action-card",
            "--input",
            "fixtures/lateral_raise/input.json",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert json.loads(output.read_text(encoding="utf-8")) == expected_payload

