#!/bin/bash
# 钉钉机器人一键停止脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 服务名称
SERVICE_NAME="dingtalk-bot"
LOG_FILE="/var/log/dingtalk-bot.log"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人服务停止脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用 root 权限运行此脚本${NC}"
    echo "用法: sudo ./stop.sh"
    exit 1
fi

# 检查服务是否存在
if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
    echo -e "${RED}错误: 服务 ${SERVICE_NAME} 不存在${NC}"
    exit 1
fi

# 检查服务状态
echo -e "${YELLOW}检查服务状态...${NC}"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${YELLOW}服务正在运行，正在停止...${NC}"
    systemctl stop "$SERVICE_NAME"
    
    # 等待服务停止
    sleep 2
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${RED}服务停止失败，尝试强制停止...${NC}"
        systemctl kill "$SERVICE_NAME" 2>/dev/null || true
        sleep 1
        
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            echo -e "${RED}错误: 无法停止服务${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}服务停止成功${NC}"
else
    echo -e "${YELLOW}服务已经停止${NC}"
fi

# 取消开机自启（可选）
echo ""
echo -e "${YELLOW}是否取消开机自启? [y/N]${NC}"
read -t 5 -n 1 -r answer || true
echo ""

if [[ $answer =~ ^[Yy]$ ]]; then
    systemctl disable "$SERVICE_NAME" > /dev/null 2>&1
    echo -e "${GREEN}已取消开机自启${NC}"
else
    echo -e "${YELLOW}保留开机自启设置${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人服务已停止${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "服务状态: ${RED}$(systemctl is-active "$SERVICE_NAME")${NC}"
echo ""
echo -e "启动服务: ${YELLOW}sudo ./start.sh${NC}"
echo -e "查看日志: ${YELLOW}sudo tail -n 50 $LOG_FILE${NC}"
echo ""
