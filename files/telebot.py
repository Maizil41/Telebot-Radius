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
from pymysql.err import MySQLError
from typing import Dict
from datetime import datetime
from telegram.error import TimedOut
from pymysql.cursors import DictCursor
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, Updater, JobQueue, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler

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
DEFAULT_FILE_UPLOAD_PATH  = "/root/"
QUANTITY_KEYBOARD = "/root/Telebot-Radius/files/quantity_keyboard.json"

POLL_INTERVAL = 5
MAX_ERRORS = 3

# Daftar ID admin yang diizinkan
ADMIN_IDS = set(USER_IDS)

# State untuk conversation handler
CHOOSE_DURATION, TOPUP_AMOUNT, LAST_POSITION, ASK_FOR_FILE, PILIH_TINDAKAN, PILIH_JUMLAH, PILIH_DURASI, PAGE_SELECTION, CHECK_FILE, CONFIRM_REPLACE, BACKUP_CONFIRMATION = range(11)

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
                    COMMAND RADIUS 

1. /backup - Backup database
2. /replace - Ganti database
3. /list - List voucher 
4. /online - List online user
5. /kick - Disconnect user 
6. /hapus - Hapus voucher
8. /generate - Generate voucher
9. /listbatch - List batch user
10. /delbatch - Hapus batch user
11. /listplan - List plan
12. /addplan - Membuat plan dan grup
13. /delplan - Menghapus plan dan grup
14. /pendapatan - Kalkulasi pendapatan
15. /Kuota - Penggunaan kuota client
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                  COMMAND OPENWRT

1. /upload <filepath> - Unggah file
2. /cmd <cmd> - Custom cmd
3. /restart - Restart Bot
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
        button = InlineKeyboardButton(text="Dukung Owner", url="https://saweria.co/MutiaraWrt")
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
                    COMMAND RADIUS 

1. /backup - Backup database
2. /replace - Ganti database
3. /list - List voucher 
4. /online - List online user
5. /kick - Disconnect user 
6. /hapus - Hapus voucher
8. /generate - Generate voucher
9. /listbatch - List batch user
10. /delbatch - Hapus batch user
11. /listplan - List plan
12. /addplan - Membuat plan dan grup
13. /delplan - Menghapus plan dan grup
14. /pendapatan - Kalkulasi pendapatan
15. /Kuota - Penggunaan kuota client
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                  COMMAND OPENWRT

1. /upload <filepath> - Unggah file
2. /cmd <cmd> - Custom cmd
3. /restart - Restart Bot
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
        button = InlineKeyboardButton(text="Dukung Owner", url="https://saweria.co/MutiaraWrt")
        keyboard = InlineKeyboardMarkup([[button]])
        await update.message.reply_text(f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ {commands}", reply_markup=keyboard)
    else:
        welcome_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
    MUTIARA-WRT TELEBOT-RADIUS
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

async def get_pendapatan() -> Dict[str, Dict[str, str]]:
    try:
        with pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME
        ) as conn:
            with conn.cursor() as cursor:
                # Query total pendapatan per hari
                query_total_hari = """
                SELECT 
                    tanggal,
                    SUM(total_pendapatan) AS total_pendapatan
                FROM (
                    SELECT 
                        DATE(a.acctstoptime) AS tanggal,
                        r.username,
                        MAX(p.planCost) AS total_pendapatan
                    FROM radcheck r
                    JOIN radacct a ON r.username = a.username
                    JOIN userbillinfo u ON a.username = u.username
                    JOIN billing_plans p ON u.planName = p.planName
                    WHERE a.acctstoptime IS NOT NULL
                    GROUP BY tanggal, r.username
                ) AS daily_totals
                GROUP BY tanggal
                ORDER BY tanggal;
                """
                cursor.execute(query_total_hari)
                results_total_hari = cursor.fetchall()

                # Query total pendapatan per bulan
                query_total_bulan = """
                SELECT 
                    bulan,
                    SUM(total_pendapatan) AS total_pendapatan
                FROM (
                    SELECT 
                        DATE_FORMAT(a.acctstoptime, '%Y-%m') AS bulan,
                        r.username,
                        MAX(p.planCost) AS total_pendapatan
                    FROM radcheck r
                    JOIN radacct a ON r.username = a.username
                    JOIN userbillinfo u ON a.username = u.username
                    JOIN billing_plans p ON u.planName = p.planName
                    WHERE a.acctstoptime IS NOT NULL
                    GROUP BY bulan, r.username
                ) AS monthly_totals
                GROUP BY bulan
                ORDER BY bulan;
                """
                cursor.execute(query_total_bulan)
                results_total_bulan = cursor.fetchall()

                # Query total pendapatan per tahun
                query_total_tahun = """
                SELECT 
                    tahun,
                    SUM(total_pendapatan) AS total_pendapatan
                FROM (
                    SELECT 
                        DATE_FORMAT(a.acctstoptime, '%Y') AS tahun,
                        r.username,
                        MAX(p.planCost) AS total_pendapatan
                    FROM radcheck r
                    JOIN radacct a ON r.username = a.username
                    JOIN userbillinfo u ON a.username = u.username
                    JOIN billing_plans p ON u.planName = p.planName
                    WHERE a.acctstoptime IS NOT NULL
                    GROUP BY tahun, r.username
                ) AS yearly_totals
                GROUP BY tahun
                ORDER BY tahun;
                """
                cursor.execute(query_total_tahun)
                results_total_tahun = cursor.fetchall()

                # Query estimasi pendapatan harian untuk hari ini
                query_estimasi_pendapatan_hari = """
                SELECT 
                    tanggal,
                    SUM(planCost) AS total_estimasi_pendapatan
                FROM (
                    SELECT 
                        DATE(ub.creationDate) AS tanggal,
                        r.username,
                        MAX(p.planCost) AS planCost
                    FROM radcheck r
                    JOIN userbillinfo ub ON r.username = ub.username
                    JOIN billing_plans p ON ub.planName = p.planName
                    WHERE DATE(ub.creationDate) = CURDATE() -- Hanya untuk hari ini
                    GROUP BY tanggal, r.username
                ) AS daily_estimations
                GROUP BY tanggal
                ORDER BY tanggal;
                """
                cursor.execute(query_estimasi_pendapatan_hari)
                results_estimasi_pendapatan_hari = cursor.fetchall()

                # Query estimasi pendapatan bulanan untuk bulan ini
                query_estimasi_pendapatan_bulan = """
                SELECT 
                    bulan,
                    SUM(planCost) AS total_estimasi_pendapatan
                FROM (
                    SELECT 
                        DATE_FORMAT(ub.creationDate, '%Y-%m') AS bulan,
                        r.username,
                        MAX(p.planCost) AS planCost
                    FROM radcheck r
                    JOIN userbillinfo ub ON r.username = ub.username
                    JOIN billing_plans p ON ub.planName = p.planName
                    WHERE DATE_FORMAT(ub.creationDate, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m') -- Bulan ini
                    GROUP BY bulan, r.username
                ) AS monthly_estimations
                GROUP BY bulan
                ORDER BY bulan;
                """
                cursor.execute(query_estimasi_pendapatan_bulan)
                results_estimasi_pendapatan_bulan = cursor.fetchall()

                # Query estimasi pendapatan tahunan untuk tahun ini
                query_estimasi_pendapatan_tahun = """
                SELECT 
                    tahun,
                    SUM(planCost) AS total_estimasi_pendapatan
                FROM (
                    SELECT 
                        DATE_FORMAT(ub.creationDate, '%Y') AS tahun,
                        r.username,
                        MAX(p.planCost) AS planCost
                    FROM radcheck r
                    JOIN userbillinfo ub ON r.username = ub.username
                    JOIN billing_plans p ON ub.planName = p.planName
                    WHERE DATE_FORMAT(ub.creationDate, '%Y') = DATE_FORMAT(CURDATE(), '%Y') -- Tahun ini
                    GROUP BY tahun, r.username
                ) AS yearly_estimations
                GROUP BY tahun
                ORDER BY tahun;
                """
                cursor.execute(query_estimasi_pendapatan_tahun)
                results_estimasi_pendapatan_tahun = cursor.fetchall()

        # Format results as a dictionary
        def format_results(results):
            formatted = {}
            for row in results:
                amount = row[1]
                formatted_amount = f'Rp {amount:,.0f}'  # Menghilangkan desimal
                formatted[row[0]] = formatted_amount
            return formatted if results else {}

        return {
            'total_pendapatan_hari': format_results(results_total_hari),
            'total_pendapatan_bulan': format_results(results_total_bulan),
            'total_pendapatan_tahun': format_results(results_total_tahun),
            'estimasi_pendapatan_hari': format_results(results_estimasi_pendapatan_hari),
            'estimasi_pendapatan_bulan': format_results(results_estimasi_pendapatan_bulan),
            'estimasi_pendapatan_tahun': format_results(results_estimasi_pendapatan_tahun),
        }
    except MySQLError as e:
        print(f"Error fetching data: {e}")
        return {
            'total_pendapatan_hari': {},
            'total_pendapatan_bulan': {},
            'total_pendapatan_tahun': {},
            'estimasi_pendapatan_hari': {},
            'estimasi_pendapatan_bulan': {},
            'estimasi_pendapatan_tahun': {},
        }

