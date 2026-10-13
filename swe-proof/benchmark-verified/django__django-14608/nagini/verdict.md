# P2 adversarial audit — django__django-14608

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. Both verifying candidates (atk_6, atk_7) are legitimate echoes: their materialized faithful patches RESOLVE under the official harness (resolved=true, all 4 FAIL_TO_PASS success, PASS_TO_PASS success). No verifying wrong impl whose faithful patch fails to resolve was found.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,34 +114,21 @@
                     ToSeq(collection.items) == ToSeq(rejection_messages)))
     # post-conditions-end
     # impl-start
-    # init site: rebuild the collection empty, with the marker tag.
     empty = []  # type: List[int]
-    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
     collection.css_class = init_class
     collection.items = empty
-    if group_flagged:
-        # a single group-wide message is appended to the collection before the
-        # rejection check (the collection is NOT rebuilt here, so the marker
-        # class set at the init site is preserved).
-        collection.items = collection.items + [group_message]
     if rejected:
-        # rejection site: rebuild the collection from the rejection messages,
-        # again with the marker tag (this replaces any earlier group-wide
-        # message held in the collection).
         items_copy = []  # type: List[int]
         i = 0
         while i < len(rejection_messages):
-            # invariants-start
             Invariant(Acc(list_pred(rejection_messages), 1 / 2))
             Invariant(Acc(list_pred(items_copy)))
             Invariant(0 <= i and i <= len(rejection_messages))
             Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
-            # invariants-end
             items_copy = items_copy + [rejection_messages[i]]
             i = i + 1
-        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
         collection.css_class = rej_class
         collection.items = items_copy
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,34 +114,23 @@
                     ToSeq(collection.items) == ToSeq(rejection_messages)))
     # post-conditions-end
     # impl-start
-    # init site: rebuild the collection empty, with the marker tag.
     empty = []  # type: List[int]
-    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
     collection.css_class = init_class
     collection.items = empty
     if group_flagged:
-        # a single group-wide message is appended to the collection before the
-        # rejection check (the collection is NOT rebuilt here, so the marker
-        # class set at the init site is preserved).
         collection.items = collection.items + [group_message]
     if rejected:
-        # rejection site: rebuild the collection from the rejection messages,
-        # again with the marker tag (this replaces any earlier group-wide
-        # message held in the collection).
         items_copy = []  # type: List[int]
         i = 0
-        while i < len(rejection_messages):
-            # invariants-start
+        while i < len(rejection_messages) - 1:
             Invariant(Acc(list_pred(rejection_messages), 1 / 2))
             Invariant(Acc(list_pred(items_copy)))
             Invariant(0 <= i and i <= len(rejection_messages))
             Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
-            # invariants-end
             items_copy = items_copy + [rejection_messages[i]]
             i = i + 1
-        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
         collection.css_class = rej_class
         collection.items = items_copy
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,34 +114,24 @@
                     ToSeq(collection.items) == ToSeq(rejection_messages)))
     # post-conditions-end
     # impl-start
-    # init site: rebuild the collection empty, with the marker tag.
     empty = []  # type: List[int]
-    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
     collection.css_class = init_class
     collection.items = empty
     if group_flagged:
-        # a single group-wide message is appended to the collection before the
-        # rejection check (the collection is NOT rebuilt here, so the marker
-        # class set at the init site is preserved).
         collection.items = collection.items + [group_message]
     if rejected:
-        # rejection site: rebuild the collection from the rejection messages,
-        # again with the marker tag (this replaces any earlier group-wide
-        # message held in the collection).
         items_copy = []  # type: List[int]
         i = 0
         while i < len(rejection_messages):
-            # invariants-start
             Invariant(Acc(list_pred(rejection_messages), 1 / 2))
             Invariant(Acc(list_pred(items_copy)))
             Invariant(0 <= i and i <= len(rejection_messages))
             Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
-            # invariants-end
             items_copy = items_copy + [rejection_messages[i]]
             i = i + 1
-        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
         collection.css_class = rej_class
         collection.items = items_copy
+        collection.items = collection.items + [group_message]
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,34 +114,23 @@
                     ToSeq(collection.items) == ToSeq(rejection_messages)))
     # post-conditions-end
     # impl-start
