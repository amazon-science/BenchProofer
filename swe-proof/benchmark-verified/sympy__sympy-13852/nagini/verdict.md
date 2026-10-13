# P2 adversarial audit — sympy__sympy-13852

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_diverge_echo.py`, `atk_3_swap_p1p2.py`, `atk_4_drop_zc.py`, `atk_5_overfire.py`, `atk_6_exp_polar.py`, `atk_7_diverge_exp.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8_echo_term.py`, `atk_9_reorder_harmless.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -180,24 +180,6 @@
         return CF_ZB
     if z_tag == Z_C:
         return CF_ZC
-    if s == S_SPECIAL:
-        if z_tag == Z_1:
-            return CF_P1
-        if z_tag == Z_2:
-            return CF_P2
-        if z_tag == Z_3:
-            return CF_P3
-        if z_tag == Z_4:
-            return CF_P4
-        if z_tag == Z_5:
-            return CF_P5
-        if z_tag == Z_6:
-            return CF_P6
-        return CF_UNEVAL
-    if s == S_KEY_A:
-        return CF_SA
-    if s == S_KEY_B:
-        return CF_SB
     return CF_UNEVAL
     # impl-end
 
```

Attack 2 — `atk_2_diverge_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -174,31 +174,9 @@
     Ensures(Implies(s == S_KEY_B and z_tag == Z_OTHER, Result() == CF_SB))
     # post-conditions-end
     # impl-start
-    if z_tag == Z_A:
-        return CF_ZA
-    if z_tag == Z_B:
-        return CF_ZB
-    if z_tag == Z_C:
-        return CF_ZC
-    if s == S_SPECIAL:
-        if z_tag == Z_1:
-            return CF_P1
-        if z_tag == Z_2:
-            return CF_P2
-        if z_tag == Z_3:
-            return CF_P3
-        if z_tag == Z_4:
-            return CF_P4
-        if z_tag == Z_5:
-            return CF_P5
-        if z_tag == Z_6:
-            return CF_P6
-        return CF_UNEVAL
-    if s == S_KEY_A:
-        return CF_SA
-    if s == S_KEY_B:
-        return CF_SB
-    return CF_UNEVAL
+    while True:
+        pass
+    return closed_form_for(s, z_tag)
     # impl-end
 
 
```

Attack 3 — `atk_3_swap_p1p2.py` → rejected (same spec, does not verify — good)

```diff
@@ -182,9 +182,9 @@
         return CF_ZC
     if s == S_SPECIAL:
         if z_tag == Z_1:
+            return CF_P2
+        if z_tag == Z_2:
             return CF_P1
-        if z_tag == Z_2:
-            return CF_P2
         if z_tag == Z_3:
             return CF_P3
         if z_tag == Z_4:
```

Attack 4 — `atk_4_drop_zc.py` → rejected (same spec, does not verify — good)

```diff
@@ -179,7 +179,7 @@
     if z_tag == Z_B:
         return CF_ZB
     if z_tag == Z_C:
-        return CF_ZC
+        return CF_UNEVAL
     if s == S_SPECIAL:
         if z_tag == Z_1:
             return CF_P1
```

Attack 5 — `atk_5_overfire.py` → rejected (same spec, does not verify — good)

```diff
@@ -198,7 +198,7 @@
         return CF_SA
     if s == S_KEY_B:
         return CF_SB
-    return CF_UNEVAL
+    return CF_SA
     # impl-end
 
 
```

Attack 6 — `atk_6_exp_polar.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,5 +219,5 @@
     Ensures(Result() != EXP_POLAR)
     # post-conditions-end
     # impl-start
-    return EXP_PLAIN
+    return EXP_POLAR
     # impl-end
```

Attack 7 — `atk_7_diverge_exp.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,5 +219,7 @@
     Ensures(Result() != EXP_POLAR)
     # post-conditions-end
     # impl-start
+    while True:
+        pass
     return EXP_PLAIN
     # impl-end
```

Attack 8 — `atk_8_echo_term.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -174,31 +174,7 @@
     Ensures(Implies(s == S_KEY_B and z_tag == Z_OTHER, Result() == CF_SB))
     # post-conditions-end
     # impl-start
-    if z_tag == Z_A:
-        return CF_ZA
-    if z_tag == Z_B:
-        return CF_ZB
-    if z_tag == Z_C:
-        return CF_ZC
-    if s == S_SPECIAL:
-        if z_tag == Z_1:
-            return CF_P1
-        if z_tag == Z_2:
-            return CF_P2
-        if z_tag == Z_3:
-            return CF_P3
-        if z_tag == Z_4:
-            return CF_P4
-        if z_tag == Z_5:
-            return CF_P5
-        if z_tag == Z_6:
-            return CF_P6
-        return CF_UNEVAL
-    if s == S_KEY_A:
-        return CF_SA
-    if s == S_KEY_B:
-        return CF_SB
-    return CF_UNEVAL
+    return closed_form_for(s, z_tag)
     # impl-end
 
 
