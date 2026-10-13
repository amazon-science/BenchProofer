# P2 adversarial audit — sympy__sympy-13877

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `Solution.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found — no wrong impl admits a closing clean-axiom proof. The spec problem_spec_firstNonzero is total and FUNCTIONAL (for each col exactly one accepted result: pos = first mathematically-nonzero index with all earlier entries math-zero, val forced by col[pos]?; else none), so any impl that deviates violates the spec on a concrete input and correct_firstNonzero is genuinely unprovable. This is machine-confirmed for all 7 attacks by separate refutation files (each PROVES ¬∀col, problem_spec col (impl col), verifying exit 0): ref2_atk_1..7 + ref_atk_4.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,7 +96,7 @@
   let mut i := 0
   for x in col do
     if isMathZero x = false then
-      return some (i, x)
+      return some (i + 1, x)
     i := i + 1
   return none
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
     (col : List PExpr) : Option (Nat × PExpr) := Id.run do
   let mut i := 0
   for x in col do
-    if isMathZero x = false then
+    if isMathZero x = true then
       return some (i, x)
     i := i + 1
   return none
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
     (col : List PExpr) : Option (Nat × PExpr) := Id.run do
   let mut i := 0
   for x in col do
-    if isMathZero x = false then
+    if x ≠ PExpr.const 0 then
       return some (i, x)
     i := i + 1
   return none
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,13 +92,7 @@
 
 -- impl-start
 def implementation_firstNonzero
-    (col : List PExpr) : Option (Nat × PExpr) := Id.run do
-  let mut i := 0
-  for x in col do
-    if isMathZero x = false then
-      return some (i, x)
-    i := i + 1
-  return none
+    (col : List PExpr) : Option (Nat × PExpr) := none
 -- impl-end
 
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,13 +92,10 @@
 
 -- impl-start
 def implementation_firstNonzero
-    (col : List PExpr) : Option (Nat × PExpr) := Id.run do
-  let mut i := 0
-  for x in col do
-    if isMathZero x = false then
-      return some (i, x)
-    i := i + 1
-  return none
+    (col : List PExpr) : Option (Nat × PExpr) :=
+  match col with
+  | [] => none
+  | x :: _ => some (0, x)
 -- impl-end
 
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
     (col : List PExpr) : Option (Nat × PExpr) := Id.run do
   let mut i := 0
   for x in col do
-    if isMathZero x = false then
+    if i ≥ 1 && isMathZero x = false then
       return some (i, x)
     i := i + 1
   return none
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,11 +94,12 @@
 def implementation_firstNonzero
     (col : List PExpr) : Option (Nat × PExpr) := Id.run do
   let mut i := 0
+  let mut res : Option (Nat × PExpr) := none
   for x in col do
     if isMathZero x = false then
-      return some (i, x)
+      res := some (i, x)
     i := i + 1
-  return none
+  return res
 -- impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `Solution.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting a pivot from a column of symbolic expressions.

During fraction-free Gaussian elimination one repeatedly takes the first column
of a (sub)matrix and chooses a *pivot*: the first entry of that column that is
not zero. The subtlety is that the entries are symbolic expressions, and an
expression can be written in a structurally non-trivial form yet still be
mathematically equal to zero (for example a difference of two products that
cancels completely). A pivot must be a *genuinely* nonzero entry; choosing an
entry that is mathematically zero corrupts the elimination.

We model a column entry as an integer-coefficient polynomial expression in a
single indeterminate. "Mathematically zero" means the expression evaluates to
the zero polynomial (every coefficient is `0`).

The desired behavior, stated as an input→output relation:

* if the column contains some mathematically-nonzero entry, the result is the
  position and value of the *first* such entry (and every earlier entry is
  mathematically zero);
* if every entry is mathematically zero, the result is nothing.

The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The zero test that decides
-- whether an entry may serve as a pivot is spelled out concretely below
-- (`eval` / `isMathZero`, an A-reference): an expression is mathematically zero
-- exactly when it evaluates to the zero polynomial. There is nothing to
-- axiomatize — the modeled behavior is validated directly against the real
-- routine by the differential conformance check.
-- axioms-end

