# Koristimo Python 3.11 na slim Debian bazi
FROM python:3.11-slim

# Instaliramo sistemske ovisnosti:
# - libgl1, libglib2.0-0: OpenCV potrebuje ovo za prikaz slika
# - fonts-noto-color-emoji: emoji font (zamjena za Windows seguiemj.ttf)
# - libusb-1.0-0, v4l-utils: pristup web kameri unutar containera
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    fonts-noto-color-emoji \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# Radni direktorij unutar containera
WORKDIR /app

# Kopiramo requirements.txt prvi (Docker cache optimizacija)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiramo sav kod i model fajlove
COPY . .

# Kreiramo direktorij za fotografije
RUN mkdir -p photos

# Pokretanje aplikacije
CMD ["python3", "main.py"]
