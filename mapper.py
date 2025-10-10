#!/usr/bin/env python3
"""
Button Mapper für JamCon
Ermöglicht das Remapping von Joy-Con Buttons
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class ButtonMapper:
    """Verwaltet Button-Mappings für einen Controller"""
    
    # Vordefinierte Mapping-Profile
    MAPPING_PROFILES = {
        'jc_left': {
            # Beispiel: A -> X, B -> Y
            'a': 'x',
            'b': 'y',
        },
        'jc_right': {
            # Beispiel: A -> B, X -> Y
            'a': 'b',
            'x': 'y',
        },
        'jc_extra': {
            # Beispiel: L <-> R tauschen
            'l': 'r',
            'r': 'l',
        },
        'default': {
            # Kein Mapping (Passthrough)
        }
    }
    
    def __init__(self, controller_name: str):
        """
        Args:
            controller_name: Name des Controllers für Mapping-Lookup
        """
        self.controller_name = controller_name
        self.mapping = self.MAPPING_PROFILES.get(
            controller_name, 
            self.MAPPING_PROFILES['default']
        ).copy()
        
        logger.info(f'ButtonMapper initialized for {controller_name} with {len(self.mapping)} mappings')
        
    def apply_mapping(self, raw_state: Dict[str, bool]) -> Dict[str, bool]:
        """
        Wendet das Button-Mapping auf den Raw-State an
        
        Args:
            raw_state: Dictionary mit Button-Namen und deren Status (True/False)
            
        Returns:
            Dictionary mit gemappten Buttons
        """
        mapped_state = {}
        
        # Alle Buttons durchgehen
        for button_name, is_pressed in raw_state.items():
            # Prüfen ob Mapping existiert
            if button_name in self.mapping:
                target_button = self.mapping[button_name]
                mapped_state[target_button] = is_pressed
                # Original-Button auf False setzen
                mapped_state[button_name] = False
            else:
                # Kein Mapping -> Button durchreichen
                mapped_state[button_name] = is_pressed
                
        return mapped_state
        
    def set_mapping(self, source_button: str, target_button: str):
        """
        Setzt ein individuelles Mapping
        
        Args:
            source_button: Original-Button (z.B. 'a')
            target_button: Ziel-Button (z.B. 'x')
        """
        self.mapping[source_button.lower()] = target_button.lower()
        logger.info(f'{self.controller_name}: Mapped {source_button} -> {target_button}')
        
    def remove_mapping(self, source_button: str):
        """Entfernt ein Mapping"""
        if source_button.lower() in self.mapping:
            del self.mapping[source_button.lower()]
            logger.info(f'{self.controller_name}: Removed mapping for {source_button}')
            
    def clear_mappings(self):
        """Entfernt alle Mappings"""
        self.mapping.clear()
        logger.info(f'{self.controller_name}: All mappings cleared')
        
    def load_profile(self, profile_name: str):
        """Lädt ein vordefiniertes Mapping-Profil"""
        if profile_name in self.MAPPING_PROFILES:
            self.mapping = self.MAPPING_PROFILES[profile_name].copy()
            logger.info(f'{self.controller_name}: Loaded profile "{profile_name}"')
        else:
            logger.warning(f'{self.controller_name}: Profile "{profile_name}" not found')
            
    def get_current_mappings(self) -> Dict[str, str]:
        """Gibt die aktuellen Mappings zurück"""
        return self.mapping.copy()


# Beispiel für Custom Mapping-Funktionen
class AdvancedButtonMapper(ButtonMapper):
    """Erweiterte Mapping-Funktionen"""
    
    def __init__(self, controller_name: str):
        super().__init__(controller_name)
        self.inverted_buttons = set()
        self.combo_mappings = {}  # {('a', 'b'): 'x'} -> A+B gleichzeitig = X
        
    def set_inverted(self, button_name: str, inverted: bool = True):
        """
        Invertiert einen Button (gedrückt -> nicht gedrückt)
        
        Args:
            button_name: Button-Name
            inverted: True = invertieren, False = normal
        """
        button = button_name.lower()
        if inverted:
            self.inverted_buttons.add(button)
        else:
            self.inverted_buttons.discard(button)
            
    def add_combo_mapping(self, buttons: tuple, target_button: str):
        """
        Mappt eine Button-Kombination auf einen einzelnen Button
        
        Args:
            buttons: Tuple von Button-Namen (z.B. ('a', 'b'))
            target_button: Ziel-Button
        """
        key = tuple(sorted([b.lower() for b in buttons]))
        self.combo_mappings[key] = target_button.lower()
        logger.info(f'{self.controller_name}: Combo {"+".join(key)} -> {target_button}')
        
    def apply_mapping(self, raw_state: Dict[str, bool]) -> Dict[str, bool]:
        """Erweiterte Mapping-Logik mit Inversionen und Combos"""
        # Basis-Mapping anwenden
        mapped_state = super().apply_mapping(raw_state)
        
        # Invertierte Buttons
        for button in self.inverted_buttons:
            if button in mapped_state:
                mapped_state[button] = not mapped_state[button]
                
        # Combo-Mappings prüfen
        for combo_buttons, target in self.combo_mappings.items():
            # Prüfen ob alle Buttons der Combo gedrückt sind
            if all(raw_state.get(btn, False) for btn in combo_buttons):
                # Combo aktivieren
                mapped_state[target] = True
                # Original-Buttons deaktivieren
                for btn in combo_buttons:
                    mapped_state[btn] = False
                    
        return mapped_state
