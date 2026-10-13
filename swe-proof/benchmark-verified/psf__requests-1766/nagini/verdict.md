# P2 adversarial audit — psf__requests-1766

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_8.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(ncvalue), 1 / 2))
     Requires(Acc(list_pred(cnonce), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -107,17 +105,11 @@
     # post-conditions-end
     # impl-start
     result = list(base)  # type: List[int]
-    # ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
-    result = result + [44, 32, 113, 111, 112, 61]
-    result = result + [34, 97, 117, 116, 104, 34]
-    result = result + [44, 32, 110, 99, 61]
-    # the count value, bare
+    # BUG: emit bare qop=auth (no surrounding quotes)
+    result = result + [44, 32, 113, 111, 112, 61, 97, 117, 116, 104, 44, 32, 110, 99, 61]
     result = result + ncvalue
-    # ', cnonce="'
     result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
-    # the client-nonce value
     result = result + cnonce
-    # closing double quote
     result = result + [34]
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(ncvalue), 1 / 2))
     Requires(Acc(list_pred(cnonce), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -107,17 +105,17 @@
     # post-conditions-end
     # impl-start
     result = list(base)  # type: List[int]
-    # ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
+    while True:
+        Invariant(Acc(list_pred(result)))
+        Invariant(Acc(list_pred(base), 1 / 2))
+        Invariant(Acc(list_pred(ncvalue), 1 / 2))
+        Invariant(Acc(list_pred(cnonce), 1 / 2))
     result = result + [44, 32, 113, 111, 112, 61]
     result = result + [34, 97, 117, 116, 104, 34]
     result = result + [44, 32, 110, 99, 61]
-    # the count value, bare
     result = result + ncvalue
-    # ', cnonce="'
     result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
-    # the client-nonce value
     result = result + cnonce
-    # closing double quote
     result = result + [34]
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(ncvalue), 1 / 2))
     Requires(Acc(list_pred(cnonce), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -107,17 +105,14 @@
     # post-conditions-end
     # impl-start
     result = list(base)  # type: List[int]
-    # ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
     result = result + [44, 32, 113, 111, 112, 61]
     result = result + [34, 97, 117, 116, 104, 34]
     result = result + [44, 32, 110, 99, 61]
-    # the count value, bare
     result = result + ncvalue
-    # ', cnonce="'
     result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
-    # the client-nonce value
     result = result + cnonce
-    # closing double quote
     result = result + [34]
+    # divergent recursion: recompute via infinite self-call, ignore
+    dummy = append_qop_directive(base, ncvalue, cnonce)  # type: List[int]
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(ncvalue), 1 / 2))
     Requires(Acc(list_pred(cnonce), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -107,17 +105,12 @@
     # post-conditions-end
     # impl-start
     result = list(base)  # type: List[int]
-    # ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
     result = result + [44, 32, 113, 111, 112, 61]
     result = result + [34, 97, 117, 116, 104, 34]
     result = result + [44, 32, 110, 99, 61]
-    # the count value, bare
     result = result + ncvalue
-    # ', cnonce="'
     result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
-    # the client-nonce value
     result = result + cnonce
-    # closing double quote
-    result = result + [34]
+    # BUG: omit closing quote
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(ncvalue), 1 / 2))
     Requires(Acc(list_pred(cnonce), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -107,17 +105,16 @@
     # post-conditions-end
     # impl-start
     result = list(base)  # type: List[int]
-    # ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
-    result = result + [44, 32, 113, 111, 112, 61]
-    result = result + [34, 97, 117, 116, 104, 34]
-    result = result + [44, 32, 110, 99, 61]
-    # the count value, bare
+    if len(base) == 0:
+        # BUG on empty base: emit bare auth
+        result = result + [44, 32, 113, 111, 112, 61, 97, 117, 116, 104, 44, 32, 110, 99, 61]
+    else:
+        result = result + [44, 32, 113, 111, 112, 61]
+        result = result + [34, 97, 117, 116, 104, 34]
+        result = result + [44, 32, 110, 99, 61]
     result = result + ncvalue
-    # ', cnonce="'
     result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
-    # the client-nonce value
     result = result + cnonce
-    # closing double quote
     result = result + [34]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(ncvalue), 1 / 2))
     Requires(Acc(list_pred(cnonce), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -107,17 +105,13 @@
     # post-conditions-end
     # impl-start
     result = list(base)  # type: List[int]
-    # ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
     result = result + [44, 32, 113, 111, 112, 61]
     result = result + [34, 97, 117, 116, 104, 34]
     result = result + [44, 32, 110, 99, 61]
-    # the count value, bare
+    # BUG: interpolate cnonce where ncvalue belongs
+    result = result + cnonce
+    result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
     result = result + ncvalue
-    # ', cnonce="'
-    result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
-    # the client-nonce value
-    result = result + cnonce
-    # closing double quote
     result = result + [34]
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -33,7 +33,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
     Requires(Acc(list_pred(base), 1 / 2))
     Requires(Acc(list_pred(ncvalue), 1 / 2))
     Requires(Acc(list_pred(cnonce), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base), 1 / 2))
@@ -107,17 +105,18 @@
     # post-conditions-end
     # impl-start
     result = list(base)  # type: List[int]
-    # ', qop=' + '"auth"' + ', nc='   (the value token wrapped in double quotes)
     result = result + [44, 32, 113, 111, 112, 61]
     result = result + [34, 97, 117, 116, 104, 34]
     result = result + [44, 32, 110, 99, 61]
-    # the count value, bare
     result = result + ncvalue
-    # ', cnonce="'
     result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
-    # the client-nonce value
     result = result + cnonce
-    # closing double quote
     result = result + [34]
+    i = 0  # type: int
+    while i >= 0:
+        Invariant(i >= 0)
+        Invariant(Acc(list_pred(result)))
+        Invariant(ToSeq(result) == ToSeq(base) + qop_segment(ToSeq(ncvalue), ToSeq(cnonce)))
+        i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_8.py`

```python
"""Twin-artifact model for psf__requests-1766.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an HTTP Digest authorization credential carries a quality-of-protection
  ("qop") directive, the value of that directive must be a QUOTED string: the
  token `auth` is delimited by a double-quote code point immediately before it
  and immediately after it, so the emitted directive reads `qop="auth"` rather
  than the bare `qop=auth`. (RFC 2617 specifies the qop-options value as a
  quoted string of tokens.)

  Concretely, assembling the credential appends, to the already-built prefix, a
  constant directive segment that is the ordered concatenation of:

    (1) the literal `, qop="auth"` — the directive name, then the value `auth`
        wrapped in double quotes;
    (2) the literal `, nc=` followed by the caller-supplied count token,
        emitted bare (no surrounding quotes);
    (3) the literal `, cnonce="` followed by the caller-supplied client-nonce
        token and a closing double quote.

  The assembled credential is the prefix followed by exactly that segment; in
  particular the quoted value token `"auth"` (a double quote, the four code
  points of `auth`, a closing double quote) occurs contiguously in the result.

Textual values are modelled as ``List[int]`` of Unicode code points (Nagini
bans ``str`` indexing); the specification is carried over ``PSeq[int]``. The
segment is assembled DEEPLY (spelled out as a verified concatenation of literal
code-point sequences with the two interpolated caller tokens), so no opaque
callee is consumed and there are no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the directive segment is assembled deeply from input code-point
#  sequences and constant literals; it invokes no opaque library callee, so there
#  is nothing to axiomatize or G-AX-check.)
# axioms-end


# pure-start
@Pure
def quoted_value_token() -> PSeq[int]:
    """The quality-of-protection value emitted as a QUOTED string: a double
    quote (34), the four code points of the token `auth` (97,117,116,104), and
    a closing double quote (34)."""
    return PSeq(34, 97, 117, 116, 104, 34)  # '"auth"'


@Pure
def directive_head() -> PSeq[int]:
    """The literal head of the directive segment up to the count value:
    `, qop=` then the QUOTED value token then `, nc=`."""
    #   ','  ' '  'q'  'o'  'p'  '='  ('"auth"')          ','  ' '  'n'  'c'  '='
    return PSeq(44, 32, 113, 111, 112, 61) + quoted_value_token() + PSeq(44, 32, 110, 99, 61)


@Pure
def directive_mid() -> PSeq[int]:
    """The literal between the count value and the client-nonce value:
    `, cnonce="` (the client-nonce being a quoted string as well)."""
    #   ','  ' '  'c'  'n'  'o'  'n'  'c'  'e'  '='  '"'
    return PSeq(44, 32, 99, 110, 111, 110, 99, 101, 61, 34)


@Pure
def directive_tail() -> PSeq[int]:
    """The literal closing the client-nonce value: a single double quote."""
    return PSeq(34)


@Pure
def qop_segment(ncvalue: PSeq[int], cnonce: PSeq[int]) -> PSeq[int]:
    """The whole directive segment appended when a quality-of-protection token
    is present: the literal head (carrying the QUOTED value token `"auth"`), the
    count value, the literal mid, the client-nonce value, the closing quote."""
    return directive_head() + ncvalue + directive_mid() + cnonce + directive_tail()
# pure-end


def append_qop_directive(base: List[int], ncvalue: List[int],
                         cnonce: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(ncvalue), 1 / 2))
    Requires(Acc(list_pred(cnonce), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(ncvalue), 1 / 2))
    Ensures(Acc(list_pred(cnonce), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The assembled credential is the prefix followed by exactly the directive
    # segment, whose value token is the QUOTED form `"auth"`.
    Ensures(ToSeq(Result()) == ToSeq(base) + qop_segment(ToSeq(ncvalue), ToSeq(cnonce)))
    # Discriminating structural property: immediately after the prefix the
    # segment opens with the literal head, which carries the quoted value token
    # `"auth"` contiguously (a bare `auth` would not match this head).
    Ensures(ToSeq(Result()).drop(len(base)).take(len(directive_head())) == directive_head())
    Ensures(directive_head().take(6 + len(quoted_value_token())).drop(6) == quoted_value_token())
    # post-conditions-end
    # impl-start
    result = list(base)  # type: List[int]
    result = result + [44, 32, 113, 111, 112, 61]
    result = result + [34, 97, 117, 116, 104, 34]
    result = result + [44, 32, 110, 99, 61]
    result = result + ncvalue
    result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
    result = result + cnonce
    result = result + [34]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec fully PINS append_qop_directive's output: postcondition ToSeq(Result()) == ToSeq(base) + qop_segment(ToSeq(ncvalue), ToSeq(cnonce)) where qop_segment is a DEEP literal-code-point model (no axioms, no deep-model references). Two extra discriminating clauses lock the quoted `"auth"` token contiguously at the head of the appended segment. A-leg (axiom/deep-model) audit is VACUOUS and correctly declared: meta axioms=[], deep_model_references=[], no @ContractOnly/IOExists in model.py; refinement.md §C and mapping.md §3 correctly state no A-consumed / no A-reference / no axiom_check.py; all legs A1..A6 are R/I. model<->patch correspondence VERIFIED: the deep literals reconstruct EXACTLY the gold post-image template ', qop="auth", nc=%s, cnonce="%s"' (directive_head -> ', qop="auth", nc=', directive_mid -> ', cnonce="', directive_tail -> '"').

Attack battery (all same-spec confirmed via `adversary same-spec` exit 0; only impl region edited byte-for-byte elsewhere), each run through `adversary weakness nagini psf__requests-1766`:
- atk_1 prepatch bug (bare qop=auth): weakness exit=2, verify FAILED (spec rejects — reproduces the prepatch/G-DIFF witness).
- atk_2 control-flow-effect `while True` (no exit): weakness exit=2, verify FAILED (Nagini enforces termination).
- atk_3 control-flow-effect divergent self-recursion: weakness exit=2, verify FAILED.
- atk_4 boundary: omit closing quote: weakness exit=2, verify FAILED.
- atk_5 partial-domain: bare auth when len(base)==0: weakness exit=2, verify FAILED.
- atk_6 control-flow: swap nc/cnonce interpolation: weakness exit=2, verify FAILED.
- atk_7 control-flow-effect infinite loop with output-preserving invariant: weakness exit=2, verify FAILED (termination enforced — closes the usual partial-correctness verify-not-correct hole).
- atk_8 CORRECT deep-quoted impl (positive control): weakness exit=0 CANDIDATE, verifies in 24.1s (also direct nagini_verify exit 0).

MANDATORY resolve check on the sole verifying candidate: materialized atk_8_faithful.patch (== gold post-image edit, since atk_8 emits ', qop="auth", nc=' + ncvalue + ', cnonce="' + cnonce + '"'). run_resolve("psf__requests-1766", patch, timeout=3600) => completed=True resolved=True attempts=1 flaky=False (log: resolve_atk8.log). It RESOLVES, so it is a legitimate echo of the gold, NOT a weakness.

No verifying wrong-impl exists; every incorrect impl was rejected by the spec, and the only verifying candidate resolves. verify => correct holds. Ran 7 distinct wrong impls (>=4-6 required, spanning prepatch/differential, boundary, partial-domain, reorder, and three control-flow-effect/non-termination shapes) plus a positive control; batches launched concurrently at <=3 JVMs. Evidence (atk_*.py, w*.log, v8.log, atk_8_faithful.patch, resolve_atk8.log, SUMMARY.txt).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_8.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_8.py`

```python
"""Twin-artifact model for psf__requests-1766.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an HTTP Digest authorization credential carries a quality-of-protection
  ("qop") directive, the value of that directive must be a QUOTED string: the
  token `auth` is delimited by a double-quote code point immediately before it
  and immediately after it, so the emitted directive reads `qop="auth"` rather
  than the bare `qop=auth`. (RFC 2617 specifies the qop-options value as a
  quoted string of tokens.)

  Concretely, assembling the credential appends, to the already-built prefix, a
  constant directive segment that is the ordered concatenation of:

    (1) the literal `, qop="auth"` — the directive name, then the value `auth`
        wrapped in double quotes;
    (2) the literal `, nc=` followed by the caller-supplied count token,
        emitted bare (no surrounding quotes);
    (3) the literal `, cnonce="` followed by the caller-supplied client-nonce
        token and a closing double quote.

  The assembled credential is the prefix followed by exactly that segment; in
  particular the quoted value token `"auth"` (a double quote, the four code
  points of `auth`, a closing double quote) occurs contiguously in the result.

Textual values are modelled as ``List[int]`` of Unicode code points (Nagini
bans ``str`` indexing); the specification is carried over ``PSeq[int]``. The
segment is assembled DEEPLY (spelled out as a verified concatenation of literal
code-point sequences with the two interpolated caller tokens), so no opaque
callee is consumed and there are no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none — the directive segment is assembled deeply from input code-point
#  sequences and constant literals; it invokes no opaque library callee, so there
#  is nothing to axiomatize or G-AX-check.)
# axioms-end


# pure-start
@Pure
def quoted_value_token() -> PSeq[int]:
    """The quality-of-protection value emitted as a QUOTED string: a double
    quote (34), the four code points of the token `auth` (97,117,116,104), and
    a closing double quote (34)."""
    return PSeq(34, 97, 117, 116, 104, 34)  # '"auth"'


@Pure
def directive_head() -> PSeq[int]:
    """The literal head of the directive segment up to the count value:
    `, qop=` then the QUOTED value token then `, nc=`."""
    #   ','  ' '  'q'  'o'  'p'  '='  ('"auth"')          ','  ' '  'n'  'c'  '='
    return PSeq(44, 32, 113, 111, 112, 61) + quoted_value_token() + PSeq(44, 32, 110, 99, 61)


@Pure
def directive_mid() -> PSeq[int]:
    """The literal between the count value and the client-nonce value:
    `, cnonce="` (the client-nonce being a quoted string as well)."""
    #   ','  ' '  'c'  'n'  'o'  'n'  'c'  'e'  '='  '"'
    return PSeq(44, 32, 99, 110, 111, 110, 99, 101, 61, 34)


@Pure
def directive_tail() -> PSeq[int]:
    """The literal closing the client-nonce value: a single double quote."""
    return PSeq(34)


@Pure
def qop_segment(ncvalue: PSeq[int], cnonce: PSeq[int]) -> PSeq[int]:
    """The whole directive segment appended when a quality-of-protection token
    is present: the literal head (carrying the QUOTED value token `"auth"`), the
    count value, the literal mid, the client-nonce value, the closing quote."""
    return directive_head() + ncvalue + directive_mid() + cnonce + directive_tail()
# pure-end


def append_qop_directive(base: List[int], ncvalue: List[int],
                         cnonce: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(ncvalue), 1 / 2))
    Requires(Acc(list_pred(cnonce), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(ncvalue), 1 / 2))
    Ensures(Acc(list_pred(cnonce), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The assembled credential is the prefix followed by exactly the directive
    # segment, whose value token is the QUOTED form `"auth"`.
    Ensures(ToSeq(Result()) == ToSeq(base) + qop_segment(ToSeq(ncvalue), ToSeq(cnonce)))
    # Discriminating structural property: immediately after the prefix the
    # segment opens with the literal head, which carries the quoted value token
    # `"auth"` contiguously (a bare `auth` would not match this head).
    Ensures(ToSeq(Result()).drop(len(base)).take(len(directive_head())) == directive_head())
    Ensures(directive_head().take(6 + len(quoted_value_token())).drop(6) == quoted_value_token())
    # post-conditions-end
    # impl-start
    result = list(base)  # type: List[int]
    result = result + [44, 32, 113, 111, 112, 61]
    result = result + [34, 97, 117, 116, 104, 34]
    result = result + [44, 32, 110, 99, 61]
    result = result + ncvalue
    result = result + [44, 32, 99, 110, 111, 110, 99, 101, 61, 34]
    result = result + cnonce
    result = result + [34]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Frozen spec fully PINS append_qop_directive's output: postcondition ToSeq(Result()) == ToSeq(base) + qop_segment(ToSeq(ncvalue), ToSeq(cnonce)) where qop_segment is a DEEP literal-code-point model (no axioms, no deep-model references). Two extra discriminating clauses lock the quoted `"auth"` token contiguously at the head of the appended segment. A-leg (axiom/deep-model) audit is VACUOUS and correctly declared: meta axioms=[], deep_model_references=[], no @ContractOnly/IOExists in model.py; refinement.md §C and mapping.md §3 correctly state no A-consumed / no A-reference / no axiom_check.py; all legs A1..A6 are R/I. model<->patch correspondence VERIFIED: the deep literals reconstruct EXACTLY the gold post-image template ', qop="auth", nc=%s, cnonce="%s"' (directive_head -> ', qop="auth", nc=', directive_mid -> ', cnonce="', directive_tail -> '"').

Attack battery (all same-spec confirmed via `adversary same-spec` exit 0; only impl region edited byte-for-byte elsewhere), each run through `adversary weakness nagini psf__requests-1766`:
- atk_1 prepatch bug (bare qop=auth): weakness exit=2, verify FAILED (spec rejects — reproduces the prepatch/G-DIFF witness).
- atk_2 control-flow-effect `while True` (no exit): weakness exit=2, verify FAILED (Nagini enforces termination).
- atk_3 control-flow-effect divergent self-recursion: weakness exit=2, verify FAILED.
- atk_4 boundary: omit closing quote: weakness exit=2, verify FAILED.
- atk_5 partial-domain: bare auth when len(base)==0: weakness exit=2, verify FAILED.
- atk_6 control-flow: swap nc/cnonce interpolation: weakness exit=2, verify FAILED.
- atk_7 control-flow-effect infinite loop with output-preserving invariant: weakness exit=2, verify FAILED (termination enforced — closes the usual partial-correctness verify-not-correct hole).
- atk_8 CORRECT deep-quoted impl (positive control): weakness exit=0 CANDIDATE, verifies in 24.1s (also direct nagini_verify exit 0).

MANDATORY resolve check on the sole verifying candidate: materialized atk_8_faithful.patch (== gold post-image edit, since atk_8 emits ', qop="auth", nc=' + ncvalue + ', cnonce="' + cnonce + '"'). run_resolve("psf__requests-1766", patch, timeout=3600) => completed=True resolved=True attempts=1 flaky=False (log: resolve_atk8.log). It RESOLVES, so it is a legitimate echo of the gold, NOT a weakness.

No verifying wrong-impl exists; every incorrect impl was rejected by the spec, and the only verifying candidate resolves. verify => correct holds. Ran 7 distinct wrong impls (>=4-6 required, spanning prepatch/differential, boundary, partial-domain, reorder, and three control-flow-effect/non-termination shapes) plus a positive control; batches launched concurrently at <=3 JVMs. Evidence (atk_*.py, w*.log, v8.log, atk_8_faithful.patch, resolve_atk8.log, SUMMARY.txt).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec models the gold post-patch behavior of requests/auth.py:147 (the `if qop:` branch of HTTPDigestAuth.build_digest_header). At base_commit 847735553 the pre-patch line emits `, qop=auth, nc=%s, cnonce="%s"`; the gold patch changes it to `, qop="auth", nc=%s, cnonce="%s"`. The model's postcondition pins ToSeq(Result()) == ToSeq(base) + qop_segment(ToSeq(ncvalue), ToSeq(cnonce)), where qop_segment = directive_head (`, qop="auth", nc=`, carrying the quoted token PSeq(34,97,117,116,104,34)) + ncvalue + directive_mid (`, cnonce="`) + cnonce + directive_tail (`"`). This is exactly the post-patch %-format template with the two %s holes filled verbatim.

Fidelity checks performed:
1. nagini_verify.sh on model.py: Verification successful (21.53s, exit 0) — the impl actually satisfies the spec, so it is not vacuous.
2. Differential cross-check: computed the model's assembled code-point output vs the real gold `', qop="auth", nc=%s, cnonce="%s"' % (ncvalue, cnonce)` over 20000 random inputs (base/ncvalue/cnonce with codepoints 32..300, lengths 0..6) plus adversarial inputs containing %s, %d, %%, and double-quote characters. ZERO mismatches. Since ncvalue/cnonce enter via %s (verbatim string substitution) and the model concatenates their code points verbatim, there is no possible divergence — the %-format of a constant template with two %s substitutions is exactly sequence concatenation.
3. The spec is not too strong: it exactly equals the gold behavior, not stronger. The value token is emitted quoted (`"auth"`) as the gold does; ncvalue is bare and cnonce quoted, matching gold. The cosmetic whitespace-only hunk at auth.py:108 is correctly excluded (observed by no test, alters no emitted string).

No axioms are involved (deep model), so no drift risk from an opaque callee. The modeled function agrees with the real repo post-patch callee on every input; no diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py with impl elided) reviewed against the public problem_statement only (hints_text is empty and excluded). Gold edit is `, qop=auth` -> `, qop="auth"` (wrap the qop value in double quotes) plus a cosmetic trailing-whitespace hunk. The ENTIRE discriminating content of the fix is already disclosed by the public problem_statement, which explicitly states: 'quote qop options in Digest Auth ... the value of qop-options directive should be quoted with double quotes ... The value "auth" indicates authentication ... curl also appends these quotes.' So the spec view's disclosure that the qop value `auth` must be emitted as the quoted string `"auth"` rather than the bare `qop=auth` reveals nothing beyond the task text. Checked all vectors: (1) no diff markers; (2) patched file path requests/auth.py NOT present in spec view; (3) no bug/fix/patch/wrong/previously narration — docstring framed as desired behaviour, not an edit; (4) the pre-state contrast 'rather than the bare qop=auth' is directly derivable from the public report (which asks to ADD quoting to an unquoted value); (5) no spec-view identifier or comment echoes a patched repo symbol not in the problem statement. Mechanical leakage.screen() also passes clean (no hard failures). NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
