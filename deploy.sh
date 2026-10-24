#!/bin/bash
# ==============================================================================
# CleanCity / CivicPulse AI - Automated Linux & Alibaba Cloud ECS Deployment
# Compatible with: Alibaba Cloud Linux 2/3, Ubuntu 20.04/22.04/24.04, Debian, CentOS 7/8/9
# ==============================================================================

set -e

# ANSI Color codes
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}================================================================${RESET}"
echo -e "${BOLD}${GREEN}   CivicPulse AI • CleanCity Copilot - Production Deployment    ${RESET}"
echo -e "${BOLD}${CYAN}================================================================${RESET}"

# 1. Root / Sudo Check
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${YELLOW}[!] Note: Running as non-root user. Checking sudo access...${RESET}"
    SUDO="sudo"
else
    SUDO=""
fi

# 2. Check and Install Docker & Docker Compose
echo -e "\n${BOLD}${CYAN}[Step 1/5] Checking Docker & Docker Compose installation...${RESET}"
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${YELLOW}[*] Docker not found. Installing Docker Engine via official automated script...${RESET}"
    $SUDO apt-get update -y 2>/dev/null || $SUDO yum makecache -y 2>/dev/null || true
    curl -fsSL https://get.docker.com -o get-docker.sh
    $SUDO sh get-docker.sh
    rm -f get-docker.sh
    $SUDO systemctl enable --now docker
    echo -e "${GREEN}[+] Docker successfully installed and service started!${RESET}"
else
    echo -e "${GREEN}[✓] Docker is already installed: $(docker --version)${RESET}"
fi

# Ensure docker service is running
$SUDO systemctl start docker || true

# Check docker compose (plugin or standalone)
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo -e "${YELLOW}[*] Installing docker-compose-plugin...${RESET}"
    if command -v apt-get >/dev/null 2>&1; then
        $SUDO apt-get update && $SUDO apt-get install -y docker-compose-plugin
    elif command -v yum >/dev/null 2>&1; then
        $SUDO yum install -y docker-compose-plugin
    fi
    COMPOSE_CMD="docker compose"
fi
echo -e "${GREEN}[✓] Compose command: $COMPOSE_CMD${RESET}"

# 3. Configure Local Firewall (UFW / Firewalld)
echo -e "\n${BOLD}${CYAN}[Step 2/5] Configuring firewall rules (Ports 22, 80, 443, 8000, 8501)...${RESET}"
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
    echo -e "${YELLOW}[*] Configuring UFW rules...${RESET}"
    $SUDO ufw allow 22/tcp comment 'SSH' || true
    $SUDO ufw allow 80/tcp comment 'HTTP Gateway' || true
    $SUDO ufw allow 443/tcp comment 'HTTPS' || true
    $SUDO ufw allow 8000/tcp comment 'CivicPulse FastAPI Backend' || true
    $SUDO ufw allow 8501/tcp comment 'Streamlit Dashboard' || true
    echo -e "${GREEN}[✓] UFW firewall ports opened.${RESET}"
elif command -v firewall-cmd >/dev/null 2>&1 && systemctl is-active --quiet firewalld; then
    echo -e "${YELLOW}[*] Configuring firewalld rules...${RESET}"
    $SUDO firewall-cmd --permanent --add-port=22/tcp || true
    $SUDO firewall-cmd --permanent --add-port=80/tcp || true
    $SUDO firewall-cmd --permanent --add-port=443/tcp || true
    $SUDO firewall-cmd --permanent --add-port=8000/tcp || true
    $SUDO firewall-cmd --permanent --add-port=8501/tcp || true
    $SUDO firewall-cmd --reload || true
    echo -e "${GREEN}[✓] Firewalld ports opened.${RESET}"
else
    echo -e "${CYAN}[i] No active local firewall detected or managed by Cloud Security Groups.${RESET}"
fi

