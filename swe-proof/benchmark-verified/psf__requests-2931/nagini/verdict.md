# P2 adversarial audit — psf__requests-2931

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_n1_prepatch.py`, `atk_n2_serialize_forcefalse.py`, `atk_n3_serialize_oracle_keeptag.py`, `atk_n4_normalize_keeptag.py`, `atk_n5_ctor_negtag.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_c1_normalize_no_native.py`, `atk_c2_serialize_echo.py`, `atk_c3_normalize_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_c1_normalize_no_native.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_bytes) and Acc(self.data))
@@ -78,7 +76,6 @@
 def serialize_request_body(v: Value) -> Value:
     # pre-conditions-start
     Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -100,7 +97,6 @@
     # A binary query value must be ASCII (the long-standing contract for the
     # query component) so the native-string decoder is defined on it.
     Requires(Implies(v.is_bytes, is_ascii(v.data)))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -110,7 +106,6 @@
     Ensures(Result().data == v.data)
     # post-conditions-end
     # impl-start
-    nd = to_native(v.is_bytes, v.data)
-    r = Value(False, nd)
+    r = Value(False, v.data)
     return r
     # impl-end
```

Attack 2 — `atk_c2_serialize_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_bytes) and Acc(self.data))
@@ -78,7 +76,6 @@
 def serialize_request_body(v: Value) -> Value:
     # pre-conditions-start
     Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -89,7 +86,9 @@
     Ensures(Result().data == v.data)
     # post-conditions-end
     # impl-start
-    r = Value(v.is_bytes, v.data)
+    tag = v.is_bytes
+    content = v.data
+    r = Value(tag, content)
     return r
     # impl-end
 
@@ -100,7 +99,6 @@
     # A binary query value must be ASCII (the long-standing contract for the
     # query component) so the native-string decoder is defined on it.
     Requires(Implies(v.is_bytes, is_ascii(v.data)))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
```

Attack 3 — `atk_c3_normalize_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_bytes) and Acc(self.data))
@@ -78,7 +76,6 @@
 def serialize_request_body(v: Value) -> Value:
     # pre-conditions-start
     Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -100,7 +97,6 @@
     # A binary query value must be ASCII (the long-standing contract for the
     # query component) so the native-string decoder is defined on it.
     Requires(Implies(v.is_bytes, is_ascii(v.data)))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -111,6 +107,7 @@
     # post-conditions-end
     # impl-start
     nd = to_native(v.is_bytes, v.data)
-    r = Value(False, nd)
+    nd2 = nd
+    r = Value(False, nd2)
     return r
     # impl-end
```

Attack 4 — `atk_n1_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_bytes) and Acc(self.data))
@@ -78,7 +76,6 @@
 def serialize_request_body(v: Value) -> Value:
     # pre-conditions-start
     Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -89,7 +86,8 @@
     Ensures(Result().data == v.data)
     # post-conditions-end
     # impl-start
-    r = Value(v.is_bytes, v.data)
+    nd = to_native(v.is_bytes, v.data)
+    r = Value(False, nd)
     return r
     # impl-end
 
@@ -100,7 +98,6 @@
     # A binary query value must be ASCII (the long-standing contract for the
     # query component) so the native-string decoder is defined on it.
     Requires(Implies(v.is_bytes, is_ascii(v.data)))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
```

Attack 5 — `atk_n2_serialize_forcefalse.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_bytes) and Acc(self.data))
@@ -78,7 +76,6 @@
 def serialize_request_body(v: Value) -> Value:
     # pre-conditions-start
     Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -89,7 +86,7 @@
     Ensures(Result().data == v.data)
     # post-conditions-end
     # impl-start
-    r = Value(v.is_bytes, v.data)
+    r = Value(False, v.data)
     return r
     # impl-end
 
@@ -100,7 +97,6 @@
     # A binary query value must be ASCII (the long-standing contract for the
     # query component) so the native-string decoder is defined on it.
     Requires(Implies(v.is_bytes, is_ascii(v.data)))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
```

Attack 6 — `atk_n3_serialize_oracle_keeptag.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_bytes) and Acc(self.data))
@@ -78,7 +76,6 @@
 def serialize_request_body(v: Value) -> Value:
     # pre-conditions-start
     Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -89,7 +86,8 @@
     Ensures(Result().data == v.data)
     # post-conditions-end
     # impl-start
