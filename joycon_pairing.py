#!/usr/bin/env python3
"""
Joy-Con automatic discovery and pairing module
Handles Bluetooth connection to physical Joy-Con controllers
"""

import asyncio
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass
import subprocess
import re

logger = logging.getLogger(__name__)


@dataclass
class JoyConDevice:
    """Represents a connected Joy-Con controller"""
    mac_address: str
    device_type: str  # 'JOYCON_L', 'JOYCON_R', or 'PRO_CONTROLLER'
    name: str
    battery_level: int = 100
    connected: bool = False


class JoyConPairingManager:
    """Manages Joy-Con discovery, pairing, and connection"""
    
    # Joy-Con Bluetooth device name patterns
    JOYCON_PATTERNS = [
        r'Joy-Con \(L\)',
        r'Joy-Con \(R\)',
        r'Pro Controller',
    ]
    
    def _determine_type(self, device_name: str) -> str:
        """Determine Joy-Con type from device name"""
        if 'Joy-Con (L)' in device_name:
            return 'JOYCON_L'
        elif 'Joy-Con (R)' in device_name:
            return 'JOYCON_R'
        elif 'Pro Controller' in device_name:
            return 'PRO_CONTROLLER'
        return 'UNKNOWN'
    
    async def _pair_device(self, device: JoyConDevice) -> bool:
        """
        Pair with a specific Joy-Con device
        
        Args:
            device: JoyConDevice to pair with
            
        Returns:
            True if pairing successful, False otherwise
        """
        logger.info(f"Pairing with {device.name} ({device.mac_address})...")
        
        try:
            # Use bluetoothctl to pair and trust
            commands = [
                f'pair {device.mac_address}',
                f'trust {device.mac_address}',
                f'connect {device.mac_address}'
            ]
            
            for cmd in commands:
                success = await self._run_bluetoothctl_command(cmd)
                if not success:
                    logger.warning(f"Failed to execute: {cmd}")
                    # Continue anyway, sometimes devices are already paired
                
                await asyncio.sleep(1)
            
            # Verify connection
            is_connected = await self._verify_connection(device.mac_address)
            
            if is_connected:
                device.connected = True
                logger.info(f"Successfully paired and connected to {device.name}")
                return True
            else:
                logger.error(f"Failed to verify connection to {device.name}")
                return False
        
        except Exception as e:
            logger.error(f"Error pairing device {device.name}: {e}")
            return False
    
    async def _run_bluetoothctl_command(self, command: str) -> bool:
        """
        Execute a bluetoothctl command
        
        Args:
            command: Command to execute
            
        Returns:
            True if successful, False otherwise
        """
        try:
            process = await asyncio.create_subprocess_exec(
                'bluetoothctl',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send command
            process.stdin.write(f'{command}\n'.encode())
            await process.stdin.drain()
            
            # Wait for output
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=b'quit\n'),
                    timeout=10
                )
                
                output = stdout.decode('utf-8', errors='ignore')
                
                # Check for success indicators
                success_patterns = [
                    'Pairing successful',
                    'Connection successful',
                    'trust succeeded',
                    'already paired',
                    'already connected'
                ]
                
                for pattern in success_patterns:
                    if pattern.lower() in output.lower():
                        return True
                
                # If no explicit success but no error, assume success
                if 'failed' not in output.lower() and 'error' not in output.lower():
                    return True
                
            except asyncio.TimeoutError:
                logger.warning(f"Command timeout: {command}")
                process.kill()
                
        except Exception as e:
            logger.error(f"Error executing bluetoothctl command: {e}")
        
        return False
    
    async def _verify_connection(self, mac_address: str) -> bool:
        """
        Verify that a device is connected
        
        Args:
            mac_address: MAC address to check
            
        Returns:
            True if connected, False otherwise
        """
        try:
            result = subprocess.run(
                ['bluetoothctl', 'info', mac_address],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.lower()
            return 'connected: yes' in output
            
        except Exception as e:
            logger.error(f"Error verifying connection: {e}")
            return False
    
    async def disconnect_all(self):
        """Disconnect all connected Joy-Cons"""
        logger.info("Disconnecting all Joy-Cons...")
        
        for mac, device in self.connected_joycons.items():
            try:
                await self._run_bluetoothctl_command(f'disconnect {mac}')
                device.connected = False
                logger.info(f"Disconnected {device.name}")
            except Exception as e:
                logger.error(f"Error disconnecting {device.name}: {e}")
        
        self.connected_joycons.clear()
    
    def get_connected_joycons(self) -> List[JoyConDevice]:
        """Get list of currently connected Joy-Cons"""
        return [d for d in self.connected_joycons.values() if d.connected]
    
    async def read_input(self, mac_address: str) -> Optional[Dict]:
        """
        Read input data from a connected Joy-Con
        
        Args:
            mac_address: MAC address of Joy-Con to read from
            
        Returns:
            Dictionary of button states, or None if unavailable
        """
        device = self.connected_joycons.get(mac_address)
        if not device or not device.connected:
            return None
        
        # This would integrate with hid library to read actual Joy-Con data
        # For now, this is a placeholder that would be implemented based on
        # the Joy-Con HID protocol
        
        # Example structure of what would be returned:
        return {
            'buttons': {
                'a': False, 'b': False, 'x': False, 'y': False,
                'l': False, 'r': False, 'zl': False, 'zr': False,
                'plus': False, 'minus': False, 'home': False, 'capture': False,
                'left_stick': False, 'right_stick': False
            },
            'dpad': {
                'up': False, 'down': False, 'left': False, 'right': False
            },
            'sticks': {
                'left': {'x': 0, 'y': 0},
                'right': {'x': 0, 'y': 0}
            },
            'battery': device.battery_level
        } __init__(self):
        self.connected_joycons: Dict[str, JoyConDevice] = {}
        self.scanning = False
    
    async def discover_and_pair(self, timeout: int = 30) -> List[JoyConDevice]:
        """
        Automatically discover and pair with nearby Joy-Con controllers
        
        Args:
            timeout: Maximum time to scan in seconds
            
        Returns:
            List of successfully paired JoyConDevice objects
        """
        logger.info(f"Starting Joy-Con discovery (timeout: {timeout}s)...")
        self.scanning = True
        
        try:
            # Ensure Bluetooth is ready
            await self._prepare_bluetooth()
            
            # Scan for Joy-Con devices
            discovered = await self._scan_for_joycons(timeout)
            
            if not discovered:
                logger.warning("No Joy-Con devices discovered")
                return []
            
            # Attempt to pair each discovered device
            paired_devices = []
            for device in discovered:
                success = await self._pair_device(device)
                if success:
                    paired_devices.append(device)
                    self.connected_joycons[device.mac_address] = device
            
            logger.info(f"Successfully paired {len(paired_devices)} device(s)")
            return paired_devices
            
        finally:
            self.scanning = False
    
    async def _prepare_bluetooth(self):
        """Ensure Bluetooth adapter is ready for pairing"""
        logger.debug("Preparing Bluetooth adapter...")
        
        commands = [
            ['sudo', 'hciconfig', 'hci0', 'up'],
            ['sudo', 'hciconfig', 'hci0', 'piscan'],
            ['sudo', 'systemctl', 'restart', 'bluetooth'],
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    logger.warning(f"Command {' '.join(cmd)} returned {result.returncode}")
            except subprocess.TimeoutExpired:
                logger.warning(f"Command {' '.join(cmd)} timed out")
            except Exception as e:
                logger.warning(f"Error running {' '.join(cmd)}: {e}")
        
        # Give Bluetooth time to stabilise
        await asyncio.sleep(2)
    
    async def _scan_for_joycons(self, timeout: int) -> List[JoyConDevice]:
        """
        Scan for Joy-Con devices using bluetoothctl
        
        Returns:
            List of discovered JoyConDevice objects
        """
        logger.info("Scanning for Bluetooth devices...")
        
        discovered = []
        scan_process = None
        
        try:
            # Start bluetoothctl scan
            scan_process = await asyncio.create_subprocess_exec(
                'bluetoothctl',
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send scan on command
            scan_process.stdin.write(b'scan on\n')
            await scan_process.stdin.drain()
            
            # Monitor output for Joy-Con devices
            start_time = asyncio.get_event_loop().time()
            seen_macs = set()
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    line = await asyncio.wait_for(
                        scan_process.stdout.readline(),
                        timeout=1.0
                    )
                    
                    if not line:
                        break
                    
                    line_str = line.decode('utf-8', errors='ignore').strip()
                    
                    # Parse device info
                    device = self._parse_device_line(line_str)
                    if device and device.mac_address not in seen_macs:
                        logger.info(f"Discovered: {device.name} ({device.mac_address})")
                        discovered.append(device)
                        seen_macs.add(device.mac_address)
                        
                        # If we found a Joy-Con, we can stop early
                        if len(discovered) >= 1:
                            logger.info("Joy-Con found, ending scan early")
                            break
                
                except asyncio.TimeoutError:
                    continue
            
            # Stop scan
            scan_process.stdin.write(b'scan off\n')
            await scan_process.stdin.drain()
            
        except Exception as e:
            logger.error(f"Error during Bluetooth scan: {e}")
        
        finally:
            if scan_process:
                try:
                    scan_process.stdin.write(b'quit\n')
                    await scan_process.stdin.drain()
                    await asyncio.wait_for(scan_process.wait(), timeout=2)
                except:
                    scan_process.kill()
        
        return discovered
    
    def _parse_device_line(self, line: str) -> Optional[JoyConDevice]:
        """Parse a bluetoothctl output line for Joy-Con info"""
        
        # Look for device discovery lines
        # Format: [NEW] Device XX:XX:XX:XX:XX:XX Name
        match = re.search(r'\[(?:NEW|CHG)\] Device ([0-9A-F:]+) (.+)', line, re.IGNORECASE)
        if not match:
            return None
        
        mac_address = match.group(1).upper()
        device_name = match.group(2).strip()
        
        # Check if it's a Joy-Con
        for pattern in self.JOYCON_PATTERNS:
            if re.search(pattern, device_name, re.IGNORECASE):
                device_type = self._determine_type(device_name)
                return JoyConDevice(
                    mac_address=mac_address,
                    device_type=device_type,
                    name=device_name
                )
        
        return None
    
    def
