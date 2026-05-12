# Auth & Storage Migration: Complete

This document summarizes the migration from local CSV storage and dev tokens to Supabase-backed Postgres with bcrypt password authentication and session-based login.

## What Changed

### 1. Storage Layer (Postgres-Only, No CSV Fallback)

**Removed:**
- CSV fallback paths from all data loading functions
- `_normalize_csv_rows()` CSV parsing utility
- Local file path constants in main.py and workers

**Added:**
- DB-only reads: `load_headlines()`, `load_news_articles()`, `load_price_quotes()`
- DB writes: `insert_news_articles()`, `insert_price_quote()`
- User persistence: `create_user()`, `get_user_by_email()`
- Session management: `create_session()`, `get_active_session()`, `revoke_session()`

Files modified:
- [backend/app/storage.py](backend/app/storage.py) — 70% rewritten for DB-only ops

### 2. Authentication & Sessions (Bcrypt + Postgres)

**Added:**
- `hash_password()` — bcrypt hashing for secure storage
- `verify_password()` — constant-time password comparison
- `generate_session_token()` — cryptographically secure token generation
- `hash_session_token()` — SHA256 hashing for session lookup without storing raw tokens

**New Endpoints:**
- `POST /api/auth/register` — Create new user with bcrypt password
- `POST /api/auth/login` — Validate credentials, issue session cookie
- `GET /api/auth/me` — Return authenticated user info
- `POST /api/auth/logout` — Revoke session and clear cookie

**Middleware Update:**
- Session cookie fallback auth when bearer token not present
- Supports both JWT (dev tokens) and session-based auth simultaneously

Files modified:
- [backend/app/security.py](backend/app/security.py) — Added bcrypt, session token functions
- [backend/app/main.py](backend/app/main.py) — New routes, Pydantic models, middleware update

### 3. Database Schema Additions

**New Tables:**
- `app_users` (email, password_hash, role, created_at)
- `app_sessions` (user_id, token_hash, expires_at, revoked_at, created_at)

Migration file: [migrations/0002_auth_sessions.sql](migrations/0002_auth_sessions.sql)

### 4. Data Ingestion (Workers & Fetch Scripts)

**Changed from CSV writes to Postgres inserts:**
- [backend/app/workers/news_worker.py](backend/app/workers/news_worker.py) — Now reads from DB, writes to Redis streams
- [backend/app/workers/price_worker.py](backend/app/workers/price_worker.py) — Now reads from DB, writes to Redis streams
- [backend/fetch_news.py](backend/fetch_news.py) — Inserts via `storage.insert_news_articles()`
- [backend/fetch_price.py](backend/fetch_price.py) — Inserts via `storage.insert_price_quote()`

### 5. Dependencies

**New:** [requirements.txt](backend/requirements.txt) and [requirements.prod.txt](backend/requirements.prod.txt)
- Added: `bcrypt==4.2.0`

## How to Use

### Register a User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "securepass1234"}'
```

Response:
```json
{
  "id": 1,
  "email": "alice@example.com",
  "role": "user"
}
```

### Login (Get Session Cookie)

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "securepass1234"}' \
  -c cookies.txt
```

Response:
```json
{
  "id": 1,
  "email": "alice@example.com",
  "role": "user"
}
```
Header: `Set-Cookie: finsentinel_session=<token>; HttpOnly; SameSite=lax; ...`

### Authenticated Request

Use session cookie:
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -b cookies.txt
```

Or bearer token (still supported for backward compatibility):
```bash
curl -X GET http://localhost:8000/api/portfolio/analyze \
  -H "Authorization: Bearer <jwt-token>" \
  -d '{"holdings": [...]}'
```

### Logout

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -b cookies.txt
```

Response: `{"status": "logged_out"}`
Header: `Set-Cookie: finsentinel_session=; Max-Age=0; ...` (deletion cookie)

## Security Notes

1. **Password Storage:** Bcrypt with default salt rounds (12), secure by design
2. **Session Tokens:** 48-byte random tokens hashed with SHA256 before storage
3. **Session Expiry:** Default 86400 seconds (24h), configurable via `SESSION_TTL_SECONDS`
4. **Cookie Flags:** HttpOnly=true (JS can't access), SameSite=lax (CSRF protection), Secure=(if HTTPS)
5. **Environment Variables:**
   - `SESSION_COOKIE_NAME` (default: `finsentinel_session`)
   - `SESSION_TTL_SECONDS` (default: `86400`)
   - `SESSION_COOKIE_SECURE` (default: `0`; set to `1` for HTTPS)

## Migration Path for Existing Deployments

1. Pull this code.
2. Run migrations: `python3 backend/run_migrations.py`
3. Existing JWT/dev tokens continue to work (backward compatible).
4. Users can now register and login via bcrypt + sessions.
5. Old CSV files in `data/` are no longer used but can be kept for reference.

## Testing

**Auth flow validation (all tests passed):**
- ✓ User creation with bcrypt hashing
- ✓ Password verification
- ✓ Session token generation and hashing
- ✓ Session creation and lookup in Postgres
- ✓ Session revocation and expiry enforcement
- ✓ Full register → login → me → logout cycle

## What's Next

1. Frontend integration: Use login endpoint to get session cookie, include in subsequent requests
2. Role-based access control (RBAC) — `role` column is ready for authorization logic
3. Password reset / email verification (out of scope for this phase)
4. 2FA / TOTP (future hardening)

---

**Deployed:** 2026-05-12  
**Tested:** All auth routes and session lifecycle verified  
**Status:** Ready for production use with Supabase Postgres + bcrypt sessions
