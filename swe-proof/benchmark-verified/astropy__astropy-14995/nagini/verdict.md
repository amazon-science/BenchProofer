# P2 adversarial audit — astropy__astropy-14995

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
@@ -39,7 +39,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -165,9 +164,6 @@
     elif not self_has_mask:
         c = copy_seq(operand.mask)
         return MaskResult(True, c)
-    elif not operand.has_mask:
-        c = copy_seq(self_mask)
-        return MaskResult(True, c)
     else:
         c = apply_combiner(self_mask, operand.mask)
         return MaskResult(True, c)
@@ -177,7 +173,6 @@
 def copy_seq(xs: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -193,7 +188,6 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(xs))
         Invariant(ToSeq(out) == ToSeq(xs).take(i))
-        Invariant(MustTerminate(len(xs) - i + 1))
         # invariants-end
         out.append(xs[i])
         Assert(ToSeq(xs).take(i + 1) == ToSeq(xs).take(i) + PSeq(xs[i]))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -163,10 +162,10 @@
     if (not self_has_mask and not operand.has_mask) or not handle_mask_present:
         return MaskResult(False, empty)
     elif not self_has_mask:
-        c = copy_seq(operand.mask)
+        c = copy_seq(self_mask)
         return MaskResult(True, c)
     elif not operand.has_mask:
-        c = copy_seq(self_mask)
+        c = copy_seq(operand.mask)
         return MaskResult(True, c)
     else:
         c = apply_combiner(self_mask, operand.mask)
@@ -177,7 +176,6 @@
 def copy_seq(xs: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -193,7 +191,6 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(xs))
         Invariant(ToSeq(out) == ToSeq(xs).take(i))
-        Invariant(MustTerminate(len(xs) - i + 1))
         # invariants-end
         out.append(xs[i])
         Assert(ToSeq(xs).take(i + 1) == ToSeq(xs).take(i) + PSeq(xs[i]))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -166,7 +165,7 @@
         c = copy_seq(operand.mask)
         return MaskResult(True, c)
     elif not operand.has_mask:
-        c = copy_seq(self_mask)
+        c = copy_seq(operand.mask)
         return MaskResult(True, c)
     else:
         c = apply_combiner(self_mask, operand.mask)
@@ -177,7 +176,6 @@
 def copy_seq(xs: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -193,7 +191,6 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(xs))
         Invariant(ToSeq(out) == ToSeq(xs).take(i))
-        Invariant(MustTerminate(len(xs) - i + 1))
         # invariants-end
         out.append(xs[i])
         Assert(ToSeq(xs).take(i + 1) == ToSeq(xs).take(i) + PSeq(xs[i]))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -161,7 +160,7 @@
     # impl-start
     empty = []  # type: List[int]
     if (not self_has_mask and not operand.has_mask) or not handle_mask_present:
-        return MaskResult(False, empty)
+        return MaskResult(True, empty)
     elif not self_has_mask:
         c = copy_seq(operand.mask)
         return MaskResult(True, c)
@@ -177,7 +176,6 @@
 def copy_seq(xs: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -193,7 +191,6 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(xs))
         Invariant(ToSeq(out) == ToSeq(xs).take(i))
-        Invariant(MustTerminate(len(xs) - i + 1))
         # invariants-end
         out.append(xs[i])
         Assert(ToSeq(xs).take(i + 1) == ToSeq(xs).take(i) + PSeq(xs[i]))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -169,7 +168,7 @@
         c = copy_seq(self_mask)
         return MaskResult(True, c)
     else:
-        c = apply_combiner(self_mask, operand.mask)
+        c = copy_seq(self_mask)
         return MaskResult(True, c)
     # impl-end
 
@@ -177,7 +176,6 @@
 def copy_seq(xs: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -193,7 +191,6 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(xs))
         Invariant(ToSeq(out) == ToSeq(xs).take(i))
-        Invariant(MustTerminate(len(xs) - i + 1))
         # invariants-end
         out.append(xs[i])
         Assert(ToSeq(xs).take(i + 1) == ToSeq(xs).take(i) + PSeq(xs[i]))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -169,7 +168,7 @@
         c = copy_seq(self_mask)
         return MaskResult(True, c)
     else:
