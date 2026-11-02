"""生日快乐（通用版 · 竖屏 9:16 · 代码合成的音乐盒版生日歌）。frame-video skill。

    python3 birthday.py --preview   # 低清预览几个关键时间点
    python3 birthday.py             # 合成音乐 → 版面自检 → 4K/1080p 60fps → 成片自检 → 删中间文件

改名字：把 NAME 改成 "小明"，第三句旋律（原本唱名字的位置）会显示「亲爱的 小明」。
"""
import os
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/frame-video/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 优先用仓库里的 fv.py
import fv  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import patheffects as pe  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
from matplotlib.transforms import Affine2D  # noqa: E402

NAME = ""                      # 写名字：NAME = "小明"
WISH = "愿所有美好，如期而至"
OUT = Path(__file__).with_name("birthday")
W, H = 720, 1280               # 逻辑像素，渲染 ×3 → 2160×3840

# ============================================================ 音乐时间轴（画面跟着它走）
BEAT = 0.56                    # 秒/拍，约 107 BPM
T_MUSIC = 2.2                  # 旋律开始；之前是蛋糕入场 + 点蜡烛
T_LIGHT = [1.0 + 0.22 * i for i in range(5)]       # 5 根蜡烛依次点亮，每根配一个琶音音符
LIGHT_NOTES = [72, 76, 79, 84, 88]                  # C5 E5 G5 C6 E6

# 《Happy Birthday to You》旋律（公有领域），C 大调，(MIDI 音高, 拍数)，3/4 拍
MELODY = [
    [(67, .75), (67, .25), (69, 1), (67, 1), (72, 1), (71, 2)],
    [(67, .75), (67, .25), (69, 1), (67, 1), (74, 1), (72, 2)],
    [(67, .75), (67, .25), (79, 1), (76, 1), (72, 1), (71, 1), (69, 2)],
    [(77, .75), (77, .25), (76, 1), (72, 1), (74, 1), (72, 3)],
]
# 低音伴奏：{句内音符序号: [MIDI...]}，C / G7 / F 三个和弦
BASS = [{2: [48, 55], 5: [43, 53]}, {2: [43, 53], 5: [48, 55]},
        {2: [48, 52], 6: [41, 48]}, {2: [48, 55], 4: [43, 53], 5: [36, 48, 52, 55]}]

NOTES = []                     # (onset 秒, midi, 拍数, 句号, 句内序号)
_t = T_MUSIC
for ph, phrase in enumerate(MELODY):
    for i, (m, b) in enumerate(phrase):
        NOTES.append((_t, m, b, ph, i))
        _t += b * BEAT
ONSETS = np.array([n[0] for n in NOTES])
PHRASE_T = [next(n[0] for n in NOTES if n[3] == ph) for ph in range(4)]
T_FINAL = NOTES[-1][0]                              # 最后一个长音
DURATION = round(T_FINAL + 3 * BEAT + 1.7, 2)       # 长音结束后再定格约 1.7s
TITLE_ON = [NOTES[i][0] for i in (0, 2, 3, 4)]      # 「生日快乐」跟第一句的 4 个音符弹出

# ============================================================ 配色
BG_TOP, BG_BOT = "#0b1026", "#2b1242"
GOLD, GOLD_LIGHT, GLOW = "#f6d27a", "#ffe6a8", "#ffb347"
INK2 = "#e9e3f5"
CONFETTI = ["#ff6b8b", "#ffd166", "#06d6a0", "#4cc9f0", "#c77dff", "#ffffff", "#ff9f1c"]

