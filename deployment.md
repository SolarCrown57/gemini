# Zeabur 部署策略（基于容器）

本指南详细介绍了如何使用 Docker 将 Vertex AI Proxy 应用程序部署到类似 Zeabur 的 VPS 环境中。

## 1. Dockerfile

此 `Dockerfile` 设置 Python 环境，安装 Playwright 所需的依赖项，并准备应用程序以供执行。

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Prevent Playwright from complaining about root user
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Set work directory
WORKDIR /app

# Install system dependencies required for building Python packages
# and basic tools
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and system dependencies
# We install only chromium to save space/time as it's the default for this app
RUN playwright install chromium \
    && playwright install-deps chromium

# Copy the rest of the application code
COPY . .

# Create a directory for default configs to support volume initialization
# We copy the local config folder to a defaults location
RUN mkdir -p /app/config_defaults && \
    cp -r config/* /app/config_defaults/ || true

# Copy and setup entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose the API and WebSocket ports
EXPOSE 28880 28881

# Define the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
```

## 2. 入口脚本 (`entrypoint.sh`)

此脚本对于**持久化**至关重要。当您将卷挂载到 `/app/config` 时，它最初可能为空。此脚本确保在应用程序启动之前存在必要的默认配置文件。

```bash
#!/bin/bash
set -e

# Define directories
CONFIG_DIR="/app/config"
DEFAULTS_DIR="/app/config_defaults"

# Ensure config directory exists
mkdir -p "$CONFIG_DIR"

# Initialize config files if they are missing
# This handles the case where a new volume is mounted
echo "Checking configuration files..."
if [ -d "$DEFAULTS_DIR" ]; then
    for file in "$DEFAULTS_DIR"/*; do
        filename=$(basename "$file")
        target="$CONFIG_DIR/$filename"
        
        if [ ! -e "$target" ]; then
            echo "Initializing missing config: $filename"
            # Use -r to handle directories like browser_data if they exist in defaults
            cp -r "$file" "$target"
        fi
    done
fi

# Start the application
echo "Starting Vertex AI Proxy..."
exec python main.py
```

## 3. 持久化策略

为了防止重启时数据丢失（浏览器会话、Cookie、统计信息），您必须持久化 `config/` 目录。

*   **卷挂载：** 将持久卷挂载到 `/app/config`。
*   **持久化的内容：**
    *   `config.json`：用户设置。
    *   `credentials.json`：保存的身份验证令牌。
    *   `stats.json`：使用统计信息。
    *   `browser_data/`：**至关重要**。此目录包含 Chromium 用户数据配置文件（Cookie、本地存储、会话）。持久化此目录允许“无头”模式在容器重启之间保持登录会话，从而减少频繁重新验证的需要。

## 4. 端口

应用程序需要暴露两个端口：

*   **28880 (TCP)：** 主 HTTP API 端口。
*   **28881 (TCP)：** WebSocket 端口（用于“有头”模式通信，虽然在纯无头 VPS 设置中不太重要，但为了调试或混合设置，最好将其暴露）。

## 5. Zeabur / Docker Compose 配置

### Zeabur 特性
在 Zeabur 中，您通常在“服务设置”选项卡中配置这些设置：

*   **服务名称：** `vertex-proxy`（示例）
*   **镜像：**（从 Dockerfile 构建）
*   **端口：**
    *   添加端口：`28880` (HTTP)
    *   添加端口：`28881` (HTTP/WS)
*   **卷（持久存储）：**
    *   挂载路径：`/app/config`
    *   卷名称：`vertex-config`（创建一个新卷）
*   **命令：** Dockerfile 中的 `ENTRYPOINT` 处理此操作，因此通常留空或默认即可。

### Docker Compose 等效项（用于本地测试）

```yaml
version: '3.8'

services:
  vertex-proxy:
    build: .
    container_name: vertex-proxy
    restart: unless-stopped
    ports:
      - "28880:28880"
      - "28881:28881"
    volumes:
      # Persist the config directory
      - ./data/config:/app/config
    environment:
      - TZ=Asia/Shanghai
```

## 用户步骤总结

1.  在项目根目录创建 `Dockerfile`。
2.  在项目根目录创建 `entrypoint.sh`。
3.  （可选）创建 `docker-compose.yml` 用于测试。
4.  部署到 Zeabur/VPS，确保 **卷** 挂载到 `/app/config`。