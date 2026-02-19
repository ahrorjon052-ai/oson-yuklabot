import logging
import os
import asyncio
import threading
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# --- SOZLAMALAR ---
# Tokeningizni bu yerga yozing yoki muhit o'zgaruvchisiga saqlang
API_TOKEN = os.environ.get('API_TOKEN', '8530462813:AAFxPrAjZyDG6Fgv_JMqy0XwMgnCKQp1Zv4')
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

if not os.path.exists('downloads'):
    os.makedirs('downloads')

# --- RENDER/HEROKU UCHUN SERVER ---
class StaticServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot ishlamoqda!")

def run_static_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), StaticServer)
    httpd.serve_forever()

# --- YUKLASH FUNKSIYALARI ---

def download_media(url_or_query, mode='video'):
    """
    mode: 'video' (link orqali) yoki 'audio' (ism orqali qidirish)
    """
    unique_id = str(uuid.uuid4())
    
    if mode == 'video':
        # Video yuklash sozlamalari
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f'downloads/{unique_id}.%(ext)s',
            'noplaylist': True,
            'quiet': True,
        }
    else:
        # Musiqa qidirish va yuklash (MP3)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'downloads/{unique_id}.%(ext)s',
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
            info = ydl.extract_info(url_or_query, download=True)
            if 'entries' in info: # Qidiruv natijasi bo'lsa
                info = info['entries'][0]
            
            filename = ydl.prepare_filename(info)
            if mode == 'audio':
                return filename.rsplit('.', 1)[0] + '.mp3'
            return filename
    except Exception as e:
        logging.error(f"Xatolik yuklashda: {e}")
        return None

# --- TUGMALAR ---
def get_main_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📢 Kanalimiz", url="https://t.me/your_channel"),
        InlineKeyboardButton("➕ Guruhga qo'shish", url="https://t.me/bot_username?startgroup=true")
    )
    return kb

# --- HANDLERLAR ---

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 **Xush kelibsiz!**\n\n"
        "Men orqali:\n"
        "1️⃣ **YouTube/Instagram/TikTok** linkini yuborib video yuklashingiz mumkin.\n"
        "2️⃣ **Qo'shiq nomi yoki ijrochi** ismini yozib musiqa topishingiz mumkin."
    )
    await message.reply(welcome_text, parse_mode="Markdown", reply_markup=get_main_kb())

@dp.message_handler()
async def handle_message(message: types.Message):
    user_input = message.text
    status_msg = await message.answer("⏳ Biroz kuting...")

    try:
        if user_input.startswith("http"):
            # Link bo'lsa video sifatida yuklaymiz
            file_path = await asyncio.get_event_loop().run_in_executor(None, download_media, user_input, 'video')
            
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as video:
                    await message.answer_video(video, caption="✅ Video yuklab olindi!")
                os.remove(file_path)
            else:
                await message.answer("❌ Videoni yuklashda xatolik yuz berdi (link noto'g'ri bo'lishi mumkin).")
        
        else:
            # Matn bo'lsa musiqa qidiramiz
            file_path = await asyncio.get_event_loop().run_in_executor(None, download_media, user_input, 'audio')
            
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as audio:
                    await message.answer_audio(audio, caption=f"🎵 {user_input} qidiruvi bo'yicha topildi.")
                os.remove(file_path)
            else:
                await message.answer("❌ Musiqa topilmadi.")

    except Exception as e:
        await message.answer("⚠️ Kutilmagan xatolik yuz berdi.")
        logging.error(e)
    
    finally:
        await status_msg.delete()

# --- ISHGA TUSHIRISH ---
if __name__ == '__main__':
    # Serverni alohida oqimda ishga tushirish
    threading.Thread(target=run_static_server, daemon=True).start()
    # Botni ishga tushirish
    executor.start_polling(dp, skip_updates=True)
