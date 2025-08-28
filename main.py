from joycontrol.controller import JoyConController


jc_left = JoyConController('jc_left')
jc_right = JoyConController('jc_right')
jc_extra = JoyConController('jc_extra')


while True:
   
    jc_left.update_inputs(jc_left.get_raw_buttons())
    jc_right.update_inputs(jc_right.get_raw_buttons())
    jc_extra.update_inputs(jc_extra.get_raw_buttons())
