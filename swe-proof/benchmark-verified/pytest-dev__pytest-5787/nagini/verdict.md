# P2 adversarial audit — pytest-dev__pytest-5787

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
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -64,7 +63,6 @@
     # `chain` is a read-only input (fractional permission): serialization reads
     # the links and emits a fresh transport list; it does not mutate the chain.
     Requires(Acc(list_pred(chain), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(chain) >= 1)
@@ -78,27 +76,9 @@
             [[ToSeq(Result())[k]]])))
     # post-conditions-end
     # impl-start
-    out = []  # type: List[int]
-    i = 0
-    while i < len(chain):
-        # invariants-start
-        Invariant(Acc(list_pred(chain), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(chain))
-        Invariant(len(out) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
-                  [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(chain) - i + 1))
-        # invariants-end
-        old = out  # type: List[int]
-        out = out + [chain[i]]
-        Assert(ToSeq(out) == ToSeq(old) + PSeq(chain[i]))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
-               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
-        Assert(ToSeq(out)[i] == chain[i])
-        i = i + 1
-    return out
+        out = []  # type: List[int]
+        out = out + [chain[len(chain) - 1]]
+        return out
     # impl-end
 
 
@@ -107,7 +87,6 @@
     # `transport` is a read-only input (fractional permission): reconstruction
     # reads the transport links and emits a fresh chain; it does not mutate it.
     Requires(Acc(list_pred(transport), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(transport) >= 1)
@@ -132,7 +111,6 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   ToSeq(out)[k] == copy_link(ToSeq(transport)[k])),
                   [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(transport) - i + 1))
         # invariants-end
         old = out  # type: List[int]
         out = out + [transport[i]]
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -64,7 +63,6 @@
     # `chain` is a read-only input (fractional permission): serialization reads
     # the links and emits a fresh transport list; it does not mutate the chain.
     Requires(Acc(list_pred(chain), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(chain) >= 1)
@@ -78,27 +76,15 @@
             [[ToSeq(Result())[k]]])))
     # post-conditions-end
     # impl-start
-    out = []  # type: List[int]
-    i = 0
-    while i < len(chain):
-        # invariants-start
-        Invariant(Acc(list_pred(chain), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(chain))
-        Invariant(len(out) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
-                  [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(chain) - i + 1))
-        # invariants-end
-        old = out  # type: List[int]
-        out = out + [chain[i]]
-        Assert(ToSeq(out) == ToSeq(old) + PSeq(chain[i]))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
-               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
-        Assert(ToSeq(out)[i] == chain[i])
-        i = i + 1
-    return out
+        out = []  # type: List[int]
+        i = len(chain) - 1
+        while i >= 0:
+            Invariant(Acc(list_pred(chain), 1 / 2))
+            Invariant(Acc(list_pred(out)))
+            Invariant(-1 <= i and i < len(chain))
+            out = out + [chain[i]]
+            i = i - 1
+        return out
     # impl-end
 
 
@@ -107,7 +93,6 @@
     # `transport` is a read-only input (fractional permission): reconstruction
     # reads the transport links and emits a fresh chain; it does not mutate it.
     Requires(Acc(list_pred(transport), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(transport) >= 1)
@@ -132,7 +117,6 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   ToSeq(out)[k] == copy_link(ToSeq(transport)[k])),
                   [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(transport) - i + 1))
         # invariants-end
         old = out  # type: List[int]
         out = out + [transport[i]]
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -64,7 +63,6 @@
     # `chain` is a read-only input (fractional permission): serialization reads
     # the links and emits a fresh transport list; it does not mutate the chain.
     Requires(Acc(list_pred(chain), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(chain) >= 1)
@@ -78,27 +76,19 @@
             [[ToSeq(Result())[k]]])))
     # post-conditions-end
     # impl-start
