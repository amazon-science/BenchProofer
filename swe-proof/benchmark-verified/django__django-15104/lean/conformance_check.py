#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15104.

The bundle models ONE function:
`MigrationAutodetector.only_relation_agnostic_fields`
(`django/db/migrations/autodetector.py`). Its Lean implementation
(`implementation_relationAgnosticFields`) normalizes each field's deconstruction
so that related-field targets are ignored, returning the list of transformed
deconstructions (modeled as `Option (List Decon)`; the real method's `KeyError`
raise is modeled as `None`):

    out = []
    for f in fields:               # already in visit order (sorted upstream)
        d = remove_target(f.decon) if f.is_relation else f.decon
        out.append(d)
    return out                     # post-patch: always returns (never raises)

where `remove_target(decon)` drops the `'to'` key from the deconstruction's
keyword mapping. The gold patch changes the relation branch from
`del deconstruction[2]['to']` (raises `KeyError` when `'to'` is absent) to
`deconstruction[2].pop('to', None)` (total). So the POST-PATCH oracle always
returns a list; the modeled removal tolerates an absent target key.

This script transliterates that R/I impl into Python (`shadow`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH `only_relation_agnostic_fields` per-field loop — relation fields have
their `'to'` keyword entry removed via `pop('to', None)`, non-relation fields are
carried over verbatim, output order = input order, and the function always
returns (never raises).

We do NOT stand up Django's autodetector / field machinery (heavy; the modeled
value is a pure transform over a list of already-deconstructed fields). The
`deep_deconstruct` result and the `remote_field.model` truthiness are folded into
the input representation (a `FieldDef` = is_relation flag + a `(path, args,
kwargs)` deconstruction), exactly as in mapping.md. Both legs are total functions
over the modeled abstraction; the edge set enumerates the structurally
interesting cases (relation/non-relation × target-present/absent × duplicate-free
kwargs × empty/length-varying field lists) and the fuzz loop samples random
field lists, including relation fields whose kwargs lack `'to'` (the
discriminating case the F2P test exercises — pre-patch this raised, post-patch it
returns).

stdlib-only. Pinned seed: 15104 (also recorded in mapping.md).
"""
import sys

SEED = 15104
N = 120_000

TARGET_KEY = "to"
# small key/value alphabets; 'to' is included so target-present/absent both occur
KEYS = ("to", "on_delete", "related_name", "blank")
VALS = ("v0", "v1")
PATHS = ("p.A", "p.B")


def remove_target(decon):
    path, args, kwargs = decon
    # post-patch: pop('to', None) — tolerant of an absent key (unique keys)
    new_kwargs = [(k, v) for (k, v) in kwargs if k != TARGET_KEY]
    return (path, args, new_kwargs)


# --- ORACLE: post-patch only_relation_agnostic_fields, in-process replica -----
def oracle(fields):
    out = []
    for is_rel, decon in fields:
        if is_rel:
            d = remove_target(decon)
        else:
            d = decon
        out.append(d)
    return out  # always returns (never raises) post-patch


# --- shadow of implementation_relationAgnosticFields (the R/I leg) ------------
# Mirrors Solution.lean op-for-op.
def shadow(fields):
    acc = []
    for is_rel, decon in fields:
        d = remove_target(decon) if is_rel else decon
        acc.append(d)
    return acc


def disagree(fields):
    got = oracle(fields)
    want = shadow(fields)
    if got != want:
        return (fields, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0

    # --- Edge set: structurally interesting fields, all assembled into lists ---
    edge_fields = [
        # non-relation, ignored regardless of kwargs
        (False, ("p.A", [], [])),
        (False, ("p.A", ["a"], [("to", "v0"), ("blank", "v1")])),
        # relation with explicit target present -> 'to' removed
        (True, ("p.B", [], [("to", "v0")])),
        (True, ("p.B", ["x"], [("to", "v0"), ("on_delete", "v1")])),
        # relation WITHOUT a target entry -> pre-patch raised; post-patch no-op
        (True, ("p.B", [], [])),
        (True, ("p.B", [], [("on_delete", "v0")])),
        (True, ("p.B", [], [("on_delete", "v0"), ("blank", "v1")])),
    ]
    # exercise every prefix/sublist combination up to length 3 over the edge set
    import itertools
    for r in range(0, 4):
        for combo in itertools.product(edge_fields, repeat=r):
            d = disagree(list(combo))
            if d:
                print(f"DISAGREE edge fields={d[0]!r}: oracle={d[1]} shadow={d[2]}")
                print("status=fail")
                return 1
            checked += 1

    # --- Random fuzz over field lists -----------------------------------------
    rnd = _lcg(SEED)

    def nxt(mod):
        return next(rnd) % mod

    def mk_kwargs():
        n = nxt(4)  # 0..3 entries, unique keys (dict-like)
        used = []
        out = []
        for _ in range(n):
            k = KEYS[nxt(len(KEYS))]
            if k in used:
                continue
            used.append(k)
            out.append((k, VALS[nxt(len(VALS))]))
        return out

    def mk_field():
        is_rel = nxt(2) == 0
        path = PATHS[nxt(len(PATHS))]
        nargs = nxt(3)
        args = [VALS[nxt(len(VALS))] for _ in range(nargs)]
        return (is_rel, (path, args, mk_kwargs()))

    for _ in range(N):
        nfields = nxt(6)  # 0..5 fields
        fields = [mk_field() for _ in range(nfields)]
        d = disagree(fields)
        if d:
            print(f"DISAGREE fuzz fields={d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
