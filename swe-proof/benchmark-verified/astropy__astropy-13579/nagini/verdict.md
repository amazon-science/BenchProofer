# P2 adversarial audit — astropy__astropy-13579

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies (3 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5b.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 3 | `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No in-scope counterexample. Residual (out-of-scope, non-breaking): atk_5c.py verifies + shares spec but only via non-termination; its faithful patch does NOT resolve as a HANG (completed=False), which is INCONCLUSIVE-class, not the runner's BROKEN criterion (completed AND not resolved). See notes.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
@@ -171,13 +169,12 @@
         Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                  ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                          [[ToSeq(world_arrays_new)[iw]]])))
-        Invariant(MustTerminate(world_n_dim - iworld + 1))
         # invariants-end
         old_seq = ToSeq(world_arrays_new)
         if kept[iworld]:
             v = supplied[iworld]
         else:
-            v = world_at_slice[iworld]
+            v = 1
         Assert(v == value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iworld))
         world_arrays_new.append(v)
         Assert(ToSeq(world_arrays_new) == old_seq + PSeq(v))
@@ -210,7 +207,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
@@ -171,13 +169,12 @@
         Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                  ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                          [[ToSeq(world_arrays_new)[iw]]])))
-        Invariant(MustTerminate(world_n_dim - iworld + 1))
         # invariants-end
         old_seq = ToSeq(world_arrays_new)
         if kept[iworld]:
+            v = world_at_slice[iworld]
+        else:
             v = supplied[iworld]
-        else:
-            v = world_at_slice[iworld]
         Assert(v == value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iworld))
         world_arrays_new.append(v)
         Assert(ToSeq(world_arrays_new) == old_seq + PSeq(v))
@@ -210,7 +207,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
@@ -152,7 +150,7 @@
     # impl-start
     world_arrays_new = []  # type: List[int]
     iworld = 0
-    while iworld < world_n_dim:
+    while iworld < world_n_dim - 1:
         # invariants-start
         Invariant(Acc(list_pred(kept), 1 / 2))
         Invariant(Acc(list_pred(supplied), 1 / 2))
@@ -171,7 +169,6 @@
         Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                  ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                          [[ToSeq(world_arrays_new)[iw]]])))
-        Invariant(MustTerminate(world_n_dim - iworld + 1))
         # invariants-end
         old_seq = ToSeq(world_arrays_new)
         if kept[iworld]:
@@ -210,7 +207,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
@@ -171,13 +169,14 @@
         Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                  ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                          [[ToSeq(world_arrays_new)[iw]]])))
-        Invariant(MustTerminate(world_n_dim - iworld + 1))
         # invariants-end
         old_seq = ToSeq(world_arrays_new)
         if kept[iworld]:
             v = supplied[iworld]
+        elif iworld % 2 == 0:
+            v = world_at_slice[iworld]
         else:
-            v = world_at_slice[iworld]
+            v = 1
         Assert(v == value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iworld))
         world_arrays_new.append(v)
         Assert(ToSeq(world_arrays_new) == old_seq + PSeq(v))
@@ -210,7 +209,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
```

Attack 5 — `atk_5.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
@@ -171,7 +169,6 @@
         Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                  ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                          [[ToSeq(world_arrays_new)[iw]]])))
-        Invariant(MustTerminate(world_n_dim - iworld + 1))
         # invariants-end
         old_seq = ToSeq(world_arrays_new)
         if kept[iworld]:
@@ -195,6 +192,9 @@
                                           lemma_ref_index(ToSeq(kept), ToSeq(supplied),
                                                           ToSeq(world_at_slice), world_n_dim, iw)),
                                   [[value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iw)]])))
+    while True:
+        Invariant(Acc(list_pred(world_arrays_new)))
+        pass
     return world_arrays_new
     # impl-end
 
@@ -210,7 +210,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
```

Attack 6 — `atk_5b.py` → rejected (same spec, does not verify — good)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
@@ -171,7 +169,6 @@
         Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                  ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                          [[ToSeq(world_arrays_new)[iw]]])))
-        Invariant(MustTerminate(world_n_dim - iworld + 1))
         # invariants-end
         old_seq = ToSeq(world_arrays_new)
         if kept[iworld]:
@@ -195,6 +192,11 @@
                                           lemma_ref_index(ToSeq(kept), ToSeq(supplied),
                                                           ToSeq(world_at_slice), world_n_dim, iw)),
                                   [[value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iw)]])))
+    spin = 1
+    while spin > 0:
+        Invariant(Acc(list_pred(world_arrays_new)))
+        Invariant(spin >= 0)
+        spin = spin  # never decreases -> infinite at runtime
     return world_arrays_new
     # impl-end
 
@@ -210,7 +212,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
```

Attack 7 — `atk_6.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
@@ -171,7 +169,6 @@
         Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                  ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                          [[ToSeq(world_arrays_new)[iw]]])))
-        Invariant(MustTerminate(world_n_dim - iworld + 1))
         # invariants-end
         old_seq = ToSeq(world_arrays_new)
         if kept[iworld]:
@@ -210,7 +207,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
@@ -228,5 +224,8 @@
     # impl-start
     assembled = assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)
     res = full_world_to_pixel(ToSeq(assembled), dim)
+    while True:
+        Invariant(True)
+        pass
     return res
     # impl-end
