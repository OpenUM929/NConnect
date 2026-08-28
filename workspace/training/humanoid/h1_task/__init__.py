"""Humanoid (H1) training package — NAVER Connect Robotics Cup 2026 예선.

Tasks:
  - Humanoid-v0 : humanoid_rewards.py 의 REWARD_WEIGHTS 를 적용해 학습.
"""

__version__ = "0.1.0"

import gymnasium as gym


gym.register(
    id="Humanoid-v0",
    entry_point="isaaclab.envs:ManagerBasedRLEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{__name__}.env_cfg:HumanoidRoughEnvCfg",
        "rsl_rl_cfg_entry_point": f"{__name__}.agent_cfg:HumanoidPPORunnerCfg",
    },
)
