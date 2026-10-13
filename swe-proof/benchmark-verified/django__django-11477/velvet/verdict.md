# P2 adversarial audit — django__django-11477

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-wrong TERMINATING implementation exists; the spec pins both outputs as exact functions of the inputs (out.named = keepPresent namedGroups; out.positional = if out.named=[] then positionalGroups else []). The only verifying wrong impl is a divergent while-true loop (atk_2), which is an out-of-scope partial-correctness artifact — see notes.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (none) The modeled operation post-processes values already produced by the
@@ -58,12 +58,11 @@
     let mut i := namedGroups.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ namedGroups.length
-      invariant result = keepPresent (namedGroups.drop i)
+      invariant result = namedGroups.drop i
       done_with i = 0
-      decreasing i
     do
       let p := namedGroups[i - 1]!
-      result := keepOne p ++ result
+      result := p :: result
       i := i - 1
     return ⟨result, if result = [] then positionalGroups else []⟩
     -- impl-end
```

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (none) The modeled operation post-processes values already produced by the
@@ -58,9 +58,8 @@
     let mut i := namedGroups.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ namedGroups.length
-      invariant result = keepPresent (namedGroups.drop i)
+      invariant result = keepPresent (namedGroups.drop (i - 1))
       done_with i = 0
-      decreasing i
     do
       let p := namedGroups[i - 1]!
       result := keepOne p ++ result
```

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (none) The modeled operation post-processes values already produced by the
@@ -60,12 +60,11 @@
       invariant 0 ≤ i ∧ i ≤ namedGroups.length
       invariant result = keepPresent (namedGroups.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := namedGroups[i - 1]!
       result := keepOne p ++ result
       i := i - 1
-    return ⟨result, if result = [] then positionalGroups else []⟩
+    return ⟨result, positionalGroups⟩
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 4 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (none) The modeled operation post-processes values already produced by the
@@ -54,18 +54,8 @@
   ensures out.positional = (if out.named = [] then positionalGroups else [])
   do
     -- impl-start
-    let mut result : List Named := []
-    let mut i := namedGroups.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ namedGroups.length
-      invariant result = keepPresent (namedGroups.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let p := namedGroups[i - 1]!
-      result := keepOne p ++ result
-      i := i - 1
-    return ⟨result, if result = [] then positionalGroups else []⟩
+    let named := keepPresent namedGroups
+    return ⟨named, if named = [] then positionalGroups else []⟩
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -84,5 +74,3 @@
 
 prove_correct bindCaptures by
   loom_solve
-  rw [keepPresent_drop_step namedGroups i (by omega) (by omega)]
-  simp_all
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (none) The modeled operation post-processes values already produced by the
@@ -60,10 +60,9 @@
       invariant 0 ≤ i ∧ i ≤ namedGroups.length
       invariant result = keepPresent (namedGroups.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := namedGroups[i - 1]!
-      result := keepOne p ++ result
+      result := (if p.2.isNone then [p] else []) ++ result
       i := i - 1
     return ⟨result, if result = [] then positionalGroups else []⟩
     -- impl-end
```

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (none) The modeled operation post-processes values already produced by the
@@ -55,16 +55,15 @@
   do
     -- impl-start
     let mut result : List Named := []
-    let mut i := namedGroups.length
-    while i > 0
+    let mut i := 0
+    while i < namedGroups.length
       invariant 0 ≤ i ∧ i ≤ namedGroups.length
-      invariant result = keepPresent (namedGroups.drop i)
-      done_with i = 0
-      decreasing i
+      invariant result = keepPresent (namedGroups.take i)
+      done_with i = namedGroups.length
     do
-      let p := namedGroups[i - 1]!
-      result := keepOne p ++ result
-      i := i - 1
+      let p := namedGroups[i]!
+      result := result ++ keepOne p
+      i := i + 1
     return ⟨result, if result = [] then positionalGroups else []⟩
     -- impl-end
 
@@ -83,6 +82,15 @@
   rw [hcons, keepPresent_cons]
 
 prove_correct bindCaptures by
+  have kp_app : ∀ (xs ys : List Named), keepPresent (xs ++ ys) = keepPresent xs ++ keepPresent ys := by
+    intro xs ys
+    induction xs with
+    | nil => simp [keepPresent]
+    | cons a rest ih => simp [keepPresent_cons, ih, List.append_assoc]
   loom_solve
-  rw [keepPresent_drop_step namedGroups i (by omega) (by omega)]
-  simp_all
+  · have hlt : i < namedGroups.length := by omega
+    have hget : namedGroups[i]! = namedGroups[i] := by
+      rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
+    rw [invariant_2, List.take_succ_eq_append_getElem hlt, kp_app, hget]
+    simp [keepPresent]
+  all_goals simp_all
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (none) The modeled operation post-processes values already produced by the
@@ -56,11 +56,10 @@
     -- impl-start
     let mut result : List Named := []
     let mut i := namedGroups.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ namedGroups.length
       invariant result = keepPresent (namedGroups.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = 1
     do
       let p := namedGroups[i - 1]!
       result := keepOne p ++ result
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (none) The modeled operation post-processes values already produced by the
@@ -60,12 +60,11 @@
       invariant 0 ≤ i ∧ i ≤ namedGroups.length
       invariant result = keepPresent (namedGroups.drop i)
       done_with i = 0
-      decreasing i
     do
       let p := namedGroups[i - 1]!
       result := keepOne p ++ result
       i := i - 1
-    return ⟨result, if result = [] then positionalGroups else []⟩
+    return ⟨result, []⟩
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (none) The modeled operation post-processes values already produced by the
-- pattern engine; it calls no further routine whose contract must be assumed.
-- axioms-end

-- pure-start
/- A captured named group: its name paired with the value the engine bound to
   it, or `none` when the group took part in no alternative that actually
   participated in the overall capture (an optional group that contributed
   nothing). -/
abbrev Named := String × Option String

/- Per-group contribution to the keyword bindings: a group that bound a value
   contributes itself; a group that bound nothing contributes nothing. -/
def keepOne (p : Named) : List Named :=
  if p.2.isSome then [p] else []

/- The keyword bindings of a whole capture list: concatenate the per-group
   contributions, in order. Front-recursive so a single unfold is available per
   loop step (the fold pattern). -/
def keepPresent : List Named → List Named
  | []      => []
  | p :: ps => keepOne p ++ keepPresent ps

@[grind] lemma keepPresent_nil : keepPresent [] = [] := rfl
@[grind] lemma keepPresent_cons (p : Named) (ps : List Named) :
    keepPresent (p :: ps) = keepOne p ++ keepPresent ps := rfl
-- pure-end

/- The result of binding a single capture: the keyword bindings, plus the
   positional bindings (used only when there are no keyword bindings). -/
structure Bindings where
  named : List Named
  positional : List String
deriving Repr, Inhabited

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method bindCaptures (namedGroups : List Named) (positionalGroups : List String)
    return (out : Bindings)
  ensures out.named = keepPresent namedGroups
  ensures out.positional = (if out.named = [] then positionalGroups else [])
  do
    -- impl-start
    let mut result : List Named := []
    let mut i := namedGroups.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ namedGroups.length
      invariant result = keepPresent (namedGroups.drop i)
      done_with i = 0
    do
      let p := namedGroups[i - 1]!
      result := keepOne p ++ result
      i := i - 1
    return ⟨result, if result = [] then positionalGroups else []⟩
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `keepPresent` peels one `keepOne`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma keepPresent_drop_step (xs : List Named) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    keepPresent (xs.drop (i - 1)) = keepOne xs[i - 1]! ++ keepPresent (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keepPresent_cons]

prove_correct bindCaptures by
  loom_solve
  rw [keepPresent_drop_step namedGroups i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: bindCaptures has NO precondition and TWO exact-equality postconditions over concrete pure functions keepOne/keepPresent — the strongest possible shape. same_spec elides only the impl region and the prove_correct body (verified against markers.spec_view), so a legitimate alternative impl ships its OWN proof; the helper lemma keepPresent_drop_step is in the spec view and was kept byte-identical in every attack. All 10 candidate files confirmed same_spec=True.

### VERIFY TALLY (scripts/lean_verify.sh <file>, run concurrently ≤4):
- pos_control.lean (baseline backward while-fold, correct): exit 0 — POSITIVE CONTROL verifies.
- atk_5.lean (ungrounded-oracle ECHO: `let named := keepPresent namedGroups; return ⟨named, …⟩`, correct): exit 0 — verifies (structurally different correct alt).
- atk_7.lean (control-flow variant: FORWARD fold `result ++ keepOne p`, take-based invariant + own inline keepPresent_append proof, correct): exit 0 — verifies (2nd correct alt).
- atk_1.lean (PREPATCH bug: keep-all, no filter, `result := p :: result`): exit 1 — REJECTED on ensures_1 `out.named = keepPresent namedGroups` (invariant result = namedGroups.drop i cannot discharge the filtered post). Prepatch reproduced.
- atk_3.lean (keep-all with keepPresent/drop invariant mismatch): exit 1 — REJECTED, residual keepOne … ++ result = keepPresent (drop (i-1-1)).
- atk_4.lean (correct named, positional ALWAYS = positionalGroups): exit 1 — REJECTED on ensures_2 (needs keepPresent namedGroups=[] to justify positionalGroups when named≠[]).
- atk_6.lean (INVERTED filter: keep when isNone): exit 1 — REJECTED, residual (if isNone then [p] else []) = keepOne p (false for present groups).
- atk_8.lean (BOUNDARY off-by-one: loop `i>1`, skips first element): exit 1 — REJECTED on done_1 (i=1 leaves one element unprocessed).
- atk_9.lean (positional ALWAYS []): exit 1 — REJECTED on ensures_2 (when out.named=[] must return positionalGroups, returns []).
Every wrong TERMINATING impl is rejected; both correct alternatives verify. Spec is TIGHT.

### EXECUTED HARNESS EVIDENCE (run_resolve):
- GOLD/echo patch (the faithful refined patch of atk_5 AND atk_7 — both compute the present-only filter + emptiness-guarded positional, i.e. exactly `kwargs = {k:v for … if v is not None}` and the unchanged args line): `RESOLVE resolved=True completed=True note='resolved'`. verify⇒correct confirmed on the F2P/P2P suite (test_re_path_with_optional_parameter, test_two_variable_at_start_of_path_pattern, test_translate_url_utility).

DIVERGENCE PROBE (atk_2, atk_2.lean) — DELIBERATELY NOT SUBMITTED AS A BREAKING ATTACK: a `while true … done_with False` loop with its own proof (`loom_solve`). same_spec=True, lean_verify exit 0 (no sorry; #print axioms of the baseline = [propext, Classical.choice, Quot.sound], genuine). It verifies because `set_option loom.semantics.termination "partial"` (part of the FROZEN spec view, and a framework-blessed setting per spec_guide.md:112/quickref.md:6) makes any postcondition VACUOUSLY true of a divergent program. This is a UNIVERSAL partial-correctness artifact (it would 'break' every partial-correctness velvet/lean bundle identically), NOT a refinement-fidelity defect:

(1) a `while True` loop refines NONE of refinement.md's mapped output-producing ops A1–A5, so it has no faithful refined patch under the map — refinement.md §D scopes the twin guarantee to a model 'refined by the map above';

(2) the correctness oracle is G-RESOLVE, and the gold obviously terminates. I still MATERIALIZED a strawman divergent patch (atk_2_patch.diff: inserts `while True: pass` before the kwargs assignment) and RAN it: `RESOLVE resolved=False completed=False note='no report … harness error'` — i.e. INCONCLUSIVE, NOT the derivation's BROKEN path (`r.completed and not r.resolved`). A divergent patch can never be completed-but-unresolved, so the framework's own mechanization does not count divergence as a spec weakness. Submitting atk_2 would only fail-close the gate to INCONCLUSIVE on a resolve that cannot complete — a spurious result — so it is documented here rather than listed.

REFINEMENT.md LEG AUDIT (A-leg focus): meta.json axioms=[], deep_model_references=[], additional_change_sites=[]. Solution.lean has zero banned tokens (no sorry/admit/native_decide/Classical.choice/unsafe/extern). #print axioms bindCaptures_correct = [propext, Classical.choice, Quot.sound] — NO sorryAx, proof genuine. Leg classification: A1 (namedGroups↔match.groupdict()) = R (dict↔key-distinct assoc list, an INPUT not a callee); A2 (positionalGroups↔match.groups()) = R (tuple↔list, input); A3 (keepPresent↔`{…if v is not None}` comprehension) = I (directly modeled, G-CONF-checked); A4 (out.positional guard↔`args = () if kwargs`) = I; A5 (`path[match.end():]`) = out-of-scope unchanged remainder, correctly unmodeled.

NO kind-A (axiom-consumed / deep-model-reference) legs and NO kind-3 (inexpressible) legs — the changed op is a finite per-element filter + emptiness test, expressible and modeled directly. G-AX is a legitimate skip stub (asserts the no-axiom invariant). conformance_check.py transliterates keepOne/keepPresent + the args fallback (all R/I) with zero A-callees, seed 11477 — consistent with the no-axiom claim. The A-leg correspondence audit therefore holds: there are no A-legs to be unfaithful.

VERDICT: SOUND. 8 attacks re-run (6 wrong→rejected, 2 correct→verify), prepatch reproduced (atk_1), positive control verifies, and the faithful refined patch of the verifying-correct candidates RESOLVES under the executed official harness. The only verifying wrong impl is an out-of-scope partial-correctness divergence artifact that neither corresponds to any refinement leg nor triggers the mechanized BROKEN path.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean`, `atk_9.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-wrong TERMINATING implementation exists; the spec pins both outputs as exact functions of the inputs (out.named = keepPresent namedGroups; out.positional = if out.named=[] then positionalGroups else []). The only verifying wrong impl is a divergent while-true loop (atk_2), which is an out-of-scope partial-correctness artifact — see notes.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (none) The modeled operation post-processes values already produced by the
-- pattern engine; it calls no further routine whose contract must be assumed.
-- axioms-end

-- pure-start
/- A captured named group: its name paired with the value the engine bound to
   it, or `none` when the group took part in no alternative that actually
   participated in the overall capture (an optional group that contributed
   nothing). -/
abbrev Named := String × Option String

/- Per-group contribution to the keyword bindings: a group that bound a value
   contributes itself; a group that bound nothing contributes nothing. -/
def keepOne (p : Named) : List Named :=
  if p.2.isSome then [p] else []

/- The keyword bindings of a whole capture list: concatenate the per-group
   contributions, in order. Front-recursive so a single unfold is available per
   loop step (the fold pattern). -/
def keepPresent : List Named → List Named
  | []      => []
  | p :: ps => keepOne p ++ keepPresent ps

@[grind] lemma keepPresent_nil : keepPresent [] = [] := rfl
@[grind] lemma keepPresent_cons (p : Named) (ps : List Named) :
    keepPresent (p :: ps) = keepOne p ++ keepPresent ps := rfl
-- pure-end

/- The result of binding a single capture: the keyword bindings, plus the
   positional bindings (used only when there are no keyword bindings). -/
structure Bindings where
  named : List Named
  positional : List String
deriving Repr, Inhabited

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method bindCaptures (namedGroups : List Named) (positionalGroups : List String)
    return (out : Bindings)
  ensures out.named = keepPresent namedGroups
  ensures out.positional = (if out.named = [] then positionalGroups else [])
  do
    -- impl-start
    let mut result : List Named := []
    let mut i := namedGroups.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ namedGroups.length
      invariant result = keepPresent (namedGroups.drop i)
      done_with i = 0
    do
      let p := namedGroups[i - 1]!
      result := keepOne p ++ result
      i := i - 1
    return ⟨result, if result = [] then positionalGroups else []⟩
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `keepPresent` peels one `keepOne`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma keepPresent_drop_step (xs : List Named) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    keepPresent (xs.drop (i - 1)) = keepOne xs[i - 1]! ++ keepPresent (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keepPresent_cons]

prove_correct bindCaptures by
  loom_solve
  rw [keepPresent_drop_step namedGroups i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: bindCaptures has NO precondition and TWO exact-equality postconditions over concrete pure functions keepOne/keepPresent — the strongest possible shape. same_spec elides only the impl region and the prove_correct body (verified against markers.spec_view), so a legitimate alternative impl ships its OWN proof; the helper lemma keepPresent_drop_step is in the spec view and was kept byte-identical in every attack. All 10 candidate files confirmed same_spec=True.

### VERIFY TALLY (scripts/lean_verify.sh <file>, run concurrently ≤4):
- pos_control.lean (baseline backward while-fold, correct): exit 0 — POSITIVE CONTROL verifies.
- atk_5.lean (ungrounded-oracle ECHO: `let named := keepPresent namedGroups; return ⟨named, …⟩`, correct): exit 0 — verifies (structurally different correct alt).
- atk_7.lean (control-flow variant: FORWARD fold `result ++ keepOne p`, take-based invariant + own inline keepPresent_append proof, correct): exit 0 — verifies (2nd correct alt).
- atk_1.lean (PREPATCH bug: keep-all, no filter, `result := p :: result`): exit 1 — REJECTED on ensures_1 `out.named = keepPresent namedGroups` (invariant result = namedGroups.drop i cannot discharge the filtered post). Prepatch reproduced.
- atk_3.lean (keep-all with keepPresent/drop invariant mismatch): exit 1 — REJECTED, residual keepOne … ++ result = keepPresent (drop (i-1-1)).
- atk_4.lean (correct named, positional ALWAYS = positionalGroups): exit 1 — REJECTED on ensures_2 (needs keepPresent namedGroups=[] to justify positionalGroups when named≠[]).
- atk_6.lean (INVERTED filter: keep when isNone): exit 1 — REJECTED, residual (if isNone then [p] else []) = keepOne p (false for present groups).
- atk_8.lean (BOUNDARY off-by-one: loop `i>1`, skips first element): exit 1 — REJECTED on done_1 (i=1 leaves one element unprocessed).
- atk_9.lean (positional ALWAYS []): exit 1 — REJECTED on ensures_2 (when out.named=[] must return positionalGroups, returns []).
Every wrong TERMINATING impl is rejected; both correct alternatives verify. Spec is TIGHT.

### EXECUTED HARNESS EVIDENCE (run_resolve):
- GOLD/echo patch (the faithful refined patch of atk_5 AND atk_7 — both compute the present-only filter + emptiness-guarded positional, i.e. exactly `kwargs = {k:v for … if v is not None}` and the unchanged args line): `RESOLVE resolved=True completed=True note='resolved'`. verify⇒correct confirmed on the F2P/P2P suite (test_re_path_with_optional_parameter, test_two_variable_at_start_of_path_pattern, test_translate_url_utility).

DIVERGENCE PROBE (atk_2, atk_2.lean) — DELIBERATELY NOT SUBMITTED AS A BREAKING ATTACK: a `while true … done_with False` loop with its own proof (`loom_solve`). same_spec=True, lean_verify exit 0 (no sorry; #print axioms of the baseline = [propext, Classical.choice, Quot.sound], genuine). It verifies because `set_option loom.semantics.termination "partial"` (part of the FROZEN spec view, and a framework-blessed setting per spec_guide.md:112/quickref.md:6) makes any postcondition VACUOUSLY true of a divergent program. This is a UNIVERSAL partial-correctness artifact (it would 'break' every partial-correctness velvet/lean bundle identically), NOT a refinement-fidelity defect:

(1) a `while True` loop refines NONE of refinement.md's mapped output-producing ops A1–A5, so it has no faithful refined patch under the map — refinement.md §D scopes the twin guarantee to a model 'refined by the map above';

(2) the correctness oracle is G-RESOLVE, and the gold obviously terminates. I still MATERIALIZED a strawman divergent patch (atk_2_patch.diff: inserts `while True: pass` before the kwargs assignment) and RAN it: `RESOLVE resolved=False completed=False note='no report … harness error'` — i.e. INCONCLUSIVE, NOT the derivation's BROKEN path (`r.completed and not r.resolved`). A divergent patch can never be completed-but-unresolved, so the framework's own mechanization does not count divergence as a spec weakness. Submitting atk_2 would only fail-close the gate to INCONCLUSIVE on a resolve that cannot complete — a spurious result — so it is documented here rather than listed.

REFINEMENT.md LEG AUDIT (A-leg focus): meta.json axioms=[], deep_model_references=[], additional_change_sites=[]. Solution.lean has zero banned tokens (no sorry/admit/native_decide/Classical.choice/unsafe/extern). #print axioms bindCaptures_correct = [propext, Classical.choice, Quot.sound] — NO sorryAx, proof genuine. Leg classification: A1 (namedGroups↔match.groupdict()) = R (dict↔key-distinct assoc list, an INPUT not a callee); A2 (positionalGroups↔match.groups()) = R (tuple↔list, input); A3 (keepPresent↔`{…if v is not None}` comprehension) = I (directly modeled, G-CONF-checked); A4 (out.positional guard↔`args = () if kwargs`) = I; A5 (`path[match.end():]`) = out-of-scope unchanged remainder, correctly unmodeled.

NO kind-A (axiom-consumed / deep-model-reference) legs and NO kind-3 (inexpressible) legs — the changed op is a finite per-element filter + emptiness test, expressible and modeled directly. G-AX is a legitimate skip stub (asserts the no-axiom invariant). conformance_check.py transliterates keepOne/keepPresent + the args fallback (all R/I) with zero A-callees, seed 11477 — consistent with the no-axiom claim. The A-leg correspondence audit therefore holds: there are no A-legs to be unfaithful.

VERDICT: SOUND. 8 attacks re-run (6 wrong→rejected, 2 correct→verify), prepatch reproduced (atk_1), positive control verifies, and the faithful refined patch of the verifying-correct candidates RESOLVES under the executed official harness. The only verifying wrong impl is an out-of-scope partial-correctness divergence artifact that neither corresponds to any refinement leg nor triggers the mechanized BROKEN path.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo) audit for django__django-11477 velvet bundle. Modeled function bindCaptures(namedGroups, positionalGroups) with postconditions: out.named = keepPresent namedGroups (drop groups whose value is `none`), out.positional = if out.named = [] then positionalGroups else []. This models the gold patch's `kwargs = {k:v for k,v in match.groupdict().items() if v is not None}` and the observably-re-driven `args = () if kwargs else match.groups()`.

### Verification performed
1) same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — spec regions byte-identical; prepatch differs only in impl/proof (correct for G-DIFF). Spec view rendered and inspected.
2) Built a fresh base_commit worktree (e2867118...) (which itself was at a LATER refactor commit 755dbf39 whose match() computes args from the UNFILTERED groupdict — NOT the gold behavior; so I did not trust it), applied the gold patch.diff (filter-first), and drove the REAL patched django.urls.resolvers.RegexPattern.match.
3) Compared model vs real oracle on adversarial cases: mixed named+positional (^(?P<a>x)?(\d+)$ on 'x5' and '5'), None-valued positional entries (oracle returns (None,'5')), all-absent-named (^(?P<a>x)?(?P<b>y)?$ on '' -> args=(None,None), kwargs={}), positional-only, no-groups, one-present-one-absent. ALL agree.
4) Fuzzed 20000 random regex/path pairs (named+positional, optional/required mix): 0 disagreements.
5) Recorded G-CONF ran 100010 inputs (seed=11477) with 0 disagreements; my independent re-check corroborates.

Key subtlety confirmed faithful: the all-absent-named case flips args from () to match.groups() post-patch — the model's `if out.named = []` guard captures this exactly. The type abstraction (dict.items() order <-> assoc list, None <-> none, tuple <-> list, opaque String payload) holds; model never inspects value contents, only some/none status. No input where the modeled function disagrees with the real callee was found. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (velvet Solution.lean, impl+proof elided) does not leak the gold edit beyond the public problem_statement.

Gold edit (patch.diff): `kwargs = {k: v for k, v in match.groupdict().items() if v is not None}` in django/urls/resolvers.py — drop None-valued named groups from kwargs, with the downstream `args = () if kwargs else match.groups()` flip.

Public problem_statement already frames the domain: 'translate_url() creates an incorrect URL when optional named groups are missing … problem when translating urls with absent optional arguments.' So the notion of absent optional named groups is public (not from hints_text).

Mechanical screen (leakage.screen) PASSES with zero hard failures. Independently verified:
 - No diff markers (@@, diff --git, +++, index) in the view.
 - No gold-patch changed line reproduced: spec uses abstract carriers keepOne/keepPresent/isSome over `List Named`; it never contains `groupdict`, `kwargs`, `args`, or the comprehension text.
 - Patched file path `django/urls/resolvers.py` and its dotted module form absent from the view.
 - Patched repo symbols (match/groupdict) not embedded in any spec-view identifier (namedGroups, positionalGroups, Bindings, keepOne, keepPresent — all domain-abstract) and not named in any comment/docstring.
 - No fix/bug/patch/regression narration in spec-view comments; prose is behavioral and neutral ('a group that bound nothing contributes nothing'), never referencing an edit, before/after, or the diff.

Semantic gold-reconstruction check: the frozen spec (`out.named = keepPresent namedGroups`; positional surfaced only when named is empty) formalizes the DESIRED behavior, which any faithful spec must; it follows naturally from the public problem statement and does not disclose the file, function, diff, or edit localization beyond legitimate behavioral description. same_spec(Solution.lean, Solution_prepatch.lean) = True, confirming the spec view is the shared frozen spec (prepatch fails the same ensures clause), not tilted toward the gold implementation. Bundle is NOT relaxed (meta relaxed_leakage=None, recorded G-LEAK status 'pass'), so no RELAXED_LEAKAGE deferral is in play — judged on the merits. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.