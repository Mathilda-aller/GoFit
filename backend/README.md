# 后端

后端分为两个中心，职责边界保持简单明确：

```text
Frontend
   |
   v
Business center -----> AI center
   |
   v
SQLite and local storage
```

前端只调用业务中心。业务中心负责业务数据、演示用户状态、数据保存和对外 API；
AI 中心负责模型相关工作，可以由 AI 负责同学独立实现。

当前 MVP 暂时不引入复杂的长任务基础设施。业务中心先保留任务接口，第一版可以使用
进程内执行或预置结果，后续再接入真正的 AI Worker。
