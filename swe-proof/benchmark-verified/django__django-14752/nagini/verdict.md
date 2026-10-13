# P2 adversarial audit — django__django-14752

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
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class View:
@@ -45,7 +44,6 @@
     captured here by the receiver argument to `record_entry`."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(True)
 
 
@@ -57,7 +55,6 @@
     def __init__(self, id_text: PSeq[int], display_text: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_text) and Acc(self.display_text))
@@ -78,7 +75,6 @@
     def __init__(self, id_val: PSeq[int], text_val: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_val) and Acc(self.text_val))
@@ -140,7 +136,6 @@
 def default_record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
     # pre-conditions-start
     Requires(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
@@ -161,7 +156,6 @@
     Requires(Acc(list_pred(recs), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
              Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recs), 1 / 2))
@@ -190,9 +184,8 @@
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   result[k] is record_entry(view, recs[k], to_field_name)))))
-        Invariant(MustTerminate(len(recs) - i + 1))
         # invariants-end
-        result.append(record_entry(view, recs[i], to_field_name))
+        result.append(Entry(lookup_text(recs[i], to_field_name), display(recs[i])))
         i = i + 1
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class View:
@@ -45,7 +44,6 @@
     captured here by the receiver argument to `record_entry`."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(True)
 
 
@@ -57,7 +55,6 @@
     def __init__(self, id_text: PSeq[int], display_text: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_text) and Acc(self.display_text))
@@ -78,7 +75,6 @@
     def __init__(self, id_val: PSeq[int], text_val: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_val) and Acc(self.text_val))
@@ -140,7 +136,6 @@
 def default_record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
     # pre-conditions-start
     Requires(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
@@ -152,7 +147,7 @@
     Ensures(Result().text_val == display(rec))
     # post-conditions-end
     # impl-start
-    return Entry(lookup_text(rec, to_field_name), display(rec))
+    return Entry(display(rec), lookup_text(rec, to_field_name))
     # impl-end
 
 
@@ -161,7 +156,6 @@
     Requires(Acc(list_pred(recs), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
              Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recs), 1 / 2))
@@ -190,7 +184,6 @@
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   result[k] is record_entry(view, recs[k], to_field_name)))))
-        Invariant(MustTerminate(len(recs) - i + 1))
         # invariants-end
         result.append(record_entry(view, recs[i], to_field_name))
         i = i + 1
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class View:
@@ -45,7 +44,6 @@
     captured here by the receiver argument to `record_entry`."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(True)
 
 
@@ -57,7 +55,6 @@
     def __init__(self, id_text: PSeq[int], display_text: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_text) and Acc(self.display_text))
@@ -78,7 +75,6 @@
     def __init__(self, id_val: PSeq[int], text_val: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_val) and Acc(self.text_val))
@@ -140,7 +136,6 @@
 def default_record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
     # pre-conditions-start
     Requires(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
@@ -161,7 +156,6 @@
     Requires(Acc(list_pred(recs), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
              Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recs), 1 / 2))
@@ -180,7 +174,7 @@
     # impl-start
     result = []  # type: List[Entry]
     i = 0
-    while i < len(recs):
+    while i < len(recs) - 1:
         # invariants-start
         Invariant(Acc(list_pred(recs), 1 / 2))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
@@ -190,7 +184,6 @@
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   result[k] is record_entry(view, recs[k], to_field_name)))))
-        Invariant(MustTerminate(len(recs) - i + 1))
         # invariants-end
         result.append(record_entry(view, recs[i], to_field_name))
         i = i + 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class View:
@@ -45,7 +44,6 @@
     captured here by the receiver argument to `record_entry`."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(True)
 
 
@@ -57,7 +55,6 @@
     def __init__(self, id_text: PSeq[int], display_text: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_text) and Acc(self.display_text))
@@ -78,7 +75,6 @@
     def __init__(self, id_val: PSeq[int], text_val: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_val) and Acc(self.text_val))
