"""Flatten Bambu Studio system profiles (resolve the `inherits` chain) so the CLI gets complete settings.

  python3 flatten.py PROFILES_DIR/BBL OUT_DIR
Writes machine.json, process.json, filament.json for the A1 0.4 / 0.20mm Standard / Bambu PLA Basic set.
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
    d = index[(kind, name)]
    base = resolve(kind, d["inherits"]) if d.get("inherits") else {}
    merged = dict(base)
    merged.update(d)
    merged.pop("inherits", None)
    return merged


picks = {"machine": "Bambu Lab A1 0.4 nozzle", "process": "0.20mm Standard @BBL A1", "filament": "Bambu PLA Basic @BBL A1"}
os.makedirs(out, exist_ok=True)
for kind, name in picks.items():
    d = resolve(kind, name)
    d["from"] = "system"
    json.dump(d, open(os.path.join(out, kind + ".json"), "w"), indent=1)
    print(kind, name, len(d), "keys")
