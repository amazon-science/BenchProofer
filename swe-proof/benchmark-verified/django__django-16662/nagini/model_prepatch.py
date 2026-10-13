"""Twin-artifact model for django__django-16662.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of import lines is arranged into the order they should appear in
  a generated source file. Two attributes of each line decide its position:

    * whether the line is a plain module import (``import X``) or an
      object import drawn from a module (``from Y import ...``); and
    * the name of the module the line refers to.

  The required order places EVERY plain module-import line before EVERY
  from-import line (the two forms are grouped, plain imports first), and within
  each group the lines are ordered by their module name. Equivalently, the lines
  are ordered ascending by the pair (is-a-from-import, module-name), the group
  flag being the PRIMARY ordering criterion and the module name the secondary
  one. The arrangement is a rearrangement of exactly the given lines (no line is
  added, dropped, or duplicated).

  The discriminating case the contract pins: a from-import line whose module
  name sorts BEFORE a plain module-import line's module name must still appear
  AFTER that plain import line, because the group flag dominates the module
  name. Ordering by module name alone would interleave the two groups and is
  rejected.

Each line is characterised by two integers: a group flag in {0, 1} (0 = plain
module import, 1 = from-import) and an order-preserving integer code of the
module-name sort token (Nagini bans ``str`` indexing; the code preserves the
lexicographic ordering of the module names, see mapping.md). The pair is
linearised into a single ordering key ``compkey`` whose ascending integer order
is exactly the ascending order of the pair (group flag dominating). The
specification is carried over the pure sequence/multiset theory (``PSeq`` /
``ToMS``). The modelled domain is the three-line configuration that exhibits the
behaviour (see mapping.md / refinement.md for the domain choice); the ordering
is produced by a comparison arrangement pinned to be a sorted rearrangement.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the ordering key is the changed decision and is
# modelled deeply as the linearised pair `compkey`. The comparison sort the
# real code performs is the standard library `sorted`; that the ascending order
# of `compkey` agrees with the ascending order of the real pair key is an
# A-reference validated out-of-band by axiom_check.py / G-AX, not a consumed
# axiom.)
# axioms-end


# pure-start
@Pure
def compkey(is_from: int, module: int) -> int:
    """The single ordering key for a line, linearising the pair
    (group flag, module code). The group flag is scaled by a bound strictly
    larger than any module code, so ascending integer order on `compkey` is
    exactly ascending order on the pair with the group flag dominating: every
    plain-import line (flag 0) keys below every from-import line (flag 1)
    regardless of module code, and within a group the module code decides."""
    Ensures(Result() == is_from * 1000000000 + module)
    return is_from * 1000000000 + module
# pure-end


def arrange_lines(flags: List[int], modules: List[int]) -> List[int]:
    # pre-conditions-start
    # `flags[k]` is the group flag of line k (0 = plain import, 1 = from-import);
    # `modules[k]` is the order-preserving code of line k's module name, bounded
    # below the group scale so the linearisation is order-preserving. Both
    # carriers are read-only (fractional permission: arranging never mutates the
    # line attributes).
    Requires(Acc(list_pred(flags), 1 / 2))
    Requires(Acc(list_pred(modules), 1 / 2))
    Requires(len(flags) == 3 and len(modules) == 3)
    Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
             flags[k] == 0 or flags[k] == 1)))
    Requires(Forall(int, lambda k: Implies(0 <= k and k < 3,
             0 <= modules[k] and modules[k] < 1000000000)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(flags), 1 / 2))
    Ensures(Acc(list_pred(modules), 1 / 2))
    Ensures(len(flags) == 3 and len(modules) == 3)
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 3)
    # The output is a rearrangement of EXACTLY the given lines' keys: no key is
    # added, dropped, or duplicated (grounds the result in the actual input).
    Ensures(ToMS(ToSeq(Result())) == ToMS(PSeq(
        compkey(flags[0], modules[0]),
        compkey(flags[1], modules[1]),
        compkey(flags[2], modules[2]))))
    # The output is ascending in the ordering key: by `compkey`'s construction
    # this places every plain-import line before every from-import line, and
    # orders by module name within each group.
    Ensures(Result()[0] <= Result()[1] and Result()[1] <= Result()[2])
    # post-conditions-end
    # impl-start
    # Pre-fix behaviour: arrange by module name ALONE, ignoring the group flag.
    # The keys are still produced, but the comparison that decides the order
    # uses only the module code, so the two forms interleave by module name.
    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    m0 = modules[0]
    m1 = modules[1]
    m2 = modules[2]
    x = k0
    y = k1
    z = k2
    mx = m0
    my = m1
    mz = m2
    if mx > my:
        t = x
        x = y
        y = t
        tm = mx
        mx = my
        my = tm
    if my > mz:
        t2 = y
        y = z
        z = t2
        tm2 = my
        my = mz
        mz = tm2
    if mx > my:
        t3 = x
        x = y
        y = t3
        tm3 = mx
        mx = my
        my = tm3
    Assert(ToMS(PSeq(x, y, z)) == ToMS(PSeq(k0, k1, k2)))
    res = [x, y, z]  # type: List[int]
    Assert(ToSeq(res) == PSeq(x, y, z))
    return res
    # impl-end
