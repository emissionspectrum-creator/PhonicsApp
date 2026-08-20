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

**日期：** 2026-08-19（2026-08-19 修訂：補 B2 題型模式與選字約束、七欄 schema、階段七定案清單；補階段九、階段十定案清單。2026-08-21 修訂：階段十一入庫，§B2、§C、§D 改寫為現況）
**狀態：** 階段編號 7–11 已由家長確認採用。階段七 29 字、階段八 22 字（另補階段一 -am 三字）、階段九 37 字、階段十 44 字、階段十一 44 字已入庫，音檔齊全。words.json 現有 253 字，**七到十一階段全數產完**。模式 A 與 C 及各自的第 1 層干擾項**皆已實作**；模式 B 只存在於程式合成的階段六，**階段十一原定用 B、實際改用 A ＋ C**（見 §B2 ①、§C）。

回答五個問題：schema 是否要變、各階段題型、family 的意義、對比組去留、不要產出什麼。

---

## A. 階段編號（已定案）

| stage | 內容 | 例 |
| --- | --- | --- |
| 7 | 字尾子音組 -ck, -ng, -nk, -nd, -mp | sick, sing, sink, hand, jump |
| 8 | 開頭子音串 st-, fl-, gr-… | stop, flag, grab |
| 9 | 子音 digraph sh, ch, th, wh（字首與字尾） | ship, chin, fish |
| 10 | magic e | cake, kite, rope |
| 11 | 母音組合 ee, ea, oo, ai, oa | rain, boat, feet |

**`stage: 6` 保留、永遠不寫入 words.json** —— 它是程式合成的母音對比階段（第一部分 §3）。新資料從 7 起跳。

-ck 嚴格說是 digraph（一音兩字母），但歸在階段七：它是「短母音後的字尾拼法規則」，不引入新的字首音；階段九的 sh/ch/th/wh 才是引入新音的組。

**階段七已定案：8 族 29 字，已寫入 words.json。**

| family | 字 |
| --- | --- |
| -ack | pack, sack, tack, rack |
| -ick | kick, sick, lick |
| -ock | lock, rock, sock, dock |
| -ing | king, ring, wing, sing |
| -ink | ink, sink, pink, link |
| -and | hand, sand, band |
| -ump | jump, pump, lump, hump |
| -amp | lamp, camp, ramp |

- **-ll、-ss 移到階段九**（bell、kiss 與 sh/ch/th 同屬「字尾拼法」組）。
- **-ong、-uck、-eck、-ank 整族排除**，不再產出。

**階段八已定案：11 個 blend 共 22 字，已寫入 words.json。**

| onset | 字 |
| --- | --- |
| st- | stick, stamp, stop, stump, stand |
| cl- | clock, clip, clap, clam |
| sp- | spot, spin |
| tr- | track, trap |
| tw- | twig, twin |
| bl- | block, black |
| fl- | flag, flat |
| sn- / sw- / pl- | snack / swing / plug（各一字） |

- **另補 `ham`、`jam`、`dam` 三字為 `stage: 1`**，新開 -am 家族。三字都給階段一是因為它們是單子音 CVC；只給兩字的話階段一的 -am session 只有兩個選項，違反 E8 的族下限。
- 第 1 層（成分字）為空的有 black、clam、flag、stamp、stump 五字，其餘 17 字都有。**不需為此補字**，理由同階段七的模式 C。

**階段九已定案：37 字，已寫入 words.json。** 字首 digraph（模式 A）與字尾 digraph／-ll／-ss（模式 C）一併收在此階段。

| 類別 | family／onset | 字 |
| --- | --- | --- |
| 字首 sh- | -ip / -op / -ut / -ell | ship, shop, shut, shell |
| 字首 ch- | -ip / -op / -at | chip, chop, chat |
| 字首 th- | -umb / -in / -ick | thumb, thin, thick |
| 字首 wh- | -ip | whip（單字破例） |
| -ish | | fish, dish, wish |
| -ash | | cash, trash, flash |
| -unch | | lunch, punch, bunch |
| -atch | | catch, match, patch |
| -itch | | witch, ditch, pitch |
| -ath | | bath, path, math |
| -ell | | shell, bell, well |
| -ill | | hill, pill, bill |
| -oss | | boss, moss, toss |

