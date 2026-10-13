# P2 adversarial audit — sympy__sympy-24443

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_2_dropneg.py`, `atk_3_skipzero.py`, `atk_4_reverse.py`, `atk_5_droplast.py`, `atk_6_dropfirst.py`, `atk_7_leftmul.py`, `atk_8_negexp.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -98,28 +98,5 @@
     Ensures(Result() == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
     # post-conditions-end
     # impl-start
-    w = gid()
-    i = 0
-    while i < len(block_elems):
-        # invariants-start
-        Invariant(Acc(list_pred(block_elems), 1 / 2))
-        Invariant(Acc(list_pred(block_pows), 1 / 2))
-        Invariant(len(block_elems) == len(block_pows))
-        Invariant(0 <= i and i <= len(block_elems))
-        Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
-        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
-        # `w` is the product of the first `i` blocks; the remaining suffix folds
-        # onto it to give the whole-word image.
-        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
-                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
-        # invariants-end
-        # The fold unfolds at the head of drop(i) (non-empty since i < len):
-        # supply the head/tail split so a single unfold relates step i to i+1.
-        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
-        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
-        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
-        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
-        w = gmul(w, gpow(block_elems[i], block_pows[i]))
-        i = i + 1
-    return w
+    return image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows))
     # impl-end
```

Attack 2 — `atk_2_dropneg.py` → rejected (same spec, does not verify — good)

```diff
@@ -101,25 +101,14 @@
     w = gid()
     i = 0
     while i < len(block_elems):
-        # invariants-start
         Invariant(Acc(list_pred(block_elems), 1 / 2))
         Invariant(Acc(list_pred(block_pows), 1 / 2))
         Invariant(len(block_elems) == len(block_pows))
         Invariant(0 <= i and i <= len(block_elems))
         Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
         Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
-        # `w` is the product of the first `i` blocks; the remaining suffix folds
-        # onto it to give the whole-word image.
-        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
-                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
-        # invariants-end
-        # The fold unfolds at the head of drop(i) (non-empty since i < len):
-        # supply the head/tail split so a single unfold relates step i to i+1.
-        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
-        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
-        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
-        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
-        w = gmul(w, gpow(block_elems[i], block_pows[i]))
+        if block_pows[i] >= 0:
+            w = gmul(w, gpow(block_elems[i], block_pows[i]))
         i = i + 1
     return w
     # impl-end
```

Attack 3 — `atk_3_skipzero.py` → rejected (same spec, does not verify — good)

```diff
@@ -101,25 +101,13 @@
     w = gid()
     i = 0
     while i < len(block_elems):
-        # invariants-start
         Invariant(Acc(list_pred(block_elems), 1 / 2))
         Invariant(Acc(list_pred(block_pows), 1 / 2))
         Invariant(len(block_elems) == len(block_pows))
         Invariant(0 <= i and i <= len(block_elems))
         Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
-        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
-        # `w` is the product of the first `i` blocks; the remaining suffix folds
-        # onto it to give the whole-word image.
-        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
-                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
-        # invariants-end
-        # The fold unfolds at the head of drop(i) (non-empty since i < len):
-        # supply the head/tail split so a single unfold relates step i to i+1.
-        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
-        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
-        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
-        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
-        w = gmul(w, gpow(block_elems[i], block_pows[i]))
+        if block_pows[i] != 0:
+            w = gmul(w, gpow(block_elems[i], block_pows[i]))
         i = i + 1
     return w
     # impl-end
```

Attack 4 — `atk_4_reverse.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,27 +99,14 @@
     # post-conditions-end
     # impl-start
     w = gid()
-    i = 0
-    while i < len(block_elems):
-        # invariants-start
+    i = len(block_elems)
+    while i > 0:
         Invariant(Acc(list_pred(block_elems), 1 / 2))
         Invariant(Acc(list_pred(block_pows), 1 / 2))
         Invariant(len(block_elems) == len(block_pows))
         Invariant(0 <= i and i <= len(block_elems))
         Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
