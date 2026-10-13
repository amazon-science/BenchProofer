# P2 adversarial audit — sympy__sympy-13877

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_last.lean`, `atk_3_skip0.lean`, `atk_4_offbyone.lean`, `atk_5_neverfound.lean`, `atk_7_idxplus.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,14 +70,14 @@
     let mut idx := 0
     while i < col.size ∧ found = false
       invariant 0 ≤ i ∧ i ≤ col.size
-      invariant found = false → (∀ j, j < i → (col[j]!).mathNonzero = false)
+      invariant found = false → (∀ j, j < i → (col[j]!).litNonzero = false)
       invariant found = true →
-        (idx < col.size ∧ (col[idx]!).mathNonzero = true ∧
-          (∀ j, j < idx → (col[j]!).mathNonzero = false))
+        (idx < col.size ∧ (col[idx]!).litNonzero = true ∧
+          (∀ j, j < idx → (col[j]!).litNonzero = false))
       done_with (i = col.size ∨ found = true)
       decreasing col.size - i
     do
-      if (col[i]!).mathNonzero = true then
+      if (col[i]!).litNonzero = true then
         idx := i
         found := true
       i := i + 1
```

Attack 2 — `atk_2_last.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,13 +68,9 @@
     let mut i := 0
     let mut found := false
     let mut idx := 0
-    while i < col.size ∧ found = false
+    while i < col.size
       invariant 0 ≤ i ∧ i ≤ col.size
-      invariant found = false → (∀ j, j < i → (col[j]!).mathNonzero = false)
-      invariant found = true →
-        (idx < col.size ∧ (col[idx]!).mathNonzero = true ∧
-          (∀ j, j < idx → (col[j]!).mathNonzero = false))
-      done_with (i = col.size ∨ found = true)
+      done_with (i = col.size)
       decreasing col.size - i
     do
       if (col[i]!).mathNonzero = true then
```

Attack 3 — `atk_3_skip0.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,11 +65,11 @@
     (∀ j, j < col.size → (col[j]!).mathNonzero = false)
   do
     -- impl-start
-    let mut i := 0
+    let mut i := 1
     let mut found := false
     let mut idx := 0
     while i < col.size ∧ found = false
