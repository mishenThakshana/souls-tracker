# Build a name -> positions index from elden-ring-compass generated data.
import json, re, sys, os, collections
G = sys.argv[1]; OUT = sys.argv[2]

def arr(f):
    s = open(os.path.join(G, f)).read()
    if 'JSON.parse(' in s:
        q = s[s.index('JSON.parse(')+11:]
        q = q[:q.rindex(')')]
        return json.loads(json.loads(q))
    i = s.index('= [') + 3
    dec = json.JSONDecoder(); out = []
    while True:
        while s[i] in ' \n\r\t,': i += 1
        if s[i] == ']': return out
        o, i = dec.raw_decode(s, i); out.append(o)

conv = collections.defaultdict(list)
for c in arr('world-map-legacy-conv.ts'): conv[c['srcMapId']].append(c)
OX, OY = -7168, 16640
def project(mapId, x, z):
    m = re.match(r'^m(60|61)_(\d+)_(\d+)_\d(\d)$', mapId)
    if m:
        tier = int(m.group(4))
        if tier > 2: return None
        size = 256 * 2**tier
        wx = int(m.group(2))*size + size/2 + x
        wz = int(m.group(3))*size + size/2 + z
        return ('M00' if m.group(1) == '60' else 'M10', wx+OX, OY-wz)
    m = re.match(r'^(m\d\d_\d\d_\d\d)_', mapId)
    if not m or m.group(1) not in conv: return None
    best = min(conv[m.group(1)], key=lambda p: (x-p['srcX'])**2 + (z-p['srcZ'])**2)
    return (best['master'], x+best['addX']+OX, OY-(z+best['addZ']))

idx = []  # (name, kind, master, px, py, extra)
def add(name, kind, mapId, x, z, extra=''):
    if not name or 'dummy' in name.lower() or name.startswith('[ERROR'): return
    p = project(mapId, x, z)
    if p and p[0] in ('M00','M01','M10','M11'):
        idx.append(dict(name=name, kind=kind, master=p[0], px=round(p[1],1), py=round(p[2],1), map=mapId, extra=extra))

markers = []
for line in open(os.path.join(G,'markers.ts')):
    line = line.strip().rstrip(',')
    if line.startswith('{"mapId"'): markers.append(json.loads(line))
byEnt = {}
for mk in markers:
    byEnt.setdefault(mk['entityId'], mk)
    if mk['category'] == 'npc' and mk['displayName']:
        add(mk['displayName'], 'npc', mk['mapId'], mk['x'], mk['z'])
regions = {r['name']: r['area'] for r in arr('regions.ts')}
for g in arr('graces.ts'):
    mk = byEnt.get(g['bonfireEntityId'])
    if mk: add(g['name'], 'grace', mk['mapId'], mk['x'], mk['z'], g['region'] or '')
for b in arr('bosses.ts'):
    add(b['name'], 'boss', b['mapId'], b['x'], b['z'])

names = {}
for f, t in [('weapons.ts','weapon'),('goods.ts','goods'),('armor.ts','armor'),('talismans.ts','talisman'),('spells.ts','goods'),('spirit-ashes.ts','goods'),('ashes-of-war.ts','gem')]:
    for it in arr(f):
        names.setdefault((t, it['id']), it['name'])
for p in arr('placements.ts'):
    t = p['itemType']; iid = p['itemId']
    n = names.get((t, iid))
    if n is None and t == 'weapon':
        n = names.get(('weapon', iid - iid % 100))  # infused/upgraded variants
    if n is None and t == 'armor':
        n = names.get(('armor', iid))
    if n is None:
        n = names.get(('gem', iid))
    add(n, 'armor' if t == 'armor' else 'item', p['mapId'], p['x'], p['z'], p['source'])

# dedupe near-identical points per name
seen = collections.defaultdict(list); out = []
for e in idx:
    k = (e['name'], e['kind'], e['master'])
    if any((e['px']-a)**2+(e['py']-b)**2 < 40**2 for a,b in seen[k]): continue
    seen[k].append((e['px'],e['py'])); out.append(e)
json.dump(out, open(OUT,'w'))
print(len(out), collections.Counter(e['kind'] for e in out), collections.Counter(e['master'] for e in out))
