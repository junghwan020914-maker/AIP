# -*- coding: utf-8 -*-
"""VP-following 커리큘럼 — "주어진 VP를 향해 나는 조종사" 학습.

stage0 vp_orient: 넓은 조준(τ 크게)으로 'VP를 향하고 안 죽기' 먼저.
stage1 vp_track : 날카로운 조준(τ 작게)으로 정밀 추적.
target=loiter(움직임), reward=student.my_reward_vp, observation=student.my_observation_vp.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dogfight.ai.curriculum import CurriculumStage


_COMMON = dict(
    vp_alt_gate_scale=1.0,        # 고도 유지할 때만 조준 보상(coordinated turn)
    bank_penalty_scale=1.0,
    dive_penalty_scale=1.0,
    low_altitude_penalty=0.5,
    safe_altitude_m=1000.0,
    loss_reward=-100.0,
)
_RAND = {"enabled": True, "radius": 500.0, "r_roll": 5.0, "r_pitch": 5.0, "r_heading": 15.0}


def get_stages() -> list[CurriculumStage]:
    return [
        CurriculumStage(
            index=0,
            name="vp_orient",
            description="VP를 향해 기수 맞추고 안 죽기(넓은 조준). loiter의 리드점.",
            target_mode="loiter",
            episode_step_limit=3600,
            max_iterations=300,
            checkpoint_interval=50,
            reward_overrides={**_COMMON, "vp_aim_scale": 1.0, "vp_aim_tau_deg": 30.0},
            randomization=_RAND,
            advance_conditions={},
            advance_window=10,
        ),
        CurriculumStage(
            index=1,
            name="vp_track",
            description="VP 정밀 조준·추적(날카로운 조준).",
            target_mode="loiter",
            episode_step_limit=3600,
            max_iterations=300,
            checkpoint_interval=50,
            reward_overrides={**_COMMON, "vp_aim_scale": 1.0, "vp_aim_tau_deg": 15.0},
            randomization=_RAND,
            advance_conditions={},
            advance_window=10,
        ),
    ]


__all__ = ["get_stages"]