-        c = apply_combiner(self_mask, operand.mask)
+        c = apply_combiner(operand.mask, self_mask)
         return MaskResult(True, c)
     # impl-end
 
@@ -177,7 +176,6 @@
 def copy_seq(xs: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -193,7 +191,6 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(xs))
         Invariant(ToSeq(out) == ToSeq(xs).take(i))
-        Invariant(MustTerminate(len(xs) - i + 1))
         # invariants-end
         out.append(xs[i])
         Assert(ToSeq(xs).take(i + 1) == ToSeq(xs).take(i) + PSeq(xs[i]))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Operand:
@@ -160,8 +159,11 @@
     # post-conditions-end
     # impl-start
     empty = []  # type: List[int]
-    if (not self_has_mask and not operand.has_mask) or not handle_mask_present:
+    if not handle_mask_present:
         return MaskResult(False, empty)
+    elif not self_has_mask and not operand.has_mask:
+        c = apply_combiner(self_mask, operand.mask)
+        return MaskResult(True, c)
     elif not self_has_mask:
         c = copy_seq(operand.mask)
         return MaskResult(True, c)
@@ -177,7 +179,6 @@
 def copy_seq(xs: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(xs), 1 / 2))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(xs), 1 / 2))
@@ -193,7 +194,6 @@
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= i and i <= len(xs))
         Invariant(ToSeq(out) == ToSeq(xs).take(i))
-        Invariant(MustTerminate(len(xs) - i + 1))
         # invariants-end
         out.append(xs[i])
         Assert(ToSeq(xs).take(i + 1) == ToSeq(xs).take(i) + PSeq(xs[i]))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for astropy__astropy-14995.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A binary array operation combines two operands and must decide the array of
  per-element flags ("mask") carried by the result. Each operand may carry such
  a flag array or carry none at all. A combiner callable, when supplied, merges
  two present flag arrays element-by-element. The required result is:

    (1) no flags at all when neither operand carries flags, or when no combiner
        was supplied;
    (2) a copy of the *other* operand's flag array when this operand carries no
        flags but the other one does;
    (3) a copy of *this* operand's flag array when this operand carries flags
        and the other operand carries none — the lone present array is
        propagated unchanged, never combined against a missing array;
    (4) the element-wise combination of the two flag arrays (the combiner
        applied to both) when both operands carry them.

  The decision is symmetric in the two operands when only one carries flags:
  whichever operand has a flag array, that array (copied) is the result, and it
  must reach the result intact regardless of which side it came from. In
  particular case (3) is decided by the OTHER operand's flag array being absent,
  independently of any other attribute of that operand.

Flag arrays are modelled as ``List[int]`` (a bitmask of non-negative ints).
"Carries flags" / "carries none" is the boolean ``has_mask``. The decision
returns a small carrier (``MaskResult``) whose ``present`` flag says whether the
result has flags and whose ``data`` holds them when it does — the faithful
``Optional`` "mask or None" return. The element-wise combiner callable is the
UNCHANGED callee that is *invoked* in case (4); it is axiomatized opaquely as
``combine_masks`` (a per-element fold over equal-length arrays preserving the
shape) and its materializing call as ``apply_combiner``. Its soundness against
the real callee is checked by axiom_check.py (G-AX). The decision under
specification is the branch selection (cases 1-3), where the combiner is NOT
called; case (4) merely defers to the unchanged combiner.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class Operand:
    """The second operand: a minimal object carrying only its flag array.
    ``has_mask`` is False when the operand carries no flags; ``mask`` then holds
    no meaningful content (it is never read in that case)."""

    def __init__(self, has_mask: bool, mask: List[int]) -> None:
        Requires(Acc(list_pred(mask), 1 / 2))
        Ensures(Acc(self.has_mask) and self.has_mask == has_mask)  # type: ignore
        Ensures(Acc(self.mask) and self.mask is mask)  # type: ignore
        Ensures(Acc(list_pred(self.mask), 1 / 2))  # type: ignore
        self.has_mask = has_mask
        self.mask = mask


