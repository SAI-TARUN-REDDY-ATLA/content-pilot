"""YouTube OAuth: a one-time local sign-in that prints a refresh token, and CI credentials from it.

    content-pilot-auth path/to/client_secret.json

Store the three values it prints as GitHub secrets: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET,
YOUTUBE_REFRESH_TOKEN. Set the OAuth consent screen to "In production": in "Testing" Google
expires refresh tokens after 7 days and the nightly upload starts failing.
"""

import json
import os
import sys
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
TOKEN_URI = "https://oauth2.googleapis.com/token"
ENV = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")


def configured() -> bool:
    return all(os.getenv(k) for k in ENV)


def credentials():
    """Credentials built from the refresh token in the environment."""
    from google.oauth2.credentials import Credentials

    missing = [k for k in ENV if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing {', '.join(missing)}; run content-pilot-auth once to create them")
    return Credentials(None, refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"], token_uri=TOKEN_URI,
                       client_id=os.environ["YOUTUBE_CLIENT_ID"],
                       client_secret=os.environ["YOUTUBE_CLIENT_SECRET"], scopes=SCOPES)


def main() -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    if len(sys.argv) != 2:
        sys.exit("usage: content-pilot-auth path/to/client_secret.json")
    secrets = Path(sys.argv[1])
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    client = json.loads(secrets.read_text()).get("installed") or {}
    print("\nAdd these as GitHub repository secrets (Settings > Secrets and variables > Actions):\n")
    print(f"YOUTUBE_CLIENT_ID={client.get('client_id', creds.client_id)}")
    print(f"YOUTUBE_CLIENT_SECRET={client.get('client_secret', creds.client_secret)}")
    print(f"YOUTUBE_REFRESH_TOKEN={creds.refresh_token}")


if __name__ == "__main__":
    main()
