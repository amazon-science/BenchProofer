# P2 adversarial audit — django__django-15375

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_19.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 9 | `atk_2.py`, `atk_3.py`, `atk_8.py`, `atk_9.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no counterexample survived. 19 same-spec attacks were run through `adversary weakness`; 9 came back CANDIDATE (share the frozen spec AND verify), and every one of those 9 had its faithful refined patch materialized, checked with `git apply --check` at base_commit, and EXECUTED under the official harness (run_resolve). ALL NINE RESOLVED (resolved=True, completed=True, F2P 1/1, P2P 95/95). So no verifying same-spec wrong impl was exhibited whose refined patch fails to resolve: verify⇏correct is NOT falsified on this cell.

On audit the 9 verifying impls are not wrong impls — each is observationally equivalent to the gold patch, which is why each resolves. Grouped by the freedom each exploits:

(1) IDENTITY OF THE EXPOSED AGGREGATION (atk_2, atk_8, atk_14, atk_15). The spec describes the returned/exposed aggregation by its FIELDS (final-flag, supplies-nothing, holds-nothing, parts_usable on the three-part condition) and never pins it to be the SAME OBJECT resolution built. So an impl may substitute a second aggregation, provided that one's parts really are in resolved form. atk_2/atk_14 do this on the no-fallback path, atk_8/atk_15 on the wrapper's exposed aggregation. Refined faithfully — atk_2/atk_8 as a second FULL resolution (`super().resolve_expression` PLUS the `:53` condition step), atk_14/atk_15 as `c.copy()` — all four resolve. This is exactly the calibration refinement.md B5 documents (`pos-control-second-full-resolution`): the parts_usable clause deliberately forbids wrapping an aggregation whose parts were NEVER resolved, not wrapping a different fully-resolved one. B5 predicts this resolves; execution confirms it. The distinction is load-bearing and correctly drawn: atk_11 (`c.parts_usable = True` unconditionally) and atk_4/atk_12 (dropping or weakening a leg) all FAIL verification.

(2) MODELLED STATE ON `holds_own_fallback` (atk_16, atk_17). Steps A4/A10 model the resolved aggregation as holding the fallback value and then being cleared. Nothing in the postcondition observes that intermediate state on any returned object, so an impl may reverse A4 (atk_16: read the value off `c` and clear it immediately, so `c` holds none from that point on, including on the refusal) or drop A4 and A10 together (atk_17: no reset at all). Both refine faithfully and both resolve — and I verified WHY: `Coalesce` is a `Func` with no `default` attribute, and the only readers of `.default` in the whole ORM are `aggregates.py:63` / `:67` themselves plus the unrelated `Case.default` (`expressions.py:1080-1137`). Nothing downstream reads the wrapped aggregate's `.default`, so the reset is observationally dead. refinement.md A4 itself concedes it is 'modelled STATE, not a step of the work'.

(3) STAMP TIMING / RIGHT-HAND SIDE (atk_18). The wrapper is born ALREADY MARKED and step A9 is dropped; the `Assert(not wrapper.is_final_aggregation)` is deleted along with it. Refined as a `Coalesce` subclass carrying `is_summary = c.is_summary` at construction. Resolves — same final field value.

(4) UNOBSERVABLE WRITE ON THE REJECT PATH (atk_9). The `Exsures` frames the yield's `usable` but NOT its `resolution_of`, so the nested-aggregate reject path may scribble a false provenance edge before refusing. Refined as running the delegated step on the written default on the reject path too. Resolves — the `FieldError` escapes and the object is discarded, so the write is unobservable. A genuine but harmless frame gap.

ONE DOCUMENTATION DEFECT (not a spec weakness). atk_18 refutes refinement.md A8b's incidental claim that `Assert(not wrapper.is_final_aggregation)` 'makes a model variant whose wrapper is born already marked FAIL verification'. It does not: the Assert lives INSIDE the impl region, so an attacker deletes it together with the construction change and the spec stays byte-identical (`adversary same-spec` => SAME). The Assert constrains the bundle's own impl and the G-MUT mutant, not the space of admissible impls. This is an over-claim about a proof annotation's discriminating power — cosmetic, affects no leg's kind, and admits no incorrect impl (atk_18 is behaviourally correct and resolves). This is the same finding the retained prior G-EQ pass recorded via its atk_11, independently reproduced here.
```

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -584,9 +584,8 @@
     # expression built over it, and the value it supplies: so all of its parts are
     # usable exactly when that value is.
     wrapper.parts_usable = supplied.usable
-    # The returned fallback-supplying expression must carry the same final-flag
-    # as the aggregation it supplies the fallback for.
-    wrapper.is_final_aggregation = c.is_final_aggregation
+    # PRE-PATCH: the fallback-supplying expression is returned still unmarked —
+    # the final-flag of the aggregation is NOT propagated onto it.
     # The aggregation itself no longer holds the fallback value — the returned
     # expression is what supplies it — and it stays reachable from that
     # expression, which is what supplies the fallback FOR it.
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -552,7 +552,13 @@
         # non-final resolution was requested: rejected, no expression produced.
         raise ResolutionRefused()
     if fallback is None:
-        return c
+        # ATTACK (identity of the returned bare aggregation): return a SECOND,
+        # separately built aggregation carrying the requested final-flag and with
+        # its parts in resolved form -- NOT the aggregation resolved above.
+        c2 = Expression(requested_final, False)
+        c2.parts_usable = (operand_resolution_usable and condition_resolution_usable
+                           and not vacuous_condition)
+        return c2
     supplied = fallback
     if fallback_is_expression:
         # The requested fallback value is itself an expression, so it is put
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -518,6 +518,10 @@
                         resolution_yield.usable == Old(resolution_yield.usable)))
     # post-conditions-end
     # impl-start
+    # ATTACK (control-flow-effect): the nested-aggregate refusal is decided
+    # BEFORE the unresolvable-part refusal, reversing the order of the two.
+    if aggregating_operand and not requested_final:
+        raise ResolutionRefused()
     if not parts_resolve:
         # A part this resolution has to resolve cannot be resolved against the
         # query at all, so no expression is produced for the aggregation.
@@ -547,10 +551,6 @@
     # leaving the fallback in place while wrapping, which is the behaviour the
     # clearing exists to prevent.
     c.holds_own_fallback = fallback is not None
-    if aggregating_operand and not requested_final:
-        # The resolved aggregation aggregates over another aggregation and a
-        # non-final resolution was requested: rejected, no expression produced.
-        raise ResolutionRefused()
     if fallback is None:
         return c
     supplied = fallback
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -536,8 +536,9 @@
     # aggregation is usable as it stands exactly when all three came out that way.
     # This is the step whose omission leaves a correctly flagged aggregation that
     # was never actually resolved.
-    c.parts_usable = (operand_resolution_usable and condition_resolution_usable
-                      and not vacuous_condition)
+    # ATTACK (echo): the condition-left-as-written leg is dropped, so an
+    # aggregation still carrying an unresolved written condition is claimed usable.
+    c.parts_usable = (operand_resolution_usable and condition_resolution_usable)
     # MODELLED STATE, not a step of the work: a resolved aggregation for which a
     # fallback value was requested DOES still hold that value at this point —
     # resolution reads the value off the resolved aggregation and only clears it
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -561,17 +561,10 @@
         # outcome is READ here: the value that came back is what the returned
         # expression goes on to supply, whether or not it is usable as it stands.
         # The value as written is left untouched either way.
