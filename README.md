# aaronyang-agent-plugins

Aaron Yang 的 agent plugin marketplace，Claude Code 和 GitHub Copilot 都能安裝。

## 內容

| Plugin | 內容 |
|---|---|
| `aaronyang-playbook` | 共用工作原則（`principles.md`）＋ 三個 skill |

| Skill | 用途 |
|---|---|
| `aaronyang-writing-rules` | 寫出精簡、真正改變行為的 agent 規則；判斷規則該放哪裡；用 evals 驗證 |
| `aaronyang-plain-explain` | 用「專有名詞＋白話解釋＋生活比喻＋編號 References」把知識講清楚 |
| `aaronyang-knowledge-notes` | 把知識 ingest 進自己的知識庫，照各自現有的架構寫 |

Skill 一律加 `aaronyang-` 前綴，避免在沒有命名空間的地方（個人 skill、claude.ai、Copilot）撞名。

## 安裝

### Claude Code

```bash
claude plugin marketplace add jk195417/aaronyang-agent-plugins
claude plugin install aaronyang-playbook@aaronyang-agent-plugins
```

### GitHub Copilot CLI

Copilot CLI 也會讀 `.claude-plugin/marketplace.json`。

```bash
copilot plugin marketplace add jk195417/aaronyang-agent-plugins
copilot plugin install aaronyang-playbook@aaronyang-agent-plugins
```

### VS Code（Copilot agent plugins，預覽功能）

在 `settings.json` 的 `chat.plugins.marketplaces` 加入 `jk195417/aaronyang-agent-plugins`，再從 Extensions 的 Agent Plugins 安裝。

### claude.ai

把 `plugins/aaronyang-playbook/skills/` 底下的 skill 資料夾壓縮後，上傳到 claude.ai 的 skills。

## 共用工作原則

Plugin 不會自動載入常駐指令，所以 `principles.md` 要自己匯入。先 clone 這個 repo：

```bash
git clone https://github.com/jk195417/aaronyang-agent-plugins ~/code/aaronyang-agent-plugins
```

再在自己的 `~/.claude/CLAUDE.md` 加一行：

```markdown
@~/code/aaronyang-agent-plugins/plugins/aaronyang-playbook/principles.md
```

個人的設定（知識庫位置、溝通習慣、資料夾慣例）留在自己的檔案；共用的方法放這裡，改一處大家都更新。

## 開發

```bash
claude plugin validate .
claude plugin validate ./plugins/aaronyang-playbook
```
