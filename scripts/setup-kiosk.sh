#!/bin/bash
#
# Raspberry Pi HMI - Kiosk Mode Setup
# ====================================
# Sets up the Raspberry Pi to boot directly into the HMI interface.
#
# Usage: sudo ./scripts/setup-kiosk.sh
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

# Check if running on Raspberry Pi
if [ ! -f /proc/cpuinfo ] || ! grep -q "Raspberry Pi\|BCM" /proc/cpuinfo; then
    echo -e "${RED}Error: This script is intended for Raspberry Pi only${NC}"
    exit 1
fi

echo -e "${BLUE}Setting up Kiosk Mode for Raspberry Pi HMI...${NC}"

# Get the actual user
ACTUAL_USER="${SUDO_USER:-pi}"
ACTUAL_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)

# Install required packages
echo -e "\n${BLUE}[1/5] Installing required packages...${NC}"
apt-get update
apt-get install -y chromium-browser unclutter xdotool

# Disable screen blanking
echo -e "\n${BLUE}[2/5] Disabling screen blanking...${NC}"
cat > /etc/X11/xorg.conf.d/10-blanking.conf << EOF
Section "ServerFlags"
    Option "BlankTime" "0"
    Option "StandbyTime" "0"
    Option "SuspendTime" "0"
    Option "OffTime" "0"
EndSection
EOF

# Create autostart directory
mkdir -p "$ACTUAL_HOME/.config/autostart"
chown "$ACTUAL_USER:$ACTUAL_USER" "$ACTUAL_HOME/.config/autostart"

# Create kiosk autostart entry
echo -e "\n${BLUE}[3/5] Creating autostart configuration...${NC}"
cat > "$ACTUAL_HOME/.config/autostart/kiosk.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Raspberry Pi HMI Kiosk
Exec=/usr/bin/chromium-browser --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble --disable-restore-session-state --incognito http://localhost:8000
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
chown "$ACTUAL_USER:$ACTUAL_USER" "$ACTUAL_HOME/.config/autostart/kiosk.desktop"

# Create unclutter autostart (hide mouse cursor)
cat > "$ACTUAL_HOME/.config/autostart/unclutter.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Unclutter
Exec=unclutter -idle 0.5 -root
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
chown "$ACTUAL_USER:$ACTUAL_USER" "$ACTUAL_HOME/.config/autostart/unclutter.desktop"

# Disable screen saver
echo -e "\n${BLUE}[4/5] Disabling screen saver...${NC}"
cat > "$ACTUAL_HOME/.config/autostart/disable-screensaver.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Disable Screensaver
Exec=xset s off -dpms
Hidden=false
X-GNOME-Autostart-enabled=true
EOF
chown "$ACTUAL_USER:$ACTUAL_USER" "$ACTUAL_HOME/.config/autostart/disable-screensaver.desktop"

# Enable autologin
echo -e "\n${BLUE}[5/5] Enabling autologin...${NC}"
mkdir -p /etc/systemd/system/getty@tty1.service.d/
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $ACTUAL_USER --noclear %I \$TERM
EOF

# Set to boot to desktop automatically
raspi-config nonint do_boot_behaviour B4 2>/dev/null || true

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Kiosk Mode Setup Complete!           ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "The Raspberry Pi will now boot directly into the HMI interface."
echo ""
echo -e "${YELLOW}To disable kiosk mode:${NC}"
echo -e "  1. Remove ~/.config/autostart/kiosk.desktop"
echo -e "  2. Or press Alt+F4 to close Chrome"
echo ""
echo -e "${BLUE}Please reboot to apply changes:${NC}"
echo -e "  sudo reboot"
