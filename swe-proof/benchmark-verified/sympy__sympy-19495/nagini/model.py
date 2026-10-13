"""Twin-artifact model for sympy__sympy-19495.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A solution-set object carries a bound (dummy) variable, a defining
  predicate over that bound variable, and a base domain that the bound
  variable ranges over. Building such an object reduces it, and which
  reduction applies depends on the predicate's truth status AND on the shape
  of the base domain:

    * predicate identically FALSE  -> the empty domain;
    * base domain already empty    -> the empty domain (no member can
      qualify, whatever the predicate says);
    * predicate identically TRUE   -> the base domain itself (the predicate
      imposes no restriction, so every member of the base domain qualifies);
    * base domain given as an EXPLICIT FINITE LISTING -> the predicate is
      decided member by member: members it refutes are dropped, members it
      admits are kept outright, and the members whose status stays undecided
      remain gathered in a restricted object. That restricted object, when
      there is one, is keyed on the SAME bound variable and keeps the same
      non-trivial predicate;
    * base domain that is ITSELF a restricted object -> the two restrictions
      are MERGED into one: the result is a restricted object over the INNER
      base domain, whose predicate is the conjunction of both restrictions and
      whose bound variable is the one the merge settles on. That bound variable
      need NOT be the outer one: the merge may adopt the inner object's bound
      variable, or mint a fresh internal name when each variable occurs in the
      other's predicate. This is the ONE shape in which the bound variable is
      not carried over. The merge also performs no further reduction, so the
      merged object stands as a restricted object even when the conjoined
      predicate it carries is identically false;
    * otherwise                    -> the restricted object built from
      (bound variable, predicate, base domain).

  The truth status those cases turn on is the one the CONSTRUCTION ITSELF
  assigns to the predicate. Before it chooses a reduction it reads the predicate
  as a truth value, so a predicate handed over as a number, or as a quantity
  whose vanishing is already settled, counts as identically false or identically
  true and is reduced on accordingly rather than left standing as a restriction;
  a predicate handed over as an explicit listing of expressions is read as the
  requirement that every one of them vanish. Only a predicate the construction
  leaves undecided is a non-trivial restriction.

  When a FREE parameter of such an object (a parameter that is NOT the bound
  variable) is replaced by a value, the replacement is pushed into both the
  predicate and the base domain, and the resulting object is rebuilt under the
  SAME reduction WITH THE BOUND VARIABLE UNCHANGED. The bound variable is
  an internal name of the object; replacing a free parameter must never turn
  the bound variable into the replacement value, and must never re-interpret
  the result as ranging over the replacement value. In particular, if the
  predicate becomes identically true under the replacement, the result is
  exactly the (replacement-applied) base domain -- not a fresh restricted
  object keyed on the replacement value. The rebuild is the reduction above,
  so where the replacement-applied base domain turns out to be itself a
  restricted object the merge decides the bound variable, as stated there;
  that is the reduction's own doing and not an adoption of the replacement
  value.

  Both the construction of such an object and the replacement of a free
  parameter in one are TOTAL operations: each is required to DELIVER its
  reduced object to the caller. Deciding a predicate's truth status, deciding
  the shape of a base domain, and deciding an explicitly listed base domain
  member by member are each a bounded amount of work over finitely many
  members, so on every admitted input the operation runs to completion and
  hands back a result. Producing no answer at all -- looping without end, or
  re-entering the same replacement on the same unchanged arguments -- is not a
  permitted behaviour for either operation, and satisfies neither of them: an
  operation that never yields the reduced object has not performed the
  reduction, whatever it would have returned had it stopped.

  There is one input on which the reduction yields no domain at all: it REFUSES
  the input, when the bound variable it has SETTLED on is a compound expression
  rather than a name AND the predicate the object would carry retains no trace
  of that expression. That refusal is itself a stated outcome of the reduction
  (the "refused" result above), not a gap in what is specified: the operations
  are still total, and on such an input the answer they deliver is the refusal.
  Two things about it bear stating. The settled bound variable is not
  always the caller's -- the merge above may have adopted the inner object's, so
  the refusal is reachable from a perfectly ordinary caller-supplied name. And a
  compound settled bound variable is NOT refused on account of being compound:
  when it still occurs in the predicate the object would carry, the construction
  accepts it and the object stands keyed on that compound expression, exactly as
  the merge clause above says. Nowhere else does the reduction refuse; every
  other admitted input receives one of the three domains.

  Separately, where the predicate cannot be read as a truth value at all the
  operation is not specified: such an input has no truth status to branch on, so
  no reduction is asserted for it and the totality requirement is not a claim
  about it either.

Symbols and the predicate's truth status are modelled by small integer-tagged
carriers (Nagini bans rich-object indexing); a restricted object is a minimal
class holding only the three observed fields. The shape of the base domain is
carried by its own tag, and the member-by-member outcome for an explicitly
listed base domain is folded into arguments the caller supplies, exactly as
the replacement-applied predicate and base domain are. mapping.md gives the
field bijection to the real objects.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# ---------------------------------------------------------------------------
# Truth status of a predicate after a replacement is applied.
#   COND_FALSE : the predicate is identically false
#   COND_TRUE  : the predicate is identically true
#   COND_OPEN  : the predicate stays a non-trivial restriction
COND_FALSE = 0
COND_TRUE = 1
COND_OPEN = 2

# Kind of a canonical result object.
#   K_EMPTY   : the empty domain
#   K_BASE    : the base domain passes through unrestricted
#   K_SET     : a restricted object (bound var, open predicate, base domain)
#   K_REFUSED : the construction REFUSES the input and yields no domain at all.
#               This is an outcome of the reduction, not a domain: it is what
#               the construction does when the bound variable it has settled on
#               is one it cannot work with (see MERGE_REFUSED below). Naming it
#               keeps the operations total -- they still always deliver an
#               answer, and the answer on those inputs is "refused" -- so the
#               reduction is pinned everywhere rather than left unconstrained
#               on a corner.
K_EMPTY = 0
K_BASE = 1
K_SET = 2
K_REFUSED = 3

# Shape of the base domain the bound variable ranges over. The reduction that
# applies depends on it, so it is an observed input and not an opaque id.
#   BASE_EMPTY  : the base domain is empty
#   BASE_LISTED : the base domain is an explicit finite listing of members,
#                 so the predicate can be decided member by member
#   BASE_MERGED : the base domain is ITSELF a restricted object, so the two
#                 restrictions are merged and the merge decides the bound
#                 variable of the result
#   BASE_PLAIN  : any other base domain (members are not enumerated)
BASE_EMPTY = 0
BASE_LISTED = 1
BASE_PLAIN = 2
BASE_MERGED = 3

# The bound variable a merge settles on may be one the construction then
# REFUSES: it is a compound expression rather than a name, and the predicate the
# merged object would carry retains no trace of it. On such an input no domain
# is produced, so there is no bound variable of a result to carry an identity --
# MERGE_REFUSED is that absence, and it is what the merge reports instead of an
# identity. The operations below ARE specified on it: they deliver K_REFUSED,
# which is why they stay total there. This is NOT the same thing as a compound
# settled bound variable per se: one the predicate still mentions is accepted and
# IS carried, with its own identity, like any other.
MERGE_REFUSED = 0


class Result0:
    """A canonical solution-set object after reduction.

    Fields (the only observed ones):
      kind : K_EMPTY / K_BASE / K_SET / K_REFUSED
      sym  : identity of the bound variable (meaningful only when kind==K_SET)
      base : identity of the base domain
      cond : truth tag of the predicate (COND_* ; only COND_OPEN when kind==K_SET)
    """

    def __init__(self, kind: int, sym: int, base: int, cond: int) -> None:
        # Recording the observed fields of a reduced object is a bounded
        # construction that must complete and yield the object.
        Requires(MustTerminate(1))
        self.kind = kind  # type: int
        self.sym = sym    # type: int
        self.base = base  # type: int
        self.cond = cond  # type: int
        Ensures(Acc(self.kind) and self.kind == kind)
        Ensures(Acc(self.sym) and self.sym == sym)
        Ensures(Acc(self.base) and self.base == base)
        Ensures(Acc(self.cond) and self.cond == cond)


# axioms-start
# (none — every operation the change touches is modelled deeply below)
# axioms-end


# pure-start
# (no pure helpers — the canonical reduction rule is realised by `build`)
# pure-end


def build(sym: int, cond: int, base: int, base_kind: int,
          listed_kind: int, listed_base: int,
          merged_sym: int, merged_base: int) -> Result0:
    """The construction/reduction rule (mirrors the set constructor): a false
    predicate collapses to the empty domain, an empty base domain collapses to
    the empty domain, a true predicate collapses to the base domain, an
    explicitly listed base domain is decided member by member, a base domain
    that is itself a restricted object is merged with it, and otherwise a
    restricted object on the given bound variable is produced.

    `listed_kind` / `listed_base` carry the member-by-member outcome for an
    explicitly listed base domain: which kind of object the surviving members
    form and the identity of the domain it is built over. They are relevant
    only when the base domain is an explicit listing and the predicate stays a
    non-trivial restriction.

    `merged_sym` / `merged_base` likewise carry the outcome of merging with a
    base domain that is itself a restricted object: the bound variable the
    merge settles on and the inner base domain the merged object stands over.
    They are relevant only when the base domain is such an object. The merged
    predicate is the conjunction of the two restrictions; the merge runs no
    further reduction, so no truth status is claimed of it here. `merged_sym`
    is MERGE_REFUSED on exactly the merges the construction then refuses (a
    settled bound variable that is a compound expression the merged predicate
    retains no trace of); on those the result is the refusal itself, pinned
    below, because there is no domain for the merge to stand over."""
    # pre-conditions-start
    # TOTALITY: building the object is a bounded decision over the predicate's
    # truth status and the base domain's shape (and, for an explicit listing,
    # over its finitely many members). It must DELIVER the reduced object to
    # the caller on every admitted input rather than merely never contradict
    # the clauses below; an operation that produces no answer has not built
    # anything.
    Requires(MustTerminate(2))
    Requires(cond == COND_FALSE or cond == COND_TRUE or cond == COND_OPEN)
    Requires(base_kind == BASE_EMPTY or base_kind == BASE_LISTED
             or base_kind == BASE_PLAIN or base_kind == BASE_MERGED)
    Requires(listed_kind == K_EMPTY or listed_kind == K_BASE
             or listed_kind == K_SET)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().kind) and Acc(Result().sym) and Acc(Result().base)
            and Acc(Result().cond))
    Ensures(Implies(cond == COND_FALSE, Result().kind == K_EMPTY))
    # An empty base domain leaves nothing that could qualify.
    Ensures(Implies(base_kind == BASE_EMPTY, Result().kind == K_EMPTY))
    # A predicate that imposes no restriction lets the whole base domain
    # through, provided the base domain has members at all.
    Ensures(Implies(cond == COND_TRUE and base_kind != BASE_EMPTY,
                    Result().kind == K_BASE and Result().base == base))
    # A non-trivial predicate over a base domain whose members are not
    # enumerated yields the restricted object keyed on the given bound
    # variable over that same base domain.
    Ensures(Implies(cond == COND_OPEN and base_kind == BASE_PLAIN,
                    Result().kind == K_SET and Result().sym == sym
                    and Result().base == base and Result().cond == COND_OPEN))
    # Over an explicit finite listing the predicate is decided member by
    # member; the surviving members form the folded outcome.
    Ensures(Implies(cond == COND_OPEN and base_kind == BASE_LISTED,
                    Result().kind == listed_kind))
    Ensures(Implies(cond == COND_OPEN and base_kind == BASE_LISTED
                    and listed_kind != K_EMPTY,
                    Result().base == listed_base))
    # Whatever restricted object survives the member-by-member decision is
    # still keyed on the given bound variable, with the predicate open.
    Ensures(Implies(cond == COND_OPEN and base_kind == BASE_LISTED
                    and listed_kind == K_SET,
                    Result().sym == sym and Result().cond == COND_OPEN))
    # A base domain that is itself a restricted object is MERGED with it: the
    # result is a restricted object over the INNER base domain, keyed on the
    # bound variable the merge settles on -- which is where, and only where,
    # the given bound variable is not carried over. No further reduction is
    # performed, so the object stands whatever its conjoined predicate says.
    # Claimed on the merges the construction accepts.
    Ensures(Implies(cond == COND_OPEN and base_kind == BASE_MERGED
                    and merged_sym != MERGE_REFUSED,
                    Result().kind == K_SET and Result().sym == merged_sym
                    and Result().base == merged_base))
    # And where the merge settles on a bound variable the construction cannot
    # work with, the outcome is exactly the refusal -- no domain of any kind.
    # Pinning this rather than leaving it open matters: it is the one corner
    # where the construction hands back no object, and an implementation that
    # invented some domain here (empty, or one keyed on a value of its own
    # choosing) would not be the real reduction.
    Ensures(Implies(cond == COND_OPEN and base_kind == BASE_MERGED
                    and merged_sym == MERGE_REFUSED,
                    Result().kind == K_REFUSED))
    # A refusal happens ONLY there: on every other admitted input the
    # construction really does deliver one of the three domains.
    Ensures(Implies(not (cond == COND_OPEN and base_kind == BASE_MERGED
                         and merged_sym == MERGE_REFUSED),
                    Result().kind != K_REFUSED))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    if cond == COND_FALSE:
        return Result0(K_EMPTY, sym, base, cond)
    elif base_kind == BASE_EMPTY:
        return Result0(K_EMPTY, sym, base, cond)
    elif cond == COND_TRUE:
        return Result0(K_BASE, sym, base, cond)
    elif base_kind == BASE_LISTED:
        return Result0(listed_kind, sym, listed_base, cond)
    elif base_kind == BASE_MERGED:
        if merged_sym == MERGE_REFUSED:
            return Result0(K_REFUSED, merged_sym, merged_base, cond)
        return Result0(K_SET, merged_sym, merged_base, cond)
    else:
        return Result0(K_SET, sym, base, cond)
    # impl-end


def replace_free_parameter(self_sym: int, new: int,
                           cond_after: int, base_after: int,
                           base_kind: int, listed_kind: int,
                           listed_base: int, merged_sym: int,
                           merged_base: int) -> Result0:
    """Replace a FREE parameter (not the bound variable) inside a restricted
    solution-set object.

    The caller has already pushed the replacement into the predicate and the
    base domain, yielding `cond_after` (truth tag of the new predicate),
    `base_after` (identity of the new base domain) and `base_kind` (its
    shape); `listed_kind` / `listed_base` carry the member-by-member outcome
    when that new base domain is an explicit finite listing, and `merged_sym`
    / `merged_base` the outcome of merging when it is itself a restricted
    object. This function rebuilds the result. `self_sym` is the object's
    bound variable and `new` is the replacement value.

    Desired behaviour: the bound variable of any rebuilt restricted object is
    the original `self_sym`; `new` is never adopted as the bound variable.
    Hence a predicate that became identically true yields exactly the base
    domain. The one shape in which the bound variable is not carried over is
    the merge with a base domain that is itself a restricted object, where the
    reduction itself settles the bound variable (`merged_sym`) -- again not by
    adopting the replacement value. `merged_sym` is MERGE_REFUSED on exactly
    the merges the rebuild then refuses outright, yielding no domain; on those
    the result is the refusal itself, pinned below.
    """
    # pre-conditions-start
    # TOTALITY: replacing a free parameter is likewise a bounded operation --
    # rebuild the object under the same reduction and hand it back. It must
    # DELIVER that object on every admitted input; re-entering the same
    # replacement on the same unchanged arguments, or otherwise never
    # answering, does not perform the replacement. The measure exceeds the
    # one the construction demands, so the rebuild may invoke it.
    Requires(MustTerminate(3))
    Requires(cond_after == COND_FALSE or cond_after == COND_TRUE
             or cond_after == COND_OPEN)
    Requires(base_kind == BASE_EMPTY or base_kind == BASE_LISTED
             or base_kind == BASE_PLAIN or base_kind == BASE_MERGED)
    Requires(listed_kind == K_EMPTY or listed_kind == K_BASE
             or listed_kind == K_SET)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().kind) and Acc(Result().sym) and Acc(Result().base)
            and Acc(Result().cond))
    # The rebuilt object is the reduction keyed on the ORIGINAL bound variable
    # self_sym, applied to (cond_after, base_after) and that base domain's
    # shape.
    Ensures(Implies(cond_after == COND_FALSE, Result().kind == K_EMPTY))
    Ensures(Implies(base_kind == BASE_EMPTY, Result().kind == K_EMPTY))
    # A predicate that collapsed to true yields the base domain itself —
    # never a fresh restricted object on `new`.
    Ensures(Implies(cond_after == COND_TRUE and base_kind != BASE_EMPTY,
                    Result().kind == K_BASE and Result().base == base_after))
    # An open predicate over a base domain whose members are not enumerated
    # yields a restricted object whose bound variable is the ORIGINAL self_sym
    # (not `new`) over the replacement-applied base domain.
    Ensures(Implies(cond_after == COND_OPEN and base_kind == BASE_PLAIN,
                    Result().kind == K_SET and Result().sym == self_sym
                    and Result().base == base_after
                    and Result().cond == COND_OPEN))
    # Over an explicit finite listing the member-by-member outcome governs the
    # kind and the surviving domain.
    Ensures(Implies(cond_after == COND_OPEN and base_kind == BASE_LISTED,
                    Result().kind == listed_kind))
    Ensures(Implies(cond_after == COND_OPEN and base_kind == BASE_LISTED
                    and listed_kind != K_EMPTY,
                    Result().base == listed_base))
    # ... and any surviving restricted object is STILL keyed on the original
    # self_sym, never on `new`.
    Ensures(Implies(cond_after == COND_OPEN and base_kind == BASE_LISTED
                    and listed_kind == K_SET,
                    Result().sym == self_sym
                    and Result().cond == COND_OPEN))
    # A replacement-applied base domain that is itself a restricted object is
    # MERGED with it: the rebuilt object stands over the INNER base domain and
    # is keyed on the bound variable the merge settles on. This is the only
    # shape in which the result is not keyed on self_sym, and the bound
    # variable is still the reduction's choice, never the replacement value as
    # such. Claimed on the merges the reduction accepts.
    Ensures(Implies(cond_after == COND_OPEN and base_kind == BASE_MERGED
                    and merged_sym != MERGE_REFUSED,
                    Result().kind == K_SET and Result().sym == merged_sym
                    and Result().base == merged_base))
    # And where the merge settles on a bound variable the reduction cannot work
    # with, the outcome is exactly the refusal -- not the empty domain, and not
    # a restricted object keyed on the replacement value or on anything else.
    Ensures(Implies(cond_after == COND_OPEN and base_kind == BASE_MERGED
                    and merged_sym == MERGE_REFUSED,
                    Result().kind == K_REFUSED))
    # A refusal happens ONLY there: everywhere else a domain is delivered.
    Ensures(Implies(not (cond_after == COND_OPEN and base_kind == BASE_MERGED
                         and merged_sym == MERGE_REFUSED),
                    Result().kind != K_REFUSED))
    # post-conditions-end
    # invariants-start
    # invariants-end
    # impl-start
    return build(self_sym, cond_after, base_after, base_kind, listed_kind,
                 listed_base, merged_sym, merged_base)
    # impl-end
