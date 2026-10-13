# P2 adversarial audit — sympy__sympy-19637

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_prepatch.lean`, `atk_2_alwaystrue.lean`, `atk_3_underscore.lean`, `atk_4_swapped.lean`, `atk_5_echo.lean`, `atk_6_length.lean`, `atk_7_tab.lean`, `atk_8_alwaysfalse.lean`, `atk_11_head.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9_decide.lean`, `atk_10_notnot.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,13 +53,9 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
     let out : Except MarkerError Bool :=
       if s.contains ' ' then Except.ok true
-      else Except.ok false
+      else Except.error MarkerError.markerUnavailable
     return out
     -- impl-end
 
```

Attack 2 — `atk_2_alwaystrue.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,13 +53,7 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
-    let out : Except MarkerError Bool :=
-      if s.contains ' ' then Except.ok true
-      else Except.ok false
+    let out : Except MarkerError Bool := Except.ok true
     return out
     -- impl-end
 
```

Attack 3 — `atk_3_underscore.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,13 +53,7 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
-    let out : Except MarkerError Bool :=
-      if s.contains ' ' then Except.ok true
-      else Except.ok false
+    let out : Except MarkerError Bool := Except.ok (s.contains '_')
     return out
     -- impl-end
 
```

Attack 4 — `atk_4_swapped.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,13 +53,9 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
     let out : Except MarkerError Bool :=
-      if s.contains ' ' then Except.ok true
-      else Except.ok false
+      if s.contains ' ' then Except.ok false
+      else Except.ok true
     return out
     -- impl-end
 
```

Attack 5 — `atk_5_echo.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,14 +53,7 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
-    let out : Except MarkerError Bool :=
-      if s.contains ' ' then Except.ok true
-      else Except.ok false
-    return out
+    return Except.ok (markerFlag s)
     -- impl-end
 
 prove_correct markerPresent by
```

Attack 6 — `atk_6_length.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,13 +53,7 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
-    let out : Except MarkerError Bool :=
-      if s.contains ' ' then Except.ok true
-      else Except.ok false
+    let out : Except MarkerError Bool := Except.ok (decide (s.length > 0))
     return out
     -- impl-end
 
```

Attack 7 — `atk_7_tab.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,13 +53,8 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
     let out : Except MarkerError Bool :=
-      if s.contains ' ' then Except.ok true
-      else Except.ok false
+      Except.ok (s.contains ' ' || s.contains '\t')
     return out
     -- impl-end
 
```

Attack 8 — `atk_8_alwaysfalse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,13 +53,7 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
-    let out : Except MarkerError Bool :=
-      if s.contains ' ' then Except.ok true
-      else Except.ok false
+    let out : Except MarkerError Bool := Except.ok false
     return out
     -- impl-end
 
```

Attack 9 — `atk_9_decide.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -53,12 +53,8 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
     let out : Except MarkerError Bool :=
-      if s.contains ' ' then Except.ok true
+      if h : s.contains ' ' = true then Except.ok true
       else Except.ok false
     return out
     -- impl-end
```

Attack 10 — `atk_10_notnot.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -53,13 +53,9 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
     let out : Except MarkerError Bool :=
-      if s.contains ' ' then Except.ok true
-      else Except.ok false
+      if !(s.contains ' ') then Except.ok false
+      else Except.ok true
     return out
     -- impl-end
 
```

Attack 11 — `atk_11_head.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,13 +53,10 @@
   ensures out = Except.ok (markerFlag s)
   do
     -- impl-start
-    -- Decide the flag from whether a substitution marker is present in `s`,
-    -- branching so BOTH paths yield a value: when a marker is present the flag
-    -- is the membership result; when none is present the flag is `false`. The
-    -- step always returns the success leg — it never surfaces the failure leg.
     let out : Except MarkerError Bool :=
-      if s.contains ' ' then Except.ok true
-      else Except.ok false
+      match s with
+      | [] => Except.ok false
+      | c :: _ => Except.ok (decide (c = ' '))
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The recoverable failure shape of the marker-presence step: the step is asked
   to report a flag, and on one path the earlier-stage value it consults has
   never been established. Reifying that "value not established" outcome as the
   error leg of `Except` lets the desired behavior insist the step is TOTAL — it
   must always yield a flag and never surface this failure. This is the only
   failure the desired behavior distinguishes. -/
