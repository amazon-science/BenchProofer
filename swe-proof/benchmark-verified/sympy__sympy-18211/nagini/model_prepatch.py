"""Twin-artifact model for sympy__sympy-18211.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A univariate relation (a relation in exactly one free variable) is turned into
  the set of real values of that variable for which the relation holds. A
  general-purpose univariate solver is consulted for that solution set. The
  solver is partial: for some relations it determines the solution set as a
  concrete set, but for others it cannot determine it at all and signals that it
  is undecided.

  The behaviour pinned here is totality of the conversion. The conversion must
  return a set for EVERY univariate relation in its domain — it may never let the
  solver's "undecided" signal propagate to its caller. Concretely:

  (1) When the solver determines the solution set, the conversion returns EXACTLY
      that solver-produced set.

  (2) When the solver is undecided, the conversion returns the symbolic
      solution set built directly from the relation itself: the set of values of
      the variable that range over the whole real line and additionally satisfy
      the relation as an explicit defining condition. That fallback set carries
      the original relation as its condition, the conversion's variable as its
      bound symbol, and the whole real line as its base domain.

The relation is modelled abstractly by a small object carrying the count of its
free variables, an identity token for the relation, an identity token for its
single free variable, and a tag for whether the solver determines or is
undecided about its solution set. The discriminating observable is purely WHICH
set the conversion produces, not the symbolic contents of the relation, so the
relation's algebraic structure is not modelled. The solution set is modelled by
a small object carrying a tag distinguishing a solver-produced set from the
symbolic fallback, plus the fallback's defining condition / bound symbol /
base-domain fields. The univariate solver is an unchanged callee the conversion
invokes; it is axiomatised, and its undecided signal is a user-defined exception
class (a builtin exception in an `Exsures` crashes the translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class SolverUndecided(Exception):
    """The univariate solver's signal that it cannot determine the solution set
    of the given relation. User-defined stand-in for the undecidability signal
    the solver raises on some relations (a builtin exception in an `Exsures`
    crashes the Nagini translator; mapping.md §2)."""
    pass


class SolutionSet:
    """A solution set the conversion may return. `is_fallback` distinguishes the
    symbolic fallback set (built from the relation when the solver is undecided)
    from a concrete solver-produced set. For the fallback, `cond` is the relation
    carried as the explicit defining condition, `sym` is the bound variable, and
    `over_reals` records that the base domain is the whole real line."""

    def __init__(self, is_fallback: bool, cond: int, sym: int,
                 over_reals: bool) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_fallback) and Acc(self.cond) and Acc(self.sym)
                and Acc(self.over_reals))
        Ensures(self.is_fallback == is_fallback)
        Ensures(self.cond == cond)
        Ensures(self.sym == sym)
        Ensures(self.over_reals == over_reals)
        # post-conditions-end
        # impl-start
        self.is_fallback = is_fallback  # type: bool
        self.cond = cond                # type: int
        self.sym = sym                  # type: int
        self.over_reals = over_reals    # type: bool
        # impl-end


class Relation:
    """A relation under conversion: the count of its free variables, an identity
    token for the relation itself, an identity token for its single free
    variable, and a tag for whether the solver determines (`solvability == 0`) or
    is undecided about (`solvability == 1`) its solution set."""

    def __init__(self, n_free: int, token: int, sym: int,
                 solvability: int) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.n_free) and Acc(self.token) and Acc(self.sym)
                and Acc(self.solvability))
        Ensures(self.n_free == n_free)
        Ensures(self.token == token)
        Ensures(self.sym == sym)
        Ensures(self.solvability == solvability)
        # post-conditions-end
        # impl-start
        self.n_free = n_free            # type: int
        self.token = token              # type: int
        self.sym = sym                  # type: int
        self.solvability = solvability  # type: int
        # impl-end


# axioms-start
@Pure
@ContractOnly
def solved_cond(rel: Relation) -> int:
    """The defining-condition token of the set the solver produces when it
    determines a solution set (`solvability == 0`). Its value is left ABSTRACT —
    the proof needs only that the determined branch returns EXACTLY this callee's
    set (so the determined result is pinned to the solver's own returned set, not
    a value the conversion fabricates). Provenance + executable soundness check:
    mapping.md §3 / axiom_check.py."""
    Requires(Acc(rel.solvability, 1 / 4) and rel.solvability == 0)
    Ensures(True)


@Pure
@ContractOnly
def solved_sym(rel: Relation) -> int:
    """The `sym` field of the set the solver produces when it determines a
    solution set (`solvability == 0`). Value left ABSTRACT, like `solved_cond`:
    together the three accessors pin the determined branch to EXACTLY the
    solver's own returned set, field for field, so a verifying implementation
    cannot substitute a set that differs from the solver's in any modelled
    field. mapping.md §3 / axiom_check.py."""
    Requires(Acc(rel.solvability, 1 / 4) and rel.solvability == 0)
    Ensures(True)


@Pure
@ContractOnly
def solved_reals(rel: Relation) -> bool:
    """The `over_reals` field of the set the solver produces when it determines
    a solution set (`solvability == 0`). Value left ABSTRACT, like
    `solved_cond` / `solved_sym`: the determined-branch result is pinned to the
    solver's own returned set in EVERY modelled field. mapping.md §3 /
    axiom_check.py."""
    Requires(Acc(rel.solvability, 1 / 4) and rel.solvability == 0)
    Ensures(True)


@ContractOnly
def solve_univariate(rel: Relation) -> SolutionSet:
    """The general-purpose univariate solver (the unchanged callee the conversion
    invokes). It is partial: it determines the solution set as a concrete set on
    relations tagged `solvability == 0`, and is undecided (raising the
    undecidability signal) on relations tagged `solvability == 1`.

    DOMAIN CARVE-OUT (stated, not implicit). The tag `solvability` is a TOTAL
    function only over the two-way partition this axiom describes: the relations
    on which the solver either (0) returns a concrete set, or (1) signals
    undecidability via the undecidability signal. A relation on which the solver
    instead reports a domain error, a malformed-argument error, exhausts the
    recursion bound, or fails to terminate has NO `solvability` value — it is
    OUTSIDE this abstraction's domain by construction, because no `Relation`
    carrier can be built for it (`solvability ∈ {0,1}` has no preimage there).
    The precondition `solvability == 0 or solvability == 1` is therefore the
    stated mechanism that admits ONLY the return/undecidability-signal relations;
    the conversion's totality is claimed only over them, never over relations with
    any other solver outcome. (Directive 7: the axiom is not stronger than the real
    callee, because the real callee's other failure outcomes have no carrier in the
    abstraction and so are never asserted away.) mapping.md §3.1 / axiom_check.py.

    The weakest facts the proof needs over that domain: it returns normally on
    EXACTLY the determined tag — and the determined return is a concrete
    solver-produced set (NOT the symbolic fallback: `is_fallback` is False),
    pinned field-for-field to the solver's own returned set (condition token
    `solved_cond(rel)`, bound-symbol field `solved_sym(rel)`, base-domain field
    `solved_reals(rel)` — never values the conversion fabricates) — and it
    raises the undecidability signal on EXACTLY the undecided tag. Provenance +
    executable soundness check: mapping.md §3 / axiom_check.py.
    """
    Requires(Acc(rel.solvability, 1 / 2))
    # Stated domain carve-out: ONLY the return/undecidability-signal relations are
    # in the abstraction's domain; no carrier exists for any other solver outcome.
    Requires(rel.solvability == 0 or rel.solvability == 1)
    Requires(MustTerminate(2))
    Ensures(Acc(rel.solvability, 1 / 2))
    Ensures(rel.solvability == 0)
    Ensures(Acc(Result().is_fallback) and Acc(Result().cond)
            and Acc(Result().sym) and Acc(Result().over_reals))
    Ensures(Result().is_fallback == False)
    Ensures(Result().cond == solved_cond(rel))
    Ensures(Result().sym == solved_sym(rel))
    Ensures(Result().over_reals == solved_reals(rel))
    Exsures(SolverUndecided, Acc(rel.solvability, 1 / 2)
            and rel.solvability == 1)
# axioms-end


# pure-start
# (no module-level pure helpers required: the conversion's decision is stated
# inline over the relation's solvability tag and the result's fields.)
# pure-end


def solution_set_of_relation(rel: Relation) -> SolutionSet:
    # pre-conditions-start
    # The relation is univariate (exactly one free variable) and lies in the
    # solver's two-way domain: the solver either determines its solution set
    # (solvability 0) or is undecided about it (solvability 1, the undecidability
    # signal). Relations on which the solver reports any other outcome (a domain
    # error, a malformed-argument error, a recursion-bound exhaustion, or
    # non-termination) have NO solvability value and are OUTSIDE this domain by
    # construction; the totality pinned below is claimed only over the two-way
    # domain, never over those relations (matching the conversion, which catches
    # only the undecidability signal and lets any other solver outcome escape).
    Requires(Acc(rel.n_free, 1 / 2) and Acc(rel.token, 1 / 2)
             and Acc(rel.sym, 1 / 2) and Acc(rel.solvability, 1 / 2))
    Requires(rel.n_free == 1)
    Requires(rel.solvability == 0 or rel.solvability == 1)
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rel.n_free, 1 / 2) and Acc(rel.token, 1 / 2)
            and Acc(rel.sym, 1 / 2) and Acc(rel.solvability, 1 / 2))
    Ensures(Acc(Result().is_fallback) and Acc(Result().cond)
            and Acc(Result().sym) and Acc(Result().over_reals))
    # Totality: the conversion returns a set for EVERY relation in its domain —
    # it never lets the solver's undecided signal escape (no Exsures declared, so
    # a normal return is required on both tags).
    #
    # When the solver determines the solution set, the conversion returns EXACTLY
    # that solver-produced set: a concrete set (not the fallback), pinned
    # field-for-field to the solver's own returned set (condition token, bound
    # symbol, base-domain flag — never values the conversion fabricates).
    Ensures(Implies(rel.solvability == 0,
                    Result().is_fallback == False
                    and Result().cond == solved_cond(rel)
                    and Result().sym == solved_sym(rel)
                    and Result().over_reals == solved_reals(rel)))
    # When the solver is undecided, the conversion returns the symbolic fallback
    # set built directly from the relation: it IS the fallback, it carries the
    # original relation as its defining condition, the conversion's variable as
    # its bound symbol, and the whole real line as its base domain.
    Ensures(Implies(rel.solvability == 1,
                    Result().is_fallback == True
                    and Result().cond == rel.token
                    and Result().sym == rel.sym
                    and Result().over_reals == True))
    # post-conditions-end
    # impl-start
    syms = rel.n_free
    Assert(syms == 1)
    x = rel.sym
    # Pre-patch: the solver is consulted directly and its result returned. When
    # the solver is undecided it raises the undecidability signal, which is left
    # to propagate to the caller instead of being turned into a fallback set.
    xset = solve_univariate(rel)  # type: SolutionSet
    return xset
    # impl-end
