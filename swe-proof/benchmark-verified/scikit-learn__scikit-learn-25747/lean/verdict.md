# P2 adversarial audit — scikit-learn__scikit-learn-25747

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition problem_spec_buildOutputContainer := (result = containerResult input columns index) is exact functional equality to a total deterministic function, so every closing impl is provably pointwise-equal to the gold post-patch behavior (same cols/idx/data/error-string on all three InputData categories). No closing-but-non-resolving impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,6 +104,8 @@
       let mut out := df
       if let some c := columns then
         out := { out with cols := c }
+      if let some i := index then
+        out := { out with idx := i }
       return Except.ok out
   | .ndarray values =>
       let cols := match columns with | some c => c | none => ndColumns values
@@ -119,10 +121,13 @@
   intro input columns index
   unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult
   cases input with
-  | sparse => rfl
+  | sparse => first | rfl | simp_all
   | dataframe df =>
       cases columns with
-      | none => rfl
-      | some c => rfl
-  | ndarray values => rfl
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
+  | ndarray values =>
+      cases columns with
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,7 +99,7 @@
     Except String DataFrame := Id.run do
   match input with
   | .sparse =>
-      return Except.error "Pandas output does not support sparse data."
+      return Except.ok { cols := [], idx := [], data := [] }
   | .dataframe df =>
       let mut out := df
       if let some c := columns then
@@ -119,10 +119,13 @@
   intro input columns index
   unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult
   cases input with
-  | sparse => rfl
+  | sparse => first | rfl | simp_all
   | dataframe df =>
       cases columns with
-      | none => rfl
-      | some c => rfl
-  | ndarray values => rfl
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
+  | ndarray values =>
+      cases columns with
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -107,8 +107,7 @@
       return Except.ok out
   | .ndarray values =>
       let cols := match columns with | some c => c | none => ndColumns values
-      let idx := match index with | some i => i | none => ndIndex values
-      return Except.ok { cols := cols, idx := idx, data := values }
+      return Except.ok { cols := cols, idx := ndIndex values, data := values }
 -- impl-end
 
 -- proof-start
@@ -119,10 +118,13 @@
   intro input columns index
   unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult
   cases input with
-  | sparse => rfl
+  | sparse => first | rfl | simp_all
   | dataframe df =>
       cases columns with
-      | none => rfl
-      | some c => rfl
-  | ndarray values => rfl
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
+  | ndarray values =>
+      cases columns with
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -101,10 +101,7 @@
   | .sparse =>
       return Except.error "Pandas output does not support sparse data."
   | .dataframe df =>
-      let mut out := df
-      if let some c := columns then
-        out := { out with cols := c }
-      return Except.ok out
+      return Except.ok df
   | .ndarray values =>
       let cols := match columns with | some c => c | none => ndColumns values
       let idx := match index with | some i => i | none => ndIndex values
@@ -119,10 +116,13 @@
   intro input columns index
   unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult
   cases input with
-  | sparse => rfl
+  | sparse => first | rfl | simp_all
   | dataframe df =>
       cases columns with
-      | none => rfl
-      | some c => rfl
-  | ndarray values => rfl
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
+  | ndarray values =>
+      cases columns with
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,9 +106,8 @@
         out := { out with cols := c }
       return Except.ok out
   | .ndarray values =>
-      let cols := match columns with | some c => c | none => ndColumns values
       let idx := match index with | some i => i | none => ndIndex values
-      return Except.ok { cols := cols, idx := idx, data := values }
+      return Except.ok { cols := ndColumns values, idx := idx, data := values }
 -- impl-end
 
 -- proof-start
@@ -119,10 +118,13 @@
   intro input columns index
   unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult
   cases input with
-  | sparse => rfl
+  | sparse => first | rfl | simp_all
   | dataframe df =>
       cases columns with
-      | none => rfl
-      | some c => rfl
-  | ndarray values => rfl
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
+  | ndarray values =>
+      cases columns with
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
 -- proof-end
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -99,7 +99,7 @@
     Except String DataFrame := Id.run do
   match input with
   | .sparse =>
-      return Except.error "Pandas output does not support sparse data."
+      return Except.error "sparse not supported"
   | .dataframe df =>
       let mut out := df
       if let some c := columns then
