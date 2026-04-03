# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Baseline inference entrypoint for the operational risk triage environment."""

from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any

from openai import OpenAI

try:
    from client import RiskTriageEnv
    from models import Decision, TaskName, TriageAction, TriageObservation
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("Run inference.py from the repository root.") from exc


SYSTEM_PROMPT = """You are an operational risk triage agent.
Decide exactly one action for the current case: accept, reject, or review.
Return valid JSON with keys: decision, rationale, confidence.
Use review sparingly and only when the evidence is genuinely ambiguous.
"""


def _build_user_prompt(observation: TriageObservation) -> str:
    if observation.current_case is None:
        return "The episode is complete. No action is required."

    payload = {
        "task_name": observation.task_name,
        "remaining_review_budget": observation.remaining_review_budget,
        "processed_cases": observation.processed_cases,
        "remaining_cases": observation.remaining_cases,
        "current_case": observation.current_case.model_dump(),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _extract_action(text: str, observation: TriageObservation) -> TriageAction:
    decision: Decision | None = None
    rationale = ""
    confidence: float | None = None

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match is not None:
        try:
            data = json.loads(match.group(0))
            raw_decision = str(data.get("decision", "")).strip().lower()
            if raw_decision in {"accept", "reject", "review"}:
                decision = raw_decision  # type: ignore[assignment]
            rationale = str(data.get("rationale", "")).strip()
            raw_confidence = data.get("confidence")
            if raw_confidence is not None:
                confidence = max(0.0, min(1.0, float(raw_confidence)))
        except (ValueError, TypeError):
            pass

    if decision is None:
        fallback_match = re.search(r"\b(accept|reject|review)\b", text.lower())
        if fallback_match is not None:
            decision = fallback_match.group(1)  # type: ignore[assignment]

    if decision is None and observation.current_case is not None:
        recommendation = observation.current_case.model_recommendation
        if recommendation == "review" and observation.remaining_review_budget == 0:
            decision = "reject"
        else:
            decision = recommendation

    return TriageAction(
        decision=decision or "review",
        rationale=rationale or "Fallback to deterministic parser output.",
        confidence=confidence,
    )


def _model_decision(
    model_client: OpenAI,
    model_name: str,
    observation: TriageObservation,
) -> TriageAction:
    response = model_client.chat.completions.create(
        model=model_name,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(observation)},
        ],
    )
    content = response.choices[0].message.content or ""
    return _extract_action(content, observation)


def run_episode(
    env_url: str,
    task: TaskName,
    model_base_url: str | None,
    model_name: str,
    hf_token: str | None,
    max_steps: int | None,
) -> dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY") or hf_token or "dummy"
    model_client = OpenAI(base_url=model_base_url, api_key=api_key)

    env = RiskTriageEnv(base_url=env_url).sync()
    with env:
        result = env.reset(task=task)
        steps = 0
        rewards: list[float] = []

        while not result.done:
            if max_steps is not None and steps >= max_steps:
                break
            action = _model_decision(model_client, model_name, result.observation)
            result = env.step(action)
            rewards.append(float(result.reward or 0.0))
            steps += 1
            print(
                json.dumps(
                    {
                        "step": steps,
                        "decision": action.decision,
                        "reward": result.reward,
                        "done": result.done,
                        "feedback": result.observation.last_feedback,
                    }
                )
            )

        final_state = env.state()

    summary = {
        "task": task,
        "steps": steps,
        "cumulative_reward": round(sum(rewards), 3),
        "remaining_review_budget": final_state.remaining_review_budget,
        "accepted_count": final_state.accepted_count,
        "rejected_count": final_state.rejected_count,
        "reviewed_count": final_state.reviewed_count,
    }
    print(json.dumps({"summary": summary}, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-url", default="http://localhost:8000")
    parser.add_argument("--task", choices=["easy", "medium", "hard"], default="easy")
    parser.add_argument("--max-steps", type=int, default=None)
    args = parser.parse_args()

    model_base_url = os.environ.get("API_BASE_URL")
    model_name = os.environ.get("MODEL_NAME", "gpt-4.1-mini")
    hf_token = os.environ.get("HF_TOKEN")

    run_episode(
        env_url=args.env_url,
        task=args.task,
        model_base_url=model_base_url,
        model_name=model_name,
        hf_token=hf_token,
        max_steps=args.max_steps,
    )


if __name__ == "__main__":
    main()
