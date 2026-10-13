# Prompt corpus

Every agent prompt the pipeline uses, as data rather than code. Loaded by
`swebench_unified.prompts.load_prompt(name, backend, **subs)`, which tries four
paths in this order and takes the first that exists:

1. `$SBU_PROMPTS_DIR/<backend>/<name>.md`
2. `$SBU_PROMPTS_DIR/shared/<name>.md`
3. `prompts/<backend>/<name>.md`
4. `prompts/shared/<name>.md`

`SBU_PROMPTS_DIR` is the only override; there is no flag. A miss raises
`PromptNotFound` listing every path tried, so a partial override directory fails
loudly rather than silently running a different experiment than the configured
one.

A prompt lives in `shared/` when it is language-general and in `<backend>/` when
it names that backend's artifact shape, verifier invocation, or contract idiom.
Adding a backend therefore means adding a `prompts/<backend>/` directory with
the per-backend files below; everything in `shared/` is inherited.

Substitution is `str.format` and only runs when subs are passed. Two rules
follow: a file that takes placeholders must escape literal braces as `{{ }}`,
and a file loaded with no subs keeps its braces as-is (the judge schema files
rely on this, since they are literal JSON). `load_prompt` takes `backend`
itself, so a template placeholder may not be named `{backend}` — the
manifest-authoring prompt uses `{backend_name}`.

Per-instance material (issue text, candidate model/patch, gold references,
spec/localization blocks) is assembled in code, not stored here; only the
reusable prompt TEXT is a file.

## Construction — `construct/build_one.py`

System = `construct_system`, user = `worker`. A worktree note and per-round
refinement feedback are appended in code.

| file | purpose | placeholders |
|---|---|---|
| `<b>/worker.md` | construction worker prompt | `{iid}`, `{root}` |
| `<b>/spec_guide.md` | binding spec-construction rules, referenced by the worker | none |
| `<b>/construct_system.md` | construction system prompt | none |

## Proof phase (Lean-family backends) — `prove.py`

System = `proof_system`, user = `proof_agent` (`{iid}`). Under axiom refinement,
`axiom_propose_system` + `axiom_propose`.

| file | purpose | placeholders |
|---|---|---|
| `lean/proof_system.md` | proof agent system prompt | none |
| `lean/proof_agent.md` | proof agent task prompt, with the playbook appended | `{iid}` |
| `lean/proof_playbook.md` | the playbook alone (reference copy) | none |
| `lean/axiom_propose_system.md` | axiom-propose system prompt | none |
| `lean/axiom_propose.md` | axiom-propose task prompt | `{iid}`, `{stuck}` |

## G-PBT manifest authoring — `construct/build_one.py:author_pbt_manifest`

Opt-in (`build_one --pbt`). One agent runs after the bundle is green and writes
`properties.py`, the falsification battery G-PBT then judges mechanically. The
falsification classes are language-general, so all of these are shared; backend
mechanics are reached through `<b>/spec_guide.md` and `{solution_filename}`. The
last two rows belong to the batch drivers (`scripts/pbt_port_fleet.py`,
`scripts/pbt_audit_fleet.py`) rather than to `build_one`.

| file | purpose | placeholders |
|---|---|---|
| `shared/pbt_author_system.md` | adversarial-engineer system prompt | none |
| `shared/pbt_author.md` | manifest-authoring task prompt | `{iid}`, `{backend_name}`, `{root}` |
| `shared/pbt_port.md` + `_system` | port an existing battery to another backend | `{iid}`, `{backend_name}`, `{root}`, `{solution_filename}`, `{src_backend}` |
| `shared/pbt_audit.md` + `_system` | adversarially audit a battery | `{iid}`, `{backend_name}`, `{root}`, `{solution_filename}` |

## Audit — `gates/_audit.py:run_audit`

Per role r in {eq, panel_1, panel_2, panel_3}: system = `audit_<r>`, user =
`audit_<r>_task` (`{instance_id}`, `{bundle_dir}`, `{scratch}`).

| file | purpose | placeholders |
|---|---|---|
| `<b>/audit_eq.md` | G-EQ, refinement fidelity | none |
| `<b>/audit_panel_1.md` | G-PANEL-1, spec-too-weak attacker | none |
| `shared/audit_panel_2.md` | G-PANEL-2, faithfulness-break attacker | none |
| `shared/audit_panel_3.md` | G-PANEL-3, leakage attacker | none |
| `<b>/audit_<r>_task.md` | task wrapper: bundle files, verify toolkit, submit schema | `{instance_id}`, `{bundle_dir}`, `{scratch}` |

