# P2 adversarial audit — pydata__xarray-3095

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # A distinguished code for "no explicit element type supplied" (re-derive it).
@@ -46,10 +45,6 @@
 
     def __init__(self, array_kind: int, stored_dtype: int) -> None:
         Requires(stored_dtype != NO_DTYPE)
-        # Level 1: the constructor is a leaf (two field writes, no obligated
-        # callee), and it must sit strictly BELOW every caller's level so the
-        # caller can hand its obligation down without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
         Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
         Ensures(self.array_kind == array_kind)    # type: ignore
@@ -91,7 +86,6 @@
     Requires(self.stored_dtype != NO_DTYPE)
     # a buffer always has some re-derivable element type (never the sentinel).
     Requires(self.array_kind != NO_DTYPE)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.array_kind, 1 / 2))
@@ -106,10 +100,8 @@
     Ensures(Result() == Old(self.stored_dtype))
     # post-conditions-end
     # impl-start
-    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
-    # so its reported type is carried over rather than re-derived.
+    # Re-derive from the duplicated buffer (drop the stored dtype) -- the bug.
     array_kind = self.array_kind
-    dtype = self.stored_dtype
-    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
+    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, NO_DTYPE))
     return duplicate.stored_dtype
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # A distinguished code for "no explicit element type supplied" (re-derive it).
@@ -46,10 +45,6 @@
 
     def __init__(self, array_kind: int, stored_dtype: int) -> None:
         Requires(stored_dtype != NO_DTYPE)
-        # Level 1: the constructor is a leaf (two field writes, no obligated
-        # callee), and it must sit strictly BELOW every caller's level so the
-        # caller can hand its obligation down without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
         Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
         Ensures(self.array_kind == array_kind)    # type: ignore
@@ -91,7 +86,6 @@
     Requires(self.stored_dtype != NO_DTYPE)
     # a buffer always has some re-derivable element type (never the sentinel).
     Requires(self.array_kind != NO_DTYPE)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.array_kind, 1 / 2))
@@ -106,10 +100,10 @@
     Ensures(Result() == Old(self.stored_dtype))
     # post-conditions-end
     # impl-start
-    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
-    # so its reported type is carried over rather than re-derived.
+    # Partial-domain: preserve only when re-derivation would agree anyway.
     array_kind = self.array_kind
     dtype = self.stored_dtype
-    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
-    return duplicate.stored_dtype
+    if array_kind == dtype:
+        return dtype
+    return array_kind
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # A distinguished code for "no explicit element type supplied" (re-derive it).
@@ -46,10 +45,6 @@
 
     def __init__(self, array_kind: int, stored_dtype: int) -> None:
         Requires(stored_dtype != NO_DTYPE)
-        # Level 1: the constructor is a leaf (two field writes, no obligated
-        # callee), and it must sit strictly BELOW every caller's level so the
-        # caller can hand its obligation down without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
         Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
         Ensures(self.array_kind == array_kind)    # type: ignore
@@ -91,7 +86,6 @@
     Requires(self.stored_dtype != NO_DTYPE)
     # a buffer always has some re-derivable element type (never the sentinel).
     Requires(self.array_kind != NO_DTYPE)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.array_kind, 1 / 2))
@@ -106,10 +100,9 @@
     Ensures(Result() == Old(self.stored_dtype))
     # post-conditions-end
     # impl-start
-    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
-    # so its reported type is carried over rather than re-derived.
+    # Boundary/arg-swap: pass array_kind as the 'given' dtype -> used verbatim.
     array_kind = self.array_kind
     dtype = self.stored_dtype
-    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
+    duplicate = IndexWrapper(dtype, derive_dtype(dtype, array_kind))
     return duplicate.stored_dtype
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # A distinguished code for "no explicit element type supplied" (re-derive it).
@@ -46,10 +45,6 @@
 
     def __init__(self, array_kind: int, stored_dtype: int) -> None:
         Requires(stored_dtype != NO_DTYPE)
-        # Level 1: the constructor is a leaf (two field writes, no obligated
-        # callee), and it must sit strictly BELOW every caller's level so the
-        # caller can hand its obligation down without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
         Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
         Ensures(self.array_kind == array_kind)    # type: ignore
