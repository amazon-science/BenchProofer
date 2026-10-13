# P2 adversarial audit — django__django-11133

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 # Representation tags.
 KIND_OCTETS = 0   # an immutable octet string
@@ -74,7 +73,6 @@
                  data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.kind) and Acc(self.buf) and Acc(self.cps)
@@ -96,7 +94,6 @@
     # pre-conditions-start
     Requires(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
              and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
@@ -112,7 +109,7 @@
                     Result().data == charset_encode(v.cps)))
     # post-conditions-end
     # impl-start
-    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
+    if v.kind == KIND_OCTETS:
         return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
     return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 # Representation tags.
 KIND_OCTETS = 0   # an immutable octet string
@@ -74,7 +73,6 @@
                  data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.kind) and Acc(self.buf) and Acc(self.cps)
@@ -96,7 +94,6 @@
     # pre-conditions-start
     Requires(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
              and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
@@ -112,7 +109,7 @@
                     Result().data == charset_encode(v.cps)))
     # post-conditions-end
     # impl-start
-    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
+    if v.kind == KIND_VIEW:
         return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
     return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 # Representation tags.
 KIND_OCTETS = 0   # an immutable octet string
@@ -74,7 +73,6 @@
                  data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.kind) and Acc(self.buf) and Acc(self.cps)
@@ -96,7 +94,6 @@
     # pre-conditions-start
     Requires(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
              and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
@@ -113,6 +110,6 @@
     # post-conditions-end
     # impl-start
     if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
-        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
-    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
+        return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
+    return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 # Representation tags.
 KIND_OCTETS = 0   # an immutable octet string
@@ -74,7 +73,6 @@
                  data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.kind) and Acc(self.buf) and Acc(self.cps)
@@ -96,7 +94,6 @@
     # pre-conditions-start
     Requires(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
              and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
@@ -114,5 +111,5 @@
     # impl-start
     if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
         return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
-    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
+    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.buf))
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 # Representation tags.
 KIND_OCTETS = 0   # an immutable octet string
@@ -74,7 +73,6 @@
                  data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.kind) and Acc(self.buf) and Acc(self.cps)
@@ -96,7 +94,6 @@
     # pre-conditions-start
     Requires(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
              and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
@@ -114,5 +111,7 @@
     # impl-start
     if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
         return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
-    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
+    if v.kind == KIND_TEXT:
+        return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
+    return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 # Representation tags.
 KIND_OCTETS = 0   # an immutable octet string
@@ -74,7 +73,6 @@
                  data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.kind) and Acc(self.buf) and Acc(self.cps)
@@ -96,7 +94,6 @@
     # pre-conditions-start
     Requires(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
              and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
@@ -112,7 +109,7 @@
                     Result().data == charset_encode(v.cps)))
     # post-conditions-end
     # impl-start
-    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
-        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
+    if is_buffer_kind(v.kind):
+        return Value(KIND_OCTETS, v.buf, v.cps, v.cps)
     return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -32,7 +32,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 # Representation tags.
 KIND_OCTETS = 0   # an immutable octet string
@@ -74,7 +73,6 @@
                  data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.kind) and Acc(self.buf) and Acc(self.cps)
@@ -96,7 +94,6 @@
     # pre-conditions-start
     Requires(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
              and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
@@ -112,7 +109,7 @@
                     Result().data == charset_encode(v.cps)))
     # post-conditions-end
     # impl-start
-    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
-        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
-    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
+    if not is_buffer_kind(v.kind):
+        return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
+    return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11133.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A value is coerced to the response body's output bytestring according to its
  runtime representation:

  (1) A value that already carries a raw octet buffer -- whether it is an
      immutable octet string or a buffer view exposing the same underlying
      octets -- is carried through as exactly those octets, with no decoding,
      re-encoding, or textual rendering. The two buffer-bearing representations
      are treated identically: the output is the buffer's octets verbatim.

  (2) A native text value is encoded to octets in the output charset.

  (3) Any other value is first rendered to its native-text form and that text is
      then encoded to octets in the output charset.

A value is modelled as a small object carrying a representation tag (`kind`),
its raw octet buffer (`buf`, meaningful for the two buffer-bearing kinds), and
the code points that are charset-encoded for the text and other kinds (`cps`;
for an "other" value these are the code points of its native-text rendering).
The output bytestring is carried in `data`. Octets and code points are
`PSeq[int]` (Nagini bans `str`/`bytes` indexing).

