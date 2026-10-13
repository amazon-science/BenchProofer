# P2 adversarial audit — sympy__sympy-14531

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 18 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_20.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_16.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. Two attacks (atk_5, atk_16) came back CANDIDATE (same-spec AND verifying); per protocol BOTH had their faithful refined patches materialized and RUN through the official harness, and BOTH RESOLVED (run_resolve -> {"resolved": true, "completed": true, "note": "resolved"}). Neither is therefore a wrong impl: each is a semantically-equivalent refactor of the gold delegation, so verify=>correct is upheld on both. The other 18 attacks were rejected by the verifier on their intended clauses.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -402,21 +402,27 @@
     Ensures(ToSeq(reg) == eq_registry(Old(ToSeq(reg)), kl, ul, vl, kr, ur, vr))
     # post-conditions-end
     # impl-start
-    # The previous, narrower obligation of this method (a NAME left slot and a
-    # FRACTIONAL right slot) is the (kl==1, kr==0) instance of the two clauses
-    # above; asserted here so the generalisation is machine-checked to RETAIN it.
-    Assert(Implies(kl == 1 and kr == 0,
-                   eq_text(wrap, kl, ul, vl, kr, ur, vr)
-                   == lit_eq_open() + lit_name(ul) + lit_comma_space()
-                   + render_rational(wrap, ur, vr) + lit_rparen()))
-    Assert(Implies(kl == 1 and kr == 0,
-                   eq_registry(ToSeq(reg), kl, ul, vl, kr, ur, vr)
-                   == registered(ToSeq(reg), ul)))
+    # PRE-PATCH: each operand slot is re-rendered by a DETACHED ambient-default
+    # renderer (its own fresh registry, the default configuration) instead of by
+    # the renderer that owns the compound. The name slots come out with exactly
+    # the right TEXT, so only the registry clause and the wrap-dependent slots
+    # can tell the difference.
     out = []  # type: List[int]
+    fresh = []  # type: List[int]
     out = out + [69, 113, 40]                          # 'Eq('
-    out = out + render_atom(kl, ul, vl, wrap, reg)     # lhs: THIS renderer's
+    if kl == 1:
+        out = out + materialize(lit_name(ul))            # detached: right text, NO registration
+    elif kl == 0:
+        out = out + render_operand(False, ul, vl, fresh)  # detached: ambient default config
+    else:
+        out = out + render_unmodeled(ul, False, fresh)     # detached: a fresh ambient renderer
     out = out + [44, 32]                               # ', '
-    out = out + render_atom(kr, ur, vr, wrap, reg)     # rhs: THIS renderer's
+    if kr == 1:
+        out = out + materialize(lit_name(ur))            # detached: right text, NO registration
+    elif kr == 0:
+        out = out + render_operand(False, ur, vr, fresh)  # detached: ambient default config
+    else:
+        out = out + render_unmodeled(ur, False, fresh)     # detached: a fresh ambient renderer
     out = out + [41]                                   # ')'
     return out
     # impl-end
@@ -449,28 +455,38 @@
                                          kz, uz, vz, k0, u0, v0, ud))
     # post-conditions-end
     # impl-start
-    # The previous, narrower obligation of this method (the one-form, three-slot
-    # template) is the `plus` instance of the two clauses above; asserted here so
-    # the generalisation is machine-checked to RETAIN it.
-    Assert(Implies(plus,
-                   limit_text(wrap, plus, ke, ue, ve, kz, uz, vz, k0, u0, v0, ud)
-                   == lit_limit_open() + atom_text(ke, ue, ve, wrap)
-                   + lit_comma_space() + atom_text(kz, uz, vz, wrap)
-                   + lit_comma_space() + atom_text(k0, u0, v0, wrap)
-                   + lit_rparen()))
+    # PRE-PATCH: as in render_equation, EVERY slot -- the three operands and, in
+    # the second template form, the direction -- is re-rendered by a detached
+    # ambient-default renderer.
     out = []  # type: List[int]
+    fresh = []  # type: List[int]
     out = out + [76, 105, 109, 105, 116, 40]           # 'Limit('
-    out = out + render_atom(ke, ue, ve, wrap, reg)     # body slot
+    if ke == 1:
+        out = out + materialize(lit_name(ue))            # detached: right text, NO registration
+    elif ke == 0:
+        out = out + render_operand(False, ue, ve, fresh)  # detached: ambient default config
+    else:
+        out = out + render_unmodeled(ue, False, fresh)     # detached: a fresh ambient renderer
     out = out + [44, 32]                               # ', '
-    out = out + render_atom(kz, uz, vz, wrap, reg)     # variable slot
+    if kz == 1:
+        out = out + materialize(lit_name(uz))            # detached: right text, NO registration
+    elif kz == 0:
+        out = out + render_operand(False, uz, vz, fresh)  # detached: ambient default config
+    else:
+        out = out + render_unmodeled(uz, False, fresh)     # detached: a fresh ambient renderer
     out = out + [44, 32]                               # ', '
-    out = out + render_atom(k0, u0, v0, wrap, reg)     # point slot
+    if k0 == 1:
+        out = out + materialize(lit_name(u0))            # detached: right text, NO registration
+    elif k0 == 0:
+        out = out + render_operand(False, u0, v0, fresh)  # detached: ambient default config
+    else:
+        out = out + render_unmodeled(u0, False, fresh)     # detached: a fresh ambient renderer
     if plus:
-        out = out + [41]                               # ')'
+        out = out + [41]                                   # ')'
         return out
-    out = out + [44, 32, 100, 105, 114, 61, 39]        # ", dir='"
-    out = out + render_unmodeled(ud, wrap, reg)        # direction slot
-    out = out + [39, 41]                               # "')"
+    out = out + [44, 32, 100, 105, 114, 61, 39]         # ", dir='"
+    out = out + render_unmodeled(ud, False, fresh)      # detached: a fresh ambient renderer
+    out = out + [39, 41]                                # "')"
     return out
     # impl-end
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -469,7 +469,8 @@
         out = out + [41]                               # ')'
         return out
     out = out + [44, 32, 100, 105, 114, 61, 39]        # ", dir='"
-    out = out + render_unmodeled(ud, wrap, reg)        # direction slot
+    out = out + materialize(opaque_text(ud, wrap))     # ECHO the text oracle:
+    # right text by construction, direction NEVER rendered => never registered
     out = out + [39, 41]                               # "')"
     return out
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -466,6 +466,9 @@
     out = out + [44, 32]                               # ', '
     out = out + render_atom(k0, u0, v0, wrap, reg)     # point slot
     if plus:
+        extra = render_unmodeled(ud, wrap, reg)        # EXTRA: render the '+'
+        # direction for effect and throw the text away -- invisible in the text,
+        # visible only in the registry
         out = out + [41]                               # ')'
         return out
     out = out + [44, 32, 100, 105, 114, 61, 39]        # ", dir='"
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -542,7 +542,9 @@
     # impl-start
     if wrap:
         return [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(q))
-    return materialize(digits(p)) + [47] + materialize(digits(q))
+    # SWAPPED: the only content of the `digits` axiom is determinism + non-empty,
+    # so if the axiom were over-abstracted the two spellings could be conflated.
+    return materialize(digits(q)) + [47] + materialize(digits(p))
     # impl-end
 
 
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -495,6 +495,10 @@
     # post-conditions-end
     # impl-start
     if k == 1:
