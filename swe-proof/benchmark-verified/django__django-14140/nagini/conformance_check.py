#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14140 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert and the loop Invariants) stripped.
The `Node` / `Deconstruction` carrier classes copy over as plain Python
classes (their bodies are the plain field assignments; the contracts were
spec-side only). There are no @Pure helpers and no @ContractOnly callees in
this bundle, and no PSeq/ToSeq use survives outside the stripped contracts,
so no sequence shim is needed.

ORACLE: the REAL repo method the model models per mapping.md section 1 —
``django.db.models.Q.deconstruct`` — imported from /testbed with the gate
having already applied patch.diff. Only the args/kwargs halves of the
returned triple are compared (the path element is outside the modeled
behaviour, mapping.md section 1).

Type bridge (mapping.md section 2):
  * a real child object <-> an opaque int identifier: the k-th child of a
    node is identifier k; the real ``args`` tuple is lifted back to a list of
    identifiers by matching each element against the node's children in
    order (identity first, equality fallback) — order and multiplicity
    preserved, so the lift is the inverse of the abstraction exactly when
    the real args are the children verbatim;
  * the string connector codes <-> int codes: the only operation performed
    is the (in)equality with the class default, so the bridge maps the
    default code to 0 and any other connector value to 1;
  * the returned ``kwargs`` dict <-> two booleans: ``'_connector' in kwargs``
    <-> ``connector_kwarg`` and ``'_negated' in kwargs`` <-> ``negated_kwarg``.
    Any other key in the real kwargs is outside the bridge's image (a child
    relocated into kwargs) and is reported as a disagreement.

Input domain: the model's preconditions only demand readable fields, so every
real node shape lowers to a Requires-satisfying input. Generation covers the
boundary shapes (no children; a single keyword child; a single positional
tuple child; a single non-subscriptable conditional-expression child; nested
combinations with an empty node on either side; multi-child; non-default
connector; negation; the fixture shapes from the instance's tests) plus
100000 randomized node shapes. Pinned fuzz seed: 141400.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

# Pin the patched repo at /testbed ahead of the script directory so the
# script-dir-first import rule cannot shadow the patched ``django/`` with a
# stray copy sitting next to this file in a non-clean mount. Hardening only.
sys.path.insert(0, "/testbed")

SEED = 141400
N_FUZZ = 100000

import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
    )
    django.setup()

from django.db.models import Exists, F, Q  # noqa: E402


# --- carrier classes from model.py, contracts stripped ------------------------

class Node(object):
    """A logical filter node, holding only the state the modeled routine
    observes (contract-stripped copy of model.py's Node)."""

    def __init__(self, children, connector, default, negated):
        self.children = children
        self.connector = connector
        self.default = default
        self.negated = negated


class Deconstruction(object):
    """The argument halves of the reconstruction triple (contract-stripped
    copy of model.py's Deconstruction)."""

    def __init__(self, args, connector_kwarg, negated_kwarg):
        self.args = args
        self.connector_kwarg = connector_kwarg
        self.negated_kwarg = negated_kwarg


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def deconstruct_arguments(node):
    # Every child becomes a positional argument (a faithful copy of the
    # children sequence), regardless of how many children there are.
    args = []  # type: list
    i = 0
    n = len(node.children)
    while i < n:
        args = args + [node.children[i]]
        i = i + 1
    # The keyword arguments carry only the connector (when non-default) and the
    # negation flag; never a child.
    connector_kwarg = node.connector != node.default
    negated_kwarg = node.negated
    result = Deconstruction(args, connector_kwarg, negated_kwarg)
    return result
    # (the stripped Invariant/Assert lines carried only proof-side facts)


# --- bridge + differential driver ----------------------------------------------

def lift_args_to_ids(real_args, children):
    """Lift the real args tuple back to identifiers: match each element to a
    not-yet-used child position, identity first then equality. Returns a list
    of indices, or None if some element matches no remaining child (i.e. the
    real args are not a sub-multiset of the children — automatically a
    disagreement with the shadow, whose args are always child identifiers)."""
    used = [False] * len(children)
    ids = []
    for a in real_args:
        hit = None
        for j, c in enumerate(children):
            if not used[j] and c is a:
                hit = j
                break
        if hit is None:
            for j, c in enumerate(children):
                if used[j]:
                    continue
                try:
                    if c == a:
                        hit = j
                        break
                except Exception:
                    pass
        if hit is None:
            return None
        used[hit] = True
        ids.append(hit)
    return ids


