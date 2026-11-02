% 实验二 2 频谱分析：x(t)=e^(-a t) sin(b*pi*t) u(t)，a=2，b=2
clear; clc; close all;
syms t w
a = 2; b = 2;
x  = exp(-a*t)*sin(b*pi*t)*heaviside(t);   % 正弦衰减信号
Xw = simplify(fourier(x, t, w))            % 频谱表达式 X(w)

figure('Position',[100 100 700 600]);
subplot(2,1,1);                            % 时域波形
fplot(x, [-0.5 3], 'LineWidth', 1.5); grid on;
xlabel('t'); ylabel('x(t)');
title('正弦衰减信号 x(t) = e^{-2t}sin(2\pi t)u(t)');

subplot(2,1,2);                            % 幅频特性 |X(w)|
fplot(abs(Xw), [-40 40], 'LineWidth', 1.5); grid on;
xlabel('\omega (rad/s)'); ylabel('|X(\omega)|');
title('幅频特性 |X(\omega)|');
exportgraphics(gcf,'fig/2_spectrum.png','Resolution',200);

% 峰值位置检查：理论峰值在 w=sqrt((b*pi)^2-a^2)≈5.96 处
ww = linspace(0,40,4001);
Xa = double(subs(abs(Xw), w, ww));
[pk, k] = max(Xa);
fprintf('幅频峰值 %.4f，出现在 w = %.2f rad/s\n', pk, ww(k));
fprintf('理论峰值位置 sqrt((b*pi)^2-a^2) = %.2f rad/s\n', sqrt((b*pi)^2-a^2));
