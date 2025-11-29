# Instagram Story Liker - Architektur

## 1. Architekturübersicht

### 1.1 Architekturentscheidungen (ADRs)

#### ADR-001: Datenbank-Wahl
- **Kontext**: Persistenz für Story- und Beitrags-Datensätze benötigt
- **Entscheidung**: SQLite als Default, PostgreSQL als Option
- **Begründung**: 
  - SQLite: Zero-Config, File-basiert, ideal für Single-Instance
  - PostgreSQL: Skalierbar, wenn mehrere Instanzen benötigt
- **Konsequenzen**: SQLAlchemy als ORM für Abstraktion

#### ADR-002: Scheduling-Ansatz
- **Kontext**: Regelmäßige Ausführung des Abruf-Zyklus
- **Entscheidung**: APScheduler (in-process)
- **Begründung**: 
  - Kein externer Cron-Daemon nötig
  - Graceful Shutdown einfacher
  - Konfigurierbare Intervalle zur Laufzeit
- **Alternativen verworfen**: 
  - Cron: Externe Abhängigkeit
  - Celery: Overkill für Single-Task

#### ADR-003: Logging-Strategie
- **Kontext**: 12-Factor verlangt Logs als Event-Streams
- **Entscheidung**: Strukturiertes JSON-Logging nach stdout
- **Begründung**: 
  - Container-native (Docker logs)
  - Parsing durch Log-Aggregatoren (Loki, ELK)
  - Kein File-Management im Container

#### ADR-004: Session-Management
- **Kontext**: Instagram-Sessions müssen Container-Restarts überleben
- **Entscheidung**: Session in Datenbank speichern + Keep-Alive
- **Begründung**:
  - Konsistent mit 12-Factor (Stateless Processes)
  - Keine separaten Session-Files
  - Keep-Alive verhindert Session-Ablauf
  - Device-Fingerprint bleibt konsistent

#### ADR-005: Rate-Limiting Strategie
- **Kontext**: Instagram hat strikte Rate-Limits, Überschreitung führt zu Sperren
- **Entscheidung**: Sliding-Window Counter in DB + Jitter + Backoff
- **Begründung**:
  - Counter persistent (überlebt Restarts)
  - Jitter simuliert menschliches Verhalten
  - Exponentielles Backoff bei Fehlern
- **Konsequenzen**: Etwas langsamere Verarbeitung, aber sicherer

#### ADR-006: Multi-Account Verarbeitung
- **Kontext**: Mehrere Zielaccounts sollen unterstützt werden
- **Entscheidung**: Sequentielle Verarbeitung mit Delays
- **Begründung**:
  - Einfacher zu implementieren als parallel
  - Bessere Kontrolle über Rate-Limits
  - Delays zwischen Accounts wirken natürlicher
- **Alternativen verworfen**:
  - Parallele Verarbeitung: Komplexes Rate-Limit-Management

#### ADR-007: Trennung Stories vs. Beiträge
- **Kontext**: Stories sind temporär (24h), Beiträge permanent
- **Entscheidung**: Separate Tabellen mit unterschiedlicher Cleanup-Logik
- **Begründung**:
  - Klare Trennung der Lifecycle
  - Stories: Auto-Cleanup nach 24h
  - Posts: Kein Auto-Cleanup (permanent)
- **Konsequenzen**: Zwei Services, zwei Repositories

---

## 2. C4-Modell

### 2.1 Context Diagram (Level 1)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         System Context                               │
└─────────────────────────────────────────────────────────────────────┘

                           ┌─────────────┐
                           │   Betreiber │
                           │   (Person)  │
                           └──────┬──────┘
                                  │ Konfiguriert via
                                  │ ENV / docker-compose
                                  ▼
┌─────────────┐           ┌──────────────────┐           ┌─────────────┐
│  Instagram  │◄─────────►│  Story Liker     │           │  Monitoring │
│  Platform   │  API      │  Service         │──────────►│  (Optional) │
│  (External) │  Calls    │  [Container]     │  Metrics  │  Prometheus │
└─────────────┘           └────────┬─────────┘           └─────────────┘
                                   │
                                   │ Logs (stdout)
                                   ▼
                          ┌─────────────────┐
                          │  Log Collector  │
                          │  (Loki/Docker)  │
                          └─────────────────┘
