# P2 adversarial audit — django__django-14089

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,14 +22,14 @@
   result = xs.reverse
 -- post-conditions-end
 
+
 -- impl-start
-/-- Enumerate the ordered collection's elements in reverse of their existing
-order. We walk the elements in their current order and prepend each onto an
-accumulator, so the element seen last ends up at the front. -/
+/-- Prepatch bug: no reverse enumeration; iterate forward, append to end,
+producing the original order (identity). -/
 def implementation_reversed (xs : List Int) : List Int := Id.run do
   let mut acc : List Int := []
   for x in xs do
-    acc := x :: acc
+    acc := acc ++ [x]
   return acc
 -- impl-end
 
@@ -41,17 +41,17 @@
   unfold problem_spec_reversed implementation_reversed
   have helper : ∀ (ys : List Int) (init : List Int),
       Id.run (forIn ys init
-        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))
-        = ys.reverse ++ init := by
+        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [x])))))
+        = init ++ ys := by
     intro ys
     induction ys with
-    | nil => intro init; rfl
+    | nil => intro init; simp [Id.run]
     | cons a as ih =>
       intro init
       rw [List.forIn_cons]
       simp only [Id.run, bind] at ih ⊢
       rw [ih]
-      simp [List.reverse_cons]
+      simp
   show Id.run (forIn xs [] _) = xs.reverse
   rw [helper xs []]
   simp
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,15 +22,10 @@
   result = xs.reverse
 -- post-conditions-end
 
+
 -- impl-start
-/-- Enumerate the ordered collection's elements in reverse of their existing
-order. We walk the elements in their current order and prepend each onto an
-accumulator, so the element seen last ends up at the front. -/
-def implementation_reversed (xs : List Int) : List Int := Id.run do
-  let mut acc : List Int := []
-  for x in xs do
-    acc := x :: acc
-  return acc
+/-- Wrong: returns the members in their original order (identity), no reversal. -/
+def implementation_reversed (xs : List Int) : List Int := xs
 -- impl-end
 
 -- proof-start
@@ -39,20 +34,5 @@
     problem_spec_reversed xs (implementation_reversed xs) := by
   intro xs
   unfold problem_spec_reversed implementation_reversed
-  have helper : ∀ (ys : List Int) (init : List Int),
-      Id.run (forIn ys init
-        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))
-        = ys.reverse ++ init := by
-    intro ys
-    induction ys with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [List.reverse_cons]
-  show Id.run (forIn xs [] _) = xs.reverse
-  rw [helper xs []]
-  simp
+  rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,15 +22,15 @@
   result = xs.reverse
 -- post-conditions-end
 
+
 -- impl-start
-/-- Enumerate the ordered collection's elements in reverse of their existing
-order. We walk the elements in their current order and prepend each onto an
-accumulator, so the element seen last ends up at the front. -/
-def implementation_reversed (xs : List Int) : List Int := Id.run do
-  let mut acc : List Int := []
-  for x in xs do
-    acc := x :: acc
-  return acc
+/-- Partial-domain wrong: reverse only for lists of length <= 1 (where reversal
+is a no-op anyway), identity otherwise. -/
+def implementation_reversed (xs : List Int) : List Int :=
+  match xs with
+  | [] => []
+  | [a] => [a]
+  | _ => xs
 -- impl-end
 
 -- proof-start
@@ -39,20 +39,10 @@
     problem_spec_reversed xs (implementation_reversed xs) := by
   intro xs
   unfold problem_spec_reversed implementation_reversed
-  have helper : ∀ (ys : List Int) (init : List Int),
-      Id.run (forIn ys init
-        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))
-        = ys.reverse ++ init := by
-    intro ys
-    induction ys with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [List.reverse_cons]
-  show Id.run (forIn xs [] _) = xs.reverse
-  rw [helper xs []]
-  simp
+  cases xs with
+  | nil => rfl
+  | cons a as =>
+    cases as with
+    | nil => rfl
+    | cons b bs => simp
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,15 +22,10 @@
   result = xs.reverse
 -- post-conditions-end
 