-        if resolution_yields_distinct:
-            # A DISTINCT value came back. It is recorded as the resolved form OF
-            # the requested one, and its usability is whatever resolving yielded
-            # — not something this step may assert.
-            resolution_yield.resolution_of = fallback
-            supplied = resolution_yield
-        else:
-            # Resolution handed back the very value it was given: a value already
-            # in resolved form is its own resolved form, so that value is what is
-            # supplied, exactly as it arrived.
-            supplied = fallback
+        # ATTACK (self-resolution cycle): record the provenance edge on the yield
+        # unconditionally, without asking whether a DISTINCT value came back.
+        resolution_yield.resolution_of = fallback
+        supplied = resolution_yield
     # A fallback is supplied: return a distinct expression that supplies it. It
     # is built unmarked.
     wrapper = Expression(False, True)
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -583,7 +583,9 @@
     # Its parts are the resolved aggregation, which always stands as a part of the
     # expression built over it, and the value it supplies: so all of its parts are
     # usable exactly when that value is.
-    wrapper.parts_usable = supplied.usable
+    # ATTACK (boundary, over-claim): the wrapper is claimed usable as it stands
+    # as soon as EITHER the supplied value or the aggregation is.
+    wrapper.parts_usable = supplied.usable or c.parts_usable
     # The returned fallback-supplying expression must carry the same final-flag
     # as the aggregation it supplies the fallback for.
     wrapper.is_final_aggregation = c.is_final_aggregation
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -551,6 +551,11 @@
         # The resolved aggregation aggregates over another aggregation and a
         # non-final resolution was requested: rejected, no expression produced.
         raise ResolutionRefused()
+    # ATTACK (partial domain): refuse when the requested value is not itself an
+    # expression and cannot be used as it stands -- the B3 precondition that was
+    # deliberately removed, smuggled back in as a refusal instead.
+    if fallback is not None and not fallback_is_expression and not fallback.usable:
+        raise ResolutionRefused()
     if fallback is None:
         return c
     supplied = fallback
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -591,7 +591,13 @@
     # expression is what supplies it — and it stays reachable from that
     # expression, which is what supplies the fallback FOR it.
     c.holds_own_fallback = False
-    wrapper.wrapped = c
+    # ATTACK (B5 identity): the aggregation the wrapper exposes is a SECOND,
+    # separately built aggregation carrying the requested final-flag with its
+    # parts in resolved form -- not the aggregation resolved above.
+    c2 = Expression(requested_final, False)
+    c2.parts_usable = (operand_resolution_usable and condition_resolution_usable
+                       and not vacuous_condition)
+    wrapper.wrapped = c2
     # The value the returned expression supplies is the one resolution arrived
     # at for the requested fallback.
     wrapper.fallback = supplied
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -548,8 +548,13 @@
     # clearing exists to prevent.
     c.holds_own_fallback = fallback is not None
     if aggregating_operand and not requested_final:
-        # The resolved aggregation aggregates over another aggregation and a
-        # non-final resolution was requested: rejected, no expression produced.
+        # ATTACK (frame gap on the reject path): the Exsures frames the yield's
+        # `usable` but NOT its `resolution_of`, so scribble a FALSE provenance
+        # edge onto the yield -- claiming it is the resolved form of ITSELF --
+        # before refusing.
+        if (fallback is not None and fallback_is_expression
+                and resolution_yields_distinct):
+            resolution_yield.resolution_of = resolution_yield
         raise ResolutionRefused()
     if fallback is None:
         return c
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -566,6 +566,9 @@
             # the requested one, and its usability is whatever resolving yielded
             # — not something this step may assert.
             resolution_yield.resolution_of = fallback
+            # ATTACK: repair the yield's usability in place so the wrapper can be
+            # claimed usable as it stands whatever the delegated step came back with.
+            resolution_yield.usable = True
             supplied = resolution_yield
         else:
             # Resolution handed back the very value it was given: a value already
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -536,8 +536,9 @@
     # aggregation is usable as it stands exactly when all three came out that way.
     # This is the step whose omission leaves a correctly flagged aggregation that
     # was never actually resolved.
-    c.parts_usable = (operand_resolution_usable and condition_resolution_usable
-                      and not vacuous_condition)
+    # ATTACK (ungrounded-oracle echo): the resolved aggregation is claimed usable
+    # as it stands outright, reading none of the three handed-off outcomes.
+    c.parts_usable = True
     # MODELLED STATE, not a step of the work: a resolved aggregation for which a
     # fallback value was requested DOES still hold that value at this point —
     # resolution reads the value off the resolved aggregation and only clears it
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -536,7 +536,9 @@
     # aggregation is usable as it stands exactly when all three came out that way.
     # This is the step whose omission leaves a correctly flagged aggregation that
     # was never actually resolved.
