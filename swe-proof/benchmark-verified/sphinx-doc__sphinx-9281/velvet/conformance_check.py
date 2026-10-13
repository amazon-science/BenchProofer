#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9281 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`objectDescription`,
              routed through the deep model `describe`) transliterated to Python
              over the real repo types. There are NO A-tagged callees in the
              impl region (no axioms), so the shadow is pure R/I.

              `describe` distinguishes exactly two cases (mapping.md §2):
                - a member of an enumerated type renders as `type.member`
                  (`className ++ "." ++ memberName`)  — the CHANGED branch;
                - any other value renders with the generic textual description
                  the UNCHANGED renderer already produced (the `genericText`
                  field of the model). The unchanged generic renderer
                  (containers + the repr/strip/newline fallback) is reproduced
                  here so the `plain` leg is an independent computation, not an
                  echo of the oracle.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `sphinx.util.inspect.object_description` applied at base_commit
              (the real correctness oracle, G-RESOLVE applies the gold patch
              before this runs).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import enum
import random
import re
import sys

SEED = 9281
N_FUZZ = 100_000

# --- the R/I shadow: Solution.lean describe/objectDescription, transliterated -
# The unchanged generic renderer is reproduced (containers + the repr/strip/
# newline fallback) so that the `plain` leg is computed independently rather
# than echoed from the oracle. The CHANGED branch is the `enum.Enum` case.
_MEM_ADDR_RE = re.compile(r' at 0x[0-9a-f]{8,16}(?=>)', re.IGNORECASE)


def shadow_describe(obj):
    """Faithful transliteration of `describe`, with the unchanged generic
    renderer reproduced for the `plain` case (mapping.md §2, §3.1)."""
    # --- unchanged container legs (carried in `genericText`; recurse) --------
    if isinstance(obj, dict):
        try:
            sorted_keys = sorted(obj)
        except Exception:
            pass
        else:
            items = ("%s: %s" % (shadow_describe(k), shadow_describe(obj[k]))
                     for k in sorted_keys)
            return "{%s}" % ", ".join(items)
    if isinstance(obj, set):
        try:
            sorted_values = sorted(obj)
        except TypeError:
            pass
        else:
            return "{%s}" % ", ".join(shadow_describe(x) for x in sorted_values)
    if isinstance(obj, frozenset):
        try:
            sorted_values = sorted(obj)
        except TypeError:
            pass
        else:
            return "frozenset({%s})" % ", ".join(shadow_describe(x)
                                                 for x in sorted_values)
    # --- the CHANGED branch: a member of an enumerated type -> type.member ---
    if isinstance(obj, enum.Enum):
        return "%s.%s" % (obj.__class__.__name__, obj.name)
    # --- unchanged generic fallback (carried in `genericText`) ---------------
    try:
        s = repr(obj)
    except Exception as exc:
        raise ValueError from exc
    s = _MEM_ADDR_RE.sub('', s)
    return s.replace('\n', ' ')


def oracle_describe(obj):
    """patch.diff's behaviour: the patched object_description at base_commit."""
    from sphinx.util.inspect import object_description
    return object_description(obj)


# --- enum classes for the fuzz pool (the CHANGED branch's discriminator) -----
class ColorEnum(enum.Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class UglyEnum(enum.Enum):
    ValueA = 10
    ValueB = 20


class IntFlavor(enum.IntEnum):
    LOW = 0
    HIGH = 100


class StrName(enum.Enum):
    a = "x"
    b_long_name = "y"


_ENUM_MEMBERS = (list(ColorEnum) + list(UglyEnum) + list(IntFlavor)
                 + list(StrName))


class _Plain:
    """A custom object whose repr carries a memory address (stripped by the
    unchanged fallback) — exercises the repr/strip/newline leg."""


def _scalar(rng):
    kind = rng.randint(0, 7)
    if kind == 0:
        return rng.randint(-1000, 1000)
    if kind == 1:
        return rng.choice([True, False])
    if kind == 2:
        return None
    if kind == 3:
        return rng.choice(["", "abc", "Joe's", "a\nb", "x=1&y=2", "café"])
    if kind == 4:
        return round(rng.uniform(-100, 100), 3)
    if kind == 5:
        return rng.choice(_ENUM_MEMBERS)           # bare enum member
    if kind == 6:
        return _Plain()                            # custom object (repr+strip)
    return rng.choice(["alpha", "beta", "gamma", 0, 1, -1])


def _value(rng, depth):
    if depth <= 0:
        return _scalar(rng)
    kind = rng.randint(0, 6)
    if kind == 0:
        return _scalar(rng)
    if kind == 1:
        return [_value(rng, depth - 1) for _ in range(rng.randint(0, 4))]
    if kind == 2:
        return tuple(_value(rng, depth - 1) for _ in range(rng.randint(0, 4)))
    if kind == 3:
        # dict with scalar keys (sortable-or-not; both legs reproduced)
        keys = [_scalar(rng) for _ in range(rng.randint(0, 4))]
        return {k: _value(rng, depth - 1) for k in keys}
    if kind == 4:
        try:
            return set(_scalar(rng) for _ in range(rng.randint(0, 4)))
        except TypeError:
            return _scalar(rng)
    if kind == 5:
        try:
            return frozenset(_scalar(rng) for _ in range(rng.randint(0, 4)))
        except TypeError:
            return _scalar(rng)
    return _scalar(rng)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): each enum member alone
    for m in _ENUM_MEMBERS:
        yield m
    # the issue's own minimal example
    yield UglyEnum.ValueA
    yield UglyEnum.ValueB
    # scalars and container boundaries
    yield None
    yield ""
    yield 0
    yield []
    yield {}
    yield set()
    yield frozenset()
    yield [ColorEnum.RED, ColorEnum.GREEN]            # enums nested in a list
    yield {"k": UglyEnum.ValueA}                      # enum nested in a dict
    yield {IntFlavor.LOW, IntFlavor.HIGH}             # sortable enum set
    yield _Plain()
    # randomized fuzz
    for _ in range(n):
        yield _value(rng, rng.randint(0, 3))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for obj in fuzz_inputs(N_FUZZ, rng):
        count += 1
        try:
            shadow = shadow_describe(obj)
        except Exception as e:
            shadow = ("SHADOW-RAISED", type(e).__name__)
        try:
            oracle = oracle_describe(obj)
        except Exception as e:
            oracle = ("ORACLE-RAISED", type(e).__name__)
        if shadow != oracle:
            disagreements.append((repr(obj)[:80], shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for o, sh, orc in disagreements:
            print("  input=%s shadow=%r oracle=%r" % (o, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of objectDescription agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