-    r = Value(v.is_bytes, v.data)
+    nd = to_native(v.is_bytes, v.data)
+    r = Value(v.is_bytes, nd)
     return r
     # impl-end
 
@@ -100,7 +98,6 @@
     # A binary query value must be ASCII (the long-standing contract for the
     # query component) so the native-string decoder is defined on it.
     Requires(Implies(v.is_bytes, is_ascii(v.data)))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
```

Attack 7 — `atk_n4_normalize_keeptag.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_bytes) and Acc(self.data))
@@ -78,7 +76,6 @@
 def serialize_request_body(v: Value) -> Value:
     # pre-conditions-start
     Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -100,7 +97,6 @@
     # A binary query value must be ASCII (the long-standing contract for the
     # query component) so the native-string decoder is defined on it.
     Requires(Implies(v.is_bytes, is_ascii(v.data)))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -111,6 +107,6 @@
     # post-conditions-end
     # impl-start
     nd = to_native(v.is_bytes, v.data)
-    r = Value(False, nd)
+    r = Value(v.is_bytes, nd)
     return r
     # impl-end
```

Attack 8 — `atk_n5_ctor_negtag.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List, Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -62,7 +61,6 @@
     def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.is_bytes) and Acc(self.data))
@@ -70,15 +68,14 @@
         Ensures(self.data == data)
         # post-conditions-end
         # impl-start
-        self.is_bytes = is_bytes  # type: bool
-        self.data = data  # type: PSeq[int]
+        self.is_bytes = not is_bytes
+        self.data = data
         # impl-end
 
 
 def serialize_request_body(v: Value) -> Value:
     # pre-conditions-start
     Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
@@ -100,7 +97,6 @@
     # A binary query value must be ASCII (the long-standing contract for the
     # query component) so the native-string decoder is defined on it.
     Requires(Implies(v.is_bytes, is_ascii(v.data)))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for psf__requests-2931.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) When a textual-or-binary value is serialized to become the outgoing
      HTTP request body, its representation is preserved exactly: a value that
      arrives as a binary octet string stays a binary octet string (its type
      tag and its octet content are unchanged), and a value that arrives as a
      native text string stays native text. In particular a binary payload
      whose octets are not all ASCII-decodable is carried through verbatim
      rather than being run through a native-string decoder that would change
      its type (and would be undefined on non-ASCII octets).

  (2) A textual-or-binary value supplied as the query component of a URL is, by
      contrast, normalized to a native text string before being appended to the
      query: a binary octet string of ASCII octets becomes native text with the
      same characters, and a native text string is left as native text. This is
      the long-standing behaviour for query parameters and must be retained.

A value is modelled as a small object carrying a type tag (`is_bytes`) and its
content as `PSeq[int]` (octet values for a binary string, code points for text;
Nagini bans `str`/`bytes` indexing). The native-string decoder used for query
normalization is the unchanged utility callee, axiomatized as `to_native`: it
is defined only on ASCII octets for a binary input and returns the same content
as a native string there. The body path does NOT use it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def to_native(v_is_bytes: bool, v_data: PSeq[int]) -> PSeq[int]:
    """The unchanged native-string decoder (utility callee). For a native-text
    input it is the identity; for a binary input it ASCII-decodes, which is
    defined ONLY when every octet is ASCII (< 128) and yields the same content
    as native text. The result is always native text (the caller drops the
    binary tag). Provenance + executable soundness check: mapping.md /
    axiom_check.py (G-AX runs the real callee against this contract).
    """
    Requires(Implies(v_is_bytes, is_ascii(v_data)))
    Ensures(Result() == v_data)
# axioms-end


# pure-start
@Pure
def is_ascii(b: PSeq[int]) -> bool:
    """Every element of the content is an ASCII octet (< 128)."""
    return Forall(int, lambda i: (Implies(0 <= i and i < len(b), b[i] < 128),
                                  [[b[i]]]))
# pure-end


class Value:
    """A textual-or-binary string value: a type tag plus its content."""

    def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_bytes) and Acc(self.data))
        Ensures(self.is_bytes == is_bytes)
        Ensures(self.data == data)
        # post-conditions-end
        # impl-start
        self.is_bytes = is_bytes  # type: bool
        self.data = data  # type: PSeq[int]
        # impl-end


