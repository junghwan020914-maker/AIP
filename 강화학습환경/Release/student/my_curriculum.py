# -*- coding: utf-8 -*-
"""Minimal student curriculum template.

Use this file only when you want to replace the built-in curriculum.
Run with:
  python train_curriculum.py --stages-module student.my_curriculum

For the full built-in curriculum and two-circle head-on reference, see:
  src/dogfight/ai/curriculum.py
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


def get_stages() -> list[CurriculumStage]:
    """Stage 0(생존)만 정의 — 단계별 끊어 학습. 이후 단계는 검증 후 추가."""
    return [
        CurriculumStage(
            index=0,
            name="flight_survival",
            description="생존과 스로틀 제어. 고정 타겟.",
            target_mode="fixed",              # 적은 고정(정지) 상태
            episode_step_limit=3600,          # 60초
            max_iterations=200,
            checkpoint_interval=5,            # 5 iteration마다 저장
            reward_overrides={
                # ── 켜는 것 (생존) ──
                "survival_bonus": 0.05,       # 살아있으면 매 프레임 +
                "low_altitude_penalty": 1.0,  # 낮게 날면 강한 벌 (기본 0.1의 10배)
                "loss_reward": -50.0,         # 추락하면 벌
                # ── 끄는 것 (0으로) ──
                "pursuit_scale": 0.0,         # 추격 끔
                "positioning_scale": 0.0,     # 위치 끔  ← 우리가 추가한 것
                "wez_bonus": 0.0,             # 공격 끔  ← 순수 생존 위해
                "wez_threat_penalty": 0.0,    # 회피 끔  ← 우리가 추가한 것
                "damage_scale": 0.0,          # 전투 끔
                "win_reward": 0.0,            # 이기든 말든 무관
                "draw_reward": 0.0,
            },
            randomization={
                "enabled": True,
                "radius": 1.0,                # 0이면 ValueError 버그 → 1.0 (사실상 위치 고정)
                "r_roll": 5.0,
                "r_pitch": 5.0,
                "r_heading": 15.0,
            },
            advance_conditions={
                "crash_rate_max": 0.20,       # 추락률 20% 미만이면 통과
            },
            advance_window=10,
        ),
    ]

__all__ = ["get_stages"]