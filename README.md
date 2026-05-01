<<<<<<< HEAD
# autoposter
=======
# football-autopost-bot

Production-ready MVP Telegram bot for football predictions with moderation flow before channel publishing.

## Implemented Scope

- Python 3.11, aiogram 3, APScheduler, SQLAlchemy async, asyncpg, Alembic.
- Daily draft generation (match provider abstraction + mock provider).
- Moderation workflow in Telegram (approve/reject/edit button placeholder).
- Channel publishing only after approval.
- Fixed-time scheduler + retention cleanup (90 days).
- Result provider abstraction with mock.
- Admin-only commands and stats snapshots.
- Dockerfile + Railway `Procfile`.
- If `GEMINI_API_KEY` is empty, generator falls back to a deterministic template text.

## Architecture

Project is split by modules:

- `app/bot`: handlers, callbacks, keyboards
- `app/services`: business logic
- `app/providers`: external APIs abstractions
- `app/db`: ORM models, repositories, sessions
- `app/scheduler`: APScheduler jobs
- `app/domain`: enums/entities

## TODO (External APIs)

1. Replace `MockMatchProvider` with a stable free source API.
2. Implement `OpenRouterFallbackProvider` if fallback mode is needed.
3. Add concrete free `ResultProvider` integration (or keep semi-auto admin confirmation mode).

## Env Variables

See `.env.example`. Required minimum:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHANNEL_ID`
- `TELEGRAM_ADMIN_IDS`
- `TELEGRAM_MODERATION_CHAT_ID` (optional; if empty bot sends moderation drafts to all admin private chats)
- `DATABASE_URL`
- `TZ`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `ENABLE_OPENROUTER_FALLBACK`
- `OPENROUTER_API_KEY`
- `POST_FIXED_TIMES`
- `PREMATCH_WINDOW_HOURS`
- `MAX_DRAFTS_PER_DAY`

## Local Run

1. Create and activate environment:
   - `python -m venv .venv`
   - Windows: `.venv\Scripts\activate`
2. Install project:
   - `pip install -e .`
   - optional tests: `pip install -e .[dev]`
3. Configure env:
   - `copy .env.example .env`
   - fill required values.
4. Run migrations:
   - `alembic upgrade head`
5. Start bot:
   - `python -m app.main`

## Migrations

- New migration:
  - `alembic revision --autogenerate -m "message"`
- Apply:
  - `alembic upgrade head`
- Rollback one:
  - `alembic downgrade -1`

## Tests

- Run all:
  - `pytest -q`

Covered tests:

- generation text with mocked LLM
- moderation workflow state transitions
- retention cleanup invocation

## Railway Deploy

1. Create Railway project and PostgreSQL plugin.
2. Add env vars from `.env.example`.
   - For private moderation mode:
     - set `TELEGRAM_MODERATION_CHAT_ID` as empty
     - each admin from `TELEGRAM_ADMIN_IDS` must press `/start` in private chat with bot once.
3. Set start command:
   - `python -m app.main`
   or rely on `Procfile` worker.
4. Run migration as one-off command:
   - `alembic upgrade head`
5. Redeploy worker.

## Commands

- `/start`
- `/help`
- `/status`
- `/queue`
- `/stats`
- `/force_generate`
>>>>>>> 147fe0c (Initial commit: football autopost bot MVP)