-    out = []  # type: List[int]
-    i = 0
-    while i < len(chain):
-        # invariants-start
-        Invariant(Acc(list_pred(chain), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(chain))
-        Invariant(len(out) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
-                  [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(chain) - i + 1))
-        # invariants-end
-        old = out  # type: List[int]
-        out = out + [chain[i]]
-        Assert(ToSeq(out) == ToSeq(old) + PSeq(chain[i]))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
-               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
-        Assert(ToSeq(out)[i] == chain[i])
-        i = i + 1
-    return out
+        out = []  # type: List[int]
+        i = 0
+        while i < len(chain) - 1:
+            Invariant(Acc(list_pred(chain), 1 / 2))
+            Invariant(Acc(list_pred(out)))
+            Invariant(0 <= i and i <= len(chain))
+            Invariant(len(out) == i)
+            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
+                      ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
+                      [[ToSeq(out)[k]]])))
+            out = out + [chain[i]]
+            i = i + 1
+        return out
     # impl-end
 
 
@@ -107,7 +97,6 @@
     # `transport` is a read-only input (fractional permission): reconstruction
     # reads the transport links and emits a fresh chain; it does not mutate it.
     Requires(Acc(list_pred(transport), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(transport) >= 1)
@@ -132,7 +121,6 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   ToSeq(out)[k] == copy_link(ToSeq(transport)[k])),
                   [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(transport) - i + 1))
         # invariants-end
         old = out  # type: List[int]
         out = out + [transport[i]]
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -64,7 +63,6 @@
     # `chain` is a read-only input (fractional permission): serialization reads
     # the links and emits a fresh transport list; it does not mutate the chain.
     Requires(Acc(list_pred(chain), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(chain) >= 1)
@@ -78,27 +76,16 @@
             [[ToSeq(Result())[k]]])))
     # post-conditions-end
     # impl-start
-    out = []  # type: List[int]
-    i = 0
-    while i < len(chain):
-        # invariants-start
-        Invariant(Acc(list_pred(chain), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(chain))
-        Invariant(len(out) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
-                  [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(chain) - i + 1))
-        # invariants-end
-        old = out  # type: List[int]
-        out = out + [chain[i]]
-        Assert(ToSeq(out) == ToSeq(old) + PSeq(chain[i]))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
-               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
-        Assert(ToSeq(out)[i] == chain[i])
-        i = i + 1
-    return out
+        out = []  # type: List[int]
+        i = 0
+        while i < len(chain):
+            Invariant(Acc(list_pred(chain), 1 / 2))
+            Invariant(Acc(list_pred(out)))
+            Invariant(0 <= i and i <= len(chain))
+            Invariant(len(out) == i)
+            out = out + [chain[i] + 1]
+            i = i + 1
+        return out
     # impl-end
 
 
@@ -107,7 +94,6 @@
     # `transport` is a read-only input (fractional permission): reconstruction
     # reads the transport links and emits a fresh chain; it does not mutate it.
     Requires(Acc(list_pred(transport), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(transport) >= 1)
@@ -132,7 +118,6 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   ToSeq(out)[k] == copy_link(ToSeq(transport)[k])),
                   [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(transport) - i + 1))
         # invariants-end
         old = out  # type: List[int]
         out = out + [transport[i]]
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -64,7 +63,6 @@
     # `chain` is a read-only input (fractional permission): serialization reads
     # the links and emits a fresh transport list; it does not mutate the chain.
     Requires(Acc(list_pred(chain), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(chain) >= 1)
@@ -89,7 +87,6 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
                   [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(chain) - i + 1))
         # invariants-end
         old = out  # type: List[int]
         out = out + [chain[i]]
@@ -107,7 +104,6 @@
     # `transport` is a read-only input (fractional permission): reconstruction
     # reads the transport links and emits a fresh chain; it does not mutate it.
     Requires(Acc(list_pred(transport), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(transport) >= 1)
@@ -121,25 +117,7 @@
             [[ToSeq(Result())[k]]])))
     # post-conditions-end
     # impl-start
