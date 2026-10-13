# P2 adversarial audit — django__django-13212

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_20.py`, `atk_21.py`, `atk_vacuity.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_11.py`, `atk_12.py`, `atk_16.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 22 same-spec attacks were run; 19 were REJECTED by the spec, and all 3 CANDIDATEs (atk_11, atk_12, atk_16 — share spec AND verify) had their faithful refined patches materialized at base_commit f4e93919 and RUN through the official harness: ALL THREE RESOLVED (FAIL_TO_PASS 5/5, PASS_TO_PASS 2/2, no PASS_TO_FAIL, patch_successfully_applied=true, 1 attempt each, not flaky). No verifying wrong impl's faithful patch fails to resolve, so verify=>correct is not falsified on this bundle.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,8 +100,9 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    # PREPATCH A: `raise ValidationError(self.message, code=self.code)` --
+    # no params argument at all, so the value placeholder is never bound.
     params = {}  # type: Dict[int, PSeq[int]]
-    params[placeholder_value()] = ToSeq(value)
     return params
     # impl-end
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -133,9 +133,10 @@
                 k == placeholder_limit() or k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    # PREPATCH B: params={'max': self.max_digits} only -- the value binding the
+    # patch adds is missing.
     params = {}  # type: Dict[int, PSeq[int]]
     params[placeholder_limit()] = ToSeq(limit)
-    params[placeholder_value()] = ToSeq(value)
     return params
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -166,8 +166,10 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    # The not-finite screen that would intercept with a parameter-less rejection
-    # is gone: a not-finite candidate flows through to the same bare rejection
-    # as the finite-but-invalid one, so both produce the value-binding mapping.
+    # PREPATCH C: DecimalField.validate's duplicate not-finite screen is STILL
+    # there and short-circuits with a parameter-less rejection.
+    if not finite:
+        empty = {}  # type: Dict[int, PSeq[int]]
+        return empty
     return build_invalid_params(value)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,8 +100,11 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    # PARTIAL DOMAIN: params={'value': value} only when the input is non-empty;
+    # the empty input still gets the paramless map.
     params = {}  # type: Dict[int, PSeq[int]]
-    params[placeholder_value()] = ToSeq(value)
+    if len(value) > 0:
+        params[placeholder_value()] = ToSeq(value)
     return params
     # impl-end
 
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -133,9 +133,11 @@
                 k == placeholder_limit() or k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    # SWAPPED: params={'max': value, 'value': self.max_digits} -- both keys
+    # present, both bound to the wrong operand.
     params = {}  # type: Dict[int, PSeq[int]]
-    params[placeholder_limit()] = ToSeq(limit)
-    params[placeholder_value()] = ToSeq(value)
+    params[placeholder_limit()] = ToSeq(value)
+    params[placeholder_value()] = ToSeq(limit)
     return params
     # impl-end
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -166,8 +166,11 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    # The not-finite screen that would intercept with a parameter-less rejection
-    # is gone: a not-finite candidate flows through to the same bare rejection
-    # as the finite-but-invalid one, so both produce the value-binding mapping.
+    # CONTROL-FLOW EFFECT: the not-finite screen is retained and routed to the
+    # bound-limit rejection shape, so the not-finite report carries a spurious
+    # extra binding alongside the value.
+    if not finite:
+        bogus = []  # type: List[int]
+        return build_limit_params(value, bogus)
     return build_invalid_params(value)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -166,8 +166,7 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    # The not-finite screen that would intercept with a parameter-less rejection
-    # is gone: a not-finite candidate flows through to the same bare rejection
-    # as the finite-but-invalid one, so both produce the value-binding mapping.
-    return build_invalid_params(value)
+    # UNGROUNDED ORACLE ECHO: assert the answer by calling the specified
+    # function itself -- establishes nothing.
+    return decimal_reject_params(finite, value)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,8 +100,14 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    # DIVERGENCE: the binding is made but control never returns, so no error is
+    # ever reported at all.
     params = {}  # type: Dict[int, PSeq[int]]
     params[placeholder_value()] = ToSeq(value)
+    spin = True
+    while spin:
+        Invariant(spin)
+        spin = True
     return params
     # impl-end
 
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,8 +100,11 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    # VALUE CORRUPTION: params={'value': ''} -- the placeholder is bound, but to
+    # the empty string instead of the offending input.
     params = {}  # type: Dict[int, PSeq[int]]
-    params[placeholder_value()] = ToSeq(value)
+    blank = []  # type: List[int]
+    params[placeholder_value()] = ToSeq(blank)
     return params
     # impl-end
 
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,9 +100,8 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    params = {}  # type: Dict[int, PSeq[int]]
-    params[placeholder_value()] = ToSeq(value)
-    return params
+    # EXCEPTIONAL EXIT: no mapping is produced at all.
+    raise Exception()
     # impl-end
 
 
```

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -166,8 +166,12 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    # The not-finite screen that would intercept with a parameter-less rejection
-    # is gone: a not-finite candidate flows through to the same bare rejection
-    # as the finite-but-invalid one, so both produce the value-binding mapping.
+    # C3 ATTACK: the duplicate not-finite screen is RETAINED (the deletion
+    # refinement.md C3 claims to model is NOT performed); it is merely fixed to
+    # publish the value binding itself.
+    if not finite:
+        nf = {}  # type: Dict[int, PSeq[int]]
+        nf[placeholder_value()] = ToSeq(value)
+        return nf
     return build_invalid_params(value)
     # impl-end
```

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -133,9 +133,12 @@
                 k == placeholder_limit() or k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    # B2/B3 ATTACK: the params dict is written value-first -- the pre-existing
+    # limit binding is added AFTER the value binding, inverting the patch's
+    # "keep the existing entry, add 'value'" order.
     params = {}  # type: Dict[int, PSeq[int]]