-        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
-        # `w` is the product of the first `i` blocks; the remaining suffix folds
-        # onto it to give the whole-word image.
-        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
-                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
-        # invariants-end
-        # The fold unfolds at the head of drop(i) (non-empty since i < len):
-        # supply the head/tail split so a single unfold relates step i to i+1.
-        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
-        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
-        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
-        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
+        i = i - 1
         w = gmul(w, gpow(block_elems[i], block_pows[i]))
-        i = i + 1
     return w
     # impl-end
```

Attack 5 — `atk_5_droplast.py` → rejected (same spec, does not verify — good)

```diff
@@ -100,25 +100,12 @@
     # impl-start
     w = gid()
     i = 0
-    while i < len(block_elems):
-        # invariants-start
+    while i + 1 < len(block_elems):
         Invariant(Acc(list_pred(block_elems), 1 / 2))
         Invariant(Acc(list_pred(block_pows), 1 / 2))
         Invariant(len(block_elems) == len(block_pows))
         Invariant(0 <= i and i <= len(block_elems))
         Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
-        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
-        # `w` is the product of the first `i` blocks; the remaining suffix folds
-        # onto it to give the whole-word image.
-        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
-                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
-        # invariants-end
-        # The fold unfolds at the head of drop(i) (non-empty since i < len):
-        # supply the head/tail split so a single unfold relates step i to i+1.
-        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
-        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
-        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
-        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
         w = gmul(w, gpow(block_elems[i], block_pows[i]))
         i = i + 1
     return w
```

Attack 6 — `atk_6_dropfirst.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,26 +99,13 @@
     # post-conditions-end
     # impl-start
     w = gid()
-    i = 0
+    i = 1
     while i < len(block_elems):
-        # invariants-start
         Invariant(Acc(list_pred(block_elems), 1 / 2))
         Invariant(Acc(list_pred(block_pows), 1 / 2))
         Invariant(len(block_elems) == len(block_pows))
-        Invariant(0 <= i and i <= len(block_elems))
+        Invariant(0 <= i and i <= len(block_elems) + 1)
         Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
-        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
-        # `w` is the product of the first `i` blocks; the remaining suffix folds
-        # onto it to give the whole-word image.
-        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
-                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
-        # invariants-end
-        # The fold unfolds at the head of drop(i) (non-empty since i < len):
-        # supply the head/tail split so a single unfold relates step i to i+1.
-        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
-        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
-        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
-        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
         w = gmul(w, gpow(block_elems[i], block_pows[i]))
         i = i + 1
     return w
```

Attack 7 — `atk_7_leftmul.py` → rejected (same spec, does not verify — good)

```diff
@@ -101,25 +101,12 @@
     w = gid()
     i = 0
     while i < len(block_elems):
-        # invariants-start
         Invariant(Acc(list_pred(block_elems), 1 / 2))
         Invariant(Acc(list_pred(block_pows), 1 / 2))
         Invariant(len(block_elems) == len(block_pows))
         Invariant(0 <= i and i <= len(block_elems))
         Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
-        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
-        # `w` is the product of the first `i` blocks; the remaining suffix folds
-        # onto it to give the whole-word image.
-        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
-                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
-        # invariants-end
-        # The fold unfolds at the head of drop(i) (non-empty since i < len):
-        # supply the head/tail split so a single unfold relates step i to i+1.
-        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
-        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
-        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
-        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
-        w = gmul(w, gpow(block_elems[i], block_pows[i]))
+        w = gmul(gpow(block_elems[i], block_pows[i]), w)
         i = i + 1
     return w
     # impl-end
```

Attack 8 — `atk_8_negexp.py` → rejected (same spec, does not verify — good)

```diff
@@ -101,25 +101,12 @@
     w = gid()
     i = 0
     while i < len(block_elems):
-        # invariants-start
         Invariant(Acc(list_pred(block_elems), 1 / 2))
         Invariant(Acc(list_pred(block_pows), 1 / 2))
         Invariant(len(block_elems) == len(block_pows))
         Invariant(0 <= i and i <= len(block_elems))
         Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
