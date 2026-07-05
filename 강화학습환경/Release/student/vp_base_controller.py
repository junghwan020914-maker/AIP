# -*- coding: utf-8 -*-
"""VP-base 컨트롤러 — BT의 실제 StickController(Controller_CY.cpp) 파이썬 포팅.

BT의 lift-vector BFM 제어: UpVector(양력벡터)를 타겟(VP) 방향으로 롤 + LOS(각도)에 비례한 pull.
= 제대로 된 coordinated turn. residual/imitation의 'base/시범자'.
소스: AIP/BehaviorTree/aip-dogfight-bt-main/Geometry/Controller_CY.cpp GetStick().
단순화: rudder moving-average 필터·LOS 적분항 생략(cpp 주석의 대안). throttle는 BT StickValue에 없어 고정.

⚠️ pitch 부호: BT는 PitchCMD 음수=pull(기수 상승). RL env sim의 pitch 부호와 일치하는지 base 단독 테스트로 검증
   (추락하면 pitch 부호 반전). 학습 전 반드시 base 단독 비행 확인.
"""
from __future__ import annotations

import math
import numpy as np

from dogfight.sim.state_schema import StateIndex

RADTODEG = 180.0 / math.pi


def _clamp(x, lo, hi):
    return lo if x <= lo else (hi if x >= hi else x)


def _euler_to_quat(roll, pitch, yaw):
    """BT EulerAngle.toQuaternion 컨벤션(라디안 입력)."""
    c1, s1 = math.cos(yaw / 2), math.sin(yaw / 2)
    c2, s2 = math.cos(pitch / 2), math.sin(pitch / 2)
    c3, s3 = math.cos(roll / 2), math.sin(roll / 2)
    c1c2, s1s2 = c1 * c2, s1 * s2
    w = c1c2 * c3 + s1s2 * s3
    x = c1 * s2 * c3 + s1 * c2 * s3
    y = s1 * c2 * c3 - c1 * s2 * s3
    z = c1c2 * s3 - s1s2 * c3
    n = math.sqrt(w * w + x * x + y * y + z * z) + 1e-12
    return w / n, x / n, y / n, z / n


# pitch 부호 계수: RL env가 BT와 반대면 -1로 (base 단독 테스트로 결정)
# BT 프레임=Up-positive(LLAtoCartesian dD=고도-base), RL env=NED(Down-positive) → 위치·VP Z 뒤집어 맞춤.
PITCH_SIGN = 1.0
ROLL_SIGN = 1.0
THROTTLE_CMD = 0.7


def base_action(ownship_state, vp_ned) -> np.ndarray:
    # BT 프레임(N,E,Up)으로: RL의 NED(N,E,Down)에서 Z(=D) 부호 뒤집기
    _o = np.asarray(ownship_state[:3], dtype=float)
    my = np.array([_o[0], _o[1], -_o[2]])
    _v = np.asarray(vp_ned, dtype=float)
    vp = np.array([_v[0], _v[1], -_v[2]])
    qw, qx, qy, qz = _euler_to_quat(
        math.radians(float(ownship_state[StateIndex.ROLL])),
        math.radians(float(ownship_state[StateIndex.PITCH])),
        math.radians(float(ownship_state[StateIndex.YAW])),
    )
    fwd = np.array([1 - 2 * (qx * qx + qy * qy), 2 * (qx * qz + qw * qy), -2 * (qy * qz - qw * qx)])
    up = np.array([-2 * (qy * qz + qw * qx), -2 * (qx * qy - qw * qz), 1 - 2 * (qx * qx + qz * qz)])
    right = np.array([2 * (qx * qz - qw * qy), 1 - 2 * (qy * qy + qz * qz), -2 * (qx * qy + qw * qz)])

    fpp = fwd * 1000.0 + my
    proj_v = np.dot(vp - fpp, fwd) * fwd
    proj_tv = (vp - proj_v) - fpp
    ptv_len = float(np.linalg.norm(proj_tv)) or 0.0001

    ut_ang = math.acos(_clamp(float(np.dot(up, proj_tv / ptv_len)), -1.0, 1.0))
    if math.isnan(ut_ang):
        ut_ang = 0.0
    ut = ut_ang if np.dot(right, proj_tv / ptv_len) >= 0 else -ut_ang

    los_vec = vp - my
    los = math.degrees(math.acos(_clamp(float(np.dot(fwd, los_vec)) / (float(np.linalg.norm(los_vec)) + 1e-9), -1.0, 1.0)))
    if math.isnan(los):
        los = 0.0

    # ── RollCMD (BT 로직) ──
    if abs(ut * RADTODEG) > 90:
        roll_cmd = math.sin(ut)
        roll_cmd = _clamp(roll_cmd, -1, 1) if los > 3 else roll_cmd * los * (-0.1)
    else:
        roll_cmd = _clamp(math.sin(ut), -1, 1)
        roll_cmd = roll_cmd * abs(roll_cmd)
    if roll_cmd < 0.1:
        roll_cmd = roll_cmd * 3
    roll_cmd = roll_cmd * _clamp(los, 0, 1)

    # ── RudderCMD (필터 생략) ──
    rudder_cmd = -math.sin(ut) * _clamp(los, 0, 6)

    # ── PitchCMD (적분항 생략, 음수=pull) ──
    error_effect = _clamp(los / 6.0, 0, 1.5)
    roll_effect = 1 - _clamp(abs(ut * RADTODEG) / 90.0, 0, 1)
    horizon_effect = 1.0 if abs(ut * RADTODEG) <= 90 else 0.5
    pitch_cmd = (error_effect * roll_effect * horizon_effect * (-1.0)) if los < 90 else -1.0
    pitch_cmd *= PITCH_SIGN

    return np.array([_clamp(ROLL_SIGN * roll_cmd, -1, 1), _clamp(pitch_cmd, -1, 1),
                     _clamp(ROLL_SIGN * rudder_cmd, -1, 1), THROTTLE_CMD], dtype=np.float32)


__all__ = ["base_action"]
