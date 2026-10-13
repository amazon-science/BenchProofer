"""Twin-artifact model for pytest-dev__pytest-7205.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a parametrized fixture's recorded parameter value is rendered for the
  human-readable single-line trace of fixture setup/teardown, it must be shown
  through its size-limited *programmer's representation* rather than through its
  plain text form. For a parameter value that is an ordinary short text string
  (no embedded apostrophe, short enough not to be elided), the programmer's
  representation surrounds the text with apostrophe delimiters: the rendered
  token is the apostrophe code point, then the verbatim text, then the
  apostrophe code point. The plain text form, by contrast, would show the bare
  text with no surrounding delimiters. The rendering is also length-bounded:
  it never exceeds the configured size limit.

  Concretely the rendered token for such a value `s` is `' + s + '` (apostrophe
  U+0027 = code point 39 on each side), so a value whose text is `foo` is shown
  as `'foo'`, not as `foo`.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The
size-limited programmer's representation is modelled DEEPLY as the apostrophe
delimiting (`repr_quote`) for the tested domain of short delimiter-free text;
its equality to the real size-limited representation helper on that domain is
validated out-of-band by axiom_check.py (G-AX), NOT consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The genuinely changed operation -- rendering the recorded
# parameter through the size-limited programmer's representation instead of the
# plain text form -- is modelled DEEPLY as `repr_quote` (the apostrophe
# delimiting) over the tested domain of short, delimiter-free text. The real
# representation helper is therefore an A-reference (validated == the deep model
# by axiom_check.py / G-AX), never a @ContractOnly the proof consumes.
# axioms-end


# pure-start
QUOTE = 39  # the apostrophe delimiter code point U+0027


@Pure
def repr_quote(s: PSeq[int]) -> PSeq[int]:
    """The size-limited programmer's representation of a short, delimiter-free
    text value: the apostrophe delimiter, the verbatim code points, the
    apostrophe delimiter. (Deep model of the rendering the trace now uses.)"""
    return PSeq(QUOTE) + s + PSeq(QUOTE)
# pure-end


def render_param_token(param: List[int], maxsize: int) -> List[int]:
    # pre-conditions-start
    # `param` is the recorded parameter text; it is read only (fractional perm).
    Requires(Acc(list_pred(param), 1 / 2))
    # Tested domain: a short, plainly-printable text value whose programmer's
    # representation is simply the verbatim text wrapped in apostrophe
    # delimiters -- short enough that the size limit does not elide it, and made
    # of plain printable code points only (no apostrophe delimiter, no backslash,
    # no control characters), so the representation introduces no escapes. This
    # is the domain the parametrized-fixture trace tests exercise.
    Requires(maxsize >= 2)
    Requires(len(param) + 2 <= maxsize)
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(param),
                                             param[k] >= 32 and param[k] <= 126
                                             and param[k] != QUOTE
                                             and param[k] != 92))))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(param), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered token is the size-limited programmer's representation of the
    # value: the verbatim text wrapped in apostrophe delimiters.
    Ensures(ToSeq(Result()) == repr_quote(ToSeq(param)))
    # Stated structurally, so a plain-text rendering (bare `param`) is rejected:
    # the token is delimited on both ends by the apostrophe, and its interior is
    # exactly the parameter text.
    Ensures(len(Result()) == len(param) + 2)
    Ensures(Result()[0] == QUOTE)
    Ensures(Result()[len(Result()) - 1] == QUOTE)
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(param),
                                           Result()[k + 1] == param[k]))))
    # The rendering respects the size limit.
    Ensures(len(Result()) <= maxsize)
    # post-conditions-end
    # impl-start
    result = [QUOTE]  # type: List[int]
    i = 0
    while i < len(param):
        # invariants-start
        Invariant(Acc(list_pred(param), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(param))
        Invariant(len(param) + 2 <= maxsize)
        Invariant(len(result) == i + 1)
        Invariant(result[0] == QUOTE)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  result[k + 1] == param[k]))))
        Invariant(ToSeq(result) == PSeq(QUOTE) + ToSeq(param).take(i))
        Invariant(MustTerminate(len(param) - i + 1))
        # invariants-end
        result.append(param[i])
        i = i + 1
    result.append(QUOTE)
    return result
    # impl-end
