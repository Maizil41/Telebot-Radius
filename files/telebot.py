import os
import sys
import json
import random
import string
import pymysql
import datetime
import subprocess
from telegram.error import TimedOut
from telegram.constants import ParseMode
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters, ConversationHandler


# Membaca token dan chat ID admin dari berkas token.txt
with open('/root/Telebot/auth', 'r') as token_file:
    lines = token_file.readlines()
    if len(lines) >= 2:
        TOKEN = lines[0].strip()
        USER_ID = int(lines[1].strip())
    else:
        print("Berkas token harus memiliki setidaknya 2 baris (token dan chat ID admin).")
        exit()
        
# File JSON untuk menyimpan kode dan saldo pengguna
PROFILES_JSON_FILE = '/root/Telebot/profiles.json'  # Sesuaikan dengan path yang sesuai di OpenWRT

# Daftar ID admin yang diizinkan
ADMIN_IDS = set([USER_ID])

# State untuk conversation handler
CHOOSE_DURATION, TOPUP_AMOUNT = range(2)

# Restart bot apabila ada kesalahan
def restart_bot():
    """Restart the bot by reloading the script."""
    os.execv(sys.executable, [sys.executable] + sys.argv)
    
# Fungsi untuk membaca data dari file JSON
def read_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Fungsi untuk menulis data ke file JSON
def write_json(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file)

