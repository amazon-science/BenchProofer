import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The only callees the modeled renderers invoke are the
   renderers of their sub-expressions; each unchanged sub-expression is carried
   as a pre-rendered atom (`Expr.atom`), and the two expression shapes whose
   rendering this bundle pins — a parenthesized group of values and an indexing
   expression — are modeled DEEPLY by `render` below (all-I/R; mapping.md §2). -/
-- axioms-end

-- pure-start
/- A source expression, abstracted to exactly the shapes whose rendering matters
   here. `atom t` is any expression already rendered to the text `t` by an
   unchanged renderer (a name, a literal, an operator expression, …). `unpack e`
   is an unpacking element `*e`. `group elts` is a parenthesized, comma-separated
   group of expressions. `index value idx` is an indexing expression
   `value[idx]`. -/
inductive Expr where
  | atom (text : List Char)
  | unpack (value : Expr)
  | group (elts : List Expr)
  | index (value : Expr) (idx : Expr)
deriving Inhabited

/- Join already-rendered pieces with ", " between them (front-recursive so a
   single unfold is available per step). -/
def joinComma : List (List Char) → List Char
  | []      => []
  | [x]     => x
  | x :: xs => x ++ ", ".toList ++ joinComma xs

/- Whether an expression is an unpacking element. -/
def isUnpack : Expr → Bool
  | .unpack _ => true
  | _         => false

/- Render an expression to source text. `atom` reproduces its pre-rendered text;
   `unpack e` prefixes `*`. A non-empty `group` is enclosed in its surrounding
   parentheses around the comma-separated members; an empty group renders as the
   literal `()`. An `index` whose index is a non-empty group carrying no
   unpacking element renders the group's members directly inside the brackets
   (no redundant grouping parentheses); otherwise the index is rendered as a
   whole expression inside the brackets. -/
def render : Expr → List Char
  | .atom t   => t
  | .unpack v => "*".toList ++ render v
  | .group elts =>
      if elts.isEmpty then "()".toList
      else "(".toList ++ joinComma (elts.map render) ++ ")".toList
  | .index value idx =>
      match idx with
      | .group elts =>
          if (!elts.isEmpty) && (!elts.any isUnpack) then
            render value ++ "[".toList ++ joinComma (elts.map render) ++ "]".toList
          else
            render value ++ "[".toList ++ render (.group elts) ++ "]".toList
      | s => render value ++ "[".toList ++ render s ++ "]".toList

/- One-step unfold of `render` on a group — the single fact the group renderer's
   proof needs. -/
@[grind] theorem render_group (elts : List Expr) :
    render (.group elts) =
      (if elts.isEmpty then "()".toList
       else "(".toList ++ joinComma (elts.map render) ++ ")".toList) := by
  conv_lhs => unfold render

/- One-step unfold of `render` on an indexing expression. -/
@[grind] theorem render_index (value idx : Expr) :
    render (.index value idx) =
      (match idx with
       | .group elts =>
           if (!elts.isEmpty) && (!elts.any isUnpack) then
             render value ++ "[".toList ++ joinComma (elts.map render) ++ "]".toList
           else
             render value ++ "[".toList ++ render (.group elts) ++ "]".toList
       | s => render value ++ "[".toList ++ render s ++ "]".toList) := by
  conv_lhs => unfold render
-- pure-end

-- pre-conditions-start
-- (the group renderer needs no precondition: every element list is valid input)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method renderGroup (elts : List Expr) return (out : List Char)
  ensures out = render (.group elts)
  do
    -- impl-start
    -- Render a group of expressions to source text: an empty group is the
    -- literal `()`; a non-empty group is its comma-separated members enclosed in
    -- the surrounding parentheses.
    let out : List Char :=
      if elts.isEmpty then "()".toList
      else "(".toList ++ joinComma (elts.map render) ++ ")".toList
    return out
    -- impl-end

prove_correct renderGroup by
  loom_solve

-- pre-conditions-start
-- (the index renderer needs no precondition)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method renderIndex (value : Expr) (idx : Expr) return (out : List Char)
  ensures out = render (.index value idx)
  do
    -- impl-start
    -- Render an indexing expression `value[idx]`. When the index is a non-empty
    -- group with no unpacking element, its members are placed directly inside
    -- the brackets, so no extra grouping parentheses are introduced around the
    -- index; in every other case the index is rendered as a whole expression.
    -- Pre-image skeleton: the index is always rendered as a whole expression
    -- inside the brackets, with no special handling for a group index. The
    -- frozen spec flattens a simple group index, so prove_correct MUST fail.
    let out : List Char :=
      render value ++ "[".toList ++ render idx ++ "]".toList
    return out
    -- impl-end

prove_correct renderIndex by
  loom_solve
