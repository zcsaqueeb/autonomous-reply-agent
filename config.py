# =========================
# 🔐 TELEGRAM API
# =========================
# Get from https://my.telegram.org
API_ID = 123456            # int (replace with your own)
API_HASH = "YOUR_API_HASH_HERE"


# =========================
# 🤖 TELEGRAM BOT
# =========================
# Bot token from @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"


# =========================
# 🧠 GEMINI AI
# =========================
# Get from Google AI Studio
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"


# =========================
# 🎯 TARGET GROUPS
# =========================
# Group name OR @username
# Supports multiple groups
TARGET_GROUPS = [
    "@your_target_group"
]


# =========================
# ⏱️ TIMING CONTROLS
# =========================
# Delay before replying to admin announcement
RESPONSE_DELAY = 1   # seconds


# =========================
# 👥 ACCOUNTS
# =========================
# Number of Telegram user accounts to login via QR
# Example: 2, 3, 4, 5 ...
ACCOUNT_COUNT = 2
MULTI_REPLY_DELAY = 30  # seconds between replies in multi-entry mode


# =========================
# 🔐 TWO-STEP VERIFICATION
# =========================
# Index = account number (user0, user1, user2, ...)
# Value = 2FA password for that account
# Only include accounts that HAVE 2FA
# Leave others out
TWO_FA_PASSWORDS = {
    # 0: "YOUR_2FA_PASSWORD_FOR_USER0",
    # 1: "YOUR_2FA_PASSWORD_FOR_USER1",
}
