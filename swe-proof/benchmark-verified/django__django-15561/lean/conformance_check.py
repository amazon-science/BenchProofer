#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15561.

The bundle models ONE function:
`BaseDatabaseSchemaEditor._field_should_be_altered(self, old_field, new_field)`
(`django/db/backends/base/schema.py`). It returns a bool: whether altering
`old_field` into `new_field` requires a column-level schema change. The Lean
implementation (`implementation_requiresColumnChange`) transliterates the
post-patch body:

    old_kwargs = dict(old.kwargs); new_kwargs = dict(new.kwargs)
    for attr in IGNORED: old_kwargs.pop(attr, None)
    for attr in IGNORED: new_kwargs.pop(attr, None)
    return quote(old.column) != quote(new.column) or \
           (old.path, old.args, old_kwargs) != (new.path, new.args, new_kwargs)

where IGNORED is the post-patch `Field.non_db_attrs` tuple (it INCLUDES
"choices").

This script builds the R/I shadow of the impl in Python (`shadow`) and
differential-tests it against an ORACLE: a faithful in-process replica of the
POST-PATCH `_field_should_be_altered` decision (IGNORED includes "choices",
both kwargs dicts popped). We do NOT stand up Django's schema framework (heavy;
the modeled value is a pure decision over the two field descriptions). `column`
quoting is the unchanged callee `quote_name`, replicated identically in oracle
and shadow (SQLite quoting), so no property of it is assumed.

Both legs are total functions over the modeled abstraction; the edge set
EXHAUSTIVELY enumerates a structured grid (column equal/changed × path
equal/changed × args equal/changed × kwargs differing only on an IGNORED attr
("choices" / "verbose_name") vs a column-relevant attr ("max_length")), and the
fuzz loop additionally samples random field-description pairs. The discriminating
case — descriptions that differ ONLY in the "choices" kwarg, same column/path/
args — is covered: oracle returns False (post-patch noop), and the pre-patch
code (IGNORED without "choices") would return True.

stdlib-only. Pinned seed: 15561 (also recorded in mapping.md).
"""
import itertools
import sys

SEED = 15561
N = 120_000

# Post-patch ignored-attribute set (Field.non_db_attrs) — INCLUDES "choices".
IGNORED = (
    "blank", "choices", "db_column", "editable", "error_messages", "help_text",
    "limit_choices_to", "on_delete", "related_name", "related_query_name",
    "validators", "verbose_name",
)


def quote_name(name):
    # Faithful SQLite quote_name replica (unchanged callee, identical both sides).
    return '"%s"' % name.replace('"', '""')


def _pop(kwargs):
    return [(k, v) for (k, v) in kwargs if k not in IGNORED]


# --- ORACLE: post-patch _field_should_be_altered, faithful in-process replica --
def oracle(old, new):
    old_k = _pop(old["kwargs"])
    new_k = _pop(new["kwargs"])
    return quote_name(old["column"]) != quote_name(new["column"]) or (
        (old["path"], old["args"], old_k) != (new["path"], new["args"], new_k)
    )


# --- shadow of implementation_requiresColumnChange (the R/I leg) --------------
# Mirrors Solution.lean op-for-op.
def shadow(old, new):
    old_k = list(old["kwargs"])
    new_k = list(new["kwargs"])
    for attr in IGNORED:
        old_k = [(k, v) for (k, v) in old_k if k != attr]
    for attr in IGNORED:
        new_k = [(k, v) for (k, v) in new_k if k != attr]
    return quote_name(old["column"]) != quote_name(new["column"]) or (
        (old["path"], old["args"], old_k) != (new["path"], new["args"], new_k)
    )


def disagree(old, new):
    g = oracle(old, new)
    w = shadow(old, new)
    if g != w:
        return (old, new, g, w)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _fd(col, path, args, kwargs):
    return {"column": col, "path": path, "args": list(args), "kwargs": list(kwargs)}


def main() -> int:
    checked = 0

    COLS = ("name", "fullname")
    PATHS = ("CharField", "IntegerField")
    ARGSETS = ([], ["255"])
    # kwargs variants exercising: column-relevant attr, ignored attrs incl the
    # FIXED one ("choices"), and combinations.
    KWSETS = (
        [],
        [("max_length", "255")],
        [("max_length", "255"), ("choices", "((Jane,Jane),(Joe,Joe))")],
        [("max_length", "255"), ("verbose_name", "Name")],
        [("choices", "A")],
        [("max_length", "200")],
    )

    grid = itertools.product(
        COLS, PATHS, ARGSETS, KWSETS,   # old
        COLS, PATHS, ARGSETS, KWSETS,   # new
    )
    for o_col, o_p, o_a, o_kw, n_col, n_p, n_a, n_kw in grid:
        old = _fd(o_col, o_p, o_a, o_kw)
        new = _fd(n_col, n_p, n_a, n_kw)
        d = disagree(old, new)
        if d:
            print(f"DISAGREE exhaustive old={d[0]!r} new={d[1]!r}: "
                  f"oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    # Redundant random fuzz over a wider alphabet of attrs/values.
    rnd = _lcg(SEED)
    cols = ("name", "fullname", "title", "x")
    paths = ("CharField", "IntegerField", "TextField")
    attrs = ("max_length", "choices", "verbose_name", "blank", "help_text", "null")
    vals = ("255", "200", "A", "B", "True", "False", "Name", "")

    def pick(seq):
        return seq[next(rnd) % len(seq)]

    for _ in range(N):
        def mk():
            nkw = next(rnd) % 4
            kw = []
            for _i in range(nkw):
                kw.append((pick(attrs), pick(vals)))
            return _fd(pick(cols), pick(paths),
                       [] if next(rnd) % 2 else [pick(vals)], kw)
        old, new = mk(), mk()
        d = disagree(old, new)
        if d:
            print(f"DISAGREE fuzz old={d[0]!r} new={d[1]!r}: "
                  f"oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
