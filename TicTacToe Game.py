# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 19:48:48 2021

@author: WSY
"""

import random
import math
import time
import pygame
import numpy as np
import pickle # 保存/读取字典

# 读取Q表格
with open('Q_table_dict.pkl', 'rb') as f:
    Q_table_pkl = pickle.load(f)

###########################################################
######################### 通用函数 #########################
def str2tuple(string): # Input: '(1,1)'
    string2list = list(string)
    return ( int(string2list[1]), int(string2list[4]) ) # Output: (1,1)


###########################################################
######################### 游戏状态 #########################
class Game():
    def __init__(self):
        self.state = np.zeros([3,3])
        self.first = None
        self.currentMove = None
        self.winner = None
    
    def switchMove(self): # 切换行动玩家
        move = self.currentMove
        if move == 'blue': self.currentMove = 'red'
        elif move == 'red': self.currentMove = 'blue'
    
    
    def newGame(self): # 新建游戏
        self.state = np.zeros([3,3])
        self.first = 'blue' if random.random() > 0.5 else 'red'
        self.currentMove = self.first
        self.winner = None
    
    def step(self, action_):
        # 动作的格式：action = {'mark':'circle'/'cross', 'pos':(x,y)} # 产生状态
        x = action_['pos'][0]
        y = action_['pos'][1]
        if action_['mark'] == 'blue':  
            self.state[x][y] = 1
        elif action_['mark'] == 'red': 
            self.state[x][y] = -1
    
    def judgeEnd(self):
        # 检查两对角
        check_diag_1 = self.state[0][0] + self.state[1][1] + self.state[2][2]
        check_diag_2 = self.state[2][0] + self.state[1][1] + self.state[0][2]
        if check_diag_1 == 3 or check_diag_2 == 3:
            self.winner = 'blue'
            return True
        elif check_diag_1 == -3 or check_diag_2 == -3:
            self.winner = 'red'
            return True
        # 检查三行三列
        state_T = self.state.T
        for i in range(3):
            check_row = sum(self.state[i]) # 检查行
            check_col = sum(state_T[i]) # 检查列
            if check_row == 3 or check_col == 3:
                self.winner = 'blue'
                return True
            elif check_row == -3 or check_col == -3:
                self.winner = 'red'
                return True
        # 检查整个棋盘是否还有空位
        empty = []
        for i in range(3):
            for j in range(3):
                if self.state[i][j] == 0: empty.append((i,j))
        if empty == []: return True
        
        return False
   

###########################################################
######################### 决策类 ##########################                 
class Agent():
    def __init__(self):
        self.Q_table = Q_table_pkl
        self.EPSILON = 0 # 试探几率
    
    def getEmptyPos(self, state_): # 返回空位的坐标
        action_space = []
        for i, row in enumerate(state_):
            for j, one in enumerate(row):
                if one == 0: action_space.append((i,j)) 
        return action_space
    
    def randomAction(self, state_, mark): # 随机选择空格动作
        actions = self.getEmptyPos(state_)
        action_pos = random.choice(actions)
        action = {'mark':mark, 'pos':action_pos}
        return action
    
    def overTurn(self, state_): # 翻转状态
        state_tf = state_.copy()
        for i, row in enumerate(state_tf):
            for j, one in enumerate(row):
                if one != 0: state_tf[i][j] *= -1
        return state_tf
    
    def epsilon_greedy(self, state_, currentMove): # ε-贪心策略
        state = state_.copy() if currentMove == 'blue' else self.overTurn(state_) # 如果是红方行动则翻转状态
        Q_Sa = self.Q_table[str(state)]
        maxAction, maxValue, otherAction = [], -100, [] 
        for one in Q_Sa:
            if Q_Sa[one] > maxValue:
                maxValue = Q_Sa[one]
        for one in Q_Sa:
            if Q_Sa[one] == maxValue:
                maxAction.append(str2tuple(one))
            else:
                otherAction.append(str2tuple(one))
        try:
            action_pos = random.choice(maxAction) if random.random() > self.EPSILON else random.choice(otherAction)
        except: # 处理从空的otherAction中取值的情况
            action_pos = random.choice(maxAction) 
        action = {'mark':currentMove, 'pos':action_pos}
        return action
    
                                                   
###########################################################
######################### 用户界面 #########################
class UserInterface():
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((1100,580)) # 设置游戏窗口大小
        pygame.display.set_caption('Tic-tac-toe') # 设置游戏窗口名称
        
        self.running = True # 运行状态
        self.clock = pygame.time.Clock() # 帧数控制
        self.time = time.time() # 行动间隔控制
        
        # 其他类的引入
        self.game = Game()
        self.agent = Agent()
        
        # 选中对象
        self.pick_player1 = None
        self.pick_player2 = None
        self.isCheat = False  
        self.human_pick = None
        
        # 颜色类
        self.GrassGreen = (226,240,217) # 草绿  
        self.DarkKhaki = (189,183,107) # 深卡其布
        self.LightBlue = (0,176,240) # 浅蓝
        self.Pink = (235,179,235) # 粉红
        self.Black = (59,56,56) # 黑色
        self.Red = (255,104,76) # 胡萝卜红
        
        # 常用属性类
        self.BGCOLOR = self.GrassGreen # 背景色
        self.INTERVAL = 0.5 # 行动间隔
        self.FPS = 40 # 帧数
        self.SIZE_L = 150 # 游戏内常用尺寸(地图块 物品块等)
        self.SIZE_M = 80
        self.SIZE_S = 25
        
        # 字体类
        self.font = pygame.font.Font('texture/arialbd.ttf', self.SIZE_S)
        self.font1 = pygame.font.Font('texture/BD_Cartoon_Shout.ttf', 20)
        self.font2 = pygame.font.Font('texture/arialbd.ttf', 20)
        
        # 图片类
        self.img_circle = pygame.image.load('texture/circle.png').convert_alpha() # convert_alpha() 加载图片去黑边
        self.img_circle = pygame.transform.smoothscale(self.img_circle, (self.SIZE_M, self.SIZE_M))
        self.img_cross = pygame.image.load('texture/cross.png').convert_alpha()
        self.img_cross = pygame.transform.smoothscale(self.img_cross, (self.SIZE_M, self.SIZE_M))
        self.img_pick = pygame.image.load('texture/pick.png').convert_alpha()
        self.img_pick = pygame.transform.smoothscale(self.img_pick, (35, 35))
        
        # 文字类
        self.player1_text = self.font1.render('PLAYER1', True, self.LightBlue) # True: 抗锯齿
        self.player2_text = self.font1.render('PLAYER2', True, self.Pink)
        self.Q_text = self.font.render('Q', True, self.Black)
        self.random_text = self.font.render('random', True, self.Black)
        self.human_text = self.font.render('human', True, self.Black)
        self.start_text = self.font1.render('START', True, self.Red)
        self.cheat_text = self.font.render('CHEAT', True, self.Black)
    
    # 更新胜负平率
    def updateRate(self):
        if self.Q_vs_Q != 0:
            self.Q_vs_Q_win_rate = self.Q_vs_Q_win / self.Q_vs_Q
            self.Q_vs_Q_draw_rate = self.Q_vs_Q_draw / self.Q_vs_Q
            self.Q_vs_Q_lose_rate = self.Q_vs_Q_lose / self.Q_vs_Q
        if self.Q_vs_random != 0:
            self.Q_vs_random_win_rate = self.Q_vs_random_win / self.Q_vs_random
            self.Q_vs_random_draw_rate = self.Q_vs_random_draw / self.Q_vs_random
            self.Q_vs_random_lose_rate = self.Q_vs_random_lose / self.Q_vs_random
        if self.Q_vs_human != 0:
            self.Q_vs_human_win_rate = self.Q_vs_human_win / self.Q_vs_human
            self.Q_vs_human_draw_rate = self.Q_vs_human_draw / self.Q_vs_human
            self.Q_vs_human_lose_rate = self.Q_vs_human_lose / self.Q_vs_human
        if self.human_vs_random != 0:
            self.human_vs_random_win_rate = self.human_vs_random_win / self.human_vs_random
            self.human_vs_random_draw_rate = self.human_vs_random_draw / self.human_vs_random
            self.human_vs_random_lose_rate = self.human_vs_random_lose / self.human_vs_random
    
    # 开始一局游戏
    def startGame(self):
        if self.pick_player1 is None or self.pick_player2 is None:
            return
        self.game.newGame()
    
    # 玩家1行动
    def player1Move(self):
        if self.pick_player1 == 'Q':
            action = self.agent.epsilon_greedy(self.game.state, self.game.currentMove)
            self.game.step(action)
            self.game.switchMove()
            self.time = time.time()
            
        elif self.pick_player1 == 'random':
            action = self.agent.randomAction(self.game.state, self.game.currentMove)
            self.game.step(action)
            self.game.switchMove()
            self.time = time.time()
            
        elif self.pick_player1 == 'human':
            if self.human_pick is None:
                return
            x, y = self.human_pick
            if self.game.state[x][y] == 0:
                action = {'mark':self.game.currentMove, 'pos':self.human_pick}
                self.game.step(action)
                self.game.switchMove()
                self.time = time.time()
        
    # 玩家2行动
    def player2Move(self):
        if self.pick_player2 == 'Q':
            action = self.agent.epsilon_greedy(self.game.state, self.game.currentMove)
        elif self.pick_player2 == 'random':
            action = self.agent.randomAction(self.game.state, self.game.currentMove)
        self.game.step(action)
        self.game.switchMove()
        self.time = time.time()
        
    
    # 玩家输入
    def processInput(self):
        for event in pygame.event.get():
            # 按下右上角的游戏退出键
            if event.type == pygame.QUIT:
                self.running = False
                break
            elif event.type == pygame.MOUSEBUTTONDOWN: # 按下鼠标  
                x, y = pygame.mouse.get_pos()            
                if event.button == 1: # 按下鼠标左键
                    print(x, ' ', y)
                    # 是否作弊
                    if 600 <= x <= 675 and 180 <= y <= 200: 
                        temp = self.isCheat
                        self.isCheat = True if temp is False else False
                    # 选择player1
                    if 740 <= x <= 760 and 55 <= y <= 70:
                        self.pick_player1 = 'Q'
                    elif 800 <= x <= 890 and 55 <= y <= 70:
                        self.pick_player1 = 'random'
                    elif 940 <= x <= 1020 and 55 <= y <= 70:
                        self.pick_player1 = 'human'
                    # 选择player2
                    if 740 <= x <= 760 and 105 <= y <= 120:
                        self.pick_player2 = 'Q'
                    elif 800 <= x <= 890 and 105 <= y <= 120:
                        self.pick_player2 = 'random'
                    # 开始游戏
                    if 940 <= x <= 1025 and 105 <= y <= 120:
                        self.startGame()
                        self.human_pick = None
                    # 选择井字格
                    if 50 <= x <= 500 and 50 <= y <= 500:
                        if self.pick_player1 == 'human' and self.game.currentMove == 'blue':
                            row = math.floor((x - 50)/self.SIZE_L)
                            col = math.floor((y - 50)/self.SIZE_L)
                            self.human_pick = (row, col)
                            print(self.human_pick)
                        
                        
    # 更新界面状态 
    def update(self):
        if self.game.judgeEnd():
            if time.time() - self.time > self.INTERVAL:
                self.human_pick = None
        else:
            if self.game.currentMove == 'blue' and time.time() - self.time > self.INTERVAL:
                self.player1Move()
                return
            if self.game.currentMove == 'red' and time.time() - self.time > self.INTERVAL:
                self.player2Move()
                return
    
    # 更新显示
    def render(self):
        # 填充背景色
        self.window.fill(self.BGCOLOR)
        
        # 显示分隔线
        for i in range(4):
            pygame.draw.line(self.window, self.DarkKhaki, (50, 50 + i * self.SIZE_L), (50 + 3 * self.SIZE_L, 50 + i * self.SIZE_L), 8)
            pygame.draw.line(self.window, self.DarkKhaki, (50 + i * self.SIZE_L, 50 + 3 * self.SIZE_L), (50 + i * self.SIZE_L, 50), 8)
            
        # 显示图片
        for i, row in enumerate(self.game.state):
            for j, one in enumerate(row):
                if one == 1: self.window.blit(self.img_circle, ( 85 + i * self.SIZE_L, 85 + j * self.SIZE_L) )
                if one == -1: self.window.blit(self.img_cross, ( 85 + i * self.SIZE_L, 85 + j * self.SIZE_L) )
        
        # 显示信息面板
        # player1
        self.window.blit(self.player1_text, (600,55))
        self.window.blit(self.Q_text,(740,50))
        self.window.blit(self.random_text, (800,50))
        self.window.blit(self.human_text, (940,50))
        if self.pick_player1 == 'Q':
            self.window.blit(self.img_pick, (740,60))
        elif self.pick_player1 == 'random':
            self.window.blit(self.img_pick, (800,60))
        elif self.pick_player1 == 'human':
            self.window.blit(self.img_pick, (940,60))
        # player2
        self.window.blit(self.player2_text, (600,105))
        self.window.blit(self.Q_text,(740,100))
        self.window.blit(self.random_text, (800,100))
        self.window.blit(self.start_text, (940,105))
        if self.pick_player2 == 'Q':
            self.window.blit(self.img_pick, (740,110))
        elif self.pick_player2 == 'random':
            self.window.blit(self.img_pick, (800,110))

        # 显示作弊
        self.window.blit(self.cheat_text, (600,180))
        if self.isCheat:
            self.window.blit(self.img_pick, (600,190))
            for i in range(4):
                pygame.draw.line(self.window, self.Black, (740, 180 + i * self.SIZE_M), (740 + 3 * self.SIZE_M, 180 + i * self.SIZE_M), 2)
                pygame.draw.line(self.window, self.Black, (740 + i * self.SIZE_M, 180 + 3 * self.SIZE_M), (740 + i * self.SIZE_M, 180), 2)
            if self.game.currentMove == 'blue':
                try:
                    Q_Sa = self.agent.Q_table[str(self.game.state)]
                    for action in Q_Sa:
                        i, j = str2tuple(action)
                        value = round(Q_Sa[action],3)
                        text = self.font2.render(str(value), True, self.Black)
                        self.window.blit(text, (750 + i * self.SIZE_M, 205 + j * self.SIZE_M))
                except:
                    pass
        
        # pygame刷新显示
        pygame.display.update() 
    
    # 主循环
    def run(self):
        while self.running:
            self.processInput()
            self.update()
            self.render()
            self.clock.tick(self.FPS)


###########################################################
userInterface = UserInterface()
userInterface.run()
pygame.quit()