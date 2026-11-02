% 实验二 4 连续时间系统的频率特性：H(s)=(2s+1)/(s^2+2s+3)
clear; clc; close all;
b = [2 1];                   % 分子系数
a = [1 2 3];                 % 分母系数
w = linspace(0, 10, 1000);   % 频率范围 0~10 rad/s
h = freqs(b, a, w);          % 频率响应
figure('Position',[100 100 700 600]);
subplot(2,1,1);
plot(w, abs(h), 'LineWidth', 1.5); grid on;
xlabel('\omega (rad/s)'); ylabel('|H(j\omega)|');
title('幅频特性');
subplot(2,1,2);
plot(w, angle(h)*180/pi, 'LineWidth', 1.5); grid on;
xlabel('\omega (rad/s)'); ylabel('相位 (°)');
title('相频特性');
exportgraphics(gcf,'fig/4_freqs.png','Resolution',200);
[hm, k] = max(abs(h));
fprintf('|H| 最大值 %.4f，出现在 w = %.3f rad/s；|H(j0)| = %.4f\n', hm, w(k), abs(h(1)));
