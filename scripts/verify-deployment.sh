#!/bin/bash
# Deployment Verification Script
# Verifies that services are healthy and HTTPS is working after deployment
# Usage: ./verify-deployment.sh <server-ip> [--skip-https]

set -e

SERVER_IP=$1
SKIP_HTTPS=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
if [[ "$2" == "--skip-https" ]]; then
    SKIP_HTTPS=true
fi

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${GREEN}===${NC} $1"
}

# Function to check if server is reachable
check_server_reachable() {
    log_step "Checking Server Connectivity"

    if ping -c 1 -W 2 "$SERVER_IP" &> /dev/null; then
        log_success "Server $SERVER_IP is reachable"
        return 0
    else
        log_error "Server $SERVER_IP is not reachable"
        return 1
    fi
}

# Function to check Docker service health
check_docker_health() {
    local service_name=$1
    local server=$2

    log_info "Checking health: $service_name"

    # Try to get container status via SSH
    local status=$(ssh -o ConnectTimeout=10 "wizardsofts@${server}" \
        "docker ps --filter name=${service_name} --format '{{.Status}}'" 2>/dev/null || echo "unknown")

    if echo "$status" | grep -q "healthy"; then
        log_success "$service_name is healthy"
        return 0
    elif echo "$status" | grep -q "Up"; then
        log_warn "$service_name is up but health status unknown"
        return 0
    else
        log_error "$service_name status: $status"
        return 1
    fi
}

# Function to test HTTP endpoint
test_http_endpoint() {
    local url=$1
    local expected_code=${2:-200}

    log_info "Testing HTTP endpoint: $url"

    local http_code=$(curl -s -o /dev/null -w "%{http_code}" -m 10 "$url" 2>/dev/null || echo "000")

    if [[ "$http_code" == "$expected_code" ]] || [[ "$http_code" =~ ^(200|301|302|308)$ ]]; then
        log_success "Endpoint responding with HTTP $http_code: $url"
        return 0
    else
        log_error "Endpoint returned HTTP $http_code (expected $expected_code): $url"
        return 1
    fi
}

# Function to verify HTTPS certificate
verify_https_cert() {
    local domain=$1

    log_info "Verifying HTTPS certificate: $domain"

    # Check if domain is resolvable
    if ! nslookup "$domain" &> /dev/null; then
        log_error "Domain not resolvable: $domain"
        return 1
    fi

    # Check certificate validity
    local cert_info=$(echo | openssl s_client -connect "${domain}:443" -servername "$domain" 2>/dev/null | \
        openssl x509 -noout -dates 2>/dev/null || echo "error")

    if [[ "$cert_info" == "error" ]]; then
        log_error "Could not retrieve certificate for $domain"
        return 1
    fi

    # Check if certificate is valid (not expired)
    local expiry=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
    local expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$expiry" +%s 2>/dev/null || echo "0")
    local now_epoch=$(date +%s)

    if [[ $expiry_epoch -gt $now_epoch ]]; then
        log_success "Certificate valid until: $expiry"

        # Check issuer
        local issuer=$(echo | openssl s_client -connect "${domain}:443" -servername "$domain" 2>/dev/null | \
            openssl x509 -noout -issuer 2>/dev/null | grep -oP 'CN\s*=\s*\K[^,]+' || echo "unknown")
        log_info "Certificate issuer: $issuer"

        if echo "$issuer" | grep -qi "Let's Encrypt"; then
            log_success "Using Let's Encrypt certificate"
        elif echo "$issuer" | grep -qi "Self-signed"; then
            log_warn "Using self-signed certificate"
        fi

        return 0
    else
        log_error "Certificate expired or invalid for $domain"
        return 1
    fi
}

# Function to test HTTPS endpoint
test_https_endpoint() {
    local domain=$1

    log_info "Testing HTTPS connection: https://$domain"

    local response=$(curl -sI "https://$domain" -m 10 2>&1 | head -5)
    local http_code=$(echo "$response" | grep -oP 'HTTP/\S+\s+\K\d+' | head -1)

    if [[ -n "$http_code" ]] && [[ "$http_code" =~ ^(200|301|302|308)$ ]]; then
        log_success "HTTPS endpoint responding: https://$domain (HTTP $http_code)"
        return 0
    else
        log_error "HTTPS endpoint failed: https://$domain"
        echo "$response" | sed 's/^/  /'
        return 1
    fi
}

# Main verification logic
main() {
    local exit_code=0

    echo "========================================="
    echo "  Deployment Verification"
    echo "========================================="
    echo ""

    if [[ -z "$SERVER_IP" ]]; then
        log_error "Usage: $0 <server-ip> [--skip-https]"
        echo "Example: $0 10.0.0.84"
        exit 1
    fi

    log_info "Target server: $SERVER_IP"
    if [[ "$SKIP_HTTPS" == true ]]; then
        log_warn "HTTPS verification will be skipped"
    fi
    echo ""

    # Check server connectivity
    if ! check_server_reachable; then
        exit_code=1
    fi

    # Check Docker services (requires SSH access)
    log_step "Checking Docker Services"
    for service in "traefik" "ws-wizardsofts-web" "pf-padmafoods-web" "gibd-quant-web"; do
        if ! check_docker_health "$service" "$SERVER_IP"; then
            exit_code=1
        fi
    done

    # Test HTTP endpoints
    log_step "Testing HTTP Endpoints"
    test_http_endpoint "http://${SERVER_IP}:3000/" || exit_code=1
    test_http_endpoint "http://${SERVER_IP}:3001/" || exit_code=1
    test_http_endpoint "http://${SERVER_IP}:3002/" || exit_code=1

    # Test Traefik routing
    log_step "Testing Traefik Routing"
    test_http_endpoint "http://${SERVER_IP}/" 308 || exit_code=1  # Should redirect to HTTPS

    # HTTPS verification
    if [[ "$SKIP_HTTPS" == false ]]; then
        log_step "Verifying HTTPS Certificates"

        # Define domains to check
        declare -A domains=(
            ["www.wizardsofts.com"]="WizardSofts"
            ["www.mypadmafoods.com"]="Padma Foods"
            ["www.guardianinvestmentbd.com"]="GIBD Quant"
        )

        for domain in "${!domains[@]}"; do
            local name="${domains[$domain]}"
            log_info "--- $name ---"

            # Check if domain resolves to this server
            local resolved_ip=$(nslookup "$domain" 2>/dev/null | grep -A1 "Name:" | grep "Address:" | awk '{print $2}' | head -1)

            if [[ "$resolved_ip" == "$SERVER_IP" ]]; then
                verify_https_cert "$domain" || exit_code=1
                test_https_endpoint "$domain" || exit_code=1
            else
                log_warn "Domain $domain resolves to $resolved_ip, not $SERVER_IP - skipping HTTPS check"
                log_info "This is expected for staging/development servers"
            fi
            echo ""
        done
    else
        log_warn "HTTPS verification skipped"
    fi

    # Summary
    echo "========================================="
    if [[ $exit_code -eq 0 ]]; then
        log_success "All deployment verifications passed!"
        echo "========================================="
        exit 0
    else
        log_error "Deployment verification failed"
        log_info "Check logs above for details"
        echo "========================================="
        exit $exit_code
    fi
}

# Run main function
main
