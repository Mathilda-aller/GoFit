# 「练过」前端开发方案

> 版本：v1.0
> 日期：2026-07-22
> 状态：开发前基线
> 需求依据：`交互Demo设计说明_练过_v1.0.md`（文内 v2.0）、`PRD_健身视频重构_v0.1.md`（文内 v0.7）
> 适用范围：Hackathon P0 移动端 Web Demo，不包含 P1 动作知识页

如本文件与早期总技术方案中的前端“参考技术栈”冲突，以本文件作为当前前端执行基线；前端只对接业务后端等系统边界仍沿用总技术方案。

## 1. 结论

前端采用 **React 19 + TypeScript + Vite 8 的单页应用（SPA）**，按移动端优先方式实现，并保留 PWA、离线恢复和静态部署能力。

当前项目已有独立 FastAPI 业务后端，页面没有 SEO、服务端渲染或前端 BFF 的硬需求，因此 P0 不使用 Next.js。Vite SPA 的工程边界更简单，适合两名前端并行开发、Mock 数据先行和后续替换真实 API。

前端只连接业务后端 `/api/v1`，不直接调用 AI 服务、数据库或模型供应商。

```text
React SPA / PWA
  ├─ 页面、业务组件、交互状态
  ├─ Mock API（开发和稳定演示）
  ├─ HTTP Repository（真实联调）
  └─ IndexedDB（训练恢复、待同步操作）
             │ REST / JSON
             ▼
       FastAPI 业务中心
             │
             ▼
       AI 中心与本地媒体
```

## 2. P0 开发边界

### 必须完成

- P00—P11 的主页面与交互，P07 作为训练页内底部面板；
- 视频接入状态、视频动作卡完整步骤／训练速记；
- 练单的新建、命名、添加、删除、排序、自动保存和再次使用；
- 从练单复制出独立训练会话，支持完成、跳过、退出和恢复；
- 五类体感、其他部位二次选择、练友经验分支和不适安全分流；
- 单动作／整份练单的肌群展示；
- 集中 Mock 数据与真实 API 的无感切换；
- 360px 宽度、手机安全区、刷新恢复、弱网提示和关键异常状态。

### 本轮不做

- P1 独立动作知识页；
- 登录注册、复杂权限和多用户切换；
- 任意视频上传、摄像头动作识别、3D 人体；
- 重型社区信息流、排行榜、训练处方；
- 前端直连 AI 或在浏览器中执行视频分析。

## 3. 技术栈

版本基线以 2026-07 的稳定版为准，安装后由 lockfile 固定具体补丁版本。

| 领域 | 选型 | 用途与约束 |
| --- | --- | --- |
| 运行时 | Node.js LTS + pnpm | 根目录固定 `packageManager` 与 `engines` |
| UI | React 19.2 + TypeScript | 开启严格类型，不引入实验性 React API |
| 构建 | Vite 8.1 | SPA 构建、开发代理、按路由拆包 |
| 路由 | React Router 7（Data Mode） | 页面路由、参数、返回来源和路由级懒加载 |
| 样式 | Tailwind CSS 4.3 + CSS Variables | Token 统一管理颜色、间距、圆角、阴影和安全区 |
| 无障碍原语 | Radix UI | Dialog、Tabs、Popover 等复杂交互的键盘和焦点基础 |
| 服务端状态 | TanStack Query 5 | 请求缓存、mutation、失效刷新和联调切换 |
| 客户端状态 | Zustand 5 | 只保存跨组件的临时交互状态，不复制完整服务端对象 |
| 数据校验 | Zod | 在 Mock 和真实 HTTP 边界校验 DTO |
| 本地持久化 | IndexedDB + `idb` | 活动训练快照、待同步写操作和 Demo 数据版本 |
| Mock | MSW | 用真实 HTTP 形态驱动页面，模拟延迟、失败和状态流转 |
| 排序 | dnd-kit | 拖动排序；必须同时提供上移／下移按钮 |
| PWA | `vite-plugin-pwa` / Workbox | 缓存 App Shell、字体、图标和演示媒体，不缓存写请求 |
| 单元／组件测试 | Vitest + React Testing Library | 状态机、业务规则和组件行为 |
| E2E | Playwright | 手机视口下覆盖主 Demo 和安全分支 |
| 代码质量 | ESLint + Prettier | CI 执行 typecheck、lint、test、build |

