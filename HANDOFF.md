# 交接說明：階段六實作後的資料與程式現況

**這份文件給誰看：** 負責產字彙、寫提示詞、討論學習順序的 Claude Project 對話（看不到 code）。
**目的：** 讓它在產生 words.json 條目或後續文件時，知道現在的資料契約是什麼、什麼會自動發生、什麼不要做。

**日期：** 2026-08-19　**對應 commit：** 階段六（母音對比）實作完成，僅動 `index.html`。

---

## 0. 一句話結論

**階段六不需要任何新資料。** words.json 的 schema、欄位、每字一筆的結構全部不變，沒有 stage 6 條目，也沒有新增 review.json 或任何第二個資料檔。對比組（hat/hit/hot/hut）是**程式從現有欄位算出來的**。

產字的規則因此完全沒變 —— 但多了一個副作用值得知道：**你加進去的每一個字，都可能自動促成一組新的對比題**。詳見第 4 節。

---

## 1. 曾經考慮但否決的兩個方案

記錄下來，避免之後又繞回來。

| 方案 | 否決原因 |
| --- | --- |
| 在 words.json 複製一份 `stage: 6` 的條目 | app 的取字邏輯是 `filter(w => w.family === family)`，**按 family 撈，不看 stage**。複製 `hat` 進去（family 仍是 `-at`）會污染階段一的 -at 練習；且選項位置是以 onset 當 Map key，兩筆 `h` 會互相覆蓋。此方案原本唯一的優點是「不用改程式」，而這個前提是錯的。 |
| 另建 `review.json` 記錄對比組 | 會產生兩份真相。刪掉或改掉某個字時，review.json 仍指著它，要靠人記得同步。而對比組本身可從現有欄位 100% 推導，不需要獨立記錄。 |

**真正要改的地方跟用哪種資料格式無關**：階段六是另一種題型（見第 3 節），版面與出題邏輯本來就得動。

---

## 2. words.json 規格（**未變更**）

單一檔案，扁平陣列，一字一筆。目前 74 筆，stage 1–5。

```json
{
  "word": "hat",
  "onset": "h",
  "rime": "at",
  "family": "-at",
  "stage": 1,
  "note": ""
}
```

| 欄位 | 說明 |
| --- | --- |
| `word` | 單字本身，同時是音檔與圖片的檔名 |
| `onset` | 字首子音。**母音開頭的字為空字串 `""`**（目前只有 `ox`、`up`） |
| `rime` | 韻腳。**第一個字元必然是母音** |
| `family` | 字族，如 `-at` |
| `stage` | 學習階段編號，目前 1–5 |
| `note` | 同形異義取義說明等，不顯示於畫面 |

### 程式依賴的三條不變式

新增條目時必須維持，否則階段六會算錯：

1. **`onset + rime === word`**，不多不少。
2. **`rime[0]` 必須是 `a/e/i/o/u` 其中之一。** 程式用 `rime[0]` 取母音、用 `rime.slice(1)` 取尾子音。
3. **`onset` 可以是空字串，但不可省略欄位。**

目前 74 筆全數符合，已驗證。

檔名一律由 `word` 推導：`assets/audio/{word}.mp3`、`assets/images/{word}.webp`。

---

## 3. 階段六是新題型，不是新資料

這是整件事的重點。

| | 階段 1–5 | 階段 6 |
| --- | --- | --- |
| 固定顯示 | 韻腳（`_ a t`） | 字首 + 尾子音（`h _ t`） |
| 空格位置 | **最前面** | **中間** |
| 選項 | 各種 onset（c / b / h / m） | 各種母音（a / i / o / u） |
| 一組的來源 | `family` 欄位 | 算出來的對比組 |
| 訓練什麼 | 聽字首子音 | **聽母音** |

DESIGN.md §7.3 講的「真正困難也真正有用的是只差一個母音的對決」，就是這個畫面。

### 對比組怎麼算

