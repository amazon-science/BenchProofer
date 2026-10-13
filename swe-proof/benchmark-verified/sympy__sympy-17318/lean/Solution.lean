import Mathlib
-- imports-end

/-!
Decomposing an additive expression into a nested-square-root normal form.

An additive expression is presented as a list of addends. The routine tries to
express it in a normal form built around square roots. Each addend has a square;
the square is classified by whether it is a rational number and, if so, by its
sign.

The behavior is governed by a single decision over the addends:

* When EVERY addend's square is a positive rational, a specialized fast
  decomposition routine applies. That routine is the source of the result on
  this branch; its result is returned unchanged.

* Otherwise — i.e. as soon as some addend's square fails to be a positive
  rational (it is not rational at all, or it is a non-positive rational) — the
  fast routine is not applicable, and a general depth-based matcher produces the
  result instead. The general matcher always yields a normal form (possibly the
  empty one, meaning "no nontrivial decomposition").

We model the outcome as `Except Unit NestedForm`. `Except.ok f` carries a
returned normal form `f`; `Except.error ()` denotes the fast routine being
unable to process its argument and that inability escaping the computation. A
correct computation routes to the general matcher whenever the fast routine is
not applicable, and therefore yields `Except.ok` on that branch — it never lets
an inapplicability escape.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
/-- A single addend of the additive expression. `sq` is the value of the
addend's square WHEN that square is a rational number (`some q`), and `none`
when the square is not rational. `tag` is an opaque identity distinguishing
addends that share the same square. The decision that drives the behavior
observes only `sq`; the two decomposition routines below observe the full
addend. -/
structure Addend where
  sq : Option Rat
  tag : Nat
deriving DecidableEq, Inhabited, Repr

/-- A nested-square-root normal form (the kind of object the routine returns),
identified by its canonical representation. Observed only through equality. -/
structure NestedForm where
  repr : String
deriving DecidableEq, Inhabited, Repr

/-- The unchanged specialized fast decomposition routine. It is applicable only
when every addend's square is a positive rational; `Except.ok f` is a produced
normal form `f`, and `Except.error ()` is the routine signalling it cannot
process its argument (the inability that, unguarded, escapes the computation).
Its internal algorithm lies outside this behavior and is left abstract. -/
opaque fastDecomp : List Addend → Except Unit NestedForm

/-- The unchanged general depth-based matcher: it always produces a normal form
(possibly the empty one) for any additive expression. Left abstract — it is an
outside callee, not part of the behavior under specification. -/
opaque depthMatch : List Addend → NestedForm
-- axioms-end

-- pure-start
/-- Whether a single addend's square is a positive rational: the square must be
rational (`some q`) and that rational must be strictly positive. -/
def squarePosRat (a : Addend) : Bool :=
  match a.sq with
  | some q => decide (0 < q)
  | none => false

/-- Whether EVERY addend of the expression has a positive-rational square — the
decision that selects the fast decomposition routine. -/
def allSquarePosRat (p : List Addend) : Bool :=
  p.all squarePosRat
-- pure-end

-- post-conditions-start
/-- The outcome of decomposing the additive expression `p`.

If every addend's square is a positive rational: the fast routine is applicable
and its result is returned unchanged (`result = fastDecomp p`).

Otherwise: the fast routine is not applicable, so the general matcher produces
the result and it is returned as `Except.ok (depthMatch p)`. The computation
never propagates the fast routine's inability on this branch. -/
def problem_spec_decompose (p : List Addend) (result : Except Unit NestedForm) : Prop :=
  if allSquarePosRat p = true then
    result = fastDecomp p
  else
    result = Except.ok (depthMatch p)
-- post-conditions-end

-- impl-start
def implementation_decompose (p : List Addend) : Except Unit NestedForm := Id.run do
  if allSquarePosRat p then
    return fastDecomp p
  else
    return Except.ok (depthMatch p)
-- impl-end

-- proof-start
theorem correct_decompose :
    ∀ (p : List Addend),
      problem_spec_decompose p (implementation_decompose p) := by
  intro p
  unfold problem_spec_decompose implementation_decompose
  by_cases h : allSquarePosRat p = true
  · simp only [Id.run, h, if_true]; rfl
  · simp only [Id.run, h]; rfl
-- proof-end
