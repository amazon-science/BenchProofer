# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Grading for the eval harness (judge prompt TEXT lives in the prompt registry).

Per submission:
  resolve     (all modes, mechanical) — harness.run_resolve → the SWE-bench oracle.
  verify      (modes 7,3,8, mechanical, host) — backend verifier on the agent's
              model + adapter.antifakery hygiene.
  equivalence (modes 7,3, agentic, PRIVILEGED) — 3-vote judge: model ≡ patch and
              spec OK (unchanged vs reference for mode 7; faithful to the issue
              for mode 3). Catches the hole verify∧resolve don't pin: a
              vacuous/unrelated spec.
  spec audit  (mode 8, agentic, tool-using) — adversarial five-property audit
              of the agent's OWN spec (axioms_sound/admissible/sound/complete/
              faithful), machine-grounded via the checker tool + axiom probe.

Verdict: modes 4/6/2/0/1 → pass = resolved. Modes 7/3/5 → pass = verified ∧
resolved ∧ equivalent (100 = "verified mode 4": localization given, spec from
scratch, so the scratch judge applies as in mode 3). Mode 8 → pass =
verified ∧ antifakery ∧ spec audit. Persisted as grade/result.json.

EARS (natural language — no verifier, no judge): every mode is resolve-only
here; for the audited twins (modes 5/6/3) run.py then runs the adversarial
counterexample audit (eval/adversary.py) on passing submissions and demotes
`passed` when a real ground-truth violation is confirmed. Mode 8 N/A.

Expected judge prompt files (load_prompt, prompts/<backend>/ then shared/;
PromptNotFound fails loudly rather than judging with the wrong rubric):
  judge_equivalence_system.md / judge_equivalence_schema.md          (mode 7)
  judge_equivalence_scratch_system.md / judge_equivalence_scratch_schema.md (mode 3)
  judge_specgen_system.md / judge_specgen_schema.md                  (mode 8)
No placeholders; per-instance material is assembled in the user prompt here.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

from ..harness import run_resolve
from ..paths import DATASET_JSONL
from ..prompts import load_prompt
from .adapter import EvalAdapter
from .dataset import EvalTask
from .providers import ToolSpec

VERIFY_TIMEOUT = 300
JUDGE_VOTES = 3


@dataclass
class GradeResult:
    instance_id: str
    mode: int
    resolved: bool = False
    resolve_note: str = ""
    verified: bool | None = None       # None when N/A (modes 4,6)
    verify_note: str = ""
    equivalent: bool | None = None     # None when N/A (modes 4,6)
    equivalence: dict = field(default_factory=dict)
    antifakery_ok: bool | None = None  # model is an honest contract
    antifakery_note: str = ""
    spec_ok: bool | None = None        # mode 8 spec audit
    spec_audit: dict = field(default_factory=dict)
    adversary: dict = field(default_factory=dict)  # ears audited modes (5/6/3)
    passed: bool = False
    note: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def _frozen_row(instance_id: str) -> dict:
    with DATASET_JSONL.open() as fh:
        for line in fh:
            if f'"{instance_id}"' in line:
                row = json.loads(line)
                if row.get("instance_id") == instance_id:
                    return row
    raise ValueError(f"{instance_id} not in frozen dataset")


def grade_resolve(instance_id: str, patch: str, run_id: str,
                  timeout: int = 1800) -> tuple[bool, str]:
    if not patch.strip():
        return False, "empty patch"
    res = run_resolve(instance_id, patch, run_id=run_id, timeout=timeout)
    if not res.completed:
        return False, f"harness incomplete: {res.note}"
    return res.resolved, res.note


def grade_verify(adapter: EvalAdapter, model_src: str | None,
                 float_encoding: str | None = None) -> tuple[bool, str]:
    if not model_src:
        return False, "no model submitted"
    if adapter.backend.language.flavor == "ears":
        # NO verifier exists — the verify slot records the structural LINT,
        # explicitly labelled (a strictly weaker claim).
        from ..ears_lint import lint
        ok, report = lint(model_src)
        return ok, f"lint (no formal verifier): {report}"
    r = adapter.check_source(model_src, timeout=VERIFY_TIMEOUT,
                             float_encoding=float_encoding)
    return r.success, r.summary


