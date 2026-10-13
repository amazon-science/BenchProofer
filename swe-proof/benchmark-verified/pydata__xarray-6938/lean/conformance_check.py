#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_toIndexVariable
against the patch.diff behaviour (post-patch `IndexVariable.to_index_variable`
returning an independent object via `self.copy()`).

The impl region is all R/I (no A-tagged op): the copy semantics are modeled
deeply, not abstracted behind an axiom. So this runs a real fuzz.

* `shadow(...)` reproduces the Lean impl op-for-op on the heap model:
  read the source record, allocate a fresh slot (handle = old size) holding a
  duplicate, return (grown heap, handle).
* `reference(...)` independently reconstructs the post-patch Python behaviour
  using REAL object identity / aliasing: a list of mutable objects standing in
  for the live `Variable` universe, `to_index_variable` performing `copy()`
  (a structural duplicate that is a new object), and then exercising the exact
  property the F2P test asserts — `a is not b`, and mutating the produced
  object's `dims` leaves the source's `dims` unchanged.

We diff the two on: produced handle (freshness), heap growth, produced-object
contents, frame (all pre-existing objects unchanged), and the F2P
post-mutation independence invariant. Zero disagreements required over >=10^5
fuzzed inputs.

stdlib-only. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 6938           # pinned in mapping.md
N = 120_000           # >= 10^5


# ---- the heap-model shadow of implementation_toIndexVariable -----------------

def shadow(heap, src):
    """R/I shadow of the Lean impl. `heap` is a list of (dims, data) tuples;
    `src` a valid index. Returns (new_heap, handle)."""
    h = list(heap)
    fresh = h[src]            # h[src]! — duplicate the source record
    handle = len(h)           # identity of produced object: a fresh slot
    h.append(fresh)           # allocate the produced object independently
    return h, handle


# ---- independent reconstruction of the post-patch Python semantics -----------

class _Obj:
    """Stand-in for a live Variable/IndexVariable object: a mutable record with
    real Python object identity."""
    __slots__ = ("dims", "data")

    def __init__(self, dims, data):
        self.dims = list(dims)
        self.data = data


def _to_index_variable_patched(obj):
    """post-patch `return self.copy()` — a structural duplicate (same fields),
    a DIFFERENT object."""
    return _Obj(obj.dims, obj.data)


def reference(heap, src):
    """Build the real-object universe, run the patched conversion, and read back
    the heap-model observations (handle, size, contents, frame), PLUS the F2P
    independence property. Returns a dict of observations."""
    objs = [_Obj(d, v) for (d, v) in heap]
    produced = _to_index_variable_patched(objs[src])

    # Identity model: append the produced object; its handle is its index.
    universe = objs + [produced]
    handle = len(objs)

    # F2P invariant: mutate the produced object's dims in place, then confirm
    # the source object is untouched (this is exactly test_to_index_variable_copy).
    src_dims_before = list(objs[src].dims)
    produced.dims = produced.dims + [9_999]      # b.dims = (...) ; in-place edit
    f2p_source_unchanged = (objs[src].dims == src_dims_before)
    f2p_distinct_object = (produced is not objs[src])
    # undo the mutation so the recorded contents reflect the freshly-copied state
    produced.dims = list(heap[src][0])

    return {
        "handle": handle,
        "size": len(universe),
        "produced": (tuple(universe[handle].dims), universe[handle].data),
        "frame": [(tuple(universe[i].dims), universe[i].data) for i in range(len(objs))],
        "f2p_source_unchanged": f2p_source_unchanged,
        "f2p_distinct_object": f2p_distinct_object,
    }


def observe_shadow(heap, src):
    h, handle = shadow(heap, src)
    return {
        "handle": handle,
        "size": len(h),
        "produced": h[handle],
        "frame": [h[i] for i in range(len(heap))],
    }


def rand_heap(rng, n):
    heap = []
    for _ in range(n):
        dims = tuple(rng.randint(0, 50) for _ in range(rng.randint(0, 4)))
        data = rng.randint(0, 1000)
        heap.append((dims, data))
    return heap


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first (incl. F2P-shaped single-object heap).
    fixed = [
        ([(("x",) if False else (0,), 7)], 0),   # single object, src=0 (F2P shape)
        ([((0,), 1), ((1,), 2)], 0),
        ([((0,), 1), ((1,), 2)], 1),
        ([((), 0)], 0),                          # empty dims
        ([((5, 6, 7), 3), ((8,), 4), ((), 9)], 2),
    ]
    cases = list(fixed)
    for _ in range(N):
        size = rng.randint(1, 8)
        heap = rand_heap(rng, size)
        src = rng.randint(0, size - 1)
        cases.append((heap, src))

    for heap, src in cases:
        ref = reference(heap, src)
        sh = observe_shadow(heap, src)
        ok = (
            sh["handle"] == ref["handle"] == len(heap) and       # freshness
            sh["size"] == ref["size"] == len(heap) + 1 and       # growth
            sh["produced"] == ref["produced"] and                # contents
            sh["produced"] == heap[src] and                      # contents == source
            sh["frame"] == ref["frame"] == list(heap) and        # frame intact
            ref["f2p_distinct_object"] and                       # a is not b
            ref["f2p_source_unchanged"]                          # mutation independence
        )
        if not ok:
            disagreements += 1
            if len(examples) < 10:
                examples.append(((heap, src), sh, ref))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for inp, s, r in examples:
            print(f"  in={inp!r}\n    shadow={s!r}\n    ref={r!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
