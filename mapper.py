#!/usr/bin/env python3
"""
Button Mapping Module
Flexible button remapping system with multiple profiles
"""

import logging
from enum import Enum
from typing import Dict, Optional
from copy import deepcopy

logger = logging.getLogger(__name__)


class MappingProfile(Enum):
    """Predefined mapping profiles"""
    PASSTHROUGH = 'passthrough'
    DEFAULT = 'default'  # A<->B swap
    FIGHTING = 'fighting'  # Optimised for fighting games
    PLATFORMER = 'platformer'  # Optimised for platform games


class ButtonMapper:
    """Manages button input/output mapping"""
    
    # All valid button identifiers
    VALID_BUTTONS = {
        # Face buttons
        'a', 'b', 'x', 'y',
        # Shoulder buttons
        'l', 'r', 'zl', 'zr',
        # D-pad
        'up', 'down', 'left', 'right',
        # System buttons
        'plus', 'minus', 'home', 'capture',
        # Stick buttons
        'left_stick', 'right_stick'
    }
    
    # Predefined mapping profiles
    PROFILES = {
        MappingProfile.PASSTHROUGH: {
            # No remapping - direct passthrough
        },
        
        MappingProfile.DEFAULT: {
            # A <-> B swap (default for this project)
            'a': 'b',
            'b': 'a',
        },
        
        MappingProfile.FIGHTING: {
            # Optimised for fighting games
            'a': 'y',  # Light attack
            'b': 'b',  # Medium attack
            'x': 'a',  # Heavy attack
            'y': 'x',  # Special
            'zl': 'l',
            'zr': 'r',
        },
        
        MappingProfile.PLATFORMER: {
            # Optimised for platformers
            'a': 'b',  # Jump
            'b': 'y',  # Run
            'x': 'a',  # Action
            'y': 'x',  # Special
        }
    }
    
    def __init__(self, initial_profile: MappingProfile = MappingProfile.DEFAULT):
        """
        Initialize button mapper
        
        Args:
            initial_profile: Starting mapping profile
        """
        self.current_profile = initial_profile
        self.custom_mappings: Dict[str, str] = {}
        self.active_mappings: Dict[str, str] = {}
        
        self.set_profile(initial_profile)
        logger.info(f"ButtonMapper initialized with profile: {initial_profile.value}")
    
    def set_profile(self, profile: MappingProfile):
        """
        Load a predefined mapping profile
        
        Args:
            profile: MappingProfile to activate
        """
        self.current_profile = profile
        self.active_mappings = deepcopy(self.PROFILES[profile])
        
        # Apply any custom mappings on top
        self.active_mappings.update(self.custom_mappings)
        
        logger.info(f"Loaded profile: {profile.value} with {len(self.active_mappings)} mappings")
    
    def set_mapping(self, input_button: str, output_button: str):
        """
        Set a custom button mapping
        
        Args:
            input_button: Button being pressed
            output_button: Button to output
        """
        if input_button not in self.VALID_BUTTONS:
            logger.warning(f"Invalid input button: {input_button}")
            return
        
        if output_button not in self.VALID_BUTTONS:
            logger.warning(f"Invalid output button: {output_button}")
            return
        
        self.custom_mappings[input_button] = output_button
        self.active_mappings[input_button] = output_button
        
        logger.debug(f"Mapping set: {input_button} -> {output_button}")
    
    def remove_mapping(self, input_button: str):
        """
        Remove a custom mapping (revert to passthrough)
        
        Args:
            input_button: Button to remove mapping for
        """
        if input_button in self.custom_mappings:
            del self.custom_mappings[input_button]
        
        if input_button in self.active_mappings:
            del self.active_mappings[input_button]
        
        logger.debug(f"Mapping removed: {input_button}")
    
    def get_mapping(self, input_button: str) -> str:
        """
        Get the mapped output for an input button
        
        Args:
            input_button: Button being pressed
            
        Returns:
            Mapped output button (or input button if no mapping)
        """
        return self.active_mappings.get(input_button, input_button)
    
    def map_buttons(self, button_states: Dict[str, bool]) -> Dict[str, bool]:
        """
        Apply mapping to a full set of button states
        
        Args:
            button_states: Dictionary of button: pressed state
            
        Returns:
            Mapped button states
        """
        mapped_states = {}
        
        for input_btn, pressed in button_states.items():
            output_btn = self.get_mapping(input_btn)
            mapped_states[output_btn] = pressed
        
        return mapped_states
    
    def cycle_profile(self) -> MappingProfile:
        """
        Cycle to the next mapping profile
        
        Returns:
            The newly activated profile
        """
        profiles = list(MappingProfile)
        current_index = profiles.index(self.current_profile)
        next_index = (current_index + 1) % len(profiles)
        next_profile = profiles[next_index]
        
        self.set_profile(next_profile)
        logger.info(f"Cycled to profile: {next_profile.value}")
        
        return next_profile
    
    def get_current_profile(self) -> MappingProfile:
        """Get currently active profile"""
        return self.current_profile
    
    def get_all_mappings(self) -> Dict[str, str]:
        """Get all active mappings"""
        return self.active_mappings.copy()
    
    def clear_all_mappings(self):
        """Clear all custom mappings and revert to profile defaults"""
        self.custom_mappings.clear()
        self.set_profile(self.current_profile)
        logger.info("All custom mappings cleared")
    
    def export_config(self) -> Dict:
        """
        Export current configuration
        
        Returns:
            Dictionary with current profile and custom mappings
        """
        return {
            'profile': self.current_profile.value,
            'custom_mappings': self.custom_mappings.copy(),
            'active_mappings': self.active_mappings.copy()
        }
    
    def import_config(self, config: Dict):
        """
        Import configuration
        
        Args:
            config: Configuration dictionary from export_config()
        """
        try:
            profile_name = config.get('profile', 'default')
            profile = MappingProfile(profile_name)
            
            self.set_profile(profile)
            
            if 'custom_mappings' in config:
                for input_btn, output_btn in config['custom_mappings'].items():
                    self.set_mapping(input_btn, output_btn)
            
            logger.info(f"Configuration imported: {profile_name}")
            
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")


