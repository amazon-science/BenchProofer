# P2 adversarial audit — sphinx-doc__sphinx-7454

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,9 +114,6 @@
         i = i + 1
     Assert(ToSeq(text).take(len(text)) == ToSeq(text))
     ref.target = target
-    if ToSeq(text) == name_value():
-        ref.kind = [111, 98, 106]
-    else:
-        ref.kind = [99, 108, 97, 115, 115]
+    ref.kind = [99, 108, 97, 115, 115]
     return ref
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -115,8 +115,8 @@
     Assert(ToSeq(text).take(len(text)) == ToSeq(text))
     ref.target = target
     if ToSeq(text) == name_value():
+        ref.kind = [99, 108, 97, 115, 115]
+    else:
         ref.kind = [111, 98, 106]
-    else:
-        ref.kind = [99, 108, 97, 115, 115]
     return ref
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,7 @@
         i = i + 1
     Assert(ToSeq(text).take(len(text)) == ToSeq(text))
     ref.target = target
-    if ToSeq(text) == name_value():
+    if len(text) == 4:
         ref.kind = [111, 98, 106]
     else:
         ref.kind = [99, 108, 97, 115, 115]
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -101,19 +101,6 @@
     # post-conditions-end
     # impl-start
     ref = CrossReference()
-    target = []  # type: List[int]
-    i = 0
-    while i < len(text):
-        # invariants-start
-        Invariant(Acc(list_pred(text), 1 / 2))
-        Invariant(Acc(list_pred(target)))
-        Invariant(0 <= i and i <= len(text))
-        Invariant(ToSeq(target) == ToSeq(text).take(i))
-        # invariants-end
-        target = target + [text[i]]
-        i = i + 1
-    Assert(ToSeq(text).take(len(text)) == ToSeq(text))
-    ref.target = target
     if ToSeq(text) == name_value():
         ref.kind = [111, 98, 106]
     else:
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,7 @@
         i = i + 1
     Assert(ToSeq(text).take(len(text)) == ToSeq(text))
     ref.target = target
-    if ToSeq(text) == name_value():
+    if len(text) > 0 and text[0] == 78:
         ref.kind = [111, 98, 106]
     else:
         ref.kind = [99, 108, 97, 115, 115]
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -114,9 +114,9 @@
         i = i + 1
     Assert(ToSeq(text).take(len(text)) == ToSeq(text))
     ref.target = target
-    if ToSeq(text) == name_value():
+    if ToSeq(text) != name_value():
+        ref.kind = [99, 108, 97, 115, 115]
+    else:
         ref.kind = [111, 98, 106]
-    else:
-        ref.kind = [99, 108, 97, 115, 115]
     return ref
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,7 +114,7 @@
         i = i + 1
     Assert(ToSeq(text).take(len(text)) == ToSeq(text))
     ref.target = target
-    if ToSeq(text) == name_value():
+    if ToSeq(text) == name_value() or len(text) == 0:
         ref.kind = [111, 98, 106]
     else:
         ref.kind = [99, 108, 97, 115, 115]
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -103,16 +103,13 @@
     ref = CrossReference()
     target = []  # type: List[int]
     i = 0
-    while i < len(text):
-        # invariants-start
+    while i + 1 < len(text):
         Invariant(Acc(list_pred(text), 1 / 2))
         Invariant(Acc(list_pred(target)))
         Invariant(0 <= i and i <= len(text))
         Invariant(ToSeq(target) == ToSeq(text).take(i))
-        # invariants-end
         target = target + [text[i]]
         i = i + 1
-    Assert(ToSeq(text).take(len(text)) == ToSeq(text))
     ref.target = target
     if ToSeq(text) == name_value():
         ref.kind = [111, 98, 106]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7454.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a single textual type name appearing in a parsed type annotation is
  turned into a resolvable cross-reference, the reference must carry two
  pieces of information derived from that text:

    (1) its TARGET is exactly the text itself (the name being referred to is
        carried through unchanged), and

    (2) its REFERENCE KIND distinguishes the singleton value name from an
        ordinary type name. The text consisting of the four code points of the
        singleton value name (capital-N, lower-o, lower-n, lower-e) is
        classified as a VALUE reference; every other text is classified as a
        TYPE reference. The two kinds are distinct constant tags, so a value
        name and a type name of identical spelling would still be classified
        differently — but here the spelling itself decides the kind.

  This makes the singleton value name resolve like the other built-in names
  occurring in signatures, rather than being treated as an ordinary type and
  failing to resolve.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); a cross-reference is a minimal object exposing only the two touched
