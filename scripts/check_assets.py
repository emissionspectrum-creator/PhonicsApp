#!/usr/bin/env python3
"""檢查 words.json 中每個字是否有對應的音檔與圖片。"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = Path(os.environ.get("ASSETS_DIR", ROOT / "assets"))
WORDS_JSON = ROOT / "words.json"


def check_assets():
    words = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    audio_dir = ASSETS_DIR / "audio"
    images_dir = ASSETS_DIR / "images"

    missing_audio = []
    missing_images = []
    for w in words:
        word = w["word"]
        if not (audio_dir / f"{word}.mp3").exists():
            missing_audio.append(word)
        if not (images_dir / f"{word}.webp").exists():
            missing_images.append(word)

    return {
        "total": len(words),
        "missing_audio": missing_audio,
        "missing_images": missing_images,
    }


def print_report(result):
    print(f"共 {result['total']} 個字\n")

    if result["missing_audio"]:
        print(f"缺音檔 ({len(result['missing_audio'])}):")
        for word in result["missing_audio"]:
            print(f"  - {word}")
    else:
        print("音檔齊全。")

    print()
    print("=" * 40)
    print("缺圖片清單(可直接複製)")
    print("=" * 40)
    if result["missing_images"]:
        for word in result["missing_images"]:
            print(word)
    else:
        print("(無)")


if __name__ == "__main__":
    print_report(check_assets())
