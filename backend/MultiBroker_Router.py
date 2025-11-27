"""
This module implements a simplified multi‑user router for a multi‑broker trading
application.  It provides user registration, login and per‑user client
management.  Client records are stored under `data/users/<username>/clients` in
separate sub‑directories for each broker.  The module also mirrors user and
client files to a GitHub repository (if configured) so that data is backed up.

Only the user‑management and client‑management portions of the full router are
included here.  Trading, order placement and other broker functions from the
original code base are intentionally omitted to keep this example focused on
demonstrating per‑user storage.  Those functions can be integrated later by
loading client credentials from the per‑user storage implemented here.

The file format for each client record follows **Option 1** from the user’s
request, which includes descriptive fields (broker, userid, display name,
capital, credentials and session status).  All GitHub writes happen
synchronously via the GitHub API – if the token is not set, writes are
silently skipped.
"""

import os
import json
import hashlib
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import requests
from fastapi import FastAPI, HTTPException, Body, Header, Depends
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# FastAPI application setup
# ---------------------------------------------------------------------------
# Create the FastAPI app before declaring any routes.  If this comes later the
# decorators will fail with `NameError: name 'app' is not defined`.
app = FastAPI(title="Multi‑User Multi‑Broker Router (Simplified)")

# Configure CORS so that the frontend (e.g. React/Next.js) can call our API.
# Adjust the allowed origins as appropriate for deployment.  Here we allow
# everything for demonstration purposes.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
# Base directory for all local data.  When deploying on Railway or another
# container, set DATA_DIR in the environment to preserve data across restarts.
BASE_DIR = os.path.abspath(os.environ.get("DATA_DIR", "./data"))
# Root under BASE_DIR where user data will be stored.  Each user gets their
# own subdirectory here containing user.json and clients/.
USERS_ROOT = os.path.join(BASE_DIR, "users")
os.makedirs(USERS_ROOT, exist_ok=True)

# GitHub configuration.  If GITHUB_TOKEN is not set then all GitHub writes
# become no‑ops.  The repo is expected to already exist.  Data is stored
# relative to the root of the repository (e.g. users/<username>/...).
GITHUB_REPO = os.environ.get("GITHUB_REPO", "wealthoceaninstitute-commits/Clients")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Password hashing salt and session TTL in minutes.  These values can be
# configured via environment variables if needed.  A salt ensures that two
# identical passwords hash to different values when the salt changes.
PASSWORD_SALT = os.environ.get("USER_PASSWORD_SALT", "woi_default_salt")
SESSION_TTL_MIN = int(os.environ.get("USER_SESSION_TTL", "720"))

# In‑memory session store.  Production deployments should use Redis or a
# database.  A dictionary is sufficient for this example.  Keys are session
# tokens and values hold the username and expiry time.
_sessions: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _safe(value: str) -> str:
    """Return a filesystem‑safe version of the given string."""
    return "".join(ch for ch in (value or "").strip() if ch.isalnum() or ch in ("-", "_")) or "x"


def _hash_password(password: str) -> str:
    """Hash the password using SHA‑256 and a salt."""
    return hashlib.sha256((password + PASSWORD_SALT).encode("utf-8")).hexdigest()


