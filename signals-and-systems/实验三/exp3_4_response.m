% 实验三 4 零输入响应、零状态响应和全响应
clear; clc; close all;

%% 1) 连续系统 H(s)=(s+5)/(s^2+3s+2)，e(t)=3u(t)，y(0)=1，y'(0)=2
% 对应微分方程 y''+3y'+2y = e'+5e
syms t s
syms y(t)
Dy = diff(y, t);
yzi = dsolve(diff(y,t,2) + 3*Dy + 2*y == 0, [y(0) == 1, Dy(0) == 2]);  % 零输入响应
yzi = simplify(yzi)
Hs  = (s+5)/(s^2+3*s+2);
yzs = simplify(ilaplace(Hs*3/s, s, t))      % 零状态响应：L^-1[H(s)E(s)]，E(s)=3/s
yfull = simplify(yzi + yzs)                 % 全响应

% 数值验证零状态响应：lsim 计算 3u(t) 输入下的响应
tn  = 0:0.01:8;
yzs_num = lsim(tf([1 5],[1 3 2]), 3*ones(size(tn)), tn);
fprintf('零状态响应 lsim 与解析解最大误差：%.2e\n', ...
        max(abs(yzs_num.' - double(subs(yzs, t, tn)))));

figure('Position',[100 100 700 450]);
plot(tn, double(subs(yzi, t, tn)), 'LineWidth', 1.5); hold on;
plot(tn, double(subs(yzs, t, tn)), 'LineWidth', 1.5);
plot(tn, double(subs(yfull, t, tn)), 'k--', 'LineWidth', 1.5); hold off; grid on;
xlabel('t (s)'); ylabel('y(t)');
legend('零输入响应 y_{zi}(t)', '零状态响应 y_{zs}(t)', '全响应 y(t)', 'Location', 'east');
title('连续系统的零输入、零状态和全响应');
exportgraphics(gcf,'fig/4_1_continuous.png','Resolution',200);

%% 2) 离散系统 y(n+2)+3y(n+1)+2y(n)=x(n)，x(n)=0.2^n u(n)，y(0)=2，y(1)=1
% 令 w(k)=y(k+2)，方程变为 w(k)+3w(k-1)+2w(k-2)=x(k)，初始状态 w(-1)=y(1)，w(-2)=y(0)
N  = 11;                                     % 计算 n=0~10
k  = 0:N-3;                                  % w(k) 对应 y(2)~y(10)
xk = 0.2.^k;
b = 1; a = [1 3 2];
zi_zi = filtic(b, a, [1 2]);                 % 初始状态 [w(-1) w(-2)] = [y(1) y(0)]
w_zi  = filter(b, a, zeros(size(k)), zi_zi); % 零输入：输入为 0，只有初始状态
w_zs  = filter(b, a, xk);                    % 零状态：初始状态为 0
yzi_d = [2 1 w_zi];                          % 拼上 y(0)、y(1)
yzs_d = [0 0 w_zs];                          % 零状态时 y(0)=y(1)=0
yfu_d = yzi_d + yzs_d;                       % 全响应

% 解析解：z 域推导结果
nn = 0:N-1;
yzi_a = 5*(-1).^nn - 3*(-2).^nn;
yzs_a = 25/66*0.2.^nn - 5/6*(-1).^nn + 5/11*(-2).^nn;
fprintf('零输入 filter 与解析解最大误差：%.2e\n', max(abs(yzi_d - yzi_a)));
fprintf('零状态 filter 与解析解最大误差：%.2e\n', max(abs(yzs_d - yzs_a)));
fprintf('%4s %10s %10s %10s\n', 'n', '零输入', '零状态', '全响应');
fprintf('%4d %10.4f %10.4f %10.4f\n', [nn; yzi_d; yzs_d; yfu_d]);

figure('Position',[100 100 700 650]);
subplot(3,1,1); stem(nn, yzi_d, 'filled'); grid on; ylabel('y_{zi}(n)'); title('零输入响应');
subplot(3,1,2); stem(nn, yzs_d, 'filled'); grid on; ylabel('y_{zs}(n)'); title('零状态响应');
subplot(3,1,3); stem(nn, yfu_d, 'filled'); grid on; ylabel('y(n)'); xlabel('n'); title('全响应');
exportgraphics(gcf,'fig/4_2_discrete.png','Resolution',200);
