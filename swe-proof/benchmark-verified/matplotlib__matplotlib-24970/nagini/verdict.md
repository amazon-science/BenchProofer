# P2 adversarial audit — matplotlib__matplotlib-24970

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1.py`, `atk2.py`, `atk5.py`, `atk7.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk3.py`, `atk4.py`, `atk6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # index it writes; the largest is n + 2, so the container must admit values
     # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
     Requires(modulus >= n + 3)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(values), 1 / 2))
     Ensures(Acc(list_pred(bads), 1 / 2))
     Ensures(Acc(list_pred(Result())))
@@ -172,7 +170,6 @@
     Requires(len(values) == len(bads))
     Requires(n >= 1)
     Requires(modulus >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(values), 1 / 2))
@@ -192,12 +189,6 @@
     Ensures(rows_assigned(ToSeq(Result()), n))
     # post-conditions-end
     # impl-start
-    # Build the per-element special-row assignment input-by-input, mirroring the
-    # element-wise array operation, then carry it out on a container that admits
-    # every special index it writes. The special indices are the under-range row
-    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
-    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
-    # admits the whole assignment -- the input's own container may be narrower.
     sel_values = []  # type: List[int]
     sel_bads = []  # type: List[bool]
     i = len(values)
@@ -213,7 +204,6 @@
         Invariant(len(sel_bads) == len(bads) - i)
         Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
         Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         v = values[i - 1]
         bad = bads[i - 1]
@@ -226,7 +216,7 @@
         i = i - 1
     Assert(ToSeq(sel_values) == ToSeq(values))
     Assert(ToSeq(sel_bads) == ToSeq(bads))
-    carrier = n + 3
+    carrier = n + 2
     result = assign_special_rows(sel_values, sel_bads, n, carrier)
     return result
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # index it writes; the largest is n + 2, so the container must admit values
     # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
     Requires(modulus >= n + 3)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(values), 1 / 2))
     Ensures(Acc(list_pred(bads), 1 / 2))
     Ensures(Acc(list_pred(Result())))
@@ -172,7 +170,6 @@
     Requires(len(values) == len(bads))
     Requires(n >= 1)
     Requires(modulus >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(values), 1 / 2))
@@ -192,12 +189,6 @@
     Ensures(rows_assigned(ToSeq(Result()), n))
     # post-conditions-end
     # impl-start
-    # Build the per-element special-row assignment input-by-input, mirroring the
-    # element-wise array operation, then carry it out on a container that admits
-    # every special index it writes. The special indices are the under-range row
-    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
-    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
-    # admits the whole assignment -- the input's own container may be narrower.
     sel_values = []  # type: List[int]
     sel_bads = []  # type: List[bool]
     i = len(values)
@@ -213,7 +204,6 @@
         Invariant(len(sel_bads) == len(bads) - i)
         Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
         Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         v = values[i - 1]
         bad = bads[i - 1]
@@ -228,5 +218,5 @@
     Assert(ToSeq(sel_bads) == ToSeq(bads))
     carrier = n + 3
     result = assign_special_rows(sel_values, sel_bads, n, carrier)
-    return result
+    return sel_values
     # impl-end
```

Attack 3 — `atk3.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # index it writes; the largest is n + 2, so the container must admit values
     # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
     Requires(modulus >= n + 3)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(values), 1 / 2))
     Ensures(Acc(list_pred(bads), 1 / 2))
     Ensures(Acc(list_pred(Result())))
@@ -172,7 +170,6 @@
     Requires(len(values) == len(bads))
     Requires(n >= 1)
     Requires(modulus >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(values), 1 / 2))
@@ -192,12 +189,6 @@
     Ensures(rows_assigned(ToSeq(Result()), n))
     # post-conditions-end
     # impl-start
-    # Build the per-element special-row assignment input-by-input, mirroring the
-    # element-wise array operation, then carry it out on a container that admits
-    # every special index it writes. The special indices are the under-range row
-    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
-    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
-    # admits the whole assignment -- the input's own container may be narrower.
     sel_values = []  # type: List[int]
     sel_bads = []  # type: List[bool]
     i = len(values)
@@ -213,7 +204,6 @@
         Invariant(len(sel_bads) == len(bads) - i)
         Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
         Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         v = values[i - 1]
         bad = bads[i - 1]
@@ -226,7 +216,10 @@
         i = i - 1
     Assert(ToSeq(sel_values) == ToSeq(values))
     Assert(ToSeq(sel_bads) == ToSeq(bads))
-    carrier = n + 3
+    if modulus >= n + 3:
+        carrier = modulus
+    else:
+        carrier = n + 3
     result = assign_special_rows(sel_values, sel_bads, n, carrier)
     return result
     # impl-end
```

Attack 4 — `atk4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # index it writes; the largest is n + 2, so the container must admit values
     # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
     Requires(modulus >= n + 3)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(values), 1 / 2))
     Ensures(Acc(list_pred(bads), 1 / 2))
     Ensures(Acc(list_pred(Result())))
@@ -172,7 +170,6 @@
     Requires(len(values) == len(bads))
     Requires(n >= 1)
     Requires(modulus >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(values), 1 / 2))