def serialize_request_body(v: Value) -> Value:
    # pre-conditions-start
    Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    Ensures(Acc(Result().is_bytes) and Acc(Result().data))
    # The representation is preserved exactly: same type tag, same content.
    # A binary payload (incl. one with non-ASCII octets) stays binary.
    Ensures(Result().is_bytes == v.is_bytes)
    Ensures(Result().data == v.data)
    # post-conditions-end
    # impl-start
    r = Value(v.is_bytes, v.data)
    return r
    # impl-end


def normalize_query_string(v: Value) -> Value:
    # pre-conditions-start
    Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    # A binary query value must be ASCII (the long-standing contract for the
    # query component) so the native-string decoder is defined on it.
    Requires(Implies(v.is_bytes, is_ascii(v.data)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    Ensures(Acc(Result().is_bytes) and Acc(Result().data))
    # The query value is normalized to native text with the same characters.
    Ensures(Result().is_bytes == False)
    Ensures(Result().data == v.data)
    # post-conditions-end
    # impl-start
    nd = to_native(v.is_bytes, v.data)
    r = Value(False, nd)
    return r
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for nagini psf__requests-2931. Scratch: Env: adversary CLI run venv with SBU_BENCHMARK_DIR=benchmark-verified; it dispatches scripts/nagini_verify.sh (own nagini env). Verdict: SOUND.

### Positive control
pos_control.py = bundle model.py verbatim. `adversary verify nagini psf__requests-2931 pos_control.py` => VERIFIED in 12.8s (exit 0).

== ATTACKS (all same-spec confirmed: `adversary same-spec` => SAME/exit 0 for all 8; only impl regions edited, axioms/@Pure/Requires/Ensures byte-identical) ==
Command per attack: `python -m swebench_unified.adversary weakness nagini psf__requests-2931 <path>`.

CANDIDATEs (share spec AND verify):
- atk_c1_normalize_no_native.py: normalize_query_string returns Value(False, v.data) WITHOUT calling to_native. weakness=CANDIDATE (12.8s, exit 0). Faithful patch patch_c1.diff (site A gold; site B direct .decode('ascii') on bytes / identity on str = exactly what to_native_string does on py3). run_resolve => {resolved:true, completed:true, attempts:1, note:'resolved'}. RESOLVES.
- atk_c2_serialize_echo.py: serialize_request_body via temps tag/content, same value. weakness=CANDIDATE (12.8s, exit 0). Faithful patch = gold verbatim (behaviourally identical). run_resolve => resolved:true (tag gold-c2c3). RESOLVES.
- atk_c3_normalize_echo.py: normalize via to_native then rebind nd2=nd. weakness=CANDIDATE (14.0s, exit 0). Faithful patch = gold verbatim. Covered by same gold run_resolve => resolved:true. RESOLVES.

### NON-COUNTEREXAMPLES (share spec but REJECTED by verification, exit 2 - spec correctly senses each defect):
- atk_n1_prepatch.py: the actual prepatch bug - serialize routes body through to_native, Value(False, nd). weakness=NOT-A-COUNTEREXAMPLE, verification failed. Prepatch bug reproduced (matches bundle model_prepatch.py). PREPATCH_REPRODUCED=true.
- atk_n2_serialize_forcefalse.py: serialize returns Value(False, v.data) (wrong tag). REJECTED (fails Result().is_bytes==v.is_bytes).
- atk_n3_serialize_oracle_keeptag.py: ungrounded-oracle echo - serialize calls to_native(v.is_bytes,v.data) but keeps tag; to_native's Requires(binary=>ascii) not established in serialize's permission-only Requires. REJECTED (verification failed).
- atk_n4_normalize_keeptag.py: control-flow-effect - normalize keeps original tag Value(v.is_bytes, nd). REJECTED (fails Result().is_bytes==False for binary input).
- atk_n5_ctor_negtag.py: deep-model tamper - Value.__init__ stores `not is_bytes`; breaks the constructor Ensures and downstream postconditions. REJECTED.

### Why SOUND
Every verifying wrong-impl candidate's materialized faithful refined patch RESOLVED under the official harness (run_resolve, real SWE-bench_Verified image, F2P+P2P). No verify->non-resolve gap found. The spec's postconditions pin the FULL observable of both functions over the entire Requires domain: serialize_request_body pins Result().is_bytes==v.is_bytes AND Result().data==v.data (permission-only Requires => whole str/bytes domain incl. non-ASCII binary); normalize_query_string pins Result().is_bytes==False AND Result().data==v.data over Requires(binary=>ASCII). Any verifying impl is therefore observably gold-equivalent (tag+content), so it resolves. All three CANDIDATEs are behaviour-preserving echoes and all resolved.

### Refinement.md leg audit
A1 (Value param <-> str/bytes): R - valid type refinement per mapping.md sec2. A2 (return Value(v.is_bytes,v.data) <-> return data): I+R - the genuinely-changed op (body no longer decoded) is modeled DIRECTLY, not behind an axiom; confirmed by atk_n1 (the exact removed decode) being REJECTED. B1 (to_native <-> to_native_string): A-consumed - weakest contract on the UNCHANGED utility callee; G-AX axiom_check.py run => 'G-AX OK [real callee]: sound on 8 text + 6 bytes boundary + 40000 fuzz, rejects 5 non-ASCII binary', exit 0. B2 (Value(False,nd) <-> native params): R+I. Section C claim (no kind-3, no A-reference) is CORRECT: the one consumed axiom maps to an unchanged callee the gold patch does not modify. Every leg is R / A-consumed / I. No kind-3 detected. A-leg correspondence holds (G-AX pass + c1 shows the axiom carries no discriminating power beyond its faithful correspondence, since c1 omits to_native entirely yet still resolves).

All ≥5 attacks (8 total) fully verified; every needed run_resolve completed. No break found => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_n1_prepatch.py`, `atk_n2_serialize_forcefalse.py`, `atk_n3_serialize_oracle_keeptag.py`, `atk_n4_normalize_keeptag.py`, `atk_n5_ctor_negtag.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_c1_normalize_no_native.py`, `atk_c2_serialize_echo.py`, `atk_c3_normalize_echo.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_c1_normalize_no_native.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_c2_serialize_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_c3_normalize_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_n1_prepatch.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_n2_serialize_forcefalse.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_n3_serialize_oracle_keeptag.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_n4_normalize_keeptag.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_n5_ctor_negtag.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for psf__requests-2931.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) When a textual-or-binary value is serialized to become the outgoing
      HTTP request body, its representation is preserved exactly: a value that
      arrives as a binary octet string stays a binary octet string (its type
      tag and its octet content are unchanged), and a value that arrives as a
      native text string stays native text. In particular a binary payload
      whose octets are not all ASCII-decodable is carried through verbatim
      rather than being run through a native-string decoder that would change
      its type (and would be undefined on non-ASCII octets).

  (2) A textual-or-binary value supplied as the query component of a URL is, by
      contrast, normalized to a native text string before being appended to the
      query: a binary octet string of ASCII octets becomes native text with the
      same characters, and a native text string is left as native text. This is
      the long-standing behaviour for query parameters and must be retained.

A value is modelled as a small object carrying a type tag (`is_bytes`) and its
content as `PSeq[int]` (octet values for a binary string, code points for text;
Nagini bans `str`/`bytes` indexing). The native-string decoder used for query
normalization is the unchanged utility callee, axiomatized as `to_native`: it
is defined only on ASCII octets for a binary input and returns the same content
as a native string there. The body path does NOT use it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def to_native(v_is_bytes: bool, v_data: PSeq[int]) -> PSeq[int]:
    """The unchanged native-string decoder (utility callee). For a native-text
    input it is the identity; for a binary input it ASCII-decodes, which is
    defined ONLY when every octet is ASCII (< 128) and yields the same content
    as native text. The result is always native text (the caller drops the
    binary tag). Provenance + executable soundness check: mapping.md /
    axiom_check.py (G-AX runs the real callee against this contract).
    """
    Requires(Implies(v_is_bytes, is_ascii(v_data)))
    Ensures(Result() == v_data)
# axioms-end


# pure-start
@Pure
def is_ascii(b: PSeq[int]) -> bool:
    """Every element of the content is an ASCII octet (< 128)."""
    return Forall(int, lambda i: (Implies(0 <= i and i < len(b), b[i] < 128),
                                  [[b[i]]]))
# pure-end


class Value:
    """A textual-or-binary string value: a type tag plus its content."""

    def __init__(self, is_bytes: bool, data: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.is_bytes) and Acc(self.data))
        Ensures(self.is_bytes == is_bytes)
        Ensures(self.data == data)
        # post-conditions-end
        # impl-start
        self.is_bytes = is_bytes  # type: bool
        self.data = data  # type: PSeq[int]
        # impl-end


