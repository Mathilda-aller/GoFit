"""Demo seed data matching the fit-front branch frontend cards."""

from __future__ import annotations

import json

import aiosqlite


async def seed_data(db: aiosqlite.Connection) -> None:
    """Insert fixed demo data. Uses INSERT OR IGNORE for idempotency."""

    # --- Demo user ---
    await db.execute(
        "INSERT OR IGNORE INTO demo_users (id, nickname) VALUES (?, ?)",
        ("demo_user_001", "Demo"),
    )

    # --- Source videos ---
    videos = [
        ("video_lateral_raise", "新手肩部训练：侧平举这样做，肩中束更容易找到感觉",
         "阿哲的训练课", "https://example.test/videos/lateral-raise"),
        ("video_front_raise", "肩部前束训练：前平举动作细节",
         "阿哲的训练课", "https://example.test/videos/front-raise"),
        ("video_reverse_fly", "后束肩入门：俯身反向飞鸟",
         "训练家101", "https://example.test/videos/reverse-fly"),
        ("video_lat_pulldown", "高位下拉：新手找到背部发力的三个提示",
         "背部训练笔记", "https://example.test/videos/lat-pulldown"),
        ("video_lateral_raise_light", "侧平举总是手臂酸？先把重量降下来",
         "肩部训练笔记", "https://example.test/videos/lateral-raise-light"),
        ("video_lateral_raise_elbow", "侧平举不要用手腕提，用手肘打开",
         "训练家101", "https://example.test/videos/lateral-raise-elbow"),
        ("video_lateral_raise_shrug", "侧平举耸肩怎么办：幅度和肩胛控制",
         "阿哲的训练课", "https://example.test/videos/lateral-raise-shrug"),
    ]
    await db.executemany(
        "INSERT OR IGNORE INTO source_videos (id, title, creator_name, source_url) "
        "VALUES (?, ?, ?, ?)",
        videos,
    )

    # --- Standard exercises ---
    exercises = [
        ("exercise_lateral_raise", "哑铃侧平举", "肩部",
         json.dumps(["三角肌中束"]), json.dumps(["三角肌前束"]), json.dumps(["哑铃"])),
        ("exercise_front_raise", "哑铃前平举", "肩部",
         json.dumps(["三角肌前束"]), json.dumps(["胸上部"]), json.dumps(["哑铃"])),
        ("exercise_reverse_fly", "俯身反向飞鸟", "肩部",
         json.dumps(["三角肌后束"]), json.dumps(["菱形肌"]), json.dumps(["哑铃"])),
        ("exercise_lat_pulldown", "高位下拉", "背部",
         json.dumps(["背阔肌"]), json.dumps(["肱二头肌"]), json.dumps(["高位下拉器"])),
    ]
    await db.executemany(
        "INSERT OR IGNORE INTO standard_exercises "
        "(id, name, body_region, primary_muscles, secondary_muscles, equipment) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        exercises,
    )

    # --- Video action cards ---
    cards_data = [
        {
            "id": "lateral-raise",
            "video_id": "video_lateral_raise",
            "exercise_id": "exercise_lateral_raise",
            "action_name": "哑铃侧平举",
            "body_region": "肩部",
            "primary_muscles": ["三角肌中束"],
            "secondary_muscles": ["三角肌前束", "斜方肌"],
            "equipment": ["哑铃"],
            "card_data": {
                "creator": "阿哲的训练课",
                "title": "新手肩部训练：侧平举这样做，肩中束更容易找到感觉",
                "source": "来自本视频",
                "cue": "肩放松 → 肘带动 → 缓慢落",
                "steps": [
                    ["站稳，手肘微屈，哑铃贴近身体两侧", "00:08"],
                    ["先想象用手肘向两侧打开，而不是甩起", "00:16"],
                    ["抬到与肩平齐即可，停住一秒", "00:24"],
                    ["控制下放，保持肩膀远离耳朵", "00:31"],
                ],
                "tip": "不要为了抬得更高而耸肩；动作幅度以肩部持续发力为准",
                "experienceCount": 68,
                "videoCount": 4,
            },
        },
        {
            "id": "front-raise",
            "video_id": "video_front_raise",
            "exercise_id": "exercise_front_raise",
            "action_name": "哑铃前平举",
            "body_region": "肩部",
            "primary_muscles": ["三角肌前束"],
            "secondary_muscles": ["胸上部"],
            "equipment": ["哑铃"],
            "card_data": {
                "creator": "阿哲的训练课",
                "title": "肩部前束训练：前平举动作细节",
                "source": "来自本视频",
                "cue": "核心收紧 → 手臂前举 → 控制落下",
                "steps": [
                    ["双脚站稳，哑铃放在大腿前侧", "00:07"],
                    ["手臂向前举至视线下方", "00:19"],
                    ["停住后缓慢还原", "00:28"],
                ],
                "tip": "重量不需要很大，身体不要为了完成次数而后仰",
                "experienceCount": 21,
                "videoCount": 2,
            },
        },
        {
            "id": "reverse-fly",
            "video_id": "video_reverse_fly",
            "exercise_id": "exercise_reverse_fly",
            "action_name": "俯身反向飞鸟",
            "body_region": "肩部",
            "primary_muscles": ["三角肌后束"],
            "secondary_muscles": ["菱形肌"],
            "equipment": ["哑铃"],
            "card_data": {
                "creator": "训练家101",
                "title": "后束肩入门：俯身反向飞鸟",
                "source": "来自本视频",
                "cue": "髋部折叠 → 肘向外开 → 回到起点",
                "steps": [
                    ["髋部折叠，背部保持稳定", "00:11"],
                    ["肘部向外打开，手腕保持放松", "00:22"],
                    ["用控制感完成回落", "00:34"],
                ],
                "tip": "先把动作做小，感受后肩，而不是追求哑铃高度",
                "experienceCount": 32,
                "videoCount": 3,
            },
        },
        {
            "id": "lat-pulldown",
            "video_id": "video_lat_pulldown",
            "exercise_id": "exercise_lat_pulldown",
            "action_name": "高位下拉",
            "body_region": "背部",
            "primary_muscles": ["背阔肌"],
            "secondary_muscles": ["肱二头肌"],
            "equipment": ["高位下拉器"],
            "card_data": {
                "creator": "背部训练笔记",
                "title": "高位下拉：新手找到背部发力的三个提示",
                "source": "来自本视频",
                "cue": "肩胛下沉 → 肘向下 → 慢慢放",
                "steps": [
                    ["坐稳并让肩膀远离耳朵", "00:09"],
                    ["想象肘部向裤兜方向移动", "00:18"],
                    ["不要借身体后仰完成下拉", "00:29"],
                ],
                "tip": "如果手臂先酸，先减轻重量并重新找回肩胛下沉",
                "experienceCount": 45,
                "videoCount": 3,
            },
        },
    ]

    for card in cards_data:
        await db.execute(
            "INSERT OR IGNORE INTO video_action_cards "
            "(id, video_id, exercise_id, action_name, body_region, "
            "primary_muscles, secondary_muscles, equipment, card_data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                card["id"],
                card["video_id"],
                card["exercise_id"],
                card["action_name"],
                card["body_region"],
                json.dumps(card["primary_muscles"]),
                json.dumps(card["secondary_muscles"]),
                json.dumps(card["equipment"]),
                json.dumps(card["card_data"], ensure_ascii=False),
            ),
        )

    # --- Preset plan: "上次练背" ---
    await db.execute(
        "INSERT OR IGNORE INTO training_plans "
        "(id, user_id, name, status, use_count) VALUES (?, ?, ?, ?, ?)",
        ("plan_back_day", "demo_user_001", "上次练背", "SAVED", 2),
    )
    await db.execute(
        "INSERT OR IGNORE INTO training_plan_items "
        "(id, plan_id, card_id, sort_order) VALUES (?, ?, ?, ?)",
        ("plan_item_back_1", "plan_back_day", "lat-pulldown", 0),
    )

    # --- Peer experience clusters for 哑铃侧平举 ---
    clusters = [
        ("cluster_arms_felt_more_1", "exercise_lateral_raise", "ARMS_FELT_MORE",
         "降低重量",
         "先减轻重量，让肩部完成完整轨迹，手臂不需要抢着发力。",
         24, 4, json.dumps(["c1", "c2", "c3"]), 0),
        ("cluster_arms_felt_more_2", "exercise_lateral_raise", "ARMS_FELT_MORE",
         "由手肘带动",
         "想象手肘向两边打开，由手肘带动而不是手腕硬提。",
         18, 3, json.dumps(["c4", "c5", "c6"]), 0),
        ("cluster_arms_felt_more_3", "exercise_lateral_raise", "ARMS_FELT_MORE",
         "不要为了抬高而耸肩",
         "肩膀始终远离耳朵，抬到与肩同高即可。",
         15, 3, json.dumps(["c7", "c8"]), 0),
    ]
    await db.executemany(
        "INSERT OR IGNORE INTO peer_experience_clusters "
        "(id, exercise_id, problem_tag, method_name, summary, "
        "mention_count, source_video_count, comment_ids, has_disagreement) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        clusters,
    )

    comments = [
        ("c1", "cluster_arms_felt_more_1", "video_lateral_raise", "练完才懂",
         "我之前手臂先酸，后来把哑铃重量减半，肩中束反而更容易找到感觉。",
         "https://example.test/comments/c1"),
        ("c2", "cluster_arms_felt_more_1", "video_lateral_raise_light", "小白肩训",
         "重量太大就会靠甩，先用轻重量慢慢抬，手臂抢力少很多。",
         "https://example.test/comments/c2"),
        ("c3", "cluster_arms_felt_more_1", "video_lateral_raise_elbow", "今天练肩",
         "别急着加重量，能控制下放的时候肩部感觉会明显一点。",
         "https://example.test/comments/c3"),
        ("c4", "cluster_arms_felt_more_2", "video_lateral_raise_elbow", "肩中束打卡",
         "想手肘往两边推开，不要想着手腕把哑铃拎起来。",
         "https://example.test/comments/c4"),
        ("c5", "cluster_arms_felt_more_2", "video_lateral_raise", "不想耸肩",
         "我跟着这个提示改成肘带动，手臂酸少了，肩旁边更有感觉。",
         "https://example.test/comments/c5"),
        ("c6", "cluster_arms_felt_more_2", "video_lateral_raise_shrug", "慢慢练",
         "手肘带着走，手腕放松，动作小一点也可以。",
         "https://example.test/comments/c6"),
        ("c7", "cluster_arms_felt_more_3", "video_lateral_raise_shrug", "阿青",
         "我一抬高就耸肩，控制到肩平齐就停，反而更稳。",
         "https://example.test/comments/c7"),
        ("c8", "cluster_arms_felt_more_3", "video_lateral_raise_light", "肩部新手",
         "肩膀离耳朵远一点，不要追求特别高的幅度。",
         "https://example.test/comments/c8"),
    ]
    await db.executemany(
        "INSERT OR IGNORE INTO peer_experience_comments "
        "(id, cluster_id, source_video_id, author_name, content, source_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        comments,
    )

    await db.commit()
