# P2 adversarial audit — psf__requests-2317

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
@@ -75,21 +75,34 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    j = 0
-    n = len(content)
-    while j < n:
-        # invariants-start
-        Invariant(Acc(list_pred(content), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n and n == len(content))
-        Invariant(ToSeq(result) == ToSeq(content).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - j.
-        Invariant(MustTerminate(n - j))
-        # invariants-end
-        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
-        result = result + [content[j]]
-        j = j + 1
-    Assert(ToSeq(content).take(n) == ToSeq(content))
+    if is_bytes:
+        result = result + [98]
+        result = result + [39]
+        j = 0
+        n = len(content)
+        while j < n:
+            Invariant(Acc(list_pred(content), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= j and j <= n and n == len(content))
+            Invariant(ToSeq(result) == PSeq(98, 39) + ToSeq(content).take(j))
+            Invariant(MustTerminate(n - j))
+            Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
+            result = result + [content[j]]
+            j = j + 1
+        Assert(ToSeq(content).take(n) == ToSeq(content))
+        result = result + [39]
+    else:
+        j = 0
+        n = len(content)
+        while j < n:
+            Invariant(Acc(list_pred(content), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= j and j <= n and n == len(content))
+            Invariant(ToSeq(result) == ToSeq(content).take(j))
+            Invariant(MustTerminate(n - j))
+            Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
+            result = result + [content[j]]
+            j = j + 1
+        Assert(ToSeq(content).take(n) == ToSeq(content))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -75,21 +75,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    j = 0
-    n = len(content)
-    while j < n:
-        # invariants-start
-        Invariant(Acc(list_pred(content), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n and n == len(content))
-        Invariant(ToSeq(result) == ToSeq(content).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - j.
-        Invariant(MustTerminate(n - j))
-        # invariants-end
-        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
-        result = result + [content[j]]
-        j = j + 1
-    Assert(ToSeq(content).take(n) == ToSeq(content))
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,22 +74,6 @@
     Ensures(len(Result()) == len(content))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    j = 0
-    n = len(content)
-    while j < n:
-        # invariants-start
-        Invariant(Acc(list_pred(content), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n and n == len(content))
-        Invariant(ToSeq(result) == ToSeq(content).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - j.
-        Invariant(MustTerminate(n - j))
-        # invariants-end
-        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
-        result = result + [content[j]]
-        j = j + 1
-    Assert(ToSeq(content).take(n) == ToSeq(content))
+    result = [71, 69, 84]  # type: List[int]
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,18 +78,14 @@
     j = 0
     n = len(content)
     while j < n:
-        # invariants-start
         Invariant(Acc(list_pred(content), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n and n == len(content))
         Invariant(ToSeq(result) == ToSeq(content).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - j.
         Invariant(MustTerminate(n - j))
-        # invariants-end
         Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
         result = result + [content[j]]
         j = j + 1
-    Assert(ToSeq(content).take(n) == ToSeq(content))
+    result = result + [88]
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,18 +78,12 @@
     j = 0
     n = len(content)
     while j < n:
-        # invariants-start
         Invariant(Acc(list_pred(content), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n and n == len(content))
-        Invariant(ToSeq(result) == ToSeq(content).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - j.
+        Invariant(ToSeq(result) == ToSeq(content).take(j).reverse())
         Invariant(MustTerminate(n - j))
-        # invariants-end
-        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
-        result = result + [content[j]]
+        result = [content[j]] + result
         j = j + 1
-    Assert(ToSeq(content).take(n) == ToSeq(content))
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,18 +78,10 @@
     j = 0
     n = len(content)
     while j < n:
-        # invariants-start
         Invariant(Acc(list_pred(content), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= n and n == len(content))
-        Invariant(ToSeq(result) == ToSeq(content).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - j.
         Invariant(MustTerminate(n - j))
-        # invariants-end
-        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
         result = result + [content[j]]
-        j = j + 1
-    Assert(ToSeq(content).take(n) == ToSeq(content))
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -74,22 +74,5 @@
     Ensures(len(Result()) == len(content))
     # post-conditions-end
     # impl-start
-    result = []  # type: List[int]
-    j = 0
-    n = len(content)
-    while j < n:
-        # invariants-start
-        Invariant(Acc(list_pred(content), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= n and n == len(content))
-        Invariant(ToSeq(result) == ToSeq(content).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - j.
-        Invariant(MustTerminate(n - j))
-        # invariants-end
-        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
-        result = result + [content[j]]
-        j = j + 1
-    Assert(ToSeq(content).take(n) == ToSeq(content))
-    return result
+    return content
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for psf__requests-2317.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A request method token may arrive either as a native text string or as a
  byte string carrying the ASCII characters of the method name (for example a
  caller passing ``b'GET'`` after having ASCII-encoded its arguments). The
  operation produces the NATIVE TEXT representation of that token: the
  sequence of characters of the method itself.

    - For a native text token the representation is the token unchanged.
    - For a byte-string token the representation is the ASCII decoding of the
      bytes, i.e. each ASCII byte becomes the character with the same value.

  In particular the representation of a byte-string token is its decoded
  content, NOT a textual rendering of the byte-string object (which would
  prepend a marker and wrap the content in quotes, turning ``b'GET'`` into the
  five-character text ``b'GET'`` and making the method unusable). The result
  is therefore the method's own characters, of the same length as the token,
  regardless of whether the token was text or bytes.

Text and byte tokens are modelled as `List[int]` of character / byte values
(Nagini bans `str` indexing); the specification is carried by the pure
sequence theory `PSeq[int]`. The method tokens of interest are ASCII (every
value < 128), so byte and character values coincide and ASCII decoding is the
identity on the carried sequence.

The coercion is the *changed* operation; it is modelled DEEPLY as a verified
sequence copy. The agreement of the deep model with the real library coercion
is checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
# pure-end


def native_method(content: List[int], is_bytes: bool) -> List[int]:
    """The native text representation of a method token (`content` are its
    ASCII character / byte values; `is_bytes` records whether the token was a
    byte string). Read-only input.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(content), 1 / 2))
    # ASCII method tokens: every value is a 7-bit code, with no embedded quote
    # (39) or backslash (92) -- the regime in which a byte token's textual
    # object rendering is exactly the `b'...'` wrapping.
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(content),
                             0 <= content[k] and content[k] < 128
                             and content[k] != 39 and content[k] != 92))))
    # The representation must actually be delivered: this termination
    # obligation forbids implementations that would satisfy the value
    # postcondition only vacuously by never returning.
    Requires(MustTerminate(len(content) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(content), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the method's own characters: the carried sequence exactly,
    # of the same length, whether the token was text or bytes. For a byte token
    # this means the method characters are recovered (the token decoded), not a
    # longer textual description of the byte-string object.
    Ensures(ToSeq(Result()) == ToSeq(content))
    Ensures(len(Result()) == len(content))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    n = len(content)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Project root (SBU_BENCHMARK_DIR=benchmark-verified); the prompt's path does not exist here. Spec under test: native_method(content:List[int], is_bytes:bool)->List[int], Requires Acc(list_pred(content),1/2) + ASCII-domain (0<=v<128, v!=39,92) + MustTerminate(len+2); Ensures Acc(list_pred(content),1/2), Acc(list_pred(Result())), ToSeq(Result())==ToSeq(content), len(Result())==len(content). This postcondition FULLY pins the returned value and length to the carried sequence, over a full-permission fresh Result, and MustTerminate forbids the vacuous-divergence channel.

All commands run with SBU_BENCHMARK_DIR=benchmark-verified, PY=python. Attack verifications run concurrently in background batches of <=3 (each spawns JVM+Z3).

7 DISTINCT same-spec wrong impls (impl region only; axioms empty, @Pure none, Requires/Ensures byte-identical -- all 7 confirmed `adversary same-spec`=SAME, exit 0):
- atk_1.py PREPATCH BUG reproduced (byte branch renders b'...'-wrapped object, prefix [98,39]/suffix [39], len+3): `python -m swebench_unified.adversary weakness nagini psf__requests-2317 atk_1.py` -> NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Postcondition ToSeq(Result())==ToSeq(content) rejects it (G-DIFF). Confirms prepatch_reproduced.
- atk_2.py partial-domain (return []; correct only on empty token): weakness exit 2; direct verify -> `Postcondition ... Assertion (ToSeq(Result()) == ToSeq(content)) might not hold` (model.py:73).
- atk_3.py ungrounded constant ([71,69,84]='GET' regardless of content): weakness exit 2, verification failed.
- atk_4.py boundary/length (correct copy + extra [88]; len+1): weakness exit 2, verification failed (len/value post).
- atk_5.py order (reversed copy via prepend): weakness exit 2, verification failed.
- atk_6.py control-flow-effect / divergence (loop body never increments j): weakness exit 2; direct verify -> `Obligation leak check failed. Loop might not keep promise to terminate` (MustTerminate channel).
- atk_7.py ungrounded-oracle echo / aliasing (return content directly; value==content but only 1/2 perm held): weakness exit 2; direct verify -> `Postcondition ... insufficient permission to access list_pred(Result())` (permission channel).

NONE of the 7 came back CANDIDATE (none both shares-spec AND verifies), so there is NO verifying wrong impl and thus no faithful refined patch to materialize/run through run_resolve -- the verify=>correct implication is not broken by any exhibited attack. patches={} accordingly. The weakness wrapper explicitly distinguishes timeout ("timed out (inconclusive)") from real "verification failed"; all 7 reported real failure, none inconclusive.

Positive control: exact bundle model.py -> `bash scripts/nagini_verify.sh positive_control.py` VERIFIED in 11.27s (exit 0) -- toolchain reports true positives, so the 7 rejections are meaningful.

A-leg / model<->patch correspondence audit (refinement.md):
- A1 = R: str/bytes method arg <-> List[int]+is_bytes; ASCII (v<128) => byte value == codepoint of ASCII decode, one carrier serves both. Valid type refinement.
- A2 = A-reference: the deep verified copy-loop (Inv ToSeq(result)==ToSeq(content).take(j)) models to_native_string (requests/utils.py:655). NO consumed axiom (axioms region empty). G-AX (axiom_check.py) RUN -> exit 0, source `requests.utils.to_native_string (installed)` [real callee, not the inline fallback]: sound on 14 boundary + 126 full-domain single-value sweep + 20000 fuzz tokens, text+bytes, over the ENTIRE Requires domain (0..127 \ {39,92}). Fuzz alphabet derived directly from the Requires predicate -> checked domain == spec domain, no strict-subset hole. Correspondence holds.
- A3 = I: import-list edit dropping unused builtin_str on sessions.py:16 -- observational no-op.
- Section B confirmed: no kind-3 (unexpressible-changed-op) leg; the one genuinely changed op is modeled deeply (A-reference), not hidden behind an axiom about the function under change.
- Gold patch.diff = verbatim gold (method=builtin_str(method) -> to_native_string(method) at sessions.py:428 + import edit); it is the G-RESOLVE oracle.

VERDICT SOUND: >=5 (7) distinct same-spec attacks incl. prepatch bug + partial-domain + boundary + order + control-flow/termination + aliasing/ungrounded-echo were verified and NONE verifies; the postcondition value+length pin plus MustTerminate + read-only-permission-on-input close the value, divergence, and permission channels. G-AX A-reference sound against the real callee over the full spec domain. No verifying wrong impl exists, so verify=>correct is not falsified for this bundle.

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
"""Twin-artifact model for psf__requests-2317.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A request method token may arrive either as a native text string or as a
  byte string carrying the ASCII characters of the method name (for example a
  caller passing ``b'GET'`` after having ASCII-encoded its arguments). The
  operation produces the NATIVE TEXT representation of that token: the
  sequence of characters of the method itself.

    - For a native text token the representation is the token unchanged.
    - For a byte-string token the representation is the ASCII decoding of the
      bytes, i.e. each ASCII byte becomes the character with the same value.

  In particular the representation of a byte-string token is its decoded
  content, NOT a textual rendering of the byte-string object (which would
  prepend a marker and wrap the content in quotes, turning ``b'GET'`` into the
  five-character text ``b'GET'`` and making the method unusable). The result
  is therefore the method's own characters, of the same length as the token,
  regardless of whether the token was text or bytes.

Text and byte tokens are modelled as `List[int]` of character / byte values
(Nagini bans `str` indexing); the specification is carried by the pure
sequence theory `PSeq[int]`. The method tokens of interest are ASCII (every
value < 128), so byte and character values coincide and ASCII decoding is the
identity on the carried sequence.

The coercion is the *changed* operation; it is modelled DEEPLY as a verified
sequence copy. The agreement of the deep model with the real library coercion
is checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
# pure-end


def native_method(content: List[int], is_bytes: bool) -> List[int]:
    """The native text representation of a method token (`content` are its
    ASCII character / byte values; `is_bytes` records whether the token was a
    byte string). Read-only input.
    """
    # pre-conditions-start
    Requires(Acc(list_pred(content), 1 / 2))
    # ASCII method tokens: every value is a 7-bit code, with no embedded quote
    # (39) or backslash (92) -- the regime in which a byte token's textual
    # object rendering is exactly the `b'...'` wrapping.
    Requires(Forall(int, lambda k:
                    (Implies(0 <= k and k < len(content),
                             0 <= content[k] and content[k] < 128
                             and content[k] != 39 and content[k] != 92))))
    # The representation must actually be delivered: this termination
    # obligation forbids implementations that would satisfy the value
    # postcondition only vacuously by never returning.
    Requires(MustTerminate(len(content) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(content), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the method's own characters: the carried sequence exactly,
    # of the same length, whether the token was text or bytes. For a byte token
    # this means the method characters are recovered (the token decoded), not a
    # longer textual description of the byte-string object.
    Ensures(ToSeq(Result()) == ToSeq(content))
    Ensures(len(Result()) == len(content))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    n = len(content)
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(content), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n and n == len(content))
        Invariant(ToSeq(result) == ToSeq(content).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - j.
        Invariant(MustTerminate(n - j))
        # invariants-end
        Assert(ToSeq(content).take(j + 1) == ToSeq(content).take(j) + PSeq(content[j]))
        result = result + [content[j]]
        j = j + 1
    Assert(ToSeq(content).take(n) == ToSeq(content))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Project root (SBU_BENCHMARK_DIR=benchmark-verified); the prompt's path does not exist here. Spec under test: native_method(content:List[int], is_bytes:bool)->List[int], Requires Acc(list_pred(content),1/2) + ASCII-domain (0<=v<128, v!=39,92) + MustTerminate(len+2); Ensures Acc(list_pred(content),1/2), Acc(list_pred(Result())), ToSeq(Result())==ToSeq(content), len(Result())==len(content). This postcondition FULLY pins the returned value and length to the carried sequence, over a full-permission fresh Result, and MustTerminate forbids the vacuous-divergence channel.

All commands run with SBU_BENCHMARK_DIR=benchmark-verified, PY=python. Attack verifications run concurrently in background batches of <=3 (each spawns JVM+Z3).

7 DISTINCT same-spec wrong impls (impl region only; axioms empty, @Pure none, Requires/Ensures byte-identical -- all 7 confirmed `adversary same-spec`=SAME, exit 0):
- atk_1.py PREPATCH BUG reproduced (byte branch renders b'...'-wrapped object, prefix [98,39]/suffix [39], len+3): `python -m swebench_unified.adversary weakness nagini psf__requests-2317 atk_1.py` -> NOT-A-COUNTEREXAMPLE, does not verify (exit 2). Postcondition ToSeq(Result())==ToSeq(content) rejects it (G-DIFF). Confirms prepatch_reproduced.
- atk_2.py partial-domain (return []; correct only on empty token): weakness exit 2; direct verify -> `Postcondition ... Assertion (ToSeq(Result()) == ToSeq(content)) might not hold` (model.py:73).
- atk_3.py ungrounded constant ([71,69,84]='GET' regardless of content): weakness exit 2, verification failed.
- atk_4.py boundary/length (correct copy + extra [88]; len+1): weakness exit 2, verification failed (len/value post).
- atk_5.py order (reversed copy via prepend): weakness exit 2, verification failed.
- atk_6.py control-flow-effect / divergence (loop body never increments j): weakness exit 2; direct verify -> `Obligation leak check failed. Loop might not keep promise to terminate` (MustTerminate channel).
- atk_7.py ungrounded-oracle echo / aliasing (return content directly; value==content but only 1/2 perm held): weakness exit 2; direct verify -> `Postcondition ... insufficient permission to access list_pred(Result())` (permission channel).

NONE of the 7 came back CANDIDATE (none both shares-spec AND verifies), so there is NO verifying wrong impl and thus no faithful refined patch to materialize/run through run_resolve -- the verify=>correct implication is not broken by any exhibited attack. patches={} accordingly. The weakness wrapper explicitly distinguishes timeout ("timed out (inconclusive)") from real "verification failed"; all 7 reported real failure, none inconclusive.

Positive control: exact bundle model.py -> `bash scripts/nagini_verify.sh positive_control.py` VERIFIED in 11.27s (exit 0) -- toolchain reports true positives, so the 7 rejections are meaningful.

A-leg / model<->patch correspondence audit (refinement.md):
- A1 = R: str/bytes method arg <-> List[int]+is_bytes; ASCII (v<128) => byte value == codepoint of ASCII decode, one carrier serves both. Valid type refinement.
- A2 = A-reference: the deep verified copy-loop (Inv ToSeq(result)==ToSeq(content).take(j)) models to_native_string (requests/utils.py:655). NO consumed axiom (axioms region empty). G-AX (axiom_check.py) RUN -> exit 0, source `requests.utils.to_native_string (installed)` [real callee, not the inline fallback]: sound on 14 boundary + 126 full-domain single-value sweep + 20000 fuzz tokens, text+bytes, over the ENTIRE Requires domain (0..127 \ {39,92}). Fuzz alphabet derived directly from the Requires predicate -> checked domain == spec domain, no strict-subset hole. Correspondence holds.
- A3 = I: import-list edit dropping unused builtin_str on sessions.py:16 -- observational no-op.
- Section B confirmed: no kind-3 (unexpressible-changed-op) leg; the one genuinely changed op is modeled deeply (A-reference), not hidden behind an axiom about the function under change.
- Gold patch.diff = verbatim gold (method=builtin_str(method) -> to_native_string(method) at sessions.py:428 + import edit); it is the G-RESOLVE oracle.

VERDICT SOUND: >=5 (7) distinct same-spec attacks incl. prepatch bug + partial-domain + boundary + order + control-flow/termination + aliasing/ungrounded-echo were verified and NONE verifies; the postcondition value+length pin plus MustTerminate + read-only-permission-on-input close the value, divergence, and permission channels. G-AX A-reference sound against the real callee over the full spec domain. No verifying wrong impl exists, so verify=>correct is not falsified for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness of native_method's spec against the real callee to_native_string (requests/utils.py:655), confirmed at base_commit 091991be in the worktree.

SPEC REGION: native_method postcondition is ToSeq(Result())==ToSeq(content) AND len(Result())==len(content) — Result == content UNCONDITIONALLY (independent of is_bytes) over the Requires domain {0<=v<128, v!=39, v!=92}, both text and byte carriers. Model verifies in Nagini (exit 0, 10.5s), current bundle also carries Requires(MustTerminate(len(content)+2)).

REAL CALLEE (Py3 branch, builtin_str==str, is_py2==False): text token -> identity; byte token -> string.decode('ascii'). For any in-domain ASCII token BOTH branches yield the token's own code-point sequence, i.e. the identity on the carrier.

INDEPENDENT VERIFICATION (not via bundle scripts): I re-derived to_native_string's Py3 branch and ran it directly (old requests fails to import on py3.11: collections.Mapping). Exhaustive check — empty token + full single-value sweep over 0..127\{39,92} + multi-char products — on BOTH text and byte carriers: 1027 tokens, 0 disagreements with Result==content. axiom_check.py logic reproduced; the deep model (list(content)) == real callee everywhere in-domain.

Excluded values (>=128, 39, 92) are outside Requires, so no divergence is reachable — the domain restriction only shrinks coverage, it never enlarges the admitted set nor overclaims. Therefore the spec is neither too strong nor drifting: there is NO Requires-satisfying input on which the Ensures disagrees with the real repo callee. FAITHFUL.

Note: the recorded Role-1/Role-2 fails on this cell are a TERMINATION (spec-too-weak) axis (partial-correctness / MustTerminate absence), which is orthogonal to faithfulness and does not constitute a spec-too-strong / drift defect. The current model.py already adds the MustTerminate obligation.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures) and the semantic judgment agrees. The gold edit is `method = builtin_str(method)` -> `method = to_native_string(method)` in requests/sessions.py. The public problem_statement ALREADY discloses: the exact removed line `method = builtin_str(method)`, the file `requests/sessions.py`, the failure mode (b'GET' coerced to the literal string "b'GET'" causing a 404), and the desired behavior (requests should handle a binary method value). The spec view (model.py spec/pure/proof regions) restates exactly this co-extensive behavior: a method token arriving as text or bytes must produce its NATIVE TEXT representation, byte tokens decoded to their characters rather than rendered as the b'...' object. Crucially the spec view does NOT reveal anything beyond the problem_statement: it never names the gold-introduced callee `to_native_string`, never names the removed `builtin_str`, never quotes any gold-patch line, never names the patched file path or module path, and carries no bug/fix narration in comments. The gold callee `to_native_string` and `builtin_str` are named only in mapping.md and refinement.md, which are auditor/refinement artifacts, NOT the consumer spec view. The b'GET' example and the decode-vs-render distinction are all straight from the public issue. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
