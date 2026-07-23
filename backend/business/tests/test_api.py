from __future__ import annotations

import os
import json
import sqlite3
from pathlib import Path
import tempfile
import unittest


_temp_dir = tempfile.TemporaryDirectory()
_db_path = Path(_temp_dir.name) / "business-test.db"
os.environ["GOFIT_DATABASE_URL"] = f"sqlite:///{_db_path}"
os.environ["GOFIT_STORAGE_DIR"] = str(Path(_temp_dir.name) / "storage")
os.environ["GOFIT_AI_CENTER_URL"] = "http://127.0.0.1:1"
(Path(_temp_dir.name) / "storage" / "videos").mkdir(parents=True)
(Path(_temp_dir.name) / "storage" / "videos" / "01-lateral-raise.mp4").write_bytes(b"demo-video")
clip_root = Path(_temp_dir.name) / "storage" / "curated-clips" / "01-lateral-raise"
(clip_root / "correct").mkdir(parents=True)
(clip_root / "error").mkdir(parents=True)
(clip_root / "correct" / "01-lateral-raise--correct-01.mp4").write_bytes(b"correct")
(clip_root / "error" / "01-lateral-raise--error-01.mp4").write_bytes(b"error")
(clip_root / "manifest.json").write_text(json.dumps({
    "schemaVersion": "1.0.0",
    "standardActionId": "action_lateral_raise",
    "actionName": "哑铃侧平举",
    "sourceVideo": {
        "videoId": "video_lateral_raise_demo",
        "file": "storage/videos/01-lateral-raise.mp4",
        "title": "侧平举教学",
        "creatorName": "测试教练",
        "sourceUrl": "https://example.test/lateral-raise",
    },
    "correctClips": [{
        "candidateId": "action_lateral_raise_correct_01",
        "file": "storage/curated-clips/01-lateral-raise/correct/01-lateral-raise--correct-01.mp4",
        "sourceStartMs": 1000,
        "sourceEndMs": 4000,
    }],
    "errorClips": [{
        "candidateId": "action_lateral_raise_error_01",
        "file": "storage/curated-clips/01-lateral-raise/error/01-lateral-raise--error-01.mp4",
        "sourceStartMs": 5000,
        "sourceEndMs": 7000,
    }],
}), encoding="utf-8")

from fastapi.testclient import TestClient  # noqa: E402

from app.api.routes.videos import _media_artifacts  # noqa: E402
from app.main import app  # noqa: E402
from app.services.curated_media import load_manifest_for_video  # noqa: E402


