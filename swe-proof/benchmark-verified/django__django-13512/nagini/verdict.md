# P2 adversarial audit — django__django-13512

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -65,7 +64,6 @@
     # every code point is printable (>= U+0020): the tested domain
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                              text[k] >= 32), [[text[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -84,22 +82,19 @@
     body = []  # type: List[int]
     i = len(text)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(body)))
         Invariant(0 <= i and i <= len(text))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                                   text[k] >= 32), [[text[k]]])))
         Invariant(ToSeq(body) == json_string_body(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = text[i - 1]
-        Assert(ToSeq(text).drop(i - 1)[0] == c)
-        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
         if c == 34:
             body = [92, 34] + body
         elif c == 92:
             body = [92, 92] + body
+        elif c >= 128:
+            body = [92, 117] + body
         else:
             body = [c] + body
         i = i - 1
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -65,7 +64,6 @@
     # every code point is printable (>= U+0020): the tested domain
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                              text[k] >= 32), [[text[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -84,22 +82,15 @@
     body = []  # type: List[int]
     i = len(text)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(body)))
         Invariant(0 <= i and i <= len(text))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                                   text[k] >= 32), [[text[k]]])))
         Invariant(ToSeq(body) == json_string_body(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = text[i - 1]
-        Assert(ToSeq(text).drop(i - 1)[0] == c)
-        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
         if c == 34:
             body = [92, 34] + body
-        elif c == 92:
-            body = [92, 92] + body
         else:
             body = [c] + body
         i = i - 1
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -65,7 +64,6 @@
     # every code point is printable (>= U+0020): the tested domain
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                              text[k] >= 32), [[text[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -84,18 +82,13 @@
     body = []  # type: List[int]
     i = len(text)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(body)))
         Invariant(0 <= i and i <= len(text))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                                   text[k] >= 32), [[text[k]]])))
         Invariant(ToSeq(body) == json_string_body(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = text[i - 1]
-        Assert(ToSeq(text).drop(i - 1)[0] == c)
-        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
         if c == 34:
             body = [92, 34] + body
         elif c == 92:
@@ -103,6 +96,6 @@
         else:
             body = [c] + body
         i = i - 1
-    result = [34] + body + [34]
+    result = [34] + body
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -65,7 +64,6 @@
     # every code point is printable (>= U+0020): the tested domain
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                              text[k] >= 32), [[text[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -84,22 +82,17 @@
     body = []  # type: List[int]
     i = len(text)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(body)))
         Invariant(0 <= i and i <= len(text))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                                   text[k] >= 32), [[text[k]]])))
         Invariant(ToSeq(body) == json_string_body(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = text[i - 1]
-        Assert(ToSeq(text).drop(i - 1)[0] == c)
-        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
         if c == 34:
+            body = [92, 92] + body
+        elif c == 92:
             body = [92, 34] + body
-        elif c == 92:
-            body = [92, 92] + body
         else:
             body = [c] + body
         i = i - 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -65,7 +64,6 @@
     # every code point is printable (>= U+0020): the tested domain
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                              text[k] >= 32), [[text[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -84,18 +82,13 @@
     body = []  # type: List[int]
     i = len(text)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(body)))
         Invariant(0 <= i and i <= len(text))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                                   text[k] >= 32), [[text[k]]])))
         Invariant(ToSeq(body) == json_string_body(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         c = text[i - 1]
-        Assert(ToSeq(text).drop(i - 1)[0] == c)
-        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
         if c == 34:
             body = [92, 34] + body
         elif c == 92:
@@ -103,6 +96,6 @@
         else:
             body = [c] + body
         i = i - 1
-    result = [34] + body + [34]
+    result = [33] + body + [34]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -65,7 +64,6 @@
     # every code point is printable (>= U+0020): the tested domain
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                              text[k] >= 32), [[text[k]]])))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(text), 1 / 2))
@@ -82,27 +80,23 @@
     # post-conditions-end
     # impl-start
     body = []  # type: List[int]
-    i = len(text)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(text):
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(body)))
         Invariant(0 <= i and i <= len(text))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                                   text[k] >= 32), [[text[k]]])))