- **`thumb` 是家長裁定收錄的破例**（silent b；-umb 全庫僅此一字）。族內不足 2 字就湊不出選項，**程式端已改成不把這種字族列進選單** —— 所以 `-umb` 在階段九選單裡看不到，thumb 目前不會被出題。要讓它出題，-umb 需再補到 2 字以上（本階段沒有合規候選）。
- **`wh-` 只有 whip 一字**，被開頭音選單的 ≥2 門檻擋掉（同階段八的 sn-／sw-／pl-）；whip 仍會出現在 -ip 字族的題目裡。
- 模式 A 第 1 層（成分字）為空的有 shell、thumb、thin、thick、trash、flash 六字，其餘有 onset 為子音串／digraph 的字都有。模式 C 第 1 層為空的是 sh-／ch-／wh- 底下的字（同 onset 內每個字母音都不同）。**兩者皆不需為此補字**，理由同階段七、八。
- `math` 的圖必須含阿拉伯數字與加號，與「畫面不出現文字」的風格描述牴觸，**待家長確認**（前例：階段七 clock 的鐘面數字、階段八 stop 的路牌）。

**階段十已定案：17 族 44 字，已寫入 words.json。**

| 母音 | family | 字 |
| --- | --- | --- |
| a_e | -ake / -age / -ace / -ane / -ape / -ave | cake lake rake ／ cage page stage ／ face race lace ／ cane mane lane ／ cape tape ／ cave wave |
| i_e | -ice / -ine / -ike / -ide / -ipe / -ive / -ite | rice ice dice ／ pine line nine ／ bike hike spike ／ ride hide wide ／ pipe wipe ripe ／ five hive dive ／ kite bite |
| o_e | -ole / -ose | mole pole hole ／ rose nose hose |
| u_e | -ute / -uge | cute ／ huge |

- **模式 C（開頭音選單）是本階段的主力題型，全數成立。** 15 個開頭音池全部 ≥2，第 1 層（同 onset、同母音字母、異尾子音）實測長這樣：cute → cut/cup、huge → hug/hut/hump、kite → kit/kick/king、cape → cap、cake → cap/camp/catch。§B2 那條「同母音是同母音**字母**段、不是音值」的前提在這裡才真正生效，實測正確。
- **`-ute`（cute）與 `-uge`（huge）族內各只有 1 字，被字族選單的 ≥2 門檻擋掉**，同階段九的 -umb。但**兩字不會因此消失**：它們在 c-／h- 的開頭音 session 裡是正常 target，而模式 C 本來就是階段十該練的題型，教學上無損失。
- **`nine` 與 `nose` 的模式 C 第 1 層是空的**（n- 池只有 nap/net/nut，沒有 i 或 o 母音的字），如字彙表所述，兩者的誘答項落到第 2 層。**不需為此補字**，理由同階段七、八、九。
- **`ice` 是零 onset 字，只能從 `-ice` 字族進去**，不會出現在開頭音選單（程式明確排除空 onset，同 ox/up/ink 前例）。字彙表所寫的「零 onset 對比桶（ink 為同母音異尾子音）」目前**沒有對應的 session**。若要開，需另外做一個零 onset 的開頭音項目，屬新功能，尚未實作。
- 模式 A 第 1 層（成分字）為空的只有 stage、spike 兩個子音串字（`-age`／`-ike` 族內沒有 s/t/p 開頭的同族字）。
- 收字時已排除的發音例外：have、give、live、tube、rule、white、write（理由見字彙表 note 與 E6／E7）。

## B. schema：完全不變

**七欄**照舊，三條不變式照舊（`onset + rime === word`；`rime[0]` 是 a/e/i/o/u；`onset` 可為空字串但不可省略）。逐階段驗證過：

| 階段 | 例 | onset | rime | 備註 |
| --- | --- | --- | --- | --- |
| 7 | sick | `s` | `ick` | 尾子音 = `ck` |
| 8 | stop | `st` | `op` | onset 是完整子音串 |
| 9 | ship / fish | `sh` / `f` | `ip` / `ish` | 字首、字尾 digraph 皆可 |
| 10 | cake | `c` | `ake` | `rime[0]`='a' 仍是母音 |
| 11 | rain | `r` | `ain` | 母音單位是 `ai`，見 D 節的排除規則 |

**七欄是：** `word`、`onset`、`rime`、`family`、`stage`、`note`、`zh`。兩個文字欄分工不同，兩個都要給：