class BusinessApiFlowTest(unittest.TestCase):
    def test_frontend_integration_flow(self) -> None:
        with TestClient(app) as client:
            health = client.get("/api/v1/health")
            self.assertEqual(health.status_code, 200)

            self.assertEqual(client.get("/api/v1/action-cards").json()["items"], [])
            cards = client.get("/api/v1/action-cards", params={"includeDemo": "true"}).json()["items"]
            self.assertEqual(len(cards), 10)
            self.assertEqual({card["bodyRegion"] for card in cards}, {"肩部", "背部"})
            for card in cards:
                experience = client.get(
                    "/api/v1/experiences",
                    params={"exerciseId": card["exerciseId"], "problemTag": "ARMS_FELT_MORE"},
                ).json()
                self.assertGreater(len(experience["groups"]), 0)
                self.assertTrue(experience["problemTitle"].endswith("？"))

            imported = client.post(
                "/api/v1/videos/import",
                json={"videoId": "video_lateral_raise_demo", "assetFileName": "01-lateral-raise.mp4"},
            ).json()
            self.assertEqual(imported["status"], "COMPLETED")
            self.assertTrue(imported["videoId"].startswith("video_"))
            self.assertNotEqual(imported["videoId"], "video_lateral_raise")
            self.assertTrue(imported["cardId"].startswith("mock-video_"))
            self.assertEqual(imported["contentSource"], "MOCK_FALLBACK")

            generated = client.get(f"/api/v1/action-cards/{imported['cardId']}").json()
            self.assertEqual(generated["cardData"]["contentSource"], "MOCK_FALLBACK")
            self.assertIn("/media/curated/", generated["cardData"]["curatedMedia"]["correctDemo"]["mediaUrl"])
            fallback_steps = generated["cardData"]["aiResult"]["actionCard"]["learningSide"]["steps"]
            self.assertEqual(
                len({(step["startMs"], step["endMs"]) for step in fallback_steps}),
                len(fallback_steps),
            )

            ai_data = dict(generated["cardData"])
            ai_data["contentSource"] = "AI"
            db = sqlite3.connect(_db_path)
            try:
                db.execute(
                    """
                    INSERT INTO video_action_cards
                    (id, video_id, exercise_id, action_name, body_region, primary_muscles,
                     secondary_muscles, equipment, card_data, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'READY')
                    """,
                    ("ai-preferred", imported["videoId"], "exercise_lateral_raise", "哑铃侧平举", "肩部", '["三角肌中束"]', '["三角肌前束"]', '["哑铃"]', json.dumps(ai_data, ensure_ascii=False)),
                )
                db.commit()
            finally:
                db.close()
            repeated = client.post(
                "/api/v1/videos/import",
                json={"videoId": "seed-id-is-ignored", "assetFileName": "01-lateral-raise.mp4"},
            ).json()
            self.assertEqual(repeated["cardId"], "ai-preferred")
            self.assertEqual(repeated["contentSource"], "AI")

            media = client.get("/api/v1/media/videos/01-lateral-raise.mp4")
            self.assertEqual(media.status_code, 200)
            self.assertEqual(media.content, b"demo-video")

            plan = client.post(
                "/api/v1/plans",
                json={"name": "联调测试", "initialCardId": "video_lateral_raise_demo"},
            ).json()
            plan = client.post(
                f"/api/v1/plans/{plan['id']}/items",
                json={"cardId": "video_front_raise_demo"},
            ).json()
            self.assertEqual(plan["itemCount"], 2)

            session = client.post(f"/api/v1/plans/{plan['id']}/sessions").json()
            first_item, second_item = session["items"]
            first_feedback = client.post(
                f"/api/v1/sessions/{session['id']}/feedback",
                json={"itemId": first_item["id"], "feedbackType": "TARGET_FELT", "feltMuscles": ["三角肌中束"]},
            ).json()
            self.assertEqual(first_feedback["session"]["currentIndex"], 1)

            final_feedback = client.post(
                f"/api/v1/sessions/{session['id']}/feedback",
                json={"itemId": second_item["id"], "feedbackType": "DISCOMFORT", "feltMuscles": ["肩部"]},
            ).json()
            self.assertTrue(final_feedback["shouldShowSafety"])
            self.assertEqual(final_feedback["session"]["status"], "COMPLETED")

            another_session = client.post(f"/api/v1/plans/{plan['id']}/sessions").json()
            ended = client.post(f"/api/v1/sessions/{another_session['id']}/end").json()
            self.assertEqual(ended["status"], "ENDED")

    def test_media_artifact_paths_are_deployable(self) -> None:
        manifest = load_manifest_for_video("01-lateral-raise.mp4")
        artifacts = _media_artifacts(
            manifest,
            [{
                "candidateId": "action_lateral_raise_correct_01",
                "kind": "CORRECT_DEMO",
                "filePath": r"D:\coding_project\GoFit\storage\curated-clips\legacy.mp4",
            }],
        )
        self.assertEqual(
            artifacts[0]["filePath"],
            "storage/curated-clips/01-lateral-raise/correct/01-lateral-raise--correct-01.mp4",
        )
        self.assertEqual(
            artifacts[0]["mediaUrl"],
            "/api/v1/media/curated/01-lateral-raise/correct/01-lateral-raise--correct-01.mp4",
        )


if __name__ == "__main__":
    unittest.main()
