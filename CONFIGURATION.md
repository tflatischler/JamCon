# JamCon Configuration & Troubleshooting Guide

## Quick Start Guide

### First Time Setup

1. **Flash Raspberry Pi OS**
   ```bash
   # Download Raspberry Pi OS Lite (recommended)
   # Use Raspberry Pi Imager to flash to microSD card
   # Enable SSH in imager settings (optional but recommended)
   ```

2. **Initial Configuration**
   ```bash
   # Update system
   sudo apt-get update && sudo apt-get upgrade -y
   
   # Clone JamCon
   git clone https://github.com/tflatischler/JamCon.git
   cd JamCon
   
   # Run setup
   sudo bash setup.sh
   ```

3. **Hardware Connection**
   - Connect PCB via 10-pin FPC connector
   - Verify LED is visible (GPIO 24)
   - Ensure all buttons are properly connected

4. **First Run**
   ```bash
   sudo python3 main.py
   ```

## Hardware Configuration

### GPIO Pinout Verification

Test individual GPIO pins before running the main application:

```bash
# Test UP button (GPIO 17)
gpio -g mode 17 in
gpio -g mode 17 up
gpio -g read 17  # Should return 1 (not pressed) or 0 (pressed)

# Test LED (GPIO 24)
gpio -g mode 24 out
gpio -g write 24 1  # LED on
gpio -g write 24 0  # LED off
```

### PCB Button Testing

Run the standalone PCB controller test:

```bash
sudo python3 pcb_controller.py
```

This will display button press events in real-time. Press each arrow button to verify connectivity.

### Custom Pin Configuration

If you need to use different GPIO pins, edit the pin assignments in `main.py`:

```python
self.pcb = PCBController(
    up_pin=17,      # Change to your UP button GPIO
    down_pin=27,    # Change to your DOWN button GPIO
    left_pin=22,    # Change to your LEFT button GPIO
    right_pin=23    # Change to your RIGHT button GPIO
)

self.led = LEDController(gpio_pin=24)  # Change to your LED GPIO
```

## Bluetooth Configuration

### Optimising Bluetooth Performance

Edit `/etc/bluetooth/main.conf`:

```ini
[General]
Name = JamCon-Proxy
Class = 0x002508
DiscoverableTimeout = 0
PairableTimeout = 0

[Policy]
AutoEnable=true
```

Restart Bluetooth:
```bash
sudo systemctl restart bluetooth
```

### Bluetooth Troubleshooting

#### Joy-Cons Won't Pair

1. **Reset Bluetooth adapter**:
   ```bash
   sudo systemctl stop bluetooth
   sudo rfkill unblock bluetooth
   sudo systemctl start bluetooth
   sudo hciconfig hci0 up
   sudo hciconfig hci0 piscan
   ```

2. **Remove old pairings**:
   ```bash
   bluetoothctl
   > devices  # List all devices
   > remove XX:XX:XX:XX:XX:XX  # Remove Joy-Con MAC address
   > exit
   ```

3. **Check Bluetooth status**:
   ```bash
   hciconfig -a
   sudo systemctl status bluetooth
   ```

4. **Increase Bluetooth scan timeout**:
   Edit `joycon_pairing.py` and increase timeout:
   ```python
   joycons = await self.pairing_manager.discover_and_pair(timeout=60)  # Increase from 30
   ```

#### Switch Won't Detect Emulated Controller

1. **Verify joycontrol installation**:
   ```bash
   pip3 list | grep joycontrol
   python3 -c "import joycontrol; print(joycontrol.__file__)"
   ```

2. **Check Bluetooth discoverability**:
   ```bash
   sudo hciconfig hci0 piscan
   sudo hciconfig hci0 sspmode 1
   ```

3. **Test with joycontrol directly**:
   ```bash
   cd joycontrol
   sudo python3 run_controller_cli.py PRO_CONTROLLER
   ```

## Button Mapping Configuration

### Creating Custom Profiles

Edit `mapper.py` to add custom mapping profiles:

```python
PROFILES = {
    # ... existing profiles ...
    
    MappingProfile.CUSTOM: {
        'a': 'x',      # A button acts as X
        'b': 'y',      # B button acts as Y
        'x': 'a',      # X button acts as A
        'y': 'b',      # Y button acts as B
        'l': 'zl',     # L acts as ZL
        'r': 'zr',     # R acts as ZR
    },
}
```

