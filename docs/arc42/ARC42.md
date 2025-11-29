# Instagram Auto-Liker - Arc42 Architekturdokumentation

**Version:** 1.0  
**Stand:** November 2025  
**Status:** Draft

---

# 1. Einführung und Ziele

## 1.1 Aufgabenstellung

Der Instagram Auto-Liker ist ein automatisierter Dienst, der Stories und Beiträge von konfigurierbaren Instagram-Zielaccounts abruft und automatisch liked. Der Dienst läuft als Container auf einem Docker-Host und folgt den 12-Factor-App-Prinzipien.

### Wesentliche Features

| Feature | Beschreibung |
|---------|--------------|
| Multi-Account Support | Verarbeitung mehrerer Zielaccounts (1..n) |
| Story-Verarbeitung | Abruf, Like und temporäre Persistenz (24h Cleanup) |
| Beitrags-Verarbeitung | Abruf, Like und permanente Persistenz |
| Rate-Limiting | Einhaltung der Instagram API-Limits |
| Session-Management | Persistente Sessions zur Vermeidung von Re-Logins |

## 1.2 Qualitätsziele

| Priorität | Qualitätsziel | Beschreibung |
|-----------|---------------|--------------|
| 1 | Zuverlässigkeit | Der Dienst muss stabil laufen und Instagram Rate-Limits einhalten |
| 2 | Wartbarkeit | Klare Struktur, 12-Factor Compliance, einfache Konfiguration |
| 3 | Betreibbarkeit | Container-native, strukturierte Logs, Health-Checks |
| 4 | Sicherheit | Keine Credentials im Code, Session-Persistenz |
| 5 | Erweiterbarkeit | Einfaches Hinzufügen neuer Zielaccounts |

## 1.3 Stakeholder

| Rolle | Erwartungshaltung |
|-------|-------------------|
| Betreiber | Einfache Installation, minimaler Wartungsaufwand, stabile Ausführung |
| Entwickler | Klare Architektur, testbarer Code, gute Dokumentation |
| Instagram | Einhaltung der Nutzungsbedingungen und Rate-Limits |

---

# 2. Randbedingungen

## 2.1 Technische Randbedingungen

| Randbedingung | Beschreibung |
|---------------|--------------|
| Programmiersprache | Python 3.11+ |
| Instagram API | instagrapi Bibliothek (Private API) |
| Container | OCI-konformes Image (Docker/Podman) |
| Datenbank | SQLite (Default) oder PostgreSQL |
| Laufzeitumgebung | Docker-Host mit persistentem Volume |

## 2.2 Organisatorische Randbedingungen

| Randbedingung | Beschreibung |
|---------------|--------------|
| 12-Factor App | Alle 12 Faktoren müssen eingehalten werden |
| Konfiguration | Ausschließlich über Umgebungsvariablen |
| Logging | JSON-strukturiert nach stdout |
| Deployment | Docker Compose auf privatem Host |

## 2.3 Konventionen

| Konvention | Beschreibung |
|------------|--------------|
| Code Style | PEP 8, Type Hints |
| Dokumentation | Arc42, Markdown |
| Versionierung | Semantic Versioning |
| Branching | Git Flow |

---

# 3. Kontextabgrenzung

## 3.1 Fachlicher Kontext

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Fachlicher Kontext                             │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │    Betreiber    │
                              │    (Mensch)     │
                              └────────┬────────┘
                                       │
                          Konfiguriert │ Zielaccounts,
                          Credentials, │ Intervalle
                                       ▼
┌─────────────────┐            ┌───────────────────┐
│  Zielaccounts   │            │                   │
│  (Instagram     │◄───────────│  Instagram        │
│   Profile)      │  Likes     │  Auto-Liker       │
│                 │            │                   │
│  - Stories      │            │  Verarbeitet:     │
│  - Beiträge     │            │  - Stories        │
│  - Reels        │            │  - Beiträge       │
└─────────────────┘            │  - Reels          │
                               │                   │
                               └─────────┬─────────┘
                                         │
                                         │ Logs, Metriken
                                         ▼
                               ┌─────────────────┐
                               │   Monitoring    │
                               │   (Optional)    │
                               └─────────────────┘
