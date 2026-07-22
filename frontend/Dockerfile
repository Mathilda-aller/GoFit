# GoFit Frontend - 生产镜像
FROM node:22-alpine AS builder

WORKDIR /app

# 启用 corepack 并使用项目指定的 pnpm 版本
RUN corepack enable && corepack prepare pnpm@11.9.0 --activate

# 安装依赖
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# 复制源码并构建
COPY . .
RUN pnpm build

# 用 Nginx 托管静态文件
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
