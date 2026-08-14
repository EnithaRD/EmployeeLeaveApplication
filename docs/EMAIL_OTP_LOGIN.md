# Email OTP Login

**Implementation memo** &middot; Employee Leave Application &middot; backend
Sender account: `varshajk271@gmail.com` &middot; Date: 14 Aug 2026 &middot; New dependencies: none

How password login gained a one-time-code companion sent through a personal Gmail account — the abstraction it's built on, the files it touched, and what's still worth doing next.

## Contents

1. [Why & scope](#1-why--scope)
2. [Architecture](#2-architecture)
3. [Request → verify flow](#3-request--verify-flow)
4. [File manifest](#4-file-manifest)
5. [Security notes](#5-security-notes)
6. [Configuration](#6-configuration)
7. [Testing](#7-testing)
8. [Try it against a running server](#8-try-it-against-a-running-server)
9. [Open items](#9-open-items)

## 1. Why & scope

The app only had one way in: an email + password form checked against the `users` table. The ask was to add a second path — request a one-time code by email, then log in with that code instead of a password — sent through a personal Gmail account, without disturbing the existing login.

Two things shaped every decision below. First, **nothing about password login changed** — `POST /auth/login`, `/auth/me`, and `require_role` are untouched; the OTP path is additive. Second, the request asked for the email-sending piece to follow SOLID principles specifically so that *more accounts or providers can be added later* — that requirement is what shaped the architecture in the next section.

## 2. Architecture

Nothing in the OTP flow talks to Gmail directly. Routes and services depend on an `EmailSender` interface; only one small factory function knows that today's implementation happens to be SMTP over a Gmail App Password.

| Layer | Piece | Responsibility |
|---|---|---|
| Interface | `EmailSender` (ABC) | One method, `send(to, subject, body)`. The only thing callers know about. |
| Implementation | `SmtpEmailSender` | Sends via `smtplib` + `email.mime` (stdlib only). Takes host/port/credentials as constructor args — no hidden globals. |
| Wiring | `get_email_sender()` | FastAPI dependency that reads settings and builds the sender. The one place that would change to add a second account or swap providers. |
| Consumer | `otp_service` | Generates, hashes, stores, and emails codes — receives an `EmailSender` as a parameter, never constructs one. |

**Why this earns its keep later:** adding a second send-from address, or swapping Gmail for another provider, means writing one new class that implements `EmailSender` and pointing `get_email_sender()` at it. The route, the OTP service, and every test that uses a fake sender stay exactly as they are — that's the Dependency Inversion / Open-Closed payoff the request asked for.

## 3. Request → verify flow

Two endpoints, both under `/api/v1/auth`, alongside the existing `/login`:

```
Client            otp_service                 Gmail SMTP        Client              JWT issued
(enters email) →  (generate + hash + store) →  (delivers code) → (submits code)  →  (same as password login)
```

### `POST /auth/otp/request`

1. Look up the user by email. If they don't exist, or exist but are inactive, do nothing — the endpoint still replies `202` either way, so it can't be used to fingerprint which emails have accounts.
2. Generate a random 6-digit code with `secrets.randbelow` (cryptographically strong, not `random`).
3. Hash it with a per-code random salt and store the salt+hash pair, plus a 5-minute expiry, as a new `otp_codes` row.
4. Email the plaintext code through the injected `EmailSender`. The database never holds a readable code.

### `POST /auth/otp/verify`

1. Find that user's most recent unconsumed code.
2. Reject if it's missing, expired, or has already failed `OTP_MAX_ATTEMPTS` times.
3. Compare the submitted code against the stored hash using a constant-time comparison; every attempt (right or wrong) increments the attempt counter.
4. On a match, mark the code consumed and issue the same JWT `create_access_token` that password login produces — downstream auth (`get_current_user`, `require_role`) can't tell which door the user came through.

## 4. File manifest

Nine files touched in total — five new, four edited. Nothing outside `backend/`.

| File | | What it does |
|---|---|---|
| `app/core/email/base.py` | **new** | The `EmailSender` abstract base class. |
| `app/core/email/smtp_sender.py` | **new** | `SmtpEmailSender` — the Gmail-compatible SMTP implementation. |
| `app/core/email/dependency.py` | **new** | `get_email_sender()`, the FastAPI dependency that builds a sender from settings. |
| `app/models/otp_code.py` | **new** | `OtpCode` table: hashed code, expiry, consumed-at, attempt count. |
| `app/services/otp_service.py` | **new** | `request_otp()` / `verify_otp()` — the actual logic, independent of FastAPI. |
| `app/core/config.py` | edited | Added `SMTP_*` and `OTP_*` settings, all with safe defaults. |
| `app/schemas/auth.py` | edited | Added `OtpRequest` / `OtpVerify` request bodies. |
| `app/api/v1/endpoints/auth.py` | edited | Added the two OTP routes; every existing route untouched. |
| `app/main.py` | edited | One import line so `OtpCode` is registered with `Base.metadata.create_all`. |
| `backend/.env` | edited | SMTP host/port/credentials and OTP timing — gitignored, never committed. |

## 5. Security notes

### Hashing the code — and why it isn't bcrypt

The obvious choice was the same `passlib` + `bcrypt` pairing already in `requirements.txt`. It turned out to be broken in this environment: `passlib 1.7.4`'s bcrypt backend self-test throws `ValueError` against `bcrypt 5.0.0`, a known incompatibility from bcrypt dropping silent 72-byte truncation. Upgrading either pinned version was out of scope for this change, so codes are hashed with stdlib `hashlib.pbkdf2_hmac` (SHA-256, 260,000 iterations, random 16-byte salt per code) and compared with `hmac.compare_digest` instead — no dependency changes, no timing side-channel.

### Everything else, briefly

- **No user enumeration.** Requesting an OTP for an email that doesn't exist (or belongs to an inactive account) returns the same `202` as a real one — it just sends nothing.
- **Codes expire and get consumed.** `OTP_EXPIRE_MINUTES` (default 5) bounds the window; a successful verify sets `consumed_at`, so replaying the same code a second time fails.
- **Attempts are capped.** `OTP_MAX_ATTEMPTS` (default 5) stops brute-forcing a 6-digit code against one outstanding OTP.
- **The Gmail App Password lives only in `backend/.env`**, which was already listed in `.gitignore` before this change — confirmed it stays untracked, not just ignored by convention.

## 6. Configuration

All new settings live in `Settings` (`app/core/config.py`) and are read from `backend/.env`:

| Key | Default | Note |
|---|---|---|
| `SMTP_HOST` | `smtp.gmail.com` | Gmail's SMTP endpoint. |
| `SMTP_PORT` | `587` | STARTTLS port. |
| `SMTP_USERNAME` | `varshajk271@gmail.com` | The sending account. |
| `SMTP_PASSWORD` | — | Gmail App Password. Set locally, not shown here. |
| `SMTP_FROM_EMAIL` | `= SMTP_USERNAME` | Optional override for the From header. |
| `OTP_EXPIRE_MINUTES` | `5` | Code lifetime. |
| `OTP_MAX_ATTEMPTS` | `5` | Wrong guesses allowed per code. |

All five SMTP fields are optional at the settings level — the app still boots with none of them set. `get_email_sender()` only raises (a clear `RuntimeError`) if an OTP is actually requested without credentials configured.

## 7. Testing

- **20/20** tests passing
- **7** new OTP tests
- **6** pre-existing tests repaired
- **0** real emails sent in CI

`tests/test_otp_login.py` covers the request/verify flow end to end — known user, unknown user, inactive user, correct code, wrong code, replaying a consumed code, and verifying with no request on record — using a `FakeEmailSender` test double swapped in through `app.dependency_overrides`, so the suite never touches Gmail or the network:

```python
# captures sent messages instead of hitting SMTP
class FakeEmailSender(EmailSender):
    def __init__(self):
        self.sent = []

    def send(self, to, subject, body):
        self.sent.append({"to": to, "subject": subject, "body": body})
```

### Two unrelated test files were also broken

A prior merge had changed the `Employee`/`User` models and the login route's request shape without updating the tests. Since this pass touched the login area anyway, those were fixed too: `test_root_endpoint`'s expected message, the login tests' switch from JSON to OAuth2 form data plus a seeded `User` row, and three `leave_balance_service` tests updated to construct an `Employee` through its current `user_id` foreign key instead of a removed `email` field.

```bash
# run it, from backend/, PowerShell or Git Bash
venv/Scripts/python -m pytest -v
```

## 8. Try it against a running server

The test suite deliberately never calls real SMTP. To confirm the Gmail App Password actually works, start the app and call the two endpoints directly — the second command needs the 6-digit code from the email that arrives:

```bash
# request a code
curl -X POST http://localhost:8000/api/v1/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"email": "employee@example.com"}'
```

```bash
# verify it
curl -X POST http://localhost:8000/api/v1/auth/otp/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "employee@example.com", "code": "482913"}'
```

## 9. Open items

- **Live send unverified.** The App Password is wired in, but no real email has been sent through it yet in this session — worth the curl check above before calling this done.
- **Frontend has no OTP screen.** Only the backend endpoints exist; the login UI still only posts to `/auth/login`.
- **No per-email request throttling.** `OTP_MAX_ATTEMPTS` limits guesses against one code, but nothing yet stops someone from requesting a fresh code every few seconds.
- **`@app.on_event` is deprecated.** Pre-existing FastAPI warning, unrelated to this change — noted, not fixed.

---

*Employee Leave Application &middot; backend/app &middot; written after implementing and testing the change described above.*