```

### Fachliche Schnittstellen

| Nachbarsystem | Input | Output |
|---------------|-------|--------|
| Instagram Platform | Stories, Beiträge, Reels | Likes |
| Betreiber | Konfiguration (ENV) | Logs, Status |
| Monitoring | - | Metriken, Health-Status |

## 3.2 Technischer Kontext

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Technischer Kontext                             │
└─────────────────────────────────────────────────────────────────────────┘

                                Internet
                                    │
                                    │ HTTPS/443
                                    ▼
                          ┌─────────────────────┐
                          │   Instagram API     │
                          │   (i.instagram.com) │
                          └──────────┬──────────┘
                                     │
                                     │ Private API
                                     │ (instagrapi)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Docker Host                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  story-liker Container                                             │  │
│  │                                                                    │  │
│  │  ┌─────────────────┐      ┌─────────────────┐                     │  │
│  │  │  Python App     │─────►│  SQLite DB      │                     │  │
│  │  │  (Port: keine)  │      │  (Volume Mount) │                     │  │
│  │  └────────┬────────┘      └─────────────────┘                     │  │
│  │           │                                                        │  │
│  │           │ stdout/stderr                                          │  │
│  │           ▼                                                        │  │
│  │  ┌─────────────────┐                                              │  │
│  │  │  Docker Logs    │                                              │  │
│  │  └─────────────────┘                                              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Technische Schnittstellen

| Schnittstelle | Technologie | Protokoll | Beschreibung |
|---------------|-------------|-----------|--------------|
| Instagram API | instagrapi | HTTPS | Private Mobile API |
| Datenbank | SQLAlchemy | SQLite/PostgreSQL | Persistenz |
| Konfiguration | Pydantic | ENV | 12-Factor Config |
| Logging | structlog | stdout (JSON) | Event-Stream |

---

# 4. Lösungsstrategie

## 4.1 Technologieentscheidungen

| Entscheidung | Technologie | Begründung |
|--------------|-------------|------------|
| Sprache | Python 3.11+ | Requirement, instagrapi-Kompatibilität |
| Instagram API | instagrapi | Aktiv gepflegt, vollständige API-Abdeckung |
| ORM | SQLAlchemy 2.x | Standard, typsicher, DB-agnostisch |
| Config | Pydantic 2.x | Validation, Settings, ENV-Parsing |
| Scheduling | APScheduler | In-Process, konfigurierbar, Graceful Shutdown |
| Logging | structlog | JSON-Ausgabe, Processor-Pipeline |
| Container | python:3.11-slim | Minimales Image, sicher |

## 4.2 Architekturansatz

| Aspekt | Ansatz |
|--------|--------|
| Architekturstil | Modularer Monolith mit Clean Architecture |
| Schichten | Services → Repositories → Models |
| Konfiguration | 12-Factor via Pydantic Settings |
| Persistenz | Repository Pattern mit SQLAlchemy |
| Scheduling | APScheduler mit konfigurierbaren Jobs |

## 4.3 Qualitätssicherung

| Qualitätsziel | Maßnahme |
|---------------|----------|
| Zuverlässigkeit | Rate-Limiting, Exponentielles Backoff, Session-Persistenz |
| Wartbarkeit | Clean Architecture, Type Hints, strukturierte Logs |
| Testbarkeit | Dependency Injection, Repository Pattern |
| Betreibbarkeit | Docker, Health-Checks, JSON-Logs |

---

# 5. Bausteinsicht

## 5.1 Ebene 1: Whitebox Gesamtsystem

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Instagram Auto-Liker                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                         Application Layer                          │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │ │
│  │  │    main      │  │    config    │  │      scheduler           │ │ │
│  │  │  (Entrypoint)│  │  (Settings)  │  │    (APScheduler)         │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                          Service Layer                             │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │ │
│  │  │ StoryService │  │ PostService  │  │    InstagramClient       │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘ │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │ │
│  │  │ RateLimiter  │  │SessionManager│  │    CleanupService        │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘ │ │
│  │  ┌──────────────┐                                                 │ │
│  │  │AccountManager│                                                 │ │
│  │  └──────────────┘                                                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                        Repository Layer                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │ │
│  │  │StoryRepo     │  │PostRepo      │  │    SessionRepo           │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘ │ │
│  │  ┌──────────────┐  ┌──────────────┐                               │ │
│  │  │RateLimitRepo │  │TargetAccRepo │                               │ │
│  │  └──────────────┘  └──────────────┘                               │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                          Model Layer                               │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│ │
│  │  │  Story   │ │   Post   │ │ Session  │ │RateLimit │ │ Target   ││ │
│  │  │          │ │          │ │          │ │ Counter  │ │ Account  ││ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────┐
                          │    SQLite DB    │
                          │   (persistent)  │
                          └─────────────────┘
```