class MaskResult:
    """The decided result mask: ``present`` is False for "no flags" (the
    ``None`` mask); when True, ``data`` holds the flag array."""

    def __init__(self, present: bool, data: List[int]) -> None:
        Requires(Acc(list_pred(data), 1 / 2))
        Ensures(Acc(self.present) and self.present == present)  # type: ignore
        Ensures(Acc(self.data) and self.data is data)  # type: ignore
        Ensures(Acc(list_pred(self.data), 1 / 2))  # type: ignore
        Ensures(ToSeq(self.data) == ToSeq(data))  # type: ignore
        self.present = present
        self.data = data


# axioms-start
@Pure
@ContractOnly
def combine_masks(a: PSeq[int], b: PSeq[int]) -> PSeq[int]:
    """The unchanged element-wise combiner callable, applied to two present
    equal-length flag arrays (case 4 only — it is NEVER invoked when one array
    is absent). The weakest contract the proof needs: the combination has the
    same shape (length) as its inputs. Provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Ensures(Implies(len(a) == len(b), len(Result()) == len(a)))


@ContractOnly
def apply_combiner(a: List[int], b: List[int]) -> List[int]:
    """Materializing call to the unchanged combiner callable: returns a freshly
    allocated flag array whose content is exactly the abstract combination of
    the two inputs. Same callee as `combine_masks`; this is its impure (list-
    producing) face used inside the implementation. G-AX checks both against the
    real callee."""
    Requires(Acc(list_pred(a), 1 / 2))
    Requires(Acc(list_pred(b), 1 / 2))
    Requires(len(ToSeq(a)) == len(ToSeq(b)))
    Ensures(Acc(list_pred(a), 1 / 2))
    Ensures(Acc(list_pred(b), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == combine_masks(ToSeq(a), ToSeq(b)))
# axioms-end


# pure-start
# (No auxiliary pure spec functions: the combiner is opaque, axiomatized above;
# the branch selection cases 1-3 are stated directly over the flag arrays.)
# pure-end


def result_mask(
    self_has_mask: bool,
    self_mask: List[int],
    operand: Operand,
    handle_mask_present: bool,
) -> MaskResult:
    # pre-conditions-start
    Requires(Acc(list_pred(self_mask), 1 / 2))
    Requires(Acc(operand.has_mask, 1 / 2) and Acc(operand.mask, 1 / 2))
    Requires(Acc(list_pred(operand.mask), 1 / 2))
    # The two operands wrap co-shaped data, so their flag arrays are stored at
    # the same shape (the combiner is defined on equal-length arrays). This
    # holds regardless of which operand currently carries flags.
    Requires(len(ToSeq(self_mask)) == len(ToSeq(operand.mask)))
    # pre-conditions-end
    # post-conditions-start
    # read-only inputs are returned with their permission and value intact.
    Ensures(Acc(list_pred(self_mask), 1 / 2))
    Ensures(Acc(operand.has_mask, 1 / 2) and Acc(operand.mask, 1 / 2))
    Ensures(Acc(list_pred(operand.mask), 1 / 2))
    Ensures(operand.has_mask == Old(operand.has_mask)
            and operand.mask is Old(operand.mask))
    # the result carrier is fully formed.
    Ensures(Acc(Result().present) and Acc(Result().data)
            and Acc(list_pred(Result().data), 1 / 2))

    # (1) no flags when neither operand carries flags, or when no combiner.
    Ensures(Implies(not handle_mask_present, not Result().present))
    Ensures(Implies(handle_mask_present and not self_has_mask
                    and not operand.has_mask,
                    not Result().present))

    # (2) this operand has no flags, the other does: copy the other's array.
    Ensures(Implies(handle_mask_present and not self_has_mask
                    and operand.has_mask,
                    Result().present
                    and ToSeq(Result().data) == ToSeq(operand.mask)))

    # (3) this operand carries flags and the other carries none: the lone
    # present array is copied through unchanged, NOT combined against a missing
    # array. The decision turns on the OTHER operand's flag array being absent.
    Ensures(Implies(handle_mask_present and self_has_mask
                    and not operand.has_mask,
                    Result().present
                    and ToSeq(Result().data) == ToSeq(self_mask)))

    # (4) both operands carry flags: the element-wise combination, i.e. exactly
    # the unchanged combiner applied to both present arrays.
    Ensures(Implies(handle_mask_present and self_has_mask and operand.has_mask,
                    Result().present
                    and ToSeq(Result().data) == combine_masks(ToSeq(self_mask),
                                                              ToSeq(operand.mask))))
    # post-conditions-end
    # impl-start
    empty = []  # type: List[int]
    if (not self_has_mask and not operand.has_mask) or not handle_mask_present:
        return MaskResult(False, empty)
    elif not self_has_mask:
        c = copy_seq(operand.mask)
        return MaskResult(True, c)
    elif not operand.has_mask:
        c = copy_seq(self_mask)
        return MaskResult(True, c)
    else:
        c = apply_combiner(self_mask, operand.mask)
        return MaskResult(True, c)
    # impl-end


def copy_seq(xs: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(xs))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(xs):
        # invariants-start
        Invariant(Acc(list_pred(xs), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(xs))
        Invariant(ToSeq(out) == ToSeq(xs).take(i))
        # invariants-end
        out.append(xs[i])
        Assert(ToSeq(xs).take(i + 1) == ToSeq(xs).take(i) + PSeq(xs[i]))
        i = i + 1
    Assert(ToSeq(xs).take(len(xs)) == ToSeq(xs))
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for astropy__astropy-14995 (nagini).

SPEC SHAPE: result_mask's postconditions pin the FULL output (present flag + ToSeq(data) content) across every one of the 8 boolean combos of (handle_mask_present, self_has_mask, operand.has_mask). Cases 1-3 are stated directly over the flag arrays; case 4 defers to the opaque combine_masks. Because output content is fully constrained in each branch, any impl that decides a branch wrongly, copies the wrong array, mislabels present, or substitutes/echoes an array where the combiner is required cannot discharge the postcondition. This is a TIGHT spec.

POSITIVE CONTROL: copied model.py -> positive_control.py; `bash scripts/nagini_verify.sh positive_control.py` => VERIFIED (16.2s, exit 0).

ATTACKS (all copied from model.py, impl region ONLY edited; axioms/@Pure/Requires/Ensures byte-identical; all confirmed same-spec exit 0 via `adversary same-spec`). Each run via `python -m swebench_unified.adversary weakness nagini astropy__astropy-14995 <file>` (SBU_BENCHMARK_DIR=benchmark-verified), concurrently in batches of 3:
- atk_1.py (PREPATCH BUG reproduction): drops the `elif not operand.has_mask` branch so case-3 inputs (self has mask, operand none) fall through to apply_combiner. => NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Prepatch bug reproduced: the spec's case-3 postcondition ToSeq(Result().data)==ToSeq(self_mask) rejects the combiner fall-through (combiner opaque). prepatch_reproduced=true.
- atk_2.py (case 2/3 swap): copies self_mask in case 2 and operand.mask in case 3. => does not verify (exit 2).
- atk_3.py (boundary/partial-domain): case 3 copies operand.mask (the absent array) instead of self_mask. => does not verify (exit 2).
- atk_4.py (control-flow-effect): case 1 (no combiner / no masks) returns MaskResult(True, empty) instead of present=False. => does not verify (exit 2).
- atk_5.py (ungrounded-oracle echo): case 4 (both masks) returns copy_seq(self_mask) instead of apply_combiner — echoes an operand array where the real combiner is required. => does not verify (exit 2). Confirms case-4 is grounded in the consumed combiner axiom, not echoable.
- atk_6.py (combiner arg swap): case 4 calls apply_combiner(operand.mask, self_mask) — opaque combine_masks is not commutative, so postcondition ==combine_masks(self_mask,operand.mask) fails. => does not verify (exit 2).
- atk_7.py (partial-domain): neither-mask + combiner-present routed to apply_combiner instead of MaskResult(False). => does not verify (exit 2).

RESULT: 7/7 same-spec wrong impls REJECTED by the spec; ZERO CANDIDATEs (no impl both shares spec AND verifies). Therefore no faithful refined patch needed materialization/resolve — there is no verify-but-wrong impl to exhibit. run_resolve not applicable (no candidate).

REFINEMENT.MD AUDIT: legs A1-A8 are all R / R+I / A-consumed / I. A7 & section B (combine_masks/apply_combiner) are the only A-legs, both A-consumed (proof uses apply_combiner's Ensures to discharge case-4). refinement.md §C explicitly and correctly states there is NO A-reference and NO kind-3: the changed op (branch guard operand is None -> operand.mask is None) is modelled DIRECTLY as the boolean branch `elif not operand.has_mask` (A6, an R+I step), not hidden behind an axiom. The A-consumed legs' correspondence holds: combine_masks/apply_combiner <-> handle_mask == numpy.bitwise_or (the value the issue/F2P test supply, unchanged by the patch), G-AX-checked by axiom_check.py (shape-preservation + determinism, boundary + 20000 fuzz). The domain exclusion of operand is None (mapping.md §2.1) is sound and matches the gold-patch reachability. Correspondence audit: PASS.

VERDICT: SOUND. The frozen spec is tight enough that every distinct wrong impl (including the prepatch bug and an ungrounded-oracle echo) fails to verify; no verify-not-correct gap exhibited.

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
"""Twin-artifact model for astropy__astropy-14995.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A binary array operation combines two operands and must decide the array of
  per-element flags ("mask") carried by the result. Each operand may carry such
  a flag array or carry none at all. A combiner callable, when supplied, merges
  two present flag arrays element-by-element. The required result is:

    (1) no flags at all when neither operand carries flags, or when no combiner
        was supplied;
    (2) a copy of the *other* operand's flag array when this operand carries no
        flags but the other one does;
    (3) a copy of *this* operand's flag array when this operand carries flags
        and the other operand carries none — the lone present array is
        propagated unchanged, never combined against a missing array;
    (4) the element-wise combination of the two flag arrays (the combiner
        applied to both) when both operands carry them.

  The decision is symmetric in the two operands when only one carries flags:
  whichever operand has a flag array, that array (copied) is the result, and it
  must reach the result intact regardless of which side it came from. In
  particular case (3) is decided by the OTHER operand's flag array being absent,
  independently of any other attribute of that operand.