-    out = []  # type: List[int]
-    i = 0
-    while i < len(transport):
-        # invariants-start
-        Invariant(Acc(list_pred(transport), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(transport))
-        Invariant(len(out) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                  ToSeq(out)[k] == copy_link(ToSeq(transport)[k])),
-                  [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(transport) - i + 1))
-        # invariants-end
-        old = out  # type: List[int]
-        out = out + [transport[i]]
-        Assert(ToSeq(out) == ToSeq(old) + PSeq(transport[i]))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
-               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
-        Assert(ToSeq(out)[i] == transport[i])
-        i = i + 1
-    return out
+        out = []  # type: List[int]
+        out = out + [transport[len(transport) - 1]]
+        return out
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -64,7 +63,6 @@
     # `chain` is a read-only input (fractional permission): serialization reads
     # the links and emits a fresh transport list; it does not mutate the chain.
     Requires(Acc(list_pred(chain), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(chain) >= 1)
@@ -78,27 +76,15 @@
             [[ToSeq(Result())[k]]])))
     # post-conditions-end
     # impl-start
-    out = []  # type: List[int]
-    i = 0
-    while i < len(chain):
-        # invariants-start
-        Invariant(Acc(list_pred(chain), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(chain))
-        Invariant(len(out) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
-                  [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(chain) - i + 1))
-        # invariants-end
-        old = out  # type: List[int]
-        out = out + [chain[i]]
-        Assert(ToSeq(out) == ToSeq(old) + PSeq(chain[i]))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
-               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
-        Assert(ToSeq(out)[i] == chain[i])
-        i = i + 1
-    return out
+        out = []  # type: List[int]
+        i = 0
+        while i < len(chain):
+            Invariant(Acc(list_pred(chain), 1 / 2))
+            Invariant(Acc(list_pred(out)))
+            Invariant(0 <= i and i <= len(chain))
+            out = out + [chain[i]] + [chain[i]]
+            i = i + 1
+        return out
     # impl-end
 
 
@@ -107,7 +93,6 @@
     # `transport` is a read-only input (fractional permission): reconstruction
     # reads the transport links and emits a fresh chain; it does not mutate it.
     Requires(Acc(list_pred(transport), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(transport) >= 1)
@@ -132,7 +117,6 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   ToSeq(out)[k] == copy_link(ToSeq(transport)[k])),
                   [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(transport) - i + 1))
         # invariants-end
         old = out  # type: List[int]
         out = out + [transport[i]]
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -64,7 +63,6 @@
     # `chain` is a read-only input (fractional permission): serialization reads
     # the links and emits a fresh transport list; it does not mutate the chain.
     Requires(Acc(list_pred(chain), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(chain) >= 1)
@@ -78,27 +76,12 @@
             [[ToSeq(Result())[k]]])))
     # post-conditions-end
     # impl-start
-    out = []  # type: List[int]
-    i = 0
-    while i < len(chain):
-        # invariants-start
-        Invariant(Acc(list_pred(chain), 1 / 2))
-        Invariant(Acc(list_pred(out)))
-        Invariant(0 <= i and i <= len(chain))
-        Invariant(len(out) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
-                  [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(chain) - i + 1))
-        # invariants-end
-        old = out  # type: List[int]
-        out = out + [chain[i]]
-        Assert(ToSeq(out) == ToSeq(old) + PSeq(chain[i]))
-        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
-               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
-        Assert(ToSeq(out)[i] == chain[i])
-        i = i + 1
-    return out
+        out = []  # type: List[int]
+        if len(chain) == 1:
+            out = out + [chain[0]]
+            return out
+        out = out + [chain[0]]
+        return out
     # impl-end
 
 
@@ -107,7 +90,6 @@
     # `transport` is a read-only input (fractional permission): reconstruction
     # reads the transport links and emits a fresh chain; it does not mutate it.
     Requires(Acc(list_pred(transport), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Requires(len(transport) >= 1)
@@ -132,7 +114,6 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   ToSeq(out)[k] == copy_link(ToSeq(transport)[k])),
                   [[ToSeq(out)[k]]])))