### Bausteine Ebene 1

| Baustein | Verantwortung |
|----------|---------------|
| Application Layer | Initialisierung, Konfiguration, Scheduling |
| Service Layer | Geschäftslogik, API-Kommunikation, Rate-Limiting |
| Repository Layer | Datenzugriff, CRUD-Operationen |
| Model Layer | Datenstrukturen, ORM-Mapping |

## 5.2 Ebene 2: Service Layer (Whitebox)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            Service Layer                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  InstagramClient                                                 │    │
│  │  ┌─────────────────────────────────────────────────────────────┐│    │
│  │  │  - login()           : Authentifizierung                    ││    │
│  │  │  - get_user_stories(): Stories abrufen                      ││    │
│  │  │  - get_user_medias() : Beiträge abrufen                     ││    │
│  │  │  - story_like()      : Story liken                          ││    │
│  │  │  - media_like()      : Beitrag liken                        ││    │
│  │  │  - get_user_id()     : User-ID ermitteln                    ││    │
│  │  └─────────────────────────────────────────────────────────────┘│    │
│  │                              │                                   │    │
│  │                    ┌─────────┴─────────┐                        │    │
│  │                    ▼                   ▼                        │    │
│  │            ┌───────────────┐   ┌───────────────┐                │    │
│  │            │  instagrapi   │   │ SessionManager│                │    │
│  │            │  (Library)    │   │               │                │    │
│  │            └───────────────┘   └───────────────┘                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐                     │
│  │  StoryService        │  │  PostService         │                     │
│  │  ──────────────────  │  │  ──────────────────  │                     │
│  │  - process_stories() │  │  - process_posts()   │                     │
│  │  - like_story()      │  │  - like_post()       │                     │
│  │  - is_already_liked()│  │  - is_already_liked()│                     │
│  │                      │  │                      │                     │
│  │  Cleanup: JA (24h)   │  │  Cleanup: NEIN       │                     │
│  └──────────┬───────────┘  └──────────┬───────────┘                     │
│             │                         │                                  │
│             └────────────┬────────────┘                                  │
│                          │                                               │
│                          ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  RateLimiter                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────┐│    │
│  │  │  - check_can_proceed()  : Prüft ob Limit erlaubt            ││    │
│  │  │  - increment_counter()  : Zähler erhöhen                    ││    │
│  │  │  - wait_with_jitter()   : Delay mit Zufallsvariation        ││    │
│  │  │  - apply_backoff()      : Exponentielles Backoff            ││    │
│  │  │  - reset_if_expired()   : Zeitfenster-Reset                 ││    │
│  │  └─────────────────────────────────────────────────────────────┘│    │
│  │                                                                  │    │
│  │  Counter: requests_hour, likes_hour, likes_day                  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐                     │
│  │  SessionManager      │  │  CleanupService      │                     │
│  │  ──────────────────  │  │  ──────────────────  │                     │
│  │  - load_session()    │  │  - cleanup_stories() │                     │
│  │  - save_session()    │  │  - get_expired()     │                     │
│  │  - keep_alive()      │  │                      │                     │
│  │  - refresh()         │  │  NUR für Stories!    │                     │
│  │  - handle_challenge()│  │  Posts bleiben.      │                     │
│  └──────────────────────┘  └──────────────────────┘                     │
│                                                                          │
│  ┌──────────────────────┐                                               │
│  │  AccountManager      │                                               │
│  │  ──────────────────  │                                               │
│  │  - get_enabled()     │                                               │
│  │  - sync_from_config()│                                               │
│  │  - update_last_check │                                               │
│  └──────────────────────┘                                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Bausteinbeschreibungen

#### InstagramClient
| Aspekt | Beschreibung |
|--------|--------------|
| Verantwortung | Wrapper für instagrapi, API-Kommunikation |
| Schnittstellen | instagrapi.Client, SessionManager |
| Qualitätsmerkmale | Fehlerbehandlung, Retry-Logic |

#### StoryService
| Aspekt | Beschreibung |
|--------|--------------|
| Verantwortung | Story-Verarbeitung, Like-Logik, Cleanup-Trigger |
| Schnittstellen | InstagramClient, StoryRepository, RateLimiter |
| Besonderheit | Stories werden nach 24h gelöscht |