```

### 2.2 Container Diagram (Level 2)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Host (dein Server)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                 story-liker Container                        │   │
│   │  ┌───────────────────────────────────────────────────────┐  │   │
│   │  │                    Python Application                  │  │   │
│   │  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │  │   │
│   │  │  │  Scheduler  │  │   Core      │  │  Instagram   │  │  │   │
│   │  │  │ (APScheduler)│  │   Logic     │  │   Client     │  │  │   │
│   │  │  │             │──►│             │──►│ (instagrapi) │  │  │   │
│   │  │  └─────────────┘  └──────┬──────┘  └──────┬───────┘  │  │   │
│   │  │                          │                 │          │  │   │
│   │  │                          ▼                 │          │  │   │
│   │  │                   ┌─────────────┐          │          │  │   │
│   │  │                   │  Repository │          │          │  │   │
│   │  │                   │   (SQLAlchemy)         │          │  │   │
│   │  │                   └──────┬──────┘          │          │  │   │
│   │  └──────────────────────────┼─────────────────┼──────────┘  │   │
│   │                             │                 │              │   │
│   └─────────────────────────────┼─────────────────┼──────────────┘   │
│                                 │                 │                   │
│         ┌───────────────────────┘                 │                   │
│         │                                         │                   │
│         ▼                                         ▼                   │
│   ┌───────────┐                          ┌───────────────┐           │
│   │  Volume   │                          │   Instagram   │           │
│   │  /data    │                          │   API         │           │
│   │           │                          │   (External)  │           │
│   │ stories.db│                          └───────────────┘           │
│   └───────────┘                                                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Component Diagram (Level 3)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Application Components                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  main.py                                                            │
│  ┌──────────────────┐                                               │
│  │  Entrypoint      │  - Konfiguration laden                        │
│  │                  │  - DI Container aufbauen                      │
│  │                  │  - Scheduler starten                          │
│  │                  │  - Signal Handler registrieren                │
│  └────────┬─────────┘                                               │
└───────────┼─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  config.py                                                          │
│  ┌──────────────────┐                                               │
│  │  Settings        │  - Pydantic BaseSettings                      │
│  │  (12-Factor)     │  - Validierung                                │
│  │                  │  - ENV-Variablen Mapping                      │
│  │                  │  - Rate-Limit Defaults                        │
│  │                  │  - Target Account Liste                       │
│  └──────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  services/                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  StoryService    │  │  PostService     │  │  InstagramClient │  │
│  │                  │  │                  │  │                  │  │
│  │  - fetch_stories │  │  - fetch_posts   │  │  - login()       │  │
│  │  - process_story │  │  - process_post  │  │  - get_stories() │  │
│  │  - like_story    │  │  - like_post     │  │  - get_medias()  │  │
│  └────────┬─────────┘  └────────┬─────────┘  │  - like_story()  │  │
│           │                     │            │  - like_media()  │  │
│           │                     │            └────────┬─────────┘  │
│           │                     │                     │            │
│  ┌────────┴─────────────────────┴─────────────────────┘            │
│  │                                                                  │
│  │  ┌──────────────────┐  ┌──────────────────┐                     │
│  │  │  RateLimiter     │  │  SessionManager  │                     │
│  │  │                  │  │                  │                     │
│  │  │  - check_limit() │  │  - load_session()│                     │
│  │  │  - increment()   │  │  - save_session()│                     │
│  │  │  - get_delay()   │  │  - keep_alive()  │                     │
│  │  │  - wait_jitter() │  │  - refresh()     │                     │
│  │  └────────┬─────────┘  └────────┬─────────┘                     │
│  │           │                     │                                │
│  │  ┌────────┴─────────┐  ┌────────┴─────────┐                     │
│  │  │  CleanupService  │  │  AccountManager  │                     │
│  │  │                  │  │                  │                     │
│  │  │  - cleanup_old() │  │  - sync_accounts │                     │
│  │  │  (nur Stories!)  │  │  - get_enabled() │                     │
│  │  └──────────────────┘  └──────────────────┘                     │
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  repositories/                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  StoryRepository │  │  PostRepository  │  │ SessionRepository│  │
│  │                  │  │                  │  │                  │  │
│  │  - get_by_pk()   │  │  - get_by_pk()   │  │  - get_session() │  │
│  │  - create()      │  │  - create()      │  │  - save_session()│  │
│  │  - update()      │  │  - update()      │  │                  │  │
│  │  - delete_old()  │  │  (kein delete!)  │  │                  │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│           │                     │                     │            │
│  ┌────────┴─────────┐  ┌────────┴─────────────────────┘            │
│  │RateLimitRepository│ │ TargetAccountRepo │                        │
│  │                  │  │                  │                        │
│  │  - get_counter() │  │  - get_enabled() │                        │
│  │  - increment()   │  │  - update_check()│                        │
│  │  - reset_window()│  │  - sync_from_cfg │                        │
│  └──────────────────┘  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  models/                                                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐ │
│  │  Story       │ │  Post        │ │  Session     │ │ RateLimit  │ │
│  │  (SQLAlchemy)│ │  (SQLAlchemy)│ │  (SQLAlchemy)│ │  Counter   │ │
│  │              │ │              │ │              │ │            │ │
│  │  - story_pk  │ │  - media_pk  │ │  - username  │ │  - type    │ │
│  │  - created_at│ │  - media_type│ │  - session   │ │  - count   │ │
│  │  - liked     │ │  - created_at│ │  - device    │ │  - window  │ │
│  │  - liked_at  │ │  - liked     │ │  - updated_at│ │            │ │
│  └──────────────┘ │  - liked_at  │ └──────────────┘ └────────────┘ │
│                   └──────────────┘                                  │
│  ┌──────────────┐                                                   │
│  │TargetAccount │                                                   │
│  │              │                                                   │
│  │  - username  │                                                   │
│  │  - enabled   │                                                   │
│  │  - last_check│                                                   │
│  └──────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Deployment-Architektur

### 3.1 Docker Host Deployment

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Docker Host                                 │
│                      (dein Server/Homelab)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  docker-compose.yml                                                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                                                                │  │
│  │  services:                                                     │  │
│  │    story-liker:                                                │  │
│  │      image: story-liker:latest                                 │  │
│  │      restart: unless-stopped                                   │  │
│  │      env_file: .env                                            │  │
│  │      volumes:                                                  │  │
│  │        - story-data:/app/data                                  │  │
│  │      healthcheck:                                              │  │
│  │        test: ["CMD", "python", "-c", "..."]                    │  │
│  │      logging:                                                  │  │
│  │        driver: json-file                                       │  │
│  │        options:                                                │  │
│  │          max-size: "10m"                                       │  │
│  │          max-file: "3"                                         │  │
│  │                                                                │  │
│  │  volumes:                                                      │  │
│  │    story-data:                                                 │  │
│  │                                                                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Volumes:                                                            │
│  ┌─────────────────┐                                                │
│  │ story-data      │  /var/lib/docker/volumes/story-data/_data     │
│  │                 │                                                │
│  │  └── data/      │                                                │
│  │       ├── stories.db    (SQLite Datenbank)                      │
│  │       └── session.json  (Instagram Session Backup)              │
│  └─────────────────┘                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Netzwerk-Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Network Architecture                           │
└─────────────────────────────────────────────────────────────────────┘

    Internet
        │
        │ HTTPS (443)
        ▼
┌───────────────┐
│   Instagram   │
│   API         │
│   Servers     │
└───────┬───────┘
        │
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│  Docker Host                                                       │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  bridge network (default)                                    │  │
│  │                                                              │  │
│  │     ┌─────────────────┐                                     │  │
│  │     │  story-liker    │                                     │  │
│  │     │  Container      │                                     │  │
│  │     │                 │ ──► Outbound HTTPS zu Instagram     │  │
│  │     │  (kein Port     │                                     │  │
│  │     │   exposed)      │                                     │  │
│  │     └─────────────────┘                                     │  │
│  │                                                              │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘

Hinweis: Der Container benötigt KEINE eingehenden Ports.
         Nur ausgehende HTTPS-Verbindungen zu Instagram.
```

