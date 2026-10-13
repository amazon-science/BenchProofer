# P2 adversarial audit — astropy__astropy-13236

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5b.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,21 +194,15 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 1 (prepatch bug): re-adds the DELETED structured-ndarray clause,
+    # diverting a non-column non-mixin structured ndarray into KIND_MIXIN.
+    data_is_mixin = is_mixin
+    if (not is_column) and (not data_is_mixin) and is_ndarray and is_structured:
+        data_is_mixin = True
     if is_column:
         if is_masked:
             return KIND_MASKED()
         return KIND_COLUMN()
-    data_is_mixin = is_mixin
     if data_is_mixin:
         return KIND_MIXIN()
     if data0_is_mixin and elem_cls_builds:
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,21 +194,17 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 2 (boundary, half-fix): the override survives only for MASKED
+    # structured arrays, so test_ndarray_mixin[False] passes but
+    # test_structured_masked_column would get an NdarrayMixin.
+    data_is_mixin = is_mixin
+    if (not is_column) and (not data_is_mixin) and is_ndarray \
+            and is_structured and is_masked:
+        data_is_mixin = True
     if is_column:
         if is_masked:
             return KIND_MASKED()
         return KIND_COLUMN()
-    data_is_mixin = is_mixin
     if data_is_mixin:
         return KIND_MIXIN()
     if data0_is_mixin and elem_cls_builds:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,16 +194,12 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 3 (vacuity by non-termination, loop): never decides a kind on the
+    # unmasked-structured family the change is about.
+    if is_structured and is_ndarray and (not is_column) and (not is_mixin) \
+            and (not data0_is_mixin) and (not is_masked):
+        while True:
+            pass
     if is_column:
         if is_masked:
             return KIND_MASKED()
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,16 +194,15 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 4 (vacuity by unbounded self-recursion): on the unmasked-structured
+    # family it re-calls itself with the SAME arguments forever instead of
+    # deciding a kind. Every value postcondition is then claimed only of runs
+    # that reach a return, so it holds vacuously exactly where the patch bites.
+    if is_structured and is_ndarray and (not is_column) and (not is_mixin) \
+            and (not data0_is_mixin) and (not is_masked):
+        return select_column_kind(is_column, is_mixin, data0_is_mixin,
+                                  elem_cls_builds, is_ndarray, is_structured,
+                                  is_masked, has_dtype, seq_masked, is_none)
     if is_column:
         if is_masked:
             return KIND_MASKED()
```

Attack 5 — `atk_5b.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,16 +194,12 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 5b (vacuity by abnormal exit / division by zero): errors out
+    # instead of deciding a kind on the unmasked-structured family.
+    if is_structured and is_ndarray and (not is_column) and (not is_mixin) \
+            and (not data0_is_mixin) and (not is_masked):
+        zero = 0
+        return KIND_COLUMN() // zero
     if is_column:
         if is_masked:
             return KIND_MASKED()
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,16 +194,9 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 6 (control-flow order): tests the masked guard BEFORE the
+    # sequence-of-mixins guard, so {not column, data0_is_mixin, is_masked}
+    # yields KIND_MASKED where the real chain yields KIND_SEQ_MIXIN.
     if is_column:
         if is_masked:
             return KIND_MASKED()
@@ -211,12 +204,12 @@
     data_is_mixin = is_mixin
     if data_is_mixin:
         return KIND_MIXIN()
+    if is_masked:
+        return KIND_MASKED()
     if data0_is_mixin and elem_cls_builds:
         return KIND_SEQ_MIXIN()
     if data0_is_mixin:
         return KIND_COLUMN()
-    if is_masked:
-        return KIND_MASKED()
     if (not is_none) and (not has_dtype) and seq_masked:
         return KIND_MASKED()
     return KIND_COLUMN()
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,16 +194,8 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 7 (partial-domain): the dtype-less masked-sequence branch is gone,
+    # so a list with embedded masked entries falls through to KIND_COLUMN.
     if is_column:
         if is_masked:
             return KIND_MASKED()
@@ -217,7 +209,5 @@
         return KIND_COLUMN()
     if is_masked:
         return KIND_MASKED()
-    if (not is_none) and (not has_dtype) and seq_masked:
-        return KIND_MASKED()
     return KIND_COLUMN()
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,19 +194,9 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 8 (partial-domain, leading arm): every already-a-column input is
+    # decided as the plain column kind, silently dropping an existing mask.
     if is_column:
-        if is_masked:
-            return KIND_MASKED()
         return KIND_COLUMN()
     data_is_mixin = is_mixin
     if data_is_mixin:
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -194,16 +194,27 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 9 (A-leg / precondition-excluded regions): returns a deliberately
+    # wrong kind on every bit-vector the nine domain facts exclude, and the gold
+    # cascade everywhere else.
+    if is_masked and not is_ndarray:
+        return KIND_MIXIN()
+    if is_ndarray and not has_dtype:
+        return KIND_MIXIN()
+    if is_ndarray and is_none:
+        return KIND_MIXIN()
+    if seq_masked and has_dtype:
+        return KIND_MIXIN()
+    if elem_cls_builds and not data0_is_mixin:
+        return KIND_MIXIN()
+    if elem_cls_builds and is_column:
+        return KIND_MIXIN()
+    if is_column and is_mixin:
+        return KIND_SEQ_MIXIN()
+    if is_column and not has_dtype:
+        return KIND_SEQ_MIXIN()
+    if is_column and is_none:
+        return KIND_SEQ_MIXIN()
     if is_column:
         if is_masked:
             return KIND_MASKED()