inductive MarkerError where
  | markerUnavailable
  deriving DecidableEq
-- axioms-end

-- pure-start
/- The intended value of the marker-presence flag for a working string `s`:
   `true` exactly when a substitution marker is present in `s`, `false`
   otherwise. The flag is total — defined for every `s` — and is the membership
   of the distinguished marker code point in `s` (mapping.md §2, §3). -/
def markerFlag (s : List Char) : Bool :=
  s.contains ' '
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Report whether a substitution marker is present in a working string, as a
   flag consulted by a later recovery step.

   Desired behavior: the step inspects the working string `s` and decides the
   flag from whether a substitution marker was introduced into it. When a marker
   is present the flag is set accordingly; when no marker is present the flag is
   simply `false`. The step is TOTAL: for every working string it yields a flag
   and never fails — in particular it must still yield `false` (not surface a
   failure) on the path where no marker was ever introduced. The result is the
   success leg carrying the flag (`out = Except.ok (markerFlag s)`); the failure
   leg is never produced.

   `s` is the read-only working string (not `mut`): the step inspects it and
   mutates nothing (directive 5). The string is modeled as a `List Char` (a
   per-code-point string) and the marker as the distinguished space code point
   (mapping.md §2). -/
method markerPresent (s : List Char) return (out : Except MarkerError Bool)
  ensures out = Except.ok (markerFlag s)
  do
    -- impl-start
    -- Decide the flag from whether a substitution marker is present in `s`,
    -- branching so BOTH paths yield a value: when a marker is present the flag
    -- is the membership result; when none is present the flag is `false`. The
    -- step always returns the success leg — it never surfaces the failure leg.
    let out : Except MarkerError Bool :=
      if s.contains ' ' then Except.ok true
      else Except.ok false
    return out
    -- impl-end

prove_correct markerPresent by
  loom_solve
  simp only [markerFlag]
  split <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec's postcondition `ensures out = Except.ok (markerFlag s)` with the FROZEN pure def `markerFlag s = s.contains ' '` pins the output UNIQUELY and TOTALLY for every s: any verifying impl must return exactly Except.ok (s.contains ' ') on every input — the gold total-flag behavior. There is zero behavioral slack, so no verifying WRONG impl exists.

Same-spec check: all 11 attacks + positive control gave same_spec=True (verified via swebench_unified.markers.same_spec, velvet backend). Negative control confirms same_spec is discriminating: tampering the pure region (markerFlag -> s.contains (Char.ofNat 65)) => False; tampering the ensures (=> Except.ok true) => False.

Verification results (scripts/lean_verify.sh, 300s cap, run concurrently <=4):
- positive_control (gold two-branch): exit 0 VERIFIES.
- atk_1_prepatch (error leg on no-space path): exit 1, fails on goal `' ' \notin s |- False` — PREPATCH BUG REPRODUCED on exactly the else/no-marker path (matches G-DIFF).
- atk_2_alwaystrue (Except.ok true): exit 1 rejected.
- atk_3_underscore (s.contains '_', ungrounded-oracle echo of kern seed): exit 1 rejected.
- atk_4_swapped (branches swapped): exit 1 rejected.
- atk_5_echo (return Except.ok (markerFlag s); behaviorally correct): exit 1 — fails ONLY on the frozen proof script (`split` -> "No goals to be solved"), NOT a spec weakness; behaviorally gold-equivalent.
- atk_6_length (decide (s.length>0)): exit 1 rejected.
- atk_7_tab (space OR tab): exit 1 rejected.
- atk_8_alwaysfalse (Except.ok false): exit 1, fails on `Except.ok false = Except.ok (s.contains ' ')` — rejected.
- atk_9_decide (if s.contains ' ' = true then ok true else ok false): exit 0 VERIFIES — behaviorally CORRECT (= s.contains ' ', gold-equivalent), NOT a wrong impl.
- atk_10_notnot (double-negated control flow, = s.contains ' '): exit 0 VERIFIES — behaviorally CORRECT, NOT a wrong impl.
- atk_11_head (match on head char only): exit 1, fails on `decide (c = ' ') = (decide (' ' = c) || decide (' ' \in tail))` — genuinely WRONG (differs on e.g. "x ") and correctly rejected.

