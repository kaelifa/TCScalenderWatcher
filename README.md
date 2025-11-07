# Castle School Calendar Watcher

Watches these resources for changes:
- Page: https://www.castleschool.co.uk/calendar/academic-year-diary.htm
- PDF: https://www.castleschool.co.uk/uploads/pdf-files/1055-Academic_Year_Diary_202526.pdf

When a change is detected, a Telegram message is sent.

## Quick start

1. **Create a Telegram bot** (via `@BotFather`) and note the **bot token**.
2. **Get your chat ID**: send a message to your bot, then visit `https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates` and copy your numeric `chat.id`.
3. **Create a new GitHub repo** and upload this folder's contents.
4. In the repo, go to **Settings → Secrets and variables → Actions → New repository secret** and add:
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `TELEGRAM_CHAT_ID` = your chat id
5. Commit and push. The workflow runs on a schedule and on each push. It will store hashes in `state/` and commit updates when changes are seen.

## How it works

- The Action fetches the page HTML and the PDF and computes a SHA-256 for each.
- If the hash has changed since the last run, it sends a Telegram message and writes updated hash and metadata into `state/`.
- The workflow then commits the changed `state/` files back to the repo (so the next run can compare correctly).

## Tuning

- Edit the cron in `.github/workflows/calendar-watch.yml` if you want to check more/less often.
- To add more URLs, edit `watcher.py`'s `URLS` list.

