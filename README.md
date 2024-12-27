# Reinforcement Environment of SuperMario
A reinforcement learning environment based on. 
A improved supermario game based on https://github.com/marblexu/PythonSuperMario.
* Implemented OpenAI-Gym like interface.
* Allowed objects (includes ground and steps) to be freely positioned independently of the background for reinforcement learning experiments, instead, eliminated background.
* Omitted information displayed on top (score, coins, etc) and the production of reaching the goal, because this is a reinforcement learning environment.
* Fixed many in-game behaviors (refer to the bottom).


# Demo
Left: Run trained agent in Level 1-1, Right: Run the same agent in modified level

<video width="480" height="360" controls>
  <source src="resources/demo/L1-1full.mp4" type="video/mp4">
</video>
<video width="480" height="360" controls>
  <source src="resources/demo/Modified_L1-1.mp4" type="video/mp4">
</video>

# Requirement
\* In particular, later versions of Python, OpenAI Gym and Stable Baselines3 do not work.
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

# Modified Points of Game
* Made speed of time decrease faster
* Aspect and resolution of display
* Changed animation control from real-time-based to frame-based
* Coloring of Goomba
* Fixed viewport misalignment in various situations (e.g. during transformation)
* Changed so that which power-up item appears depends on Mario's status
* Jump height during dash jump
* Changed behavior when jumping so that you are not affected by gravity for a certain period of time while pressing A
* This enabled adjustment jump height
* Changed fireball firing from a cool time system to a limit of two shots on screen
* Disabled firing fireball during crouching
* Enabled crouching jump
* Made hitbox of Mario a bit narrower (in general action games, hitbox is narrower than appearance)
* Made enemies turn their direction when they contact another enemy
* Enabled sliding during crouching after dush
* Trajectry of fireballs
<!-- # How to Play
* use LEFT/RIGHT/DOWN key to control player
* use key 'a' to jump
* use key 's' to shoot firewall or run -->