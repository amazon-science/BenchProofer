#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14140 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`deconstructNode`, routed through the deep model `deconstructed`)
              transliterated to Python over the real repo types. There are NO
              A-tagged callees in the impl region (no axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Q.deconstruct()` invoked at
              base_commit (the real correctness oracle; G-RESOLVE applies the
              gold patch before this runs).

Observable of a decomposition, per the mapping.md §2 bijection:
  - the positional children carried back, IN ORDER and BY IDENTITY
        ↔  the `Decon.args : List Child` payload;
  - whether a lone child was instead recorded as a keyword pair
        ↔  `Decon.pairKw : Option (String × Int)`  (the desired behaviour: never);
  - the recorded combinator, present only when non-default
        ↔  `Decon.connKw : Option Connector`  (kwargs['_connector']);
  - whether negation is recorded
        ↔  `Decon.negKw : Bool`  (kwargs['_negated']);
  - decomposition always succeeds (`Except.ok`) — never raises.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 14140
N_FUZZ = 100_000

# Configure minimal settings so importing the ORM filter machinery is safe.
# Constructing a `Q(...)` and calling `.deconstruct()` touches neither the
# database nor the populated app registry, so `django.setup()` is deliberately
# avoided (mirrors the §4.1 minimal-import discipline).
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
    )

from django.db.models import Q  # patched: deconstruct places every child in args


# --- A lightweight stand-in for an embedded boolean expression child ---------
# The patched `deconstruct` performs NO type inspection of children
# (`args = tuple(self.children)`), so any non-tuple, non-Q object faithfully
# exercises the "embedded boolean expression" child shape. Mirrors the real
# `conditional = True` marker carried by `Exists`/`Q` expressions.
class BoolExpr:
    conditional = True

    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return "BoolExpr(%r)" % (self.tag,)


# --- the R/I shadow: Solution.lean deconstructed/deconstructNode -------------
# `Connector`: conj <-> 'AND' (the default); disj <-> 'OR' (the only non-default).
DEFAULT_CONNECTOR = "AND"


def shadow_deconstruct(children, connector, negated):
    """deconstructed (pure region) transliterated. Returns the observable
    (status, args_identities, pairKw, connKw, negKw)."""
    args = list(children)                                   # placed positionally
    pair_kw = None                                          # never, in the spec
    conn_kw = connector if connector != DEFAULT_CONNECTOR else None
    neg_kw = bool(negated)
    return ("ok", [id(c) for c in args], pair_kw, conn_kw, neg_kw)


def oracle_deconstruct(children, connector, negated):
    """patch.diff's behaviour: build the real Q and observe its deconstruction.
    A construction-time `_connector` is recorded by Q's __init__; deconstruct
    surfaces it (and _negated) in kwargs when present."""
    # Build the node with the chosen children, connector, and negation. Passing
    # children positionally yields `self.children == list(children)` in order
    # (Q sorts only the keyword items, of which there are none here).
    conn_arg = None if connector == DEFAULT_CONNECTOR else connector
    try:
        q = Q(*children, _connector=conn_arg, _negated=negated)
        _path, args, kwargs = q.deconstruct()
    except Exception as exc:                                # pragma: no cover
        return ("error", type(exc).__name__, None, None, None)
    # Identity-and-order check: the carried-back args must be exactly the input
    # children objects in order (this is the heart of the desired behaviour).
    args_identities = [id(a) for a in args]
    # Any leftover kwargs beyond the recognised _connector/_negated would be a
    # stray keyword recording (the removed special case) -> surface as pairKw.
    extra = {k: v for k, v in kwargs.items() if k not in ("_connector", "_negated")}
    pair_kw = extra if extra else None
    conn_kw = kwargs.get("_connector")
    neg_kw = kwargs.get("_negated", False)
    return ("ok", args_identities, pair_kw, conn_kw, bool(neg_kw))


def make_children(kinds):
    """Materialise a list of child objects from kind tags."""
    objs = []
    for i, k in enumerate(kinds):
        if k == "pair":
            objs.append(("k%d" % i, i))         # a length-2 key/value pair
        elif k == "node":
            objs.append(Q(**{"z%d" % i: i}))     # a non-empty nested filter node
        else:  # "expr"
            objs.append(BoolExpr(i))             # an embedded boolean expression
    return objs


def fuzz_cases(n, rng):
    kinds = ("pair", "node", "expr")
    connectors = ("AND", "OR")
    # boundary: every single-child shape, under both connectors and negations;
    # plus the empty node (no children).
    yield ([], "AND", False)
    yield ([], "OR", False)
    yield ([], "AND", True)
    for k in kinds:
        for conn in connectors:
            for neg in (False, True):
                yield ([k], conn, neg)
    # a couple of fixed mixed shapes
    yield (["pair", "pair"], "AND", False)
    yield (["pair", "node", "expr"], "OR", True)
    yield (["expr", "expr"], "AND", False)
    # randomized
    for _ in range(n):
        m = rng.randint(0, 5)
        ks = [rng.choice(kinds) for _ in range(m)]
        conn = rng.choice(connectors)
        neg = rng.random() < 0.5
        yield (ks, conn, neg)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for kinds, conn, neg in fuzz_cases(N_FUZZ, rng):
        count += 1
        children = make_children(kinds)
        shadow = shadow_deconstruct(children, conn, neg)
        oracle = oracle_deconstruct(children, conn, neg)
        if shadow != oracle:
            disagreements.append((kinds, conn, neg, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kinds, conn, neg, sh, orc in disagreements:
            print("  kinds=%r conn=%r neg=%r shadow=%r oracle=%r"
                  % (kinds, conn, neg, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of deconstructNode agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