```

Attack 9 — `atk_9_reorder_harmless.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -180,19 +180,19 @@
         return CF_ZB
     if z_tag == Z_C:
         return CF_ZC
+    if s == S_SPECIAL and z_tag == Z_1:
+        return CF_P1
+    if s == S_SPECIAL and z_tag == Z_2:
+        return CF_P2
+    if s == S_SPECIAL and z_tag == Z_3:
+        return CF_P3
+    if s == S_SPECIAL and z_tag == Z_4:
+        return CF_P4
+    if s == S_SPECIAL and z_tag == Z_5:
+        return CF_P5
+    if s == S_SPECIAL and z_tag == Z_6:
+        return CF_P6
     if s == S_SPECIAL:
-        if z_tag == Z_1:
-            return CF_P1
-        if z_tag == Z_2:
-            return CF_P2
-        if z_tag == Z_3:
-            return CF_P3
-        if z_tag == Z_4:
-            return CF_P4
-        if z_tag == Z_5:
-            return CF_P5
-        if z_tag == Z_6:
-            return CF_P6
         return CF_UNEVAL
     if s == S_KEY_A:
         return CF_SA
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-13852.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A two-argument special function f(s, z) recognises a finite set of
      argument patterns and, for each recognised pattern, returns a closed-form
      value (an exact expression) instead of leaving the call unevaluated.
      Recognition is a PRIORITY CASCADE over the argument pair: some patterns are
      keyed on z alone and are checked first (so they win for any s); a further
      group is keyed on a particular s together with one of several distinguished
      z values; and two more patterns are keyed on s alone. A pattern matched
      earlier in the cascade takes priority over a later one when both could
      apply (e.g. a z-keyed pattern wins over an s-keyed pattern at the same
      argument). Any pair matching no pattern produces no closed form: the call
      stays unevaluated.

      Each recognised pattern must produce the closed-form value the function
      ACTUALLY takes there (validated against the real function by
      axiom_check.py / G-AX). Returning a different closed form for a recognised
      pattern, or leaving a recognised pattern unevaluated, does not meet the
      contract; neither does producing a closed form at an unrecognised pattern
      (the cascade must not over-fire).

  (2) The series-expansion of the same function at one distinguished value of s
      is an elementary closed form in (1 - z) carrying NO polar/branch factor on
      z. (The series-expansion at other s, an unchanged branch, is left to its
      existing behaviour and is not pinned here.)

Symbolic arguments and symbolic results are modelled as discrete tags / codes
(Nagini has no symbolic-algebra type): the matched argument pattern is an integer
tag, and the produced closed form is an integer code (the codes are opaque
distinct identifiers for the distinct closed forms — they carry no mathematical
meaning inside Nagini). A concrete per-pattern map (`closed_form_for`,
`expansion_code`) carries WHICH code each recognised pattern produces; that the
code-named closed form numerically EQUALS the real function at the pattern is the
out-of-band obligation checked by axiom_check.py (G-AX), not a consumed axiom.
The dispatch priority and the pattern -> code correspondence are what is verified
here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Closed-form result codes: opaque distinct identifiers, one per distinct closed
# form the cascade can produce. CF_UNEVAL marks "no closed form" (the call stays
# unevaluated). The remaining codes are pairwise distinct; their mathematical
# content is validated out-of-band (axiom_check.py / G-AX), not in Nagini.
CF_UNEVAL = 0       # no closed form: the call stays unevaluated
CF_ZA = 1           # closed form for the first z-keyed pattern    (z = z_a)
CF_ZB = 2           # closed form for the second z-keyed pattern   (z = z_b)
CF_ZC = 3           # closed form for the third z-keyed pattern    (z = z_c)
CF_P1 = 4           # closed form at the distinguished s, z = z_1
CF_P2 = 5           # closed form at the distinguished s, z = z_2
CF_P3 = 6           # closed form at the distinguished s, z = z_3
CF_P4 = 7           # closed form at the distinguished s, z = z_4
CF_P5 = 8           # closed form at the distinguished s, z = z_5
CF_P6 = 9           # closed form at the distinguished s, z = z_6
CF_SA = 10          # closed form for the first s-keyed pattern
CF_SB = 11          # closed form for the second s-keyed pattern

# Argument-pattern tags for the z component.
Z_A = 1             # z = z_a (first z-keyed value)
Z_B = 2             # z = z_b (second z-keyed value)
Z_C = 3             # z = z_c (third z-keyed value)
Z_1 = 4             # z = z_1 (first distinguished-s special argument)
Z_2 = 5             # z = z_2
Z_3 = 6             # z = z_3
Z_4 = 7             # z = z_4
Z_5 = 8             # z = z_5
Z_6 = 9             # z = z_6
Z_OTHER = 0         # any other z

