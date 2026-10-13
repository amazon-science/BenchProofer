# P2 adversarial audit — django__django-13363

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
- **machine verdict:** Instance django__django-13363, nagini bundle. Attack goal: show the spec is too strong / drifts from real repo behavior. Result: no divergence found — spec is FAITHFUL.

Real callee (post-patch, verified against repo at base_commit 76e0151ea0e0f56dca66cee846a78b89346d2c4c): TruncDate.as_sql and TruncTime.as_sql (django/db/models/functions/datetime.py:292/305) delegate to TimezoneMixin.get_tzname (datetime.py:17-28):
  - settings.USE_TZ False               -> None
  - USE_TZ True, self.tzinfo is None    -> timezone.get_current_timezone_name()  (ambient)
  - USE_TZ True, self.tzinfo present    -> timezone._get_timezone_name(self.tzinfo) == self.tzinfo.tzname(None)  (supplied)

Modeled selected_tzname(use_tz, tzinfo, current_name): not use_tz -> None; tzinfo is not None -> tzinfo; else -> current_name. Both date_cast_tzname/time_cast_tzname pin exactly `Result() is selected_tzname(...)`.

Under the mapping's name abstraction (a tzinfo object <-> its name List[int]; _get_timezone_name(tz)==tz.tzname(None) is the identity; None<->no tz; USE_TZ bool identity; ambient str<->current_name) the three model branches match the real get_tzname branch-for-branch on ALL inputs. The postcondition is `is`-identity on the exact selected value — the tightest possible pin, not an over-strong one; it neither adds constraints nor drifts. The two downstream backend SQL builders (datetime_cast_{date,time}_sql) are unchanged, deterministic consumers of tzname with identical lhs, so equal tzname => equal SQL (not part of the spec).

Machine checks (from project root, swebench-lean env):
  - same-spec on the byte-identical bundle model.py: SAME, exit 0 (NOTE: a generically named atk.py was overwritten with an unrelated django-13158 model before the comparison; re-run under the per-instance name atk_13363_fb.py, whose md5 matches the bundle model.py, it is SAME).
  - scripts/nagini_verify.sh model.py: Verification successful, 10.31s, exit 0 (spec is satisfiable, not vacuous/over-strong).
  - axiom_check.py: exit 0, deep-model three-branch logic exercised on 2018 boundary+fuzz inputs; Django absent on host so pytz-only fallback ran (container G-AX validates the REAL get_tzname). No mismatch on any input.

No diverging input exists between the modeled function and the real callee. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view byte-identical to bundle: recomputed spec_view sha256 = 0c0c932b121f58d8dde74359062dae34f0f142824d1e24c3af8e424c35bd02cc == recorded region_hashes.spec_view. Spec view = docstring + imports + empty axioms + Pure selected_tzname + pre/post-conditions; BOTH impl regions elided to `...`.

Gold edit: in TruncDate.as_sql/TruncTime.as_sql replace `tzname = timezone.get_current_timezone_name() if settings.USE_TZ else None` with `tzname = self.get_tzname()`.

What the spec view discloses: only the abstract three-case selection rule (USE_TZ off -> None; supplied tzinfo -> its name; else ambient name) and the discriminating clause that a supplied zone must not be silently discarded.

This is fully within the PUBLIC problem_statement (hints excluded), which already states verbatim: (a) the code 'uses the return value from get_current_timezone_name() unconditionally and completely discards the passed in timezone info object'; (b) 'This should allow a developer to pass in a tzinfo object to be used'; and (c) links the exact offending line (L295) AND the method it should use (L17 = get_tzname). The problem_statement is in fact MORE revealing than the spec view (it names get_tzname; the spec view does not).

The concrete gold token self.get_tzname()/TimezoneMixin.get_tzname appears ONLY in the private refinement.md, never in the spec view. Both impl regions are elided, so no implementation/delegation is disclosed. A solver reading the spec view learns no more about the concrete fix than the public problem_statement already provides. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `refinement.md`, which ships in this bundle, so a reader can start there.
