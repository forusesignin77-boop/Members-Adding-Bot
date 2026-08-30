"""
🤖 TOOLS BY REHAN – ULTIMATE TELEGRAM BOT
👑 Owner: REHAN | Tag: RN ON TOP
📌 Channel: @ToolsByRehan | Group: @Tools_By_Rehan
🚀 All features + fixed member adding + auto‑join source groups
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
from telethon.tl.functions.channels import JoinChannelRequest, InviteToChannelRequest
from telethon.errors import (
    FloodWaitError, QueryIdInvalidError, PhoneNumberInvalidError,
    PhoneCodeInvalidError, PhoneCodeExpiredError, ChannelPrivateError,
    ChannelInvalidError, UserNotMutualContactError, UserPrivacyRestrictedError
)
from telethon.tl.custom import Button

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ============================================================
# 🔐 CONFIGURATION
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "8644395767:AAFDStlmZ7cwITftnHgUPgPMb7AbRDAXpNs")
API_ID = int(os.getenv("API_ID", "30217812"))
API_HASH = os.getenv("API_HASH", "d21066a90786cf2dd348b907ece69d24")
OWNER_ID = int(os.getenv("OWNER_ID", "8762845215"))
OWNER_NAME = os.getenv("OWNER_NAME", "REHAN")
TAG = os.getenv("TAG", "RN ON TOP")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

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
BOT_USERNAME = None
pending_logins = {}
pending_ops = {}

# ============================================================
# 📂 DATABASE SETUP (unchanged)
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
# 📂 DATABASE HELPER FUNCTIONS (ALL – unchanged)
# ============================================================
# (All helper functions – get_user, create_user, etc. – are identical to previous)

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
# 🎨 UI HELPER FUNCTIONS
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

# ---------- DEBUG LOGGING ----------
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

    if data == "verify":
        try:
            channel_entity = await client.get_entity(REQUIRED_CHANNEL)
            group_entity = await client.get_entity(REQUIRED_GROUP)
            try:
                await client.get_permissions(channel_entity, user_id)
                await client.get_permissions(group_entity, user_id)
                set_verified(user_id)
                await event.edit("✅ Verification successful!")
                inviter, total, ready = get_invite_bonus_status(user_id)
                if ready:
                    inviter_id = award_invite_bonus(user_id)
                    if inviter_id:
                        await client.send_message(inviter_id, f"🎉 Your invited user has completed {INVITE_REQUIRED_ADDS} adds! You earned 100 credits.")
                    await event.respond("🎉 You also earned 100 credits for your inviter.")
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

    # Admin menu actions
    if data.startswith("admin_"):
        if not is_admin(user_id) and user_id != OWNER_ID:
            await event.edit("⛔ Admin access required.", buttons=back_button())
            return

        if data == "admin_list_users":
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
            await event.edit("Usage: `/admin add <user_id>`", buttons=back_button())
            return

        if data == "admin_ban_user":
            await event.edit("Usage: `/admin ban <user_id>`", buttons=back_button())
            return

        if data == "admin_set_credits":
            await event.edit("Usage: `/admin setcredits <user_id> <amount>`", buttons=back_button())
            return

        if data == "admin_broadcast":
            await event.edit("Usage: `/broadcast <message>`", buttons=back_button())
            return

        if data == "admin_backup":
            backup_data()
            await event.edit("✅ Backup completed!", buttons=back_button())
            return

        if data == "admin_stats":
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

    # Main menu actions
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
            text += "\n🔹 **Admin Panel** – click below for controls"
            await event.edit(text, buttons=admin_menu_buttons())
        else:
            await event.edit(text, buttons=back_button())
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
        await event.edit(text, buttons=[[Button.inline("💸 Send Credits", b"send_credits")], back_button()[0]])
        return

    if data == "send_credits":
        await event.edit("💸 **Send Credits**\n\nSend command: `/sendcredits <user_id_or_username> <amount>`\nExample: `/sendcredits 123456789 50` or `/sendcredits @username 50`", buttons=back_button())
        return

    if data == "menu_accounts":
        accounts = get_user_accounts(user_id)
        if not accounts:
            text = "📱 **Your Accounts**\n\nYou have no active accounts. Use /addacc to add one."
        else:
            text = "📱 **Your Accounts:**\n\n"
            for aid, phone, sess in accounts:
                text += f"🆔 ID: `{aid}` | 📞 Phone: `{phone}`\n"
            text += "\nUse /addacc to add more, /removeacc <id> to remove."
        await event.edit(text, buttons=back_button())
        return

    if data == "menu_add":
        await event.edit("➕ **Add Members**\n\nType `/add` and follow the steps:\n1️⃣ Source group\n2️⃣ Target group\n3️⃣ How many to add", buttons=back_button())
        return

    if data == "menu_dm":
        await event.edit("💬 **DM Members**\n\nType `/dm` and follow the steps:\n1️⃣ Group\n2️⃣ How many\n3️⃣ Your message", buttons=back_button())
        return

    if data == "menu_ai_dm":
        if not GROQ_API_KEY:
            await event.edit("❌ AI service not available.", buttons=back_button())
            return
        await event.edit("🤖 **AI DM**\n\nSend command: `/aidm <group_username> <prompt>`\nExample: `/aidm @mygroup Invite message for crypto group`\n\n💡 AI will generate a message, then you can send it via /dm.", buttons=back_button())
        return

    if data == "menu_schedule":
        await event.edit("📅 **Schedules**\n\nCommands:\n`/schedule add <source_group> <target_group> <count> <interval_hours>`\n`/schedule del <task_id>`\n`/schedule toggle <task_id>`\n\n📋 To list: `/schedule`", buttons=back_button())
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
        bot_username = BOT_USERNAME or "tg_members_adding_bot"
        text = f"👥 **Referral System**\n\n"
        text += f"🔑 Your invite code: `{invite_code}`\n"
        text += f"📊 Total invited (completed): {total_invites}\n"
        text += f"🎁 Next tier bonus: {tier_bonus} credits at {25} invites\n"
        text += f"🔗 Share: https://t.me/{bot_username}?start={invite_code}"
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
                         "`/sendcredits` - Send credits to another user\n"
                         "`/addacc` - Add an account (phone only)\n"
                         "`/accounts` - List accounts\n"
                         "`/removeacc` - Remove account\n"
                         "`/add` - Add members (step‑by‑step)\n"
                         "`/dm` - Send DMs (step‑by‑step)\n"
                         "`/aidm` - AI DM\n"
                         "`/schedule` - Manage schedules\n"
                         "`/groups` - Manage account groups\n"
                         "`/analytics` - View stats\n"
                         "`/dashboard` - Growth dashboard\n"
                         "`/referral` - Referral system\n"
                         "`/settings` - Configure filters\n"
                         "`/addedmembers` - List added members\n"
                         "`/spintax` - Toggle spintax\n"
                         "`/skip` - Skip existing toggle\n"
                         "`/clone` - Clone group members (step‑by‑step)\n\n"
                         "**Admin Commands:** (only for admins – hidden from users)\n"
                         "`/admin add/remove <user_id>`\n"
                         "`/admin ban/unban <user_id>`\n"
                         "`/admin delete <user_id>`\n"
                         "`/admin setcredits <user_id> <amount>`\n"
                         "`/broadcast` - Send global message\n"
                         "`/backup` - Backup database\n"
                         "`/stats` - Bot statistics", buttons=back_button())
        return

    await event.answer("❓ Unknown action.", alert=True)

# ---------- COMMAND HANDLERS ----------

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

@client.on(events.NewMessage(pattern='/help', func=is_private))
async def help_cmd(event):
    await start(event)

@client.on(events.NewMessage(pattern='/ping', func=is_private))
async def ping(event):
    await event.reply("🏓 Pong! Bot is alive and responding.")

@client.on(events.NewMessage(pattern='/verify', func=is_private))
async def verify(event):
    user_id = event.sender_id
    if is_banned(user_id):
        await event.reply("🚫 Banned.")
        return
    try:
        channel_entity = await client.get_entity(REQUIRED_CHANNEL)
        group_entity = await client.get_entity(REQUIRED_GROUP)
        try:
            await client.get_permissions(channel_entity, user_id)
            await client.get_permissions(group_entity, user_id)
            set_verified(user_id)
            await event.reply("✅ Verification successful!")
            inviter, total, ready = get_invite_bonus_status(user_id)
            if ready:
                inviter_id = award_invite_bonus(user_id)
                if inviter_id:
                    await client.send_message(inviter_id, f"🎉 Your invited user has completed {INVITE_REQUIRED_ADDS} adds! You earned 100 credits.")
                await event.reply("🎉 You also earned 100 credits for your inviter.")
            await start(event)
        except:
            await event.reply("❌ You haven't joined the required channel/group.")
    except Exception as e:
        logger.error("Verify error: %s", e)
        await event.reply("❌ Error checking verification. Please try again later.")

@client.on(events.NewMessage(pattern='/credits', func=is_private))
async def credits_cmd(event):
    user_id = event.sender_id
    credits = get_credits(user_id)
    await event.reply(f"💰 Your credits: {credits}", buttons=[[Button.inline("💸 Send Credits", b"send_credits")], [Button.inline("🔙 Back", b"menu_main")]])

@client.on(events.NewMessage(pattern='/sendcredits', func=is_private))
async def send_credits(event):
    user_id = event.sender_id
    if is_banned(user_id) or not is_verified(user_id):
        await event.reply("❌ You need to be verified and not banned.")
        return
    args = event.message.text.split()
    if len(args) < 3:
        await event.reply("Usage: `/sendcredits <user_id_or_username> <amount>`\nExample: `/sendcredits 123456789 50` or `/sendcredits @username 50`")
        return
    target = args[1]
    amount = int(args[2])
    if amount <= 0:
        await event.reply("❌ Amount must be positive.")
        return
    if target.startswith('@'):
        target_user = get_user_by_username(target[1:])
        if not target_user:
            await event.reply("❌ User not found.")
            return
        target_id = target_user
    else:
        try:
            target_id = int(target)
        except ValueError:
            await event.reply("❌ Invalid user ID or username.")
            return
    if target_id == user_id:
        await event.reply("❌ You cannot send credits to yourself.")
        return
    sender_credits = get_credits(user_id)
    if sender_credits < amount:
        await event.reply(f"❌ Insufficient credits. You have {sender_credits}, need {amount}.")
        return
    deduct_credit(user_id, amount)
    add_credits(target_id, amount, f"sent from {user_id}")
    add_credit_log(user_id, -amount, f"sent to {target_id}")
    add_credit_log(target_id, amount, f"received from {user_id}")
    await event.reply(f"✅ Successfully sent {amount} credits to user {target_id}.")
    try:
        await client.send_message(target_id, f"💸 You received {amount} credits from user {user_id}.")
    except:
        pass

# ---------- ADD ACCOUNT – PHONE ONLY ----------
@client.on(events.NewMessage(pattern='/addacc', func=is_private))
async def add_account_start(event):
    user_id = event.sender_id
    if is_banned(user_id) or not is_verified(user_id):
        await event.reply("❌ You need to be verified and not banned.")
        return
    if user_id in pending_logins:
        await event.reply("⏳ You already have a pending login. Provide the code or use /cancel.")
        return

    args = event.message.text.split()
    if len(args) > 1:
        phone = args[1]
        if not re.match(r'^\+\d+$', phone):
            await event.reply("❌ Invalid phone format. Use country code, e.g. +1234567890")
            return
        try:
            temp_client = TelegramClient(StringSession(), API_ID, API_HASH)
            await temp_client.connect()
            await temp_client.send_code_request(phone)
            pending_logins[user_id] = {
                'client': temp_client,
                'phone': phone,
                'step': 'awaiting_code'
            }
            await event.reply(f"📲 Verification code sent to {phone}. Enter the code (numbers only).")
        except PhoneNumberInvalidError:
            await event.reply("❌ Invalid phone number. Check and try again.")
        except Exception as e:
            await event.reply(f"❌ Failed to send code: {e}")
        return

    try:
        temp_client = TelegramClient(StringSession(), API_ID, API_HASH)
        await temp_client.connect()
        pending_logins[user_id] = {
            'client': temp_client,
            'step': 'awaiting_phone',
            'phone': None
        }
        await event.reply("📱 Send your phone with country code.\nExample: `+1234567890`\n\nUse /cancel to abort.")
    except Exception as e:
        await event.reply(f"❌ Failed to initialize: {e}")

@client.on(events.NewMessage(pattern='/cancel', func=is_private))
async def cancel_operation(event):
    user_id = event.sender_id
    if user_id in pending_logins:
        try:
            await pending_logins[user_id]['client'].disconnect()
        except:
            pass
        del pending_logins[user_id]
        await event.reply("✅ Login cancelled.")
    elif user_id in pending_ops:
        del pending_ops[user_id]
        await event.reply("✅ Operation cancelled.")
    else:
        await event.reply("❌ No pending operation.")

@client.on(events.NewMessage(func=is_private))
async def handle_login_step(event):
    user_id = event.sender_id
    if user_id not in pending_logins:
        return
    text = event.text.strip()
    if text.startswith('/'):
        return
    login_data = pending_logins[user_id]
    step = login_data.get('step')
    phone = login_data.get('phone')
    client_obj = login_data.get('client')

    if step == 'awaiting_phone':
        phone = text
        if not re.match(r'^\+\d+$', phone):
            await event.reply("❌ Invalid phone format. Use country code, e.g. +1234567890")
            return
        try:
            login_data['phone'] = phone
            await client_obj.send_code_request(phone)
            login_data['step'] = 'awaiting_code'
            await event.reply("📲 Verification code sent. Enter the code (numbers only).")
        except PhoneNumberInvalidError:
            await event.reply("❌ Invalid phone number. Check and try again.")
            await client_obj.disconnect()
            del pending_logins[user_id]
        except Exception as e:
            await event.reply(f"❌ Failed to send code: {e}")
            await client_obj.disconnect()
            del pending_logins[user_id]

    elif step == 'awaiting_code':
        code = text.strip()
        if not code.isdigit():
            await event.reply("❌ Enter only the numeric code.")
            return
        try:
            await client_obj.sign_in(phone, code)
            session_string = StringSession.save(client_obj.session)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id FROM user_accounts WHERE user_id = ? AND phone = ?", (user_id, phone))
            if c.fetchone():
                conn.close()
                await event.reply("⚠️ This phone is already added.")
                await client_obj.disconnect()
                del pending_logins[user_id]
                return
            add_user_account(user_id, phone, session_string)
            await event.reply(f"✅ Account with phone {phone} added successfully.")
            await client_obj.disconnect()
            del pending_logins[user_id]
        except PhoneCodeInvalidError:
            await event.reply("❌ Invalid code. Try again.")
        except PhoneCodeExpiredError:
            await event.reply("❌ Code expired. Restart with /addacc.")
            await client_obj.disconnect()
            del pending_logins[user_id]
        except Exception as e:
            await event.reply(f"❌ Login failed: {e}")
            await client_obj.disconnect()
            del pending_logins[user_id]

# ---------- STEP‑BY‑STEP ADD MEMBERS (FIXED) ----------
@client.on(events.NewMessage(pattern='/add', func=is_private))
async def add_start(event):
    user_id = event.sender_id
    if is_banned(user_id) or not is_verified(user_id):
        await event.reply("❌ Not allowed.")
        return
    if user_id in pending_ops:
        await event.reply("⏳ You already have a pending operation. Please complete it or use /cancel.")
        return

    pending_ops[user_id] = {'type': 'add', 'step': 'source'}
    await event.reply("📤 **Step 1/3:** Which group do you want to copy members **from**?\n\nSend the group username (e.g., @sourcegroup).\nUse /cancel to abort.")

@client.on(events.NewMessage(func=is_private))
async def handle_interactive_add(event):
    user_id = event.sender_id
    if user_id not in pending_ops:
        return
    op = pending_ops[user_id]
    if op['type'] != 'add':
        return
    if event.text.startswith('/'):
        return
    text = event.text.strip()
    step = op['step']

    if step == 'source':
        op['source'] = text
        op['step'] = 'target'
        await event.reply("📥 **Step 2/3:** Which group do you want to add members **to**?\n\nSend the target group username (e.g., @targetgroup).")
    elif step == 'target':
        op['target'] = text
        op['step'] = 'count'
        await event.reply("🔢 **Step 3/3:** How many members do you want to add?\n\nSend a number.")
    elif step == 'count':
        try:
            count = int(text)
            if count <= 0:
                await event.reply("❌ Please send a positive number.")
                return
            op['count'] = count
            del pending_ops[user_id]
            await event.reply(f"⏳ Starting add of {count} members from {op['source']} to {op['target']}...")
            asyncio.create_task(do_interactive_add(event, user_id, op['source'], op['target'], count))
        except ValueError:
            await event.reply("❌ Please send a valid number.")

async def do_interactive_add(event, user_id, source, target, count):
    credits = get_credits(user_id)
    cost = get_add_cost()
    total_cost = count * cost
    if credits < total_cost:
        await event.reply(f"❌ Insufficient credits. Need {total_cost}, you have {credits}.")
        return
    accounts = get_user_accounts(user_id)
    if not accounts:
        await event.reply("❌ No active accounts. Add one with /addacc.")
        return
    deduct_credit(user_id, total_cost)

    try:
        source_entity = await client.get_entity(source)
        target_entity = await client.get_entity(target)
    except Exception as e:
        await event.reply(f"❌ Invalid group: {e}")
        add_credits(user_id, total_cost, "refund_add_fail")
        return

    target_group_id = target_entity.id
    added = 0
    failed = 0
    account_index = 0
    settings = get_settings(user_id)
    skip_existing = settings[8] if len(settings) > 8 else 1

    for i in range(count):
        try:
            account_id, phone, session_string = accounts[account_index % len(accounts)]
            account_index += 1
            user_client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await user_client.connect()
            if not await user_client.is_user_authorized():
                deactivate_account(account_id)
                await event.reply(f"⚠️ Account {phone} deactivated (not authorized).")
                continue

            # JOIN SOURCE GROUP – CRITICAL STEP
            try:
                await user_client(JoinChannelRequest(source_entity))
                await asyncio.sleep(2)  # Wait for join to take effect
                logger.info(f"✅ Joined source group {source} with account {phone}")
            except Exception as e:
                logger.warning(f"⚠️ Could not join source group {source}: {e}")
                # Try to get participants anyway – maybe already a member
                pass

            # GET PARTICIPANTS
            try:
                participants = await user_client.get_participants(source_entity, limit=1, offset=i)
                if not participants:
                    await event.reply(f"⚠️ No more members to fetch from {source} (stopped at {i})")
                    break
                member = participants[0]
                member_id = member.id
                
                if skip_existing and is_member_added(user_id, target_group_id, member_id):
                    failed += 1
                    continue
                    
                # INVITE TO TARGET
                try:
                    await user_client(InviteToChannelRequest(target_entity, [member_id]))
                    mark_member_added(user_id, target_group_id, member_id, account_id, target, member.username or "", member.first_name or "")
                    added += 1
                    increment_daily_add(user_id)
                    await asyncio.sleep(ADD_DELAY)
                    if added % 5 == 0:
                        await event.reply(f"✅ Progress: Added {added} members so far...")
                except FloodWaitError as e:
                    await event.reply(f"⏳ Flood wait {e.seconds}s – pausing...")
                    await asyncio.sleep(e.seconds)
                except UserPrivacyRestrictedError:
                    failed += 1
                except Exception as e:
                    logger.error(f"Invite error: {e}")
                    failed += 1
            except ChannelPrivateError:
                await event.reply(f"❌ The group {source} is private. The bot account must be a member first.")
                break
            except ChannelInvalidError:
                await event.reply(f"❌ Invalid group: {source}. Please check the username.")
                break
            except Exception as e:
                logger.error(f"Get participants error: {e}")
                failed += 1
                await asyncio.sleep(1)
            finally:
                try:
                    await user_client.disconnect()
                except:
                    pass
        except Exception as e:
            logger.error(f"Account error: {e}")
            failed += 1
            continue

    update_group_analytics(user_id, target_group_id, added, failed)
    await event.reply(f"✅ **Done:** Added {added} members, failed {failed}.")

# ---------- STEP‑BY‑STEP DM ----------
@client.on(events.NewMessage(pattern='/dm', func=is_private))
async def dm_start(event):
    user_id = event.sender_id
    if is_banned(user_id) or not is_verified(user_id):
        await event.reply("❌ Not allowed.")
        return
    if user_id in pending_ops:
        await event.reply("⏳ You already have a pending operation. Please complete it or use /cancel.")
        return

    pending_ops[user_id] = {'type': 'dm', 'step': 'group'}
    await event.reply("💬 **Step 1/3:** Which group do you want to DM members **from**?\n\nSend the group username (e.g., @mygroup).\nUse /cancel to abort.")

@client.on(events.NewMessage(func=is_private))
async def handle_interactive_dm(event):
    user_id = event.sender_id
    if user_id not in pending_ops:
        return
    op = pending_ops[user_id]
    if op['type'] != 'dm':
        return
    if event.text.startswith('/'):
        return
    text = event.text.strip()
    step = op['step']

    if step == 'group':
        op['group'] = text
        op['step'] = 'count'
        await event.reply("🔢 **Step 2/3:** How many members do you want to DM?\n\nSend a number.")
    elif step == 'count':
        try:
            count = int(text)
            if count <= 0:
                await event.reply("❌ Please send a positive number.")
                return
            op['count'] = count
            op['step'] = 'message'
            await event.reply("✍️ **Step 3/3:** What message do you want to send to these members?\n\nSend your message now.")
        except ValueError:
            await event.reply("❌ Please send a valid number.")
    elif step == 'message':
        op['message'] = text
        del pending_ops[user_id]
        await event.reply(f"⏳ Sending DMs to {op['count']} members in {op['group']}...")
        asyncio.create_task(do_interactive_dm(event, user_id, op['group'], op['count'], op['message']))

async def do_interactive_dm(event, user_id, group_username, count, message):
    credits = get_credits(user_id)
    cost = get_dm_cost()
    total_cost = count * cost
    if credits < total_cost:
        await event.reply(f"❌ Need {total_cost} credits, you have {credits}.")
        return
    accounts = get_user_accounts(user_id)
    if not accounts:
        await event.reply("❌ No accounts.")
        return
    deduct_credit(user_id, total_cost)
    try:
        target_group = await client.get_entity(group_username)
    except Exception as e:
        await event.reply(f"❌ Invalid group: {e}")
        add_credits(user_id, total_cost, "refund_dm_fail")
        return
    group_id = target_group.id
    settings = get_settings(user_id)
    spintax_enabled = settings[6] if len(settings) > 6 else 0
    sent = 0
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
            # Join group if not already member
            try:
                await user_client(JoinChannelRequest(target_group))
                await asyncio.sleep(1)
            except:
                pass
            participants = await user_client.get_participants(target_group, limit=1, offset=i)
            if not participants:
                break
            member = participants[0]
            member_id = member.id
            if is_dm_sent(user_id, member_id, group_id):
                failed += 1
                continue
            msg = message
            if spintax_enabled:
                msg = apply_spintax(msg)
            try:
                await user_client.send_message(member_id, msg)
                add_dm_sent(user_id, member_id, group_id)
                sent += 1
                await asyncio.sleep(DM_DELAY)
            except Exception as e:
                failed += 1
            await user_client.disconnect()
        except Exception as e:
            failed += 1
    await event.reply(f"✅ DMs sent: {sent}, failed: {failed}.")

# ---------- STEP‑BY‑STEP CLONE ----------
@client.on(events.NewMessage(pattern='/clone', func=is_private))
async def clone_start(event):
    user_id = event.sender_id
    if is_banned(user_id) or not is_verified(user_id):
        await event.reply("❌ Not allowed.")
        return
    if user_id in pending_ops:
        await event.reply("⏳ You already have a pending operation. Please complete it or use /cancel.")
        return

    pending_ops[user_id] = {'type': 'clone', 'step': 'source'}
    await event.reply("📤 **Step 1/2:** Which group do you want to clone **from**?\n\nSend the source group username (e.g., @sourcegroup).\nUse /cancel to abort.")

@client.on(events.NewMessage(func=is_private))
async def handle_interactive_clone(event):
    user_id = event.sender_id
    if user_id not in pending_ops:
        return
    op = pending_ops[user_id]
    if op['type'] != 'clone':
        return
    if event.text.startswith('/'):
        return
    text = event.text.strip()
    step = op['step']

    if step == 'source':
        op['source'] = text
        op['step'] = 'target'
        await event.reply("📥 **Step 2/2:** Which group do you want to clone **to**?\n\nSend the target group username (e.g., @targetgroup).")
    elif step == 'target':
        op['target'] = text
        del pending_ops[user_id]
        await event.reply(f"⏳ Cloning from {op['source']} to {op['target']}...")
        asyncio.create_task(do_interactive_clone(event, user_id, op['source'], op['target']))

async def do_interactive_clone(event, user_id, source, target):
    try:
        source_entity = await client.get_entity(source)
        source_participants = await client.get_participants(source_entity)
        count = len(source_participants)
    except Exception as e:
        await event.reply(f"❌ Error: {e}")
        return
    if count == 0:
        await event.reply("❌ Source group has no members.")
        return
    credits = get_credits(user_id)
    cost = get_add_cost()
    total_cost = count * cost
    if credits < total_cost:
        await event.reply(f"❌ Insufficient credits for {count} members. Need {total_cost}, you have {credits}.")
        return
    accounts = get_user_accounts(user_id)
    if not accounts:
        await event.reply("❌ No accounts.")
        return
    deduct_credit(user_id, total_cost)
    try:
        target_entity = await client.get_entity(target)
    except Exception as e:
        await event.reply(f"❌ Invalid target group: {e}")
        add_credits(user_id, total_cost, "refund_clone_fail")
        return
    target_group_id = target_entity.id
    added = 0
    failed = 0
    account_index = 0
    settings = get_settings(user_id)
    skip_existing = settings[8] if len(settings) > 8 else 1
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
                await user_client(JoinChannelRequest(source_entity))
                await asyncio.sleep(1)
            except:
                pass
            participants = await user_client.get_participants(source_entity, limit=1, offset=i)
            if not participants:
                break
            member = participants[0]
            member_id = member.id
            if skip_existing and is_member_added(user_id, target_group_id, member_id):
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
            await user_client.disconnect()
        except Exception as e:
            failed += 1
            continue
    update_group_analytics(user_id, target_group_id, added, failed)
    await event.reply(f"✅ Clone completed: Added {added} members, failed {failed}.")

# ---------- OTHER COMMANDS (unchanged) ----------
# (accounts, removeacc, aidm, schedule, groups, analytics, dashboard, referral, addedmembers, spintax, skip, settings, admin, broadcast, backup, stats)

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
    except Exception as e:
        logger.error("Scheduled task error: invalid groups %s", e)
        return
    target_group_id = target_entity.id
    added = 0
    failed = 0
    account_index = 0
    settings = get_settings(user_id)
    skip_existing = settings[8] if len(settings) > 8 else 1
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
                await user_client(JoinChannelRequest(source_entity))
                await asyncio.sleep(1)
            except:
                pass
            try:
                participants = await user_client.get_participants(source_entity, limit=1, offset=i)
                if not participants:
                    break
                member = participants[0]
                member_id = member.id
                if skip_existing and is_member_added(user_id, target_group_id, member_id):
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
    global BOT_USERNAME
    logger.info("🤖 Tools By Rehan Bot is starting...")
    while True:
        try:
            logger.info("🔌 Attempting to connect to Telegram...")
            await client.start(bot_token=BOT_TOKEN)
            me = await client.get_me()
            BOT_USERNAME = me.username
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
