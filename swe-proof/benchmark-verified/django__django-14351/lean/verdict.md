# P2 adversarial audit — django__django-14351

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
@@ -88,6 +88,7 @@
       result.2 = some (if q.explicitlySelected then q else normalizeRhs q)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_membershipGroupColumns
     (lhsCols : List Col) (rhs : Option RhsSubquery) :
@@ -96,17 +97,10 @@
   match rhs with
   | none =>
       return (cols, none)
-  | some q0 =>
-      let mut q := q0
-      if !q.explicitlySelected then
-        -- discard the implicit selection …
-        q := { q with selected := [], explicitlySelected := false }
-        -- … then select only the identity column.
-        q := { q with selected := [q.identityColumn], explicitlySelected := true }
+  | some q =>
       cols := cols ++ q.groupKeys
       return (cols, some q)
 -- impl-end
-
 -- proof-start
 theorem correct_membershipGroupColumns :
     ∀ (lhsCols : List Col) (rhs : Option RhsSubquery),
@@ -115,8 +109,9 @@
   intro lhsCols rhs
   unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns
   cases rhs with
-  | none => exact ⟨rfl, rfl⟩
+  | none => first | exact ⟨rfl, rfl⟩ | (simp_all)
   | some q =>
     simp only [Id.run, normalizeRhs]
-    by_cases h : q.explicitlySelected <;> simp only [h] <;> exact ⟨rfl, rfl⟩
+    by_cases h : q.explicitlySelected <;> simp only [h] <;>
+      first | exact ⟨rfl, rfl⟩ | (simp_all [normalizeRhs]) | rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,6 +88,7 @@
       result.2 = some (if q.explicitlySelected then q else normalizeRhs q)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_membershipGroupColumns
     (lhsCols : List Col) (rhs : Option RhsSubquery) :
@@ -98,15 +99,11 @@
       return (cols, none)
   | some q0 =>
       let mut q := q0
-      if !q.explicitlySelected then
-        -- discard the implicit selection …
-        q := { q with selected := [], explicitlySelected := false }
-        -- … then select only the identity column.
+      if q.explicitlySelected then
         q := { q with selected := [q.identityColumn], explicitlySelected := true }
       cols := cols ++ q.groupKeys
       return (cols, some q)
 -- impl-end
-
 -- proof-start
 theorem correct_membershipGroupColumns :
     ∀ (lhsCols : List Col) (rhs : Option RhsSubquery),
@@ -115,8 +112,9 @@
   intro lhsCols rhs
   unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns
   cases rhs with
-  | none => exact ⟨rfl, rfl⟩
+  | none => first | exact ⟨rfl, rfl⟩ | (simp_all)
   | some q =>
     simp only [Id.run, normalizeRhs]
-    by_cases h : q.explicitlySelected <;> simp only [h] <;> exact ⟨rfl, rfl⟩
+    by_cases h : q.explicitlySelected <;> simp only [h] <;>
+      first | exact ⟨rfl, rfl⟩ | (simp_all [normalizeRhs]) | rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,6 +88,7 @@
       result.2 = some (if q.explicitlySelected then q else normalizeRhs q)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_membershipGroupColumns
     (lhsCols : List Col) (rhs : Option RhsSubquery) :
@@ -98,15 +99,10 @@
       return (cols, none)
   | some q0 =>
       let mut q := q0
-      if !q.explicitlySelected then
-        -- discard the implicit selection …
-        q := { q with selected := [], explicitlySelected := false }
-        -- … then select only the identity column.
-        q := { q with selected := [q.identityColumn], explicitlySelected := true }
+      q := { q with selected := [q.identityColumn], explicitlySelected := true }
       cols := cols ++ q.groupKeys
       return (cols, some q)
 -- impl-end
-
 -- proof-start
 theorem correct_membershipGroupColumns :
     ∀ (lhsCols : List Col) (rhs : Option RhsSubquery),
@@ -115,8 +111,9 @@
   intro lhsCols rhs
   unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns
   cases rhs with