async def pendapatan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_pendapatan()
    
    if not any(data.values()):
        await update.message.reply_text('Tidak ada data pendapatan.')
        return

    def format_output(title: str, data: Dict[str, str]) -> str:
        separator = '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬'
        indent = ' ' * 18  # Adjust the number of spaces for indent
        content = '\n'.join([f'{key}: {value}' for key, value in data.items()])
        return f'{separator}\n{indent}{title}:\n{separator}\n{content}\n{separator}'

    response = (
        f"{format_output('PENDAPATAN HARIAN', data['total_pendapatan_hari'])}\n\n"
        f"{format_output('PENDAPATAN BULANAN', data['total_pendapatan_bulan'])}\n\n"
        f"{format_output('PENDAPATAN TAHUNAN', data['total_pendapatan_tahun'])}\n\n"
        f"{format_output('ESTIMASI HARI INI', data['estimasi_pendapatan_hari'])}\n\n"
        f"{format_output('ESTIMASI BULAN INI', data['estimasi_pendapatan_bulan'])}\n\n"
        f"{format_output('ESTIMASI TAHUN INI', data['estimasi_pendapatan_tahun'])}"
    )

    await update.message.reply_text(response)

def convert_bytes(byte_count: int) -> str:
    """Convert byte count to a human-readable format (KB, MB, GB)."""
    if byte_count < 1024:
        return f'{byte_count} bytes'
    elif byte_count < 1024 ** 2:
        return f'{byte_count / 1024:.2f} KB'
    elif byte_count < 1024 ** 3:
        return f'{byte_count / (1024 ** 2):.2f} MB'
    else:
        return f'{byte_count / (1024 ** 3):.2f} GB'

async def get_usage() -> Dict[str, Dict[str, str]]:
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME
        )
        with connection:
            with connection.cursor() as cursor:
                # Query penggunaan kuota per hari
                query_per_hari = """
                SELECT 
                    tanggal,
                    SUM(total_kuota) AS total_kuota
                FROM (
                    SELECT 
                        DATE(acctstarttime) AS tanggal,
                        r.username,
                        SUM(acctinputoctets + acctoutputoctets) AS total_kuota
                    FROM radcheck r
                    JOIN radacct a ON r.username = a.username
                    WHERE a.acctstarttime IS NOT NULL
                    GROUP BY tanggal, r.username
                ) AS daily_totals
                GROUP BY tanggal
                ORDER BY tanggal;
                """
                cursor.execute(query_per_hari)
                results_per_hari = cursor.fetchall()

                # Query penggunaan kuota per bulan
                query_per_bulan = """
                SELECT 
                    bulan,
                    SUM(total_kuota) AS total_kuota
                FROM (
                    SELECT 
                        DATE_FORMAT(acctstarttime, '%Y-%m') AS bulan,
                        r.username,
                        SUM(acctinputoctets + acctoutputoctets) AS total_kuota
                    FROM radcheck r
                    JOIN radacct a ON r.username = a.username
                    WHERE a.acctstarttime IS NOT NULL
                    GROUP BY bulan, r.username
                ) AS monthly_totals
                GROUP BY bulan
                ORDER BY bulan;
                """
                cursor.execute(query_per_bulan)
                results_per_bulan = cursor.fetchall()

                # Query penggunaan kuota per tahun
                query_per_tahun = """
                SELECT 
                    tahun,
                    SUM(total_kuota) AS total_kuota
                FROM (
                    SELECT 
                        DATE_FORMAT(acctstarttime, '%Y') AS tahun,
                        r.username,
                        SUM(acctinputoctets + acctoutputoctets) AS total_kuota
                    FROM radcheck r
                    JOIN radacct a ON r.username = a.username
                    WHERE a.acctstarttime IS NOT NULL
                    GROUP BY tahun, r.username
                ) AS yearly_totals
                GROUP BY tahun
                ORDER BY tahun;
                """
                cursor.execute(query_per_tahun)
                results_per_tahun = cursor.fetchall()

        # Format results as a dictionary
        def format_results(results):
            formatted = {}
            for row in results:
                date = row[0]
                amount = row[1]
                formatted_amount = convert_bytes(amount)  # Konversi byte ke format yang lebih mudah dibaca
                formatted[f'* {date}'] = formatted_amount
            return formatted if results else {}

        return {
            'usage_per_hari': format_results(results_per_hari),
            'usage_per_bulan': format_results(results_per_bulan),
            'usage_per_tahun': format_results(results_per_tahun),
        }
    except MySQLError as e:
        print(f"Error fetching data: {e}")
        return {
            'usage_per_hari': {},
            'usage_per_bulan': {},
            'usage_per_tahun': {},
        }

async def usage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = await get_usage()
    
    if not any(data.values()):
        await update.message.reply_text('Tidak ada data penggunaan kuota.')
        return

    def format_output(title: str, data: Dict[str, str]) -> str:
        separator = '▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬'
        indent = ' ' * 8  # Adjust the number of spaces for indent
        content = '\n'.join([f'{key}: {value}' for key, value in data.items()])
        return f'{separator}\n{indent}{title}:\n{separator}\n{content}\n{separator}'

    response = (
        f"{format_output('PENGGUNAAN KUOTA HARIAN', data['usage_per_hari'])}\n\n"
        f"{format_output('PENGGUNAAN KUOTA BULANAN', data['usage_per_bulan'])}\n\n"
        f"{format_output('PENGGUNAAN KUOTA TAHUNAN', data['usage_per_tahun'])}"
    )

    await update.message.reply_text(response)