# ============================================================ 画布
fig, L = fv.canvas(w=W, h=H, bg=BG_TOP, ink=GOLD)
ax = fig.add_axes([0, 0, 1, 1])
# 背景渐变用 64 条矩形色带画（矢量填充）：全屏 imshow 在 4K 下每帧要多花约 0.6s；
# 相邻色带的颜色差不到 1 个 8-bit 色阶，看不出分层
_ys = np.linspace(0, H, 65)
_top, _bot = np.array(to_rgb(BG_TOP)), np.array(to_rgb(BG_BOT))
ax.add_collection(PolyCollection([[[0, _ys[i]], [W, _ys[i]], [W, _ys[i + 1] + 0.5], [0, _ys[i + 1] + 0.5]]
                                  for i in range(64)],
                                 facecolors=[_top + (_bot - _top) * (i + 0.5) / 64 for i in range(64)],
                                 edgecolors="none", zorder=0), autolim=False)
ax.set_xlim(0, W)
ax.set_ylim(H, 0)              # y 向下，和逻辑像素一致
ax.axis("off")

rng = np.random.default_rng(20261102)   # 固定种子：每次渲染完全一样

# ---- 背景星点（闪烁）
N_STAR = 70
STAR_XY = np.column_stack([rng.uniform(10, W - 10, N_STAR), rng.uniform(10, 640, N_STAR)])
STAR_S = rng.uniform(1.5, 7, N_STAR)
STAR_W, STAR_PH = rng.uniform(1.2, 3.5, N_STAR), rng.uniform(0, 2 * np.pi, N_STAR)
stars = ax.scatter(STAR_XY[:, 0], STAR_XY[:, 1], s=STAR_S, c="#ffffff", linewidths=0, zorder=0.5)

# ---- 散景光斑（缓慢上浮）
N_BOKEH = 16
BK_X, BK_Y0 = rng.uniform(0, W, N_BOKEH), rng.uniform(0, H, N_BOKEH)
BK_V = rng.uniform(6, 16, N_BOKEH)
BK_D = rng.uniform(50, 160, N_BOKEH) / 1.389          # 直径：逻辑像素 → pt
BK_C = np.array([to_rgb(c) for c in rng.choice(["#ff8fab", "#ffd166", "#b8a1ff", "#7fb4ff"], N_BOKEH)])
BK_A = rng.uniform(0.05, 0.12, N_BOKEH)
bokeh_outer = ax.scatter(BK_X, BK_Y0, s=BK_D**2, linewidths=0, zorder=1)
bokeh_inner = ax.scatter(BK_X, BK_Y0, s=(BK_D * 0.6) ** 2, linewidths=0, zorder=1)

# ---- 烛光暖光晕（径向渐变图）
GLOW_C, GLOW_R = (360, 690), 330
yy, xx = np.mgrid[-1:1:256j, -1:1:256j]
glow_rgba = np.zeros((256, 256, 4))
glow_rgba[..., :3] = to_rgb(GLOW)
glow_rgba[..., 3] = np.clip(1 - np.hypot(xx, yy), 0, 1) ** 2.2
glow_img = ax.imshow(glow_rgba, extent=[GLOW_C[0] - GLOW_R, GLOW_C[0] + GLOW_R,
                                        GLOW_C[1] + GLOW_R, GLOW_C[1] - GLOW_R],
                     interpolation="bilinear", zorder=2, alpha=0)

# ---- 蛋糕（静态部件共用一个平移变换，入场时整体上升）
cake_off = Affine2D()
CAKE_SCALE, CAKE_ANCHOR_Y = 1.18, 984   # 以盘子中心 (360, 1004) 为锚点放大，再放到 y=984
CAKE_TR = cake_off + ax.transData


def cake_add(artist, z):
    artist.set_transform(CAKE_TR)   # 先设变换再加入坐标轴，add_* 不会覆盖已设的变换
    artist.set_zorder(z)
    if isinstance(artist, Line2D):
        ax.add_line(artist)
    elif isinstance(artist, PolyCollection):
        ax.add_collection(artist, autolim=False)
    else:
        ax.add_patch(artist)
    return artist


def drips(x0, x1, ytop, n, base=12):
    xs = np.linspace(x0, x1, 160)
    d = np.full_like(xs, base)
    for c, dp, wd in zip(rng.uniform(x0 + 18, x1 - 18, n), rng.uniform(8, 26, n), rng.uniform(6, 11, n)):
        d += dp * np.exp(-2 * ((xs - c) / wd) ** 2)
    return np.vstack([[x0, ytop], np.column_stack([xs, ytop + d]), [x1, ytop]])


