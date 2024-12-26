import os
from os import makedirs
import sys
from time import time
from datetime import datetime, timedelta, timezone

import cv2
import gym
from gym import spaces
import numpy as np
import pygame as pg

cwd = os.path.dirname(__file__)
sys.path.append(os.path.join(cwd))

from source import setup, tools
from source import constants as c
from source.states import main_menu, load_screen, level


class PSMEnv(gym.Env):
    def __init__(self, level_name='level_1'):
        super(PSMEnv, self).__init__()
        self.action_space = spaces.Discrete(14)
        self.observation_space = spaces.Box(0, 255, (240, 256, 3), dtype=np.uint8)
        self.reward_range = (-15, 15)
        self.game = tools.Control()
        self.state_dict = {c.MAIN_MENU: main_menu.Menu(),
                        c.LOAD_SCREEN: load_screen.LoadScreen(),
                        c.LEVEL: level.Level(),
                        c.GAME_OVER: load_screen.GameOver(),
                        c.TIME_OUT: load_screen.TimeOut()}
        self.key_list = (pg.K_LEFT, pg.K_DOWN, pg.K_RIGHT, pg.K_s, pg.K_a)
        self.action_list = ((0, 0, 0, 0, 0), (1, 0, 0, 0, 0), (0, 1, 0, 0, 0),
                            (0, 0, 1, 0, 0), (0, 0, 0, 1, 0), (0, 0, 0, 0, 1),
                            (1, 0, 0, 1, 0), (0, 0, 1, 1, 0), (1, 0, 0, 0, 1),
                            (0, 1, 0, 0, 1), (0, 0, 1, 0, 1), (1, 0, 0, 1, 1),
                            (0, 0, 1, 1, 1), (0, 0, 0, 1, 1))
        self.level_name = level_name
        self.reset()
    
    def reset(self):
        self.game.setup_states(self.state_dict, c.LEVEL)
        self.game.state.done = False
        persist = self.state_dict[c.MAIN_MENU].persist
        self.game.state.startup(pg.time.get_ticks(), persist, self.level_name)
        # self.rendering = False
        self.game.keys = [0]*5
        self.game.update()
        self.output_screen = np.array(pg.surfarray.pixels3d(self.game.state.screen))
        self.output_screen = self.output_screen.transpose(1,0,2)
        player = self.game.state.player
        self.info = {'x': player.rect.x, 'y': player.rect.y, 'vx': player.x_vel, 'vy': player.y_vel,
                     'time': self.game.state.overhead_info.time, 'dead':self.game.state.player.dead,
                     'info': self.game.state.game_info}
        self.total_reward = 0
        return self.output_screen

    def render(self, mode='human'):
        if mode == 'human':
            self.rendering = True
            screen_expand = pg.transform.scale(self.game.state.screen, c.SCREEN_SIZE)
            self.game.screen.blit(screen_expand, (0,0))
            pg.display.update()
        elif mode == 'rgb_array':
            # screen_expand = pg.transform.scale(self.game.state.screen, c.SCREEN_SIZE)
            # self.game.screen.blit(screen_expand, (0,0))
            # pg.display.update()
            return self.output_screen
        elif mode == 'gray_array':
            # screen_expand = pg.transform.scale(self.game.state.screen, c.SCREEN_SIZE)
            # self.game.screen.blit(screen_expand, (0,0))
            # pg.display.update()
            gray_screen = cv2.cvtColor(self.output_screen, cv2.COLOR_RGB2GRAY)
            return gray_screen
        else:
            pass

    def step(self, action, step_count=1):
        if self.game.done:
            return 0, 0, True, 0
        for _ in range(step_count):
            self.game.event_loop()
            # self.keys = pg.key.get_pressed()
            self.keys = self.action_list[action]
            self.game.keys = self.keys
            self.game.update()
            if self.game.state.done:
                break
        player = self.game.state.player
        if player.fire:
            size = 'fire'
        elif player.big:
            size = 'big'
        else:
            size = 'small'
            
        self.next_info = {'x': player.rect.x, 'y': player.rect.y, 'vx': player.x_vel, 'vy': player.y_vel,
                          'time': self.game.state.overhead_info.time, 'dead':self.game.state.player.dead,
                          'info': self.game.state.game_info, 'viewport_x': self.game.state.viewport.x,
                          'size': size}
        reward = self._reward()
        self.info = self.next_info
        self.output_screen = np.array(pg.surfarray.pixels3d(self.game.state.screen))
        self.output_screen = self.output_screen.transpose(1,0,2)
        self.total_reward += reward
        return self.output_screen, reward, self.game.state.done, self.info

    def snap(self, viewport):
        area = (viewport, 0, 256, 240)
        self.game.state.screen.blit(self.game.state.level, (0, 0), area)
        self.output_screen = np.array(pg.surfarray.pixels3d(self.game.state.screen))
        return self.output_screen

    # Calculate the reward
    def _reward(self):
        dx = self.next_info['x'] - self.info['x']
        dy = self.next_info['y'] - self.info['y']
        dt = self.next_info['time'] - self.info['time']
        reward = dx + dt
        if self.game.state.done:
            if self.next_info['dead']:
                reward -= 15
            else:
                reward += 10
        return reward

    def seed():
        pass

    def close(self):
        pg.quit()
