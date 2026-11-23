# aaronyang-agent-plugins

[English](README.md) | 繁體中文

Aaron Yang 的 agent plugin。一個 marketplace，Claude Code 和 GitHub Copilot 都能安裝。

## Plugins

| Plugin | Skill | 用途 |
|---|---|---|
| `knowledge-work` | `aaronyang-writing-rules` | 寫出精簡、真正改變行為的 agent 規則；判斷規則該放哪裡；用 evals 驗證 |
| | `aaronyang-plain-explain` | 把知識講給外行人聽懂：專有名詞、白話解釋、生活比喻、編號 References |
| | `aaronyang-knowledge-notes` | 把知識 ingest 進自己的知識庫，照各自現有的架構寫 |
| | `aaronyang-reflection` | 用 AAR 四問把教訓記進反省佇列，再批次 review：依影響、成本、等待時間排序，把每個教訓放到規則、skill、hook、筆記或原則 |
| | `aaronyang-orchestrating` | 安排長時間的 agent 工作：一個 session 一個目標、判斷在這裡做或交給 subagent 或另開 session、岔題時保留可見的 stack、附來源標記的交接、session 收尾 |
| `gmail-tools` | `aaronyang-gmail-pdf-archive`、`aaronyang-gmail-filters`、`aaronyang-gmail-triage` | 從 Gmail 依月份歸檔對帳單、收據 PDF；用 TOML 檔管理 Gmail 篩選器（lint、套用到舊信、事後抽查）；巡檢收件匣。個人設定與資料放在 plugin 以外的 home 資料夾 |
| `file-archiving` | `aaronyang-file-archiving` | 安全地歸檔個人文件：PARA 結構、比對雜湊再搬移、原始證據只增不改、年度資料夾、以 manifest 為正本。自己的資料夾地圖寫在該資料夾的 AGENTS.md |
| `ms-atwork` | `aaronyang-ms-atwork-download` | 下載 Morgan Stanley at Work 的所有文件與報表（對帳單、交易確認、稅表、RSU/ESPP 報表、授予明細）並產生 manifest。需 Windows 與 Edge，登入由你自己完成 |

一個 plugin 放會一起安裝、一起修改的 skill：`knowledge-work` 是每台機器都用的一套工作方法；工具類 plugin 各有自己的設定、平台與使用對象。需要哪個裝哪個，每個都能單獨使用。`knowledge-work` 裡的 skill 有對方就互相引用，所以單獨複製某個 skill 資料夾到別處也能用。

2026-11-23 以前，`knowledge-work` 的五個 skill 是分開的 plugin（`writing-rules`、`plain-explain`、`knowledge-notes`、`reflection`、`orchestrating`）。升級時安裝 `knowledge-work`，再移除這五個，避免同一個 skill 出現兩次。

Skill 名稱都加上 `aaronyang-` 前綴，因為個人 skill 資料夾、claude.ai、Copilot 不會替 skill 加命名空間，同名的 skill 可能互相覆蓋。

## Roadmap

