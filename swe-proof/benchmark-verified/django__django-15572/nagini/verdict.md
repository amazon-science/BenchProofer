# P2 adversarial audit — django__django-15572

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 8 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 8 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Investigated in the real repo worktree at base_commit 0b31e024. Findings:

1. SPEC INTACT & MODEL VERIFIES. Positive control: the bundle model.py verifies in pinned Nagini (exit 0, 11.9s). axiom_check.py passes against the real callees (exit 0). Gate snapshot: G-AX/G-DIFF/G-EQ/G-GOLD/G-VERIFY/G-RESOLVE all pass (G-RESOLVE resolved, gold patch applies).

2. THE ONE GENUINE DIVERGENCE (dot-paths). The type abstraction maps a directory entry str/Path -> int token by truthiness, with join_base(d)==d != 0 (a distinct, non-base location) for EVERY present entry. The real site is `cwd / to_path(dir) for dir in dirs if dir`. On a truthy dot-path such as "." the two disagree: real -> {cwd} (collapses onto the BASE location, yet truthy so passes the `if dir` guard), model -> a distinct non-base token. Confirmed empirically: cwd/to_path(".")==cwd is True while bool(".") is True.

3. WHY THIS IS FAITHFUL, NOT A DEFECT (spec is NOT too strong):
   - Out of tested domain. The F2P/P2P inputs are "", absolute str, "template_tests/relative_str", Path("template_tests/relative_path"), EXTRA_TEMPLATES_DIR — verified none is a bare dot; the P2P set has size 3 (all present entries distinct), matching the model's ordered-subsequence-as-set refinement.
   - No false universal is published. mapping.md §2/§3.2 and refinement.md A3/D scope notes EXPLICITLY decline to assert "every truthy entry joins to a distinct location", and axiom_check.py actively exercises the dot-path family (".","./.","././.","./",Path(".")) as the boundary where truthiness != distinctness, so the evidence is non-vacuous.
   - Load-bearing fact is a genuine universal. The empty-entry collapse cwd/to_path("")==cwd (the F2P DIRS:[""] => set() scenario) is validated universally (~3000 fuzz empties). Present-entry distinctness is validated only on the configured/tested corpus (~17000 fuzz non-dot entries), never as a universal.
   - The verify => resolved chain depends only on (a) the empty-entry collapse and (b) distinctness on the tested entries — never on the dot-path over-claim. So the model agrees with the real callee on every tested input; it diverges only on the untested, explicitly-documented dot-path boundary.

Conclusion: the spec accommodates the gold patch (which resolves) and does not drift from real behaviour on any tested input. The dot-path divergence is a known, documented, deliberately-non-relied-upon abstraction boundary, not a spec-too-strong / faithfulness break. VERDICT: FAITHFUL. (Note: G-PANEL-1 is separately marked fail in meta; that is a different panel attacker's concern, not this faithfulness axis.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (3) leakage / gold-reconstruction assessment for django__django-15572 (nagini).

Gold edit (public patch): add a truthiness guard on the raw entry at each of the two collection sites in get_template_directories() — `for dir in backend.engine.dirs if dir` and `if directory and not is_django_path(directory)`.

What the PUBLIC problem_statement already discloses: the bug is an empty string ('' / ['']) in TEMPLATES DIRS; empty strings normalize to the project root so template_changed() always returns True; and the statement explicitly recommends the fix `filter(None, os.getenv(...).split(','))` — i.e. drop empty entries before collecting. So 'filter out empty directory entries' is already public, gold-relevant knowledge.

Spec view (consumer-visible, generated via markers.spec_view over NaginiBackend): specifies the desired behaviour abstractly — 'an entry contributes its joined watched location exactly when present (non-empty); an empty entry contributes nothing', modeled with opaque integer tokens (0 = empty), pure helpers is_present/join_base/selected_direct/selected_provider, and postconditions ToSeq(Result()) == selected_direct/provider(ToSeq(entries)). The two impl bodies are elided.

Leakage assessment vs problem_statement (NOT hints_text):
- No repo-specific identifiers appear in the spec view: it never names django/template/autoreload.py, get_template_directories, backend.engine.dirs, loader.get_dirs, cwd / to_path, is_django_path, or the literal `if dir` guard. Those repo bindings live only in mapping.md / refinement.md (auditor artifacts, not the consumer spec view).
- The behavioral content the spec pins (empty entry contributes nothing) is exactly the empty-string-filtering fix the problem_statement already publishes via the filter(None, ...) suggestion. A legitimate behavioral spec of the corrected function.
- The 'beneath_framework' predicate is disclosed as the UNCHANGED pre-existing callee (is_django_path); revealing an unchanged filter conjunct does not reveal the gold edit. The two-site structure is inherent to specifying the function, not a disclosure of the diff.

The spec is a behavioral specification (its job is to state correct behaviour) and does not reconstruct the gold edit beyond what problem_statement already makes public. No single spec-view line uniquely encodes the diff location/tokens.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
