import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The downstream operation the
   selector is forwarded to (the trapezoidal integrator over a chosen
   coordinate) is UNCHANGED by this change and is fully determined by the single
   value the dispatch forwards to it — its result is observed only THROUGH the
   forwarded selector, which is the input carrier. So there is nothing to
   axiomatize and nothing to validate against a real callee (no axiom_check.py;
   meta.json G-AX skip). This change is entirely in how the public entry point
   chooses which coordinate to forward and whether to raise an advisory. -/
-- axioms-end

-- pure-start
/- A coordinate selector argument, which may be supplied or omitted. A selector
   name is modeled as a `Nat` tag: the dispatch only ever asks whether a selector
   was supplied and, if so, forwards its value verbatim — it never inspects the
   name's internals. `none` ↔ the argument left at its absent default;
   `some k` ↔ the argument supplied with name tag `k`. -/
abbrev Selector := Option Nat

/- Why the dispatch rejects a call: the caller supplied BOTH the primary selector
   and the legacy selector at once, which is contradictory. -/
inductive DispatchErr where
  | bothSupplied
  deriving DecidableEq, Repr

/- The outcome of resolving the two selectors into a single forwarded call:
   the coordinate name handed to the (unchanged) integrator, and whether the
   one-time advisory about the legacy selector is raised. -/
structure Dispatch where
  /-- the coordinate name forwarded to the integrator -/
  forwarded : Nat
  /-- whether the advisory about the legacy selector fires -/
  advisory  : Bool
  deriving DecidableEq, Repr

/- Resolve a call given the primary selector and the legacy selector.

   * Supplying BOTH selectors is contradictory and is rejected.
   * If the primary selector is supplied (and the legacy one is not), its value
     is forwarded and no advisory is raised.
   * If only the legacy selector is supplied, its value is forwarded — the
     legacy selector remains accepted — but the one-time advisory fires, because
     the legacy selector is being phased out in favour of the primary one.
   * If neither is supplied, there is nothing to forward; the call cannot select
     a coordinate. (Modeled as the absence of a forwarded coordinate, `none`.)

   The legacy selector is therefore still honoured for the value it carries; the
   only newly-observable consequences are (a) rejecting a both-supplied call and
   (b) raising the advisory on a legacy-only call. -/
def resolve (primary legacy : Selector) : Except DispatchErr (Option Dispatch) :=
  match primary, legacy with
  | some _, some _ => Except.error .bothSupplied
  | some c, none   => Except.ok (some { forwarded := c, advisory := false })
  | none,   some d => Except.ok (some { forwarded := d, advisory := true })
  | none,   none   => Except.ok none

@[grind] lemma resolve_both (c d : Nat) :
    resolve (some c) (some d) = Except.error .bothSupplied := rfl
@[grind] lemma resolve_primary (c : Nat) :
    resolve (some c) none = Except.ok (some { forwarded := c, advisory := false }) := rfl
@[grind] lemma resolve_legacy (d : Nat) :
    resolve none (some d) = Except.ok (some { forwarded := d, advisory := true }) := rfl
@[grind] lemma resolve_neither :
    resolve none none = Except.ok (none : Option Dispatch) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method integrateDispatch (primary : Selector) (legacy : Selector)
    return (out : Except DispatchErr (Option Dispatch))
  ensures out = resolve primary legacy
  -- The two selector arguments are read-only: this query computes the dispatch
  -- decision and mutates nothing (directive 5). They are not declared `mut`.
  do
    -- impl-start
    -- Pre-image skeleton: the entry point accepted only a single selector and
    -- forwarded it verbatim, NEVER raising the advisory and NEVER rejecting a
    -- both-supplied call. Whatever selector carries a value is forwarded with
    -- `advisory := false`. On a legacy-only call this MUST fail the frozen spec,
    -- which requires the advisory to fire (resolve none (some d) has
    -- advisory := true).
    let res : Except DispatchErr (Option Dispatch) :=
      match primary, legacy with
      | some c, _      => Except.ok (some { forwarded := c, advisory := false })
      | none,   some d => Except.ok (some { forwarded := d, advisory := false })
      | none,   none   => Except.ok none
    return res
    -- impl-end

prove_correct integrateDispatch by
  loom_solve