+    params[placeholder_value()] = ToSeq(value)
     params[placeholder_limit()] = ToSeq(limit)
-    params[placeholder_value()] = ToSeq(value)
     return params
     # impl-end
 
@@ -166,8 +169,9 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    # The not-finite screen that would intercept with a parameter-less rejection
-    # is gone: a not-finite candidate flows through to the same bare rejection
-    # as the finite-but-invalid one, so both produce the value-binding mapping.
-    return build_invalid_params(value)
+    # C4 ATTACK: the decimal rejection does NOT delegate to site A; it builds
+    # its own mapping inline.
+    params = {}  # type: Dict[int, PSeq[int]]
+    params[placeholder_value()] = ToSeq(value)
+    return params
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,9 +100,9 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    params = {}  # type: Dict[int, PSeq[int]]
-    params[placeholder_value()] = ToSeq(value)
-    return params
+    # DELEGATION INVERSION: site A produces its map by calling the decimal
+    # rejection path, inverting the callee direction C4 pins.
+    return decimal_reject_params(True, value)
     # impl-end
 
 
@@ -166,8 +166,7 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    # The not-finite screen that would intercept with a parameter-less rejection
-    # is gone: a not-finite candidate flows through to the same bare rejection
-    # as the finite-but-invalid one, so both produce the value-binding mapping.
-    return build_invalid_params(value)
+    params = {}  # type: Dict[int, PSeq[int]]
+    params[placeholder_value()] = ToSeq(value)
+    return params
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -166,8 +166,13 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    # The not-finite screen that would intercept with a parameter-less rejection
-    # is gone: a not-finite candidate flows through to the same bare rejection
-    # as the finite-but-invalid one, so both produce the value-binding mapping.
-    return build_invalid_params(value)
+    # PARTIAL DOMAIN (finite branch): the not-finite class is reported properly,
+    # but the finite-but-invalid class binds the empty string instead of the
+    # offending input.
+    if not finite:
+        return build_invalid_params(value)
+    blank = []  # type: List[int]
+    params = {}  # type: Dict[int, PSeq[int]]
+    params[placeholder_value()] = ToSeq(blank)
+    return params
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,8 +100,11 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    # SPURIOUS EXTRA BINDING: params={'value': value, 'max': value} at a bare
+    # rejection site that publishes no limit at all.
     params = {}  # type: Dict[int, PSeq[int]]
     params[placeholder_value()] = ToSeq(value)
+    params[placeholder_limit()] = ToSeq(value)
     return params
     # impl-end
 
```

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -166,8 +166,12 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    # The not-finite screen that would intercept with a parameter-less rejection
-    # is gone: a not-finite candidate flows through to the same bare rejection
-    # as the finite-but-invalid one, so both produce the value-binding mapping.
+    # POLARITY: the retained screen is guarded on the POSITIVE finiteness
+    # predicate instead of its negation; both classes still produce the bare
+    # value-binding map.
+    if finite:
+        fb = {}  # type: Dict[int, PSeq[int]]
+        fb[placeholder_value()] = ToSeq(value)
+        return fb
     return build_invalid_params(value)
     # impl-end
```

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -133,8 +133,11 @@
                 k == placeholder_limit() or k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    # PARTIAL DOMAIN (B2): the pre-existing limit binding is preserved only when
+    # its string form is non-empty; otherwise it is silently dropped.
     params = {}  # type: Dict[int, PSeq[int]]
-    params[placeholder_limit()] = ToSeq(limit)
+    if len(limit) > 0:
+        params[placeholder_limit()] = ToSeq(limit)
     params[placeholder_value()] = ToSeq(value)
     return params
     # impl-end
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,6 +100,8 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    # SIDE EFFECT: the rejection mutates the offending input before binding it.
+    value.append(65)
     params = {}  # type: Dict[int, PSeq[int]]
     params[placeholder_value()] = ToSeq(value)
     return params
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -133,10 +133,9 @@
                 k == placeholder_limit() or k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    params = {}  # type: Dict[int, PSeq[int]]
-    params[placeholder_limit()] = ToSeq(limit)
-    params[placeholder_value()] = ToSeq(value)
-    return params
+    # UNGROUNDED ORACLE ECHO (B leg): assert the bound-limit map by calling the
+    # specified function itself.
+    return build_limit_params(value, limit)
     # impl-end
 
 
```

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -166,8 +166,7 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    # The not-finite screen that would intercept with a parameter-less rejection
-    # is gone: a not-finite candidate flows through to the same bare rejection
-    # as the finite-but-invalid one, so both produce the value-binding mapping.
-    return build_invalid_params(value)
+    # UNCONDITIONAL SPURIOUS BINDING: every rejected decimal candidate is routed
+    # to the bound-limit shape, so the report always carries a bogus limit.
+    return build_limit_params(value, value)
     # impl-end
```

Attack 21 — `atk_21.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,9 +100,8 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    params = {}  # type: Dict[int, PSeq[int]]
-    params[placeholder_value()] = ToSeq(value)
-    return params
+    # CROSS-LEG SUBSTITUTION: the bare rejection publishes the bound-limit shape.
+    return build_limit_params(value, value)
     # impl-end
 
 
```