Then update the `MappingProfile` enum:

```python
class MappingProfile(Enum):
    PASSTHROUGH = 'passthrough'
    DEFAULT = 'default'
    FIGHTING = 'fighting'
    PLATFORMER = 'platformer'
    CUSTOM = 'custom'  # Add your custom profile
```

### Runtime Mapping Changes

The PCB buttons allow runtime configuration:

| Button | Action |
|--------|--------|
| **UP** | Toggle A ↔ B swap |
| **DOWN** | Toggle X ↔ Y swap |
| **LEFT** | Reset all mappings (passthrough) |
| **RIGHT** | Cycle through profiles |
| **LEFT+DOWN (3s)** | Re-pair Joy-Cons |

### Programmatic Mapping

You can also change mappings programmatically in `main.py`:

```python
# After emulator starts, add custom mappings
await self.emulator.start()

# Swap specific buttons
self.mapper.set_mapping('l', 'r')
self.mapper.set_mapping('r', 'l')

# Or load a specific profile
self.mapper.set_profile(MappingProfile.FIGHTING)
```

## Performance Optimisation

### Reduce Input Latency

1. **Increase polling rate** in `switch_emulator.py`:
   ```python
   # Change from 10ms to 5ms (200Hz)
   await asyncio.sleep(0.005)
   ```

2. **Disable unnecessary services**:
   ```bash
   sudo systemctl disable avahi-daemon
   sudo systemctl disable triggerhappy
   ```

3. **Overclock Pi Zero 2 W** (requires cooling):
   Edit `/boot/config.txt`:
   ```ini
   over_voltage=2
   arm_freq=1200
   ```

### Optimise for Battery Life

1. **Reduce LED brightness** by using PWM in `led_controller.py`
2. **Lower polling rate** to 50Hz (20ms delay)
3. **Disable HDMI** if running headless:
   ```bash
   /usr/bin/tvservice -o
   ```

## LED Status Codes

### Normal Operation

| Pattern | Meaning | Action Required |
|---------|---------|-----------------|
| Rapid blink (5 Hz) | Scanning for Joy-Cons | Ensure Joy-Cons are in pairing mode |
| Slow blink (1 Hz) | Pairing successful | Press any PCB button to confirm |
| Solid on | Proxy active | Normal operation |
| Double blink | Mapping changed | Configuration updated successfully |
| Triple blink | Error state | Check logs for details |
| Off | System idle | Not running or powered down |

### Error Codes

When LED shows triple blink pattern, check system logs:

```bash
# View recent logs
sudo journalctl -u jamcon -n 50

# Follow logs in real-time
sudo journalctl -u jamcon -f

# Check Python errors
sudo python3 main.py 2>&1 | tee jamcon_debug.log
```

Common error patterns:
- **Triple blink + immediate stop**: GPIO permission issue
- **Triple blink after scanning**: Joy-Con pairing failed
- **Triple blink during operation**: Connection lost to Switch or Joy-Con

## Advanced Configuration

### Running as Systemd Service

Enable automatic startup on boot:

```bash
# Enable service
sudo systemctl enable jamcon

# Start service
sudo systemctl start jamcon

# Check status
sudo systemctl status jamcon

# View logs
sudo journalctl -u jamcon -f

# Stop service
sudo systemctl stop jamcon

# Disable auto-start
sudo systemctl disable jamcon
```

### Configuration Persistence

Create a configuration file to save settings:

Create `config.json`:

```json
{
  "gpio_pins": {
    "up": 17,
    "down": 27,
    "left": 22,
    "right": 23,
    "led": 24
  },
  "default_mapping_profile": "default",
  "bluetooth": {
    "scan_timeout": 30,
    "reconnect_attempts": 3
  },
  "performance": {
    "polling_rate_hz": 100,
    "enable_logging": false
  }
}
```

Then modify `main.py` to load this configuration:

```python
import json

class JamConProxy:
    def __init__(self, config_file='config.json'):
        # Load configuration
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Initialize with config values
        pins = config['gpio_pins']
        self.pcb = PCBController(
            up_pin=pins['up'],
            down_pin=pins['down'],
            left_pin=pins['left'],
            right_pin=pins['right']
        )
        self.led = LEDController(gpio_pin=pins['led'])
        # ... rest of initialization
```

