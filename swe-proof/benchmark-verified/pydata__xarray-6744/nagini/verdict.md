# P2 adversarial audit — pydata__xarray-6744

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py`, `atk_prepatch.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -179,16 +179,10 @@
     stops = []  # type: List[int]
     k = n
     while k > 0:
-        # invariants-start
         Invariant(Acc(list_pred(stops)))
         Invariant(0 <= k and k <= n)
-        Invariant(shift == end_shift(w, center))
-        Invariant(ToSeq(stops) == ends_from(k, n, w, center))
-        # invariants-end
-        Assert(shift + (k - 1) == end_at(k - 1, w, center))
-        Assert(ends_unfold(k - 1, n, w, center))
-        stops = [shift + (k - 1)] + stops
-        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
+        Invariant(len(stops) == n - k)
+        stops = [shift + k] + stops
         k = k - 1
     return stops
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,21 +219,14 @@
     starts = []  # type: List[int]
     k = n
     while k > 0:
-        # invariants-start
         Invariant(Acc(list_pred(starts)))
         Invariant(0 <= k and k <= n)
-        Invariant(shift == end_shift(w, center))
-        Invariant(ToSeq(starts) == begins_from(k, n, w, center))
-        # invariants-end
-        Assert(shift + (k - 1) == end_at(k - 1, w, center))
-        Assert(begins_unfold(k - 1, n, w, center))
-        raw = (shift + (k - 1)) - w
+        Invariant(len(starts) == n - k)
+        raw = (shift + (k - 1)) - (w - 1)
         if raw > 0:
             starts = [raw] + starts
         else:
             starts = [0] + starts
-        Assert(starts[0] == begin_at(k - 1, w, center))
-        Assert(ToSeq(starts) == PSeq(begin_at(k - 1, w, center)) + begins_from(k, n, w, center))
         k = k - 1
     return starts
     # impl-end
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,20 +175,14 @@
                                     [[Result()[i]]])))
     # post-conditions-end
     # impl-start
-    shift = end_shift(w, center)
+    shift = w // 2 if center else 1
     stops = []  # type: List[int]
     k = n
     while k > 0:
-        # invariants-start
         Invariant(Acc(list_pred(stops)))
         Invariant(0 <= k and k <= n)
-        Invariant(shift == end_shift(w, center))
-        Invariant(ToSeq(stops) == ends_from(k, n, w, center))
-        # invariants-end
-        Assert(shift + (k - 1) == end_at(k - 1, w, center))
-        Assert(ends_unfold(k - 1, n, w, center))
+        Invariant(len(stops) == n - k)
         stops = [shift + (k - 1)] + stops
-        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
         k = k - 1
     return stops
     # impl-end
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -177,19 +177,13 @@
     # impl-start
     shift = end_shift(w, center)
     stops = []  # type: List[int]
-    k = n
-    while k > 0:
-        # invariants-start
+    k = 0
+    while k < n:
         Invariant(Acc(list_pred(stops)))
         Invariant(0 <= k and k <= n)
-        Invariant(shift == end_shift(w, center))
-        Invariant(ToSeq(stops) == ends_from(k, n, w, center))
-        # invariants-end
-        Assert(shift + (k - 1) == end_at(k - 1, w, center))
-        Assert(ends_unfold(k - 1, n, w, center))
-        stops = [shift + (k - 1)] + stops
-        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
-        k = k - 1
+        Invariant(len(stops) == k)
+        stops = stops + [shift + (n - 1 - k)]
+        k = k + 1
     return stops
     # impl-end
 
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -178,17 +178,11 @@
     shift = end_shift(w, center)
     stops = []  # type: List[int]
     k = n
-    while k > 0:
-        # invariants-start
+    while k > 1:
         Invariant(Acc(list_pred(stops)))
-        Invariant(0 <= k and k <= n)
-        Invariant(shift == end_shift(w, center))
-        Invariant(ToSeq(stops) == ends_from(k, n, w, center))
-        # invariants-end
-        Assert(shift + (k - 1) == end_at(k - 1, w, center))
-        Assert(ends_unfold(k - 1, n, w, center))
+        Invariant(1 <= k and k <= n)
+        Invariant(len(stops) == n - k)
         stops = [shift + (k - 1)] + stops
-        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
         k = k - 1
     return stops
     # impl-end
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,20 +175,16 @@
                                     [[Result()[i]]])))
     # post-conditions-end
     # impl-start
