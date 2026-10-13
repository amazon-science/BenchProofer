# P2 adversarial audit — django__django-13279

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 21 admissible attacks re-run of 21 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 21 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py`, `atk_19.py`, `atk_20.py`, `atk_0_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_6.py`, `atk_8.py`, `atk_13.py`, `atk_16.py`, `atk_17.py`, `atk_18.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (21):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -167,5 +167,6 @@
     if algorithm == ALGO_LEGACY:
         body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    e = empty_payload()
+    return Frame(FMT_MODERN, modern_digest(e), e)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -167,5 +167,6 @@
     if algorithm == ALGO_LEGACY:
         body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    c = PSeq(120, 121, 122)
+    return Frame(FMT_MODERN, modern_digest(c), c)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -167,5 +167,6 @@
     if algorithm == ALGO_LEGACY:
         body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    t = ToSeq(payload).drop(1)
+    return Frame(FMT_MODERN, modern_digest(t), t)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -166,6 +166,6 @@
     # impl-start
     if algorithm == ALGO_LEGACY:
         body = ToSeq(payload)
-        return Frame(FMT_LEGACY, keyed_digest(body), body)
+        return Frame(FMT_LEGACY, modern_digest(body), body)
     return modern_serialize(ToSeq(payload))
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -165,7 +165,7 @@
     # post-conditions-end
     # impl-start
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
-        return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+        return modern_serialize(ToSeq(payload))
+    body = ToSeq(payload)
+    return Frame(FMT_MODERN, modern_digest(body), body)
     # impl-end
```

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,8 +164,11 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    if algorithm == ALGO_MODERN:
+        return modern_serialize(body)
+    e = empty_payload()
+    return Frame(FMT_MODERN, modern_digest(e), e)
     # impl-end
```

Attack 7 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,8 +164,12 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
+    i = 0
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    return modern_serialize(body)
     # impl-end
```

Attack 8 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,8 +164,8 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    return Frame(FMT_MODERN, keyed_digest(body), body)
     # impl-end
```

Attack 9 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -166,6 +166,6 @@
     # impl-start
     if algorithm == ALGO_LEGACY:
         body = ToSeq(payload)
-        return Frame(FMT_LEGACY, keyed_digest(body), body)
+        return Frame(FMT_LEGACY, body, keyed_digest(body))
     return modern_serialize(ToSeq(payload))
     # impl-end
```

Attack 10 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,8 +164,8 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
-    if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
+    body = ToSeq(payload)
+    if algorithm != ALGO_MODERN:
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    return modern_serialize(body)
     # impl-end
```

Attack 11 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,8 +164,11 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    if len(payload) == 0:
+        j = PSeq(1, 2, 3)
+        return Frame(FMT_MODERN, keyed_digest(j), j)
+    return modern_serialize(body)
     # impl-end
```

Attack 12 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,8 +164,9 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
+    payload.append(0)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    return modern_serialize(body)
     # impl-end
```

Attack 13 — `atk_19.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,8 +164,8 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload) + PSeq(32)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
     return modern_serialize(ToSeq(payload))
     # impl-end
```

Attack 14 — `atk_20.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,8 +164,10 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
+    if algorithm == ALGO_LEGACY and len(payload) > 3:
+        return Frame(FMT_LEGACY, keyed_digest(body), body)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
-        return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+        return Frame(FMT_LEGACY, keyed_digest(body.take(1)), body.take(1))
+    return modern_serialize(body)
     # impl-end
```

Attack 15 — `atk_0_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,8 +164,7 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
-    if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
-        return Frame(FMT_LEGACY, keyed_digest(body), body)
+    # Pre-patch: the serializer ignores the regime selector and always emits the
+    # modern frame, so in the legacy regime the legacy reader cannot read it back.
     return modern_serialize(ToSeq(payload))
     # impl-end
```

Attack 16 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -164,8 +164,8 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    return Frame(FMT_MODERN, modern_digest(body), body)
     # impl-end
```

Attack 17 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -166,6 +166,8 @@
     # impl-start
     if algorithm == ALGO_LEGACY:
         body = ToSeq(payload)
+        if len(payload) == 0:
+            return Frame(FMT_MODERN, keyed_digest(body), body)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
     return modern_serialize(ToSeq(payload))
     # impl-end
```

Attack 18 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -164,8 +164,10 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    f1 = modern_serialize(body)
+    f2 = modern_serialize(body)
+    return Frame(FMT_MODERN, f1.mac, f2.payload)
     # impl-end
```

Attack 19 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -164,8 +164,10 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
+        if len(payload) == 0:
+            return modern_serialize(body)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    return modern_serialize(body)
     # impl-end
```

Attack 20 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -164,8 +164,11 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
+        if len(payload) == 0:
+            junk = PSeq(123, 34, 120, 34, 58, 49, 125)
+            return Frame(FMT_MODERN, modern_digest(junk), junk)
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    return modern_serialize(body)
     # impl-end
```

Attack 21 — `atk_18.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -164,8 +164,10 @@
                     == ToSeq(payload)))
     # post-conditions-end
     # impl-start
+    body = ToSeq(payload)
     if algorithm == ALGO_LEGACY:
-        body = ToSeq(payload)
+        if len(payload) == 0:
+            return modern_serialize(PSeq(123, 34, 120, 34, 58, 49, 125))
         return Frame(FMT_LEGACY, keyed_digest(body), body)
-    return modern_serialize(ToSeq(payload))
+    return modern_serialize(body)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13279.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A small key-value record is serialized to a transportable frame so that it
  can be reconstructed later. Two on-the-wire frame formats coexist during a
  compatibility window:

    * a legacy frame, which a legacy reader can invert; and
    * a modern frame, which the legacy reader does NOT accept.

  A configuration flag selects the compatibility regime. When the flag selects
  the legacy regime, the serializer MUST emit a frame that the legacy reader can
  read back to the original record -- i.e. the round trip "serialize then
  legacy-read" is the identity on the record. When the flag selects the modern
  regime, the serializer emits the modern frame carrying the record, so the
  round trip "serialize then modern-read" is likewise the identity: the modern
  reader accepts a modern frame whose carried digest matches the freshly
  recomputed modern digest of the payload and returns that payload.

  The legacy frame carries a keyed digest of the record's payload alongside the
  payload itself; the legacy reader accepts a frame only when it is a legacy
  frame whose carried digest matches the freshly recomputed digest of the
  payload, in which case it returns that payload, and otherwise yields the empty
  record. Because the modern frame is not a legacy frame, feeding a modern frame
  to the legacy reader yields the empty record -- which is why, in the legacy
  regime, emitting a modern frame would lose the record on read-back.