@@ -140,7 +136,6 @@
 def default_record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
     # pre-conditions-start
     Requires(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
@@ -161,7 +156,6 @@
     Requires(Acc(list_pred(recs), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
              Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recs), 1 / 2))
@@ -190,9 +184,8 @@
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   result[k] is record_entry(view, recs[k], to_field_name)))))
-        Invariant(MustTerminate(len(recs) - i + 1))
         # invariants-end
-        result.append(record_entry(view, recs[i], to_field_name))
+        result.append(record_entry(view, recs[0], to_field_name))
         i = i + 1
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class View:
@@ -45,7 +44,6 @@
     captured here by the receiver argument to `record_entry`."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(True)
 
 
@@ -57,7 +55,6 @@
     def __init__(self, id_text: PSeq[int], display_text: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_text) and Acc(self.display_text))
@@ -78,7 +75,6 @@
     def __init__(self, id_val: PSeq[int], text_val: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_val) and Acc(self.text_val))
@@ -140,7 +136,6 @@
 def default_record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
     # pre-conditions-start
     Requires(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
@@ -161,7 +156,6 @@
     Requires(Acc(list_pred(recs), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
              Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recs), 1 / 2))
@@ -179,20 +173,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[Entry]
-    i = 0
-    while i < len(recs):
-        # invariants-start
-        Invariant(Acc(list_pred(recs), 1 / 2))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
-                  Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(recs))
-        Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                  result[k] is record_entry(view, recs[k], to_field_name)))))
-        Invariant(MustTerminate(len(recs) - i + 1))
-        # invariants-end
-        result.append(record_entry(view, recs[i], to_field_name))
-        i = i + 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class View:
@@ -45,7 +44,6 @@
     captured here by the receiver argument to `record_entry`."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(True)
 
 
@@ -57,7 +55,6 @@
     def __init__(self, id_text: PSeq[int], display_text: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_text) and Acc(self.display_text))
@@ -78,7 +75,6 @@
     def __init__(self, id_val: PSeq[int], text_val: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_val) and Acc(self.text_val))
@@ -140,7 +136,6 @@
 def default_record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
     # pre-conditions-start
     Requires(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
@@ -152,7 +147,7 @@
     Ensures(Result().text_val == display(rec))
     # post-conditions-end
     # impl-start
-    return Entry(lookup_text(rec, to_field_name), display(rec))
+    return Entry(lookup_text(rec, to_field_name), lookup_text(rec, to_field_name))
     # impl-end
 
 
@@ -161,7 +156,6 @@
     Requires(Acc(list_pred(recs), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
              Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recs), 1 / 2))
@@ -190,7 +184,6 @@
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   result[k] is record_entry(view, recs[k], to_field_name)))))
-        Invariant(MustTerminate(len(recs) - i + 1))
         # invariants-end
         result.append(record_entry(view, recs[i], to_field_name))
         i = i + 1
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,7 +36,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class View:
@@ -45,7 +44,6 @@
     captured here by the receiver argument to `record_entry`."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(True)
 
 
@@ -57,7 +55,6 @@
     def __init__(self, id_text: PSeq[int], display_text: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_text) and Acc(self.display_text))
@@ -78,7 +75,6 @@
     def __init__(self, id_val: PSeq[int], text_val: PSeq[int]) -> None:
         # pre-conditions-start
         Requires(True)
-        Requires(MustTerminate(2))
         # pre-conditions-end
         # post-conditions-start
         Ensures(Acc(self.id_val) and Acc(self.text_val))
@@ -140,7 +136,6 @@
 def default_record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
     # pre-conditions-start
     Requires(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
@@ -161,7 +156,6 @@
     Requires(Acc(list_pred(recs), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
              Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(recs), 1 / 2))
@@ -190,9 +184,8 @@
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                   result[k] is record_entry(view, recs[k], to_field_name)))))
-        Invariant(MustTerminate(len(recs) - i + 1))
         # invariants-end
