"""
Self-healing CI/CD pipeline: small educational prototype.

Flow: run pipeline -> collect log -> preprocess -> analyze (root cause)
      -> recover -> re-run -> success, or escalate after MAX_ATTEMPTS.

The pipeline here is SIMULATED (a few checks on a state dictionary), so the
whole loop can run on any laptop with plain Python 3. No installs needed.

analyze() uses simple keyword rules by default. If the ANTHROPIC_API_KEY
environment variable is set and the "anthropic" package is installed, it asks
an LLM instead (optional; falls back to the rules if anything fails).
"""
import json
import os
import re
from datetime import datetime

MAX_ATTEMPTS = 3


# ---------- 1. Simulated pipeline ----------
def run_pipeline(state):
    """Return (success, log_text). Fails depending on the state."""
    log = ["[INFO] Stage: build", "[INFO] Stage: unit-testing"]
    if state["numpy_pin"].startswith("2"):
        log += ["[ERROR] Cannot install pandas==2.2.0 and numpy==" + state["numpy_pin"],
                "[ERROR] conflicting dependencies: pandas requires numpy<2.0",
                "[FATAL] Dependency installation failed"]
    elif state["DATABASE_URL"] is None:
        log += ["[WARN] DATABASE_URL is not set",
                "[ERROR] Deployment aborted: invalid configuration"]
    elif not state["memory_ok"]:
        log += ["[ERROR] container build-runner-7 terminated: OOMKilled",
                "[FATAL] Build interrupted"]
    elif state["buggy_code"]:
        log += ["[ERROR] test_refund_total FAILED", "[FATAL] 1 failed, 63 passed"]
    else:
        return True, "\n".join(log + ["[INFO] Pipeline successful"])
    return False, "\n".join(log)


# ---------- 2. Log preprocessing ----------
def preprocess(log):
    """Clean the log: strip timestamps, drop duplicates, keep only problem lines."""
    seen, keep = set(), []
    for line in log.splitlines():
        line = re.sub(r"^\[\d{2}:\d{2}:\d{2}\]\s*", "", line).strip()
        if line and line not in seen and not line.startswith("[INFO]"):
            seen.add(line)
            keep.append(line)
    return "\n".join(keep)


# ---------- 3. Analysis (root cause) ----------
RULES = [  # (keyword, category, recovery action)
    ("conflicting dependencies", "Dependency conflict", "fix_dependency"),
    ("invalid configuration", "Configuration error", "repair_config"),
    ("oomkilled", "Infrastructure issue", "restart_service"),
    ("failed", "Failed test cases", None),  # no safe automatic fix
]


def analyze_rules(clean_log):
    text = clean_log.lower()
    for keyword, category, action in RULES:
        if keyword in text:
            return {"category": category, "action": action}
    return {"category": "Unknown", "action": None}


def analyze_llm(clean_log):
    """Optional: ask an LLM to classify the failure. Returns None if unavailable."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
        reply = anthropic.Anthropic().messages.create(
            model="claude-sonnet-5-5", max_tokens=200,
            messages=[{"role": "user", "content":
                "Classify this CI/CD failure. Reply with JSON only: "
                '{"category": "...", "action": "fix_dependency|repair_config|restart_service|none"}'
                "\n\nLog:\n" + clean_log}])
        data = json.loads(reply.content[0].text)
        action = None if data["action"] == "none" else data["action"]
        return {"category": data["category"], "action": action}
    except Exception:
        return None


def analyze(clean_log):
    return analyze_llm(clean_log) or analyze_rules(clean_log)


# ---------- 4. Recovery actions (simulated) ----------
def fix_dependency(state):
    state["numpy_pin"] = "1.26.4"
    return "Pinned numpy to 1.26.4"


def repair_config(state):
    state["DATABASE_URL"] = "postgres://example/db"
    return "Restored DATABASE_URL from template"


def restart_service(state):
    state["memory_ok"] = True
    return "Restarted build runner with a clean environment"


ACTIONS = {"fix_dependency": fix_dependency,
           "repair_config": repair_config,
           "restart_service": restart_service}


# ---------- 5. Self-healing loop ----------
def self_heal(name, state):
    history = {"scenario": name, "attempts": [], "outcome": None}
    print("\n=== Scenario: " + name + " ===")
    for attempt in range(1, MAX_ATTEMPTS + 1):
        ok, log = run_pipeline(state)
        if ok:
            history["outcome"] = "success"
            print("Attempt " + str(attempt) + ": pipeline successful")
            break
        result = analyze(preprocess(log))
        print("Attempt " + str(attempt) + ": failed -> " + result["category"])
        step = {"attempt": attempt, "category": result["category"]}
        if result["action"] is None:
            step["action"] = "none (not safe to automate)"
            history["attempts"].append(step)
            history["outcome"] = "escalated to DevOps engineer"
            print("  No safe automatic fix. Escalating.")
            break
        step["action"] = ACTIONS[result["action"]](state)
        print("  Action: " + step["action"])
        history["attempts"].append(step)
    else:
        history["outcome"] = "escalated to DevOps engineer"
        print("Still failing after " + str(MAX_ATTEMPTS) + " attempts. Escalating.")
    history["time"] = datetime.now().isoformat(timespec="seconds")
    return history


if __name__ == "__main__":
    base = {"numpy_pin": "1.26.4", "DATABASE_URL": "set", "memory_ok": True, "buggy_code": False}
    scenarios = {
        "Dependency conflict": dict(base, numpy_pin="2.0.1"),
        "Configuration error": dict(base, DATABASE_URL=None),
        "Infrastructure issue": dict(base, memory_ok=False),
        "Failed tests (code bug)": dict(base, buggy_code=True),
    }
    results = [self_heal(n, s) for n, s in scenarios.items()]
    with open("recovery_history.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved recovery_history.json")
