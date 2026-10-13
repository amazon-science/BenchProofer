import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation is a pure dispatch over the kind of a
--  comparison expression and is modeled DEEPLY in the `pure` region below. The
--  recursive rewrite of the two operand sub-expressions is an UNCHANGED
--  behaviour of the surrounding rewriter, abstracted as the free input `visit`,
--  about which the spec asserts nothing — so there is nothing to check against a
--  real callee. There is no `axiom` declaration and no A-reference deep model.)
-- axioms-end

-- pure-start
/- The comparison kinds an expression-rewriter can encounter, reduced to the
   only distinctions the rewrite reacts to:
     * `ne`  — "not equal";
     * `lt`  — "less than";
     * `le`  — "less than or equal";
     * `gt`  — "greater than";
     * `ge`  — "greater than or equal";
     * `eq`  — "equal";
     * `other` — any remaining comparison kind (identity, membership, …) that
                 the rewrite does not turn into a symbolic relation. -/
inductive CompareKind where
  | ne
  | lt
  | le
  | gt
  | ge
  | eq
  | other
  deriving Inhabited, DecidableEq

/- The symbolic relation constructors the six ordered/equality comparisons map
   to (the SymPy relational classes named in the issue: `Lt`, and its siblings). -/
inductive RelKind where
  | Ne
  | Lt
  | Le
  | Gt
  | Ge
  | Eq
  deriving Inhabited, DecidableEq

/- An expression node, reduced to the shapes this rewrite produces or preserves:
     * `leaf t`              — any operand sub-expression (opaque; identified by a
                               tag so distinct operands stay distinct);
     * `comparison k l r`    — a comparison expression of kind `k` over operands
                               `l`, `r` (the input shape, and the shape PRESERVED
                               for an unsupported comparison kind);
     * `relation rk built l r` — an application of the symbolic relation
                               constructor `rk` to `l`, `r`. The flag `built`
                               records whether the relation was built so that it
                               is held UNEVALUATED (`built = false`) — the only
                               way the comparison survives as a symbolic relation
                               instead of collapsing to a truth value. -/
inductive Node where
  | leaf (tag : Nat)
  | comparison (k : CompareKind) (l r : Node)
  | relation (rk : RelKind) (built : Bool) (l r : Node)
  deriving Inhabited, DecidableEq

/- The relation constructor an ordered/equality comparison maps to; the
   remaining comparison kinds have no symbolic-relation counterpart here. -/
def relOf : CompareKind → Option RelKind
  | .ne    => some .Ne
  | .lt    => some .Lt
  | .le    => some .Le
  | .gt    => some .Gt
  | .ge    => some .Ge
  | .eq    => some .Eq
  | .other => none

/- The rewrite of one comparison expression, modeled deeply. The desired
   behaviour, given the unchanged operand rewrite `visit`:
     * an ordered/equality comparison becomes an application of the matching
       symbolic relation constructor to the two REWRITTEN operands, held
       UNEVALUATED (`built = false`) so the comparison stays a symbolic relation
       rather than collapsing to a truth value;
     * any other comparison kind is left exactly as it is. -/
def rewriteCompare (visit : Node → Node) (k : CompareKind) (l r : Node) : Node :=
  match relOf k with
  | some rk => Node.relation rk false (visit l) (visit r)
  | none    => Node.comparison k l r
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Rewrite a single comparison expression into the symbolic-relation form. An
   ordered/equality comparison (`<`, `<=`, `>`, `>=`, `==`, `!=`) becomes the
   matching relation constructor applied to the two rewritten operands and held
   unevaluated, so it survives as a symbolic relation rather than reducing to a
   truth value; every other comparison kind is preserved unchanged. `visit`,
   `k`, `l`, `r` are read-only (not `mut`); the rewrite computes a single node
   and mutates nothing (directive 5). -/
method rewriteComparison (visit : Node → Node) (k : CompareKind) (l : Node) (r : Node) return (out : Node)
  ensures out = rewriteCompare visit k l r
  -- A supported comparison becomes the matching relation, applied to the
  -- rewritten operands and held unevaluated. (Pins both the class and the
  -- unevaluated flag: an EVALUATED relation would collapse to a truth value.)
  ensures k = .lt → out = .relation .Lt false (visit l) (visit r)
  ensures k = .le → out = .relation .Le false (visit l) (visit r)
  ensures k = .gt → out = .relation .Gt false (visit l) (visit r)
  ensures k = .ge → out = .relation .Ge false (visit l) (visit r)
  ensures k = .eq → out = .relation .Eq false (visit l) (visit r)
  ensures k = .ne → out = .relation .Ne false (visit l) (visit r)
  -- An unsupported comparison kind is preserved exactly.
  ensures relOf k = none → out = .comparison k l r
  -- Whenever a relation is produced it is held unevaluated.
  ensures ∀ (rk : RelKind) (b : Bool) (a c : Node), out = .relation rk b a c → b = false
  do
    -- impl-start
    -- Dispatch on the comparison kind. An ordered/equality comparison is turned
    -- into the matching symbolic relation constructor applied to the two
    -- rewritten operands, held unevaluated; any other comparison kind is left
    -- exactly as it is.
    let out : Node :=
      match relOf k with
      | some rk => Node.relation rk false (visit l) (visit r)
      | none    => Node.comparison k l r
    return out
    -- impl-end

prove_correct rewriteComparison by
  loom_solve
  all_goals cases k <;> simp_all [rewriteCompare, relOf]