-        result.append(record_entry(view, recs[i], to_field_name))
+        result.append(record_entry(view, recs[i], to_field_name + 1))
         i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14752.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An autocomplete endpoint answers a query by turning each matched record into
  one entry of an answer sequence. Two behaviours are pinned:

  (1) The per-record conversion is performed through a single, replaceable
      conversion step that belongs to the responder: every entry of the answer
      sequence is exactly the value that conversion step produces for the
      corresponding record, IN ORDER. Because the responder DEFERS to its own
      conversion step rather than settling the entry contents itself, a
      responder that supplies a different conversion step changes every entry
      accordingly -- the conversion step is the extension point, and the answer
      entries are bound to it, not to any predetermined entry shape.

  (2) The default conversion step turns a record into an entry exposing two
      fields: an identifier field carrying the textual form of the record's
      designated lookup attribute, and a display field carrying the textual form
      of the record itself.

The responder is modelled as a minimal object (`View`); a matched record as a
minimal object (`Record`) carrying the two textual values the default
conversion reads. An entry of the answer sequence is a minimal object (`Entry`).
The designated lookup attribute name is carried as an `int` token. The textual
values are `PSeq[int]` of code points (Nagini bans `str` indexing).

The replaceable conversion step (the responder's own, possibly-supplied
conversion) is the late-bound callee, axiomatized as `record_entry`: an
opaque per-(responder, record) entry producer. The default conversion step is
modelled deeply as `default_record_entry`; its agreement with the late-bound
step for a responder that supplies no replacement is validated out-of-band by
axiom_check.py (G-AX), not consumed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class View:
    """The responder. Modelled as a bare identity-bearing object: the late-bound
    conversion step is selected by WHICH responder this is (its dynamic type),
    captured here by the receiver argument to `record_entry`."""

    def __init__(self) -> None:
        Ensures(True)


class Record:
    """A matched record. Carries only the two textual values the default
    conversion step reads: the textual form of its designated lookup attribute
    (`id_text`) and the textual form of the record itself (`display_text`)."""

    def __init__(self, id_text: PSeq[int], display_text: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.id_text) and Acc(self.display_text))
        Ensures(self.id_text == id_text)
        Ensures(self.display_text == display_text)
        # post-conditions-end
        # impl-start
        self.id_text = id_text            # type: PSeq[int]
        self.display_text = display_text  # type: PSeq[int]
        # impl-end


class Entry:
    """One entry of the answer sequence: an identifier field and a display field
    (the entry may carry further fields supplied by a replacement conversion
    step; only these two are observed for the default step)."""

    def __init__(self, id_val: PSeq[int], text_val: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.id_val) and Acc(self.text_val))
        Ensures(self.id_val == id_val)
        Ensures(self.text_val == text_val)
        # post-conditions-end
        # impl-start
        self.id_val = id_val      # type: PSeq[int]
        self.text_val = text_val  # type: PSeq[int]
        # impl-end


# axioms-start
@Pure
@ContractOnly
def lookup_text(rec: Record, to_field_name: int) -> PSeq[int]:
    """The unchanged extraction of the textual form of a record's designated
    lookup attribute (`str(getattr(obj, to_field_name))`). A pure, deterministic
    function of the record and the attribute token; for the modelled record it
    yields the record's stored `id_text`. Provenance + soundness: mapping.md /
    axiom_check.py (an unchanged callee). The conversion of an attribute to its
    textual form is the same wherever it is performed."""
    Requires(Acc(rec.id_text, 1 / 8))
    Ensures(Result() == rec.id_text)