-    shift = end_shift(w, center)
     stops = []  # type: List[int]
     k = n
     while k > 0:
-        # invariants-start
         Invariant(Acc(list_pred(stops)))
         Invariant(0 <= k and k <= n)
-        Invariant(shift == end_shift(w, center))
-        Invariant(ToSeq(stops) == ends_from(k, n, w, center))
-        # invariants-end
-        Assert(shift + (k - 1) == end_at(k - 1, w, center))
-        Assert(ends_unfold(k - 1, n, w, center))
-        stops = [shift + (k - 1)] + stops
-        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
+        Invariant(len(stops) == n - k)
+        if center:
+            stops = [end_at(k - 1, w, center) + 1] + stops
+        else:
+            stops = [end_at(k - 1, w, center)] + stops
         k = k - 1
     return stops
     # impl-end
```

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,21 +219,10 @@
     starts = []  # type: List[int]
     k = n
     while k > 0:
-        # invariants-start
         Invariant(Acc(list_pred(starts)))
         Invariant(0 <= k and k <= n)
-        Invariant(shift == end_shift(w, center))
-        Invariant(ToSeq(starts) == begins_from(k, n, w, center))
-        # invariants-end
-        Assert(shift + (k - 1) == end_at(k - 1, w, center))
-        Assert(begins_unfold(k - 1, n, w, center))
-        raw = (shift + (k - 1)) - w
-        if raw > 0:
-            starts = [raw] + starts
-        else:
-            starts = [0] + starts
-        Assert(starts[0] == begin_at(k - 1, w, center))
-        Assert(ToSeq(starts) == PSeq(begin_at(k - 1, w, center)) + begins_from(k, n, w, center))
+        Invariant(len(starts) == n - k)
+        starts = [(shift + (k - 1)) - w] + starts
         k = k - 1
     return starts
     # impl-end
```

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,20 +175,18 @@
                                     [[Result()[i]]])))
     # post-conditions-end
     # impl-start
-    shift = end_shift(w, center)
+    # Pre-patch skeleton: every block end is its position plus one, regardless
+    # of the justification mode (the centred flag is never consulted here).
+    shift = 1
     stops = []  # type: List[int]
     k = n
     while k > 0:
         # invariants-start
         Invariant(Acc(list_pred(stops)))
         Invariant(0 <= k and k <= n)
-        Invariant(shift == end_shift(w, center))
         Invariant(ToSeq(stops) == ends_from(k, n, w, center))
         # invariants-end
-        Assert(shift + (k - 1) == end_at(k - 1, w, center))
-        Assert(ends_unfold(k - 1, n, w, center))
         stops = [shift + (k - 1)] + stops
-        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
         k = k - 1
     return stops
     # impl-end
@@ -215,25 +213,23 @@
                                    [[Result()[i]]])))
     # post-conditions-end
     # impl-start
-    shift = end_shift(w, center)
+    # Pre-patch skeleton: the block end uses the same position-plus-one rule,
+    # so the start is its position-plus-one minus the window size, clamped to 0
+    # for the leading positions; the centred flag is never consulted.
+    shift = 1
     starts = []  # type: List[int]
     k = n
     while k > 0:
         # invariants-start
         Invariant(Acc(list_pred(starts)))
         Invariant(0 <= k and k <= n)
-        Invariant(shift == end_shift(w, center))
         Invariant(ToSeq(starts) == begins_from(k, n, w, center))
         # invariants-end
-        Assert(shift + (k - 1) == end_at(k - 1, w, center))
-        Assert(begins_unfold(k - 1, n, w, center))
         raw = (shift + (k - 1)) - w
         if raw > 0:
             starts = [raw] + starts
         else:
             starts = [0] + starts
-        Assert(starts[0] == begin_at(k - 1, w, center))
-        Assert(ToSeq(starts) == PSeq(begin_at(k - 1, w, center)) + begins_from(k, n, w, center))
         k = k - 1
     return starts
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-6744.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A one-dimensional moving-window object can be traversed one element at a
  time. The i-th step exposes the contiguous block of the underlying sequence
  that the windowed reduction assigns to position i, given by a half-open
  index range [begin_i, end_i) into that sequence of length n. The block must
  be the SAME block the vectorised windowed reduction uses for position i, so
  that traversing element by element reproduces the vectorised result exactly.

  The window has a constant size w (w > 0) and a justification mode:

    * When the window is NOT centred, position i ends just past index i:
      end_i = i + 1, so the block looks back over the w entries ending at i.

    * When the window IS centred, position i is shifted forward so the block is
      symmetric about i. The forward shift is exactly ceil(w / 2): the block for
      position i ends at end_i = i + ceil(w / 2). (For w = 1 this collapses to
      the non-centred case, end_i = i + 1, since ceil(1/2) = 1.)

  In both modes the block begins w entries before its end but is clamped at the
  beginning of the sequence: begin_i = max(0, end_i - w). The justification mode
  is therefore observable ONLY through this forward shift of the block ends; the
  shift must depend on whether the window is centred, and must equal ceil(w / 2)
  when it is.

