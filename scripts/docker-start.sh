#!/bin/bash
# 钉钉机器人 Docker 一键启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
ENV_FILE="${PROJECT_DIR}/.env"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人 Docker 部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    echo -e "请先安装 Docker:"
    echo -e "  ${YELLOW}curl -fsSL https://get.docker.com | sh${NC}"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    echo -e "请先安装 Docker Compose:"
    echo -e "  ${YELLOW}pip install docker-compose${NC}"
    exit 1
fi

# 检查 .env 文件
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}错误: 配置文件 .env 不存在${NC}"
    echo -e "请复制 .env.example 到 .env 并配置相关参数:"
    echo -e "  ${YELLOW}cp .env.example .env${NC}"
    echo -e "  ${YELLOW}vim .env${NC}"
    exit 1
fi

# 检查必要的配置
echo -e "${YELLOW}检查配置...${NC}"
source "$ENV_FILE"

if [ -z "$DINGTALK_CLIENT_ID" ] || [ "$DINGTALK_CLIENT_ID" = "your_client_id_here" ]; then
    echo -e "${RED}错误: DINGTALK_CLIENT_ID 未配置${NC}"
    exit 1
fi

if [ -z "$DINGTALK_CLIENT_SECRET" ] || [ "$DINGTALK_CLIENT_SECRET" = "your_client_secret_here" ]; then
    echo -e "${RED}错误: DINGTALK_CLIENT_SECRET 未配置${NC}"
    exit 1
fi

echo -e "${GREEN}配置检查通过${NC}"

# 创建必要的目录
echo -e "${YELLOW}创建数据目录...${NC}"
mkdir -p "${PROJECT_DIR}/images"
mkdir -p "${PROJECT_DIR}/logs"
echo -e "${GREEN}目录创建完成${NC}"

# 进入项目目录
cd "$PROJECT_DIR"

# 拉取最新镜像（如果有远程镜像）
# echo -e "${YELLOW}拉取最新镜像...${NC}"
# docker-compose pull

# 构建镜像
echo -e "${YELLOW}构建 Docker 镜像...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}镜像构建完成${NC}"

# 停止旧容器（如果存在）
if docker-compose ps | grep -q "dingtalk-bot"; then
    echo -e "${YELLOW}停止旧容器...${NC}"
    docker-compose down
    echo -e "${GREEN}旧容器已停止${NC}"
fi

# 启动服务
echo -e "${YELLOW}启动服务...${NC}"
docker-compose up -d
echo -e "${GREEN}服务启动完成${NC}"

# 等待服务启动
sleep 3

# 检查服务状态
echo ""
echo -e "${BLUE}服务状态:${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "  容器状态: ${GREEN}运行中 ✓${NC}"
    CONTAINER_ID=$(docker-compose ps -q)
    echo -e "  容器ID: ${GREEN}${CONTAINER_ID:0:12}${NC}"
    
    # 显示日志
    echo ""
    echo -e "${BLUE}启动日志 (最后10行):${NC}"
    echo -e "${YELLOW}"
    docker-compose logs --tail=10
    echo -e "${NC}"
else
    echo -e "  容器状态: ${RED}启动失败 ✗${NC}"
    echo -e "${RED}请检查日志: docker-compose logs${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人 Docker 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "查看日志: ${YELLOW}docker-compose logs -f${NC}"
echo -e "停止服务: ${YELLOW}docker-compose down${NC}"
echo -e "重启服务: ${YELLOW}docker-compose restart${NC}"
echo -e "查看状态: ${YELLOW}docker-compose ps${NC}"
echo ""