def grade_antifakery(adapter: EvalAdapter, model_src: str | None) -> tuple[bool, str]:
    """Minimal anti-fakery guard so "verifies" MEANS something; per-backend
    rules live on the adapter. Spec STRENGTH is the equivalence judge's job."""
    return adapter.antifakery(model_src)


def _judge_prompt(adapter: EvalAdapter, task: EvalTask, model_src: str, patch: str,
                  gold_patch: str, reference_model: str,
                  from_scratch: bool = False) -> str:
    fence = adapter.lang_fence
    schema_hint = load_prompt(
        "judge_equivalence_scratch_schema" if from_scratch else "judge_equivalence_schema",
        backend=adapter.backend.name)
    head = (
        f"INSTANCE: {task.instance_id}\nISSUE (problem statement):\n"
        f"{task.problem_statement[:3000]}\n\n"
    )
    cand = (
        f"=== CANDIDATE MODEL (the solver's submitted model + its spec) ===\n"
        f"```{fence}\n{model_src[:12000]}\n```\n\n"
        f"=== CANDIDATE PATCH (the solver's real-code edit being judged) ===\n"
        f"```diff\n{patch[:8000]}\n```\n\n"
        f"=== GOLD PATCH (ground-truth intended behaviour, for context) ===\n"
        f"```diff\n{gold_patch[:8000]}\n```\n\n"
    )
    if from_scratch:
        return (
            head + cand +
            f"Decide: (1) does the candidate model's SPEC faithfully represent the "
            f"issue's intent (not vacuous, not a different problem)? (2) is the "
            f"candidate model a faithful skeleton EQUIVALENT to the candidate patch? "
            f"{schema_hint}"
        )
    ref_block = (
        f"=== REFERENCE MODEL (the spec the solver was given; its signatures + "
        f"contract clauses define the spec that must NOT meaningfully change) ===\n"
        f"```{fence}\n{reference_model[:12000]}\n```\n\n"
        if reference_model else
        "=== REFERENCE MODEL: (unavailable — judge spec_unchanged=true unless the "
        "candidate model's spec is self-evidently broken) ===\n\n"
    )
    return (
        head + ref_block + cand +
        f"Decide: (1) is the candidate model's SPEC unchanged vs the reference model "
        f"(cosmetic/equivalent tweaks OK, meaningful changes not)? (2) is the "
        f"candidate model a faithful skeleton EQUIVALENT to the candidate patch? "
        f"{schema_hint}"
    )


def _extract_last_json(text: str, key: str) -> dict | None:
    """LAST balanced top-level {...} in `text` containing `"<key>"` that parses
    to a dict. Reasoning models emit prose with stray braces before the verdict,
    so a greedy `\\{.*\\}` mis-cuts; this scan is STRING-AWARE. On strict-JSON
    failure, falls back to a regex field pull (tolerates unescaped quotes in
    `reason`)."""
    text = text or ""
    spans, n = [], len(text)
    for start in (i for i, ch in enumerate(text) if ch == "{"):
        depth, in_str, esc = 0, False, False
        for i in range(start, n):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    spans.append(text[start:i + 1])
                    break
    for cand in reversed(spans):
        if f'"{key}"' not in cand:
            continue
        try:
            d = json.loads(cand)
        except (ValueError, TypeError):
            d = _loads_lenient(cand)
        if isinstance(d, dict) and key in d:
            return d
    return None


