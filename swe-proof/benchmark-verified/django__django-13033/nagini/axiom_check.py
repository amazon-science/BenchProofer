#!/usr/bin/env python3
"""G-AX soundness check for django__django-13033.

This bundle consumes NO @ContractOnly axiom: the changed decision predicate in
`find_ordering_name` is modelled deeply (a pure boolean/sequence comparison over
the inputs). The single external fact the model's precondition encodes is the
semantics of `pieces = name.split(LOOKUP_SEP)` (LOOKUP_SEP == '__'):

    Implies(len(pieces) > 1, name != last_segment(pieces))

i.e. a lookup path that splits into more than one segment is never equal to its
own final segment (it carries the separator and the preceding segments). This
script executes the REAL CPython `str.split('__')` on boundary inputs plus
randomized fuzz and asserts that invariant on every observation, exactly as the
model's precondition claims. It also reproduces the issue's discriminating case
to confirm the model's intended semantics matches reality.

stdlib-only; exit 0 iff the invariant holds on every observation.
"""
import random
import string
import sys

LOOKUP_SEP = "__"


def split_invariant_holds(name):
    """The fact the model's precondition encodes for one `name`."""
    pieces = name.split(LOOKUP_SEP)
    # pieces is always non-empty (str.split never returns []).
    if len(pieces) <= 1:
        return True
    return name != pieces[-1]


def main():
    violations = []
    checked = 0

    # --- Boundary / structured inputs ---------------------------------------
    boundary = [
        "",                       # empty
        "pk",                     # the pk shortcut
        "root_id",                # a bare attname (single segment)
        "record",                 # single relation segment
        "record__root_id",        # the issue reproducer (multi-segment attname)
        "record__root",           # multi-segment relation
        "record__root__id",       # explicit pk descent
        "a__b__c__d",             # deep path
        "__",                     # separator only -> ['', '']
        "__x",                    # leading separator
        "x__",                    # trailing separator
        "a____b",                 # doubled separator -> ['a', '', 'b']
        "_",                      # single underscore (not a separator)
        "a_b",                    # single underscore inside a name
        "a_b__c_d",               # mixed single/double underscores
        "____",                   # only separators
        "x",                      # one char
        "id",
    ]
    for name in boundary:
        checked += 1
        if not split_invariant_holds(name):
            violations.append((name, name.split(LOOKUP_SEP)))

    # Explicit reproducer sanity: the model's intended discrimination.
    name = "record__root_id"
    pieces = name.split(LOOKUP_SEP)
    attname = "root_id"
    assert pieces[-1] == attname, "reproducer: final segment is the attname"
    assert (attname != pieces[-1]) is False, "patched conjunct must be False here"
    assert (attname != name) is True, "pre-patch conjunct must be True here"

    # --- Randomized fuzz ----------------------------------------------------
    rng = random.Random(13033)
    alphabet = string.ascii_lowercase + string.digits + "_"
    for _ in range(50000):
        n = rng.randint(0, 12)
        name = "".join(rng.choice(alphabet) for _ in range(n))
        checked += 1
        if not split_invariant_holds(name):
            violations.append((name, name.split(LOOKUP_SEP)))

    # Fuzz over assembled segment lists rejoined with the separator (the exact
    # split-then-rejoin shape the model assumes: '__'.join(pieces) == name).
    for _ in range(50000):
        k = rng.randint(1, 5)
        segs = []
        for _ in range(k):
            m = rng.randint(0, 5)
            segs.append("".join(rng.choice(string.ascii_lowercase) for _ in range(m)))
        name = LOOKUP_SEP.join(segs)
        checked += 1
        if not split_invariant_holds(name):
            violations.append((name, name.split(LOOKUP_SEP)))

    if violations:
        print("UNSOUND: split invariant violated on %d input(s):" % len(violations))
        for name, pieces in violations[:20]:
            print("  name=%r split=%r" % (name, pieces))
        sys.exit(1)

    print("SOUND: split invariant (len(pieces)>1 => name != pieces[-1]) holds "
          "on %d observations of real str.split('__')." % checked)
    sys.exit(0)


if __name__ == "__main__":
    main()