-    # init site: rebuild the collection empty, with the marker tag.
     empty = []  # type: List[int]
-    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116]
     collection.css_class = init_class
     collection.items = empty
     if group_flagged:
-        # a single group-wide message is appended to the collection before the
-        # rejection check (the collection is NOT rebuilt here, so the marker
-        # class set at the init site is preserved).
         collection.items = collection.items + [group_message]
     if rejected:
-        # rejection site: rebuild the collection from the rejection messages,
-        # again with the marker tag (this replaces any earlier group-wide
-        # message held in the collection).
         items_copy = []  # type: List[int]
         i = 0
         while i < len(rejection_messages):
-            # invariants-start
             Invariant(Acc(list_pred(rejection_messages), 1 / 2))
             Invariant(Acc(list_pred(items_copy)))
             Invariant(0 <= i and i <= len(rejection_messages))
             Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
-            # invariants-end
             items_copy = items_copy + [rejection_messages[i]]
             i = i + 1
-        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
         collection.css_class = rej_class
         collection.items = items_copy
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,34 +114,23 @@
                     ToSeq(collection.items) == ToSeq(rejection_messages)))
     # post-conditions-end
     # impl-start
-    # init site: rebuild the collection empty, with the marker tag.
     empty = []  # type: List[int]
-    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
     collection.css_class = init_class
     collection.items = empty
     if group_flagged:
-        # a single group-wide message is appended to the collection before the
-        # rejection check (the collection is NOT rebuilt here, so the marker
-        # class set at the init site is preserved).
         collection.items = collection.items + [group_message]
     if rejected:
-        # rejection site: rebuild the collection from the rejection messages,
-        # again with the marker tag (this replaces any earlier group-wide
-        # message held in the collection).
         items_copy = []  # type: List[int]
         i = 0
         while i < len(rejection_messages):
-            # invariants-start
             Invariant(Acc(list_pred(rejection_messages), 1 / 2))
             Invariant(Acc(list_pred(items_copy)))
             Invariant(0 <= i and i <= len(rejection_messages))
             Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
-            # invariants-end
             items_copy = items_copy + [rejection_messages[i]]
             i = i + 1
-        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116]
         collection.css_class = rej_class
         collection.items = items_copy
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -114,34 +114,21 @@
                     ToSeq(collection.items) == ToSeq(rejection_messages)))
     # post-conditions-end
     # impl-start
-    # init site: rebuild the collection empty, with the marker tag.
     empty = []  # type: List[int]
-    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
     collection.css_class = init_class
     collection.items = empty
     if group_flagged:
-        # a single group-wide message is appended to the collection before the
-        # rejection check (the collection is NOT rebuilt here, so the marker
-        # class set at the init site is preserved).
         collection.items = collection.items + [group_message]
     if rejected:
-        # rejection site: rebuild the collection from the rejection messages,
-        # again with the marker tag (this replaces any earlier group-wide
-        # message held in the collection).
         items_copy = []  # type: List[int]
         i = 0
         while i < len(rejection_messages):
-            # invariants-start
             Invariant(Acc(list_pred(rejection_messages), 1 / 2))
             Invariant(Acc(list_pred(items_copy)))
             Invariant(0 <= i and i <= len(rejection_messages))
             Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
-            # invariants-end
             items_copy = items_copy + [rejection_messages[i]]
             i = i + 1
-        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
-        collection.css_class = rej_class
         collection.items = items_copy
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -114,34 +114,26 @@
                     ToSeq(collection.items) == ToSeq(rejection_messages)))
     # post-conditions-end
     # impl-start
-    # init site: rebuild the collection empty, with the marker tag.
     empty = []  # type: List[int]
-    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+    gen = [101, 114, 114, 111, 114, 108, 105, 115, 116]  # 'errorlist'
+    tag = [110, 111, 110, 102, 111, 114, 109]  # 'nonform'
+    init_class = gen + [32] + tag
     collection.css_class = init_class
     collection.items = empty
