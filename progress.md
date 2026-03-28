# OOD Decision-Making Environment Progress Tracker

## Stage 0
### 0.1 Product Scope Lock
- [ ] Lock the environment name and one-sentence pitch around out-of-distribution decision-making for real-world AI operations.
- [ ] Lock the action space to exactly `accept`, `reject`, and `review`.
- [ ] Lock the primary decision workflow to match production-style triage rather than a toy classification loop.
- [ ] Lock the business objective as maximizing correct decisions while minimizing costly mistakes and unnecessary reviews.
- [ ] Lock the supported domains to fraud detection, anomaly detection, and moderation under one shared decision interface.
- [ ] Lock the target user of the environment as an LLM-driven decision agent with optional human-review escalation.

### 0.2 Real-World Scenario Definition
- [ ] Define how each case represents a realistic operational record instead of a synthetic single-field prompt.
- [ ] Define which fields are visible to the agent for every case.
- [ ] Define which fields remain hidden and are used only for grading.
- [ ] Define how uncertainty, ambiguity, and missing signals appear in observations.
- [ ] Define how review capacity is limited or penalized so `review` remains meaningful.
- [ ] Define why false accepts and false rejects have asymmetric business cost.

### 0.3 Success Criteria Lock
- [ ] Freeze the requirement for at least three tasks labeled easy, medium, and hard.
- [ ] Freeze the requirement that every task must be solvable through the same typed action interface.
- [ ] Freeze the requirement that grading is deterministic and normalized to the range `0.0` to `1.0`.
- [ ] Freeze the requirement that rewards are meaningful at each step and not purely terminal.
- [ ] Freeze the requirement that the final implementation must pass `openenv` validation.

## Stage 1
### 1.1 Repo Conversion Plan
- [ ] Replace the starter echo-environment assumptions in `README.md` with OOD decision-making language.
- [ ] Replace the starter action and observation schema in `models.py`.
- [ ] Replace the starter transition logic in `server/my_env_environment.py`.
- [ ] Confirm whether `client.py` remains the package client or is only kept for OpenEnv compatibility.
- [ ] Add a root-level `inference.py` file and reserve that exact filename for the baseline submission script.
- [ ] Decide whether new helper modules are needed for task generation, grading, prompts, and fixtures.

### 1.2 File Ownership Map
- [ ] Mark `models.py` as the source of truth for typed action and observation models.
- [ ] Mark `server/my_env_environment.py` as the source of truth for environment state, reset, and step behavior.
- [ ] Mark `server/app.py` as the source of truth for OpenEnv server wiring.
- [ ] Mark `openenv.yaml` as the source of truth for runtime metadata and entrypoint configuration.
- [ ] Mark `server/Dockerfile` as the source of truth for container build and launch.
- [ ] Mark `inference.py` as the source of truth for the baseline agent runner.

## Stage 2
### 2.1 Task Design
- [ ] Define the easy task with strong in-distribution signals and low ambiguity.
- [ ] Define the medium task with moderate distribution shift, missing fields, and mixed evidence.
- [ ] Define the hard task with strong OOD behavior, adversarial or conflicting features, and higher review pressure.
- [ ] Ensure all three tasks use the same action schema and grading API.
- [ ] Ensure all three tasks feel like operational decision queues rather than unrelated mini-games.
- [ ] Ensure each task has a clear narrative grounded in fraud, anomaly, or moderation workflows.
- [ ] Verify OpenEnv can enumerate and run all tasks programmatically

### 2.2 Case Schema Design
- [ ] Define the full case record structure for account, transaction, content, or event-level evidence.
- [ ] Define which numeric features are visible to the agent.
- [ ] Define which categorical features are visible to the agent.
- [ ] Define which free-text rationale or notes are visible to the agent.
- [ ] Define how task difficulty changes which fields are noisy, shifted, missing, or misleading.
- [ ] Define hidden ground-truth labels, hidden OOD tags, and hidden business cost fields for grading.

