def apply_mapping_multi(raw_button_state, controller_name):
    mapping = {
        "jc_left": {"A": "X"},      # Beispiel: linker JoyCon -> A wird X
        "jc_right": {"B": "Y"},     # rechter JoyCon -> B wird Y
        "jc_extra": {"L": "R"},     # dritter JoyCon -> L wird R
    }

    mapped_state = raw_button_state.copy()

    if controller_name in mapping:
        for src, dst in mapping[controller_name].items():
            if raw_button_state.get(src, False):
                mapped_state[dst] = True
                mapped_state[src] = False

    return mapped_state