```
key = onset + "_" + rime.slice(1)      // 即「字首 + 尾子音」
```

`hat` → `h_t`，`hit` → `h_t`，`hot` → `h_t`，`hut` → `h_t`，四個字自動歸為同一組。

**門檻：同組至少 3 個字才會出現在選單**（少於 3 個做成四選一沒有意義）。`ox`、`up` 因為 onset 為空，key 是 `_x` / `_p`，各只有 1 個字，自然被門檻濾掉，不需要特別處理。

**排序：按 key 字母序**，不做難度排序。理由：組的大小不是難度軸，真正的難度來自「哪兩個母音在對比」——`p_n`（pan/pen/pin）含 a–e，對中文母語的孩子是最難的一組，比 `h_t` 的 a/i/o/u（四個彼此都離得遠）難得多。按大小排反而會把最難的排到前面。真要排就是人工策展，**現在不做，等看到孩子實際卡在哪再說**。

### 目前自動長出來的 6 組

| 組 | 字 | 母音對比 |
| --- | --- | --- |
| `b_g` | bag / big / bug | a–i–u |
| `c_t` | cat / cot / cut | a–o–u |
| `h_t` | hat / hit / hot / hut | a–i–o–u（唯一四母音全齊） |
| `p_n` | pan / pen / pin | a–e–i ← **最難**，含 /ɛ/ 與 /æ/ |
| `p_p` | pip / pop / pup | i–o–u |
| `p_t` | pet / pit / pot | e–i–o |

選單預設選中字母序第一個 `b_g`（a–i–u，三個都離得遠），是合理的起手組。`p_n` 排第四，不會被隨手點到。

### 選項一定是組內真實存在的字

不是給滿 a/e/i/o/u。程式在答錯時會播放**被誤選的那個字**的音檔（這正是聽 minimal pair 的時機：目標 hat、點了 `i`，聽到 "hit"）。若給滿五個母音，`h_t` 會出現 `het` 這種非字，既沒有音檔也沒有圖，點下去只會沉默；教學上也不該讓孩子在解碼練習裡被餵非字。

**這一條對產字的意義：不需要為了湊滿五個母音而去找非字或冷僻字。** 三個真詞就是一組合格的對比題。

---

## 4. 這對「產生 words.json 條目」的實際影響

### 你加一個字，會自動發生什麼

加入一個字時，除了它所屬的 `family` 多一個成員（階段 1–5 的練習），還會自動落進 `onset + 尾子音` 的桶裡。**如果那個桶因此達到 3 個字，階段六的選單就會多出一組新對比題，不需要改任何程式或設定。**

例：加入 `tip` → `t_p` 桶變成 tap / tip / top，階段六立刻多一組。

### 目前的缺口

下表是**機械算出來的拼法槽位，不是候選字**。`het`、`wug`、`cet` 這類不是英文字。哪些是真詞、夠具體、畫得出來、適合 7 歲孩子，是你和家長要判斷的（DESIGN.md §8 的分工）。

**已成組（≥3），可再補的槽位：**

| 組 | 現有 | 空槽 |
| --- | --- | --- |
| `h_t` (4) | hat hit hot hut | het |
| `b_g` (3) | bag big bug | beg bog |
| `c_t` (3) | cat cot cut | cet cit |
| `p_n` (3) | pan pen pin | pon pun |
| `p_p` (3) | pip pop pup | pap pep |
| `p_t` (3) | pet pit pot | pat put |

**只差 1 個字就能成組（現有 2 個），投報率最高：**

| 組 | 現有 | 空槽 |
| --- | --- | --- |
| `t_p` | tap top | tep **tip** tup |
| `f_n` | fan fin | fen fon **fun** |
| `c_p` | cap cup | cep cip **cop** |
| `p_g` | pig pug | pag **peg** pog |
| `r_g` | rag rug | reg **rig** rog |
| `n_t` | net nut | nat **nit** **not** |
| `b_n` | bin bun | **ban** **ben** bon |
| `h_p` | hip hop | hap hep hup |
| `m_p` | map mop | mep mip mup |
| `w_g` | wag wig | weg wog wug |

