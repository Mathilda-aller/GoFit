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
        ("video_lateral_raise", "侧平举总是手臂酸？新手先记住这 3 点",
         "阿哲的训练课", "https://example.test/videos/lateral-raise"),
        ("video_front_raise", "前平举：身体别跟着重量后仰",
         "阿元练肩", "https://example.test/videos/front-raise"),
        ("video_reverse_fly", "反向飞鸟：别让斜方肌抢活",
         "小贺的训练笔记", "https://example.test/videos/reverse-fly"),
        ("video_shoulder_press", "坐姿推肩：新手先把躯干稳定住",
         "GoFit Demo Coach", "https://example.test/videos/shoulder-press"),
        ("video_face_pull", "绳索面拉：拉向眉眼，不是拉向胸口",
         "训练家101", "https://example.test/videos/face-pull"),
        ("video_lat_pulldown", "高位下拉：新手找到背部发力的 3 个提示",
         "背部训练笔记", "https://example.test/videos/lat-pulldown"),
        ("video_seated_row", "坐姿划船：别把身体变成钟摆",
         "背练研究所", "https://example.test/videos/seated-row"),
        ("video_one_arm_row", "单臂哑铃划船：髋和肩别跟着翻",
         "力量新手村", "https://example.test/videos/one-arm-row"),
        ("video_chest_supported_row", "胸托划船：不借腰也能练到上背",
         "稳稳练背", "https://example.test/videos/chest-supported-row"),
        ("video_straight_arm_pulldown", "直臂下压：保持手肘角度",
         "背阔肌说明书", "https://example.test/videos/straight-arm-pulldown"),
        ("video_lat_pulldown_elbow", "高位下拉：肘部向裤兜走",
         "背练研究所", "https://example.test/videos/lat-pulldown-elbow"),
        ("video_lat_pulldown_light", "高位下拉先别急着加重量",
         "力量新手村", "https://example.test/videos/lat-pulldown-light"),
        ("video_lateral_raise_light", "侧平举总是手臂酸？先把重量降下来",
         "肩部训练笔记", "https://example.test/videos/lateral-raise-light"),
        ("video_lateral_raise_elbow", "侧平举不要用手腕提，用手肘打开",
         "训练家101", "https://example.test/videos/lateral-raise-elbow"),
        ("video_lateral_raise_shrug", "侧平举耸肩怎么办：幅度和肩胛控制",
         "阿哲的训练课", "https://example.test/videos/lateral-raise-shrug"),
    ]
    await db.executemany(
        "INSERT INTO source_videos (id, title, creator_name, source_url) "
        "VALUES (?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "title = excluded.title, creator_name = excluded.creator_name, source_url = excluded.source_url",
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
        ("exercise_shoulder_press", "坐姿哑铃推肩", "肩部",
         json.dumps(["三角肌前束", "三角肌中束"]), json.dumps(["肱三头肌"]), json.dumps(["哑铃", "训练凳"])),
        ("exercise_face_pull", "绳索面拉", "肩部",
         json.dumps(["三角肌后束"]), json.dumps(["冈下肌", "斜方肌中部"]), json.dumps(["龙门架", "绳索把手"])),
        ("exercise_lat_pulldown", "高位下拉", "背部",
         json.dumps(["背阔肌"]), json.dumps(["肱二头肌"]), json.dumps(["高位下拉器"])),
        ("exercise_seated_row", "坐姿绳索划船", "背部",
         json.dumps(["背阔肌", "菱形肌"]), json.dumps(["斜方肌中部", "肱二头肌"]), json.dumps(["坐姿划船器"])),
        ("exercise_one_arm_row", "单臂哑铃划船", "背部",
         json.dumps(["背阔肌"]), json.dumps(["菱形肌", "肱二头肌"]), json.dumps(["哑铃", "训练凳"])),
        ("exercise_chest_supported_row", "上斜凳俯卧划船", "背部",
         json.dumps(["菱形肌", "斜方肌中部"]), json.dumps(["背阔肌", "三角肌后束"]), json.dumps(["哑铃", "上斜训练凳"])),
        ("exercise_straight_arm_pulldown", "直臂下压", "背部",
         json.dumps(["背阔肌"]), json.dumps(["大圆肌", "肱三头肌长头"]), json.dumps(["龙门架", "直杆"])),
    ]
    await db.executemany(
        "INSERT INTO standard_exercises "
        "(id, name, body_region, primary_muscles, secondary_muscles, equipment) "
        "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "name = excluded.name, body_region = excluded.body_region, primary_muscles = excluded.primary_muscles, "
        "secondary_muscles = excluded.secondary_muscles, equipment = excluded.equipment",
        exercises,
    )

    # --- Video action cards ---
    cards_data = [
        {
            "id": "video_lateral_raise_demo",
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
            "id": "video_front_raise_demo",
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
            "id": "video_reverse_fly_demo",
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
            "id": "video_lat_pulldown_demo",
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
        {
            "id": "video_shoulder_press_demo", "video_id": "video_shoulder_press",
            "exercise_id": "exercise_shoulder_press", "action_name": "坐姿哑铃推肩", "body_region": "肩部",
            "primary_muscles": ["三角肌前束", "三角肌中束"], "secondary_muscles": ["肱三头肌"],
            "equipment": ["哑铃", "训练凳"],
            "card_data": {"cue": "背贴稳 → 向上推 → 稳稳落", "steps": [["调整靠背，双脚踩稳", "00:06"], ["沿舒适路径向上推起", "00:17"], ["缓慢回落到起始位置", "00:29"]], "tip": "腰背保持稳定，肘部不要锁死"},
        },
        {
            "id": "video_face_pull_demo", "video_id": "video_face_pull",
            "exercise_id": "exercise_face_pull", "action_name": "绳索面拉", "body_region": "肩部",
            "primary_muscles": ["三角肌后束"], "secondary_muscles": ["冈下肌", "斜方肌中部"],
            "equipment": ["龙门架", "绳索把手"],
            "card_data": {"cue": "肩胛稳 → 拉向脸 → 外旋停", "steps": [["绳索调到面部高度", "00:07"], ["肘部向外拉开", "00:18"], ["绳端来到脸两侧后缓慢还原", "00:31"]], "tip": "不要把绳索拉向胸口做成普通划船"},
        },
        {
            "id": "video_seated_row_demo", "video_id": "video_seated_row",
            "exercise_id": "exercise_seated_row", "action_name": "坐姿绳索划船", "body_region": "背部",
            "primary_muscles": ["背阔肌", "菱形肌"], "secondary_muscles": ["斜方肌中部", "肱二头肌"],
            "equipment": ["坐姿划船器"],
            "card_data": {"cue": "坐稳 → 肘向后 → 肩胛合", "steps": [["双脚踩稳，躯干保持直立", "00:06"], ["手肘贴身向后移动", "00:17"], ["控制手臂向前伸", "00:29"]], "tip": "不要用躯干前后摆动制造惯性"},
        },
        {
            "id": "video_one_arm_row_demo", "video_id": "video_one_arm_row",
            "exercise_id": "exercise_one_arm_row", "action_name": "单臂哑铃划船", "body_region": "背部",
            "primary_muscles": ["背阔肌"], "secondary_muscles": ["菱形肌", "肱二头肌"],
            "equipment": ["哑铃", "训练凳"],
            "card_data": {"cue": "躯干稳 → 肘向髋 → 慢慢放", "steps": [["一手一膝稳定支撑", "00:05"], ["工作侧手肘朝髋部后拉", "00:16"], ["控制哑铃下放", "00:28"]], "tip": "骨盆和肩膀保持朝向地面"},
        },
        {
            "id": "video_chest_supported_row_demo", "video_id": "video_chest_supported_row",
            "exercise_id": "exercise_chest_supported_row", "action_name": "上斜凳俯卧划船", "body_region": "背部",
            "primary_muscles": ["菱形肌", "斜方肌中部"], "secondary_muscles": ["背阔肌", "三角肌后束"],
            "equipment": ["哑铃", "上斜训练凳"],
            "card_data": {"cue": "胸贴凳 → 肘向后 → 顶端停", "steps": [["胸口稳定贴住靠垫", "00:05"], ["手肘沿舒适角度向后拉", "00:16"], ["顶端停顿后缓慢伸臂", "00:27"]], "tip": "胸口不要离开靠垫，颈部保持自然"},
        },
        {
            "id": "video_straight_arm_pulldown_demo", "video_id": "video_straight_arm_pulldown",
            "exercise_id": "exercise_straight_arm_pulldown", "action_name": "直臂下压", "body_region": "背部",
            "primary_muscles": ["背阔肌"], "secondary_muscles": ["大圆肌", "肱三头肌长头"],
            "equipment": ["龙门架", "直杆"],
            "card_data": {"cue": "髋后坐 → 直臂压 → 背阔收", "steps": [["面对龙门架稳定站立", "00:06"], ["固定手肘角度压向大腿", "00:18"], ["控制横杆回到前上方", "00:30"]], "tip": "动作来自肩关节，不要反复弯曲手肘"},
        },
    ]

    demo_media = {
        "video_lateral_raise_demo": ("01-lateral-raise", "action_lateral_raise"),
        "video_shoulder_press_demo": ("02-shoulder-press", "action_shoulder_press"),
        "video_reverse_fly_demo": ("03-reverse-fly", "action_reverse_fly"),
        "video_front_raise_demo": ("04-front-raise", "action_front_raise"),
        "video_face_pull_demo": ("05-face-pull", "action_face_pull"),
        "video_lat_pulldown_demo": ("06-lat-pulldown", "action_lat_pulldown"),
        "video_seated_row_demo": ("07-seated-cable-row", "action_seated_cable_row"),
        "video_one_arm_row_demo": ("08-one-arm-dumbbell-row", "action_one_arm_dumbbell_row"),
        "video_chest_supported_row_demo": ("09-chest-supported-row", "action_chest_supported_row"),
        "video_straight_arm_pulldown_demo": ("10-straight-arm-pulldown", "action_straight_arm_pulldown"),
    }

    for card in cards_data:
        slug, action_id = demo_media[card["id"]]
        correct_file = f"{slug}--correct-01.mp4"
        error_file = f"{slug}--error-01.mp4"
        card["card_data"].update({
            "contentSource": "SEED_DEMO",
            "sourceMediaUrl": f"/api/v1/media/videos/{slug}.mp4",
            "curatedMedia": {
                "correctDemo": {
                    "candidateId": f"{action_id}_correct_01",
                    "mediaUrl": f"/api/v1/media/curated/{slug}/correct/{correct_file}",
                },
                "errorDemos": [] if slug == "09-chest-supported-row" else [{
                    "candidateId": f"{action_id}_error_01",
                    "mediaUrl": f"/api/v1/media/curated/{slug}/error/{error_file}",
                }],
            },
        })
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
        await db.execute(
            """
            UPDATE video_action_cards
            SET card_data = json_set(
                card_data,
                '$.contentSource', json_extract(?, '$.contentSource'),
                '$.sourceMediaUrl', json_extract(?, '$.sourceMediaUrl'),
                '$.curatedMedia', json_extract(?, '$.curatedMedia')
            )
            WHERE id = ? AND json_extract(card_data, '$.aiResult') IS NULL
            """,
            (
                json.dumps(card["card_data"], ensure_ascii=False),
                json.dumps(card["card_data"], ensure_ascii=False),
                json.dumps(card["card_data"], ensure_ascii=False),
                card["id"],
            ),
        )
        # Older plans may still reference legacy card ids such as
        # "front-raise". Keep their text, but attach the same curated source
        # video and clips so existing training sessions remain playable.
        await db.execute(
            """
            UPDATE video_action_cards
            SET card_data = json_set(
                card_data,
                '$.contentSource', json_extract(?, '$.contentSource'),
                '$.sourceMediaUrl', json_extract(?, '$.sourceMediaUrl'),
                '$.curatedMedia', json_extract(?, '$.curatedMedia')
            )
            WHERE video_id = ?
              AND id != ?
              AND json_extract(card_data, '$.aiResult') IS NULL
            """,
            (
                json.dumps(card["card_data"], ensure_ascii=False),
                json.dumps(card["card_data"], ensure_ascii=False),
                json.dumps(card["card_data"], ensure_ascii=False),
                card["video_id"],
                card["id"],
            ),
        )

    # --- Preset plan: shoulder + back demo ---
    await db.execute(
        "INSERT OR IGNORE INTO training_plans "
        "(id, user_id, name, status, use_count) VALUES (?, ?, ?, ?, ?)",
        ("plan_shoulder_back_demo", "demo_user_001", "肩背训练", "SAVED", 2),
    )
    plan_items = [
        ("plan_item_shoulder_back_1", "plan_shoulder_back_demo", "video_shoulder_press_demo", 0),
        ("plan_item_shoulder_back_2", "plan_shoulder_back_demo", "video_lateral_raise_demo", 1),
        ("plan_item_shoulder_back_3", "plan_shoulder_back_demo", "video_reverse_fly_demo", 2),
        ("plan_item_shoulder_back_4", "plan_shoulder_back_demo", "video_lat_pulldown_demo", 3),
        ("plan_item_shoulder_back_5", "plan_shoulder_back_demo", "video_seated_row_demo", 4),
        ("plan_item_shoulder_back_6", "plan_shoulder_back_demo", "video_straight_arm_pulldown_demo", 5),
    ]
    await db.executemany(
        "INSERT OR IGNORE INTO training_plan_items "
        "(id, plan_id, card_id, sort_order) VALUES (?, ?, ?, ?)", plan_items,
    )

    # --- Peer experience clusters for 哑铃侧平举 ---
    clusters = [
        ("cluster_arms_felt_more_1", "exercise_lateral_raise", "ARMS_FELT_MORE",
         "先减轻重量，再用手肘带动",
         "重量过大时手臂和斜方肌更容易抢力；先减重，再想象手肘向两侧打开。",
         21, 3, json.dumps(["c1", "c2", "c3", "c4"]), 1),
        ("cluster_front_raise", "exercise_front_raise", "ARMS_FELT_MORE", "收紧核心并降低重量",
         "先消除身体摆动，再考虑次数和重量。", 11, 1, json.dumps(["c_front_1", "c_front_2"]), 1),
        ("cluster_reverse_fly", "exercise_reverse_fly", "ARMS_FELT_MORE", "把动作做小，手肘向外",
         "用小幅度、慢速度和放松手腕寻找后肩发力。", 16, 1, json.dumps(["c_reverse_1", "c_reverse_2"]), 1),
        ("cluster_shoulder_press", "exercise_shoulder_press", "ARMS_FELT_MORE", "先稳定躯干和前臂",
         "固定靠背、脚位和前臂角度后再逐步增加重量。", 14, 1, json.dumps(["c_press_1", "c_press_2"]), 1),
        ("cluster_face_pull", "exercise_face_pull", "ARMS_FELT_MORE", "调高绳索并把肘向外打开",
         "绳索高度和拉向脸部的路径，是找到后肩的关键。", 13, 1, json.dumps(["c_face_1", "c_face_2"]), 1),
        ("cluster_lat_pulldown", "exercise_lat_pulldown", "ARMS_FELT_MORE", "先沉肩，再让手肘向下",
         "先减重、完成肩胛下沉，再把注意力放在手肘路径上。", 24, 3, json.dumps(["c_lat_1", "c_lat_2", "c_lat_3", "c_lat_4"]), 1),
        ("cluster_seated_row", "exercise_seated_row", "ARMS_FELT_MORE", "固定躯干，让手肘贴身向后",
         "先减少身体摆动，再用手肘向后带动把手。", 17, 1, json.dumps(["c_seated_1", "c_seated_2"]), 1),
        ("cluster_one_arm_row", "exercise_one_arm_row", "ARMS_FELT_MORE", "固定躯干，手肘拉向髋部",
         "稳住骨盆和肩线，再寻找手肘靠近髋部的路径。", 15, 1, json.dumps(["c_one_arm_1", "c_one_arm_2"]), 1),
        ("cluster_chest_row", "exercise_chest_supported_row", "ARMS_FELT_MORE", "放松握力并在顶端停顿",
         "在胸托稳定的前提下减少死握，感受肩胛靠拢。", 12, 1, json.dumps(["c_chest_1", "c_chest_2"]), 1),
        ("cluster_straight_arm", "exercise_straight_arm_pulldown", "ARMS_FELT_MORE", "锁定手肘角度，用腋窝向下夹",
         "固定手肘并想象腋窝向下夹，减少手臂主导。", 18, 1, json.dumps(["c_straight_1", "c_straight_2"]), 1),
    ]
    await db.executemany(
        "INSERT INTO peer_experience_clusters "
        "(id, exercise_id, problem_tag, method_name, summary, "
        "mention_count, source_video_count, comment_ids, has_disagreement) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "exercise_id = excluded.exercise_id, problem_tag = excluded.problem_tag, method_name = excluded.method_name, "
        "summary = excluded.summary, mention_count = excluded.mention_count, "
        "source_video_count = excluded.source_video_count, comment_ids = excluded.comment_ids, "
        "has_disagreement = excluded.has_disagreement",
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
        ("c4", "cluster_arms_felt_more_1", "video_lateral_raise_elbow", "肩中束打卡",
         "想手肘往两边推开，不要想着手腕把哑铃拎起来。",
         "https://example.test/comments/c4"),
        ("c_front_1", "cluster_front_raise", "video_front_raise", "肩前束日记", "重量轻一点、肚子收紧以后，腰不再跟着晃。", "https://example.test/comments/c-front-1"),
        ("c_front_2", "cluster_front_raise", "video_front_raise", "动作先做稳", "抬到肩高就够了，再高我就会不自觉后仰。", "https://example.test/comments/c-front-2"),
        ("c_reverse_1", "cluster_reverse_fly", "video_reverse_fly", "后束补课", "幅度做小以后，终于不是斜方肌先酸了。", "https://example.test/comments/c-reverse-1"),
        ("c_reverse_2", "cluster_reverse_fly", "video_reverse_fly", "不甩哑铃", "手肘往外走、手腕放松这个提示特别有用。", "https://example.test/comments/c-reverse-2"),
        ("c_press_1", "cluster_shoulder_press", "video_shoulder_press", "训练打卡员", "把靠背调好、脚踩稳以后，推的时候不再一直晃。", "https://example.test/comments/c-press-1"),
        ("c_press_2", "cluster_shoulder_press", "video_shoulder_press", "慢慢加重量", "重量降一档，前臂保持竖直后肩膀参与感更清楚。", "https://example.test/comments/c-press-2"),
        ("c_face_1", "cluster_face_pull", "video_face_pull", "后肩加餐", "绳索调到眼睛高度后，动作终于不像划船了。", "https://example.test/comments/c-face-1"),
        ("c_face_2", "cluster_face_pull", "video_face_pull", "圆肩自救中", "重量轻一点，拉到脸旁停一下，后肩感觉更明显。", "https://example.test/comments/c-face-2"),
        ("c_lat_1", "cluster_lat_pulldown", "video_lat_pulldown", "背阔肌寻路", "先沉肩再拉之后，二头肌没有以前那么快酸了。", "https://example.test/comments/c-lat-1"),
        ("c_lat_2", "cluster_lat_pulldown", "video_lat_pulldown", "下拉学习中", "想象肘往裤兜走，比想着把杆拉下来更容易找到背。", "https://example.test/comments/c-lat-2"),
        ("c_lat_3", "cluster_lat_pulldown", "video_lat_pulldown_elbow", "背训第一月", "不想着拉杆，只想着肘向下，二头没那么抢了。", "https://example.test/comments/c-lat-3"),
        ("c_lat_4", "cluster_lat_pulldown", "video_lat_pulldown_light", "新手练背", "减重后先沉肩，背阔肌的拉伸感明显很多。", "https://example.test/comments/c-lat-4"),
        ("c_seated_1", "cluster_seated_row", "video_seated_row", "划船不摇摆", "重量降下来不再前后晃，背中间反而更有感觉。", "https://example.test/comments/c-seated-1"),
        ("c_seated_2", "cluster_seated_row", "video_seated_row", "背日记录", "手肘贴着身体往后走，比用手拉把手好理解。", "https://example.test/comments/c-seated-2"),
        ("c_one_arm_1", "cluster_one_arm_row", "video_one_arm_row", "左背补课", "不再转身体以后，背阔肌感觉更连续。", "https://example.test/comments/c-one-arm-1"),
        ("c_one_arm_2", "cluster_one_arm_row", "video_one_arm_row", "单臂划船打卡", "肘往裤兜拉这个提示，比单纯往上提好用。", "https://example.test/comments/c-one-arm-2"),
        ("c_chest_1", "cluster_chest_row", "video_chest_supported_row", "上背训练日", "胸口一直贴着凳子，终于不会靠腰甩重量。", "https://example.test/comments/c-chest-1"),
        ("c_chest_2", "cluster_chest_row", "video_chest_supported_row", "握力别太紧", "手像钩子一样挂住，顶端停一下，上背感觉更清楚。", "https://example.test/comments/c-chest-2"),
        ("c_straight_1", "cluster_straight_arm", "video_straight_arm_pulldown", "背阔肌上线", "手肘不再反复弯以后，动作终于不是三头下压了。", "https://example.test/comments/c-straight-1"),
        ("c_straight_2", "cluster_straight_arm", "video_straight_arm_pulldown", "直臂练习生", "想象腋窝夹住东西往下压，背两侧更容易发力。", "https://example.test/comments/c-straight-2"),
    ]
    await db.executemany(
        "INSERT INTO peer_experience_comments "
        "(id, cluster_id, source_video_id, author_name, content, source_url) "
        "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
        "cluster_id = excluded.cluster_id, source_video_id = excluded.source_video_id, "
        "author_name = excluded.author_name, content = excluded.content, source_url = excluded.source_url",
        comments,
    )

    await db.commit()