#### PostService
| Aspekt | Beschreibung |
|--------|--------------|
| Verantwortung | Beitrags-Verarbeitung (Photo, Album, Reel) |
| Schnittstellen | InstagramClient, PostRepository, RateLimiter |
| Besonderheit | Beiträge werden NICHT gelöscht |

#### RateLimiter
| Aspekt | Beschreibung |
|--------|--------------|
| Verantwortung | Einhaltung der Instagram Rate-Limits |
| Counter | requests_hour, likes_hour, likes_day |
| Features | Jitter, exponentielles Backoff |

#### SessionManager
| Aspekt | Beschreibung |
|--------|--------------|
| Verantwortung | Session-Persistenz, Keep-Alive |
| Schnittstellen | SessionRepository, InstagramClient |
| Features | Auto-Refresh, Challenge-Handling |

---

# 6. Laufzeitsicht

## 6.1 Story-Verarbeitungs-Zyklus

```
┌─────────┐  ┌─────────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐
│Scheduler│  │AccountMgr   │  │StoryService│ │RateLimiter│  │IG Client │
└────┬────┘  └──────┬──────┘  └─────┬─────┘  └─────┬─────┘  └────┬─────┘
     │              │               │              │              │
     │ trigger()    │               │              │              │
     │─────────────►│               │              │              │
     │              │               │              │              │
     │              │ get_enabled_accounts()       │              │
     │              │──────────────►│              │              │
     │              │               │              │              │
     │              │ loop [for each account]      │              │
     │              │ │             │              │              │
     │              │ │ process_stories(account)   │              │
     │              │ │────────────►│              │              │
     │              │ │             │              │              │
     │              │ │             │ check_can_proceed()         │
     │              │ │             │─────────────►│              │
     │              │ │             │◄─────────────│              │
     │              │ │             │ true         │              │
     │              │ │             │              │              │
     │              │ │             │ get_user_stories()          │
     │              │ │             │─────────────────────────────►
     │              │ │             │◄─────────────────────────────
     │              │ │             │ List[Story]  │              │
     │              │ │             │              │              │
     │              │ │             │ loop [for each story]       │
     │              │ │             │ │            │              │
     │              │ │             │ │ exists_in_db?             │
     │              │ │             │ │ if not:    │              │
     │              │ │             │ │   like_story()            │
     │              │ │             │ │   ─────────────────────────►
     │              │ │             │ │   ◄─────────────────────────
     │              │ │             │ │   wait_with_jitter()      │
     │              │ │             │ │   ─────────►│              │
     │              │ │             │ │   ◄─────────│ (delay)     │
     │              │ │             │ │   increment_counter()     │
     │              │ │             │ │   ─────────►│              │
     │              │ │             │ │   save_to_db()            │
     │              │ │             │ │            │              │
     │              │ │             │              │              │
     │              │ │ delay_between_accounts     │              │
     │              │ │◄───────────│              │              │
     │              │              │              │              │
     │ done         │              │              │              │
     │◄─────────────│              │              │              │
```

## 6.2 Session Keep-Alive

```
┌─────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────┐
│Scheduler│  │SessionManager│  │IG Client  │  │ Database │
└────┬────┘  └──────┬───────┘  └─────┬─────┘  └────┬─────┘
     │              │                │              │
     │ keep_alive() │                │              │
     │─────────────►│                │              │
     │              │                │              │
     │              │ lightweight_request()         │
     │              │───────────────►│              │
     │              │                │ (API Call)   │
     │              │◄───────────────│              │
     │              │ success        │              │
     │              │                │              │
     │              │ update_session()              │
     │              │─────────────────────────────►│
     │              │◄─────────────────────────────│
     │              │                │              │
     │ done         │                │              │
     │◄─────────────│                │              │
```

## 6.3 Rate-Limit Erreicht

```
┌─────────┐  ┌───────────┐  ┌───────────┐
│Service  │  │RateLimiter│  │  Logger   │
└────┬────┘  └─────┬─────┘  └─────┬─────┘
     │             │              │
     │ check_can_proceed()        │
     │────────────►│              │
     │             │              │
     │             │ (limit erreicht)
     │             │              │
     │             │ log_warning()│
     │             │─────────────►│
     │             │              │ {"level":"WARN",
     │             │              │  "msg":"Rate limit reached",
     │             │              │  "counter":"likes_hour",
     │             │              │  "current":40,
     │             │              │  "max":40}
     │             │              │
     │ false       │              │
     │◄────────────│              │
     │             │              │
     │ (skip processing)          │
     │             │              │
     │ calculate_wait_time()      │
     │────────────►│              │
     │             │              │
     │ wait_seconds│              │
     │◄────────────│              │
```

