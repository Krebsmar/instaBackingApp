# Instagram Auto-Liker Dockerfile
# Basis-Image: Python 3.11 slim für kleinere Größe
FROM python:3.11-slim

# Maintainer-Info
LABEL maintainer="Instagram Auto-Liker"
LABEL description="Automatisches Liken von Instagram Stories, Posts und Reels"

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Abhängigkeiten installieren (für Pillow und andere Bibliotheken)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY instagram_auto_liker.py .

# Datenverzeichnis erstellen
RUN mkdir -p /app/data

# Volume für persistente Daten (Session, Liked-Items)
VOLUME ["/app/data"]

# Umgebungsvariablen (können beim Container-Start überschrieben werden)
ENV IG_TARGET=""
ENV IG_USERNAME=""
ENV IG_PASSWORD=""
ENV IG_CYCLE="3600"
ENV IG_DATA_DIR="/app/data"
ENV IG_DELAY="2.0"
ENV IG_MAX_LIKES="50"
ENV PYTHONUNBUFFERED="1"

# Health-Check (optional)
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/data/session.json') else 1)" || exit 0

# Startbefehl
ENTRYPOINT ["python", "instagram_auto_liker.py"]

# Standard-CMD kann überschrieben werden
CMD []
