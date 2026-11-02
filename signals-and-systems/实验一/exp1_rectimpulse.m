function [t,y]=exp1_rectimpulse(E,width,T1,T2,dt,T0)
% 矩形脉冲信号函数
% E 为矩形脉冲幅度，width 为矩形脉冲宽度
% T1,T2,dt 分别为起始时间、终止时间和时间间隔
% T0 为脉冲上升沿跳变点，脉冲占据区间 [T0, T0+width]
% 函数调用格式：[t,y]=exp1_rectimpulse(5,1,-10,10,0.01,2);
t=T1:dt:T2;                          % 时间范围
y=E*((t>=T0)&(t<=T0+width));         % 区间内为 E，区间外为 0
plot(t,y,'LineWidth',1.5);
grid on
axis([T1 T2 -0.1*E 1.2*E]);
xlabel('t')
ylabel('f(t)')
title(['矩形脉冲信号，幅值 ',num2str(E),'，脉宽 ',num2str(width), ...
       '，中心 ',num2str(T0+width/2)])
end
