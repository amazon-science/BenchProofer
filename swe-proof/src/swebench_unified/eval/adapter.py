# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The EvalAdapter: the SINGLE place where per-backend eval differences live
(docs/adding_a_backend.md §4). The rest of eval/ is one shared code path, which
is what makes a cross-backend number a comparison of methods rather than of
harnesses. What belongs here: the agent's verifier tool and its arguments,
host-side source checking, the solution filename, hygiene/anti-fakery rules and
mechanical feedback, spec-view elision plus the leak guard, the judge-side check
tool name, gold-reference artifact names, and the quickref block. A per-backend
`if` chain anywhere else under eval/ should be moved here.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from ..backends import Backend, get_backend
from ..benchmarks import active_workdir
from ..markers import ELISION_IMPL, ELISION_PROOF, spec_view
from ..paths import bundle_dir
from ..verify import VerifyResult, verify_source_via
from .providers import ToolSpec

VERIFY_TIMEOUT = 300

# audit/metrics scan saved trajectories, so must recognize any backend's tool
# (ears_lint is the ears backend's lint tool — there is no verifier for it)
VERIFY_TOOL_NAMES = ("nagini_verify", "velvet_verify", "lean_verify", "ears_lint")

# Eval-side allowlist deltas over Backend.language.import_allowlist: velvet's
# eval harness additionally allowed CaseStudies/Loom/Auto (Velvet front-door
# deps that agent models legitimately import).
_EVAL_ALLOWLIST_EXTRA = {
    "nagini": (),
    "velvet": ("CaseStudies", "Loom", "Auto"),
    "lean": (),
    "ears": (),
}

_LEAN_BLOCK_COMMENT = re.compile(r"/-.*?-/", re.DOTALL)
_LEAN_LINE_COMMENT = re.compile(r"--[^\n]*")


def _strip_lean_comments(src: str) -> str:
    """Blank Lean comments (preserving newlines) so hygiene scans don't match
    prose in doc comments."""
    src = _LEAN_BLOCK_COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), src)
    return _LEAN_LINE_COMMENT.sub("", src)


def _banned_hit(stripped: str, code: str) -> bool:
    """Match banned tokens exactly as construction-side G-HYGIENE: identifiers
    on word boundaries, operator-ish tokens by substring."""
    if stripped.isidentifier():
        return re.search(rf"(?<![\w.]){re.escape(stripped)}(?![\w])", code) is not None
    return stripped in code


# lean-backend structural checks (from lean eval/grade.py)

_THEOREM_RE = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)*theorem\s+[A-Za-z_][\w'.]*"
    r"([^\n]*(?:\n(?![^\s])[^\n]*)*)", re.MULTILINE)


def _theorem_states_obligation(code: str) -> bool:
    """Some theorem's statement mentions a problem_spec_* symbol (only the spec
    side is pinned; implementation names vary)."""
    for m in _THEOREM_RE.finditer(code):
        if re.search(r"\bproblem_spec\w*", m.group(1)):
            return True
    return False


