"""Four camera-mount test pieces on one plate, to pick the M2 pitch / opening offset that fits:
uv run --with cadquery --with trimesh --with numpy python sensor-box/cam_variants.py  -> v5/cam_test_variants.stl"""
import sys; sys.path.insert(0, 'sensor-box')
import box as B
import cadquery as cq

VARIANTS = [   # (marks, M2 centre pitch, clear-housing offset)
    (1, (34.1, 29.0), B.CLEAR_DY),   # v5: reading = near-edge gap + 2.2
    (2, (33.0, 27.9), B.CLEAR_DY),   # half way
    (3, (31.9, 26.8), B.CLEAR_DY),   # reading taken as centre distance
    (4, (34.1, 29.0), 0.0),          # clear housing centred (if it is not flush after all)
]
out = cq.Workplane("XY")
for k, (marks, pitch, dy) in enumerate(VARIANTS):
    B.M2_HOLES = [(sx * pitch[0] / 2, sz * pitch[1] / 2) for sx in (-1, 1) for sz in (-1, 1)]
    B.CLEAR_DY = dy
    t = B.cam_test()
    w, h = B.PAD[0] + 10, B.PAD[1] + 10
    for m in range(marks):                     # 1-4 small holes in the bottom-left corner = variant number
        t = t.cut(cq.Workplane("XY").center(-w / 2 + 3.5 + m * 3.5, B.CAM_Z - h / 2 + 3.5).circle(0.9).extrude(10))
    out = out.union(t.translate(((k % 2) * (w + 6), -(k // 2) * (h + 6), 0)))
cq.exporters.export(out, "sensor-box/v5/cam_test_variants.stl")
print("ok")
