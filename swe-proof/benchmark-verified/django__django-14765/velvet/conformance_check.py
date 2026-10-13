#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-14765 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of `refinement.md`: the deep
argument-normalization model of `Solution.lean` (`normalizeSpec` — an absent
argument stores the empty collection; an argument that is already a set is stored
as-is; an argument that is not a set is REJECTED rather than silently coerced)
transliterated to Python, differential-tested against `patch.diff`'s behaviour
driven through the REAL gold-patched `ProjectState.__init__` at base_commit+gold.

ORACLE — the gold-patched `ProjectState.__init__` itself. We construct a
`ProjectState(real_apps=<arg>)` and observe the pair
  (raised AssertionError?, stored `real_apps` value when accepted).
The patch's whole content is that a `real_apps` argument which is non-None and
not already a `set` now triggers `assert isinstance(real_apps, set)` (raising
AssertionError) instead of being silently wrapped with `set(real_apps)`.

SHADOW — `Solution.lean`'s `normalizeSpec`, transliterated. It classifies the
argument by running the SAME unchanged primitive tests the construction performs
(`real_apps is None` and `isinstance(real_apps, set)` — run live, NOT an axiom
model):
  * None / omitted                 -> absent        -> ok, stored == set()
  * already a set                  -> alreadySet xs -> ok, stored == that set
  * non-None and not a set         -> coercible ys  -> rejected (AssertionError)

For each argument we compare the pair (raised?, normalized stored value) between
ORACLE and SHADOW. Exit 0 iff zero disagreements over the boundary arguments plus
the fuzz budget (seed pinned, mapping.md §4).

stdlib + Django only; no network, no database access (only ProjectState.__init__
runs — it touches neither). The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

# Minimal settings so importing django.db.migrations.state is safe.
# ProjectState.__init__ touches neither the database nor the app registry, so
# `django.setup()` is deliberately avoided.
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=[],
        USE_I18N=False,
    )

from django.db.migrations.state import ProjectState

SEED = 14765
FUZZ = 120000  # > 1e5 fuzzed arguments (plan §4.1)

# A sentinel meaning "argument omitted entirely" (real_apps defaults to None).
OMIT = object()


# ---- SHADOW: Solution.lean normalizeSpec, transliterated --------------------
def classify(arg):
    """Run the UNCHANGED primitive tests and bucket the argument into the three
    SetArg shapes (mapping.md §2). `None`/omitted -> absent; an actual set ->
    alreadySet; anything else non-None -> coercible."""
    if arg is OMIT or arg is None:
        return ("absent", None)
    if isinstance(arg, set):
        return ("alreadySet", arg)
    return ("coercible", arg)


def shadow_observe(arg):
    """normalizeSpec(a): the outcome the model assigns.
    Returns (raised, stored) where `stored` is the stored set on acceptance
    (normalized to a Python set) or None on rejection."""
    kind, payload = classify(arg)
    if kind == "absent":
        return (False, set())                 # Except.ok []  -> stored empty set
    if kind == "alreadySet":
        return (False, set(payload))          # Except.ok xs  -> stored the set as-is
    return (True, None)                       # Except.error .rejected -> AssertionError


# ---- ORACLE: the real gold-patched ProjectState.__init__ --------------------
def oracle_observe(arg):
    """Construct a real ProjectState and observe acceptance/rejection + the
    stored real_apps. Returns (raised, stored)."""
    try:
        if arg is OMIT:
            ps = ProjectState()
        else:
            ps = ProjectState(real_apps=arg)
    except AssertionError:
        return (True, None)
    return (False, set(ps.real_apps))


# ---- argument corpus --------------------------------------------------------
def boundary_args():
    """The arguments the F2P/P2P matrix and issue exercise, plus boundaries."""
    return [
        OMIT,                                   # omitted -> default empty set
        None,                                   # explicit None -> empty set
        set(),                                  # empty set -> kept (empty)
        {"contenttypes"},                       # set -> kept
        {"a", "b", "c"},                        # multi-element set
        frozenset({"x"}),                       # frozenset is NOT a set -> reject (the bug class)
        ["contenttypes"],                       # the F2P test: list -> AssertionError
        [],                                     # empty list -> non-set -> reject
        ("a", "b"),                             # tuple -> reject
        (),                                     # empty tuple -> reject
        "contenttypes",                         # str is iterable, non-set -> reject
        "",                                     # empty str -> reject
        {"k": 1},                               # dict -> reject
        iter(["a"]),                            # iterator -> reject
        0, 1, 3.14,                             # non-iterable scalars -> reject
        True,                                   # bool -> reject
        object(),                               # unrelated object -> reject
    ]


def fuzz_args(rng):
    for _ in range(FUZZ):
        roll = rng.random()
        if roll < 0.10:
            yield OMIT
        elif roll < 0.20:
            yield None
        elif roll < 0.45:
            # a real set of random small strings (the accepting branch)
            k = rng.randint(0, 6)
            yield {("".join(rng.choice("abcde") for _ in range(rng.randint(0, 4))))
                   for _ in range(k)}
        elif roll < 0.65:
            # a list (the canonical reject case)
            k = rng.randint(0, 6)
            yield [("".join(rng.choice("abcde") for _ in range(rng.randint(0, 4))))
                   for _ in range(k)]
        elif roll < 0.78:
            yield tuple("".join(rng.choice("abcde") for _ in range(rng.randint(0, 4)))
                        for _ in range(rng.randint(0, 5)))
        elif roll < 0.86:
            yield frozenset({"".join(rng.choice("abcde") for _ in range(2))})
        elif roll < 0.92:
            yield "".join(rng.choice("abcde ") for _ in range(rng.randint(0, 8)))
        elif roll < 0.97:
            yield rng.choice([0, 1, -1, 2, 3.5, -2.0, True, False])
        else:
            yield rng.choice([{}, {"k": 1}, object(), b"abc"])


def _key(arg):
    """A safe printable key for an argument that may be unhashable/consumable."""
    try:
        return ascii(arg)
    except Exception:                                          # noqa: BLE001
        return "<unprintable>"


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    def check(arg):
        nonlocal count
        count += 1
        # iterators are single-use: materialize a fresh copy per observer
        oracle = oracle_observe(arg)
        shadow = shadow_observe(arg)
        if oracle[0] != shadow[0]:
            disagreements.append(("RAISED", _key(arg), shadow, oracle))
        elif not oracle[0] and oracle[1] != shadow[1]:
            disagreements.append(("STORED", _key(arg), shadow, oracle))

    for arg in boundary_args():
        check(arg)
        if len(disagreements) >= 8:
            break

    if not disagreements:
        for arg in fuzz_args(rng):
            check(arg)
            if len(disagreements) >= 8:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for tag, arg, sh, orc in disagreements:
            print("  [%s] arg=%s shadow=%s oracle=%s" % (tag, arg, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of normalizeSetArg (absent->empty, set->kept, "
          "non-set->rejected) agrees with patch.diff behaviour through the real "
          "ProjectState.__init__ on %d arguments (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
