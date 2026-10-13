#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14017 (nagini).

SHADOW: the impl region of model.py's ``combine``, copied VERBATIM below with
only the contract calls (Requires / Ensures / Exsures) stripped, together with
the ``Combined`` result class and the ``OperandTypeRejected`` exception
(contract calls likewise stripped). There are no @Pure helpers and no
@ContractOnly callees (mapping.md section 3: the axioms and pure regions are
empty), so the shadow is self-contained.

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — ``django.db.models.query_utils.Q._combine``. The gate applies
patch.diff to /testbed before this script runs and sets PYTHONPATH=/testbed,
so the import resolves to the patched module.

TYPE BRIDGE (mapping.md section 2): the model's inputs are the operand's and
container's observable predicates. Each probe builds CONCRETE Django values
and lowers them per the documented bijection:

  * ``other_is_container``       <- isinstance(other, Q)
  * ``other_is_boolean_operand`` <- getattr(other, 'conditional', False) is True
  * ``other_empty``              <- not other
  * ``self_empty``               <- not self
  * ``conn``                     <- opaque int tag {0: Q.AND, 1: Q.OR}

and the outcome comparison is over the observables the model pins:
rejection (TypeError <-> OperandTypeRejected, the user-defined stand-in of
mapping.md section 2) vs. normal return, WHICH acceptance branch produced the
result (branch 0: a fresh copy of the container — same type, children and
negation; branch 1: a fresh value of the operand's own type, with
children/negation equality when the operand is a container; branch 2: a
fresh non-empty container), and — for a branch-2 merge — that the result
carries EXACTLY the requested connector. The identity branches' connectors
are left abstract by the model (Combined docstring), so they are not pinned
here either.

INPUT PLAN (>= 1e5 Requires-satisfying inputs; the precondition demands only
termination, so every lowered probe qualifies): an exhaustive boundary grid
over a catalogue of concrete operands spanning the full realizable observable
space (empty / non-empty / negated / OR-rooted / nested containers; several
distinct boolean-condition non-container operands, i.e. Exists over varied
querysets; non-acceptable operands: plain ints and strings, None, lists,
bare objects, a non-boolean expression, and objects whose conditional flag
is truthy-but-not-True or otherwise off), crossed with container states and
both connectors — plus 100000 fuzz probes drawing random container shapes
(fresh randomly-built children, connectors, negation) and random operands
from the same categories. Pinned fuzz seed: 14017 (recorded in mapping.md).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 14017
N_FUZZ = 100000


# --- shadow: model.py declarations, contract calls stripped -------------------

class OperandTypeRejected(Exception):
    pass


class Combined:
    def __init__(self, branch, connector):
        self.branch = branch
        self.connector = connector


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def combine(other_is_container, other_is_boolean_operand,
            other_empty, self_empty, conn):
    if not (other_is_container or other_is_boolean_operand):
        raise OperandTypeRejected()

    # If the operand is empty, ignore it and just use the container (a copy).
    if other_empty:
        return Combined(0, conn)
    # Or if the container is empty, ignore it and just use the operand (a copy).
    elif self_empty:
        return Combined(1, conn)

    # Both sides non-empty: a fresh container under the requested connector,
    # joining the container and the operand.
    obj = Combined(2, conn)
    return obj
    # (verbatim end)


# --- oracle plumbing -----------------------------------------------------------

def _setup_django():
    """Configure a minimal in-memory Django so model classes import."""
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )
    django.setup()


def _describe(x):
    """Compact printable description of a probe operand/container."""
    try:
        return "%s(%r)" % (type(x).__name__, getattr(x, "children", x))
    except Exception:
        return "%s instance" % type(x).__name__


# --- differential driver -------------------------------------------------------