-        Invariant(MustTerminate(len(transport) - i + 1))
         # invariants-end
         old = out  # type: List[int]
         out = out + [transport[i]]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-5787.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A failure representation that is sent across a process boundary is reduced to
  a transport form built only from primitive entries (the "serialize" step) and
  later reconstructed from that transport form (the "deserialize" step). Such a
  representation is a CHAIN of one or more links; each link records a distinct
  stage of the failure (an originating cause, then the intermediate stages, and
  finally the outermost failure that surfaced), in that order. A single,
  unchained failure is just the degenerate chain of length one.

  The required guarantee is that the transport form preserves the WHOLE chain,
  not only its outermost link, and that reconstruction is its exact inverse:

    (1) serialize(chain) carries every link, in order — its length and each
        link are those of the input chain (no link is dropped, none reordered);
    (2) deserialize(transport) reproduces every link of the transport form, in
        order — so deserialize(serialize(chain)) == chain for chains of ANY
        length, in particular length >= 2 (a genuinely multi-stage failure),
        not merely length one.

  Each link is an opaque token here; what is under specification is that the
  COUNT and ORDER of links survive the round trip — a chain of several stages
  must not collapse to a single stage.

Each link is modelled as an `int` token and a chain as a `List[int]` of those
tokens (Nagini bans `str` indexing, and the per-link content is an unchanged
structural copy, irrelevant to the count/order property under test). The pure
sequence theory `PSeq[int]` carries the specification. The per-link structural
copy that both steps perform on a link's contents is the unchanged behaviour,
modelled deeply as the identity on the token and validated == the real per-link
(de)serializer out-of-band by axiom_check.py (G-AX); it is not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom. The per-link structural copy each step
# applies to one link's contents is the unchanged callee behaviour; it is
# modelled DEEPLY as the identity on the link token (`copy_link` below) and
# validated == the real per-link (de)serializer by axiom_check.py / G-AX as an
# A-reference. The proof never depends on a @ContractOnly contract.)
# axioms-end


# pure-start
@Pure
def copy_link(link: int) -> int:
    """The structural copy applied to a single link's contents. It is the
    unchanged behaviour and is content-preserving: the round trip on one link
    is the identity on its token."""
    return link
# pure-end


def serialize_chain(chain: List[int]) -> List[int]:
    # pre-conditions-start
    # `chain` is a read-only input (fractional permission): serialization reads
    # the links and emits a fresh transport list; it does not mutate the chain.
    Requires(Acc(list_pred(chain), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Requires(len(chain) >= 1)
    Ensures(Acc(list_pred(chain), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The transport form carries the WHOLE chain, in order: same length and
    # every link preserved (each via the content-preserving structural copy).
    Ensures(len(Result()) == len(chain))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(chain),
            ToSeq(Result())[k] == copy_link(ToSeq(chain)[k])),
            [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(chain):
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(chain))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
                  [[ToSeq(out)[k]]])))
        # invariants-end
        old = out  # type: List[int]
        out = out + [chain[i]]
        Assert(ToSeq(out) == ToSeq(old) + PSeq(chain[i]))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == chain[i])
        i = i + 1
    return out
    # impl-end


def deserialize_chain(transport: List[int]) -> List[int]:
    # pre-conditions-start
    # `transport` is a read-only input (fractional permission): reconstruction
    # reads the transport links and emits a fresh chain; it does not mutate it.
    Requires(Acc(list_pred(transport), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Requires(len(transport) >= 1)
    Ensures(Acc(list_pred(transport), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Reconstruction reproduces EVERY transport link, in order: same length and
    # every link preserved (each via the content-preserving structural copy).
    Ensures(len(Result()) == len(transport))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(transport),
            ToSeq(Result())[k] == copy_link(ToSeq(transport)[k])),
            [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(transport):
        # invariants-start
        Invariant(Acc(list_pred(transport), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(transport))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  ToSeq(out)[k] == copy_link(ToSeq(transport)[k])),
                  [[ToSeq(out)[k]]])))
        # invariants-end
        old = out  # type: List[int]
        out = out + [transport[i]]
        Assert(ToSeq(out) == ToSeq(old) + PSeq(transport[i]))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == transport[i])
        i = i + 1
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT-FIDELITY (G-EQ) adversarial audit of pytest-dev__pytest-5787 nagini bundle.

