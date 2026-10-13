import Mathlib
-- imports-end

/-!
Resolving a single ORDER BY column to its position within the result columns of a
*combined* query (a UNION / INTERSECT / DIFFERENCE of sub-queries).

In a combined query, an ORDER BY term cannot be referenced by name; it must be
rewritten to the 1-based position of a matching column in the result column set.

Two column lists take part, and they are different lists.

* The **result columns** are what the term is matched against: each carries an
  expression and an optional output alias, and a match reports that column's
  1-based ordinal in this list. This list is assembled once, ahead of ordering,
  and ordering never grows it.
* The query's own **selected columns**, with the list of value labels naming
  them, are the state a new order column joins. The label list is what the
  combination hands down to every sub-query so that each arm selects the same
  columns as the outer query, so the two stay in one-to-one correspondence and
  anything added to the selected columns must be named in the label list as
  well. A newly added order column's position is its 1-based ordinal in *this*
  list, which in general is neither as long as the result columns nor a prefix
  of them.

An optional alias counts as an alias exactly where it is tested for truth: a
name that is present and non-empty. A present but empty name is no alias at all,
and neither is an absent one.

The order term is a stack of zero or more *reference wrappers* over an
underlying expression. Each wrapper carries its own identity together with the
alias name it references; the innermost expression is the one no wrapper stands
over. The expression the term compares is its outermost wrapper if it has one,
else the underlying expression, and every wrapper contributes the same value
label as the underlying expression, since a wrapper only names what it stands
over. That label is the one an expression contributes when it becomes one of the
query's selected columns: a name, no name at all, or — for an expression whose
output is itself undetermined — no label that can be produced.

Two expressions are the SAME EXPRESSION exactly when their identities agree.
That test reads the identity and nothing else: an expression's identity does not
settle the value label it contributes, so two expressions may be the same
expression and still contribute different labels — a scan that has met one of
them has met the other, and it is the label of the term in hand, not of the
column it met, that is contributed if the term is later added — and two
expressions with different identities may contribute the same label.

The result columns are scanned in order, carrying the term along:
* when the term is a reference and the column's alias is exactly the alias its
  outermost wrapper references, that one wrapper is removed, so the compared
  expression becomes whatever the wrapper stood over — which may be a further
  wrapper, whose own referenced alias a later column can then meet in turn;
* a column is compared only if it is that referenced column, or it carries no
  alias; any other aliased column is skipped;
* the first column whose expression is the same expression as the carried
  compared expression gives the result: its 1-based ordinal among the result
  columns, with the query's column state left untouched;
* a referenced alias can only be read off a wrapper, so a reference term with no
  wrapper left over it cannot be compared against a further column at all:
  resolution stops there with the query's column state untouched.

When no result column matches, the outcome depends on the alias the no-match
case consults, which is the alias of the LAST COLUMN THE SCAN VISITED — the
trailing result column. That alias belongs to the column the scan last visited,
so where there was no column to visit at all there is no such alias in hand and
none can be obtained: resolution stops there, with the query's column state
untouched. Otherwise, if that alias is an alias, the term genuinely does not
correspond to any result column and resolution fails; if it is not, the final
compared expression is appended to the query's selected columns, and then its value label is appended to the label
list so that the two stay in correspondence, and the term resolves to that
column's new trailing ordinal among the query's selected columns. Those two
appends happen in that order, and the second needs a label to append: for an
expression that has none to produce, the column has already joined the selected
columns by the time the label cannot be had, so resolution stops there — the
selected columns grown by that column, the label list untouched, the two parts out
of correspondence, and no position reported.