@@ -119,10 +119,13 @@
   intro input columns index
   unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult
   cases input with
-  | sparse => rfl
+  | sparse => first | rfl | simp_all
   | dataframe df =>
       cases columns with
-      | none => rfl
-      | some c => rfl
-  | ndarray values => rfl
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
+  | ndarray values =>
+      cases columns with
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
 -- proof-end
```

Attack 7 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -97,18 +97,7 @@
 def implementation_buildOutputContainer
     (input : InputData) (columns : Option (List String)) (index : Option (List Int)) :
     Except String DataFrame := Id.run do
-  match input with
-  | .sparse =>
-      return Except.error "Pandas output does not support sparse data."
-  | .dataframe df =>
-      let mut out := df
-      if let some c := columns then
-        out := { out with cols := c }
-      return Except.ok out
-  | .ndarray values =>
-      let cols := match columns with | some c => c | none => ndColumns values
-      let idx := match index with | some i => i | none => ndIndex values
-      return Except.ok { cols := cols, idx := idx, data := values }
+  return containerResult input columns index
 -- impl-end
 
 -- proof-start
@@ -119,10 +108,13 @@
   intro input columns index
   unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult
   cases input with
-  | sparse => rfl
+  | sparse => first | rfl | simp_all
   | dataframe df =>
       cases columns with
-      | none => rfl
-      | some c => rfl
-  | ndarray values => rfl
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
+  | ndarray values =>
+      cases columns with
+      | none => first | rfl | (cases index <;> simp_all) | simp_all
+      | some c => first | rfl | (cases index <;> simp_all) | simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Wrapping a transformer's output into a tabular ("DataFrame") container.

When a transformer produces output that downstream code wants as a labelled
table, the output is wrapped into a container with column labels and a row index.
The wrapping reads three things: the produced data, an optional set of column
labels, and an optional caller-supplied row index.

The wrapping rule is:

  * if the data cannot be represented as a dense table (a sparse payload), the
    request is rejected with an error;
  * if the data is ALREADY a table, it is returned as that same table — its
    column labels replaced by the supplied labels when those are given, but its
    OWN row index always kept (a caller-supplied row index does not apply
    to data that already carries its own index);
  * otherwise a fresh table is built from the data, using the supplied column
    labels when given (else positional labels) and the supplied row index when
    given (else a positional `0,1,2,…` index).

In particular, when the data is already a table, the resulting container keeps
the data's own row index regardless of any caller-supplied index — so a
transformer that re-labels its rows (e.g. by aggregating) is not silently forced
back onto the caller's index.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The wrapping
-- rule is modeled structurally over the observable parts of the inputs (the
-- data's runtime category, its own column/index/payload when it is already a
-- table, the optional supplied column labels, the optional supplied row index),
-- so no `opaque`/`axiom` callee contract is needed. (`check_pandas_support`
-- merely makes the table library available and has no effect on the produced
-- value; it is not modeled.)
-- axioms-end

-- pure-start
/-- A tabular container, projected to the three parts the wrapping observes:
`cols` (column labels, in order), `idx` (row index labels, in order), and `data`
(the cell payload, one inner list per row). -/
structure DataFrame where
  cols : List String
  idx : List Int
  data : List (List Int)
deriving DecidableEq, Repr

/-- The data to wrap, by runtime category:
* `sparse` — a sparse payload that cannot be densely tabulated;
* `dataframe df` — data that is already a table `df`;
* `ndarray values` — a plain dense array-like payload (rows of cells). -/
inductive InputData where
  | sparse
  | dataframe (df : DataFrame)
  | ndarray (values : List (List Int))
deriving Repr

/-- Positional column labels `"0","1",…` for a fresh table built from `values`
(one label per column of the first row). -/
def ndColumns (values : List (List Int)) : List String :=
  (List.range (values.headD []).length).map (fun i => toString i)

/-- Positional row index `0,1,…` for a fresh table built from `values` (one entry
per row). -/
def ndIndex (values : List (List Int)) : List Int :=
  (List.range values.length).map (fun i => (i : Int))

/-- The container produced by the wrapping rule. -/
def containerResult (input : InputData) (columns : Option (List String))
    (index : Option (List Int)) : Except String DataFrame :=
  match input with
  | .sparse => Except.error "Pandas output does not support sparse data."
  | .dataframe df =>
      -- already a table: replace columns when supplied; keep the table's own
      -- row index (the supplied index does not apply).
      let cols := match columns with | some c => c | none => df.cols
      Except.ok { df with cols := cols }
  | .ndarray values =>
      let cols := match columns with | some c => c | none => ndColumns values
      let idx := match index with | some i => i | none => ndIndex values
      Except.ok { cols := cols, idx := idx, data := values }
-- pure-end

-- post-conditions-start
/-- The produced container is exactly the one the wrapping rule selects. When the
input is already a table, its own row index is preserved (the caller-supplied
`index` is not applied); only its column labels may change. -/
def problem_spec_buildOutputContainer
    (input : InputData) (columns : Option (List String)) (index : Option (List Int))
    (result : Except String DataFrame) : Prop :=
  result = containerResult input columns index
-- post-conditions-end

-- impl-start
def implementation_buildOutputContainer
    (input : InputData) (columns : Option (List String)) (index : Option (List Int)) :
    Except String DataFrame := Id.run do
  match input with
  | .sparse =>
      return Except.error "Pandas output does not support sparse data."
  | .dataframe df =>
      let mut out := df
      if let some c := columns then
        out := { out with cols := c }
      return Except.ok out
  | .ndarray values =>
      let cols := match columns with | some c => c | none => ndColumns values
      let idx := match index with | some i => i | none => ndIndex values
      return Except.ok { cols := cols, idx := idx, data := values }
-- impl-end

-- proof-start
theorem correct_buildOutputContainer :
    ∀ (input : InputData) (columns : Option (List String)) (index : Option (List Int)),
      problem_spec_buildOutputContainer input columns index
        (implementation_buildOutputContainer input columns index) := by
  intro input columns index
  unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult
  cases input with
  | sparse => rfl
  | dataframe df =>
      cases columns with
      | none => rfl
      | some c => rfl
  | ndarray values => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & RESULTS (project root; verify cmd `bash scripts/lean_verify.sh <f>`; same_spec via python swebench_unified.markers.same_spec, all 7 attacks True; scratch dir).

Positive control: positive_control.lean (byte-copy of Solution.lean) -> lean_verify EXIT=0 (verifies, no sorry).

6 DISTINCT same-spec WRONG impls (edited impl region only; axioms/pure/pre/post byte-identical):
- atk_1 (prepatch bug, index overwrite re-added in .dataframe branch): EXIT=1. Genuine false goal `case dataframe.none.some ... val✝ = df.idx`. Reproduces the recorded prepatch_variant.
- atk_2 (boundary: sparse -> Except.ok empty frame instead of error): EXIT=1. Goal `case sparse ... ⊢ False`.
- atk_3 (partial-domain: ndarray ignores supplied index, always positional): EXIT=1. Goal `ndIndex values = val✝`.
- atk_4 (control-flow-effect: .dataframe branch never replaces columns, returns df): EXIT=1. Goal `df = { cols := c, idx := df.idx, data := df.data }`.
- atk_5 (ndarray ignores supplied columns, always positional): EXIT=1. Goal `ndColumns values = c`.
- atk_7 (boundary: sparse -> wrong error string "sparse not supported"): EXIT=1. Goal `case sparse ⊢ False`.
All six proofs used a strong tactic block (unfold; cases input; per-branch `first | rfl | (cases index <;> simp_all) | simp_all`), so the EXIT=1 failures are irreducible-false-goal failures, NOT tactic weakness.

atk_6 (ungrounded-oracle echo: `return containerResult input columns index`): lean_verify EXIT=0. `#print axioms correct_buildOutputContainer` -> 'does not depend on any axioms' (clean; verified via atk_6_ax.lean, EXIT=0). BUT atk_6 is behaviorally IDENTICAL to the gold post-patch routine (it literally returns the modeled decision), so its faithful patch IS the gold patch (patch.diff), which resolves by definition (patch_equals_gold=true). Not a counterexample; no separate resolve run needed to disprove the spec.