# Test function
def test_mapper():
    """Test button mapper functionality"""
    logger.info("=== Button Mapper Test ===\n")
    
    mapper = ButtonMapper()
    
    # Test default profile (A<->B)
    print("Test 1: Default profile (A<->B)")
    print(f"  A maps to: {mapper.get_mapping('a')}")
    print(f"  B maps to: {mapper.get_mapping('b')}")
    print(f"  X maps to: {mapper.get_mapping('x')}")
    
    # Test full button state mapping
    print("\nTest 2: Full button state mapping")
    input_states = {'a': True, 'b': False, 'x': True, 'y': False}
    output_states = mapper.map_buttons(input_states)
    print(f"  Input:  {input_states}")
    print(f"  Output: {output_states}")
    
    # Test custom mapping
    print("\nTest 3: Custom mapping")
    mapper.set_mapping('x', 'y')
    print(f"  X now maps to: {mapper.get_mapping('x')}")
    
    # Test profile cycling
    print("\nTest 4: Profile cycling")
    for i in range(5):
        next_profile = mapper.cycle_profile()
        print(f"  Cycle {i+1}: {next_profile.value}")
    
    # Test passthrough
    print("\nTest 5: Passthrough mode")
    mapper.set_profile(MappingProfile.PASSTHROUGH)
    print(f"  A maps to: {mapper.get_mapping('a')}")
    print(f"  B maps to: {mapper.get_mapping('b')}")
    
    # Test config export/import
    print("\nTest 6: Config export/import")
    mapper.set_profile(MappingProfile.DEFAULT)
    config = mapper.export_config()
    print(f"  Exported config: {config}")
    
    mapper.set_profile(MappingProfile.PASSTHROUGH)
    print(f"  Changed to passthrough")
    
    mapper.import_config(config)
    print(f"  Imported config, now: {mapper.get_current_profile().value}")
    
    print("\n=== Tests Complete ===")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_mapper()
