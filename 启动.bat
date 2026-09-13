@echo off
title B站视频下载工具

echo ========================================
echo    B站视频下载工具 - 正在启动...
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+ 并添加到 PATH
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

python -c "import yt_dlp" >nul 2>&1
if errorlevel 1 (
    echo [信息] 首次使用，正在安装依赖 yt-dlp...
    python -m pip install yt-dlp
    echo.
)

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [提示] 未检测到 ffmpeg，高清视频合并需要它
    echo 下载地址：https://ffmpeg.org/download.html
    echo.
)

echo [成功] 正在打开浏览器...
echo.

python "%~dp0bilibili_gui.py"

pause
