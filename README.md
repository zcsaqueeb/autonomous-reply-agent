A **multi-account Telegram auto-responder** built for `$VELO` quiz and announcement events.  
It detects eligible announcements, generates a **single Gemini-powered reply**, and deploys it across multiple Telegram **user accounts** with controlled timing, emojis, and optional fake `@username` mentions when required.

This is automation with guardrails — not blind spam.

## What This Bot Does

- Monitors specific Telegram groups for **new, original `$VELO` announcements**
- Generates **one concise Gemini response per announcement**
  - Correct quiz answers
  - Hashtags (when required)
  - Emojis (natural, non-excessive)
  - Optional fake `@name` mentions for “tag friends” tasks
- Reuses the same generated reply across all accounts
- Supports **single-entry** and **multi-entry** events automatically
- Schedules replies intelligently to avoid clustering

---

## Core Features

### Message Qualification
- Processes **only**:
  - New messages
  - Non-forwarded
  - Non-edited
  - Non-replies
- Ignores general chat noise completely

### Gemini Response Rules
- Exactly **one AI call per announcement**
- Cached by message ID
- Output constraints:
  - One short sentence
  - No explanations
  - No `$VELO`
  - Emojis allowed
  - Fake mentions added *only* if explicitly requested

### Multi-Account Execution
- Uses **Telegram user accounts** (not bots)
- Telethon sessions stored locally
- Sequential client startup to avoid SQLite corruption
- Optional per-account 2FA support

---

## Entry Modes

### Multi-Entry Mode
Triggered when the announcement contains phrases such as:
- `unlimited entries`
- `multiple entries`
- `multiple submissions`
- `no entry limit`

Behavior:
- Accounts loop replies indefinitely
- Delay between replies controlled by `MULTI_REPLY_DELAY`

### Single-Entry Mode
Default behavior when multi-entry keywords are absent.

Behavior:
- Event end date parsed from text (e.g. `Jan 5–10, 2026`)
- Replies distributed across accounts between now and event end
- If no date is detected:
  - Only `user0` replies immediately

---

## Installation

```bash
git clone https://github.com/zcsaqueeb/telegram-gemini-quiz-bot.git
cd telegram-gemini-quiz-bot

pip install -r requirements.txt
````

**Strongly recommended**:

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Configuration

All settings are defined in **`config.py`**.

### Required

```python
API_ID = 123456
API_HASH = "your_api_hash"

GEMINI_API_KEY = "your_gemini_api_key"

TARGET_GROUPS = [
    "@yourgroup",
]

ACCOUNT_COUNT = 2
MULTI_REPLY_DELAY = 3
```

### Optional

```python
TWO_FA_PASSWORDS = {
    0: "password_for_user0",
    1: "password_for_user1",
}
```

**Notes**

* `TARGET_GROUPS` accepts usernames or invite links
* Sessions are created as:

  ```
  sessions/user0.session
  sessions/user1.session
  ```

> **Do not commit real credentials.**
> Replace all secrets before pushing to GitHub.

---

## Runtime Flow

1. Startup

   * SSL fixes applied (if needed)
   * Gemini initialized
   * `sessions/` directory created
   * Telegram clients started sequentially

2. Group Resolution

   * Target groups resolved by username or link
   * Message handlers attached

3. Message Handling

   * `$VELO` detected → continue
   * Gemini called once → response cached
   * Entry mode selected
   * Replies scheduled or looped accordingly

---

## Running the Bot

```bash
python main.py
```

### First Run

* Each account (`user0`, `user1`, …) requires login via code or QR
* Session files persist for future runs

### Stop

* `Ctrl + C`

---

## Tech Stack

* Python 3.10+
* Telethon
* Google Gemini (`google-generativeai`)
* asyncio-based scheduling
* Regex + datetime parsing

---

## Operational Notes

* Designed specifically for `$VELO`-style quiz events
* Assumes repetitive, structured announcement formats
* Aggressive misuse will get accounts restricted or banned

You are responsible for:

* Telegram Terms of Service
* Group rules
* Account safety

Operate with intent.
