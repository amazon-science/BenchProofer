import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the reconstruction round-trip of
-- an atomic string value is modeled DEEPLY below (the impl spells out applying the
-- value's reconstruction callable to the argument data the value reports about
-- itself, under each argument-passing convention). No outside callee is invoked,
-- hence no consumed axiom and no A-reference. The proof agent may add `_prop`
-- axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- An atomic string value: it carries its text as intrinsic data. -/
structure StringObj where
  text : String
deriving DecidableEq, Repr

/-- The positional argument list of an atomic string value. An atomic value
exposes NO positional children — its text is intrinsic, not a positional
argument — so the list is empty. (This is the `args` in `expr.func(*expr.args)`.) -/
def stringArgs (_s : StringObj) : List StringObj := []

/-- The argument-passing conventions under which a value reports its own
reconstruction data: as a positional list (the `args` in
`expr.func(*expr.args)`) and as a keyword mapping (the `kwargs()` in
`expr.func(**expr.kwargs())`). Both are conventions the same value publishes
about itself, so both describe the same single reconstruction. -/
inductive ReconCall where
  | positional : ReconCall
  | keyword : ReconCall
deriving DecidableEq, Repr, Fintype
-- pure-end

-- post-conditions-start
/-- Argument-reconstruction invariance for an atomic string value, under EVERY
argument-passing convention that value publishes about itself. Handing the
value's reconstruction callable the value's OWN self-reported argument data
reproduces the original value: `expr.func(*expr.args) == expr` for the
positional list, and equally `expr.func(**expr.kwargs()) == expr` for the
keyword mapping. On each convention the round-trip SUCCEEDS and carries back
exactly the input value (`= some s`); the results are fully determined by the
input (frame: nothing is left unconstrained), and `none` — a call the callable
does not admit, or one that yields a different value — is excluded. The
quantifier is the substance of the clause: the two conventions describe one
value's single reconstruction, so honouring the data the value publishes under
one convention while refusing the data it publishes under the other does NOT
satisfy this. -/
def problem_spec_reconstructString (s : StringObj)
    (result : ReconCall → Option StringObj) : Prop :=
  ∀ c : ReconCall, result c = some s
-- post-conditions-end

-- impl-start
def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
  fun c =>
    -- The positional argument list the value reports about itself (empty for an
    -- atomic value).
    let args := stringArgs s
    -- The keyword argument names the value reports about itself. An atomic value
    -- publishes no reconstruction keywords, so the mapping is empty too.
    let kwargNames : List String := []
    -- The value's reconstruction callable. It consumes NO reconstruction data at
    -- all and yields the value itself, so it admits exactly the empty positional
    -- list and the empty keyword mapping — which is precisely the data the value
    -- publishes under each convention.
    let reconstructPositional : List StringObj → Option StringObj :=
      fun pos => if pos.isEmpty then some s else none
    let reconstructKeyword : List String → Option StringObj :=
      fun kw => if kw.isEmpty then some s else none
    -- Apply the callable to the value's own self-reported data, per convention.
    match c with
    | ReconCall.positional => reconstructPositional args
    | ReconCall.keyword => reconstructKeyword kwargNames
-- impl-end

-- proof-start
theorem correct_reconstructString : ∀ s : StringObj,
    problem_spec_reconstructString s (implementation_reconstructString s) := by
  intro s
  unfold problem_spec_reconstructString implementation_reconstructString
  intro c
  cases c <;> rfl
-- proof-end
