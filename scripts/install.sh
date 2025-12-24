#!/bin/bash
#
# Raspberry Pi HMI Installation Script
# =====================================
# Installs all dependencies and sets up the HMI system.
#
# Usage: sudo ./scripts/install.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Raspberry Pi HMI Installation Script  ${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: Running without sudo. Some features may require root privileges.${NC}"
fi

# Detect if running on Raspberry Pi
IS_RASPBERRY_PI=false
if [ -f /proc/cpuinfo ]; then
    if grep -q "Raspberry Pi\|BCM" /proc/cpuinfo; then
        IS_RASPBERRY_PI=true
        echo -e "${GREEN}Detected Raspberry Pi hardware${NC}"
    fi
fi

if [ "$IS_RASPBERRY_PI" = false ]; then
    echo -e "${YELLOW}Not running on Raspberry Pi - installing in simulation mode${NC}"
fi

# Update system packages
echo -e "\n${BLUE}[1/7] Updating system packages...${NC}"
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv nodejs npm git
fi

# Enable I2C and SPI on Raspberry Pi
if [ "$IS_RASPBERRY_PI" = true ]; then
    echo -e "\n${BLUE}[2/7] Enabling hardware interfaces...${NC}"

    # Enable I2C
    if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
        echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
        echo -e "${GREEN}I2C enabled${NC}"
    fi

    # Enable SPI
    if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
        echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
        echo -e "${GREEN}SPI enabled${NC}"
    fi

    # Install Raspberry Pi specific packages
    sudo apt-get install -y python3-rpi.gpio python3-smbus i2c-tools
else
    echo -e "\n${BLUE}[2/7] Skipping hardware interface setup (not on Raspberry Pi)${NC}"
fi

# Create Python virtual environment
echo -e "\n${BLUE}[3/7] Setting up Python virtual environment...${NC}"
cd "$PROJECT_DIR/backend"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "\n${BLUE}[4/7] Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Install Raspberry Pi specific packages
if [ "$IS_RASPBERRY_PI" = true ]; then
    echo -e "\n${BLUE}Installing Raspberry Pi hardware libraries...${NC}"
    pip install RPi.GPIO gpiozero spidev smbus2
    pip install adafruit-circuitpython-dht adafruit-circuitpython-bmp280
    pip install adafruit-circuitpython-ads1x15 adafruit-circuitpython-ssd1306
    pip install adafruit-circuitpython-neopixel rpi-ws281x
    pip install RPLCD
fi

# Install frontend dependencies
echo -e "\n${BLUE}[5/7] Installing frontend dependencies...${NC}"
cd "$PROJECT_DIR/frontend"
npm install

# Build frontend
echo -e "\n${BLUE}[6/7] Building frontend...${NC}"
npm run build

# Copy build to backend static folder
echo -e "\n${BLUE}[7/7] Copying frontend build to backend...${NC}"
mkdir -p "$PROJECT_DIR/backend/static"
cp -r dist/* "$PROJECT_DIR/backend/static/"

# Create data directories
mkdir -p "$PROJECT_DIR/backend/data"
mkdir -p "$PROJECT_DIR/backend/logs"

# Create .env file if not exists
if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
    cat > "$PROJECT_DIR/backend/.env" << EOF
# Raspberry Pi HMI Configuration
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
SIMULATION_MODE=$([ "$IS_RASPBERRY_PI" = true ] && echo "false" || echo "true")
HARDWARE_UPDATE_INTERVAL=0.5
DATA_LOG_INTERVAL=5.0
DATA_RETENTION_DAYS=30
EOF
    echo -e "${GREEN}Created .env configuration file${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Complete!                ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "To start the HMI server:"
echo -e "  ${BLUE}cd $PROJECT_DIR/backend${NC}"
echo -e "  ${BLUE}source venv/bin/activate${NC}"
echo -e "  ${BLUE}python -m uvicorn app.main:app --host 0.0.0.0 --port 8000${NC}"
echo ""
echo -e "Or install as a system service:"
echo -e "  ${BLUE}sudo ./scripts/install-service.sh${NC}"
echo ""

if [ "$IS_RASPBERRY_PI" = true ]; then
    echo -e "${YELLOW}Note: A reboot may be required to enable I2C and SPI.${NC}"
fi
