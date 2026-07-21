# FitnessVideoToActionCardSkill 契约

## 卡片是什么

一张动作卡代表“某一条视频是怎么教这个动作的”，不是这个动作的标准答案。输入必须是当前视频已经完成时间对齐的证据，不是原始视频。

```text
原视频处理 Workflow → 对齐证据 → 本 Skill → 双面动作卡 → 业务后端
```

一般情况下标准动作候选由业务后端提供。P0 原始视频 Demo 已人工确认是“哑铃侧平举”，省略候选时由请求契约注入这个唯一候选；AI 不再重新识别或创建动作。AI 返回内容后，仍由业务后端决定是否保存。

## 必要输入

- `requestId`
- `sourceVideo`：视频 ID、标题、创作者和原地址
- `standardActionCandidates`：至少一个业务后端提供的标准动作
- `evidence`：至少一条 ASR、OCR 或 VISION 证据，每条包含 `evidenceId`、`startMs`、`endMs` 和 `text`
- `mediaCandidates`：可选的封面、正确示范和错误示范区间

完整输入见 `backend/ai/fixtures/lateral_raise/input.json`。

## 输出是同一张卡的两个状态

`schemaVersion` 当前为 `1.1.0`。

```text
actionCard
├─ sourceVideo、actionName、肌群、器械等共享信息
├─ learningSide：翻卡正面，供第一次学习
└─ trainingSide：翻卡背面，供训练现场速记
```

正反面不能在同一页同时展示。前端负责翻面动画和当前显示哪一面，AI 只准备两面的内容。

### 正面 learningSide

- `correctDemo`：正确示范片段
- `steps`：3–5 个步骤，每一步只说一件事
- `keyReminders`：最多 2 条关键提醒
- `commonErrors`：只有原视频明确提供错误示范时才出现；每条错误都包含 `errorDemo`

### 背面 trainingSide

- `loopDemo`：训练时循环播放的正确示范
- `quickCue`：一句动作暗号
- `quickTips`：最多 3 条短提示

正面的 `correctDemo` 和背面的 `loopDemo` 必须是同一个候选区间，避免翻面后出现不同动作片段。

## 共同规则

- 每个步骤、提醒、暗号、速记提示、错误和媒体片段都必须引用输入中的 `evidenceId`。
- 标准动作只能从输入候选中选择。
- 媒体只能从输入候选中选择，时间和证据引用不能改写。
- 没有 `ERROR_DEMO` 候选时，`commonErrors` 必须为空。
- 来源视频信息必须原样保留，让用户能区分同一动作的不同视频卡。
- 不允许未声明字段。

完整固定输出见 `backend/ai/fixtures/lateral_raise/expected-output.json`。

## 不属于动作卡的内容

练友经验来自同动作的多条视频评论，不能进入当前视频卡的正文。业务后端使用 `standardActionId` 在卡片外单独加载练友经验。

收藏、加入练单、查看练单、“练过”、跳过等状态和按钮也不由 AI 输出。

## 当前限制

固定假模型只支持 `video_lateral_raise_demo`，不会调用真实模型，也不会读取评论、数据库或视频文件。未知视频必须返回 `MOCK_FIXTURE_NOT_FOUND`。

## 原始视频 Workflow

`FitnessVideoReconstructionWorkflow` 负责把原视频变成上述 Skill 的输入：

```text
原视频
→ FFmpeg 提取音频和粗采样画面
→ ASR 生成带时间口播
→ 视觉模型生成 VISION、OCR 观察和候选片段
→ 按时间组装 evidence 和 mediaCandidates
→ FFmpeg 精确输出图片与循环视频
→ 调用 FitnessVideoToActionCardSkill
```

原始视频请求见 `backend/ai/fixtures/video_workflow/request.example.json`。该 P0 请求省略 `standardActionCandidates` 时会自动使用唯一的 `action_lateral_raise`；未来处理其他动作时必须由业务后端显式提供候选。

真实运行前，从 `.env.example` 创建 `backend/ai/.env`，填写 `DASHSCOPE_API_KEY`；ASR、OCR、视觉和动作卡模型名已经预填。DashScope 基础地址已有默认值。不要把真实 Key 提交到 Git。
