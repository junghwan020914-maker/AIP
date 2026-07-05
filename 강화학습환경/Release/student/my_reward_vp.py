# -*- coding: utf-8 -*-
"""VP-following 보상 — "주어진 VP를 향해 안 죽고 에너지 효율적으로 조준·비행".

dogfight 자율 보상(pursuit/positioning/aim/damage…)을 버리고, RL의 올바른 범위로 단순화:
  주보상 = VP 조준(기수를 VP에) × 접근(가까이) × 고도게이트(고도 유지할 때만)
  + 자세규율(스파이럴 방지) + 고도 floor + step + 종료(추락) 페널티.
lead/전술은 VP(=BT 또는 synthetic)가 담당 → RL은 조종만. reactive(MLP로 충분).
"""
from __future__ import annotations

import math

from dogfight.sim.state_schema import StateIndex
from student.vp_utils import compute_vp, vp_relative


MY_REWARD_CONFIG = {
    "step_penalty": -0.01,
    # ── VP 조준(주보상) ──
    "vp_lead_time": 1.2,          # my_observation_vp.VP_LEAD_TIME과 동일해야 함
    "vp_aim_scale": 1.0,
    "vp_aim_tau_deg": 25.0,       # 작을수록 정조준에 집중 (exp(-ata_vp/tau))
    "vp_range_m": 4000.0,         # 이 안에서 가까울수록 range_factor↑
    # ── 고도게이트(coordinated turn 유도, dogfight서 검증) ──
    "vp_alt_gate_scale": 1.0,     # 0=off, 1=완전게이팅
    "vp_alt_gate_ref_m": 7000.0,
    "vp_alt_gate_floor_m": 4000.0,
    # ── 자세규율(스파이럴 방지) ──
    "bank_penalty_scale": 1.0,
    "bank_limit_deg": 100.0,
    "dive_penalty_scale": 1.0,
    "dive_limit_deg": 30.0,
    # ── 고도 floor(보조 안전망) ──
    "low_altitude_penalty": 0.5,
    "safe_altitude_m": 1000.0,
    # ── 종료 ──
    "loss_reward": -100.0,
    "win_reward": 0.0,
    "draw_reward": 0.0,
}


def compute_reward(ownship_state, target_state, ownship_damage, target_damage,
                   geo_info, wez_config, reward_config, terminated, truncated, end_condition):
    c = {}
    g = reward_config.get

    vp = compute_vp(ownship_state, target_state, lead_time=float(g("vp_lead_time", 1.2)))
    _, rng, ata_vp, _ = vp_relative(ownship_state, vp)

    altitude = float(ownship_state[StateIndex.ALT])
    roll = abs(float(ownship_state[StateIndex.ROLL]))
    pitch = float(ownship_state[StateIndex.PITCH])

    # ── 1. VP 조준 (주보상): 기수를 VP에 × 가까이 × 고도게이트 ──
    tau = max(0.1, float(g("vp_aim_tau_deg", 25.0)))
    aim = math.exp(-ata_vp / tau)                                  # 0(먼각)~1(정조준)
    vp_range = max(1.0, float(g("vp_range_m", 4000.0)))
    range_factor = max(0.0, 1.0 - rng / vp_range)                 # 가까울수록↑
    alt_gate_s = float(g("vp_alt_gate_scale", 0.0))
    if alt_gate_s > 0.0:
        aref = float(g("vp_alt_gate_ref_m", 7000.0)); afloor = float(g("vp_alt_gate_floor_m", 4000.0))
        af = max(0.0, min(1.0, (altitude - afloor) / max(1.0, aref - afloor)))
        gate = (1.0 - alt_gate_s) + alt_gate_s * af
    else:
        gate = 1.0
    c["vp_aim"] = float(g("vp_aim_scale", 1.0)) * aim * range_factor * gate

    # ── 2. step ──
    c["step"] = float(g("step_penalty", -0.01))

    # ── 3. 자세규율 (극단 롤/급강하만) ──
    bank_s = float(g("bank_penalty_scale", 0.0))
    if bank_s != 0.0:
        bl = float(g("bank_limit_deg", 100.0))
        c["bank"] = -bank_s * max(0.0, roll - bl) / max(1.0, 180.0 - bl)
    else:
        c["bank"] = 0.0
    dive_s = float(g("dive_penalty_scale", 0.0))
    if dive_s != 0.0:
        dl = float(g("dive_limit_deg", 30.0))
        c["dive"] = -dive_s * max(0.0, (-pitch) - dl) / max(1.0, 90.0 - dl)
    else:
        c["dive"] = 0.0

    # ── 4. 고도 floor (보조 안전망) ──
    safe_alt = float(g("safe_altitude_m", 1000.0))
    if altitude < safe_alt:
        depth = (safe_alt - altitude) / safe_alt
        c["altitude"] = -float(g("low_altitude_penalty", 0.5)) * (1.0 + depth)
    else:
        c["altitude"] = 0.0

    # ── 5. 종료(추락 등) ──
    terminal = 0.0
    if terminated or truncated:
        own_h = float(ownship_state[StateIndex.HEALTH])
        if end_condition in ("ownship altitude below min", "FDM Update Fail", "Ownship FDM output Fall") or own_h <= 0.0:
            terminal = float(g("loss_reward", -100.0))
        else:
            terminal = float(g("draw_reward", 0.0))
    c["terminal"] = terminal

    return float(sum(c.values())), c


__all__ = ["MY_REWARD_CONFIG", "compute_reward"]
