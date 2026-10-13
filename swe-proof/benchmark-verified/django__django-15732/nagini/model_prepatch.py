"""Twin-artifact model for django__django-15732.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composed-uniqueness constraint is being removed from a table. The set of
  candidate constraint names that were discovered on the affected column(s) is
  given, together with the DEFAULT name that the composed-uniqueness rule would
  itself generate for those column(s). Exactly one constraint must be selected
  for removal; if the candidates cannot be reduced to exactly one, selection is
  refused rather than removing an arbitrary constraint.

  The desired selection discipline:

    * If the discovered set already contains exactly one candidate, that
      candidate is the one removed.

    * If the operation is a uniqueness removal AND the backend permits several
      uniqueness constraints to coexist on the same column(s), then a discovered
      set that also contains the rule's own DEFAULT name is disambiguated to
      that default name alone — so the constraint that belongs to the composed
      rule is the one removed, even when an independent single-column uniqueness
      constraint is present on the same column.

    * In every other situation where the discovered set does not reduce to a
      single candidate (no candidate; several candidates none of which is the
      default; or disambiguation is unavailable), selection is impossible and
      the operation fails rather than removing an arbitrary constraint.

  The pinned behaviour is exactly that: the removed name is the rule's default
  whenever disambiguation applies and the default is among the candidates;
  otherwise the sole candidate; and a non-resolvable set raises the
  ambiguous-selection failure and never removes an arbitrary constraint.

Constraint names are modelled as distinct integer identifiers; the discovered
set is a `List[int]` of such identifiers and the rule's default name is one
identifier. The discriminating observable is purely WHICH name is selected (or
that selection fails), not the characters of any name. The ambiguous-selection
failure is a user-defined exception class (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class AmbiguousConstraintSelection(Exception):
    """Signals that the discovered candidate set does not reduce to exactly one
    constraint, so no single constraint can be removed. User-defined stand-in
    for the not-exactly-one-constraint failure the desired behaviour raises; a
    builtin exception in an `Exsures` crashes the Nagini translator (mapping.md
    §2)."""


# axioms-start
# (no callee is axiomatized: the discovery of the candidate set and the
# generation of the rule's default name are UNCHANGED upstream operations whose
# results are passed in as inputs; the changed operation — the disambiguating
# selection over those inputs — is spelled out directly over the modelled
# carrier. There is no unchanged opaque callee whose contract the proof
# consumes inside the changed operation. mapping.md §3.)
# axioms-end


# pure-start
@Pure
def disambiguates(unique: bool, feature_on: bool, n_candidates: int) -> bool:
    """The condition under which a multi-candidate discovered set may be
    narrowed to the rule's own default name: a uniqueness removal, on a backend
    that allows several uniqueness constraints to coexist on the same
    column(s), with at least one candidate discovered."""
    return unique and feature_on and n_candidates >= 1
# pure-end


def select_constraint_to_remove(candidates: List[int], default_name: int,
                                 unique: bool, feature_on: bool) -> int:
    # pre-conditions-start
    # ``candidates`` is the set of constraint names discovered on the column(s)
    # (read-only here: it is inspected, never mutated — fractional permission,
    # directive 5, so no impl can satisfy a postcondition by overwriting it).
    Requires(Acc(list_pred(candidates), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(candidates), 1 / 2))
    # Normal-return domain: a single constraint is returned ONLY when the
    # discovered set actually reduces to exactly one candidate — either because
    # disambiguation applies and the rule's own default name is among the
    # candidates (the set narrows to that one name), or because the set already
    # holds exactly one candidate. In every other situation no normal return is
    # permitted (the operation must refuse rather than remove an arbitrary
    # constraint); this makes the refusal REQUIRED, not merely allowed, closing
    # the silent-arbitrary-selection hole.
    Ensures((disambiguates(unique, feature_on, len(candidates))
             and (default_name in ToSeq(candidates)))
            or (len(candidates) == 1))
    # Disambiguation path: when narrowing applies AND the rule's own default
    # name is among the discovered candidates, the SELECTED name is exactly that
    # default name — and it is a genuine member of the discovered set (it is the
    # candidate that belongs to the composed rule, not an invented value).
    Ensures(Implies(disambiguates(unique, feature_on, len(candidates))
                    and (default_name in ToSeq(candidates)),
                    Result() == default_name))
    Ensures(Implies(disambiguates(unique, feature_on, len(candidates))
                    and (default_name in ToSeq(candidates)),
                    Result() in ToSeq(candidates)))
    # Sole-candidate path: when the discovered set holds exactly one candidate,
    # that candidate is the selected name. (This also covers the unique removal
    # whose single discovered candidate happens to be the default.)
    Ensures(Implies(len(candidates) == 1, Result() == candidates[0]))
    # Whatever is selected is always one of the discovered candidates: a removal
    # never targets a name that was not discovered.
    Ensures(Result() in ToSeq(candidates))
    # The ambiguous-selection failure: when selection cannot reduce the
    # discovered set to a single candidate — i.e. it is NOT the case that there
    # is exactly one candidate, NOR that disambiguation applies with the default
    # among the candidates — the operation raises and removes nothing.
    Exsures(AmbiguousConstraintSelection,
            Acc(list_pred(candidates), 1 / 2)
            and (len(candidates) != 1)
            and not (disambiguates(unique, feature_on, len(candidates))
                     and (default_name in ToSeq(candidates))))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON (buggy): the discovered set is used as-is, with no
    # disambiguation toward the composed rule's own default name. Selection
    # succeeds only when the discovered set already holds exactly one candidate;
    # any other size — including a uniqueness removal whose column also carries
    # an independent single-column uniqueness constraint, so two candidates are
    # discovered — fails the count check, even when the rule's default name is
    # among them. This is precisely the missing-disambiguation defect.
    if len(candidates) == 1:
        return candidates[0]
    raise AmbiguousConstraintSelection()
    # impl-end
