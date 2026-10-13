# P2 adversarial audit — django__django-9296

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     # but does not mutate it, so it is required AND ensured at fractional
     # permission (directive 5).
     Requires(Acc(list_pred(page_numbers), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(page_numbers), 1 / 2))
@@ -74,19 +72,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(page_numbers)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(page_numbers), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(page_numbers))
-        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        x = page_numbers[i - 1]
-        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
-        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
-        result = [page_lookup(x)] + result
-        i = i - 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     # but does not mutate it, so it is required AND ensured at fractional
     # permission (directive 5).
     Requires(Acc(list_pred(page_numbers), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(page_numbers), 1 / 2))
@@ -74,18 +72,12 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(page_numbers)
+    i = len(page_numbers) - 1
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(page_numbers), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(page_numbers))
-        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         x = page_numbers[i - 1]
-        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
-        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
         result = [page_lookup(x)] + result
         i = i - 1
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     # but does not mutate it, so it is required AND ensured at fractional
     # permission (directive 5).
     Requires(Acc(list_pred(page_numbers), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(page_numbers), 1 / 2))
@@ -76,17 +74,11 @@
     result = []  # type: List[int]
     i = len(page_numbers)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(page_numbers), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(page_numbers))
-        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         x = page_numbers[i - 1]
-        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
-        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
-        result = [page_lookup(x)] + result
+        result = result + [page_lookup(x)]
         i = i - 1
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     # but does not mutate it, so it is required AND ensured at fractional
     # permission (directive 5).
     Requires(Acc(list_pred(page_numbers), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(page_numbers), 1 / 2))
@@ -76,17 +74,11 @@
     result = []  # type: List[int]
     i = len(page_numbers)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(page_numbers), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(page_numbers))
-        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         x = page_numbers[i - 1]
-        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
-        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
-        result = [page_lookup(x)] + result
+        result = [page_lookup(x)] + [page_lookup(x)] + result
         i = i - 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     # but does not mutate it, so it is required AND ensured at fractional
     # permission (directive 5).
     Requires(Acc(list_pred(page_numbers), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(page_numbers), 1 / 2))
@@ -76,17 +74,10 @@
     result = []  # type: List[int]
     i = len(page_numbers)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(page_numbers), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(page_numbers))
-        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        x = page_numbers[i - 1]
-        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
-        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
-        result = [page_lookup(x)] + result
+        result = [page_lookup(1)] + result
         i = i - 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     # but does not mutate it, so it is required AND ensured at fractional
     # permission (directive 5).
     Requires(Acc(list_pred(page_numbers), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(page_numbers), 1 / 2))
@@ -74,18 +72,14 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
+    if len(page_numbers) > 0:
+        return result
     i = len(page_numbers)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(page_numbers), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(page_numbers))
-        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         x = page_numbers[i - 1]
-        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
-        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
         result = [page_lookup(x)] + result
         i = i - 1
     return result
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -60,7 +59,6 @@
     # but does not mutate it, so it is required AND ensured at fractional
     # permission (directive 5).
     Requires(Acc(list_pred(page_numbers), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(page_numbers), 1 / 2))
@@ -74,19 +72,16 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(page_numbers)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(page_numbers):
         Invariant(Acc(list_pred(page_numbers), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(page_numbers))
-        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        x = page_numbers[i - 1]
-        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
-        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
-        result = [page_lookup(x)] + result
-        i = i - 1
+        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).take(i)))
+        x = page_numbers[i]
+        Assert(ToSeq(page_numbers).take(i + 1) == ToSeq(page_numbers).take(i) + PSeq(x))
+        result = result + [page_lookup(x)]
+        i = i + 1
+    Assert(ToSeq(page_numbers).take(len(page_numbers)) == ToSeq(page_numbers))
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-9296.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A paginated collection exposes a natural traversal over all of its pages.
  Given the collection's ordered run of 1-based page numbers, walking the
  collection produces — in that same order, one item per page number, none
  skipped, none repeated, none reordered — the page obtained by looking up each
  page number through the collection's existing page-by-number accessor.

  In particular: the traversal has exactly as many items as there are page
  numbers; the k-th item produced is the page for the k-th page number; and an
  empty run of page numbers yields an empty traversal.