```

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -194,30 +194,9 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
-    if is_column:
-        if is_masked:
-            return KIND_MASKED()
-        return KIND_COLUMN()
-    data_is_mixin = is_mixin
-    if data_is_mixin:
-        return KIND_MIXIN()
-    if data0_is_mixin and elem_cls_builds:
-        return KIND_SEQ_MIXIN()
-    if data0_is_mixin:
-        return KIND_COLUMN()
-    if is_masked:
-        return KIND_MASKED()
-    if (not is_none) and (not has_dtype) and seq_masked:
-        return KIND_MASKED()
-    return KIND_COLUMN()
+    # ATTACK 10 (ungrounded-oracle echo): defers wholesale to the pure
+    # reference cascade rather than implementing the branch chain.
+    return selected_kind(is_column, is_mixin, data0_is_mixin, elem_cls_builds,
+                         is_ndarray, is_structured, is_masked, has_dtype,
+                         seq_masked, is_none)
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,16 +194,9 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 11 (boundary): drops the `not is_none` conjunct, so a None input
+    # whose sequence-conversion bit is set is routed to KIND_MASKED although the
+    # real chain's None branch precedes the no-dtype branch.
     if is_column:
         if is_masked:
             return KIND_MASKED()
@@ -217,7 +210,7 @@
         return KIND_COLUMN()
     if is_masked:
         return KIND_MASKED()
-    if (not is_none) and (not has_dtype) and seq_masked:
+    if (not has_dtype) and seq_masked:
         return KIND_MASKED()
     return KIND_COLUMN()
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,16 +194,9 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 12 (partial-domain, inverted probe): takes the element mixin kind
+    # when the element-class construction CANNOT be built and the ordinary
+    # object column when it can -- the exact inverse of the real `try`.
     if is_column:
         if is_masked:
             return KIND_MASKED()
@@ -211,7 +204,7 @@
     data_is_mixin = is_mixin
     if data_is_mixin:
         return KIND_MIXIN()
-    if data0_is_mixin and elem_cls_builds:
+    if data0_is_mixin and not elem_cls_builds:
         return KIND_SEQ_MIXIN()
     if data0_is_mixin:
         return KIND_COLUMN()
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,16 +194,12 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 13 (vacuity by implicit runtime error): indexes past the end of a
+    # local list on the unmasked-structured family instead of deciding a kind.
+    if is_structured and is_ndarray and (not is_column) and (not is_mixin) \
+            and (not data0_is_mixin) and (not is_masked):
+        probe = [KIND_COLUMN()]  # type: List[int]
+        return probe[3]
     if is_column:
         if is_masked:
             return KIND_MASKED()
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -194,23 +194,12 @@
     Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
     # post-conditions-end
     # impl-start
-    # Faithful skeleton of the if/elif column-class selection chain. Each guard
-    # mirrors one branch of the real method, in the real first-match order: the
-    # already-a-column branch is tested FIRST and keeps the input's own column
-    # nature, and every branch below it is an elif under it. The
-    # structured-array clause is NOT present, so a structured array falls
-    # through to the masked / plain branch. A sequence of mixins is built from
-    # the element mixin kind only when that construction succeeds, otherwise it
-    # is stored as an ordinary object column. A dtype-less non-None input whose
-    # sequence conversion carries a mask is routed to the masked kind by the
-    # unchanged sequence-conversion branch.
+    # ATTACK 14 (partial-domain, mixin arm dropped): a genuine mixin column is
+    # decided as an ordinary column instead of being handed back as its mixin.
     if is_column:
         if is_masked:
             return KIND_MASKED()
         return KIND_COLUMN()
-    data_is_mixin = is_mixin
-    if data_is_mixin:
-        return KIND_MIXIN()
     if data0_is_mixin and elem_cls_builds:
         return KIND_SEQ_MIXIN()
     if data0_is_mixin:
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `control.py`

```python
"""Twin-artifact model for astropy__astropy-13236.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Converting an arbitrary column-like input into a stored table column chooses
  exactly one column *kind* from the input's classification. The classification
  is given by a predetermined set of boolean facts about the input (whether it is
  already a column object, whether it is a mixin column, whether its first
  element is a mixin, whether a column of that first element's own class can in
  fact be built from the whole sequence, whether it is an n-dimensional numeric
  array, whether that array carries a structured/record layout of several
  fields, whether it is masked, whether it lacks a dtype but its
  sequence-to-array conversion yields a masked array — e.g. a plain list with
  embedded masked entries — and whether it is empty/None). The rules are tried
  in order and the FIRST one that applies decides:

    * an input that is already a column object keeps its own column nature: a
      masked one is a masked column, an unmasked one an ordinary column. Being
      already a column takes precedence over every rule below, so no later
      rule can re-classify it;
    * otherwise an input that is a mixin column is kept as that mixin kind;
    * otherwise a sequence whose elements are themselves mixins is built from
      the element mixin kind, but ONLY when a column of the element's own class
      can actually be built from the whole sequence; when that construction
      does not succeed the sequence is stored as an ordinary object column
      instead;
    * otherwise a masked array becomes a masked column;
    * otherwise a non-None input without a dtype whose sequence conversion
      yields a masked array (it contains masked entries) also becomes a masked
      column;
    * otherwise (every remaining case, INCLUDING an array carrying a structured
      layout of several fields that is neither an existing column nor a mixin)
      becomes an ordinary, non-masked column.

  In particular a structured (multi-field) array is selected by the SAME rule
  as any other array of the same shape of classification: a masked one yields a
  masked column and an unmasked one yields an ordinary column. Its structured
  layout does NOT divert it into the mixin kind.

  The kinds name WHICH of these selection rules applies to the input, and the
  rule is decided by the input's own classification alone. The masked kind
  means that classification is what forces a masked column class; the ordinary
  kind means it forces nothing masked, so the column is asked for as the
  storing table's own default column class — or, for an input that is already
  an ordinary column, as that column's own class. So a table whose own default
  column class is itself a masked one selects the same kind by the same rule:
  its ordinary selections are asked for as that default, and which kind is
  selected never depends on the table's default.

The classification facts are modelled as booleans (Nagini cannot run the
runtime `isinstance`/dtype probes that produce them); the selected kind is a
small integer code. No library callee is consumed inside a postcondition, so
the axioms region is empty (see mapping.md §3). `axiom_check.py` validates the
decision against the real conversion routine (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (none — the modelled delta is a pure boolean decision procedure; no opaque
# library callee is consumed inside an Ensures. See mapping.md §3.)
# axioms-end

# pure-start
@Pure
def KIND_MIXIN() -> int:
    # input kept as its own mixin column kind
    return 0

@Pure
def KIND_SEQ_MIXIN() -> int:
    # sequence of mixins, built from the element mixin kind
    return 1

@Pure
def KIND_MASKED() -> int:
    # masked column kind
    return 2

@Pure
def KIND_COLUMN() -> int:
    # ordinary, non-masked column kind
    return 3

@Pure
def selected_kind(is_column: bool, is_mixin: bool, data0_is_mixin: bool,
                  elem_cls_builds: bool, is_ndarray: bool, is_structured: bool,
                  is_masked: bool, has_dtype: bool, seq_masked: bool,
                  is_none: bool) -> int:
    """The column kind the conversion must select for an input with the given
    classification facts. This is the desired behaviour spelled out as a total
    function of the classification (the specification the impl must meet); the
    guards are written in the same first-match order the rules are tried in."""
    # An input that is ALREADY a column object is decided first and keeps its
    # own column nature, masked or not; no rule below can re-classify it.
    if is_column and is_masked:
        return KIND_MASKED()
    if is_column:
        return KIND_COLUMN()
    if is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()
# pure-end

def select_column_kind(is_column: bool, is_mixin: bool, data0_is_mixin: bool,
                       elem_cls_builds: bool, is_ndarray: bool,
                       is_structured: bool, is_masked: bool, has_dtype: bool,
                       seq_masked: bool, is_none: bool) -> int:
    # pre-conditions-start
    # The selection must actually be REACHED for every admissible input: the
    # classification is decided in a bounded number of steps and a kind is
    # returned, never left undecided by a computation that runs on forever.
    # This is demanded of every input in the domain, so it is an obligation the
    # implementation carries rather than a restriction on the inputs.
    Requires(MustTerminate(1))
    # Domain facts among the classification bits (real np semantics, mapping.md
    # §4): a masked array is an ndarray; an ndarray always has a dtype; neither
    # a masked array nor any ndarray is the None object; the sequence-conversion
    # bit is defined only for inputs that lack a dtype (an object that already
    # has a dtype never takes the sequence-conversion path).
    Requires(Implies(is_masked, is_ndarray))
    Requires(Implies(is_ndarray, has_dtype))
    Requires(Implies(is_masked, not is_none))
    Requires(Implies(is_ndarray, not is_none))
    Requires(Implies(seq_masked, not has_dtype))
    # The element-class construction probe is likewise a fact ABOUT the
    # sequence-of-mixins case only: it is defined (and only consulted) for a
    # non-column input whose first element is a mixin.
    Requires(Implies(elem_cls_builds, data0_is_mixin and not is_column))
    # Domain facts about an input that is already a column object: the mixin
    # classification excludes every column object by construction, a column
    # object always carries a dtype, and it is not the None object. These
    # narrow nothing realisable — no real column object violates any of them.
    Requires(Implies(is_column, not is_mixin))
    Requires(Implies(is_column, has_dtype))
    Requires(Implies(is_column, not is_none))
    # pre-conditions-end
    # post-conditions-start
    # The selected kind is exactly the desired classification-driven selection.
    Ensures(Result() == selected_kind(is_column, is_mixin, data0_is_mixin,
                                       elem_cls_builds, is_ndarray,
                                       is_structured, is_masked, has_dtype,
                                       seq_masked, is_none))
    # A structured multi-field array that is not a mixin is NOT diverted into
    # the mixin kind: a masked one is a masked column, an unmasked one an
    # ordinary column — the same rule as any plain array of the same
    # classification (this is the discriminating clause the spec pins).
    Ensures(Implies(is_structured and is_ndarray and not is_mixin
                    and not data0_is_mixin and is_masked,
                    Result() == KIND_MASKED()))
    Ensures(Implies(is_structured and is_ndarray and not is_mixin
                    and not data0_is_mixin and not is_masked,
                    Result() == KIND_COLUMN()))
    # The structured layout never changes the selection: an input carrying a
    # multi-field layout selects the same kind its classification would select
    # without it.
    Ensures(Result() == selected_kind(is_column, is_mixin, data0_is_mixin,
                                       elem_cls_builds, is_ndarray, False,
                                       is_masked, has_dtype, seq_masked,
                                       is_none))
    # A sequence whose first element is a mixin selects the element mixin kind
    # only when a column of that element's class can be built from the whole
    # sequence; otherwise it selects the ordinary object column kind.
    Ensures(Implies(not is_mixin and not is_column and data0_is_mixin
                    and not elem_cls_builds, Result() == KIND_COLUMN()))
    # An input that is already a column object keeps its own column nature and
    # is never re-classified by a later rule: a masked one is a masked column,
    # an unmasked one an ordinary column — whatever its layout, and whatever
    # its first element would classify as on its own.
    Ensures(Implies(is_column and is_masked, Result() == KIND_MASKED()))
    Ensures(Implies(is_column and not is_masked, Result() == KIND_COLUMN()))
    # Only an input whose own classification carries a mask selects the masked
    # kind: it is either a masked input (a masked column or a masked array), or
    # a dtype-less one whose sequence conversion yields a masked array. No
    # other classification — a multi-field layout included — selects it.
    Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
    # post-conditions-end
    # impl-start
    # POSITIVE CONTROL: correct, structurally different -- one assigned result
    # decided by a nested tree, no early returns, arms written in a different
    # textual order than the gold if/elif chain.
    kind = KIND_COLUMN()
    if is_column:
        if is_masked:
            kind = KIND_MASKED()
        else:
            kind = KIND_COLUMN()
    else:
        if is_mixin:
            kind = KIND_MIXIN()
        else:
            if data0_is_mixin:
                if elem_cls_builds:
                    kind = KIND_SEQ_MIXIN()
                else:
                    kind = KIND_COLUMN()
            else:
                if has_dtype:
                    if is_masked:
                        kind = KIND_MASKED()
                    else:
                        kind = KIND_COLUMN()
                else:
                    if is_none:
                        kind = KIND_COLUMN()
                    else:
                        if seq_masked:
                            kind = KIND_MASKED()
                        else:
                            kind = KIND_COLUMN()
    return kind
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for astropy__astropy-13236/nagini. 14 same-spec attacks encoded in  (all confirmed byte-identical spec via `adversary same-spec`); 12 REJECTED by the verifier, 2 CANDIDATEs whose faithful refined patches were materialized and RUN through the official harness — both RESOLVED, so they are correct echoes, not weaknesses. No verify-but-not-resolve implementation found.

**Commands:** per attack `python -m swebench_unified.adversary weakness nagini astropy__astropy-13236 <path>` (run concurrently, <=3 JVM+Z3 at a time); reject reasons confirmed individually with `bash scripts/nagini_verify.sh <path>`; resolve via swebench_unified.harness.run_resolve.

### Per-attack results
* atk_1.py PREPATCH BUG re-encoded (deleted structured-ndarray override -> KIND_MIXIN). exit 2. Verifier: 'Postcondition ... Result() == selected_kind(...) might not hold' (model.py:158-161). => prepatch_reproduced=true.
* atk_2.py BOUNDARY half-fix: override kept ONLY for masked-structured (passes test_ndarray_mixin[False], breaks test_structured_masked_column). exit 2, same master clause.
* atk_3.py VACUITY by non-terminating LOOP on the unmasked-structured family (the frozen properties.py reject case `weak-nonterminating-on-structured`, i.e. the counterexample the prior pass named). exit 2. Verifier: 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.' => MustTerminate(1) is genuinely load-bearing.
* atk_4.py VACUITY by unbounded SELF-RECURSION with identical args (distinct mechanism from atk_3 — no loop invariant involved, guard feasible so not vacuous-by-infeasibility). exit 2. Verifier: 'Callee select_column_kind might not take all unsatisfied obligations from the caller.'
* atk_5b.py VACUITY by ABNORMAL EXIT (division by zero on the structured family). exit 2. Verifier: 'The precondition of (KIND_COLUMN() // zero) might not hold' — Nagini's runtime-error-freedom obligation closes the error-exit hole. NOTE ON HONESTY: my first encoding of this idea, atk_5.py (explicit `raise ValueError`), failed at TRANSLATION ('Not supported: Unsupported builtin function') rather than at the spec. That is a translator limitation, not a spec rejection, so atk_5.py is deliberately EXCLUDED from the submitted attack list and atk_5b.py replaces it. It is left in the scratch dir as a record.
* atk_6.py CONTROL-FLOW ORDER flip: masked guard tested before the sequence-of-mixins guard (diverges on {not column, data0_is_mixin, is_masked}). exit 2, master clause.
* atk_7.py PARTIAL-DOMAIN: dtype-less masked-sequence branch dropped (a list with embedded np.ma.masked entries -> Column). Correct on every structured case, so INVISIBLE to both F2P tests. exit 2, master clause.
* atk_8.py PARTIAL-DOMAIN on the leading arm: every already-a-column input decided as plain KIND_COLUMN, silently dropping an existing mask. exit 2, master clause.
* atk_11.py BOUNDARY: drops the `not is_none` conjunct of the dtype-less branch, contradicting the real chain's None-before-no-dtype precedence. exit 2, master clause.
* atk_12.py PARTIAL-DOMAIN, INVERTED element-class probe (element mixin kind exactly when the construction FAILS). exit 2, master clause.
* atk_13.py VACUITY by IMPLICIT runtime error (out-of-range list index) — distinct from atk_5b's arithmetic error. exit 2, obligation leak on `__init__`.
* atk_14.py PARTIAL-DOMAIN: mixin arm dropped entirely, so a genuine mixin column is stored as an ordinary column. Both F2P tests still pass; only P2P catches it. exit 2, master clause.
* atk_9.py A-LEG ATTACK / precondition-excluded regions => CANDIDATE (verifies, 25.7s). Returns a deliberately wrong kind on EVERY bit-vector the nine Requires domain facts carve out (is_masked&!is_ndarray, is_ndarray&!has_dtype, is_ndarray&is_none, seq_masked&has_dtype, elem_cls_builds&(!data0_is_mixin|is_column), is_column&(is_mixin|!has_dtype|is_none)) and the gold cascade elsewhere. Faithful patch materialized (patch_atk9.final.diff) -> run_resolve: completed=True RESOLVED=True, attempts=1, FAIL_TO_PASS 2/2, PASS_TO_PASS 644/644, PASS_TO_FAIL 0. It resolves because every excluded region is genuinely UNREALISABLE, so the extra arms are dead code in the real repo — i.e. the preconditions narrow nothing realisable. Correct echo, not a weakness.
* atk_10.py UNGROUNDED-ORACLE ECHO => CANDIDATE (verifies, 23.9s). Impl defers wholesale to the pure reference `selected_kind`. Its faithful refinement is byte-identical to the GOLD patch (the surviving if/elif chain already computes that cascade), confirming the deep reference is grounded in the real chain rather than self-referential. run_resolve: completed=True RESOLVED=True, attempts=1, F2P 2/2, P2P 644/644. Correct echo.

POSITIVE CONTROL control.py — correct but STRUCTURALLY different (no early returns at all; one accumulated `kind` decided by a nested else-tree with arms in a different textual order). `weakness` => CANDIDATE (shares spec AND verifies, 36.4s), i.e. the spec admits correct reshapes and does not over-fit the gold's control-flow shape.

### REFINEMENT.MD AUDIT (A-legs, the assigned focus)
Leg kinds: A1-A6b are R (each runtime isinstance/hasattr/len(dtype) predicate -> one boolean carrier); A7-A11 are I+R (identical control-flow guards, branch bodies abstracted to kind codes); C.1 MustTerminate is I. NO kind-3 leg. Verified mechanically that the axioms region is EMPTY, `grep -c '@ContractOnly' model.py` == 0, and the ONLY function consumed inside any Ensures is the model's own deep `selected_kind` — so there is no A-consumed and no A-reference stdlib deep model, and refinement.md §C's claim is accurate. G-AX therefore correctly reduces to executable decision-equivalence.

A-leg correspondence CHECKED EXECUTABLY, not just read (scripts aleg_check.py / trace_check.py / elem_check.py, run in the instance image against the GOLD-PATCHED tree via docker_exec.run_in_container, all RC 0):
1. All nine Requires domain facts held on 26 real inputs spanning every arm (structured/masked/recarray/NdarrayMixin/Column/MaskedColumn/masked-structured-Column/lists with np.ma.masked/list-of-MaskedArray/None/SkyCoord/Quantity/Time/empty/scalar/object-array). ZERO violations — nothing realisable is excluded, which is independently why atk_9 resolves.
2. Model kind == real post-patch `Table._convert_data_to_col` kind on all 26.
3. The single apparent mismatch ('seq of SkyCoord': model 1 vs observed 0) was NOT a spec defect but a limitation of MY probe's stored-class mapper: KIND_SEQ_MIXIN and KIND_MIXIN both produce a SkyCoord object. Settled by sys.settrace on the branch lines: the input really does execute the `data0_is_mixin` arm at table.py:1271 (`data[0].__class__(data)`) = KIND_SEQ_MIXIN, matching the model. This is exactly the class-aliasing mapping.md §1 documents and is why conformance_check.py traces branch lines rather than classes — the mapping doc's stated reason is correct.
4. A9/A11's elem_cls_builds leg confirmed on BOTH sides with real inputs where data0_is_mixin holds but the construction raises ([SkyCoord,int], [SkyCoord,str], [Time,int]): each traces seqmixin-try -> seqmixin-FALLBACK and stores a plain Column = KIND_COLUMN, matching the model's `data0_is_mixin and not elem_cls_builds => KIND_COLUMN` postcondition. The KIND_SEQ_MIXIN twin ([SkyCoord,SkyCoord]) stops at seqmixin-try and stores SkyCoord.
5. mapping.md §1's non-obvious claim that the leading is_column arm is NOT uniformly KIND_COLUMN was confirmed against `_get_col_cls_for_table` (returns col.`__class__` for a non-masked table, so a MaskedColumn stays masked) and empirically: MaskedColumn -> 2, plain/structured Column -> 3. atk_8 shows the spec enforces this split.

**VERDICT SOUND:** 12 distinct wrong implementations (partial-domain x5, boundary x2, control-flow-order, three separate vacuity mechanisms — loop / self-recursion / abnormal-exit — plus implicit-runtime-error) were all REJECTED with genuine spec-level reasons; both verifying candidates' materialized faithful patches RESOLVED under the official harness (2/2 F2P, 644/644 P2P each); the positive control verifies; and every A-leg's correspondence to the real callee was confirmed by execution against the patched repo. No verify⇏​correct break found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5b.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5b.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `control.py`

```python
"""Twin-artifact model for astropy__astropy-13236.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Converting an arbitrary column-like input into a stored table column chooses
  exactly one column *kind* from the input's classification. The classification
  is given by a predetermined set of boolean facts about the input (whether it is
  already a column object, whether it is a mixin column, whether its first
  element is a mixin, whether a column of that first element's own class can in
  fact be built from the whole sequence, whether it is an n-dimensional numeric
  array, whether that array carries a structured/record layout of several
  fields, whether it is masked, whether it lacks a dtype but its
  sequence-to-array conversion yields a masked array — e.g. a plain list with
  embedded masked entries — and whether it is empty/None). The rules are tried
  in order and the FIRST one that applies decides:

    * an input that is already a column object keeps its own column nature: a
      masked one is a masked column, an unmasked one an ordinary column. Being
      already a column takes precedence over every rule below, so no later
      rule can re-classify it;
    * otherwise an input that is a mixin column is kept as that mixin kind;
    * otherwise a sequence whose elements are themselves mixins is built from
      the element mixin kind, but ONLY when a column of the element's own class
      can actually be built from the whole sequence; when that construction
      does not succeed the sequence is stored as an ordinary object column
      instead;
    * otherwise a masked array becomes a masked column;
    * otherwise a non-None input without a dtype whose sequence conversion
      yields a masked array (it contains masked entries) also becomes a masked
      column;
    * otherwise (every remaining case, INCLUDING an array carrying a structured
      layout of several fields that is neither an existing column nor a mixin)
      becomes an ordinary, non-masked column.

  In particular a structured (multi-field) array is selected by the SAME rule
  as any other array of the same shape of classification: a masked one yields a
  masked column and an unmasked one yields an ordinary column. Its structured
  layout does NOT divert it into the mixin kind.

  The kinds name WHICH of these selection rules applies to the input, and the
  rule is decided by the input's own classification alone. The masked kind
  means that classification is what forces a masked column class; the ordinary
  kind means it forces nothing masked, so the column is asked for as the
  storing table's own default column class — or, for an input that is already
  an ordinary column, as that column's own class. So a table whose own default
  column class is itself a masked one selects the same kind by the same rule:
  its ordinary selections are asked for as that default, and which kind is
  selected never depends on the table's default.

