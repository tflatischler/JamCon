#!/usr/bin/env python3
"""
Switch Pro Controller Emulator
Emulates a Pro Controller to the Nintendo Switch using joycontrol
"""

import asyncio
import logging
from typing import Optional, Dict
from joycontrol import logging_default as log
from joycontrol.controller import Controller
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from joycontrol.controller_state import ControllerState, button_push

from mapper import ButtonMapper
from joycon_pairing import JoyConPairingManager

logger = logging.getLogger(__name__)


class SwitchProControllerEmulator:
    """Emulates a Pro Controller to Nintendo Switch"""
    
    def __init__(self, mapper: ButtonMapper, joycon_manager: JoyConPairingManager):
        """
        Initialize Switch emulator
        
        Args:
            mapper: ButtonMapper instance for input remapping
            joycon_manager: JoyConPairingManager for reading Joy-Con inputs
        """
        self.mapper = mapper
        self.joycon_manager = joycon_manager
        self.controller: Optional[Controller] = None
        self.controller_state: Optional[ControllerState] = None
        self.running = False
        self.transport = None
        self.protocol = None
        
        logger.info("Switch Pro Controller Emulator initialized")
    
    async def start(self):
        """Initialize and connect emulated controller to Switch"""
        logger.info("Starting Switch Pro Controller emulation...")
        
        try:
            # Create HID server for Pro Controller
            factory = controller_protocol_factory(Controller.PRO_CONTROLLER)
            self.transport, self.protocol = await create_hid_server(
                factory,
                reconnect_bt_addr=None,
                ctl_psm=17,
                itr_psm=19
            )
            
            self.controller_state = self.protocol.get_controller_state()
            
            logger.info("Emulated Pro Controller ready")
            logger.info("Waiting for Switch to connect...")
            logger.info("On Switch: System -> Controllers -> Change Grip/Order")
            
            # Wait for connection
            await self._wait_for_switch_connection()
            
            self.running = True
            logger.info("Successfully connected to Nintendo Switch!")
            
        except Exception as e:
            logger.error(f"Error starting emulator: {e}", exc_info=True)
            raise
    
    async def _wait_for_switch_connection(self, timeout: int = 60):
        """
        Wait for Switch to connect
        
        Args:
            timeout: Maximum wait time in seconds
        """
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if self.protocol and self.protocol.transport:
                # Check if we have an active connection
                if hasattr(self.protocol, 'connection_established'):
                    if self.protocol.connection_established:
                        return
            
            await asyncio.sleep(0.5)
        
        raise TimeoutError("Switch did not connect within timeout period")
    
    async def stop(self):
        """Stop emulator and disconnect"""
        logger.info("Stopping emulator...")
        self.running = False
        
        if self.transport:
            self.transport.close()
        
        logger.info("Emulator stopped")
    
    async def run(self):
        """Main emulation loop - forwards mapped Joy-Con inputs to Switch"""
        logger.info("Starting input forwarding loop...")
        
        previous_states = {}
        
        try:
            while self.running:
                # Get input from all connected Joy-Cons
                joycons = self.joycon_manager.get_connected_joycons()
                
                if not joycons:
                    await asyncio.sleep(0.01)
                    continue
                
                # Read inputs from first Joy-Con (or combine multiple)
                for joycon in joycons:
                    raw_input = await self.joycon_manager.read_input(joycon.mac_address)
                    
                    if not raw_input:
                        continue
                    
                    # Apply button mapping
                    mapped_input = self._apply_mapping(raw_input)
                    
                    # Send to Switch
                    await self._send_to_switch(mapped_input, previous_states)
                    
                    # Update previous states
                    previous_states = mapped_input['buttons'].copy()
                
                # Polling rate: ~100Hz (10ms delay)
                await asyncio.sleep(0.01)
        
        except asyncio.CancelledError:
            logger.info("Input forwarding cancelled")
        except Exception as e:
            logger.error(f"Error in input forwarding: {e}", exc_info=True)
            raise
    
    def _apply_mapping(self, raw_input: Dict) -> Dict:
        """
        Apply button mapping to raw Joy-Con input
        
        Args:
            raw_input: Raw input from Joy-Con
            
        Returns:
            Mapped input data
        """
        mapped_buttons = self.mapper.map_buttons(raw_input['buttons'])
        mapped_dpad = self.mapper.map_buttons(raw_input['dpad'])
        
        return {
            'buttons': mapped_buttons,
            'dpad': mapped_dpad,
            'sticks': raw_input['sticks'],  # Sticks not remapped
            'battery': raw_input.get('battery', 100)
        }
    
    async def _send_to_switch(self, input_data: Dict, previous_states: Dict):
        """
        Send input data to Switch
        
        Args:
            input_data: Mapped input data
            previous_states: Previous button states for edge detection
        """
        if not self.controller_state:
            return
        
        try:
            # Update button states
            await self._update_buttons(input_data['buttons'], previous_states)
            
            # Update D-pad
            await self._update_dpad(input_data['dpad'])
            
            # Update analog sticks
            await self._update_sticks(input_data['sticks'])
            
        except Exception as e:
            logger.error(f"Error sending input to Switch: {e}")
    
    async def _update_buttons(self, button_states: Dict[str, bool], previous: Dict):
        """Update button states on emulated controller"""
        
        button_mapping = {
            'a': self.controller_state.button_state.a,
            'b': self.controller_state.button_state.b,
            'x': self.controller_state.button_state.x,
            'y': self.controller_state.button_state.y,
            'l': self.controller_state.button_state.l,
            'r': self.controller_state.button_state.r,
            'zl': self.controller_state.button_state.zl,
            'zr': self.controller_state.button_state.zr,
            'plus': self.controller_state.button_state.plus,
            'minus': self.controller_state.button_state.minus,
            'home': self.controller_state.button_state.home,
            'capture': self.controller_state.button_state.capture,
            'left_stick': self.controller_state.button_state.l_stick,
            'right_stick': self.controller_state.button_state.r_stick,
        }
        
        for button_name, state in button_states.items():
            if button_name not in button_mapping:
                continue
            
            button_obj = button_mapping[button_name]
            previous_state = previous.get(button_name, False)
            
            # Only update on state change
            if state != previous_state:
                if state:
                    await button_obj.push()
                else:
                    await button_obj.release()
    
    async def _update_dpad(self, dpad_states: Dict[str, bool]):
        """Update D-pad states"""
        
        if dpad_states.get('up'):
            self.controller_state.button_state.set_button('up')
        else:
            self.controller_state.button_state.clear_button('up')
        
        if dpad_states.get('down'):
            self.controller_state.button_state.set_button('down')
        else:
            self.controller_state.button_state.clear_button('down')
        
        if dpad_states.get('left'):
            self.controller_state.button_state.set_button('left')
        else:
            self.controller_state.button_state.clear_button('left')
        
        if dpad_states.get('right'):
            self.controller_state.button_state.set_button('right')
        else:
            self.controller_state.button_state.clear_button('right')
    
    async def _update_sticks(self, stick_data: Dict):
        """
        Update analog stick positions
        
        Args:
            stick_data: Dictionary with 'left' and 'right' stick coordinates
        """
        if 'left' in stick_data:
            left_x = stick_data['left'].get('x', 0)
            left_y = stick_data['left'].get('y', 0)
            self.controller_state.l_stick_state.set_center()
            self.controller_state.l_stick_state.set_h(
                self._normalize_stick_value(left_x)
            )
            self.controller_state.l_stick_state.set_v(
                self._normalize_stick_value(left_y)
            )
        
        if 'right' in stick_data:
            right_x = stick_data['right'].get('x', 0)
            right_y = stick_data['right'].get('y', 0)
            self.controller_state.r_stick_state.set_center()
            self.controller_state.r_stick_state.set_h(
                self._normalize_stick_value(right_x)
            )
            self.controller_state.r_stick_state.set_v(
                self._normalize_stick_value(right_y)
            )
    
    def _normalize_stick_value(self, value: int) -> int:
        """
        Normalize stick value from Joy-Con range to Pro Controller range
        
        Joy-Con sticks typically range from 0-4095 (12-bit)
        Pro Controller expects similar range
        
        Args:
            value: Raw stick value
            
        Returns:
            Normalized value
        """
        # This is a simplified normalization
        # Real implementation would need calibration data
        return max(0, min(4095, value))
    
    async def send_button_press(self, button: str, duration: float = 0.1):
        """
        Manually send a button press (for testing or special commands)
        
        Args:
            button: Button name
            duration: Press duration in seconds
        """
        if not self.controller_state:
            return
        
        await button_push(self.controller_state, button, duration)
        logger.debug(f"Sent button press: {button}")


# Test/standalone mode
async def test_emulator():
    """Test the emulator in standalone mode"""
    logger.info("=== Switch Emulator Test Mode ===")
    
    # Create mock components
    mapper = ButtonMapper()
    joycon_manager = JoyConPairingManager()
    
    emulator = SwitchProControllerEmulator(mapper, joycon_manager)
    
    try:
        await emulator.start()
        
        logger.info("Emulator started. Press Ctrl+C to exit.")
        logger.info("Note: This test mode won't forward real inputs without paired Joy-Cons")
        
        # Test button press
        await asyncio.sleep(2)
        await emulator.send_button_press('a')
        await asyncio.sleep(1)
        await emulator.send_button_press('b')
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Test interrupted")
    finally:
        await emulator.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_emulator())
