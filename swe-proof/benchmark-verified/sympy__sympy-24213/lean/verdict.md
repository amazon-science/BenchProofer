# P2 adversarial audit — sympy__sympy-24213

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The frozen spec is a COMPLETE functional equality with an EMPTY axioms region and no opaque/axiom callees: problem_spec pins result = (if allDimsMatch head addends then some (summedFactor head addends, head.2) else none), where allDimsMatch = every addend's canonical deps equals head's deps, and summedFactor = head.1 + Σ addend factors. Any impl whose correct_ closes is therefore extensionally equal to this single function (= the post-patch deps-equivalence semantics). No verifying-but-wrong impl exists, so no faithful-patch resolve obligation arises. All 7 same-spec wrong impls failed to verify (exit 1, genuine proof errors).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
   let dim := head.2
   let mut factor := head.1
   for a in addends do
-    if dim.deps ≠ a.2.deps then
+    if dim.name ≠ a.2.name then
       return none
     factor := factor + a.1
   return some (factor, dim)
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,8 +82,6 @@
   let dim := head.2
   let mut factor := head.1
   for a in addends do
-    if dim.deps ≠ a.2.deps then
-      return none
     factor := factor + a.1
   return some (factor, dim)
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,11 +80,10 @@
     (head : Rat × Dim) (addends : List (Rat × Dim)) :
     Option (Rat × Dim) := Id.run do
   let dim := head.2
-  let mut factor := head.1
+  let factor := head.1
   for a in addends do
     if dim.deps ≠ a.2.deps then
       return none
-    factor := factor + a.1
   return some (factor, dim)
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -82,7 +82,7 @@
   let dim := head.2
   let mut factor := head.1
   for a in addends do
-    if dim.deps ≠ a.2.deps then
+    if dim.deps = a.2.deps then
       return none
     factor := factor + a.1
   return some (factor, dim)
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,12 +79,13 @@
 def implementation_factorAndDimensionOfSum
     (head : Rat × Dim) (addends : List (Rat × Dim)) :
     Option (Rat × Dim) := Id.run do
-  let dim := head.2
+  let mut dim := head.2
   let mut factor := head.1
   for a in addends do
     if dim.deps ≠ a.2.deps then
       return none
     factor := factor + a.1
+    dim := a.2
   return some (factor, dim)
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
     Option (Rat × Dim) := Id.run do
   let dim := head.2
   let mut factor := head.1
-  for a in addends do
+  for a in addends.tail do
     if dim.deps ≠ a.2.deps then
       return none
     factor := factor + a.1
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,11 +81,15 @@
     Option (Rat × Dim) := Id.run do
   let dim := head.2
   let mut factor := head.1
-  for a in addends do
+  match addends with
+  | [] => return some (factor, dim)
+  | a :: rest =>
     if dim.deps ≠ a.2.deps then
       return none
     factor := factor + a.1
-  return some (factor, dim)
+    for b in rest do
+      factor := factor + b.1
+    return some (factor, dim)
 -- impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Combining the scale factor and the dimension of a *sum* of dimensional
quantities.

A dimensional quantity carries a rational scale factor together with a
dimension. A dimension is described two ways at once: by its surface symbolic
identity (`name`), and by its canonical reduction to integer powers of base
dimensions (`deps`, an association list pairing each base dimension with its
exponent). Two dimensions are considered the *same physical dimension* exactly
when these canonical base-dimension power maps coincide — even when their
surface identities are written differently (for instance a quantity recorded
directly as one dimension versus the product of two others that reduces to the
same base powers).

