---
name: fitness-video-to-action-card
description: 将原始健身视频或带时间范围的 ASR、OCR 和画面证据整理为可追溯、可翻面的健身视频动作卡。用于运行 GoFit 视频重构 Workflow、检查 FitnessVideoToActionCardSkill、生成完整学习正面和训练速记背面的动作卡 JSON，或验证动作卡是否只使用当前视频证据。
---

# Fitness Video to Action Card

把已经完成时间对齐的多模态证据交给仓库中的核心 Skill，生成并校验一张有正反两面的动作卡。不要在这里处理原视频、评论或数据库。

## 工作流程

1. 阅读 `references/contract.md`。原始视频请求使用 `raw-video`；已有对齐证据使用 `aligned-evidence`。P0 原始视频 Demo 省略标准动作候选时，默认使用人工确认的唯一动作“哑铃侧平举”；已有对齐证据仍必须明确包含候选。
2. 不补写输入证据之外的动作知识；评论、练友经验和其他视频的观点不能进入动作卡。
3. 已有对齐证据时，从仓库根目录运行：

   ```powershell
   python .agents/skills/fitness-video-to-action-card/scripts/run_skill.py `
     --input backend/ai/fixtures/lateral_raise/input.json `
     --output backend/ai/tmp/action-card.json
   ```

   处理原始视频时，先配置 `backend/ai/.env` 和 FFmpeg，再运行：

   ```powershell
   python .agents/skills/fitness-video-to-action-card/scripts/run_skill.py `
     --mode raw-video `
     --input backend/ai/fixtures/video_workflow/request.example.json `
     --output backend/ai/tmp/video-workflow-result.json
   ```

4. 检查命令退出码。原始视频模式还要检查 `actionCardRequest` 是否同时包含 ASR、OCR、VISION 证据，以及 `mediaArtifacts` 是否存在。
5. 成功时读取动作卡，分别检查 `learningSide` 正面和 `trainingSide` 背面，不要把它们合并为同一页面内容。
6. 确认每个步骤、提示、错误和媒体选择都有 `evidenceIds`，并确认正反面使用同一段正确示范。
7. 如果证据不足或动作匹配不确定，保留 `NEEDS_REVIEW` 和人工确认原因，不要猜测缺失内容。
8. 向用户返回动作卡和媒体文件位置、执行是否成功，以及需要人工确认的原因。

`scripts/run_skill.py` 只负责找到仓库并调用 `backend/ai` 中的命令行；动作卡逻辑必须保留在 Python Skill 中。
