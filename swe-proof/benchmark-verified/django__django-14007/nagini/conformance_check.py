#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14007 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (Assert/Invariant lines removed; the executable statements are
untouched), plus the @Pure helper `fold_chain` copied over as a plain
function. PSeq is bridged by a small immutable-sequence shim providing the
operations the impl uses (construction, len, indexing, take, drop, +). The
one @ContractOnly callee, `step(converter_id, value)`, calls the REAL repo
callee it models: a single value converter, i.e. `step` invokes the very
converter callable that the real pipeline invokes for that chain position
(mapping.md section 2 bridges a converter id to one converter callable; the
extra expression/connection arguments are opaque pass-throughs the exercised
converters ignore, as mapping.md notes for the modeled fields).

ORACLE: the REAL patched repo method the model models per mapping.md —
`django.db.models.sql.compiler.SQLInsertCompiler.execute_sql`. The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched code importable. The method's inputs that the model
abstracts away are injected at exactly the modeling boundary mapping.md
documents:

  * the raw returned rows are an abstracted input (`rows`): the backend
    row-source hook on the connection ops is stubbed to hand back the fuzzed
    rows (that hook is UNCHANGED and merely produces the model's `rows`
    input, per mapping.md section 1);
  * the per-column converter chains are an abstracted input (`chains`): each
    returning field is a stand-in whose column expression reports the fuzzed
    chain of converter callables through the standard per-expression
    converter-discovery hook (an empty chain column reports none, so the
    discovery step omits it — the identity case);
  * the SQL emission and cursor execution are stubbed to no-ops (no DB I/O);
    they precede the modeled behaviour and produce nothing the model reads.

Everything downstream of those inputs — the branch structure, the converter
discovery over the returning columns, the conversion pipeline application,
and the returned value — is the REAL patched code, exercised end to end.
A secondary driver routes single-row single-column cases through the
fallback row-source branch (the last-resort id lookup) to confirm the
conversion is branch-independent.

Type bridge (mapping.md section 2): rows of int column values <-> the
sequence-of-row-sequences carrier; a converter id <-> one converter
callable; the converted values may be arbitrary objects produced by the
converters (compared with ==). ncols == number of returning fields ==
len(chains). The ncols == 0 point of the input domain is realizable on the
real path only with rows == [] (with no returning fields the method returns
[] before any row is fetched), so that boundary case is checked with
rows == [] and fuzz uses ncols >= 1; this is the documented modeling
boundary, not a domain restriction of the shadow.

