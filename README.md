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

Stage 1 converts the starter template into a production-shaped environment scaffold:

- typed decision and observation models
- deterministic multi-case queue handling
- explicit task selection via `reset(task="easy" | "medium" | "hard")`
- fixed review budgets per task
- baseline `inference.py` entrypoint using the OpenAI client

Task-bank calibration, richer grading analysis, and benchmark hardening continue in later stages.

## Quick Start

### Run the server locally

```bash
uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
```

### Interact with the environment

```python
from my_env import RiskTriageEnv, TriageAction

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
- cumulative reward and action counts
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

## Project Structure

```text
my_env/
├── __init__.py
├── client.py
├── inference.py
├── models.py
├── openenv.yaml
├── progress.md
├── pyproject.toml
├── README.md
└── server/
    ├── app.py
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
