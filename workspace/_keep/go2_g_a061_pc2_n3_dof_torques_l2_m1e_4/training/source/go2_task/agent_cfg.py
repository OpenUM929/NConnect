"""PPO runner config for Quadruped (Unitree Go2) training.

Go2 의 action space 는 12 (각 다리 3 joint × 4 다리). H1 의 19 보다 작음.
네트워크는 비슷한 크기 [512,256,128] 유지 — overkill 아님, robust.
"""

from __future__ import annotations

from isaaclab.utils import configclass
from isaaclab_rl.rsl_rl import (
    RslRlOnPolicyRunnerCfg,
    RslRlPpoActorCriticCfg,
    RslRlPpoAlgorithmCfg,
)


@configclass
class QuadrupedPPORunnerCfg(RslRlOnPolicyRunnerCfg):
    num_steps_per_env = 24
    max_iterations = 5000
    save_interval = 100
    experiment_name = "quadruped"
    empirical_normalization = False
    policy = RslRlPpoActorCriticCfg(
        class_name="ActorCritic",
        init_noise_std=1.0,
        actor_hidden_dims=[512, 256, 128],
        critic_hidden_dims=[512, 256, 128],
        activation="elu",
    )
    # ─── PPO hyperparameter — H1 검증값 정렬 (2026-06-11) ────────────
    # 이력: 2026-05-25 발산(iter 7097 value_loss=inf) 후 보수화했었음
    #   (lr 5e-4 / desired_kl 0.008 / grad_norm 0.5).
    # ⚠️ 그 보수화가 신 스택(rsl-rl 4.x)에선 역효과: 탐색이 조기 수축
    #   (action std 1.0→0.43 @ iter 300)해 "서서 제자리 회전" 국소최적에
    #   갇히고 보행을 못 배움. 같은 서버에서 H1 은 아래 값으로 std 1.1 유지
    #   하며 정상 학습(terrain 5.9) → H1 검증값으로 정렬.
    # 발산 재발 시: model_best 선별이 발산 전 최고 체크포인트를 집으므로
    #   결과물은 보존됨. 그래도 재발하면 lr 만 7e-4 로 한 단계 내릴 것.
    algorithm = RslRlPpoAlgorithmCfg(
        class_name="PPO",
        value_loss_coef=1.0,
        use_clipped_value_loss=True,
        clip_param=0.2,
        entropy_coef=0.008,
        num_learning_epochs=5,
        num_mini_batches=4,
        learning_rate=1.0e-3,
        schedule="adaptive",
        gamma=0.99,
        lam=0.95,
        desired_kl=0.01,
        max_grad_norm=1.0,
    )
