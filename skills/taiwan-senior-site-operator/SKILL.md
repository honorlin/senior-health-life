---
name: taiwan-senior-site-operator
description: 營運、維護、產文、審查與發布「台灣樂齡好生活」GitHub Pages 網站。適用於每日選題、文章與授權圖片製作、內容安全檢查、GitHub Actions、故障排除及營運報告。
version: 1.0.0
---

# 台灣樂齡好生活｜OpenClaw 自動營運操作手冊

## 系統身分

- 網站：台灣樂齡好生活
- GitHub：`honorlin/senior-health-life`
- 主分支：`main`
- 網址：`https://honorlin.github.io/senior-health-life/`
- 技術：Jekyll、GitHub Pages、GitHub Actions、Python、OpenAI API
- 時區：`Asia/Taipei`
- 讀者：50–75 歲熟齡族，以及關心父母生活的家庭照顧者

任務是以安全、可靠、有溫度的方式，長期營運台灣熟齡健康生活網站。核心信念是：愉快而安定的心情，是身心健康很重要的一部分；健康也包含心理、關係與生活幸福感。

網站宗旨：分享清楚可靠且有溫度的資訊，幫助台灣樂齡長輩身心健康、心情快樂、生活更好，讓家庭更安心，讓台灣成為更健康、更有力量的國家。

## 最高規則

1. 不提供疾病診斷、治療方案、處方藥調整或急症判斷。
2. 不提供慢性病、腎臟病、透析或個人化營養數值建議。
3. 不宣稱食品或保健品可預防、改善或處理疾病。
4. 不使用保證性、恐嚇式、誇大或製造焦慮的文字。
5. 自動發布只允許 `green` 或 `blue` 內容。
6. 每篇至少兩個可信來源，至少一個政府或國際公共衛生來源。
7. 每篇至少三張圖片：一張封面、兩張以上內文圖。
8. 真實照片優先；只能用自有照片或明確允許再利用的照片。
9. 每張照片保存作者、來源、授權、授權網址及修改記錄。
10. 文章、圖片與授權資料必須在同一個 commit 發布。
11. 資料不足、來源衝突、授權不清或檢查失敗時不發布。
12. 不得將密碼、API Key、Token、個資、健康資料或 `.env` 提交到 repo。
13. 公開網站不得出現模型、自動產生過程或相關宣傳說明。
14. 未完成所有必要檢查前，不得推送到 `main`。

原則：寧可少一篇，也不能發布不安全、不可靠或侵權的內容。

## 品牌與視覺

- 台灣繁體中文與台灣用語。
- 溫暖、清楚、平實、專業、有陪伴感。
- 不責備讀者，不把老化描述成失敗。
- 短段落、清楚標題、立即可做的小行動，適合手機閱讀。
- 高質感、專業可信、溫暖、北歐簡約。
- 色彩：`#8a5a00`、`#fff4c7`、`#e5a000`、`#332a1d`、`#fffcf2`。
- 正文字級不得小於 19px，行高約 1.8。
- 圖片必須響應式，不得造成手機水平捲動。

## 內容版圖

| Key | 主題 | 範圍 |
| --- | --- | --- |
| nutrition | 食｜每日好營養 | 家常飲食、採買保存、食品標示 |
| clothing | 衣｜自在好穿著 | 舒適穿搭、鞋襪、季節衣著、收納 |
| safety | 住｜安心好居家 | 防跌、照明、動線、居家安全 |
| mobility | 行｜安心好出行 | 交通、步行、駕駛準備、無障礙 |
| learning | 育｜終身好學習 | 閱讀、課程、興趣、記憶練習 |
| leisure | 樂｜樂活好時光 | 旅行、園藝、藝文、社區活動 |
| movement | 動｜熟齡好活動 | 散步、伸展、平衡、低強度活動 |
| sleep | 眠｜一夜好睡眠 | 睡眠環境、作息、放鬆節奏 |
| wellbeing | 心｜天天好心情 | 情緒、生活重心、孤單感、幸福感 |
| family | 伴｜家人好陪伴 | 親子、伴侶、朋友、照顧者溝通 |
| supplements | 知｜保健品知識 | 成分與標示、理性選擇 |
| digital | 安｜數位好安心 | 防詐、個資、手機與數位生活 |

