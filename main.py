#!/usr/bin/env python3
"""
JamCon - Joy-Con BLE Proxy with Button Mapping
Main entry point for the application
"""
import asyncio
import logging
from joycontrol import logging_default as log
from joycontrol.controller import Controller
from joycontrol.protocol import controller_protocol_factory
from joycontrol.server import create_hid_server
from mapper import ButtonMapper

# Logging Setup
logger = logging.getLogger(__name__)

class JamConController:
    """Wrapper für einen Joy-Con mit Button-Mapping"""
    
    def __init__(self, controller_name, controller_type='PRO_CONTROLLER'):
        """
        Args:
            controller_name: Eindeutiger Name ('jc_left', 'jc_right', etc.)
            controller_type: Joy-Con Typ ('JOYCON_L', 'JOYCON_R', 'PRO_CONTROLLER')
        """
        self.controller_name = controller_name
        self.controller_type = controller_type
        self.mapper = ButtonMapper(controller_name)
        self.protocol = None
        self.transport = None
        
    async def start(self, reconnect_bt_addr=None):
        """Startet den Controller und verbindet mit der Switch"""
        logger.info(f'Starting {self.controller_name} ({self.controller_type})...')
        
        # Factory für den Controller erstellen
        factory = controller_protocol_factory(Controller.from_arg(self.controller_type))
        
        # HID Server erstellen und auf Verbindung warten
        transport, protocol = await create_hid_server(
            factory,
            reconnect_bt_addr=reconnect_bt_addr
        )
        
        self.transport = transport
        self.protocol = protocol
        
        # Warte auf vollständige Verbindung
        await protocol.connection.sig_ensure_paired_and_received_imu_calibration.wait()
        logger.info(f'{self.controller_name} connected!')
        
        return protocol
        
    async def run_input_loop(self):
        """Hauptloop für Input-Verarbeitung mit Mapping"""
        if not self.protocol:
            raise RuntimeError(f'{self.controller_name}: Not connected!')
            
        button_state = self.protocol.get_button_state()
        
        logger.info(f'{self.controller_name}: Starting input loop...')
        
        try:
            while True:
                await asyncio.sleep(0.05)  # 50ms Update-Rate
                
                # Original Button-State auslesen
                raw_state = self._get_current_button_state(button_state)
                
                # Mapping anwenden
                mapped_state = self.mapper.apply_mapping(raw_state)
                
                # Gemappte Buttons setzen
                self._apply_button_state(button_state, mapped_state)
                
        except KeyboardInterrupt:
            logger.info(f'{self.controller_name}: Stopped by user')
        except Exception as e:
            logger.error(f'{self.controller_name}: Error in input loop: {e}')
            
    def _get_current_button_state(self, button_state):
        """Liest den aktuellen Button-State aus"""
        # Extrahiere alle relevanten Buttons
        return {
            'a': button_state.get_button('a'),
            'b': button_state.get_button('b'),
            'x': button_state.get_button('x'),
            'y': button_state.get_button('y'),
            'l': button_state.get_button('l'),
            'r': button_state.get_button('r'),
            'zl': button_state.get_button('zl'),
            'zr': button_state.get_button('zr'),
            'plus': button_state.get_button('plus'),
            'minus': button_state.get_button('minus'),
            'home': button_state.get_button('home'),
            'capture': button_state.get_button('capture'),
            'down': button_state.get_button('down'),
            'up': button_state.get_button('up'),
            'right': button_state.get_button('right'),
            'left': button_state.get_button('left'),
        }
        
    def _apply_button_state(self, button_state, mapped_state):
        """Wendet den gemappten Button-State an"""
        for button_name, pressed in mapped_state.items():
            if pressed:
                button_state.set_button(button_name)
            else:
                button_state.release_button(button_name)


async def main():
    """Hauptfunktion"""
    # Beispiel: Einen Pro Controller starten
    controller = JamConController('jc_main', 'PRO_CONTROLLER')
    
    try:
        # Controller verbinden
        await controller.start()
        
        # Input Loop starten
        await controller.run_input_loop()
        
    except KeyboardInterrupt:
        logger.info('Shutting down...')
    except Exception as e:
        logger.error(f'Error: {e}')
        raise
    finally:
        if controller.transport:
            controller.transport.close()


if __name__ == '__main__':
    # Logging einrichten
    log.configure()
    
    # Hauptprogramm starten
    asyncio.run(main())