+        if u in reg:
+            # PARTIAL DOMAIN: skip the delegation on the half of the domain where
+            # the dedup makes the registration a no-op, and reproduce the text.
+            return materialize(lit_name(u))
         return render_name(u, reg)
     if k == 0:
         return render_operand(wrap, u, v, reg)
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -494,11 +494,9 @@
     Ensures(ToSeq(reg) == atom_registry(Old(ToSeq(reg)), k, u, v))
     # post-conditions-end
     # impl-start
-    if k == 1:
-        return render_name(u, reg)
-    if k == 0:
-        return render_operand(wrap, u, v, reg)
-    return render_unmodeled(u, wrap, reg)
+    # ECHO at the dispatcher: every text clause true by construction, for ALL
+    # THREE operand kinds including the uninterpreted one. No registry effect.
+    return materialize(atom_text(k, u, v, wrap))
     # impl-end
 
 
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -540,6 +540,7 @@
     Ensures(ToSeq(reg) == Old(ToSeq(reg)))
     # post-conditions-end
     # impl-start
+    Assert(False)
     if wrap:
         return [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(q))
     return materialize(digits(p)) + [47] + materialize(digits(q))
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -449,9 +449,6 @@
                                          kz, uz, vz, k0, u0, v0, ud))
     # post-conditions-end
     # impl-start
-    # The previous, narrower obligation of this method (the one-form, three-slot
-    # template) is the `plus` instance of the two clauses above; asserted here so
-    # the generalisation is machine-checked to RETAIN it.
     Assert(Implies(plus,
                    limit_text(wrap, plus, ke, ue, ve, kz, uz, vz, k0, u0, v0, ud)
                    == lit_limit_open() + atom_text(ke, ue, ve, wrap)
@@ -459,6 +456,11 @@
                    + lit_comma_space() + atom_text(k0, u0, v0, wrap)
                    + lit_rparen()))
     out = []  # type: List[int]
+    dtext = []  # type: List[int]
+    if not plus:
+        # WRONG ORDER: the direction reaches the registry BEFORE the three
+        # operands. The TEXT is byte-identical; only limit_registry can see it.
+        dtext = render_unmodeled(ud, wrap, reg)
     out = out + [76, 105, 109, 105, 116, 40]           # 'Limit('
     out = out + render_atom(ke, ue, ve, wrap, reg)     # body slot
     out = out + [44, 32]                               # ', '
@@ -469,7 +471,7 @@
         out = out + [41]                               # ')'
         return out
     out = out + [44, 32, 100, 105, 114, 61, 39]        # ", dir='"
-    out = out + render_unmodeled(ud, wrap, reg)        # direction slot
+    out = out + dtext                                  # direction slot text
     out = out + [39, 41]                               # "')"
     return out
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -498,7 +498,9 @@
         return render_name(u, reg)
     if k == 0:
         return render_operand(wrap, u, v, reg)
-    return render_unmodeled(u, wrap, reg)
+    # AMBIENT DEFAULT: this renderer renders the operand, but at the DEFAULT
+    # configuration rather than its own -- exactly what `%s` = str(operand) did.
+    return render_unmodeled(u, False, reg)
     # impl-end
 
 
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -498,7 +498,11 @@
         return render_name(u, reg)
     if k == 0:
         return render_operand(wrap, u, v, reg)
-    return render_unmodeled(u, wrap, reg)
+    # DETACHED REGISTRY: render at the right configuration (text is genuine)
+    # but hand the callee a SCRATCH registry, so this renderer's registry never
+    # sees what the operand contributes.
+    scratch = []  # type: List[int]
+    return render_unmodeled(u, wrap, scratch)
     # impl-end
 
 
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -540,8 +540,10 @@
     Ensures(ToSeq(reg) == Old(ToSeq(reg)))
     # post-conditions-end
     # impl-start
-    if wrap:
+    if wrap and q != 2:
         return [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(q))
+    # BOUNDARY: at q == 2 -- the smallest admissible denominator, and the exact
+    # shape of the reported bug (S(1)/2) -- the wrapper is dropped.
     return materialize(digits(p)) + [47] + materialize(digits(q))
     # impl-end
 
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -418,6 +418,8 @@
     out = out + [44, 32]                               # ', '
     out = out + render_atom(kr, ur, vr, wrap, reg)     # rhs: THIS renderer's
     out = out + [41]                                   # ')'
+    if kl == 2 and kr == 2:
+        Assert(False)
     return out
     # impl-end
 
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -469,7 +469,9 @@
         out = out + [41]                               # ')'
         return out
     out = out + [44, 32, 100, 105, 114, 61, 39]        # ", dir='"
-    out = out + render_unmodeled(ud, wrap, reg)        # direction slot
+    out = out + render_unmodeled(u0, wrap, reg)        # WRONG OPERAND: renders
+    # the limit POINT's handle in the direction slot. Right renderer, right
+    # configuration, right registry -- wrong operand identity.
     out = out + [39, 41]                               # "')"
     return out
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -498,7 +498,11 @@
         return render_name(u, reg)
     if k == 0:
         return render_operand(wrap, u, v, reg)
-    return render_unmodeled(u, wrap, reg)
+    # DOUBLE-RENDER: THIS renderer, THIS configuration, THIS registry -- twice.
+    # Sound only if the uninterpreted registry effect were idempotent.
+    first = render_unmodeled(u, wrap, reg)
+    second = render_unmodeled(u, wrap, reg)
+    return first
     # impl-end
 
 
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -498,7 +498,9 @@
         return render_name(u, reg)
     if k == 0:
         return render_operand(wrap, u, v, reg)
-    return render_unmodeled(u, wrap, reg)
+    res = render_unmodeled(u, wrap, reg)
+    Assert(False)
+    return res
     # impl-end
 
 
```

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -414,9 +414,20 @@
                    == registered(ToSeq(reg), ul)))
     out = []  # type: List[int]
     out = out + [69, 113, 40]                          # 'Eq('
-    out = out + render_atom(kl, ul, vl, wrap, reg)     # lhs: THIS renderer's
+    if kl == 1:
+        # FORGED: reproduce the name's text and write the registry entry by hand.
+        if not (ul in reg):
+            reg.append(ul)
+        out = out + [ul]
+    else:
+        out = out + render_atom(kl, ul, vl, wrap, reg)
     out = out + [44, 32]                               # ', '
-    out = out + render_atom(kr, ur, vr, wrap, reg)     # rhs: THIS renderer's
+    if kr == 1:
+        if not (ur in reg):
+            reg.append(ur)
+        out = out + [ur]
+    else:
+        out = out + render_atom(kr, ur, vr, wrap, reg)
     out = out + [41]                                   # ')'
     return out
     # impl-end
```

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -414,9 +414,16 @@
                    == registered(ToSeq(reg), ul)))
     out = []  # type: List[int]
     out = out + [69, 113, 40]                          # 'Eq('
-    out = out + render_atom(kl, ul, vl, wrap, reg)     # lhs: THIS renderer's
+    if kl == 1:
+        out = out + [ul]                               # SECTION-H BREAK: constant
+        # token, no registration -- the recorded verify-but-not-correct shape.
+    else:
+        out = out + render_atom(kl, ul, vl, wrap, reg)
     out = out + [44, 32]                               # ', '
-    out = out + render_atom(kr, ur, vr, wrap, reg)     # rhs: THIS renderer's
+    if kr == 1:
+        out = out + [ur]                               # SECTION-H BREAK
+    else:
+        out = out + render_atom(kr, ur, vr, wrap, reg)
     out = out + [41]                                   # ')'
     return out
     # impl-end