@@ -91,7 +86,6 @@
     Requires(self.stored_dtype != NO_DTYPE)
     # a buffer always has some re-derivable element type (never the sentinel).
     Requires(self.array_kind != NO_DTYPE)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.array_kind, 1 / 2))
@@ -106,10 +100,8 @@
     Ensures(Result() == Old(self.stored_dtype))
     # post-conditions-end
     # impl-start
-    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
-    # so its reported type is carried over rather than re-derived.
-    array_kind = self.array_kind
-    dtype = self.stored_dtype
-    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
-    return duplicate.stored_dtype
+    # Effect attack: overwrite the original's stored_dtype to satisfy the
+    # postcondition vacuously (blocked by fractional read-only permission).
+    self.stored_dtype = self.array_kind
+    return self.stored_dtype
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # A distinguished code for "no explicit element type supplied" (re-derive it).
@@ -46,10 +45,6 @@
 
     def __init__(self, array_kind: int, stored_dtype: int) -> None:
         Requires(stored_dtype != NO_DTYPE)
-        # Level 1: the constructor is a leaf (two field writes, no obligated
-        # callee), and it must sit strictly BELOW every caller's level so the
-        # caller can hand its obligation down without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
         Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
         Ensures(self.array_kind == array_kind)    # type: ignore
@@ -91,7 +86,6 @@
     Requires(self.stored_dtype != NO_DTYPE)
     # a buffer always has some re-derivable element type (never the sentinel).
     Requires(self.array_kind != NO_DTYPE)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.array_kind, 1 / 2))
@@ -106,10 +100,6 @@
     Ensures(Result() == Old(self.stored_dtype))
     # post-conditions-end
     # impl-start
-    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
-    # so its reported type is carried over rather than re-derived.
-    array_kind = self.array_kind
-    dtype = self.stored_dtype
-    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
-    return duplicate.stored_dtype
+    # Ungrounded-oracle echo: always report the generic object code.
+    return OBJECT_DTYPE
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # A distinguished code for "no explicit element type supplied" (re-derive it).
@@ -46,10 +45,6 @@
 
     def __init__(self, array_kind: int, stored_dtype: int) -> None:
         Requires(stored_dtype != NO_DTYPE)
-        # Level 1: the constructor is a leaf (two field writes, no obligated
-        # callee), and it must sit strictly BELOW every caller's level so the
-        # caller can hand its obligation down without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
         Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
         Ensures(self.array_kind == array_kind)    # type: ignore
@@ -91,7 +86,6 @@
     Requires(self.stored_dtype != NO_DTYPE)
     # a buffer always has some re-derivable element type (never the sentinel).
     Requires(self.array_kind != NO_DTYPE)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.array_kind, 1 / 2))
@@ -106,10 +100,6 @@
     Ensures(Result() == Old(self.stored_dtype))
     # post-conditions-end
     # impl-start
-    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
-    # so its reported type is carried over rather than re-derived.
-    array_kind = self.array_kind
-    dtype = self.stored_dtype
-    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
-    return duplicate.stored_dtype
+    # Return the re-derived buffer kind directly (drops the stored dtype).
+    return self.array_kind
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # A distinguished code for "no explicit element type supplied" (re-derive it).
@@ -46,10 +45,6 @@
 
     def __init__(self, array_kind: int, stored_dtype: int) -> None:
         Requires(stored_dtype != NO_DTYPE)
-        # Level 1: the constructor is a leaf (two field writes, no obligated
-        # callee), and it must sit strictly BELOW every caller's level so the
-        # caller can hand its obligation down without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
         Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
         Ensures(self.array_kind == array_kind)    # type: ignore
@@ -91,7 +86,6 @@
     Requires(self.stored_dtype != NO_DTYPE)
     # a buffer always has some re-derivable element type (never the sentinel).
     Requires(self.array_kind != NO_DTYPE)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.array_kind, 1 / 2))
@@ -106,10 +100,6 @@
     Ensures(Result() == Old(self.stored_dtype))
     # post-conditions-end
     # impl-start