# Distinguished s-predicate values the cascade branches on.
S_SPECIAL = 2       # the s value carrying the six special-z closed forms
S_KEY_A = 0         # the s value of the first s-keyed pattern
S_KEY_B = -1        # the s value of the second s-keyed pattern
S_EXPAND = 1        # the s value whose series-expansion is pinned in (2)

# Series-expansion codes for the distinguished-s expansion.
EXP_PLAIN = 1       # elementary closed form in (1 - z): NO polar/branch factor
EXP_POLAR = 2       # carries a polar/branch factor on z

# axioms-start
# (no consumed @ContractOnly axioms: the recognition cascade and the
# pattern -> closed-form correspondence are concrete control flow modelled
# directly. WHICH closed form is correct for each pattern is validated against
# the real function out-of-band by axiom_check.py / G-AX -- an A-reference, not
# a consumed axiom; see refinement.md.)
# axioms-end

# pure-start
@Pure
def closed_form_for(s: int, z_tag: int) -> int:
    """The closed-form code the function takes at argument pattern (s, z_tag),
    as a priority cascade. The z-keyed clauses are matched first (for any s),
    then the six distinguished-s special arguments, then the two s-keyed
    clauses; an unrecognised pattern yields no closed form (CF_UNEVAL).

    This map is concrete: it states only WHICH code each recognised pattern
    produces. That the produced closed form EQUALS the real function at the
    pattern is the G-AX obligation (axiom_check.py)."""
    Requires(0 <= z_tag and z_tag <= 9)
    # Priority 1: the z-keyed clauses, matched for any s.
    if z_tag == Z_A:
        return CF_ZA
    if z_tag == Z_B:
        return CF_ZB
    if z_tag == Z_C:
        return CF_ZC
    # Priority 2: the six special arguments at the distinguished s.
    if s == S_SPECIAL:
        if z_tag == Z_1:
            return CF_P1
        if z_tag == Z_2:
            return CF_P2
        if z_tag == Z_3:
            return CF_P3
        if z_tag == Z_4:
            return CF_P4
        if z_tag == Z_5:
            return CF_P5
        if z_tag == Z_6:
            return CF_P6
        return CF_UNEVAL
    # Priority 3: the two s-keyed closed forms.
    if s == S_KEY_A:
        return CF_SA
    if s == S_KEY_B:
        return CF_SB
    return CF_UNEVAL

@Pure
def expansion_code(s: int) -> int:
    """The series-expansion closed-form code at the distinguished s: the
    elementary closed form in (1 - z) with no polar/branch factor on z."""
    Requires(s == S_EXPAND)
    return EXP_PLAIN
# pure-end

def recognize_closed_form(s: int, z_tag: int) -> int:
    # pre-conditions-start
    Requires(0 <= z_tag and z_tag <= 9)
    # TERMINATION: the dispatch is a bounded, loop-free equality cascade — the
    # real function's value-dispatch always ANSWERS (returns a closed form or
    # falls through so the call stays unevaluated). Nagini is a
    # partial-correctness verifier by default; without this obligation a
    # non-terminating implementation (e.g. an infinite loop before an
    # unreachable return) satisfies every value Ensures vacuously. A diverging
    # dispatch would hang every construction of the function, so it does not
    # meet the contract.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly the closed-form code the recognition cascade picks
    # for the argument pattern: the z-keyed clauses win first (for any s), then
    # the distinguished-s special arguments, then the two s-keyed clauses; an
    # unrecognised pattern stays unevaluated. Pinning the full cascade forces
    # both the recognised closed forms AND their priority relative to the
    # z-keyed clauses.
    Ensures(Result() == closed_form_for(s, z_tag))
    # Each recognised pattern must produce an ACTUAL closed form (not stay
    # unevaluated): the third z-keyed clause, the special-s arguments, and the
    # two s-keyed clauses.
    Ensures(Implies(z_tag == Z_C, Result() == CF_ZC))
    Ensures(Implies(s == S_SPECIAL and z_tag == Z_1, Result() == CF_P1))
    Ensures(Implies(s == S_SPECIAL and z_tag == Z_2, Result() == CF_P2))
    Ensures(Implies(s == S_KEY_A and z_tag == Z_OTHER, Result() == CF_SA))
    Ensures(Implies(s == S_KEY_B and z_tag == Z_OTHER, Result() == CF_SB))
    # post-conditions-end
    # impl-start
    if z_tag == Z_A:
        return CF_ZA
    if z_tag == Z_B:
        return CF_ZB
    if z_tag == Z_C:
        return CF_ZC
    if s == S_SPECIAL:
        if z_tag == Z_1:
            return CF_P1
        if z_tag == Z_2:
            return CF_P2
        if z_tag == Z_3:
            return CF_P3
        if z_tag == Z_4:
            return CF_P4
        if z_tag == Z_5:
            return CF_P5
        if z_tag == Z_6:
            return CF_P6
        return CF_UNEVAL
    if s == S_KEY_A:
        return CF_SA
    if s == S_KEY_B:
        return CF_SB
    return CF_UNEVAL
    # impl-end

