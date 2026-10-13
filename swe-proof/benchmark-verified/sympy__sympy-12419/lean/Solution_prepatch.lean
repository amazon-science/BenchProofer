import Mathlib
-- imports-end

/-!
The single element of an identity matrix at a pair of (possibly symbolic) row
and column positions.

An identity matrix is one on the diagonal and zero off the diagonal. When the
two positions are concrete the answer is immediate: equal positions give one and
distinct positions give zero. But in a symbolic setting a position can be an
expression (e.g. a free integer symbol), and the equality of two such positions
need not be decidable in advance — it is only resolved once concrete values are
substituted.

The desired behavior distinguishes THREE situations for the pair of positions:

  * their equality is known to hold  → the element is one;
  * their equality is known to fail  → the element is zero;
  * their equality is not yet determined → the element is a *deferred equality
    indicator* of the two positions: a symbolic value that evaluates to one when
    the positions later turn out equal and to zero otherwise.

The essential point is the third case: when it is not yet known whether the two
positions coincide, the element must remain the deferred indicator and must NOT
be reported as a plain zero. Reporting zero there would treat an undetermined
comparison as if the positions were definitely distinct, and downstream
aggregations (such as summing the element over a range that includes the
diagonal) would then lose the diagonal contribution.

Obtaining that deferred indicator is itself an act of comparison, and it need not
leave the comparison open. The indicator is produced by an operation carrying its
own means of settling the two positions, and that means is not the one that
classified the pair as undetermined above: on some pairs it succeeds where the
earlier classification did not, and it then delivers an outright value rather
than a symbolic one. Where it settles such a pair negatively, the value it
delivers is a plain zero, and there is no symbolic indicator left to report.

The element is therefore specified over BOTH observations: how the pair of
positions is classified, and — when that classification is undetermined — what
obtaining the indicator actually delivered. On an undetermined pair the element
is exactly the latter: the symbolic indicator on the pairs where obtaining it
left the comparison open, and a plain zero on the pairs where obtaining it
settled the comparison. So the requirement of the third case is precisely this: a
plain zero must not be reported for an undetermined pair whose indicator was left
SYMBOLIC. That is what keeps the diagonal contribution alive under aggregation,
and demanding more than it would demand a symbolic value on pairs where none
exists.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The element is
-- modeled DEEPLY over the two observations the reported value depends on: the
-- three-valued classification of the pair of positions (known-equal,
-- known-distinct, undetermined) and, on an undetermined classification, the
-- outcome of obtaining the deferred indicator. Both are upstream observations
-- carried as plain input data, and the symbolic indicator is represented
-- structurally. So no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The three-valued status of comparing two (possibly symbolic) positions:
* `known_equal`   — the two positions are known to coincide;
* `known_distinct`— the two positions are known to differ;
* `undetermined`  — it is not (yet) known whether they coincide. -/
inductive IdxCmp where
  | known_equal
  | known_distinct
  | undetermined
deriving DecidableEq, Repr

/-- The outcome of obtaining the deferred equality indicator of the two
positions — the second observation, read only where the classification of the
pair is `undetermined`:
* `settled_zero`  — obtaining the indicator settled the two positions
  negatively, so what it delivered is a plain zero and no symbolic value
  remains;
* `left_symbolic` — obtaining the indicator left the comparison open, so what it
  delivered is a genuine symbolic indicator of the two positions. -/
inductive IndOutcome where
  | settled_zero
  | left_symbolic
deriving DecidableEq, Repr

/-- The value of a single matrix element at positions `i, j` (each of position
type `α`):
* `one`         — the constant one;
* `zero`        — the constant zero;
* `deferred i j`— the deferred equality indicator of `i` and `j` (a symbolic
  value, distinct from `zero`, that resolves to one iff `i` and `j` coincide). -/
inductive Elem (α : Type) where
  | one
  | zero
  | deferred (i j : α)
deriving Repr

/-- The element dictated by the two observations: the classification of the pair
of positions decides first, and only on an undetermined classification does the
outcome of obtaining the deferred indicator decide between the symbolic
indicator and a plain zero. -/
def elemOf {α : Type} (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α :=
  match cmp with
  | .known_equal    => .one
  | .known_distinct => .zero
  | .undetermined   =>
    match ind with
    | .settled_zero  => .zero
    | .left_symbolic => .deferred i j
-- pure-end

-- post-conditions-start
/-- The reported element is exactly the one dictated by the two observations: one
when the positions are known equal, zero when they are known distinct, and — when
their equality is undetermined — exactly what obtaining the deferred indicator
delivered, which is the deferred indicator of those two positions (NOT a plain
zero) on every pair where that indicator was left symbolic. -/
def problem_spec_identityElement {α : Type}
    (cmp : IdxCmp) (ind : IndOutcome) (i j : α) (result : Elem α) : Prop :=
  result = elemOf cmp ind i j
-- post-conditions-end

-- impl-start
def implementation_identityElement {α : Type}
    (cmp : IdxCmp) (ind : IndOutcome) (i j : α) : Elem α := Id.run do
  -- Pre-patch state: a two-valued comparison — equal positions give one, and
  -- EVERY other case (including an undetermined comparison, whatever obtaining
  -- the indicator delivered) gives a plain zero, so the symbolic indicator is
  -- never produced.
  match cmp with
  | .known_equal => return .one
  | _            => return .zero
-- impl-end

-- proof-start
theorem correct_identityElement {α : Type} :
    ∀ (cmp : IdxCmp) (ind : IndOutcome) (i j : α),
      problem_spec_identityElement cmp ind i j
        (implementation_identityElement cmp ind i j) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
