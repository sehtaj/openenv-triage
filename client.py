# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Client for the operational risk triage environment."""

from typing import Any

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

try:
    from .models import TaskName, TriageAction, TriageObservation, TriageState
except ImportError:
    from models import TaskName, TriageAction, TriageObservation, TriageState  # type: ignore


class RiskTriageEnv(EnvClient[TriageAction, TriageObservation, TriageState]):
    """Typed OpenEnv client for deterministic operational risk triage episodes."""

    def _step_payload(self, action: TriageAction) -> dict[str, Any]:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: dict[str, Any]) -> StepResult[TriageObservation]:
        observation_payload = dict(payload.get("observation", {}))
        observation_payload["done"] = payload.get("done", observation_payload.get("done", False))
        observation_payload["reward"] = payload.get("reward", observation_payload.get("reward"))
        observation = TriageObservation.model_validate(observation_payload)
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict[str, Any]) -> TriageState:
        return TriageState.model_validate(payload)

    async def reset_for_task(
        self,
        task: TaskName,
        *,
        seed: int | None = None,
        episode_id: str | None = None,
    ) -> StepResult[TriageObservation]:
        """Convenience wrapper for deterministic task selection."""

        return await self.reset(task=task, seed=seed, episode_id=episode_id)


# Backwards-compatible alias while the package name remains `my_env`.
MyEnv = RiskTriageEnv
