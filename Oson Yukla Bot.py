import logging
import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# ==========================================================
# 1. BOT TOKENINGIZNI SHU YERGA YOZING
API_TOKEN = '8530462813:AAFxPrAjZyDG6Fgv_JMqy0XwMgnCKQp1Zv4'
# ==========================================================

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher obyektlari
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Fayllarni saqlash uchun papka
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# --- RENDER UCHUN SOXTA SERVER (PORT TIMEOUT OLDINI OLISH) ---
class StaticServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_static_server():
    # Render avtomatik beradigan PORT ni oladi, bo'lmasa 8080
    port = int(os.environ.get("PORT", 8080))
    server_address = ('', port)
    httpd = HTTPServer(server_address, StaticServer)
    logging.info(f"Fake server started on port {port}")
    httpd.serve_forever()

# --- YUKLASH FUNKSIYASI ---
def download_media(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        logging.error(f"Yuklash xatosi: {e}")
        return None

# --- QIDIRUV FUNKSIYASI ---
def search_music(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            filename = ydl.prepare_filename(info)
            if not filename.endswith('.mp3'):
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            return filename
    except Exception as e:
        logging.error(f"Musiqa qidiruv xatosi: {e}")
        return None

# --- TUGMACHALAR ---
def get_inline_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    btn_group = InlineKeyboardButton(
        text="➕ Guruhga qo'shish ⤴️", 
        url="https://t.me/OsonYukla_UzBot?startgroup=true"
    )
    keyboard.add(btn_group)
    return keyboard

# --- HANDLERLAR ---

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply(
        "👋 <b>Salom! OsonYukla Botga xush kelibsiz!</b>\n\n"
        "📥 Instagram, TikTok yoki YouTube linkini yuboring.\n"
        "🎵 Yoki qo'shiq nomini yozing.",
        parse_mode="HTML"
    )

@dp.message_handler()
async def handle_all_messages(message: types.Message):
    user_text = message.text
    waiting_msg = await message.answer("🔍 Iltimos, kuting...")
    
    keyboard = get_inline_keyboard()
    caption_text = (
        "✅ <b>Tayyor!</b>\n\n"
        "🤖 @OsonYukla_UzBot orqali istagan musiqangizni tez va oson toping! 🚀"
    )

    if user_text.startswith("http"):
        # Videoni yuklab olish
        file_path = await asyncio.get_event_loop().run_in_executor(None, download_media, user_text)
        
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as video:
                await message.answer_video(
                    video=video,
                    caption=caption_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            os.remove(file_path)
        else:
            await message.answer("❌ Videoni yuklab bo'lmadi. Linkni tekshiring.")
    else:
        # Musiqani qidirish
        file_path = await asyncio.get_event_loop().run_in_executor(None, search_music, user_text)
        
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as audio:
                await message.answer_audio(
                    audio=audio,
                    caption=caption_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            os.remove(file_path)
        else:
            await message.answer("❌ Bunday qo'shiq topilmadi.")

    await waiting_msg.delete()

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == '__main__':
    # Render uchun soxta serverni alohida oqimda ishga tushiramiz
    threading.Thread(target=run_static_server, daemon=True).start()
    
    print("Bot @OsonYukla_UzBot nomi bilan ishga tushdi...")
    executor.start_polling(dp, skip_updates=True)