RESOLVE (protocol §2): the only impls that verify (atk_9, atk_10) are gold-equivalent; their faithful patch is exactly the gold total-flag step (kern identity, mapping.md §3). Materialized to faithful_patch_atk9_atk10.diff and RUN through the official harness: run_resolve("sympy__sympy-19637", patch, timeout=1200) => RESOLVED=True COMPLETED=True NOTE=resolved ATTEMPTS=1. So every verifying impl's faithful patch RESOLVES — verify=>correct holds; no break.

Refinement.md audit (§3): every leg is R or I (A1=R, A2=I+R, A3=I+R, A4=R; the §A/§B/§C are section-letter headers, not A-tags). NO A-consumed and NO A-reference legs, NO kind-3 steps. meta.json corroborates: axioms=[], deep_model_references=[], G-AX=skip (no axiom_check.py). The only deep correspondence is mapping.md §3's marker identity `kern in s <=> ' ' in s`, tagged I+R (concrete per-code-point membership modeled directly). Verified against the real repo at base_commit 63f8f465: pre-patch has `hit = kern in s` at the outer if-level (UnboundLocalError on no-space path); post-patch moves it inside `if ' ' in s:` and adds `else: hit = False`. kern is chosen ABSENT from s (while kern in s loop) then every space -> kern, so post-replace `kern in s` iff s had a space iff ' ' in s; else branch is exactly ' ' not in s where hit=False. Correspondence FAITHFUL. G-CONF (100013 strings, seed 19637, 0 disagreements) and G-RESOLVE (pass) corroborate.

MODEL<->PATCH correspondence holds; no verifying wrong impl; the verifying (correct) impls' faithful patch resolves. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1_prepatch.lean`, `atk_2_alwaystrue.lean`, `atk_3_underscore.lean`, `atk_4_swapped.lean`, `atk_5_echo.lean`, `atk_6_length.lean`, `atk_7_tab.lean`, `atk_8_alwaysfalse.lean`, `atk_11_head.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9_decide.lean`, `atk_10_notnot.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_alwaystrue.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_underscore.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_swapped.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_echo.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_length.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_tab.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_alwaysfalse.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_decide.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_notnot.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_head.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The recoverable failure shape of the marker-presence step: the step is asked
   to report a flag, and on one path the earlier-stage value it consults has
   never been established. Reifying that "value not established" outcome as the
   error leg of `Except` lets the desired behavior insist the step is TOTAL — it
   must always yield a flag and never surface this failure. This is the only
   failure the desired behavior distinguishes. -/
inductive MarkerError where
  | markerUnavailable
  deriving DecidableEq
-- axioms-end

-- pure-start
/- The intended value of the marker-presence flag for a working string `s`:
   `true` exactly when a substitution marker is present in `s`, `false`
   otherwise. The flag is total — defined for every `s` — and is the membership
   of the distinguished marker code point in `s` (mapping.md §2, §3). -/
def markerFlag (s : List Char) : Bool :=
  s.contains ' '
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Report whether a substitution marker is present in a working string, as a
   flag consulted by a later recovery step.

   Desired behavior: the step inspects the working string `s` and decides the
   flag from whether a substitution marker was introduced into it. When a marker
   is present the flag is set accordingly; when no marker is present the flag is
   simply `false`. The step is TOTAL: for every working string it yields a flag
   and never fails — in particular it must still yield `false` (not surface a
   failure) on the path where no marker was ever introduced. The result is the
   success leg carrying the flag (`out = Except.ok (markerFlag s)`); the failure
   leg is never produced.

   `s` is the read-only working string (not `mut`): the step inspects it and
   mutates nothing (directive 5). The string is modeled as a `List Char` (a
   per-code-point string) and the marker as the distinguished space code point
   (mapping.md §2). -/
