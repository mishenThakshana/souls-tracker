# Convert the matched checklist into the compact JSON the Android app reads from assets.
import json, sys
src, dst = sys.argv[1], sys.argv[2]
d = json.load(open(src))
titles = {'base': 'Base Game', 'dlc': 'Shadow of the Erdtree'}
sheets = []
for key in ('base', 'dlc'):
    entries = []
    number = 0  # displayed step number counts tasks only; section headers are not steps
    for e in d[key]:
        if not e['section']: number += 1
        p = e['pin'] or {}
        entry = {
            'id': f"{key}-{e['step']}", 'step': 0 if e['section'] else number, 'item': e['item'], 'category': e['category'],
            'location': e['location'], 'notes': e['notes'], 'section': e['section'], 'ng': e['ng'],
            'map': p.get('master'), 'x': round(p['px']) if p else 0, 'y': round(p['py']) if p else 0,
            'precise': bool(p.get('precise')),
        }
        # Fields left out fall back to the defaults in Models.kt.
        entries.append({k: v for k, v in entry.items() if v not in ('', False, None, 0) or k in ('id', 'item')})
    sheets.append({'id': key, 'title': titles[key], 'entries': entries})
json.dump({'game': 'eldenring', 'title': 'Elden Ring', 'tips': d.get('tips', []), 'sheets': sheets},
          open(dst, 'w'), ensure_ascii=False, separators=(',', ':'))