Attack 22 — `atk_vacuity.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -100,6 +100,7 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    Assert(False)
     params = {}  # type: Dict[int, PSeq[int]]
     params[placeholder_value()] = ToSeq(value)
     return params
@@ -133,6 +134,7 @@
                 k == placeholder_limit() or k == placeholder_value()))))
     # post-conditions-end
     # impl-start
+    Assert(False)
     params = {}  # type: Dict[int, PSeq[int]]
     params[placeholder_limit()] = ToSeq(limit)
     params[placeholder_value()] = ToSeq(value)
@@ -166,8 +168,6 @@
         Implies(k in Result(), k == placeholder_value()))))
     # post-conditions-end
     # impl-start
-    # The not-finite screen that would intercept with a parameter-less rejection
-    # is gone: a not-finite candidate flows through to the same bare rejection
-    # as the finite-but-invalid one, so both produce the value-binding mapping.
+    Assert(False)
     return build_invalid_params(value)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-13212/nagini. 22 attacks, all confirmed same-spec (`adversary same-spec` => exit 0 "SAME" on every one, plus pos_control). Positive control (byte-identical copy of model.py) VERIFIED 13.4s. VACUITY CONTROL: atk_vacuity.py = correct impl + `Assert(False)` in all three impl regions => REJECTED, so the preconditions are not contradictory and every rejection below is a real measurement. Verdict SOUND.

Command for every attack: `python -m swebench_unified.adversary weakness nagini django__django-13212 <path>` (raw outputs kept <name>.out). Resolves via swebench_unified.harness.run_resolve (raw outputs at res_<name>.out). Attacks were scheduled 3-at-a-time as detached background jobs per the parallelism instruction; pass criteria unchanged. Every one of the 22 weakness runs returned a definitive exit 0/2 — no timeouts, no crashes, nothing inconclusive.

REJECTED (exit 2, "attack does not verify — the spec rejected this impl") — 19:
- atk_1  PREPATCH BUG A: bare rejection publishes no params at all (pre-patch `raise ValidationError(self.message, code=self.code)`). REJECTED.
- atk_2  PREPATCH BUG B: bound-limit rejection keeps only `{'max': ...}`, never adds value. REJECTED.
- atk_3  PREPATCH BUG C: duplicate not-finite screen retained, short-circuits paramless (`if not finite: return {}`). REJECTED.
- atk_4  PARTIAL DOMAIN: binds value only when `len(value) > 0`; drops it for the empty input. REJECTED.
- atk_5  BOUNDARY/SWAPPED: both keys present but bound to the wrong operands ({'max': value, 'value': limit}). REJECTED.
- atk_6  CONTROL-FLOW EFFECT: not-finite branch retained but routed to the bound-limit shape, smuggling a spurious 'max'. REJECTED.
- atk_7  UNGROUNDED ORACLE ECHO: `return decimal_reject_params(finite, value)` self-call. REJECTED (MustTerminate(3) + postconditions kill the echo).
- atk_8  DIVERGENCE: value bound but the mapping never produced (`while spin: Invariant(spin)`). REJECTED — MustTerminate is at the method level.
- atk_9  VALUE CORRUPTION: value placeholder bound to the empty PSeq instead of the input. REJECTED.
- atk_10 EXCEPTIONAL EXIT: bare rejection raises instead of producing the mapping. REJECTED.
- atk_13 DELEGATION INVERSION: site A produces its map by calling decimal_reject_params(True, value), inverting C4's callee direction. REJECTED.
- atk_14 PARTIAL DOMAIN on the finite branch (exactly what a finiteness-GUARDED closure would admit). REJECTED — confirms refinement.md §C's deliberately UNCONDITIONAL closure is load-bearing as documented.
- atk_15 SPURIOUS EXTRA BINDING on the bare rejection itself ({'value':..., 'max':...}). REJECTED.
- atk_17 PARTIAL DOMAIN on the PRESERVED limit binding (B2): limit dropped when its string form is empty. REJECTED.
- atk_18 SIDE EFFECT: the rejection mutates the offending input (`value.append(65)`) before binding it. REJECTED.
- atk_19 UNGROUNDED ORACLE ECHO on the B leg (`return build_limit_params(value, limit)`). REJECTED.
- atk_20 UNCONDITIONAL spurious binding: every decimal candidate routed to the bound-limit shape. REJECTED.
- atk_21 CROSS-LEG SUBSTITUTION: bare site publishes the bound-limit shape. REJECTED.
- atk_vacuity see above. REJECTED.

CANDIDATEs (share spec AND verify) — faithful patches materialized in a git worktree at base_commit f4e93919 and RUN through the official harness. ALL THREE RESOLVE, so none is a break:
- atk_11 (verifies 13.5s). The sharpest question in this bundle, aimed straight at the C-leg control-flow correspondence: refinement.md C3 tags the ABSENCE of the `if not finite` early return as BEING the gold DELETION of DecimalField.validate, but the spec only constrains the produced MAPPING, so an impl that KEEPS the screen and merely fixes it to bind value also verifies. Faithful patch = gold + re-inserted DecimalField.validate whose not-finite raise carries params={'value': value} (fix the screen instead of deleting it). run_resolve => RESOLVED: True, F2P 5/5 (incl. test_value_placeholder_with_decimal_field, the 'NaN' case), P2P 2/2, no PASS_TO_FAIL. So 'delete the screen' and 'keep the screen but bind value' are observationally EQUAL on the tested inputs; the model's mapping-level abstraction captures the only observable consequence. C3's R/I tag is behaviourally sound. NOT a break.
- atk_12 (verifies 17.2s). Targets the B2/B3 construction ORDER and C4's delegation: bound-limit map built value-first, and the decimal rejection builds its map inline instead of delegating to build_invalid_params. Faithful patch = gold with the three magnitude params dicts written {'value':..., 'max':...}. run_resolve => RESOLVED: True, F2P 5/5, P2P 2/2. Dict-insertion order is not observable through %-interpolation, so the I-tags on A2/B2/B3 are order-insensitive as claimed. NOT a break.
- atk_16 (verifies 16.6s). Polarity of the `finite` carrier (C1): the retained screen is guarded on the POSITIVE predicate; both classes still produce the bare value-binding map. Faithful patch = gold with DecimalField.validate retained but inert on BOTH polarities, so every candidate falls through to DecimalValidator's value-binding raise. run_resolve => RESOLVED: True, F2P 5/5, P2P 2/2. NOT a break.

A-LEG AUDIT (the assigned focus). meta.json records `axioms: []` and exactly ONE deep_model_reference of kind A-reference; `grep -c ContractOnly model.py` = 0 (the axioms region is a comment only). So there is NO A-consumed leg and NO kind-3. Leg-kind tally straight from refinement.md's tables: A1=R, A2=R+I, A3=R, B1=R, B2=R+I, B3=R+I, B4=R, C1=R, C2=R, C3=R/I, C4=R+I; §D declares the single A-reference (the unchanged %-interpolation mechanism). LEG-KIND AUDIT: PASS — every leg is R / I / A-reference, no kind-3.

I re-derived the A-reference INDEPENDENTLY in plain Python rather than trusting axiom_check.py (27/27 assertions PASS): for a template that is exactly '%(NAME)s', rendering == str(params['NAME']) iff 'NAME' in params — checked on the bare map across all F2P shapes ('-42.5', '你 好', 'a\x00b', 'myfile.txt', 'NaN', 'Infinity', ''), on the two-key limit map (BOTH %(value)s and %(max)s still render, so the limit binding really is preserved), key-order insensitivity (the atk_12 leg), extra-key harmlessness, and the CONVERSE on all three pre-patch map shapes ({}, {'max':2}, the fileext 2-key map) which raise KeyError exactly as modelled. Confirmed against the real base_commit source: exceptions.py:166-175 `__iter__` does `message %= error.params` guarded by `if error.params`, and fields.py:130-142 `run_validators` overrides `e.message` keyed on `e.code` while PRESERVING `e.params` — exactly what mapping.md §§2,3 claim. A-REFERENCE CORRESPONDENCE: PASS.

MODEL<->PATCH CORRESPONDENCE, probed empirically on the gold-patched worktree (not just read):
- A-leg: every reachable bound bare-rejection site (validate_integer, EmailValidator, validate_slug/unicode_slug, validate_ipv4/6/46_address, comma_separated_integer_list, URLValidator x3, ProhibitNullCharactersValidator, RegexValidator) produces params key set EXACTLY ['value'] with params['value'] IS the offending input. PASS.
- B-leg: DecimalValidator(2,1) on Decimal('123')/'0.12'/'12' gives codes max_digits/max_decimal_places/max_whole_digits with keys EXACTLY ['max','value'], limit PRESERVED and value ADDED. PASS.
- C-leg: every not-finite shape (NaN, -NaN, sNaN, -sNaN, Infinity, -Infinity) hits validators.py:441 with code='invalid' and keys EXACTLY ['value'] bound to the offending Decimal (compared by identity — NaN != NaN, so an == check here is a self-inflicted false negative). PASS.
- C1 carrier equivalence: `exponent in {'F','n','N'}` is the EXACT complement of `is_finite()` over 4022 Decimal samples (all NaN/sNaN/Infinity shapes + randomized magnitudes incl. 1E+/-999999999 and 50-digit values) — 0 mismatches. And over 609 finite samples, ZERO reach the site-441 raise, so the finite branch is outside the modeled callee's real domain: the unconditional closure is a strengthening over a don't-care that gold vacuously satisfies (and atk_14 shows it is load-bearing against a guarded-closure evasion).
- Scope, not drift: FileExtensionValidator really produces THREE keys ['allowed_extensions','extension','value'] and BaseValidator (MaxLength/MinLength, UNTOUCHED by the patch) produces ['limit_value','show_value','value']. Neither contradicts build_limit_params: mapping.md binds it to the three magnitude raises and hedges FileExtensionValidator as only 'structural'; BaseValidator is not a bound site at all. The 2-arg signature cannot express a 3-key site.

ONE CORRESPONDENCE COVERAGE PROBE worth recording (a documentation-scope observation, NOT a spec break; not a verifying wrong impl, so not submitted as an attack): probe_nocode = gold with ONLY `code='invalid'` dropped at the DecimalValidator line-441 raise (params={'value': value} KEPT). run_resolve => RESOLVED: False, F2P 3/5 with test_value_placeholder_with_decimal_field failing ({'field': ['Enter a number.']} != {'field': ['NaN']}). The model carries no carrier for the `code=` kwarg, and the params binding alone is not sufficient end-to-end — without a code the template override never installs.

This is NOT a hole in verify=>correct, because the refinement map does not license dropping code=: mapping.md §§1-2 binds the model to the params dict only and §§2-3 state the override is 'keyed by e.code' with params preserved, so a faithful refinement carries code= unchanged (gold does; all three CANDIDATE patches do, and all three resolve). The map would read tighter if A3/B4 named the code= kwarg as a preserved component alongside params=. Same-shaped result for probe_polarity (the aggressive polarity reading, screen raising on the POSITIVE predicate): RESOLVED False, decimal_field fails — i.e. the C-leg's finiteness polarity IS oracle-sensed once the screen actually intercepts, which is why atk_16's inert-screen refinement is the faithful one.

MEASUREMENT CAVEAT I chased down rather than reporting as-is: both probes' harness reports listed test_value_placeholder_with_file_field in F2P `failure` alongside decimal_field, even though neither probe touches the FileExtensionValidator site. Preserving the container log (run_evaluation test_output.txt) showed file_field actually reported `... ok` — the swebench log parser mis-attributes it because decimal_field's verbose line has no trailing status before the next test name. Confirmed independently: per-test local runs against the worktree give file_field OK under both probes, and gold itself resolves 5/5 through the same harness path (control run). This artifact affects only the two non-resolving PROBES' failure lists, never a CANDIDATE verdict — all three CANDIDATE patches came back cleanly RESOLVED: True with empty failure lists.

HYGIENE: the bundle was never modified (git status clean for this instance's paths). The scratch git worktree was removed and pruned, and the one deliberately-kept run_evaluation log dir was deleted.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_20.py`, `atk_21.py`, `atk_vacuity.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_11.py`, `atk_12.py`, `atk_16.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. 22 same-spec attacks were run; 19 were REJECTED by the spec, and all 3 CANDIDATEs (atk_11, atk_12, atk_16 — share spec AND verify) had their faithful refined patches materialized at base_commit f4e93919 and RUN through the official harness: ALL THREE RESOLVED (FAIL_TO_PASS 5/5, PASS_TO_PASS 2/2, no PASS_TO_FAIL, patch_successfully_applied=true, 1 attempt each, not flaky). No verifying wrong impl's faithful patch fails to resolve, so verify=>correct is not falsified on this bundle.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 22 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good)

Attack 21 — `atk_21.py` → rejected (same spec, does not verify — good)

Attack 22 — `atk_vacuity.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for django__django-13212/nagini. 22 attacks, all confirmed same-spec (`adversary same-spec` => exit 0 "SAME" on every one, plus pos_control). Positive control (byte-identical copy of model.py) VERIFIED 13.4s. VACUITY CONTROL: atk_vacuity.py = correct impl + `Assert(False)` in all three impl regions => REJECTED, so the preconditions are not contradictory and every rejection below is a real measurement. Verdict SOUND.

