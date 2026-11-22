# Setup

## 1. Google OAuth client

1. In a Google Cloud project, enable the Gmail API and create an OAuth client of type "Desktop app".
2. Save its JSON as `credentials.json` in the home folder.
3. If the OAuth consent screen is in testing, add your Gmail address as a test user. Authorization then expires after about 7 days and the script opens the browser again.

The first download opens a browser and writes `token.json` (read-only `gmail.readonly`). The filters skill uses the same `credentials.json` with its own `token_filters.json`.

## 2. targets.toml

Copy `assets/targets.example.toml` to `<home>/targets.toml`. Each `[[targets]]` entry is one kind of email:

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | Unique; used in file names. No spaces or underscores. |
| `from` | yes | Sender address. |
| `subject` | no | Only match emails with this phrase in the subject. |
| `password` | no | Password key, or a list tried in order. Omit for PDFs without a password. |

To stop collecting a sender, comment its entry out instead of deleting it, so its old files stay explained.

## 3. .env

Copy `assets/env.example` to `<home>/.env`. Key `CARD` reads `PDF_PASSWORD_CARD`, so several targets can share a password.

| Variable | Meaning |
|---|---|
| `PDF_PASSWORD_<KEY>` | Password for targets using that key. |
| `EXPORT_PATH` | Optional. Also copy decrypted PDFs to `<EXPORT_PATH>/YYYY-MM`. |

## 4. manifest.csv columns

| Column | Written by | Contents |
|---|---|---|
| `file`, `month`, `target` | both | Saved name, data month, target |
| `received_at`, `message_id`, `sender`, `subject`, `attachment` | download | Source email and original attachment name |
| `size`, `sha256`, `downloaded_at` | download | Downloaded file |
| `encrypted` | decrypt | `yes` if the original needed a password |
| `decrypted_sha256`, `decrypted_at` | decrypt | Decrypted copy |
| `exported_to` | decrypt | Exported copy, if any |

## Security

- The home folder holds plain-text passwords and a token that reads the whole mailbox. Keep it out of synced or shared folders; revoke the token in your Google account if it leaks.
- `manifest.csv` lists senders and subjects of financial mail; treat it like the PDFs.