Because the only impl with a closing clean-axiom proof is gold-equivalent, there is NO closing-clean-axiom impl whose faithful patch would fail to resolve; the mandatory 'materialize + run resolve for every verifying wrong impl' step has no applicable wrong impl. verify => correct holds.

A-LEG AUDIT: axioms-start/axioms-end region is COMMENT-ONLY (no `opaque`/`axiom`) — there are zero A-consumed / A-reference legs to audit. The changed decision (which row index a DataFrame-input container keeps) is modeled deeply/structurally over observable input parts, per SPEC_GUIDE §3. refinement.md legs are all R (1,2,3,6) or I (4 deletion, 5), no kind-3 changed-inexpressible op; op #4 (deleted `data_to_wrap.index = index`) is faithfully mirrored by the ABSENCE of an index-write in the .dataframe branch. Correspondence to the real callee `_wrap_in_pandas_container` at base_commit holds (confirmed against mapping.md/patch.diff). R/I legs are G-CONF territory (out of scope here).

VERDICT: SOUND — >=6 distinct same-spec wrong impls attempted, none closes; the sole closing impl is gold-equivalent and resolves. Spec is exact functional equality to the post-patch model, leaving no semantic slack.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition problem_spec_buildOutputContainer := (result = containerResult input columns index) is exact functional equality to a total deterministic function, so every closing impl is provably pointwise-equal to the gold post-patch behavior (same cols/idx/data/error-string on all three InputData categories). No closing-but-non-resolving impl exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Wrapping a transformer's output into a tabular ("DataFrame") container.

