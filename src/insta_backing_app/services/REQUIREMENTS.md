# Instagram Story Liker - Anforderungsdokumentation

## 1. Projektübersicht

### 1.1 Projektziel
Entwicklung eines automatisierten Dienstes zum Abrufen und Liken von Instagram Stories und Beiträgen mehrerer Zielaccounts. Der Dienst läuft containerisiert auf einem Docker-Host und folgt den 12-Factor-App-Prinzipien.

### 1.2 Scope
- Automatisches Abrufen von Stories und Beiträgen mehrerer konfigurierbarer Zielaccounts
- Persistente Speicherung verarbeiteter Stories und Beiträge mit Metadaten
- Automatisches Liken neuer Stories und Beiträge
- Automatische Bereinigung abgelaufener Story-Datensätze (>24h)
- Beiträge werden persistent gespeichert (kein Cleanup)
- Einhaltung der Instagram Rate-Limits
- Optimales Session-Management zur Vermeidung von Re-Logins

---

## 2. Funktionale Anforderungen

### 2.1 Multi-Account Support (FA-001)
| ID | Anforderung |
|----|-------------|
| FA-001.1 | Das System MUSS eine Liste von Zielaccounts unterstützen (1..n) |
| FA-001.2 | Die Zielaccount-Liste MUSS via Konfiguration definierbar sein |
| FA-001.3 | Das System MUSS alle Zielaccounts sequentiell verarbeiten |
| FA-001.4 | Das System MUSS für jeden Zielaccount eigene Statistiken führen |
| FA-001.5 | Das Hinzufügen/Entfernen von Accounts SOLL ohne Neustart möglich sein |

### 2.2 Story-Verarbeitung (FA-002)
| ID | Anforderung |
|----|-------------|
| FA-002.1 | Das System MUSS Stories aller Zielaccounts abrufen können |
| FA-002.2 | Das System MUSS sich mit eigenen Instagram-Credentials authentifizieren |
| FA-002.3 | Das System MUSS den Abruf in konfigurierbaren Intervallen durchführen |
| FA-002.4 | Das System MUSS das Erstellungsdatum (`taken_at`) jeder Story auslesen |
| FA-002.5 | Neue Stories MÜSSEN automatisch geliked werden |
| FA-002.6 | Story-Datensätze mit `liked=true` und `created_at > 24h` MÜSSEN gelöscht werden |

### 2.3 Beitrags-Verarbeitung (FA-003)
| ID | Anforderung |
|----|-------------|
| FA-003.1 | Das System MUSS Beiträge (Posts) aller Zielaccounts abrufen können |
| FA-003.2 | Das System MUSS Fotos (media_type=1) verarbeiten |
| FA-003.3 | Das System MUSS Alben/Karussells (media_type=8) verarbeiten |
| FA-003.4 | Das System MUSS Reels (media_type=2, product_type=clips) verarbeiten |
| FA-003.5 | Neue Beiträge MÜSSEN automatisch geliked werden |
| FA-003.6 | Beitrags-Datensätze DÜRFEN NICHT automatisch gelöscht werden (permanent) |
| FA-003.7 | Die Anzahl abzurufender Beiträge pro Account MUSS konfigurierbar sein |

### 2.4 Persistenz (FA-004)
| ID | Anforderung |
|----|-------------|
| FA-004.1 | Das System MUSS für jede neue Story einen Datensatz anlegen |
| FA-004.2 | Das System MUSS für jeden neuen Beitrag einen Datensatz anlegen |
| FA-004.3 | Story-Datensätze MÜSSEN enthalten: `story_pk`, `target_username`, `created_at`, `liked`, `liked_at` |
| FA-004.4 | Beitrags-Datensätze MÜSSEN enthalten: `media_pk`, `media_type`, `target_username`, `created_at`, `liked`, `liked_at` |
| FA-004.5 | Das System MUSS vor Verarbeitung prüfen, ob ein Datensatz bereits existiert |
| FA-004.6 | Die Persistenz MUSS Container-Neustarts überleben (Volume) |

### 2.5 Like-Logik (FA-005)
| ID | Anforderung |
|----|-------------|
| FA-005.1 | Das System MUSS neue Items (nicht in DB) automatisch liken |
| FA-005.2 | Das System MUSS nach erfolgreichem Like das Feld `liked=true` setzen |
| FA-005.3 | Das System DARF bereits gelikte Items NICHT erneut liken |
| FA-005.4 | Das System MUSS bei Like-Fehlern den Datensatz mit `liked=false` behalten |
| FA-005.5 | Das System SOLL fehlgeschlagene Likes im nächsten Zyklus erneut versuchen |