Forming the sum requires all addends to share the head addend's physical
dimension. The combination is computed by taking the head addend's
`(scaleFactor, dimension)` and folding the remaining addends in left-to-right
order: each remaining addend is required to have the *same physical dimension*
as the head — comparison is on the canonical base-dimension power map, so two
differently-written but physically equal dimensions are accepted — and when it
does, its scale factor is added to the running total. If any addend's physical
dimension differs from the head's, the sum is undefined (no result). When every
addend matches, the result is the total scale factor paired with the head
addend's dimension (the dimension component is carried through unchanged).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- physical-dimension comparison is modeled DEEPLY: a dimension is paired with
-- its canonical base-dimension power map (`deps`), and "same physical
-- dimension" is equality of those maps. Rational scale-factor addition is the
-- field operation on `Rat`. No `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A dimension, described both by its surface symbolic identity (`name`) and by
its canonical reduction to integer powers of base dimensions (`deps`, an
association list base-dimension ↦ exponent). Two dimensions denote the same
physical dimension exactly when their `deps` maps coincide. The `deps` list is
canonical: sorted by key with no zero exponents, so list equality is map
equality. -/
structure Dim where
  name : String
  deps : List (String × Int)
deriving DecidableEq, Repr

/-- The combined scale factor when every addend shares the head's physical
dimension: the head's factor plus the sum of all addend factors. -/
def summedFactor (head : Rat × Dim) (addends : List (Rat × Dim)) : Rat :=
  head.1 + (addends.map Prod.fst).sum

/-- All addends share the head addend's physical dimension (canonical
base-dimension power maps coincide). -/
def allDimsMatch (head : Rat × Dim) (addends : List (Rat × Dim)) : Bool :=
  addends.all (fun a => decide (a.2.deps = head.2.deps))
-- pure-end

-- post-conditions-start
/-- The outcome of combining a sum's addends. When every addend shares the head
addend's physical dimension — compared via the canonical base-dimension power
map — the result is `some (totalFactor, headDimension)`: the summed scale factor
paired with the head addend's dimension carried through unchanged. When any
addend's physical dimension differs from the head's, there is no result
(`none`). -/
def problem_spec_factorAndDimensionOfSum
    (head : Rat × Dim) (addends : List (Rat × Dim))
    (result : Option (Rat × Dim)) : Prop :=
  result =
    (if allDimsMatch head addends then
        some (summedFactor head addends, head.2)
      else
        none)
-- post-conditions-end

-- impl-start
def implementation_factorAndDimensionOfSum
    (head : Rat × Dim) (addends : List (Rat × Dim)) :
    Option (Rat × Dim) := Id.run do
  let dim := head.2
  let mut factor := head.1
  for a in addends do
    if dim.deps ≠ a.2.deps then
      return none
    factor := factor + a.1
  return some (factor, dim)
-- impl-end


-- proof-start
theorem correct_factorAndDimensionOfSum
    (head : Rat × Dim) (addends : List (Rat × Dim)) :
    problem_spec_factorAndDimensionOfSum head addends
      (implementation_factorAndDimensionOfSum head addends) := by
  simp only [problem_spec_factorAndDimensionOfSum, implementation_factorAndDimensionOfSum,
    Id.run, allDimsMatch, summedFactor]
  generalize head.1 = c
  induction addends generalizing c with
  | nil => simp; rfl
  | cons a as ih =>
    simp only [List.forIn_cons, List.all_cons, List.map_cons, List.sum_cons]
    by_cases h : head.2.deps = a.2.deps
    · simp only [ne_eq, not_true_eq_false, decide_true, Bool.true_and, reduceIte,
        pure_bind, h] at ih ⊢
      rw [ih]
      by_cases h2 : (as.all fun x => decide (x.2.deps = a.2.deps)) = true <;>
        simp only [h2, if_true] <;> [skip; rfl] <;> congr 2 <;> ring
    · rw [if_pos h, if_neg (by
        simp only [Bool.and_eq_true, decide_eq_true_eq, not_and]
        intro hcon _; exact absurd hcon.symm h)]
      rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL executed same_spec confirmed True for all 7 attacks and the positive control (swebench_unified.markers.same_spec, lean backend). Verifications run concurrently in two background batches of 4 (≤4 at a time) via scripts/lean_verify.sh <file>.

POSITIVE CONTROL (pos_control.lean = official Solution.lean): `bash scripts/lean_verify.sh pos_control.lean` -> exit 0 (only cosmetic unnecessarySeqFocus linter warnings). Appended `#print axioms correct_factorAndDimensionOfSum` (pos_axcheck.lean) -> exit 0, axioms = [propext, Classical.choice, Quot.sound] — CLEAN, no sorryAx.

