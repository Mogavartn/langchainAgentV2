#!/bin/bash

# 🚀 Script de déploiement optimisé pour JAK Company RAG API
# Version 3.0-Clean

set -e  # Arrêt en cas d'erreur

# Configuration
PROJECT_NAME="jak-company-rag-api"
VERSION="3.0-Clean"
DEPLOY_ENV=${1:-"production"}

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions de logging
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifications pré-déploiement
pre_deployment_checks() {
    log_info "🔍 Vérifications pré-déploiement..."
    
    # Vérifier que Python est installé
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 n'est pas installé"
        exit 1
    fi
    
    # Vérifier que pip est installé
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 n'est pas installé"
        exit 1
    fi
    
    # Vérifier que les fichiers essentiels existent
    if [ ! -f "process_optimized.py" ]; then
        log_error "process_optimized.py n'existe pas"
        exit 1
    fi
    
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt n'existe pas"
        exit 1
    fi
    
    log_success "Vérifications pré-déploiement terminées"
}

# Installation des dépendances
install_dependencies() {
    log_info "📦 Installation des dépendances..."
    
    # Mettre à jour pip
    pip3 install --upgrade pip
    
    # Installer les dépendances
    pip3 install -r requirements.txt
    
    log_success "Dépendances installées"
}

# Tests de validation
run_tests() {
    log_info "🧪 Exécution des tests de validation..."
    
    # Test de syntaxe Python
    python3 -m py_compile process_optimized.py
    log_success "Syntaxe Python valide"
    
    # Tests fonctionnels (si le fichier existe)
    if [ -f "test_optimized.py" ]; then
        log_info "Exécution des tests fonctionnels..."
        python3 test_optimized.py
        log_success "Tests fonctionnels passés"
    else
        log_warning "Fichier de test non trouvé, tests ignorés"
    fi
}

# Nettoyage et optimisation
cleanup_and_optimize() {
    log_info "🧹 Nettoyage et optimisation..."
    
    # Nettoyer les caches Python
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    
    # Nettoyer les fichiers temporaires
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name "*.log" -delete 2>/dev/null || true
    
    log_success "Nettoyage terminé"
}

# Sauvegarde de l'ancienne version
backup_old_version() {
    log_info "💾 Sauvegarde de l'ancienne version..."
    
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Sauvegarder l'ancien process.py s'il existe
    if [ -f "process.py" ]; then
        cp process.py "$BACKUP_DIR/process_old.py"
        log_success "Ancien process.py sauvegardé"
    fi
    
    # Sauvegarder les logs s'ils existent
    if [ -d "logs" ]; then
        cp -r logs "$BACKUP_DIR/"
        log_success "Logs sauvegardés"
    fi
    
    log_success "Sauvegarde terminée dans $BACKUP_DIR"
}

# Déploiement de la nouvelle version
deploy_new_version() {
    log_info "🚀 Déploiement de la nouvelle version..."
    
    # Renommer le fichier optimisé
    if [ -f "process_optimized.py" ]; then
        mv process_optimized.py process.py
        log_success "process_optimized.py renommé en process.py"
    fi
    
    # Créer les dossiers nécessaires
    mkdir -p logs
    mkdir -p data
    
    # Définir les permissions
    chmod +x process.py
    chmod 644 requirements.txt
    
    log_success "Nouvelle version déployée"
}

# Configuration de l'environnement
configure_environment() {
    log_info "⚙️  Configuration de l'environnement..."
    
    # Vérifier les variables d'environnement
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "OPENAI_API_KEY non définie"
    else
        log_success "OPENAI_API_KEY configurée"
    fi
    
    # Créer le fichier de configuration si nécessaire
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Configuration JAK Company RAG API
OPENAI_API_KEY=${OPENAI_API_KEY:-""}
ENVIRONMENT=${DEPLOY_ENV}
VERSION=${VERSION}
LOG_LEVEL=INFO
MEMORY_TTL=3600
MEMORY_MAX_SIZE=1000
EOF
        log_success "Fichier .env créé"
    fi
    
    log_success "Environnement configuré"
}

# Test de démarrage
test_startup() {
    log_info "🔧 Test de démarrage..."
    
    # Test de démarrage rapide (timeout 30s)
    timeout 30s python3 -c "
import process
print('✅ Import réussi')
" || {
        log_error "Test de démarrage échoué"
        exit 1
    }
    
    log_success "Test de démarrage réussi"
}

# Démarrage du service
start_service() {
    log_info "🚀 Démarrage du service..."
    
    # Vérifier si le service est déjà en cours
    if pgrep -f "process.py" > /dev/null; then
        log_warning "Service déjà en cours, arrêt..."
        pkill -f "process.py" || true
        sleep 2
    fi
    
    # Démarrer le service en arrière-plan
    nohup python3 process.py > logs/app.log 2>&1 &
    SERVICE_PID=$!
    
    # Attendre que le service démarre
    sleep 5
    
    # Vérifier que le service fonctionne
    if kill -0 $SERVICE_PID 2>/dev/null; then
        log_success "Service démarré (PID: $SERVICE_PID)"
    else
        log_error "Échec du démarrage du service"
        exit 1
    fi
}

# Tests de santé
health_check() {
    log_info "🏥 Tests de santé..."
    
    # Attendre que le service soit prêt
    sleep 10
    
    # Test de l'endpoint de santé
    if command -v curl &> /dev/null; then
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Endpoint de santé accessible"
        else
            log_error "Endpoint de santé inaccessible"
            exit 1
        fi
    else
        log_warning "curl non disponible, test de santé ignoré"
    fi
    
    log_success "Tests de santé passés"
}

# Affichage des informations de déploiement
show_deployment_info() {
    log_info "📊 Informations de déploiement"
    echo "=================================="
    echo "Projet: $PROJECT_NAME"
    echo "Version: $VERSION"
    echo "Environnement: $DEPLOY_ENV"
    echo "Port: 8000"
    echo "Logs: logs/app.log"
    echo "PID: $(pgrep -f 'process.py' || echo 'Non trouvé')"
    echo "=================================="
    
    log_success "Déploiement terminé avec succès!"
}

# Fonction principale
main() {
    echo "🚀 DÉPLOIEMENT JAK COMPANY RAG API v$VERSION"
    echo "=============================================="
    
    pre_deployment_checks
    install_dependencies
    run_tests
    cleanup_and_optimize
    backup_old_version
    deploy_new_version
    configure_environment
    test_startup
    start_service
    health_check
    show_deployment_info
}

# Gestion des arguments
case "${1:-}" in
    "production"|"staging"|"development")
        main
        ;;
    "test")
        log_info "🧪 Mode test uniquement"
        pre_deployment_checks
        install_dependencies
        run_tests
        ;;
    "clean")
        log_info "🧹 Mode nettoyage uniquement"
        cleanup_and_optimize
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [environment]"
        echo ""
        echo "Environnements:"
        echo "  production  - Déploiement complet en production"
        echo "  staging     - Déploiement en staging"
        echo "  development - Déploiement en développement"
        echo ""
        echo "Options:"
        echo "  test        - Tests uniquement"
        echo "  clean       - Nettoyage uniquement"
        echo "  help        - Afficher cette aide"
        ;;
    *)
        log_error "Environnement invalide: $1"
        echo "Utilisez '$0 help' pour voir les options disponibles"
        exit 1
        ;;
esac