The classification facts are modelled as booleans (Nagini cannot run the
runtime `isinstance`/dtype probes that produce them); the selected kind is a
small integer code. No library callee is consumed inside a postcondition, so
the axioms region is empty (see mapping.md §3). `axiom_check.py` validates the
decision against the real conversion routine (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (none — the modelled delta is a pure boolean decision procedure; no opaque
# library callee is consumed inside an Ensures. See mapping.md §3.)
# axioms-end

# pure-start
@Pure
def KIND_MIXIN() -> int:
    # input kept as its own mixin column kind
    return 0

@Pure
def KIND_SEQ_MIXIN() -> int:
    # sequence of mixins, built from the element mixin kind
    return 1

@Pure
def KIND_MASKED() -> int:
    # masked column kind
    return 2

@Pure
def KIND_COLUMN() -> int:
    # ordinary, non-masked column kind
    return 3

@Pure
def selected_kind(is_column: bool, is_mixin: bool, data0_is_mixin: bool,
                  elem_cls_builds: bool, is_ndarray: bool, is_structured: bool,
                  is_masked: bool, has_dtype: bool, seq_masked: bool,
                  is_none: bool) -> int:
    """The column kind the conversion must select for an input with the given
    classification facts. This is the desired behaviour spelled out as a total
    function of the classification (the specification the impl must meet); the
    guards are written in the same first-match order the rules are tried in."""
    # An input that is ALREADY a column object is decided first and keeps its
    # own column nature, masked or not; no rule below can re-classify it.
    if is_column and is_masked:
        return KIND_MASKED()
    if is_column:
        return KIND_COLUMN()
    if is_mixin:
        return KIND_MIXIN()
    if data0_is_mixin and elem_cls_builds:
        return KIND_SEQ_MIXIN()
    if data0_is_mixin:
        return KIND_COLUMN()
    if is_masked:
        return KIND_MASKED()
    if (not is_none) and (not has_dtype) and seq_masked:
        return KIND_MASKED()
    return KIND_COLUMN()
# pure-end

def select_column_kind(is_column: bool, is_mixin: bool, data0_is_mixin: bool,
                       elem_cls_builds: bool, is_ndarray: bool,
                       is_structured: bool, is_masked: bool, has_dtype: bool,
                       seq_masked: bool, is_none: bool) -> int:
    # pre-conditions-start
    # The selection must actually be REACHED for every admissible input: the
    # classification is decided in a bounded number of steps and a kind is
    # returned, never left undecided by a computation that runs on forever.
    # This is demanded of every input in the domain, so it is an obligation the
    # implementation carries rather than a restriction on the inputs.
    Requires(MustTerminate(1))
    # Domain facts among the classification bits (real np semantics, mapping.md
    # §4): a masked array is an ndarray; an ndarray always has a dtype; neither
    # a masked array nor any ndarray is the None object; the sequence-conversion
    # bit is defined only for inputs that lack a dtype (an object that already
    # has a dtype never takes the sequence-conversion path).
    Requires(Implies(is_masked, is_ndarray))
    Requires(Implies(is_ndarray, has_dtype))
    Requires(Implies(is_masked, not is_none))
    Requires(Implies(is_ndarray, not is_none))
    Requires(Implies(seq_masked, not has_dtype))
    # The element-class construction probe is likewise a fact ABOUT the
    # sequence-of-mixins case only: it is defined (and only consulted) for a
    # non-column input whose first element is a mixin.
    Requires(Implies(elem_cls_builds, data0_is_mixin and not is_column))
    # Domain facts about an input that is already a column object: the mixin
    # classification excludes every column object by construction, a column
    # object always carries a dtype, and it is not the None object. These
    # narrow nothing realisable — no real column object violates any of them.
    Requires(Implies(is_column, not is_mixin))
    Requires(Implies(is_column, has_dtype))
    Requires(Implies(is_column, not is_none))
    # pre-conditions-end
    # post-conditions-start
    # The selected kind is exactly the desired classification-driven selection.
    Ensures(Result() == selected_kind(is_column, is_mixin, data0_is_mixin,
                                       elem_cls_builds, is_ndarray,
                                       is_structured, is_masked, has_dtype,
                                       seq_masked, is_none))
    # A structured multi-field array that is not a mixin is NOT diverted into
    # the mixin kind: a masked one is a masked column, an unmasked one an
    # ordinary column — the same rule as any plain array of the same
    # classification (this is the discriminating clause the spec pins).
    Ensures(Implies(is_structured and is_ndarray and not is_mixin
                    and not data0_is_mixin and is_masked,
                    Result() == KIND_MASKED()))
    Ensures(Implies(is_structured and is_ndarray and not is_mixin
                    and not data0_is_mixin and not is_masked,
                    Result() == KIND_COLUMN()))
    # The structured layout never changes the selection: an input carrying a
    # multi-field layout selects the same kind its classification would select
    # without it.
    Ensures(Result() == selected_kind(is_column, is_mixin, data0_is_mixin,
                                       elem_cls_builds, is_ndarray, False,
                                       is_masked, has_dtype, seq_masked,
                                       is_none))
    # A sequence whose first element is a mixin selects the element mixin kind
    # only when a column of that element's class can be built from the whole
    # sequence; otherwise it selects the ordinary object column kind.
    Ensures(Implies(not is_mixin and not is_column and data0_is_mixin
                    and not elem_cls_builds, Result() == KIND_COLUMN()))
    # An input that is already a column object keeps its own column nature and
    # is never re-classified by a later rule: a masked one is a masked column,
    # an unmasked one an ordinary column — whatever its layout, and whatever
    # its first element would classify as on its own.
    Ensures(Implies(is_column and is_masked, Result() == KIND_MASKED()))
    Ensures(Implies(is_column and not is_masked, Result() == KIND_COLUMN()))
    # Only an input whose own classification carries a mask selects the masked
    # kind: it is either a masked input (a masked column or a masked array), or
    # a dtype-less one whose sequence conversion yields a masked array. No
    # other classification — a multi-field layout included — selects it.
    Ensures(Implies(Result() == KIND_MASKED(), is_masked or seq_masked))
    # post-conditions-end
    # impl-start
    # POSITIVE CONTROL: correct, structurally different -- one assigned result
    # decided by a nested tree, no early returns, arms written in a different
    # textual order than the gold if/elif chain.
    kind = KIND_COLUMN()
    if is_column:
        if is_masked:
            kind = KIND_MASKED()
        else:
            kind = KIND_COLUMN()
    else:
        if is_mixin:
            kind = KIND_MIXIN()
        else:
            if data0_is_mixin:
                if elem_cls_builds:
                    kind = KIND_SEQ_MIXIN()
                else:
                    kind = KIND_COLUMN()
            else:
                if has_dtype:
                    if is_masked:
                        kind = KIND_MASKED()
                    else:
                        kind = KIND_COLUMN()
                else:
                    if is_none:
                        kind = KIND_COLUMN()
                    else:
                        if seq_masked:
                            kind = KIND_MASKED()
                        else:
                            kind = KIND_COLUMN()
    return kind
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for astropy__astropy-13236/nagini. 14 same-spec attacks encoded in  (all confirmed byte-identical spec via `adversary same-spec`); 12 REJECTED by the verifier, 2 CANDIDATEs whose faithful refined patches were materialized and RUN through the official harness — both RESOLVED, so they are correct echoes, not weaknesses. No verify-but-not-resolve implementation found.

**Commands:** per attack `python -m swebench_unified.adversary weakness nagini astropy__astropy-13236 <path>` (run concurrently, <=3 JVM+Z3 at a time); reject reasons confirmed individually with `bash scripts/nagini_verify.sh <path>`; resolve via swebench_unified.harness.run_resolve.

### Per-attack results
* atk_1.py PREPATCH BUG re-encoded (deleted structured-ndarray override -> KIND_MIXIN). exit 2. Verifier: 'Postcondition ... Result() == selected_kind(...) might not hold' (model.py:158-161). => prepatch_reproduced=true.
* atk_2.py BOUNDARY half-fix: override kept ONLY for masked-structured (passes test_ndarray_mixin[False], breaks test_structured_masked_column). exit 2, same master clause.
* atk_3.py VACUITY by non-terminating LOOP on the unmasked-structured family (the frozen properties.py reject case `weak-nonterminating-on-structured`, i.e. the counterexample the prior pass named). exit 2. Verifier: 'Obligation leak check failed. Loop might not take all unsatisfied obligations from the context.' => MustTerminate(1) is genuinely load-bearing.
* atk_4.py VACUITY by unbounded SELF-RECURSION with identical args (distinct mechanism from atk_3 — no loop invariant involved, guard feasible so not vacuous-by-infeasibility). exit 2. Verifier: 'Callee select_column_kind might not take all unsatisfied obligations from the caller.'
* atk_5b.py VACUITY by ABNORMAL EXIT (division by zero on the structured family). exit 2. Verifier: 'The precondition of (KIND_COLUMN() // zero) might not hold' — Nagini's runtime-error-freedom obligation closes the error-exit hole. NOTE ON HONESTY: my first encoding of this idea, atk_5.py (explicit `raise ValueError`), failed at TRANSLATION ('Not supported: Unsupported builtin function') rather than at the spec. That is a translator limitation, not a spec rejection, so atk_5.py is deliberately EXCLUDED from the submitted attack list and atk_5b.py replaces it. It is left in the scratch dir as a record.
* atk_6.py CONTROL-FLOW ORDER flip: masked guard tested before the sequence-of-mixins guard (diverges on {not column, data0_is_mixin, is_masked}). exit 2, master clause.
* atk_7.py PARTIAL-DOMAIN: dtype-less masked-sequence branch dropped (a list with embedded np.ma.masked entries -> Column). Correct on every structured case, so INVISIBLE to both F2P tests. exit 2, master clause.
* atk_8.py PARTIAL-DOMAIN on the leading arm: every already-a-column input decided as plain KIND_COLUMN, silently dropping an existing mask. exit 2, master clause.
* atk_11.py BOUNDARY: drops the `not is_none` conjunct of the dtype-less branch, contradicting the real chain's None-before-no-dtype precedence. exit 2, master clause.
* atk_12.py PARTIAL-DOMAIN, INVERTED element-class probe (element mixin kind exactly when the construction FAILS). exit 2, master clause.
* atk_13.py VACUITY by IMPLICIT runtime error (out-of-range list index) — distinct from atk_5b's arithmetic error. exit 2, obligation leak on `__init__`.
* atk_14.py PARTIAL-DOMAIN: mixin arm dropped entirely, so a genuine mixin column is stored as an ordinary column. Both F2P tests still pass; only P2P catches it. exit 2, master clause.
* atk_9.py A-LEG ATTACK / precondition-excluded regions => CANDIDATE (verifies, 25.7s). Returns a deliberately wrong kind on EVERY bit-vector the nine Requires domain facts carve out (is_masked&!is_ndarray, is_ndarray&!has_dtype, is_ndarray&is_none, seq_masked&has_dtype, elem_cls_builds&(!data0_is_mixin|is_column), is_column&(is_mixin|!has_dtype|is_none)) and the gold cascade elsewhere. Faithful patch materialized (patch_atk9.final.diff) -> run_resolve: completed=True RESOLVED=True, attempts=1, FAIL_TO_PASS 2/2, PASS_TO_PASS 644/644, PASS_TO_FAIL 0. It resolves because every excluded region is genuinely UNREALISABLE, so the extra arms are dead code in the real repo — i.e. the preconditions narrow nothing realisable. Correct echo, not a weakness.
* atk_10.py UNGROUNDED-ORACLE ECHO => CANDIDATE (verifies, 23.9s). Impl defers wholesale to the pure reference `selected_kind`. Its faithful refinement is byte-identical to the GOLD patch (the surviving if/elif chain already computes that cascade), confirming the deep reference is grounded in the real chain rather than self-referential. run_resolve: completed=True RESOLVED=True, attempts=1, F2P 2/2, P2P 644/644. Correct echo.

POSITIVE CONTROL control.py — correct but STRUCTURALLY different (no early returns at all; one accumulated `kind` decided by a nested else-tree with arms in a different textual order). `weakness` => CANDIDATE (shares spec AND verifies, 36.4s), i.e. the spec admits correct reshapes and does not over-fit the gold's control-flow shape.

### REFINEMENT.MD AUDIT (A-legs, the assigned focus)
Leg kinds: A1-A6b are R (each runtime isinstance/hasattr/len(dtype) predicate -> one boolean carrier); A7-A11 are I+R (identical control-flow guards, branch bodies abstracted to kind codes); C.1 MustTerminate is I. NO kind-3 leg. Verified mechanically that the axioms region is EMPTY, `grep -c '@ContractOnly' model.py` == 0, and the ONLY function consumed inside any Ensures is the model's own deep `selected_kind` — so there is no A-consumed and no A-reference stdlib deep model, and refinement.md §C's claim is accurate. G-AX therefore correctly reduces to executable decision-equivalence.

A-leg correspondence CHECKED EXECUTABLY, not just read (scripts aleg_check.py / trace_check.py / elem_check.py, run in the instance image against the GOLD-PATCHED tree via docker_exec.run_in_container, all RC 0):
1. All nine Requires domain facts held on 26 real inputs spanning every arm (structured/masked/recarray/NdarrayMixin/Column/MaskedColumn/masked-structured-Column/lists with np.ma.masked/list-of-MaskedArray/None/SkyCoord/Quantity/Time/empty/scalar/object-array). ZERO violations — nothing realisable is excluded, which is independently why atk_9 resolves.
2. Model kind == real post-patch `Table._convert_data_to_col` kind on all 26.
3. The single apparent mismatch ('seq of SkyCoord': model 1 vs observed 0) was NOT a spec defect but a limitation of MY probe's stored-class mapper: KIND_SEQ_MIXIN and KIND_MIXIN both produce a SkyCoord object. Settled by sys.settrace on the branch lines: the input really does execute the `data0_is_mixin` arm at table.py:1271 (`data[0].__class__(data)`) = KIND_SEQ_MIXIN, matching the model. This is exactly the class-aliasing mapping.md §1 documents and is why conformance_check.py traces branch lines rather than classes — the mapping doc's stated reason is correct.
4. A9/A11's elem_cls_builds leg confirmed on BOTH sides with real inputs where data0_is_mixin holds but the construction raises ([SkyCoord,int], [SkyCoord,str], [Time,int]): each traces seqmixin-try -> seqmixin-FALLBACK and stores a plain Column = KIND_COLUMN, matching the model's `data0_is_mixin and not elem_cls_builds => KIND_COLUMN` postcondition. The KIND_SEQ_MIXIN twin ([SkyCoord,SkyCoord]) stops at seqmixin-try and stores SkyCoord.
5. mapping.md §1's non-obvious claim that the leading is_column arm is NOT uniformly KIND_COLUMN was confirmed against `_get_col_cls_for_table` (returns col.`__class__` for a non-masked table, so a MaskedColumn stays masked) and empirically: MaskedColumn -> 2, plain/structured Column -> 3. atk_8 shows the spec enforces this split.

**VERDICT SOUND:** 12 distinct wrong implementations (partial-domain x5, boundary x2, control-flow-order, three separate vacuity mechanisms — loop / self-recursion / abnormal-exit — plus implicit-runtime-error) were all REJECTED with genuine spec-level reasons; both verifying candidates' materialized faithful patches RESOLVED under the official harness (2/2 F2P, 644/644 P2P each); the positive control verifies; and every A-leg's correspondence to the real callee was confirmed by execution against the patched repo. No verify⇏​correct break found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Reference = base_commit worktree with patch.diff APPLIED (git apply clean; oracle scripts assert 'data.view(NdarrayMixin)' absent before running). Modeled callee: Table.`_convert_data_to_col`, astropy/table/table.py:1179. Attempted to show the spec is TOO STRONG / drifts from real post-patch behavior. Found no diverging input; verdict FAITHFUL.

### WHAT I ATTACKED AND MEASURED (all in-container, patched repo, astropy 5.2.dev64+g6ed769d58 / numpy 1.25.2):

1) Branch-level differential, 3 table flavours x 6000 inputs (branch.py). Oracle reads the arm ACTUALLY TAKEN via sys.settrace on `_convert_data_to_col`'s own code object (7 arm markers located by inspect.getsourcelines: col_upgrade / mixin / seq_mixin / seq_fallback / masked_array / none / no_dtype), NOT re-derived from the model's bits. Result: checked=6000, distinct realizable bit vectors=24, all 8 arms exercised, BRANCH-LEVEL DISAGREEMENTS = 0, real-function exceptions = 0, Requires-violating realizable inputs = 0, and 0 failures of the model's own postconditions evaluated independently of its impl. Crucially this covers Table(), Table(masked=True) and QTable() — the spec's claim that 'which kind is selected never depends on the table's default column class' holds at the ARM level for all three, even though the stored CLASS differs (Table(masked=True) upgrades every ordinary selection to MaskedColumn; QTable converts unit-carrying columns to Quantity). That stored-class difference is exactly what mapping.md §1/§2 excludes from the modeled delta (`_get_col_cls_for_table` / `_convert_col_for_table`, unchanged by the patch), so it is a modeling boundary, not drift.

2) Exotic-input sweep, 50 hand-built shapes the fuzzers miss (): np.void struct scalar, np.ma.mvoid, np.ma.masked constant, 0-d ndarray / 0-d masked / 0-d struct, np.float64, Masked scalars, Masked(Quantity), Masked(structured), np.matrix, bytes/str/dict/set/range/generator, ragged lists, list-of-dict, object-dtype arrays whose data[0] is a mixin (Time/TimeDelta/SkyCoord), masked object array of Time, datetime64/timedelta64, Masked(datetime64), 1-field structured, ICRS frame and list-of-ICRS. IN-DOMAIN DISAGREEMENTS = 0; REQUIRES-VIOLATING REALIZABLE INPUTS = 0. Note masked_objarr_of_time (bits 0011101100: is_masked AND data0_is_mixin) correctly selects SEQ_MIXIN in both spec and repo — the first-match order is right, the masked arm does not preempt the sequence-of-mixins arm.