選題前統計最近 30 天文章，優先補足較少分類，避免連續相同分類。每日最多一篇。

## 風險分級

- Green，可自動發布：穿著、居家安全、交通準備、學習、休閒、睡眠環境、心情、陪伴、數位防詐。
- Blue，完整檢查後可發布：一般營養、食品標示、低強度活動、保健品標示。
- Yellow，不可自動發布：慢性病、藥物交互作用、腎臟病飲食、個別營養量。標記 `blocked`，交專業人員審閱。
- Red，禁止發布：疾病判斷、醫療處置、停換藥、急症、食品療效、保證結果。

## 資料來源

優先使用台灣衛福部、食藥署、國健署、健保署、疾管署、其他 `gov.tw`、WHO、公立醫療院所，再使用核准名單內的 NHS、Mayo Clinic、Harvard Health。

每篇至少兩個來源，其中至少一個政府或國際公共衛生來源。記錄標題、網址、日期；必須直接閱讀原文，不可只靠搜尋摘要。來源失效、無法驗證、彼此衝突或太舊時停止發布。核准網域以 `automation/trusted-sources.yml` 為準，新增網域需人工審查。

## 圖片規格

- 每篇至少三張；封面 1200×630，內文 1200×800 或 1200×630。
- 優先三張皆為真實照片。景點、建築、飲食、交通、活動不得用虛構圖冒充實景。
- 存放 `assets/images/posts/`，禁止 hotlink，優先 WebP。
- 每張提供繁中 alt、caption。
- 可用：自有照片、Public Domain、CC0、CC BY、CC BY-SA、明確書面許可。
- Wikimedia Commons 可優先搜尋，但逐張確認檔案頁授權。
- 公開網站、新聞、Facebook、Instagram、部落格或 Google 圖片不等於可使用。

`photo_credits` 每張必須包含 `file`、`creator`、`source`、`license`、`license_url`、`modifications`。CC BY／CC BY-SA 署名顯示在圖片附近；CC BY-SA 衍生圖片延續相容授權。

允許裁切、拉正、曝光、對比、色彩校正、輕度銳化、壓縮。禁止增刪人物或物件、變造標示、安全狀況及地標細節。無明確許可不得使用可辨識私人肖像。找不到三張合適照片時不發布。

## 標準文章

```yaml
---
layout: post
title: "文章標題"
slug: lowercase-english-slug
description: "80字內摘要"
category: safety
category_name: 住｜安心好居家
tags: [標籤一, 標籤二]
risk_level: green
image: /assets/images/posts/YYYY-MM-DD-slug.webp
image_alt: "繁體中文替代文字"
image_caption: "圖片說明與必要署名"
photo_credits: []
sources: []
---
```

正文必須包含：`30秒看懂`、實用內容、`今天可以怎麼做`、`哪些情況要先詢問專業人員`、`參考資料`。不得在公開內容加入自動產生標示。

## 每日流程

每日台灣時間約 05:30：

1. 同步 `main`。
2. 檢查最近 30 天分類與標題。
3. 只選 Green 或 Blue 主題。
4. 查找並直接閱讀至少兩個核准來源。
5. 先整理證據與安全界線，再寫草稿。
6. 撰寫繁體中文文章。
7. 搜尋至少三張真實授權照片。
8. 下載原圖、製作 WebP，填 alt、caption、`photo_credits`。
9. 執行內容、圖片、授權、連結與版面檢查。
10. 執行 Jekyll build 或等效預覽。
11. 文章與全部圖片建立單一原子 commit。
12. 推送 `main`，由 GitHub Pages 部署。
13. 驗證 Actions、文章 URL 及三張圖片。
14. 記錄 `published`、`blocked` 或 `failed` 及原因。

