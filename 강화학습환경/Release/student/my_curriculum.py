# -*- coding: utf-8 -*-
"""Minimal student curriculum template.

Use this file only when you want to replace the built-in curriculum.
Run with:
  python train_curriculum.py --stages-module student.my_curriculum

For the full built-in curriculum and two-circle head-on reference, see:
  src/dogfight/ai/curriculum.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dogfight.ai.curriculum import CurriculumStage


def get_stages() -> list[CurriculumStage]:
    """Stage 0(생존)과 Stage 1(기초 추격) 정의 — 단계별 끊어 학습."""
    return [
        # =====================================================================
        # Stage 0: 순수 비행 생존 단계 (이미 2000번 완수함)
        # =====================================================================
        CurriculumStage(
            index=0,
            name="flight_survival",
            description="생존 + 안정적 loiter 적을 향해 완만히 정렬(orient). fixed는 sim이 가라앉아 폐기.",
            target_mode="loiter",             # ★안정적 적(fixed/autopilot은 고도유지 안 됨=가라앉음). bank15는 yaml
            episode_step_limit=3600,          # 60초
            max_iterations=300,
            checkpoint_interval=50,
            reward_overrides={
                # ── 생존 + 자세규율 ──
                "survival_bonus": 0.05,       # 살아있으면 매 프레임 +
                "low_altitude_penalty": 0.5,  # 완만한 고도 floor
                "safe_altitude_m": 1000.0,
                "bank_penalty_scale": 1.0,    # 스파이럴 방지(orient하며 기동해도)
                "dive_penalty_scale": 1.0,
                "sink_rate_penalty_scale": 0.0,  # v11: sink 제거(disengage 유발) → 고도게이트로 대체
                "pursuit_alt_gate_scale": 1.0,   # ★고도유지하며 선회할 때만 pursuit 보상(tension 해소)
                "loss_reward": -50.0,
                # ── ★약한 추격: 적을 무시 안 하고 향하게(시드 ignore-prior 근절) ──
                "pursuit_scale": 0.2,         # 약하게만 (생존 우선, 적 방향 유지 학습)
                "pursuit_half_angle_deg": 180.0,
                # ── 아직 끔 ──
                "positioning_scale": 0.0,
                "aim_scale": 0.0,
                "wez_bonus": 0.0,
                "wez_threat_penalty": 0.0,
                "damage_scale": 0.0,
                "win_reward": 0.0,
                "draw_reward": 0.0,
            },
            randomization={
                "enabled": True,
                "radius": 500.0,              # 적과 거리 두고 시작 → 향하는 법 학습
                "r_roll": 5.0,
                "r_pitch": 5.0,
                "r_heading": 15.0,
            },
            advance_conditions={},
            advance_window=10,
        ),

        # =====================================================================
        # Stage 1: 기초 추격 및 조준 단계 (새로운 전술 가동)
        # =====================================================================
        CurriculumStage(
            index=1,
            name="basic_pursuit",
            description="움직이는 적(Loiter)을 향해 기수를 정렬하고 꼬리를 잡는 기초 추격.",
            target_mode="loiter",              # ★안정적 gentle loiter(bank15). fixed/autopilot은 가라앉아 폐기
            episode_step_limit=3600,          # 60초 제한시간 유지
            max_iterations=300,               # 진단·해결 단계: 추락(스파이럴) 잡히는지 확인(stage0 ~240 수렴 참고). 해결되면 늘림
            checkpoint_interval=50,           # [속도] 10→50: 체크포인트 저장 I/O↓(최종 번들은 별도 저장)
            reward_overrides={
                # ── 1. 기본 비행 유지 (Stage 0의 학습 내용 보존) ──
                "survival_bonus": 0.02,       # 비행은 이미 잘하므로 생존 보상은 살짝 낮춤
                # v4 교훈: safe_alt 6000/큰 페널티는 역효과(교전회피+SAC불안정, crash 악화). 완만한 floor net만.
                "low_altitude_penalty": 0.5,
                "safe_altitude_m": 1000.0,
                # ★v4 replay 진단: 추락 원인=인버티드 스파이럴(롤 150°→급강하). 자세규율로 직접 억제.
                # scale만 켜면 됨 — limit(80°/30°)은 MY_REWARD_CONFIG 기본값이 자동 병합됨(train_curriculum 근본수정).
                "bank_penalty_scale": 1.0,    # |roll|>80°(기본) 페널티 (뒤집힘 억제, 정상 선회 무영향)
                "dive_penalty_scale": 1.0,    # pitch<-30°(기본) 급강하 페널티
                "sink_rate_penalty_scale": 0.0,  # v11: sink 제거(disengage 유발) → 고도게이트로 대체
                "pursuit_alt_gate_scale": 1.0,   # ★고도유지하며 선회할 때만 pursuit 보상(tension 해소)
                "loss_reward": -100.0,        # 추락하면 여전히 큰 페널티
                
                # ── 2. 공격/추격 신호 ON (지안 님 my_reward.py의 핵심 장치들 작동) ──
                "pursuit_scale": 0.8,         # 0.4→0.8: 교전 유인 강화(시드 "적 무시" prior 극복)
                "pursuit_half_angle_deg": 180.0,  # ★dead-zone 제거: 전 각도에서 "적 향해 돌아서라" gradient(45°는 반대쪽서 신호 0)
                "positioning_scale": 0.3,     # [ON] 적의 후방 6시 방향(AA 감소)으로 진입하면 추가 보상!
                
                # ── 3. 전투/회피 신호 OFF (아직 단계가 아님) ──
                "wez_bonus": 0.0,             # 아직 미사일 발사 각도(1도 이내 정조준)는 보지 않음
                "wez_threat_penalty": 0.0,    # 적이 나를 쏘는 방어 상황은 고려하지 않음
                "damage_scale": 0.0,          # 대미지 계산 제외
                "win_reward": 100.0,          # 추격을 잘해서 우연히 적을 격추하거나 세션 통과 시 보상
                "draw_reward": 0.0,
            },
            # [1] 랜덤화 확장: 적이 선회하므로, 적과의 거리(radius)와 기수 각도를 더 크게 틀어놓고 시작합니다.
            randomization={
                "enabled": True,
                "radius": 500.0,              # 시작할 때 적과의 거리를 500m 반경 내에서 무작위로 섞음
                "r_roll": 5.0,                # 초기 기체의 기울기도 살짝 랜덤화
                "r_pitch": 5.0,
                "r_heading": 10.0,            # 시작 기수 방향을 틀어놓아 '적을 찾아 선회하는 법' 유도
            },
            
            # [2] auto-advance 비활성화(빈 dict): crash_rate/win_rate가 nan으로 찍히면
            #     _check_advance가 nan을 조건충족으로 오판해 조기 진급/종료하는 버그 있음(Stage0 확인).
            #     → 고정 max_iterations로 돌리고 최적 checkpoint를 수동 선택.
            #     지표 로깅 안정화되면 복구: {"crash_rate_max": 0.10, "win_rate_min": 0.30}
            advance_conditions={},
            advance_window=20,
        ),

        # =====================================================================
        # Stage 2 (Step1): WEZ 정조준·사격 — 비선회(autopilot 직진) 타겟부터
        #   v2 실패 교훈: (a) aim τ=3°가 밴드내 33° 구간에 gradient 0,
        #   (b) pursuit 0.2로 추적 자체가 약해짐(replay상 stage1보다 나쁨),
        #   (c) loiter turn-matching이 너무 어려움(관측에 적 속도 없어 리드 불가).
        #   → Step1: pursuit 복원(0.4)+aim τ=15+비선회 타겟으로 '밴드내 정조준' 가능성 검증.
        # =====================================================================
        CurriculumStage(
            index=2,
            name="wez_gunnery",
            description="비선회(직진) 적을 2° WEZ(152~914m)에 넣어 정조준·사격.",
            target_mode="loiter",             # ★안정적 gentle loiter(bank15)서 사격 학습
            episode_step_limit=3600,          # 60초
            max_iterations=300,               # v13: 하드닝(bank30 pursuit), 사격 defer
            checkpoint_interval=50,           # [속도] 20→50: 저장 I/O↓
            reward_overrides={
                # ── 기본 비행/생존 (v4 교훈: 큰 고도페널티 역효과 → 완만한 floor + 자세규율로 전환) ──
                "survival_bonus": 0.02,
                "low_altitude_penalty": 0.5,     # 6000/2.0 역효과 → 완만한 floor net
                "safe_altitude_m": 1000.0,
                "bank_penalty_scale": 1.0,       # ★인버티드 스파이럴 억제(롤>80° 기본)
                "dive_penalty_scale": 1.0,       # ★급강하 억제(pitch<-30° 기본)
                "sink_rate_penalty_scale": 0.0,  # v11: sink 제거 → 고도게이트로 대체
                "pursuit_alt_gate_scale": 1.0,   # ★고도유지하며 선회할 때만 pursuit 보상(tension 해소)
                "loss_reward": -100.0,
                # ── 코스 추적: stage1 수준으로 복원(0.4). v2의 0.2는 추적을 망침(replay 확인) ──
                "pursuit_scale": 0.8,            # 0.4→0.8: 교전 유인 강화
                "pursuit_half_angle_deg": 180.0, # dead-zone 제거: 전각도 추적 gradient
                "pursuit_range_m": 4000.0,
                "positioning_scale": 0.15,
                # ── ★정밀 조준: 밴드 안 ATA→0 급상승. τ=15로 완만화(33°→10° 구간에 gradient) ──
                "aim_scale": 0.0,                # v13 하드닝: 사격 defer(LSTM 후일), bank30 추격 교전만 굳힘
                "aim_tau_deg": 8.0,              # v12: 15→8 더 날카롭게(ATA<20° 구간에 강한 gradient — 정밀도 벽 공략)
                "optimal_range_m": 300.0,        # 152m 위 안전마진 + 데미지 높은 지점
                # ── 과접근 방지: v3에선 애초에 min_range 근처도 못 감(최소 237m) → 접근 억제만 함. 제거 ──
                "too_close_penalty": 0.0,
                # ── 사격 payoff (ATA≤1° 달성 시 실데미지/격추) ──
                "wez_bonus": 0.0,
                "damage_scale": 50.0,            # 고정 (스윕 폐기 — 계수는 문제 아니었음)
                "win_reward": 100.0,
                "wez_threat_penalty": 0.0,
                "draw_reward": 0.0,
            },
            # Stage1과 동일 초기분포 (변수는 보상만)
            randomization={
                "enabled": True,
                "radius": 500.0,
                "r_roll": 5.0,
                "r_pitch": 5.0,
                "r_heading": 10.0,
            },
            # v13 하드닝: 이 스테이지만 어려운 loiter(bank 30)로 → 난이도 램프(15→30)
            env_overrides={"target_loiter": {"bank": 30.0}},
            # auto-advance 비활성화 (nan 오진급 버그 회피). 고정 iter + 최적 checkpoint 수동 선택.
            advance_conditions={},
            advance_window=20,
        ),
    ]

__all__ = ["get_stages"]