@Pure
@ContractOnly
def display(rec: Record) -> PSeq[int]:
    """The unchanged extraction of the textual form of a record itself
    (`str(obj)`). A pure, deterministic function of the record; for the modelled
    record it yields the record's stored `display_text`. Provenance + soundness:
    mapping.md / axiom_check.py (an unchanged callee). The conversion of a record
    to its textual form is the same wherever it is performed."""
    Requires(Acc(rec.display_text, 1 / 8))
    Ensures(Result() == rec.display_text)


@Pure
@ContractOnly
def record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
    """The responder's OWN, replaceable conversion step (the extension point),
    late-bound on the responder `view`. Opaque: the produced entry is whatever
    this responder's conversion step yields for the record -- a responder that
    supplies a different conversion step yields a different entry. The default
    responder's conversion step agrees with `default_record_entry`; that
    agreement is validated against the real callee out-of-band by axiom_check.py
    (G-AX), NOT consumed here. Provenance: mapping.md."""
    Requires(Acc(rec.id_text, 1 / 8) and Acc(rec.display_text, 1 / 8))
    Ensures(True)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def default_record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
    # pre-conditions-start
    Requires(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
    Ensures(Acc(Result().id_val) and Acc(Result().text_val))
    # The default entry exposes two fields: the identifier field carries the
    # textual form of the record's designated lookup attribute, and the display
    # field carries the textual form of the record itself.
    Ensures(Result().id_val == lookup_text(rec, to_field_name))
    Ensures(Result().text_val == display(rec))
    # post-conditions-end
    # impl-start
    return Entry(lookup_text(rec, to_field_name), display(rec))
    # impl-end


def build_results(view: View, recs: List[Record], to_field_name: int) -> List[Entry]:
    # pre-conditions-start
    Requires(Acc(list_pred(recs), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
             Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(recs), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
            Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
    Ensures(Acc(list_pred(Result())))
    # The answer sequence is aligned, one entry per record, IN ORDER ...
    Ensures(len(Result()) == len(recs))
    # ... and every entry is exactly what the responder's OWN replaceable
    # conversion step produces for the corresponding record. The responder
    # defers to its conversion step: it does not settle the entry contents
    # itself, so a responder supplying a different step changes every entry.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
            Result()[k] is record_entry(view, recs[k], to_field_name)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[Entry]
    i = 0
    while i < len(recs):
        # invariants-start
        Invariant(Acc(list_pred(recs), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
                  Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(recs))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  result[k] is record_entry(view, recs[k], to_field_name)))))
        # invariants-end
        result.append(record_entry(view, recs[i], to_field_name))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement fidelity) audit for django__django-14752 (nagini). commands run with SBU_BENCHMARK_DIR=benchmark-verified via python -m swebench_unified.adversary.

SPEC SHAPE (frozen, byte-identical across all attacks — same-spec exit 0 for all 7): build_results pins len(Result())==len(recs) AND Forall k: Result()[k] is record_entry(view, recs[k], to_field_name) — an IDENTITY to the opaque @Pure @ContractOnly callee record_entry (Ensures(True)). This is dischargeable ONLY by actually appending that exact per-record call; inlining a fixed Entry cannot prove the `is`. default_record_entry pins id_val==lookup_text(rec,tf) and text_val==display(rec). Both make the spec very tight.

ATTACKS (all copied from model.py editing ONLY impl regions; axioms/@Pure/Requires/Ensures byte-identical; each run via `adversary weakness nagini django__django-14752 <path>`):
- atk_1 (PREPATCH BUG: build_results inlines result.append(Entry(lookup_text(recs[i],tf), display(recs[i]))) instead of deferring to record_entry): same-spec SAME, verify FAILED at atk_1.py:185 'Loop invariant might not be preserved: Forall(...) result[k] is record_entry(...)'. weakness exit 2 (NOT-A-COUNTEREXAMPLE). => prepatch_reproduced=True; spec sees the bug exactly where the F2P test test_serialize_result observes it.
- atk_2 (boundary/field-swap id<->text: Entry(display(rec), lookup_text(rec,tf))): SAME, FAILED at atk_2.py:146 'Postcondition of default_record_entry might not hold: Result().id_val == lookup_text(rec,tf)'. exit 2.
- atk_3 (partial-domain: loop while i < len(recs)-1, drops last record): SAME, FAILED. exit 2.
- atk_4 (wrong-index echo: always record_entry(view, recs[0], tf)): SAME, FAILED. exit 2.
- atk_5 (control-flow-effect: return empty result list unconditionally): SAME, FAILED. exit 2.
- atk_6 (ungrounded-oracle echo: Entry(lookup_text, lookup_text) — id used for both fields): SAME, FAILED. exit 2.
- atk_7 (arg-perturbation: record_entry(view, recs[i], to_field_name + 1) — different attribute token): SAME, FAILED. exit 2.

