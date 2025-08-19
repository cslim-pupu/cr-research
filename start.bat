@echo off
chcp 65001 >nul

echo 正在启动HTML源代码版权分析器...
echo 请确保已安装Python 3.7+
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt

REM 启动应用
echo 启动Web应用...
echo 应用将在以下地址运行:
echo   - http://localhost:8080
echo   - http://127.0.0.1:8080
echo.
echo 按 Ctrl+C 停止应用
echo ==========================================
echo.

python web_app.py

pause