"""Regression tests for baseline inference formatting."""

from __future__ import annotations

import os
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from openenv.core.client_types import StepResult

import inference
from models import TriageCaseView, TriageObservation, TriageState


def _current_case() -> TriageCaseView:
    return TriageCaseView(
        case_id="easy-001",
        task_name="easy",
        domain_hint="payment",
        event_type="card_payment",
        impact_score=10,
        risk_score=0.10,
        anomaly_score=0.10,
        history_risk_score=0.10,
        model_recommendation="accept",
        model_confidence=0.99,
        uncertainty_score=0.05,
        novelty_score=0.05,
        feature_completeness=0.95,
        policy_flags=["known_customer"],
        missing_fields=[],
        evidence_text="Known good customer.",
        queue_position=1,
        remaining_cases=1,
        remaining_review_budget=0,
    )


def _observation(*, done: bool, normalized_score: float | None) -> TriageObservation:
    return TriageObservation(
        task_name="easy",
        episode_status="completed" if done else "in_progress",
        current_case=None if done else _current_case(),
        cases_total=2,
        processed_cases=2 if done else 1,
        remaining_cases=0 if done else 1,
        remaining_review_budget=0,
        cumulative_reward=6.0 if done else 3.0,
        normalized_score=normalized_score,
        raw_score_min=-10.0,
        raw_score_max=10.0,
        raw_score_optimal=6.0,
        accepted_count=2 if done else 1,
        rejected_count=0,
        reviewed_count=0,
        last_decision="accept",
        last_feedback="ok",
        last_outcome_category="correct_accept",
        done=done,
        reward=3.0 if done else 3.0,
    )


class _FakeSyncEnv:
    def __init__(self, *args, **kwargs) -> None:
        del args, kwargs
        self._steps = 0

    def sync(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    def reset(self, **kwargs):
        del kwargs
        self._steps = 0
        return StepResult(
            observation=_observation(done=False, normalized_score=0.5),
            reward=None,
            done=False,
        )

    def step(self, action):
        del action
        self._steps += 1
        done = self._steps >= 2
        return StepResult(
            observation=_observation(done=done, normalized_score=0.99 if done else 0.5),
            reward=3.0,
            done=done,
        )

    def state(self):
        return TriageState(
            episode_id="episode-1",
            step_count=2,
            task_name="easy",
            episode_status="completed",
            cases_total=2,
            processed_cases=2,
            remaining_cases=0,
            review_budget_total=0,
            remaining_review_budget=0,
            cumulative_reward=6.0,
            normalized_score=0.99,
            raw_score_min=-10.0,
            raw_score_max=10.0,
            raw_score_optimal=6.0,
            accepted_count=2,
            rejected_count=0,
            reviewed_count=0,
            last_decision="accept",
            last_feedback="ok",
            last_outcome_category="correct_accept",
        )


def test_run_episode_emits_only_required_log_lines() -> None:
    buffer = StringIO()

    with (
        patch.object(inference, "RiskTriageEnv", _FakeSyncEnv),
        patch.object(inference, "_llm_enabled", lambda api_base_url: False),
        redirect_stdout(buffer),
    ):
        exit_code = inference.run_episode(
            env_url="http://example.com",
            task="easy",
            api_base_url=None,
            model_name="gpt-4.1-mini",
            hf_token=None,
        )

    lines = buffer.getvalue().strip().splitlines()

    assert exit_code == 0
    assert len(lines) == 4
    assert lines[0] == "[START] task=easy env=operational_risk_triage model=gpt-4.1-mini"
    assert lines[1] == "[STEP] step=1 action=accept reward=3.00 done=false error=null"
    assert lines[2] == "[STEP] step=2 action=accept reward=3.00 done=true error=null"
    assert lines[3] == "[END] success=true steps=2 score=0.99 rewards=3.00,3.00"


def test_run_episode_makes_one_proxy_openai_call_without_changing_logs() -> None:
    buffer = StringIO()
    client_inits: list[tuple[str | None, str | None]] = []
    proxy_calls: list[dict[str, object]] = []

    class _FakeChatCompletions:
        def create(self, **kwargs):
            proxy_calls.append(kwargs)
            return type(
                "_Response",
                (),
                {
                    "choices": [
                        type(
                            "_Choice",
                            (),
                            {
                                "message": type(
                                    "_Message",
                                    (),
                                    {"content": "review"},
                                )()
                            },
                        )()
                    ]
                },
            )()

    class _FakeClient:
        def __init__(self, *, base_url=None, api_key=None):
            client_inits.append((base_url, api_key))
            self.chat = type(
                "_Chat",
                (),
                {"completions": _FakeChatCompletions()},
            )()

    with (
        patch.dict(
            os.environ,
            {
                "API_BASE_URL": "https://proxy.example/v1",
                "OPENAI_API_KEY": "proxy-key",
            },
            clear=False,
        ),
        patch.object(inference, "OpenAI", _FakeClient),
        patch.object(inference, "RiskTriageEnv", _FakeSyncEnv),
        redirect_stdout(buffer),
    ):
        exit_code = inference.run_episode(
            env_url="http://example.com",
            task="easy",
            api_base_url=None,
            model_name="gpt-4.1-mini",
            hf_token=None,
        )

    lines = buffer.getvalue().strip().splitlines()

    assert exit_code == 0
    assert client_inits[:2] == [
        ("https://proxy.example/v1", "proxy-key"),
        ("https://proxy.example/v1", "proxy-key"),
    ]
    assert len(proxy_calls) == 1
    assert proxy_calls[0]["model"] == "gpt-4.1-mini"
    assert lines[0] == "[START] task=easy env=operational_risk_triage model=gpt-4.1-mini"
    assert lines[1] == "[STEP] step=1 action=accept reward=3.00 done=false error=null"
    assert lines[2] == "[STEP] step=2 action=accept reward=3.00 done=true error=null"
    assert lines[3] == "[END] success=true steps=2 score=0.99 rewards=3.00,3.00"


def test_run_episode_uses_api_key_fallback_for_proxy_call() -> None:
    client_inits: list[tuple[str | None, str | None]] = []
    proxy_calls = 0

    class _FakeChatCompletions:
        def create(self, **kwargs):
            nonlocal proxy_calls
            del kwargs
            proxy_calls += 1
            return type(
                "_Response",
                (),
                {
                    "choices": [
                        type(
                            "_Choice",
                            (),
                            {
                                "message": type(
                                    "_Message",
                                    (),
                                    {"content": "review"},
                                )()
                            },
                        )()
                    ]
                },
            )()

    class _FakeClient:
        def __init__(self, *, base_url=None, api_key=None):
            client_inits.append((base_url, api_key))
            self.chat = type(
                "_Chat",
                (),
                {"completions": _FakeChatCompletions()},
            )()

    with (
        patch.dict(
            os.environ,
            {
                "API_BASE_URL": "https://proxy.example/v1",
                "API_KEY": "validator-key",
            },
            clear=True,
        ),
        patch.object(inference, "OpenAI", _FakeClient),
        patch.object(inference, "RiskTriageEnv", _FakeSyncEnv),
    ):
        exit_code = inference.run_episode(
            env_url="http://example.com",
            task="easy",
            api_base_url=None,
            model_name="gpt-4.1-mini",
            hf_token=None,
        )

    assert exit_code == 0
    assert client_inits[:2] == [
        ("https://proxy.example/v1", "validator-key"),
        ("https://proxy.example/v1", "validator-key"),
    ]
    assert proxy_calls == 1
