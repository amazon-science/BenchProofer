"""Twin-artifact model for sphinx-doc__sphinx-9229.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A name that is documented as an attribute-style alias of another object can
  optionally carry an authored attribute comment (the documentation text placed
  alongside the assignment). The presence of such a comment changes two
  observable decisions:

    (1) The block of documentation lines selected for the alias. When the alias
        carries a non-empty authored comment, a documentation block IS selected
        (a PRESENT but EMPTY block — the comment lines are supplied through the
        attribute-documentation channel, so the block itself contributes no
        further lines but is present so the documentation pipeline still runs).
        When the alias carries NO authored comment, NO documentation block is
        selected at all (an ABSENT block, distinct from the present empty one).
        For a name that is NOT an attribute-style alias this decision is
        unchanged and the already-prepared documentation block is returned
        as-is.

    (2) Whether the synthetic "alias of <target>" placeholder line is
        substituted as the additional content. The placeholder is substituted
        for an attribute-style alias ONLY when the alias carries NO authored
        comment. When the alias carries a non-empty authored comment, the
        incoming additional content is left untouched (so the authored comment,
        emitted through the attribute-documentation channel, is what the reader
        sees, instead of the placeholder). For a name that is not an
        attribute-style alias the additional content is also left untouched.

The authored comment is modelled as a `List[int]` of code points produced by
the unchanged source-comment lookup (the module source analyzer); its only
discriminating property here is whether it is empty. The presence of a
documentation block is modelled as `Optional[List[int]]` (ABSENT ~ `None`,
distinguished from a present EMPTY list). The synthetic placeholder line is the
output of an unchanged cross-reference formatter, axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def placeholder_seq(target: List[int]) -> PSeq[int]:
    """The 'alias of <target>' placeholder text, as a pure sequence of code
    points, produced by the unchanged cross-reference formatter for the alias'
    target descriptor. Its defining property is that it is NON-EMPTY (it always
    spells out the target). Unchanged callee; provenance + executable soundness
    check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(target), 1 / 4))
    Ensures(len(Result()) > 0)


@ContractOnly
def make_placeholder(target: List[int]) -> List[int]:
    """The impl-callable face of the cross-reference formatter: a freshly-built
    code-point list equal to ``placeholder_seq`` of the target descriptor."""
    Requires(Acc(list_pred(target), 1 / 4))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(target), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == placeholder_seq(target))
# axioms-end


# pure-start
@Pure
def has_authored_comment(comment: List[int]) -> bool:
    """The discriminating property of the authored attribute comment: it is
    present iff it has at least one line/character. The empty lookup result
    (no comment authored alongside the alias) is the absent case."""
    Requires(Acc(list_pred(comment), 1 / 4))
    return len(comment) > 0


@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The element sequence of an optional content block: its code points when a
    block is present, the empty sequence when it is absent. Guards the None case
    so the spec can compare a produced block without indexing through None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)
# pure-end


def select_doc_block(is_attr_alias: bool, comment: List[int],
                     prepared: List[int]) -> Optional[List[int]]:
    # pre-conditions-start
    # Both carriers are read-only here (this decision selects, it does not
    # mutate): required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(comment), 1 / 2))
    Requires(Acc(list_pred(prepared), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(comment), 1 / 2))
    Ensures(Acc(list_pred(prepared), 1 / 2))
    # (1a) An attribute-style alias WITH a non-empty authored comment selects a
    # PRESENT but EMPTY documentation block (distinct from the absent case).
    Ensures(Implies(is_attr_alias and has_authored_comment(comment),
                    Result() is not None and Acc(list_pred(Result())) and
                    len(Result()) == 0))
    # (1b) An attribute-style alias WITHOUT an authored comment selects NO
    # documentation block at all (the absent case).
    Ensures(Implies(is_attr_alias and not has_authored_comment(comment),
                    Result() is None))
    # (1c) A name that is not an attribute-style alias is unchanged: the
    # already-prepared documentation block is returned as-is.
    Ensures(Implies(not is_attr_alias, Result() is prepared))
    # post-conditions-end
    # impl-start
    # PRE-PATCH behaviour for the alias branch: an attribute-style alias always
    # yields the ABSENT block, regardless of any authored comment (the comment
    # is never consulted). This is the bug the change repairs.
    if is_attr_alias:
        return None
    return prepared
    # impl-end


def alias_additional_content(is_attr_alias: bool, comment: List[int],
                             target: List[int],
                             more_content: Optional[List[int]]
                             ) -> Optional[List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(comment), 1 / 2))
    Requires(Acc(list_pred(target), 1 / 2))
    Requires(Implies(more_content is not None, Acc(list_pred(more_content), 1 / 2)))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(comment), 1 / 2))
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Implies(more_content is not None, Acc(list_pred(more_content), 1 / 2)))
    # (2a) The synthetic placeholder is substituted ONLY for an attribute-style
    # alias that carries NO authored comment; the result is then a present,
    # freshly-built block (own write permission) whose content is exactly the
    # formatter's placeholder sequence for the target.
    Ensures(Implies(is_attr_alias and not has_authored_comment(comment),
                    Result() is not None and Acc(list_pred(Result()), 1 / 4) and
                    opt_seq(Result()) == placeholder_seq(target)))
    # (2b) Otherwise (not an alias, OR an alias WITH a non-empty comment) the
    # incoming additional content is passed through untouched.
    Ensures(Implies(not (is_attr_alias and not has_authored_comment(comment)),
                    Result() is more_content))
    # post-conditions-end
    # impl-start
    if is_attr_alias and not has_authored_comment(comment):
        result = make_placeholder(target)  # type: Optional[List[int]]
        return result
    return more_content
    # impl-end