def check_one(Q, self_q, other, conn_str, conn_tag):
    """Lower one concrete (container, operand, connector) probe to the model's
    observables, run shadow and oracle, and compare the pinned outcome
    observables. Returns an error string on disagreement, else None."""
    # bridge: concrete values -> the model's observable predicates
    other_is_container = isinstance(other, Q)
    other_is_boolean_operand = getattr(other, "conditional", False) is True
    other_empty = not other
    self_empty = not self_q

    desc = ("self=%s (empty=%s), other=%s (container=%s, boolean_operand=%s, "
            "empty=%s), conn=%s"
            % (_describe(self_q), self_empty, _describe(other),
               other_is_container, other_is_boolean_operand, other_empty,
               conn_str))

    # SHADOW
    try:
        shadow = combine(other_is_container, other_is_boolean_operand,
                         other_empty, self_empty, conn_tag)
        s_out = "return branch=%d connector_tag=%d" % (shadow.branch,
                                                       shadow.connector)
    except OperandTypeRejected:
        shadow = None
        s_out = "raise OperandTypeRejected"

    # ORACLE (the real patched Q._combine)
    try:
        result = self_q._combine(other, conn_str)
        r_kind = "ok"
        r_out = "return %s connector=%r" % (_describe(result),
                                            getattr(result, "connector", None))
    except TypeError:
        result = None
        r_kind = "reject"
        r_out = "raise TypeError"
    except Exception as exc:
        return ("DISAGREEMENT (oracle raised unexpectedly) on %s:\n"
                "  shadow = %s\n  real   = raise %r" % (desc, s_out, exc))

    # 1. acceptance decision
    if (shadow is None) != (r_kind == "reject"):
        return ("DISAGREEMENT (acceptance) on %s:\n"
                "  shadow (impl region)        = %s\n"
                "  real (patched Q._combine)   = %s" % (desc, s_out, r_out))
    if shadow is None:
        return None  # both rejected: outcome fully agrees

    # 2. branch observables
    err = None
    if shadow.branch == 0:
        # a fresh copy of the container (connector left abstract: the model's
        # identity branches carry the copied side's own connector, and the
        # copy round-trip normalizes a single-child container's connector)
        if not (type(result) is type(self_q)
                and result is not self_q
                and list(result.children) == list(self_q.children)
                and result.negated == self_q.negated):
            err = "branch 0 (container copy) observables do not hold"
    elif shadow.branch == 1:
        # a fresh value of the operand's own type (connector left abstract)
        if type(result) is not type(other):
            err = "branch 1 (operand copy) result type differs from operand"
        elif isinstance(other, Q) and not (
                result is not other
                and list(result.children) == list(other.children)
                and result.negated == other.negated):
            err = "branch 1 (operand copy) container observables do not hold"
    else:
        # branch 2: fresh container, EXACTLY the requested connector
        if not (isinstance(result, Q)
                and result is not self_q and result is not other
                and result.connector == conn_str
                and bool(result)):
            err = "branch 2 (merge) observables do not hold"
    # 3. connector tag consistency of the shadow itself (bridge sanity)
    if err is None and shadow.connector != conn_tag:
        err = "shadow result does not carry the passed connector tag"
    if err is not None:
        return ("DISAGREEMENT (%s) on %s:\n"
                "  shadow (impl region)        = %s\n"
                "  real (patched Q._combine)   = %s" % (err, desc, s_out, r_out))
    return None


