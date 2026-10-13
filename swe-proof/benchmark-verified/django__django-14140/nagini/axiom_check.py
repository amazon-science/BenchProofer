#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14140.

There is no consumed ``@ContractOnly`` axiom in this bundle: the decomposition
of a logical filter node into its reconstruction arguments is the CHANGED
behaviour and is modelled DEEPLY in model.py (`deconstruct_arguments`), not
behind an axiom. This script validates that deep model **== the real callee**
(the A-reference): it runs the real ``django.db.models.Q.deconstruct`` on
boundary + randomized inputs and asserts that, for every node, the real method's
``args``/``kwargs`` halves match what model.py specifies, namely:

  (1) the positional ``args`` are EXACTLY the node's children, in order, for
      every node (including a single-child node);
  (2) the keyword ``kwargs`` contain ``_connector`` iff the connector differs
      from the class default, ``_negated`` iff the node is negated, and NO child
      key otherwise.

model.py abstracts a child as an opaque identifier and ``args`` as a list of
those identifiers; here we use the real Python child objects and compare the
``args`` tuple to ``tuple(self.children)`` (the abstraction's concretisation).
The single-child boolean-expression child (an ``Exists``) is the case that the
removed pre-patch special case crashed on / mis-filed; the test below exercises
it directly.

Run in-container with the gold patch applied (G-AX harness). Imports only the
repo's own public ``django.db.models`` symbols (the module under change) plus
the standard library. Exit 0 iff every observation matches model.py.
"""
import os
import random
import sys

# Pin the patched repo at /testbed ahead of the script directory so Python's
# script-dir-first import rule cannot shadow the patched `django/` with an
# unpatched copy that happens to sit next to this file in a non-clean mount
# (which would resurrect the pre-patch TypeError even post-gold). Hardening
# only; in a clean G-AX mount the behaviour is identical.
sys.path.insert(0, "/testbed")

import django
from django.conf import settings

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


# --- model.py reference (the deep model, concretised) ------------------------

def model_args_kwargs(children, connector, default, negated):
    """model.py's `deconstruct_arguments`, concretised onto real children.

      args            == tuple(children)                      (clause 1)
      connector_kwarg == (connector != default)               (clause 2)
      negated_kwarg   == negated                              (clause 2)
    """
    args = tuple(children)
    connector_kwarg = connector != default
    negated_kwarg = negated
    return args, connector_kwarg, negated_kwarg


def check(q):
    """Assert the real Q.deconstruct args/kwargs == the model's prediction."""
    _path, args, kwargs = q.deconstruct()

    expected_args, expected_conn_kw, expected_neg_kw = model_args_kwargs(
        list(q.children), q.connector, q.default, q.negated)

    assert args == expected_args, (
        "args mismatch on %r: real deconstruct gave %r, model predicts %r"
        % (q, args, expected_args))

    # No child ever appears as a keyword argument; the only permitted keys are
    # the two state markers.
    assert set(kwargs).issubset({"_connector", "_negated"}), (
        "unexpected kwargs keys on %r: %r" % (q, kwargs))
    assert ("_connector" in kwargs) == expected_conn_kw, (
        "_connector presence mismatch on %r: kwargs=%r, model predicts %r"
        % (q, kwargs, expected_conn_kw))
    if "_connector" in kwargs:
        assert kwargs["_connector"] == q.connector
    assert ("_negated" in kwargs) == expected_neg_kw, (
        "_negated presence mismatch on %r: kwargs=%r, model predicts %r"
        % (q, kwargs, expected_neg_kw))
    if "_negated" in kwargs:
        assert kwargs["_negated"] is True


def round_trip(q):
    """The deconstruction must rebuild an equal node (reconstruction is the
    consumer of `deconstruct`)."""
    path, args, kwargs = q.deconstruct()
    rebuilt = Q(*args, **kwargs)
    assert rebuilt == q, "round trip broke for %r: rebuilt %r" % (q, rebuilt)


def main():
    is_poc = Exists(Q())  # any conditional expression child (non-subscriptable)

    boundary = [
        Q(),                                   # no children
        Q(x=1),                                # single kwarg child -> ('x', 1)
        Q(("x", 1)),                           # single tuple child (positional)
        Q(x=1, y=2),                           # two children
        Q(x=1) & Q(y=2),                       # combined (nested children)
        Q(x=1) | Q(y=2),                       # non-default connector
        ~Q(x=1),                               # negated single child
        ~Q(x=1, y=2),                          # negated multi child
        ~(Q(x=1) | Q(y=2)),                    # negated, non-default connector
        Q(price__gt=F("discounted_price")),    # the test_deconstruct case
        ~Q(price__gt=F("discounted_price")),   # the test_deconstruct_negated case
        Q(is_poc),                             # single non-subscriptable child
        ~Q(is_poc),                            # negated single expression child
        Q(is_poc, x=1),                        # expression + kwarg -> two children
        Q(is_poc) & Q(),                       # boolean expr combined w/ empty Q
        Q() & Q(is_poc),
        Q(is_poc) | Q(),
        Q() | Q(is_poc),
    ]
    for q in boundary:
        check(q)
        round_trip(q)

    # --- randomized fuzz over node shapes ------------------------------------
    rng = random.Random(14140)
    for _ in range(5000):
        nkw = rng.randint(0, 3)
        kw = {("k%d" % i): rng.randint(0, 9) for i in range(nkw)}
        npos = rng.randint(0, 2)
        pos = [(("p%d" % i), rng.randint(0, 9)) for i in range(npos)]
        # sometimes inject a non-subscriptable conditional-expression child
        if rng.random() < 0.4:
            pos.append(Exists(Q()))
        q = Q(*pos, **kw)
        if rng.random() < 0.5 and len(q.children) >= 2:
            q.connector = Q.OR
        if rng.random() < 0.5:
            q.negated = True
        check(q)

    print("G-AX OK: deconstruct_arguments deep model (== real Q.deconstruct) "
          "sound on %d boundary + 5000 fuzz nodes; args == children, kwargs ⊆ "
          "{_connector,_negated} with exact presence." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
