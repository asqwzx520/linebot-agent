<!-- generated-by: gsd-doc-writer -->
# Getting Started

This guide walks you through deploying the LINE Bot AI Agent to Render.com in five main stages: gather API keys, set up Supabase, push code to GitHub, deploy on Render, and connect the LINE Webhook.

For a step-by-step beginner walkthrough with screenshots and detailed instructions, see [SETUP_GUIDE.md](../SETUP_GUIDE.md). This document is the concise quick-start reference.

Estimated time: 60–90 minutes.

---

## Prerequisites

You need the following accounts and tools before starting. All services have a free tier.

| Requirement | Version / Detail | Where to get it |
|---|---|---|
| Python | 3.11 | Managed by Docker on Render — no local install needed for cloud deploy |
| Git | Any recent version | https://git-scm.com/download/win |
| LINE account | — | https://line.me/ |
| LINE Developers account | — | https://developers.line.biz/ |
| Google account | For Gemini API key | https://aistudio.google.com/ |
| Supabase account | Free tier | https://supabase.com/ |
| GitHub account | Free tier | https://github.com/ |
| Render.com account | Free tier | https://render.com/ |

---

## Installation Steps

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/linebot-agent.git
cd linebot-agent
```

If you already have the project files locally, initialise git and push to a new GitHub repository instead:

```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/linebot-agent.git
git push -u origin master
```

### 2. Copy the environment variable template (local development only)

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials (see the [API Keys](#api-keys) section below). This file is only used when running locally — Render.com receives these values as environment variables set in its dashboard.

### 3. Install dependencies (local development only)

```bash
pip install -r requirements.txt
```

---

## API Keys

Collect the following values before deploying. Keep them in a text file temporarily.

### LINE Channel credentials

1. Go to https://developers.line.biz/ and log in with your LINE account.
2. Create a Provider, then create a **Messaging API** channel inside it.
3. On the **Messaging API** tab: scroll to **Channel access token** and click **Issue**. Copy the value.
4. On the **Basic settings** tab: copy the **Channel secret**.

### Gemini API key

1. Go to https://aistudio.google.com/ and log in with a Google account.
2. Click **Get API key** in the left sidebar, then **Create API key**. Copy the value.
3. Optional: repeat with up to two additional Google accounts and set them as `GEMINI_API_KEY_2` and `GEMINI_API_KEY_3` in Render for extra free-tier quota.

### Supabase credentials

1. Go to https://supabase.com/ and create a new project.
   - Region: Southeast Asia (Singapore) is recommended for LINE users in Taiwan/Asia.
   - Note your database password.
2. Go to **Project Settings → API**.
   - Copy **Project URL** (format: `https://YOUR_PROJECT_REF.supabase.co`).
   - Copy the **anon / public** key.
3. Go to **SQL Editor → New query**. Paste the contents of `setup_supabase.sql` from this repository and click **Run**. This creates the `memories` and `conversations` tables.
4. Go to **Storage → New bucket**. Name it `images` and enable **Public bucket**.

### HuggingFace token (optional)

Used as a fallback image generation provider. Get a token at https://huggingface.co/settings/tokens. If omitted, image generation falls back to Pollinations only.

---

## First Run

### Cloud deployment on Render.com

1. Log in to https://render.com/ with your GitHub account.
2. Click **New + → Web Service** and connect your `linebot-agent` repository.
3. Configure the service:

   | Setting | Value |
   |---|---|
   | Name | `linebot-agent` (or any name) |
   | Region | Singapore |
   | Branch | `master` |
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Instance Type | **Free** |

4. Scroll to **Environment Variables** and add each key:

   | Key | Value |
   |---|---|
   | `LINE_CHANNEL_ACCESS_TOKEN` | Your LINE channel access token |
   | `LINE_CHANNEL_SECRET` | Your LINE channel secret |
   | `GEMINI_API_KEY` | Your Gemini API key |
   | `SUPABASE_URL` | Your Supabase project URL |
   | `SUPABASE_ANON_KEY` | Your Supabase anon key |
   | `HF_TOKEN` | Your HuggingFace token (optional) |

5. Click **Create Web Service**. Deployment takes approximately 3–5 minutes. The service is ready when the logs show `Uvicorn running on http://0.0.0.0:PORT`.
6. Copy your Render service URL — it will look like `https://linebot-agent-xxxx.onrender.com`.

### Local development

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The server listens on port `8000` by default (controlled by the `PORT` environment variable).

---

## Connect the LINE Webhook

1. Return to https://developers.line.biz/ and open your channel.
2. Click the **Messaging API** tab.
3. Set **Webhook URL** to your Render URL with `/webhook` appended:
   ```
   https://linebot-agent-xxxx.onrender.com/webhook
   ```
4. Click **Update**, then **Verify**. You should see **Success**.
5. Ensure **Use webhook** is toggled on.
6. Disable **Auto-reply messages** and **Greeting messages** to prevent them from interfering with the bot.

---

## Common Setup Issues

**`git push` prompts for username and password**
Use your GitHub username and a Personal Access Token (not your account password). Generate one at GitHub → Settings → Developer settings → Personal access tokens.

**Render deployment fails**
Click **Logs** on the Render dashboard. The most common causes are a missing or misspelled environment variable, or a `requirements.txt` dependency installation error.

**LINE Webhook Verify returns an error**
Confirm the Render deployment completed successfully (log shows `Uvicorn running`), and that the webhook URL includes `/webhook` at the end.

**Bot does not reply**
Check the Render live logs for Python exceptions. The most frequent cause is an incorrect `GEMINI_API_KEY` or exhausted free-tier quota.

**Images do not display**
Confirm the Supabase Storage `images` bucket exists and is set to **Public**.

**First message after a period of inactivity takes 20–30 seconds**
This is expected behaviour on Render's free tier. The service sleeps after 15 minutes of inactivity and needs a cold-start on the next request. Subsequent messages respond normally.

---

## Updating the Deployed Bot

Push changes to GitHub and Render will automatically detect the push and redeploy:

```bash
git add -A
git commit -m "describe your change"
git push
```

---

## Next Steps

- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — System components, data flow, and module overview.
- [docs/CONFIGURATION.md](CONFIGURATION.md) — Full environment variable reference including optional settings.
- [SETUP_GUIDE.md](../SETUP_GUIDE.md) — Detailed beginner walkthrough with every step explained.
