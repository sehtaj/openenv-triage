"""Integration tests for deterministic environment behavior."""

from __future__ import annotations

from time import perf_counter
import tracemalloc

from openai import OpenAI
from pydantic import ValidationError
from inference import _decision_for_observation
from models import TriageAction
from server.my_env_environment import MyEnvironment


def _baseline_decision(observation):
    client = OpenAI(api_key="dummy")
    return _decision_for_observation(client, observation, llm_enabled=False)


def _run_baseline_episode(task: str) -> tuple[list[str], list[float], float]:
    env = MyEnvironment()
    observation = env.reset(task=task)
    actions: list[str] = []
    rewards: list[float] = []

    while not observation.done:
        decision = _baseline_decision(observation)
        actions.append(decision)
        observation = env.step(
            TriageAction(
                decision=decision,
                rationale="Deterministic test baseline.",
            )
        )
        rewards.append(float(observation.reward or 0.0))

    return actions, rewards, float(observation.normalized_score or 0.0)


def test_reset_initializes_deterministic_task_state() -> None:
    env = MyEnvironment()
    observation = env.reset(task="medium", episode_id="episode-medium")
    state = env.state

    assert observation.task_name == "medium"
    assert observation.current_case is not None
    assert observation.current_case.case_id == "medium-001"
    assert observation.processed_cases == 0
    assert observation.remaining_cases == 25
    assert observation.remaining_review_budget == 4
    assert observation.normalized_score is None
    assert state.episode_id == "episode-medium"
    assert state.episode_status == "ready"
    assert state.review_budget_total == 4
    assert state.raw_score_optimal > 0.0


def test_step_updates_state_and_completes_episode() -> None:
    env = MyEnvironment()
    observation = env.reset(task="easy")

    first_decision = _baseline_decision(observation)
    observation = env.step(TriageAction(decision=first_decision, rationale="first"))
    state = env.state

    assert observation.processed_cases == 1
    assert state.step_count == 1
    assert state.processed_cases == 1
    assert observation.last_decision == first_decision
    assert observation.last_outcome_category is not None
    assert observation.normalized_score is not None

    while not observation.done:
        next_decision = _baseline_decision(observation)
        observation = env.step(TriageAction(decision=next_decision, rationale="loop"))

    final_state = env.state
    assert observation.done is True
    assert observation.current_case is None
    assert observation.processed_cases == 20
    assert final_state.episode_status == "completed"
    assert final_state.processed_cases == 20
    assert 0.0 <= float(observation.normalized_score or 0.0) <= 1.0


def test_step_before_reset_raises_runtime_error() -> None:
    env = MyEnvironment()
    try:
        env.step(TriageAction(decision="accept", rationale="invalid_order"))
    except RuntimeError as exc:
        assert "reset" in str(exc).lower()
    else:  # pragma: no cover
        raise AssertionError("step() should raise before reset().")


def test_step_after_done_returns_stable_completed_observation() -> None:
    env = MyEnvironment()
    observation = env.reset(task="easy")
    while not observation.done:
        decision = _baseline_decision(observation)
        observation = env.step(TriageAction(decision=decision, rationale="complete"))

    completed = env.step(TriageAction(decision="accept", rationale="after_done"))

    assert completed.done is True
    assert completed.reward == 0.0
    assert completed.current_case is None
    assert "completed" in (completed.last_feedback or "").lower()


def test_invalid_action_payload_is_rejected_deterministically() -> None:
    try:
        TriageAction.model_validate({"decision": "escalate", "rationale": "invalid"})
    except ValidationError as exc:
        assert "decision" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Invalid decisions must be rejected by the typed action model.")


def test_parallel_environment_instances_do_not_share_state() -> None:
    env_easy = MyEnvironment()
    env_hard = MyEnvironment()

    obs_easy = env_easy.reset(task="easy", episode_id="easy-episode")
    obs_hard = env_hard.reset(task="hard", episode_id="hard-episode")

    for _ in range(3):
        obs_easy = env_easy.step(TriageAction(decision=_baseline_decision(obs_easy), rationale="easy"))
    for _ in range(2):
        obs_hard = env_hard.step(TriageAction(decision=_baseline_decision(obs_hard), rationale="hard"))

    state_easy = env_easy.state
    state_hard = env_hard.state

    assert state_easy.episode_id == "easy-episode"
    assert state_hard.episode_id == "hard-episode"
    assert state_easy.task_name == "easy"
    assert state_hard.task_name == "hard"
    assert state_easy.processed_cases == 3
    assert state_hard.processed_cases == 2


def test_baseline_policy_is_reproducible_for_all_tasks() -> None:
    first_pass = {task: _run_baseline_episode(task) for task in ("easy", "medium", "hard")}
    second_pass = {task: _run_baseline_episode(task) for task in ("easy", "medium", "hard")}

    assert first_pass == second_pass
    assert first_pass["easy"][2] == 1.0
    assert first_pass["medium"][2] == 1.0
    assert first_pass["hard"][2] == 0.941176


def test_local_baseline_runtime_is_lightweight() -> None:
    start = perf_counter()
    for task in ("easy", "medium", "hard"):
        _run_baseline_episode(task)
    elapsed = perf_counter() - start

    assert elapsed < 1.0


def test_repeated_resets_do_not_show_unbounded_memory_growth() -> None:
    tracemalloc.start()
    env = MyEnvironment()

    for _ in range(40):
        observation = env.reset(task="easy")
        while not observation.done:
            observation = env.step(
                TriageAction(
                    decision=_baseline_decision(observation),
                    rationale="memory_check",
                )
            )

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert current < 1_000_000
    assert peak < 2_500_000