cake_add(Ellipse((360, 1004), 430, 44, fc="#cfd0e3", ec="none"), 3)                 # 盘子
cake_add(Ellipse((360, 998), 400, 30, fc="#e9e9f4", ec="none"), 3)
for (x, y, w, h, body, shade, ndrip) in [(200, 860, 320, 140, "#f4a7b9", "#e3879f", 8),
                                         (250, 760, 220, 104, "#fff1dc", "#f1dcbf", 6)]:
    cake_add(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=16",
                            fc=body, ec="none"), 3.1)
    cake_add(FancyBboxPatch((x, y + h - 26), w, 26, boxstyle="round,pad=0,rounding_size=14",
                            fc=shade, ec="none"), 3.2)                                     # 底部阴影
    cake_add(FancyBboxPatch((x + 10, y + 22), 10, h - 50, boxstyle="round,pad=0,rounding_size=5",
                            fc="#ffffff", ec="none", alpha=0.22), 3.2)                     # 左侧高光
    cake_add(Polygon(drips(x + 3, x + w - 3, y + 8, ndrip), closed=True, fc="#fffaf3", ec="none"), 3.3)
    cake_add(FancyBboxPatch((x, y), w, 20, boxstyle="round,pad=0,rounding_size=12",
                            fc="#fffaf3", ec="none"), 3.3)                                 # 奶油顶

# 糖针
N_SPR = 46
spr_c = np.column_stack([rng.uniform(222, 498, N_SPR), rng.uniform(912, 980, N_SPR)])
spr_a = rng.uniform(0, np.pi, N_SPR)
spr = []
for (cx, cy), a in zip(spr_c, spr_a):
    d = np.array([np.cos(a), np.sin(a)]) * 5
    n = np.array([-np.sin(a), np.cos(a)]) * 1.6
    spr.append([[cx, cy] - d - n, [cx, cy] + d - n, [cx, cy] + d + n, [cx, cy] - d + n])
cake_add(PolyCollection(spr, facecolors=rng.choice(CONFETTI[:5], N_SPR), edgecolors="none"), 3.25)

# 蜡烛
CANDLE_X = [290, 325, 360, 395, 430]
CANDLE_TOP, CANDLE_BOT = 708, 772
CANDLE_C = ["#8ec5ff", "#ffd36e", "#ff8fab", "#b8f2c9", "#c9b6ff"]
for x, c in zip(CANDLE_X, CANDLE_C):
    cake_add(FancyBboxPatch((x - 6, CANDLE_TOP), 12, CANDLE_BOT - CANDLE_TOP,
                            boxstyle="round,pad=0,rounding_size=3", fc=c, ec="none"), 3.4)
    for sy in range(CANDLE_TOP + 8, CANDLE_BOT - 8, 14):
        cake_add(Polygon([[x - 6, sy + 6], [x + 6, sy], [x + 6, sy + 4], [x - 6, sy + 10]],
                         closed=True, fc="#ffffff", ec="none", alpha=0.6), 3.45)           # 斜条纹
    cake_add(Line2D([x, x], [CANDLE_TOP, CANDLE_TOP - 8], color="#3a2e2a", lw=1.6), 3.5)  # 烛芯

# 火苗：泪滴曲线 x = sin u·sin(u/2), y = cos u（y=1 为尖端）
_u = np.linspace(0, 2 * np.pi, 60)
TEAR = np.column_stack([np.sin(_u) * np.sin(_u / 2), np.cos(_u)])
FLAME_LAYERS = [(9.0, 17.0, 0.0, "#ff9f1c", 0.95), (5.6, 11.0, 1.5, "#ffd56b", 1.0),
                (3.0, 6.0, 2.5, "#fffbe6", 1.0)]                 # (半宽, 半高, 底部上移, 颜色, 不透明度)