Input domain (the model's Requires): ncols >= 0, len(chains) == ncols,
every row of width ncols. Boundary cases cover 0 rows, the single-row
single-converter case, multi-row, empty chains (identity), multi-column
mixed chains, order-sensitive multi-step chains, zero columns, and extreme
int values; fuzz draws rows x cols x per-column chains with empty chains
common.

>= 1e5 Requires-satisfying inputs: 17 boundary + 100000 fuzz cases.
Pinned fuzz seed: 914007.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 914007
N_FUZZ = 100_000


# --- PSeq bridge: immutable sequence with the operations the impl uses -------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _of(cls, iterable):
        s = cls()
        s._t = tuple(iterable)
        return s

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def take(self, n):
        return PSeq._of(self._t[:n])

    def drop(self, n):
        return PSeq._of(self._t[n:])

    def __add__(self, other):
        return PSeq._of(self._t + other._t)


# --- @ContractOnly callee: calls the REAL converter callable ------------------

def step(converter_id, value):
    # The bridge maps a converter id to the converter callable itself; the
    # trailing expression/connection arguments are ignored by the exercised
    # converters (pure value -> value maps, per mapping.md).
    return converter_id(value, None, None)


# --- @Pure helper from model.py, decorator stripped ---------------------------

def fold_chain(chain, value):
    if len(chain) == 0:
        return value
    return fold_chain(chain.drop(1), step(chain[0], value))


# --- the impl region of model.py, verbatim (contract calls stripped) ----------

def apply_row(row, chains, ncols):
    out = PSeq(0).take(0)  # type: PSeq[int]
    p = 0
    while p < ncols:
        old = out  # type: PSeq[int]
        nv = fold_chain(chains[p], row[p])
        out = out + PSeq(nv)
        p = p + 1
    return out


def execute_returning(rows, chains, ncols):
    out = rows.take(0)  # type: PSeq[PSeq[int]]
    j = 0
    while j < len(rows):
        old = out  # type: PSeq[PSeq[int]]
        cr = apply_row(rows[j], chains, ncols)
        out = out + PSeq(cr)
        j = j + 1
    return out


def shadow(rows, chains):
    """Run the shadow on plain lists: wrap into the sequence carrier, run the
    verbatim impl, unwrap to lists of lists."""
    ncols = len(chains)
    rows_ps = PSeq._of(PSeq._of(r) for r in rows)
    chains_ps = PSeq._of(PSeq._of(c) for c in chains)
    out = execute_returning(rows_ps, chains_ps, ncols)
    return [list(out[j]._t) for j in range(len(out))]


# --- oracle: drive the REAL patched method at the modeling boundary -----------

class _Cursor:
    def execute(self, sql, params=None):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _Features:
    def __init__(self, bulk_rows, columns):
        self.can_return_rows_from_bulk_insert = bulk_rows
        self.can_return_columns_from_insert = columns


class _Ops:
    """Connection ops stand-in: the row-source hooks hand back the fuzzed raw
    rows (they are unchanged producers of the model's `rows` input), and the
    backend-level converter discovery reports none (chains are injected
    per-field)."""

    def __init__(self, rows):
        self._rows = rows

    def get_db_converters(self, expression):
        return []

    def fetch_returned_insert_rows(self, cursor):
        return [tuple(r) for r in self._rows]

    def last_insert_id(self, cursor, table, pk_column):
        # Only used by the single-row single-column fallback driver.
        return self._rows[0][0]


class _Connection:
    def __init__(self, rows, features):
        self.features = features
        self.ops = _Ops(rows)

    def cursor(self):
        return _Cursor()


class _PK:
    column = "id"


class _Opts:
    db_table = "t"
    pk = _PK()


class _Query:
    def __init__(self, nobjs):
        self.objs = [object()] * nobjs

    def get_meta(self):
        return _Opts()


class _Col:
    """A returning column expression stand-in: truthy, and reports its
    column's converter chain through the standard per-expression converter
    discovery hook."""

    def __init__(self, chain):
        self._chain = list(chain)

    def get_db_converters(self, connection):
        return list(self._chain)


class _Field:
    def __init__(self, chain):
        self._chain = chain

    def get_col(self, table):
        return _Col(self._chain)


def make_real(SQLInsertCompiler):
    def real(rows, chains, branch="bulk"):
        ncols = len(chains)
        if branch == "bulk":
            features = _Features(bulk_rows=True, columns=False)
            nobjs = 2
        else:  # the fallback single-id branch: exactly one row, one column
            features = _Features(bulk_rows=False, columns=False)
            nobjs = 1
        compiler = object.__new__(SQLInsertCompiler)
        compiler.query = _Query(nobjs)
        compiler.connection = _Connection(rows, features)
        compiler.using = "default"
        compiler.returning_params = None
        compiler.as_sql = lambda: []  # SQL emission precedes the modeled tail
        fields = [_Field(chains[p]) for p in range(ncols)]
        out = compiler.execute_sql(returning_fields=fields)
        return [list(r) for r in out]
    return real


# --- differential --------------------------------------------------------------

def check_case(real, rows, chains, branch="bulk"):
    shadow_out = shadow(rows, chains)
    real_out = real(rows, chains, branch)
    if shadow_out != real_out:
        return ("DISAGREEMENT (branch=%s)\n  rows=%r\n  chains=%r\n"
                "  shadow=%r\n  real=%r"
                % (branch, rows, [[getattr(c, "__name__", repr(c)) for c in ch]
                                  for ch in chains], shadow_out, real_out))
    return None


class Wrapper:
    """A converted-value carrier (models a converter that changes the value's
    type); equality by payload so both sides compare with ==."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __eq__(self, o):
        return isinstance(o, Wrapper) and o.v == self.v

    def __repr__(self):
        return "Wrapper(%r)" % (self.v,)


def _unwrap(v):
    while isinstance(v, Wrapper):
        v = v.v
    return v


def wrap(value, expression, connection):
    return Wrapper(_unwrap(value))


def add1(value, expression, connection):
    return _unwrap(value) + 1


def times2(value, expression, connection):
    return _unwrap(value) * 2


def to_neg(value, expression, connection):
    return -_unwrap(value)


CONVERTER_POOL = [wrap, add1, times2, to_neg]


def boundary_cases():
    """(rows, chains, branch) triples; branch 'last' = the fallback
    single-row single-column row source."""
    return [
        # zero columns: realizable on the real path only with no rows
        ([], [], "bulk"),
        # 0 rows, 1 col, empty chain
        ([], [[]], "bulk"),
        # single row, single column, single type-changing converter
        ([[2]], [[wrap]], "bulk"),
        ([[2]], [[wrap]], "last"),
        # several rows, single column, converter applied to each row
        ([[1], [2], [3]], [[wrap]], "bulk"),
        # empty chain => identity passthrough
        ([[7], [8]], [[]], "bulk"),
        ([[7]], [[]], "last"),
        # multi-column: one converted, one identity
        ([[5, 9], [6, 10]], [[wrap], []], "bulk"),
        # multi-step chains: order matters (left fold)
        ([[3]], [[add1, times2]], "bulk"),
        ([[3]], [[times2, add1]], "bulk"),
        ([[3]], [[add1, times2]], "last"),
        # several columns each with their own chain
        ([[1, 2, 3]], [[wrap], [add1, add1], [to_neg]], "bulk"),
        # extreme values
        ([[2 ** 63], [-(2 ** 63)]], [[add1]], "bulk"),
        ([[0], [-1], [1]], [[to_neg, wrap]], "bulk"),
        ([[10 ** 18, -(10 ** 18)]], [[times2], [times2]], "bulk"),
        # wider grid, all identity
        ([[1, 2, 3, 4], [5, 6, 7, 8]], [[], [], [], []], "bulk"),
        # single row through the fallback branch, negative value
        ([[-42]], [[wrap]], "last"),
    ]


def rand_case(rng):
    ncols = rng.randint(1, 4)   # ncols == 0 covered as a boundary case
    nrows = rng.randint(0, 4)
    rows = []
    for _ in range(nrows):
        row = []
        for _ in range(ncols):
            k = rng.random()
            if k < 0.8:
                row.append(rng.randint(-50, 50))
            elif k < 0.95:
                row.append(rng.randint(-10 ** 6, 10 ** 6))
            else:
                row.append(rng.randint(-2 ** 66, 2 ** 66))
        rows.append(row)
    chains = []
    for _ in range(ncols):
        clen = rng.randint(0, 3)  # empty chains common
        chains.append([rng.choice(CONVERTER_POOL) for _ in range(clen)])
    return rows, chains


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    # REAL patched method under test.
    from django.db.models.sql.compiler import SQLInsertCompiler
    real = make_real(SQLInsertCompiler)

    checked = 0
    for rows, chains, branch in boundary_cases():
        err = check_case(real, rows, chains, branch)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        rows, chains = rand_case(rng)
        err = check_case(real, rows, chains)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real row-returning insert conversion on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
