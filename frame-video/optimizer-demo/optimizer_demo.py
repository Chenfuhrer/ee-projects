"""四种优化器在 f(x, y) = x²/20 + y² 上的轨迹（鱼书第 6 章那个函数）。frame-video skill 版。

    python3 optimizer_demo.py --preview   # 低清预览
    python3 optimizer_demo.py             # 版面自检 → 4K/1080p 60fps → 成片自检 → 删中间帧
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/frame-video/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 优先用仓库里的 fv.py
import fv  # noqa: E402
import numpy as np  # noqa: E402

DURATION = 5.0
T_START, T_END = 0.4, 4.2  # 0–0.4s 停在起点，0.4–4.2s 走完 30 步，之后定格
N_ITER = 30
OUT = Path(__file__).with_name("optimizer_demo")

# ---------- 配色（dataviz 参考色板，深色模式；4 色已用 validate_palette.js 校验） ----------
SURFACE = "#1a1a19"
INK, INK2, MUTED = "#f0efec", "#c3c2b7", "#898781"
GRID, AXIS = "#2c2c2a", "#383835"
COLORS = ["#3987e5", "#d95926", "#199e70", "#c98500"]  # 分类色 slot 1–4


# ---------- 优化器：整条轨迹先算好，frame(t) 只查表 ----------
def f(x, y):
    return x**2 / 20 + y**2


def grad(p):
    return np.array([p[0] / 10, 2 * p[1]])


def run(name, n=N_ITER, start=(-7.0, 2.0)):
    p = np.array(start)
    path = [p.copy()]
    v, h, m, s = (np.zeros(2) for _ in range(4))
    for t in range(1, n + 1):
        g = grad(p)
        if name == "SGD":
            p = p - 0.95 * g
        elif name == "Momentum":
            v = 0.9 * v - 0.1 * g
            p = p + v
        elif name == "AdaGrad":
            h += g * g
            p = p - 1.5 * g / (np.sqrt(h) + 1e-7)
        elif name == "Adam":
            lr_t = 0.3 * np.sqrt(1 - 0.999**t) / (1 - 0.9**t)
            m += 0.1 * (g - m)
            s += 0.001 * (g * g - s)
            p = p - lr_t * m / (np.sqrt(s) + 1e-7)
        path.append(p.copy())
    return np.array(path)


OPTS = [("SGD", "lr=0.95"), ("Momentum", "lr=0.1, β=0.9"),
        ("AdaGrad", "lr=1.5"), ("Adam", "lr=0.3")]
PATHS = {name: run(name) for name, _ in OPTS}
# loss 曲线在 log 轴上，对 log10(loss) 插值才自然
LOG_LOSS = {name: np.column_stack([np.arange(N_ITER + 1), np.log10(f(P[:, 0], P[:, 1]))])
            for name, P in PATHS.items()}

# ---------- 画布（只建一次，每帧更新数据） ----------
fig, L = fv.canvas(bg=SURFACE, ink=INK)
fig.text(*L.xy(48, 52), "优化器怎么走到最低点", fontsize=22, weight="bold", color=INK)
fig.text(*L.xy(48, 84), "f(x, y) = x²/20 + y²，起点 (−7, 2)，每种优化器迭代 30 步",
         fontsize=12, color=MUTED)
step_text = fig.text(*L.xy(1232, 52), "", fontsize=16, color=INK2, ha="right")

xs, ys = np.linspace(-8, 2, 300), np.linspace(-2.6, 2.6, 200)
X, Y = np.meshgrid(xs, ys)
Z = f(X, Y)

PANEL_W, PANEL_H = 340, 177
cells = [(48, 182), (416, 182), (48, 425), (416, 425)]
trails, heads = {}, {}
for (name, hp), color, (x0, y0) in zip(OPTS, COLORS, cells):
    ax = fig.add_axes(L.rect(x0, y0, PANEL_W, PANEL_H), facecolor=SURFACE)
    ax.contour(X, Y, Z, levels=[0.05, 0.2, 0.5, 1, 2, 3.5, 5.5], colors=AXIS, linewidths=0.8)
    ax.plot(0, 0, marker="+", color=MUTED, ms=9, mew=1.2)
    ax.plot(-7, 2, marker="o", color=MUTED, ms=4)
    ax.set_xlim(-8, 2)
    ax.set_ylim(-2.6, 2.6)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color(GRID)
    # 小图标题：色点 + 名称（墨色）+ 超参（灰色）
    ax.plot([0.012], [1.09], "o", color=color, ms=8, transform=ax.transAxes, clip_on=False)
    ax.text(0.04, 1.09, name, transform=ax.transAxes, fontsize=13, weight="bold",
            color=INK, va="center")
    ax.text(0.99, 1.09, hp, transform=ax.transAxes, fontsize=10, color=MUTED,
            va="center", ha="right")
    trails[name], = ax.plot([], [], "-o", color=color, lw=1.8, ms=3.2, mec=SURFACE, mew=0.6)
    heads[name], = ax.plot([], [], "o", color=color, ms=9, mec=SURFACE, mew=1.8, zorder=5)

LOSS_BOX = (842, 182, 270, 420)
lax = fig.add_axes(L.rect(*LOSS_BOX), facecolor=SURFACE)
lax.set_yscale("log")
YMIN, YMAX = 3e-4, 12
lax.set_xlim(0, N_ITER)
lax.set_ylim(YMIN, YMAX)
lax.set_title("loss  f(x, y)", loc="left", fontsize=13, weight="bold", color=INK, pad=12)
lax.set_xlabel("迭代步数", color=MUTED, fontsize=10)
lax.tick_params(colors=MUTED, labelsize=9, length=0)
lax.grid(True, which="major", color=GRID, lw=0.8)
lax.set_axisbelow(True)
for side, sp in lax.spines.items():
    sp.set_visible(side == "bottom")
    sp.set_color(AXIS)
loss_lines, loss_heads, loss_labels = {}, {}, {}
for (name, _), color in zip(OPTS, COLORS):
    loss_lines[name], = lax.plot([], [], color=color, lw=1.8)
    loss_heads[name], = lax.plot([], [], "o", color=color, ms=7, mec=SURFACE, mew=1.5,
                                 zorder=5, clip_on=False)
    loss_labels[name] = lax.text(0, 1, "", fontsize=10, color=INK2, va="center",
                                 clip_on=False, fontfamily=["Menlo", "PingFang SC"])

LOG_LO, LOG_HI = np.log10(YMIN), np.log10(YMAX)
GAP = (LOG_HI - LOG_LO) * 18 / LOSS_BOX[3]  # 直标间距约 18 逻辑像素


def frame(t):
    k = fv.progress(t, T_START, T_END) * N_ITER
    step_text.set_text(f"第 {int(k):>2d} / {N_ITER} 步")
    heads_xy = []
    for name, _ in OPTS:
        P = fv.reveal(PATHS[name], k)
        trails[name].set_data(P[:, 0], P[:, 1])
        heads[name].set_data([P[-1, 0]], [P[-1, 1]])
        LP = fv.reveal(LOG_LOSS[name], k)
        loss_lines[name].set_data(LP[:, 0], 10 ** LP[:, 1])
        loss_heads[name].set_data([LP[-1, 0]], [10 ** LP[-1, 1]])
        heads_xy.append(LP[-1])
    label_y = fv.repel([max(y, LOG_LO) for _, y in heads_xy], GAP, lo=LOG_LO + GAP / 2, hi=LOG_HI - GAP / 2)
    for (name, _), (hx, hy), ly in zip(OPTS, heads_xy, label_y):
        loss_labels[name].set_position((hx + 0.8, 10**ly))
        loss_labels[name].set_text(f"{name} {10 ** hy:.1e}")


if __name__ == "__main__":
    if "--preview" in sys.argv:
        fv.stills(fig, frame, [0, 1.5, 3.0, DURATION - 0.02])
    else:
        fv.build(fig, frame, DURATION, out=OUT)