-      invariant 0 ≤ i ∧ i ≤ col.size
+      invariant 1 ≤ i ∧ i ≤ col.size
       invariant found = false → (∀ j, j < i → (col[j]!).mathNonzero = false)
       invariant found = true →
         (idx < col.size ∧ (col[idx]!).mathNonzero = true ∧
```

Attack 4 — `atk_4_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,13 +68,13 @@
     let mut i := 0
     let mut found := false
     let mut idx := 0
-    while i < col.size ∧ found = false
+    while i + 1 < col.size ∧ found = false
       invariant 0 ≤ i ∧ i ≤ col.size
       invariant found = false → (∀ j, j < i → (col[j]!).mathNonzero = false)
       invariant found = true →
         (idx < col.size ∧ (col[idx]!).mathNonzero = true ∧
           (∀ j, j < idx → (col[j]!).mathNonzero = false))
-      done_with (i = col.size ∨ found = true)
+      done_with (i + 1 = col.size ∨ found = true)
       decreasing col.size - i
     do
       if (col[i]!).mathNonzero = true then
```

Attack 5 — `atk_5_neverfound.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,22 +66,13 @@
   do
     -- impl-start
     let mut i := 0
-    let mut found := false
-    let mut idx := 0
-    while i < col.size ∧ found = false
+    while i < col.size
       invariant 0 ≤ i ∧ i ≤ col.size
-      invariant found = false → (∀ j, j < i → (col[j]!).mathNonzero = false)
-      invariant found = true →
-        (idx < col.size ∧ (col[idx]!).mathNonzero = true ∧
-          (∀ j, j < idx → (col[j]!).mathNonzero = false))
-      done_with (i = col.size ∨ found = true)
+      done_with (i = col.size)
       decreasing col.size - i
     do
-      if (col[i]!).mathNonzero = true then
-        idx := i
-        found := true
       i := i + 1
-    return ⟨found, idx⟩
+    return ⟨false, 0⟩
     -- impl-end
 
 prove_correct selectPivot by
```

Attack 6 — `atk_7_idxplus.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,7 @@
       decreasing col.size - i
     do
       if (col[i]!).mathNonzero = true then
-        idx := i
+        idx := i + 1
         found := true
       i := i + 1
     return ⟨found, idx⟩
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The decisive zero-recogniser this operation depends on is
   modeled DEEPLY by the `mathNonzero` field of `Entry` (see the `pure` region)
   and validated against the real recogniser by axiom_check.py (G-AX); it is an
   A-reference, not an axiom the proof consumes. -/
-- axioms-end

-- pure-start
/- A column entry, abstracted to the two boolean observations the selection step
   makes of a scalar value:

   * `litNonzero` — the cheap, structural recogniser: the value is not one of the
     recognised numeric/literal zeros.
   * `mathNonzero` — the decisive recogniser: the value is still non-zero after
     algebraic normalisation. This is the observation that decides selection.

   For every real scalar, `mathNonzero` implies `litNonzero` (a value non-zero
   after normalisation is certainly not a literal zero); the converse may fail —
   a value can look structurally non-zero yet normalise to zero. The bijection to
   the repository scalar type and the soundness check live in mapping.md §2/§3
   and axiom_check.py (G-AX). -/
structure Entry where
  litNonzero  : Bool
  mathNonzero : Bool
deriving Inhabited, Repr

/- The result of the selection step: whether a usable entry exists and, if so,
   its index in the column. -/
structure PivotResult where
  found : Bool
  idx   : Nat
deriving Inhabited, Repr

/- The standing relationship between the two recognisers on every real scalar:
   decisive non-zero ⟹ structurally non-zero. Stated over a whole column. -/
@[grind] def consistent (col : Array Entry) : Prop :=
  ∀ j, j < col.size → (col[j]!).mathNonzero = true → (col[j]!).litNonzero = true
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the first column entry usable for the elimination step: scan the
   column in order and choose the first index whose value is decisively non-zero
   (`mathNonzero`). Report whether such an index exists and which one. The
   decision must rest on the decisive recogniser alone — an entry that merely
   looks non-zero but normalises to zero must be skipped. -/
method selectPivot (col : Array Entry) return (res : PivotResult)
  require consistent col
  ensures res.found = true →
    res.idx < col.size ∧ (col[res.idx]!).mathNonzero = true ∧
      (∀ j, j < res.idx → (col[j]!).mathNonzero = false)
  ensures res.found = false →
    (∀ j, j < col.size → (col[j]!).mathNonzero = false)
  do
    -- impl-start
    let mut i := 0
    let mut found := false
    let mut idx := 0
    while i < col.size ∧ found = false
      invariant 0 ≤ i ∧ i ≤ col.size
      invariant found = false → (∀ j, j < i → (col[j]!).mathNonzero = false)
      invariant found = true →
        (idx < col.size ∧ (col[idx]!).mathNonzero = true ∧
          (∀ j, j < idx → (col[j]!).mathNonzero = false))
      done_with (i = col.size ∨ found = true)
      decreasing col.size - i
    do
      if (col[i]!).mathNonzero = true then
        idx := i
        found := true
      i := i + 1
    return ⟨found, idx⟩
    -- impl-end

prove_correct selectPivot by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Velvet bundle sympy__sympy-13877, G-EQ refinement-fidelity audit. All commands. same_spec confirmed True for all 8 files via swebench_unified.markers.same_spec (velvet). Verify cmd per file: `bash scripts/lean_verify.sh <file>` (exit0=verifies, 1=error). Ran concurrently in two ≤4 background batches.

RESULTS: positive_control.lean -> EXIT 0 (verifies). Correct alternate atk_6_echo.lean -> EXIT 0 (verifies; not counted as an attack since it is a correct impl, only shows the spec is not vacuously rejecting). Six DISTINCT same-spec WRONG impls all FAIL to verify (EXIT 1):
 - atk_1_prepatch: guards on litNonzero (structural) not mathNonzero = the exact prepatch #12362 bug; fails ensures (col[res.idx]!).mathNonzero=true. PREPATCH REPRODUCED.
 - atk_2_last: no early stop, records last mathNonzero index; fails first-index minimality invariant.
 - atk_3_skip0 (partial-domain): starts scan at i=1; cannot prove forall j<idx for j=0.
 - atk_4_offbyone (boundary): loop guard i+1<col.size misses last entry; fails found=false coverage clause.
 - atk_5_neverfound (ungrounded-oracle echo): always returns found=false; fails ensures found=false -> forall j, mathNonzero=false when a nonzero entry exists.
 - atk_7_idxplus (boundary): idx:=i+1; fails mathNonzero(idx) / idx<col.size.

The two ensures clauses functionally PIN selectPivot to 'first index with mathNonzero=true, else found=false' -- a complete functional spec on the modeled non-Float branch. Therefore NO same-spec wrong impl verifies. The mandatory 'materialize faithful patch -> run_resolve for every VERIFYING wrong impl' obligation is VACUOUSLY discharged: zero verifying wrong impls exist, so patches={} and no resolve run was needed (nothing to falsify with). This is reported per protocol, not skipped.

refinement.md leg audit: A1=R (column mat[:,0] <-> Array Entry), A2=A-reference (expand_mul(x)!=0 => bool(x)), A3=A-reference + I (mathNonzero == not _is_zero_after_expand_mul; scan ops I), A4=R (pivot_offset <-> found/idx). NO kind-3 (inexpressible-changed-op) leg: the single genuinely-changed op (decisive zero-test) is modeled DEEPLY via Entry.mathNonzero + spelled-out scan, not hidden behind a consumed axiom (axioms region empty). A-reference correspondences match the real post-patch callees _is_zero_after_expand_mul (matrices.py:39-46) and _find_reasonable_pivot decisive-iszerofunc branch, G-AX-checked. Correspondence holds.

VERDICT SOUND: 6 distinct attacks run (>=5), positive control + correct alternate verify, prepatch reproduced, no verifying wrong impl -> verify=>correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_2_last.lean`, `atk_3_skip0.lean`, `atk_4_offbyone.lean`, `atk_5_neverfound.lean`, `atk_7_idxplus.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_last.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_skip0.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_neverfound.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7_idxplus.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The decisive zero-recogniser this operation depends on is
   modeled DEEPLY by the `mathNonzero` field of `Entry` (see the `pure` region)
   and validated against the real recogniser by axiom_check.py (G-AX); it is an
   A-reference, not an axiom the proof consumes. -/
-- axioms-end

-- pure-start
/- A column entry, abstracted to the two boolean observations the selection step
   makes of a scalar value:

   * `litNonzero` — the cheap, structural recogniser: the value is not one of the
     recognised numeric/literal zeros.
   * `mathNonzero` — the decisive recogniser: the value is still non-zero after
     algebraic normalisation. This is the observation that decides selection.

   For every real scalar, `mathNonzero` implies `litNonzero` (a value non-zero
   after normalisation is certainly not a literal zero); the converse may fail —
   a value can look structurally non-zero yet normalise to zero. The bijection to
   the repository scalar type and the soundness check live in mapping.md §2/§3
   and axiom_check.py (G-AX). -/
structure Entry where
  litNonzero  : Bool
  mathNonzero : Bool
deriving Inhabited, Repr

/- The result of the selection step: whether a usable entry exists and, if so,
   its index in the column. -/
structure PivotResult where
  found : Bool
  idx   : Nat
deriving Inhabited, Repr

/- The standing relationship between the two recognisers on every real scalar:
   decisive non-zero ⟹ structurally non-zero. Stated over a whole column. -/
@[grind] def consistent (col : Array Entry) : Prop :=
  ∀ j, j < col.size → (col[j]!).mathNonzero = true → (col[j]!).litNonzero = true
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the first column entry usable for the elimination step: scan the
   column in order and choose the first index whose value is decisively non-zero
   (`mathNonzero`). Report whether such an index exists and which one. The
   decision must rest on the decisive recogniser alone — an entry that merely
   looks non-zero but normalises to zero must be skipped. -/
method selectPivot (col : Array Entry) return (res : PivotResult)
  require consistent col
  ensures res.found = true →
    res.idx < col.size ∧ (col[res.idx]!).mathNonzero = true ∧
      (∀ j, j < res.idx → (col[j]!).mathNonzero = false)
  ensures res.found = false →
    (∀ j, j < col.size → (col[j]!).mathNonzero = false)
  do
    -- impl-start
    let mut i := 0
    let mut found := false
    let mut idx := 0
    while i < col.size ∧ found = false
      invariant 0 ≤ i ∧ i ≤ col.size
      invariant found = false → (∀ j, j < i → (col[j]!).mathNonzero = false)
      invariant found = true →
        (idx < col.size ∧ (col[idx]!).mathNonzero = true ∧
          (∀ j, j < idx → (col[j]!).mathNonzero = false))
      done_with (i = col.size ∨ found = true)
      decreasing col.size - i
    do
      if (col[i]!).mathNonzero = true then
        idx := i
        found := true
      i := i + 1
    return ⟨found, idx⟩
    -- impl-end

prove_correct selectPivot by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Velvet bundle sympy__sympy-13877, G-EQ refinement-fidelity audit. All commands. same_spec confirmed True for all 8 files via swebench_unified.markers.same_spec (velvet). Verify cmd per file: `bash scripts/lean_verify.sh <file>` (exit0=verifies, 1=error). Ran concurrently in two ≤4 background batches.

RESULTS: positive_control.lean -> EXIT 0 (verifies). Correct alternate atk_6_echo.lean -> EXIT 0 (verifies; not counted as an attack since it is a correct impl, only shows the spec is not vacuously rejecting). Six DISTINCT same-spec WRONG impls all FAIL to verify (EXIT 1):
 - atk_1_prepatch: guards on litNonzero (structural) not mathNonzero = the exact prepatch #12362 bug; fails ensures (col[res.idx]!).mathNonzero=true. PREPATCH REPRODUCED.
 - atk_2_last: no early stop, records last mathNonzero index; fails first-index minimality invariant.
 - atk_3_skip0 (partial-domain): starts scan at i=1; cannot prove forall j<idx for j=0.
 - atk_4_offbyone (boundary): loop guard i+1<col.size misses last entry; fails found=false coverage clause.
 - atk_5_neverfound (ungrounded-oracle echo): always returns found=false; fails ensures found=false -> forall j, mathNonzero=false when a nonzero entry exists.
 - atk_7_idxplus (boundary): idx:=i+1; fails mathNonzero(idx) / idx<col.size.

The two ensures clauses functionally PIN selectPivot to 'first index with mathNonzero=true, else found=false' -- a complete functional spec on the modeled non-Float branch. Therefore NO same-spec wrong impl verifies. The mandatory 'materialize faithful patch -> run_resolve for every VERIFYING wrong impl' obligation is VACUOUSLY discharged: zero verifying wrong impls exist, so patches={} and no resolve run was needed (nothing to falsify with). This is reported per protocol, not skipped.

refinement.md leg audit: A1=R (column mat[:,0] <-> Array Entry), A2=A-reference (expand_mul(x)!=0 => bool(x)), A3=A-reference + I (mathNonzero == not _is_zero_after_expand_mul; scan ops I), A4=R (pivot_offset <-> found/idx). NO kind-3 (inexpressible-changed-op) leg: the single genuinely-changed op (decisive zero-test) is modeled DEEPLY via Entry.mathNonzero + spelled-out scan, not hidden behind a consumed axiom (axioms region empty). A-reference correspondences match the real post-patch callees _is_zero_after_expand_mul (matrices.py:39-46) and _find_reasonable_pivot decisive-iszerofunc branch, G-AX-checked. Correspondence holds.

VERDICT SOUND: 6 distinct attacks run (>=5), positive control + correct alternate verify, prepatch reproduced, no verifying wrong impl -> verify=>correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical with Solution_prepatch.lean (swebench_unified.markers.same_spec = True). Solution.lean verifies (scripts/lean_verify.sh exit 0). Independently validated the modeled function against the REAL repo callee _find_reasonable_pivot(mat[:,0], iszerofunc=_is_zero_after_expand_mul) at base_commit (sympy 1.1.2.dev, py3.8 venv,:). (1) Ran 100k+ fuzzed non-Float columns across two independent harnesses (structured pool + random polynomial/rational expression generator with injected expand_mul-zero pseudo-zeros); zero divergences on (found, idx). (2) _is_zero_after_expand_mul was ALWAYS decisive (never None) on every tested scalar, so _find_reasonable_pivot's PASS 2/PASS 3 fallthrough never fires — PASS 1 alone selects the first index where iszerofunc==False, i.e. first expand_mul(x)!=0, exactly the model's scan. (3) The `require consistent col` precondition (mathNonzero → litNonzero, i.e. expand_mul(x)!=0 ⟹ bool(x)) held on EVERY real scalar tested and every fuzzed column — it excludes no real column, so the spec is not too strong / does not narrow behavior via an unsatisfiable precondition. (4) Empty column matches (both (False,-1)). (5) The discriminating pseudo-zero case a*(a+1)-a**2-a (litNonzero=true, mathNonzero=false) is correctly skipped by both model and real callee. The abstraction (column↔Array Entry, pivot_offset↔found/idx) and the deep-recogniser model faithfully track the real callee within the modeled non-Float branch. No drift / spec-too-strong defect found.

Counterexample / evidence:

```
No in-domain counterexample found. Out-of-domain (documented as excluded): [Float(1.0), Float(5.0), Float(2.0)] → real (found=true, idx=1) vs model (found=true, idx=0).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Dispositioned relaxed-leakage bundle, re-verified independently (not rubber-stamped). meta.json relaxed_leakage=true, G-LEAK=relaxed, RELAXED_LEAKAGE.md present. Spec region frozen: same_spec(Solution, Solution_prepatch)=True; Solution.lean verifies (lean_verify exit 0). 

The spec view DOES leak the gold discriminator beyond problem_statement — the pure-region Entry docstring ('mathNonzero — the value is still non-zero after algebraic normalisation. This is the observation that decides selection'), the method docstring ('an entry that merely looks non-zero but normalises to zero must be skipped'), and the postcondition 'res.found = true → (col[res.idx]!).mathNonzero = true' all encode the structural-truthiness→algebraic-zero pivot-test that is the gold fix (_find_reasonable_pivot with iszerofunc=_is_zero_after_expand_mul). Token scan of problem_statement confirms 0 occurrences of zero/nonzero/expand/normalis/iszero/select (the 3 'pivot' hits are incidental 'pivot_val' in the traceback); the discriminator vocabulary lives only in the EXCLUDED hints_text ('val = val.expand() before if val:') and the gold diff.

However this facet is EXACTLY the one covered by the accepted disposition, and the leak is provably unavoidable under faithfulness: G-DIFF requires Solution_prepatch (litNonzero/structural scan) to fail, forcing any faithful spec to distinguish the two recognisers precisely on entries where they disagree (structurally non-zero yet algebraically zero — the issue's a*(a-1)-a*a+a pattern); a problem_statement-only spec (crash traceback + the reporter's wrong integer-matrix hypothesis) cannot pin selection to the algebraic recogniser without either admitting the prepatch (spec-too-weak) or pinning unrelated non-faithful behavior. Core soundness re-confirmed intact (G-VERIFY/DIFF/EQ/CONF/AX/PANEL-1/PANEL-2 pass; positive control verifies, prepatch fails on the discriminating clause). 

No NEW leaking line beyond the dispositioned structural-vs-algebraic pivot-test facet was found: the spec view stays abstract (no Bareiss/determinant/_find_reasonable_pivot/expand_mul repo names), and the second gold site (randtest.py tolerance keyword) is test-neutral, not modeled, and not leaked. The unavoidability argument is not refuted. Per the G-PANEL-3 relaxed-leakage recording convention (defer to accepted RELAXED_LEAKAGE.md; record pass/NO-LEAKAGE for the known dispositioned facet), verdict is NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