+
 -- impl-start
-/-- Enumerate the ordered collection's elements in reverse of their existing
-order. We walk the elements in their current order and prepend each onto an
-accumulator, so the element seen last ends up at the front. -/
-def implementation_reversed (xs : List Int) : List Int := Id.run do
-  let mut acc : List Int := []
-  for x in xs do
-    acc := x :: acc
-  return acc
+/-- Boundary wrong: reverse but drop the first produced element (off-by-one). -/
+def implementation_reversed (xs : List Int) : List Int := xs.reverse.tail
 -- impl-end
 
 -- proof-start
@@ -39,20 +34,7 @@
     problem_spec_reversed xs (implementation_reversed xs) := by
   intro xs
   unfold problem_spec_reversed implementation_reversed
-  have helper : ∀ (ys : List Int) (init : List Int),
-      Id.run (forIn ys init
-        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))
-        = ys.reverse ++ init := by
-    intro ys
-    induction ys with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [List.reverse_cons]
-  show Id.run (forIn xs [] _) = xs.reverse
-  rw [helper xs []]
-  simp
+  cases xs with
+  | nil => rfl
+  | cons a as => simp
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,15 +22,17 @@
   result = xs.reverse
 -- post-conditions-end
 
+
 -- impl-start
-/-- Enumerate the ordered collection's elements in reverse of their existing
-order. We walk the elements in their current order and prepend each onto an
-accumulator, so the element seen last ends up at the front. -/
+/-- Control-flow wrong: proper reverse fold but appends an extra copy of the last
+processed element at the end. -/
 def implementation_reversed (xs : List Int) : List Int := Id.run do
   let mut acc : List Int := []
   for x in xs do
     acc := x :: acc
-  return acc
+  match xs with
+  | [] => return acc
+  | h :: _ => return acc ++ [h]
 -- impl-end
 
 -- proof-start
@@ -39,20 +41,7 @@
     problem_spec_reversed xs (implementation_reversed xs) := by
   intro xs
   unfold problem_spec_reversed implementation_reversed
-  have helper : ∀ (ys : List Int) (init : List Int),
-      Id.run (forIn ys init
-        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))
-        = ys.reverse ++ init := by
-    intro ys
-    induction ys with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [List.reverse_cons]
-  show Id.run (forIn xs [] _) = xs.reverse
-  rw [helper xs []]
-  simp
+  cases xs with
+  | nil => rfl
+  | cons a as => simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,15 +22,10 @@
   result = xs.reverse
 -- post-conditions-end
 
+
 -- impl-start
-/-- Enumerate the ordered collection's elements in reverse of their existing
-order. We walk the elements in their current order and prepend each onto an
-accumulator, so the element seen last ends up at the front. -/
-def implementation_reversed (xs : List Int) : List Int := Id.run do
-  let mut acc : List Int := []
-  for x in xs do
-    acc := x :: acc
-  return acc
+/-- Ungrounded wrong: always returns the empty list. -/
+def implementation_reversed (xs : List Int) : List Int := []
 -- impl-end
 
 -- proof-start
@@ -39,20 +34,7 @@
     problem_spec_reversed xs (implementation_reversed xs) := by
   intro xs
   unfold problem_spec_reversed implementation_reversed
-  have helper : ∀ (ys : List Int) (init : List Int),
-      Id.run (forIn ys init
-        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))
-        = ys.reverse ++ init := by
-    intro ys
-    induction ys with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [List.reverse_cons]
-  show Id.run (forIn xs [] _) = xs.reverse
-  rw [helper xs []]
-  simp
+  cases xs with
+  | nil => rfl
+  | cons a as => simp
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -22,15 +22,14 @@
   result = xs.reverse
 -- post-conditions-end
 
+
 -- impl-start
