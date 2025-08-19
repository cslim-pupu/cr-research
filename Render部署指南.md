# 🚀 Render部署指南 - HTML版权分析器

本指南将帮助您将HTML源代码版权分析器部署到Render平台，**完全免费**使用。

## 📋 部署前准备

### 1. 注册GitHub账号
- 访问 https://github.com
- 注册并创建账号

### 2. 上传代码到GitHub
```bash
# 在项目目录下执行
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

### 3. 注册Render账号
- 访问 https://render.com
- 使用GitHub账号登录（推荐）

## 🛠️ 部署步骤

### 步骤1：创建Web Service
1. 登录Render控制台
2. 点击 **"New +"** 按钮
3. 选择 **"Web Service"**

### 步骤2：连接GitHub仓库
1. 选择 **"Build and deploy from a Git repository"**
2. 点击 **"Connect"** 连接您的GitHub账号
3. 选择包含代码的仓库
4. 点击 **"Connect"**

### 步骤3：配置部署设置

**基本设置：**
- **Name:** `html-copyright-analyzer`（或您喜欢的名称）
- **Region:** 选择离您最近的区域
- **Branch:** `main`
- **Root Directory:** 留空

**构建设置：**
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn --bind 0.0.0.0:$PORT web_app:app`

**计划设置：**
- **Instance Type:** 选择 **"Free"**

### 步骤4：环境变量（可选）
如果需要，可以添加环境变量：
- `PYTHON_VERSION`: `3.11`

### 步骤5：部署
1. 点击 **"Create Web Service"**
2. 等待部署完成（通常需要5-10分钟）
3. 部署成功后，您将获得一个免费的URL

## 🔗 获取访问链接

部署成功后：
1. 在Render控制台找到您的服务
2. 复制提供的URL（格式：`https://your-app-name.onrender.com`）
3. 分享给同事使用

## ✅ 验证部署

访问您的应用URL，确认：
- ✅ 页面正常加载
- ✅ 可以输入URL进行分析
- ✅ 分析结果正确显示

## 🔄 自动更新

**优势：** 每次您向GitHub推送代码时，Render会自动重新部署

```bash
# 更新代码后
git add .
git commit -m "更新功能"
git push
# Render会自动检测并重新部署
```

## 💤 休眠机制说明

**免费版特点：**
- 🕐 15分钟无访问自动休眠
- 🚀 访问时自动唤醒（15-30秒）
- 💾 数据和配置不丢失
- 🆓 完全免费使用

## 🛠️ 故障排除

### 部署失败
**可能原因：**
- requirements.txt格式错误
- Python版本不兼容
- 启动命令错误

**解决方案：**
1. 检查构建日志
2. 确认所有文件已上传到GitHub
3. 验证requirements.txt中的包版本

### 应用无法访问
**检查项目：**
- ✅ 部署状态是否为"Live"
- ✅ 健康检查是否通过
- ✅ 启动命令是否正确

### 功能异常
**调试步骤：**
1. 查看Render日志
2. 检查环境变量配置
3. 验证代码在本地是否正常运行

## 📊 监控和管理

### 查看日志
1. 进入Render控制台
2. 选择您的服务
3. 点击"Logs"标签页

### 重新部署
1. 在服务页面点击"Manual Deploy"
2. 选择"Deploy latest commit"

### 暂停服务
1. 在服务设置中
2. 点击"Suspend"（需要时可重新启用）

## 🎯 使用建议

**适合场景：**
- ✅ 个人项目分享
- ✅ 团队内部工具
- ✅ 偶尔使用的分析工具
- ✅ 演示和测试

**不适合场景：**
- ❌ 高频访问的生产应用
- ❌ 需要实时响应的服务
- ❌ 大量并发用户

## 📞 获取帮助

**Render官方资源：**
- 📖 文档：https://render.com/docs
- 💬 社区：https://community.render.com
- 📧 支持：通过控制台提交工单

**常见问题：**
- 部署时间较长是正常现象
- 免费版有资源限制，但足够个人使用
- 休眠后首次访问需要等待唤醒

---

🎉 **恭喜！** 您的HTML版权分析器现在已经在线运行，可以随时随地使用了！