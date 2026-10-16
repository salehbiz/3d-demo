"""Render a floor-plan JSON (see ground_floor.json) to a PNG for review.

Usage: python3 plan/render_plan.py plan/ground_floor.json plan/ground_floor.png
Room fill colour shows confidence: green = confirmed from video, amber = partly,
grey hatch = assumed (not visible in the video).
"""
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Rectangle

FILL = {"high": "#d8ecd5", "medium": "#eef3d6", "low": "#f7e6c8", "assumed": "#eeeeee"}
WALL_W = {"exterior": 7, "interior": 3}


def wall_line(spec, lo, hi):
    axis, val = spec.split("=")
    val = float(val)
    return ((lo, val), (hi, val)) if axis == "y" else ((val, lo), (val, hi))


def main(src, dst):
    plan = json.load(open(src))
    fig, ax = plt.subplots(figsize=(9, 11), dpi=150)
    ax.set_aspect("equal")
    ax.axis("off")

    for r in plan["rooms"]:
        conf = r.get("confidence", "assumed")
        ax.add_patch(Rectangle((r["x"], r["y"]), r["w"], r["d"], facecolor=FILL[conf],
                               edgecolor="none", hatch="///" if conf == "assumed" else None,
                               linestyle="--" if r.get("exterior") else "-", zorder=0))
        if r.get("label") is False:
            continue
        label = r["name"] + ("\n(assumed)" if conf == "assumed" else "")
        ax.text(r["x"] + r["w"] / 2, r["y"] + r["d"] / 2, label, ha="center", va="center",
                fontsize=8, zorder=5,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.7, pad=1.5))

    for w in plan["walls"]:
        (x1, y1), (x2, y2) = w["a"], w["b"]
        ax.plot([x1, x2], [y1, y2], color="black", lw=WALL_W[w["type"]],
                solid_capstyle="projecting", zorder=2)

    for o in plan["openings"]:
        (x1, y1), (x2, y2) = wall_line(o["wall"], o["from"], o["to"])
        ax.plot([x1, x2], [y1, y2], color="white", lw=9, zorder=3)
        k = o["kind"]
        color = "#888" if o.get("confidence") == "assumed" else "#1f5fa8"
        if k in ("window", "sliding_glass", "glass_door"):
            ax.plot([x1, x2], [y1, y2], color=color, lw=2 if k == "window" else 3, zorder=4)
        if k in ("door", "pivot_door", "glass_door"):
            width = abs(x2 - x1) + abs(y2 - y1)
            ax.add_patch(Arc((x1, y1), 2 * width, 2 * width, theta1=0, theta2=90,
                             color=color, lw=1, zorder=4))

    for f in plan["fixtures"]:
        if "w" not in f:
            continue
        ax.add_patch(Rectangle((f["x"], f["y"]), f["w"], f["d"], facecolor="white",
                               edgecolor="#444", lw=1, zorder=4))
        if f["kind"] == "planter":
            ax.add_patch(Rectangle((f["x"], f["y"]), f["w"], f["d"], facecolor="#c9c4b8",
                                   edgecolor="#444", lw=1, zorder=4))
    stair = next(r for r in plan["rooms"] if r["id"] == "stair")
    for i in range(1, 17):
        y = stair["y"] + stair["d"] * i / 17
        ax.plot([stair["x"], stair["x"] + stair["w"]], [y, y], color="#666", lw=0.6, zorder=4)
    ax.annotate("UP", xy=(stair["x"] + stair["w"] / 2, stair["y"] + stair["d"] - 0.3),
                xytext=(stair["x"] + stair["w"] / 2, stair["y"] + 0.3), ha="center", fontsize=7,
                arrowprops=dict(arrowstyle="->", lw=0.8), zorder=6)

    fp = plan["footprint"]
    ax.text(fp["w"] / 2, -2.4, "DIAMOND STREET (front)", ha="center", fontsize=9)
    ax.text(fp["w"] / 2, fp["d"] + 0.5, "Pool terrace (rear)", ha="center", fontsize=9)
    ax.annotate("", xy=(0, -0.7), xytext=(fp["w"], -0.7),
                arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(1.0, -0.6, f'{fp["w"]:.1f} m', fontsize=8)
    ax.annotate("", xy=(-0.7, 0), xytext=(-0.7, fp["d"]),
                arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(-1.0, fp["d"] / 2, f'{fp["d"]:.1f} m', fontsize=8, rotation=90, va="center")
    ax.set_xlim(-1.5, fp["w"] + 1)
    ax.set_ylim(-3, fp["d"] + 1.2)
    ax.set_title("Ground floor — 1159 Diamond St  (green = seen in video, amber = partly, grey = assumed)",
                 fontsize=9)
    fig.savefig(dst, bbox_inches="tight")


if __name__ == "__main__":
    main(*sys.argv[1:3])