Flag arrays are modelled as ``List[int]`` (a bitmask of non-negative ints).
"Carries flags" / "carries none" is the boolean ``has_mask``. The decision
returns a small carrier (``MaskResult``) whose ``present`` flag says whether the
result has flags and whose ``data`` holds them when it does — the faithful
``Optional`` "mask or None" return. The element-wise combiner callable is the
UNCHANGED callee that is *invoked* in case (4); it is axiomatized opaquely as
``combine_masks`` (a per-element fold over equal-length arrays preserving the
shape) and its materializing call as ``apply_combiner``. Its soundness against
the real callee is checked by axiom_check.py (G-AX). The decision under
specification is the branch selection (cases 1-3), where the combiner is NOT
called; case (4) merely defers to the unchanged combiner.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class Operand:
    """The second operand: a minimal object carrying only its flag array.
    ``has_mask`` is False when the operand carries no flags; ``mask`` then holds
    no meaningful content (it is never read in that case)."""

    def __init__(self, has_mask: bool, mask: List[int]) -> None:
        Requires(Acc(list_pred(mask), 1 / 2))
        Ensures(Acc(self.has_mask) and self.has_mask == has_mask)  # type: ignore
        Ensures(Acc(self.mask) and self.mask is mask)  # type: ignore
        Ensures(Acc(list_pred(self.mask), 1 / 2))  # type: ignore
        self.has_mask = has_mask
        self.mask = mask


