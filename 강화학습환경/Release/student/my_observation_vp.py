# -*- coding: utf-8 -*-
"""VP-following 관측 — "주어진 VP를 향해 나는 조종사"용.

자기 상태(자세·에너지) + VP 상대(어디를 조준/얼마나 가까이). 적을 직접 추적하지 않고
'주어진 점(VP)'만 좇으므로 lead 예측 불필요 → reactive(MLP로 충분, LSTM 불필요).

사용:
  observation_mode: custom
  observation_module: student.my_observation_vp
"""
from __future__ import annotations

import numpy as np

from dogfight.envs.observation import normalize
from dogfight.sim.state_schema import StateIndex
from student.vp_utils import compute_vp, vp_relative


OBSERVATION_MODE = "vp_follow"
OBSERVATION_SIZE = 11
OBSERVATION_LOW = -1.0
OBSERVATION_HIGH = 1.0

VP_LEAD_TIME = 1.2   # reward와 동일해야 함(my_reward_vp의 vp_lead_time과 맞춤)


def build_observation(ownship_state, target_state, geo_info, wez_config=None):
    obs = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
    # 0-4: 자기 상태(자세 + 에너지)
    obs[0] = normalize(float(ownship_state[StateIndex.ROLL]),  -180.0, 180.0)
    obs[1] = normalize(float(ownship_state[StateIndex.PITCH]),  -90.0,  90.0)
    obs[2] = normalize(float(ownship_state[StateIndex.YAW]),      0.0, 360.0)
    obs[3] = normalize(float(ownship_state[StateIndex.KCAS]),     0.0, 600.0)
    obs[4] = normalize(float(ownship_state[StateIndex.ALT]),      0.0, 15000.0)
    # 5-10: VP 상대 (Δn/e/d, ATA-to-VP, 거리, 접근율)
    vp = compute_vp(ownship_state, target_state, lead_time=VP_LEAD_TIME)
    delta, rng, ata_vp, closure = vp_relative(ownship_state, vp)
    obs[5] = normalize(float(delta[0]), -15000.0, 15000.0)
    obs[6] = normalize(float(delta[1]), -15000.0, 15000.0)
    obs[7] = normalize(float(delta[2]),  -8000.0,  8000.0)
    obs[8] = normalize(float(ata_vp),       0.0, 180.0)      # 기수↔VP 각 (0=정조준)
    obs[9] = normalize(float(rng),          0.0, 10000.0)
    obs[10] = normalize(float(closure),  -600.0, 600.0)
    return obs


def describe_observation():
    return {
        "mode": OBSERVATION_MODE,
        "size": OBSERVATION_SIZE,
        "features": [
            "own_roll", "own_pitch", "own_yaw", "own_kcas", "own_alt",
            "vp_dn", "vp_de", "vp_dd", "ata_to_vp", "range_to_vp", "closure_to_vp",
        ],
        "description": "VP-following: 자기상태 + VP상대. 주어진 점을 향해 나는 조종사(reactive).",
    }


__all__ = ["OBSERVATION_MODE", "OBSERVATION_SIZE", "OBSERVATION_LOW", "OBSERVATION_HIGH",
           "build_observation", "describe_observation"]