The charset encoder is the unchanged utility callee, axiomatized as
`charset_encode`; the buffer path does NOT use it. The text and "other" kinds
are observationally identical here (both encode their code points), so the
specification distinguishes only buffer-bearing values from the rest.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *

# Representation tags.
KIND_OCTETS = 0   # an immutable octet string
KIND_VIEW = 1     # a buffer view exposing the same underlying octets
KIND_TEXT = 2     # a native text string
KIND_OTHER = 3    # any other value


# axioms-start
@Pure
@ContractOnly
def charset_encode(cps: PSeq[int]) -> PSeq[int]:
    """The unchanged charset encoder (utility callee): maps a sequence of code
    points to the octet sequence of its encoding in the output charset. A pure,
    deterministic function of its argument (Nagini derives determinism from
    @Pure, which is all the proof needs). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX runs the real callee against this
    contract).
    """
    Ensures(True)
# axioms-end


# pure-start
@Pure
def is_buffer_kind(kind: int) -> bool:
    """The two buffer-bearing representations: an immutable octet string and a
    buffer view exposing the same underlying octets."""
    return kind == KIND_OCTETS or kind == KIND_VIEW
# pure-end


class Value:
    """A value to be coerced to the output bytestring: a representation tag, its
    raw octet buffer, the code points encoded for text/other kinds, and the
    resulting output octets (`data`, meaningful on a result)."""

    def __init__(self, kind: int, buf: PSeq[int], cps: PSeq[int],
                 data: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.kind) and Acc(self.buf) and Acc(self.cps)
                and Acc(self.data))
        Ensures(self.kind == kind)
        Ensures(self.buf == buf)
        Ensures(self.cps == cps)
        Ensures(self.data == data)
        # post-conditions-end
        # impl-start
        self.kind = kind  # type: int
        self.buf = buf    # type: PSeq[int]
        self.cps = cps    # type: PSeq[int]
        self.data = data  # type: PSeq[int]
        # impl-end