Command for every attack: `python -m swebench_unified.adversary weakness nagini django__django-13212 <path>` (raw outputs kept <name>.out). Resolves via swebench_unified.harness.run_resolve (raw outputs at res_<name>.out). Attacks were scheduled 3-at-a-time as detached background jobs per the parallelism instruction; pass criteria unchanged. Every one of the 22 weakness runs returned a definitive exit 0/2 — no timeouts, no crashes, nothing inconclusive.

REJECTED (exit 2, "attack does not verify — the spec rejected this impl") — 19:
- atk_1  PREPATCH BUG A: bare rejection publishes no params at all (pre-patch `raise ValidationError(self.message, code=self.code)`). REJECTED.
- atk_2  PREPATCH BUG B: bound-limit rejection keeps only `{'max': ...}`, never adds value. REJECTED.
- atk_3  PREPATCH BUG C: duplicate not-finite screen retained, short-circuits paramless (`if not finite: return {}`). REJECTED.
- atk_4  PARTIAL DOMAIN: binds value only when `len(value) > 0`; drops it for the empty input. REJECTED.
- atk_5  BOUNDARY/SWAPPED: both keys present but bound to the wrong operands ({'max': value, 'value': limit}). REJECTED.
- atk_6  CONTROL-FLOW EFFECT: not-finite branch retained but routed to the bound-limit shape, smuggling a spurious 'max'. REJECTED.
- atk_7  UNGROUNDED ORACLE ECHO: `return decimal_reject_params(finite, value)` self-call. REJECTED (MustTerminate(3) + postconditions kill the echo).
- atk_8  DIVERGENCE: value bound but the mapping never produced (`while spin: Invariant(spin)`). REJECTED — MustTerminate is at the method level.
- atk_9  VALUE CORRUPTION: value placeholder bound to the empty PSeq instead of the input. REJECTED.
- atk_10 EXCEPTIONAL EXIT: bare rejection raises instead of producing the mapping. REJECTED.
- atk_13 DELEGATION INVERSION: site A produces its map by calling decimal_reject_params(True, value), inverting C4's callee direction. REJECTED.
- atk_14 PARTIAL DOMAIN on the finite branch (exactly what a finiteness-GUARDED closure would admit). REJECTED — confirms refinement.md §C's deliberately UNCONDITIONAL closure is load-bearing as documented.
- atk_15 SPURIOUS EXTRA BINDING on the bare rejection itself ({'value':..., 'max':...}). REJECTED.
- atk_17 PARTIAL DOMAIN on the PRESERVED limit binding (B2): limit dropped when its string form is empty. REJECTED.
- atk_18 SIDE EFFECT: the rejection mutates the offending input (`value.append(65)`) before binding it. REJECTED.
- atk_19 UNGROUNDED ORACLE ECHO on the B leg (`return build_limit_params(value, limit)`). REJECTED.
- atk_20 UNCONDITIONAL spurious binding: every decimal candidate routed to the bound-limit shape. REJECTED.
- atk_21 CROSS-LEG SUBSTITUTION: bare site publishes the bound-limit shape. REJECTED.
- atk_vacuity see above. REJECTED.

