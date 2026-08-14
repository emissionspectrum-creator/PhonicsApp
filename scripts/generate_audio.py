#!/usr/bin/env python3
"""讀 words.json,為 assets/audio/ 中不存在的字產生 edge-tts 音檔。

只補缺的檔案,絕不覆蓋已存在的檔案(除非透過 generate_word 被明確呼叫覆寫,
例如 admin.html 的重新生成功能)。
"""
import asyncio
import json
import os
from pathlib import Path

import edge_tts
from pydub import AudioSegment, effects
from pydub.silence import detect_leading_silence

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = Path(os.environ.get("ASSETS_DIR", ROOT / "assets"))
WORDS_JSON = ROOT / "words.json"

DEFAULT_VOICE = "en-US-AriaNeural"
DEFAULT_RATE = "+0%"


def trim_and_normalize(path: Path) -> None:
    audio = AudioSegment.from_file(path, format="mp3")
    start = detect_leading_silence(audio)
    end = detect_leading_silence(audio.reverse())
    trimmed = audio[start: len(audio) - end]
    trimmed = effects.normalize(trimmed)
    trimmed.export(path, format="mp3")


async def _synthesize(word: str, voice: str, rate: str, out_path: Path) -> None:
    communicate = edge_tts.Communicate(text=word, voice=voice, rate=rate)
    await communicate.save(str(out_path))


def generate_word(word: str, out_path: Path, voice: str = DEFAULT_VOICE, rate: str = DEFAULT_RATE) -> None:
    asyncio.run(_synthesize(word, voice, rate, out_path))
    trim_and_normalize(out_path)


def main():
    words = json.loads(WORDS_JSON.read_text(encoding="utf-8"))
    audio_dir = ASSETS_DIR / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    for w in words:
        word = w["word"]
        out_path = audio_dir / f"{word}.mp3"
        if out_path.exists():
            continue
        print(f"生成中: {word}")
        generate_word(word, out_path)
        generated.append(word)

    if generated:
        print(f"\n已生成 {len(generated)} 個音檔: {', '.join(generated)}")
        print("請務必逐一試聽確認發音正確(TTS 偶有異常發音)。")
    else:
        print("沒有缺少的音檔。")


if __name__ == "__main__":
    main()