-- pure-start
/-- A symbolic expression: an integer-coefficient polynomial in one
indeterminate, built from integer constants, the indeterminate, addition,
multiplication and negation. This is the carrier for a single column entry. -/
inductive PExpr where
  | const : Int → PExpr
  | sym   : PExpr
  | add   : PExpr → PExpr → PExpr
  | mul   : PExpr → PExpr → PExpr
  | neg   : PExpr → PExpr
deriving Repr, DecidableEq

/-- Add two coefficient lists (little-endian, index `i` = coefficient of `xⁱ`). -/
def addC : List Int → List Int → List Int
  | [], ys => ys
  | xs, [] => xs
  | x :: xs, y :: ys => (x + y) :: addC xs ys

/-- Multiply two coefficient lists (polynomial convolution). -/
def mulC : List Int → List Int → List Int
  | [], _ => []
  | x :: xs, ys => addC (ys.map (· * x)) (0 :: mulC xs ys)

/-- Evaluate an expression to its little-endian list of integer coefficients. -/
def eval : PExpr → List Int
  | .const c => [c]
  | .sym      => [0, 1]
  | .add a b  => addC (eval a) (eval b)
  | .mul a b  => mulC (eval a) (eval b)
  | .neg a    => (eval a).map (fun c => -c)

/-- An expression is *mathematically zero* when it evaluates to the zero
polynomial — every coefficient is `0`. -/
def isMathZero (e : PExpr) : Bool := (eval e).all (· == 0)
-- pure-end

-- post-conditions-start
/-- The pivot-selection contract on a column `col`:

* `some (pos, val)`: `pos` is a valid index, `val` is exactly the entry there,
  that entry is mathematically nonzero, and every strictly-earlier entry is
  mathematically zero (so `pos` is the *first* genuinely nonzero position);
* `none`: every entry of the column is mathematically zero. -/
def problem_spec_firstNonzero
    (col : List PExpr) (result : Option (Nat × PExpr)) : Prop :=
  match result with
  | some (pos, val) =>
      pos < col.length ∧
      col[pos]? = some val ∧
      isMathZero val = false ∧
      (∀ k e, k < pos → col[k]? = some e → isMathZero e = true)
  | none =>
      ∀ e ∈ col, isMathZero e = true
-- post-conditions-end

-- impl-start
def implementation_firstNonzero
    (col : List PExpr) : Option (Nat × PExpr) := Id.run do
  let mut i := 0
  for x in col do
    if isMathZero x = false then
      return some (i, x)
    i := i + 1
  return none
-- impl-end


-- proof-start
/-- Pure recursive de-monadified form of the scanning loop: returns the first
index/value pair whose entry is mathematically nonzero, carrying the current
global index as the second argument. -/
def go : List PExpr → Nat → Option (Nat × PExpr)
  | [], _ => none
  | x :: xs, i => if isMathZero x = false then some (i, x) else go xs (i + 1)

theorem go_spec_general :
    ∀ (col : List PExpr) (i : Nat),
      (match go col i with
        | some (pos, val) =>
            i ≤ pos ∧ pos - i < col.length ∧ col[pos - i]? = some val ∧
              isMathZero val = false ∧
              (∀ k e, k < pos - i → col[k]? = some e → isMathZero e = true)
        | none => ∀ e ∈ col, isMathZero e = true) := by
  intro col
  induction col with
  | nil => intro i; simp [go]
  | cons x xs ih =>
    intro i
    simp only [go]
    split_ifs with hx
    · -- isMathZero x = false, result = some (i, x)
      refine ⟨le_refl i, ?_, ?_, hx, ?_⟩
      · simp
      · simp
      · intro k e hk _; simp only [Nat.sub_self] at hk; omega
    · -- isMathZero x = true, result = go xs (i+1)
      have hx' : isMathZero x = true := by
        simp only [Bool.not_eq_false] at hx; exact hx
      have this' := ih (i + 1)
      cases hgo : go xs (i + 1) with
      | none =>
        rw [hgo] at this'
        intro e he
        rcases List.mem_cons.mp he with rfl | he'
        · exact hx'
        · exact this' e he'
      | some pv =>
        obtain ⟨pos, val⟩ := pv
        rw [hgo] at this'
        obtain ⟨h1, h2, h3, h4, h5⟩ := this'
        refine ⟨by omega, ?_, ?_, h4, ?_⟩
        · simp only [List.length_cons]; omega
        · have hpi : pos - i = (pos - (i + 1)) + 1 := by omega
          rw [hpi, List.getElem?_cons_succ]; exact h3
        · intro k e hk he
          cases k with
          | zero =>
            simp only [List.getElem?_cons_zero, Option.some.injEq] at he
            subst he; exact hx'
          | succ k' =>
            rw [List.getElem?_cons_succ] at he
            have hk' : k' < pos - (i + 1) := by omega
            exact h5 k' e hk' he

