#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12050 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `resolveSeq` impl region
              transliterated to Python over the *real* repo carrier. The impl
              constructs a fresh sequence whose KIND equals the input kind and
              whose ELEMENTS are the per-element resolution of the input
              elements, in order. The kind is the discriminating observable the
              fix changed (list stays list, tuple stays tuple); the per-element
              map is the A-reference `resolveElem` (left as identity here — it
              is the unchanged element step, out of scope for the R/I diff,
              validated separately as an A-reference; see mapping.md §3).
  * ORACLE  — `patch.diff`'s behaviour: the patched reassembly
              `type(value)(... for sub_value in value)`. For a `list` input it
              returns a `list`; for a `tuple` input it returns a `tuple` — the
              container TYPE is preserved. We exercise the REAL construction
              `type(value)(gen)` in-process (it needs no Django / DB), so the
              oracle is the actual Python the patch ships.

They must agree on every input: the SHADOW's kind observable must equal whether
the ORACLE's rebuilt container is a list (vs a tuple). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

stdlib-only. The fuzz seed is pinned (mapping.md §4) for a deterministic
verdict. No Django import, no DB, no Docker required.
"""
import random
import sys

SEED = 12050
N_FUZZ = 100_000


# --- the per-element resolution (A-reference, identity for the R/I diff) -----
def resolve_elem(x):
    """The unchanged per-element resolve_expression step. Modeled opaquely in
    Solution.lean (`opaque resolveElem`); for the R/I shadow it is the identity
    on the abstract element — its concrete result is never pinned. It is the
    SAME map applied to every element on both sides, so it cancels in the diff
    and the discriminating observable is purely the container kind."""
    return x


# --- SHADOW: Solution.lean resolveSeq, transliterated ------------------------
# Solution.lean models the input as a (kind, elems) carrier and returns
# {kind := value.kind, elems := value.elems.map resolveElem}. The bijection
# (mapping.md §2): SeqKind.list ↔ python list, SeqKind.tuple ↔ python tuple.
def shadow_resolve_kind(input_is_list):
    """out.kind = value.kind — the kind is preserved. Returns True iff the
    modeled output kind is `list` (SeqKind.list)."""
    return input_is_list  # kind is copied straight through


def shadow_resolve_elems(elems):
    """out.elems = value.elems.map resolveElem — order-preserving element map."""
    return [resolve_elem(x) for x in elems]


# --- ORACLE: patch.diff's behaviour, the real `type(value)(...)` rebuild ------
def oracle_rebuild(value):
    """The patched reassembly:

        return type(value)(
            self.resolve_lookup_value(sub_value, ...) for sub_value in value
        )

    where the recursive sub-call on a scalar sub_value returns it resolved (here
    the per-element map `resolve_elem`). `type(value)(gen)` preserves the
    container type: list -> list, tuple -> tuple. This is the actual Python the
    gold patch ships; it needs neither Django nor a DB."""
    return type(value)(resolve_elem(sub_value) for sub_value in value)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield []
    yield ()
    yield [0]
    yield (0,)
    yield [1, 2, 3]
    yield (1, 2, 3)
    yield list(range(50))
    yield tuple(range(50))
    yield [-1, -2, -3]
    yield (-1,)
    for _ in range(n):
        k = rng.randint(0, 24)
        elems = [rng.randint(-1000, 1000) for _ in range(k)]
        # vary list vs tuple inputs
        if rng.random() < 0.5:
            yield elems
        else:
            yield tuple(elems)


def main():
    rng = random.Random(SEED)
    fails = 0
    checked = 0
    for value in fuzz_inputs(N_FUZZ, rng):
        input_is_list = isinstance(value, list)
        rebuilt = oracle_rebuild(value)

        # 1) kind preservation: shadow's kind == (oracle rebuild is a list)
        oracle_is_list = isinstance(rebuilt, list)
        shadow_is_list = shadow_resolve_kind(input_is_list)
        if shadow_is_list != oracle_is_list:
            fails += 1
            if fails <= 10:
                print(f"KIND DISAGREE: input_is_list={input_is_list} "
                      f"shadow_list={shadow_is_list} oracle_list={oracle_is_list} "
                      f"value={value!r} rebuilt={rebuilt!r}", file=sys.stderr)

        # 2) element map: shadow's elems == oracle rebuilt elems (in order)
        shadow_elems = shadow_resolve_elems(list(value))
        oracle_elems = list(rebuilt)
        if shadow_elems != oracle_elems:
            fails += 1
            if fails <= 10:
                print(f"ELEM DISAGREE: value={value!r} shadow={shadow_elems} "
                      f"oracle={oracle_elems}", file=sys.stderr)
        checked += 1

    if fails:
        print(f"G-CONF FAIL: {fails} disagreement(s) over {checked} inputs "
              f"(seed {SEED}).", file=sys.stderr)
        return 1
    print(f"G-CONF PASS: {checked} inputs, 0 disagreements "
          f"(seed {SEED}). list->list, tuple->tuple type preservation; "
          f"order-preserving element map.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
