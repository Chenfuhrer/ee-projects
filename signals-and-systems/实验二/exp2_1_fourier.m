% 实验二 1 傅里叶正变换和逆变换
clear; clc;
% 1) 求 f(t)=E[u(t-tau/2)-u(t+tau/2)] 的傅里叶正变换 F(w)
syms t w
syms E tau positive                 % 幅度 E、宽度 tau 均为正数
f  = E*(heaviside(t-tau/2) - heaviside(t+tau/2));
Fw = simplify(fourier(f, t, w))     % 傅里叶正变换

% 对照：标准门函数 g(t)=E[u(t+tau/2)-u(t-tau/2)] 的傅里叶变换
g  = E*(heaviside(t+tau/2) - heaviside(t-tau/2));
Gw = simplify(fourier(g, t, w))

% 2) 求 F(w)=delta(w-w0) 的傅里叶逆变换 f(t)
syms w0 real
F2 = dirac(w - w0);
f2 = ifourier(F2, w, t)             % 傅里叶逆变换
