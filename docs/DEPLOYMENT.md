<!-- generated-by: gsd-doc-writer -->
# Deployment

This document describes how to deploy the LINE Bot AI Agent to Render.com using Docker.

---

## Deployment Targets

The project supports one deployment target:

| Platform | Config File | Type |
|----------|-------------|------|
| Render.com | `render.yaml`, `Dockerfile` | Docker web service (free tier) |

- **Service name:** `linebot-ai-agent` (as defined in `render.yaml`)
- **Live URL:** <!-- VERIFY: https://linebot-agent.onrender.com -->
- **Webhook endpoint:** <!-- VERIFY: https://linebot-agent.onrender.com/webhook -->

The `Dockerfile` uses `python:3.11-slim` as the base image, installs dependencies from `requirements.txt`, and starts the application with `uvicorn` on the port provided by Render's `$PORT` environment variable (defaulting to `8000`).

---

## Build Pipeline

No CI/CD pipeline is configured in this repository (no `.github/workflows/` files are present).

Deployments are triggered manually or automatically by Render.com on push to the connected GitHub branch.

**Render.com build and start commands** (from `render.yaml`):

1. **Build command:** `pip install -r requirements.txt`
2. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Docker-based local build** (from `Dockerfile`):

```bash
# Build the image
docker build -t linebot-agent .

# Run the container locally
docker run -p 8000:8000 --env-file .env linebot-agent
```

The application exposes port `8000` internally; Render injects its own `$PORT` at runtime.

---

## Environment Setup

All environment variables must be set in the Render.com dashboard under the service's **Environment** tab. None of the secret values are stored in the repository.

| Variable | Required | Description |
|----------|----------|-------------|
| `LINE_CHANNEL_ACCESS_TOKEN` | Required | LINE Messaging API channel access token |
| `LINE_CHANNEL_SECRET` | Required | LINE Messaging API channel secret for webhook signature verification |
| `GEMINI_API_KEY` | Required | Primary Google Gemini API key |
| `GEMINI_API_KEY_2` | Optional | Second Gemini API key (separate Google account quota) |
| `GEMINI_API_KEY_3` | Optional | Third Gemini API key (separate Google account quota) |
| `SUPABASE_URL` | Required | Supabase project URL |
| `SUPABASE_ANON_KEY` | Required | Supabase anonymous (public) key |
| `SUPABASE_SERVICE_ROLE_KEY` | Required | Supabase service role key (full backend access) |
| `HF_TOKEN` | Optional | Hugging Face API token |
| `PORT` | Injected by Render | HTTP port the server listens on (Render sets this automatically) |

See `docs/CONFIGURATION.md` for a full description of each variable and its effect on the application.

> **Note:** `render.yaml` declares `sync: false` for all secrets, meaning their values are never read from the file — they must be entered directly in the Render dashboard.

---

## Rollback Procedure

Render.com retains a deploy history for each service. To roll back to a previous deployment:

1. Open the Render.com dashboard <!-- VERIFY: https://dashboard.render.com -->.
2. Navigate to the `linebot-ai-agent` service.
3. Click **Deploys** in the left sidebar.
4. Locate the last known-good deploy and click **Redeploy**.

Alternatively, revert the offending commit in the GitHub repository (`asqwzx520/linebot-agent`) and push — Render will automatically trigger a new build from the reverted state.

---

## LINE Webhook Configuration

After a successful deployment, the LINE webhook URL must be registered in the LINE Developers Console:

1. Log in to the [LINE Developers Console](https://developers.line.biz/).
2. Select your channel under the target provider.
3. Go to **Messaging API** > **Webhook settings**.
4. Set the **Webhook URL** to:
   ```
   https://linebot-agent.onrender.com/webhook
   ```
   <!-- VERIFY: confirm this matches the actual Render service URL -->
5. Enable **Use webhook**.
6. Click **Verify** — the console sends a test POST request; the service should return `{"status": "ok"}`.

---

## Monitoring

No monitoring library (Sentry, Datadog, New Relic, OpenTelemetry) is included in `requirements.txt`.

Runtime logs are available in the Render.com dashboard under the service's **Logs** tab. <!-- VERIFY: confirm log retention period on Render free tier -->

The health of the service can be checked via the root endpoint:

```bash
curl https://linebot-agent.onrender.com/
# Expected response: {"status": "LINE Bot AI Agent is running 🤖"}
```

<!-- VERIFY: confirm the above URL is reachable after deployment -->

---

## Free Tier Considerations

Render.com free tier web services spin down after a period of inactivity. The first request after a cold start may take 30–60 seconds to respond. <!-- VERIFY: confirm current Render free tier spin-down and cold-start behaviour -->

To keep the service warm, consider setting up an external uptime monitor that pings the root endpoint (`/`) at regular intervals.