theorem loop_eq_go :
    ∀ (col : List PExpr),
      implementation_firstNonzero col = go col 0 := by
  intro col
  simp only [implementation_firstNonzero, Id.run]
  generalize (0 : Nat) = i
  induction col generalizing i with
  | nil => rfl
  | cons x xs ih =>
      simp only [List.forIn_cons, go]
      by_cases hx : isMathZero x = false
      · simp only [hx, if_true]
        rfl
      · simp only [hx]
        exact ih (i + 1)

theorem go_spec_zero :
    ∀ (col : List PExpr), problem_spec_firstNonzero col (go col 0) := by
  intro col
  have h := go_spec_general col 0
  simp only [Nat.sub_zero] at h
  unfold problem_spec_firstNonzero
  cases hg : go col 0 with
  | none => rw [hg] at h; exact h
  | some p =>
      obtain ⟨pos, val⟩ := p
      rw [hg] at h
      exact ⟨h.2.1, h.2.2.1, h.2.2.2.1, h.2.2.2.2⟩

theorem correct_firstNonzero :
    ∀ (col : List PExpr),
      problem_spec_firstNonzero col (implementation_firstNonzero col) := by
  intro col
  rw [loop_eq_go col]
  exact go_spec_zero col

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL SUMMARY (all runs from project root with; verifier: `bash scripts/lean_verify.sh <f>`).

SAME_SPEC: all 7 attacks byte-identical spec view (axioms/pure/pre/post unchanged; only impl region edited). Confirmed True via markers.same_spec for atk_1..7.

POSITIVE CONTROL: gold Solution.lean verifies EXIT=0; `#print axioms correct_firstNonzero` => [propext, Classical.choice, Quot.sound] — clean, no sorryAx.

7 DISTINCT WRONG IMPLS (each same_spec=True, gold proof carried verbatim as a genuine closing attempt, ALL fail to close EXIT=1 with genuine rfl/type-mismatch errors against the mutated impl):
- atk_1 off-by-one position (returns some(i+1,x)). #eval on [sym] => some(1,sym); violates pos<length.
- atk_2 inverted/ungrounded oracle (picks first isMathZero=true). #eval [const 0] => some(0,const 0); violates isMathZero val=false.
- atk_3 prepatch literal-zero truthiness bug (x ≠ const 0). #eval [a-a] => some(0,a-a); a-a is math-zero => violates isMathZero val=false. THE REAL PRE-PATCH BUG, reproduced.
- atk_4 partial-domain degenerate (always none). Refuted on [sym]: none-branch requires isMathZero sym=true (false).
- atk_5 ungrounded echo (unconditional some(0,head)). #eval [const 0] => some(0,const 0); violates isMathZero val=false.
- atk_6 control-flow-effect (skips index 0, scans from i>=1). #eval [sym] => none; violates none-branch (sym not math-zero).
- atk_7 boundary (returns LAST nonzero via mutable accumulator). #eval [sym, const 2] => some(1,const 2); violates 'all earlier math-zero' (col[0]=sym nonzero).

GOLD-PROOF-CLOSE RESULTS (attacks carrying gold proof): atk_1..7 all EXIT=1 (genuine unification failures, not sorry/timeout).

MACHINE-CHECKED REFUTATIONS (definitive: prove no correct proof exists): ref_atk_4.lean EXIT=0; ref2_atk_1/2/3/5/6/7.lean EXIT=0 — each proves ¬(∀col, problem_spec_firstNonzero col (implementation_firstNonzero col)) by instantiating at the witness column and reducing the violated conjunct. Since correct's statement is refutable, it is unprovable by Lean soundness.

RESOLVE RUNS: NONE required — protocol step 2 (materialize+resolve every wrong impl whose proof closes with clean axioms) is VACUOUS because ZERO wrong impls close. patches={} accordingly.