def _loads_lenient(cand: str) -> dict | None:
    """Regex field pull when strict json.loads fails — the booleans are what
    gate the verdict."""
    out = {}
    for fld in ("equivalent", "spec_unchanged", "spec_faithful",
                "axioms_sound", "admissible", "sound", "complete", "faithful"):
        m = re.search(rf'"{fld}"\s*:\s*(true|false)', cand, re.I)
        if m:
            out[fld] = m.group(1).lower() == "true"
    if not out:
        return None
    mc = re.search(r'"confidence"\s*:\s*([0-9.]+)', cand)
    if mc:
        try:
            out["confidence"] = float(mc.group(1))
        except ValueError:
            pass
    mr = re.search(r'"reason"\s*:\s*"(.*)', cand, re.S)
    if mr:
        out["reason"] = mr.group(1).rstrip().rstrip('"}').rstrip()
    return out


def _parse_judge(text: str) -> dict:
    """Extract the judge's verdict (last {...} carrying `equivalent`).
    `parse_error=True` marks an infra failure (truncation / no verdict) so the
    caller retries rather than counting it a refute. A ballot PASSES iff the
    spec gate (spec_unchanged in given-spec modes / spec_faithful in
    from-scratch modes; default true when omitted) AND equivalent."""
    d = _extract_last_json(text, key="equivalent")
    if isinstance(d, dict):
        equivalent = bool(d.get("equivalent", False))
        # spec gate: `spec_unchanged` (given-spec) or `spec_faithful`
        # (from-scratch); accept either, default true
        spec_ok = bool(d.get("spec_unchanged", d.get("spec_faithful", True)))
        return {"equivalent": equivalent, "spec_ok": spec_ok,
                "pass": equivalent and spec_ok,
                "confidence": float(d.get("confidence", 0.0) or 0.0),
                "reason": str(d.get("reason", ""))[:500], "parse_error": False}
    # no parseable verdict → infra failure, NOT a refutation
    return {"equivalent": False, "spec_ok": False, "pass": False,
            "confidence": 0.0,
            "reason": "unparseable judge output (no verdict JSON)", "parse_error": True}


def grade_equivalence(adapter: EvalAdapter, task: EvalTask, model_src: str,
                      patch: str, judge_provider, votes: int = JUDGE_VOTES) -> dict:
    """N-vote judge; ballot pass = spec_ok AND equivalent, instance passes on a
    majority of DECISIVE ballots. "Spec OK" = unchanged-vs-reference (mode 7)
    or faithful-to-the-issue (mode 3). The judge is PRIVILEGED (gold patch +
    reference model). Infra failures abstain and are retried, never counted as
    a refutation."""
    if not model_src or not patch.strip():
        return {"equivalent": False, "votes": [], "note": "missing model or patch"}
    gold = _frozen_row(task.instance_id).get("patch", "")
    from_scratch = task.spec_from_scratch
    system = load_prompt(
        "judge_equivalence_scratch_system" if from_scratch else "judge_equivalence_system",
        backend=adapter.backend.name)
    # from-scratch modes have no reference model — judge faithfulness to the issue
    reference_model = "" if from_scratch else (adapter.model_src(task.instance_id) or "")
    prompt = _judge_prompt(adapter, task, model_src, patch, gold, reference_model,
                           from_scratch)
    ballots = []
    for _ in range(votes):
        b = None
        # 2 attempts per vote: parse_error/exception is INFRA, retried rather
        # than counted as a refutation (which biased pass rate down)
        for _attempt in range(2):
            try:
                turn = judge_provider.chat(system,
                                           [{"role": "user", "content": [{"text": prompt}]}], [])
                b = _parse_judge(turn.text)
            except Exception as e:  # noqa: BLE001
                b = {"equivalent": False, "spec_ok": False, "pass": False,
                     "confidence": 0.0,
                     "reason": f"judge error: {type(e).__name__}: {e}", "parse_error": True}
            if not b.get("parse_error"):
                break
        ballots.append(b)
    # only decisive ballots count; infra failures abstain
    decisive = [b for b in ballots if not b.get("parse_error")]
    yes = sum(1 for b in decisive if b.get("pass"))           # spec_ok AND equivalent
    no = sum(1 for b in decisive if not b.get("pass"))
    n_err = len(ballots) - len(decisive)
    n_spec = sum(1 for b in decisive if not b.get("spec_ok"))
    n_neq = sum(1 for b in decisive if not b.get("equivalent"))
    # all-infra → equivalent is None ("judge unavailable")
    equivalent = None if not decisive else yes > no
    spec_label = "spec-unfaithful" if from_scratch else "spec-changed"
    return {"equivalent": equivalent, "yes": yes, "no": no, "errors": n_err,
            "spec_failed_votes": n_spec, "not_equivalent_votes": n_neq,
            "votes": ballots,
            "note": f"{yes} pass / {no} fail / {n_err} infra of {votes} "
                    f"(of failing: {n_spec} {spec_label}, {n_neq} not-equiv)"}


