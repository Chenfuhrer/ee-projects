# ee-projects

电子信息专业的小项目合集：硬件打样、课程实验代码、数据动画和一些小工具。

| 目录 | 内容 |
|---|---|
| [`hardware/tlv5638-da-module`](hardware/tlv5638-da-module) | TLV5638 双路 12 位 DAC 模块 PCB（嘉立创 EDA），两版生产文件 |
| [`signals-and-systems`](signals-and-systems) | 《信号与系统》MATLAB 实验一至三 |
| [`frame-video`](frame-video) | matplotlib 逐帧渲染 + ffmpeg 合成的 4K/60fps 动画 |
| [`laser-engrave`](laser-engrave) | 照片转木板激光雕刻图的脚本 |

## hardware/tlv5638-da-module

基于 TI TLV5638（SOIC-8，SPI 接口双路 12 位 DAC）的小模块，元件全部来自立创商城（LCSC），可以直接在嘉立创下单打样和 SMT 贴片。

| 版本 | 日期 | 区别 |
|---|---|---|
| `v1-vertical-header` | 2026-10-24 | 直插排针（PZ254V） |
| `v2-right-angle-header` | 2026-11-01 | 排针改为弯针（PZ254R），R9 由 49.9Ω 改为 0Ω |

每个版本目录里有 `Gerber_*.zip`（制板）、`BOM_*`（物料清单）、`PickAndPlace_*`（贴片坐标）和 PCB 预览图。

**待补**：原理图 PDF、实测数据（输出范围、INL/DNL、建立时间）。

## signals-and-systems

《信号与系统》课程实验的 MATLAB 代码，每个实验目录里 `fig/` 是运行结果图，`out/` 是命令行输出。

- **实验一** 常用信号：自己写冲激、阶跃、矩形脉冲、正弦（连续）和对应的离散序列函数，`exp1_main.m` 依次调用并出图
- **实验二** 傅里叶变换与频域分析：符号法求傅里叶正/逆变换、频谱分析、连续和离散系统冲激响应、`freqs` 求频率特性
- **实验三** 复频域分析：拉普拉斯变换、Z 变换、阶跃响应、零输入/零状态/全响应

实验二、三可以用 `exp2_runall.m` / `exp3_runall.m` 一次跑完。需要 Symbolic Math Toolbox。

## frame-video

用 matplotlib 逐帧渲染、ffmpeg 合成高清视频，`fv.py` 是公共工具库（预览图、合成 4K + 1080p 60fps、成片自检、清理中间帧）。

- `optimizer-demo/`：SGD、Momentum、AdaGrad、Adam 四种优化器在 f(x, y) = x²/20 + y² 上的轨迹对比（《深度学习入门》第 6 章的例子）
- `birthday/`：竖屏 9:16 生日贺卡动画，背景音乐是代码合成的音乐盒版《Happy Birthday to You》；改脚本里的 `NAME` 就能换名字

```bash
pip install numpy matplotlib   # 另需安装 ffmpeg
python3 optimizer_demo.py --preview   # 先出低清预览图看版面
python3 optimizer_demo.py             # 渲染成片
```

成片 mp4 体积较大，没有放进仓库，运行脚本即可生成。

## laser-engrave

把一张照片处理成木板激光雕刻用的三种图：灰度图（导入 LightBurn 后选 Jarvis 抖动）、Floyd-Steinberg 抖动预览、DoG 自动线稿；可选再出一套半身裁剪版。

```bash
pip install numpy pillow scipy scikit-image
python3 make_engrave.py 你的照片.jpg
python3 make_engrave.py 你的照片.jpg --bust 505,140,1075,800   # 半身裁剪框（原图像素坐标）
```