| 欄 | 給誰看 | 可否為空 | 例（sack） |
| --- | --- | --- | --- |
| `note` | 產字者／畫圖者，用來辨義與避免撞字 | 可為空字串 | `麻布袋;與階段一 bag 以材質與束口造型區隔` |
| `zh` | **孩子**，揭曉時滑鼠停留顯示的中文提示 | **不可為空** | `麻布袋` |

`zh` 是後加的欄位（commit 267882b），舊版契約漏寫，導致階段七交來的 29 筆只有六欄、得由 Claude Code 從 `note` 反推。**從階段八起，`zh` 請隨字一起給。**

**不新增任何其他欄位。** `pattern` / `vowel` / `coda` 都可從 onset/rime 推導，存進檔案就是第二份會走鐘的真相；`blank_index` 是題型的屬性不是字的屬性，由程式依階段決定。

## B2. 題型模式與選字約束（**產字之前必讀**）

原契約用「語言學內容」定義階段（階段七＝字尾子音組），卻默認題型恆為「挖 onset」。這個默認在階段七破功——字產完才發現 29 字裡有 11 個永遠當不了題目。補上的規則是：

> **挖空的格子，必須正好落在該階段要教的那個單位上。**

依這條推下去，模式只有三種：

| 模式 | 挖哪一格 | 用在 |
| --- | --- | --- |
| **A** | onset 磚 | 階段 1–5；階段 7–11 的**字族選單**（階段 8、9 的字首 blend／digraph 也走這條，onset 磚整塊顯示） |
| **B** | rime 裡的母音單位 | **只有階段 6**（1 字母，程式合成的對比組）。階段十一原定用 B，實際改用 A ＋ C，見下方 ① |
| **C** | 整塊 rime 磚 | 階段 7–11 的**開頭音選單**（階段 9 的字尾 digraph 也走這條） |

### 模式決定選字約束

**這張表要在挑字之前套用，不是挑完字才驗。** 階段七整件事唯一真正的教訓，不是字挑錯了，是挑字時不知道題型長什麼樣。

| 模式 | 選字時必須湊滿的組 | 備註 |
| --- | --- | --- |
| A | 同 **rime 家族** ≥ 3 | 現行規則，一直都對 |
| C | 同 **onset** ≥ 2，**且其中至少 1 個與 target 只差一個維度** | 階段七缺的就是這條 |
| B | 同 **onset ＋尾子音骨架** ≥ 3 | **從未實際用於選字**：階段六不選字（既有字自動成組），階段十一最後沒走這條路 |

「只差一個維度」＝ 母音相同而尾子音不同（sick / sing），或尾子音相同而母音不同（cap / cape、lick / lock）。沒有這個同伴，選項湊滿 3 個也只是亂猜，題目沒有教學點。

### 三條可以直接照做的選字結論（已用現有 103 字驗證）

**① ~~階段十一照 16 個骨架挑字~~ —— 未採用，本條已作廢。** 原建議是「選 `coat` 不選 `boat`」，按 `onset ＋尾子音骨架` 湊出模式 B 的對比組。實際交來的階段十一 44 字是按 rime 家族挑的，與骨架清單沒對上：全庫套用骨架 key 之後，44 字裡只有 5 個（beet、boat、boot、coat、sheep）落進 ≥3 的骨架組，總共 3 組 —— `b_t`(bat beet boat boot)、`c_t`(cat coat cot cut)、`sh_p`(sheep ship shop)。**家長裁定階段十一改用模式 A ＋ C**（同階段 7–10），模式 B 不再用於階段十一，這條骨架約束連帶失效。原清單留在下面，僅供日後真要開模式 B 時參考：

```
b_g(bag big bug)  c_t(cat cot cut)  h_t(hat hit hot hut)  p_n(pan pen pin)
p_p(pip pop pup)  p_t(pet pit pot)  c_p(cap cup)  f_n(fan fin)  h_p(hip hop)
m_p(map mop)      n_t(net nut)      p_g(pig pug)  r_g(rag rug)  t_p(tap top)
w_g(wag wig)      b_n(bin bun)
```

**② 階段十優先挑「短母音字已在庫」的。** cape / tape / kite / hope / pine / cute / cane / mane / rate / mate / pipe / dine / site —— cap、tap、kit、hop、pin、cut、can、man、rat、mat、pip、din、sit 全部已在 words.json，配對題天然成立。

