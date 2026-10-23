import json, re, sys, collections, math
raw = json.load(open(sys.argv[1])); idx = json.load(open(sys.argv[2])); OUT = sys.argv[3]

def norm(s):
    s = (s or '').lower().replace('’',"'").replace('&', 'and')
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r"[^a-z0-9' ]+", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

by = collections.defaultdict(list)
for e in idx: by[norm(e['name'])].append(e)
# armor pieces grouped by set prefix
ARMOR_SUFFIX = r' (helm|hood|mask|crown|hat|headband|helmet|armor|robe|gauntlets|gloves|bracers|greaves|trousers|boots|leggings|manchettes|cuirass|garb|vest|attire|cloak|coat|surcoat|chest armor|gown|dress|shirt|cuffs|sleeves|skirt|loincloth|wrap|tights|shoes)( altered)?$'
sets = collections.defaultdict(list)
for e in idx:
    if e['kind'] == 'armor':
        m = re.sub(ARMOR_SUFFIX, '', norm(e['name']))
        if m != norm(e['name']): sets[m].append(e)

# location anchors: graces by name, grace region centroids
anchor = {}
reg = collections.defaultdict(list)
for e in idx:
    if e['kind'] == 'grace':
        anchor.setdefault(norm(e['name']), e)
        if e['extra']: reg[norm(e['extra'])].append(e)
for r, es in reg.items():
    if r not in anchor:
        m = collections.Counter(x['master'] for x in es).most_common(1)[0][0]
        es = [x for x in es if x['master'] == m]
        cx = sum(x['px'] for x in es)/len(es); cy = sum(x['py'] for x in es)/len(es)
        rad = max(math.hypot(x['px']-cx, x['py']-cy) for x in es)
        anchor[r] = dict(master=m, px=cx, py=cy, name=r, radius=rad)
ALIAS = {'west limgrave':'limgrave','east limgrave':'limgrave','western liurnia':'liurnia of the lakes','east liurnia':'liurnia of the lakes',
 'northern liurnia':'liurnia of the lakes','west liurnia':'liurnia of the lakes','altus plateau':'altus plateau','altus leyndell':'leyndell royal capital',
 'leyndell':'leyndell royal capital','raya lucaria':'raya lucaria academy','castle redmane':'redmane castle','shaded castle':'the shaded castle',
 'farum azula':'crumbling farum azula','nokron city':'nokron eternal city','ruin strewn precipe':'ruin strewn precipice','stranded graveyward':'stranded graveyard',
 'chuch of elleh':'church of elleh','roundtable':'roundtable hold','dragonbarrow':"greyoll's dragonbarrow",'mountaintops of giants':'mountaintops of the giants',
 'gravesite plain':'gravesite plain','rauh base':'rauh base','hinterlands':'hinterland','caelid':'caelid','three sisters':'three sisters',
 'deeproot depths':'deeproot depths','subterranean shunning grounds':'subterranean shunning grounds','lands between':None,'elden ring':None,'all':None,'npc':None,'cleanup':None,'event':None}
# Map landmarks that are not graces, anchored to their nearest graces (per the Fextralife wiki pages).
LANDMARKS = {
    'fort laiedd': ['Seethewater Terminus'], 'three sisters': ["Ranni's Rise"],
    'dragon burnt ruins': ['Agheel Lake North', 'Agheel Lake South'], 'witchbane ruins': ['Fourth Church of Marika'],
    'shaded castle': ['Shaded Castle Ramparts'], 'the shaded castle': ['Shaded Castle Ramparts'],
    'ordina lithurgical town': ['Ordina, Liturgical Town'],
    'western nameless mausoleum': ['Scorched Ruins'], 'eastern nameless mausoleum': ["Recluses' River Downstream"],
    'northern nameless mausoleum': ['Temple Town Ruins'], 'church of consolation': ['Gravesite Plain'],
    'prospect town': ['Cliffroad Terminus'], 'ruins of unte': ['Castle Watering Hole'],
    'abandoned ailing village': ['Greatbridge, North'],
}
for loc, graces in LANDMARKS.items():
    gs = [by[norm(g)][0] for g in graces if norm(g) in by]
    missing = [g for g in graces if norm(g) not in by]
    if missing: print('landmark grace not found:', missing)
    if gs:
        anchor[loc] = dict(master=gs[0]['master'], px=sum(g['px'] for g in gs)/len(gs), py=sum(g['py'] for g in gs)/len(gs), name=loc, radius=300)

