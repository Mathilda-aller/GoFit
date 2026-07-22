from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest


_temp_dir = tempfile.TemporaryDirectory()
os.environ["GOFIT_DATABASE_URL"] = f"sqlite:///{Path(_temp_dir.name) / 'business-test.db'}"
os.environ["GOFIT_STORAGE_DIR"] = str(Path(_temp_dir.name) / "storage")
(Path(_temp_dir.name) / "storage" / "videos").mkdir(parents=True)
(Path(_temp_dir.name) / "storage" / "videos" / "01-lateral-raise.mp4").write_bytes(b"demo-video")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


class BusinessApiFlowTest(unittest.TestCase):
    def test_frontend_integration_flow(self) -> None:
        with TestClient(app) as client:
            health = client.get("/api/v1/health")
            self.assertEqual(health.status_code, 200)

            cards = client.get("/api/v1/action-cards").json()["items"]
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
                json={"videoId": "video_lateral_raise"},
            ).json()
            self.assertEqual(imported["status"], "COMPLETED")
            self.assertEqual(imported["cardId"], "video_lateral_raise_demo")

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


if __name__ == "__main__":
    unittest.main()
