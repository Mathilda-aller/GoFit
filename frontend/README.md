# GoFit frontend

移动端优先的 React/Vite Demo，实现“模拟抖音 → 视频动作卡 → 练单 → 训练 → 体感 → 练友经验／安全分流 → 完成总结”主流程。

## 启动

```bash
pnpm install
pnpm dev
```

打开 `http://localhost:5173`。根路由默认进入模拟抖音页。

## 验证

```bash
pnpm typecheck
pnpm test
pnpm build
```

## 数据

- `src/mocks/lateral-raise.json` 是 `backend/ai/fixtures/lateral_raise/expected-output.json` 的前端契约副本。
- `src/domain.ts` 使用 Zod 校验 AI 返回的完整字段。
- 练单和训练进度通过 Zustand 持久化到 IndexedDB。
- “我的”页面提供开发期 Demo 数据重置入口。

真实业务 API 接入时，页面组件保持不变，只替换 `src/api.ts` 中的 Repository 实现。
