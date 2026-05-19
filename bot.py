import telebot
from telebot import types
import subprocess
import os
import time

# قراءة التوكن من متغيرات البيئة (لن نضعه مباشرة في الكود)
API_TOKEN = os.environ.get('7411288267:AAHF-tS9mlgqeCdhhgdcN_WCbgMSO6XaIY8')
if not API_TOKEN:
    raise ValueError("لم يتم العثور على BOT_TOKEN في متغيرات البيئة!")

bot = telebot.TeleBot(API_TOKEN)

# قواميس لتخزين البيانات المؤقتة
active_streams = {}
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🚀 بدء بث جديد")
    btn2 = types.KeyboardButton("🛑 إيقاف البث")
    markup.add(btn1, btn2)
    
    bot.reply_to(
        message,
        "🎬 أهلاً بك في بوت البث المباشر!\n\n"
        "الخطوات:\n"
        "1️⃣ اضغط (🚀 بدء بث جديد)\n"
        "2️⃣ أرسل رابط البث (m3u8/ts)\n"
        "3️⃣ أرسل Server URL\n"
        "4️⃣ أرسل Stream Key\n"
        "5️⃣ سيبدأ البث ✅",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "🚀 بدء بث جديد")
def ask_m3u8(message):
    chat_id = message.chat.id
    if chat_id in active_streams:
        bot.reply_to(message, "⚠️ لديك بث شغال حالياً! أوقفه أولاً.")
        return
    user_data[chat_id] = {}
    msg = bot.reply_to(message, "📎 أرسل رابط البث (m3u8 أو ts):")
    bot.register_next_step_handler(msg, save_m3u8)

def save_m3u8(message):
    chat_id = message.chat.id
    user_data[chat_id]['m3u8'] = message.text.strip()
    msg = bot.reply_to(
        message,
        "🖥️ الآن أرسل **Server URL** فقط\n\n"
        "مثال:\n"
        "`rtmps://dc4-1.rtmp.telegram.org/stream/`",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_server_url)

def save_server_url(message):
    chat_id = message.chat.id
    server_url = message.text.strip()
    if not server_url.endswith('/'):
        server_url += '/'
    user_data[chat_id]['server_url'] = server_url
    msg = bot.reply_to(message, "🔑 أرسل الآن **Stream Key** فقط:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, start_streaming)

def start_streaming(message):
    chat_id = message.chat.id
    stream_key = message.text.strip()
    server_url = user_data[chat_id]['server_url']
    m3u8_url = user_data[chat_id]['m3u8']
    full_rtmp_url = server_url + stream_key

    bot.reply_to(message, "⏳ جاري الاتصال وتشغيل البث... انتظر لحظة ⏳")

    command = [
        'ffmpeg',
        '-re',
        '-i', m3u8_url,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '44100',
        '-f', 'flv',
        full_rtmp_url
    ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_streams[chat_id] = process
        time.sleep(3)

        if process.poll() is None:
            bot.reply_to(message, "✅ **تم تشغيل البث بنجاح!** 🎉\n\n📺 اذهب إلى قناتك واضغط على **Start Live Stream**.", parse_mode="Markdown")
        else:
            stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
            error_msg = stderr_output[-400:] if len(stderr_output) > 400 else stderr_output
            bot.reply_to(message, f"❌ فشل الاتصال بالسيرفر:\n```{error_msg}```", parse_mode="Markdown")
            if chat_id in active_streams:
                del active_streams[chat_id]
    except FileNotFoundError:
        bot.reply_to(message, "❌ **FFmpeg غير مثبت على السيرفر!** راجع إعدادات Docker.")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ غير متوقع:\n`{str(e)}`", parse_mode="Markdown")
        if chat_id in active_streams:
            del active_streams[chat_id]

@bot.message_handler(func=lambda message: message.text == "🛑 إيقاف البث")
def stop_stream(message):
    chat_id = message.chat.id
    if chat_id in active_streams:
        process = active_streams[chat_id]
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        del active_streams[chat_id]
        bot.reply_to(message, "🛑 **تم إيقاف البث بنجاح!**")
    else:
        bot.reply_to(message, "ℹ️ لا يوجد بث شغال حالياً.")

print("✅ بوت البث يعمل الآن...")
bot.infinity_polling()