def coerce_to_octets(v: Value) -> Value:
    # pre-conditions-start
    Requires(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
             and Acc(v.data, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
            and Acc(v.data, 1 / 2))
    Ensures(Acc(Result().kind) and Acc(Result().buf) and Acc(Result().cps)
            and Acc(Result().data))
    # A buffer-bearing value (octet string OR buffer view, treated identically)
    # is carried through as exactly its underlying octets.
    Ensures(Implies(is_buffer_kind(v.kind), Result().data == v.buf))
    # A text value, and any other value (via its native-text rendering), is
    # encoded to octets in the output charset.
    Ensures(Implies(not is_buffer_kind(v.kind),
                    Result().data == charset_encode(v.cps)))
    # post-conditions-end
    # impl-start
    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: coerce_to_octets postconditions form a TOTAL case split on is_buffer_kind that fully pins observable Result().data: Implies(is_buffer_kind(v.kind), data==v.buf) AND Implies(not is_buffer_kind(v.kind), data==charset_encode(v.cps)). charset_encode is @Pure @ContractOnly (uninterpreted, Ensures(True)) — proof consumes only determinism. Because both arms pin data exactly, the only verifying variants are behavior-preserving refactors, which resolve.

### COMMANDS (from project root):
- positive control: `bash scripts/nagini_verify.sh .../pos_control.py` -> 'Verification successful' 12.34s, exit 0.
- same-spec sanity (atk_1): `python -m swebench_unified.adversary same-spec nagini django__django-11133 .../atk_1.py` -> SAME, exit 0 (edits confined to impl region).
- weakness (each atk_N): `python -m swebench_unified.adversary weakness nagini django__django-11133 .../atk_N.py`, run 3-at-a-time as background jobs.

### Weakness results
- atk_1 prepatch-bug (KIND_OCTETS only; KIND_VIEW falls through) -> exit 2 NOT-A-COUNTEREXAMPLE (verification failed). PREPATCH REPRODUCED: byte-identical impl to model_prepatch.py; spec senses the memoryview F2P gap.
- atk_2 boundary (KIND_VIEW only; KIND_OCTETS falls through) -> exit 2, fails verify.
- atk_3 control-flow-effect (buffer->encode, non-buffer->buf) -> exit 2, fails verify.
- atk_4 ungrounded-oracle echo (non-buffer emits charset_encode(v.buf) not v.cps) -> exit 2, fails verify.
- atk_5 partial-domain (KIND_TEXT encodes; KIND_OTHER wrongly passes v.buf) -> exit 2, fails verify.
- atk_6 ungrounded data (buffer branch emits v.cps not v.buf) -> exit 2, fails verify.
- atk_7 behavior-preserving reorder (non-buffer/encode branch first via `if not is_buffer_kind(v.kind)`, then buffer passthrough) -> exit 0 CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (12.5s).

CANDIDATE atk_7 -> MATERIALIZED FAITHFUL PATCH + OFFICIAL HARNESS: faithful patch reorders make_bytes to test `not isinstance(value,(bytes,memoryview))` first (str/other encode arms) then `return bytes(value)` — same observable behaviour as gold. Ran run_resolve('django__django-11133', patch) via official harness: RESOLVED=True, completed=True, attempts=1, non-flaky. FAIL_TO_PASS test_memoryview_content PASSES; all 63 PASS_TO_PASS pass; 0 failures. => resolving echo, NOT a weakness (per 2026-08-06 G-PANEL-1/G-EQ policy: same-spec verifying attack whose refined patch RESOLVES is not a break).

G-AX / A-leg audit: axiom_check.py exit 0 (buffer passthrough bytes==memoryview==underlying octets on 7 boundary + 20000 fuzz buffers x4 charsets; charset_encode==str.encode determinism on 20000 text + 5000 other fuzz). refinement.md legs: A1-A3 = R (type refinement: value<->Value, bytes() verbatim copy, KIND_VIEW disjunct + data==v.buf models the widened guard directly), A4 = A-consumed (charset_encode <-> str.encode, purity/determinism only). NO kind-3: the one changed op (widening guard for memoryview) is spelled out in impl + pinned by postcondition, not hidden behind an axiom (§B confirmed). A-consumed correspondence to real callee str.encode validated by G-AX. No A-reference deep-model leg (buffer passthrough is verbatim equality, not a recomputed fold) — nothing further to audit there.

CONCLUSION: 7 attacks run (prepatch + 6 distinct wrong impls across partial-domain/boundary/control-flow-effect/ungrounded-oracle-echo classes); all 6 wrong impls rejected by verification; the sole verifying variant is a behavior-preserving reorder whose faithful patch RESOLVES under the official harness. Positive control verifies; G-AX sound. verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11133.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A value is coerced to the response body's output bytestring according to its
  runtime representation:

  (1) A value that already carries a raw octet buffer -- whether it is an
      immutable octet string or a buffer view exposing the same underlying
      octets -- is carried through as exactly those octets, with no decoding,
      re-encoding, or textual rendering. The two buffer-bearing representations
      are treated identically: the output is the buffer's octets verbatim.

  (2) A native text value is encoded to octets in the output charset.

  (3) Any other value is first rendered to its native-text form and that text is
      then encoded to octets in the output charset.

A value is modelled as a small object carrying a representation tag (`kind`),
its raw octet buffer (`buf`, meaningful for the two buffer-bearing kinds), and
the code points that are charset-encoded for the text and other kinds (`cps`;
for an "other" value these are the code points of its native-text rendering).
The output bytestring is carried in `data`. Octets and code points are
`PSeq[int]` (Nagini bans `str`/`bytes` indexing).

The charset encoder is the unchanged utility callee, axiomatized as
`charset_encode`; the buffer path does NOT use it. The text and "other" kinds
are observationally identical here (both encode their code points), so the
specification distinguishes only buffer-bearing values from the rest.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *

# Representation tags.
KIND_OCTETS = 0   # an immutable octet string
KIND_VIEW = 1     # a buffer view exposing the same underlying octets
KIND_TEXT = 2     # a native text string
KIND_OTHER = 3    # any other value


# axioms-start
@Pure
@ContractOnly
def charset_encode(cps: PSeq[int]) -> PSeq[int]:
    """The unchanged charset encoder (utility callee): maps a sequence of code
    points to the octet sequence of its encoding in the output charset. A pure,
    deterministic function of its argument (Nagini derives determinism from
    @Pure, which is all the proof needs). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX runs the real callee against this
    contract).
    """
    Ensures(True)
# axioms-end


# pure-start
@Pure
def is_buffer_kind(kind: int) -> bool:
    """The two buffer-bearing representations: an immutable octet string and a
    buffer view exposing the same underlying octets."""
    return kind == KIND_OCTETS or kind == KIND_VIEW
# pure-end


class Value:
    """A value to be coerced to the output bytestring: a representation tag, its
    raw octet buffer, the code points encoded for text/other kinds, and the
    resulting output octets (`data`, meaningful on a result)."""

    def __init__(self, kind: int, buf: PSeq[int], cps: PSeq[int],
                 data: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.kind) and Acc(self.buf) and Acc(self.cps)
                and Acc(self.data))
        Ensures(self.kind == kind)
        Ensures(self.buf == buf)
        Ensures(self.cps == cps)
        Ensures(self.data == data)
        # post-conditions-end
        # impl-start
        self.kind = kind  # type: int
        self.buf = buf    # type: PSeq[int]
        self.cps = cps    # type: PSeq[int]
        self.data = data  # type: PSeq[int]
        # impl-end