### 2.3 Episode Structure
- [ ] Define the episode length for each task.
- [ ] Define whether all tasks use the same number of cases or task-specific counts.
- [ ] Define how `reset()` selects the task and initial episode content.
- [ ] Define whether the environment supports explicit task selection through reset metadata or config.
- [ ] Define the terminal condition for the episode.
- [ ] Define how step count, processed cases, and remaining budget are tracked in state.

## Stage 3
### 3.1 Typed Model Redesign
- [ ] Replace `MyAction` with a typed action model that only permits valid decision actions.
- [ ] Add typed action fields for decision rationale, optional confidence, and optional review note if needed.
- [ ] Replace `MyObservation` with a typed observation model reflecting the current case, queue status, and recent feedback.
- [ ] Add typed observation fields for task name, difficulty, remaining cases, review budget, and cumulative metrics.
- [ ] Ensure all model fields have explicit types and clear field descriptions.
- [ ] Ensure no required field depends on ambiguous free-form runtime inference.

### 3.2 State Design
- [ ] Define the environment state object content beyond `episode_id` and `step_count`.
- [ ] Decide where the current task definition is stored.
- [ ] Decide where pending cases are stored.
- [ ] Decide where cumulative reward and score components are stored.
- [ ] Decide where review usage and error counts are stored.
- [ ] Decide which state fields are exposed through the OpenEnv `state` property versus kept internal.

### 3.3 Schema Stability
- [ ] Ensure the action schema remains stable across easy, medium, and hard tasks.
- [ ] Ensure the observation schema remains stable across all tasks and steps.
- [ ] Ensure all metadata keys are deterministic and documented.
- [ ] Ensure the schema supports OpenEnv serialization without custom hacks.
- [ ] Ensure the schema remains lightweight enough for sub-20-minute evaluation runs.

## Stage 4
### 4.1 Deterministic Task Bank
- [ ] Create a deterministic task bank for easy, medium, and hard episodes.
- [ ] Assign a fixed seed strategy so the same task definition always produces the same cases.
- [ ] Create realistic feature distributions for each domain scenario.
- [ ] Create explicit OOD shift patterns for medium and hard tasks.
- [ ] Create adversarial or borderline examples that make `review` strategically necessary.
- [ ] Create enough case diversity to prevent trivial one-rule policies from winning.

### 4.2 Data Quality Controls
- [ ] Verify every case has a single authoritative hidden label.
- [ ] Verify every case has a business cost profile for false accept, false reject, and review actions.
- [ ] Verify every case has enough visible evidence for an agent to justify its choice.
- [ ] Verify no case contains contradictory grading targets.
- [ ] Verify no task accidentally leaks hidden labels through visible fields.
- [ ] Verify task definitions are deterministic across local runs and container runs.

### 4.3 Difficulty Calibration
- [ ] Calibrate the easy task so a simple baseline can achieve a non-trivial but imperfect score.
- [ ] Calibrate the medium task so robust reasoning and review usage clearly outperform naive thresholds.
- [ ] Calibrate the hard task so OOD awareness matters and overconfident accept/reject behavior is punished.
- [ ] Verify task difficulty increases in a visible and defensible way from easy to hard.
- [ ] Verify the hard task is still tractable within hackathon runtime limits.

## Stage 5
### 5.1 Environment Reset Logic
- [ ] Redesign `reset()` in `server/my_env_environment.py` around task initialization instead of echo behavior.
- [ ] Ensure `reset()` creates a fresh episode id.
- [ ] Ensure `reset()` resets step count, cumulative reward, score counters, and review budget.
- [ ] Ensure `reset()` returns the first actionable observation immediately.
- [ ] Ensure `reset()` works deterministically for a given task selection and seed.
- [ ] Ensure the deployed Hugging Face Space responds successfully to `reset()`.