def loc_anchor(loc):
    n = norm(loc)
    if n in LANDMARKS: return anchor.get(n)
    n = ALIAS.get(n, n) if n in ALIAS else n
    if n is None: return None
    if n in anchor: return anchor[n]
    for k, v in anchor.items():
        if n and (k.startswith(n) or n.startswith(k)) and len(k) > 4: return v
    for k, v in anchor.items():
        if n and n in k: return v
    return None

STRIP = [r'^ash of war ', r'^map ', r'^spirit ash(es)? ', r'^boss ', r'^npc ', r'^(the )?']
def candidates(item, cat):
    n = norm(item); c = (cat or '').lower()
    keys = [n, re.sub(r'^map ', '', n), 'ash of war ' + n, re.sub(r'^ash of war ', '', n)]
    if c.startswith('map'): keys.insert(0, 'map ' + re.sub(r'^map ', '', n))
    if c.startswith('spirit'): keys += [n + ' ashes', n + ' ash', re.sub(r' ashes?$', '', n)]
    if c.startswith('sog') or c.startswith('checkpoint'): keys = [n]
    if c.startswith('armor') or n.endswith(' set'):
        s = re.sub(r' (set|armor)( partial)?$', '', n)
        if s in sets: return sets[s], 'exact'
        es = [e for e in idx if e['kind'] == 'armor' and norm(e['name']).startswith(s + ' ')]
        if es and len(s) > 2: return es, 'exact'
    for k in keys:
        if k in by:
            es = by[k]
            if c.startswith('sog') or c.startswith('checkpoint'): es = [e for e in es if e['kind'] == 'grace'] or es
            elif c in ('boss',): es = [e for e in es if e['kind'] == 'boss'] or es
            elif c in ('npc',): es = [e for e in es if e['kind'] == 'npc'] or es
            return es, 'exact'
    # NPC/boss names like "Patches" vs "Patches the Untethered" / "Margit, the Fell Omen"
    if c in ('npc', 'boss', 'invader', 'enemy', 'summon'):
        kinds = {'npc':('npc',), 'boss':('boss',)}.get(c, ('npc','boss'))
        head = n.split(' ')[0]
        es = [e for e in idx if e['kind'] in kinds and (norm(e['name']).startswith(n) or (len(n) > 4 and n in norm(e['name'])))]
        if es: return es, 'exact'
    if c.startswith('sog') or c.startswith('checkpoint'):
        es = [e for e in idx if e['kind'] == 'grace' and len(n) > 5 and norm(e['name']).startswith(n)]
        if es: return es, 'exact'
    # typo tolerance ("Whestone Knife", "Cemetary Shade", "Renalla")
    import difflib
    pool = ALLNAMES if not (c.startswith('sog') or c.startswith('checkpoint')) else GRACENAMES
    hit = difflib.get_close_matches(n, pool, n=1, cutoff=0.93)
    if hit and len(n) > 5 and re.findall(r'\d+', hit[0]) == re.findall(r'\d+', n): return by[hit[0]], 'fuzzy'
    return [], None
ALLNAMES = list(by)
GRACENAMES = [k for k, v in by.items() if any(e['kind'] == 'grace' for e in v)]

def d2(a, b):
    if a is None or b is None or a['master'] != b['master']: return 1e12
    return (a['px']-b['px'])**2 + (a['py']-b['py'])**2