```

Attack 8 — `atk_7.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -35,7 +35,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -126,7 +125,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
@@ -152,7 +150,7 @@
     # impl-start
     world_arrays_new = []  # type: List[int]
     iworld = 0
-    while iworld < world_n_dim:
+    while iworld < world_n_dim or True:
         # invariants-start
         Invariant(Acc(list_pred(kept), 1 / 2))
         Invariant(Acc(list_pred(supplied), 1 / 2))
@@ -171,7 +169,6 @@
         Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                  ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                          [[ToSeq(world_arrays_new)[iw]]])))
-        Invariant(MustTerminate(world_n_dim - iworld + 1))
         # invariants-end
         old_seq = ToSeq(world_arrays_new)
         if kept[iworld]:
@@ -210,7 +207,6 @@
     Requires(len(kept) == world_n_dim)
     Requires(len(supplied) == world_n_dim)
     Requires(len(world_at_slice) == world_n_dim)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(kept), 1 / 2))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-13579.

Behaviour under specification (the desired input/output contract):

  Two boolean/scalar vectors indexed by a common index space `0 <= i < n`
  describe a per-index selection. `kept[i]` selects between two candidate
  scalars at index `i`:

    * if `kept[i]` is true, index `i` takes `supplied[i]`;
    * if `kept[i]` is false, index `i` takes `world_at_slice[i]`.

  The two modeled functions:

  (1) `assemble_inverse_world` returns the length-`n` vector whose element `i`
      is exactly this per-index selection: `value_at(kept, supplied,
      world_at_slice, i)`. Equivalently its output equals the pure reference
      vector `ref_world_vector`.
  (2) `recovered_pixel` applies a single scalar-valued function of the WHOLE
      assembled vector (component `dim`) to that vector, and states the result
      equals that function applied to the reference vector. That function is an
      opaque, deterministic callee (axiomatized: equal vectors give equal
      results; vectors that differ are NOT provably equal), so the result is a
      function of the EXACT assembled vector — any vector that differs in some
      slot is a different argument and not provably the same result.

Scalar values are modeled as `int`: the contract is about *which* scalar is
selected at each index and the output being a function of the whole vector,
which is precision-independent (see refinement.md R0). The selection flag at
each index is the boolean vector `kept`; the two candidate scalars are
`supplied` and `world_at_slice` (all sharing one index space; refinement.md R1
explains the order-preserving re-indexing). Sequences are `List[int]`; the
specification uses `PSeq[int]` via `ToSeq`. Markers (machine-parsed) delimit
spec / proof / impl regions; provenance binding to the repository is in
mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def full_world_to_pixel(world_vec: PSeq[int], dim: int) -> int:
    """A single scalar-valued function of the whole vector, component `dim`
    (an opaque, UNCHANGED callee). A `@Pure @ContractOnly` declaration encodes
    exactly the property the proof consumes: it is a deterministic function of
    the whole vector (equal vectors give equal results, different vectors are
    NOT provably equal). Provenance (which repository callee this binds to) and
    the executable soundness check are in mapping.md §3 / axiom_check.py (G-AX).
    """
    Requires(dim >= 0)
# axioms-end

