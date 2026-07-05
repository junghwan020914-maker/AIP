# -*- coding: utf-8 -*-
"""VP(추적점) 계산 공용 모듈 — VP-following RL용.

방향성(팀): BT가 전술 판단 → VP(조준점) 생성 → RL이 그 VP를 향해 최적 비행(고전 StickController 대체).
학습 단계에선 BT DLL 대신 synthetic VP(리드 추적점)를 파이썬에서 생성. 나중에 BT GetVP로 교체 가능.

VP = 적 위치 + 적 속도벡터 × lead_time  (적이 갈 곳을 미리 조준 = 사격 리드)
observation과 reward가 동일 VP를 쓰도록 여기 한 곳에서 계산.
"""
from __future__ import annotations

import math
import numpy as np

from dogfight.sim.state_schema import StateIndex


def vel_ned(state) -> np.ndarray:
    """YAW/PITCH/KCAS로 NED 속도벡터 근사 (KCAS=속도 proxy, 방향은 정확)."""
    spd = float(state[StateIndex.KCAS])
    yaw = math.radians(float(state[StateIndex.YAW]))
    pit = math.radians(float(state[StateIndex.PITCH]))
    cp = math.cos(pit)
    return np.array([spd * cp * math.cos(yaw), spd * cp * math.sin(yaw), -spd * math.sin(pit)], dtype=float)


def compute_vp(ownship_state, target_state, lead_time: float = 1.2) -> np.ndarray:
    """synthetic 리드 추적점(NED). lead_time=0이면 순수추적(적 현위치)."""
    tpos = np.asarray(target_state[:3], dtype=float)          # N,E,D
    tvel = vel_ned(target_state)
    return tpos + tvel * float(lead_time)


def vp_relative(ownship_state, vp_ned):
    """VP의 아군 상대 정보: (delta_ned, range_m, ata_to_vp_deg, closure_mps).

    ata_to_vp = 아군 기수(속도방향)와 VP 방향(LOS) 사이 각. 0°=기수가 VP를 정확히 조준.
    closure = 아군 속도의 LOS 투영(양수=VP로 접근).
    """
    opos = np.asarray(ownship_state[:3], dtype=float)
    delta = np.asarray(vp_ned, dtype=float) - opos
    rng = float(np.linalg.norm(delta)) + 1e-6
    los = delta / rng
    ovel = vel_ned(ownship_state)
    nose = ovel / (np.linalg.norm(ovel) + 1e-6)              # 기수(속도) 방향
    cos_ata = float(np.clip(np.dot(nose, los), -1.0, 1.0))
    ata_deg = math.degrees(math.acos(cos_ata))
    closure = float(np.dot(ovel, los))
    return delta, rng, ata_deg, closure


__all__ = ["vel_ned", "compute_vp", "vp_relative"]