-/-- Enumerate the ordered collection's elements in reverse of their existing
-order. We walk the elements in their current order and prepend each onto an
-accumulator, so the element seen last ends up at the front. -/
-def implementation_reversed (xs : List Int) : List Int := Id.run do
-  let mut acc : List Int := []
-  for x in xs do
-    acc := x :: acc
-  return acc
+/-- Wrong: returns the reverse of the *tail-appended* list, i.e. append head at end
+then reverse — actually identity-ish; here we reverse xs++[head] extra dup at front. -/
+def implementation_reversed (xs : List Int) : List Int :=
+  match xs with
+  | [] => []
+  | h :: t => (h :: t).reverse ++ [h]
 -- impl-end
 
 -- proof-start
@@ -39,20 +38,7 @@
     problem_spec_reversed xs (implementation_reversed xs) := by
   intro xs
   unfold problem_spec_reversed implementation_reversed
-  have helper : ∀ (ys : List Int) (init : List Int),
-      Id.run (forIn ys init
-        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))
-        = ys.reverse ++ init := by
-    intro ys
-    induction ys with
-    | nil => intro init; rfl
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      rw [ih]
-      simp [List.reverse_cons]
-  show Id.run (forIn xs [] _) = xs.reverse
-  rw [helper xs []]
-  simp
+  cases xs with
+  | nil => rfl
+  | cons a as => simp
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Producing the elements of an
-- ordered collection in reverse of their existing order is the changed operation;
-- it is modeled deeply as an order-reversal over the element sequence (an
-- accumulator fold), not abstracted behind a callee. The proof agent may add
-- `_prop` axioms only if it gets genuinely stuck.
-- axioms-end

-- pure-start
-- (no auxiliary pure helpers needed; the spec is a direct order relation)
-- pure-end

-- post-conditions-start
/-- The reverse enumeration of an ordered collection. Given the collection's
elements in their existing order (`xs`), the produced sequence lists exactly the
same elements in the opposite order: the last element first and the first element
last. The result is fully determined by the input order — it is its reversal. -/
def problem_spec_reversed (xs : List Int) (result : List Int) : Prop :=
  result = xs.reverse
-- post-conditions-end

-- impl-start
/-- Enumerate the ordered collection's elements in reverse of their existing
order. We walk the elements in their current order and prepend each onto an
accumulator, so the element seen last ends up at the front. -/
def implementation_reversed (xs : List Int) : List Int := Id.run do
  let mut acc : List Int := []
  for x in xs do
    acc := x :: acc
  return acc
-- impl-end

-- proof-start
theorem correct_reversed :
    ∀ (xs : List Int),
    problem_spec_reversed xs (implementation_reversed xs) := by
  intro xs
  unfold problem_spec_reversed implementation_reversed
  have helper : ∀ (ys : List Int) (init : List Int),
      Id.run (forIn ys init
        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))
        = ys.reverse ++ init := by
    intro ys
    induction ys with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
      simp [List.reverse_cons]
  show Id.run (forIn xs [] _) = xs.reverse
  rw [helper xs []]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a TOTAL EXACT functional postcondition: problem_spec_reversed xs result := (result = xs.reverse), universally quantified over all xs : List Int. Axioms region is EMPTY (no A-legs, no ungrounded oracle to echo). Any impl deviating from xs.reverse on even one input cannot satisfy the goal.

refinement.md audit: 2 legs, R (carrier type refinement List Int <-> dict keys) and R/I (the changed op reversed(self.dict) modeled deeply as List.reverse via prepend-fold acc := x :: acc). No A-consumed / A-reference / kind-3 legs, correctly so: the changed callee is realized concretely, not axiomatized. R/I correspondence holds (dict.fromkeys -> insertion-ordered distinct keys; reversed(dict) yields last->first == xs.reverse; conformance_check.py validates differentially over 120k fuzzed inputs). Model<->patch correspondence sound.

Protocol: confirmed byte-identical spec via swebench_unified.markers.same_spec = True for the positive control and ALL 7 attacks.

Command template: bash scripts/lean_verify.sh <file>. Attacks verified concurrently in 2 batches of 4.

