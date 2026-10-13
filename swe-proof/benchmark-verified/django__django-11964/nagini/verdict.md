# P2 adversarial audit — django__django-11964

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prefix.py`, `atk_2_qualified.py`, `atk_3_empty.py`, `atk_4_skipfirst.py`, `atk_5_double.py`, `atk_7_constant.py`, `atk_8_reverse.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prefix.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,7 +86,7 @@
     # impl-start
     result = []  # type: List[int]
     i = 0
-    while i < len(self.value_text):
+    while i < len(self.value_text) - 1:
         # invariants-start
         Invariant(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
         Invariant(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
```

Attack 2 — `atk_2_qualified.py` → rejected (same spec, does not verify — good)

```diff
@@ -86,7 +86,7 @@
     # impl-start
     result = []  # type: List[int]
     i = 0
-    while i < len(self.value_text):
+    while i < len(self.qualified_label):
         # invariants-start
         Invariant(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
         Invariant(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
@@ -97,11 +97,11 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.qualified_label),
                                                   self.qualified_label[k] == Old(self.qualified_label[k])))))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(self.value_text))
+        Invariant(0 <= i and i <= len(self.qualified_label))
         Invariant(len(result) == i)
-        Invariant(ToSeq(result) == ToSeq(self.value_text).take(i))
+        Invariant(ToSeq(result) == ToSeq(self.qualified_label).take(i))
         # invariants-end
-        result.append(self.value_text[i])
+        result.append(self.qualified_label[i])
         i = i + 1
     return result
     # impl-end
```

Attack 3 — `atk_3_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,23 +85,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(self.value_text):
-        # invariants-start
-        Invariant(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
-        Invariant(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
-        Invariant(len(self.value_text) == Old(len(self.value_text)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.value_text),
-                                                  self.value_text[k] == Old(self.value_text[k])))))
-        Invariant(len(self.qualified_label) == Old(len(self.qualified_label)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.qualified_label),
-                                                  self.qualified_label[k] == Old(self.qualified_label[k])))))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(self.value_text))
-        Invariant(len(result) == i)
-        Invariant(ToSeq(result) == ToSeq(self.value_text).take(i))
-        # invariants-end
-        result.append(self.value_text[i])
-        i = i + 1
     return result
     # impl-end
```

Attack 4 — `atk_4_skipfirst.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
+    i = 1
     while i < len(self.value_text):
         # invariants-start
         Invariant(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
@@ -97,9 +97,8 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.qualified_label),
                                                   self.qualified_label[k] == Old(self.qualified_label[k])))))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(self.value_text))
-        Invariant(len(result) == i)
-        Invariant(ToSeq(result) == ToSeq(self.value_text).take(i))
+        Invariant(1 <= i and i <= len(self.value_text))
+        Invariant(len(result) == i - 1)
         # invariants-end
         result.append(self.value_text[i])
         i = i + 1
```

Attack 5 — `atk_5_double.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,9 +98,8 @@
                                                   self.qualified_label[k] == Old(self.qualified_label[k])))))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(self.value_text))
-        Invariant(len(result) == i)
-        Invariant(ToSeq(result) == ToSeq(self.value_text).take(i))
         # invariants-end
+        result.append(self.value_text[i])
         result.append(self.value_text[i])
         i = i + 1
     return result
```

Attack 6 — `atk_6_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -86,7 +86,7 @@
     # impl-start
     result = []  # type: List[int]
     i = 0
-    while i < len(self.value_text):
+    while i != len(self.value_text):
         # invariants-start
         Invariant(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
         Invariant(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
```

Attack 7 — `atk_7_constant.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,23 +85,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(self.value_text):
-        # invariants-start
-        Invariant(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
-        Invariant(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
-        Invariant(len(self.value_text) == Old(len(self.value_text)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.value_text),
-                                                  self.value_text[k] == Old(self.value_text[k])))))
-        Invariant(len(self.qualified_label) == Old(len(self.qualified_label)))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.qualified_label),
-                                                  self.qualified_label[k] == Old(self.qualified_label[k])))))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(self.value_text))
-        Invariant(len(result) == i)
-        Invariant(ToSeq(result) == ToSeq(self.value_text).take(i))
-        # invariants-end
-        result.append(self.value_text[i])
-        i = i + 1
+    result.append(65)
     return result
     # impl-end
