# P2 adversarial audit — astropy__astropy-12907

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
None found. The spec problem_spec_direct_sum pins result.length AND result.getD i [] at every in-range index (conjunct 1 covers 0..left.length-1, conjunct 3 covers left.length..total-1), uniquely determining the output for all preconditioned inputs. No same-spec wrong impl could be made to verify with clean axioms, so there is no verifying-but-wrong impl to falsify the spec with. The prepatch bug (right-block padded with ones instead of copying `right`) is positively refuted by disproof_atk1.lean: `¬ problem_spec_direct_sum 1 1 [[0]] [] (impl_bad ...)` closes (exit 0), witnessing spec violation at a precondition-valid input.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
   let mut result : List (List Nat) := []
   for i in [0:noutp] do
     let cleftRow := if i < lout then left.getD i [] else zeroRow lin
-    let crightRow := if lout ≤ i then right.getD (i - lout) [] else zeroRow rin
+    let crightRow := if lout ≤ i then right.getD (i - lout) [] else List.replicate rin 1
     result := result ++ [cleftRow ++ crightRow]
   return result
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
   let mut result : List (List Nat) := []
   for i in [0:noutp] do
     let cleftRow := if i < lout then left.getD i [] else zeroRow lin
-    let crightRow := if lout ≤ i then right.getD (i - lout) [] else zeroRow rin
+    let crightRow := zeroRow rin
     result := result ++ [cleftRow ++ crightRow]
   return result
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
   let mut result : List (List Nat) := []
   for i in [0:noutp] do
     let cleftRow := if i < lout then left.getD i [] else zeroRow lin
-    let crightRow := if lout ≤ i then right.getD (i - lout) [] else zeroRow rin
+    let crightRow := if lout ≤ i then right.getD (i - lout + 1) [] else zeroRow rin
     result := result ++ [cleftRow ++ crightRow]
   return result
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,7 +49,7 @@
     let cleftRow := if i < lout then left.getD i [] else zeroRow lin
     let crightRow := if lout ≤ i then right.getD (i - lout) [] else zeroRow rin
     result := result ++ [cleftRow ++ crightRow]
-  return result
+  return result.reverse
 -- impl-end
 
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
   let mut result : List (List Nat) := []
   for i in [0:noutp] do
     let cleftRow := if i < lout then left.getD i [] else zeroRow lin
-    let crightRow := if lout ≤ i then right.getD (i - lout) [] else zeroRow rin
+    let crightRow := if lout ≤ i then right.getD (i - lout) [] else zeroRow lin
     result := result ++ [cleftRow ++ crightRow]
   return result
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,7 @@
   let rout := right.length
   let noutp := lout + rout
   let mut result : List (List Nat) := []
-  for i in [0:noutp] do
+  for i in [0:noutp-1] do
     let cleftRow := if i < lout then left.getD i [] else zeroRow lin
     let crightRow := if lout ≤ i then right.getD (i - lout) [] else zeroRow rin
     result := result ++ [cleftRow ++ crightRow]
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,8 +46,8 @@
   let noutp := lout + rout
   let mut result : List (List Nat) := []
   for i in [0:noutp] do
-    let cleftRow := if i < lout then left.getD i [] else zeroRow lin
-    let crightRow := if lout ≤ i then right.getD (i - lout) [] else zeroRow rin
+    let cleftRow := if i < lout then zeroRow lin else left.getD (i) []
+    let crightRow := if lout ≤ i then zeroRow rin else right.getD (i) []
     result := result ++ [cleftRow ++ crightRow]
   return result
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Combining the correlation matrices of two independent sub-transforms that are
placed side by side (each acting on its own block of inputs to produce its own
block of outputs). The combined matrix relates the concatenated outputs to the
concatenated inputs: a top-left block carrying the first sub-transform's own
correlations, a bottom-right block carrying the second's, and zeros elsewhere
(the two sub-transforms share neither inputs nor outputs).

A correlation matrix is modeled as `List (List Nat)`: one inner list per output
row, all rows sharing one width (the input count); an entry is `0` (independent)
or nonzero (dependent). `lin`/`rin` are the input widths of the two blocks.
-/

-- axioms-start
-- No unchanged callees are consumed: the combinator is modeled deeply.
-- axioms-end

-- pure-start
/-- A row of `n` independent (zero) entries. -/
def zeroRow (n : Nat) : List Nat := List.replicate n 0
-- pure-end