_DECL_RE = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)*(?:noncomputable\s+)?(def|abbrev|axiom)\s+([A-Za-z_][\w'.]*)"
    r"([^\n]*(?:\n(?![^\s])[^\n]*)*)", re.MULTILINE)

_SPEC_IMPL_RE = re.compile(r"\bproblem_spec\w*|\bimplementation_\w+")


def _axiom_wraps_obligation(code: str) -> bool:
    """True iff an `axiom` mentions a spec/impl symbol, directly or via
    file-local def/abbrev aliases (conservative regex fixpoint)."""
    decls = [m.groups() for m in _DECL_RE.finditer(code)]

    def _mentions(text: str, names: set[str]) -> bool:
        if _SPEC_IMPL_RE.search(text):
            return True
        return any(re.search(rf"(?<![\w.']){re.escape(n)}(?![\w'])", text)
                   for n in names)

    tainted: set[str] = set()
    changed = True
    while changed:
        changed = False
        for kind, name, body in decls:
            if kind in ("def", "abbrev") and name not in tainted \
                    and _mentions(body, tainted):
                tainted.add(name)
                changed = True
    return any(kind == "axiom" and _mentions(body, tainted)
               for kind, name, body in decls)


@dataclass
class EvalAdapter:
    """Per-backend eval seam. Build with `get_adapter(name)`."""
    backend: Backend
    tool_name: str                 # agent-facing verifier tool
    check_tool_name: str           # judge-facing checker tool (grade.py mode 8)
    solution_filename: str         # model.py | Solution.lean
    lang_fence: str                # markdown fence language: python | lean
    supports_float_encoding: bool  # nagini only (meta.json / tool arg)
    eval_import_allowlist: tuple[str, ...] = ()
    banned_tokens: tuple[str, ...] = ()
    # non-submit-exit model recovery: candidate model FILENAMES (relative to the
    # checkout — this adapter is per-backend and holds no benchmark, so the
    # container path is only knowable at use time; see guess_model_paths) plus a
    # token a real model file must contain
    guess_model_names: tuple[str, ...] = ()
    spec_marker_token: str = ""
    contract_label: str = ""       # "honest Nagini/Velvet/Lean contract"
    # spec modes: nagini/velvet read modeled_functions from the bundle's
    # meta.json; lean reuses the offline edit localization (source parity)
    modeled_functions_from_meta: bool = False

    @staticmethod
    def for_backend(backend: Backend) -> "EvalAdapter":
        name = backend.name
        sol = backend.language.solution_filename
        allow = tuple(backend.language.import_allowlist) + _EVAL_ALLOWLIST_EXTRA[name]
        if name == "nagini":
            return EvalAdapter(
                backend=backend, tool_name="nagini_verify",
                check_tool_name="nagini_check", solution_filename=sol,
                lang_fence="python", supports_float_encoding=True,
                eval_import_allowlist=allow,
                banned_tokens=("Assume", "Refute"),   # matched as AST calls
                guess_model_names=("model.py", "spec.py"),
                spec_marker_token="Ensures",
                contract_label="model is an honest Nagini contract",
                modeled_functions_from_meta=True)
        if name == "velvet":
            return EvalAdapter(
                backend=backend, tool_name="velvet_verify",
                check_tool_name="velvet_check", solution_filename=sol,
                lang_fence="lean", supports_float_encoding=False,
                eval_import_allowlist=allow,
                banned_tokens=backend.language.banned_tokens,
                guess_model_names=("Solution.lean", "Model.lean"),
                spec_marker_token="ensures",
                contract_label="model is an honest Velvet contract",
                modeled_functions_from_meta=True)
        if name == "lean":
            return EvalAdapter(
                backend=backend, tool_name="lean_verify",
                check_tool_name="lean_check", solution_filename=sol,
                lang_fence="lean", supports_float_encoding=False,
                eval_import_allowlist=allow,
                banned_tokens=backend.language.banned_tokens,
                guess_model_names=("Solution.lean", "Model.lean"),
                spec_marker_token="problem_spec",
                contract_label="model is an honest Lean contract")
        if name == "ears":
            # NO verifier: the "verify" tool is the EARS structural LINT and
            # every surface labels it so. check_tool_name="" — the mode-8
            # spec judge gets no checker tool (behavioral probes only).
            return EvalAdapter(
                backend=backend, tool_name="ears_lint",
                check_tool_name="", solution_filename=sol,
                lang_fence="markdown", supports_float_encoding=False,
                eval_import_allowlist=allow,
                banned_tokens=(),
                guess_model_names=("requirements.md",),
                spec_marker_token="SHALL",
                contract_label="requirements document is well-formed, "
                               "non-vacuous EARS")
        raise ValueError(f"no eval adapter for backend {name!r}")

    def guess_model_paths(self, workdir: str | None = None) -> tuple[str, ...]:
        """Container paths to try when recovering a model on a non-submit exit:
        each candidate name under the checkout, then the container ROOT as a last
        resort (an agent that never `cd`s writes to /). `workdir` defaults to the
        active benchmark's container_workdir, resolved at CALL time — the same
        convention docker_exec uses — because the adapter is per-backend and a
        run's benchmark is not known where the names are declared."""
        if not self.guess_model_names:
            return ()
        if workdir is None:
            workdir = active_workdir()
        base = workdir.rstrip("/")
        return (tuple(f"{base}/{n}" for n in self.guess_model_names)
                + (f"/{self.guess_model_names[0]}",))

    def verify_tool_spec(self, workdir: str | None = None) -> ToolSpec:
        """The agent's verifier tool. `workdir` (default: the active benchmark's
        container_workdir) only fills in the EXAMPLE path in the argument
        description — agent-visible text, so it must name a directory that
        exists in this benchmark's image."""
        if workdir is None:
            workdir = active_workdir()
        example = f"{workdir.rstrip('/')}/{self.solution_filename}"
        if self.backend.name == "ears":
            return ToolSpec(
                self.tool_name,
                "Run the EARS structural LINT on YOUR requirements.md in the "
                "container. There is NO formal verifier for this task type — "
                "'verified' here means only that the document is well-formed "
                "EARS (Introduction, numbered requirements, user stories, "
                "WHEN/THEN...SHALL acceptance criteria). Semantic adequacy is "
                "judged separately.",
                {"path": {"type": "string",
                          "description": "path to the requirements .md file in the "
                                         f"container, e.g. {example}"}},
                ["path"])
        if self.backend.name == "nagini":
            return ToolSpec(
                self.tool_name,
                "Run the Nagini verifier on YOUR candidate model file in the "
                "container. Returns whether it verifies, or the verifier's error "
                "output. Use this to check your model satisfies its own spec "
                "before submitting.",
                {"path": {"type": "string",
                          "description": "path to the model .py file in the container, "
                                         f"e.g. {example}"},
                 "float_encoding": {"type": "string",
                                    "description": "optional Nagini --float-encoding value "
                                                   "(e.g. 'real'); omit if unsure"}},
                ["path"])
        if self.backend.name == "velvet":
            return ToolSpec(
                self.tool_name,
                "Run the Velvet (Lean 4 + Loom) verifier on YOUR candidate model "
                "file in the container. Returns whether it verifies, or the "
                "verifier's error output. Use this to check your model satisfies "
                "its own spec before submitting.",
                {"path": {"type": "string",
                          "description": "path to the model .lean file in the container, "
                                         f"e.g. {example}"}},
                ["path"])
        return ToolSpec(
            self.tool_name,
            "Run the Lean 4 + Mathlib verifier on YOUR candidate model file in "
            "the container. Returns whether it verifies (compiles with a closed "
            "proof, no sorry), or the verifier's error output. Use this to check "
            "your correctness theorem holds before submitting.",
            {"path": {"type": "string",
                      "description": "path to the model .lean file in the container, "
                                     f"e.g. {example}"}},
            ["path"])

    def check_tool_spec(self) -> ToolSpec:
        """The mode-8 spec-judge's checker tool (grade.py). ears has none
        (check_tool_name="") — callers must guard on check_tool_name."""
        if not self.check_tool_name:
            raise ValueError(f"backend {self.backend.name!r} has no judge "
                             f"checker tool (no verifier)")
        if self.backend.name == "nagini":
            desc = ("Run the Nagini verifier on a candidate model you write (use "
                    "the solver's exact signatures/spec, your own impl body). "
                    "Returns whether it VERIFIES. Use it to test soundness (a "
                    "correct impl must verify) and completeness (a wrong impl "
                    "must NOT verify).")
            src_desc = "full Nagini model source to verify"
        elif self.backend.name == "velvet":
            desc = ("Run the Velvet (Lean 4 + Loom) verifier on a candidate model "
                    "you write (use the solver's exact signatures/spec, your own "
                    "impl body). Returns whether it VERIFIES. Use it to test "
                    "soundness (a correct impl must verify) and completeness (a "
                    "wrong impl must NOT verify).")
            src_desc = "full Velvet/Lean model source to verify"
        else:
            desc = ("Run the Lean 4 + Mathlib verifier on a candidate model you "
                    "write (use the solver's exact signatures/spec, your own impl "
                    "body + proof). Returns whether it VERIFIES. Use it to test "
                    "soundness (a correct impl must verify) and completeness (a "
                    "wrong impl must NOT verify).")
            src_desc = "full Lean model source to verify"
        return ToolSpec(self.check_tool_name, desc,
                        {"model_src": {"type": "string", "description": src_desc}},
                        ["model_src"])

    def check_source(self, src: str, timeout: int = VERIFY_TIMEOUT,
                     float_encoding: str | None = None) -> VerifyResult:
        """HOST-verify the candidate source — the agent's own artifact only (no
        repo code, no hidden tests). `float_encoding`: nagini only."""
        if self.supports_float_encoding and float_encoding:
            check = lambda p, t: self.backend.check(p, t, float_encoding=float_encoding)  # noqa: E731
            return verify_source_via(check, src, self.solution_filename, timeout)
        return self.backend.check_source(src, timeout)

    def bundle_dir(self, instance_id: str) -> Path:
        return bundle_dir(instance_id, self.backend.name)

    def model_src(self, instance_id: str) -> str | None:
        p = self.bundle_dir(instance_id) / self.solution_filename
        return p.read_text() if p.exists() else None

    def gold_prepatch_src(self, instance_id: str) -> str | None:
        """The benchmark's KNOWN-BUGGY witness (<stem>_prepatch<suffix>);
        canonical name first, then any variant (lean bundles may carry several)."""
        root = self.bundle_dir(instance_id)
        stem, suffix = Path(self.solution_filename).stem, Path(self.solution_filename).suffix
        canonical = root / f"{stem}_prepatch{suffix}"
        if canonical.exists():
            return canonical.read_text()
        others = sorted(root.glob(f"{stem}_prepatch*{suffix}"))
        return others[0].read_text() if others else None

    def gold_axiom_check_src(self, instance_id: str) -> str | None:
        p = self.bundle_dir(instance_id) / "axiom_check.py"
        return p.read_text() if p.exists() else None

    def bundle_meta(self, instance_id: str) -> dict:
        """Bundle meta.json; {} when absent. A CORRUPT meta raises (source
        parity) — it feeds the information environment, so fail loudly."""
        import json
        p = self.bundle_dir(instance_id) / "meta.json"
        return json.loads(p.read_text()) if p.exists() else {}

    def float_encoding(self, instance_id: str) -> str | None:
        if not self.supports_float_encoding:
            return None
        return self.bundle_meta(instance_id).get("float_encoding")

    def spec_view(self, model_src: str) -> str:
        """Leak-safe projection via the unified markers module, with the hard
        guard: every impl (and lean proof) region must actually be elided."""
        sv = spec_view(model_src, self.backend.language)
        if "impl-start" in model_src and ELISION_IMPL not in sv:
            raise ValueError("spec_view failed to elide impl — refusing to expose")
        if ("proof" in self.backend.language.region_names
                and "proof-start" in model_src and ELISION_PROOF not in sv):
            raise ValueError("spec_view failed to elide proof — refusing to expose")
        # velvet: proofs are `prove_correct ... by` tactic bodies, not a marker
        # region — the elider keeps the header line and stubs only the tactic
        # body. Guard added on critic review (source only guarded impl).
        if ("proof" not in self.backend.language.region_names
                and self.backend.language.flavor == "lean"
                and "prove_correct" in model_src and ELISION_PROOF not in sv):
            raise ValueError("spec_view failed to elide prove_correct body — refusing to expose")
        return sv

    def mechanical_feedback(self, src: str) -> str:
        """Non-leaking feedback on mechanical conventions (import allowlist, no
        verification-faking escapes, real contract). '' when nothing to flag."""
        if self.backend.name == "nagini":
            return self._nagini_feedback(src)
        if self.backend.name == "ears":
            from ..ears_lint import analyze
            return "\n".join(f"  - {p}" for p in analyze(src).problems)
        return self._lean_flavor_feedback(src)

    def _nagini_feedback(self, src: str) -> str:
        msgs = []
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            return f"  - the model file does not parse: {e}"
        roots, banned, has_ensures = set(), set(), False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    roots.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in self.banned_tokens:
                    banned.add(node.func.id)
                elif node.func.id == "Ensures":
                    has_ensures = True
        bad = roots - set(self.eval_import_allowlist)
        if bad:
            msgs.append(f"  - import only `typing` and `nagini_contracts.*` (saw: {sorted(bad)}). "
                        f"Model the relevant behaviour yourself rather than importing "
                        f"repo/stdlib code.")
        if banned:
            msgs.append(f"  - remove {sorted(banned)}: Assume/Refute can fake verification and are "
                        f"disallowed — the model must verify honestly.")
        if not has_ensures:
            msgs.append("  - add at least one `Ensures(...)` postcondition that actually pins the "
                        "required behaviour (a model with no/empty postcondition proves nothing).")
        return "\n".join(msgs)

    def _lean_flavor_feedback(self, src: str) -> str:
        code = _strip_lean_comments(src)
        msgs = []
        bad_imports = sorted({
            m.group(1).split(".")[0]
            for m in re.finditer(r"^\s*import\s+([A-Za-z_][\w.]*)", code, re.MULTILINE)
            if m.group(1).split(".")[0] not in self.eval_import_allowlist
        })
        if bad_imports:
            front = ("the Velvet front door + Lean/Mathlib core"
                     if self.backend.name == "velvet" else "Lean/Mathlib core")
            msgs.append(f"  - import only {front} "
                        f"({', '.join(self.eval_import_allowlist)}); "
                        f"saw disallowed root(s): {bad_imports}. "
                        f"Model the relevant behaviour yourself rather than importing "
                        f"repo/stdlib code.")
        banned = sorted({s for s in (t.strip() for t in self.banned_tokens)
                         if _banned_hit(s, code)})
        if banned:
            hint = ("native_decide/Classical.choice/unsafe/extern are disallowed"
                    if self.backend.name == "velvet"
                    else "native_decide/unsafe/extern are disallowed")
            msgs.append(f"  - remove {banned}: these defeat the proof (sorry/admit leave it "
                        f"incomplete; {hint}) — the model must verify honestly.")
        if self.backend.name == "velvet":
            if not re.search(r"\bensures\b", code):
                msgs.append("  - add at least one `ensures` postcondition that actually pins the "
                            "required behaviour (a model with no/empty postcondition proves "
                            "nothing).")
        else:  # lean
            if not re.search(r"\bProp\b", code):
                msgs.append("  - add a `problem_spec_<name> … : Prop` specification predicate that "
                            "actually pins the required behaviour (a model with no/vacuous spec "
                            "proves nothing).")
            if not re.search(r"\btheorem\b", code):
                msgs.append("  - add a `theorem correct_<name> : ∀ …, problem_spec_<name> … "
                            "(implementation_<name> …)` correctness theorem with a closed proof — "
                            "an implementation without a proved theorem verifies nothing.")
        return "\n".join(msgs)

    def antifakery(self, model_src: str | None) -> tuple[bool, str]:
        """Minimal anti-fakery guard so "verifies" MEANS something — NOT a
        structural/marker check. Spec STRENGTH is the equivalence judge's job."""
        if not model_src:
            return False, "no model"
        if self.backend.name == "nagini":
            return self._nagini_antifakery(model_src)
        if self.backend.name == "ears":
            return self._ears_antifakery(model_src)
        return self._lean_flavor_antifakery(model_src)

    def _ears_antifakery(self, model_src: str) -> tuple[bool, str]:
        """Non-vacuity heuristics for a requirements document: structurally
        valid EARS with enough substance that 'lint-clean' means something —
        several SHALL criteria and at least one behavioral (WHEN/WHILE/IF)
        trigger. Semantic adequacy is the spec audit / judge's job."""
        from ..ears_lint import analyze
        rep = analyze(model_src)
        problems = list(rep.problems)
        if rep.n_criteria < 3:
            problems.append(f"only {rep.n_criteria} acceptance criteria — a "
                            "requirements document this thin pins nothing")
        # (the missing-trigger case is already a lint problem via analyze())
        return (not problems), ("; ".join(problems) or self.contract_label)

    def _nagini_antifakery(self, model_src: str) -> tuple[bool, str]:
        problems = []
        try:
            tree = ast.parse(model_src)
        except SyntaxError as e:
            return False, f"model does not parse: {e}"
        roots, banned, has_ensures = set(), set(), False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    roots.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in self.banned_tokens:
                    banned.add(node.func.id)
                elif node.func.id == "Ensures":
                    has_ensures = True
        bad_imports = roots - set(self.eval_import_allowlist)
        if bad_imports:
            problems.append(f"imports outside allowlist: {sorted(bad_imports)}")
        if banned:
            problems.append(f"verification-faking calls: {sorted(banned)}")
        if not has_ensures:
            problems.append("no Ensures postcondition (an empty/vacuous spec proves nothing)")
        return (not problems), ("; ".join(problems) or self.contract_label)

    def _lean_flavor_antifakery(self, model_src: str) -> tuple[bool, str]:
        code = _strip_lean_comments(model_src)
        problems = []
        bad_imports = sorted({
            m.group(1).split(".")[0]
            for m in re.finditer(r"^\s*import\s+([A-Za-z_][\w.]*)", code, re.MULTILINE)
            if m.group(1).split(".")[0] not in self.eval_import_allowlist
        })
        if bad_imports:
            problems.append(f"imports outside allowlist: {bad_imports}")
        banned = sorted({s for s in (t.strip() for t in self.banned_tokens)
                         if _banned_hit(s, code)})
        if banned:
            problems.append(f"verification-faking tokens: {banned}")
        if self.backend.name == "velvet":
            if not re.search(r"\bensures\b", code):
                problems.append("no ensures postcondition (an empty/vacuous spec proves nothing)")
        else:  # lean — a hand-proved backend needs the stricter structure
            if not re.search(r"\bProp\b", code):
                problems.append("no Prop specification predicate "
                                "(an empty/vacuous spec proves nothing)")
            if not _theorem_states_obligation(code):
                problems.append("no correctness theorem stating a problem_spec_* obligation "
                                "(an unrelated/vacuous theorem proves nothing)")
            if _axiom_wraps_obligation(code):
                problems.append("an `axiom` references the spec/implementation symbols "
                                "(directly or via a local alias) — axiomatizing the "
                                "correctness obligation instead of proving it")
        return (not problems), ("; ".join(problems) or self.contract_label)

    def quickref(self) -> str:
        """Backend quick-reference block (prompts/<backend>/quickref.md)."""
        return self.backend.quickref()


def get_adapter(backend: str | Backend) -> EvalAdapter:
    be = backend if isinstance(backend, Backend) else get_backend(backend)
    return EvalAdapter.for_backend(be)
