#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16595.

The bundle models ONE function: `AlterField.reduce`
(`django/db/migrations/operations/fields.py`). Its Lean implementation
(`implementation_reduceAlter`) decides how an alter-field step `self` reduces
against the operation `op` that immediately follows it, returning a list of
replacement operations (modeled as `List Op`; the real method's bool return —
"no replacement list" — is modeled as the empty list `[]`):

    if op.kind in (alterField, removeField) and same_field(self, op):
        return [op]
    if op.kind == renameField and same_field(self, op) and self.field.db_column is None:
        return [op, AlterField(model=self.model, name=op.new_name, field=self.field)]
    if self.elidable:               # Operation.reduce elidable fall-through
        return [op]
    if op.elidable:
        return [self]
    return []                       # super().reduce(...) bool case

This script transliterates that R/I impl into Python (`shadow_reduce`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `AlterField.reduce` — first arm widened to fire on
`(AlterField, RemoveField)`, the rename arm gated on `db_column is None`,
then the fall-through to `super().reduce(...)`: `FieldOperation.reduce`
delegates to `Operation.reduce`, whose elidable branches produce a replacement
LIST (`[operation]` when `self.elidable`, `[self]` when `operation.elidable`),
which short-circuits the trailing `or not operation.references_field(...)`;
only when neither step is elidable does the chain yield a bool (no
replacement list, modeled `[]`).

We do NOT stand up Django's migration framework (heavy; the modeled value is a
pure decision over the operation pair's type tags, names, elidable flags, and
the altered field's `db_column`). Both legs are total functions over the
modeled abstraction, so the edge set EXHAUSTIVELY enumerates the modeled input
space (4 op kinds × a small ASCII name alphabet exercising case-insensitive
matching × db_column present / absent × new_name choices × both elidable flags);
the fuzz loop additionally samples random points. The discriminating case —
`op.kind == alterField`, same field, neither step elidable — is therefore
covered exhaustively: oracle (post-patch) returns `[op]`, and a same-field
alter falls through to `[]` only under the PRE-patch code.

stdlib-only. Pinned seed: 16595 (also recorded in mapping.md).
"""
import itertools
import sys

SEED = 16595
N = 120_000

# Modeled operation kinds.
KINDS = ("alterField", "removeField", "renameField", "otherOp")
# ASCII identifier alphabet — mixed case to exercise the case-insensitive
# (`str.lower()` / `String.toLower`) model/field-name comparison.
NAMES = ("a", "A", "b")
DBCOLS = (None, "col")


def same_field(self_op, op):
    # self.is_same_field_operation(operation): model+field names compared lower.
    return (
        self_op["modelName"].lower() == op["modelName"].lower()
        and self_op["name"].lower() == op["name"].lower()
    )


# --- ORACLE: the post-patch AlterField.reduce, faithful in-process replica ----
def oracle_reduce(self_op, op):
    if op["kind"] in ("alterField", "removeField") and same_field(self_op, op):
        return [op]
    if (
        op["kind"] == "renameField"
        and same_field(self_op, op)
        and self_op["field"]["dbColumn"] is None
    ):
        return [
            op,
            {
                "kind": "alterField",
                "modelName": self_op["modelName"],
                "name": op["newName"],
                "newName": "",
                "elidable": False,
                "field": self_op["field"],
            },
        ]
    # super().reduce(...): FieldOperation.reduce -> Operation.reduce.
    # `if self.elidable: return [operation]` / `elif operation.elidable:
    # return [self]` — a NON-EMPTY list short-circuits the trailing
    # `or not operation.references_field(...)`.
    if self_op["elidable"]:
        return [op]
    if op["elidable"]:
        return [self_op]
    # bool case ("no replacement list produced"); modeled [].
    return []


# --- shadow of implementation_reduceAlter (the R/I leg) -----------------------
# Mirrors Solution.lean op-for-op.
def shadow_reduce(self_op, op):
    if op["kind"] in ("alterField", "removeField") and same_field(self_op, op):
        return [op]
    if (
        op["kind"] == "renameField"
        and same_field(self_op, op)
        and self_op["field"]["dbColumn"] is None
    ):
        return [
            op,
            {
                "kind": "alterField",
                "modelName": self_op["modelName"],
                "name": op["newName"],
                "newName": "",
                "elidable": False,
                "field": self_op["field"],
            },
        ]
    if self_op["elidable"]:
        return [op]
    if op["elidable"]:
        return [self_op]
    return []


def disagree(self_op, op):
    got = oracle_reduce(self_op, op)
    want = shadow_reduce(self_op, op)
    if got != want:
        return (self_op, op, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


ELIDABLES = (False, True)


def _mk_self(mn, fn, dbcol, elid=False):
    return {"kind": "alterField", "modelName": mn, "name": fn, "newName": "",
            "elidable": elid, "field": {"dbColumn": dbcol, "repr": "f"}}


def _mk_op(kind, mn, fn, nn, dbcol, elid=False):
    return {"kind": kind, "modelName": mn, "name": fn, "newName": nn,
            "elidable": elid, "field": {"dbColumn": dbcol, "repr": "g"}}


def main() -> int:
    checked = 0

    # Edge set = EXHAUSTIVE over the modeled abstraction. `self` is the
    # AlterField receiver (kind fixed); the impl never reads self.kind.
    grid = itertools.product(
        NAMES, NAMES, DBCOLS, ELIDABLES,     # self model, field, db_column, elidable
        KINDS, NAMES, NAMES, NAMES, ELIDABLES,  # op kind, model, field, new_name, elidable
    )
    for s_mn, s_fn, s_db, s_el, o_kind, o_mn, o_fn, o_nn, o_el in grid:
        self_op = _mk_self(s_mn, s_fn, s_db, s_el)
        op = _mk_op(o_kind, o_mn, o_fn, o_nn, None, o_el)
        d = disagree(self_op, op)
        if d:
            print(f"DISAGREE exhaustive self={d[0]!r} op={d[1]!r}: "
                  f"oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    # Redundant random fuzz over a wider name alphabet.
    rnd = _lcg(SEED)
    alpha = ("a", "A", "b", "B", "name", "Name", "title")
    for _ in range(N):
        def pick(seq):
            return seq[next(rnd) % len(seq)]
        self_op = _mk_self(pick(alpha), pick(alpha), pick(DBCOLS),
                           pick(ELIDABLES))
        op = _mk_op(pick(KINDS), pick(alpha), pick(alpha), pick(alpha),
                    pick(DBCOLS), pick(ELIDABLES))
        d = disagree(self_op, op)
        if d:
            print(f"DISAGREE fuzz self={d[0]!r} op={d[1]!r}: "
                  f"oracle={d[2]} shadow={d[3]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