-    if group_flagged:
-        # a single group-wide message is appended to the collection before the
-        # rejection check (the collection is NOT rebuilt here, so the marker
-        # class set at the init site is preserved).
-        collection.items = collection.items + [group_message]
+    if not rejected:
+        if group_flagged:
+            collection.items = collection.items + [group_message]
     if rejected:
-        # rejection site: rebuild the collection from the rejection messages,
-        # again with the marker tag (this replaces any earlier group-wide
-        # message held in the collection).
         items_copy = []  # type: List[int]
         i = 0
         while i < len(rejection_messages):
-            # invariants-start
             Invariant(Acc(list_pred(rejection_messages), 1 / 2))
             Invariant(Acc(list_pred(items_copy)))
             Invariant(0 <= i and i <= len(rejection_messages))
             Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
-            # invariants-end
             items_copy = items_copy + [rejection_messages[i]]
             i = i + 1
-        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
         collection.css_class = rej_class
         collection.items = items_copy
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,34 +114,23 @@
                     ToSeq(collection.items) == ToSeq(rejection_messages)))
     # post-conditions-end
     # impl-start
-    # init site: rebuild the collection empty, with the marker tag.
     empty = []  # type: List[int]
-    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
     collection.css_class = init_class
     collection.items = empty
-    if group_flagged:
-        # a single group-wide message is appended to the collection before the
-        # rejection check (the collection is NOT rebuilt here, so the marker
-        # class set at the init site is preserved).
-        collection.items = collection.items + [group_message]
     if rejected:
-        # rejection site: rebuild the collection from the rejection messages,
-        # again with the marker tag (this replaces any earlier group-wide
-        # message held in the collection).
         items_copy = []  # type: List[int]
         i = 0
         while i < len(rejection_messages):
-            # invariants-start
             Invariant(Acc(list_pred(rejection_messages), 1 / 2))
             Invariant(Acc(list_pred(items_copy)))
             Invariant(0 <= i and i <= len(rejection_messages))
             Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
-            # invariants-end
             items_copy = items_copy + [rejection_messages[i]]
             i = i + 1
-        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
-                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
+        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32, 110, 111, 110, 102, 111, 114, 109]
         collection.css_class = rej_class
         collection.items = items_copy
+    if group_flagged and not rejected:
+        collection.items = empty
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for django__django-14608.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of validation messages that are not attached to any individual
  member of a group renders with a marker tag in addition to the generic list
  tag, so a custom renderer can tell these group-wide messages apart from the
  per-member ones. Concretely, after the group's whole-clean step finishes, the
  collection holding those group-wide messages carries the rendered class
  attribute "errorlist nonform" (the generic class "errorlist" followed by the
  marker "nonform"), instead of the bare "errorlist".

  This holds on EVERY outcome of the whole-clean step. The held messages are
  exactly those the step produces:
    (1) the step accepts the data and nothing flagged the group as a whole:
        the collection stays empty;
    (2) the step accepts the data but the group as a whole was flagged once
        before the acceptance check: the collection holds exactly that single
        group-wide message;
    (3) the step rejects the data: the collection is rebuilt to carry exactly
        the rejection messages (replacing any earlier group-wide message).
  In every case the rendered class attribute is "errorlist nonform".

The message collection is modelled as a minimal class carrying only the two
touched, observable fields: its rendered class attribute and its held items,
both as `List[int]` of Unicode code points. The unchanged collection
constructor's rule for the class attribute — no marker tag yields the generic
class, a marker tag `t` yields the generic class, a space, then `t` — is
modelled deeply by the pure function `class_attr`, validated equal to the real
constructor out-of-band by axiom_check.py (G-AX), NOT consumed as an axiom.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class MessageCollection:
    def __init__(self, css_class: List[int], items: List[int]) -> None:
        Requires(Acc(list_pred(css_class)))
        Requires(Acc(list_pred(items)))
        Ensures(Acc(self.css_class) and self.css_class is css_class)  # type: ignore
        Ensures(Acc(self.items) and self.items is items)  # type: ignore
        self.css_class = css_class
        self.items = items


# axioms-start
# (no consumed @ContractOnly axioms: the only callee whose behaviour the proof
#  relies on — the collection constructor's class-attribute rule — is modelled
#  DEEPLY by the pure function `class_attr` below and validated == the real
#  constructor out-of-band by axiom_check.py / G-AX, so it is an A-reference,
#  not an A-consumed axiom.)
# axioms-end


