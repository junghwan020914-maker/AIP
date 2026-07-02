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
            max_iterations=300,               # 400 iteration 정도 충분히 배정
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
            max_iterations=300,               # 변수가 늘어났으므로 300~400 iter 정도 충분히 배정
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
        )
    ]

__all__ = ["get_stages"]