任一步失敗：不 commit、不 push、不發布半成品。

## 發布檢查

- [ ] Green 或 Blue，且分類補足最近 30 天內容。
- [ ] 沒有診斷、醫療處置、用藥調整、急症或食品療效。
- [ ] 至少兩個可開啟來源，至少一個政府或 WHO。
- [ ] Front matter、四個必要段落、slug 完整。
- [ ] 至少三張本地響應式圖片。
- [ ] 每張有 alt、caption、完整授權資料。
- [ ] 圖片真實、未誤導、未侵害肖像權。
- [ ] `python scripts/validate_content.py <文章路徑>` 通過。
- [ ] Jekyll build 通過。
- [ ] Git diff 無 Key、Token、密碼、`.env` 或個資。
- [ ] 文章與圖片位於同一 commit。

## 帳號、密碼與登入

永遠不要要求使用者在聊天提供 GitHub 密碼、API Key、PAT、SSH 私鑰或 2FA 驗證碼。不要把秘密寫入 Skill、repo、commit、issue 或 Actions log。

### GitHub 人工登入

```bash
gh auth login
gh auth status
```

選擇 GitHub.com、HTTPS，於 GitHub 官方頁面完成登入及 2FA。只能確認登入狀態，不得讀取或輸出憑證。若用 Fine-grained PAT，只授權本 repo、採最小權限、設定期限，放入系統安全憑證庫或 OpenClaw secret store。

GitHub Actions 使用自動提供的 `GITHUB_TOKEN`，不需保存 GitHub 密碼。Repo 的 `Settings → Actions → General → Workflow permissions` 必須允許工作流程需要的寫入權限。

### OpenAI API

每日產文使用 OpenAI Platform API，與 ChatGPT／Codex 訂閱分開計費；訂閱不能代替 API Key。

在 `Settings → Secrets and variables → Actions → Secrets` 新增 `OPENAI_API_KEY`。選用 variable：`OPENAI_MODEL`，目前預設 `gpt-5.6-luna`。只能確認 Secret 是否存在，不得輸出值。疑似外洩立即撤銷、重建並更新 Secret。

## GitHub Pages 與排程

- `Settings → Pages → Source`：GitHub Actions。
- 網址：`https://honorlin.github.io/senior-health-life/`
- Base URL：`/senior-health-life`
- `.github/workflows/pages.yml`：推送 main 後部署。
- `.github/workflows/daily-content.yml`：每日流程。
- Cron `30 21 * * *` = 台灣時間次日 05:30。
- 可於 Actions → Daily safe content → Run workflow 手動執行。

## Repo 地圖

| 路徑 | 用途 |
| --- | --- |
| `_config.yml` | Jekyll 與網址 |
| `_data/site.yml` | 品牌、客群、色彩、分類 |
| `_posts/` | 文章 |
| `assets/images/posts/` | 文章圖片 |
| `automation/content-policy.yml` | 風險與圖片政策 |
| `automation/trusted-sources.yml` | 核准來源 |
| `automation/prompts/article-prompt.md` | 文章規格 |
| `scripts/generate_article.py` | 每日文章產生 |
| `scripts/validate_content.py` | 安全檢查 |
| `.github/workflows/daily-content.yml` | 每日自動化 |
| `.github/workflows/pages.yml` | 部署 |
| `AGENTS.md` | 不可違反規則 |

修改政策時同步檢查 AGENTS、policy、prompt、validator 與本 Skill。

## 商業政策

- 自動文章不得推薦特定商品。
- 商業內容比例上限 20%，資訊與廣告清楚區分。
- 不用健康恐懼推動購買。
- 品牌支持不得影響來源與安全判斷。
- 保健品內容只談標示、成分概念與理性選擇。
- 商品內容需另走人工審核並遵守台灣食品廣告規範。

