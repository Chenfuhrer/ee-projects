% 实验三 3 连续系统和离散系统的阶跃响应
clear; clc; close all;

% (1) 连续系统 H(s)=s/(s^2+5s+6) 的阶跃响应 g(t)
b = [1 0]; a = [1 5 6];                  % 系数按 s 的降幂排列
tn = 0:0.01:5;                           % 指定时间域
g = step(b, a, tn);                      % 数值阶跃响应
syms s t
gt = ilaplace((s/(s^2+5*s+6))/s, s, t)   % 解析解 g(t)=L^-1[H(s)/s]
figure;
plot(tn, g, 'LineWidth', 1.5); hold on;
plot(tn, double(subs(gt, t, tn)), 'r--', 'LineWidth', 1.2); hold off; grid on;
xlabel('t (s)'); ylabel('g(t)');
legend('step 数值解', '解析解 e^{-2t}-e^{-3t}');
title('连续系统 H(s)=s/(s^2+5s+6) 的阶跃响应');
exportgraphics(gcf,'fig/3_1_step.png','Resolution',200);

% (2) 离散系统 H(z)=z/(z^2-3z+2) 的阶跃响应 g(n)
% dstep 的系数按 z^-1 的升幂排列：H(z)=z^-1/(1-3z^-1+2z^-2)
B = [0 1 0]; A = [1 -3 2];
N = 11;                                  % 观察 n=0~10
gn = dstep(B, A, N);
syms z n
gz = simplify(iztrans(z/(z^2-3*z+2) * z/(z-1), z, n))   % 解析解：H(z) 乘阶跃的 Z 变换 z/(z-1)
figure;
stem(0:N-1, gn, 'filled'); grid on;
xlabel('n'); ylabel('g(n)');
title('离散系统 H(z)=z/(z^2-3z+2) 的阶跃响应');
exportgraphics(gcf,'fig/3_2_dstep.png','Resolution',200);
fprintf('dstep 结果 g(0)~g(5)：'); disp(gn(1:6).');
fprintf('解析解   g(0)~g(5)：'); disp(double(subs(gz, n, 0:5)));