### Multiple Joy-Con Support

To proxy multiple Joy-Cons simultaneously, modify `main.py`:

```python
async def _proxy_phase(self):
    """Proxy multiple Joy-Cons"""
    
    # Get all connected Joy-Cons
    joycons = self.pairing_manager.get_connected_joycons()
    
    # Create emulator for each Joy-Con
    emulators = []
    for joycon in joycons:
        if joycon.device_type == 'JOYCON_L':
            emulator = SwitchProControllerEmulator(
                mapper=self.mapper,
                joycon_manager=self.pairing_manager
            )
            # Configure for left Joy-Con
            await emulator.start()
            emulators.append(emulator)
    
    # Run all emulators in parallel
    await asyncio.gather(*[e.run() for e in emulators])
```

### Custom Button Actions

Add custom actions to PCB button presses in `main.py`:

```python
async def _handle_pcb_event(self, event: PCBEvent):
    """Extended PCB event handler with custom actions"""
    
    # Existing handlers...
    
    # Add custom actions
    if event.button == 'UP+RIGHT' and event.hold_time >= 2.0:
        # Custom action: Save current mapping profile
        await self._save_current_profile()
    
    if event.button == 'DOWN+LEFT' and event.hold_time >= 2.0:
        # Custom action: Load saved profile
        await self._load_saved_profile()

async def _save_current_profile(self):
    """Save current mapping configuration"""
    config = self.mapper.export_config()
    with open('saved_profile.json', 'w') as f:
        json.dump(config, f, indent=2)
    logger.info("Profile saved")
    await self.led.blink(count=3, duration=0.2)

async def _load_saved_profile(self):
    """Load saved mapping configuration"""
    try:
        with open('saved_profile.json', 'r') as f:
            config = json.load(f)
        self.mapper.import_config(config)
        logger.info("Profile loaded")
        await self.led.blink(count=3, duration=0.2)
    except FileNotFoundError:
        logger.warning("No saved profile found")
        await self.led.blink(count=5, duration=0.1)
```

## Debugging & Diagnostics

### Enable Debug Logging

For detailed debugging information, modify logging level in `main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jamcon_debug.log'),
        logging.StreamHandler()
    ]
)
```

### Hardware Diagnostics

#### Complete GPIO Test

```bash
# Install gpio utilities if not present
sudo apt-get install -y wiringpi

# Display all GPIO states
gpio readall

# Test all configured pins
for pin in 17 27 22 23 24; do
    echo "Testing GPIO $pin"
    gpio -g mode $pin in
    gpio -g mode $pin up
    echo "State: $(gpio -g read $pin)"
done
```

#### Bluetooth Device Information

```bash
# List all Bluetooth devices
hcitool dev

# Scan for nearby devices
sudo hcitool lescan

# Get detailed adapter info
hciconfig hci0 -a

# Check for Joy-Cons specifically
sudo bluetoothctl << EOF
scan on
EOF
# Wait 10 seconds, then Ctrl+C
# Look for "Joy-Con" in device names
```

#### Joy-Con Battery Status

Add battery monitoring to your script:

```python
async def _monitor_battery(self):
    """Monitor Joy-Con battery levels"""
    while self.running:
        for joycon in self.joycon_manager.get_connected_joycons():
            battery = joycon.battery_level
            logger.info(f"{joycon.name}: {battery}% battery")
            
            if battery < 20:
                logger.warning(f"Low battery on {joycon.name}")
                await self.led.blink(count=5, duration=0.1)
        
        await asyncio.sleep(300)  # Check every 5 minutes
```

### Common Issues & Solutions

#### Issue: "Permission denied" on GPIO

**Solution:**
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Reboot or re-login
sudo reboot
```

#### Issue: Joy-Cons pair but disconnect immediately

**Solution:**
```bash
# Increase Bluetooth connection timeout
sudo hciconfig hci0 lestates

# Edit /etc/bluetooth/main.conf
# Add under [General]:
# ConnectionParameters=6,6,0,420

sudo systemctl restart bluetooth
```

#### Issue: High input latency (>20ms)

**Solutions:**
1. Reduce other Bluetooth devices in range
2. Disable Wi-Fi if not needed:
   ```bash
   sudo rfkill block wifi
   ```
3. Optimise CPU governor:
   ```bash
   echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

