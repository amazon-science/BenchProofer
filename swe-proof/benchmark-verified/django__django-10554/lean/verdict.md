# P2 adversarial audit — django__django-10554

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong implementation closed correct_resolveOrderColumn, so there is no verifying attack whose faithful patch could exhibit verify-does-not-imply-correct. All 10 attacks were REJECTED (lean_verify.sh exit 1), each additionally backed by a machine-checked refutation witness (wit_N.lean, exit 0) proving the postcondition is FALSE at a concrete input for that impl -- so each attack is genuinely unprovable, not merely failing to reapply gold's tactic body. Positive control verifies (exit 0, clean axioms) with a structurally different impl shape. Oracle discriminating power confirmed by EXECUTED resolve runs: the prepatch-shaped faithful patch does NOT resolve (completed=true, resolved=false, 3 consistent attempts, both F2P fail), while a model-faithful transliteration of resolveOutcome DOES resolve (completed=true, resolved=true, 2/2 F2P + 23/23 P2P).
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -352,13 +352,8 @@
     if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
       return OrderByOutcome.resolved (idx + 1) q
     idx := idx + 1
-  match q.resultCols.getLast? with
-  | some lastCol =>
-      if hasAlias lastCol.colAlias then
-        return OrderByOutcome.noMatch
-      else
-        return addedOutcome q cur.compared
-  | none => return OrderByOutcome.aborted q
+  -- PREPATCH BUG re-encoded: unconditional failure on the no-match case.
+  return OrderByOutcome.noMatch
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -341,15 +341,14 @@
 -- impl-start
 def implementation_resolveOrderColumn
     (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome := Id.run do
+  -- PARTIAL DOMAIN: a reference term is not handled at all; the impl stops
+  -- immediately instead of scanning, so the whole isRef=true slice is wrong.
+  if isRef then
+    return OrderByOutcome.aborted q
   let mut cur : OrderSrc := src
   let mut idx : Nat := 0
   for col in q.resultCols do
-    if isRef && cur.refs?.isNone then
-      return OrderByOutcome.aborted q
-    let aliasMatch := isRef && cur.refs? == some col.colAlias
-    if aliasMatch then
-      cur := cur.stripped
-    if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
+    if !hasAlias col.colAlias && cur.compared.sameExpr col.expr then
       return OrderByOutcome.resolved (idx + 1) q
     idx := idx + 1
   match q.resultCols.getLast? with
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -352,9 +352,11 @@
     if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
       return OrderByOutcome.resolved (idx + 1) q
     idx := idx + 1
-  match q.resultCols.getLast? with
-  | some lastCol =>
-      if hasAlias lastCol.colAlias then
+  -- BOUNDARY: consults the alias of the FIRST result column instead of the
+  -- LAST one the scan visited (head? for getLast?).
+  match q.resultCols.head? with
+  | some firstCol =>
+      if hasAlias firstCol.colAlias then
         return OrderByOutcome.noMatch
       else
         return addedOutcome q cur.compared
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -352,12 +352,23 @@
     if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
       return OrderByOutcome.resolved (idx + 1) q
     idx := idx + 1
+  -- CONTROL-FLOW EFFECT: on an expression with no label to append, the stop
+  -- carries the state UNTOUCHED, i.e. the first of the two appends is undone,
+  -- so the observable between-the-appends state is lost.
   match q.resultCols.getLast? with
   | some lastCol =>
       if hasAlias lastCol.colAlias then
         return OrderByOutcome.noMatch
       else
-        return addedOutcome q cur.compared
+        match cur.compared.label with
+        | OutputLabel.name s =>
+            let newCols := withNewResultCol q cur.compared (some s)
+            return OrderByOutcome.resolved newCols.querySelect.length newCols
+        | OutputLabel.anonymous =>
+            let newCols := withNewResultCol q cur.compared none
+            return OrderByOutcome.resolved newCols.querySelect.length newCols
+        | OutputLabel.undetermined =>
+            return OrderByOutcome.aborted q
   | none => return OrderByOutcome.aborted q
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -341,13 +341,15 @@
 -- impl-start
 def implementation_resolveOrderColumn
     (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome := Id.run do
+  -- CONTROL-FLOW EFFECT: the wrapper is peeled on every visited column when the
+  -- term is a reference, not only on the column whose alias that wrapper names.
   let mut cur : OrderSrc := src
   let mut idx : Nat := 0
   for col in q.resultCols do
     if isRef && cur.refs?.isNone then
       return OrderByOutcome.aborted q
     let aliasMatch := isRef && cur.refs? == some col.colAlias
-    if aliasMatch then
+    if isRef then
       cur := cur.stripped
     if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
       return OrderByOutcome.resolved (idx + 1) q
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -340,25 +340,15 @@
 -- post-conditions-end
 -- impl-start
 def implementation_resolveOrderColumn
-    (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome := Id.run do
-  let mut cur : OrderSrc := src
-  let mut idx : Nat := 0
-  for col in q.resultCols do
-    if isRef && cur.refs?.isNone then
-      return OrderByOutcome.aborted q
-    let aliasMatch := isRef && cur.refs? == some col.colAlias
-    if aliasMatch then
-      cur := cur.stripped
-    if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
-      return OrderByOutcome.resolved (idx + 1) q
-    idx := idx + 1
-  match q.resultCols.getLast? with
-  | some lastCol =>
-      if hasAlias lastCol.colAlias then
-        return OrderByOutcome.noMatch
-      else
-        return addedOutcome q cur.compared
-  | none => return OrderByOutcome.aborted q
+    (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome :=
+  -- UNGROUNDED-ORACLE ECHO with a twist: delegates to the spec's own reference
+  -- function on the non-empty-scan case, but on an EMPTY scanned list reports a
+  -- position instead of stopping -- the leg refinement.md row 7b grounds on the
+  -- real UnboundLocalError. If the spec cannot see this the 7b leg is ungrounded.
+  match q.resultCols with
+  | [] => OrderByOutcome.resolved (q.querySelect.length + 1)
+            (withNewResultCol q src.compared none)
+  | _  => resolveOutcome q isRef src
 -- impl-end
 
 -- proof-start
@@ -544,9 +534,6 @@
         (implementation_resolveOrderColumn q isRef src) := by
   intro q isRef src
   have himpl : implementation_resolveOrderColumn q isRef src = resolveOutcome q isRef src := by
-    rw [implementation_resolveOrderColumn,
-        forIn_cons_unfold isRef q q.resultCols src 0,
-        loop_eq_scanCols isRef q q.resultCols src 0]
     rfl
   refine ⟨himpl, ?_⟩
   intro hq
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -349,7 +349,9 @@
     let aliasMatch := isRef && cur.refs? == some col.colAlias
     if aliasMatch then
       cur := cur.stripped
-    if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
+    -- LABEL-IN-MATCH-TEST: reads the value label as part of the match test,
+    -- i.e. structural equality on the whole carrier instead of identity only.
+    if (aliasMatch || !hasAlias col.colAlias) && cur.compared == col.expr then
       return OrderByOutcome.resolved (idx + 1) q
     idx := idx + 1
   match q.resultCols.getLast? with
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -357,7 +357,17 @@
       if hasAlias lastCol.colAlias then
         return OrderByOutcome.noMatch
       else
-        return addedOutcome q cur.compared
+        -- ANONYMOUS-AS-EMPTY-NAME: a column that contributes no name at all is
+        -- named with a present-but-empty label instead of with no label.
+        match cur.compared.label with
+        | OutputLabel.name s =>
+            let newCols := withNewResultCol q cur.compared (some s)
+            return OrderByOutcome.resolved newCols.querySelect.length newCols
+        | OutputLabel.anonymous =>
+            let newCols := withNewResultCol q cur.compared (some "")
+            return OrderByOutcome.resolved newCols.querySelect.length newCols
+        | OutputLabel.undetermined =>
+            return OrderByOutcome.aborted (withPartialResultCol q cur.compared)
   | none => return OrderByOutcome.aborted q
 -- impl-end
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -357,7 +357,17 @@
       if hasAlias lastCol.colAlias then
         return OrderByOutcome.noMatch
       else
-        return addedOutcome q cur.compared
+        -- BOUNDARY / WRONG LIST: the new column's ordinal is counted off the
+        -- SCANNED result columns rather than the query's selected columns.
+        match cur.compared.label with
+        | OutputLabel.name s =>
+            let newCols := withNewResultCol q cur.compared (some s)
+            return OrderByOutcome.resolved (q.resultCols.length + 1) newCols
+        | OutputLabel.anonymous =>
+            let newCols := withNewResultCol q cur.compared none
+            return OrderByOutcome.resolved (q.resultCols.length + 1) newCols
+        | OutputLabel.undetermined =>
+            return OrderByOutcome.aborted (withPartialResultCol q cur.compared)
   | none => return OrderByOutcome.aborted q
 -- impl-end
 
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -346,7 +346,10 @@
   for col in q.resultCols do
     if isRef && cur.refs?.isNone then
       return OrderByOutcome.aborted q
-    let aliasMatch := isRef && cur.refs? == some col.colAlias
+    -- A-REFERENCE ATTACK: the referenced alias is read off the ORIGINAL term
+    -- rather than off whatever the scan currently carries (the "substitute but
+    -- keep comparing the original name" reading).
+    let aliasMatch := isRef && src.refs? == some col.colAlias
     if aliasMatch then
       cur := cur.stripped
     if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
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
    (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome :=
  -- POSITIVE CONTROL: a structurally different but CORRECT impl -- pure
  -- functional form (no do-block / for / mut), with the trailing dispatch's
  -- branches written in the INVERTED order and the alias test taken negatively.
  match scanCols isRef 0 src q.resultCols with
  | ScanResult.atPos pos => OrderByOutcome.resolved pos q
  | ScanResult.halted => OrderByOutcome.aborted q
  | ScanResult.exhausted finalCur =>
    match q.resultCols.getLast? with
    | none => OrderByOutcome.aborted q
    | some lastCol =>
        if !hasAlias lastCol.colAlias then addedOutcome q finalCur
        else OrderByOutcome.noMatch
-- impl-end

-- proof-start
/-- Pure recursion mirroring exactly one iteration of the imperative `for`-loop
followed by the trailing `getLast?` dispatch: over a suffix `cs` of the result
columns, carrying the term `cur` with the wrappers met so far removed and the
0-based index `idx`, while the FULL outer column state `q` is used for the
resolved/extend payload. -/
def loopBody (isRef : Bool) (q : QueryCols) :
    Nat → OrderSrc → List SelCol → OrderByOutcome
  | _idx, cur, [] =>
    match q.resultCols.getLast? with
    | some lastCol =>
        if hasAlias lastCol.colAlias then
          OrderByOutcome.noMatch
        else
          addedOutcome q cur.compared
    | none => OrderByOutcome.aborted q
  | idx, cur, col :: rest =>
    if isRef && cur.refs?.isNone then
      OrderByOutcome.aborted q
    else
      let aliasMatch := isRef && cur.refs? == some col.colAlias
      let cur' := if aliasMatch then cur.stripped else cur
      if (aliasMatch || !hasAlias col.colAlias) && cur'.compared.sameExpr col.expr then
        OrderByOutcome.resolved (idx + 1) q
      else
        loopBody isRef q (idx + 1) cur' rest

/-- The `Id.run` for-loop over a suffix `cs` starting from mutable state
`(cur0, idx0)`, followed by the trailing `getLast?` dispatch, computes exactly
`loopBody`.  Proven by induction on `cs`, unfolding one `forIn` step at a time
(`List.forIn_cons`/`List.forIn_nil`), observing that a `return x` inside the body
becomes `ForInStep.done x` and a fall-through becomes `.yield` of the updated
state.  The outer `q` stays fixed as the resolved/extend payload. -/
theorem forIn_cons_unfold (isRef : Bool) (q : QueryCols) :
    ∀ (cs : List SelCol) (cur0 : OrderSrc) (idx0 : Nat),
      (Id.run do
        let mut cur : OrderSrc := cur0
        let mut idx : Nat := idx0
        for col in cs do
          if isRef && cur.refs?.isNone then
            return OrderByOutcome.aborted q
          let aliasMatch := isRef && cur.refs? == some col.colAlias
          if aliasMatch then
            cur := cur.stripped
          if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
            return OrderByOutcome.resolved (idx + 1) q
          idx := idx + 1
        match q.resultCols.getLast? with
        | some lastCol =>
            if hasAlias lastCol.colAlias then
              return OrderByOutcome.noMatch
            else
              return addedOutcome q cur.compared
        | none => return OrderByOutcome.aborted q)
        = loopBody isRef q idx0 cur0 cs := by
  intro cs
  induction cs with
  | nil =>
    intro cur0 idx0
    rfl
  | cons col rest ih =>
    intro cur0 idx0
    simp only [List.forIn_cons, loopBody]
    split_ifs with h0 h1 h2 h2 <;>
      simp only [Id.run, bind_pure_comp, pure_bind, map_pure] <;>
      first
        | rfl
        | (exact ih _ _)

/-- Core refinement: `loopBody` over `cs` from state `(cur, idx)` equals the
`scanCols` result dispatched identically to `resolveOutcome`'s body — the early
`atPos pos` becomes `resolved pos q`, `halted` becomes a stop with `q` untouched,
and the fall-through `exhausted finalCur` runs the identical `getLast?`/extend
dispatch on the outer `q`. -/
theorem loop_eq_scanCols (isRef : Bool) (q : QueryCols) :
    ∀ (cs : List SelCol) (cur : OrderSrc) (idx : Nat),
      loopBody isRef q idx cur cs
        = (match scanCols isRef idx cur cs with
           | ScanResult.atPos pos => OrderByOutcome.resolved pos q
           | ScanResult.halted => OrderByOutcome.aborted q
           | ScanResult.exhausted finalCur =>
               match q.resultCols.getLast? with
               | some lastCol =>
                   if hasAlias lastCol.colAlias then
                     OrderByOutcome.noMatch
                   else
                     addedOutcome q finalCur
               | none => OrderByOutcome.aborted q) := by
  intro cs
  induction cs with
  | nil =>
    intro cur idx
    simp [loopBody, scanCols, addedOutcome, withNewResultCol, withPartialResultCol]
  | cons col rest ih =>
    intro cur idx
    unfold loopBody scanCols
    by_cases hs : isRef && cur.refs?.isNone
    · simp only [hs, if_true]
    · simp only [hs, if_false, Bool.false_eq_true]
      by_cases h : (isRef && cur.refs? == some col.colAlias || !hasAlias col.colAlias) &&
          (if isRef && cur.refs? == some col.colAlias then cur.stripped else cur).compared.sameExpr
            col.expr
      · simp only [h, if_true]
      · simp only [h]
        exact ih _ _

/-- A matching column's reported position is a genuine 1-based ordinal of a
result column the scan has actually visited: strictly above the starting index
and no further than the end of the scanned suffix. -/
theorem scanCols_bound (isRef : Bool) :
    ∀ (cs : List SelCol) (idx : Nat) (cur : OrderSrc) (pos : Nat),
      scanCols isRef idx cur cs = ScanResult.atPos pos →
      idx < pos ∧ pos ≤ idx + cs.length := by
  intro cs
  induction cs with
  | nil =>
    intro idx cur pos h
    simp [scanCols] at h
  | cons col rest ih =>
    intro idx cur pos h
    unfold scanCols at h
    by_cases hs : isRef && cur.refs?.isNone
    · rw [if_pos hs] at h
      simp at h
    · rw [if_neg hs] at h
      by_cases hg : (isRef && cur.refs? == some col.colAlias || !hasAlias col.colAlias) &&
          (if isRef && cur.refs? == some col.colAlias then cur.stripped else cur).compared.sameExpr
            col.expr
      · rw [if_pos hg] at h
        have hp : pos = idx + 1 := by
          simpa using (ScanResult.atPos.inj h).symm
        subst hp
        simp
      · rw [if_neg hg] at h
        have := ih (idx + 1) _ pos h
        refine ⟨by omega, by simpa [List.length_cons] using by omega⟩

/-- The usability guarantee, proven of the reference outcome itself: on a column
state whose two query-side parts correspond, a reported position is a genuine
1-based ordinal of the list it belongs to and the resulting state still
corresponds, and a stop leaves the labels alone. The match leg leaves the query
column state untouched and uses `scanCols_bound` to place the position inside the
result columns; the extend leg grows the query column state by exactly one
column, and the reported position is that column's ordinal there, correspondence
being maintained because the column and its label are added together; the stop
after the first append leaves the labels alone by construction, as does the stop
where the scan visited no column at all. -/
theorem resolveOutcome_usable (q : QueryCols) (isRef : Bool) (src : OrderSrc)
    (hq : inCorrespondence q = true) :
    outcomeUsable q (resolveOutcome q isRef src) = true := by
  unfold resolveOutcome
  cases hscan : scanCols isRef 0 src q.resultCols with
  | atPos pos =>
    have hb := scanCols_bound isRef q.resultCols 0 src pos hscan
    have h1 : 1 ≤ pos := by omega
    have h2 : pos ≤ q.resultCols.length := by simpa using hb.2
    simp [outcomeUsable, hq, h1, h2]
  | halted => simp [outcomeUsable]
  | exhausted finalCur =>
    unfold inCorrespondence at hq
    simp only [beq_iff_eq] at hq
    have hadd : outcomeUsable q (addedOutcome q finalCur) = true := by
      unfold addedOutcome
      cases hlab : finalCur.label with
      | name s =>
        simp [outcomeUsable, withNewResultCol, inCorrespondence, hq]
      | anonymous =>
        simp [outcomeUsable, withNewResultCol, inCorrespondence, hq]
      | undetermined =>
        simp [outcomeUsable, withPartialResultCol]
    cases hlast : q.resultCols.getLast? with
    | none => simp [outcomeUsable]
    | some lastCol =>
      by_cases ha : hasAlias lastCol.colAlias
      · simp [ha, outcomeUsable]
      · simpa [ha] using hadd

theorem correct_resolveOrderColumn :
    ∀ (q : QueryCols) (isRef : Bool) (src : OrderSrc),
      problem_spec_resolveOrderColumn q isRef src
        (implementation_resolveOrderColumn q isRef src) := by
  intro q isRef src
  have himpl : implementation_resolveOrderColumn q isRef src = resolveOutcome q isRef src := by
    unfold implementation_resolveOrderColumn resolveOutcome
    cases scanCols isRef 0 src q.resultCols with
    | atPos pos => rfl
    | halted => rfl
    | exhausted finalCur =>
      cases q.resultCols.getLast? with
      | none => rfl
      | some lastCol => by_cases ha : hasAlias lastCol.colAlias <;> simp [ha]
  refine ⟨himpl, ?_⟩
  intro hq
  rw [himpl]
  exact resolveOutcome_usable q isRef src hq
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Repo cloned at base_commit 14d026cccb144c6877294ba4cd4e03ebf0842498. Attacks built by copying Solution.lean and editing ONLY the impl region; same_spec=True verified for all 10 via swebench_unified.markers.same_spec, and re-confirmed by the official adversary.check_attack (same_spec=True, admissible=True, verifies=False, verify_completed=True for all 10; positive_control verifies=True).

**COMMANDS.** Per attack: bash scripts/lean_verify.sh atk_N.lean  (run 4-way concurrent as background jobs). Per witness: same command on wit_N.lean. Axioms: gold_axioms.lean and pos_axioms.lean append '#print axioms correct_resolveOrderColumn'.

### ATTACK RESULTS (all exit 1 = REJECTED; wit exit 0 = spec provably refutes it):
atk_1 reject-all / PREPATCH BUG re-encoded (impl byte-identical to Solution_prepatch.lean modulo comments, no sorry): unconditional noMatch on exhaust. wit_1 exit 0. atk_2 PARTIAL DOMAIN: the whole isRef=true slice unimplemented (immediate abort). wit_2 exit 0. atk_3 BOUNDARY: trailing dispatch reads resultCols.head? instead of getLast?

(first vs last visited column's alias). wit_3 exit 0. atk_4 CONTROL-FLOW EFFECT: the undetermined-label stop discards the first append, returning aborted q instead of the between-the-appends partial state. wit_4 exit 0. atk_5 CONTROL-FLOW EFFECT: peels a reference wrapper on EVERY visited column when isRef, not only on the column whose alias that wrapper names. wit_5 exit 0. atk_6 UNGROUNDED-ORACLE ECHO: delegates to the spec's own resolveOutcome except on an EMPTY scanned list, where it reports a position instead of stopping -- targets refinement row 7b (the real UnboundLocalError). Rejected, so 7b is non-vacuously pinned. wit_6 exit 0. atk_7 label-in-match-test: reads the value label as part of the match test (full-view structural equality instead of identity-only sameExpr).

This is the exact reading G-PANEL-2 flagged; it is rejected. wit_7 exit 0. atk_8 anonymous-as-empty-name: appends some "" instead of none for an expression contributing no name. wit_8 exit 0. atk_9 BOUNDARY / WRONG LIST: measures the add position off resultCols rather than querySelect. wit_9 exit 0. atk_10 A-REFERENCE ATTACK: reads the referenced alias off the ORIGINAL term rather than the carried one (substitute-but-keep-the-original-name). Refuted with a depth-2 chain witness. wit_10 exit 0.

**POSITIVE CONTROL.** pos_control.lean: pure functional impl (no do-block/for/mut) with the trailing dispatch branches INVERTED and the alias test taken negatively. lean_verify.sh exit 0. #print axioms correct_resolveOrderColumn -> [propext, Classical.choice, Quot.sound] -- no sorryAx. Gold Solution.lean prints the identical axiom set. So the spec is not over-fit to the imperative shape.

A-LEG AUDIT (the assigned focus). refinement.md declares NO A-tagged rows: the census is 13 R + 2 I over ops 1,2,2b,3,4,5,6,7,7b,8,9a,9b,9c,9d,10, with zero kind-3 legs and G-AX recorded as skip ('no consumed axioms in bundle'). That claim is only as good as the deep model's correspondence to the real callee, so I re-measured it independently rather than trusting the bundle's own conformance_check.py. I extracted the patched combinator suite from the REAL instance container (swebench/sweb.eval.x86_64.django_1776_django-10554 with patch.diff applied) and ran 17 probes over real Col/Ref/Value/Random/RawSQL objects and a real Query, then asserted the Lean model's resolveOutcome equals each measured outcome by `decide` in aleg_lean.lean -- exit 0, all 17 pass. Confirmed legs:

(1) `==` reads identity ONLY -- Col('t0',app_label) == Col('t0',username) is True with labels app_label vs username, and the real scan RESOLVES AT 1 there, matching sameExpr's id-only test (this is the G-PANEL-2 divergence; the current carrier handles it, and atk_7 shows the old full-view reading is rejected);

(2) rows 9a+9b -- both appends land, in that order, values_select gets 'username';

(3) row 9d -- Value(1).output_field raises FieldError BETWEEN the appends, leaving select grown and values_select untouched;

(4) row 7b -- an empty scanned list raises UnboundLocalError with nothing mutated;

(5) rows 7/8 -- the trailing alias is the LAST visited entry's (aliased-last -> noMatch, unaliased-last -> add path);

(6) rows 2b/3/4 -- a depth-2 Ref chain peels TWICE off the CARRIED term and then halts, Ref is never == its source, and Ref.output_field delegates to its source;

(7) hasAlias is TRUTH not presence -- a present-but-empty alias is compared and takes the add path;

(8) Random().output_field.name is None so the anonymous leg appends none, not the empty string. Also probed 8 further boundary shapes (Ref with .refs None or '', aliasMatch firing without a column match so the scan proceeds and re-reads the halt guard, isRef=false over a Ref term, peel-then-match-same-column, second-column peel, RawSQL label, non-reference term under isRef) -- all agree with the model. Model-patch correspondence therefore holds on every leg I could measure.

RESOLVE RUNS (executed, not speculated). No attack verified, so no attack REQUIRED a resolve run; I ran two anyway to establish the oracle can actually discriminate here, since a non-discriminating oracle would make any future candidate's resolve outcome meaningless. patch_atk_1.diff, atk_1's faithful refinement (prepatch shape: add_select_col added but the no-match case still raises unconditionally): run_resolve -> completed=true, resolved=FALSE, 3 consistent attempts, both F2P tests fail, all 23 P2P pass. (b) patch_model_faithful.diff, a structurally different transliteration of the Lean resolveOutcome (explicit while-scan carrying src, then the trailing dispatch incl. the empty-scan stop and the label-less stop): run_resolve -> completed=true, resolved=TRUE, attempts=1, FAIL_TO_PASS 2/2 and PASS_TO_PASS 23/23. So on this instance verify=>correct is corroborated in the one direction available, and the oracle demonstrably refutes a wrong impl.

**WHY NO BREAK IS AVAILABLE.** The postcondition's first conjunct is exact functional equality, result = resolveOutcome q isRef src, over a total transparent carrier with no axioms and no opaque callee. Any impl differing from resolveOutcome at even one input is refuted by decidable evaluation there, which is exactly what the 10 witnesses demonstrate. A G-EQ break therefore cannot come from a weak obligation; it could only come from resolveOutcome itself mismodelling the real callee, which is a model-fidelity (G-CONF/G-AX) question. I attacked precisely that surface with atk_6 (echo the reference but diverge on the empty-scan leg), atk_7 (the panel's own identity/label divergence) and atk_10 (the reference-stack reading), and independently re-measured all 17 correspondence points against the real container -- none diverged.

**ARTIFACTS.** atk_1..atk_10.lean (+ .log/.rc), wit_1..wit_10.lean (+ .log/.rc), pos_control.lean, pos_axioms.lean, gold_axioms.lean, aleg.py, aleg2.py, aleg_lean.lean, patch_atk_1.diff, patch_model_faithful.diff, res_atk1.json, res_model.json, gen.py, mkpatch.py -- all under 

**VERDICT SOUND:** 10 distinct same-spec wrong impls (>= the 5 required, covering partial-domain, boundary, control-flow-effect and ungrounded-oracle-echo classes, including the prepatch bug), every one rejected with a machine-checked refutation witness; positive control verifies with clean axioms; refinement.md is all R/I with no kind-3 legs and its A-equivalent correspondence claims re-measured against the real callee; both resolve runs completed and behaved as the spec predicts.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 admissible attacks re-run of 10 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong implementation closed correct_resolveOrderColumn, so there is no verifying attack whose faithful patch could exhibit verify-does-not-imply-correct. All 10 attacks were REJECTED (lean_verify.sh exit 1), each additionally backed by a machine-checked refutation witness (wit_N.lean, exit 0) proving the postcondition is FALSE at a concrete input for that impl -- so each attack is genuinely unprovable, not merely failing to reapply gold's tactic body. Positive control verifies (exit 0, clean axioms) with a structurally different impl shape. Oracle discriminating power confirmed by EXECUTED resolve runs: the prepatch-shaped faithful patch does NOT resolve (completed=true, resolved=false, 3 consistent attempts, both F2P fail), while a model-faithful transliteration of resolveOutcome DOES resolve (completed=true, resolved=true, 2/2 F2P + 23/23 P2P).
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
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
    (q : QueryCols) (isRef : Bool) (src : OrderSrc) : OrderByOutcome :=
  -- POSITIVE CONTROL: a structurally different but CORRECT impl -- pure
  -- functional form (no do-block / for / mut), with the trailing dispatch's
  -- branches written in the INVERTED order and the alias test taken negatively.
  match scanCols isRef 0 src q.resultCols with
  | ScanResult.atPos pos => OrderByOutcome.resolved pos q
  | ScanResult.halted => OrderByOutcome.aborted q
  | ScanResult.exhausted finalCur =>
    match q.resultCols.getLast? with
    | none => OrderByOutcome.aborted q
    | some lastCol =>
        if !hasAlias lastCol.colAlias then addedOutcome q finalCur
        else OrderByOutcome.noMatch
-- impl-end

-- proof-start
/-- Pure recursion mirroring exactly one iteration of the imperative `for`-loop
followed by the trailing `getLast?` dispatch: over a suffix `cs` of the result
columns, carrying the term `cur` with the wrappers met so far removed and the
0-based index `idx`, while the FULL outer column state `q` is used for the
resolved/extend payload. -/
def loopBody (isRef : Bool) (q : QueryCols) :
    Nat → OrderSrc → List SelCol → OrderByOutcome
  | _idx, cur, [] =>
    match q.resultCols.getLast? with
    | some lastCol =>
        if hasAlias lastCol.colAlias then
          OrderByOutcome.noMatch
        else
          addedOutcome q cur.compared
    | none => OrderByOutcome.aborted q
  | idx, cur, col :: rest =>
    if isRef && cur.refs?.isNone then
      OrderByOutcome.aborted q
    else
      let aliasMatch := isRef && cur.refs? == some col.colAlias
      let cur' := if aliasMatch then cur.stripped else cur
      if (aliasMatch || !hasAlias col.colAlias) && cur'.compared.sameExpr col.expr then
        OrderByOutcome.resolved (idx + 1) q
      else
        loopBody isRef q (idx + 1) cur' rest

/-- The `Id.run` for-loop over a suffix `cs` starting from mutable state
`(cur0, idx0)`, followed by the trailing `getLast?` dispatch, computes exactly
`loopBody`.  Proven by induction on `cs`, unfolding one `forIn` step at a time
(`List.forIn_cons`/`List.forIn_nil`), observing that a `return x` inside the body
becomes `ForInStep.done x` and a fall-through becomes `.yield` of the updated
state.  The outer `q` stays fixed as the resolved/extend payload. -/
theorem forIn_cons_unfold (isRef : Bool) (q : QueryCols) :
    ∀ (cs : List SelCol) (cur0 : OrderSrc) (idx0 : Nat),
      (Id.run do
        let mut cur : OrderSrc := cur0
        let mut idx : Nat := idx0
        for col in cs do
          if isRef && cur.refs?.isNone then
            return OrderByOutcome.aborted q
          let aliasMatch := isRef && cur.refs? == some col.colAlias
          if aliasMatch then
            cur := cur.stripped
          if (aliasMatch || !hasAlias col.colAlias) && cur.compared.sameExpr col.expr then
            return OrderByOutcome.resolved (idx + 1) q
          idx := idx + 1
        match q.resultCols.getLast? with
        | some lastCol =>
            if hasAlias lastCol.colAlias then
              return OrderByOutcome.noMatch
            else
              return addedOutcome q cur.compared
        | none => return OrderByOutcome.aborted q)
        = loopBody isRef q idx0 cur0 cs := by
  intro cs
  induction cs with
  | nil =>
    intro cur0 idx0
    rfl
  | cons col rest ih =>
    intro cur0 idx0
    simp only [List.forIn_cons, loopBody]
    split_ifs with h0 h1 h2 h2 <;>
      simp only [Id.run, bind_pure_comp, pure_bind, map_pure] <;>
      first
        | rfl
        | (exact ih _ _)

/-- Core refinement: `loopBody` over `cs` from state `(cur, idx)` equals the
`scanCols` result dispatched identically to `resolveOutcome`'s body — the early
`atPos pos` becomes `resolved pos q`, `halted` becomes a stop with `q` untouched,
and the fall-through `exhausted finalCur` runs the identical `getLast?`/extend
dispatch on the outer `q`. -/
theorem loop_eq_scanCols (isRef : Bool) (q : QueryCols) :
    ∀ (cs : List SelCol) (cur : OrderSrc) (idx : Nat),
      loopBody isRef q idx cur cs
        = (match scanCols isRef idx cur cs with
           | ScanResult.atPos pos => OrderByOutcome.resolved pos q
           | ScanResult.halted => OrderByOutcome.aborted q
           | ScanResult.exhausted finalCur =>
               match q.resultCols.getLast? with
               | some lastCol =>
                   if hasAlias lastCol.colAlias then
                     OrderByOutcome.noMatch
                   else
                     addedOutcome q finalCur
               | none => OrderByOutcome.aborted q) := by
  intro cs
  induction cs with
  | nil =>
    intro cur idx
    simp [loopBody, scanCols, addedOutcome, withNewResultCol, withPartialResultCol]
  | cons col rest ih =>
    intro cur idx
    unfold loopBody scanCols
    by_cases hs : isRef && cur.refs?.isNone
    · simp only [hs, if_true]
    · simp only [hs, if_false, Bool.false_eq_true]
      by_cases h : (isRef && cur.refs? == some col.colAlias || !hasAlias col.colAlias) &&
          (if isRef && cur.refs? == some col.colAlias then cur.stripped else cur).compared.sameExpr
            col.expr
      · simp only [h, if_true]
      · simp only [h]
        exact ih _ _

/-- A matching column's reported position is a genuine 1-based ordinal of a
result column the scan has actually visited: strictly above the starting index
and no further than the end of the scanned suffix. -/
theorem scanCols_bound (isRef : Bool) :
    ∀ (cs : List SelCol) (idx : Nat) (cur : OrderSrc) (pos : Nat),
      scanCols isRef idx cur cs = ScanResult.atPos pos →
      idx < pos ∧ pos ≤ idx + cs.length := by
  intro cs
  induction cs with
  | nil =>
    intro idx cur pos h
    simp [scanCols] at h
  | cons col rest ih =>
    intro idx cur pos h
    unfold scanCols at h
    by_cases hs : isRef && cur.refs?.isNone
    · rw [if_pos hs] at h
      simp at h
    · rw [if_neg hs] at h
      by_cases hg : (isRef && cur.refs? == some col.colAlias || !hasAlias col.colAlias) &&
          (if isRef && cur.refs? == some col.colAlias then cur.stripped else cur).compared.sameExpr
            col.expr
      · rw [if_pos hg] at h
        have hp : pos = idx + 1 := by
          simpa using (ScanResult.atPos.inj h).symm
        subst hp
        simp
      · rw [if_neg hg] at h
        have := ih (idx + 1) _ pos h
        refine ⟨by omega, by simpa [List.length_cons] using by omega⟩

/-- The usability guarantee, proven of the reference outcome itself: on a column
state whose two query-side parts correspond, a reported position is a genuine
1-based ordinal of the list it belongs to and the resulting state still
corresponds, and a stop leaves the labels alone. The match leg leaves the query
column state untouched and uses `scanCols_bound` to place the position inside the
result columns; the extend leg grows the query column state by exactly one
column, and the reported position is that column's ordinal there, correspondence
being maintained because the column and its label are added together; the stop
after the first append leaves the labels alone by construction, as does the stop
where the scan visited no column at all. -/
theorem resolveOutcome_usable (q : QueryCols) (isRef : Bool) (src : OrderSrc)
    (hq : inCorrespondence q = true) :
    outcomeUsable q (resolveOutcome q isRef src) = true := by
  unfold resolveOutcome
  cases hscan : scanCols isRef 0 src q.resultCols with
  | atPos pos =>
    have hb := scanCols_bound isRef q.resultCols 0 src pos hscan
    have h1 : 1 ≤ pos := by omega
    have h2 : pos ≤ q.resultCols.length := by simpa using hb.2
    simp [outcomeUsable, hq, h1, h2]
  | halted => simp [outcomeUsable]
  | exhausted finalCur =>
    unfold inCorrespondence at hq
    simp only [beq_iff_eq] at hq
    have hadd : outcomeUsable q (addedOutcome q finalCur) = true := by
      unfold addedOutcome
      cases hlab : finalCur.label with
      | name s =>
        simp [outcomeUsable, withNewResultCol, inCorrespondence, hq]
      | anonymous =>
        simp [outcomeUsable, withNewResultCol, inCorrespondence, hq]
      | undetermined =>
        simp [outcomeUsable, withPartialResultCol]
    cases hlast : q.resultCols.getLast? with
    | none => simp [outcomeUsable]
    | some lastCol =>
      by_cases ha : hasAlias lastCol.colAlias
      · simp [ha, outcomeUsable]
      · simpa [ha] using hadd

theorem correct_resolveOrderColumn :
    ∀ (q : QueryCols) (isRef : Bool) (src : OrderSrc),
      problem_spec_resolveOrderColumn q isRef src
        (implementation_resolveOrderColumn q isRef src) := by
  intro q isRef src
  have himpl : implementation_resolveOrderColumn q isRef src = resolveOutcome q isRef src := by
    unfold implementation_resolveOrderColumn resolveOutcome
    cases scanCols isRef 0 src q.resultCols with
    | atPos pos => rfl
    | halted => rfl
    | exhausted finalCur =>
      cases q.resultCols.getLast? with
      | none => rfl
      | some lastCol => by_cases ha : hasAlias lastCol.colAlias <;> simp [ha]
  refine ⟨himpl, ?_⟩
  intro hq
  rw [himpl]
  exact resolveOutcome_usable q isRef src hq
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Repo cloned at base_commit 14d026cccb144c6877294ba4cd4e03ebf0842498. Attacks built by copying Solution.lean and editing ONLY the impl region; same_spec=True verified for all 10 via swebench_unified.markers.same_spec, and re-confirmed by the official adversary.check_attack (same_spec=True, admissible=True, verifies=False, verify_completed=True for all 10; positive_control verifies=True).

**COMMANDS.** Per attack: bash scripts/lean_verify.sh atk_N.lean  (run 4-way concurrent as background jobs). Per witness: same command on wit_N.lean. Axioms: gold_axioms.lean and pos_axioms.lean append '#print axioms correct_resolveOrderColumn'.

### ATTACK RESULTS (all exit 1 = REJECTED; wit exit 0 = spec provably refutes it):
atk_1 reject-all / PREPATCH BUG re-encoded (impl byte-identical to Solution_prepatch.lean modulo comments, no sorry): unconditional noMatch on exhaust. wit_1 exit 0. atk_2 PARTIAL DOMAIN: the whole isRef=true slice unimplemented (immediate abort). wit_2 exit 0. atk_3 BOUNDARY: trailing dispatch reads resultCols.head? instead of getLast?

(first vs last visited column's alias). wit_3 exit 0. atk_4 CONTROL-FLOW EFFECT: the undetermined-label stop discards the first append, returning aborted q instead of the between-the-appends partial state. wit_4 exit 0. atk_5 CONTROL-FLOW EFFECT: peels a reference wrapper on EVERY visited column when isRef, not only on the column whose alias that wrapper names. wit_5 exit 0. atk_6 UNGROUNDED-ORACLE ECHO: delegates to the spec's own resolveOutcome except on an EMPTY scanned list, where it reports a position instead of stopping -- targets refinement row 7b (the real UnboundLocalError). Rejected, so 7b is non-vacuously pinned. wit_6 exit 0. atk_7 label-in-match-test: reads the value label as part of the match test (full-view structural equality instead of identity-only sameExpr).

This is the exact reading G-PANEL-2 flagged; it is rejected. wit_7 exit 0. atk_8 anonymous-as-empty-name: appends some "" instead of none for an expression contributing no name. wit_8 exit 0. atk_9 BOUNDARY / WRONG LIST: measures the add position off resultCols rather than querySelect. wit_9 exit 0. atk_10 A-REFERENCE ATTACK: reads the referenced alias off the ORIGINAL term rather than the carried one (substitute-but-keep-the-original-name). Refuted with a depth-2 chain witness. wit_10 exit 0.

**POSITIVE CONTROL.** pos_control.lean: pure functional impl (no do-block/for/mut) with the trailing dispatch branches INVERTED and the alias test taken negatively. lean_verify.sh exit 0. #print axioms correct_resolveOrderColumn -> [propext, Classical.choice, Quot.sound] -- no sorryAx. Gold Solution.lean prints the identical axiom set. So the spec is not over-fit to the imperative shape.

A-LEG AUDIT (the assigned focus). refinement.md declares NO A-tagged rows: the census is 13 R + 2 I over ops 1,2,2b,3,4,5,6,7,7b,8,9a,9b,9c,9d,10, with zero kind-3 legs and G-AX recorded as skip ('no consumed axioms in bundle'). That claim is only as good as the deep model's correspondence to the real callee, so I re-measured it independently rather than trusting the bundle's own conformance_check.py. I extracted the patched combinator suite from the REAL instance container (swebench/sweb.eval.x86_64.django_1776_django-10554 with patch.diff applied) and ran 17 probes over real Col/Ref/Value/Random/RawSQL objects and a real Query, then asserted the Lean model's resolveOutcome equals each measured outcome by `decide` in aleg_lean.lean -- exit 0, all 17 pass. Confirmed legs:

(1) `==` reads identity ONLY -- Col('t0',app_label) == Col('t0',username) is True with labels app_label vs username, and the real scan RESOLVES AT 1 there, matching sameExpr's id-only test (this is the G-PANEL-2 divergence; the current carrier handles it, and atk_7 shows the old full-view reading is rejected);

(2) rows 9a+9b -- both appends land, in that order, values_select gets 'username';

(3) row 9d -- Value(1).output_field raises FieldError BETWEEN the appends, leaving select grown and values_select untouched;

(4) row 7b -- an empty scanned list raises UnboundLocalError with nothing mutated;

(5) rows 7/8 -- the trailing alias is the LAST visited entry's (aliased-last -> noMatch, unaliased-last -> add path);

(6) rows 2b/3/4 -- a depth-2 Ref chain peels TWICE off the CARRIED term and then halts, Ref is never == its source, and Ref.output_field delegates to its source;

(7) hasAlias is TRUTH not presence -- a present-but-empty alias is compared and takes the add path;

(8) Random().output_field.name is None so the anonymous leg appends none, not the empty string. Also probed 8 further boundary shapes (Ref with .refs None or '', aliasMatch firing without a column match so the scan proceeds and re-reads the halt guard, isRef=false over a Ref term, peel-then-match-same-column, second-column peel, RawSQL label, non-reference term under isRef) -- all agree with the model. Model-patch correspondence therefore holds on every leg I could measure.

RESOLVE RUNS (executed, not speculated). No attack verified, so no attack REQUIRED a resolve run; I ran two anyway to establish the oracle can actually discriminate here, since a non-discriminating oracle would make any future candidate's resolve outcome meaningless. patch_atk_1.diff, atk_1's faithful refinement (prepatch shape: add_select_col added but the no-match case still raises unconditionally): run_resolve -> completed=true, resolved=FALSE, 3 consistent attempts, both F2P tests fail, all 23 P2P pass. (b) patch_model_faithful.diff, a structurally different transliteration of the Lean resolveOutcome (explicit while-scan carrying src, then the trailing dispatch incl. the empty-scan stop and the label-less stop): run_resolve -> completed=true, resolved=TRUE, attempts=1, FAIL_TO_PASS 2/2 and PASS_TO_PASS 23/23. So on this instance verify=>correct is corroborated in the one direction available, and the oracle demonstrably refutes a wrong impl.

**WHY NO BREAK IS AVAILABLE.** The postcondition's first conjunct is exact functional equality, result = resolveOutcome q isRef src, over a total transparent carrier with no axioms and no opaque callee. Any impl differing from resolveOutcome at even one input is refuted by decidable evaluation there, which is exactly what the 10 witnesses demonstrate. A G-EQ break therefore cannot come from a weak obligation; it could only come from resolveOutcome itself mismodelling the real callee, which is a model-fidelity (G-CONF/G-AX) question. I attacked precisely that surface with atk_6 (echo the reference but diverge on the empty-scan leg), atk_7 (the panel's own identity/label divergence) and atk_10 (the reference-stack reading), and independently re-measured all 17 correspondence points against the real container -- none diverged.

**ARTIFACTS.** atk_1..atk_10.lean (+ .log/.rc), wit_1..wit_10.lean (+ .log/.rc), pos_control.lean, pos_axioms.lean, gold_axioms.lean, aleg.py, aleg2.py, aleg_lean.lean, patch_atk_1.diff, patch_model_faithful.diff, res_atk1.json, res_model.json, gen.py, mkpatch.py -- all under 

**VERDICT SOUND:** 10 distinct same-spec wrong impls (>= the 5 required, covering partial-domain, boundary, control-flow-effect and ungrounded-oracle-echo classes, including the prepatch bug), every one rejected with a machine-checked refutation witness; positive control verifies with clean axioms; refinement.md is all R/I with no kind-3 legs and its A-equivalent correspondence claims re-measured against the real callee; both resolve runs completed and behaved as the spec predicts.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** FAITHFULNESS-BREAK attack on django__django-10554 Solution.lean. No divergence found between the modeled function and the real patched callee, on ~215k randomized + ~32k exhaustive differential cases and 700 checks evaluated against the ACTUAL Lean definitions. Verdict FAITHFUL.

### Mechanical checks
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- `#print axioms correct_resolveOrderColumn` -> [propext, Classical.choice, Quot.sound]. No sorryAx; proof is real.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, get_backend('lean')) -> True. Spec region (axioms/pure/pre/post) is byte-identical across the gold/prepatch pair, so the prepatch rival is refuted by the same spec text.

### Reference discipline
I took the modeled function's reference to be the base-commit worktree with patch.diff APPLIED (fresh worktree at 14d026cccb144c6877294ba4cd4e03ebf0842498, `git apply patch.diff` -> clean). I did NOT score the patch delta itself as divergence. Base commit was used only for the untouched callees the bridge reads: BaseExpression.identity/`__eq__` and Ref.output_field delegation in django/db/models/expressions.py.

### INDEPENDENT ORACLE (not the bundle's harness)
I built my own oracle rather than trusting conformance_check.py: sliced the `for idx, (sel_expr, _, col_alias) in enumerate(self.select):` suite and its `else:` verbatim out of the PATCHED compiler.py, compiled it in a copy of that module's own globals, and ran it over real Col/Ref/Value/RawSQL/Random objects against a real Query whose add_select_col is the real patched helper. Extraction asserts guard all nine landmarks (realias, `elif col_alias:`, `src == sel_expr`, the else-suite `if col_alias:`, the DatabaseError, add_select_col, `len(self.query.select)`) plus the helper's two lines, so an unpatched repo fails extraction instead of silently passing. I also wrote my own transliteration of the Lean pure region and my own ==-quotient computation.

### BRIDGE CLAIMS I RE-DERIVED FROM SCRATCH (all held)
1. ==-quotient EXACT, not injective: over my 162-object pool (120 classes) and again over the exhaustive set, `(a==b) == (ID[a]==ID[b])` for all ordered pairs -> 0 violations. Confirms QExpr.sameExpr := a.id == b.id is exactly the callee's ==.
2. Collapsed class is IN domain: Col('t0',app_label) == Col('t0',username) is True while labels are 'app_label'/'username'. 21 pool classes carry >1 label. This is the shape a pairwise-unequal pool assertion would have excluded.
3. Ref.output_field delegates: for every pool member, label_of(e) == label_of(innermost non-Ref base) -> 0 violations at depths {0:13,1:65,2:60,3:24}. Confirms OrderSrc.compared carrying the BASE's label with the WRAPPER's identity.
4. A Ref is never == its source -> the one shape mapping.md admits but the callee cannot build is a strict SUPERSET of the callee's domain (safe over-approximation, not unsoundness).

### Differential results
- Randomized fuzz, my own generator, 6 seeds (10554/1/7/99/31337/424242/987654), 215k cases total: 0 mismatches on the tuple (outcome class, position, querySelect AS FULL VIEW incl. label, valuesSelect). All six outcome classes reached every run (resolved-match, resolved-added, noMatch, aborted-unbound, aborted-refs, aborted-nolabel).
- Exhaustive small-space search over |select| in 0..2 x 9 expressions x 4 aliases x is_ref x 12 sources = 31,992 cases: 0 mismatches, all six classes hit.
- **NON-VACUITY:** a `structural` control shadow (full-view equality substituted for sameExpr) DISAGREES with the real code on 141-392 cases per run, and 224-591 collapsed-class matches were actually drawn. So identity-only matching is discriminated from label-comparing matching by measurement, not assumed.
- Usability conjunct checked OF THE REAL ORACLE'S OWN RESULT (not the model's) on every input arriving in correspondence: 0 breaks.

### LEAN-LEVEL CONFIRMATION (closes the 'my transliteration might be wrong' gap)
Generated Lean files importing the gold spec's pure region verbatim and `by decide`-checking resolveOutcome against the REAL suite's measured outcome on real-object-derived inputs: 300 checks (seed 777) -> exit 0; 400 class-biased checks (seed 4242, all six classes incl. aborted-nolabel and resolved-match) -> exit 0. Plus a dedicated Collapse.lean proving resolveOutcome resolves 1 with state untouched on the collapsed pair, that the two QExprs are NOT equal as full views, and that sameExpr is true of them -> exit 0.

### HIGH-RISK LEGS PROBED DIRECTLY AGAINST REAL CODE (all matched the model)
- aborted-nolabel lands BETWEEN the helper's two appends: query.select grew to 2, values_select stayed ('app_label',). Exactly withPartialResultCol.
- anonymous label: RawSQL and Random both -> values_select == (None,). Exactly OutputLabel.anonymous |-> none.
- present-but-EMPTY alias '': trailing entry with alias '' and no match ADDS rather than raising, so hasAlias(some "") = false is the truth test, not a presence test.
- multi-realias stack: depth-2 term Ref('y',Ref('s',X)) over select [('y'),('s'=X)] -> real resolves 2; depth-3 -> real resolves 3; the variant whose 's' entry holds Ref('s',X) -> real noMatch. Model agrees on all three, refuting the single-flag rival panel repair 2 removed.
- empty scanned list, both is_ref values -> aborted-unbound (UnboundLocalError), NOT noMatch. Confirms the `| none => aborted q` leg is the right outcome and not the deliberate DatabaseError.
- two-list separation: I confirmed the scan indexes self.select while add_select_col appends to and len() is read off self.query.select, so resultCols vs querySelect/valuesSelect is the correct split (this is what panel repair 1 fixed and it holds).

### Attack angles that failed to produce a counterexample
Too-strong postcondition: outcomeUsable's aborted leg only demands resultCols/valuesSelect preserved and querySelect grown by <=1 — the real aborted-nolabel state satisfies this exactly; no real stop violates it. Too-strong match test: tried to find an input where real == disagrees with id-equality — the quotient is exact, so none exists in the pool. Too-strong add leg: tried labels the model cannot represent — output_field.name is only str/None/FieldError, exactly the three OutputLabel constructors. Domain over-reach is one-directional (superset), which cannot make the spec unfaithful.

**CONCLUSION:** I could not construct any input on which the modeled function disagrees with the real patched callee. The spec is not too strong and does not drift from repo behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** django__django-10554 lean bundle, leakage/gold-reconstruction layer. NO RELAXATION CLAIMED: meta.json has no `relaxed_leakage` key and there is no RELAXED_LEAKAGE.md anywhere in the bundle dir, so the relaxed-leakage branch is moot here -- I judged this as an ordinary strict-mode leakage review and everything below is my own measurement, not an inherited disposition.

### WHAT I RAN (all from swe-proof, PYTHONPATH=src, backend LeanBackend):
1. **SPEC REGION IDENTITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True, and stronger -- markers.spec_view() of the two files is BYTE-identical (a==b True), not merely signature-equal. So the consumer-visible spec view is provably incapable of discriminating post- from pre-patch impl; the discriminator lives wholly in the elided impl region. markers.region_hashes() recomputed on the shipped Solution.lean matches the G-HYGIENE stamp's region_hashes exactly (spec_view 26ed1ab205c4..., pure 103320bf..., post-conditions 37414ece..., axioms 50d3f8f4...). NOTE: the top-level meta.json `region_hashes` block (spec_view 37ebd4ac...) disagrees with both -- it is a stale sibling block; the in-gate G-HYGIENE copy is the fresh one. Hygiene/stamp matter, not a leak.
2. LEAN SOUNDNESS (so the gates I lean on are not vacuous): scripts/lean_verify.sh on shipped Solution.lean -> exit 0 in 17s. `#print axioms correct_resolveOrderColumn` -> [propext, Classical.choice, Quot.sound]. NO sorryAx, so the proof is real, not fake. Solution_prepatch.lean -> exit 3, "declaration uses 'sorry'" at line 363, i.e. G-DIFF/G-GOLD are genuinely discriminating (pre-patch impl cannot be proven against this spec). Zero axioms/opaque callees in the bundle (meta axioms=[], opaque_callees=[]), so G-AX's skip is honest -- there is no axiom surface to over-claim through.
3. MECHANICAL LEAK SCREEN, re-run by me not inherited: leakage.screen(Solution.lean, LeanBackend, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Reproduces the G-LEAK stamp (which carries the CURRENT Solution.lean digest 67f67afd...).
4. GOLD-LINE REPRODUCTION, per line, whitespace-normalized: all 10 changed lines of the gold patch checked against the normalized spec view -- every one hit=False, including the two longest/most distinctive (`raise DatabaseError('ORDER BY term does not match any column in the result set.'` len 69, `resolved.set_source_expressions([RawSQL('%d' % len(self.query.select), ())])` len 73). No diff markers (@@, diff --git, +++, index) present.
5. REPO-SYMBOL ECHO, run STRICTER than the gate: I tokenized every gold changed line and tested each token >=4 chars, underscore-stripped and case-folded, against (a) every spec-view identifier and (b) the concatenated spec-view comment/docstring text. The three patch def-symbols (`add_select_col`, `get_order_by`, `clear_select_fields`) appear NOWHERE -- 0 occurrences in spec view for add_select/select_col/values_select/output_field/DatabaseError/col_alias/RawSQL/get_order_by/clear_select_fields/'%d'/compiler/query.py, and 0 for django/Django/sql/SQL. The only surviving echoes are `col_alias`->`colAlias` and `values_select`->`valuesSelect`. I checked these against the real repo worktree (git HEAD 14d026cccb144c6877294ba4cd4e03ebf0842498 == instance base_commit): both are PRE-EXISTING symbols at base (col_alias 6 occurrences in compiler.py, values_select 3 in query.py), i.e. they name the data model the function already reads, not anything the fix invents. Naming a pre-existing carrier field localizes no edit -- the solver still cannot tell from `valuesSelect` existing whether the fix appends to it. Nothing in the fix's invented vocabulary leaks.
6. NARRATION / DIAGNOSIS: grepped the spec view for instead/no longer/used to/now/formerly/change/error/raise/crash/fail/'position N not in' and for the issue-specific vocabulary from the problem_statement (Dimension, queryset/QuerySet, order_by, values_list, pk__in, ProgrammingError, 'select list', 'position 4', copy(), re-evaluat). All 0 except abstract structural uses of "fails"/"instead" describing the CONTRACT's own case split (line 68 "resolution fails", line 82 "stops instead of reporting a position"), which are outcome names, not bug->fix narration. The pre-patch model DOES carry an explicit "PRE-PATCH BUG:" comment, but I confirmed it sits inside the impl region and is elided: 'PRE-PATCH' in spec_view = False for both files. No before/after contrast, no diagnosis, no mention of the union/derived-queryset reproduction.
7. **GOLD RECONSTRUCTION JUDGEMENT:** the spec view does state the post-fix contract in the abstract -- on no match, if the last-visited result column carries no alias, append the compared expression to the query's selected columns, append its value label to the label list, and report the new trailing ordinal. That IS the behavior the gold implements, but stating the desired behavior is a spec's entire job and is what the consumer is entitled to under eval_mode_1 (the consumer is asked to produce BOTH a model and a repo patch from this contract). It is expressed purely over the bundle's own modeled carriers (QueryCols/OrderSrc/SelCol/OutputLabel), never as the edit: no patched file, no patched function, no invented symbol, no diff line, no statement of what the code did before. Abstract desired behavior, not the edit or the diagnosis -- exactly the line spec_guide.md rule 6 draws.

GATE-FRESHNESS AUDIT (does my verdict rest on a sound disposition): I recomputed sha256 of all five gate source files and cross-checked every gate's `sources` block. Every gate I lean on carries the CURRENT digests: G-LEAK, G-HYGIENE, G-GOLD, G-DIFF, G-VERIFY, G-CONF, G-INTEGRITY, G-MUT, G-AX, G-PBT, G-RESOLVE all src-ok against Solution.lean 67f67afd... G-EQ and the G-PANEL* stamps are STALE (they cite Solution.lean 948fdba7... and, for G-EQ, properties.py 860b012b... vs current 80e66cb0...) -- those predate the third documented panel repair. This does not soften my verdict: I re-measured same_spec, spec_view byte-identity, the leak screen, verify, prepatch-fails, and #print axioms MYSELF on the shipped 67f67afd... artifact, so the NO-LEAKAGE finding is my own measurement on the current file, not a re-stamp of the stale panel record. The stale G-EQ/G-PANEL stamps are a stamp-freshness matter for whoever owns G-INTEGRITY.

BUNDLE-ADDRESSES-THE-AUDITOR CHECK (reported as a finding in its own right per my instructions): I grepped mapping.md, refinement.md and verdict.md for auditor/panel/reviewer/attacker/NO-LEAKAGE/submit_result/'honest verdict'/'do not flag'. NOTHING in this bundle instructs me how to record or which verdict to reach. refinement.md's "What the Nth panel repair changed" sections and verdict.md's line 15340 record of a PRIOR panel-3 run (which also submitted NO-LEAKAGE and flagged the same stale-stamp observation) are historical records of earlier reviews, not instructions addressed at me. I reached my verdict independently and did not rely on that prior run; the agreement is corroboration, not inheritance. No attempt at auditor capture found.

**VERDICT:** NO-LEAKAGE. The spec view is byte-identical across the post/pre pair, reproduces no gold line, names no patched file or fix-invented symbol, echoes only two pre-existing base-commit field names, carries no bug->fix narration, and the proof backing the gates is real (clean #print axioms, prepatch genuinely fails).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