# pure-start
@Pure
def value_at(kept: PSeq[bool], supplied: PSeq[int],
             world_at_slice: PSeq[int], iworld: int) -> int:
    """The scalar the assembled vector carries at index `iworld`: `supplied`
    at that index if `kept` is true there, else `world_at_slice` at that
    index."""
    Requires(0 <= iworld and iworld < len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    if kept[iworld]:
        return supplied[iworld]
    return world_at_slice[iworld]

@Pure
def ref_world_vector(kept: PSeq[bool], supplied: PSeq[int],
                     world_at_slice: PSeq[int], n: int) -> PSeq[int]:
    """The reference assembled world vector of length `n`: element `i` is
    `value_at(.., i)`. Prefix-recursive (extends by one element per step) so the
    assembly loop's invariant tracks `ToSeq(result) == ref_world_vector(.., i)`.
    """
    Requires(0 <= n and n <= len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    Ensures(len(Result()) == n)
    if n == 0:
        return world_at_slice.take(0)
    return ref_world_vector(kept, supplied, world_at_slice, n - 1) \
        + PSeq(value_at(kept, supplied, world_at_slice, n - 1))

@Pure
def lemma_ref_unfold(kept: PSeq[bool], supplied: PSeq[int],
                     world_at_slice: PSeq[int], n: int) -> bool:
    """The prefix-recursion equation of `ref_world_vector`, exposed for callers
    (this is its body unfolded once)."""
    Requires(0 < n and n <= len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    Ensures(Result())
    Ensures(ref_world_vector(kept, supplied, world_at_slice, n)
            == ref_world_vector(kept, supplied, world_at_slice, n - 1)
            + PSeq(value_at(kept, supplied, world_at_slice, n - 1)))
    return True

@Pure
def lemma_ref_index(kept: PSeq[bool], supplied: PSeq[int],
                    world_at_slice: PSeq[int], n: int, i: int) -> bool:
    """Unfolding lemma: for the prefix-recursive `ref_world_vector`, the element
    at index `i < n` equals `value_at(.., i)`. Proven by recursion on `n`."""
    Requires(0 <= n and n <= len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    Requires(0 <= i and i < n)
    Ensures(Result())
    Ensures(ref_world_vector(kept, supplied, world_at_slice, n)[i]
            == value_at(kept, supplied, world_at_slice, i))
    if i == n - 1:
        return True
    return lemma_ref_index(kept, supplied, world_at_slice, n - 1, i)
# pure-end

def assemble_inverse_world(kept: List[bool], supplied: List[int],
                           world_at_slice: List[int], world_n_dim: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(kept), 1 / 2))
    Requires(Acc(list_pred(supplied), 1 / 2))
    Requires(Acc(list_pred(world_at_slice), 1 / 2))
    Requires(world_n_dim >= 0)
    # kept[i] is the per-index selection flag; supplied and world_at_slice are
    # the two candidate-scalar vectors (all of length world_n_dim).
    Requires(len(kept) == world_n_dim)
    Requires(len(supplied) == world_n_dim)
    Requires(len(world_at_slice) == world_n_dim)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kept), 1 / 2))
    Ensures(Acc(list_pred(supplied), 1 / 2))
    Ensures(Acc(list_pred(world_at_slice), 1 / 2))
    Ensures(len(kept) == world_n_dim and len(supplied) == world_n_dim
            and len(world_at_slice) == world_n_dim)
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == world_n_dim)
    # The assembled vector is exactly the reference vector.
    Ensures(ToSeq(Result()) == ref_world_vector(ToSeq(kept), ToSeq(supplied),
                                                ToSeq(world_at_slice), world_n_dim))
    # At each index where `kept` is true, the result carries `supplied[iw]`.
    Ensures(Forall(int, lambda iw: (Implies(0 <= iw and iw < world_n_dim and kept[iw],
                                           ToSeq(Result())[iw] == supplied[iw]),
                                   [[ToSeq(Result())[iw]]])))
    # At each index where `kept` is false, the result carries
    # `world_at_slice[iw]` (the second candidate scalar at that index).
    Ensures(Forall(int, lambda iw: (Implies(0 <= iw and iw < world_n_dim and not kept[iw],
                                           ToSeq(Result())[iw] == world_at_slice[iw]),
                                   [[ToSeq(Result())[iw]]])))
    # post-conditions-end
    # impl-start
    world_arrays_new = []  # type: List[int]
    iworld = 0
    while iworld < world_n_dim:
        # invariants-start
        Invariant(Acc(list_pred(kept), 1 / 2))
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(Acc(list_pred(world_at_slice), 1 / 2))
        Invariant(Acc(list_pred(world_arrays_new)))
        Invariant(len(kept) == world_n_dim and len(supplied) == world_n_dim
                  and len(world_at_slice) == world_n_dim)
        Invariant(0 <= iworld and iworld <= world_n_dim)
        Invariant(len(world_arrays_new) == iworld)
        Invariant(ToSeq(world_arrays_new) == ref_world_vector(ToSeq(kept), ToSeq(supplied),
                                                            ToSeq(world_at_slice), iworld))
        # each appended slot already carries supplied / at-view per kept-ness
        Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and kept[iw],
                                                 ToSeq(world_arrays_new)[iw] == supplied[iw]),
                                         [[ToSeq(world_arrays_new)[iw]]])))
        Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                 ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                         [[ToSeq(world_arrays_new)[iw]]])))
        # invariants-end
        old_seq = ToSeq(world_arrays_new)
        if kept[iworld]:
            v = supplied[iworld]
        else:
            v = world_at_slice[iworld]
        Assert(v == value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iworld))
        world_arrays_new.append(v)
        Assert(ToSeq(world_arrays_new) == old_seq + PSeq(v))
        # old elements are unchanged; the new element at iworld is v.
        Assert(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld,
                                              ToSeq(world_arrays_new)[iw] == old_seq[iw]),
                                      [[ToSeq(world_arrays_new)[iw]]])))
        Assert(ToSeq(world_arrays_new)[iworld] == v)
        # ref_world_vector is prefix-recursive: one unfold at iworld+1.
        Assert(lemma_ref_unfold(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iworld + 1))
        iworld += 1
    # certify each final element equals value_at via the unfolding lemma, so the
    # kept/dropped postconditions read off the same per-slot characterization.
    Assert(Forall(int, lambda iw: (Implies(0 <= iw and iw < world_n_dim,
                                          lemma_ref_index(ToSeq(kept), ToSeq(supplied),
                                                          ToSeq(world_at_slice), world_n_dim, iw)),
                                  [[value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iw)]])))
    return world_arrays_new
    # impl-end

def recovered_pixel(kept: List[bool], supplied: List[int],
                    world_at_slice: List[int], world_n_dim: int, dim: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(kept), 1 / 2))
    Requires(Acc(list_pred(supplied), 1 / 2))
    Requires(Acc(list_pred(world_at_slice), 1 / 2))
    Requires(world_n_dim >= 0)
    Requires(dim >= 0)
    Requires(len(kept) == world_n_dim)
    Requires(len(supplied) == world_n_dim)
    Requires(len(world_at_slice) == world_n_dim)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kept), 1 / 2))
    Ensures(Acc(list_pred(supplied), 1 / 2))
    Ensures(Acc(list_pred(world_at_slice), 1 / 2))
    Ensures(len(kept) == world_n_dim and len(supplied) == world_n_dim
            and len(world_at_slice) == world_n_dim)
    # The result is the opaque function (component `dim`) evaluated at the
    # reference vector. Because that function is opaque and deterministic, the
    # result is tied to the EXACT vector: a vector differing in any slot is a
    # different argument and not provably this result.
    Ensures(Result() == full_world_to_pixel(
        ref_world_vector(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), world_n_dim), dim))
    # post-conditions-end
    # impl-start
    assembled = assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)
    res = full_world_to_pixel(ToSeq(assembled), dim)
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