---

## 4. Sequenzdiagramme

### 4.1 Story-Verarbeitungs-Zyklus

```
┌─────────┐     ┌─────────────┐     ┌───────────┐     ┌──────────┐     ┌───────────┐
│Scheduler│     │StoryService │     │IG Client  │     │Repository│     │  Database │
└────┬────┘     └──────┬──────┘     └─────┬─────┘     └────┬─────┘     └─────┬─────┘
     │                 │                  │                │                 │
     │  trigger()      │                  │                │                 │
     │────────────────►│                  │                │                 │
     │                 │                  │                │                 │
     │                 │  get_stories()   │                │                 │
     │                 │─────────────────►│                │                 │
     │                 │                  │                │                 │
     │                 │                  │ API Call       │                 │
     │                 │                  │───────────────────────────────►  │
     │                 │                  │◄───────────────────────────────  │
     │                 │                  │                │                 │
     │                 │  List[Story]     │                │                 │
     │                 │◄─────────────────│                │                 │
     │                 │                  │                │                 │
     │                 │ ┌────────────────────────────────────────────────┐ │
     │                 │ │ loop [for each story]                          │ │
     │                 │ │                │                │                │ │
     │                 │ │ get_by_pk()    │                │                │ │
     │                 │ │────────────────────────────────►│                │ │
     │                 │ │                │                │  SELECT        │ │
     │                 │ │                │                │───────────────►│ │
     │                 │ │                │                │◄───────────────│ │
     │                 │ │ Story|None     │                │                │ │
     │                 │ │◄────────────────────────────────│                │ │
     │                 │ │                │                │                │ │
     │                 │ │ alt [Story not found]           │                │ │
     │                 │ │ │              │                │                │ │
     │                 │ │ │ like_story() │                │                │ │
     │                 │ │ │─────────────►│                │                │ │
     │                 │ │ │              │ API Call       │                │ │
     │                 │ │ │              │─────────────────────────────►   │ │
     │                 │ │ │              │◄─────────────────────────────   │ │
     │                 │ │ │ True         │                │                │ │
     │                 │ │ │◄─────────────│                │                │ │
     │                 │ │ │              │                │                │ │
     │                 │ │ │ create()     │                │                │ │
     │                 │ │ │────────────────────────────────►               │ │
     │                 │ │ │              │                │  INSERT        │ │
     │                 │ │ │              │                │───────────────►│ │
     │                 │ │ │              │                │◄───────────────│ │
     │                 │ │ └──────────────┴────────────────┴────────────────┘ │
     │                 │ └────────────────────────────────────────────────────┘
     │                 │                  │                │                 │
     │  done           │                  │                │                 │
     │◄────────────────│                  │                │                 │
     │                 │                  │                │                 │
```

