# P2 adversarial audit — django__django-12663

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
   Id.run do
     if selections.length = 1 then
       let select := selections.headI
-      return some (baseOrDeclared select)
+      return some select.declared
     else if annotations.length = 1 then
       return some annotations.headI.outputField
     return none
@@ -93,6 +93,10 @@
   intro selections annotations
   unfold problem_spec_outputType implementation_outputType
   by_cases h1 : selections.length = 1
-  · simp only [Id.run, h1, if_true]; rfl
-  · by_cases h2 : annotations.length = 1 <;> simp only [Id.run, h1, h2, if_true, if_false] <;> rfl
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
 def implementation_outputType
     (selections : List Selection) (annotations : List AnnExpr) : Option FieldId :=
   Id.run do
-    if selections.length = 1 then
+    if selections.length ≥ 1 then
       let select := selections.headI
       return some (baseOrDeclared select)
     else if annotations.length = 1 then
@@ -93,6 +93,10 @@
   intro selections annotations
   unfold problem_spec_outputType implementation_outputType
   by_cases h1 : selections.length = 1
-  · simp only [Id.run, h1, if_true]; rfl
-  · by_cases h2 : annotations.length = 1 <;> simp only [Id.run, h1, h2, if_true, if_false] <;> rfl
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,11 +77,11 @@
 def implementation_outputType
     (selections : List Selection) (annotations : List AnnExpr) : Option FieldId :=
   Id.run do
-    if selections.length = 1 then
+    if annotations.length = 1 then
+      return some annotations.headI.outputField
+    else if selections.length = 1 then
       let select := selections.headI
       return some (baseOrDeclared select)
-    else if annotations.length = 1 then
-      return some annotations.headI.outputField
     return none
 -- impl-end
 
@@ -93,6 +93,10 @@
   intro selections annotations
   unfold problem_spec_outputType implementation_outputType
   by_cases h1 : selections.length = 1
-  · simp only [Id.run, h1, if_true]; rfl
-  · by_cases h2 : annotations.length = 1 <;> simp only [Id.run, h1, h2, if_true, if_false] <;> rfl
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
   Id.run do
     if selections.length = 1 then
       let select := selections.headI
-      return some (baseOrDeclared select)
+      return some (select.base.getD 0)
     else if annotations.length = 1 then
       return some annotations.headI.outputField
     return none
@@ -93,6 +93,10 @@
   intro selections annotations
   unfold problem_spec_outputType implementation_outputType
   by_cases h1 : selections.length = 1
-  · simp only [Id.run, h1, if_true]; rfl
-  · by_cases h2 : annotations.length = 1 <;> simp only [Id.run, h1, h2, if_true, if_false] <;> rfl
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
       let select := selections.headI
       return some (baseOrDeclared select)
     else if annotations.length = 1 then
-      return some annotations.headI.outputField
+      return none
     return none
 -- impl-end
 
@@ -93,6 +93,10 @@
   intro selections annotations
   unfold problem_spec_outputType implementation_outputType
   by_cases h1 : selections.length = 1
-  · simp only [Id.run, h1, if_true]; rfl
-  · by_cases h2 : annotations.length = 1 <;> simp only [Id.run, h1, h2, if_true, if_false] <;> rfl
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,11 +77,6 @@
 def implementation_outputType
     (selections : List Selection) (annotations : List AnnExpr) : Option FieldId :=
   Id.run do
-    if selections.length = 1 then
-      let select := selections.headI
-      return some (baseOrDeclared select)
-    else if annotations.length = 1 then
-      return some annotations.headI.outputField
     return none
 -- impl-end
 
@@ -93,6 +88,10 @@
   intro selections annotations
   unfold problem_spec_outputType implementation_outputType
   by_cases h1 : selections.length = 1
-  · simp only [Id.run, h1, if_true]; rfl
-  · by_cases h2 : annotations.length = 1 <;> simp only [Id.run, h1, h2, if_true, if_false] <;> rfl
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
       let select := selections.headI
       return some (baseOrDeclared select)
     else if annotations.length = 1 then
-      return some annotations.headI.outputField
+      return some (annotations.headI.outputField + 1)
     return none
 -- impl-end
 
