<!-- generated-by: gsd-doc-writer -->
# Development Guide

This guide covers local development setup, the module structure, code style conventions, and the deployment workflow for the LINE Bot AI Agent.

## Local Setup

1. Clone the repository and enter the project directory:

```bash
git clone <your-repo-url>
cd LINEBOT
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate.bat
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in all required API keys:

```bash
copy .env.example .env
```

Edit `.env` and set at minimum: `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`, `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY`. See `docs/CONFIGURATION.md` for the full variable reference.

5. Start the development server with hot-reload:

```bash
uvicorn app.main:app --reload --port 8000
```

### One-Command Local Start (Windows)

`start.bat` automates steps 5 plus launching ngrok in a second terminal window:

```bat
start.bat
```

It checks for `.env`, starts `uvicorn --reload` on port 8000, then opens ngrok on the same port. After both windows are up, copy the `https://xxxx.ngrok-free.app` URL from the ngrok window, paste it into the LINE Developers Console as the Webhook URL (append `/webhook`), click **Verify**, and enable **Use webhook**.

## Build Commands

There is no compilation step — Python runs directly from source. The commands used across dev and production are:

| Command | Context | Description |
|---|---|---|
| `uvicorn app.main:app --reload --port 8000` | Local dev | Run with hot-reload on port 8000 |
| `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | Docker / Render | Production start command |
| `pip install -r requirements.txt` | Setup / CI | Install all runtime dependencies |

## Module Overview

All application code lives under `app/`. Each module has a focused responsibility:

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI entry point; `/` health check and `/webhook` POST handler |
| `app/config.py` | Loads environment variables via `python-dotenv`; exposes typed constants |
| `app/line_handler.py` | Parses and dispatches incoming LINE events |
| `app/gemini_agent.py` | Gemini API integration; multi-key rotation logic |
| `app/memory.py` | Conversation history read/write against Supabase |
| `app/image_gen.py` | Image generation via Hugging Face Inference API |
| `app/rate_limiter.py` | Per-user rate limiting to guard against API quota exhaustion |
| `app/search.py` | DuckDuckGo web search integration |

## Code Style

No automated linter or formatter is configured in this project. The following conventions are used in the existing codebase:

- **Docstrings** — module-level docstrings use triple-quoted strings in Traditional Chinese (matching existing modules).
- **Imports** — standard library first, then third-party, then local `app.*` imports.
- **Async** — all route handlers and event processors are `async def`; blocking I/O calls should use `await`.
- **Environment variables** — all config is centralized in `app/config.py`; never read `os.getenv` directly outside that module.

If you add a linter (e.g., `ruff`, `black`), add its config to `pyproject.toml` (create one if needed) and document the run command here.

## Adding a New Feature Module

1. Create `app/<feature>.py`.
2. Add any new environment variables to `.env.example` and `app/config.py`.
3. Import and wire up the feature in `app/line_handler.py` or `app/main.py` as appropriate.
4. Update `docs/ARCHITECTURE.md` if the module introduces a new external dependency or data flow path.

## Branch and Deployment Conventions

There is no formal branch naming convention documented. The default branch is `master`.

**Deployment is automatic:** any push to `master` triggers a Render redeploy via the `render.yaml` configuration. The build command on Render is `pip install -r requirements.txt` and the start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

Because there is no CI pipeline, make sure the server starts cleanly locally before pushing to `master`:

```bash
uvicorn app.main:app --port 8000
# Confirm {"status": "LINE Bot AI Agent is running 🤖"} at http://localhost:8000
```

## PR Process

No pull request template is configured. Recommended practice before merging to `master`:

- Verify the local dev server starts without errors after your changes.
- Confirm the `/webhook` endpoint returns `{"status": "ok"}` for a valid LINE signature.
- Update `.env.example` if any new environment variables were added.
- Update the relevant doc in `docs/` if architecture or configuration changed.
