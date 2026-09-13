# B站视频下载工具

基于 yt-dlp 的 B站视频下载工具，提供简洁的 Web 图形界面。

## 功能

- 粘贴链接即可下载，无需命令行
- 支持 bilibili.com 和 b23.tv 短链接
- 自动选择最高画质
- 实时下载进度显示
- 下载完成后保存到浏览器默认下载目录

## 使用方法

```bash
pip install yt-dlp
python bilibili_gui.py
```

运行后浏览器会自动打开，粘贴 B站视频链接点击下载即可。

## 技术栈

- 后端：Python + yt-dlp + http.server
- 前端：原生 HTML/CSS/JS

## 依赖

- Python 3.8+
- yt-dlp
- ffmpeg（合并音视频流）

## 声明

仅供学习使用，请遵守 B站用户协议。
