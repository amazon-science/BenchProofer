import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The one piece of machinery
   this slice consults — rendering the underlying existence test to a fragment —
   is UNCHANGED by the desired behaviour and may, for some inputs, signal that
   the underlying set is provably empty. Its outcome is therefore modeled as a
   free input to the operation (an `Except` carrier, mapping.md §2): the
   postcondition then holds for EVERY such outcome, strictly weaker than any
   concrete renderer, so no contract is owed (directive 7). There is no
   module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A rendered SQL fragment, reduced to the only two observables the operation
   carries through: the predicate text and its ordered bound parameters
   (mapping.md §2). The text and parameter element types are irrelevant to the
   behaviour under spec, so they are modeled by simple carriers. -/
structure Frag where
  sql : List Char
  params : List Int
  deriving DecidableEq

/- The desired rendering of a (possibly logically-complemented) subquery-existence
   test, given the rendering `inner` the unchanged underlying renderer produces:

     * `inner = Except.ok f`  — the renderer produced fragment `f`. The test is
       rendered as `f`; when the test is logically complemented the predicate is the
       complement of `f` (its text prefixed by the SQL `NOT` keyword, the bound
       parameters unchanged).

     * `inner = Except.error ()` — the renderer signalled that the underlying set
       is provably empty. A plain existence over a provably-empty set is itself a
       provably-empty (unsatisfiable) predicate, so that signal propagates. Its
       complement, however, is an always-true predicate; an always-true
       predicate contributes nothing to a conjunctive filter and is rendered as
       the empty fragment (no text, no parameters) rather than propagating the
       emptiness signal. -/
def renderExists (complemented : Bool) (inner : Except Unit Frag) : Except Unit Frag :=
  match inner with
  | Except.ok f =>
      Except.ok (if complemented then { f with sql := "NOT ".toList ++ f.sql } else f)
  | Except.error _ =>
      if complemented then Except.ok ⟨[], []⟩ else Except.error ()

@[grind] lemma renderExists_def (complemented : Bool) (inner : Except Unit Frag) :
    renderExists complemented inner =
      (match inner with
       | Except.ok f =>
           Except.ok (if complemented then { f with sql := "NOT ".toList ++ f.sql } else f)
       | Except.error _ =>
           if complemented then Except.ok ⟨[], []⟩ else Except.error ()) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render a subquery-existence test (possibly logically complemented) to a SQL
   fragment, given the rendering `inner` the unchanged underlying renderer
   produces for the bare existence test (mapping.md §1/§2). When the renderer
   signals that the underlying set is provably empty, a complemented test must still
   yield a fragment — the empty (always-true) fragment — instead of letting the
   emptiness signal discard the whole predicate. -/
method renderExistsTest (complemented : Bool) (inner : Except Unit Frag)
    return (out : Except Unit Frag)
  ensures out = renderExists complemented inner
  do
    -- impl-start
    -- Carry the produced fragment through (prefixing `NOT` to its text when the
    -- test is complemented); on a provably-empty signal, propagate it for a plain
    -- test but render a complemented test as the empty (always-true) fragment.
    let out : Except Unit Frag :=
      match inner with
      | Except.ok f =>
          Except.ok (if complemented then { f with sql := "NOT ".toList ++ f.sql } else f)
      | Except.error _ =>
          if complemented then Except.ok ⟨[], []⟩ else Except.error ()
    return out
    -- impl-end

prove_correct renderExistsTest by
  loom_solve