### 4.2 Cleanup-Prozess

```
┌─────────┐     ┌──────────────┐     ┌───────────┐     ┌──────────┐
│Scheduler│     │CleanupService│     │Repository │     │ Database │
└────┬────┘     └──────┬───────┘     └─────┬─────┘     └────┬─────┘
     │                 │                   │                │
     │  trigger()      │                   │                │
     │────────────────►│                   │                │
     │                 │                   │                │
     │                 │  delete_older_than(24h)            │
     │                 │──────────────────►│                │
     │                 │                   │                │
     │                 │                   │  DELETE WHERE  │
     │                 │                   │  liked=true    │
     │                 │                   │  AND           │
     │                 │                   │  created_at <  │
     │                 │                   │  now()-24h     │
     │                 │                   │───────────────►│
     │                 │                   │                │
     │                 │                   │  rows_deleted  │
     │                 │                   │◄───────────────│
     │                 │                   │                │
     │                 │  count: int       │                │
     │                 │◄──────────────────│                │
     │                 │                   │                │
     │  done           │                   │                │
     │◄────────────────│                   │                │
     │                 │                   │                │
```

---

## 5. 12-Factor Mapping

```
┌─────────────────────────────────────────────────────────────────────┐
│                    12-Factor App Implementation                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────┬────────────────────────────────────────────────────────────┐
│ Factor  │ Implementation                                             │
├─────────┼────────────────────────────────────────────────────────────┤
│    I    │ Git Repository (GitHub/GitLab)                             │
│         │ └── story-liker/                                           │
│         │     ├── src/                                               │
│         │     ├── tests/                                             │
│         │     ├── Dockerfile                                         │
│         │     └── docker-compose.yml                                 │
├─────────┼────────────────────────────────────────────────────────────┤
│   II    │ pyproject.toml / requirements.txt                          │
│         │ └── instagrapi, sqlalchemy, pydantic, apscheduler         │
├─────────┼────────────────────────────────────────────────────────────┤
│   III   │ Pydantic Settings                                          │
│         │ └── class Settings(BaseSettings):                          │
│         │         ig_username: str                                   │
│         │         ig_password: SecretStr                             │
│         │         database_url: str = "sqlite:///data/stories.db"   │
├─────────┼────────────────────────────────────────────────────────────┤
│   IV    │ Database als attached resource                             │
│         │ └── DATABASE_URL=postgresql://user:pass@db:5432/stories   │
├─────────┼────────────────────────────────────────────────────────────┤
│    V    │ Multi-Stage Dockerfile                                     │
│         │ └── Build → Test → Release (slim image)                    │
├─────────┼────────────────────────────────────────────────────────────┤
│   VI    │ Stateless: Alle Daten in Datenbank                         │
│         │ └── Kein In-Memory State zwischen Zyklen                   │
├─────────┼────────────────────────────────────────────────────────────┤
│  VII    │ Health-Endpoint (optional)                                 │
│         │ └── HTTP :8080/health (wenn Monitoring gewünscht)          │
├─────────┼────────────────────────────────────────────────────────────┤
│  VIII   │ Scale via Container-Replicas                               │
│         │ └── docker-compose scale story-liker=N                     │
│         │     (Achtung: Rate-Limiting bei >1)                        │
├─────────┼────────────────────────────────────────────────────────────┤
│   IX    │ Graceful Shutdown                                          │
│         │ └── signal.signal(SIGTERM, shutdown_handler)               │
├─────────┼────────────────────────────────────────────────────────────┤
│    X    │ Docker für Dev, Test, Prod                                 │
│         │ └── Identisches Image in allen Umgebungen                  │
├─────────┼────────────────────────────────────────────────────────────┤
│   XI    │ Structured Logging nach stdout                             │
│         │ └── {"timestamp": "...", "level": "INFO", "msg": "..."}   │
├─────────┼────────────────────────────────────────────────────────────┤
│  XII    │ CLI Commands für Admin-Tasks                               │
│         │ └── python -m story_liker migrate                          │
│         │ └── python -m story_liker cleanup --force                  │
└─────────┴────────────────────────────────────────────────────────────┘
```