### 不选 Next.js 的原因

- P0 是登录后式工具界面，没有 SEO 和 SSR 需求；
- 业务 API 已由 FastAPI 承担，不需要再增加 Node BFF；
- 静态 SPA 更容易本地运行、Mock、部署和现场兜底；
- 未来若出现官网 SEO 或服务端渲染需求，可单独增加官网，不需要改动当前业务域模型。

## 4. 前端架构

按“应用壳 → 页面 → 功能 → 业务实体 → 共享基础设施”分层。页面负责组合，业务规则放在 feature/entity 中，基础组件不感知业务。

```text
frontend/
  public/
    media/                    # 允许公开访问的固定 Demo 媒体
  src/
    app/
      router/                 # 路由、懒加载、返回规则
      providers/              # Query、Router、Theme、ErrorBoundary
      styles/                 # 全局样式与 design tokens
    pages/                    # P00—P11 页面组合
    features/
      import-video/
      collect-card/
      add-card-to-plan/
      edit-plan/
      start-training/
      submit-sensation/
      view-experience/
    entities/
      action-card/
      exercise/
      plan/
      training-session/
      peer-experience/
      body-buddy/
    widgets/
      app-shell/
      bottom-navigation/
      action-card-view/
      muscle-map/
      training-player/
    shared/
      api/                    # Repository 接口、HTTP 实现、Zod schema
      ui/                     # Button、Sheet、Card、Status、EmptyState
      lib/                    # 时间、ID、媒体、可访问性工具
      config/                 # 环境变量与 feature flags
    mocks/
      data/                   # 固定 ID 的集中 Demo 数据
      handlers/               # MSW 接口与异常场景
      scenarios/              # normal、empty、offline、discomfort
    test/
  e2e/
  package.json
  README.md
```

约束：

- 页面和组件不得直接导入 `mocks/data`；统一通过 Repository／Query Hook 读取；
- 页面不得直接写 `fetch`，所有接口集中在 `shared/api`；
- 业务枚举、DTO 和 Zod Schema 只定义一次；
- 不建立巨大的全局 `components/` 或 `store/`；代码跟随业务能力放置；
- 当前视频动作卡、标准动作、练友经验是三个不同实体，类型上不得混用。

## 5. 路由规划

| 页面 | 路由 | 实现备注 |
| --- | --- | --- |
| P00 模拟抖音 | `/demo/douyin/:videoId` | Demo 专用，不出现在底部导航 |
| P01 视频接入 | `/import/:videoId` | 支持已有、处理中、失败、待确认 |
| P02 动作卡详情 | `/cards/:cardId` | `mode=learn|quick` 可写入 query string |
| P03 练单首页 | `/plans` | 一级入口 |
| P03A 练单详情 | `/plans/:planId` | 自动保存、训练入口 |
| P04 动作选择 | `/plans/:planId/select` | 保留搜索与筛选状态 |
| P05 动作库 | `/library` | 一级入口 |
| P06 训练执行 | `/train/:sessionId` | 活动训练的唯一主路由 |
| P07 练后体感 | 无独立路由 | P06 内的 `SensationSheet` 状态 |
| P08 练友经验 | `/experience/:exerciseId` | query 携带 `issue`、`videoId`、`from=train` |
| P09 不适提示 | `/safety` | state/query 携带 session item，刷新可恢复 |
| P10 训练完成 | `/train/:sessionId/complete` | 会话未结束时禁止误入 |
| P11 我的 | `/me` | 一级入口 |