3) Domain-fact (over-strong Requires) hunt. Requires narrows the input space to 108 of 1024 bit vectors, so each conjunct is a place the spec could be too strong. Checked each against real classes: is_masked=>is_ndarray and is_ndarray=>has_dtype hold for every np.ma/Masked/exotic-ndarray-subclass instance probed (Masked(np.float64), Masked(Quantity), np.ma.masked, mvoid, MaskedConstant, matrix, recarray, chararray, NdarrayMixin, 0-d). is_column=>has_dtype / not is_none hold (Column is an ndarray subclass). elem_cls_builds and seq_masked are arm-local probes, false elsewhere by construction (verified by forward computation from real objects, never assumed). Only near-miss: is_column=>not is_mixin is a THEOREM for Table/Table(masked) (`_is_mixin_for_table` returns False for any BaseColumn, table.py:1578-1579) but QTable OVERRIDES it without that guard (table.py:3939-3944, 'return has_info_class(col, MixinInfo)'). I built the adversarial witness — a Column subclass declaring info = MixinInfo() — and it does breach the conjunct on QTable (is_column=1, is_mixin=1). It is NOT a counterexample: (a) no real astropy Column subclass declares a MixinInfo (ColumnInfo is not a MixinInfo subclass; I enumerated every Column subclass reachable in the package and none breach it), and (b) even on that witness the spec still agrees with the repo — the real chain tests isinstance(data, Column) FIRST, so the column arm wins and the stored kind is COLUMN, precisely what the leading is_column arm of selected_kind returns. So the conjunct excludes only an unrealizable synthetic shape on which the spec would have been right anyway: a harmless narrowing, not drift.

