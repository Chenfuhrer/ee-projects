% 实验二 3 连续和离散时间系统的冲激响应
clear; clc; close all;

% 1) 连续系统 H(s)=(s+2)/(s^2+5s+3) 的冲激响应
num = [1 2];                 % 分子多项式系数（s 的降幂）
den = [1 5 3];               % 分母多项式系数
[Y,X,T] = impulse(num, den); % 冲激响应
figure;
plot(T, Y, 'LineWidth', 1.5); grid on;
xlabel('t (s)'); ylabel('h(t)');
title('连续系统 H(s)=(s+2)/(s^2+5s+3) 的冲激响应');
exportgraphics(gcf,'fig/3_1_impulse.png','Resolution',200);
fprintf('连续系统极点：'); disp(roots(den).');

% 2) 离散系统 H(z)=(5z^2+3z+3)/(z^2-2z+0.8) 的单位脉冲响应
b = [5 3 3];                 % 分子系数
a = [1 -2 0.8];              % 分母系数
N = 20;                      % 观察 0~19 共 20 个点
h = dimpulse(b, a, N);       % 单位脉冲响应
figure;
stem(0:N-1, h, 'filled'); grid on;
xlabel('n'); ylabel('h(n)');
title('离散系统 H(z)=(5z^2+3z+3)/(z^2-2z+0.8) 的单位脉冲响应');
exportgraphics(gcf,'fig/3_2_dimpulse.png','Resolution',200);
fprintf('离散系统极点：'); disp(roots(a).');
fprintf('h(0)~h(4) = '); disp(h(1:5).');