# 4. Prepare Directories and Permissions
echo -e "\n${BOLD}${CYAN}[Step 3/5] Initializing local storage directories...${RESET}"
mkdir -p data media/images media/audio static templates
chmod -R 775 media data || true

# If cleancity.db is in root, copy to data/cleancity.db if data/cleancity.db does not exist yet
if [ ! -f data/cleancity.db ] && [ -f cleancity.db ]; then
    echo -e "${YELLOW}[*] Seeding initial database from local repository copy...${RESET}"
    cp cleancity.db data/cleancity.db
    chmod 664 data/cleancity.db || true
fi

# 5. Build and Launch Containers
echo -e "\n${BOLD}${CYAN}[Step 4/5] Building and launching Docker Compose container stack...${RESET}"
$SUDO $COMPOSE_CMD down --remove-orphans || true
$SUDO $COMPOSE_CMD build --pull
$SUDO $COMPOSE_CMD up -d

# 6. Verify Health Status
echo -e "\n${BOLD}${CYAN}[Step 5/5] Performing live container health-checks...${RESET}"
MAX_RETRIES=20
COUNT=0
HEALTHY=false

while [ $COUNT -lt $MAX_RETRIES ]; do
    COUNT=$((COUNT + 1))
    echo -n "   Waiting for FastAPI backend to initialize (Attempt $COUNT/$MAX_RETRIES)... "
    if curl -s -f http://localhost:8000/api/health >/dev/null 2>&1; then
        echo -e "${GREEN}ONLINE!${RESET}"
        HEALTHY=true
        break
    else
        echo -e "${YELLOW}booting...${RESET}"
        sleep 2
    fi
done

# Fetch Server Public IP
PUBLIC_IP=$(curl -s -m 5 https://api.ipify.org || curl -s -m 5 ifconfig.me || echo "YOUR_SERVER_IP")

echo -e "\n${BOLD}${GREEN}================================================================${RESET}"
echo -e "${BOLD}${GREEN}   DEPLOYMENT SUCCESSFUL - CIVICPULSE AI STACK IS RUNNING!     ${RESET}"
echo -e "${BOLD}${GREEN}================================================================${RESET}"

echo -e "\n${BOLD}Container Status:${RESET}"
$SUDO $COMPOSE_CMD ps

echo -e "\n${BOLD}${CYAN}Access Endpoints:${RESET}"
echo -e "  ${BOLD}1. Main Municipal Portal (Port 80):${RESET}      http://${PUBLIC_IP}/"
echo -e "  ${BOLD}2. Interactive Swagger Docs (Port 8000):${RESET} http://${PUBLIC_IP}:8000/docs"
echo -e "  ${BOLD}3. Streamlit Citizen UI (Port 8501):${RESET}     http://${PUBLIC_IP}:8501/"
echo -e "  ${BOLD}4. Health Check Endpoint:${RESET}                http://${PUBLIC_IP}:8000/api/health"

echo -e "\n${BOLD}${YELLOW}Security Group Reminder:${RESET}"
echo -e "  If deploying on Alibaba Cloud ECS, AWS, or GCP, make sure your Cloud Console"
echo -e "  Security Group allows Inbound TCP rules for:"
echo -e "    - Port 80   (HTTP Portal)"
echo -e "    - Port 443  (HTTPS SSL)"
echo -e "    - Port 8000 (Backend API)"
echo -e "    - Port 8501 (Streamlit UI)"
echo -e "    - Port 22   (SSH Access)"

echo -e "\n${BOLD}Useful Operational Commands:${RESET}"
echo -e "  View logs:          ${CYAN}$SUDO $COMPOSE_CMD logs -f${RESET}"
echo -e "  Restart stack:      ${CYAN}$SUDO $COMPOSE_CMD restart${RESET}"
echo -e "  Stop stack:         ${CYAN}$SUDO $COMPOSE_CMD down${RESET}"
echo -e "  Check status:       ${CYAN}$SUDO $COMPOSE_CMD ps${RESET}\n"