---

# 7. Verteilungssicht

## 7.1 Infrastruktur

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Docker Host                                    │
│                        (Homelab/Server)                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Docker Engine                                                     │  │
│  │                                                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  Container: story-liker                                      │  │  │
│  │  │  Image: story-liker:latest                                   │  │  │
│  │  │  Restart: unless-stopped                                     │  │  │
│  │  │                                                              │  │  │
│  │  │  ┌────────────────────────────────────────────────────────┐ │  │  │
│  │  │  │  Python 3.11 Runtime                                    │ │  │  │
│  │  │  │                                                         │ │  │  │
│  │  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐│ │  │  │
│  │  │  │  │ Application │  │  instagrapi │  │   SQLAlchemy    ││ │  │  │
│  │  │  │  │   Code      │  │  (Library)  │  │    (ORM)        ││ │  │  │
│  │  │  │  └─────────────┘  └─────────────┘  └─────────────────┘│ │  │  │
│  │  │  └────────────────────────────────────────────────────────┘ │  │  │
│  │  │                              │                               │  │  │
│  │  │                              │ Volume Mount                  │  │  │
│  │  │                              ▼                               │  │  │
│  │  │                    /app/data ────────────────────────┐      │  │  │
│  │  └─────────────────────────────────────────────────────┼──────┘  │  │
│  │                                                         │         │  │
│  │  ┌─────────────────────────────────────────────────────┼──────┐  │  │
│  │  │  Volume: story-liker-data                           │      │  │  │
│  │  │                                                     ▼      │  │  │
│  │  │  /var/lib/docker/volumes/story-liker-data/_data           │  │  │
│  │  │                                                            │  │  │
│  │  │    ├── stories.db        (SQLite Datenbank)               │  │  │
│  │  │    └── logs/             (Optional: Log-Rotation)          │  │  │
│  │  │                                                            │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │                                                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  Netzwerk: Outbound HTTPS (443) zu i.instagram.com                      │
│  Ports: Keine eingehenden Ports erforderlich                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 7.2 Docker Compose Konfiguration

```yaml
version: '3.8'

services:
  story-liker:
    image: story-liker:latest
    container_name: story-liker
    restart: unless-stopped
    
    environment:
      - IG_USERNAME=${IG_USERNAME}
      - IG_PASSWORD=${IG_PASSWORD}
      - IG_TARGET_USERNAMES=${IG_TARGET_USERNAMES}
      - IG_CYCLE_SECONDS=${IG_CYCLE_SECONDS:-3600}
      - DATABASE_URL=sqlite:///data/stories.db
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - LOG_FORMAT=json
    
    volumes:
      - story-liker-data:/app/data
    
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 5m
      timeout: 10s
      retries: 3
    
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  story-liker-data:
```

## 7.3 Deployment-Anforderungen

| Anforderung | Spezifikation |
|-------------|---------------|
| Docker Version | 20.10+ |
| RAM | Minimum 256 MB |
| Disk | 100 MB + Datenbank |
| Netzwerk | Ausgehend HTTPS (443) |
| Architektur | amd64, arm64 |

---

# 8. Querschnittliche Konzepte

## 8.1 Persistenz

### Datenbankschema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Datenbankschema                                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────┐       ┌─────────────────────┐
│      stories        │       │       posts         │
├─────────────────────┤       ├─────────────────────┤
│ PK story_pk VARCHAR │       │ PK media_pk VARCHAR │
│    story_id VARCHAR │       │    media_id VARCHAR │
│    target_username  │       │    media_type INT   │
│    created_at TS    │       │    product_type     │
│    liked BOOL       │       │    target_username  │
│    liked_at TS      │       │    created_at TS    │
│    processed_at TS  │       │    liked BOOL       │
└─────────────────────┘       │    liked_at TS      │
         │                    │    processed_at TS  │
         │                    │    caption_text     │
         │                    └─────────────────────┘
         │                             │
         └──────────────┬──────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │   target_accounts   │
              ├─────────────────────┤
              │ PK username VARCHAR │
              │    user_id VARCHAR  │
              │    enabled BOOL     │
              │    process_stories  │
              │    process_posts    │
              │    last_story_check │
              │    last_post_check  │
              │    error_count      │
              └─────────────────────┘