-        Invariant(ToSeq(body) == json_string_body(ToSeq(text).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        c = text[i - 1]
-        Assert(ToSeq(text).drop(i - 1)[0] == c)
-        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
+        Invariant(ToSeq(body) == json_string_body(ToSeq(text).take(i)))
+        c = text[i]
+        Assert(ToSeq(text).take(i + 1) == ToSeq(text).take(i) + PSeq(c))
         if c == 34:
-            body = [92, 34] + body
+            body = body + [92, 34]
         elif c == 92:
-            body = [92, 92] + body
+            body = body + [92, 92]
         else:
-            body = [c] + body
-        i = i - 1
+            body = body + [c, c]
+        i = i + 1
     result = [34] + body + [34]
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13512.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a textual value is serialised to its JSON-text rendering for display
  and editing, the resulting rendering must preserve every character of the
  text literally. Concretely, the rendering of a text scalar is an opening
  quotation mark, followed by the per-character JSON encoding of each code
  point of the text in order, followed by a closing quotation mark. The
  per-character encoding escapes only the two JSON-structural code points — the
  quotation mark (U+0022) becomes a backslash followed by a quotation mark, and
  the backslash (U+005C) becomes a doubled backslash — while EVERY other code
  point, INCLUDING every non-ASCII code point at or above U+0080 (e.g. CJK
  text, accented Latin letters, emoji), is emitted unchanged. Non-ASCII code
  points are therefore rendered as themselves, not transliterated into any
  ASCII-only surrogate form.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.
The modelled domain is the printable code points (>= U+0020), which is exactly
the domain of every tested input; the per-character encoding is spelled out
DEEPLY (`json_string_body`) and validated equal to the real serialiser by
axiom_check.py (G-AX), not consumed as an axiom — there is no consumed axiom in
this bundle.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def json_char(c: int) -> PSeq[int]:
    """JSON-text encoding of one printable code point (>= U+0020) when the
    serialiser is configured to keep non-ASCII text literal. The quotation
    mark and the backslash are the only escaped code points; everything else,
    including all non-ASCII code points, is emitted as itself."""
    if c == 34:        # '"'  -> '\"'
        return PSeq(92, 34)
    if c == 92:        # '\'  -> '\\'
        return PSeq(92, 92)
    return PSeq(c)


@Pure
def json_string_body(s: PSeq[int]) -> PSeq[int]:
    """Per-code-point JSON-text encoding of a whole sequence: concatenate the
    per-code-point encodings. Front-recursive so a single unfold is available
    to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return json_char(s[0]) + json_string_body(s.drop(1))
# pure-end


def json_render_text(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # every code point is printable (>= U+0020): the tested domain
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                             text[k] >= 32), [[text[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendering is a quotation mark, the per-code-point JSON encoding of
    # the text, then a closing quotation mark.
    Ensures(ToSeq(Result()) ==
            PSeq(34) + json_string_body(ToSeq(text)) + PSeq(34))
    # Discriminating clause: every non-ASCII code point (>= U+0080) is rendered
    # literally as itself (a single code point), never expanded into a longer
    # ASCII-only surrogate form.
    Ensures(Forall(int, lambda c: (Implies(c >= 128, json_char(c) == PSeq(c)),
                                    [[json_char(c)]])))
    # post-conditions-end
    # impl-start
    body = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(body)))
        Invariant(0 <= i and i <= len(text))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                                  text[k] >= 32), [[text[k]]])))
        Invariant(ToSeq(body) == json_string_body(ToSeq(text).drop(i)))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 34:
            body = [92, 34] + body
        elif c == 92:
            body = [92, 92] + body
        else:
            body = [c] + body
        i = i - 1
    result = [34] + body + [34]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE: django__django-13512 nagini. SOUND. Ran 6 distinct same-spec wrong impls through `python -m swebench_unified.adversary weakness nagini django__django-13512 <atk>`; ALL 6 came back NOT-A-COUNTEREXAMPLE (attack does not verify), so NO CANDIDATE arose and no run_resolve run was triggered (correct: resolve is only required for a verifying candidate). Positive control (unmodified model.py) verifies (nagini_verify.sh exit 0, 31.9s). G-AX axiom_check.py exit 0.

SPEC SHAPE: The postcondition pins the output EXACTLY: `ToSeq(Result()) == PSeq(34) + json_string_body(ToSeq(text)) + PSeq(34)` over the whole precondition domain (code points >= U+0020, which mapping.md documents = the entire tested-input domain). json_string_body/json_char is a DEEP model (spelled-out per-code-point fold), NOT a consumed axiom. Because the output is fully determined for every in-domain input, any impl that diverges from gold on any tested input cannot verify — leaving no room for a verifying-but-wrong impl.

### ATTACKS (all same-spec exit 0; all weakness exit 2 = rejected):
- atk_1: prepatch bug re-encoded (c>=128 -> [92,117] '\u' escape, i.e. ensure_ascii=True). FAILED to verify => G-DIFF confirmed, prepatch reproduced.
- atk_2: backslash not doubled (emit '\' literal). FAILED.
- atk_3: boundary/off-by-one — drop the closing quote (`[34]+body`). FAILED.
- atk_4: control-flow-effect — swap the two escape branches ('"'->\\, '\'->\"). FAILED.
- atk_5: ungrounded-oracle echo — wrong opening quote constant (33 instead of 34). FAILED.
- atk_6: control-flow-effect — forward loop over take(i), emit [c,c] for non-escaped chars (doubles every literal char). FAILED.

SAME-SPEC: positive_control + atk_1..6 all exit 0 (spec region byte-identical; only impl region edited).

REFINEMENT.MD AUDIT: legs are A1=R (str<->List[int]), A2/B1=A-reference (deep model json_string_body validated == json.dumps(s, ensure_ascii=False) by G-AX). No A-consumed leg, no kind-3 leg (§C). A-reference correspondence verified: gold patch (dataset) is exactly the two `ensure_ascii=False` edits at forms/fields.py:1261 and admin/utils.py:403 (+ `import json`), matching mapping.md/refinement.md; G-AX exit 0 confirms deep model == real callee over full 0x20-0xFFFF sweep + astral + 40k fuzz + F2P discriminators, incl. the c>=128-kept-literal discriminator on BOTH sides. Correspondence holds.

### Commands
- python -m swebench_unified.adversary same-spec nagini django__django-13512 <atk> => exit 0 for all
- python -m swebench_unified.adversary weakness nagini django__django-13512 <atk> => exit 2 for atk_1..6
- bash scripts/nagini_verify.sh positive_control.py => 'Verification successful' (31.88s)
- axiom_check.py (nagini-verifier python) => 'G-AX OK ...' exit 0

No verifying wrong impl exists => verify=>correct holds for this spec on the tested domain. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13512.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a textual value is serialised to its JSON-text rendering for display
  and editing, the resulting rendering must preserve every character of the
  text literally. Concretely, the rendering of a text scalar is an opening
  quotation mark, followed by the per-character JSON encoding of each code
  point of the text in order, followed by a closing quotation mark. The
  per-character encoding escapes only the two JSON-structural code points — the
  quotation mark (U+0022) becomes a backslash followed by a quotation mark, and
  the backslash (U+005C) becomes a doubled backslash — while EVERY other code
  point, INCLUDING every non-ASCII code point at or above U+0080 (e.g. CJK
  text, accented Latin letters, emoji), is emitted unchanged. Non-ASCII code
  points are therefore rendered as themselves, not transliterated into any
  ASCII-only surrogate form.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.
The modelled domain is the printable code points (>= U+0020), which is exactly
the domain of every tested input; the per-character encoding is spelled out
DEEPLY (`json_string_body`) and validated equal to the real serialiser by
axiom_check.py (G-AX), not consumed as an axiom — there is no consumed axiom in
this bundle.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def json_char(c: int) -> PSeq[int]:
    """JSON-text encoding of one printable code point (>= U+0020) when the
    serialiser is configured to keep non-ASCII text literal. The quotation
    mark and the backslash are the only escaped code points; everything else,
    including all non-ASCII code points, is emitted as itself."""
    if c == 34:        # '"'  -> '\"'
        return PSeq(92, 34)
    if c == 92:        # '\'  -> '\\'
        return PSeq(92, 92)
    return PSeq(c)


@Pure
def json_string_body(s: PSeq[int]) -> PSeq[int]:
    """Per-code-point JSON-text encoding of a whole sequence: concatenate the
    per-code-point encodings. Front-recursive so a single unfold is available
    to callers."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return json_char(s[0]) + json_string_body(s.drop(1))
# pure-end


def json_render_text(text: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # every code point is printable (>= U+0020): the tested domain
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                             text[k] >= 32), [[text[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendering is a quotation mark, the per-code-point JSON encoding of
    # the text, then a closing quotation mark.
    Ensures(ToSeq(Result()) ==
            PSeq(34) + json_string_body(ToSeq(text)) + PSeq(34))
    # Discriminating clause: every non-ASCII code point (>= U+0080) is rendered
    # literally as itself (a single code point), never expanded into a longer
    # ASCII-only surrogate form.
    Ensures(Forall(int, lambda c: (Implies(c >= 128, json_char(c) == PSeq(c)),
                                    [[json_char(c)]])))
    # post-conditions-end
    # impl-start
    body = []  # type: List[int]
    i = len(text)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(body)))
        Invariant(0 <= i and i <= len(text))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(text),
                                                  text[k] >= 32), [[text[k]]])))
        Invariant(ToSeq(body) == json_string_body(ToSeq(text).drop(i)))
        # invariants-end
        c = text[i - 1]
        Assert(ToSeq(text).drop(i - 1)[0] == c)
        Assert(ToSeq(text).drop(i - 1).drop(1) == ToSeq(text).drop(i))
        if c == 34:
            body = [92, 34] + body
        elif c == 92:
            body = [92, 92] + body
        else:
            body = [c] + body
        i = i - 1
    result = [34] + body + [34]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE: django__django-13512 nagini. SOUND. Ran 6 distinct same-spec wrong impls through `python -m swebench_unified.adversary weakness nagini django__django-13512 <atk>`; ALL 6 came back NOT-A-COUNTEREXAMPLE (attack does not verify), so NO CANDIDATE arose and no run_resolve run was triggered (correct: resolve is only required for a verifying candidate). Positive control (unmodified model.py) verifies (nagini_verify.sh exit 0, 31.9s). G-AX axiom_check.py exit 0.

