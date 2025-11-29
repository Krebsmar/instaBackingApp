#!/bin/bash
# =============================================================================
# instaBackingApp Bootstrap Script
# =============================================================================
# Dieses Skript richtet das Projekt ein und startet den Dienst.
#
# Verwendung:
#   chmod +x bootstrap.sh
#   ./bootstrap.sh
# =============================================================================

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Header
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                     instaBackingApp                            ║"
echo "║              Instagram Backing Service Setup                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Funktion für Status-Nachrichten
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Prüfe ob Docker installiert ist
check_docker() {
    info "Prüfe Docker Installation..."
    if ! command -v docker &> /dev/null; then
        error "Docker ist nicht installiert. Bitte installiere Docker: https://docs.docker.com/get-docker/"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker Daemon läuft nicht oder keine Berechtigung. Versuche: sudo systemctl start docker"
    fi
    
    success "Docker ist verfügbar"
}

# Prüfe ob Docker Compose verfügbar ist
check_docker_compose() {
    info "Prüfe Docker Compose..."
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        success "Docker Compose (Plugin) gefunden"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        success "Docker Compose (Standalone) gefunden"
    else
        error "Docker Compose nicht gefunden. Bitte installiere Docker Compose."
    fi
}

# Erstelle .env Datei wenn nicht vorhanden
setup_env() {
    info "Prüfe Konfiguration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            warn ".env Datei wurde aus .env.example erstellt"
            echo ""
            echo -e "${YELLOW}╔═══════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${YELLOW}║  WICHTIG: Bitte bearbeite die .env Datei mit deinen Daten!    ║${NC}"
            echo -e "${YELLOW}╚═══════════════════════════════════════════════════════════════╝${NC}"
            echo ""
            echo "Mindestens diese Werte müssen gesetzt werden:"
            echo "  - IG_USERNAME      (dein Instagram Benutzername)"
            echo "  - IG_PASSWORD      (dein Instagram Passwort)"
            echo "  - IG_TARGET_USERNAMES (Zielaccounts, kommasepariert)"
            echo ""
            read -p "Möchtest du die .env Datei jetzt bearbeiten? [Y/n] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                ${EDITOR:-nano} .env
            fi
        else
            error ".env.example nicht gefunden. Bitte erstelle eine .env Datei."
        fi
    else
        success ".env Datei vorhanden"
    fi
    
    # Prüfe ob Pflichtfelder gesetzt sind
    source .env 2>/dev/null || true
    
    if [ -z "$IG_USERNAME" ] || [ "$IG_USERNAME" = "dein_username" ]; then
        warn "IG_USERNAME ist nicht konfiguriert!"
        NEEDS_CONFIG=true
    fi
    
    if [ -z "$IG_PASSWORD" ] || [ "$IG_PASSWORD" = "dein_passwort" ]; then
        warn "IG_PASSWORD ist nicht konfiguriert!"
        NEEDS_CONFIG=true
    fi
    
    if [ -z "$IG_TARGET_USERNAMES" ] || [ "$IG_TARGET_USERNAMES" = "account1,account2,account3" ]; then
        warn "IG_TARGET_USERNAMES ist nicht konfiguriert!"
        NEEDS_CONFIG=true
    fi
    
    if [ "$NEEDS_CONFIG" = true ]; then
        echo ""
        error "Bitte konfiguriere die .env Datei und starte das Skript erneut."
    fi
}

# Erstelle Datenverzeichnis
setup_directories() {
    info "Erstelle Verzeichnisse..."
    mkdir -p data
    success "Datenverzeichnis erstellt"
}

# Baue Docker Image
build_image() {
    info "Baue Docker Image..."
    $COMPOSE_CMD build --no-cache
    success "Docker Image gebaut"
}

# Starte Container
start_container() {
    info "Starte Container..."
    $COMPOSE_CMD up -d
    success "Container gestartet"
}

# Zeige Status
show_status() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    Setup abgeschlossen!                        ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Nützliche Befehle:"
    echo "  Logs anzeigen:     $COMPOSE_CMD logs -f"
    echo "  Status prüfen:     $COMPOSE_CMD ps"
    echo "  Stoppen:           $COMPOSE_CMD down"
    echo "  Neustarten:        $COMPOSE_CMD restart"
    echo ""
    
    # Zeige aktuelle Logs
    echo "Aktuelle Logs:"
    echo "─────────────────────────────────────────────────────────────────"
    $COMPOSE_CMD logs --tail=20
}

# Hauptprogramm
main() {
    check_docker
    check_docker_compose
    setup_env
    setup_directories
    build_image
    start_container
    show_status
}

# Ausführen
main "$@"