method markerPresent (s : List Char) return (out : Except MarkerError Bool)
  ensures out = Except.ok (markerFlag s)
  do
    -- impl-start
    -- Decide the flag from whether a substitution marker is present in `s`,
    -- branching so BOTH paths yield a value: when a marker is present the flag
    -- is the membership result; when none is present the flag is `false`. The
    -- step always returns the success leg — it never surfaces the failure leg.
    let out : Except MarkerError Bool :=
      if s.contains ' ' then Except.ok true
      else Except.ok false
    return out
    -- impl-end

prove_correct markerPresent by
  loom_solve
  simp only [markerFlag]
  split <;> simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen spec's postcondition `ensures out = Except.ok (markerFlag s)` with the FROZEN pure def `markerFlag s = s.contains ' '` pins the output UNIQUELY and TOTALLY for every s: any verifying impl must return exactly Except.ok (s.contains ' ') on every input — the gold total-flag behavior. There is zero behavioral slack, so no verifying WRONG impl exists.

Same-spec check: all 11 attacks + positive control gave same_spec=True (verified via swebench_unified.markers.same_spec, velvet backend). Negative control confirms same_spec is discriminating: tampering the pure region (markerFlag -> s.contains (Char.ofNat 65)) => False; tampering the ensures (=> Except.ok true) => False.

Verification results (scripts/lean_verify.sh, 300s cap, run concurrently <=4):
- positive_control (gold two-branch): exit 0 VERIFIES.
- atk_1_prepatch (error leg on no-space path): exit 1, fails on goal `' ' \notin s |- False` — PREPATCH BUG REPRODUCED on exactly the else/no-marker path (matches G-DIFF).
- atk_2_alwaystrue (Except.ok true): exit 1 rejected.
- atk_3_underscore (s.contains '_', ungrounded-oracle echo of kern seed): exit 1 rejected.
- atk_4_swapped (branches swapped): exit 1 rejected.
- atk_5_echo (return Except.ok (markerFlag s); behaviorally correct): exit 1 — fails ONLY on the frozen proof script (`split` -> "No goals to be solved"), NOT a spec weakness; behaviorally gold-equivalent.
- atk_6_length (decide (s.length>0)): exit 1 rejected.
- atk_7_tab (space OR tab): exit 1 rejected.
- atk_8_alwaysfalse (Except.ok false): exit 1, fails on `Except.ok false = Except.ok (s.contains ' ')` — rejected.
- atk_9_decide (if s.contains ' ' = true then ok true else ok false): exit 0 VERIFIES — behaviorally CORRECT (= s.contains ' ', gold-equivalent), NOT a wrong impl.
- atk_10_notnot (double-negated control flow, = s.contains ' '): exit 0 VERIFIES — behaviorally CORRECT, NOT a wrong impl.
- atk_11_head (match on head char only): exit 1, fails on `decide (c = ' ') = (decide (' ' = c) || decide (' ' \in tail))` — genuinely WRONG (differs on e.g. "x ") and correctly rejected.

RESOLVE (protocol §2): the only impls that verify (atk_9, atk_10) are gold-equivalent; their faithful patch is exactly the gold total-flag step (kern identity, mapping.md §3). Materialized to faithful_patch_atk9_atk10.diff and RUN through the official harness: run_resolve("sympy__sympy-19637", patch, timeout=1200) => RESOLVED=True COMPLETED=True NOTE=resolved ATTEMPTS=1. So every verifying impl's faithful patch RESOLVES — verify=>correct holds; no break.

Refinement.md audit (§3): every leg is R or I (A1=R, A2=I+R, A3=I+R, A4=R; the §A/§B/§C are section-letter headers, not A-tags). NO A-consumed and NO A-reference legs, NO kind-3 steps. meta.json corroborates: axioms=[], deep_model_references=[], G-AX=skip (no axiom_check.py). The only deep correspondence is mapping.md §3's marker identity `kern in s <=> ' ' in s`, tagged I+R (concrete per-code-point membership modeled directly). Verified against the real repo at base_commit 63f8f465: pre-patch has `hit = kern in s` at the outer if-level (UnboundLocalError on no-space path); post-patch moves it inside `if ' ' in s:` and adds `else: hit = False`. kern is chosen ABSENT from s (while kern in s loop) then every space -> kern, so post-replace `kern in s` iff s had a space iff ' ' in s; else branch is exactly ' ' not in s where hit=False. Correspondence FAITHFUL. G-CONF (100013 strings, seed 19637, 0 disagreements) and G-RESOLVE (pass) corroborate.

