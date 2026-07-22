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
- 原始视频统一放在本地 `storage/videos/`，由业务后端提供媒体 URL，并把同一文件的绝对路径提交给 AI 中心；不引入 MinIO 或云对象存储。
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

## 启动前端联调

保持业务中心运行，再打开一个终端：

```text
cd frontend
pnpm install
pnpm dev
```

Vite 默认把 `/api/v1` 代理到业务中心的 `8000` 端口。进入
`http://127.0.0.1:5173` 后，右上角显示“业务后端已连接”即可继续联调。