```

Attack 8 — `atk_8_reverse.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,8 +85,8 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[int]
-    i = 0
-    while i < len(self.value_text):
+    i = len(self.value_text)
+    while i > 0:
         # invariants-start
         Invariant(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
         Invariant(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
@@ -98,10 +98,8 @@
                                                   self.qualified_label[k] == Old(self.qualified_label[k])))))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(self.value_text))
-        Invariant(len(result) == i)
-        Invariant(ToSeq(result) == ToSeq(self.value_text).take(i))
         # invariants-end
+        i = i - 1
         result.append(self.value_text[i])
-        i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11964.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An enumerated-choice member carries two pieces of textual identity:

    * the textual rendering of its underlying VALUE (e.g. the choice value
      "first" of a text choice, or the decimal "1" of an integer choice), and

    * a default, diagnostic qualified label of the form "Owner.NAME" naming the
      member within its enumeration.

  When such a member is rendered to text for ordinary use — i.e. coerced to a
  string for templates, persistence and outbound payloads — the result MUST be
  the rendering of the member's VALUE, character for character, and NOT the
  diagnostic "Owner.NAME" label. Concretely, coercing a member to text yields a
  sequence of characters equal to the textual rendering of that member's value.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The member
is a minimal read-only object exposing only the two touched character
sequences. No callee is axiomatized: the rendering is the member's own value
text, modelled deeply as an element-for-element copy. The textual coercion of
the value itself (the standard string coercion) is validated against its real
Python semantics out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The rendering returns the member's own value text, which
# is modelled deeply as an element-for-element copy of the value's character
# sequence. The standard string coercion that produces that value text from the
# underlying value (decimal digits for an integer value, the characters
# themselves for a text value) is an A-reference: it is validated equal to real
# Python str() out-of-band by axiom_check.py (G-AX), not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Member:
    def __init__(self) -> None:
        Ensures(Acc(self.value_text) and Acc(list_pred(self.value_text)))  # type: ignore
        Ensures(len(self.value_text) == 0)  # type: ignore
        Ensures(Acc(self.qualified_label) and Acc(list_pred(self.qualified_label)))  # type: ignore
        Ensures(len(self.qualified_label) == 0)  # type: ignore
        # value_text: the textual rendering of the member's underlying value.
        self.value_text = []  # type: List[int]
        # qualified_label: the diagnostic "Owner.NAME" rendering of the member.
        self.qualified_label = []  # type: List[int]


