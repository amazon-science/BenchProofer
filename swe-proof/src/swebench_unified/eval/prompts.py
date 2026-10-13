# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Per-mode prompt ASSEMBLY for the eval agent; prompt TEXT lives in the
file-based registry (load_prompt). Which blocks a mode gets is decided here and
nowhere else, so a mode's information environment is auditable in one place.

Expected prompt files (per backend, falling back to shared; PromptNotFound at
runtime is acceptable-by-design if the corpus lacks a file):
  eval_common_rules.md (placeholders {repo} {multisite} {workdir}),
  eval_mode_{0,2,3,4,5,6,7,8}.md (placeholder {workdir}), and
  prompts/<backend>/quickref.md (appended to the system prompt in modes
  1,2,3,4,11 via adapter.quickref()).

{workdir} is the active benchmark's `container_workdir` — the directory the
agent's checkout lives in (/testbed on SWE-bench_Verified, /app on SWE-bench
Pro). It is substituted here rather than written literally because these files
are the agent's information environment: a prompt naming a directory the image
does not have is a prompt that sends the agent to the wrong place. Note that
passing ANY substitution makes a file a strict str.format target, so every
literal brace in it (including in an SBU_PROMPTS_DIR override) must be doubled
— which is what tests/test_prompts.py checks.

The multi-site clause is phrased with/without a localization reference
depending on whether the mode shows a localization block (0/1/2 do), so
nothing dangles — as in the sources.
"""
from __future__ import annotations

from ..benchmarks import active_workdir
from ..prompts import load_prompt
from .adapter import EvalAdapter
from .dataset import EvalTask

_MULTISITE_LOC = (
    "Any function(s) named below mark where the CORE change goes, but they are "
    "usually NOT the only edit"
)
_MULTISITE_NOLOC = (
    "The fix usually has a CORE change, but that is usually NOT the only edit"
)


def _common_rules(adapter: EvalAdapter, task: EvalTask) -> str:
    multisite = _MULTISITE_LOC if task.gives_localization else _MULTISITE_NOLOC
    return load_prompt("eval_common_rules", backend=adapter.backend.name,
                       repo=task.repo, multisite=multisite, workdir=active_workdir())


def _mode_task(adapter: EvalAdapter, task: EvalTask) -> str:
    # Audited twins are agent-side identical to their unaudited pair (the
    # audit is a grading-time difference the agent never sees) — one prompt
    # file, no drift: ears 100 -> 0, and 101 -> 10 for every backend.
    # Formal mode 5 ("verified mode 4") has its own prompt file.
    mode = task.mode
    if task.mode == 5 and task.backend == "ears":
        mode = 4
    elif task.mode == 1:
        mode = 0
    return load_prompt(f"eval_mode_{mode}", backend=adapter.backend.name,
                       workdir=active_workdir())


def _spec_block(adapter: EvalAdapter, task: EvalTask) -> str:
    if not task.gives_spec:
        return ""
    # nagini: float-encoding hint travels with the spec (source parity)
    fe = ""
    if adapter.supports_float_encoding and task.float_encoding:
        fe = f"\nFloat encoding for verification: --float-encoding={task.float_encoding}"
    fns = ""
    if task.modeled_functions:
        if adapter.modeled_functions_from_meta:
            # nagini/velvet: model_symbol ↔ repo_symbol pairs
            fns = "\nModeled function(s): " + ", ".join(
                f"{m.get('model_symbol', '?')} (↔ {m.get('repo_symbol', '?')})"
                for m in task.modeled_functions)
        else:
            # lean: repo-side localization only
            fns = "\nModeled repo function(s): " + ", ".join(
                f"{m.get('repo_symbol', '?')}"
                + (f"  ({m.get('repo_location')})" if m.get("repo_location") else "")
                for m in task.modeled_functions)
    label = {"nagini": "Nagini spec view",
             "velvet": "Velvet/Lean spec view",
             "lean": "Lean 4 spec view",
             "ears": "EARS requirements document"}[adapter.backend.name]
    if adapter.backend.language.flavor == "ears":
        # natural-language spec: nothing is elided — the document is complete
        return (f"\n\n--- SPECIFICATION ({label}; complete — your patch must "
                f"satisfy every SHALL) ---{fns}\n\n"
                f"```{adapter.lang_fence}\n{task.spec_view}\n```\n")
    elided = ("the implementation and proof are elided — that is what you must supply"
              if "proof" in adapter.backend.language.region_names
              else "the implementation is elided — that is what you must supply")
    return (f"\n\n--- FORMAL SPECIFICATION ({label}; {elided}) ---{fe}{fns}\n\n"
            f"```{adapter.lang_fence}\n{task.spec_view}\n```\n")


def _localization_block(task: EvalTask) -> str:
    """Edit-localization aid, rendered standalone only when there is NO spec
    (mode 4); modes 7/6 show it via the spec block's modeled functions."""
    if task.gives_spec or not task.gives_localization:
        return ""
    lines = []
    for loc in task.localization:
        sym, where = loc.get("repo_symbol", ""), loc.get("repo_location", "")
        lines.append(f"  - {sym}" + (f"  ({where})" if where else ""))
    files = "\n".join(f"  - {f}" for f in task.changed_files)
    body = ""
    if lines:
        body += "\nFunction(s) to modify:\n" + "\n".join(lines)
    if files:
        body += "\nFile(s) changed:\n" + files
    return ("\n\n--- EDIT LOCALIZATION (where the fix goes; the SAME information the "
            "spec modes get, with NO specification or verification detail) ---" + body + "\n")


def system_prompt(adapter: EvalAdapter, task: EvalTask) -> str:
    rules = _common_rules(adapter, task)
    quickref = ""
    # verifier modes (7,6,2,3,8, formal 100): quick-reference on tool
    # mechanics — verifier conventions, not hints about the fix.
    if task.offers_verifier:
        quickref = "\n\n" + adapter.quickref()
    return ("You are an expert software engineer being evaluated on resolving a "
            "real GitHub issue.\n\n" + rules + quickref)


def initial_user(adapter: EvalAdapter, task: EvalTask) -> str:
    parts = [_mode_task(adapter, task)]
    parts.append(f"\n\n--- ISSUE (problem statement) ---\n{task.problem_statement}")
    if task.hints_text:
        parts.append(f"\n\n--- HINTS ---\n{task.hints_text}")
    parts.append(_localization_block(task))    # mode 4 (spec modes show it via the spec)
    parts.append(_spec_block(adapter, task))   # modes 7,6
    parts.append("\nBegin. Inspect the repository with `bash`, make your edits, and "
                 "`submit` when ready.")
    return "".join(parts)
