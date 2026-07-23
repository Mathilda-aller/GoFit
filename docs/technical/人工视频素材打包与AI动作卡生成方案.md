# GoFit 人工视频素材打包与 AI 动作卡生成方案

## 1. 目标与结论

本方案用于 GoFit 内置的 10 个标准动作。每个动作由人工准备：

- 1 条原视频，交给真实 AI 做 ASR、OCR、画面理解和动作卡文案生成；
- 至少 1 条人工确认的正确动作裁片；
- 0～N 条人工确认的错误动作裁片；
- 1 份 `manifest.json`，明确动作身份、文件关系和裁片在原视频中的时间范围。

推荐的仓库内目录是：

```text
storage/
├── videos/                         # 原视频；现有业务后端从这里读取
│   ├── 01-lateral-raise.mp4
│   ├── 02-shoulder-press.mp4
│   └── ...
├── curated-clips/                  # 人工确认的正确/错误裁片
│   ├── 01-lateral-raise/
│   │   ├── manifest.json
│   │   ├── correct/
│   │   │   └── 01-lateral-raise--correct-01.mp4
│   │   └── error/
│   │       ├── 01-lateral-raise--error-01.mp4
│   │       └── 01-lateral-raise--error-02.mp4
│   └── ...
└── ai-generated/                   # AI/FFmpeg 运行产物；不要人工投放素材
```

核心原则：**动作身份和正确/错误片段由人工确定；动作步骤、提示、纠错说明等内容由真实 AI 根据该动作的原视频证据生成。**

## 2. 从现有 mock 代码得到的十个动作

十个动作以 `frontend/src/mocks/demo-catalog.ts` 和 `backend/ai/fixtures/video_workflow/shoulder-back-demo.json` 中的标识为准。原视频文件名继续沿用前端当前的 `assetFileName`，这样业务后端和现有页面不需要重新映射文件名。

| 序号 | 标准动作 ID | 动作名 | 目录 slug | 原视频文件名 | 正确裁片文件名 |
|---:|---|---|---|---|---|
| 01 | `action_lateral_raise` | 哑铃侧平举 | `01-lateral-raise` | `01-lateral-raise.mp4` | `01-lateral-raise--correct-01.mp4` |
| 02 | `action_shoulder_press` | 坐姿哑铃推肩 | `02-shoulder-press` | `02-shoulder-press.mp4` | `02-shoulder-press--correct-01.mp4` |
| 03 | `action_reverse_fly` | 俯身反向飞鸟 | `03-reverse-fly` | `03-reverse-fly.mp4` | `03-reverse-fly--correct-01.mp4` |
| 04 | `action_front_raise` | 哑铃前平举 | `04-front-raise` | `04-front-raise.mp4` | `04-front-raise--correct-01.mp4` |
| 05 | `action_face_pull` | 绳索面拉 | `05-face-pull` | `05-face-pull.mp4` | `05-face-pull--correct-01.mp4` |
| 06 | `action_lat_pulldown` | 高位下拉 | `06-lat-pulldown` | `06-lat-pulldown.mp4` | `06-lat-pulldown--correct-01.mp4` |
| 07 | `action_seated_cable_row` | 坐姿绳索划船 | `07-seated-cable-row` | `07-seated-cable-row.mp4` | `07-seated-cable-row--correct-01.mp4` |
| 08 | `action_one_arm_dumbbell_row` | 单臂哑铃划船 | `08-one-arm-dumbbell-row` | `08-one-arm-dumbbell-row.mp4` | `08-one-arm-dumbbell-row--correct-01.mp4` |
| 09 | `action_chest_supported_row` | 上斜凳俯卧划船 | `09-chest-supported-row` | `09-chest-supported-row.mp4` | `09-chest-supported-row--correct-01.mp4` |
| 10 | `action_straight_arm_pulldown` | 直臂下压 | `10-straight-arm-pulldown` | `10-straight-arm-pulldown.mp4` | `10-straight-arm-pulldown--correct-01.mp4` |

错误裁片统一按同一规则递增编号。例如坐姿推肩有三条错误裁片时：

