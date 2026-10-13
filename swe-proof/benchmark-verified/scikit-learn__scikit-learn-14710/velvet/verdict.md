# P2 adversarial audit — scikit-learn__scikit-learn-14710

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No consumed callee contracts. The per-element index→label lookup is the
@@ -60,10 +60,7 @@
   ensures isClf = false → out = y
   do
     -- impl-start
-    if isClf then
-      return gather labels y
-    else
-      return y
+    return y
     -- impl-end
 
 prove_correct prepareScorerTargets by
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
 -- (No consumed callee contracts. The per-element index→label lookup is the
@@ -61,9 +61,9 @@
   do
     -- impl-start
     if isClf then
+      return y
+    else
       return gather labels y
-    else
-      return y
     -- impl-end
 
 prove_correct prepareScorerTargets by
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
 -- (No consumed callee contracts. The per-element index→label lookup is the
@@ -60,10 +60,7 @@
   ensures isClf = false → out = y
   do
     -- impl-start
-    if isClf then
-      return gather labels y
-    else
-      return y
+    return gather labels y
     -- impl-end
 
 prove_correct prepareScorerTargets by
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
 -- (No consumed callee contracts. The per-element index→label lookup is the
@@ -61,7 +61,7 @@
   do
     -- impl-start
     if isClf then
-      return gather labels y
+      return gather y labels
     else
       return y
     -- impl-end
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
 -- (No consumed callee contracts. The per-element index→label lookup is the
@@ -61,7 +61,7 @@
   do
     -- impl-start
     if isClf then
-      return gather labels y
+      return y.map (fun i => labels[i.toNat + 1]!)
     else
       return y
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
 -- (No consumed callee contracts. The per-element index→label lookup is the
@@ -61,7 +61,7 @@
   do
     -- impl-start
     if isClf then
-      return gather labels y
+      return (gather labels y).reverse
     else
       return y
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-element index→label lookup is the
--  ordinary table-indexing operation, modeled deeply as `gather` below; it is
--  not borrowed from any axiomatized callee, so there is no soundness to import
--  and no axiom_check.py. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- Look up each entry of `idxs` in `table` and collect the results in order.
   `idxs` carries integer codes, each an index into `table`; the result is the
   ordered, count-preserving sequence of the looked-up entries. Written as a
   front-to-back element-wise map so a single per-element fact discharges it. -/
def gather (table : List Int) (idxs : List Int) : List Int :=
  idxs.map (fun i => table[i.toNat]!)

@[grind] lemma gather_def (table idxs : List Int) :
    gather table idxs = idxs.map (fun i => table[i.toNat]!) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare the target sequence that is handed to the evaluation scorer.

   The targets `y` arrive as integer codes. When the estimation task is a
   CLASSIFICATION task, these codes index a table `labels` of the original
   class labels, and the score must be computed against those original labels:
   the prepared targets are obtained by looking each code up in `labels`, in
   order (an order- and count-preserving lookup). When the task is NOT a
   classification task, the targets are already in their final form and are
   handed to the scorer unchanged.

   Two guarantees pin the demanded behavior:
   - classification (`isClf = true`): the prepared targets are exactly the
     per-code lookups of `y` through `labels`, in order — the codes are mapped
     back to the original labels they stand for before scoring (so the scorer
     compares values from the same domain as its predictions);
   - non-classification (`isClf = false`): the prepared targets equal `y`
     exactly — the read-only input target sequence is passed through with
     nothing added, dropped, reordered, or transformed (directive-5 frame).

   `isClf`, `labels`, `y` are read-only inputs; a fresh sequence is produced and
   no input is mutated. The precondition records that every code is a valid
   index into `labels` (codes range over `0 … labels.length - 1`). -/
method prepareScorerTargets (isClf : Bool) (labels : List Int) (y : List Int)
    return (out : List Int)
  require ∀ i, i ∈ y → 0 ≤ i ∧ i.toNat < labels.length
  ensures isClf = true  → out = gather labels y
  ensures isClf = false → out = y
  do
    -- impl-start
    if isClf then
      return gather labels y
    else
      return y
    -- impl-end

prove_correct prepareScorerTargets by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) — velvet scikit-learn__scikit-learn-14710, method prepareScorerTargets.

SPEC SHAPE: two ensures FULLY pin the output on both Bool legs: (isClf=true -> out = gather labels y) and (isClf=false -> out = y), where gather table idxs = idxs.map (fun i => table[i.toNat]!). require: forall i in y, 0<=i and i.toNat < labels.length. No slack -> no room for a verifying-but-wrong impl.

SAME-SPEC: same_spec(Solution.lean, X, velvet.language)=True for pc.lean and all 6 attacks (impl-region-only edits; axioms/pure/pre/post byte-identical). Verified via swebench_unified.markers.same_spec + backends.get_backend('velvet').

COMMANDS (run concurrently in 2 background batches of <=4): bash scripts/lean_verify.sh <path>.

### RESULTS (exit 0=verifies, 1=error/unsolved-goals):
- pc.lean (byte-identical correct impl, positive control): EXIT 0 (verifies).
- atk_1 return y on both legs (= PREPATCH BUG, reproduced): EXIT 1, 'unsolved goals' at prove_correct (fails isClf=true -> out=gather labels y).
- atk_2 control-flow-effect, branches swapped (if isClf then return y else return gather labels y): EXIT 1 unsolved goals.
- atk_3 partial-domain, always gather (drops regressor pass-through): EXIT 1 unsolved goals (fails isClf=false -> out=y).
- atk_4 ungrounded-oracle echo, args swapped (gather y labels): EXIT 1 unsolved goals.
- atk_5 boundary/off-by-one (labels[i.toNat+1]!): EXIT 1 unsolved goals.
- atk_6 order-violating ((gather labels y).reverse): EXIT 1 unsolved goals.
All six failures are genuine spec-obligation 'unsolved goals' at prove_correct, not parse errors (confirmed by grep of *.out).

RESOLVE STEP: Protocol step 2 requires materializing + run_resolve-running a faithful patch ONLY for wrong impls that VERIFY. ZERO wrong impls verified (the spec fully pins out on both legs), so the verifying-wrong-impl set is empty -> no faithful patch to run, no verify-not-correct break to exhibit. patches={} accordingly.

A-LEG / correspondence audit (the focus of this pass): refinement.md legs are all R or I, NO A-consumed and NO A-reference. Solution.lean axioms region is comment-only (grep: zero 'axiom' declarations). gather is a fully-defined DEEP MODEL of the ordinary total operation classes_[y.astype(int)] (NumPy fancy index), spelled out as idxs.map (table[i.toNat]!) with @[grind] gather_def — correctly tagged I under the R type bijection (is_classifier<->isClf, classes_<->labels, integer-code array<->y, fancy-index<->gather). G-AX=skip is justified: no axiomatized callee contract imported, no opaque unchanged-callee map to validate, so no axiom trust point to attack. Unchanged callee self.scorer_ correctly out of scope. No kind-3 (inexpressible-changed-op) legs. The require is a domain RESTRICTION matching the real _encode_y invariant (codes 0..n_classes-1) => weakens, keeps deep model total/faithful.

VERDICT: SOUND. >=5 (6) distinct same-spec wrong impls attempted and every one rejected by the official verifier while the positive control verifies; prepatch bug reproduced (atk_1); no verifying wrong impl exists so verify=>correct is not broken. Spec is tight and refinement fidelity holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The per-element index→label lookup is the
--  ordinary table-indexing operation, modeled deeply as `gather` below; it is
--  not borrowed from any axiomatized callee, so there is no soundness to import
--  and no axiom_check.py. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- Look up each entry of `idxs` in `table` and collect the results in order.
   `idxs` carries integer codes, each an index into `table`; the result is the
   ordered, count-preserving sequence of the looked-up entries. Written as a
   front-to-back element-wise map so a single per-element fact discharges it. -/
def gather (table : List Int) (idxs : List Int) : List Int :=
  idxs.map (fun i => table[i.toNat]!)

@[grind] lemma gather_def (table idxs : List Int) :
    gather table idxs = idxs.map (fun i => table[i.toNat]!) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare the target sequence that is handed to the evaluation scorer.

   The targets `y` arrive as integer codes. When the estimation task is a
   CLASSIFICATION task, these codes index a table `labels` of the original
   class labels, and the score must be computed against those original labels:
   the prepared targets are obtained by looking each code up in `labels`, in
   order (an order- and count-preserving lookup). When the task is NOT a
   classification task, the targets are already in their final form and are
   handed to the scorer unchanged.

   Two guarantees pin the demanded behavior:
   - classification (`isClf = true`): the prepared targets are exactly the
     per-code lookups of `y` through `labels`, in order — the codes are mapped
     back to the original labels they stand for before scoring (so the scorer
     compares values from the same domain as its predictions);
   - non-classification (`isClf = false`): the prepared targets equal `y`
     exactly — the read-only input target sequence is passed through with
     nothing added, dropped, reordered, or transformed (directive-5 frame).

   `isClf`, `labels`, `y` are read-only inputs; a fresh sequence is produced and
   no input is mutated. The precondition records that every code is a valid
   index into `labels` (codes range over `0 … labels.length - 1`). -/
method prepareScorerTargets (isClf : Bool) (labels : List Int) (y : List Int)
    return (out : List Int)
  require ∀ i, i ∈ y → 0 ≤ i ∧ i.toNat < labels.length
  ensures isClf = true  → out = gather labels y
  ensures isClf = false → out = y
  do
    -- impl-start
    if isClf then
      return gather labels y
    else
      return y
    -- impl-end

prove_correct prepareScorerTargets by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) — velvet scikit-learn__scikit-learn-14710, method prepareScorerTargets.

SPEC SHAPE: two ensures FULLY pin the output on both Bool legs: (isClf=true -> out = gather labels y) and (isClf=false -> out = y), where gather table idxs = idxs.map (fun i => table[i.toNat]!). require: forall i in y, 0<=i and i.toNat < labels.length. No slack -> no room for a verifying-but-wrong impl.

SAME-SPEC: same_spec(Solution.lean, X, velvet.language)=True for pc.lean and all 6 attacks (impl-region-only edits; axioms/pure/pre/post byte-identical). Verified via swebench_unified.markers.same_spec + backends.get_backend('velvet').

COMMANDS (run concurrently in 2 background batches of <=4): bash scripts/lean_verify.sh <path>.

### RESULTS (exit 0=verifies, 1=error/unsolved-goals):
- pc.lean (byte-identical correct impl, positive control): EXIT 0 (verifies).
- atk_1 return y on both legs (= PREPATCH BUG, reproduced): EXIT 1, 'unsolved goals' at prove_correct (fails isClf=true -> out=gather labels y).
- atk_2 control-flow-effect, branches swapped (if isClf then return y else return gather labels y): EXIT 1 unsolved goals.
- atk_3 partial-domain, always gather (drops regressor pass-through): EXIT 1 unsolved goals (fails isClf=false -> out=y).
- atk_4 ungrounded-oracle echo, args swapped (gather y labels): EXIT 1 unsolved goals.
- atk_5 boundary/off-by-one (labels[i.toNat+1]!): EXIT 1 unsolved goals.
- atk_6 order-violating ((gather labels y).reverse): EXIT 1 unsolved goals.
All six failures are genuine spec-obligation 'unsolved goals' at prove_correct, not parse errors (confirmed by grep of *.out).

RESOLVE STEP: Protocol step 2 requires materializing + run_resolve-running a faithful patch ONLY for wrong impls that VERIFY. ZERO wrong impls verified (the spec fully pins out on both legs), so the verifying-wrong-impl set is empty -> no faithful patch to run, no verify-not-correct break to exhibit. patches={} accordingly.

A-LEG / correspondence audit (the focus of this pass): refinement.md legs are all R or I, NO A-consumed and NO A-reference. Solution.lean axioms region is comment-only (grep: zero 'axiom' declarations). gather is a fully-defined DEEP MODEL of the ordinary total operation classes_[y.astype(int)] (NumPy fancy index), spelled out as idxs.map (table[i.toNat]!) with @[grind] gather_def — correctly tagged I under the R type bijection (is_classifier<->isClf, classes_<->labels, integer-code array<->y, fancy-index<->gather). G-AX=skip is justified: no axiomatized callee contract imported, no opaque unchanged-callee map to validate, so no axiom trust point to attack. Unchanged callee self.scorer_ correctly out of scope. No kind-3 (inexpressible-changed-op) legs. The require is a domain RESTRICTION matching the real _encode_y invariant (codes 0..n_classes-1) => weakens, keeps deep model total/faithful.

VERDICT: SOUND. >=5 (6) distinct same-spec wrong impls attempted and every one rejected by the official verifier while the positive control verifies; prepatch bug reproduced (atk_1); no verifying wrong impl exists so verify=>correct is not broken. Spec is tight and refinement fidelity holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of velvet prepareScorerTargets vs the real _check_early_stopping_scorer scorer-target prep at base_commit 4b6273b8 (sklearn/ensemble/_hist_gradient_boosting/gradient_boosting.py). Verified prerequisites: (1) same_spec(Solution, Solution_prepatch, velvet) == True — spec region byte-identical, so the spec is genuinely frozen; (2) Solution.lean elaborates clean (lean_verify exit 0, no sorry/error); (3) conformance_check.py passes 0 disagreements over 100011 inputs.

Model checked against real repo on the full precondition domain (require: every code i in y satisfies 0 <= i and i.toNat < labels.length):
- Classifier leg (isClf=true): model out = gather labels y = y.map(fun i => labels[i.toNat]!); real gold = classes_[y.astype(int)] (NumPy fancy index). Both are order- and count-preserving element-wise label lookups. Under the in-range require, getElem! never returns its default, matching in-range fancy indexing; codes are exact small ints (0..n_classes-1) so .astype(int) == .toNat. Agree on all inputs.
- Regressor leg (isClf=false): model out = y; real passes y through unchanged. Agree.
- Boundary cases (empty y, singleton, all-same code, repeats, full-range reversed, every class once) all covered with zero disagreement.

No input within the precondition makes the model demand an output the real callee does not produce. The require on the regressor leg constraining labels only WEAKENS the spec (more vacuous) — not an over-strong/drift direction. The prepatch (return y on both legs) correctly fails the discriminating clause isClf=true -> out = gather labels y, confirming the frozen postcondition captures exactly the gold behavior. No divergence found; spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigor checks: same_spec(Solution.lean, Solution_prepatch.lean)=True with VelvetBackend.language tables; the spec view elides impl-start/impl-end and the proof body (consumer-supplied). Mechanical lexical screen (leakage.screen) passes with zero hard_failures. Semantic assessment: the spec view discloses (a) a `gather labels y` = per-code table lookup that maps integer codes back to original labels, (b) a classification-vs-regression branch (isClf true → decode, false → pass-through), (c) the scorer-target-preparation context. ALL of this is already fully public in the problem_statement, which explicitly states 'The scorer used under the hood... is provided with y_true being integer while y_pred are original classes (i.e. string). We need to encode y_true each time that we want to compute the score' AND includes a 'Potential resolution' diff giving the exact edit `if hasattr(self, 'classes_'): y_small_train = self.classes_[y_small_train.astype(int)]` for both the train and validation sites. The gold patch differs only in the guard predicate (`is_classifier(self)` vs `hasattr(self, 'classes_')`), a triviality not exposed by the spec. Therefore the spec view leaks nothing about the gold edit beyond the public problem_statement (which itself contains a near-verbatim resolution diff). No line in the spec view reveals gold-specific detail beyond problem_statement. (Note: hints_text excluded from consideration per task scope; conclusion holds on problem_statement alone.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
