"""1:1 A4 template of the servo and horn sizes crab.py assumes (S = MG996R, M = MG90S), to check real servos on paper.

Print servo_template.pdf at 100 % ("실제 크기", no fit-to-page) and check the 100 mm bar with a ruler first. Lay each
servo and horn on its outline: where the real part doesn't match, write the measured value in the table on page 2.

Run:  uv run --with numpy --with matplotlib python crab-arm/servo_template.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

import crab as C

HERE = os.path.dirname(os.path.abspath(__file__))
A4 = (210.0, 297.0)
plt.rcParams["font.family"] = "AppleGothic"
plt.rcParams["pdf.fonttype"] = 42
INK, DIM = "#222", "#c0392b"


def page():
    fig = plt.figure(figsize=(A4[0] / 25.4, A4[1] / 25.4))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, A4[0]); ax.set_ylim(0, A4[1]); ax.set_aspect("equal"); ax.set_axis_off()
    return fig, ax


def text(ax, x, y, s, size=7, **kw):
    ax.text(x, y, s, fontsize=size, color=kw.pop("color", INK), **kw)


def top_view(ax, s, x0, y0, name):
    """case + ears from above, spline on the left (the 'front'), holes; x0, y0 = case left-bottom corner"""
    L, W, span = s["L"], s["W"], s["SPAN"]
    ear = (span - L) / 2
    ax.add_patch(Rectangle((x0 - ear, y0), span, W, fill=False, lw=0.5, ls="--", ec=INK))
    ax.add_patch(Rectangle((x0, y0), L, W, fill=False, lw=0.8, ec=INK))
    cx = x0 + L / 2
    hx, hy = s["HOLES"]
    for sx in (-1, 1):
        for sy in ((-1, 1) if hy else (0,)):
            ax.add_patch(Circle((cx + sx * hx / 2, y0 + W / 2 + sy * hy / 2), 1.0, fill=False, lw=0.6, ec=INK))
    sp = (x0 + s["SPL"], y0 + W / 2)
    ax.add_patch(Circle(sp, s["BOSS"][0] / 2, fill=False, lw=0.6, ec=INK))
    ax.plot(*sp, "+", color=INK, ms=4, mew=0.6)
    text(ax, x0 - ear, y0 + W + 2, f"{name} 위에서 (점선 = 귀)", 8, weight="bold")
    text(ax, x0, y0 - 4, f"몸통 {L} × {W}   귀 끝-끝 {span}   귀 구멍 간격 {hx}" + (f" × {hy}" if hy else ""), 6.5, color=DIM)
    text(ax, x0, y0 - 7.5, f"스플라인 중심: 앞 끝에서 {s['SPL']}", 6.5, color=DIM)


def side_view(ax, s, x0, y0, name):
    """from the side: case, ears, boss, horn; y0 = case bottom"""
    L, span = s["L"], s["SPAN"]
    ear = (span - L) / 2
    bot, top, tab, horn, ht = s["BOT"], s["TOP"], s["TAB"], s["HORN"], s["HT"]
    ax.add_patch(Rectangle((x0, y0), L, bot + top, fill=False, lw=0.8, ec=INK))
    ax.add_patch(Rectangle((x0 - ear, y0 + bot), span, tab, fill=False, lw=0.6, ec=INK))
    sx = x0 + s["SPL"]
    b = s["BOSS"][0]
    ax.add_patch(Rectangle((sx - b / 2, y0 + bot + top), b, horn - ht - top, fill=False, lw=0.6, ec=INK))
    hd = s["HD"] if s is C.S else s["ARM"][0] * 2
    ax.add_patch(Rectangle((sx - hd / 2, y0 + bot + horn - ht), hd, ht, fill=False, lw=0.6, ec=INK))
    ax.plot([x0 - ear - 4, x0 + L + ear + 4], [y0, y0], color="#999", lw=0.4)
    text(ax, x0 - ear, y0 + bot + horn + 2, f"{name} 옆에서", 8, weight="bold")
    text(ax, x0 + L + ear + 3, y0 + bot / 2, f"귀 아랫면까지 {bot}", 6.5, color=DIM)
    text(ax, x0 + L + ear + 3, y0 + bot + tab / 2 - 1, f"귀 두께 {tab}", 6.5, color=DIM)
    text(ax, x0 + L + ear + 3, y0 + bot + horn - 2, f"귀 아랫면→혼 윗면 {horn}", 6.5, color=DIM)


def round_horn(ax, s, c):
    ax.add_patch(Circle(c, s["HD"] / 2, fill=False, lw=0.8, ec=INK))
    for r, a in s["HSCREW"]:
        import math
        ax.add_patch(Circle((c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a))), 0.6,
                            fill=False, lw=0.5, ec=INK))
    ax.plot(*c, "+", color=INK, ms=4, mew=0.6)
    text(ax, c[0] - s["HD"] / 2, c[1] + s["HD"] / 2 + 2, "MG996R 원형 혼", 8, weight="bold")
    text(ax, c[0] - s["HD"] / 2, c[1] - s["HD"] / 2 - 4, f"지름 {s['HD']}  두께 {s['HT']}  나사 반지름 7.5 × 4", 6.5, color=DIM)


def arm_horn(ax, m, c):
    """MG90S one-arm horn: hub circle, tapered arm to the tip circle, screw holes along the arm"""
    hub, (length, tip) = m["HD"], m["ARM"]
    ax.add_patch(Circle(c, hub / 2, fill=False, lw=0.8, ec=INK))
    ax.add_patch(Circle((c[0] + length, c[1]), tip / 2, fill=False, lw=0.8, ec=INK))
    ax.plot([c[0], c[0] + length], [c[1] + hub / 2, c[1] + tip / 2], color=INK, lw=0.8)
    ax.plot([c[0], c[0] + length], [c[1] - hub / 2, c[1] - tip / 2], color=INK, lw=0.8)
    for r, _ in m["HSCREW"]:
        ax.add_patch(Circle((c[0] + r, c[1]), 0.5, fill=False, lw=0.5, ec=INK))
    ax.plot(*c, "+", color=INK, ms=4, mew=0.6)
    text(ax, c[0] - hub / 2, c[1] + hub / 2 + 2, "MG90S 한쪽 팔 혼", 8, weight="bold")
    text(ax, c[0] - hub / 2, c[1] - hub / 2 - 4, f"허브 {hub}  끝 {tip}  길이 {length}  두께 {m['HT']}  구멍 9 · 12", 6.5,
         color=DIM)


def scale(ax, x, y):
    ax.plot([x, x + 100], [y, y], color=INK, lw=1.0)
    for i in range(0, 101, 10):
        ax.plot([x + i, x + i], [y, y + (3 if i % 50 == 0 else 1.5)], color=INK, lw=0.6)
    text(ax, x, y + 4, "100 mm: 자로 재서 맞는지 먼저 확인 (안 맞으면 '실제 크기'로 다시 인쇄)", 7)
    ax.add_patch(Rectangle((x + 110, y - 2), 50, 50, fill=False, lw=0.6, ec=INK))
    text(ax, x + 112, y + 22, "50 × 50 mm", 7)


def main():
    S, M = C.S, C.M
    out = os.path.join(HERE, "servo_template.pdf")
    with PdfPages(out) as pdf:
        fig, ax = page()
        text(ax, 15, 282, "서보 맞춤 템플릿 1:1  (crab.py 가정 치수)", 13, weight="bold")
        text(ax, 15, 276, "100 % 인쇄 → 진짜 서보·혼을 그림 위에 올려 보고, 다른 곳은 2쪽 표에 실측값을 적기", 8)
        top_view(ax, S, 30, 235, "MG996R")
        side_view(ax, S, 30, 160, "MG996R")
        top_view(ax, M, 140, 240, "MG90S")
        side_view(ax, M, 140, 175, "MG90S")
        round_horn(ax, S, (50, 105))
        arm_horn(ax, M, (130, 105))
        scale(ax, 15, 30)
        pdf.savefig(fig); plt.close(fig)

        fig, ax = page()
        text(ax, 15, 282, "실측 기록 (mm, 캘리퍼)", 13, weight="bold")
        rows = [("몸통 길이", S["L"], M["L"]), ("몸통 폭", S["W"], M["W"]), ("귀 끝-끝", S["SPAN"], M["SPAN"]),
                ("귀 구멍 간격 (길이 방향)", S["HOLES"][0], M["HOLES"][0]), ("귀 구멍 간격 (폭 방향)", S["HOLES"][1], "-"),
                ("귀 구멍 지름", "", ""), ("귀 두께", S["TAB"], M["TAB"]),
                ("바닥 → 귀 아랫면", S["BOT"], M["BOT"]), ("귀 아랫면 → 몸통 윗면", S["TOP"], M["TOP"]),
                ("귀 아랫면 → 혼 윗면 (혼 끼운 상태)", S["HORN"], M["HORN"]), ("스플라인 중심 → 몸통 앞 끝", S["SPL"], M["SPL"]),
                ("스플라인 보스 지름", S["BOSS"][0], M["BOSS"][0]), ("혼 지름 / 허브 지름", S["HD"], M["HD"]),
                ("혼 두께", S["HT"], M["HT"]), ("혼 나사 구멍 반지름 / 위치", "7.5", "9, 12"), ("MG90S 혼 팔 길이 / 끝 지름", "-", "15 / 4")]
        y = 262
        for i, h in enumerate(["항목", "MG996R 가정", "실측", "MG90S 가정", "실측"]):
            text(ax, [15, 105, 130, 155, 180][i], y, h, 8, weight="bold")
        for name, a, b in rows:
            y -= 12
            ax.plot([15, 200], [y - 3, y - 3], color="#ccc", lw=0.4)
            text(ax, 15, y, name, 7.5)
            text(ax, 105, y, str(a), 7.5, color=DIM)
            text(ax, 155, y, str(b), 7.5, color=DIM)
        text(ax, 15, y - 15, "사진으로 보내도 됨: 서보를 템플릿 위에 올린 채 위에서 한 장, 옆에서 한 장.", 8)
        text(ax, 15, y - 22, "이 값으로 crab.py 의 S / M 을 고치면 팔·더미·충돌 검사가 전부 따라감.", 8)
        pdf.savefig(fig); plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()