-    c.parts_usable = (operand_resolution_usable and condition_resolution_usable
+    # ATTACK (boundary): EITHER handed-off step coming back usable is treated as
+    # enough, instead of both.
+    c.parts_usable = ((operand_resolution_usable or condition_resolution_usable)
                       and not vacuous_condition)
     # MODELLED STATE, not a step of the work: a resolved aggregation for which a
     # fallback value was requested DOES still hold that value at this point —
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -572,6 +572,11 @@
             # in resolved form is its own resolved form, so that value is what is
             # supplied, exactly as it arrived.
             supplied = fallback
+    # ATTACK (partial domain): where the value arrived at cannot be used as it
+    # stands, skip building the fallback-supplying expression and hand back the
+    # bare aggregation instead.
+    if not supplied.usable:
+        return c
     # A fallback is supplied: return a distinct expression that supplies it. It
     # is built unmarked.
     wrapper = Expression(False, True)
```

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -552,7 +552,12 @@
         # non-final resolution was requested: rejected, no expression produced.
         raise ResolutionRefused()
     if fallback is None:
-        return c
+        # ATTACK (identity): hand back a SECOND aggregation, built separately,
+        # whose parts are as usable as the resolved one's -- not the aggregation
+        # resolved above.
+        c2 = Expression(requested_final, False)
+        c2.parts_usable = c.parts_usable
+        return c2
     supplied = fallback
     if fallback_is_expression:
         # The requested fallback value is itself an expression, so it is put
```

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -591,7 +591,11 @@
     # expression is what supplies it — and it stays reachable from that
     # expression, which is what supplies the fallback FOR it.
     c.holds_own_fallback = False
-    wrapper.wrapped = c
+    # ATTACK (identity): the aggregation the fallback-supplying expression exposes
+    # is a SECOND aggregation whose parts are as usable as the resolved one's.
+    c2 = Expression(requested_final, False)
+    c2.parts_usable = c.parts_usable
+    wrapper.wrapped = c2
     # The value the returned expression supplies is the one resolution arrived
     # at for the requested fallback.
     wrapper.fallback = supplied
```

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -546,7 +546,9 @@
     # which is false of the real callee; and such a model can no longer describe
     # leaving the fallback in place while wrapping, which is the behaviour the
     # clearing exists to prevent.
-    c.holds_own_fallback = fallback is not None
+    # ATTACK (A4 correspondence): the modelled fact is asserted the other way --
+    # the resolved aggregation holds NO fallback value of its own at this point.
+    c.holds_own_fallback = False
     if aggregating_operand and not requested_final:
         # The resolved aggregation aggregates over another aggregation and a
         # non-final resolution was requested: rejected, no expression produced.
```

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -546,7 +546,8 @@
     # which is false of the real callee; and such a model can no longer describe
     # leaving the fallback in place while wrapping, which is the behaviour the
     # clearing exists to prevent.
-    c.holds_own_fallback = fallback is not None
+    # ATTACK (A4 dropped): the resolved aggregation is never modelled as holding
+    # a fallback value of its own at all.
     if aggregating_operand and not requested_final:
         # The resolved aggregation aggregates over another aggregation and a
         # non-final resolution was requested: rejected, no expression produced.
@@ -587,10 +588,7 @@
     # The returned fallback-supplying expression must carry the same final-flag
     # as the aggregation it supplies the fallback for.
     wrapper.is_final_aggregation = c.is_final_aggregation
-    # The aggregation itself no longer holds the fallback value — the returned
-    # expression is what supplies it — and it stays reachable from that
-    # expression, which is what supplies the fallback FOR it.
-    c.holds_own_fallback = False
+    # ATTACK (A10 dropped as redundant): nothing to clear -- it was never set.
     wrapper.wrapped = c
     # The value the returned expression supplies is the one resolution arrived
     # at for the requested fallback.
```

Attack 18 — `atk_18.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -574,19 +574,16 @@
             supplied = fallback
     # A fallback is supplied: return a distinct expression that supplies it. It
     # is built unmarked.
-    wrapper = Expression(False, True)
-    # Pin the modelled fact (G-AX negative control (3)): a freshly constructed
-    # fallback wrapper is UNMARKED — the real one inherits the class default
-    # until assigned. A model whose wrapper is born marked is unfaithful to the
-    # real callee and must not verify.
-    Assert(not wrapper.is_final_aggregation)
+    # ATTACK (A8b correspondence): the fallback wrapper is born ALREADY MARKED,
+    # and the Assert that refinement.md A8b claims makes this unfaithful model
+    # fail verification is deleted with it. The Assert is inside the impl region,
+    # so the spec stays byte-identical.
+    wrapper = Expression(requested_final, True)
     # Its parts are the resolved aggregation, which always stands as a part of the
     # expression built over it, and the value it supplies: so all of its parts are
     # usable exactly when that value is.
     wrapper.parts_usable = supplied.usable
-    # The returned fallback-supplying expression must carry the same final-flag
-    # as the aggregation it supplies the fallback for.
-    wrapper.is_final_aggregation = c.is_final_aggregation
+    # The flag was stamped at construction instead.
     # The aggregation itself no longer holds the fallback value — the returned
     # expression is what supplies it — and it stays reachable from that
     # expression, which is what supplies the fallback FOR it.
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -568,9 +568,9 @@
             resolution_yield.resolution_of = fallback
             supplied = resolution_yield
         else:
-            # Resolution handed back the very value it was given: a value already
-            # in resolved form is its own resolved form, so that value is what is
-            # supplied, exactly as it arrived.
+            # ATTACK (frame): the step handed back the very value it was given --
+            # supply it, but first WIPE the provenance edge it arrived carrying.
+            fallback.resolution_of = None
             supplied = fallback
     # A fallback is supplied: return a distinct expression that supplies it. It
     # is built unmarked.
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** G-EQ refinement fidelity (docs/architecture.md §5) for the nagini bundle of django__django-15375. Per brief, R/I legs are G-CONF's job; I concentrated on the A legs and the model↔patch correspondence. Bundle byte-untouched throughout (`git status --porcelain benchmark-verified/django__django-15375/` => 0 lines, checked at start and end). Attack verifications and resolve runs were launched 3 at a time as detached background jobs (each Nagini check spawns a JVM+Z3); this changed only the schedule — every attack was fully verified and every needed resolve run completed.

**POSITIVE CONTROL:** `pos_control.py` (byte-identical copy of model.py). `bash scripts/nagini_verify.sh pos_control.py` => 'Verification successful', 30.79s, exit 0. Spec is satisfiable and the verifier is live.

**PREPATCH REPRODUCED:** yes — atk_1.py. I diffed model.py vs model_prepatch.py: the only behavioural delta is step A9 (`wrapper.is_final_aggregation = c.is_final_aggregation`), and atk_1 drops exactly that line. `python -m swebench_unified.adversary weakness nagini django__django-15375 atk_1.py` => exit 2, NOT-A-COUNTEREXAMPLE (does not verify). The spec senses the change (G-DIFF holds).

**SAME-SPEC:** all 19 attacks + pos_control returned 'SAME — attack shares the bundle's exact specification'. Every attack edits ONLY the impl region; axioms/@Pure/Requires/Ensures/Exsures byte-identical.

**ATTACK LEDGER** — path / command / observed result. Command for every attack: `python -m swebench_unified.adversary weakness nagini django__django-15375 atk_N.py`. Resolve form: `run_resolve('django__django-15375', <patch text>)` via do_resolve.py (harness.run_resolve, timeout 3600).

1.  atk_1.py  — PREPATCH: drop A9. => exit 2, does not verify. REJECTED (good).
2.  atk_2.py  — IDENTITY (no-fallback path): return a SECOND, separately built aggregation with all three parts_usable legs assigned, not `c`. => exit 0 CANDIDATE. patch_atk_2.diff (second FULL resolution: base + the `:53` condition step). RESOLVE: resolved=True completed=True attempts=1 flaky=False F2P 1/1 P2P 95/95.
3.  atk_3.py  — CONTROL-FLOW-EFFECT: decide the nested-aggregate refusal BEFORE the unresolvable-part refusal (reorder the two). => exit 0 CANDIDATE. patch_atk_3.diff moves `:53` after the `not summarize` guard. RESOLVE: resolved=True attempts=1 flaky=False F2P 1/1 P2P 95/95. Sound: on the reject path the exception escapes either way, so the order is unobservable.
4.  atk_4.py  — UNGROUNDED-ORACLE ECHO: drop the `vacuous_condition` leg from parts_usable. => exit 2, does not verify. REJECTED (the leg is load-bearing).
5.  atk_5.py  — SELF-RESOLUTION CYCLE: write the provenance edge on the yield unconditionally, without asking whether a DISTINCT value came back. => exit 2, does not verify. REJECTED (case (b)'s two arms bite).
6.  atk_6.py  — BOUNDARY over-claim: `wrapper.parts_usable = supplied.usable or c.parts_usable`. => exit 2, does not verify. REJECTED (A8c's equality is two-sided).
7.  atk_7.py  — PARTIAL DOMAIN: refuse a non-expression fallback value that is not usable as it stands (the B3 precondition smuggled back as a refusal). => exit 2, does not verify. REJECTED — confirms B3's repair is live and the domain really is whole.
8.  atk_8.py  — IDENTITY (fallback path): the wrapper exposes a SECOND, separately built aggregation. => exit 0 CANDIDATE. patch_atk_8.diff (second full resolution). RESOLVE: resolved=True attempts=1 flaky=False F2P 1/1 P2P 95/95.
9.  atk_9.py  — FRAME GAP on the reject path: scribble `resolution_yield.resolution_of = resolution_yield` (un-framed by the Exsures) before refusing. => exit 0 CANDIDATE. patch_atk_9.diff runs the delegated step on the reject path.
10. atk_10.py — FRAME (stated): write over `resolution_yield.usable` to make the wrapper claim easier. => exit 2, does not verify. REJECTED (the Ensures frames it).
11. atk_11.py — UNGROUNDED-ORACLE ECHO: `c.parts_usable = True` unconditionally (the pre-repair over-claim). => exit 2, does not verify. REJECTED.
12. atk_12.py — BOUNDARY: OR instead of AND on the operand/condition legs. => exit 2, does not verify. REJECTED.
13. atk_13.py — PARTIAL DOMAIN / control-flow: return the bare aggregation instead of building the wrapper when the supplied value is not usable. => exit 2, does not verify. REJECTED (B1's `supplies_fallback` clause bites).
14. atk_14.py — IDENTITY: no-fallback path returns a second aggregation inheriting `c.parts_usable`. => exit 0 CANDIDATE. patch_atk_14.diff = `return c.copy()`. RESOLVE: resolved=True attempts=1 flaky=False F2P 1/1 P2P 95/95.
15. atk_15.py — IDENTITY: the wrapper exposes a second aggregation inheriting `c.parts_usable`. => exit 0 CANDIDATE. patch_atk_15.diff wraps `c.copy()`. RESOLVE: resolved=True attempts=1 flaky=False F2P 1/1 P2P 95/95.
16. atk_16.py — A4 CORRESPONDENCE REVERSED: `c.holds_own_fallback = False` before the branch (the resolved aggregation holds none of its own from that point). => exit 0 CANDIDATE. patch_atk_16.diff reads the value off `c` and moves the reset up to `:53`. RESOLVE: resolved=True completed=True F2P 1/1 P2P 95/95 (attempts=2, flaky — earlier attempt did not complete; report is full-green).
17. atk_17.py — A4+A10 BOTH DROPPED: `c` is never modelled as holding a fallback of its own and the reset disappears. => exit 0 CANDIDATE. patch_atk_17.diff removes `c.default = None`. RESOLVE: resolved=True F2P 1/1 P2P 95/95 (first run flaky; a second re-run hit a docker ImageNotFound INFRA error — not a verdict — and a THIRD clean run gave attempts=1 flaky=False resolved=True).
18. atk_18.py — A8b CORRESPONDENCE: construct the wrapper ALREADY MARKED (`Expression(requested_final, True)`), DELETE the `Assert(not wrapper.is_final_aggregation)`, and drop A9. => exit 0 CANDIDATE. patch_atk_18.diff stamps the flag at construction via a marked Coalesce subclass. RESOLVE: resolved=True attempts=1 flaky=False F2P 1/1 P2P 95/95. See the counterexample field: refutes refinement.md A8b's incidental claim about the Assert. Doc over-claim only.
19. atk_19.py — FRAME on the non-distinct arm: wipe `fallback.resolution_of` before supplying the written value. => exit 2, does not verify. REJECTED (case (b)'s frame is stated and bites).

**SO:** 19 attacks; 10 REJECTED (do not verify); 9 CANDIDATES; 9 faithful refined patches materialized, all 9 `git apply --check`-clean at base_commit beb7ddbc; 9 resolve runs EXECUTED; 9/9 RESOLVED with F2P 1/1 and P2P 95/95. Every needed resolve run completed with a report. Nothing INCONCLUSIVE. The three flaky/infra hiccups (atk_9, atk_16, atk_17) were all re-run; atk_9 and atk_17 came back attempts=1 flaky=False, and atk_16's completed report is full-green — per host-saturation policy these are load artifacts, not verdicts, and in every case the recorded verdict is resolved=True with a complete report.

**A-LEG AUDIT (the brief's focus).** model.py's `axioms-start` region is EMPTY and meta.json records `"axioms": []`. I grepped the model for `@ContractOnly`, `@Pure`, `Assume`, `sorry`: zero hits. So there is NO A-consumed leg — nothing is assumed about the function under change, which is the right posture (we never axiomatize the function under change). meta.json declares exactly ONE `deep_model_references` entry, kind `A-reference`.

I validated that A-reference myself rather than trusting the stamp: `git worktree add --detach` at base_commit beb7ddbcee03270e833b2f74927ccfc8027aa693, then `PYTHONPATH=<wt> python3 axiom_check.py` => exit 0, 42 observations, all seven facts hold — including fact (7)'s NEGATIVE CONTROL (the operand resolution ALONE, `Func.resolve_expression`, resolves every operand and stamps `is_summary` while leaving the condition a raw `Q` with no `as_sql`, because it walks `c.source_expressions` directly at expressions.py:694-699 and the condition is resolved one line later at aggregates.py:53). That control is what makes 'carries the right final-flag' and 'was actually resolved' provably come apart in the REAL code rather than being trivially co-extensive.

Crucially I confirmed the check ABSTAINS from the one fact that would make it vacuous: grepping `is_summary` in axiom_check.py shows it asserts `inner.is_summary == summarize` (the wrapped aggregation), the no-fallback aggregation's flag, and the fresh-`Coalesce` `is_summary is False` negative control — but never the returned WRAPPER's own propagated flag. That propagation IS the change; asserting it would make G-AX pass vacuously on the base image. The abstention is real.

Correspondence to the real callees checked by hand against `git show beb7ddbc:django/db/models/aggregates.py`: A2's four rejection legs all exist and all escape the body (`:52` operand, `:53` condition, `:66` expression-valued default, `:68` `c._output_field_or_none` → expressions.py:272-282, which re-raises unless the field resolved to None; that fourth leg escapes as AttributeError via `get_source_fields` at `:38`, and is reached only when a value is supplied — matching the bridge's asymmetric conjunction). A3's modelled effects are the literal `c = self.copy()` / `c.is_summary = summarize` of expressions.py:246-247 and :696.

A3b's two delegated steps are real and dispatched on the operand's/condition's own class (`OuterRef.resolve_expression` returning its inner name at :645-648; `MultiColSource.resolve_expression` = `return self` at fields/related_lookups.py:25-26), and `vacuous_condition` is correctly the CONJUNCTION of left-as-written and not-compilable — `Node.__bool__` (utils/tree.py:60-62) makes a childless `Q` falsy so `:53`'s `and` short-circuits, while a `WhereNode()` is equally falsy yet HAS `as_sql` (sql/where.py:65). A5's guard is the literal `if not summarize: ... if expr.contains_aggregate: raise FieldError` at :54-62. A6 is `if (default := c.default) is None: return c` at :63-64 — identity, not truthiness, matching the model. A9's `coalesce.is_summary = c.is_summary` is verbatim the gold hunk in patch.diff. A10 is `c.default = None` at :67. All hold.

**REFINEMENT.MD LEG-KIND AUDIT:** all 16 rows of §A carry a kind and none is kind-3. R: A1, A2, A4, A5, A6, A8, A8b, A8c, A11, A12. 'I (under R)' with G-AX A-reference backing: A3, A3b, A7, A10, A13. I: A9 — the single genuinely changed operation, correctly an I step since it is the very same `coalesce.is_summary = c.is_summary` assignment with `is_summary` refined to a field by R. §C states there is no kind-3 step and no consumed `@ContractOnly` axiom, and I verified both independently (empty axioms region, `axioms: []`, no ContractOnly/Assume/sorry anywhere). No leg is left unclassified. The A-legs' correspondence to the real callees holds.

**One documentation defect found:** A8b's over-claim that the `Assert` makes a born-marked wrapper fail verification (refuted by atk_18, which deletes the Assert from the impl region while keeping the spec byte-identical). Cosmetic — it does not affect any leg's kind and admits no incorrect impl.

**WHY SOUND RATHER THAN INCONCLUSIVE:** 19 distinct same-spec wrong-impl attacks were run (well past the ≥5 floor), spanning every category the brief names — partial-domain (atk_7, atk_13), boundary in both directions (atk_6, atk_12), control-flow-effect (atk_3, atk_13), ungrounded-oracle echo (atk_4, atk_11), frame/reject-path (atk_9, atk_10, atk_19), self-resolution cycle (atk_5), identity-of-the-exposed-object (atk_2, atk_8, atk_14, atk_15), and direct A-leg correspondence probes (atk_16, atk_17, atk_18). The prepatch bug was re-encoded and is REJECTED; the positive control VERIFIES; the A-reference was re-validated from a fresh base-commit worktree; and every CANDIDATE's faithful patch was executed under the official harness with a completed, full-green verdict. None breaks verify⇒correct.

**RESIDUAL RISK (advisory, not a fail):** the 9 verifying variants show real behavioural slack — the spec does not pin the IDENTITY of the aggregation it exposes (only its fields), does not observe the `holds_own_fallback` intermediate state on any returned object, does not fix the stamp's timing, and does not frame `resolution_yield.resolution_of` on the reject path. In every case the slack is over operations observationally equivalent to the gold patch on the real callee, which is what a refinement-fidelity spec is permitted to admit, and the identity slack is the bundle's OWN documented calibration (B5). The frame gap on the reject path (atk_9) is the one I would tighten if the cell is ever revised — it is a genuine under-specification, harmless here only because the exception discards the object. I found no input on which a verifying impl and the gold patch differ observably.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_19.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 9 | `atk_2.py`, `atk_3.py`, `atk_8.py`, `atk_9.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py`, `atk_18.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no counterexample survived. 19 same-spec attacks were run through `adversary weakness`; 9 came back CANDIDATE (share the frozen spec AND verify), and every one of those 9 had its faithful refined patch materialized, checked with `git apply --check` at base_commit, and EXECUTED under the official harness (run_resolve). ALL NINE RESOLVED (resolved=True, completed=True, F2P 1/1, P2P 95/95). So no verifying same-spec wrong impl was exhibited whose refined patch fails to resolve: verify⇏correct is NOT falsified on this cell.

On audit the 9 verifying impls are not wrong impls — each is observationally equivalent to the gold patch, which is why each resolves. Grouped by the freedom each exploits:

(1) IDENTITY OF THE EXPOSED AGGREGATION (atk_2, atk_8, atk_14, atk_15). The spec describes the returned/exposed aggregation by its FIELDS (final-flag, supplies-nothing, holds-nothing, parts_usable on the three-part condition) and never pins it to be the SAME OBJECT resolution built. So an impl may substitute a second aggregation, provided that one's parts really are in resolved form. atk_2/atk_14 do this on the no-fallback path, atk_8/atk_15 on the wrapper's exposed aggregation. Refined faithfully — atk_2/atk_8 as a second FULL resolution (`super().resolve_expression` PLUS the `:53` condition step), atk_14/atk_15 as `c.copy()` — all four resolve. This is exactly the calibration refinement.md B5 documents (`pos-control-second-full-resolution`): the parts_usable clause deliberately forbids wrapping an aggregation whose parts were NEVER resolved, not wrapping a different fully-resolved one. B5 predicts this resolves; execution confirms it. The distinction is load-bearing and correctly drawn: atk_11 (`c.parts_usable = True` unconditionally) and atk_4/atk_12 (dropping or weakening a leg) all FAIL verification.

(2) MODELLED STATE ON `holds_own_fallback` (atk_16, atk_17). Steps A4/A10 model the resolved aggregation as holding the fallback value and then being cleared. Nothing in the postcondition observes that intermediate state on any returned object, so an impl may reverse A4 (atk_16: read the value off `c` and clear it immediately, so `c` holds none from that point on, including on the refusal) or drop A4 and A10 together (atk_17: no reset at all). Both refine faithfully and both resolve — and I verified WHY: `Coalesce` is a `Func` with no `default` attribute, and the only readers of `.default` in the whole ORM are `aggregates.py:63` / `:67` themselves plus the unrelated `Case.default` (`expressions.py:1080-1137`). Nothing downstream reads the wrapped aggregate's `.default`, so the reset is observationally dead. refinement.md A4 itself concedes it is 'modelled STATE, not a step of the work'.

(3) STAMP TIMING / RIGHT-HAND SIDE (atk_18). The wrapper is born ALREADY MARKED and step A9 is dropped; the `Assert(not wrapper.is_final_aggregation)` is deleted along with it. Refined as a `Coalesce` subclass carrying `is_summary = c.is_summary` at construction. Resolves — same final field value.

(4) UNOBSERVABLE WRITE ON THE REJECT PATH (atk_9). The `Exsures` frames the yield's `usable` but NOT its `resolution_of`, so the nested-aggregate reject path may scribble a false provenance edge before refusing. Refined as running the delegated step on the written default on the reject path too. Resolves — the `FieldError` escapes and the object is discarded, so the write is unobservable. A genuine but harmless frame gap.

ONE DOCUMENTATION DEFECT (not a spec weakness). atk_18 refutes refinement.md A8b's incidental claim that `Assert(not wrapper.is_final_aggregation)` 'makes a model variant whose wrapper is born already marked FAIL verification'. It does not: the Assert lives INSIDE the impl region, so an attacker deletes it together with the construction change and the spec stays byte-identical (`adversary same-spec` => SAME). The Assert constrains the bundle's own impl and the G-MUT mutant, not the space of admissible impls. This is an over-claim about a proof annotation's discriminating power — cosmetic, affects no leg's kind, and admits no incorrect impl (atk_18 is behaviourally correct and resolves). This is the same finding the retained prior G-EQ pass recorded via its atk_11, independently reproduced here.
```

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 19 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** G-EQ refinement fidelity (docs/architecture.md §5) for the nagini bundle of django__django-15375. Per brief, R/I legs are G-CONF's job; I concentrated on the A legs and the model↔patch correspondence. Bundle byte-untouched throughout (`git status --porcelain benchmark-verified/django__django-15375/` => 0 lines, checked at start and end). Attack verifications and resolve runs were launched 3 at a time as detached background jobs (each Nagini check spawns a JVM+Z3); this changed only the schedule — every attack was fully verified and every needed resolve run completed.

**POSITIVE CONTROL:** `pos_control.py` (byte-identical copy of model.py). `bash scripts/nagini_verify.sh pos_control.py` => 'Verification successful', 30.79s, exit 0. Spec is satisfiable and the verifier is live.

**PREPATCH REPRODUCED:** yes — atk_1.py. I diffed model.py vs model_prepatch.py: the only behavioural delta is step A9 (`wrapper.is_final_aggregation = c.is_final_aggregation`), and atk_1 drops exactly that line. `python -m swebench_unified.adversary weakness nagini django__django-15375 atk_1.py` => exit 2, NOT-A-COUNTEREXAMPLE (does not verify). The spec senses the change (G-DIFF holds).

**SAME-SPEC:** all 19 attacks + pos_control returned 'SAME — attack shares the bundle's exact specification'. Every attack edits ONLY the impl region; axioms/@Pure/Requires/Ensures/Exsures byte-identical.

**ATTACK LEDGER** — path / command / observed result. Command for every attack: `python -m swebench_unified.adversary weakness nagini django__django-15375 atk_N.py`. Resolve form: `run_resolve('django__django-15375', <patch text>)` via do_resolve.py (harness.run_resolve, timeout 3600).

1.  atk_1.py  — PREPATCH: drop A9. => exit 2, does not verify. REJECTED (good).
2.  atk_2.py  — IDENTITY (no-fallback path): return a SECOND, separately built aggregation with all three parts_usable legs assigned, not `c`. => exit 0 CANDIDATE. patch_atk_2.diff (second FULL resolution: base + the `:53` condition step). RESOLVE: resolved=True completed=True attempts=1 flaky=False F2P 1/1 P2P 95/95.
3.  atk_3.py  — CONTROL-FLOW-EFFECT: decide the nested-aggregate refusal BEFORE the unresolvable-part refusal (reorder the two). => exit 0 CANDIDATE. patch_atk_3.diff moves `:53` after the `not summarize` guard. RESOLVE: resolved=True attempts=1 flaky=False F2P 1/1 P2P 95/95. Sound: on the reject path the exception escapes either way, so the order is unobservable.
4.  atk_4.py  — UNGROUNDED-ORACLE ECHO: drop the `vacuous_condition` leg from parts_usable. => exit 2, does not verify. REJECTED (the leg is load-bearing).
5.  atk_5.py  — SELF-RESOLUTION CYCLE: write the provenance edge on the yield unconditionally, without asking whether a DISTINCT value came back. => exit 2, does not verify. REJECTED (case (b)'s two arms bite).
6.  atk_6.py  — BOUNDARY over-claim: `wrapper.parts_usable = supplied.usable or c.parts_usable`. => exit 2, does not verify. REJECTED (A8c's equality is two-sided).
7.  atk_7.py  — PARTIAL DOMAIN: refuse a non-expression fallback value that is not usable as it stands (the B3 precondition smuggled back as a refusal). => exit 2, does not verify. REJECTED — confirms B3's repair is live and the domain really is whole.
8.  atk_8.py  — IDENTITY (fallback path): the wrapper exposes a SECOND, separately built aggregation. => exit 0 CANDIDATE. patch_atk_8.diff (second full resolution). RESOLVE: resolved=True attempts=1 flaky=False F2P 1/1 P2P 95/95.
9.  atk_9.py  — FRAME GAP on the reject path: scribble `resolution_yield.resolution_of = resolution_yield` (un-framed by the Exsures) before refusing. => exit 0 CANDIDATE. patch_atk_9.diff runs the delegated step on the reject path.
10. atk_10.py — FRAME (stated): write over `resolution_yield.usable` to make the wrapper claim easier. => exit 2, does not verify. REJECTED (the Ensures frames it).
11. atk_11.py — UNGROUNDED-ORACLE ECHO: `c.parts_usable = True` unconditionally (the pre-repair over-claim). => exit 2, does not verify. REJECTED.
12. atk_12.py — BOUNDARY: OR instead of AND on the operand/condition legs. => exit 2, does not verify. REJECTED.
13. atk_13.py — PARTIAL DOMAIN / control-flow: return the bare aggregation instead of building the wrapper when the supplied value is not usable. => exit 2, does not verify. REJECTED (B1's `supplies_fallback` clause bites).
14. atk_14.py — IDENTITY: no-fallback path returns a second aggregation inheriting `c.parts_usable`. => exit 0 CANDIDATE. patch_atk_14.diff = `return c.copy()`. RESOLVE: resolved=True attempts=1 flaky=False F2P 1/1 P2P 95/95.
15. atk_15.py — IDENTITY: the wrapper exposes a second aggregation inheriting `c.parts_usable`. => exit 0 CANDIDATE. patch_atk_15.diff wraps `c.copy()`. RESOLVE: resolved=True attempts=1 flaky=False F2P 1/1 P2P 95/95.
16. atk_16.py — A4 CORRESPONDENCE REVERSED: `c.holds_own_fallback = False` before the branch (the resolved aggregation holds none of its own from that point). => exit 0 CANDIDATE. patch_atk_16.diff reads the value off `c` and moves the reset up to `:53`. RESOLVE: resolved=True completed=True F2P 1/1 P2P 95/95 (attempts=2, flaky — earlier attempt did not complete; report is full-green).
17. atk_17.py — A4+A10 BOTH DROPPED: `c` is never modelled as holding a fallback of its own and the reset disappears. => exit 0 CANDIDATE. patch_atk_17.diff removes `c.default = None`. RESOLVE: resolved=True F2P 1/1 P2P 95/95 (first run flaky; a second re-run hit a docker ImageNotFound INFRA error — not a verdict — and a THIRD clean run gave attempts=1 flaky=False resolved=True).
18. atk_18.py — A8b CORRESPONDENCE: construct the wrapper ALREADY MARKED (`Expression(requested_final, True)`), DELETE the `Assert(not wrapper.is_final_aggregation)`, and drop A9. => exit 0 CANDIDATE. patch_atk_18.diff stamps the flag at construction via a marked Coalesce subclass. RESOLVE: resolved=True attempts=1 flaky=False F2P 1/1 P2P 95/95. See the counterexample field: refutes refinement.md A8b's incidental claim about the Assert. Doc over-claim only.
19. atk_19.py — FRAME on the non-distinct arm: wipe `fallback.resolution_of` before supplying the written value. => exit 2, does not verify. REJECTED (case (b)'s frame is stated and bites).

**SO:** 19 attacks; 10 REJECTED (do not verify); 9 CANDIDATES; 9 faithful refined patches materialized, all 9 `git apply --check`-clean at base_commit beb7ddbc; 9 resolve runs EXECUTED; 9/9 RESOLVED with F2P 1/1 and P2P 95/95. Every needed resolve run completed with a report. Nothing INCONCLUSIVE. The three flaky/infra hiccups (atk_9, atk_16, atk_17) were all re-run; atk_9 and atk_17 came back attempts=1 flaky=False, and atk_16's completed report is full-green — per host-saturation policy these are load artifacts, not verdicts, and in every case the recorded verdict is resolved=True with a complete report.

**A-LEG AUDIT (the brief's focus).** model.py's `axioms-start` region is EMPTY and meta.json records `"axioms": []`. I grepped the model for `@ContractOnly`, `@Pure`, `Assume`, `sorry`: zero hits. So there is NO A-consumed leg — nothing is assumed about the function under change, which is the right posture (we never axiomatize the function under change). meta.json declares exactly ONE `deep_model_references` entry, kind `A-reference`.

I validated that A-reference myself rather than trusting the stamp: `git worktree add --detach` at base_commit beb7ddbcee03270e833b2f74927ccfc8027aa693, then `PYTHONPATH=<wt> python3 axiom_check.py` => exit 0, 42 observations, all seven facts hold — including fact (7)'s NEGATIVE CONTROL (the operand resolution ALONE, `Func.resolve_expression`, resolves every operand and stamps `is_summary` while leaving the condition a raw `Q` with no `as_sql`, because it walks `c.source_expressions` directly at expressions.py:694-699 and the condition is resolved one line later at aggregates.py:53). That control is what makes 'carries the right final-flag' and 'was actually resolved' provably come apart in the REAL code rather than being trivially co-extensive.

Crucially I confirmed the check ABSTAINS from the one fact that would make it vacuous: grepping `is_summary` in axiom_check.py shows it asserts `inner.is_summary == summarize` (the wrapped aggregation), the no-fallback aggregation's flag, and the fresh-`Coalesce` `is_summary is False` negative control — but never the returned WRAPPER's own propagated flag. That propagation IS the change; asserting it would make G-AX pass vacuously on the base image. The abstention is real.

Correspondence to the real callees checked by hand against `git show beb7ddbc:django/db/models/aggregates.py`: A2's four rejection legs all exist and all escape the body (`:52` operand, `:53` condition, `:66` expression-valued default, `:68` `c._output_field_or_none` → expressions.py:272-282, which re-raises unless the field resolved to None; that fourth leg escapes as AttributeError via `get_source_fields` at `:38`, and is reached only when a value is supplied — matching the bridge's asymmetric conjunction). A3's modelled effects are the literal `c = self.copy()` / `c.is_summary = summarize` of expressions.py:246-247 and :696.

A3b's two delegated steps are real and dispatched on the operand's/condition's own class (`OuterRef.resolve_expression` returning its inner name at :645-648; `MultiColSource.resolve_expression` = `return self` at fields/related_lookups.py:25-26), and `vacuous_condition` is correctly the CONJUNCTION of left-as-written and not-compilable — `Node.__bool__` (utils/tree.py:60-62) makes a childless `Q` falsy so `:53`'s `and` short-circuits, while a `WhereNode()` is equally falsy yet HAS `as_sql` (sql/where.py:65). A5's guard is the literal `if not summarize: ... if expr.contains_aggregate: raise FieldError` at :54-62. A6 is `if (default := c.default) is None: return c` at :63-64 — identity, not truthiness, matching the model. A9's `coalesce.is_summary = c.is_summary` is verbatim the gold hunk in patch.diff. A10 is `c.default = None` at :67. All hold.

**REFINEMENT.MD LEG-KIND AUDIT:** all 16 rows of §A carry a kind and none is kind-3. R: A1, A2, A4, A5, A6, A8, A8b, A8c, A11, A12. 'I (under R)' with G-AX A-reference backing: A3, A3b, A7, A10, A13. I: A9 — the single genuinely changed operation, correctly an I step since it is the very same `coalesce.is_summary = c.is_summary` assignment with `is_summary` refined to a field by R. §C states there is no kind-3 step and no consumed `@ContractOnly` axiom, and I verified both independently (empty axioms region, `axioms: []`, no ContractOnly/Assume/sorry anywhere). No leg is left unclassified. The A-legs' correspondence to the real callees holds.

**One documentation defect found:** A8b's over-claim that the `Assert` makes a born-marked wrapper fail verification (refuted by atk_18, which deletes the Assert from the impl region while keeping the spec byte-identical). Cosmetic — it does not affect any leg's kind and admits no incorrect impl.

**WHY SOUND RATHER THAN INCONCLUSIVE:** 19 distinct same-spec wrong-impl attacks were run (well past the ≥5 floor), spanning every category the brief names — partial-domain (atk_7, atk_13), boundary in both directions (atk_6, atk_12), control-flow-effect (atk_3, atk_13), ungrounded-oracle echo (atk_4, atk_11), frame/reject-path (atk_9, atk_10, atk_19), self-resolution cycle (atk_5), identity-of-the-exposed-object (atk_2, atk_8, atk_14, atk_15), and direct A-leg correspondence probes (atk_16, atk_17, atk_18). The prepatch bug was re-encoded and is REJECTED; the positive control VERIFIES; the A-reference was re-validated from a fresh base-commit worktree; and every CANDIDATE's faithful patch was executed under the official harness with a completed, full-green verdict. None breaks verify⇒correct.

**RESIDUAL RISK (advisory, not a fail):** the 9 verifying variants show real behavioural slack — the spec does not pin the IDENTITY of the aggregation it exposes (only its fields), does not observe the `holds_own_fallback` intermediate state on any returned object, does not fix the stamp's timing, and does not frame `resolution_yield.resolution_of` on the reject path. In every case the slack is over operations observationally equivalent to the gold patch on the real callee, which is what a refinement-fidelity spec is permitted to admit, and the identity slack is the bundle's OWN documented calibration (B5). The frame gap on the reject path (atk_9) is the one I would tighten if the cell is ever revised — it is a genuine under-specification, harmless here only because the exception discards the object. I found no input on which a verifying impl and the gold patch differ observably.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**REFERENCE DISCIPLINE.** Worktree at base beb7ddbcee with patch.diff APPLIED is the reference for the modeled function (the fix's `coalesce.is_summary = c.is_summary` tail); base commit is the reference only for untouched callees. I did NOT report the patch delta itself as divergence.

**SPEC REGION.** `adversary same-spec` on a byte-copy of the bundle model.py returns exit 0 ("SAME"). Live region_hashes differ from meta.json only in impl/pre/post/spec_view, and model_prepatch.py shares the identical live spec_view (548c7c76) with model.py -- i.e. both twins carry the same current spec text; the meta drift is a stale digest, not a spec mismatch between the artifacts I compared. Axioms and pure regions hash-match meta exactly, and both are EMPTY (no @ContractOnly callee consumed), so there is no axiom over-assumption surface at all.

**BASELINES REPRODUCED.** G-CONF: 135376 inputs, 0 disagreements. G-AX: OK over 42 observations, asserting only unchanged-callee facts present in the base image.

MY OWN INDEPENDENT ATTACKS (all bridge columns computed a priori by calling the DELEGATED callee on the WRITTEN object, never off the oracle's answer):

(1) Widened realization space v2 -- 21 operand families, 23 default families, 20 filter families, 5 aggregate kinds = 78,960 cases beyond the bundle's space. Added Star, RawSQL, ExpressionWrapper, Case/When, Length, Coalesce-as-operand, Ref-over-agg, Subquery, Exists, OrderBy, ExpressionList, OuterRef at 1/2 nesting with and without explicit output_field; defaults incl. tuple, bytes, Value(None), NothingNode, WhereNode, raw Q, Sum, MultiColSource; filters incl. a TRUTHY resolved WhereNode, Value(True/False), Star, RawSQL, Ref, Sum, OrderBy, Q(Q()). Result: 0 disagreements.

(2) Written-vs-resolved split hunt on `aggregating_operand`. mapping.md maps it to contains_aggregate over the RESOLVED sources (aggregates.py:57-59 loops the resolved c). I found a genuine split family the bundle never realizes: Case(When(num__gt=1, then=Sum('num'))) has written contains_aggregate False but resolved True. Measured against the real callee: summarize=False -> REFUSED ("Cannot compute Sum('<Case...')"), summarize=True -> produced. That is exactly what the RESOLVED reading predicts and the written reading contradicts -- so mapping.md's choice is the faithful one and this is a strengthening of the spec's credibility, not a break.

(3) Probe v3 rebuilt with `aggregating_operand` computed from the resolved sources plus the entire Case/Sum, Lower/Sum, Abs/Sum, Coalesce/Sum, ExprWrapper/Sum, ExprList/Sum, OrderBy/Sum, Subquery-with-annotated-agg family: 47,360 cases, 0 disagreements, 0 crashes.

(4) Multi-operand probe (the bundle's space is 1-operand ONLY): a real Aggregate subclass over TWO operands x 6 operand kinds^2 x 4 filters x 3 defaults x both summarize = 864 rows, incl. one operand usable and the other not. The three-part parts_usable equality (operand_resolution_usable AND condition_resolution_usable AND NOT vacuous_condition) held on every produced bare aggregation: 0 mismatches. The conjunction generalizes correctly over multiple operands, which the spec's prose asserts but the bundle never tested.

(5) AST sweep of the whole django tree for any resolve_expression that returns None explicitly or can fall off its end (which would make `_parts_usable`'s None-skip diverge from the model's boolean): 0 hits, so that hole is not reachable.

FALSE ALARM I RETRACTED, recorded for honesty: probe v3 first reported 420 "disagreement signatures", all of shape written_intact=None on the refused path. Root cause was MY oracle stub -- I had widened the rejection catch to (FieldError, AttributeError) but returned a hardcoded None for written_intact instead of recomputing it as the real oracle does. After computing usable-before the call and comparing after, all 420 vanished (0/47360). None of these were spec defects.

**BOUNDARY CASES I CHECKED AND FOUND CORRECTLY MODELED:** the vacuous_condition CONJUNCTION (left-as-written AND not compilable) -- a childless WhereNode is equally falsy and short-circuits :53 yet HAS as_sql, and the real callee keeps parts usable for it, which a falsiness-only reading would get wrong; the asymmetric :68 output-type rejection (mixed-type aggregate produced bare, refused with a fallback); OuterRef-over-OuterRef handing back a bare inner OuterRef with no as_sql while nothing raised (resolution succeeded but yield unusable -- correctly disjoint from parts_resolve); Ref/MultiColSource `return self` (step hands back the very value it was given, usable and not-usable arms both); provenance pinned by identity from the traced delegated call rather than by equality, which is load-bearing for Subquery/Exists that inherit object.`__eq__`.

**CONCLUSION.** No input found on which the modeled function disagrees with the real patched callee. The spec is not too strong: every clause that could have been an over-claim (the unconditional parts_usable, the falsiness-only vacuity reading, the written-form aggregating_operand, provenance-by-equality) is either read as an input or pinned the way the real callee actually behaves, and I confirmed each with a realization the bundle's own space does not contain. No diverging input to cite; FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET:** leakage / gold-reconstruction of the consumer spec view for django__django-15375 (nagini). Judged against the PUBLIC problem_statement only; hints_text never consulted.

**NO RELAXATION IN THIS BUNDLE.** Checked programmatically, not by assertion: meta.json top-level keys are [additional_change_sites, axioms, base_commit, changed_files, deep_model_references, float_encoding, gates, instance_id, modeled_functions, patch_diff, prepatch_models, region_hashes, repo, schema_version, string_modeling, version] -- no `relaxed_leakage` key ([k for k in meta if 'relax' in k.lower()] -> []); no RELAXED_LEAKAGE.md anywhere under the instance dir (find over ., ../lean, ../velvet, ../ears). So this is an ORDINARY leakage judgement with no unavoidability argument to re-derive, and nothing was inherited from a relaxation document.

**BYTES I JUDGED.** model.py sha256 acecaa8a174db0b6156e132543a6aee4eb0dfba3c104d99f7fe725753bd351f2, which equals the sources hash recorded by both G-LEAK and G-VERIFY, so I judged the same bytes the gates did. I generated the view MYSELF via markers.spec_view(model.py, NaginiBackend.language) -> spec_view.py (599 source lines project to 522; the impl region collapses to the `impl-start / ... / impl-end` elision placeholder). All findings below are on that projection, not on the raw file.

**GOLD EDIT.** patch.diff touches one hunk in django/db/models/aggregates.py: `return Coalesce(...)` becomes `coalesce = Coalesce(...); coalesce.is_summary = c.is_summary; return coalesce`. The discriminator is the propagation of is_summary (the final-flag) onto the Coalesce wrapper. Changed symbol set = {resolve_expression}, and I confirmed 'resolve_expression' is NOT in the problem_statement (substring test on the lowered statement -> False), so it is a symbol the screen must protect rather than one already public.

**WHAT THE PROBLEM_STATEMENT ALREADY GIVES.** Sum("id", default=0) after annotate() emits 'SELECT FROM (SELECT ... COALESCE(SUM(...), ?) AS "id__sum" ...) subquery' -- i.e. the aggregate vanished from the outer select list -- while the long form Coalesce(Sum("id"), 0) works. So `default`, Coalesce-wrapping, the aggregate-vs-annotate interaction, and the fact that the wrapper is the thing that misbehaves are ALL public. The spec view stays strictly inside that envelope, in fully de-repo'd vocabulary (aggregation / fallback value / final-flag / usable as it stands), and never names the mechanism (is_summary) that turns the public symptom into the edit.

MEASUREMENT 1 -- mechanical screen. leakage.screen(model.py, NaginiBackend.language, instance['patch'], instance['problem_statement'], instance['test_patch']) -> hard_failures == []. That covers L1 (diff markers; verbatim gold-patch lines, of which the four candidates are 'return Coalesce(c, default, output_field=c.`_output_field_or_none`)', 'coalesce = Coalesce(...)', 'coalesce.is_summary = c.is_summary', 'return coalesce'), L2 (patched file path 'django/db/models/aggregates.py' and dotted module 'django.db.models.aggregates'), L2/L5 (spec-view identifier embedding 'resolve_expression'), L2/L3 (that symbol named in a view comment/docstring), and L3 narration regex.

MEASUREMENT 2 -- my own independent vocabulary sweep, since a clean screen is necessary not sufficient. Grepped the PROJECTION for is_summary, Coalesce/COALESCE, summarize, output_field/`_output_field`, FieldError, Func, BaseExpression, OuterRef, resolve_expression, contains_aggregate, as_sql, expressions.py, aggregates.py, django.db, Sum(, id__sum, core_book, SELECT, subquery, OperationalError, sqlite, postgres, 4.0.1, annotate, Book. Exactly 5 hits, ALL benign morphological matches on the generic word 'aggregate' inside 'aggregation/aggregates over' (lines 8, 12, 36, 249, 504) -- the domain noun, not a repo symbol. ZERO hits for every repo/edit identifier, notably is_summary and Coalesce. The only 'django' token in the entire 522-line view is the instance id in the line-1 docstring title ('Twin-artifact model for django__django-15375.'), which localizes nothing beyond the task the solver was already handed.

MEASUREMENT 3 -- edit-narration sweep beyond the regex set. Grepped the projection for prepatch/pre-patch/the change/the fix/the edit/propagat/used to/previously/no longer propagat/omitted/missing/forgot/regression/before this/was not set/was not marked/unmarked/born marked/inherit the class default/G-AX -> ZERO hits. Critically, the text in model.py that DOES narrate the edit is confined to the elided impl region and I confirmed it does not survive projection: model.py:578-580 ('a freshly constructed fallback wrapper is UNMARKED -- the real one inherits the class default until assigned ... a model whose wrapper is born marked is unfaithful') greps in the raw file and greps EMPTY in spec_view.py; likewise the prepatch twin's 'PRE-PATCH: the fallback-supplying expression is returned still unmarked -- the final-flag ... is NOT propagated' is impl-region only. Elision is doing its job.

MEASUREMENT 4 -- load-bearing test on the one clause a reconstructor could use. The only view line that constrains the discriminator is post-conditions line 371: `Ensures(Result().is_final_aggregation == requested_final)`. I ran the standard test rather than reasoning about it. (a) Pinned verifier on the prepatch twin: `bash scripts/nagini_verify.sh prepatch.py` -> exit 1, and the SOLE error is 'Postcondition of resolve_aggregation might not hold. Assertion (Result().is_final_aggregation == requested_final) might not hold.' at line 371. (b) Stripped exactly that one Ensures (verified single occurrence) and re-ran: prepatch_no371.py -> 'Verification successful', exit 0 in 16.8s.

So the clause is genuinely load-bearing -- removing it lets the PRE-patch impl pass -- and a spec that omitted it would be unfaithful (it could not distinguish gold from prepatch at all). It is stated as desired behaviour ('the returned expression's final-flag equals the requested final-flag'), which is precisely the corrected outcome, in abstract vocabulary; it does NOT say which attribute to assign, where, or that the wrapper previously failed to carry it. A solver reading it learns the required end state -- which is what a spec IS -- not the edit's location or identifier.

MEASUREMENT 5 -- reviewer-directed / steering check. leakage.reviewer_directed() -> [] on refinement.md, mapping.md AND verdict.md. Full grep across the bundle's .md and .py for 'leakage panel', 'attacker (3)', 'the honest verdict', 'you should submit', 'record this as', 'NO-LEAKAGE' as an instruction, 'relaxed_leakage' -> no hits outside verdict.md's own historical gate records. The single 'auditor' mention (refinement.md:219) describes a rival variant's re-resolution behaviour, not my recording. NO FILE IN THIS BUNDLE ADDRESSES ME or tells me how to record. Nothing to report as steering.

MEASUREMENT 6 -- other consumer-visible surface. In spec modes the consumer also receives meta.json's `modeled_functions` (eval/dataset.py, MODES_WITH_SPEC). That entry DOES name is_summary, Coalesce, aggregates.py:50-68 and exact line numbers -- but that is the deliberate localization channel the mode ships (the same mode also ships changed_files/localization), not the spec view, and it is outside this facet's scope. Flagging for the record, not as a leak: my verdict is on the spec-view projection, which is what this gate screens. I also confirmed adapter.spec_view's hard guard (refuses to expose a view where ELISION_IMPL is absent) is what gates exposure, and that same-spec tooling agrees the region split is intact (`adversary same-spec` on an unmodified copy -> exit 0, 'SAME'); markers.same_spec(model.py, model_prepatch.py) -> True, i.e. the twins differ in impl only, so the spec region I judged is the frozen one.

OUT-OF-FACET CONTEXT, deliberately NOT folded into this verdict. (a) G-PANEL-2 (faithfulness) is a recorded FAIL on this cell concerning the condition/parts_usable equality leg. That is a different facet's finding; re-labelling an unfaithfulness finding as leakage would invent a leak, so it does not move this verdict. (b) meta.json's TOP-LEVEL region_hashes block is STALE and I re-measured this rather than repeat a prior note: markers.region_hashes(model.py) gives pre-conditions 3494df38..., post-conditions 5afcc2b7..., impl ae626703..., spec_view 548c7c76..., which match G-HYGIENE's recorded data block exactly, while the top-level block still carries an older generation (c07dc494/301d6b3d/330c7136/4147ee67). Note also that the prior G-PANEL-3 note in verdict.md records a DIFFERENT set of recomputed hashes (1c2cd646/a57eb926/27282dbf/b3583eaa) and a different model sha (705af70b...), i.e. it judged an earlier revision of model.py than the current acecaa8a... bytes -- which is exactly why I re-derived everything above from scratch instead of inheriting it. Ledger-hygiene issue for the gate owner; not a leak.

**CONCLUSION:** the spec view reproduces no gold-patch line, no patched path or module, no patched symbol, and no repo identifier; all edit narration is confined to the elided impl region; and the single discriminating clause is measured load-bearing (prepatch verifies without it, fails on it) and phrased as required behaviour within the envelope the public problem_statement already establishes. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