CANDIDATEs (share spec AND verify) — faithful patches materialized in a git worktree at base_commit f4e93919 and RUN through the official harness. ALL THREE RESOLVE, so none is a break:
- atk_11 (verifies 13.5s). The sharpest question in this bundle, aimed straight at the C-leg control-flow correspondence: refinement.md C3 tags the ABSENCE of the `if not finite` early return as BEING the gold DELETION of DecimalField.validate, but the spec only constrains the produced MAPPING, so an impl that KEEPS the screen and merely fixes it to bind value also verifies. Faithful patch = gold + re-inserted DecimalField.validate whose not-finite raise carries params={'value': value} (fix the screen instead of deleting it). run_resolve => RESOLVED: True, F2P 5/5 (incl. test_value_placeholder_with_decimal_field, the 'NaN' case), P2P 2/2, no PASS_TO_FAIL. So 'delete the screen' and 'keep the screen but bind value' are observationally EQUAL on the tested inputs; the model's mapping-level abstraction captures the only observable consequence. C3's R/I tag is behaviourally sound. NOT a break.
- atk_12 (verifies 17.2s). Targets the B2/B3 construction ORDER and C4's delegation: bound-limit map built value-first, and the decimal rejection builds its map inline instead of delegating to build_invalid_params. Faithful patch = gold with the three magnitude params dicts written {'value':..., 'max':...}. run_resolve => RESOLVED: True, F2P 5/5, P2P 2/2. Dict-insertion order is not observable through %-interpolation, so the I-tags on A2/B2/B3 are order-insensitive as claimed. NOT a break.
- atk_16 (verifies 16.6s). Polarity of the `finite` carrier (C1): the retained screen is guarded on the POSITIVE predicate; both classes still produce the bare value-binding map. Faithful patch = gold with DecimalField.validate retained but inert on BOTH polarities, so every candidate falls through to DecimalValidator's value-binding raise. run_resolve => RESOLVED: True, F2P 5/5, P2P 2/2. NOT a break.

