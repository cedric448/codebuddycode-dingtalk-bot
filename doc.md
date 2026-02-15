Codebuddy接钉钉机器人用户手册
测试时间：2026-2-15日

基于 dingtalk-stream SDK 实现的钉钉机器人，集成 CodeBuddy HTTP API，支持 Stream 模式、群聊/单聊、Markdown 格式回复。

目录
1.功能特性
2.系统要求
3.快速安装
4.钉钉配置
5.服务管理
6.使用指南
7.故障排查
8.常见问题
9.高级配置
10.安全建议

功能特性
●✅ Stream 模式：基于 WebSocket 的实时消息推送
●✅ 群聊支持：支持 @机器人 进行群聊互动
●✅ 单聊支持：支持一对一私聊
●✅ Markdown 格式：支持富文本格式回复
●✅ 长消息分割：自动处理超过 20000 字符的长消息
●✅ Systemd 服务：支持系统服务管理，开机自启
●✅ 日志管理：完整的日志记录和轮转

系统要求
●操作系统：Linux (CentOS 7+, Ubuntu 18.04+, TencentOS 等)
●Python：3.8 或更高版本
●内存：最低 256MB，推荐 512MB
●网络：能够访问钉钉服务器和 CodeBuddy API

快速安装
1. 克隆/下载项目

cd /root/project-wb/dingtalk-bot

2. 安装依赖

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

3. 配置环境变量

# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
vim .env

编辑以下内容：
# 钉钉机器人配置（从钉钉开放平台获取）
DINGTALK_CLIENT_ID=your_client_id_here
DINGTALK_CLIENT_SECRET=your_client_secret_here

# CodeBuddy HTTP API 配置
CODEBUDDY_API_URL=http://your-codebuddy-server/agent
CODEBUDDY_API_TOKEN=your_api_token_here

# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
4. 安装 Systemd 服务

# 复制服务文件
sudo cp dingtalk-bot.service /etc/systemd/system/

# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start dingtalk-bot

# 设置开机自启
sudo systemctl enable dingtalk-bot

5. 验证安装

# 查看服务状态
sudo systemctl status dingtalk-bot

# 查看实时日志
sudo tail -f /var/log/dingtalk-bot.log


钉钉配置
步骤 1：创建企业内部应用
1.登录 https://open.dingtalk.com/ 
2.点击右上角 "开发者后台"
3.选择你的企业组织
4.点击 "应用开发" → "企业内部应用"
5.点击 "创建应用"
步骤 2：填写应用信息
●应用名称：CodeBuddy Assistant（或自定义）
●应用描述：AI 助手，基于 CodeBuddy 提供智能问答服务
●应用图标：上传你的应用图标
●开发方式：企业自助开发
步骤 3：配置机器人
1.在应用详情页，点击左侧 "机器人"
2.打开 "机器人" 开关
3.配置机器人：
●消息接收模式：选择 "Stream 模式"（重要！）
●机器人名称：CodeBuddy Bot
●描述：智能 AI 助手
步骤 4：获取凭证
1.点击左侧 "凭证与基础信息"
2.复制以下信息：
●Client ID (原 AppKey)
●Client Secret (原 AppSecret)
3.将这些信息填入 .env 文件的对应位置
步骤 5：发布应用
1.点击左侧 "版本管理与发布"
2.点击 "创建新版本"
3.填写版本信息：
●版本号：1.0.0
●版本描述：初始版本
4.点击 "保存" → "发布"
步骤 6：添加应用到企业
1.在 "版本管理与发布" 页面
2.点击 "添加应用至企业"
3.选择需要使用机器人的部门
4.点击 "确定"
步骤 7：群聊配置（可选）
如果需要在群聊中使用：
1.打开目标群聊
2.点击右上角 "群设置"（齿轮图标）
3.选择 "智能群助手"
4.点击 "添加机器人"
5.选择 "CodeBuddy Assistant"
6.点击 "确定"

服务管理
启动服务

sudo systemctl start dingtalk-bot

停止服务

sudo systemctl stop dingtalk-bot

重启服务

sudo systemctl restart dingtalk-bot

查看状态

sudo systemctl status dingtalk-bot

启用开机自启

sudo systemctl enable dingtalk-bot

禁用开机自启

sudo systemctl disable dingtalk-bot

查看日志

# 实时查看日志
sudo tail -f /var/log/dingtalk-bot.log

# 查看最近 100 行
sudo tail -n 100 /var/log/dingtalk-bot.log

# 查看完整日志
sudo cat /var/log/dingtalk-bot.log

日志轮转
日志文件会自动轮转，当文件大小超过 10MB 时会自动创建新文件，保留最近 7 天的日志。

使用指南
单聊使用
1.在钉钉中搜索 "CodeBuddy Assistant"（或你的应用名称）
2.进入聊天窗口
3.直接发送消息，例如：
●"你好"
●"2+2等于几"
●"帮我写一段 Python 代码"
群聊使用
1.在已添加机器人的群聊中
2.@机器人 并发送消息，例如：
●"@CodeBuddy Bot 你好"
●"@CodeBuddy Bot 解释一下什么是人工智能"
消息格式
机器人支持 Markdown 格式回复，包括：
●粗体
●斜体
●代码块
●http://example.com 列表
●引用

