"""批次產圖:讀 prompt.txt,每則產一張 1024x1024 PNG 到 pictures/。

用法:python3 gen.py
已存在的檔案會跳過,所以可以重跑補圖——要重生某張就先刪掉那個檔。
"""

import base64
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from queue import Queue

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(BASE_DIR, "prompt.txt")
PICTURES_DIR = os.path.join(BASE_DIR, "pictures")
ENV_PATH = "/home/emissionspectrum/Dev/prompt-To-Image/.env"

API_URL = "https://api.openai.com/v1/images/generations"
PARAMS = {"model": "gpt-image-2", "quality": "low", "size": "1024x1024", "n": 1}
WORKERS = 3
PLACEHOLDER = "[風格描述]"
RETRIES = 6
RATE_LIMIT_WAIT = 15


class Rejected(Exception):
    """內容政策拒絕。不可重試,要改 prompt。"""


def load_key():
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    with open(ENV_PATH) as f:
        for line in f:
            if line.startswith("OPENAI_API_KEY="):
                return line.partition("=")[2].strip()
    sys.exit(f"找不到 OPENAI_API_KEY(環境變數與 {ENV_PATH} 都沒有)")


def load_prompts():
    """檔案開頭是風格描述宣告與風格句,之後每則是 `單字 — 描述 [風格描述]`。

    分節標題(如 `ee /iː/`)不含佔位符,略過;含佔位符卻配不出單字檔名的行
    要報行號停下來——寧可停在這裡,也不要安靜地漏掉一張圖。
    """
    entries, style = [], None
    with open(PROMPT_PATH, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            if style is None:
                if PLACEHOLDER.strip("[]") in line and line.endswith((":", "：")):
                    continue
                style = line
                continue
            if PLACEHOLDER not in line:
                continue
            m = re.fullmatch(r"([a-z0-9_-]+) — (.+)", line)
            if not m:
                sys.exit(f"prompt.txt 第 {lineno} 行認不出 `單字 — 描述`:{line[:60]}")
            entries.append((m.group(1), m.group(2).replace(PLACEHOLDER, style)))
    if style is None:
        sys.exit("prompt.txt 找不到風格描述句")
    if not entries:
        sys.exit("prompt.txt 沒有任何 `單字 — 描述 [風格描述]` 的條目")
    return entries


def call_api(prompt):
    payload = json.dumps({"prompt": prompt, **PARAMS}).encode()
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.load(resp)
    return base64.b64decode(data["data"][0]["b64_json"]), data.get("usage")


def generate(prompt):
    last = ""
    for attempt in range(RETRIES):
        wait = 2**attempt
        try:
            return call_api(prompt)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            try:
                error = json.loads(body).get("error", {})
            except ValueError:
                error = {}
            message = error.get("message", body[:200])
            # 400 時 error.type 分不出 moderation 與參數錯誤,要看 error.code
            if e.code == 400 and error.get("code") == "moderation_blocked":
                raise Rejected(message)
            if e.code != 429 and e.code < 500:
                raise RuntimeError(message)
            # 每分鐘只准 5 張,指數退避的頭幾秒遠不夠等額度回來
            if e.code == 429:
                wait = RATE_LIMIT_WAIT
            last = message
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = str(e)
        time.sleep(wait)
    raise RuntimeError(last)


def cost_usd(usage):
    if not usage:
        return 0.006
    text = usage.get("input_tokens_details", {}).get("text_tokens", 0)
    image = usage.get("output_tokens_details", {}).get("image_tokens", 0)
    return text / 1_000_000 * 5.00 + image / 1_000_000 * 30.00


lock = threading.Lock()
done, rejected, failed, total_cost = [], [], [], 0.0


def worker(queue):
    global total_cost
    while True:
        item = queue.get()
        if item is None:
            return
        word, prompt = item
        try:
            image_bytes, usage = generate(prompt)
        except Rejected as e:
            with lock:
                rejected.append((word, str(e)))
                print(f"  拒絕 {word}: {e}")
        except Exception as e:
            with lock:
                failed.append((word, str(e)))
                print(f"  失敗 {word}: {e}")
        else:
            with open(os.path.join(PICTURES_DIR, f"{word}.png"), "wb") as f:
                f.write(image_bytes)
            with lock:
                done.append(word)
                total_cost += cost_usd(usage)
                print(f"  完成 {word}.png")
        finally:
            queue.task_done()


if __name__ == "__main__":
    API_KEY = load_key()
    os.makedirs(PICTURES_DIR, exist_ok=True)

    todo, skipped = [], []
    for word, prompt in load_prompts():
        if os.path.exists(os.path.join(PICTURES_DIR, f"{word}.png")):
            skipped.append(word)
        else:
            todo.append((word, prompt))

    print(f"待產 {len(todo)} 張,跳過 {len(skipped)} 張已存在")
    queue = Queue()
    for item in todo:
        queue.put(item)
    threads = [threading.Thread(target=worker, args=(queue,)) for _ in range(WORKERS)]
    for t in threads:
        queue.put(None)
        t.start()
    for t in threads:
        t.join()

    print(f"\n完成 {len(done)} 張,跳過 {len(skipped)} 張,花費約 ${total_cost:.3f}")
    if rejected:
        print(f"被內容政策拒絕({len(rejected)}):" + ", ".join(w for w, _ in rejected))
    if failed:
        print(f"失敗({len(failed)}):" + ", ".join(w for w, _ in failed))
