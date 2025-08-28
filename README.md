# JamCon
A project for experimenting with a BLE proxy device for Joy-Cons.
It allows mapping and remapping of Joy-Con inputs using joycontrol
 by mart1nro.
This is just for fun and educational purposes.

This Repo is work in progress. 

# Tools and dependencies
For listening to BLE PAckages, emulating and mapping Joy-Con Inputs, we will use joycontrol (https://github.com/mart1nro/joycontrol) - written by mart1nro. Beside joycontrol i used 
python3-pip, python3-dbus, libhidapi-hidraw0, bluetooth, bluez, bluez-tools  and screen

# Step 1:
install all requirements with 
```bash
git clone https://github.com/mart1nro/joycontrol.git
cd joycontrol
pip3 install -r requirements.txt
sudo python3 setup.py install
```
make shure to run as root.

# Step 2:
open the joycontroll folder with
```bash
cd /joycontrol
```
then edit controller.py with
```bash
sudo nano controller.py
```
There is a function in the file that records the raw buttons from the Joy-Con – often 
```python
update_inputs()

set_button_state()
```
 or similar.
Then you have to paste in this mapping logic on the lower- or upper end of the file: 
```python
# ----------------------------
# Mapping for 3 Joy-Cons
# ----------------------------
def apply_mapping_multi(button_state, controller_name):
    """
    button_state: dict mit allen Buttons, z.B. {'A': True, 'B': False, ...}
    controller_name: 'jc_left', 'jc_right', 'jc_extra'
    """

    mapped_state = button_state.copy()

    # --- left (jc_left) ---
    if controller_name == 'jc_left':
        # sample: A -> X, B -> Y
        if mapped_state.get('A', False):
            mapped_state['X'] = True
            mapped_state['A'] = False
        if mapped_state.get('B', False):
            mapped_state['Y'] = True
            mapped_state['B'] = False

    # --- right (jc_right) ---
    elif controller_name == 'jc_right':
        # sample: A -> B, X -> Y
        if mapped_state.get('A', False):
            mapped_state['B'] = True
            mapped_state['A'] = False
        if mapped_state.get('X', False):
            mapped_state['Y'] = True
            mapped_state['X'] = False

    # --- extra right (jc_extra) ---
    elif controller_name == 'jc_extra':
        # sample: invert all buttons
        for btn in mapped_state.keys():
            mapped_state[btn] = not mapped_state[btn]

    return mapped_state
```
(This sample is for 3 Controllers, one left and two right.
You can edit this by deleting or pasting this Block in the function)
```python
#this Block maps A to B and X to Y
 # --- left/right (left/right) ---
    elif controller_name == 'jc_right': #for left write 'jc_left'
        # sample: A -> B, X -> Y        #extra mapping
        if mapped_state.get('A', False):
            mapped_state['B'] = True
            mapped_state['A'] = False
        if mapped_state.get('X', False):
            mapped_state['Y'] = True
            mapped_state['X'] = False

#or

 # --- extra left/right (jc_extra) ---
    elif controller_name == 'jc_extra':
        # sample: invert all buttons
        for btn in mapped_state.keys():
            mapped_state[btn] = not mapped_state[btn]
```
IMPORTANT: if you extend the script for more or less controllers, you also have to change that in mapper.py

When you have done that, you have to edit the class update_inputs() (or similar) like that: 
```python
def update_inputs(self, raw_button_state):
    mapped_state = apply_mapping_multi(raw_button_state, self.controller_name)
    self.send_report(mapped_state)
```
IMPORTANT:
apply_mapping_multi has to be definied in another file (mapper.py),
you have to import it:
```python
from mapper import apply_mapping_multi
```
To do that, you have to create two files, main.py and mapper.py in /joycontrol:
```python
#main.py
from joycontrol.controller import JoyConController

# Controller-Instanzen erzeugen
jc_left = JoyConController('jc_left')
jc_right = JoyConController('jc_right')
jc_extra = JoyConController('jc_extra')

# Hauptschleife (Joycontrol intern kümmert sich um BLE & Switch)
while True:
    # Hier werden normalerweise interne Updates gemacht
    jc_left.update_inputs(jc_left.get_raw_buttons())
    jc_right.update_inputs(jc_right.get_raw_buttons())
    jc_extra.update_inputs(jc_extra.get_raw_buttons())
```

```python
#mapper.py
def apply_mapping_multi(raw_button_state, controller_name):
    mapping = {
        "jc_left": {"A": "X"},      # Beispiel: linker JoyCon -> A wird X
        "jc_right": {"B": "Y"},     # rechter JoyCon -> B wird Y
        "jc_extra": {"L": "R"},     # dritter JoyCon -> L wird R
    }

    mapped_state = raw_button_state.copy()

    # Nur wenn für diesen Controller eine Regel existiert
    if controller_name in mapping:
        for src, dst in mapping[controller_name].items():
            if raw_button_state.get(src, False):
                mapped_state[dst] = True
                mapped_state[src] = False

    return mapped_state

```
# Step 3: 
for starting type 
```bash
sudo python3 main.py
```
# Legal disclaimer
This software is provided for educational and research purposes only.
It does not interact with real Nintendo hardware and should not be used to circumvent, emulate, or interfere with official Nintendo products.
The author(s) assume no liability for misuse of this project.







 



 
