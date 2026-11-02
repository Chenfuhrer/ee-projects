function [n,y]=exp1_dsin(A,wn,k1,k2)
% 正弦序列函数
% k1,k2 分别为起始时间、终止时间，默认时间间隔为 1；
% A,wn 为幅度和角频率参数
% 函数调用格式：[n,y]=exp1_dsin(5,0.25,-30,30);
n=k1:k2;                    % 序号范围
y=A*sin(wn*n);              % 正弦序列
stem(n,y,'filled');
grid on
axis([k1-1 k2+1 -1.2*A 1.2*A]);
xlabel('n')
ylabel('y(n)')
title(['正弦序列 y(n) = ',num2str(A),'sin(',num2str(wn),'n)'])
end