MODEL<->PATCH correspondence holds; no verifying wrong impl; the verifying (correct) impls' faithful patch resolves. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real callee) confirmed for sympy__sympy-19637 velvet.

What is modeled: `markerPresent (s : List Char)` with `ensures out = Except.ok (markerFlag s)`, `markerFlag s = s.contains ' '`. Models the flag step of kernS (sympy/core/sympify.py, post-patch lines 516-518).

Real callee (post-patch gold):
  if ' ' in s:
      kern='_'; while kern in s: kern += choice(...); s=s.replace(' ',kern); hit = kern in s
  else:
      hit = False

Equivalence argument (exact, not sampled): inside the branch kern is chosen ABSENT from s (the while loop), then substituted for every space, so `kern in s` is necessarily True there; the branch is entered iff `' ' in s`. The else path yields False and is entered iff no space. Hence hit == (' ' in s) on every working string == s.contains ' ' under the str↔List Char / marker↔space-codepoint bijection (mapping.md §2,§3). Totality also holds: the while loop terminates on any finite string and no raise occurs post-patch, so the spec's 'always Except.ok, never error leg' matches the real callee, which never raises or diverges.

Checks performed:
- same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True → spec region (axioms/pure/pre/post/signature+ensures) is byte-identical; only the impl region differs (prepatch surfaces Except.error on the no-space path). Spec is not silently strengthened.
- scripts/lean_verify.sh Solution.lean → EXIT 0 (elaborates, no sorry/error; prove_correct discharged).
- conformance_check.py replayed the REAL gold control flow (oracle_marker) vs the R/I shadow over 100013 working strings (seed 19637), including boundary cases '' , ' ', '  ', 'x', '(2*x)/(x-1)' (F2P), '_', 'abc_def', leading/trailing spaces: 0 disagreements.

Searched for a diverging input where the modeled markerFlag disagrees with the real kernS flag: none exists. The kern-collision/multi-char-kern subtleties are observationally irrelevant to the flag (kern always present inside branch). The spec constrains exactly the value the gold computes — not too strong, no drift. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean projected via markers.spec_view for velvet backend) judged for leakage of the gold edit beyond the PUBLIC problem_statement (hints_text excluded; empty here anyway).

Gold edit (patch.diff): indent `hit = kern in s` into the `if ' ' in s:` branch and add `else: hit = False`, making the flag step total instead of raising UnboundLocalError on the no-marker path.

Public problem_statement ALREADY discloses: the function `kernS`, the offending line `hit = kern in s`, and `UnboundLocalError: local variable 'kern' referenced before assignment`. So the bug, its exact failing line, and the error class are all public.

Spec-view content: describes a marker-presence flag step (`markerPresent`/`markerFlag`/`MarkerError`) that is TOTAL — always `Except.ok`, yielding `false` on the no-marker path. This is a behavioral requirement, not a reproduction of the edit:
- No gold-patch line reproduced (normalized check: `hit=kernins`, `else:`, `hit=False` absent from the Lean spec view).
- No patched repo symbol leaked: identifiers are markerPresent/markerFlag/MarkerError/s/out — none echoes `kernS`, `kern`, or `hit`; the patched path `sympy/core/sympify.py` and dotted module are absent.
- No diff markers; no narration terms (bug/fix/pre-patch/broken/…). Mechanical leakage.screen() PASSES with zero hard_failures.
- The auditor-only docs (mapping.md, refinement.md) that DO quote the gold hunk and name kernS/kern are NOT part of the consumer spec view, so they are out of scope for G-LEAK.

The totality-of-the-flag-step requirement is the intrinsic behavioral goal any faithful spec of this fix must state; it does not reconstruct the gold beyond what the problem_statement already makes public. same_spec(Solution, Solution_prepatch)=True (byte-identical spec region). meta G-LEAK status=pass, no relaxed_leakage flag, no RELAXED_LEAKAGE.md — no deferral needed. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
