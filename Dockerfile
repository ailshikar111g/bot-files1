FROM python:3.10-slim

# تثبيت FFmpeg من مستودعات دبيان الرسمية
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# إعداد مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات وتثبيته
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود البوت
COPY bot.py .

# أمر التشغيل
CMD ["python", "bot.py"]
