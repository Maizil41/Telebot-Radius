import os
import re
import sys
import json
import random
import string
import logging
import pymysql
import asyncio
import datetime
import subprocess
from datetime import datetime
from telegram.error import TimedOut
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, Updater, JobQueue, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

# WARNING ❗
# Script ini disusun oleh 𝐌𝐚𝐢𝐳𝐢𝐥(https://t.me/maizil41) gunakan secara wajar, jangan mengedit lalu mengunggah ulang ke grup lain tanpa konfirmasi terlebih dahulu.
# ⓒ 2024 - Mutiara-Wrt by Maizil https://t.me/maizil41

with open("/root/Telebot-Radius/files/auth", "r") as token_file:
    lines = token_file.readlines()
    
    if len(lines) >= 2:
        TOKEN = lines[0].strip()
        
        try:
            # Mengambil beberapa ID admin dari baris kedua, jika ada
            USER_IDS = [int(user_id.strip()) for user_id in lines[1].strip().split(',')]
        except ValueError as e:
            print(f"Error parsing user IDs: {e}")
            USER_IDS = []  # Atau tangani kesalahan sesuai kebutuhan

    else:
        print("Berkas token harus memiliki setidaknya 2 baris (token dan chat ID admin).")
        exit()
        
with open("/root/Telebot-Radius/files/ip_address.json", "r") as file:
    ip_data = json.load(file)

ip_chilli = ip_data["ip_chilli"]
ip_lan = ip_data["ip_lan"]

with open('/root/Telebot-Radius/files/db.json') as f:
    config = json.load(f)

DB_HOST = config['DB_HOST']
DB_USER = config['DB_USER']
DB_PASS = config['DB_PASS']
DB_NAME = config['DB_NAME']

# File JSON untuk menyimpan saldo pengguna
PROFILES_JSON_FILE = "/root/Telebot-Radius/files/profiles.json"

# Lokasi File yang dibutuhkan
LAST_POSITION_FILE = "/root/Telebot-Radius/files/bot.pid"
FILE_PATH = "/root/Telebot-Radius/files/radius.sql"
LOG_FILE_PATH = "/tmp/log/radius.log"
DURATION_KEYBOARD = "/root/Telebot-Radius/files/duration_keyboard.json"
QUANTITY_KEYBOARD = "/root/Telebot-Radius/files/quantity_keyboard.json"
DURATION_FILE = "/root/Telebot-Radius/files/durations.json"
DEFAULT_FILE_UPLOAD_PATH  = "/root/"

POLL_INTERVAL = 5
MAX_ERRORS = 3

# Daftar ID admin yang diizinkan
ADMIN_IDS = set(USER_IDS)

# State untuk conversation handler
CHOOSE_DURATION, TOPUP_AMOUNT, LAST_POSITION, ASK_FOR_FILE, PILIH_TINDAKAN, PILIH_JUMLAH, PILIH_DURASI = range(7)

# Restart bot apabila ada kesalahan
def restart_bot():
    os.system('/etc/init.d/telebot restart')

def save_last_position(position):
    with open(LAST_POSITION_FILE, "w") as f:
        f.write(str(position))

# Fungsi untuk membaca data dari file profile
def read_profiles():
    try:
        with open(PROFILES_JSON_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Fungsi untuk menulis data ke file profile
def write_profiles(profiles):
    with open(PROFILES_JSON_FILE, "w") as file:
        json.dump(profiles, file, indent=4)

# Fungsi untuk memuat data dari file JSON
def load_duration_data(filename):
    with open(DURATION_FILE, 'r') as file:
        data = json.load(file)
    return data

# Fungsi untuk memuat data keyboard dari file JSON
def load_keyboard_quantity(filename):
    with open(QUANTITY_KEYBOARD, 'r') as file:
        data = json.load(file)
    return data['keyboard']
    
# Fungsi untuk mengonversi data JSON ke dalam format InlineKeyboardMarkup
def create_keyboard_quantity(keyboard_data):
    keyboard = [[InlineKeyboardButton(button['text'], callback_data=button['callback_data'])
                 for button in row] for row in keyboard_data]
    return InlineKeyboardMarkup(keyboard)
    
# Memuat data keyboard dari file JSON
quantity_keyboard_data = load_keyboard_quantity('quantity_keyboard.json')
quantity_keyboard_markup = create_keyboard_quantity(quantity_keyboard_data)

# Fungsi untuk memuat data keyboard dari file JSON
def load_keyboard_duration(filename):
    with open(DURATION_KEYBOARD, 'r') as file:
        data = json.load(file)
    return data['keyboard']

# Fungsi untuk mengonversi data JSON ke dalam format InlineKeyboardMarkup
def create_keyboard_duration(keyboard_data):
    keyboard = [[InlineKeyboardButton(button['text'], callback_data=button['callback_data'])
                 for button in row] for row in keyboard_data]
    return InlineKeyboardMarkup(keyboard)

# Memuat data keyboard dari file JSON
duration_keyboard_data = load_keyboard_duration('duration_keyboard.json')
duration_keyboard_markup = create_keyboard_duration(duration_keyboard_data)

def generate_random_string(length=4):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
    
# Fungsi untuk memeriksa apakah pengguna adalah admin
def is_admin(user_id):
    return user_id in ADMIN_IDS


# Command /start untuk memberikan daftar command kepada admin dan sambutan kepada user
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username
    profiles = read_profiles()
    balance = profiles.get(str(user_id), {}).get("balance", 0)
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)

    if is_admin(user_id):
        commands = """      
        DAFTAR COMMAND UNTUK ADMIN     
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                   COMMAND TELEGRAM

1. /topup - Topup saldo manual
2. /saldo - Cek saldo user
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                COMMAND DALORADIUS 

1. /backup - Backup database radius
2. /replace - Ganti database radius
3. /list - List voucher daloradius
4. /online - List online user daloradius
5. /kick - Disconnect user daloradius
6. /hapus - Hapus voucher daloradius
8. /generate - Generate voucher daloradius
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                  COMMAND OPENWRT

1. /upload <filepath> - Unggah file ke openwrt
2. /cmd <cmd> - Custom cmd openwrt
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
        button = InlineKeyboardButton(text="Dukung Admin", url="https://saweria.co/MutiaraWrt")
        keyboard = InlineKeyboardMarkup([[button]])
        await update.message.reply_text(f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ {commands}", reply_markup=keyboard)

    else:
        welcome_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
 SELAMAT DATANG DI MUTIARA-WRT
                   TELEBOT-RADIUS
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
USERNAME  :  @{username}
USER ID         :  {user_id}
BALANCE      :   Rp.{balance}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
        keyboard = [
            [
                InlineKeyboardButton("DAPATKAN KODE", callback_data="get_code"),
                InlineKeyboardButton("TOPUP SALDO", callback_data="start_topup"),
            ],
            [InlineKeyboardButton("HUBUNGI ADMIN", url="https://t.me/Maizil41")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)


# Fungsi untuk menangani
async def send_services_menu(update, context):
    await update.callback_query.message.edit_reply_markup(reply_markup=None)
    welcome_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
    keyboard = [
    [
        InlineKeyboardButton("HUBUNGI ADMIN", url="https://t.me/Maizil41"),
        InlineKeyboardButton("TOPUP SALDO", callback_data="start_topup"),
    ],
]
    reply_markup = InlineKeyboardMarkup(keyboard)
        
    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    else:
        # Tangani kasus ketika update.message adalah None
        # Misalnya, mengirim pesan ke chat ID tertentu jika diperlukan
        chat_id = update.callback_query.message.chat_id if update.callback_query else None
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=welcome_message, reply_markup=reply_markup)
            
# Fungsi untuk menangani perintah /menu
async def show_menu(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username
    profiles = read_profiles()
    balance = profiles.get(str(user_id), {}).get("balance", 0)
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    
    if is_admin(user_id):
        commands = """      
        DAFTAR COMMAND UNTUK ADMIN     
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                   COMMAND TELEGRAM

