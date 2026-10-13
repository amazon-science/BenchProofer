#!/usr/bin/env python3
"""G-CONF: differential conformance for sympy__sympy-19346.

Runs INSIDE the instance image with the GOLD patch applied (apply_gold=True,
PYTHONPATH=/testbed). Exercises the two modeled functions — the canonical
representation of a mapping and of an unordered collection — by comparing the
Lean impl's R/I shadow against the REAL post-patch `srepr`.

Lean ↔ Python bijection (mapping.md):
  - `elemRepr x`        == real `srepr(x)` of one contained element (the
                           canonical recursive renderer the toolkit uses);
  - dict shadow         == "{" + ", ".join("%s: %s" % (srepr(k), srepr(v))) + "}"
                           over the dict's items in iteration order;
  - set shadow          == "set()" if empty else
                           "{" + ", ".join(srepr(e)) + "}" over iteration order.

The Lean impl threads each contained element's rendering through the SAME
recursive renderer (`elemRepr`), exactly as the real `self.doprint`/`reprify`
calls do — so the shadow rebuilds the real `srepr(container)` from the real
`srepr` of each element. Sets/dicts have implementation-defined iteration order,
so we drive `srepr` and the shadow over the SAME live container object (identical
iteration order) and compare the resulting strings byte-for-byte.

Exit 0 iff zero disagreements over a boundary catalogue plus >=1e5 randomized
draws. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 19346
N_RANDOM = 120_000  # >= 1e5


def main() -> int:
    from sympy import srepr, Symbol, Integer, Rational

    checked = 0
    mism = 0

    def dict_shadow(d):
        # Lean R/I shadow of implementation_dictRepr over the SAME object's
        # iteration order: each entry rendered key ": " value, both via srepr
        # (the canonical recursive renderer == elemRepr), joined by ", ".
        parts = ["%s: %s" % (srepr(k), srepr(v)) for k, v in d.items()]
        return "{%s}" % ", ".join(parts)

    def set_shadow(s):
        # Lean R/I shadow of implementation_setRepr: dedicated empty literal,
        # else each element via srepr, joined by ", ".
        if not s:
            return "set()"
        parts = [srepr(e) for e in s]
        return "{%s}" % ", ".join(parts)

    def check_dict(d):
        nonlocal checked, mism
        real = srepr(d)
        exp = dict_shadow(d)
        if real != exp:
            print(f"DICT MISMATCH d={d!r} real={real!r} expected={exp!r}")
            mism += 1
        checked += 1

    def check_set(s):
        nonlocal checked, mism
        real = srepr(s)
        exp = set_shadow(s)
        if real != exp:
            print(f"SET MISMATCH s={s!r} real={real!r} expected={exp!r}")
            mism += 1
        checked += 1

    x, y, z = Symbol('x'), Symbol('y'), Symbol('z')

    # ---- boundary / hand-picked catalogue ----
    boundary_dicts = [
        {},
        {x: y},
        {x: y, y: z},
        {x: {y: z}},                 # nested dict (recursion must reach down)
        {x: Integer(3)},
        {Integer(1): x, Integer(2): y},
        {x: [y, z]},                 # nested list
        {Rational(1, 2): x},
    ]
    boundary_sets = [
        set(),
        {x},
        {x, y},
        {x, y, z},
        {Integer(5)},
        {Integer(1), Integer(2), Integer(3)},
    ]
    for d in boundary_dicts:
        check_dict(d)
        if mism:
            break
    if not mism:
        for s in boundary_sets:
            check_set(s)
            if mism:
                break

    # ---- fuzz ----
    if not mism:
        rnd = random.Random(SEED)
        atoms = [x, y, z, Symbol('a'), Symbol('b'),
                 Integer(0), Integer(1), Integer(-2), Integer(7),
                 Rational(1, 3), Rational(-5, 2)]
        for it in range(N_RANDOM):
            if it % 2 == 0:
                n = rnd.randint(0, 5)
                d = {}
                for _ in range(n):
                    k = rnd.choice(atoms)
                    v = rnd.choice(atoms)
                    # occasionally nest a container value
                    if rnd.random() < 0.15:
                        v = {rnd.choice(atoms): rnd.choice(atoms)}
                    d[k] = v
                check_dict(d)
            else:
                n = rnd.randint(0, 5)
                s = set()
                for _ in range(n):
                    s.add(rnd.choice(atoms))
                check_set(s)
            if mism:
                break

    if mism:
        print(f"checked={checked} mismatches={mism}")
        print("status=fail")
        return 1
    print(f"conformance OK ({checked} checks, 0 disagreements)")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
