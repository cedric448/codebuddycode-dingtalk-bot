#!/bin/bash
# 钉钉机器人状态查看脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务名称
SERVICE_NAME="dingtalk-bot"
PROJECT_DIR="/root/project-wb/dingtalk_bot"
LOG_FILE="/var/log/dingtalk-bot.log"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人服务状态${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查服务状态
echo -e "${BLUE}服务状态:${NC}"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "  运行状态: ${GREEN}运行中 ✓${NC}"
    echo -e "  进程PID:  ${GREEN}$(systemctl show --property=MainPID --value "$SERVICE_NAME")${NC}"
    echo -e "  运行时间: ${GREEN}$(systemctl show --property=ActiveEnterTimestamp --value "$SERVICE_NAME" | cut -d' ' -f2-)${NC}"
else
    echo -e "  运行状态: ${RED}已停止 ✗${NC}"
fi

# 开机自启状态
echo ""
echo -e "${BLUE}开机自启:${NC}"
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo -e "  ${GREEN}已启用${NC}"
else
    echo -e "  ${YELLOW}未启用${NC}"
fi

# 资源使用
echo ""
echo -e "${BLUE}资源使用:${NC}"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    PID=$(systemctl show --property=MainPID --value "$SERVICE_NAME")
    if [ -n "$PID" ] && [ "$PID" != "0" ]; then
        CPU=$(ps -p "$PID" -o %cpu= 2>/dev/null | tr -d ' ')
        MEM=$(ps -p "$PID" -o %mem= 2>/dev/null | tr -d ' ')
        RSS=$(ps -p "$PID" -o rss= 2>/dev/null | tr -d ' ')
        
        echo -e "  CPU使用: ${GREEN}${CPU}%${NC}"
        echo -e "  内存使用: ${GREEN}${MEM}% (${RSS}KB)${NC}"
    fi
fi

# 日志状态
echo ""
echo -e "${BLUE}日志状态:${NC}"
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(du -h "$LOG_FILE" 2>/dev/null | cut -f1)
    LOG_LINES=$(wc -l < "$LOG_FILE" 2>/dev/null)
    echo -e "  日志文件: ${GREEN}$LOG_FILE${NC}"
    echo -e "  文件大小: ${GREEN}${LOG_SIZE}${NC}"
    echo -e "  日志行数: ${GREEN}${LOG_LINES}${NC}"
else
    echo -e "  日志文件: ${RED}不存在${NC}"
fi

# 图片目录
echo ""
echo -e "${BLUE}图片存储:${NC}"
if [ -d "${PROJECT_DIR}/images" ]; then
    IMAGE_COUNT=$(ls -1 "${PROJECT_DIR}/images" 2>/dev/null | wc -l)
    IMAGE_SIZE=$(du -sh "${PROJECT_DIR}/images" 2>/dev/null | cut -f1)
    echo -e "  存储目录: ${GREEN}${PROJECT_DIR}/images${NC}"
    echo -e "  图片数量: ${GREEN}${IMAGE_COUNT}${NC}"
    echo -e "  占用空间: ${GREEN}${IMAGE_SIZE}${NC}"
else
    echo -e "  存储目录: ${YELLOW}不存在${NC}"
fi

# 最近日志
echo ""
echo -e "${BLUE}最近日志 (最后5行):${NC}"
if [ -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}"
    tail -n 5 "$LOG_FILE"
    echo -e "${NC}"
else
    echo -e "  ${RED}日志文件不存在${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "操作命令:"
echo -e "  启动服务: ${YELLOW}sudo ./start.sh${NC}"
echo -e "  停止服务: ${YELLOW}sudo ./stop.sh${NC}"
echo -e "  重启服务: ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC}"
echo -e "  查看日志: ${YELLOW}sudo tail -f $LOG_FILE${NC}"
echo ""