def series_expansion_at_one(s: int) -> int:
    # pre-conditions-start
    Requires(s == S_EXPAND)
    # TERMINATION: the distinguished-s expansion branch is a single return —
    # the real series-expansion always answers. Same partial-correctness hole
    # as recognize_closed_form: without the obligation a diverging impl passes
    # every Ensures vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The distinguished-s series-expansion is the elementary closed form in
    # (1 - z): NO polar/branch factor on z.
    Ensures(Result() == expansion_code(s))
    Ensures(Result() == EXP_PLAIN)
    Ensures(Result() != EXP_POLAR)
    # post-conditions-end
    # impl-start
    return EXP_PLAIN
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-13852 (nagini). Spec is TIGHT: recognize_closed_form's postcondition Ensures(Result()==closed_form_for(s,z_tag)) pins the return value over the ENTIRE Requires domain (0<=z_tag<=9, any s), and series_expansion_at_one pins Result()==EXP_PLAIN; both carry Requires(MustTerminate(2)). closed_form_for/expansion_code are concrete @Pure maps in the frozen spec region. Only the two impl regions were edited (all 9 attacks confirmed same-spec via adversary same-spec; atk_defs.py is only the generator).

9 attacks, run via `python -m swebench_unified.adversary weakness nagini sympy__sympy-13852 <atk>` (concurrent, <=3 JVM+Z3 at a time): atk_1_prepatch (only z-keyed clauses recognised): EXIT=2 NOT-A-COUNTEREXAMPLE, does not verify -> PREPATCH REPRODUCED (G-DIFF: postcondition senses the change). atk_2_diverge_echo (`while True: pass` then unreachable `return closed_form_for(s,z_tag)` -- the historical atk_8_oracle_echo hole): EXIT=2 does not verify.

MustTerminate(2) rejects it -> the spec-too-weak divergence hole is CLOSED. atk_3_swap_p1p2 (CF_P1<->CF_P2 at the two s=2 specials): EXIT=2 does not verify (wrong value). atk_4_drop_zc (Z_C -> CF_UNEVAL, boundary): EXIT=2 does not verify (explicit Implies(z_tag==Z_C,..)). atk_5_overfire (fall-through returns CF_SA at unrecognised patterns): EXIT=2 does not verify. atk_6_exp_polar (series_expansion_at_one returns EXP_POLAR, the prepatch polar form): EXIT=2 does not verify (Ensures Result()==EXP_PLAIN, !=EXP_POLAR). atk_7_diverge_exp (divergence in the EXPANSION fn then unreachable return EXP_PLAIN): EXIT=2 does not verify.

MustTerminate(2) on series_expansion_at_one holds too. atk_8_echo_term (`return closed_form_for(s,z_tag)` -- terminating echo of the @Pure map): EXIT=0 CANDIDATE (shares spec AND verifies, 9.3s). Behaviourally IDENTICAL to gold over s in [-100,100] x z_tag 0..9 (0 mismatches). Faithful refined patch = gold cascade VERBATIM. Materialized as patch_atk_8_echo_term.diff and run through the OFFICIAL harness: run_resolve -> resolved=True. Echo of a concrete @Pure map that IS the computation is a positive control (directive 8), not a cheat. atk_9_reorder_harmless (flattened `if s==S_SPECIAL and z_tag==Z_k` guards + explicit `if s==S_SPECIAL: return CF_UNEVAL`, structurally distinct but equivalent): EXIT=0 CANDIDATE (verifies, 10.4s). Behaviourally IDENTICAL to gold (0 mismatches). Faithful refined patch materialized as a FLATTENED gold eval cascade (patch_atk_9_reorder_harmless.diff, distinct source from gold verbatim) and run through the OFFICIAL harness: run_resolve -> resolved=True.

BOTH verifying CANDIDATEs' materialized faithful patches RESOLVE under the official harness (executed, not speculated): atk8 resolved=True, atk9 resolved=True. verify => correct holds; no verifying wrong impl found. Positive control (unmodified model.py) verifies (Verification successful, 9.9s).

