<!-- generated-by: gsd-doc-writer -->
# Configuration

All configuration for this LINE Bot AI assistant is loaded at startup via `app/config.py` using `python-dotenv`. Values are read exclusively from environment variables — either a local `.env` file (development) or the host platform's secret manager (production).

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | **Required** | — | LINE Messaging API channel access token, obtained from the LINE Developers Console |
| `LINE_CHANNEL_SECRET` | **Required** | — | LINE channel secret used to verify webhook request signatures |
| `GEMINI_API_KEY` | **Required** | — | Primary Google AI Studio API key for Gemini |
| `GEMINI_API_KEY_2` | Optional | — | Secondary Gemini API key from a different Google account, providing an independent quota pool |
| `GEMINI_API_KEY_3` | Optional | — | Tertiary Gemini API key from a third Google account |
| `SUPABASE_URL` | **Required** | — | Supabase project URL (e.g. `https://xxxx.supabase.co`) |
| `SUPABASE_ANON_KEY` | **Required** | — | Supabase publishable anon key — safe for client-side use; also used by backend read paths |
| `SUPABASE_SERVICE_ROLE_KEY` | **Required** | — | Supabase service role secret key — grants full access and bypasses RLS. **Never expose this value publicly.** |
| `HF_TOKEN` | Optional | `""` | Hugging Face token for SDXL image generation fallback via the Hugging Face Inference API |
| `PORT` | Optional | `8000` | TCP port the uvicorn server listens on. Set automatically by Render in production. |

## Config File Format

Environment variables are loaded by `app/config.py` at import time using `python-dotenv`. No separate JSON or YAML config file is used. The canonical list of accepted variables is defined in `.env.example`:

```dotenv
# LINE Bot (obtain from LINE Developers Console)
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_CHANNEL_SECRET=your_channel_secret_here

# Google Gemini (obtain from Google AI Studio)
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase (obtain from Supabase project settings)
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Hugging Face (optional, image generation fallback)
HF_TOKEN=your_huggingface_token_here
```

Copy `.env.example` to `.env` and fill in your values for local development:

```bash
cp .env.example .env
```

## Required vs Optional Settings

The following variables will cause runtime failures or silent misbehaviour if absent. `app/config.py` assigns an empty string as the default for all of them — there is no hard startup validation, but missing required values will produce errors when the relevant code path is first exercised:

- **`LINE_CHANNEL_ACCESS_TOKEN`** — used by `app/line_handler.py`; missing causes all outgoing LINE API calls to fail with an authentication error.
- **`LINE_CHANNEL_SECRET`** — used by `app/main.py`; missing causes every incoming webhook to fail signature verification and return `400`.
- **`GEMINI_API_KEY`** — used by `app/gemini_agent.py` via `GEMINI_API_KEYS`; missing means no AI responses can be generated.
- **`SUPABASE_URL`** and **`SUPABASE_SERVICE_ROLE_KEY`** — used by `app/memory.py` and `app/image_gen.py`; missing disables conversation memory and image storage.
- **`SUPABASE_ANON_KEY`** — used by `app/memory.py` and `app/image_gen.py` alongside the service role key.

Optional variables (`GEMINI_API_KEY_2`, `GEMINI_API_KEY_3`, `HF_TOKEN`) default to an empty string and are simply ignored when absent.

## Defaults

Defaults are applied directly in `app/config.py`:

| Variable | Default value | Set in |
|---|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | `""` | `app/config.py` line 6 |
| `LINE_CHANNEL_SECRET` | `""` | `app/config.py` line 7 |
| `SUPABASE_URL` | `""` | `app/config.py` line 8 |
| `SUPABASE_ANON_KEY` | `""` | `app/config.py` line 9 |
| `SUPABASE_SERVICE_ROLE_KEY` | `""` | `app/config.py` line 10 |
| `HF_TOKEN` | `""` | `app/config.py` line 11 |
| `PORT` | `8000` | `app/config.py` line 12 |

The Gemini key list (`GEMINI_API_KEYS`) is built by `_collect_gemini_keys()`, which iterates `GEMINI_API_KEY`, `GEMINI_API_KEY_2`, and `GEMINI_API_KEY_3` and collects only non-empty values. `GEMINI_API_KEY` (the first entry) defaults to `""` if the list is empty.

## Per-Environment Overrides

| Environment | Mechanism |
|---|---|
| **Local development** | `.env` file in the project root, loaded by `python-dotenv` |
| **Production (Render)** | Environment variables defined in `render.yaml` (`sync: false`) and managed through the Render dashboard secret manager |

The `render.yaml` service definition (`linebot-ai-agent`) declares the following variables as secrets (`sync: false`), meaning their values must be set manually in the Render dashboard and are never committed to the repository:

- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`
- `GEMINI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `HF_TOKEN`

`SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY_2`, and `GEMINI_API_KEY_3` are not listed in `render.yaml` but can be added as additional environment variables in the Render dashboard if required. <!-- VERIFY: confirm these variables are set via Render dashboard for production deployments -->

No `.env.development`, `.env.production`, or `.env.test` override files are present in the repository. All environment differentiation is handled by supplying different values on each target platform.