```text
02-shoulder-press--error-01.mp4
02-shoulder-press--error-02.mp4
02-shoulder-press--error-03.mp4
```

文件名只使用小写英文字母、数字和连字符。动作的中文名、错误含义和时间范围写进 `manifest.json`，不写进文件名，避免文件名过长或人工改文案后失效。

## 3. 每个动作的完整打包结构

以哑铃侧平举为例：

```text
storage/
├── videos/
│   └── 01-lateral-raise.mp4
└── curated-clips/
    └── 01-lateral-raise/
        ├── manifest.json
        ├── correct/
        │   └── 01-lateral-raise--correct-01.mp4
        └── error/
            ├── 01-lateral-raise--error-01.mp4
            └── 01-lateral-raise--error-02.mp4
```

原视频不复制进动作裁片目录。`manifest.json` 通过相对仓库根目录的路径引用 `storage/videos/` 中的原视频，因此一条视频只有一个主文件。

### 3.1 `manifest.json` 建议格式

```json
{
  "schemaVersion": "1.0.0",
  "standardActionId": "action_lateral_raise",
  "actionName": "哑铃侧平举",
  "sourceVideo": {
    "videoId": "video_lateral_raise_demo",
    "file": "storage/videos/01-lateral-raise.mp4",
    "title": "侧平举总是手臂酸？新手先记住这 3 点",
    "creatorName": "阿哲的训练课",
    "sourceUrl": "https://example.test/videos/lateral-raise"
  },
  "correctClips": [
    {
      "candidateId": "action_lateral_raise_correct_01",
      "file": "storage/curated-clips/01-lateral-raise/correct/01-lateral-raise--correct-01.mp4",
      "sourceStartMs": 8000,
      "sourceEndMs": 15000
    }
  ],
  "errorClips": [
    {
      "candidateId": "action_lateral_raise_error_01",
      "file": "storage/curated-clips/01-lateral-raise/error/01-lateral-raise--error-01.mp4",
      "sourceStartMs": 22000,
      "sourceEndMs": 27000,
      "reviewNote": "人工确认：画面展示耸肩代偿；该备注仅供验收，不直接作为 AI 文案证据。"
    },
    {
      "candidateId": "action_lateral_raise_error_02",
      "file": "storage/curated-clips/01-lateral-raise/error/01-lateral-raise--error-02.mp4",
      "sourceStartMs": 28000,
      "sourceEndMs": 33000,
      "reviewNote": "人工确认：画面展示下放过快。"
    }
  ]
}
```

字段约定：

- `standardActionId` 必须是上表十个 ID 之一，不允许 AI 创建第十一个动作。
- `videoId` 与当前 mock 的 `video_*_demo` 保持一致，便于前端和业务数据映射。
- `candidateId` 在全部十个动作中唯一，并且提交后不随文案变化。
- `sourceStartMs`、`sourceEndMs` 是裁片在**原视频时间轴**中的毫秒位置，不是裁片自身的 `0～时长`。
- `reviewNote` 是人工验收备注。若要求动作卡内容完全来自视频证据，就不能把该备注直接拼进模型提示词。
- 每个动作必须有且只有一个主正确片段；错误片段允许为空，也允许有多条。

时间范围非常重要。当前动作卡的每个媒体选择都需要引用 ASR、OCR 或 VISION 的 `evidenceIds`。有了原视频时间范围，工作流才能把人工裁片与原视频证据对齐；只有孤立裁片文件而没有时间范围，会失去可追溯性。

## 4. 素材制作标准

### 4.1 原视频

- 放在仓库根目录 `storage/videos/`，不要放在 `frontend/src/mocks/`、`backend/ai/fixtures/` 或 `storage/ai-generated/`。
- 文件名必须与上表完全一致，因为当前业务接口按 `assetFileName` 查找文件。
- 推荐 MP4 容器、H.264 视频、AAC 音频、`yuv420p` 像素格式。
- 保留原始口播、字幕和画面文字。AI 的步骤、提示、纠错说明需要这些证据。
- 不在交付后改变时长、帧率或片头；否则 manifest 中的毫秒时间范围会失效。

