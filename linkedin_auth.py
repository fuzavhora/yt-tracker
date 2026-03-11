"""
linkedin_auth.py — LinkedIn OAuth 2.0 Token Helper

One-time local setup script to generate a LinkedIn access token.
Run: python linkedin_auth.py --setup

The generated token is valid for 60 days. Store it as a GitHub Secret
named LINKEDIN_ACCESS_TOKEN and re-run this script every ~55 days.
"""

from __future__ import annotations

import http.server
import os
import sys
import urllib.parse
import webbrowser
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "openid profile w_member_social"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"


def get_authorization_url(client_id: str) -> str:
    """Build the LinkedIn OAuth authorization URL."""
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": "linkedin_jobs_auth",
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(client_id: str, client_secret: str, code: str) -> dict:
    """Exchange the authorization code for an access token."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def validate_token(access_token: str) -> dict | None:
    """Check if an access token is still valid by calling /v2/userinfo."""
    resp = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json()
    return None


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP handler to capture the OAuth callback."""

    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authorization successful!</h1>"
                b"<p>You can close this tab and go back to the terminal.</p>"
                b"</body></html>"
            )
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<html><body><h1>Error: {error}</h1></body></html>".encode()
            )

    def log_message(self, format, *args):
        pass  # Suppress server logs


def run_setup():
    """Interactive setup flow to generate a LinkedIn access token."""
    client_id = os.environ.get("LINKEDIN_CLIENT_ID")
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("\n" + "=" * 60)
        print("LinkedIn OAuth Setup")
        print("=" * 60)
        print("\nYou need to provide your LinkedIn App credentials.")
        print("Get them from: https://developer.linkedin.com/")
        print()
        client_id = input("Enter your LinkedIn Client ID: ").strip()
        client_secret = input("Enter your LinkedIn Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Error: Client ID and Secret are required.")
        sys.exit(1)

    # Generate authorization URL
    auth_url = get_authorization_url(client_id)

    print("\n" + "=" * 60)
    print("Step 1: Open this URL in your browser and authorize the app:")
    print("=" * 60)
    print(f"\n{auth_url}\n")

    # Try to open browser automatically
    try:
        webbrowser.open(auth_url)
        print("(Browser opened automatically)")
    except Exception:
        print("(Please copy and paste the URL above into your browser)")

    # Start local server to capture callback
    print("\nStep 2: Waiting for authorization callback on localhost:8080...")
    server = http.server.HTTPServer(("localhost", 8080), OAuthCallbackHandler)
    server.handle_request()  # Handle single request

    if not OAuthCallbackHandler.auth_code:
        print("Error: No authorization code received.")
        sys.exit(1)

    # Exchange code for token
    print("\nStep 3: Exchanging code for access token...")
    try:
        token_data = exchange_code_for_token(
            client_id, client_secret, OAuthCallbackHandler.auth_code
        )
    except requests.RequestException as e:
        print(f"Error exchanging code: {e}")
        sys.exit(1)

    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 0)
    expires_days = expires_in // 86400

    # Validate token
    user_info = validate_token(access_token)

    print("\n" + "=" * 60)
    print("SUCCESS! Your LinkedIn access token:")
    print("=" * 60)
    print(f"\n{access_token}\n")
    print(f"Expires in: {expires_days} days")

    if user_info:
        name = user_info.get("name", "Unknown")
        print(f"Authenticated as: {name}")

    print("\n" + "-" * 60)
    print("Next steps:")
    print("-" * 60)
    print("1. Add this to your .env file:")
    print(f"   LINKEDIN_ACCESS_TOKEN={access_token}")
    print()
    print("2. Add it as a GitHub Secret named LINKEDIN_ACCESS_TOKEN")
    print()
    print(f"3. Set a reminder to re-run this in {expires_days - 5} days")
    print("   (token expires every 60 days)")
    print("=" * 60)


if __name__ == "__main__":
    if "--setup" in sys.argv or len(sys.argv) == 1:
        run_setup()
    elif "--validate" in sys.argv:
        token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
        if not token:
            print("Error: LINKEDIN_ACCESS_TOKEN not set in .env")
            sys.exit(1)
        info = validate_token(token)
        if info:
            print(f"Token is valid. User: {info.get('name', 'Unknown')}")
        else:
            print("Token is INVALID or EXPIRED. Re-run: python linkedin_auth.py --setup")
            sys.exit(1)
