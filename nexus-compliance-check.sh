#!/bin/bash

# NEXUS Compliance Check Script for Virtual-Fazer
# Uses NEXUS security policies to validate codebase

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
info() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
warn() { echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"; }
error() { echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"; }

# NEXUS Policy Checks based on security-policy.md

check_security_headers() {
    info "Checking security headers (NEXUS Security Policy: Network Security)"
    
    # Check Django settings for security
    if grep -q "SECURE_SSL_REDIRECT" backend/python/instagran/settings.py 2>/dev/null; then
        log "✓ SSL redirect configured"
    else
        warn "✗ SECURE_SSL_REDIRECT not configured"
    fi
    
    if grep -q "X_FRAME_OPTIONS" backend/python/instagran/settings.py 2>/dev/null; then
        log "✓ X-Frame-Options configured"
    else
        warn "✗ X_FRAME_OPTIONS not configured"
    fi
    
    if grep -q "SECURE_CONTENT_TYPE_NOSNIFF" backend/python/instagran/settings.py 2>/dev/null; then
        log "✓ Content-Type nosniff configured"
    else
        warn "✗ SECURE_CONTENT_TYPE_NOSNIFF not configured"
    fi
}

check_auth_security() {
    info "Checking authentication security (NEXUS Security Policy: Access Control)"
    
    # Check for JWT usage
    if grep -r "JWTAuthentication" backend/python --include="*.py" >/dev/null 2>&1; then
        log "✓ JWT authentication in use"
    else
        warn "✗ JWT authentication not found"
    fi
    
    # Check for password validators
    if grep -q "AUTH_PASSWORD_VALIDATORS" backend/python/instagran/settings.py 2>/dev/null; then
        log "✓ Password validators configured"
    else
        warn "✗ Password validators not configured"
    fi
    
    # Check for secure password fields
    if grep -r "make_password\|check_password" backend/python --include="*.py" >/dev/null 2>&1; then
        log "✓ Django password hashing in use"
    else
        warn "✗ Password hashing functions not found"
    fi
}

check_secrets_management() {
    info "Checking secrets management (NEXUS Security Policy: Data Protection)"
    
    # Check for hardcoded secrets (not using env() or os.environ)
    local secrets_found=0
    
    # Check for SECRET_KEY = 'hardcoded' pattern (excluding env() calls)
    if grep -r "^SECRET_KEY\s*=\s*['\"]" backend/python --include="*.py" >/dev/null 2>&1; then
        error "✗ Hardcoded SECRET_KEY found!"
        secrets_found=$((secrets_found + 1))
    else
        log "✓ No hardcoded SECRET_KEY detected (uses environment)"
    fi
    
    # Check for password = 'hardcoded' pattern
    if grep -r "password\s*=\s*['\"][^'\"]\{4,\}['\"]" backend/python --include="*.py" | grep -v "example\|test\|#\|default=" >/dev/null 2>&1; then
        warn "✗ Potential hardcoded password found"
        secrets_found=$((secrets_found + 1))
    fi
    
    # Check .env.example exists
    if [ -f ".env.example" ]; then
        log "✓ .env.example exists"
    else
        warn "✗ .env.example missing"
    fi
    
    return $secrets_found
}

check_dependency_vulnerabilities() {
    info "Checking for dependency vulnerabilities (NEXUS Security Policy: Supply Chain)"
    
    # Check Python requirements
    if [ -f "backend/python/requirements.txt" ]; then
        log "✓ Python requirements.txt found"
        
        # Check for pinned versions
        local unpinned=$(grep -v "^#\|^$\|^\-" backend/python/requirements.txt | grep -v "==" | wc -l)
        if [ $unpinned -gt 0 ]; then
            warn "✗ $unpinned unpinned dependencies found"
        else
            log "✓ All Python dependencies pinned"
        fi
    fi
    
    # Check Node.js packages
    if [ -f "frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/package.json" ]; then
        log "✓ Frontend package.json found"
    fi
    
    # Run Trivy for vulnerability scanning (preferred - fast, no build required)
    if command -v trivy >/dev/null 2>&1; then
        info "Running Trivy vulnerability scan..."
        local trivy_output=$(trivy fs backend/python --severity HIGH,CRITICAL --format json --quiet 2>/dev/null)
        local trivy_count=$(echo "$trivy_output" | grep -c '"VulnerabilityID":' || echo "0")
        if [ "$trivy_count" -eq "0" ]; then
            log "✓ No HIGH/CRITICAL vulnerabilities found (Trivy)"
        else
            warn "✗ $trivy_count HIGH/CRITICAL vulnerabilities found - run 'trivy fs backend/python' for details"
        fi
    # Fallback to pip-audit
    elif command -v pip-audit >/dev/null 2>&1; then
        info "Running pip-audit on Python dependencies..."
        pip-audit --local --format=json 2>/dev/null | grep -q '"vulns": \[\]' && log "✓ No known vulnerabilities found" || warn "Vulnerabilities detected - review pip-audit output"
    else
        warn "Trivy/pip-audit not installed - skipping vulnerability scan"
    fi
}

check_cors_policy() {
    info "Checking CORS policy (NEXUS Security Policy: Network Security)"
    
    if grep -q "CORS_ALLOW_ALL_ORIGINS.*=.*True" backend/python/instagran/settings.py 2>/dev/null; then
        error "✗ CORS_ALLOW_ALL_ORIGINS is True (security risk)"
    else
        log "✓ CORS not allowing all origins"
    fi
    
    if grep -q "CORS_ALLOWED_ORIGINS" backend/python/instagran/settings.py 2>/dev/null; then
        log "✓ CORS_ALLOWED_ORIGINS configured"
    else
        warn "✗ CORS_ALLOWED_ORIGINS not configured"
    fi
}

check_logging_audit() {
    info "Checking logging configuration (NEXUS Security Policy: Audit)"
    
    if grep -q "LOGGING" backend/python/instagran/settings.py 2>/dev/null; then
        log "✓ Django LOGGING configured"
    else
        warn "✗ Django LOGGING not configured"
    fi
    
    # Check for security event logging
    if grep -r "logger.*security\|audit" backend/python --include="*.py" >/dev/null 2>&1; then
        log "✓ Security/audit logging found"
    else
        warn "✗ No security/audit logging found"
    fi
}

check_encryption_at_rest() {
    info "Checking encryption at rest (NEXUS Security Policy: Data Protection)"
    
    # Check for password field encryption
    if grep -r "models.PasswordField\|encrypt" backend/python --include="*.py" >/dev/null 2>&1; then
        log "✓ Encryption patterns found"
    else
        info "~ No explicit encryption fields (using Django default hashing)"
    fi
    
    # Check for sensitive data handling
    if grep -r "credit_card\|ssn\|social_security" backend/python --include="*.py" >/dev/null 2>&1; then
        warn "✗ Sensitive data fields detected - verify encryption"
    else
        log "✓ No obvious sensitive data fields found"
    fi
}

check_rate_limiting() {
    info "Checking rate limiting (NEXUS Security Policy: DDoS Protection)"
    
    # Check for DRF throttling (preferred method)
    if grep -q "DEFAULT_THROTTLE_CLASSES\|DEFAULT_THROTTLE_RATES" backend/python/instagran/settings.py 2>/dev/null; then
        log "✓ DRF throttling configured (rate limiting)"
    elif grep -r "RATE_LIMIT\|@rate_limit" backend/python --include="*.py" >/dev/null 2>&1; then
        log "✓ Rate limiting configured"
    else
        warn "✗ Rate limiting not found"
    fi
}

check_sbom_compliance() {
    info "Checking SBOM compliance (NEXUS Security Policy: Supply Chain)"
    
    # Check for lock files
    if [ -f "backend/python/requirements-fixed.txt" ]; then
        log "✓ Python requirements-fixed.txt exists (SBOM-like)"
    else
        warn "✗ No requirements-fixed.txt (generate with pip freeze)"
    fi
    
    if [ -f "frontend/6573c743-d3f3-45d3-b81d-1775f8ec5861/package-lock.json" ]; then
        log "✓ package-lock.json exists"
    else
        warn "✗ package-lock.json missing"
    fi
}

# Generate compliance report
generate_report() {
    info "============================================"
    info "NEXUS Compliance Check Complete"
    info "============================================"
    info ""
    info "Based on NEXUS Security Policy requirements:"
    info "1. Zero Trust Architecture - Partial"
    info "2. Defense in Depth - Partial"
    info "3. Least Privilege - Needs Review"
    info "4. Secure by Default - Partial"
    info "5. Continuous Monitoring - Not Implemented"
    info ""
    info "Recommendations:"
    info "- Configure Django security middleware"
    info "- Implement rate limiting on all endpoints"
    info "- Add security event logging"
    info "- Generate SBOM with pip freeze > requirements-fixed.txt"
    info "- Set up dependency vulnerability scanning"
}

# Main
cd /Volumes/UnionSine/fix\ the\ site/virtual-fazer

log "Starting NEXUS compliance check on virtual-fazer..."
log "Using NEXUS Security Policy from /Volumes/UnionSine/fix the site/NEXUS/policies/security-policy.md"

check_security_headers
check_auth_security
check_secrets_management
check_dependency_vulnerabilities
check_cors_policy
check_logging_audit
check_encryption_at_rest
check_rate_limiting
check_sbom_compliance

generate_report

log "NEXUS compliance check complete"
