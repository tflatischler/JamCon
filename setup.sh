#!/bin/bash
# JamCon Setup Script
# Installiert alle Abhängigkeiten und richtet das Projekt ein

set -e  # Bei Fehler abbrechen

echo "================================"
echo "JamCon Installation"
echo "================================"

# Prüfen ob als root ausgeführt
if [ "$EUID" -ne 0 ]; then 
    echo "Bitte als root ausführen: sudo bash setup.sh"
    exit 1
fi

# System-Pakete aktualisieren
echo ""
echo "[1/5] System aktualisieren..."
apt-get update
apt-get upgrade -y

# Abhängigkeiten installieren
echo ""
echo "[2/5] Abhängigkeiten installieren..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-dbus \
    libhidapi-hidraw0 \
    bluetooth \
    bluez \
    bluez-tools \
    git

# Python-Pakete installieren
echo ""
echo "[3/5] Python-Pakete installieren..."
pip3 install --upgrade pip
pip3 install hid aioconsole crc8

# Joycontrol klonen und installieren
echo ""
echo "[4/5] Joycontrol installieren..."

if [ -d "joycontrol" ]; then
    echo "Joycontrol bereits vorhanden, wird aktualisiert..."
    cd joycontrol
    git pull
    cd ..
else
    git clone https://github.com/mart1nro/joycontrol.git
fi

cd joycontrol
pip3 install -r requirements.txt
python3 setup.py install
cd ..

# Bluetooth-Service konfigurieren
echo ""
echo "[5/5] Bluetooth konfigurieren..."

# Bluetooth-Service neustarten
systemctl stop bluetooth
systemctl start bluetooth

# Bluetooth in Pairing-Modus setzen
hciconfig hci0 up
hciconfig hci0 piscan

echo ""
echo "================================"
echo "Installation abgeschlossen!"
echo "================================"
echo ""
echo "Nächste Schritte:"
echo "1. Erstelle die Dateien main.py und mapper.py im aktuellen Verzeichnis"
echo "2. Passe die Button-Mappings in mapper.py an"
echo "3. Starte mit: sudo python3 main.py"
echo ""
echo "Die Nintendo Switch sollte im Controller-Pairing-Modus sein:"
echo "System -> Controller -> Controller-Verbindung ändern"
echo ""
