# P2 adversarial audit — pytest-dev__pytest-5809

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_9.py` |

**Non-vacuity.** The positive control `ctrl.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 14 same-spec, admissible attacks were run; 12 were rejected by the spec and the 2 that verified (atk_5, atk_9) had their faithful refined patches materialized and RUN through the official harness — both RESOLVED (completed=true, resolved=true, attempts=1), so both are correct echoes of the gold patch rather than verify⇏correct witnesses. No verifying wrong impl exists among the classes probed.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,12 @@
     Ensures(ToSeq(Result()) == text_token())
     # post-conditions-end
     # impl-start
-    mode = [116, 101, 120, 116]  # type: List[int]
+    # ATTACK 1 (prepatch bug re-encoded): the mode field is DERIVED from the
+    # interpreter major version instead of being the fixed plain-text token.
+    if py_major >= 3:
+        mode = [112, 121, 116, 104, 111, 110, 51]  # type: List[int]  # gloss: "python3"
+    else:
+        mode = [112, 121, 116, 104, 111, 110]      # "python"
     return mode
     # impl-end
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,13 @@
     Ensures(ToSeq(Result()) == text_token())
     # post-conditions-end
     # impl-start
-    mode = [116, 101, 120, 116]  # type: List[int]
+    # ATTACK 2 (partial domain): correct on the interpreter version the CI
+    # actually runs (py_major == 3) and wrong everywhere else — the A2 leg
+    # claims the postcondition quantifies over EVERY py_major.
+    if py_major == 3:
+        mode = [116, 101, 120, 116]  # type: List[int]  # gloss: "text"
+    else:
+        mode = [112, 121, 116, 104, 111, 110]  # "python"
     return mode
     # impl-end
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,11 @@
     Ensures(ToSeq(Result()) == text_token())
     # post-conditions-end
     # impl-start
-    mode = [116, 101, 120, 116]  # type: List[int]
+    # ATTACK 3 (boundary / trailing byte): "text\n" instead of "text". NOTE the
+    # F2P assertion is a SUBSTRING check on "lexer=text", and urlencode turns
+    # "text\n" into "text%0A", which still CONTAINS "lexer=text" — so this impl
+    # would slip past the test suite if the spec let it through.
+    mode = [116, 101, 120, 116, 10]  # type: List[int]  # gloss: "text\n"
     return mode
     # impl-end
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,6 +60,11 @@
     Ensures(ToSeq(Result()) == text_token())
     # post-conditions-end
     # impl-start
+    # ATTACK 4 (control-flow effect / recursive divergence): the value is the
+    # gold token, but the method re-enters itself with the SAME argument, so the
+    # termination measure never decreases and the call never returns.
+    if py_major >= 0:
+        return paste_mode_field(py_major)
     mode = [116, 101, 120, 116]  # type: List[int]
     return mode
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

