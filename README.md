# JamCon - Joy-Con Proxy Device

A Bluetooth Low Energy (BLE) proxy device that intercepts, remaps, and emulates Nintendo Joy-Con controllers using a Raspberry Pi Zero 2 W. This project enables custom button mapping with real-time configuration through a dedicated PCB control interface.

## Overview

JamCon transforms your Raspberry Pi Zero 2 W into an intelligent Joy-Con proxy that sits between your physical Joy-Con controllers and your Nintendo Switch. The device automatically pairs with Joy-Cons, remaps button inputs (e.g., swapping A ↔ B), and presents itself to the Switch as a legitimate controller.

### Key Features

- **Automatic Joy-Con Detection & Pairing**: Seamlessly discovers and connects to Joy-Con controllers via Bluetooth
- **Button Remapping**: Flexible button mapping system with default A ↔ B swap functionality
- **PCB Control Interface**: 4-button arrow PCB for pairing confirmation and runtime mapping adjustments
- **LED Status Indicators**: Visual feedback for pairing, connection, and operational states
- **Pro Controller Emulation**: Presents as a Pro Controller to the Nintendo Switch for maximum compatibility
- **Real-time Configuration**: Adjust button mappings on-the-fly without restarting

## System Requirements

### Hardware

- **Raspberry Pi Zero 2 W** (recommended) or Raspberry Pi 4
- **Bluetooth 4.0+** (integrated in Pi Zero 2 W)
- **Custom Button PCB** with 4 directional arrow buttons
- **10-pin FPC connector** for PCB attachment
- **Status LED** (optional, can use onboard LED)
- **MicroSD card** (8GB minimum, 16GB recommended)
- **Power supply** (5V, 2.5A recommended)

### Software

- **Raspberry Pi OS** (Bullseye or newer, Lite version recommended)
- **Python 3.7+**
- **Root access** (required for Bluetooth operations)

### Pinout Configuration (10-pin FPC Connector)

```
Pin 1  → Up Arrow Button    (GPIO 17)
Pin 2  → Down Arrow Button  (GPIO 27)
Pin 3  → Left Arrow Button  (GPIO 22)
Pin 4  → Right Arrow Button (GPIO 23)
Pin 5  → Ground
Pin 6  → Status LED Anode   (GPIO 24)
Pin 7  → Ground
Pin 8  → 3.3V Power
Pin 9  → Ground
Pin 10 → Ground
```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/tflatischler/JamCon.git
cd JamCon
```

### 2. Run Automated Setup

```bash
sudo bash setup.sh
```

This will install all required dependencies, including:
- System packages (Python, Bluetooth tools, libraries)
- Joycontrol framework
- Python dependencies (hid, aioconsole, crc8, RPi.GPIO)

### 3. Manual Installation (Alternative)

If you prefer manual setup:

```bash
# Update system packages
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-dbus \
    libhidapi-hidraw0 bluetooth bluez bluez-tools git

# Install joycontrol
git clone https://github.com/mart1nro/joycontrol.git
cd joycontrol
pip3 install -r requirements.txt
sudo python3 setup.py install
cd ..

# Install Python dependencies
pip3 install hid aioconsole crc8 RPi.GPIO
```

### 4. Enable Bluetooth

```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
sudo hciconfig hci0 up
sudo hciconfig hci0 piscan
```

## Hardware Setup

### PCB Connection

1. Connect the 10-pin FPC cable from your custom button PCB to the Raspberry Pi
2. Ensure proper orientation (Pin 1 marker alignment)
3. Verify GPIO connections match the pinout configuration above
4. Connect the status LED (if external) to GPIO 24 with appropriate current-limiting resistor (220Ω recommended)

### Physical Joy-Con Preparation

1. Ensure your Joy-Cons are fully charged
2. Remove Joy-Cons from the Switch console
3. Keep Joy-Cons within 2 metres of the Raspberry Pi during pairing

## Usage

### Starting the Proxy Device

```bash
sudo python3 main.py
```

### Pairing Workflow

1. **Automatic Detection Phase**
   - The status LED will blink rapidly (5 Hz)
   - Script automatically scans for nearby Joy-Con controllers
   - Once detected, pairing begins automatically
   - Press the sync button on Joy-Con if needed (inside rail, next to LEDs)

2. **Confirmation Phase**
   - LED blinks slowly (1 Hz) when pairing is successful
   - Press **any arrow button** on the PCB to confirm connection
   - LED becomes solid once confirmed

3. **Proxy Active**
   - Joy-Cons are now proxied through the Raspberry Pi
   - Navigate to Nintendo Switch: System → Controllers → Change Grip/Order
   - The Switch will detect the emulated Pro Controller
   - LED remains solid during normal operation

### Button Mapping Configuration

#### Default Mapping

By default, the following swap is active:
- **A button → B button**
- **B button → A button**

#### Runtime Mapping Adjustment

Use the PCB arrow buttons to modify mappings on-the-fly:

- **Up Arrow**: Swap A ↔ B (toggle)
- **Down Arrow**: Swap X ↔ Y (toggle)
- **Left Arrow**: Reset all mappings to passthrough (no swaps)
- **Right Arrow**: Cycle through preset mapping profiles

**Visual Feedback**: LED blinks twice when a mapping change is applied.

### Pairing Additional Joy-Cons

To pair different Joy-Cons:

1. Press **Left + Down arrows simultaneously** for 3 seconds
2. Current Joy-Cons will disconnect
3. LED returns to rapid blinking (scanning mode)
4. Repeat pairing workflow

## LED Status Reference

| LED Pattern | Meaning |
|-------------|---------|
| Rapid blink (5 Hz) | Scanning for Joy-Cons |
| Slow blink (1 Hz) | Pairing successful, awaiting PCB confirmation |
| Solid on | Proxy active and connected to Switch |
| Double blink | Mapping configuration changed |
| Triple blink | Error state (check console output) |
| Off | System idle or powered down |

## Advanced Configuration

### Custom Button Mappings

Edit `mapper.py` to create custom mapping profiles:

```python
MAPPING_PROFILES = {
    'default': {
        'a': 'b',
        'b': 'a',
    },
    'fighting_game': {
        'a': 'y',
        'b': 'b',
        'x': 'a',
        'y': 'x',
    },
    'platformer': {
        'a': 'b',
        'b': 'y',
        'zl': 'l',
        'zr': 'r',
    }
}
```

Available button identifiers:
- Face buttons: `a`, `b`, `x`, `y`
- Shoulder buttons: `l`, `r`, `zl`, `zr`
- D-pad: `up`, `down`, `left`, `right`
- System buttons: `plus`, `minus`, `home`, `capture`
- Sticks: `left_stick`, `right_stick` (as buttons when pressed)

### Controller Type Selection

Modify `main.py` to change emulated controller type:

```python
# Pro Controller (default, recommended)
controller_type = 'PRO_CONTROLLER'