@@ -192,12 +189,6 @@
     Ensures(rows_assigned(ToSeq(Result()), n))
     # post-conditions-end
     # impl-start
-    # Build the per-element special-row assignment input-by-input, mirroring the
-    # element-wise array operation, then carry it out on a container that admits
-    # every special index it writes. The special indices are the under-range row
-    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
-    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
-    # admits the whole assignment -- the input's own container may be narrower.
     sel_values = []  # type: List[int]
     sel_bads = []  # type: List[bool]
     i = len(values)
@@ -213,7 +204,6 @@
         Invariant(len(sel_bads) == len(bads) - i)
         Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
         Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         v = values[i - 1]
         bad = bads[i - 1]
@@ -226,7 +216,7 @@
         i = i - 1
     Assert(ToSeq(sel_values) == ToSeq(values))
     Assert(ToSeq(sel_bads) == ToSeq(bads))
-    carrier = n + 3
+    carrier = 2 * n + 100
     result = assign_special_rows(sel_values, sel_bads, n, carrier)
     return result
     # impl-end
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # index it writes; the largest is n + 2, so the container must admit values
     # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
     Requires(modulus >= n + 3)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(values), 1 / 2))
     Ensures(Acc(list_pred(bads), 1 / 2))
     Ensures(Acc(list_pred(Result())))
@@ -172,7 +170,6 @@
     Requires(len(values) == len(bads))
     Requires(n >= 1)
     Requires(modulus >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(values), 1 / 2))
@@ -192,12 +189,6 @@
     Ensures(rows_assigned(ToSeq(Result()), n))
     # post-conditions-end
     # impl-start
-    # Build the per-element special-row assignment input-by-input, mirroring the
-    # element-wise array operation, then carry it out on a container that admits
-    # every special index it writes. The special indices are the under-range row
-    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
-    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
-    # admits the whole assignment -- the input's own container may be narrower.
     sel_values = []  # type: List[int]
     sel_bads = []  # type: List[bool]
     i = len(values)
@@ -213,7 +204,6 @@
         Invariant(len(sel_bads) == len(bads) - i)
         Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
         Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         v = values[i - 1]
         bad = bads[i - 1]
@@ -227,6 +217,7 @@
     Assert(ToSeq(sel_values) == ToSeq(values))
     Assert(ToSeq(sel_bads) == ToSeq(bads))
     carrier = n + 3
-    result = assign_special_rows(sel_values, sel_bads, n, carrier)
+    result = sel_values
+    Fold(rows_assigned(ToSeq(result), n))
     return result
     # impl-end
```

Attack 6 — `atk6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # index it writes; the largest is n + 2, so the container must admit values
     # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
     Requires(modulus >= n + 3)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(values), 1 / 2))
     Ensures(Acc(list_pred(bads), 1 / 2))
     Ensures(Acc(list_pred(Result())))
@@ -172,7 +170,6 @@
     Requires(len(values) == len(bads))
     Requires(n >= 1)
     Requires(modulus >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(values), 1 / 2))
@@ -192,41 +189,7 @@
     Ensures(rows_assigned(ToSeq(Result()), n))
     # post-conditions-end
     # impl-start
-    # Build the per-element special-row assignment input-by-input, mirroring the
-    # element-wise array operation, then carry it out on a container that admits
-    # every special index it writes. The special indices are the under-range row
-    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
-    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
-    # admits the whole assignment -- the input's own container may be narrower.
-    sel_values = []  # type: List[int]
-    sel_bads = []  # type: List[bool]
-    i = len(values)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(values), 1 / 2))
-        Invariant(Acc(list_pred(bads), 1 / 2))
-        Invariant(Acc(list_pred(sel_values)))
-        Invariant(Acc(list_pred(sel_bads)))
-        Invariant(len(values) == len(bads))
-        Invariant(0 <= i and i <= len(values))
-        Invariant(len(sel_values) == len(values) - i)
-        Invariant(len(sel_bads) == len(bads) - i)
-        Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
-        Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        v = values[i - 1]
-        bad = bads[i - 1]
-        Assert(ToSeq(values).drop(i - 1)[0] == v)
-        Assert(ToSeq(values).drop(i - 1).drop(1) == ToSeq(values).drop(i))
-        Assert(ToSeq(bads).drop(i - 1)[0] == bad)
-        Assert(ToSeq(bads).drop(i - 1).drop(1) == ToSeq(bads).drop(i))
-        sel_values = [v] + sel_values
-        sel_bads = [bad] + sel_bads
-        i = i - 1
-    Assert(ToSeq(sel_values) == ToSeq(values))
-    Assert(ToSeq(sel_bads) == ToSeq(bads))
-    carrier = n + 3
-    result = assign_special_rows(sel_values, sel_bads, n, carrier)
+
+    result = assign_special_rows(values, bads, n, n + 3)
     return result
     # impl-end