-  | none => exact ⟨rfl, rfl⟩
+  | none => first | exact ⟨rfl, rfl⟩ | (simp_all)
   | some q =>
     simp only [Id.run, normalizeRhs]
-    by_cases h : q.explicitlySelected <;> simp only [h] <;> exact ⟨rfl, rfl⟩
+    by_cases h : q.explicitlySelected <;> simp only [h] <;>
+      first | exact ⟨rfl, rfl⟩ | (simp_all [normalizeRhs]) | rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,6 +88,7 @@
       result.2 = some (if q.explicitlySelected then q else normalizeRhs q)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_membershipGroupColumns
     (lhsCols : List Col) (rhs : Option RhsSubquery) :
@@ -99,14 +100,10 @@
   | some q0 =>
       let mut q := q0
       if !q.explicitlySelected then
-        -- discard the implicit selection …
-        q := { q with selected := [], explicitlySelected := false }
-        -- … then select only the identity column.
-        q := { q with selected := [q.identityColumn], explicitlySelected := true }
+        q := { q with selected := [], explicitlySelected := true }
       cols := cols ++ q.groupKeys
       return (cols, some q)
 -- impl-end
-
 -- proof-start
 theorem correct_membershipGroupColumns :
     ∀ (lhsCols : List Col) (rhs : Option RhsSubquery),
@@ -115,8 +112,9 @@
   intro lhsCols rhs
   unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns
   cases rhs with
-  | none => exact ⟨rfl, rfl⟩
+  | none => first | exact ⟨rfl, rfl⟩ | (simp_all)
   | some q =>
     simp only [Id.run, normalizeRhs]
-    by_cases h : q.explicitlySelected <;> simp only [h] <;> exact ⟨rfl, rfl⟩
+    by_cases h : q.explicitlySelected <;> simp only [h] <;>
+      first | exact ⟨rfl, rfl⟩ | (simp_all [normalizeRhs]) | rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,6 +88,7 @@
       result.2 = some (if q.explicitlySelected then q else normalizeRhs q)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_membershipGroupColumns
     (lhsCols : List Col) (rhs : Option RhsSubquery) :
@@ -99,14 +100,10 @@
   | some q0 =>
       let mut q := q0
       if !q.explicitlySelected then
-        -- discard the implicit selection …
-        q := { q with selected := [], explicitlySelected := false }
-        -- … then select only the identity column.
         q := { q with selected := [q.identityColumn], explicitlySelected := true }
-      cols := cols ++ q.groupKeys
+      cols := q.groupKeys ++ cols
       return (cols, some q)
 -- impl-end
-
 -- proof-start
 theorem correct_membershipGroupColumns :
     ∀ (lhsCols : List Col) (rhs : Option RhsSubquery),
@@ -115,8 +112,9 @@
   intro lhsCols rhs
   unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns
   cases rhs with
-  | none => exact ⟨rfl, rfl⟩
+  | none => first | exact ⟨rfl, rfl⟩ | (simp_all)
   | some q =>
     simp only [Id.run, normalizeRhs]
-    by_cases h : q.explicitlySelected <;> simp only [h] <;> exact ⟨rfl, rfl⟩
+    by_cases h : q.explicitlySelected <;> simp only [h] <;>
+      first | exact ⟨rfl, rfl⟩ | (simp_all [normalizeRhs]) | rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,6 +88,7 @@
       result.2 = some (if q.explicitlySelected then q else normalizeRhs q)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_membershipGroupColumns
     (lhsCols : List Col) (rhs : Option RhsSubquery) :
@@ -99,14 +100,9 @@
   | some q0 =>
       let mut q := q0
       if !q.explicitlySelected then
-        -- discard the implicit selection …
-        q := { q with selected := [], explicitlySelected := false }
-        -- … then select only the identity column.
         q := { q with selected := [q.identityColumn], explicitlySelected := true }
-      cols := cols ++ q.groupKeys
       return (cols, some q)
 -- impl-end
-
 -- proof-start
 theorem correct_membershipGroupColumns :
     ∀ (lhsCols : List Col) (rhs : Option RhsSubquery),
