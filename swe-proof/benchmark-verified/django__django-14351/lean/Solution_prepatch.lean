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
-- PRE-PATCH (buggy) skeleton: a nested right-hand side contributes its grouping
-- columns directly, WITHOUT first being reduced to a single identity column when
-- it carries no explicit selection. An implicitly-selected subquery is therefore
-- left with all of its default columns — it is no longer single-valued.
def implementation_membershipGroupColumns
    (lhsCols : List Col) (rhs : Option RhsSubquery) :
    List Col × Option RhsSubquery := Id.run do
  let mut cols := lhsCols
  match rhs with
  | none =>
      return (cols, none)
  | some q =>
      cols := cols ++ q.groupKeys
      return (cols, some q)
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl: for a
-- nested rhs with no explicit selection the spec demands the result state be the
-- normalized query, but the buggy impl returns it untouched.
theorem correct_membershipGroupColumns :
    ∀ (lhsCols : List Col) (rhs : Option RhsSubquery),
      problem_spec_membershipGroupColumns lhsCols rhs
        (implementation_membershipGroupColumns lhsCols rhs) := by
  sorry
-- proof-end