class MaskResult:
    """The decided result mask: ``present`` is False for "no flags" (the
    ``None`` mask); when True, ``data`` holds the flag array."""

    def __init__(self, present: bool, data: List[int]) -> None:
        Requires(Acc(list_pred(data), 1 / 2))
        Ensures(Acc(self.present) and self.present == present)  # type: ignore
        Ensures(Acc(self.data) and self.data is data)  # type: ignore
        Ensures(Acc(list_pred(self.data), 1 / 2))  # type: ignore
        Ensures(ToSeq(self.data) == ToSeq(data))  # type: ignore
        self.present = present
        self.data = data


# axioms-start
@Pure
@ContractOnly
def combine_masks(a: PSeq[int], b: PSeq[int]) -> PSeq[int]:
    """The unchanged element-wise combiner callable, applied to two present
    equal-length flag arrays (case 4 only — it is NEVER invoked when one array
    is absent). The weakest contract the proof needs: the combination has the
    same shape (length) as its inputs. Provenance + executable soundness check:
    mapping.md / axiom_check.py."""
    Ensures(Implies(len(a) == len(b), len(Result()) == len(a)))


@ContractOnly
def apply_combiner(a: List[int], b: List[int]) -> List[int]:
    """Materializing call to the unchanged combiner callable: returns a freshly
    allocated flag array whose content is exactly the abstract combination of
    the two inputs. Same callee as `combine_masks`; this is its impure (list-
    producing) face used inside the implementation. G-AX checks both against the
    real callee."""
    Requires(Acc(list_pred(a), 1 / 2))
    Requires(Acc(list_pred(b), 1 / 2))
    Requires(len(ToSeq(a)) == len(ToSeq(b)))
    Ensures(Acc(list_pred(a), 1 / 2))
    Ensures(Acc(list_pred(b), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == combine_masks(ToSeq(a), ToSeq(b)))
# axioms-end


# pure-start
# (No auxiliary pure spec functions: the combiner is opaque, axiomatized above;
# the branch selection cases 1-3 are stated directly over the flag arrays.)
# pure-end


def result_mask(
    self_has_mask: bool,
    self_mask: List[int],
    operand: Operand,
    handle_mask_present: bool,
) -> MaskResult:
    # pre-conditions-start
    Requires(Acc(list_pred(self_mask), 1 / 2))
    Requires(Acc(operand.has_mask, 1 / 2) and Acc(operand.mask, 1 / 2))
    Requires(Acc(list_pred(operand.mask), 1 / 2))
    # The two operands wrap co-shaped data, so their flag arrays are stored at
    # the same shape (the combiner is defined on equal-length arrays). This
    # holds regardless of which operand currently carries flags.
    Requires(len(ToSeq(self_mask)) == len(ToSeq(operand.mask)))
    # pre-conditions-end
    # post-conditions-start
    # read-only inputs are returned with their permission and value intact.
    Ensures(Acc(list_pred(self_mask), 1 / 2))
    Ensures(Acc(operand.has_mask, 1 / 2) and Acc(operand.mask, 1 / 2))
    Ensures(Acc(list_pred(operand.mask), 1 / 2))
    Ensures(operand.has_mask == Old(operand.has_mask)
            and operand.mask is Old(operand.mask))
    # the result carrier is fully formed.
    Ensures(Acc(Result().present) and Acc(Result().data)
            and Acc(list_pred(Result().data), 1 / 2))

    # (1) no flags when neither operand carries flags, or when no combiner.
    Ensures(Implies(not handle_mask_present, not Result().present))
    Ensures(Implies(handle_mask_present and not self_has_mask
                    and not operand.has_mask,
                    not Result().present))

    # (2) this operand has no flags, the other does: copy the other's array.
    Ensures(Implies(handle_mask_present and not self_has_mask
                    and operand.has_mask,
                    Result().present
                    and ToSeq(Result().data) == ToSeq(operand.mask)))

    # (3) this operand carries flags and the other carries none: the lone
    # present array is copied through unchanged, NOT combined against a missing
    # array. The decision turns on the OTHER operand's flag array being absent.
    Ensures(Implies(handle_mask_present and self_has_mask
                    and not operand.has_mask,
                    Result().present
                    and ToSeq(Result().data) == ToSeq(self_mask)))

    # (4) both operands carry flags: the element-wise combination, i.e. exactly
    # the unchanged combiner applied to both present arrays.
    Ensures(Implies(handle_mask_present and self_has_mask and operand.has_mask,
                    Result().present
                    and ToSeq(Result().data) == combine_masks(ToSeq(self_mask),
                                                              ToSeq(operand.mask))))
    # post-conditions-end
    # impl-start
    empty = []  # type: List[int]
    if (not self_has_mask and not operand.has_mask) or not handle_mask_present:
        return MaskResult(False, empty)
    elif not self_has_mask:
        c = copy_seq(operand.mask)
        return MaskResult(True, c)
    elif not operand.has_mask:
        c = copy_seq(self_mask)
        return MaskResult(True, c)
    else:
        c = apply_combiner(self_mask, operand.mask)
        return MaskResult(True, c)
    # impl-end


def copy_seq(xs: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(xs))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(xs):
        # invariants-start
        Invariant(Acc(list_pred(xs), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(xs))
        Invariant(ToSeq(out) == ToSeq(xs).take(i))
        # invariants-end
        out.append(xs[i])
        Assert(ToSeq(xs).take(i + 1) == ToSeq(xs).take(i) + PSeq(xs[i]))
        i = i + 1
    Assert(ToSeq(xs).take(len(xs)) == ToSeq(xs))
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for astropy__astropy-14995 (nagini).

SPEC SHAPE: result_mask's postconditions pin the FULL output (present flag + ToSeq(data) content) across every one of the 8 boolean combos of (handle_mask_present, self_has_mask, operand.has_mask). Cases 1-3 are stated directly over the flag arrays; case 4 defers to the opaque combine_masks. Because output content is fully constrained in each branch, any impl that decides a branch wrongly, copies the wrong array, mislabels present, or substitutes/echoes an array where the combiner is required cannot discharge the postcondition. This is a TIGHT spec.

POSITIVE CONTROL: copied model.py -> positive_control.py; `bash scripts/nagini_verify.sh positive_control.py` => VERIFIED (16.2s, exit 0).

ATTACKS (all copied from model.py, impl region ONLY edited; axioms/@Pure/Requires/Ensures byte-identical; all confirmed same-spec exit 0 via `adversary same-spec`). Each run via `python -m swebench_unified.adversary weakness nagini astropy__astropy-14995 <file>` (SBU_BENCHMARK_DIR=benchmark-verified), concurrently in batches of 3:
- atk_1.py (PREPATCH BUG reproduction): drops the `elif not operand.has_mask` branch so case-3 inputs (self has mask, operand none) fall through to apply_combiner. => NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Prepatch bug reproduced: the spec's case-3 postcondition ToSeq(Result().data)==ToSeq(self_mask) rejects the combiner fall-through (combiner opaque). prepatch_reproduced=true.
- atk_2.py (case 2/3 swap): copies self_mask in case 2 and operand.mask in case 3. => does not verify (exit 2).
- atk_3.py (boundary/partial-domain): case 3 copies operand.mask (the absent array) instead of self_mask. => does not verify (exit 2).
- atk_4.py (control-flow-effect): case 1 (no combiner / no masks) returns MaskResult(True, empty) instead of present=False. => does not verify (exit 2).
- atk_5.py (ungrounded-oracle echo): case 4 (both masks) returns copy_seq(self_mask) instead of apply_combiner — echoes an operand array where the real combiner is required. => does not verify (exit 2). Confirms case-4 is grounded in the consumed combiner axiom, not echoable.
- atk_6.py (combiner arg swap): case 4 calls apply_combiner(operand.mask, self_mask) — opaque combine_masks is not commutative, so postcondition ==combine_masks(self_mask,operand.mask) fails. => does not verify (exit 2).
- atk_7.py (partial-domain): neither-mask + combiner-present routed to apply_combiner instead of MaskResult(False). => does not verify (exit 2).

RESULT: 7/7 same-spec wrong impls REJECTED by the spec; ZERO CANDIDATEs (no impl both shares spec AND verifies). Therefore no faithful refined patch needed materialization/resolve — there is no verify-but-wrong impl to exhibit. run_resolve not applicable (no candidate).

REFINEMENT.MD AUDIT: legs A1-A8 are all R / R+I / A-consumed / I. A7 & section B (combine_masks/apply_combiner) are the only A-legs, both A-consumed (proof uses apply_combiner's Ensures to discharge case-4). refinement.md §C explicitly and correctly states there is NO A-reference and NO kind-3: the changed op (branch guard operand is None -> operand.mask is None) is modelled DIRECTLY as the boolean branch `elif not operand.has_mask` (A6, an R+I step), not hidden behind an axiom. The A-consumed legs' correspondence holds: combine_masks/apply_combiner <-> handle_mask == numpy.bitwise_or (the value the issue/F2P test supply, unchanged by the patch), G-AX-checked by axiom_check.py (shape-preservation + determinism, boundary + 20000 fuzz). The domain exclusion of operand is None (mapping.md §2.1) is sound and matches the gold-patch reachability. Correspondence audit: PASS.

VERDICT: SOUND. The frozen spec is tight enough that every distinct wrong impl (including the prepatch bug and an ungrounded-oracle echo) fails to verify; no verify-not-correct gap exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness confirmed by two independent checks against the real patched astropy _arithmetic_mask (NDArithmeticMixin, ndarithmetic.py:485) over the full modeled domain.

(1) G-CONF re-run (impl vs real): the contract-stripped impl region (result_mask + copy_seq, apply_combiner realized as the real np.bitwise_or handle_mask) matched the real repo method on 104,080 inputs (80 boundary + 104000 fuzz, seed 14995), 0 disagreements.

(2) Independent SPEC-ORACLE vs real: I derived an oracle DIRECTLY from model.py's Ensures postconditions (not from the impl) — case 1 (not hmp, or neither has mask) -> None; case 2 (only operand has mask) -> copy(operand.mask); case 3 (only self has mask, THE FIX operand.mask is None) -> copy(self.mask); case 4 (both) -> np.bitwise_or — and compared it to the real patched _arithmetic_mask across all 8 (self_has,op_has,hmp) bool combos crossed with boundary + 20000 fuzz mask pairs = 160,072 inputs. Zero divergences.

Spec-region byte-identity was not in question (same-spec framework); this attack targeted spec-vs-repo drift. The spec is neither too strong nor drifted: every postcondition clause holds on the real callee. The `operand is not None` conjuncts dropped from the model are constant-true in the reached domain (justified mapping.md 2.1: scalars are wrapped to flag-less NDData before this path; genuine operand-None collapse case is handled earlier and never calls _arithmetic_mask). The equal-length Requires matches co-shaped operands; the combiner is only consumed via its shape-preservation axiom (G-AX sound against np.bitwise_or). No diverging input exists in the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 leakage/gold-reconstruction review of the solver-visible spec view (spec_view(model.py); mapping.md/refinement.md are audit-only, NOT part of the spec view screened by leak.py). Mechanical G-LEAK screen passes: no diff markers, no gold-patch line reproduced, no patched file/module path, no narration, and no spec-view identifier embedding the patched repo symbol.

Gold edit: `_arithmetic_mask` branch guard `elif operand is None:` -> `elif operand.mask is None:` (the second hunk line is a behavior-free comment typo fix). The distinctive patched symbol is `_arithmetic_mask` (stripped 'arithmetic_mask').

Semantic judgment: the spec view leaks NOTHING beyond the public problem_statement.
- The problem_statement ALREADY states the required behavior verbatim: 'When one of the operand does not have mask, the mask that exists should just be copied over to the output,' and demonstrates all four operand combinations (no-mask x no-mask -> none; mask x no-mask -> should copy, currently fails; mask x mask -> bitwise_or combine). So the four cases in the model docstring (none / copy-other / copy-self / combine) are fully derivable from public text.
- The spec view expresses the fixed guard abstractly as `not operand.has_mask` over a type-refined boolean carrier; it does NOT quote the gold code token `operand.mask is None`, does NOT reproduce the `elif operand is None` bug line, and does NOT localize the edit to a specific branch/line.
- Repo symbols are abstracted: identifiers are `result_mask`, `Operand.has_mask`, `MaskResult`, `combine_masks`, `apply_combiner` — none embeds the patched `_arithmetic_mask`. The patched file path `astropy/nddata/mixins/ndarithmetic.py` does not appear in the spec view.
- No bug/fix/regression narration in any spec-view comment or docstring.

The spec is a legitimate behavioral specification whose content is public via the issue; it does not reconstruct the gold edit. VERDICT: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