# Mode 8 spec audit: grades verify => correct as five falsifiable properties.
# The judge is a tool-using ADVERSARY — every claimed break is discharged with a
# real tool, so verdicts are machine-backed. Privileged on BEHAVIOUR (gold patch
# + issue + FAIL_TO_PASS) but NOT shown the gold spec: we judge the guarantee,
# not similarity to ours.

_SPEC_PROPERTIES = ("axioms_sound", "admissible", "sound", "complete", "faithful")


def _spec_judge_prompt(adapter: EvalAdapter, task: EvalTask, model_src: str,
                       gold_patch: str) -> str:
    fence = adapter.lang_fence
    schema_hint = load_prompt("judge_specgen_schema", backend=adapter.backend.name)
    f2p = ""
    row = _frozen_row(task.instance_id)
    fp = row.get("FAIL_TO_PASS", "")
    if fp:
        try:
            names = json.loads(fp) if isinstance(fp, str) else fp
            f2p = "\n".join(f"  - {t}" for t in (names or [])[:40])
        except (ValueError, TypeError):
            f2p = str(fp)[:1500]
    gold_model = adapter.model_src(task.instance_id) or ""
    gold_buggy = adapter.gold_prepatch_src(task.instance_id) or ""
    gold_axiom = adapter.gold_axiom_check_src(task.instance_id) or ""
    check = adapter.check_tool_name
    ref_blocks = ""
    if gold_model:
        ref_blocks += (
            f"=== GOLD MODEL (a CORRECT reference spec+witness, benchmark's own "
            f"signatures — ground truth, NOT an equivalence target; port its logic "
            f"into the CANDIDATE signatures for your `sound` witness) ===\n"
            f"```{fence}\n{gold_model[:12000]}\n```\n\n")
    if gold_buggy:
        ref_blocks += (
            f"=== GOLD PRE-FIX BUGGY WITNESS (the canonical WRONG impl the issue is "
            f"about — port into the CANDIDATE signatures for your `complete` witness) ===\n"
            f"```{fence}\n{gold_buggy[:10000]}\n```\n\n")
    if gold_axiom:
        ref_blocks += (
            f"=== GOLD AXIOM-CHECK (which callees are legitimately axiomatizable + the "
            f"in-container probe technique — the candidate's axioms may differ) ===\n"
            f"```python\n{gold_axiom[:8000]}\n```\n\n")
    tools_line = (f"Discharge each property with a tool on the CANDIDATE's "
                  f"spec (`{check}` / `run_axiom_probe`)."
                  if check else
                  "There is no verifier for this spec format: discharge each "
                  "property with `run_axiom_probe` — behavioral probes "
                  "against the real repo that confirm or refute what the "
                  "requirements mandate.")
    return (
        f"INSTANCE: {task.instance_id}\nISSUE (problem statement):\n"
        f"{task.problem_statement[:4000]}\n\n"
        f"=== CANDIDATE SPECIFICATION (the solver's model — judge its spec) ===\n"
        f"```{fence}\n{model_src[:14000]}\n```\n\n"
        f"=== GOLD PATCH (ground truth for the CORRECT behaviour — NOT a reference spec) ===\n"
        f"```diff\n{gold_patch[:8000]}\n```\n\n"
        f"=== HIDDEN TESTS that define 'correct' (names only) ===\n{f2p}\n\n"
        f"{ref_blocks}"
        f"Remember: the gold artifacts are REFERENCES in the benchmark's signatures, "
        f"not equivalence targets and not verifiable under the candidate spec — a "
        f"different-but-sound candidate must PASS. {tools_line} {schema_hint}"
    )


