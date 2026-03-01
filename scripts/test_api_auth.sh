#!/bin/bash
# API认证测试脚本
# 测试Nginx Bearer Token认证是否正常工作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
API_URL="http://119.28.50.67/agent"
VALID_TOKEN="Bearer 06d56890c91f19135e6d8020e8448a35b31cb9b7cedd7da2842f0616ccadeac4"
TEST_PAYLOAD='{"prompt":"test"}'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   API 认证测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 测试1: 无Token访问
echo -e "${YELLOW}测试1: 无Authorization头访问${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "$TEST_PAYLOAD")

if [ "$HTTP_CODE" == "401" ]; then
    echo -e "${GREEN}✓ 通过: 返回401 Unauthorized${NC}"
else
    echo -e "${RED}✗ 失败: 期望401, 实际返回$HTTP_CODE${NC}"
    exit 1
fi
echo ""

# 测试2: 错误Token访问
echo -e "${YELLOW}测试2: 使用错误Token访问${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer wrong_token_12345" \
    -d "$TEST_PAYLOAD")

if [ "$HTTP_CODE" == "401" ]; then
    echo -e "${GREEN}✓ 通过: 返回401 Unauthorized${NC}"
else
    echo -e "${RED}✗ 失败: 期望401, 实际返回$HTTP_CODE${NC}"
    exit 1
fi
echo ""

# 测试3: 正确Token访问
echo -e "${YELLOW}测试3: 使用正确Token访问${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: $VALID_TOKEN" \
    -d "$TEST_PAYLOAD")

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ 通过: 返回200 OK${NC}"
else
    echo -e "${RED}✗ 失败: 期望200, 实际返回$HTTP_CODE${NC}"
    exit 1
fi
echo ""

# 测试4: Token格式错误（缺少Bearer前缀）
echo -e "${YELLOW}测试4: Token缺少Bearer前缀${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -H "Authorization: 06d56890c91f19135e6d8020e8448a35b31cb9b7cedd7da2842f0616ccadeac4" \
    -d "$TEST_PAYLOAD")

if [ "$HTTP_CODE" == "401" ]; then
    echo -e "${GREEN}✓ 通过: 返回401 Unauthorized${NC}"
else
    echo -e "${RED}✗ 失败: 期望401, 实际返回$HTTP_CODE${NC}"
    exit 1
fi
echo ""

# 测试5: 完整响应测试
echo -e "${YELLOW}测试5: 检查401响应体${NC}"
RESPONSE=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "$TEST_PAYLOAD")

if echo "$RESPONSE" | grep -q "Unauthorized"; then
    echo -e "${GREEN}✓ 通过: 响应包含Unauthorized消息${NC}"
    echo -e "${BLUE}响应内容: $RESPONSE${NC}"
else
    echo -e "${RED}✗ 失败: 响应不包含Unauthorized消息${NC}"
    exit 1
fi
echo ""

# 汇总
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   所有测试通过! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}认证保护工作正常:${NC}"
echo -e "  - 无Token访问: ${RED}拒绝${NC}"
echo -e "  - 错误Token访问: ${RED}拒绝${NC}"
echo -e "  - 正确Token访问: ${GREEN}允许${NC}"
echo -e "  - 格式错误Token: ${RED}拒绝${NC}"
echo ""