@@ -93,6 +93,10 @@
   intro selections annotations
   unfold problem_spec_outputType implementation_outputType
   by_cases h1 : selections.length = 1
-  · simp only [Id.run, h1, if_true]; rfl
-  · by_cases h2 : annotations.length = 1 <;> simp only [Id.run, h1, h2, if_true, if_false] <;> rfl
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
+  · by_cases h2 : annotations.length = 1 <;>
+      simp only [Id.run, h1, h2, if_true, if_false] <;>
+      first | rfl | simp_all | omega
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the type descriptor that represents a query's single output column.

A query produces a list of selected columns and a list of selected annotations.
When asked for the type descriptor of its overall output, the query reports:

  * if it selects EXACTLY ONE column, that column's type descriptor — preferring
    the column's underlying referenced attribute when it has one, and otherwise
    falling back to the column's declared output type;
  * else if it selects EXACTLY ONE annotation, that annotation's declared output
    type;
  * otherwise, nothing (the output type is undetermined).

The distinction in the single-column case matters because a column's underlying
referenced attribute and its declared output type can be different descriptors.
Reporting the underlying referenced attribute (when present) is what lets a
downstream consumer coerce a related-object value against the right attribute,
rather than mis-coercing it against a plain declared type.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- single-column choice (underlying referenced attribute, else declared output
-- type) is modeled structurally over the data carried by each selection; the
-- annotation's output type is carried directly as an observable field. So no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A field / column type descriptor. Only its identity is observed here, so an
injective `Nat` encoding of the distinct descriptor objects suffices. -/
abbrev FieldId := Nat

/-- One selected column, restricted to its two observable candidate type
descriptors:
* `base` — the column's underlying referenced attribute, when it has one;
* `declared` — the column's declared output type (always present). -/
structure Selection where
  base : Option FieldId
  declared : FieldId
deriving DecidableEq, Inhabited

/-- One selected annotation, restricted to the observable here: its declared
output type. -/
structure AnnExpr where
  outputField : FieldId
deriving DecidableEq, Inhabited

/-- The type descriptor reported for a single selected column: the underlying
referenced attribute when present, otherwise the declared output type. -/
def baseOrDeclared (s : Selection) : FieldId :=
  s.base.getD s.declared
-- pure-end

-- post-conditions-start
/-- The reported output type descriptor. With exactly one selected column the
result is that column's `baseOrDeclared` descriptor; otherwise with exactly one
selected annotation it is that annotation's output type; otherwise it is `none`.
Every branch is pinned to the inputs, and the unselected lists never contribute
to the chosen descriptor in the branch that fires. -/
def problem_spec_outputType
    (selections : List Selection) (annotations : List AnnExpr)
    (result : Option FieldId) : Prop :=
  result =
    (if selections.length = 1 then
        some (baseOrDeclared selections.headI)
      else if annotations.length = 1 then
        some annotations.headI.outputField
      else
        none)
-- post-conditions-end

-- impl-start
def implementation_outputType
    (selections : List Selection) (annotations : List AnnExpr) : Option FieldId :=
  Id.run do
    if selections.length = 1 then
      let select := selections.headI
      return some (baseOrDeclared select)
    else if annotations.length = 1 then
      return some annotations.headI.outputField
    return none
-- impl-end

-- proof-start
theorem correct_outputType :
    ∀ (selections : List Selection) (annotations : List AnnExpr),
      problem_spec_outputType selections annotations
        (implementation_outputType selections annotations) := by
  intro selections annotations
  unfold problem_spec_outputType implementation_outputType
  by_cases h1 : selections.length = 1
  · simp only [Id.run, h1, if_true]; rfl
  · by_cases h2 : annotations.length = 1 <;> simp only [Id.run, h1, h2, if_true, if_false] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle django__django-12663/lean models Query.output_field. The postcondition problem_spec_outputType is a TOTAL FUNCTIONAL EQUALITY: result = (if selections.length=1 then some (baseOrDeclared selections.headI) else if annotations.length=1 then some annotations.headI.outputField else none). Every output component is pinned; single-column branch pinned to baseOrDeclared = base.getD declared (prefers base). By Lean soundness (consistency), any impl differing from f on any input makes correct_outputType FALSE and unprovable without sorry, so NO same-spec wrong impl can close with clean axioms => no faithful patch exists to run through the harness (resolve step vacuous by construction).

