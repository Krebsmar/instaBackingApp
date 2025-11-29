# instaBackingApp

**Automatisierter Instagram-Backing-Service für Story- und Post-Interaktionen**

---

## 🎯 Projekt-Hintergrund

Dieses Projekt demonstriert einen modernen Entwicklungsansatz, bei dem **fundiertes Requirements Engineering und Architekturdesign** mit **AI-gestütztem Vibe Coding** kombiniert werden, um schnell einen funktionsfähigen MVP zu realisieren.

### Mein Beitrag: Anforderungen & Architektur

Die konzeptionelle Grundlage wurde von mir nach **ISAQB-Standards** erarbeitet:

- **Requirements Engineering** — Systematische Analyse funktionaler und nicht-funktionaler Anforderungen
- **Arc42-Architekturdokumentation** — Strukturierte Dokumentation aller Architekturentscheidungen
- **Qualitätsattribute** — Definition von Zuverlässigkeit, Sicherheit und Wartbarkeit
- **Technische Constraints** — Auswahl geeigneter Technologien und Patterns

Die vollständige Dokumentation findet sich in:
- [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) — Anforderungsspezifikation
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Architekturübersicht
- [`docs/arc42/`](docs/arc42/) — Arc42-Dokumentation

### Vibe Coding: Vom Konzept zum MVP

Basierend auf meiner Architektur- und Anforderungsdokumentation wurde **Vibe Coding** eingesetzt — ein AI-gestützter Entwicklungsansatz, bei dem:

1. **Klare Spezifikationen** als Input dienen (meine Dokumentation)
2. **AI-Assistenz** (Claude) den Code generiert und iterativ verfeinert
3. **Schnelle Feedback-Loops** Bugs direkt im Dialog beheben
4. **Der Entwickler** als Architekt und Reviewer fungiert

> **Ergebnis:** Ein produktionsreifer MVP in wenigen Stunden statt Tagen — ohne Kompromisse bei der Architekturqualität.

---

## ✨ Features

- **Multi-Account Support** — Mehrere Zielaccounts parallel überwachen
- **Story & Post Processing** — Automatisches Liken von Stories und Beiträgen
- **Intelligentes Rate-Limiting** — Konservative Limits mit Jitter für menschliches Verhalten
- **Session-Persistenz** — Login-Session überlebt Container-Neustarts
- **Exponentielles Backoff** — Automatische Fehlerbehandlung bei API-Limits
- **Structured Logging** — JSON-Logs für einfache Analyse
- **12-Factor Compliance** — Cloud-native Architektur

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                     instaBackingApp                          │
├─────────────────────────────────────────────────────────────┤
│  Scheduler (APScheduler)                                     │
│    ├── Main Processing Cycle (stündlich)                    │
│    └── Session Keep-Alive (30 Min)                          │
├─────────────────────────────────────────────────────────────┤
│  Services                                                    │
│    ├── ProcessingOrchestrator  → Koordiniert Abläufe        │
│    ├── InstagramClient         → API-Wrapper (instagrapi)   │
│    ├── StoryService            → Story-Verarbeitung         │
│    ├── PostService             → Post-Verarbeitung          │
│    ├── AccountManager          → Zielaccount-Verwaltung     │
│    └── RateLimiter             → Request-/Like-Limits       │
├─────────────────────────────────────────────────────────────┤
│  Repositories (Data Access Layer)                           │
│    ├── StoryRepository         │ SessionRepository          │
│    ├── PostRepository          │ RateLimitRepository        │
│    └── TargetAccountRepository                              │
├─────────────────────────────────────────────────────────────┤
│  Models (SQLAlchemy ORM)                                    │
│    Story │ Post │ SessionData │ RateLimitCounter │ Target   │
├─────────────────────────────────────────────────────────────┤
│  SQLite / PostgreSQL                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Repository klonen

```bash
git clone https://github.com/your-username/instaBackingApp.git
cd instaBackingApp
```

### 2. Konfiguration erstellen

```bash
cp .env.example .env
```

Bearbeite `.env` mit deinen Zugangsdaten:

```env
# Pflichtangaben
IG_USERNAME=dein_instagram_username
IG_PASSWORD=dein_instagram_passwort
IG_TARGET_USERNAMES=account1,account2,account3
```

### 3. Starten

```bash
docker-compose up -d
```

### 4. Logs beobachten

```bash
docker-compose logs -f
```

---

## ⚙️ Konfiguration

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `IG_USERNAME` | — | Instagram Benutzername (Pflicht) |
| `IG_PASSWORD` | — | Instagram Passwort (Pflicht) |
| `IG_TARGET_USERNAMES` | — | Kommaseparierte Zielaccounts (Pflicht) |
| `IG_CYCLE_SECONDS` | `3600` | Intervall zwischen Zyklen |
| `IG_MAX_LIKES_PER_HOUR` | `40` | Maximale Likes pro Stunde |
| `IG_MAX_LIKES_PER_DAY` | `800` | Maximale Likes pro Tag |
| `LOG_LEVEL` | `INFO` | Log-Level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | `json` | Log-Format (json, text) |

Siehe [`.env.example`](.env.example) für alle Optionen.

---

## 🛠️ Entwicklung

### Lokale Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Ausführen

```bash
python -m insta_backing_app
```

### Tests

```bash
pytest
```

---

## 📁 Projektstruktur

```
instaBackingApp/
├── src/insta_backing_app/
│   ├── __main__.py          # Entry Point
│   ├── config.py            # Pydantic Settings
│   ├── logging_config.py    # structlog Setup
│   ├── models/              # SQLAlchemy Models
│   ├── repositories/        # Data Access Layer
│   └── services/            # Business Logic
├── docs/
│   ├── REQUIREMENTS.md      # Anforderungsdokumentation
│   ├── ARCHITECTURE.md      # Architekturübersicht
│   └── arc42/               # Arc42-Dokumentation
├── Dockerfile               # Multi-Stage Build
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## 📊 Technologie-Stack

| Komponente | Technologie |
|------------|-------------|
| Sprache | Python 3.11+ |
| Instagram API | instagrapi |
| ORM | SQLAlchemy 2.x |
| Konfiguration | Pydantic Settings |
| Scheduler | APScheduler |
| Logging | structlog |
| Container | Docker |

---

## ⚠️ Disclaimer

Dieses Projekt dient Lern- und Demonstrationszwecken. Die Nutzung automatisierter Tools kann gegen die Instagram-Nutzungsbedingungen verstoßen. Verwende dieses Tool verantwortungsvoll und auf eigenes Risiko.

---

## 📄 Lizenz

MIT License — siehe [LICENSE](LICENSE)

---

## 🙏 Entstehung

**Konzept & Architektur:** Mario Krebs  
**Implementierung:** AI-gestütztes Vibe Coding mit Claude (Anthropic)

> *"Gute Architektur ist die Grundlage für erfolgreiche AI-Assistenz. Vibe Coding funktioniert am besten, wenn der Mensch das 'Was' und 'Warum' definiert — und die AI beim 'Wie' unterstützt."*

docker-compose down
docker volume rm insta-backing-data
docker rmi -f insta-backing-app:latest
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f