# P2 adversarial audit — django__django-11555

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verifies, so there is no verifying-but-wrong candidate whose faithful refined patch could fail to resolve. verify => correct holds for this spec.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms and no deep-model reference to a library callee. An
@@ -82,22 +82,21 @@
   ensures out = expandItems resolve items
   do
     -- impl-start
+    -- Pre-image skeleton: EVERY item is handed to the recursive name resolution,
+    -- including an order expression (its identity is threaded through `resolve`
+    -- as if it were a field name). The frozen spec requires an order expression
+    -- to contribute exactly `[(e, false)]`, so prove_correct MUST fail.
     let mut result : List Pair := []
     let mut i := items.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant result = expandItems resolve (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let it := items[i - 1]!
-      -- An order expression is already a complete ordering: take it as-is,
-      -- paired with `false`. A field name is expanded by its recursive
-      -- resolution. (The branch is what keeps an expression off the
-      -- name-resolution path.)
       let contribution : List Pair :=
         match it with
-        | .expr e => [(e, false)]
+        | .expr e => resolve e
         | .name n => resolve n
       result := contribution ++ result
       i := i - 1
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
 /- No consumed axioms and no deep-model reference to a library callee. An
@@ -88,17 +88,12 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant result = expandItems resolve (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let it := items[i - 1]!
-      -- An order expression is already a complete ordering: take it as-is,
-      -- paired with `false`. A field name is expanded by its recursive
-      -- resolution. (The branch is what keeps an expression off the
-      -- name-resolution path.)
       let contribution : List Pair :=
         match it with
-        | .expr e => [(e, false)]
-        | .name n => resolve n
+        | .expr e => resolve e
+        | .name n => [(n, false)]
       result := contribution ++ result
       i := i - 1
     return result
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
 /- No consumed axioms and no deep-model reference to a library callee. An
@@ -88,16 +88,11 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant result = expandItems resolve (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let it := items[i - 1]!
-      -- An order expression is already a complete ordering: take it as-is,
-      -- paired with `false`. A field name is expanded by its recursive
-      -- resolution. (The branch is what keeps an expression off the
-      -- name-resolution path.)
       let contribution : List Pair :=
         match it with
-        | .expr e => [(e, false)]
+        | .expr e => [(e, true)]
         | .name n => resolve n
       result := contribution ++ result
       i := i - 1
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
 /- No consumed axioms and no deep-model reference to a library callee. An
@@ -88,16 +88,11 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant result = expandItems resolve (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let it := items[i - 1]!
-      -- An order expression is already a complete ordering: take it as-is,
-      -- paired with `false`. A field name is expanded by its recursive
-      -- resolution. (The branch is what keeps an expression off the
-      -- name-resolution path.)
       let contribution : List Pair :=
         match it with
-        | .expr e => [(e, false)]
+        | .expr _ => []
         | .name n => resolve n
       result := contribution ++ result
       i := i - 1
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
 /- No consumed axioms and no deep-model reference to a library callee. An
@@ -82,25 +82,7 @@
   ensures out = expandItems resolve items
   do
     -- impl-start
-    let mut result : List Pair := []
-    let mut i := items.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ items.length
-      invariant result = expandItems resolve (items.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let it := items[i - 1]!
-      -- An order expression is already a complete ordering: take it as-is,
-      -- paired with `false`. A field name is expanded by its recursive
-      -- resolution. (The branch is what keeps an expression off the
-      -- name-resolution path.)
-      let contribution : List Pair :=
-        match it with
-        | .expr e => [(e, false)]
-        | .name n => resolve n
-      result := contribution ++ result
-      i := i - 1
+    let result : List Pair := []
     return result
     -- impl-end
 
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
 /- No consumed axioms and no deep-model reference to a library callee. An
@@ -88,16 +88,11 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant result = expandItems resolve (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let it := items[i - 1]!
-      -- An order expression is already a complete ordering: take it as-is,
-      -- paired with `false`. A field name is expanded by its recursive
-      -- resolution. (The branch is what keeps an expression off the
-      -- name-resolution path.)
       let contribution : List Pair :=
         match it with
-        | .expr e => [(e, false)]
+        | .expr e => [(e, false)] ++ resolve e
         | .name n => resolve n
       result := contribution ++ result
       i := i - 1
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
 /- No consumed axioms and no deep-model reference to a library callee. An
@@ -88,18 +88,13 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant result = expandItems resolve (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let it := items[i - 1]!
-      -- An order expression is already a complete ordering: take it as-is,
-      -- paired with `false`. A field name is expanded by its recursive
-      -- resolution. (The branch is what keeps an expression off the
-      -- name-resolution path.)
       let contribution : List Pair :=
         match it with
         | .expr e => [(e, false)]
         | .name n => resolve n
-      result := contribution ++ result
+      result := result ++ contribution
       i := i - 1
     return result
     -- impl-end
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
 /- No consumed axioms and no deep-model reference to a library callee. An
@@ -88,16 +88,11 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant result = expandItems resolve (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let it := items[i - 1]!
-      -- An order expression is already a complete ordering: take it as-is,
-      -- paired with `false`. A field name is expanded by its recursive
-      -- resolution. (The branch is what keeps an expression off the
-      -- name-resolution path.)
       let contribution : List Pair :=
         match it with
-        | .expr e => [(e, false)]
+        | .expr e => if e = 0 then [(e, false)] else resolve e
         | .name n => resolve n
       result := contribution ++ result
       i := i - 1
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee. An
@@ -88,17 +88,12 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant result = expandItems resolve (items.drop i)
       done_with i = 0
-      decreasing i
     do
       let it := items[i - 1]!
-      -- An order expression is already a complete ordering: take it as-is,
-      -- paired with `false`. A field name is expanded by its recursive
-      -- resolution. (The branch is what keeps an expression off the
-      -- name-resolution path.)
       let contribution : List Pair :=
         match it with
         | .expr e => [(e, false)]
-        | .name n => resolve n
+        | .name _ => []
       result := contribution ++ result
       i := i - 1
     return result
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee. An
@@ -88,13 +88,8 @@
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant result = expandItems resolve (items.drop i)
       done_with i = 0
-      decreasing i
     do
-      let it := items[i - 1]!
-      -- An order expression is already a complete ordering: take it as-is,
-      -- paired with `false`. A field name is expanded by its recursive
-      -- resolution. (The branch is what keeps an expression off the
-      -- name-resolution path.)
+      let it := items[i]!
       let contribution : List Pair :=
         match it with
         | .expr e => [(e, false)]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. An
   ordering specification is a list of items; a *name* item is resolved by a
   recursive lookup that is UNCHANGED here, so it is modeled as an arbitrary
   total resolver `resolve` (a free input on the method). The postcondition holds
   for EVERY `resolve`, so it is owed no contract — it is strictly weaker than any
   concrete callee (directive 7). The only behaviour this bundle pins — how each
   kind of ordering item contributes to the expanded result — is modeled DEEPLY
   in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The two kinds of item a default-ordering specification may contain:
     * `expr e` — an order *expression* that already denotes a complete ordering
                  (it is its own resolved ordering, carried by an identity `e`);
     * `name n` — a *field-name* lookup (identity `n`) that must be resolved into
                  one or more concrete orderings by the recursive resolver. -/
abbrev Expr := Int          -- identity of an order expression
abbrev Name := Int          -- identity of a field-name lookup

/- A single resolved ordering entry: the order expression it denotes paired with
   the flag that travels alongside it in the expanded result. -/
abbrev Pair := Expr × Bool

inductive Item where
  | expr (e : Expr)
  | name (n : Name)
  deriving DecidableEq, Inhabited, Repr

/- What one item contributes to the expanded ordering:
     * an order expression contributes exactly itself, paired with the flag
       `false`, and is NOT routed through name resolution (it is already a
       complete ordering — there is no name to look up);
     * a field name contributes whatever its recursive resolution yields. -/
def itemContribution (resolve : Name → List Pair) : Item → List Pair
  | .expr e => [(e, false)]
  | .name n => resolve n

/- The expansion of a whole specification: concatenate each item's contribution,
   in order. Written front-recursively so a single unfold is available per loop
   step (the fold pattern, plan §5.4). -/
def expandItems (resolve : Name → List Pair) : List Item → List Pair
  | []        => []
  | it :: rest => itemContribution resolve it ++ expandItems resolve rest

@[grind] lemma expandItems_nil (resolve : Name → List Pair) :
    expandItems resolve [] = [] := rfl
@[grind] lemma expandItems_cons (resolve : Name → List Pair)
    (it : Item) (rest : List Item) :
    expandItems resolve (it :: rest)
      = itemContribution resolve it ++ expandItems resolve rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Expand a default-ordering specification into its list of resolved ordering
   entries. All inputs are read-only (none is `mut`):
     * `items`   — the ordering specification, a list of items each of which is
                   either an order expression or a field-name lookup;
     * `resolve` — the recursive resolution of a field-name lookup into its
                   resolved ordering entries (unchanged here; abstracted as an
                   arbitrary total function).

   Desired behaviour: the result is the in-order concatenation of every item's
   contribution, where an order expression contributes exactly itself paired with
   `false` (it is already a complete ordering and is taken as-is, never handed to
   name resolution) and a field name contributes its recursive resolution. -/
method expandOrdering (items : List Item) (resolve : Name → List Pair)
    return (out : List Pair)
  ensures out = expandItems resolve items
  do
    -- impl-start
    let mut result : List Pair := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant result = expandItems resolve (items.drop i)
      done_with i = 0
    do
      let it := items[i - 1]!
      -- An order expression is already a complete ordering: take it as-is,
      -- paired with `false`. A field name is expanded by its recursive
      -- resolution. (The branch is what keeps an expression off the
      -- name-resolution path.)
      let contribution : List Pair :=
        match it with
        | .expr e => [(e, false)]
        | .name n => resolve n
      result := contribution ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer item exposes the item at `i-1` on
   the front, so `expandItems` peels one `itemContribution`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma expandItems_drop_step (resolve : Name → List Pair)
    (items : List Item) (i : Nat) (hi : 0 < i) (hle : i ≤ items.length) :
    expandItems resolve (items.drop (i - 1))
      = itemContribution resolve items[i - 1]! ++ expandItems resolve (items.drop i) := by
  have hlt : i - 1 < items.length := by omega
  have hcons : items.drop (i - 1) = items[i - 1]! :: items.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, expandItems_cons]

prove_correct expandOrdering by
  loom_solve
  rw [expandItems_drop_step resolve items i (by omega) (by omega)]
  simp_all [itemContribution]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. All files built by copying Solution.lean and editing ONLY the impl region; same_spec(velvet) verified True for all 11 files (atk_1..atk_10 + atk_pc). No patch.diff in the bundle dir (gold patch stored in gate results; G-RESOLVE=pass, note='resolved').

SPEC IS TIGHT — 10 DISTINCT same-spec wrong impls, all fail lean_verify (EXIT=1) for the RIGHT reason (unsolved postcondition/invariant goal on the discriminating clause, not an unrelated elaboration error):
  cmd (each): bash scripts/lean_verify.sh <path>
  - atk_1 (prepatch bug: .expr e => resolve e) EXIT=1, goal reduces to resolve e = [(e,false)] — exact OrderBy-routed-through-name-resolution crash.
  - atk_2 (swap: .expr e=>resolve e | .name n=>[(n,false)]) EXIT=1, both branches mismatch.
  - atk_3 (wrong flag: .expr e=>[(e,true)]) EXIT=1, [(e,true)]=[(e,false)] — Bool flag pinned.
  - atk_4 (drop expr: .expr _=>[]) EXIT=1, []=[(e,false)].
  - atk_5 (control-flow-effect: return [] with no loop accumulation) EXIT=1, ensures goal []=expandItems resolve items.
  - atk_6 (extra: .expr e=>[(e,false)]++resolve e) EXIT=1, (e,false)::resolve e=[(e,false)].
  - atk_7 (control-flow-effect: append instead of prepend, result++contribution) EXIT=1, invariant fold-direction mismatch.
  - atk_8 (partial-domain: .expr e=>if e=0 then [(e,false)] else resolve e) EXIT=1, non-zero expr identity still routed through resolve.
  - atk_9 (drop name: .name _=>[]) EXIT=1, []=resolve n — name branch pinned to resolve.
  - atk_10 (boundary/off-by-one: items[i]! instead of items[i-1]!) EXIT=1, invariant mismatch.
  Positive control atk_pc (exact Solution.lean) EXIT=0 — spec non-vacuous.
  Attacks span partial-domain (atk_8), boundary (atk_10), control-flow-effect (atk_5,atk_7), ungrounded-oracle echo (atk_1,atk_2 echo resolve on an expr item), wrong-flag/drop/extra (atk_3,atk_4,atk_6,atk_9). Verifications launched concurrently in batches of <=4 background Bash jobs.

STEP 2 (materialize+resolve faithful patches): ZERO applicable candidates — no wrong impl verifies, so patches={}. There is no verify-but-fails-resolve pathway to exhibit; verify=>correct is not falsifiable here.

REFINEMENT AUDIT (A-leg focus): refinement.md legs A1-A5 are all R/I; NO kind-3 (inexpressible-changed-op) leg. The one genuinely changed op (OrderBy dispatch) is modeled DEEPLY in itemContribution (.expr e=>[(e,false)]), visible in the pure region, not behind an axiom. NO A-legs exist: meta.json axioms=[], deep_model_references=[], G-AX=skip (legitimate). The sole opaque symbol resolve is a FREE universally-quantified method parameter (mapping.md 3.1), not an axiom/A-reference — the postcondition holds for every resolve, so it owes no contract and there is no callee-correspondence to falsify. The .expr branch is pinned to concrete [(e,false)] INDEPENDENT of resolve, so the free input cannot be echoed to bypass work (atk_1/atk_2 are exactly that echo attempt and both fail). mapping.md binds expandOrdering to compiler.py:723-727 default-ordering loop; type bijection OrderBy<->expr, str<->name, (OrderBy,False)<->Pair is sound. Supporting gates consistent: G-RESOLVE=pass, G-CONF=pass (100005 specs, 0 disagree, seed 11555, incl. F2P OrderBy(F(...)) shape), G-DIFF=pass (prepatch fails), G-VERIFY=pass.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verifies, so there is no verifying-but-wrong candidate whose faithful refined patch could fail to resolve. verify => correct holds for this spec.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. An
   ordering specification is a list of items; a *name* item is resolved by a
   recursive lookup that is UNCHANGED here, so it is modeled as an arbitrary
   total resolver `resolve` (a free input on the method). The postcondition holds
   for EVERY `resolve`, so it is owed no contract — it is strictly weaker than any
   concrete callee (directive 7). The only behaviour this bundle pins — how each
   kind of ordering item contributes to the expanded result — is modeled DEEPLY
   in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The two kinds of item a default-ordering specification may contain:
     * `expr e` — an order *expression* that already denotes a complete ordering
                  (it is its own resolved ordering, carried by an identity `e`);
     * `name n` — a *field-name* lookup (identity `n`) that must be resolved into
                  one or more concrete orderings by the recursive resolver. -/
abbrev Expr := Int          -- identity of an order expression
abbrev Name := Int          -- identity of a field-name lookup

/- A single resolved ordering entry: the order expression it denotes paired with
   the flag that travels alongside it in the expanded result. -/
abbrev Pair := Expr × Bool

inductive Item where
  | expr (e : Expr)
  | name (n : Name)
  deriving DecidableEq, Inhabited, Repr

/- What one item contributes to the expanded ordering:
     * an order expression contributes exactly itself, paired with the flag
       `false`, and is NOT routed through name resolution (it is already a
       complete ordering — there is no name to look up);
     * a field name contributes whatever its recursive resolution yields. -/
def itemContribution (resolve : Name → List Pair) : Item → List Pair
  | .expr e => [(e, false)]
  | .name n => resolve n

/- The expansion of a whole specification: concatenate each item's contribution,
   in order. Written front-recursively so a single unfold is available per loop
   step (the fold pattern, plan §5.4). -/
def expandItems (resolve : Name → List Pair) : List Item → List Pair
  | []        => []
  | it :: rest => itemContribution resolve it ++ expandItems resolve rest

@[grind] lemma expandItems_nil (resolve : Name → List Pair) :
    expandItems resolve [] = [] := rfl
@[grind] lemma expandItems_cons (resolve : Name → List Pair)
    (it : Item) (rest : List Item) :
    expandItems resolve (it :: rest)
      = itemContribution resolve it ++ expandItems resolve rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Expand a default-ordering specification into its list of resolved ordering
   entries. All inputs are read-only (none is `mut`):
     * `items`   — the ordering specification, a list of items each of which is
                   either an order expression or a field-name lookup;
     * `resolve` — the recursive resolution of a field-name lookup into its
                   resolved ordering entries (unchanged here; abstracted as an
                   arbitrary total function).

   Desired behaviour: the result is the in-order concatenation of every item's
   contribution, where an order expression contributes exactly itself paired with
   `false` (it is already a complete ordering and is taken as-is, never handed to
   name resolution) and a field name contributes its recursive resolution. -/
method expandOrdering (items : List Item) (resolve : Name → List Pair)
    return (out : List Pair)
  ensures out = expandItems resolve items
  do
    -- impl-start
    let mut result : List Pair := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant result = expandItems resolve (items.drop i)
      done_with i = 0
    do
      let it := items[i - 1]!
      -- An order expression is already a complete ordering: take it as-is,
      -- paired with `false`. A field name is expanded by its recursive
      -- resolution. (The branch is what keeps an expression off the
      -- name-resolution path.)
      let contribution : List Pair :=
        match it with
        | .expr e => [(e, false)]
        | .name n => resolve n
      result := contribution ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer item exposes the item at `i-1` on
   the front, so `expandItems` peels one `itemContribution`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma expandItems_drop_step (resolve : Name → List Pair)
    (items : List Item) (i : Nat) (hi : 0 < i) (hle : i ≤ items.length) :
    expandItems resolve (items.drop (i - 1))
      = itemContribution resolve items[i - 1]! ++ expandItems resolve (items.drop i) := by
  have hlt : i - 1 < items.length := by omega
  have hcons : items.drop (i - 1) = items[i - 1]! :: items.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, expandItems_cons]

prove_correct expandOrdering by
  loom_solve
  rw [expandItems_drop_step resolve items i (by omega) (by omega)]
  simp_all [itemContribution]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. All files built by copying Solution.lean and editing ONLY the impl region; same_spec(velvet) verified True for all 11 files (atk_1..atk_10 + atk_pc). No patch.diff in the bundle dir (gold patch stored in gate results; G-RESOLVE=pass, note='resolved').

SPEC IS TIGHT — 10 DISTINCT same-spec wrong impls, all fail lean_verify (EXIT=1) for the RIGHT reason (unsolved postcondition/invariant goal on the discriminating clause, not an unrelated elaboration error):
  cmd (each): bash scripts/lean_verify.sh <path>
  - atk_1 (prepatch bug: .expr e => resolve e) EXIT=1, goal reduces to resolve e = [(e,false)] — exact OrderBy-routed-through-name-resolution crash.
  - atk_2 (swap: .expr e=>resolve e | .name n=>[(n,false)]) EXIT=1, both branches mismatch.
  - atk_3 (wrong flag: .expr e=>[(e,true)]) EXIT=1, [(e,true)]=[(e,false)] — Bool flag pinned.
  - atk_4 (drop expr: .expr _=>[]) EXIT=1, []=[(e,false)].
  - atk_5 (control-flow-effect: return [] with no loop accumulation) EXIT=1, ensures goal []=expandItems resolve items.
  - atk_6 (extra: .expr e=>[(e,false)]++resolve e) EXIT=1, (e,false)::resolve e=[(e,false)].
  - atk_7 (control-flow-effect: append instead of prepend, result++contribution) EXIT=1, invariant fold-direction mismatch.
  - atk_8 (partial-domain: .expr e=>if e=0 then [(e,false)] else resolve e) EXIT=1, non-zero expr identity still routed through resolve.
  - atk_9 (drop name: .name _=>[]) EXIT=1, []=resolve n — name branch pinned to resolve.
  - atk_10 (boundary/off-by-one: items[i]! instead of items[i-1]!) EXIT=1, invariant mismatch.
  Positive control atk_pc (exact Solution.lean) EXIT=0 — spec non-vacuous.
  Attacks span partial-domain (atk_8), boundary (atk_10), control-flow-effect (atk_5,atk_7), ungrounded-oracle echo (atk_1,atk_2 echo resolve on an expr item), wrong-flag/drop/extra (atk_3,atk_4,atk_6,atk_9). Verifications launched concurrently in batches of <=4 background Bash jobs.

STEP 2 (materialize+resolve faithful patches): ZERO applicable candidates — no wrong impl verifies, so patches={}. There is no verify-but-fails-resolve pathway to exhibit; verify=>correct is not falsifiable here.

REFINEMENT AUDIT (A-leg focus): refinement.md legs A1-A5 are all R/I; NO kind-3 (inexpressible-changed-op) leg. The one genuinely changed op (OrderBy dispatch) is modeled DEEPLY in itemContribution (.expr e=>[(e,false)]), visible in the pure region, not behind an axiom. NO A-legs exist: meta.json axioms=[], deep_model_references=[], G-AX=skip (legitimate). The sole opaque symbol resolve is a FREE universally-quantified method parameter (mapping.md 3.1), not an axiom/A-reference — the postcondition holds for every resolve, so it owes no contract and there is no callee-correspondence to falsify. The .expr branch is pinned to concrete [(e,false)] INDEPENDENT of resolve, so the free input cannot be echoed to bypass work (atk_1/atk_2 are exactly that echo attempt and both fail). mapping.md binds expandOrdering to compiler.py:723-727 default-ordering loop; type bijection OrderBy<->expr, str<->name, (OrderBy,False)<->Pair is sound. Supporting gates consistent: G-RESOLVE=pass, G-CONF=pass (100005 specs, 0 disagree, seed 11555, incl. F2P OrderBy(F(...)) shape), G-DIFF=pass (prepatch fails), G-VERIFY=pass.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (G-PANEL-2) audit of the velvet bundle for django__django-11555. Verdict: FAITHFUL — the modeled function agrees with the real repo callee on every input; the spec does not drift from / over-constrain the gold-patched behavior.

### Setup verified
- Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. The frozen spec view is exactly the `pure` model (Expr/Name/Pair/Item, itemContribution, expandItems + grind lemmas) plus the method signature `ensures out = expandItems resolve items`. No impl/proof leakage into the spec.
- Solution.lean verifies via scripts/lean_verify.sh (exit 0). prepatch (`.expr e => resolve e`) fails to verify (G-DIFF), so the frozen postcondition genuinely discriminates the bug.
- Gold patch confirmed from data/swe_bench_verified/test.jsonl: the 3-line insertion into SQLCompiler.find_ordering_name's expansion loop — `if isinstance(item, OrderBy): results.append((item, False)); continue` before `results.extend(self.find_ordering_name(item, ...))`. This matches refinement.md/mapping.md verbatim. (Note: is at a LATER commit 580a4341 whose loop has extra guards `hasattr(resolve_expression)` / pk-shortcut; that is NOT this instance's gold patch and is irrelevant — the SWE-bench gold for base_commit 8dd5877f is the simple insertion, which I used.)

FAITHFULNESS ANALYSIS (model expandItems vs. real gold-patched loop, under the mapping.md §2 bijection OrderBy↔expr e, str↔name n, (obj,False)↔(e,false)):
1. OrderBy path (the ONLY behavior the spec pins deeply): model contributes exactly [(e,false)] and never routes to resolution; real code appends exactly (item, False) and continues. Agree on all inputs.
2. Non-OrderBy path: modeled as `resolve n`, a FREE universally-quantified total function (no Requires/Ensures). `out = expandItems resolve items` must hold for EVERY resolve, so the spec pins nothing about the unchanged recursive callee — it cannot be too strong there; any real find_ordering_name behavior on a name item is representable by some resolve. This is a correct application of directive 7 (free input strictly weaker than any concrete callee); G-AX correctly has nothing to check.
3. Ordering/accumulation: left-to-right ++ concatenation matches Python extend/append order; the backward `while i>0` fold is proven equal to expandItems via expandItems_drop_step (invariant result = expandItems resolve (items.drop i)).
4. Partial-correctness semantics: model does not over-claim termination/non-crash of the real code; it only asserts the concatenation shape the real loop produces.

G-CONF re-run independently: conformance_check.py exits 0 — the transliterated shadow (expandItems) agrees with the gold-patched oracle loop on 100,005 specifications (5 boundary incl. the F2P OrderBy(F(...)) scenario + 100k fuzz, seed=11555), 0 disagreements. Oracle choice (transliterate patched control flow, share the same free `resolve` closure with the shadow) is sound: the recursive resolution is unchanged by the patch, so only the OrderBy dispatch is under differential test — exactly the behavioral content of the fix.

No diverging input found on any path. The spec is neither too strong nor drifting: it is exactly as strong as the gold patch's behavioral change and no stronger. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True). Lexical G-LEAK screen passes (rep.passed=True, no hard_failures); relaxed_leakage not set. Reviewed the full velvet spec view (axioms/pure/pre/post + method signature + ensures) for gold-patch reconstruction beyond the public problem_statement.

Public problem_statement already discloses the discriminating fact: the crash is because 'the field is an OrderBy object, not a string, during get_order_dir' when Meta.ordering contains expressions — i.e. an OrderBy expression must not be routed through the field-name (string) parsing path. The spec view encodes exactly this behavior abstractly: itemContribution maps `.expr e => [(e, false)]` (taken as-is) vs `.name n => resolve n` (recursive resolution), with postcondition out = expandItems resolve items. This is the same semantic content the problem_statement gives, not more.

No gold-patch lexical specifics appear in the spec view: no isinstance/OrderBy/results.append/continue/find_ordering_name/opts.ordering/compiler.py tokens. Symbols are abstract (Item.expr/Item.name, Int identities, free `resolve`). The repo binding, exact patched function, and the `isinstance(item, OrderBy)` guard shape live only in mapping.md and refinement.md, which are auditor docs and NOT part of the consumer spec view. The `false` flag is a correctness property of the modeled Pair output type, not a location/form hint for the edit.

A faithful spec necessarily pins the correct output behavior; here that pinning stays at the abstraction level already implied by problem_statement and carries no gold-edit-reconstruction detail. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