### 2.6 Datenbereinigung (FA-006)
| ID | Anforderung |
|----|-------------|
| FA-006.1 | Das System MUSS bei jedem Abruf prüfen, ob Story-Datensätze älter als 24h sind |
| FA-006.2 | Das System MUSS Story-Datensätze mit `liked=true` UND `created_at > 24h` löschen |
| FA-006.3 | Die 24h-Schwelle SOLL konfigurierbar sein |
| FA-006.4 | Beitrags-Datensätze DÜRFEN NICHT automatisch gelöscht werden |
| FA-006.5 | Das System SOLL ein manuelles Cleanup-Command für Beiträge bereitstellen |

---

## 3. Rate-Limiting Anforderungen

### 3.1 Instagram Rate-Limits (FA-007)

#### 3.1.1 Bekannte Instagram Rate-Limits (Stand: 2025)
| Aktion | Limit | Zeitraum | Empfohlenes Limit |
|--------|-------|----------|-------------------|
| API Requests (gesamt) | ~200 | pro Stunde | 150/h |
| Likes | ~60 | pro Stunde | 40/h |
| Likes | ~1000 | pro Tag | 800/Tag |
| Story Views | ~200 | pro Stunde | 150/h |
| User Info Requests | ~200 | pro Stunde | 100/h |
| Follow/Unfollow | ~60 | pro Stunde | nicht relevant |
| Comments | ~30 | pro Stunde | nicht relevant |
| DMs | ~50 | pro Tag | nicht relevant |

#### 3.1.2 Anforderungen
| ID | Anforderung |
|----|-------------|
| FA-007.1 | Das System MUSS alle Rate-Limits als Konfiguration unterstützen |
| FA-007.2 | Das System MUSS Delays zwischen API-Aufrufen einhalten |
| FA-007.3 | Das System MUSS Delays zwischen Likes einhalten |
| FA-007.4 | Das System MUSS tägliche Like-Limits pro Account tracken |
| FA-007.5 | Das System MUSS bei Erreichen des Limits den Zyklus pausieren |
| FA-007.6 | Das System SOLL bei HTTP 429 (Rate Limit) exponentielles Backoff anwenden |
| FA-007.7 | Das System SOLL "menschliches" Verhalten simulieren (variable Delays) |

#### 3.1.3 Rate-Limit Konfiguration
```yaml
rate_limits:
  # Delays (in Sekunden)
  delay_between_requests: 2.0      # Basis-Delay zwischen API-Calls
  delay_between_likes: 3.0         # Delay zwischen Like-Aktionen
  delay_between_accounts: 10.0     # Delay zwischen Zielaccounts
  delay_jitter_percent: 30         # Zufällige Variation (+/- 30%)
  
  # Stündliche Limits
  max_requests_per_hour: 150
  max_likes_per_hour: 40
  max_story_views_per_hour: 150
  
  # Tägliche Limits
  max_likes_per_day: 800
  
  # Backoff bei Fehlern
  backoff_base_seconds: 60         # Basis für exponentielles Backoff
  backoff_max_seconds: 3600        # Maximum Backoff (1 Stunde)
  backoff_multiplier: 2.0          # Multiplikator pro Retry
```

### 3.2 Rate-Limit Tracking (FA-008)
| ID | Anforderung |
|----|-------------|
| FA-008.1 | Das System MUSS API-Aufrufe pro Stunde zählen |
| FA-008.2 | Das System MUSS Likes pro Stunde zählen |
| FA-008.3 | Das System MUSS Likes pro Tag zählen |
| FA-008.4 | Die Zähler MÜSSEN nach Ablauf des Zeitraums zurückgesetzt werden |
| FA-008.5 | Die Zähler SOLLEN persistent gespeichert werden (Restart-sicher) |
| FA-008.6 | Das System SOLL aktuelle Auslastung loggen |

---

## 4. Session-Management Anforderungen

### 4.1 Session-Persistenz (FA-009)
| ID | Anforderung |
|----|-------------|
| FA-009.1 | Das System MUSS die Instagram-Session persistent speichern |
| FA-009.2 | Das System MUSS beim Start eine gespeicherte Session laden |
| FA-009.3 | Das System MUSS die Session nach jedem erfolgreichen API-Call aktualisieren |
| FA-009.4 | Das System MUSS Session-Daten in der Datenbank speichern (nicht als File) |
| FA-009.5 | Das System SOLL Session-Daten verschlüsselt speichern |

