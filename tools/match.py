import json, re, sys, collections, math, unicodedata
raw = json.load(open(sys.argv[1])); idx = json.load(open(sys.argv[2])); OUT = sys.argv[3]

def norm(s):
    s = (s or '').replace('’', "'")
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().replace('&', 'and')   # "Kalé" -> "kale"
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r"[^a-z0-9' ]+", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

idx = [e for e in idx if e['name'] != 'Melina']   # she appears at graces everywhere; the one datamined spot misleads
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
    'abandoned ailing village': ['Greatbridge, North'], "seluvis's rise": ['Preceptor Seluvis'], "chelona's rise": ['Altar South'],
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
    n = flat(item) if (cat or '').lower().startswith(('sog', 'checkpoint')) else norm(item); c = (cat or '').lower()
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
        es = [e for e in idx if e['kind'] in kinds and (norm(e['name']).startswith(n) or (len(n) > 4 and n in norm(e['name']))
                                                         or norm(e['name']).endswith(' ' + n))]   # "Iji" -> "Smithing Master Iji"
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

# Places named in a step's notes ("Return to the X SoG", "Dropped by Y") locate it more tightly than
# its Location column, which is often just the region. Rank: 0 "<grace> SoG", 1 grace/landmark, 2 boss,
# 3 NPC, 4 a Location-column name written in the notes ("Soldiers, Stormveil Castle").
NOTE_NAMES = {}
SOG_ONLY = set()
GENERIC = {'merchant', 'sister', 'husks', 'corpse', 'knight', 'nurse', 'crone', 'guardian', 'stand', 'table', 'maiden',
           'priestess', 'communion', 'scout', 'hand', 'bear', 'mask', 'grandam', 'assassin', 'atonement', 'shadow', 'bairn'}
# Melina appears at graces everywhere but has one datamined spot; Shabriri is mostly "Shabriri Grape"
NOT_PLACES = {'the', 'd', 'melina', 'shabriri'}
def note_name(key, rank, es):
    if len(key) < 3 or key in NOT_PLACES: return
    if key not in NOTE_NAMES or NOTE_NAMES[key][0] > rank: NOTE_NAMES[key] = (rank, es)
    elif NOTE_NAMES[key][0] == rank and NOTE_NAMES[key][1] is not es:   # "hyetta": Lightseeker and Finger Maiden
        NOTE_NAMES[key] = (rank, NOTE_NAMES[key][1] + [e for e in es if e not in NOTE_NAMES[key][1]])
for kind, rank in (('npc', 3), ('boss', 2), ('grace', 1)):
    full = collections.defaultdict(list)
    for e in idx:
        if e['kind'] == kind: full[norm(e['name'])].append(e)
    for k, es in full.items():
        note_name(k, rank, es)
        if kind != 'grace':
            head = norm(es[0]['name'].split(',')[0])   # "Adan, Thief of Fire" -> "adan"
            note_name(head, rank, es)
            if ',' in es[0]['name']: note_name(norm(es[0]['name'].split(',', 1)[1]), rank, es)   # "Gurranq, Beast Clergyman"
            note_name(head.split(' the ')[0], rank, es)   # "Blaidd the Half-Wolf" -> "blaidd"
            last = head.split(' the ')[0].split(' ')[-1]   # "Finger Reader Enia" -> "enia"
            if kind == 'npc' and len(last) > 2 and last not in GENERIC: note_name(last, rank, es)
        else:
            if not k.endswith('s'): note_name(k + 's', rank, es)   # "Hinterlands SoG" for the Hinterland grace
            tail = norm(es[0]['name'].split(', ')[-1])
            if ', ' in es[0]['name'] and ' ' in tail: note_name(tail, rank, es); SOG_ONLY.add(tail)   # "Seventh Floor SoG"
# items the walkthrough steers by ("Head South from the Nomadic Warrior's Cookbook 4"); short or one-word names are too generic
ITEM_NAMES = collections.defaultdict(list)
for e in idx:
    if e['kind'] in ('item', 'armor') and ' ' in e['name'] and len(e['name']) >= 10: ITEM_NAMES[norm(e['name'])].append(dict(e, kind='item'))