底部导航只有“练单、动作库、我的”。训练、接入、安全提示等沉浸页不显示底部导航。

返回来源使用 URL 和 Router state 表达；不得只依赖全局布尔值。训练中打开动作卡或练友经验后，返回必须恢复同一 `sessionId` 和当前动作。

## 6. 核心数据与状态

### 6.1 领域对象

前端至少维护以下强类型对象：

- `SourceVideo`：来源平台、视频 ID、标题、创作者、封面、原视频地址；
- `ActionCard`：当前视频独有的步骤、提示、暗号、媒体、证据和 `exerciseId`；
- `Exercise`：标准动作 ID、名称、别名和肌群编号，仅用于关联；
- `Plan`：可复用练单，保存卡片 ID 和顺序；
- `TrainingSession`：由练单创建的不可变动作快照和本次进度；
- `SensationFeedback`：五类体感，`OTHER_FELT` 额外保存实际部位；
- `PeerExperienceDigest`：问题、经验组、评论数、视频数、分歧与来源；
- `BodyBuddySummary`：最近记录、训练次数和是否含不适。

### 6.2 状态归属

| 状态 | 唯一归属 | 示例 |
| --- | --- | --- |
| 可分享、可返回状态 | URL | cardId、planId、sessionId、筛选条件 |
| 服务端／Mock 事实 | TanStack Query | 动作卡、练单、训练、经验 |
| 当前组件状态 | React local state | 展开项、输入框、面板步骤 |
| 跨组件临时状态 | Zustand | 选择练单面板、返回意图、媒体控制 |
| 断点与待同步 | IndexedDB | 活动训练、未同步体感、Mock 数据版本 |

不得把完整动作卡、练单和训练会话同时复制进 Query Cache、Zustand 和 localStorage。IndexedDB 中的活动训练只用于恢复和同步，服务端成功后以服务端版本为准。

### 6.3 状态机

```text
视频处理：EXISTING | QUEUED | PROCESSING | READY | FAILED | NEEDS_REVIEW

训练会话：IN_PROGRESS → COMPLETED
                     └→ ENDED

训练动作：NOT_STARTED → COMPLETED
                       ├→ SKIPPED
                       └→ STOPPED_DISCOMFORT
```

“点击练过”只打开体感面板；提交体感成功后才把动作改为 `COMPLETED`。选择不适则改为 `STOPPED_DISCOMFORT`，进入安全分流，不能触发庆祝文案。

### 6.4 统一体感枚举

本方案以最新版交互稿为准：

```text
TARGET_FELT
OTHER_FELT
NO_FEELING
TOO_HARD
DISCOMFORT
```

旧团队文档中的 `NO_CLEAR_FEELING`、`TOO_DIFFICULT` 不再用于新前端。正式联调前，业务后端与 AI 输入契约必须完成同名同步。

## 7. 数据访问与 Mock 策略

定义同一套 Repository 接口，两种实现只在应用启动时切换：

```text
VITE_DATA_SOURCE=mock  → MSW + IndexedDB
VITE_DATA_SOURCE=http  → /api/v1
```

组件只调用 Query Hook，例如 `usePlan(planId)`、`useStartTraining()`，不知道数据来自 Mock 还是真实后端。

Mock 必须满足：

- 使用固定 ID，不按中文名或数组下标关联；
- 覆盖 `normal`、`empty`、`processing-failed`、`offline`、`discomfort`；
- 写操作真实改变 Mock 数据，刷新后从 IndexedDB 恢复；
- 可配置 300—800ms 延迟，暴露 loading、saving 和 error UI；
- 返回结构必须通过与 HTTP 实现相同的 Zod Schema；
- 提供“一键重置 Demo 数据”的开发入口，生产 UI 不显示。

接口以仓库 `docs/technical/api.md` 的 `/api/v1` 约定为准。前端不得直接对接 AI 中心。接口尚未实现时，先固定请求／响应 fixture，再由业务后端补齐。

