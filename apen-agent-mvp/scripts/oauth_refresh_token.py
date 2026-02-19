#!/usr/bin/env python3
"""
One-time script to obtain a Google OAuth2 refresh token for Calendar API.
Use this when your organization blocks service account key creation.

Prerequisites:
1. In Google Cloud Console: APIs & Services → Credentials → Create credentials → OAuth client ID.
2. Application type: "Web application" (important: not Desktop app).
3. Under "Authorized redirect URIs" add:  http://localhost:8765/
4. Copy Client ID and Client secret, set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.

Run from apen-agent-mvp/:
  python scripts/oauth_refresh_token.py

A browser will open; sign in with the Google account that owns the calendar.
Then add the printed refresh token to .env as GOOGLE_REFRESH_TOKEN.
"""
import os
import sys
from pathlib import Path

# Load .env from project root (apen-agent-mvp)
ROOT = Path(__file__).resolve().parent.parent
_env = ROOT / ".env"
if _env.exists():
    from dotenv import load_dotenv
    load_dotenv(_env)

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
# Use 8766 (8765 often in use). Add this exact URI to OAuth client: http://localhost:8766/
REDIRECT_URI = "http://localhost:8766/"

def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install: pip install google-auth-oauthlib")
        sys.exit(1)

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        print("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env (from OAuth 2.0 Client ID in Google Cloud Console).")
        print("Create OAuth client: Web application, add redirect URI:", REDIRECT_URI)
        sys.exit(1)

    # Use "web" client config so redirect_uri is respected (must match Google Cloud Console)
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES, redirect_uri=REDIRECT_URI)
    print("If you get 'redirect_uri_mismatch': Add", REDIRECT_URI, "to your OAuth client's Authorized redirect URIs (Web application).")
    # prompt='consent' forces the consent screen so we always get a refresh token
    creds = flow.run_local_server(port=8766, prompt="consent")

    if creds and creds.refresh_token:
        print("\nAdd this to your .env (or set in your environment):\n")
        print("GOOGLE_REFRESH_TOKEN=" + creds.refresh_token)
        print("\nAlso set GOOGLE_CALENDAR_ID=primary (or your calendar ID).")
    else:
        print("No refresh token in response. Try again and ensure redirect URI", REDIRECT_URI, "is in your OAuth client.")

if __name__ == "__main__":
    main()