A-LEG AUDIT (the assigned focus). meta.json records `axioms: []` and exactly ONE deep_model_reference of kind A-reference; `grep -c ContractOnly model.py` = 0 (the axioms region is a comment only). So there is NO A-consumed leg and NO kind-3. Leg-kind tally straight from refinement.md's tables: A1=R, A2=R+I, A3=R, B1=R, B2=R+I, B3=R+I, B4=R, C1=R, C2=R, C3=R/I, C4=R+I; §D declares the single A-reference (the unchanged %-interpolation mechanism). LEG-KIND AUDIT: PASS — every leg is R / I / A-reference, no kind-3.

I re-derived the A-reference INDEPENDENTLY in plain Python rather than trusting axiom_check.py (27/27 assertions PASS): for a template that is exactly '%(NAME)s', rendering == str(params['NAME']) iff 'NAME' in params — checked on the bare map across all F2P shapes ('-42.5', '你 好', 'a\x00b', 'myfile.txt', 'NaN', 'Infinity', ''), on the two-key limit map (BOTH %(value)s and %(max)s still render, so the limit binding really is preserved), key-order insensitivity (the atk_12 leg), extra-key harmlessness, and the CONVERSE on all three pre-patch map shapes ({}, {'max':2}, the fileext 2-key map) which raise KeyError exactly as modelled. Confirmed against the real base_commit source: exceptions.py:166-175 `__iter__` does `message %= error.params` guarded by `if error.params`, and fields.py:130-142 `run_validators` overrides `e.message` keyed on `e.code` while PRESERVING `e.params` — exactly what mapping.md §§2,3 claim. A-REFERENCE CORRESPONDENCE: PASS.

MODEL<->PATCH CORRESPONDENCE, probed empirically on the gold-patched worktree (not just read):
- A-leg: every reachable bound bare-rejection site (validate_integer, EmailValidator, validate_slug/unicode_slug, validate_ipv4/6/46_address, comma_separated_integer_list, URLValidator x3, ProhibitNullCharactersValidator, RegexValidator) produces params key set EXACTLY ['value'] with params['value'] IS the offending input. PASS.
- B-leg: DecimalValidator(2,1) on Decimal('123')/'0.12'/'12' gives codes max_digits/max_decimal_places/max_whole_digits with keys EXACTLY ['max','value'], limit PRESERVED and value ADDED. PASS.
- C-leg: every not-finite shape (NaN, -NaN, sNaN, -sNaN, Infinity, -Infinity) hits validators.py:441 with code='invalid' and keys EXACTLY ['value'] bound to the offending Decimal (compared by identity — NaN != NaN, so an == check here is a self-inflicted false negative). PASS.
- C1 carrier equivalence: `exponent in {'F','n','N'}` is the EXACT complement of `is_finite()` over 4022 Decimal samples (all NaN/sNaN/Infinity shapes + randomized magnitudes incl. 1E+/-999999999 and 50-digit values) — 0 mismatches. And over 609 finite samples, ZERO reach the site-441 raise, so the finite branch is outside the modeled callee's real domain: the unconditional closure is a strengthening over a don't-care that gold vacuously satisfies (and atk_14 shows it is load-bearing against a guarded-closure evasion).
- Scope, not drift: FileExtensionValidator really produces THREE keys ['allowed_extensions','extension','value'] and BaseValidator (MaxLength/MinLength, UNTOUCHED by the patch) produces ['limit_value','show_value','value']. Neither contradicts build_limit_params: mapping.md binds it to the three magnitude raises and hedges FileExtensionValidator as only 'structural'; BaseValidator is not a bound site at all. The 2-arg signature cannot express a 3-key site.

ONE CORRESPONDENCE COVERAGE PROBE worth recording (a documentation-scope observation, NOT a spec break; not a verifying wrong impl, so not submitted as an attack): probe_nocode = gold with ONLY `code='invalid'` dropped at the DecimalValidator line-441 raise (params={'value': value} KEPT). run_resolve => RESOLVED: False, F2P 3/5 with test_value_placeholder_with_decimal_field failing ({'field': ['Enter a number.']} != {'field': ['NaN']}). The model carries no carrier for the `code=` kwarg, and the params binding alone is not sufficient end-to-end — without a code the template override never installs.

This is NOT a hole in verify=>correct, because the refinement map does not license dropping code=: mapping.md §§1-2 binds the model to the params dict only and §§2-3 state the override is 'keyed by e.code' with params preserved, so a faithful refinement carries code= unchanged (gold does; all three CANDIDATE patches do, and all three resolve). The map would read tighter if A3/B4 named the code= kwarg as a preserved component alongside params=. Same-shaped result for probe_polarity (the aggressive polarity reading, screen raising on the POSITIVE predicate): RESOLVED False, decimal_field fails — i.e. the C-leg's finiteness polarity IS oracle-sensed once the screen actually intercepts, which is why atk_16's inert-screen refinement is the faithful one.