-    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
-    # so its reported type is carried over rather than re-derived.
-    array_kind = self.array_kind
-    dtype = self.stored_dtype
-    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
-    return duplicate.stored_dtype
+    # Correct echo: report the original's stored element type directly.
+    return self.stored_dtype
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # A distinguished code for "no explicit element type supplied" (re-derive it).
@@ -46,10 +45,6 @@
 
     def __init__(self, array_kind: int, stored_dtype: int) -> None:
         Requires(stored_dtype != NO_DTYPE)
-        # Level 1: the constructor is a leaf (two field writes, no obligated
-        # callee), and it must sit strictly BELOW every caller's level so the
-        # caller can hand its obligation down without an obligation leak.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
         Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
         Ensures(self.array_kind == array_kind)    # type: ignore
@@ -91,7 +86,6 @@
     Requires(self.stored_dtype != NO_DTYPE)
     # a buffer always has some re-derivable element type (never the sentinel).
     Requires(self.array_kind != NO_DTYPE)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(self.array_kind, 1 / 2))
@@ -106,10 +100,10 @@
     Ensures(Result() == Old(self.stored_dtype))
     # post-conditions-end
     # impl-start
-    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
-    # so its reported type is carried over rather than re-derived.
+    # Correct variant: reconstruct supplying the original dtype verbatim,
+    # but read the return straight from the passed dtype value.
     array_kind = self.array_kind
     dtype = self.stored_dtype
-    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
+    duplicate = IndexWrapper(array_kind, dtype)
     return duplicate.stored_dtype
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-3095.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A labelled-index wrapper preserves the element type (dtype) it was created
  with. When such a wrapper is duplicated — whether the duplication makes an
  independent copy of the underlying buffer or merely shares it — the duplicate
  must report the SAME element type as the original.

  This matters because re-deriving the element type from a freshly materialised
  buffer is lossy for some types: a buffer holding fixed-width text, once it has
  round-tripped through the general-purpose index machinery, can no longer be
  distinguished from a buffer of arbitrary Python objects, so a re-derivation
  would report the generic "object" type instead of the original text type.
  The contract therefore requires the duplicate to carry over the element type
  the original was constructed with, rather than recomputing it from the
  duplicated buffer.

The wrapper is modelled as a minimal class carrying only the facts that decide
the reported element type:

  * ``stored_dtype``  — the element-type code the wrapper was created with;
  * ``array_kind``    — the type code that WOULD be re-derived from the wrapper's
                        underlying buffer if no element type were supplied.

These two can disagree precisely for the fixed-width-text case, where
``stored_dtype`` is the text code while a re-derivation of ``array_kind`` yields
the generic object code. Element-type codes and re-derivation are modelled
deeply (``derive_dtype``); there is no consumed axiom. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# A distinguished code for "no explicit element type supplied" (re-derive it).
NO_DTYPE = -1            # type: int
# The generic object element-type code (the lossy fallback).
OBJECT_DTYPE = 0         # type: int


class IndexWrapper:
    """A wrapper around a labelled index. ``stored_dtype`` is the element-type
    code the wrapper reports; ``array_kind`` is the type code that would be
    re-derived from the underlying buffer with no element type supplied."""

    def __init__(self, array_kind: int, stored_dtype: int) -> None:
        Requires(stored_dtype != NO_DTYPE)
        Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
        Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
        Ensures(self.array_kind == array_kind)    # type: ignore
        Ensures(self.stored_dtype == stored_dtype)  # type: ignore
        self.array_kind = array_kind
        self.stored_dtype = stored_dtype


# axioms-start
# (no @ContractOnly callees: the element-type re-derivation is modelled deeply
# below as derive_dtype, validated against the real wrapper construction by
# axiom_check.py / G-AX, not consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def derive_dtype(array_kind: int, given_dtype: int) -> int:
    """The element-type code a freshly constructed wrapper reports, given the
    re-derivable type code of its buffer (``array_kind``) and an optionally
    supplied element-type code (``given_dtype``).

    When an element type IS supplied (``given_dtype != NO_DTYPE``) it is used
    verbatim. When none is supplied the type is re-derived from the buffer —
    which is the lossy step: a fixed-width-text buffer that has round-tripped
    through the general index machinery re-derives to OBJECT_DTYPE, so any
    ``array_kind`` may legitimately re-derive to the generic object code.
    """
    if given_dtype != NO_DTYPE:
        return given_dtype
    return array_kind
