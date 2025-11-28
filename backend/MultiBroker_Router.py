import os, json, base64, hashlib, uuid, logging
from datetime import datetime
from typing import Dict

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ================= CONFIG =================

APP_TITLE = "Wealth Ocean Multi User"
APP_VERSION = "1.0"

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# ================== CORS ==================

DEFAULT_FRONTEND = "https://multibrokertradermultiuser-production-f735.up.railway.app"

allowed_env = os.getenv("ALLOWED_ORIGINS", "").strip()
if allowed_env:
    ORIGINS = [o.strip().rstrip("/") for o in allowed_env.split(",")]
else:
    ORIGINS = [DEFAULT_FRONTEND]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ STORAGE ======================

DATA_DIR = os.path.abspath(
    os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
)

USERS_FILE = os.path.join(DATA_DIR, "users.json")


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def save_json(path: str, data):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =========== GITHUB SYNC ==================

GITHUB_REPO = os.getenv("GITHUB_REPO", "wealthoceaninstitute-commits/Clients")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

ENABLE_GITHUB = bool(GITHUB_TOKEN)


def gh_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def gh_url(path):
    return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"


def github_read_json(path, default):
    if not ENABLE_GITHUB:
        return default

    r = requests.get(gh_url(path), headers=gh_headers())
    if r.status_code != 200:
        return default

    content = r.json().get("content", "")
    decoded = base64.b64decode(content).decode()
    return json.loads(decoded)


def github_write_file(path, content, message):
    if not ENABLE_GITHUB:
        return

    url = gh_url(path)
    sha = None

    r = requests.get(url, headers=gh_headers())
    if r.status_code == 200:
        sha = r.json().get("sha")

    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": GITHUB_BRANCH,
    }

    if sha:
        payload["sha"] = sha

    requests.put(url, headers=gh_headers(), json=payload)


# ================= AUTH STORE =============

ACTIVE_TOKENS: Dict[str, str] = {}


def _hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _verify_password(raw: str, hashed: str) -> bool:
    return _hash_password(raw) == hashed


def _load_users():
    if ENABLE_GITHUB:
        return github_read_json("users/users.json", {})
    return load_json(USERS_FILE, {})


def _save_users(data):
    if ENABLE_GITHUB:
        github_write_file(
            "users/users.json",
            json.dumps(data, indent=2),
            "Update users DB",
        )
    save_json(USERS_FILE, data)


# ================= MODELS ==================

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=3)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=4)


class UserLoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    username: str
    token: str


# ================= ROUTES ==================

@app.get("/")
def home():
    return {"status": "OK - Multi User Backend Working"}


@app.post("/users/register", response_model=AuthResponse)
def register(req: UserRegisterRequest):

    users = _load_users()
    email = req.email.strip().lower()

    if email in users:
        raise HTTPException(status_code=400, detail="Email already exists")

    users[email] = {
        "name": req.name,
        "email": email,
        "password_hash": _hash_password(req.password),
        "created_at": now(),
    }

    _save_users(users)

    # Create user folders
    user_dir = os.path.join(DATA_DIR, "users", email)
    ensure_dir(user_dir)
    ensure_dir(os.path.join(user_dir, "clients"))

    # Save user file to GitHub
    github_write_file(
        f"users/{email}/user.json",
        json.dumps({
            "name": req.name,
            "email": email,
            "created_at": users[email]["created_at"]
        }, indent=2),
        f"Create user {email}"
    )

    token = uuid.uuid4().hex
    ACTIVE_TOKENS[token] = email

    logger.info(f"✅ USER REGISTERED: {email}")
    return {"success": True, "username": email, "token": token}


@app.post("/users/login", response_model=AuthResponse)
def login(req: UserLoginRequest):

    users = _load_users()
    email = req.email.strip().lower()

    if email not in users:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not _verify_password(req.password, users[email]["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = uuid.uuid4().hex
    ACTIVE_TOKENS[token] = email

    logger.info(f"✅ LOGIN SUCCESS: {email}")
    return {"success": True, "username": email, "token": token}


# ================= LOCAL RUN =============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("MultiBroker_Router:app", host="0.0.0.0", port=8000, reload=True)
