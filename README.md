---
title: Operational Risk Triage Environment
emoji: 🚦
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Operational Risk Triage Environment

This repository hosts a deterministic OpenEnv environment for operational decision-making under uncertainty and distribution shift. The agent processes a queue of cases and must choose exactly one action per case:

- `accept`
- `reject`
- `review`

The workflow is grounded in a fraud-like approval pipeline, with moderation-style ambiguity and anomaly-style OOD behavior introduced through the `easy`, `medium`, and `hard` tasks.

## Current Stage

The core environment, deterministic task bank, and deterministic grader are now in place:

- typed decision and observation models
- deterministic multi-case queue handling
- explicit task selection via `reset(task="easy" | "medium" | "hard")`
- fixed review budgets per task
- task-bank calibration against naive shortcut policies
- deterministic raw business-value grading with normalized episode scores
- baseline `inference.py` entrypoint using the OpenAI client

## Quick Start

### Run the server locally

```bash
uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
```

### Interact with the environment

```python
from client import RiskTriageEnv
from models import TriageAction

client = RiskTriageEnv(base_url="http://localhost:8000").sync()

with client:
    result = client.reset(task="easy")
    print(result.observation.current_case.case_id)
    print(result.observation.current_case.evidence_text)

    result = client.step(
        TriageAction(
            decision="review",
            rationale="Signals conflict and review budget is still available.",
            confidence=0.62,
        )
    )
    print(result.reward, result.done)
```

### Run the baseline entrypoint

```bash
API_BASE_URL=https://your-model-endpoint/v1 \
MODEL_NAME=gpt-4.1-mini \
HF_TOKEN=your_token \
OPENAI_API_KEY=your_api_key \
.venv/bin/python inference.py --env-url http://localhost:8000 --task easy
```

### Required environment variables

- `API_BASE_URL`: model endpoint base URL
- `MODEL_NAME`: model identifier used by `inference.py`
- `HF_TOKEN`: token passed through for gated deployment scenarios
- `OPENAI_API_KEY`: optional API key used by the OpenAI client if required by the target endpoint

## Environment Contract

### Action

`TriageAction`

- `decision`: one of `accept`, `reject`, `review`
- `rationale`: short explanation of the action
- `confidence`: optional score in `[0.0, 1.0]`

### Observation

`TriageObservation` exposes:

- the current visible case record
- queue progress and remaining review budget
- cumulative raw reward, normalized score, and action counts
- deterministic feedback for the previous action

The visible case includes:

- contextual identifiers: `case_id`, `task_name`, `domain_hint`, `event_type`
- structured signals: `impact_score`, `risk_score`, `anomaly_score`, `history_risk_score`
- model outputs: `model_recommendation`, `model_confidence`
- uncertainty and novelty: `uncertainty_score`, `novelty_score`
- evidence quality: `feature_completeness`, `policy_flags`, `missing_fields`
- analyst-style summary: `evidence_text`

### Tasks

- `easy`: 20 cases, review budget 4
- `medium`: 25 cases, review budget 4
- `hard`: 30 cases, review budget 3

All tasks share the same API and differ only in ambiguity, missing evidence, and OOD behavior.

## Review Semantics

`review` always means bounded human escalation, but the operational interpretation differs by domain:

- `payment`: send the transaction or account event to a manual fraud analyst queue
- `content`: send the content or account action to a human moderation queue
- `system`: send the anomaly or operational event to a human investigation queue

In all three domains, `review` resolves the current case immediately in the environment, consumes review budget, and carries an explicit cost.

## Scoring

The environment uses two related score views:

- `reward` and `cumulative_reward` are raw business-value signals used during the episode
- `normalized_score` is the public evaluation score clipped into `[0.0, 1.0]`

Normalization is deterministic:

```text
normalized_score = clip(raw_score / raw_score_optimal, 0.0, 1.0)
```

Where:

- `raw_score` is the total business value earned by the agent
- `raw_score_optimal` is the deterministic hidden-policy optimum for that task

This means:

- positive but suboptimal play earns partial credit
- net-negative business value earns `0.0`
- the best possible task episode earns `1.0`

Aggregate evaluation across `easy`, `medium`, and `hard` is the arithmetic mean of the three normalized task scores.

## Reward Philosophy

- false accepts are penalized most heavily because they allow harmful events through
- false rejects are penalized materially but less than false accepts
- review has a small explicit cost and is only optimal on genuinely ambiguous cases
- step rewards are raw business-value signals and final episode scores are normalized for evaluation

This means the interaction reward and the final grader are aligned: the normalized episode score is derived directly from accumulated raw business value rather than a separate contradictory objective.

The baseline script prints only these line types:

```text
[START] task=<task_name> env=<env_name> model=<model_name>
[STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END] success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
```

## Project Structure

```text
my_env/
├── AGENTS.md
├── RULES.md
├── __init__.py
├── client.py
├── inference.py
├── models.py
├── openenv.yaml
├── pyproject.toml
├── README.md
├── PROGRESS.md
├── tests/
│   ├── test_environment.py
│   └── test_grader.py
├── validate-submission.sh
└── server/
    ├── app.py
    ├── grader.py
    ├── my_env_environment.py
    ├── task_bank.py
    └── Dockerfile
```

## Docker

Build the environment image with:

```bash
docker build -t operational-risk-triage:latest -f server/Dockerfile .
```

## Deployment

This repo follows the standard OpenEnv layout and can be deployed to Hugging Face Spaces with:

```bash
openenv push
```

## Validation

Run the local submission checks with:

```bash
./validate-submission.sh
```

Run the local OpenEnv validator directly with:

```bash
openenv validate
```

## Determinism

- deterministic task seeds are centralized in [server/task_bank.py](/Users/sehtaj/githubRepos/my_env/server/task_bank.py)
- the task bank is bundled directly in the repository
- the environment does not download task data or fixtures at runtime
