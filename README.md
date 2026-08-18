# 樂齡好生活｜熟齡健康生活自動營運網站

這是一個以 50 歲以上熟齡族與照顧父母的家庭為主要讀者、採 GitHub Pages 發布的自動化健康生活網站。

## 核心原則

- 把複雜資訊整理成看得懂、做得到的日常方法
- 只允許低風險生活與一般營養知識自動發布
- 疾病診斷、治療、處方藥、洗腎個別飲食及療效宣稱一律阻擋
- 每項健康主張需附可信來源
- 系統寧可不發布，也不為了篇數降低安全標準

## 網站結構

- `_data/site.yml`：網站定位、客群、內容分類與視覺設定
- `automation/content-policy.yml`：內容風險與禁止規則
- `automation/trusted-sources.yml`：可信來源白名單
- `automation/prompts/article-prompt.md`：每日文章產生規格
- `scripts/generate_article.py`：產生每日文章
- `scripts/validate_content.py`：發布前安全檢查
- `.github/workflows/daily-content.yml`：每日自動營運
- `.github/workflows/pages.yml`：GitHub Pages 部署

## 啟用每日 AI 文章

在 Repo 的 Settings → Secrets and variables → Actions 新增：

- `OPENAI_API_KEY`：OpenAI Platform API Key
- 選用 Repository variable `OPENAI_MODEL`：預設 `gpt-5.6-luna`

密鑰不得寫進 Repo、文章或工作流程檔案。

## 發布節奏

每日台灣時間約 05:30 執行：選題 → 官方資料研究 → 草稿 → 安全檢查 → 提交文章 → 部署。若缺少來源、出現高風險詞或結構不完整，該日不發布。

> 本站內容為一般健康生活資訊，不能取代醫師、藥師、營養師或其他醫療專業人員的個別建議。
