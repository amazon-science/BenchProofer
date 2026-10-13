# P2 adversarial audit — django__django-13297

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_3.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,6 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
-    w = wrap_resolvable(value)  # type: Wrapped
+    w = wrap_opaque(value)  # type: Wrapped
     return w
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -509,5 +509,8 @@
     # post-conditions-end
     # impl-start
     w = wrap_resolvable(value)  # type: Wrapped
+    if not own_type_unpreparable(value):
+        peek = run_deferral(w, value, 0)  # type: int
+        Assert(peek == value)
     return w
     # impl-end
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 3] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,9 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
+    if own_type_unpreparable(value):
+        spare = wrap_opaque(value)  # type: Wrapped
+        raise Exception()
     w = wrap_resolvable(value)  # type: Wrapped
     return w
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,9 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
-    w = wrap_resolvable(value)  # type: Wrapped
-    return w
+    if value < 0:
+        a = wrap_resolvable(value)  # type: Wrapped
+        return a
+    b = wrap_opaque(value)  # type: Wrapped
+    return b
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,8 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
+    if value == 0:
+        raise Exception()
     w = wrap_resolvable(value)  # type: Wrapped
     return w
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,8 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
+    if not own_type_unpreparable(value):
+        raise Exception()
     w = wrap_resolvable(value)  # type: Wrapped
     return w
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -509,5 +509,7 @@
     # post-conditions-end
     # impl-start
     w = wrap_resolvable(value)  # type: Wrapped
+    other = wrap_opaque(value + 7)  # type: Wrapped
+    burned = run_deferral(other, value + 7, 0)  # type: int
     return w
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,8 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
-    w = wrap_resolvable(value)  # type: Wrapped
+    probe = wrap_opaque(value)  # type: Wrapped
+    seen = run_deferral(probe, value, 0)  # type: int
+    w = wrap_resolvable(seen)  # type: Wrapped
     return w
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,9 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
-    w = wrap_resolvable(value)  # type: Wrapped
-    return w
+    if own_type_unpreparable(value):
+        a = wrap_opaque(value)  # type: Wrapped
+        return a
+    b = wrap_resolvable(value)  # type: Wrapped
+    return b
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,9 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
+    if own_type_unpreparable(value):
+        r = wrap_kwarg_value(value)  # type: Wrapped
+        return r
     w = wrap_resolvable(value)  # type: Wrapped
     return w
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,8 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
-    w = wrap_resolvable(value)  # type: Wrapped
+    real = wrap_resolvable(value)  # type: Wrapped
+    Assert(binder_accepts(real))
+    w = Wrapped()  # type: Wrapped
     return w
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -509,5 +509,9 @@
     # post-conditions-end
     # impl-start
     w = wrap_resolvable(value)  # type: Wrapped
+    i = 0  # type: int
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
     return w
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -509,5 +509,7 @@
     # post-conditions-end
     # impl-start
     w = wrap_resolvable(value)  # type: Wrapped
+    if not own_type_unpreparable(value):
+        seen = run_deferral(w, value, -1)  # type: int
     return w
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,5 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
-    w = wrap_resolvable(value)  # type: Wrapped
-    return w
+    return wrap_resolvable(value)
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-13297 (nagini). VERDICT: SOUND. Per brief, concentrated on the A legs and the model<->patch correspondence; R/I legs left to G-CONF.

**SAME-SPEC:** all 13 attacks + the positive control return exit 0 from `adversary same-spec nagini django__django-13297 <f>` -- only the impl region differs, so no attack cheats by weakening a contract.

POSITIVE CONTROL (non-vacuity): atk_pos.py is a structural reshape, not a copy -- `return wrap_resolvable(value)`, collapsing the gold's named-local-then-return. `adversary weakness` -> exit 0 (CANDIDATE, verifies 15.5s). So the 12 rejections are genuine, not a verifier that refuses everything.

**COMMAND FOR EVERY ATTACK:** `python -m swebench_unified.adversary weakness nagini django__django-13297 <atk_N.py>` (exit 2 = rejected/good, exit 0 = CANDIDATE); clause text from `bash scripts/nagini_verify.sh` on the same file. Verifications were run 3-at-a-time as concurrent background jobs (each Nagini check spawns JVM+Z3); scheduling only, every attack fully verified.

atk_1  PREPATCH BUG (`wrap_opaque(value)`, the non-Promise SimpleLazyObject image) -> exit 2. Error: 'insufficient permission to access binder_accepts(Result())'. prepatch_reproduced=TRUE; G-DIFF sensing is real. atk_2  PRIOR-AUDIT HOLE RE-ENCODED (eager resolution during assembly): build the gold entry, `peek = run_deferral(w, value, 0)`, `Assert(peek == value)`, hand the CORRECT entry on -> exit 2, 'deferrals_run(0)'. Facets (1)/(2) hold verbatim, so ONLY obligation (3) can reject -- and it does. THE PRIOR HOLE IS CLOSED. atk_3  ABORT ON THE ABSTRACT PARTIALITY FAMILY, having first allocated and discarded a hookless stand-in -> exit 0, CANDIDATE.

