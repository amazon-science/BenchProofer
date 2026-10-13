# P2 adversarial audit — django__django-13590

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl's faithful patch fails to resolve. The spec admits verifying impls that differ from gold only in the runtime TYPE of the returned container (plain list vs reconstructed same-kind tuple/namedtuple) — invisible to the List[int] value abstraction — but that difference is behaviourally inert on the tested inputs (Django's __range/__in lookups consume any sequence), so every verifying impl resolves. verify ⇒ correct holds.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # field-named kind handed a single (un-spread) iterable does not well-form a
     # container (the lone iterable cannot fill the separate fields).
     Requires(field_named == spread)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(elems), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The well-formed container holds exactly the elements, in order.
@@ -131,7 +129,6 @@
     # The input sequence is read-only; only fractional permission is needed and
     # returned (the spec may not be satisfied by overwriting the input).
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -161,22 +158,11 @@
         Invariant(0 <= i and i <= len(value))
         Invariant(len(resolved) == len(value) - i)
         Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == e)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
         resolved = [resolve_one(e)] + resolved
         i = i - 1
-    # Reconstruct the container of the same kind from the resolved elements,
-    # choosing the builder convention by the container kind so the construction
-    # is well-formed: a field-named kind gets its elements spread one-per-field
-    # (spread = True), a plain kind gets the single iterable (spread = False).
-    # Either way the well-formed construction holds the resolved elements and
-    # grants the token the postcondition requires.
-    if field_named:
-        result = build_container(resolved, field_named, True)
-    else:
-        result = build_container(resolved, field_named, False)
-    return result
+    return resolved
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # field-named kind handed a single (un-spread) iterable does not well-form a
     # container (the lone iterable cannot fill the separate fields).
     Requires(field_named == spread)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(elems), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The well-formed container holds exactly the elements, in order.
@@ -131,7 +129,6 @@
     # The input sequence is read-only; only fractional permission is needed and
     # returned (the spec may not be satisfied by overwriting the input).
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -161,22 +158,12 @@
         Invariant(0 <= i and i <= len(value))
         Invariant(len(resolved) == len(value) - i)
         Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == e)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
         resolved = [resolve_one(e)] + resolved
         i = i - 1
-    # Reconstruct the container of the same kind from the resolved elements,
-    # choosing the builder convention by the container kind so the construction
-    # is well-formed: a field-named kind gets its elements spread one-per-field
-    # (spread = True), a plain kind gets the single iterable (spread = False).
-    # Either way the well-formed construction holds the resolved elements and
-    # grants the token the postcondition requires.
-    if field_named:
-        result = build_container(resolved, field_named, True)
-    else:
-        result = build_container(resolved, field_named, False)
+    result = build_container(resolved, field_named, False)
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # field-named kind handed a single (un-spread) iterable does not well-form a
     # container (the lone iterable cannot fill the separate fields).
     Requires(field_named == spread)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(elems), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The well-formed container holds exactly the elements, in order.
@@ -131,7 +129,6 @@
     # The input sequence is read-only; only fractional permission is needed and
     # returned (the spec may not be satisfied by overwriting the input).
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -161,22 +158,15 @@
         Invariant(0 <= i and i <= len(value))
         Invariant(len(resolved) == len(value) - i)
         Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == e)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
         resolved = [resolve_one(e)] + resolved
         i = i - 1
-    # Reconstruct the container of the same kind from the resolved elements,
-    # choosing the builder convention by the container kind so the construction
-    # is well-formed: a field-named kind gets its elements spread one-per-field
-    # (spread = True), a plain kind gets the single iterable (spread = False).
-    # Either way the well-formed construction holds the resolved elements and
-    # grants the token the postcondition requires.
     if field_named:
-        result = build_container(resolved, field_named, True)
+        return resolved
     else:
         result = build_container(resolved, field_named, False)
-    return result
+        return result
     # impl-end
```

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # field-named kind handed a single (un-spread) iterable does not well-form a
     # container (the lone iterable cannot fill the separate fields).
     Requires(field_named == spread)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(elems), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The well-formed container holds exactly the elements, in order.
@@ -131,7 +129,6 @@
     # The input sequence is read-only; only fractional permission is needed and
     # returned (the spec may not be satisfied by overwriting the input).
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -161,22 +158,12 @@
         Invariant(0 <= i and i <= len(value))
         Invariant(len(resolved) == len(value) - i)
         Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == e)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
         resolved = [resolve_one(e)] + resolved
         i = i - 1
-    # Reconstruct the container of the same kind from the resolved elements,
-    # choosing the builder convention by the container kind so the construction
-    # is well-formed: a field-named kind gets its elements spread one-per-field
-    # (spread = True), a plain kind gets the single iterable (spread = False).
-    # Either way the well-formed construction holds the resolved elements and
-    # grants the token the postcondition requires.
-    if field_named:
-        result = build_container(resolved, field_named, True)
-    else:
-        result = build_container(resolved, field_named, False)
+    result = build_container(resolved, False, False)
     return result
     # impl-end
```

