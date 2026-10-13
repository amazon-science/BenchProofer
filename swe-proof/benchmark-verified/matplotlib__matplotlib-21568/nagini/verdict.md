# P2 adversarial audit — matplotlib__matplotlib-21568

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
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
 def protect_codepoints(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -109,17 +107,12 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
         Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
         if c == 45:
             result = [123, 45, 125] + result
-        elif c == 58:
-            result = [123, 58, 125] + result
-        elif c == 32:
-            result = [92, 59] + result
         else:
             result = [c] + result
         i = i - 1
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
 def protect_codepoints(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -109,14 +107,11 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
         Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
-        if c == 45:
-            result = [123, 45, 125] + result
-        elif c == 58:
+        if c == 58:
             result = [123, 58, 125] + result
         elif c == 32:
             result = [92, 59] + result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
 def protect_codepoints(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -102,14 +100,13 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(text)
+    i = len(text) - 1 if len(text) > 0 else 0
     while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
 def protect_codepoints(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -109,7 +107,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
@@ -119,7 +116,7 @@
         elif c == 58:
             result = [123, 58, 125] + result
         elif c == 32:
-            result = [92, 59] + result
+            result = [92] + result
         else:
             result = [c] + result
         i = i - 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
 def protect_codepoints(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -102,26 +100,24 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(text)
-    while i > 0:
+    i = 0
+    while i < len(text):
         # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
-        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
+        Invariant(ToSeq(result) == protected_seq(ToSeq(text).take(i)))
         # invariants-end
-        c = text[i - 1]
-        Assert(ToSeq(text).drop(i - 1)[0] == c)
-        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
+        c = text[i]
+        Assert(ToSeq(text).take(i + 1) == ToSeq(text).take(i) + PSeq(c))
         if c == 45:
-            result = [123, 45, 125] + result
+            result = result + [123, 45, 125]
         elif c == 58:
-            result = [123, 58, 125] + result
+            result = result + [123, 58, 125]
         elif c == 32:
-            result = [92, 59] + result
+            result = result + [92, 59]
         else:
-            result = [c] + result
-        i = i - 1
+            result = result + [c]
+        i = i + 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
 def protect_codepoints(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -109,7 +107,6 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         c = text[i - 1]
         Assert(ToSeq(text).drop(i - 1)[0] == c)
@@ -117,7 +114,7 @@
         if c == 45:
             result = [123, 45, 125] + result
         elif c == 58:
-            result = [123, 58, 125] + result
+            result = [123, 58] + result
         elif c == 32:
             result = [92, 59] + result
         else:
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -86,7 +85,6 @@
 def protect_codepoints(text: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(text), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -102,26 +100,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = len(text)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(text), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(text))
-        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = text[i - 1]
-        Assert(ToSeq(text).drop(i - 1)[0] == c)
-        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
-        if c == 45:
-            result = [123, 45, 125] + result
-        elif c == 58:
-            result = [123, 58, 125] + result
-        elif c == 32:
-            result = [92, 59] + result
-        else:
-            result = [c] + result
-        i = i - 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-21568.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a tick label is rendered in math mode, the literal characters that a
  math renderer would otherwise typeset as spaced binary operators or as
  inter-token gaps must be neutralised so the label keeps the same visual
  spacing as a plain-text label. Three code points need this protection:

    * the hyphen-minus U+002D is wrapped in braces  ->  `{-}`
    * the colon       U+003A is wrapped in braces    ->  `{:}`
    * the space       U+0020 is replaced by a thin    ->  `\\;`
      non-breaking math space so adjacent numbers do not run together.

  Every other code point passes through unchanged. The protection is a
  per-code-point substitution: element i of the result is the constant
  expansion of element i of the input (a length-3 token for the hyphen-minus
  and the colon, a length-2 token for the space, the singleton for any other
  code point), concatenated in order.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

The substitution is the operation under specification; it is modelled DEEPLY as
a verified per-code-point fold (`protected_seq`), whose equality to the real
math-mode neutralisation is checked out-of-band by axiom_check.py (G-AX), not
consumed as an axiom. There is no consumed `@ContractOnly` callee: the proof is
self-contained.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none — the modeled operation is a self-contained per-code-point substitution;
#  no unchanged opaque callee is consumed in the proof.)
# axioms-end

# pure-start
@Pure
def tok_dash() -> PSeq[int]:
    # '{-}'  = '{' '-' '}'
    return PSeq(123, 45, 125)

@Pure
def tok_colon() -> PSeq[int]:
    # '{:}'  = '{' ':' '}'
    return PSeq(123, 58, 125)

@Pure
def tok_space() -> PSeq[int]:
    # '\;'   = '\\' ';'
    return PSeq(92, 59)

@Pure
def protect(c: int) -> PSeq[int]:
    """Protected expansion of a single code point: the three math-significant
    code points expand to a constant token, every other code point maps to the
    singleton containing itself."""
    if c == 45:        # '-'
        return tok_dash()
    if c == 58:        # ':'
        return tok_colon()
    if c == 32:        # ' '
        return tok_space()
    return PSeq(c)

@Pure
def protected_seq(s: PSeq[int]) -> PSeq[int]:
    """The protection of a whole sequence: concatenate the per-code-point
    expansions. Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return protect(s[0]) + protected_seq(s.drop(1))
# pure-end

def protect_codepoints(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The protected output is the per-code-point math-space substitution.
    Ensures(ToSeq(Result()) == protected_seq(ToSeq(text)))
    # The three protected code points expand to their constant brace/space
    # tokens; in particular the colon and the space are protected (the
    # discriminating cases) alongside the hyphen-minus.
    Ensures(protect(45) == tok_dash())
    Ensures(protect(58) == tok_colon())
    Ensures(protect(32) == tok_space())
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 45:
            result = [123, 45, 125] + result
        elif c == 58:
            result = [123, 58, 125] + result
        elif c == 32:
            result = [92, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle: matplotlib__matplotlib-21568/nagini. Project root env sourced from experiments/regate/keepalive.sh (SBU_PYTHON=python; adversary invoked as `python -m swebench_unified.adversary ...`).

SPEC STRENGTH (why no wrong impl verifies): the postcondition `Ensures(ToSeq(Result()) == protected_seq(ToSeq(text)))` is TOTAL over the whole precondition domain (Requires is only read-access to any List[int]) and pins the abstract output EXACTLY as the deep per-code-point fold, plus three clauses pinning protect(45)/protect(58)/protect(32) to their tokens. Any verifying impl is therefore functionally identical to gold => verify=>correct on this bundle. No spec-too-weak surface exists.

atk_1 prepatch bug (only '-' protected, ':'/' ' dropped) => weakness exit 2 NOT-A-COUNTEREXAMPLE; direct nagini_verify: 'Loop invariant might not be preserved. (ToSeq(result) == protected_seq(ToSeq(text).drop(i)))'. Prepatch bug reproduced (matches model_prepatch.py which fails the postcondition). atk_2 partial-domain (drop '-' protection, keep ':'/' ') => exit 2 (does not verify). atk_3 boundary off-by-one (start i=len-1, drops last char) => exit 2. atk_4 control-flow-effect (space token [92] only, missing ';'=59) => exit 2; invariant fails. atk_5 ungrounded-oracle echo (functionally CORRECT but rewritten as a forward append loop with take(i) invariant) => exit 2 (proof-strength, still no candidate). atk_6 colon token wrong ([123,58], missing closing '}'=125) => exit 2. atk_7 empty output (return []) extreme partial-domain => exit 2; direct verify: 'Postcondition of protect_codepoints might not hold.

(ToSeq(Result()) == protected_seq(ToSeq(text)))'. All 7 are genuine verification FAILURES (verify_completed true — summary 'verification failed', not 'verifier timed out'), landing exactly on the spec-carrying postcondition/invariant. ZERO CANDIDATES => no verifying wrong impl => no faithful refined patch to materialize/run_resolve (per protocol step 2, run_resolve is only required for verifying candidates; none exist). patches={} accordingly.

POSITIVE CONTROL: shipped model.py copied verbatim => nagini_verify.sh exit 0 ('Verification successful', 13.3s); adversary same-spec exit 0.

A-LEG / MODEL-CORRESPONDENCE AUDIT (focus of this pass): same_spec compares the spec_view (everything except the elided impl region) byte-for-byte; every attack edited ONLY lines between `# impl-start` and `# impl-end`, leaving axioms/@Pure/Requires/Ensures/Invariant untouched — all 7 same-spec exit 0. refinement.md legs: A1=R (str<->List[int] code points, G-CONF/G-CONF-covered), A2=I (unchanged regex framing `re.sub(r'([a-zA-Z]+)',...)`, introduces only framing chars none of which are '-'/':'/'  '), A3=A-REFERENCE (the changed .replace('-','{-}').replace(':','{:}').replace(' ',r'\;') chain modeled DEEPLY by protected_seq/protect; NO @ContractOnly consumed), A4=I (unchanged `$\mathdefault{...}$` wrap + empty-fragment strip).

No A-consumed axiom, NO kind-3 step — every leg is R / A-reference / I, as claimed. G-AX (axiom_check.py) run: exit 0 — 'protected_seq deep model == gold _wrap_in_tex protection sound on 26 boundary + 20000 fuzz inputs; end-to-end deep-model framing == gold on 37 boundary + 5000 fuzz labels'. Confirms the A-reference correspondence to the real callee holds. Independent re-check of the A3 disjointness/framing claim on adversarial collision inputs ('{-}','{:}','\;',pre-braced,backslash/brace collisions, '$\mathdefault{}$'): real .replace chain == deep model on all; regex framing never adds/removes a protected code point ('-'/':'/space) on any tested label — 0 mismatches.

CONCLUSION: verify(model) => behaviourally equal to gold on the tested inputs => resolves (G-RESOLVE, gold patch.diff verbatim). No verify-but-incorrect impl found across 7 distinct wrong-impl classes; refinement fidelity and the single A-reference both hold. Verdict SOUND (advisory; runner re-runs the artifacts).

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
"""Twin-artifact model for matplotlib__matplotlib-21568.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a tick label is rendered in math mode, the literal characters that a
  math renderer would otherwise typeset as spaced binary operators or as
  inter-token gaps must be neutralised so the label keeps the same visual
  spacing as a plain-text label. Three code points need this protection:

    * the hyphen-minus U+002D is wrapped in braces  ->  `{-}`
    * the colon       U+003A is wrapped in braces    ->  `{:}`
    * the space       U+0020 is replaced by a thin    ->  `\\;`
      non-breaking math space so adjacent numbers do not run together.

  Every other code point passes through unchanged. The protection is a
  per-code-point substitution: element i of the result is the constant
  expansion of element i of the input (a length-3 token for the hyphen-minus
  and the colon, a length-2 token for the space, the singleton for any other
  code point), concatenated in order.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

The substitution is the operation under specification; it is modelled DEEPLY as
a verified per-code-point fold (`protected_seq`), whose equality to the real
math-mode neutralisation is checked out-of-band by axiom_check.py (G-AX), not
consumed as an axiom. There is no consumed `@ContractOnly` callee: the proof is
self-contained.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
# (none — the modeled operation is a self-contained per-code-point substitution;
#  no unchanged opaque callee is consumed in the proof.)
# axioms-end

# pure-start
@Pure
def tok_dash() -> PSeq[int]:
    # '{-}'  = '{' '-' '}'
    return PSeq(123, 45, 125)

@Pure
def tok_colon() -> PSeq[int]:
    # '{:}'  = '{' ':' '}'
    return PSeq(123, 58, 125)

@Pure
def tok_space() -> PSeq[int]:
    # '\;'   = '\\' ';'
    return PSeq(92, 59)

@Pure
def protect(c: int) -> PSeq[int]:
    """Protected expansion of a single code point: the three math-significant
    code points expand to a constant token, every other code point maps to the
    singleton containing itself."""
    if c == 45:        # '-'
        return tok_dash()
    if c == 58:        # ':'
        return tok_colon()
    if c == 32:        # ' '
        return tok_space()
    return PSeq(c)

@Pure
def protected_seq(s: PSeq[int]) -> PSeq[int]:
    """The protection of a whole sequence: concatenate the per-code-point
    expansions. Front-recursive so a single unfold is available to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return protect(s[0]) + protected_seq(s.drop(1))
# pure-end

def protect_codepoints(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The protected output is the per-code-point math-space substitution.
    Ensures(ToSeq(Result()) == protected_seq(ToSeq(text)))
    # The three protected code points expand to their constant brace/space
    # tokens; in particular the colon and the space are protected (the
    # discriminating cases) alongside the hyphen-minus.
    Ensures(protect(45) == tok_dash())
    Ensures(protect(58) == tok_colon())
    Ensures(protect(32) == tok_space())
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(result) == protected_seq(ToSeq(text).drop(i)))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 45:
            result = [123, 45, 125] + result
        elif c == 58:
            result = [123, 58, 125] + result
        elif c == 32:
            result = [92, 59] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle: matplotlib__matplotlib-21568/nagini. Project root env sourced from experiments/regate/keepalive.sh (SBU_PYTHON=python; adversary invoked as `python -m swebench_unified.adversary ...`).

SPEC STRENGTH (why no wrong impl verifies): the postcondition `Ensures(ToSeq(Result()) == protected_seq(ToSeq(text)))` is TOTAL over the whole precondition domain (Requires is only read-access to any List[int]) and pins the abstract output EXACTLY as the deep per-code-point fold, plus three clauses pinning protect(45)/protect(58)/protect(32) to their tokens. Any verifying impl is therefore functionally identical to gold => verify=>correct on this bundle. No spec-too-weak surface exists.

atk_1 prepatch bug (only '-' protected, ':'/' ' dropped) => weakness exit 2 NOT-A-COUNTEREXAMPLE; direct nagini_verify: 'Loop invariant might not be preserved. (ToSeq(result) == protected_seq(ToSeq(text).drop(i)))'. Prepatch bug reproduced (matches model_prepatch.py which fails the postcondition). atk_2 partial-domain (drop '-' protection, keep ':'/' ') => exit 2 (does not verify). atk_3 boundary off-by-one (start i=len-1, drops last char) => exit 2. atk_4 control-flow-effect (space token [92] only, missing ';'=59) => exit 2; invariant fails. atk_5 ungrounded-oracle echo (functionally CORRECT but rewritten as a forward append loop with take(i) invariant) => exit 2 (proof-strength, still no candidate). atk_6 colon token wrong ([123,58], missing closing '}'=125) => exit 2. atk_7 empty output (return []) extreme partial-domain => exit 2; direct verify: 'Postcondition of protect_codepoints might not hold.

(ToSeq(Result()) == protected_seq(ToSeq(text)))'. All 7 are genuine verification FAILURES (verify_completed true — summary 'verification failed', not 'verifier timed out'), landing exactly on the spec-carrying postcondition/invariant. ZERO CANDIDATES => no verifying wrong impl => no faithful refined patch to materialize/run_resolve (per protocol step 2, run_resolve is only required for verifying candidates; none exist). patches={} accordingly.

POSITIVE CONTROL: shipped model.py copied verbatim => nagini_verify.sh exit 0 ('Verification successful', 13.3s); adversary same-spec exit 0.

A-LEG / MODEL-CORRESPONDENCE AUDIT (focus of this pass): same_spec compares the spec_view (everything except the elided impl region) byte-for-byte; every attack edited ONLY lines between `# impl-start` and `# impl-end`, leaving axioms/@Pure/Requires/Ensures/Invariant untouched — all 7 same-spec exit 0. refinement.md legs: A1=R (str<->List[int] code points, G-CONF/G-CONF-covered), A2=I (unchanged regex framing `re.sub(r'([a-zA-Z]+)',...)`, introduces only framing chars none of which are '-'/':'/'  '), A3=A-REFERENCE (the changed .replace('-','{-}').replace(':','{:}').replace(' ',r'\;') chain modeled DEEPLY by protected_seq/protect; NO @ContractOnly consumed), A4=I (unchanged `$\mathdefault{...}$` wrap + empty-fragment strip).

No A-consumed axiom, NO kind-3 step — every leg is R / A-reference / I, as claimed. G-AX (axiom_check.py) run: exit 0 — 'protected_seq deep model == gold _wrap_in_tex protection sound on 26 boundary + 20000 fuzz inputs; end-to-end deep-model framing == gold on 37 boundary + 5000 fuzz labels'. Confirms the A-reference correspondence to the real callee holds. Independent re-check of the A3 disjointness/framing claim on adversarial collision inputs ('{-}','{:}','\;',pre-braced,backslash/brace collisions, '$\mathdefault{}$'): real .replace chain == deep model on all; regex framing never adds/removes a protected code point ('-'/':'/space) on any tested label — 0 mismatches.

CONCLUSION: verify(model) => behaviourally equal to gold on the tested inputs => resolves (G-RESOLVE, gold patch.diff verbatim). No verify-but-incorrect impl found across 7 distinct wrong-impl classes; refinement fidelity and the single A-reference both hold. Verdict SOUND (advisory; runner re-runs the artifacts).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 faithfulness audit for matplotlib__matplotlib-21568 (nagini). Spec region byte-identical; model verifies (Nagini exit 0, 18.6s). The modeled operation protected_seq/protect (per-code-point substitution: '-'->[123,45,125], ':'->[123,58,125], ' '->[92,59], else singleton) was checked against the REAL post-patch callee _wrap_in_tex |mpl_overlay|mpl25311_test/matplotlib/dates.py (all three identical). Differential results: (1) isolated protection chain protected_seq == real .replace('-','{-}').replace(':','{:}').replace(' ',r'\;') — EXHAUSTIVE over all strings length<=3 on adversarial alphabet incl {,},backslash,;,em-dash,control chars = 0 divergences; 200k full-Unicode fuzz = 0 divergences. (2) End-to-end model+framing == gold _wrap_in_tex on 200k fuzz labels (incl alpha runs exercising the regex) = 0 divergences, matching axiom_check's own claim. The three .replace targets are disjoint and no replacement output contains another target, so the sequential chain is exactly the per-code-point map with no interference; the unchanged regex introduces only framing chars (}$\mathdefault{) that are never protected code points, so modeling the substitution over the protected-code-point alphabet is faithful. No diverging input found — the spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Properly-dispositioned relaxed-leakage bundle (meta.json relaxed_leakage=true, RELAXED_LEAKAGE.md present, G-LEAK status=relaxed). Independently re-verified, not rubber-stamped: (1) same_spec=TRUE — model.py spec region (axioms/pure/pre/post/invariants) byte-identical to model_prepatch.py, only impl differs; confirmed by the same-spec command (exit 0) and direct diff of the pre..impl-start region. (2) Core soundness intact — all of G-VERIFY/G-DIFF/G-EQ/G-AX/G-RESOLVE/G-PANEL-1/2 pass; G-DIFF genuinely fails the prepatch (which protects only '-') on the postcondition ToSeq(Result())==protected_seq(ToSeq(text)), so the spec truly senses the colon/space delta. (3) Unavoidability re-derived — problem_statement reports only the 'unclear datetime axis with usetex spacing' symptom and names none of the three code points, the {-}/{:}/\; tokens, _wrap_in_tex, mathdefault, or the .replace mechanism; the fix vocabulary lives only in hints_text/test_patch. A faithful G-DIFF-failing spec MUST pin the colon and space protection (the pre-patch already had '-'), so faithful+non-leaking is impossible: a genuine problem_statement<->gold mismatch, not lazy de-narration. (4) No NEW leak beyond the dispositioned facet — grep over the spec view (model.py) finds no _wrap_in_tex, dates.py, mathdefault, .replace, re.sub, or patch/diff/gold/base_commit narration; only the dispositioned per-code-point protection-substitution vocabulary (docstring code points, tok_dash/tok_colon/tok_space, protect(45/58/32) postconditions) is present, which is the gold's tested discriminator the disposition explicitly covers. Model identifiers (protect_codepoints, protected_seq) describe behavior, not the edit. Per RELAXED_LEAKAGE.md / gates/_audit.py panel convention, a dispositioned relaxed leak records as NO-LEAKAGE (pass) + note; LEAKAGE reserved for a new leak beyond the facet or a broken disposition, neither of which is present.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `model.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
