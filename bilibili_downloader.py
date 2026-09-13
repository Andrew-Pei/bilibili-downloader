#!/usr/bin/env python3
"""B站视频下载工具 - 基于 yt-dlp 实现"""

import sys
import os
import re

try:
    import yt_dlp
except ImportError:
    print("缺少依赖 yt-dlp，正在自动安装...")
    os.system(f"{sys.executable} -m pip install yt-dlp")
    import yt_dlp


# B站链接校验正则
BILIBILI_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?(?:bilibili\.com|b23\.tv)/"
)


def is_valid_bilibili_url(url: str) -> bool:
    """检查是否为合法的 B站链接"""
    return bool(BILIBILI_URL_PATTERN.match(url.strip()))


class ProgressLogger:
    """自定义下载进度日志"""

    def debug(self, msg):
        pass

    def warning(self, msg):
        print(f"  [警告] {msg}")

    def error(self, msg):
        print(f"  [错误] {msg}")

    def info(self, msg):
        print(f"  [信息] {msg}")


def download_video(url: str, output_dir: str = "downloads") -> None:
    """下载 B站视频

    Args:
        url: B站视频链接
        output_dir: 下载目录
    """
    if not is_valid_bilibili_url(url):
        print("错误：请输入有效的 B站链接（以 https://www.bilibili.com 或 https://b23.tv 开头）")
        return

    os.makedirs(output_dir, exist_ok=True)

    # 提取视频信息（标题、UP主等）
    print("=" * 50)
    print("正在获取视频信息...")
    print("=" * 50)

    ydl_opts = {
        # 下载最佳画质：mp4 优先，1080p 及以上
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        # 输出文件名格式：标题_视频ID.mp4
        "outtmpl": os.path.join(output_dir, "%(title)s.mp4"),
        # 进度日志
        "logger": ProgressLogger(),
        # 显示进度条
        "progress_hooks": [progress_hook],
        # 使用中文
        "writesubtitles": False,
        # 模拟浏览器请求头
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com",
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 先提取视频信息
            info = ydl.extract_info(url, download=False)
            print(f"\n  视频标题：{info.get('title', '未知')}")
            print(f"  UP主：{info.get('uploader', '未知')}")
            print(f"  时长：{info.get('duration', 0)} 秒")
            print(f"  视频ID：{info.get('id', '未知')}")
            print()

            # 开始下载
            print("=" * 50)
            print("开始下载...")
            print("=" * 50)
            ydl.download([url])

            print("\n下载完成！文件已保存到目录："
                  f"{os.path.abspath(output_dir)}")

    except yt_dlp.utils.DownloadError as e:
        print(f"\n下载失败：{e}")
        print("\n可能的原因：")
        print("  1. 视频链接无效或已被删除")
        print("  2. 需要登录才能访问的内容（请在浏览器中登录 B站后重试）")
        print("  3. 网络连接问题")
    except Exception as e:
        print(f"\n发生未知错误：{e}")


def progress_hook(d: dict) -> None:
    """下载进度回调"""
    status = d.get("status")

    if status == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        downloaded = d.get("downloaded_bytes", 0)
        speed = d.get("speed", 0)
        percentage = (downloaded / total * 100) if total else 0

        # 格式化文件大小
        def fmt_size(n):
            for unit in ["B", "KB", "MB", "GB"]:
                if n < 1024:
                    return f"{n:.1f}{unit}"
                n /= 1024
            return f"{n:.1f}TB"

        speed_str = fmt_size(speed) + "/s" if speed else "--"
        total_str = fmt_size(total) if total else "未知"
        downloaded_str = fmt_size(downloaded)

        # 进度条
        bar_length = 30
        filled = int(bar_length * percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)

        print(f"\r  [{bar}] {percentage:.1f}% | "
              f"{downloaded_str}/{total_str} | {speed_str}", end="")

    elif status == "finished":
        print(f"\n  [完成] 文件合并中...")


def main():
    """主程序入口"""
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║         B站视频下载工具 v1.0                  ║")
    print("║         基于 yt-dlp 开源项目                  ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    # 从命令行参数获取链接
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("请输入 B站视频链接：").strip()

    if not url:
        print("错误：链接不能为空")
        return

    # 可选：自定义下载目录
    output_dir = "downloads"
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]

    download_video(url, output_dir)


if __name__ == "__main__":
    main()
