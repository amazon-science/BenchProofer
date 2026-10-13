#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15563 (nagini).

SHADOW: the impl region of model.py `assign_columns`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped. The impl
runs on plain Python lists of 0/1 flags, so it executes directly — no
transliteration. The @Pure helper `count_fresh` copies over as a plain
function on top of a tuple-backed PSeq shim; it is used to derive the
pre-selection row width (1 + number of fresh targets) and as an internal
cross-check of the dense-column pin. There are no @ContractOnly callees.

ORACLE: the REAL patched repo method the model models per mapping.md —
`django.db.models.sql.compiler.SQLUpdateCompiler.pre_sql_setup`. The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched module importable. The method is driven with stand-ins
injected at exactly the modeling boundary mapping.md documents:

  * the per-target path-classification predicate value is an abstracted INPUT
    (the model's `chain[k]` flag, an A-reference validated by axiom_check.py /
    G-AX): each stand-in ancestor target's path metadata is built so the real
    conjunction over `path.join_field.primary_key` evaluates to the fuzzed
    flag (True realized by all-primary-key hop lists of varying length,
    including the empty-path realization; False by hop lists with at least
    one non-primary-key hop at a randomized position);
  * the pre-selection execution is a stub compiler handing back the fuzzed
    result rows (in one or more blocks, as the real MULTI iteration consumes
    them) — the fetch itself is unchanged plumbing that merely produces the
    rows the assigned columns are read from;
  * the query objects are attribute-level stand-ins recording the observable
    effects (the selected field list, the per-target identifying-value lists,
    the source-row filter); the inherited base-class setup step is
    neutralized for the run (it is unchanged machinery operating on ORM state
    the abstraction drops, and it produces nothing the modeled behaviour
    reads).

Everything between those boundaries — the per-target column assignment, the
per-block projection of each target's assigned column, and the per-target
value lists stored for the downstream per-ancestor filters — is the REAL
patched code, exercised end to end.

Observables compared per input:
  (1) per target k, the identifying-value list the real method stores for it
      (the values its downstream update is filtered by) == the shadow's
      projection of column `assign_columns(flags)[k]` over all rows;
  (2) the width of the selected field list == the shadow's derived row width
      1 + count_fresh(flags) (the dense pin: fresh columns are exactly the
      contiguous block 1..F);
  (3) the source-row filter values == column 0 of all rows.

Type bridge (mapping.md section 2): the ordered mapping of ancestor targets
<-> the index domain 0..len(flags)-1 (stand-in target objects keep insertion
order); the path predicate bool <-> the 0/1 int flag; the recorded column
index is compared through observable (1) — with per-case unique-valued row
grids in the boundary layer, projection equality pins the column index
itself.

Input domain: the Requires ask that every chain entry be 0 or 1 (plus access
permissions), so every 0/1 flag vector is Requires-satisfying; rows are free
inputs of the derived width. Boundary cases cover the empty vector, all-ones,
all-zeros, single-target vectors, alternating patterns, the F2P-shaped
single-fresh-target case, zero rows, and multi-block row delivery; the fuzz
layer randomizes vector length, flag pattern, path-shape realization, row
count, block split, and values.

>= 1e5 Requires-satisfying inputs: 40 boundary cases + 100000 fuzz cases.
Pinned fuzz seed: 215563.

Exit 0 iff zero disagreements; on disagreement prints the input and both
sides' observations and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 215563
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the pure helper uses ------

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

    def drop(self, n):
        return PSeq._of(self._t[n:])


# --- @Pure helper from model.py, contracts stripped ---------------------------