-        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
-        # `w` is the product of the first `i` blocks; the remaining suffix folds
-        # onto it to give the whole-word image.
-        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
-                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
-        # invariants-end
-        # The fold unfolds at the head of drop(i) (non-empty since i < len):
-        # supply the head/tail split so a single unfold relates step i to i+1.
-        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
-        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
-        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
-        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
-        w = gmul(w, gpow(block_elems[i], block_pows[i]))
+        w = gmul(w, gpow(block_elems[i], -block_pows[i]))
         i = i + 1
     return w
     # impl-end
```

Attack 9 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -119,7 +119,8 @@
         Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
         Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
         Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
-        w = gmul(w, gpow(block_elems[i], block_pows[i]))
+        if block_pows[i] >= 0:
+            w = gmul(w, gpow(block_elems[i], block_pows[i]))
         i = i + 1
     return w
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-24443.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relator word is a finite ordered sequence of blocks; each block is a
  (generator, exponent) pair, and the exponent may be negative (an inverted
  generator). A given assignment maps each generator to a group element of the
  codomain; resolving every block through that assignment yields, for each
  block, the codomain element assigned to its generator together with the
  block's exponent. The IMAGE of the relator word under the assignment is the
  ordered product, taken left to right over the blocks, of the assigned element
  raised to the block's exponent:

        image  =  (g0 ^ e0) * (g1 ^ e1) * ... * (g_{n-1} ^ e_{n-1})

  EVERY block contributes its factor, regardless of the sign of its exponent:
  a block with a negative exponent contributes `g ^ e` (the inverse power) in
  exactly its position, just like a positive one. No block may be silently
  skipped or have its factor replaced by the group identity. The empty word
  maps to the identity. The product is taken in word order; the group operation
  is associative with identity but is NOT assumed commutative, so the order and
  multiplicity of factors is observable.

Group elements of the codomain are modelled as opaque handles (`int` tags) and
the two unchanged group operations the image computation CALLS -- the group
product `gmul` and the integer power `gpow` -- are axiomatized as opaque,
non-commutative monoid operations (A-consumed; provenance + soundness in
mapping.md / axiom_check.py). The relator's blocks are modelled as two parallel
`List[int]`: `block_elems[k]` is the codomain element assigned to block k's
generator (the resolved per-block image) and `block_pows[k]` its exponent. The
image is the front-recursive accumulator fold `image_fold`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def gid() -> int:
    """The codomain group identity element (opaque handle). Unchanged callee."""
    Ensures(True)


@Pure
@ContractOnly
def gmul(a: int, b: int) -> int:
    """The codomain group product a*b (opaque, NOT assumed commutative). The
    unchanged group multiplication the image computation calls. Provenance +
    executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def gpow(g: int, e: int) -> int:
    """The codomain integer power g**e of a group element (opaque). Defined for
    every integer exponent e, positive, zero, or NEGATIVE (the inverse power).
    The unchanged power callee the image computation invokes per block.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def image_fold(acc: int, elems: PSeq[int], pows: PSeq[int]) -> int:
    """Left-to-right product of the per-block factors onto the running product
    `acc`: block 0's factor is `gpow(elems[0], pows[0])`, multiplied on the
    right of `acc`, then recurse over the tail. Front-recursive over the head so
    a single unfold is available per loop step. The empty word leaves `acc`."""
    Requires(len(elems) == len(pows))
    if len(elems) == 0:
        return acc
    return image_fold(gmul(acc, gpow(elems[0], pows[0])),
                      elems.drop(1), pows.drop(1))
# pure-end


def relator_image(block_elems: List[int], block_pows: List[int]) -> int:
    # pre-conditions-start
    # The relator's blocks (resolved element + exponent) are read-only.
    Requires(Acc(list_pred(block_elems), 1 / 2))
    Requires(Acc(list_pred(block_pows), 1 / 2))
    # The two parallel block arrays have equal length (one exponent per block).
    Requires(len(block_elems) == len(block_pows))
    Requires(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(block_elems), 1 / 2))
    Ensures(Acc(list_pred(block_pows), 1 / 2))
    Ensures(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
    # The image is the ordered left-to-right product of every block's factor
    # onto the identity -- every block, including negative-exponent ones,
    # contributes `gpow(elem, exponent)` in its position.
    Ensures(Result() == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
    # post-conditions-end
    # impl-start
    w = gid()
    i = 0
    while i < len(block_elems):
        # invariants-start
        Invariant(Acc(list_pred(block_elems), 1 / 2))
        Invariant(Acc(list_pred(block_pows), 1 / 2))
        Invariant(len(block_elems) == len(block_pows))
        Invariant(0 <= i and i <= len(block_elems))
        Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
        # `w` is the product of the first `i` blocks; the remaining suffix folds
        # onto it to give the whole-word image.
        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
        # invariants-end
        # The fold unfolds at the head of drop(i) (non-empty since i < len):
        # supply the head/tail split so a single unfold relates step i to i+1.
        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
        w = gmul(w, gpow(block_elems[i], block_pows[i]))
        i = i + 1
    return w
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-24443 (nagini). SBU_BENCHMARK_DIR=benchmark-verified, PY=python.

KEY OBSERVATION: the postcondition is a FULLY FUNCTIONAL pin: Ensures(Result() == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows))). Any impl that verifies MUST return exactly the ordered left-to-right per-block product image_fold(gid(), full_seqs) = the gold _image(r). Verify therefore admits only behaviorally-correct impls.

ATTACKS (all same-spec exit 0; spec/axioms/@Pure/Requires/Ensures byte-identical, only impl region edited). Command per attack: `python -m swebench_unified.adversary weakness nagini sympy__sympy-24443 <path>`.
- atk_1_echo.py: ungrounded-oracle ECHO, `return image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows))`. weakness EXIT=0 => CANDIDATE (shares spec AND verifies). But it is behaviorally the exact gold per-block product => its faithful refined patch IS the gold patch.
- atk_2_dropneg.py: prepatch bug reproduction — skips factor when block_pows[i] < 0 (drops inverted-generator factor). weakness EXIT=2 (does NOT verify) — spec rejects it via the loop invariant image_fold(w,drop(i),..)==image_fold(gid(),..). PREPATCH REPRODUCED.
- atk_3_skipzero.py: control-flow-effect — skips factor when exponent==0 (gpow(g,0) is opaque, != gid()). EXIT=2 rejected.
- atk_4_reverse.py: right-to-left product (non-commutative gmul => wrong). EXIT=2 rejected.
- atk_5_droplast.py: boundary — drops last block (i+1<len). EXIT=2 rejected.
- atk_6_dropfirst.py: partial-domain — starts i=1, drops first block. EXIT=2 rejected.
- atk_7_leftmul.py: control-flow-effect — accumulates gmul(factor, w) (left-multiply, reversed). EXIT=2 rejected.
- atk_8_negexp.py: boundary — uses gpow(elem, -pow) (negated exponents). EXIT=2 rejected.
- atk_prepatch.py: the bundle's model_prepatch.py verbatim. EXIT=2 rejected.

Parallelism: weakness runs launched as background jobs, <=3 JVM/Z3 at a time (3 batches). All logs in scratch dir (*.weakness.log).

VERIFYING CANDIDATES: only pos_control.py (exact gold impl region) and atk_1_echo.py (returns the spec expression verbatim). BOTH are behaviorally the gold _image. Materialized faithful patch for the verifying candidate = the gold patch (verbatim; base_commit 809c53c0). run_resolve executed: `run_resolve('sympy__sympy-24443', gold_patch)` -> RESOLVED=True, COMPLETED=True, note='resolved' (docker oracle OK, swe_bench_verified). No verifying-but-wrong impl exists, so no non-resolving faithful patch exists. verify => correct holds.

REFINEMENT.MD LEG AUDIT: every leg is R / A-consumed / A-reference / I — no kind-3. A1/A2=R (array_form (symbol,power) blocks <-> block_pows/block_elems; total symbol->generator->image lookup modeled as opaque handle). A3/A5/A6=A-consumed (gid/gmul/gpow, UNCHANGED codomain monoid ops: codomain.identity, elt __mul__, elt __pow__ total over negative exponents; weakest Ensures(True); correspondence in meta.axioms + mapping.md sec 3.1). A4=A-reference (image_fold deep model of the CHANGED enumeration _image; NOT a consumed value-axiom; validated == real _image by axiom_check.py/G-AX over 23 relators/9 group cases incl. inverted generators). A7=I. Matches meta.json deep_model_references (kind='A-reference') and modeled_functions. The changed op (block enumeration+product) is modeled deeply, not hidden behind a function-under-change axiom.

VERDICT: SOUND. 9 distinct wrong impls (incl. prepatch) all rejected by the spec; the functional postcondition admits only the correct per-block product; the sole verifying candidates' faithful patch resolves under the official harness. verify does NOT admit an incorrect impl for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_2_dropneg.py`, `atk_3_skipzero.py`, `atk_4_reverse.py`, `atk_5_droplast.py`, `atk_6_dropfirst.py`, `atk_7_leftmul.py`, `atk_8_negexp.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2_dropneg.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_skipzero.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_reverse.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_droplast.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_dropfirst.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_leftmul.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_negexp.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sympy__sympy-24443.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relator word is a finite ordered sequence of blocks; each block is a
  (generator, exponent) pair, and the exponent may be negative (an inverted
  generator). A given assignment maps each generator to a group element of the
  codomain; resolving every block through that assignment yields, for each
  block, the codomain element assigned to its generator together with the
  block's exponent. The IMAGE of the relator word under the assignment is the
  ordered product, taken left to right over the blocks, of the assigned element
  raised to the block's exponent:

        image  =  (g0 ^ e0) * (g1 ^ e1) * ... * (g_{n-1} ^ e_{n-1})

  EVERY block contributes its factor, regardless of the sign of its exponent:
  a block with a negative exponent contributes `g ^ e` (the inverse power) in
  exactly its position, just like a positive one. No block may be silently
  skipped or have its factor replaced by the group identity. The empty word
  maps to the identity. The product is taken in word order; the group operation
  is associative with identity but is NOT assumed commutative, so the order and
  multiplicity of factors is observable.

Group elements of the codomain are modelled as opaque handles (`int` tags) and
the two unchanged group operations the image computation CALLS -- the group
product `gmul` and the integer power `gpow` -- are axiomatized as opaque,
non-commutative monoid operations (A-consumed; provenance + soundness in
mapping.md / axiom_check.py). The relator's blocks are modelled as two parallel
`List[int]`: `block_elems[k]` is the codomain element assigned to block k's
generator (the resolved per-block image) and `block_pows[k]` its exponent. The
image is the front-recursive accumulator fold `image_fold`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def gid() -> int:
    """The codomain group identity element (opaque handle). Unchanged callee."""
    Ensures(True)


@Pure
@ContractOnly
def gmul(a: int, b: int) -> int:
    """The codomain group product a*b (opaque, NOT assumed commutative). The
    unchanged group multiplication the image computation calls. Provenance +
    executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def gpow(g: int, e: int) -> int:
    """The codomain integer power g**e of a group element (opaque). Defined for
    every integer exponent e, positive, zero, or NEGATIVE (the inverse power).
    The unchanged power callee the image computation invokes per block.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def image_fold(acc: int, elems: PSeq[int], pows: PSeq[int]) -> int:
    """Left-to-right product of the per-block factors onto the running product
    `acc`: block 0's factor is `gpow(elems[0], pows[0])`, multiplied on the
    right of `acc`, then recurse over the tail. Front-recursive over the head so
    a single unfold is available per loop step. The empty word leaves `acc`."""
    Requires(len(elems) == len(pows))
    if len(elems) == 0:
        return acc
    return image_fold(gmul(acc, gpow(elems[0], pows[0])),
                      elems.drop(1), pows.drop(1))
# pure-end


def relator_image(block_elems: List[int], block_pows: List[int]) -> int:
    # pre-conditions-start
    # The relator's blocks (resolved element + exponent) are read-only.
    Requires(Acc(list_pred(block_elems), 1 / 2))
    Requires(Acc(list_pred(block_pows), 1 / 2))
    # The two parallel block arrays have equal length (one exponent per block).
    Requires(len(block_elems) == len(block_pows))
    Requires(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(block_elems), 1 / 2))
    Ensures(Acc(list_pred(block_pows), 1 / 2))
    Ensures(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
    # The image is the ordered left-to-right product of every block's factor
    # onto the identity -- every block, including negative-exponent ones,
    # contributes `gpow(elem, exponent)` in its position.
    Ensures(Result() == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
    # post-conditions-end
    # impl-start
    w = gid()
    i = 0
    while i < len(block_elems):
        # invariants-start
        Invariant(Acc(list_pred(block_elems), 1 / 2))
        Invariant(Acc(list_pred(block_pows), 1 / 2))
        Invariant(len(block_elems) == len(block_pows))
        Invariant(0 <= i and i <= len(block_elems))
        Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
        # `w` is the product of the first `i` blocks; the remaining suffix folds
        # onto it to give the whole-word image.
        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
        # invariants-end
        # The fold unfolds at the head of drop(i) (non-empty since i < len):
        # supply the head/tail split so a single unfold relates step i to i+1.
        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
        w = gmul(w, gpow(block_elems[i], block_pows[i]))
        i = i + 1
    return w
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sympy__sympy-24443 (nagini). SBU_BENCHMARK_DIR=benchmark-verified, PY=python.

KEY OBSERVATION: the postcondition is a FULLY FUNCTIONAL pin: Ensures(Result() == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows))). Any impl that verifies MUST return exactly the ordered left-to-right per-block product image_fold(gid(), full_seqs) = the gold _image(r). Verify therefore admits only behaviorally-correct impls.

ATTACKS (all same-spec exit 0; spec/axioms/@Pure/Requires/Ensures byte-identical, only impl region edited). Command per attack: `python -m swebench_unified.adversary weakness nagini sympy__sympy-24443 <path>`.
- atk_1_echo.py: ungrounded-oracle ECHO, `return image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows))`. weakness EXIT=0 => CANDIDATE (shares spec AND verifies). But it is behaviorally the exact gold per-block product => its faithful refined patch IS the gold patch.
- atk_2_dropneg.py: prepatch bug reproduction — skips factor when block_pows[i] < 0 (drops inverted-generator factor). weakness EXIT=2 (does NOT verify) — spec rejects it via the loop invariant image_fold(w,drop(i),..)==image_fold(gid(),..). PREPATCH REPRODUCED.
- atk_3_skipzero.py: control-flow-effect — skips factor when exponent==0 (gpow(g,0) is opaque, != gid()). EXIT=2 rejected.
- atk_4_reverse.py: right-to-left product (non-commutative gmul => wrong). EXIT=2 rejected.
- atk_5_droplast.py: boundary — drops last block (i+1<len). EXIT=2 rejected.
- atk_6_dropfirst.py: partial-domain — starts i=1, drops first block. EXIT=2 rejected.
- atk_7_leftmul.py: control-flow-effect — accumulates gmul(factor, w) (left-multiply, reversed). EXIT=2 rejected.
- atk_8_negexp.py: boundary — uses gpow(elem, -pow) (negated exponents). EXIT=2 rejected.
- atk_prepatch.py: the bundle's model_prepatch.py verbatim. EXIT=2 rejected.

Parallelism: weakness runs launched as background jobs, <=3 JVM/Z3 at a time (3 batches). All logs in scratch dir (*.weakness.log).

VERIFYING CANDIDATES: only pos_control.py (exact gold impl region) and atk_1_echo.py (returns the spec expression verbatim). BOTH are behaviorally the gold _image. Materialized faithful patch for the verifying candidate = the gold patch (verbatim; base_commit 809c53c0). run_resolve executed: `run_resolve('sympy__sympy-24443', gold_patch)` -> RESOLVED=True, COMPLETED=True, note='resolved' (docker oracle OK, swe_bench_verified). No verifying-but-wrong impl exists, so no non-resolving faithful patch exists. verify => correct holds.

REFINEMENT.MD LEG AUDIT: every leg is R / A-consumed / A-reference / I — no kind-3. A1/A2=R (array_form (symbol,power) blocks <-> block_pows/block_elems; total symbol->generator->image lookup modeled as opaque handle). A3/A5/A6=A-consumed (gid/gmul/gpow, UNCHANGED codomain monoid ops: codomain.identity, elt __mul__, elt __pow__ total over negative exponents; weakest Ensures(True); correspondence in meta.axioms + mapping.md sec 3.1). A4=A-reference (image_fold deep model of the CHANGED enumeration _image; NOT a consumed value-axiom; validated == real _image by axiom_check.py/G-AX over 23 relators/9 group cases incl. inverted generators). A7=I. Matches meta.json deep_model_references (kind='A-reference') and modeled_functions. The changed op (block enumeration+product) is modeled deeply, not hidden behind a function-under-change axiom.

VERDICT: SOUND. 9 distinct wrong impls (incl. prepatch) all rejected by the spec; the functional postcondition admits only the correct per-block product; the sole verifying candidates' faithful patch resolves under the official harness. verify does NOT admit an incorrect impl for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for the modeled function relator_image vs the real callee _image inside sympy/combinatorics/homomorphisms.py:_check_homomorphism.

SPEC INTEGRITY: `python -m swebench_unified.adversary same-spec nagini sympy__sympy-24443 <copy-of-model>` returns SAME (exit 0). The audited spec region (axioms + pre/post-conditions + pure image_fold) is well-defined and shared.

REAL CALLEE: worktree is at base_commit 809c53c... with the gold patch applied. Post-patch _image(r) = `w = identity; for symbol, power in r.array_form: w *= images[symbols_to_domain_generators[symbol]]**power; return w` — the ordered left-to-right product of every block's factor, negative exponents included. This is exactly what the spec's postcondition Result() == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)) demands.

OPAQUE AXIOMS NOT TOO STRONG: gid/gmul/gpow are @ContractOnly with Ensures(True) — the weakest possible contracts. They assume NO commutativity, no algebraic identity beyond what the fold structure implies, so the spec cannot over-claim relative to the real non-abelian permutation-group operations. gpow is total over all integer exponents (matches FreeGroupElement/Permutation __pow__ handling n<0), so negative-exponent (inverted-generator) blocks are honored — the discriminating case.

### Executable differential evidence
1. Bundle conformance_check.py run against the REAL gold-patched repo: `G-CONF OK ... == real patched verdict on 100026 cases / 231100 relator inputs (seed 24443), 0 disagreements` (exit 0).
2. Independent re-implemented differential probe (20000 random self-map assignments over D3/D5/S4/A5/C7 + an FpGroup->A4 case, negative exponents exercised) comparing the modeled fold to the real _image: 0 divergences.

The modeled function agrees with the real repo callee on every tested input; the spec is the weakest-sufficient one and does not drift. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen) PASSES on the nagini spec view: no diff markers, no gold-patch line reproduced (the abstract math `image = (g0^e0)*(g1^e1)*...` does not echo the gold `w *= images[g]**power`), no patched file path/module, no bug/fix narration, and no spec-view identifier or comment naming a patched repo symbol (only the distinctive changed symbol `homomorphism` is checked, and it does not appear). Spec view identifiers are all model-local (gid/gmul/gpow/image_fold/relator_image/block_elems/block_pows); repo symbols (_image, array_form, images, gens, PermutationGroup) never appear. Semantically, the spec states the desired behavior — every block, including negative-exponent (inverted-generator) ones, contributes its factor g^e in order — but this discriminator is ALREADY PUBLIC in the problem_statement, which explicitly says the bug is in _image on PermutationGroups and that 'When r[i] is an inverted generator, the `in gens` test fails' plus 'the whole thing can be greatly simplified.' The spec merely encodes correct behavior at the same altitude as the public task without revealing the specific code edit. mapping.md/refinement.md do quote gold-hunk code and repo symbols, but those are audit artifacts, not the consumer spec view screened by G-PANEL-3. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
