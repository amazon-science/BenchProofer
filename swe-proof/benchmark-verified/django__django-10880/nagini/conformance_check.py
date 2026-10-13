#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-10880 (nagini).

SHADOW: the impl region of model.py `render_fragment`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. The impl
region operates on plain Python lists, so it is directly executable as-is. The
@Pure helpers (kw_distinct/sep/open_paren/close_paren/modifier/fragment) copy
over as plain functions on top of a tuple-backed PSeq shim; they are used only
as an internal cross-check of the shadow. There are no @ContractOnly callees.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.models.aggregates.Aggregate.as_sql`, whose rendered SQL string is
produced by the inherited `django.db.models.expressions.Func.as_sql` template
substitution. The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched modules importable. The aggregate is
driven with a stub compiler (returns the pre-compiled operand text verbatim,
which is exactly what `%(expressions)s` receives after arg_joiner.join over a
single part) and a stub connection (feature/support hooks are no-ops); the
function keyword is supplied through Func's **extra plumbing. This isolates
precisely the modeled operation: the rendered fragment for a given
(function keyword, operand text, duplicate-eliminating mode) triple.

Type bridge (mapping.md section 2): repo `str` <-> model `List[int]` of code
points via ord/chr; `bool` carries over identically. The oracle's returned SQL
string is lifted to a code-point list and compared elementwise against the
shadow's result list.

Input domain: the Requires are pure access permissions, so every
(function, operands, distinct) triple over code-point lists is
Requires-satisfying. Generation mirrors axiom_check.py: every boundary
function keyword x operand shape x both modes, plus randomized printable-ish
strings in both modes.

>= 1e5 Requires-satisfying inputs: 112 boundary cases + 100000 fuzz triples.
Pinned fuzz seed: 10880.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 10880
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


# --- pure helpers from model.py, contracts stripped ---------------------------

def kw_distinct():
    # D, I, S, T, I, N, C, T
    return PSeq(68, 73, 83, 84, 73, 78, 67, 84)


def sep():
    return 32


def open_paren():
    return PSeq(40)   # '('


def close_paren():
    return PSeq(41)   # ')'


def modifier(distinct):
    if distinct:
        return kw_distinct() + PSeq(sep())
    return PSeq(0).take(0)


def fragment(function, operands, distinct):
    return function + open_paren() + modifier(distinct) + operands + close_paren()


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def render_fragment(function, operands, distinct):
    result = []  # type: List[int]
    # NAME
    j = 0
    while j < len(function):
        result.append(function[j])
        j = j + 1
    # opening delimiter
    result.append(40)
    # modifier
    if distinct:
        result.append(68)
        result.append(73)
        result.append(83)
        result.append(84)
        result.append(73)
        result.append(78)
        result.append(67)
        result.append(84)
        result.append(32)
    # operands
    k = 0
    while k < len(operands):
        result.append(operands[k])
        k = k + 1
    # closing delimiter
    result.append(41)
    return result


# --- oracle plumbing: drive the REAL patched Aggregate.as_sql -----------------

class _StubOps:
    def check_expression_support(self, expression):
        pass


class _StubFeatures:
    supports_aggregate_filter_clause = False


class _StubConnection:
    ops = _StubOps()
    features = _StubFeatures()


class _StubCompiler:
    """Returns the pre-compiled operand text for the single source expression;
    this is exactly the already-joined text the template's expressions field
    receives (the model's `operands` carrier)."""

    def __init__(self, operand_text):
        self._text = operand_text

    def compile(self, node):
        return self._text, []


def make_oracle():
    import django.conf
    if not django.conf.settings.configured:
        django.conf.settings.configure()
    from django.db.models.aggregates import Aggregate

    class _ProbeAggregate(Aggregate):
        name = 'Probe'
        allow_distinct = True

    def oracle(function_s, operands_s, distinct):
        # The function keyword flows in through Func's **extra plumbing
        # (data.setdefault path); the operand text through the stub compiler.
        agg = _ProbeAggregate('placeholder', distinct=distinct,
                              function=function_s)
        sql, params = agg.as_sql(_StubCompiler(operands_s), _StubConnection())
        assert params == [], params
        return sql

    return oracle


# --- differential driver -------------------------------------------------------

def check_triple(oracle, function_s, operands_s, distinct):
    """Run shadow and oracle on one triple; return an error string on
    disagreement, else None."""
    function = [ord(ch) for ch in function_s]
    operands = [ord(ch) for ch in operands_s]

    shadow = render_fragment(function, operands, distinct)
    # internal cross-check: impl agrees with the pure deep model
    assert PSeq._wrap(shadow) == fragment(PSeq._wrap(function),
                                          PSeq._wrap(operands), distinct)

    real = oracle(function_s, operands_s, distinct)
    real_pts = [ord(ch) for ch in real]

    if shadow != real_pts:
        return ("DISAGREEMENT\n  function=%r\n  operands=%r\n  distinct=%r\n"
                "  shadow=%r (%r)\n  real=%r (%r)"
                % (function_s, operands_s, distinct,
                   shadow, "".join(chr(c) for c in shadow), real_pts, real))
    return None


def boundary_triples():
    functions = ["COUNT", "SUM", "AVG", "MAX", "MIN", "", "F"]
    operands = [
        "",                                       # empty operand text
        "CASE WHEN pages > 300 THEN rating END",  # conditional operand text
        "rating",
        "*",
        "publisher_id",
        "a, b, c",
        "T1.col",
        "x",
    ]
    return [(f, o, d) for f in functions for o in operands
            for d in (True, False)]


def main():
    oracle = make_oracle()

    checked = 0
    boundary = boundary_triples()
    for f, o, d in boundary:
        err = check_triple(oracle, f, o, d)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    alphabet = [chr(c) for c in range(33, 127)] + [" ", "\t"]
    for _ in range(N_FUZZ):
        nf = rng.randint(0, 8)
        no = rng.randint(0, 32)
        f = "".join(rng.choice(alphabet) for _ in range(nf))
        o = "".join(rng.choice(alphabet) for _ in range(no))
        d = rng.random() < 0.5
        err = check_triple(oracle, f, o, d)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched render on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
