# JamCon - Joy-Con BLE Proxy mit Button-Mapping

Ein Projekt zum Emulieren und Remapping von Joy-Con Inputs über einen Raspberry Pi.

## 🎮 Features

- Emuliert Pro Controller oder Joy-Cons über Bluetooth
- Flexibles Button-Mapping System
- Unterstützung für mehrere Controller gleichzeitig
- Erweiterte Funktionen (Button-Combos, Invertierung)
- Einfache Konfiguration über Python

## 📋 Voraussetzungen

### Hardware
- Raspberry Pi (getestet mit Pi Zero 2 W)
- Bluetooth 4.0+ Unterstützung
- Nintendo Switch

### Software
- Raspberry Pi OS (Bullseye oder neuer)
- Python 3.7+
- Root-Zugriff

## 🚀 Installation

### Schnellinstallation

```bash
# Repository klonen
git clone https://github.com/tflatischler/JamCon.git
cd JamCon

# Setup-Script ausführen (als root)
sudo bash setup.sh
```

### Manuelle Installation

```bash
# System-Pakete
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-dbus \
    libhidapi-hidraw0 bluetooth bluez bluez-tools git

# Joycontrol installieren
git clone https://github.com/mart1nro/joycontrol.git
cd joycontrol
pip3 install -r requirements.txt
sudo python3 setup.py install
cd ..

# Python-Abhängigkeiten
pip3 install hid aioconsole crc8
```

## 📁 Projektstruktur

```
JamCon/
├── main.py          # Hauptprogramm
├── mapper.py        # Button-Mapping Logik
├── setup.sh         # Installations-Script
├── README.md        # Diese Datei
└── hardware/        # Hardware-Anleitungen (optional)
```

## 🎯 Verwendung

### 1. Switch in Pairing-Modus versetzen

Auf der Nintendo Switch:
- **System** → **Controller** → **Controller-Verbindung ändern**

### 2. JamCon starten

```bash
sudo python3 main.py
```

### 3. Controller sollte automatisch verbinden

Die Switch sollte den emulierten Controller erkennen.

## ⚙️ Konfiguration

### Button-Mappings anpassen

Bearbeite `mapper.py` und passe die `MAPPING_PROFILES` an:

```python
MAPPING_PROFILES = {
    'jc_main': {
        'a': 'b',      # A-Button wird zu B
        'x': 'y',      # X-Button wird zu Y
        # Weitere Mappings...
    }
}
```

### Verfügbare Buttons

```
Face Buttons:  a, b, x, y
Shoulder:      l, r, zl, zr
D-Pad:         up, down, left, right
System:        plus, minus, home, capture
```

### Verschiedene Controller-Typen

In `main.py` kannst du den Controller-Typ ändern:

```python
# Pro Controller (empfohlen)
controller = JamConController('jc_main', 'PRO_CONTROLLER')

# Linker Joy-Con
controller = JamConController('jc_left', 'JOYCON_L')

# Rechter Joy-Con
controller = JamConController('jc_right', 'JOYCON_R')
```

## 🔧 Erweiterte Funktionen

### Custom Mapping zur Laufzeit

```python
# In main.py nach controller.start():
controller.mapper.set_mapping('a', 'x')
controller.mapper.set_mapping('b', 'y')
```

### Button-Kombos

```python
from mapper import AdvancedButtonMapper

# Verwende den erweiterten Mapper
controller = JamConController('jc_main', 'PRO_CONTROLLER')
controller.mapper = AdvancedButtonMapper('jc_main')

# A+B zusammen = X
controller.mapper.add_combo_mapping(('a', 'b'), 'x')
```

### Button-Invertierung

```python
# L-Button invertieren (gedrückt = nicht gedrückt)
controller.mapper.set_inverted('l', True)
```

## 🐛 Troubleshooting

### Controller verbindet nicht

```bash
# Bluetooth-Status prüfen
sudo systemctl status bluetooth

# Bluetooth neustarten
sudo systemctl restart bluetooth
sudo hciconfig hci0 up
sudo hciconfig hci0 piscan
```

### Keine Root-Rechte

JamCon benötigt Root-Rechte für Bluetooth:

```bash
sudo python3 main.py
```

### Import-Fehler

```bash
# Joycontrol neu installieren
cd joycontrol
sudo python3 setup.py install
```

### Verbindung bricht ab

- Stelle sicher, dass die Switch in Reichweite ist
- Prüfe ob andere Bluetooth-Geräte stören
- Teste mit einem anderen Bluetooth-Dongle

## 📚 Mehrere Controller

Du kannst mehrere Controller gleichzeitig emulieren:

```python
import asyncio

async def main():
    # Zwei Controller erstellen
    controller1 = JamConController('jc_left', 'JOYCON_L')
    controller2 = JamConController('jc_right', 'JOYCON_R')
    
    # Beide verbinden
    await controller1.start()
    await controller2.start()
    
    # Parallel laufen lassen
    await asyncio.gather(
        controller1.run_input_loop(),
        controller2.run_input_loop()
    )
```

## ⚠️ Hinweise

### Dieses Projekt ist noch in Entwicklung

- Dieses Projekt ist nur für **Bildungs- und Forschungszwecke**
- Verwende es nicht für unfaire Vorteile in Online-Spielen
- Der Autor übernimmt keine Haftung für Missbrauch

## 🤝 Danksagungen

- [joycontrol](https://github.com/mart1nro/joycontrol) von mart1nro
- Nintendo Switch Reverse-Engineering Community

## 📄 Lizenz

Nur für Bildungs- und Forschungszwecke. Nicht für kommerzielle Nutzung.

## 🔗 Links

- [Joycontrol Dokumentation](https://github.com/mart1nro/joycontrol)
- 
