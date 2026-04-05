# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Deterministic baseline inference entrypoint with strict log formatting."""

from __future__ import annotations

import argparse
import os
from typing import Iterable

from openai import OpenAI

try:
    from client import RiskTriageEnv
    from models import Decision, TaskName, TriageAction, TriageObservation
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("Run inference.py from the repository root.") from exc


ENV_NAME = "operational_risk_triage"
HIGH_RISK_FLAGS = {
    "velocity_spike",
    "credential_reset",
    "gift_card_cluster",
    "checkout_fanout",
    "identity_fragmentation",
    "linked_chargeback_cluster",
}


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _sanitize_error(message: str) -> str:
    compact = "_".join(message.strip().split())
    return compact or "runtime_error"


def _format_reward(value: float) -> str:
    return f"{value:.2f}"


def _format_score(value: float | None) -> str:
    if value is None:
        return "0.000000"
    return f"{value:.6f}"


def _format_rewards(values: Iterable[float]) -> str:
    return ",".join(_format_reward(value) for value in values)


def _decision_for_observation(observation: TriageObservation) -> Decision:
    case = observation.current_case
    if case is None:
        return "review"

    if (
        case.risk_score >= 0.79
        or case.anomaly_score >= 0.82
        or any(flag in HIGH_RISK_FLAGS for flag in case.policy_flags)
    ):
        return "reject"
    if case.model_recommendation == "review" and observation.remaining_review_budget > 0:
        return "review"
    if (
        observation.remaining_review_budget > 0
        and case.uncertainty_score >= 0.66
        and case.novelty_score >= 0.24
    ):
        return "review"
    if (
        case.risk_score <= 0.30
        and case.anomaly_score <= 0.35
        and case.history_risk_score <= 0.30
    ):
        return "accept"
    if case.model_recommendation == "review" and observation.remaining_review_budget == 0:
        return "reject"
    return case.model_recommendation


def run_episode(
    env_url: str,
    task: TaskName,
    api_base_url: str | None,
    model_name: str,
    hf_token: str | None,
) -> int:
    api_key = os.environ.get("OPENAI_API_KEY") or hf_token or "dummy"
    _model_client = OpenAI(base_url=api_base_url, api_key=api_key)

    rewards: list[float] = []
    steps = 0
    final_score = 0.0

    print(f"[START] task={task} env={ENV_NAME} model={model_name}")

    try:
        env = RiskTriageEnv(base_url=env_url).sync()
        with env:
            result = env.reset(task=task)

            while not result.done:
                action = _decision_for_observation(result.observation)
                error_value = "null"
                reward_value = 0.0
                try:
                    result = env.step(
                        TriageAction(
                            decision=action,
                            rationale="Deterministic rule-based baseline.",
                        )
                    )
                    reward_value = float(result.reward or 0.0)
                    rewards.append(reward_value)
                    steps += 1
                except Exception as exc:  # pragma: no cover
                    error_value = _sanitize_error(str(exc))
                    print(
                        f"[STEP] step={steps + 1} action={action} reward={_format_reward(0.0)} "
                        f"done=true error={error_value}"
                    )
                    print(
                        f"[END] success=false steps={steps} score={_format_score(final_score)} "
                        f"rewards={_format_rewards(rewards)}"
                    )
                    return 1

                final_score = float(result.observation.normalized_score or 0.0)
                print(
                    f"[STEP] step={steps} action={action} reward={_format_reward(reward_value)} "
                    f"done={_bool_text(result.done)} error={error_value}"
                )

            final_state = env.state()
            final_score = float(final_state.normalized_score or 0.0)
    except Exception as exc:  # pragma: no cover
        print(
            f"[END] success=false steps={steps} score={_format_score(final_score)} "
            f"rewards={_format_rewards(rewards)}"
        )
        return 1

    print(
        f"[END] success=true steps={steps} score={_format_score(final_score)} "
        f"rewards={_format_rewards(rewards)}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-url", default="http://localhost:8000")
    parser.add_argument("--task", choices=["easy", "medium", "hard"], default="easy")
    args = parser.parse_args()

    api_base_url = os.environ.get("API_BASE_URL")
    model_name = os.environ.get("MODEL_NAME", "gpt-4.1-mini")
    hf_token = os.environ.get("HF_TOKEN")

    return run_episode(
        env_url=args.env_url,
        task=args.task,
        api_base_url=api_base_url,
        model_name=model_name,
        hf_token=hf_token,
    )


if __name__ == "__main__":
    raise SystemExit(main())