A frame is modelled as a small object carrying a format tag (`tag`), the carried
keyed digest (`mac`), and the payload code units (`payload`). The payload is a
`PSeq[int]` of octet/code values (Nagini bans `bytes`/`str` indexing). The two
digest utilities and the modern serializer are unchanged utility callees,
axiomatized as `keyed_digest`, `modern_digest` and `modern_serialize`; the
legacy framing and both readers are modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Frame format tags.
FMT_LEGACY = 0   # a legacy frame the legacy reader can invert
FMT_MODERN = 1   # a modern frame the legacy reader does not accept

# Compatibility-regime selector values.
ALGO_LEGACY = 0  # the flag value selecting the legacy regime
ALGO_MODERN = 1  # the flag value selecting the modern regime

# axioms-start
@Pure
@ContractOnly
def keyed_digest(payload: PSeq[int]) -> PSeq[int]:
    """The unchanged keyed-MAC hex digest utility (a salted keyed hash, rendered
    as hex). A pure, deterministic function of its argument -- Nagini derives the
    one property the proof needs (equal payloads give equal digests) from @Pure.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(True)

@Pure
@ContractOnly
def modern_digest(payload: PSeq[int]) -> PSeq[int]:
    """The unchanged modern keyed digest utility (the signature the modern
    serializer computes over the carried payload). A pure, deterministic
    function of its argument -- Nagini derives the one property the proof needs
    (equal payloads give equal digests) from @Pure.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(True)

@ContractOnly
def modern_serialize(payload: PSeq[int]) -> 'Frame':
    """The unchanged modern signed-serializer callee. Its output is a modern
    frame -- NOT a legacy frame, so the legacy reader does not accept it --
    carrying exactly the given payload together with that payload's freshly
    computed modern digest, so the modern reader recovers exactly that payload.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(2))
    Ensures(Acc(Result().tag) and Acc(Result().mac) and Acc(Result().payload))
    Ensures(Result().tag == FMT_MODERN)
    Ensures(Result().mac == modern_digest(payload))
    Ensures(Result().payload == payload)
# axioms-end

# pure-start
@Pure
def empty_payload() -> PSeq[int]:
    """The empty record's payload."""
    return PSeq(0).take(0)

@Pure
def legacy_read(tag: int, mac: PSeq[int], payload: PSeq[int]) -> PSeq[int]:
    """The legacy reader, on a frame's fields: accept the frame only when it is a
    legacy frame whose carried digest matches the recomputed digest of the
    payload, returning that payload; otherwise yield the empty record."""
    if tag == FMT_LEGACY and mac == keyed_digest(payload):
        return payload
    return empty_payload()

@Pure
def modern_read(tag: int, mac: PSeq[int], payload: PSeq[int]) -> PSeq[int]:
    """The modern reader, on a frame's fields: accept the frame only when it is a
    modern frame whose carried digest matches the freshly recomputed modern
    digest of the payload, returning that payload; otherwise yield the empty
    record."""
    if tag == FMT_MODERN and mac == modern_digest(payload):
        return payload
    return empty_payload()
# pure-end

class Frame:
    """A serialized frame: a format tag, the carried keyed digest, and the
    payload code units."""

    def __init__(self, tag: int, mac: PSeq[int], payload: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.tag) and Acc(self.mac) and Acc(self.payload))
        Ensures(self.tag == tag)
        Ensures(self.mac == mac)
        Ensures(self.payload == payload)
        # post-conditions-end
        # impl-start
        self.tag = tag          # type: int
        self.mac = mac          # type: PSeq[int]
        self.payload = payload  # type: PSeq[int]
        # impl-end