@@ -115,8 +111,9 @@
   intro lhsCols rhs
   unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns
   cases rhs with
-  | none => exact ⟨rfl, rfl⟩
+  | none => first | exact ⟨rfl, rfl⟩ | (simp_all)
   | some q =>
     simp only [Id.run, normalizeRhs]
-    by_cases h : q.explicitlySelected <;> simp only [h] <;> exact ⟨rfl, rfl⟩
+    by_cases h : q.explicitlySelected <;> simp only [h] <;>
+      first | exact ⟨rfl, rfl⟩ | (simp_all [normalizeRhs]) | rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Collecting the grouping-key columns contributed by a *membership* condition — a
condition of the form "this column's value is among the results of a nested
query".

A grouping key is built from two parts: the columns contributed by the
condition's left-hand side, followed by the columns contributed by its
right-hand side when that right-hand side is itself a nested query. A nested
query carries a notion of *which columns it selects*: either an explicit list of
selected columns chosen by the caller, or — when no explicit selection was made
— the full set of default columns of its underlying model.

A nested query used purely as the right-hand side of a membership condition must
behave as a single-valued expression: when contributing to a grouping key it has
to be reduced to exactly one identity column. The desired behavior is therefore:

* the left-hand side columns are always collected verbatim, in order, first;
* if the right-hand side is a nested query that has NO explicit selection, it is
  first normalized so that it selects only its single identity column, and only
  then does it contribute its grouping columns;
* if the right-hand side already has an explicit selection, it is left untouched;
* if the right-hand side is not a nested query, nothing is appended and no
  normalization occurs.

The grouping columns a nested query contributes are determined by the query as a
whole and do not themselves change under this normalization; what changes — and
what makes the membership condition emit a single-valued nested query — is the
normalized selection state the query is left in. The behavior is stated as an
input→output relation over both the collected column list and the resulting
nested-query state; the implementation and proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Both operations on a
-- nested query — discarding an implicit selection and then selecting only its
-- identity column — are modeled DEEPLY as field updates on the query-state
-- structure below, so there is no consumed axiom.
-- axioms-end

-- pure-start
/-- A column expression, modeled by its identity. Only equality/identity of
columns matters for grouping-key collection, so a `Nat` tag suffices. -/
abbrev Col := Nat

/-- The touched state of a nested query used as the right-hand side of a
membership condition. Only the fields the behavior reads or writes are modeled. -/
structure RhsSubquery where
  /-- Whether the query has an explicit caller-chosen column selection. -/
  explicitlySelected : Bool
  /-- The explicitly-selected columns (meaningful when `explicitlySelected`). -/
  selected : List Col
  /-- The model's default columns (what the query would emit with no explicit
  selection). -/
  defaultColumns : List Col
  /-- The grouping columns this query contributes; determined by the query as a
  whole and invariant under selection normalization. -/
  groupKeys : List Col
  /-- The single identity column the query is reduced to when normalized. -/
  identityColumn : Col
  deriving DecidableEq, Repr

/-- Normalize a nested query that lacks an explicit selection: discard any
implicit selection, then select only its identity column. -/
def normalizeRhs (q : RhsSubquery) : RhsSubquery :=
  { q with selected := [q.identityColumn], explicitlySelected := true }
-- pure-end

-- post-conditions-start
/-- The collected grouping key (`result.1`) and the resulting right-hand-side
state (`result.2`):

* left-hand-side columns are always collected first, in order;
* when the rhs is a nested query, its grouping columns are appended;
* a nested query with no explicit selection is normalized to its identity
  column before it contributes (and that normalized state is the result state);
* a nested query that already has an explicit selection is left untouched;
* a non-query rhs contributes nothing and leaves no rhs state. -/
def problem_spec_membershipGroupColumns
    (lhsCols : List Col) (rhs : Option RhsSubquery)
    (result : List Col × Option RhsSubquery) : Prop :=
  match rhs with
  | none => result.1 = lhsCols ∧ result.2 = none
  | some q =>
      result.1 = lhsCols ++ q.groupKeys ∧
      result.2 = some (if q.explicitlySelected then q else normalizeRhs q)
