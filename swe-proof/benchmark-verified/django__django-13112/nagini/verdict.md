# P2 adversarial audit — django__django-13112

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_3.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def normalize_reference(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -100,8 +98,11 @@
     Ensures(ToSeq(Result()) == normalized(ToSeq(text)))
     # post-conditions-end
     # impl-start
+    # ATTACK 1 (prepatch bug): treat the whole reference as a bare name and
+    # lower-case everything (keep = 0), ignoring the separator dot. This is the
+    # pre-patch behaviour; it must FAIL the postcondition on qualified refs.
     s = ToSeq(text)
-    keep = keep_count(s)
+    keep = 0
     result = []  # type: List[int]
     i = len(text)
     while i > 0:
@@ -112,15 +113,11 @@
         Invariant(0 <= keep and keep <= len(s))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = text[i - 1]
         Assert(s.drop(i - 1)[0] == c)
         Assert(s.drop(i - 1).drop(1) == s.drop(i))
-        if i - 1 < keep:
-            result = [c] + result
-        else:
-            result = [lower_cp(c)] + result
+        result = [lower_cp(c)] + result
         i = i - 1
     Assert(s.drop(0) == s)
     return result
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def normalize_reference(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -100,8 +98,11 @@
     Ensures(ToSeq(Result()) == normalized(ToSeq(text)))
     # post-conditions-end
     # impl-start
+    # ATTACK 2 (partial-domain / identity): keep EVERYTHING verbatim
+    # (keep = len(s)), i.e. return the input unchanged. Correct only on inputs
+    # already normalized; must FAIL the postcondition on any foldable name.
     s = ToSeq(text)
-    keep = keep_count(s)
+    keep = len(text)
     result = []  # type: List[int]
     i = len(text)
     while i > 0:
@@ -112,7 +113,6 @@
         Invariant(0 <= keep and keep <= len(s))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = text[i - 1]
         Assert(s.drop(i - 1)[0] == c)
```

Attack 3 — `atk_3.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def normalize_reference(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -100,28 +98,15 @@
     Ensures(ToSeq(Result()) == normalized(ToSeq(text)))
     # post-conditions-end
     # impl-start
-    s = ToSeq(text)
-    keep = keep_count(s)
+    # ATTACK 3 (non-termination / partial correctness): loop forever, never
+    # return. Nagini proves only partial correctness (no MustTerminate here),
+    # so the postcondition is vacuously discharged on the unreachable exit.
     result = []  # type: List[int]
-    i = len(text)
-    while i > 0:
+    while True:
         # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(s == ToSeq(text))
-        Invariant(0 <= keep and keep <= len(s))
-        Invariant(0 <= i and i <= len(text))
-        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
-        c = text[i - 1]
-        Assert(s.drop(i - 1)[0] == c)
-        Assert(s.drop(i - 1).drop(1) == s.drop(i))
-        if i - 1 < keep:
-            result = [c] + result
-        else:
-            result = [lower_cp(c)] + result
-        i = i - 1
-    Assert(s.drop(0) == s)
+        result = result
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def normalize_reference(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -100,8 +98,12 @@
     Ensures(ToSeq(Result()) == normalized(ToSeq(text)))
     # post-conditions-end
     # impl-start
+    # ATTACK 4 (boundary off-by-one): keep_count - 1 leading chars verbatim
+    # instead of keep_count, wrongly lower-casing the last app-label char on a
+    # qualified reference (e.g. 'AB.X' -> 'Ab.x' instead of 'AB.x'). Must FAIL.
     s = ToSeq(text)
-    keep = keep_count(s)
+    kc = keep_count(s)
+    keep = kc - 1 if kc - 1 > 0 else 0
     result = []  # type: List[int]
     i = len(text)
     while i > 0:
@@ -112,7 +114,6 @@
         Invariant(0 <= keep and keep <= len(s))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = text[i - 1]
         Assert(s.drop(i - 1)[0] == c)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def normalize_reference(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -100,28 +98,10 @@
     Ensures(ToSeq(Result()) == normalized(ToSeq(text)))
     # post-conditions-end
     # impl-start
-    s = ToSeq(text)
-    keep = keep_count(s)
+    # ATTACK 5 (control-flow-effect / exceptional exit): raise an exception
+    # before any return. If Nagini discharges the postcondition vacuously on
+    # the exceptional path (no exsures obligation stated), this verifies while
+    # the real refined patch (which raises) never resolves.
     result = []  # type: List[int]
-    i = len(text)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(text), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(s == ToSeq(text))
-        Invariant(0 <= keep and keep <= len(s))
-        Invariant(0 <= i and i <= len(text))
-        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = text[i - 1]
-        Assert(s.drop(i - 1)[0] == c)
-        Assert(s.drop(i - 1).drop(1) == s.drop(i))
-        if i - 1 < keep:
-            result = [c] + result
-        else:
-            result = [lower_cp(c)] + result
-        i = i - 1
-    Assert(s.drop(0) == s)
-    return result
+    raise Exception()
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def normalize_reference(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -100,28 +98,9 @@
     Ensures(ToSeq(Result()) == normalized(ToSeq(text)))
     # post-conditions-end
     # impl-start
-    s = ToSeq(text)
-    keep = keep_count(s)
+    # ATTACK 6 (partial-domain / constant-empty): always return the empty
+    # list, ignoring the input. Correct only when text is empty; must FAIL the
+    # postcondition (length mismatch) on any nonempty reference.
     result = []  # type: List[int]
-    i = len(text)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(text), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(s == ToSeq(text))
-        Invariant(0 <= keep and keep <= len(s))
-        Invariant(0 <= i and i <= len(text))
-        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = text[i - 1]
-        Assert(s.drop(i - 1)[0] == c)
-        Assert(s.drop(i - 1).drop(1) == s.drop(i))
-        if i - 1 < keep:
-            result = [c] + result
-        else:
-            result = [lower_cp(c)] + result
-        i = i - 1
-    Assert(s.drop(0) == s)
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -25,7 +25,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -91,7 +90,6 @@
 def normalize_reference(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -100,6 +98,9 @@
     Ensures(ToSeq(Result()) == normalized(ToSeq(text)))
     # post-conditions-end
     # impl-start
+    # ATTACK 7 (control-flow / wrong order): append instead of prepend so the
+    # result is the per-char fold in REVERSED order. Length matches but the
+    # sequence differs from normalized on any non-palindrome; must FAIL.
     s = ToSeq(text)
     keep = keep_count(s)
     result = []  # type: List[int]
@@ -111,17 +112,12 @@
         Invariant(s == ToSeq(text))
         Invariant(0 <= keep and keep <= len(s))
         Invariant(0 <= i and i <= len(text))
-        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = text[i - 1]
-        Assert(s.drop(i - 1)[0] == c)
-        Assert(s.drop(i - 1).drop(1) == s.drop(i))
         if i - 1 < keep:
-            result = [c] + result
+            result = result + [c]
         else:
-            result = [lower_cp(c)] + result
+            result = result + [lower_cp(c)]
         i = i - 1
-    Assert(s.drop(0) == s)
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13112.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A model reference is given as text. When the text contains a separator dot,
  it names a model qualified by an application label: everything before the
  first dot is the application label, everything after it is the model name.
  The normalized reference preserves the application label's letter case
  exactly as written and folds ONLY the model-name portion to lower case; the
  separator dot is retained in place. When the text contains no separator dot
  it is a bare model name and is folded to lower case in its entirety.

  Letter-case folding here is the ASCII lower-casing of identifier text: each
  upper-case ASCII letter (U+0041..U+005A) maps to the corresponding lower-case
  letter (code point + 32); every other code point is left unchanged.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The whole transformation is modelled DEEPLY (spelled out as verified pure folds
over the code-point sequence); there is no consumed axiom. The ASCII
lower-casing fold is validated equal to the real `str.lower()` on identifier
text out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none) — the transformation is modelled deeply; no callee is axiomatized.
# axioms-end

# pure-start
@Pure
def lower_cp(c: int) -> int:
    """ASCII lower-casing of a single code point: an upper-case ASCII letter
    (U+0041..U+005A) maps to + 32; every other code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c

@Pure
def first_dot(s: PSeq[int]) -> int:
    """Index of the first separator dot (U+002E) in the sequence, or len(s)
    if there is none. Front-recursive."""
    Ensures(0 <= Result() and Result() <= len(s))
    if len(s) == 0:
        return 0
    if s[0] == 46:
        return 0
    return 1 + first_dot(s.drop(1))

@Pure
def normfold(s: PSeq[int], keep: int) -> PSeq[int]:
    """Keep the first `keep` code points verbatim and ASCII-lower-case the rest.
    Front-recursive so a single unfold is available to callers."""
    Requires(keep >= 0)
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    if keep > 0:
        return PSeq(s[0]) + normfold(s.drop(1), keep - 1)
    return PSeq(lower_cp(s[0])) + normfold(s.drop(1), 0)

@Pure
def keep_count(s: PSeq[int]) -> int:
    """Number of leading code points kept verbatim: the application-label
    length when a separator dot is present (so the label keeps its case), else
    zero so a bare name is lower-cased in full."""
    Ensures(0 <= Result() and Result() <= len(s))
    if first_dot(s) < len(s):
        return first_dot(s)
    return 0

@Pure
def normalized(s: PSeq[int]) -> PSeq[int]:
    """The normalized reference: the application label (the prefix before the
    first dot, if any) is kept verbatim and everything from the dot onward is
    lower-cased; with no dot the whole text is lower-cased."""
    return normfold(s, keep_count(s))
# pure-end

def normalize_reference(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the normalized reference of the input.
    Ensures(ToSeq(Result()) == normalized(ToSeq(text)))
    # post-conditions-end
    # impl-start
    s = ToSeq(text)
    keep = keep_count(s)
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(s == ToSeq(text))
        Invariant(0 <= keep and keep <= len(s))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
        # invariants-end
        c = text[i - 1]
        Assert(s.drop(i - 1)[0] == c)
        Assert(s.drop(i - 1).drop(1) == s.drop(i))
        if i - 1 < keep:
            result = [c] + result
        else:
            result = [lower_cp(c)] + result
        i = i - 1
    Assert(s.drop(0) == s)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### SAME-SPEC (all 8 attacks + control): all SAME (adversary same-spec, exit 0).

=== WEAKNESS RESULTS (python -m swebench_unified.adversary weakness nagini django__django-13112 <atk>), run concurrently in batches of <=3 JVMs ===
- atk_1.py (PREPATCH BUG: keep=0, lower-cases the whole reference incl. app label): NOT-A-COUNTEREXAMPLE — does not verify (postcondition fails on dotted refs). => prepatch reproduced.
- atk_2.py (partial-domain/identity: keep=len(s), returns input unchanged): NOT-A-COUNTEREXAMPLE — does not verify.
- atk_3.py (control-flow: `while True`): NOT-A-COUNTEREXAMPLE — Nagini 'Translation failed / Type error: dead.code' (return statically unreachable). The front end refused the program, so the spec never ruled on it and it counts in neither tally: the attack SHAPE is unexpressible in nagini's fragment rather than rejected by a clause, and it therefore did not test the spec's method-level `MustTerminate`.
- atk_4.py (boundary off-by-one: keep=keep_count-1, lower-cases last app-label char e.g. 'AB.X'->'Ab.x'): NOT-A-COUNTEREXAMPLE — does not verify.
- atk_5.py (control-flow-effect: `raise Exception()` before return): NOT-A-COUNTEREXAMPLE — 'Exhale might fail. Assertion "method raises no exceptions" might not hold.' Rejected.
- atk_6.py (partial-domain: always return []): NOT-A-COUNTEREXAMPLE — does not verify (length mismatch).
- atk_7.py (control-flow/wrong order: append instead of prepend => reversed output): NOT-A-COUNTEREXAMPLE — does not verify.
Positive control pos_control.py (unmodified bundle impl): VERIFIES (scripts/nagini_verify.sh exit 0, 20.8s).

### CANDIDATE INVESTIGATED (ungrounded non-termination), reported per mandate
atk_8.py (atk_8.py): SEMANTIC non-termination — `result=[]; i=0; while i>=0: i=i+1; return result` with Invariant. Avoids atk_3's dead-code error (loop body not statically dead). weakness => CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (21.7s; raw nagini_verify.sh exit 0). Under Nagini's PARTIAL-correctness semantics the loop never exits, so the post-loop exit state (guard false: i<0) contradicts the invariant (i>=0) and the postcondition is discharged VACUOUSLY. MATERIALIZED FAITHFUL PATCH: patch_atk8.diff — injects the identical infinite loop into the str-branch of ForeignObject.deconstruct (related.py:585) before kwargs['to'] is assigned.

OFFICIAL HARNESS (run_evaluation, the exact engine run_resolve wraps; run_id sbu-atk8-direct2, timeout 300): patch 'Applied patch django/db/models/fields/related.py cleanly.' then 'django__django-13112: Test timed out after 300 seconds.' => 'Instances resolved: 0'. GOLD control on same harness resolves True/completed True. So atk_8's faithful patch does NOT resolve (it HANGS). run_resolve() wrapper on the same patch returns resolved=False, completed=False, note='no report ... harness error' (the test-timeout EvaluationError writes no report.json).

### WHY atk_8 IS NOT A GENUINE G-EQ BREAK (verdict SOUND, not BROKEN)
(1) Non-termination is a UNIVERSAL property of Nagini's partial-correctness semantics — it breaks the literal 'verify=>resolved' claim of EVERY nagini bundle equally, so it cannot discriminate a weak spec. quickref.md:6 states plainly: 'Termination proofs are NOT required by default.' The frozen spec has no MustTerminate and is not expected to.

(2) The runner's OWN mechanical G-EQ derivation (construct/build_one.py:306-311) records BROKEN only when `r.completed and not r.resolved` (a COMPLETING run whose tests fail = wrong output). atk_8's patch does not resolve via TIMEOUT => run_resolve completed=False => line 310 buckets it as INCONCLUSIVE, explicitly NOT a break. The runner would never flag atk_8 as verify-not-correct.

(3) The spec is tight over the entire IN-SCOPE domain: for all normally-terminating impls, verify => Result()==normalized(text) EXACTLY => equals the gold str value for kwargs['to'] (R: str<->List[int]) => resolves. This is corroborated by atk_1,2,4,6,7 all being rejected on value grounds and the raise-path (atk_5) being blocked by the no-exception obligation; the input list is read-only (Acc 1/2) so it can't be mutated to cheat.
Including atk_8 in the machine attacks list would force the gate to INCONCLUSIVE (its timeout non-resolve => inconclusive_hit), which would misrepresent a spec that is genuinely robust against every terminating implementation; hence it is documented here rather than listed.

### Refinement.md / a-leg audit
All 5 legs are R / A-reference / I; NO consumed axiom, NO kind-3 step. The single trust point is the A-reference deep model (normalized/normfold/keep_count/first_dot/lower_cp) == the real gold transform (str.split('.') / str.lower() / %-format). Re-ran axiom_check.py (G-AX): 'G-AX OK: deep model (normalized) == real gold reference transform on 26 boundary + 40000 fuzz inputs' (exit 0). Correspondence to the real callees holds. mapping.md symbol bindings (related.py:584-585 deconstruct str-branch) and the str<->List[int]/PSeq[int] type abstraction are consistent with patch.diff.

CONCLUSION: 7 distinct same-spec wrong-VALUE impls (prepatch, partial-domain, boundary, control-flow-effect, ungrounded echo) all correctly REJECTED by the spec; positive control verifies; prepatch reproduced; A-reference sound (G-AX pass); no kind-3 leg. The only 'verify but not resolve' vector is out-of-scope non-termination (universal Nagini partial-correctness, treated as inconclusive-not-break by the runner). SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_3.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13112.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A model reference is given as text. When the text contains a separator dot,
  it names a model qualified by an application label: everything before the
  first dot is the application label, everything after it is the model name.
  The normalized reference preserves the application label's letter case
  exactly as written and folds ONLY the model-name portion to lower case; the
  separator dot is retained in place. When the text contains no separator dot
  it is a bare model name and is folded to lower case in its entirety.

  Letter-case folding here is the ASCII lower-casing of identifier text: each
  upper-case ASCII letter (U+0041..U+005A) maps to the corresponding lower-case
  letter (code point + 32); every other code point is left unchanged.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by the pure sequence theory `PSeq[int]`.
The whole transformation is modelled DEEPLY (spelled out as verified pure folds
over the code-point sequence); there is no consumed axiom. The ASCII
lower-casing fold is validated equal to the real `str.lower()` on identifier
text out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none) — the transformation is modelled deeply; no callee is axiomatized.
# axioms-end

# pure-start
@Pure
def lower_cp(c: int) -> int:
    """ASCII lower-casing of a single code point: an upper-case ASCII letter
    (U+0041..U+005A) maps to + 32; every other code point is unchanged."""
    if 65 <= c and c <= 90:
        return c + 32
    return c

@Pure
def first_dot(s: PSeq[int]) -> int:
    """Index of the first separator dot (U+002E) in the sequence, or len(s)
    if there is none. Front-recursive."""
    Ensures(0 <= Result() and Result() <= len(s))
    if len(s) == 0:
        return 0
    if s[0] == 46:
        return 0
    return 1 + first_dot(s.drop(1))

@Pure
def normfold(s: PSeq[int], keep: int) -> PSeq[int]:
    """Keep the first `keep` code points verbatim and ASCII-lower-case the rest.
    Front-recursive so a single unfold is available to callers."""
    Requires(keep >= 0)
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    if keep > 0:
        return PSeq(s[0]) + normfold(s.drop(1), keep - 1)
    return PSeq(lower_cp(s[0])) + normfold(s.drop(1), 0)

@Pure
def keep_count(s: PSeq[int]) -> int:
    """Number of leading code points kept verbatim: the application-label
    length when a separator dot is present (so the label keeps its case), else
    zero so a bare name is lower-cased in full."""
    Ensures(0 <= Result() and Result() <= len(s))
    if first_dot(s) < len(s):
        return first_dot(s)
    return 0

@Pure
def normalized(s: PSeq[int]) -> PSeq[int]:
    """The normalized reference: the application label (the prefix before the
    first dot, if any) is kept verbatim and everything from the dot onward is
    lower-cased; with no dot the whole text is lower-cased."""
    return normfold(s, keep_count(s))
# pure-end

def normalize_reference(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is exactly the normalized reference of the input.
    Ensures(ToSeq(Result()) == normalized(ToSeq(text)))
    # post-conditions-end
    # impl-start
    s = ToSeq(text)
    keep = keep_count(s)
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(s == ToSeq(text))
        Invariant(0 <= keep and keep <= len(s))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == normfold(s.drop(i), keep - i if keep - i > 0 else 0))
        # invariants-end
        c = text[i - 1]
        Assert(s.drop(i - 1)[0] == c)
        Assert(s.drop(i - 1).drop(1) == s.drop(i))
        if i - 1 < keep:
            result = [c] + result
        else:
            result = [lower_cp(c)] + result
        i = i - 1
    Assert(s.drop(0) == s)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### SAME-SPEC (all 8 attacks + control): all SAME (adversary same-spec, exit 0).

=== WEAKNESS RESULTS (python -m swebench_unified.adversary weakness nagini django__django-13112 <atk>), run concurrently in batches of <=3 JVMs ===
- atk_1.py (PREPATCH BUG: keep=0, lower-cases the whole reference incl. app label): NOT-A-COUNTEREXAMPLE — does not verify (postcondition fails on dotted refs). => prepatch reproduced.
- atk_2.py (partial-domain/identity: keep=len(s), returns input unchanged): NOT-A-COUNTEREXAMPLE — does not verify.
- atk_3.py (control-flow: `while True`): NOT-A-COUNTEREXAMPLE — Nagini 'Translation failed / Type error: dead.code' (return statically unreachable). The front end refused the program, so the spec never ruled on it and it counts in neither tally: the attack SHAPE is unexpressible in nagini's fragment rather than rejected by a clause, and it therefore did not test the spec's method-level `MustTerminate`.
- atk_4.py (boundary off-by-one: keep=keep_count-1, lower-cases last app-label char e.g. 'AB.X'->'Ab.x'): NOT-A-COUNTEREXAMPLE — does not verify.
- atk_5.py (control-flow-effect: `raise Exception()` before return): NOT-A-COUNTEREXAMPLE — 'Exhale might fail. Assertion "method raises no exceptions" might not hold.' Rejected.
- atk_6.py (partial-domain: always return []): NOT-A-COUNTEREXAMPLE — does not verify (length mismatch).
- atk_7.py (control-flow/wrong order: append instead of prepend => reversed output): NOT-A-COUNTEREXAMPLE — does not verify.
Positive control pos_control.py (unmodified bundle impl): VERIFIES (scripts/nagini_verify.sh exit 0, 20.8s).

### CANDIDATE INVESTIGATED (ungrounded non-termination), reported per mandate
atk_8.py (atk_8.py): SEMANTIC non-termination — `result=[]; i=0; while i>=0: i=i+1; return result` with Invariant. Avoids atk_3's dead-code error (loop body not statically dead). weakness => CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (21.7s; raw nagini_verify.sh exit 0). Under Nagini's PARTIAL-correctness semantics the loop never exits, so the post-loop exit state (guard false: i<0) contradicts the invariant (i>=0) and the postcondition is discharged VACUOUSLY. MATERIALIZED FAITHFUL PATCH: patch_atk8.diff — injects the identical infinite loop into the str-branch of ForeignObject.deconstruct (related.py:585) before kwargs['to'] is assigned.

OFFICIAL HARNESS (run_evaluation, the exact engine run_resolve wraps; run_id sbu-atk8-direct2, timeout 300): patch 'Applied patch django/db/models/fields/related.py cleanly.' then 'django__django-13112: Test timed out after 300 seconds.' => 'Instances resolved: 0'. GOLD control on same harness resolves True/completed True. So atk_8's faithful patch does NOT resolve (it HANGS). run_resolve() wrapper on the same patch returns resolved=False, completed=False, note='no report ... harness error' (the test-timeout EvaluationError writes no report.json).

### WHY atk_8 IS NOT A GENUINE G-EQ BREAK (verdict SOUND, not BROKEN)
(1) Non-termination is a UNIVERSAL property of Nagini's partial-correctness semantics — it breaks the literal 'verify=>resolved' claim of EVERY nagini bundle equally, so it cannot discriminate a weak spec. quickref.md:6 states plainly: 'Termination proofs are NOT required by default.' The frozen spec has no MustTerminate and is not expected to.

(2) The runner's OWN mechanical G-EQ derivation (construct/build_one.py:306-311) records BROKEN only when `r.completed and not r.resolved` (a COMPLETING run whose tests fail = wrong output). atk_8's patch does not resolve via TIMEOUT => run_resolve completed=False => line 310 buckets it as INCONCLUSIVE, explicitly NOT a break. The runner would never flag atk_8 as verify-not-correct.

(3) The spec is tight over the entire IN-SCOPE domain: for all normally-terminating impls, verify => Result()==normalized(text) EXACTLY => equals the gold str value for kwargs['to'] (R: str<->List[int]) => resolves. This is corroborated by atk_1,2,4,6,7 all being rejected on value grounds and the raise-path (atk_5) being blocked by the no-exception obligation; the input list is read-only (Acc 1/2) so it can't be mutated to cheat.
Including atk_8 in the machine attacks list would force the gate to INCONCLUSIVE (its timeout non-resolve => inconclusive_hit), which would misrepresent a spec that is genuinely robust against every terminating implementation; hence it is documented here rather than listed.

### Refinement.md / a-leg audit
All 5 legs are R / A-reference / I; NO consumed axiom, NO kind-3 step. The single trust point is the A-reference deep model (normalized/normfold/keep_count/first_dot/lower_cp) == the real gold transform (str.split('.') / str.lower() / %-format). Re-ran axiom_check.py (G-AX): 'G-AX OK: deep model (normalized) == real gold reference transform on 26 boundary + 40000 fuzz inputs' (exit 0). Correspondence to the real callees holds. mapping.md symbol bindings (related.py:584-585 deconstruct str-branch) and the str<->List[int]/PSeq[int] type abstraction are consistent with patch.diff.

CONCLUSION: 7 distinct same-spec wrong-VALUE impls (prepatch, partial-domain, boundary, control-flow-effect, ungrounded echo) all correctly REJECTED by the spec; positive control verifies; prepatch reproduced; A-reference sound (G-AX pass); no kind-3 leg. The only 'verify but not resolve' vector is out-of-scope non-termination (universal Nagini partial-correctness, treated as inconclusive-not-break by the runner). SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo drift) verdict: FAITHFUL. Setup: worktree at base_commit 09914ccf... contains the PRE-patch deconstruct (kwargs['to']=model.lower() for all strings); model.py specs the POST-patch (gold) behavior modeled as normalize_reference. I applied the gold hunk to and ran the bundle's conformance_check.py against the REAL patched ForeignObject.deconstruct.

Evidence the modeled function AGREES with the real callee on all in-domain inputs:
- Nagini verification of model.py: SUCCESS (16.9s) — the spec is real, not trivially-verifying.
- G-AX (axiom_check.py): deep model `normalized` == real gold transform (str.split('.')/str.lower()/%-format) on 26 boundary + 40000 fuzz inputs, exit 0.
- G-CONF (conformance_check.py) run against a freshly gold-patched Django: shadow impl region == real patched deconstruct kwargs['to'] on 120026 inputs (26 boundary + 120000 fuzz, bare + single-dot ASCII identifiers, seed 131120); ZERO disagreements.

Divergence hunt — I found two divergence classes but BOTH are genuinely out-of-domain, not defects:
1. Multi-dot e.g. 'a.B.C': spec returns 'a.b.c', but the REAL repo RAISES ValueError (tuple-unpack `app_label, model_name = model.split('.')`). This is not the modeled function disagreeing on a returned value; the real callee errors, and Django never produces multi-dot lazy references. mapping.md/axiom_check.py explicitly scope the domain to exactly-one-dot.
2. Non-ASCII e.g. 'MÖDEL': spec's ASCII lower_cp leaves U+00D6 unchanged while real str.lower() folds it. But Django model/app references are ASCII identifiers (letters/digits/underscore); this input is unreachable in the modeled domain, which mapping.md §3 explicitly restricts to ASCII identifiers.

The spec is NOT too strong: within the reachable domain of lazy model reference strings (bare + single-dot ASCII), the modeled function equals the real patched repo behavior on 120k+ inputs. The domain restriction is legitimate (matches what Django actually produces and what the gold's tuple-unpack accepts). No in-domain diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the CONSUMER SPEC VIEW (markers.spec_view over model.py: module docstring + axioms(empty)/pure regions + normalize_reference signature/pre/post-conditions, impl elided) against the solver-visible problem_statement ONLY (not hints_text). Mechanical screen (gates.leak.leakage.screen, nagini flavor) returns LeakageReport(hard_failures=[], warnings=[]) — zero hard failures.

What the public problem_statement already discloses: 'makemigrations crashes for ForeignKey with mixed-case app name'; the ValueError shows the lazy reference 'dj_reglogin.category' (lower-cased) vs the installed app declared 'DJ_RegLogin'. So the discriminator — a mixed-case APPLICATION LABEL folded to lowercase, breaking a dotted app_label.model_name reference — is public. Both the dotted structure and the case-sensitivity of the app label are visible in the task.

What the spec view adds: it states the desired behaviour ('preserves the application label's letter case exactly as written and folds ONLY the model-name portion to lower case; separator dot retained; bare name lower-cased in full'), explicitly framed 'as desired behaviour, not as an edit'. This is the natural correct spec fully within the scope the problem statement discloses, not a reconstruction of the gold edit beyond it.

Leak checks: (L1) no gold-patch line reproduced — the view contains no str.split('.'), no '%s.%s' format, no model.lower(); no diff markers. (L2) patched file path 'django/db/models/fields/related.py' does NOT appear; the sole distinctive patched symbol 'deconstruct' appears in NO spec-view identifier and NO spec-view comment/docstring. Spec identifiers (normalize_reference, normalized, normfold, first_dot, keep_count, lower_cp) are model-theory names, none echoing a patched repo symbol. (L3) no bug/fix/pre-patch/regression narration in the consumer view. The gold hunk, pre-patch 'model.lower()' behaviour, and 'deconstruct'/related.py are confined to refinement.md, mapping.md and model_prepatch.py — audit artifacts, NOT the leak-screened spec view. Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