flames = [[ax.add_patch(Polygon(np.zeros((3, 2)), closed=True, fc=c, ec="none", alpha=a, zorder=5 + 0.1 * j))
           for j, (_, _, _, c, a) in enumerate(FLAME_LAYERS)] for _ in CANDLE_X]
HOT_R = 120                    # 烛火附近更亮的一小团暖光（径向渐变，边缘柔和）
hot_rgba = glow_rgba.copy()
hot_rgba[..., :3] = to_rgb("#ffcf70")
hot_rgba[..., 3] = np.clip(1 - np.hypot(xx, yy), 0, 1) ** 1.6
hot_img = ax.imshow(hot_rgba, extent=[0, 1, 1, 0], interpolation="bilinear", zorder=4.9, alpha=0)

# ---- 文字
TITLE_Y, SUB_Y, DIV_Y, WISH_Y = 300, 410, 456, 498
GLOW_FX = lambda a: [pe.withStroke(linewidth=lw, foreground="#ffcf70", alpha=al * a)  # noqa: E731
                     for lw, al in [(14, .035), (9, .05), (5, .07), (2.5, .10)]] + [pe.Normal()]  # 多层由宽到窄≈柔光
title_chars = [ax.text(360 + (i - 1.5) * 124, TITLE_Y, ch, fontsize=82, color=GOLD, ha="center",
                       va="center", fontfamily="Songti SC", fontweight=900, zorder=6, alpha=0)
               for i, ch in enumerate("生日快乐")]
subtitle = ax.text(360, SUB_Y, "Happy Birthday", fontsize=40, color=GOLD_LIGHT, ha="center",
                   va="center", fontfamily="Snell Roundhand", fontweight=700, zorder=6, alpha=0)
div_l = ax.plot([], [], color=GOLD, lw=1.0, zorder=6)[0]
div_r = ax.plot([], [], color=GOLD, lw=1.0, zorder=6)[0]
div_dot = ax.plot([360], [DIV_Y], marker="D", ms=4.5, color=GOLD, zorder=6, alpha=0)[0]
wish_lines = [f"亲爱的 {NAME}", WISH] if NAME else [WISH]
wishes = [ax.text(360, WISH_Y + 40 * i, s, fontsize=20, color=INK2, ha="center", va="center",
                  fontfamily="Songti SC", zorder=6, alpha=0) for i, s in enumerate(wish_lines)]

# ---- 闪光：每个音符一颗四角星
STAR4 = MPath([(0, 1), (.2, .2), (1, 0), (.2, -.2), (0, -1), (-.2, -.2), (-1, 0), (-.2, .2), (0, 1)], closed=True)
SP_XY = np.column_stack([rng.uniform(70, 650, len(NOTES)), rng.uniform(170, 560, len(NOTES))])
RING = np.column_stack([360 + 290 * np.cos(np.linspace(0, 2 * np.pi, 14, endpoint=False)),
                        TITLE_Y + 150 * np.sin(np.linspace(0, 2 * np.pi, 14, endpoint=False))])
SP_ALL = np.vstack([SP_XY, RING])
SP_T = np.concatenate([ONSETS, T_FINAL + np.linspace(0, 0.5, len(RING))])
SP_C = np.array([to_rgb(c) for c in rng.choice([GOLD_LIGHT, "#ffffff", "#ffd1dc"], len(SP_ALL))])
sparks = ax.scatter(SP_ALL[:, 0], SP_ALL[:, 1], marker=STAR4, s=np.zeros(len(SP_ALL)),
                    linewidths=0, zorder=7)


