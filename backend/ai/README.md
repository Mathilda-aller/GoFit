# GoFit AI 中心

AI 中心只负责把业务后端提供的来源材料整理为结构化结果。业务后端负责校验业务规则、保存数据，并向前端提供接口。

当前实现包含四项独立能力：`FitnessVideoReconstructionWorkflow` 把原始视频加工为对齐证据；`FitnessVideoToActionCardSkill` 把证据生成可追溯的双面动作卡；`PeerExperienceService` 对 Mock 评论执行真实向量聚类、摘要和体感召回；`RecommendationRanker` 根据业务后端提供的练单上下文执行可解释的规则推荐。它们都不访问业务数据库。

## 当前链路

```text
原视频 → ASR / OCR / 画面理解 → 时间对齐 → 媒体候选
                                      ↓
业务后端提供标准动作候选 → FitnessVideoToActionCardSkill
                                      ↓
                    双面动作卡和媒体文件 → 业务后端保存
```

证据到动作卡接口可以显式使用固定侧平举假模型。原始视频 Workflow 默认使用阿里云 DashScope；配置一个 API Key、三个模型名和 FFmpeg 后才会调用真实模型。

## 动作卡的正反面

返回的不是一张塞满所有内容的长页面，而是一张可以翻面的卡：

```text
动作卡共享信息
├─ 动作名称、训练部位、肌群、器械
├─ 来源视频、创作者和原视频地址
├─ 正面 learningSide：完整学习
│  ├─ 正确示范
│  ├─ 3–5 个步骤
│  ├─ 最多 2 条关键提醒
│  └─ 有原视频证据时才出现的错误示范
└─ 背面 trainingSide：训练速记
   ├─ 循环示范
   ├─ 一句动作暗号
   └─ 最多 3 条提示
```

`learningSide` 和 `trainingSide` 是翻卡前后的两个状态，不应该同时展示在一页。正反面使用同一段正确示范，AI 会检查两边是否一致。

练友经验不属于动作卡内容。业务后端可以通过返回的 `standardActionId`，在卡片正文之外加载同动作、多视频评论整理结果。收藏、加入练单和“练过”等按钮状态也由业务后端和前端负责，不由 AI 生成。

## 目录

```text
app/models/       输入和输出的数据格式
app/providers/    固定假模型；未来真实模型实现相同接口
app/skills/       动作卡生成与证据引用校验
app/api/routes/   AI 内部接口
fixtures/         可重复运行的侧平举样例
tests/            契约、Skill、API 和命令行测试
```

## 本地启动

需要 Python 3.11 或更高版本。

```powershell
cd backend/ai
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8001
```

浏览器或业务后端可调用：

```text
GET  http://127.0.0.1:8001/internal/v1/health
POST http://127.0.0.1:8001/internal/v1/action-cards/build
POST http://127.0.0.1:8001/internal/v1/recommendations/rank
POST http://127.0.0.1:8001/internal/v1/peer-experiences/digest
POST http://127.0.0.1:8001/internal/v1/peer-experiences/match
```

业务后端当前默认查找 `http://127.0.0.1:8100`。如果 AI 服务按上面的示例运行在 `8001`，启动业务后端前设置：

```powershell
$env:GOFIT_AI_CENTER_URL = "http://127.0.0.1:8001"
```

请求样例就是 [`fixtures/lateral_raise/input.json`](fixtures/lateral_raise/input.json)，固定返回值是 [`fixtures/lateral_raise/expected-output.json`](fixtures/lateral_raise/expected-output.json)。

PowerShell 调用示例：

```powershell
$body = Get-Content fixtures/lateral_raise/input.json -Raw
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8001/internal/v1/action-cards/build `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

## 命令行

命令行、HTTP API 和 Python 代码使用同一个 Skill，不会复制生成逻辑。

```powershell
python -m app.cli build-action-card `
  --input fixtures/lateral_raise/input.json `
  --output tmp/action-card.json
```

Python 调用入口：

```python
request = ActionCardBuildRequest.model_validate(payload)
skill = FitnessVideoToActionCardSkill(FixedFixtureActionCardGenerator())
result = skill.execute(request)
```

## 第二阶段：从原始视频生成动作卡

`FitnessVideoReconstructionWorkflow` 已实现以下流程：

