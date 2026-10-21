import re

def parse_val(text):
    tokens = text.split()
    for ti, tk in enumerate(tokens):
        clean_tk = re.sub(r'^[^\d]+|[^\d.,]+$', '', tk)
        if not clean_tk:
            continue
        if re.match(r'^\d+[.,]\d+$', clean_tk):
            return clean_tk.replace(',', '.')
        if re.match(r'^\d+$', clean_tk) and ti + 1 < len(tokens):
            next_tk = re.sub(r'^[^\d]+|[^\d.,]+$', '', tokens[ti+1])
            if re.match(r'^\d{2}$', next_tk):
                return f'{clean_tk}.{next_tk}'
        if re.match(r'^\d+$', clean_tk):
            if len(clean_tk) == 3 and clean_tk[0] in '456789':
                return f'{clean_tk[0]}.{clean_tk[1:]}'
            return clean_tk
    return None

lines = [
    'Plat Address mpsstay (N) 163 00 toomlsggy (P) 13 75 embue eggs (K) 238 00',
    'mle 2027 (pH) 775 (EC) 0 22d5ym BB (0c)osewx',
    'Shp (S) 12.50 ppm Sssprat (Zn) 1.56 Gump (B) 0.50 ppm',
    'BMeoby (Fe) 447 ppm tommuaefa (Mn) 1.71 gemdgd (Cu) 6 85 ppm'
]

symbols = [
    ('nitrogen', r'\(\s*N\s*\)'),
    ('phosphorus', r'\(\s*P\s*\)'),
    ('potassium', r'\(\s*K\s*\)'),
    ('ph', r'\(\s*pH\s*[\)}]?'),
    ('ec', r'\(\s*EC\s*[\)}]?'),
    ('organic_carbon', r'\(\s*[0O]c\s*[\)}]?'),
    ('sulphur', r'\(\s*S\s*\)'),
    ('zinc', r'\(\s*Zn\s*\)'),
    ('boron', r'\(\s*B\s*\)'),
    ('iron', r'\(\s*Fe\s*\)'),
    ('manganese', r'\(\s*Mn\s*\)'),
    ('copper', r'\(\s*Cu\s*\)')
]

for l in lines:
    matches = []
    for k, pat in symbols:
        m = re.search(pat, l, re.I)
        if m:
            matches.append((m.start(), m.end(), k))
    matches.sort()
    for idx, (st, en, key) in enumerate(matches):
        next_st = matches[idx+1][0] if idx+1 < len(matches) else len(l)
        chunk = l[en:next_st]
        val = parse_val(chunk)
        print(f'{key}: {val} (from {chunk.strip()})')