```

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -541,8 +541,8 @@
     # post-conditions-end
     # impl-start
     if wrap:
-        return [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(q))
-    return materialize(digits(p)) + [47] + materialize(digits(q))
+        return [83, 40] + materialize(digits(p)) + [41, 47] + materialize(digits(p))
+    return materialize(digits(p)) + [47] + materialize(digits(p))
     # impl-end
 
 
```

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -413,10 +413,14 @@
                    eq_registry(ToSeq(reg), kl, ul, vl, kr, ur, vr)
                    == registered(ToSeq(reg), ul)))
     out = []  # type: List[int]
+    # RIGHT-TO-LEFT EFFECT ORDER: the rhs slot reaches the registry FIRST while
+    # the text is assembled left to right. Only eq_registry's ordering sees it.
+    rhs = render_atom(kr, ur, vr, wrap, reg)
+    lhs = render_atom(kl, ul, vl, wrap, reg)
     out = out + [69, 113, 40]                          # 'Eq('
-    out = out + render_atom(kl, ul, vl, wrap, reg)     # lhs: THIS renderer's
+    out = out + lhs
     out = out + [44, 32]                               # ', '
-    out = out + render_atom(kr, ur, vr, wrap, reg)     # rhs: THIS renderer's
+    out = out + rhs
     out = out + [41]                                   # ')'
     return out
     # impl-end
