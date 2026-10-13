# P2 adversarial audit — django__django-11138

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 6 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The audit re-ran 6 candidate wrong implementations against this specification, each changing the implementation and leaving the specification as this bundle ships it. None of them verified without also resolving the instance, which is what a counterexample to `verify => correct` would require. The positive control verifies, so the specification is satisfiable by a correct implementation and that outcome is not an artifact of a specification nothing can satisfy.

**How far this record can be re-checked.** The attack sources are not carried in this bundle. The count above and the positive-control outcome are what the harness recorded; the sources and their individual outcomes are not, so this role is the one part of the cell a reader cannot re-run from the bundle alone. The audit record states the same limitation.

_The attack bodies behind this role's verdict are not carried in this bundle. The count of attacks re-run and the positive-control outcome are recorded above; the sources themselves are not, so this role is the one part of the cell a reader cannot re-verify from the bundle alone._

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / spec-drifts-from-repo) check for django__django-11138 nagini bundle. The modeled function local_walltime/normalised_walltime models the SQLite read path _sqlite_datetime_parse (sqlite3/base.py:401, the F2P-executed callee: test_query_convert_timezones on SQLite). Verdict FAITHFUL — the model agrees with the real callee on every in-domain input at the observable granularity.

Evidence:
1. same-spec: SAME (exit 0) for the unmodified bundle model. A first pass wrote a generically named atk.py whose contents were overwritten before the comparison, producing a spurious cross-instance diff; re-run with a per-instance attack filename it is SAME. Model verifies with pinned Nagini in 11.4s (exit 0).
2. axiom_check.py (G-AX) passes exit 0: deep model == real datetime/pytz relabel+convert over F2P instants + boundary matrix + 20000 fuzz, actual pytz offsets (LMT/replace subtlety honoured).
3. Independent second-precision fuzz (200,000 samples, seed 999) comparing the model against the REAL gold operation (typecast naive -> replace(conn) -> astimezone(target)) across DST/half-hour/45-min zones NOT in axiom_check's list (Australia/Sydney, Pacific/Chatham, America/St_Johns, Europe/Paris, Asia/Kathmandu, plus LMT-sensitive Asia/Bangkok): 0 minute-level mismatches, 0 DATE-level mismatches. The 196,733 TIME-level 'mismatches' are solely the DECLARED minute-granularity abstraction dropping the seconds component (mapping.md §2) — the F2P observable is .date(), which never diverges; sub-minute rounding never flips a whole-day boundary here (offsets are whole-minute).
4. Precondition Requires(use_tz or not has_target) excludes exactly the case not use_tz AND has_target, which is UNREACHABLE in the real code: _convert_tznames_to_sql emits (NULL, NULL) when not USE_TZ so tzname is None (has_target False). Hence not an over-strong precondition that would drop reachable behavior.
5. Guard-divergence probe: model uses target_off != conn_off where real uses tzname != conn_tzname. Two distinct zone names sharing one offset make real call astimezone (net stored - conn_off + target_off == stored) while the model takes the restore branch (stored) — identical observable, no divergence.

No diverging input found; the spec is neither too strong nor drifted from repo behavior on the tested/observable domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction check for django__django-11138 (nagini). The public problem_statement is an unusually explicit bug report that already discloses the entire desired behavior: (1) 'conversion should go from the database timezone tz2 to the django app one tz1' instead of UTC->Paris; (2) 'when tz1 == tz2, there should be no need to use CONVERT_TZ'; and (3) it even links the exact source line where 'UTC' is hard-wired. Every behavioral fact pinned by the spec view is fully derivable from that baseline:
- The pure model normalised_walltime and postconditions state the net shift is (target_off - conn_off) = re-expressing the stored connection-zone wall clock in the target zone — the math form of 'convert from tz2 to tz1'.
- The comment 'the source zone is the CONNECTION offset, never a hard-wired universal zero' restates problem_statement's core complaint about UTC being forced.
- The Ensures(conn_off==target_off => Result()==stored) and comment 'no-conversion optimisation is observationally the identity' restate 'when tz1==tz2 no need for CONVERT_TZ'.
- use_tz off / no target => passthrough restates the settings.USE_TZ guard already visible in the linked code region and the problem_statement.
The spec uses only abstract modeling identifiers (conn_off, target_off, has_target, use_tz, integer-minutes wall clock) and does NOT expose any gold-edit-specific implementation structure: no self.connection.timezone_name, no CONVERT_TZ/FROM_TZ SQL string edits, no sqlite create_function arity changes (2->3, 3->4), no conn_tzname parameter threading, no _convert_tznames_to_sql rename. Those concrete edit shapes are unrecoverable from the spec view. This is a legitimate formalization of a detailed public bug report, not a disclosure of the gold patch beyond problem_statement. Spec view rendered via markers.spec_view with the nagini backend; impl region correctly elided.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