现有 `backend/business/storage/videos/` 不是代码默认目录。除非专门设置了 `GOFIT_STORAGE_DIR=./storage`，否则不要继续向该目录投放正式的十动作素材。仓库 README 和业务后端默认配置都指向仓库根目录的 `storage/videos/`。

### 4.2 正确裁片

- 每个动作至少 1 条，默认命名为 `--correct-01.mp4`。
- 建议 3～8 秒，包含至少一次可辨认的完整动作过程；实际时长以动作需要为准。
- 推荐无声输出，因为当前 FFmpeg 自动裁片也会移除音频，循环播放时不会反复播出口播。
- 不变速、不倒放、不插帧、不拼接多个不连续区间。
- 正面 `correctDemo` 和背面 `loopDemo` 必须使用同一条正确片段。

如果确实需要多个角度，先只指定一条为主正确片段；其余可命名 `--correct-02.mp4`、`--correct-03.mp4`，但 manifest 需新增 `isPrimary`，并确保只有一个 `true`。

### 4.3 错误裁片

- 没有明确错误画面时，不要为了凑数制作错误片段；该动作的 `errorClips` 使用空数组。
- 一条裁片只表达一种主要错误。多个错误分别编号，避免 AI 无法判断错误描述对应哪段画面。
- 建议 2～6 秒，保留错误发生前后的少量上下文。
- `reviewNote` 可以帮助人工复核，但最终 `mistake` 和 `correction` 文案仍应由 AI 从原视频的口播、字幕和画面证据中生成。
- 如果原视频只展示错误动作、但没有解释怎样纠正，AI 不应凭通用健身知识补写纠正方法；应返回 `NEEDS_REVIEW`。

## 5. “人工选片 + 真实 AI 内容”的数据边界

建议的数据流是：

```text
十动作白名单 + 人工 manifest
              │
              ├── 固定动作身份
              ├── 固定正确/错误媒体文件
              └── 提供原视频时间范围
                         │
原视频 ── ASR / OCR / VISION ── 对齐证据
                         │
                         └── 真实动作卡模型
                             ├── steps
                             ├── keyReminders
                             ├── quickCue / quickTips
                             └── commonErrors 的文字
```

以下内容由人工或业务规则决定：

- 只能从十个标准动作中选哪个动作；
- 哪条片段是正确示范；
- 哪些片段是错误示范；
- 原视频和裁片文件之间的时间对应关系。

以下内容由真实 AI 基于当前原视频证据生成：

- 3～5 个动作步骤；
- 最多 2 条关键提醒；
- 一句训练暗号和最多 3 条速记提示；
- 原视频明确支持时的错误描述和纠正说明；
- 每段文案引用的 `evidenceIds`。

以下内容不应进入当前视频动作卡：

- mock 里的预写 `card.steps`、`card.tips`、`mistake`、`correction`；
- 其他视频或评论区的练友经验；
- 模型根据常识补写、但当前视频没有证据支持的知识。

## 6. 当前代码现状与必须补的接入工作

### 6.1 现在已经能工作的部分

- 业务后端能从 `storage/videos/<assetFileName>` 读取原视频并提供 `/api/v1/media/videos/<fileName>`。
- 业务后端会把原视频绝对路径提交给 AI 中心。
- AI 工作流会对原视频执行 ASR、OCR 和视觉分析。
- AI 工作流能根据媒体候选的原视频时间范围，用 FFmpeg 生成片段到 `storage/ai-generated/<requestId>/`。
- 动作卡契约已经区分 `CORRECT_DEMO` 和 `ERROR_DEMO`，且要求所有媒体和文案关联证据。

### 6.2 当前不能直接工作的部分