### 4.2 Session-Erhaltung (FA-010)
| ID | Anforderung |
|----|-------------|
| FA-010.1 | Das System MUSS Login nur durchführen, wenn keine gültige Session existiert |
| FA-010.2 | Das System MUSS bei `LoginRequired`-Exception Re-Login versuchen |
| FA-010.3 | Das System MUSS bei `ChallengeRequired` den Admin benachrichtigen |
| FA-010.4 | Das System SOLL den Device-Fingerprint konsistent halten |
| FA-010.5 | Das System SOLL den User-Agent konsistent halten |
| FA-010.6 | Das System SOLL regelmäßig "Keep-Alive" Requests durchführen |

### 4.3 Session-Konfiguration
```yaml
session:
  # Device Simulation
  device_name: "Samsung Galaxy S21"    # Konsistenter Device Name
  app_version: "269.0.0.18.75"         # Instagram App Version
  
  # Keep-Alive
  keepalive_interval_seconds: 1800     # Alle 30 Min einen Request
  keepalive_endpoint: "timeline_feed"  # Welcher Endpoint für Keep-Alive
  
  # Re-Login Verhalten
  max_login_attempts: 3
  login_retry_delay_seconds: 300       # 5 Minuten zwischen Login-Versuchen
  
  # Session Refresh
  session_refresh_interval_hours: 12   # Session-Daten alle 12h neu speichern
```

### 4.4 Challenge Handling (FA-011)
| ID | Anforderung |
|----|-------------|
| FA-011.1 | Das System MUSS bei 2FA-Challenge den Prozess pausieren |
| FA-011.2 | Das System SOLL bei Email-Challenge automatisch Code abrufen (optional) |
| FA-011.3 | Das System MUSS bei Challenge einen Alert/Notification senden |
| FA-011.4 | Das System SOLL einen manuellen Challenge-Resolution Endpoint bereitstellen |

---

## 5. Nicht-funktionale Anforderungen

### 5.1 12-Factor App Compliance (NFA-001)

| Factor | Anforderung | Umsetzung |
|--------|-------------|-----------|
| I. Codebase | Eine Codebase, viele Deployments | Git Repository |
| II. Dependencies | Explizite Deklaration | `requirements.txt` / `pyproject.toml` |
| III. Config | Konfiguration in Umgebungsvariablen | Alle Credentials und Settings via ENV |
| IV. Backing Services | Als angehängte Ressourcen | Datenbank als Service behandeln |
| V. Build, Release, Run | Strikte Trennung | Dockerfile + CI/CD |
| VI. Processes | Stateless Prozesse | Kein In-Memory State |
| VII. Port Binding | Services via Port exportieren | Health-Endpoint optional |
| VIII. Concurrency | Skalierung via Prozesse | Container-Replikation möglich |
| IX. Disposability | Schneller Start/Stop | Graceful Shutdown |
| X. Dev/Prod Parity | Umgebungen angleichen | Docker für alle Stages |
| XI. Logs | Als Event-Streams | stdout/stderr, JSON-Format |
| XII. Admin Processes | Als einmalige Prozesse | CLI-Commands für Admin-Tasks |

### 5.2 Container/OCI (NFA-002)
| ID | Anforderung |
|----|-------------|
| NFA-002.1 | Das System MUSS als OCI-konformes Container-Image bereitgestellt werden |
| NFA-002.2 | Das Image MUSS auf Docker/Podman lauffähig sein |
| NFA-002.3 | Das Image SOLL minimal sein (Alpine/Slim Base) |
| NFA-002.4 | Das Image MUSS als Non-Root User laufen |

### 5.3 Betrieb (NFA-003)
| ID | Anforderung |
|----|-------------|
| NFA-003.1 | Das System MUSS strukturierte Logs (JSON) nach stdout schreiben |
| NFA-003.2 | Das System SOLL einen Health-Check Endpoint bereitstellen |
| NFA-003.3 | Das System MUSS Graceful Shutdown unterstützen (SIGTERM) |
| NFA-003.4 | Das System SOLL Metriken für Monitoring bereitstellen |