# pure-end


def adapter_copy(self: IndexWrapper, deep: bool) -> int:
    # pre-conditions-start
    Requires(Acc(self.array_kind, 1 / 2))
    Requires(Acc(self.stored_dtype, 1 / 2))
    Requires(self.stored_dtype != NO_DTYPE)
    # a buffer always has some re-derivable element type (never the sentinel).
    Requires(self.array_kind != NO_DTYPE)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.array_kind, 1 / 2))
    Ensures(Acc(self.stored_dtype, 1 / 2))
    # the read-only original is unchanged.
    Ensures(self.array_kind == Old(self.array_kind))
    Ensures(self.stored_dtype == Old(self.stored_dtype))
    # The duplicate reports the SAME element type the original carried, never a
    # type re-derived from the duplicated buffer. This is the discriminating
    # guarantee: it must hold even when a re-derivation would differ (the
    # fixed-width-text case, where re-derivation collapses to the object code).
    Ensures(Result() == Old(self.stored_dtype))
    # post-conditions-end
    # impl-start
    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
    # so its reported type is carried over rather than re-derived.
    array_kind = self.array_kind
    dtype = self.stored_dtype
    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
    return duplicate.stored_dtype
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 Project root: (SBU_BENCHMARK_DIR=.../benchmark-verified; python=python; docker via `docker`).

SPEC (frozen): adapter_copy(self,deep)->int with Requires(Acc(array_kind,1/2),Acc(stored_dtype,1/2), stored_dtype!=NO_DTYPE, array_kind!=NO_DTYPE); Ensures(Acc x2 @1/2, array_kind==Old(array_kind), stored_dtype==Old(stored_dtype), Result()==Old(self.stored_dtype)). @Pure derive_dtype returns given verbatim unless NO_DTYPE else array_kind. The postcondition Result()==Old(stored_dtype) + fractional read-only perms + Old-equality frame are the discriminators.

8 attacks built by editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); all 8 confirmed SAME-spec via `adversary same-spec`.

WEAKNESS results (`python -m swebench_unified.adversary weakness nagini pydata__xarray-3095 <atk>`):
- atk_1 (re-derive bug echo = prepatch essence): exit2 NOT-A-CE. Direct verify: 'Postcondition of adapter_copy might not hold. Assertion (Result()==Old(self.stored_dtype)) might not hold' -> spec catches the prepatch bug (PREPATCH REPRODUCED).
- atk_2 (partial-domain: preserve only when array_kind==stored_dtype): exit2, does not verify.
- atk_3 (boundary/arg-swap: derive_dtype(dtype,array_kind) -> array_kind verbatim): exit2, does not verify.
- atk_4 (control-flow-effect: self.stored_dtype=self.array_kind to satisfy vacuously): exit2. Direct verify: 'Assignment might fail. There might be insufficient permission to access self.stored_dtype' -> fractional read-only perm (refinement.md C) blocks the mutation cheat.
- atk_5 (ungrounded-oracle echo: return OBJECT_DTYPE): exit2, does not verify.
- atk_6 (return self.array_kind directly): exit2, does not verify.
- atk_7 (CORRECT echo: return self.stored_dtype): exit0 CANDIDATE (shares spec AND verifies).
- atk_8 (CORRECT reconstruct: IndexWrapper(array_kind,dtype); return duplicate.stored_dtype): exit0 CANDIDATE.
Positive control (model.py) verifies: `nagini_verify.sh` Verification successful 7.72s.

MANDATORY RESOLVE ON CANDIDATES: atk_7 and atk_8 are behaviorally-correct echoes. Under the R-map (stored_dtype<->_dtype, array_kind<->rederived buffer dtype, deep dtype-irrelevant) each faithful refined patch is the gold PandasIndexAdapter.copy returning PandasIndexAdapter(array,self._dtype) + the caller rewire + the else: dtype=np.dtype(dtype) hunk => the gold patch verbatim (byte-identical, sha len 4029). Materialized patch_atk_7.diff / patch_atk_8.diff. EXECUTED run_resolve('pydata__xarray-3095', patch, timeout=1800): resolved=True, completed=True, attempts=1, flaky=False, note='resolved'. Both candidates RESOLVE -> no verify-not-correct gap.

