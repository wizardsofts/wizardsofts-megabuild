#!/bin/bash
# Configuration Validation Script
# Validates YAML files, Docker configurations, and environment setup
# Usage: ./validate-config.sh [--strict]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STRICT_MODE=false
EXIT_CODE=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
if [[ "$1" == "--strict" ]]; then
    STRICT_MODE=true
fi

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    if [[ "$STRICT_MODE" == true ]]; then
        EXIT_CODE=1
    fi
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    EXIT_CODE=1
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

# Function to validate YAML syntax
validate_yaml() {
    local file=$1
    if [[ ! -f "$file" ]]; then
        log_warn "File not found: $file"
        return 1
    fi

    log_info "Validating YAML: $file"

    # Try Python YAML validation
    if command -v python3 &> /dev/null; then
        if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
            log_success "YAML syntax valid: $file"
            return 0
        else
            log_error "YAML syntax invalid: $file"
            python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>&1 | sed 's/^/  /'
            return 1
        fi
    else
        log_warn "Python3 not available, skipping YAML validation"
        return 0
    fi
}

# Function to validate Docker Compose files
validate_docker_compose() {
    local file=$1
    if [[ ! -f "$file" ]]; then
        log_warn "File not found: $file"
        return 1
    fi

    log_info "Validating Docker Compose: $file"

    if command -v docker-compose &> /dev/null; then
        if docker-compose -f "$file" config > /dev/null 2>&1; then
            log_success "Docker Compose valid: $file"
            return 0
        else
            log_error "Docker Compose invalid: $file"
            docker-compose -f "$file" config 2>&1 | sed 's/^/  /'
            return 1
        fi
    else
        log_warn "docker-compose not available, skipping Docker Compose validation"
        return 0
    fi
}

# Function to check for environment variable placeholders
check_env_placeholders() {
    local file=$1
    if [[ ! -f "$file" ]]; then
        return 0
    fi

    log_info "Checking for unset environment variables: $file"

    # Look for ${VAR} patterns that might not be set
    local placeholders=$(grep -oP '\$\{[A-Z_]+\}' "$file" 2>/dev/null || true)

    if [[ -n "$placeholders" ]]; then
        log_warn "Found environment variable placeholders in $file:"
        echo "$placeholders" | sort -u | sed 's/^/  - /'
        log_warn "Ensure these are set in the deployment environment"
    else
        log_success "No environment variable placeholders found"
    fi
}

# Function to validate Traefik configuration
validate_traefik_config() {
    local traefik_yml="$1"

    if [[ ! -f "$traefik_yml" ]]; then
        log_warn "Traefik configuration not found: $traefik_yml"
        return 0
    fi

    log_info "Validating Traefik configuration: $traefik_yml"

    # Check for required sections
    local required_sections=("api" "entryPoints" "providers")
    for section in "${required_sections[@]}"; do
        if ! grep -q "^${section}:" "$traefik_yml"; then
            log_error "Missing required section in Traefik config: $section"
        fi
    done

    # Check for ping endpoint (required for healthcheck)
    if ! grep -q "^ping:" "$traefik_yml"; then
        log_warn "Traefik config missing 'ping:' endpoint (required for healthcheck)"
    fi

    # Check for email in ACME configuration
    if grep -q "certificatesResolvers:" "$traefik_yml"; then
        if grep -q 'email:.*\${' "$traefik_yml"; then
            log_error "Traefik ACME email uses environment variable placeholder - this may not work!"
            log_error "Use hardcoded email instead: email: admin@wizardsofts.com"
        elif ! grep -q 'email:.*@' "$traefik_yml"; then
            log_error "Traefik ACME email not configured or invalid"
        else
            log_success "Traefik ACME email configured correctly"
        fi
    fi

    # Check network configuration
    if grep -q "network:.*traefik-public" "$traefik_yml"; then
        log_warn "Traefik using 'traefik-public' network - should be 'microservices-overlay'"
    elif grep -q "network:.*microservices-overlay" "$traefik_yml"; then
        log_success "Traefik network configured correctly"
    fi
}

# Function to validate GitLab CI configuration
validate_gitlab_ci() {
    local ci_file="$PROJECT_ROOT/.gitlab-ci.yml"

    if [[ ! -f "$ci_file" ]]; then
        log_warn "GitLab CI configuration not found"
        return 0
    fi

    log_info "Validating GitLab CI: $ci_file"
    validate_yaml "$ci_file"
}

# Main validation logic
main() {
    echo "========================================="
    echo "  Configuration Validation"
    echo "========================================="
    echo ""

    if [[ "$STRICT_MODE" == true ]]; then
        log_info "Running in STRICT mode - warnings will cause failure"
    fi

    # Validate GitLab CI
    validate_gitlab_ci
    echo ""

    # Validate Traefik configuration
    log_info "=== Traefik Configuration ==="
    if [[ -f "$PROJECT_ROOT/infrastructure/traefik/traefik.yml" ]]; then
        validate_yaml "$PROJECT_ROOT/infrastructure/traefik/traefik.yml"
        validate_traefik_config "$PROJECT_ROOT/infrastructure/traefik/traefik.yml"
        check_env_placeholders "$PROJECT_ROOT/infrastructure/traefik/traefik.yml"
    fi
    echo ""

    # Validate Docker Compose files
    log_info "=== Docker Compose Files ==="
    find "$PROJECT_ROOT" -name "docker-compose*.yml" -type f | while read -r compose_file; do
        validate_yaml "$compose_file"
        # Skip docker-compose validation if docker-compose not available
        if command -v docker-compose &> /dev/null; then
            validate_docker_compose "$compose_file"
        fi
        check_env_placeholders "$compose_file"
        echo ""
    done

    # Validate other YAML files
    log_info "=== Other YAML Files ==="
    find "$PROJECT_ROOT" -name "*.yml" -o -name "*.yaml" -type f | \
        grep -v "node_modules" | \
        grep -v "docker-compose" | \
        grep -v ".gitlab-ci.yml" | \
        grep -v "traefik.yml" | \
        while read -r yaml_file; do
            validate_yaml "$yaml_file"
        done
    echo ""

    # Summary
    echo "========================================="
    if [[ $EXIT_CODE -eq 0 ]]; then
        log_success "All validations passed!"
        echo "========================================="
        exit 0
    else
        log_error "Validation failed with errors"
        echo "========================================="
        exit $EXIT_CODE
    fi
}

# Run main function
main