for k, es in ITEM_NAMES.items(): note_name(k, 3.5, es)   # after graces, bosses and NPCs
for loc in LANDMARKS: note_name(loc, 1, [dict(anchor[loc], kind='landmark')] if loc in anchor else [])
# graces named after a whole region ("Gravesite Plain") or a boss ("Fire Giant") only count when written as "<name> SoG"
BOSSES = {norm(e['name']) for e in idx if e['kind'] == 'boss'}
REGION_GRACES = {k for k in NOTE_NAMES if NOTE_NAMES[k][0] == 1 and (k in reg or k in BOSSES or k[:-1] in BOSSES)} | SOG_ONLY
NOTE_KEYS = []
def note_index():
    for k in set(anchor) | set(LEARNED):
        if k not in ALIAS and len(k) > 4 and NOTE_NAMES.get(k, (4,))[0] >= 4: NOTE_NAMES[k] = (4, [LEARNED.get(k) or anchor[k]])
    NOTE_KEYS[:] = [(k, ' ' + flat(k) + ' ') for k in sorted((k for k in NOTE_NAMES if NOTE_NAMES[k][1]), key=len, reverse=True)]
# a boss named as a precondition ("Sold by Enia after defeating Malenia") says nothing about where the step is
AFTER = re.compile(r"((after|once|until|before|when) (you('ve| have)? )?(defeat|beat|kill)\w*|remembrance of|about|for|drops?|contains?) (the )?$")
# nor does where an item is taken afterwards ("Give to Miriel in the Church of Vows")
LATER = re.compile(r"\b(give|hand|bring|deliver)\w* ((it|this|them|these|the book|the item) )?(over )?to\b.*$")

# "Sold by Enia", "Dropped by Adan": the step happens wherever that NPC or boss stands
SOURCE = re.compile(r"\b(?P<verb>sold|given|received|purchased?|bought|obtained|dropped|rewarded|traded?|available for purchase) (to you |to us )?(by|from) (the )?((\w+ ){1,5}(and|or) (the )?)?$"
                    r"|\b(?P<give>give|trade|offer)\w* (?!(it|this|them|these|the book|the item|her|him|one)\b)(\w+ ){1,6}to (the )?$"
                    r"|\b(?P<talk>speak|speaking|talk|talking|spoke) (with|to) (the )?$")

# the guide's spellings of grace names
TYPOS = [('labrynth', 'labyrinth'), ('alter', 'altar'), ('abandon coffin', 'abandoned coffin'), ('form caelid', 'from caelid'),
         ('altus junction highway', 'altus highway junction'), ('impassable great bridge', 'impassable greatbridge'),
         ('caria manor gate', 'main caria manor gate'), ('main main', 'main'), ('gelmir campsite', 'mt gelmir campsite'),
         ('mt mt', 'mt'), ('shaded castle rampart', 'shaded castle ramparts'), ('rampartss', 'ramparts'), ('undergound', 'underground'),
         ('snow fields', 'snowfield'), ('snowfields', 'snowfield'), ('ancient ruins of rauh', 'rauh ancient ruins'),
         ('ruins of rauh', 'rauh ancient ruins'), ('ancient rauh', 'rauh'), ('ante room', 'anteroom'), ('stormviel', 'stormveil'),
         ('cemetary', 'cemetery'), ('apostles derelict', 'apostate derelict'), ('coloseum', 'colosseum'), ('chuch', 'church')]
def flat(s):   # "Morgott's boss gate", "Worshippers' Woods" -> "morgott boss gate", "worshipper woods"
    s = ' ' + re.sub(r"(?<=\w)s?'s?(?=\W|$)", '', norm(s)).replace("'", '') + ' '
    for a, b in TYPOS: s = s.replace(' ' + a + ' ', ' ' + b + ' ')
    return s.strip()

