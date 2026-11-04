"""King Crab arm v2: step-by-step assembly sheet (v2/assembly.png).

Each panel shows the arm in the home pose with the parts already fitted in purple, the servos in dark grey and the
parts of this step in orange, pulled out along their joint axis so you can see where they go.

Run:  uv run --with cadquery --with trimesh --with numpy --with vtk --with matplotlib --with scipy --with networkx \\
        --with manifold3d --with shapely python crab-arm/assembly_v2.py
"""
import os

import numpy as np

import crab_v2 as V
import render_v2 as R

HOME = V.POSES["home (upright, forearm forward)"]
PURPLE, NEW, SERVO, LID = (0.55, 0.45, 0.75), (0.96, 0.55, 0.20), (0.20, 0.20, 0.22), (0.86, 0.86, 0.85)

# (title, parts of this step, explode direction: "z" up, "x" out along the joint axis)
STEPS = [
    ("1  터렛 → 뚜껑 (M4×20 4개, 너트는 뚜껑 밑 육각홈)\n    J1 MG996R을 터렛에 세워 넣고 귀 M3×8 4개",
     ["turret", "j1_case"], "z"),
    ("2  서보 중립(1500us) 맞추고 J1 원형 혼 끼움\n    턴테이블을 혼 위에, 혼 나사 M2×10 3개",
     ["j1_horn", "turntable"], "z"),
    ("3  J2 MG996R을 턴테이블 받침 홈에 위에서 내려 넣기\n    귀 M3×8 4개, 혼은 윗팔이 세워진 자세(90°)로",
     ["j2_case", "j2_horn"], "z"),
    ("4  윗팔 Q를 J2 혼에 (바깥에서 혼 나사 4개)\n    J3 MG996R을 Q 바깥면 창에 → 어깨쪽 귀 2개 먼저 M3×8\n    J3 덮개 씌우고 팔꿈치쪽 귀를 M3×16 2개로 덮개째",
     ["upper_q", "j3_case", "j3_horn", "cover_j3"], "x"),
    ("5  아래팔 F를 J3 혼에 (앞으로 뻗은 자세)\n    J4 MG90S를 F 바깥면에 → 귀 하나 먼저 M2×8\n    J4 덮개 씌우고 남은 귀를 M2×14로 덮개째",
     ["fore_f", "j4_case", "j4_horn", "cover_j4"], "x"),
    ("6  J5 MG90S를 집게 몸통 안에 눕혀 넣고 귀 M2×8\n    집게 관절을 J4 혼에 (관절 밑 카운터보어에서 M2)\n    움직이는 손가락을 J5 혼에 (닫힌 자세, M2 2개)",
     ["claw", "j5_case", "j5_horn", "dactyl"], "x"),
    ("7  아래팔 막대(web) → 반대판 F' (막대에 M3×12 2개)\n    J4 축: F' 구멍으로 M3×16 + 와셔, 부드럽게 돌 만큼만",
     ["web_f", "fore_fp"], "x"),
    ("8  윗팔 막대 → 반대판 Q' (막대에 M3×12 2개)\n    J2·J3 축: Q' 구멍으로 M3×12 + 와셔 각각, 살짝만",
     ["web_u", "upper_qp"], "x"),
]


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "AppleGothic"

    parts, dummies, lid, _ = V.scene_meshes()
    ch = V.chain(HOME)
    world = {}
    for n, (m, fr) in {**parts, **dummies}.items():
        w = m.copy(); w.apply_transform(ch[fr]); world[n] = w
    lid = lid.copy()
    mid_x = (world["upper_q"].centroid[0] + world["upper_qp"].centroid[0]) / 2

    def colour(n):
        return SERVO if n.endswith("_case") else PURPLE

    fig, axs = plt.subplots(2, 4, figsize=(24, 13.5))
    done = []
    for ax, (title, new, how) in zip(axs.flat, STEPS):
        scene = [(lid, LID)] + [(world[n], colour(n)) for n in done]
        for n in new:
            m = world[n].copy()
            if how == "z":
                m.apply_translation((0, 0, 45 + 20 * new.index(n)))
            else:
                s = 1.0 if m.centroid[0] >= mid_x else -1.0
                m.apply_translation((s * (35 + 12 * new.index(n)), 0, 0))
            scene.append((m, SERVO if n.endswith("_case") else NEW))
        cam = R._cam(150, 22, 720, (0, 70, 110))
        ax.imshow(R.render(scene, cam, size=(1000, 820)))
        ax.set_title(title, fontsize=13, loc="left", color="#222")
        ax.set_axis_off()
        done += new
    fig.suptitle("킹크랩 팔 v2 조립 순서  ·  주황 = 이번 단계 부품,  회색 = 서보,  보라 = 이미 끼운 것", fontsize=17)
    fig.tight_layout()
    out = os.path.join(V.OUT, "assembly.png")
    fig.savefig(out, dpi=90)
    print(out)


if __name__ == "__main__":
    main()