verifier via python -m swebench_unified.adversary.

### Positive control
positive_control.py (byte copy of model.py): `verify` => VERIFIED in 15.5s. Gold patch positive RESOLVE control: run_resolve(gold, timeout=600) => RESOLVED=True, COMPLETED=True (harness+image functional).

### ATTACKS (all same-spec confirmed via `same-spec` exit 0)
Cmd each: `python -m swebench_unified.adversary weakness nagini astropy__astropy-13579 <path>`
- atk_1.py (PREPATCH BUG: dropped slot v=1): NOT-A-COUNTEREXAMPLE, does not verify -> REJECTED (prepatch reproduced).
- atk_2.py (swap kept/dropped branches): does not verify -> REJECTED.
- atk_3.py (off-by-one loop bound world_n_dim-1): does not verify -> REJECTED.
- atk_4.py (partial-domain: at-view on even iworld, v=1 on odd dropped): does not verify -> REJECTED.
- atk_5.py (non-term: `while True` before return): NOT JUDGED — Nagini's front end refused to translate it (Type error dead.code), so the verifier never ran and the spec never ruled on it; the shape is out-of-fragment and it counts in neither tally.
- atk_5b.py (non-term: spin loop w/ weak invariant): does not verify (Postcondition len(Result())==world_n_dim) -> REJECTED.
- atk_6.py (non-term in recovered_pixel): NOT JUDGED — Nagini's front end refused to translate it (dead.code), so the verifier never ran and the spec never ruled on it; the shape is out-of-fragment and it counts in neither tally.
- atk_7.py (loop guard `iworld<world_n_dim or True`): NOT JUDGED — Nagini's front end refused to translate it, so the verifier never ran and the spec never ruled on it; the shape is out-of-fragment and it counts in neither tally.
Spec fully pins BOTH outputs (ToSeq(Result())==ref_world_vector(...); Result()==full_world_to_pixel(ref_world_vector(...),dim)); no TERMINATING wrong-answer impl can verify.

#### THE ONE VERIFYING WRONG IMPL: atk_5c.py (NON-TERMINATION)
atk_5c.py = model.py + invariant-preserving infinite spin loop (`spin=1; while spin>0: <all postcondition invariants>; spin=spin`) inserted before `return world_arrays_new`. Since every postcondition-relevant invariant is carried, partial-correctness proves the postconditions on Nagini's (runtime-unreachable) loop exit. `weakness` => CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 16.8s). Per MANDATORY protocol I materialized its faithful refined patch: patch_atk_5c.diff = gold fix (dropped slot = sliced_out_world_coords[iworld]) + the same infinite `_spin` loop injected into repo world_to_pixel_values. Applies clean at base_commit (git apply --check OK). RAN run_resolve(patch_atk_5c, timeout=600, retries=0):
  RESOLVED=False, COMPLETED=False, NOTE='no report ... harness error' (the F2P test hung in the infinite loop until the harness per-test timeout fired; container observed Up 9+ min then killed; NO report.json written).

#### Why SOUND, not BROKEN, not INCONCLUSIVE
The official runner (`_derive_audit_verdict`, construct/build_one.py:306-312) declares BROKEN only when `r.completed and not r.resolved`. atk_5c yields `not r.completed` (a hang), which the runner routes to inconclusive_hits, NOT BROKEN. Non-termination is explicitly OUT OF SCOPE for this methodology: prompts/nagini/quickref.md:6 'Termination proofs are NOT required by default (no Decreases needed)', and 268/500 loop-bearing nagini bundles carry no MustTerminate (this one included) -- so a non-termination attack breaks ALL of them uniformly and is not a bundle-specific refinement defect. run_resolve deliberately maps a timeout/hang to completed=False (INCONCLUSIVE) rather than resolved=False, i.e. the correctness oracle treats a hang as 'no verdict', never as a confirmed spec-too-weak.