def count_fresh(s):
    if len(s) == 0:
        return 0
    elif s[0] == 0:
        return 1 + count_fresh(s.drop(1))
    else:
        return count_fresh(s.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def assign_columns(chain):
    result = []  # type: List[int]
    width = 1
    i = 0
    while i < len(chain):
        if chain[i] == 1:
            result = result + [0]
        else:
            result = result + [width]
            width = width + 1
        i = i + 1
    return result


# --- oracle plumbing: stand-ins at the modeling boundary ----------------------

class _PK:
    def __init__(self, name):
        self.name = name


class _TargetMeta:
    def __init__(self, pk_name):
        self.pk = _PK(pk_name)


class _Target:
    """Stand-in ancestor target: an ordered-dict key with its own pk metadata."""

    def __init__(self, k):
        self._k = k
        self._meta = _TargetMeta("target_pk_%d" % k)

    def __repr__(self):
        return "<target %d>" % self._k


class _JoinField:
    def __init__(self, primary_key):
        self.primary_key = primary_key


class _PathHop:
    def __init__(self, primary_key):
        self.join_field = _JoinField(primary_key)


class _SourceMeta:
    """The source model's metadata: its own pk (column 0's field) and the
    per-target path metadata realizing the fuzzed predicate values."""

    def __init__(self, paths_by_target):
        self.pk = _PK("source_pk")
        self._paths = paths_by_target

    def get_path_to_parent(self, related):
        return self._paths[related]


class _RowSource:
    """Stub pre-selection compiler: hands back the fuzzed row blocks."""

    def __init__(self, blocks):
        self._blocks = blocks

    def execute_sql(self, result_type):
        return iter(self._blocks)


class _InnerQuery:
    """The chained pre-selection query stand-in: records the selected field
    list and serves the row blocks."""

    def __init__(self, meta, blocks):
        self._meta = meta
        self._blocks = blocks
        self.added_fields = None
        self.select_related = None
        self.extra = None
        self.select = None

    def clear_ordering(self, force=False):
        pass

    def get_meta(self):
        return self._meta

    def add_fields(self, fields):
        self.added_fields = list(fields)

    def get_compiler(self, using):
        return _RowSource(self._blocks)


class _OuterQuery:
    """The update query stand-in: carries the ordered targets and records the
    observable effects (filter values, per-target identifying values)."""

    def __init__(self, related_updates, inner):
        self.alias_refcount = {}
        self.related_updates = related_updates
        self._inner = inner
        self.related_ids = None
        self.filters = []

    def get_initial_alias(self):
        return "source_table"

    def count_active_tables(self):
        # >1 active table + a backend that cannot self-select forces the
        # pre-selection branch even with zero targets, so the empty flag
        # vector is exercised on the real path too.
        return 2

    def chain(self, klass=None):
        return self._inner

    def clear_where(self):
        pass

    def add_filter(self, name, value):
        self.filters.append((name, list(value)))

    def reset_refcounts(self, refcounts):
        pass


class _Features:
    update_can_self_select = False


class _Connection:
    features = _Features()


def make_oracle():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    from django.db.models.sql.compiler import SQLUpdateCompiler, SQLCompiler

    # Neutralize the inherited base-class setup step for the whole run: it is
    # unchanged machinery operating on real ORM state the abstraction drops
    # (mapping.md section 2), and nothing the modeled behaviour reads flows
    # from it.
    SQLCompiler.pre_sql_setup = lambda self: None

    def oracle(flags, blocks, rng):
        # Realize each flag as path metadata whose real conjunction over the
        # hops' primary_key evaluates to exactly that flag.
        targets = [_Target(k) for k in range(len(flags))]
        paths = {}
        for k, f in enumerate(flags):
            if f == 1:
                # every hop is a primary-key link; the empty path (a target
                # coinciding with the source) also realizes True.
                n = rng.randint(0, 3)
                paths[targets[k]] = [_PathHop(True) for _ in range(n)]
            else:
                n = rng.randint(1, 3)
                hops = [_PathHop(rng.random() < 0.5) for _ in range(n)]
                hops[rng.randrange(n)].join_field.primary_key = False
                paths[targets[k]] = hops
        meta = _SourceMeta(paths)
        inner = _InnerQuery(meta, [[tuple(r) for r in block]
                                   for block in blocks])
        related_updates = {}
        for t in targets:
            related_updates[t] = ["placeholder-values"]
        outer = _OuterQuery(related_updates, inner)

        compiler = object.__new__(SQLUpdateCompiler)
        compiler.query = outer
        compiler.connection = _Connection()
        compiler.using = "default"
        compiler.pre_sql_setup()

        per_target = [list(outer.related_ids[t]) for t in targets]
        n_fields = len(inner.added_fields) if inner.added_fields is not None else None
        source_filter = None
        for name, value in outer.filters:
            if name == "pk__in":
                source_filter = value
        return per_target, n_fields, source_filter

    return oracle


# --- differential driver -------------------------------------------------------

def shadow(flags, rows):
    cols = assign_columns(list(flags))
    # internal cross-check of the dense pin: column 0 iff flag 1; fresh
    # columns are the contiguous block 1..F in target order.
    total = count_fresh(PSeq._of(flags))
    for k in range(len(flags)):
        assert (cols[k] == 0) == (flags[k] == 1)
        if flags[k] == 0:
            assert cols[k] == 1 + (total - count_fresh(PSeq._of(flags).drop(k)))
    width = 1 + total
    per_target = [[r[c] for r in rows] for c in cols]
    idents = [r[0] for r in rows]
    return per_target, width, idents


def check_case(oracle, flags, blocks, rng):
    rows = [r for block in blocks for r in block]
    s_per_target, s_width, s_idents = shadow(flags, rows)
    try:
        r_per_target, r_fields, r_filter = oracle(flags, blocks, rng)
    except Exception as exc:
        return ("DISAGREEMENT (oracle raised)\n  flags=%r\n  blocks=%r\n"
                "  shadow=(%r, width=%r, idents=%r)\n  real raised: %r"
                % (flags, blocks, s_per_target, s_width, s_idents, exc))
    if (s_per_target != r_per_target or s_width != r_fields
            or s_idents != r_filter):
        return ("DISAGREEMENT\n  flags=%r\n  blocks=%r\n"
                "  shadow: per_target=%r width=%r idents=%r\n"
                "  real:   per_target=%r n_fields=%r filter=%r"
                % (flags, blocks, s_per_target, s_width, s_idents,
                   r_per_target, r_fields, r_filter))
    return None


def unique_grid(flags, n_rows):
    """Rows with per-(row, column) unique values so projection equality pins
    the column index itself."""
    width = 1 + sum(1 for f in flags if f == 0)
    return [[(r + 1) * 10007 + c for c in range(width)]
            for r in range(n_rows)]


def boundary_cases():
    cases = []
    flag_vectors = [
        [],
        [1],
        [0],            # F2P-shaped: one target reached through a non-pk link
        [1, 1],
        [0, 0],
        [1, 0],
        [0, 1],
        [1, 0, 1],
        [0, 1, 0],
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [1, 0, 0, 1, 0],
        [0, 1, 1, 0, 1, 0],
    ]
    for flags in flag_vectors:
        for n_rows in (0, 1, 3):
            rows = unique_grid(flags, n_rows)
            cases.append((flags, [rows]))
    # multi-block delivery of the same grid
    cases.append(([0, 1], [unique_grid([0, 1], 2), unique_grid([0, 1], 1)]))
    return cases


def main():
    oracle = make_oracle()

    checked = 0
    boundary = boundary_cases()
    for flags, blocks in boundary:
        rng = random.Random(SEED + checked)
        err = check_case(oracle, flags, blocks, rng)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 10)
        flags = [rng.randint(0, 1) for _ in range(n)]
        width = 1 + sum(1 for f in flags if f == 0)
        n_rows = rng.randint(0, 5)
        rows = [[rng.randint(-10**6, 10**6) for _ in range(width)]
                for _ in range(n_rows)]
        # split into 1-3 blocks (the real iteration consumes rows per block)
        n_blocks = rng.randint(1, 3)
        blocks = []
        start = 0
        for b in range(n_blocks - 1):
            end = rng.randint(start, n_rows)
            blocks.append(rows[start:end])
            start = end
        blocks.append(rows[start:])
        err = check_case(oracle, flags, blocks, rng)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched column assignment + "
          "projection on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
