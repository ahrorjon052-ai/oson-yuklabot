FROM python:3.10-slim

# Tizimga FFmpeg o'rnatish (video/audio formatlash uchun shart)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodlarni nusxalash
COPY . .

# Portni ochish
EXPOSE 8080

# Botni ishga tushirish (Fayl nomi probel bilan bo'lsa qo'shtirnoq shart)
CMD ["python", "Oson Yukla Bot.py"]
