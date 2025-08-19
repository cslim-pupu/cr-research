# HTML源代码版权分析器

一个专门用于分析微信文章HTML源代码中版权信息的Web应用工具。

## 功能特点

- 🔍 **智能版权检测**: 自动识别HTML源代码中的版权信息
- 👤 **开发者识别**: 检测页面开发者和作者信息
- 📊 **置信度评估**: 提供分析结果的可信度评分
- 🌐 **Web界面**: 简洁易用的网页操作界面
- ⚡ **快速分析**: 支持微信文章链接快速分析

## 支持的版权属性

- `copyright` - 版权声明
- `author` - 作者信息
- `creator` - 创建者
- `owner` - 所有者
- `powered-by` - 技术支持方
- `data-copyright` - 数据版权
- `data-cpy` - 版权缩写
- `name` - 名称属性
- 以及更多HTML注释中的版权信息

## 快速开始

### 方法一：使用启动脚本（推荐）

**Mac/Linux用户：**
```bash
# 给脚本执行权限
chmod +x start.sh

# 运行启动脚本
./start.sh
```

**Windows用户：**
```cmd
# 双击运行或在命令行执行
start.bat
```

### 方法二：手动启动

1. **安装Python依赖**
   ```bash
   # 创建虚拟环境
   python3 -m venv venv
   
   # 激活虚拟环境
   # Mac/Linux:
   source venv/bin/activate
   # Windows:
   venv\Scripts\activate
   
   # 安装依赖
   pip install -r requirements.txt
   ```

2. **启动应用**
   ```bash
   python web_app.py
   ```

3. **访问应用**
   - 打开浏览器访问: http://localhost:8080
   - 或访问: http://127.0.0.1:8080

## 使用方法

1. 在浏览器中打开应用
2. 输入微信文章链接（如：https://mp.weixin.qq.com/s/xxxxx）
3. 点击"开始分析"按钮
4. 查看详细的分析结果

## 分析结果说明

- **主要作者**: 识别出的主要开发者或作者
- **所有作者**: 所有检测到的作者信息
- **版权持有者**: 检测到的版权相关信息
- **整体置信度**: 分析结果的可信度（0.0-1.0）

## 系统要求

- Python 3.7 或更高版本
- Chrome浏览器（用于动态内容抓取）
- 网络连接（用于访问微信文章）

## 依赖包

- Flask - Web框架
- BeautifulSoup4 - HTML解析
- Selenium - 动态内容抓取
- Requests - HTTP请求
- Loguru - 日志记录

## 注意事项

- 首次运行会自动下载Chrome驱动程序
- 分析过程可能需要几秒钟时间
- 确保网络连接正常
- 支持大部分微信公众号文章链接

## 故障排除

**问题：无法访问微信文章**
- 检查网络连接
- 确认链接格式正确
- 尝试在浏览器中手动打开链接

**问题：Chrome驱动错误**
- 确保已安装Chrome浏览器
- 程序会自动下载匹配的驱动版本

**问题：依赖安装失败**
- 确保Python版本≥3.7
- 尝试升级pip: `pip install --upgrade pip`
- 使用国内镜像: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`

## 技术支持

如有问题，请检查：
1. Python版本是否符合要求
2. 所有依赖是否正确安装
3. 网络连接是否正常
4. Chrome浏览器是否已安装

---

**版本**: 1.0.0  
**更新时间**: 2025年1月