### 5.4 Sicherheit (NFA-004)
| ID | Anforderung |
|----|-------------|
| NFA-004.1 | Credentials DÜRFEN NICHT im Image/Code gespeichert werden |
| NFA-004.2 | Die Instagram-Session SOLL persistent gespeichert werden |
| NFA-004.3 | Das System SOLL Rate-Limiting implementieren |

---

## 6. Technische Anforderungen

### 6.1 Technologie-Stack
| Komponente | Technologie | Begründung |
|------------|-------------|------------|
| Sprache | Python 3.11+ | Requirement, instagrapi-Kompatibilität |
| Instagram API | instagrapi | Requirement |
| Persistenz | SQLite / PostgreSQL | Leichtgewichtig oder skalierbar |
| Container Runtime | Docker/Podman | OCI-Konformität |
| Scheduling | APScheduler | Intervall-basierte Ausführung |

### 6.2 Umgebungsvariablen
| Variable | Beschreibung | Required | Default |
|----------|--------------|----------|---------|
| `IG_USERNAME` | Instagram Benutzername | Ja | - |
| `IG_PASSWORD` | Instagram Passwort | Ja | - |
| `IG_TARGET_USERNAMES` | Zielaccounts (kommasepariert) | Ja | - |
| `IG_CYCLE_SECONDS` | Abrufintervall in Sekunden | Nein | 3600 |
| `IG_CLEANUP_HOURS` | Schwelle für Story-Bereinigung | Nein | 24 |
| `IG_POSTS_AMOUNT` | Anzahl Beiträge pro Account | Nein | 20 |
| `DATABASE_URL` | Datenbankverbindung | Nein | sqlite:///data/stories.db |
| `LOG_LEVEL` | Logging-Level | Nein | INFO |
| `LOG_FORMAT` | Log-Format (json/text) | Nein | json |
| | | | |
| **Rate-Limit Konfiguration** | | | |
| `IG_DELAY_BETWEEN_REQUESTS` | Sekunden zwischen API-Calls | Nein | 2.0 |
| `IG_DELAY_BETWEEN_LIKES` | Sekunden zwischen Likes | Nein | 3.0 |
| `IG_DELAY_BETWEEN_ACCOUNTS` | Sekunden zwischen Accounts | Nein | 10.0 |
| `IG_DELAY_JITTER_PERCENT` | Zufällige Variation in % | Nein | 30 |
| `IG_MAX_LIKES_PER_HOUR` | Max Likes pro Stunde | Nein | 40 |
| `IG_MAX_LIKES_PER_DAY` | Max Likes pro Tag | Nein | 800 |
| `IG_MAX_REQUESTS_PER_HOUR` | Max API-Calls pro Stunde | Nein | 150 |
| | | | |
| **Session Konfiguration** | | | |
| `IG_SESSION_KEEPALIVE_SECONDS` | Keep-Alive Intervall | Nein | 1800 |
| `IG_SESSION_DEVICE_NAME` | Device für Fingerprint | Nein | auto |
| `IG_MAX_LOGIN_ATTEMPTS` | Max Login-Versuche | Nein | 3 |

---

## 7. Datenmodell