┌─────────────────────┐       ┌─────────────────────┐
│      sessions       │       │ rate_limit_counters │
├─────────────────────┤       ├─────────────────────┤
│ PK id INT           │       │ PK id INT           │
│    username VARCHAR │       │    counter_type     │
│    session_data TEXT│       │    count INT        │
│    device_settings  │       │    window_start TS  │
│    created_at TS    │       │    window_end TS    │
│    updated_at TS    │       └─────────────────────┘
│    last_login_at    │
│    last_request_at  │
└─────────────────────┘
```

### Persistenzstrategie

| Entity | Persistenz | Cleanup |
|--------|------------|---------|
| Story | Temporär | Nach 24h wenn liked=true |
| Post | Permanent | Kein automatischer Cleanup |
| Session | Permanent | Manuell oder bei Neulogin |
| RateLimitCounter | Temporär | Nach Window-Ablauf |
| TargetAccount | Permanent | Bei Config-Sync |

## 8.2 Rate-Limiting

### Konfigurierbare Limits

```python
class RateLimitConfig:
    # Delays (Sekunden)
    delay_between_requests: float = 2.0
    delay_between_likes: float = 3.0
    delay_between_accounts: float = 10.0
    delay_jitter_percent: int = 30
    
    # Stündliche Limits
    max_requests_per_hour: int = 150
    max_likes_per_hour: int = 40
    max_story_views_per_hour: int = 150
    
    # Tägliche Limits
    max_likes_per_day: int = 800
    
    # Backoff
    backoff_base_seconds: int = 60
    backoff_max_seconds: int = 3600
    backoff_multiplier: float = 2.0
```

### Jitter-Implementierung

```
Base Delay: 3.0 Sekunden
Jitter: ±30%

Berechnung:
  min_delay = base * (1 - jitter/100) = 3.0 * 0.7 = 2.1s
  max_delay = base * (1 + jitter/100) = 3.0 * 1.3 = 3.9s
  actual_delay = random.uniform(2.1, 3.9)
```

### Exponentielles Backoff

```
Fehler 1: wait = 60s * 2^0 = 60s
Fehler 2: wait = 60s * 2^1 = 120s
Fehler 3: wait = 60s * 2^2 = 240s
Fehler 4: wait = 60s * 2^3 = 480s
...
Maximum: 3600s (1 Stunde)
```

## 8.3 Session-Management

### Session-Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Session Lifecycle                                 │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────┐
    │  START  │
    └────┬────┘
         │
         ▼
    ┌─────────────────┐     Ja    ┌─────────────────┐
    │ Session in DB?  │──────────►│ Load Session    │
    └────────┬────────┘           └────────┬────────┘
             │ Nein                        │
             ▼                             │
    ┌─────────────────┐                    │
    │  Fresh Login    │                    │
    └────────┬────────┘                    │
             │                             │
             ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │  Save Session   │           │ Validate Session│
    └────────┬────────┘           └────────┬────────┘
             │                             │
             │                             ▼
             │                    ┌─────────────────┐
             │                    │ Session Valid?  │
             │                    └────────┬────────┘
             │                      Ja │      │ Nein
             │                         │      │
             │                         │      ▼
             │                         │  ┌─────────────────┐
             │                         │  │  Re-Login       │
             │                         │  └────────┬────────┘
             │                         │           │
             ▼                         ▼           │
    ┌─────────────────────────────────────────────────────┐
    │                    RUNNING                           │
    │                                                      │
    │   ┌──────────────┐    ┌──────────────────────────┐  │
    │   │  Keep-Alive  │    │  Process Cycle           │  │
    │   │  (30 min)    │    │  (konfigurierbar)        │  │
    │   └──────────────┘    └──────────────────────────┘  │
    │                                                      │
    └──────────────────────────────────────────────────────┘
             │
             │ SIGTERM / Challenge / Fatal Error
             ▼
    ┌─────────────────┐
    │  Save Session   │
    └────────┬────────┘
             │
             ▼
    ┌─────────┐
    │   END   │
    └─────────┘
```

### Device Fingerprint

```python
session_config = {
    "device_name": "Samsung Galaxy S21",
    "app_version": "269.0.0.18.75",
    "android_version": "31",
    "android_release": "12",
    "dpi": "420dpi",
    "resolution": "1080x2400",
    "manufacturer": "Samsung",
    "model": "SM-G991B"
}
```