def coerce_to_octets(v: Value) -> Value:
    # pre-conditions-start
    Requires(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
             and Acc(v.data, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.kind, 1 / 2) and Acc(v.buf, 1 / 2) and Acc(v.cps, 1 / 2)
            and Acc(v.data, 1 / 2))
    Ensures(Acc(Result().kind) and Acc(Result().buf) and Acc(Result().cps)
            and Acc(Result().data))
    # A buffer-bearing value (octet string OR buffer view, treated identically)
    # is carried through as exactly its underlying octets.
    Ensures(Implies(is_buffer_kind(v.kind), Result().data == v.buf))
    # A text value, and any other value (via its native-text rendering), is
    # encoded to octets in the output charset.
    Ensures(Implies(not is_buffer_kind(v.kind),
                    Result().data == charset_encode(v.cps)))
    # post-conditions-end
    # impl-start
    if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:
        return Value(KIND_OCTETS, v.buf, v.cps, v.buf)
    return Value(KIND_OCTETS, v.buf, v.cps, charset_encode(v.cps))
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: coerce_to_octets postconditions form a TOTAL case split on is_buffer_kind that fully pins observable Result().data: Implies(is_buffer_kind(v.kind), data==v.buf) AND Implies(not is_buffer_kind(v.kind), data==charset_encode(v.cps)). charset_encode is @Pure @ContractOnly (uninterpreted, Ensures(True)) — proof consumes only determinism. Because both arms pin data exactly, the only verifying variants are behavior-preserving refactors, which resolve.

### COMMANDS (from project root):
- positive control: `bash scripts/nagini_verify.sh .../pos_control.py` -> 'Verification successful' 12.34s, exit 0.
- same-spec sanity (atk_1): `python -m swebench_unified.adversary same-spec nagini django__django-11133 .../atk_1.py` -> SAME, exit 0 (edits confined to impl region).
- weakness (each atk_N): `python -m swebench_unified.adversary weakness nagini django__django-11133 .../atk_N.py`, run 3-at-a-time as background jobs.

### Weakness results
- atk_1 prepatch-bug (KIND_OCTETS only; KIND_VIEW falls through) -> exit 2 NOT-A-COUNTEREXAMPLE (verification failed). PREPATCH REPRODUCED: byte-identical impl to model_prepatch.py; spec senses the memoryview F2P gap.
- atk_2 boundary (KIND_VIEW only; KIND_OCTETS falls through) -> exit 2, fails verify.
- atk_3 control-flow-effect (buffer->encode, non-buffer->buf) -> exit 2, fails verify.
- atk_4 ungrounded-oracle echo (non-buffer emits charset_encode(v.buf) not v.cps) -> exit 2, fails verify.
- atk_5 partial-domain (KIND_TEXT encodes; KIND_OTHER wrongly passes v.buf) -> exit 2, fails verify.
- atk_6 ungrounded data (buffer branch emits v.cps not v.buf) -> exit 2, fails verify.
- atk_7 behavior-preserving reorder (non-buffer/encode branch first via `if not is_buffer_kind(v.kind)`, then buffer passthrough) -> exit 0 CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (12.5s).