fields (its kind tag and its target). The two constant kind tags and the
discriminating name are spelled out deeply as code-point sequences; no callee
is axiomatized (the classification is pure structure logic).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the classification of a name into a reference-kind tag
# and the carry-through of the target are pure structure logic, modelled
# deeply over `List[int]` code points. The constructor of the cross-reference
# node is unchanged by the behaviour under specification.
# axioms-end


# pure-start
@Pure
def name_value() -> PSeq[int]:
    # the singleton value name, as Unicode code points
    return PSeq(78, 111, 110, 101)


@Pure
def tag_value() -> PSeq[int]:
    # the constant kind tag for a value reference, as Unicode code points
    return PSeq(111, 98, 106)


@Pure
def tag_type() -> PSeq[int]:
    # the constant kind tag for an ordinary type reference, as code points
    return PSeq(99, 108, 97, 115, 115)


@Pure
def kind_for(text: PSeq[int]) -> PSeq[int]:
    """The reference-kind tag for a name: the value tag exactly when the name
    is the singleton value name, the type tag otherwise."""
    if text == name_value():
        return tag_value()
    return tag_type()
# pure-end


class CrossReference:
    def __init__(self) -> None:
        Ensures(Acc(self.kind) and Acc(list_pred(self.kind)))      # type: ignore
        Ensures(Acc(self.target) and Acc(list_pred(self.target)))  # type: ignore
        Ensures(ToSeq(self.kind) == PSeq(0).take(0))               # type: ignore
        Ensures(ToSeq(self.target) == PSeq(0).take(0))             # type: ignore
        self.kind = []    # type: List[int]
        self.target = []  # type: List[int]


def make_cross_reference(text: List[int]) -> CrossReference:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(Result().kind) and Acc(list_pred(Result().kind)))      # type: ignore
    Ensures(Acc(Result().target) and Acc(list_pred(Result().target)))  # type: ignore
    # The reference carries the name through unchanged as its target.
    Ensures(ToSeq(Result().target) == ToSeq(text))                     # type: ignore
    # The reference kind is the value tag exactly when the name is the
    # singleton value name, and the type tag otherwise.
    Ensures(ToSeq(Result().kind) == kind_for(ToSeq(text)))             # type: ignore
    # Spelled out so the discriminating value/type split is pinned directly:
    Ensures(Implies(ToSeq(text) == name_value(),
                    ToSeq(Result().kind) == tag_value()))             # type: ignore
    Ensures(Implies(ToSeq(text) != name_value(),
                    ToSeq(Result().kind) == tag_type()))              # type: ignore
    # post-conditions-end
    # impl-start
    ref = CrossReference()
    target = []  # type: List[int]
    i = 0
    while i < len(text):
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(target) == ToSeq(text).take(i))
        # invariants-end
        target = target + [text[i]]
        i = i + 1
    Assert(ToSeq(text).take(len(text)) == ToSeq(text))
    ref.target = target
    if ToSeq(text) == name_value():
        ref.kind = [111, 98, 106]
    else:
        ref.kind = [99, 108, 97, 115, 115]
    return ref
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a TOTAL functional specification: Requires only demands read access (Acc(list_pred(text),1/2)); Ensures pins BOTH output fields for ALL inputs -- ToSeq(Result().target)==ToSeq(text) (carry-through) and ToSeq(Result().kind)==kind_for(ToSeq(text)) plus two redundant Implies clauses (kind==tag_value() iff text==name_value(), else tag_type()). No partial-domain escape hatch. kind_for/name_value/tag_value/tag_type modeled DEEPLY as code-point constants (78,111,110,101='None'; 111,98,106='obj'; 99,108,97,115,115='class'), matching gold rule text=='None'->'obj' else 'class'.

Refinement audit: meta.json axioms=[] and deep_model_references=[], consistent with refinement.md sec C. Legs A1=R, A2=R, A3=I+R; NO kind-3 legs and NO A-consumed/A-reference legs -> the A-leg correspondence obligation is VACUOUS (the changed op is modeled deeply, not behind an axiom). axiom_check.py performs no callee fuzz (no callee) and independently checks the deep classifier vs gold on boundary+20000 fuzz names -> consistent.

