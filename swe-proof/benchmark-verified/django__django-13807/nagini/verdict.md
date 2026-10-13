# P2 adversarial audit — django__django-13807

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
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-13807 nagini bundle. No diverging input found; spec is faithful to real repo behavior.

Empirical evidence (all run from /tmp worktree at base_commit 89fc144dedc737a79929231438f035b1d4a993c9):

1) delimit/delimit_id axiom EXACTLY matches the real callee. Real django/db/backends/sqlite3/operations.py:170-173 quote_name is verbatim: `if name.startswith('"') and name.endswith('"'): return name; return '"%s"' % name`. Ran the bundle's axiom_check.py against the REAL quote_name (PYTHONPATH to worktree) -> exit 0, sound over 35 boundary + 20000 fuzz identifiers. Independently confirmed axiom==real on tricky edges ('', '"', '""', '"a', 'a"', 'a"b', '\x00', ' ', SQL keywords). The axiom is an exact model (not merely weakest), so it can never reject a value the real callee accepts -> not too strong.

2) build_single_table_command postcondition: single_table_prefix()+delimit(table_name)+close_paren(). Verified prefix code points spell exactly 'PRAGMA foreign_key_check(' and suffix ')'. Real code: 'PRAGMA foreign_key_check(%s)' % quote_name(table_name). Single-%s interpolation of a str == concatenation (format specs only parsed in the literal, identifiers with '%' insert verbatim). Byte-faithful.

3) build_three_id_command uses opaque placeholder constants three_id_head/sep/mid ([1,2]/[3]/[4,5]) instead of literal 'SELECT '/', '/' FROM '. This abstraction is applied IDENTICALLY to model.py and model_prepatch.py, so it does not strengthen or weaken the discriminating clause; load-bearing properties (each of the 3 identifiers delimited, correct order) preserved. WHERE rowid=%%s tail is a constant identifier-free suffix, correctly omitted. No induced disagreement.

4) same-spec: SAME (exit 0). nagini_verify.sh on bundle model: Verification successful (16.15s). Prepatch fails postconditions (bug sensed, G-DIFF). 

No input exists on which the modeled functions disagree with real check_constraints command assembly / quote_name in a spec-too-strong direction.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker (3) leakage/gold-reconstruction review of nagini django__django-13807 spec view (projected via swebench_unified.markers.spec_view, impl regions elided). The spec view is strictly MORE abstract than the public problem_statement and leaks nothing about the gold edit beyond it: (1) the fix requirement ('each spliced identifier must be the backend's *delimited* form, never bare') is exactly what the public problem_statement already states ('table name order is not quoted properly', 'missing back ticks around %s'); (2) the hints-only term quote_name does NOT appear — it is abstracted to the neutral axiom `delimit`; (3) no repo coordinates leak: 'base.py','operations.py','SELECT','foreign_key_list','primary_key','column_name','ops.' are all absent from the view; (4) the single_table_prefix code points decode to 'PRAGMA foreign_key_check(', but that literal SQL is verbatim in the public problem_statement, so not disclosure beyond it; (5) the undisclosed SELECT site #3 (columns/table) is deliberately hidden behind opaque placeholder constants ([1,2],[3],[4,5]) and neutral names ident_a/b/c — a suppression, not a leak; hits on 'order'/'table_name' in the view are the English phrase 'in order' and a benign param name. Machine checks: substring scan of spec_view negative for quote_name/base.py/operations.py/SELECT/foreign_key_list/primary_key/column_name/ops./966b/pull-13807. meta.json G-LEAK=pass corroborates.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
