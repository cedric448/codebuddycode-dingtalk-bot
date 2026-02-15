#!/bin/bash
# 钉钉机器人 Docker 一键停止脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人 Docker 停止脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    exit 1
fi

# 进入项目目录
cd "$PROJECT_DIR"

# 检查容器是否运行
if ! docker-compose ps | grep -q "dingtalk-bot"; then
    echo -e "${YELLOW}钉钉机器人容器未运行${NC}"
    exit 0
fi

echo -e "${YELLOW}正在停止钉钉机器人服务...${NC}"

# 停止服务
docker-compose down

echo -e "${GREEN}服务已停止${NC}"

# 询问是否删除镜像和数据
echo ""
echo -e "${YELLOW}是否删除 Docker 镜像和数据? [y/N]${NC}"
read -t 10 -n 1 -r answer || true
echo ""

if [[ $answer =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}删除 Docker 镜像...${NC}"
    docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true
    docker rmi dingtalk-bot:latest 2>/dev/null || true
    echo -e "${GREEN}镜像和数据已删除${NC}"
else
    echo -e "${YELLOW}保留 Docker 镜像和数据${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人 Docker 服务已停止${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "启动服务: ${YELLOW}./docker-start.sh${NC}"
echo ""