Attack 5 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # field-named kind handed a single (un-spread) iterable does not well-form a
     # container (the lone iterable cannot fill the separate fields).
     Requires(field_named == spread)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(elems), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The well-formed container holds exactly the elements, in order.
@@ -131,7 +129,6 @@
     # The input sequence is read-only; only fractional permission is needed and
     # returned (the spec may not be satisfied by overwriting the input).
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -161,22 +158,15 @@
         Invariant(0 <= i and i <= len(value))
         Invariant(len(resolved) == len(value) - i)
         Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == e)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
         resolved = [resolve_one(e)] + resolved
         i = i - 1
-    # Reconstruct the container of the same kind from the resolved elements,
-    # choosing the builder convention by the container kind so the construction
-    # is well-formed: a field-named kind gets its elements spread one-per-field
-    # (spread = True), a plain kind gets the single iterable (spread = False).
-    # Either way the well-formed construction holds the resolved elements and
-    # grants the token the postcondition requires.
     if field_named:
-        result = build_container(resolved, field_named, True)
+        tmp = build_container(resolved, field_named, True)
     else:
-        result = build_container(resolved, field_named, False)
-    return result
+        tmp = build_container(resolved, field_named, False)
+    return resolved
     # impl-end
```

Attack 6 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # field-named kind handed a single (un-spread) iterable does not well-form a
     # container (the lone iterable cannot fill the separate fields).
     Requires(field_named == spread)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(elems), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The well-formed container holds exactly the elements, in order.
@@ -131,7 +129,6 @@
     # The input sequence is read-only; only fractional permission is needed and
     # returned (the spec may not be satisfied by overwriting the input).
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -161,22 +158,18 @@
         Invariant(0 <= i and i <= len(value))
         Invariant(len(resolved) == len(value) - i)
         Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == e)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
         resolved = [resolve_one(e)] + resolved
         i = i - 1
-    # Reconstruct the container of the same kind from the resolved elements,
-    # choosing the builder convention by the container kind so the construction
-    # is well-formed: a field-named kind gets its elements spread one-per-field
-    # (spread = True), a plain kind gets the single iterable (spread = False).
-    # Either way the well-formed construction holds the resolved elements and
-    # grants the token the postcondition requires.
+    if len(value) == 0:
+        e0 = build_container(resolved, field_named, field_named)
+        return resolved
     if field_named:
-        result = build_container(resolved, field_named, True)
+        t1 = build_container(resolved, field_named, True)
     else:
-        result = build_container(resolved, field_named, False)
-    return result
+        t1 = build_container(resolved, field_named, False)
+    return resolved
     # impl-end
```

Attack 7 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # field-named kind handed a single (un-spread) iterable does not well-form a
     # container (the lone iterable cannot fill the separate fields).
     Requires(field_named == spread)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(elems), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The well-formed container holds exactly the elements, in order.
@@ -131,7 +129,6 @@
     # The input sequence is read-only; only fractional permission is needed and
     # returned (the spec may not be satisfied by overwriting the input).
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -161,22 +158,13 @@
         Invariant(0 <= i and i <= len(value))
         Invariant(len(resolved) == len(value) - i)
         Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == e)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
         resolved = [resolve_one(e)] + resolved
         i = i - 1
-    # Reconstruct the container of the same kind from the resolved elements,
-    # choosing the builder convention by the container kind so the construction
-    # is well-formed: a field-named kind gets its elements spread one-per-field
-    # (spread = True), a plain kind gets the single iterable (spread = False).
-    # Either way the well-formed construction holds the resolved elements and
-    # grants the token the postcondition requires.
-    if field_named:
-        result = build_container(resolved, field_named, True)
-    else:
-        result = build_container(resolved, field_named, False)
+    spread = field_named
+    result = build_container(resolved, field_named, spread)
     return result
     # impl-end