The two mechanized roles do not trust the agent's verdict.
`build_one._derive_audit_verdict` re-runs every submitted attack artifact and
derives the verdict itself: a same-spec impl that verifies fails G-PANEL-1, and
a verifying impl whose faithful patch does not resolve fails G-EQ. A pass also
requires the falsification floor (at least `MIN_ATTACKS` distinct canonical
attacks, the prepatch bug reproduced, and a structurally different positive
control that verifies), else the role is INCONCLUSIVE and fails closed. This is
why the task wrappers ask for `attacks` / `positive_control` /
`prepatch_reproduced` / `patches` rather than a verdict.

The two judgment roles have no executable oracle, so they remain evidence-gated
self-reports and a pass may not also cite a defect. A FAIL from any role is
therefore sound (a reproduced counterexample); a PASS means "survived a bounded
adversarial search", which is the ceiling without an exhaustive proof.

## Spec repair — `scripts/spec_repair_fleet.py`

One prompt per `--mode`, chosen by the defect class the driver is closing.

| file | purpose | placeholders |
|---|---|---|
| `shared/spec_repair.md` + `_system` | `--mode repair`: a spec an audit proved TOO WEAK | `{iid}`, `{bk}`, `{root}`, `{python}`, `{spec_files}` |
| `shared/spec_panel.md` + `_system` | `--mode panel`: an UNFAITHFUL or LEAKING spec | as above plus `{roles}` |
| `shared/spec_mech.md` + `_system` | `--mode mech`: an artifact a mechanical gate refuted | as `spec_repair` plus `{gate}` |

## Eval — mode prompts (`eval/prompts.py`, `backends/base.py`)

`system_prompt()` composes a header + `eval_common_rules` +, in verifier modes,
`quickref`. `initial_user()` is `eval_mode_<M>` followed by issue / hints /
localization / spec blocks assembled in code.

| file | purpose | placeholders |
|---|---|---|
| `shared/eval_common_rules.md` | ground rules | `{repo}`, `{multisite}`, `{workdir}` |
| `<b>/quickref.md` | verifier quick reference; appended whenever the mode offers the verifier (1, 2, 3, 4, 11, and 100 on a verifier-backed backend) | none |
| `shared/eval_mode_4.md`, `shared/eval_mode_0.md` | localization / baseline task prompts | `{workdir}` |
| `<b>/eval_mode_{2,3,5,6,7}.md` | verifier-mode task prompts | `{workdir}` |
| `<b>/eval_mode_8.md` | spec-generation task prompts | none used (still rendered) |

Mode 100 on a backend with no verifier is agent-side identical to mode 0, since
its only difference is a grading-time audit, so it reuses the baseline `eval_mode_0` rather
than duplicating the file.

The verifier modes are kept per backend rather than parameterized: they differ
structurally, not just in nouns (a `problem_spec` predicate plus a theorem to
prove, versus `require`/`ensures`, versus `Requires`/`Ensures` with
`@ContractOnly`).

`{workdir}` is the ONE container fact these files carry: the active benchmark's
`container_workdir` (`/testbed` on SWE-bench_Verified, `/app` on SWE-bench Pro),
substituted by `eval/prompts.py`. "still rendered" above is the part that bites:
`_mode_task` passes `{workdir}` to EVERY mode file, so a file that happens not to
use it is a `str.format` target all the same, and a literal brace anywhere in one
— including in an `SBU_PROMPTS_DIR` override — must be doubled. That is why
`tests/test_prompts.py` checks the `eval_*` files by name rather than by whether
they declare a placeholder, and why `load_prompt` names the offending file at
runtime for the overrides it cannot see.

## Eval — judge prompts (`eval/grade.py`)

`grade.py` loads the system prompts and schema hints only; the judge user
prompts (candidate and gold blocks, truncations) are assembled in code with the
schema hint appended. The schema files hold literal JSON braces and are loaded
WITHOUT substitutions — never pass subs to them.

| file | purpose | placeholders |
|---|---|---|
| `<b>/judge_equivalence_system.md` | given-spec judge (mode 1) | none |
| `<b>/judge_equivalence_scratch_system.md` | spec-from-scratch judge (modes 4 and 100) | none |
| `<b>/judge_specgen_system.md` | adversarial spec-audit judge (mode 8) | none |
| `shared/judge_equivalence_schema.md` | verdict-JSON schema hint, given-spec | none (literal braces) |
| `shared/judge_equivalence_scratch_schema.md` | verdict-JSON schema hint, from-scratch | none (literal braces) |
| `shared/judge_specgen_schema.md` | verdict-JSON schema hint, mode 8 | none (literal braces) |