Attacks (env: python=python; cmd base: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-7454 <path>`):
- atk_1 prepatch bug (unconditional 'class' tag) -> exit 2 NOT-A-CE (verification failed; G-DIFF senses the change, matches model_prepatch.py). prepatch_reproduced=true.
- atk_2 swapped tags (obj<->class) -> exit 2 NOT-A-CE.
- atk_3 boundary: classify by len(text)==4 -> exit 2 NOT-A-CE.
- atk_4 partial-domain/broken target (empty, no carry-through) -> exit 2 NOT-A-CE.
- atk_5 control-flow-effect: classify by text[0]==78 ('N') -> exit 2 NOT-A-CE.
- atk_6 ECHO: correct behavior via reversed `if text != name_value()` branch -> exit 0 CANDIDATE (verifies 19.5s). Materialized faithful refined patch atk_6_patch.diff and RAN it through the official harness via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-7454', patch): completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. It is a correct behavioral echo of gold (identical reftype/reftarget mapping), NOT a weakness (per resolve-based policy a resolving same-spec verifying echo is not a G-EQ break).
- atk_7 ungrounded broadening: value tag for name_value() OR empty text -> exit 2 NOT-A-CE.
- atk_8 boundary: target truncated by one element (i+1<len loop) with correct kind -> exit 2 NOT-A-CE.

Positive control (unmodified model.py impl): `bash scripts/nagini_verify.sh positive_control.py` -> Verification successful, exit 0 (16.4s).

Conclusion: 8 distinct wrong impls (incl. prepatch, boundary, partial-domain, control-flow-effect, ungrounded-oracle-echo) run; only the correct-echo verifies and its faithful patch RESOLVES. No verifying wrong impl whose faithful patch fails to resolve exists. verify=>correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-7454.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a single textual type name appearing in a parsed type annotation is
  turned into a resolvable cross-reference, the reference must carry two
  pieces of information derived from that text:

    (1) its TARGET is exactly the text itself (the name being referred to is
        carried through unchanged), and

    (2) its REFERENCE KIND distinguishes the singleton value name from an
        ordinary type name. The text consisting of the four code points of the
        singleton value name (capital-N, lower-o, lower-n, lower-e) is
        classified as a VALUE reference; every other text is classified as a
        TYPE reference. The two kinds are distinct constant tags, so a value
        name and a type name of identical spelling would still be classified
        differently — but here the spelling itself decides the kind.

  This makes the singleton value name resolve like the other built-in names
  occurring in signatures, rather than being treated as an ordinary type and
  failing to resolve.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); a cross-reference is a minimal object exposing only the two touched
fields (its kind tag and its target). The two constant kind tags and the
discriminating name are spelled out deeply as code-point sequences; no callee
is axiomatized (the classification is pure structure logic).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the classification of a name into a reference-kind tag
# and the carry-through of the target are pure structure logic, modelled
# deeply over `List[int]` code points. The constructor of the cross-reference
# node is unchanged by the behaviour under specification.
# axioms-end


# pure-start
@Pure
def name_value() -> PSeq[int]:
    # the singleton value name, as Unicode code points
    return PSeq(78, 111, 110, 101)


@Pure
def tag_value() -> PSeq[int]:
    # the constant kind tag for a value reference, as Unicode code points
    return PSeq(111, 98, 106)


@Pure
def tag_type() -> PSeq[int]:
    # the constant kind tag for an ordinary type reference, as code points
    return PSeq(99, 108, 97, 115, 115)


@Pure
def kind_for(text: PSeq[int]) -> PSeq[int]:
    """The reference-kind tag for a name: the value tag exactly when the name
    is the singleton value name, the type tag otherwise."""
    if text == name_value():
        return tag_value()
    return tag_type()
# pure-end


class CrossReference:
    def __init__(self) -> None:
        Ensures(Acc(self.kind) and Acc(list_pred(self.kind)))      # type: ignore
        Ensures(Acc(self.target) and Acc(list_pred(self.target)))  # type: ignore
        Ensures(ToSeq(self.kind) == PSeq(0).take(0))               # type: ignore
        Ensures(ToSeq(self.target) == PSeq(0).take(0))             # type: ignore
        self.kind = []    # type: List[int]
        self.target = []  # type: List[int]


def make_cross_reference(text: List[int]) -> CrossReference:
    # pre-conditions-start
    Requires(Acc(list_pred(text), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(text), 1 / 2))
    Ensures(Acc(Result().kind) and Acc(list_pred(Result().kind)))      # type: ignore
    Ensures(Acc(Result().target) and Acc(list_pred(Result().target)))  # type: ignore
    # The reference carries the name through unchanged as its target.
    Ensures(ToSeq(Result().target) == ToSeq(text))                     # type: ignore
    # The reference kind is the value tag exactly when the name is the
    # singleton value name, and the type tag otherwise.
    Ensures(ToSeq(Result().kind) == kind_for(ToSeq(text)))             # type: ignore
    # Spelled out so the discriminating value/type split is pinned directly:
    Ensures(Implies(ToSeq(text) == name_value(),
                    ToSeq(Result().kind) == tag_value()))             # type: ignore
    Ensures(Implies(ToSeq(text) != name_value(),
                    ToSeq(Result().kind) == tag_type()))              # type: ignore
    # post-conditions-end
    # impl-start
    ref = CrossReference()
    target = []  # type: List[int]
    i = 0
    while i < len(text):
        # invariants-start
        Invariant(Acc(list_pred(text), 1 / 2))
        Invariant(Acc(list_pred(target)))
        Invariant(0 <= i and i <= len(text))
        Invariant(ToSeq(target) == ToSeq(text).take(i))
        # invariants-end
        target = target + [text[i]]
        i = i + 1
    Assert(ToSeq(text).take(len(text)) == ToSeq(text))
    ref.target = target
    if ToSeq(text) == name_value():
        ref.kind = [111, 98, 106]
    else:
        ref.kind = [99, 108, 97, 115, 115]
    return ref
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a TOTAL functional specification: Requires only demands read access (Acc(list_pred(text),1/2)); Ensures pins BOTH output fields for ALL inputs -- ToSeq(Result().target)==ToSeq(text) (carry-through) and ToSeq(Result().kind)==kind_for(ToSeq(text)) plus two redundant Implies clauses (kind==tag_value() iff text==name_value(), else tag_type()). No partial-domain escape hatch. kind_for/name_value/tag_value/tag_type modeled DEEPLY as code-point constants (78,111,110,101='None'; 111,98,106='obj'; 99,108,97,115,115='class'), matching gold rule text=='None'->'obj' else 'class'.

Refinement audit: meta.json axioms=[] and deep_model_references=[], consistent with refinement.md sec C. Legs A1=R, A2=R, A3=I+R; NO kind-3 legs and NO A-consumed/A-reference legs -> the A-leg correspondence obligation is VACUOUS (the changed op is modeled deeply, not behind an axiom). axiom_check.py performs no callee fuzz (no callee) and independently checks the deep classifier vs gold on boundary+20000 fuzz names -> consistent.

Attacks (env: python=python; cmd base: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-7454 <path>`):
- atk_1 prepatch bug (unconditional 'class' tag) -> exit 2 NOT-A-CE (verification failed; G-DIFF senses the change, matches model_prepatch.py). prepatch_reproduced=true.
- atk_2 swapped tags (obj<->class) -> exit 2 NOT-A-CE.
- atk_3 boundary: classify by len(text)==4 -> exit 2 NOT-A-CE.
- atk_4 partial-domain/broken target (empty, no carry-through) -> exit 2 NOT-A-CE.
- atk_5 control-flow-effect: classify by text[0]==78 ('N') -> exit 2 NOT-A-CE.
- atk_6 ECHO: correct behavior via reversed `if text != name_value()` branch -> exit 0 CANDIDATE (verifies 19.5s). Materialized faithful refined patch atk_6_patch.diff and RAN it through the official harness via swebench_unified.harness.run_resolve('sphinx-doc__sphinx-7454', patch): completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. It is a correct behavioral echo of gold (identical reftype/reftarget mapping), NOT a weakness (per resolve-based policy a resolving same-spec verifying echo is not a G-EQ break).
- atk_7 ungrounded broadening: value tag for name_value() OR empty text -> exit 2 NOT-A-CE.
- atk_8 boundary: target truncated by one element (i+1<len loop) with correct kind -> exit 2 NOT-A-CE.