```text
原始视频
→ FFmpeg 提取音频和等间隔画面
→ ASR 生成带时间口播
→ 视觉模型理解动作画面并补充 OCR 文字
→ 组装 ASR / OCR / VISION 证据
→ 找出正确示范、错误示范和封面候选
→ FFmpeg 精确输出媒体文件
→ 调用 FitnessVideoToActionCardSkill
→ 返回双面动作卡
```

### 配置模型

复制示例配置，真实 `.env` 已被 Git 忽略：

```powershell
Copy-Item .env.example .env
```

P0 主链全部使用阿里云百炼 DashScope。`.env` 里可以把阿里云配置集中放在一起，日常只需要填写：

```dotenv
DASHSCOPE_API_KEY=你的百炼 API Key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com
GOFIT_ASR_MODEL=qwen3-asr-flash
GOFIT_OCR_MODEL=qwen3.5-ocr
GOFIT_VISION_MODEL=qwen3.6-plus
GOFIT_ACTION_CARD_MODEL=qwen-flash
```

VLM、独立 OCR 和动作卡文本模型使用 DashScope OpenAI 兼容 `chat/completions`；短音频 ASR 使用同一 API Key 调用 DashScope `multimodal-generation`，本地 WAV 以 Base64 Data URI 上传。OCR 只读取画面文字，VLM 负责动作阶段和候选片段，动作卡文本模型负责证据约束整理。

虽然都是阿里云模型，但 DashScope 目前有两套接口路径：OCR / VLM / 文本模型走 OpenAI 兼容接口，ASR 走原生接口。所以代码现在默认从同一个 `DASHSCOPE_BASE_URL` 自动派生：

- `DASHSCOPE_COMPATIBLE_BASE_URL = {DASHSCOPE_BASE_URL}/compatible-mode/v1`
- `DASHSCOPE_NATIVE_BASE_URL = {DASHSCOPE_BASE_URL}/api/v1`

只有账号使用特定地域或 Workspace 地址，或者未来某一类模型必须单独切地址时，才需要显式设置 `DASHSCOPE_COMPATIBLE_BASE_URL`、`DASHSCOPE_NATIVE_BASE_URL` 或 `GOFIT_PEER_API_BASE_URL`。

本机还必须安装 FFmpeg，并确保 `ffmpeg` 和 `ffprobe` 可以在命令行运行；也可以在 `.env` 中填写它们的完整路径。

### 命令行处理视频

主 Demo 已人工确认是“哑铃侧平举”。请求省略 `standardActionCandidates` 时，会自动注入唯一候选 `action_lateral_raise`，模型不再负责动作识别或多候选选择。仓库根目录已经包含对应的 Demo 视频，可直接使用 [`fixtures/video_workflow/request.example.json`](fixtures/video_workflow/request.example.json) 跑通链路；替换为自己的视频时，只需修改请求中的 `videoPath`。

```powershell
python -m app.cli process-video `
  --input fixtures/video_workflow/request.example.json `
  --output tmp/video-workflow-result.json
```

结果包含：

- `actionCardRequest`：Workflow 生成的对齐证据，也就是第一阶段 Skill 的输入；
- `actionCardResult`：双面动作卡；
- `mediaArtifacts`：FFmpeg 输出的封面或循环视频文件位置。

### 业务后端创建处理任务

长时间模型调用不会放在普通同步请求里。业务后端使用：

```text
POST /internal/v1/action-card-jobs
GET  /internal/v1/action-card-jobs/{jobId}
```

`POST` 请求体与 `request.example.json` 相同。重复提交同一个 `requestId` 不会重复执行。查询接口会返回：

```text
QUEUED     任务已创建
RUNNING    正在理解视频内容 / 正在定位关键片段 / 正在整理动作要点
COMPLETED  动作卡已生成
FAILED     返回安全、可读的失败原因
```

当前任务状态保存在 AI 服务内存中，服务重启后会丢失，适合本地 Hackathon MVP。正式持久化和状态恢复仍由业务后端负责。

## 练单助手动作推荐

推荐接口是同步的纯规则计算，不调用大模型，也不会写入或修改当前练单。业务后端负责准备候选卡、收藏、历史体感和仍在屏蔽期的不感兴趣 ID。

固定请求和响应样例分别位于 [`fixtures/recommendation/input.json`](fixtures/recommendation/input.json) 和 [`fixtures/recommendation/expected-output.json`](fixtures/recommendation/expected-output.json)。调用示例：