The underlying sequence length n, the window size w and the centred flag are
the only inputs that determine the index ranges; the ranges are plain integers,
so the model is exact integer arithmetic (no type refinement of the carrier).
There are no axiomatized callees: the index computation is the changed
operation and is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No axiomatized callees: the index computation under specification is the
#  changed operation and is modelled deeply below; the underlying sequence
#  slicing it feeds is the unchanged caller, not a callee of this operation.)
# axioms-end

# pure-start
@Pure
def end_shift(w: int, center: bool) -> int:
    """Forward shift of every block end. Centred windows shift by ceil(w / 2)
    (so the block is symmetric about its position); otherwise by 1 (the block
    ends at its position)."""
    Requires(w > 0)
    Ensures(Result() >= 1)
    Ensures(Implies(not center, Result() == 1))
    Ensures(Implies(center, Result() == (w + 1) // 2))
    if center:
        return (w + 1) // 2
    return 1

@Pure
def end_at(i: int, w: int, center: bool) -> int:
    """End (exclusive) of the block at position i."""
    Requires(w > 0)
    Ensures(Result() == i + end_shift(w, center))
    return i + end_shift(w, center)

@Pure
def begin_at(i: int, w: int, center: bool) -> int:
    """Start (inclusive) of the block at position i: w entries before its end,
    clamped to the start of the sequence."""
    Requires(w > 0)
    Ensures(Result() >= 0)
    Ensures(Implies(end_at(i, w, center) - w >= 0, Result() == end_at(i, w, center) - w))
    Ensures(Implies(end_at(i, w, center) - w < 0, Result() == 0))
    raw = end_at(i, w, center) - w
    if raw > 0:
        return raw
    return 0

@Pure
def ends_from(j: int, n: int, w: int, center: bool) -> PSeq[int]:
    """The block ends for positions j, j+1, ..., n-1 in order. Front-recursive
    so callers get a single unfold per step."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Ensures(len(Result()) == n - j)
    if j == n:
        return PSeq(0).take(0)
    return PSeq(end_at(j, w, center)) + ends_from(j + 1, n, w, center)

@Pure
def begins_from(j: int, n: int, w: int, center: bool) -> PSeq[int]:
    """The block starts for positions j, j+1, ..., n-1 in order. Front-recursive
    so callers get a single unfold per step."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Ensures(len(Result()) == n - j)
    if j == n:
        return PSeq(0).take(0)
    return PSeq(begin_at(j, w, center)) + begins_from(j + 1, n, w, center)

@Pure
def ends_unfold(j: int, n: int, w: int, center: bool) -> bool:
    """Lemma: a single front-unfold of the block-end fold."""
    Requires(w > 0)
    Requires(0 <= j and j < n)
    Ensures(Result())
    Ensures(ends_from(j, n, w, center)
            == PSeq(end_at(j, w, center)) + ends_from(j + 1, n, w, center))
    return True

@Pure
def begins_unfold(j: int, n: int, w: int, center: bool) -> bool:
    """Lemma: a single front-unfold of the block-start fold."""
    Requires(w > 0)
    Requires(0 <= j and j < n)
    Ensures(Result())
    Ensures(begins_from(j, n, w, center)
            == PSeq(begin_at(j, w, center)) + begins_from(j + 1, n, w, center))
    return True

@Pure
def ends_index_lemma(j: int, m: int, n: int, w: int, center: bool) -> bool:
    """Lemma: the m-th entry of the block-end fold from j is the end of
    position j+m. Proven by front-recursion mirroring ends_from."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Requires(0 <= m and m < n - j)
    Ensures(Result())
    Ensures(ends_from(j, n, w, center)[m] == end_at(j + m, w, center))
    if m == 0:
        return True
    return ends_index_lemma(j + 1, m - 1, n, w, center)

@Pure
def begins_index_lemma(j: int, m: int, n: int, w: int, center: bool) -> bool:
    """Lemma: the m-th entry of the block-start fold from j is the start of
    position j+m. Proven by front-recursion mirroring begins_from."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Requires(0 <= m and m < n - j)
    Ensures(Result())
    Ensures(begins_from(j, n, w, center)[m] == begin_at(j + m, w, center))
    if m == 0:
        return True
    return begins_index_lemma(j + 1, m - 1, n, w, center)
# pure-end

def block_ends(n: int, w: int, center: bool) -> List[int]:
    # pre-conditions-start
    Requires(n >= 0)
    Requires(w > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n)
    Ensures(ToSeq(Result()) == ends_from(0, n, w, center))
    # Each block end is its position shifted forward by end_shift(w, center):
    # the centred shift ceil(w/2) is what makes the traversal centre-justified.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           ends_index_lemma(0, i, n, w, center)),
                                    [[Result()[i]]])))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           Result()[i] == end_at(i, w, center)),
                                    [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    shift = end_shift(w, center)
    stops = []  # type: List[int]
    k = n
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(stops)))
        Invariant(0 <= k and k <= n)
        Invariant(shift == end_shift(w, center))
        Invariant(ToSeq(stops) == ends_from(k, n, w, center))
        # invariants-end
        Assert(shift + (k - 1) == end_at(k - 1, w, center))
        Assert(ends_unfold(k - 1, n, w, center))
        stops = [shift + (k - 1)] + stops
        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
        k = k - 1
    return stops
    # impl-end