The collection's ordered run of page numbers (an UNCHANGED property of the
collection) is the input, modelled as a `List[int]` and carried in the
specification by the pure sequence theory `PSeq[int]`. The page-by-number
accessor is an UNCHANGED callee (`page_lookup`), abstracted to an opaque pure
function of the page number; the traversal does not alter what a single page
contains, only that every page number is visited in order and mapped through
this accessor. The result is the per-page-number image of that accessor,
specified as the front-recursive map `mapped` (one unfold per traversal step).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def page_lookup(number: int) -> int:
    """The collection's UNCHANGED page-by-number accessor, abstracted to an
    opaque per-page-number value. It is a pure function of the 1-based page
    number alone (the value for a given page number does not depend on when in
    the traversal it is visited), which is all the traversal relies on.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def mapped(s: PSeq[int]) -> PSeq[int]:
    """The traversal image of a run of page numbers `s`: the page accessor
    applied to each page number, in order. Front-recursive over the sequence so
    a single unfold is available per traversal step (the canonical
    `f(s) == g(s[0]) + f(s.drop(1))` pattern)."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(page_lookup(s[0])) + mapped(s.drop(1))
# pure-end


def paginate_iter(page_numbers: List[int]) -> List[int]:
    # pre-conditions-start
    # The ordered run of page numbers is read-only: the traversal consumes it
    # but does not mutate it, so it is required AND ensured at fractional
    # permission (directive 5).
    Requires(Acc(list_pred(page_numbers), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(page_numbers), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The traversal produces exactly one item per page number, in the same
    # order, each item being the page accessor applied to that page number.
    # This pins the count (== number of page numbers), the order preservation
    # (item k is the page for page number k), and that no page number is
    # skipped, repeated, or reordered. An empty run yields an empty result.
    Ensures(ToSeq(Result()) == mapped(ToSeq(page_numbers)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(page_numbers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(page_numbers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(page_numbers))
        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
        # invariants-end
        x = page_numbers[i - 1]
        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
        result = [page_lookup(x)] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-9296 (nagini). Frozen spec view = axioms (@Pure @ContractOnly page_lookup, Ensures(True)) + pure region (front-recursive `mapped(s) = PSeq(page_lookup(s[0])) + mapped(s.drop(1))`) + pre/post of paginate_iter. The discriminating postcondition ToSeq(Result()) == mapped(ToSeq(page_numbers)) TOTALLY pins the output sequence: its length (== #page numbers), its order, and each element (page_lookup(page_numbers[k])). The impl region (incl. invariants) is consumer-supplied.

PROTOCOL. Positive control (gold model.py, unedited) VERIFIES: `bash scripts/nagini_verify.sh positive_control.py` => 'Verification successful' (12.3s). Encoded 7 attacks by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); all 7 confirmed byte-identical spec via `adversary same-spec` (exit 0). Ran `adversary weakness nagini django__django-9296 atk_N.py` on each, ==3 JVMs concurrently.

### RESULTS (all exit 2 = NOT-A-COUNTEREXAMPLE, spec rejected the wrong impl):
- atk_1 PREPATCH bug (return [] — collection not iterable, empty traversal): does not verify. Reproduces model_prepatch failure of the postcondition for non-empty runs (G-DIFF sense).
- atk_2 BOUNDARY off-by-one (i = len-1, skips last page number): does not verify.
- atk_3 REORDER (append at tail while iterating backward => reversed output): does not verify.
- atk_4 DUPLICATE (prepend each value twice, len = 2n): does not verify.
- atk_5 UNGROUNDED/WRONG-VALUE (every position = page_lookup(1) instead of page_lookup(page_numbers[k])): does not verify.
- atk_6 CONTROL-FLOW-EFFECT / partial-domain (early `return []` when len>0): does not verify.
- atk_7 CORRECT-ECHO (forward-build i:0..n, result = result + [page_lookup(x)]): does not verify only because my take()-based loop invariant did not discharge — a proof-shape artifact, NOT a spec hole (the gold back-recursive impl verifies as positive control).

No attack came back a CANDIDATE (none shares-spec-AND-verifies as a WRONG impl), so per protocol step 2 no faithful-patch run_resolve was required (that step triggers only for a verifying wrong impl). Every wrong-impl was rejected by the verifier => the spec is not too weak on any partial-domain / boundary / reorder / duplicate / control-flow / ungrounded-oracle-echo axis probed.

REFINEMENT.MD AUDIT (A-legs, R/I mechanically covered by G-CONF): A1 param<->self.page_range = R (range<->materialized element list); A2 backward loop<->generator = R+I (same in-order one-item-per-page-number production, construction direction only differs); A3 page_lookup<->Paginator.page = A-consumed (axiom Ensures(True); proof uses only purity-in-n; axiom_check.py asserts determinism of real Paginator.page); A4 mapped<->real Paginator.__iter__ = A-reference (deep front-recursive model validated == [page(n) for n in page_range] page-for-page by axiom_check.py over broad sweep incl. F2P witness Paginator([1,2,3],2), empty/single/orphan boundaries). §B: NO kind-3 leg — the one changed behaviour (added ordered traversal) is modeled DEEPLY in the consumed pure region, not behind a consumed __iter__ axiom; the only consumed axiom covers the UNCHANGED page accessor. patch.diff is purely additive (adds Paginator.__iter__ only); page/page_range/num_pages unchanged, so the A-leg correspondence to the real callees holds. verdict.md §C verify(model)=>resolved chain is coherent.

VERDICT: SOUND — >=5 distinct wrong impls (6 genuine + 1 correct-echo control) all run through the official adversary weakness harness; none is a verifying counterexample; refinement legs are all R/A-consumed/A-reference/I with sound callee correspondence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-9296.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A paginated collection exposes a natural traversal over all of its pages.
  Given the collection's ordered run of 1-based page numbers, walking the
  collection produces — in that same order, one item per page number, none
  skipped, none repeated, none reordered — the page obtained by looking up each
  page number through the collection's existing page-by-number accessor.

  In particular: the traversal has exactly as many items as there are page
  numbers; the k-th item produced is the page for the k-th page number; and an
  empty run of page numbers yields an empty traversal.

The collection's ordered run of page numbers (an UNCHANGED property of the
collection) is the input, modelled as a `List[int]` and carried in the
specification by the pure sequence theory `PSeq[int]`. The page-by-number
accessor is an UNCHANGED callee (`page_lookup`), abstracted to an opaque pure
function of the page number; the traversal does not alter what a single page
contains, only that every page number is visited in order and mapped through
this accessor. The result is the per-page-number image of that accessor,
specified as the front-recursive map `mapped` (one unfold per traversal step).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def page_lookup(number: int) -> int:
    """The collection's UNCHANGED page-by-number accessor, abstracted to an
    opaque per-page-number value. It is a pure function of the 1-based page
    number alone (the value for a given page number does not depend on when in
    the traversal it is visited), which is all the traversal relies on.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def mapped(s: PSeq[int]) -> PSeq[int]:
    """The traversal image of a run of page numbers `s`: the page accessor
    applied to each page number, in order. Front-recursive over the sequence so
    a single unfold is available per traversal step (the canonical
    `f(s) == g(s[0]) + f(s.drop(1))` pattern)."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(page_lookup(s[0])) + mapped(s.drop(1))
# pure-end


def paginate_iter(page_numbers: List[int]) -> List[int]:
    # pre-conditions-start
    # The ordered run of page numbers is read-only: the traversal consumes it
    # but does not mutate it, so it is required AND ensured at fractional
    # permission (directive 5).
    Requires(Acc(list_pred(page_numbers), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(page_numbers), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The traversal produces exactly one item per page number, in the same
    # order, each item being the page accessor applied to that page number.
    # This pins the count (== number of page numbers), the order preservation
    # (item k is the page for page number k), and that no page number is
    # skipped, repeated, or reordered. An empty run yields an empty result.
    Ensures(ToSeq(Result()) == mapped(ToSeq(page_numbers)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(page_numbers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(page_numbers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(page_numbers))
        Invariant(ToSeq(result) == mapped(ToSeq(page_numbers).drop(i)))
        # invariants-end
        x = page_numbers[i - 1]
        Assert(ToSeq(page_numbers).drop(i - 1)[0] == x)
        Assert(ToSeq(page_numbers).drop(i - 1).drop(1) == ToSeq(page_numbers).drop(i))
        result = [page_lookup(x)] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-9296 (nagini). Frozen spec view = axioms (@Pure @ContractOnly page_lookup, Ensures(True)) + pure region (front-recursive `mapped(s) = PSeq(page_lookup(s[0])) + mapped(s.drop(1))`) + pre/post of paginate_iter. The discriminating postcondition ToSeq(Result()) == mapped(ToSeq(page_numbers)) TOTALLY pins the output sequence: its length (== #page numbers), its order, and each element (page_lookup(page_numbers[k])). The impl region (incl. invariants) is consumer-supplied.

PROTOCOL. Positive control (gold model.py, unedited) VERIFIES: `bash scripts/nagini_verify.sh positive_control.py` => 'Verification successful' (12.3s). Encoded 7 attacks by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); all 7 confirmed byte-identical spec via `adversary same-spec` (exit 0). Ran `adversary weakness nagini django__django-9296 atk_N.py` on each, ==3 JVMs concurrently.

### RESULTS (all exit 2 = NOT-A-COUNTEREXAMPLE, spec rejected the wrong impl):
- atk_1 PREPATCH bug (return [] — collection not iterable, empty traversal): does not verify. Reproduces model_prepatch failure of the postcondition for non-empty runs (G-DIFF sense).
- atk_2 BOUNDARY off-by-one (i = len-1, skips last page number): does not verify.
- atk_3 REORDER (append at tail while iterating backward => reversed output): does not verify.
- atk_4 DUPLICATE (prepend each value twice, len = 2n): does not verify.
- atk_5 UNGROUNDED/WRONG-VALUE (every position = page_lookup(1) instead of page_lookup(page_numbers[k])): does not verify.
- atk_6 CONTROL-FLOW-EFFECT / partial-domain (early `return []` when len>0): does not verify.
- atk_7 CORRECT-ECHO (forward-build i:0..n, result = result + [page_lookup(x)]): does not verify only because my take()-based loop invariant did not discharge — a proof-shape artifact, NOT a spec hole (the gold back-recursive impl verifies as positive control).

No attack came back a CANDIDATE (none shares-spec-AND-verifies as a WRONG impl), so per protocol step 2 no faithful-patch run_resolve was required (that step triggers only for a verifying wrong impl). Every wrong-impl was rejected by the verifier => the spec is not too weak on any partial-domain / boundary / reorder / duplicate / control-flow / ungrounded-oracle-echo axis probed.

REFINEMENT.MD AUDIT (A-legs, R/I mechanically covered by G-CONF): A1 param<->self.page_range = R (range<->materialized element list); A2 backward loop<->generator = R+I (same in-order one-item-per-page-number production, construction direction only differs); A3 page_lookup<->Paginator.page = A-consumed (axiom Ensures(True); proof uses only purity-in-n; axiom_check.py asserts determinism of real Paginator.page); A4 mapped<->real Paginator.__iter__ = A-reference (deep front-recursive model validated == [page(n) for n in page_range] page-for-page by axiom_check.py over broad sweep incl. F2P witness Paginator([1,2,3],2), empty/single/orphan boundaries). §B: NO kind-3 leg — the one changed behaviour (added ordered traversal) is modeled DEEPLY in the consumed pure region, not behind a consumed __iter__ axiom; the only consumed axiom covers the UNCHANGED page accessor. patch.diff is purely additive (adds Paginator.__iter__ only); page/page_range/num_pages unchanged, so the A-leg correspondence to the real callees holds. verdict.md §C verify(model)=>resolved chain is coherent.

VERDICT: SOUND — >=5 distinct wrong impls (6 genuine + 1 correct-echo control) all run through the official adversary weakness harness; none is a verifying counterexample; refinement legs are all R/A-consumed/A-reference/I with sound callee correspondence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found between the modeled function and the real repo callee.

BASE/PATCH: base_commit 84322a29ce9b0940335f8ab3d60e55192bef1e50 present. Gold patch is purely additive — adds `def __iter__(self): for page_number in self.page_range: yield self.page(page_number)` to Paginator (django/core/paginator.py). page_range, page, num_pages, _get_page, Page are unchanged. This matches the model exactly.

SPEC INTEGRITY: same-spec on a byte-identical copy of model.py returns exit 0 (SAME).

### MACHINE CHECKS (against real patched repo worktree):
- nagini_verify.sh: Verification successful (18.5s).
- axiom_check.py (G-AX): OK over 480 configs — real Paginator.__iter__ == [page(n) for n in page_range] page-for-page (number + object_list), plus page(n) determinism; incl. F2P witness Paginator([1,2,3],2)=>[[1,2],[3]] and empty/single/orphan boundaries.
- conformance_check.py (G-CONF): OK over 100018 configs (18 boundary + 100000 fuzz, seed 9296), 0 disagreements — contract-stripped impl (backward-prepend loop) == real left-to-right traversal.
- Independent differential sweep over length x per_page x orphans x allow_empty: 0 divergences.

WHY NOT OVER-STRONG: The page_lookup axiom claims only the WEAKEST sufficient property (Ensures(True) — page(n) is a pure/deterministic function of n for a fixed collection), which the real Paginator.page satisfies; it deliberately does NOT encode slice/content/orphan/EmptyPage behaviour (page's unchanged concern). The deep model `mapped` equals the real traversal in order and per-position. The postcondition ToSeq(Result()) == mapped(ToSeq(page_numbers)) pins exactly count == len(page_numbers), order preservation, no skip/repeat/reorder, and empty->empty — precisely what the gold generator does, no more. Domain restriction orphans < per_page matches Django's operating domain and does not over-constrain vs. the real callee. G-DIFF: model_prepatch.py (returns []) fails the postcondition on any non-empty run, confirming the spec senses the change.

Conclusion: spec is a faithful abstraction of the real repo behavior; no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement for django__django-9296 already contains the gold patch VERBATIM (`def __iter__(self):\n    for page_num in self.page_range:\n        yield self.page(page_num)`). Because the entire gold edit — the new Paginator.__iter__ method, iterating self.page_range and yielding self.page(page_number), in django/core/paginator.py — is fully disclosed publicly, no line in the spec view can leak the gold edit BEYOND the public baseline. Every specifics-bearing statement in model.py/mapping.md/refinement.md (ordered per-page-number traversal, page-by-number accessor, page_range element list, empty-run boundary, target file/class) is traceable to code the problem_statement already prints. Auxiliary derivation detail (F2P witness Paginator([1,2,3],2), test name test_paginator_iteration, base_commit hash, line numbers) reveals test/provenance, not any residual gold-edit content the problem_statement does not already give. Judged against problem_statement only, not hints_text.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
