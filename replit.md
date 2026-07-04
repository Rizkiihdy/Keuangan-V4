# Oliv — Personal Finance Bot

Oliv is a Telegram bot that helps track personal finances by logging transactions (income, expenses, transfers) to Google Sheets using natural language and receipt photo scanning powered by Gemini AI.

## Run & Operate

- `python main.py` — run the Telegram finance bot (main workflow)
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)

## Required Secrets

All secrets are stored in Replit's secret store (never hardcoded):
- `TELEGRAM_TOKEN` — Telegram bot token
- `GEMINI_API_KEY` — Google Gemini API key for AI parsing
- `GOOGLE_SERVICE_ACCOUNT_JSON` — Full JSON content of the Google service account key
- `GOOGLE_SHEET_ID` — (env var) Google Sheet ID for the spreadsheet

## Stack

- **Bot**: Python 3.11, python-telegram-bot, google-genai, gspread
- **AI**: Google Gemini 2.0/2.5 Flash (text + vision for receipt scanning)
- **Storage**: Google Sheets ("keuangan v4" → "Transaksi" worksheet)
- **API**: Express 5, Node.js, TypeScript (pnpm monorepo)
- **DB**: PostgreSQL + Drizzle ORM (for API server)

## Where things live

- `bot/bot.py` — Telegram command handlers and message routing
- `bot/gemini_ai.py` — AI transaction parsing and receipt OCR
- `bot/sheets.py` — Google Sheets read/write operations
- `bot/config.py` — Categories, accounts, keywords configuration
- `main.py` — Entry point (adds bot/ to sys.path, runs bot)
- `artifacts/api-server/` — Express API server
- `artifacts/mockup-sandbox/` — Vite component preview server

## Architecture decisions

- No login flow — bot is Telegram-native, user identity comes from Telegram
- All credentials in Replit secrets, never in code
- GOOGLE_SERVICE_ACCOUNT_JSON may have trailing commas (pasted from GCloud Console) — sheets.py cleans this automatically
- Bot runs via `python main.py` from workspace root (not `cd bot && python bot.py`)

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- The GOOGLE_SERVICE_ACCOUNT_JSON secret may be pasted with trailing commas — the loader in `bot/sheets.py` handles this automatically
- If the bot shows "409 Conflict", there are two instances running simultaneously — stop one and wait ~30s before restarting
- Job queue (weekly report scheduler) requires `pip install "python-telegram-bot[job-queue]"` — currently disabled gracefully