SPEC ANALYSIS: The frozen spec fully PINS each function's output. For both serialize_chain and deserialize_chain the postconditions are: len(Result())==len(input) AND Forall k in [0,len): Result()[k]==copy_link(input[k]), where copy_link is the DEEP identity model (@Pure returns link). Conjoined, these force any VERIFYING impl to return a list element-wise equal to its input (the identity), which is exactly gold behaviour up to R (link-tuple<->int token) and the A-reference copy_link. Hence verify=>correct is expected to hold; a rubber-stamp would be unjustified without falsification, so 7 distinct wrong impls + both prepatch bugs were machine-checked.

SAME-SPEC: all 7 attacks + positive_control pass `adversary same-spec nagini` (exit 0, byte-identical spec_signature). spec_view elides only impl-start..impl-end (invariants included), so only impl regions differ; axioms/@Pure/Requires/Ensures byte-identical.

POSITIVE CONTROL: positive_control.py == model.py; `bash scripts/nagini_verify.sh` -> exit 0 (Verification successful, 12.7s). Toolchain confirmed live (FSx HOME, swebench-nagini-verifier env).

ATTACKS (each: cp model.py, edit ONLY one impl region; run `adversary weakness nagini pytest-dev__pytest-5787 <path>`, run concurrently in batches of <=3 JVM+Z3 jobs):
- atk_1.py (prepatch site A / boundary): serialize emits only chain[len-1] (outermost link, collapse). weakness EXIT=2 NOT-A-COUNTEREXAMPLE (verification failed) — fails len(Result())==len(chain) for len>=2. PREPATCH BUG A reproduced.
- atk_2.py (order/control-flow): serialize reverses link order. EXIT=2, verification failed (fails per-index Forall).
- atk_3.py (boundary/partial-domain): serialize loops to len-1, drops last link. EXIT=2, verification failed (len mismatch).
- atk_4.py (content corruption / ungrounded-oracle echo): serialize emits chain[i]+1. EXIT=2, verification failed (per-index copy_link identity violated).
- atk_5.py (prepatch site B / boundary): deserialize rebuilds only transport[len-1] (single-link collapse). EXIT=2 NOT-A-COUNTEREXAMPLE (verification failed). PREPATCH BUG B reproduced.
- atk_6.py (count/duplication): serialize emits each link twice (2x length). EXIT=2, verification failed (len mismatch).
- atk_7.py (partial-domain control-flow-effect): serialize correct only path emits chain[0] always (single link, ignoring len). EXIT=2, verification failed.
No attack returned CANDIDATE (exit 0). Therefore NO faithful refined patch needed materialization/resolve; the resolve-obligation is vacuously satisfied (nothing verified-yet-wrong to run).

REFINEMENT.MD AUDIT: Legs are R / A-reference / I only; no consumed @ContractOnly axiom (D. no kind-3 confirmed — the two genuinely-changed ops serialize/deserialize are modeled DEEPLY as verified per-link loops, not hidden behind a change-op axiom). A-reference correspondence verified against patch.diff (gold, src/_pytest/reports.py two-site change): serialize_longrepr iterates rep.longrepr.chain emitting (serialize_repr_traceback, serialize_repr_crash, description) per link (A2, every link/order) <-> model loop out=out+[chain[i]]; _report_kwargs_from_json iterates reportdict['longrepr']['chain'] rebuilding each link then ExceptionChainRepr(chain) (B2) <-> model loop out=out+[transport[i]]; per-link __dict__.copy()/re-__init__ content-preserving (A3/B3) <-> copy_link identity, validated ==real callee by axiom_check.py/G-AX (A-reference, not consumed). mapping.md R-refinements (link tuple<->int token, list order<->list order, len<->len, ReprExceptionInfo<->length-1 chain) are faithful.