REFINEMENT.MD AUDIT: legs A1(R),A2(R),A3(R/I),A4(A-reference),A5(R); section D confirms NO kind-3 and NO consumed @ContractOnly axiom; the sole A-leg (A4) is an A-reference: deep derive_dtype/adapter_copy validated == real PandasIndexAdapter.__init__/copy by G-AX/axiom_check.py (meta.json G-AX exit0 apply_gold, F1/F2/F3). A4/A5 correspondence confirmed against the gold hunks (copy returns PandasIndexAdapter(array,self._dtype); else: dtype=np.dtype(dtype)). Correspondence holds.

CONCLUSION: 6 distinct verifying-wrong-impl attack classes all rejected by the spec via genuine postcondition/permission failures; the only verifying candidates are correct and their materialized faithful patches RESOLVE under the official harness. verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-3095.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A labelled-index wrapper preserves the element type (dtype) it was created
  with. When such a wrapper is duplicated — whether the duplication makes an
  independent copy of the underlying buffer or merely shares it — the duplicate
  must report the SAME element type as the original.

  This matters because re-deriving the element type from a freshly materialised
  buffer is lossy for some types: a buffer holding fixed-width text, once it has
  round-tripped through the general-purpose index machinery, can no longer be
  distinguished from a buffer of arbitrary Python objects, so a re-derivation
  would report the generic "object" type instead of the original text type.
  The contract therefore requires the duplicate to carry over the element type
  the original was constructed with, rather than recomputing it from the
  duplicated buffer.

The wrapper is modelled as a minimal class carrying only the facts that decide
the reported element type:

  * ``stored_dtype``  — the element-type code the wrapper was created with;
  * ``array_kind``    — the type code that WOULD be re-derived from the wrapper's
                        underlying buffer if no element type were supplied.

These two can disagree precisely for the fixed-width-text case, where
``stored_dtype`` is the text code while a re-derivation of ``array_kind`` yields
the generic object code. Element-type codes and re-derivation are modelled
deeply (``derive_dtype``); there is no consumed axiom. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# A distinguished code for "no explicit element type supplied" (re-derive it).
NO_DTYPE = -1            # type: int
# The generic object element-type code (the lossy fallback).
OBJECT_DTYPE = 0         # type: int


class IndexWrapper:
    """A wrapper around a labelled index. ``stored_dtype`` is the element-type
    code the wrapper reports; ``array_kind`` is the type code that would be
    re-derived from the underlying buffer with no element type supplied."""

    def __init__(self, array_kind: int, stored_dtype: int) -> None:
        Requires(stored_dtype != NO_DTYPE)
        Ensures(Acc(self.array_kind, 1 / 2))      # type: ignore
        Ensures(Acc(self.stored_dtype, 1 / 2))    # type: ignore
        Ensures(self.array_kind == array_kind)    # type: ignore
        Ensures(self.stored_dtype == stored_dtype)  # type: ignore
        self.array_kind = array_kind
        self.stored_dtype = stored_dtype


# axioms-start
# (no @ContractOnly callees: the element-type re-derivation is modelled deeply
# below as derive_dtype, validated against the real wrapper construction by
# axiom_check.py / G-AX, not consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def derive_dtype(array_kind: int, given_dtype: int) -> int:
    """The element-type code a freshly constructed wrapper reports, given the
    re-derivable type code of its buffer (``array_kind``) and an optionally
    supplied element-type code (``given_dtype``).

    When an element type IS supplied (``given_dtype != NO_DTYPE``) it is used
    verbatim. When none is supplied the type is re-derived from the buffer —
    which is the lossy step: a fixed-width-text buffer that has round-tripped
    through the general index machinery re-derives to OBJECT_DTYPE, so any
    ``array_kind`` may legitimately re-derive to the generic object code.
    """
    if given_dtype != NO_DTYPE:
        return given_dtype
    return array_kind
# pure-end


