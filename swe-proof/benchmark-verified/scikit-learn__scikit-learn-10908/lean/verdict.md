# P2 adversarial audit — scikit-learn__scikit-learn-10908

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,14 @@
               (¬ v.isEmpty → result = Except.ok (featureNames v))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_getFeatureNames
     (st : VecState) : Except VErr (List String) := Id.run do
   let mut voc : List (String × Nat) := []
   match st.learned with
   | some v => voc := v
-  | none =>
-    match st.param with
-    | none => return Except.error VErr.notFitted
-    | some p =>
-      match validateList p with
-      | Except.error e => return Except.error e
-      | Except.ok v => voc := v
+  | none => return Except.error VErr.notFitted   -- BUG: never consults param
   if voc.isEmpty then return Except.error VErr.empty
   return Except.ok (featureNames voc)
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,6 +70,7 @@
               (¬ v.isEmpty → result = Except.ok (featureNames v))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_getFeatureNames
     (st : VecState) : Except VErr (List String) := Id.run do
@@ -83,7 +84,7 @@
       match validateList p with
       | Except.error e => return Except.error e
       | Except.ok v => voc := v
-  if voc.isEmpty then return Except.error VErr.empty
+  if voc.isEmpty then return Except.error VErr.notFitted  -- BUG: should be empty
   return Except.ok (featureNames voc)
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,21 @@
               (¬ v.isEmpty → result = Except.ok (featureNames v))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_getFeatureNames
     (st : VecState) : Except VErr (List String) := Id.run do
   let mut voc : List (String × Nat) := []
-  match st.learned with
-  | some v => voc := v
+  -- BUG: consult param FIRST, overriding an already-available learned vocab
+  match st.param with
+  | some p =>
+    match validateList p with
+    | Except.error e => return Except.error e
+    | Except.ok v => voc := v
   | none =>
-    match st.param with
+    match st.learned with
+    | some v => voc := v
     | none => return Except.error VErr.notFitted
-    | some p =>
-      match validateList p with
-      | Except.error e => return Except.error e
-      | Except.ok v => voc := v
   if voc.isEmpty then return Except.error VErr.empty
   return Except.ok (featureNames voc)
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,21 +70,12 @@
               (¬ v.isEmpty → result = Except.ok (featureNames v))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_getFeatureNames
-    (st : VecState) : Except VErr (List String) := Id.run do
-  let mut voc : List (String × Nat) := []
-  match st.learned with
-  | some v => voc := v
-  | none =>
-    match st.param with
-    | none => return Except.error VErr.notFitted
-    | some p =>
-      match validateList p with
-      | Except.error e => return Except.error e
-      | Except.ok v => voc := v
-  if voc.isEmpty then return Except.error VErr.empty
-  return Except.ok (featureNames voc)
+    (st : VecState) : Except VErr (List String) :=
+  -- BUG: ignore state entirely, always report notFitted
+  Except.error VErr.notFitted
 -- impl-end
 
 -- proof-start
@@ -92,7 +83,6 @@
     problem_spec_getFeatureNames st (implementation_getFeatureNames st) := by
   intro st
   unfold problem_spec_getFeatureNames implementation_getFeatureNames
-  simp only [Id.run, bind, pure]
   rcases st with ⟨learned, param⟩
   cases learned with
   | some v =>
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,6 +70,7 @@
               (¬ v.isEmpty → result = Except.ok (featureNames v))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_getFeatureNames
     (st : VecState) : Except VErr (List String) := Id.run do
@@ -84,7 +85,8 @@
       | Except.error e => return Except.error e
       | Except.ok v => voc := v
   if voc.isEmpty then return Except.error VErr.empty
-  return Except.ok (featureNames voc)
+  -- BUG: return terms in raw stored order, NOT index-sorted (skip mergeSort)
+  return Except.ok (voc.map (·.1))
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,6 +70,7 @@
               (¬ v.isEmpty → result = Except.ok (featureNames v))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_getFeatureNames
     (st : VecState) : Except VErr (List String) := Id.run do
@@ -81,7 +82,7 @@
     | none => return Except.error VErr.notFitted
     | some p =>
       match validateList p with
-      | Except.error e => return Except.error e
+      | Except.error _ => return Except.error VErr.empty  -- BUG: collapse dup->empty
       | Except.ok v => voc := v
   if voc.isEmpty then return Except.error VErr.empty
   return Except.ok (featureNames voc)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is left opaque: the vocabulary-validation step and the
