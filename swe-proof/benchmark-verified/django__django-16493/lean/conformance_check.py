#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_recordedStorage
against the patch.diff behaviour (post-patch storage-kwarg decision in
FileField.deconstruct).

The impl region is all R/I (no A-tagged op), so this runs a real fuzz. The shadow
reproduces the impl op-for-op: compute the original reference
(`getattr(self, "_storage_callable", self.storage)` = the callable when present,
else the evaluated instance), then record it iff it differs by identity from the
default. We diff that against an independent reconstruction of the post-patch
`deconstruct` decision driven by real object-identity (`is`) semantics over Python
objects standing in for the storage instances.

Object identities are modeled as small ints in the Lean spec; here we use real
distinct Python objects and the real `is` operator, then map the chosen object
back to its identity int for comparison with the shadow. Zero disagreements
required over >=10^5 fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 16493          # pinned in mapping.md
N = 120_000           # >= 10^5


class Obj:
    """A stand-in storage object; identity is what matters (`is`)."""
    __slots__ = ("ident",)

    def __init__(self, ident):
        self.ident = ident


def shadow(original_callable, evaluated_storage, default_storage):
    """R/I shadow of implementation_recordedStorage, over identity ints.

    original_callable: int | None ; evaluated_storage, default_storage: int.
    Returns int | None (the recorded identity, or None for 'key absent').
    """
    storage = original_callable if original_callable is not None else evaluated_storage
    result = None
    if storage != default_storage:
        result = storage
    return result


def patched_deconstruct(has_callable, callable_obj, evaluated_obj, default_obj):
    """Independent reconstruction of the post-patch decision using REAL `is`.

    has_callable: bool — whether `_storage_callable` is set.
    Returns the recorded object (by identity) or None.
    """
    # getattr(self, "_storage_callable", self.storage)
    storage = callable_obj if has_callable else evaluated_obj
    recorded = None
    if storage is not default_obj:
        recorded = storage
    return recorded


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    default = Obj(0)

    def fresh_or_default(p_default):
        """Return an Obj that is `default` with prob p_default, else a fresh one."""
        if rng.random() < p_default:
            return default
        return Obj(rng.randint(1, 10_000))

    # Deterministic boundary cases first, incl. the exact F2P shape.
    # Each: (has_callable, callable_is_default, evaluated_is_default)
    fixed = [
        # F2P: a non-default callable that EVALUATES to the default instance.
        (True, False, True),
        # callable that is itself the default object (edge): dropped both ways.
        (True, True, True),
        # callable distinct from default, evaluating to a non-default instance.
        (True, False, False),
        # no callable; evaluated == default  -> dropped.
        (False, False, True),
        # no callable; evaluated != default  -> recorded.
        (False, False, False),
    ]

    cases = []
    for has_callable, c_def, e_def in fixed:
        cases.append((has_callable, c_def, e_def))
    for _ in range(N):
        has_callable = rng.random() < 0.5
        # oversample the discriminating combos (callable != default, evaluated == default)
        c_def = rng.random() < 0.3
        e_def = rng.random() < 0.5
        cases.append((has_callable, c_def, e_def))

    for has_callable, c_def, e_def in cases:
        callable_obj = default if c_def else Obj(rng.randint(1, 10_000))
        evaluated_obj = default if e_def else Obj(rng.randint(1, 10_000))

        # Real-`is` reference.
        recorded = patched_deconstruct(has_callable, callable_obj, evaluated_obj, default)
        want = None if recorded is None else recorded.ident

        # Shadow over identity ints.
        original_callable = callable_obj.ident if has_callable else None
        got = shadow(original_callable, evaluated_obj.ident, default.ident)

        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((has_callable, c_def, e_def), got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, g, w in examples:
            print(f"  in={inp!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