```

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # index it writes; the largest is n + 2, so the container must admit values
     # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
     Requires(modulus >= n + 3)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(values), 1 / 2))
     Ensures(Acc(list_pred(bads), 1 / 2))
     Ensures(Acc(list_pred(Result())))
@@ -172,7 +170,6 @@
     Requires(len(values) == len(bads))
     Requires(n >= 1)
     Requires(modulus >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(values), 1 / 2))
@@ -192,12 +189,6 @@
     Ensures(rows_assigned(ToSeq(Result()), n))
     # post-conditions-end
     # impl-start
-    # Build the per-element special-row assignment input-by-input, mirroring the
-    # element-wise array operation, then carry it out on a container that admits
-    # every special index it writes. The special indices are the under-range row
-    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
-    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
-    # admits the whole assignment -- the input's own container may be narrower.
     sel_values = []  # type: List[int]
     sel_bads = []  # type: List[bool]
     i = len(values)
@@ -213,7 +204,6 @@
         Invariant(len(sel_bads) == len(bads) - i)
         Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
         Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         v = values[i - 1]
         bad = bads[i - 1]
@@ -226,7 +216,9 @@
         i = i - 1
     Assert(ToSeq(sel_values) == ToSeq(values))
     Assert(ToSeq(sel_bads) == ToSeq(bads))
-    carrier = n + 3
+    carrier = modulus
+    if carrier < 1:
+        carrier = 1
     result = assign_special_rows(sel_values, sel_bads, n, carrier)
     return result
     # impl-end
```

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -99,7 +98,6 @@
     # index it writes; the largest is n + 2, so the container must admit values
     # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
     Requires(modulus >= n + 3)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(values), 1 / 2))
     Ensures(Acc(list_pred(bads), 1 / 2))
     Ensures(Acc(list_pred(Result())))
@@ -172,7 +170,6 @@
     Requires(len(values) == len(bads))
     Requires(n >= 1)
     Requires(modulus >= 1)
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(values), 1 / 2))
@@ -213,7 +210,6 @@
         Invariant(len(sel_bads) == len(bads) - i)
         Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
         Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         v = values[i - 1]
         bad = bads[i - 1]
@@ -226,7 +222,10 @@
         i = i - 1
     Assert(ToSeq(sel_values) == ToSeq(values))
     Assert(ToSeq(sel_bads) == ToSeq(bads))
-    carrier = n + 3
+    # Carry out the assignment on the input's OWN integer container (no change to
+    # its range): the special indices are assigned through the container of range
+    # modulus, whatever its width.
+    carrier = modulus
     result = assign_special_rows(sel_values, sel_bads, n, carrier)
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24970.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A colormap maps each data value to a row of a lookup table that has ``N``
  ordinary colour rows (indices ``0 .. N-1``) followed by three special rows:
  the under-range row at index ``N``, the over-range row at index ``N + 1`` and
  the bad/masked row at index ``N + 2``.

  For one element the final lookup row is determined as follows. The element
  carries an integer value ``v`` (for floating inputs this is the
  scaled-and-clipped value). The three special rows are applied in turn --
  over-range, then under-range, then bad -- so they take this precedence: a
  bad/masked element selects the bad row ``N + 2`` regardless of ``v``;
  otherwise an out-of-range-high value (``v > N - 1``) selects the over-range
  row ``N + 1``; otherwise a negative value (``v < 0``) selects the under-range
  row ``N``; any remaining in-range value keeps its own index ``v``. The
  selected index is then clipped into the valid table-row range ``0 .. N + 2``.

  The required behaviour is that this row assignment COMPLETES for any data
  value of any integer width -- in particular it must not perform an operation
  that is only conditionally valid for the data's integer container. Assigning
  the special row indices is such an operation: an integer container only
  admits an index it can represent, and the special indices run up to ``N + 2``.
  The operation must therefore be carried out on a container that admits every
  index it assigns (an index of ``N + 2`` requires a container that admits
  values up to ``N + 2``); a container that admits only a narrower range than
  the special indices it is asked to hold does not admit the assignment. The
  result is required to be one produced BY such an admitting assignment, so the
  whole operation completes for every input width rather than for some widths
  only.

The data array is modelled as ``List[int]`` of per-element integer values plus
a parallel ``List[bool]`` mask. ``modulus`` abstracts the range of values the
INPUT integer container admits (a container admitting ``modulus`` distinct
values represents ``0 .. modulus - 1``). The pure sequence theory ``PSeq[int]``
carries the per-element specification.

The per-element row assignment over the array is an UNCHANGED integer-array
operation; it is modelled as a callee ``assign_special_rows`` whose contract
captures both its result (the per-element selected-and-clipped rows) and the
EFFECT that distinguishes a completing assignment from a non-completing one --
it is well-defined (it grants the unforgeable ``rows_assigned`` token) ONLY when
the container it writes into admits every special index it assigns. The result's
postcondition REQUIRES that token, so a verifying operation must route its
result through an admitting assignment; it cannot return a row sequence that no
admitting assignment produced. No callee under change is axiomatized; the
callee's contract is validated against the real integer-array operation
out-of-band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# Abstract token marking a row sequence PRODUCED BY a well-defined per-element
# special-row assignment for a table of ``n`` ordinary rows: a capability the
# assignment grants on its output, that nothing else can fabricate. Its
# arguments record the produced rows and the table size. The result of the
# whole operation must hold this token, so the result can only be a row sequence
# an admitting assignment actually produced -- an assignment into a container
# that does not admit the special indices it must hold is not well-defined and
# never grants it. Provenance + executable soundness check: mapping.md /
# axiom_check.py.
@ContractOnly
@Predicate
def rows_assigned(rows: PSeq[int], n: int) -> bool:
    pass