Refinement.md audit: axioms region contains NO consumed @ContractOnly axiom (comment-only), so there are no A-consumed and no kind-3 legs. Every leg is R / A-reference / I (matches doc). A-reference legs (A6/A7/B2) validated by G-AX/axiom_check.py against the REAL gold-patched polylog.eval / _eval_expand_func. Code<->closed-form correspondence audited: model.py, axiom_check.py, and conformance_check.py share BYTE-IDENTICAL code/tag integer constants (0 mismatches); axiom_check gold_closed_form expressions (CF_P1=pi**2/12-log(2)**2/2, CF_P2=pi**2/4-I*pi*log(2), CF_SA=z/(1-z), CF_SB=z/(1-z)**2, EXP_PLAIN=-log(1-z) polar-free) match the gold patch.diff hunks exactly. G-AX status in meta.json = pass. The MustTerminate(2) obligations (legs A9/B3) are precisely what closes the one documented same-spec hole, confirmed live by atk_2/atk_7.

VERDICT SOUND: >=5 distinct attacks run (9 total), the prepatch bug reproduced, the named historical counterexample (oracle echo behind a diverging loop) re-encoded and REJECTED, and every verifying candidate's materialized faithful patch RESOLVES under run_resolve. No broken leg.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prepatch.py`, `atk_2_diverge_echo.py`, `atk_3_swap_p1p2.py`, `atk_4_drop_zc.py`, `atk_5_overfire.py`, `atk_6_exp_polar.py`, `atk_7_diverge_exp.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8_echo_term.py`, `atk_9_reorder_harmless.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_diverge_echo.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_swap_p1p2.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_drop_zc.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_overfire.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_exp_polar.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_diverge_exp.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_echo_term.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_reorder_harmless.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-13852.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A two-argument special function f(s, z) recognises a finite set of
      argument patterns and, for each recognised pattern, returns a closed-form
      value (an exact expression) instead of leaving the call unevaluated.
      Recognition is a PRIORITY CASCADE over the argument pair: some patterns are
      keyed on z alone and are checked first (so they win for any s); a further
      group is keyed on a particular s together with one of several distinguished
      z values; and two more patterns are keyed on s alone. A pattern matched
      earlier in the cascade takes priority over a later one when both could
      apply (e.g. a z-keyed pattern wins over an s-keyed pattern at the same
      argument). Any pair matching no pattern produces no closed form: the call
      stays unevaluated.

      Each recognised pattern must produce the closed-form value the function
      ACTUALLY takes there (validated against the real function by
      axiom_check.py / G-AX). Returning a different closed form for a recognised
      pattern, or leaving a recognised pattern unevaluated, does not meet the
      contract; neither does producing a closed form at an unrecognised pattern
      (the cascade must not over-fire).

  (2) The series-expansion of the same function at one distinguished value of s
      is an elementary closed form in (1 - z) carrying NO polar/branch factor on
      z. (The series-expansion at other s, an unchanged branch, is left to its
      existing behaviour and is not pinned here.)

Symbolic arguments and symbolic results are modelled as discrete tags / codes
(Nagini has no symbolic-algebra type): the matched argument pattern is an integer
tag, and the produced closed form is an integer code (the codes are opaque
distinct identifiers for the distinct closed forms — they carry no mathematical
meaning inside Nagini). A concrete per-pattern map (`closed_form_for`,
`expansion_code`) carries WHICH code each recognised pattern produces; that the
code-named closed form numerically EQUALS the real function at the pattern is the
out-of-band obligation checked by axiom_check.py (G-AX), not a consumed axiom.
The dispatch priority and the pattern -> code correspondence are what is verified
here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Closed-form result codes: opaque distinct identifiers, one per distinct closed
# form the cascade can produce. CF_UNEVAL marks "no closed form" (the call stays
# unevaluated). The remaining codes are pairwise distinct; their mathematical
# content is validated out-of-band (axiom_check.py / G-AX), not in Nagini.
CF_UNEVAL = 0       # no closed form: the call stays unevaluated
CF_ZA = 1           # closed form for the first z-keyed pattern    (z = z_a)
CF_ZB = 2           # closed form for the second z-keyed pattern   (z = z_b)
CF_ZC = 3           # closed form for the third z-keyed pattern    (z = z_c)
CF_P1 = 4           # closed form at the distinguished s, z = z_1
CF_P2 = 5           # closed form at the distinguished s, z = z_2
CF_P3 = 6           # closed form at the distinguished s, z = z_3
CF_P4 = 7           # closed form at the distinguished s, z = z_4
CF_P5 = 8           # closed form at the distinguished s, z = z_5
CF_P6 = 9           # closed form at the distinguished s, z = z_6
CF_SA = 10          # closed form for the first s-keyed pattern
CF_SB = 11          # closed form for the second s-keyed pattern

# Argument-pattern tags for the z component.
Z_A = 1             # z = z_a (first z-keyed value)
Z_B = 2             # z = z_b (second z-keyed value)
Z_C = 3             # z = z_c (third z-keyed value)
Z_1 = 4             # z = z_1 (first distinguished-s special argument)
Z_2 = 5             # z = z_2
Z_3 = 6             # z = z_3
Z_4 = 7             # z = z_4
Z_5 = 8             # z = z_5
Z_6 = 9             # z = z_6
Z_OTHER = 0         # any other z