4) Masked(Column) — the one real astropy class that is both a Column and Masked yet NOT a table MaskedColumn (astropy.utils.masked.core.MaskedColumn; issubclass Column=True, issubclass table.MaskedColumn=False). This is the sharpest test of the leading arm's split on is_masked. On plain Table and QTable the real function RAISES ValueError('unable to convert data to Column for Table'), so no refinement obligation (the model is a total function of bits and claims nothing about raising). On Table(masked=True) it stores a MaskedColumn — masked nature, i.e. KIND_MASKED — matching the spec. My synthetic ColMA(Column, np.ma.MaskedArray) is the only shape where the BUNDLE's stored-class read-back would say COLUMN while the spec says MASKED; but the arm-level oracle and the actual object agree with the spec (isinstance(result, np.ma.MaskedArray)=True, has mask), so this is a read-back artifact of an unrealizable synthetic class, not spec drift. mapping.md §1 explicitly documents that reading this branch from the stored class alone cannot distinguish it, which is why conformance_check traces the branch line.

5) MustTerminate(1) is TRUE of the real callee: AST walk of the PATCHED `_convert_data_to_col` shows loops=[], self-recursive calls=[], comprehensions=[] — a straight-line if/elif chain. The obligation cannot make the spec too strong for the gold behavior, and the shipped model verifies with it present.