### 7.1 Entity: Story
```
┌─────────────────────────────────────────────────────────────────────┐
│ stories                                                             │
├─────────────────────────────────────────────────────────────────────┤
│ story_pk        : VARCHAR(64)   PRIMARY KEY                         │
│ story_id        : VARCHAR(128)  NOT NULL                            │
│ target_username : VARCHAR(64)   NOT NULL                            │
│ created_at      : TIMESTAMP     NOT NULL  -- taken_at von Instagram │
│ liked           : BOOLEAN       NOT NULL  DEFAULT false             │
│ liked_at        : TIMESTAMP     NULL                                │
│ processed_at    : TIMESTAMP     NOT NULL  DEFAULT now()             │
├─────────────────────────────────────────────────────────────────────┤
│ INDEX idx_stories_target (target_username)                          │
│ INDEX idx_stories_created_at (created_at)                           │
│ INDEX idx_stories_cleanup (liked, created_at)                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 Entity: Post (Beitrag)
```
┌─────────────────────────────────────────────────────────────────────┐
│ posts                                                               │
├─────────────────────────────────────────────────────────────────────┤
│ media_pk        : VARCHAR(64)   PRIMARY KEY                         │
│ media_id        : VARCHAR(128)  NOT NULL                            │
│ media_type      : INTEGER       NOT NULL  -- 1=Photo, 2=Video, 8=Album │
│ product_type    : VARCHAR(32)   NULL      -- feed, clips, igtv      │
│ target_username : VARCHAR(64)   NOT NULL                            │
│ created_at      : TIMESTAMP     NOT NULL  -- taken_at von Instagram │
│ liked           : BOOLEAN       NOT NULL  DEFAULT false             │
│ liked_at        : TIMESTAMP     NULL                                │
│ processed_at    : TIMESTAMP     NOT NULL  DEFAULT now()             │
│ caption_text    : TEXT          NULL      -- Optional: Caption      │
├─────────────────────────────────────────────────────────────────────┤
│ INDEX idx_posts_target (target_username)                            │
│ INDEX idx_posts_created_at (created_at)                             │
│ INDEX idx_posts_media_type (media_type)                             │
│ INDEX idx_posts_liked (liked)                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Entity: Session
```
┌─────────────────────────────────────────────────────────────────────┐
│ sessions                                                            │
├─────────────────────────────────────────────────────────────────────┤
│ id              : INTEGER       PRIMARY KEY AUTOINCREMENT           │
│ username        : VARCHAR(64)   UNIQUE NOT NULL                     │
│ session_data    : TEXT          NOT NULL  -- JSON (encrypted)       │
│ device_settings : TEXT          NULL      -- JSON Device Info       │
│ created_at      : TIMESTAMP     NOT NULL  DEFAULT now()             │
│ updated_at      : TIMESTAMP     NOT NULL                            │
│ last_login_at   : TIMESTAMP     NULL                                │
│ last_request_at : TIMESTAMP     NULL                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.4 Entity: RateLimitCounter
```
┌─────────────────────────────────────────────────────────────────────┐
│ rate_limit_counters                                                 │
├─────────────────────────────────────────────────────────────────────┤
│ id              : INTEGER       PRIMARY KEY AUTOINCREMENT           │
│ counter_type    : VARCHAR(32)   NOT NULL  -- 'likes_hour', 'likes_day', 'requests_hour' │
│ count           : INTEGER       NOT NULL  DEFAULT 0                 │
│ window_start    : TIMESTAMP     NOT NULL  -- Start des Zeitfensters │
│ window_end      : TIMESTAMP     NOT NULL  -- Ende des Zeitfensters  │
├─────────────────────────────────────────────────────────────────────┤
│ UNIQUE INDEX idx_counter_type (counter_type)                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.5 Entity: TargetAccount
```
┌─────────────────────────────────────────────────────────────────────┐
│ target_accounts                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ username        : VARCHAR(64)   PRIMARY KEY                         │
│ user_id         : VARCHAR(64)   NULL      -- Instagram User ID      │
│ enabled         : BOOLEAN       NOT NULL  DEFAULT true              │
│ process_stories : BOOLEAN       NOT NULL  DEFAULT true              │
│ process_posts   : BOOLEAN       NOT NULL  DEFAULT true              │
│ last_story_check: TIMESTAMP     NULL                                │
│ last_post_check : TIMESTAMP     NULL                                │
│ added_at        : TIMESTAMP     NOT NULL  DEFAULT now()             │
│ error_count     : INTEGER       NOT NULL  DEFAULT 0                 │
│ last_error      : TEXT          NULL                                │
├─────────────────────────────────────────────────────────────────────┤
│ INDEX idx_target_enabled (enabled)                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Use Cases

### 8.1 UC-001: Neue Story verarbeiten
```
Akteur:     Scheduler (Timer)
Vorbedingung: System ist authentifiziert, Rate-Limits nicht erreicht
Ablauf:
  1. Prüfe ob Rate-Limits erlauben (Requests, Likes)
  2. Für jeden aktivierten Zielaccount:
     a. Warte delay_between_accounts (mit Jitter)
     b. Rufe Stories des Zielaccounts ab
     c. Für jede Story:
        - Prüfe ob story_pk in Datenbank existiert
        - WENN nicht existiert:
          * Erstelle Datensatz (story_pk, created_at, liked=false)
          * Prüfe Like-Limit
          * Like die Story via API
          * Warte delay_between_likes (mit Jitter)
          * Setze liked=true, liked_at=now()
          * Inkrementiere Like-Counter
        - WENN existiert UND liked=true:
          * Keine Aktion
     d. Aktualisiere last_story_check für Account