@ContractOnly
def assign_special_rows(values: List[int], bads: List[bool], n: int,
                        modulus: int) -> List[int]:
    """The per-element special-row assignment over the whole array (the
    UNCHANGED integer-array operation: write the special indices for the
    out-of-range / masked elements, then clip into the table-row range). It is
    carried out on an integer container that admits ``0 .. modulus - 1``.

    The assignment is only WELL-DEFINED -- actually yielding a row sequence and
    granting the ``rows_assigned`` token -- when that container admits every
    special index it assigns. The largest special index is ``n + 2``, so the
    container must admit values up to ``n + 2``; that is the precondition
    ``modulus >= n + 3``. A container narrower than the special indices it is
    asked to hold does not admit the assignment, so this contract does not apply
    to it (the operation is not well-defined there). On a well-defined
    assignment it returns the per-element selected-and-clipped rows AND grants
    the ``rows_assigned`` token on its output for this table size. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(Acc(list_pred(bads), 1 / 2))
    Requires(len(values) == len(bads))
    Requires(len(ToSeq(values)) == len(ToSeq(bads)))
    Requires(n >= 1)
    # A well-defined assignment requires the container to admit every special
    # index it writes; the largest is n + 2, so the container must admit values
    # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
    Requires(modulus >= n + 3)
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(bads), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(values))
    Ensures(len(ToSeq(values)) == len(ToSeq(bads)))
    # The well-defined assignment yields exactly the per-element rows...
    Ensures(ToSeq(Result()) == rows_of(ToSeq(values), ToSeq(bads), n))
    # ...and grants the token marking it as an admitting assignment's output.
    Ensures(rows_assigned(ToSeq(Result()), n))
# axioms-end

# pure-start
@Pure
def selected_index(v: int, n: int, bad: bool) -> int:
    """The special-or-ordinary row index selected for one element, before it is
    clipped into the table. The three special rows are applied in turn
    (over-range, then under-range, then bad), so the bad row has the highest
    precedence, then over-range, then under-range; any remaining in-range value
    keeps its own index."""
    Requires(n >= 1)
    if bad:
        return n + 2            # bad/masked row (applied last, wins)
    if v > n - 1:
        return n + 1            # over-range row
    if v < 0:
        return n                # under-range row
    return v                    # ordinary in-range index

@Pure
def clip_row(idx: int, n: int) -> int:
    """Clip a row index to the valid lookup-table row range ``0 .. N+2`` (the
    ``mode='clip'`` of the row gather)."""
    Requires(n >= 1)
    if idx < 0:
        return 0
    if idx > n + 2:
        return n + 2
    return idx

@Pure
def final_row(v: int, n: int, bad: bool) -> int:
    """The lookup-table row a single element ends up at: select the row, then
    clip into range. Every selected index already lies in ``0 .. N+2``, so this
    is exactly the selected index."""
    Requires(n >= 1)
    return clip_row(selected_index(v, n, bad), n)

@Pure
def rows_of(vs: PSeq[int], bs: PSeq[bool], n: int) -> PSeq[int]:
    """The row sequence for a whole element sequence: the per-element
    final_row of each element. Front-recursive so a single unfold is available
    per loop step."""
    Requires(n >= 1)
    Requires(len(vs) == len(bs))
    if len(vs) == 0:
        return PSeq(0).take(0)
    return PSeq(final_row(vs[0], n, bs[0])) + rows_of(vs.drop(1), bs.drop(1), n)
# pure-end

def take_rows(values: List[int], bads: List[bool], n: int,
              modulus: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(Acc(list_pred(bads), 1 / 2))
    Requires(len(values) == len(bads))
    Requires(n >= 1)
    Requires(modulus >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(bads), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(values) == len(bads))
    Ensures(len(Result()) == len(values))
    # Every element ends at the row dictated by selection + clip.
    Ensures(ToSeq(Result()) == rows_of(ToSeq(values), ToSeq(bads), n))
    # Load-bearing: the result must be one PRODUCED BY a special-row assignment
    # that completed -- an assignment carried out on a container that admits
    # every special index it writes. The token is granted only by such an
    # admitting assignment; it cannot be discharged by value-equality alone,
    # because the row values are identical whether or not the assignment's
    # container admitted the special indices -- the discriminator is the
    # completing-assignment effect, not a row value.
    Ensures(rows_assigned(ToSeq(Result()), n))
    # post-conditions-end
    # impl-start
    # Build the per-element special-row assignment input-by-input, mirroring the
    # element-wise array operation, then carry it out on a container that admits
    # every special index it writes. The special indices are the under-range row
    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
    # admits the whole assignment -- the input's own container may be narrower.
    sel_values = []  # type: List[int]
    sel_bads = []  # type: List[bool]
    i = len(values)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(Acc(list_pred(bads), 1 / 2))
        Invariant(Acc(list_pred(sel_values)))
        Invariant(Acc(list_pred(sel_bads)))
        Invariant(len(values) == len(bads))
        Invariant(0 <= i and i <= len(values))
        Invariant(len(sel_values) == len(values) - i)
        Invariant(len(sel_bads) == len(bads) - i)
        Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
        Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
        # invariants-end
        v = values[i - 1]
        bad = bads[i - 1]
        Assert(ToSeq(values).drop(i - 1)[0] == v)
        Assert(ToSeq(values).drop(i - 1).drop(1) == ToSeq(values).drop(i))
        Assert(ToSeq(bads).drop(i - 1)[0] == bad)
        Assert(ToSeq(bads).drop(i - 1).drop(1) == ToSeq(bads).drop(i))
        sel_values = [v] + sel_values
        sel_bads = [bad] + sel_bads
        i = i - 1
    Assert(ToSeq(sel_values) == ToSeq(values))
    Assert(ToSeq(sel_bads) == ToSeq(bads))
    carrier = n + 3
    result = assign_special_rows(sel_values, sel_bads, n, carrier)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Toolchain confirmed: positive_control (frozen model.py) VERIFIED in 14.7s; prepatch bug reproduced (atk_prepatch.py = model_prepatch.py, same-spec SAME, weakness -> does NOT verify: narrow carrier=modulus cannot satisfy assign_special_rows Requires(modulus>=n+3), so the rows_assigned token is never granted). G-AX axiom_check.py RC=0 (numpy 1.26.4): final_row == real widened NumPy pipeline (48 boundary + 20000 fuzz); modulus>=n+3 is the weakest-sufficient no-deprecation legality precondition across uint8/uint16/int8/int16; F2P witness holds.

Attack surface: the impl region's only real degree of freedom is the carrier width passed to assign_special_rows plus the reconstruction loop. Verification requires the unforgeable rows_assigned token (@ContractOnly @Predicate), obtainable ONLY from assign_special_rows under Requires(modulus>=n+3); result rows are pinned to rows_of(...).

REJECTED (spec correctly rejects, exit 2 / does not verify): atk1 carrier=n+2 (just below threshold -> precondition unmet); atk2 returns reconstructed input (loses token + wrong rows); atk5 ungrounded-oracle echo: builds fresh seq and Fold(rows_assigned(...)) -> cannot forge the ContractOnly predicate; atk7 carrier=modulus (max with 1) -> still narrow, precondition unmet (prepatch class).

CANDIDATES (share spec AND verify, exit 0): atk3 conditional carrier (keep modulus if >=n+3 else n+3); atk4 over-wide carrier 2*n+100; atk6 direct call assign_special_rows(values,bads,n,n+3) skipping the loop. All three choose a carrier that admits every special index (>= n+3) for ALL inputs, i.e. exactly gold's 'cast xa to int before the special-row writes' (refinement.md A6). Per protocol, materialized each candidate's faithful refined patch and RAN it through the official harness (run_resolve, swe_bench_verified, docker oracle):
  - faithful_atk4.diff / faithful_atk6.diff (byte-identical to gold patch.diff): run_resolve -> resolved=true, completed=true, attempts=1, flaky=false.
  - faithful_atk3.diff (distinct: conditional cast, casts only when input dtype cannot hold N+2): run_resolve -> resolved=true, completed=true, attempts=1, flaky=false.
Every verifying wrong-impl's faithful patch RESOLVES => verify does not admit a non-resolving impl on this spec. No break.

refinement.md leg audit: A1-A5 R (array/dtype/N type refinements + faithful element-wise materialization loop); A6 R (carrier-width choice <-> gold astype(int) hoisted before special-row writes); A7 A-consumed (assign_special_rows = UNCHANGED NumPy 3 sequential special-row stores _i_over/_i_under/_i_bad in order + lut.take(mode='clip'), consumes Ensures row-result + rows_assigned token, gated by Requires(modulus>=n+3)). No kind-3 leg; no axiom about the function under change. A7 correspondence to the real callee validated by G-AX (RC=0). All legs R/A-consumed/I; correspondence holds.

Commands (PATH prepend; nagini via ~/miniconda3/envs/swebench-nagini-verifier shim):
  same-spec/weakness: python -m swebench_unified.adversary {same-spec,weakness} nagini matplotlib__matplotlib-24970 <N>.py
  resolve: ... python run_resolve.py <label> <faithful_diff> (SBU_BENCHMARK_DIR set).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk1.py`, `atk2.py`, `atk5.py`, `atk7.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk3.py`, `atk4.py`, `atk6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24970.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A colormap maps each data value to a row of a lookup table that has ``N``
  ordinary colour rows (indices ``0 .. N-1``) followed by three special rows:
  the under-range row at index ``N``, the over-range row at index ``N + 1`` and
  the bad/masked row at index ``N + 2``.

  For one element the final lookup row is determined as follows. The element
  carries an integer value ``v`` (for floating inputs this is the
  scaled-and-clipped value). The three special rows are applied in turn --
  over-range, then under-range, then bad -- so they take this precedence: a
  bad/masked element selects the bad row ``N + 2`` regardless of ``v``;
  otherwise an out-of-range-high value (``v > N - 1``) selects the over-range
  row ``N + 1``; otherwise a negative value (``v < 0``) selects the under-range
  row ``N``; any remaining in-range value keeps its own index ``v``. The
  selected index is then clipped into the valid table-row range ``0 .. N + 2``.

  The required behaviour is that this row assignment COMPLETES for any data
  value of any integer width -- in particular it must not perform an operation
  that is only conditionally valid for the data's integer container. Assigning
  the special row indices is such an operation: an integer container only
  admits an index it can represent, and the special indices run up to ``N + 2``.
  The operation must therefore be carried out on a container that admits every
  index it assigns (an index of ``N + 2`` requires a container that admits
  values up to ``N + 2``); a container that admits only a narrower range than
  the special indices it is asked to hold does not admit the assignment. The
  result is required to be one produced BY such an admitting assignment, so the
  whole operation completes for every input width rather than for some widths
  only.

The data array is modelled as ``List[int]`` of per-element integer values plus
a parallel ``List[bool]`` mask. ``modulus`` abstracts the range of values the
INPUT integer container admits (a container admitting ``modulus`` distinct
values represents ``0 .. modulus - 1``). The pure sequence theory ``PSeq[int]``
carries the per-element specification.

The per-element row assignment over the array is an UNCHANGED integer-array
operation; it is modelled as a callee ``assign_special_rows`` whose contract
captures both its result (the per-element selected-and-clipped rows) and the
EFFECT that distinguishes a completing assignment from a non-completing one --
it is well-defined (it grants the unforgeable ``rows_assigned`` token) ONLY when
the container it writes into admits every special index it assigns. The result's
postcondition REQUIRES that token, so a verifying operation must route its
result through an admitting assignment; it cannot return a row sequence that no
admitting assignment produced. No callee under change is axiomatized; the
callee's contract is validated against the real integer-array operation
out-of-band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# Abstract token marking a row sequence PRODUCED BY a well-defined per-element
# special-row assignment for a table of ``n`` ordinary rows: a capability the
# assignment grants on its output, that nothing else can fabricate. Its
# arguments record the produced rows and the table size. The result of the
# whole operation must hold this token, so the result can only be a row sequence
# an admitting assignment actually produced -- an assignment into a container
# that does not admit the special indices it must hold is not well-defined and
# never grants it. Provenance + executable soundness check: mapping.md /
# axiom_check.py.
@ContractOnly
@Predicate
def rows_assigned(rows: PSeq[int], n: int) -> bool:
    pass

@ContractOnly
def assign_special_rows(values: List[int], bads: List[bool], n: int,
                        modulus: int) -> List[int]:
    """The per-element special-row assignment over the whole array (the
    UNCHANGED integer-array operation: write the special indices for the
    out-of-range / masked elements, then clip into the table-row range). It is
    carried out on an integer container that admits ``0 .. modulus - 1``.

    The assignment is only WELL-DEFINED -- actually yielding a row sequence and
    granting the ``rows_assigned`` token -- when that container admits every
    special index it assigns. The largest special index is ``n + 2``, so the
    container must admit values up to ``n + 2``; that is the precondition
    ``modulus >= n + 3``. A container narrower than the special indices it is
    asked to hold does not admit the assignment, so this contract does not apply
    to it (the operation is not well-defined there). On a well-defined
    assignment it returns the per-element selected-and-clipped rows AND grants
    the ``rows_assigned`` token on its output for this table size. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(Acc(list_pred(bads), 1 / 2))
    Requires(len(values) == len(bads))
    Requires(len(ToSeq(values)) == len(ToSeq(bads)))
    Requires(n >= 1)
    # A well-defined assignment requires the container to admit every special
    # index it writes; the largest is n + 2, so the container must admit values
    # up to n + 2 (modulus >= n + 3). A narrower container does not admit it.
    Requires(modulus >= n + 3)
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(bads), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(values))
    Ensures(len(ToSeq(values)) == len(ToSeq(bads)))
    # The well-defined assignment yields exactly the per-element rows...
    Ensures(ToSeq(Result()) == rows_of(ToSeq(values), ToSeq(bads), n))
    # ...and grants the token marking it as an admitting assignment's output.
    Ensures(rows_assigned(ToSeq(Result()), n))
