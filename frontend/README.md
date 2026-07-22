# GoFit frontend

移动端优先的 React/Vite Demo，实现“模拟抖音 → 视频动作卡 → 练单 → 训练 → 体感 → 练友经验／安全分流 → 完成总结”主流程。

## 启动

先在一个终端启动业务后端：

```powershell
cd backend/business
python -m venv .venv
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

再在另一个终端启动前端：

```bash
cd frontend
pnpm install
pnpm dev
```

打开 `http://localhost:5173`。页面右上角显示“业务后端已连接”即表示联调环境正常。
Vite 会将 `/api/v1` 代理到 `http://127.0.0.1:8000`；分开部署时可以通过
`VITE_BUSINESS_API_URL` 指定完整地址，示例见 `.env.example`。

## 验证

```bash
pnpm typecheck
pnpm test
pnpm build
```

## 数据

- `src/mocks/lateral-raise.json` 是 `backend/ai/fixtures/lateral_raise/expected-output.json` 的前端契约副本。
- `src/domain.ts` 使用 Zod 校验 AI 返回的完整字段。
- `src/business-api.ts` 负责 Business API 请求和业务模型到前端领域模型的适配。
- 动作卡、收藏、练单、推荐、训练反馈、练友经验和“我的”统计均优先使用业务后端。
- 后端不可用时保留 IndexedDB 和 mock 数据作为明确的演示降级路径。
- 页面右上角连接状态可以用于重试后端水合。

## 联调入口

- Business API 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/v1/health`
- 前端：`http://127.0.0.1:5173`