## 8.4 Logging

### Log-Format (JSON)

```json
{
  "timestamp": "2025-11-29T10:15:30.123Z",
  "level": "INFO",
  "logger": "story_liker.services.story_service",
  "message": "Story processed successfully",
  "context": {
    "story_pk": "3152048407587698594",
    "target_username": "example_user",
    "action": "liked",
    "cycle_id": "abc123"
  }
}
```

### Log-Levels

| Level | Verwendung |
|-------|------------|
| DEBUG | Detaillierte Diagnose, API-Responses |
| INFO | Normale Operationen, verarbeitete Items |
| WARNING | Rate-Limits erreicht, Retry-Situationen |
| ERROR | Fehler die Verarbeitung stoppen |
| CRITICAL | Fatale Fehler, Shutdown erforderlich |

## 8.5 Fehlerbehandlung

### Exception-Hierarchie

```
BaseException
└── Exception
    └── StoryLikerException (Custom Base)
        ├── ConfigurationError
        ├── InstagramError
        │   ├── LoginError
        │   ├── ChallengeRequired
        │   ├── RateLimitExceeded
        │   └── SessionExpired
        ├── PersistenceError
        │   ├── DatabaseConnectionError
        │   └── DataIntegrityError
        └── ServiceError
            ├── AccountNotFoundError
            └── ProcessingError
```

### Retry-Strategie

| Exception | Retry | Backoff | Max Retries |
|-----------|-------|---------|-------------|
| RateLimitExceeded | Ja | Exponentiell | 5 |
| SessionExpired | Ja | Linear (5 min) | 3 |
| NetworkError | Ja | Exponentiell | 3 |
| ChallengeRequired | Nein | - | - |
| LoginError | Ja | Linear (5 min) | 3 |

---

# 9. Architekturentscheidungen

## ADR-001: Datenbank-Wahl

| Aspekt | Beschreibung |
|--------|--------------|
| Status | Akzeptiert |
| Kontext | Persistenz für Stories, Posts, Sessions, Counter |
| Entscheidung | SQLite als Default, PostgreSQL als Option |
| Begründung | SQLite: Zero-Config, File-basiert, ideal für Single-Instance |
| Konsequenzen | SQLAlchemy als ORM für Abstraktion |
| Alternativen | PostgreSQL (für Multi-Instance), Redis (für Counter) |

## ADR-002: Scheduling-Ansatz

| Aspekt | Beschreibung |
|--------|--------------|
| Status | Akzeptiert |
| Kontext | Regelmäßige Ausführung des Verarbeitungs-Zyklus |
| Entscheidung | APScheduler (in-process) |
| Begründung | Kein externer Daemon, Graceful Shutdown, konfigurierbar |
| Konsequenzen | Scheduler ist Teil der Anwendung |
| Alternativen | Cron (extern), Celery (Overkill) |

## ADR-003: Session-Persistenz

| Aspekt | Beschreibung |
|--------|--------------|
| Status | Akzeptiert |
| Kontext | Instagram-Sessions müssen Restarts überleben |
| Entscheidung | Session in Datenbank speichern |
| Begründung | 12-Factor konform, kein File-Handling |
| Konsequenzen | Session-Repository, verschlüsselte Speicherung |
| Alternativen | Session-File im Volume |

## ADR-004: Rate-Limiting Implementierung

| Aspekt | Beschreibung |
|--------|--------------|
| Status | Akzeptiert |
| Kontext | Instagram Rate-Limits einhalten |
| Entscheidung | Sliding Window Counter mit Jitter und Backoff |
| Begründung | Menschliches Verhalten simulieren, Limits nicht ausreizen |
| Konsequenzen | Counter in DB, konfigurierbare Limits |
| Alternativen | Token Bucket, Feste Delays |

## ADR-005: Multi-Account Strategie

| Aspekt | Beschreibung |
|--------|--------------|
| Status | Akzeptiert |
| Kontext | Mehrere Zielaccounts verarbeiten |
| Entscheidung | Sequentielle Verarbeitung mit Delays |
| Begründung | Einfach, Rate-Limits leichter einzuhalten |
| Konsequenzen | Längere Zykluszeiten bei vielen Accounts |
| Alternativen | Parallele Verarbeitung (Rate-Limit Risiko) |

---

# 10. Qualitätsanforderungen

## 10.1 Qualitätsbaum