（粗體是我看起來像真詞的槽位，僅供起點，具體性與適齡性請自行判斷。`h_p`、`m_p`、`w_g` 三組的空槽看起來都不是常用真詞，可能就停在 2 個字。）

### 明確不要做的事

- **不要輸出 `stage: 6` 的條目。** 階段六不從 stage 欄位取字。
- **不要輸出 review.json、contrast.json 或任何記錄「哪些字是一組」的檔案。** 這個關係是算出來的。
- **不要為了湊組而收非字或冷僻字**（`wug`、`pon`、`cet`）。組只有 2 個字是可接受的結果。
- **不要改動 `onset` / `rime` 的切法**（例如把 `ox` 寫成 `onset: "o", rime: "x"`）。那會讓程式把 `x` 當成母音。

---

## 5. index.html 的結構變更

只動這一個檔，+92 / −48 行。列在這裡是為了讓你知道「已經完成到什麼程度」，產資料時不需要用到這節。

### 版面：從寫死三個節點改成動態排版

**變更前** —— DOM 寫死，只能表達「空格在最前面」：

```html
<div id="puzzle">
  <div class="letter-slot placeholder" id="onset-slot"></div>
  <div class="gap-spacer" id="gap-spacer"></div>
  <div id="rime-group"></div>          <!-- 韻腳字母塞這裡 -->
</div>
```

**變更後** —— 空容器，由 JS 依 `session.blankIndex` 排出字母磚，並在空格有鄰居的那一側插入間隔：

```html
<div id="puzzle"></div>
```

```
階段 1–5   blankIndex = 0   →   [?] _____ [a][t]
階段 6     blankIndex = 1   →   [h] _____ [?] _____ [t]
```

寫成通用版而不是加第二套寫死的版面，是因為兩套寫死的 code 比一套通用的長。階段 1–5 的呈現與動畫與改版前完全相同。

### 函式層面

| 變更前 | 變更後 |
| --- | --- |
| `startFamilySession(family)` | `startSession(name, stage)` — 名稱與階段一起傳，因為它現在也吃對比組 |
| `session.familyWords` | `session.items` |
| 到處直接用 `w.onset` 當作「要選的字母」 | `session.keyAt(w)` — 階段 1–5 回傳 onset，階段六回傳母音 |
| — | 新增 `buildContrastSets()`、`letters(w)`、`isContrastStage(stage)` |
| `buildStageSelect()` 從資料推導階段清單 | 多一行把階段 6 加進選單（words.json 裡沒有 stage 6） |
| `buildFamilySelect(stage)` 列 family | 階段六時改列對比組的 key |

視覺上唯一的差異：字母磚間距從「收合後 onset 貼死韻腳、韻腳內部 4px」統一成 4px。

### 驗證狀況

以 DOM stub 在 node 執行真實的 `index.html` 程式碼（非複製一份邏輯），六組 × 每組每字各當一次目標，全數通過。斷言涵蓋：版面等於 `{onset}_?_{尾子音}`、選項全為母音、含正解、不重複、每個選項都對應組內真實存在的字、每字各當一次目標；以及階段一版面仍為 `?_at`。

**尚未用真實瀏覽器驗收** —— 中間空格的實際比例與兩側間隔同時收合的動畫手感還沒用眼睛確認過。

---

## 6. 素材現況

階段六的六組共 19 個字，**mp3 與 webp 全部已存在，零新素材需求**。

```
b_g  bag big bug        p_n  pan pen pin
c_t  cat cot cut        p_p  pip pop pup
h_t  hat hit hot hut    p_t  pet pit pot
```