-- index-ordered feature-name extraction are both modeled DEEPLY below
-- (`validateList` / `featureNames`), so they are A-references (validated ==
-- the real callees by G-AX), not consumed axioms. The `axioms` region is empty.
-- axioms-end

-- pure-start
/-- Outcome of requesting the ordered feature names of a text vectorizer.
The three error shapes are the observable failure modes:
* `notFitted` — no usable vocabulary is available at all;
* `dup`       — a supplied vocabulary lists the same term more than once;
* `empty`     — the available vocabulary has no terms. -/
inductive VErr | notFitted | dup | empty
  deriving DecidableEq, Repr

/-- The state of a vectorizer at the moment feature names are requested.
* `learned` — `some v` when a vocabulary (term ↦ integer index) is already
  available on the object (e.g. established from data during fitting); `none`
  otherwise.
* `param`   — `some p` when a vocabulary was supplied at construction time as an
  ordered list of terms; `none` otherwise. -/
structure VecState where
  learned : Option (List (String × Nat))
  param   : Option (List String)

/-- Turn a constructor-supplied ordered term list into a term↦index vocabulary.
Mirrors the standard validation of a list vocabulary: an empty list is rejected
(`empty`); a list with a repeated term is rejected (`dup`); otherwise each term
is paired with its position in the list. -/
def validateList (p : List String) : Except VErr (List (String × Nat)) :=
  if p.isEmpty then Except.error VErr.empty
  else if p.dedup.length ≠ p.length then Except.error VErr.dup
  else Except.ok p.zipIdx

/-- The ordered feature names of a vocabulary: the terms taken in increasing
order of their integer index. -/
def featureNames (voc : List (String × Nat)) : List String :=
  (voc.mergeSort (fun a b => a.2 ≤ b.2)).map (·.1)
-- pure-end

-- post-conditions-start
/-- The ordered feature names are produced whenever a vocabulary is available,
and exactly the documented error is reported otherwise.

* If a vocabulary is already available (`learned = some v`): an empty vocabulary
  reports `empty`; a non-empty one yields its index-ordered feature names.
* Otherwise, if a vocabulary was supplied at construction (`param = some p`): the
  supplied list is validated; on a validation error that error is reported, and
  on success the (non-empty) validated vocabulary yields its index-ordered
  feature names.
* Otherwise (no vocabulary at all): `notFitted` is reported. -/
def problem_spec_getFeatureNames
    (st : VecState) (result : Except VErr (List String)) : Prop :=
  match st.learned with
  | some v =>
      (v.isEmpty → result = Except.error VErr.empty) ∧
      (¬ v.isEmpty → result = Except.ok (featureNames v))
  | none =>
      match st.param with
      | none => result = Except.error VErr.notFitted
      | some p =>
          match validateList p with
          | Except.error e => result = Except.error e
          | Except.ok v =>
              (v.isEmpty → result = Except.error VErr.empty) ∧
              (¬ v.isEmpty → result = Except.ok (featureNames v))
-- post-conditions-end

-- impl-start
def implementation_getFeatureNames
    (st : VecState) : Except VErr (List String) := Id.run do
  let mut voc : List (String × Nat) := []
  match st.learned with
  | some v => voc := v
  | none =>
    match st.param with
    | none => return Except.error VErr.notFitted
    | some p =>
      match validateList p with
      | Except.error e => return Except.error e
      | Except.ok v => voc := v
  if voc.isEmpty then return Except.error VErr.empty
  return Except.ok (featureNames voc)
-- impl-end

