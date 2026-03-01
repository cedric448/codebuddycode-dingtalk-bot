#!/bin/bash
# 钉钉机器人 Docker 状态查看脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人 Docker 状态${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    exit 1
fi

# 进入项目目录
cd "$PROJECT_DIR"

# 检查容器状态
echo -e "${BLUE}容器状态:${NC}"
if docker-compose ps | grep -q "dingtalk-bot"; then
    CONTAINER_STATUS=$(docker-compose ps | grep "dingtalk-bot" | awk '{print $4}')
    CONTAINER_ID=$(docker-compose ps -q)
    
    if [ "$CONTAINER_STATUS" = "Up" ] || echo "$CONTAINER_STATUS" | grep -q "Up"; then
        echo -e "  运行状态: ${GREEN}运行中 ✓${NC}"
        echo -e "  容器ID: ${GREEN}${CONTAINER_ID:0:12}${NC}"
        
        # 获取容器详细信息
        CONTAINER_INFO=$(docker inspect "$CONTAINER_ID" 2>/dev/null)
        if [ -n "$CONTAINER_INFO" ]; then
            START_TIME=$(echo "$CONTAINER_INFO" | grep -o '"StartedAt": "[^"]*"' | head -1 | cut -d'"' -f4)
            if [ -n "$START_TIME" ]; then
                echo -e "  启动时间: ${GREEN}${START_TIME}${NC}"
            fi
        fi
        
        # 资源使用
        echo ""
        echo -e "${BLUE}资源使用:${NC}"
        STATS=$(docker stats --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" "$CONTAINER_ID" 2>/dev/null | tail -n 1)
        if [ -n "$STATS" ]; then
            CPU=$(echo "$STATS" | awk '{print $1}')
            MEM=$(echo "$STATS" | awk '{print $2 " " $3}')
            echo -e "  CPU: ${GREEN}${CPU}${NC}"
            echo -e "  内存: ${GREEN}${MEM}${NC}"
        fi
    else
        echo -e "  运行状态: ${RED}已停止${NC}"
    fi
else
    echo -e "  运行状态: ${RED}未部署${NC}"
fi

# 镜像信息
echo ""
echo -e "${BLUE}镜像信息:${NC}"
IMAGE_INFO=$(docker images dingtalk-bot:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 2>/dev/null | tail -n 1)
if [ -n "$IMAGE_INFO" ]; then
    echo -e "  ${GREEN}${IMAGE_INFO}${NC}"
else
    echo -e "  ${YELLOW}镜像未构建${NC}"
fi

# 数据卷
echo ""
echo -e "${BLUE}数据卷:${NC}"
if [ -d "${PROJECT_DIR}/images" ]; then
    IMAGE_COUNT=$(ls -1 "${PROJECT_DIR}/images" 2>/dev/null | wc -l)
    IMAGE_SIZE=$(du -sh "${PROJECT_DIR}/images" 2>/dev/null | cut -f1)
    echo -e "  图片目录: ${GREEN}${PROJECT_DIR}/images${NC}"
    echo -e "  图片数量: ${GREEN}${IMAGE_COUNT}${NC}"
    echo -e "  占用空间: ${GREEN}${IMAGE_SIZE}${NC}"
fi

if [ -d "${PROJECT_DIR}/logs" ]; then
    LOG_SIZE=$(du -sh "${PROJECT_DIR}/logs" 2>/dev/null | cut -f1)
    echo -e "  日志目录: ${GREEN}${PROJECT_DIR}/logs${NC}"
    echo -e "  占用空间: ${GREEN}${LOG_SIZE}${NC}"
fi

# 最近日志
echo ""
echo -e "${BLUE}最近日志 (最后10行):${NC}"
if docker-compose ps | grep -q "dingtalk-bot"; then
    echo -e "${YELLOW}"
    docker-compose logs --tail=10 2>/dev/null || echo "无法获取日志"
    echo -e "${NC}"
else
    echo -e "  ${YELLOW}容器未运行，无法获取日志${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "操作命令:"
echo -e "  启动服务: ${YELLOW}./docker-start.sh${NC}"
echo -e "  停止服务: ${YELLOW}./docker-stop.sh${NC}"
echo -e "  重启服务: ${YELLOW}docker-compose restart${NC}"
echo -e "  查看日志: ${YELLOW}docker-compose logs -f${NC}"
echo -e "  进入容器: ${YELLOW}docker-compose exec dingtalk-bot bash${NC}"
echo ""
