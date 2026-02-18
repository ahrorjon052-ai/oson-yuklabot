import logging
import os
import asyncio
import threading
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# Sozlamalar
API_TOKEN = os.environ.get('API_TOKEN', '8530462813:AAFxPrAjZyDG6Fgv_JMqy0XwMgnCKQp1Zv4')
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

if not os.path.exists('downloads'):
    os.makedirs('downloads')

# Render uchun soxta server
class StaticServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

def run_static_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), StaticServer)
    httpd.serve_forever()

# Yuklash funksiyasi (Video va YouTube uchun)
def download_video(url):
    unique_name = str(uuid.uuid4())
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': f'downloads/{unique_name}.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0'}
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception:
        return None

# Musiqa qidirish va yuklash
def download_audio(query):
    unique_name = str(uuid.uuid4())
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'downloads/{unique_name}.%(ext)s',
        'default_search': 'ytsearch1',
        'noplaylist': True,
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
            return filename.rsplit('.', 1)[0] + '.mp3'
    except Exception:
        return None

# Tugmachalar
def main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📥 Qo'shiqni yuklab olish", callback_data="download_audio_action"),
        InlineKeyboardButton("➕ Guruhga qo'shish ⤴️", url="https://t.me/OsonYukla_UzBot?startgroup=true")
    )
    return keyboard

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("👋 **Xush kelibsiz!**\n\nLink yuboring yoki qo'shiq nomini yozing.", parse_mode="Markdown")

@dp.message_handler()
async def process_message(message: types.Message):
    user_text = message.text
    msg = await message.answer("🔍 Qidirilmoqda...")

    if user_text.startswith("http"):
        # Video yuklash
        file_path = await asyncio.get_event_loop().run_in_executor(None, download_video, user_text)
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as video:
                await message.answer_video(video, caption="✅ @OsonYukla_UzBot orqali yuklandi!", reply_markup=main_keyboard())
            os.remove(file_path)
        else:
            await message.answer("❌ Videoni yuklab bo'lmadi.")
    else:
        # Musiqa qidirish
        file_path = await asyncio.get_event_loop().run_in_executor(None, download_audio, user_text)
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as audio:
                await message.answer_audio(audio, caption="✅ @OsonYukla_UzBot orqali topildi!", reply_markup=main_keyboard())
            os.remove(file_path)
        else:
            await message.answer("❌ Musiqa topilmadi.")
    
    await msg.delete()

if __name__ == '__main__':
    threading.Thread(target=run_static_server, daemon=True).start()
    executor.start_polling(dp, skip_updates=True)
