function [t,y]=exp1_impulse(t1,t2,dt,t0)
% 单位冲激信号函数
% t1,t2,dt 分别为起始时间、终止时间和时间间隔，t0 为冲激点
% 函数调用格式：[t,y]=exp1_impulse(-10,10,0.1,0);
t=t1:dt:t2;                 % 时间范围
y=(abs(t-t0)<dt/2);         % 只在 t0 处取 1，用误差限代替 t==t0，避免浮点误差
plot(t,y,'LineWidth',1.5);  % 连续信号用 plot
grid on
axis([t1 t2 -0.2 1.2]);     % 留出上下边距
xlabel('t')                 % X 轴坐标
ylabel('\delta(t-t_0)')     % Y 轴坐标
title(['单位冲激信号，冲激点 t_0 = ',num2str(t0)])
end
