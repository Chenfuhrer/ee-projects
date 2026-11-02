% 实验一 主程序：依次调用各自编函数并保存图像
% X 取学号最后三位 050，即 X = 50
clear; clc; close all;
X = 50;
if ~exist('fig','dir'), mkdir('fig'); end

% 1.1 单位冲激信号：冲激点在 t=50，时间范围取 45~55
figure; [t,y]=exp1_impulse(45,55,0.01,50);
exportgraphics(gcf,'fig/1_1_impulse.png','Resolution',200);

% 1.2 单位阶跃信号：跳变点在 t=50，时间范围取 40~60
figure; [t,y]=exp1_step(40,60,0.01,50);
exportgraphics(gcf,'fig/1_2_step.png','Resolution',200);

% 1.3 矩形脉冲信号：幅值 50，脉宽 2，中心 50，所以上升沿在 49
figure; [t,y]=exp1_rectimpulse(50,2,45,55,0.01,49);
exportgraphics(gcf,'fig/1_3_rect.png','Resolution',200);

% 1.4 正弦信号：幅值 50，角频率 2，时间范围 -10~10
figure; [t,y]=exp1_sin(-10,10,0.01,50,2);
exportgraphics(gcf,'fig/1_4_sin.png','Resolution',200);

% 2.1 单位冲激序列：冲激点在 n=50，序号范围 40~60
figure; [n,y]=exp1_dimpluse(40,60,1,50);
exportgraphics(gcf,'fig/2_1_dimpulse.png','Resolution',200);

% 2.2 矩形序列：幅值 50，脉宽 2，中心 50，所以上升沿在 49
figure; [n,y]=exp1_drectimpulse(40,60,49,2,50);
exportgraphics(gcf,'fig/2_2_drect.png','Resolution',200);

% 2.3 指数序列：底数 50，幅度 1，序号范围 -2~4
figure; subplot(2,1,1); [n,y]=exp1_dexp(1,50,-2,4);
subplot(2,1,2); stem(n,y,'filled'); set(gca,'YScale','log'); grid on;
xlim([-3 5]); xlabel('n'); ylabel('y(n)（对数坐标）'); title('同一序列的对数纵坐标显示');
exportgraphics(gcf,'fig/2_3_dexp.png','Resolution',200);
disp('2.3 指数序列取值：'); disp([n; y]);

% 2.4 正弦序列：幅值 50，角频率 2，序号范围 -20~20
figure; [n,y]=exp1_dsin(50,2,-20,20);
exportgraphics(gcf,'fig/2_4_dsin.png','Resolution',200);
