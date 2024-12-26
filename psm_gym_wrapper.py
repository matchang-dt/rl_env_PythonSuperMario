import numpy as np
import cv2
from collections import deque

import gym
from gym.wrappers import GrayScaleObservation
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv

class SkipFrame(gym.Wrapper):
    def __init__(self, env, skip):
        super().__init__(env)
        self._skip = skip
        self.viewport_que = deque()
        self.x_que = deque()
        self.y_que = deque()

    def step(self, action):
        """repeat actions and add up the rewards"""
        total_reward = 0
        done = False
        for i in range(self._skip):
            # while the set up skip frames, repeat the same actions and add up the rewards
            obs, reward, done, info = self.env.step(action)
            total_reward += reward
            self.viewport_que.append(info['viewport_x'])
            self.x_que.append(info['x'])
            self.y_que.append(info['y'])
            if len(self.viewport_que) > 4:
                self.viewport_que.popleft()
            if len(self.x_que) > 4:
                self.x_que.popleft()
            if len(self.y_que) > 4:
                self.y_que.popleft()
            if done:
                break
        info['viewport_real_x'] = list(self.viewport_que)
        info['xs'] = list(self.x_que)
        info['ys'] = list(self.y_que)
        return obs, total_reward, done, info

class ResizeEnv(gym.ObservationWrapper):
    def __init__(self, env, size):
        """
        Downsample images by a factor of ratio
        """
        gym.ObservationWrapper.__init__(self, env)
        (oldh, oldw, oldc) = env.observation_space.shape
        newshape = (*size, oldc)
        self.observation_space = gym.spaces.Box(low=0, high=255,
            shape=newshape, dtype=np.uint8)

    def observation(self, frame):
        height, width, _ = self.observation_space.shape
        frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)
        if frame.ndim == 2:
            frame = frame[:,:,None]
        return frame