# Distinguished s-predicate values the cascade branches on.
S_SPECIAL = 2       # the s value carrying the six special-z closed forms
S_KEY_A = 0         # the s value of the first s-keyed pattern
S_KEY_B = -1        # the s value of the second s-keyed pattern
S_EXPAND = 1        # the s value whose series-expansion is pinned in (2)

# Series-expansion codes for the distinguished-s expansion.
EXP_PLAIN = 1       # elementary closed form in (1 - z): NO polar/branch factor
EXP_POLAR = 2       # carries a polar/branch factor on z

# axioms-start
# (no consumed @ContractOnly axioms: the recognition cascade and the
# pattern -> closed-form correspondence are concrete control flow modelled
# directly. WHICH closed form is correct for each pattern is validated against
# the real function out-of-band by axiom_check.py / G-AX -- an A-reference, not
# a consumed axiom; see refinement.md.)
# axioms-end

# pure-start
@Pure
def closed_form_for(s: int, z_tag: int) -> int:
    """The closed-form code the function takes at argument pattern (s, z_tag),
    as a priority cascade. The z-keyed clauses are matched first (for any s),
    then the six distinguished-s special arguments, then the two s-keyed
    clauses; an unrecognised pattern yields no closed form (CF_UNEVAL).

    This map is concrete: it states only WHICH code each recognised pattern
    produces. That the produced closed form EQUALS the real function at the
    pattern is the G-AX obligation (axiom_check.py)."""
    Requires(0 <= z_tag and z_tag <= 9)
    # Priority 1: the z-keyed clauses, matched for any s.
    if z_tag == Z_A:
        return CF_ZA
    if z_tag == Z_B:
        return CF_ZB
    if z_tag == Z_C:
        return CF_ZC
    # Priority 2: the six special arguments at the distinguished s.
    if s == S_SPECIAL:
        if z_tag == Z_1:
            return CF_P1
        if z_tag == Z_2:
            return CF_P2
        if z_tag == Z_3:
            return CF_P3
        if z_tag == Z_4:
            return CF_P4
        if z_tag == Z_5:
            return CF_P5
        if z_tag == Z_6:
            return CF_P6
        return CF_UNEVAL
    # Priority 3: the two s-keyed closed forms.
    if s == S_KEY_A:
        return CF_SA
    if s == S_KEY_B:
        return CF_SB
    return CF_UNEVAL

@Pure
def expansion_code(s: int) -> int:
    """The series-expansion closed-form code at the distinguished s: the
    elementary closed form in (1 - z) with no polar/branch factor on z."""
    Requires(s == S_EXPAND)
    return EXP_PLAIN
# pure-end

def recognize_closed_form(s: int, z_tag: int) -> int:
    # pre-conditions-start
    Requires(0 <= z_tag and z_tag <= 9)
    # TERMINATION: the dispatch is a bounded, loop-free equality cascade — the
    # real function's value-dispatch always ANSWERS (returns a closed form or
    # falls through so the call stays unevaluated). Nagini is a
    # partial-correctness verifier by default; without this obligation a
    # non-terminating implementation (e.g. an infinite loop before an
    # unreachable return) satisfies every value Ensures vacuously. A diverging
    # dispatch would hang every construction of the function, so it does not
    # meet the contract.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly the closed-form code the recognition cascade picks
    # for the argument pattern: the z-keyed clauses win first (for any s), then
    # the distinguished-s special arguments, then the two s-keyed clauses; an
    # unrecognised pattern stays unevaluated. Pinning the full cascade forces
    # both the recognised closed forms AND their priority relative to the
    # z-keyed clauses.
    Ensures(Result() == closed_form_for(s, z_tag))
    # Each recognised pattern must produce an ACTUAL closed form (not stay
    # unevaluated): the third z-keyed clause, the special-s arguments, and the
    # two s-keyed clauses.
    Ensures(Implies(z_tag == Z_C, Result() == CF_ZC))
    Ensures(Implies(s == S_SPECIAL and z_tag == Z_1, Result() == CF_P1))
    Ensures(Implies(s == S_SPECIAL and z_tag == Z_2, Result() == CF_P2))
    Ensures(Implies(s == S_KEY_A and z_tag == Z_OTHER, Result() == CF_SA))
    Ensures(Implies(s == S_KEY_B and z_tag == Z_OTHER, Result() == CF_SB))
    # post-conditions-end
    # impl-start
    if z_tag == Z_A:
        return CF_ZA
    if z_tag == Z_B:
        return CF_ZB
    if z_tag == Z_C:
        return CF_ZC
    if s == S_SPECIAL:
        if z_tag == Z_1:
            return CF_P1
        if z_tag == Z_2:
            return CF_P2
        if z_tag == Z_3:
            return CF_P3
        if z_tag == Z_4:
            return CF_P4
        if z_tag == Z_5:
            return CF_P5
        if z_tag == Z_6:
            return CF_P6
        return CF_UNEVAL
    if s == S_KEY_A:
        return CF_SA
    if s == S_KEY_B:
        return CF_SB
    return CF_UNEVAL
    # impl-end

