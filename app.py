import logging
import re
import shutil
import tempfile
from urllib.parse import urlparse

import imageio_ffmpeg
import yt_dlp
from flask import Flask, jsonify, render_template, request, send_file

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}',
)
logger = logging.getLogger("yt-downloader")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024  # request bodies are tiny

ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}
QUALITIES = {"2160", "1440", "1080", "720", "480", "360", "240", "144"}
VIDEO_ID_RE = re.compile(r"[\w-]{11}")
MAX_DURATION_SECONDS = 60 * 60  # 1 hour
MAX_FILESIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB
FFMPEG_PATH = shutil.which("ffmpeg")
if not FFMPEG_PATH:
    try:
        FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()  # bundled binary
    except Exception:
        FFMPEG_PATH = None
HAS_FFMPEG = FFMPEG_PATH is not None


def is_valid_youtube_url(url: str) -> bool:
    if not url or len(url) > 2048:
        return False
    parsed = urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in ALLOWED_HOSTS


def format_selector(quality: str) -> str:
    if HAS_FFMPEG:
        # Separate video+audio streams are merged into MP4 by ffmpeg
        return (
            f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]"
            f"/best[height<={quality}][ext=mp4]/best[height<={quality}]"
        )
    # Without ffmpeg only pre-merged (progressive) MP4 files can be used
    return f"best[height<={quality}][ext=mp4]/best[height<={quality}]"


@app.get("/")
def index():
    return render_template("index.html", has_ffmpeg=HAS_FFMPEG)


@app.post("/api/preview")
def preview():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()

    if not is_valid_youtube_url(url):
        return jsonify(error="Please enter a valid YouTube video URL."), 400

    opts = {
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        video_id = str((info or {}).get("id", ""))
        if not VIDEO_ID_RE.fullmatch(video_id):
            raise ValueError("bad video id")
    except Exception:
        logger.error("Preview failed", exc_info=True)
        return jsonify(error="Could not load this video. It may be unavailable or private."), 500

    duration = info.get("duration") or 0
    if duration > MAX_DURATION_SECONDS:
        return jsonify(error="This video is too long (limit is 1 hour)."), 400

    return jsonify(
        title=str(info.get("title", "video"))[:200],
        duration=int(duration),
        thumbnail=f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
    )


@app.post("/api/download")
def download():
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    quality = str(data.get("quality", "720"))

    if not is_valid_youtube_url(url):
        return jsonify(error="Please enter a valid YouTube video URL."), 400
    if quality not in QUALITIES:
        return jsonify(error="Invalid quality option."), 400

    tmp_dir = tempfile.mkdtemp(prefix="ytdl_")
    opts = {
        "format": format_selector(quality),
        "merge_output_format": "mp4",
        "outtmpl": f"{tmp_dir}/%(id)s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        "ffmpeg_location": FFMPEG_PATH,
        "max_filesize": MAX_FILESIZE_BYTES,
        "match_filter": yt_dlp.utils.match_filter_func(
            f"duration <= {MAX_DURATION_SECONDS}"
        ),
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("no info")
            path = ydl.prepare_filename(info)
            if HAS_FFMPEG and not path.endswith(".mp4"):
                path = re.sub(r"\.[^.]+$", ".mp4", path)
        title = re.sub(r"[^\w\- ]+", "", info.get("title", "video")).strip() or "video"
        filename = f"{title[:80]}_{quality}p.mp4"
        if not path.endswith(".mp4"):
            raise ValueError("not mp4")
    except Exception:
        logger.error("Download failed", exc_info=True)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return (
            jsonify(
                error="Could not download this video. It may be unavailable, "
                "too long, too large, or the selected quality is not supported."
            ),
            500,
        )

    response = send_file(path, mimetype="video/mp4", as_attachment=True, download_name=filename)
    response.call_on_close(lambda: shutil.rmtree(tmp_dir, ignore_errors=True))
    logger.info("Download served")
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
