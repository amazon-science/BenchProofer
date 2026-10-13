import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The positional arguments an atomic
--  string-valued object exposes is the observable result of an UNCHANGED
--  inspection of the object's structure; it is deep-modeled below as
--  `exposedArgs` and validated against the real object by axiom_check.py
--  (G-AX, A-reference), not borrowed from an asserted axiom. The operation
--  under specification — choosing the object's reconstruction function and its
--  keyword-argument view so that argument invariance holds — is modeled deeply
--  as the do block, so it is never axiomatized.)
-- axioms-end

-- pure-start
/- An atomic string-valued object: fully determined by its text content. Two
   such objects are equal exactly when their text agrees (so a reconstruction
   reproduces the object iff it reproduces the text). -/
structure StrObj where
  text : List Char
  deriving DecidableEq, Inhabited

/- The positional arguments an atomic object exposes for reconstruction. An
   atomic object has no constituent sub-arguments, so this is the empty list —
   `args == ()`. (An UNCHANGED structural inspection; A-reference, mapping.md.) -/
def exposedArgs (_ : StrObj) : List StrObj := []

/- The two distinguishable arities a reconstruction function `func` can have:

     * `noArgForm`  — `func` accepts a call with no positional and no keyword
       arguments, and then reproduces the object; supplying any positional or
       keyword argument makes the call fail.
     * `oneArgForm` — `func` requires the single text specifier: a positional
       call succeeds only when exactly one positional value is supplied, and a
       keyword call only when the lone `text` keyword is supplied.

   The behavior under specification turns on WHICH arity the object's `func`
   has, paired with which keyword names its `kwargs()` view exposes. -/
inductive FuncKind
  | noArgForm
  | oneArgForm
  deriving DecidableEq, Inhabited

/- Apply `func` positionally — the `func(*pos)` call. A `noArgForm` function
   accepts the call only when `pos` is empty (and then yields the object); a
   `oneArgForm` function accepts only a single positional value. The call fails
   (`none`) on any incompatible arity. -/
def applyPos (k : FuncKind) (s : StrObj) (pos : List StrObj) : Option StrObj :=
  match k with
  | .noArgForm  => if pos = [] then some s else none
  | .oneArgForm => match pos with
                   | [t] => some { text := t.text }
                   | _   => none

/- Apply `func` by keyword — the `func(**kwargs())` call, where `names` are the
   keyword names the `kwargs()` view supplies. A `noArgForm` function accepts
   the call only when no keyword names are supplied; a `oneArgForm` function
   accepts only the lone `text` keyword. The call fails (`none`) on any
   incompatible keyword set. -/
def applyKw (k : FuncKind) (s : StrObj) (names : List (List Char)) : Option StrObj :=
  match k with
  | .noArgForm  => if names = [] then some s else none
  | .oneArgForm => if names = ["text".toList] then some s else none

/- The reconstruction view selected for an object: the arity its reconstruction
   function `func` has (`kind`) and the keyword names its `kwargs()` view exposes
   (`kwNames`). Argument invariance is checked by APPLYING this `func` to the
   object's own positional `args` and to its keyword `kwargs()` and demanding
   both reproduce the object — so the verdict is *produced by* the recorded
   choices via `applyPos`/`applyKw`, never asserted as a free outcome value. -/
structure InvarianceResult where
  kind      : FuncKind
  kwNames   : List (List Char)
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- An atomic string-valued object (a `Basic` subclass) must support argument
   invariance: applying its reconstruction function `func` to its own positional
   arguments `args` reproduces the object — `func(*args) == self` — and likewise
   applying `func` to the keyword arguments returned by `kwargs()` reproduces it
   — `func(**kwargs()) == self`. Both reconstruction identities must hold at the
   same time.

   The operation chooses, for the object, the signature of its reconstruction
   function `func` and the keyword names exposed by its `kwargs()` view. The
   behavior pinned here: applying that `func` to the object's own positional
   arguments and to its keyword arguments BOTH reproduce the object — neither
   reconstruction fails and neither yields a different object.

   `s` is a read-only object handle (not `mut`); the routine inspects it and
   mutates nothing (directive 5). -/
method reconstructInvariance (s : StrObj) return (out : InvarianceResult)
  ensures applyPos out.kind s (exposedArgs s) = some s
  ensures applyKw  out.kind s out.kwNames     = some s
  do
    -- impl-start
    -- Pre-image skeleton: the reconstruction function `func` requires the single
    -- text specifier (`oneArgForm`), while the exposed positional `args` is
    -- empty. Applying `func` to the empty `args` therefore supplies no value for
    -- the required specifier and fails to reconstruct the object: `func(*args)`
    -- does not reproduce it. The frozen spec requires
    -- `applyPos out.kind s (exposedArgs s) = some s`, so prove_correct MUST fail.
    let kind : FuncKind := FuncKind.oneArgForm
    let kwNames : List (List Char) := ["text".toList]
    return { kind := kind, kwNames := kwNames }
    -- impl-end

prove_correct reconstructInvariance by
  loom_solve <;> simp_all [applyPos, applyKw, exposedArgs]
