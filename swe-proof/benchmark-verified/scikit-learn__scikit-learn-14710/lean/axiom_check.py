#!/usr/bin/env python
"""G-AX: validate the A-reference gather for scikit-learn__scikit-learn-14710.

Runs INSIDE the instance image with the gold patch applied (PYTHONPATH=/testbed).

The bundle declares no consumed property axiom. The soundness-critical A-reference
is the deep model `relabelTargets labels codes` of the operation the fix adds for
a categorical estimator just before scoring:

    self.classes_[y_small_train.astype(int)]   # and the analogous y_val line

The Lean model is a **partial** element-wise gather, in three pieces that mirror
numpy fancy indexing over a 1-D table:

    codeIndex size c        = c + size  if c < 0 else c     -- where the code lands
    codesIndexLabels ls cs  = every code lands inside the table
    relabelTargets ls cs    = .ok (gathered entries)  when it does,
                              .error codeOutOfRange   when some code does not

So the model claims three things about `self.classes_[codes.astype(int)]`, and
this script asserts all three on both sides of the domain:

* a non-negative code in range gathers the entry it indexes from the front;
* a code in `[-size, 0)` gathers the entry it indexes from the **end** — numpy
  counts a negative index backwards, and the model resolves it the same way
  rather than clamping it (clamping would invent `classes_[0]`);
* a code outside `[-size, size)` gathers nothing at all: numpy RAISES
  `IndexError`, and the model's `.error codeOutOfRange` is that raise. Where the
  model reports the failure is exactly where numpy refuses, on either side of
  zero; this is a correspondence in both directions, so the check fails both if
  the model errs where numpy returns a value and if it returns a value where
  numpy raises.

The float codes come from `astype(int)`, which truncates toward zero (not toward
negative infinity); the model consumes the truncated integer, so the script
truncates the same way before resolving. Truncation and wraparound compose:
`-0.4` truncates to `0` and stays at the front of the table, while `-1.4`
truncates to `-1` and lands on its last entry.

That gather is an UNCHANGED callee: the fix merely adds a *call* to
`self.classes_[y.astype(int)]`; the indexing operation itself is stock numpy and
behaves identically at base_commit (where G-AX runs, unpatched). The end-to-end
witness that the patched method decodes targets before scoring is the harness's
job (G-RESOLVE, patch applied) — not G-AX, which validates real callees as they
exist at base_commit. stdlib + numpy only. Exit 0 iff sound.
"""
import random
import sys
import traceback

import numpy as np

SEED = 20240630
N_FUZZ = 5000

# Stands for the Lean `.error EarlyStopError.codeOutOfRange` on the model side and
# for numpy's `IndexError` on the real side: the gather produced no array at all.
NO_GATHER = "<codeOutOfRange>"


def code_index(size, c):
    """The Lean `codeIndex size c`: where one code lands in a table of `size`
    entries. `int(c)` is numpy's `astype(int)` — truncation toward zero."""
    i = int(c)
    return i + size if i < 0 else i


def codes_index_labels(labels, codes):
    """The Lean `codesIndexLabels labels codes`: the decode's domain — every code
    lands inside the table, from the front or from the end."""
    n = len(labels)
    return all(0 <= code_index(n, c) < n for c in codes)


def relabel_model(labels, codes):
    """The Lean `relabelTargets labels codes`: the gathered entries when every
    code lands inside the table, and `NO_GATHER` (the `codeOutOfRange` failure)
    when some code does not."""
    if not codes_index_labels(labels, codes):
        return NO_GATHER
    n = len(labels)
    return [labels[code_index(n, c)] for c in codes]


def relabel_real(classes_, codes):
    """`self.classes_[codes.astype(int)]`, with numpy's refusal to gather
    reported as `NO_GATHER` instead of propagating."""
    try:
        return list(classes_[codes.astype(int)])
    except IndexError:
        return NO_GATHER


def region(labels, codes):
    """Which part of the domain a code array exercises: "out" if some code lands
    outside the table (numpy raises), else "neg" if some code is negative (numpy
    counts from the end), else "front"."""
    n = len(labels)
    if any(not (0 <= code_index(n, c) < n) for c in codes):
        return "out"
    if any(int(c) < 0 for c in codes):
        return "neg"
    return "front"


def check(classes_, codes, where, failures, seen):
    """Assert the model and numpy agree about this pair, and record which part of
    the domain it exercised."""
    r = region(classes_, codes)
    seen[r] = seen.get(r, 0) + 1
    real = relabel_real(classes_, codes)
    model = relabel_model(classes_, codes)
    if real != model:
        failures.append(
            f"{where} mismatch [{r}]: classes_={list(classes_)} "
            f"codes={list(codes)} real={real!r} model={model!r}")
        return
    # The agreement must be the one this region is about, not an accident of both
    # sides gathering: outside the domain BOTH must decline, inside it neither.
    if r == "out" and model != NO_GATHER:
        failures.append(
            f"{where} classifier disagrees [{r}]: classes_={list(classes_)} "
            f"codes={list(codes)} gathered {model!r} where no code indexes")
    if r != "out" and model == NO_GATHER:
        failures.append(
            f"{where} classifier disagrees [{r}]: classes_={list(classes_)} "
            f"codes={list(codes)} declined although every code indexes")