Positive control: unchanged model.py copied to positive_control.py -> `adversary verify` VERIFIED in 20.5s (exit 0).

NO CANDIDATE (same-spec AND verifies) arose among the 7 wrong impls, so NO faithful refined patch / run_resolve execution was required or possible. Every attack was mechanically rejected by the frozen spec.

REFINEMENT.MD LEG AUDIT: A1=R (queryset<->List[Record], order), A2=A-consumed (record_entry opaque axiom <-> late-bound self.serialize_result dynamic dispatch; the fix), A3=R (result list<->'results' list), B1=I+A-consumed (Entry(lookup_text,display) <-> {'id':str(getattr..),'text':str(obj)}; lookup_text/display <-> str(getattr)/str builtins), plus the A-reference (default_record_entry deep model == real default serialize_result, validated by axiom_check.py check_default_reference, NOT consumed). No kind-3 leg: the one genuinely-changed op (deferral to overridable step) is A-consumed A2, an axiom about an unchanged-in-function callee the new code calls, not about the function under change. A-leg<->callee correspondences hold and are executed by G-AX (axiom_check.py: 6 boundary + 20000 fuzz, exit 0) and G-CONF (conformance_check.py: 13 boundary + 100000 fuzz batches over base + 2 overriding responders, exit 0).