**③ 階段九字尾 digraph 挑 onset 湊得滿的。** f-（fan / fat / fig / fin / fox）配 fish、w-（wag / wet / wig / win / wing）配 wish，一進來就成組。

**④ 階段八、九字首挑「成分字已在庫」的 blend／digraph。** 這是模式 A 第 1 層的選字面：stop 的教學價值在 top（st 對 t），沒有 top 就沒有第 1 層。用現有 103 字掃過，**18 個可成組**：

```
stop(top)    spot(pot)     stick(sick)   swing(sing wing)  stand(sand)
slip(lip)    flip(lip)     clip(lip)     spin(pin)         twin(win)
drag(rag)    brag(bag rag) snack(sack)   track(tack rack)  crack(rack)
clock(lock)  block(lock)   clap(cap)
```

**成分字不在庫、目前成不了組：** flag、trip、skip、sled、stamp（`-ip` 家族只有 dip/hip/lip/pip/zip，沒有 tip 也沒有 sip）。正式進階段八時再完整盤點，此處先確立約束。

### 干擾項分層（程式端規則，列在此供選字時參考）

選項依序這樣抽，三層都在**同 onset**（模式 C）或**同字族**（模式 A）的前提下運作：

1. **第 1 層＝教學點，不問階段，名額內全部抽進來**（定義隨模式而變，見下表）
2. 同 target 階段的其他字
3. 其餘（任何階段）

**第 1 層的定義由模式決定——挖哪一格，就變哪一格：**

| 模式 | 用在 | 第 1 層＝ | 例 |
| --- | --- | --- | --- |
| **A** | 8、9 字首 | 同字族，onset 是 target onset 的**單一成分** | stop → top、swing → sing / wing、ship → hip |
| **A** | 1–5 | 不必分層（同字族本來就只差 onset） | — |
| **B** | 6 | 同 onset，**同尾子音、異母音** | cat → cot / cut |
| **C** | 7–11 的開頭音選單 | 同 onset，**同母音、異尾子音** | sick → sit / sing / sink、cape → cap、sea → seat / seal |

**第 1 層不問階段是必要的**：cape 最該有的干擾項是 cap（階段一），sick 最該有的是 sit（階段一），stop 最該有的是 top（階段三）。若「同階段優先」，這些教學點全會被排到最後。

**實作時的一處收斂（模式 A）**：字族模式只實作第 1 層，第 1 層填不滿的名額直接從同族其他字隨機補，沒有「同階段優先」的第 2、3 層。理由是加了會改動階段 1–5 的既有行為（例如階段八的 -at session 裡，`flat` 會永遠不被抽來當 `cat` 的干擾項），而那不是階段八要解決的問題。模式 C 維持三層不變。

**第 1 層不設抽取上限**（Project 原建議抽 1–2 個以保留難度梯度，此項授權程式端決定）。理由：上限只在第 1 層很豐富時才生效，而那正是題目最好的時候——sick 的第 1 層是 sit / sing / sink，四選一全是「同母音、異尾子音」，正是階段七要練的；設上限會擠掉一個，換成 sock 這種異母音的**更簡單**選項，與「保留難度梯度」的用意相反。難度梯度由第 1 層本身的多寡自然形成：28 個階段七 target 的第 1 層數量分布為 0（6 個）、1（6 個）、2（9 個）、3（6 個）、4（1 個）。

**兩條實作上不可省的前提：**

1. **切法**：`母音段 = rime 開頭的連續母音字母`，`尾子音段 = 其餘`。所以 `ape` 拆成 `a` ＋ `pe`，cap(`a`|`p`) 對 cape(`a`|`pe`) 自動落在「同母音、異尾子音」，magic e 不必另開特例。
2. **「同母音」是同母音字母段，不是同母音音值。** cap /æ/ 和 cape /eɪ/ 的音值完全不同，若拿音值比對，階段十的第 1 層會全部落空。階段七剛好字母與音值一致，測不出這個錯；階段十才會爆。