-- post-conditions-end

-- impl-start
def implementation_membershipGroupColumns
    (lhsCols : List Col) (rhs : Option RhsSubquery) :
    List Col × Option RhsSubquery := Id.run do
  let mut cols := lhsCols
  match rhs with
  | none =>
      return (cols, none)
  | some q0 =>
      let mut q := q0
      if !q.explicitlySelected then
        -- discard the implicit selection …
        q := { q with selected := [], explicitlySelected := false }
        -- … then select only the identity column.
        q := { q with selected := [q.identityColumn], explicitlySelected := true }
      cols := cols ++ q.groupKeys
      return (cols, some q)
-- impl-end

-- proof-start
theorem correct_membershipGroupColumns :
    ∀ (lhsCols : List Col) (rhs : Option RhsSubquery),
      problem_spec_membershipGroupColumns lhsCols rhs
        (implementation_membershipGroupColumns lhsCols rhs) := by
  intro lhsCols rhs
  unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns
  cases rhs with
  | none => exact ⟨rfl, rfl⟩
  | some q =>
    simp only [Id.run, normalizeRhs]
    by_cases h : q.explicitlySelected <;> simp only [h] <;> exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. G-EQ refinement-fidelity audit of django__django-14351 (lean). All same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, lean backend). Cmd for every attack: `bash scripts/lean_verify.sh <path>`; exit 0=verifies/no-sorry, 1=error/unsolved goals.

WHY verify=>correct HOLDS: problem_spec_membershipGroupColumns is a TOTAL FUNCTIONAL spec. rhs=none pins result.1=lhsCols AND result.2=none; some q pins result.1 = lhsCols ++ q.groupKeys AND result.2 = some (if q.explicitlySelected then q else normalizeRhs q). Every output component fixed by '=' for every input => zero wiggle room. Any spec-violating impl yields genuine `unsolved goals` and cannot close; hence NO closing-clean-axiom wrong impl exists, so there is no faithful patch to materialize/resolve (patches={}). Not INCONCLUSIVE: all verifications completed with definite exit codes.

### Attack results
- atk_1 (PREPATCH BUG: no normalization, returns some q unchanged): exit=1, genuine 'unsolved goals' at result.2 for implicitly-selected rhs. Prepatch reproduced (matches Solution_prepatch.lean skeleton).
- atk_2 (control-flow: branch flipped, normalizes only when explicitlySelected=true): exit=1, unsolved goals.
- atk_3 (control-flow-effect: ALWAYS normalizes; wrong for explicitlySelected=true which must be left untouched): exit=1, unsolved goals.
- atk_4 (BOUNDARY: normalizes to selected:=[] instead of [identityColumn], flips explicitlySelected:=true): exit=1, unsolved goals (spec pins normalizeRhs which sets selected:=[identityColumn]).
- atk_5 (wrong cols ORDER: q.groupKeys ++ cols instead of cols ++ q.groupKeys): exit=1, unsolved goals.
- atk_6 (PARTIAL/ungrounded output: drops q.groupKeys from cols, returns cols only): exit=1, unsolved goals.

