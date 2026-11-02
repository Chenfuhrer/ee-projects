% 实验三 1 连续信号的拉普拉斯正变换和逆变换
clear; clc;
syms t s
% 1) f(t)=t*u(t-2) 的拉氏正变换
f1 = t*heaviside(t-2);
F1 = simplify(laplace(f1, t, s))
% 2) F(s)=10(s+2)(s+5)/[s(s+1)(s+3)] 的拉氏逆变换
F2 = 10*(s+2)*(s+5)/(s*(s+1)*(s+3));
f2 = ilaplace(F2, s, t)
% 用部分分式展开验证：residue 给出各极点的留数
[r, p, k] = residue(10*conv([1 2],[1 5]), conv([1 0], conv([1 1],[1 3])))
