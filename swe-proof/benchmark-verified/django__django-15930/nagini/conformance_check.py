#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15930 (nagini).

SHADOW: the impl region of model.py `render_branch`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. The impl
region operates on plain Python lists plus the @Pure helpers (lead/sep/
true_predicate/true_params, and clause_text/clause_params used as an internal
cross-check), which copy over as plain functions on top of a tuple-backed PSeq
shim. There are no @ContractOnly callees.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.models.expressions.When.as_sql`. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH/cwd make the patched modules
importable. The branch renderer's four inputs are the upstream compile
products of its condition and result; an injecting compiler hands those in
directly (returning the supplied fragment/params for the two sentinel nodes)
and DELEGATES every other compile call to a real SQLCompiler over a live
sqlite connection — so the always-true substitution inside the oracle runs
the genuine repo callee, not a stub.

Type bridge (mapping.md section 2 and 3):
  * SQL fragment `str` <-> model `List[int]` of code points via ord/chr.
  * bound-parameter list <-> `List[int]` of opaque identity tokens; the
    injected params are ints, returned verbatim by the oracle.
  * the model's abstract always-true constants (`true_predicate()` /
    `true_params()`) stand for the real always-true compile product (the
    documented deep-model reference). The substitution fires exactly when the
    supplied predicate fragment is empty, so the bridge deterministically
    rewrites that segment of the oracle output — the real fragment's code
    points to `true_predicate()` and the real params to `true_params()` —
    before the elementwise diff. Any structural mismatch leaves the oracle
    output un-rewritten and is reported as a disagreement.

Input domain: the Requires are pure access permissions, so every
(pred, pred_params, cons, cons_params) quadruple is Requires-satisfying.
Boundary cases cover the empty/non-empty predicate split, empty/non-empty
consequents and param lists, and fragments containing the framing keywords
and format-directive characters; fuzz draws random code-point fragments with
the empty predicate oversampled to exercise the substitution branch.

>= 1e5 Requires-satisfying inputs: 384 boundary cases + 100000 fuzz quads.
Pinned fuzz seed: 15930.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
from typing import List, Tuple  # noqa: F401  (kept for impl-region fidelity)

SEED = 15930
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure helpers use ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(xs):
    return PSeq._wrap(xs)


# --- pure helpers from model.py, contracts stripped ---------------------------

def lead():
    """The constant leading keyword spliced before the predicate: 'WHEN '."""
    return PSeq(87, 72, 69, 78, 32)


def sep():
    """The constant separating keyword spliced between predicate and
    consequent: ' THEN '."""
    return PSeq(32, 84, 72, 69, 78, 32)


def true_predicate():
    """The constant, NON-EMPTY always-true predicate fragment spliced in when
    the supplied predicate fragment is empty (abstract constant; bridged to
    the real always-true compile product below)."""
    return PSeq(84, 82, 85, 69)


def true_params():
    """The bound parameters carried by the always-true predicate: a single
    opaque parameter token."""
    return PSeq(1)


def clause_text(pred, cons):
    if len(pred) == 0:
        return lead() + true_predicate() + sep() + cons
    return lead() + pred + sep() + cons


def clause_params(pred, pred_params, cons_params):
    if len(pred) == 0:
        return true_params() + cons_params
    return pred_params + cons_params


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def render_branch(pred,          # type: List[int]
                  pred_params,   # type: List[int]
                  cons,          # type: List[int]
                  cons_params):  # type: List[int]
    # Determine the predicate slot text and its parameters: the supplied
    # predicate when non-empty, otherwise the constant always-true predicate.
    cond_text = []  # type: List[int]
    cond_params = []  # type: List[int]
    if len(pred) == 0:
        k = 0
        while k < len(true_predicate()):
            cond_text = cond_text + [true_predicate()[k]]
            k = k + 1
        k = 0
        while k < len(true_params()):
            cond_params = cond_params + [true_params()[k]]
            k = k + 1
    else:
        k = 0
        while k < len(pred):
            cond_text = cond_text + [pred[k]]
            k = k + 1
        k = 0
        while k < len(pred_params):
            cond_params = cond_params + [pred_params[k]]
            k = k + 1
    # Assemble lead + predicate-slot + sep + consequent.
    text = []  # type: List[int]
    i = 0
    while i < len(lead()):
        text = text + [lead()[i]]
        i = i + 1
    i = 0
    while i < len(cond_text):
        text = text + [cond_text[i]]
        i = i + 1
    i = 0
    while i < len(sep()):
        text = text + [sep()[i]]
        i = i + 1
    i = 0
    while i < len(cons):
        text = text + [cons[i]]
        i = i + 1
    # Combined parameters: predicate-slot parameters then consequent parameters.
    params = []  # type: List[int]
    i = 0
    while i < len(cond_params):
        params = params + [cond_params[i]]
        i = i + 1
    i = 0
    while i < len(cons_params):
        params = params + [cons_params[i]]
        i = i + 1
    return text, params


# --- oracle plumbing: drive the REAL patched branch renderer ------------------

def _configure_django():
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
    import django
    django.setup()


class _InjectingCompiler:
    """Hands the branch renderer its four upstream inputs: compile() of the
    two sentinel nodes returns the injected (fragment, params) pairs; every
    OTHER compile call (in particular the oracle's internal always-true
    substitution) delegates to the REAL compiler, so the substituted product
    is the genuine repo callee's output."""

    def __init__(self, inner):
        self._inner = inner
        self._map = {}

    def inject(self, node, sql, params):
        self._map[id(node)] = (sql, list(params))

    def compile(self, node):
        hit = self._map.get(id(node))
        if hit is not None:
            return hit
        return self._inner.compile(node)


def make_oracle():
    _configure_django()
    from django.db import connection
    from django.db.models import When, Value, Q
    from django.db.models.sql.compiler import SQLCompiler
    from django.db.models.sql.query import Query
    from django.contrib.auth.models import User

    query = Query(User)
    inner = SQLCompiler(query, connection, using="default")
    compiler = _InjectingCompiler(inner)

    # One reusable branch node; its condition/result are replaced by sentinel
    # objects whose compile products we inject per test case.
    when = When(Q(pk__gt=0), then=Value(1))
    cond_sentinel = object()
    result_sentinel = object()
    when.condition = cond_sentinel
    when.result = result_sentinel

    # The real always-true compile product, computed once through the same
    # delegate path the oracle's substitution uses; the bridge below rewrites
    # this segment of the oracle output to the model's abstract constants.
    true_sql, true_pl = inner.compile(Value(True))
    assert isinstance(true_sql, str) and true_sql != "", (true_sql, true_pl)

    def oracle(pred_s, pred_pl, cons_s, cons_pl):
        compiler.inject(cond_sentinel, pred_s, pred_pl)
        compiler.inject(result_sentinel, cons_s, cons_pl)
        sql, params = when.as_sql(compiler, connection)
        return sql, list(params)

    return oracle, true_sql, list(true_pl)


def bridge_oracle(sql, params, pred_s, true_sql, true_pl):
    """Lift the oracle output to the model's carriers. When the supplied
    predicate fragment is empty the oracle substitutes the real always-true
    product; rewrite exactly that segment to the model's abstract constants
    (true_predicate() / true_params()). If the segment does not match the
    real product the output is left as-is and the diff reports it."""
    if pred_s == "":
        head = "".join(chr(c) for c in lead())
        model_true = "".join(chr(c) for c in true_predicate())
        if sql.startswith(head + true_sql):
            sql = head + model_true + sql[len(head) + len(true_sql):]
        n = len(true_pl)
        if params[:n] == true_pl:
            params = [true_params()[k] for k in range(len(true_params()))] \
                + params[n:]
    return [ord(ch) for ch in sql], list(params)


# --- differential driver -------------------------------------------------------

def check_quad(oracle, true_sql, true_pl, pred_s, pred_pl, cons_s, cons_pl):
    """Run shadow and oracle on one quadruple; return an error string on
    disagreement, else None."""
    pred = [ord(ch) for ch in pred_s]
    cons = [ord(ch) for ch in cons_s]

    shadow_text, shadow_params = render_branch(pred, list(pred_pl),
                                               cons, list(cons_pl))
    # internal cross-check: impl agrees with the pure deep model
    assert ToSeq(shadow_text) == clause_text(ToSeq(pred), ToSeq(cons))
    assert ToSeq(shadow_params) == clause_params(
        ToSeq(pred), ToSeq(list(pred_pl)), ToSeq(list(cons_pl)))

    real_sql, real_params = oracle(pred_s, pred_pl, cons_s, cons_pl)
    real_text, real_pl = bridge_oracle(real_sql, real_params, pred_s,
                                       true_sql, true_pl)

    if shadow_text != real_text or shadow_params != real_pl:
        return ("DISAGREEMENT\n  pred=%r pred_params=%r\n"
                "  cons=%r cons_params=%r\n"
                "  shadow_text=%r (%r)\n  real_text=%r (raw sql %r)\n"
                "  shadow_params=%r\n  real_params=%r (raw %r)"
                % (pred_s, pred_pl, cons_s, cons_pl,
                   shadow_text, "".join(chr(c) for c in shadow_text),
                   real_text, real_sql,
                   shadow_params, real_pl, real_params))
    return None


def boundary_quads():
    preds = [
        "",                      # the substitution trigger
        "x",
        '"t"."id" > %s',         # placeholder-bearing fragment
        "%s",
        "TRUE",                  # equals the model's abstract constant text
        "WHEN ",                 # framing keyword as content
        " THEN ",
        "NOT (1 = 0)",
    ]
    conss = ["", "%s", "'selected'", " THEN ", "a, b"]
    param_lists = [[], [7], [2, 3, 5]]
    quads = []
    for p in preds:
        for c in conss:
            for ppl in param_lists:
                for cpl in ([], [11], [13, 17]):
                    quads.append((p, ppl, c, cpl))
    return quads


def main():
    oracle, true_sql, true_pl = make_oracle()

    checked = 0
    boundary = boundary_quads()
    for p, ppl, c, cpl in boundary:
        err = check_quad(oracle, true_sql, true_pl, p, ppl, c, cpl)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    codepoints = list(range(32, 127)) + [9, 233, 955, 0x4E2D]

    def rand_fragment(max_len):
        n = rng.randint(0, max_len)
        return "".join(chr(rng.choice(codepoints)) for _ in range(n))

    def rand_params(max_len):
        n = rng.randint(0, max_len)
        return [rng.randint(0, 10 ** 6) for _ in range(n)]

    for _ in range(N_FUZZ):
        # oversample the empty predicate: it is the discriminating branch
        pred_s = "" if rng.random() < 0.35 else rand_fragment(24)
        cons_s = rand_fragment(24)
        pred_pl = rand_params(4)
        cons_pl = rand_params(4)
        err = check_quad(oracle, true_sql, true_pl,
                         pred_s, pred_pl, cons_s, cons_pl)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched branch renderer on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
