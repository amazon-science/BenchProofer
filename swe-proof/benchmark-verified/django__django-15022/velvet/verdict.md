# P2 adversarial audit — django__django-15022

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies, so no verify⇏correct breach exists. The load-bearing discriminator: spec pins `result = anyRecord matchTerm terms records` (∃ related item r. ∀ search word t. matchTerm r t), a FULLY GROUNDED postcondition over concrete recursive folds (no axioms/opaque symbols). The quantifier-swap counterexample records=[r0,r1], terms=[t0,t1], matchTerm matrix=[[0,1],[1,0]] (each word matched by a DIFFERENT item, no single item matches all) yields prepatch/atk_4 ∀word∃item = true but spec ∃item∀word = false — exactly what F2P test_related_field_multiple_search_terms exercises; the buggy accumulator cannot satisfy the ensures goal.
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
 -- (No axiomatized callees. The per-item-per-word match test — "does this related
@@ -67,18 +67,7 @@
   ensures result = anyRecord matchTerm terms records
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := records.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ records.length
-      invariant acc = anyRecord matchTerm terms (records.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := records[i - 1]!
-      acc := conjTerms (matchTerm r) terms || acc
-      i := i - 1
-    return acc
+    return true
     -- impl-end
 
 /- The backward-fold step over the related items: dropping one fewer item exposes
@@ -113,5 +102,4 @@
 
 prove_correct searchKeepsRow by
   loom_solve
-  rw [anyRecord_drop_step matchTerm terms records i (by omega) (by omega)]
   simp_all
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-item-per-word match test — "does this related
@@ -67,18 +67,7 @@
   ensures result = anyRecord matchTerm terms records
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := records.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ records.length
-      invariant acc = anyRecord matchTerm terms (records.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := records[i - 1]!
-      acc := conjTerms (matchTerm r) terms || acc
-      i := i - 1
-    return acc
+    return false
     -- impl-end
 
 /- The backward-fold step over the related items: dropping one fewer item exposes
@@ -113,5 +102,4 @@
 
 prove_correct searchKeepsRow by
   loom_solve
-  rw [anyRecord_drop_step matchTerm terms records i (by omega) (by omega)]
   simp_all
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-item-per-word match test — "does this related
@@ -67,18 +67,7 @@
   ensures result = anyRecord matchTerm terms records
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := records.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ records.length
-      invariant acc = anyRecord matchTerm terms (records.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := records[i - 1]!
-      acc := conjTerms (matchTerm r) terms || acc
-      i := i - 1
-    return acc
+    return records.any (fun r => matchTerm r terms[0]!)
     -- impl-end
 
 /- The backward-fold step over the related items: dropping one fewer item exposes
@@ -112,6 +101,4 @@
   rw [hcons, conjTerms_cons]
 
 prove_correct searchKeepsRow by
-  loom_solve
-  rw [anyRecord_drop_step matchTerm terms records i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> grind
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-item-per-word match test — "does this related
@@ -67,18 +67,17 @@
   ensures result = anyRecord matchTerm terms records
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := records.length
+    let mut keep : Bool := true
+    let mut i := terms.length
     while i > 0
-      invariant 0 ≤ i ∧ i ≤ records.length
-      invariant acc = anyRecord matchTerm terms (records.drop i)
+      invariant 0 ≤ i ∧ i ≤ terms.length
+      invariant keep = (terms.drop i).all (fun t => records.any (fun r => matchTerm r t))
       done_with i = 0
-      decreasing i
     do
-      let r := records[i - 1]!
-      acc := conjTerms (matchTerm r) terms || acc
+      let t := terms[i - 1]!
+      keep := (records.any (fun r => matchTerm r t)) && keep
       i := i - 1
-    return acc
+    return keep
     -- impl-end
 
 /- The backward-fold step over the related items: dropping one fewer item exposes
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-item-per-word match test — "does this related
@@ -67,18 +67,7 @@
   ensures result = anyRecord matchTerm terms records
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := records.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ records.length
-      invariant acc = anyRecord matchTerm terms (records.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := records[i - 1]!
-      acc := conjTerms (matchTerm r) terms || acc
-      i := i - 1
-    return acc
+    return records.any (fun r => terms.any (fun t => matchTerm r t))
     -- impl-end
 
 /- The backward-fold step over the related items: dropping one fewer item exposes
@@ -112,6 +101,4 @@
   rw [hcons, conjTerms_cons]
 
 prove_correct searchKeepsRow by
-  loom_solve
-  rw [anyRecord_drop_step matchTerm terms records i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> grind
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-item-per-word match test — "does this related
@@ -67,18 +67,7 @@
   ensures result = anyRecord matchTerm terms records
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := records.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ records.length
-      invariant acc = anyRecord matchTerm terms (records.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := records[i - 1]!
-      acc := conjTerms (matchTerm r) terms || acc
-      i := i - 1
-    return acc
+    return records.all (fun r => terms.all (fun t => matchTerm r t))
     -- impl-end
 
 /- The backward-fold step over the related items: dropping one fewer item exposes
@@ -112,6 +101,4 @@
   rw [hcons, conjTerms_cons]
 
 prove_correct searchKeepsRow by
-  loom_solve
-  rw [anyRecord_drop_step matchTerm terms records i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> grind
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-item-per-word match test — "does this related
@@ -67,18 +67,7 @@
   ensures result = anyRecord matchTerm terms records
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := records.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ records.length
-      invariant acc = anyRecord matchTerm terms (records.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := records[i - 1]!
-      acc := conjTerms (matchTerm r) terms || acc
-      i := i - 1
-    return acc
+    return conjTerms (matchTerm records[0]!) terms
     -- impl-end
 
 /- The backward-fold step over the related items: dropping one fewer item exposes
@@ -112,6 +101,4 @@
   rw [hcons, conjTerms_cons]
 
 prove_correct searchKeepsRow by
-  loom_solve
-  rw [anyRecord_drop_step matchTerm terms records i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> grind
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The per-item-per-word match test — "does this related
@@ -68,12 +68,11 @@
   do
     -- impl-start
     let mut acc : Bool := false
-    let mut i := records.length
+    let mut i := records.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ records.length
       invariant acc = anyRecord matchTerm terms (records.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := records[i - 1]!
       acc := conjTerms (matchTerm r) terms || acc
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-item-per-word match test — "does this related
--  item match this search word, on at least one of the searched fields" — is an
--  UNCHANGED callee, taken here as a FREE INPUT `matchTerm`. The spec makes no
--  behavioural claim about it and holds for every value, so there is nothing to
--  validate against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- "Does one single related item match EVERY search word?" — the conjunction of
   the per-word match test `matchOf` over the word list. Written front-recursively
   so a single unfold is available per loop step (the backward fold pattern,
   plan §5.4). Empty word list ⇒ vacuously matched ⇒ `true`. -/
def conjTerms (matchOf : Nat → Bool) : List Nat → Bool
  | []      => true
  | t :: ts => matchOf t && conjTerms matchOf ts

@[grind] lemma conjTerms_nil (f : Nat → Bool) : conjTerms f [] = true := rfl
@[grind] lemma conjTerms_cons (f : Nat → Bool) (t : Nat) (ts : List Nat) :
    conjTerms f (t :: ts) = (f t && conjTerms f ts) := rfl

/- "Is there SOME related item that matches every search word?" — the disjunction
   over the related items of `conjTerms (matchTerm r) terms` ("item `r` matches all
   words"). Front-recursive for the same per-step unfold. Empty item list ⇒ no
   witness ⇒ `false`. The `terms` list is the shared word list every item is tested
   against. -/
def anyRecord (matchTerm : Nat → Nat → Bool) (terms : List Nat) : List Nat → Bool
  | []      => false
  | r :: rs => conjTerms (matchTerm r) terms || anyRecord matchTerm terms rs

@[grind] lemma anyRecord_nil (f : Nat → Nat → Bool) (terms : List Nat) :
    anyRecord f terms [] = false := rfl
@[grind] lemma anyRecord_cons (f : Nat → Nat → Bool) (terms : List Nat)
    (r : Nat) (rs : List Nat) :
    anyRecord f terms (r :: rs) = (conjTerms (f r) terms || anyRecord f terms rs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The membership decision for one candidate row of the outer collection, when a
   search over its related items is in effect (at least one search word present).

   A row is kept exactly when a SINGLE related item matches all of the search
   words at once: `anyRecord matchTerm terms records` — there exists a related
   item `r` such that for every search word `t`, `matchTerm r t` holds. Words are
   NOT allowed to be satisfied by different items: the matching item must be the
   same for all words.

   `records` (the related items), `terms` (the search words) and `matchTerm` (the
   per-item-per-word test) are read-only; the decision mutates nothing it is handed
   (directive 5). -/
method searchKeepsRow (records : List Nat) (terms : List Nat) (matchTerm : Nat → Nat → Bool)
    return (result : Bool)
  require 0 < terms.length
  ensures result = anyRecord matchTerm terms records
  do
    -- impl-start
    return records.any (fun r => conjTerms (matchTerm r) terms)
    -- impl-end

/- The backward-fold step over the related items: dropping one fewer item exposes
   the item at `i-1` on the front, so `anyRecord` peels one disjunct. The single
   goal `loom_solve` leaves for the loop body. -/
lemma anyRecord_drop_step (f : Nat → Nat → Bool) (terms : List Nat)
    (records : List Nat) (i : Nat) (hi : 0 < i) (hle : i ≤ records.length) :
    anyRecord f terms (records.drop (i - 1))
      = (conjTerms (f records[i - 1]!) terms || anyRecord f terms (records.drop i)) := by
  have hlt : i - 1 < records.length := by omega
  have hcons : records.drop (i - 1) = records[i - 1]! :: records.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyRecord_cons]

/- The backward-fold step over the search words: the conjunction analogue of
   `anyRecord_drop_step`. Carried for the alternative aggregate over words; a
   generic list lemma, content-neutral. -/
lemma conjTerms_drop_step (matchOf : Nat → Bool) (terms : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ terms.length) :
    conjTerms matchOf (terms.drop (i - 1))
      = (matchOf terms[i - 1]! && conjTerms matchOf (terms.drop i)) := by
  have hlt : i - 1 < terms.length := by omega
  have hcons : terms.drop (i - 1) = terms[i - 1]! :: terms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, conjTerms_cons]

prove_correct searchKeepsRow by
  loom_solve
  -- goal: (records.any fun r => conjTerms (matchTerm r) terms) = anyRecord matchTerm terms records
  induction records with
  | nil => simp [anyRecord]
  | cons r rs ih =>
    simp [List.any_cons, anyRecord_cons, ih]
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL COMPLETED.** Toolchain validated: baseline Solution.lean verifies RC=0; same_spec(identical copy)=True; same_spec(prepatch)=True.

**SPEC SHAPE:** velvet method searchKeepsRow(records:List Nat, terms:List Nat, matchTerm:Nat→Nat→Bool), require 0<terms.length, ensures result = anyRecord matchTerm terms records. anyRecord/conjTerms are concrete pure recursive folds. axioms:[] deep_model_references:[] → NO A-legs to attack; all refinement legs are R (type-only bijections) or I (concrete folds covered by G-CONF). The genuinely-changed op (N chained queryset.filter per word [∀word∃item] → one combined queryset.filter(Q(*term_queries)) [∃item∀word]) is modeled DEEPLY, not behind an axiom. No kind-3 leg. Because there are no axioms/ungrounded oracles, the only 'answer key' is the spec's own concrete definition; an echo of it IS the correct computation (positive control), not a cheat.

**EDIT DISCIPLINE:** each attack copies Solution.lean and edits ONLY the impl region + the elided prove_correct body (both elided from spec_view; verified same_spec=True for all 8). No top-level lemma/signature/contract changes.

### ATTACKS (all same_spec=True; verify cmd: `bash scripts/lean_verify.sh <path>`; ALL exit 1 = fail-to-verify):
- atk_1 `return true` (constant/boundary) → RC=1, unsolved `⊢ anyRecord matchTerm terms records = true`.
- atk_2 `return false` (constant) → RC=1, unsolved `⊢ anyRecord matchTerm terms records = false`.
- atk_3 `records.any (fun r => matchTerm r terms[0]!)` (first-word partial-domain) → RC=1, grind fails: `¬(records.any … terms[0]) = anyRecord …`.
- atk_4 PREPATCH BUG ∀word∃item (while over terms, keep := records.any(matchTerm r t) && keep) → RC=1, anyRecord_drop_step rewrite finds NO occurrence (∀word∃item structurally distinct from ∃item∀word). Same failure signature as shipped Solution_prepatch.lean (independently reproduced: prepatch.lean RC=1, identical invariant_2 rewrite miss).
- atk_5 `records.any (fun r => terms.any (fun t => matchTerm r t))` (∃item∃word; OR over words not AND) → RC=1, residual `= anyRecord` unclosable (simp_all no progress).
- atk_6 `records.all (fun r => terms.all …)` (∀item∀word; too strict) → RC=1, residual `= anyRecord` unclosable.
- atk_7 `conjTerms (matchTerm records[0]!) terms` (first-record partial-domain) → RC=1, grind fails: `¬ conjTerms(matchTerm records[0]) terms = anyRecord …`.
- atk_8 off-by-one boundary (i starts at records.length-1, last item never accumulated; control-flow-effect) → RC=1, unsolved invariant_2 `false = anyRecord matchTerm terms (drop (records.length-1) records)`.

All 8 failures land on the DISCRIMINATING goal (ensures_1 `result = anyRecord …` or the matching invariant_2/anyRecord_drop_step rewrite), NOT spurious parse/tactic-choice errors. Confirmed via an independent Python enumeration over require-satisfying inputs (|records|≤3, |terms|∈{1,2,3}, all match-bit matrices): every attack is SEMANTICALLY DISTINCT from anyRecord with an explicit witness (atk_1/atk_6 witness []/[0]; atk_2 [[1]]; atk_3/atk_5 [[1,0]]/[[0,1]]; atk_4 [[0,1],[1,0]]; atk_7 [[0],[1]]; atk_8 [[1]]). Since Lean is sound and the ensures must hold for EVERY free matchTerm, no alternative proof tactic could ever close these — the rejections are principled.

**RESOLVE STEP:** protocol step 2 (materialize + run_resolve the faithful patch) is triggered ONLY for a wrong impl that VERIFIES. ZERO wrong impls verified, so no faithful patch was materialized/resolve-run — vacuously satisfied, not skipped. Reported honestly rather than fabricated.

POSITIVE CONTROL (non-vacuity): positive_control.lean — structurally DIFFERENT correct impl `return records.any (fun r => conjTerms (matchTerm r) terms)` (direct functional, NO backward while-loop) with an inline induction proof (nil/cons on records, anyRecord_cons). same_spec=True, verify RC=0. The spec is satisfiable by a genuinely different correct algorithm.

REFINEMENT.md AUDIT: all legs A1-A6 R/I (no A-consumed, no A-reference, no kind-3), consistent with axioms:[]/deep_model_references:[]. R-legs are pure type bijections (List Nat ↔ opaque item/word identities; Nat→Nat→Bool ↔ the UNCHANGED per-(item,word) OR-of-fields match; Bool kept↔true); I-legs (conjTerms/anyRecord folds) are concrete and covered by G-CONF (100685 checks seed 15022, 0 disagreements). The mapping↔patch correspondence holds: the modeled ∃item∀word membership equals gold-patch queryset.filter(Q(*term_queries)) row membership (G-PANEL independently confirmed spec==real ORM on 11 F2P shapes incl. 'danielle 19'→0 / 'daniel 19'→1). No callee under change is abstracted — all callees (smart_split, unescape_string_literal, construct_search, or_queries, queryset.filter) are UNCHANGED by the patch.

**VERDICT:** SOUND. ≥5 distinct same-spec wrong impls (8 total, incl. the named prepatch counterexample and the prepatch bug) all fail to verify; positive control verifies; no verify⇏correct breach. INCONCLUSIVE not warranted — every verification completed (no timeouts/contention); resolve runs were vacuously unneeded (no verifying wrong impl).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl verifies, so no verify⇏correct breach exists. The load-bearing discriminator: spec pins `result = anyRecord matchTerm terms records` (∃ related item r. ∀ search word t. matchTerm r t), a FULLY GROUNDED postcondition over concrete recursive folds (no axioms/opaque symbols). The quantifier-swap counterexample records=[r0,r1], terms=[t0,t1], matchTerm matrix=[[0,1],[1,0]] (each word matched by a DIFFERENT item, no single item matches all) yields prepatch/atk_4 ∀word∃item = true but spec ∃item∀word = false — exactly what F2P test_related_field_multiple_search_terms exercises; the buggy accumulator cannot satisfy the ensures goal.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-item-per-word match test — "does this related
--  item match this search word, on at least one of the searched fields" — is an
--  UNCHANGED callee, taken here as a FREE INPUT `matchTerm`. The spec makes no
--  behavioural claim about it and holds for every value, so there is nothing to
--  validate against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- "Does one single related item match EVERY search word?" — the conjunction of
   the per-word match test `matchOf` over the word list. Written front-recursively
   so a single unfold is available per loop step (the backward fold pattern,
   plan §5.4). Empty word list ⇒ vacuously matched ⇒ `true`. -/
def conjTerms (matchOf : Nat → Bool) : List Nat → Bool
  | []      => true
  | t :: ts => matchOf t && conjTerms matchOf ts

@[grind] lemma conjTerms_nil (f : Nat → Bool) : conjTerms f [] = true := rfl
@[grind] lemma conjTerms_cons (f : Nat → Bool) (t : Nat) (ts : List Nat) :
    conjTerms f (t :: ts) = (f t && conjTerms f ts) := rfl

/- "Is there SOME related item that matches every search word?" — the disjunction
   over the related items of `conjTerms (matchTerm r) terms` ("item `r` matches all
   words"). Front-recursive for the same per-step unfold. Empty item list ⇒ no
   witness ⇒ `false`. The `terms` list is the shared word list every item is tested
   against. -/
def anyRecord (matchTerm : Nat → Nat → Bool) (terms : List Nat) : List Nat → Bool
  | []      => false
  | r :: rs => conjTerms (matchTerm r) terms || anyRecord matchTerm terms rs

@[grind] lemma anyRecord_nil (f : Nat → Nat → Bool) (terms : List Nat) :
    anyRecord f terms [] = false := rfl
@[grind] lemma anyRecord_cons (f : Nat → Nat → Bool) (terms : List Nat)
    (r : Nat) (rs : List Nat) :
    anyRecord f terms (r :: rs) = (conjTerms (f r) terms || anyRecord f terms rs) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The membership decision for one candidate row of the outer collection, when a
   search over its related items is in effect (at least one search word present).

   A row is kept exactly when a SINGLE related item matches all of the search
   words at once: `anyRecord matchTerm terms records` — there exists a related
   item `r` such that for every search word `t`, `matchTerm r t` holds. Words are
   NOT allowed to be satisfied by different items: the matching item must be the
   same for all words.

   `records` (the related items), `terms` (the search words) and `matchTerm` (the
   per-item-per-word test) are read-only; the decision mutates nothing it is handed
   (directive 5). -/
method searchKeepsRow (records : List Nat) (terms : List Nat) (matchTerm : Nat → Nat → Bool)
    return (result : Bool)
  require 0 < terms.length
  ensures result = anyRecord matchTerm terms records
  do
    -- impl-start
    return records.any (fun r => conjTerms (matchTerm r) terms)
    -- impl-end

/- The backward-fold step over the related items: dropping one fewer item exposes
   the item at `i-1` on the front, so `anyRecord` peels one disjunct. The single
   goal `loom_solve` leaves for the loop body. -/
lemma anyRecord_drop_step (f : Nat → Nat → Bool) (terms : List Nat)
    (records : List Nat) (i : Nat) (hi : 0 < i) (hle : i ≤ records.length) :
    anyRecord f terms (records.drop (i - 1))
      = (conjTerms (f records[i - 1]!) terms || anyRecord f terms (records.drop i)) := by
  have hlt : i - 1 < records.length := by omega
  have hcons : records.drop (i - 1) = records[i - 1]! :: records.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyRecord_cons]

/- The backward-fold step over the search words: the conjunction analogue of
   `anyRecord_drop_step`. Carried for the alternative aggregate over words; a
   generic list lemma, content-neutral. -/
lemma conjTerms_drop_step (matchOf : Nat → Bool) (terms : List Nat) (i : Nat)
    (hi : 0 < i) (hle : i ≤ terms.length) :
    conjTerms matchOf (terms.drop (i - 1))
      = (matchOf terms[i - 1]! && conjTerms matchOf (terms.drop i)) := by
  have hlt : i - 1 < terms.length := by omega
  have hcons : terms.drop (i - 1) = terms[i - 1]! :: terms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, conjTerms_cons]

prove_correct searchKeepsRow by
  loom_solve
  -- goal: (records.any fun r => conjTerms (matchTerm r) terms) = anyRecord matchTerm terms records
  induction records with
  | nil => simp [anyRecord]
  | cons r rs ih =>
    simp [List.any_cons, anyRecord_cons, ih]
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL COMPLETED.** Toolchain validated: baseline Solution.lean verifies RC=0; same_spec(identical copy)=True; same_spec(prepatch)=True.

**SPEC SHAPE:** velvet method searchKeepsRow(records:List Nat, terms:List Nat, matchTerm:Nat→Nat→Bool), require 0<terms.length, ensures result = anyRecord matchTerm terms records. anyRecord/conjTerms are concrete pure recursive folds. axioms:[] deep_model_references:[] → NO A-legs to attack; all refinement legs are R (type-only bijections) or I (concrete folds covered by G-CONF). The genuinely-changed op (N chained queryset.filter per word [∀word∃item] → one combined queryset.filter(Q(*term_queries)) [∃item∀word]) is modeled DEEPLY, not behind an axiom. No kind-3 leg. Because there are no axioms/ungrounded oracles, the only 'answer key' is the spec's own concrete definition; an echo of it IS the correct computation (positive control), not a cheat.

**EDIT DISCIPLINE:** each attack copies Solution.lean and edits ONLY the impl region + the elided prove_correct body (both elided from spec_view; verified same_spec=True for all 8). No top-level lemma/signature/contract changes.

### ATTACKS (all same_spec=True; verify cmd: `bash scripts/lean_verify.sh <path>`; ALL exit 1 = fail-to-verify):
- atk_1 `return true` (constant/boundary) → RC=1, unsolved `⊢ anyRecord matchTerm terms records = true`.
- atk_2 `return false` (constant) → RC=1, unsolved `⊢ anyRecord matchTerm terms records = false`.
- atk_3 `records.any (fun r => matchTerm r terms[0]!)` (first-word partial-domain) → RC=1, grind fails: `¬(records.any … terms[0]) = anyRecord …`.
- atk_4 PREPATCH BUG ∀word∃item (while over terms, keep := records.any(matchTerm r t) && keep) → RC=1, anyRecord_drop_step rewrite finds NO occurrence (∀word∃item structurally distinct from ∃item∀word). Same failure signature as shipped Solution_prepatch.lean (independently reproduced: prepatch.lean RC=1, identical invariant_2 rewrite miss).
- atk_5 `records.any (fun r => terms.any (fun t => matchTerm r t))` (∃item∃word; OR over words not AND) → RC=1, residual `= anyRecord` unclosable (simp_all no progress).
- atk_6 `records.all (fun r => terms.all …)` (∀item∀word; too strict) → RC=1, residual `= anyRecord` unclosable.
- atk_7 `conjTerms (matchTerm records[0]!) terms` (first-record partial-domain) → RC=1, grind fails: `¬ conjTerms(matchTerm records[0]) terms = anyRecord …`.
- atk_8 off-by-one boundary (i starts at records.length-1, last item never accumulated; control-flow-effect) → RC=1, unsolved invariant_2 `false = anyRecord matchTerm terms (drop (records.length-1) records)`.

All 8 failures land on the DISCRIMINATING goal (ensures_1 `result = anyRecord …` or the matching invariant_2/anyRecord_drop_step rewrite), NOT spurious parse/tactic-choice errors. Confirmed via an independent Python enumeration over require-satisfying inputs (|records|≤3, |terms|∈{1,2,3}, all match-bit matrices): every attack is SEMANTICALLY DISTINCT from anyRecord with an explicit witness (atk_1/atk_6 witness []/[0]; atk_2 [[1]]; atk_3/atk_5 [[1,0]]/[[0,1]]; atk_4 [[0,1],[1,0]]; atk_7 [[0],[1]]; atk_8 [[1]]). Since Lean is sound and the ensures must hold for EVERY free matchTerm, no alternative proof tactic could ever close these — the rejections are principled.

**RESOLVE STEP:** protocol step 2 (materialize + run_resolve the faithful patch) is triggered ONLY for a wrong impl that VERIFIES. ZERO wrong impls verified, so no faithful patch was materialized/resolve-run — vacuously satisfied, not skipped. Reported honestly rather than fabricated.

POSITIVE CONTROL (non-vacuity): positive_control.lean — structurally DIFFERENT correct impl `return records.any (fun r => conjTerms (matchTerm r) terms)` (direct functional, NO backward while-loop) with an inline induction proof (nil/cons on records, anyRecord_cons). same_spec=True, verify RC=0. The spec is satisfiable by a genuinely different correct algorithm.

REFINEMENT.md AUDIT: all legs A1-A6 R/I (no A-consumed, no A-reference, no kind-3), consistent with axioms:[]/deep_model_references:[]. R-legs are pure type bijections (List Nat ↔ opaque item/word identities; Nat→Nat→Bool ↔ the UNCHANGED per-(item,word) OR-of-fields match; Bool kept↔true); I-legs (conjTerms/anyRecord folds) are concrete and covered by G-CONF (100685 checks seed 15022, 0 disagreements). The mapping↔patch correspondence holds: the modeled ∃item∀word membership equals gold-patch queryset.filter(Q(*term_queries)) row membership (G-PANEL independently confirmed spec==real ORM on 11 F2P shapes incl. 'danielle 19'→0 / 'daniel 19'→1). No callee under change is abstracted — all callees (smart_split, unescape_string_literal, construct_search, or_queries, queryset.filter) are UNCHANGED by the patch.

**VERDICT:** SOUND. ≥5 distinct same-spec wrong impls (8 total, incl. the named prepatch counterexample and the prepatch bug) all fail to verify; positive control verifies; no verify⇏correct breach. INCONCLUSIVE not warranted — every verification completed (no timeouts/contention); resolve runs were vacuously unneeded (no verifying wrong impl).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec too strong / drift from real repo) — NO DEFECT FOUND. All mechanical gates re-run independently: (1) same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — frozen spec region (imports/set_options, pure conjTerms/anyRecord folds + @[grind] lemmas, searchKeepsRow signature with `require 0 < terms.length` and `ensures result = anyRecord matchTerm terms records`) byte-identical across variants. (2) Solution.lean verifies clean via scripts/lean_verify.sh (exit 0). (3) Solution_prepatch.lean genuinely FAILS at invariant_2 — the buggy ∀word.∃item accumulator `(terms.drop i).all (fun t => records.any (fun r => matchTerm r t))` cannot be rewritten via anyRecord_drop_step to the ∃item.∀word aggregate; structurally distinct (G-DIFF real). REAL REPO CHECK: worktree at base_commit e1d673c (git HEAD 4e8121e) carries the PRE-patch chained-filter code `for bit in smart_split(search_term): ... queryset = queryset.filter(or_queries)` = ∀word.∃related-item (buggy, one JOIN per word). The gold patch (patch.diff) collects per-word OR-queries into term_queries and applies ONE queryset.filter(models.Q(*term_queries)) = AND-of-per-word-ORs in a single filter/join = ∃item.∀word (fixed). The spec postcondition anyRecord matchTerm terms records = (∃ r∈records. ∀ t∈terms. matchTerm r t) is EXACTLY that gold ∃item.∀word row-membership semantics. WHY NOT TOO STRONG / NO DRIFT: (a) `require 0 < terms.length` mirrors the guarded branch `if search_fields and search_term:` and NARROWS the modeled domain — cannot make a spec too strong; the zero-word degenerate case (row unconditionally kept) is legitimately outside the modeled branch. (b) matchTerm is a FREE input (Nat→Nat→Bool) and the ensures holds for EVERY such function, so it makes no behavioural claim about the UNCHANGED per-(item,word) OR-of-fields callee and cannot over-constrain it; mixed local+relational search_fields fold into a valid matchTerm (matchTerm(r,t) = local(t) ∨ matchRel(r,t) is representable), single-self-item local-only search is the |records|=1 case. (c) Empty records ⇒ false agrees with Django's INNER-JOIN exclusion of rows with no related items under the combined relational filter. G-CONF: R/I shadow agrees with gold oracle any(all(match(r,t) for t in terms) for r in records) on 100685 checks (exhaustive small cubes + seeded fuzz, seed 15022), 0 disagreements. I could construct NO input within the modeled decision (records × terms × matchTerm) on which anyRecord disagrees with the real gold-patched queryset.filter(models.Q(*term_queries)) row membership — for any such triple anyRecord equals the gold ∃r.∀t membership over that exact match matrix. The sole theoretical corner (mixed local field + LEFT-JOIN promotion for a row with zero related items) is an explicit, documented scoping choice of the deliberately-scoped free-input model, not a demonstrable divergence with a concrete diverging input, and it rejects no gold-faithful impl. The abstraction (deep model of the combination logic, free-input abstraction of unchanged callees) is faithful.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (spec_view over Solution.lean, velvet) is fully abstracted: the modeled domain is opaque `records : List Nat`, `terms : List Nat`, `matchTerm : Nat → Nat → Bool`, result `Bool`. No repo-locating information appears anywhere in the consumer view: no `options.py`, no `get_search_results`, no `queryset.filter`, no `models.Q`, no `term_queries`, no `smart_split`/`search_fields`/`orm_lookups`. same_spec(Solution, Solution_prepatch) = True (frozen region byte-identical). Mechanical G-LEAK screen PASSES (0 hard failures): no diff markers, no gold-patch line reproduced (>=8 chars normalized), no patched file/module path, no spec-view identifier or comment echoing a patched repo symbol, no narration keyword (bug/fix/pre-patch/regression/...). The spec necessarily encodes correct post-patch behavior (a row is kept iff SOME related item matches EVERY word — the ∃item∀word semantics), but that is intrinsic to any verification spec and is not gold-edit leakage. The discriminating quantifier-swap prose (∀word∃item vs ∃item∀word) lives only in refinement.md/mapping.md (auditor docs, NOT the solver spec view). The public problem_statement already names the buggy `qs = qs.filter(...)` per-term chaining pattern; the spec view adds no localization or reconstruction beyond it — a solver cannot recover the file/method or the `models.Q(*term_queries)` combination from opaque List Nat combinatorics. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