### 5.2 Environment Step Logic
- [ ] Redesign `step()` to consume one case decision per call.
- [ ] Validate the action before mutating state.
- [ ] Apply business-cost logic for `accept`.
- [ ] Apply business-cost logic for `reject`.
- [ ] Apply business-cost logic for `review`.
- [ ] Advance to the next case after scoring the current action.
- [ ] Mark `done` only when the episode is complete.
- [ ] Return updated observation, reward, done flag, and deterministic metadata on every step.
- [ ] Ensure invalid or malformed actions are handled deterministically with a fallback or penalty

### 5.3 Review Workflow Realism
- [ ] Define exactly what `review` means operationally for each domain scenario.
- [ ] Decide whether `review` resolves the case immediately or defers with a bounded penalty.
- [ ] Apply a measurable cost to overusing review.
- [ ] Prevent `review` from becoming a dominant always-safe policy.
- [ ] Ensure some borderline cases are best handled by `review`.
- [ ] Ensure some clearly labeled cases are worse if sent to `review`.

## Stage 6
### 6.1 Reward Function Design
- [ ] Define per-step reward contributions for correct `accept`, correct `reject`, and justified `review`.
- [ ] Define per-step penalties for costly false accepts.
- [ ] Define per-step penalties for costly false rejects.
- [ ] Define per-step penalties for wasteful review usage.
- [ ] Ensure the reward function is dense enough to guide agent behavior during the full episode.
- [ ] Ensure the reward function aligns with the final grader rather than rewarding contradictory behavior.

### 6.2 Score Normalization
- [ ] Define the deterministic mapping from raw business value to normalized score.
- [ ] Ensure every episode score is clipped or normalized into `0.0` to `1.0`.
- [ ] Ensure impossible edge cases cannot produce scores below `0.0` or above `1.0`.
- [ ] Define whether the public reward shown during steps matches the final normalized score or a shaped intermediate value.
- [ ] Define how aggregate score is computed across easy, medium, and hard tasks.

### 6.3 Anti-Shortcut Checks
- [ ] Verify an always-accept policy scores poorly on at least one task.
- [ ] Verify an always-reject policy scores poorly on at least one task.
- [ ] Verify an always-review policy scores poorly due to explicit review cost or budget pressure.
- [ ] Verify the optimal policy requires reading task evidence and reacting to OOD signals.

## Stage 7
### 7.1 Deterministic Grader Implementation
- [ ] Implement a deterministic grading path that uses only hidden task data and recorded actions.
- [ ] Ensure the grader has no dependence on model outputs other than the chosen action and allowed auxiliary fields.
- [ ] Ensure grading produces the same result across repeated runs.
- [ ] Ensure grading works for each step and for the final episode summary.
- [ ] Ensure grading handles invalid actions with a deterministic penalty path.

### 7.2 Grader Test Coverage
- [ ] Add tests for correct scoring of `accept` on positive and negative cases.
- [ ] Add tests for correct scoring of `reject` on positive and negative cases.
- [ ] Add tests for correct scoring of `review` on borderline and obvious cases.
- [ ] Add tests for review budget exhaustion behavior if a budget exists.
- [ ] Add tests for normalization boundaries at `0.0` and `1.0`.
- [ ] Add golden tests for one fully worked easy episode, one medium episode, and one hard episode.

### 7.3 Grader Transparency
- [ ] Define deterministic metadata fields that explain score components without leaking future labels.
- [ ] Ensure observation metadata is useful for debugging but does not reveal hidden truth before the action.
- [ ] Ensure final evaluation outputs are traceable to business-cost components.

## Stage 8
### 8.1 OpenEnv Client Compatibility
- [ ] Update `client.py` to parse the new observation schema correctly.
- [ ] Ensure the client continues to support `reset()`, `step()`, and `state()` operations.
- [ ] Ensure state parsing reflects the new episode counters and identifiers.
- [ ] Ensure package exports remain valid after model and environment renames.
- [ ] Ensure no starter echo-environment assumptions remain in client-side parsing.