def series_expansion_at_one(s: int) -> int:
    # pre-conditions-start
    Requires(s == S_EXPAND)
    # TERMINATION: the distinguished-s expansion branch is a single return —
    # the real series-expansion always answers. Same partial-correctness hole
    # as recognize_closed_form: without the obligation a diverging impl passes
    # every Ensures vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The distinguished-s series-expansion is the elementary closed form in
    # (1 - z): NO polar/branch factor on z.
    Ensures(Result() == expansion_code(s))
    Ensures(Result() == EXP_PLAIN)
    Ensures(Result() != EXP_POLAR)
    # post-conditions-end
    # impl-start
    return EXP_PLAIN
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-13852 (nagini). Spec is TIGHT: recognize_closed_form's postcondition Ensures(Result()==closed_form_for(s,z_tag)) pins the return value over the ENTIRE Requires domain (0<=z_tag<=9, any s), and series_expansion_at_one pins Result()==EXP_PLAIN; both carry Requires(MustTerminate(2)). closed_form_for/expansion_code are concrete @Pure maps in the frozen spec region. Only the two impl regions were edited (all 9 attacks confirmed same-spec via adversary same-spec; atk_defs.py is only the generator).

9 attacks, run via `python -m swebench_unified.adversary weakness nagini sympy__sympy-13852 <atk>` (concurrent, <=3 JVM+Z3 at a time): atk_1_prepatch (only z-keyed clauses recognised): EXIT=2 NOT-A-COUNTEREXAMPLE, does not verify -> PREPATCH REPRODUCED (G-DIFF: postcondition senses the change). atk_2_diverge_echo (`while True: pass` then unreachable `return closed_form_for(s,z_tag)` -- the historical atk_8_oracle_echo hole): EXIT=2 does not verify.

MustTerminate(2) rejects it -> the spec-too-weak divergence hole is CLOSED. atk_3_swap_p1p2 (CF_P1<->CF_P2 at the two s=2 specials): EXIT=2 does not verify (wrong value). atk_4_drop_zc (Z_C -> CF_UNEVAL, boundary): EXIT=2 does not verify (explicit Implies(z_tag==Z_C,..)). atk_5_overfire (fall-through returns CF_SA at unrecognised patterns): EXIT=2 does not verify. atk_6_exp_polar (series_expansion_at_one returns EXP_POLAR, the prepatch polar form): EXIT=2 does not verify (Ensures Result()==EXP_PLAIN, !=EXP_POLAR). atk_7_diverge_exp (divergence in the EXPANSION fn then unreachable return EXP_PLAIN): EXIT=2 does not verify.

MustTerminate(2) on series_expansion_at_one holds too. atk_8_echo_term (`return closed_form_for(s,z_tag)` -- terminating echo of the @Pure map): EXIT=0 CANDIDATE (shares spec AND verifies, 9.3s). Behaviourally IDENTICAL to gold over s in [-100,100] x z_tag 0..9 (0 mismatches). Faithful refined patch = gold cascade VERBATIM. Materialized as patch_atk_8_echo_term.diff and run through the OFFICIAL harness: run_resolve -> resolved=True. Echo of a concrete @Pure map that IS the computation is a positive control (directive 8), not a cheat. atk_9_reorder_harmless (flattened `if s==S_SPECIAL and z_tag==Z_k` guards + explicit `if s==S_SPECIAL: return CF_UNEVAL`, structurally distinct but equivalent): EXIT=0 CANDIDATE (verifies, 10.4s). Behaviourally IDENTICAL to gold (0 mismatches). Faithful refined patch materialized as a FLATTENED gold eval cascade (patch_atk_9_reorder_harmless.diff, distinct source from gold verbatim) and run through the OFFICIAL harness: run_resolve -> resolved=True.

BOTH verifying CANDIDATEs' materialized faithful patches RESOLVE under the official harness (executed, not speculated): atk8 resolved=True, atk9 resolved=True. verify => correct holds; no verifying wrong impl found. Positive control (unmodified model.py) verifies (Verification successful, 9.9s).