def adapter_copy(self: IndexWrapper, deep: bool) -> int:
    # pre-conditions-start
    Requires(Acc(self.array_kind, 1 / 2))
    Requires(Acc(self.stored_dtype, 1 / 2))
    Requires(self.stored_dtype != NO_DTYPE)
    # a buffer always has some re-derivable element type (never the sentinel).
    Requires(self.array_kind != NO_DTYPE)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.array_kind, 1 / 2))
    Ensures(Acc(self.stored_dtype, 1 / 2))
    # the read-only original is unchanged.
    Ensures(self.array_kind == Old(self.array_kind))
    Ensures(self.stored_dtype == Old(self.stored_dtype))
    # The duplicate reports the SAME element type the original carried, never a
    # type re-derived from the duplicated buffer. This is the discriminating
    # guarantee: it must hold even when a re-derivation would differ (the
    # fixed-width-text case, where re-derivation collapses to the object code).
    Ensures(Result() == Old(self.stored_dtype))
    # post-conditions-end
    # impl-start
    # Mirror the fix: rebuild the wrapper supplying the ORIGINAL element type,
    # so its reported type is carried over rather than re-derived.
    array_kind = self.array_kind
    dtype = self.stored_dtype
    duplicate = IndexWrapper(array_kind, derive_dtype(array_kind, dtype))
    return duplicate.stored_dtype
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

 Project root: (SBU_BENCHMARK_DIR=.../benchmark-verified; python=python; docker via `docker`).

SPEC (frozen): adapter_copy(self,deep)->int with Requires(Acc(array_kind,1/2),Acc(stored_dtype,1/2), stored_dtype!=NO_DTYPE, array_kind!=NO_DTYPE); Ensures(Acc x2 @1/2, array_kind==Old(array_kind), stored_dtype==Old(stored_dtype), Result()==Old(self.stored_dtype)). @Pure derive_dtype returns given verbatim unless NO_DTYPE else array_kind. The postcondition Result()==Old(stored_dtype) + fractional read-only perms + Old-equality frame are the discriminators.

8 attacks built by editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical); all 8 confirmed SAME-spec via `adversary same-spec`.

WEAKNESS results (`python -m swebench_unified.adversary weakness nagini pydata__xarray-3095 <atk>`):
- atk_1 (re-derive bug echo = prepatch essence): exit2 NOT-A-CE. Direct verify: 'Postcondition of adapter_copy might not hold. Assertion (Result()==Old(self.stored_dtype)) might not hold' -> spec catches the prepatch bug (PREPATCH REPRODUCED).
- atk_2 (partial-domain: preserve only when array_kind==stored_dtype): exit2, does not verify.
- atk_3 (boundary/arg-swap: derive_dtype(dtype,array_kind) -> array_kind verbatim): exit2, does not verify.
- atk_4 (control-flow-effect: self.stored_dtype=self.array_kind to satisfy vacuously): exit2. Direct verify: 'Assignment might fail. There might be insufficient permission to access self.stored_dtype' -> fractional read-only perm (refinement.md C) blocks the mutation cheat.
- atk_5 (ungrounded-oracle echo: return OBJECT_DTYPE): exit2, does not verify.
- atk_6 (return self.array_kind directly): exit2, does not verify.
- atk_7 (CORRECT echo: return self.stored_dtype): exit0 CANDIDATE (shares spec AND verifies).
- atk_8 (CORRECT reconstruct: IndexWrapper(array_kind,dtype); return duplicate.stored_dtype): exit0 CANDIDATE.
Positive control (model.py) verifies: `nagini_verify.sh` Verification successful 7.72s.

MANDATORY RESOLVE ON CANDIDATES: atk_7 and atk_8 are behaviorally-correct echoes. Under the R-map (stored_dtype<->_dtype, array_kind<->rederived buffer dtype, deep dtype-irrelevant) each faithful refined patch is the gold PandasIndexAdapter.copy returning PandasIndexAdapter(array,self._dtype) + the caller rewire + the else: dtype=np.dtype(dtype) hunk => the gold patch verbatim (byte-identical, sha len 4029). Materialized patch_atk_7.diff / patch_atk_8.diff. EXECUTED run_resolve('pydata__xarray-3095', patch, timeout=1800): resolved=True, completed=True, attempts=1, flaky=False, note='resolved'. Both candidates RESOLVE -> no verify-not-correct gap.