# axioms-end

# pure-start
@Pure
def selected_index(v: int, n: int, bad: bool) -> int:
    """The special-or-ordinary row index selected for one element, before it is
    clipped into the table. The three special rows are applied in turn
    (over-range, then under-range, then bad), so the bad row has the highest
    precedence, then over-range, then under-range; any remaining in-range value
    keeps its own index."""
    Requires(n >= 1)
    if bad:
        return n + 2            # bad/masked row (applied last, wins)
    if v > n - 1:
        return n + 1            # over-range row
    if v < 0:
        return n                # under-range row
    return v                    # ordinary in-range index

@Pure
def clip_row(idx: int, n: int) -> int:
    """Clip a row index to the valid lookup-table row range ``0 .. N+2`` (the
    ``mode='clip'`` of the row gather)."""
    Requires(n >= 1)
    if idx < 0:
        return 0
    if idx > n + 2:
        return n + 2
    return idx

@Pure
def final_row(v: int, n: int, bad: bool) -> int:
    """The lookup-table row a single element ends up at: select the row, then
    clip into range. Every selected index already lies in ``0 .. N+2``, so this
    is exactly the selected index."""
    Requires(n >= 1)
    return clip_row(selected_index(v, n, bad), n)

@Pure
def rows_of(vs: PSeq[int], bs: PSeq[bool], n: int) -> PSeq[int]:
    """The row sequence for a whole element sequence: the per-element
    final_row of each element. Front-recursive so a single unfold is available
    per loop step."""
    Requires(n >= 1)
    Requires(len(vs) == len(bs))
    if len(vs) == 0:
        return PSeq(0).take(0)
    return PSeq(final_row(vs[0], n, bs[0])) + rows_of(vs.drop(1), bs.drop(1), n)
