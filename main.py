# ================= SSL FIX =================
import os, certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

# ================= IMPORTS =================
import sys
import asyncio
import time
import re
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat
import google.generativeai as genai

from config import *

# ================= LOGGING =================
def log(section, message, level="INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level:<5}] [{section:<8}] {message}")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

os.makedirs("sessions", exist_ok=True)

# ================= GEMINI (AUTO MODEL, ONE CALL) =================
genai.configure(api_key=GEMINI_API_KEY)

def get_model():
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            log("AI", f"Using model {m.name}")
            return genai.GenerativeModel(m.name)
    raise RuntimeError("No Gemini model supports generateContent")

MODEL = get_model()

AI_CACHE = {}  # message_id -> final reply (ONE CALL ONLY)

async def ai_reply_once(msg_id: int, text: str):
    if msg_id in AI_CACHE:
        log("AI", "CACHE HIT → reuse reply")
        return AI_CACHE[msg_id]

    prompt = f"""
You analyze a Telegram announcement and produce ONE final reply.

Rules:
- If quiz/question → answer correctly.
- If hashtag required → include exactly one existing hashtag.
- One short sentence.
- No mentions.
- No emojis.
- No explanations.
- Do NOT include $VELO.

Announcement:
{text}

Final Reply:
""".strip()

    log("AI", "CALL Gemini (first & only time)")
    r = MODEL.generate_content(prompt)

    if not r or not r.text:
        log("AI", "Empty response", "ERROR")
        return None

    reply = r.text.strip()
    AI_CACHE[msg_id] = reply
    log("AI", "Reply cached")
    return reply

# ================= PATTERNS =================
VELO_PATTERN = re.compile(r"\$velo\b", re.IGNORECASE)
MULTI_ENTRY_PATTERN = re.compile(
    r"(unlimited entries|multiple entries|multiple submissions|no entry limit)",
    re.IGNORECASE
)

# ================= EVENT END PARSER (UTC) =================
MONTHS = {
    "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
    "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12
}

DATE_RANGE = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}.*?-\s*\d{1,2}.*?,\s*\d{4}",
    re.IGNORECASE
)

def parse_event_end(text):
    m = DATE_RANGE.search(text)
    if not m:
        return None
    raw = m.group(0)
    parts = re.split(r"\s|-|,", raw)
    try:
        month = MONTHS[parts[0][:3].lower()]
        day = int(re.sub(r"\D", "", parts[-2]))
        year = int(parts[-1])
        return datetime(year, month, day, 23, 59, tzinfo=timezone.utc)
    except Exception:
        return None

# ================= SCHEDULE CALCULATOR =================
def compute_schedule(account_count, event_end):
    now = datetime.now(timezone.utc)
    schedule = []

    for i in range(account_count):
        if i == 0:
            schedule.append(now)
        elif i == 1:
            schedule.append(now + timedelta(hours=5))
        elif i == 2:
            schedule.append(now + timedelta(days=2))
        elif i == 3:
            schedule.append(now + timedelta(days=2, hours=5))
        elif i == account_count - 1 and event_end:
            schedule.append(event_end - timedelta(minutes=1))
        else:
            schedule.append(now + timedelta(hours=5 * i))

    return schedule

# ================= GROUP RESOLUTION =================
def normalize(t):
    return re.sub(r"https?://t\.me/", "", t).lstrip("@").lower()

async def resolve_groups(client):
    targets = [normalize(t) for t in TARGET_GROUPS]
    found = []

    async for d in client.iter_dialogs():
        if isinstance(d.entity, (Channel, Chat)):
            name = (d.name or "").lower()
            user = (getattr(d.entity, "username", "") or "").lower()
            if name in targets or user in targets:
                found.append(d.id)
                log("GROUP", f"Found {d.name} ({d.id})")

    return found

# ================= HANDLER =================
handled = set()

def attach_handler(controller, groups, clients):
    @controller.on(events.NewMessage(chats=groups))
    async def handler(e):
        if e.id in handled or e.edit_date or e.forward or e.is_reply:
            return

        text = e.raw_text.strip()
        if not text or not VELO_PATTERN.search(text):
            return

        log("TRIGGER", "$VELO detected")

        ai_text = await ai_reply_once(e.id, text)
        if not ai_text:
            return

        handled.add(e.id)

        is_multi = MULTI_ENTRY_PATTERN.search(text) is not None

        # MULTI-ENTRY MODE
        if is_multi:
            log("ENTRY", "Multi-entry mode")
            async def loop():
                idx = 0
                while True:
                    await clients[idx].send_message(e.chat_id, ai_text, reply_to=e.id)
                    log("SEND", f"Account {idx} replied (loop)")
                    idx = (idx + 1) % len(clients)
                    await asyncio.sleep(MULTI_REPLY_DELAY)
            asyncio.create_task(loop())
            return

        # SINGLE-ENTRY MODE (SCHEDULED)
        log("ENTRY", "Single-entry mode")
        event_end = parse_event_end(text)

        if not event_end:
            await clients[0].send_message(e.chat_id, ai_text, reply_to=e.id)
            log("SEND", "Account 0 replied (no event end)")
            return

        schedule = compute_schedule(len(clients), event_end)

        for idx, send_time in enumerate(schedule):
            delay = (send_time - datetime.now(timezone.utc)).total_seconds()
            if delay <= 0:
                continue

            async def delayed_send(c, d, i):
                await asyncio.sleep(d)
                await c.send_message(e.chat_id, ai_text, reply_to=e.id)
                log("SEND", f"Account {i} replied (scheduled)")

            asyncio.create_task(delayed_send(clients[idx], delay, idx))

# ================= MAIN =================
async def main():
    log("SYSTEM", "Bot starting")

    clients = [
        TelegramClient(f"sessions/user{i}.session", API_ID, API_HASH)
        for i in range(ACCOUNT_COUNT)
    ]

    # 🔒 SEQUENTIAL START (SQLite safe)
    for i, c in enumerate(clients):
        log("CLIENT", f"Starting account {i}")
        await c.start()
        await asyncio.sleep(1.5)

    groups = await resolve_groups(clients[0])
    if not groups:
        log("SYSTEM", "No target groups found", "ERROR")
        return

    attach_handler(clients[0], groups, clients)

    log("SYSTEM", "Bot running")
    await clients[0].run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