REFINEMENT.MD AUDIT: legs A1(R),A2(R),A3(R/I),A4(A-reference),A5(R); section D confirms NO kind-3 and NO consumed @ContractOnly axiom; the sole A-leg (A4) is an A-reference: deep derive_dtype/adapter_copy validated == real PandasIndexAdapter.__init__/copy by G-AX/axiom_check.py (meta.json G-AX exit0 apply_gold, F1/F2/F3). A4/A5 correspondence confirmed against the gold hunks (copy returns PandasIndexAdapter(array,self._dtype); else: dtype=np.dtype(dtype)). Correspondence holds.

CONCLUSION: 6 distinct verifying-wrong-impl attack classes all rejected by the spec via genuine postcondition/permission failures; the only verifying candidates are correct and their materialized faithful patches RESOLVE under the official harness. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no divergence found. The modeled adapter_copy pins Result()==Old(self.stored_dtype) (duplicate always reports the original's stored element type). Real callee = patch's new PandasIndexAdapter.copy: `array = self.array.copy(deep=True) if deep else self.array; return PandasIndexAdapter(array, self._dtype)`, which via __init__'s patched `else: dtype = np.dtype(dtype)` sets duplicate.dtype = np.dtype(self._dtype). Since self._dtype is always an already-normalized np.dtype (idempotent under np.dtype) and never None, the duplicate's dtype equals the original's on every input — exactly the modeled postcondition. Evidence, all against the REAL patched callee (gold patch applied to at base_commit 1757dff): bundle conformance_check.py exit 0 over 100,154 inputs (boundary matrix + 100k fuzz, seed 3095), zero disagreements; bundle axiom_check.py (G-AX F1/F2/F3 against real PandasIndexAdapter + IndexVariable) exit 0; my independent differential probe of 310 inputs (text/int/float/bool/complex/datetime/timedelta/period/categorical/object buffers + MultiIndex, × supplied dtypes {None,O,<U3,<U32,int64,int32,float64,float32,bool,complex128,M8,m8} × deep∈{True,False}) found 0 dtype divergences — only construction-time exceptions that never reach copy. Confirmed self._dtype is never None post-construction, so the domain restriction stored_dtype != NO_DTYPE excludes no real copy invocation. Model verifies under pinned Nagini (6.88s); spec region byte-identical (same-spec exit 0 on identity). The spec is not too strong: it captures precisely the discriminating dtype-preservation guarantee (including the <U* case where re-derivation collapses to object) without over-strengthening. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified: spec_view(model.py, nagini) reproduced byte-for-byte; its sha256 (2eada5fb...1bed265) matches meta.json region_hashes.spec_view, and the impl region is elided ('... implementation elided — supplied by the consumer'). The public problem_statement already discloses the full desired behaviour: copy(deep=True/False) must NOT cast '<U*' (fixed-width unicode) IndexVariables to object — dtype must be preserved across duplication (with a worked <U3->object example). The spec view only restates this in abstracted, repo-agnostic terms (a wrapper preserves the element type it was constructed with; a duplicate must report the SAME element type; postcondition Result() == Old(self.stored_dtype)), plus an explanation of WHY re-derivation is lossy for fixed-width text — a mechanism explanation, not the gold code.

Lexical screen over the spec view for gold-edit tokens: NONE present. PandasIndexAdapter, IndexVariable.copy, indexing.py, variable.py, self._data, standalone _dtype, np.dtype, safe_cast_to_index, deep=deep, npcompat, DTypeLike all ABSENT from the solver's view (the sole substring hit for '_dtype' is inside stored_dtype/derive_dtype, not the repo attribute). None of the gold's discriminating edits are disclosed: no 'add a copy method', no 'else: dtype = np.dtype(dtype)', no 'self._data.copy(deep=deep)' rewire, no 'pass self._dtype'. Those repo symbols appear only in audit artifacts (mapping.md/refinement.md/meta.json), not the spec view.

The consumer must still author the duplication implementation and locate it in the real repo; the postcondition is a faithful abstraction of the public bug report and does not exceed it. Concurs with recorded G-LEAK (spec view clean) and G-PANEL-3.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