# pure-end

def take_rows(values: List[int], bads: List[bool], n: int,
              modulus: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(Acc(list_pred(bads), 1 / 2))
    Requires(len(values) == len(bads))
    Requires(n >= 1)
    Requires(modulus >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(bads), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(values) == len(bads))
    Ensures(len(Result()) == len(values))
    # Every element ends at the row dictated by selection + clip.
    Ensures(ToSeq(Result()) == rows_of(ToSeq(values), ToSeq(bads), n))
    # Load-bearing: the result must be one PRODUCED BY a special-row assignment
    # that completed -- an assignment carried out on a container that admits
    # every special index it writes. The token is granted only by such an
    # admitting assignment; it cannot be discharged by value-equality alone,
    # because the row values are identical whether or not the assignment's
    # container admitted the special indices -- the discriminator is the
    # completing-assignment effect, not a row value.
    Ensures(rows_assigned(ToSeq(Result()), n))
    # post-conditions-end
    # impl-start
    # Build the per-element special-row assignment input-by-input, mirroring the
    # element-wise array operation, then carry it out on a container that admits
    # every special index it writes. The special indices are the under-range row
    # (n), the over-range row (n + 1) and the bad/masked row (n + 2); the largest
    # is the bad row at n + 2, so a container admitting 0 .. n + 2 (range n + 3)
    # admits the whole assignment -- the input's own container may be narrower.
    sel_values = []  # type: List[int]
    sel_bads = []  # type: List[bool]
    i = len(values)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(Acc(list_pred(bads), 1 / 2))
        Invariant(Acc(list_pred(sel_values)))
        Invariant(Acc(list_pred(sel_bads)))
        Invariant(len(values) == len(bads))
        Invariant(0 <= i and i <= len(values))
        Invariant(len(sel_values) == len(values) - i)
        Invariant(len(sel_bads) == len(bads) - i)
        Invariant(ToSeq(sel_values) == ToSeq(values).drop(i))
        Invariant(ToSeq(sel_bads) == ToSeq(bads).drop(i))
        # invariants-end
        v = values[i - 1]
        bad = bads[i - 1]
        Assert(ToSeq(values).drop(i - 1)[0] == v)
        Assert(ToSeq(values).drop(i - 1).drop(1) == ToSeq(values).drop(i))
        Assert(ToSeq(bads).drop(i - 1)[0] == bad)
        Assert(ToSeq(bads).drop(i - 1).drop(1) == ToSeq(bads).drop(i))
        sel_values = [v] + sel_values
        sel_bads = [bad] + sel_bads
        i = i - 1
    Assert(ToSeq(sel_values) == ToSeq(values))
    Assert(ToSeq(sel_bads) == ToSeq(bads))
    carrier = n + 3
    result = assign_special_rows(sel_values, sel_bads, n, carrier)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Toolchain confirmed: positive_control (frozen model.py) VERIFIED in 14.7s; prepatch bug reproduced (atk_prepatch.py = model_prepatch.py, same-spec SAME, weakness -> does NOT verify: narrow carrier=modulus cannot satisfy assign_special_rows Requires(modulus>=n+3), so the rows_assigned token is never granted). G-AX axiom_check.py RC=0 (numpy 1.26.4): final_row == real widened NumPy pipeline (48 boundary + 20000 fuzz); modulus>=n+3 is the weakest-sufficient no-deprecation legality precondition across uint8/uint16/int8/int16; F2P witness holds.

Attack surface: the impl region's only real degree of freedom is the carrier width passed to assign_special_rows plus the reconstruction loop. Verification requires the unforgeable rows_assigned token (@ContractOnly @Predicate), obtainable ONLY from assign_special_rows under Requires(modulus>=n+3); result rows are pinned to rows_of(...).

REJECTED (spec correctly rejects, exit 2 / does not verify): atk1 carrier=n+2 (just below threshold -> precondition unmet); atk2 returns reconstructed input (loses token + wrong rows); atk5 ungrounded-oracle echo: builds fresh seq and Fold(rows_assigned(...)) -> cannot forge the ContractOnly predicate; atk7 carrier=modulus (max with 1) -> still narrow, precondition unmet (prepatch class).

CANDIDATES (share spec AND verify, exit 0): atk3 conditional carrier (keep modulus if >=n+3 else n+3); atk4 over-wide carrier 2*n+100; atk6 direct call assign_special_rows(values,bads,n,n+3) skipping the loop. All three choose a carrier that admits every special index (>= n+3) for ALL inputs, i.e. exactly gold's 'cast xa to int before the special-row writes' (refinement.md A6). Per protocol, materialized each candidate's faithful refined patch and RAN it through the official harness (run_resolve, swe_bench_verified, docker oracle):
  - faithful_atk4.diff / faithful_atk6.diff (byte-identical to gold patch.diff): run_resolve -> resolved=true, completed=true, attempts=1, flaky=false.
  - faithful_atk3.diff (distinct: conditional cast, casts only when input dtype cannot hold N+2): run_resolve -> resolved=true, completed=true, attempts=1, flaky=false.
Every verifying wrong-impl's faithful patch RESOLVES => verify does not admit a non-resolving impl on this spec. No break.

refinement.md leg audit: A1-A5 R (array/dtype/N type refinements + faithful element-wise materialization loop); A6 R (carrier-width choice <-> gold astype(int) hoisted before special-row writes); A7 A-consumed (assign_special_rows = UNCHANGED NumPy 3 sequential special-row stores _i_over/_i_under/_i_bad in order + lut.take(mode='clip'), consumes Ensures row-result + rows_assigned token, gated by Requires(modulus>=n+3)). No kind-3 leg; no axiom about the function under change. A7 correspondence to the real callee validated by G-AX (RC=0). All legs R/A-consumed/I; correspondence holds.

Commands (PATH prepend; nagini via ~/miniconda3/envs/swebench-nagini-verifier shim):
  same-spec/weakness: python -m swebench_unified.adversary {same-spec,weakness} nagini matplotlib__matplotlib-24970 <N>.py
  resolve: ... python run_resolve.py <label> <faithful_diff> (SBU_BENCHMARK_DIR set).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function take_rows ↔ Colormap.__call__ integer index-resolution stage (post-patch), lib/matplotlib/colors.py:683. Faithfulness verified rigorously:

1) VALUE AGREEMENT: reimplemented the real post-patch NumPy pipeline over WHOLE arrays (astype(int) → sequential stores xa[xa>N-1]=N+1, xa[xa<0]=N, xa[mask]=N+2, in that exact order → clip to 0..N+2) and compared against the model's rows_of/final_row spec over 200,000 random (n∈[1,50], length∈[0,8], v∈[-10,n+10], bad~0.3) cases. 0 mismatches. This exercises the load-bearing sequential-store interaction (over before under before bad) that the model's selected_index precedence reproduces exactly.

