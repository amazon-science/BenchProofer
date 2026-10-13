import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The only callee whose behaviour the proof depends on is
-- the recursive name-collector `referencedNames` (the pure region), which is a
-- DEEP MODEL (A-reference) validated against its real counterpart by G-AX
-- (axiom_check.py), not an opaque assumption. Every other dependency of the
-- query under spec (the structural flags, the membership-in-the-SELECT-set
-- predicate, the presence of a row-summarising or windowed prior alias entry)
-- is an explicit, observable input of the method, so it needs no axiom.
-- axioms-end

-- pure-start
/- A declared alias entry, abstracted to exactly the fields that decide the
   shape of a counting query: its `name`, whether it is part of the query's
   visible SELECT set (`selected`), and whether it itself summarises rows
   (`isAggregate`) or is a windowed expression (`isWindow`). -/
structure Annotation where
  name : String
  selected : Bool
  isAggregate : Bool
  isWindow : Bool
deriving Inhabited, DecidableEq

/- The shape of an expression for the purpose of collecting the alias names it
   refers to: a `reference` names exactly one alias; a `composite` is built out
   of sub-expressions and refers to whatever they do. -/
inductive Expr where
  | reference : String → Expr
  | composite : List Expr → Expr
deriving Inhabited

/- An alias entry that is being added for the summary itself: its `name` and the
   expression tree it is computed from. -/
structure Added where
  name : String
  expr : Expr
deriving Inhabited

/- The decided plan: whether the count needs to run inside a nested query, and
   the set of alias names retained in the produced SQL. -/
structure Plan where
  needsNesting : Bool
  keptNames : List String
deriving Inhabited, DecidableEq

/- The alias names an expression refers to: a reference contributes its single
   target name; a composite contributes the union (here concatenation —
   membership is all that is observed) of its parts. Written with an explicit
   list companion so a single structural unfold is available per element. -/
mutual
def referencedNames : Expr → List String
  | .reference s => [s]
  | .composite es => referencedNamesList es
def referencedNamesList : List Expr → List String
  | [] => []
  | e :: rest => referencedNames e ++ referencedNamesList rest
end

/- The retained-name fold for the added summary entries, front-recursive so
   one unfold is exposed per loop step: each added entry contributes its
   own name followed by every name it refers to. -/
def maskFold : List Added → List String
  | [] => []
  | a :: rest => (a.name :: referencedNames a.expr) ++ maskFold rest

@[grind] lemma maskFold_nil : maskFold [] = [] := rfl
@[grind] lemma maskFold_cons (a : Added) (rest : List Added) :
    maskFold (a :: rest) = (a.name :: referencedNames a.expr) ++ maskFold rest := rfl

/- A prior (already-declared) alias entry: one that is in the visible SELECT set
   and is NOT itself one of the names being added for the summary. -/
def isExisting (names : List String) (a : Annotation) : Bool :=
  a.selected && !(names.contains a.name)

/- A nested query is forced by a prior alias entry only when that entry itself
   summarises rows or is windowed — or when a row-summarising filter is
   present. A prior entry that is neither is harmless and is pruned. -/
def anyPriorAggregate (annos : List Annotation) (names : List String)
    (havingFilter : Bool) : Bool :=
  ((annos.filter (isExisting names)).any (fun a => a.isAggregate || a.isWindow))
    || havingFilter

/- The nesting decision: the structural triggers, OR a row-summarising prior
   alias entry / filter. -/
def needsNesting (annos : List Annotation) (names : List String)
    (groupByTuple isSliced distinct combinator havingFilter : Bool) : Bool :=
  groupByTuple || isSliced
    || anyPriorAggregate annos names havingFilter
    || distinct || combinator

/- The names retained in the produced SQL. When the count is nested and the
   query does NOT collapse duplicate rows: the added names together with
   everything they refer to (prior entries not referred to are dropped). When
   the count is nested but the query DOES collapse duplicate rows (`distinct`):
   pruning is suppressed — narrowing the visible entries could change which
   rows collapse — so every visible prior entry is retained alongside the
   added names. Otherwise (no nesting): just the added names (prior ones
   inlined away). -/
def keptNames (nesting distinct : Bool) (annos : List Annotation)
    (added : List Added) : List String :=
  if nesting then
    if distinct then
      added.map (·.name)
        ++ (annos.filter (isExisting (added.map (·.name)))).map (·.name)
    else maskFold added
  else added.map (·.name)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method countQueryShape
    (annos : List Annotation) (added : List Added)
    (groupByTuple : Bool) (isSliced : Bool) (distinct : Bool)
    (combinator : Bool) (havingFilter : Bool)
    return (res : Plan)
  ensures res.needsNesting =
    needsNesting annos (added.map (·.name))
      groupByTuple isSliced distinct combinator havingFilter
  ensures res.keptNames = keptNames res.needsNesting distinct annos added
  do
    -- impl-start
    let names := added.map (·.name)
    let existing := annos.filter (isExisting names)
    let priorAgg := (existing.any (fun a => a.isAggregate || a.isWindow)) || havingFilter
    let nesting := groupByTuple || isSliced || priorAgg || distinct || combinator
    let mut m : List String := []
    let mut i := added.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ added.length
      invariant m = maskFold (added.drop i)
      done_with i = 0
      decreasing i
    do
      let a := added[i - 1]!
      m := (a.name :: referencedNames a.expr) ++ m
      i := i - 1
    let kept :=
      if nesting then
        if distinct then names ++ existing.map (·.name) else m
      else names
    return { needsNesting := nesting, keptNames := kept }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `maskFold` peels one contribution. The single goal
   `loom_solve` leaves for the loop body. -/
lemma maskFold_drop_step (added : List Added) (i : Nat)
    (hi : 0 < i) (hle : i ≤ added.length) :
    maskFold (added.drop (i - 1))
      = ((added[i - 1]!).name :: referencedNames (added[i - 1]!).expr)
        ++ maskFold (added.drop i) := by
  have hlt : i - 1 < added.length := by omega
  have hcons : added.drop (i - 1) = added[i - 1]! :: added.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, maskFold_cons]

prove_correct countQueryShape by
  loom_solve
  · rw [maskFold_drop_step added i (by omega) (by omega)]
    simp_all
  all_goals simp_all [keptNames, needsNesting, anyPriorAggregate]
