#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_initRealApps
against the patch.diff behaviour (post-patch `ProjectState.__init__` real_apps
initialization).

The impl region is NOT all-A-tagged (it is pure I/R structure: a constructor-tag
dispatch). The shadow reproduces the post-patch control flow op-for-op:
  * None        -> real_apps = set()                (Except.ok [])
  * a set       -> real_apps = <the set>            (Except.ok elems)
  * any other   -> assert isinstance(...set) FAILS  (Except.error)
We assert zero disagreements vs an independent reconstruction of the patched
code over >= 10^5 fuzzed inputs across the three argument kinds.

Outputs are compared as SETS for the ok case (Python set identity is preserved
by the patch; the Lean model carries the elements as a list compared up to set
equality, per mapping.md).

stdlib-only. exit 0 iff zero disagreements.
"""
import json
import random
import sys

SEED = 14765          # pinned in mapping.md
N = 120_000           # >= 10^5

LABELS = ["a", "b", "c", "contenttypes", "auth", "admin", "", "x", "y", "z"]

# Sentinels for the produced outcome.
OK = "ok"
ERR = "error"


def rand_elems(rng):
    k = rng.randint(0, 5)
    return [rng.choice(LABELS) for _ in range(k)]


def make_arg(rng):
    """Produce a (kind, python_value) pair sampling the three argument kinds."""
    kind = rng.choice(["absent", "set", "set", "nonset", "nonset"])
    if kind == "absent":
        return "absent", None
    elems = rand_elems(rng)
    if kind == "set":
        return "set", set(elems)
    # non-set iterable: list / tuple / frozenset / str-of-labels
    flavor = rng.choice(["list", "tuple", "frozenset"])
    if flavor == "list":
        return "nonset", list(elems)
    if flavor == "tuple":
        return "nonset", tuple(elems)
    return "nonset", frozenset(elems)


def shadow(kind, value):
    """R/I shadow of implementation_initRealApps (Lean impl, constructor-tag
    dispatch). Returns (outcome, elems_as_set)."""
    if kind == "absent":
        return OK, frozenset()
    if kind == "set":
        return OK, frozenset(value)
    # nonset
    return ERR, None


def patched_init(value):
    """Independent reconstruction of the POST-PATCH django code:

        if real_apps is None:
            real_apps = set()
        else:
            assert isinstance(real_apps, set)
        self.real_apps = real_apps

    Returns (outcome, elems_as_set)."""
    real_apps = value
    if real_apps is None:
        real_apps = set()
    else:
        try:
            assert isinstance(real_apps, set)
        except AssertionError:
            return ERR, None
    return OK, frozenset(real_apps)


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    fixed = [
        ("absent", None),
        ("set", set()),
        ("set", {"a"}),
        ("set", {"a", "b", "c"}),
        ("nonset", []),
        ("nonset", ["contenttypes"]),
        ("nonset", ("a", "b")),
        ("nonset", frozenset({"a"})),
    ]
    cases = fixed + [make_arg(rng) for _ in range(N)]

    for kind, value in cases:
        got = shadow(kind, value)
        want = patched_init(value)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((kind, repr(value), got, want))

    if disagreements:
        print(json.dumps({
            "gate": "G-CONF", "status": "fail",
            "disagreements": disagreements, "examples": examples,
        }))
        return 1

    print(json.dumps({
        "gate": "G-CONF", "status": "pass",
        "checked": len(cases), "seed": SEED, "disagreements": 0,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
