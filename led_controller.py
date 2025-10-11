#!/usr/bin/env python3
"""
LED Controller Module
Manages status LED indication for various system states
"""

import asyncio
import logging
from enum import Enum

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock for non-Pi testing
    class MockGPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode): pass
        @staticmethod
        def output(pin, state): pass
        @staticmethod
        def cleanup(): pass
    
    GPIO = MockGPIO()

logger = logging.getLogger(__name__)


class LEDState(Enum):
    """LED operational states"""
    OFF = 'off'
    ON = 'on'
    SCANNING = 'scanning'  # Rapid blink (5 Hz)
    PAIRED = 'paired'  # Slow blink (1 Hz)
    CONNECTED = 'connected'  # Solid on
    ERROR = 'error'  # Triple blink pattern


class LEDController:
    """Manages LED status indication"""
    
    def __init__(self, gpio_pin: int = 24):
        """
        Initialize LED controller
        
        Args:
            gpio_pin: GPIO pin number for LED control
        """
        self.gpio_pin = gpio_pin
        self.current_state = LEDState.OFF
        self.running = False
        self.blink_task: asyncio.Task = None
        
        logger.info(f"LED Controller initialized on GPIO {gpio_pin}")
    
    async def start(self):
        """Initialize GPIO for LED"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.OUT)
            GPIO.output(self.gpio_pin, GPIO.LOW)
            
            self.running = True
            logger.info("LED controller started")
            
        except Exception as e:
            logger.error(f"Error starting LED controller: {e}")
            raise
    
    async def stop(self):
        """Stop LED and cleanup"""
        self.running = False
        
        if self.blink_task:
            self.blink_task.cancel()
        
        try:
            GPIO.output(self.gpio_pin, GPIO.LOW)
            logger.info("LED controller stopped")
        except Exception as e:
            logger.error(f"Error stopping LED: {e}")
    
    def set_state(self, state: LEDState):
        """
        Set LED to a specific state
        
        Args:
            state: LEDState to activate
        """
        if not self.running:
            return
        
        # Cancel existing blink task
        if self.blink_task:
            self.blink_task.cancel()
            self.blink_task = None
        
        self.current_state = state
        logger.debug(f"LED state changed to: {state.value}")
        
        # Handle state-specific patterns
        if state == LEDState.OFF:
            GPIO.output(self.gpio_pin, GPIO.LOW)
        
        elif state == LEDState.ON or state == LEDState.CONNECTED:
            GPIO.output(self.gpio_pin, GPIO.HIGH)
        
        elif state == LEDState.SCANNING:
            self.blink_task = asyncio.create_task(
                self._blink_pattern(on_time=0.1, off_time=0.1)
            )
        
        elif state == LEDState.PAIRED:
            self.blink_task = asyncio.create_task(
                self._blink_pattern(on_time=0.5, off_time=0.5)
            )
        
        elif state == LEDState.ERROR:
            self.blink_task = asyncio.create_task(
                self._error_pattern()
            )
    
    async def _blink_pattern(self, on_time: float, off_time: float):
        """
        Continuous blink pattern
        
        Args:
            on_time: Time LED is on (seconds)
            off_time: Time LED is off (seconds)
        """
        try:
            while self.running:
                GPIO.output(self.gpio_pin, GPIO.HIGH)
                await asyncio.sleep(on_time)
                GPIO.output(self.gpio_pin, GPIO.LOW)
                await asyncio.sleep(off_time)
        except asyncio.CancelledError:
            GPIO.output(self.gpio_pin, GPIO.LOW)
    
    async def _error_pattern(self):
        """Triple blink error pattern"""
        try:
            while self.running:
                # Three quick blinks
                for _ in range(3):
                    GPIO.output(self.gpio_pin, GPIO.HIGH)
                    await asyncio.sleep(0.1)
                    GPIO.output(self.gpio_pin, GPIO.LOW)
                    await asyncio.sleep(0.1)
                
                # Longer pause
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            GPIO.output(self.gpio_pin, GPIO.LOW)
    
    async def blink(self, count: int = 1, duration: float = 0.2):
        """
        Perform a specific number of blinks
        
        Args:
            count: Number of blinks
            duration: Duration of each blink (seconds)
        """
        if not self.running:
            return
        
        original_state = self.current_state
        
        try:
            for _ in range(count):
                GPIO.output(self.gpio_pin, GPIO.HIGH)
                await asyncio.sleep(duration)
                GPIO.output(self.gpio_pin, GPIO.LOW)
                await asyncio.sleep(duration)
        finally:
            # Restore original state
            self.set_state(original_state)
    
    def get_state(self) -> LEDState:
        """Get current LED state"""
        return self.current_state


# Test function
async def test_led_controller():
    """Test LED controller functionality"""
    logger.info("LED Controller Test Mode")
    
    controller = LEDController()
    await controller.start()
    
    states = [
        (LEDState.SCANNING, "Scanning mode", 3),
        (LEDState.PAIRED, "Paired mode", 3),
        (LEDState.CONNECTED, "Connected mode", 2),
        (LEDState.ERROR, "Error mode", 3),
    ]
    
    try:
        for state, description, duration in states:
            print(f"\nTesting: {description}")
            controller.set_state(state)
            await asyncio.sleep(duration)
        
        print("\nTesting blink function")
        controller.set_state(LEDState.ON)
        await controller.blink(count=5, duration=0.2)
        
        print("\nTest complete")
        
    finally:
        await controller.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(test_led_controller())
