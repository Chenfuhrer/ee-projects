function [n,y]=exp1_dexp(c,a,k1,k2)
% 指数序列函数
% c: 指数序列的幅度
% a: 指数序列的底数
% k1:绘制序列的起始序号
% k2:绘制序列的终止序号
% 函数调用格式：[n,y]=exp1_dexp(1,2,-2,10);
n=k1:k2;                    % 序号范围
y=c*a.^n;                   % 指数序列 y(n)=c*a^n，注意用点乘方 .^
stem(n,y,'filled');
grid on
xlim([k1-1 k2+1]);
xlabel('n')
ylabel('y(n)')
title(['指数序列 y(n) = ',num2str(c),'\times',num2str(a),'^n'])
end