**第 1 層可以是空的。** 現有 103 字實測：28 個模式 C target 裡有 6 個（lock、rock、sock、ring、lump、lamp）湊不出同母音的同伴——例如 s- 底下母音 o 的字只有 sock。這 6 個自然往第 2 層落，候選池和不分層時一樣，**不需要為此補字**。階段十一入庫後同樣量過：39 個模式 C target 的第 1 層數量分布為 0（18 個）、1（18 個）、2（3 個），空的比例比階段七高（母音組合的同 onset 同伴本來就少，例如 b- 底下拼 `oa` 的只有 boat），結論不變，**一樣不需要為此補字**。模式 A 那邊，階段十一的 35 個字族 target 第 1 層**全數為空**（sheet、sweep、tree、green、screen、spoon、stool、school、broom 等子音串字的成分字都不在同一個 rime 家族裡），同階段十的情形，一樣不補。

---

## C. 各階段題型與 family 的意義

**family 永遠是 rime 字族**（-uck、-op、-ake、-ain），不改成 pattern 名（st-、magic-e）。硬理由：現有題型的選項必須是同 rime 的真字（錯選會播那個字的音），以「st-」為單位出題，target stop 的干擾項會變成 flop、grop 之類的非字。

**session 規則（已實作）：選單列出「含該階段字」的字族；session 內容 = 該字族中 `stage ≤ 所選階段` 的字。** 所以階段三選 -op 只有 top/mop/hop/pop；階段八選 -op 是這四個加 stop —— rime 固定、onset 混入子音串，正是「一次只動一個變數」。

| 階段 | 模式 | 題型 | 程式端 |
| --- | --- | --- | --- |
| 7 | **A ＋ C** | 字族選單（-ack）挖 onset；開頭音選單（s-）挖整塊 rime | 已實作 |
| 8 | **A ＋ C** | 字族選單（-ock）挖 onset，onset 磚顯示 `cl` 整塊；開頭音選單（st-）挖整塊 rime | 已實作（模式 A 第 1 層：成分字必進選項） |
| 9 | **A ＋ C** | 字族選單（-ish）挖 onset，onset 磚顯示 `sh` 整塊；開頭音選單（sh-、f-）挖整塊 rime | 已實作 |
| 10 | **A ＋ C** | 字族選單（-ake）挖 onset；開頭音選單（c-）挖整塊 rime，`c` ＋ `[ap]` / `[ape]`，點錯播 cap（真字）就是辨別回饋 | 已實作 |
| 11 母音組合 | **A ＋ C** | 字族選單（-eet）挖 onset；開頭音選單（s-）挖整塊 rime，`s` ＋ `[ea]`／`[eat]`／`[eal]`／`[oap]`，母音組合的長短與異同就在整塊 rime 上對比 | 已實作（`RIME_MODE_STAGES` 加入 11，一行） |

**選單的收錄門檻（已實作）：同 onset／同字族的字（含 `stage` 較小的舊字）不足 2 個就不列進選單** —— 少於 2 字連一組選項都湊不出來，選了也開不了 session。這是 B2「模式 C 要同 onset ≥ 2」在程式端的落實。階段七 12 個開頭音全數 ≥2，選單不變；階段八 **st-（5 字）、cl-（4 字）、bl-／fl-／sp-／tr-／tw-（各 2 字）** 過關，只有 sn-、sw-、pl- 各 1 字被擋掉。**要開出新的開頭音 session，該 onset 補到第 2 個字即可**，例如 sw- 補 swing 之外的第二字。字族選單同樣套用此門檻，目前擋掉階段九的 -umb（thumb）與階段十的 -ute（cute）、-uge（huge）三族。

**階段十一的門檻結果（實測）：** 開頭音 18 個過關，`br-`、`gr-`、`qu-`、`sch-`、`scr-` 各 1 字被擋掉；字族擋掉 -eaf、-eal、-eeth、-oad、-oap、-oast、-oof、-oom、-ooth 九族。合計 31 個 session、74 題。green／queen／screen 走 -een、school 走 -ool，teeth／leaf／seal／soap／toast／toad／tooth／roof 八字族內只有自己、全靠開頭音 session 出題。**兩條路都被擋掉、因而完全出不了題的只有 `broom`**（`-oom` 與 `br-` 都只有它一字）—— 補第二個 `br-` 的字或第二個 `-oom` 的字，任一即可救回，這是選字決定。

**階段 10–11 不需要第四種模式。** 原本預告的「cap↔cape 辨別題」與「母音組合辨音題」**都由模式 C 涵蓋**，兩項**結案**。階段十一原定走模式 B（挖 rime 裡的母音單位），實際改用 A ＋ C：字族選單練「-eet 前面接什麼」，開頭音選單練「s 後面是 ea、eat、eal 還是 oap」—— 後者就是母音組合的辨音題，只是挖整塊 rime 而不是只挖母音那幾個字母。程式端僅把 11 加進 `RIME_MODE_STAGES`，**沒有新增任何模式**。