-- proof-start
theorem correct_getFeatureNames : ∀ st : VecState,
    problem_spec_getFeatureNames st (implementation_getFeatureNames st) := by
  intro st
  unfold problem_spec_getFeatureNames implementation_getFeatureNames
  simp only [Id.run, bind, pure]
  rcases st with ⟨learned, param⟩
  cases learned with
  | some v =>
    simp only
    constructor
    · intro h; simp [h]
    · intro h; simp [h]
  | none =>
    cases param with
    | none => simp
    | some p =>
      cases hv : validateList p with
      | error e => simp [hv]
      | ok v =>
        simp only [hv]
        constructor
        · intro h; simp [h]
        · intro h; simp [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. problem_spec_getFeatureNames is a TOTALLY-PINNING functional spec: it case-splits on st.learned / st.param / validateList and in every branch (including both isEmpty / not-isEmpty sub-cases) pins result to an exact value via equality. It is quantified for-all st with NO precondition binder and NO unconstrained domain, so any impl satisfying it is extensionally equal to gold. Hence there is no verifying-but-incorrect impl and nothing to feed run_resolve (step 2 has no closing-clean-axiom patch to materialize).

PROTOCOL EXECUTED; same_spec('lean')=True for ALL 6 attacks + positive control (swebench_unified.markers.same_spec, get_backend('lean')). Verifications run concurrently as background jobs, <=4 at a time. Command per file: bash scripts/lean_verify.sh <path>.

### Results
- pos_control.lean (gold impl): EXIT 0, verifies clean; #print axioms correct_getFeatureNames => [propext, Quot.sound] (no sorryAx, no extra axioms).
- atk_1 (PREPATCH BUG: learned=none => always notFitted, param never consulted): EXIT 1, unsolved goals on none.some.* clause. Exactly the F2P-fixed behavior => prepatch reproduced.
- atk_2 (BOUNDARY: empty available vocab => notFitted instead of empty): EXIT 1, unsolved goals.
- atk_3 (CONTROL-FLOW EFFECT: param consulted FIRST, overriding an available learned vocab): EXIT 1, unsolved goals.
- atk_4 (PARTIAL-DOMAIN / degenerate: ignore state, always notFitted): EXIT 1, unsolved goals.
- atk_5 (UNGROUNDED-ORACLE ECHO: return voc.map(.1) in raw stored order, skipping the index sort that featureNames performs): EXIT 1, unsolved goals.
- atk_6 (ERROR CONFUSION: validateList error collapsed dup->empty): EXIT 1, unsolved goals.

All 6 wrong impls fail with genuine 'unsolved goals' arising from false equality goals (e.g. Except.error VErr.notFitted = Except.ok (featureNames v)), not weak tactics; the proof body is the gold proof shape and is what fails. No attack closes, so no faithful patch needed materializing/resolving.

REFINEMENT.MD AUDIT: legs 1,2 = R; leg 3 = R/A-reference; legs 4,5,6,8 = A-reference; leg 7 = I/A-reference. NO kind-3 (changed-inexpressible) leg; axioms region empty (no consumed axiom, no opaque callee). A-references validateList <-> _validate_vocabulary (list branch) and featureNames <-> [t for t,i in sorted(vocab.items(), key=itemgetter(1))] are G-AX-grounded: axiom_check.py runs the REAL repo callees (CountVectorizer._validate_vocabulary, index-ordered comprehension) over 120000+ fuzzed inputs + boundary cases, seed 10908, asserting model==real. Correspondence to the real callees holds; mapping.md type bijection consistent. G-DIFF discriminating behavior (learned=none, param=some p valid => ok(featureNames v) not notFitted) is precisely what atk_1 (=prepatch) fails on.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is left opaque: the vocabulary-validation step and the
-- index-ordered feature-name extraction are both modeled DEEPLY below
-- (`validateList` / `featureNames`), so they are A-references (validated ==
-- the real callees by G-AX), not consumed axioms. The `axioms` region is empty.
-- axioms-end

-- pure-start
/-- Outcome of requesting the ordered feature names of a text vectorizer.
The three error shapes are the observable failure modes:
* `notFitted` — no usable vocabulary is available at all;
* `dup`       — a supplied vocabulary lists the same term more than once;
* `empty`     — the available vocabulary has no terms. -/
inductive VErr | notFitted | dup | empty
  deriving DecidableEq, Repr

/-- The state of a vectorizer at the moment feature names are requested.
* `learned` — `some v` when a vocabulary (term ↦ integer index) is already
  available on the object (e.g. established from data during fitting); `none`
  otherwise.
* `param`   — `some p` when a vocabulary was supplied at construction time as an
  ordered list of terms; `none` otherwise. -/
structure VecState where
  learned : Option (List (String × Nat))
  param   : Option (List String)

/-- Turn a constructor-supplied ordered term list into a term↦index vocabulary.
Mirrors the standard validation of a list vocabulary: an empty list is rejected
(`empty`); a list with a repeated term is rejected (`dup`); otherwise each term
is paired with its position in the list. -/
def validateList (p : List String) : Except VErr (List (String × Nat)) :=
  if p.isEmpty then Except.error VErr.empty
  else if p.dedup.length ≠ p.length then Except.error VErr.dup
  else Except.ok p.zipIdx

/-- The ordered feature names of a vocabulary: the terms taken in increasing
order of their integer index. -/
def featureNames (voc : List (String × Nat)) : List String :=
  (voc.mergeSort (fun a b => a.2 ≤ b.2)).map (·.1)
-- pure-end

-- post-conditions-start
/-- The ordered feature names are produced whenever a vocabulary is available,
and exactly the documented error is reported otherwise.

* If a vocabulary is already available (`learned = some v`): an empty vocabulary
  reports `empty`; a non-empty one yields its index-ordered feature names.
* Otherwise, if a vocabulary was supplied at construction (`param = some p`): the
  supplied list is validated; on a validation error that error is reported, and
  on success the (non-empty) validated vocabulary yields its index-ordered
  feature names.
* Otherwise (no vocabulary at all): `notFitted` is reported. -/
def problem_spec_getFeatureNames
    (st : VecState) (result : Except VErr (List String)) : Prop :=
  match st.learned with
  | some v =>
      (v.isEmpty → result = Except.error VErr.empty) ∧
      (¬ v.isEmpty → result = Except.ok (featureNames v))
  | none =>
      match st.param with
      | none => result = Except.error VErr.notFitted
      | some p =>
          match validateList p with
          | Except.error e => result = Except.error e
          | Except.ok v =>
              (v.isEmpty → result = Except.error VErr.empty) ∧
              (¬ v.isEmpty → result = Except.ok (featureNames v))
-- post-conditions-end

-- impl-start
def implementation_getFeatureNames
    (st : VecState) : Except VErr (List String) := Id.run do
  let mut voc : List (String × Nat) := []
  match st.learned with
  | some v => voc := v
  | none =>
    match st.param with
    | none => return Except.error VErr.notFitted
    | some p =>
      match validateList p with
      | Except.error e => return Except.error e
      | Except.ok v => voc := v
  if voc.isEmpty then return Except.error VErr.empty
  return Except.ok (featureNames voc)
-- impl-end

-- proof-start
theorem correct_getFeatureNames : ∀ st : VecState,
    problem_spec_getFeatureNames st (implementation_getFeatureNames st) := by
  intro st
  unfold problem_spec_getFeatureNames implementation_getFeatureNames
  simp only [Id.run, bind, pure]
  rcases st with ⟨learned, param⟩
  cases learned with
  | some v =>
    simp only
    constructor
    · intro h; simp [h]
    · intro h; simp [h]
  | none =>
    cases param with
    | none => simp
    | some p =>
      cases hv : validateList p with
      | error e => simp [hv]
      | ok v =>
        simp only [hv]
        constructor
        · intro h; simp [h]
        · intro h; simp [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. problem_spec_getFeatureNames is a TOTALLY-PINNING functional spec: it case-splits on st.learned / st.param / validateList and in every branch (including both isEmpty / not-isEmpty sub-cases) pins result to an exact value via equality. It is quantified for-all st with NO precondition binder and NO unconstrained domain, so any impl satisfying it is extensionally equal to gold. Hence there is no verifying-but-incorrect impl and nothing to feed run_resolve (step 2 has no closing-clean-axiom patch to materialize).

PROTOCOL EXECUTED; same_spec('lean')=True for ALL 6 attacks + positive control (swebench_unified.markers.same_spec, get_backend('lean')). Verifications run concurrently as background jobs, <=4 at a time. Command per file: bash scripts/lean_verify.sh <path>.

### Results
- pos_control.lean (gold impl): EXIT 0, verifies clean; #print axioms correct_getFeatureNames => [propext, Quot.sound] (no sorryAx, no extra axioms).
- atk_1 (PREPATCH BUG: learned=none => always notFitted, param never consulted): EXIT 1, unsolved goals on none.some.* clause. Exactly the F2P-fixed behavior => prepatch reproduced.
- atk_2 (BOUNDARY: empty available vocab => notFitted instead of empty): EXIT 1, unsolved goals.
- atk_3 (CONTROL-FLOW EFFECT: param consulted FIRST, overriding an available learned vocab): EXIT 1, unsolved goals.
- atk_4 (PARTIAL-DOMAIN / degenerate: ignore state, always notFitted): EXIT 1, unsolved goals.
- atk_5 (UNGROUNDED-ORACLE ECHO: return voc.map(.1) in raw stored order, skipping the index sort that featureNames performs): EXIT 1, unsolved goals.
- atk_6 (ERROR CONFUSION: validateList error collapsed dup->empty): EXIT 1, unsolved goals.

All 6 wrong impls fail with genuine 'unsolved goals' arising from false equality goals (e.g. Except.error VErr.notFitted = Except.ok (featureNames v)), not weak tactics; the proof body is the gold proof shape and is what fails. No attack closes, so no faithful patch needed materializing/resolving.

REFINEMENT.MD AUDIT: legs 1,2 = R; leg 3 = R/A-reference; legs 4,5,6,8 = A-reference; leg 7 = I/A-reference. NO kind-3 (changed-inexpressible) leg; axioms region empty (no consumed axiom, no opaque callee). A-references validateList <-> _validate_vocabulary (list branch) and featureNames <-> [t for t,i in sorted(vocab.items(), key=itemgetter(1))] are G-AX-grounded: axiom_check.py runs the REAL repo callees (CountVectorizer._validate_vocabulary, index-ordered comprehension) over 120000+ fuzzed inputs + boundary cases, seed 10908, asserting model==real. Correspondence to the real callees holds; mapping.md type bijection consistent. G-DIFF discriminating behavior (learned=none, param=some p valid => ok(featureNames v) not notFitted) is precisely what atk_1 (=prepatch) fails on.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness audit of problem_spec_getFeatureNames vs the real CountVectorizer.get_feature_names (post-patch) @ base 67d06b18c6.

Checks performed:
1. Solution.lean compiles under scripts/lean_verify.sh (exit 0); #print axioms correct_getFeatureNames = [propext, Quot.sound] — no sorryAx, genuine proof.
2. swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean_tables) = True — spec region byte-identical prepatch/postpatch; fix isolated to impl region.
3. Read verbatim real callees from a base-commit sklearn checkout: _validate_vocabulary (list branch: set->sorted, non-Mapping enumerate+setdefault dup detection, empty->ValueError 'empty', else {t:i}), _check_vocabulary (NotFittedError if no vocabulary_, ValueError 'empty' if len==0), and get_feature_names ([t for t,i in sorted(items, key=itemgetter(1))]).
4. Case-by-case correspondence confirmed: learned=some v (empty->empty, else index-ordered names); learned=none/param=none -> notFitted; learned=none/param=some p -> validateList error surfaces, else names. validateList == _validate_vocabulary list branch; featureNames == sorted-by-index comprehension.
5. mergeSort stability: verified Lean (voc.mergeSort (·.2 <= ·.2)) is a STABLE sort on index ties ([("a",0),("b",0),("c",0)] -> ["a","b","c"]), matching Python's stable sorted — so tied/duplicate indices do not diverge.
6. Differential fuzz: 300k random states (verbatim real logic vs Lean model semantics, seed 10908, covering empty learned dicts, duplicate indices, unsorted learned, dup/empty param lists) -> 0 mismatches. Bundled G-AX and G-CONF harnesses independently assert the same equivalence over >=1e5 inputs.

Spec is total (forall st, no spurious precondition — matches the total real function) and asserts nothing stronger than the real repo guarantees on any realizable input. The unmodeled dict/set _validate_vocabulary branches are correctly scoped out (not reachable via get_feature_names on the modeled state space and not asserted by the deep model). No too-strong assertion and no drift found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (lean backend) does not leak the gold edit beyond the public problem_statement.

Gold edit: insert `if not hasattr(self, 'vocabulary_'): self._validate_vocabulary()` before `_check_vocabulary()` in `get_feature_names`, so that a supplied `vocabulary` parameter yields feature names instead of NotFittedError.

The problem_statement already publicly discloses the entire discriminating behavior: 'get_feature_names raise not NotFittedError when the vocabulary parameter is provided', 'get_feature_names method should not raise NotFittedError if the vocabulary parameter is provided but the vectorizer has not been trained', and even names the callee ('transform calls _validate_vocabulary method which sets the vocabulary_ instance variable'). The spec-view post-conditions region encodes exactly this behavior (param = some p branch validates and returns index-ordered names rather than notFitted) — nothing beyond the issue.

Evidence:
- Mechanical leakage.screen() passes (no hard failures): no diff markers, no patched file path/module, no reproduced gold line, no narration, no spec-view identifier or comment echoing a patched symbol. Patch-changed distinctive symbol set = {inverse_transform} (from the hunk section header only), which does not appear in the spec view.
- same_spec(Solution.lean, Solution_prepatch.lean) = True: the spec view is byte-identical pre/post-patch, so it cannot encode which branch constitutes the fix — it only asserts the total (∀ st) behavior, all of which is public.
- validateList/featureNames model UNCHANGED callees (_validate_vocabulary list branch, index-ordered comprehension) that predate the patch; the dup/empty error shapes are pre-existing behavior, not the gold edit. G-LEAK meta status = pass, relaxed_leakage unset.

Spec byte-identity (same_spec) confirmed and mechanical screen confirmed clean; semantic reconstruction adds nothing over the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
