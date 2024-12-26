# Reinforcement Environment of SuperMario
A reinforcement learning environment based on. 
A improved supermario game based on https://github.com/marblexu/PythonSuperMario.
* Implemented OpenAI-Gym like interface.
* Allowed objects (includes ground and steps) to be freely positioned independently of the background for reinforcement learning experiments, instead, eliminated background.
* Omitted information displayed on top (score, coins, etc) and the production of reaching the goal, because this is a reinforcement learning environment.
* Fixed many in-game behaviors (refer to the bottom).

# Requirement
\* In particular, later versions of OpenAI Gym and Stable Baselines3 do not work.
* Python 3.9
* Python-Pygame 3.2
* Python-Numpy 1.26
* Python-OpenCV 4.1
* Python-OpenAI Gym 0.21
* Python-Stable-Baselines3 1.6

# How To Use Environment
You can use this environment like OpenAI Gym
```Python
from stable_baselines3 import PPO
from gym.wrappers import GrayScaleObservation
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv

from psmenv import PSMEnv
from psm_gym_wrapper import SkipFrame, ResizeEnv

# Use wrappers for dimentionality reduction
env = PSMEnv()
env = SkipFrame(env, skip=3)
env = ResizeEnv(env, (60, 64))
env = GrayScaleObservation(env, keep_dim=True)
env = DummyVecEnv([lambda: env])
STACK_FRAME_NUMB = 4
env = VecFrameStack(env, STACK_FRAME_NUMB, channels_order='last')

trainsteps = 10000
model = PPO('MlpPolicy', env, verbose=1)
model.learn(total_timesteps=trainsteps)

test_episodes = 10
for i in range(test_episodes):
    obs = env.reset()
    total_reward = 0
    while True:
        action, _state = model.predict(obs, deterministic=False)
        obs, reward, done, info = env.step(action)
        total_reward += reward
        env.render()
        if done:
            break

```

<!-- # How to Play
* use LEFT/RIGHT/DOWN key to control player
* use key 'a' to jump
* use key 's' to shoot firewall or run -->

<!-- # Demo
![level_1_1](https://raw.githubusercontent.com/marblexu/PythonSuperMario/master/resources/demo/level_1_1.png)
![level_1_2](https://raw.githubusercontent.com/marblexu/PythonSuperMario/master/resources/demo/level_1_2.png)
![level_1_3](https://raw.githubusercontent.com/marblexu/PythonSuperMario/master/resources/demo/level_1_3.png)
![level_1_4](https://raw.githubusercontent.com/marblexu/PythonSuperMario/master/resources/demo/level_1_4.png) -->
