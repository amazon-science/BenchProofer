#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-22865.

There is NO consumed `@ContractOnly` axiom in this bundle: the changed
behaviour (which contiguous run of candidate separators is drawn) is modelled
DEEPLY in model.py — the pure `start_index` / `end_index` helpers plus the
verified copy loop that materialises `segments[start:end]`.  G-AX validates
that deep model against the REAL behaviour it stands in for:

  (A-reference 1)  the start/end offset selection.  The real code computes
        start_idx = 0 if self._extend_lower() else 1
        end_idx   = len(X) if self._extend_upper() else -1
  where the two unchanged predicates are
        _extend_lower():  extend in ('both', 'min'/'max' by inversion)
        _extend_upper():  extend in ('both', 'max'/'min' by inversion)
  We reproduce those predicates verbatim from the repo and assert the deep
  model's `start_index(extend_lower)` / `end_index(extend_upper, n)` give the
  exact same kept-run bounds (after normalising the real code's `-1` upper
  bound to `n-1`, which Python/numpy basic slicing treats identically when the
  array has length n).

  (A-reference 2)  the slice materialisation.  The real code keeps
        np.dstack([X, Y])[start_idx:end_idx]
  i.e. basic slicing along the first axis of an (n, 2, 2) array.  Element i of
  that array is fully identified by its mesh-row position, so we model the
  array as a list of distinct position ids and assert the deep model's kept run
  (`drawn_separators` reference) equals the real basic slice `S[start_idx:end_idx]`.

Imports nothing repo-specific and nothing beyond the standard library; the
slicing semantics exercised here are exactly Python/numpy basic first-axis
slicing.  Exit 0 iff every observation matches the deep model.
"""
import itertools
import random
import sys


# --- repo predicates, reproduced verbatim from colorbar.py @ base_commit -----
# def _extend_lower(self):
#     minmax = "max" if self._long_axis().get_inverted() else "min"
#     return self.extend in ('both', minmax)
# def _extend_upper(self):
#     minmax = "min" if self._long_axis().get_inverted() else "max"
#     return self.extend in ('both', minmax)

def real_extend_lower(extend, inverted):
    minmax = "max" if inverted else "min"
    return extend in ('both', minmax)


def real_extend_upper(extend, inverted):
    minmax = "min" if inverted else "max"
    return extend in ('both', minmax)


# --- the real slice-bound selection (the changed hunk), reproduced -----------
# start_idx = 0 if self._extend_lower() else 1
# end_idx   = len(X) if self._extend_upper() else -1
# self.dividers.set_segments(np.dstack([X, Y])[start_idx:end_idx])
def real_drawn(segments, extend, inverted):
    n = len(segments)
    el = real_extend_lower(extend, inverted)
    eu = real_extend_upper(extend, inverted)
    start_idx = 0 if el else 1
    end_idx = n if eu else -1                 # len(X) == n; -1 == drop last
    return segments[start_idx:end_idx]        # basic first-axis slicing


# --- model.py deep model, reproduced -----------------------------------------
def model_start_index(extend_lower):
    return 0 if extend_lower else 1


def model_end_index(extend_upper, n):
    return n if extend_upper else n - 1


def model_drawn(segments, extend_lower, extend_upper):
    n = len(segments)
    start = model_start_index(extend_lower)
    end = model_end_index(extend_upper, n)
    out = []
    i = start
    while i < end:
        out.append(segments[i])
        i += 1
    return out


def check(segments, extend, inverted):
    el = real_extend_lower(extend, inverted)
    eu = real_extend_upper(extend, inverted)
    observed = real_drawn(segments, extend, inverted)        # real behaviour
    modeled = model_drawn(segments, el, eu)                  # deep model
    assert observed == modeled, (
        "deep model unsound for extend=%r inverted=%r n=%d: real slice %r, "
        "deep model %r" % (extend, inverted, len(segments), observed, modeled))
    return el, eu


def main():
    extends = ['both', 'min', 'max', 'neither']

    # Sanity: the four canonical (non-inverted) cases the F2P test fixes, with
    # n = number-of-candidate-separators for that case (bounds=arange(3)).
    # 'both' -> 3 separators kept [0,1,2]; 'min'/'max' -> 2; 'neither' -> 1.
    canonical = {
        ('both', 3): [0, 1, 2],
        ('min', 3): [0, 1],
        ('max', 3): [1, 2],
        ('neither', 3): [1],
    }
    for (extend, n), expected_positions in canonical.items():
        segs = list(range(n))                  # position ids 0..n-1
        kept = real_drawn(segs, extend, inverted=False)
        assert kept == expected_positions, (
            "canonical mismatch extend=%r: real kept %r, F2P expects %r"
            % (extend, kept, expected_positions))
        check(segs, extend, inverted=False)

    # Boundary + exhaustive small sizes, both orientations of the long axis.
    small_configs = 0
    for n in range(2, 9):
        segs = list(range(n))
        for extend in extends:
            for inverted in (False, True):
                check(segs, extend, inverted)
                small_configs += 1

    # Fuzz: random sizes and random distinct position payloads.
    rng = random.Random(22865)
    for _ in range(20000):
        n = rng.randint(2, 40)
        # distinct ids so a kept element is unambiguously located
        segs = rng.sample(range(1000), n)
        extend = rng.choice(extends)
        inverted = rng.choice((False, True))
        check(segs, extend, inverted)

    # Cross-check: inversion swaps which end is open for 'min'/'max', and is a
    # no-op for 'both'/'neither' — confirm the predicate truth-table coverage.
    for extend, inverted in itertools.product(extends, (False, True)):
        el = real_extend_lower(extend, inverted)
        eu = real_extend_upper(extend, inverted)
        if extend == 'both':
            assert el and eu
        elif extend == 'neither':
            assert (not el) and (not eu)
        else:
            assert el != eu  # exactly one end open for min/max

    print("G-AX OK: deep model (start_index/end_index + slice loop) == real "
          "np.dstack[...][start_idx:end_idx] selection on 4 canonical + "
          "%d small-exhaustive + 20000 fuzz configurations" % small_configs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