PROTOCOL EXECUTED (all, verified via scripts/lean_verify.sh <file>; project root). same_spec=True confirmed for ALL attacks + positive_control (swebench_unified.markers.same_spec, lean backend). Only the impl region edited; axioms/pure/pre/post byte-identical. Verifications launched concurrently as background jobs (batches of 4).

Positive control (gold copy): exit 0 (verifies, no sorry). #print axioms correct_outputType => [propext] only (clean, no sorryAx).

7 DISTINCT same-spec wrong impls, all FAIL to compile (exit 1) — no closing clean-axiom proof, so none required a materialized/resolved patch:
- atk_1 (prepatch bug / partial-domain single-col): single-col returns some select.declared (ignores base). exit 1. PREPATCH REPRODUCED — this is the base_commit buggy behavior; its gold proof cannot discharge the frozen spec.
- atk_2 (boundary): guard selections.length >= 1 instead of = 1. exit 1 — unsolved goals, provably-mismatched if-branches.
- atk_3 (control-flow): branch order swapped (annotation checked before selection). exit 1.
- atk_4 (partial-domain / wrong fallback): single-col returns some (select.base.getD 0), dropping the declared fallback. exit 1.
- atk_5 (control-flow-effect): annotation branch returns none instead of outputField. exit 1 — goal reduces to False.
- atk_6 (control-flow-effect collapse): always return none. exit 1 — goals reduce to False.
- atk_7 (ungrounded-oracle echo / off-by-one): annotation branch returns some (outputField+1). exit 1.
All used a strong generic closing tactic (by_cases split + simp + first|rfl|simp_all|omega); errors are genuine semantic rejections (goals to False / branch mismatch), not tactic weakness.

