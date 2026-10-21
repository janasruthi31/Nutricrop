import re

def is_plausible(num_str, key):
    try:
        v = float(num_str)
        if key == "ph":
            return 3.0 <= v <= 11.0
        if key == "ec":
            return 0.0 <= v <= 20.0
        if key == "organic_carbon":
            return 0.0 <= v <= 5.0
        return True
    except Exception:
        return False

print('2027 for pH plausible?', is_plausible('2027', 'ph'))
print('7.75 for pH plausible?', is_plausible('7.75', 'ph'))