```diff
@@ -60,7 +60,20 @@
     Ensures(ToSeq(Result()) == text_token())
     # post-conditions-end
     # impl-start
-    mode = [116, 101, 120, 116]  # type: List[int]
+    # ATTACK 5 (echo, built differently): assemble the same "text" token with a
+    # loop over a code-point table instead of a literal. Behaviourally the gold
+    # value; this is the control that a CANDIDATE that IS correct resolves.
+    table = [116, 101, 120, 116]  # type: List[int]
+    mode = []  # type: List[int]
+    i = 0
+    while i < len(table):
+        Invariant(Acc(list_pred(table), 1 / 4))
+        Invariant(Acc(list_pred(mode)))
+        Invariant(0 <= i and i <= len(table))
+        Invariant(ToSeq(mode) == ToSeq(table).take(i))
+        Invariant(MustTerminate(len(table) - i + 1))
+        mode.append(table[i])
+        i = i + 1
     return mode
     # impl-end
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,22 @@
     Ensures(ToSeq(Result()) == ToSeq(contents))
     # post-conditions-end
     # impl-start
-    body = list(contents)  # type: List[int]
+    # ATTACK 6 (boundary on the identity leg): forward the contents, except an
+    # EMPTY body is replaced by a single space. Every non-empty test body is
+    # unaffected, so only a spec that pins identity on the whole domain rejects it.
+    body = []  # type: List[int]
+    if len(contents) == 0:
+        body.append(32)
+    else:
+        i = 0
+        while i < len(contents):
+            Invariant(Acc(list_pred(contents), 1 / 4))
+            Invariant(Acc(list_pred(body)))
+            Invariant(0 <= i and i <= len(contents))
+            Invariant(ToSeq(body) == ToSeq(contents).take(i))
+            Invariant(MustTerminate(len(contents) - i + 1))
+            body.append(contents[i])
+            i = i + 1
     return body
     # impl-end
 
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -92,6 +92,9 @@
     Ensures(ToSeq(Result()) == expiry_token())
     # post-conditions-end
     # impl-start
-    exp = [49, 119, 101, 101, 107]  # type: List[int]
+    # ATTACK 7 (wrong constant, unchanged leg): the expiry token is "1week5"
+    # (a plausible typo). The gold hunk leaves this entry alone, so the model
+    # must still pin it.
+    exp = [49, 119, 101, 101, 107, 53]  # type: List[int]  # gloss: "1week5"
     return exp
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,14 @@
     Ensures(ToSeq(Result()) == text_token())
     # post-conditions-end
     # impl-start
+    # ATTACK 8 (divergence): the right token is computed but the method spins
+    # forever first. MustTerminate(2) at the method level must reject this;
+    # a diverging refinement hangs the pastebin submission.
     mode = [116, 101, 120, 116]  # type: List[int]
+    i = 0
+    while i >= 0:
+        Invariant(i >= 0)
+        i = i + 1
     return mode
     # impl-end
 
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -60,7 +60,19 @@
     Ensures(ToSeq(Result()) == text_token())
     # post-conditions-end
     # impl-start
-    mode = [116, 101, 120, 116]  # type: List[int]
+    # ATTACK 9 (ungrounded-oracle echo): discharge the postcondition by copying
+    # the SPEC's own oracle text_token() element by element, never naming a
+    # concrete token. Verifies trivially; the question the audit asks is whether
+    # its faithful refinement has any repo-level meaning (is text_token grounded?).
+    mode = []  # type: List[int]
+    i = 0
+    while i < len(text_token()):
+        Invariant(Acc(list_pred(mode)))
+        Invariant(0 <= i and i <= len(text_token()))
+        Invariant(ToSeq(mode) == text_token().take(i))
+        Invariant(MustTerminate(len(text_token()) - i + 1))
+        mode.append(text_token()[i])
+        i = i + 1
     return mode
     # impl-end
 
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,19 @@
     Ensures(ToSeq(Result()) == ToSeq(contents))
     # post-conditions-end
     # impl-start
-    body = list(contents)  # type: List[int]
+    # ATTACK 10 (partial domain, truncation): forward the contents, but cap the
+    # body at 4096 code points. Every test body is far shorter, so only a spec
+    # that pins identity on the WHOLE domain rejects this.
+    body = []  # type: List[int]
+    i = 0
+    while i < len(contents) and i < 4096:
+        Invariant(Acc(list_pred(contents), 1 / 4))
+        Invariant(Acc(list_pred(body)))
+        Invariant(0 <= i and i <= len(contents))
+        Invariant(ToSeq(body) == ToSeq(contents).take(i))
+        Invariant(MustTerminate(len(contents) - i + 1))
+        body.append(contents[i])
+        i = i + 1
     return body
     # impl-end
 
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,10 @@
     Ensures(ToSeq(Result()) == text_token())
     # post-conditions-end
     # impl-start
-    mode = [116, 101, 120, 116]  # type: List[int]
+    # ATTACK 11 (boundary superstring): "text2" — passes the F2P substring
+    # assertion ("lexer=text" occurs inside "lexer=text2") yet is not the
+    # plain-text mode the service accepts.
+    mode = [116, 101, 120, 116, 50]  # type: List[int]  # gloss: "text2"
     return mode
     # impl-end
 
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -77,6 +77,11 @@
     Ensures(ToSeq(Result()) == ToSeq(contents))
     # post-conditions-end
     # impl-start
+    # ATTACK 12 (heap effect): return the identity copy, but first MUTATE the
+    # caller's contents list. ToSeq(Result()) == ToSeq(contents) can still be
+    # read as holding at exit (both sides changed together), while the refined
+    # code corrupts the session log the caller still holds.
+    contents.append(88)
     body = list(contents)  # type: List[int]
     return body
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,8 @@
     Ensures(ToSeq(Result()) == text_token())
     # post-conditions-end
     # impl-start
-    mode = [116, 101, 120, 116]  # type: List[int]
+    # ATTACK 13a (cross-wired): the mode field carries the EXPIRY token.
+    mode = [49, 119, 101, 101, 107]  # type: List[int]  # gloss: "1week"
     return mode
     # impl-end
 
@@ -92,6 +93,7 @@
     Ensures(ToSeq(Result()) == expiry_token())
     # post-conditions-end
     # impl-start
-    exp = [49, 119, 101, 101, 107]  # type: List[int]
+    # ATTACK 13b (cross-wired): the expiry field carries the TEXT token.
+    exp = [116, 101, 120, 116]  # type: List[int]  # gloss: "text"
     return exp
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -60,6 +60,7 @@
     Ensures(ToSeq(Result()) == text_token())
     # post-conditions-end
     # impl-start
+    Assert(False)
     mode = [116, 101, 120, 116]  # type: List[int]
     return mode
     # impl-end
@@ -77,6 +78,7 @@
     Ensures(ToSeq(Result()) == ToSeq(contents))
     # post-conditions-end
     # impl-start
+    Assert(False)
     body = list(contents)  # type: List[int]
     return body
     # impl-end
@@ -92,6 +94,7 @@
     Ensures(ToSeq(Result()) == expiry_token())
     # post-conditions-end
     # impl-start
+    Assert(False)
     exp = [49, 119, 101, 101, 107]  # type: List[int]
     return exp
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.py`

