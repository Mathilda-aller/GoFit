# GoFit DigitalOcean + Docker Hub 自动部署指南

本方案使用 **GitHub Actions + Docker Hub + DigitalOcean Droplet + Docker Compose + Watchtower**，实现：

```text
本地 push 代码到 GitHub main 分支
    ↓
GitHub Actions 自动构建 3 个 Docker 镜像
    ↓
镜像推送到 Docker Hub
    ↓
DigitalOcean 服务器上的 Watchtower 检测到新镜像
    ↓
自动拉取新镜像并重启 gofit-business / gofit-ai / gofit-frontend
```

---

## 1. 准备工作

### 1.1 注册 Docker Hub 并创建仓库

1. 去 [Docker Hub](https://hub.docker.com) 注册账号。
2. 创建 3 个仓库：
   - `gofit-business`
   - `gofit-ai`
   - `gofit-frontend`
3. 记录你的 Docker Hub 用户名（例如 `muxinji`）。

### 1.2 生成 Docker Hub Access Token

1. 登录 Docker Hub。
2. 点击右上角头像 → **Account Settings**。
3. 左侧选择 **Security**。
4. 点击 **New Access Token**。
5. 名字填 `github-actions`，权限选 **Read, Write, Delete**。
6. 点击 **Generate**，复制生成的 token（只显示一次，务必保存）。

### 1.3 在 GitHub 配置 Secrets

打开你的 GitHub 仓库：

```text
Settings → Secrets and variables → Actions → New repository secret
```

添加以下 2 个 Secrets：

| Secret 名称 | 说明 |
|-------------|------|
| `DOCKERHUB_USERNAME` | 你的 Docker Hub 用户名，如 `muxinji` |
| `DOCKERHUB_TOKEN` | 刚才生成的 Docker Hub Access Token |

---

## 2. 购买并配置 DigitalOcean Droplet

### 2.1 创建 Droplet

1. 登录 [DigitalOcean 控制台](https://cloud.digitalocean.com/)。
2. 点击 **Create → Droplets**。
3. 选择配置：
   - **Region**：新加坡（Singapore）或离你用户最近的地区
   - **Plan**：建议至少 **$12/月（2GB 内存）**，$6/月（1GB 内存）运行 3 个服务可能吃紧
   - **OS**：Ubuntu 24.04 (LTS) x64
   - **Authentication**：SSH key 或密码（建议 SSH key）
4. 点击 **Create Droplet**。

### 2.2 登录服务器

```bash
ssh root@你的Droplet公网IP
```

---

## 3. 在 DigitalOcean 服务器上部署

### 3.1 安装 Docker 和 Docker Compose

```bash
apt update
apt install -y ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl start docker
systemctl enable docker
```

### 3.2 拉取项目代码

```bash
cd ~
git clone https://github.com/你的用户名/GoFit.git
cd GoFit
```

### 3.3 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```bash
nano .env
```

内容示例：

```text
DOCKERHUB_USERNAME=muxinji

# 如果需要真实 AI 模型，取消注释并填写
# DASHSCOPE_API_KEY=your-dashscope-api-key
# GOFIT_ASR_MODEL=qwen3-asr-flash
# GOFIT_OCR_MODEL=
# GOFIT_VISION_MODEL=
# GOFIT_ACTION_CARD_MODEL=
# GOFIT_ACTION_CARD_PROVIDER=dashscope
```

保存退出（Ctrl+O，回车，Ctrl+X）。

### 3.4 登录 Docker Hub 并拉取首次镜像

```bash
docker login docker.io -u muxinji
# 输入你的 Docker Hub 密码或 Access Token
```

### 3.5 启动服务

```bash
docker compose up -d
```

这会启动 4 个容器：

- `gofit-business`：业务后端，端口 8000
- `gofit-ai`：AI 中心，端口 8100
- `gofit-frontend`：前端 Nginx，端口 80
- `watchtower`：自动更新

查看运行状态：

```bash
docker compose ps
docker logs -f gofit-business
docker logs -f gofit-ai
docker logs -f gofit-frontend
```

### 3.6 访问服务

- 前端页面：`http://你的Droplet公网IP`
- 业务 API：`http://你的Droplet公网IP:8000/api/v1/health`
- AI 中心健康检查：`http://你的Droplet公网IP:8100/internal/v1/health`

---

## 4. 上传视频文件

你的视频文件没有进 GitHub，需要手动传到服务器的 `storage/` 目录。

在本地终端执行：

```bash
scp -r /Users/fenganhao/code/GoFit/storage/* root@你的Droplet公网IP:~/GoFit/storage/
```

如果视频很多，用 rsync：

```bash
rsync -avz --progress /Users/fenganhao/code/GoFit/storage/ root@你的Droplet公网IP:~/GoFit/storage/
```

传完后重启业务后端和 AI 中心（因为 storage 是挂载的，通常不需要重启，但保险起见可以重启）：

```bash
docker compose restart gofit-business gofit-ai
```

---

## 5. 验证自动更新

1. 在本地修改任意代码。
2. 提交并 push 到 `main` 分支：
   ```bash
   git add .
   git commit -m "update feature"
   git push origin main
   ```
3. 打开 GitHub 仓库的 Actions 页面，确认 3 个 workflow 都执行成功。
4. 等待约 1~2 分钟，Watchtower 会检测到新镜像并自动重启容器。
5. 在服务器上查看日志确认更新：
   ```bash
   docker logs -f watchtower
   ```

---

## 6. 常见问题

### 6.1 服务器内存不足

如果你买了 $6/月（1GB 内存）的 Droplet，可能跑不动 3 个服务。建议升级到 $12/月（2GB 内存），或者只部署需要的部分。

### 6.2 AI 中心启动失败

检查环境变量：

```bash
docker logs -f gofit-ai
```

如果缺少模型配置，AI 中心会使用固定假模型。如果需要真实模型，填写 `.env` 中的 `DASHSCOPE_API_KEY` 等配置。

### 6.3 前端访问不到后端

确认 `gofit-frontend` 容器里 `VITE_BUSINESS_API_URL=/api/v1`，并且 Nginx 配置正确反向代理到 `gofit-business:8000`。

### 6.4 Watchtower 没有自动更新

- 确认容器标签是 `latest`。
- 查看 Watchtower 日志：
  ```bash
  docker logs -f watchtower
  ```
- 确认容器有标签 `com.centurylinklabs.watchtower.enable=true`。

### 6.5 想用 HTTPS / 域名访问

可以在服务器上再装一个 Nginx 或 Traefik 做反向代理，并配置 SSL 证书。需要时再说。

---

## 7. 文件说明

| 文件 | 作用 |
|------|------|
| `backend/business/Dockerfile` | 业务中心镜像构建文件 |
| `backend/ai/Dockerfile` | AI 中心镜像构建文件 |
| `frontend/Dockerfile` | 前端镜像构建文件 |
| `frontend/nginx.conf` | 前端 Nginx 反向代理配置 |
| `docker-compose.yml` | 生产环境服务编排 |
| `.github/workflows/deploy.yml` | GitHub Actions 自动构建推送 |
| `.env.example` | 环境变量模板 |
