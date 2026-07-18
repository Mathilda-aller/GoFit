# GoFit

GoFit 是一个黑客松 MVP 项目，目标是把健身视频整理成可以直接执行的动作卡，
再将动作卡组织成练单，并记录用户的训练反馈。

当前仓库以本地可运行和职责清晰为目标，不考虑正式上线所需的用户规模、账号体系、
高并发和多区域部署。

## 仓库结构

```text
frontend/          前端应用和演示素材
backend/
  business/        业务中心：业务 API、业务规则和数据持久化
  ai/              AI 中心：视频解析、动作卡和推荐能力
database/          数据库说明和种子数据
storage/           MVP 使用的本地媒体文件
docs/              产品、接口和架构文档
```

## MVP 约定

- 不做登录系统，演示阶段使用一个本地演示用户。
- 默认使用 SQLite，后续如果需要再替换为 PostgreSQL。
- 媒体文件放在本地 `storage/`，不引入 MinIO 或云对象存储。
- AI 处理只保留调用边界，具体实现由 AI 负责同学补充。
- 第一版不引入 Redis、Celery、Kubernetes、限流和生产级监控。

## 启动业务中心

```text
cd backend/business
python -m venv .venv
.venv\\Scripts\\activate
pip install -e .
uvicorn app.main:app --reload
```

健康检查接口地址：`http://127.0.0.1:8000/api/v1/health`。

## 启动前端 Demo

```text
cd frontend
python -m http.server 5173
```

打开 `http://127.0.0.1:5173`，可以体验“模拟抖音 → AI 解析 → 动作卡 → 练单 → 训练反馈”的完整 P0 主流程。

前端 Demo 当前使用浏览器内 mock 数据，不需要安装 Node 依赖，也不需要先启动后端。
