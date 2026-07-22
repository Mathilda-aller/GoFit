"""Database table definitions for GoFit MVP (SQLite)."""

from __future__ import annotations

TABLES: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS demo_users (
        id TEXT PRIMARY KEY,
        nickname TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS source_videos (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        creator_name TEXT NOT NULL,
        source_url TEXT NOT NULL,
        cover_url TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS processing_tasks (
        id TEXT PRIMARY KEY,
        video_id TEXT NOT NULL REFERENCES source_videos(id),
        status TEXT NOT NULL DEFAULT 'PENDING',
        result_card_id TEXT,
        error_message TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS standard_exercises (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        aliases TEXT NOT NULL DEFAULT '[]',
        body_region TEXT NOT NULL,
        primary_muscles TEXT NOT NULL DEFAULT '[]',
        secondary_muscles TEXT NOT NULL DEFAULT '[]',
        equipment TEXT NOT NULL DEFAULT '[]',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS video_action_cards (
        id TEXT PRIMARY KEY,
        video_id TEXT NOT NULL REFERENCES source_videos(id),
        exercise_id TEXT NOT NULL REFERENCES standard_exercises(id),
        action_name TEXT NOT NULL,
        body_region TEXT NOT NULL,
        primary_muscles TEXT NOT NULL DEFAULT '[]',
        secondary_muscles TEXT NOT NULL DEFAULT '[]',
        equipment TEXT NOT NULL DEFAULT '[]',
        card_data TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'READY',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_saved_cards (
        user_id TEXT NOT NULL REFERENCES demo_users(id),
        card_id TEXT NOT NULL REFERENCES video_action_cards(id),
        saved_at TEXT NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY (user_id, card_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS training_plans (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES demo_users(id),
        name TEXT NOT NULL DEFAULT '未命名练单',
        status TEXT NOT NULL DEFAULT 'DRAFT',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        last_used_at TEXT,
        use_count INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS training_plan_items (
        id TEXT PRIMARY KEY,
        plan_id TEXT NOT NULL REFERENCES training_plans(id) ON DELETE CASCADE,
        card_id TEXT NOT NULL REFERENCES video_action_cards(id),
        sort_order INTEGER NOT NULL,
        added_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(plan_id, card_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS training_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES demo_users(id),
        plan_id TEXT NOT NULL REFERENCES training_plans(id),
        status TEXT NOT NULL DEFAULT 'IN_PROGRESS',
        current_index INTEGER NOT NULL DEFAULT 0,
        started_at TEXT NOT NULL DEFAULT (datetime('now')),
        completed_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS training_session_items (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
        card_id TEXT NOT NULL REFERENCES video_action_cards(id),
        sort_order INTEGER NOT NULL,
        item_status TEXT NOT NULL DEFAULT 'PENDING',
        feedback_type TEXT,
        felt_muscles TEXT,
        feedback_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS peer_experience_clusters (
        id TEXT PRIMARY KEY,
        exercise_id TEXT NOT NULL REFERENCES standard_exercises(id),
        problem_tag TEXT NOT NULL,
        method_name TEXT NOT NULL,
        summary TEXT NOT NULL,
        mention_count INTEGER NOT NULL DEFAULT 0,
        source_video_count INTEGER NOT NULL DEFAULT 0,
        comment_ids TEXT NOT NULL DEFAULT '[]',
        has_disagreement INTEGER NOT NULL DEFAULT 0,
        risk_type TEXT NOT NULL DEFAULT 'NORMAL',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS peer_experience_comments (
        id TEXT PRIMARY KEY,
        cluster_id TEXT NOT NULL REFERENCES peer_experience_clusters(id) ON DELETE CASCADE,
        source_video_id TEXT NOT NULL REFERENCES source_videos(id),
        author_name TEXT NOT NULL,
        content TEXT NOT NULL,
        source_url TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS recommendation_events (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES demo_users(id),
        plan_id TEXT,
        request_data TEXT,
        result_data TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
]
