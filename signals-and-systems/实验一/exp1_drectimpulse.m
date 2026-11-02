function [n,y]=exp1_drectimpulse(k1,k2,k0,width,E)
% 矩形序列函数
% k1,k2 分别为起始时间、终止时间，默认时间间隔为 1
% E 为矩形脉冲幅值，width 为矩形脉冲宽度
% k0 为矩形脉冲上升沿跳变点，非零区间为 [k0, k0+width]
% 函数调用格式：[n,y]=exp1_drectimpulse(-10,10,3,2,3);
n=k1:k2;                             % 序号范围
y=E*((n>=k0)&(n<=k0+width));         % 区间内为 E，区间外为 0
stem(n,y,'filled');
grid on
axis([k1-1 k2+1 -0.1*E 1.2*E]);
xlabel('n')
ylabel('f(n)')
title(['矩形序列，幅值 ',num2str(E),'，脉宽 ',num2str(width), ...
       '，中心 ',num2str(k0+width/2)])
end