MEASUREMENT CAVEAT I chased down rather than reporting as-is: both probes' harness reports listed test_value_placeholder_with_file_field in F2P `failure` alongside decimal_field, even though neither probe touches the FileExtensionValidator site. Preserving the container log (run_evaluation test_output.txt) showed file_field actually reported `... ok` — the swebench log parser mis-attributes it because decimal_field's verbose line has no trailing status before the next test name. Confirmed independently: per-test local runs against the worktree give file_field OK under both probes, and gold itself resolves 5/5 through the same harness path (control run). This artifact affects only the two non-resolving PROBES' failure lists, never a CANDIDATE verdict — all three CANDIDATE patches came back cleanly RESOLVED: True with empty failure lists.

HYGIENE: the bundle was never modified (git status clean for this instance's paths). The scratch git worktree was removed and pruned, and the one deliberately-kept run_evaluation log dir was deleted.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

No diverging input found. Reference = worktree at base_commit f4e93919 with patch.diff APPLIED (fresh worktree from the upstream repository); base commit used only for untouched callees. Bundle not modified (git status clean for this instance).

SPEC INTEGRITY: swebench_unified.markers.same_spec(model.py, rival, nagini backend) == True for all three rivals (model_prepatch, _2, _3), so the spec region is byte-identical across the bundle. Pinned verifier: model.py 'Verification successful' (12.2s). All three rivals FAIL, each on the discriminating clause 'placeholder_value() in Result()' (build_invalid_params:96, build_limit_params:127, decimal_reject_params:159) -- the spec is non-vacuous and senses the change (G-DIFF holds).

(1) build_invalid_params -- CONFIRMED FAITHFUL on all 18 bare-rejection sites mapping.md §1 binds. Observed real e.params in-container for RegexValidator/51, validate_integer, validate_slug, validate_unicode_slug, comma_separated_integer_list, int_list_validator, URL/103 (not-str), URL/107 (scheme), URL/118, URL/142 (netloc>253), email/211, email/216, email/228, ipv4/275, ipv6/280, ipv46/290, ProhibitNullCharacters/553, DecimalValidator/441. Every one produces EXACTLY {'value': value} with str(params['value']) == str(input). The spec's closure (binds nothing but the value placeholder) is exactly right, not too strong.

(2) build_limit_params -- CONFIRMED FAITHFUL on its primary referent, the three DecimalValidator magnitude raises (460/466/473). Swept configs (2,1),(5,2),(3,0) x values '123456','0.12345','12345': every rejection yields EXACTLY {'max','value'}, with 'max' equal to the config-derived limit (max_digits / decimal_places / max_digits-decimal_places per code) and 'value' rendering to str(value). Both the preserved-limit clause and the added-value clause hold; the two-key closure is exact.

(3) decimal_reject_params -- the uniform-in-`finite` closure was my strongest attack candidate, and it SURVIVES. Two independent checks:

  (a) Reachability: fuzzed 300,010 decimals (curated NaN/sNaN/-NaN/Infinity/-Infinity/inf/nan pool + randomized ints, fixed-point, and E-notation exponents in +/-40000), seed 13212. `exponent in {'F','n','N'}` == `not is_finite()` with ZERO mismatches, so no FINITE candidate reaches site 441 through normal control flow -- the finite=True arm is unreachable, hence unfalsifiable by any real input.

  (b) Counterfactual: I forced a finite candidate through the modeled site anyway (as_tuple exponent 'F' but is_finite() True). The real site 441 produced EXACTLY {'value': ...} rendering to the input -- because `raise ValidationError(self.messages['invalid'], code='invalid', params={'value': value})` is UNCONDITIONAL on finiteness. So the unconditional closure faithfully mirrors the modeled raise site rather than over-claiming, and refinement.md §C's justification (a finiteness-guarded closure would admit an impl smuggling a spurious 'max' onto the finite branch) is sound. conformance_check.py:28-32 already discloses this arm as a strengthening with no distinct real observation.

END-TO-END: 4 of 5 F2P tests pass on the patched worktree (test_value_placeholder_with_decimal_field -- incl. the 'NaN' case the fields.py deletion routes -- plus null_character, integer_field, file_field). Raw params confirm the routing: NaN -> code='invalid', {'value': Decimal('NaN')}; '123' -> {'max':2,'value':...}; '0.12' -> {'max':1,...}; '12' -> {'max':1,...}.

TWO NON-DEFECTS I chased and dismissed (recording so they aren't re-raised):
  * FileExtensionValidator/507 real params = {extension, allowed_extensions, value} (3 keys), which a LITERAL reading of build_limit_params' two-key closure would violate. Not a faithfulness break: mapping.md hedges this as 'structurally' analogous (adds 'value' to a dict already carrying other bindings), the primary binding is the three magnitude raises, extension/allowed_extensions are not parameters of build_limit_params so FileExtension is outside the modeled function's domain, and conformance_check.py never compares it against build_limit_params (axiom_check uses it only for end-to-end %(value)s rendering). At most an imprecise mapping note; it cannot reject a correct impl.
  * BaseValidator (Max/MinLength, Max/MinValue) params = {limit_value, show_value, value} (3 keys). Already bound 'value' AT BASE COMMIT (validators.py:341 pre-patch), untouched by patch.diff, and claimed by no model symbol in mapping.md §1. Out of scope.

MEASUREMENT ARTIFACTS, NOT SPEC DEFECTS: test_value_placeholder_with_char_field errors and conformance_check.py aborts on input 'http://[::1:2::3]/' with ValueError from Python 3.10's urllib.parse.`_check_bracketed_host` -- a stdlib hardening postdating this Django 3.2-era base commit, raising where the code expects urlsplit to succeed. That is independent of the patch and of the spec. Separately, `import django` can resolve to an unrelated copy of Django here; every result above was obtained with the import pinned to my own worktree, confirmed by the runner's 'Testing against Django installed ...' line.

CONCLUSION: every clause of the frozen spec is either exactly matched by the real patched callee on all probed inputs, or (the finite=True arm) unreachable AND consistent with the modeled site's unconditional behavior. No input exists on which the modeled function disagrees with its real referent. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

MEASURED ON THE REAL SOLVER-VISIBLE VIEW. Computed the exact projection with markers.spec_view(model.py, get_backend('nagini')) -> sha256 2879d42c5ab91887ff7641c0ef34b437574342a84664ec6a32dbe02e198b0569 (165 lines), and judged only that. Public baseline = the 6-line problem_statement from data/swe_bench_verified/test.jsonl ('Make validators include the provided value in ValidationError' / override an error message with a %(value)s placeholder). hints_text (the PR-discussion thread) was NOT used as a baseline.

NO RELAXATION IS IN PLAY. meta.json has no relaxed_leakage key, there is no RELAXED_LEAKAGE.md (ls confirms), and gates.G-LEAK.status == 'pass' -- this bundle claims plain no-leakage, so I judged it as such. I also ran leakage.reviewer_directed() over every file in the bundle: zero hits, so nothing in it instructs me how to record or which verdict is honest. No bundle-authored steering to report.

MECHANICAL SCREEN: leakage.screen(model.py, nagini, gold_patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. Not an accidental pass -- I checked the substantive branch by hand. _patch_changed_symbols(gold) = {to_python, validate, validate_ipv46_address, validate_ipv4_address}; none is embedded in a spec-view identifier and none is named verbatim in a comment/docstring (the docstring's 'validation'/'validates' cannot satisfy the screen's (?<![\w])validate(?![\w]) anchors, so the clean result is real, not a boundary fluke). No patched path ('django/core/validators.py', 'django/forms/fields.py') or dotted module appears; no diff marker; no gold-patch changed line survives normalized >=8-char matching.

THE PRIOR G-PANEL-3 FAIL HAS BEEN REPAIRED, AND I RE-DERIVED IT RATHER THAN INHERITING IT. meta.json gates.G-PANEL-3 records a fail whose finding was mechanism narration in the docstring/comments -- 'duplicate' screen, 'short-circuited', 'flows through', 'parameter-less', i.e. the fix's non-obvious half (delete the redundant paramless not-finite guard in DecimalField.validate). Term-by-term on the CURRENT view, every one of those is absent: 'duplicate' 0, 'screen' 0, 'short-circuit' 0, 'intercept' 0, 'flows through' 0, 'removed'/'remove' 0, 'paramless'/'parameter-less' 0, 'is_finite' 0, 'DecimalField'/'DecimalValidator' 0, 'validate' 0, 'nan'/'infinit' 0. That narration now lives ONLY inside the impl region of model.py (lines 169-171, 'The not-finite screen ... is gone: ... flows through to'), and I confirmed it does not survive projection ('is gone', 'flows through', 'not-finite screen', 'parameter-less' all absent from the spec view). Consumer-invisible, so not a leak -- flagging it only as a fragility: it becomes leakage the moment the impl marker shifts.

WHAT REMAINS, AND WHY IT IS NOT A LEAK. The residual disclosure beyond the problem_statement is the discriminator's IDENTITY, not the edit: the signature decimal_reject_params(finite: bool, value) plus abstract prose that the produced mapping is UNIFORM in that bit ('decimal' occurs once, 'finite' six times, all in the view). I applied the strip-the-narration control to exactly that facet. Built denarr_gold.py: the finite/decimal PROSE replaced by contentless wording ('A third shape carries an extra boolean input alongside the offending input.

Its produced mapping is shape (1) regardless of that boolean's value.'), and all three finite-mentioning pre/post comments deleted -- signature and Ensures untouched. nagini_verify -> exit 0 (Verification successful, 11.45s), so the de-narrated spec still admits gold. Then denarr_pre3.py = that SAME de-narrated spec + the pre-patch impl lifted verbatim from the bundle's model_prepatch_3.py ('if not finite: return empty'); markers.same_spec(denarr_gold, denarr_pre3) -> True; nagini_verify -> exit 1, 'denarr_pre3.py:146: Postcondition of decimal_reject_params might not hold. Assertion (placeholder_value() in Result()) might not hold.' (Unstripped controls agree: gold exit 0; model_prepatch_3.py exit 1 at the same postcondition, same_spec True.)

So the prose carries no verification weight -- but the CARRIER does. The discrimination is done by the unconditional Ensures pair over a `finite` parameter, and you cannot state 'the mapping is identical for either value of the bit' without the bit being in the signature. Naming that boolean is therefore structurally forced by the facet the spec must cover: F2P includes test_value_placeholder_with_decimal_field, which exercises 'NaN' -> 'invalid' alongside '0.12' -> 'max_decimal_places', so a spec strong enough to reject the pre-patch decimal behaviour must expose the finiteness classification. Crucially, the surviving prose states the DESIRED behaviour (uniform in the bit; neither class contributes a spurious binding) and never the diagnosis -- it does not say a second screen exists, that one class currently drops the value, or that anything must be deleted. Localizing WHICH behaviour is under specification is what a spec does; the gate bans naming the edit, the patched symbols, and the bug->fix mechanism, and none of those survives. Hence NO-LEAKAGE.

SEPARATE BOOKKEEPING DEFECT (not leakage, not my verdict basis): meta.json top-level region_hashes are STALE against the current model.py -- spec_view recorded b52c66f1... vs computed 2879d42c..., and pre-conditions (94846ee1...) and post-conditions (057f3028...) both mismatch; axioms, pure and impl still match. Consistent with a post-fail repair that edited the spec-region comments without refreshing the hashes, and gates.G-HYGIENE carries no region_hashes block of its own (null). Worth a G-HYGIENE re-stamp so the recorded spec_view hash names the artifact consumers actually receive.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