ADDITIONAL: atk_7 (ungrounded-oracle ECHO: returns the spec's exact expression) is a GENUINELY CORRECT alt impl, NOT a counterexample — it verifies (exit=0) with clean axioms ('does not depend on any axioms'). It behaves identically to gold, so its faithful patch would resolve; not submitted as an attack.

AXIOMS: pos_control (`#print axioms correct_membershipGroupColumns`) => depends on axioms: [propext] (clean/standard); atk_7 => no axioms. No sorry anywhere. pos_control exit=0.

REFINEMENT.MD AUDIT: 8 legs, all R / A-reference / I — NO kind-3 (changed-inexpressible), axioms list empty, conf_skip=false. Legs 1-3,8 = R/I (list build, Option match, frame-discipline pair). Legs 4-7 = A-reference deep field-update models of the real callees: leg4 explicitlySelected<->has_select_fields=bool(select or masks) query.py:243-245; leg5 {selected:=[],explicitlySelected:=false}<->clear_select_clause() query.py:1861; leg6 {selected:=[identityColumn],explicitlySelected:=true}<->add_fields(['pk']) query.py:1893; leg7 groupKeys<->rhs.get_group_by_cols() (patch-invariant [self]). All validated by G-CONF (conformance_check.py runs the REAL patched In.get_group_by_cols over faithful Query-state collaborators, both polarities of explicitlySelected + none rhs, 120000 randomized + catalogue cases, seed 20240630). A-leg correspondence holds; discriminating component is result.2 (rhs selection state), which is exactly where prepatch (atk_1) diverges.

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

/-!
Collecting the grouping-key columns contributed by a *membership* condition — a
condition of the form "this column's value is among the results of a nested
query".

A grouping key is built from two parts: the columns contributed by the
condition's left-hand side, followed by the columns contributed by its
right-hand side when that right-hand side is itself a nested query. A nested
query carries a notion of *which columns it selects*: either an explicit list of
selected columns chosen by the caller, or — when no explicit selection was made
— the full set of default columns of its underlying model.

A nested query used purely as the right-hand side of a membership condition must
behave as a single-valued expression: when contributing to a grouping key it has
to be reduced to exactly one identity column. The desired behavior is therefore:

* the left-hand side columns are always collected verbatim, in order, first;
* if the right-hand side is a nested query that has NO explicit selection, it is
  first normalized so that it selects only its single identity column, and only
  then does it contribute its grouping columns;
* if the right-hand side already has an explicit selection, it is left untouched;
* if the right-hand side is not a nested query, nothing is appended and no
  normalization occurs.

The grouping columns a nested query contributes are determined by the query as a
whole and do not themselves change under this normalization; what changes — and
what makes the membership condition emit a single-valued nested query — is the
normalized selection state the query is left in. The behavior is stated as an
input→output relation over both the collected column list and the resulting
nested-query state; the implementation and proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Both operations on a
-- nested query — discarding an implicit selection and then selecting only its
-- identity column — are modeled DEEPLY as field updates on the query-state
-- structure below, so there is no consumed axiom.
-- axioms-end

-- pure-start
/-- A column expression, modeled by its identity. Only equality/identity of
columns matters for grouping-key collection, so a `Nat` tag suffices. -/
abbrev Col := Nat

/-- The touched state of a nested query used as the right-hand side of a
membership condition. Only the fields the behavior reads or writes are modeled. -/
structure RhsSubquery where
  /-- Whether the query has an explicit caller-chosen column selection. -/
  explicitlySelected : Bool
  /-- The explicitly-selected columns (meaningful when `explicitlySelected`). -/
  selected : List Col
  /-- The model's default columns (what the query would emit with no explicit
  selection). -/
  defaultColumns : List Col
  /-- The grouping columns this query contributes; determined by the query as a
  whole and invariant under selection normalization. -/
  groupKeys : List Col
  /-- The single identity column the query is reduced to when normalized. -/
  identityColumn : Col
  deriving DecidableEq, Repr

/-- Normalize a nested query that lacks an explicit selection: discard any
implicit selection, then select only its identity column. -/
def normalizeRhs (q : RhsSubquery) : RhsSubquery :=
  { q with selected := [q.identityColumn], explicitlySelected := true }
-- pure-end

-- post-conditions-start
/-- The collected grouping key (`result.1`) and the resulting right-hand-side
state (`result.2`):

* left-hand-side columns are always collected first, in order;
* when the rhs is a nested query, its grouping columns are appended;
* a nested query with no explicit selection is normalized to its identity
  column before it contributes (and that normalized state is the result state);
* a nested query that already has an explicit selection is left untouched;
* a non-query rhs contributes nothing and leaves no rhs state. -/
def problem_spec_membershipGroupColumns
    (lhsCols : List Col) (rhs : Option RhsSubquery)
    (result : List Col × Option RhsSubquery) : Prop :=
  match rhs with
  | none => result.1 = lhsCols ∧ result.2 = none
  | some q =>
      result.1 = lhsCols ++ q.groupKeys ∧
      result.2 = some (if q.explicitlySelected then q else normalizeRhs q)
