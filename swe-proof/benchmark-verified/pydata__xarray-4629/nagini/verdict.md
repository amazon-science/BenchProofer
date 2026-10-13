# P2 adversarial audit — pydata__xarray-4629

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 DROP = 0
 OVERRIDE = 1
@@ -67,7 +66,6 @@
     Requires(mode == DROP or mode == OVERRIDE)
     # The leading source mapping is read-only: fractional permission.
     Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(variable_attrs), 1 / 2))
@@ -91,20 +89,5 @@
     if mode == DROP:
         empty = []  # type: List[int]
         return empty
-    src = variable_attrs[0]  # type: List[int]
-    result = []  # type: List[int]
-    i = 0
-    while i < len(src):
-        # invariants-start
-        Invariant(Acc(list_pred(src), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(result is not src)
-        Invariant(0 <= i and i <= len(src))
-        Invariant(len(result) == i)
-        Invariant(ToSeq(result) == ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
-        result.append(src[i])
-        i = i + 1
-    return result
+    return variable_attrs[0]
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 DROP = 0
 OVERRIDE = 1
@@ -67,7 +66,6 @@
     Requires(mode == DROP or mode == OVERRIDE)
     # The leading source mapping is read-only: fractional permission.
     Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(variable_attrs), 1 / 2))
@@ -88,22 +86,16 @@
                     ToSeq(Result()) == ToSeq(variable_attrs[0])))
     # post-conditions-end
     # impl-start
-    if mode == DROP:
-        empty = []  # type: List[int]
-        return empty
     src = variable_attrs[0]  # type: List[int]
     result = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(result is not src)
         Invariant(0 <= i and i <= len(src))
         Invariant(len(result) == i)
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         result.append(src[i])
         i = i + 1
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 DROP = 0
 OVERRIDE = 1
@@ -67,7 +66,6 @@
     Requires(mode == DROP or mode == OVERRIDE)
     # The leading source mapping is read-only: fractional permission.
     Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(variable_attrs), 1 / 2))
@@ -88,23 +86,6 @@
                     ToSeq(Result()) == ToSeq(variable_attrs[0])))
     # post-conditions-end
     # impl-start
-    if mode == DROP:
-        empty = []  # type: List[int]
-        return empty
-    src = variable_attrs[0]  # type: List[int]
-    result = []  # type: List[int]
-    i = 0
-    while i < len(src):
-        # invariants-start
-        Invariant(Acc(list_pred(src), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(result is not src)
-        Invariant(0 <= i and i <= len(src))
-        Invariant(len(result) == i)
-        Invariant(ToSeq(result) == ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
-        result.append(src[i])
-        i = i + 1
-    return result
+    empty = []  # type: List[int]
+    return empty
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 DROP = 0
 OVERRIDE = 1
@@ -67,7 +66,6 @@
     Requires(mode == DROP or mode == OVERRIDE)
     # The leading source mapping is read-only: fractional permission.
     Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(variable_attrs), 1 / 2))
@@ -94,16 +92,13 @@
     src = variable_attrs[0]  # type: List[int]
     result = []  # type: List[int]
     i = 0
-    while i < len(src):
-        # invariants-start
+    while i < len(src) - 1:
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(result is not src)
         Invariant(0 <= i and i <= len(src))
         Invariant(len(result) == i)
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         result.append(src[i])
         i = i + 1
     return result
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 DROP = 0
 OVERRIDE = 1
@@ -67,7 +66,6 @@
     Requires(mode == DROP or mode == OVERRIDE)
     # The leading source mapping is read-only: fractional permission.
     Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(variable_attrs), 1 / 2))
@@ -95,16 +93,14 @@
     result = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(result is not src)
         Invariant(0 <= i and i <= len(src))
         Invariant(len(result) == i)
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         result.append(src[i])
         i = i + 1
+    result.append(0)
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 DROP = 0
 OVERRIDE = 1
@@ -67,7 +66,6 @@
     Requires(mode == DROP or mode == OVERRIDE)
     # The leading source mapping is read-only: fractional permission.
     Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(variable_attrs), 1 / 2))
@@ -88,22 +86,16 @@
                     ToSeq(Result()) == ToSeq(variable_attrs[0])))
     # post-conditions-end
     # impl-start
-    if mode == DROP:
-        empty = []  # type: List[int]
-        return empty
     src = variable_attrs[0]  # type: List[int]
     result = []  # type: List[int]
     i = 0
     while i < len(src):
