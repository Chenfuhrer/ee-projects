function [t,y]=exp1_step(t1,t2,dt,t0)
% 单位阶跃信号函数
% t1,t2,dt 分别为起始时间、终止时间和时间间隔，t0 为阶跃跳变点
% 函数调用格式：[t,y]=exp1_step(-10,10,0.1,3);
t=t1:dt:t2;                 % 时间范围
y=(t>=t0);                  % t>=t0 时为 1，否则为 0
plot(t,y,'LineWidth',1.5);
grid on
axis([t1 t2 -0.2 1.2]);
xlabel('t')
ylabel('u(t-t_0)')
title(['单位阶跃信号，跳变点 t_0 = ',num2str(t0)])
end