階段 10、11 的字均已入庫（各 44 字），本節到此全部落地。

## D. 對比組：繼續運作，不加開關

推導是跨階段的，新字會自動長出新組：deck/dock/duck（`d_ck`）、sing/song/sung（`s_ng`）、step/stop（`st_p`）。magic-e 字天然分流（cut=`c_t`、cute=`c_te`，不相撞）。

唯一的排除規則（已實作）：**`rime` 第二個字元也是母音的字（rain、boat、feet）不入對比組** —— 它們的母音是兩個字母，不是單母音對比。

**這條原本規劃是階段六專用的保護措施，2026-08-21 起改為永久規則。** 原訂到階段十一時把對比組的 key 從「onset ＋ rime 去掉第一個字母」改成「onset ＋ rime 去掉**開頭的母音連續段**」，讓 cat / cot / cut / coat 落進 `c_t` 一組、模式 B 自動成立，並刪掉本條排除規則。**這項推廣沒有執行** —— 階段十一改走模式 A ＋ C（見 §B2 ①、§C），不需要模式 B，key 維持原樣，排除規則留著。

**日後若真要開模式 B，代價先記在這裡（已用現有 253 字實測）：** 階段六的對比組會從 7 組變成 9 組 —— 多出 `b_t`(bat beet boat boot) 與 `sh_p`(sheep ship shop)，且既有的 `c_t` 會從 cat/cot/cut 變成 cat/coat/cot/cut，選項裡出現兩個字母的 `oa`。**這是階段六的行為變動，不是純新增**，要改就得連帶確認階段六還是不是家長要的樣子。

## E. 不要產出的清單

1. 不產 `stage: 6` 條目。
2. 不發明新欄位；**七欄一個都不能少**（`note` 可為空字串，**`zh` 不可為空**）。
3. onset 必須含完整子音串／digraph（ship → `sh` 不是 `s`）。自檢法：**rime 必須從第一個母音開始**。
4. 不收 y 當母音的字（fly、my、play、day）—— 程式的母音表沒有 y。
5. 不收 -all／-alk／wa- 開頭（ball、walk、want）—— 母音變音，同 DESIGN.md 的 -og 理由。
6. magic e 只收規則的短→長對應；不收例外拼法（have、give、love、come、some、one、done）。
7. 母音組合只收規則發音：ea 取 /iː/ 組（eat、sea），不收 bread、head；**同一 family 內母音發音必須一致**（-ood 會裂成 food /uː/ 對 good /ʊ/，這種拆開或擇一收）。
8. 每個新 family 至少 3 個真字（族下限）；**並照 B2 的模式對應約束再驗一次**（模式 C 要同 onset ≥2、模式 B 要同骨架 ≥3）。只滿足族下限不夠——階段七就是這樣漏掉的。
9. 不重複產出既有的字（現有清單以 words.json 為準）。

## F. 每階段一筆範例 JSON

```json
{ "word": "sick", "onset": "s",  "rime": "ick", "family": "-ick", "stage": 7,  "note": "生病;畫發燒躺床,勿與 hurt 混淆", "zh": "生病" }
{ "word": "stop", "onset": "st", "rime": "op",  "family": "-op",  "stage": 8,  "note": "停止;畫路牌不畫手勢",              "zh": "停止" }
{ "word": "ship", "onset": "sh", "rime": "ip",  "family": "-ip",  "stage": 9,  "note": "大船;與階段一 boat 區隔",         "zh": "船" }
{ "word": "cake", "onset": "c",  "rime": "ake", "family": "-ake", "stage": 10, "note": "",                                "zh": "蛋糕" }
{ "word": "rain", "onset": "r",  "rime": "ain", "family": "-ain", "stage": 11, "note": "",                                "zh": "雨" }
```

（實際交付時仍是一個 JSON 陣列，上面分行只為易讀。）

**Project 可自檢的四條規則：** ① 每筆 `onset + rime === word`；② `rime` 第一個字元 ∈ a/e/i/o/u；③ `stage` ∈ {7,8,9,10,11} 且與 A 節的分類一致；④ 七欄齊全且 `zh` 非空。交給 Claude Code 寫入時會再跑一次同樣的檢查。
