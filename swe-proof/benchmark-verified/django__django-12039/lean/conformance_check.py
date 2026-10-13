#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12039.

The bundle models two routines from `django/db/backends/ddl_references.py`:
`Columns.__str__` (renderColumns) and `IndexColumns.__str__` (renderIndexColumns).
Both render a comma-joined column clause; the fix makes the positional render
hint (`col_suffixes[idx]`) append only when non-empty, set off by a single space.

The modeled value is a PURE function of the observables each `__str__` reads
(`self.columns`, `self.col_suffixes`, `self.opclasses`, and the bound
`self.quote_name`). Standing up the full SchemaEditor/Index machinery is heavy
and unnecessary, so the ORACLE is a faithful in-process replica of the
POST-PATCH `col_str` bodies, and the SHADOW is the op-for-op transliteration of
the `implementation_*` impl regions (Solution.lean), per refinement.md.

`self.quote_name` is universally quantified in the Lean theorems; here we
instantiate it with a concrete quoter (double-quoting, like the real backends)
so the rendering/separation logic is what gets differential-tested.

This tests the soundness-critical clause for BOTH functions:
* an ascending column carries an EMPTY suffix → no trailing space, no stray
  separator (the `("name"DESC)` vs `("name")` and `text_pattern_ops ` bugs);
* a non-empty suffix is appended with exactly one separating space.

stdlib-only. Pinned seed: 12039 (also in mapping.md).
"""
import random
import sys

SEED = 12039
N = 120_000

NAME_POOL = ["name", "headline", "pubdate", "author", "id", "col_x"]
# realistic col_suffixes tokens: '' (ascending), 'DESC' (descending).
SUFFIX_POOL = ["", "DESC"]
OPCLASS_POOL = ["text_pattern_ops", "varchar_pattern_ops", "int4_ops"]


def quote_name(s):
    # concrete instantiation of the universally-quantified quoteName
    return '"%s"' % s


# --- ORACLE: faithful replica of the POST-PATCH col_str bodies ----------------
def oracle_columns(columns, col_suffixes):
    def col_str(column, idx):
        col = quote_name(column)
        try:
            suffix = col_suffixes[idx]
            if suffix:
                col = '{} {}'.format(col, suffix)
        except IndexError:
            pass
        return col
    return ', '.join(col_str(c, i) for i, c in enumerate(columns))


def oracle_index_columns(columns, col_suffixes, opclasses):
    def col_str(column, idx):
        # Index.__init__ guarantees len(opclasses) == len(columns)
        col = '{} {}'.format(quote_name(column), opclasses[idx])
        try:
            suffix = col_suffixes[idx]
            if suffix:
                col = '{} {}'.format(col, suffix)
        except IndexError:
            pass
        return col
    return ', '.join(col_str(c, i) for i, c in enumerate(columns))


# --- SHADOW of the implementation_* impl regions (the R/I legs) ---------------
def get_d(xs, idx, default=""):
    return xs[idx] if 0 <= idx < len(xs) else default


def shadow_columns(columns, col_suffixes):
    parts = []
    for idx, column in enumerate(columns):  # zipIdx
        col = quote_name(column)
        if 0 <= idx < len(col_suffixes):    # suffixes[idx]? = some
            suffix = col_suffixes[idx]
            if suffix != "":
                col = col + " " + suffix
        # else none -> unchanged
        parts.append(col)
    return ", ".join(parts)


def shadow_index_columns(columns, col_suffixes, opclasses):
    parts = []
    for idx, column in enumerate(columns):  # zipIdx
        col = quote_name(column) + " " + get_d(opclasses, idx, "")
        if 0 <= idx < len(col_suffixes):
            suffix = col_suffixes[idx]
            if suffix != "":
                col = col + " " + suffix
        parts.append(col)
    return ", ".join(parts)


def disagree_columns(columns, col_suffixes):
    got = oracle_columns(columns, col_suffixes)
    want = shadow_columns(columns, col_suffixes)
    return None if got == want else (columns, col_suffixes, got, want)


def disagree_index(columns, col_suffixes, opclasses):
    got = oracle_index_columns(columns, col_suffixes, opclasses)
    want = shadow_index_columns(columns, col_suffixes, opclasses)
    return None if got == want else (columns, col_suffixes, opclasses, got, want)


def _edge_cases():
    # (columns, col_suffixes) for the plain renderer
    plain = [
        # F2P: descending column -> "name" DESC, single space, no run-on
        (["name"], ["DESC"]),
        # F2P: ascending column -> empty suffix contributes nothing
        (["name"], [""]),
        # multiple columns, mixed order
        (["name", "pubdate"], ["", "DESC"]),
        # no suffixes at all (default ()) -> all IndexError path
        (["name", "headline"], []),
        # more suffixes than columns
        (["name"], ["DESC", "DESC"]),
        # empty column list
        ([], []),
    ]
    # (columns, col_suffixes, opclasses) for the index renderer
    index = [
        # F2P: opclass, ascending -> "(name" text_pattern_ops) no trailing space
        (["name"], [""], ["text_pattern_ops"]),
        # opclass, descending -> annotation then DESC
        (["name"], ["DESC"], ["text_pattern_ops"]),
        # two columns, mixed
        (["name", "headline"], ["", "DESC"], ["text_pattern_ops", "int4_ops"]),
        # opclasses present, col_suffixes default empty (IndexError path)
        (["name"], [], ["text_pattern_ops"]),
        ([], [], []),
    ]
    return plain, index


def main() -> int:
    checked = 0
    plain, index = _edge_cases()
    for cols, suf in plain:
        d = disagree_columns(cols, suf)
        if d:
            print(f"DISAGREE edge columns: oracle={d[2]!r} shadow={d[3]!r} "
                  f"columns={d[0]} suffixes={d[1]}")
            print("status=fail")
            return 1
        checked += 1
    for cols, suf, ops in index:
        d = disagree_index(cols, suf, ops)
        if d:
            print(f"DISAGREE edge index: oracle={d[3]!r} shadow={d[4]!r} "
                  f"columns={d[0]} suffixes={d[1]} opclasses={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        ncols = rng.randint(0, 5)
        columns = [rng.choice(NAME_POOL) for _ in range(ncols)]
        # col_suffixes length is independent of columns in the plain renderer
        nsuf = rng.randint(0, ncols + 2)
        col_suffixes = [rng.choice(SUFFIX_POOL) for _ in range(nsuf)]

        d = disagree_columns(columns, col_suffixes)
        if d:
            print(f"DISAGREE fuzz columns: oracle={d[2]!r} shadow={d[3]!r} "
                  f"columns={d[0]} suffixes={d[1]}")
            print("status=fail")
            return 1
        checked += 1

        # IndexColumns: Index.__init__ guarantees len(opclasses) == len(columns)
        opclasses = [rng.choice(OPCLASS_POOL) for _ in range(ncols)]
        d = disagree_index(columns, col_suffixes, opclasses)
        if d:
            print(f"DISAGREE fuzz index: oracle={d[3]!r} shadow={d[4]!r} "
                  f"columns={d[0]} suffixes={d[1]} opclasses={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