#### Issue: LED not working

**Diagnostic:**
```python
# Run standalone LED test
sudo python3 led_controller.py
```

**Solutions:**
- Check LED polarity (anode to GPIO, cathode to ground)
- Verify current-limiting resistor (220Ω)
- Test with multimeter (should see ~3.3V when on)
- Try different GPIO pin

#### Issue: PCB buttons not responding

**Diagnostic:**
```python
# Run standalone PCB test
sudo python3 pcb_controller.py
```

**Solutions:**
- Check FPC connector seating
- Verify pin assignments in code match hardware
- Test continuity with multimeter
- Check for shorts or damaged traces

## Network Configuration

### SSH Access (Optional)

Enable SSH for remote management:

```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Set static IP (edit /etc/dhcpcd.conf)
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

### Web Interface (Advanced)

Create a simple web interface for remote control:

```python
# Install Flask
pip3 install flask

# Create web_interface.py
from flask import Flask, render_template, jsonify
import asyncio

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('control.html')

@app.route('/api/status')
def status():
    return jsonify({
        'connected': proxy.paired,
        'profile': proxy.mapper.get_current_profile().value,
        'joycons': len(proxy.joycon_manager.get_connected_joycons())
    })

@app.route('/api/profile/<name>')
def set_profile(name):
    proxy.mapper.set_profile(MappingProfile(name))
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Security Considerations

### Bluetooth Security

1. **Disable unnecessary services**:
   ```bash
   sudo systemctl disable avahi-daemon
   ```

2. **Firewall configuration**:
   ```bash
   sudo apt-get install ufw
   sudo ufw enable
   sudo ufw allow 22/tcp  # SSH only
   ```

3. **Regular updates**:
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

### Best Practices

- Change default password immediately
- Use SSH keys instead of passwords
- Keep system and packages updated
- Monitor logs for unusual activity
- Disable unused services

## Performance Benchmarks

### Expected Performance

| Metric | Target | Typical |
|--------|--------|---------|
| Input latency | <10ms | 8-12ms |
| Polling rate | 100Hz | 100Hz |
| CPU usage | <30% | 15-25% |
| Memory usage | <100MB | 60-80MB |
| Power consumption | <1.5W | 1.0-1.3W |

### Measuring Latency

```python
import time

async def measure_latency():
    """Measure input-to-output latency"""
    samples = []
    
    for _ in range(100):
        start = time.perf_counter()
        
        # Simulate input processing
        raw_input = await joycon_manager.read_input(mac)
        mapped = mapper.map_buttons(raw_input['buttons'])
        await emulator._send_to_switch(mapped, {})
        
        end = time.perf_counter()
        samples.append((end - start) * 1000)  # Convert to ms
    
    avg_latency = sum(samples) / len(samples)
    print(f"Average latency: {avg_latency:.2f}ms")
```

## Backup & Recovery

### Create System Backup

```bash
# Backup entire SD card (from another Linux machine)
sudo dd if=/dev/sdX of=jamcon_backup.img bs=4M status=progress

# Compress backup
gzip jamcon_backup.img
```

### Configuration Backup

```bash
# Backup configuration and scripts
tar -czf jamcon_config_backup.tar.gz \
    /home/pi/JamCon/*.py \
    /home/pi/JamCon/config.json \
    /etc/systemd/system/jamcon.service

# Restore
tar -xzf jamcon_config_backup.tar.gz -C /
```

## Support & Resources

### Useful Commands

```bash
# Quick status check
sudo systemctl status jamcon bluetooth

# View all logs
sudo journalctl -u jamcon --since "1 hour ago"

# Test Bluetooth
sudo hcitool dev && sudo hcitool lescan

# GPIO status
gpio readall

# System resources
htop
```

### Getting Help

1. Check logs first: `sudo journalctl -u jamcon -n 100`
2. Run in debug mode: `sudo python3 main.py 2>&1 | tee debug.log`
3. Test components individually (PCB, LED, Bluetooth)
4. Check GitHub issues for similar problems
5. Provide detailed error messages when reporting issues

---

**Last Updated:** October 2025  
**Version:** 2.0.0