ATTACKS (all edit ONLY the impl region; original gold proof body retained; all exit 1 = genuine proof error, NOT sorry(3)/timeout(124)):
- atk_1 (prepatch bug: branch on dim.name ≠ a.2.name instead of deps): exit 1, `rewrite failed`. This reproduces Solution_prepatch.lean's fixed behavior -> prepatch_reproduced=true.
- atk_2 (no compatibility check; always sums, always some): exit 1, rewrite failed.
- atk_3 (never accumulates addend factors; returns head factor): exit 1.
- atk_4 (inverted condition: returns none when dims MATCH): exit 1.
- atk_5 (control-flow-effect: carries LAST addend dim instead of head dim): exit 1.
- atk_6 (boundary/off-by-one: iterates addends.tail, drops first addend's check+factor): exit 1.
- atk_7 (partial-domain/ungrounded-echo: checks only head vs first addend, sums rest unchecked): exit 1.

STEP 2 (materialize+resolve): VACUOUS by construction — zero wrong impls closed with clean axioms, so there is no closing-clean-axiom impl whose faithful patch could fail to resolve. Nothing to run through run_resolve. Reported as executed evidence, not speculation: the 7 verify runs are the falsification attempts and none produced a closing proof.

REFINEMENT.MD AUDIT (§4 correspondence): 6 legs, all tagged R (steps 1-5) or I (step 6); axioms region byte-empty; NO A-consumed / A-reference / kind-3 legs. The single changed op (addend compatibility) is modeled DEEPLY as Dim.deps equality, NOT axiomatized — SPEC_GUIDE §3 compliant. The deep-model correspondence Dim.deps-equality ↔ equivalent_dims (= dict equality of get_dimensional_dependencies, dimensions.py:428) holds against the real base_commit callee (confirmed via mapping.md + verdict.md Role-3 worktree check: equivalent_dims(velocity, acceleration*time)=True same deps {L:1,T:-1}; equivalent_dims(velocity, time)=False). R/I legs additionally covered mechanically by G-CONF (conformance_check.py present). Recursive sub-calls _collect_factor_and_dimension are unchanged behavior taken as inputs (head/addends) — legitimate R, no flag dependence.

CONCLUSION: verify⇒correct holds. The spec admits no verifying wrong impl; no A-leg or ungrounded oracle to exploit. SOUND (≥5 distinct attacks — 7 — run; none breaks it).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The frozen spec is a COMPLETE functional equality with an EMPTY axioms region and no opaque/axiom callees: problem_spec pins result = (if allDimsMatch head addends then some (summedFactor head addends, head.2) else none), where allDimsMatch = every addend's canonical deps equals head's deps, and summedFactor = head.1 + Σ addend factors. Any impl whose correct_ closes is therefore extensionally equal to this single function (= the post-patch deps-equivalence semantics). No verifying-but-wrong impl exists, so no faithful-patch resolve obligation arises. All 7 same-spec wrong impls failed to verify (exit 1, genuine proof errors).
```

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
Combining the scale factor and the dimension of a *sum* of dimensional
quantities.

A dimensional quantity carries a rational scale factor together with a
dimension. A dimension is described two ways at once: by its surface symbolic
identity (`name`), and by its canonical reduction to integer powers of base
dimensions (`deps`, an association list pairing each base dimension with its
exponent). Two dimensions are considered the *same physical dimension* exactly
when these canonical base-dimension power maps coincide — even when their
surface identities are written differently (for instance a quantity recorded
directly as one dimension versus the product of two others that reduces to the
same base powers).

Forming the sum requires all addends to share the head addend's physical
dimension. The combination is computed by taking the head addend's
`(scaleFactor, dimension)` and folding the remaining addends in left-to-right
order: each remaining addend is required to have the *same physical dimension*
as the head — comparison is on the canonical base-dimension power map, so two
differently-written but physically equal dimensions are accepted — and when it
does, its scale factor is added to the running total. If any addend's physical
dimension differs from the head's, the sum is undefined (no result). When every
addend matches, the result is the total scale factor paired with the head
addend's dimension (the dimension component is carried through unchanged).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- physical-dimension comparison is modeled DEEPLY: a dimension is paired with
-- its canonical base-dimension power map (`deps`), and "same physical
-- dimension" is equality of those maps. Rational scale-factor addition is the
-- field operation on `Rat`. No `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A dimension, described both by its surface symbolic identity (`name`) and by
its canonical reduction to integer powers of base dimensions (`deps`, an
association list base-dimension ↦ exponent). Two dimensions denote the same
physical dimension exactly when their `deps` maps coincide. The `deps` list is
canonical: sorted by key with no zero exponents, so list equality is map
equality. -/
structure Dim where
  name : String
  deps : List (String × Int)
deriving DecidableEq, Repr

/-- The combined scale factor when every addend shares the head's physical
dimension: the head's factor plus the sum of all addend factors. -/
def summedFactor (head : Rat × Dim) (addends : List (Rat × Dim)) : Rat :=
  head.1 + (addends.map Prod.fst).sum

/-- All addends share the head addend's physical dimension (canonical
base-dimension power maps coincide). -/
def allDimsMatch (head : Rat × Dim) (addends : List (Rat × Dim)) : Bool :=
  addends.all (fun a => decide (a.2.deps = head.2.deps))
