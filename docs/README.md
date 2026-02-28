# 文档目录

本目录包含钉钉机器人项目的所有文档，按类别组织。

## 📁 目录结构

### 🚀 [deployment/](deployment/) - 部署文档
部署相关的配置和说明文档

- [IMAGE_SERVER_DEPLOYMENT.md](deployment/IMAGE_SERVER_DEPLOYMENT.md) - 图片服务器部署指南
- [IMAGE_SERVER_FIX.md](deployment/IMAGE_SERVER_FIX.md) - 图片服务器和API代理配置修复

### 🔧 [troubleshooting/](troubleshooting/) - 故障排查
问题诊断和修复记录

- [BUGFIX.md](troubleshooting/BUGFIX.md) - Bug修复记录
- [BUGFIX_IMAGE_RESPONSE.md](troubleshooting/BUGFIX_IMAGE_RESPONSE.md) - 图片响应修复
- [BUGFIX_MESSAGE_DEDUPLICATION.md](troubleshooting/BUGFIX_MESSAGE_DEDUPLICATION.md) - 消息去重修复
- [IMAGE_SEND_ISSUE.md](troubleshooting/IMAGE_SEND_ISSUE.md) - 图片发送问题
- [TROUBLESHOOTING.md](troubleshooting/TROUBLESHOOTING.md) - 常见问题排查指南

### ✨ [features/](features/) - 功能文档
各项功能的详细说明

- [ASYNC_FEATURE.md](features/ASYNC_FEATURE.md) - 异步任务处理功能
- [IMAGE_GENERATION_README.md](features/IMAGE_GENERATION_README.md) - 图片生成功能
- [MARKDOWN_SUPPORT.md](features/MARKDOWN_SUPPORT.md) - Markdown消息支持

### 🧪 [testing/](testing/) - 测试文档
测试指南和测试结果

- [TEST_ASYNC.md](testing/TEST_ASYNC.md) - 异步功能测试
- [TEST_DEDUPLICATION_RESULT.md](testing/TEST_DEDUPLICATION_RESULT.md) - 消息去重测试结果
- [TEST_MARKDOWN.md](testing/TEST_MARKDOWN.md) - Markdown功能测试
- [TEST_RESULTS.md](testing/TEST_RESULTS.md) - 综合测试结果
- [TESTING_GUIDE.txt](testing/TESTING_GUIDE.txt) - 测试指南
- [TESTING_IMAGE_GEN.md](testing/TESTING_IMAGE_GEN.md) - 图片生成测试

### 🏗️ [architecture/](architecture/) - 架构文档
系统架构和设计文档

- [ARCHITECTURE.md](architecture/ARCHITECTURE.md) - 系统架构说明
- [CONFIG.md](architecture/CONFIG.md) - 配置详细说明
- [DEPLOYMENT_SUMMARY.md](architecture/DEPLOYMENT_SUMMARY.md) - 部署总结
- [MARKDOWN_DEPLOYMENT.md](architecture/MARKDOWN_DEPLOYMENT.md) - Markdown功能部署
- [MARKDOWN_IMPLEMENTATION.md](architecture/MARKDOWN_IMPLEMENTATION.md) - Markdown实现细节
- [PROJECT_SUMMARY.md](architecture/PROJECT_SUMMARY.md) - 项目总结

## 📖 快速导航

### 新手入门
1. 先看项目根目录的 [README.md](../README.md) 了解项目概况
2. 查看 [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md) 理解系统架构
3. 按照 [deployment/IMAGE_SERVER_DEPLOYMENT.md](deployment/IMAGE_SERVER_DEPLOYMENT.md) 进行部署

### 功能使用
- **异步任务**: [features/ASYNC_FEATURE.md](features/ASYNC_FEATURE.md)
- **图片生成**: [features/IMAGE_GENERATION_README.md](features/IMAGE_GENERATION_README.md)
- **Markdown支持**: [features/MARKDOWN_SUPPORT.md](features/MARKDOWN_SUPPORT.md)

### 遇到问题
1. 先查看 [troubleshooting/TROUBLESHOOTING.md](troubleshooting/TROUBLESHOOTING.md)
2. 查看相关的BUGFIX文档了解已知问题
3. 参考测试文档进行验证

### 测试验证
- 按照 [testing/TESTING_GUIDE.txt](testing/TESTING_GUIDE.txt) 进行全面测试
- 查看各功能的测试文档了解测试方法

## 🔄 文档更新

文档会随着项目迭代持续更新，请以最新版本为准。

- 文档版本: 1.2.0
- 最后更新: 2026-03-01
