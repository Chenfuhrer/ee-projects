function [n,y]=exp1_dimpluse(k1,k2,dt,k0)
% 单位冲激序列函数
% k1,k2,dt 分别为起始时间、终止时间和时间间隔，dt 要求为整数
% k0 为冲激点
% 函数调用格式：[n,y]=exp1_dimpluse(-10,10,1,0);
n=k1:dt:k2;                 % 序号范围
y=(n==k0);                  % 只在 n=k0 处为 1（整数比较，不存在浮点误差）
stem(n,y,'filled');         % 离散信号用 stem
grid on
axis([k1-1 k2+1 -0.2 1.2]);
xlabel('n')
ylabel('\delta(n-k_0)')
title(['单位冲激序列，冲激点 k_0 = ',num2str(k0)])
end
