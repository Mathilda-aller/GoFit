# 数据库

黑客松 MVP 默认使用本地 SQLite 数据库。数据库访问仍然应该经过 Repository 层，
这样以后切换到 PostgreSQL 时，不需要修改 API 和业务模型。

计划中的数据区域：

```text
demo_users
source_videos
processing_tasks
standard_exercises
video_action_cards
training_plans
training_plan_items
training_sessions
training_session_items
training_feedback
peer_experience_clusters
recommendation_events
```

第一个功能模块开始实现后，再补充数据库迁移和固定演示种子数据。