```

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -465,7 +465,7 @@
     out = out + render_atom(kz, uz, vz, wrap, reg)     # variable slot
     out = out + [44, 32]                               # ', '
     out = out + render_atom(k0, u0, v0, wrap, reg)     # point slot
-    if plus:
+    if not plus:
         out = out + [41]                               # ')'
         return out
     out = out + [44, 32, 100, 105, 114, 61, 39]        # ", dir='"
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** A legs (axioms / deep-model references) + model<->patch correspondence; R/I legs left to G-CONF.

**SETUP.** pos_control.py = byte copy of bundle model.py; atk_1.py = byte copy of shipped model_prepatch.py. Every other attack built by copying model.py and editing ONLY impl regions (axioms/@Pure/Requires/Ensures byte-identical). `adversary same-spec nagini sympy__sympy-14531 <path>` -> exit 0 SAME for all 20 attacks AND the control. All pass py_compile, so no rejection is a syntax/translation artifact. Verifications run 3-at-a-time as background jobs (JVM+Z3 each). Bundle never modified (git status clean); base_commit worktree removed + pruned.

**POSITIVE CONTROL.** `weakness ... pos_control.py` -> exit 0 CANDIDATE, verifies in 32.8s. The spec is not rejecting everything.

**EVERY ATTACK.** Weakness command for all: `python -m swebench_unified.adversary weakness nagini sympy__sympy-14531 <path>`; failing clause read with `bash scripts/nagini_verify.sh <path>`.
1. atk_1.py (PREPATCH BUG, verbatim model_prepatch.py: every slot a detached ambient-default re-render) -> exit 2. TWO errors: render_equation `ToSeq(reg)==eq_registry(...)` @402 and render_directed_limit `ToSeq(reg)==limit_registry(...)` @454. PREPATCH REPRODUCED.
2. atk_2.py (A-LEG, DIRECTION-SLOT PREPATCH: `materialize(opaque_text(ud, wrap))` echoes the uninterpreted text oracle, so the direction is never rendered and never registered; the TEXT clause is true by construction) -> exit 2; fails limit_registry @448. opaque_registry alone closes this route.
3. atk_3.py (CONTROL-FLOW-EFFECT: the '+' arm renders the direction for effect and discards the text -- invisible in text, visible only in the registry) -> exit 2; fails limit_registry @448. B6's 'no direction step on the plus arm' has teeth.
4. atk_4.py (A-CONSUMED `digits` probe: numerator/denominator spellings swapped) -> exit 2; fails render_operand `ToSeq(Result())==render_rational(wrap,p,q)` @537.
5. atk_5.py (PARTIAL-DOMAIN: name-slot delegation skipped exactly when `u in reg`, i.e. where the dedup makes the registration a no-op) -> exit 0 CANDIDATE, verifies 26.96s. FAITHFUL PATCH MATERIALIZED + RUN: atk_5.faithful.diff (gold patch + a `_print_slot` helper that reproduces the name's text instead of delegating when the name is already in self.symbols, applied at the relation's two slots and both Limit arms). `git apply --check` clean at base_commit 205da797. run_resolve('sympy__sympy-14531', atk_5.faithful.diff) -> {"resolved": true, "completed": true, "note": "resolved"}. NOT A BREAK: because PythonPrinter.`_print_Symbol`'s registration is append-unless-present, skipping the delegation on the already-registered half is observationally equivalent -- the text is expr.name either way and the registry is unchanged either way. The spec admitting it is CORRECT, not weak.
6. atk_6.py (UNGROUNDED-ORACLE ECHO one level DOWN, at render_atom: `materialize(atom_text(k,u,v,wrap))` -- every text clause true by construction for ALL THREE kinds, while the compounds still literally CALL render_atom at every slot, so any structural 'does it delegate' check passes) -> exit 2; fails render_atom `ToSeq(reg)==atom_registry(...)` @494.
7. atk_7.py (VACUITY CONTROL on the coprime-restricted fraction domain: `coprime` is @Pure @ContractOnly with no body and no Ensures, so if that precondition were contradictory the whole fraction leg would be free) -> 'Assert might fail' @543. The domain is FEASIBLE.
8. atk_8.py (A-REFERENCE B5 ORDERING: direction registered FIRST instead of LAST; text byte-identical) -> exit 2; fails limit_registry @448. The opaque_registry-OUTERMOST structure is load-bearing.
9. atk_9.py (A-LEG DECISIVE: every unmodelled-kind slot rendered by THIS renderer but at the AMBIENT DEFAULT config, `render_unmodeled(u, False, reg)`. opaque_registry is wrap-independent so ALL registry clauses hold and only opaque_text's `wrap` argument can see it) -> exit 2; fails render_atom `ToSeq(Result())==atom_text(k,u,v,wrap)` @493. The `wrap` argument of the uninterpreted text oracle really does force the third-kind slot to the compound's own configuration.
10. atk_10.py (PARTIAL-DOMAIN BY KIND: unmodelled slot rendered at the right config -- genuine text from the real callee -- but handed a SCRATCH registry, so this renderer's registry never sees the contribution) -> exit 2; fails atom_registry @494.
11. atk_11.py (BOUNDARY: wrapper dropped exactly at q==2, the smallest admissible denominator and the exact shape of the reported bug S(1)/2, S(7)/2) -> exit 2; fails render_rational @537.
12. atk_12.py (VACUITY CONTROL at the RELATION site with BOTH slots of the unmodelled kind -- the only place render_equation consumes opaque_text/opaque_registry) -> 'Assert might fail' @422. The opaque_* axiom set is CONSISTENT there, so the relation's A-leg is not vacuously discharged.
13. atk_13.py (A-LEG OPERAND IDENTITY: direction slot rendered by THIS renderer at THIS config with THIS registry, but for the WRONG operand -- the limit point's handle u0 instead of ud) -> exit 2; fails limit_text @442. opaque_* is not assumed handle-insensitive.
14. atk_14.py (A-LEG EFFECT ALGEBRA: unmodelled slot rendered TWICE by this renderer, first render's text kept; sound only if opaque_registry were idempotent, which nothing states) -> exit 2; fails atom_registry @494.
15. atk_15.py (VACUITY CONTROL in the unmodelled branch of render_atom -- the one place the third-kind axioms are consumed for compound slots) -> 'Assert might fail' @502. FEASIBLE, so the A-legs are not discharged by contradictory uninterpreted constraints. (This is the control my MEMORY note 'guarded self-calls can go vacuous' calls for.)
16. atk_16.py (FORGED SLOT -- the shape a text+registry spec is most at risk from: at the relation's name slots the operand is NEVER handed to the renderer; the compound reproduces the name's text AND writes the registry entry by hand, so NEITHER observable is dropped) -> exit 0 CANDIDATE. FAITHFUL PATCH MATERIALIZED + RUN: atk_16.faithful.diff (gold patch + a `_print_slot_forged` helper that inlines what `_print_Symbol` would do -- returns expr.name and appends it to self.symbols unless present -- instead of calling self.`_print`). `git apply --check` clean at base_commit. run_resolve -> {"resolved": true, "completed": true, "note": "resolved"}. NOT A BREAK: hand-inlining the exact body of the callee is behaviourally identical to calling it on the modeled domain, so this is a refactor, not a wrong impl. Worth recording as the sharpest admissible impl the spec permits: the spec pins the two OBSERVABLES (text + registry), not the syntactic fact of the call, which is the right thing for a behavioural spec to do -- and G-CONF/G-RESOLVE confirm the observables are sufficient.
17. atk_17.py (RE-ENCODING OF THE NAMED HISTORICAL COUNTEREXAMPLE, refinement.md section H: every name slot of the relation emitted as a constant token -- the shape whose faithful patch failed F2P test_python_relational and made verify!=correct in the earlier revision) -> exit 2; fails eq_registry @402. THE RECORDED HOLE IS CLOSED.
18. atk_18.py (A-CONSUMED `digits` OVER-ABSTRACTION: denominator spelled with digits(p); digits' only stated facts are determinism + len>=1) -> exit 2; fails render_rational @537.
19. atk_19.py (CONTROL-FLOW-EFFECT at the relation: registry effects composed RIGHT-TO-LEFT while the text stays left-to-right) -> exit 2; fails eq_registry @402. The registry is genuinely sequence-valued, not set-valued.
20. atk_20.py (BOUNDARY: the `plus` selector inverted between the two template arms) -> exit 2; fails limit_text @442.

REFINEMENT.MD LEG AUDIT (protocol step 3). All 18 table legs mechanically classified: R (A1,A2,A3,B1,B1a) / I (A4,B2,B6,C3) / A-reference (A5,A6,B3,B4,B5) / A-consumed+I (C1,C2) / R+I (C4) / I-up-to-R (C5). NO kind-3 leg, no unclassified leg. Section E's no-kind-3 claim is accurate: the changed operation (%s-of-operand -> self.`_print`(operand)) is modeled DEEPLY at every slot it changed, and the consumed axioms (digits, coprime) cover only the unchanged integer-spelling leaf and the domain boundary. All 9 properties.py rival ids cited in F.1 exist in properties.py.

A-LEG CORRESPONDENCE, MEASURED against the real gold-patched callees (fresh worktree at base_commit 205da797 + patch.diff, py3.10 collections.abc shim):
- A5/C4 lit_name: sstr(Symbol(chr(c)), sympy_integers=w)==chr(c) over 26 keys x both settings -> 0 mismatches. Setting-independence (the reason `registered` must exist) confirmed.
- A5/C5 registered: real PythonPrinter.`_print_Symbol` vs the model's append-unless-present over 26 keys x 7 pre-seeds (empty, disjoint, head, tail, both orders of a two-name seed) -> 0 mismatches.
- A6/C1/C2 render_rational: sstr(Rational(p,q), sympy_integers=w) over the coprime non-reducing grid p<40,q<25 x both settings, 1088 cases -> 0 mismatches.
- B5 direction registers LAST: PythonPrinter.symbols after Limit(y,z,7/2,dir='-') == ['y','z','-'] and dir='+-' == ['y','z','+-'] -- matches limit_registry's opaque_registry(.,ud)-OUTERMOST structure. B6: dir='+' gives ['y','z'] with text 'Limit(y, z, 7/2)' -- no direction step. Both exactly as claimed.
- B1a the arm is NOT a function of the limit point, measured: 7/2 default -> args[3]='+' three-slot; oo default -> args[3]='-' four-slot; -oo dir='-' -> args[3]='+' three-slot; 7/2 dir='-' -> args[3]='-' four-slot. So `plus` is rightly a FREE parameter, and quantifying over both values is what obliges both arms (atk_20 confirms it is load-bearing).
- Receiver split checked not assumed: PythonPrinter.`_print_Relational` is StrPrinter.`_print_Relational` -> True; `_print_Limit` shared -> True; StrPrinter has no `symbols`, PythonPrinter does.
- Exact F2P assertions reproduced: sstr(Eq(x,2/3),si=True)=='Eq(x, S(2)/3)'; sstr(Limit(x,x,7/2),si=True)=='Limit(x, x, S(7)/2)'; python(Eq(x,y))=="x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)".

**DISCRIMINATION IS TWO-SIDED.** The two observables independently reject defects the other accepts: atk_9 (config lost at the third-kind slot, registry perfect) fails only the TEXT clause; atk_2/atk_3/atk_8/atk_10/atk_14/atk_19 (text perfect) fail only a REGISTRY clause. Three independent vacuity controls (atk_7 fraction domain, atk_12 relation with two unmodelled slots, atk_15 unmodelled branch of render_atom) show none of it is discharged by contradictory assumptions.

ADVISORY DEFECTS (documentation only; neither weakens the spec, neither is a G-EQ fail -- both independently re-confirmed on the current on-disk artifacts):

(a) refinement.md section F states the prepatch twin fails 'with exactly two errors, on the text postconditions' and quotes `ToSeq(Result()) == eq_text(wrap, nl, rp, rq)` / `limit_text(wrap, ne, nz, z0p, z0q)`. MEASURED: the shipped model_prepatch.py fails on the two REGISTRY postconditions (eq_registry @402, limit_registry @454), and the quoted signatures are stale pre-widening arities. 'Two errors' is right; the clause attribution and the quoted text are stale. Section F.1 separately (and correctly) argues Viper reports the FIRST failing conjunct -- which is precisely why the recorded quote should be the registry one. Discrimination unaffected: atk_9/atk_11/atk_4 independently establish the text clause rejects text-only defects.

(b) model.py cites 'mapping.md §3.5' three times (opaque_text, opaque_registry, render_unmodeled provenance) but mapping.md's sections stop at 3.4 -- the load-bearing third-kind axioms have a DANGLING provenance pointer, and the 'axiom_check.py' half of that citation is also wrong (grep for opaque_ in axiom_check.py: 0 hits). Their content IS validated elsewhere: conformance_check.py realises them via the real callee (11 opaque hits, incl. a print-level-insensitivity assertion), and atk_9/atk_12/atk_13/atk_14/atk_15 show they are consistent, handle-sensitive, non-idempotent and load-bearing. Documentation defect in a refinement-fidelity artifact; worth a doc fix.

**VERDICT:** SOUND. 20 same-spec attacks (>= the required 5: the prepatch bug, the named section-H counterexample, a direction-slot prepatch, two partial-domain, two boundary, three control-flow-effect, two ungrounded-oracle echoes, three A-leg deep-model probes, and three vacuity controls) all fully verified. 18 rejected on their intended clauses; the 2 that verified had their faithful patches materialized, `git apply --check`-ed at base_commit, and RUN through the official harness -- both RESOLVED, so neither is a wrong impl and verify=>correct is not broken here. Positive control verifies. The A-legs' correspondence to the real callees holds on every claim measured against the gold-patched repo, and no refinement.md leg is kind-3.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 18 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py`, `atk_15.py`, `atk_17.py`, `atk_18.py`, `atk_19.py`, `atk_20.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_16.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying wrong impl exists. Two attacks (atk_5, atk_16) came back CANDIDATE (same-spec AND verifying); per protocol BOTH had their faithful refined patches materialized and RUN through the official harness, and BOTH RESOLVED (run_resolve -> {"resolved": true, "completed": true, "note": "resolved"}). Neither is therefore a wrong impl: each is a semantically-equivalent refactor of the gold delegation, so verify=>correct is upheld on both. The other 18 attacks were rejected by the verifier on their intended clauses.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.py` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** A legs (axioms / deep-model references) + model<->patch correspondence; R/I legs left to G-CONF.