def split_message(message, max_length=4096):
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

def create_keyboard_list(batch_index, total_batches):
    keyboard = []
    
    # Create navigation buttons for list
    navigation_buttons = []
    if batch_index > 1:
        navigation_buttons.append(InlineKeyboardButton("⮜ PREV", callback_data='list_prev'))
    
    if batch_index < total_batches:
        navigation_buttons.append(InlineKeyboardButton("NEXT ⮞", callback_data='list_next'))
    
    if navigation_buttons:
        keyboard.append(navigation_buttons)
    
    # Add CLOSE button in a new row
    close_button = [InlineKeyboardButton("CLOSE", callback_data='list_close')]
    keyboard.append(close_button)
    
    return InlineKeyboardMarkup(keyboard)

def create_keyboard_online(batch_index, total_batches):
    keyboard = []
    
    # Create navigation buttons for online
    navigations_buttons = []
    if batch_index > 1:
        navigations_buttons.append(InlineKeyboardButton("⮜ PREV", callback_data='online_prev'))
    
    if batch_index < total_batches:
        navigations_buttons.append(InlineKeyboardButton("NEXT ⮞", callback_data='online_next'))
    
    if navigations_buttons:
        keyboard.append(navigations_buttons)
    
    # Add CLOSE button in a new row
    closes_button = [InlineKeyboardButton("CLOSE", callback_data='online_close')]
    keyboard.append(closes_button)
    
    return InlineKeyboardMarkup(keyboard)