### RESULTS (exit code; 0=verifies, 1=proof/goal error):
- pos_control.lean (gold): exit 0 VERIFIES; #print axioms correct_reversed => [propext, Quot.sound] (clean, no sorryAx / no injected _prop).
- atk_1 (prepatch bug: forward-order append acc:=acc++[x], identity): exit 1, unsolved goals (helper proves = init++ys, contradicts xs.reverse).
- atk_2 (return xs, direct identity): exit 1, rfl failed (LHS xs != xs.reverse).
- atk_3 (partial-domain: reverse only for len<=1 where reversal is a no-op, identity otherwise): exit 1, unsolved goals on cons/cons case.
- atk_4 (boundary/off-by-one: xs.reverse.tail): exit 1, unsolved goals (drops last-produced element).
- atk_5 (control-flow-effect: proper reverse fold then append extra copy of head): exit 1, unsolved goals.
- atk_6 (ungrounded/constant: return []): exit 1, unsolved goals.
- atk_7 (control-flow: (h::t).reverse ++ [h], extra element): exit 1, unsolved goals.

No same-spec wrong impl produced a closing clean-axiom proof. Therefore there are NO faithful patches to materialize/resolve (patches={}); step 2 (resolve of a verifying wrong impl) is vacuously satisfied because no attack verified. The exact-functional postcondition leaves no slack for partial-domain, boundary, control-flow-effect, or ungrounded-oracle deviations. Prepatch bug reproduced as atk_1 (fails to close against the frozen spec, matching Solution_prepatch.lean's sorry-carrying G-DIFF signal). Verdict: SOUND. Verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Producing the elements of an
-- ordered collection in reverse of their existing order is the changed operation;
-- it is modeled deeply as an order-reversal over the element sequence (an
-- accumulator fold), not abstracted behind a callee. The proof agent may add
-- `_prop` axioms only if it gets genuinely stuck.
-- axioms-end

-- pure-start
-- (no auxiliary pure helpers needed; the spec is a direct order relation)
-- pure-end

-- post-conditions-start
/-- The reverse enumeration of an ordered collection. Given the collection's
elements in their existing order (`xs`), the produced sequence lists exactly the
same elements in the opposite order: the last element first and the first element
last. The result is fully determined by the input order — it is its reversal. -/
def problem_spec_reversed (xs : List Int) (result : List Int) : Prop :=
  result = xs.reverse
-- post-conditions-end

-- impl-start
/-- Enumerate the ordered collection's elements in reverse of their existing
order. We walk the elements in their current order and prepend each onto an
accumulator, so the element seen last ends up at the front. -/
def implementation_reversed (xs : List Int) : List Int := Id.run do
  let mut acc : List Int := []
  for x in xs do
    acc := x :: acc
  return acc
-- impl-end

-- proof-start
theorem correct_reversed :
    ∀ (xs : List Int),
    problem_spec_reversed xs (implementation_reversed xs) := by
  intro xs
  unfold problem_spec_reversed implementation_reversed
  have helper : ∀ (ys : List Int) (init : List Int),
      Id.run (forIn ys init
        (fun x r => (do pure PUnit.unit; pure (ForInStep.yield (x :: r)))))
        = ys.reverse ++ init := by
    intro ys
    induction ys with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
      simp [List.reverse_cons]
  show Id.run (forIn xs [] _) = xs.reverse
  rw [helper xs []]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is a TOTAL EXACT functional postcondition: problem_spec_reversed xs result := (result = xs.reverse), universally quantified over all xs : List Int. Axioms region is EMPTY (no A-legs, no ungrounded oracle to echo). Any impl deviating from xs.reverse on even one input cannot satisfy the goal.

refinement.md audit: 2 legs, R (carrier type refinement List Int <-> dict keys) and R/I (the changed op reversed(self.dict) modeled deeply as List.reverse via prepend-fold acc := x :: acc). No A-consumed / A-reference / kind-3 legs, correctly so: the changed callee is realized concretely, not axiomatized. R/I correspondence holds (dict.fromkeys -> insertion-ordered distinct keys; reversed(dict) yields last->first == xs.reverse; conformance_check.py validates differentially over 120k fuzzed inputs). Model<->patch correspondence sound.

Protocol: confirmed byte-identical spec via swebench_unified.markers.same_spec = True for the positive control and ALL 7 attacks.

Command template: bash scripts/lean_verify.sh <file>. Attacks verified concurrently in 2 batches of 4.

### RESULTS (exit code; 0=verifies, 1=proof/goal error):
- pos_control.lean (gold): exit 0 VERIFIES; #print axioms correct_reversed => [propext, Quot.sound] (clean, no sorryAx / no injected _prop).
- atk_1 (prepatch bug: forward-order append acc:=acc++[x], identity): exit 1, unsolved goals (helper proves = init++ys, contradicts xs.reverse).
- atk_2 (return xs, direct identity): exit 1, rfl failed (LHS xs != xs.reverse).
- atk_3 (partial-domain: reverse only for len<=1 where reversal is a no-op, identity otherwise): exit 1, unsolved goals on cons/cons case.
- atk_4 (boundary/off-by-one: xs.reverse.tail): exit 1, unsolved goals (drops last-produced element).
- atk_5 (control-flow-effect: proper reverse fold then append extra copy of head): exit 1, unsolved goals.
- atk_6 (ungrounded/constant: return []): exit 1, unsolved goals.
- atk_7 (control-flow: (h::t).reverse ++ [h], extra element): exit 1, unsolved goals.

No same-spec wrong impl produced a closing clean-axiom proof. Therefore there are NO faithful patches to materialize/resolve (patches={}); step 2 (resolve of a verifying wrong impl) is vacuously satisfied because no attack verified. The exact-functional postcondition leaves no slack for partial-domain, boundary, control-flow-effect, or ungrounded-oracle deviations. Prepatch bug reproduced as atk_1 (fails to close against the frozen spec, matching Solution_prepatch.lean's sorry-carrying G-DIFF signal). Verdict: SOUND. Verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real callee. (1) Spec region byte-identical: markers.same_spec(Solution, Solution_prepatch, lean-backend) = True; frozen spec is `problem_spec_reversed xs result := result = xs.reverse`. (2) Proof is genuine: lean_verify.sh exit 0; `#print axioms correct_reversed` = [propext, Quot.sound] only — no sorryAx / no _prop axioms. (3) Modeling boundary is faithful: real callee OrderedSet.__reversed__ = `return reversed(self.dict)`, where self.dict = dict.fromkeys(iterable) so its keys are the distinct members in first-seen order; reversed(self.dict) yields those keys last->first. The model binds xs = the deduped ordered-key list and asserts result = xs.reverse = exactly reverse insertion order. Dedup happens at carrier construction (before the modeled boundary), so xs already equals self.dict's key sequence — the spec matches the callee on its entire domain. The iterator-vs-list distinction is a Python protocol artifact correctly scoped out (F2P materializes with list()). (4) Conformance corroborates: conformance_check.py = 120007 fuzzed inputs (duplicates/empty/singleton/negatives), 0 disagreements vs an independent reconstruction list(reversed(dict.fromkeys(raw))), seed 14089. No diverging input exists; spec is neither too strong nor drifting. Not a defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl + proof regions elided) contains only: abstract axioms/pure comments, the docstring for problem_spec_reversed, and `def problem_spec_reversed (xs result) : Prop := result = xs.reverse`. Mechanical leakage.screen() PASSED with zero hard failures — no diff markers, no reproduced gold-patch line, no patched file path (django/utils/datastructures.py) or dotted module path, no spec-view identifier embedding a patched symbol, no bug/fix narration. Crucially, the public problem_statement itself fully describes the gold edit ('Allow calling reversed() on an OrderedSet ... by adding a __reversed__() method'), so the reversal behavior is already public. The spec merely formalizes reverse-order enumeration (result = xs.reverse) — exactly the task — and never names __reversed__, reversed, self.dict, OrderedSet, or the patched module. same_spec confirms the spec region is byte-identical between Solution.lean and Solution_prepatch.lean, so the discriminator resides only in the elided impl/proof. Nothing leaks beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