-- post-conditions-start
/-- The combined matrix is the block-diagonal (direct-sum) arrangement of the
two input matrices:
* it has one row per output of the two blocks together;
* the first `left.length` rows reproduce `left`'s own row, then `rin` zeros;
* the remaining rows are `lin` zeros, then `right`'s corresponding row. -/
def problem_spec_direct_sum
    (lin rin : Nat) (left right : List (List Nat)) (result : List (List Nat)) : Prop :=
  result.length = left.length + right.length ∧
  (∀ i, i < left.length →
      result.getD i [] = left.getD i [] ++ zeroRow rin) ∧
  (∀ i, left.length ≤ i → i < left.length + right.length →
      result.getD i [] = zeroRow lin ++ right.getD (i - left.length) [])
-- post-conditions-end

-- impl-start
def implementation_direct_sum
    (lin rin : Nat) (left right : List (List Nat)) : List (List Nat) := Id.run do
  let lout := left.length
  let rout := right.length
  let noutp := lout + rout
  let mut result : List (List Nat) := []
  for i in [0:noutp] do
    let cleftRow := if i < lout then left.getD i [] else zeroRow lin
    let crightRow := if lout ≤ i then right.getD (i - lout) [] else zeroRow rin
    result := result ++ [cleftRow ++ crightRow]
  return result
-- impl-end