RESOLVE-CHECKED, see below. atk_4  PARTIAL-DOMAIN (resolvable on value<0, pre-patch hookless stand-in on value>=0, where the F2P str tag lands) -> exit 2, binder_accepts(Result()). atk_5  BOUNDARY ABORT at the single tag value==0 (type_of's collapse boundary) -> exit 2, 'Assertion own_type_unpreparable(value) might not hold'. Arithmetic on the tag cannot decide the abstract family. atk_6  INVERTED GUARD: abort OFF the family, return on it -> exit 2, same Exsures guard. Confirms the guard is directional, not a free abort licence. atk_7  CONTROL-FLOW EFFECT charged to ANOTHER value's throwaway: the returned entry is the gold one and never touched; a side stand-in for `value + 7` has ITS deferral run -> exit 2, deferrals_run(0).

The ledger is indexed by neither entry nor value nor construction. atk_8  UNGROUNDED-ORACLE ECHO: recover the value via a cheap opaque probe (`seen = run_deferral(probe, value, 0)`), rebuild the RETURNED entry from the echoed int (`wrap_resolvable(seen)`) so every value-level clause is discharged by the echo -> exit 2, deferrals_run(0). No answer-key without charging the ledger. atk_9  A-LEG GRACEFUL-DEGRADATION FALLBACK (the realistic wrong fix): on exactly the guarded family, hand back the PRE-PATCH hookless stand-in instead of aborting -> exit 2, binder_accepts(Result()).

KEY A-LEG PROBE for the recognition/resolution split: guarding binder_castable is NOT a licence to return a binder-REFUSED stand-in, because binder_accepts is unconditional. mapping.md's 'keeps the contract non-silent on the unpreparable family' bites. atk_10 DIVERGENCE via a FEASIBLE guarded self-call on the family -> exit 2, 'Obligation leak check failed. Callee wrap_kwarg_value might not take all unsatisfied obligations from the caller'. MustTerminate(14) is at the METHOD level, so an unbounded self-call is refused rather than verified vacuously. atk_11 CAPABILITY FROM NOWHERE: build the real entry, `Assert(binder_accepts(real))`, then return a bare `Wrapped()` and try to discharge the clauses on IT -> exit 2, 'insufficient permission to access deferral_of(Result(), value)'.

Not a Fold attempt (an invalid program): the postcondition is simply unprovable, which is what unforgeability must mean. atk_12 CONTROL-FLOW DIVERGENCE: build the correct entry, then spin in `while i >= 0` -- every value-level, capability and ledger clause holds verbatim, so ONLY termination can reject -> exit 2, 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context'. Had it verified, the refined patch would hang the mapping assembly and the F2P test would never return. atk_13 LEDGER-ARITHMETIC UNDERFLOW: run the deferral charged to index -1, so `deferrals_run(-1 + 1)` is literally the postcondition `deferrals_run(0)` -> exit 2, 'The precondition of method run_deferral might not hold. There might be insufficient permission to access deferrals_run(n)'. The ledger is not forgeable by arithmetic: deferrals_run(-1) has no producer.

**TALLY:** 12 rejected with clause-attributable errors; 1 CANDIDATE, resolve-checked. Rejections distribute across obligations -- binder_accepts (atk_1,4,9), deferrals_run (atk_2,7,8), deferral_of (atk_11), the A9 Exsures guard (atk_5,6), run_deferral's ledger precondition (atk_13), method-level MustTerminate (atk_10,12). No single clause carries the spec.

CANDIDATE RESOLVE (the mandatory G-EQ step): atk_3's faithful refined patch is atk_3.diff -- gold's `lazy(access_value, type(value))()` plus a faithful classifier that aborts on exactly the `own_type_unpreparable` family (the build's own exception, plus the route-(ii) bytes-arm detected as `type(entry)._delegate_bytes and not isinstance(value, bytes)`), allocating and discarding a SimpleLazyObject stand-in on the way out to mirror the attack's discarded spare. Confirmed to apply at base_commit 8954f255bbf5f4ee997fd6de62cb50fc9b5dd697 via `git apply --check` in a detached worktree of the upstream repository -> 'Checking patch django/views/generic/base.py... APPLY-CHECK OK'.

Verified out-of-band that the classifier partitions the family EXACTLY as axiom_check.py measures and WITHOUT running any deferral: all 18 abort-route witnesses (13 type-valued + `_MroData`/`_MroOneArg`/`_MroProp`/`_EqBoom`/`_EqAll`) -> family/abort, both bytes-arm witnesses (`_EqBytesOnly`, `_IntBytesArm`) -> family/bytes-arm, and all 17 not_type_valued witnesses -> off-family. Also measured on the patched tree: building 5 entries raises 0 notices, the entries ARE Promises, the real Field.get_prep_value resolves them to the value at its own real type with exactly 1 notice each, construction survives an escalating configuration while resolution raises RemovedInDjango40Warning, and the aborting exits raise 0 notices.

RUN via `swebench_unified.harness.run_resolve('django__django-13297', atk_3.diff, timeout=3600)`: resolved=TRUE, completed=TRUE, patch_successfully_applied=TRUE, F2P 1/1 (test_template_params_filtering), P2P 52/52, FAIL_TO_FAIL 0, PASS_TO_FAIL 0, ZERO failures -- INCLUDING test_template_params_warning and test_cached_views, the two P2P tests the prior counterexample killed. (note: 'resolved on attempt 2/3 (flaky)'; the gold control run in the same window also resolved=TRUE/completed=TRUE, so the environment is not the explanation for anything here.)

So the sole verifying wrong-shaped impl's faithful patch RESOLVES: no verify-but-not-correct witness. WHY atk_3 IS AN ADMITTED ALTERNATIVE FIX AND NOT A HOLE: refinement.md A9 states the exceptional exit is 'PERMITTED, never REQUIRED' and GUARDED -- takeable only on the family the real post-patch callee already fails on. atk_3 aborts exactly there, so gold and atk_3 are behaviourally indistinguishable on every input either returns for, which is why the harness scores both 1/1 + 52/52. Contrast atk_9/atk_5/atk_6, which take a degraded or misplaced exit BESIDE/OUTSIDE that family and are rejected. atk_3 also confirms obligation (3) forbids RUNNING a deferral, not ALLOCATING (the pos-extra-entry-unrun anti-over-fit control).

**REFINEMENT.MD LEG AUDIT:** 11 legs (A1-A9 incl. A4b/A5b), tag census = 1 R, 1 A-consumed, 5 A-reference, 3 A-reference + I, 1 I. NO kind-3 step; the only occurrences of 'inexpressible'/'kind-3' are the explicit denial in A2 and the section-B heading. The changed operation is the difference between two A-consumed construction callees (wrap_resolvable vs wrap_opaque), grounded per directive 8 as unforgeable capability predicates rather than an answer-key oracle -- borne out by atk_8 (the echo fails on the ledger, not on luck) and atk_11 (a bare entry cannot supply deferral_of).

A-LEG CORRESPONDENCE, checked against the real callees in a base_commit worktree (all mechanics confirmed, minor line-number drift in the citations only):
  * A3/A5/A5b (wrap_resolvable / binder_castable / binder_accepts <-> `lazy(access_value, type(value))()` + Field.get_prep_value): `class __proxy__(Promise)` confirmed, and the real binder is `if isinstance(value, Promise): value = value._proxy____cast()` at django/db/models/fields/`__init__`.py:805-809 (refinement.md cites 825-828 -- drift). So the recognition branch really is taken for every entry the build returns. atk_9 shows recognition cannot be degraded; atk_11 shows the capabilities cannot be conjured on a bare entry.
  * A6 (absence of the binder capabilities from wrap_opaque <-> SimpleLazyObject is not a Promise): `class SimpleLazyObject(LazyObject)` at functional.py:356, `class LazyObject` at :245 -- no Promise in the MRO. Confirmed dynamically by atk_1, the prepatch image, failing exactly the recognition clause.
  * A7 (type_of <-> the value's own real runtime type): type_of is INTERPRETED (`value < 0 -> 0 else value + 1`) and hence NOT injective on negative tags, which contradicts mapping.md section 2's 'distinct types map to distinct tags' on a literal reading. Probed at the collapse boundary (atk_5, value == 0) and rejected on the Exsures guard, because facets (1)/(2a) pin the entry independently of the type component. Recorded as a latent modelling imprecision, NOT a finding.
  * A4/A4b/A8 (resolves_to / deferral_of / deferrals_run <-> access_value and the RemovedInDjango40Warning it raises at base.py:172-178): mapping.md's 'no side channel reads the value without the effect' and refinement.md B's 'run_deferral is the only route from an entry to its value' are mechanically true here -- Wrapped has no field, no function maps an entry to its value, resolves_to/deferral_of/deferrals_run are bodiless @ContractOnly @Predicates. Obligation (3) bit on every route I constructed: the returned entry (atk_2), another value's throwaway (atk_7), an echo-rebuild (atk_8) and a negative ledger index (atk_13).
  * A9 (partiality <-> the real two-route `__prepare_class__` failure): all cited mechanics confirmed at base_commit -- `for type_ in resultclass.mro()` at functional.py:112, the delegate overlay `bytes in resultclasses` / `str in resultclasses` / `assert not (both)` at :120-123, `__bytes_cast` returning `bytes(func(...))` at :142-143. Guard enforced (atk_5/atk_6 rejected), FEASIBLE and hence load-bearing (atk_3's abort branch is live code that verifies), not a licence to degrade (atk_9), and permitted-not-required confirmed empirically (atk_3 verifies AND resolves 52/52). The family is confirmed neither `isinstance(value, type)` nor a synonym for 'the build aborts': the two bytes-arm witnesses build successfully and are Promise-recognised, exactly as mapping.md claims.

**BATTERY INTEGRITY:** properties.py, axiom_check.py and conformance_check.py all import cleanly from the repo root under SBU_BENCHMARK_DIR=benchmark-verified.

NON-BLOCKING DOCUMENTATION DEFECTS (not spec holes, not exploitable): (1) mapping.md section 2's 'distinct types map to distinct tags' is literally false of the interpreted type_of on negative tags (see A7); (2) refinement.md/mapping.md cite Field.get_prep_value at fields/`__init__`.py:825-828 but it is at 805-809 at base_commit, and functional.py:111 vs the actual :112. Latent imprecision; the boundary was attacked and rejected.

**SUMMARY:** 13 distinct same-spec wrong-impl attacks spanning every required family (prepatch bug, prior counterexample re-encoded, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo) plus the A-leg families the brief asked me to concentrate on (graceful-degradation fallback across the recognition/resolution split, capability-from-nowhere, inverted/unjustified abort guard, ledger-arithmetic underflow, non-termination, guarded self-call divergence, the type_of collapse boundary). 12 rejected with clause-attributable errors; the 1 that verified was materialized as a faithful refined patch, confirmed to apply at base_commit, and RUN through the official harness -- resolved=True, completed=True, F2P 1/1, P2P 52/52, zero failures, matching the gold control exactly. No verifying impl whose faithful patch fails to resolve exists on this evidence. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_3.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 3]

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -508,6 +508,5 @@
     Exsures(Exception, deferrals_run(0))
     # post-conditions-end
     # impl-start
-    w = wrap_resolvable(value)  # type: Wrapped
-    return w
+    return wrap_resolvable(value)
     # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-13297 (nagini). VERDICT: SOUND. Per brief, concentrated on the A legs and the model<->patch correspondence; R/I legs left to G-CONF.

**SAME-SPEC:** all 13 attacks + the positive control return exit 0 from `adversary same-spec nagini django__django-13297 <f>` -- only the impl region differs, so no attack cheats by weakening a contract.

POSITIVE CONTROL (non-vacuity): atk_pos.py is a structural reshape, not a copy -- `return wrap_resolvable(value)`, collapsing the gold's named-local-then-return. `adversary weakness` -> exit 0 (CANDIDATE, verifies 15.5s). So the 12 rejections are genuine, not a verifier that refuses everything.

**COMMAND FOR EVERY ATTACK:** `python -m swebench_unified.adversary weakness nagini django__django-13297 <atk_N.py>` (exit 2 = rejected/good, exit 0 = CANDIDATE); clause text from `bash scripts/nagini_verify.sh` on the same file. Verifications were run 3-at-a-time as concurrent background jobs (each Nagini check spawns JVM+Z3); scheduling only, every attack fully verified.

atk_1  PREPATCH BUG (`wrap_opaque(value)`, the non-Promise SimpleLazyObject image) -> exit 2. Error: 'insufficient permission to access binder_accepts(Result())'. prepatch_reproduced=TRUE; G-DIFF sensing is real. atk_2  PRIOR-AUDIT HOLE RE-ENCODED (eager resolution during assembly): build the gold entry, `peek = run_deferral(w, value, 0)`, `Assert(peek == value)`, hand the CORRECT entry on -> exit 2, 'deferrals_run(0)'. Facets (1)/(2) hold verbatim, so ONLY obligation (3) can reject -- and it does. THE PRIOR HOLE IS CLOSED. atk_3  ABORT ON THE ABSTRACT PARTIALITY FAMILY, having first allocated and discarded a hookless stand-in -> exit 0, CANDIDATE.

RESOLVE-CHECKED, see below. atk_4  PARTIAL-DOMAIN (resolvable on value<0, pre-patch hookless stand-in on value>=0, where the F2P str tag lands) -> exit 2, binder_accepts(Result()). atk_5  BOUNDARY ABORT at the single tag value==0 (type_of's collapse boundary) -> exit 2, 'Assertion own_type_unpreparable(value) might not hold'. Arithmetic on the tag cannot decide the abstract family. atk_6  INVERTED GUARD: abort OFF the family, return on it -> exit 2, same Exsures guard. Confirms the guard is directional, not a free abort licence. atk_7  CONTROL-FLOW EFFECT charged to ANOTHER value's throwaway: the returned entry is the gold one and never touched; a side stand-in for `value + 7` has ITS deferral run -> exit 2, deferrals_run(0).

The ledger is indexed by neither entry nor value nor construction. atk_8  UNGROUNDED-ORACLE ECHO: recover the value via a cheap opaque probe (`seen = run_deferral(probe, value, 0)`), rebuild the RETURNED entry from the echoed int (`wrap_resolvable(seen)`) so every value-level clause is discharged by the echo -> exit 2, deferrals_run(0). No answer-key without charging the ledger. atk_9  A-LEG GRACEFUL-DEGRADATION FALLBACK (the realistic wrong fix): on exactly the guarded family, hand back the PRE-PATCH hookless stand-in instead of aborting -> exit 2, binder_accepts(Result()).

KEY A-LEG PROBE for the recognition/resolution split: guarding binder_castable is NOT a licence to return a binder-REFUSED stand-in, because binder_accepts is unconditional. mapping.md's 'keeps the contract non-silent on the unpreparable family' bites. atk_10 DIVERGENCE via a FEASIBLE guarded self-call on the family -> exit 2, 'Obligation leak check failed. Callee wrap_kwarg_value might not take all unsatisfied obligations from the caller'. MustTerminate(14) is at the METHOD level, so an unbounded self-call is refused rather than verified vacuously. atk_11 CAPABILITY FROM NOWHERE: build the real entry, `Assert(binder_accepts(real))`, then return a bare `Wrapped()` and try to discharge the clauses on IT -> exit 2, 'insufficient permission to access deferral_of(Result(), value)'.

Not a Fold attempt (an invalid program): the postcondition is simply unprovable, which is what unforgeability must mean. atk_12 CONTROL-FLOW DIVERGENCE: build the correct entry, then spin in `while i >= 0` -- every value-level, capability and ledger clause holds verbatim, so ONLY termination can reject -> exit 2, 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context'. Had it verified, the refined patch would hang the mapping assembly and the F2P test would never return. atk_13 LEDGER-ARITHMETIC UNDERFLOW: run the deferral charged to index -1, so `deferrals_run(-1 + 1)` is literally the postcondition `deferrals_run(0)` -> exit 2, 'The precondition of method run_deferral might not hold. There might be insufficient permission to access deferrals_run(n)'. The ledger is not forgeable by arithmetic: deferrals_run(-1) has no producer.

**TALLY:** 12 rejected with clause-attributable errors; 1 CANDIDATE, resolve-checked. Rejections distribute across obligations -- binder_accepts (atk_1,4,9), deferrals_run (atk_2,7,8), deferral_of (atk_11), the A9 Exsures guard (atk_5,6), run_deferral's ledger precondition (atk_13), method-level MustTerminate (atk_10,12). No single clause carries the spec.

CANDIDATE RESOLVE (the mandatory G-EQ step): atk_3's faithful refined patch is atk_3.diff -- gold's `lazy(access_value, type(value))()` plus a faithful classifier that aborts on exactly the `own_type_unpreparable` family (the build's own exception, plus the route-(ii) bytes-arm detected as `type(entry)._delegate_bytes and not isinstance(value, bytes)`), allocating and discarding a SimpleLazyObject stand-in on the way out to mirror the attack's discarded spare. Confirmed to apply at base_commit 8954f255bbf5f4ee997fd6de62cb50fc9b5dd697 via `git apply --check` in a detached worktree of the upstream repository -> 'Checking patch django/views/generic/base.py... APPLY-CHECK OK'.

Verified out-of-band that the classifier partitions the family EXACTLY as axiom_check.py measures and WITHOUT running any deferral: all 18 abort-route witnesses (13 type-valued + `_MroData`/`_MroOneArg`/`_MroProp`/`_EqBoom`/`_EqAll`) -> family/abort, both bytes-arm witnesses (`_EqBytesOnly`, `_IntBytesArm`) -> family/bytes-arm, and all 17 not_type_valued witnesses -> off-family. Also measured on the patched tree: building 5 entries raises 0 notices, the entries ARE Promises, the real Field.get_prep_value resolves them to the value at its own real type with exactly 1 notice each, construction survives an escalating configuration while resolution raises RemovedInDjango40Warning, and the aborting exits raise 0 notices.

RUN via `swebench_unified.harness.run_resolve('django__django-13297', atk_3.diff, timeout=3600)`: resolved=TRUE, completed=TRUE, patch_successfully_applied=TRUE, F2P 1/1 (test_template_params_filtering), P2P 52/52, FAIL_TO_FAIL 0, PASS_TO_FAIL 0, ZERO failures -- INCLUDING test_template_params_warning and test_cached_views, the two P2P tests the prior counterexample killed. (note: 'resolved on attempt 2/3 (flaky)'; the gold control run in the same window also resolved=TRUE/completed=TRUE, so the environment is not the explanation for anything here.)

So the sole verifying wrong-shaped impl's faithful patch RESOLVES: no verify-but-not-correct witness. WHY atk_3 IS AN ADMITTED ALTERNATIVE FIX AND NOT A HOLE: refinement.md A9 states the exceptional exit is 'PERMITTED, never REQUIRED' and GUARDED -- takeable only on the family the real post-patch callee already fails on. atk_3 aborts exactly there, so gold and atk_3 are behaviourally indistinguishable on every input either returns for, which is why the harness scores both 1/1 + 52/52. Contrast atk_9/atk_5/atk_6, which take a degraded or misplaced exit BESIDE/OUTSIDE that family and are rejected. atk_3 also confirms obligation (3) forbids RUNNING a deferral, not ALLOCATING (the pos-extra-entry-unrun anti-over-fit control).

**REFINEMENT.MD LEG AUDIT:** 11 legs (A1-A9 incl. A4b/A5b), tag census = 1 R, 1 A-consumed, 5 A-reference, 3 A-reference + I, 1 I. NO kind-3 step; the only occurrences of 'inexpressible'/'kind-3' are the explicit denial in A2 and the section-B heading. The changed operation is the difference between two A-consumed construction callees (wrap_resolvable vs wrap_opaque), grounded per directive 8 as unforgeable capability predicates rather than an answer-key oracle -- borne out by atk_8 (the echo fails on the ledger, not on luck) and atk_11 (a bare entry cannot supply deferral_of).

A-LEG CORRESPONDENCE, checked against the real callees in a base_commit worktree (all mechanics confirmed, minor line-number drift in the citations only):
  * A3/A5/A5b (wrap_resolvable / binder_castable / binder_accepts <-> `lazy(access_value, type(value))()` + Field.get_prep_value): `class __proxy__(Promise)` confirmed, and the real binder is `if isinstance(value, Promise): value = value._proxy____cast()` at django/db/models/fields/`__init__`.py:805-809 (refinement.md cites 825-828 -- drift). So the recognition branch really is taken for every entry the build returns. atk_9 shows recognition cannot be degraded; atk_11 shows the capabilities cannot be conjured on a bare entry.
  * A6 (absence of the binder capabilities from wrap_opaque <-> SimpleLazyObject is not a Promise): `class SimpleLazyObject(LazyObject)` at functional.py:356, `class LazyObject` at :245 -- no Promise in the MRO. Confirmed dynamically by atk_1, the prepatch image, failing exactly the recognition clause.
  * A7 (type_of <-> the value's own real runtime type): type_of is INTERPRETED (`value < 0 -> 0 else value + 1`) and hence NOT injective on negative tags, which contradicts mapping.md section 2's 'distinct types map to distinct tags' on a literal reading. Probed at the collapse boundary (atk_5, value == 0) and rejected on the Exsures guard, because facets (1)/(2a) pin the entry independently of the type component. Recorded as a latent modelling imprecision, NOT a finding.
  * A4/A4b/A8 (resolves_to / deferral_of / deferrals_run <-> access_value and the RemovedInDjango40Warning it raises at base.py:172-178): mapping.md's 'no side channel reads the value without the effect' and refinement.md B's 'run_deferral is the only route from an entry to its value' are mechanically true here -- Wrapped has no field, no function maps an entry to its value, resolves_to/deferral_of/deferrals_run are bodiless @ContractOnly @Predicates. Obligation (3) bit on every route I constructed: the returned entry (atk_2), another value's throwaway (atk_7), an echo-rebuild (atk_8) and a negative ledger index (atk_13).
  * A9 (partiality <-> the real two-route `__prepare_class__` failure): all cited mechanics confirmed at base_commit -- `for type_ in resultclass.mro()` at functional.py:112, the delegate overlay `bytes in resultclasses` / `str in resultclasses` / `assert not (both)` at :120-123, `__bytes_cast` returning `bytes(func(...))` at :142-143. Guard enforced (atk_5/atk_6 rejected), FEASIBLE and hence load-bearing (atk_3's abort branch is live code that verifies), not a licence to degrade (atk_9), and permitted-not-required confirmed empirically (atk_3 verifies AND resolves 52/52). The family is confirmed neither `isinstance(value, type)` nor a synonym for 'the build aborts': the two bytes-arm witnesses build successfully and are Promise-recognised, exactly as mapping.md claims.

**BATTERY INTEGRITY:** properties.py, axiom_check.py and conformance_check.py all import cleanly from the repo root under SBU_BENCHMARK_DIR=benchmark-verified.

NON-BLOCKING DOCUMENTATION DEFECTS (not spec holes, not exploitable): (1) mapping.md section 2's 'distinct types map to distinct tags' is literally false of the interpreted type_of on negative tags (see A7); (2) refinement.md/mapping.md cite Field.get_prep_value at fields/`__init__`.py:825-828 but it is at 805-809 at base_commit, and functional.py:111 vs the actual :112. Latent imprecision; the boundary was attacked and rejected.

**SUMMARY:** 13 distinct same-spec wrong-impl attacks spanning every required family (prepatch bug, prior counterexample re-encoded, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo) plus the A-leg families the brief asked me to concentrate on (graceful-degradation fallback across the recognition/resolution split, capability-from-nowhere, inverted/unjustified abort guard, ledger-arithmetic underflow, non-termination, guarded self-call divergence, the type_of collapse boundary). 12 rejected with clause-attributable errors; the 1 that verified was materialized as a faithful refined patch, confirmed to apply at base_commit, and RUN through the official harness -- resolved=True, completed=True, F2P 1/1, P2P 52/52, zero failures, matching the gold control exactly. No verifying impl whose faithful patch fails to resolve exists on this evidence. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**REFERENCE SETUP.** Fresh worktree at base_commit 8954f255bbf5f4ee997fd6de62cb50fc9b5dd697 from the upstream repository, then `git apply` of the gold patch (byte-identical to meta.json patch_diff / g2f_13297_gold.diff). Per instructions the PATCHED tree is the reference for the modelled function (wrap_kwarg_value <-> the per-entry wrapping `context_kwargs[key] = lazy(access_value, type(value))()` in django/views/generic/base.py:180); base_commit is the reference only for untouched callees.

**CONTROLS.** Unmodified model.py verifies (`Verification successful`, 12.16s, pinned nagini_verify.sh) and `adversary same-spec` reports SAME, so the spec region I audited is byte-identical to the bundle's. Bundle's own batteries re-run against MY worktree, not the cell's cached artifacts: axiom_check.py exit 0 (G-AX OK; 8 values across CharField/IntegerField/FloatField incl. F2P str 'Rene Magritte'; partiality boundary on both preparation routes); conformance_check.py exit 0 (100051 inputs = 51 boundary + 100000 fuzz seed 132970, 0 disagreements, 0 build-time deferral runs on both sides, 18 partiality inputs agreeing on the abort).

**WHAT A TOO-STRONG SPEC WOULD LOOK LIKE HERE.** `own_type_unpreparable` is an abstract uninterpreted @ContractOnly @Pure marker, so every clause guarded by it (1b resolves_to, 2b binder_castable) and the Exsures can only ever be too WEAK, never too strong -- an over-large family loses guarantees, it never predicts an outcome the repo does not produce. The spec can therefore only over-claim through its FOUR UNGUARDED obligations, which is where I concentrated: (i) Ensures(deferrals_run(0)) on the normal exit, (ii) Ensures(deferral_of(Result(), value)) [provenance, whole domain], (iii) Ensures(binder_accepts(Result())) [Promise-recognition, whole domain], (iv) Exsures(Exception, deferrals_run(0)) [ledger preserved on the aborting exit].

SWEEP (atk2fa_sweep.py). Oracle = the REAL patched `_wrap_url_kwargs_with_deprecation_warning` called one value per invocation so an abort cannot mask siblings. 66-case hand-built corpus + 30000 fuzz values: str (empty/space/latin-1/astral/NUL/5000-char), int (0, +-1, +-`2**63`, `2**200`), float (+-0.0, +-inf, 1e308, 5e-324), bool, None, bytes/bytearray, tuple/list/dict/set/frozenset, complex, Decimal, date, datetime, uuid, Fraction, str/bytes/int subclasses, `__slots__` and no-`__dict__` instances, object(), lambda, range, iterator, Ellipsis, NotImplemented; type-valued (int, str, type, Field, abc.ABCMeta); and the hostile non-type members of both preparation routes -- mro shadowed as a data attribute / one-arg method / property, custom-mro metaclass, `__dict__`-raising metaclass, `__setattr__`-raising metaclass, and metaclass `__eq__` variants returning bytes-only / True-for-all / raising / str-only. Result: 0 violations of any unguarded clause.

### Clause-by-clause confirmation
(iii) binder_accepts unconditional is the spec's boldest unguarded claim and it holds structurally: django.utils.functional.lazy's `__proxy__` subclasses Promise (functional.py:85), so whenever the build RETURNS it returns a Promise -- there is no value at which it returns a non-Promise stand-in. I attacked this directly (atk2fa_probe4.py) with 20 result classes whose `__dict__` shadows proxy internals (`__class__`, `__cast`, `_delegate_bytes`, `_delegate_text`, `__prepared`, `__promise__`, `__prepare_class__`, `__args`, `__kw`, `__reduce__`, `__text_cast`, `__bytes_cast`, `__str__`, `__eq__`, `__lt__`, `__hash__`, `__mod__`, ...): every surviving build was still isinstance(w, Promise). 0 subversions. Critically the guarded/unguarded split is exactly right on the awkward bytes-arm member: EqBytesOnly builds OK, IS Promise-recognised, and then `_proxy____cast`() raises TypeError -- so binder_accepts unconditional is satisfied there while binder_castable must be (and is) guarded. A spec that had guarded 2a instead would be too weak, not too strong.

(ii) deferral_of unconditional: wrapped 4 keys in ONE real call and resolved each entry -- each closed over its own key's value with exactly 1 notice. The post-patch closure still binds `value=value` from the loop, so provenance holds on the whole domain including inside the unpreparable family; nothing was substituted. (i)/(iv) deferrals_run(0) on BOTH exits: instrumented warnings.warn with a traceback spy that counts only frames actually inside `access_value` -- i.e. real deferral RUNS, not merely RemovedInDjango40Warning-category emissions. Across the whole corpus + fuzz the delta at build time is 0 on the returning exit AND 0 on every aborting exit.

This also killed my only apparent hit: a value whose metaclass `__eq__` itself emits RemovedInDjango40Warning showed 2 category-matching warnings at build, but the spy proved access_value ran 0 times -- the notices came from the value's own metaclass during `bytes in resultclasses`, not from a deferral. Probe artifact, not a divergence.

Abort provenance: every real abort I could produce (int, type, abc.ABCMeta, Field, EqBoom->RuntimeError, EqAll->AssertionError, MroData->TypeError, DictBoom->ValueError) originates inside `__proxy__`.`__prepare_class__` (functional.py:109-127), which is precisely the family mapping.md defines, so the guarded Exsures never licenses an abort the repo does not take -- and Exsures is permitted-not-required, so the total pre-patch construction remains admissible. Off-family resolution / type_of: for every ordinary value the binder returned the IDENTICAL object (`is`, stronger than ==) with type(resolved) is type(value), and each cast performed exactly 1 run (non-memoised, matching run_deferral counting runs not accesses). So binder_castable(Result(), value, type_of(value)) with type_of = the value's OWN runtime type is exactly what the repo delivers -- not the proxy's surface type (`__proxy__`) and not the declared result class.

**ONE NIT EXAMINED AND DISMISSED.** type_of is the concrete `value < 0 -> 0 else value + 1`, hence injective on non-negatives, which literally contradicts its own docstring's 'distinct values may share a type-tag'. It is NOT a faithfulness break: the contract only ever instantiates type_of at the single value under construction and never relates the tags of two different values, so injectivity is unobservable to any proof and shifts the obligation on no input. Separately, MustTerminate(6) on wrap_resolvable would not model a value whose metaclass `__eq__` diverges, but that is the Nagini termination-measure convention rather than a value-level behavioural divergence, and it is not an input on which the modelled function disagrees with the real callee.

**CONCLUSION.** I found no input on which the modelled wrap_kwarg_value disagrees with the real patched per-entry wrapping. The unguarded clauses are each independently justified by the repo (Promise-by-construction, closure provenance, no access_value call during build on either exit); the guarded clauses are guarded exactly where the repo withdraws its guarantee, including the subtle silent bytes-arm case. The spec is not too strong and does not drift from repo behaviour. FAITHFUL. (No diverging input is cited because none exists; per the gate's rule a diverging input is required only to claim a defect.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**SCOPE.** Leakage judged against the solver-visible problem_statement ONLY (hints_text excluded, 452 chars, never consulted for screening). No relaxation is in play and none is needed: `ls` of the bundle shows NO RELAXED_LEAKAGE.md, and a recursive key scan of meta.json for /relax/i returns nothing; meta.json gates.G-LEAK is {status: pass, mode: strict}. So this is judged at the STRICT bar, which is the bar the bundle asserts.

WHICH BYTES I JUDGED (this matters -- the spec was revised since the last panel run). Current model.py sha256 = b32f7e1cb4830991920e9f76c6faa38ffee309b8e9f4c0610be8257c2acec919. I regenerated the consumer view myself with markers.spec_view(model.py, nagini_backend) -> 512 lines, sha256 bc35c08472765abc63bcc71bec7aaab50ca89ae08483a7d4c200cb6616c1dfe8, which matches meta gates.G-HYGIENE.data.region_hashes.spec_view exactly. The PRIOR G-PANEL-3 LEAKAGE finding recorded in meta/verdict.md was against model.py 3794e31d22bc..., a DIFFERENT and now-superseded artifact, so I did not inherit its disposition; I re-derived everything on the current bytes.

THE PRIOR FINDING'S CITED LEAK IS GONE -- measured, not assumed. That note's whole reconstruction rested on the spec view paraphrasing the unique internals of django.utils.functional.lazy.`__proxy__`.`__prepare_class__` (mro ancestor-chain enumeration, bytes/str delegate arms, advertised result types). I grepped the current spec view for every one of those tokens, case-insensitive: mro 0, ancestor 0, advertis 0, 'result type' 0, resultclass 0, metaclass 0, overlay 0, 'zero-argument' 0, delegat 0, enumerat 0, 'type-of-types' 0, contradictory 0, 'post-process' 0, `__proxy__` 0, prepare_class 0. Also: lazy 0, SimpleLazyObject 0, Promise 0 (capital-P), functional 0. The mechanism narration the earlier reviewer measured has been de-narrated out. The only residual 'prepar' hits (23) are all the identifier own_type_unpreparable itself, and the 2 'member' hits are the English word 'membership'.

REPO-SYMBOL / PATH / QUOTED-LINE SCREEN (all re-run by me, not read off the gate). Zero occurrences in the spec view of: access_value, `_wrap_url_kwargs_with_deprecation_warning`, context_kwargs, url_kwargs, TemplateView, get_context_data, RemovedInDjango40Warning, views/generic, base.py, django/utils, and every gold file:line coordinate (168/172/181/109/127 all 0). I ran leakage.`_patch_changed_lines` over the real gold patch and whitespace-normalized both sides: NO changed gold line of length >=8 appears in the spec view. Diff markers: none of `_PY_DIFF_MARKERS` present. Patched path django/views/generic/base.py: not present. leakage.`_NARRATION_RE` over the spec view returns [] -- no bug/fix/patch/regression vocabulary. Full leakage.screen(...) -> passed=True, hard_failures=[], warnings=[]. I treated that pass as necessary-not-sufficient and did the L3 mechanism judgement by hand above, since G-LEAK's `_patch_changed_symbols` only harvests def|class names ({access_value, wrap_url_kwargs_with_deprecation_warning}) and structurally cannot see `lazy`, which enters the gold diff as an import and a call.

WHAT THE SPEC VIEW *DOES* NAME, AND WHY IT IS PS-COVERED. It says an entry must be RECOGNISED by a type-directed parameter binder rather than refused as an "unsupported type" (2a), and off an abstract family must resolve to the value at its own real runtime type (2b). Both are readable straight off the public problem_statement: the PS supplies the crash 'Error binding parameter 0 - probably unsupported type' (the literal phrase 'unsupported type' is IN the PS), names SimpleLazyObject as the object that fails to resolve, and shows the user-side workaround str(offer_slug) -- i.e. the PS itself states that the object must resolve to a value of the right type at the DB-binding boundary. 'Resolve to the value at its own real type' is the abstract restatement of exactly that symptom, not a disclosure of the repair.

UNAVOIDABILITY / LOAD-BEARING TEST (the usual strip-and-reverify, run against the PRE-patch impl). I measured which clause is the actual discriminator rather than guessing. Baseline: gold model verifies (`nagini_verify.sh gold.py` -> Verification successful, 11.78s); prepatch fails at pre.py:483 'Postcondition of wrap_kwarg_value might not hold. There might be insufficient permission to access binder_accepts(Result())' (22.10s). I then deleted the guarded binder_castable/type_of clause (2b) from the prepatch model and re-ran: STILL fails, and still on binder_accepts (pre_no2b.py:481, 12.19s). So the load-bearing discriminator is binder_accepts (2a) -- 'the binder recognises the entry instead of refusing it as an unsupported type' -- which is the PS's own crash text. The type-flavoured clause is NOT what senses the change, so it is not carrying gold internals as its justification.

**IDENTIFIER-AVOIDABILITY CHECK.** Someone could argue own_type_unpreparable hints at type(value). I tested it: renamed it to the neutral domain_marker_p throughout, confirmed logic identity by ast.parse + docstring-strip + ast.unparse (LOGIC IDENTICAL, all Requires/Ensures/Exsures clause sets byte-equal modulo the rename), and the renamed spec still verifies (16.79s). So the name is cosmetic, and in the spec view the family is explicitly declared abstract and UNINTERPRETED -- the view states outright that it asserts nothing about which values are in it, that no arithmetic on the value-tag can decide it, that a proof can only use it as an opaque case split, and that membership is settled out of band. It also explicitly says membership does NOT coincide with 'the build aborts'. A solver reading only the spec view learns that some unspecified value family is exempt; it cannot recover mro-unavailability or bytes/str delegation, which is where the real partition lives (mapping.md line 17 -- a file the consumer never receives; only spec_view + problem_statement + modeled_functions reach the consumer per eval/prompts.py).

RESIDUAL SOLUTION SPACE (the real test of whether the gold edit is pinned). The view demands: recognised by the binder, resolves to the value at its real type, provenance-faithful, and ledger-preserving (no deferred computation run at build time). Multiple non-gold repairs satisfy that reading -- make the existing lazy stand-in expose the binder's resolution hook, register it with the binder, hand back a differently-constructed deferred proxy, or supply any other recognised deferred wrapper. Nothing in the view says WHICH callee to swap in or that the repair is an import change plus a two-argument call, and 'lazy' appears zero times. The view constrains the observable contract; it does not select the edit.

**CORE GATES THE DISPOSITION LEANS ON:** G-VERIFY pass, G-GOLD pass (gold verifies, prepatch fails), G-DIFF pass (prepatch 'verification failed'), G-LEAK pass/strict, G-RESOLVE pass/resolved, G-AX pass, G-CONF pass (100051 checked, 0 disagreements). I independently reproduced the two that carry this verdict -- gold verifies, prepatch fails on binder_accepts.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as a finding in its own right, per instructions): CLEAN in the spec-bearing artifacts. I grepped model.py, mapping.md and refinement.md for attacker/panel/reviewer/'honest verdict'/'should record'/'do not flag'/NO-LEAKAGE/submit_result/leaking_line: only ordinary self-description ('lets the contract stay honest' at model.py:295, describing the contract's treatment of the partial family). Nothing instructs me how to record or which verdict to reach. Noting for the record, without treating it as steering of me: verdict.md contains the superseded prior G-PANEL-3 LEAKAGE write-up (line 961 onward, incl. its own bundle-addresses-reviewer paragraph at 1011). That is an audit ledger of a past run against older bytes, not an instruction to this run; I judged the current spec view independently and my conclusion differs from it because the narration it cited has since been removed.

**CONCLUSION:** NO-LEAKAGE. On the current bytes the spec view quotes no gold line, names no patched file/function/symbol, echoes no gold-only vocabulary, and narrates no bug->fix mechanism. The one discriminator it does state (binder recognition / 'unsupported type') is verbatim public in the problem_statement, and I measured it to be the load-bearing clause, so removing it would break G-DIFF rather than merely de-narrate.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
