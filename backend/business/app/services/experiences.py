"""Peer experience response shaping."""

from __future__ import annotations

import json

import aiosqlite

from app.repositories import business as repo

PROBLEM_TITLES = {
    "NO_TARGET_FEELING": "目标肌群无感",
    "TOO_DIFFICULT": "动作有点吃力",
    "DISCOMFORT": "出现不适",
}


def problem_title(problem_tag: str, exercise: dict | None) -> str:
    if problem_tag != "ARMS_FELT_MORE":
        return PROBLEM_TITLES.get(problem_tag, "相关练友经验")
    muscles = json.loads(exercise["primary_muscles"]) if exercise else []
    target = muscles[0] if muscles else "目标部位"
    return f"手臂比{target}更有感觉？"


async def experience_for(
    db: aiosqlite.Connection,
    exercise_id: str,
    problem_tag: str,
) -> dict:
    exercise, groups = await repo.list_experience_groups(db, exercise_id, problem_tag)
    exercise_name = exercise["name"] if exercise else exercise_id
    response_groups = []
    comment_count = 0
    source_video_count = 0
    safety = problem_tag == "DISCOMFORT"
    for group in groups:
        comment_count += int(group["mention_count"])
        source_video_count = max(source_video_count, int(group["source_video_count"]))
        safety = safety or group["risk_type"] != "NORMAL"
        comments = [
            {
                "id": comment["id"],
                "content": comment["content"],
                "author_name": comment["author_name"],
                "source_url": comment["source_url"],
                "source_video": {
                    "id": comment["source_video_id"],
                    "title": comment["video_title"],
                    "creator_name": comment["video_creator_name"],
                    "source_url": comment["video_source_url"],
                    "cover_url": comment["video_cover_url"],
                },
            }
            for comment in group["comments"]
        ]
        response_groups.append(
            {
                "id": group["id"],
                "method_name": group["method_name"],
                "summary": group["summary"],
                "mention_count": group["mention_count"],
                "source_video_count": group["source_video_count"],
                "has_disagreement": bool(group["has_disagreement"]),
                "risk_type": group["risk_type"],
                "comments": comments,
            }
        )
    return {
        "exercise_id": exercise_id,
        "exercise_name": exercise_name,
        "problem_tag": problem_tag,
        "problem_title": problem_title(problem_tag, exercise),
        "comment_count": comment_count,
        "source_video_count": source_video_count,
        "source_note": f"AI 整理自 {source_video_count} 条{exercise_name}视频下的 {comment_count} 条公开评论",
        "safety_triggered": safety,
        "groups": response_groups,
    }
