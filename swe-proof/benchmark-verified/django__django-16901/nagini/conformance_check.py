#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16901 (nagini).

SHADOW: the impl region of model.py's ``xor_fallback_matches``, copied
VERBATIM below with only the contract calls (Requires / Ensures / Invariant /
Assert / MustTerminate) stripped. The @Pure helpers ``count_true`` /
``any_true`` / ``derived_count`` / ``xor_holds`` copy over as plain functions
on a small immutable PSeq shim and serve as an internal cross-check of the
executable shadow. There are no @ContractOnly callees (mapping.md section 3:
no axioms), so no real repo callee is substituted inside the shadow.

ORACLE: the REAL patched repo code the model models per mapping.md section 1
— the exclusive-disjunction fallback branch of
``django.db.models.sql.where.WhereNode.as_sql``. The gate applies patch.diff
to /testbed and sets PYTHONPATH=/testbed before this script runs, so the
import resolves to the patched module. Each probe builds a real
``WhereNode(children, XOR)`` whose k-th child is the lookup
``Exact(Value(operands[k]), 1)`` (true for a row exactly when the k-th entry
equals 1 — the documented operand-truth bridge), compiles it with a real
SQLCompiler against the in-container SQLite connection (SQLite reports
``supports_logical_xor = False``, so ``as_sql`` takes exactly the fallback
branch under check), and evaluates the produced predicate by executing
``SELECT 1 WHERE <sql>`` on that connection (Django's SQLite backend
registers the MOD user-defined function it needs). A row comes back exactly
when the fallback predicate holds for that operand assignment — the boolean
the model returns.

TYPE BRIDGE (mapping.md section 2): the model carrier is already
``List[int]`` of per-operand values (entry 1 <=> a true operand, any other
integer contributes 0), so probes pass the same list to both sides; the
oracle lifts each entry k into the child predicate "value_k == 1".

DOMAIN: the fallback combines the operand predicates of a node that HAS
children; a zero-operand node never reaches this branch (recorded in the
bundle's faithfulness audit), so generation uses len >= 1.

PERFORMANCE NOTE: the SQL text depends only on the operand count, so per
length the node is compiled ONCE with distinct sentinel parameter values and
each probe substitutes its entries at the recorded parameter positions; a
periodic direct compile-and-execute of the full pipeline cross-checks that
the template substitution is faithful.

>= 1e5 Requires-satisfying inputs: exhaustive 0/1 assignments for 1..12
operands (8190), non-binary and long boundary lists, plus 100000 random fuzz
lists (lengths 1..16, mostly 0/1 with mixed-integer salt). Pinned fuzz seed:
16901. Exit 0 iff zero disagreements; on disagreement prints the input and
both outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 16901
N_FUZZ = 100000
EXHAUSTIVE_MAX = 12
SENT_BASE = 90000001  # sentinel params; never collides with the constants 0/1/2
DIRECT_EVERY = 509    # cross-check the template against a direct compile


# --- PSeq shim: immutable sequence with the operations the model uses --------

class PSeq(object):
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

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, copied as plain functions ----------------------

def count_true(s):
    """Number of true operands: the sum of the per-operand 1/0 contributions
    (an operand contributes 1 exactly when its entry is 1)."""
    if len(s) == 0:
        return 0
    return (1 if s[0] == 1 else 0) + count_true(s.drop(1))


def any_true(s):
    """Disjunction of the operands: at least one operand is true."""
    if len(s) == 0:
        return False
    return s[0] == 1 or any_true(s.drop(1))


def derived_count(s):
    """The count compared against one by the re-expression: the raw number of
    true operands when there are at most two operands, its parity (remainder
    modulo two) when there are three or more."""
    if len(s) > 2:
        return count_true(s) % 2
    return count_true(s)


def xor_holds(s):
    """The truth value of the arithmetic re-expression on this assignment:
    the disjunction of the operands AND the derived count equals one."""
    return any_true(s) and derived_count(s) == 1


# --- impl region of model.py, verbatim with contract calls stripped ----------

def xor_fallback_matches(operands):
    total = 0
    any_t = False
    i = len(operands)
    while i > 0:
        c = operands[i - 1]
        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
        contribution = 1 if c == 1 else 0
        total = contribution + total
        any_t = (c == 1) or any_t
        i = i - 1
    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
    if len(operands) > 2:
        rhs = total % 2
    else:
        rhs = total
    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
    return any_t and rhs == 1


# --- oracle: the real patched fallback, driven through WhereNode.as_sql ------

def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            USE_TZ=False,
        )
    django.setup()


