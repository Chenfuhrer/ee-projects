"""把照片处理成木板激光雕刻用的图。

用法:
  python3 make_engrave.py source.webp
  python3 make_engrave.py source.webp --bust 505,140,1075,800   # 另出半身像（原图像素坐标）

输出:
  01_照片雕刻_灰度.png    导入 LightBurn 后选 Jarvis 抖动
  02_照片雕刻_抖动预览.png  Floyd-Steinberg 抖动，看大致效果
  03_线稿.png             DoG 自动线稿，适合刻线 / 快速雕刻
  半身_01/02/03_*.png     同上，半身裁剪，放大 2 倍，底边和左边渐隐
"""
import argparse

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
from skimage import color, exposure, filters, measure, morphology, restoration


def segment(rgb):
    """抠图：草地是绿色，人身上没有绿色。"""
    hsv = color.rgb2hsv(rgb)
    h, s = hsv[..., 0] * 360, hsv[..., 1]
    grass = (h > 45) & (h < 150) & (s > 0.18)
    person = morphology.opening(~grass, morphology.disk(3))
    person = morphology.closing(person, morphology.disk(5))
    lab = measure.label(person)
    person = lab == max(measure.regionprops(lab), key=lambda r: r.area).label
    # 只补小洞（衣服褶皱里的噪点），发丝和脖子之间露出的草地保留为背景
    person = morphology.remove_small_holes(person, max_size=400)
    return morphology.opening(person, morphology.disk(2))


def to_gray(rgb, person, alpha):
    """灰度 + 轻度对比度增强。木头会把中间调烧得偏深，所以整体提亮一点。"""
    g = color.rgb2gray(rgb)
    lo, hi = np.percentile(g[person], [1, 99.5])
    gray = np.clip((g - lo) / (hi - lo), 0, 1)
    gray = exposure.equalize_adapthist(gray, clip_limit=0.004, kernel_size=128)  # clip 太大脸会脏
    gray = gray ** 0.75
    return gray * alpha + 1.0 * (1 - alpha)  # 背景 = 白 = 不烧


def to_line(rgb, person):
    """线稿：先去纹理，再取 DoG 边缘（只要线，不要大块黑，否则裤子会烧成一整片）。"""
    gd = restoration.denoise_tv_chambolle(color.rgb2gray(rgb), weight=0.04)
    edge = (filters.gaussian(gd, 1.6) - filters.gaussian(gd, 0.9)) > 0.007
    lab = measure.label(gd < 0.12)
    pupils = np.isin(lab, [r.label for r in measure.regionprops(lab) if r.area < 250])  # 小块深色 = 瞳孔
    line = (edge | pupils) & ndi.binary_dilation(person, iterations=2)  # 只留人物范围
    line |= person ^ morphology.erosion(person, morphology.disk(1))  # 外轮廓
    return morphology.remove_small_objects(line, max_size=30)


def edge_fade(h, w, bottom=0.22, left=0.08):
    """底边和左边渐隐到白，避免裁剪处在木板上留下一条硬边。"""
    def smooth(t):
        t = np.clip(t, 0, 1)
        return t * t * (3 - 2 * t)
    y = np.arange(h)[:, None]
    x = np.arange(w)[None, :]
    return smooth((h - 1 - y) / (bottom * h)) * smooth(x / (left * w))


def export(gray, line, prefix, scale=1):
    g8 = Image.fromarray((np.clip(gray, 0, 1) * 255).astype(np.uint8))
    l8 = Image.fromarray(np.where(line, 0, 255).astype(np.uint8))
    if scale != 1:
        # 插值放大只是让边缘更顺，不会凭空多出细节
        size = (g8.width * scale, g8.height * scale)
        g8 = g8.resize(size, Image.LANCZOS)
        l8 = l8.resize(size, Image.LANCZOS).point(lambda v: 0 if v < 128 else 255)
    g8 = g8.filter(ImageFilter.UnsharpMask(radius=1.5 * scale, percent=50, threshold=3))
    g8.save(f"{prefix}01_照片雕刻_灰度.png", dpi=(300, 300))
    g8.convert("1").save(f"{prefix}02_照片雕刻_抖动预览.png", dpi=(300, 300))
    l8.save(f"{prefix}03_线稿.png", dpi=(300, 300))
    print(f"{prefix or '全身'}: {g8.width}x{g8.height}px，按 300 DPI ≈ "
          f"{g8.width / 300 * 25.4:.0f}x{g8.height / 300 * 25.4:.0f} mm")


ap = argparse.ArgumentParser()
ap.add_argument("src", nargs="?", default="source.webp")
ap.add_argument("--bust", help="半身裁剪框 x0,y0,x1,y1（原图像素坐标）")
args = ap.parse_args()

rgb = np.asarray(Image.open(args.src).convert("RGB")) / 255.0
person = segment(rgb)
line = to_line(rgb, person)

# 全身：裁到人物外框，四周留白
y0, x0, y1, x1 = measure.regionprops(person.astype(int))[0].bbox
pad = 30
y0, x0 = max(y0 - pad, 0), max(x0 - pad, 0)
y1, x1 = min(y1 + pad, rgb.shape[0]), min(x1 + pad, rgb.shape[1])
crop = (slice(y0, y1), slice(x0, x1))
alpha = filters.gaussian(person[crop].astype(float), sigma=1.2)  # 边缘羽化
export(to_gray(rgb[crop], person[crop], alpha), line[crop], "")

if args.bust:
    bx0, by0, bx1, by1 = map(int, args.bust.split(","))
    crop = (slice(by0, by1), slice(bx0, bx1))
    fade = edge_fade(by1 - by0, bx1 - bx0)
    alpha = filters.gaussian(person[crop].astype(float), sigma=1.2) * fade
    export(to_gray(rgb[crop], person[crop], alpha), line[crop] & (fade > 0.4), "半身_", scale=2)
