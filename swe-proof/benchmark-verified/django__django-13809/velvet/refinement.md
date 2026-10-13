# refinement.md — django__django-13809

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`runStartupChecks` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The gating site — `inner_run()` system-checks block (`runserver.py:117-118`)

Gold hunk:
```
-        self.stdout.write("Performing system checks...\n\n")
-        self.check(display_num_errors=True)
+        if not options['skip_checks']:
+            self.stdout.write('Performing system checks...\n\n')
+            self.check(display_num_errors=True)
```

| # | Solution.lean impl op (`runStartupChecks`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `skipChecks : Bool` (read-only) | `options['skip_checks']` (argparse `store_true` bool) | R | `bool ↔ Bool` (mapping.md §2). Read-only: the routine consults it and never writes it (directive 5 — not `mut`). |
| A2 | entry `require announced = false` / observable `announced` | the occurrence of `self.stdout.write("Performing system checks...\n\n")` | R | occurrence-flag refinement (mapping.md §2): `announced` is `true` iff that write executed. False on entry (the announcement has not yet happened at this point of startup). |
| A3 | entry `require checked = false` / observable `checked` | the occurrence of `self.check(display_num_errors=True)` | R | occurrence-flag refinement (mapping.md §2): `checked` is `true` iff `self.check(...)` was invoked. False on entry. The check routine is unchanged and its result is not pinned — only its invocation. |
| A4 | `if !skipChecks then announced := true; checked := true else return ()` | `if not options['skip_checks']: <write>; <check>` | I | identical control flow: the two effects fire together exactly when the flag is not set; both branches transliterated concretely (G-CONF). The empty `else` mirrors the gold's implicit no-op fall-through (neither effect occurs). |
| A5 | post `ensures announced = (!skipChecks)` and `ensures checked = (!skipChecks)` | the observable consequence of the guard | I | the exact behavior the F2P test pins: `skip_checks=True ⇒` no announcement and `check` not called; `skip_checks=False ⇒` announcement written and `check` called. Both observables pinned to the *same* `!skipChecks` because the gold guards both effects with the one condition (neither may occur independently). |

Discriminating content of the change — the two effects are now CONDITIONAL on
`not options['skip_checks']` rather than unconditional. `Solution_prepatch.lean`
reproduces the pre-patch skeleton (both effects performed unconditionally,
consulting no flag) and **fails** both `ensures announced = (!skipChecks)` and
`ensures checked = (!skipChecks)`: with `skipChecks = true` the spec demands both
stay `false`, but the unconditional skeleton sets them `true` (G-DIFF). This is
exactly the bug the F2P test `ManageRunserver.test_skip_checks` catches.

## B. The argument-registration site — `add_arguments()` (`runserver.py:50-53`)

Gold hunk:
```
+        parser.add_argument(
+            '--skip-checks', action='store_true',
+            help='Skip system checks.',
+        )
```

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `skipChecks : Bool` free input | `parser.add_argument('--skip-checks', action='store_true', ...)` | R | declarative argument registration with no algorithmic content: it only makes the boolean `options['skip_checks']` exist and reach `inner_run`. Refined to "`skipChecks` is a free boolean input" — its presence/value is the whole effect. Nothing to compute, nothing to pin, no separate observable behavior. |

No separate failing prepatch for site B: a missing argument registration is a
*declarative* defect, not an algorithmic one — there is no `do`-block operation
whose behavior could diverge under the frozen spec, and a prepatch must keep the
spec byte-identical (G-DIFF). Its only behavioral consequence — that
`options['skip_checks']` exists and feeds the guard at site A — is already
exercised by site A's prepatch (which observes both values of `skipChecks`). The
two gold hunks are one indivisible behavior: register the flag, then honor it.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — making the two
startup effects conditional on the request flag — is a pure control-flow guard,
modeled **directly** (the `if !skipChecks` branch and the two occurrence-flag
writes, step A4), not hidden behind any axiom. There are **no consumed axioms**
and **no A-reference deep models** in this bundle: the two effects
(`self.stdout.write`, `self.check`) are modeled as occurrence flags, not as
callees whose return contract the proof consumes (mapping.md §3). Hence no
`axiom_check.py` and G-AX is skipped.

## D. verify(Solution) ⇒ resolved

`runStartupChecks` verifies only if both observables equal `!skipChecks` (A5):
each effect occurs exactly when the operator did not request a skip. By R (the
`bool ↔ Bool` and occurrence-flag bijections of mapping.md §2) this is exactly
the gold guard `if not options['skip_checks']: <announce>; <check>` at site A,
fed by the `--skip-checks` flag registered at site B. By G-CONF the R/I
transliteration of the guard agrees with `patch.diff`'s behaviour on both
boolean inputs plus ≥10⁵ fuzz. There are no axioms, so there is no G-AX trust
point. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement — and the gold patch resolves (G-RESOLVE). The
sole trust point of plan §1.1 in play is refinement fidelity (this doc, G-EQ +
G-CONF); axiom soundness is vacuous (no axioms).