2) DISCRIMINATOR: the gold patch's real effect (widen carrier so special-row stores are in-range → no out-of-bound DeprecationWarning under filterwarnings=error) is value-invisible on the F2P input cm(uint8(0)) (row 0 either way). The spec correctly models it as the unforgeable rows_assigned @ContractOnly @Predicate token, not a value property. Matches the real pre/post distinction.

3) G-AX: axiom_check.py exits 0 (48 boundary + 20000 fuzz result agreement; legality threshold coincides exactly with no-deprecation across uint8/uint16/int8/int16; F2P witness confirmed against numpy 1.26.4).

4) NON-VACUITY: model.py verifies (RC=0, 12.4s); token is @ContractOnly so it cannot be forged/folded, and carries rows+n so cannot be laundered across a value-equal copy.

EXAMINED NON-ISSUE: for signed dtypes the abstract precondition modulus>=n+3 diverges from the real 'container admits n+2' threshold near dtype max (e.g. int8, N=126: modulus=256>=129 true, but n+2=128>127 does not fit). However (a) this lives in the callee's abstract precondition, not the modeled function's behavior; (b) take_rows NEVER consumes its own modulus argument — it always sets carrier=n+3 internally; (c) the real post-patch code always casts to int64, so it always completes regardless of input dtype. The modeled function's observable output (rows_of value + guaranteed token) matches the real post-patch __call__ on every input. Not a behavioral divergence of the modeled function; the spec is not too strong. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures): no gold-diff line reproduced, no diff markers, no patched file path (lib/matplotlib/colors.py) or module, no patched-symbol echo (__call__ is non-distinctive/allowlisted), no bug/fix narration in spec-view comments/docstrings. Bundle is NOT relaxed (relaxed_leakage=None, meta G-LEAK status=pass), so no RELAXED_LEAKAGE deferral is in play.

Semantic review (the real G-PANEL-3 question): the spec view formalizes the special-row indices (N under, N+1 over, N+2 bad), the over->under->bad precedence, the clip into 0..N+2, and the load-bearing requirement that the row-assignment must be carried out on a container that admits every special index so it COMPLETES for any integer width.

Every one of these facts is already public in the problem_statement: the three failing NumPy assignments (xa[xa > self.N - 1] = self._i_over, xa[xa < 0] = self._i_under, xa[mask_bad] = self._i_bad) are quoted verbatim in the deprecation-warning traceback, and 'conversion of 257/256/258 to uint8 will fail' + 'Expected outcome: No warnings' already discloses that the narrow (uint8) container cannot represent the special indices and that the operation must complete for all widths. The spec restates that desired behavior faithfully WITHOUT revealing the gold fix mechanism: it never mentions astype(int), the relocation of the int cast out of the float-only branch, np.errstate, or the colors.py path/module.

The concrete fix embodiment (carrier = n + 3, routing the result through an admitting assignment) lives entirely in the elided impl region, not the spec view. Nothing in the spec view reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).