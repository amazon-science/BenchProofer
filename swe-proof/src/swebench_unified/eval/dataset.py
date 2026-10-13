# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The agent-visible task view, per evaluation mode — the SINGLE source of
truth for what an evaluated agent may see. Parameterized on the EvalAdapter, so
the information environment is identical across backends and a cross-backend
number compares methods rather than harnesses.

Deliberately a *projection* of the frozen row + bundle that DROPS every
withheld field (gold patch, test_patch, FAIL_TO_PASS/PASS_TO_PASS) so those are
never even in the agent process's memory. `hints_text` excluded by default.

Modes (inputs + pass criterion; grading is elsewhere). RENUMBERED 2026-08-19
(legacy number in [brackets]; LEGACY_MODE_MAP below — run dirs created before
the renumbering carry legacy numbers in config.json). The design disentangles
the spec modes' two advantages — verification signal vs edit localization:

  0  baseline    [10] : canonical SWE-bench-Verified — no spec/localization/
                    verifier, no mention of models. Pass = resolve. The bar
                    mode 2 must beat.
  1  audited 0  [101] : all backends — agent-side identical to mode 0
                    (canonical baseline, bash+submit only); pass = resolve ∧
                    the adversarial counterexample audit finds no real
                    violation. Backend-independent (grounds in the lean spec).
  2  end-to-end   [3] : issue + repo only; prompted to construct spec + model.
                    Pass = resolve only (formal work encouraged, not scored).
  3  end-to-end+  [4] : same inputs as 2, formal work SCORED: pass = verify ∧
                    resolve ∧ EQUIVALENT (constructed-spec faithfulness judged).
  4  localization [0] : issue + repo + EDIT LOCALIZATION; no spec/verifier.
                    Pass = resolve.
  5  verified 4 [100] : formal backends — mode 4's inputs (localization, NO
                    spec) plus the verifier; spec/model constructed from
                    scratch as in mode 3. Pass = verify ∧ resolve ∧ equivalence
                    (scratch judge). Ears variant: inputs identical to mode 4,
                    pass = resolve ∧ the adversarial counterexample audit finds
                    no real ground-truth violation (its native check, as the
                    formal variant's verifier is ITS native check).
  6  spec-aided   [2] : + spec_view + verifier (optional aid). Pass = resolve.
  7  spec→verified [1]: + spec_view + verifier. Pass = verify ∧ resolve ∧
                    EQUIVALENT (3-vote judge).
  8  spec-gen    [11] : issue + repo only; construct spec + verifying witness
                    (no patch graded). Pass = the adversarial spec audit.

Ablations: (6−4) spec+verifier given localization; (4−2) localization;
(2−0) verification method with identical inputs; (7−3) given vs constructed spec.

EARS overrides the table above (natural language: no verifier, no judge —
see MODES_SCORED_ON_AUDIT_EARS below): all ears modes are resolve-scored, in
unaudited/audited pairs 4→5, 7→6 (spec given), 2→3 (spec authored); mode 8
is not applicable. Agent-side an audited mode is byte-identical to its twin.

`spec_view` = markers-based projection: contracts/signatures/axioms/pure
helpers pass through; impl (and lean proof / velvet prove_correct bodies) are
elided — what G-LEAK certifies as non-leaking.

"edit localization" = repo-side only (repo_symbol + repo_location +
changed_files), NO modeling/verification detail. Precomputed OFFLINE into the
benchmark's eval_localization.json by scripts/build_eval_localization.py, so the
eval process never opens the gold patch; nagini/velvet use the bundle
meta.json's modeled_functions instead (source parity). A mode whose signal IS
that localization refuses to run without it — see MODES_REQUIRE_LOCALIZATION.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from ..paths import DATASET_JSONL, EVAL_LOCALIZATION, FROZEN_INSTANCES
from .adapter import EvalAdapter

MODES_WITH_SPEC = {6, 7}             # agent gets spec_view + verifier
MODES_WITH_LOCALIZATION = {4, 5, 6, 7}
# Modes that REFUSE to run without localization, because it is the whole
# difference between them and the baseline: they render it as their own block
# (prompts._localization_block), so an instance with no entry is silently mode 0
# under another label and the ablation measures nothing. Modes 1/2 also carry
# localization but convey it through the spec, which is their signal, so they
# stay tolerant — that is what lets a benchmark be smoke-tested before its
# localization file exists (scripts/benchmark_smoke.py).
MODES_REQUIRE_LOCALIZATION = MODES_WITH_LOCALIZATION - MODES_WITH_SPEC
MODES_PROMPT_MODEL = {2, 3, 5, 7, 8}      # prompt asks to build a verifying model
# submit BLOCKED without a model (3 may submit patch-only)
MODES_REQUIRE_MODEL_TO_SUBMIT = {3, 5, 7, 8}
MODES_SCORED_ON_VERIFY = {3, 5, 7, 8}
MODES_SCORED_ON_EQUIVALENCE = {3, 5, 7}    # pass requires the equivalence judge
MODES_SPEC_FROM_SCRATCH = {2, 3, 5, 8}     # agent CONSTRUCTS the spec
MODES_SCORED_ON_SPEC = {8}           # pass requires the spec-quality audit
MODE_BASELINE = 0                    # canonical SWE-bench
MODES_BASH_ONLY = {0, 1}             # the ONLY tool is bash
ALL_MODES = (0, 1, 2, 3, 4, 5, 6, 7, 8)

# 2026-08-19 renumbering, old -> new. Run dirs created BEFORE this date carry
# the legacy numbers in config.json; the ranges overlap, so translation is
# deliberately manual/opt-in (a loader cannot distinguish old 0-4 from new 0-4
# by value alone).
LEGACY_MODE_MAP = {10: 0, 101: 1, 3: 2, 4: 3, 0: 4, 100: 5, 2: 6, 1: 7, 11: 8}

# Mode 1 = audited baseline, ALL backends: agent-side byte-identical to
# mode 0 (canonical SWE-bench, bash+submit), pass = resolve ∧ the
# adversarial counterexample audit (eval/adversary.py, lean formal ground
# truth + gold) finds no real violation. The audit is backend-independent,
# so mode-1 numbers are comparable across backend labels.
MODES_SCORED_ON_AUDIT_ALL = {1}

# EARS redefinition: natural language has no verifier or judge, so ears scoring
# is resolve-only everywhere, and each unaudited mode has an AUDITED twin whose
# score additionally requires surviving the adversarial
# counterexample audit (eval/adversary.py: agent hunts a behavior where the
# accepted patch diverges from the lean formal ground truth + gold patch,
# every claim re-run mechanically). Pairs (unaudited → audited): 4 → 5,
# 7 → 6 (spec given), 2 → 3 (spec authored). Agent-side, each audited mode is
# byte-identical to its twin. Mode 8 is NOT APPLICABLE for ears. Formal
# backends run mode 5 too, but as "verified mode 4" (scratch judge, no
# adversarial audit) — this set governs only the ears audit scoring; the
# backend-independent audit itself exists (mode 1, eval/adversary.py).
MODES_SCORED_ON_AUDIT_EARS = {3, 5, 6}


@dataclass
class EvalTask:
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    mode: int
    backend: str = ""                 # adapter/backend name (nagini|velvet|lean)
    # spec layer (modes 6,7 only; None otherwise)
    spec_view: str | None = None
    modeled_functions: list = field(default_factory=list)
    # edit-localization layer (modes 4,6,7): which repo functions/files are modified
    localization: list = field(default_factory=list)   # [{repo_symbol, repo_location}]
    changed_files: list = field(default_factory=list)
    hints_text: str = ""              # empty unless explicitly included
    float_encoding: str | None = None  # nagini bundles only (meta.json)

    @property
    def gives_spec(self) -> bool:
        return self.spec_view is not None

    @property
    def gives_localization(self) -> bool:
        return bool(self.localization or self.changed_files)

    @property
    def bash_only(self) -> bool:
        """Baseline (mode 0): bash is the only tool (official SWE-bench)."""
        return self.mode in MODES_BASH_ONLY

    @property
    def prompt_model(self) -> bool:
        # ears modes 1/2: the given requirements document is COMPLETE (nothing
        # is elided), so there is no model artifact for the agent to build.
        # ears mode 5 is a pure mode-4 twin (audit-scored, no doc).
        if self.backend == "ears" and self.mode in (5, 6, 7):
            return False
        return self.mode in MODES_PROMPT_MODEL

    @property
    def require_model_to_submit(self) -> bool:
        # ears: mode 7 has no model to build; mode 3 must be agent-side
        # IDENTICAL to mode 2 (the audited twin), so the doc is encouraged
        # (prompt_model) but never blocks submit; mode 5 mirrors mode 4.
        if self.backend == "ears" and self.mode in (3, 5, 7):
            return False
        return self.mode in MODES_REQUIRE_MODEL_TO_SUBMIT

    @property
    def offers_verifier(self) -> bool:
        """Is the backend verify tool in the agent's toolbox? False in the
        no-verification modes (0, 1, 4) and in ears mode 5 (a pure
        mode-4 twin); formal mode 5 is 'verified mode 4' and DOES get it."""
        if self.mode in (0, 1, 4):
            return False
        if self.backend == "ears" and self.mode == 5:
            return False
        return True

    @property
    def scored_on_verify(self) -> bool:
        if self.backend == "ears":     # no verifier exists; resolve±audit only
            return False
        return self.mode in MODES_SCORED_ON_VERIFY

    @property
    def scored_on_equivalence(self) -> bool:
        if self.backend == "ears":     # judge dropped from ears scoring
            return False
        return self.mode in MODES_SCORED_ON_EQUIVALENCE

    @property
    def scored_on_spec(self) -> bool:
        """Mode 8: pass = spec-quality audit of the agent's OWN spec; the
        patch (resolve) is not graded. Not applicable for ears."""
        if self.backend == "ears":
            return False
        return self.mode in MODES_SCORED_ON_SPEC

    @property
    def scored_on_audit(self) -> bool:
        """Audited modes: pass = resolved AND the adversarial counterexample
        audit does not confirm a real ground-truth violation. Mode 1
        (audited baseline) for every backend; 3/5/6 for ears."""
        if self.mode in MODES_SCORED_ON_AUDIT_ALL:
            return True
        return self.backend == "ears" and self.mode in MODES_SCORED_ON_AUDIT_EARS

    @property
    def spec_from_scratch(self) -> bool:
        """Agent CONSTRUCTS the spec (modes 2,3,5,8); the audit checks it is
        FAITHFUL to the issue's intent, not that it matches a reference."""
        return self.mode in MODES_SPEC_FROM_SCRATCH

    # back-compat alias used by the agent loop's model-guess path
    @property
    def requires_model(self) -> bool:
        return self.prompt_model


def all_instance_ids() -> list[str]:
    """`--all` default: every row of the frozen dataset. To evaluate a fixed
    subset instead, pass --frozen-list (run.py)."""
    return [json.loads(ln)["instance_id"] for ln in DATASET_JSONL.open() if ln.strip()]


def frozen_instance_ids(path=None) -> list[str]:
    """Explicit frozen instance list (one id per line). A run over a subset is
    only comparable to another if both used the same list, so it is a file
    rather than a flag."""
    p = path or FROZEN_INSTANCES
    return [ln.strip() for ln in p.open() if ln.strip()]


def _decoded(s) -> str:
    """Pro text fields arrive JSON-STRING-ENCODED from the source dataset
    ('"## Title\\n..."' — literal quotes and backslash-n): decode when the
    value is such a wrapper, pass through otherwise (Verified is clean)."""
    if isinstance(s, str) and len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        try:
            d = json.loads(s)
            if isinstance(d, str):
                return d
        except json.JSONDecodeError:
            pass
    return s or ""


def _official_task_text(row: dict) -> str:
    """The benchmark's OWN task text. For SWE-bench Pro that is problem
    statement + requirements brief + new-interface list — the exact template
    of the official harness (scaleapi/SWE-bench_Pro-os,
    helper_code/create_problem_statement.py); the tasks are AUTHORED
    underspecified and refined via the requirements, and the hidden
    fail-to-pass tests are written against them, so issue-only is a strictly
    harder non-canonical variant. Rows without those fields (Verified) keep
    the plain problem statement."""
    ps = _decoded(row.get("problem_statement", "") or "")
    pro = row.get("pro") or {}
    if not isinstance(pro, dict) or not (
            "requirements" in pro or "interface" in pro):
        return ps
    req = _decoded(pro.get("requirements") or "")
    iface = _decoded(pro.get("interface") or "")
    return (f"{ps}\n\nRequirements:\n{req}\n\n"
            f"New interfaces introduced:\n{iface}")


def _frozen_row(instance_id: str) -> dict | None:
    with DATASET_JSONL.open() as fh:
        for line in fh:
            if f'"{instance_id}"' in line:
                row = json.loads(line)
                if row.get("instance_id") == instance_id:
                    return row
    return None


def _localization(instance_id: str) -> dict:
    """Precomputed offline edit-localization for one instance, from
    scripts/build_eval_localization.py. Empty when the file or the entry is
    missing; whether that is fatal is the mode's question, not this reader's."""
    if not EVAL_LOCALIZATION.exists():
        return {}
    try:
        return json.loads(EVAL_LOCALIZATION.read_text()).get(instance_id, {}) or {}
    except json.JSONDecodeError:
        return {}


def _entries(raw) -> list[dict]:
    """Localization entries from either shape a bundle records them in.

    Most bundles record a dict per modeled function; a few record only the repo
    symbol, as a bare string. A string still says where to edit, so it is
    normalized rather than dropped -- dropping it is what made four velvet cells
    raise "mode 0 has no localization" while their meta.json named the function.
    """
    out = []
    for m in raw or []:
        if isinstance(m, str) and m.strip():
            out.append({"repo_symbol": m.strip(), "repo_location": ""})
        elif isinstance(m, dict) and m.get("repo_symbol"):
            out.append({"repo_symbol": m["repo_symbol"],
                        "repo_location": m.get("repo_location", "")})
    return out


def build_task(adapter: EvalAdapter, instance_id: str, mode: int,
               include_hints: bool = False) -> EvalTask:
    """Agent-visible task for an instance + mode. Raises on unknown instance.
    Withheld fields are never read into the result."""
    if mode not in ALL_MODES:
        raise ValueError(f"unknown mode {mode}; expected one of {ALL_MODES}")
    if mode == 8 and adapter.backend.name == "ears":
        raise ValueError("mode 8 is not applicable for the ears backend "
                         "(no verifying witness exists; spec quality is "
                         "measured via the audited modes instead)")
    row = _frozen_row(instance_id)
    if row is None:
        raise ValueError(f"{instance_id} not in frozen dataset")
    task = EvalTask(
        instance_id=instance_id,
        repo=row.get("repo", ""),
        base_commit=row.get("base_commit", ""),
        problem_statement=_official_task_text(row),
        mode=mode,
        backend=adapter.backend.name,
        hints_text=(row.get("hints_text", "") or "") if include_hints else "",
    )

    # Bundle meta is consulted only where the adapter declares it a source of
    # localization; otherwise localization comes from the offline
    # eval_localization.json. Reading meta unconditionally would hand a
    # localization mode more than its definition allows.
    meta = (adapter.bundle_meta(instance_id)
            if (adapter.modeled_functions_from_meta
                and mode in (MODES_WITH_SPEC | MODES_WITH_LOCALIZATION)) else {})

    if mode in MODES_WITH_LOCALIZATION:
        # ONLY repo_symbol + repo_location + changed files — no modeling/spec
        # detail, isolating "where to edit" from "how/verification".
        raw, files = [], []
        if adapter.modeled_functions_from_meta:
            raw = _entries(meta.get("modeled_functions"))
            files = list(meta.get("changed_files") or [])
        # The offline derivation is the fallback for every backend, PER FIELD: a
        # bundle that records the symbols but not the changed files still gets its
        # files from it, and a backend whose bundle carries no localization at all
        # gets both. Without the fallback such a bundle silently becomes a mode-0
        # run reporting numbers from a mode-10 information environment.
        if not raw or not files:
            loc = _localization(instance_id)
            raw = raw or _entries(loc.get("localization"))
            files = files or list(loc.get("changed_files") or [])
        task.localization = raw
        task.changed_files = files
        if mode in MODES_REQUIRE_LOCALIZATION and not task.gives_localization:
            # Loud, because the quiet version is a run that reports mode-0
            # numbers for a mode-10 information environment.
            raise ValueError(
                f"{instance_id}: mode {mode} is defined by its edit localization "
                f"and neither source has any: the bundle's meta.json "
                f"(modeled_functions / changed_files) nor {EVAL_LOCALIZATION} — "
                f"build the latter with "
                f"`python scripts/build_eval_localization.py`")

    if mode in MODES_WITH_SPEC:
        model = adapter.model_src(instance_id)
        if model is None:
            raise ValueError(f"{instance_id}: no {adapter.solution_filename} to "
                             f"derive spec_view (mode {mode})")
        # adapter.spec_view refuses to expose an unelided view (guard over G-LEAK)
        try:
            task.spec_view = adapter.spec_view(model)
        except ValueError as e:
            raise ValueError(f"{instance_id}: {e}") from e
        if adapter.supports_float_encoding:
            # Source parity: nagini sets float_encoding ONLY in spec modes
            # (1,2); in from-scratch modes the agent picks its own via the tool
            # arg and grading uses the default. Do not "fix" without a parity
            # rerun.
            task.float_encoding = meta.get("float_encoding")
        # modeled functions: nagini/velvet from meta.json (dict entries only);
        # lean uses the repo-side localization (no model mapping in its bundle)
        if adapter.modeled_functions_from_meta:
            task.modeled_functions = [m for m in (meta.get("modeled_functions", []) or [])
                                      if isinstance(m, dict)]
        else:
            task.modeled_functions = task.localization
    return task


def as_dict(task: EvalTask) -> dict:
    """Serializable agent-visible view — only agent-allowed fields, safe to
    persist alongside the trajectory."""
    d = {
        "instance_id": task.instance_id, "repo": task.repo,
        "base_commit": task.base_commit, "mode": task.mode,
        # record metadata only; never included in agent prompts (info-env parity)
        "backend": task.backend,
        "problem_statement": task.problem_statement,
    }
    if task.hints_text:
        d["hints_text"] = task.hints_text
    if task.gives_localization:
        d["localization"] = task.localization
        d["changed_files"] = task.changed_files
    if task.gives_spec:
        d["spec_view"] = task.spec_view
        d["modeled_functions"] = task.modeled_functions
        # emitted only when set (nagini); agent-visible value unchanged
        if task.float_encoding is not None:
            d["float_encoding"] = task.float_encoding
    return d


# frozen-row fields that must NEVER appear in any agent-visible view
WITHHELD_FIELDS = ("patch", "test_patch", "FAIL_TO_PASS", "PASS_TO_PASS")


def assert_no_leak(task_dict: dict) -> None:
    """The serialized agent view must not carry any withheld field."""
    bad = [k for k in WITHHELD_FIELDS if k in task_dict]
    if bad:
        raise AssertionError(f"agent view leaks withheld fields: {bad}")