Nachbedingung: Alle neuen Stories sind geliked und persistiert
```

### 8.2 UC-002: Neuen Beitrag verarbeiten
```
Akteur:     Scheduler (Timer)
Vorbedingung: System ist authentifiziert, Rate-Limits nicht erreicht
Ablauf:
  1. Prüfe ob Rate-Limits erlauben
  2. Für jeden aktivierten Zielaccount:
     a. Warte delay_between_accounts (mit Jitter)
     b. Rufe die letzten N Beiträge ab (konfigurierbar)
     c. Für jeden Beitrag (Photo, Album, Reel):
        - Prüfe ob media_pk in Datenbank existiert
        - WENN nicht existiert:
          * Erstelle Datensatz (media_pk, media_type, created_at, liked=false)
          * Prüfe Like-Limit
          * Like den Beitrag via API
          * Warte delay_between_likes (mit Jitter)
          * Setze liked=true, liked_at=now()
          * Inkrementiere Like-Counter
        - WENN existiert:
          * Keine Aktion (Beiträge werden NICHT gelöscht)
     d. Aktualisiere last_post_check für Account
Nachbedingung: Alle neuen Beiträge sind geliked und persistent gespeichert
```

### 8.3 UC-003: Story-Datensätze bereinigen
```
Akteur:     Scheduler (Timer)
Vorbedingung: Datenbank enthält Story-Datensätze
Ablauf:
  1. Ermittle alle Story-Datensätze mit liked=true UND created_at < (now - 24h)
  2. Lösche diese Datensätze
  3. Logge Anzahl gelöschter Datensätze
Nachbedingung: Keine Story-Datensätze älter als 24h in der Datenbank
Hinweis: Beiträge (posts) werden NICHT automatisch gelöscht!
```

### 8.4 UC-004: Rate-Limit erreicht
```
Akteur:     System (automatisch)
Vorbedingung: Like-Limit oder Request-Limit erreicht
Ablauf:
  1. System erkennt Limit-Überschreitung
  2. Logge Warning mit aktuellem Counter-Stand
  3. Berechne Wartezeit bis Limit-Reset
  4. Pausiere aktuellen Zyklus
  5. Setze Verarbeitung fort wenn Limit zurückgesetzt
Nachbedingung: Keine API-Calls während Limit-Überschreitung
```

### 8.5 UC-005: Session Keep-Alive
```
Akteur:     Scheduler (Timer, alle 30 Min)
Vorbedingung: Gültige Session existiert
Ablauf:
  1. Führe leichtgewichtigen API-Call durch (z.B. Timeline)
  2. Aktualisiere last_request_at in Session
  3. Speichere aktualisierte Session-Daten
Nachbedingung: Session bleibt aktiv, kein Re-Login nötig
```

### 8.6 UC-006: Re-Login nach Session-Ablauf
```
Akteur:     System (automatisch)
Vorbedingung: API gibt LoginRequired zurück
Ablauf:
  1. Logge Warning "Session abgelaufen"
  2. Lade gespeicherte Session-Daten
  3. Versuche Login mit Session-Daten
  4. WENN erfolgreich:
     - Aktualisiere Session in DB
     - Setze Verarbeitung fort
  5. WENN fehlgeschlagen:
     - Versuche Fresh-Login (max 3 Versuche)
     - WENN Challenge: Pausiere und benachrichtige Admin
Nachbedingung: Gültige Session oder Admin-Intervention erforderlich
```

### 8.7 UC-007: Graceful Shutdown
```
Akteur:     Container Runtime (SIGTERM)
Vorbedingung: System läuft
Ablauf:
  1. System empfängt SIGTERM
  2. Setze Shutdown-Flag
  3. Warte auf Abschluss des aktuellen API-Calls (max 30s)
  4. Speichere aktuelle Session
  5. Speichere Rate-Limit Counter
  6. Schließe Datenbankverbindung
  7. Prozess beendet mit Exit Code 0
Nachbedingung: Keine Datenverluste, sauberer Shutdown
```

### 8.8 UC-008: Neuen Zielaccount hinzufügen
```
Akteur:     Admin (via CLI oder Config-Reload)
Vorbedingung: System läuft
Ablauf:
  1. Account wird zu Konfiguration hinzugefügt
  2. System erkennt neuen Account (Config-Watch oder Restart)
  3. Erstelle Eintrag in target_accounts Tabelle
  4. Ermittle user_id via API
  5. Account wird im nächsten Zyklus verarbeitet