# ---- 彩纸：解析解（指数阻尼 + 终端速度），不做逐帧积分，任意 t 都能直接算
def burst(n, t0, x0, y0, vx, vy, k, vterm):
    return dict(t0=t0 + rng.uniform(0, 0.12, n), x0=x0, y0=y0, vx=vx, vy=vy, k=k, vterm=vterm,
                sway=rng.uniform(8, 30, n), swf=rng.uniform(2, 5, n), ph=rng.uniform(0, 2 * np.pi, n),
                w=rng.uniform(7, 12, n), h=rng.uniform(11, 18, n), th=rng.uniform(0, np.pi, n),
                spin=rng.uniform(-6, 6, n), flip=rng.uniform(5, 11, n),
                col=np.array([to_rgb(c) for c in rng.choice(CONFETTI, n)]))


N_CAN, N_RAIN = 75, 150
BURSTS = [
    burst(N_CAN, PHRASE_T[3], np.full(N_CAN, 20.0), np.full(N_CAN, 1300.0), rng.uniform(150, 650, N_CAN),
          rng.uniform(-2300, -1300, N_CAN), rng.uniform(1.8, 2.6, N_CAN), rng.uniform(140, 220, N_CAN)),
    burst(N_CAN, PHRASE_T[3], np.full(N_CAN, W - 20.0), np.full(N_CAN, 1300.0), -rng.uniform(150, 650, N_CAN),
          rng.uniform(-2300, -1300, N_CAN), rng.uniform(1.8, 2.6, N_CAN), rng.uniform(140, 220, N_CAN)),
    burst(N_RAIN, T_FINAL, rng.uniform(0, W, N_RAIN), rng.uniform(-450, -20, N_RAIN), rng.uniform(-40, 40, N_RAIN),
          rng.uniform(150, 230, N_RAIN), np.full(N_RAIN, 1.5), rng.uniform(150, 230, N_RAIN)),
]
confetti = ax.add_collection(PolyCollection([], edgecolors="none", zorder=8))


def confetti_verts(t):
    verts, cols = [], []
    for b in BURSTS:
        tau = t - b["t0"]
        on = tau > 0
        if not on.any():
            continue
        tau = np.where(on, tau, 0)
        e = 1 - np.exp(-b["k"] * tau)
        x = b["x0"] + b["vx"] * e / b["k"] + b["sway"] * np.sin(b["swf"] * tau + b["ph"]) * e
        y = b["y0"] + b["vterm"] * tau + (b["vy"] - b["vterm"]) * e / b["k"]
        fl = np.cos(b["flip"] * tau + b["ph"])
        hw = b["w"] / 2 * np.maximum(np.abs(fl), 0.15)
        hh = b["h"] / 2
        th = b["th"] + b["spin"] * tau
        c, s = np.cos(th), np.sin(th)
        corners = np.stack([np.stack([sx * hw * c - sy * hh * s, sx * hw * s + sy * hh * c], -1)
                            for sx, sy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]], 1)
        corners += np.stack([x, y], -1)[:, None, :]
        keep = on & (y < H + 40) & (y > -60) & (x > -40) & (x < W + 40)
        verts.append(corners[keep])
        cols.append(b["col"][keep] * (0.62 + 0.38 * np.abs(fl[keep]))[:, None])  # 翻面时变暗
    if not verts:
        return np.zeros((0, 4, 2)), np.zeros((0, 3))
    return np.concatenate(verts), np.concatenate(cols)


# ============================================================ 每一帧
def noise(t, seed):
    return (np.sin(5.3 * t + seed * 1.7) * 0.5 + np.sin(8.9 * t + seed * 2.9) * 0.3
            + np.sin(14.1 * t + seed * 4.1) * 0.2)