```python
"""Twin-artifact model for pytest-dev__pytest-5809.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the session output is submitted to the paste service, the request body
  carries three named fields. Two of them are forwarded unchanged from the
  inputs:

    * the paste BODY field holds exactly the supplied contents (identity), and
    * the EXPIRY field holds the constant one-week token "1week".

  The third field selects the syntax-highlighting MODE under which the paste
  service should render the body. Because the body being submitted is the
  console output of a test run — arbitrary text rather than source code in any
  particular language — the mode field is the constant plain-text token "text".
  Crucially this choice is INVARIANT under the running interpreter's major
  version: whatever the interpreter major version, the mode field is "text"
  (it is NOT derived from, and does not vary with, the interpreter version).

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No axiomatized callee: the modelled behaviour — which constant token the
# request's mode field carries — is concrete and modelled deeply.)
# axioms-end

# pure-start
@Pure
def text_token() -> PSeq[int]:
    """The plain-text highlighting-mode token "text" as code points."""
    return PSeq(116, 101, 120, 116)

@Pure
def expiry_token() -> PSeq[int]:
    """The constant one-week expiry token "1week" as code points."""
    return PSeq(49, 119, 101, 101, 107)
# pure-end

def paste_mode_field(py_major: int) -> List[int]:
    # pre-conditions-start
    # py_major is the running interpreter's major version (an arbitrary int);
    # no carrier object is required.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The mode field is the constant plain-text token, INVARIANT under py_major:
    # the very same value is returned whatever the interpreter major version.
    Ensures(ToSeq(Result()) == text_token())
    # post-conditions-end
    # impl-start
    mode = [116, 101, 120, 116]  # type: List[int]
    return mode
    # impl-end

def paste_body_field(contents: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(contents), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(contents), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The body field forwards the supplied contents unchanged (identity).
    Ensures(ToSeq(Result()) == ToSeq(contents))
    # post-conditions-end
    # impl-start
    body = list(contents)  # type: List[int]
    return body
    # impl-end

def paste_expiry_field() -> List[int]:
    # pre-conditions-start
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The expiry field is the constant one-week token, unchanged.
    Ensures(ToSeq(Result()) == expiry_token())
    # post-conditions-end
    # impl-start
    exp = [49, 119, 101, 101, 107]  # type: List[int]
    return exp
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: (all paths below are in it).

### Commands
  python -m swebench_unified.adversary same-spec nagini pytest-dev__pytest-5809 <D>/atk_N.py   -> SAME for all 14 + ctrl.py
  python -m swebench_unified.adversary weakness  nagini pytest-dev__pytest-5809 <D>/atk_N.py   -> per-attack below
  bash scripts/nagini_verify.sh <D>/atk_N.py                                                   -> failure REASON below
  python <D>/do_resolve.py <D>/patch_atkN.diff <D>/resolve_atkN.json atkN                       -> harness run_resolve
Verifications were run 3-at-a-time as concurrent background jobs (JVM+Z3 per check).

PER-ATTACK RESULTS (all 14: same_spec=True, admissible=True, verify_completed=True — mirrored via adversary.check_attack, the runner's own primitive): atk_1  prepatch bug re-encoded (version-derived "python3"/"python" lexer)   -> exit 2, NOT-A-COUNTEREXAMPLE. Reason: "Postcondition of paste_mode_field might not hold. Assertion (ToSeq(Result()) == text_token())". => prepatch_reproduced. atk_2  PARTIAL DOMAIN: "text" only when py_major == 3, "python" otherwise    -> exit 2. Same postcondition failure => the A2 leg's "holds for EVERY py_major" really is quantified. atk_3  BOUNDARY: "text\n" (urlencodes to text%0A, which still CONTAINS the F2P substring "lexer=text") -> exit 2, mode-field postcondition.

The SPEC is strictly stronger than the F2P assertion here. atk_4  CONTROL-FLOW EFFECT: right value, non-decreasing recursive self-call  -> exit 2. Reason: "Obligation leak check failed. Callee paste_mode_field might not take all unsatisfied obligations from the caller" => method-level MustTerminate(2) bites. atk_5  ECHO: same "text" token assembled by a loop over a code-point table   -> exit 0, CANDIDATE (11.6s).

Patch <D>/patch_atk5.diff materialized and RUN: {completed:true, resolved:TRUE, attempts:1, flaky:false} => correct echo, NOT a weakness. atk_6  BOUNDARY on identity leg: empty body replaced by a single space       -> exit 2. "Postcondition of paste_body_field might not hold (ToSeq(Result()) == ToSeq(contents))". atk_7  WRONG CONSTANT on the UNCHANGED expiry leg: "1week5"                  -> exit 2. "Postcondition of paste_expiry_field ... == expiry_token()" => the unchanged entries are genuinely pinned (hunk fidelity, A4). atk_8  DIVERGENCE: right value, infinite loop first                          -> exit 2. "Obligation leak check failed.

Loop might not take all unsatisfied obligations from the context." atk_9  UNGROUNDED-ORACLE ECHO: impl copies the spec's own text_token() element-by-element, never naming a concrete token -> exit 0, CANDIDATE (14.9s). Patch <D>/patch_atk9.diff materialized and RUN: {completed:true, resolved:TRUE, attempts:1} => text_token() IS grounded (its faithful refinement is the correct "text"); no ungrounded-oracle hole. atk_10 PARTIAL DOMAIN on identity leg: body truncated at 4096 code points    -> exit 2, paste_body_field postcondition. atk_11 BOUNDARY SUPERSTRING: "text2". NOTE the F2P assertion is a SUBSTRING check ('"lexer=%s" % lexer in data.decode()') and "lexer=text" IS contained in "lexer=text2" — verified in python: this impl would PASS FAIL_TO_PASS.

The SPEC rejected it anyway (mode-field postcondition). Spec > tests. atk_12 HEAP EFFECT: identity copy, but mutates the caller's contents list    -> exit 2. "The precondition of method append might not hold. There might be insufficient permission" => the 1/2 fractional list_pred on contents forbids the side effect. atk_13 CROSS-WIRED legs: mode<-"1week", expiry<-"text"                       -> exit 2. BOTH postconditions flagged. atk_14 VACUITY CONTROL: Assert(False) in all three impl regions              -> exit 2 with "Assert might fail. Assertion False might not hold" x3 => preconditions are satisfiable; nothing is discharged vacuously.

POSITIVE CONTROL: <D>/ctrl.py (byte-identical to bundle model.py) -> weakness exit 0 / check_attack verifies=True (11.4s).

ORACLE-REFUTATION CONTROL (the decisive check that my two "resolved" verdicts carry information): <D>/patch_oracle_control.diff embeds the PRE-PATCH lexer expression as a patch that definitely applies and imports (only a trailing comment added). run_resolve -> {completed:true, resolved:FALSE, attempts:3, note:"patch did not resolve in 3 attempts (consistent — not flaky)"}. So the harness genuinely REFUTES a wrong lexer on this instance; the atk_5/atk_9 resolutions are real evidence, not an oracle that resolves everything.

METHODOLOGICAL CORRECTION I made on myself: atk_1,2,3,7,11,13 initially "failed" only because my inline gloss ('# type: List[int]  "text"') made Nagini emit a type-comment SYNTAX error — a rejection the specification never performed, which would have been a rubber stamp dressed as falsification. Also atk_4's first encoding used `raise`, which Nagini cannot translate ("Not supported: Unsupported builtin function") — again no spec verdict. All seven were re-encoded and re-run; every one now fails on a NAMED spec obligation (quoted above).

refinement.md AUDIT (legs A1-A5): tags are I, I/R, R+I, I, A-reference — no kind-3, consistent with an EMPTY axioms region (grep: 0 hits for ContractOnly/Assume(/Refute( in model.py), so there is no A-consumed leg to over-trust. A1/A2 correspondence confirmed against the repo at base_commit 8aba863 (src/_pytest/pastebin.py:80-84) and the gold diff, which touches ONLY the params dict (3 removed value lines + 1 added line). A5's A-reference (urllib.parse.urlencode, unchanged by the patch, pastebin.py:86) holds: axiom_check.py exits 0 (20010 body inputs x 3 version witnesses). MINOR GAP, not a defect: axiom_check.py exercises only str bodies, while the F2P test passes BYTES (b"full-paste-contents"). I checked the bytes case myself — urlencode({'code': b'full-paste-contents', ...}) -> 'code=full-paste-contents&lexer=text&expiry=1week', and b'', b'a b', b'x\xc3\xa9' all keep lexer=text and never lexer=python — so the leg is sound on the domain that actually matters; the A-reference's coverage claim is merely narrower than its justification implies.

NOTABLE STRENGTH: the spec is strictly STRONGER than the official test. atk_11 ("text2") and atk_3 ("text\n") both satisfy the F2P substring assertion yet are rejected by ToSeq(Result()) == text_token(). The unchanged legs (body identity, "1week") are pinned too (atk_6/7/10/12/13), the whole py_major domain is covered (atk_2), termination is enforced at the method level (atk_4/atk_8), and the heap is protected by the fractional permission (atk_12).

VERDICT: SOUND (advisory). 14 admissible attacks run, 12 rejected on named spec obligations; both candidates' faithful patches executed through the official harness and BOTH RESOLVED; oracle proven able to refute on this instance; positive control verifies; prepatch bug reproduced.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.py`, `atk_9.py` |

