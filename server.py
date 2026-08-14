#!/usr/bin/env python3
"""靜態檔案伺服器 + admin 上傳端點。無資料庫、無狀態、無業務邏輯。"""
import os
import sys
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from PIL import Image

ROOT = Path(__file__).resolve().parent
ASSETS_DIR = Path(os.environ.get("ASSETS_DIR", ROOT / "assets"))
AUDIO_DIR = ASSETS_DIR / "audio"
IMAGES_DIR = ASSETS_DIR / "images"

sys.path.insert(0, str(ROOT / "scripts"))
import check_assets  # noqa: E402
import generate_audio  # noqa: E402

app = Flask(__name__)

IMAGE_SIZE = (1024, 1024)
BACKGROUND_COLOR = (255, 255, 255, 255)


@app.route("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.route("/admin")
@app.route("/admin.html")
def admin():
    return send_from_directory(ROOT, "admin.html")


@app.route("/words.json")
def words_json():
    return send_from_directory(ROOT, "words.json")


@app.route("/assets/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)


@app.route("/assets/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/fonts/<path:filename>")
def serve_font(filename):
    return send_from_directory(ROOT / "fonts", filename)


@app.route("/api/check")
def api_check():
    return jsonify(check_assets.check_assets())


@app.route("/api/regenerate-audio", methods=["POST"])
def api_regenerate_audio():
    data = request.get_json(force=True) or {}
    word = (data.get("word") or "").strip()
    if not word:
        abort(400)
    voice = data.get("voice") or generate_audio.DEFAULT_VOICE
    rate = data.get("rate") or generate_audio.DEFAULT_RATE

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    out_path = AUDIO_DIR / f"{word}.mp3"
    generate_audio.generate_word(word, out_path, voice=voice, rate=rate)
    return jsonify({"word": word, "voice": voice, "rate": rate})


@app.route("/api/upload-image", methods=["POST"])
def api_upload_image():
    word = (request.form.get("word") or "").strip()
    file = request.files.get("file")
    if not word or not file:
        abort(400)

    image = Image.open(file.stream).convert("RGBA")
    image.thumbnail(IMAGE_SIZE, Image.LANCZOS)
    canvas = Image.new("RGBA", IMAGE_SIZE, BACKGROUND_COLOR)
    offset = ((IMAGE_SIZE[0] - image.width) // 2, (IMAGE_SIZE[1] - image.height) // 2)
    canvas.paste(image, offset, image)
    canvas = canvas.convert("RGB")

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = IMAGES_DIR / f"{word}.webp"
    canvas.save(out_path, "WEBP")
    return jsonify({"word": word, "path": f"assets/images/{word}.webp"})


if __name__ == "__main__":
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    app.run(host="127.0.0.1", port=5001, debug=True)
