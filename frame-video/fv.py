"""frame-video 工具库：matplotlib 逐帧渲染 → ffmpeg 合成 → 自检 → 清理中间帧。

在动画脚本里：
    import sys; from pathlib import Path
    sys.path.insert(0, str(Path.home() / ".claude/skills/frame-video/scripts"))
    import fv

    fig, L = fv.canvas()                    # 版面按 1280×720 逻辑像素写
    ...                                     # 静态元素只建一次
    def frame(t): ...                       # 只由 t 决定画面：更新 artist 数据，不新建
    fv.stills(fig, frame, [0, 2.5, 4.9])    # 先出低清预览图看版面
    fv.build(fig, frame, duration=5, out="path/stem")   # 4K+1080p MP4、自检、删帧

命令行：
    python3 fv.py qa VIDEO.mp4 [--times 0.2,2.5,-0.1]       # 参数/硬解/抽帧拼图
    python3 fv.py encode FRAMES_DIR --fps 60 --out STEM [--audio A] [--gif]
    python3 fv.py mux VIDEO.mp4 AUDIO OUT.mp4                # 给成片配音频，不重编码视频
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

W, H, DPI = 1280, 720, 100
FONTS = ["PingFang SC", "Hiragino Sans GB", "Source Han Sans CN", "Arial Unicode MS"]


# ============================================================ 时间与插值
def linear(x):
    return x


def smoothstep(x):
    return x * x * (3 - 2 * x)


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def ease_in_out_cubic(x):
    return 4 * x**3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_back(x, s=1.70158):
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def progress(t, t0, t1, ease=linear):
    """t 在 [t0, t1] 内映射到 0→1（两端 clamp），再过 easing。"""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return ease(min(max((t - t0) / (t1 - t0), 0.0), 1.0))


def interp(t, t0, t1, a=0.0, b=1.0, ease=linear):
    """Remotion interpolate() 的等价物：t0→t1 期间从 a 过渡到 b，区间外保持端点值。
    a、b 可以是数、数组或 RGB 元组。"""
    p = progress(t, t0, t1, ease)
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    out = a + (b - a) * p
    return float(out) if out.ndim == 0 else out


def reveal(points, k):
    """折线逐步出现：完整取前 floor(k)+1 个点，再按小数部分插值出半段，动画才连续。
    points: (N, D) 数组；k: 0…N-1 的浮点进度。"""
    points = np.asarray(points, dtype=float)
    i = int(math.floor(k))
    if i >= len(points) - 1:
        return points
    if i < 0:
        return points[:1]
    tip = points[i] + (k - i) * (points[i + 1] - points[i])
    return np.vstack([points[: i + 1], tip])


def repel(ys, gap, lo=-np.inf, hi=np.inf):
    """一维标签去重叠：相邻至少隔 gap，并整体限制在 [lo, hi] 内。
    先自下而上推开，再把顶端压到 hi 以下自上而下回推（单向推会把标签推出坐标区）。"""
    ys = np.asarray(ys, dtype=float)
    order = np.argsort(ys, kind="stable")
    v = ys[order].copy()
    v[0] = max(v[0], lo)
    for i in range(1, len(v)):
        v[i] = max(v[i], v[i - 1] + gap)
    v[-1] = min(v[-1], hi)
    for i in range(len(v) - 2, -1, -1):
        v[i] = min(v[i], v[i + 1] - gap)
    out = np.empty_like(v)
    out[order] = v
    return out


# ============================================================ 画布与版面
class Layout:
    """逻辑像素（左上角为原点）→ figure 坐标。版面永远按 w×h 写，渲染倍率另算。"""

    def __init__(self, w, h):
        self.w, self.h = w, h

    def rect(self, x, y, w, h):
        return [x / self.w, 1 - (y + h) / self.h, w / self.w, h / self.h]

    def xy(self, x, y):
        return x / self.w, 1 - y / self.h


def canvas(w=W, h=H, bg="#1a1a19", ink="#f0efec", fonts=FONTS):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": list(fonts),
        "axes.unicode_minus": False,
        "text.color": ink,
    })
    fig = plt.figure(figsize=(w / DPI, h / DPI), dpi=DPI, facecolor=bg)
    return fig, Layout(w, h)


# ============================================================ 版面自检：文字碰撞 / 越界
def _drawn_texts(fig):
    """当前这一帧真正画出来的非空文字（刻度标签只算实际绘制的那些）。"""
    from matplotlib.text import Text

    tick_labels, drawn_ticks = set(), []
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            for tick in axis.get_major_ticks() + axis.get_minor_ticks():
                tick_labels.update({id(tick.label1), id(tick.label2)})
            if not (ax.axison and axis.get_visible()):  # axis("off") 时刻度标签根本不画
                continue
            try:
                ticks = axis._update_ticks()  # 私有 API：返回本次实际绘制的刻度
            except Exception:
                ticks = []
            for tick in ticks:
                for lab in (tick.label1, tick.label2):
                    if lab.get_visible():
                        drawn_ticks.append(lab)
    texts = [a for a in fig.findobj(Text) if id(a) not in tick_labels] + drawn_ticks
    return [a for a in texts
            if a.get_visible() and a.get_text().strip() and (a.get_alpha() is None or a.get_alpha() > 0)]


def text_issues(fig, frame_fn, times, pad=1.0):
    """在若干时间点检查文字压文字、文字越出画面。返回问题列表（空 = 通过）。"""
    issues = []
    fig.canvas.draw()
    for t in times:
        frame_fn(t)
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        fb = fig.bbox
        boxes = []
        for a in _drawn_texts(fig):
            bb = a.get_window_extent(r)
            if bb.width <= 0 or bb.height <= 0:
                continue
            boxes.append((a, bb))
            if bb.x0 < fb.x0 - pad or bb.x1 > fb.x1 + pad or bb.y0 < fb.y0 - pad or bb.y1 > fb.y1 + pad:
                issues.append({"t": round(t, 3), "kind": "越界", "a": a.get_text()})
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                (a, ba), (b, bb) = boxes[i], boxes[j]
                ox = min(ba.x1, bb.x1) - max(ba.x0, bb.x0)
                oy = min(ba.y1, bb.y1) - max(ba.y0, bb.y0)
                if ox > pad and oy > pad:
                    issues.append({"t": round(t, 3), "kind": "压字", "a": a.get_text(), "b": b.get_text()})
    return issues


# ============================================================ 预览与渲染
def _sheet(images, labels, out_png, cols=None, width=1600):
    """把若干 PIL 图拼成联系表；时间标签放在每格上方的标题条里，不遮挡画面。
    cols 默认按画幅自动选：横屏 2 列，竖屏 4 列（否则竖屏拼图会拉得很长）。"""
    from PIL import Image, ImageDraw

    if cols is None:
        cols = min(len(images), 2 if images[0].width >= images[0].height else 4)
    cell_w, bar, gap = width // cols, 20, 4
    ims = [im.convert("RGB").resize((cell_w, round(im.height * cell_w / im.width)), Image.LANCZOS)
           for im in images]
    cell_h = ims[0].height + bar + gap
    rows = math.ceil(len(ims) / cols)
    sheet = Image.new("RGB", (cell_w * cols, cell_h * rows), "#000000")
    draw = ImageDraw.Draw(sheet)
    for n, (im, lab) in enumerate(zip(ims, labels)):
        x, y = (n % cols) * cell_w, (n // cols) * cell_h
        draw.text((x + 6, y + 4), lab, fill="#ffffff")
        sheet.paste(im, (x, y + bar))
    sheet.save(out_png)
    return out_png


def stills(fig, frame_fn, times, out_png=None):
    """低清（1×）预览若干时间点，拼成一张图，用于全量渲染前检查版面和节奏。"""
    from PIL import Image

    images = []
    for t in times:
        frame_fn(t)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=DPI, facecolor=fig.get_facecolor())
        buf.seek(0)
        images.append(Image.open(buf))
    out_png = out_png or os.path.join(tempfile.gettempdir(), f"fv_stills_{os.getpid()}.png")
    _sheet(images, [f"t={t:g}s" for t in times], out_png)
    print(f"[fv] 预览图 → {out_png}")
    return out_png


def render(fig, frame_fn, duration, fps=60, scale=3, frames_dir=None):
    """逐帧渲染 PNG。默认写到带 PID 的临时目录（并发安全），返回 (目录, 耗时秒)。"""
    w, h = round(fig.get_figwidth() * DPI * scale), round(fig.get_figheight() * DPI * scale)
    if w % 2 or h % 2:
        raise ValueError(f"渲染尺寸 {w}×{h} 含奇数，H.264 yuv420p 要求宽高为偶数")
    d = Path(frames_dir) if frames_dir else Path(tempfile.mkdtemp(prefix=f"fv_{os.getpid()}_"))
    d.mkdir(parents=True, exist_ok=True)
    n = round(duration * fps)
    t0 = time.time()
    for i in range(n):
        frame_fn(i / fps)
        fig.savefig(d / f"{i:05d}.png", dpi=DPI * scale, facecolor=fig.get_facecolor(),
                    pil_kwargs={"compress_level": 1})
        if (i + 1) % max(1, n // 10) == 0:
            print(f"[fv] 渲染 {i + 1}/{n}", flush=True)
    return d, time.time() - t0


# ============================================================ 编码
def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"命令失败：{' '.join(map(str, cmd))}\n{p.stderr[-2000:]}")
    return p


def _level(w, h):
    # x264 遇到 4K60 + preset slow 会自动标 Level 6.0，苹果硬解只到 5.2，必须手动压住
    return "5.2" if max(w, h) > 1920 else "4.2"


def encode(frames_dir, out, fps=60, audio=None, gif=False, half=True, crf=14):
    """PNG 序列 → 原分辨率 MP4（+ 半分辨率 MP4，+ GIF）。返回输出路径列表。"""
    from PIL import Image

    frames_dir = Path(frames_dir)
    pattern = str(frames_dir / "%05d.png")
    w, h = Image.open(frames_dir / "00000.png").size
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    common = ["-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-crf", str(crf),
              "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    targets = [(w, h)]
    if half:
        targets.append((w // 4 * 2, h // 4 * 2))  # 一半且保持偶数；相当于 2×2 超采样抗锯齿
    outputs = []
    for tw, th in targets:
        dst = out.with_name(f"{out.name}_{min(tw, th)}p.mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern]
        if audio:
            cmd += ["-i", str(audio)]
        if (tw, th) != (w, h):
            cmd += ["-vf", f"scale={tw}:{th}:flags=lanczos"]
        cmd += common + ["-level:v", _level(tw, th)]
        if audio:
            cmd += ["-af", "apad", "-c:a", "aac", "-b:a", "192k", "-shortest"]  # 音频短了补静音
        _run(cmd + [str(dst)])
        outputs.append(dst)
    if gif:
        dst = out.with_name(f"{out.name}.gif")
        pal = frames_dir / "palette.png"
        vf = "fps=15,scale=960:-1:flags=lanczos"
        _run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern,
              "-vf", f"{vf},palettegen=stats_mode=diff", str(pal)])
        _run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern, "-i", str(pal),
              "-lavfi", f"{vf}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle",
              str(dst)])
        outputs.append(dst)
    return outputs


def mux(video, audio, out):
    """给已有 MP4 配音频：视频流直接拷贝，音频转 AAC；音频短了补静音，时长以视频为准。"""
    _run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
          "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "apad", "-c:a", "aac", "-b:a", "192k",
          "-shortest", "-movflags", "+faststart", str(out)])
    return Path(out)


# ============================================================ 成片自检
def probe(video):
    p = _run(["ffprobe", "-v", "error", "-show_entries",
              "stream=codec_type,codec_name,profile,level,width,height,r_frame_rate,nb_frames,pix_fmt",
              "-show_entries", "format=duration,size", "-of", "json", str(video)])
    d = json.loads(p.stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    return {
        "file": Path(video).name, "w": v["width"], "h": v["height"],
        "fps": v["r_frame_rate"], "frames": int(v.get("nb_frames", 0)),
        "level": v.get("level", 0) / 10, "pix_fmt": v.get("pix_fmt"),
        "audio": any(s["codec_type"] == "audio" for s in d["streams"]),
        "duration": round(float(d["format"]["duration"]), 3),
        "size_kb": round(int(d["format"]["size"]) / 1024),
    }


def hw_decode_ok(video):
    """macOS 上用 VideoToolbox 硬解整片：能过基本说明 QuickTime/Safari 能放。非 macOS 返回 None。"""
    if platform.system() != "Darwin":
        return None
    p = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-hwaccel", "videotoolbox",
                        "-hwaccel_output_format", "videotoolbox_vld", "-i", str(video), "-f", "null", "-"],
                       capture_output=True, text=True)
    return p.returncode == 0 and not p.stderr.strip()


def psnr(frames_dir, video, fps):
    """成片 vs 源帧的 PSNR（dB），亮度/色度分开报：色度明显偏低 = 彩色细线被 yuv420p 糊了。"""
    v = probe(video)
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-framerate", str(fps), "-i", str(Path(frames_dir) / "%05d.png"),
         "-i", str(video), "-lavfi",
         f"[0:v]scale={v['w']}:{v['h']}:flags=lanczos,format=yuv444p[a];[1:v]format=yuv444p[b];[a][b]psnr",
         "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"PSNR y:([\d.inf]+) u:([\d.inf]+) v:([\d.inf]+)", p.stderr)
    return {"y": float(m[1]), "u": float(m[2]), "v": float(m[3])} if m else None


def sheet_from_video(video, times, out_png=None):
    """从成片里按时间抽帧拼图（负数 = 距结尾），检查的是编码后的真实画面。"""
    from PIL import Image

    tmp = Path(tempfile.mkdtemp(prefix=f"fv_sheet_{os.getpid()}_"))
    images = []
    for n, t in enumerate(times):
        dst = tmp / f"{n}.png"
        seek = ["-sseof", str(t)] if t < 0 else ["-ss", str(t)]
        _run(["ffmpeg", "-y", "-loglevel", "error", *seek, "-i", str(video), "-frames:v", "1", str(dst)])
        images.append(Image.open(dst))
    out_png = out_png or os.path.join(tempfile.gettempdir(), f"fv_sheet_{os.getpid()}.png")
    _sheet(images, [f"t={t:g}s" for t in times], out_png)
    shutil.rmtree(tmp, ignore_errors=True)
    return out_png


def qa(video, times=None):
    info = probe(video)
    info["hw_decode"] = hw_decode_ok(video)
    d = info["duration"]
    info["sheet"] = sheet_from_video(video, times or [0.1, round(d / 3, 2), round(2 * d / 3, 2), -0.05])
    return info


# ============================================================ 一条龙
def build(fig, frame_fn, duration, out, fps=60, scale=3, audio=None, gif=False,
          check_step=0.25, strict=True, keep_frames=False, sheet_times=None):
    """版面自检 → 渲染 → 编码 → 成片自检 → 删中间帧 → 打印报告。返回报告 dict。"""
    times = list(np.arange(0, duration, check_step)) + [duration - 1 / fps]
    issues = text_issues(fig, frame_fn, times)
    if issues:
        print(f"[fv] 版面自检发现 {len(issues)} 处问题（前 10 条）：")
        for it in issues[:10]:
            print("   ", it)
        if strict:
            raise SystemExit("[fv] 先修版面再渲染；确认可接受时传 strict=False")
    else:
        print(f"[fv] 版面自检通过：{len(times)} 个时间点无压字/越界")

    frames_dir, secs = render(fig, frame_fn, duration, fps=fps, scale=scale)
    print(f"[fv] 渲染完成 {round(duration * fps)} 帧，用时 {secs:.1f}s")
    outputs = encode(frames_dir, out, fps=fps, audio=audio, gif=gif)
    report = {"render_seconds": round(secs, 1), "text_issues": len(issues), "outputs": []}
    for o in outputs:
        if o.suffix == ".gif":
            report["outputs"].append({"file": o.name, "size_kb": round(o.stat().st_size / 1024)})
            continue
        info = probe(o)
        info["hw_decode"] = hw_decode_ok(o)
        info["psnr"] = psnr(frames_dir, o, fps)
        report["outputs"].append(info)
    report["sheet"] = sheet_from_video(outputs[0], sheet_times or
                                       [0.1, round(duration / 3, 2), round(2 * duration / 3, 2), -0.05])
    if keep_frames:
        report["frames_dir"] = str(frames_dir)
    else:
        shutil.rmtree(frames_dir, ignore_errors=True)

    print("\n| 文件 | 分辨率 | fps | Level | 大小 | 硬解 | PSNR Y/U/V (dB) |")
    print("|---|---|---|---|---|---|---|")
    for o in report["outputs"]:
        if "w" not in o:
            print(f"| {o['file']} | GIF 960 宽 15fps | | | {o['size_kb']} KB | | |")
            continue
        p = o["psnr"]
        ps = f"{p['y']:.1f} / {p['u']:.1f} / {p['v']:.1f}" if p else "—"
        hw = {True: "✓", False: "✗", None: "—"}[o["hw_decode"]]
        print(f"| {o['file']} | {o['w']}×{o['h']} | {o['fps']} | {o['level']:.1f} | {o['size_kb']} KB | {hw} | {ps} |")
    print(f"\n[fv] 抽帧拼图 → {report['sheet']}（用 Read 看）")
    return report


# ============================================================ CLI
def _main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("qa")
    q.add_argument("video")
    q.add_argument("--times", help="逗号分隔的秒数，负数表示距结尾")
    e = sub.add_parser("encode")
    e.add_argument("frames_dir")
    e.add_argument("--out", required=True)
    e.add_argument("--fps", type=int, default=60)
    e.add_argument("--audio")
    e.add_argument("--gif", action="store_true")
    m = sub.add_parser("mux")
    m.add_argument("video")
    m.add_argument("audio")
    m.add_argument("out")
    a = ap.parse_args()
    if a.cmd == "qa":
        times = [float(x) for x in a.times.split(",")] if a.times else None
        print(json.dumps(qa(a.video, times), ensure_ascii=False, indent=2))
    elif a.cmd == "encode":
        for o in encode(a.frames_dir, a.out, fps=a.fps, audio=a.audio, gif=a.gif):
            print(o)
    elif a.cmd == "mux":
        print(mux(a.video, a.audio, a.out))


if __name__ == "__main__":
    _main()