# Left Joy-Con only
controller_type = 'JOYCON_L'

# Right Joy-Con only
controller_type = 'JOYCON_R'
```

## Troubleshooting

### Joy-Cons Won't Pair

- Verify Bluetooth is enabled: `sudo systemctl status bluetooth`
- Restart Bluetooth service: `sudo systemctl restart bluetooth`
- Check Bluetooth is discoverable: `sudo hciconfig hci0 piscan`
- Ensure Joy-Cons are in pairing mode (hold sync button for 3 seconds)
- Check for interference from other Bluetooth devices

### Switch Doesn't Detect Controller

- Verify you're running the script with `sudo`
- Ensure Switch is in "Change Grip/Order" mode
- Try restarting the Switch
- Check console output for error messages
- Verify joycontrol installation: `pip3 list | grep joycontrol`

### PCB Buttons Not Responding

- Verify GPIO connections using `gpio readall`
- Check continuity of FPC cable connections
- Ensure pull-up resistors are enabled in code (default configuration)
- Test individual GPIOs with `raspi-gpio get`

### LED Not Working

- Verify GPIO 24 connection
- Check LED polarity (anode to GPIO via resistor, cathode to ground)
- Test with: `gpio -g write 24 1` (on) and `gpio -g write 24 0` (off)
- Ensure current-limiting resistor is present (220Ω recommended)

### Performance Issues

- Reduce Bluetooth polling interval in `main.py`
- Disable unnecessary services: `sudo systemctl disable [service_name]`
- Use Raspberry Pi OS Lite for minimal overhead
- Overclock the Pi Zero 2 W (with adequate cooling)

## Project Structure

```
JamCon/
├── main.py              # Main application entry point
├── mapper.py            # Button mapping logic and profiles
├── joycon_pairing.py    # Joy-Con detection and pairing module
├── pcb_controller.py    # PCB button input handler
├── switch_emulator.py   # Switch Pro Controller emulation
├── led_controller.py    # Status LED management
├── setup.sh             # Automated installation script
├── config.json          # Runtime configuration (auto-generated)
├── README.md            # This file
└── hardware/
    └── pcb_schematic.pdf  # PCB design files (optional)
```

## Performance Considerations

- **Latency**: Expect 8-12ms additional input lag due to Bluetooth relay
- **Battery Life**: Joy-Cons maintain normal battery life; Pi draws ~200mA at 5V
- **Range**: Effective range is 2-3 metres from Switch (Bluetooth limitation)
- **Compatibility**: Tested with Switch firmware 18.0.0 (January 2025)

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-mapping`)
3. Commit your changes with clear messages
4. Test thoroughly on physical hardware
5. Submit a pull request with detailed description

## Legal & Ethical Use

⚠️ **Important Notice**

This project is intended for:
- Educational purposes and Bluetooth protocol research
- Accessibility modifications for users with disabilities
- Personal experimentation and learning

**This project must NOT be used for:**
- Gaining unfair advantages in online competitive gaming
- Circumventing game mechanics or anti-cheat systems
- Commercial purposes without proper authorisation

The authors assume no liability for misuse of this software.

## Credits

- **joycontrol** by [mart1nro](https://github.com/mart1nro/joycontrol) - Nintendo Switch controller emulation
- Nintendo Switch reverse-engineering community
- Raspberry Pi Foundation

## Licence

This project is provided for educational and research purposes only. Not for commercial use.

**Nintendo Switch™, Joy-Con™, and Pro Controller™** are registered trademarks of Nintendo Co., Ltd.

---

**Version**: 2.0.0  
**Last Updated**: October 2025  
**Maintainer**: tflatischler
