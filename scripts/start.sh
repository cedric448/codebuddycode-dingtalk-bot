#!/bin/bash
# 钉钉机器人一键启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="/root/project-wb/dingtalk_bot"
SERVICE_NAME="dingtalk-bot"
LOG_FILE="/var/log/dingtalk-bot.log"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人服务启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用 root 权限运行此脚本${NC}"
    echo "用法: sudo ./start.sh"
    exit 1
fi

# 检查项目目录是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}错误: 项目目录不存在: $PROJECT_DIR${NC}"
    exit 1
fi

cd "$PROJECT_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}虚拟环境创建成功${NC}"
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${RED}错误: 配置文件 .env 不存在${NC}"
    echo -e "请复制 .env.example 到 .env 并配置相关参数:"
    echo -e "  cp .env.example .env"
    echo -e "  vim .env"
    exit 1
fi

# 检查 systemd 服务文件
if [ ! -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    echo -e "${YELLOW}Systemd 服务文件不存在，正在安装...${NC}"
    cp "systemd/${SERVICE_NAME}.service" /etc/systemd/system/
    systemctl daemon-reload
    echo -e "${GREEN}Systemd 服务文件安装成功${NC}"
fi

# 检查日志目录
if [ ! -d "/var/log" ]; then
    mkdir -p /var/log
fi

if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
fi

# 检查图片目录
if [ ! -d "images" ]; then
    echo -e "${YELLOW}创建图片存储目录...${NC}"
    mkdir -p images
    echo -e "${GREEN}图片目录创建成功${NC}"
fi

# 激活虚拟环境并安装依赖
echo -e "${YELLOW}检查并安装依赖...${NC}"
source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}依赖检查完成${NC}"

# 检查服务状态
echo ""
echo -e "${YELLOW}检查服务状态...${NC}"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${YELLOW}服务已在运行，正在重启...${NC}"
    systemctl restart "$SERVICE_NAME"
    echo -e "${GREEN}服务重启成功${NC}"
else
    echo -e "${YELLOW}服务未运行，正在启动...${NC}"
    systemctl start "$SERVICE_NAME"
    echo -e "${GREEN}服务启动成功${NC}"
fi

# 设置开机自启
echo -e "${YELLOW}设置开机自启...${NC}"
systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
echo -e "${GREEN}开机自启设置成功${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   钉钉机器人服务启动完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "服务状态: ${GREEN}$(systemctl is-active "$SERVICE_NAME")${NC}"
echo -e "服务PID:  ${GREEN}$(systemctl show --property=MainPID --value "$SERVICE_NAME")${NC}"
echo ""
echo -e "查看日志: ${YELLOW}sudo tail -f $LOG_FILE${NC}"
echo -e "查看状态: ${YELLOW}sudo systemctl status $SERVICE_NAME${NC}"
echo -e "停止服务: ${YELLOW}sudo ./stop.sh${NC}"
echo ""