def block_begins(n: int, w: int, center: bool) -> List[int]:
    # pre-conditions-start
    Requires(n >= 0)
    Requires(w > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n)
    Ensures(ToSeq(Result()) == begins_from(0, n, w, center))
    # Each block begins w entries before its end, clamped to 0. Because the end
    # carries the justification shift, the start is centre-aware too.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           begins_index_lemma(0, i, n, w, center)),
                                    [[Result()[i]]])))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           Result()[i] == begin_at(i, w, center)),
                                    [[Result()[i]]])))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n, Result()[i] >= 0),
                                   [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    shift = end_shift(w, center)
    starts = []  # type: List[int]
    k = n
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(starts)))
        Invariant(0 <= k and k <= n)
        Invariant(shift == end_shift(w, center))
        Invariant(ToSeq(starts) == begins_from(k, n, w, center))
        # invariants-end
        Assert(shift + (k - 1) == end_at(k - 1, w, center))
        Assert(begins_unfold(k - 1, n, w, center))
        raw = (shift + (k - 1)) - w
        if raw > 0:
            starts = [raw] + starts
        else:
            starts = [0] + starts
        Assert(starts[0] == begin_at(k - 1, w, center))
        Assert(ToSeq(starts) == PSeq(begin_at(k - 1, w, center)) + begins_from(k, n, w, center))
        k = k - 1
    return starts
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for pydata__xarray-6744 (nagini). All commands run (SBU_BENCHMARK_DIR=.../benchmark-verified), swebench-lean venv, via `python -m swebench_unified.adversary weakness nagini pydata__xarray-6744 <atk>`.

SPEC SHAPE: block_ends/block_begins share one frozen spec that pins the ENTIRE output: Ensures(len(Result())==n), Ensures(ToSeq(Result())==ends_from(0,n,w,center)), and element-wise Ensures(Result()[i]==end_at(i,w,center)) / begin_at(i,w,center) plus Result()[i]>=0. This maximally-tight postcondition leaves no slack for a wrong array to verify.

