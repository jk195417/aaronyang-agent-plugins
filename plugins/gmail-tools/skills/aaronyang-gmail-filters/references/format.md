# filters.toml format

Each `[[rules]]` entry is criteria plus actions. Every action becomes its own Gmail filter (so each can change independently) unless `split = false`.

```toml
[[rules]]
name = "Bank A transfer results"        # optional note, not sent to Gmail
from = "notify@bank-a.example"
subject = "transfer result"
label = "Banks"

[[rules]]
from = "news@shop.example"
label = "Marketing"
archive = true                           # becomes a second filter
```

## Criteria (all optional, at least one required)

| Key | Gmail field |
|---|---|
| `from`, `to`, `subject` | From / To / Subject. `a OR b` and `(...)` work as in Gmail search. |
| `query` | Has the words (any Gmail search syntax, e.g. `list:news.example`). |
| `negated_query` | Doesn't have. |
| `has_attachment`, `exclude_chats` | `true` to enable. |
| `size`, `size_comparison` | Bytes, with `larger` or `smaller`. |

## Actions

| Key | Effect |
|---|---|
| `label` | Apply a label, or a list of labels. Missing labels are created on apply. |
| `archive` | Skip the inbox. |
| `mark_read` | Mark as read. |
| `star` | Star. |
| `important` | `true` always mark important, `false` never. |
| `category` | `primary`, `social`, `promotions`, `updates` or `forums`. |
| `never_spam` | Never send to spam. |
| `trash` | Delete. |
| `forward` | Forward to a verified address. |
| `remove_label` | Remove a label (appears only in exports of filters made elsewhere). |
| `split` | `false` keeps all actions of this rule in one Gmail filter. |

Gmail has no filter update: changing a rule means a new filter is created and, with `--prune`, the old one deleted.