LEARNED = {}  # location -> median of exact pins sharing that Location column

def loc_anchor(loc, _base=loc_anchor):
    return LEARNED.get(norm(loc)) or _base(loc)

def run():
    result = {}; stats = collections.Counter()
    for sheet, rows in raw.items():
        if sheet.endswith(' tips'): continue
        dlc = sheet != 'Base Game'
        prev = None; out = []
        for r in rows:
            item = str(r['item'] or '').strip(); loc = str(r['loc'] or '').strip()
            es, how = candidates(item, r['cat'])
            la = loc_anchor(loc)
            realm = (la['master'] in ('M10','M11')) if la else dlc
            es = [e for e in es if (e['master'] in ('M10','M11')) == realm]
            pin = None
            if es:
                best = min(es, key=lambda e: (d2(e, la) if la else 0) + 0.5*d2(e, prev))
                # a match far outside the stated location is usually a different instance (merchant, reward, NPC move)
                if not (la and best['master'][:2] == la['master'][:2] and d2(best, la) > (la.get('radius', 300) + 900)**2):
                    pin = dict(master=best['master'], px=best['px'], py=best['py'], precise=True, src=best['name'])
            if pin is None and la:
                pin = dict(master=la['master'], px=la['px'], py=la['py'], precise=False, src='location: '+la['name'])
            stats[(sheet, 'precise' if pin and pin['precise'] else ('approx' if pin else 'none'))] += 1
            out.append(dict(step=len(out)+1, item=item, category=(r['cat'] or '').strip(), location=loc,
                            notes=str(r['notes'] or '').strip(), section=bool(r.get('header')), ng=bool(r.get('ng')), pin=pin))
            if pin and pin['precise']: prev = dict(master=pin['master'], px=pin['px'], py=pin['py'])
        result['dlc' if dlc else 'base'] = out
    return result, stats

def learn(result):
    groups = collections.defaultdict(list)
    for rows in result.values():
        for e in rows:
            if e['pin'] and e['pin']['precise'] and e['location']:
                groups[norm(e['location'])].append(e['pin'])
    for loc, pins in groups.items():
        if len(pins) < 3 or (loc in ALIAS and ALIAS[loc] is None): continue
        m = collections.Counter(p['master'] for p in pins).most_common(1)[0][0]
        pins = [p for p in pins if p['master'] == m]
        xs = sorted(p['px'] for p in pins); ys = sorted(p['py'] for p in pins)
        cx, cy = xs[len(xs)//2], ys[len(ys)//2]
        ds = sorted(math.hypot(p['px']-cx, p['py']-cy) for p in pins)
        LEARNED[loc] = dict(master=m, px=cx, py=cy, name=loc, radius=max(250, ds[int(len(ds)*0.8)]))

result, stats = run()
learn(result)
result, stats = run()
result['tips'] = raw.get('Base Game tips', [])
json.dump(result, open(OUT, 'w'), indent=0)
print(stats)
for sheet in ('base','dlc'):
    miss = collections.Counter(e['category'] for e in result[sheet] if not (e['pin'] and e['pin']['precise']))
    print(sheet, 'unmatched by cat', miss.most_common(30))
if len(sys.argv) > 4:
    out = []
    for sheet in ('base','dlc'):
        for e in result[sheet]:
            p = e['pin']; la = loc_anchor(e['location'])
            if p and p['precise'] and la:
                d = math.sqrt(d2(p, la)) if p['master'] == la['master'] else -1
                out.append((d, sheet, e['step'], e['item'], e['location'], p['src'], p['master'], la['master'], la['name']))
    out.sort(key=lambda x: (x[0] != -1, -x[0]))
    print(sum(1 for o in out if o[0] == -1 or o[0] > 1200), 'suspicious of', len(out))
    for o in out[:70]: print(o)