def _parse_spec_judge(text: str) -> dict:
    """Mode-8 verdict (five booleans). parse_error => infra abstention
    (retried), not a refutation."""
    d = (_extract_last_json(text, key="faithful")
         or _extract_last_json(text, key="complete")
         or _extract_last_json(text, key="admissible"))
    if not isinstance(d, dict):
        return {"pass": False, "parse_error": True,
                "reason": "unparseable spec-judge output (no verdict JSON)"}
    props = {p: bool(d.get(p, False)) for p in _SPEC_PROPERTIES}
    return {**props, "pass": all(props.values()),
            "confidence": float(d.get("confidence", 0.0) or 0.0),
            "reason": str(d.get("reason", ""))[:800], "parse_error": False}


# tools the spec-judge uses to MACHINE-CONFIRM a falsification

def _spec_judge_tools(adapter: EvalAdapter) -> list[ToolSpec]:
    # ears has no checker tool (check_tool_name="") — probes are the only
    # machine grounding for its spec judge.
    checker = [adapter.check_tool_spec()] if adapter.check_tool_name else []
    return checker + [
        ToolSpec("run_axiom_probe",
                 "Run a Python probe inside the repo container at base_commit (the "
                 "UNCHANGED code) to test whether one of the solver's `axiom`s holds of "
                 "the REAL callee: call the real callee on inputs satisfying the axiom's "
                 "hypotheses and assert its conclusion; print and sys.exit(1) on a "
                 "violation. Returns exit code + output. Only the repo package + stdlib "
                 "are importable.",
                 {"probe_src": {"type": "string",
                                "description": "self-contained python probe; "
                                               "exit!=0 on axiom violation"}},
                 ["probe_src"]),
    ]


def _spec_judge_tool(adapter: EvalAdapter, name: str, inp: dict, instance_id: str,
                     float_encoding: str | None = None) -> str:
    import tempfile
    from pathlib import Path
    if name == adapter.check_tool_name:
        src = inp.get("model_src", "")
        if not src.strip():
            return f"({name}: empty model_src)"
        res = adapter.check_source(src, timeout=VERIFY_TIMEOUT,
                                   float_encoding=float_encoding)
        return (f"VERIFIES={res.success}\n" + (res.stdout or "")[:4000])
    if name == "run_axiom_probe":
        src = inp.get("probe_src", "")
        if not src.strip():
            return "(run_axiom_probe: empty probe_src)"
        d = Path(tempfile.mkdtemp(prefix="specjudge_"))
        try:
            (d / "probe.py").write_text(src)
            from ..docker_exec import run_in_container, ensure_image
            if ensure_image(instance_id):
                return "(run_axiom_probe: image unavailable; cannot confirm axiom in-container)"
            r = run_in_container(instance_id, str(d), "probe.py",
                                 apply_gold=False, timeout=600)
            return (f"exit={r.returncode}\nSTDOUT:\n{(r.stdout or '')[:3000]}"
                    f"\nSTDERR:\n{(r.stderr or '')[:1500]}")
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)
    return f"(unknown tool {name})"


def _tool_signal(adapter: EvalAdapter, name: str, out: str) -> str:
    """One-line machine signal for the audit trace — the objective fact the
    judge observed, not its prose retelling."""
    head = (out or "").lstrip().splitlines()[0] if (out or "").strip() else ""
    if name == adapter.check_tool_name:
        return head if head.startswith("VERIFIES=") else f"({head[:40]})"
    if name == "run_axiom_probe":
        return head if head.startswith("exit=") else f"({head[:40]})"
    return head[:40]


