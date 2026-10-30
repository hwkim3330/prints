"""Flatten Bambu Studio system profiles (resolve the `inherits` chain) so the CLI gets complete settings.

  python3 flatten.py PROFILES_DIR/BBL OUT_DIR
Writes machine.json, process.json, filament.json for the A1 0.4 / 0.20mm Standard / Bambu PLA Basic set.
  python3 flatten.py PROFILES_DIR/BBL OUT_DIR "Generic PETG @BBL A1" filament_petg
Writes only that filament, as OUT_DIR/filament_petg.json (pick it with FIL=filament_petg in slice.sh).
"""
import json, os, sys

root, out = sys.argv[1], sys.argv[2]
index = {}
for kind in ("machine", "process", "filament"):
    for dp, _, fs in os.walk(os.path.join(root, kind)):
        for f in fs:
            if f.endswith(".json"):
                p = os.path.join(dp, f)
                try:
                    d = json.load(open(p))
                except Exception:
                    continue
                if "name" in d:
                    index[(kind, d["name"])] = d


def resolve(kind, name):
    """inherits chain first, then the profile's `include` templates (newer profiles keep the start/end/
    filament-change G-code there; without them the CLI falls back to a generic start that only heats the
    nozzle to 205 C), then the profile itself."""
    d = index[(kind, name)]
    merged = dict(resolve(kind, d["inherits"])) if d.get("inherits") else {}
    for inc in d.get("include", []):
        merged.update({k: v for k, v in index[(kind, inc)].items() if k not in ("name", "instantiation")})
    merged.update(d)
    for k in ("inherits", "include"):
        merged.pop(k, None)
    return merged


picks = {"machine": "Bambu Lab A1 0.4 nozzle", "process": "0.20mm Standard @BBL A1", "filament": "Bambu PLA Basic @BBL A1"}
if len(sys.argv) > 4:
    picks = {sys.argv[4]: sys.argv[3]}
os.makedirs(out, exist_ok=True)
for kind, name in picks.items():
    d = resolve("filament" if kind.startswith("filament") else kind, name)
    d["from"] = "system"
    json.dump(d, open(os.path.join(out, kind + ".json"), "w"), indent=1)
    print(kind, name, len(d), "keys")
