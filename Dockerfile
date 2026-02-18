# Python-ning yengil versiyasidan foydalanamiz
FROM python:3.10-slim

# Tizim yangilanishlari va FFmpeg-ni o'rnatish
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Ishchi papkani yaratish
WORKDIR /app

# Kutubxonalar ro'yxatini nusxalash va o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Barcha kodlarni konteynerga nusxalash
COPY . .

# Render beradigan PORT-ni ochish
EXPOSE 8080

# Oxirgi qatorni shunday yozing:
CMD ["python", "Oson Yukla Bot.py"]
