# Instagram Auto-Liker

Automatisches Liken von Stories, Posts und Reels eines Instagram-Zielaccounts.

## ⚠️ Wichtiger Hinweis

Die Nutzung dieses Scripts kann gegen Instagram's Nutzungsbedingungen verstoßen und zu Account-Sperrungen führen. Verwendung auf eigenes Risiko!

## Features

- Automatisches Liken von Posts und Reels
- Stories werden als "gesehen" markiert
- Speicherung bereits verarbeiteter Items (keine Duplikate)
- Session-Persistenz für weniger Logins
- Konfigurierbarer Zykluszeitraum
- Rate-Limiting zum Schutz vor Instagram-Sperren
- Docker-Support für einfaches Deployment

## Installation

### Option 1: Docker (Empfohlen)

```bash
# Repository klonen oder Dateien herunterladen
cd instagram_auto_liker

# .env Datei erstellen
cp .env.example .env
# .env Datei bearbeiten und Credentials eintragen

# Container starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

### Option 2: Direkt mit Python

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Programm starten
python instagram_auto_liker.py \
  -t zielaccount \
  -u mein_username \
  -p mein_passwort \
  -c 3600
```

## Konfiguration

### Kommandozeilenargumente

| Argument | Beschreibung | Standard |
|----------|--------------|----------|
| `-t, --target` | Zielaccount (ohne @) | - |
| `-u, --username` | Dein Instagram-Username | - |
| `-p, --password` | Dein Instagram-Passwort | - |
| `-c, --cycle` | Zykluszeit in Sekunden | 3600 |
| `--no-stories` | Stories nicht verarbeiten | false |
| `--no-posts` | Posts nicht verarbeiten | false |
| `--no-reels` | Reels nicht verarbeiten | false |
| `--delay` | Verzögerung zwischen Likes (Sek) | 2.0 |
| `--max-likes` | Max Likes pro Zyklus | 50 |
| `--data-dir` | Datenverzeichnis | ./data |
| `-v, --verbose` | Ausführliche Ausgabe | false |

### Umgebungsvariablen

| Variable | Beschreibung |
|----------|--------------|
| `IG_TARGET` | Zielaccount |
| `IG_USERNAME` | Dein Username |
| `IG_PASSWORD` | Dein Passwort |
| `IG_CYCLE` | Zykluszeit |
| `IG_DELAY` | Verzögerung |
| `IG_MAX_LIKES` | Max Likes |
| `IG_DATA_DIR` | Datenverzeichnis |

## Datenstruktur

```
data/
├── session.json      # Instagram-Session (für persistenten Login)
└── liked_items.json  # Liste bereits verarbeiteter Items
```

## Empfohlene Einstellungen

Für sicheren Betrieb empfehlen wir:

- **Zykluszeit**: Mindestens 1800 Sekunden (30 Min)
- **Verzögerung**: Mindestens 2 Sekunden zwischen Likes
- **Max Likes**: Nicht mehr als 50 pro Zyklus

## Troubleshooting

### Zwei-Faktor-Authentifizierung (2FA)

Falls 2FA aktiviert ist, muss diese temporär deaktiviert werden oder ein App-spezifisches Passwort verwendet werden.

### Challenge Required

Instagram kann bei verdächtigen Aktivitäten eine Verifizierung anfordern. In diesem Fall:

1. Im Browser bei Instagram einloggen
2. Verifizierung abschließen
3. Script neu starten

### Rate Limiting

Bei zu vielen Likes kann Instagram den Account temporär sperren. Erhöhe in diesem Fall:

- Die Zykluszeit (`--cycle`)
- Die Verzögerung (`--delay`)
- Reduziere Max Likes (`--max-likes`)

## Lizenz

MIT License - Verwendung auf eigenes Risiko.