def _run_spec_judge_once(adapter: EvalAdapter, task: EvalTask, model_src: str,
                         gold_patch: str, judge_provider, max_iters: int = 12) -> dict:
    """One adversarial ballot: a tool-use loop ending in a five-boolean verdict.
    Records `trace` (every tool invoked + machine signal) so tool-grounding is
    auditable ground truth, not the judge's self-report."""
    system = load_prompt("judge_specgen_system", backend=adapter.backend.name)
    tools = _spec_judge_tools(adapter)
    messages = [{"role": "user", "content": [{"text":
                 _spec_judge_prompt(adapter, task, model_src, gold_patch)}]}]
    last_text = ""
    trace: list[dict] = []
    for _ in range(max_iters):
        turn = judge_provider.chat(system, messages, tools)
        last_text = turn.text or last_text
        messages.append(turn.raw)
        if not turn.tool_calls:
            b = _parse_spec_judge(turn.text)
            if not b.get("parse_error"):
                return {**b, "trace": trace}
            # no verdict yet — nudge toward emitting it
            messages.append({"role": "user", "content": [{"text":
                "Emit your final verdict now as the JSON object described."}]})
            continue
        results = []
        for c in turn.tool_calls:
            out = _spec_judge_tool(adapter, c.name, c.input, task.instance_id,
                                   float_encoding=task.float_encoding)
            trace.append({"tool": c.name, "signal": _tool_signal(adapter, c.name, out),
                          "in_len": len((c.input or {}).get("model_src")
                                         or (c.input or {}).get("probe_src") or "")})
            results.append({"tool_result": {"id": c.id, "content": out, "is_error": False}})
        messages.append({"role": "user", "content": results})
    # fell out of the loop — try a last parse, else infra-abstain
    return {**_parse_spec_judge(last_text), "trace": trace}


def grade_spec(adapter: EvalAdapter, task: EvalTask, model_src: str, judge_provider,
               votes: int = JUDGE_VOTES) -> dict:
    """N-vote adversarial audit of the agent's OWN spec (mode 8). Ballot pass
    = axioms_sound ∧ admissible ∧ sound ∧ complete ∧ faithful; overall pass on
    a majority of DECISIVE ballots. Infra-failed ballots abstain and are
    retried, never counted as a refutation."""
    if not model_src or not model_src.strip():
        return {"spec_ok": False, "votes": [], "note": "missing spec/model"}
    gold = _frozen_row(task.instance_id).get("patch", "")
    ballots = []
    for _ in range(votes):
        b = None
        for _attempt in range(2):          # retry an infra abstention once
            try:
                b = _run_spec_judge_once(adapter, task, model_src, gold, judge_provider)
            except Exception as e:  # noqa: BLE001
                b = {"pass": False, "parse_error": True, "trace": [],
                     "reason": f"judge error: {type(e).__name__}: {e}"}
            if not b.get("parse_error"):
                break
        ballots.append(b)
    decisive = [b for b in ballots if not b.get("parse_error")]
    yes = sum(1 for b in decisive if b.get("pass"))
    no = len(decisive) - yes
    n_err = len(ballots) - len(decisive)
    spec_ok = None if not decisive else yes > no
    # per-property failure tally — the paper's headline
    fails = {p: sum(1 for b in decisive if not b.get(p, False)) for p in _SPEC_PROPERTIES}
    # tool-grounding per ballot: a verdict with NO tool calls is suspect
    # (text-only reasoning), so surface it in the audit
    check = adapter.check_tool_name
    grounded = sum(1 for b in decisive if b.get("trace"))
    n_check = sum(1 for b in decisive
                  if any(t.get("tool") == check for t in b.get("trace", [])))
    n_probe = sum(1 for b in decisive
                  if any(t.get("tool") == "run_axiom_probe" for t in b.get("trace", [])))
    return {"spec_ok": spec_ok, "yes": yes, "no": no, "errors": n_err,
            "property_fail_votes": fails, "votes": ballots,
            "ballots_tool_grounded": grounded, "ballots_ran_check": n_check,
            "ballots_ran_axiom_probe": n_probe,
            "note": f"{yes} pass / {no} fail / {n_err} infra of {votes}; "
                    f"tool-grounded {grounded}/{len(decisive)} decisive "
                    f"({check} {n_check}, axiom_probe {n_probe}); "
                    f"property fails (of {len(decisive)} decisive): " +
                    ", ".join(f"{p}={fails[p]}" for p in _SPEC_PROPERTIES)}