### 8.2 Baseline Agent Contract
- [ ] Create `inference.py` at the repository root.
- [ ] Ensure `inference.py` uses the OpenAI client for inference.
- [ ] Ensure `inference.py` reads `API_BASE_URL` from the environment.
- [ ] Ensure `inference.py` reads `MODEL_NAME` from the environment.
- [ ] Ensure `inference.py` reads `HF_TOKEN` from the environment if deployment or gated assets require it.
- [ ] Ensure `inference.py` can connect to the running environment and complete an episode end-to-end.

### 8.3 Baseline Agent Behavior
- [ ] Define the system prompt for operational decision-making behavior.
- [ ] Define the user prompt format from the current observation.
- [ ] Define strict output parsing so the model only returns valid actions.
- [ ] Add retry or fallback behavior for malformed model responses.
- [ ] Log per-step decisions, rewards, and final score for debugging.
- [ ] Ensure the baseline finishes within the runtime budget.

## Stage 9
### 9.1 OpenEnv Server Wiring
- [ ] Update `server/app.py` so the app wires the final environment class and final models.
- [ ] Ensure the app still exposes the expected OpenEnv endpoints.
- [ ] Ensure the app works with local development and Docker execution.
- [ ] Ensure session behavior is correct for the intended concurrency model.
- [ ] Ensure `env_name` and runtime labels match the final project identity.

### 9.2 Manifest and Packaging
- [ ] Update `openenv.yaml` with the final valid spec fields.
- [ ] Verify the `app` target in `openenv.yaml` matches the deployed server entrypoint.
- [ ] Verify the port in `openenv.yaml` matches the runtime server port.
- [ ] Verify `pyproject.toml` metadata matches the final environment purpose.
- [ ] Verify package imports work both from source and inside the container.

### 9.3 Documentation
- [ ] Rewrite `README.md` around the OOD decision-making environment.
- [ ] Document the easy, medium, and hard tasks in `README.md`.
- [ ] Document the action semantics for `accept`, `reject`, and `review`.
- [ ] Document the reward and grading philosophy at a high level.
- [ ] Document required environment variables including `API_BASE_URL`, `MODEL_NAME`, and `HF_TOKEN`.
- [ ] Document local run, Docker run, and validation commands.

## Stage 10
### 10.1 Docker Build Path
- [ ] Update `server/Dockerfile` if new files or dependencies require different copy or install behavior.
- [ ] Ensure the Docker build completes from the repository root.
- [ ] Ensure the container starts the OpenEnv FastAPI app without manual patching.
- [ ] Ensure the container exposes the expected port and health endpoint.
- [ ] Ensure the container image contains `inference.py` if evaluation expects it in the project root.

### 10.2 Runtime Budget Validation
- [ ] Measure one full baseline run locally.
- [ ] Measure one full baseline run inside Docker.
- [ ] Verify the full evaluation path remains under 20 minutes on a 2 vCPU and 8 GB RAM budget.
- [ ] Reduce task size, prompt size, or model round-trips if runtime exceeds the budget.
- [ ] Re-run timing after every major change to task count or prompt format.

### 10.3 Resource Stability
- [ ] Verify memory usage remains stable across repeated resets.
- [ ] Verify no task generation path requires internet access at runtime.
- [ ] Verify deterministic fixtures are bundled with the repo if external downloads are not allowed.
- [ ] Verify there are no hidden heavyweight dependencies that slow cold start.
- [ ] Ensure no runtime dependency on external APIs or downloads (except LLM calls)

## Stage 11
### 11.1 Local Validation
- [ ] Run unit tests for models, environment logic, and grader behavior.
- [ ] Run integration tests for reset-step-state sequences.
- [ ] Run a baseline episode through `inference.py`.
- [ ] Run Docker build and container smoke tests.
- [ ] Run `openenv` validation locally and fix all reported issues.
- [ ] Re-run validation after every manifest, schema, or Docker change.
- [ ] Verify baseline produces reproducible scores across multiple runs