def frame(t):
    # 背景：星点闪烁、光斑上浮
    a = 0.25 + 0.45 * (0.5 + 0.5 * np.sin(STAR_W * t + STAR_PH))
    stars.set_facecolors(np.column_stack([np.ones((N_STAR, 3)), a]))
    by = (BK_Y0 - BK_V * t + 150) % (H + 300) - 150
    bokeh_outer.set_offsets(np.column_stack([BK_X, by]))
    bokeh_inner.set_offsets(np.column_stack([BK_X, by]))
    bokeh_outer.set_facecolors(np.column_stack([BK_C, BK_A * 0.5]))
    bokeh_inner.set_facecolors(np.column_stack([BK_C, BK_A]))

    # 蛋糕从底部升起
    dy = fv.interp(t, 0.1, 1.2, 460, 0, fv.ease_out_cubic)
    cake_off.clear().translate(-360, -1004).scale(CAKE_SCALE).translate(360, CAKE_ANCHOR_Y + dy)

    # 点蜡烛 + 火苗摇曳；音符起音时烛光脉动
    last = np.searchsorted(ONSETS, t, side="right") - 1
    pulse = 0.22 * np.exp(-(t - ONSETS[last]) / 0.25) if last >= 0 else 0.0
    scales = []
    for i, (x, layers) in enumerate(zip(CANDLE_X, flames)):
        s = fv.interp(t, T_LIGHT[i], T_LIGHT[i] + 0.3, 0, 1, fv.ease_out_back)
        scales.append(min(s, 1))
        hgt = s * (1 + 0.08 * noise(t, i))
        sway = 2.4 * noise(t * 1.3, i + 7) * s
        base = CANDLE_TOP - 6
        for (wx, hyy, up, _, _), poly in zip(FLAME_LAYERS, layers):
            yn = (TEAR[:, 1] + 1) / 2                       # 0 底部 → 1 尖端
            px = x + wx * s * TEAR[:, 0] + sway * yn**1.5
            py = base - up - hyy * hgt * (TEAR[:, 1] + 1)
            poly.set_xy(cake_off.transform(np.column_stack([px, py])))
    lit = np.mean(scales)
    gx, gy = cake_off.transform([[360, CANDLE_TOP - 22]])[0]   # 火苗那一排的中心
    glow_img.set_alpha(min(1.0, 0.55 * lit * (1 + pulse)))
    glow_img.set_extent([gx - GLOW_R, gx + GLOW_R, gy + GLOW_R, gy - GLOW_R])
    hot_img.set_alpha(min(1.0, 0.42 * lit * (1 + 0.8 * pulse + 0.06 * noise(t, 3))))
    hot_img.set_extent([gx - HOT_R, gx + HOT_R, gy + HOT_R * 0.8, gy - HOT_R * 0.8])

    # 标题逐字弹出（只做纵向位移，不缩放，免得相邻字互相压住）
    for txt, on in zip(title_chars, TITLE_ON):
        p = fv.progress(t, on, on + 0.5)
        al = fv.progress(t, on, on + 0.22)
        txt.set_y(TITLE_Y + 46 * (1 - fv.ease_out_back(p)))
        txt.set_alpha(al)
        txt.set_path_effects(GLOW_FX(al))

    # 第二句：Happy Birthday + 分隔线
    p2 = fv.progress(t, PHRASE_T[1], PHRASE_T[1] + 0.9, fv.ease_out_cubic)
    subtitle.set_y(SUB_Y + 24 * (1 - p2))
    subtitle.set_alpha(p2)
    subtitle.set_path_effects(GLOW_FX(p2 * 0.7))
    half = fv.interp(t, PHRASE_T[1] + 0.25, PHRASE_T[1] + 1.1, 0, 74, fv.ease_out_cubic)
    div_l.set_data([346 - half, 346], [DIV_Y, DIV_Y])
    div_r.set_data([374, 374 + half], [DIV_Y, DIV_Y])
    div_dot.set_alpha(fv.progress(t, PHRASE_T[1] + 0.25, PHRASE_T[1] + 0.6))

    # 第三句（唱名字的位置）：名字 / 祝福语
    for i, txt in enumerate(wishes):
        on = PHRASE_T[2] + 0.5 * i
        p3 = fv.progress(t, on, on + 0.9, fv.ease_out_cubic)
        txt.set_y(WISH_Y + 40 * i + 18 * (1 - p3))
        txt.set_alpha(p3)

    # 闪光：起音后 0.8s 内先放大后缩小
    age = (t - SP_T) / 0.8
    live = (age >= 0) & (age <= 1)
    sz = np.where(live, (22 * np.sin(np.pi * np.clip(age, 0, 1))) ** 2, 0)
    sparks.set_sizes(sz)
    sparks.set_facecolors(np.column_stack([SP_C, np.where(live, 1 - np.clip(age, 0, 1) ** 2, 0)]))

    # 彩纸
    v, c = confetti_verts(t)
    confetti.set_verts(v)
    confetti.set_facecolors(c)


