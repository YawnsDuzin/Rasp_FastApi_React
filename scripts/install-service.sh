#!/bin/bash
#
# Raspberry Pi HMI - Systemd Service Installation
# ================================================
# Installs the HMI as a system service for auto-start on boot.
#
# Usage: sudo ./scripts/install-service.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root (sudo)${NC}"
    exit 1
fi

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Installing Raspberry Pi HMI as a system service...${NC}"

# Get current user (the user who ran sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_GROUP="$(id -gn $ACTUAL_USER)"

# Create service file
cat > /etc/systemd/system/raspi-hmi.service << EOF
[Unit]
Description=Raspberry Pi HMI Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=$ACTUAL_USER
Group=$ACTUAL_GROUP
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$PROJECT_DIR/backend/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

# Logging
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=$PROJECT_DIR/backend/data $PROJECT_DIR/backend/logs

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Created systemd service file${NC}"

# Reload systemd
systemctl daemon-reload

# Enable service
systemctl enable raspi-hmi.service

# Start service
systemctl start raspi-hmi.service

# Check status
sleep 2
if systemctl is-active --quiet raspi-hmi.service; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Service installed and running!       ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "Service status: ${GREEN}active${NC}"
    echo ""
    echo -e "Useful commands:"
    echo -e "  ${BLUE}sudo systemctl status raspi-hmi${NC}   - Check status"
    echo -e "  ${BLUE}sudo systemctl restart raspi-hmi${NC} - Restart service"
    echo -e "  ${BLUE}sudo systemctl stop raspi-hmi${NC}    - Stop service"
    echo -e "  ${BLUE}sudo journalctl -u raspi-hmi -f${NC}  - View logs"
    echo ""
    echo -e "Access the HMI at: ${BLUE}http://$(hostname -I | cut -d' ' -f1):8000${NC}"
else
    echo -e "${RED}Service failed to start. Check logs with:${NC}"
    echo -e "  ${BLUE}sudo journalctl -u raspi-hmi -n 50${NC}"
fi