def render_to_text(self: Member) -> List[int]:
    # pre-conditions-start
    # The member is read-only: both of its character sequences are required
    # (and ensured) only at fractional permission, so a rendering that mutated
    # the member to satisfy its postcondition vacuously is rejected.
    Requires(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
    Requires(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The member is left exactly as it was (returned at the same fractional
    # permission, with the same contents).
    Ensures(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
    Ensures(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
    Ensures(len(self.value_text) == Old(len(self.value_text)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.value_text),
                                            self.value_text[k] == Old(self.value_text[k])))))
    Ensures(len(self.qualified_label) == Old(len(self.qualified_label)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.qualified_label),
                                            self.qualified_label[k] == Old(self.qualified_label[k])))))

    # The result is a freshly owned character sequence.
    Ensures(Acc(list_pred(Result())))
    # The discriminating guarantee: the rendered text equals the member's VALUE
    # text, character for character — NOT the diagnostic "Owner.NAME" label.
    Ensures(ToSeq(Result()) == ToSeq(self.value_text))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(self.value_text):
        # invariants-start
        Invariant(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
        Invariant(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
        Invariant(len(self.value_text) == Old(len(self.value_text)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.value_text),
                                                  self.value_text[k] == Old(self.value_text[k])))))
        Invariant(len(self.qualified_label) == Old(len(self.qualified_label)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.qualified_label),
                                                  self.qualified_label[k] == Old(self.qualified_label[k])))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(self.value_text))
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(self.value_text).take(i))
        # invariants-end
        result.append(self.value_text[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's postcondition `ToSeq(Result()) == ToSeq(self.value_text)` pins the returned sequence EXACTLY to the member's value text; the fractional-permission (Acc 1/2) + Old(...) equality postconditions forbid mutating the member. Any verifying impl must return value_text char-for-char = str(self.value).

ENV: project root;:$PATH; SBU_BENCHMARK_DIR=benchmark-verified. All 8 attacks + positive_control + prepatch confirmed SAME-SPEC via `python -m swebench_unified.adversary same-spec nagini django__django-11964 <f>` (only impl region edited; axioms/@Pure/Requires/Ensures byte-identical).

atk_1_prefix.py (partial-domain, loop to len-1): EXIT 2 NOT-A-COUNTEREXAMPLE (verification failed) — rejected.
- atk_2_qualified.py (prepatch bug / control-flow-effect, returns qualified_label): EXIT 2 — rejected. (prepatch bug reproduced.)
- atk_3_empty.py (ungrounded-oracle, returns []): EXIT 2 — rejected.
- atk_4_skipfirst.py (boundary, i=1): EXIT 2 — rejected.
- atk_5_double.py (control-flow-effect, each char twice): EXIT 2 — rejected.
- atk_7_constant.py (ungrounded-oracle echo, returns [65]): EXIT 2 — rejected.
- atk_8_reverse.py (wrong permutation, reversed copy): EXIT 2 — rejected.
- atk_6_echo.py (semantic echo, `while i != len(self.value_text)` instead of `<`, still copies value_text char-for-char): EXIT 0 CANDIDATE-COUNTEREXAMPLE — shares spec AND verifies (12.3s). This is the ONLY verifying attack.

Positive control (model.py copy): `bash scripts/nagini_verify.sh positive_control.py` -> Verification successful (11.8s).

MANDATORY RESOLVE for the CANDIDATE (atk_6): materialized faithful refined patch = value_text copied char-for-char = `return str(self.value)`, which is byte-identical to the gold patch body (patch_sha e4681817d9 == pre-existing sbu-audit-gold-e4681817d9). EXECUTED `run_resolve('django__django-11964', <patch>, run_id='sbu-eqaudit-x6azctc-atk6')` -> RESOLVED: True, COMPLETED: True (F2P test_str + test_textchoices: 2 pass / 0 fail; cross-confirmed by pre-existing reports sbu-resolve-...-e4681817d9 and sbu-audit-gold-e4681817d9, both resolved=True). So the sole verifying wrong-shaped impl actually resolves — verify DOES imply correct here; spec NOT broken.

REFINEMENT.MD AUDIT: 3 legs, all R/A-reference/I, NO kind-3. A1 (self.value_text:List[int] <-> self.value / str(self.value)) = R (code-point type refinement). A2 (element-copy of value_text -> return str(self.value)) = A-reference: the changed op is modelled DEEPLY (impl loop IS the rendering); no consumed @ContractOnly axiom (axioms region empty, verified). The one abstracted primitive str(value) is validated == real Python str() by axiom_check.py (G-AX). A3 (fresh List[int] returned <-> str returned) = R. A-reference correspondence HOLDS: re-ran axiom_check.py -> 'G-AX OK ... over 20031 members (boundary + 20000 fuzz)', exit 0; it reconstructs the exact patched construction (Choices.__str__ -> str(self.value) + IntegerChoices/TextChoices mixins) and asserts str(member)==str(member.value) and !=default 'Owner.NAME' label. The F2P test_str asserts `str(test[member.name]) == str(member.value)`, exactly matching the postcondition ToSeq(Result())==ToSeq(self.value_text).

CONCLUSION: ≥5 distinct wrong impls (7 here) run and all rejected by Nagini; the only same-spec verifying impl (echo) has a faithful patch that RESOLVES (executed). No verify⇏correct witness found. G-EQ = SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1_prefix.py`, `atk_2_qualified.py`, `atk_3_empty.py`, `atk_4_skipfirst.py`, `atk_5_double.py`, `atk_7_constant.py`, `atk_8_reverse.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prefix.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_qualified.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_empty.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_skipfirst.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_double.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7_constant.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_reverse.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-11964.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An enumerated-choice member carries two pieces of textual identity:

    * the textual rendering of its underlying VALUE (e.g. the choice value
      "first" of a text choice, or the decimal "1" of an integer choice), and

    * a default, diagnostic qualified label of the form "Owner.NAME" naming the
      member within its enumeration.

  When such a member is rendered to text for ordinary use — i.e. coerced to a
  string for templates, persistence and outbound payloads — the result MUST be
  the rendering of the member's VALUE, character for character, and NOT the
  diagnostic "Owner.NAME" label. Concretely, coercing a member to text yields a
  sequence of characters equal to the textual rendering of that member's value.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The member
is a minimal read-only object exposing only the two touched character
sequences. No callee is axiomatized: the rendering is the member's own value
text, modelled deeply as an element-for-element copy. The textual coercion of
the value itself (the standard string coercion) is validated against its real
Python semantics out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The rendering returns the member's own value text, which
# is modelled deeply as an element-for-element copy of the value's character
# sequence. The standard string coercion that produces that value text from the
# underlying value (decimal digits for an integer value, the characters
# themselves for a text value) is an A-reference: it is validated equal to real
# Python str() out-of-band by axiom_check.py (G-AX), not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Member:
    def __init__(self) -> None:
        Ensures(Acc(self.value_text) and Acc(list_pred(self.value_text)))  # type: ignore
        Ensures(len(self.value_text) == 0)  # type: ignore
        Ensures(Acc(self.qualified_label) and Acc(list_pred(self.qualified_label)))  # type: ignore
        Ensures(len(self.qualified_label) == 0)  # type: ignore
        # value_text: the textual rendering of the member's underlying value.
        self.value_text = []  # type: List[int]
        # qualified_label: the diagnostic "Owner.NAME" rendering of the member.
        self.qualified_label = []  # type: List[int]


def render_to_text(self: Member) -> List[int]:
    # pre-conditions-start
    # The member is read-only: both of its character sequences are required
    # (and ensured) only at fractional permission, so a rendering that mutated
    # the member to satisfy its postcondition vacuously is rejected.
    Requires(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
    Requires(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The member is left exactly as it was (returned at the same fractional
    # permission, with the same contents).
    Ensures(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
    Ensures(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
    Ensures(len(self.value_text) == Old(len(self.value_text)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.value_text),
                                            self.value_text[k] == Old(self.value_text[k])))))
    Ensures(len(self.qualified_label) == Old(len(self.qualified_label)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(self.qualified_label),
                                            self.qualified_label[k] == Old(self.qualified_label[k])))))

    # The result is a freshly owned character sequence.
    Ensures(Acc(list_pred(Result())))
    # The discriminating guarantee: the rendered text equals the member's VALUE
    # text, character for character — NOT the diagnostic "Owner.NAME" label.
    Ensures(ToSeq(Result()) == ToSeq(self.value_text))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(self.value_text):
        # invariants-start
        Invariant(Acc(self.value_text, 1 / 2) and Acc(list_pred(self.value_text), 1 / 2))
        Invariant(Acc(self.qualified_label, 1 / 2) and Acc(list_pred(self.qualified_label), 1 / 2))
        Invariant(len(self.value_text) == Old(len(self.value_text)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.value_text),
                                                  self.value_text[k] == Old(self.value_text[k])))))
        Invariant(len(self.qualified_label) == Old(len(self.qualified_label)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(self.qualified_label),
                                                  self.qualified_label[k] == Old(self.qualified_label[k])))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(self.value_text))
        Invariant(len(result) == i)
        Invariant(ToSeq(result) == ToSeq(self.value_text).take(i))
        # invariants-end
        result.append(self.value_text[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's postcondition `ToSeq(Result()) == ToSeq(self.value_text)` pins the returned sequence EXACTLY to the member's value text; the fractional-permission (Acc 1/2) + Old(...) equality postconditions forbid mutating the member. Any verifying impl must return value_text char-for-char = str(self.value).

ENV: project root;:$PATH; SBU_BENCHMARK_DIR=benchmark-verified. All 8 attacks + positive_control + prepatch confirmed SAME-SPEC via `python -m swebench_unified.adversary same-spec nagini django__django-11964 <f>` (only impl region edited; axioms/@Pure/Requires/Ensures byte-identical).

atk_1_prefix.py (partial-domain, loop to len-1): EXIT 2 NOT-A-COUNTEREXAMPLE (verification failed) — rejected.
- atk_2_qualified.py (prepatch bug / control-flow-effect, returns qualified_label): EXIT 2 — rejected. (prepatch bug reproduced.)
- atk_3_empty.py (ungrounded-oracle, returns []): EXIT 2 — rejected.
- atk_4_skipfirst.py (boundary, i=1): EXIT 2 — rejected.
- atk_5_double.py (control-flow-effect, each char twice): EXIT 2 — rejected.
- atk_7_constant.py (ungrounded-oracle echo, returns [65]): EXIT 2 — rejected.
- atk_8_reverse.py (wrong permutation, reversed copy): EXIT 2 — rejected.
- atk_6_echo.py (semantic echo, `while i != len(self.value_text)` instead of `<`, still copies value_text char-for-char): EXIT 0 CANDIDATE-COUNTEREXAMPLE — shares spec AND verifies (12.3s). This is the ONLY verifying attack.

Positive control (model.py copy): `bash scripts/nagini_verify.sh positive_control.py` -> Verification successful (11.8s).

MANDATORY RESOLVE for the CANDIDATE (atk_6): materialized faithful refined patch = value_text copied char-for-char = `return str(self.value)`, which is byte-identical to the gold patch body (patch_sha e4681817d9 == pre-existing sbu-audit-gold-e4681817d9). EXECUTED `run_resolve('django__django-11964', <patch>, run_id='sbu-eqaudit-x6azctc-atk6')` -> RESOLVED: True, COMPLETED: True (F2P test_str + test_textchoices: 2 pass / 0 fail; cross-confirmed by pre-existing reports sbu-resolve-...-e4681817d9 and sbu-audit-gold-e4681817d9, both resolved=True). So the sole verifying wrong-shaped impl actually resolves — verify DOES imply correct here; spec NOT broken.

REFINEMENT.MD AUDIT: 3 legs, all R/A-reference/I, NO kind-3. A1 (self.value_text:List[int] <-> self.value / str(self.value)) = R (code-point type refinement). A2 (element-copy of value_text -> return str(self.value)) = A-reference: the changed op is modelled DEEPLY (impl loop IS the rendering); no consumed @ContractOnly axiom (axioms region empty, verified). The one abstracted primitive str(value) is validated == real Python str() by axiom_check.py (G-AX). A3 (fresh List[int] returned <-> str returned) = R. A-reference correspondence HOLDS: re-ran axiom_check.py -> 'G-AX OK ... over 20031 members (boundary + 20000 fuzz)', exit 0; it reconstructs the exact patched construction (Choices.__str__ -> str(self.value) + IntegerChoices/TextChoices mixins) and asserts str(member)==str(member.value) and !=default 'Owner.NAME' label. The F2P test_str asserts `str(test[member.name]) == str(member.value)`, exactly matching the postcondition ToSeq(Result())==ToSeq(self.value_text).

CONCLUSION: ≥5 distinct wrong impls (7 here) run and all rejected by Nagini; the only same-spec verifying impl (echo) has a faithful patch that RESOLVES (executed). No verify⇏correct witness found. G-EQ = SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness / spec-too-strong drift audit for django__django-11964 nagini bundle.

Modeled function: render_to_text(self: Member). Postcondition: ToSeq(Result()) == ToSeq(self.value_text), plus fractional-permission framing (Acc at 1/2) that leaves self unchanged. The impl copies value_text element-for-element under a take(i) loop invariant, so the result equals the member's value_text character-for-character. Model VERIFIES under pinned Nagini (exit 0, 16.6s), so the spec is non-vacuous. same-spec toolkit confirms the model copy shares the bundle's exact spec (exit 0).

Real callee (mapping.md/meta.json): django.db.models.enums.Choices.__str__(self). Read the patched worktree (django/db/models/enums.py lines 60-90): body is `return str(self.value)`. Confirmed the MRO for TextChoices(str, Choices) and IntegerChoices(int, Choices) resolves __str__ to Choices.__str__ (not str.__str__/int.__str__), so str(member) == str(member.value) in all cases — verified by loading the actual patched enums module (Suit int choices, Year text choices, Plain Choices with int/str/float/tuple/empty/unicode values): ZERO disagreements.

Bridge (mapping.md §2): value_text = code points of str(member.value) via ord; result reconstructed from those code points. So the modeled function computes exactly str(member.value); the real callee returns str(member.value). Identical by construction.

Divergence hunt: integer, float (3.5), text (empty, 'café', 'FR'/'SO'), tuple values — no input where the modeled function disagrees with the real callee. G-CONF in meta.json independently records 100203 differential checks, 0 disagreements against the real patched repo.

The spec is not too strong: it pins precisely the patched behaviour (render the member's value text, never the default 'Owner.NAME' Enum label). qualified_label is modeled but legitimately unused by both impl and real callee — it exists only so model_prepatch.py reproduces the pre-patch Enum.__str__ and fails G-DIFF. No drift, no diverging input. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen over spec_view → no hard failures). Manual review confirms the consumer spec view (model.py docstring + spec/pre/post regions) discloses nothing about the gold edit beyond the public problem_statement:

- Gold edit: `django/db/models/enums.py` — replace `Choices`'s `pass` body with `def __str__(self): return str(self.value)`.
- The public problem_statement already fully reveals the discriminating behavior: `str(my_object.my_str_value)` returns the qualified label `'MyChoice.FIRST_CHOICE'` when it should return the value `'first'`; it names TextChoices/IntegerChoices/choices and says `__str__` fails to yield the value property. The 'Owner.NAME' label detail is taken straight from the public traceback (`'MyChoice.FIRST_CHOICE'`).
- Spec view restates this at an abstract behavioral level (coerce member to text ⇒ value text, not the diagnostic Owner.NAME label). No patched file path (enums.py), no module path, no verbatim gold line (`return str(self.value)` / `def __str__`), no diff markers.
- Patched symbols: `Choices` is already public via `TextChoices`/`MyChoice.choices` in the statement; `__str__` is a common non-distinctive dunder (in _COMMON_NONDISTINCTIVE / stripped len<4). Symbol-collision check finds nothing not already public.
- Pre-patch narration (empty `pass` body, inherited Enum.__str__) lives only in refinement.md/mapping.md — audit artifacts, NOT the consumer spec view — and is scrubbed from model.py. No bug/fix/prepatch narration terms in spec-view comments.

The spec view expresses the target behavior (which the task legitimately requires) without localizing the edit; behavior-not-edit framing is intact. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