class Oracle(object):
    """Evaluates the real (patched) WhereNode XOR fallback for one operand
    assignment by compiling and executing the SQL it constructs."""

    def __init__(self):
        _setup_django()
        from django.db import connection
        from django.db.models import Value
        from django.db.models.lookups import Exact
        from django.db.models.sql.query import Query
        from django.db.models.sql.where import WhereNode, XOR

        connection.ensure_connection()
        if connection.features.supports_logical_xor:
            raise RuntimeError(
                "oracle backend evaluates the connective natively; the "
                "fallback branch under check would not be exercised")
        self.connection = connection
        self.Value = Value
        self.Exact = Exact
        self.Query = Query
        self.WhereNode = WhereNode
        self.XOR = XOR
        self.cursor = connection.cursor()
        self._templates = {}

    def _compile(self, values):
        """Build the real node for these operand values and run the real
        patched as_sql (SQLite takes the fallback branch)."""
        children = [self.Exact(self.Value(v), 1) for v in values]
        node = self.WhereNode(children, self.XOR)
        compiler = self.Query(None).get_compiler(connection=self.connection)
        sql, params = node.as_sql(compiler, self.connection)
        return sql, list(params)

    def _execute(self, sql, params):
        self.cursor.execute("SELECT 1 WHERE " + sql, params)
        return self.cursor.fetchone() is not None

    def _template(self, n):
        t = self._templates.get(n)
        if t is None:
            sents = [SENT_BASE + 13 * k for k in range(n)]
            sql, params = self._compile(sents)
            sent_index = {s: k for k, s in enumerate(sents)}
            positions = [[] for _ in range(n)]
            for i, p in enumerate(params):
                k = sent_index.get(p)
                if k is not None:
                    positions[k].append(i)
            for k in range(n):
                if not positions[k]:
                    raise RuntimeError(
                        "template for %d operands lost operand %d in the "
                        "compiled parameters" % (n, k))
            t = (sql, params, positions)
            self._templates[n] = t
        return t

    def evaluate(self, xs):
        """Truth value of the real fallback predicate for this assignment
        (template-compiled SQL, per-probe parameter substitution)."""
        sql, base, positions = self._template(len(xs))
        params = list(base)
        for k, pos in enumerate(positions):
            for i in pos:
                params[i] = xs[k]
        return self._execute(sql, params)

    def evaluate_direct(self, xs):
        """Same value via a fresh compile of the real as_sql on the concrete
        values — cross-checks the template substitution."""
        sql, params = self._compile(xs)
        return self._execute(sql, params)


# --- input generation ---------------------------------------------------------

def boundary_lists():
    out = []
    # exhaustive 0/1 assignments across the <=2 / >2 operand-count split
    for n in range(1, EXHAUSTIVE_MAX + 1):
        for mask in range(2 ** n):
            out.append([(mask >> k) & 1 for k in range(n)])
    # non-binary entries: anything other than 1 must count as a false operand
    out += [
        [2], [-1], [0], [1], [10 ** 9], [-10 ** 9],
        [0, 2], [2, 2], [1, 2], [2, 1], [2, 0],
        [1, 2, 3], [2, 3, 4], [1, 1, 2], [1, 2, 1], [2, 1, 1],
        [1, 1, 1, 2], [7, 1, 7, 1, 7], [-1, 1, -1],
        [1000000, 1], [1, 10 ** 9, -10 ** 9, 1, 1],
        [2, 2, 2, 2, 2], [0, 0, 0, 2],
    ]
    # lengths beyond the exhaustive bound, both parities of the true-count
    out += [
        [1] * 13, [1] * 14, [1] * 15, [1] * 16,
        [0] * 13, [0] * 15 + [1], [1, 0] * 8, [0, 1] * 8,
        [1] * 13 + [0], [1] * 12 + [0, 0, 0, 1],
        [1, 1, 0] * 5, [2] * 16, [1, 2] * 8,
    ]
    return out


def fuzz_list(rng):
    n = rng.randint(1, 16)
    if rng.random() < 0.7:
        return [rng.randint(0, 1) for _ in range(n)]
    salt = (0, 1, 1, 2, -1, 3, 42, -7, 10 ** 6, -10 ** 6)
    return [rng.choice(salt) for _ in range(n)]


# --- differential driver -------------------------------------------------------

def main(oracle=None):
    if oracle is None:
        oracle = Oracle()

    checked = 0

    def check(xs, cross_direct):
        shadow = xor_fallback_matches(list(xs))
        # internal cross-check: the impl region agrees with the pure spec fns
        s = ToSeq(xs)
        if shadow != xor_holds(s) or shadow != (count_true(s) % 2 == 1):
            return ("INTERNAL: impl region and pure region disagree on %r "
                    "(impl=%r, xor_holds=%r, parity=%r)"
                    % (xs, shadow, xor_holds(s), count_true(s) % 2 == 1))
        real = oracle.evaluate(xs)
        if shadow != real:
            return ("DISAGREEMENT on operands %r:\n"
                    "  shadow (impl region)              = %r\n"
                    "  real (patched WhereNode fallback) = %r"
                    % (xs, shadow, real))
        if cross_direct:
            direct = oracle.evaluate_direct(xs)
            if direct != real:
                return ("TEMPLATE INCONSISTENCY on operands %r: "
                        "template SQL = %r, direct compile = %r"
                        % (xs, real, direct))
        return None

    boundary = boundary_lists()
    for idx, xs in enumerate(boundary):
        # direct-compile cross-check on a periodic subsample + every
        # non-binary/long case (everything past the exhaustive block)
        cross = (idx % DIRECT_EVERY == 0) or (idx >= 2 ** (EXHAUSTIVE_MAX + 1) - 2)
        err = check(xs, cross)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for j in range(N_FUZZ):
        xs = fuzz_list(rng)
        err = check(xs, j % DIRECT_EVERY == 0)
        if err:
            print(err)
            return 1
        checked += 1

    print("PASS: shadow impl == real patched fallback predicate on %d inputs "
          "(%d boundary incl. exhaustive 0/1 up to %d operands + %d fuzz, "
          "seed %d); 0 disagreements."
          % (checked, len(boundary), EXHAUSTIVE_MAX, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
