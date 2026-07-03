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
            description="생존과 스로틀 제어. 고정 타겟.",
            target_mode="fixed",              # 적은 고정(정지) 상태
            episode_step_limit=3600,          # 60초
            max_iterations=300,               # 생존 ~240 수렴 + 안정, 붕괴(~360) 전 (탄탄 베이스)
            checkpoint_interval=10,           # 10 iteration마다 저장
            reward_overrides={
                # ── 켜는 것 (생존) ──
                "survival_bonus": 0.05,       # 살아있으면 매 프레임 +
                "low_altitude_penalty": 1.0,  # 낮게 날면 강한 벌 (기본 0.1의 10배)
                "loss_reward": -50.0,         # 추락하면 벌
                # ── 끄는 것 (0으로) ──
                "pursuit_scale": 0.0,         # 추격 끔
                "positioning_scale": 0.0,     # 위치 끔
                "wez_bonus": 0.0,             # 공격 끔
                "wez_threat_penalty": 0.0,    # 회피 끔
                "damage_scale": 0.0,          # 전투 끔
                "win_reward": 0.0,            # 이기든 말든 무관
                "draw_reward": 0.0,
            },
            randomization={
                "enabled": True,
                "radius": 1.0,
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
            target_mode="loiter",              # [핵심] 적기가 가만히 있지 않고 선회 비행을 시작함!
            episode_step_limit=3600,          # 60초 제한시간 유지
            max_iterations=400,               # 탄탄한 추격 tail = 베이스라인 핵심(BT팀 전달용)
            checkpoint_interval=10,           # 10 iter마다 저장 (30개 ≈ 90MB, 디스크 절약)
            reward_overrides={
                # ── 1. 기본 비행 유지 (Stage 0의 학습 내용 보존) ──
                "survival_bonus": 0.02,       # 비행은 이미 잘하므로 생존 보상은 살짝 낮춤
                "low_altitude_penalty": 0.8,  # pursuit 켜지므로 고도규율 강하게 유지(0.5→0.8, 붕괴 재발 방지)
                "loss_reward": -100.0,        # 추락하면 여전히 큰 페널티
                
                # ── 2. 공격/추격 신호 ON (지안 님 my_reward.py의 핵심 장치들 작동) ──
                "pursuit_scale": 0.4,         # [ON] 내 기수를 적에게 향할 때(ATA 감소) 보상 부여 시작!
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
            target_mode="loiter",             # Step2: 실전형 선회 적. 새 관측(적 속도)으로 리드 학습
            episode_step_limit=3600,          # 60초
            max_iterations=1500,              # 사격은 어려움 → 충분한 학습량. 개선 지속 시 연장
            checkpoint_interval=20,           # 800 iter → 20마다 (40개, 디스크 절약)
            reward_overrides={
                # ── 기본 비행/생존 (조준하다 강하→추락 억제 위해 고도규율 강화) ──
                "survival_bonus": 0.02,
                "low_altitude_penalty": 1.5,     # 추락 40% → 1.0→1.5 강화
                "loss_reward": -100.0,
                # ── 코스 추적: stage1 수준으로 복원(0.4). v2의 0.2는 추적을 망침(replay 확인) ──
                "pursuit_scale": 0.4,
                "pursuit_half_angle_deg": 180.0, # dead-zone 제거: 전각도 추적 gradient(81°서 굳던 문제 해결)
                "pursuit_range_m": 4000.0,
                "positioning_scale": 0.15,
                # ── ★정밀 조준: 밴드 안 ATA→0 급상승. τ=15로 완만화(33°→10° 구간에 gradient) ──
                "aim_scale": 0.6,                # 주 정밀 조준 신호
                "aim_tau_deg": 15.0,             # v2의 3°는 너무 날카로워 밴드내 33°서 신호≈0이었음
                "optimal_range_m": 300.0,        # 152m 위 안전마진 + 데미지 높은 지점
                # ── 과접근 방지 (v1의 16m 파고들기 차단) ──
                "too_close_penalty": 0.5,
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
            # auto-advance 비활성화 (nan 오진급 버그 회피). 고정 iter + 최적 checkpoint 수동 선택.
            advance_conditions={},
            advance_window=20,
        ),
    ]

__all__ = ["get_stages"]