CANDIDATE atk_7 -> MATERIALIZED FAITHFUL PATCH + OFFICIAL HARNESS: faithful patch reorders make_bytes to test `not isinstance(value,(bytes,memoryview))` first (str/other encode arms) then `return bytes(value)` — same observable behaviour as gold. Ran run_resolve('django__django-11133', patch) via official harness: RESOLVED=True, completed=True, attempts=1, non-flaky. FAIL_TO_PASS test_memoryview_content PASSES; all 63 PASS_TO_PASS pass; 0 failures. => resolving echo, NOT a weakness (per 2026-08-06 G-PANEL-1/G-EQ policy: same-spec verifying attack whose refined patch RESOLVES is not a break).

G-AX / A-leg audit: axiom_check.py exit 0 (buffer passthrough bytes==memoryview==underlying octets on 7 boundary + 20000 fuzz buffers x4 charsets; charset_encode==str.encode determinism on 20000 text + 5000 other fuzz). refinement.md legs: A1-A3 = R (type refinement: value<->Value, bytes() verbatim copy, KIND_VIEW disjunct + data==v.buf models the widened guard directly), A4 = A-consumed (charset_encode <-> str.encode, purity/determinism only). NO kind-3: the one changed op (widening guard for memoryview) is spelled out in impl + pinned by postcondition, not hidden behind an axiom (§B confirmed). A-consumed correspondence to real callee str.encode validated by G-AX. No A-reference deep-model leg (buffer passthrough is verbatim equality, not a recomputed fold) — nothing further to audit there.

CONCLUSION: 7 attacks run (prepatch + 6 distinct wrong impls across partial-domain/boundary/control-flow-effect/ungrounded-oracle-echo classes); all 6 wrong impls rejected by verification; the sole verifying variant is a behavior-preserving reorder whose faithful patch RESOLVES under the official harness. Positive control verifies; G-AX sound. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo drift) audit for django__django-11133 nagini bundle. Spec region byte-identical (same-spec: SAME, exit 0). The modeled coerce_to_octets refines HttpResponseBase.make_bytes (post-gold-patch, django/http/response.py) via the mapping.md type abstraction: bytes->KIND_OCTETS, memoryview->KIND_VIEW, str->KIND_TEXT, other->KIND_OTHER. Buffer branch returns v.buf (== bytes(value) underlying octets verbatim), non-buffer branch returns charset_encode(cps) (== value.encode/str(value).encode). Verified no drift on all tested inputs: recorded G-CONF gate passed with 100196 inputs, 0 disagreements, seed 11133; my independent differential against the real gold-patched repo over adversarial edge cases -- multi-byte and .cast() memoryviews, reversed/sliced views, bytearray-backed views, lone surrogate '\ud800', astral chars, exotic non-string objects, complex), high bytes -- across utf-8/latin-1/ascii/utf-16 found 0 disagreements, including matching raise-outcomes. The spec is neither too strong nor drifting: no input found where the modeled function disagrees with the real callee. The single fix behaviour (memoryview joining the verbatim-octet branch) is modeled directly and not hidden behind an axiom; the only axiom (charset_encode) covers the unchanged str.encode and consumes only purity/determinism, which axiom_check.py (G-AX pass) validates. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (0 hard failures) and semantic review confirms NO-LEAKAGE. Gold edit: make_bytes widens `isinstance(value, bytes)` -> `isinstance(value, (bytes, memoryview))` so a memoryview is carried through as verbatim octets rather than rendered to text. The public problem_statement ALREADY discloses this discriminator in full: it shows HttpResponse(memoryview(b'My Content')).content producing the wrong b'<memory at 0x...>' and states the expected result is b'My Content' (the memoryview's underlying bytes verbatim), while bytes/str cases already work. Thus the memoryview->verbatim-octets behavior is public up front. The spec view stays above the edit: (1) purely abstract behavioral prose (kinds: octets/view/text/other; 'buffer view exposing the same underlying octets' rather than the concrete `memoryview`); (2) no patched file path (django/http/response.py absent); (3) no patched repo symbol — `make_bytes`/`force_bytes` appear ONLY in hints_text and are correctly NOT echoed; `charset_encode` is a neutral placeholder; (4) no diff markers, no reproduced gold-patch line (verified: no changed line of len>=8 present in normalized view); (5) no bug/fix narration; behavior stated as desired, not as an edit. The 4-kind dispatch is the natural faithful model whose buffer-view-verbatim discriminator coincides with the already-public problem-statement behavior — no leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
