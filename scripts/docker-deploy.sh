#!/bin/bash
# 钉钉机器人 Docker 一键部署脚本（包含环境检查、安装、配置）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人 Docker 一键部署${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用 root 权限运行此脚本${NC}"
    echo "用法: sudo ./docker-deploy.sh"
    exit 1
fi

# 步骤 1: 检查并安装 Docker
echo -e "${BLUE}[步骤 1/5] 检查 Docker 环境...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker 未安装，正在安装...${NC}"
    
    # 安装 Docker
    curl -fsSL https://get.docker.com | sh
    
    # 启动 Docker 服务
    systemctl start docker
    systemctl enable docker
    
    echo -e "${GREEN}Docker 安装完成${NC}"
else
    echo -e "${GREEN}Docker 已安装: $(docker --version)${NC}"
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose 未安装，正在安装...${NC}"
    
    # 安装 Docker Compose
    pip3 install docker-compose || pip install docker-compose
    
    echo -e "${GREEN}Docker Compose 安装完成${NC}"
else
    echo -e "${GREEN}Docker Compose 已安装: $(docker-compose --version)${NC}"
fi

# 步骤 2: 创建项目目录
echo ""
echo -e "${BLUE}[步骤 2/5] 创建项目目录...${NC}"

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"
mkdir -p images logs

echo -e "${GREEN}项目目录创建完成: $PROJECT_DIR${NC}"

# 步骤 3: 创建配置文件
echo ""
echo -e "${BLUE}[步骤 3/5] 创建配置文件...${NC}"

if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# 钉钉机器人配置（从钉钉开放平台获取）
DINGTALK_CLIENT_ID=your_client_id_here
DINGTALK_CLIENT_SECRET=your_client_secret_here
DINGTALK_APP_ID=your_app_id_here

# CodeBuddy HTTP API 配置
CODEBUDDY_API_URL=http://your-server-ip:port/agent
CODEBUDDY_API_TOKEN=your_codebuddy_api_token_here

# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
EOF
    echo -e "${GREEN}配置文件 .env 已创建${NC}"
    echo -e "${YELLOW}提示: 请根据需要修改 .env 文件中的配置${NC}"
else
    echo -e "${GREEN}配置文件 .env 已存在${NC}"
fi

# 步骤 4: 构建并启动服务
echo ""
echo -e "${BLUE}[步骤 4/5] 构建并启动服务...${NC}"

# 确保脚本有执行权限
chmod +x docker-start.sh docker-stop.sh docker-status.sh 2>/dev/null || true

# 启动服务
./docker-start.sh

# 步骤 5: 验证部署
echo ""
echo -e "${BLUE}[步骤 5/5] 验证部署...${NC}"

sleep 3

if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ 服务运行正常${NC}"
else
    echo -e "${RED}✗ 服务启动失败${NC}"
    echo -e "请检查日志: docker-compose logs"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人 Docker 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "项目目录: ${BLUE}$PROJECT_DIR${NC}"
echo ""
echo -e "常用命令:"
echo -e "  查看状态: ${YELLOW}./docker-status.sh${NC}"
echo -e "  查看日志: ${YELLOW}docker-compose logs -f${NC}"
echo -e "  停止服务: ${YELLOW}./docker-stop.sh${NC}"
echo -e "  重启服务: ${YELLOW}docker-compose restart${NC}"
echo ""
echo -e "配置文件: ${YELLOW}$PROJECT_DIR/.env${NC}"
echo ""