SPEC SHAPE: The postcondition pins the output EXACTLY: `ToSeq(Result()) == PSeq(34) + json_string_body(ToSeq(text)) + PSeq(34)` over the whole precondition domain (code points >= U+0020, which mapping.md documents = the entire tested-input domain). json_string_body/json_char is a DEEP model (spelled-out per-code-point fold), NOT a consumed axiom. Because the output is fully determined for every in-domain input, any impl that diverges from gold on any tested input cannot verify — leaving no room for a verifying-but-wrong impl.

### ATTACKS (all same-spec exit 0; all weakness exit 2 = rejected):
- atk_1: prepatch bug re-encoded (c>=128 -> [92,117] '\u' escape, i.e. ensure_ascii=True). FAILED to verify => G-DIFF confirmed, prepatch reproduced.
- atk_2: backslash not doubled (emit '\' literal). FAILED.
- atk_3: boundary/off-by-one — drop the closing quote (`[34]+body`). FAILED.
- atk_4: control-flow-effect — swap the two escape branches ('"'->\\, '\'->\"). FAILED.
- atk_5: ungrounded-oracle echo — wrong opening quote constant (33 instead of 34). FAILED.
- atk_6: control-flow-effect — forward loop over take(i), emit [c,c] for non-escaped chars (doubles every literal char). FAILED.

SAME-SPEC: positive_control + atk_1..6 all exit 0 (spec region byte-identical; only impl region edited).

REFINEMENT.MD AUDIT: legs are A1=R (str<->List[int]), A2/B1=A-reference (deep model json_string_body validated == json.dumps(s, ensure_ascii=False) by G-AX). No A-consumed leg, no kind-3 leg (§C). A-reference correspondence verified: gold patch (dataset) is exactly the two `ensure_ascii=False` edits at forms/fields.py:1261 and admin/utils.py:403 (+ `import json`), matching mapping.md/refinement.md; G-AX exit 0 confirms deep model == real callee over full 0x20-0xFFFF sweep + astral + 40k fuzz + F2P discriminators, incl. the c>=128-kept-literal discriminator on BOTH sides. Correspondence holds.

### Commands
- python -m swebench_unified.adversary same-spec nagini django__django-13512 <atk> => exit 0 for all
- python -m swebench_unified.adversary weakness nagini django__django-13512 <atk> => exit 2 for atk_1..6
- bash scripts/nagini_verify.sh positive_control.py => 'Verification successful' (31.88s)
- axiom_check.py (nagini-verifier python) => 'G-AX OK ...' exit 0

No verifying wrong impl exists => verify=>correct holds for this spec on the tested domain. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real repo behavior) CONFIRMED for django__django-13512/nagini.

The modeled function `json_render_text` (via the deep model `json_char`/`json_string_body`, output `'"' + body + '"'`) is the twin of the real callee the gold patch invokes: `json.dumps(value, ensure_ascii=False, cls=...)` on a text scalar (forms/fields.py:1261 and admin/utils.py:403). Domain is restricted by `Requires(text[k] >= 32)` to printable code points (>= U+0020), which is exactly the tested F2P domain.

Independent verification (not relying on the bundle's axiom_check.py):
1. Full single-code-point sweep U+0020..U+10FFFF (incl. surrogates 0xD800/0xDFFF, DEL 0x7F, astral) comparing model_render(chr(c)) vs [ord(x) for x in json.dumps(chr(c), ensure_ascii=False)]: 0 divergences.
2. 200,000 multi-char fuzz strings over an adversarial pool (", \, controls-adjacent, CJK, surrogates, astral, DEL, 0xFEFF): 0 divergences.
3. Boundary set (0x7f,0x80,0x9f,0xa0,0xad,0x200b,0x2028,0x2029,0xfeff): 0 divergences.

Real `ensure_ascii=False` escapes only " , \ , and control chars < U+0020 (ESCAPE = r'[\x00-\x1f\\"]'). On the modeled domain (>= U+0020) the only escapes are "->\" (34->[92,34]) and \->\\ (92->[92,92]), exactly what json_char encodes; every other code point (incl. all non-ASCII >= U+0080) maps to itself, matching the discriminating clause `json_char(c)==PSeq(c)` for c>=128. `cls=encoder` is identity on a plain text scalar and does not affect string serialization.

Supporting facts: model verifies under pinned Nagini (Verification successful, 13.4s); the bundle's G-AX axiom_check.py passes and is genuinely loud (F2P discriminators '你好 世界', '你好，世界', '😀🐱', 'jaźń' asserted, not skipped) with full BMP sweep + astral + 40k fuzz.

The spec is neither too strong nor drifted: within its declared (and tested) domain the modeled function agrees with the real repo callee on every input. No diverging input exists. Spec region markers are consistent with the model.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures). Independent adversarial review of the spec view against the PUBLIC problem_statement (not hints_text) confirms no leakage of the gold edit.

Gold edit: add `ensure_ascii=False` to json.dumps in JSONField.prepare_value (django/forms/fields.py) and the JSONField branch of display_for_field (django/contrib/admin/utils.py:403, replacing field.get_prep_value(value)).

Public problem_statement already fully discloses the target behavior: it shows `json.dumps('中国')` -> `"中国"`, states 'json.dumps use ASCII encoding by default when serializing Chinese', and complains that a JSONField with Chinese chars in Django admin 'will appear in ASCII characters' — i.e. the desired fix is to render non-ASCII text literally. So the solver-visible task itself already demands: keep non-ASCII code points literal instead of \uXXXX transliteration.

Spec view (model.py docstring + json_char/json_string_body/json_render_text contracts) describes exactly this behavior as DESIRED behavior, not as an edit: rendering = quote + per-code-point JSON encoding + quote, escaping only U+0022 and U+005C, every other code point (incl. all >= U+0080, CJK/emoji/accented Latin) emitted unchanged and never expanded into an ASCII-only surrogate. This is a faithful behavioral restatement of the already-public requirement.

Leakage checks beyond the public statement, all clean:
- No diff markers, no reproduced gold-patch line, and the discriminating keyword `ensure_ascii` never appears.
- No patched file paths (forms/fields.py, admin/utils.py) or dotted module paths in the spec view.
- No patched repo symbols surfaced: spec-view identifiers are json_render_text/json_char/json_string_body/text/s/c — none echo prepare_value, display_for_field, get_prep_value, or JSONField. (Those symbols DO appear in mapping.md, but mapping.md is the audit-view, not the consumer spec view.)
- No bug/fix/patch narration in comments; the JSON escaping rules ('"'->'\"', '\'->'\\') are standard JSON semantics, not edit-localizing.
- impl region is elided ('implementation elided — supplied by the consumer'); the solver must still discover WHERE (which two call sites) and HOW (ensure_ascii=False) — none of that is revealed.

The spec pins the same non-ASCII-literal behavior the problem statement already requires, at behavioral altitude, without revealing the edit location or mechanism. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