-- proof-start
theorem correct_direct_sum :
    ∀ (lin rin : Nat) (left right : List (List Nat)),
      (∀ r ∈ left, r.length = lin) → (∀ r ∈ right, r.length = rin) →
      problem_spec_direct_sum lin rin left right
        (implementation_direct_sum lin rin left right) := by
  intro lin rin left right hleft hright
  have key : ∀ (l : List Nat) (f : Nat → List Nat) (acc : List (List Nat)),
      ((forIn l acc (fun i r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [f i]))))) : Id (List (List Nat)))
        = acc ++ l.map f := by
    intro l f acc
    induction l generalizing acc with
    | nil => simp; rfl
    | cons a t ih =>
        rw [List.forIn_cons]
        show ((forIn t (acc ++ [f a]) (fun i r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [f i]))))) : Id (List (List Nat))) = acc ++ (a::t).map f
        rw [ih]
        simp [List.append_assoc]
  have impl_eq : implementation_direct_sum lin rin left right =
      (List.range (left.length + right.length)).map (fun i =>
        (if i < left.length then left.getD i [] else zeroRow lin) ++
        (if left.length ≤ i then right.getD (i - left.length) [] else zeroRow rin)) := by
    unfold implementation_direct_sum Id.run
    simp only [Std.Range.forIn_eq_forIn_range', Std.Range.size, Nat.div_one]
    rw [key]
    simp only [List.nil_append, List.range_eq_range', Nat.add_sub_cancel]
    rfl
  rw [impl_eq]
  refine ⟨by simp, ?_, ?_⟩
  · intro i hi
    have hlt : i < left.length + right.length := by omega
    rw [List.getD_eq_getElem?_getD, List.getElem?_map, List.getElem?_range hlt]
    simp only [Option.map_some, Option.getD_some]
    rw [if_pos hi, if_neg (by omega)]
  · intro i hle hlt
    rw [List.getD_eq_getElem?_getD, List.getElem?_map, List.getElem?_range hlt]
    simp only [Option.map_some, Option.getD_some]
    rw [if_neg (by omega), if_pos hle]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. All 8 files confirmed same_spec=True vs Solution.lean via swebench_unified.markers.same_spec (lean backend). Note: lean spec_view elides BOTH impl and proof regions, so only axioms/pure/pre/post are byte-compared; all attacks left those regions and the shipped proof byte-identical, editing only the impl-region def body.

COMMAND (each): `bash scripts/lean_verify.sh <file>`.

### Results
- pos_control.lean (verbatim correct impl): exit 0 (VERIFIES). #print axioms correct_direct_sum => [propext, Classical.choice, Quot.sound] (clean, no sorryAx) via pos_axioms.lean exit 0.
- atk_1 PREPATCH BUG (right block of left-rows padded with `List.replicate rin 1` instead of zeros; i.e. cright=1): exit 1 (FAILS). Additionally positively DISPROVED: disproof_atk1.lean proves ¬spec at lin=1,rin=1,left=[[0]],right=[] — exit 0.
- atk_2 partial-domain (crightRow := zeroRow rin always; right block dropped): exit 1 (FAILS).
- atk_3 boundary/off-by-one (right.getD (i-lout+1)): exit 1 (FAILS).
- atk_4 control-flow-effect (return result.reverse; rows permuted): exit 1 (FAILS).
- atk_5 wrong-padding-width (pad left rows with zeroRow lin instead of rin): exit 1 (FAILS).
- atk_6 length off-by-one (loop [0:noutp-1]; drops last row): exit 1 (FAILS).
- atk_7 ungrounded-oracle-echo (blocks swapped: left placed bottom-left, right top): exit 1 (FAILS).

7 DISTINCT wrong impls attacked (partial-domain, boundary, control-flow-effect, wrong-width, length-defect, block-swap echo, plus the prepatch). Verifications run concurrently in two batches of 4 as background Bash jobs. NONE of the wrong impls produced a closing clean-axiom proof, so step-2 (materialize faithful patch + run_resolve) is vacuous — patches={} — there is no verify-but-wrong artifact to run.

REFINEMENT.md AUDIT: 6 legs, all tagged R (1,3,4,5) or I (2,6); axioms region is empty ('No unchanged callees are consumed: the combinator is modeled deeply'), so NO A-legs and NO kind-3 legs. mapping.md confirms deep-model correspondence to _cstack array/array branch (separable.py:219-247): op #5 (cright=right) is exactly the fixed line, op #4 zero-padded left block, op #6 hstack per-row concat. No A-reference callee to validate against a real callee. Correspondence holds.

VERDICT: SOUND — verify⇒correct holds; the tight spec (length + every-row getD pinned) admits no verifying same-spec wrong impl, and the prepatch is positively refuted.

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
None found. The spec problem_spec_direct_sum pins result.length AND result.getD i [] at every in-range index (conjunct 1 covers 0..left.length-1, conjunct 3 covers left.length..total-1), uniquely determining the output for all preconditioned inputs. No same-spec wrong impl could be made to verify with clean axioms, so there is no verifying-but-wrong impl to falsify the spec with. The prepatch bug (right-block padded with ones instead of copying `right`) is positively refuted by disproof_atk1.lean: `¬ problem_spec_direct_sum 1 1 [[0]] [] (impl_bad ...)` closes (exit 0), witnessing spec violation at a precondition-valid input.
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
Combining the correlation matrices of two independent sub-transforms that are
placed side by side (each acting on its own block of inputs to produce its own
block of outputs). The combined matrix relates the concatenated outputs to the
concatenated inputs: a top-left block carrying the first sub-transform's own
correlations, a bottom-right block carrying the second's, and zeros elsewhere
(the two sub-transforms share neither inputs nor outputs).

A correlation matrix is modeled as `List (List Nat)`: one inner list per output
row, all rows sharing one width (the input count); an entry is `0` (independent)
or nonzero (dependent). `lin`/`rin` are the input widths of the two blocks.
-/

-- axioms-start
-- No unchanged callees are consumed: the combinator is modeled deeply.
-- axioms-end

-- pure-start
/-- A row of `n` independent (zero) entries. -/
def zeroRow (n : Nat) : List Nat := List.replicate n 0
-- pure-end

-- post-conditions-start
/-- The combined matrix is the block-diagonal (direct-sum) arrangement of the
two input matrices:
* it has one row per output of the two blocks together;
* the first `left.length` rows reproduce `left`'s own row, then `rin` zeros;
* the remaining rows are `lin` zeros, then `right`'s corresponding row. -/
def problem_spec_direct_sum
    (lin rin : Nat) (left right : List (List Nat)) (result : List (List Nat)) : Prop :=
  result.length = left.length + right.length ∧
  (∀ i, i < left.length →
      result.getD i [] = left.getD i [] ++ zeroRow rin) ∧
  (∀ i, left.length ≤ i → i < left.length + right.length →
      result.getD i [] = zeroRow lin ++ right.getD (i - left.length) [])
-- post-conditions-end

-- impl-start
def implementation_direct_sum
    (lin rin : Nat) (left right : List (List Nat)) : List (List Nat) := Id.run do
  let lout := left.length
  let rout := right.length
  let noutp := lout + rout
  let mut result : List (List Nat) := []
  for i in [0:noutp] do
    let cleftRow := if i < lout then left.getD i [] else zeroRow lin
    let crightRow := if lout ≤ i then right.getD (i - lout) [] else zeroRow rin
    result := result ++ [cleftRow ++ crightRow]
  return result
-- impl-end


-- proof-start
theorem correct_direct_sum :
    ∀ (lin rin : Nat) (left right : List (List Nat)),
      (∀ r ∈ left, r.length = lin) → (∀ r ∈ right, r.length = rin) →
      problem_spec_direct_sum lin rin left right
        (implementation_direct_sum lin rin left right) := by
  intro lin rin left right hleft hright
  have key : ∀ (l : List Nat) (f : Nat → List Nat) (acc : List (List Nat)),
      ((forIn l acc (fun i r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [f i]))))) : Id (List (List Nat)))
        = acc ++ l.map f := by
    intro l f acc
    induction l generalizing acc with
    | nil => simp; rfl
    | cons a t ih =>
        rw [List.forIn_cons]
        show ((forIn t (acc ++ [f a]) (fun i r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [f i]))))) : Id (List (List Nat))) = acc ++ (a::t).map f
        rw [ih]
        simp [List.append_assoc]
  have impl_eq : implementation_direct_sum lin rin left right =
      (List.range (left.length + right.length)).map (fun i =>
        (if i < left.length then left.getD i [] else zeroRow lin) ++
        (if left.length ≤ i then right.getD (i - left.length) [] else zeroRow rin)) := by
    unfold implementation_direct_sum Id.run
    simp only [Std.Range.forIn_eq_forIn_range', Std.Range.size, Nat.div_one]
    rw [key]
    simp only [List.nil_append, List.range_eq_range', Nat.add_sub_cancel]
    rfl
  rw [impl_eq]
  refine ⟨by simp, ?_, ?_⟩
  · intro i hi
    have hlt : i < left.length + right.length := by omega
    rw [List.getD_eq_getElem?_getD, List.getElem?_map, List.getElem?_range hlt]
    simp only [Option.map_some, Option.getD_some]
    rw [if_pos hi, if_neg (by omega)]
  · intro i hle hlt
    rw [List.getD_eq_getElem?_getD, List.getElem?_map, List.getElem?_range hlt]
    simp only [Option.map_some, Option.getD_some]
    rw [if_neg (by omega), if_pos hle]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. All 8 files confirmed same_spec=True vs Solution.lean via swebench_unified.markers.same_spec (lean backend). Note: lean spec_view elides BOTH impl and proof regions, so only axioms/pure/pre/post are byte-compared; all attacks left those regions and the shipped proof byte-identical, editing only the impl-region def body.

COMMAND (each): `bash scripts/lean_verify.sh <file>`.

### Results
- pos_control.lean (verbatim correct impl): exit 0 (VERIFIES). #print axioms correct_direct_sum => [propext, Classical.choice, Quot.sound] (clean, no sorryAx) via pos_axioms.lean exit 0.
- atk_1 PREPATCH BUG (right block of left-rows padded with `List.replicate rin 1` instead of zeros; i.e. cright=1): exit 1 (FAILS). Additionally positively DISPROVED: disproof_atk1.lean proves ¬spec at lin=1,rin=1,left=[[0]],right=[] — exit 0.
- atk_2 partial-domain (crightRow := zeroRow rin always; right block dropped): exit 1 (FAILS).
- atk_3 boundary/off-by-one (right.getD (i-lout+1)): exit 1 (FAILS).
- atk_4 control-flow-effect (return result.reverse; rows permuted): exit 1 (FAILS).
- atk_5 wrong-padding-width (pad left rows with zeroRow lin instead of rin): exit 1 (FAILS).
- atk_6 length off-by-one (loop [0:noutp-1]; drops last row): exit 1 (FAILS).
- atk_7 ungrounded-oracle-echo (blocks swapped: left placed bottom-left, right top): exit 1 (FAILS).

7 DISTINCT wrong impls attacked (partial-domain, boundary, control-flow-effect, wrong-width, length-defect, block-swap echo, plus the prepatch). Verifications run concurrently in two batches of 4 as background Bash jobs. NONE of the wrong impls produced a closing clean-axiom proof, so step-2 (materialize faithful patch + run_resolve) is vacuous — patches={} — there is no verify-but-wrong artifact to run.

REFINEMENT.md AUDIT: 6 legs, all tagged R (1,3,4,5) or I (2,6); axioms region is empty ('No unchanged callees are consumed: the combinator is modeled deeply'), so NO A-legs and NO kind-3 legs. mapping.md confirms deep-model correspondence to _cstack array/array branch (separable.py:219-247): op #5 (cright=right) is exactly the fixed line, op #4 zero-padded left block, op #6 hstack per-row concat. No A-reference callee to validate against a real callee. Correspondence holds.

VERDICT: SOUND — verify⇒correct holds; the tight spec (length + every-row getD pinned) admits no verifying same-spec wrong impl, and the prepatch is positively refuted.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous verification performed:
1. Solution.lean COMPILES (scripts/lean_verify.sh exit 0, no sorry). #print axioms correct_direct_sum = [propext, Classical.choice, Quot.sound] — CLEAN, no sorryAx; the proof is genuine, not a stub.
2. Spec (post-conditions region) is byte-identical between Solution.lean and Solution_prepatch.lean (spec fixed across bug/fix boundary), as required.
3. Modeling target confirmed against the REAL repo at base_commit d16bfe05: problem_spec_direct_sum models the array/array branch of _cstack in astropy/modeling/separable.py (post-patch). Gold patch fixes cright[...] = 1 -> = right; the spec's 3rd conjunct (result.getD i [] = zeroRow lin ++ right.getD (i-lout) []) faithfully encodes the FIXED behavior (copies right's rows verbatim), NOT the buggy all-ones fill. The prepatch (List.replicate rin 1) correctly fails the spec (G-DIFF pass).
4. FAITHFULNESS FUZZ (real patched _cstack vs the Lean-spec transliteration, numpy 1.26.4): over the reachable domain lin,rin,lout,rout in [1,6] with {0,1} entries, 200,000 random cases => 0 mismatches. Values preserved verbatim on both sides. Also tested arbitrary edge cases; the sole divergence is the rout=0 numpy-broadcast-error case described above, which is out-of-domain.
5. conformance_check.py (G-CONF, checked=83786 mismatches=0) fuzzes [0,6] but fails-open (try/except skip) on exactly the numpy-error degenerate inputs, consistent with treating them as out-of-domain.

Conclusion: The spec is NOT too strong and does not drift from real repo behavior on any reachable input. It is FAITHFUL. The only disagreement is on inputs numpy itself rejects and that the astropy call graph cannot produce.

Rigorous verification performed:
1. Solution.lean COMPILES (scripts/lean_verify.sh exit 0, no sorry). #print axioms correct_direct_sum = [propext, Classical.choice, Quot.sound] — CLEAN, no sorryAx; the proof is genuine, not a stub.
2. Spec (post-conditions region) is byte-identical between Solution.lean and Solution_prepatch.lean (spec fixed across bug/fix boundary), as required.
3. Modeling target confirmed against the REAL repo at base_commit d16bfe05: problem_spec_direct_sum models the array/array branch of _cstack in astropy/modeling/separable.py (post-patch). Gold patch fixes cright[...] = 1 -> = right; the spec's 3rd conjunct (result.getD i [] = zeroRow lin ++ right.getD (i-lout) []) faithfully encodes the FIXED behavior (copies right's rows verbatim), NOT the buggy all-ones fill. The prepatch (List.replicate rin 1) correctly fails the spec (G-DIFF pass).
4. FAITHFULNESS FUZZ (real patched _cstack vs the Lean-spec transliteration, numpy 1.26.4): over the reachable domain lin,rin,lout,rout in [1,6] with {0,1} entries, 200,000 random cases => 0 mismatches. Values preserved verbatim on both sides. Also tested arbitrary edge cases; the sole divergence is the rout=0 numpy-broadcast-error case described above, which is out-of-domain.
5. conformance_check.py (G-CONF, checked=83786 mismatches=0) fuzzes [0,6] but fails-open (try/except skip) on exactly the numpy-error degenerate inputs, consistent with treating them as out-of-domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen over spec_view) PASSES: no diff markers, no gold-patch line reproduced (neither 'cright[...] = 1' nor '= right' appears in the spec view), no patched file path (astropy/modeling/separable.py), no changed symbol ('cstack') echoed in identifiers or comments, no bug/fix narration. same_spec(Solution, Solution_prepatch)=True — the spec region is byte-identical, so the spec is a faithful discriminating spec, not fix-tailored. The post-condition problem_spec_direct_sum states correct block-diagonal (direct-sum) semantics SYMMETRICALLY for both left (left.getD i [] ++ zeroRow rin) and right (zeroRow lin ++ right.getD (i-left.length) []) blocks; this is the same altitude as the public problem_statement, which already shows the expected separable/block-diagonal output for nested CompoundModels. The spec does NOT localize the edit (does not reveal the bug is specifically in the right/cright branch, nor fill-with-1 vs copy). Gold-revealing prose ('= right' was '= 1', 'the fixed line') is confined to refinement.md/mapping.md, which are auditor-facing and not part of the consumer spec view. No leakage beyond problem_statement; hints_text is empty.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