音檔：edge-tts、en-US、已去頭尾靜音並統一音量（`scripts/generate_audio.py`，只補缺的）。
圖片：1024×1024 WebP，人工準備後經 admin.html 拖放上傳，**不由程式自動搜尋或產生**。
缺漏檢查：`python3 scripts/check_assets.py`。

---

## 7. 已知落差：DESIGN.md 的階段表 vs words.json

DESIGN.md §7.2 的範例字列了幾個 words.json 裡沒有的字。不是錯誤（範例表本來就是示意），但其中兩個剛好能促成新的對比組：

| 字 | DESIGN.md 位置 | words.json | 影響 |
| --- | --- | --- | --- |
| `tip` | 階段二 -ip | 缺 | 補了 → `t_p` = tap/tip/top **成組** |
| `fun` | 階段四 -un | 缺 | 補了 → `f_n` = fan/fin/fun **成組** |
| `bit` | 階段二 -it | 缺 | 補了 → `b_t` = bat/bit，2 個未達門檻，不成組 |
| `fed` | 階段五 -ed | 缺 | 補了 → `f_d` 只有它一個，不成組 |

另外 DESIGN.md **尚未記錄**階段六的實作方式（推導規則、≥3 門檻、字母序、選項限真詞）。§7.2「階段六：五母音總混合」與 §7.3「此功能依賴 onset / rime 欄位查詢」的敘述仍然正確，只是沒有描述到實作細節。要不要把本文件第 3 節併進 DESIGN.md，可以再決定。

---

## 8. 附：分工提醒（沿用 DESIGN.md §8）

判斷性工作（選字、順序、風格、提示詞）在 Claude Project 討論；執行性工作（寫檔、跑腳本）交給 Claude Code。

給 Claude Code 的指令要明確寫「不要自行尋找或產生圖片」。

---
---

# 第二部分：階段七以後的資料契約

**日期：** 2026-08-19　**狀態：** 階段編號 7–11 已由家長確認採用，程式端契約已實作並通過測試。

回答五個問題：schema 是否要變、各階段題型、family 的意義、對比組去留、不要產出什麼。

---

## A. 階段編號（已定案）

| stage | 內容 | 例 |
| --- | --- | --- |
| 7 | 字尾雙子音 -ck, -ll, -ss, -ng | duck, bell, kiss, sing |
| 8 | 開頭子音串 st-, fl-, gr-… | stop, flag, grab |
| 9 | 子音 digraph sh, ch, th, wh（字首與字尾） | ship, chin, fish |
| 10 | magic e | cake, kite, rope |
| 11 | 母音組合 ee, ea, oo, ai, oa | rain, boat, feet |

**`stage: 6` 保留、永遠不寫入 words.json** —— 它是程式合成的母音對比階段（第一部分 §3）。新資料從 7 起跳。

-ck 嚴格說是 digraph（一音兩字母），但歸在階段七：它和 -ll、-ss 一樣是「短母音後的字尾拼法規則」，不引入新的字首音；階段九的 sh/ch/th/wh 才是引入新音的組。

## B. schema：完全不變

六欄照舊，三條不變式照舊（`onset + rime === word`；`rime[0]` 是 a/e/i/o/u；`onset` 可為空字串但不可省略）。逐階段驗證過：

| 階段 | 例 | onset | rime | 備註 |
| --- | --- | --- | --- | --- |
| 7 | duck | `d` | `uck` | 尾子音 = `ck` |
| 8 | stop | `st` | `op` | onset 是完整子音串 |
| 9 | ship / fish | `sh` / `f` | `ip` / `ish` | 字首、字尾 digraph 皆可 |
| 10 | cake | `c` | `ake` | `rime[0]`='a' 仍是母音 |
| 11 | rain | `r` | `ain` | 母音單位是 `ai`，見 D 節的排除規則 |

**不新增任何欄位。** `pattern` / `vowel` / `coda` 都可從 onset/rime 推導，存進檔案就是第二份會走鐘的真相；`blank_index` 是題型的屬性不是字的屬性，由程式依階段決定。