規劃中的 plugin 記在[標了 `roadmap` 的 issue](https://github.com/jk195417/aaronyang-agent-plugins/issues?q=label%3Aroadmap)。

## 安裝

### claude.ai（建議；Claude Code 也會同步）

1. claude.ai → 自訂 → 外掛程式 → 新增 → 新增市集 → 從存放庫新增，填 `jk195417/aaronyang-agent-plugins`。
2. 開啟「自動同步」。要自動同步，GitHub 上的 Claude GitHub App 要能存取這個 repo；畫面提示時按「授予存取權」，只勾需要的 repo 即可。
3. 在市集清單裡把要用的 plugin 逐個按「新增」。

Windows、Mac 的 Claude Code（桌面 app 與終端機，v2.1.273 以上、用 claude.ai 帳號登入）每次啟動時會同步帳號裡的 plugin；剛裝好時可能要啟動兩次才看得到。WSL、用 API key 或 Bedrock 登入的 Claude Code 不會同步，改用下面的 CLI 安裝，兩種不要同時裝同一個 plugin，以免 skill 出現兩次。

### Claude Code（CLI）

```bash
claude plugin marketplace add jk195417/aaronyang-agent-plugins
claude plugin install knowledge-work@aaronyang-agent-plugins
```

### GitHub Copilot CLI

Copilot CLI 也會讀 `.claude-plugin/marketplace.json`。

```bash
copilot plugin marketplace add jk195417/aaronyang-agent-plugins
copilot plugin install knowledge-work@aaronyang-agent-plugins
```

### VS Code（Copilot agent plugins，預覽功能）

在 `settings.json` 的 `chat.plugins.marketplaces` 加入 `jk195417/aaronyang-agent-plugins`，再從 Extensions → Agent Plugins 安裝。

### 其他支援 Agent Plugins 的工具（Codex、Cursor 等）

每個 plugin 資料夾的根目錄另有一份符合 [Agent Plugins 1.0](https://agent-plugins.org/specification) 的 `plugin.json`。照各工具安裝 Agent Plugins 的方式，安裝 `plugins/<plugin>` 資料夾即可。Skill 採用 [Agent Skills](https://agentskills.io/specification) 格式，只讀 skill 的工具可以直接使用 `plugins/<plugin>/skills/` 底下的資料夾。

## 設定

Plugin 只有方法和程式；個人設定與資料都放在 plugin 以外，所以更新 plugin 不會蓋掉它們。第一次使用時，Claude 會照 skill 的說明問你位置並帶你建立。

| Plugin | 要設定什麼 | 放在哪 |
|---|---|---|
| `knowledge-work` | 知識庫與反省佇列在哪（例如 Notion 的資料庫） | 自己的 `~/.claude/CLAUDE.md`，例如「知識庫在 Notion『知識庫』頁」「反省佇列：Notion『反省佇列』資料庫」 |
| `gmail-tools` | Google Cloud OAuth 用戶端、要抓的寄件人、PDF 密碼、匯出位置 | home 資料夾：plugin 設定 `home`，或環境變數 `GMAIL_TOOLS_HOME`，預設 `~/.config/gmail-tools`。OAuth 申請步驟見 [setup.md](plugins/gmail-tools/skills/aaronyang-gmail-pdf-archive/references/setup.md)；密碼自己填進 `.env` |
| `ms-atwork` | 文件下載到哪（`.env` 的 `MS_OUTPUT_DIR`）、要抓的報表（`reports.toml`） | home 資料夾：plugin 設定 `home`，或 `MS_ATWORK_HOME`，預設 `~/.config/ms-atwork`。只支援 Windows＋Edge；網站介面語言要是英文；登入由你自己完成 |
| `file-archiving` | 你的資料夾地圖、命名格式 | 要整理的資料夾裡的 `AGENTS.md` 或 `CLAUDE.md` |

設定環境變數：Windows 用 `setx GMAIL_TOOLS_HOME "D:\path"`（開新的終端機才生效）；Mac 在 `~/.zshrc` 加 `export GMAIL_TOOLS_HOME="$HOME/path"`。home 資料夾不要放在雲端同步資料夾裡（裡面有 token 與密碼）。

## 共用工作原則

Plugin 不會載入常駐指令，所以 `principles.md` 要另外匯入。先 clone：

```bash
git clone https://github.com/jk195417/aaronyang-agent-plugins ~/code/aaronyang-agent-plugins
```

再在自己的 `~/.claude/CLAUDE.md` 加一行：

```markdown
@~/code/aaronyang-agent-plugins/principles.md
```

個人設定（知識庫位置、溝通習慣、資料夾慣例）留在自己的檔案；共用的方法放這裡，改一處大家都更新。

## 開發

`plugins/<plugin>/.claude-plugin/plugin.json` 是正本，根目錄的 `plugin.json` 由它產生。只改 Claude Code 的 manifest，再執行同步腳本；腳本也會檢查 marketplace 的描述和 skill 名稱。

```bash
uv run tools/sync_manifests.py          # 重新產生後檢查
uv run tools/sync_manifests.py --check  # 只檢查，有問題時以代碼 1 結束
uv run tests/test_gmail_filters.py      # gmail-tools 的離線測試
claude plugin validate .
for p in plugins/*; do claude plugin validate "$p"; done
```

改了 plugin 內容要升 `version`。merge 之後，從 claude.ai 安裝的會自動同步，重開 Claude Code 就是新版；沒更新的話，到 claude.ai 外掛程式 → 新增 → 管理市集，對這個市集按「檢查更新」。新增的 plugin 要在 claude.ai 另外按「新增」。

用 CLI 安裝的（例如 WSL）要手動更新；`autoUpdate` 曾經沒更新本機的 marketplace 副本：

```bash
claude plugin marketplace update aaronyang-agent-plugins
claude plugin update <plugin>@aaronyang-agent-plugins    # 每個有改的 plugin
claude plugin install <plugin>@aaronyang-agent-plugins   # 每個新的 plugin
```

## 授權

[Apache License 2.0](LICENSE) © Aaron Yang。可以自由使用、修改、分享，包括商用；條件是保留版權與授權聲明，並註明改過的檔案。在這次變更之前的版本以 CC BY-SA 4.0 釋出。