async def handle_navigation_list(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    data = query.data
    chat_id = update.effective_chat.id

    if context.chat_data.get(f'{chat_id}_list_batches'):
        batch_index = context.chat_data.get(f'{chat_id}_list_batch_index', 1)
        message_batches = context.chat_data.get(f'{chat_id}_list_batches', [])
        total_batches = context.chat_data.get(f'{chat_id}_list_total_batches', 0)

        if data == 'list_next':
            if batch_index < total_batches:
                batch_index += 1
                context.chat_data[f'{chat_id}_list_batch_index'] = batch_index
                await query.edit_message_text(
                    text=message_batches[batch_index - 1],
                    reply_markup=create_keyboard_list(batch_index, total_batches)
                )

        elif data == 'list_prev':
            if batch_index > 1:
                batch_index -= 1
                context.chat_data[f'{chat_id}_list_batch_index'] = batch_index
                await query.edit_message_text(
                    text=message_batches[batch_index - 1],
                    reply_markup=create_keyboard_list(batch_index, total_batches)
                )

        elif data == 'list_close':
            await query.edit_message_text(
                text="𝙋𝙧𝙤𝙘𝙚𝙨𝙨 𝙘𝙡𝙤𝙨𝙚𝙙.",
                reply_markup=None
            )
            return ConversationHandler.END

    return PAGE_SELECTION

async def handle_navigation_online(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    data = query.data
    chat_id = update.effective_chat.id

    if context.chat_data.get(f'{chat_id}_online_batches'):
        batch_index = context.chat_data.get(f'{chat_id}_online_batch_index', 1)
        message_batches = context.chat_data.get(f'{chat_id}_online_batches', [])
        total_batches = context.chat_data.get(f'{chat_id}_online_total_batches', 0)

        if data == 'online_next':
            if batch_index < total_batches:
                batch_index += 1
                context.chat_data[f'{chat_id}_online_batch_index'] = batch_index
                await query.edit_message_text(
                    text=message_batches[batch_index - 1],
                    reply_markup=create_keyboard_online(batch_index, total_batches)
                )

        elif data == 'online_prev':
            if batch_index > 1:
                batch_index -= 1
                context.chat_data[f'{chat_id}_online_batch_index'] = batch_index
                await query.edit_message_text(
                    text=message_batches[batch_index - 1],
                    reply_markup=create_keyboard_online(batch_index, total_batches)
                )

        elif data == 'online_close':
            await query.edit_message_text(
                text="𝙋𝙧𝙤𝙘𝙚𝙨𝙨 𝙘𝙡𝙤𝙨𝙚𝙙.",
                reply_markup=None
            )
            return ConversationHandler.END

    return PAGE_SELECTION

async def alluser(update: Update, context: CallbackContext) -> int:
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
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

            output = result.stdout.strip()
            if output:
                lines = output.splitlines()
                data_lines = lines[1:]

                batch_size = 7
                message_batches = []
                current_batch = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
            LIST ALL USER (1/{len(data_lines) // batch_size + (1 if len(data_lines) % batch_size != 0 else 0)})
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""

                for index, line in enumerate(data_lines):
                    fields = line.split("\t")
                    current_batch += (f"""
USERNAME  : {fields[0]}
STATUS  :  {fields[1]}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""")

                    if (index + 1) % batch_size == 0:
                        message_batches.append(current_batch)
                        current_batch = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
            LIST ALL USER ({len(message_batches) + 1}/{len(data_lines) // batch_size + (1 if len(data_lines) % batch_size != 0 else 0)})
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""

                if current_batch.strip():
                    message_batches.append(current_batch)

                total_batches = len(message_batches)

                first_batch = message_batches[0]
                context.chat_data[f'{update.effective_chat.id}_list_batches'] = message_batches
                context.chat_data[f'{update.effective_chat.id}_list_batch_index'] = 1
                context.chat_data[f'{update.effective_chat.id}_list_total_batches'] = total_batches

                keyboard = create_keyboard_list(1, total_batches)
                await update.message.reply_text(
                    f"{first_batch}",
                    reply_markup=keyboard
                )

                return PAGE_SELECTION

            else:
                message = "𝙏𝙞𝙙𝙖𝙠 𝙖𝙙𝙖 𝙙𝙖𝙩𝙖 𝙥𝙚𝙣𝙜𝙜𝙪𝙣𝙖 𝙨𝙖𝙖𝙩 𝙞𝙣𝙞."
                await update.message.reply_text(message)

                return ConversationHandler.END

        except subprocess.CalledProcessError as e:

            await update.message.reply_text(
                f"Terjadi kesalahan saat mengakses database: {e.stderr}"
            )

            return ConversationHandler.END
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")

        return ConversationHandler.END

async def online(update: Update, context: CallbackContext) -> int:
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
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
                    "--default-character-set=utf8mb4",
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
                lines = output.splitlines()
                data_lines = lines[1:]

                batch_size = 4
                message_batches = []
                current_batch = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
               ONLINE USER (1/{len(data_lines) // batch_size + (1 if len(data_lines) % batch_size != 0 else 0)})
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""

                for index, line in enumerate(data_lines):
                    fields = line.split("\t")
                    current_batch += (f"""
USERNAME   :  {fields[0]}
MAC ADDR    :  {fields[3]}
IP ADDRESS  :  {fields[2]}
PAKET       :  {fields[4]}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""")

                    if (index + 1) % batch_size == 0:
                        message_batches.append(current_batch)
                        current_batch = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
               ONLINE USER ({len(message_batches) + 1}/{len(data_lines) // batch_size + (1 if len(data_lines) % batch_size != 0 else 0)})
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""

                if current_batch.strip():
                    message_batches.append(current_batch)

                total_batches = len(message_batches)

                first_batch = message_batches[0]
                context.chat_data[f'{update.effective_chat.id}_online_batches'] = message_batches
                context.chat_data[f'{update.effective_chat.id}_online_batch_index'] = 1
                context.chat_data[f'{update.effective_chat.id}_online_total_batches'] = total_batches

                keyboard = create_keyboard_online(1, total_batches)
                await update.message.reply_text(
                    f"{first_batch}",
                    reply_markup=keyboard
                )

                return PAGE_SELECTION

            else:
                message = "𝙏𝙞𝙙𝙖𝙠 𝙖𝙙𝙖 𝙙𝙖𝙩𝙖 𝙥𝙚𝙣𝙜𝙜𝙪𝙣𝙖 𝙨𝙖𝙖𝙩 𝙞𝙣𝙞. "
                await update.message.reply_text(message)

                return ConversationHandler.END

        except subprocess.CalledProcessError as e:

            await update.message.reply_text(
                f"Terjadi kesalahan saat mengakses database: {e.stderr}"
            )

            return ConversationHandler.END
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")

        return ConversationHandler.END

async def delete_user(update: Update, context: CallbackContext):
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            if context.args:
                username = context.args[0]
            else:
                message = f"Gunakan perintah : /hapus <username>."
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

            await update.message.reply_text(message)

        except subprocess.CalledProcessError as e:
            await update.message.reply_text(
                f"Terjadi kesalahan saat mengakses database: {e.stderr}"
            )
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")
        
def convert_time_to_seconds(time_str):
    if 'HARI' in time_str:
        hours = int(time_str.replace('HARI', ''))
        return hours * 3600
    elif 'MENIT' in time_str:
        minutes = int(time_str.replace('MENIT', ''))
        return minutes * 60
    elif 'JAM' in time_str:
        jam = int(time_str.replace('JAM', ''))
        return jam * 3600
    # Tambahkan konversi lainnya jika diperlukan
    else:
        raise ValueError("Format waktu tidak dikenali.")

def convert_bandwidth_to_bytes(bandwidth_str):
    if bandwidth_str[-1].upper() == 'K':
        return int(bandwidth_str[:-1]) * 1024
    elif bandwidth_str[-1].upper() == 'M':
        return int(bandwidth_str[:-1]) * 1024 * 1024
    elif bandwidth_str[-1].upper() == 'G':
        return int(bandwidth_str[:-1]) * 1024 * 1024 * 1024
    else:
        raise ValueError("Format bandwidth tidak valid. Gunakan K, M, atau G untuk ukuran.")

async def add_plan(update: Update, context: CallbackContext):
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            if len(context.args) >= 4:  # Memastikan ada setidaknya 4 argumen
                plan_name = " ".join(context.args[:-3])  # Gabungkan semua argumen kecuali 3 terakhir untuk plan_name
                plan_cost = context.args[-3]
                plan_timebank = convert_time_to_seconds(context.args[-2])  # Konversi waktu ke detik
                bandwidth = context.args[-1].split('/')  # Misal: "2M/1M" menjadi ['2M', '1M']
                max_down = convert_bandwidth_to_bytes(bandwidth[0])
                max_up = convert_bandwidth_to_bytes(bandwidth[1])
                max_all_session = plan_timebank  # Atur `Max-All-Session` sesuai dengan `plan_timebank`
            else:
                message = "Gunakan perintah: /addplan <plan_name> <plan_cost> <plan_timebank> <down/up>."
                await update.message.reply_text(message)
                return

            # Query untuk memasukkan data ke tabel billing_plans
            billing_plans_query = f"""
            INSERT INTO billing_plans (
                id, planName, planId, planType, planTimeBank, planTimeType, 
                planTimeRefillCost, planBandwidthUp, planBandwidthDown, 
                planTrafficTotal, planTrafficUp, planTrafficDown, 
                planTrafficRefillCost, planRecurring, planRecurringPeriod, 
                planRecurringBillingSchedule, planCost, planSetupCost, 
                planTax, planCurrency, planGroup, planActive, creationdate, 
                creationby, updatedate, updateby
            ) VALUES (
                NULL, '{plan_name}', '', 'Prepaid', '{plan_timebank}', 'Accumulative', 
                '', '{max_up}', '{max_down}', '', '', '', '', 'No', 'Never', 'Fixed', 
                '{plan_cost}', '', '', '', '', 'yes', NOW(), 
                'Administrator', NOW(), 'Administrator'
            )
            """

            # Query untuk memasukkan data ke tabel radgroupreply
            radgroupreply_query = f"""
            INSERT INTO radgroupreply (groupname, attribute, op, value) VALUES 
            ('{plan_name}', 'WISPr-Bandwidth-Max-Down', ':=', '{max_down}'), 
            ('{plan_name}', 'WISPr-Bandwidth-Max-Up', ':=', '{max_up}'), 
            ('{plan_name}', 'Acct-Interim-Interval', ':=', '60')
            """

            # Query untuk memasukkan data ke tabel radgroupcheck
            radgroupcheck_query = f"""
            INSERT INTO radgroupcheck (groupname, attribute, op, value) VALUES 
            ('{plan_name}', 'Max-All-Session', ':=', '{max_all_session}'), 
            ('{plan_name}', 'Simultaneous-Use', ':=', '1'), 
            ('{plan_name}', 'Auth-Type', ':=', 'Accept')
            """

            # Menjalankan semua query
            queries = [billing_plans_query, radgroupreply_query, radgroupcheck_query]
            for query in queries:
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

            message = f"Plan dan group '{plan_name}' berhasil ddibuat dengan harga '{plan_cost}' dan durasi '{context.args[-2]}' dan kecepatan '{max_down}'/'{max_up}')."
            await update.message.reply_text(message)

        except subprocess.CalledProcessError as e:
            await update.message.reply_text(
                f"Terjadi kesalahan saat mengakses database: {e.stderr}"
            )
        except ValueError as e:
            await update.message.reply_text(str(e))
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")

def time_to_seconds(time_str):
    time_str = time_str.upper()
    units = {'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    total_seconds = 0
    num = ''
    for char in time_str:
        if char.isdigit():
            num += char
        elif char in units:
            if num:
                total_seconds += int(num) * units[char]
                num = ''
    return total_seconds

def format_time(seconds):
    if not isinstance(seconds, int) or seconds < 0:
        return "Invalid time value"
    
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} hari")
    if hours > 0:
        parts.append(f"{hours} jam")
    if minutes > 0:
        parts.append(f"{minutes} menit")
    if seconds > 0 or not parts:  # Display seconds if it's zero and no other parts are there
        parts.append(f"{seconds} detik")
    
    return ' '.join(parts)

def format_bandwidth(bytes_value):
    if not isinstance(bytes_value, (int, float)):
        return "Invalid bandwidth value"
    
    if bytes_value >= 1073741824:  # GB
        return f"{bytes_value / 1073741824:.2f} G"
    elif bytes_value >= 1048576:  # MB
        return f"{bytes_value / 1048576:.2f} M"
    elif bytes_value >= 1024:  # KB
        return f"{bytes_value / 1024:.2f} K"
    else:  # B
        return f"{bytes_value} B"

def bandwidth_str_to_bytes(bandwidth_str):
    bandwidth_str = bandwidth_str.upper()
    units = {'K': 1024, 'M': 1048576, 'G': 1073741824}
    try:
        value, unit = bandwidth_str.split(' ')
        value = float(value)
        if unit in units:
            return int(value * units[unit])
        else:
            return int(value)
    except ValueError:
        return 0

async def list_plan(update: Update, context: CallbackContext):
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            select_query = "SELECT planName, planCost, planTimeBank, planBandwidthUp, planBandwidthDown FROM billing_plans"
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(select_query)
                plans = cursor.fetchall()

            if plans:
                keyboard = []
                row = []
                for plan in plans:
                    plan_name = plan[0]
                    row.append(
                        InlineKeyboardButton(text=plan_name, callback_data=f"view_plan_{plan_name}")
                    )
                    # Add a new row after a certain number of buttons (e.g., 2 buttons per row)
                    if len(row) == 2:  # You can adjust this number based on your preference
                        keyboard.append(row)
                        row = []
                
                # Add the last row if it has any buttons
                if row:
                    keyboard.append(row)
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬       
                        DAFTAR PLAN
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""", reply_markup=reply_markup)
            else:
                await update.message.reply_text("Tidak ada plan yang tersedia.")
        except Exception as e:
            await update.message.reply_text(f"Terjadi kesalahan saat mengakses database: {e}")
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")

# Fungsi untuk menangani callback query dari tombol inline keyboard
async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("view_plan_"):
        plan_name = data[len("view_plan_"):]
        
        try:
            detail_query = "SELECT planName, planCost, planTimeBank, planBandwidthUp, planBandwidthDown FROM billing_plans WHERE planName = %s"
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(detail_query, (plan_name,))
                plan_details = cursor.fetchone()
                
            if plan_details:
                plan_name = plan_details[0]
                plan_cost = plan_details[1]
                plan_timebank_seconds = int(plan_details[2])  # Pastikan ini adalah integer
                plan_timebank = format_time(plan_timebank_seconds)
                plan_bandwidth_up = format_bandwidth(float(plan_details[3]))  # Konversi ke float untuk bandwidth
                plan_bandwidth_down = format_bandwidth(float(plan_details[4]))  # Konversi ke float untuk bandwidth
                
                details_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬       
                        DETAIL PLAN
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Nama Plan: {plan_name}
Harga: Rp.{plan_cost}
Durasi: {plan_timebank}
Bandwidth: {plan_bandwidth_down}/{plan_bandwidth_up}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
                await query.edit_message_text(details_message)
            else:
                await query.edit_message_text("Detail plan tidak ditemukan.")
        except Exception as e:
            await query.edit_message_text(f"Terjadi kesalahan saat mengakses database: {e}")

async def delete_plan(update: Update, context: CallbackContext):
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                select_query = "SELECT id, planName FROM billing_plans"
                cursor.execute(select_query)
                plans = cursor.fetchall()
            
            if plans:
                keyboard = []
                row = []
                for plan in plans:
                    plan_id = plan[0]  # Access ID (first element of tuple)
                    plan_name = plan[1]  # Access Plan Name (second element of tuple)
                    row.append(
                        InlineKeyboardButton(text=f"{plan_name}", callback_data=f"remove_plan_{plan_id}")
                    )
                    if len(row) == 2:  # Adjust the number as needed
                        keyboard.append(row)
                        row = []
                
                if row:
                    keyboard.append(row)
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬       
                        HAPUS PLAN
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""", reply_markup=reply_markup)
            else:
                await update.message.reply_text("Tidak ada plan yang tersedia.")
        
        except Exception as e:
            await update.message.reply_text(f"Terjadi kesalahan saat mengambil daftar plan: {e}")
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")
        
async def handle_remove_plan(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("remove_plan_"):
        plan_id = data[len("remove_plan_"):]

        try:
            # Ambil nama plan berdasarkan ID sebelum menghapus
            select_query = "SELECT planName FROM billing_plans WHERE id = %s"
            delete_plan_query = "DELETE FROM billing_plans WHERE id = %s"
            delete_radgroupreply_query = "DELETE FROM radgroupreply WHERE groupname = %s"
            delete_radgroupcheck_query = "DELETE FROM radgroupcheck WHERE groupname = %s"
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Ambil nama plan
                cursor.execute(select_query, (plan_id,))
                plan_name_row = cursor.fetchone()
                
                if plan_name_row:
                    plan_name = plan_name_row[0]
                    
                    # Hapus plan dari billing_plans
                    cursor.execute(delete_plan_query, (plan_id,))
                    
                    # Hapus entri terkait dari radgroupreply dan radgroupcheck
                    cursor.execute(delete_radgroupreply_query, (plan_name,))
                    cursor.execute(delete_radgroupcheck_query, (plan_name,))
                    
                    conn.commit()
                    
                    await query.edit_message_text(f"Plan dan grup '{plan_name}' telah dihapus.")
                else:
                    await query.edit_message_text("Plan tidak ditemukan.")
        except Exception as e:
            await query.edit_message_text(f"Terjadi kesalahan saat menghapus plan: {e}")

async def delete_batch(update: Update, context: CallbackContext):
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            if context.args:
                batch_name = context.args[0]
            else:
                message = "Gunakan perintah : /delbatch <nama_batch>."
                await update.message.reply_text(message)
                return

            # Koneksi ke database
            connection = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                charset='utf8mb4',
                cursorclass=DictCursor
            )

            with connection.cursor() as cursor:
                # Periksa ketersediaan nama batch dan ambil batch_id serta batch_description
                check_batch_query = "SELECT id, batch_description FROM batch_history WHERE batch_name=%s"
                cursor.execute(check_batch_query, (batch_name,))
                batch = cursor.fetchone()

                if batch is None:
                    message = f"Batch dengan nama '{batch_name}' tidak terdapat di database."
                    await update.message.reply_text(message)
                    return

                batch_id = batch['id']
                batch_description = batch['batch_description']

                # Ambil username dari userbillinfo yang batch_id-nya sama dengan batch_id dari batch_history
                get_usernames_query = """
                SELECT username 
                FROM userbillinfo 
                WHERE batch_id=%s
                """
                cursor.execute(get_usernames_query, (batch_id,))
                usernames = [row['username'] for row in cursor.fetchall()]

                if not usernames:
                    message = f"Tidak ada pengguna dengan batch_id '{batch_id}' dalam database."
                    await update.message.reply_text(message)
                    return

                # Hapus batch dari batch_history menggunakan batch_id
                delete_batch_query = "DELETE FROM batch_history WHERE id=%s"
                cursor.execute(delete_batch_query, (batch_id,))
                connection.commit()

                # Hapus data terkait username dari tabel-tabel lain
                delete_queries = [
                    "DELETE FROM radcheck WHERE username=%s",
                    "DELETE FROM radacct WHERE username=%s",
                    "DELETE FROM userinfo WHERE username=%s",
                    "DELETE FROM radusergroup WHERE username=%s",
                    "DELETE FROM userbillinfo WHERE username=%s"
                ]

                for username in usernames:
                    for query in delete_queries:
                        cursor.execute(query, (username,))
                        connection.commit()

                message = f"Batch '{batch_name}' dan semua voucher yang dibuat dengan batch '{batch_name}' berhasil dihapus."

            connection.close()

            await update.message.reply_text(message)

        except pymysql.MySQLError as e:
            await update.message.reply_text(
                f"Terjadi kesalahan saat mengakses database: {e}"
            )
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")

async def list_batch(update: Update, context: CallbackContext):
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            # Koneksi ke database
            with pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                charset='utf8mb4'
            ) as connection:
                with connection.cursor() as cursor:
                    # Ambil daftar batch dari database
                    list_batch_query = "SELECT id, batch_name FROM batch_history"
                    cursor.execute(list_batch_query)
                    rows = cursor.fetchall()

                    if not rows:
                        message = "Tidak ada batch yang tersedia dalam database."
                        await update.message.reply_text(message)
                        return

                    batch_list = []
                    for batch_id, batch_name in rows:
                        # Hitung jumlah username dengan batch_id yang sama
                        count_query = """
                            SELECT COUNT(*) 
                            FROM userbillinfo 
                            WHERE batch_id = %s
                        """
                        cursor.execute(count_query, (batch_id,))
                        count = cursor.fetchone()[0]

                        batch_list.append(f"""
NAMA BATCH : {batch_name}
JUMLAH USER : {count}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""")

            message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                        BATCH LIST
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{''.join(batch_list)}"""

            await update.message.reply_text(message)

        except MySQLError as e:
            await update.message.reply_text(
                f"Terjadi kesalahan saat mengakses database: {e}"
            )
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")

async def disconnect_user(update: Update, context: CallbackContext):
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            # Ambil username dari pesan
            if not context.args:
                message = f"Gunakan perintah : /kick <username>."
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
                await update.message.reply_text(message)
            
            else:
                message = f"Gagal memutuskan pengguna '{username}': {disconnect_result.stderr}"
                await update.message.reply_text(message)
            
        except subprocess.CalledProcessError as e:
                message = f"Terjadi kesalahan saat mengakses database: {e.stderr}"
                await update.message.reply_text(message)
    else:
            await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")
            
# Fungsi untuk memulai proses backup
async def start_backup(update: Update, context: CallbackContext) -> int:
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            # Hapus pesan konfirmasi dari sesi sebelumnya jika ada
            if 'confirm_message_id' in context.chat_data:
                try:
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=context.chat_data['confirm_message_id']
                    )
                except Exception as e:
                    print(f"Terjadi kesalahan saat menghapus pesan konfirmasi: {e}")
                finally:
                    del context.chat_data['confirm_message_id']
                    del context.chat_data['backup_file_path']

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

            # Kirim pesan konfirmasi dengan tombol
            keyboard = [
                [InlineKeyboardButton("YA", callback_data='confirm_download'),
                InlineKeyboardButton("TIDAK", callback_data='cancel_download')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            confirm_message = await update.message.reply_text(
                "Backup database berhasil. Apakah Anda ingin mendownloadnya juga?",
                reply_markup=reply_markup
            )
            
            # Simpan path file dan ID pesan untuk pengolahan lebih lanjut
            context.chat_data['backup_file_path'] = FILE_PATH
            context.chat_data['confirm_message_id'] = confirm_message.message_id
            
            return BACKUP_CONFIRMATION
        
        except subprocess.CalledProcessError as e:
            await update.message.reply_text(
                f"Terjadi kesalahan saat backup database: {e.stderr}"
            )
            return ConversationHandler.END
    else:
        sent_message = await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")
        return ConversationHandler.END

# Fungsi untuk menangani tombol konfirmasi
async def handle_backup_buttons(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    action = query.data
    
    if action == 'confirm_download':
        await query.answer("Mengirimkan file backup...")
        try:
            file_path = context.chat_data.get('backup_file_path')
            if file_path and os.path.exists(file_path):
                # Kirim file backup
                await context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, "rb"))
            else:
                await query.message.reply_text("File backup tidak ditemukan.")
        
        except Exception as e:
            await query.message.reply_text(f"Terjadi kesalahan saat mengirim file: {e}")
        
    elif action == 'cancel_download':
        await query.answer("Download dibatalkan.")
        await query.message.reply_text("Pengunduhan file dibatalkan.")
    
    # Hapus pesan konfirmasi setelah tombol ditekan
    if 'confirm_message_id' in context.chat_data:
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=context.chat_data['confirm_message_id']
            )
        except Exception as e:
            print(f"Terjadi kesalahan saat menghapus pesan: {e}")
        finally:
            del context.chat_data['confirm_message_id']
            del context.chat_data['backup_file_path']
    
    return ConversationHandler.END

# Command /replace untuk memeriksa file SQL
async def start_replace(update: Update, context: CallbackContext) -> int:
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        file_path = FILE_PATH
        
        # Cek apakah file SQL ada
        if os.path.exists(file_path):
            
            # Kirim pesan konfirmasi dengan tombol
            keyboard = [
                [InlineKeyboardButton("YAKIN", callback_data='confirm_replace'),
                InlineKeyboardButton("TIDAK", callback_data='cancel_replace')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            confirm_message = await update.message.reply_text(
                "Apakah Anda yakin ingin mengganti database dengan file radius.sql?",
                reply_markup=reply_markup
            )
            
            # Simpan ID pesan konfirmasi untuk pengolahan lebih lanjut
            context.chat_data['confirm_message_id'] = confirm_message.message_id
            
            return CONFIRM_REPLACE
        
        else:
            await update.message.reply_text("Gagal : File radius.sql tidak ada.")
            return ConversationHandler.END
    else:
        sent_message = await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")
        return ConversationHandler.END

# Fungsi untuk menangani tombol konfirmasi
async def handle_replace_buttons(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    action = query.data
    
    if action == 'confirm_replace':
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=context.chat_data['confirm_message_id']
        )
        sent_message = await query.message.reply_text("Proses mengganti database dimulai...")
        try:
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

            # Kirim pesan konfirmasi
            await query.message.reply_text("Database radius berhasil diganti menggunakan file backup.")
        
        except subprocess.CalledProcessError as e:
            await query.message.reply_text(f"Terjadi kesalahan saat mengganti database: {e}")
        
    elif action == 'cancel_replace':
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=context.chat_data['confirm_message_id']
        )
        await query.answer("Proses digagalkan.")
        await query.message.reply_text("Penggantian database dibatalkan.")
    
    return ConversationHandler.END

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

async def custom_cmd(update: Update, context: CallbackContext):
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            command = " ".join(context.args)
            
            if not command:
                await update.message.reply_text("Gunakan perintah /cmd <command>")
                return

            # Debugging: log perintah yang akan dijalankan

            # Pastikan perintah valid
            if not command.strip():
                await update.message.reply_text("Perintah tidak valid.")
                return

            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout + result.stderr

            if output:
                await update.message.reply_text(f"{output}")
            else:
                await update.message.reply_text("Perintah dieksekusi tanpa output.")
                
        except Exception as e:
            await update.message.reply_text(f"Terjadi kesalahan saat mengeksekusi perintah: {e}")
    else:
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

# Fungsi untuk menghasilkan string acak
def generate_random_string(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Fungsi untuk memilih menu voucher
async def voucher(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)

    if is_admin(user_id):
        keyboard = [[InlineKeyboardButton("GENERATE", callback_data='generate_voucher'),
                     InlineKeyboardButton("CANCEL", callback_data='cancels')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                  BATCH ADD USER
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""", reply_markup=reply_markup)
        return PILIH_TINDAKAN
    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")
        return ConversationHandler.END

# Fungsi untuk memilih durasi voucher
async def choose_durasi(update: Update, context: CallbackContext):
    query = update.callback_query
    billing_plan_keyboard_markup = create_groupname_keyboard()
    await query.message.edit_text("""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
         PILIH DURASI DAN HARGA
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""", reply_markup=billing_plan_keyboard_markup)
    return PILIH_DURASI

# Fungsi untuk memilih groupname
async def choose_groupname(update: Update, context: CallbackContext):
    query = update.callback_query
    reply_markup = create_groupname_keyboard()
    await query.message.edit_text("""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
 PILIH GROUP NAME
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""", reply_markup=reply_markup)
    return PILIH_GROUPNAME

# Fungsi untuk memilih jumlah voucher
async def choose_quantity(update: Update, context: CallbackContext):
    query = update.callback_query
    reply_markup = quantity_keyboard_markup
    await query.message.edit_text("""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
 PILIH JUMLAH YANG AKAN DICETAK 
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬""", reply_markup=reply_markup)
    return PILIH_JUMLAH

# Fungsi untuk mengambil nama grup beserta biayanya dari database
def fetch_groupnames_with_cost():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT DISTINCT groups.groupname, billing_plans.planCost
            FROM (
                SELECT groupname FROM radgroupcheck
                UNION
                SELECT groupname FROM radgroupreply
            ) AS groups
            JOIN billing_plans ON groups.groupname = billing_plans.planName
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
    finally:
        connection.close()
    
    return rows

def create_groupname_keyboard():
    groupnames_with_cost = fetch_groupnames_with_cost()
    
    keyboard = []
    row = []
    for groupname, plan_cost in groupnames_with_cost:
        button_text = f"{groupname} - Rp.{plan_cost}"
        callback_data = f"group_{groupname}"
        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        if len(row) == 2:  # Ganti 2 dengan jumlah tombol per baris yang diinginkan
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)  # Untuk tombol yang tersisa
    
    return InlineKeyboardMarkup(keyboard)

# Fungsi untuk membuat voucher
async def create_voucher(update: Update, context: CallbackContext):
    query = update.callback_query
    groupname = context.user_data.get('groupname')
    quantity = context.user_data.get('quantity', 1)
    all_numbers = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        random_string = generate_random_string()
        batch_name = f"{random_string}"
        batch_description = groupname

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
                (number, groupname, '0'),
            )
            cursor.execute("INSERT INTO userinfo (username, firstname, lastname, email, department, company, workphone, homephone, mobilephone, address, city, state, country, zip, notes, changeuserinfo, portalloginpassword, creationdate, creationby) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                (number, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '0', '', now, 'administrator'),
            )
            cursor.execute(
                "INSERT INTO userbillinfo (username, planName, contactperson, company, email, phone, address, city, state, country, zip, paymentmethod, cash, creditcardname, creditcardnumber, creditcardverification, creditcardtype, creditcardexp, notes, changeuserbillinfo, lead, coupon, ordertaker, billstatus, postalinvoice, faxinvoice, emailinvoice, batch_id, creationdate, creationby) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (number, groupname, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '0', '', '', '', '', '', '', '', batch_id, now, 'administrator'),
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
    link = f"http://{ip_lan}/daloradius/include/common/printTickets.php?type=batch&plan={groupname}&accounts=Username,Password||{accounts_str}"

    # Membuat pesan konfirmasi dengan semua username
    numbers_list = ', '.join(all_numbers)
    confirmation_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
              BATCH INFORMATION
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
BATCH NAME  :  {batch_name}
GROUP NAME : {groupname}
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

# Fungsi untuk menangani pilihan admin
async def handle_admin_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "cancels":
        return await cancel_batch(update, context)
    
    if data == "generate_voucher":
        return await choose_durasi(update, context)
    
    if data.startswith("durasi_"):
        # Pilihan durasi
        context.user_data['durasi'] = data.split("_")[1]  # Simpan durasi jika perlu
        return await choose_groupname(update, context)
    
    if data.startswith("group_"):
        # Pilihan groupname
        context.user_data['groupname'] = data.split("_")[1]
        return await choose_quantity(update, context)
    
    if data.startswith("quantity_"):
        quantity = int(data.split("_")[1])
        context.user_data['quantity'] = quantity
        return await create_voucher(update, context)
    
    return ConversationHandler.END

# Fungsi untuk menangani pembatalan
async def cancel_batch(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer("Operasi dibatalkan.")
    await query.edit_message_text(text="Operasi telah dibatalkan.")
    context.user_data.clear()  # Membersihkan data pengguna jika diperlukan
    return ConversationHandler.END

# Fungsi untuk menampilkan pilihan durasi voucher

async def send_login_link(query, code):
    login_url = f"http://{ip_chilli}:3990/login?username={code}&password=Accept"

    login_button = InlineKeyboardButton(text="Login", url=login_url)
    keyboard = [[login_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.edit_reply_markup(reply_markup=reply_markup)

def get_duration_data_from_db():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT groups.groupname, billing_plans.planCost
                FROM (
                    SELECT groupname FROM radgroupcheck
                    UNION
                    SELECT groupname FROM radgroupreply
                ) AS groups
                JOIN billing_plans ON groups.groupname = billing_plans.planName
            """)
            # Fetch all rows from the query result
            results = cursor.fetchall()
            
            # Convert the results to a list of dictionaries
            data = []
            for row in results:
                data.append({
                    "group_name": row[0],
                    "plan_cost": row[1]
                })
                
            return data
    finally:
        connection.close()

async def choose_duration(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)  # Mengubah user_id menjadi string untuk pencocokan di JSON

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
    reply_markup = create_cost_keyboard()
    await query.message.edit_text(reply_message, reply_markup=reply_markup)
    return CHOOSE_DURATION

def create_cost_keyboard():
    groupnames_with_cost = get_duration_data_from_db()
    
    keyboard = []
    row = []
    for item in groupnames_with_cost:
        groupname = item["group_name"]
        plan_cost = item["plan_cost"]
        button_text = f"{groupname} - Rp.{plan_cost}"
        callback_data = f"{plan_cost}, {groupname}"  # Format callback data
        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        if len(row) == 2:  # Ganti 2 dengan jumlah tombol per baris yang diinginkan
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)  # Untuk tombol yang tersisa
    
    return InlineKeyboardMarkup(keyboard)

async def handle_duration_choice(update: Update, context: CallbackContext):
    query = update.callback_query

    # Ambil data durasi dari database
    duration_data = get_duration_data_from_db()

    # Parsing data dari callback
    try:
        duration_code, group_name = query.data.split(", ")
        plan_cost = int(duration_code)
        price_info = group_name
        duration_name = group_name
    except ValueError:
        await query.answer()
        await send_services_menu(update, context)
        return CHOOSE_DURATION

    # Verifikasi saldo pengguna
    user_id = str(update.effective_user.id)
    username = update.effective_user.username
    profiles = read_profiles()
    balance = profiles.get(user_id, {}).get("balance", 0)

    if balance < plan_cost:
        reply_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                INFORMATION
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
SALDO ANDA TIDAK MENCUKUPI
UNTUK MEMBELI KODE VOUCHER 
SILAHKAN ISI ULANG SALDO ANDA.
"""
        keyboard = [[InlineKeyboardButton("MENU", callback_data="send_services_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(reply_message, reply_markup=reply_markup)
        await query.answer()
        return

    # Generate kode angka acak 6 digit
    code = "".join(random.choices(string.digits, k=6))

    # Kurangi saldo user
    profiles[user_id]["balance"] -= plan_cost
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
HARGA : Rp.{plan_cost}
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
            # Insert ke tabel radcheck
            cursor.execute(
                "INSERT INTO radcheck (username, attribute, op, value) VALUES (%s, %s, %s, %s)",
                (code, "Auth-Type", ":=", "Accept"),
            )

            # Insert ke tabel radusergroup
            cursor.execute(
                "INSERT INTO radusergroup (username, groupname, priority) VALUES (%s, %s, %s)",
                (code, duration_name, "0"),
            )

            # Insert ke tabel userinfo
            cursor.execute("INSERT INTO userinfo (username, firstname, lastname, email, department, company, workphone, homephone, mobilephone, address, city, state, country, zip, notes, changeuserinfo, portalloginpassword, creationdate, creationby) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                (code, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '0', '', now, 'administrator'),
            )

            # Insert ke tabel userbillinfo
            cursor.execute(
                "INSERT INTO userbillinfo (username, planName, contactperson, company, email, phone, address, city, state, country, zip, paymentmethod, cash, creditcardname, creditcardnumber, creditcardverification, creditcardtype, creditcardexp, notes, changeuserbillinfo, lead, coupon, ordertaker, billstatus, nextinvoicedue, billdue, postalinvoice, faxinvoice, emailinvoice, creationdate, creationby) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (code, price_info, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '0', '', '', '', '', '0', '0', '', '', '', now, 'administrator'),
            )

        connection.commit()

    finally:
        connection.close()

    return ConversationHandler.END

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
                else "Ditolak",
            )

            # Fetch user details
            chat_member = await context.bot.get_chat_member(
                chat_id=user_id, user_id=user_id
            )
            user = chat_member.user

            if action == "topup" and topup_action == "accept":
                await query.answer("Topup diterima.")
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
                
                await query.answer("Topup ditolak.")
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
        logout_logs = [log for log in new_logs if "LogOut OK" in log]

        for log in login_ok_logs:
            match = re.search(
                r"(\w+ \w+ {1,2}\d+ \d+:\d+:\d+ \d+) : Auth: \(\d+\) Login OK: \[([\w\d]+).*\] \(from client .* cli ([\w-]+)\)",
                log,
            )
            if match:
                timestamp = match.group(1)
                code = match.group(2)
                mac = match.group(3)
                now = datetime.now()
                formatted_time = now.strftime("%d-%m-%Y %H:%M:%S WIB")
                formatted_log = f"🔑 Pengguna {mac} Login menggunakan kode voucher {code} pada {formatted_time}"
                for admin_id in ADMIN_IDS:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id, text=formatted_log
                        )
                    except TimedOut:
                        continue

        for log in logout_logs:
            match = re.search(
                r"(\w+ \w+ {1,2}\d+ \d+:\d+:\d+ \d+) : Auth: \(\d+\) LogOut OK: \[(\d+)\/([\w-]+)\] \(from client .* cli ([\w-]+)\)",
                log,
            )
            if match:
                log_timestamp = match.group(1)
                session_id = match.group(2)
                terminate_cause = match.group(3)
                mac = match.group(4)
                log_time = datetime.strptime(log_timestamp, "%a %b %d %H:%M:%S %Y")
                formatted_time = log_time.strftime("%d-%m-%Y %H:%M:%S WIB")
                if terminate_cause == "User-Request":
                    formatted_log = f"🔑 Pengguna {mac} Logout dari kode voucher {session_id} pada {formatted_time}"
                elif terminate_cause == "Session-Timeout":
                    formatted_log = f"⏰ Kode voucher {session_id} telah Expired dan dihapus pada {formatted_time}"
                
                if formatted_log:  # Check if formatted_log is not None
                    for admin_id in ADMIN_IDS:
                        try:
                            await context.bot.send_message(
                                chat_id=admin_id, text=formatted_log
                            )
                        except TimedOut:
                            continue

    except FileNotFoundError:
        pass
    except IOError as e:
        print(f"IOError: {e}")

def clear_log_file():
    global LAST_POSITION

    try:
        with open(LOG_FILE_PATH, "w") as file:
            pass

        LAST_POSITION = 0
        save_last_position(LAST_POSITION)
    except FileNotFoundError:
        pass

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    sent_message = await update.message.reply_text("𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩...")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=sent_message.message_id)
    
    if is_admin(user_id):
        update_message = await update.message.reply_text("Merestart BOT.")

        try:
            subprocess.run("service telebot restart", shell=True, check=True)
            await update.message.reply_text("BOT Direstart.")
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update_message.message_id)
        except subprocess.CalledProcessError as e:
            await update.message.reply_text(f"Failed to execute restart command: {e}")

    else:
        await update.message.reply_text("𝙋𝙚𝙧𝙞𝙣𝙩𝙖𝙝 𝙞𝙣𝙞 𝙝𝙖𝙣𝙮𝙖 𝙪𝙣𝙩𝙪𝙠 𝘼𝙙𝙢𝙞𝙣.")
    
    

def main():
    clear_log_file()
    application = Application.builder().token(TOKEN).build()

    # Handler untuk berbagai command dan callback
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("topup", add_balance))
    application.add_handler(CommandHandler("menu", show_menu))
    application.add_handler(CommandHandler("saldo", check_balance))
    application.add_handler(CommandHandler("hapus", delete_user))
    application.add_handler(CommandHandler("kick", disconnect_user))
    application.add_handler(CommandHandler("cmd", custom_cmd))
    application.add_handler(CommandHandler("pendapatan", pendapatan))
    application.add_handler(CommandHandler("kuota", usage))
    application.add_handler(CommandHandler("delbatch", delete_batch))
    application.add_handler(CommandHandler("listbatch", list_batch))
    application.add_handler(CommandHandler("restart", restart_bot))
    application.add_handler(CommandHandler("addplan", add_plan))
    application.add_handler(CommandHandler("listplan", list_plan))
    application.add_handler(CommandHandler("delplan", delete_plan))
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
    
    # ConversationHandler untuk /alluser
    alluser_handler = ConversationHandler(
        entry_points=[CommandHandler('list', alluser)],
        states={
            PAGE_SELECTION: [CallbackQueryHandler(handle_navigation_list)],
        },
        fallbacks=[],
    )
    
    # ConversationHandler untuk /online
    online_handler = ConversationHandler(
        entry_points=[CommandHandler('online', online)],
        states={
            PAGE_SELECTION: [CallbackQueryHandler(handle_navigation_online)],
        },
        fallbacks=[],
    )

    # ConversationHandler untuk /replace
    replace_handler = ConversationHandler(
        entry_points=[CommandHandler('replace', start_replace)],
        states={
            CONFIRM_REPLACE: [CallbackQueryHandler(handle_replace_buttons)],
        },
        fallbacks=[],
    )

    # ConversationHandler untuk /backup
    backup_handler = ConversationHandler(
        entry_points=[CommandHandler('backup', start_backup)],
        states={
            BACKUP_CONFIRMATION: [CallbackQueryHandler(handle_backup_buttons)],
        },
        fallbacks=[],
    )

    application.add_handler(voucher_handler)
    application.add_handler(upload_handler)
    application.add_handler(conv_handler)
    application.add_handler(topup_handler)
    application.add_handler(alluser_handler)
    application.add_handler(online_handler)
    application.add_handler(replace_handler)
    application.add_handler(backup_handler)
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^view_plan_"))
    application.add_handler(CallbackQueryHandler(handle_remove_plan, pattern="^remove_plan_"))


    job_queue = application.job_queue
    job_queue.run_repeating(poll_log_changes, interval=POLL_INTERVAL, first=0)

    application.run_polling()

if __name__ == "__main__":
    main()
    
     # ⓒ  2024 - Mutiara-Wrt by Maizil https://t.me/maizil41