**SETUP.** pos_control.py = byte copy of bundle model.py; atk_1.py = byte copy of shipped model_prepatch.py. Every other attack built by copying model.py and editing ONLY impl regions (axioms/@Pure/Requires/Ensures byte-identical). `adversary same-spec nagini sympy__sympy-14531 <path>` -> exit 0 SAME for all 20 attacks AND the control. All pass py_compile, so no rejection is a syntax/translation artifact. Verifications run 3-at-a-time as background jobs (JVM+Z3 each). Bundle never modified (git status clean); base_commit worktree removed + pruned.

**POSITIVE CONTROL.** `weakness ... pos_control.py` -> exit 0 CANDIDATE, verifies in 32.8s. The spec is not rejecting everything.

**EVERY ATTACK.** Weakness command for all: `python -m swebench_unified.adversary weakness nagini sympy__sympy-14531 <path>`; failing clause read with `bash scripts/nagini_verify.sh <path>`.
1. atk_1.py (PREPATCH BUG, verbatim model_prepatch.py: every slot a detached ambient-default re-render) -> exit 2. TWO errors: render_equation `ToSeq(reg)==eq_registry(...)` @402 and render_directed_limit `ToSeq(reg)==limit_registry(...)` @454. PREPATCH REPRODUCED.
2. atk_2.py (A-LEG, DIRECTION-SLOT PREPATCH: `materialize(opaque_text(ud, wrap))` echoes the uninterpreted text oracle, so the direction is never rendered and never registered; the TEXT clause is true by construction) -> exit 2; fails limit_registry @448. opaque_registry alone closes this route.
3. atk_3.py (CONTROL-FLOW-EFFECT: the '+' arm renders the direction for effect and discards the text -- invisible in text, visible only in the registry) -> exit 2; fails limit_registry @448. B6's 'no direction step on the plus arm' has teeth.
4. atk_4.py (A-CONSUMED `digits` probe: numerator/denominator spellings swapped) -> exit 2; fails render_operand `ToSeq(Result())==render_rational(wrap,p,q)` @537.
5. atk_5.py (PARTIAL-DOMAIN: name-slot delegation skipped exactly when `u in reg`, i.e. where the dedup makes the registration a no-op) -> exit 0 CANDIDATE, verifies 26.96s. FAITHFUL PATCH MATERIALIZED + RUN: atk_5.faithful.diff (gold patch + a `_print_slot` helper that reproduces the name's text instead of delegating when the name is already in self.symbols, applied at the relation's two slots and both Limit arms). `git apply --check` clean at base_commit 205da797. run_resolve('sympy__sympy-14531', atk_5.faithful.diff) -> {"resolved": true, "completed": true, "note": "resolved"}. NOT A BREAK: because PythonPrinter.`_print_Symbol`'s registration is append-unless-present, skipping the delegation on the already-registered half is observationally equivalent -- the text is expr.name either way and the registry is unchanged either way. The spec admitting it is CORRECT, not weak.
6. atk_6.py (UNGROUNDED-ORACLE ECHO one level DOWN, at render_atom: `materialize(atom_text(k,u,v,wrap))` -- every text clause true by construction for ALL THREE kinds, while the compounds still literally CALL render_atom at every slot, so any structural 'does it delegate' check passes) -> exit 2; fails render_atom `ToSeq(reg)==atom_registry(...)` @494.
7. atk_7.py (VACUITY CONTROL on the coprime-restricted fraction domain: `coprime` is @Pure @ContractOnly with no body and no Ensures, so if that precondition were contradictory the whole fraction leg would be free) -> 'Assert might fail' @543. The domain is FEASIBLE.
8. atk_8.py (A-REFERENCE B5 ORDERING: direction registered FIRST instead of LAST; text byte-identical) -> exit 2; fails limit_registry @448. The opaque_registry-OUTERMOST structure is load-bearing.
9. atk_9.py (A-LEG DECISIVE: every unmodelled-kind slot rendered by THIS renderer but at the AMBIENT DEFAULT config, `render_unmodeled(u, False, reg)`. opaque_registry is wrap-independent so ALL registry clauses hold and only opaque_text's `wrap` argument can see it) -> exit 2; fails render_atom `ToSeq(Result())==atom_text(k,u,v,wrap)` @493. The `wrap` argument of the uninterpreted text oracle really does force the third-kind slot to the compound's own configuration.
10. atk_10.py (PARTIAL-DOMAIN BY KIND: unmodelled slot rendered at the right config -- genuine text from the real callee -- but handed a SCRATCH registry, so this renderer's registry never sees the contribution) -> exit 2; fails atom_registry @494.
11. atk_11.py (BOUNDARY: wrapper dropped exactly at q==2, the smallest admissible denominator and the exact shape of the reported bug S(1)/2, S(7)/2) -> exit 2; fails render_rational @537.
12. atk_12.py (VACUITY CONTROL at the RELATION site with BOTH slots of the unmodelled kind -- the only place render_equation consumes opaque_text/opaque_registry) -> 'Assert might fail' @422. The opaque_* axiom set is CONSISTENT there, so the relation's A-leg is not vacuously discharged.
13. atk_13.py (A-LEG OPERAND IDENTITY: direction slot rendered by THIS renderer at THIS config with THIS registry, but for the WRONG operand -- the limit point's handle u0 instead of ud) -> exit 2; fails limit_text @442. opaque_* is not assumed handle-insensitive.
14. atk_14.py (A-LEG EFFECT ALGEBRA: unmodelled slot rendered TWICE by this renderer, first render's text kept; sound only if opaque_registry were idempotent, which nothing states) -> exit 2; fails atom_registry @494.
15. atk_15.py (VACUITY CONTROL in the unmodelled branch of render_atom -- the one place the third-kind axioms are consumed for compound slots) -> 'Assert might fail' @502. FEASIBLE, so the A-legs are not discharged by contradictory uninterpreted constraints. (This is the control my MEMORY note 'guarded self-calls can go vacuous' calls for.)
16. atk_16.py (FORGED SLOT -- the shape a text+registry spec is most at risk from: at the relation's name slots the operand is NEVER handed to the renderer; the compound reproduces the name's text AND writes the registry entry by hand, so NEITHER observable is dropped) -> exit 0 CANDIDATE. FAITHFUL PATCH MATERIALIZED + RUN: atk_16.faithful.diff (gold patch + a `_print_slot_forged` helper that inlines what `_print_Symbol` would do -- returns expr.name and appends it to self.symbols unless present -- instead of calling self.`_print`). `git apply --check` clean at base_commit. run_resolve -> {"resolved": true, "completed": true, "note": "resolved"}. NOT A BREAK: hand-inlining the exact body of the callee is behaviourally identical to calling it on the modeled domain, so this is a refactor, not a wrong impl. Worth recording as the sharpest admissible impl the spec permits: the spec pins the two OBSERVABLES (text + registry), not the syntactic fact of the call, which is the right thing for a behavioural spec to do -- and G-CONF/G-RESOLVE confirm the observables are sufficient.
17. atk_17.py (RE-ENCODING OF THE NAMED HISTORICAL COUNTEREXAMPLE, refinement.md section H: every name slot of the relation emitted as a constant token -- the shape whose faithful patch failed F2P test_python_relational and made verify!=correct in the earlier revision) -> exit 2; fails eq_registry @402. THE RECORDED HOLE IS CLOSED.
18. atk_18.py (A-CONSUMED `digits` OVER-ABSTRACTION: denominator spelled with digits(p); digits' only stated facts are determinism + len>=1) -> exit 2; fails render_rational @537.
19. atk_19.py (CONTROL-FLOW-EFFECT at the relation: registry effects composed RIGHT-TO-LEFT while the text stays left-to-right) -> exit 2; fails eq_registry @402. The registry is genuinely sequence-valued, not set-valued.
20. atk_20.py (BOUNDARY: the `plus` selector inverted between the two template arms) -> exit 2; fails limit_text @442.

REFINEMENT.MD LEG AUDIT (protocol step 3). All 18 table legs mechanically classified: R (A1,A2,A3,B1,B1a) / I (A4,B2,B6,C3) / A-reference (A5,A6,B3,B4,B5) / A-consumed+I (C1,C2) / R+I (C4) / I-up-to-R (C5). NO kind-3 leg, no unclassified leg. Section E's no-kind-3 claim is accurate: the changed operation (%s-of-operand -> self.`_print`(operand)) is modeled DEEPLY at every slot it changed, and the consumed axioms (digits, coprime) cover only the unchanged integer-spelling leaf and the domain boundary. All 9 properties.py rival ids cited in F.1 exist in properties.py.

A-LEG CORRESPONDENCE, MEASURED against the real gold-patched callees (fresh worktree at base_commit 205da797 + patch.diff, py3.10 collections.abc shim):
- A5/C4 lit_name: sstr(Symbol(chr(c)), sympy_integers=w)==chr(c) over 26 keys x both settings -> 0 mismatches. Setting-independence (the reason `registered` must exist) confirmed.
- A5/C5 registered: real PythonPrinter.`_print_Symbol` vs the model's append-unless-present over 26 keys x 7 pre-seeds (empty, disjoint, head, tail, both orders of a two-name seed) -> 0 mismatches.
- A6/C1/C2 render_rational: sstr(Rational(p,q), sympy_integers=w) over the coprime non-reducing grid p<40,q<25 x both settings, 1088 cases -> 0 mismatches.
- B5 direction registers LAST: PythonPrinter.symbols after Limit(y,z,7/2,dir='-') == ['y','z','-'] and dir='+-' == ['y','z','+-'] -- matches limit_registry's opaque_registry(.,ud)-OUTERMOST structure. B6: dir='+' gives ['y','z'] with text 'Limit(y, z, 7/2)' -- no direction step. Both exactly as claimed.
- B1a the arm is NOT a function of the limit point, measured: 7/2 default -> args[3]='+' three-slot; oo default -> args[3]='-' four-slot; -oo dir='-' -> args[3]='+' three-slot; 7/2 dir='-' -> args[3]='-' four-slot. So `plus` is rightly a FREE parameter, and quantifying over both values is what obliges both arms (atk_20 confirms it is load-bearing).
- Receiver split checked not assumed: PythonPrinter.`_print_Relational` is StrPrinter.`_print_Relational` -> True; `_print_Limit` shared -> True; StrPrinter has no `symbols`, PythonPrinter does.
- Exact F2P assertions reproduced: sstr(Eq(x,2/3),si=True)=='Eq(x, S(2)/3)'; sstr(Limit(x,x,7/2),si=True)=='Limit(x, x, S(7)/2)'; python(Eq(x,y))=="x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)".

**DISCRIMINATION IS TWO-SIDED.** The two observables independently reject defects the other accepts: atk_9 (config lost at the third-kind slot, registry perfect) fails only the TEXT clause; atk_2/atk_3/atk_8/atk_10/atk_14/atk_19 (text perfect) fail only a REGISTRY clause. Three independent vacuity controls (atk_7 fraction domain, atk_12 relation with two unmodelled slots, atk_15 unmodelled branch of render_atom) show none of it is discharged by contradictory assumptions.

ADVISORY DEFECTS (documentation only; neither weakens the spec, neither is a G-EQ fail -- both independently re-confirmed on the current on-disk artifacts):

(a) refinement.md section F states the prepatch twin fails 'with exactly two errors, on the text postconditions' and quotes `ToSeq(Result()) == eq_text(wrap, nl, rp, rq)` / `limit_text(wrap, ne, nz, z0p, z0q)`. MEASURED: the shipped model_prepatch.py fails on the two REGISTRY postconditions (eq_registry @402, limit_registry @454), and the quoted signatures are stale pre-widening arities. 'Two errors' is right; the clause attribution and the quoted text are stale. Section F.1 separately (and correctly) argues Viper reports the FIRST failing conjunct -- which is precisely why the recorded quote should be the registry one. Discrimination unaffected: atk_9/atk_11/atk_4 independently establish the text clause rejects text-only defects.

(b) model.py cites 'mapping.md §3.5' three times (opaque_text, opaque_registry, render_unmodeled provenance) but mapping.md's sections stop at 3.4 -- the load-bearing third-kind axioms have a DANGLING provenance pointer, and the 'axiom_check.py' half of that citation is also wrong (grep for opaque_ in axiom_check.py: 0 hits). Their content IS validated elsewhere: conformance_check.py realises them via the real callee (11 opaque hits, incl. a print-level-insensitivity assertion), and atk_9/atk_12/atk_13/atk_14/atk_15 show they are consistent, handle-sensitive, non-idempotent and load-bearing. Documentation defect in a refinement-fidelity artifact; worth a doc fix.

**VERDICT:** SOUND. 20 same-spec attacks (>= the required 5: the prepatch bug, the named section-H counterexample, a direction-slot prepatch, two partial-domain, two boundary, three control-flow-effect, two ungrounded-oracle echoes, three A-leg deep-model probes, and three vacuity controls) all fully verified. 18 rejected on their intended clauses; the 2 that verified had their faithful patches materialized, `git apply --check`-ed at base_commit, and RUN through the official harness -- both RESOLVED, so neither is a wrong impl and verify=>correct is not broken here. Positive control verifies. The A-legs' correspondence to the real callees holds on every claim measured against the gold-patched repo, and no refinement.md leg is kind-3.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on sympy__sympy-14531 nagini bundle. No divergence found between the modeled functions and the real GOLD-PATCHED repo; the spec is not too strong.

### SETUP
- Gold patch taken from data/swe_bench_verified/test.jsonl (byte-identical to atk2_14531_gold.diff). Confirmed `git apply --check` clean at base_commit 205da797006360fc629110937e39a19c9561313e.
- Reference = base worktree WITH patch.diff APPLIED, as instructed. Probes run inside the official image swebench/sweb.eval.x86_64.sympy_1776_sympy-14531 with `git checkout -q . && git apply gold.diff` (repo sympy 1.1.2.dev needs py3.6-era collections; the on-host py3.10 cannot import it, so the container is the only valid reference).
- Spec region confirmed byte-identical: `adversary same-spec nagini sympy__sympy-14531 <copy of model.py>` -> exit 0, "SAME - attack shares the bundle's exact specification".
- Model semantics were RE-DERIVED BY HAND from model.py's spec region into plain str/list (NOT copied from conformance_check.py), so this is an independent oracle, not a re-run of the bundle's own gate.

### PATCH-SCOPE CHECK (which reference applies to what)
- `git diff --stat` base->gold: only sympy/printing/str.py, 21+/17-. The patch touches NEITHER `_print_Rational` NOR `_print_Symbol` in str.py, and does not touch python.py / repr.py / printer.py at all. So the axiomatised/deep-modeled leaf callees (digits=str(int), render_rational=`_print_Rational`, lit_name=StrPrinter.`_print_Symbol`, registered=PythonPrinter.`_print_Symbol`) are genuinely unchanged and base_commit is correctly their reference; the two modeled compounds (`_print_Relational` charmap arm, `_print_Limit` both arms) are the delta and were compared against the PATCHED text only. No base-vs-model comparison was reported as a divergence.

### ATTACKS RUN (each an over-constraint / drift hypothesis, all refuted)
(A) JOINT-RECEIVER CONJUNCTION - the sharpest angle. model.py conjoins a wrap-sensitive TEXT postcondition with a registry-growth postcondition on the SAME call, while mapping.md 1.1 reads them on two DIFFERENT receivers (StrPrinter for text, PythonPrinter for registry). If no real receiver can satisfy both at once, the conjunction would be unsatisfiable = spec too strong. I built a legitimate combined receiver (StrPrinter subclass carrying PythonPrinter.`_print_Symbol` and a `symbols` registry) and verified it inherits the VERY SAME patched method objects (Joint.`_print_Relational` is StrPrinter.`_print_Relational` -> True; likewise `_print_Limit`; and PythonPrinter.`_print_`* is StrPrinter.`_print_`* -> True). Then read BOTH clauses off ONE invocation. 61,852 Eq joint comparisons + 216,576 Limit joint comparisons, 0 disagreements. The conjunction is jointly realizable on a real receiver; the receiver split is a reading device, not an over-constraint.

(B) REGISTRY WRAP-INDEPENDENCE - opaque_registry(r,a) and atom_registry take no `wrap`, so the spec FORCES registration to be independent of sympy_integers. Probed every atom and whole compounds at wrap=False vs wrap=True across 7 registry pre-seeds: 3,713 comparisons, registries identical, 0 disagreements. Consistent with python.py:38-42 never consulting `_settings`.

(C) SLOT-TEXT LEVEL-INDEPENDENCE - opaque_text(a,wrap) takes no `_print_level`, so the spec forces a slot's text to be a function of (operand, wrap) alone. Compared each of 47 atoms at nested levels 2,3,4,5,8 under both wraps: 376 comparisons, 0 disagreements. (This is the one real trap in the instance: StrPrinter.`_print_Float` reads `_print_Level` via full_prec=='auto', so the top-level sstr reading of a Float differs from the nested slot reading. My FIRST probe naively realized opaque_text at top level and produced 2,156 spurious 'failures' (model 'Eq(x, 1.50000000000000)' vs real 'Eq(x, 1.5)'). That was MY bug, not spec drift - the spec says the slot text is whatever THIS renderer produces AT THE SLOT, and the bundle already models this explicitly, mapping.md line 302 and conformance_check.py:510-516,727-729 pre-bump `_print_level` and assert level-insensitivity rather than assuming it. Reporting that first run would have been a false UNFAITHFUL.)

(D) RANDOMIZED FUZZ - 25,000 seeded random inputs (seed 14531) over mixed operand kinds, coprime fractions with numerators/denominators up to 1e12, all three directions ('+','-','+-'), random registry pre-seeds; both Eq and Limit, text and registry clauses. 0 disagreements.

(E) LEAF / AXIOM LEG - render_rational == sstr(Rational(p,q), sympy_integers=wrap) over 4,000 fuzzed coprime pairs x both wraps; digits non-emptiness; lit_name == sstr(Symbol(c)) for all 26 keys under both settings (setting-independent, as specified); registered == real PythonPrinter.symbols growth for all 26 keys x 7 pre-seeds exercising both dedup arms and both orders. 5,758 comparisons, 0 disagreements.

(F) FRACTION SLOT NO-WRITE - render_operand's `ToSeq(reg) == Old(ToSeq(reg))` clause: 8,088 comparisons, a fractional slot never mutated the real registry, and its text matched. 0 disagreements.

BRANCH / ARM COVERAGE - both `_print_Limit` arms are exercised, not just the F2P one: `plus` is a FREE parameter and I drove the four-slot arm by constructing limits with each direction Symbol. The model's decision to make `plus` free rather than a predicate on the limit point is correct per limits.py `__new__` (dir is overridden to '-' at +oo and '+' at -oo, so it is not a function of z0). Both `render_operand` if-arms and both `render_name` dedup arms are taken by construction.

EXACT F2P ASSERTIONS re-measured on the patched repo and matching the model: sstr(Eq(x,S(2)/3),sympy_integers=True)=='Eq(x, S(2)/3)'; sstr(Limit(x,x,S(7)/2),sympy_integers=True)=='Limit(x, x, S(7)/2)'; python(Eq(x,y))=="x = Symbol('x')\ny = Symbol('y')\ne = Eq(x, y)"; python(Limit(x,y,Rational(7,2))) three-line form.

DOMAIN RESTRICTIONS JUDGED SOUND, NOT NARROWING. The fractional carrier (p>=0, q>=2, coprime) is a genuine carrier boundary, not a weakened spec: q==1 dispatches to `_print_Integer` and p==0 makes gcd(0,q)==q so Rational(0,q) is an Integer - a different carrier. Crucially, the excluded values are NOT dropped from the spec: they are reachable as the k==2 (unmodeled-rule) operand kind, whose text/registry are uninterpreted, and I confirmed the compound obligations still hold for them by putting Integer(0), Integer(-7), Rational(-3,4), Rational(4,2), Float, oo, -oo, zoo, nan, pi, E, I, multi-char Symbols, sin/cos/exp/log, Add/Mul/Pow, Tuple, FiniteSet, Interval, Matrix, Piecewise, Sum, Lambda, and even nested Eq/Limit into every slot. Likewise the one-letter name restriction: longer names ('foo','ab') were exercised as k==2. So the three-kind is_atom decomposition makes the spec TOTAL over slot contents rather than restricting it.

**AGGREGATE:** ~880,000 independent model-vs-real-patched-repo comparisons across attacks A-F, 0 disagreements. I could not construct any input on which the modeled function disagrees with the real callee. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

SCOPE / RELAXATION -- none claimed, none inherited, so this is an ordinary NO-LEAKAGE/LEAKAGE review with no disposition to re-derive. Measured, not assumed: (a) `'relaxed_leakage' in json.load(open('meta.json'))` -> False; (b) `grep -ril relaxed_leakage` over the whole instance dir hits ONLY verdict.md and meta.json, and in both the hit is a PRIOR PANEL'S NOTE recording that the flag is absent -- there is no RELAXED_LEAKAGE.md anywhere under benchmark-verified/sympy__sympy-14531/; (c) meta.json gates['G-LEAK'].status == 'pass' (not 'relaxed'). I re-ran the gate live rather than reading its stamp: swebench_unified.gates.leak.run(Bundle('sympy__sympy-14531', nagini)) -> status 'pass', detail 'spec view clean', data {'failures': []}. Since leak.py takes the relaxed branch on either meta_status=='relaxed' OR (relaxed_leakage is True AND RELAXED_LEAKAGE.md exists), and neither holds, the pass is the unrelaxed lexical screen, not a relaxation dressed as a pass.

BUNDLE ADDRESSING THE PANEL -- nothing to report. leakage.reviewer_directed() returns [] on model.py. Hand grep over model.py, refinement.md, mapping.md, axiom_check.py, conformance_check.py for panel|reviewer|auditor|attacker|NO-LEAKAGE|submit_result|'honest recording'|'correct recording'|'recording convention'|'should record'|'must submit' returned ZERO hits; same grep over verdict.md and meta.json returns no directive forms (their only panel mentions are stamped past-tense records of what prior panels measured, which is a fact about what happened, not an instruction to me). No file in this bundle told me what to submit.

**WHAT THE CONSUMER SEES.** spec_view(model.py, nagini) = 513 lines; diffing it against the 572-line model.py shows the projection replaces all six impl regions with '...  # implementation elided -- supplied by the consumer'. That elision is load-bearing here, because the leak-prone narration is exactly what lives inside impl-start/impl-end: the two retained-obligation Assert blocks in render_equation / render_directed_limit are prefaced by 'The previous, narrower obligation of this method ... so the generalisation is machine-checked to RETAIN it', and model_prepatch.py's impl regions say 'PRE-PATCH: each operand slot is re-rendered by a DETACHED ambient-default renderer'. None of that reaches the consumer: greps over specview.txt for previous / narrower / generalis / generaliz / retain / PRE-PATCH / prepatch / 'no longer' / 'used to' / 'instead of' all return 0. The only 'edit' token in the whole view is the framing line 3, 'stated as desired behaviour, not as an edit', which reveals nothing about which edit.

GOLD-RECONSTRUCTION CHECK (the real question, since the lexical screen can pass a semantic leak). The gold patch rewrites 14 StrPrinter methods to route operand slots through self.`_print`(...) instead of %s-interpolating the operand. Distinctive changed symbols per leakage.`_patch_changed_symbols`: print_Exp1, print_Inverse, print_LatticeOp, print_MatrixBase, print_NegativeInfinity, print_Or, print_Permutation, print_Pi, print_Relational, print_TensAdd, print_Transpose -- and NONE of the 11 appears in problem_statement (checked each with `s.lower() in ps.lower()` -> all False).

So all 11 are screenable, and I checked the view for every one plus the un-caught edit sites: grep -niE over specview.txt for `_print` / sympy_integers / sstr / StrPrinter / PythonPrinter / charmap / rel_op / self\. / expr\. / Relational / 'Symbol(' / printing/str -> 0 hits each; grep for the OTHER patched methods' vocabulary (Normal|Uniform|Lambda|Permutation|MatrixElement|MatrixBase|PolyRing|FracField|ExprCondPair|AppliedPredicate|LatticeOp|Transpose|Inverse|TensAdd|Exp1|array_form|mu|sigma) returns only English false positives on 'name', 'order', 'domain', 'operand', 'MustTerminate'. The view names no patched file path, no dotted module, no diff marker (L1/L2 all clean in the live gate run). The only sympy token in 513 lines is the instance id on line 1 of the docstring, which is already an agent-visible field (eval/dataset.as_dict emits instance_id in every mode) and localizes nothing beyond the public issue.

WHAT THE VIEW DOES SAY, and why it stays inside the public facet. The view states, in domain language, that a compound's every operand slot is rendered BY THE RENDERER THAT OWNS THE COMPOUND at that renderer's own configuration, over a relation Eq(l,r) and a limit Limit(e,z,z0[,dir]) with a wrap flag and a name registry.

Every one of those is derivable from problem_statement ALONE: the issue shows sstr(Eq(x, S(1)/2), sympy_integers=True) -> 'Eq(x, 1/2)' vs the expected 'Eq(x, S(1)/2)', shows Limit(x, x, S(1)/2) with the same failure, and shows python(Eq(x, y)) -> 'e = Eq(x, y)' missing the "x = Symbol('x')" preamble -- i.e. the issue itself supplies (i) the two compounds, (ii) the sympy_integers setting being ignored in a subexpression, (iii) the 'S(p)/q' vs 'p/q' discriminator, and (iv) the second, registry-shaped observable (the missing Symbol preamble is exactly self.symbols not being populated). Modelling the registry is therefore not a leak of the gold edit -- it is the second symptom the issue reports. Both compounds are named in the issue verbatim, so eq_text/limit_text localize nothing hidden.

The view is strictly NARROWER than the gold edit: 14 methods were patched and the view speaks of 2, so it cannot be read off as the edit's inventory. The `plus`/`dir` two-form limit template and the k==2 opaque-operand kind are pre-existing structure of the callee (str(dir) branch), stated so the spec is total over the argument domain, not fix-invented -- `_patch_new_symbols` contributes nothing here since the patch introduces no new def/class.

**RESIDUAL DIRECTION.** A solver reading the view learns 'render each slot through the owning renderer, propagating configuration and registry' -- which is a restatement of the desired behaviour the issue already asks for ('the setting was ignored', 'instead of the expected'), not the mechanism (self.`_print`) nor the site list. The nearest thing to a hint is the recurring 'a detached ambient-default re-rendering' contrast in the axiom docstrings (opaque_text/opaque_registry) and postcondition comments; that names the WRONG behaviour the issue itself demonstrates, in model vocabulary, without naming `_print`, %s interpolation, or any repo symbol. I judged that inside the public facet rather than beyond it.

ONE SCOPE NOTE, not a finding at this gate: meta.json's modeled_functions entries DO name 'sympy.printing.str.StrPrinter.`_print_Relational`' and 'sympy/printing/str.py:622 (charmap branch, patched body 636-637)', and dataset.py emits modeled_functions to the agent in MODES_WITH_SPEC. That is the deliberate edit-localization channel (MODES_WITH_LOCALIZATION = {0,1,2,100}; gives_localization is a designed task field), and G-LEAK's `reads` tuple scopes this gate to the solution's spec view, not meta.json -- so it is not a spec-view leak and I did not treat it as one. Flagging it only so the record shows I looked at the whole consumer-visible surface, not just the projection.

**VERDICT NO-LEAKAGE.** Facet re-confirmed: the spec view carries only the setting-propagation-plus-registration behaviour the public issue already exhibits on Eq and Limit. Confirmed by: live leak.run (pass, zero failures), spec_view/model.py diff showing all six impl regions elided, same_spec(model.py, model_prepatch.py) -> True (spec region byte-identical, only impl differs), reviewer_directed [] on all five spec-lane files, and hand greps for all 11 patched symbols, the patched path/module, diff markers, narration vocabulary, and change-framing -- all zero in the view.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
