#!/usr/bin/env python3
"""
JamCon - Joy-Con Proxy Device Main Application
Runs on Raspberry Pi Zero 2 W with custom PCB control interface
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from joycon_pairing import JoyConPairingManager
from pcb_controller import PCBController, PCBEvent
from switch_emulator import SwitchProControllerEmulator
from mapper import ButtonMapper, MappingProfile
from led_controller import LEDController, LEDState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JamConProxy:
    """Main proxy application coordinator"""
    
    def __init__(self):
        self.led = LEDController(gpio_pin=24)
        self.pcb = PCBController(
            up_pin=17,
            down_pin=27,
            left_pin=22,
            right_pin=23
        )
        self.pairing_manager = JoyConPairingManager()
        self.mapper = ButtonMapper()
        self.emulator: Optional[SwitchProControllerEmulator] = None
        self.running = False
        self.paired = False
        self.confirmed = False
        
    async def start(self):
        """Start the proxy application"""
        logger.info("JamCon Proxy Device starting...")
        self.running = True
        
        # Initialize LED controller
        await self.led.start()
        self.led.set_state(LEDState.SCANNING)
        
        # Initialize PCB controller
        await self.pcb.start()
        self.pcb.register_callback(self._handle_pcb_event)
        
        # Start main workflow
        await self._main_workflow()
    
    async def _main_workflow(self):
        """Main application workflow"""
        try:
            # Phase 1: Automatic Joy-Con pairing
            await self._pairing_phase()
            
            # Phase 2: Wait for user confirmation
            await self._confirmation_phase()
            
            # Phase 3: Start proxy operation
            await self._proxy_phase()
            
        except Exception as e:
            logger.error(f"Error in main workflow: {e}", exc_info=True)
            self.led.set_state(LEDState.ERROR)
            await asyncio.sleep(3)
            await self.shutdown()
    
    async def _pairing_phase(self):
        """Automatic Joy-Con detection and pairing"""
        logger.info("=== Pairing Phase Started ===")
        self.led.set_state(LEDState.SCANNING)
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Scanning for Joy-Cons (attempt {attempt}/{max_attempts})...")
            
            # Automatically discover and pair Joy-Cons
            joycons = await self.pairing_manager.discover_and_pair(timeout=30)
            
            if joycons:
                logger.info(f"Successfully paired {len(joycons)} Joy-Con(s)")
                self.paired = True
                self.led.set_state(LEDState.PAIRED)
                return
            
            logger.warning(f"No Joy-Cons found on attempt {attempt}")
            await asyncio.sleep(2)
        
        # If we get here, pairing failed
        logger.error("Failed to pair Joy-Cons after multiple attempts")
        self.led.set_state(LEDState.ERROR)
        raise RuntimeError("Joy-Con pairing failed")
    
    async def _confirmation_phase(self):
        """Wait for PCB button press to confirm pairing"""
        logger.info("=== Confirmation Phase Started ===")
        logger.info("Press any arrow button on PCB to confirm pairing...")
        
        self.confirmed = False
        confirmation_timeout = 60  # seconds
        
        # Wait for any button press
        start_time = asyncio.get_event_loop().time()
        while not self.confirmed and self.running:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > confirmation_timeout:
                logger.error("Confirmation timeout - no button pressed")
                self.led.set_state(LEDState.ERROR)
                raise RuntimeError("User confirmation timeout")
            
            await asyncio.sleep(0.1)
        
        if self.confirmed:
            logger.info("Pairing confirmed by user!")
            await self.led.blink(count=2, duration=0.2)
            self.led.set_state(LEDState.CONNECTED)
    
    async def _proxy_phase(self):
        """Main proxy operation with button remapping"""
        logger.info("=== Proxy Phase Started ===")
        
        # Initialize Switch emulator with default A<->B mapping
        self.emulator = SwitchProControllerEmulator(
            mapper=self.mapper,
            joycon_manager=self.pairing_manager
        )
        
        # Set default mapping (A <-> B)
        self.mapper.set_profile(MappingProfile.DEFAULT)
        logger.info("Default mapping active: A ↔ B")
        
        # Start emulator
        await self.emulator.start()
        self.led.set_state(LEDState.CONNECTED)
        
        logger.info("Proxy is now active! Joy-Cons -> Pi -> Switch")
        logger.info("Use PCB buttons to adjust mappings:")
        logger.info("  UP: Toggle A↔B swap")
        logger.info("  DOWN: Toggle X↔Y swap")
        logger.info("  LEFT: Reset all mappings (passthrough)")
        logger.info("  RIGHT: Cycle mapping profiles")
        logger.info("  LEFT+DOWN (3s): Re-pair Joy-Cons")
        
        # Keep running and forwarding inputs
        try:
            await self.emulator.run()
        except Exception as e:
            logger.error(f"Emulator error: {e}", exc_info=True)
            self.led.set_state(LEDState.ERROR)
            raise
    
    async def _handle_pcb_event(self, event: PCBEvent):
        """Handle PCB button press events"""
        
        # During confirmation phase, any button confirms
        if not self.confirmed and self.paired:
            logger.info(f"PCB button {event.button} pressed - confirming pairing")
            self.confirmed = True
            return
        
        # During proxy phase, buttons adjust mappings
        if self.emulator and self.confirmed:
            if event.button == 'UP':
                await self._toggle_ab_mapping()
            elif event.button == 'DOWN':
                await self._toggle_xy_mapping()
            elif event.button == 'LEFT':
                await self._reset_mappings()
            elif event.button == 'RIGHT':
                await self._cycle_profiles()
            elif event.button == 'LEFT+DOWN' and event.hold_time >= 3.0:
                await self._trigger_repair()
    
    async def _toggle_ab_mapping(self):
        """Toggle A <-> B button swap"""
        current = self.mapper.get_mapping('a')
        if current == 'b':
            self.mapper.set_mapping('a', 'a')
            self.mapper.set_mapping('b', 'b')
            logger.info("A↔B swap disabled (passthrough)")
        else:
            self.mapper.set_mapping('a', 'b')
            self.mapper.set_mapping('b', 'a')
            logger.info("A↔B swap enabled")
        
        await self.led.blink(count=2, duration=0.15)
    
    async def _toggle_xy_mapping(self):
        """Toggle X <-> Y button swap"""
        current = self.mapper.get_mapping('x')
        if current == 'y':
            self.mapper.set_mapping('x', 'x')
            self.mapper.set_mapping('y', 'y')
            logger.info("X↔Y swap disabled (passthrough)")
        else:
            self.mapper.set_mapping('x', 'y')
            self.mapper.set_mapping('y', 'x')
            logger.info("X↔Y swap enabled")
        
        await self.led.blink(count=2, duration=0.15)
    
    async def _reset_mappings(self):
        """Reset all mappings to passthrough"""
        self.mapper.set_profile(MappingProfile.PASSTHROUGH)
        logger.info("All mappings reset to passthrough")
        await self.led.blink(count=3, duration=0.15)
    
    async def _cycle_profiles(self):
        """Cycle through available mapping profiles"""
        next_profile = self.mapper.cycle_profile()
        logger.info(f"Switched to profile: {next_profile.value}")
        await self.led.blink(count=2, duration=0.15)
    
    async def _trigger_repair(self):
        """Trigger Joy-Con re-pairing process"""
        logger.info("Re-pairing requested by user")
        await self.led.blink(count=4, duration=0.2)
        
        # Stop emulator
        if self.emulator:
            await self.emulator.stop()
        
        # Disconnect Joy-Cons
        await self.pairing_manager.disconnect_all()
        
        # Reset states
        self.paired = False
        self.confirmed = False
        
        # Restart workflow
        await self._main_workflow()
    
    async def shutdown(self):
        """Clean shutdown of all components"""
        logger.info("Shutting down JamCon Proxy...")
        self.running = False
        
        if self.emulator:
            await self.emulator.stop()
        
        await self.pairing_manager.disconnect_all()
        await self.pcb.stop()
        await self.led.stop()
        
        logger.info("Shutdown complete")


async def main():
    """Application entry point"""
    proxy = JamConProxy()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(proxy.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await proxy.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await proxy.shutdown()


if __name__ == '__main__':
    # Verify we're running as root (required for Bluetooth)
    import os
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (sudo)")
        sys.exit(1)
    
    # Run the async application
    asyncio.run(main())