Positive control (unmodified model.py impl): `bash scripts/nagini_verify.sh positive_control.py` -> Verification successful, exit 0 (16.4s).

Conclusion: 8 distinct wrong impls (incl. prepatch, boundary, partial-domain, control-flow-effect, ungrounded-oracle-echo) run; only the correct-echo verifies and its faithful patch RESOLVES. No verifying wrong impl whose faithful patch fails to resolve exists. verify=>correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) FAILED to find a divergence; the modeled function agrees with the real repo callee.

Modeled function: make_cross_reference(text: List[int]) ↔ real nested helper make_xref(text: str) inside _parse_annotation in sphinx/domains/python.py at base_commit aca3f825f2e4a8817190f3c885a242a285aa0dba.

Gold patch (post-patch make_xref):
  if text == 'None': reftype = 'obj' else: reftype = 'class'
  return pending_xref('', nodes.Text(text), refdomain='py', reftype=reftype, reftarget=text)

Spec pins exactly two touched fields: (target) ToSeq(Result().target)==ToSeq(text) [reftarget=text, identity carry-through], and (kind) ToSeq(Result().kind)==kind_for(ToSeq(text)) which is tag_value()=PSeq(111,98,106)='obj' iff text==name_value()=PSeq(78,111,110,101)='None', else tag_type()=PSeq(99,108,97,115,115)='class'. Under the documented str↔List[int] code-point bijection this is byte-for-byte the gold classification.

