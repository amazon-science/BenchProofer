#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-23299.

The bundle consumes NO axioms. Its single kind-A obligation is an A-reference:
the deep model `updateDict` (Solution.lean `pure` region) must equal the REAL
builtin mapping overlay that the gold patch uses —

    dict.update(rcParams, orig)      # "Revert to the original rcs."

i.e. overlaying a saved mapping `saved` onto a current mapping `current`:
every key in `saved` takes its `saved` value; keys only in `current` are kept.

Solution.lean models that as
    updateDict current saved = saved ++ current.filter(key not in saved)
(as a key->value mapping, `saved` bindings win). G-AX runs the REAL builtin
`dict.update` on boundary + fuzz inputs and asserts the deep model agrees, as a
KEY->VALUE MAPPING (order is not observable through dict semantics, which is the
level the model claims equality at — directive 7: no double-masking).

It also checks the I op `eraseKey` against the real `del`/comprehension drop
the patch performs (`del orig['backend']`).

Imports nothing repo-specific: `dict.update` / `del` are Python builtins — the
exact operations the gold patch calls. Exit 0 iff every obligation holds.
"""
import random
import sys

BACKEND = "backend"


# --- model.py reference encodings (kept in lock-step with Solution.lean) ------

def lookup_key(saved, name):
    for k, v in saved:
        if k == name:
            return v
    return None


def update_dict_model(current, saved):
    """Deep model `updateDict` as an assoc list: saved ++ current-keys-not-in-saved.
    Returned as a dict (the observable mapping the patch's dict.update yields)."""
    saved_keys = {k for k, _ in saved}
    out = list(saved) + [(k, v) for (k, v) in current if k not in saved_keys]
    # assoc list -> mapping (first binding wins; inputs have unique keys)
    d = {}
    for k, v in out:
        d.setdefault(k, v)
    return d


def erase_key_model(d_items, name):
    """Deep model `eraseKey`: drop every binding for `name`."""
    return [(k, v) for (k, v) in d_items if k != name]


# --- the checks --------------------------------------------------------------

def check_update_reference(current, saved):
    """Assert updateDict deep model == the REAL builtin dict.update overlay."""
    # real callee: dict.update(current, saved) mutates `current` in place.
    real = dict(current)
    dict.update(real, dict(saved))                    # real builtin overlay
    model = update_dict_model(current, saved)         # deep model
    assert real == model, (
        "updateDict deep model unsound: current=%r saved=%r real=%r model=%r"
        % (current, saved, real, model))


def check_erase_reference(items, name):
    """Assert eraseKey deep model == the real `del key` drop."""
    real = dict(items)
    if name in real:
        del real[name]                                 # real builtin del
    model = dict(erase_key_model(items, name))
    assert real == model, (
        "eraseKey deep model unsound: items=%r name=%r real=%r model=%r"
        % (items, name, real, model))


def main():
    keys = [BACKEND, "interactive", "figure.dpi", "lines.linewidth",
            "axes.grid", "font.size", "savefig.format", "toolbar", "x", "y"]
    vals = ["module://aardvark", "Agg", "QtAgg", "TkAgg", "0", "1", "100",
            "true", "false", "png", "pdf", "", "x", "Y"]

    # --- boundary cases -------------------------------------------------------
    boundary = [
        ([], []),
        ([(BACKEND, "Agg")], [(BACKEND, "QtAgg")]),
        ([(BACKEND, "module://aardvark")], [(BACKEND, "Agg")]),
        ([(BACKEND, "Z"), ("font.size", "99")],
         [(BACKEND, "Agg"), ("font.size", "12")]),
        ([("a", "1"), ("b", "2")], [("b", "3"), ("c", "4")]),     # disjoint + overlap
        ([("only.current", "v")], []),                             # saved empty
        ([], [("only.saved", "v")]),                               # current empty
        ([("x", "")], [("x", "y")]),                               # empty value
    ]
    for current, saved in boundary:
        check_update_reference(current, saved)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(23299)
    for _ in range(20000):
        ck = rng.sample(keys, rng.randint(0, len(keys)))
        sk = rng.sample(keys, rng.randint(0, len(keys)))
        current = [(k, rng.choice(vals)) for k in ck]
        saved = [(k, rng.choice(vals)) for k in sk]
        check_update_reference(current, saved)

    # --- eraseKey I op: drop 'backend' (and other keys) -----------------------
    for current, saved in boundary:
        check_erase_reference(saved, BACKEND)
        check_erase_reference(current, BACKEND)
    for _ in range(5000):
        sk = rng.sample(keys, rng.randint(0, len(keys)))
        items = [(k, rng.choice(vals)) for k in sk]
        check_erase_reference(items, rng.choice(keys))

    # --- end-to-end: patched restore keeps body 'backend', reverts the rest ---
    # saved = entry snapshot; current = mapping at restore time.
    for _ in range(5000):
        sk = [BACKEND] + rng.sample(keys[1:], rng.randint(0, len(keys) - 1))
        saved = [(k, rng.choice(vals)) for k in sk]
        current = [(k, rng.choice(vals)) for k in sk]
        # model restore: updateDict(current, eraseKey(saved, backend))
        restore_src = erase_key_model(saved, BACKEND)
        model_restore = update_dict_model(current, restore_src)
        # real restore (gold patch finally block):
        real_restore = dict(current)
        orig = dict(saved)
        del orig[BACKEND]
        dict.update(real_restore, orig)
        assert model_restore == real_restore, (
            "restore model/real mismatch: current=%r saved=%r model=%r real=%r"
            % (current, saved, model_restore, real_restore))
        # the designated key must equal its CURRENT value, not the saved one
        assert model_restore[BACKEND] == dict(current)[BACKEND]

    print("G-AX OK: updateDict deep model (== builtin dict.update overlay) and "
          "eraseKey (== builtin del) sound on %d boundary + 30000 fuzz cases; "
          "patched restore preserves the designated 'backend' key." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