ATTACKS (all same-spec confirmed via `same-spec` exit 0; spec/pure/axioms/Requires/Ensures byte-identical, only the two impl regions edited):
- atk1 (control-flow off-by-one on end: shift+k not shift+(k-1)) => weakness exit 2, REJECTED. res_atk1.log.
- atk2 (window boundary off-by-one: subtract w-1 not w in starts) => exit 2, REJECTED. res_atk2.log.
- atk3 (ungrounded formula: centred FLOOR shift w//2 not ceil (w+1)//2) => exit 2, REJECTED. res_atk3.log.
- atk4 (control-flow-effect: descending/reversed build order) => exit 2, REJECTED. res_atk4.log.
- atk5 (partial-domain: loop while k>1, drops last element, len=n-1) => exit 2, REJECTED. res_atk5.log.
- atk6 (ungrounded-oracle echo: end_at(i)+1 when centred) => exit 2, REJECTED. res_atk6.log.
- atk7 (boundary: no max(0,.) clamp on starts) => exit 2, REJECTED. res_atk7.log.
- atk_prepatch (the real bug, model_prepatch.py: shift=1 always, ignores center) => exit 2, REJECTED (prepatch bug reproduced; spec senses centred shift ceil(w/2) is required).

POSITIVE CONTROL: positive_control.py (= bundle model.py verbatim) => weakness exit 0 CANDIDATE (shares spec AND verifies, 20.8s). It is the gold-faithful impl and resolves under G-RESOLVE, so it is an echo, not a weakness (no materialization needed per policy).

No wrong impl verified => NO CANDIDATE requiring faithful-patch materialization + run_resolve. patches={} accordingly.

A-LEG / refinement.md AUDIT: every leg is R (A1 n<->dim size, A2 w<->window0, A3 center<->center[0], A5 arange<->ascending List[int], B2 subtract), A-reference+I (A4/B1: end_shift == gold offset=(w+1)//2 if center else 1), or I (B3: leading slice-assign clamp == max(0,end_at-w)). No kind-3 (unexpressible-changed-op) legs; NO @ContractOnly consumed axiom (refinement.md §D confirmed against model.py axioms-start/end block, which is empty). The lone A-reference correspondence to the real changed operation is machine-validated: axiom_check.py reproduces the gold patch's arange/subtract/slice-assign VERBATIM with plain ints and asserts end_at/begin_at match element-by-element => `python axiom_check.py` exit 0, OK on 200234 (n,window,center) cases (boundary sweep + 200000 fuzz + worked example n=9,w=3,center=True giving position-1 block [0,3)); clamp identity begin_at==max(0,end_at-w) and ceil(w/2)==(w+1)//2 identities hold. mapping.md §1-4 correspondences (base_commit 7cc6cc99...) are consistent with model.py symbols.

VERDICT SOUND: 7 distinct wrong impls + the prepatch bug all rejected by the frozen spec; positive control verifies; A-reference fidelity confirmed by axiom_check (exit 0); refinement legs all R/A-reference/I with no kind-3 and no consumed axiom. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py`, `atk_prepatch.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-6744.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A one-dimensional moving-window object can be traversed one element at a
  time. The i-th step exposes the contiguous block of the underlying sequence
  that the windowed reduction assigns to position i, given by a half-open
  index range [begin_i, end_i) into that sequence of length n. The block must
  be the SAME block the vectorised windowed reduction uses for position i, so
  that traversing element by element reproduces the vectorised result exactly.

  The window has a constant size w (w > 0) and a justification mode:

    * When the window is NOT centred, position i ends just past index i:
      end_i = i + 1, so the block looks back over the w entries ending at i.

    * When the window IS centred, position i is shifted forward so the block is
      symmetric about i. The forward shift is exactly ceil(w / 2): the block for
      position i ends at end_i = i + ceil(w / 2). (For w = 1 this collapses to
      the non-centred case, end_i = i + 1, since ceil(1/2) = 1.)

  In both modes the block begins w entries before its end but is clamped at the
  beginning of the sequence: begin_i = max(0, end_i - w). The justification mode
  is therefore observable ONLY through this forward shift of the block ends; the
  shift must depend on whether the window is centred, and must equal ceil(w / 2)
  when it is.

The underlying sequence length n, the window size w and the centred flag are
the only inputs that determine the index ranges; the ranges are plain integers,
so the model is exact integer arithmetic (no type refinement of the carrier).
There are no axiomatized callees: the index computation is the changed
operation and is modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (No axiomatized callees: the index computation under specification is the
#  changed operation and is modelled deeply below; the underlying sequence
#  slicing it feeds is the unchanged caller, not a callee of this operation.)
# axioms-end

# pure-start
@Pure
def end_shift(w: int, center: bool) -> int:
    """Forward shift of every block end. Centred windows shift by ceil(w / 2)
    (so the block is symmetric about its position); otherwise by 1 (the block
    ends at its position)."""
    Requires(w > 0)
    Ensures(Result() >= 1)
    Ensures(Implies(not center, Result() == 1))
    Ensures(Implies(center, Result() == (w + 1) // 2))
    if center:
        return (w + 1) // 2
    return 1

@Pure
def end_at(i: int, w: int, center: bool) -> int:
    """End (exclusive) of the block at position i."""
    Requires(w > 0)
    Ensures(Result() == i + end_shift(w, center))
    return i + end_shift(w, center)

@Pure
def begin_at(i: int, w: int, center: bool) -> int:
    """Start (inclusive) of the block at position i: w entries before its end,
    clamped to the start of the sequence."""
    Requires(w > 0)
    Ensures(Result() >= 0)
    Ensures(Implies(end_at(i, w, center) - w >= 0, Result() == end_at(i, w, center) - w))
    Ensures(Implies(end_at(i, w, center) - w < 0, Result() == 0))
    raw = end_at(i, w, center) - w
    if raw > 0:
        return raw
    return 0

@Pure
def ends_from(j: int, n: int, w: int, center: bool) -> PSeq[int]:
    """The block ends for positions j, j+1, ..., n-1 in order. Front-recursive
    so callers get a single unfold per step."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Ensures(len(Result()) == n - j)
    if j == n:
        return PSeq(0).take(0)
    return PSeq(end_at(j, w, center)) + ends_from(j + 1, n, w, center)

@Pure
def begins_from(j: int, n: int, w: int, center: bool) -> PSeq[int]:
    """The block starts for positions j, j+1, ..., n-1 in order. Front-recursive
    so callers get a single unfold per step."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Ensures(len(Result()) == n - j)
    if j == n:
        return PSeq(0).take(0)
    return PSeq(begin_at(j, w, center)) + begins_from(j + 1, n, w, center)

@Pure
def ends_unfold(j: int, n: int, w: int, center: bool) -> bool:
    """Lemma: a single front-unfold of the block-end fold."""
    Requires(w > 0)
    Requires(0 <= j and j < n)
    Ensures(Result())
    Ensures(ends_from(j, n, w, center)
            == PSeq(end_at(j, w, center)) + ends_from(j + 1, n, w, center))
    return True

@Pure
def begins_unfold(j: int, n: int, w: int, center: bool) -> bool:
    """Lemma: a single front-unfold of the block-start fold."""
    Requires(w > 0)
    Requires(0 <= j and j < n)
    Ensures(Result())
    Ensures(begins_from(j, n, w, center)
            == PSeq(begin_at(j, w, center)) + begins_from(j + 1, n, w, center))
    return True

@Pure
def ends_index_lemma(j: int, m: int, n: int, w: int, center: bool) -> bool:
    """Lemma: the m-th entry of the block-end fold from j is the end of
    position j+m. Proven by front-recursion mirroring ends_from."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Requires(0 <= m and m < n - j)
    Ensures(Result())
    Ensures(ends_from(j, n, w, center)[m] == end_at(j + m, w, center))
    if m == 0:
        return True
    return ends_index_lemma(j + 1, m - 1, n, w, center)

@Pure
def begins_index_lemma(j: int, m: int, n: int, w: int, center: bool) -> bool:
    """Lemma: the m-th entry of the block-start fold from j is the start of
    position j+m. Proven by front-recursion mirroring begins_from."""
    Requires(w > 0)
    Requires(0 <= j and j <= n)
    Requires(0 <= m and m < n - j)
    Ensures(Result())
    Ensures(begins_from(j, n, w, center)[m] == begin_at(j + m, w, center))
    if m == 0:
        return True
    return begins_index_lemma(j + 1, m - 1, n, w, center)
# pure-end

def block_ends(n: int, w: int, center: bool) -> List[int]:
    # pre-conditions-start
    Requires(n >= 0)
    Requires(w > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n)
    Ensures(ToSeq(Result()) == ends_from(0, n, w, center))
    # Each block end is its position shifted forward by end_shift(w, center):
    # the centred shift ceil(w/2) is what makes the traversal centre-justified.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           ends_index_lemma(0, i, n, w, center)),
                                    [[Result()[i]]])))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           Result()[i] == end_at(i, w, center)),
                                    [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    shift = end_shift(w, center)
    stops = []  # type: List[int]
    k = n
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(stops)))
        Invariant(0 <= k and k <= n)
        Invariant(shift == end_shift(w, center))
        Invariant(ToSeq(stops) == ends_from(k, n, w, center))
        # invariants-end
        Assert(shift + (k - 1) == end_at(k - 1, w, center))
        Assert(ends_unfold(k - 1, n, w, center))
        stops = [shift + (k - 1)] + stops
        Assert(ToSeq(stops) == PSeq(shift + (k - 1)) + ends_from(k, n, w, center))
        k = k - 1
    return stops
    # impl-end

def block_begins(n: int, w: int, center: bool) -> List[int]:
    # pre-conditions-start
    Requires(n >= 0)
    Requires(w > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == n)
    Ensures(ToSeq(Result()) == begins_from(0, n, w, center))
    # Each block begins w entries before its end, clamped to 0. Because the end
    # carries the justification shift, the start is centre-aware too.
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           begins_index_lemma(0, i, n, w, center)),
                                    [[Result()[i]]])))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n,
                                           Result()[i] == begin_at(i, w, center)),
                                    [[Result()[i]]])))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < n, Result()[i] >= 0),
                                   [[Result()[i]]])))
    # post-conditions-end
    # impl-start
    shift = end_shift(w, center)
    starts = []  # type: List[int]
    k = n
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(starts)))
        Invariant(0 <= k and k <= n)
        Invariant(shift == end_shift(w, center))
        Invariant(ToSeq(starts) == begins_from(k, n, w, center))
        # invariants-end
        Assert(shift + (k - 1) == end_at(k - 1, w, center))
        Assert(begins_unfold(k - 1, n, w, center))
        raw = (shift + (k - 1)) - w
        if raw > 0:
            starts = [raw] + starts
        else:
            starts = [0] + starts
        Assert(starts[0] == begin_at(k - 1, w, center))
        Assert(ToSeq(starts) == PSeq(begin_at(k - 1, w, center)) + begins_from(k, n, w, center))
        k = k - 1
    return starts
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for pydata__xarray-6744 (nagini). All commands run (SBU_BENCHMARK_DIR=.../benchmark-verified), swebench-lean venv, via `python -m swebench_unified.adversary weakness nagini pydata__xarray-6744 <atk>`.

SPEC SHAPE: block_ends/block_begins share one frozen spec that pins the ENTIRE output: Ensures(len(Result())==n), Ensures(ToSeq(Result())==ends_from(0,n,w,center)), and element-wise Ensures(Result()[i]==end_at(i,w,center)) / begin_at(i,w,center) plus Result()[i]>=0. This maximally-tight postcondition leaves no slack for a wrong array to verify.

ATTACKS (all same-spec confirmed via `same-spec` exit 0; spec/pure/axioms/Requires/Ensures byte-identical, only the two impl regions edited):
- atk1 (control-flow off-by-one on end: shift+k not shift+(k-1)) => weakness exit 2, REJECTED. res_atk1.log.
- atk2 (window boundary off-by-one: subtract w-1 not w in starts) => exit 2, REJECTED. res_atk2.log.
- atk3 (ungrounded formula: centred FLOOR shift w//2 not ceil (w+1)//2) => exit 2, REJECTED. res_atk3.log.
- atk4 (control-flow-effect: descending/reversed build order) => exit 2, REJECTED. res_atk4.log.
- atk5 (partial-domain: loop while k>1, drops last element, len=n-1) => exit 2, REJECTED. res_atk5.log.
- atk6 (ungrounded-oracle echo: end_at(i)+1 when centred) => exit 2, REJECTED. res_atk6.log.
- atk7 (boundary: no max(0,.) clamp on starts) => exit 2, REJECTED. res_atk7.log.
- atk_prepatch (the real bug, model_prepatch.py: shift=1 always, ignores center) => exit 2, REJECTED (prepatch bug reproduced; spec senses centred shift ceil(w/2) is required).

POSITIVE CONTROL: positive_control.py (= bundle model.py verbatim) => weakness exit 0 CANDIDATE (shares spec AND verifies, 20.8s). It is the gold-faithful impl and resolves under G-RESOLVE, so it is an echo, not a weakness (no materialization needed per policy).

No wrong impl verified => NO CANDIDATE requiring faithful-patch materialization + run_resolve. patches={} accordingly.

A-LEG / refinement.md AUDIT: every leg is R (A1 n<->dim size, A2 w<->window0, A3 center<->center[0], A5 arange<->ascending List[int], B2 subtract), A-reference+I (A4/B1: end_shift == gold offset=(w+1)//2 if center else 1), or I (B3: leading slice-assign clamp == max(0,end_at-w)). No kind-3 (unexpressible-changed-op) legs; NO @ContractOnly consumed axiom (refinement.md §D confirmed against model.py axioms-start/end block, which is empty). The lone A-reference correspondence to the real changed operation is machine-validated: axiom_check.py reproduces the gold patch's arange/subtract/slice-assign VERBATIM with plain ints and asserts end_at/begin_at match element-by-element => `python axiom_check.py` exit 0, OK on 200234 (n,window,center) cases (boundary sweep + 200000 fuzz + worked example n=9,w=3,center=True giving position-1 block [0,3)); clamp identity begin_at==max(0,end_at-w) and ceil(w/2)==(w+1)//2 identities hold. mapping.md §1-4 correspondences (base_commit 7cc6cc99...) are consistent with model.py symbols.

VERDICT SOUND: 7 distinct wrong impls + the prepatch bug all rejected by the frozen spec; positive control verifies; A-reference fidelity confirmed by axiom_check (exit 0); refinement legs all R/A-reference/I with no kind-3 and no consumed axiom. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pydata__xarray-6744 nagini bundle. The modeled functions block_ends/block_begins specify the gold-patched DataArrayRolling.__iter__ index arithmetic: offset=(w+1)//2 if center else 1; stops=arange(offset,n+offset); starts=stops-w; starts[:w-offset]=0. Spec pins Result()[i]==end_at(i)=i+end_shift(w,center), begin_at(i)=max(0,end_at(i)-w), and begin_at>=0.

Checks performed:

(1) DOMAIN MATCH — model preconditions n>=0, w>0 exactly match the real repo: Rolling.__init__ raises ValueError('window must be > 0') (xarray/core/rolling.py ~line 80 at base_commit 7cc6cc9), and n=self.obj.sizes[dim0] is a nonnegative dimension size. There is NO excluded input where the modeled function could disagree with the real callee.

(2) INDEPENDENT NUMPY COMPARISON — my own script reproducing the gold patch's real np.arange/subtract/slice-assign (numpy, not the stdlib mirror) over the full boundary sweep n=0..40 x w=1..40 x {center True,False} PLUS 300000 random cases up to n,w=200: model end_at/begin_at match the real index arrays element-for-element with ZERO mismatches; verified starts never negative. checked=303280 mismatches=0.

(3) CLAMP EQUIVALENCE — w-offset = w-(w+1)//2 = floor(w/2) >= 0 when center, and w-1 >= 0 when not center (since w>0), so the slice count is always well-defined and starts[:w-offset]=0 equals max(0,offset+i-w)=begin_at(i).

(4) end_shift>=1 and begin_at>=0 hold for all real repo values; the centered shift (w+1)//2 == ceil(w/2) and collapses to 1 at w=1, matching the patch.

(5) same-spec harness on the identity (bundle) model returns exit 0 — spec region is byte-identical / correctly audited.

(6) Bundle axiom_check.py (200k+ fuzz) and G-CONF (100308 cases, 0 disagreements) independently agree.

The spec is neither too strong nor drifted from the real callee: no diverging input exists between the modeled functions and the gold patch's real index computation. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (consumer projection of model.py) computed via spec_view/NaginiBackend; mechanical leak.screen PASSES (no hard failures) and meta G-LEAK=pass, relaxed_leakage unset. Semantic check confirms no gold-edit disclosure beyond the public problem_statement:

- No gold-implementation tokens present in spec view: 'offset', 'window0', 'np.arange', 'starts[', 'stops', 'self.center', 'self.window', 'self.dim', 'isel', 'sizes[', 'rolling.py', '__iter__' — all absent.
- No diff markers, no patched file/module path, no patched repo symbol echoed in spec-view identifiers or comments. Patch's only distinctive changed symbol is 'iter' (from __iter__), which does not appear.
- No bug/fix narration; the module docstring explicitly frames the content 'as desired behaviour, not as an edit.'
- The gold-shaped impl regions of block_ends/block_begins are elided ('... implementation elided — supplied by the consumer').

The only substantive spec content is the abstract behavioral characterization: end_shift = ceil(w/2) when centered else 1, end_at(i)=i+shift, begin_at(i)=max(0, end_at(i)-w). This is the mathematical definition of center-justified windows, which is exactly the behavior the PUBLIC problem_statement demands (it shows rolling(x=3, center=True) must yield [nan,2,3,4,5,6,7,8,nan] via manual iteration, not [nan,nan,2,...]) and its worked example (w=3 -> shift 2 = ceil(3/2)) makes the shift derivable. A spec MUST state required behavior; stating it is not leaking the edit. The spec does not reveal the pre-patch offset value (1), does not name the patched local 'offset'/'window0', and does not reproduce any diff line. auditor docs (mapping.md, refinement.md) quote patch.diff verbatim but are NOT the solver-visible spec view. Faithful behavioral spec; leaks nothing beyond public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.