When a transformer produces output that downstream code wants as a labelled
table, the output is wrapped into a container with column labels and a row index.
The wrapping reads three things: the produced data, an optional set of column
labels, and an optional caller-supplied row index.

The wrapping rule is:

  * if the data cannot be represented as a dense table (a sparse payload), the
    request is rejected with an error;
  * if the data is ALREADY a table, it is returned as that same table — its
    column labels replaced by the supplied labels when those are given, but its
    OWN row index always kept (a caller-supplied row index does not apply
    to data that already carries its own index);
  * otherwise a fresh table is built from the data, using the supplied column
    labels when given (else positional labels) and the supplied row index when
    given (else a positional `0,1,2,…` index).

In particular, when the data is already a table, the resulting container keeps
the data's own row index regardless of any caller-supplied index — so a
transformer that re-labels its rows (e.g. by aggregating) is not silently forced
back onto the caller's index.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The wrapping
-- rule is modeled structurally over the observable parts of the inputs (the
-- data's runtime category, its own column/index/payload when it is already a
-- table, the optional supplied column labels, the optional supplied row index),
-- so no `opaque`/`axiom` callee contract is needed. (`check_pandas_support`
-- merely makes the table library available and has no effect on the produced
-- value; it is not modeled.)
-- axioms-end

-- pure-start
/-- A tabular container, projected to the three parts the wrapping observes:
`cols` (column labels, in order), `idx` (row index labels, in order), and `data`
(the cell payload, one inner list per row). -/
structure DataFrame where
  cols : List String
  idx : List Int
  data : List (List Int)
deriving DecidableEq, Repr

/-- The data to wrap, by runtime category:
* `sparse` — a sparse payload that cannot be densely tabulated;
* `dataframe df` — data that is already a table `df`;
* `ndarray values` — a plain dense array-like payload (rows of cells). -/
inductive InputData where
  | sparse
  | dataframe (df : DataFrame)
  | ndarray (values : List (List Int))
deriving Repr

/-- Positional column labels `"0","1",…` for a fresh table built from `values`
(one label per column of the first row). -/
def ndColumns (values : List (List Int)) : List String :=
  (List.range (values.headD []).length).map (fun i => toString i)

/-- Positional row index `0,1,…` for a fresh table built from `values` (one entry
per row). -/
def ndIndex (values : List (List Int)) : List Int :=
  (List.range values.length).map (fun i => (i : Int))

/-- The container produced by the wrapping rule. -/
def containerResult (input : InputData) (columns : Option (List String))
    (index : Option (List Int)) : Except String DataFrame :=
  match input with
  | .sparse => Except.error "Pandas output does not support sparse data."
  | .dataframe df =>
      -- already a table: replace columns when supplied; keep the table's own
      -- row index (the supplied index does not apply).
      let cols := match columns with | some c => c | none => df.cols
      Except.ok { df with cols := cols }
  | .ndarray values =>
      let cols := match columns with | some c => c | none => ndColumns values
      let idx := match index with | some i => i | none => ndIndex values
      Except.ok { cols := cols, idx := idx, data := values }
