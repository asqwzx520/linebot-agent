<!-- generated-by: gsd-doc-writer -->
# API Reference

This document covers all HTTP endpoints exposed by the LINE Bot AI Agent FastAPI server and the five Gemini function-calling tools that the AI agent dispatches internally.

---

## Authentication

### HTTP Endpoints

The two HTTP endpoints use different authentication mechanisms:

| Endpoint | Mechanism |
|---|---|
| `GET /` | None — public health check |
| `POST /webhook` | LINE signature validation via `X-Line-Signature` header |

For the webhook endpoint, every inbound request from the LINE platform includes an `X-Line-Signature` header. The server validates this signature against `LINE_CHANNEL_SECRET` using `linebot.v3.WebhookParser`. Requests with a missing or invalid signature are rejected with HTTP `400`.

The server never exposes its own API key to callers. All Gemini API calls are made server-side using `GEMINI_API_KEY` (and optional `GEMINI_API_KEY_2` / `GEMINI_API_KEY_3`), which are read from environment variables and never returned in responses.

---

## Endpoints Overview

| Method | Path | Description | Auth Required |
|---|---|---|---|
| `GET` | `/` | Health check — confirms the server is running | No |
| `POST` | `/webhook` | LINE Messaging API webhook receiver | `X-Line-Signature` (LINE HMAC) |

---

## Endpoint Details

### `GET /`

Health check endpoint. Use this to verify the server is reachable and the FastAPI application has started successfully.

**Request**

No headers or body required.

**Response — `200 OK`**

```json
{"status": "LINE Bot AI Agent is running 🤖"}
```

---

### `POST /webhook`

Receives webhook events from the LINE Messaging API. Validates the `X-Line-Signature` header, parses the event payload, and dispatches events asynchronously via `handle_line_events`.

**Request Headers**

| Header | Required | Description |
|---|---|---|
| `X-Line-Signature` | Yes | HMAC-SHA256 signature computed by LINE from `LINE_CHANNEL_SECRET` |
| `Content-Type` | Yes | `application/json` (set by LINE platform automatically) |

**Request Body**

Raw JSON payload as sent by the LINE platform. The body is read as raw bytes and passed directly to `WebhookParser.parse()` for signature verification before any JSON deserialization occurs.

**Supported Event Types**

| LINE Event | Handling |
|---|---|
| `FollowEvent` | Sends a welcome text message listing the bot's capabilities |
| `MessageEvent` + `TextMessageContent` | Passes text to Gemini agent; replies with text and/or image |
| `MessageEvent` + `ImageMessageContent` | Downloads image bytes; passes to Gemini vision; replies with text |
| `MessageEvent` + `FileMessageContent` (PDF) | Downloads PDF (max 10 MB); extracts text; passes to Gemini for summary |
| `MessageEvent` + other file types | Replies informing the user only PDF is supported |
| All other event types | Silently ignored |

**Response — `200 OK`**

```json
{"status": "ok"}
```

Returned after all events have been dispatched. The LINE platform expects a `200` response within a few seconds; event processing itself runs via `asyncio`.

**Error Responses**

| Status | Condition |
|---|---|
| `400 Bad Request` | `X-Line-Signature` is missing or does not match — body: `{"detail": "Invalid signature"}` |
| `400 Bad Request` | Webhook body cannot be parsed — body: `{"detail": "Parse error: <message>"}` |

**Per-User Rate Limiting**

Internally, each `user_id` is limited to **10 messages per 60-second sliding window** (enforced in `app/rate_limiter.py`). Requests exceeding this limit receive a LINE text reply ("⚠️ 請求太頻繁，請稍後再試（每分鐘最多 10 則）。") but the HTTP response to LINE is still `200 OK`.

---

## Gemini Function-Calling Tools

These five tools are registered with the Gemini model using `google.generativeai` function calling. The model decides autonomously when to invoke them based on the conversation context. They are not directly callable via HTTP — they execute server-side during `process_text`.

Each tool is scoped to the current `user_id` via a closure created in `_make_tools(user_id)` (`app/gemini_agent.py`).

