# 业务中心

业务中心负责 MVP 的业务 API 和持久化数据。

## 负责内容

- 演示用户上下文和权限
- 来源视频和处理任务状态
- 视频动作卡与标准动作的关联
- 收藏和练单
- 训练会话、训练进度和体感反馈
- 不适安全记录
- 推荐请求和推荐结果记录
- 练友经验查询结果

## 开发约定

随着代码增加，HTTP 层、业务规则和数据持久化要保持分层。不要把 AI Prompt 或模型
相关逻辑写进业务中心。

当前已经实现 P0 Demo 所需的基础业务接口：

- 来源视频导入和处理状态查询
- 视频动作卡列表、详情和收藏状态
- 练单创建、重命名、排序、添加动作和删除动作
- 从练单复制创建本次训练
- 训练进度、五类体感反馈和不适分流标记
- 练单推荐候选，AI 不在线时有本地降级
- 练友经验摘要、原评论依据和来源视频
- Demo 用户的“我的”摘要

## 启动

```powershell
cd backend/business
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m uvicorn app.main:app --reload
```

接口地址统一使用 `/api/v1` 前缀，完整清单见 `../../docs/technical/api.md`。
