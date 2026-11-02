function [t,y]=exp1_sin(t1,t2,dt,A,w)
% 正弦信号函数
% t1,t2,dt 分别为起始时间、终止时间和时间间隔
% A,w 为正弦信号的幅度和角频率
% 函数调用格式：[t,y]=exp1_sin(-10,10,0.1,10,1);
t=t1:dt:t2;                 % 时间范围
y=A*sin(w*t);               % 正弦信号
plot(t,y,'LineWidth',1.5);
grid on
axis([t1 t2 -1.2*A 1.2*A]);
xlabel('t')
ylabel('f(t)')
title(['正弦信号 f(t) = ',num2str(A),'sin(',num2str(w),'t)'])
end
