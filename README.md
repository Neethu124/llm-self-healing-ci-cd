# LLM-Guided Self-Healing CI/CD Pipeline

An educational prototype of a CI/CD pipeline that detects its own failures, finds the root cause from the logs, applies a corrective action, and re-runs itself. It follows the design of our team project, "Large Language Models for Robust Pipelines".

**Note:** this repository is a small simulated prototype of the concept, not our team's full original codebase. The pipeline is simulated, so it runs anywhere with plain Python.

## How it works

1. Run the pipeline and collect the log
2. Preprocess the log (remove timestamps, duplicates and noise)
3. Analyze the log to classify the failure and find the root cause (keyword rules by default; an LLM if `ANTHROPIC_API_KEY` is set)
4. Run a corrective action (dependency fix, configuration repair, service restart)
5. Re-run the pipeline; if it still fails after 3 attempts, or no safe fix exists, escalate to a DevOps engineer
6. Save every outcome to `recovery_history.json`

## Run it

```
python self_healing_pipeline.py
```

No installs needed. The LLM step is optional (`pip install anthropic`, then set `ANTHROPIC_API_KEY`).

## Scenarios included

- Dependency conflict (recovers)
- Configuration error (recovers)
- Infrastructure issue (recovers)
- Failed tests from a code bug (escalated, since it is not safe to fix automatically)

## Interactive walkthrough

Open `demo.html` in a browser for a step-by-step visual walkthrough of the same workflow.

## My part in the team project

Debugging, monitoring dashboards and project reports.
