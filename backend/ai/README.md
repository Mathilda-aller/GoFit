# AI 中心

此目录由 AI 负责同学维护。当前先作为 AI 能力边界，不要求一开始就完成具体实现。

AI 中心后续可以提供：

- 视频转动作卡
- 标准动作归一化
- 练友经验聚类
- 练单候选动作推荐

业务中心通过稳定的结构化接口调用 AI。AI 代码不能直接修改练单、训练会话或用户数据，
这些数据的写入仍然由业务中心负责。

后续可以提供的内部接口：

```text
POST /internal/v1/action-card-jobs
POST /internal/v1/peer-experience-jobs
POST /internal/v1/recommendations
```