def grade(adapter: EvalAdapter, task: EvalTask, patch: str, model_src: str | None,
          run_id: str, judge_provider=None, resolve_timeout: int = 1800) -> GradeResult:
    """Verdict by mode:
      modes 4/6/2/0/1 → pass = RESOLVED.
      modes 7/3/5 → pass = verify ∧ resolve ∧ equivalent.
      mode 8 → pass = witness verifies ∧ honest contract ∧ spec audit.
    EARS: resolve-only for every mode (the audited twins' demotion happens in
    run.py, after this returns). `antifakery` is a minimal honesty guard (not
    structural); for mode 2 verify/antifakery are recorded as informational,
    not gating."""
    g = GradeResult(task.instance_id, task.mode)

    # resolve — all modes (the SWE-bench oracle)
    g.resolved, g.resolve_note = grade_resolve(task.instance_id, patch, run_id, resolve_timeout)

    # verify + anti-fakery — recorded wherever a model was prompted (1,3,4,11)
    if task.prompt_model and model_src:
        g.antifakery_ok, g.antifakery_note = grade_antifakery(adapter, model_src)
        g.verified, g.verify_note = grade_verify(adapter, model_src, task.float_encoding)

    if task.scored_on_equivalence:                       # modes 7, 3 (formal)
        # equivalence — only worth running if verify/resolve/antifakery all hold
        if g.verified and g.resolved and g.antifakery_ok and judge_provider is not None:
            g.equivalence = grade_equivalence(adapter, task, model_src or "", patch,
                                              judge_provider)
            g.equivalent = g.equivalence.get("equivalent", False)  # True | False | None
        else:
            g.equivalent = False
            g.equivalence = {"equivalent": False,
                             "note": "skipped (verify/resolve/anti-fakery not all green)"}
        # pass requires a POSITIVE verdict; equivalent=None (all-infra) does not
        # pass but is recorded distinctly so it isn't mistaken for a refutation
        g.passed = bool(g.verified and g.resolved and g.antifakery_ok and g.equivalent is True)
        g.note = (f"verified={g.verified} resolved={g.resolved} "
                  f"antifakery={g.antifakery_ok} equivalent={g.equivalent}")
    elif task.scored_on_spec:                            # mode 8
        # witness must verify + be an honest contract, then the adversarial
        # spec audit gates. Resolve is NOT gated (spec submitted, not a patch).
        if g.verified and g.antifakery_ok and judge_provider is not None:
            g.spec_audit = grade_spec(adapter, task, model_src or "", judge_provider)
            g.spec_ok = g.spec_audit.get("spec_ok", False)   # True | False | None
        else:
            g.spec_ok = False
            g.spec_audit = {"spec_ok": False,
                            "note": "skipped (witness did not verify / not an honest contract)"}
        g.passed = bool(g.verified and g.antifakery_ok and g.spec_ok is True)
        g.note = (f"witness_verified={g.verified} antifakery={g.antifakery_ok} "
                  f"spec_ok={g.spec_ok} (resolve={g.resolved}, informational)")
    else:
        # modes 4, 6, 2, 0, 1 and ALL ears modes (incl. 100) — resolve
        # only (apples-to-apples w/ the leaderboard). For scored_on_audit
        # modes (1 everywhere; ears 3/5/6) run.py additionally runs the adversarial
        # counterexample audit on passing submissions and demotes
        # passed on a confirmed-real violation (recorded in g.adversary).
        g.passed = g.resolved
        extra = ""
        if task.mode == 3 and g.verified is not None:
            extra = f" (informational: model verified={g.verified}, honest={g.antifakery_ok})"
        g.note = f"resolved={g.resolved}{extra}"
    return g