### 11.2 Hugging Face Space Validation
- [ ] Prepare the repo for Hugging Face Space deployment without local-only assumptions.
- [ ] Verify the Space starts successfully with the Docker configuration.
- [ ] Verify the Space responds to `reset()`.
- [ ] Verify the Space supports a full episode through the OpenEnv API.
- [ ] Verify any required tokens or secrets are mapped to the expected environment variables.
- [ ] Verify README front matter and app metadata do not conflict with the deployment target.

### 11.3 Final Quality Pass
- [ ] Remove all echo-environment references from code, docs, and metadata.
- [ ] Remove dead starter logic and unused dependencies.
- [ ] Ensure logs are useful for debugging but not excessively verbose.
- [ ] Ensure deterministic seeds are centralized and documented.
- [ ] Ensure no TODO markers remain in submission-critical files.

## Special Section: OpenEnv Spec Compliance
- [ ] Confirm the environment exposes typed action and observation models.
- [ ] Confirm `reset()` returns a valid observation for a fresh episode.
- [ ] Confirm `step()` accepts the typed action model and returns a valid step result.
- [ ] Confirm `state` returns a valid OpenEnv state object.
- [ ] Confirm schema serialization works for action, observation, and state models.
- [ ] Confirm `openenv.yaml` is valid and points to the correct app entrypoint.
- [ ] Confirm the project passes OpenEnv validation without manual overrides.

## Special Section: inference.py Compliance
- [ ] Confirm the file is named exactly `inference.py`.
- [ ] Confirm `inference.py` uses the OpenAI client.
- [ ] Confirm `inference.py` reads `API_BASE_URL`.
- [ ] Confirm `inference.py` reads `MODEL_NAME`.
- [ ] Confirm `inference.py` reads `HF_TOKEN`.
- [ ] Confirm `inference.py` can run against the local server.
- [ ] Confirm `inference.py` can run against the deployed Hugging Face Space.
- [ ] Confirm `inference.py` produces valid `accept`, `reject`, or `review` actions only.

## Special Section: Grading Correctness
- [ ] Confirm graders are deterministic.
- [ ] Confirm graders return values in the range `0.0` to `1.0`.
- [ ] Confirm graders treat easy, medium, and hard tasks consistently.
- [ ] Confirm graders penalize false accepts, false rejects, and unnecessary reviews appropriately.
- [ ] Confirm graders reward correct high-confidence decisions and justified reviews appropriately.
- [ ] Confirm shaped rewards shown during interaction do not contradict final grading.
- [ ] Confirm golden tests lock expected scores for representative episodes.

## Special Section: Deployment Validation
- [ ] Confirm the Dockerfile builds successfully from a clean environment.
- [ ] Confirm the Docker container starts and serves the OpenEnv app.
- [ ] Confirm the deployed Hugging Face Space exposes working API endpoints.
- [ ] Confirm the deployed Hugging Face Space responds to `reset()`.
- [ ] Confirm the full evaluation path stays under the runtime limit.
- [ ] Confirm all required environment variables are documented and supported.
- [ ] Confirm no secret is hardcoded in the repository.

## Final Pre-Submission Checklist
- [ ] At least three tasks exist and are labeled easy, medium, and hard.
- [ ] The environment represents a real-world OOD decision system rather than a toy example.
- [ ] The only decision actions are `accept`, `reject`, and `review`.
- [ ] Reward is meaningful and non-sparse across the episode.
- [ ] Grading is deterministic and normalized to `0.0` to `1.0`.
- [ ] Typed models are complete and OpenEnv-compliant.
- [ ] `reset()`, `step()`, and `state` all behave correctly.
- [ ] `inference.py` exists and meets all naming and environment-variable requirements.
- [ ] `openenv.yaml` is valid.
- [ ] Docker build and run are successful.
- [ ] Hugging Face Space deployment responds to `reset()`.
- [ ] Runtime stays below 20 minutes on the target hardware budget.
- [ ] OpenEnv validation passes.
- [ ] README, metadata, and manifests reflect the final environment accurately.
- [ ] No starter echo-environment behavior remains anywhere in the submission.