-        # invariants-start
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(result is not src)
         Invariant(0 <= i and i <= len(src))
         Invariant(len(result) == i)
         Invariant(ToSeq(result) == ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
         result.append(src[i])
         i = i + 1
     return result
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 DROP = 0
 OVERRIDE = 1
@@ -67,7 +66,6 @@
     Requires(mode == DROP or mode == OVERRIDE)
     # The leading source mapping is read-only: fractional permission.
     Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(variable_attrs), 1 / 2))
@@ -88,23 +86,20 @@
                     ToSeq(Result()) == ToSeq(variable_attrs[0])))
     # post-conditions-end
     # impl-start
-    if mode == DROP:
-        empty = []  # type: List[int]
-        return empty
-    src = variable_attrs[0]  # type: List[int]
-    result = []  # type: List[int]
-    i = 0
-    while i < len(src):
-        # invariants-start
-        Invariant(Acc(list_pred(src), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(result is not src)
-        Invariant(0 <= i and i <= len(src))
-        Invariant(len(result) == i)
-        Invariant(ToSeq(result) == ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
-        result.append(src[i])
-        i = i + 1
-    return result
+    if mode == OVERRIDE:
+        src = variable_attrs[0]  # type: List[int]
+        result = []  # type: List[int]
+        i = 0
+        while i < len(src):
+            Invariant(Acc(list_pred(src), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(result is not src)
+            Invariant(0 <= i and i <= len(src))
+            Invariant(len(result) == i)
+            Invariant(ToSeq(result) == ToSeq(src).take(i))
+            result.append(src[i])
+            i = i + 1
+        return result
+    empty = []  # type: List[int]
+    return empty
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 DROP = 0
 OVERRIDE = 1
@@ -67,7 +66,6 @@
     Requires(mode == DROP or mode == OVERRIDE)
     # The leading source mapping is read-only: fractional permission.
     Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(variable_attrs), 1 / 2))
@@ -93,18 +91,13 @@
         return empty
     src = variable_attrs[0]  # type: List[int]
     result = []  # type: List[int]
-    i = 0
-    while i < len(src):
-        # invariants-start
+    i = len(src) - 1
+    while i >= 0:
         Invariant(Acc(list_pred(src), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(result is not src)
-        Invariant(0 <= i and i <= len(src))
-        Invariant(len(result) == i)
-        Invariant(ToSeq(result) == ToSeq(src).take(i))
-        Invariant(MustTerminate(len(src) - i + 1))
-        # invariants-end
+        Invariant(-1 <= i and i < len(src))
         result.append(src[i])
-        i = i + 1
+        i = i - 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-4629.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A routine combines the per-source attribute mappings carried by several
  objects into a single attribute mapping for a combined object, according to a
  selected combination mode. Two of the modes are pinned here:

    * "drop" discards every attribute: the combined mapping is empty.

    * "override" adopts the leading source's attributes wholesale. The
      behaviour that matters: the combined mapping must be an INDEPENDENT
      object that merely has the same content as the leading source. A caller
      that subsequently mutates an entry of the combined mapping must NOT
      thereby change the leading source's mapping. In other words, the combined
      mapping is a copy of the leading source, not a shared reference to it.

  The consequence the specification pins down: after combining, mutating the
  result leaves every source's attribute mapping exactly as it was.

Modelling choices (Nagini fragment):
  * An attribute mapping is carried by its content sequence as a `List[int]`
    (the per-entry tokens of the mapping; the operation under specification
    cares about content equality and, decisively, OBJECT IDENTITY, both of
    which the list carrier models faithfully -- mapping.md §2). The collection
    of per-source mappings is the `List[List[int]]` argument `variable_attrs`.
  * The combination mode is an `int` token (`DROP`, `OVERRIDE`).
  * "independent copy" is expressed in separation-logic permissions: the
    read-only source keeps its fractional permission, while the result carries
    FULL permission on a DISTINCT object. A result that aliased the source
    could not hold full permission while the source retains half (they would
    sum past one) -- so the permission discipline forces a genuine copy.
  * The empty-source short-circuit and the conflict-resolving modes are
    unchanged and outside the modeled domain (precondition: at least one source
    mapping); they are not re-modelled here.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

DROP = 0
OVERRIDE = 1


# axioms-start
# No consumed axioms. The combination is the behaviour under specification and
# is modelled deeply (the impl region spells out the per-entry copy and the
# empty mapping). The list operations it composes have ordinary Python
# semantics, validated out-of-band by axiom_check.py (G-AX) as an A-reference.
# axioms-end


# pure-start
# No pure helpers: the selection and the copy are spelled out in the impl
# region; their content/identity guarantees are the postconditions.
# pure-end


def combine_attrs(variable_attrs: List[List[int]], mode: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(variable_attrs), 1 / 2))
    # At least one source mapping is present (the modeled, non-trivial domain).
    Requires(len(variable_attrs) > 0)
    Requires(mode == DROP or mode == OVERRIDE)
    # The leading source mapping is read-only: fractional permission.
    Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(variable_attrs), 1 / 2))
    Ensures(len(variable_attrs) > 0)
    # The leading source's read-only permission is returned to the caller
    # unchanged -- it is never mutated, nor handed out as the result.
    Ensures(Acc(list_pred(variable_attrs[0]), 1 / 2))
    # The result is a freshly produced mapping: FULL permission on a new object.
    Ensures(Acc(list_pred(Result())))
    # Drop mode discards every attribute: the result mapping is empty.
    Ensures(Implies(mode == DROP, len(Result()) == 0))
    # Override mode: the result is a DISTINCT object from the leading source
    # (so the source's retained half-permission and the result's full
    # permission coexist -- impossible were they the same object) ...
    Ensures(Implies(mode == OVERRIDE, Result() is not variable_attrs[0]))
    # ... with the SAME content as the leading source (a faithful copy).
    Ensures(Implies(mode == OVERRIDE,
                    ToSeq(Result()) == ToSeq(variable_attrs[0])))
    # post-conditions-end
    # impl-start
    if mode == DROP:
        empty = []  # type: List[int]
        return empty
    src = variable_attrs[0]  # type: List[int]
    result = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(result is not src)
        Invariant(0 <= i and i <= len(src))
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        result.append(src[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. No same-spec, Nagini-verifying WRONG impl exists; the sole verifying candidate is a behavioural echo of the gold whose faithful refined patch RESOLVES under the official harness.

Ran with PY=python and SBU_BENCHMARK_DIR=$PWD/benchmark-verified. patch.diff in the bundle is a placeholder; gold patch text taken from data/swe_bench_verified/test.jsonl. Spec-view regions (axioms/pure/pre/post) held byte-identical across all attacks; only the impl region + invariants were edited. same-spec confirmed for all 8 attacks + positive control.

atk_1.py PREPATCH BUG (override returns alias `return variable_attrs[0]`): same-spec, does NOT verify -> spec rejects it (cannot prove full Acc(list_pred(Result())) while source keeps 1/2). Matches model_prepatch.py impl region verbatim => prepatch reproduced, G-DIFF sound.
- atk_2.py drop returns a non-empty copy of src: same-spec, does NOT verify (violates Implies(mode==DROP, len(Result())==0)).
- atk_3.py partial-domain: override returns empty list: same-spec, does NOT verify (violates ToSeq(Result())==ToSeq(src) when src non-empty).
- atk_4.py boundary/off-by-one: copy loop `while i < len(src)-1` drops last element: same-spec, does NOT verify (ToSeq equality fails).
- atk_5.py control-flow-effect: correct copy then result.append(0) (superset): same-spec, does NOT verify (ToSeq equality fails).
- atk_6.py mode ignored (always copy, drop falls through): same-spec, does NOT verify (drop len==0 fails).
- atk_7.py ungrounded-oracle ECHO: correct per-entry copy for OVERRIDE, empty for DROP, written with reordered branch structure: same-spec AND VERIFIES => CANDIDATE (13.8s).
- atk_8.py reversed-order copy (prepend): same-spec, does NOT verify (ToSeq(Result())==ToSeq(src) fails for len>1).

MANDATORY RESOLVE for the one CANDIDATE (atk_7): its impl is behaviourally the gold combination (override->independent copy, drop->empty). Under the refinement map A4 (copy loop <-> dict(variable_attrs[0])) and B1 (empty list <-> {}), its faithful refined patch IS the gold hunk (merge.py:504 `return variable_attrs[0]` -> `return dict(variable_attrs[0])`). Materialized as patch_atk_7.diff and executed: swebench_unified.harness.run_resolve('pydata__xarray-4629', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, note='resolved' (F2P test_merge_attrs_override_copy + 32 P2P pass). Image swebench/sweb.eval.x86_64.pydata_1776_xarray-4629 present. So the only verifying impl is CORRECT: verify=>resolve holds; the spec is NOT too weak.

POSITIVE CONTROL: pos_control.py = bundle model.py verbatim; nagini_verify.sh => 'Verification successful' (13.67s), exit 0.

REFINEMENT.MD A-LEG AUDIT: legs A1/A2 = R (dict<->List[int] value carrier; str mode<->int token); A3 = R/I (index-0 selection); A4 = A-reference (spelled-out per-entry copy loop <-> real dict(variable_attrs[0]); machine-validated by G-AX/axiom_check.py, exit 0, 6 boundary + 20000 fuzz incl. exact F2P scenario: override always distinct+content-equal, mutation never reaches the source); B1 = R/I (fresh empty list <-> {}). model.py imports only typing + nagini_contracts (no @ContractOnly) => zero A-consumed axioms, consistent with refinement.md §C 'no kind-3 steps'. The value-only carrier is adequate: the modeled operation is a whole-object copy (dict(d) preserves keys by construction) and the decisive observable is object identity/aliasing, carried faithfully by Nagini reference identity + the fractional-permission discipline (aliasing the source would need 3/2 permission). A-reference correspondence to the real callee holds. axiom_check.py imports only stdlib.

CONCLUSION: 8 attacks run (>=5, distinct classes: prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, mode-insensitive, order), all verified & reported; the single CANDIDATE's materialized faithful patch executed through run_resolve and RESOLVED. No verify∧¬resolve witness exists. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-4629.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A routine combines the per-source attribute mappings carried by several
  objects into a single attribute mapping for a combined object, according to a
  selected combination mode. Two of the modes are pinned here:

    * "drop" discards every attribute: the combined mapping is empty.

    * "override" adopts the leading source's attributes wholesale. The
      behaviour that matters: the combined mapping must be an INDEPENDENT
      object that merely has the same content as the leading source. A caller
      that subsequently mutates an entry of the combined mapping must NOT
      thereby change the leading source's mapping. In other words, the combined
      mapping is a copy of the leading source, not a shared reference to it.

  The consequence the specification pins down: after combining, mutating the
  result leaves every source's attribute mapping exactly as it was.

Modelling choices (Nagini fragment):
  * An attribute mapping is carried by its content sequence as a `List[int]`
    (the per-entry tokens of the mapping; the operation under specification
    cares about content equality and, decisively, OBJECT IDENTITY, both of
    which the list carrier models faithfully -- mapping.md §2). The collection
    of per-source mappings is the `List[List[int]]` argument `variable_attrs`.
  * The combination mode is an `int` token (`DROP`, `OVERRIDE`).
  * "independent copy" is expressed in separation-logic permissions: the
    read-only source keeps its fractional permission, while the result carries
    FULL permission on a DISTINCT object. A result that aliased the source
    could not hold full permission while the source retains half (they would
    sum past one) -- so the permission discipline forces a genuine copy.
  * The empty-source short-circuit and the conflict-resolving modes are
    unchanged and outside the modeled domain (precondition: at least one source
    mapping); they are not re-modelled here.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

DROP = 0
OVERRIDE = 1


# axioms-start
# No consumed axioms. The combination is the behaviour under specification and
# is modelled deeply (the impl region spells out the per-entry copy and the
# empty mapping). The list operations it composes have ordinary Python
# semantics, validated out-of-band by axiom_check.py (G-AX) as an A-reference.
# axioms-end


# pure-start
# No pure helpers: the selection and the copy are spelled out in the impl
# region; their content/identity guarantees are the postconditions.
# pure-end


def combine_attrs(variable_attrs: List[List[int]], mode: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(variable_attrs), 1 / 2))
    # At least one source mapping is present (the modeled, non-trivial domain).
    Requires(len(variable_attrs) > 0)
    Requires(mode == DROP or mode == OVERRIDE)
    # The leading source mapping is read-only: fractional permission.
    Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(variable_attrs), 1 / 2))
    Ensures(len(variable_attrs) > 0)
    # The leading source's read-only permission is returned to the caller
    # unchanged -- it is never mutated, nor handed out as the result.
    Ensures(Acc(list_pred(variable_attrs[0]), 1 / 2))
    # The result is a freshly produced mapping: FULL permission on a new object.
    Ensures(Acc(list_pred(Result())))
    # Drop mode discards every attribute: the result mapping is empty.
    Ensures(Implies(mode == DROP, len(Result()) == 0))
    # Override mode: the result is a DISTINCT object from the leading source
    # (so the source's retained half-permission and the result's full
    # permission coexist -- impossible were they the same object) ...
    Ensures(Implies(mode == OVERRIDE, Result() is not variable_attrs[0]))
    # ... with the SAME content as the leading source (a faithful copy).
    Ensures(Implies(mode == OVERRIDE,
                    ToSeq(Result()) == ToSeq(variable_attrs[0])))
    # post-conditions-end
    # impl-start
    if mode == DROP:
        empty = []  # type: List[int]
        return empty
    src = variable_attrs[0]  # type: List[int]
    result = []  # type: List[int]
    i = 0
    while i < len(src):
        # invariants-start
        Invariant(Acc(list_pred(src), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(result is not src)
        Invariant(0 <= i and i <= len(src))
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(src).take(i))
        # invariants-end
        result.append(src[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. No same-spec, Nagini-verifying WRONG impl exists; the sole verifying candidate is a behavioural echo of the gold whose faithful refined patch RESOLVES under the official harness.

Ran with PY=python and SBU_BENCHMARK_DIR=$PWD/benchmark-verified. patch.diff in the bundle is a placeholder; gold patch text taken from data/swe_bench_verified/test.jsonl. Spec-view regions (axioms/pure/pre/post) held byte-identical across all attacks; only the impl region + invariants were edited. same-spec confirmed for all 8 attacks + positive control.

atk_1.py PREPATCH BUG (override returns alias `return variable_attrs[0]`): same-spec, does NOT verify -> spec rejects it (cannot prove full Acc(list_pred(Result())) while source keeps 1/2). Matches model_prepatch.py impl region verbatim => prepatch reproduced, G-DIFF sound.
- atk_2.py drop returns a non-empty copy of src: same-spec, does NOT verify (violates Implies(mode==DROP, len(Result())==0)).
- atk_3.py partial-domain: override returns empty list: same-spec, does NOT verify (violates ToSeq(Result())==ToSeq(src) when src non-empty).
- atk_4.py boundary/off-by-one: copy loop `while i < len(src)-1` drops last element: same-spec, does NOT verify (ToSeq equality fails).
- atk_5.py control-flow-effect: correct copy then result.append(0) (superset): same-spec, does NOT verify (ToSeq equality fails).
- atk_6.py mode ignored (always copy, drop falls through): same-spec, does NOT verify (drop len==0 fails).
- atk_7.py ungrounded-oracle ECHO: correct per-entry copy for OVERRIDE, empty for DROP, written with reordered branch structure: same-spec AND VERIFIES => CANDIDATE (13.8s).
- atk_8.py reversed-order copy (prepend): same-spec, does NOT verify (ToSeq(Result())==ToSeq(src) fails for len>1).

MANDATORY RESOLVE for the one CANDIDATE (atk_7): its impl is behaviourally the gold combination (override->independent copy, drop->empty). Under the refinement map A4 (copy loop <-> dict(variable_attrs[0])) and B1 (empty list <-> {}), its faithful refined patch IS the gold hunk (merge.py:504 `return variable_attrs[0]` -> `return dict(variable_attrs[0])`). Materialized as patch_atk_7.diff and executed: swebench_unified.harness.run_resolve('pydata__xarray-4629', patch, timeout=1800) => RESOLVED=True, COMPLETED=True, attempts=1, flaky=False, note='resolved' (F2P test_merge_attrs_override_copy + 32 P2P pass). Image swebench/sweb.eval.x86_64.pydata_1776_xarray-4629 present. So the only verifying impl is CORRECT: verify=>resolve holds; the spec is NOT too weak.

POSITIVE CONTROL: pos_control.py = bundle model.py verbatim; nagini_verify.sh => 'Verification successful' (13.67s), exit 0.

REFINEMENT.MD A-LEG AUDIT: legs A1/A2 = R (dict<->List[int] value carrier; str mode<->int token); A3 = R/I (index-0 selection); A4 = A-reference (spelled-out per-entry copy loop <-> real dict(variable_attrs[0]); machine-validated by G-AX/axiom_check.py, exit 0, 6 boundary + 20000 fuzz incl. exact F2P scenario: override always distinct+content-equal, mutation never reaches the source); B1 = R/I (fresh empty list <-> {}). model.py imports only typing + nagini_contracts (no @ContractOnly) => zero A-consumed axioms, consistent with refinement.md §C 'no kind-3 steps'. The value-only carrier is adequate: the modeled operation is a whole-object copy (dict(d) preserves keys by construction) and the decisive observable is object identity/aliasing, carried faithfully by Nagini reference identity + the fractional-permission discipline (aliasing the source would need 3/2 permission). A-reference correspondence to the real callee holds. axiom_check.py imports only stdlib.

CONCLUSION: 8 attacks run (>=5, distinct classes: prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, mode-insensitive, order), all verified & reported; the single CANDIDATE's materialized faithful patch executed through run_resolve and RESOLVED. No verify∧¬resolve witness exists. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for pydata__xarray-4629 nagini bundle.

Modeled function: combine_attrs(variable_attrs: List[List[int]], mode: int). Real callee: xarray/core/merge.py::merge_attrs(variable_attrs, combine_attrs) at base_commit a41edc7 (verified worktree). Modeled domain = preconditions: len(variable_attrs)>0 and mode in {DROP=0, OVERRIDE=1}, with fractional read-permission on variable_attrs[0].

Spec pins (postconditions): drop -> fresh empty mapping (full perm, distinct object, len==0); override -> Result() is not variable_attrs[0] AND ToSeq(Result())==ToSeq(variable_attrs[0]) with full permission on the fresh result while the source retains its 1/2 read permission.

Real post-patch behaviour (base worktree + gold patch): drop -> `return {}`; override -> `return dict(variable_attrs[0])`. Confirmed the pre-patch code was `elif combine_attrs=='override': return variable_attrs[0]` (alias) and the gold hunk wraps it in dict(...). These agree with the spec exactly on the modeled domain: dict(d) is a distinct object (dict(d) is not d) with equal content (dict(d)==d), insertion-order preserving, so mutating the result cannot reach the source.

Checks performed and PASSED:
1. Model verifies with the pinned Nagini verifier (exit 0, 16.4s).
2. same_spec(model, model_prepatch, nagini) == True; spec_view is clean (impl elided, no leakage). Spec region byte-identical between model and prepatch.
3. axiom_check.py (G-AX A-reference) executes the REAL patched merge_attrs over 6 boundary + 20000 fuzz inputs, asserting drop->fresh-empty and override->distinct+content-equal with mutation-of-result never touching the leading source, including the exact F2P test_merge_attrs_override_copy scenario. Exit 0.
4. Domain restriction is sound: the excluded branches (empty short-circuit merge.py:497-499, no_conflicts, identical) are genuinely unchanged by the patch and orthogonal to tested behaviour; no_conflicts/identical already open with dict(variable_attrs[0]) at base_commit (lines 506,517).

No over-constraint found: the spec demands exactly and only what the real dict(...) copy provides (distinct object + equal content). I searched for a diverging input within the modeled domain and found none. The type refinement (dict carried by List[int] content sequence, mode carried by int token, identity carried by Nagini reference identity + fractional permission) is faithful for the tested read/copy/identity behaviour, which never indexes a specific key.

Verdict: FAITHFUL. The modeled function agrees with the real post-patch callee on every input in the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already discloses the gold edit in full and verbatim: it names the exact file line (merge.py#L504), the buggy code `return variable_attrs[0]`, the precise replacement `return dict(variable_attrs[0])`, the reference to the other combine_attrs cases, and the desired behavior (mutating the merged product must not affect the source, with a copy-pastable MCVE). The gold patch is exactly that one-line change. Since the leakage bar is 'beyond the public problem_statement', nothing in the spec view can leak beyond a baseline that already states the edit word-for-word. The model.py spec region (pre/post-conditions of combine_attrs) encodes only that same behavior at a MORE abstract level than the problem_statement: OVERRIDE -> a DISTINCT object (Result() is not variable_attrs[0]) with equal content (ToSeq equality) and full permission while the source keeps 1/2 read permission (independent copy); DROP -> empty mapping. All carried through List[int]/int-token abstractions rather than the concrete Python edit the issue quotes. refinement.md and mapping.md do quote the gold hunk `return variable_attrs[0]` -> `return dict(variable_attrs[0])` verbatim, but (a) these are audit/refinement artifacts, not the primary spec-view under scrutiny, and (b) `dict(variable_attrs[0])` appears explicitly in the public problem_statement, so they reveal nothing beyond it. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