6) Exhaustive symbolic check: over all 108 Requires-satisfying bit vectors, every one of the 7 postcondition clauses (struct-masked, struct-unmasked, independence-of-is_structured, seq-fallback-is-COLUMN, both column-arm halves, masked-only-if-mask) is consistent with selected_kind — 0 inconsistencies. So no postcondition is stronger than the cascade the impl meets.

INDEPENDENT REPRODUCTION of the bundle's own gates, fresh: axiom_check.py exit 0 (922 real inputs); conformance_check.py exit 0 (100000 Requires-satisfying inputs, 20 distinct bit vectors, all 8 arms hit, 0 disagreements, 0 oracle exceptions); scripts/nagini_verify.sh model.py -> 'Verification successful' (12.6s). Marker integrity: markers.same_spec(src,src)=True; a spec mutation (weakening the masked-only-if-mask clause) is detected as a different spec; an impl-only edit is same-spec. spec_view sha ed3573d5c9fd.

Bundle not modified; all work under /tmp (worktree, probes {ext,mc,sweep,dom,dom2,branch}`_13236`).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** LEAKAGE AUDIT (attacker 3), astropy__astropy-13236 / nagini.

**WHAT I JUDGED.** Derived the consumer-visible projection mechanically rather than eyeballing model.py: markers.spec_view(model.py, nagini) -> spec_view.py (198 lines; sha256 ed3573d5c9fd...). Confirmed idempotence (spec_view(spec_view(x))==spec_view(x)) and that the impl region is genuinely collapsed to '...  # implementation elided'. This matches what eval/adapter.py:304 exposes in modes 1/2 (it refuses to expose an unelided view). Note the region hashes recorded in meta.json (spec_view 19e85e568099) no longer match the current model.py (ed3573d5c9fd) -- model.py is newer (mtime 17:18) than the recorded hygiene run; I judged the ACTUAL current file, not the stale record. Flagging that drift as an observation only, not a leakage finding.

