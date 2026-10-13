#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_deconstruct
against the patch.diff behaviour (the POST-patch `Q.deconstruct` derivation of
`(args, kwargs)` from a node's stored components).

The impl region is all R/I content (no A-tagged op), so this runs a real fuzz.
The shadow reproduces the Lean impl's control flow op-for-op:
    args = list(children)                      -- let args := children
    kw   = {pair:None, connector:None, neg:False}
    if connector != AND: kw.connector = connector
    if negated:          kw.negated = True
    return (path, args, kw)

The patched side is an independent reconstruction of the POST-patch body's
`(args, kwargs)` derivation:
    args = tuple(self.children)
    kwargs = {}
    if self.connector != self.default: kwargs['_connector'] = self.connector
    if self.negated: kwargs['_negated'] = True

The Lean model's `Kwargs` carries explicit `pair / connector / negated` slots;
we bridge to Python's `kwargs` dict via mapping.md:
  - kw.pair        ↔ an inlined {key: val} entry (always None post-patch)
  - kw.connector   ↔ presence of '_connector'
  - kw.negated     ↔ presence of '_negated': True
We compare the bridged (args, kwargs-dict) pair. The `path` component is an
input-independent pass-through (pinned equal in the spec), so it is fixed to a
constant on both sides and not separately fuzzed.

We assert zero disagreements over >=10^5 fuzzed node inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14140          # pinned in mapping.md
N = 120_000           # >= 10^5

AND = "AND"
OR = "OR"
DEFAULT = AND
PATH = "django.db.models.Q"   # input-independent pass-through, fixed both sides


# --- child model (mapping.md type bijection) ---
# ('cond', key, val) : index-addressable length-2 lookup pair  (Child.cond)
# ('expr', label)    : standalone conditional expression, NOT subscriptable (Child.expr)
# ('nested', label)  : a nested Q node                          (Child.nested)


def shadow(children, connector, negated):
    """R/I shadow of implementation_deconstruct (post-patch control flow)."""
    args = list(children)                       # let args := children
    pair = None                                 # kw.pair stays none
    kw_connector = None
    kw_negated = False
    if connector != AND:                        # connector ≠ Connector.cAnd
        kw_connector = connector
    if negated:
        kw_negated = True
    # bridge Kwargs -> Python kwargs dict
    kwargs = {}
    if pair is not None:
        kwargs[pair[0]] = pair[1]
    if kw_connector is not None:
        kwargs["_connector"] = kw_connector
    if kw_negated:
        kwargs["_negated"] = True
    return (PATH, tuple(args), kwargs)


def patched_deconstruct(children, connector, negated):
    """Independent reconstruction of the POST-patch Q.deconstruct() body's
    (args, kwargs) derivation."""
    args = tuple(children)
    kwargs = {}
    if connector != DEFAULT:
        kwargs["_connector"] = connector
    if negated:
        kwargs["_negated"] = True
    return (PATH, args, kwargs)


def rand_children(rng):
    n = rng.randint(0, 5)
    out = []
    for _ in range(n):
        kind = rng.choice(["cond", "cond", "expr", "nested"])
        if kind == "cond":
            out.append(("cond", rng.choice(["x", "y", "price__gt", "k"]),
                        rng.choice(["1", "2", "F(d)", "v"])))
        elif kind == "expr":
            out.append(("expr", rng.choice(["Exists(q)", "RawSQL(s)", "Q?"])))
        else:
            out.append(("nested", rng.choice(["Q1", "Q2"])))
    return out


def main() -> int:
    rng = random.Random(SEED)

    # Deterministic boundary cases first (the F2P discriminators):
    #  - single cond child (was routed to kwargs pre-patch)
    #  - single expr child (Exists -> TypeError pre-patch)
    #  - negated single child; empty; multi-child; OR connector
    fixed = [
        ([], AND, False),
        ([("cond", "price__gt", "F(d)")], AND, False),     # test_deconstruct
        ([("cond", "price__gt", "F(d)")], AND, True),       # test_deconstruct_negated
        ([("expr", "Exists(tagged)")], AND, False),         # test_deconstruct_boolean_expression
        ([("expr", "Exists(tagged)")], AND, True),
        ([("nested", "Q1")], AND, False),                   # test_deconstruct_nested
        ([("cond", "x", "1"), ("cond", "y", "2")], AND, False),
        ([("cond", "x", "1")], OR, False),
        ([("cond", "x", "1"), ("cond", "x", "2")], OR, False),
        ([("expr", "Exists(q)")], OR, True),
    ]
    cases = fixed + [
        (rand_children(rng), rng.choice([AND, OR]), rng.choice([True, False]))
        for _ in range(N)
    ]

    disagreements = 0
    examples = []
    for children, connector, negated in cases:
        got = shadow(children, connector, negated)
        want = patched_deconstruct(children, connector, negated)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((children, connector, negated), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
