#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13786.

Executes the REAL Python language primitives the gold patch composes and
asserts that every observation matches the model's axioms (model.py axioms
region). Both are unchanged language primitives -- the NEW logic of the gold
patch (deciding WHICH managed keys to clear) is modelled deeply in the impl and
is NOT axiomatised.

  (A-consumed) merge_options(a, b) == the dict-display merge {**a, **b}
      (PEP 448 unpacking, CPython BUILD_MAP/DICT_UPDATE), which is exactly the
      gold patch's `options = {**self.options, **operation.options}`.
      Checked obligations (the axiom's Ensures):
        - the result is a FRESH object (neither a nor b is mutated);
        - b's value wins where b carries the name;
        - a's value carries where a has the name and b does not;
        - the result holds no name outside a's and b's names.

  (A-consumed) without_key(d, k) == the residue {kk: vv for kk, vv in d.items()
      if kk != k}, the value of d after the gold patch's `options.pop(k, None)`
      (which removes k if present and is a no-op otherwise). The model treats
      it functionally (a fresh residue mapping); the in-place pop in the gold
      patch yields the same key/value contents.
      Checked obligations (the axiom's Ensures):
        - k is absent from the result;
        - every other name of d is carried through with its value;
        - the result introduces no name d did not have (and changes no value).

Together these primitives, composed by the impl's deep clearing logic, equal the
gold patch's `options = {**self.options, **operation.options}; for key in
ALTER_OPTION_KEYS: if key not in operation.options: options.pop(key, None)`.

Imports nothing repo-specific: dict-display merge and dict.pop are pure Python
language primitives (the very constructs the gold patch calls). Exit 0 iff every
obligation holds.
"""
import random
import sys


# --- the REAL language primitives under check --------------------------------

def real_merge(a, b):
    """The exact construction the gold patch uses for the merged options."""
    return {**a, **b}


def real_without_key(d, k):
    """The residue of d after `d.pop(k, None)` (the gold patch's clearing step),
    expressed as a fresh mapping with k removed -- the model's functional view."""
    r = dict(d)
    r.pop(k, None)
    return r


# --- the checks --------------------------------------------------------------

def check_merge(a, b):
    snap_a, snap_b = dict(a), dict(b)
    result = real_merge(a, b)
    assert a == snap_a, "merge_options unsound: a mutated %r -> %r" % (snap_a, a)
    assert b == snap_b, "merge_options unsound: b mutated %r -> %r" % (snap_b, b)
    assert result is not a and result is not b, (
        "merge_options unsound: result is not fresh")
    # b wins where b carries the name
    for k, v in snap_b.items():
        assert k in result and result[k] == v, (
            "merge_options unsound: b key %r=%r not winning in %r" % (k, v, result))
    # a's value carries where a has it and b does not
    for k, v in snap_a.items():
        if k not in snap_b:
            assert k in result and result[k] == v, (
                "merge_options unsound: a key %r=%r lost in %r" % (k, v, result))
    # no name outside a ∪ b
    for k in result:
        assert k in snap_a or k in snap_b, (
            "merge_options unsound: spurious key %r in %r" % (k, result))


def check_without_key(d, k):
    snap = dict(d)
    result = real_without_key(d, k)
    assert d == snap, "without_key unsound: d mutated %r -> %r" % (snap, d)
    assert result is not d, "without_key unsound: result is not fresh"
    # k is gone
    assert k not in result, "without_key unsound: removed key %r still in %r" % (k, result)
    # every other name carried with its value
    for j, v in snap.items():
        if j != k:
            assert j in result and result[j] == v, (
                "without_key unsound: key %r=%r lost in %r" % (j, v, result))
    # no spurious / changed name
    for j in result:
        assert j != k and j in snap and result[j] == snap[j], (
            "without_key unsound: spurious/changed key %r in %r" % (j, result))


# --- the COMPOSITION: the whole gold reduce-options computation ---------------
# The model composes merge_options + (clear managed keys not in op). This mirror
# of the gold computation is checked against a direct reimplementation so the
# A-consumed axioms, composed by the deep clearing logic, equal the gold.

ALTER_OPTION_KEYS = [
    "base_manager_name", "default_manager_name", "default_related_name",
    "get_latest_by", "managed", "ordering", "permissions",
    "default_permissions", "select_on_save", "verbose_name",
    "verbose_name_plural",
]


def gold_reduce_options(self_options, operation_options):
    """The gold patch's exact computation."""
    options = {**self_options, **operation_options}
    for key in ALTER_OPTION_KEYS:
        if key not in operation_options:
            options.pop(key, None)
    return options


def model_reduce_options(self_options, operation_options):
    """The model's composition: merge, then drop each managed key not in op."""
    options = real_merge(self_options, operation_options)
    for key in ALTER_OPTION_KEYS:
        if key not in operation_options:
            options = real_without_key(options, key)
    return options


def check_composition(self_options, operation_options):
    assert gold_reduce_options(self_options, operation_options) == \
        model_reduce_options(self_options, operation_options), (
            "composition mismatch for self=%r op=%r" % (self_options, operation_options))


def main():
    # --- boundary cases (the F2P scenarios) -------------------------------
    # F2P case 1: CreateModel(options={'verbose_name': 'My Model'}) + AlterModel
    # Options(options={}) -> CreateModel() with NO options (verbose_name cleared)
    f2p1_self = {"verbose_name": "My Model"}
    f2p1_op = {}
    assert gold_reduce_options(f2p1_self, f2p1_op) == {}, "F2P1 expectation"
    # F2P case 2: self has verbose_name + verbose_name_plural; op provides only
    # verbose_name -> result keeps verbose_name, clears verbose_name_plural.
    f2p2_self = {"verbose_name": "My Model", "verbose_name_plural": "My Model plural"}
    f2p2_op = {"verbose_name": "My Model"}
    assert gold_reduce_options(f2p2_self, f2p2_op) == {"verbose_name": "My Model"}, "F2P2 expectation"

    boundary_pairs = [
        (f2p1_self, f2p1_op),
        (f2p2_self, f2p2_op),
        ({}, {}),
        ({"verbose_name": "X"}, {"verbose_name": "Y"}),         # op value wins
        ({"verbose_name": "X"}, {"ordering": ["a"]}),           # clear vn, set ordering
        ({"proxy": True}, {}),                                  # non-managed survives
        ({"proxy": True, "verbose_name": "X"}, {}),             # managed cleared, other kept
        ({"managed": False, "ordering": ["a"]}, {"managed": True}),
        ({k: i for i, k in enumerate(ALTER_OPTION_KEYS)}, {}),  # all managed -> cleared
        ({k: i for i, k in enumerate(ALTER_OPTION_KEYS)},
         {ALTER_OPTION_KEYS[0]: 99}),                           # one provided, rest cleared
    ]
    for a, b in boundary_pairs:
        check_merge(a, b)
        check_composition(a, b)
    for d in [p[0] for p in boundary_pairs] + [p[1] for p in boundary_pairs]:
        for k in list(d.keys()) + ["verbose_name", "proxy", "nonexistent"]:
            check_without_key(d, k)

    # --- integer-keyed carrier (the model's Dict[int, int]) ---------------
    # 0,1 == key_managed_a/b (managed); 2 == key_other (non-managed). Exercise
    # the pointwise behaviours the model pins.
    int_pairs = [
        ({}, {}),
        ({0: 7}, {}),                 # managed in self, not op -> cleared
        ({0: 7}, {0: 9}),             # managed provided -> op wins
        ({1: 7}, {}),                 # second managed cleared
        ({2: 7}, {}),                 # other in self, not op -> kept
        ({0: 7, 1: 8, 2: 9}, {0: 1}), # mixed
        ({0: 7, 1: 8, 2: 9}, {2: 1}),
    ]
    MANAGED_INT = [0, 1]

    def gold_int(self_o, op):
        o = {**self_o, **op}
        for key in MANAGED_INT:
            if key not in op:
                o.pop(key, None)
        return o

    def model_int(self_o, op):
        o = real_merge(self_o, op)
        for key in MANAGED_INT:
            if key not in op:
                o = real_without_key(o, key)
        return o

    for a, b in int_pairs:
        check_merge(a, b)
        assert gold_int(a, b) == model_int(a, b), "int composition mismatch %r %r" % (a, b)
        for k in [0, 1, 2, 3]:
            check_without_key({**a, **b}, k)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(13786)
    all_keys = ALTER_OPTION_KEYS + ["proxy", "indexes", "constraints", "app_label", "db_table"]
    for _ in range(20000):
        na = rng.randint(0, 8)
        nb = rng.randint(0, 8)
        a = {rng.choice(all_keys): rng.randint(0, 5) for _ in range(na)}
        b = {rng.choice(all_keys): rng.randint(0, 5) for _ in range(nb)}
        check_merge(a, b)
        check_composition(a, b)
        for k in rng.sample(all_keys, k=min(3, len(all_keys))):
            check_without_key({**a, **b}, k)

    print("G-AX OK: merge_options / without_key axioms sound against the real "
          "dict-display merge and dict.pop residue; their composition equals the "
          "gold reduce-options computation on the 2 F2P scenarios + %d boundary "
          "pairs + int-carrier cases + 20000 fuzz pairs (inputs never mutated; "
          "results always fresh)" % len(boundary_pairs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