## 8. 关键交互实现规则

### 练单

- 新建后立即创建草稿；名称、动作、顺序变更采用乐观更新；
- 自动保存显示“保存中／已保存／保存失败，点击重试”；
- 排序一次提交完整 ID 顺序，并携带 `version` 防止覆盖；
- 同一卡片不能重复加入同一练单；
- 删除练单不删除动作卡与历史训练。

### 训练

- 开始训练时复制动作卡必要字段，生成会话快照；
- 编辑原练单不能影响已开始的训练；
- 每次完成、跳过、体感提交后立即写 IndexedDB，再幂等同步后端；
- 同时只保留一个进行中的训练，开始新训练前处理旧训练；
- 当前媒体优先加载，下一个动作空闲预取；媒体失败时文字仍可完成训练。

### 练友经验与安全

- 查询至少携带 `exerciseId + issue + currentVideoId + fromTraining`；
- 始终区分“来自本视频”“来自练友”“AI 整理”；
- 样本不足不使用“多数人”“有效率”等确定表达；
- 不适、疼痛、麻木、眩晕等直接进入 P09，不优先展示普通经验；
- `DISCOMFORT` 只能明确撤销，不能被普通体感直接覆盖。

## 9. UI 与体验基线

- 设计宽度以 390px 为主，同时验收 360px；桌面端居中显示手机内容区；
- 所有点击区域至少 44×44 CSS px，并适配 `safe-area-inset-*`；
- 训练速记核心信息在一屏内优先显示，媒体加载不阻塞文字；
- 颜色不是唯一状态表达，主要／辅助肌群同时使用标签或图例；
- Sheet、Dialog 打开后锁定背景滚动并正确管理焦点；
- 骨架屏用于初次加载，局部刷新不清空已有内容；
- 错误状态必须说明“发生了什么”和“下一步做什么”；
- 动画服务于状态变化，并尊重 `prefers-reduced-motion`；
- P0 人体图优先使用可点亮的前／后二维 SVG；若素材未就绪，先用肌群列表完成同等信息。

## 10. 组件清单

第一批通用组件：

- `AppShell`、`BottomNavigation`、`PageHeader`；
- `Button`、`IconButton`、`Tag`、`SourceBadge`；
- `Sheet`、`Dialog`、`Toast`、`ConfirmDialog`；
- `LoadingSkeleton`、`EmptyState`、`ErrorState`、`OfflineBanner`；
- `ActionCardView`、`QuickMemoryView`、`SourceClipPlayer`；
- `PlanCard`、`PlanItem`、`RecommendationCard`；
- `MuscleMap`、`MuscleLegend`；
- `TrainingControls`、`TrainingProgress`、`SensationSheet`；
- `PeerExperienceGroup`、`EvidenceList`、`SafetyNotice`；
- `BodyBuddy`、`TrainingSummary`。

先实现业务中真实复用两次以上的组件，不提前建设完整组件库。

## 11. 开发阶段

### 阶段 0：契约与素材准备

- 确认五种体感、训练动作状态、肌群编号；
- 确认 4 张主 Demo 卡、媒体、练友经验和固定 ID；
- 补齐前端需要的 API fixture；
- 确认视觉方向与人体 SVG／健身搭子素材。

完成标志：Mock DTO、枚举和素材清单不再口头变更。

### 阶段 1：工程骨架与设计基线

- 建立 Vite、路由、Query、MSW、Tailwind、测试与 CI；
- 完成 App Shell、底部导航、Token 和基础状态组件；
- 打通 Mock／HTTP Repository 切换。

完成标志：三个一级入口可运行，正常／空／错误状态可切换。

### 阶段 2：动作卡与练单闭环

- 完成 P00—P05；
- 完成动作卡双模式、来源标签、选择练单；
- 完成练单 CRUD、排序、自动保存、推荐候选和肌群概览。