Nachbedingung: Neuer Account aktiv ohne Service-Unterbrechung
```

---

## 9. Abnahmekriterien

| ID | Kriterium | Prüfmethode |
|----|-----------|-------------|
| **Container & Start** | | |
| AK-001 | Container startet ohne Fehler | `docker run` erfolgreich |
| AK-002 | Graceful Shutdown funktioniert | SIGTERM führt zu Exit 0 |
| AK-003 | 12-Factor Compliance | Checkliste erfüllt |
| | | |
| **Stories** | | |
| AK-010 | Stories werden abgerufen | Logs zeigen Abruf |
| AK-011 | Neue Stories werden geliked | Like in Instagram sichtbar |
| AK-012 | Story-Datensätze werden persistiert | DB-Inhalt prüfen |
| AK-013 | Story-Duplikate werden verhindert | Zweiter Durchlauf überspringt |
| AK-014 | Story-Cleanup funktioniert | Datensätze >24h werden gelöscht |
| | | |
| **Beiträge** | | |
| AK-020 | Beiträge werden abgerufen | Logs zeigen Abruf |
| AK-021 | Neue Beiträge werden geliked | Like in Instagram sichtbar |
| AK-022 | Beitrags-Datensätze werden persistiert | DB-Inhalt prüfen |
| AK-023 | Beitrags-Duplikate werden verhindert | Zweiter Durchlauf überspringt |
| AK-024 | Beiträge werden NICHT gelöscht | Alte Datensätze bleiben erhalten |
| | | |
| **Multi-Account** | | |
| AK-030 | Mehrere Zielaccounts werden verarbeitet | Logs zeigen alle Accounts |
| AK-031 | Accounts können dynamisch hinzugefügt werden | Config-Änderung wird erkannt |
| | | |
| **Rate-Limiting** | | |
| AK-040 | Delays zwischen Requests eingehalten | Logs zeigen Timing |
| AK-041 | Like-Limit pro Stunde funktioniert | Counter stoppt bei Limit |
| AK-042 | Like-Limit pro Tag funktioniert | Counter stoppt bei Limit |
| AK-043 | Jitter wird angewendet | Delays variieren |
| | | |
| **Session** | | |
| AK-050 | Session wird persistent gespeichert | DB enthält Session-Daten |
| AK-051 | Session überlebt Container-Restart | Kein Re-Login nach Restart |
| AK-052 | Keep-Alive verhindert Session-Ablauf | Session bleibt aktiv |

---

## 10. Risiken und Einschränkungen

| Risiko | Wahrscheinlichkeit | Auswirkung | Mitigation |
|--------|-------------------|------------|------------|
| Instagram Rate-Limiting | Hoch | Temporäre Sperre | Konservative Limits, Jitter, Backoff |
| Instagram Account-Sperre | Mittel | Service-Ausfall | Session-Persistenz, "menschliches" Verhalten |
| API-Änderungen | Mittel | Funktionsverlust | instagrapi-Updates verfolgen |
| 2FA-Challenge | Mittel | Login-Fehler | Session-Persistenz, Admin-Alerting |
| Session-Ablauf | Mittel | Re-Login nötig | Keep-Alive Requests |
| Shadowban | Niedrig | Likes nicht sichtbar | Konservative Limits, Pausen |
| IP-Sperre | Niedrig | Kompletter Ausfall | Proxy-Support (optional) |

---

## 11. Glossar

| Begriff | Definition |
|---------|------------|
| Story | Temporärer Instagram-Inhalt (24h Lebensdauer) |
| Post/Beitrag | Permanenter Instagram-Inhalt (Photo, Video, Album, Reel) |
| Reel | Kurzvideos (media_type=2, product_type=clips) |
| story_pk | Primary Key einer Story (numerische ID) |
| media_pk | Primary Key eines Beitrags (numerische ID) |
| taken_at | Zeitstempel der Content-Erstellung |
| instagrapi | Python-Bibliothek für Instagram Private API |
| 12-Factor App | Methodik für Cloud-native Anwendungen |
| OCI | Open Container Initiative (Container-Standard) |
| Rate-Limit | Maximale Anzahl API-Calls pro Zeiteinheit |
| Jitter | Zufällige Variation bei Delays |
| Backoff | Exponentiell steigende Wartezeit bei Fehlern |
| Keep-Alive | Regelmäßige Requests zur Session-Erhaltung |
| Challenge | Instagram-Verifizierung (2FA, Captcha, etc.) |
