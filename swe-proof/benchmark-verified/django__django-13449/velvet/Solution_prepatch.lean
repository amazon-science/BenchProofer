import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee is axiomatized for this bundle. The behaviour under spec
   is a pure string-assembly decision over three abstracted inputs: whether the
   windowed expression's result type is a fixed-precision decimal, the SQL of the
   operand the window is computed over, and the already-assembled window clause.
   The two string operations involved — the numeric cast wrapper and the OVER
   template — are unchanged, shared rendering steps, transliterated directly; no
   foreign callee's behaviour is assumed (no consumed axiom, no deep-model
   reference). -/
-- axioms-end

-- pure-start
/- The numeric cast wrapper: a SQL fragment is wrapped so its value is coerced to
   a numeric type. (Concrete unchanged string operation; refinement.md §A.) -/
def numericCast (sql : List Char) : List Char :=
  "CAST(".toList ++ sql ++ " AS NUMERIC)".toList

/- The windowing template: an operand SQL fragment placed in front of its
   parenthesised window clause via the OVER keyword. (Concrete unchanged string
   template `expression OVER (window)`; refinement.md §A.) -/
def overClause (expr win : List Char) : List Char :=
  expr ++ " OVER (".toList ++ win ++ ")".toList

/- The SQL rendered for a windowed expression on a backend whose decimal results
   must be coerced with a numeric cast.

   * When the result type is a fixed-precision decimal, the numeric cast wraps
     the ENTIRE windowed expression — the operand together with its OVER clause —
     and the operand itself carries no inner cast. (The cast must be around the
     whole expression; a cast around the operand alone would split the OVER
     syntax.)
   * Otherwise the expression is rendered as the plain OVER template with no cast.

   This is the deep model of the rendering (refinement.md §A; mapping.md §2). -/
def windowSql (isDecimal : Bool) (innerBase win : List Char) : List Char :=
  if isDecimal then numericCast (overClause innerBase win)
  else overClause innerBase win
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the SQL for a windowed expression on a backend whose fixed-precision
   decimal results must be wrapped in a numeric cast. All three inputs are
   read-only and unchanged by the rendering (none is `mut`):

   * `isDecimal` says the windowed expression's result type is a fixed-precision
     decimal;
   * `innerBase` is the SQL of the operand the window is computed over, WITHOUT
     any numeric cast of its own;
   * `win` is the already-assembled window clause (the text inside the OVER
     parentheses).

   Desired behaviour: when the result is a fixed-precision decimal the numeric
   cast must wrap the ENTIRE windowed expression — the operand together with its
   OVER clause — rather than the operand alone (which would leave the cast inside
   the OVER syntax); when the result is not a decimal the expression renders as
   the plain OVER template with no cast. The rendered string is the SQL the
   backend executes, so it fully determines the result. -/
method windowNumericSql (isDecimal : Bool) (innerBase : List Char) (win : List Char)
    return (out : List Char)
  ensures out = windowSql isDecimal innerBase win
  do
    -- impl-start
    -- Pre-image skeleton: on the decimal branch the numeric cast wraps the
    -- OPERAND ALONE, and the cast operand is then placed in front of the OVER
    -- clause. This puts `CAST(... AS NUMERIC)` immediately before `OVER (...)`,
    -- so the cast closes before the window clause and the syntax is split
    -- (`CAST(LAG(...) AS NUMERIC) OVER (...)`). The frozen spec (windowSql)
    -- requires the cast to wrap the entire windowed expression, so prove_correct
    -- MUST fail on the decimal clause.
    let mut out : List Char := []
    if isDecimal then
      let castInner := numericCast innerBase
      out := overClause castInner win
    else
      out := overClause innerBase win
    return out
    -- impl-end

prove_correct windowNumericSql by
  loom_solve <;> simp only [windowSql] <;> split_ifs <;> simp_all