def note_anchor(item, notes, la, prev, realm):
    """The place a step's notes point to, and the NPC/boss it comes from if the notes name one."""
    notes = re.split(r'\bNOTE:', notes)[0]   # "NOTE: ..." asides talk about other places and playthroughs
    text = ' ' + flat(notes) + ' '
    own = ' ' + flat(item) + ' '
    taken = []; found = []; sources = []
    for k, kk in NOTE_KEYS:
        i = text.find(kk)
        while i >= 0 and any(a <= i < b or a < i + len(kk) <= b for a, b in taken): i = text.find(kk, i + 1)
        if i < 0: continue
        taken.append((i, i + len(kk)))
        rank, es = NOTE_NAMES[k]
        if rank >= 2 and (kk in own or own in kk): continue   # the step's own NPC/boss/item says nothing new
        if AFTER.search(text[:i + 1]) or LATER.search(text[:i + 1]): continue
        sog = text.startswith(' sog ', i + len(kk) - 1) or text.startswith(' site of grace ', i + len(kk) - 1)
        if rank == 1 and sog: rank = 0
        if k in REGION_GRACES and rank: continue
        es = [e for e in es if (e['master'] in ('M10', 'M11')) == realm]
        m = SOURCE.search(text[:i + 1]) if rank in (2, 3) else None
        if m and m.group('talk') and rank != 3: m = None   # "speak to <NPC>"; bosses aren't spoken to
        # bosses and NPCs recur across the map; one far from the stated Location is another instance
        # (unless the step names them as the source: "Give Remembrance of the Fire Giant to Enia")
        if la and rank >= 2 and not (m and m.group('give')): es = [e for e in es if d2(e, la) < (min(la.get('radius', 300), 1200) + 1500)**2]
        if not es: continue
        # a region named in the notes only helps when it is narrower than the Location column
        if rank == 4 and la and es[0].get('radius', 300) >= la.get('radius', 300): continue
        if m: sources += [dict(e, drop=m.group('verb') == 'dropped') for e in es]
        elif la or rank not in (2, 3): found.append((rank, i, es))   # without a Location, a boss/NPC is usually just context
    ref = la or prev
    na = None
    if found:
        rank, _, es = min(found, key=lambda f: f[:2])
        r = prev if es[0].get('kind') == 'item' and prev else ref
        na = dict(min(es, key=lambda e: d2(e, r) if r else 0), rank=rank)
        if es[0].get('kind') == 'item' and prev and d2(na, prev) > 1500**2: na = None   # another copy of a common item
    near = na or ref
    src = min(sources, key=lambda e: d2(e, near) if near else 0, default=None)
    if src and na and d2(src, na) > 1500**2: src = None   # "Dropped by Ulcerated Tree Spirit in Leyndell": not the one elsewhere
    return na, src

SCARABS = [e for e in idx if e['kind'] == 'scarab']
# the step is the scarab's drop ("kill the scarab", "find scarab on island"), not a landmark ("ruins with scarab")
KILL_SCARAB = re.compile(r"\b(kill\w*|find|on|look for)(\s+(a|the|an|invisible|teleporting))*\s+scarabs?\b|\bscarabs?\s+(to kill|that|guarded|hanging|on|drops?)\b|(^|\.\s*)(invisible\s+)?scarab\b", re.I)
COMPASS = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}
def headings(notes):
    """Unit vectors for the first compass direction in the notes ("South/Southwest" -> both)."""
    m = re.search(r"\b((?:north|south|east|west|northeast|northwest|southeast|southwest)(?:\s*/\s*(?:north|south|east|west|northeast|northwest|southeast|southwest))*)\b", notes.lower())
    if not m: return []
    out = []
    for w in re.split(r'\s*/\s*', m.group(1)):
        v = [sum(c) for c in zip(*[COMPASS[p] for p in re.findall('north|south|east|west', w)])]
        n = math.hypot(*v); out.append((v[0]/n, v[1]/n))
    return out

def toward(e, ref, dirs):
    """True when e lies roughly in one of the directions from ref."""
    dx, dy = e['px'] - ref['px'], e['py'] - ref['py']; n = math.hypot(dx, dy)
    return not dirs or n < 60 or any((dx*u + dy*v) / n > 0.38 for u, v in dirs)   # within ~67 degrees

def near_steps(out):
    """The guide is walked in order: a step known only by its region sits with the steps around it, not at the region's middle."""
    def neighbour(i, step, la, r):
        j = i + step
        while 0 <= j < len(out) and abs(j - i) <= 3 and not out[j]['section']:
            p = out[j]['pin']
            if p and p['precise'] and p['master'] == la['master'] and d2(p, la) < (r + 300)**2: return p
            j += step
    for i, e in enumerate(out):
        p, la = e['pin'], e['la']
        if e['section'] or not p or not p['src'].startswith('location:') or la.get('radius', 300) <= 400: continue
        r = la['radius']; a, b = neighbour(i, -1, la, r), neighbour(i, 1, la, r)
        if a and b and d2(a, b) < 1500**2: x, y = (a['px'] + b['px']) / 2, (a['py'] + b['py']) / 2
        elif a or b: x, y = (a or b)['px'], (a or b)['py']
        else: continue
        e['pin'] = dict(master=la['master'], px=x, py=y, precise=False, src='near steps')