**Non-vacuity.** The positive control `ctrl.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. 14 same-spec, admissible attacks were run; 12 were rejected by the spec and the 2 that verified (atk_5, atk_9) had their faithful refined patches materialized and RUN through the official harness — both RESOLVED (completed=true, resolved=true, attempts=1), so both are correct echoes of the gold patch rather than verify⇏correct witnesses. No verifying wrong impl exists among the classes probed.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.py`

```python
"""Twin-artifact model for pytest-dev__pytest-5809.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the session output is submitted to the paste service, the request body
  carries three named fields. Two of them are forwarded unchanged from the
  inputs:

    * the paste BODY field holds exactly the supplied contents (identity), and
    * the EXPIRY field holds the constant one-week token "1week".

  The third field selects the syntax-highlighting MODE under which the paste
  service should render the body. Because the body being submitted is the
  console output of a test run — arbitrary text rather than source code in any
  particular language — the mode field is the constant plain-text token "text".
  Crucially this choice is INVARIANT under the running interpreter's major
  version: whatever the interpreter major version, the mode field is "text"
  (it is NOT derived from, and does not vary with, the interpreter version).

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No axiomatized callee: the modelled behaviour — which constant token the
# request's mode field carries — is concrete and modelled deeply.)
# axioms-end

# pure-start
@Pure
def text_token() -> PSeq[int]:
    """The plain-text highlighting-mode token "text" as code points."""
    return PSeq(116, 101, 120, 116)

@Pure
def expiry_token() -> PSeq[int]:
    """The constant one-week expiry token "1week" as code points."""
    return PSeq(49, 119, 101, 101, 107)
# pure-end

def paste_mode_field(py_major: int) -> List[int]:
    # pre-conditions-start
    # py_major is the running interpreter's major version (an arbitrary int);
    # no carrier object is required.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The mode field is the constant plain-text token, INVARIANT under py_major:
    # the very same value is returned whatever the interpreter major version.
    Ensures(ToSeq(Result()) == text_token())
    # post-conditions-end
    # impl-start
    mode = [116, 101, 120, 116]  # type: List[int]
    return mode
    # impl-end

def paste_body_field(contents: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(contents), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(contents), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The body field forwards the supplied contents unchanged (identity).
    Ensures(ToSeq(Result()) == ToSeq(contents))
    # post-conditions-end
    # impl-start
    body = list(contents)  # type: List[int]
    return body
    # impl-end

def paste_expiry_field() -> List[int]:
    # pre-conditions-start
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The expiry field is the constant one-week token, unchanged.
    Ensures(ToSeq(Result()) == expiry_token())
    # post-conditions-end
    # impl-start
    exp = [49, 119, 101, 101, 107]  # type: List[int]
    return exp
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SCRATCH: (all paths below are in it).

### Commands
  python -m swebench_unified.adversary same-spec nagini pytest-dev__pytest-5809 <D>/atk_N.py   -> SAME for all 14 + ctrl.py
  python -m swebench_unified.adversary weakness  nagini pytest-dev__pytest-5809 <D>/atk_N.py   -> per-attack below
  bash scripts/nagini_verify.sh <D>/atk_N.py                                                   -> failure REASON below
  python <D>/do_resolve.py <D>/patch_atkN.diff <D>/resolve_atkN.json atkN                       -> harness run_resolve
Verifications were run 3-at-a-time as concurrent background jobs (JVM+Z3 per check).

PER-ATTACK RESULTS (all 14: same_spec=True, admissible=True, verify_completed=True — mirrored via adversary.check_attack, the runner's own primitive): atk_1  prepatch bug re-encoded (version-derived "python3"/"python" lexer)   -> exit 2, NOT-A-COUNTEREXAMPLE. Reason: "Postcondition of paste_mode_field might not hold. Assertion (ToSeq(Result()) == text_token())". => prepatch_reproduced. atk_2  PARTIAL DOMAIN: "text" only when py_major == 3, "python" otherwise    -> exit 2. Same postcondition failure => the A2 leg's "holds for EVERY py_major" really is quantified. atk_3  BOUNDARY: "text\n" (urlencodes to text%0A, which still CONTAINS the F2P substring "lexer=text") -> exit 2, mode-field postcondition.

The SPEC is strictly stronger than the F2P assertion here. atk_4  CONTROL-FLOW EFFECT: right value, non-decreasing recursive self-call  -> exit 2. Reason: "Obligation leak check failed. Callee paste_mode_field might not take all unsatisfied obligations from the caller" => method-level MustTerminate(2) bites. atk_5  ECHO: same "text" token assembled by a loop over a code-point table   -> exit 0, CANDIDATE (11.6s).

Patch <D>/patch_atk5.diff materialized and RUN: {completed:true, resolved:TRUE, attempts:1, flaky:false} => correct echo, NOT a weakness. atk_6  BOUNDARY on identity leg: empty body replaced by a single space       -> exit 2. "Postcondition of paste_body_field might not hold (ToSeq(Result()) == ToSeq(contents))". atk_7  WRONG CONSTANT on the UNCHANGED expiry leg: "1week5"                  -> exit 2. "Postcondition of paste_expiry_field ... == expiry_token()" => the unchanged entries are genuinely pinned (hunk fidelity, A4). atk_8  DIVERGENCE: right value, infinite loop first                          -> exit 2. "Obligation leak check failed.

Loop might not take all unsatisfied obligations from the context." atk_9  UNGROUNDED-ORACLE ECHO: impl copies the spec's own text_token() element-by-element, never naming a concrete token -> exit 0, CANDIDATE (14.9s). Patch <D>/patch_atk9.diff materialized and RUN: {completed:true, resolved:TRUE, attempts:1} => text_token() IS grounded (its faithful refinement is the correct "text"); no ungrounded-oracle hole. atk_10 PARTIAL DOMAIN on identity leg: body truncated at 4096 code points    -> exit 2, paste_body_field postcondition. atk_11 BOUNDARY SUPERSTRING: "text2". NOTE the F2P assertion is a SUBSTRING check ('"lexer=%s" % lexer in data.decode()') and "lexer=text" IS contained in "lexer=text2" — verified in python: this impl would PASS FAIL_TO_PASS.

The SPEC rejected it anyway (mode-field postcondition). Spec > tests. atk_12 HEAP EFFECT: identity copy, but mutates the caller's contents list    -> exit 2. "The precondition of method append might not hold. There might be insufficient permission" => the 1/2 fractional list_pred on contents forbids the side effect. atk_13 CROSS-WIRED legs: mode<-"1week", expiry<-"text"                       -> exit 2. BOTH postconditions flagged. atk_14 VACUITY CONTROL: Assert(False) in all three impl regions              -> exit 2 with "Assert might fail. Assertion False might not hold" x3 => preconditions are satisfiable; nothing is discharged vacuously.

POSITIVE CONTROL: <D>/ctrl.py (byte-identical to bundle model.py) -> weakness exit 0 / check_attack verifies=True (11.4s).

ORACLE-REFUTATION CONTROL (the decisive check that my two "resolved" verdicts carry information): <D>/patch_oracle_control.diff embeds the PRE-PATCH lexer expression as a patch that definitely applies and imports (only a trailing comment added). run_resolve -> {completed:true, resolved:FALSE, attempts:3, note:"patch did not resolve in 3 attempts (consistent — not flaky)"}. So the harness genuinely REFUTES a wrong lexer on this instance; the atk_5/atk_9 resolutions are real evidence, not an oracle that resolves everything.

METHODOLOGICAL CORRECTION I made on myself: atk_1,2,3,7,11,13 initially "failed" only because my inline gloss ('# type: List[int]  "text"') made Nagini emit a type-comment SYNTAX error — a rejection the specification never performed, which would have been a rubber stamp dressed as falsification. Also atk_4's first encoding used `raise`, which Nagini cannot translate ("Not supported: Unsupported builtin function") — again no spec verdict. All seven were re-encoded and re-run; every one now fails on a NAMED spec obligation (quoted above).

refinement.md AUDIT (legs A1-A5): tags are I, I/R, R+I, I, A-reference — no kind-3, consistent with an EMPTY axioms region (grep: 0 hits for ContractOnly/Assume(/Refute( in model.py), so there is no A-consumed leg to over-trust. A1/A2 correspondence confirmed against the repo at base_commit 8aba863 (src/_pytest/pastebin.py:80-84) and the gold diff, which touches ONLY the params dict (3 removed value lines + 1 added line). A5's A-reference (urllib.parse.urlencode, unchanged by the patch, pastebin.py:86) holds: axiom_check.py exits 0 (20010 body inputs x 3 version witnesses). MINOR GAP, not a defect: axiom_check.py exercises only str bodies, while the F2P test passes BYTES (b"full-paste-contents"). I checked the bytes case myself — urlencode({'code': b'full-paste-contents', ...}) -> 'code=full-paste-contents&lexer=text&expiry=1week', and b'', b'a b', b'x\xc3\xa9' all keep lexer=text and never lexer=python — so the leg is sound on the domain that actually matters; the A-reference's coverage claim is merely narrower than its justification implies.

NOTABLE STRENGTH: the spec is strictly STRONGER than the official test. atk_11 ("text2") and atk_3 ("text\n") both satisfy the F2P substring assertion yet are rejected by ToSeq(Result()) == text_token(). The unchanged legs (body identity, "1week") are pinned too (atk_6/7/10/12/13), the whole py_major domain is covered (atk_2), termination is enforced at the method level (atk_4/atk_8), and the heap is protected by the fractional permission (atk_12).

VERDICT: SOUND (advisory). 14 admissible attacks run, 12 rejected on named spec obligations; both candidates' faithful patches executed through the official harness and BOTH RESOLVED; oracle proven able to refute on this instance; positive control verifies; prepatch bug reproduced.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SETUP. Worktree: repo/ = base_commit 8aba863a634f, repo_gold/ = base + patch.diff (applies clean). Real oracle built by loading src/_pytest/pastebin.py directly (stubbing only six/pytest, which create_new_paste does not use) and installing a capturing stand-in at urllib.request.urlopen -- the same call-time-resolution seam the repo's own mocked_urlopen fixture uses, so the submitted request body is observed with no network traffic.

### BASELINES (all machine-checked).
1. bundle model.py verifies: `nagini_verify.sh` exit 0 ("Verification successful", 11.3s).
2. G-DIFF live: model_prepatch.py FAILS exactly at atk_pre.py:60 "Postcondition of paste_mode_field might not hold. Assertion (ToSeq(Result()) == text_token()) might not hold." The spec senses the change at the right node.
3. Oracle direction confirmed by replicating the F2P assertions verbatim against both trees: PREPATCH body = code=full-paste-contents&lexer=python3&expiry=1week -> "lexer=text" assertion False -> F2P FAILS; GOLD body = code=full-paste-contents&lexer=text&expiry=1week -> all 7 assertions True -> F2P PASSES.
4. Mapping completeness: `grep -rn lexer src testing` at base_commit returns exactly ONE production site, src/_pytest/pastebin.py:82 -- the site the model maps. No unmodeled second lexer site.
5. axiom_check.py exit 0 (A-reference urlencode, 20010 bodies).

DIFFERENTIAL FAITHFULNESS SWEEP -- 12,144 trials, ZERO divergences. For every trial I compared all three modeled postconditions against the real gold function's actual submitted payload, decoded losslessly at the wire level with unquote_to_bytes (the exact inverse of the serializer): paste_mode_field(py_major)  vs the real "lexer" value paste_body_field(contents)  vs the real "code" value paste_expiry_field()        vs the real "expiry" value plus the structural claim that the payload carries exactly {code,lexer,expiry}.

Domain: str bodies AND bytes bodies (bytes is what the F2P test and the production pytest_unconfigure path actually pass); empty, 4096-long, whitespace, URL-metacharacter (a+b&c=d%20e, =&=&, %%%, + +), NUL, non-ASCII (e-acute, CJK, U+263A, U+1F600, U+10FFFF), invalid UTF-8 (b'\xff\xfe', b'\x80', b'\xc3\x28'), bytes(range(256)); py_major over 2/3/4/0/-1/+-1e9 and random ints in +-1e6. Result: mode field was "text" on every single trial and never varied with py_major (the version-invariance claim holds against the real code, which no longer reads sys.version_info at that expression); expiry was always "1week"; body was always the exact identity; field names always exactly the three. No input made the modeled functions disagree with the real callee. Also ran an independent 8,000-trial fuzz under both bridges: 0 deviations.

### THREE THINGS I PROBED AS CANDIDATE DRIFT AND RULED OUT (with the reasoning, so a re-auditor can re-examine):

(a) Spec forbids the literal gold translation (aliasing). Requires(Acc(list_pred(contents),1/2)) + Ensures(Acc(list_pred(Result()))) forces the result to be a FRESH list, so 1/2+full>1. The real repo aliases -- `"code": contents`, no copy. I confirmed the spec genuinely rejects the alias: an attack whose only change is `return contents` passes same-spec (exit 0) but FAILS verification with "insufficient permission to access list_pred(Result())". So the model is strictly STRONGER than the repo here. Ruled a benign carrier artifact, not drift: the real dict value is str/bytes, which are IMMUTABLE (verified: item assignment raises TypeError for both), so copy-vs-alias is unobservable to any client -- I submitted the object itself and a fresh equal copy to the real function and got byte-identical payloads. The extra freshness demand is forced by modeling an immutable str as a mutable List[int]; it cannot admit a wrong impl nor reject a behaviorally-correct one.

(b) Surrogate bodies make the REAL function raise. contents="\ud800" or "a\udfffb" raises UnicodeEncodeError inside urlencode, while the modeled paste_body_field is total and claims success+identity on any List[int]. Ruled out of scope, not drift: the model's mapped node is the dict ENTRY VALUE (`"code": contents`, line 81), and building that dict entry is total for any str -- the raise originates in urlencode, which refinement.md step A5 explicitly places outside the model as an unchanged A-reference. The raise is also identical pre- and post-patch, so it is not behavior the patch touches.

(c) The bundle's own conformance bridge is lossy on bytes bodies. conformance_check.py recovers the body as [ord(c) for c in parse_qsl(...)["code"]], which round-trips non-ASCII bytes through a lossy UTF-8 decode: for b'\xff\xfe' the model identity gives [255,254] but that bridge yields [65533,65533] (U+FFFD replacement chars); b'\x80' -> [128] vs [65533]; UTF-8-encoded U+263A -> [226,152,186] vs [9786]. This is a harness artifact, NOT spec unfaithfulness: at the wire level (unquote_to_bytes) the model and repo agree exactly on all of these, and conformance_check.py only ever feeds str bodies (_rand_contents returns str), so it never reaches the lossy path. Flagged only as latent fragility in the check script -- if its input domain were ever widened to the bytes type the F2P test actually uses, it would report a false disagreement. Does not affect the spec's faithfulness.

ENV NOTE (deliberately not scored as a spec defect, per the known failure mode where load/env breakage reads as spec weakness): conformance_check.py could not run in-place because the ambient interpreter is Python 3.10 while this is pytest 4.6 -- ModuleNotFoundError atomicwrites, then _pytest._py, then the 4.6 assertion rewriter dies with 'required field "lineno" missing from alias' on 3.10. Pure toolchain-version skew in my scratch env, unrelated to the specification; I worked around it with the direct module loader above and reproduced the real behavior fully.

CONCLUSION. The spec is not too strong in any behaviorally material way and does not drift from the real repo: on every one of 12,144 inputs spanning both argument types, invalid UTF-8, and the full py_major range, the three modeled functions agree exactly with the gold-patched create_new_paste's actual submitted fields, the discriminating mode-field claim is version-invariant in the real code, the prepatch twin is correctly rejected, and the only over-strength found (result freshness) is provably unobservable because the modeled repo values are immutable. No diverging input exists, so no FAITHFUL-is-a-defect claim is available. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL attacker 3 (leakage / gold-reconstruction) on pytest-dev__pytest-5809 (nagini). Verdict: NO-LEAKAGE.

ARTIFACT JUDGED. Rendered the actual consumer projection via swebench_unified.markers.spec_view(model.py, nagini) — model.py sha256 ea47ff21846697b804895ec619bf31da659436901f6d38c449a5b8c5c9aebbaa, matching the sha recorded in meta.json gates.G-LEAK.sources, so I judged the gated bytes. Projection is idempotent (spec_view(spec_view(x))==x); all three impl regions collapse to the elision placeholder. Confirmed only model.py feeds the consumer view (eval/adapter.py:273 model_src + :304 spec_view); model_prepatch.py, mapping.md and refinement.md are NOT consumer-visible — important here, because model_prepatch.py DOES narrate ("PRE-PATCH skeleton: the mode field is derived from the interpreter major version rather than being the fixed plain-text token") and mapping.md quotes the removed conditional verbatim. Both are audit-side artifacts, so neither can leak.

DECISIVE POINT — hints_text is EMPTY (repr ''), so the relaxed-leakage escape hatch is irrelevant and the strict standard applies with the problem_statement as the sole public baseline. That baseline is unusually generous: the PS explicitly states the entire gold edit in prose — "The call goes through fine if `lexer` is changed from `python3` to `text`" — naming the dict key (lexer), the old value (python3), the new value (text), AND the exact rationale the spec-view docstring reuses ("the console output of a `pytest` run that is being uploaded is not Python code, but arbitrary text"). The gold patch is precisely lexer: python3-conditional -> "text". So the spec view's central claim (mode field == the constant token "text", justified by the body being arbitrary console text rather than source code) is a strict subset of public information. Nothing left to reconstruct.

MECHANICAL CHECKS (all clean). Ran the real screen: swebench_unified.leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[] — reproducing meta.json G-LEAK status "pass" (not "relaxed"; no RELAXED_LEAKAGE.md present, correctly). Then verified each sub-rule by hand rather than trusting the aggregate:

(a) No gold changed line reproduced. Normalized all 6 added/removed lines of patch.diff against the normalized spec view: all 6 absent, including both the removed conditional and the added post-patch params line.

(b) No patched symbol echoed. _patch_changed_symbols(patch) = {create_new_paste}; spec-view identifiers are {paste_mode_field, paste_body_field, paste_expiry_field, text_token, expiry_token, py_major, contents} plus Nagini builtins. No collision; the model names are abstract field-role names, not repo names.

(c) No patched path / callee names. Grepped the spec view: 'lexer', 'python3', 'sys.version_info', 'version_info', 'pastebin', 'bpaste', 'create_new_paste', 'params', 'urlencode', 'urlopen', 'src/', '.py', and the F2P test name are ALL absent. Only '_pytest' hits, solely inside the instance-id string on docstring line 1 ("pytest-dev__pytest-5809") — an instance label the consumer already has as instance_id, carrying zero edit-localization.

(d) No bug/fix narration. 'fix', 'bug', 'patch', 'instead of', 'previously', 'used to', 'no longer' all absent. The docstring is framed as desired behaviour and says so explicitly ("stated as desired behaviour, not as an edit"). Notably the spec view never names the OLD token: 'python3'/'python2'/'"python"' do not appear, so the pre->post delta is not narrated even though the PS would have permitted it.

THE ONE ITEM I PRESSED HARDEST — the py_major parameter plus the emphatic version-invariance prose (docstring lines 16-18 and post-condition comment lines 58-59: "INVARIANT under the running interpreter's major version ... it is NOT derived from, and does not vary with, the interpreter version"). This is the only spec-view content whose motivation is visible in the pre-patch source but NOT spelled out in the PS: the PS quotes a permalink (d47b9d0) whose line 68 reads params = {"code": contents, "lexer": "python3", ...} with NO version conditional, whereas base_commit 8aba863 line 82 is the conditional form.

I confirmed d47b9d0 is not an ancestor of base_commit, so the PS snapshot genuinely differs from the code under edit, and the PS contains no version vocabulary at all ('version', 'version_info', 'interpreter', 'major', 'Python 2' all absent). I nonetheless judge this NON-LEAKING on three independent grounds. First, it leaks no secret: base_commit is itself a consumer-visible field in the agent view (eval/dataset.py as_dict), so the solver checks out the tree and reads the conditional at pastebin.py:82 directly — the pre-patch shape is public repo content, not gold-derived information.

Second, it is load-bearing spec surface, not decoration: py_major is the differential carrier that makes the contract reject the buggy behaviour, corroborated by G-DIFF (model_prepatch.py "verification failed") — quantifying "for every py_major, result == text_token()" is what a version-branching impl cannot satisfy. Deleting it to appease a leak reading would weaken the spec and hand attacker 1 a counterexample, which directive 6 explicitly does not ask for. Third, it states the abstract post-condition (the value is constant across an input) rather than the diagnosis or the edit — the permitted "element i of the result is f(...)" register, and the same it is NOT ... phrasing used across many sibling bundles (django-15368, matplotlib-23299, sympy-24661, sphinx-9461, django-16877).

GOLD-RECONSTRUCTION TEST. A consumer given only the spec view learns: three request fields; body = identity; expiry = constant "1week"; mode = constant "text" for all interpreter versions. Every one of these is already public — "1week" and "text" are both readable in the PS-linked snippet/prose, and the file/function to edit comes from mode-gated localization metadata, not from the spec view. The spec view narrows nothing beyond the PS. Residual observation, not a finding: the two unchanged fields (paste_body_field, paste_expiry_field) are modeled for hunk fidelity and mildly signal that the changed dict has exactly three entries — but that dict is verbatim in the PS-linked permalink, so it is public.

CONCLUSION: no line of the spec view leaks the gold edit beyond the public problem_statement. The strongest candidate (version-invariance prose) is public via base_commit, load-bearing for G-DIFF/spec strength, and phrased as behaviour rather than as the edit. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
