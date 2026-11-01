# aaronyang-agent-plugins

[English](README.md) | 繁體中文

Aaron Yang 的 agent plugin。一個 marketplace，Claude Code 和 GitHub Copilot 都能安裝。

## Plugins

| Plugin | Skill | 用途 |
|---|---|---|
| `writing-rules` | `aaronyang-writing-rules` | 寫出精簡、真正改變行為的 agent 規則；判斷規則該放哪裡；用 evals 驗證 |
| `plain-explain` | `aaronyang-plain-explain` | 把知識講給外行人聽懂：專有名詞、白話解釋、生活比喻、編號 References |
| `knowledge-notes` | `aaronyang-knowledge-notes` | 把知識 ingest 進自己的知識庫，照各自現有的架構寫 |

需要哪個裝哪個，每個都能單獨使用。`knowledge-notes` 有裝 `plain-explain` 時會用它的格式，沒裝就用內建的精簡格式。

Skill 名稱都加上 `aaronyang-` 前綴，因為個人 skill 資料夾、claude.ai、Copilot 不會替 skill 加命名空間，同名的 skill 可能互相覆蓋。

## 安裝

### Claude Code

```bash
claude plugin marketplace add jk195417/aaronyang-agent-plugins
claude plugin install writing-rules@aaronyang-agent-plugins
claude plugin install plain-explain@aaronyang-agent-plugins
claude plugin install knowledge-notes@aaronyang-agent-plugins
```

### GitHub Copilot CLI

Copilot CLI 也會讀 `.claude-plugin/marketplace.json`。

```bash
copilot plugin marketplace add jk195417/aaronyang-agent-plugins
copilot plugin install writing-rules@aaronyang-agent-plugins
```

### VS Code（Copilot agent plugins，預覽功能）

在 `settings.json` 的 `chat.plugins.marketplaces` 加入 `jk195417/aaronyang-agent-plugins`，再從 Extensions → Agent Plugins 安裝。

### claude.ai

把 `plugins/<plugin>/skills/` 底下的 skill 資料夾壓縮後，上傳到 claude.ai 的 skills 設定。

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

```bash
claude plugin validate .
for p in plugins/*; do claude plugin validate "$p"; done
```

## 授權

[GNU LGPL v3.0 或更新版本](COPYING.LESSER)（LGPL 以 [GNU GPL v3.0](COPYING) 為基礎）。
