#!/usr/bin/env python3
"""B站视频下载工具 - Web 图形界面版

启动后自动打开浏览器，在网页中粘贴链接即可下载。
下载完成后点击"保存到下载文件夹"，浏览器会自动保存到默认下载目录。
"""

import os
import sys
import re
import json
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote

try:
    import yt_dlp
except ImportError:
    os.system(f"{sys.executable} -m pip install yt-dlp")
    import yt_dlp

# ── 配置 ────────────────────────────────────────────────

PORT = int(os.environ.get("PORT", 7860))
HOST = os.environ.get("HOST", "0.0.0.0")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "downloads")
INDEX_HTML = os.path.join(SCRIPT_DIR, "index.html")

BILIBILI_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?(?:bilibili\.com|b23\.tv)/"
)

# 全局状态
STATUS = {
    "state": "idle",
    "progress": 0,
    "downloaded": 0,
    "total": 0,
    "speed": 0,
    "message": "",
    "video_info": None,
    "error": "",
    "file_name": "",
}

# 下载完成后记录文件名，供 /api/file 端点使用
DOWNLOADED_FILE = {"path": "", "name": ""}


def is_valid_bilibili_url(url: str) -> bool:
    return bool(BILIBILI_URL_PATTERN.match(url.strip()))


def reset_status():
    STATUS["state"] = "idle"
    STATUS["progress"] = 0
    STATUS["downloaded"] = 0
    STATUS["total"] = 0
    STATUS["speed"] = 0
    STATUS["message"] = ""
    STATUS["video_info"] = None
    STATUS["error"] = ""
    STATUS["file_name"] = ""


def progress_hook(d: dict):
    status = d.get("status")
    if status == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        downloaded = d.get("downloaded_bytes", 0)
        speed = d.get("speed", 0) or 0
        pct = (downloaded / total * 100) if total else 0
        STATUS["progress"] = round(pct, 1)
        STATUS["downloaded"] = downloaded
        STATUS["total"] = total
        STATUS["speed"] = speed
        STATUS["message"] = "下载中..."
    elif status == "finished":
        STATUS["message"] = "文件合并中..."


def cleanup_old_files():
    """清理超过 30 分钟的旧下载文件，防止磁盘爆满"""
    if not os.path.isdir(OUTPUT_DIR):
        return
    import time
    now = time.time()
    for f in os.listdir(OUTPUT_DIR):
        path = os.path.join(OUTPUT_DIR, f)
        if os.path.isfile(path) and now - os.path.getmtime(path) > 1800:
            try:
                os.remove(path)
            except OSError:
                pass


def download_worker(url: str):
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        cleanup_old_files()

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(OUTPUT_DIR, "%(title)s_%(id)s.mp4"),
            "progress_hooks": [progress_hook],
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.bilibili.com",
            },
            "quiet": True,
            "no_warnings": False,
        }

        STATUS["state"] = "fetching"
        STATUS["message"] = "正在获取视频信息..."

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration = info.get("duration", 0) or 0
            m, s = divmod(int(duration), 60)
            STATUS["video_info"] = {
                "title": info.get("title", "未知"),
                "uploader": info.get("uploader", "未知"),
                "duration": f"{m}分{s:02d}秒",
                "id": info.get("id", "未知"),
            }

            STATUS["state"] = "downloading"
            STATUS["message"] = "开始下载..."
            STATUS["progress"] = 0

            ydl.download([url])

            # 找到下载的文件
            file_name = f"{info.get('title', 'video')}_{info.get('id', '')}.mp4"
            file_path = os.path.join(OUTPUT_DIR, file_name)

            if os.path.exists(file_path):
                DOWNLOADED_FILE["path"] = file_path
                DOWNLOADED_FILE["name"] = file_name
                STATUS["file_name"] = file_name
            else:
                # 尝试在 downloads 目录找最新的 mp4
                mp4s = [
                    os.path.join(OUTPUT_DIR, f)
                    for f in os.listdir(OUTPUT_DIR)
                    if f.endswith(".mp4")
                ]
                if mp4s:
                    latest = max(mp4s, key=os.path.getmtime)
                    DOWNLOADED_FILE["path"] = latest
                    DOWNLOADED_FILE["name"] = os.path.basename(latest)
                    STATUS["file_name"] = DOWNLOADED_FILE["name"]

            STATUS["state"] = "done"
            STATUS["progress"] = 100
            STATUS["message"] = "下载完成，点击下方按钮保存到下载文件夹"

    except yt_dlp.utils.DownloadError as e:
        STATUS["state"] = "error"
        STATUS["error"] = str(e)
        STATUS["message"] = "下载失败"
    except Exception as e:
        STATUS["state"] = "error"
        STATUS["error"] = str(e)
        STATUS["message"] = "下载失败"


# ── HTTP 服务 ────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._serve_html()

        elif parsed.path == "/api/status":
            self._send_json({
                "state": STATUS["state"],
                "progress": STATUS["progress"],
                "downloaded": STATUS["downloaded"],
                "total": STATUS["total"],
                "speed": STATUS["speed"],
                "message": STATUS["message"],
                "video_info": STATUS["video_info"],
                "error": STATUS["error"],
                "file_name": STATUS["file_name"],
            })

        elif parsed.path == "/api/file":
            qs = parse_qs(parsed.query)
            name = qs.get("name", [""])[0]
            file_path = DOWNLOADED_FILE.get("path", "")
            if not file_path or not os.path.exists(file_path):
                self._send_json({"error": "文件不存在"}, 404)
                return

            file_size = os.path.getsize(file_path)
            fname_encoded = quote(os.path.basename(file_path))
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Disposition",
                             f"attachment; filename*=UTF-8''{fname_encoded}")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Connection", "close")
            self.end_headers()

            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/download":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._send_json({"error": "无效的请求"}, 400)
                return

            url = data.get("url", "").strip()
            if not url:
                self._send_json({"error": "链接不能为空"}, 400)
                return
            if not is_valid_bilibili_url(url):
                self._send_json({"error": "请输入有效的 B站链接"}, 400)
                return
            if STATUS["state"] in ("fetching", "downloading"):
                self._send_json({"error": "已有下载任务进行中，请等待完成"}, 400)
                return

            reset_status()
            thread = threading.Thread(target=download_worker, args=(url,), daemon=True)
            thread.start()

            self._send_json({"ok": True})

        else:
            self.send_error(404)

    def _serve_html(self):
        try:
            with open(INDEX_HTML, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            content = "<h1>index.html not found</h1>"

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _send_json(self, data: dict, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{'localhost' if HOST == '127.0.0.1' else HOST}:{PORT}"

    print(f"B站视频下载工具已启动！")
    print(f"请在浏览器中访问：{url}")
    print(f"按 Ctrl+C 退出程序")
    print(f"下载文件临时目录：{OUTPUT_DIR}")

    # 仅本地模式自动打开浏览器
    if HOST == "127.0.0.1":
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已退出。")
        server.shutdown()


if __name__ == "__main__":
    main()