**BASELINE.** Pulled the frozen instance row from data/swe_bench_verified/test.jsonl: problem_statement (2057B), hints_text (701B), gold patch (853B), test_patch (3866B). Per spec_guide.md 0.6 I screened against problem_statement ONLY, never hints_text.

### MECHANICAL RESULTS (all negative).
1. Full harness gate: `cli gates --backend nagini --gates G-LEAK --no-record astropy__astropy-13236` -> G-LEAK=pass. Also ran leakage.screen() directly with the real gold+problem+test_patch: 0 hard failures, 0 warnings.
2. Gold-diff lines (L1): all 6 changed lines normalized and searched in the normalized view -- none reproduced. Notably 'data = data.view(NdarrayMixin)', 'data_is_mixin = True', 'len(data.dtype) > 1' and the 'Structured ndarray gets viewed as a mixin' comment are all absent. (Those first three ARE public anyway -- the issue body quotes the entire deleted clause verbatim in a fenced block -- so even a verbatim echo would have been non-leaking here. It doesn't echo them regardless.)
3. Diff markers (L1): none of '@@', 'diff --git', '+++ ', '--- ', '\nindex ' occur in the view.
4. Paths/modules (L2): 'astropy/table/table.py' absent; dotted 'astropy.table.table' absent; no 'astropy' token anywhere in the view.
5. Patched repo symbols (L2/L3/L5): gold's only distinctive changed symbol is 'convert_data_to_col'. Absent from every spec-view identifier and from every comment/docstring. Also checked 'NdarrayMixin', 'MaskedColumn', 'Column', 'isinstance' as identifiers -- the model's vocabulary is deliberately abstract ('select_column_kind', 'selected_kind', KIND_MIXIN/SEQ_MIXIN/MASKED/COLUMN, is_column/is_mixin/is_structured/is_masked/seq_masked). The one occurrence of the word 'isinstance' (line 51, backtick-quoted) is a statement about what Nagini CANNOT execute, not a repo-symbol reference, and gold's changed symbol set does not contain it.
6. Fix-introduced identifiers (L5): `_patch_new_symbols`(gold) is empty (a pure deletion), so this leg is vacuous.
7. Narration (L3): zero hits for the whole `_NARRATION` vocabulary -- bug/fix/patch/regression/previously/incorrectly/wrong/broken/reverted/deleted -- across all comments and docstrings. Also hand-searched for edit-shaped phrasing: '12644', '5.2', 'FutureWarning', 'delete', 'remove', 'no longer', 'revert', 'line 1239', 'instead of' -> all absent. This is the interesting part of this bundle: the genuinely edit-narrating prose ('the structured-array clause is NOT present, so a structured array falls through to the masked / plain branch', 'Faithful skeleton of the if/elif chain', 'mirrors one branch of the real method', 'the unchanged sequence-conversion branch') is real narration, but it lives ENTIRELY inside the impl region and is therefore elided. I verified each of those strings is absent from the projected view. The elision is doing load-bearing work here, not decoration.
8. Test-leak vectors (not screened by the python flavor, checked anyway): test file paths 'astropy/table/tests/test_mixin.py' / 'test_table.py' absent; test symbols test_ndarray_mixin, test_structured_masked_column, test_data_to_col_convert_strategy, test_skycoord_representation absent; the parametrization id 'as_ndarray_mixin' and the local 'class_exp' absent; no test-patch line >=16 normalized chars reproduced.
9. Hints-only vocabulary (the failure mode spec_guide.md calls most common): computed the set of >=4-char tokens in hints_text minus those in problem_statement -> 36 terms ('crippled', 'repr', 'delete', 'lines', 'no longer', 'compatible', ...). Intersected with the spec view: the only hit is the English stopword 'with'. No hints-only diagnosis vocabulary is echoed.

CLOSEST CALL, AND WHY IT IS NOT LEAKAGE. The strongest candidate is the docstring paragraph at lines 35-38 plus the paired postconditions at 166-171 ('a masked one yields a masked column and an unmasked one yields an ordinary column. Its structured layout does NOT divert it into the mixin kind'). This pins the masked-structured case, which the issue body does not spell out and which the hidden test test_structured_masked_column exercises. I considered whether this is gold-reconstruction beyond problem_statement and concluded no, on two independent grounds.

(a) The issue explicitly states the desired end behaviour -- 'the structured array will be added as a Column' and 'Change the behavior in 5.2 by removing this clause' -- so 'a structured array is no longer diverted into the mixin kind' is squarely public; the spec states that outcome as a behavioural contract, never as an edit. (b) The masked/unmasked split is not extra information the spec injects: it is the pre-existing base-commit cascade, which the solver reads directly. I opened the base worktree at 6ed769d58d and confirmed astropy/table/table.py:1286 already contains 'elif isinstance(data, (np.ma.MaskedArray, Masked)): col_cls = masked_col_cls' immediately below the clause the issue quotes.

Once the quoted clause stops firing, a masked structured array reaching that surviving elif is a mechanical consequence of code the solver has in front of them -- the spec is restating the visible cascade's first-match order, which any faithful spec of this function must do, not disclosing a hidden discriminator. This is the legitimate 'state the abstract desired behaviour the issue demands' side of the line, and crucially it does not tell the solver WHICH clause to delete or WHERE: nothing in the view names the function, the file, the mixin class, or the dtype-length test.

Second-closest: line 64 'the modelled delta is a pure boolean decision procedure' uses the word 'delta', and line 165 says 'this is the discriminating clause the spec pins'. Neither names a repo symbol, quotes a diff line, or narrates a bug->fix mechanism; 'delta' here describes the modelling scope (why the axioms region is empty), and 'clause' refers to the spec's own Ensures, not to the deleted source clause. Both are meta-commentary about the artifact, not edit-localization. I do not consider either a leak, though line 165's 'discriminating clause the spec pins' is the sort of phrasing that invites a re-read on a future revision.

One process caveat, per my own standing note: 'clause', 'delta' and 'discriminating' are exactly the measure-justification vocabulary that has tripped the leak screen on prose alone in past runs. I checked them against the actual `_NARRATION` list rather than by feel -- none of the three is in it, and the screen agrees.

**CONCLUSION.** Every mechanical leg is negative, the harness gate passes, no hints-only vocabulary is echoed, all genuine edit narration is confined to the elided impl region, and the one semantically strong docstring claim is either explicitly public in the issue or a direct consequence of unmodified base-commit code the solver can read. Verdict NO-LEAKAGE.

**Scratch:**  (problem.txt, hints.txt, patch.diff, test_patch.diff, spec_view.py).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