def check(q):
    """Run shadow and oracle on one node; return an error string on
    disagreement, else None."""
    _path, real_args, real_kwargs = q.deconstruct()

    children = list(q.children)
    # abstraction: k-th child -> identifier k; connector codes -> {0,1} with
    # the default mapped to 0 (only the (in)equality with the default is used)
    node = Node(list(range(len(children))),
                0 if q.connector == q.default else 1,
                0,
                bool(q.negated))
    shadow = deconstruct_arguments(node)

    real_ids = lift_args_to_ids(real_args, children)
    if real_ids is None or shadow.args != real_ids:
        return ("DISAGREEMENT (positional args) on %r:\n"
                "  shadow (impl region) args ids = %r\n"
                "  real deconstruct args = %r (lifted ids = %r)\n"
                "  children = %r" % (q, shadow.args, real_args, real_ids,
                                     children))

    extra_keys = set(real_kwargs) - {"_connector", "_negated"}
    if extra_keys:
        return ("DISAGREEMENT (kwargs carry a non-marker key) on %r:\n"
                "  shadow kwargs flags = (connector=%r, negated=%r)\n"
                "  real kwargs = %r" % (q, shadow.connector_kwarg,
                                        shadow.negated_kwarg, real_kwargs))
    if ("_connector" in real_kwargs) != shadow.connector_kwarg:
        return ("DISAGREEMENT (connector marker) on %r:\n"
                "  shadow connector_kwarg = %r\n"
                "  real kwargs = %r" % (q, shadow.connector_kwarg,
                                        real_kwargs))
    if ("_negated" in real_kwargs) != shadow.negated_kwarg:
        return ("DISAGREEMENT (negation marker) on %r:\n"
                "  shadow negated_kwarg = %r\n"
                "  real kwargs = %r" % (q, shadow.negated_kwarg, real_kwargs))
    return None


def boundary_cases():
    expr = Exists(Q())  # a non-subscriptable conditional-expression child
    return [
        Q(),                                   # no children
        Q(x=1),                                # single keyword child
        Q(("x", 1)),                           # single positional tuple child
        Q(x=1, y=2),                           # two children
        Q(x=1) & Q(y=2),                       # combined (nested children)
        Q(x=1) | Q(y=2),                       # non-default connector
        ~Q(x=1),                               # negated single child
        ~Q(x=1, y=2),                          # negated multi child
        ~(Q(x=1) | Q(y=2)),                    # negated, non-default connector
        Q(price__gt=F("discounted_price")),    # test fixture shape
        ~Q(price__gt=F("discounted_price")),   # negated fixture shape
        Q(expr),                               # single expression child
        ~Q(expr),                              # negated single expression child
        Q(expr, x=1),                          # expression + keyword child
        Q(expr) & Q(),                         # combined with an empty node
        Q() & Q(expr),
        Q(expr) | Q(),
        Q() | Q(expr),
    ]


def main():
    checked = 0

    boundary = boundary_cases()
    for q in boundary:
        err = check(q)
        if err:
            print(err)
            return 1
        checked += 1

    # randomized fuzz over node shapes (pinned seed)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        nkw = rng.randint(0, 3)
        kw = {("k%d" % i): rng.randint(0, 9) for i in range(nkw)}
        npos = rng.randint(0, 2)
        pos = [(("p%d" % i), rng.randint(0, 9)) for i in range(npos)]
        # sometimes inject a non-subscriptable conditional-expression child
        if rng.random() < 0.3:
            pos.append(Exists(Q()))
        q = Q(*pos, **kw)
        r = rng.random()
        if r < 0.15:
            q = q & Q(z=rng.randint(0, 9))
        elif r < 0.3:
            q = q | Q(z=rng.randint(0, 9))
        if rng.random() < 0.5 and len(q.children) >= 2:
            q.connector = Q.OR
        if rng.random() < 0.5:
            q.negated = True
        err = check(q)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real deconstruct args/kwargs halves on "
          "%d inputs (%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
