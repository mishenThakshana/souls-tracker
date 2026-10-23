# Copy the zoom-5 map tiles that any checklist crop touches into the app assets.
# The app cuts each entry's crop from these at runtime (see MapCropRenderer.kt).
import json, os, sys
from PIL import Image
TILES, MATCHED, OUTDIR = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, SIZE, TILE = 576, 360, 5248, 256   # must match MapCropRenderer
BG = (14, 13, 11)

data = json.load(open(MATCHED))
need = set()
for sheet in ('base', 'dlc'):
    for e in data[sheet]:
        p = e['pin']
        if not p: continue
        x0 = max(0, min(SIZE - W, int(p['px'] / 2 - W / 2)))
        y0 = max(0, min(SIZE - H, int(p['py'] / 2 - H / 2)))
        for ty in range(y0 // TILE, (y0 + H) // TILE + 1):
            for tx in range(x0 // TILE, (x0 + W) // TILE + 1):
                need.add((p['master'], tx, ty))

total = 0
for master, tx, ty in sorted(need):
    src = os.path.join(TILES, master, 'base', '5', str(ty), f'{tx}.webp')
    if not os.path.exists(src): continue
    tile = Image.open(src).convert('RGBA')
    flat = Image.new('RGB', tile.size, BG)
    flat.paste(tile, mask=tile.split()[3])
    os.makedirs(os.path.join(OUTDIR, master), exist_ok=True)
    dst = os.path.join(OUTDIR, master, f'{ty}_{tx}.webp')
    flat.save(dst, 'WEBP', quality=70, method=6)
    total += os.path.getsize(dst)
print(len(need), 'tiles', round(total / 1e6, 2), 'MB')
