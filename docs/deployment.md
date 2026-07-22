# GoFit 腾讯云 Docker 自动部署指南

本方案使用 **GitHub Actions + 腾讯云容器镜像服务（TCR）+ Docker Compose + Watchtower**，实现：

```text
本地 push 代码到 GitHub main 分支
    ↓
GitHub Actions 自动构建 Docker 镜像
    ↓
镜像推送到腾讯云 TCR（国内访问快）
    ↓
腾讯云轻量应用服务器上的 Watchtower 检测到新镜像
    ↓
自动拉取新镜像并重启 gofit-business 容器
```

---

## 1. 准备工作

### 1.1 在腾讯云开通 TCR

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)。
2. 进入「容器镜像服务 TCR」→ 创建一个**个人版实例**（有免费额度）。
3. 记录实例的**注册表域名**，个人版通常为：
   ```
   ccr.ccs.tencentyun.com
   ```
4. 在实例下创建一个**命名空间（Namespace）**，例如 `gofit`。
5. 在「访问凭证」中设置登录密码，或创建一个长期访问凭证。

### 1.2 在 GitHub 配置 Secrets

打开你的 GitHub 仓库：

```
Settings → Secrets and variables → Actions → New repository secret
```

添加以下 3 个 Secrets：

| Secret 名称 | 说明 |
|-------------|------|
| `TCR_REGISTRY` | TCR 注册表域名，如 `ccr.ccs.tencentyun.com` |
| `TCR_USERNAME` | TCR 登录用户名，通常是**腾讯云账号 ID**（一串数字） |
| `TCR_PASSWORD` | TCR 登录密码或访问凭证密码 |
| `TCR_NAMESPACE` | 命名空间名称，如 `gofit` |

---

## 2. 在轻量应用服务器上部署

### 2.1 登录服务器

```bash
ssh ubuntu@你的服务器公网IP
```

### 2.2 安装 Docker 和 Docker Compose

```bash
# 更新软件源
sudo apt update && sudo apt upgrade -y

# 安装 Docker
sudo apt install -y docker.io docker-compose-plugin

# 将当前用户加入 docker 组，避免每次都用 sudo
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker compose version
```

### 2.3 拉取项目代码

```bash
cd ~
git clone https://github.com/你的用户名/GoFit.git
cd GoFit
```

### 2.4 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 TCR 信息：

```bash
nano .env
```

```text
TCR_REGISTRY=ccr.ccs.tencentyun.com
TCR_NAMESPACE=你的命名空间
```

保存退出（Ctrl+O，回车，Ctrl+X）。

### 2.5 登录 TCR 并拉取首次镜像

```bash
docker login ccr.ccs.tencentyun.com -u 你的腾讯云账号ID
# 输入密码

# 手动拉取第一次镜像，确保能正常访问
docker pull ccr.ccs.tencentyun.com/你的命名空间/gofit-business:latest
```

### 2.6 启动服务

```bash
docker compose up -d
```

查看运行状态：

```bash
docker compose ps
docker logs -f gofit-business
```

访问健康检查接口：

```
http://你的服务器公网IP:8000/api/v1/health
```

---

## 3. 验证自动更新

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

## 4. 常见问题

### 4.1 服务器无法拉取镜像

- 检查 TCR 是否在中国大陆区域（建议选广州/上海/北京）。
- 检查 `docker login` 是否成功。
- 检查 `.env` 中的 `TCR_REGISTRY` 和 `TCR_NAMESPACE` 是否正确。

### 4.2 Watchtower 没有自动更新

- 确认容器标签是 `latest`，Watchtower 默认只检测 `latest` 标签。
- 查看 Watchtower 日志：
  ```bash
  docker logs -f watchtower
  ```
- 确认 `gofit-business` 容器有标签 `com.centurylinklabs.watchtower.enable=true`（已在 docker-compose.yml 中配置）。

### 4.3 想用 HTTPS / 域名访问

可以在服务器上再装一个 Nginx 或 Traefik 做反向代理，并配置 SSL 证书。需要时再说。

### 4.4 想回滚版本

在 TCR 中给镜像打具体版本标签（如 `v1.0.1`），需要回滚时修改服务器上的镜像标签并重启即可。

---

## 5. 文件说明

| 文件 | 作用 |
|------|------|
| `backend/business/Dockerfile` | 业务中心镜像构建文件 |
| `docker-compose.yml` | 生产环境服务编排（业务 + Watchtower） |
| `.github/workflows/deploy.yml` | GitHub Actions 自动构建推送到 TCR |
| `.env.example` | 环境变量模板 |