-- post-conditions-end

-- impl-start
def implementation_membershipGroupColumns
    (lhsCols : List Col) (rhs : Option RhsSubquery) :
    List Col × Option RhsSubquery := Id.run do
  let mut cols := lhsCols
  match rhs with
  | none =>
      return (cols, none)
  | some q0 =>
      let mut q := q0
      if !q.explicitlySelected then
        -- discard the implicit selection …
        q := { q with selected := [], explicitlySelected := false }
        -- … then select only the identity column.
        q := { q with selected := [q.identityColumn], explicitlySelected := true }
      cols := cols ++ q.groupKeys
      return (cols, some q)
-- impl-end

-- proof-start
theorem correct_membershipGroupColumns :
    ∀ (lhsCols : List Col) (rhs : Option RhsSubquery),
      problem_spec_membershipGroupColumns lhsCols rhs
        (implementation_membershipGroupColumns lhsCols rhs) := by
  intro lhsCols rhs
  unfold problem_spec_membershipGroupColumns implementation_membershipGroupColumns
  cases rhs with
  | none => exact ⟨rfl, rfl⟩
  | some q =>
    simp only [Id.run, normalizeRhs]
    by_cases h : q.explicitlySelected <;> simp only [h] <;> exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. G-EQ refinement-fidelity audit of django__django-14351 (lean). All same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, lean backend). Cmd for every attack: `bash scripts/lean_verify.sh <path>`; exit 0=verifies/no-sorry, 1=error/unsolved goals.

WHY verify=>correct HOLDS: problem_spec_membershipGroupColumns is a TOTAL FUNCTIONAL spec. rhs=none pins result.1=lhsCols AND result.2=none; some q pins result.1 = lhsCols ++ q.groupKeys AND result.2 = some (if q.explicitlySelected then q else normalizeRhs q). Every output component fixed by '=' for every input => zero wiggle room. Any spec-violating impl yields genuine `unsolved goals` and cannot close; hence NO closing-clean-axiom wrong impl exists, so there is no faithful patch to materialize/resolve (patches={}). Not INCONCLUSIVE: all verifications completed with definite exit codes.

### Attack results
- atk_1 (PREPATCH BUG: no normalization, returns some q unchanged): exit=1, genuine 'unsolved goals' at result.2 for implicitly-selected rhs. Prepatch reproduced (matches Solution_prepatch.lean skeleton).
- atk_2 (control-flow: branch flipped, normalizes only when explicitlySelected=true): exit=1, unsolved goals.
- atk_3 (control-flow-effect: ALWAYS normalizes; wrong for explicitlySelected=true which must be left untouched): exit=1, unsolved goals.
- atk_4 (BOUNDARY: normalizes to selected:=[] instead of [identityColumn], flips explicitlySelected:=true): exit=1, unsolved goals (spec pins normalizeRhs which sets selected:=[identityColumn]).
- atk_5 (wrong cols ORDER: q.groupKeys ++ cols instead of cols ++ q.groupKeys): exit=1, unsolved goals.
- atk_6 (PARTIAL/ungrounded output: drops q.groupKeys from cols, returns cols only): exit=1, unsolved goals.