```
                            Qualität
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   Zuverlässigkeit        Wartbarkeit           Betreibbarkeit
        │                      │                      │
   ┌────┴────┐            ┌────┴────┐            ┌────┴────┐
   │         │            │         │            │         │
Rate-    Session      Modular-   Test-       Container  Logging
Limiting Persist.    ität       barkeit      native
```

## 10.2 Qualitätsszenarien

### QS-01: Rate-Limit Einhaltung

| Aspekt | Beschreibung |
|--------|--------------|
| Qualitätsmerkmal | Zuverlässigkeit |
| Szenario | Bei hoher Last werden Rate-Limits nicht überschritten |
| Stimulus | 100 neue Stories/Posts in einem Zyklus |
| Reaktion | System verarbeitet nur bis Limit, pausiert dann |
| Metrik | 0 HTTP 429 Responses |

### QS-02: Session-Persistenz

| Aspekt | Beschreibung |
|--------|--------------|
| Qualitätsmerkmal | Zuverlässigkeit |
| Szenario | Nach Container-Restart ist kein Re-Login nötig |
| Stimulus | Container wird neu gestartet |
| Reaktion | Session wird geladen, Verarbeitung startet |
| Metrik | 0 Login-Events nach Restart |

### QS-03: Logging-Qualität

| Aspekt | Beschreibung |
|--------|--------------|
| Qualitätsmerkmal | Betreibbarkeit |
| Szenario | Fehler kann anhand von Logs diagnostiziert werden |
| Stimulus | Story-Like schlägt fehl |
| Reaktion | Log enthält story_pk, error, timestamp, context |
| Metrik | Zeit bis zur Diagnose < 5 Minuten |

### QS-04: Graceful Shutdown

| Aspekt | Beschreibung |
|--------|--------------|
| Qualitätsmerkmal | Betreibbarkeit |
| Szenario | Container-Stop führt nicht zu Datenverlust |
| Stimulus | SIGTERM während Verarbeitung |
| Reaktion | Aktueller API-Call wird abgeschlossen, Session gespeichert |
| Metrik | Exit Code 0, keine korrupten Daten |

---

# 11. Risiken und technische Schulden

## 11.1 Risiken

| ID | Risiko | Wahrscheinlichkeit | Auswirkung | Mitigation |
|----|--------|-------------------|------------|------------|
| R1 | Instagram Rate-Limiting | Hoch | Temporäre Sperre | Konservative Limits, Jitter |
| R2 | Account-Sperre | Mittel | Service-Ausfall | Session-Persistenz, "menschliches" Verhalten |
| R3 | API-Änderungen | Mittel | Funktionsverlust | instagrapi Updates verfolgen |
| R4 | 2FA-Challenge | Mittel | Login blockiert | Admin-Alerting, manuelle Intervention |
| R5 | Session-Ablauf | Mittel | Re-Login nötig | Keep-Alive Requests |
| R6 | Shadowban | Niedrig | Likes unsichtbar | Konservative Limits |

## 11.2 Technische Schulden

| ID | Schuld | Priorität | Aufwand | Beschreibung |
|----|--------|-----------|---------|--------------|
| TD1 | Keine Encryption | Mittel | 4h | Session-Daten verschlüsseln |
| TD2 | Keine Metriken | Niedrig | 8h | Prometheus Exporter |
| TD3 | Kein Admin-UI | Niedrig | 16h | Web-Interface für Status |

---

# 12. Glossar

| Begriff | Definition |
|---------|------------|
| Story | Temporärer Instagram-Inhalt (24h Lebensdauer) |
| Post/Beitrag | Permanenter Instagram-Inhalt |
| Reel | Kurzvideos (media_type=2, product_type=clips) |
| story_pk | Primary Key einer Story |
| media_pk | Primary Key eines Beitrags |
| taken_at | Zeitstempel der Content-Erstellung |
| instagrapi | Python-Bibliothek für Instagram Private API |
| Rate-Limit | Maximale Anzahl API-Calls pro Zeiteinheit |
| Jitter | Zufällige Variation bei Delays |
| Backoff | Exponentiell steigende Wartezeit bei Fehlern |
| Keep-Alive | Regelmäßige Requests zur Session-Erhaltung |
| Challenge | Instagram-Verifizierung (2FA, Captcha) |
| 12-Factor App | Methodik für Cloud-native Anwendungen |
| OCI | Open Container Initiative |
| Sliding Window | Rate-Limit Algorithmus mit gleitendem Zeitfenster |