REFINEMENT.MD AUDIT: 6 legs, all R (#1,#2,#5,#6) or I (#3,#4). Axioms region is EMPTY — grep of Solution.lean finds NO axiom/opaque/sorry/admit/native_decide declarations (only the explanatory comment). No A-consumed / A-reference legs exist, so no deep-model callee correspondence to falsify (the R/I legs are G-CONF's job, mechanically covered). The sole deep-model leg (#4) maps baseOrDeclared = base.getD declared <-> getattr(select,'target',None) or select.field; truthiness note (real model-field objects always truthy => Python or reduces to Option.getD) is valid and conformance_check.py exercises the genuine `or`. No kind-3 leg. Correspondence holds.

Conclusion: verify => correct holds here; the total functional-equality postcondition leaves no slack. SOUND after 7 attacks (>=5 required), none breaks it.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the type descriptor that represents a query's single output column.

A query produces a list of selected columns and a list of selected annotations.
When asked for the type descriptor of its overall output, the query reports:

  * if it selects EXACTLY ONE column, that column's type descriptor — preferring
    the column's underlying referenced attribute when it has one, and otherwise
    falling back to the column's declared output type;
  * else if it selects EXACTLY ONE annotation, that annotation's declared output
    type;
  * otherwise, nothing (the output type is undetermined).

The distinction in the single-column case matters because a column's underlying
referenced attribute and its declared output type can be different descriptors.
Reporting the underlying referenced attribute (when present) is what lets a
downstream consumer coerce a related-object value against the right attribute,
rather than mis-coercing it against a plain declared type.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- single-column choice (underlying referenced attribute, else declared output
-- type) is modeled structurally over the data carried by each selection; the
-- annotation's output type is carried directly as an observable field. So no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A field / column type descriptor. Only its identity is observed here, so an
injective `Nat` encoding of the distinct descriptor objects suffices. -/
abbrev FieldId := Nat

/-- One selected column, restricted to its two observable candidate type
descriptors:
* `base` — the column's underlying referenced attribute, when it has one;
* `declared` — the column's declared output type (always present). -/
structure Selection where
  base : Option FieldId
  declared : FieldId
deriving DecidableEq, Inhabited

/-- One selected annotation, restricted to the observable here: its declared
output type. -/
structure AnnExpr where
  outputField : FieldId
deriving DecidableEq, Inhabited

/-- The type descriptor reported for a single selected column: the underlying
referenced attribute when present, otherwise the declared output type. -/
def baseOrDeclared (s : Selection) : FieldId :=
  s.base.getD s.declared
-- pure-end

-- post-conditions-start
/-- The reported output type descriptor. With exactly one selected column the
result is that column's `baseOrDeclared` descriptor; otherwise with exactly one
selected annotation it is that annotation's output type; otherwise it is `none`.
Every branch is pinned to the inputs, and the unselected lists never contribute
to the chosen descriptor in the branch that fires. -/
def problem_spec_outputType
    (selections : List Selection) (annotations : List AnnExpr)
    (result : Option FieldId) : Prop :=
  result =
    (if selections.length = 1 then
        some (baseOrDeclared selections.headI)
      else if annotations.length = 1 then
        some annotations.headI.outputField
      else
        none)
-- post-conditions-end

-- impl-start
def implementation_outputType
    (selections : List Selection) (annotations : List AnnExpr) : Option FieldId :=
  Id.run do
    if selections.length = 1 then
      let select := selections.headI
      return some (baseOrDeclared select)
    else if annotations.length = 1 then
      return some annotations.headI.outputField
    return none
-- impl-end

-- proof-start
theorem correct_outputType :
    ∀ (selections : List Selection) (annotations : List AnnExpr),
      problem_spec_outputType selections annotations
        (implementation_outputType selections annotations) := by
  intro selections annotations
  unfold problem_spec_outputType implementation_outputType
  by_cases h1 : selections.length = 1
  · simp only [Id.run, h1, if_true]; rfl
  · by_cases h2 : annotations.length = 1 <;> simp only [Id.run, h1, h2, if_true, if_false] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle django__django-12663/lean models Query.output_field. The postcondition problem_spec_outputType is a TOTAL FUNCTIONAL EQUALITY: result = (if selections.length=1 then some (baseOrDeclared selections.headI) else if annotations.length=1 then some annotations.headI.outputField else none). Every output component is pinned; single-column branch pinned to baseOrDeclared = base.getD declared (prefers base). By Lean soundness (consistency), any impl differing from f on any input makes correct_outputType FALSE and unprovable without sorry, so NO same-spec wrong impl can close with clean axioms => no faithful patch exists to run through the harness (resolve step vacuous by construction).

PROTOCOL EXECUTED (all, verified via scripts/lean_verify.sh <file>; project root). same_spec=True confirmed for ALL attacks + positive_control (swebench_unified.markers.same_spec, lean backend). Only the impl region edited; axioms/pure/pre/post byte-identical. Verifications launched concurrently as background jobs (batches of 4).

Positive control (gold copy): exit 0 (verifies, no sorry). #print axioms correct_outputType => [propext] only (clean, no sorryAx).

7 DISTINCT same-spec wrong impls, all FAIL to compile (exit 1) — no closing clean-axiom proof, so none required a materialized/resolved patch:
- atk_1 (prepatch bug / partial-domain single-col): single-col returns some select.declared (ignores base). exit 1. PREPATCH REPRODUCED — this is the base_commit buggy behavior; its gold proof cannot discharge the frozen spec.
- atk_2 (boundary): guard selections.length >= 1 instead of = 1. exit 1 — unsolved goals, provably-mismatched if-branches.
- atk_3 (control-flow): branch order swapped (annotation checked before selection). exit 1.
- atk_4 (partial-domain / wrong fallback): single-col returns some (select.base.getD 0), dropping the declared fallback. exit 1.
- atk_5 (control-flow-effect): annotation branch returns none instead of outputField. exit 1 — goal reduces to False.
- atk_6 (control-flow-effect collapse): always return none. exit 1 — goals reduce to False.
- atk_7 (ungrounded-oracle echo / off-by-one): annotation branch returns some (outputField+1). exit 1.
All used a strong generic closing tactic (by_cases split + simp + first|rfl|simp_all|omega); errors are genuine semantic rejections (goals to False / branch mismatch), not tactic weakness.

REFINEMENT.MD AUDIT: 6 legs, all R (#1,#2,#5,#6) or I (#3,#4). Axioms region is EMPTY — grep of Solution.lean finds NO axiom/opaque/sorry/admit/native_decide declarations (only the explanatory comment). No A-consumed / A-reference legs exist, so no deep-model callee correspondence to falsify (the R/I legs are G-CONF's job, mechanically covered). The sole deep-model leg (#4) maps baseOrDeclared = base.getD declared <-> getattr(select,'target',None) or select.field; truthiness note (real model-field objects always truthy => Python or reduces to Option.getD) is valid and conformance_check.py exercises the genuine `or`. No kind-3 leg. Correspondence holds.

Conclusion: verify => correct holds here; the total functional-equality postcondition leaves no slack. SOUND after 7 attacks (>=5 required), none breaks it.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on the spec `problem_spec_outputType` modeling the POST-PATCH `Query.output_field` property (django/db/models/sql/query.py:236, `getattr(select,'target',None) or select.field`). No divergence found; spec is faithful (not too strong).

Evidence:
1. Solution.lean compiles (lean_verify.sh exit 0); `#print axioms correct_outputType` = [propext] only — no sorryAx, proof is genuine.
2. same_spec(Solution, Solution_prepatch, lean backend) = True (spec region byte-identical; only the impl line differs: post `some (baseOrDeclared select)` vs pre `some select.declared`).
3. Branch-by-branch match against the real repo (base 2c7846d992, patch applied): len(select)==1 guard ↔ `selections.length = 1`; `getattr(select,'target',None) or select.field` ↔ `some (base.getD declared)`; `elif len(annotation_select)==1` ↔ `else if annotations.length = 1` returning `.output_field`; implicit `None` ↔ `none`.
4. The one abstraction gap — Python `or` (falls back on ANY falsy) vs Lean `Option.getD` (falls back only on none) — is sound: Django's `Field` class defines no `__bool__`/`__len__` (only `__eq__`), so a present `target` (a Field object) is always truthy; thus `or` ≡ `getD`. Fuzzer draws field ids ≥1 preserving this, and the oracle applies the genuine Python `or`.
5. `select.field` is a property returning `select.output_field` (expressions.py:260) — matches mapping's `declared`.
6. conformance_check.py: 120,010 inputs (10 hand-picked edges incl. target present-and-different, present-and-equal, absent, present-but-None; annotation branch; empty; multi-element) + LCG-seed-12663 fuzz, 0 disagreements against an in-process replica of the patched property.

The only real-repo behavior outside the modeled value domain is that `output_field`/`select.field` may RAISE FieldError when the expression's output type is unresolvable; it never returns a falsy value or None on the single-column path. This exception path is legitimately abstracted away (out of the return-value model). Every value-returning path matches exactly and the spec imposes no constraint the real function fails to satisfy. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (problem_spec + docstrings + signatures; impl/proof elided) is clean. Mechanical leakage.screen -> hard_failures=[] (no diff markers, no gold line reproduced, no patched file path, no repo-symbol collision, no narration keyword). same_spec(Solution, Solution_prepatch)=True (frozen spec byte-identical). Direct scan of the rendered spec view confirms absence of all repo-specific edit vocabulary: no 'query.py'/'.py', 'target', 'Col.', 'getattr', 'annotation_select', 'select.field', 'select[0]', and not even 'output_field'. Identifiers are fully abstract (FieldId, Selection, base, declared, AnnExpr, outputField, baseOrDeclared). The only substantive item is the behavioral prose 'preferring the underlying referenced attribute when present, else the declared output type' — this is the gold discriminator (target vs field), and that specific mechanism is disclosed in hints_text (Col.target/Col.field) but NOT in problem_statement. This is nonetheless NOT leakage: (1) a faithful spec of any fix must encode the corrected decision rule — the postcondition intrinsically determines correct behavior; that is spec content, not edit-localization; (2) the leakage standard targets edit localization / gold reproduction / paths / repo symbols / narration judged against problem_statement — none present; (3) the spec view does not echo hints_text terms (target, Col.target, Col.field), it uses independent generic abstractions, so a solver still must locate output_field in query.py and translate 'prefer base else declared' into the concrete getattr(...)or... edit; (4) the modeled function output_field, the token 'field', and 'query.py' all already appear in the PUBLIC problem_statement traceback. No hints-only vocabulary leaks into the spec view. Recorded verdict.md role-4 NO-LEAKAGE confirmed. No RELAXED_LEAKAGE.md present and none needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
