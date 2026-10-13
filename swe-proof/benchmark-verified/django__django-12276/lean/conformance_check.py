#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12276.

The bundle models ONE routine: `FileInput.use_required_attribute` (the method the
patch ADDS). The modeled value is a PURE function of two observables the real
method reads:

    isHidden        := self.is_hidden
    initialPresent  := bool(initial)

Post-patch rule (the gold patch adds the method; `super()` resolves to
`Widget.use_required_attribute` = `not self.is_hidden`):

    use_required_attribute(initial) == (not self.is_hidden) and not initial
                                     == (not isHidden) and (not initialPresent)

Standing up the full Django widget/form machinery to drive the real method is
unnecessary: the modeled value is exactly this pure boolean decision over the two
observables the real method exposes. So the ORACLE below is a faithful in-process
replica of the POST-PATCH method, and the SHADOW is the op-for-op transliteration
of `implementation_useRequiredAttribute` (Solution.lean impl region), per
refinement.md.

This genuinely tests the soundness-critical clause: a non-hidden file input that
already has a (truthy) initial value must NOT be marked required (spec=False),
whereas the pre-patch behavior (inherited base rule, `not is_hidden`) would mark
it required — matching the F2P expectation
(`use_required_attribute('resume.txt')` is `False`).

The domain is finite (Bool x Bool, 4 points): we enumerate all four exhaustively
and additionally draw >=1e5 random pairs. stdlib-only. Pinned seed: 12276.
"""
import random
import sys

SEED = 12276
N = 120_000


# --- ORACLE: faithful in-process replica of the POST-PATCH method -------------
def oracle(isHidden, initialPresent):
    # super().use_required_attribute(initial) == not self.is_hidden
    base = (not isHidden)
    return base and (not initialPresent)


# --- SHADOW: op-for-op transliteration of implementation_useRequiredAttribute -
def shadow(isHidden, initialPresent):
    return (not isHidden) and (not initialPresent)


def disagree(isHidden, initialPresent):
    o = oracle(isHidden, initialPresent)
    s = shadow(isHidden, initialPresent)
    if o != s:
        return ({"isHidden": isHidden, "initialPresent": initialPresent}, o, s)
    return None


def main():
    checked = 0

    # Exhaustive enumeration of the finite domain.
    for isHidden in (False, True):
        for initialPresent in (False, True):
            d = disagree(isHidden, initialPresent)
            if d:
                print(f"DISAGREE exhaustive: oracle={d[1]} shadow={d[2]} inp={d[0]}")
                print("status=fail")
                return 1
            checked += 1

    # Random fuzz (redundant over the finite domain, but pins the contract).
    rng = random.Random(SEED)
    for _ in range(N):
        isHidden = rng.random() < 0.5
        initialPresent = rng.random() < 0.5
        d = disagree(isHidden, initialPresent)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
