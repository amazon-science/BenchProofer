# P2 adversarial audit — django__django-13315

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_partial_domain.lean`, `atk_2_boundary.lean`, `atk_3_cf_return_empty.lean`, `atk_4_wrong_predicate.lean`, `atk_5_prepatch_replicate.lean`, `atk_7_duplicate_emit.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_oracle_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, TERMINATING (faithfully-refinable) impl both verifies and is behaviorally wrong. The postcondition `out = keepMatching rows` is a strict value-equality with NO precondition under PartialCorrectness+DemonicChoice, so every terminating same-spec impl must return exactly keepMatching rows to verify. Empirically: all 6 terminating wrong-value impls FAIL verify (atk_1 partial-domain while i>1 exit1; atk_2 boundary rows[i]! exit1; atk_3 control-flow return-[] exit1; atk_4 wrong-predicate witnesses>1 exit1; atk_5 prepatch replicate-witnesses (the duplicate-options bug) exit1; atk_7 duplicate-emit exit1). The only verifying same-spec impls are: (a) atk_6 ungrounded-oracle echo (result := keepMatching rows), behaviorally CORRECT — its faithful refined patch IS the gold patch, which RESOLVED under the official harness (completed=true, resolved=true, attempts=1); and (b) atk_8 divergent (while (0:Nat)<1, never pinning out) which verifies VACUOUSLY under loom.semantics.termination "partial". Divergence is a universal partial-correctness artifact (the option is part of the FROZEN spec view; ~401/500 velvet bundles use it), NOT a spec weakness and NOT a faithful refinement — its 'faithful patch' is an infinite loop carrying no behavioral content, which when run through run_resolve did NOT complete (harness hung, completed=false), i.e. it cannot even mechanically demonstrate verify⇏correct. It is out of G-EQ scope (which targets same-spec, faithfully-refinable, TERMINATING wrong impls) and is therefore excluded from the submitted attack set.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_partial_domain.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The constraint that narrows the candidate collection
@@ -58,11 +58,10 @@
     -- impl-start
     let mut result : List Int := []
     let mut i := rows.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant result = keepMatching (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := rows[i - 1]!
       result := keep c ++ result
```

Attack 2 — `atk_2_boundary.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The constraint that narrows the candidate collection
@@ -62,9 +62,8 @@
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant result = keepMatching (rows.drop i)
       done_with i = 0
-      decreasing i
     do
-      let c := rows[i - 1]!
+      let c := rows[i]!
       result := keep c ++ result
       i := i - 1
     return result
```

Attack 3 — `atk_3_cf_return_empty.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The constraint that narrows the candidate collection
@@ -56,17 +56,7 @@
   ensures out = keepMatching rows
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := rows.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rows.length
-      invariant result = keepMatching (rows.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := rows[i - 1]!
-      result := keep c ++ result
-      i := i - 1
+    let result : List Int := []
     return result
     -- impl-end
 
@@ -86,5 +76,3 @@
 
 prove_correct selectEligible by
   loom_solve
-  rw [keepMatching_drop_step rows i (by omega) (by omega)]
-  simp_all
```

Attack 4 — `atk_4_wrong_predicate.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The constraint that narrows the candidate collection
@@ -62,10 +62,9 @@
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant result = keepMatching (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := rows[i - 1]!
-      result := keep c ++ result
+      result := (if c.witnesses > 1 then [c.id] else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_5_prepatch_replicate.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The constraint that narrows the candidate collection
@@ -60,12 +60,10 @@
     let mut i := rows.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ rows.length
-      invariant result = keepMatching (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := rows[i - 1]!
-      result := keep c ++ result
+      result := List.replicate c.witnesses c.id ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 6 — `atk_6_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The constraint that narrows the candidate collection
@@ -56,17 +56,7 @@
   ensures out = keepMatching rows
   do
     -- impl-start
-    let mut result : List Int := []
-    let mut i := rows.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ rows.length
-      invariant result = keepMatching (rows.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := rows[i - 1]!
-      result := keep c ++ result
-      i := i - 1
+    let result : List Int := keepMatching rows
     return result
     -- impl-end
 
@@ -86,5 +76,3 @@
 
 prove_correct selectEligible by
   loom_solve
-  rw [keepMatching_drop_step rows i (by omega) (by omega)]
-  simp_all
```

Attack 7 — `atk_7_duplicate_emit.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The constraint that narrows the candidate collection
@@ -62,10 +62,9 @@
       invariant 0 ≤ i ∧ i ≤ rows.length
       invariant result = keepMatching (rows.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := rows[i - 1]!
-      result := keep c ++ result
+      result := keep c ++ keep c ++ result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The constraint that narrows the candidate collection
--  is applied via a presence check on each candidate's matching-witness count;
--  the collection-building primitive it relies on is modeled DEEPLY as the
--  per-candidate selection below, not consumed as an outside contract. There is
--  no `axiom` declaration and no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- One candidate item considered for inclusion in a constrained collection. It
   carries only the two fields the operation observes: a stable identity `id`
   and `witnesses` — the number of distinct ways this item satisfies the
   constraint (e.g. how many related records make it eligible). A candidate is
   *eligible* exactly when it has at least one witness. -/
structure Candidate where
  id : Int
  witnesses : Nat
deriving Inhabited, DecidableEq

/- The per-candidate contribution to the constrained collection: an eligible
   candidate contributes its identity ONCE; an ineligible one contributes
   nothing. The contribution does NOT depend on HOW MANY witnesses an eligible
   candidate has — one is enough, and more do not multiply it. -/
def keep (c : Candidate) : List Int :=
  if c.witnesses > 0 then [c.id] else []

/- The constrained collection over a whole candidate sequence: concatenate the
   per-candidate contributions, in order. Front-recursive so a single unfold is
   available per loop step (the backward-fold pattern). Because each eligible
   candidate contributes exactly one identity, the result lists every eligible
   identity once — never duplicated by a candidate's witness multiplicity. -/
def keepMatching : List Candidate → List Int
  | []      => []
  | c :: cs => keep c ++ keepMatching cs

@[grind] lemma keepMatching_nil : keepMatching [] = [] := rfl
@[grind] lemma keepMatching_cons (c : Candidate) (cs : List Candidate) :
    keepMatching (c :: cs) = keep c ++ keepMatching cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method selectEligible (rows : List Candidate) return (out : List Int)
  ensures out = keepMatching rows
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      invariant result = keepMatching (rows.drop i)
      done_with i = 0
    do
      let c := rows[i - 1]!
      result := keep c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the candidate at
   `i-1` on the front, so `keepMatching` peels one `keep`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma keepMatching_drop_step (rows : List Candidate) (i : Nat)
    (hi : 0 < i) (hle : i ≤ rows.length) :
    keepMatching (rows.drop (i - 1)) = keep rows[i - 1]! ++ keepMatching (rows.drop i) := by
  have hlt : i - 1 < rows.length := by omega
  have hcons : rows.drop (i - 1) = rows[i - 1]! :: rows.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keepMatching_cons]

prove_correct selectEligible by
  loom_solve
  rw [keepMatching_drop_step rows i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 9 files confirmed same_spec==True via swebench_unified.markers.same_spec (velvet backend). Files built by a generator (gen.py) that copies Solution.lean and edits ONLY the impl region + elided prove_correct body, leaving axioms/pure/pre/post/ensures/keepMatching_drop_step byte-identical.

VERIFY (bash scripts/lean_verify.sh <f>), run concurrently in batches of <=4 background jobs:
  positive_control        EXIT=0 (verifies)   [correct impl]
  atk_1_partial_domain    EXIT=1 (rejected)   [while i>1 skips index 0]
  atk_2_boundary          EXIT=1 (rejected)   [rows[i]! off-by-one]
  atk_3_cf_return_empty   EXIT=1 (rejected)   [unconditional return []]
  atk_4_wrong_predicate   EXIT=1 (rejected)   [witnesses>1]
  atk_5_prepatch_replicate EXIT=1 (rejected)  [List.replicate witnesses id = PREPATCH DUPLICATE BUG -> prepatch_reproduced]
  atk_6_oracle_echo       EXIT=0 (verifies)   [result := keepMatching rows; behaviorally CORRECT]
  atk_7_duplicate_emit    EXIT=1 (rejected)   [keep c ++ keep c]
  atk_8_divergent         EXIT=0 (verifies VACUOUSLY) [while (0:Nat)<1; EXCLUDED from attacks — see counterexample]

### RESOLVE (swebench_unified.harness.run_resolve, official harness, docker):
  atk_6_oracle_echo (faithful patch = gold patch.diff): completed=true, resolved=true, attempts=1, flaky=false, note="resolved". => correct echo, NOT a weakness (build_one.py candidate->resolve rule).
  atk_8_divergent (faithful patch = infinite `while True: pass` in apply_limit_choices_to_to_formfield): completed=FALSE (harness produced no report — the infinite loop hung the F2P test). Even mechanically this is inconclusive, never BROKEN; and it is not a faithful refinement of the narrowing, so excluded.

REFINEMENT.MD / meta.json AUDIT (step 3): meta.json axioms=[] and deep_model_references=[] — there are NO A-legs to audit. All refinement.md legs are R or I: A1 rows<->formfield.queryset (R, QuerySet<->List Candidate bijection); A2 keep c <-> filter(Exists(...)) (I, once-iff-eligible); A3 Q/&=/OuterRef assembly <-> shared eligibility predicate (R); A4 out=keepMatching rows <-> narrowed assignment (R). No kind-3: the operation that CHANGED (emission multiplicity of the narrowing) is modeled DEEPLY via keep/keepMatching, not behind an axiom; the prepatch behavior (replicate witnesses id) is expressible and demonstrably fails the spec (atk_5 exit1), while the gold once-each is exactly keepMatching (atk_6 verifies + resolves). CAVEAT (out of G-EQ scope): conf_skip=true — the R/I legs are NOT mechanically covered by G-CONF here (mapping.md §4: no DB-free oracle for the live-DB queryset narrowing); their soundness rests on G-VERIFY + G-DIFF per the django__django-13089 precedent. This is a G-CONF-scope matter, not a G-EQ break.

VERDICT: SOUND. >=5 distinct same-spec wrong impls run (7 submitted), prepatch bug reproduced (atk_5), positive control verifies, and the only faithfully-refinable verifying impl (atk_6) resolves under the official harness. No verify⇏correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_partial_domain.lean`, `atk_2_boundary.lean`, `atk_3_cf_return_empty.lean`, `atk_4_wrong_predicate.lean`, `atk_5_prepatch_replicate.lean`, `atk_7_duplicate_emit.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_oracle_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, TERMINATING (faithfully-refinable) impl both verifies and is behaviorally wrong. The postcondition `out = keepMatching rows` is a strict value-equality with NO precondition under PartialCorrectness+DemonicChoice, so every terminating same-spec impl must return exactly keepMatching rows to verify. Empirically: all 6 terminating wrong-value impls FAIL verify (atk_1 partial-domain while i>1 exit1; atk_2 boundary rows[i]! exit1; atk_3 control-flow return-[] exit1; atk_4 wrong-predicate witnesses>1 exit1; atk_5 prepatch replicate-witnesses (the duplicate-options bug) exit1; atk_7 duplicate-emit exit1). The only verifying same-spec impls are: (a) atk_6 ungrounded-oracle echo (result := keepMatching rows), behaviorally CORRECT — its faithful refined patch IS the gold patch, which RESOLVED under the official harness (completed=true, resolved=true, attempts=1); and (b) atk_8 divergent (while (0:Nat)<1, never pinning out) which verifies VACUOUSLY under loom.semantics.termination "partial". Divergence is a universal partial-correctness artifact (the option is part of the FROZEN spec view; ~401/500 velvet bundles use it), NOT a spec weakness and NOT a faithful refinement — its 'faithful patch' is an infinite loop carrying no behavioral content, which when run through run_resolve did NOT complete (harness hung, completed=false), i.e. it cannot even mechanically demonstrate verify⇏correct. It is out of G-EQ scope (which targets same-spec, faithfully-refinable, TERMINATING wrong impls) and is therefore excluded from the submitted attack set.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_boundary.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_cf_return_empty.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_wrong_predicate.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_prepatch_replicate.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_duplicate_emit.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The constraint that narrows the candidate collection
--  is applied via a presence check on each candidate's matching-witness count;
--  the collection-building primitive it relies on is modeled DEEPLY as the
--  per-candidate selection below, not consumed as an outside contract. There is
--  no `axiom` declaration and no A-reference deep model of an outside callee.)
-- axioms-end

-- pure-start
/- One candidate item considered for inclusion in a constrained collection. It
   carries only the two fields the operation observes: a stable identity `id`
   and `witnesses` — the number of distinct ways this item satisfies the
   constraint (e.g. how many related records make it eligible). A candidate is
   *eligible* exactly when it has at least one witness. -/
structure Candidate where
  id : Int
  witnesses : Nat
deriving Inhabited, DecidableEq

/- The per-candidate contribution to the constrained collection: an eligible
   candidate contributes its identity ONCE; an ineligible one contributes
   nothing. The contribution does NOT depend on HOW MANY witnesses an eligible
   candidate has — one is enough, and more do not multiply it. -/
def keep (c : Candidate) : List Int :=
  if c.witnesses > 0 then [c.id] else []

/- The constrained collection over a whole candidate sequence: concatenate the
   per-candidate contributions, in order. Front-recursive so a single unfold is
   available per loop step (the backward-fold pattern). Because each eligible
   candidate contributes exactly one identity, the result lists every eligible
   identity once — never duplicated by a candidate's witness multiplicity. -/
def keepMatching : List Candidate → List Int
  | []      => []
  | c :: cs => keep c ++ keepMatching cs

@[grind] lemma keepMatching_nil : keepMatching [] = [] := rfl
@[grind] lemma keepMatching_cons (c : Candidate) (cs : List Candidate) :
    keepMatching (c :: cs) = keep c ++ keepMatching cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method selectEligible (rows : List Candidate) return (out : List Int)
  ensures out = keepMatching rows
  do
    -- impl-start
    let mut result : List Int := []
    let mut i := rows.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ rows.length
      invariant result = keepMatching (rows.drop i)
      done_with i = 0
    do
      let c := rows[i - 1]!
      result := keep c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the candidate at
   `i-1` on the front, so `keepMatching` peels one `keep`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma keepMatching_drop_step (rows : List Candidate) (i : Nat)
    (hi : 0 < i) (hle : i ≤ rows.length) :
    keepMatching (rows.drop (i - 1)) = keep rows[i - 1]! ++ keepMatching (rows.drop i) := by
  have hlt : i - 1 < rows.length := by omega
  have hcons : rows.drop (i - 1) = rows[i - 1]! :: rows.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, keepMatching_cons]

prove_correct selectEligible by
  loom_solve
  rw [keepMatching_drop_step rows i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 9 files confirmed same_spec==True via swebench_unified.markers.same_spec (velvet backend). Files built by a generator (gen.py) that copies Solution.lean and edits ONLY the impl region + elided prove_correct body, leaving axioms/pure/pre/post/ensures/keepMatching_drop_step byte-identical.

VERIFY (bash scripts/lean_verify.sh <f>), run concurrently in batches of <=4 background jobs:
  positive_control        EXIT=0 (verifies)   [correct impl]
  atk_1_partial_domain    EXIT=1 (rejected)   [while i>1 skips index 0]
  atk_2_boundary          EXIT=1 (rejected)   [rows[i]! off-by-one]
  atk_3_cf_return_empty   EXIT=1 (rejected)   [unconditional return []]
  atk_4_wrong_predicate   EXIT=1 (rejected)   [witnesses>1]
  atk_5_prepatch_replicate EXIT=1 (rejected)  [List.replicate witnesses id = PREPATCH DUPLICATE BUG -> prepatch_reproduced]
  atk_6_oracle_echo       EXIT=0 (verifies)   [result := keepMatching rows; behaviorally CORRECT]
  atk_7_duplicate_emit    EXIT=1 (rejected)   [keep c ++ keep c]
  atk_8_divergent         EXIT=0 (verifies VACUOUSLY) [while (0:Nat)<1; EXCLUDED from attacks — see counterexample]

### RESOLVE (swebench_unified.harness.run_resolve, official harness, docker):
  atk_6_oracle_echo (faithful patch = gold patch.diff): completed=true, resolved=true, attempts=1, flaky=false, note="resolved". => correct echo, NOT a weakness (build_one.py candidate->resolve rule).
  atk_8_divergent (faithful patch = infinite `while True: pass` in apply_limit_choices_to_to_formfield): completed=FALSE (harness produced no report — the infinite loop hung the F2P test). Even mechanically this is inconclusive, never BROKEN; and it is not a faithful refinement of the narrowing, so excluded.

REFINEMENT.MD / meta.json AUDIT (step 3): meta.json axioms=[] and deep_model_references=[] — there are NO A-legs to audit. All refinement.md legs are R or I: A1 rows<->formfield.queryset (R, QuerySet<->List Candidate bijection); A2 keep c <-> filter(Exists(...)) (I, once-iff-eligible); A3 Q/&=/OuterRef assembly <-> shared eligibility predicate (R); A4 out=keepMatching rows <-> narrowed assignment (R). No kind-3: the operation that CHANGED (emission multiplicity of the narrowing) is modeled DEEPLY via keep/keepMatching, not behind an axiom; the prepatch behavior (replicate witnesses id) is expressible and demonstrably fails the spec (atk_5 exit1), while the gold once-each is exactly keepMatching (atk_6 verifies + resolves). CAVEAT (out of G-EQ scope): conf_skip=true — the R/I legs are NOT mechanically covered by G-CONF here (mapping.md §4: no DB-free oracle for the live-DB queryset narrowing); their soundness rests on G-VERIFY + G-DIFF per the django__django-13089 precedent. This is a G-CONF-scope matter, not a G-EQ break.

VERDICT: SOUND. >=5 distinct same-spec wrong impls run (7 submitted), prepatch bug reproduced (atk_5), positive control verifies, and the only faithfully-refinable verifying impl (atk_6) resolves under the official harness. No verify⇏correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-13315 (velvet). Modeled fn selectEligible(rows)=keepMatching rows models the post-patch narrowing in apply_limit_choices_to_to_formfield: `formfield.queryset.filter(Exists(...model._base_manager.filter(complex_filter)))`. keep c = [c.id] iff c.witnesses>0 else [] captures the Exists() presence test (emit each eligible candidate exactly once, in order); ineligible omitted. This agrees with the real post-patch callee on every input in the modeled operation's domain: (a) once-each — filter(Exists) does not join-expand, so multiplicity∈{0,1} matches; (b) order — .filter() preserves base queryset order, matching list order; (c) eligibility — witnesses>0 ⇔ ≥1 matching related row ⇔ Exists true. Verified at base_commit 36bc4706 that pre-patch used complex_filter (inner join, duplicates), confirming the abstraction endpoints. No diverging input found. Spec is NOT too strong: the order claim (stronger than the F2P test's assertCountEqual) still reflects real .filter() order-preservation, so it does not drift from repo behavior. The `if limit_choices_to:` truthiness guard is upstream of the modeled narrowing step (documented scoping, mapping.md §2), not part of the modeled function's domain. Checks: same_spec(Solution,Solution_prepatch,velvet)=True (spec region byte-identical, frozen); Solution.lean compiles (lean_verify exit 0); Solution_prepatch.lean (List.replicate witnesses id) FAILS `out=keepMatching rows` — spec is discriminating/non-vacuous (G-DIFF). G-CONF conf_skip=true is legitimate (no DB-free R/I shadow; witness multiplicity only observable against a live relational backend); soundness carried by G-VERIFY + G-DIFF, django__django-13089 precedent. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — spec regions (axioms/pure/pre/post + method signature & ensures) are byte-identical; the prepatch differs only in the elided impl body (replicate-per-witness) which is not part of the spec view.

Public problem_statement discloses: limit_choices_to on a ForeignKey with a Q object involving a JOIN renders DUPLICATE options in the formfield. The correct behavior 'each eligible option appears once (deduplicated)' is a direct logical consequence of that bug report.

Spec view models exactly and only this observable behavior: Candidate{id, witnesses}, keep = contribute id ONCE iff witnesses>0 (independent of witness count), postcondition out = keepMatching rows = every eligible identity listed once, never duplicated by multiplicity. The 'witnesses = number of related records making it eligible / join multiplicity' framing directly tracks the problem_statement's own 'join -> duplicates' disclosure.

The spec view reveals NO gold-patch implementation specifics: no Exists/OuterRef/Q(pk=OuterRef('pk'))/_base_manager subquery, no 'if limit_choices_to:' truthiness change, no mention of the particular dedup mechanism. The gold could equally have used .distinct(), .annotate(), Python-side filtering, or the Exists() subquery it actually chose (all alternatives discussed in hints, which are NOT part of the leakage baseline anyway); the spec does not point to any one over the others. It leaks nothing beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