1. **人工裁片尚未被读取。** 当前工作流只接收 `videoPath`，正确/错误候选来自视觉模型，再从原视频自动裁剪。把文件放进 `storage/curated-clips/` 后，现有代码不会自动使用它们。
2. **业务导入接口没有传十动作候选。** `backend/business/app/api/routes/videos.py` 当前只传原视频信息和路径；AI 请求缺少 `standardActionCandidates` 时会默认成“哑铃侧平举”。因此其他九个动作不能直接沿用这条默认路径。
3. **前端十张 mock 卡仍使用预写文案。** `frontend/src/mocks/data.ts` 会从 catalog 生成步骤、错误和提示；真实 AI 卡片要通过业务 API 返回，不能继续以 mock 卡片作为内容来源。
4. **前端没有按 `mediaArtifacts` 播放人工/AI 片段。** 当前真实业务卡转换仍大量借用 mock 模板，需要把正确/错误片段 URL 映射到对应卡片区域。
5. **`demo-videos` 路径是遗留约定。** 前端 mock 和 AI fixture 中仍出现 `../../demo-videos/`，但实际业务读取规则和仓库 README 已统一到 `storage/videos/`。新素材不应再放到不存在的 `demo-videos/`。

### 6.3 推荐的最小改造顺序

1. 新增十动作素材 manifest 读取器，并校验 ID、路径、文件后缀、时间范围和主正确片段数量。
2. 业务导入请求显式携带该动作的 `standardActionCandidates`，删除“其余九个动作也默认侧平举”的可能。
3. 扩展 AI 工作流请求，加入 `curatedMedia`；有人工裁片时优先使用人工候选，没有时才使用 VLM 的媒体候选。
4. AI 仍分析原视频；工作流根据 `sourceStartMs/sourceEndMs` 将人工裁片绑定到重叠的 VISION/ASR/OCR 证据。
5. 将人工裁片注册为 `mediaArtifacts`，并给业务后端增加安全的媒体 URL；不要只保存本机绝对 `filePath`。
6. 前端从真实卡片的媒体 URL 播放 `correctDemo`、`loopDemo` 和每条 `errorDemo`，移除真实卡对 mock 模板媒体的依赖。
7. 完成一个动作的端到端验收后，再批量导入其余九个动作。

## 7. 人工交付流程

每完成一个动作，按以下步骤交付：

1. 按上表重命名原视频，放入 `storage/videos/`。
2. 建立 `storage/curated-clips/<序号-slug>/correct/` 和 `error/`。
3. 输出正确、错误裁片并按规则编号。
4. 填写 `manifest.json`，特别核对原视频时间范围。
5. 检查所有 MP4 是否能播放，且文件名大小写完全一致。
6. 运行素材校验脚本；在脚本落地前按本节清单人工验收。
7. 通过业务接口提交原视频和显式标准动作候选。
8. 检查 AI 结果是否同时包含 ASR、OCR、VISION 证据和 `mediaArtifacts`。
9. 抽查每个步骤、提醒、错误说明和媒体是否都能追溯到当前原视频证据。
10. 证据不足时保留 `NEEDS_REVIEW`，不要用 mock 文案填空。

## 8. 单动作验收清单

- [ ] 原视频位于 `storage/videos/`，名称与十动作表一致。
- [ ] 动作目录名称为 `<两位序号>-<slug>`。
- [ ] 至少存在一条 `--correct-01.mp4`。
- [ ] 每条错误裁片只展示一种主要错误；无错误时 `errorClips` 为空。
- [ ] `manifest.json` 中的动作 ID、视频 ID 和文件路径正确。
- [ ] 所有 `candidateId` 全局唯一。
- [ ] 所有 `sourceStartMs < sourceEndMs`，并且没有超出原视频时长。
- [ ] 裁片时长与 `sourceEndMs - sourceStartMs` 基本一致。
- [ ] 裁片没有变速、倒放或不连续拼接。
- [ ] AI 输入显式包含对应的唯一 `standardActionCandidates`。
- [ ] 动作卡文案来自真实 AI 和当前视频证据，不是 `demo-catalog.ts` 的预写内容。
- [ ] 正面正确示范与背面循环示范引用同一个 `candidateId`。
- [ ] 每条错误说明只绑定对应的错误裁片和证据。

## 9. 推荐实施范围

第一轮先只打包并接通 `01-lateral-raise`：它是当前固定 fixture 和原始视频工作流已经验证过的动作。通过后冻结 manifest 格式和前端播放契约，再复制到其余九个动作。这样人工团队可以立即按统一命名继续剪辑，同时开发团队只需对一种目录结构实现一次导入和校验。