-- pure-end

-- post-conditions-start
/-- The outcome of combining a sum's addends. When every addend shares the head
addend's physical dimension — compared via the canonical base-dimension power
map — the result is `some (totalFactor, headDimension)`: the summed scale factor
paired with the head addend's dimension carried through unchanged. When any
addend's physical dimension differs from the head's, there is no result
(`none`). -/
def problem_spec_factorAndDimensionOfSum
    (head : Rat × Dim) (addends : List (Rat × Dim))
    (result : Option (Rat × Dim)) : Prop :=
  result =
    (if allDimsMatch head addends then
        some (summedFactor head addends, head.2)
      else
        none)
-- post-conditions-end

-- impl-start
def implementation_factorAndDimensionOfSum
    (head : Rat × Dim) (addends : List (Rat × Dim)) :
    Option (Rat × Dim) := Id.run do
  let dim := head.2
  let mut factor := head.1
  for a in addends do
    if dim.deps ≠ a.2.deps then
      return none
    factor := factor + a.1
  return some (factor, dim)
-- impl-end


-- proof-start
theorem correct_factorAndDimensionOfSum
    (head : Rat × Dim) (addends : List (Rat × Dim)) :
    problem_spec_factorAndDimensionOfSum head addends
      (implementation_factorAndDimensionOfSum head addends) := by
  simp only [problem_spec_factorAndDimensionOfSum, implementation_factorAndDimensionOfSum,
    Id.run, allDimsMatch, summedFactor]
  generalize head.1 = c
  induction addends generalizing c with
  | nil => simp; rfl
  | cons a as ih =>
    simp only [List.forIn_cons, List.all_cons, List.map_cons, List.sum_cons]
    by_cases h : head.2.deps = a.2.deps
    · simp only [ne_eq, not_true_eq_false, decide_true, Bool.true_and, reduceIte,
        pure_bind, h] at ih ⊢
      rw [ih]
      by_cases h2 : (as.all fun x => decide (x.2.deps = a.2.deps)) = true <;>
        simp only [h2, if_true] <;> [skip; rfl] <;> congr 2 <;> ring
    · rw [if_pos h, if_neg (by
        simp only [Bool.and_eq_true, decide_eq_true_eq, not_and]
        intro hcon _; exact absurd hcon.symm h)]
      rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL executed same_spec confirmed True for all 7 attacks and the positive control (swebench_unified.markers.same_spec, lean backend). Verifications run concurrently in two background batches of 4 (≤4 at a time) via scripts/lean_verify.sh <file>.

POSITIVE CONTROL (pos_control.lean = official Solution.lean): `bash scripts/lean_verify.sh pos_control.lean` -> exit 0 (only cosmetic unnecessarySeqFocus linter warnings). Appended `#print axioms correct_factorAndDimensionOfSum` (pos_axcheck.lean) -> exit 0, axioms = [propext, Classical.choice, Quot.sound] — CLEAN, no sorryAx.