Abstraction is a legitimate refinement, NOT over-constraint: refdomain='py', the '' rawsource, and nodes.Text(text) child are unchanged context (untouched by the patch) and correctly excluded from the model; only the two patch-touched fields are constrained. The spec places no constraint that the real callee violates.

Machine checks (in /tmp worktree at base_commit, gold patch applied):
- Built the real post-patch make_xref standalone against real docutils.nodes + sphinx.addnodes.pending_xref and differentially fuzzed it against the spec's decision function over 300,019 inputs (boundary set: 'None', case-variants 'none'/'NONE'/'nOne', near-misses 'Non'/'NoneType', empty, tag spellings 'obj'/'class', dotted names, non-ASCII 'Néné'/fullwidth 'Ｎｏｎｅ', control chars \x00/\t/\n; plus seed=745400 fuzz with 'None'-neighbourhood mutations). Zero disagreements on reftype and reftarget.
- The spec is total (kind_for is defined for every text; make_cross_reference's Requires only demands read access), so there is no input on which the spec is silent/weaker or stronger than the real function.
- scripts/nagini_verify.sh model.py => Verification successful (13.82s), confirming this frozen spec is the one that verifies.

No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-LEAK (leakage / gold-reconstruction) over the consumer spec view (model.py), judged against the public problem_statement ONLY (not hints_text, which is empty here).

Gold edit: in make_xref (sphinx/domains/python.py), special-case `if text == 'None': reftype = 'obj' else: reftype = 'class'`, with `reftarget=text` carried through, so 'None' resolves as a value/singleton rather than an ordinary class.

The public problem_statement ALREADY describes this desired behavior in full: it states that `None` in a type hint should be a clickable link to the None-singleton documentation regardless of description/signature mode, contrasting it with `int` which resolves as an ordinary type. So 'None is treated specially and resolves like a built-in value name' is public.

Mechanical screen (swebench_unified.leakage.screen with the nagini python-flavor tables) returns PASSED=True, hard_failures=[], warnings=[]. Manual confirmation of each leak rule:
- L1 diff markers: none in the spec view.
- L1 gold-patch line reproduced: NONE. The gold literals ('None','obj','class') and the test `text=='None'` are encoded obfuscated as code-point PSeq constants — name_value()=PSeq(78,111,110,101), tag_value()=PSeq(111,98,106), tag_type()=PSeq(99,108,97,115,115) — never spelled literally; kind_for() is the classifier phrased over sequences. No 8+ char normalized gold line appears in view_norm.
- L2 patched file path 'sphinx/domains/python.py' / dotted module path: NOT in the spec view (appears only in mapping.md / refinement.md, which are auditor docs, not the consumer view).
- L2/L5 identifier collision: spec-view identifiers are name_value, tag_value, tag_type, kind_for, make_cross_reference, CrossReference, target, kind, text — none embed the distinctive patched repo symbols (make_xref, _parse_annotation, pending_xref).
- L3 narration: docstring/comments describe behavior abstractly ('VALUE reference' vs 'TYPE reference', 'resolve like the other built-in names'); no bug/fix/wrong/broken/previously terms, no edit narration.

The spec inevitably encodes the required behavior, but that behavior is already solver-visible in the problem_statement, and the internal reftype tag strings are modeled as opaque distinct code-point constants that do not localize the edit or the changed file/symbol beyond what the task already reveals. No line reconstructs the gold beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