Consequently a reported position is always a genuine 1-based ordinal: when the
query's column state is left untouched it is an ordinal of the result columns,
and when the state grows — by exactly one column — it is the ordinal of that new
column; and a state that arrives in correspondence leaves in correspondence.
Where resolution stops instead of reporting a position, the result columns and
the label list are exactly as they arrived and the selected columns have grown by
at most one column.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The result-column scan, the carried
-- reference stack and the expression it compares, the new-selected-column side
-- effect on BOTH parts of the query's column state, the value label an
-- expression contributes, and the position arithmetic are all modeled deeply
-- over the input carriers; two expressions are the same expression exactly when
-- their modeled identities agree, the value label taking no part in that test.
-- No `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The value label an expression contributes when it becomes one of the query's
selected columns: a name, no name at all, or no label that can be produced —
the last for an expression whose output is itself undetermined, so that asking
for its label yields nothing to append. -/
inductive OutputLabel where
  | name (label : String)
  | anonymous
  | undetermined
deriving DecidableEq, Repr

/-- A modeled query expression: an opaque identity together with the value label
it contributes when it becomes one of the query's selected columns. The two
components are independent observations of one expression — the identity is what
decides whether this is the same expression as another, the label is what it
contributes when added, and neither determines the other. -/
structure QExpr where
  id    : Nat
  label : OutputLabel
deriving DecidableEq, Repr

/-- Whether two expressions are the same expression, as the scan's comparison
tests them: their identities agree. The value label takes no part, so this holds
of two expressions that contribute different labels as readily as of two that
contribute the same one. -/
def QExpr.sameExpr (a b : QExpr) : Bool := a.id == b.id

/-- A result column: its expression together with its optional output alias. -/
structure SelCol where
  expr     : QExpr
  colAlias : Option String
deriving DecidableEq, Repr

/-- The column state a single ORDER BY term is resolved against.

`resultCols` are the columns the term is matched against; a match reports an
ordinal in this list, and resolving a term never grows it. `querySelect` are the
query's own selected columns and `valuesSelect` the value labels naming those
same columns for the arms of the combination; these two describe one column set,
so they stay in correspondence, and they are what a newly added order column
joins. A label in that list may be a name or no name at all. `resultCols` and
`querySelect` are independent: the former may be longer, shorter, or unrelated
in content. -/
structure QueryCols where
  resultCols   : List SelCol
  querySelect  : List QExpr
  valuesSelect : List (Option String)
deriving DecidableEq, Repr

/-- One reference wrapper of an ORDER BY term: its own opaque identity together
with the optional alias name it references. A wrapper contributes no value label
of its own — it only names the expression it stands over. -/
structure RefLink where
  id   : Nat
  refs : Option String
deriving DecidableEq, Repr

/-- An ORDER BY source term: a stack of reference wrappers, outermost first, over
the underlying expression no wrapper stands over. An empty stack is a term that
is not a reference at all. -/
structure OrderSrc where
  links : List RefLink
  base  : QExpr
deriving DecidableEq, Repr

/-- The expression the term currently compares: its outermost wrapper if it has
one, else the underlying expression. A wrapper's value label is the underlying
expression's, since a wrapper only names what it stands over. -/
def OrderSrc.compared (s : OrderSrc) : QExpr :=
  match s.links with
  | []     => s.base
  | l :: _ => { id := l.id, label := s.base.label }

/-- The alias the term's outermost wrapper references, where it still has one: a
referenced alias can only be read off a wrapper, so a term with no wrapper left
has no such alias to offer. -/
def OrderSrc.refs? (s : OrderSrc) : Option (Option String) :=
  s.links.head?.map RefLink.refs

/-- The term with its outermost wrapper removed, so that the compared expression
becomes whatever that wrapper stood over — a further wrapper, or the underlying
expression when it was the last one. -/
def OrderSrc.stripped (s : OrderSrc) : OrderSrc :=
  { s with links := s.links.tail }

/-- The outcome of resolving one ORDER BY term against the column state:
`resolved pos cols` gives the 1-based position together with the (possibly
extended) column state; `noMatch` signals the term matches no result column;
`aborted cols` signals that resolution stopped without a position, carrying the
column state as it was left. -/
inductive OrderByOutcome where
  | resolved (position : Nat) (cols : QueryCols)
  | noMatch
  | aborted (cols : QueryCols)
deriving DecidableEq, Repr

/-- The query's selected columns and the value labels naming them describe the
same column set, so they have the same length. -/
def inCorrespondence (q : QueryCols) : Bool :=
  q.valuesSelect.length == q.querySelect.length

/-- Whether an optional alias counts as an alias where the scan and the trailing
dispatch test it for truth: only a name that is present and non-empty does. -/
def hasAlias (a : Option String) : Bool :=
  match a with
  | none   => false
  | some s => !s.isEmpty

/-- What an outcome must satisfy, given the state it started from. Whenever it
reports a position: the resulting query column state is still in correspondence,
the position is a genuine 1-based ordinal, and it is an ordinal of the right
list — of the result columns when the query's selected columns were left
untouched, and of the query's selected columns (its new trailing one, the state
having grown by exactly one column) when they were extended. When it stops
without a position: the result columns and the value labels are exactly as they
arrived and the selected columns have grown by at most one column. -/
def outcomeUsable (q : QueryCols) (result : OrderByOutcome) : Bool :=
  match result with
  | OrderByOutcome.resolved pos q' =>
      inCorrespondence q' && decide (1 ≤ pos) &&
      (if q'.querySelect.length == q.querySelect.length then
         decide (q' = q) && decide (pos ≤ q.resultCols.length)
       else
         decide (q'.querySelect.length = q.querySelect.length + 1) &&
         decide (pos = q'.querySelect.length))
  | OrderByOutcome.noMatch => true
  | OrderByOutcome.aborted q' =>
      decide (q'.resultCols = q.resultCols) &&
      decide (q'.valuesSelect = q.valuesSelect) &&
      decide (q'.querySelect.length ≤ q.querySelect.length + 1)

/-- What the result-column scan yields: `atPos pos` for the first matching
column (1-based), `exhausted finalCur` when nothing matched (carrying the final
compared expression, which becomes the new selected column), or `halted` when
the scan reached a column it cannot examine at all — a reference term with no
wrapper left to read a referenced alias off. -/
inductive ScanResult where
  | atPos (position : Nat)
  | exhausted (finalCur : QExpr)
  | halted
deriving DecidableEq, Repr

/-- Scan the result columns left to right carrying `cur`, the term with as many
of its reference wrappers removed as the columns met so far have referenced, and
`idx`, the 0-based position. Mirrors the scan's removal of one wrapper when the
column's alias is the one that wrapper references — after which the wrapper below
it, if any, offers its own referenced alias to the columns still to come — and
the fact that a reference term with no wrapper left has no referenced alias to
read and so cannot be carried on to a further column. A column is met when its
expression is the same expression as the carried one, which is a question about
their identities only: a column whose expression would contribute a different
value label from the carried term's is met just the same, and the label such a
column would contribute is never consulted. -/
def scanCols (isRef : Bool) : Nat → OrderSrc → List SelCol → ScanResult
  | _, cur, [] => ScanResult.exhausted cur.compared
  | idx, cur, col :: rest =>
    if isRef && cur.refs?.isNone then
      ScanResult.halted
    else
      let aliasMatch := isRef && cur.refs? == some col.colAlias
      let cur' := if aliasMatch then cur.stripped else cur
      if (aliasMatch || !hasAlias col.colAlias) && cur'.compared.sameExpr col.expr then
        ScanResult.atPos (idx + 1)
      else
        scanCols isRef (idx + 1) cur' rest

/-- Adding the carried expression to the query's column state: it is appended to
the query's selected columns and, so that the two parts stay in correspondence,
the value label it contributes is appended to the label list. The result columns
are untouched — they are not reassembled when a term adds a column. -/
def withNewResultCol (q : QueryCols) (e : QExpr) (lab : Option String) : QueryCols :=
  { resultCols   := q.resultCols,
    querySelect  := q.querySelect ++ [e],
    valuesSelect := q.valuesSelect ++ [lab] }

/-- The column state left behind when the expression has joined the query's
selected columns but no label can be produced to name it: the first append has
landed, the label list is untouched, and the two parts no longer correspond. -/
def withPartialResultCol (q : QueryCols) (e : QExpr) : QueryCols :=
  { resultCols   := q.resultCols,
    querySelect  := q.querySelect ++ [e],
    valuesSelect := q.valuesSelect }

/-- The outcome once the carried compared expression is to become one of the
query's selected columns: it is appended there and then, if it has a value label
to contribute, that label is appended to the label list and the term resolves to
the new trailing ordinal among the selected columns; where it has no label to
produce, the first of those two appends has already landed and resolution stops
there instead. -/
def addedOutcome (q : QueryCols) (cur : QExpr) : OrderByOutcome :=
  match cur.label with
  | OutputLabel.name s =>
      let newCols := withNewResultCol q cur (some s)
      OrderByOutcome.resolved newCols.querySelect.length newCols
  | OutputLabel.anonymous =>
      let newCols := withNewResultCol q cur none
      OrderByOutcome.resolved newCols.querySelect.length newCols
  | OutputLabel.undetermined =>
      OrderByOutcome.aborted (withPartialResultCol q cur)

/-- The resolution outcome, defined structurally over the inputs: the 1-based
ordinal among the result columns of the first matching one (query column state
unchanged); a stop with the state untouched where the scan cannot examine a
column; or — when nothing matches — failure where the last result column the
scan visited carries an alias, a stop with the state untouched where there was no
column to visit and so no such alias in hand, else the final compared expression
added to the query's column state and resolved to its new trailing ordinal
there, or, when that expression has no label to append, a stop with the column
added and the label list untouched. -/
def resolveOutcome (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome :=
  match scanCols isRef 0 src q.resultCols with
  | ScanResult.atPos pos => OrderByOutcome.resolved pos q
  | ScanResult.halted => OrderByOutcome.aborted q
  | ScanResult.exhausted finalCur =>
    match q.resultCols.getLast? with
    | some lastCol =>
        if hasAlias lastCol.colAlias then
          OrderByOutcome.noMatch
        else
          addedOutcome q finalCur
    | none => OrderByOutcome.aborted q
-- pure-end

-- post-conditions-start
/-- The resolution result is exactly the structurally-defined outcome: the
1-based ordinal among the result columns of the first matching one (query column
state unchanged); a stop with the state untouched where a reference term has no
wrapper left to read a referenced alias off; or — when nothing matches — failure for
an aliased last-visited result column, a stop with the state untouched where the
scan visited no column at all and so holds no such alias, else the order column
added to the query's column state — in BOTH parts of it — and resolved to its new trailing ordinal
among the query's selected columns, and, for an order column with no label to
append, a stop after the first of those two appends. Moreover, on a column state
that arrives in correspondence, a reported position is a genuine 1-based ordinal
of the list it belongs to and the resulting query column state is still in
correspondence, so the position is readable against every arm of the
combination; and where no position is reported the labels arrive as they left and
at most one column was added. -/
def problem_spec_resolveOrderColumn
    (q : QueryCols) (isRef : Bool) (src : OrderSrc)
    (result : OrderByOutcome) : Prop :=
  result = resolveOutcome q isRef src
  ∧ (inCorrespondence q = true → outcomeUsable q result = true)
-- post-conditions-end
-- impl-start
def implementation_resolveOrderColumn
    (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome := Id.run do
  let mut cur : OrderSrc := src
  let mut idx : Nat := 0
  for col in q.resultCols do
    if isRef && cur.refs?.isNone then
      return OrderByOutcome.aborted q
    let aliasMatch := isRef && cur.refs? == some col.colAlias
    if aliasMatch then
      cur := cur.stripped
    if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
      return OrderByOutcome.resolved (idx + 1) q
    idx := idx + 1
  -- PRE-PATCH BUG: the no-match case unconditionally signals failure; it
  -- neither inspects the last result column the scan visited nor adds the order
  -- column to the query's column state, so it never asks that column for a
  -- value label either.
  return OrderByOutcome.noMatch
-- impl-end

-- proof-start
theorem correct_resolveOrderColumn :
    ∀ (q : QueryCols) (isRef : Bool) (src : OrderSrc),
      problem_spec_resolveOrderColumn q isRef src
        (implementation_resolveOrderColumn q isRef src) := by
  sorry
-- proof-end
