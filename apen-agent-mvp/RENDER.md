# Deploy APEN Agent MVP on Render

## 1. Create a Web Service

1. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Web Service**.
2. Connect your Git repo (e.g. GitHub).
3. **Root Directory:** set to `apen-agent-mvp` (if the repo root is the parent folder).
4. **Runtime:** Python 3.
5. **Build Command:** `pip install -r requirements.txt`
6. **Start Command:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`

## 2. Environment variables

In the service → **Environment** tab, add:

| Key | Required | Notes |
|-----|----------|--------|
| `BASE_URL` | Recommended | Your app URL, e.g. `https://apen-agent-mvp.onrender.com` (so webhook URL is correct). |
| `OPENAI_API_KEY` | For voice/audio | Needed for Whisper (upload recording) and AI intent/summary. |
| `GOOGLE_CALENDAR_ID` | For calendar | `primary` or your calendar ID. |
| `VAPI_ASSISTANT_ID` | For Vapi | Your assistant ID if using dynamic assistant (Option B). |

### Calendar: use OAuth (no service account key)

Because Render doesn’t have a local file system for a JSON key and many orgs block service account keys, use **OAuth 2.0**:

1. **On your machine** (one time): get a refresh token:
   - In Google Cloud → Credentials → Create credentials → **OAuth client ID** → Application type: **Web application** (not Desktop).
   - Under **Authorized redirect URIs** add: `http://localhost:8765/` (exactly).
   - Copy Client ID and Client secret; in `.env` set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
   - Run: `python scripts/oauth_refresh_token.py` and sign in in the browser.
   - Copy the printed **refresh token**.
2. **On Render** → Environment, add:
   - `GOOGLE_CLIENT_ID` = (your OAuth client ID)
   - `GOOGLE_CLIENT_SECRET` = (your OAuth client secret)
   - `GOOGLE_REFRESH_TOKEN` = (the token from step 1)
   - `GOOGLE_CALENDAR_ID` = `primary` (or your calendar ID)

No `GOOGLE_APPLICATION_CREDENTIALS` or secret file needed.

### Optional

- **VAPI_ASSISTANT_ID** – if you use “return assistant ID from server” (Option B in VAPI-ASSISTANT-SETUP.md).
- **SMTP_*** – for email sending (POST /email/send).

## 3. Deploy

Click **Deploy** (or push to the connected branch). After the build, the app will be at `https://<your-service>.onrender.com`.

## 4. Vapi

In the Vapi dashboard, set **Server URL** to:

`https://<your-service>.onrender.com/webhooks/vapi`

Use the same URL in the assistant if you configure the webhook there.

## 5. Notes

- **Free tier:** the service may spin down after inactivity; the first request after that can be slow.
- **Health:** `GET https://<your-service>.onrender.com/health`
- **Docs:** `https://<your-service>.onrender.com/docs`
