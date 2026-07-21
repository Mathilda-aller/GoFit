# GoFit 前端 Demo

这是一个零依赖的本地可点击 Demo，按照产品文档实现“视频 → 动作卡 → 练单 → 训练 → 体感反馈 → 练友经验”的 P0 主流程。

## 启动

在仓库根目录执行：

```text
cd frontend
python -m http.server 5173
```

另开一个终端启动业务后端：

```text
cd backend/business
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

然后打开 `http://127.0.0.1:5173`。

## 当前 Demo 能做什么

- 从移动端优先的模拟抖音视频流进入任意一条预置健身视频；
- 模拟 AI 解析进度并生成视频动作卡；
- 切换完整步骤和训练速记；
- 收藏动作卡、创建练单、添加动作、调整顺序；
- 开始训练并记录五种体感；
- “其他部位更酸”和“没找到明显感觉”进入跨视频练友经验；
- “出现不适”进入安全提示页；
- 保存训练结果并在“我的”查看健身搭子与历史记录。

前端启动后会优先连接 `http://127.0.0.1:8000/api/v1`。如果业务后端没有启动，会自动回退到浏览器内 mock 状态，方便单独演示页面。

如需临时切换 API 地址，可在浏览器控制台执行：

```js
localStorage.setItem("gofit-api-base", "http://127.0.0.1:8000/api/v1")
location.reload()
```