def _create_session(username: str) -> str:
    """Create a new session token for the given user and store it in memory."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=SESSION_TTL_MIN)
    _sessions[token] = {"username": username, "expires_at": expires_at}
    return token


def _resolve_token(x_auth_token: Optional[str]) -> str:
    """Validate a session token and return the associated username."""
    if not x_auth_token or x_auth_token not in _sessions:
        raise HTTPException(status_code=401, detail="Missing or invalid session token")
    sess = _sessions[x_auth_token]
    if datetime.utcnow() > sess["expires_at"]:
        _sessions.pop(x_auth_token, None)
        raise HTTPException(status_code=401, detail="Session expired")
    return sess["username"]


def get_current_user(x_auth_token: Optional[str] = Header(None)) -> str:
    """FastAPI dependency that returns the current logged‑in username."""
    return _resolve_token(x_auth_token)


def _user_dir(username: str) -> str:
    """Return the directory for the given user."""
    return os.path.join(USERS_ROOT, _safe(username))


def _user_json_path(username: str) -> str:
    return os.path.join(_user_dir(username), "user.json")


def _client_file_path(username: str, broker: str, client_id: str) -> str:
    broker = broker.lower()
    return os.path.join(_user_dir(username), "clients", broker, f"{_safe(client_id)}.json")


def _ensure_user_tree(username: str) -> None:
    """Create the folder structure for a new user locally."""
    root = _user_dir(username)
    os.makedirs(os.path.join(root, "clients", "dhan"), exist_ok=True)
    os.makedirs(os.path.join(root, "clients", "motilal"), exist_ok=True)


def _github_api_url(path: str) -> str:
    """Construct a GitHub API URL for a repo file or folder."""
    # Remove leading slashes and normalise path separators
    rel_path = path.lstrip("/").replace(os.sep, "/")
    return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{rel_path}"


def _github_headers() -> Dict[str, str]:
    """Return headers for GitHub API requests."""
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def _github_write(rel_path: str, content: str, message: str) -> None:
    """Create or update a file in the GitHub repository."""
    if not GITHUB_TOKEN:
        return
    url = _github_api_url(rel_path)
    # Determine if the file currently exists to supply a SHA for update
    sha = None
    try:
        r = requests.get(f"{url}?ref={GITHUB_BRANCH}", headers=_github_headers(), timeout=10)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except Exception:
        pass
    # Base64 encode the content as required by GitHub API
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    data: Dict[str, Any] = {
        "message": message,
        "content": content_b64,
        "branch": GITHUB_BRANCH,
    }
    if sha:
        data["sha"] = sha
    try:
        requests.put(url, headers=_github_headers(), json=data, timeout=15)
    except Exception:
        pass


def _github_delete(rel_path: str, message: str) -> None:
    """Delete a file from the GitHub repository."""
    if not GITHUB_TOKEN:
        return
    url = _github_api_url(rel_path)
    sha = None
    try:
        r = requests.get(f"{url}?ref={GITHUB_BRANCH}", headers=_github_headers(), timeout=10)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except Exception:
        pass
    if not sha:
        return
    payload = {
        "message": message,
        "sha": sha,
        "branch": GITHUB_BRANCH,
    }
    try:
        requests.delete(url, headers=_github_headers(), json=payload, timeout=15)
    except Exception:
        pass


def _sync_user_to_github(username: str) -> None:
    """Sync the local user.json to GitHub."""
    local_path = _user_json_path(username)
    if not os.path.exists(local_path):
        return
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()
    rel_path = f"users/{_safe(username)}/user.json"
    _github_write(rel_path, content, f"Create or update user {username}")


def _sync_client_to_github(username: str, broker: str, client_id: str, data: Dict[str, Any]) -> None:
    """Sync a single client JSON to GitHub."""
    rel_path = f"users/{_safe(username)}/clients/{broker}/{_safe(client_id)}.json"
    _github_write(rel_path, json.dumps(data, indent=2), f"Add or update client {client_id} for {username}")


def _sync_client_delete_from_github(username: str, broker: str, client_id: str) -> None:
    """Delete a client JSON from GitHub."""
    rel_path = f"users/{_safe(username)}/clients/{broker}/{_safe(client_id)}.json"
    _github_delete(rel_path, f"Delete client {client_id} for {username}")


def _load_user(username: str) -> Optional[Dict[str, Any]]:
    """Load the user.json document for the given user."""
    path = _user_json_path(username)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# API routes for user management
# ---------------------------------------------------------------------------

@app.post("/users/register")
def register_user(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Register a new user and return a session token."""
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    email = (payload.get("email") or "").strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    # Ensure user does not already exist
    if _load_user(username):
        raise HTTPException(status_code=400, detail="User already exists")
    # Create folder structure
    _ensure_user_tree(username)
    # Create user document
    user_doc = {
        "username": username,
        "email": email,
        "password_hash": _hash_password(password),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    # Save locally
    with open(_user_json_path(username), "w", encoding="utf-8") as f:
        json.dump(user_doc, f, indent=2)
    # Sync to GitHub
    _sync_user_to_github(username)
    # Create session token and return
    token = _create_session(username)
    return {"success": True, "username": username, "token": token}


@app.post("/users/login")
def login_user(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Authenticate a user and return a session token."""
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    user_doc = _load_user(username)
    if not user_doc:
        raise HTTPException(status_code=400, detail="User not found")
    if user_doc.get("password_hash") != _hash_password(password):
        raise HTTPException(status_code=400, detail="Invalid password")
    token = _create_session(username)
    return {"success": True, "username": username, "token": token}


@app.get("/users/me")
def get_me(current_user: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Return the current authenticated user."""
    return {"username": current_user}


# ---------------------------------------------------------------------------
# API routes for client management
# ---------------------------------------------------------------------------

@app.post("/clients/add")
def add_client(payload: Dict[str, Any] = Body(...), current_user: str = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Add a new client for the current user.  The payload should include:
      - broker: "dhan" or "motilal"
      - client_id: client login/identifier
      - name/display_name: human friendly name
      - capital: numeric or string value
      - creds: dictionary with broker‑specific credentials (e.g. API keys)
      - session_active: boolean (optional)

    Returns the saved client record.
    """
    broker = (payload.get("broker") or "").lower()
    if broker not in {"dhan", "motilal"}:
        raise HTTPException(status_code=400, detail="Broker must be 'dhan' or 'motilal'")
    client_id = (payload.get("client_id") or payload.get("userid") or "").strip()
    if not client_id:
        raise HTTPException(status_code=400, detail="client_id is required")
    name = (payload.get("name") or payload.get("display_name") or client_id).strip()
    capital = payload.get("capital", "")
    creds = payload.get("creds", {})
    session_active = bool(payload.get("session_active", False))
    # Construct client document according to Option 1 format
    doc: Dict[str, Any] = {
        "broker": broker,
        "userid": client_id,
        "display_name": name,
        "capital": capital,
        "creds": creds,
        "session_active": session_active,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    # Determine file path and save locally
    path = _client_file_path(current_user, broker, client_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    # Sync to GitHub
    _sync_client_to_github(current_user, broker, client_id, doc)
    return {"success": True, "client": doc}


@app.get("/clients/list")
def list_clients(current_user: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Return all clients for the current user grouped by broker."""
    result: Dict[str, Any] = {"dhan": [], "motilal": []}
    for broker in ["dhan", "motilal"]:
        broker_dir = os.path.join(_user_dir(current_user), "clients", broker)
        if not os.path.isdir(broker_dir):
            continue
        for fname in os.listdir(broker_dir):
            if fname.lower().endswith(".json"):
                try:
                    with open(os.path.join(broker_dir, fname), "r", encoding="utf-8") as f:
                        record = json.load(f)
                    result[broker].append(record)
                except Exception:
                    pass
    return result


@app.get("/clients/get/{broker}/{client_id}")
def get_client(broker: str, client_id: str, current_user: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Retrieve a single client record."""
    broker = broker.lower()
    if broker not in {"dhan", "motilal"}:
        raise HTTPException(status_code=400, detail="Invalid broker")
    path = _client_file_path(current_user, broker, client_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Client not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.delete("/clients/delete/{broker}/{client_id}")
def delete_client(broker: str, client_id: str, current_user: str = Depends(get_current_user)) -> Dict[str, Any]:
    """Delete a client record for the current user."""
    broker = broker.lower()
    path = _client_file_path(current_user, broker, client_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Client not found")
    # Delete locally
    os.remove(path)
    # Delete from GitHub
    _sync_client_delete_from_github(current_user, broker, client_id)
    return {"success": True, "deleted": client_id}


# ---------------------------------------------------------------------------
# Placeholder for trading functions
# ---------------------------------------------------------------------------
# The original code includes complex logic for placing orders, editing clients,
# computing positions and holdings, and dispatching to multiple brokers.  To
# integrate those features with per‑user storage, modify each function to
# resolve the current user via `get_current_user` and load the client record
# using `_client_file_path(current_user, broker, client_id)`.  Then pass the
# credentials from the loaded JSON into the appropriate broker API calls.
