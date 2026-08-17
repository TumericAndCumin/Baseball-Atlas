"""
Password-protected host for the Baseball Feature Atlas.

Serves the self-contained HTML report behind HTTP Basic Auth. Credentials come from
the environment (ATLAS_USER / ATLAS_PASS) and are never committed to this repo.
"""
import gzip
import hmac
import os
from functools import wraps
from pathlib import Path

from flask import Flask, Response, request

APP_DIR = Path(__file__).resolve().parent
REPORT = APP_DIR / "static" / "index.html"

USER = os.environ.get("ATLAS_USER", "")
PASS = os.environ.get("ATLAS_PASS", "")
if not USER or not PASS:
    raise RuntimeError(
        "ATLAS_USER and ATLAS_PASS must be set as environment variables. "
        "Locally:  ATLAS_USER=... ATLAS_PASS=... python app.py"
    )

app = Flask(__name__)

# Read and pre-compress once at boot. The report is a few MB of inline SVG and never
# changes at runtime — a new report means a new deploy.
_html = REPORT.read_bytes() if REPORT.exists() else b"<h1>No report deployed yet.</h1>"
_gz = gzip.compress(_html, 6)


def _credentials_ok(auth) -> bool:
    """Constant-time check. Both comparisons always run, so timing leaks nothing."""
    if not auth:
        return False
    user_ok = hmac.compare_digest(auth.username or "", USER)
    pass_ok = hmac.compare_digest(auth.password or "", PASS)
    return user_ok and pass_ok


def protected(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not _credentials_ok(request.authorization):
            return Response(
                "Authentication required.", 401,
                {"WWW-Authenticate": 'Basic realm="Baseball Feature Atlas", charset="UTF-8"'},
            )
        return view(*args, **kwargs)
    return wrapper


@app.get("/healthz")
def healthz():
    """Unauthenticated so Railway's healthcheck can reach it. Discloses nothing."""
    return {"ok": True, "bytes": len(_html)}


@app.get("/")
@protected
def index():
    gzip_ok = "gzip" in request.headers.get("Accept-Encoding", "")
    headers = {
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-cache",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
    }
    if gzip_ok:
        headers["Content-Encoding"] = "gzip"
        headers["Vary"] = "Accept-Encoding"
    return Response(_gz if gzip_ok else _html, 200, headers)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
