# -*- coding: utf-8 -*-
"""Custom observation: tactical20 = tactical16 + 적 운동 4개.

동기(Step 2): tactical16엔 적의 '속도/기수(어디로 가는지)'가 없어서, 기억 없는 MLP가
움직이는 적을 리드(lead)하거나 오버슈트를 예측하지 못함 → 사격 위치(꼬리)를 못 잡음.
→ 적 기수/상하/상대속도/접근율(closure)을 추가해 조준을 가능하게 함.

사용:
  observation_mode: custom
  observation_module: student.my_observation
"""
from __future__ import annotations

import math
import numpy as np

from dogfight.envs.observation import build_observation as _build_base, normalize
from dogfight.sim.state_schema import StateIndex


OBSERVATION_MODE = "tactical20"
OBSERVATION_SIZE = 20
OBSERVATION_LOW = -1.0
OBSERVATION_HIGH = 1.0


def _vel_ned(state) -> np.ndarray:
    """YAW/PITCH/KCAS로 NED 속도벡터 근사 (KCAS는 속도 proxy — 부호·방향은 정확)."""
    spd = float(state[StateIndex.KCAS])
    yaw = math.radians(float(state[StateIndex.YAW]))
    pit = math.radians(float(state[StateIndex.PITCH]))
    cp = math.cos(pit)
    return np.array([spd * cp * math.cos(yaw), spd * cp * math.sin(yaw), -spd * math.sin(pit)], dtype=float)


def build_observation(ownship_state, target_state, geo_info, wez_config=None):
    """tactical16(0-15) + 적 운동(16-19)."""
    obs = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
    obs[:16] = _build_base("tactical16", ownship_state, target_state, geo_info, wez_config)

    # 16: 적 기수(어디로 가는지) / 17: 적 상하각
    obs[16] = normalize(float(target_state[StateIndex.YAW]),   0.0, 360.0)
    obs[17] = normalize(float(target_state[StateIndex.PITCH]), -90.0, 90.0)
    # 18: 상대 속도(속도 매칭 — 꼬리 물고 유지하려면 속도를 맞춰야 함)
    obs[18] = normalize(float(target_state[StateIndex.KCAS]) - float(ownship_state[StateIndex.KCAS]), -600.0, 600.0)
    # 19: 접근율(range rate). LOS에 투영한 상대속도. 음수=접근, 양수=이탈 → 오버슈트 예측
    rel_pos = np.asarray(target_state[:3], dtype=float) - np.asarray(ownship_state[:3], dtype=float)
    dist = float(np.linalg.norm(rel_pos)) + 1e-6
    rel_vel = _vel_ned(target_state) - _vel_ned(ownship_state)
    range_rate = float(np.dot(rel_pos, rel_vel) / dist)
    obs[19] = normalize(range_rate, -600.0, 600.0)
    return obs


def describe_observation():
    return {
        "mode": OBSERVATION_MODE,
        "size": OBSERVATION_SIZE,
        "features": [
            "...tactical16 (0-15)",
            "target_yaw", "target_pitch", "relative_speed", "closure_rate(range_rate)",
        ],
        "description": "tactical16 + 적 운동(기수/상하/상대속도/접근율) — 리드·오버슈트 예측용.",
    }


__all__ = ["OBSERVATION_MODE", "OBSERVATION_SIZE", "OBSERVATION_LOW", "OBSERVATION_HIGH",
           "build_observation", "describe_observation"]