-- pure-end

-- post-conditions-start
/-- The produced container is exactly the one the wrapping rule selects. When the
input is already a table, its own row index is preserved (the caller-supplied
`index` is not applied); only its column labels may change. -/
def problem_spec_buildOutputContainer
    (input : InputData) (columns : Option (List String)) (index : Option (List Int))
    (result : Except String DataFrame) : Prop :=
  result = containerResult input columns index
-- post-conditions-end

-- impl-start
def implementation_buildOutputContainer
    (input : InputData) (columns : Option (List String)) (index : Option (List Int)) :
    Except String DataFrame := Id.run do
  match input with
  | .sparse =>
      return Except.error "Pandas output does not support sparse data."
  | .dataframe df =>
      let mut out := df
      if let some c := columns then
        out := { out with cols := c }
      return Except.ok out
  | .ndarray values =>
      let cols := match columns with | some c => c | none => ndColumns values
      let idx := match index with | some i => i | none => ndIndex values
      return Except.ok { cols := cols, idx := idx, data := values }
-- impl-end

-- proof-start
theorem correct_buildOutputContainer :
    ∀ (input : InputData) (columns : Option (List String)) (index : Option (List Int)),
      problem_spec_buildOutputContainer input columns index
        (implementation_buildOutputContainer input columns index) := by
  intro input columns index
  unfold problem_spec_buildOutputContainer implementation_buildOutputContainer containerResult
  cases input with
  | sparse => rfl
  | dataframe df =>
      cases columns with
      | none => rfl
      | some c => rfl
  | ndarray values => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & RESULTS (project root; verify cmd `bash scripts/lean_verify.sh <f>`; same_spec via python swebench_unified.markers.same_spec, all 7 attacks True; scratch dir).

Positive control: positive_control.lean (byte-copy of Solution.lean) -> lean_verify EXIT=0 (verifies, no sorry).

6 DISTINCT same-spec WRONG impls (edited impl region only; axioms/pure/pre/post byte-identical):
- atk_1 (prepatch bug, index overwrite re-added in .dataframe branch): EXIT=1. Genuine false goal `case dataframe.none.some ... val✝ = df.idx`. Reproduces the recorded prepatch_variant.
- atk_2 (boundary: sparse -> Except.ok empty frame instead of error): EXIT=1. Goal `case sparse ... ⊢ False`.
- atk_3 (partial-domain: ndarray ignores supplied index, always positional): EXIT=1. Goal `ndIndex values = val✝`.
- atk_4 (control-flow-effect: .dataframe branch never replaces columns, returns df): EXIT=1. Goal `df = { cols := c, idx := df.idx, data := df.data }`.
- atk_5 (ndarray ignores supplied columns, always positional): EXIT=1. Goal `ndColumns values = c`.
- atk_7 (boundary: sparse -> wrong error string "sparse not supported"): EXIT=1. Goal `case sparse ⊢ False`.
All six proofs used a strong tactic block (unfold; cases input; per-branch `first | rfl | (cases index <;> simp_all) | simp_all`), so the EXIT=1 failures are irreducible-false-goal failures, NOT tactic weakness.

atk_6 (ungrounded-oracle echo: `return containerResult input columns index`): lean_verify EXIT=0. `#print axioms correct_buildOutputContainer` -> 'does not depend on any axioms' (clean; verified via atk_6_ax.lean, EXIT=0). BUT atk_6 is behaviorally IDENTICAL to the gold post-patch routine (it literally returns the modeled decision), so its faithful patch IS the gold patch (patch.diff), which resolves by definition (patch_equals_gold=true). Not a counterexample; no separate resolve run needed to disprove the spec.

Because the only impl with a closing clean-axiom proof is gold-equivalent, there is NO closing-clean-axiom impl whose faithful patch would fail to resolve; the mandatory 'materialize + run resolve for every verifying wrong impl' step has no applicable wrong impl. verify => correct holds.