def main():
    random.seed(SEED)
    failures = []
    seen = {}

    # --- Part 1: relabelTargets == self.classes_[codes.astype(int)] --------
    # Boundaries: empty table, empty codes, single entry, all-same, full range,
    # repeated codes, every negative index the table answers for, the first code
    # past each end, and float codes as `astype(int)` would truncate them.
    boundary_label_sets = [
        np.array([], dtype=object),
        np.array(["x", "y"], dtype=object),
        np.array(["a"], dtype=object),
        np.array(["alpha", "beta", "gamma"], dtype=object),
        np.array(list("abcdefghij"), dtype=object),
    ]
    for classes_ in boundary_label_sets:
        n = len(classes_)
        boundary_codes = [
            np.array([], dtype=float),
            np.array([], dtype=int),
            # inside the table, counting from the front
            np.array([0]),
            np.array([n - 1]),
            np.array([0] * 7),
            np.array(list(range(n))),
            np.array(list(range(n)) * 3),
            np.array([n - 1 + 0.9]),
            np.array([0.4, 0.0]),
            # inside the table, counting from the end
            np.array([-1]),
            np.array([-n]),
            np.array([-1, 0]),
            np.array(list(range(-n, 0))),
            np.array(list(range(-n, n))),
            np.array([-1.4]),
            np.array([-0.4]),          # truncates to 0: still the front entry
            np.array([-n - 0.5]),      # truncates to -n: the first entry
            # outside the table, on either side
            np.array([n]),
            np.array([n + 1]),
            np.array([-n - 1]),
            np.array([-n - 3]),
            np.array([0, n]),
            np.array([-n - 1, 0]),
            np.array([2 * n + 1]),
            np.array([n + 0.5]),
            np.array([-n - 1.5]),
        ]
        for codes in boundary_codes:
            check(classes_, codes, "boundary", failures, seen)

    # --- Part 2: fuzz -----------------------------------------------------
    # Each array targets one part of the domain, so all three are drawn: codes
    # from the front, codes counting from the end, and codes the table cannot
    # answer for on one side or the other.
    for _ in range(N_FUZZ):
        n = random.randint(0, 8)
        classes_ = np.array(["lbl_%d" % i for i in range(n)], dtype=object)
        m = random.randint(0, 12)
        target = random.choice(["front", "neg", "out", "out"])

        def draw(kind):
            if kind == "front":
                base = random.randint(0, n - 1) if n else 0
            elif kind == "neg":
                base = random.randint(-n, -1) if n else -1
            elif kind == "above":
                base = n + random.randint(0, 20)
            else:  # "below"
                base = -n - 1 - random.randint(0, 20)
            # codes may arrive as float (the astype(int) cast in the patch handles
            # it); the jitter is toward zero, which is where truncation moves.
            jitter = 0.0 if random.random() < 0.5 else (-0.4 if base > 0 else 0.4)
            return base + jitter

        if target == "front" or n == 0:
            raw = [draw("front") for _ in range(m)]
        elif target == "neg":
            raw = [draw(random.choice(["front", "neg", "neg"])) for _ in range(m)]
        else:
            raw = [draw(random.choice(["front", "neg"])) for _ in range(m)]
            raw.insert(random.randint(0, len(raw)),
                       draw(random.choice(["above", "below"])))
        codes = np.array(raw, dtype=float) if raw else np.array([], dtype=float)
        check(classes_, codes, "fuzz", failures, seen)
        if len(failures) > 20:
            break

    # Every part of the domain has to have been measured: an unexercised region
    # is a claim in the docstring this run did not check.
    for r in ("front", "neg", "out"):
        if not seen.get(r):
            failures.append(f"region {r!r} never exercised (nothing measured there)")

    if failures:
        print("status=fail")
        for f in failures[:20]:
            print("  -", f)
        print(f"({len(failures)} total)")
        return 1

    print(f"status=pass relabelTargets == self.classes_[codes.astype(int)] over "
          f"boundary + {N_FUZZ} fuzz cases, in both directions and on both sides "
          f"of the domain: front-indexed {seen['front']}, end-indexed "
          f"{seen['neg']}, out-of-range {seen['out']} (model .error "
          f"codeOutOfRange iff numpy IndexError); numpy fancy-index gather, "
          f"unchanged callee, sound at base_commit")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        print("status=error")
        sys.exit(2)