完成标志：不依赖 AI 推荐也能建立并保存一份至少含一个动作的练单。

### 阶段 3：训练与体感闭环

- 完成 P06、P07、P09、P10；
- 实现训练快照、进度、跳过、五类体感和刷新恢复；
- 完成身体搭子正常反馈与不适禁庆祝状态。

完成标志：可从保存练单创建训练，并在刷新后继续到完成页。

### 阶段 4：练友经验与“我的”

- 完成 P08、P11；
- 完成问题匹配、来源依据、有用反馈、空状态和安全提示；
- 完成健身搭子与最近训练记录。

完成标志：“其他部位更酸 → 手臂 → 练友经验 → 返回训练”完整可走通。

### 阶段 5：真实联调与演示封板

- 将数据源切到 `/api/v1`，修正契约差异；
- 完成断网、媒体失败、处理中、无候选和不适分支；
- 执行手机 E2E、构建检查、性能检查和 Demo 重置演练。

完成标志：主流程 2—3 分钟内稳定走完，Mock 和真实 API 两种模式均可启动。

## 12. 两名前端的协作建议

| 工作流 | 前端 A：设计与体验 | 前端 B：交互与数据 |
| --- | --- | --- |
| 基础 | Token、App Shell、通用 UI | Repository、Schema、MSW、Query |
| 内容 | P00—P05 页面与动作卡表现 | 练单状态、排序、自动保存、肌群计算 |
| 训练 | P06—P11 页面与反馈表现 | 会话状态机、离线恢复、经验查询 |
| 收尾 | 响应式、动效、空错状态 | API 联调、E2E、Demo 数据重置 |

双方共同维护 DTO 与主流程 E2E；任何影响 DTO、固定 ID、肌群编号或状态枚举的变更，需要先同步业务后端。

## 13. 测试与验收

### 必测业务规则

- 同一卡片不能重复加入同一练单；
- 练单排序、删除和名称自动保存；
- 训练是练单快照，不反向修改练单；
- “练过”在体感提交前不完成动作；
- `OTHER_FELT` 必须记录实际部位；
- `DISCOMFORT` 停止动作、不庆祝、不进入普通经验建议；
- 从动作卡／经验返回训练后仍是同一动作；
- 刷新和短暂断网后能恢复最近进度；
- 来源标签和原视频／原评论入口不丢失。

### 提交门槛

```text
pnpm typecheck
pnpm lint
pnpm test
pnpm build
pnpm e2e
```

E2E 至少覆盖：

1. 模拟抖音 → 动作卡 → 新建练单 → 添加第二张卡 → 开始训练；
2. 目标部位有感觉 → 下一动作 → 完成总结；
3. 其他部位更酸 → 手臂 → 练友经验 → 返回训练；
4. 出现不适 → 安全提示 → 结束动作／退出训练；
5. 刷新页面 → 恢复活动训练。

## 14. 开工前需要确认

以下事项不阻止搭脚手架，但必须在阶段 0 结束前确定：

1. 业务后端将体感枚举统一为新版的 `NO_FEELING`、`TOO_HARD`；
2. `docs/technical/api.md` 补齐真实请求／响应示例、错误结构和版本字段；
3. 主 Demo 的视频、循环片段、封面、人体 SVG 和健身搭子素材路径；
4. 主 Demo 固定卡片 ID、标准动作 ID、肌群 code 和问题标签；
5. 现场演示默认使用 Mock、真实 API，还是通过环境变量一键切换；
6. P09 `/safety` 的刷新恢复参数由 query 还是 session lookup 提供。

## 15. 参考资料

- React versions: <https://react.dev/versions>
- Vite 8.1: <https://vite.dev/blog/announcing-vite8-1>
- React Router: <https://reactrouter.com/start/data/routing>
- TanStack Query: <https://tanstack.com/query/latest/docs/framework/react/overview>
- Tailwind CSS 4.3: <https://tailwindcss.com/blog/tailwindcss-v4-3>