ADDITIONAL: atk_7 (ungrounded-oracle ECHO: returns the spec's exact expression) is a GENUINELY CORRECT alt impl, NOT a counterexample — it verifies (exit=0) with clean axioms ('does not depend on any axioms'). It behaves identically to gold, so its faithful patch would resolve; not submitted as an attack.

AXIOMS: pos_control (`#print axioms correct_membershipGroupColumns`) => depends on axioms: [propext] (clean/standard); atk_7 => no axioms. No sorry anywhere. pos_control exit=0.

REFINEMENT.MD AUDIT: 8 legs, all R / A-reference / I — NO kind-3 (changed-inexpressible), axioms list empty, conf_skip=false. Legs 1-3,8 = R/I (list build, Option match, frame-discipline pair). Legs 4-7 = A-reference deep field-update models of the real callees: leg4 explicitlySelected<->has_select_fields=bool(select or masks) query.py:243-245; leg5 {selected:=[],explicitlySelected:=false}<->clear_select_clause() query.py:1861; leg6 {selected:=[identityColumn],explicitlySelected:=true}<->add_fields(['pk']) query.py:1893; leg7 groupKeys<->rhs.get_group_by_cols() (patch-invariant [self]). All validated by G-CONF (conformance_check.py runs the REAL patched In.get_group_by_cols over faithful Query-state collaborators, both polarities of explicitlySelected + none rhs, 120000 randomized + catalogue cases, seed 20240630). A-leg correspondence holds; discriminating component is result.2 (rhs selection state), which is exactly where prepatch (atk_1) diverges.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit found no divergence between the modeled function and the real repo callee (django.db.models.lookups.In.get_group_by_cols added by the gold patch).

Evidence:
1. Lean: Solution.lean compiles clean (lean_verify exit 0); #print axioms correct_membershipGroupColumns => [propext] only, no sorryAx. Proof genuinely constrains BOTH output components (result.1 = lhsCols ++ q.groupKeys, result.2 = some (if explicitlySelected then q else normalizeRhs q)).
2. same_spec(Solution, Solution_prepatch, lean) = True — spec region is a shared contract; the prepatch impl (returns some q untouched) genuinely fails it, so the spec is discriminating, not vacuous or over-fit.
3. Conformance: applied the exact gold hunk into a copy of the base repo (django_gold lacked the override — it is prepatch) and ran conformance_check.py against the REAL patched In.get_group_by_cols: checked=120007 disagreements=0.
4. Independent real-Query validation (not the FakeQuery stub): built a real django.db.models.sql.query.Query over a real model and ran the patched method:
   - implicit selection (has_select_fields=False): after call has_select_fields flips True, select=(Col pk,), and Query.get_group_by_cols() is INVARIANT ([] before == [] after) — exactly normalizeRhs; groupKeys-invariance claim holds in the real repo (get_group_by_cols depends on get_external_cols, not on select).
   - explicit selection: left untouched, groupKeys invariant.
   - alias argument: ignored (spec correctly omits it).
   - non-query rhs: nothing appended, no rhs state (none branch).

The modeling boundary (RhsSubquery capturing only touched state: explicitlySelected/selected/defaultColumns/groupKeys/identityColumn) faithfully mirrors query.py:243-245 (has_select_fields), :1871 (clear_select_clause), :1892/1903 (set_select/add_fields), and :1056 (get_group_by_cols). No input found where the spec is stronger than or drifts from real behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical checks: leakage.screen() PASSED (no hard failures); markers.same_spec(Solution, Solution_prepatch) = True (spec regions byte-identical). Semantic judgment: the spec view does not reconstruct the gold edit beyond the public problem_statement. The gold patch adds In.get_group_by_cols which, when the rhs subquery has no explicit selection (not has_select_fields), calls clear_select_clause()+add_fields(['pk']) to reduce it to its identity/pk column. The public problem_statement ALREADY discloses this whole mechanism: it shows the broken __in case selecting all default columns (select_fields [0..6], default_cols=True, select=()) vs the working __id__in case selecting only id ([0]), the 'subquery must return only one column' error, GROUP BY context, and even a proposed fix (reduce cols to [cols[0]]). The spec view stays at/below that abstraction: it leaks NO Python identifier (no get_group_by_cols, In, has_select_fields, clear_select_clause, add_fields, pk), no file/line, using only domain-abstract terms (membership condition, nested query, explicit selection, identity column, grouping columns). The 'normalize an implicitly-selected nested rhs to its single identity column' behavior is exactly what the problem_statement's working-vs-broken contrast makes explicit. No gold-reconstruction leverage beyond the public problem. hints_text explicitly excluded from consideration per instructions.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