1. /topup - Topup saldo manual
2. /saldo - Cek saldo user
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                COMMAND DALORADIUS 

1. /backup - Backup database radius
2. /replace - Ganti database radius
3. /list - List voucher daloradius
4. /online - List online user daloradius
5. /kick - Disconnect user daloradius
6. /hapus - Hapus voucher daloradius
8. /generate - Generate voucher daloradius
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                  COMMAND OPENWRT

1. /upload <filepath> - Unggah file ke openwrt
2. /cmd <cmd> - Custom cmd openwrt
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
        button = InlineKeyboardButton(text="Dukung Admin", url="https://saweria.co/MutiaraWrt")
        keyboard = InlineKeyboardMarkup([[button]])
        await update.message.reply_text(f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ {commands}", reply_markup=keyboard)
    else:
        welcome_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                   SERVICES MENU
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
   SILAHKAN PILIH MENU DIBAWAH
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
        keyboard = [
            [
                InlineKeyboardButton("DAPATKAN KODE", callback_data="get_code"),
                InlineKeyboardButton("TOPUP SALDO", callback_data="start_topup"),
            ],
            [InlineKeyboardButton("HUBUNGI ADMIN", url="https://t.me/Maizil41")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

def split_message(message, max_length=4096):
    # Membagi pesan menjadi bagian yang lebih kecil jika diperlukan
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

async def alluser(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            # Kirim pesan "Please wait"
            sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")

            # Query untuk mengambil daftar pengguna dan status mereka dengan emoji
            query = """
            SELECT
                r.username,
                CASE
                    WHEN latest_acct.username IS NULL THEN 'OFFLINE 🔴'
                    WHEN latest_acct.acctstoptime IS NOT NULL THEN 'OFFLINE 🔴'
                    WHEN latest_acct.acctstoptime IS NULL AND latest_acct.acctterminatecause = 'Session-Timeout' THEN 'EXPIRED ❌'
                    ELSE 'ONLINE 🟢'
                END AS status
            FROM radcheck r
            LEFT JOIN (
                SELECT username, 
                       acctstoptime, 
                       acctterminatecause
                FROM radacct
                WHERE (username, acctstarttime) IN (
                    SELECT username, MAX(acctstarttime)
                    FROM radacct
                    GROUP BY username
                )
            ) latest_acct
            ON r.username = latest_acct.username
            """
            # Eksekusi query menggunakan perintah mysql dengan encoding utf8mb4
            result = subprocess.run(
                [
                    "mysql",
                    "-u", DB_USER,
                    "-p" + DB_PASS,
                    "--default-character-set=utf8mb4",
                    "-e", query,
                    DB_NAME
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

            # Menyusun pesan untuk user
            output = result.stdout.strip()
            if output:
                # Format output agar lebih mudah dibaca
                lines = output.splitlines()
                data_lines = lines[1:]
                
                # Menyusun pesan dengan format yang lebih baik
                batch_size = 10
                message_batches = []
                current_batch = """▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                    LIST ALL USER
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
                
                for index, line in enumerate(data_lines):
                    fields = line.split("\t")
                    current_batch += (f"""
USERNAME  : {fields[0]}
STATUS  :  {fields[1]}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""")
                    
                    # Jika sudah mencapai batch_size, tambahkan batch ke message_batches dan reset
                    if (index + 1) % batch_size == 0:
                        message_batches.append(current_batch)
                        current_batch = """▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
                
                # Tambahkan batch terakhir jika ada
                if current_batch.strip():
                    message_batches.append(current_batch)

                await context.bot.delete_message(
                    chat_id=update.effective_chat.id, message_id=sent_message.message_id
                )

                # Kirim setiap batch pesan
                for batch in message_batches:
                    message_parts = split_message(batch)
                    for part in message_parts:
                        await update.message.reply_text(part)
            else:
                message = "𝙏𝙞𝙙𝙖𝙠 𝙖𝙙𝙖 𝙙𝙖𝙩𝙖 𝙥𝙚𝙣𝙜𝙜𝙪𝙣𝙖 𝙨𝙖𝙖𝙩 𝙞𝙣𝙞."
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id, message_id=sent_message.message_id
                )
                await update.message.reply_text(message)

        except subprocess.CalledProcessError as e:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=sent_message.message_id
            )
            await update.message.reply_text(
                f"Terjadi kesalahan saat mengakses database: {e.stderr}"
            )
    else:
        sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
        await update.message.reply_text(
            "𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣."
        )

async def online(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")

            query = """
                SELECT ra.username, 
                       ra.acctstarttime, 
                       ra.framedipaddress, 
                       ra.callingstationid,
                       ub.planname AS harga
                FROM radacct ra
                LEFT JOIN userbillinfo ub ON ra.username = ub.username
                WHERE ra.acctstoptime IS NULL
            """
            result = subprocess.run(
                [
                    "mysql",
                    "-u", DB_USER,
                    "-p" + DB_PASS,
                    "--default-character-set=utf8mb4",  # Menyertakan opsi encoding UTF-8
                    "-e", query,
                    DB_NAME
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

            output = result.stdout.strip()
            if output:
                # Format output agar lebih mudah dibaca
                lines = output.splitlines()
                headers = lines[0].split("\t")
                data_lines = lines[1:]
                
                # Menyusun pesan dengan format yang lebih baik
                message = """▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ 
                    ONLINE USER
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ """
                for line in data_lines:
                    fields = line.split("\t")
                    message += (f"""
USERNAME   :  {fields[0]}
MAC ADDR    :  {fields[3]}
IP ADDRESS  :  {fields[2]}
PAKET :  {fields[4]}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""")
            else:
                message = "𝙏𝙞𝙙𝙖𝙠 𝙖𝙙𝙖 𝙪𝙨𝙚𝙧 𝙤𝙣𝙡𝙞𝙣𝙚 𝙨𝙖𝙖𝙩 𝙞𝙣𝙞."

            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=sent_message.message_id
            )
            await update.message.reply_text(message)

        except subprocess.CalledProcessError as e:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=sent_message.message_id
            )
            await update.message.reply_text(
                f"Terjadi kesalahan saat mengakses database: {e.stderr}"
            )
    else:
        sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
        await update.message.reply_text(
            "𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣."
        )

async def delete_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")

            if context.args:
                username = context.args[0]
            else:
                message = f"Gunakan perintah : /hapus <username>."
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
                await update.message.reply_text(message)
                return

            check_query = f"SELECT COUNT(*) FROM radcheck WHERE username='{username}'"
            
            check_result = subprocess.run(
                [
                    "mysql",
                    "-u", DB_USER,
                    "-p" + DB_PASS,
                    "--default-character-set=utf8mb4",
                    "-e", check_query,
                    DB_NAME
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            count = int(check_result.stdout.strip().split("\n")[1])

            if count == 0:
                message = f"Username '{username}' tidak terdapat di database."
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
                await update.message.reply_text(message)
                return

            delete_queries = [
                f"DELETE FROM radcheck WHERE username='{username}'",
                f"DELETE FROM radusergroup WHERE username='{username}'",
                f"DELETE FROM userinfo WHERE username='{username}'"
            ]
            
            for query in delete_queries:
                subprocess.run(
                    [
                        "mysql",
                        "-u", DB_USER,
                        "-p" + DB_PASS,
                        "--default-character-set=utf8mb4",
                        "-e", query,
                        DB_NAME
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )

            message = f"Pengguna '{username}' berhasil dihapus dari database."

            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=sent_message.message_id
            )
            await update.message.reply_text(message)

        except subprocess.CalledProcessError as e:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=sent_message.message_id
            )
            await update.message.reply_text(
                f"Terjadi kesalahan saat mengakses database: {e.stderr}"
            )
    else:
        sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
        await update.message.reply_text(
            "𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣."
        )

async def disconnect_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            # Kirim pesan "Please wait"
            sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")

            # Ambil username dari pesan
            if not context.args:
                message = f"Gunakan perintah : /kick <username>."
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
                await update.message.reply_text(message)
                return
            
            username = context.args[0]

            # Query untuk mendapatkan Acct-Session-Id dan username
            check_query = f"SELECT acctsessionid FROM radacct WHERE username='{username}' AND acctstoptime IS NULL"
            
            # Eksekusi query untuk mendapatkan Acct-Session-Id
            check_result = subprocess.run(
                [
                    "mysql",
                    "-u", DB_USER,
                    "-p" + DB_PASS,
                    "--default-character-set=utf8mb4",
                    "-e", check_query,
                    DB_NAME
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # Ambil hasil query
            output = check_result.stdout.strip().split("\n")
            if len(output) < 2:
                message = f"Username '{username}' tidak sedang online atau tidak terdapat di database."
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
                await update.message.reply_text(message)
                return

            # Ambil Acct-Session-Id
            acctsessionid = output[1].strip()

            # Gunakan radclient untuk disconnect user
            command = (
                f'echo \'User-Name="{username}",Acct-Session-Id="{acctsessionid}",Framed-IP-Address="{ip_chilli}"\' '
                f'| radclient -c 1 -n 3 -r 3 -t 3 -x 127.0.0.1:3799 disconnect testing123 2>&1'
            )

            # Eksekusi perintah radclient
            disconnect_result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Kirim pesan balasan setelah berhasil memutuskan pengguna
            if disconnect_result.returncode == 0:
                message = f"Pengguna '{username}' berhasil diputuskan."
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
                await update.message.reply_text(message)
            
            else:
                message = f"Gagal memutuskan pengguna '{username}': {disconnect_result.stderr}"
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
                await update.message.reply_text(message)
            
        except subprocess.CalledProcessError as e:
                message = f"Terjadi kesalahan saat mengakses database: {e.stderr}"
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
                await update.message.reply_text(message)
    else:
            sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
            await update.message.reply_text(
            "𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣."
        )
            
# Command /backup Untuk mengganti file sql (hanya untuk admin)
async def sql_backup(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            # Kirim pesan "Please wait"
            sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")

            # Mengambil dump database ke dalam variabel
            result = subprocess.run(
                ["mysqldump", "-u", DB_USER, "-p" + DB_PASS, DB_NAME],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

            # Menulis hasil dump ke file
            with open(FILE_PATH, "w") as file:
                file.write(result.stdout)

            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=sent_message.message_id
            )
            await update.message.reply_text("Database berhasil dibackup.")
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(FILE_PATH, "rb"))

        except subprocess.CalledProcessError as e:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=sent_message.message_id
            )
            await update.message.reply_text(
                f"Terjadi kesalahan saat mengganti database: {e.stderr}"
            )
    else:
        sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
        await update.message.reply_text(
            "𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣."
        )


# Command /replace Untuk mengganti file sql (hanya untuk admin)
async def sql_replace(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            # Kirim pesan "Please wait"
            sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")

            # Menghapus dan Membuat database radius
            subprocess.run(
                [
                    "mysql",
                    "-u",
                    DB_USER,
                    "-p" + DB_PASS,
                    "-e",
                    f"DROP DATABASE IF EXISTS {DB_NAME}; CREATE DATABASE {DB_NAME};",
                ],
                check=True,
            )

            # Mengisi tabel radius menggunakan file backup
            with open(FILE_PATH, "r") as file:
                subprocess.run(
                    ["mysql", "-u", DB_USER, "-p" + DB_PASS, DB_NAME],
                    stdin=file,
                    check=True,
                )

            # Menghapus pesan "Please wait" dan kirim pesan konfirmasi
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=sent_message.message_id
            )
            await update.message.reply_text(
                "Database radius berhasil diganti menggunakan file backup."
            )

        except subprocess.CalledProcessError as e:
            await update.message.reply_text(
                f"Terjadi kesalahan saat mengganti database: {e}"
            )
    else:
        sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
        await update.message.reply_text(
            "𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣."
        )

# Command /upload untuk mengupload file dari chat (hanya untuk admin)
async def start_upload(update: Update, context: CallbackContext):
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        args = context.args
        if args:
            context.user_data['file_upload_path'] = args[0]
        else:
            context.user_data['file_upload_path'] = DEFAULT_FILE_UPLOAD_PATH
        
        await update.message.reply_text(f"Kirimkan file yang akan diupload ke {context.user_data['file_upload_path']}.")
        return ASK_FOR_FILE
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")
        return ConversationHandler.END

async def handle_file_upload(update: Update, context: CallbackContext):
    try:
        if update.message.document:
            file = await context.bot.get_file(update.message.document.file_id)
            file_upload_path = context.user_data.get('file_upload_path', DEFAULT_FILE_UPLOAD_PATH)
            os.makedirs(file_upload_path, exist_ok=True)  # Ensure directory exists
            file_path = os.path.join(file_upload_path, update.message.document.file_name)
            await file.download_to_drive(file_path)

            await update.message.reply_text(f"File {update.message.document.file_name} berhasil diunggah ke {file_upload_path}")
        else:
            await update.message.reply_text("Harap kirimkan file yang akan diunggah.")
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan saat mengunggah file: {e}")
    return ConversationHandler.END

async def cancel_upload(update: Update, context: CallbackContext):
    await update.message.reply_text('Proses upload dibatalkan.')
    return ConversationHandler.END

# Command /cmd untuk custom cmd (hanya untuk admin)
async def custom_cmd(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            command = " ".join(context.args)
            
            if not command:
                await update.message.reply_text("Silakan berikan perintah untuk dieksekusi.")
                return

            sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
            
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout + result.stderr
            
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
            
            if output:
                await update.message.reply_text(f"{output}")
            else:
                await update.message.reply_text("Perintah dieksekusi tanpa keluaran.")

        except Exception as e:
            await update.message.reply_text(f"Terjadi kesalahan saat mengeksekusi perintah: {e}")
    else:
        sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")
        
# Command /topup untuk menambah saldo pengguna (hanya untuk admin)
async def add_balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    if is_admin(user_id):
        try:
            if len(context.args) != 2:
                await update.message.reply_text(
                    "Gunakan perintah : /topup <user_id> <jumlah>"
                )
                return

            target_user_id = int(context.args[0])
            amount = int(context.args[1])

            # Dapatkan informasi pengguna target
            try:
                target_user = await context.bot.get_chat(target_user_id)
                username = target_user.username if target_user.username else "none"
            except Exception as e:
                await update.message.reply_text(f"User ID {target_user_id} tidak valid.")
                return

            profiles = read_profiles()

            # Buat entri baru jika pengguna tidak ditemukan
            if str(target_user_id) not in profiles:
                profiles[str(target_user_id)] = {"balance": 0, "username": "none"}

            # Tambahkan saldo ke entri pengguna
            profiles[str(target_user_id)]["balance"] += amount

            # Update username di entri pengguna
            profiles[str(target_user_id)]["username"] = username
            write_profiles(profiles)

            # Kirim pesan konfirmasi ke admin
            await update.message.reply_text(
                f"💰 Saldo pengguna @{username} ({target_user_id}) berhasil ditambahkan sebesar Rp.{amount}."
            )

            # Kirim pesan ke pengguna yang saldonya ditambahkan
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ 
            TOPUP INFORMATION            
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ 
SALDO ANDA TELAH DITAMBAHKAN
OLEH ADMIN SEBESAR : Rp.{amount}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""",
                )
            except Exception as e:
                print(f"Gagal mengirim pesan ke pengguna ID {target_user_id}: {e}")

        except (IndexError, ValueError):
            await update.message.reply_text("Gunakan perintah : /topup <user_id> <jumlah>")
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")


# Command /saldo untuk mengecek saldo pengguna
async def check_balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    profiles = read_profiles()  # Pastikan ini memuat data profil yang benar
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)

    if is_admin(user_id):
        all_balances = """▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ 
              SALDO PENGGUNA
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ \n"""
        for profile_user_id, profile in profiles.items():
            username = profile.get("username", "Unknown")
            balance = profile.get("balance", 0)
            all_balances += f"""USERNAME : @{username}\nUSER ID : {profile_user_id}\nSALDO : Rp.{balance}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"""
        await update.message.reply_text(all_balances)
    else:
        # Dapatkan username dan saldo untuk pengguna yang bukan admin
        user_profile = profiles.get(str(user_id), {})
        username = update.effective_user.username
        balance = user_profile.get("balance", 0)

        await update.message.reply_text(
            f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ 
         BALANCE INFORMATION            
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ 
USERNAME  : @{username}
USER ID         : {user_id}
SISA SALDO : Rp.{balance}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
        )
        
# Fungsi untuk mendapatkan koneksi ke database MySQL
def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
    )

# Fungsi untuk memilih menu voucher
async def voucher(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    profiles = read_profiles()
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)

    if is_admin(user_id):
        keyboard = [[InlineKeyboardButton("GENERATE", callback_data='generate_voucher')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                  BATCH ADD USER
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""", reply_markup=reply_markup)
        return PILIH_TINDAKAN
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")

# Fungsi untuk memilih jumlah voucher
async def choose_quantity(update: Update, context: CallbackContext):
    query = update.callback_query
    reply_markup = quantity_keyboard_markup
    await query.message.edit_text("""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
 PILIH JUMLAH YANG AKAN DICETAK 
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""", reply_markup=reply_markup)
    return PILIH_JUMLAH

# Fungsi untuk memilih durasi voucher
async def choose_durasi(update: Update, context: CallbackContext):
    query = update.callback_query
    reply_markup = duration_keyboard_markup
    await query.message.edit_text("""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
PILIH DURASI DAN HARGA VOUCHER
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""", reply_markup=reply_markup)
    return PILIH_DURASI

async def create_voucher(update: Update, context: CallbackContext):
    query = update.callback_query
    # Memuat data dari file JSON
    duration_data = load_duration_data('durations.json')
    # Mengakses data
    duration_mapping = duration_data["duration_mapping"]
    duration_names = duration_data["duration_names"]
    duration_price = duration_data["duration_price"]
    
    
    duration_code = query.data
    if duration_code in duration_mapping:
        amount = duration_mapping[duration_code]
        duration_name = duration_names[duration_code]
        price_info = duration_price[duration_code]
        
        # Ambil jumlah dari context.user_data
        quantity = context.user_data.get('quantity', 1)

        all_numbers = []
        all_urls = []

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            random_string = generate_random_string()
            batch_name = f"{random_string}"
            batch_description = f"{price_info}"

            cursor.execute(
                "INSERT INTO batch_history (batch_name, batch_description, hotspot_id, batch_status, creationdate, creationby) VALUES (%s, %s, %s, %s, %s, %s)",
                (batch_name, batch_description, '1', 'Pending', timestamp, 'administrator'),
            )
            
            conn.commit()

            cursor.execute("SELECT id FROM batch_history WHERE batch_name = %s", (batch_name,))
            result = cursor.fetchone()
            if result:
                batch_id = result[0] 
            else:
                raise ValueError("Batch not found")

            for _ in range(quantity):
                number = "".join(random.choices(string.digits, k=6))  # Generate random 6 digit username
                all_numbers.append(number)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute(
                    "INSERT INTO radcheck (username, attribute, op, value) VALUES (%s, %s, %s, %s)",
                    (number, 'Auth-Type', ':=', 'Accept'),
                )
                cursor.execute(
                    "INSERT INTO radusergroup (username, groupname, priority) VALUES (%s, %s, %s)",
                    (number, duration_name, '0'),
                )
                cursor.execute("INSERT INTO userinfo (username, firstname, lastname, email, department, company, workphone, homephone, mobilephone, address, city, state, country, zip, notes, changeuserinfo, portalloginpassword, creationdate, creationby) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                    (number, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '0', '', now, 'administrator'),
                )
                cursor.execute(
                    "INSERT INTO userbillinfo (username, planName, contactperson, company, email, phone, address, city, state, country, zip, paymentmethod, cash, creditcardname, creditcardnumber, creditcardverification, creditcardtype, creditcardexp, notes, changeuserbillinfo, lead, coupon, ordertaker, billstatus, postalinvoice, faxinvoice, emailinvoice, batch_id, creationdate, creationby) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (number, price_info, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '0', '', '', '', '', '', '', '', batch_id, now, 'administrator'),
                )

            conn.commit()
        except Exception as e:
            await query.message.reply_text(f"Terjadi kesalahan: {str(e)}")
            return ConversationHandler.END
        finally:
            cursor.close()
            conn.close()

        # Membuat link dengan semua username
        accounts_str = '||'.join([f"{num},Accept" for num in all_numbers])
        link = f"http://{ip_lan}/daloradius/include/common/printTickets.php?type=batch&plan={price_info}&accounts=Username,Password||{accounts_str}"

        # Membuat pesan konfirmasi dengan semua username
        numbers_list = ', '.join(all_numbers)
        confirmation_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
              BATCH INFORMATION
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
BATCH NAME  :  {batch_name}
GROUP NAME : {duration_name}
PLANS  NAME : {price_info}
QUANTITY : {quantity}
STATUS : SUCCESS
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""

        # Menghapus keyboard
        await query.message.delete()

        # Membuat tombol dengan link
        keyboard = [
            [InlineKeyboardButton("Print Ticket", url=link)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Mengirim tombol dengan link
        await query.message.reply_text(confirmation_message, reply_markup=reply_markup)

        return ConversationHandler.END

    await query.answer()
    return PILIH_DURASI

# Menangani callback query dari admin
async def handle_admin_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    
    if data.startswith("generate_voucher"):
        return await choose_quantity(update, context)
    
    if data.startswith("quantity_"):
        quantity = int(data.split("_")[1])
        context.user_data['quantity'] = quantity
        return await choose_durasi(update, context)
    
    return await create_voucher(update, context)


# Fungsi untuk menampilkan pilihan durasi voucher
async def choose_duration(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(
        query.from_user.id
    )  # Mengubah user_id menjadi string untuk pencocokan di JSON

    # Baca data profil dari file JSON
    profiles = read_profiles()
    user_profile = profiles.get(user_id, {"balance": 0})
    user_balance = user_profile.get("balance", 0)

    if user_balance < 1000:
        reply_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                     INFORMATION
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
    SALDO ANDA TIDAK MENCUKUPI
   UNTUK MEMBELI KODE VOUCHER 
  SILAHKAN ISI ULANG SALDO ANDA.
"""
        keyboard = [[InlineKeyboardButton("TOPUP SALDO", callback_data="start_topup")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(reply_message, reply_markup=reply_markup)
        return  # Keluar dari fungsi jika saldo tidak mencukupi

    reply_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
            VOUCHER INFORMATION
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
  SILAHKAN PILIH HARGA VOUCHER
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
    reply_markup = duration_keyboard_markup
    await query.message.edit_text(reply_message, reply_markup=reply_markup)
    return CHOOSE_DURATION

async def send_login_link(query, code):
    login_url = f"http://{ip_chilli}:3990/login?username={code}&password=Accept"

    # Membuat tombol dengan link
    login_button = InlineKeyboardButton(text="Login", url=login_url)
    keyboard = [[login_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Mengedit pesan yang ada untuk hanya menampilkan keyboard
    await query.message.edit_reply_markup(reply_markup=reply_markup)


async def handle_duration_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    duration_data = load_duration_data('durations.json')
    duration_mapping = duration_data["duration_mapping"]
    duration_names = duration_data["duration_names"]
    duration_price = duration_data["duration_price"]

    duration_code = query.data
    if duration_code in duration_mapping:
        amount = duration_mapping[duration_code]
        duration_name = duration_names[duration_code]
        price_info = duration_price[duration_code]
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        profiles = read_profiles()
        balance = profiles.get(user_id, {}).get("balance", 0)

        if balance < amount:
            reply_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                     INFORMATION
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
    SALDO ANDA TIDAK MENCUKUPI
   UNTUK MEMBELI KODE VOUCHER 
  SILAHKAN ISI ULANG SALDO ANDA.
"""
            keyboard = [
                [InlineKeyboardButton("MENU", callback_data="send_services_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(reply_message, reply_markup=reply_markup)
            await query.answer()
            return

        # Generate kode angka acak 6 digit
        code = "".join(random.choices(string.digits, k=6))

        # Kurangi saldo user
        profiles[user_id]["balance"] -= amount
        updated_balance = profiles[user_id]["balance"]
        write_profiles(profiles)

        # Menjawab query dari pengguna
        await query.answer()

        # Mengedit pesan yang ada dengan informasi voucher
        await query.message.edit_text(
            f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
          VOUCHER INFORMATION
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
KODE LOGIN : {code}
PAKET : {duration_name}
HARGA : Rp.{amount}
SISA SALDO : Rp.{updated_balance}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""")

        # Membuat link dengan semua username
        await send_login_link(update.callback_query, code)
        
        # Kirim notifikasi ke admin
        admin_message = f'🔑 Pengguna @{username} ({user_id}) membeli kode {code} durasi {duration_name} pada {datetime.now().strftime("%d-%m-%Y %H:%M")} WIB.'
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(admin_id, admin_message)
            
        # Menyimpan kode ke database Radius
        try:
            connection = get_db_connection()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO radcheck (username, attribute, op, value) VALUES (%s, %s, %s, %s)",
                    (code, "Auth-Type", ":=", "Accept"),
                )
                cursor.execute(
                    "INSERT INTO radusergroup (username, groupname, priority) VALUES (%s, %s, %s)",
                    (code, duration_name, "0"),
                )
                cursor.execute("INSERT INTO userinfo (username, firstname, lastname, email, department, company, workphone, homephone, mobilephone, address, city, state, country, zip, notes, changeuserinfo, portalloginpassword, creationdate, creationby) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                    (code, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '0', '', now, 'administrator'),
                )
                cursor.execute(
                    "INSERT INTO userbillinfo (username, planName, contactperson, company, email, phone, address, city, state, country, zip, paymentmethod, cash, creditcardname, creditcardnumber, creditcardverification, creditcardtype, creditcardexp, notes, changeuserbillinfo, lead, coupon, ordertaker, billstatus, nextinvoicedue, billdue, postalinvoice, faxinvoice, emailinvoice, creationdate, creationby) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (code, price_info, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '0', '', '', '', '', '0', '0', '', '', '', now, 'administrator'),
                )
            connection.commit()
        finally:
            connection.close()

        return ConversationHandler.END

    # Jika pilihan durasi tidak valid, restart bot
    await query.answer()
    await send_services_menu(update, context)
    return CHOOSE_DURATION


# Fungsi untuk memulai proses mendapatkan kode
async def get_code(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.delete()

    return CHOOSE_DURATION


# Functions for handling various commands and callbacks
async def start_topup(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("MASUKKAN JUMLAH TOPUP, MINIMAL 10.000")
    context.user_data['topup_errors'] = 0  # Initialize error count
    return TOPUP_AMOUNT

async def handle_topup_amount(update: Update, context: CallbackContext):
    user = update.message.from_user
    amount_text = update.message.text.replace(".", "")
    error_count = context.user_data.get('topup_errors', 0)

    if amount_text.isdigit():
        amount = int(amount_text)
        if 10000 <= amount <= 100000:
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

            # Send notification to admins with confirmation buttons
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Terima", callback_data=f"topup_accept_{user.id}_{amount}"
                    )
                ,
                
                    InlineKeyboardButton(
                        "Tolak", callback_data=f"topup_reject_{user.id}_{amount}"
                    )
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🚨 Pengguna @{user.username} (`{user.id}`) ingin topup dengan jumlah Rp.`{amount}` pada {timestamp}.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup,
                )
                
            topup_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                 TOPUP INFORMATION
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
LAKUKAN PEMBAYARAN KE NOMOR:

* DANA : 0853-7268-7484
* OVO    : 0853-7268-7484
* SPAY  : 0853-7268-7484

JIKA SUDAH MELAKUKAN PEMBAYARAN KIRIMKAN BUKTI TRANSFER KE ADMIN : @Maizil41

NOTE *LAKUKAN PEMBAYARAN DALAM 1JAM APABILA LEBIH DARI 1JAM TRANSAKSI DIANGGAP BATAL
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
USERNAME : @{user.username}
ID TELEGRAM : {user.id}
JUMLAH TRANSFER: Rp.{amount}
STATUS : PENDING
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
            # Tombol untuk mengirim bukti
            bukti = [[InlineKeyboardButton("KIRIM BUKTI", url="https://t.me/Maizil41")]]
            reply_markup = InlineKeyboardMarkup(bukti)

            # Kirim pesan dengan tombol
            await update.message.reply_text(
                topup_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN,  # Optional, untuk format pesan markdown
            )
            return ConversationHandler.END
        else:
            error_count += 1
            context.user_data['topup_errors'] = error_count

            if error_count >= MAX_ERRORS:
                await update.message.reply_text("ANDA TERLALU SERING MEMASUKKAN JUMLAH YANG TIDAK VALID, TOPUP DIBATALKAN.")
                return ConversationHandler.END
            else:
                await update.message.reply_text(
                    f"MINIMAL TOP-UP : 10.000\nMAKSIMAL TOP-UP : 100.000"
                )
                return TOPUP_AMOUNT
    else:
        error_count += 1
        context.user_data['topup_errors'] = error_count

        if error_count >= MAX_ERRORS:
            await update.message.reply_text("ANDA TERLALU SERING MEMASUKKAN JUMLAH YANG TIDAK VALID, TOPUP DIBATALKAN.")
            return ConversationHandler.END
        else:
            await update.message.reply_text(f"MASUKKAN JUMLAH YANG VALID.")
            return TOPUP_AMOUNT

async def handle_topup_response(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    # Debugging line to print the received callback data
    print(f"Received callback data: {data}")

    # Split data based on underscores
    parts = data.split("_")

    if len(parts) == 4:
        action, topup_action, user_id_str, amount_str = parts

        try:
            # Convert user_id and amount from strings to integers
            user_id = int(user_id_str)
            amount = int(amount_str)

            # Determine status based on the action
            status = (
                "Diterima"
                if action == "topup" and topup_action == "accept"
                else "Ditolak"
            )

            # Fetch user details
            chat_member = await context.bot.get_chat_member(
                chat_id=user_id, user_id=user_id
            )
            user = chat_member.user

            if action == "topup" and topup_action == "accept":
                # Process the topup
                profiles = read_profiles()

                # Create a new entry if user not found
                if str(user_id) not in profiles:
                    profiles[str(user_id)] = {"balance": 0, "username": "none"}

                # Add balance to the user entry
                profiles[str(user_id)]["balance"] += amount

                # Get target user info
                try:
                    target_user = await context.bot.get_chat(user_id)
                    username = target_user.username if target_user.username else "none"
                except Exception as e:
                    username = "none"
                    print(f"Gagal mendapatkan username untuk ID {user_id}: {e}")

                # Update username in the user entry
                profiles[str(user_id)]["username"] = username
                write_profiles(profiles)

                # Notify admin
                await query.edit_message_text(
                    f"💰Permintaan topup Rp.{amount} dari (@{user.username} / {user_id}) telah disetujui."
                )

                # Send success message to user
                success_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                 TOPUP INFORMATION
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
USERNAME : @{user.username}
ID TELEGRAM : {user_id}
JUMLAH TRANSFER: Rp.{amount}
STATUS : SUCCESS
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""

                # Kirim pesan notifikasi kepada pengguna
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=success_message,
                        parse_mode=ParseMode.MARKDOWN,  # Optional, untuk format markdown
                    )
                except Exception as e:
                    print(f"Gagal mengirim pesan ke pengguna ID {user_id}: {e}")

            else:

                # Send success message to user
                failed_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                 TOPUP INFORMATION
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
USERNAME : @{user.username}
ID TELEGRAM : {user_id}
JUMLAH TRANSFER: Rp.{amount}
STATUS : GAGAL
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""

                # Notify admin
                await query.edit_message_text(
                    f"💰Permintaan topup Rp.{amount} dari (@{user.username} / {user_id}) tidak disetujui."
                )

                # Kirim pesan notifikasi kepada pengguna
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=failed_message,
                        parse_mode=ParseMode.MARKDOWN,  # Optional, untuk format markdown
                    )
                except Exception as e:
                    print(f"Gagal mengirim pesan ke pengguna ID {user_id}: {e}")

        except ValueError:
            await query.answer(
                text="Data callback tidak valid. Gagal mengonversi ID pengguna atau jumlah."
            )
            print("ValueError: Data callback tidak dapat dikonversi ke integer.")

        except TimedOut:
            await query.answer(
                text="Permintaan Anda mengalami timeout. Silakan coba lagi nanti."
            )
            print("TimedOut: Permintaan ke API Telegram mengalami timeout.")

        except Exception as e:
            await context.bot.send_message(
                chat_id=ADMIN_IDS[0],  # Assuming at least one admin ID is available
                text=f"Terjadi kesalahan saat memproses topup: {str(e)}",
            )
            print(f"Exception: {str(e)}")

    else:
        await query.answer(text="Data callback tidak valid. Format data tidak sesuai.")
        print("Error: Data callback tidak sesuai format yang diharapkan.")

    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Proses topup dibatalkan.")
    return ConversationHandler.END


async def poll_log_changes(context: CallbackContext):
    global LAST_POSITION

    try:
        modified_time = datetime.fromtimestamp(os.path.getmtime(LOG_FILE_PATH))

        with open(LOG_FILE_PATH, "r") as file:
            file.seek(LAST_POSITION)

            new_logs = file.readlines()

            LAST_POSITION = file.tell()
            save_last_position(LAST_POSITION)

        login_ok_logs = [log for log in new_logs if "Login OK" in log]

        if login_ok_logs:
            selected_log = login_ok_logs[0]

            match = re.search(
                r"(\w+ \w+ \d+ \d+:\d+:\d+ \d+).*Login OK: \[([\w\d]+).*] \(from client .* cli ([\w-]+)\)",
                selected_log,
            )
            if match:
                log_timestamp = match.group(1)
                code = match.group(2)
                mac = match.group(3)
                log_time = datetime.strptime(log_timestamp, "%a %b %d %H:%M:%S %Y")
                formatted_time = log_time.strftime("%d-%m-%Y %H:%M WIB")
                formatted_log = f"🔑 Pengguna {mac} Login menggunakan kode {code} pada {formatted_time}"
                for admin_id in ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id, text=f"{formatted_log}"
                        )
                    except TimedOut:
                        continue

    except FileNotFoundError:
        pass

def clear_log_file():
    global LAST_POSITION

    try:
        with open(LOG_FILE_PATH, "w") as file:
            pass

        LAST_POSITION = 0
        save_last_position(LAST_POSITION)
    except FileNotFoundError:
        pass


def main():
    clear_log_file()
    application = Application.builder().token(TOKEN).build()

    # Handler untuk berbagai command dan callback
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("topup", add_balance))
    application.add_handler(CommandHandler("menu", show_menu))
    application.add_handler(CommandHandler("saldo", check_balance))
    application.add_handler(CommandHandler("replace", sql_replace))
    application.add_handler(CommandHandler("backup", sql_backup))
    application.add_handler(CommandHandler("online", online))
    application.add_handler(CommandHandler("list", alluser))
    application.add_handler(CommandHandler("hapus", delete_user))
    application.add_handler(CommandHandler("kick", disconnect_user))
    application.add_handler(CommandHandler("cmd", custom_cmd))
    application.add_handler(
        CallbackQueryHandler(
            handle_topup_response, pattern=r"^topup_(accept|reject)_(\d+)_(\d+)$"
        )
    )
    
    voucher_handler = ConversationHandler(
        entry_points=[CommandHandler('generate', voucher)],
        states={
            PILIH_TINDAKAN: [CallbackQueryHandler(handle_admin_choice)],
            PILIH_JUMLAH: [CallbackQueryHandler(handle_admin_choice)],
            PILIH_DURASI: [CallbackQueryHandler(handle_admin_choice)],
        },
        fallbacks=[],
    )

    
    upload_handler = ConversationHandler(
        entry_points=[CommandHandler('upload', start_upload)],
        states={
            ASK_FOR_FILE: [MessageHandler(filters.Document.ALL, handle_file_upload)]
        },
        fallbacks=[CommandHandler('cancel', cancel_upload)]
    )


    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(choose_duration, pattern="get_code")],
        states={CHOOSE_DURATION: [CallbackQueryHandler(handle_duration_choice)]},
        fallbacks=[],
        per_message=True
    )

    topup_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_topup, pattern="start_topup")],
        states={
            TOPUP_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topup_amount),
                MessageHandler(filters.COMMAND, cancel)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )
    
    application.add_handler(voucher_handler)
    application.add_handler(upload_handler)
    application.add_handler(conv_handler)
    application.add_handler(topup_handler)

    job_queue = application.job_queue
    job_queue.run_repeating(poll_log_changes, interval=POLL_INTERVAL, first=0)

    application.run_polling()

if __name__ == "__main__":
    main()
    
     # ⓒ  2024 - Mutiara-Wrt by Maizil https://t.me/maizil41