REFINEMENT.MD A-LEG AUDIT: No axiom declared or consumed (axioms-start block axiomatizes nothing; G-AX = skip stub). Every leg is R (col↦List PExpr, none↦no-pivot), I (top-to-bottom scan, same order), or A-reference. The sole A-reference — modeling _is_zero_after_expand_mul / expand_mul(x)==0 deeply as eval/isMathZero — is FAITHFUL: for integer-coefficient univariate polynomials (exactly the issue's entries i + a*j), expand_mul(x)==0 ⟺ all coefficients vanish, which isMathZero decides; this lives in the byte-identical pure region and is G-CONF-validated against the real _find_reasonable_pivot(col, iszerofunc=_is_zero_after_expand_mul). No kind-3 (unjustified) leg. Model↔patch correspondence holds: post-patch impl (isMathZero x = false) vs pre-patch (x ≠ const 0) is the exact discriminating clause of the gold hunk. The randtest.py tolerance hunk is correctly scoped OUT (not F2P-exercised).

VERDICT: SOUND. >=5 distinct attacks (7 built) all fail to verify, each machine-refuted as genuinely non-conforming; positive control verifies with clean axioms; A-legs faithful. verify ⇒ correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `Solution.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found — no wrong impl admits a closing clean-axiom proof. The spec problem_spec_firstNonzero is total and FUNCTIONAL (for each col exactly one accepted result: pos = first mathematically-nonzero index with all earlier entries math-zero, val forced by col[pos]?; else none), so any impl that deviates violates the spec on a concrete input and correct_firstNonzero is genuinely unprovable. This is machine-confirmed for all 7 attacks by separate refutation files (each PROVES ¬∀col, problem_spec col (impl col), verifying exit 0): ref2_atk_1..7 + ref_atk_4.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `Solution.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting a pivot from a column of symbolic expressions.

During fraction-free Gaussian elimination one repeatedly takes the first column
of a (sub)matrix and chooses a *pivot*: the first entry of that column that is
not zero. The subtlety is that the entries are symbolic expressions, and an
expression can be written in a structurally non-trivial form yet still be
mathematically equal to zero (for example a difference of two products that
cancels completely). A pivot must be a *genuinely* nonzero entry; choosing an
entry that is mathematically zero corrupts the elimination.

We model a column entry as an integer-coefficient polynomial expression in a
single indeterminate. "Mathematically zero" means the expression evaluates to
the zero polynomial (every coefficient is `0`).

The desired behavior, stated as an input→output relation:

* if the column contains some mathematically-nonzero entry, the result is the
  position and value of the *first* such entry (and every earlier entry is
  mathematically zero);
* if every entry is mathematically zero, the result is nothing.

The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The zero test that decides
-- whether an entry may serve as a pivot is spelled out concretely below
-- (`eval` / `isMathZero`, an A-reference): an expression is mathematically zero
-- exactly when it evaluates to the zero polynomial. There is nothing to
-- axiomatize — the modeled behavior is validated directly against the real
-- routine by the differential conformance check.
-- axioms-end

-- pure-start
/-- A symbolic expression: an integer-coefficient polynomial in one
indeterminate, built from integer constants, the indeterminate, addition,
multiplication and negation. This is the carrier for a single column entry. -/
inductive PExpr where
  | const : Int → PExpr
  | sym   : PExpr
  | add   : PExpr → PExpr → PExpr
  | mul   : PExpr → PExpr → PExpr
  | neg   : PExpr → PExpr
deriving Repr, DecidableEq

/-- Add two coefficient lists (little-endian, index `i` = coefficient of `xⁱ`). -/
def addC : List Int → List Int → List Int
  | [], ys => ys
  | xs, [] => xs
  | x :: xs, y :: ys => (x + y) :: addC xs ys

/-- Multiply two coefficient lists (polynomial convolution). -/
def mulC : List Int → List Int → List Int
  | [], _ => []
  | x :: xs, ys => addC (ys.map (· * x)) (0 :: mulC xs ys)

/-- Evaluate an expression to its little-endian list of integer coefficients. -/
def eval : PExpr → List Int
  | .const c => [c]
  | .sym      => [0, 1]
  | .add a b  => addC (eval a) (eval b)
  | .mul a b  => mulC (eval a) (eval b)
  | .neg a    => (eval a).map (fun c => -c)

/-- An expression is *mathematically zero* when it evaluates to the zero
polynomial — every coefficient is `0`. -/
def isMathZero (e : PExpr) : Bool := (eval e).all (· == 0)
-- pure-end

-- post-conditions-start
/-- The pivot-selection contract on a column `col`:

* `some (pos, val)`: `pos` is a valid index, `val` is exactly the entry there,
  that entry is mathematically nonzero, and every strictly-earlier entry is
  mathematically zero (so `pos` is the *first* genuinely nonzero position);
* `none`: every entry of the column is mathematically zero. -/
def problem_spec_firstNonzero
    (col : List PExpr) (result : Option (Nat × PExpr)) : Prop :=
  match result with
  | some (pos, val) =>
      pos < col.length ∧
      col[pos]? = some val ∧
      isMathZero val = false ∧
      (∀ k e, k < pos → col[k]? = some e → isMathZero e = true)
  | none =>
      ∀ e ∈ col, isMathZero e = true
-- post-conditions-end

-- impl-start
def implementation_firstNonzero
    (col : List PExpr) : Option (Nat × PExpr) := Id.run do
  let mut i := 0
  for x in col do
    if isMathZero x = false then
      return some (i, x)
    i := i + 1
  return none
-- impl-end


-- proof-start
/-- Pure recursive de-monadified form of the scanning loop: returns the first
index/value pair whose entry is mathematically nonzero, carrying the current
global index as the second argument. -/
def go : List PExpr → Nat → Option (Nat × PExpr)
  | [], _ => none
  | x :: xs, i => if isMathZero x = false then some (i, x) else go xs (i + 1)

theorem go_spec_general :
    ∀ (col : List PExpr) (i : Nat),
      (match go col i with
        | some (pos, val) =>
            i ≤ pos ∧ pos - i < col.length ∧ col[pos - i]? = some val ∧
              isMathZero val = false ∧
              (∀ k e, k < pos - i → col[k]? = some e → isMathZero e = true)
        | none => ∀ e ∈ col, isMathZero e = true) := by
  intro col
  induction col with
  | nil => intro i; simp [go]
  | cons x xs ih =>
    intro i
    simp only [go]
    split_ifs with hx
    · -- isMathZero x = false, result = some (i, x)
      refine ⟨le_refl i, ?_, ?_, hx, ?_⟩
      · simp
      · simp
      · intro k e hk _; simp only [Nat.sub_self] at hk; omega
    · -- isMathZero x = true, result = go xs (i+1)
      have hx' : isMathZero x = true := by
        simp only [Bool.not_eq_false] at hx; exact hx
      have this' := ih (i + 1)
      cases hgo : go xs (i + 1) with
      | none =>
        rw [hgo] at this'
        intro e he
        rcases List.mem_cons.mp he with rfl | he'
        · exact hx'
        · exact this' e he'
      | some pv =>
        obtain ⟨pos, val⟩ := pv
        rw [hgo] at this'
        obtain ⟨h1, h2, h3, h4, h5⟩ := this'
        refine ⟨by omega, ?_, ?_, h4, ?_⟩
        · simp only [List.length_cons]; omega
        · have hpi : pos - i = (pos - (i + 1)) + 1 := by omega
          rw [hpi, List.getElem?_cons_succ]; exact h3
        · intro k e hk he
          cases k with
          | zero =>
            simp only [List.getElem?_cons_zero, Option.some.injEq] at he
            subst he; exact hx'
          | succ k' =>
            rw [List.getElem?_cons_succ] at he
            have hk' : k' < pos - (i + 1) := by omega
            exact h5 k' e hk' he

theorem loop_eq_go :
    ∀ (col : List PExpr),
      implementation_firstNonzero col = go col 0 := by
  intro col
  simp only [implementation_firstNonzero, Id.run]
  generalize (0 : Nat) = i
  induction col generalizing i with
  | nil => rfl
  | cons x xs ih =>
      simp only [List.forIn_cons, go]
      by_cases hx : isMathZero x = false
      · simp only [hx, if_true]
        rfl
      · simp only [hx]
        exact ih (i + 1)

theorem go_spec_zero :
    ∀ (col : List PExpr), problem_spec_firstNonzero col (go col 0) := by
  intro col
  have h := go_spec_general col 0
  simp only [Nat.sub_zero] at h
  unfold problem_spec_firstNonzero
  cases hg : go col 0 with
  | none => rw [hg] at h; exact h
  | some p =>
      obtain ⟨pos, val⟩ := p
      rw [hg] at h
      exact ⟨h.2.1, h.2.2.1, h.2.2.2.1, h.2.2.2.2⟩

theorem correct_firstNonzero :
    ∀ (col : List PExpr),
      problem_spec_firstNonzero col (implementation_firstNonzero col) := by
  intro col
  rw [loop_eq_go col]
  exact go_spec_zero col

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL SUMMARY (all runs from project root with; verifier: `bash scripts/lean_verify.sh <f>`).

SAME_SPEC: all 7 attacks byte-identical spec view (axioms/pure/pre/post unchanged; only impl region edited). Confirmed True via markers.same_spec for atk_1..7.

POSITIVE CONTROL: gold Solution.lean verifies EXIT=0; `#print axioms correct_firstNonzero` => [propext, Classical.choice, Quot.sound] — clean, no sorryAx.

7 DISTINCT WRONG IMPLS (each same_spec=True, gold proof carried verbatim as a genuine closing attempt, ALL fail to close EXIT=1 with genuine rfl/type-mismatch errors against the mutated impl):
- atk_1 off-by-one position (returns some(i+1,x)). #eval on [sym] => some(1,sym); violates pos<length.
- atk_2 inverted/ungrounded oracle (picks first isMathZero=true). #eval [const 0] => some(0,const 0); violates isMathZero val=false.
- atk_3 prepatch literal-zero truthiness bug (x ≠ const 0). #eval [a-a] => some(0,a-a); a-a is math-zero => violates isMathZero val=false. THE REAL PRE-PATCH BUG, reproduced.
- atk_4 partial-domain degenerate (always none). Refuted on [sym]: none-branch requires isMathZero sym=true (false).
- atk_5 ungrounded echo (unconditional some(0,head)). #eval [const 0] => some(0,const 0); violates isMathZero val=false.
- atk_6 control-flow-effect (skips index 0, scans from i>=1). #eval [sym] => none; violates none-branch (sym not math-zero).
- atk_7 boundary (returns LAST nonzero via mutable accumulator). #eval [sym, const 2] => some(1,const 2); violates 'all earlier math-zero' (col[0]=sym nonzero).

GOLD-PROOF-CLOSE RESULTS (attacks carrying gold proof): atk_1..7 all EXIT=1 (genuine unification failures, not sorry/timeout).

MACHINE-CHECKED REFUTATIONS (definitive: prove no correct proof exists): ref_atk_4.lean EXIT=0; ref2_atk_1/2/3/5/6/7.lean EXIT=0 — each proves ¬(∀col, problem_spec_firstNonzero col (implementation_firstNonzero col)) by instantiating at the witness column and reducing the violated conjunct. Since correct's statement is refutable, it is unprovable by Lean soundness.

RESOLVE RUNS: NONE required — protocol step 2 (materialize+resolve every wrong impl whose proof closes with clean axioms) is VACUOUS because ZERO wrong impls close. patches={} accordingly.

REFINEMENT.MD A-LEG AUDIT: No axiom declared or consumed (axioms-start block axiomatizes nothing; G-AX = skip stub). Every leg is R (col↦List PExpr, none↦no-pivot), I (top-to-bottom scan, same order), or A-reference. The sole A-reference — modeling _is_zero_after_expand_mul / expand_mul(x)==0 deeply as eval/isMathZero — is FAITHFUL: for integer-coefficient univariate polynomials (exactly the issue's entries i + a*j), expand_mul(x)==0 ⟺ all coefficients vanish, which isMathZero decides; this lives in the byte-identical pure region and is G-CONF-validated against the real _find_reasonable_pivot(col, iszerofunc=_is_zero_after_expand_mul). No kind-3 (unjustified) leg. Model↔patch correspondence holds: post-patch impl (isMathZero x = false) vs pre-patch (x ≠ const 0) is the exact discriminating clause of the gold hunk. The randtest.py tolerance hunk is correctly scoped OUT (not F2P-exercised).

VERDICT: SOUND. >=5 distinct attacks (7 built) all fail to verify, each machine-refuted as genuinely non-conforming; positive control verifies with clean axioms; A-legs faithful. verify ⇒ correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack found NO divergence between the modeled `implementation_firstNonzero` / `problem_spec_firstNonzero` and the real patched callee `_find_reasonable_pivot(mat[:,0], iszerofunc=_is_zero_after_expand_mul)`.

### MECHANICAL CHECKS (all pass):
- scripts/lean_verify.sh Solution.lean -> exit 0.
- `#print axioms correct_firstNonzero` = [propext, Classical.choice, Quot.sound]; no sorryAx -> proof is genuine.
- swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean backend) = True; spec_view sha256 = 308d05b9755c4d1b473532cd981df7a7e45270d490bf185007688cc91a8a0413 (matches meta G-HYGIENE region_hashes.spec_view).

EMPIRICAL FAITHFULNESS (gold-patched sympy 1.4; _is_zero_after_expand_mul present = expand_mul(x)==0):
- Bundled conformance_check.py: status=pass checked=120011 (seed 20240630).
- Independent adversarial fuzz (not the bundled generator): 8 seeds x 40k = 320k columns, tree depth 5, coeffs +/-9, columns up to length 7, 25% forced a+(-a) cancellations plus 10% scaled k*e+(-k*e) math-zeros. Compared disposition (some/none), position, AND value (via expand_mul(model_val - real_val)==0). ZERO mismatches.
- Targeted probes: col=[a+(-a), a] -> real=(1,a); all-math-zero col -> (None,None); iszerofunc returns definitive True/False (never None) on this domain.

DOMAIN-REDUCTION ARGUMENT (why the real routine collapses to the model): for the PExpr->sympy bridge (Integer constants + one symbol, +/*/neg), (1) the Float/Integer partial-pivoting branch at matrices.py:4092 is unreachable because PExpr never emits a Float; (2) _is_zero_after_expand_mul returns a definitive Python bool for every entry, so PASS 1 (matrices.py:4106-4122) always resolves it -- return first entry with iszerofunc==False, else None if all zero. PASS 2 (simplify), PASS 3 (.equals), and the assumed-nonzero fallback (4124-4170) are all dead on this class. PASS 1 returns the ORIGINAL unsimplified entry, matching the model's value exactly. isMathZero (all little-endian coefficients zero) coincides with expand_mul(x)==0 for univariate integer polynomials, including the bug trigger a+(-a).

The spec is not too strong and does not drift: it agrees with the real callee on every tested input, and the only branches where it could disagree are provably outside the modeled PExpr domain. The pre-patch leg (x != const 0) correctly diverges on math-zero-but-non-literal entries, giving G-DIFF a real discriminator, confirming the spec is also not vacuously weak.

(Scope note acknowledged: the randtest.py `tolerance` hunk is auxiliary test-support, not F2P-exercised, legitimately out of modeled scope.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK passes (strict, meta status=pass, no RELAXED flag). Independent semantic review confirms NO-LEAKAGE. (1) same_spec(Solution.lean, Solution_prepatch.lean)=True: the spec view is byte-identical for the buggy vs fixed impl, so the discriminating clause (post-patch `isMathZero x = false` vs pre-patch `x ≠ PExpr.const 0`) lives entirely in the ELIDED impl region and cannot be present in the spec view by construction. (2) Spec view names none of the patched repo symbols (_find_pivot, _is_zero_after_expand_mul, _find_reasonable_pivot, _eval_det_bareiss, random_complex_number), no patched file path (sympy/matrices/matrices.py, sympy/utilities/randtest.py), no diff markers, no gold-patch lines, no bug/fix narration words. (3) The docstring describes an abstracted, self-contained problem — 'find the first mathematically-nonzero entry of a column of univariate integer-polynomial expressions', with mathematical-zero = evaluates to the zero polynomial. This is the necessary abstract content of a faithful pivot-selection spec, not a repo-edit disclosure; it does not localize the fix to any sympy symbol/file nor reveal the expand_mul zero-test mechanism. (4) The literal-vs-mathematical-zero fix concept and the `val.expand()` hint appear only in hints_text, which is correctly not counted for leakage; the public problem_statement shows only the NaN-comparison crash and does not mention pivot selection or zero detection — but the spec view does not reproduce the gold edit even relative to that. Verdict: spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