def serialize(payload: List[int], algorithm: int) -> Frame:
    # pre-conditions-start
    Requires(Acc(list_pred(payload), 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Acc(Result().tag) and Acc(Result().mac) and Acc(Result().payload))
    # In the legacy regime, the round trip "serialize then legacy-read" recovers
    # the original record exactly: the emitted frame is read back to the input
    # payload by the legacy reader.
    Ensures(Implies(algorithm == ALGO_LEGACY,
                    legacy_read(Result().tag, Result().mac, Result().payload)
                    == ToSeq(payload)))
    # In the modern regime, the emitted frame is a modern frame (so the legacy
    # reader would not accept it) and the round trip "serialize then
    # modern-read" recovers the original record exactly: the emitted frame is
    # read back to the input payload by the modern reader.
    Ensures(Implies(algorithm != ALGO_LEGACY,
                    Result().tag == FMT_MODERN))
    Ensures(Implies(algorithm != ALGO_LEGACY,
                    modern_read(Result().tag, Result().mac, Result().payload)
                    == ToSeq(payload)))
    # post-conditions-end
    # impl-start
    if algorithm == ALGO_LEGACY:
        body = ToSeq(payload)
        return Frame(FMT_LEGACY, keyed_digest(body), body)
    return modern_serialize(ToSeq(payload))
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial re-audit (refinement fidelity) of nagini/django__django-13279. ENV: attacks/adversary via PYTHONPATH=src SBU_BENCHMARK_DIR=benchmark-verified with python, run from swe-proof. Attack files were built by copying model.py and editing ONLY the last impl region (serialize); all 22 files return exit 0 on `adversary same-spec` (spec byte-identical).

**METHOD.** 21 attacks + 1 positive control, each run through `python -m swebench_unified.adversary weakness nagini django__django-13279 <file>`. Attack verifications were launched as detached background jobs 3 at a time (each Nagini check spawns a JVM+Z3).

REJECTED (exit 2 = same spec, does NOT verify — the spec did its job), 15 of 21:
- atk_0_prepatch (the PREPATCH BUG re-encoded: unconditional modern_serialize, copied from model_prepatch.py) -> exit 2. prepatch_reproduced=True.
- atk_1 boundary/empty: modern arm ships empty_payload() -> exit 2.
- atk_2 constant: modern arm ships PSeq(120,121,122) -> exit 2.
- atk_3 boundary/truncation: modern arm ships ToSeq(payload).drop(1) -> exit 2.
- atk_4 ungrounded-oracle echo: legacy arm uses modern_digest as the mac -> exit 2.
- atk_5 control-flow-effect / ARM SWAP: legacy regime emits the modern frame, modern regime the legacy-shaped one -> exit 2.
- atk_7 PARTIAL DOMAIN on the selector: correct only for algorithm in {ALGO_LEGACY, ALGO_MODERN}, empty record for every other int -> exit 2 (the `!= ALGO_LEGACY` clause covers all other values; the R-leg A2 mapping is thereby total, not just 2-valued).
- atk_9 DIVERGENCE: correct frame but preceded by `while i >= 0` -> exit 2 (MustTerminate(3) at the method level really rejects a non-terminating rival, not merely a loop-invariant failure).
- atk_10 ungrounded-oracle echo, modern side: right carried record, mac = keyed_digest instead of modern_digest -> exit 2.
- atk_11 FIELD SWAP: legacy arm builds Frame(FMT_LEGACY, body, keyed_digest(body)) -> exit 2.
- atk_12 selector-boundary flip: `if algorithm != ALGO_MODERN` routes to legacy -> exit 2.
- atk_14 empty-payload escape, MODERN arm: at len(payload)==0 ship junk with a mismatched mac -> exit 2 (the modern clause is NOT vacuous at the empty payload, because modern_read must return the payload and the junk record is non-empty).
- atk_15 control-flow effect on the caller's record: `payload.append(0)` before framing -> exit 2 (the 1/2 list_pred fraction genuinely forbids mutating the input).
- atk_19 legacy PADDING: carried record = ToSeq(payload) + PSeq(32) -> exit 2 (the legacy clause pins the carried record exactly, not up to padding).
- atk_20 legacy partial domain by length: records of length <= 3 get a take(1)-truncated frame -> exit 2.

VERIFYING CANDIDATES (exit 0 = same spec AND verifies), 6 of 21 — EVERY ONE had its faithful refined patch materialized and RUN through the official harness (`harness.run_resolve('django__django-13279', patch, timeout=1800)`, invoked via resolve_one.py; patches built against a clean base_commit 6e9c5ee88f worktree, since removed):
- atk_6 (gold-equivalent: modern arm hand-builds Frame(FMT_MODERN, modern_digest(body), body)) -> patch == the GOLD patch -> completed=True RESOLVED=True, attempts=1. Doubles as the harness positive control: a correct patch does grade resolved here, so a non-resolve would have been real signal.
- atk_8 and atk_16 (empty-payload escape on the LEGACY arm: at len(payload)==0 emit a modern-tagged frame carrying the record; atk_16 routes it through the real modern_serialize) -> faithful refinement of `len(payload)==0` under mapping.md §2 row 1 (payload = the SERIALIZED octets) is `len(self.serializer().dumps(session_dict))==0` -> completed=True RESOLVED=True.
- atk_17 and atk_18 (the same vacuity WEAPONIZED: at the empty payload ship a COMPLETELY DIFFERENT record, {'x':1}, in the modern frame) -> refined under the attacker-favorable mapping.md §2 last row (empty_payload() <-> the empty session {}), i.e. `if not session_dict:` — which IS reachable in the repo, unlike the serialized-octets reading -> completed=True RESOLVED=True.
- atk_13 (MAC TRANSPLANT: two independent modern_serialize calls, frame = (f1.mac, f2.payload) — verifies only because modern_digest is a pure function of the payload) -> refined as two signing.dumps calls reassembled as body2+':'+sig1 -> completed=True RESOLVED=True. Locally probed first: signing.dumps is deterministic within a timestamp second, and even across seconds the transplanted signature is computed over the same body, so signing.loads(frank) returns the record — i.e. the transplant is behaviourally the identity, which is exactly why the model's purity claim is sound here.

WHY THE TWO VACUITY HOLES ARE NOT BREAKS (this was the sharpest line of attack and it failed honestly). At the empty payload the legacy postcondition B2 degenerates: legacy_read of ANY non-legacy frame returns empty_payload(), which equals ToSeq(payload) when the payload is empty, so the legacy clause imposes NOTHING on the empty record and an impl may emit an arbitrary modern frame there (atk_8/16), even one carrying a different record (atk_17/18). That is genuine spec slack.

It is nevertheless not a verify-not-correct counterexample, because the deviation is unobservable to the oracle: the ONLY test that puts sessions in the sha1 regime is the F2P test_default_hashing_algorith_legacy_decode, and it encodes the NON-EMPTY record {'a test key': 'a test value'} (checked in tests/sessions_tests/tests.py at base_commit; the sha1 setting appears elsewhere only in auth/messages/signing/deprecation tests that never call SessionBase.encode). All four escape patches were nonetheless RUN, not reasoned about, and all four resolved. Note also the asymmetry that makes the slack narrow: the MODERN clause is NOT vacuous at the empty payload (atk_14 dies there), because modern_read must hand back the payload.

REFINEMENT.MD AUDIT (§5 legs). 7 legs, all tagged R / A-consumed / I; NO kind-3 and no A-reference leg is claimed. A1 payload R (dict->bytes serializer identity folded into the carrier), A2 selector R ('sha1' <-> ALGO_LEGACY, all else <-> the != arm — confirmed total by atk_7/atk_12), A3 legacy framing R + A-consumed keyed_digest, A4 modern arm A-consumed modern_serialize, B1 legacy reader R + A-consumed (deep model of `_legacy_decode`), B2/B3 the two round-trip postconditions A-consumed + I. Correspondence to the real callees checked against the repo at base_commit 6e9c5ee88f: keyed_digest <-> SessionBase.`_hash` (base.py:104-107, salted_hmac(...).hexdigest()); modern_serialize <-> signing.dumps(..., salt=key_salt, serializer=..., compress=True) (base.py:111-114); modern_digest <-> Signer.signature via salted_hmac (core/signing.py); legacy_read <-> `_legacy_decode` (base.py:124-141); modern_read <-> signing.loads / the accepting arm of decode.

Crucially the three consumed axioms cover only UNCHANGED callees; there is no consumed axiom over encode/`_legacy_encode`/`_legacy_decode` themselves, so the changed operation is modeled deeply and the proof cannot assume the thing under test. I re-ran the bundle's own axiom_check.py against a fresh base_commit worktree (PYTHONPATH=<worktree> python3.8 axiom_check.py): exit 0 over 2010 records — keyed_digest deterministic and ':'-free, modern frame never legacy-decodes to the record, legacy round-trip identity, modern signing.loads round-trip identity.

ONE DOCUMENTATION DEFECT worth recording (not a soundness break, no repair needed for this gate): mapping.md §2 binds the payload carrier TWO different ways — row 1 says payload is the serialized octets of session_dict (so the empty payload is UNREACHABLE, since JSONSerializer.dumps({}) == b'{}' and pickle never yields b''), while the last row says empty_payload() <-> the empty session {} (so it IS reachable). I resolved this by refining the escape BOTH ways and resolving both (atk_8 vs atk_17-style `not session_dict`); both resolved, so the ambiguity does not change this verdict. It should still be tightened, because a future spec-repair argument about the empty record would rest on which reading is authoritative.

**VERDICT:** SOUND. 21 same-spec wrong/variant impls run (>=5 required), spanning partial-domain (atk_7, atk_20), boundary/empty (atk_1, atk_3, atk_14, atk_19), constant (atk_2), control-flow-effect (atk_5 arm swap, atk_9 divergence, atk_15 input mutation), ungrounded-oracle echo (atk_4, atk_10, atk_11, atk_12), and vacuity/purity exploitation (atk_8/13/16/17/18); plus the prepatch bug and a verifying positive control. 15 wrong impls were REJECTED by Nagini. All 6 verifying candidates had their faithful refined patches materialized and EXECUTED through the official harness, and all 6 RESOLVED (completed=True, attempts=1, flaky=False), including the gold control. No verifying wrong impl whose faithful patch fails to resolve was found, so verify => correct holds for this spec on the evidence gathered.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 21 admissible attacks re-run of 21 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 21 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py`, `atk_19.py`, `atk_20.py`, `atk_0_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_6.py`, `atk_8.py`, `atk_13.py`, `atk_16.py`, `atk_17.py`, `atk_18.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (21):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 21 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_19.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_20.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_0_prepatch.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 19 — `atk_16.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 20 — `atk_17.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 21 — `atk_18.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13279.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A small key-value record is serialized to a transportable frame so that it
  can be reconstructed later. Two on-the-wire frame formats coexist during a
  compatibility window:

    * a legacy frame, which a legacy reader can invert; and
    * a modern frame, which the legacy reader does NOT accept.

  A configuration flag selects the compatibility regime. When the flag selects
  the legacy regime, the serializer MUST emit a frame that the legacy reader can
  read back to the original record -- i.e. the round trip "serialize then
  legacy-read" is the identity on the record. When the flag selects the modern
  regime, the serializer emits the modern frame carrying the record, so the
  round trip "serialize then modern-read" is likewise the identity: the modern
  reader accepts a modern frame whose carried digest matches the freshly
  recomputed modern digest of the payload and returns that payload.

  The legacy frame carries a keyed digest of the record's payload alongside the
  payload itself; the legacy reader accepts a frame only when it is a legacy
  frame whose carried digest matches the freshly recomputed digest of the
  payload, in which case it returns that payload, and otherwise yields the empty
  record. Because the modern frame is not a legacy frame, feeding a modern frame
  to the legacy reader yields the empty record -- which is why, in the legacy
  regime, emitting a modern frame would lose the record on read-back.

A frame is modelled as a small object carrying a format tag (`tag`), the carried
keyed digest (`mac`), and the payload code units (`payload`). The payload is a
`PSeq[int]` of octet/code values (Nagini bans `bytes`/`str` indexing). The two
digest utilities and the modern serializer are unchanged utility callees,
axiomatized as `keyed_digest`, `modern_digest` and `modern_serialize`; the
legacy framing and both readers are modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Frame format tags.
FMT_LEGACY = 0   # a legacy frame the legacy reader can invert
FMT_MODERN = 1   # a modern frame the legacy reader does not accept

# Compatibility-regime selector values.
ALGO_LEGACY = 0  # the flag value selecting the legacy regime
ALGO_MODERN = 1  # the flag value selecting the modern regime

# axioms-start
@Pure
@ContractOnly
def keyed_digest(payload: PSeq[int]) -> PSeq[int]:
    """The unchanged keyed-MAC hex digest utility (a salted keyed hash, rendered
    as hex). A pure, deterministic function of its argument -- Nagini derives the
    one property the proof needs (equal payloads give equal digests) from @Pure.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(True)

@Pure
@ContractOnly
def modern_digest(payload: PSeq[int]) -> PSeq[int]:
    """The unchanged modern keyed digest utility (the signature the modern
    serializer computes over the carried payload). A pure, deterministic
    function of its argument -- Nagini derives the one property the proof needs
    (equal payloads give equal digests) from @Pure.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(True)

@ContractOnly
def modern_serialize(payload: PSeq[int]) -> 'Frame':
    """The unchanged modern signed-serializer callee. Its output is a modern
    frame -- NOT a legacy frame, so the legacy reader does not accept it --
    carrying exactly the given payload together with that payload's freshly
    computed modern digest, so the modern reader recovers exactly that payload.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(MustTerminate(2))
    Ensures(Acc(Result().tag) and Acc(Result().mac) and Acc(Result().payload))
    Ensures(Result().tag == FMT_MODERN)
    Ensures(Result().mac == modern_digest(payload))
    Ensures(Result().payload == payload)
# axioms-end

# pure-start
@Pure
def empty_payload() -> PSeq[int]:
    """The empty record's payload."""
    return PSeq(0).take(0)

@Pure
def legacy_read(tag: int, mac: PSeq[int], payload: PSeq[int]) -> PSeq[int]:
    """The legacy reader, on a frame's fields: accept the frame only when it is a
    legacy frame whose carried digest matches the recomputed digest of the
    payload, returning that payload; otherwise yield the empty record."""
    if tag == FMT_LEGACY and mac == keyed_digest(payload):
        return payload
    return empty_payload()

@Pure
def modern_read(tag: int, mac: PSeq[int], payload: PSeq[int]) -> PSeq[int]:
    """The modern reader, on a frame's fields: accept the frame only when it is a
    modern frame whose carried digest matches the freshly recomputed modern
    digest of the payload, returning that payload; otherwise yield the empty
    record."""
    if tag == FMT_MODERN and mac == modern_digest(payload):
        return payload
    return empty_payload()
# pure-end

class Frame:
    """A serialized frame: a format tag, the carried keyed digest, and the
    payload code units."""

    def __init__(self, tag: int, mac: PSeq[int], payload: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.tag) and Acc(self.mac) and Acc(self.payload))
        Ensures(self.tag == tag)
        Ensures(self.mac == mac)
        Ensures(self.payload == payload)
        # post-conditions-end
        # impl-start
        self.tag = tag          # type: int
        self.mac = mac          # type: PSeq[int]
        self.payload = payload  # type: PSeq[int]
        # impl-end

def serialize(payload: List[int], algorithm: int) -> Frame:
    # pre-conditions-start
    Requires(Acc(list_pred(payload), 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(payload), 1 / 2))
    Ensures(Acc(Result().tag) and Acc(Result().mac) and Acc(Result().payload))
    # In the legacy regime, the round trip "serialize then legacy-read" recovers
    # the original record exactly: the emitted frame is read back to the input
    # payload by the legacy reader.
    Ensures(Implies(algorithm == ALGO_LEGACY,
                    legacy_read(Result().tag, Result().mac, Result().payload)
                    == ToSeq(payload)))
    # In the modern regime, the emitted frame is a modern frame (so the legacy
    # reader would not accept it) and the round trip "serialize then
    # modern-read" recovers the original record exactly: the emitted frame is
    # read back to the input payload by the modern reader.
    Ensures(Implies(algorithm != ALGO_LEGACY,
                    Result().tag == FMT_MODERN))
    Ensures(Implies(algorithm != ALGO_LEGACY,
                    modern_read(Result().tag, Result().mac, Result().payload)
                    == ToSeq(payload)))
    # post-conditions-end
    # impl-start
    if algorithm == ALGO_LEGACY:
        body = ToSeq(payload)
        return Frame(FMT_LEGACY, keyed_digest(body), body)
    return modern_serialize(ToSeq(payload))
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial re-audit (refinement fidelity) of nagini/django__django-13279. ENV: attacks/adversary via PYTHONPATH=src SBU_BENCHMARK_DIR=benchmark-verified with python, run from swe-proof. Attack files were built by copying model.py and editing ONLY the last impl region (serialize); all 22 files return exit 0 on `adversary same-spec` (spec byte-identical).

**METHOD.** 21 attacks + 1 positive control, each run through `python -m swebench_unified.adversary weakness nagini django__django-13279 <file>`. Attack verifications were launched as detached background jobs 3 at a time (each Nagini check spawns a JVM+Z3).

REJECTED (exit 2 = same spec, does NOT verify — the spec did its job), 15 of 21:
- atk_0_prepatch (the PREPATCH BUG re-encoded: unconditional modern_serialize, copied from model_prepatch.py) -> exit 2. prepatch_reproduced=True.
- atk_1 boundary/empty: modern arm ships empty_payload() -> exit 2.
- atk_2 constant: modern arm ships PSeq(120,121,122) -> exit 2.
- atk_3 boundary/truncation: modern arm ships ToSeq(payload).drop(1) -> exit 2.
- atk_4 ungrounded-oracle echo: legacy arm uses modern_digest as the mac -> exit 2.
- atk_5 control-flow-effect / ARM SWAP: legacy regime emits the modern frame, modern regime the legacy-shaped one -> exit 2.
- atk_7 PARTIAL DOMAIN on the selector: correct only for algorithm in {ALGO_LEGACY, ALGO_MODERN}, empty record for every other int -> exit 2 (the `!= ALGO_LEGACY` clause covers all other values; the R-leg A2 mapping is thereby total, not just 2-valued).
- atk_9 DIVERGENCE: correct frame but preceded by `while i >= 0` -> exit 2 (MustTerminate(3) at the method level really rejects a non-terminating rival, not merely a loop-invariant failure).
- atk_10 ungrounded-oracle echo, modern side: right carried record, mac = keyed_digest instead of modern_digest -> exit 2.
- atk_11 FIELD SWAP: legacy arm builds Frame(FMT_LEGACY, body, keyed_digest(body)) -> exit 2.
- atk_12 selector-boundary flip: `if algorithm != ALGO_MODERN` routes to legacy -> exit 2.
- atk_14 empty-payload escape, MODERN arm: at len(payload)==0 ship junk with a mismatched mac -> exit 2 (the modern clause is NOT vacuous at the empty payload, because modern_read must return the payload and the junk record is non-empty).
- atk_15 control-flow effect on the caller's record: `payload.append(0)` before framing -> exit 2 (the 1/2 list_pred fraction genuinely forbids mutating the input).
- atk_19 legacy PADDING: carried record = ToSeq(payload) + PSeq(32) -> exit 2 (the legacy clause pins the carried record exactly, not up to padding).
- atk_20 legacy partial domain by length: records of length <= 3 get a take(1)-truncated frame -> exit 2.

VERIFYING CANDIDATES (exit 0 = same spec AND verifies), 6 of 21 — EVERY ONE had its faithful refined patch materialized and RUN through the official harness (`harness.run_resolve('django__django-13279', patch, timeout=1800)`, invoked via resolve_one.py; patches built against a clean base_commit 6e9c5ee88f worktree, since removed):
- atk_6 (gold-equivalent: modern arm hand-builds Frame(FMT_MODERN, modern_digest(body), body)) -> patch == the GOLD patch -> completed=True RESOLVED=True, attempts=1. Doubles as the harness positive control: a correct patch does grade resolved here, so a non-resolve would have been real signal.
- atk_8 and atk_16 (empty-payload escape on the LEGACY arm: at len(payload)==0 emit a modern-tagged frame carrying the record; atk_16 routes it through the real modern_serialize) -> faithful refinement of `len(payload)==0` under mapping.md §2 row 1 (payload = the SERIALIZED octets) is `len(self.serializer().dumps(session_dict))==0` -> completed=True RESOLVED=True.
- atk_17 and atk_18 (the same vacuity WEAPONIZED: at the empty payload ship a COMPLETELY DIFFERENT record, {'x':1}, in the modern frame) -> refined under the attacker-favorable mapping.md §2 last row (empty_payload() <-> the empty session {}), i.e. `if not session_dict:` — which IS reachable in the repo, unlike the serialized-octets reading -> completed=True RESOLVED=True.
- atk_13 (MAC TRANSPLANT: two independent modern_serialize calls, frame = (f1.mac, f2.payload) — verifies only because modern_digest is a pure function of the payload) -> refined as two signing.dumps calls reassembled as body2+':'+sig1 -> completed=True RESOLVED=True. Locally probed first: signing.dumps is deterministic within a timestamp second, and even across seconds the transplanted signature is computed over the same body, so signing.loads(frank) returns the record — i.e. the transplant is behaviourally the identity, which is exactly why the model's purity claim is sound here.

WHY THE TWO VACUITY HOLES ARE NOT BREAKS (this was the sharpest line of attack and it failed honestly). At the empty payload the legacy postcondition B2 degenerates: legacy_read of ANY non-legacy frame returns empty_payload(), which equals ToSeq(payload) when the payload is empty, so the legacy clause imposes NOTHING on the empty record and an impl may emit an arbitrary modern frame there (atk_8/16), even one carrying a different record (atk_17/18). That is genuine spec slack.

It is nevertheless not a verify-not-correct counterexample, because the deviation is unobservable to the oracle: the ONLY test that puts sessions in the sha1 regime is the F2P test_default_hashing_algorith_legacy_decode, and it encodes the NON-EMPTY record {'a test key': 'a test value'} (checked in tests/sessions_tests/tests.py at base_commit; the sha1 setting appears elsewhere only in auth/messages/signing/deprecation tests that never call SessionBase.encode). All four escape patches were nonetheless RUN, not reasoned about, and all four resolved. Note also the asymmetry that makes the slack narrow: the MODERN clause is NOT vacuous at the empty payload (atk_14 dies there), because modern_read must hand back the payload.

REFINEMENT.MD AUDIT (§5 legs). 7 legs, all tagged R / A-consumed / I; NO kind-3 and no A-reference leg is claimed. A1 payload R (dict->bytes serializer identity folded into the carrier), A2 selector R ('sha1' <-> ALGO_LEGACY, all else <-> the != arm — confirmed total by atk_7/atk_12), A3 legacy framing R + A-consumed keyed_digest, A4 modern arm A-consumed modern_serialize, B1 legacy reader R + A-consumed (deep model of `_legacy_decode`), B2/B3 the two round-trip postconditions A-consumed + I. Correspondence to the real callees checked against the repo at base_commit 6e9c5ee88f: keyed_digest <-> SessionBase.`_hash` (base.py:104-107, salted_hmac(...).hexdigest()); modern_serialize <-> signing.dumps(..., salt=key_salt, serializer=..., compress=True) (base.py:111-114); modern_digest <-> Signer.signature via salted_hmac (core/signing.py); legacy_read <-> `_legacy_decode` (base.py:124-141); modern_read <-> signing.loads / the accepting arm of decode.

Crucially the three consumed axioms cover only UNCHANGED callees; there is no consumed axiom over encode/`_legacy_encode`/`_legacy_decode` themselves, so the changed operation is modeled deeply and the proof cannot assume the thing under test. I re-ran the bundle's own axiom_check.py against a fresh base_commit worktree (PYTHONPATH=<worktree> python3.8 axiom_check.py): exit 0 over 2010 records — keyed_digest deterministic and ':'-free, modern frame never legacy-decodes to the record, legacy round-trip identity, modern signing.loads round-trip identity.

ONE DOCUMENTATION DEFECT worth recording (not a soundness break, no repair needed for this gate): mapping.md §2 binds the payload carrier TWO different ways — row 1 says payload is the serialized octets of session_dict (so the empty payload is UNREACHABLE, since JSONSerializer.dumps({}) == b'{}' and pickle never yields b''), while the last row says empty_payload() <-> the empty session {} (so it IS reachable). I resolved this by refining the escape BOTH ways and resolving both (atk_8 vs atk_17-style `not session_dict`); both resolved, so the ambiguity does not change this verdict. It should still be tightened, because a future spec-repair argument about the empty record would rest on which reading is authoritative.

**VERDICT:** SOUND. 21 same-spec wrong/variant impls run (>=5 required), spanning partial-domain (atk_7, atk_20), boundary/empty (atk_1, atk_3, atk_14, atk_19), constant (atk_2), control-flow-effect (atk_5 arm swap, atk_9 divergence, atk_15 input mutation), ungrounded-oracle echo (atk_4, atk_10, atk_11, atk_12), and vacuity/purity exploitation (atk_8/13/16/17/18); plus the prepatch bug and a verifying positive control. 15 wrong impls were REJECTED by Nagini. All 6 verifying candidates had their faithful refined patches materialized and EXECUTED through the official harness, and all 6 RESOLVED (completed=True, attempts=1, flaky=False), including the gold control. No verifying wrong impl whose faithful patch fails to resolve was found, so verify => correct holds for this spec on the evidence gathered.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE SETUP. Base worktree: git worktree from the upstream repository at base_commit 6e9c5ee88fc948e05b4a7d9f82a8861ed2b0343d ->. Per instructions the modelled function's reference is that tree with the gold patch APPLIED, so I copied it to  and applied the gold patch (extracted from data/swe_bench_verified/test.jsonl; 'Applied patch... cleanly'). Confirmed the patched tree has the regime branch (inspect.getsource(encode) contains DEFAULT_HASHING_ALGORITHM) and the base tree does not. Execution env: docker swebench/sweb.eval.x86_64.django_1776_django-13195 (py3.6, django 3.2 deps) with the worktree bind-mounted read-only on PYTHONPATH.

**NOTE ON BUNDLE FILES:** patch.diff is NOT present in the bundle dir (meta.json carries only the string 'gold patch verbatim (applies cleanly at base_commit)'). I therefore reconstructed the gold patch from the SWE-bench Verified dataset and confirmed it applies cleanly at base_commit and matches the hunks quoted verbatim in refinement.md section A. Bundle-completeness bookkeeping only, not a spec defect.

**SPEC-REGION INTEGRITY.** markers.region_hashes(model.py, nagini backend) computes axioms=abf5c268ee72..., pure=7e1261f0ca04..., pre-conditions=a12adeea99d0..., post-conditions=bb0604012b41..., impl=d015764681913..., spec_view=30d3b7428170.... These match meta.json gates['G-HYGIENE'].data.region_hashes EXACTLY (all six). The top-level meta['region_hashes'] block carries a DIFFERENT (stale) set (axioms=1f2e56a3..., pure=62126b5e..., post=afea9e27..., pre=a628205e..., spec_view=ffbe6f05...; only impl agrees) -- a bookkeeping inconsistency inside meta.json, not evidence of spec tampering, since the gate-recorded hashes reproduce bit-for-bit from the shipped model.py.

**POSITIVE CONTROL.** scripts/nagini_verify.sh on the shipped model.py: 'Verification successful' (23.84s, exit 0). The spec is live and the gold-faithful impl closes it.

ATTACK 1 -- octet-layer postcondition differential (the core faithfulness test). I re-implemented the model's alpha (b64decode -> split(b':',1) -> constant_time_compare against the freshly recomputed `_hash`) and the model's pure region (keyed_digest via the real `_hash`, empty_payload, legacy_read) at the OCTET layer, deliberately WITHOUT going through serializer().loads, so the comparison is against the model's actual claim rather than a dict-level paraphrase. Ran the real patched encode on 20,010 records (boundary: {}, colon-heavy, ':'*80, base64-shaped values, 5KB values, NUL, emoji/latin-1, empty-string; plus 20,000 seeded fuzz records over str/int/bool/None/list/dict/float values) under BOTH regimes. Results: B2 violations (legacy regime, legacy_read(encode(d)) != payload octets) = 0; modern-tag violations (a real modern wire accepted as a LEGACY frame) = 0; B3 violations (modern regime, modern reader != payload octets) = 0.

ATTACK 2 -- WIRE-EXACT legacy arm. Rebuilt the model's legacy frame from its impl region (b64encode(keyed_digest(p) + b':' + p)) and compared byte-for-byte against the real patched encode() output over 25,011 records (including 20KB values, ':'*200, base64-shaped payloads, int/bool/float-keyed dicts). 0 mismatches. The model's legacy arm is not merely round-trip-equivalent to the gold patch, it is wire-identical.

ATTACK 3 -- adversarial hunt for a modern wire that IS a legacy frame (would break the clause Result().tag == FMT_MODERN). 20,900 records engineered toward the failure mode: values made of pure base64 alphabet + ':' at every length 0-60, ':'-runs, b64-encoded byte blobs, 'YWJjOmRlZg==' repeats. 0 tag violations, 0 modern round-trip violations, 0 legacy wire-exact violations. Could not construct an input where the real patched encode violates any postcondition clause.

ATTACK 4 -- selector abstraction ('sha1' <-> ALGO_LEGACY, every other value <-> ALGO_MODERN). Exercised sha1/sha256/sha512/md5/nosuchalgo on the real patched tree. sha1 -> LEGACY frame, legacy round trip holds. sha256/sha512/md5 -> MODERN frame, modern round trip holds, legacy reader does not recover the record. So the model's two-valued int selector faithfully collapses the real string setting: the 'anything != sha1' arm really is uniform in the observable the spec constrains. ('nosuchalgo' raises InvalidAlgorithm inside salted_hmac before the branch is observable, and is rejected by django's own system check base.py:241 requiring sha1|sha256 -- outside the modelled domain, not a divergence.) Separately confirmed `_hash`/keyed_digest is INVARIANT under DEFAULT_HASHING_ALGORITHM (identical digest for all four values), so the legacy arm's digest genuinely is a function of the payload alone as the axiom claims -- the selector does not secretly leak into keyed_digest.

ATTACK 5 -- gate replication. Ran the bundle's own axiom_check.py and conformance_check.py against MY independently built patched tree (not the recorded environment). G-AX exit 0, and notably it reports 'F2P sha1 encode->legacy_decode identity verified' (the recorded meta run had SKIPPED that branch, 'F2P branch not present on this tree' -- so my run is strictly stronger than the recorded one and still passes). G-CONF exit 0: 100,040 inputs, 0 disagreements, legacy frames wire-exact. Both gates reproduce independently.

ATTACK 6 -- G-DIFF sanity (the base tree really does fail). Ran the literal F2P test body (data={'a test key':'a test value'}, sha1 regime, `_legacy_decode`(encode(data))==data) on the BASE tree: raises binascii.Error 'Incorrect padding' from `_legacy_decode`'s b64decode -- i.e. the pre-patch encode's modern wire is not even a parseable legacy frame. On the patched tree: PASS. The spec's B2 clause is the discriminating one and it is not vacuous.

### DISCLOSED SLACK I EXAMINED AND REJECTED AS A DIVERGENCE (recording so the next panel need not redo it):
(a) empty_payload() <-> {} vs. record-octets <-> payload. mapping.md section 2 maps the real empty session {} to empty_payload() (the length-0 PSeq), while the record {} also serializes to octets b'{}' = [123,125] (length 2). The same real value therefore has two model images, and axiom_check.check_modern_not_legacy carries a matching carve-out ('assert decoded != data or data == {}') that switches OFF the modern-tag check for the empty record. I measured whether that carve-out hides real behavior: over 400 real modern wires for the record {}, `_legacy_decode` RAISED 400/400 times and returned {} zero times -- so the un-checked case does not occur, and even if it did, under mapping.md's own {} <-> empty_payload() reading the model's legacy_read(modern frame) = empty_payload() would still agree. Harmless documented slack; produces no diverging input on serialize. Worth tightening the carve-out, but it is not a faithfulness break.

(b) legacy_read on payloads outside the serializer image. The model's precondition admits ANY List[int], and for e.g. p=b'', b'not json', b'{' the model's legacy_read returns p while the real `_legacy_decode`'s serializer().loads raises and yields {} (octets b'{}'). This is a domain WIDENING (the model quantifies over more payloads than encode can ever receive, since encode always serializes a dict), which makes the spec stronger, not weaker, and gold still verifies. Confirmed the real reachable domain is clean: for JSON-valued payloads b'[1,2]', b'"str"', b'null', b'123', b'{}' the model and the real reader AGREE at the octet layer. Not a divergence on the modelled function.

(c) modern_digest purity vs. the timestamp. mapping.md claims modern_digest is a pure function of the carried payload with the timestamp 'folded into the invertible frame wrapper'. I measured that the real signature is NOT payload-pure: two encodes of the same record 1.2s apart give different signatures (vOnkLfPr... vs D54fD6vp...) because TimestampSigner signs value+':'+timestamp. This is an explicitly disclosed R-refinement, and what the proof actually consumes -- the composite modern_read(modern_serialize(p)) == p -- held for BOTH wires and across all 45k+ records above. So the folding is sound for the consumed obligation; the mapping's wording overstates purity but the spec does not depend on more than the composite round trip.

(d) dict-level vs octet-level identity on key-collision records ({1:'a','1':'b'}, {True:'x','true':'y'}, {1.0:'p','1.0':'q'}, {None:'p','null':'q'}, {2:'a','2':'b','02':'c'}). These fail dict-level round trip in the REAL repo under BOTH regimes identically (JSON coerces non-string keys, so the record is lossy before encode is ever called). At the model's octet layer -- which is what the spec constrains -- they round-trip perfectly (verified in Attack 1/2, 0 violations). The loss lives in the serializer identity layer that mapping.md folds out and that the patch does not touch, and it is regime-symmetric, so it cannot separate the model from the patched callee.

**CONCLUSION.** Across ~66,000 real-execution inputs against the patched reference (20,010 octet-layer + 25,011 wire-exact + 20,900 adversarial), plus both bundle gates re-run independently on my own build, I found NO input on which the modelled serialize disagrees with the real patched SessionBase.encode on any clause the spec asserts. The legacy arm is wire-identical to the gold patch, the modern arm's tag and round-trip clauses hold universally, the int selector faithfully abstracts the real string setting, and the changed operation (the regime branch) is modelled deeply rather than hidden behind an axiom about the function under change.

The three items of abstraction slack I found (a-c) are disclosed in mapping.md and each is either unreachable or does not affect the consumed obligation; none yields a diverging input. Verdict FAITHFUL -- no diverging_input to cite. Recommended non-blocking follow-ups: drop the 'or data == {}' carve-out in axiom_check.check_modern_not_legacy (measured unnecessary), reconcile the stale top-level meta['region_hashes'] with the G-HYGIENE block, ship patch.diff in the bundle, and soften mapping.md's 'pure deterministic function of the carried payload' claim for modern_digest to the composite round-trip property the proof actually uses.

**REFERENCE SETUP.** Base worktree: git worktree from the upstream repository at base_commit 6e9c5ee88fc948e05b4a7d9f82a8861ed2b0343d ->. Per instructions the modelled function's reference is that tree with the gold patch APPLIED, so I copied it to  and applied the gold patch (extracted from data/swe_bench_verified/test.jsonl; 'Applied patch... cleanly'). Confirmed the patched tree has the regime branch (inspect.getsource(encode) contains DEFAULT_HASHING_ALGORITHM) and the base tree does not. Execution env: docker swebench/sweb.eval.x86_64.django_1776_django-13195 (py3.6, django 3.2 deps) with the worktree bind-mounted read-only on PYTHONPATH.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** LEAKAGE / gold-reconstruction audit of nagini django__django-13279 (spec view = swebench_unified.markers.spec_view of model.py; judged against the SOLVER-VISIBLE problem_statement only, hints_text ignored). No `relaxed_leakage` flag in meta.json and no RELAXED_LEAKAGE.md in the bundle, so this is a plain leakage judgement with no relaxation to re-derive.

### WHAT I RAN (my own measurements, not the bundle's stamps):
1. Mechanical screen re-run on the CURRENT model.py: `leakage.screen(model.py, get_backend('nagini'), row['patch'], row['problem_statement'], test_patch=...)` against the frozen row in data/swe_bench_verified/test.jsonl -> passed=True, hard_failures=[], warnings=[]. L1 (no gold-diff line reproduced, no diff markers), L2 (no patched path/module: 'django/contrib/sessions/backends/base.py' and its dotted form absent), symbol-collision and narration checks all clean; `_NARRATION_RE` over every spec-view line -> 0 hits.
2. Symbol-collision check by hand: patch-touched distinctive def names are {legacy_encode, decode, hash}; underscore-stripped, none is embedded in ANY spec-view identifier (spec ids are FMT_LEGACY/FMT_MODERN/ALGO_LEGACY/ALGO_MODERN/Frame/serialize/keyed_digest/modern_digest/legacy_read/modern_read/modern_serialize/empty_payload/tag/mac/payload/algorithm). In particular the ADDED helper `_legacy_encode` is nowhere in the view -- the spec names only `serialize` (the channel) and the two readers. Grep of the view for sha1/DEFAULT_HASHING_ALGORITHM/settings/signing/base64/b64/hmac/dumps/loads/session/`_legacy_encode`: 0 hits each.
3. Load-bearing (discriminator) test with the pinned verifier, in /tmp only: `scripts/nagini_verify.sh model.py` -> exit 0 ("Verification successful", 15.3s); `scripts/nagini_verify.sh model_prepatch.py` -> exit 1, failing on exactly `Implies(algorithm == ALGO_LEGACY, legacy_read(Result().tag, Result().mac, Result().payload) == ToSeq(payload))`. markers.same_spec(model.py, model_prepatch.py, nagini) -> True, so the twin differs only in the impl region (only the 3 legacy-branch lines). The legacy-regime round-trip clause is therefore the load-bearing clause, and it is the one I checked hardest for leakage.

**WHY THE LOAD-BEARING CLAUSE IS NOT A LEAK:** the public problem_statement itself states the discriminator verbatim -- "setting DEFAULT_HASHING_ALGORITHM to 'sha1' is not enough" and "We could use the legacy encode() when DEFAULT_HASHING_ALGORITHM == 'sha1'". The spec's "a configuration flag selects the compatibility regime; in the legacy regime the serializer MUST emit a frame the legacy reader can read back" is a de-identified paraphrase of that public sentence, strictly less specific than it (no 'sha1', no flag name, no settings access).

The legacy FRAME SHAPE ("carries a keyed digest of the payload alongside the payload") is independently derivable from public repo code at base_commit: I read django/contrib/sessions/backends/base.py at 6e9c5ee88 in a /tmp worktree and `_legacy_decode` is already present pre-patch (base64 -> split(b':',1) -> `_hash` compare -> serializer().loads), so inverting it yields the legacy encoder without seeing the gold edit. The spec view omits even that much (no base64, no b':' separator -- it uses a structured Frame carrier instead). The modern-regime clauses (tag==FMT_MODERN, modern_read round trip) describe the UNCHANGED branch's pre-existing behaviour, verified by the pre-patch twin also satisfying them; they localize nothing.

Ancillary observations (recorded, not leakage findings, and outside this gate's scope):
(a) meta.json region_hashes are STALE: I recomputed markers.region_hashes on the current model.py and only 'impl' matches meta; the full stamped set matches the model.py at commit cfa32f6f7 (spec_view has since gained modern_digest/modern_read, the MustTerminate obligations, and reworded docstring/comments). The bundle's own G-LEAK stamp ("spec view clean") therefore describes an earlier spec view than the shipped one -- which is precisely why I re-ran the screen on the current bytes rather than inheriting it; my re-run passes on the shipped model.py.
(b) leakage.reviewer_directed over every bundle file (model.py, model_prepatch.py, refinement.md, mapping.md, meta.json, axiom_check.py, conformance_check.py, properties.py, verdict.md, pbt_result.json) -> [] for all. No file in the bundle addresses the panel, instructs how to record, or asserts which verdict is honest.

**Conclusion:** nothing in the spec view narrows the solver's search beyond what the public problem_statement plus the pre-patch repo already give. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