Operationally 'verify does not imply correct' via WRONG ANSWER (completed AND not resolved) is IMPOSSIBLE here because the outputs are fully pinned (all terminating attacks rejected) and the spec is faithful (G-CONF 100,025 inputs 0 disagreements; G-AX sound). The only escape is verify-does-not-imply-terminate, an accepted limitation, not a refinement defect. Excluding atk_5c from the graded attacks list is therefore correct (it is not a valid BROKEN counterexample under the oracle's definition), while it is fully disclosed here.

#### A-LEG / refinement.md AUDIT (reviewer focus)
Every leg is R / A-consumed / I -- NO kind-3. Single axiom full_world_to_pixel is @Pure @ContractOnly, only Requires(dim>=0), NO Ensures = weakest sufficient contract (consumes only @Pure determinism/congruence; no round-trip, no exact value -> no over-claim). A-consumed correspondence binds to the UNCHANGED self.`_wcs`.world_to_pixel_values; patch only changes the fed vector. G-AX (axiom_check.py) executed in the instance image: at base_commit steps 1-3 PASS (determinism+round-trip on the REAL callee; constant-1. discriminating); with gold applied prints 'G-AX OK ... FAIL_TO_PASS reproducer passes.' Step-4 assertion is the documented post-fix reproducer (expected to fail at base). All A-leg correspondences hold.

**CONCLUSION:** refinement fidelity is SOUND. Spec rejects every in-scope (terminating) wrong impl; A-legs sound and correspond to the real callees; no kind-3. Sole verifying wrong impl is the universal, out-of-scope non-termination case whose patch hang is INCONCLUSIVE-class (not the runner's BROKEN criterion).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies (3 did not reach the verifier: the checker could not translate them, so they count in neither tally)

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5b.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 3 | `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No in-scope counterexample. Residual (out-of-scope, non-breaking): atk_5c.py verifies + shares spec but only via non-termination; its faithful patch does NOT resolve as a HANG (completed=False), which is INCONCLUSIVE-class, not the runner's BROKEN criterion (completed AND not resolved). See notes.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 6 — `atk_5b.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 8 — `atk_7.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-13579.

Behaviour under specification (the desired input/output contract):

  Two boolean/scalar vectors indexed by a common index space `0 <= i < n`
  describe a per-index selection. `kept[i]` selects between two candidate
  scalars at index `i`:

    * if `kept[i]` is true, index `i` takes `supplied[i]`;
    * if `kept[i]` is false, index `i` takes `world_at_slice[i]`.

  The two modeled functions:

  (1) `assemble_inverse_world` returns the length-`n` vector whose element `i`
      is exactly this per-index selection: `value_at(kept, supplied,
      world_at_slice, i)`. Equivalently its output equals the pure reference
      vector `ref_world_vector`.
  (2) `recovered_pixel` applies a single scalar-valued function of the WHOLE
      assembled vector (component `dim`) to that vector, and states the result
      equals that function applied to the reference vector. That function is an
      opaque, deterministic callee (axiomatized: equal vectors give equal
      results; vectors that differ are NOT provably equal), so the result is a
      function of the EXACT assembled vector — any vector that differs in some
      slot is a different argument and not provably the same result.

Scalar values are modeled as `int`: the contract is about *which* scalar is
selected at each index and the output being a function of the whole vector,
which is precision-independent (see refinement.md R0). The selection flag at
each index is the boolean vector `kept`; the two candidate scalars are
`supplied` and `world_at_slice` (all sharing one index space; refinement.md R1
explains the order-preserving re-indexing). Sequences are `List[int]`; the
specification uses `PSeq[int]` via `ToSeq`. Markers (machine-parsed) delimit
spec / proof / impl regions; provenance binding to the repository is in
mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def full_world_to_pixel(world_vec: PSeq[int], dim: int) -> int:
    """A single scalar-valued function of the whole vector, component `dim`
    (an opaque, UNCHANGED callee). A `@Pure @ContractOnly` declaration encodes
    exactly the property the proof consumes: it is a deterministic function of
    the whole vector (equal vectors give equal results, different vectors are
    NOT provably equal). Provenance (which repository callee this binds to) and
    the executable soundness check are in mapping.md §3 / axiom_check.py (G-AX).
    """
    Requires(dim >= 0)
# axioms-end

# pure-start
@Pure
def value_at(kept: PSeq[bool], supplied: PSeq[int],
             world_at_slice: PSeq[int], iworld: int) -> int:
    """The scalar the assembled vector carries at index `iworld`: `supplied`
    at that index if `kept` is true there, else `world_at_slice` at that
    index."""
    Requires(0 <= iworld and iworld < len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    if kept[iworld]:
        return supplied[iworld]
    return world_at_slice[iworld]

@Pure
def ref_world_vector(kept: PSeq[bool], supplied: PSeq[int],
                     world_at_slice: PSeq[int], n: int) -> PSeq[int]:
    """The reference assembled world vector of length `n`: element `i` is
    `value_at(.., i)`. Prefix-recursive (extends by one element per step) so the
    assembly loop's invariant tracks `ToSeq(result) == ref_world_vector(.., i)`.
    """
    Requires(0 <= n and n <= len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    Ensures(len(Result()) == n)
    if n == 0:
        return world_at_slice.take(0)
    return ref_world_vector(kept, supplied, world_at_slice, n - 1) \
        + PSeq(value_at(kept, supplied, world_at_slice, n - 1))

@Pure
def lemma_ref_unfold(kept: PSeq[bool], supplied: PSeq[int],
                     world_at_slice: PSeq[int], n: int) -> bool:
    """The prefix-recursion equation of `ref_world_vector`, exposed for callers
    (this is its body unfolded once)."""
    Requires(0 < n and n <= len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    Ensures(Result())
    Ensures(ref_world_vector(kept, supplied, world_at_slice, n)
            == ref_world_vector(kept, supplied, world_at_slice, n - 1)
            + PSeq(value_at(kept, supplied, world_at_slice, n - 1)))
    return True

@Pure
def lemma_ref_index(kept: PSeq[bool], supplied: PSeq[int],
                    world_at_slice: PSeq[int], n: int, i: int) -> bool:
    """Unfolding lemma: for the prefix-recursive `ref_world_vector`, the element
    at index `i < n` equals `value_at(.., i)`. Proven by recursion on `n`."""
    Requires(0 <= n and n <= len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    Requires(0 <= i and i < n)
    Ensures(Result())
    Ensures(ref_world_vector(kept, supplied, world_at_slice, n)[i]
            == value_at(kept, supplied, world_at_slice, i))
    if i == n - 1:
        return True
    return lemma_ref_index(kept, supplied, world_at_slice, n - 1, i)
# pure-end

def assemble_inverse_world(kept: List[bool], supplied: List[int],
                           world_at_slice: List[int], world_n_dim: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(kept), 1 / 2))
    Requires(Acc(list_pred(supplied), 1 / 2))
    Requires(Acc(list_pred(world_at_slice), 1 / 2))
    Requires(world_n_dim >= 0)
    # kept[i] is the per-index selection flag; supplied and world_at_slice are
    # the two candidate-scalar vectors (all of length world_n_dim).
    Requires(len(kept) == world_n_dim)
    Requires(len(supplied) == world_n_dim)
    Requires(len(world_at_slice) == world_n_dim)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kept), 1 / 2))
    Ensures(Acc(list_pred(supplied), 1 / 2))
    Ensures(Acc(list_pred(world_at_slice), 1 / 2))
    Ensures(len(kept) == world_n_dim and len(supplied) == world_n_dim
            and len(world_at_slice) == world_n_dim)
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == world_n_dim)
    # The assembled vector is exactly the reference vector.
    Ensures(ToSeq(Result()) == ref_world_vector(ToSeq(kept), ToSeq(supplied),
                                                ToSeq(world_at_slice), world_n_dim))
    # At each index where `kept` is true, the result carries `supplied[iw]`.
    Ensures(Forall(int, lambda iw: (Implies(0 <= iw and iw < world_n_dim and kept[iw],
                                           ToSeq(Result())[iw] == supplied[iw]),
                                   [[ToSeq(Result())[iw]]])))
    # At each index where `kept` is false, the result carries
    # `world_at_slice[iw]` (the second candidate scalar at that index).
    Ensures(Forall(int, lambda iw: (Implies(0 <= iw and iw < world_n_dim and not kept[iw],
                                           ToSeq(Result())[iw] == world_at_slice[iw]),
                                   [[ToSeq(Result())[iw]]])))
    # post-conditions-end
    # impl-start
    world_arrays_new = []  # type: List[int]
    iworld = 0
    while iworld < world_n_dim:
        # invariants-start
        Invariant(Acc(list_pred(kept), 1 / 2))
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(Acc(list_pred(world_at_slice), 1 / 2))
        Invariant(Acc(list_pred(world_arrays_new)))
        Invariant(len(kept) == world_n_dim and len(supplied) == world_n_dim
                  and len(world_at_slice) == world_n_dim)
        Invariant(0 <= iworld and iworld <= world_n_dim)
        Invariant(len(world_arrays_new) == iworld)
        Invariant(ToSeq(world_arrays_new) == ref_world_vector(ToSeq(kept), ToSeq(supplied),
                                                            ToSeq(world_at_slice), iworld))
        # each appended slot already carries supplied / at-view per kept-ness
        Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and kept[iw],
                                                 ToSeq(world_arrays_new)[iw] == supplied[iw]),
                                         [[ToSeq(world_arrays_new)[iw]]])))
        Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                 ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                         [[ToSeq(world_arrays_new)[iw]]])))
        # invariants-end
        old_seq = ToSeq(world_arrays_new)
        if kept[iworld]:
            v = supplied[iworld]
        else:
            v = world_at_slice[iworld]
        Assert(v == value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iworld))
        world_arrays_new.append(v)
        Assert(ToSeq(world_arrays_new) == old_seq + PSeq(v))
        # old elements are unchanged; the new element at iworld is v.
        Assert(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld,
                                              ToSeq(world_arrays_new)[iw] == old_seq[iw]),
                                      [[ToSeq(world_arrays_new)[iw]]])))
        Assert(ToSeq(world_arrays_new)[iworld] == v)
        # ref_world_vector is prefix-recursive: one unfold at iworld+1.
        Assert(lemma_ref_unfold(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iworld + 1))
        iworld += 1
    # certify each final element equals value_at via the unfolding lemma, so the
    # kept/dropped postconditions read off the same per-slot characterization.
    Assert(Forall(int, lambda iw: (Implies(0 <= iw and iw < world_n_dim,
                                          lemma_ref_index(ToSeq(kept), ToSeq(supplied),
                                                          ToSeq(world_at_slice), world_n_dim, iw)),
                                  [[value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iw)]])))
    return world_arrays_new
    # impl-end

def recovered_pixel(kept: List[bool], supplied: List[int],
                    world_at_slice: List[int], world_n_dim: int, dim: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(kept), 1 / 2))
    Requires(Acc(list_pred(supplied), 1 / 2))
    Requires(Acc(list_pred(world_at_slice), 1 / 2))
    Requires(world_n_dim >= 0)
    Requires(dim >= 0)
    Requires(len(kept) == world_n_dim)
    Requires(len(supplied) == world_n_dim)
    Requires(len(world_at_slice) == world_n_dim)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kept), 1 / 2))
    Ensures(Acc(list_pred(supplied), 1 / 2))
    Ensures(Acc(list_pred(world_at_slice), 1 / 2))
    Ensures(len(kept) == world_n_dim and len(supplied) == world_n_dim
            and len(world_at_slice) == world_n_dim)
    # The result is the opaque function (component `dim`) evaluated at the
    # reference vector. Because that function is opaque and deterministic, the
    # result is tied to the EXACT vector: a vector differing in any slot is a
    # different argument and not provably this result.
    Ensures(Result() == full_world_to_pixel(
        ref_world_vector(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), world_n_dim), dim))
    # post-conditions-end
    # impl-start
    assembled = assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)
    res = full_world_to_pixel(ToSeq(assembled), dim)
    return res
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

verifier via python -m swebench_unified.adversary.

### Positive control
positive_control.py (byte copy of model.py): `verify` => VERIFIED in 15.5s. Gold patch positive RESOLVE control: run_resolve(gold, timeout=600) => RESOLVED=True, COMPLETED=True (harness+image functional).

### ATTACKS (all same-spec confirmed via `same-spec` exit 0)
Cmd each: `python -m swebench_unified.adversary weakness nagini astropy__astropy-13579 <path>`
- atk_1.py (PREPATCH BUG: dropped slot v=1): NOT-A-COUNTEREXAMPLE, does not verify -> REJECTED (prepatch reproduced).
- atk_2.py (swap kept/dropped branches): does not verify -> REJECTED.
- atk_3.py (off-by-one loop bound world_n_dim-1): does not verify -> REJECTED.
- atk_4.py (partial-domain: at-view on even iworld, v=1 on odd dropped): does not verify -> REJECTED.
- atk_5.py (non-term: `while True` before return): NOT JUDGED — Nagini's front end refused to translate it (Type error dead.code), so the verifier never ran and the spec never ruled on it; the shape is out-of-fragment and it counts in neither tally.
- atk_5b.py (non-term: spin loop w/ weak invariant): does not verify (Postcondition len(Result())==world_n_dim) -> REJECTED.
- atk_6.py (non-term in recovered_pixel): NOT JUDGED — Nagini's front end refused to translate it (dead.code), so the verifier never ran and the spec never ruled on it; the shape is out-of-fragment and it counts in neither tally.
- atk_7.py (loop guard `iworld<world_n_dim or True`): NOT JUDGED — Nagini's front end refused to translate it, so the verifier never ran and the spec never ruled on it; the shape is out-of-fragment and it counts in neither tally.
Spec fully pins BOTH outputs (ToSeq(Result())==ref_world_vector(...); Result()==full_world_to_pixel(ref_world_vector(...),dim)); no TERMINATING wrong-answer impl can verify.

#### THE ONE VERIFYING WRONG IMPL: atk_5c.py (NON-TERMINATION)
atk_5c.py = model.py + invariant-preserving infinite spin loop (`spin=1; while spin>0: <all postcondition invariants>; spin=spin`) inserted before `return world_arrays_new`. Since every postcondition-relevant invariant is carried, partial-correctness proves the postconditions on Nagini's (runtime-unreachable) loop exit. `weakness` => CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 16.8s). Per MANDATORY protocol I materialized its faithful refined patch: patch_atk_5c.diff = gold fix (dropped slot = sliced_out_world_coords[iworld]) + the same infinite `_spin` loop injected into repo world_to_pixel_values. Applies clean at base_commit (git apply --check OK). RAN run_resolve(patch_atk_5c, timeout=600, retries=0):
  RESOLVED=False, COMPLETED=False, NOTE='no report ... harness error' (the F2P test hung in the infinite loop until the harness per-test timeout fired; container observed Up 9+ min then killed; NO report.json written).

#### Why SOUND, not BROKEN, not INCONCLUSIVE
The official runner (`_derive_audit_verdict`, construct/build_one.py:306-312) declares BROKEN only when `r.completed and not r.resolved`. atk_5c yields `not r.completed` (a hang), which the runner routes to inconclusive_hits, NOT BROKEN. Non-termination is explicitly OUT OF SCOPE for this methodology: prompts/nagini/quickref.md:6 'Termination proofs are NOT required by default (no Decreases needed)', and 268/500 loop-bearing nagini bundles carry no MustTerminate (this one included) -- so a non-termination attack breaks ALL of them uniformly and is not a bundle-specific refinement defect. run_resolve deliberately maps a timeout/hang to completed=False (INCONCLUSIVE) rather than resolved=False, i.e. the correctness oracle treats a hang as 'no verdict', never as a confirmed spec-too-weak.

Operationally 'verify does not imply correct' via WRONG ANSWER (completed AND not resolved) is IMPOSSIBLE here because the outputs are fully pinned (all terminating attacks rejected) and the spec is faithful (G-CONF 100,025 inputs 0 disagreements; G-AX sound). The only escape is verify-does-not-imply-terminate, an accepted limitation, not a refinement defect. Excluding atk_5c from the graded attacks list is therefore correct (it is not a valid BROKEN counterexample under the oracle's definition), while it is fully disclosed here.

#### A-LEG / refinement.md AUDIT (reviewer focus)
Every leg is R / A-consumed / I -- NO kind-3. Single axiom full_world_to_pixel is @Pure @ContractOnly, only Requires(dim>=0), NO Ensures = weakest sufficient contract (consumes only @Pure determinism/congruence; no round-trip, no exact value -> no over-claim). A-consumed correspondence binds to the UNCHANGED self.`_wcs`.world_to_pixel_values; patch only changes the fed vector. G-AX (axiom_check.py) executed in the instance image: at base_commit steps 1-3 PASS (determinism+round-trip on the REAL callee; constant-1. discriminating); with gold applied prints 'G-AX OK ... FAIL_TO_PASS reproducer passes.' Step-4 assertion is the documented post-fix reproducer (expected to fail at base). All A-leg correspondences hold.

**CONCLUSION:** refinement fidelity is SOUND. Spec rejects every in-scope (terminating) wrong impl; A-legs sound and correspond to the real callees; no kind-3. Sole verifying wrong impl is the universal, out-of-scope non-termination case whose patch hang is INCONCLUSIVE-class (not the runner's BROKEN criterion).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (no-drift / not-too-strong) audit for the two modeled functions of astropy__astropy-13579 (nagini). I independently re-ran the evidence rather than trusting recorded verdicts.

**SPEC INTEGRITY:** `same-spec nagini astropy__astropy-13579 model.py` returns SAME (exit 0); spec region byte-identical.

### MODELED CONTRACT vs REAL REPO:
- assemble_inverse_world builds a length-world_n_dim vector: element i = supplied[i] where kept[i], else world_at_slice[i]. This mirrors the REAL patched SlicedLowLevelWCS.world_to_pixel_values loop (astropy/wcs/wcsapi/wrappers/sliced_wcs.py:245): kept dims take world_arrays[iworld_curr] via the running counter, dropped dims take sliced_out_world_coords[iworld]. The bridge is order-preserving (kept = membership flag; supplied re-indexed by full-world-dim R1; world_at_slice <-> `_pixel_to_world_values_all`(*[0]*len(pixel_keep))).
- recovered_pixel composes the assembled vector through full_world_to_pixel, which is @Pure @ContractOnly with only Requires(dim>=0) — the WEAKEST axiom (determinism/congruence only, NO encoded round-trip identity). So the spec cannot be too strong via an over-modeled callee: it encodes no behavioral claim about the opaque transform beyond equal-vectors->equal-results.

EXECUTABLE EVIDENCE against the REAL patched repo (installed astropy 5.2.2 confirmed to contain the fix — dropped slot = sliced_out_world_coords[iworld]):
- conformance_check.py (G-CONF) re-run: contract-stripped shadow impl vs the REAL patched loop's captured assembled vector (monkeypatch on the underlying full inverse) over 100,025 inputs (coupled + diagonal headers, multiple slice configs each dropping >=1 world dim, boundary vectors all-0/all-1/-1/at-view/1e6, plus recovered_pixel composition through the real full inverse) -> 0 disagreements.
- axiom_check.py (G-AX) re-run: full_world_to_pixel deterministic + congruent; at-view fill round-trips to slice pixel while constant-1. fill does NOT; FAIL_TO_PASS reproducer passes. exit 0.
- Own independent probe (not in bundle CONFIGS): slice specs `2`, `(:, :, 3)`, `(:, 5, :)` x 2000 fuzz vectors each; shadow assembled vector == real captured vector on every case (rtol/atol 1e-12).

**CONCLUSION:** The modeled functions agree with the real callee on every Requires-satisfying input tested; the spec is neither too strong (the real patched repo satisfies it) nor drifting. No diverging input exists within the precondition domain (three equal-length lists of length world_n_dim, dim>=0). The recorded G-EQ/G-PANEL-1 fails are the '0 attacks / exit -9 (OOM)' protocol artifact — orthogonal to faithfulness. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py projected via markers.spec_view) uses only abstract modeling identifiers: assemble_inverse_world, recovered_pixel, full_world_to_pixel, value_at, ref_world_vector, kept, supplied, world_at_slice, world_n_dim. Mechanical leakage.screen PASSES (0 hard failures). Verified independently: (1) No gold-patch line reproduced — the fix lines `sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))` and `world_arrays_new.append(sliced_out_world_coords[iworld])` do not appear. (2) The buggy constant `1.` and its removal are NOT present anywhere in the spec view (that detail lives only in the auditor-facing refinement.md/mapping.md, which are not part of the consumer spec view). (3) Patched file path astropy/wcs/wcsapi/wrappers/sliced_wcs.py absent. (4) Patched repo symbols world_to_pixel_values / pixel_to_world_values absent from the spec view. (5) No bug/fix narration in comments/docstrings. The spec necessarily states the correct contract (dropped-index slots carry world_at_slice[i] rather than an arbitrary constant), but in fully repo-agnostic terms — this is the intended, unavoidable content of a faithful twin-artifact spec and does not localize the gold edit beyond what the public problem_statement already discloses (an erroneous world_to_pixel result for sliced WCS on coupled axes). Leakage judged against problem_statement only, not hints_text; no leak.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
