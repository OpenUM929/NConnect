"""Quadruped (Unitree Go2) training package — NAVER Connect Robotics Cup 2026 예선.

Tasks:
  - Quadruped-v0 : quadruped_rewards.py 의 REWARD_WEIGHTS 를 적용해 학습.
"""

__version__ = "0.1.0"

import gymnasium as gym


gym.register(
    id="Quadruped-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.env_cfg:QuadrupedRoughEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agent_cfg:QuadrupedPPORunnerCfg",
    },
)