```powershell
$body = Get-Content fixtures/recommendation/input.json -Raw
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8001/internal/v1/recommendations/rank `
  -ContentType "application/json; charset=utf-8" `
  -Body $body
```

推荐规则版本为 `p0-v1`：

- 直接排除已在练单、曾记录不适、仍在偏好屏蔽期、内容未就绪、来源风险未解除或关键字段缺失的动作；
- 根据身体大区、未覆盖主要肌群、历史目标体感、收藏未练、重复肌群、没感觉和吃力记录计算内部排序分；
- 同分时依次按收藏、未练过、信息完整度和固定卡片 ID 决定顺序；
- 每次最多返回 3 个候选和一个主要理由，不返回内部得分；
- 所有候选均不可用时仍返回 HTTP 200，`outcomeCode` 为 `NO_SAFE_CANDIDATE` 且 `items` 为空。

推荐支持两套已出现过的体感编号：`NO_FEELING` 等同于 `NO_CLEAR_FEELING`，`TOO_HARD` 等同于 `TOO_DIFFICULT`。错误的顶层请求契约返回 `INVALID_RECOMMENDATION_REQUEST`；未预期异常返回 `RECOMMENDATION_FAILED`，不会返回 Python 异常内容。

## 练友经验：Mock 评论真实聚类

MVP 不抓取平台评论。固定输入位于 `fixtures/peer_experience/digest-input.json`，其中 `riskType` 和 `problemTag` 已人工校验。默认 `GOFIT_PEER_PROVIDER=fixed-mock`，无需网络即可重复演示完整接口；设置为 `aliyun` 后使用 `text-embedding-v4`（1024 维）和 Qwen Flash 非思考模式。

```dotenv
GOFIT_PEER_PROVIDER=aliyun
GOFIT_PEER_API_KEY=你的密钥
GOFIT_PEER_EMBEDDING_MODEL=text-embedding-v4
GOFIT_PEER_EMBEDDING_DIMENSIONS=1024
GOFIT_PEER_SUMMARY_MODEL=qwen-flash
```

不写 `GOFIT_PEER_API_BASE_URL` 时，也会默认复用 `DASHSCOPE_BASE_URL` 推导出的 OpenAI 兼容地址。

真实链路为：按预置风险标签过滤 → 按问题标签分桶 → Embedding → cosine/average 层次聚类 → Flash 生成组名和一句摘要 → 程序计算评论数、来源数和 ID。模型 API 失败时，主 Demo 动作降级到 `expected-digest.json`，返回的 `providerMode` 为 `fixed-json-fallback`。

## 校验规则

- 至少有一条来源证据和一个标准动作候选。
- 每段证据的结束时间必须晚于开始时间。
- 步骤、提示、错误和媒体选择都必须引用输入中的 `evidenceId`。
- 只有输入包含 `ERROR_DEMO` 候选区间时才能输出常见错误；错误必须引用该区间的证据。
- 输出只能选择业务后端给出的标准动作和媒体候选。
- 正面步骤为 3–5 个，关键提醒最多 2 条。
- 背面速记提示最多 3 条，正反面必须使用同一段正确示范。
- 评论、练友经验、收藏和练单状态不能混入动作卡。
- 未声明字段会被拒绝，不会悄悄混入动作卡。

## 错误返回

所有预期错误都使用相同格式：

```json
{
  "error": {
    "code": "NO_EVIDENCE",
    "message": "缺少生成动作卡所需的来源证据。",
    "retryable": false,
    "requestId": "demo_action_card_001"
  }
}
```

错误代码包括：

```text
NO_EVIDENCE
INVALID_EVIDENCE_RANGE
NO_STANDARD_ACTION_CANDIDATES
UNKNOWN_EVIDENCE_REFERENCE
MOCK_FIXTURE_NOT_FOUND
OUTPUT_VALIDATION_FAILED
MODEL_CONFIGURATION_MISSING
MODEL_API_FAILED
FFMPEG_NOT_FOUND
VIDEO_FILE_NOT_FOUND
NO_SPEECH_EVIDENCE
NO_CORRECT_DEMO_CANDIDATE
ACTION_CARD_JOB_NOT_FOUND
```

## 测试

```powershell
cd backend/ai
.venv\Scripts\python -m pytest
```