def serialize_request_body(v: Value) -> Value:
    # pre-conditions-start
    Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    Ensures(Acc(Result().is_bytes) and Acc(Result().data))
    # The representation is preserved exactly: same type tag, same content.
    # A binary payload (incl. one with non-ASCII octets) stays binary.
    Ensures(Result().is_bytes == v.is_bytes)
    Ensures(Result().data == v.data)
    # post-conditions-end
    # impl-start
    r = Value(v.is_bytes, v.data)
    return r
    # impl-end


def normalize_query_string(v: Value) -> Value:
    # pre-conditions-start
    Requires(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    # A binary query value must be ASCII (the long-standing contract for the
    # query component) so the native-string decoder is defined on it.
    Requires(Implies(v.is_bytes, is_ascii(v.data)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(v.is_bytes, 1 / 2) and Acc(v.data, 1 / 2))
    Ensures(Acc(Result().is_bytes) and Acc(Result().data))
    # The query value is normalized to native text with the same characters.
    Ensures(Result().is_bytes == False)
    Ensures(Result().data == v.data)
    # post-conditions-end
    # impl-start
    nd = to_native(v.is_bytes, v.data)
    r = Value(False, nd)
    return r
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for nagini psf__requests-2931. Scratch: Env: adversary CLI run venv with SBU_BENCHMARK_DIR=benchmark-verified; it dispatches scripts/nagini_verify.sh (own nagini env). Verdict: SOUND.

### Positive control
pos_control.py = bundle model.py verbatim. `adversary verify nagini psf__requests-2931 pos_control.py` => VERIFIED in 12.8s (exit 0).

== ATTACKS (all same-spec confirmed: `adversary same-spec` => SAME/exit 0 for all 8; only impl regions edited, axioms/@Pure/Requires/Ensures byte-identical) ==
Command per attack: `python -m swebench_unified.adversary weakness nagini psf__requests-2931 <path>`.

CANDIDATEs (share spec AND verify):
- atk_c1_normalize_no_native.py: normalize_query_string returns Value(False, v.data) WITHOUT calling to_native. weakness=CANDIDATE (12.8s, exit 0). Faithful patch patch_c1.diff (site A gold; site B direct .decode('ascii') on bytes / identity on str = exactly what to_native_string does on py3). run_resolve => {resolved:true, completed:true, attempts:1, note:'resolved'}. RESOLVES.
- atk_c2_serialize_echo.py: serialize_request_body via temps tag/content, same value. weakness=CANDIDATE (12.8s, exit 0). Faithful patch = gold verbatim (behaviourally identical). run_resolve => resolved:true (tag gold-c2c3). RESOLVES.
- atk_c3_normalize_echo.py: normalize via to_native then rebind nd2=nd. weakness=CANDIDATE (14.0s, exit 0). Faithful patch = gold verbatim. Covered by same gold run_resolve => resolved:true. RESOLVES.

### NON-COUNTEREXAMPLES (share spec but REJECTED by verification, exit 2 - spec correctly senses each defect):
- atk_n1_prepatch.py: the actual prepatch bug - serialize routes body through to_native, Value(False, nd). weakness=NOT-A-COUNTEREXAMPLE, verification failed. Prepatch bug reproduced (matches bundle model_prepatch.py). PREPATCH_REPRODUCED=true.
- atk_n2_serialize_forcefalse.py: serialize returns Value(False, v.data) (wrong tag). REJECTED (fails Result().is_bytes==v.is_bytes).
- atk_n3_serialize_oracle_keeptag.py: ungrounded-oracle echo - serialize calls to_native(v.is_bytes,v.data) but keeps tag; to_native's Requires(binary=>ascii) not established in serialize's permission-only Requires. REJECTED (verification failed).
- atk_n4_normalize_keeptag.py: control-flow-effect - normalize keeps original tag Value(v.is_bytes, nd). REJECTED (fails Result().is_bytes==False for binary input).
- atk_n5_ctor_negtag.py: deep-model tamper - Value.__init__ stores `not is_bytes`; breaks the constructor Ensures and downstream postconditions. REJECTED.

### Why SOUND
Every verifying wrong-impl candidate's materialized faithful refined patch RESOLVED under the official harness (run_resolve, real SWE-bench_Verified image, F2P+P2P). No verify->non-resolve gap found. The spec's postconditions pin the FULL observable of both functions over the entire Requires domain: serialize_request_body pins Result().is_bytes==v.is_bytes AND Result().data==v.data (permission-only Requires => whole str/bytes domain incl. non-ASCII binary); normalize_query_string pins Result().is_bytes==False AND Result().data==v.data over Requires(binary=>ASCII). Any verifying impl is therefore observably gold-equivalent (tag+content), so it resolves. All three CANDIDATEs are behaviour-preserving echoes and all resolved.

### Refinement.md leg audit
A1 (Value param <-> str/bytes): R - valid type refinement per mapping.md sec2. A2 (return Value(v.is_bytes,v.data) <-> return data): I+R - the genuinely-changed op (body no longer decoded) is modeled DIRECTLY, not behind an axiom; confirmed by atk_n1 (the exact removed decode) being REJECTED. B1 (to_native <-> to_native_string): A-consumed - weakest contract on the UNCHANGED utility callee; G-AX axiom_check.py run => 'G-AX OK [real callee]: sound on 8 text + 6 bytes boundary + 40000 fuzz, rejects 5 non-ASCII binary', exit 0. B2 (Value(False,nd) <-> native params): R+I. Section C claim (no kind-3, no A-reference) is CORRECT: the one consumed axiom maps to an unchanged callee the gold patch does not modify. Every leg is R / A-consumed / I. No kind-3 detected. A-leg correspondence holds (G-AX pass + c1 shows the axiom carries no discriminating power beyond its faithful correspondence, since c1 omits to_native entirely yet still resolves).

All ≥5 attacks (8 total) fully verified; every needed run_resolve completed. No break found => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No faithfulness drift found. Modeled sites: (A) serialize_request_body ↔ patched _encode_params str/bytes branch (return data); permission-only Requires accepts all values, postcondition pins Result().is_bytes==v.is_bytes ∧ Result().data==v.data — the exact identity the patched branch performs (verified: b'\xc3\xb6\xc3\xb6' preserved verbatim). (B) normalize_query_string ↔ patched prepare_url coercion (params=to_native_string(params)); Requires(binary⇒is_ascii) coincides with the real to_native_string definedness domain — non-ASCII binary raises UnicodeDecodeError in the real callee (confirmed live), so the precondition faithfully excludes only the raising domain rather than over-claiming. Postcondition native-text/same-content matches to_native_string on str (identity) and ASCII bytes (decode). Mechanical evidence against REAL patched testbed (gold patch applied): axiom_check.py exit 0 (40k fuzz + non-ASCII rejection); conformance_check.py exit 0 on 122,034 inputs, 0 disagreements (site A incl. non-ASCII binary, site B fragment + end-to-end prepare_url); nagini_verify.sh model.py = Verification successful. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over spec_view) passes clean: no diff markers, no reproduced gold-patch line (>=8 chars), no patched file path 'requests/models.py', no spec-view identifier or comment embedding the distinctive patched repo symbols {'encode_params','prepare_url'}, and no bug/fix narration terms. Semantic review confirms no leakage beyond the PUBLIC problem_statement: (1) the public task already states the bug is 'calling to_native_string' on a binary payload (data=u"ööö".encode(...)), so the body-site fix concept and the callee name are already public; (2) the spec view uses only abstracted model symbols (serialize_request_body, normalize_query_string, to_native, Value) and NEVER names the actual patched functions _encode_params or prepare_url; (3) comments state DESIRED behaviour (representation preserved exactly; query value normalized to native text; 'The body path does NOT use it') rather than narrating an edit; (4) the query site (B) is framed as 'long-standing behaviour ... must be retained' — an invariant/observable behaviour (checked by the P2P test), not disclosure of an added edit, and per refinement.md it is a behaviour-preserving relocation revealing nothing a solver couldn't infer from the tests. Every discriminator in the spec view is either observable test behaviour or already public in problem_statement. No single spec-view line localizes the gold edit beyond the public statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `refinement.md`, which ships in this bundle, so a reader can start there.
