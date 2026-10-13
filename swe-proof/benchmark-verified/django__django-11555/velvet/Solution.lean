import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. An
   ordering specification is a list of items; a *name* item is resolved by a
   recursive lookup that is UNCHANGED here, so it is modeled as an arbitrary
   total resolver `resolve` (a free input on the method). The postcondition holds
   for EVERY `resolve`, so it is owed no contract — it is strictly weaker than any
   concrete callee (directive 7). The only behaviour this bundle pins — how each
   kind of ordering item contributes to the expanded result — is modeled DEEPLY
   in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The two kinds of item a default-ordering specification may contain:
     * `expr e` — an order *expression* that already denotes a complete ordering
                  (it is its own resolved ordering, carried by an identity `e`);
     * `name n` — a *field-name* lookup (identity `n`) that must be resolved into
                  one or more concrete orderings by the recursive resolver. -/
abbrev Expr := Int          -- identity of an order expression
abbrev Name := Int          -- identity of a field-name lookup

/- A single resolved ordering entry: the order expression it denotes paired with
   the flag that travels alongside it in the expanded result. -/
abbrev Pair := Expr × Bool

inductive Item where
  | expr (e : Expr)
  | name (n : Name)
  deriving DecidableEq, Inhabited, Repr

/- What one item contributes to the expanded ordering:
     * an order expression contributes exactly itself, paired with the flag
       `false`, and is NOT routed through name resolution (it is already a
       complete ordering — there is no name to look up);
     * a field name contributes whatever its recursive resolution yields. -/
def itemContribution (resolve : Name → List Pair) : Item → List Pair
  | .expr e => [(e, false)]
  | .name n => resolve n

/- The expansion of a whole specification: concatenate each item's contribution,
   in order. Written front-recursively so a single unfold is available per loop
   step (the fold pattern, plan §5.4). -/
def expandItems (resolve : Name → List Pair) : List Item → List Pair
  | []        => []
  | it :: rest => itemContribution resolve it ++ expandItems resolve rest

@[grind] lemma expandItems_nil (resolve : Name → List Pair) :
    expandItems resolve [] = [] := rfl
@[grind] lemma expandItems_cons (resolve : Name → List Pair)
    (it : Item) (rest : List Item) :
    expandItems resolve (it :: rest)
      = itemContribution resolve it ++ expandItems resolve rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Expand a default-ordering specification into its list of resolved ordering
   entries. All inputs are read-only (none is `mut`):
     * `items`   — the ordering specification, a list of items each of which is
                   either an order expression or a field-name lookup;
     * `resolve` — the recursive resolution of a field-name lookup into its
                   resolved ordering entries (unchanged here; abstracted as an
                   arbitrary total function).

   Desired behaviour: the result is the in-order concatenation of every item's
   contribution, where an order expression contributes exactly itself paired with
   `false` (it is already a complete ordering and is taken as-is, never handed to
   name resolution) and a field name contributes its recursive resolution. -/
method expandOrdering (items : List Item) (resolve : Name → List Pair)
    return (out : List Pair)
  ensures out = expandItems resolve items
  do
    -- impl-start
    let mut result : List Pair := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant result = expandItems resolve (items.drop i)
      done_with i = 0
      decreasing i
    do
      let it := items[i - 1]!
      -- An order expression is already a complete ordering: take it as-is,
      -- paired with `false`. A field name is expanded by its recursive
      -- resolution. (The branch is what keeps an expression off the
      -- name-resolution path.)
      let contribution : List Pair :=
        match it with
        | .expr e => [(e, false)]
        | .name n => resolve n
      result := contribution ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer item exposes the item at `i-1` on
   the front, so `expandItems` peels one `itemContribution`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma expandItems_drop_step (resolve : Name → List Pair)
    (items : List Item) (i : Nat) (hi : 0 < i) (hle : i ≤ items.length) :
    expandItems resolve (items.drop (i - 1))
      = itemContribution resolve items[i - 1]! ++ expandItems resolve (items.drop i) := by
  have hlt : i - 1 < items.length := by omega
  have hcons : items.drop (i - 1) = items[i - 1]! :: items.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, expandItems_cons]

prove_correct expandOrdering by
  loom_solve
  rw [expandItems_drop_step resolve items i (by omega) (by omega)]
  simp_all [itemContribution]