故障排查
服务无法启动
现象：systemctl start dingtalk-bot 失败
排查步骤：
1.检查配置文件

cat /root/project-wb/dingtalk-bot/.env

确保 DINGTALK_CLIENT_ID 和 DINGTALK_CLIENT_SECRET 已正确填写
2.检查日志

sudo tail -n 50 /var/log/dingtalk-bot.log

3.手动测试运行

cd /root/project-wb/dingtalk-bot
source venv/bin/activate
python bot.py

收不到消息
现象：在钉钉发送消息，机器人没有响应
排查步骤：
1.检查服务状态

sudo systemctl status dingtalk-bot

2.检查网络连接

curl -I https://api.dingtalk.com

3.检查钉钉应用配置
●确认应用已发布
●确认机器人已启用 Stream 模式
●确认应用已添加到企业
4.检查日志中的错误信息

sudo tail -f /var/log/dingtalk-bot.log

CodeBuddy API 调用失败
现象：收到消息但无回复，日志显示 API 错误
排查步骤：
1.检查 API 配置

grep CODEBUDDY /root/project-wb/dingtalk-bot/.env

2.测试 API 连通性

curl -X POST http://your-codebuddy-server/agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"prompt": "test", "print": true}'

3.检查网络访问

ping your-codebuddy-server

消息发送失败
现象：处理消息成功但用户收不到回复
排查步骤：
1.检查日志中的 webhook 错误
2.确认 session_webhook 可用
3.检查消息长度是否超过限制

常见问题
Q: 机器人响应很慢怎么办？
A: 响应速度取决于 CodeBuddy API 的处理速度。可以：
1.检查 CodeBuddy 服务器性能
2.查看网络延迟
3.考虑使用更快的网络连接
Q: 如何修改消息长度限制？
A: 编辑 config.py 文件：

MAX_MESSAGE_LENGTH = 20000  # 修改为需要的值

然后重启服务：

sudo systemctl restart dingtalk-bot

Q: 如何修改日志级别？
A: 编辑 .env 文件：
LOG_LEVEL=DEBUG  # 可选：DEBUG, INFO, WARNING, ERROR
然后重启服务。
Q: 如何更新机器人代码？
A:

# 停止服务
sudo systemctl stop dingtalk-bot

# 更新代码
# ... 你的更新操作 ...

# 启动服务
sudo systemctl start dingtalk-bot

Q: 一个机器人可以在多个群使用吗？
A: 可以。只需要在每个群中添加同一个机器人即可。
Q: 如何查看当前有哪些用户在使用机器人？
A: 查看日志文件：

sudo grep "收到消息" /var/log/dingtalk-bot.log

Q: 机器人支持图片和文件吗？
A: 当前版本仅支持文本消息。图片和文件支持正在开发中。

高级配置
自定义消息处理
编辑 bot.py 中的 ChatbotHandlerImpl 类，可以添加自定义的消息处理逻辑：

async def process(self, callback: CallbackMessage) -> AckMessage:
    # 在这里添加自定义逻辑
    # 例如：消息过滤、关键词回复等
    pass

添加命令支持
可以添加特定的命令处理：

def _handle_command(self, message: ChatbotMessage, content: str) -> str:
    if content.startswith("/help"):
        return "帮助信息..."
    elif content.startswith("/status"):
        return "当前状态..."
    return None

接入其他 AI 服务
修改 codebuddy_client.py，可以接入其他 AI API：

def stream_chat(self, prompt: str) -> Generator[str, None, None]:
    # 在这里接入其他 AI 服务
    pass


安全建议
1. 保护凭证信息
●不要将 .env 文件提交到版本控制
●定期更换 Client Secret
●限制服务器访问权限
2. 网络安全
●使用防火墙限制不必要的端口访问
●考虑使用 HTTPS 代理 CodeBuddy API
●定期检查服务器安全更新
3. 日志安全
●定期清理旧日志
●不要在日志中记录敏感信息
●限制日志文件访问权限

# 设置日志文件权限
sudo chmod 640 /var/log/dingtalk-bot.log

4. 服务安全
●使用专用用户运行服务（而非 root）
●定期更新依赖包
●监控服务异常行为

技术支持
钉钉开放平台文档
●https://open.dingtalk.com/ 
●https://open.dingtalk.com/document/isvapp-server/stream-introduction 
项目相关
●dingtalk-stream SDK: https://github.com/open-dingtalk/dingtalk-stream-sdk-python 
日志位置
●应用日志：/var/log/dingtalk-bot.log
●项目日志：/root/project-wb/dingtalk-bot/logs/dingtalk_bot.log

更新日志
v1.0.0 (2026-02-15)
●初始版本发布
●支持 Stream 模式
●支持群聊和单聊
●支持 Markdown 格式
●集成 Systemd 服务

文档版本: 1.0.0
最后更新: 2026-02-15
维护者: CodeBuddy Team


