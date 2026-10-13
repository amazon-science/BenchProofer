# P2 adversarial audit — sympy__sympy-12489

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,7 @@
   if b ≠ [] then
     let bc := completeTo b a.length
     perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
-  return { arr := perm, fam := self.fam }
+  return { arr := perm, fam := 0 }
 -- impl-end
 
 -- proof-start
@@ -89,7 +89,7 @@
   unfold problem_spec_mul implementation_mul composeArr
   by_cases h : other.arr = []
   · simp only [Id.run, h, if_pos, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨rfl, ?_⟩ <;> first | rfl | simp | decide
   · simp only [Id.run, h, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨rfl, ?_⟩ <;> first | rfl | simp | decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,7 @@
   if b ≠ [] then
     let bc := completeTo b a.length
     perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
-  return { arr := perm, fam := self.fam }
+  return { arr := perm, fam := other.fam }
 -- impl-end
 
 -- proof-start
@@ -89,7 +89,7 @@
   unfold problem_spec_mul implementation_mul composeArr
   by_cases h : other.arr = []
   · simp only [Id.run, h, if_pos, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨rfl, ?_⟩ <;> first | rfl | simp | decide
   · simp only [Id.run, h, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨rfl, ?_⟩ <;> first | rfl | simp | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,12 +73,7 @@
 -- impl-start
 def implementation_mul (self other : Arr) : Arr := Id.run do
   let a := self.arr
-  let b := other.arr
-  let mut perm : List Int := a
-  if b ≠ [] then
-    let bc := completeTo b a.length
-    perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
-  return { arr := perm, fam := self.fam }
+  return { arr := a, fam := self.fam }
 -- impl-end
 
 -- proof-start
@@ -89,7 +84,7 @@
   unfold problem_spec_mul implementation_mul composeArr
   by_cases h : other.arr = []
   · simp only [Id.run, h, if_pos, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨?_, rfl⟩ <;> first | rfl | simp | decide
   · simp only [Id.run, h, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨?_, rfl⟩ <;> first | rfl | simp | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -74,10 +74,10 @@
 def implementation_mul (self other : Arr) : Arr := Id.run do
   let a := self.arr
   let b := other.arr
-  let mut perm : List Int := a
-  if b ≠ [] then
-    let bc := completeTo b a.length
-    perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
+  let mut perm : List Int := b
+  if a ≠ [] then
+    let ac := completeTo a b.length
+    perm := (b.map (fun i => ac.getD i.toNat 0)) ++ ac.drop b.length
   return { arr := perm, fam := self.fam }
 -- impl-end
 
@@ -89,7 +89,7 @@
   unfold problem_spec_mul implementation_mul composeArr
   by_cases h : other.arr = []
   · simp only [Id.run, h, if_pos, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨?_, rfl⟩ <;> first | rfl | simp | decide
   · simp only [Id.run, h, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨?_, rfl⟩ <;> first | rfl | simp | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
   let mut perm : List Int := a
   if b ≠ [] then
     let bc := completeTo b a.length
-    perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
+    perm := (a.map (fun i => bc.getD i.toNat 0))
   return { arr := perm, fam := self.fam }
 -- impl-end
 
@@ -89,7 +89,7 @@
   unfold problem_spec_mul implementation_mul composeArr
   by_cases h : other.arr = []
   · simp only [Id.run, h, if_pos, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨?_, rfl⟩ <;> first | rfl | simp | decide
   · simp only [Id.run, h, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨?_, rfl⟩ <;> first | rfl | simp | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,9 @@
   let a := self.arr
   let b := other.arr
   let mut perm : List Int := a
-  if b ≠ [] then
+  if b = [] then
+    perm := []
+  else
     let bc := completeTo b a.length
     perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
   return { arr := perm, fam := self.fam }
@@ -89,7 +91,7 @@
   unfold problem_spec_mul implementation_mul composeArr
   by_cases h : other.arr = []
   · simp only [Id.run, h, if_pos, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨?_, rfl⟩ <;> first | rfl | simp | decide
   · simp only [Id.run, h, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨?_, rfl⟩ <;> first | rfl | simp | decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,7 @@
   if b ≠ [] then
     let bc := completeTo b a.length
     perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
-  return { arr := perm, fam := self.fam }
+  return { arr := perm, fam := self.fam + 1 }
 -- impl-end
 
 -- proof-start
@@ -89,7 +89,7 @@
   unfold problem_spec_mul implementation_mul composeArr
   by_cases h : other.arr = []
   · simp only [Id.run, h, if_pos, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨rfl, ?_⟩ <;> first | rfl | simp | omega | decide
   · simp only [Id.run, h, ite_not]
-    exact ⟨rfl, rfl⟩
+    refine ⟨rfl, ?_⟩ <;> first | rfl | simp | omega | decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Composing two arrangements.

An arrangement is a finite reindexing (a permutation of `0 … n-1`) carried as its
mapping together with a tag identifying the *family* it belongs to — a base
family and any number of distinct specialised families that refine it.

Composing arrangement `self` with arrangement `other` produces a new arrangement
whose two observable parts are determined as follows:

  * its **mapping** is the composition of the two mappings: where the second
    operand has fewer entries than the first it is first completed by the
    identity so both range over the same indices, and then the first mapping is
    applied through the second (with any trailing entries of the completed second
    mapping carried over). When the second operand is empty the first mapping is
    returned unchanged.

  * its **family** is the family of the left operand: the arrangement obtained
    from a composition belongs to the same family as the value the composition
    was taken on, so a value of a specialised family composes to a value of that
    same specialised family.

Both parts are pinned to the inputs, so no component of the result is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The two observable parts of the
-- result — the composed mapping and the family tag — are both built directly
-- from the inputs (a list computation and a field copy), so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- An arrangement: its `arr` mapping (a list of indices) together with a `fam`
tag identifying its family (`0` is the base family; any other value a distinct
specialised family). -/
structure Arr where
  arr : List Int
  fam : Nat
deriving Repr, DecidableEq

/-- Complete the shorter mapping `b` with identity entries so it ranges over at
least the indices `0 … a.length-1`, leaving it unchanged when it is already at
least that long. -/
def completeTo (b : List Int) (n : Nat) : List Int :=
  b ++ (List.range' b.length (n - b.length)).map (fun k => (k : Int))

/-- The composition of two mappings, matching the index-wise definition: the
first mapping `a` is applied through the completed second mapping, and any
trailing entries of the completed second mapping beyond `a`'s length are carried
over. An empty second mapping leaves the first unchanged. -/
def composeArr (a b : List Int) : List Int :=
  if b = [] then a
  else
    let bc := completeTo b a.length
    (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
-- pure-end

-- post-conditions-start
/-- The produced arrangement is fully pinned to the two operands:

  * its mapping is exactly the composition of the two mappings, and
  * its family is exactly the family of the left operand.

Both components are determined for every input, so nothing is left free. -/
def problem_spec_mul (self other : Arr) (result : Arr) : Prop :=
  result.arr = composeArr self.arr other.arr ∧ result.fam = self.fam
-- post-conditions-end

-- impl-start
def implementation_mul (self other : Arr) : Arr := Id.run do
  let a := self.arr
  let b := other.arr
  let mut perm : List Int := a
  if b ≠ [] then
    let bc := completeTo b a.length
    perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
  return { arr := perm, fam := self.fam }
-- impl-end

-- proof-start
theorem correct_mul :
    ∀ (self other : Arr),
      problem_spec_mul self other (implementation_mul self other) := by
  intro self other
  unfold problem_spec_mul implementation_mul composeArr
  by_cases h : other.arr = []
  · simp only [Id.run, h, if_pos, ite_not]
    exact ⟨rfl, rfl⟩
  · simp only [Id.run, h, ite_not]
    exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins BOTH observable fields as exact total functions of the inputs: problem_spec_mul (frozen post-conditions) := result.arr = composeArr self.arr other.arr AND result.fam = self.fam, where composeArr/completeTo live in the frozen pure region. Both impl and proof regions collapse to placeholders in the lean spec view (_lean_spec_view), so attacks freely rewrite impl+proof while axioms/pure/post-conditions stay byte-identical — same_spec=True confirmed for all 7 attacks + positive control.

Protocol (all, verifications run concurrently ≤4 via background bash jobs, cmd: `bash scripts/lean_verify.sh <f>.lean`):
- pos_control.lean (correct impl, fam:=self.fam): EXIT=0 verifies. `#print axioms correct_mul` (pos_axcheck.lean) => depends on axioms: [propext, Quot.sound] — CLEAN, no sorryAx.
- atk_1 (prepatch bug, fam:=0 always): EXIT=1, unsolved goal `0 = self.fam`.
- atk_2 (fam:=other.fam, right-operand family): EXIT=1, `other.fam = self.fam` unprovable.
- atk_3 (control-flow effect: drop composition, arr:=a always): EXIT=1, arr mismatch vs composeArr in non-empty branch.
- atk_4 (swapped composition composeArr other.arr self.arr): EXIT=1, arr mismatch.
- atk_5 (boundary: drop the `++ bc.drop a.length` tail): EXIT=1, arr mismatch (missing trailing entries).
- atk_6 (control-flow: empty branch returns [] instead of a): EXIT=1, arr mismatch on empty-right-operand.
- atk_7 (off-by-one family tag, fam:=self.fam+1): EXIT=1, `self.fam+1 = self.fam` unprovable.

prepatch.lean (bundle Solution_prepatch.lean) reproduced: EXIT=1, unsolved `True ∧ 0 = self.fam` — the G-DIFF signal (prepatch construction ignores receiver class).

No wrong impl closed with a clean-axiom proof, so there is no faithful patch to materialize/resolve; verify⇏correct falsification is impossible here because the spec leaves no existential/free slack (both fields exactly determined). Attempted 7 DISTINCT wrong impls across all required families (partial-domain/tail-drop atk_5, boundary atk_6, control-flow-effect atk_3/atk_4, ungrounded/off-by family atk_1/atk_2/atk_7); ≥5 satisfied.

refinement.md audit: 6 legs — rows 1-3 = I (field reads + empty short-circuit), rows 4-5 = A-reference (composeArr/completeTo deep model of array-form composition, G-AX-validated vs real Permutation.__mul__().array_form; correspondence holds, compose_model mirrors composeArr), row 6 = R (self._af_new class-threading → fam:=self.fam via class↔Nat bijection, the discriminating clause). No A-consumed leg, no kind-3 (changed-inexpressible). All A-legs correspond to real callees. Sound.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

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

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Composing two arrangements.

An arrangement is a finite reindexing (a permutation of `0 … n-1`) carried as its
mapping together with a tag identifying the *family* it belongs to — a base
family and any number of distinct specialised families that refine it.

Composing arrangement `self` with arrangement `other` produces a new arrangement
whose two observable parts are determined as follows:

  * its **mapping** is the composition of the two mappings: where the second
    operand has fewer entries than the first it is first completed by the
    identity so both range over the same indices, and then the first mapping is
    applied through the second (with any trailing entries of the completed second
    mapping carried over). When the second operand is empty the first mapping is
    returned unchanged.

  * its **family** is the family of the left operand: the arrangement obtained
    from a composition belongs to the same family as the value the composition
    was taken on, so a value of a specialised family composes to a value of that
    same specialised family.

Both parts are pinned to the inputs, so no component of the result is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The two observable parts of the
-- result — the composed mapping and the family tag — are both built directly
-- from the inputs (a list computation and a field copy), so no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- An arrangement: its `arr` mapping (a list of indices) together with a `fam`
tag identifying its family (`0` is the base family; any other value a distinct
specialised family). -/
structure Arr where
  arr : List Int
  fam : Nat
deriving Repr, DecidableEq

/-- Complete the shorter mapping `b` with identity entries so it ranges over at
least the indices `0 … a.length-1`, leaving it unchanged when it is already at
least that long. -/
def completeTo (b : List Int) (n : Nat) : List Int :=
  b ++ (List.range' b.length (n - b.length)).map (fun k => (k : Int))

/-- The composition of two mappings, matching the index-wise definition: the
first mapping `a` is applied through the completed second mapping, and any
trailing entries of the completed second mapping beyond `a`'s length are carried
over. An empty second mapping leaves the first unchanged. -/
def composeArr (a b : List Int) : List Int :=
  if b = [] then a
  else
    let bc := completeTo b a.length
    (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
-- pure-end

-- post-conditions-start
/-- The produced arrangement is fully pinned to the two operands:

  * its mapping is exactly the composition of the two mappings, and
  * its family is exactly the family of the left operand.

Both components are determined for every input, so nothing is left free. -/
def problem_spec_mul (self other : Arr) (result : Arr) : Prop :=
  result.arr = composeArr self.arr other.arr ∧ result.fam = self.fam
-- post-conditions-end

-- impl-start
def implementation_mul (self other : Arr) : Arr := Id.run do
  let a := self.arr
  let b := other.arr
  let mut perm : List Int := a
  if b ≠ [] then
    let bc := completeTo b a.length
    perm := (a.map (fun i => bc.getD i.toNat 0)) ++ bc.drop a.length
  return { arr := perm, fam := self.fam }
-- impl-end

-- proof-start
theorem correct_mul :
    ∀ (self other : Arr),
      problem_spec_mul self other (implementation_mul self other) := by
  intro self other
  unfold problem_spec_mul implementation_mul composeArr
  by_cases h : other.arr = []
  · simp only [Id.run, h, if_pos, ite_not]
    exact ⟨rfl, rfl⟩
  · simp only [Id.run, h, ite_not]
    exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec fully pins BOTH observable fields as exact total functions of the inputs: problem_spec_mul (frozen post-conditions) := result.arr = composeArr self.arr other.arr AND result.fam = self.fam, where composeArr/completeTo live in the frozen pure region. Both impl and proof regions collapse to placeholders in the lean spec view (_lean_spec_view), so attacks freely rewrite impl+proof while axioms/pure/post-conditions stay byte-identical — same_spec=True confirmed for all 7 attacks + positive control.

Protocol (all, verifications run concurrently ≤4 via background bash jobs, cmd: `bash scripts/lean_verify.sh <f>.lean`):
- pos_control.lean (correct impl, fam:=self.fam): EXIT=0 verifies. `#print axioms correct_mul` (pos_axcheck.lean) => depends on axioms: [propext, Quot.sound] — CLEAN, no sorryAx.
- atk_1 (prepatch bug, fam:=0 always): EXIT=1, unsolved goal `0 = self.fam`.
- atk_2 (fam:=other.fam, right-operand family): EXIT=1, `other.fam = self.fam` unprovable.
- atk_3 (control-flow effect: drop composition, arr:=a always): EXIT=1, arr mismatch vs composeArr in non-empty branch.
- atk_4 (swapped composition composeArr other.arr self.arr): EXIT=1, arr mismatch.
- atk_5 (boundary: drop the `++ bc.drop a.length` tail): EXIT=1, arr mismatch (missing trailing entries).
- atk_6 (control-flow: empty branch returns [] instead of a): EXIT=1, arr mismatch on empty-right-operand.
- atk_7 (off-by-one family tag, fam:=self.fam+1): EXIT=1, `self.fam+1 = self.fam` unprovable.

prepatch.lean (bundle Solution_prepatch.lean) reproduced: EXIT=1, unsolved `True ∧ 0 = self.fam` — the G-DIFF signal (prepatch construction ignores receiver class).

No wrong impl closed with a clean-axiom proof, so there is no faithful patch to materialize/resolve; verify⇏correct falsification is impossible here because the spec leaves no existential/free slack (both fields exactly determined). Attempted 7 DISTINCT wrong impls across all required families (partial-domain/tail-drop atk_5, boundary atk_6, control-flow-effect atk_3/atk_4, ungrounded/off-by family atk_1/atk_2/atk_7); ≥5 satisfied.

refinement.md audit: 6 legs — rows 1-3 = I (field reads + empty short-circuit), rows 4-5 = A-reference (composeArr/completeTo deep model of array-form composition, G-AX-validated vs real Permutation.__mul__().array_form; correspondence holds, compose_model mirrors composeArr), row 6 = R (self._af_new class-threading → fam:=self.fam via class↔Nat bijection, the discriminating clause). No A-consumed leg, no kind-3 (changed-inexpressible). All A-legs correspond to real callees. Sound.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled function and the real repo callee. Evidence: (1) same_spec(Solution, Solution_prepatch)=True under LeanBackend tables — spec region byte-identical; prepatch impl (fam:=0) genuinely cannot close result.fam=self.fam, a valid G-DIFF signal, not a spec weakness. (2) lean_verify exit 0; #print axioms correct_mul = [propext, Quot.sound] — no sorryAx, proof is real. (3) Array component: composeArr == Permutation.__mul__().array_form on axiom_check.py's 50,009 probes plus my independent 20,000-case fuzz over valid permutations of varied/unequal sizes (incl. array_form truncation of trailing fixed points, identity products, empty operands, right shorter/longer needing identity pad) — 0 mismatches. getD default (0) provably never fires on valid permutations. (4) Family component: conformance_check.py's 120,008 cases (0 disagreements, seed 12489) plus my direct type-propagation probes (base/subclass x empty/nonempty x mismatched sizes) all confirm post-patch type(a*b)==type(a), matching result.fam=self.fam. The spec is neither too strong nor drifted: over the modeled domain it agrees with the real patched Permutation.__mul__ on every tested input, and I could construct no diverging input. Worktree already carries the gold patch (return self._af_new(perm)); base_commit aa9780761a behavior consistent.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no gold-patch line reproduced, no patched file path/module, no spec-view identifier or comment echoing a patched repo symbol, no bug/fix narration). same_spec(post,pre)=True (spec region byte-identical; discriminator lives only in the elided impl region). Semantic review: the spec view uses only abstract modeling vocabulary (Arr/fam/completeTo/composeArr/problem_spec_mul; 'arrangement/family/mapping'); NO repo symbols leak (no Permutation, _af_new, array_form, __mul__, Basic.__new__, permutations.py). The discriminating post-condition `result.fam = self.fam` ('family is the family of the left operand') is NOT information beyond the public problem_statement: the statement openly says the bug is that 'always instances of Permutation are returned' and requests the fix be 'use the mandatory reference to the class the method is called on for instance creation.' For __mul__ the receiver IS the left operand, so 'result carries the left operand's family' is a direct, publicly-derivable consequence of the stated fix, not new edit-localization. The mapping/composition prose describes the UNCHANGED code, not the gold edit. The actual discriminator (fam := self.fam vs prepatch fam := 0) is elided from the spec view. No leakage of the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