def run():
    note_index()
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
            na, src = (None, None) if r.get('header') else note_anchor(item, r['notes'] or '', la, prev, realm)
            pin = None
            grace = na if na and na['rank'] <= 1 else None
            if src:
                best = min(es, key=lambda e: d2(e, src), default=None)
                if not (best and d2(best, src) < 600**2):
                    best = src
                    # an enemy drop's own datamined spot beats a guess at which instance of the enemy it is
                    if src['drop'] and es:
                        old = min(es, key=lambda e: (d2(e, la) if la else 0) + 0.5*d2(e, prev))
                        if la and d2(old, la) < (la.get('radius', 300) + 900)**2: best = old
                pin = dict(master=best['master'], px=best['px'], py=best['py'], precise=best.get('extra') != 'tile', src=best['name'])
                na = src
            if es and na and pin is None:
                best = min(es, key=lambda e: d2(e, na) + 0.25*d2(e, prev))
                if d2(best, na) < 1200**2:
                    pin = dict(master=best['master'], px=best['px'], py=best['py'], precise=best.get('extra') != 'tile', src=best['name'])
            ref = na or prev
            if pin is None and ref and KILL_SCARAB.search(r['notes'] or ''):
                # "kill the scarab": the nearest scarab the directions point to
                sc = [e for e in SCARABS if e['master'] == ref['master'] and d2(e, ref) < 1100**2
                      and not (la and d2(e, la) > (la.get('radius', 300) + 300)**2)]
                dirs = headings(r['notes'])
                sc = [e for e in sc if toward(e, ref, dirs)] or sc
                best = min(sc, key=lambda e: d2(e, ref), default=None)
                drop = min(es, key=lambda e: d2(e, ref), default=None)   # the drop's own datamined spot, when there is one
                if drop and d2(drop, ref) < 1100**2 and drop.get('extra') != 'tile': best = dict(drop, name='Scarab')
                if best: pin = dict(master=best['master'], px=best['px'], py=best['py'], precise=True, src='Scarab')
            if es and pin is None:
                best = min(es, key=lambda e: (d2(e, la) if la else 0) + 0.5*d2(e, prev))
                # a match far outside the stated location is usually a different instance (merchant, reward, NPC move)
                if not (la and best['master'][:2] == la['master'][:2] and d2(best, la) > (la.get('radius', 300) + 900)**2):
                    pin = dict(master=best['master'], px=best['px'], py=best['py'], precise=best.get('extra') != 'tile', src=best['name'])
            if pin is None and es and na and na['rank'] > 1:
                # notes name only an NPC/boss/region: a datamined spot near the Location beats a ring on that name
                best = min(es, key=lambda e: (d2(e, la) if la else 0) + 0.5*d2(e, prev))
                if la and d2(best, la) < (la.get('radius', 300) + 1500)**2:
                    pin = dict(master=best['master'], px=best['px'], py=best['py'], precise=best.get('extra') != 'tile', src=best['name'])
            # a spot far from the grace the notes walk you from is another copy of the item or NPC
            if pin and grace and pin['src'] != 'Scarab' and pin['master'] == grace['master'] and d2(pin, grace) > 900**2:
                pin, na = None, grace
            if pin is None and na and not (la and d2(na, la) > (la.get('radius', 300) + 1500)**2):
                pin = dict(master=na['master'], px=na['px'], py=na['py'], precise=False, src='notes: '+na['name'])
            if pin is None and la:
                pin = dict(master=la['master'], px=la['px'], py=la['py'], precise=False, src='location: '+la['name'])
            stats[(sheet, 'precise' if pin and pin['precise'] else ('approx' if pin else 'none'))] += 1
            out.append(dict(step=len(out)+1, item=item, category=(r['cat'] or '').strip(), location=loc,
                            notes=str(r['notes'] or '').strip(), section=bool(r.get('header')), ng=bool(r.get('ng')), pin=pin, la=la))
            if pin and pin['precise']: prev = dict(master=pin['master'], px=pin['px'], py=pin['py'])
        near_steps(out)
        for e in out: del e['la']
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
