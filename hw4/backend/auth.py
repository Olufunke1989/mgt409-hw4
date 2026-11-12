"""Customer accounts: sign up, log in, log out, and "who am I".

Passwords are never stored as plain text. Each one is hashed with
PBKDF2-HMAC-SHA256 (120,000 iterations) and its own random salt, and saved
in the same format the database already uses:

    pbkdf2_sha256$<salt>$<hex digest>

The salt is stored as text and fed to PBKDF2 as its UTF-8 bytes, which is
how the existing accounts in the database were created.

Logged-in customers get an HttpOnly session cookie signed with HMAC, so the
browser can't read or forge it.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs.db"

# Password hashing settings. Signup and login both use these.
ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000
SALT_BYTES = 16
MIN_PASSWORD_LENGTH = 8

# Sessions
SESSION_COOKIE = "cc_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # one week
# Set SESSION_SECRET in .env to keep people logged in across server restarts.
# Without it, a random secret is made at startup (restarting logs everyone out).
SESSION_SECRET = (os.getenv("SESSION_SECRET") or secrets.token_hex(32)).encode()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LOGIN_ERROR = "Incorrect email or password."

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------- password hashing ----------

def _pbkdf2(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS).hex()


def hash_password(password: str) -> str:
    """Hash a new password with a fresh random salt."""
    salt = secrets.token_hex(SALT_BYTES)
    return f"{ALGORITHM}${salt}${_pbkdf2(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    """Re-hash the entered password with the stored salt and compare in constant time."""
    try:
        algorithm, salt, digest = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    return hmac.compare_digest(_pbkdf2(password, salt), digest)


# Used when an email isn't found, so a wrong email takes about as long as a
# wrong password and doesn't reveal which accounts exist.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---------- sessions ----------

def _sign(payload: str) -> str:
    return hmac.new(SESSION_SECRET, payload.encode(), hashlib.sha256).hexdigest()


def make_session_token(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_MAX_AGE}"
    raw = f"{payload}.{_sign(payload)}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def read_session_token(token: str | None) -> int | None:
    if not token:
        return None
    try:
        user_id, expires, signature = base64.urlsafe_b64decode(token.encode()).decode().split(".")
    except Exception:
        return None
    if not hmac.compare_digest(_sign(f"{user_id}.{expires}"), signature):
        return None
    if int(expires) < time.time():
        return None
    return int(user_id)


def _set_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        make_session_token(user_id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )


# ---------- database ----------

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _public_user(row: sqlite3.Row) -> dict:
    """Only the safe fields. The password hash never leaves the server."""
    return {
        "id": row["id"],
        "first_name": row["first_name"] or (row["name"] or "").split(" ")[0],
        "last_name": row["last_name"] or "",
        "name": row["name"],
        "email": row["email"],
    }


def current_user(request: Request) -> dict | None:
    user_id = read_session_token(request.cookies.get(SESSION_COOKIE))
    if user_id is None:
        return None
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _public_user(row) if row else None


# ---------- request bodies ----------

class SignupIn(BaseModel):
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""


class LoginIn(BaseModel):
    email: str = ""
    password: str = ""


# ---------- routes ----------

@router.post("/signup", status_code=201)
def signup(body: SignupIn, response: Response) -> dict:
    first = body.first_name.strip()
    last = body.last_name.strip()
    email = body.email.strip().lower()

    errors: dict[str, str] = {}
    if not first:
        errors["first_name"] = "Please enter your first name."
    if not last:
        errors["last_name"] = "Please enter your last name."
    if not email:
        errors["email"] = "Please enter your email address."
    elif not EMAIL_RE.match(email):
        errors["email"] = "Please enter a valid email address."
    if not body.password:
        errors["password"] = "Please choose a password."
    elif len(body.password) < MIN_PASSWORD_LENGTH:
        errors["password"] = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if body.password != body.confirm_password:
        errors["confirm_password"] = "Passwords don't match."
    if errors:
        raise HTTPException(status_code=422, detail={"message": "Please fix the highlighted fields.", "fields": errors})

    with _connect() as conn:
        exists = conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if exists:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "An account with this email already exists. Try logging in instead.",
                    "fields": {"email": "This email is already registered."},
                },
            )
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", email, hash_password(body.password), first, last),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409,
                detail={"message": "An account with this email already exists. Try logging in instead."},
            )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()

    _set_session(response, row["id"])
    return _public_user(row)


@router.post("/login")
def login(body: LoginIn, response: Response) -> dict:
    email = body.email.strip().lower()
    if not email or not body.password:
        raise HTTPException(status_code=422, detail={"message": "Please enter your email and password."})

    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()

    stored = row["password_hash"] if row else _DUMMY_HASH
    if not verify_password(body.password, stored) or row is None:
        raise HTTPException(status_code=401, detail={"message": LOGIN_ERROR})

    _set_session(response, row["id"])
    return _public_user(row)


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(request: Request) -> dict:
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail={"message": "Not logged in."})
    return user