Refinement.md audit: axioms region contains NO consumed @ContractOnly axiom (comment-only), so there are no A-consumed and no kind-3 legs. Every leg is R / A-reference / I (matches doc). A-reference legs (A6/A7/B2) validated by G-AX/axiom_check.py against the REAL gold-patched polylog.eval / _eval_expand_func. Code<->closed-form correspondence audited: model.py, axiom_check.py, and conformance_check.py share BYTE-IDENTICAL code/tag integer constants (0 mismatches); axiom_check gold_closed_form expressions (CF_P1=pi**2/12-log(2)**2/2, CF_P2=pi**2/4-I*pi*log(2), CF_SA=z/(1-z), CF_SB=z/(1-z)**2, EXP_PLAIN=-log(1-z) polar-free) match the gold patch.diff hunks exactly. G-AX status in meta.json = pass. The MustTerminate(2) obligations (legs A9/B3) are precisely what closes the one documented same-spec hole, confirmed live by atk_2/atk_7.

VERDICT SOUND: >=5 distinct attacks run (9 total), the prepatch bug reproduced, the named historical counterexample (oracle echo behind a diverging loop) re-encoded and REJECTED, and every verifying candidate's materialized faithful patch RESOLVES under run_resolve. No broken leg.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO diverging input. Verified against the real gold-patched callee in the /tmp worktree (patch.diff applied to sympy/functions/special/zeta_functions.py at base_commit c935e1d1). Checks run with python +:

(1) Firing/quotient fidelity: over s in {2,0,-1,1,3,5,-2} x all 10 z-tags, model()!=CF_UNEVAL iff real polylog(s,z) actually auto-evaluates (does not remain a polylog instance). No over-fire (s=2,z=1/3; s=3,z=1/2; generic z -> unevaluated) and no under-fire. Matches on every pair.

(2) Closed-form A-references numeric: all six s=2 specials equal real polylog(2,z) to <1e-25 and are pairwise distinct (distinct codes justified). z=0->S.Zero, s=0->z/(1-z), s=-1->z/(1-z)**2 confirmed.

(3) Priority cascade: z-keyed clauses win over s-keyed at conflicts — polylog(0,1)=zeta(0)=-1/2 (not z/(1-z) div-by-zero), polylog(-1,1)=-1/12, polylog(*,0)=0. Exactly closed_form_for's ordering.

(4) s=1 expansion: expand_func(polylog(1,1/3)) = -log(2)+log(3), exp_polar-free (EXP_PLAIN). Matches gold.

(5) Type abstraction faithful: 9 z-anchors numerically distinct, dispatch constant per class.

(6) Bundle verifies (nagini_verify.sh: 'Verification successful', 8.74s) => spec non-vacuous; MustTerminate closes the vacuity hole. Spec region intact.

The spec is a conjunction the gold patch satisfies in full and is at-least-as-strong as the gold fix, not drifting/too-strong-relative-to-behavior. No input where the modeled function disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view (spec_view over model.py, impl regions elided) does not leak the gold edit beyond the public problem_statement.

Gold edit content: polylog.eval closed forms (z==1->zeta(s); z==-1->-dirichlet_eta(s); z==0->S.Zero; six s==2 dilog forms in pi**2/log at golden-ratio/rational z; s==0->z/(1-z); s==-1->z/(1-z)**2) and _eval_expand_func s==1 -> -log(1-z) (exp_polar-free).

Every mathematical closed form is fully abstracted behind opaque integer codes (CF_UNEVAL, CF_ZA/ZB/ZC, CF_P1..P6, CF_SA/SB, EXP_PLAIN/EXP_POLAR). Confirmed absent from the spec view: polylog, zeta, dirichlet, dilog, sqrt, S.Zero, S.Half, log(2), pi**2, z/(1-z), -log, golden-ratio points, zeta_functions, the patched file path, diff markers, and fix/bug narration. The only 'polar/branch factor' vocabulary present (EXP_POLAR, prose 'polar/branch factor') is already disclosed in the public problem_statement, which explicitly discusses exp_polar in expand_func(polylog(1,z)). The '1 - z' substring in the spec is generic prose ('elementary closed form in (1 - z)'), not the reproduced patched line -log(1-z).

The concrete int carriers S_SPECIAL=2 / S_KEY_A=0 / S_KEY_B=-1 / S_EXPAND=1 are the genuine polylog orders and are an R-refinement of the SymPy expression s; they disclose only WHERE special-casing occurs, never the closed-form content. s==2 and s==1 are already surfaced in problem_statement (polylog(2,Rational(1,2)) and the exp_polar-of-polylog(1,z) discussion); s==0/s==-1 go slightly beyond it as locations only, revealing no edit content and insufficient to reconstruct the gold patch.

Mechanical G-LEAK screen (leakage.screen against gold patch + problem_statement) PASSES with zero hard failures; bundle is not relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md); recorded G-LEAK status=pass. A solver seeing this spec view cannot reproduce the gold patch: the discriminating mathematics is held out-of-band in axiom_check.py/G-AX. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.