def build_catalogues(Q, Exists, Value, User):
    """Concrete container states and operands spanning the observable space.

    Every entry is a zero-argument factory so each probe gets a fresh value
    (the oracle may embed operands into its result)."""
    selves = [
        ("empty", lambda: Q()),
        ("empty_negated", lambda: Q(_negated=True)),
        ("one_kwarg", lambda: Q(salary__lt=15)),
        ("two_kwargs", lambda: Q(a=1, b=2)),
        ("or_rooted", lambda: Q(Q(a=1), Q(b=2), _connector=Q.OR)),
        ("negated_nonempty", lambda: Q(x=3, _negated=True)),
        ("nested", lambda: Q(Q(a=1, b=2))),
    ]
    others = [
        # same-kind containers
        ("empty_Q", lambda: Q()),
        ("empty_negated_Q", lambda: Q(_negated=True)),
        ("nonempty_Q", lambda: Q(salary__gte=30)),
        ("or_Q", lambda: Q(Q(c=1), Q(d=2), _connector=Q.OR)),
        ("negated_Q", lambda: Q(y=9, _negated=True)),
        ("nested_Q", lambda: Q(Q(e=5))),
        # boolean-condition non-containers (real repo values whose
        # conditional flag is exactly True)
        ("Exists_all", lambda: Exists(User.objects.all())),
        ("Exists_filtered", lambda: Exists(User.objects.filter(pk=1))),
        ("Exists_negated", lambda: Exists(User.objects.all(), negated=True)),
        # neither: must be rejected by shadow and oracle alike
        ("plain_int", lambda: 7),
        ("zero_int", lambda: 0),
        ("string", lambda: "not a filter"),
        ("empty_string", lambda: ""),
        ("none", lambda: None),
        ("list", lambda: [1, 2]),
        ("object", lambda: object()),
        ("Value_int", lambda: Value(1)),
        ("cond_truthy_not_True", lambda: _CondFlag(1)),
        ("cond_false", lambda: _CondFlag(False)),
        ("cond_string", lambda: _CondFlag("True")),
    ]
    return selves, others


class _CondFlag(object):
    """A bare operand advertising an arbitrary conditional flag value —
    exercises that only the exact True flag makes an operand acceptable."""

    def __init__(self, flag):
        self.conditional = flag


def random_container(Q, rng):
    """A fresh randomly-shaped container: random children count, field names,
    values, connector and negation."""
    n = rng.randint(0, 3)
    kwargs = {}
    for _ in range(n):
        kwargs["f%d__gte" % rng.randint(0, 9)] = rng.randint(-5, 5)
    conn = Q.OR if rng.random() < 0.3 else Q.AND
    negated = rng.random() < 0.2
    if n and rng.random() < 0.3:
        return Q(Q(**kwargs), _connector=conn, _negated=negated)
    return Q(_connector=conn, _negated=negated, **kwargs)


def main():
    try:
        _setup_django()
        from django.db.models import Q
        from django.db.models.expressions import Exists, Value
        from django.contrib.auth.models import User
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-CONF ERROR: could not import Django (%r). This check is "
              "meant to run in the evaluation container." % (exc,))
        return 1

    conns = [(Q.AND, 0), (Q.OR, 1)]
    selves, others = build_catalogues(Q, Exists, Value, User)

    checked = 0
    # boundary grid: exhaustive cross of the catalogues and both connectors
    for conn_str, conn_tag in conns:
        for _, build_self in selves:
            for _, build_other in others:
                err = check_one(Q, build_self(), build_other(), conn_str,
                                conn_tag)
                if err:
                    print(err)
                    return 1
                checked += 1
    n_boundary = checked

    # randomized fuzz over the same observable space (pinned seed):
    # random container shapes on both sides, all operand categories
    rng = random.Random(SEED)
    exists_pool = [Exists(User.objects.all()),
                   Exists(User.objects.filter(pk=1)),
                   Exists(User.objects.all(), negated=True)]
    reject_pool = [7, 0, -3, "x", "", None, [], (), object(), 3.5,
                   Value(1), Value("s"),
                   _CondFlag(1), _CondFlag(0), _CondFlag(False),
                   _CondFlag("True"), _CondFlag(None), _CondFlag([True])]
    for _ in range(N_FUZZ):
        conn_str, conn_tag = conns[rng.randint(0, 1)]
        self_q = random_container(Q, rng)
        cat = rng.random()
        if cat < 0.45:
            other = random_container(Q, rng)
        elif cat < 0.65:
            other = rng.choice(exists_pool)
        else:
            other = rng.choice(reject_pool)
        err = check_one(Q, self_q, other, conn_str, conn_tag)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched Q._combine on %d probes "
          "(%d boundary grid + %d fuzz, seed %d); acceptance decision, "
          "branch outcome and merge connector agree; 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
