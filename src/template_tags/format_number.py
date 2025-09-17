import re

def format_number(value):
    if isinstance(value, str):
        mod_value = value.replace(" ", "")
        if mod_value.isdigit():
            print(mod_value, 'modvalue')
            mod_value = re.sub(r'(\d)(?=(\d{3})+(?!\d))', r'\1 ', mod_value)
            print(mod_value, 'modvalueee')
            return mod_value
    return value