```

Attack 8 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # field-named kind handed a single (un-spread) iterable does not well-form a
     # container (the lone iterable cannot fill the separate fields).
     Requires(field_named == spread)
-    Requires(MustTerminate(2))
     Ensures(Acc(list_pred(elems), 1 / 2))
     Ensures(Acc(list_pred(Result())))
     # The well-formed container holds exactly the elements, in order.
@@ -131,7 +129,6 @@
     # The input sequence is read-only; only fractional permission is needed and
     # returned (the spec may not be satisfied by overwriting the input).
     Requires(Acc(list_pred(value), 1 / 2))
-    Requires(MustTerminate(3))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(value), 1 / 2))
@@ -161,22 +158,12 @@
         Invariant(0 <= i and i <= len(value))
         Invariant(len(resolved) == len(value) - i)
         Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
-        Invariant(MustTerminate(i + 1))
         # invariants-end
         e = value[i - 1]
         Assert(ToSeq(value).drop(i - 1)[0] == e)
         Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
         resolved = [resolve_one(e)] + resolved
         i = i - 1
-    # Reconstruct the container of the same kind from the resolved elements,
-    # choosing the builder convention by the container kind so the construction
-    # is well-formed: a field-named kind gets its elements spread one-per-field
-    # (spread = True), a plain kind gets the single iterable (spread = False).
-    # Either way the well-formed construction holds the resolved elements and
-    # grants the token the postcondition requires.
-    if field_named:
-        result = build_container(resolved, field_named, True)
-    else:
-        result = build_container(resolved, field_named, False)
-    return result
+    Fold(well_formed_container(ToSeq(resolved), field_named))
+    return resolved
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13590.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a lookup argument is a sequence of sub-values, each sub-value is
  resolved independently and a NEW container of the SAME kind is produced from
  the resolved sub-values. Container kinds differ in HOW their builder accepts
  the elements, and crucially in WHETHER the builder even succeeds:

    * a plain positional sequence kind, whose builder consumes a single
      iterable holding all the elements and succeeds; and
    * a field-named sequence kind, whose builder instead takes the elements as
      SEPARATE positional arguments (one per field). Handed the elements as
      separate positional arguments it succeeds and produces a well-formed
      container; handed a single iterable instead it does NOT produce a
      well-formed container at all — the lone iterable would occupy just the
      first field, leaving the remaining required fields unfilled, so the
      construction FAILS rather than yielding a usable container.

  The reconstruction must, for EITHER kind, yield a WELL-FORMED container
  holding exactly the resolved sub-values, in order: its length equals the
  number of sub-values and its i-th element is the independent resolution of the
  i-th input sub-value. Producing a well-formed container is the load-bearing
  requirement: for a field-named kind the elements must be supplied one per
  field (spread across the fields), never bundled into a single iterable
  argument, because only the per-field convention yields a well-formed container
  for such a kind — the single-iterable convention does not construct one.

The sequence of sub-values is modelled as a `List[int]` of opaque sub-value
identities. The unchanged per-element resolution (recursively resolving one
sub-value) is axiomatized as a deterministic pure callee `resolve_one`. The
container builder is an UNCHANGED callee too (the constructor of the container
kind): it is axiomatized as `build_container`. Its contract captures the effect
that distinguishes the two calling conventions — for a field-named kind only the
per-field convention constructs a well-formed container, the single-iterable
convention does not — by granting an unforgeable `well_formed_container` token
ONLY when the convention matches the kind. The reconstruction's own
postcondition REQUIRES that token, so a verifying reconstruction must route its
result through a successful (convention-matching) construction; it cannot return
a container the builder never well-formed. No callee under change is
axiomatized; the constructor contract is validated against the real Python
container semantics out-of-band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def resolve_one(sub_value: int) -> int:
    """Independent resolution of a single sub-value (the unchanged recursive
    resolution of one element of the sequence). Deterministic: the resolution
    of a sub-value depends only on the sub-value. The unchanged callee the
    reconstruction maps over; never the operation under change. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """


# Abstract token marking a container that was PRODUCED BY a SUCCESSFUL builder
# call for its kind: a capability the builder grants on its output and that
# nothing else can fabricate. Its arguments record the container contents and
# the kind it was built for. The reconstruction's result must hold this token
# for the kind it claims to rebuild, so the result can only be a container the
# builder actually well-formed for that kind — a builder call under the
# convention that does not match a field-named kind never grants it (the
# construction does not succeed). Provenance + executable soundness check:
# mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def well_formed_container(contents: PSeq[int], field_named: bool) -> bool:
    pass


@ContractOnly
def build_container(elems: List[int], field_named: bool, spread: bool) -> List[int]:
    """Container-builder callee (the UNCHANGED constructor of the container
    kind). It is invoked under one of two conventions:

      * `spread == False`: the elements are handed to the builder as a SINGLE
        iterable (the constructor receives one positional argument holding all
        the elements);
      * `spread == True`: the elements are SPREAD one-per-field (the constructor
        receives the elements as separate positional arguments).

    The construction is only WELL-FORMED — actually yielding a usable container
    holding the elements — when the convention matches the container kind: a
    plain kind well-forms from the single iterable; a field-named kind well-forms
    only from the spread, because the single iterable would leave its required
    fields unfilled. That match is `field_named == spread`, which is the
    builder's precondition for a well-formed construction. On a well-formed
    construction it returns a fresh container holding exactly the elements, in
    order, AND grants the `well_formed_container` token on its output for this
    kind. Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(elems), 1 / 2))
    # A well-formed construction requires the convention to match the kind. A
    # field-named kind handed a single (un-spread) iterable does not well-form a
    # container (the lone iterable cannot fill the separate fields).
    Requires(field_named == spread)
    Ensures(Acc(list_pred(elems), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The well-formed container holds exactly the elements, in order.
    Ensures(len(Result()) == len(elems))
    Ensures(ToSeq(Result()) == Old(ToSeq(elems)))
    # ...and is marked as a builder-produced well-formed container for this kind.
    Ensures(well_formed_container(ToSeq(Result()), field_named))
# axioms-end


# pure-start
@Pure
def resolved_seq(s: PSeq[int]) -> PSeq[int]:
    """The element-wise resolution of a whole sequence: each element replaced by
    its independent resolution. Front-recursive so a single unfold is available
    to callers at each loop step. Length-preserving (one resolved element per
    input element)."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(resolve_one(s[0])) + resolved_seq(s.drop(1))
# pure-end


def resolve_sequence(value: List[int], field_named: bool) -> List[int]:
    # pre-conditions-start
    # The input sequence is read-only; only fractional permission is needed and
    # returned (the spec may not be satisfied by overwriting the input).
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reconstruction holds exactly the resolved sub-values, in order, for
    # BOTH container kinds: same length and element-wise independent resolution.
    Ensures(len(Result()) == len(value))
    Ensures(ToSeq(Result()) == resolved_seq(ToSeq(value)))
    # The result must be a WELL-FORMED container the builder actually produced
    # for THIS kind — it holds the token the builder grants only on a successful
    # (convention-matching) construction. For a field-named kind that means the
    # result went through the per-field (spread) construction; a result the
    # builder never well-formed (e.g. one assembled without going through a
    # successful builder call for this kind) lacks the token. This is the
    # load-bearing clause: it cannot be discharged by value-equality alone,
    # because the elements are identical whether or not the field-named builder
    # would have succeeded — the discriminator is the construction effect.
    Ensures(well_formed_container(ToSeq(Result()), field_named))
    # post-conditions-end
    # impl-start
    resolved = []  # type: List[int]
    i = len(value)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(resolved)))
        Invariant(0 <= i and i <= len(value))
        Invariant(len(resolved) == len(value) - i)
        Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
        # invariants-end
        e = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == e)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        resolved = [resolve_one(e)] + resolved
        i = i - 1
    # Reconstruct the container of the same kind from the resolved elements,
    # choosing the builder convention by the container kind so the construction
    # is well-formed: a field-named kind gets its elements spread one-per-field
    # (spread = True), a plain kind gets the single iterable (spread = False).
    # Either way the well-formed construction holds the resolved elements and
    # grants the token the postcondition requires.
    if field_named:
        result = build_container(resolved, field_named, True)
    else:
        result = build_container(resolved, field_named, False)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

All commands run there.

SPEC SHAPE: resolve_sequence postcondition pins contents exactly (len==len, ToSeq(Result())==resolved_seq(ToSeq(value))) AND requires the unforgeable token well_formed_container(ToSeq(Result()), field_named), granted only by a convention-matching build_container call (precondition field_named==spread). The only residual freedom the List[int] abstraction cannot observe is the returned container's runtime type/identity — the atk_6 class.

SAME-SPEC: all 8 attacks + positive control are byte-identical in spec (adversary same-spec => SAME).

### WEAKNESS RESULTS (python -m swebench_unified.adversary weakness nagini django__django-13590 <atk>):
- atk_1 (return resolved, never build): exit 2 NOT-A-COUNTEREXAMPLE (fails verify: no token). REJECTED.
- atk_2 (literal prepatch: build_container(resolved, field_named, False) unconditionally): exit 2 (fails precondition field_named==spread). REJECTED. == prepatch bug.
- atk_3 (namedtuple-path bug: if field_named: return resolved): exit 2 (no token on field-named branch). REJECTED.
- atk_5 (claim plain kind: build_container(resolved, False, False)): exit 2 (token key mismatch (_,False) vs (_,field_named)). REJECTED.
- atk_9 (ungrounded-oracle echo: Fold(well_formed_container(...))): exit 2 (abstract @Predicate cannot be Folded). REJECTED.
- atk_6 (build matching-convention -> earn token, then return the value-equal plain list): exit 0 CANDIDATE (17.7s).
- atk_7 (boundary/partial-domain: empty-case builds+returns list; nonempty builds+returns list): exit 0 CANDIDATE (17.8s).
- atk_8 (correct computed-spread: spread=field_named single call, return build result): exit 0 CANDIDATE (16.6s).

MANDATORY RESOLVE ON EVERY CANDIDATE (official harness via run_evaluation, --namespace swebench --instance_image_tag latest, image swebench/sweb.eval.x86_64.django_1776_django-13590 present locally):
- atk_6 faithful patch (patch_6.diff): patch_successfully_applied=True, RESOLVED=True (F2P test_range_lookup_namedtuple PASS; 145/145 P2P pass, 0 fail). run_id sbu-atk-6.
- atk_7 faithful patch (patch_7.diff): applied=True, RESOLVED=True (F2P pass, 0 P2P fail). run_id sbu-atk-7.
- atk_8 faithful patch (patch_8.diff): applied=True, RESOLVED=True (F2P pass, 0 P2P fail). run_id sbu-atk-8.
- GOLD (dataset patch, sanity): RESOLVED=True. run_id sbu-diag-gold.
Every verifying candidate's materialized faithful patch RESOLVES => spec is NOT broken.

Why the plain-list-return candidates (atk_6/atk_7) still resolve: they perform the convention-matching construction (no raise — the load-bearing fix behaviour) but return the value-equal materialized list instead of the reconstructed container. The runtime container type is unobserved by the F2P test (filters on EmployeeRange(minimum=51, maximum=100) and checks the queryset; the __range lookup accepts any 2-element sequence) and by all P2P. This is exactly the SOUND verifying-attack class documented in refinement.md §B (atk_6) — admitting it is not a soundness defect.

PREPATCH REPRODUCED: model_prepatch.py (single-iterable regardless of kind) FAILS verification: 'model_prepatch.py:170: The precondition of method build_container might not hold. Assertion (field_named == spread) might not hold.' (18.7s). This is the G-DIFF sense of the bug and matches the real prepatch TypeError (namedtuple __new__ missing positional arg).

POSITIVE CONTROL: pos_control.py (= gold-faithful model.py) VERIFIES in 19.8s => spec non-vacuous.

G-AX (A-leg correspondence): axiom_check.py exit 0 — resolve_one determinism/identity on 12 scalars; reconstruction deep model (plain single-iterable==elements, namedtuple spread==elements, namedtuple single-iterable raises/wrong) sound on 7 boundary + 20000 fuzz element lists. Both axioms (resolve_one; build_container + well_formed_container) map to UNCHANGED callees (per-element resolve; the container constructor), consistent with mapping.md §4.

REFINEMENT.MD LEG AUDIT: A1,A2 = R (type refinements: value->List[int]; field_named<->hasattr _make). A3 = A-consumed (resolve_one, the unchanged per-element resolution, purity/determinism only). A4 = A-consumed (build_container+well_formed_container, unchanged constructor) + I (the spread choice, an identical concrete control-flow op living in the impl). §D: NO kind-3 legs — the genuinely-changed op (spread choice) is in the impl as I; its raise/succeed control-flow EFFECT is captured by the unchanged constructor's contract via the capability token. Correspondence of both A-legs to the real callees holds (G-AX rc=0). AUDIT SOUND.

VERDICT: SOUND — >=5 attacks run (8 total: 5 reject at verify, 3 verify-and-resolve), none breaks the spec; every verifying candidate's faithful refined patch RESOLVES under the official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_9.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE — no verifying wrong impl's faithful patch fails to resolve. The spec admits verifying impls that differ from gold only in the runtime TYPE of the returned container (plain list vs reconstructed same-kind tuple/namedtuple) — invisible to the List[int] value abstraction — but that difference is behaviourally inert on the tested inputs (Django's __range/__in lookups consume any sequence), so every verifying impl resolves. verify ⇒ correct holds.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13590.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a lookup argument is a sequence of sub-values, each sub-value is
  resolved independently and a NEW container of the SAME kind is produced from
  the resolved sub-values. Container kinds differ in HOW their builder accepts
  the elements, and crucially in WHETHER the builder even succeeds:

    * a plain positional sequence kind, whose builder consumes a single
      iterable holding all the elements and succeeds; and
    * a field-named sequence kind, whose builder instead takes the elements as
      SEPARATE positional arguments (one per field). Handed the elements as
      separate positional arguments it succeeds and produces a well-formed
      container; handed a single iterable instead it does NOT produce a
      well-formed container at all — the lone iterable would occupy just the
      first field, leaving the remaining required fields unfilled, so the
      construction FAILS rather than yielding a usable container.

  The reconstruction must, for EITHER kind, yield a WELL-FORMED container
  holding exactly the resolved sub-values, in order: its length equals the
  number of sub-values and its i-th element is the independent resolution of the
  i-th input sub-value. Producing a well-formed container is the load-bearing
  requirement: for a field-named kind the elements must be supplied one per
  field (spread across the fields), never bundled into a single iterable
  argument, because only the per-field convention yields a well-formed container
  for such a kind — the single-iterable convention does not construct one.

The sequence of sub-values is modelled as a `List[int]` of opaque sub-value
identities. The unchanged per-element resolution (recursively resolving one
sub-value) is axiomatized as a deterministic pure callee `resolve_one`. The
container builder is an UNCHANGED callee too (the constructor of the container
kind): it is axiomatized as `build_container`. Its contract captures the effect
that distinguishes the two calling conventions — for a field-named kind only the
per-field convention constructs a well-formed container, the single-iterable
convention does not — by granting an unforgeable `well_formed_container` token
ONLY when the convention matches the kind. The reconstruction's own
postcondition REQUIRES that token, so a verifying reconstruction must route its
result through a successful (convention-matching) construction; it cannot return
a container the builder never well-formed. No callee under change is
axiomatized; the constructor contract is validated against the real Python
container semantics out-of-band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def resolve_one(sub_value: int) -> int:
    """Independent resolution of a single sub-value (the unchanged recursive
    resolution of one element of the sequence). Deterministic: the resolution
    of a sub-value depends only on the sub-value. The unchanged callee the
    reconstruction maps over; never the operation under change. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """


# Abstract token marking a container that was PRODUCED BY a SUCCESSFUL builder
# call for its kind: a capability the builder grants on its output and that
# nothing else can fabricate. Its arguments record the container contents and
# the kind it was built for. The reconstruction's result must hold this token
# for the kind it claims to rebuild, so the result can only be a container the
# builder actually well-formed for that kind — a builder call under the
# convention that does not match a field-named kind never grants it (the
# construction does not succeed). Provenance + executable soundness check:
# mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def well_formed_container(contents: PSeq[int], field_named: bool) -> bool:
    pass


@ContractOnly
def build_container(elems: List[int], field_named: bool, spread: bool) -> List[int]:
    """Container-builder callee (the UNCHANGED constructor of the container
    kind). It is invoked under one of two conventions:

      * `spread == False`: the elements are handed to the builder as a SINGLE
        iterable (the constructor receives one positional argument holding all
        the elements);
      * `spread == True`: the elements are SPREAD one-per-field (the constructor
        receives the elements as separate positional arguments).

    The construction is only WELL-FORMED — actually yielding a usable container
    holding the elements — when the convention matches the container kind: a
    plain kind well-forms from the single iterable; a field-named kind well-forms
    only from the spread, because the single iterable would leave its required
    fields unfilled. That match is `field_named == spread`, which is the
    builder's precondition for a well-formed construction. On a well-formed
    construction it returns a fresh container holding exactly the elements, in
    order, AND grants the `well_formed_container` token on its output for this
    kind. Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(elems), 1 / 2))
    # A well-formed construction requires the convention to match the kind. A
    # field-named kind handed a single (un-spread) iterable does not well-form a
    # container (the lone iterable cannot fill the separate fields).
    Requires(field_named == spread)
    Ensures(Acc(list_pred(elems), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The well-formed container holds exactly the elements, in order.
    Ensures(len(Result()) == len(elems))
    Ensures(ToSeq(Result()) == Old(ToSeq(elems)))
    # ...and is marked as a builder-produced well-formed container for this kind.
    Ensures(well_formed_container(ToSeq(Result()), field_named))
# axioms-end


# pure-start
@Pure
def resolved_seq(s: PSeq[int]) -> PSeq[int]:
    """The element-wise resolution of a whole sequence: each element replaced by
    its independent resolution. Front-recursive so a single unfold is available
    to callers at each loop step. Length-preserving (one resolved element per
    input element)."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(resolve_one(s[0])) + resolved_seq(s.drop(1))
# pure-end


def resolve_sequence(value: List[int], field_named: bool) -> List[int]:
    # pre-conditions-start
    # The input sequence is read-only; only fractional permission is needed and
    # returned (the spec may not be satisfied by overwriting the input).
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reconstruction holds exactly the resolved sub-values, in order, for
    # BOTH container kinds: same length and element-wise independent resolution.
    Ensures(len(Result()) == len(value))
    Ensures(ToSeq(Result()) == resolved_seq(ToSeq(value)))
    # The result must be a WELL-FORMED container the builder actually produced
    # for THIS kind — it holds the token the builder grants only on a successful
    # (convention-matching) construction. For a field-named kind that means the
    # result went through the per-field (spread) construction; a result the
    # builder never well-formed (e.g. one assembled without going through a
    # successful builder call for this kind) lacks the token. This is the
    # load-bearing clause: it cannot be discharged by value-equality alone,
    # because the elements are identical whether or not the field-named builder
    # would have succeeded — the discriminator is the construction effect.
    Ensures(well_formed_container(ToSeq(Result()), field_named))
    # post-conditions-end
    # impl-start
    resolved = []  # type: List[int]
    i = len(value)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(resolved)))
        Invariant(0 <= i and i <= len(value))
        Invariant(len(resolved) == len(value) - i)
        Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
        # invariants-end
        e = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == e)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        resolved = [resolve_one(e)] + resolved
        i = i - 1
    # Reconstruct the container of the same kind from the resolved elements,
    # choosing the builder convention by the container kind so the construction
    # is well-formed: a field-named kind gets its elements spread one-per-field
    # (spread = True), a plain kind gets the single iterable (spread = False).
    # Either way the well-formed construction holds the resolved elements and
    # grants the token the postcondition requires.
    if field_named:
        result = build_container(resolved, field_named, True)
    else:
        result = build_container(resolved, field_named, False)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

All commands run there.

SPEC SHAPE: resolve_sequence postcondition pins contents exactly (len==len, ToSeq(Result())==resolved_seq(ToSeq(value))) AND requires the unforgeable token well_formed_container(ToSeq(Result()), field_named), granted only by a convention-matching build_container call (precondition field_named==spread). The only residual freedom the List[int] abstraction cannot observe is the returned container's runtime type/identity — the atk_6 class.

SAME-SPEC: all 8 attacks + positive control are byte-identical in spec (adversary same-spec => SAME).

### WEAKNESS RESULTS (python -m swebench_unified.adversary weakness nagini django__django-13590 <atk>):
- atk_1 (return resolved, never build): exit 2 NOT-A-COUNTEREXAMPLE (fails verify: no token). REJECTED.
- atk_2 (literal prepatch: build_container(resolved, field_named, False) unconditionally): exit 2 (fails precondition field_named==spread). REJECTED. == prepatch bug.
- atk_3 (namedtuple-path bug: if field_named: return resolved): exit 2 (no token on field-named branch). REJECTED.
- atk_5 (claim plain kind: build_container(resolved, False, False)): exit 2 (token key mismatch (_,False) vs (_,field_named)). REJECTED.
- atk_9 (ungrounded-oracle echo: Fold(well_formed_container(...))): exit 2 (abstract @Predicate cannot be Folded). REJECTED.
- atk_6 (build matching-convention -> earn token, then return the value-equal plain list): exit 0 CANDIDATE (17.7s).
- atk_7 (boundary/partial-domain: empty-case builds+returns list; nonempty builds+returns list): exit 0 CANDIDATE (17.8s).
- atk_8 (correct computed-spread: spread=field_named single call, return build result): exit 0 CANDIDATE (16.6s).

MANDATORY RESOLVE ON EVERY CANDIDATE (official harness via run_evaluation, --namespace swebench --instance_image_tag latest, image swebench/sweb.eval.x86_64.django_1776_django-13590 present locally):
- atk_6 faithful patch (patch_6.diff): patch_successfully_applied=True, RESOLVED=True (F2P test_range_lookup_namedtuple PASS; 145/145 P2P pass, 0 fail). run_id sbu-atk-6.
- atk_7 faithful patch (patch_7.diff): applied=True, RESOLVED=True (F2P pass, 0 P2P fail). run_id sbu-atk-7.
- atk_8 faithful patch (patch_8.diff): applied=True, RESOLVED=True (F2P pass, 0 P2P fail). run_id sbu-atk-8.
- GOLD (dataset patch, sanity): RESOLVED=True. run_id sbu-diag-gold.
Every verifying candidate's materialized faithful patch RESOLVES => spec is NOT broken.

Why the plain-list-return candidates (atk_6/atk_7) still resolve: they perform the convention-matching construction (no raise — the load-bearing fix behaviour) but return the value-equal materialized list instead of the reconstructed container. The runtime container type is unobserved by the F2P test (filters on EmployeeRange(minimum=51, maximum=100) and checks the queryset; the __range lookup accepts any 2-element sequence) and by all P2P. This is exactly the SOUND verifying-attack class documented in refinement.md §B (atk_6) — admitting it is not a soundness defect.

PREPATCH REPRODUCED: model_prepatch.py (single-iterable regardless of kind) FAILS verification: 'model_prepatch.py:170: The precondition of method build_container might not hold. Assertion (field_named == spread) might not hold.' (18.7s). This is the G-DIFF sense of the bug and matches the real prepatch TypeError (namedtuple __new__ missing positional arg).

POSITIVE CONTROL: pos_control.py (= gold-faithful model.py) VERIFIES in 19.8s => spec non-vacuous.

G-AX (A-leg correspondence): axiom_check.py exit 0 — resolve_one determinism/identity on 12 scalars; reconstruction deep model (plain single-iterable==elements, namedtuple spread==elements, namedtuple single-iterable raises/wrong) sound on 7 boundary + 20000 fuzz element lists. Both axioms (resolve_one; build_container + well_formed_container) map to UNCHANGED callees (per-element resolve; the container constructor), consistent with mapping.md §4.

REFINEMENT.MD LEG AUDIT: A1,A2 = R (type refinements: value->List[int]; field_named<->hasattr _make). A3 = A-consumed (resolve_one, the unchanged per-element resolution, purity/determinism only). A4 = A-consumed (build_container+well_formed_container, unchanged constructor) + I (the spread choice, an identical concrete control-flow op living in the impl). §D: NO kind-3 legs — the genuinely-changed op (spread choice) is in the impl as I; its raise/succeed control-flow EFFECT is captured by the unchanged constructor's contract via the capability token. Correspondence of both A-legs to the real callees holds (G-AX rc=0). AUDIT SOUND.

VERDICT: SOUND — >=5 attacks run (8 total: 5 reject at verify, 3 verify-and-resolve), none breaks the spec; every verifying candidate's faithful refined patch RESOLVES under the official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No divergence found between the modeled resolve_sequence and the real repo callee (list/tuple branch of Query.resolve_lookup_value @ base_commit 755dbf3). Mechanical checks: model.py verifies (rc=0, 17.9s); model_prepatch.py fails exactly at the discriminating precondition `field_named == spread` (line 170) — the spec correctly senses the namedtuple bug; same-spec tooling confirms byte-identical spec region. Faithfulness reasoning: the postcondition (i) ToSeq(Result()) == resolved_seq(ToSeq(value)) with len preserved, and (ii) well_formed_container(ToSeq(Result()), field_named) is satisfied by post-patch gold on EVERY input — for a namedtuple value the element count equals the field count so type_(*values) always well-forms; for list/tuple type_(values) always well-forms. The boolean field_named faithfully abstracts hasattr(type_,'_make'), and the well_formed_container capability token faithfully abstracts the raise/succeed control-flow effect (invisible to a List[int] value abstraction), cross-checked against REAL Python constructor semantics by axiom_check.py on 7 boundary + 20000 fuzz lists (2-field namedtuple single-iterable raises TypeError = issue's exact error; spread succeeds; plain succeeds) — I re-confirmed these facts directly. The spec is not too strong: atk_6 (value-equal materialized list) verifies AND resolves per refinement.md/meta, so correct resolving impls are admitted. Note: conformance_check.py is absent from the bundle (listed in prompt but not present) — orthogonal to G-PANEL-2 faithfulness, which concerns spec-vs-repo drift, and none exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no gold-patch changed line reproduced, no patched file path/module path, no spec-view identifier embedding a patched repo symbol, no bug/fix narration). Semantic check also clean: the spec view reveals nothing about the gold edit beyond what the SOLVER-VISIBLE problem_statement already states publicly. The problem_statement itself: (1) names the patched public repo symbol Query.resolve_lookup_value; (2) describes the exact failure mode ('it passes a iterator to it's constructor', 'NamedTuples don't have the code path for copying an iterator', 'TypeError: __new__() missing 1 required positional argument'); and (3) states the fix verbatim: 'The fix is to * expand the contents of the iterator into the constructor.' The spec view's substance — a plain kind builds from a single iterable, a field-named (namedtuple) kind must have its elements spread one-per-field, and handing a single iterable to a field-named kind fails to construct — is directly derivable from (and explicitly in) that public statement. All spec identifiers (resolve_sequence, resolve_one, build_container, well_formed_container, field_named, spread) are abstract/invented carriers; none echoes a patched repo symbol that is not already public. The spec is framed as desired behaviour, not as an edit. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
