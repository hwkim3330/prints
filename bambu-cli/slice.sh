#!/bin/sh
# Slice STLs for the Bambu A1 (0.4 nozzle, 0.20mm Standard, Bambu PLA Basic, Textured PEI) inside an
# x86 Linux container, because the macOS Bambu Studio is blocked on this Mac.
#   bambu-cli/slice.sh OUT.gcode.3mf part.stl [more.stl ...]     (paths under ~/prints)
# First time: put the Linux AppImage at bambu-cli/bs.AppImage, then
#   docker build --platform linux/amd64 -t bambu-cli bambu-cli
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=$1; shift
P=/w/bambu-cli/profiles
if [ ! -f "$ROOT/bambu-cli/profiles/process.json" ]; then
  docker run --rm --platform linux/amd64 -v "$ROOT":/w --entrypoint python3 bambu-cli \
    /w/bambu-cli/flatten.py /opt/squashfs-root/resources/profiles/BBL $P
  python3 -c "import json,sys;p=sys.argv[1];d=json.load(open(p));d['curr_bed_type']='Textured PEI Plate';json.dump(d,open(p,'w'),indent=1)" \
    "$ROOT/bambu-cli/profiles/process.json"
fi
ARGS=""
for f in "$@"; do ARGS="$ARGS /w/$(cd "$(dirname "$f")" && pwd | sed "s|^$ROOT/||")/$(basename "$f")"; done
mkdir -p "$ROOT/sliced"
docker run --rm --platform linux/amd64 -v "$ROOT":/w --entrypoint /opt/squashfs-root/AppRun bambu-cli \
  --slice 0 --arrange 1 --orient 0 --load-settings "$P/machine.json;$P/process.json" --load-filaments "$P/filament.json" \
  --outputdir /w/sliced --export-3mf "$(basename "$OUT")" $ARGS > "$ROOT/sliced/log.txt" 2>&1
unzip -p "$ROOT/sliced/$(basename "$OUT")" Metadata/plate_1.gcode | grep -m2 -E "total estimated time|total filament weight"
cp "$ROOT/sliced/$(basename "$OUT")" "$OUT"
