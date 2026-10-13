import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour under change — how a rational number is
   rendered for the arbitrary-precision numeric backend — is modeled DEEPLY in
   the `pure` region (`render`). The only callee the operation READS, the helper
   that resolves the backend float constructor's dotted name to the spelling
   emitted in generated code, is modeled DEEPLY as `mpfName`, a function of the
   ambient name-spelling configuration, together with the import that resolving
   records (`mpfImport`); both are validated `==` the real resolver — in BOTH
   configurations, and for the recorded import — by G-AX (an A-reference,
   mapping.md §3.1), NOT carried as a consumed axiom. -/
-- axioms-end

-- pure-start
/- The spelling the backend float constructor's dotted name resolves to in
   generated code. The resolver reads the ambient name-spelling configuration:
   when module-qualified spellings are asked for it hands the dotted name back
   unchanged, and otherwise it hands back only the final component — the bare
   constructor name, which is what the caller binds in the namespace the
   generated code runs in. Deep model of that (unchanged) resolver at the one
   dotted name this operation resolves; validated against the real resolver in
   BOTH configurations by G-AX (A-reference). -/
def mpfName (qualified : Bool) : String :=
  if qualified then "mpmath.mpf" else "mpf"

/- The import that resolving the backend float constructor's dotted name
   records: the final component is requested from the module that qualifies it.
   Recorded under BOTH name-spelling configurations — the spelling handed back
   varies with the configuration, the recorded import does not. Recording is a
   set insertion, hence idempotent and independent of what is already recorded,
   so this delta characterizes the effect completely (mapping.md §2, §3.1). -/
def mpfImport : List (String × String) := [("mpmath", "mpf")]

/- The desired rendering of a rational number for the arbitrary-precision
   numeric backend: a quotient whose numerator and denominator are EACH wrapped
   in a call to the backend's float constructor, so both are carried at full
   precision rather than emitted as a bare integer ratio. The constructor is
   named by the spelling the resolver hands back under the ambient
   configuration, the SAME spelling in both positions. `p` is the (signed)
   numerator and `q` the denominator; each is rendered with its ordinary decimal
   text. -/
def render (qualified : Bool) (p q : Int) : String :=
  mpfName qualified ++ "(" ++ toString p ++ ")/" ++
    mpfName qualified ++ "(" ++ toString q ++ ")"

@[grind] lemma render_def (qualified : Bool) (p q : Int) :
    render qualified p q =
      mpfName qualified ++ "(" ++ toString p ++ ")/" ++
        mpfName qualified ++ "(" ++ toString q ++ ")" := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a rational number for the arbitrary-precision numeric backend. The
   numerator and denominator are each wrapped in a call to the backend's float
   constructor and joined as a quotient, so the value is reproduced at full
   precision instead of as a bare integer ratio. The constructor is named by
   whatever spelling the ambient configuration `qualified` resolves its dotted
   name to, and resolving that name records the import the generated code needs
   in order for the spelling to denote the constructor. The first component of
   the result is the rendered text; the second is the recorded import. -/
method mpfRational (qualified : Bool) (p : Int) (q : Int)
    return (out : String × List (String × String))
  ensures out.1 = render qualified p q
  ensures out.2 = mpfImport
  do
    -- impl-start
    -- Resolve the constructor's name once under the ambient configuration, wrap
    -- both parts of the quotient in it, and report the import that resolving
    -- recorded.
    let m : String := mpfName qualified
    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"
    return (text, mpfImport)
    -- impl-end

prove_correct mpfRational by
  loom_solve