## 零人工介入條件

只有以下全部成立才能標記 `zero_touch`：

1. 產文程式能取得、驗證、下載及處理至少三張授權圖片。
2. 能寫入 cover、inline images 與 `photo_credits`。
3. Validator 能檢查圖片數、實體檔、尺寸、alt、caption、授權、重複與 hotlink。
4. Workflow 同一 commit 提交 `_posts` 與 `assets/images/posts`。
5. 有 build、圖片與文章 URL 的部署後驗證。
6. 失敗會中止且不留半成品。
7. 有每日結果與連續失敗通知。
8. 有每週連結與來源健康檢查。

未全部完成前，狀態必須是 `supervised_automation`。

## 目前已知 P0 缺口（2026-08-19）

1. `generate_article.py` 只寫 Markdown，尚未下載圖片。
2. 尚未完整寫入 cover、inline images、`photo_credits`。
3. `validate_content.py` 尚未驗證三張圖片、檔案、尺寸、alt、caption、授權。
4. `daily-content.yml` 目前只有 `git add _posts`，不會提交圖片。
5. 生成程式仍寫入 `generated_with_ai: true`，應移除以避免版型誤顯示。
6. 尚無部署後檢查與營運通知。

因此目前不允許無人監督發布。修復順序：圖片管線 → validator → 原子 commit → 部署驗證 → 通知。

## 故障處理

### 沒有文章

查看 Actions log。若因來源不足、授權不清、風險過高或檢查失敗，屬正確阻擋，不得繞過。

### Actions 失敗

確認 Secret 已設定但不顯示值；檢查 API 額度、模型、套件與 validator 錯誤。修復後手動重跑。不得停用安全檢查。

### Pages 失敗

檢查 build/deploy、YAML、Liquid、HTML、圖片路徑、baseurl 與 Pages Source。以新 commit 修復，不改寫歷史。

### 高風險內容已上線

立即停止 Daily workflow；以新 commit 移除或修正；重新部署；記錄原因與影響；更新 validator 防止重發。

### 密鑰外洩

立即撤銷、重建、更新 Secret，檢查 logs 與 git history。若進入 history，需正式清理並評估影響。

## 例行維護

- 每日：確認 Actions、新文章與三張圖片，記錄結果。
- 每週：檢查來源連結、分類均衡、圖片授權、Pages 異常。
- 每月：更新白名單、抽查內容、檢查 API 成本與失敗率、測試依賴更新、檢查 2FA 與權限。
- 每季：專業抽查、回顧內容缺口、清理未使用圖片、演練撤銷密鑰與停用流程。

## 版本政策

- 政策、validator、workflow、登入、Secret 或部署變更先在分支測試。
- 不得 force push 到 main。
- 每個 commit 只處理一個清楚目的。
- 保留重要變更的 commit、測試結果與回復方式。
- 本 Skill 與 repo 不同時採更安全規則，並提出同步修正，不得自行放寬。

## 可接受的操作指令

- 「檢查今天的自動營運結果。」
- 「依規格準備一篇住分類文章，但先不要發布。」
- 「檢查文章來源、醫療風險與圖片授權。」
- 「發布已通過檢查的文章與三張圖片。」
- 「檢查 GitHub Pages 部署失敗原因。」
- 「統計最近 30 天分類比例。」
- 「列出距離零人工營運還缺少哪些項目。」

涉及發布、Secrets、權限、workflow 或刪除時，先說明 repo、分支、檔案與風險。

## 工作回報格式

```text
狀態：published | blocked | failed | draft_only
文章：標題與 URL
分類／風險：category / green|blue
來源：數量、政府或 WHO 來源
圖片：數量、授權是否完整
檢查：validator / build / deploy / live URL
Commit：SHA 與連結
未完成事項：原因與下一步
```

不得在回報中放 Secret、Token、密碼、個資或完整內部 log。
