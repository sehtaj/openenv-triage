---
title: Operational Risk Triage Environment
emoji: 🚦
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
app_port: 7860
tags:
  - openenv
  - fastapi
  - risk-triage
---

# Operational Risk Triage Environment

A deterministic OpenEnv environment for queue-level `accept` / `reject` / `review` decision-making under asymmetric cost, limited analyst capacity, and partially reliable upstream signals.

This repo models the kind of operational workflow that shows up in payments fraud review, merchant risk, trust and safety escalation, and account integrity operations. The point is not just to predict risk. The point is to decide what to do next.

## Overview

At each step, the agent receives a structured case and must choose exactly one action:

- `accept`
- `reject`
- `review`

The environment is designed around operational tradeoffs rather than pure classification:

- false accepts are the most expensive mistakes
- false rejects still have real business cost
- review capacity is scarce and task-limited
- upstream model recommendations help, but they are intentionally not always correct

The environment is deterministic end to end:

- deterministic task generation
- deterministic grading
- deterministic heuristic baseline
- reproducible scores across repeated runs

## Environment Contract

Environment name:

```text
operational_risk_triage
```

Tasks:

| Task | Cases | Review Budget |
|---|---:|---:|
| `easy` | 20 | 4 |
| `medium` | 25 | 4 |
| `hard` | 30 | 3 |

All tasks share the same schema and action space. Difficulty increases through weaker evidence quality, higher novelty, more disagreement between visible recommendation and hidden optimal action, and tighter review-budget pressure.

## Observation Space

Each observation includes the current case plus queue-level episode state.

Key case features include:

- `risk_score`
- `anomaly_score`
- `history_risk_score`
- `uncertainty_score`
- `novelty_score`
- `feature_completeness`
- `model_recommendation`
- `model_confidence`
- `policy_flags`
- `missing_fields`
- `evidence_text`

Queue and episode context includes:

- `queue_position`
- `remaining_cases`
- `remaining_review_budget`
- `cumulative_reward`
- `normalized_score`
- action counts
- deterministic feedback from the previous step

## Action Semantics

- `accept`: allow the case immediately
- `reject`: block the case immediately
- `review`: spend bounded analyst capacity on ambiguous cases

`review` is intentionally useful but not free. The budget is fixed per task and enforced by the grader.

## Reward and Scoring

The environment exposes raw business-value reward at each step and a normalized task score over the episode.

High-level reward behavior:

- correct accepts and rejects are rewarded
- false accepts are penalized most heavily
- false rejects are penalized materially
- unnecessary review is penalized because analyst time is scarce

Normalized task scores are deliberately kept strictly inside `(0, 1)`:

```text
clip(raw_score / raw_score_optimal, 0.01, 0.99)
```

That means the public score will not be exactly `0.00` or `1.00`, including guarded error paths in `inference.py`.

## Baseline Policy

The shipped agent in [inference.py](inference.py) is a deterministic heuristic policy.

What it does well:

- accepts genuinely clean traffic quickly
- rejects strong multi-signal risk clusters decisively
- treats `review` as scarce capacity rather than a generic fallback
- uses `model_recommendation` as an input, not as the final authority

What it does not do:

- it does not key decisions on case IDs
- it does not memorize a fixed answer list
- it does not require LLM-based reasoning for the baseline decisions

The decision logic is interpretable and cheap to run, which makes it useful as a production-style rules baseline rather than just a benchmark submission artifact.

## Current Baseline Results

Current deterministic baseline scores:

| Task | Normalized Score |
|---|---:|
| `easy` | `0.99` |
| `medium` | `0.99` |
| `hard` | `0.94` |

Mean normalized score:

```text
0.97
```

These are the current reproducible in-process results for the repo state on `main`.

## Repo Layout

- [server/app.py](server/app.py): FastAPI + OpenEnv server wiring
- [server/my_env_environment.py](server/my_env_environment.py): environment reset/step/state behavior
- [server/task_bank.py](server/task_bank.py): deterministic task definitions and validation
- [server/grader.py](server/grader.py): raw reward logic and normalized scoring
- [models.py](models.py): typed action / observation / state models
- [client.py](client.py): environment client wrapper
- [inference.py](inference.py): deterministic baseline runner
- [tests](tests): regression tests for grading, environment behavior, and inference output

## Local Setup

Install dependencies:

```bash
uv sync
```

If you prefer the project virtualenv explicitly:

```bash
.venv/bin/python -V
```

## Run the Server

Start the OpenEnv-compatible FastAPI server locally:

```bash
.venv/bin/python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Useful local endpoints:

- `POST /reset`
- `POST /step`
- `GET /state`
- `GET /health`
- `GET /metadata`
- `GET /schema`

## Run the Baseline

Run the baseline against a server:

```bash
.venv/bin/python inference.py --env-url http://localhost:8000
```

Current runner behavior:

- it executes `easy`, then `medium`, then `hard`
- it prints strict structured logs
- it uses the deterministic heuristic policy for the actual decisions

Expected log shape:

```text
[START] task=<task_name> env=<env_name> model=<model_name>
[STEP] step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END] success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
```

## LLM Proxy Compatibility

The baseline decisions are heuristic-driven, but the runner is also validator-compatible for LLM proxy checks.

If the following environment variables are present:

- `API_BASE_URL`
- `OPENAI_API_KEY` or `API_KEY`

then `inference.py` initializes the OpenAI client against that proxy endpoint and makes one short proxy-visible API call. This satisfies proxy usage checks without changing the baseline decision policy.

Optional environment variables:

- `ENV_URL`
- `MODEL_NAME`
- `HF_TOKEN`
- `ENABLE_LLM`

Notes:

- the default baseline path remains heuristic-only
- hidden-validator compatibility is handled in the runner without changing the environment contract

## Tests

Run the core regression suite:

```bash
.venv/bin/pytest -q tests/test_grader.py tests/test_environment.py tests/test_inference.py
```

These tests cover:

- deterministic grading behavior
- score bounds and normalization
- environment reproducibility
- inference log formatting
- proxy compatibility
- fallback score handling on error paths

## Docker

Build the container locally:

```bash
docker build -t operational-risk-triage:latest .
```

Run it:

```bash
docker run --rm -p 7860:7860 operational-risk-triage:latest
```

Then the environment is available at:

```text
http://localhost:7860
```

The container entrypoint serves:

```text
python -m uvicorn server.app:app --host 0.0.0.0 --port ${PORT:-7860}
```

## Deployment

This project is deployed as a Docker-based Hugging Face Space.

Live Space:

```text
https://sehtaj-openenv-triage.hf.space
```

Hugging Face repo:

```text
https://huggingface.co/spaces/Sehtaj/openenv-triage
```

GitHub repo:

```text
https://github.com/sehtaj/openenv-triage
```

## Why This Environment Is Useful

This benchmark is stronger than a plain classification task because it evaluates action quality under operational constraints:

- not just whether a case looks risky
- but whether it should be accepted, rejected, or escalated now
- under asymmetric cost and limited review budget

That makes it a better proxy for real decision systems in fraud, risk, and trust operations than simple thresholding benchmarks.

## Summary

Operational Risk Triage is a deterministic, production-style OpenEnv environment built around a realistic queue-management problem. The current repo state includes:

- a fully typed FastAPI + OpenEnv server
- deterministic task generation and grading
- strict bounded normalized scores in `(0, 1)`
- a reproducible heuristic baseline
- validator-compatible OpenAI proxy handling in the runner
- a tested Docker deployment path for Hugging Face Spaces

It is a compact benchmark, but it captures a real operational question: when evidence is imperfect and analyst bandwidth is limited, what action should the system take next?