# ============================================================ 音乐合成（音乐盒音色）
SR = 44100


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pluck(f, amp, length=2.8):
    t = np.arange(int(SR * length)) / SR
    tau = float(np.clip(0.9 * np.sqrt(523 / f), 0.35, 1.6))
    env = np.exp(-t / tau) * np.minimum(1, t / 0.003)
    y = (np.sin(2 * np.pi * f * t)
         + 0.30 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / (tau * 0.45))
         + 0.10 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t / (tau * 0.25))
         + 0.22 * np.sin(2 * np.pi * 4.95 * f * t) * np.exp(-t / 0.06))   # 金属簧片的高频「叮」
    return amp * env * y


def make_music(path):
    n = int(SR * DURATION)
    dry = np.zeros(n + SR * 3)

    def add(t0, m, amp):
        y = pluck(midi_hz(m), amp)
        i = int(t0 * SR)
        dry[i:i + len(y)] += y

    for t0, m in zip(T_LIGHT, LIGHT_NOTES):
        add(t0, m, 0.28)
    for (t0, m, b, ph, i) in NOTES:
        add(t0, m, 0.62 if (ph, i) == (3, 5) else 0.5)
        for bm in BASS[ph].get(i, []):
            add(t0, bm, 0.26)
    for j, m in enumerate([60, 64, 67, 72, 76, 79, 84]):     # 收尾琶音
        add(T_FINAL + 0.9 + 0.07 * j, m, 0.22)
    dry = dry[:n]

    # 简单混响：两条不相关的指数衰减噪声脉冲响应，左右声道各一条
    r = np.random.default_rng(7)
    ti = np.arange(int(SR * 1.6)) / SR
    size = 1 << int(np.ceil(np.log2(n + len(ti))))
    D = np.fft.rfft(dry, size)
    out = []
    for _ in range(2):
        ir = r.normal(size=len(ti)) * np.exp(-ti / 0.38)
        ir[:int(0.012 * SR)] = 0                              # 12ms 预延迟
        wet = np.fft.irfft(D * np.fft.rfft(ir, size), size)[:n]
        wet *= 0.32 * np.sqrt(np.mean(dry**2) / np.mean(wet**2))
        out.append(dry + wet)
    st = np.stack(out, 1)
    st *= np.minimum(1, np.arange(n) / (0.005 * SR))[:, None]
    fade = int(0.6 * SR)
    st[-fade:] *= np.linspace(1, 0, fade)[:, None]
    st *= 0.89 / np.max(np.abs(st))                           # 峰值 -1 dBFS
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((st * 32767).astype("<i2").tobytes())
    rms = 20 * np.log10(np.sqrt(np.mean(st**2)))
    print(f"[music] {DURATION}s，{len(NOTES)} 个旋律音，峰值 -1.0 dBFS，RMS {rms:.1f} dBFS")


if __name__ == "__main__":
    if "--preview" in sys.argv:
        fv.stills(fig, frame, [1.6, TITLE_ON[-1] + 0.6, PHRASE_T[2] + 1.6, DURATION - 0.02])
    else:
        wav = Path(tempfile.gettempdir()) / f"birthday_music_{os.getpid()}.wav"
        make_music(wav)
        try:
            fv.build(fig, frame, DURATION, out=OUT, audio=wav,
                     sheet_times=[1.6, TITLE_ON[-1] + 0.6, PHRASE_T[3] + 0.8, -0.05])
        finally:
            wav.unlink(missing_ok=True)