VERDICT SOUND: 7 distinct same-spec wrong impls (>=5 required) all fail verification, positive control verifies, prepatch bug reproduced, refinement legs all R/A-consumed/A-reference/I with sound callee correspondence. verify=>correct holds for this bundle.

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
"""Twin-artifact model for django__django-14752.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An autocomplete endpoint answers a query by turning each matched record into
  one entry of an answer sequence. Two behaviours are pinned:

  (1) The per-record conversion is performed through a single, replaceable
      conversion step that belongs to the responder: every entry of the answer
      sequence is exactly the value that conversion step produces for the
      corresponding record, IN ORDER. Because the responder DEFERS to its own
      conversion step rather than settling the entry contents itself, a
      responder that supplies a different conversion step changes every entry
      accordingly -- the conversion step is the extension point, and the answer
      entries are bound to it, not to any predetermined entry shape.

  (2) The default conversion step turns a record into an entry exposing two
      fields: an identifier field carrying the textual form of the record's
      designated lookup attribute, and a display field carrying the textual form
      of the record itself.

The responder is modelled as a minimal object (`View`); a matched record as a
minimal object (`Record`) carrying the two textual values the default
conversion reads. An entry of the answer sequence is a minimal object (`Entry`).
The designated lookup attribute name is carried as an `int` token. The textual
values are `PSeq[int]` of code points (Nagini bans `str` indexing).

The replaceable conversion step (the responder's own, possibly-supplied
conversion) is the late-bound callee, axiomatized as `record_entry`: an
opaque per-(responder, record) entry producer. The default conversion step is
modelled deeply as `default_record_entry`; its agreement with the late-bound
step for a responder that supplies no replacement is validated out-of-band by
axiom_check.py (G-AX), not consumed.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class View:
    """The responder. Modelled as a bare identity-bearing object: the late-bound
    conversion step is selected by WHICH responder this is (its dynamic type),
    captured here by the receiver argument to `record_entry`."""

    def __init__(self) -> None:
        Ensures(True)


class Record:
    """A matched record. Carries only the two textual values the default
    conversion step reads: the textual form of its designated lookup attribute
    (`id_text`) and the textual form of the record itself (`display_text`)."""

    def __init__(self, id_text: PSeq[int], display_text: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.id_text) and Acc(self.display_text))
        Ensures(self.id_text == id_text)
        Ensures(self.display_text == display_text)
        # post-conditions-end
        # impl-start
        self.id_text = id_text            # type: PSeq[int]
        self.display_text = display_text  # type: PSeq[int]
        # impl-end


class Entry:
    """One entry of the answer sequence: an identifier field and a display field
    (the entry may carry further fields supplied by a replacement conversion
    step; only these two are observed for the default step)."""

    def __init__(self, id_val: PSeq[int], text_val: PSeq[int]) -> None:
        # pre-conditions-start
        Requires(True)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.id_val) and Acc(self.text_val))
        Ensures(self.id_val == id_val)
        Ensures(self.text_val == text_val)
        # post-conditions-end
        # impl-start
        self.id_val = id_val      # type: PSeq[int]
        self.text_val = text_val  # type: PSeq[int]
        # impl-end


# axioms-start
@Pure
@ContractOnly
def lookup_text(rec: Record, to_field_name: int) -> PSeq[int]:
    """The unchanged extraction of the textual form of a record's designated
    lookup attribute (`str(getattr(obj, to_field_name))`). A pure, deterministic
    function of the record and the attribute token; for the modelled record it
    yields the record's stored `id_text`. Provenance + soundness: mapping.md /
    axiom_check.py (an unchanged callee). The conversion of an attribute to its
    textual form is the same wherever it is performed."""
    Requires(Acc(rec.id_text, 1 / 8))
    Ensures(Result() == rec.id_text)


@Pure
@ContractOnly
def display(rec: Record) -> PSeq[int]:
    """The unchanged extraction of the textual form of a record itself
    (`str(obj)`). A pure, deterministic function of the record; for the modelled
    record it yields the record's stored `display_text`. Provenance + soundness:
    mapping.md / axiom_check.py (an unchanged callee). The conversion of a record
    to its textual form is the same wherever it is performed."""
    Requires(Acc(rec.display_text, 1 / 8))
    Ensures(Result() == rec.display_text)


@Pure
@ContractOnly
def record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
    """The responder's OWN, replaceable conversion step (the extension point),
    late-bound on the responder `view`. Opaque: the produced entry is whatever
    this responder's conversion step yields for the record -- a responder that
    supplies a different conversion step yields a different entry. The default
    responder's conversion step agrees with `default_record_entry`; that
    agreement is validated against the real callee out-of-band by axiom_check.py
    (G-AX), NOT consumed here. Provenance: mapping.md."""
    Requires(Acc(rec.id_text, 1 / 8) and Acc(rec.display_text, 1 / 8))
    Ensures(True)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def default_record_entry(view: View, rec: Record, to_field_name: int) -> Entry:
    # pre-conditions-start
    Requires(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(rec.id_text, 1 / 2) and Acc(rec.display_text, 1 / 2))
    Ensures(Acc(Result().id_val) and Acc(Result().text_val))
    # The default entry exposes two fields: the identifier field carries the
    # textual form of the record's designated lookup attribute, and the display
    # field carries the textual form of the record itself.
    Ensures(Result().id_val == lookup_text(rec, to_field_name))
    Ensures(Result().text_val == display(rec))
    # post-conditions-end
    # impl-start
    return Entry(lookup_text(rec, to_field_name), display(rec))
    # impl-end


def build_results(view: View, recs: List[Record], to_field_name: int) -> List[Entry]:
    # pre-conditions-start
    Requires(Acc(list_pred(recs), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
             Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(recs), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
            Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
    Ensures(Acc(list_pred(Result())))
    # The answer sequence is aligned, one entry per record, IN ORDER ...
    Ensures(len(Result()) == len(recs))
    # ... and every entry is exactly what the responder's OWN replaceable
    # conversion step produces for the corresponding record. The responder
    # defers to its conversion step: it does not settle the entry contents
    # itself, so a responder supplying a different step changes every entry.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
            Result()[k] is record_entry(view, recs[k], to_field_name)))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[Entry]
    i = 0
    while i < len(recs):
        # invariants-start
        Invariant(Acc(list_pred(recs), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(recs),
                  Acc(recs[k].id_text, 1 / 8) and Acc(recs[k].display_text, 1 / 8)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(recs))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  result[k] is record_entry(view, recs[k], to_field_name)))))
        # invariants-end
        result.append(record_entry(view, recs[i], to_field_name))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Adversarial G-EQ (refinement fidelity) audit for django__django-14752 (nagini). commands run with SBU_BENCHMARK_DIR=benchmark-verified via python -m swebench_unified.adversary.

SPEC SHAPE (frozen, byte-identical across all attacks — same-spec exit 0 for all 7): build_results pins len(Result())==len(recs) AND Forall k: Result()[k] is record_entry(view, recs[k], to_field_name) — an IDENTITY to the opaque @Pure @ContractOnly callee record_entry (Ensures(True)). This is dischargeable ONLY by actually appending that exact per-record call; inlining a fixed Entry cannot prove the `is`. default_record_entry pins id_val==lookup_text(rec,tf) and text_val==display(rec). Both make the spec very tight.

ATTACKS (all copied from model.py editing ONLY impl regions; axioms/@Pure/Requires/Ensures byte-identical; each run via `adversary weakness nagini django__django-14752 <path>`):
- atk_1 (PREPATCH BUG: build_results inlines result.append(Entry(lookup_text(recs[i],tf), display(recs[i]))) instead of deferring to record_entry): same-spec SAME, verify FAILED at atk_1.py:185 'Loop invariant might not be preserved: Forall(...) result[k] is record_entry(...)'. weakness exit 2 (NOT-A-COUNTEREXAMPLE). => prepatch_reproduced=True; spec sees the bug exactly where the F2P test test_serialize_result observes it.
- atk_2 (boundary/field-swap id<->text: Entry(display(rec), lookup_text(rec,tf))): SAME, FAILED at atk_2.py:146 'Postcondition of default_record_entry might not hold: Result().id_val == lookup_text(rec,tf)'. exit 2.
- atk_3 (partial-domain: loop while i < len(recs)-1, drops last record): SAME, FAILED. exit 2.
- atk_4 (wrong-index echo: always record_entry(view, recs[0], tf)): SAME, FAILED. exit 2.
- atk_5 (control-flow-effect: return empty result list unconditionally): SAME, FAILED. exit 2.
- atk_6 (ungrounded-oracle echo: Entry(lookup_text, lookup_text) — id used for both fields): SAME, FAILED. exit 2.
- atk_7 (arg-perturbation: record_entry(view, recs[i], to_field_name + 1) — different attribute token): SAME, FAILED. exit 2.

Positive control: unchanged model.py copied to positive_control.py -> `adversary verify` VERIFIED in 20.5s (exit 0).

NO CANDIDATE (same-spec AND verifies) arose among the 7 wrong impls, so NO faithful refined patch / run_resolve execution was required or possible. Every attack was mechanically rejected by the frozen spec.

REFINEMENT.MD LEG AUDIT: A1=R (queryset<->List[Record], order), A2=A-consumed (record_entry opaque axiom <-> late-bound self.serialize_result dynamic dispatch; the fix), A3=R (result list<->'results' list), B1=I+A-consumed (Entry(lookup_text,display) <-> {'id':str(getattr..),'text':str(obj)}; lookup_text/display <-> str(getattr)/str builtins), plus the A-reference (default_record_entry deep model == real default serialize_result, validated by axiom_check.py check_default_reference, NOT consumed). No kind-3 leg: the one genuinely-changed op (deferral to overridable step) is A-consumed A2, an axiom about an unchanged-in-function callee the new code calls, not about the function under change. A-leg<->callee correspondences hold and are executed by G-AX (axiom_check.py: 6 boundary + 20000 fuzz, exit 0) and G-CONF (conformance_check.py: 13 boundary + 100000 fuzz batches over base + 2 overriding responders, exit 0).

VERDICT SOUND: 7 distinct same-spec wrong impls (>=5 required) all fail verification, positive control verifies, prepatch bug reproduced, refinement legs all R/A-consumed/A-reference/I with sound callee correspondence. verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14752 nagini bundle.

Model verifies (nagini_verify.sh: Verification successful, 18.7s). axiom_check.py — which reproduces the REAL gold-patch method bodies verbatim (AutocompleteJsonView.serialize_result and the get() results comprehension) — passes on 6 boundary + 20000 fuzz batches.

Agreement of modeled functions with real repo callees:
- build_results postcondition {len(Result())==len(recs); Result()[k] is record_entry(view,recs[k],tf) in order} matches the real get() comprehension [self.serialize_result(obj, tf) for obj in context['object_list']] one-per-record in order. No over-strengthening.
- record_entry axiom is opaque (Ensures(True)) → models late-bound self.serialize_result; pins no contents, so the spec demands only deferral to the dispatched step (the actual fix), not any fixed entry shape. It does not forbid behaviors the real repo permits.
- default_record_entry deep model Entry(lookup_text(rec,tf), display(rec)) == real default {'id': str(getattr(obj,tf)), 'text': str(obj)} — confirmed byte-equal keys+values over 20000 fuzz records by check_default_reference.
- lookup_text/display abstract unchanged str(getattr)/str builtins into id_text/display_text — faithful carrier refinement.
- Override-honoring dispatch (the F2P scenario: subclass adds 'extra' key) executed against real code in check_dispatch_honoured — builder defers to override, base yields default entries, all in order.

No input was found where the modeled function disagrees with the real callee. The spec is faithful and not too strong; the sole changed operation (deferral to the overridable conversion step) is modeled as an A-consumed opaque axiom whose dispatch property holds on the real executed code.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: PASSED=True, no hard failures). Independent review confirms NO leakage beyond the public problem_statement:

1. Public baseline is unusually explicit: the problem_statement itself fully specifies the gold edit — it names the new method serialize_result(self, obj, to_field_name), gives its exact body `return {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}`, and shows the `self.serialize_result(obj, to_field_name)` comprehension replacement plus the extension-point rationale. So anything the spec view could reveal about the gold is already solver-visible.

2. Identifiers: spec-view names (build_results, default_record_entry, record_entry, lookup_text, display, View, Record, Entry, id_text, display_text, id_val, text_val) do NOT echo the distinctive patched symbol `serialize_result`; the model abstracts the extension point to the neutral `record_entry`. (`get` strips to <4 chars, non-distinctive.) No spec-view identifier embeds a patched repo symbol not already in the problem statement.

3. Comment/docstring content: the str(getattr(obj, to_field_name)) / str(obj) fragments appear verbatim in the public problem_statement; the 'replaceable conversion step / extension point / defers to' prose paraphrases the problem statement's own 'result customization extension point' language — no new edit-localization.

4. No diff markers, no patched file path (django/contrib/admin/views/autocomplete.py) in the spec view; no bug/fix/patch/previously narration — docstring frames all as 'desired behaviour, not as an edit'.

The spec view is strictly more abstract than the already-fully-explicit problem statement. No spec-view line reconstructs the gold edit beyond public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