# Fungsi untuk membaca data dari file profile
def read_profiles():
    try:
        with open(PROFILES_JSON_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
        
# Fungsi untuk menulis data ke file profile
def write_profiles(profiles):
    with open(PROFILES_JSON_FILE, 'w') as file:
        json.dump(profiles, file, indent=4)

# Fungsi untuk memeriksa apakah pengguna adalah admin
def is_admin(user_id):
    return user_id in ADMIN_IDS

# Command /start untuk memberikan daftar command kepada admin dan sambutan kepada user
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username
    profiles = read_profiles()
    balance = profiles.get(str(user_id), {}).get('balance', 0)
    
    if is_admin(user_id):
        commands = """
                      ADMIN ACCESS
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Daftar perintah:
1. /isi - Topup saldo user
2. /saldo - Cek saldo user
"""
        await update.message.reply_text(f'▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ {commands}')
    else:
        welcome_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                        ACCESS USER
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Selamat datang di Mutiara-Wrt Billbot
Username  :  {username}
User Id        :  {user_id}
Balance      :   Rp.{balance}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
        keyboard = [
            [InlineKeyboardButton("DAPATKAN KODE", callback_data='get_code'),
            InlineKeyboardButton("TOPUP SALDO", callback_data='start_topup')],
            [InlineKeyboardButton("HUBUNGI ADMIN", url='https://t.me/Maizil41')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Fungsi untuk menangani perintah /menu
async def show_menu(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    profiles = read_profiles()
    
    if is_admin(user_id):
        commands = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                      ADMIN ACCESS
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Daftar perintah:
1. /isi - Topup saldo user
1. /saldo - Cek saldo user
"""
        await update.message.reply_text(commands)
    else:
        if str(user_id) in profiles:
            balance = profiles[str(user_id)]["balance"]
            username = profiles[str(user_id)].get("username", "Unknown")
            welcome_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                        ACCESS USER
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Selamat datang di Mutiara-Wrt Billbot
Username  :  {username}
User Id        :  {user_id}
Balance      :   Rp.{balance}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
            keyboard = [
                [InlineKeyboardButton("DAPATKAN KODE", callback_data='get_code'),
                InlineKeyboardButton("TOPUP SALDO", callback_data='start_topup')],
                [InlineKeyboardButton("HUBUNGI ADMIN", url='https://t.me/Maizil41')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(welcome_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text('Data saldo Anda tidak ditemukan.')

# Command /isi untuk menambah saldo pengguna (hanya untuk admin)
async def add_balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if is_admin(user_id):
        try:
            if len(context.args) != 2:
                await update.message.reply_text('Gunakan format: /isi <user_id> <jumlah>')
                return

            target_user_id = int(context.args[0])
            amount = int(context.args[1])
            profiles = read_profiles()

            # Buat entri baru jika pengguna tidak ditemukan
            if str(target_user_id) not in profiles:
                profiles[str(target_user_id)] = {'balance': 0, 'username': 'tidak memiliki username'}

            # Tambahkan saldo ke entri pengguna
            profiles[str(target_user_id)]['balance'] += amount

            # Dapatkan informasi pengguna target
            try:
                target_user = await context.bot.get_chat(target_user_id)
                username = target_user.username if target_user.username else 'tidak memiliki username'
            except Exception as e:
                username = 'tidak memiliki username'
                print(f'Gagal mendapatkan username untuk ID {target_user_id}: {e}')

            # Update username di entri pengguna
            profiles[str(target_user_id)]['username'] = username
            write_profiles(profiles)

            # Kirim pesan konfirmasi ke admin
            await update.message.reply_text(f'💰 Saldo pengguna @{username} ({target_user_id}) berhasil ditambahkan sebesar Rp.{amount}.')

            # Kirim pesan ke pengguna yang saldonya ditambahkan
            try:
                await context.bot.send_message(chat_id=target_user_id, text=f'Saldo Anda telah ditambahkan sebesar Rp.{amount} oleh admin.')
            except Exception as e:
                print(f'Gagal mengirim pesan ke pengguna ID {target_user_id}: {e}')

        except (IndexError, ValueError):
            await update.message.reply_text('Gunakan format: /isi <user_id> <jumlah>')
    else:
        await update.message.reply_text('Anda tidak memiliki izin untuk menggunakan perintah ini.')

# Command /saldo untuk melihat saldo pengguna (hanya untuk admin)
async def check_balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    profiles = read_profiles()
    
    if is_admin(user_id):
        try:
            target_user_id = context.args[0]  # Ambil user_id dari argumen
            if target_user_id in profiles:
                await update.message.reply_text(f'Saldo untuk user ID {target_user_id}: Rp {profiles[target_user_id]["balance"]}')
            else:
                await update.message.reply_text(f'Pengguna dengan ID {target_user_id} tidak ditemukan.')
        except IndexError:
            await update.message.reply_text('Gunakan format: /saldo <user_id>')
    else:
        if str(user_id) in profiles:
            await update.message.reply_text(f'Saldo Anda : Rp {profiles[str(user_id)]["balance"]}')
        else:
            await update.message.reply_text('Data saldo Anda tidak ditemukan.')

# Fungsi untuk menampilkan pilihan durasi voucher
async def choose_duration(update: Update, context: CallbackContext):
    query = update.callback_query
    reply_message = f"""▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                        ACCESS USER
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Silahkan pilih harga dan waktu voucher
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"""
    keyboard = [
        [InlineKeyboardButton("3 Jam | Rp.1000", callback_data='duration_3')],
        [InlineKeyboardButton("6 Jam | Rp.2000", callback_data='duration_6')],
        [InlineKeyboardButton("9 Jam | Rp.3000", callback_data='duration_9')],
        [InlineKeyboardButton("12 Jam | Rp.4000", callback_data='duration_12')],
        [InlineKeyboardButton("1 Hari | Rp.5000", callback_data='duration_1')],
        [InlineKeyboardButton("7 Hari | Rp.25000", callback_data='duration_7')],
        [InlineKeyboardButton("30 Hari | Rp.50000", callback_data='duration_30')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(reply_message, reply_markup=reply_markup)
    return CHOOSE_DURATION

# Fungsi untuk mendapatkan koneksi ke database MySQL
def get_db_connection():
    return pymysql.connect(
        host='127.0.0.1',  # Ganti dengan host database Anda
        user='radius',  # Ganti dengan username database Anda
        password='radius',  # Ganti dengan password database Anda
        database='radius'  # Ganti dengan nama database Anda
    )
    
async def send_login_link(query, code):
    login_url = f"http://10.10.10.1:3990/login?username={code}&password=Accept"
    
    # Membuat tombol dengan link
    login_button = InlineKeyboardButton(text="Login", url=login_url)
    keyboard = [[login_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Mengedit pesan yang ada untuk hanya menampilkan keyboard
    await query.message.edit_reply_markup(reply_markup=reply_markup)

async def handle_duration_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    duration_mapping = {
        'duration_3': 1000,
        'duration_6': 2000,
        'duration_9': 3000,
        'duration_12': 4000,
        'duration_1': 5000,
        'duration_7': 25000,
        'duration_30': 50000,
    }
    
    duration_names = {
        'duration_3': '3Jam',
        'duration_6': '6Jam',
        'duration_9': '9Jam',
        'duration_12': '12Jam',
        'duration_1': '1Hari',
        'duration_7': '7Hari',
        'duration_30': '30Hari',
    }
    
    duration_code = query.data
    if duration_code in duration_mapping:
        amount = duration_mapping[duration_code]
        duration_name = duration_names[duration_code]
        user_id = update.effective_user.id
        username = update.effective_user.username
        profiles = read_profiles()
        balance = profiles.get(str(user_id), {}).get('balance', 0)
        
        if balance < amount:
            await query.answer()
            await query.message.edit_text('Saldo Anda tidak mencukupi, klik /start untuk mulai ulang')
            restart_bot()
            return CHOOSE_DURATION
        
        # Generate kode angka acak 6 digit
        code = ''.join(random.choices(string.digits, k=6))
        
        # Kurangi saldo user
        profiles[str(user_id)]['balance'] -= amount
        write_profiles(profiles)
        
        # Kirim kode ke pengguna
        await query.answer()
        await query.message.edit_text(f'Kode Voucher : {code}\nDurasi Aktif : {duration_name}', parse_mode='MarkdownV2')
        
        # Kirim notifikasi ke admin
        admin_message = f'🔑 Pengguna @{username} ({user_id}) membeli kode {code} durasi {duration_name} pada {datetime.now().strftime("%d-%m-%Y %H:%M")} WIB.'
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(admin_id, admin_message)
        
        # Membuat link dengan semua username
        await send_login_link(update.callback_query, code)
        
        # Menyimpan kode ke database Radius
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO radcheck (username, attribute, op, value) VALUES (%s, %s, %s, %s)", 
                               (code, 'Auth-Type', ':=', 'Accept'))
                cursor.execute("INSERT INTO radusergroup (username, groupname, priority) VALUES (%s, %s, %s)", 
                               (code, duration_name, '0'))  # Gunakan nama durasi sebagai group_name
                cursor.execute("INSERT INTO userinfo (username) VALUES (%s)", (code,))
                cursor.execute("INSERT INTO userbillinfo (username, planName) VALUES (%s, %s)", (code, duration_name))  # Gunakan nama durasi sebagai planName
            connection.commit()
        finally:
            connection.close()
        
        return ConversationHandler.END

    # Jika pilihan durasi tidak valid, restart bot
    await query.answer()
    await query.message.edit_text('Pilihan durasi tidak valid, klik /start untuk mulai ulang')
    restart_bot()
    return CHOOSE_DURATION

# Fungsi untuk memulai proses mendapatkan kode
async def get_code(update: Update, context: CallbackContext):
    await update.callback_query.answer()
    await update.callback_query.message.delete()
    
    # Tampilkan keyboard pilihan durasi
    keyboard = [
        [InlineKeyboardButton("3 Jam", callback_data='duration_3')],
        [InlineKeyboardButton("6 Jam", callback_data='duration_6')],
        [InlineKeyboardButton("9 Jam", callback_data='duration_9')],
        [InlineKeyboardButton("12 Jam", callback_data='duration_12')],
        [InlineKeyboardButton("1 Hari", callback_data='duration_1')],
        [InlineKeyboardButton("7 Hari", callback_data='duration_7')],
        [InlineKeyboardButton("30 Hari", callback_data='duration_30')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Pilih durasi voucher:', reply_markup=reply_markup)
    return CHOOSE_DURATION

# Fungsi untuk memulai proses TopUp
async def start_topup(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Masukkan jumlah topup:")
    return TOPUP_AMOUNT

async def handle_topup_amount(update: Update, context: CallbackContext):
    user = update.message.from_user
    amount_text = update.message.text

    if amount_text.isdigit():
        amount = int(amount_text)
        if amount > 0:
            now = datetime.now()
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')

            # Send notification to admins with confirmation buttons
            keyboard = [
                [InlineKeyboardButton("Terima", callback_data=f"topup_accept_{user.id}_{amount}")],
                [InlineKeyboardButton("Tolak", callback_data=f"topup_reject_{user.id}_{amount}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🚨 Pengguna @{user.username} (`{user.id}`) ingin topup dengan jumlah Rp.`{amount}` pada {timestamp}.",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )

            await update.message.reply_text(
                "Permintaan topup akan diproses,\nSilahkan lakukan pembayaran sesuai jumlah topup,\nDan kirimkan bukti pembayaran ke @Maizil41"
            )
            return ConversationHandler.END
        else:
            await update.message.reply_text("Silahkan masukkan jumlah yang valid.")
            return TOPUP_AMOUNT
    else:
        await update.message.reply_text("Silahkan masukkan jumlah yang valid.")
        return TOPUP_AMOUNT

async def handle_topup_response(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    # Debugging line to print the received callback data
    print(f"Received callback data: {data}")

    # Split data based on underscores
    parts = data.split('_')
    
    if len(parts) == 4:
        action, topup_action, user_id_str, amount_str = parts
        
        try:
            # Convert user_id and amount from strings to integers
            user_id = int(user_id_str)
            amount = int(amount_str)
            
            # Determine status based on the action
            status = "Diterima" if action == "topup" and topup_action == "accept" else "Ditolak"
            
            # Fetch user details
            chat_member = await context.bot.get_chat_member(chat_id=user_id, user_id=user_id)
            user = chat_member.user

            if action == "topup" and topup_action == "accept":
                # Process the topup
                profiles = read_profiles()

                # Create a new entry if user not found
                if str(user_id) not in profiles:
                    profiles[str(user_id)] = {'balance': 0, 'username': 'tidak memiliki username'}

                # Add balance to the user entry
                profiles[str(user_id)]['balance'] += amount

                # Get target user info
                try:
                    target_user = await context.bot.get_chat(user_id)
                    username = target_user.username if target_user.username else 'tidak memiliki username'
                except Exception as e:
                    username = 'tidak memiliki username'
                    print(f'Gagal mendapatkan username untuk ID {user_id}: {e}')

                # Update username in the user entry
                profiles[str(user_id)]['username'] = username
                write_profiles(profiles)

                # Notify admin
                await query.edit_message_text(f"💰Permintaan topup Rp.{amount} dari (@{user.username} / {user_id}) telah disetujui.")

                # Notify user
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f'Permitaan Topup anda sebesar Rp.{amount} telah disetujui oleh admin\nSilahkan cek saldo anda'
                    )
                except Exception as e:
                    print(f'Gagal mengirim pesan ke pengguna ID {user_id}: {e}')
            else:
                await query.edit_message_text(f"💰Permintaan topup Rp.{amount} dari (@{user.username} / {user_id}) tidak disetujui.")
                # Notify user
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f'Permitaan Topup anda sebesar Rp.{amount} tidak disetujui oleh admin.'
                    )
                except Exception as e:
                    print(f'Gagal mengirim pesan ke pengguna ID {user_id}: {e}')
            
        
        except ValueError:
            await query.answer(text="Data callback tidak valid. Gagal mengonversi ID pengguna atau jumlah.")
            print("ValueError: Data callback tidak dapat dikonversi ke integer.")
        
        except TimedOut:
            await query.answer(text="Permintaan Anda mengalami timeout. Silakan coba lagi nanti.")
            print("TimedOut: Permintaan ke API Telegram mengalami timeout.")
        
        except Exception as e:
            await context.bot.send_message(
                chat_id=ADMIN_IDS[0],  # Assuming at least one admin ID is available
                text=f"Terjadi kesalahan saat memproses topup: {str(e)}"
            )
            print(f"Exception: {str(e)}")
    
    else:
        await query.answer(text="Data callback tidak valid. Format data tidak sesuai.")
        print("Error: Data callback tidak sesuai format yang diharapkan.")
    
    return ConversationHandler.END

async def cancel(update: Update, context):
    await update.message.reply_text('Proses topup dibatalkan.')
    return ConversationHandler.END

def main():
    application = Application.builder().token(TOKEN).build()

    # Handler untuk berbagai command dan callback
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('isi', add_balance))
    application.add_handler(CommandHandler('saldo', check_balance))
    application.add_handler(CommandHandler('menu', show_menu))
    application.add_handler(CallbackQueryHandler(handle_topup_response, pattern=r'^topup_(accept|reject)_(\d+)_(\d+)$'))
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(choose_duration, pattern='get_code')],
        states={
            CHOOSE_DURATION: [CallbackQueryHandler(handle_duration_choice)]
        },
        fallbacks=[],
    )
    
    topup_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_topup, pattern='start_topup')],
        states={
            TOPUP_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_topup_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(topup_handler)

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()