## C. 各階段題型與 family 的意義

**family 永遠是 rime 字族**（-uck、-op、-ake、-ain），不改成 pattern 名（st-、magic-e）。硬理由：現有題型的選項必須是同 rime 的真字（錯選會播那個字的音），以「st-」為單位出題，target stop 的干擾項會變成 flop、grop 之類的非字。

**session 規則（已實作）：選單列出「含該階段字」的字族；session 內容 = 該字族中 `stage ≤ 所選階段` 的字。** 所以階段三選 -op 只有 top/mop/hop/pop；階段八選 -op 是這四個加 stop —— rime 固定、onset 混入子音串，正是「一次只動一個變數」。

| 階段 | 題型 | 程式改動 |
| --- | --- | --- |
| 7 | 現有題型（選 onset），零改動 | 無 |
| 8–9 | 同上；onset 磚顯示 `st`、`sh` 整塊 | 無（雙字母磚字級可能微調，視覺層） |
| 10 | 字進來後，`-ake` 等字族立即可玩選 onset；cap↔cape 辨別題**尚未設計**，到時另開一輪 | 待設計 |
| 11 | 同上，母音組合的顯色與辨音題**尚未設計** | 待設計 |

階段 10–11 的字可以先產、先進資料，不會壞任何東西。

## D. 對比組：繼續運作，不加開關

推導是跨階段的，新字會自動長出新組：deck/dock/duck（`d_ck`）、sing/song/sung（`s_ng`）、step/stop（`st_p`）。magic-e 字天然分流（cut=`c_t`、cute=`c_te`，不相撞）。

唯一的排除規則（已實作）：**`rime` 第二個字元也是母音的字（rain、boat、feet）不入對比組** —— 它們的母音是兩個字母，不是單母音對比。

## E. 不要產出的清單

1. 不產 `stage: 6` 條目。
2. 不發明新欄位；六欄一個都不能少（`note` 可為空字串）。
3. onset 必須含完整子音串／digraph（ship → `sh` 不是 `s`）。自檢法：**rime 必須從第一個母音開始**。
4. 不收 y 當母音的字（fly、my、play、day）—— 程式的母音表沒有 y。
5. 不收 -all／-alk／wa- 開頭（ball、walk、want）—— 母音變音，同 DESIGN.md 的 -og 理由。
6. magic e 只收規則的短→長對應；不收例外拼法（have、give、love、come、some、one、done）。
7. 母音組合只收規則發音：ea 取 /iː/ 組（eat、sea），不收 bread、head；**同一 family 內母音發音必須一致**（-ood 會裂成 food /uː/ 對 good /ʊ/，這種拆開或擇一收）。
8. 每個新 family 至少 3 個真字（與族下限一致）。
9. 不重複產出既有的字（現有清單以 words.json 為準）。

## F. 每階段一筆範例 JSON

```json
{ "word": "duck", "onset": "d",  "rime": "uck", "family": "-uck", "stage": 7,  "note": "鴨子" }
{ "word": "stop", "onset": "st", "rime": "op",  "family": "-op",  "stage": 8,  "note": "停止（手勢／標誌）" }
{ "word": "ship", "onset": "sh", "rime": "ip",  "family": "-ip",  "stage": 9,  "note": "船" }
{ "word": "cake", "onset": "c",  "rime": "ake", "family": "-ake", "stage": 10, "note": "" }
{ "word": "rain", "onset": "r",  "rime": "ain", "family": "-ain", "stage": 11, "note": "雨" }
```

（實際交付時仍是一個 JSON 陣列，上面分行只為易讀。）

**Project 可自檢的三條規則：** ① 每筆 `onset + rime === word`；② `rime` 第一個字元 ∈ a/e/i/o/u；③ `stage` ∈ {7,8,9,10,11} 且與 A 節的分類一致。交給 Claude Code 寫入時會再跑一次同樣的檢查。