A-LEG AUDIT: axioms-start/axioms-end region is COMMENT-ONLY (no `opaque`/`axiom`) — there are zero A-consumed / A-reference legs to audit. The changed decision (which row index a DataFrame-input container keeps) is modeled deeply/structurally over observable input parts, per SPEC_GUIDE §3. refinement.md legs are all R (1,2,3,6) or I (4 deletion, 5), no kind-3 changed-inexpressible op; op #4 (deleted `data_to_wrap.index = index`) is faithfully mirrored by the ABSENCE of an index-write in the .dataframe branch. Correspondence to the real callee `_wrap_in_pandas_container` at base_commit holds (confirmed against mapping.md/patch.diff). R/I legs are G-CONF territory (out of scope here).

VERDICT: SOUND — >=6 distinct same-spec wrong impls attempted, none closes; the sole closing impl is gold-equivalent and resolves. Spec is exact functional equality to the post-patch model, leaving no semantic slack.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Baseline checks all pass. (1) same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend)=True — spec region byte-identical. (2) lean_verify.sh -> exit 0 (compiles, no sorry). (3) #print axioms correct_buildOutputContainer -> 'does not depend on any axioms' (no sorryAx; genuinely closed). (4) Real base_commit source (git show 2c867b8f...:sklearn/utils/_set_output.py) matches mapping.md exactly; gold patch deletes precisely the two lines `if index is not None: data_to_wrap.index = index`.

Faithfulness vs post-patch _wrap_in_pandas_container over the modeled domain: (a) .sparse -> ValueError with identical string, unchanged branch, matches. (b) .dataframe df -> columns optionally replaced, df.idx ALWAYS kept regardless of supplied index — this IS the fix, and matches the changed PASS_TO_PASS assertion (new_df.index == X_df.index) and the F2P test_set_output_pandas_keep_index. Agreement on all inputs. (c) .ndarray values -> fresh frame with supplied-or-positional cols/idx (ndColumns/ndIndex = range), matching pd.DataFrame(data, index=index, columns=columns) defaults; unchanged branch.

Candidate divergence examined and DISMISSED (not a defect): a DataFrame input with a length-mismatched supplied columns (e.g. df has 3 cols, columns=some["x"]) — real pandas `data_to_wrap.columns = columns` RAISES ValueError while the model returns ok with the mismatched labels; likewise a length-mismatched index/columns to pd.DataFrame(...) in the ndarray branch raises. This is NOT a faithfulness break because: (i) it lives entirely in the UNCHANGED branches, orthogonal to the index fix the spec concerns; (ii) it is excluded by the documented matching-length type bijection (mapping.md §type bijection) which holds at every real call site (columns from get_feature_names_out() has length = n_features; index matches the data's rows); (iii) no FAIL_TO_PASS/PASS_TO_PASS test exercises those branches as a raise for the modeled decision (column_errors test only checks the callable-exception->None fallback, which is folded into the resolved Option). The spec does not claim those branches never raise; it pins the value-decision the patch changes, and on that decision it agrees with the real callee on every input. No drift on the modeled behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: delete `if index is not None: data_to_wrap.index = index` in the DataFrame branch of `_wrap_in_pandas_container` so a DataFrame input keeps its own row index. Verified same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers with LeanBackend — spec regions byte-identical, impl/proof correctly elided in the consumer spec view. The public problem_statement (checked programmatically, hints_text excluded) already localizes the edit MORE explicitly than the spec view: it names the file `sklearn/utils/_set_output.py` and function `_wrap_in_pandas_container`, and its traceback contains the literal deleted lines `if index is not None:` and `data_to_wrap.index = index` with `---> 59` pointing at the index assignment inside the DataFrame branch, plus 'Expected Results: No error is thrown' establishing the correct behavior (don't overwrite an aggregating transformer's own index). The spec-view prose (docstring + `containerResult`: 'its OWN row index always kept; a caller-supplied row index does not apply') describes the desired post-condition — that is the spec's legitimate job and reveals nothing beyond the public statement. The signatures (InputData/DataFrame/containerResult) expose only the data model, not the edit locus. No edit-localizing information exists in the spec view that is absent from the public problem_statement. Concurring with verdict.md Role 4.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