VERDICT: SOUND. >=5 (7) distinct same-spec wrong impls machine-checked, none verifies; positive control verifies; both prepatch bugs reproduce; spec pins output to the gold identity => verify=>correct. No verifying-wrong-impl exists to break resolve.

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
"""Twin-artifact model for pytest-dev__pytest-5787.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A failure representation that is sent across a process boundary is reduced to
  a transport form built only from primitive entries (the "serialize" step) and
  later reconstructed from that transport form (the "deserialize" step). Such a
  representation is a CHAIN of one or more links; each link records a distinct
  stage of the failure (an originating cause, then the intermediate stages, and
  finally the outermost failure that surfaced), in that order. A single,
  unchained failure is just the degenerate chain of length one.

  The required guarantee is that the transport form preserves the WHOLE chain,
  not only its outermost link, and that reconstruction is its exact inverse:

    (1) serialize(chain) carries every link, in order — its length and each
        link are those of the input chain (no link is dropped, none reordered);
    (2) deserialize(transport) reproduces every link of the transport form, in
        order — so deserialize(serialize(chain)) == chain for chains of ANY
        length, in particular length >= 2 (a genuinely multi-stage failure),
        not merely length one.

  Each link is an opaque token here; what is under specification is that the
  COUNT and ORDER of links survive the round trip — a chain of several stages
  must not collapse to a single stage.

Each link is modelled as an `int` token and a chain as a `List[int]` of those
tokens (Nagini bans `str` indexing, and the per-link content is an unchanged
structural copy, irrelevant to the count/order property under test). The pure
sequence theory `PSeq[int]` carries the specification. The per-link structural
copy that both steps perform on a link's contents is the unchanged behaviour,
modelled deeply as the identity on the token and validated == the real per-link
(de)serializer out-of-band by axiom_check.py (G-AX); it is not consumed as an
axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom. The per-link structural copy each step
# applies to one link's contents is the unchanged callee behaviour; it is
# modelled DEEPLY as the identity on the link token (`copy_link` below) and
# validated == the real per-link (de)serializer by axiom_check.py / G-AX as an
# A-reference. The proof never depends on a @ContractOnly contract.)
# axioms-end


# pure-start
@Pure
def copy_link(link: int) -> int:
    """The structural copy applied to a single link's contents. It is the
    unchanged behaviour and is content-preserving: the round trip on one link
    is the identity on its token."""
    return link
# pure-end


def serialize_chain(chain: List[int]) -> List[int]:
    # pre-conditions-start
    # `chain` is a read-only input (fractional permission): serialization reads
    # the links and emits a fresh transport list; it does not mutate the chain.
    Requires(Acc(list_pred(chain), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Requires(len(chain) >= 1)
    Ensures(Acc(list_pred(chain), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The transport form carries the WHOLE chain, in order: same length and
    # every link preserved (each via the content-preserving structural copy).
    Ensures(len(Result()) == len(chain))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(chain),
            ToSeq(Result())[k] == copy_link(ToSeq(chain)[k])),
            [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(chain):
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(chain))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
                  [[ToSeq(out)[k]]])))
        # invariants-end
        old = out  # type: List[int]
        out = out + [chain[i]]
        Assert(ToSeq(out) == ToSeq(old) + PSeq(chain[i]))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == chain[i])
        i = i + 1
    return out
    # impl-end


def deserialize_chain(transport: List[int]) -> List[int]:
    # pre-conditions-start
    # `transport` is a read-only input (fractional permission): reconstruction
    # reads the transport links and emits a fresh chain; it does not mutate it.
    Requires(Acc(list_pred(transport), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Requires(len(transport) >= 1)
    Ensures(Acc(list_pred(transport), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Reconstruction reproduces EVERY transport link, in order: same length and
    # every link preserved (each via the content-preserving structural copy).
    Ensures(len(Result()) == len(transport))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(transport),
            ToSeq(Result())[k] == copy_link(ToSeq(transport)[k])),
            [[ToSeq(Result())[k]]])))
    # post-conditions-end
    # impl-start
    out = []  # type: List[int]
    i = 0
    while i < len(transport):
        # invariants-start
        Invariant(Acc(list_pred(transport), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(transport))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  ToSeq(out)[k] == copy_link(ToSeq(transport)[k])),
                  [[ToSeq(out)[k]]])))
        # invariants-end
        old = out  # type: List[int]
        out = out + [transport[i]]
        Assert(ToSeq(out) == ToSeq(old) + PSeq(transport[i]))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == transport[i])
        i = i + 1
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

REFINEMENT-FIDELITY (G-EQ) adversarial audit of pytest-dev__pytest-5787 nagini bundle.

SPEC ANALYSIS: The frozen spec fully PINS each function's output. For both serialize_chain and deserialize_chain the postconditions are: len(Result())==len(input) AND Forall k in [0,len): Result()[k]==copy_link(input[k]), where copy_link is the DEEP identity model (@Pure returns link). Conjoined, these force any VERIFYING impl to return a list element-wise equal to its input (the identity), which is exactly gold behaviour up to R (link-tuple<->int token) and the A-reference copy_link. Hence verify=>correct is expected to hold; a rubber-stamp would be unjustified without falsification, so 7 distinct wrong impls + both prepatch bugs were machine-checked.

SAME-SPEC: all 7 attacks + positive_control pass `adversary same-spec nagini` (exit 0, byte-identical spec_signature). spec_view elides only impl-start..impl-end (invariants included), so only impl regions differ; axioms/@Pure/Requires/Ensures byte-identical.

POSITIVE CONTROL: positive_control.py == model.py; `bash scripts/nagini_verify.sh` -> exit 0 (Verification successful, 12.7s). Toolchain confirmed live (FSx HOME, swebench-nagini-verifier env).

ATTACKS (each: cp model.py, edit ONLY one impl region; run `adversary weakness nagini pytest-dev__pytest-5787 <path>`, run concurrently in batches of <=3 JVM+Z3 jobs):
- atk_1.py (prepatch site A / boundary): serialize emits only chain[len-1] (outermost link, collapse). weakness EXIT=2 NOT-A-COUNTEREXAMPLE (verification failed) — fails len(Result())==len(chain) for len>=2. PREPATCH BUG A reproduced.
- atk_2.py (order/control-flow): serialize reverses link order. EXIT=2, verification failed (fails per-index Forall).
- atk_3.py (boundary/partial-domain): serialize loops to len-1, drops last link. EXIT=2, verification failed (len mismatch).
- atk_4.py (content corruption / ungrounded-oracle echo): serialize emits chain[i]+1. EXIT=2, verification failed (per-index copy_link identity violated).
- atk_5.py (prepatch site B / boundary): deserialize rebuilds only transport[len-1] (single-link collapse). EXIT=2 NOT-A-COUNTEREXAMPLE (verification failed). PREPATCH BUG B reproduced.
- atk_6.py (count/duplication): serialize emits each link twice (2x length). EXIT=2, verification failed (len mismatch).
- atk_7.py (partial-domain control-flow-effect): serialize correct only path emits chain[0] always (single link, ignoring len). EXIT=2, verification failed.
No attack returned CANDIDATE (exit 0). Therefore NO faithful refined patch needed materialization/resolve; the resolve-obligation is vacuously satisfied (nothing verified-yet-wrong to run).

REFINEMENT.MD AUDIT: Legs are R / A-reference / I only; no consumed @ContractOnly axiom (D. no kind-3 confirmed — the two genuinely-changed ops serialize/deserialize are modeled DEEPLY as verified per-link loops, not hidden behind a change-op axiom). A-reference correspondence verified against patch.diff (gold, src/_pytest/reports.py two-site change): serialize_longrepr iterates rep.longrepr.chain emitting (serialize_repr_traceback, serialize_repr_crash, description) per link (A2, every link/order) <-> model loop out=out+[chain[i]]; _report_kwargs_from_json iterates reportdict['longrepr']['chain'] rebuilding each link then ExceptionChainRepr(chain) (B2) <-> model loop out=out+[transport[i]]; per-link __dict__.copy()/re-__init__ content-preserving (A3/B3) <-> copy_link identity, validated ==real callee by axiom_check.py/G-AX (A-reference, not consumed). mapping.md R-refinements (link tuple<->int token, list order<->list order, len<->len, ReprExceptionInfo<->length-1 chain) are faithful.

VERDICT: SOUND. >=5 (7) distinct same-spec wrong impls machine-checked, none verifies; positive control verifies; both prepatch bugs reproduce; spec pins output to the gold identity => verify=>correct. No verifying-wrong-impl exists to break resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the nagini bundle for pytest-dev__pytest-5787.

Spec under test: serialize_chain(chain: List[int]) requires len>=1 and ensures len(Result())==len(chain) with Result()[k]==copy_link(chain[k]) for all k in [0,len); deserialize_chain is symmetric; copy_link is @Pure identity. Together these entail the whole-chain round-trip identity deserialize(serialize(chain))==chain for any length>=1, with count and order preserved.

Real callee behavior (checked at base_commit 955e5422 + gold patch, src/_pytest/reports.py:344-480):
- serialize_longrepr iterates rep.longrepr.chain in order and appends one transport entry per link (result['chain'].append(...)) -> count + order preserved; result['chain']=None only for the non-ExceptionChainRepr single-stage form.
- _report_kwargs_from_json iterates reportdict['longrepr']['chain'] in order, rebuilding one link each into ExceptionChainRepr(chain) -> count + order preserved.
- Per-link (de)serializers are unchanged __dict__.copy()/re-__init__ operations, content-preserving, i.e. identity under the token projection (crash message) -> matches copy_link=identity.

Independent verification: re-ran the bundle's conformance_check.py against the real patched tree (with a py-capable interpreter python). Exit 0 over 8 boundary trials (lengths 1,2,3,200; negatives; repeats) + 52000 fuzz trials (104016 modeled-function calls, seed 5787). Shadow (model impl regions, contracts stripped) == real repo (de)serializers on every trial: per-index token match, per-index description order cross-check, no input mutation (read fraction), and composed round trip o_rebuilt==tokens. No input was found where the modeled functions disagree with the real callees.

The type abstraction (link tuple <-> int token; the count/order property is what the F2P tests observe) is sound: the tokens carrier faithfully models exactly the length+ordering behavior the gold patch fixes, and the pre-patch collapse (transport carries only chain[-1]) is exactly the negated postcondition (G-DIFF confirms both prepatch skeletons fail). The spec does not over-claim beyond what the real code guarantees, and G-AX confirms the two-state differential (whole chain survives on patched, collapses on unpatched).

Conclusion: the modeled function agrees with the real callee on all tested inputs; no diverging input exists. Spec is FAITHFUL (neither too strong nor drifting).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verdict: NO-LEAKAGE. Judged the consumer-visible spec view (produced by markers.spec_view; impl regions elided) against the public problem_statement ONLY (hints_text excluded per policy).

Mechanical G-LEAK screen: status=pass, 'spec view clean', no hard failures — confirmed it runs against the frozen row's real problem_statement.

Semantic check (the substantive judgment):
1. The public problem_statement ('exception serialization should include chained exceptions'; shows xdist collapsing a multi-stage failure to only the last exception) already states the exact property the spec encodes: serialize/deserialize must preserve the WHOLE chain of links in order, not collapse to the outermost link. The spec view therefore stays at the altitude of the public task and reveals nothing beyond it.
2. No repo edit-localizers leak. None of the 13 distinctive patched symbols (disassembled_report, _report_to_json, _report_kwargs_from_json, serialize_repr_traceback/crash/entry, deserialize_repr_*, serialize_longrepr, pytest_report_(from/to)_serializable, _(to/from)_json) appear anywhere in the spec view. It uses only abstract model vocabulary: serialize_chain, deserialize_chain, chain, link, transport, copy_link.
3. No patched file/module path: src/_pytest/reports.py (and dotted _pytest.reports) is absent from the spec view.
4. No diff markers, no gold-patch changed lines reproduced (>=8-char normalized), no bug/fix/pre-patch narration in comments/docstrings.
5. The List[int]/opaque-token type abstraction deliberately hides all edit specifics (the per-link __dict__.copy structure); comments reference only model/framework identifiers (copy_link, PSeq, ToSeq, axiom_check.py, G-AX), never repo internals. Prepatch models and the collapse-to-chain[-1] detail live outside the spec view (refinement.md/model_prepatch*), not in the consumer view.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