---

### `web_search`

Searches the web for up-to-date information.

**Arguments**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `query` | `str` | Yes | Search keyword or natural-language question |

**Returns**

`str` — a text summary of search results.

**When invoked:** queries about current events, weather, news, stock prices, or any real-time data.

---

### `memory_save`

Saves a piece of information to the user's long-term memory store (Supabase).

**Arguments**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `category` | `str` | Yes | One of: `preference`, `project`, `note`, `personal`, `general`. Any other value is coerced to `note`. |
| `content` | `str` | Yes | The information to remember. Truncated to 500 characters. |

**Returns**

`str` — confirmation message.

**When invoked:** user says "remember", "help me remember", or provides important personal information.

**Input sanitization:** `content` is capped at 500 characters; `category` is capped at 50 characters and validated against the allowed set to mitigate prompt injection.

---

### `memory_recall`

Retrieves stored memories for the current user.

**Arguments**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keyword` | `str` | No (default `""`) | Filter keyword. Leave empty to retrieve all recent memories. |

**Returns**

`str` — a bullet-point list of up to 10 matching memories, or a message indicating no memories are stored.

**Example return value**

```
我記得的事：
• preference: prefers dark mode
• note: meeting every Tuesday at 3pm
```

**When invoked:** the model needs to recall something the user said in a previous session.

---

### `memory_delete`

Deletes memories matching a keyword from the user's memory store.

**Arguments**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keyword` | `str` | Yes | Keyword identifying the memory entries to delete. |

**Returns**

`str` — deletion confirmation message.

**When invoked:** user explicitly requests deletion of a stored memory.

---

### `image_generate`

Generates an image from a text prompt using the configured image generation service (`app/image_gen.py`, backed by `HF_TOKEN`).

**Arguments**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `prompt` | `str` | Yes | English description of the desired image (e.g., `"a cute orange cat sitting on a cloud"`). English prompts produce best results. |

**Returns**

`str` — on success: `IMAGE_URL:<url>`. On failure: `ERROR:<message>`.

The server parses the `IMAGE_URL:` prefix from the Gemini reply and sends the URL to the user as a LINE `ImageMessage`. The text portion of the reply (if any) is sent separately as a `TextMessage`.

**When invoked:** user requests image generation ("幫我畫", "生成圖片", "畫一個", etc.).

---

## Model Fallback Chain

The Gemini agent attempts models in the following priority order when a `ResourceExhausted` or `ServiceUnavailable` error occurs. Each API key is tried at the current model tier before falling back to the next tier.

```
Key 1 + gemini-3.5-flash
Key 2 + gemini-3.5-flash
Key 3 + gemini-3.5-flash
Key 1 + gemini-3.1-flash
Key 2 + gemini-3.1-flash
Key 3 + gemini-3.1-flash
Key 1 + gemini-3.1-flash-lite
Key 2 + gemini-3.1-flash-lite
Key 3 + gemini-3.1-flash-lite
```

If all combinations are exhausted, the agent returns a user-facing error message rather than raising an unhandled exception.

---

## Error Handling Summary

| Layer | Condition | Outcome |
|---|---|---|
| HTTP (webhook) | Invalid `X-Line-Signature` | `400` with `"Invalid signature"` |
| HTTP (webhook) | Body parse failure | `400` with `"Parse error: ..."` |
| Rate limiter | > 10 messages / 60 s per user | LINE text reply warning; HTTP `200` returned to LINE |
| PDF handler | File > 10 MB | LINE text reply; processing skipped |
| Gemini agent | All model/key combinations exhausted | LINE text reply: generic error message |
| Event dispatcher | Any unhandled exception | Logged server-side; LINE text reply: "處理時發生錯誤，請稍後再試。" |

---

## Response Size Limits

LINE messages are limited to 5000 characters per bubble. The server chunks text replies at **4500 characters** (`_chunk_text` in `app/line_handler.py`) to stay within this limit. Each chunk is sent as a separate `TextMessage` in the same `ReplyMessageRequest`.