---

## 6. Projektstruktur

```
story-liker/
├── src/
│   └── story_liker/
│       ├── __init__.py
│       ├── __main__.py              # Entrypoint
│       ├── config.py                # Pydantic Settings + Rate-Limits
│       ├── logging_config.py        # JSON Logging Setup
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py              # SQLAlchemy Base
│       │   ├── story.py             # Story Model
│       │   ├── post.py              # Post Model (Beiträge)
│       │   ├── session.py           # Session Model
│       │   ├── rate_limit.py        # RateLimitCounter Model
│       │   └── target_account.py    # TargetAccount Model
│       │
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── story_repository.py
│       │   ├── post_repository.py
│       │   ├── session_repository.py
│       │   ├── rate_limit_repository.py
│       │   └── target_account_repository.py
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   ├── instagram_client.py  # Wrapper für instagrapi
│       │   ├── story_service.py     # Story-Verarbeitung
│       │   ├── post_service.py      # Beitrags-Verarbeitung
│       │   ├── cleanup_service.py   # Story-Cleanup (nicht Posts!)
│       │   ├── rate_limiter.py      # Rate-Limit Management
│       │   ├── session_manager.py   # Session Keep-Alive
│       │   └── account_manager.py   # Multi-Account Management
│       │
│       └── cli/
│           ├── __init__.py
│           └── commands.py          # Admin Commands
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_story_service.py
│   ├── test_post_service.py
│   ├── test_rate_limiter.py
│   └── test_cleanup_service.py
│
├── docs/
│   ├── REQUIREMENTS.md
│   └── ARCHITECTURE.md
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

---

## 7. Technologie-Entscheidungen

| Komponente | Technologie | Version | Begründung |
|------------|-------------|---------|------------|
| Runtime | Python | 3.11+ | Performance, Type Hints |
| Instagram API | instagrapi | >=2.0 | Aktiv gepflegt, vollständig |
| ORM | SQLAlchemy | 2.x | Standard, async-fähig |
| Config | Pydantic | 2.x | Validation, Settings |
| Scheduling | APScheduler | 3.x | In-Process, flexibel |
| Logging | structlog | 24.x | JSON, Processors |
| Container | Python:3.11-slim | - | Minimal, sicher |
| DB (Default) | SQLite | 3.x | Zero-Config |
| DB (Optional) | PostgreSQL | 15+ | Skalierbar |
