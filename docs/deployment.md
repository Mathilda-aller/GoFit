# GoFit DigitalOcean + Docker Hub 自动部署指南

本方案使用 **GitHub Actions + Docker Hub + DigitalOcean Droplet + Docker Compose + Watchtower**，实现：

```text
本地 push 代码到 GitHub main 分支
    ↓
GitHub Actions 自动构建 Docker 镜像
    ↓
镜像推送到 Docker Hub
    ↓
DigitalOcean 服务器上的 Watchtower 检测到新镜像
    ↓
自动拉取新镜像并重启 gofit-business 容器
```

---

## 1. 准备工作

### 1.1 注册 Docker Hub 并创建仓库

1. 去 [Docker Hub](https://hub.docker.com) 注册账号。
2. 创建一个仓库，名为 `gofit-business`。
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
   - **Plan**：Basic，$6/月或 $12/月即可
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
# 更新软件源
apt update && apt upgrade -y

# 安装 Docker
apt install -y docker.io docker-compose-plugin

# 验证安装
docker --version
docker compose version
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

内容：

```text
DOCKERHUB_USERNAME=muxinji
```

保存退出（Ctrl+O，回车，Ctrl+X）。

### 3.4 登录 Docker Hub 并拉取首次镜像

```bash
docker login docker.io -u muxinji
# 输入你的 Docker Hub 密码或 Access Token

# 手动拉取第一次镜像，确保能正常访问
docker pull muxinji/gofit-business:latest
```

### 3.5 启动服务

```bash
docker compose up -d
```

查看运行状态：

```bash
docker compose ps
docker logs -f gofit-business
```

访问健康检查接口：

```text
http://你的Droplet公网IP:8000/api/v1/health
```

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

传完后重启容器（可选，因为 storage 是挂载的，通常不需要重启）：

```bash
docker compose restart gofit-business
```

---

## 5. 验证自动更新

1. 在本地修改 `backend/business/app/main.py` 或任意代码。
2. 提交并 push 到 `main` 分支：
   ```bash
   git add .
   git commit -m "update api"
   git push origin main
   ```
3. 打开 GitHub 仓库的 Actions 页面，确认 workflow 执行成功。
4. 等待约 1~2 分钟，Watchtower 会检测到新镜像并自动重启容器。
5. 在服务器上查看日志确认更新：
   ```bash
   docker logs -f watchtower
   docker logs -f gofit-business
   ```

---

## 6. 常见问题

### 6.1 服务器无法拉取镜像

- 检查 Docker Hub 登录是否成功。
- 检查 `.env` 中的 `DOCKERHUB_USERNAME` 是否正确。
- 检查 GitHub Actions 是否成功推送镜像。

### 6.2 Watchtower 没有自动更新

- 确认容器标签是 `latest`，Watchtower 默认只检测 `latest` 标签。
- 查看 Watchtower 日志：
  ```bash
  docker logs -f watchtower
  ```
- 确认 `gofit-business` 容器有标签 `com.centurylinklabs.watchtower.enable=true`（已在 docker-compose.yml 中配置）。

### 6.3 想用 HTTPS / 域名访问

可以在服务器上再装一个 Nginx 或 Traefik 做反向代理，并配置 SSL 证书。需要时再说。

### 6.4 想回滚版本

在 Docker Hub 中给镜像打具体版本标签（如 `v1.0.1`），需要回滚时修改服务器上的镜像标签并重启即可。

---

## 7. 文件说明

| 文件 | 作用 |
|------|------|
| `backend/business/Dockerfile` | 业务中心镜像构建文件 |
| `docker-compose.yml` | 生产环境服务编排（业务 + Watchtower + storage 挂载） |
| `.github/workflows/deploy.yml` | GitHub Actions 自动构建推送到 Docker Hub |
| `.env.example` | 环境变量模板 |
