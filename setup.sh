#!/bin/bash
#
# JamCon Setup Script
# Automated installation for Raspberry Pi Zero 2 W
#

set -e  # Exit on error

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Colour

echo -e "${GREEN}"
echo "======================================"
echo "  JamCon - Joy-Con Proxy Device"
echo "  Installation Script"
echo "======================================"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Please run: sudo bash setup.sh"
    exit 1
fi

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo -e "${YELLOW}WARNING: This doesn't appear to be a Raspberry Pi${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}[1/8] Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

echo -e "${GREEN}[2/8] Installing system dependencies...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-dbus \
    python3-dev \
    libhidapi-hidraw0 \
    libhidapi-dev \
    bluetooth \
    bluez \
    bluez-tools \
    git \
    build-essential \
    libbluetooth-dev

echo -e "${GREEN}[3/8] Configuring Bluetooth...${NC}"
# Enable Bluetooth
systemctl enable bluetooth
systemctl start bluetooth

# Configure Bluetooth to be discoverable
hciconfig hci0 up
hciconfig hci0 piscan

# Add user to bluetooth group
if [ -n "$SUDO_USER" ]; then
    usermod -a -G bluetooth $SUDO_USER
    echo -e "${GREEN}Added $SUDO_USER to bluetooth group${NC}"
fi

echo -e "${GREEN}[4/8] Installing Python dependencies...${NC}"
pip3 install --upgrade pip

# Core dependencies
pip3 install \
    aioconsole \
    hid \
    crc8 \
    RPi.GPIO

echo -e "${GREEN}[5/8] Installing joycontrol...${NC}"
if [ -d "joycontrol" ]; then
    echo "joycontrol directory exists, updating..."
    cd joycontrol
    git pull
    cd ..
else
    echo "Cloning joycontrol..."
    git clone https://github.com/mart1nro/joycontrol.git
fi

cd joycontrol
pip3 install -r requirements.txt
python3 setup.py install
cd ..

echo -e "${GREEN}[6/8] Setting up GPIO permissions...${NC}"
# Add user to gpio group
if [ -n "$SUDO_USER" ]; then
    usermod -a -G gpio $SUDO_USER
fi

# Create udev rule for GPIO access
cat > /etc/udev/rules.d/99-gpio.rules << EOF
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", ACTION=="add", PROGRAM="/bin/sh -c 'chown root:gpio /sys/class/gpio/export /sys/class/gpio/unexport ; chmod 220 /sys/class/gpio/export /sys/class/gpio/unexport'"
SUBSYSTEM=="gpio", KERNEL=="gpio*", ACTION=="add", PROGRAM="/bin/sh -c 'chown root:gpio /sys%p/active_low /sys%p/direction /sys%p/edge /sys%p/value ; chmod 660 /sys%p/active_low /sys%p/direction /sys%p/edge /sys%p/value'"
EOF

udevadm control --reload-rules
udevadm trigger

echo -e "${GREEN}[7/8] Creating systemd service (optional)...${NC}"
cat > /etc/systemd/system/jamcon.service << EOF
[Unit]
Description=JamCon Joy-Con Proxy Device
After=network.target bluetooth.target

[Service]
Type=simple
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${YELLOW}Systemd service created but not enabled.${NC}"
echo -e "${YELLOW}To enable auto-start on boot: sudo systemctl enable jamcon${NC}"

echo -e "${GREEN}[8/8] Verifying installation...${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check if required modules are importable
python3 << EOF
import sys
modules = ['RPi.GPIO', 'hid', 'crc8', 'aioconsole']
missing = []

for module in modules:
    try:
        __import__(module)
        print(f"✓ {module} installed")
    except ImportError:
        print(f"✗ {module} MISSING")
        missing.append(module)

if missing:
    print(f"\nERROR: Missing modules: {', '.join(missing)}")
    sys.exit(1)
EOF

# Check Bluetooth status
if systemctl is-active --quiet bluetooth; then
    echo "✓ Bluetooth service running"
else
    echo -e "${RED}✗ Bluetooth service not running${NC}"
fi

# Check GPIO access
if [ -e /dev/gpiomem ]; then
    echo "✓ GPIO accessible"
else
    echo -e "${YELLOW}⚠ GPIO may not be accessible${NC}"
fi

echo
echo -e "${GREEN}======================================"
echo "  Installation Complete!"
echo "======================================"
echo -e "${NC}"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Connect your PCB board via FPC connector"
echo "2. Power on your Joy-Cons"
echo "3. Run: sudo python3 main.py"
echo
echo -e "${YELLOW}Optional:${NC}"
echo "• Enable auto-start: sudo systemctl enable jamcon"
echo "• Start service now: sudo systemctl start jamcon"
echo "• View logs: sudo journalctl -u jamcon -f"
echo
echo -e "${YELLOW}Troubleshooting:${NC}"
echo "• Bluetooth issues: sudo systemctl restart bluetooth"
echo "• GPIO test: gpio readall"
echo "• Check Joy-Con pairing: bluetoothctl devices"
echo
echo -e "${GREEN}Ready to use! Enjoy your JamCon proxy device!${NC}"
