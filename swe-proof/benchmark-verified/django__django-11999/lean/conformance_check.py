#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_registerDisplay
against the patch.diff behaviour (post-patch display-accessor registration).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op over the modeled attribute namespace (a dict
key->value): when the field has a choice set, install the generated accessor only
if the key is absent. We diff that against an independent reconstruction of the
post-patch registration logic operating on a real Python class' attribute
namespace via `hasattr`/`setattr` (the exact primitives the patched code uses).
Zero disagreements required over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 11999          # pinned in mapping.md
N = 130_000           # >= 10^5

# Field-name alphabet; oversample short names so collisions on the generated
# accessor key happen often.
NAME_ALPHABET = list("abcfoo_bar123")


def display_key(name: str) -> str:
    """'get_%s_display' % name."""
    return "get_%s_display" % name


def shadow(attrs: dict, name: str, has_choices: bool, display: int) -> dict:
    """R/I shadow of implementation_registerDisplay over the dict namespace."""
    result = dict(attrs)
    if has_choices:
        key = display_key(name)
        if key not in result:          # `not hasKey result key`
            result[key] = display       # `setKey`
    return result


def patched_register(attrs: dict, name: str, has_choices: bool, display: int) -> dict:
    """Independent reconstruction of the post-patch registration, using a real
    Python object's attribute namespace and the actual hasattr/setattr calls
    the patched code performs."""
    class _Cls:
        pass
    cls = _Cls()
    for k, v in attrs.items():
        setattr(cls, k, v)
    if has_choices:
        key = display_key(name)
        # the patched line: only set when the attribute is not already present
        if not hasattr(cls, key):
            setattr(cls, key, display)
    # read back the induced mapping over the union of observed keys
    out = dict(attrs)
    key = display_key(name)
    if hasattr(cls, key):
        out[key] = getattr(cls, key)
    return out


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    def rand_name() -> str:
        return "".join(rng.choice(NAME_ALPHABET) for _ in range(rng.randint(1, 5)))

    def rand_attrs(name: str) -> dict:
        d = {}
        for _ in range(rng.randint(0, 4)):
            d[rand_name() + ("_x" if rng.random() < 0.3 else "")] = rng.randint(-50, 50)
        # with probability, pre-seed the generated accessor key (the override case)
        if rng.random() < 0.5:
            d[display_key(name)] = rng.randint(-50, 50)
        return d

    # Deterministic boundary cases first, incl. the exact F2P shape.
    fixed = [
        ({"get_foo_bar_display": 7}, "foo_bar", True, 99),   # override preserved
        ({}, "foo_bar", True, 99),                            # accessor installed
        ({"other": 1}, "foo_bar", True, 99),                  # installed alongside
        ({"get_foo_bar_display": 7}, "foo_bar", False, 99),   # no choices: untouched
        ({}, "x", False, 5),                                  # no choices, empty
        ({"get_x_display": 3}, "x", True, 5),                 # override, short name
    ]
    cases = list(fixed)
    for _ in range(N):
        name = rand_name()
        cases.append((rand_attrs(name), name, rng.random() < 0.5, rng.randint(-50, 50)))

    for attrs, name, has_choices, display in cases:
        got = shadow(attrs, name, has_choices, display)
        want = patched_register(attrs, name, has_choices, display)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((attrs, name, has_choices, display), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
