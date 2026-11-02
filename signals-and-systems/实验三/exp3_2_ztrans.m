% 实验三 2 离散信号的 Z 变换和 Z 反变换
clear; clc;
syms n z
% 1) f(n)=1 的 Z 变换
F1 = ztrans(sym(1), n, z)
% 2) X(z)=z^2/(z^2-1.5z+0.5) 的 Z 反变换
X2 = z^2/(z^2 - 1.5*z + 0.5);
x2 = simplify(iztrans(X2, z, n))
% 验证：用长除法（filter 递推）求前 6 项，与公式结果比较
b = [1 0 0]; a = [1 -1.5 0.5];          % X(z)=1/(1-1.5z^-1+0.5z^-2)
xd = filter(b, a, [1 zeros(1,5)])        % 长除法得到的 x(0)~x(5)
xf = double(subs(x2, n, 0:5))            % 公式计算的 x(0)~x(5)
