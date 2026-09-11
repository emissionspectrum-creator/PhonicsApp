# PhonicsApp

兒童自然發音（phonics）學習工具。完整規格見 [DESIGN.md](./DESIGN.md)。

目前進度：階段一～五（CVC 短母音）字彙與素材、階段六母音對比題型（對比組由 onset＋尾子音自動推導，見 [HANDOFF.md](./HANDOFF.md)）已完成，尚未進行實機驗證與動畫優化。

## 需求

- Python 3.12 以上
- ffmpeg（`generate_audio.py` 的靜音修剪 / 音量正規化需要；`sudo apt install ffmpeg`）
- 套件：flask、pillow、edge-tts、pydub（Python 3.13 另需 `audioop-lts`）

## 執行

```bash
./start.sh          # Linux/macOS，啟動 server 並開啟瀏覽器到主畫面
start.bat           # Windows
```

`start.sh` 會在 `.venv/` 不存在時自動建立虛擬環境並安裝套件，所以重灌系統後直接執行即可
（Ubuntu 24.04 起的 Python 受 PEP 668 保護，不能 `pip install` 到系統，必須用 venv）。

或手動啟動：

```bash
python3 -m venv .venv
.venv/bin/pip install flask pillow edge-tts pydub
.venv/bin/python server.py
```

- 主畫面（給小孩用）：`http://127.0.0.1:5001/`
  - 上帶最左的模式選單可切換「聽音選字」（聽音、選出空格裡的字母）與「看字唸音」（看完整單字自己唸，按發音鍵自我對照），見 [DESIGN.md](./DESIGN.md) §3.8
- 後台管理（音檔試聽/重生成、圖片拖放上傳、缺漏檢查）：`http://127.0.0.1:5001/admin.html`

assets 路徑預設為 `./assets`，可用環境變數 `ASSETS_DIR` 覆寫。

## 目錄結構

```
words.json          單字資料（word/onset/rime/family/stage/note）
HANDOFF.md          給產字用 Claude Project 的資料契約與現況文件
server.py           Flask server：靜態檔案 + 圖片上傳/音檔重生成 API
admin.html          後台管理頁面
index.html          主練習畫面
scripts/
  generate_audio.py 用 edge-tts 補生成缺少的單字音檔
  check_assets.py   檢查 words.json 對應的音檔/圖片是否齊全
assets/
  audio/*.mp3
  images/*.webp
fonts/               自 host 的 Lexend 字體（woff2）
```

## 產生音檔 / 檢查缺漏

```bash
python3 scripts/generate_audio.py   # 只補缺的，不覆蓋已存在檔案
python3 scripts/check_assets.py     # 列出缺音檔/缺圖片清單
```

## 圖片來源

圖片一律由人工準備後透過 admin.html 拖放上傳（自動置中裁切、統一背景、轉存為 WebP），不由程式自動搜尋或產生。
