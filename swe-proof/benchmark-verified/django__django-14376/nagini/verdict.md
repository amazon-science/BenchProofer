# P2 adversarial audit — django__django-14376

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 7 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical to the bundle (same-spec exit 0). The /tmp worktree client.py already carries the gold-patched three-level selection `database = OPTIONS.get('database', OPTIONS.get('db', NAME))` with the trailing append `if database: args += [database]`. I ran the REAL gold-patched DatabaseClient.settings_to_cmd_args_env against the model's select_name/resolve_db_arg predictions (append iff non-empty): 100 boundary configs (names x {absent, optiondbname, deprecateddbname, altname, ''} for both option keys) => 0 mismatches, plus 20,000 randomized fuzz cases including empty strings, slashes, flag-like values ('--flag'), spaces, and unicode => 0 mismatches. The precedence discriminator holds: when both 'database' and 'db' options are present with different non-empty values, the real callee selects the non-deprecated 'database' value, matching the model's first branch. dict.get membership semantics (a present key short-circuits the fallback even for empty '') match the model's Optional[List[int]] None=absent abstraction. str truthiness `if database:` <-> len>0 matches. No input exists where the modeled function disagrees with the real callee. The spec is neither too strong nor drifted; it is a faithful, tight abstraction of the gold-patched behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage check: does the spec view (model.py + refinement.md/mapping.md) disclose the gold edit beyond the public problem_statement (hints excluded)?

What the PUBLIC problem_statement already discloses: the gold edit's core is fully public. It names the exact kwarg renames db->database and passwd->password, states mysqlclient deprecated 'db'/'passwd' 'in favor of "database" and "password"', and links the precise source lines (base.py L202-L205) and mysqlclient commits. The rename that is the heart of patch.diff is therefore not secret.

What model.py adds: an abstract behavioral spec of the CLIENT-side name selection (select_name / resolve_db_arg) with three-level precedence: non-deprecated option > legacy 'db' option > settings NAME. This is stated as desired behaviour, not as an edit. It uses abstract carriers (List[int]/PSeq[int] code points, Optional[...] for present/absent) and never quotes the gold diff expression settings_dict['OPTIONS'].get('database', ...get('db', NAME)) nor gives edit sites. The 'precedence with the deprecated key still honored' framing follows directly from the public directive to migrate from a DEPRECATED (not removed) key, i.e. backward compat is implied by 'deprecated'.

Parameter names opt_database/opt_db mirror the option keys, but those keys ('database','db') are already named verbatim in the public problem_statement, so no new information is exposed.

The base.py passwd->password hunk is explicitly NOT modeled (mapping.md §4), so it cannot leak.

No spec-view line encodes the gold edit's location or diff text beyond what problem_statement already publishes. The precedence detail is a legitimate behavioral spec derivable from the public deprecation directive, not a reconstruction of the gold edit. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