# pure-start
@Pure
def generic_class() -> PSeq[int]:
    # 'errorlist' — the generic list class every such collection carries.
    return PSeq(101, 114, 114, 111, 114, 108, 105, 115, 116)


@Pure
def nonform_tag() -> PSeq[int]:
    # 'nonform' — the marker tag distinguishing group-wide messages.
    return PSeq(110, 111, 110, 102, 111, 114, 109)


@Pure
def class_attr(tag: PSeq[int]) -> PSeq[int]:
    """The rendered class attribute the collection constructor produces from an
    optional marker tag: an empty tag yields just the generic class; a non-empty
    tag `t` yields the generic class, a single space (U+0020), then `t`."""
    if len(tag) == 0:
        return generic_class()
    return generic_class() + PSeq(32) + tag
# pure-end


def finish_group_clean(collection: MessageCollection,
                       group_flagged: bool,
                       group_message: int,
                       rejected: bool,
                       rejection_messages: List[int]) -> None:
    # pre-conditions-start
    Requires(Acc(collection.css_class))
    Requires(Acc(collection.items))
    Requires(Acc(list_pred(rejection_messages), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(collection.css_class))
    Ensures(Acc(collection.items))
    Ensures(Acc(list_pred(rejection_messages), 1 / 2))
    Ensures(Acc(list_pred(collection.css_class)))
    Ensures(Acc(list_pred(collection.items)))
    # The collection's rendered class attribute carries the marker tag in
    # addition to the generic class, on EVERY outcome of the whole-clean step.
    Ensures(ToSeq(collection.css_class) == class_attr(nonform_tag()))
    # The held messages are exactly the step's product:
    #   - not rejected and nothing flagged the group as a whole: empty;
    #   - not rejected but the group as a whole was flagged once before the
    #     rejection check: exactly that single group-wide message;
    #   - rejected: exactly the rejection messages (the rebuild replaces any
    #     earlier group-wide message).
    Ensures(Implies(not rejected and not group_flagged,
                    len(collection.items) == 0))
    Ensures(Implies(not rejected and group_flagged,
                    ToSeq(collection.items) == PSeq(group_message)))
    Ensures(Implies(rejected,
                    ToSeq(collection.items) == ToSeq(rejection_messages)))
    # post-conditions-end
    # impl-start
    # init site: rebuild the collection empty, with the marker tag.
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        # a single group-wide message is appended to the collection before the
        # rejection check (the collection is NOT rebuilt here, so the marker
        # class set at the init site is preserved).
        collection.items = collection.items + [group_message]
    if rejected:
        # rejection site: rebuild the collection from the rejection messages,
        # again with the marker tag (this replaces any earlier group-wide
        # message held in the collection).
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            # invariants-start
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            # invariants-end
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-14608 (nagini). venv python (the 'python -m swebench_unified.adversary' in the prompt). All 8 attacks built by copying model.py and editing ONLY the impl region; spec/axioms/@Pure/Requires/Ensures byte-identical (adversary same-spec exit 0 confirmed for all 8).

SPEC OBSERVABLES: css_class pinned to class_attr(nonform_tag())=='errorlist nonform' on EVERY outcome; items pinned three-way: (!rejected&!group_flagged)->empty, (!rejected&group_flagged)->[group_message], rejected->rejection_messages. Both change sites (init line 336, exception line 383) sensed via prepatch models present in bundle.

WEAKNESS RESULTS (cmd: python -m swebench_unified.adversary weakness nagini django__django-14608 <atk>.py, run background in batches of 3, each JVM+Z3):
- atk_pos.py (=model.py correct impl): CANDIDATE verifies 15.7s (positive control PASS).
- atk_1 (partial-domain: omit group_flagged append): exit2 REJECTED (violates clause2).
- atk_2 (boundary: rejection loop stops at len-1): exit2 REJECTED (violates clause3).
- atk_3 (control-flow-effect: re-append group_message after rejection rebuild): exit2 REJECTED (rejected->exactly rejection_messages).
- atk_4 (ungrounded/wrong-class: init css bare 'errorlist' = prepatch_2 bug): exit2 REJECTED (css_class postcond).
- atk_5 (rejection-site css bare 'errorlist' = prepatch_1 bug): exit2 REJECTED (css_class postcond).
- atk_6 (ECHO: rejected path keeps init-site 'errorlist nonform' marker, replaces only items in place): CANDIDATE verifies 16.3s.
- atk_7 (ECHO: reordered `if not rejected: if group_flagged` + init css built via gen+[32]+tag concat; observably identical to gold): CANDIDATE verifies 14.9s.
- atk_8 (partial-domain2: clear items on non-rejected group_flagged path): exit2 REJECTED (clause2).

MANDATORY CANDIDATE RESOLVE (both verifying candidates materialized to faithful real-Django patches + run_resolve under official harness, SBU_BENCHMARK=swe_bench_verified, run background):
- atk_6 faithful patch (init error_class='nonform'; exception site mutates self._non_form_errors.data = list(e.error_list) in place, preserving the marker -> observably identical to gold): RESULT resolved=true, completed=true, patch_successfully_applied=true, FAIL_TO_PASS all 4 success (validate_max, validate_min, test_non_form_errors, test_non_form_errors_is_errorlist), PASS_TO_PASS success. => RESOLVES.
- atk_7 faithful patch (gold-equivalent, both sites tagged 'nonform'): RESULT resolved=true, completed=true, patch_successfully_applied=true, FAIL_TO_PASS all 4 success, PASS_TO_PASS success. => RESOLVES.
Both logs {atk_6,atk_7}.resolve.log.

verify=>correct HOLDS: every same-spec verifying impl found is either the correct impl or an echo whose faithful patch resolves; no verifying wrong impl whose faithful patch fails to resolve exists. 4 distinct wrong-impl classes correctly rejected at verify (partial-domain, boundary, control-flow-effect, ungrounded-oracle/wrong-class), plus 2 ungrounded-oracle echoes that verify AND resolve.

refinement.md A-LEG AUDIT: A2/A4 class_attr+nonform_tag = A-reference (deep model), NOT A-consumed; validated == real ErrorList.__init__ rule ('errorlist' if error_class None else 'errorlist {}'.format(t)) by axiom_check.py/G-AX, confirmed matches django/forms/utils.py __init__ lines 122-127 read from checked-out source. A2b = I+R (unchanged management-form append, modeled not dropped, verdict DEFECT 1). A1/A3 = R. No A-consumed axiom; no kind-3 leg (section C verified). Correspondence to real callee holds. Positive control verifies; both prepatch sites sensed. SOUND. Machine artifacts submitted for re-run (advisory verdict).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. Both verifying candidates (atk_6, atk_7) are legitimate echoes: their materialized faithful patches RESOLVE under the official harness (resolved=true, all 4 FAIL_TO_PASS success, PASS_TO_PASS success). No verifying wrong impl whose faithful patch fails to resolve was found.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for django__django-14608.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection of validation messages that are not attached to any individual
  member of a group renders with a marker tag in addition to the generic list
  tag, so a custom renderer can tell these group-wide messages apart from the
  per-member ones. Concretely, after the group's whole-clean step finishes, the
  collection holding those group-wide messages carries the rendered class
  attribute "errorlist nonform" (the generic class "errorlist" followed by the
  marker "nonform"), instead of the bare "errorlist".

  This holds on EVERY outcome of the whole-clean step. The held messages are
  exactly those the step produces:
    (1) the step accepts the data and nothing flagged the group as a whole:
        the collection stays empty;
    (2) the step accepts the data but the group as a whole was flagged once
        before the acceptance check: the collection holds exactly that single
        group-wide message;
    (3) the step rejects the data: the collection is rebuilt to carry exactly
        the rejection messages (replacing any earlier group-wide message).
  In every case the rendered class attribute is "errorlist nonform".

The message collection is modelled as a minimal class carrying only the two
touched, observable fields: its rendered class attribute and its held items,
both as `List[int]` of Unicode code points. The unchanged collection
constructor's rule for the class attribute — no marker tag yields the generic
class, a marker tag `t` yields the generic class, a space, then `t` — is
modelled deeply by the pure function `class_attr`, validated equal to the real
constructor out-of-band by axiom_check.py (G-AX), NOT consumed as an axiom.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class MessageCollection:
    def __init__(self, css_class: List[int], items: List[int]) -> None:
        Requires(Acc(list_pred(css_class)))
        Requires(Acc(list_pred(items)))
        Ensures(Acc(self.css_class) and self.css_class is css_class)  # type: ignore
        Ensures(Acc(self.items) and self.items is items)  # type: ignore
        self.css_class = css_class
        self.items = items


# axioms-start
# (no consumed @ContractOnly axioms: the only callee whose behaviour the proof
#  relies on — the collection constructor's class-attribute rule — is modelled
#  DEEPLY by the pure function `class_attr` below and validated == the real
#  constructor out-of-band by axiom_check.py / G-AX, so it is an A-reference,
#  not an A-consumed axiom.)
# axioms-end


# pure-start
@Pure
def generic_class() -> PSeq[int]:
    # 'errorlist' — the generic list class every such collection carries.
    return PSeq(101, 114, 114, 111, 114, 108, 105, 115, 116)


@Pure
def nonform_tag() -> PSeq[int]:
    # 'nonform' — the marker tag distinguishing group-wide messages.
    return PSeq(110, 111, 110, 102, 111, 114, 109)


@Pure
def class_attr(tag: PSeq[int]) -> PSeq[int]:
    """The rendered class attribute the collection constructor produces from an
    optional marker tag: an empty tag yields just the generic class; a non-empty
    tag `t` yields the generic class, a single space (U+0020), then `t`."""
    if len(tag) == 0:
        return generic_class()
    return generic_class() + PSeq(32) + tag
# pure-end


def finish_group_clean(collection: MessageCollection,
                       group_flagged: bool,
                       group_message: int,
                       rejected: bool,
                       rejection_messages: List[int]) -> None:
    # pre-conditions-start
    Requires(Acc(collection.css_class))
    Requires(Acc(collection.items))
    Requires(Acc(list_pred(rejection_messages), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(collection.css_class))
    Ensures(Acc(collection.items))
    Ensures(Acc(list_pred(rejection_messages), 1 / 2))
    Ensures(Acc(list_pred(collection.css_class)))
    Ensures(Acc(list_pred(collection.items)))
    # The collection's rendered class attribute carries the marker tag in
    # addition to the generic class, on EVERY outcome of the whole-clean step.
    Ensures(ToSeq(collection.css_class) == class_attr(nonform_tag()))
    # The held messages are exactly the step's product:
    #   - not rejected and nothing flagged the group as a whole: empty;
    #   - not rejected but the group as a whole was flagged once before the
    #     rejection check: exactly that single group-wide message;
    #   - rejected: exactly the rejection messages (the rebuild replaces any
    #     earlier group-wide message).
    Ensures(Implies(not rejected and not group_flagged,
                    len(collection.items) == 0))
    Ensures(Implies(not rejected and group_flagged,
                    ToSeq(collection.items) == PSeq(group_message)))
    Ensures(Implies(rejected,
                    ToSeq(collection.items) == ToSeq(rejection_messages)))
    # post-conditions-end
    # impl-start
    # init site: rebuild the collection empty, with the marker tag.
    empty = []  # type: List[int]
    init_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                  110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
    collection.css_class = init_class
    collection.items = empty
    if group_flagged:
        # a single group-wide message is appended to the collection before the
        # rejection check (the collection is NOT rebuilt here, so the marker
        # class set at the init site is preserved).
        collection.items = collection.items + [group_message]
    if rejected:
        # rejection site: rebuild the collection from the rejection messages,
        # again with the marker tag (this replaces any earlier group-wide
        # message held in the collection).
        items_copy = []  # type: List[int]
        i = 0
        while i < len(rejection_messages):
            # invariants-start
            Invariant(Acc(list_pred(rejection_messages), 1 / 2))
            Invariant(Acc(list_pred(items_copy)))
            Invariant(0 <= i and i <= len(rejection_messages))
            Invariant(ToSeq(items_copy) == ToSeq(rejection_messages).take(i))
            # invariants-end
            items_copy = items_copy + [rejection_messages[i]]
            i = i + 1
        rej_class = [101, 114, 114, 111, 114, 108, 105, 115, 116, 32,
                     110, 111, 110, 102, 111, 114, 109]  # 'errorlist nonform'
        collection.css_class = rej_class
        collection.items = items_copy
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-14608 (nagini). venv python (the 'python -m swebench_unified.adversary' in the prompt). All 8 attacks built by copying model.py and editing ONLY the impl region; spec/axioms/@Pure/Requires/Ensures byte-identical (adversary same-spec exit 0 confirmed for all 8).

SPEC OBSERVABLES: css_class pinned to class_attr(nonform_tag())=='errorlist nonform' on EVERY outcome; items pinned three-way: (!rejected&!group_flagged)->empty, (!rejected&group_flagged)->[group_message], rejected->rejection_messages. Both change sites (init line 336, exception line 383) sensed via prepatch models present in bundle.

WEAKNESS RESULTS (cmd: python -m swebench_unified.adversary weakness nagini django__django-14608 <atk>.py, run background in batches of 3, each JVM+Z3):
- atk_pos.py (=model.py correct impl): CANDIDATE verifies 15.7s (positive control PASS).
- atk_1 (partial-domain: omit group_flagged append): exit2 REJECTED (violates clause2).
- atk_2 (boundary: rejection loop stops at len-1): exit2 REJECTED (violates clause3).
- atk_3 (control-flow-effect: re-append group_message after rejection rebuild): exit2 REJECTED (rejected->exactly rejection_messages).
- atk_4 (ungrounded/wrong-class: init css bare 'errorlist' = prepatch_2 bug): exit2 REJECTED (css_class postcond).
- atk_5 (rejection-site css bare 'errorlist' = prepatch_1 bug): exit2 REJECTED (css_class postcond).
- atk_6 (ECHO: rejected path keeps init-site 'errorlist nonform' marker, replaces only items in place): CANDIDATE verifies 16.3s.
- atk_7 (ECHO: reordered `if not rejected: if group_flagged` + init css built via gen+[32]+tag concat; observably identical to gold): CANDIDATE verifies 14.9s.
- atk_8 (partial-domain2: clear items on non-rejected group_flagged path): exit2 REJECTED (clause2).

MANDATORY CANDIDATE RESOLVE (both verifying candidates materialized to faithful real-Django patches + run_resolve under official harness, SBU_BENCHMARK=swe_bench_verified, run background):
- atk_6 faithful patch (init error_class='nonform'; exception site mutates self._non_form_errors.data = list(e.error_list) in place, preserving the marker -> observably identical to gold): RESULT resolved=true, completed=true, patch_successfully_applied=true, FAIL_TO_PASS all 4 success (validate_max, validate_min, test_non_form_errors, test_non_form_errors_is_errorlist), PASS_TO_PASS success. => RESOLVES.
- atk_7 faithful patch (gold-equivalent, both sites tagged 'nonform'): RESULT resolved=true, completed=true, patch_successfully_applied=true, FAIL_TO_PASS all 4 success, PASS_TO_PASS success. => RESOLVES.
Both logs {atk_6,atk_7}.resolve.log.

verify=>correct HOLDS: every same-spec verifying impl found is either the correct impl or an echo whose faithful patch resolves; no verifying wrong impl whose faithful patch fails to resolve exists. 4 distinct wrong-impl classes correctly rejected at verify (partial-domain, boundary, control-flow-effect, ungrounded-oracle/wrong-class), plus 2 ungrounded-oracle echoes that verify AND resolve.

refinement.md A-LEG AUDIT: A2/A4 class_attr+nonform_tag = A-reference (deep model), NOT A-consumed; validated == real ErrorList.__init__ rule ('errorlist' if error_class None else 'errorlist {}'.format(t)) by axiom_check.py/G-AX, confirmed matches django/forms/utils.py __init__ lines 122-127 read from checked-out source. A2b = I+R (unchanged management-form append, modeled not dropped, verdict DEFECT 1). A1/A3 = R. No A-consumed axiom; no kind-3 leg (section C verified). Correspondence to real callee holds. Positive control verifies; both prepatch sites sensed. SOUND. Machine artifacts submitted for re-run (advisory verdict).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec drift / spec-too-strong) audit for nagini django__django-14608, finish_group_clean vs. real BaseFormSet.full_clean.

### METHOD (facts, not opinion):
1. same-spec: `swebench_unified.adversary same-spec` on an identity copy of model.py returned exit 0 — spec region byte-identical.
2. Differential conformance run AGAINST THE REAL PATCHED REPO (did not trust the bundle's recorded result): copied conformance_check.py, applied gold patch state is present (formsets.py:336 `self.error_class(error_class='nonform')`, :383 `self.error_class(e.error_list, error_class='nonform')`), ran with python3.10 + django 4.0.dev + asgiref/pytz/sqlparse. Result: G-CONF OK, 0 disagreements on 100162 inputs (162 boundary covering all 4 flag combos x assorted message lists including empty/dup/negative/large/len-50, + 100000 fuzz, seed 14608), plus builtin max/min raise witnesses. Shadow (contract-stripped impl region) == real post-state (rendered .error_class + held messages) on every input.
3. Extra hand-probes of the trickiest paths: (a) group_flagged AND rejected -> real returns class='errorlist nonform', items=['m1','m2'] — rebuild correctly REPLACES the appended group message, matching Implies(rejected, items==rejection_messages) independent of group_flagged; (b) unbound formset early-return -> class='errorlist nonform', items=[] matching the not-rejected/not-flagged clause.

SPEC-CLAUSE FIDELITY: css_class postcondition (== class_attr(nonform_tag()) on EVERY outcome) holds on real repo for accept-empty, accept+flag, reject, combined, and unbound paths. class_attr deep model ('errorlist' | 'errorlist {tag}') matches ErrorList.__init__ rule (utils.py:84-90). Three-way items clause faithful on all reachable paths, including the in-domain management-form-invalid append (DEFECT-1). Type refinement str->List[int] code points and structural item carry are sound.

No diverging input exists: the modeled function agrees with the real callee everywhere tested. Spec is not too strong / does not drift. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view = the marker-projected model.py (docstring + MessageCollection ctor + axioms/pure/pre/post regions; impl elided to '...'). mapping.md, refinement.md, meta.json, patch.diff are NOT part of the consumer view, so their naming of full_clean / django/forms/formsets.py is out of scope. Mechanical G-LEAK screen (leakage.screen, nagini/python flavor) PASSES with zero hard failures against the REAL dataset gold patch (adds error_class='nonform' to both self.error_class(...) constructions in BaseFormSet.full_clean): (1) no diff markers; (2) no gold changed-line reproduced in the normalized view (error_class='nonform', self.error_class(...), e.error_list all absent); (3) no patched file path 'django/forms/formsets.py' or dotted module path in view; (4) gold changed symbol is 'full_clean' — the spec uses the abstraction 'finish_group_clean' which does not embed it, and no comment/docstring names it; (5) no narration terms (bug/fix/patch/etc.). Beyond the mechanical screen: the public problem_statement ('Add `nonform` CSS class for non form errors in FormSets ... add the nonform CSS class ... custom ErrorList to make a distinction ... non form errors (FormSets)') already discloses the 'nonform' marker, the ErrorList/CSS-class mechanism, and the FormSets non-form-error target. The spec view's disclosure — that the collection's rendered class becomes 'errorlist nonform' (generic 'errorlist' + marker 'nonform') on every outcome — is the behavioral specification of exactly that publicly-stated feature, not a reveal of the code edit or its location. Specifying exact desired behavior is the spec's job; G-LEAK screens against reproducing the edit, which does not occur. The abstraction ('whole-clean step', control flags rejected/group_flagged, css_class/items as List[int]) discloses no gold-specific code beyond the public task. Note: meta.json.patch_diff is a placeholder string ('gold patch verbatim...'), not the real diff; screen was run against the authoritative dataset patch to avoid a false pass. Spec region byte-identity vs prepatch models is a G-DIFF/G-EQ concern, not leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