ATTACKS (all edit ONLY the impl region; original gold proof body retained; all exit 1 = genuine proof error, NOT sorry(3)/timeout(124)):
- atk_1 (prepatch bug: branch on dim.name ≠ a.2.name instead of deps): exit 1, `rewrite failed`. This reproduces Solution_prepatch.lean's fixed behavior -> prepatch_reproduced=true.
- atk_2 (no compatibility check; always sums, always some): exit 1, rewrite failed.
- atk_3 (never accumulates addend factors; returns head factor): exit 1.
- atk_4 (inverted condition: returns none when dims MATCH): exit 1.
- atk_5 (control-flow-effect: carries LAST addend dim instead of head dim): exit 1.
- atk_6 (boundary/off-by-one: iterates addends.tail, drops first addend's check+factor): exit 1.
- atk_7 (partial-domain/ungrounded-echo: checks only head vs first addend, sums rest unchecked): exit 1.

STEP 2 (materialize+resolve): VACUOUS by construction — zero wrong impls closed with clean axioms, so there is no closing-clean-axiom impl whose faithful patch could fail to resolve. Nothing to run through run_resolve. Reported as executed evidence, not speculation: the 7 verify runs are the falsification attempts and none produced a closing proof.

REFINEMENT.MD AUDIT (§4 correspondence): 6 legs, all tagged R (steps 1-5) or I (step 6); axioms region byte-empty; NO A-consumed / A-reference / kind-3 legs. The single changed op (addend compatibility) is modeled DEEPLY as Dim.deps equality, NOT axiomatized — SPEC_GUIDE §3 compliant. The deep-model correspondence Dim.deps-equality ↔ equivalent_dims (= dict equality of get_dimensional_dependencies, dimensions.py:428) holds against the real base_commit callee (confirmed via mapping.md + verdict.md Role-3 worktree check: equivalent_dims(velocity, acceleration*time)=True same deps {L:1,T:-1}; equivalent_dims(velocity, time)=False). R/I legs additionally covered mechanically by G-CONF (conformance_check.py present). Recursive sub-calls _collect_factor_and_dimension are unchanged behavior taken as inputs (head/addends) — legitimate R, no flag dependence.

CONCLUSION: verify⇒correct holds. The spec admits no verifying wrong impl; no A-leg or ungrounded oracle to exploit. SOUND (≥5 distinct attacks — 7 — run; none breaks it).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found. Solution.lean compiles clean (exit 0, no sorry); #print axioms = [propext, Classical.choice, Quot.sound], no sorryAx. same_spec(Solution, Solution_prepatch)=True with Lean backend (axioms/pure/pre/post regions byte-identical). patch.diff faithfully reproduces the real post-patch edit (dim != addend_dim -> not equivalent_dims(dim, addend_dim)), confirmed against unitsystem.py:175-184. Model boundary is faithful: real equivalent_dims(d1,d2) == (get_dimensional_dependencies(d1)==get_dimensional_dependencies(d2)); the model's Dim.deps equality reproduces this exactly. Crucially verified the canonicalization invariant the model depends on: get_dimensional_dependencies already returns zero-free dicts (tested length*time/time, velocity*time/length, length/length -> all zero-free), so the model's sorted/zero-free assoc-list equality genuinely equals dict equality with no divergence from dropped zero exponents. Compat test compares each addend to the head dim (never reassigned) matching the real loop; error-on-any-mismatch (model none via allDimsMatch) is observationally identical to real raise-on-first-mismatch since the outcome is the same 'no result' in both; factor sum head+Sum(addends) == real left fold on Rat (commutative/associative), confirmed 100k random cases. conformance_check.py passes (120009 cases, 0 disagreements) and independently the real sympy equivalent_dims accepts velocity / length*time^-1 / acceleration*time as equal (the discriminating category). No input exhibits spec-vs-repo disagreement; spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean docstring + pure/post-condition regions) formalizes only the CORRECT behavior at an appropriate abstraction level: two dimensions are the same physical dimension iff their canonical base-dimension power maps (deps) coincide, even when their surface identities (name) differ. This is exactly the notion of 'equivalent dimensions' already made explicit in the PUBLIC problem_statement, whose reproducer literally exhibits Dimension(velocity) vs Dimension(acceleration*time) — differently-written but physically equivalent dimensions — and the erroneous ValueError. A solver reading the public statement already knows the fix must accept dimensions equal by base-dimension content regardless of surface form; the spec view adds no gold-specific detail beyond that. No gold-patch tokens leak into the spec view: 'equivalent_dims', 'get_dimensional_dependencies', 'get_dimension_system', '_collect_factor_and_dimension' appear only in auditor-facing mapping.md/refinement.md, NOT in the spec-view region. The buggy discriminator (compare on surface name) is confined to impl/Solution_prepatch.lean and is not exposed in the spec view. The name-vs-deps distinction the spec draws is precisely the 'differently-written but equivalent' distinction the problem_statement's reproducer already demonstrates. Modeling the correct behavior is inherent to any spec and does not by itself constitute leakage; here it stays at the abstraction the public statement provides. LEAKAGE screen is lexical over the spec view — no gold-edit specifics quoted.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
