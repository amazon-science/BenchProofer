# P2 adversarial audit — pydata__xarray-3677

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 15 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived against the spec this bundle now ships, after a later edit moved the spec view the original audit ran against; same attacks, same derivation, so the evidence behind this verdict is the original battery re-measured rather than a fresh one.

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_4.py`, `atk_5.py`, `atk_9.py`, `atk_15.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,8 +219,6 @@
     # post-conditions-end
     # impl-start
     second = other
-    if is_array_shaped(other):
-        second = as_mapping(other)
     result = [receiver, second]  # type: List[Operand]
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -218,6 +218,8 @@
             and other.name_is_own_label == Old(other.name_is_own_label))
     # post-conditions-end
     # impl-start
+    if receiver is other:
+        raise NormalisationUndefined()
     second = other
     if is_array_shaped(other):
         second = as_mapping(other)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -220,7 +220,9 @@
     # impl-start
     second = other
     if is_array_shaped(other):
-        second = as_mapping(other)
+        if other.name_is_own_label:
+            raise NormalisationUndefined()
+    second = Operand(True, other.name, other.value, False)
     result = [receiver, second]  # type: List[Operand]
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -220,7 +220,9 @@
     # impl-start
     second = other
     if is_array_shaped(other):
-        second = as_mapping(other)
+        if other.name_is_own_label:
+            raise NormalisationUndefined()
+        second = Operand(True, other.name, other.value, False)
     result = [receiver, second]  # type: List[Operand]
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -220,7 +220,10 @@
     # impl-start
     second = other
     if is_array_shaped(other):
-        second = as_mapping(other)
+        if other.name < 0:
+            second = receiver
+        else:
+            second = as_mapping(other)
     result = [receiver, second]  # type: List[Operand]
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -220,7 +220,10 @@
     # impl-start
     second = other
     if is_array_shaped(other):
-        second = as_mapping(other)
+        if other.name_is_own_label:
+            second = Operand(True, other.name, other.value, False)
+        else:
+            second = as_mapping(other)
     result = [receiver, second]  # type: List[Operand]
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -220,7 +220,12 @@
     # impl-start
     second = other
     if is_array_shaped(other):
-        second = as_mapping(other)
+        if other.name_is_own_label:
+            raise NormalisationUndefined()
+        if receiver.name == other.name and receiver.value == other.value:
+            second = receiver
+        else:
+            second = as_mapping(other)
     result = [receiver, second]  # type: List[Operand]
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -147,7 +147,7 @@
             and not o.is_mapping and o.name_is_own_label)
     # post-conditions-end
     # impl-start
-    if o.name_is_own_label:
+    if o.name_is_own_label or o.value == 42:
         raise NormalisationUndefined()
     res = Operand(True, o.name, o.value, False)
     return res
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -147,10 +147,10 @@
             and not o.is_mapping and o.name_is_own_label)
     # post-conditions-end
     # impl-start
-    if o.name_is_own_label:
-        raise NormalisationUndefined()
-    res = Operand(True, o.name, o.value, False)
-    return res
+    if not o.name_is_own_label:
+        res = Operand(True, o.name, o.value, False)
+        return res
+    raise NormalisationUndefined()
     # impl-end
 
 
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,6 +219,8 @@
     # post-conditions-end
     # impl-start
     second = other
+    if other.name_is_own_label:
+        raise NormalisationUndefined()
     if is_array_shaped(other):
         second = as_mapping(other)
     result = [receiver, second]  # type: List[Operand]
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -219,6 +219,8 @@
     # post-conditions-end
     # impl-start
     second = other
+    if receiver.name_is_own_label:
+        raise NormalisationUndefined()
     if is_array_shaped(other):
         second = as_mapping(other)
     result = [receiver, second]  # type: List[Operand]
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -221,6 +221,7 @@
     second = other
     if is_array_shaped(other):
         second = as_mapping(other)
+    receiver.value = receiver.value + 1
     result = [receiver, second]  # type: List[Operand]
     return result
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -149,6 +149,8 @@
     # impl-start
     if o.name_is_own_label:
         raise NormalisationUndefined()
+    while o.value >= 0:
+        Invariant(Acc(o.value, 1 / 8))
     res = Operand(True, o.name, o.value, False)
     return res
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -221,6 +221,6 @@
     second = other
     if is_array_shaped(other):
         second = as_mapping(other)
-    result = [receiver, second]  # type: List[Operand]
+    result = [second, receiver]  # type: List[Operand]
     return result
     # impl-end
```

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -220,7 +220,10 @@
     # impl-start
     second = other
     if is_array_shaped(other):
-        second = as_mapping(other)
+        if other.name_is_own_label:
+            raise NormalisationUndefined()
+        clone = Operand(False, other.name, other.value, False)
+        second = as_mapping(clone)
     result = [receiver, second]  # type: List[Operand]
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-3677.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Combining a collection of two labelled operands into a single sequence of
  operands fit for the core combination routine. The core routine iterates the
  named entries of each operand, so every operand it receives MUST expose the
  named-entry interface (be "mapping-shaped"). The receiving operand already is
  mapping-shaped. The second operand may instead be "array-shaped": a single
  named value with no named-entry interface. The desired behaviour is that the
  produced operand sequence contains exactly the receiver followed by the second
  operand in mapping-shaped form, so that:

    * the sequence has the two operands, in order;
    * the receiver passes through unchanged as the first operand;
    * EVERY operand in the sequence is mapping-shaped (exposes named entries);
    * the second operand still carries the second input's single named value
      (its name and value are preserved), whatever shape that input arrived in;
    * neither operand is altered -- the entry each one carried on the way in is
      the entry it still carries once the sequence has been produced.

An array-shaped operand is normalised into the one-entry mapping-shaped operand
that carries the same name and value; a mapping-shaped operand passes through.
The two operands need not be different objects: the same mapping-shaped operand
may be supplied as both, and the produced sequence then holds it twice.

What the sequence is fit FOR is the core routine's own business: this operation
ends at the sequence, so whether the core can afterwards combine the operands it
receives -- and what it reports when it cannot -- is downstream of the behaviour
specified here and is not constrained by it.

Normalising an array-shaped operand is only DEFINED for some array-shaped
operands, and the sequence can be produced exactly when it is defined. An
array-shaped operand carries, besides its single entry, its own named label
entries -- the labels it holds for its axes; normalisation is undefined when the
entry's own name is also the name of one of those label entries, because the
one-entry mapping-shaped form would then have to hold two different things under
one name. On such an operand the
normalisation signals that it is undefined instead of producing an operand, and
the whole combination signals likewise -- no operand sequence is produced at all.
Neither operand is altered on that outcome either: reporting that no sequence
exists never involves rewriting an operand into the shape that makes such a
report apt.
Normalisation is likewise undefined for an unnamed array-shaped operand; that
case is excluded from this specification's domain by the precondition.

Operands are modelled as a minimal tagged object carrying only the touched
fields: a mapping-shaped flag, the single entry's name, its value, and whether
that name is also the name of one of the operand's own label entries (names and values
abstracted to ints; mapping.md gives the bijection). The normalisation of an
array-shaped operand to a mapping-shaped one is modelled deeply (`as_mapping`)
and validated == the real conversion callee out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NormalisationUndefined(Exception):
    # Signalled when an array-shaped operand has no one-entry mapping-shaped
    # form: its single entry's name is also the name of one of its own label
    # entries.
    pass


class Operand:
    # An operand to the combination routine.
    #   is_mapping        : exposes the named-entry interface the core needs
    #   name              : the single entry's name (-1 == unnamed)
    #   value             : the single entry's value
    #   name_is_own_label : `name` is also the name of one of this operand's own
    #                       label entries, so it has no one-entry mapping-shaped
    #                       form
    def __init__(self, is_mapping: bool, name: int, value: int,
                 name_is_own_label: bool) -> None:
        # level 1: the leaf obligation. `as_mapping` (level 6) and
        # `merge_method` (level 10) both construct Operands, so the
        # constructor's level must sit strictly below theirs, leaving them room
        # to discharge it. Without this, Nagini reports "Obligation leak check
        # failed. Callee __init__ might not take all unsatisfied obligations
        # from the caller." The body is straight-line: it terminates trivially.
        Requires(MustTerminate(1))
        self.is_mapping = is_mapping  # type: bool
        self.name = name              # type: int
        self.value = value            # type: int
        self.name_is_own_label = name_is_own_label  # type: bool
        Ensures(Acc(self.is_mapping) and Acc(self.name) and Acc(self.value)
                and Acc(self.name_is_own_label))
        Ensures(self.is_mapping == is_mapping)
        Ensures(self.name == name and self.value == value)
        Ensures(self.name_is_own_label == name_is_own_label)


# axioms-start
# (no consumed @ContractOnly axiom: the only callee the change introduces is the
#  array->mapping conversion, which is modelled DEEPLY as `as_mapping` below and
#  validated == the real conversion by axiom_check.py / G-AX as an A-reference.)
# axioms-end


# pure-start
@Pure
def is_array_shaped(o: Operand) -> bool:
    # An operand lacks the named-entry interface exactly when it is not
    # mapping-shaped.
    Requires(Acc(o.is_mapping, 1 / 8))
    return not o.is_mapping
# pure-end


def as_mapping(o: Operand) -> Operand:
    """Normalise an array-shaped operand into the one-entry mapping-shaped
    operand carrying the same name and value (deep model of the conversion
    callee; A-reference, G-AX-checked). Signals NormalisationUndefined on an
    array-shaped operand whose entry name is also the name of one of its own
    label entries, for which no such one-entry form exists."""
    # pre-conditions-start
    Requires(Acc(o.is_mapping, 1 / 4) and Acc(o.name, 1 / 4) and Acc(o.value, 1 / 4)
             and Acc(o.name_is_own_label, 1 / 4))
    # the conversion is defined for a named array-shaped operand
    Requires(is_array_shaped(o))
    Requires(o.name >= 0)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(o.is_mapping, 1 / 4) and Acc(o.name, 1 / 4) and Acc(o.value, 1 / 4)
            and Acc(o.name_is_own_label, 1 / 4))
    Ensures(Acc(Result().is_mapping) and Acc(Result().name) and Acc(Result().value)
            and Acc(Result().name_is_own_label))
    # an operand is produced ONLY when the entry name is not also the name of one
    # of the operand's own label entries -- the returning path is exactly that case
    Ensures(not o.is_mapping and o.name >= 0)
    Ensures(not o.name_is_own_label)
    # the produced operand is mapping-shaped and carries the same single entry
    Ensures(Result().is_mapping)
    Ensures(Result().name == o.name and Result().value == o.value)
    # and its own name does not collide with a label entry name of itself
    Ensures(not Result().name_is_own_label)
    # the ONLY other outcome: the collision case signals that no one-entry
    # mapping-shaped form exists, and it is signalled exactly on that case
    Exsures(NormalisationUndefined,
            Acc(o.is_mapping, 1 / 4) and Acc(o.name, 1 / 4) and Acc(o.value, 1 / 4)
            and Acc(o.name_is_own_label, 1 / 4)
            and not o.is_mapping and o.name_is_own_label)
    # post-conditions-end
    # impl-start
    if o.name_is_own_label:
        raise NormalisationUndefined()
    res = Operand(True, o.name, o.value, False)
    return res
    # impl-end


def merge_method(receiver: Operand, other: Operand) -> List[Operand]:
    # pre-conditions-start
    Requires(Acc(receiver.is_mapping, 1 / 2) and Acc(receiver.name, 1 / 2)
             and Acc(receiver.value, 1 / 2) and Acc(receiver.name_is_own_label, 1 / 2))
    Requires(Acc(other.is_mapping, 1 / 2) and Acc(other.name, 1 / 2)
             and Acc(other.value, 1 / 2) and Acc(other.name_is_own_label, 1 / 2))
    # the receiver is already mapping-shaped (it is the dataset the method is on)
    Requires(receiver.is_mapping)
    # (the two operands need NOT be distinct objects: the same mapping-shaped
    #  operand may be supplied as both the receiver and the second operand)
    # a second operand lacking the named-entry interface is a named single value
    Requires(Implies(is_array_shaped(other), other.name >= 0))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(receiver.is_mapping, 1 / 4) and Acc(receiver.name, 1 / 4)
            and Acc(receiver.value, 1 / 4) and Acc(receiver.name_is_own_label, 1 / 4))
    Ensures(Acc(other.is_mapping, 1 / 4) and Acc(other.name, 1 / 4)
            and Acc(other.value, 1 / 4) and Acc(other.name_is_own_label, 1 / 4))
    Ensures(Acc(list_pred(Result())))
    # the produced operand sequence has exactly the two operands, in order
    Ensures(len(Result()) == 2)
    # the receiver passes through unchanged as the first operand
    Ensures(Result()[0] is receiver)
    # EVERY operand reaching the core exposes the named-entry interface
    Ensures(Acc(Result()[0].is_mapping, 1 / 4) and Result()[0].is_mapping)
    Ensures(Acc(Result()[1].is_mapping, 1 / 4) and Result()[1].is_mapping)
    # the second operand still carries the second input's single named value
    Ensures(Acc(Result()[1].name, 1 / 4) and Acc(Result()[1].value, 1 / 4))
    Ensures(Result()[1].name == other.name and Result()[1].value == other.value)
    # NEITHER operand is altered: the second operand still carries, once the
    # sequence has been produced, exactly the entry it arrived with -- so the
    # preservation above cannot be met by rewriting the operand's own entry to
    # match whatever was produced, and (when the same operand was supplied as
    # both) the receiver's entry is equally untouched
    Ensures(other.is_mapping == Old(other.is_mapping))
    Ensures(other.name == Old(other.name) and other.value == Old(other.value))
    Ensures(other.name_is_own_label == Old(other.name_is_own_label))
    # an already-mapping-shaped second operand passes through UNCHANGED (the same
    # object), so no named entry it carries can be silently dropped: the result
    # must be produced from the actual second operand, not rebuilt from a subset
    # of it (see refinement.md B)
    Ensures(Implies(not Old(is_array_shaped(other)), Result()[1] is other))
    # a sequence is produced ONLY when an array-shaped second operand actually
    # has a one-entry mapping-shaped form -- the normalisation is not bypassed,
    # so its undefinedness is not concealed by rebuilding the operand instead
    Ensures(Implies(is_array_shaped(other), not other.name_is_own_label))
    # the ONLY other outcome: an array-shaped second operand whose entry name is
    # also the name of one of its own label entries yields NO operand sequence at
    # all, and that is signalled exactly on that case
    Exsures(NormalisationUndefined,
            Acc(receiver.is_mapping, 1 / 4) and Acc(receiver.name, 1 / 4)
            and Acc(receiver.value, 1 / 4) and Acc(receiver.name_is_own_label, 1 / 4)
            and Acc(other.is_mapping, 1 / 4) and Acc(other.name, 1 / 4)
            and Acc(other.value, 1 / 4) and Acc(other.name_is_own_label, 1 / 4)
            and not other.is_mapping and other.name_is_own_label
            # ... and the operands are as untouched on this outcome as on the other:
            # signalling that no sequence exists is not licence to edit an operand
            # into the shape that makes the signal look justified
            and other.is_mapping == Old(other.is_mapping)
            and other.name == Old(other.name) and other.value == Old(other.value)
            and other.name_is_own_label == Old(other.name_is_own_label))
    # post-conditions-end
    # impl-start
    if not is_array_shaped(other):
        passthrough = [receiver, other]  # type: List[Operand]
        return passthrough
    converted = as_mapping(other)
    result = [receiver, converted]  # type: List[Operand]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) re-audit of a REPAIRED bundle. 15 same-spec attacks encoded (all `adversary same-spec` exit 0; only the two impl regions of model.py ever edited), 4 came back CANDIDATE, and ALL FOUR had their faithful refined patch materialized and RUN through run_resolve. Every one RESOLVED (F2P 1/1, P2P 21/21, attempts=1, no flakiness) => no verify-but-wrong witness. Verdict SOUND.

PRIOR-PASS COUNTEREXAMPLE IS FIXED, AND THE FIX IS SUBSTANTIVE. verdict.md records G-EQ fail on the self-aliasing hole: the old spec carried `Requires(receiver is not other)`, justified in mapping.md as "non-weakening", but the graded P2P test TestMergeMethod::test_merge does `data.merge(data)` (test_merge.py:148,150,152) -- so the excluded class was real and tested. The current model.py has REMOVED that precondition (grep: absent) and replaced it with an explicit comment that the operands need not be distinct. Re-encoded verbatim as atk_2 (`if receiver is other: raise NormalisationUndefined()`): now NOT-A-COUNTEREXAMPLE, verification failed. Crucially I checked the repair is not cosmetic-vacuous (MEMORY: guarded self-calls can go vacuous): ctrl_alias_feasible.py puts `Assert(False)` inside the `receiver is other` branch and Nagini now REJECTS it ("Assert might fail", 19.2s), i.e. the aliasing branch is genuinely reachable and in-domain, where in the broken revision the same probe verified. Two further reachability controls also correctly fail: ctrl_array_feasible (array-shaped branch) and ctrl_ownlabel_feasible (undefinedness class).

**PREPATCH REPRODUCED:** atk_1 = model_prepatch.py's impl (`second = other`, conversion never called) -- same spec, does not verify (the Ensures Result()[1].is_mapping bites). POSITIVE CONTROL: positive_control.py, structurally different (early-return on the mapping-shaped arm, no `second` temp, as_mapping-first on the array arm) -- VERIFIES (18.4s).

PER-ATTACK (cmd: `python -m swebench_unified.adversary weakness nagini pydata__xarray-3677 <path>`; logs at <path minus .py>.weakness.log; resolve logs resolve_atk_N.log):
- atk_1 prepatch bug (no conversion) -> NOT-A-CEX (rejected)
- atk_2 prior CEX, self-aliasing refusal -> NOT-A-CEX (rejected; the repair)
- atk_3 lossy rebuild on BOTH arms -> NOT-A-CEX (rejected by the identity clause, refinement.md §B)
- atk_4 A-reference BYPASS: array arm never calls the deep model, inlines its Ensures instead -> CANDIDATE (21.7s) -> patch_atk_4.diff (`other = xr.Dataset({other.name: other.variable})`, real callee never invoked) -> RESOLVED (F2P 1/1, P2P 21/21)
- atk_5 partial domain: unnamed array-shaped operand (the class `Implies(is_array_shaped(other), other.name >= 0)` excludes) gets the RECEIVER as second operand -> CANDIDATE (21.5s) -> patch_atk_5.diff (`other = self if other.name is None else other.to_dataset()`) -> RESOLVED
- atk_6 outcome substitution: manufacture an operand for the undefinedness class -> NOT-A-CEX (rejected by the Exsures/Ensures pair)
- atk_7 control-flow effect: duplicate the receiver when it happens to carry the same (name,value) -> NOT-A-CEX (rejected)
- atk_8 subvert the DEEP MODEL body: as_mapping also reports undefined for value==42 -> NOT-A-CEX (rejected by as_mapping's Exsures) -- the A leg's own body is guarded even though the spec view elides it
- atk_9 behaviourally-equal reshape of the deep model (ECHO probe) -> CANDIDATE (20.2s) -> refined patch is gold verbatim -> RESOLVED (confirms correct alternatives are not scored as holes)
- atk_10 signal undefined for a MAPPING-shaped operand carrying name_is_own_label -> NOT-A-CEX (rejected)
- atk_11 refuse when the RECEIVER's name collides with its own label -> NOT-A-CEX (rejected)
- atk_12 frame attack: mutate receiver.value (the Ensures pin only `other`'s fields to Old) -> NOT-A-CEX (rejected -- the fractional-permission accounting, directive 5, holds)
- atk_13 total correctness on the A leg: as_mapping diverges on the returning path -> NOT-A-CEX (rejected; MustTerminate(6) binds at the method level, per MEMORY)
- atk_14 list-shape tampering: [second, receiver] -> NOT-A-CEX (rejected by Result()[0] is receiver)
- atk_15 A-leg REBUILD-THEN-CONVERT (distinct from atk_4: the real callee IS invoked, but on a freshly built array-shaped operand) -> CANDIDATE (17.1s) -> patch_atk_15.diff (`xr.DataArray(data=other.data, name=other.name).to_dataset()`) -> RESOLVED

A-LEG AUDIT (the assignment's focus). meta.json declares axioms: [] and one deep_model_reference, as_mapping, kind A-reference; there is no consumed @ContractOnly, so there is no assumption surface to be unsound. The correspondence as_mapping <-> DataArray.to_dataset()/`_to_dataset_whole` (dataarray.py:490,462) checks out against the base-commit source I read: named-array precondition `o.name >= 0` matches the ValueError at 467-471, and `name_is_own_label` matches the second ValueError at 472-476 (`if name in self.coords`). axiom_check.py exercises BOTH outcomes (10 boundary + 2000 fuzz for the returning class, 6 boundary + fuzz for the undefined class) and asserts the product is a Dataset with .items() carrying exactly [(name, value)] -- it validates the two properties the proof actually leans on. refinement.md legs: A1 R, A2 R+I, A3 R+A-reference+I, A4 R+I -- no kind-3, matching §C, and each leg's cited repo line resolved correctly when I read dataset.py:3606 and merge.py:817-819/394.

WHY atk_4/atk_15 RESOLVE DESPITE BYPASSING THE REAL CALLEE (the honest residual, not a hole). `_to_dataset_whole` copies self.`_coords` into `variables` and passes coord_names=set(self.`_coords`); atk_4 and atk_15 both drop those coords. The divergence is invisible to the graded suite only because the F2P input `xr.DataArray(data=1, name="b")` is 0-d with no coords, and no graded test merges a coord-bearing DataArray into a Dataset via the method. So these two patches are behaviourally NON-equal to gold on inputs outside the tested set, yet resolve -- which is the correct G-EQ outcome (the oracle is resolve, not gold-identity), and the A-reference is what carries the untested direction. This is a real limit of the instance's test coverage, not a defect the spec could close: the Operand carrier abstracts to one (name,value) pair by construction (refinement.md §B states this scope limitation explicitly and closes the mapping-shaped side with the unforgeable identity clause).

DOC DEFECT FOUND (advisory, not a G-EQ break; belongs to G-PANEL-2). mapping.md lines 40-43 is STALE: it still documents `receiver is not other` as a precondition of the model and defends it as "a faithful, non-weakening precondition that also keeps the field-permission accounting free of self-aliasing". That precondition no longer exists in model.py -- it was removed to fix precisely the prior G-EQ failure, and the claim it makes is the false claim the prior audit refuted (data.merge(data) is graded). model.py's own docstring and merge_method's comment now say the opposite ("The two operands need not be different objects"). The repair edited the model and left mapping.md's justification behind; it should be deleted or rewritten to record that self-aliasing is IN domain. No machine gate reads that prose, so it will not self-correct.

**SCHEDULE:** attack verifications were run concurrently 3 at a time (each Nagini check spawns a JVM+Z3); the 4 resolve runs were detached background jobs. Pass criteria unchanged -- every attack was fully verified and every candidate's patch was actually executed through run_resolve. No host-saturation timeouts or infra errors occurred (all verify_completed, all resolve completed=True attempts=1).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 15 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived against the spec this bundle now ships, after a later edit moved the spec view the original audit ran against; same attacks, same derivation, so the evidence behind this verdict is the original battery re-measured rather than a fresh one.

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py`, `atk_14.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_4.py`, `atk_5.py`, `atk_9.py`, `atk_15.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-3677.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Combining a collection of two labelled operands into a single sequence of
  operands fit for the core combination routine. The core routine iterates the
  named entries of each operand, so every operand it receives MUST expose the
  named-entry interface (be "mapping-shaped"). The receiving operand already is
  mapping-shaped. The second operand may instead be "array-shaped": a single
  named value with no named-entry interface. The desired behaviour is that the
  produced operand sequence contains exactly the receiver followed by the second
  operand in mapping-shaped form, so that:

    * the sequence has the two operands, in order;
    * the receiver passes through unchanged as the first operand;
    * EVERY operand in the sequence is mapping-shaped (exposes named entries);
    * the second operand still carries the second input's single named value
      (its name and value are preserved), whatever shape that input arrived in;
    * neither operand is altered -- the entry each one carried on the way in is
      the entry it still carries once the sequence has been produced.

An array-shaped operand is normalised into the one-entry mapping-shaped operand
that carries the same name and value; a mapping-shaped operand passes through.
The two operands need not be different objects: the same mapping-shaped operand
may be supplied as both, and the produced sequence then holds it twice.

What the sequence is fit FOR is the core routine's own business: this operation
ends at the sequence, so whether the core can afterwards combine the operands it
receives -- and what it reports when it cannot -- is downstream of the behaviour
specified here and is not constrained by it.

Normalising an array-shaped operand is only DEFINED for some array-shaped
operands, and the sequence can be produced exactly when it is defined. An
array-shaped operand carries, besides its single entry, its own named label
entries -- the labels it holds for its axes; normalisation is undefined when the
entry's own name is also the name of one of those label entries, because the
one-entry mapping-shaped form would then have to hold two different things under
one name. On such an operand the
normalisation signals that it is undefined instead of producing an operand, and
the whole combination signals likewise -- no operand sequence is produced at all.
Neither operand is altered on that outcome either: reporting that no sequence
exists never involves rewriting an operand into the shape that makes such a
report apt.
Normalisation is likewise undefined for an unnamed array-shaped operand; that
case is excluded from this specification's domain by the precondition.

Operands are modelled as a minimal tagged object carrying only the touched
fields: a mapping-shaped flag, the single entry's name, its value, and whether
that name is also the name of one of the operand's own label entries (names and values
abstracted to ints; mapping.md gives the bijection). The normalisation of an
array-shaped operand to a mapping-shaped one is modelled deeply (`as_mapping`)
and validated == the real conversion callee out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NormalisationUndefined(Exception):
    # Signalled when an array-shaped operand has no one-entry mapping-shaped
    # form: its single entry's name is also the name of one of its own label
    # entries.
    pass


class Operand:
    # An operand to the combination routine.
    #   is_mapping        : exposes the named-entry interface the core needs
    #   name              : the single entry's name (-1 == unnamed)
    #   value             : the single entry's value
    #   name_is_own_label : `name` is also the name of one of this operand's own
    #                       label entries, so it has no one-entry mapping-shaped
    #                       form
    def __init__(self, is_mapping: bool, name: int, value: int,
                 name_is_own_label: bool) -> None:
        # level 1: the leaf obligation. `as_mapping` (level 6) and
        # `merge_method` (level 10) both construct Operands, so the
        # constructor's level must sit strictly below theirs, leaving them room
        # to discharge it. Without this, Nagini reports "Obligation leak check
        # failed. Callee __init__ might not take all unsatisfied obligations
        # from the caller." The body is straight-line: it terminates trivially.
        Requires(MustTerminate(1))
        self.is_mapping = is_mapping  # type: bool
        self.name = name              # type: int
        self.value = value            # type: int
        self.name_is_own_label = name_is_own_label  # type: bool
        Ensures(Acc(self.is_mapping) and Acc(self.name) and Acc(self.value)
                and Acc(self.name_is_own_label))
        Ensures(self.is_mapping == is_mapping)
        Ensures(self.name == name and self.value == value)
        Ensures(self.name_is_own_label == name_is_own_label)


# axioms-start
# (no consumed @ContractOnly axiom: the only callee the change introduces is the
#  array->mapping conversion, which is modelled DEEPLY as `as_mapping` below and
#  validated == the real conversion by axiom_check.py / G-AX as an A-reference.)
# axioms-end


# pure-start
@Pure
def is_array_shaped(o: Operand) -> bool:
    # An operand lacks the named-entry interface exactly when it is not
    # mapping-shaped.
    Requires(Acc(o.is_mapping, 1 / 8))
    return not o.is_mapping
# pure-end


def as_mapping(o: Operand) -> Operand:
    """Normalise an array-shaped operand into the one-entry mapping-shaped
    operand carrying the same name and value (deep model of the conversion
    callee; A-reference, G-AX-checked). Signals NormalisationUndefined on an
    array-shaped operand whose entry name is also the name of one of its own
    label entries, for which no such one-entry form exists."""
    # pre-conditions-start
    Requires(Acc(o.is_mapping, 1 / 4) and Acc(o.name, 1 / 4) and Acc(o.value, 1 / 4)
             and Acc(o.name_is_own_label, 1 / 4))
    # the conversion is defined for a named array-shaped operand
    Requires(is_array_shaped(o))
    Requires(o.name >= 0)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(o.is_mapping, 1 / 4) and Acc(o.name, 1 / 4) and Acc(o.value, 1 / 4)
            and Acc(o.name_is_own_label, 1 / 4))
    Ensures(Acc(Result().is_mapping) and Acc(Result().name) and Acc(Result().value)
            and Acc(Result().name_is_own_label))
    # an operand is produced ONLY when the entry name is not also the name of one
    # of the operand's own label entries -- the returning path is exactly that case
    Ensures(not o.is_mapping and o.name >= 0)
    Ensures(not o.name_is_own_label)
    # the produced operand is mapping-shaped and carries the same single entry
    Ensures(Result().is_mapping)
    Ensures(Result().name == o.name and Result().value == o.value)
    # and its own name does not collide with a label entry name of itself
    Ensures(not Result().name_is_own_label)
    # the ONLY other outcome: the collision case signals that no one-entry
    # mapping-shaped form exists, and it is signalled exactly on that case
    Exsures(NormalisationUndefined,
            Acc(o.is_mapping, 1 / 4) and Acc(o.name, 1 / 4) and Acc(o.value, 1 / 4)
            and Acc(o.name_is_own_label, 1 / 4)
            and not o.is_mapping and o.name_is_own_label)
    # post-conditions-end
    # impl-start
    if o.name_is_own_label:
        raise NormalisationUndefined()
    res = Operand(True, o.name, o.value, False)
    return res
    # impl-end


def merge_method(receiver: Operand, other: Operand) -> List[Operand]:
    # pre-conditions-start
    Requires(Acc(receiver.is_mapping, 1 / 2) and Acc(receiver.name, 1 / 2)
             and Acc(receiver.value, 1 / 2) and Acc(receiver.name_is_own_label, 1 / 2))
    Requires(Acc(other.is_mapping, 1 / 2) and Acc(other.name, 1 / 2)
             and Acc(other.value, 1 / 2) and Acc(other.name_is_own_label, 1 / 2))
    # the receiver is already mapping-shaped (it is the dataset the method is on)
    Requires(receiver.is_mapping)
    # (the two operands need NOT be distinct objects: the same mapping-shaped
    #  operand may be supplied as both the receiver and the second operand)
    # a second operand lacking the named-entry interface is a named single value
    Requires(Implies(is_array_shaped(other), other.name >= 0))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(receiver.is_mapping, 1 / 4) and Acc(receiver.name, 1 / 4)
            and Acc(receiver.value, 1 / 4) and Acc(receiver.name_is_own_label, 1 / 4))
    Ensures(Acc(other.is_mapping, 1 / 4) and Acc(other.name, 1 / 4)
            and Acc(other.value, 1 / 4) and Acc(other.name_is_own_label, 1 / 4))
    Ensures(Acc(list_pred(Result())))
    # the produced operand sequence has exactly the two operands, in order
    Ensures(len(Result()) == 2)
    # the receiver passes through unchanged as the first operand
    Ensures(Result()[0] is receiver)
    # EVERY operand reaching the core exposes the named-entry interface
    Ensures(Acc(Result()[0].is_mapping, 1 / 4) and Result()[0].is_mapping)
    Ensures(Acc(Result()[1].is_mapping, 1 / 4) and Result()[1].is_mapping)
    # the second operand still carries the second input's single named value
    Ensures(Acc(Result()[1].name, 1 / 4) and Acc(Result()[1].value, 1 / 4))
    Ensures(Result()[1].name == other.name and Result()[1].value == other.value)
    # NEITHER operand is altered: the second operand still carries, once the
    # sequence has been produced, exactly the entry it arrived with -- so the
    # preservation above cannot be met by rewriting the operand's own entry to
    # match whatever was produced, and (when the same operand was supplied as
    # both) the receiver's entry is equally untouched
    Ensures(other.is_mapping == Old(other.is_mapping))
    Ensures(other.name == Old(other.name) and other.value == Old(other.value))
    Ensures(other.name_is_own_label == Old(other.name_is_own_label))
    # an already-mapping-shaped second operand passes through UNCHANGED (the same
    # object), so no named entry it carries can be silently dropped: the result
    # must be produced from the actual second operand, not rebuilt from a subset
    # of it (see refinement.md B)
    Ensures(Implies(not Old(is_array_shaped(other)), Result()[1] is other))
    # a sequence is produced ONLY when an array-shaped second operand actually
    # has a one-entry mapping-shaped form -- the normalisation is not bypassed,
    # so its undefinedness is not concealed by rebuilding the operand instead
    Ensures(Implies(is_array_shaped(other), not other.name_is_own_label))
    # the ONLY other outcome: an array-shaped second operand whose entry name is
    # also the name of one of its own label entries yields NO operand sequence at
    # all, and that is signalled exactly on that case
    Exsures(NormalisationUndefined,
            Acc(receiver.is_mapping, 1 / 4) and Acc(receiver.name, 1 / 4)
            and Acc(receiver.value, 1 / 4) and Acc(receiver.name_is_own_label, 1 / 4)
            and Acc(other.is_mapping, 1 / 4) and Acc(other.name, 1 / 4)
            and Acc(other.value, 1 / 4) and Acc(other.name_is_own_label, 1 / 4)
            and not other.is_mapping and other.name_is_own_label
            # ... and the operands are as untouched on this outcome as on the other:
            # signalling that no sequence exists is not licence to edit an operand
            # into the shape that makes the signal look justified
            and other.is_mapping == Old(other.is_mapping)
            and other.name == Old(other.name) and other.value == Old(other.value)
            and other.name_is_own_label == Old(other.name_is_own_label))
    # post-conditions-end
    # impl-start
    if not is_array_shaped(other):
        passthrough = [receiver, other]  # type: List[Operand]
        return passthrough
    converted = as_mapping(other)
    result = [receiver, converted]  # type: List[Operand]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) re-audit of a REPAIRED bundle. 15 same-spec attacks encoded (all `adversary same-spec` exit 0; only the two impl regions of model.py ever edited), 4 came back CANDIDATE, and ALL FOUR had their faithful refined patch materialized and RUN through run_resolve. Every one RESOLVED (F2P 1/1, P2P 21/21, attempts=1, no flakiness) => no verify-but-wrong witness. Verdict SOUND.

PRIOR-PASS COUNTEREXAMPLE IS FIXED, AND THE FIX IS SUBSTANTIVE. verdict.md records G-EQ fail on the self-aliasing hole: the old spec carried `Requires(receiver is not other)`, justified in mapping.md as "non-weakening", but the graded P2P test TestMergeMethod::test_merge does `data.merge(data)` (test_merge.py:148,150,152) -- so the excluded class was real and tested. The current model.py has REMOVED that precondition (grep: absent) and replaced it with an explicit comment that the operands need not be distinct. Re-encoded verbatim as atk_2 (`if receiver is other: raise NormalisationUndefined()`): now NOT-A-COUNTEREXAMPLE, verification failed. Crucially I checked the repair is not cosmetic-vacuous (MEMORY: guarded self-calls can go vacuous): ctrl_alias_feasible.py puts `Assert(False)` inside the `receiver is other` branch and Nagini now REJECTS it ("Assert might fail", 19.2s), i.e. the aliasing branch is genuinely reachable and in-domain, where in the broken revision the same probe verified. Two further reachability controls also correctly fail: ctrl_array_feasible (array-shaped branch) and ctrl_ownlabel_feasible (undefinedness class).

**PREPATCH REPRODUCED:** atk_1 = model_prepatch.py's impl (`second = other`, conversion never called) -- same spec, does not verify (the Ensures Result()[1].is_mapping bites). POSITIVE CONTROL: positive_control.py, structurally different (early-return on the mapping-shaped arm, no `second` temp, as_mapping-first on the array arm) -- VERIFIES (18.4s).

PER-ATTACK (cmd: `python -m swebench_unified.adversary weakness nagini pydata__xarray-3677 <path>`; logs at <path minus .py>.weakness.log; resolve logs resolve_atk_N.log):
- atk_1 prepatch bug (no conversion) -> NOT-A-CEX (rejected)
- atk_2 prior CEX, self-aliasing refusal -> NOT-A-CEX (rejected; the repair)
- atk_3 lossy rebuild on BOTH arms -> NOT-A-CEX (rejected by the identity clause, refinement.md §B)
- atk_4 A-reference BYPASS: array arm never calls the deep model, inlines its Ensures instead -> CANDIDATE (21.7s) -> patch_atk_4.diff (`other = xr.Dataset({other.name: other.variable})`, real callee never invoked) -> RESOLVED (F2P 1/1, P2P 21/21)
- atk_5 partial domain: unnamed array-shaped operand (the class `Implies(is_array_shaped(other), other.name >= 0)` excludes) gets the RECEIVER as second operand -> CANDIDATE (21.5s) -> patch_atk_5.diff (`other = self if other.name is None else other.to_dataset()`) -> RESOLVED
- atk_6 outcome substitution: manufacture an operand for the undefinedness class -> NOT-A-CEX (rejected by the Exsures/Ensures pair)
- atk_7 control-flow effect: duplicate the receiver when it happens to carry the same (name,value) -> NOT-A-CEX (rejected)
- atk_8 subvert the DEEP MODEL body: as_mapping also reports undefined for value==42 -> NOT-A-CEX (rejected by as_mapping's Exsures) -- the A leg's own body is guarded even though the spec view elides it
- atk_9 behaviourally-equal reshape of the deep model (ECHO probe) -> CANDIDATE (20.2s) -> refined patch is gold verbatim -> RESOLVED (confirms correct alternatives are not scored as holes)
- atk_10 signal undefined for a MAPPING-shaped operand carrying name_is_own_label -> NOT-A-CEX (rejected)
- atk_11 refuse when the RECEIVER's name collides with its own label -> NOT-A-CEX (rejected)
- atk_12 frame attack: mutate receiver.value (the Ensures pin only `other`'s fields to Old) -> NOT-A-CEX (rejected -- the fractional-permission accounting, directive 5, holds)
- atk_13 total correctness on the A leg: as_mapping diverges on the returning path -> NOT-A-CEX (rejected; MustTerminate(6) binds at the method level, per MEMORY)
- atk_14 list-shape tampering: [second, receiver] -> NOT-A-CEX (rejected by Result()[0] is receiver)
- atk_15 A-leg REBUILD-THEN-CONVERT (distinct from atk_4: the real callee IS invoked, but on a freshly built array-shaped operand) -> CANDIDATE (17.1s) -> patch_atk_15.diff (`xr.DataArray(data=other.data, name=other.name).to_dataset()`) -> RESOLVED

A-LEG AUDIT (the assignment's focus). meta.json declares axioms: [] and one deep_model_reference, as_mapping, kind A-reference; there is no consumed @ContractOnly, so there is no assumption surface to be unsound. The correspondence as_mapping <-> DataArray.to_dataset()/`_to_dataset_whole` (dataarray.py:490,462) checks out against the base-commit source I read: named-array precondition `o.name >= 0` matches the ValueError at 467-471, and `name_is_own_label` matches the second ValueError at 472-476 (`if name in self.coords`). axiom_check.py exercises BOTH outcomes (10 boundary + 2000 fuzz for the returning class, 6 boundary + fuzz for the undefined class) and asserts the product is a Dataset with .items() carrying exactly [(name, value)] -- it validates the two properties the proof actually leans on. refinement.md legs: A1 R, A2 R+I, A3 R+A-reference+I, A4 R+I -- no kind-3, matching §C, and each leg's cited repo line resolved correctly when I read dataset.py:3606 and merge.py:817-819/394.

WHY atk_4/atk_15 RESOLVE DESPITE BYPASSING THE REAL CALLEE (the honest residual, not a hole). `_to_dataset_whole` copies self.`_coords` into `variables` and passes coord_names=set(self.`_coords`); atk_4 and atk_15 both drop those coords. The divergence is invisible to the graded suite only because the F2P input `xr.DataArray(data=1, name="b")` is 0-d with no coords, and no graded test merges a coord-bearing DataArray into a Dataset via the method. So these two patches are behaviourally NON-equal to gold on inputs outside the tested set, yet resolve -- which is the correct G-EQ outcome (the oracle is resolve, not gold-identity), and the A-reference is what carries the untested direction. This is a real limit of the instance's test coverage, not a defect the spec could close: the Operand carrier abstracts to one (name,value) pair by construction (refinement.md §B states this scope limitation explicitly and closes the mapping-shaped side with the unforgeable identity clause).

DOC DEFECT FOUND (advisory, not a G-EQ break; belongs to G-PANEL-2). mapping.md lines 40-43 is STALE: it still documents `receiver is not other` as a precondition of the model and defends it as "a faithful, non-weakening precondition that also keeps the field-permission accounting free of self-aliasing". That precondition no longer exists in model.py -- it was removed to fix precisely the prior G-EQ failure, and the claim it makes is the false claim the prior audit refuted (data.merge(data) is graded). model.py's own docstring and merge_method's comment now say the opposite ("The two operands need not be different objects"). The repair edited the model and left mapping.md's justification behind; it should be deleted or rewritten to record that self-aliasing is IN domain. No machine gate reads that prose, so it will not self-correct.

**SCHEDULE:** attack verifications were run concurrently 3 at a time (each Nagini check spawns a JVM+Z3); the 4 resolve runs were detached background jobs. Pass criteria unchanged -- every attack was fully verified and every candidate's patch was actually executed through run_resolve. No host-saturation timeouts or infra errors occurred (all verify_completed, all resolve completed=True attempts=1).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** REFERENCE DISCIPLINE: modelled function (merge_method) compared against the worktree WITH patch.diff APPLIED (patch applied in the pinned container swebench/sweb.eval.x86_64.pydata_1776_xarray-3677, confirmed line `other = other.to_dataset() if isinstance(other, xr.DataArray) else other` present at dataset.py:3607). Base commit ef6e6a7b used as reference only for the untouched callee DataArray.to_dataset()/`_to_dataset_whole`, which is what as_mapping models. No divergence found; I could not construct a diverging input.

**SPEC REGION INTEGRITY:** `adversary same-spec nagini pydata__xarray-3677 pre3677.py` -> exit 0, "SAME — attack shares the bundle's exact specification", so the spec region is byte-identical and the delimiters parse.

WHAT VERIFIES / WHAT FAILS (spec senses the delta, not vacuous):
- `bash scripts/nagini_verify.sh model.py` -> exit 0 (verifies).
- The same spec against model_prepatch.py (`second = other`, no as_mapping) -> "Verification failed ... Postcondition of merge_method might not hold. Assertion Result()[1].is_mapping might not hold." So the spec is strong enough to reject the pre-patch behaviour and is not trivially satisfiable.

### BUNDLE CHECKS RE-RUN INDEPENDENTLY IN-CONTAINER (patch applied):
- axiom_check.py -> exit 0 (as_mapping == real to_dataset() on 10 boundary + 2000 fuzz, both outcomes).
- conformance_check.py -> exit 0 (100050 inputs, real patched Dataset.merge called via a spy over dataset_merge_method, not transliterated; `_assert_oracle_is_patched` guard active).

MY OWN ADVERSARIAL PROBES (independent bridge, not the bundle's script; I deliberately used mapping.md's PRIMARY binding `isinstance(obj, xr.DataArray)` -> array-shaped rather than the conformance script's `hasattr(obj,'items')` proxy, so a divergence between the two readings would surface):
1. name_is_own_label predicate faithfulness — 90 structured named-DataArray probes (scalar; self-coord; 1-D with name as dim+coord; name as dim without coord; other index coord; non-index coord; scalar coord sharing the name; 2-D; pandas MultiIndex coord) asserting `name in da.coords` holds EXACTLY iff the real `to_dataset()` raises ValueError, and that on the returning path the product is a Dataset with exactly one data_var keyed by the name and holding the value. 0 errors. This is the clause most at risk of being too strong (the model's Exsures claims the collision case is the ONLY undefined case inside the domain) and it held on every probe.
2. Full-postcondition differential — 485 systematic (5 receivers x 97 arguments) + 4000 seeded-fuzz inputs diffing len==2, Result()[0] is receiver, is_mapping of BOTH operands, real `.items()` presence on both, name/value preservation of the second operand, and the identity clause `Implies(not Old(is_array_shaped(other)), Result()[1] is other)`. 0 disagreements. Both outcomes diffed in both directions (model-returns/real-raises AND model-raises/real-returns).
3. Targeted edge classes the bundle's script does NOT generate, all agreeing with the model: DataArray carrying a coord literally named `items` (real repo: hasattr(da,'items') is True by attribute fall-through yet `da.items()` raises TypeError 'DataArray' object is not callable and coerce_pandas_values still fails — so the conformance script's hasattr proxy is arguably looser than the semantics, but the MODEL under mapping.md's isinstance binding classifies it correctly as array-shaped and the real patched merge converts it, giving vars ['a','b'] + coord 'items'; no divergence); name-collides-with-receiver at equal and differing values (MergeError regime, inside the model's Requires and correctly left unconstrained since the spec ends at the operand sequence); empty receiver; empty/coords-only/multi-var Dataset argument; plain dict argument; self-merge (ds.merge(ds), the aliased-operand case the spec explicitly permits); MultiIndex level-name collision (to_dataset succeeds, merge later raises ValueError downstream of the modelled boundary — correctly outside the spec's scope per the model's explicit 'what the sequence is fit FOR is the core routine's business' disclaimer).
4. Framing / non-mutation — verified on the real patched code that the DataArray argument, the Dataset argument, and the receiver are all unmutated on the returning path AND on the ValueError (undefined-normalisation) path, matching the model's Ensures/Exsures Old(...) preservation clauses and the fractional-permission Acc requirements.
5. overwrite_vars — the spec models only the default frozenset() arm. I probed frozenset(), set(), 'a', 'b', ['a','b'] with both Dataset and DataArray arguments; the patch's normalisation runs before dataset_merge_method in every case, so the modelled (receiver, normalised-other) pair the spy records is unchanged. The 3-operand `objs` split on the non-default arm is downstream of the modelled boundary (the model ends at the pair handed to dataset_merge_method, per mapping.md §1), so restricting to the default arm is a scope choice that does not overclaim.

DOMAIN-EXCLUSION AUDIT (is the precondition hiding a divergence?): `Requires(Implies(is_array_shaped(other), other.name >= 0))` excludes the UNNAMED DataArray, where `_to_dataset_whole` raises ValueError (dataarray.py:467-471). This exclusion is legitimate rather than a faithfulness dodge: it is a genuinely different real outcome that the gold patch does not fix either (test_merge_dataarray_unnamed is a PASS_TO_PASS on the top-level merge path, untouched here), and critically the model does NOT exclude the sibling collision case — it predicts it via Exsures, which is the harder and correct choice. Excluding both would have been the weak-spec move.

**CONCLUSION:** no input found on which the modelled function disagrees with the real patched callee. The spec is strong (rejects the pre-patch model on exactly the discriminating clause), its partiality matches the real callee's two ValueError paths rather than papering over them, and the identity clause closes the lossy-rebuild hole documented in refinement.md B. FAITHFUL.

**REFERENCE DISCIPLINE:** modelled function (merge_method) compared against the worktree WITH patch.diff APPLIED (patch applied in the pinned container swebench/sweb.eval.x86_64.pydata_1776_xarray-3677, confirmed line `other = other.to_dataset() if isinstance(other, xr.DataArray) else other` present at dataset.py:3607). Base commit ef6e6a7b used as reference only for the untouched callee DataArray.to_dataset()/`_to_dataset_whole`, which is what as_mapping models. No divergence found; I could not construct a diverging input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: judged the machine-generated consumer spec view (markers.spec_view of model.py, nagini python flavor: both impl regions collapsed to '... # implementation elided'), against the SOLVER-VISIBLE problem_statement only. hints_text for this instance is EMPTY, so it could not have been used as an excuse; every acquittal below rests on the public PS. refinement.md / mapping.md / meta.json / conformance_check.py are private bundle artifacts and were NOT treated as consumer-visible (confirmed in eval/dataset.py: mode 1/2 pass only spec_view + meta.modeled_functions; audit.py flags bundle reads).

1. **MECHANICAL SCREEN PASSES.** swebench_unified.leakage.screen(model.py, nagini, gold_patch, problem_statement, test_patch) => passed=True, zero hard failures, zero warnings. Covers L1 (no gold-diff line reproduced, no diff markers), L2 (no patched file/module path), L2/L5 (no spec-view identifier embedding a patched repo symbol), L2/L3 (no patched symbol named in comment/docstring), L3 (no bug/fix narration vocabulary). Note the screen is only the mechanical half; the judgment half follows.

2. GOLD-RECONSTRUCTION TEST (the real question). The gold edit is one line in xarray/core/dataset.py: `other = other.to_dataset() if isinstance(other, xr.DataArray) else other`. Its four reconstructable components are (a) the file/function to edit, (b) the isinstance discriminator, (c) the to_dataset() callee, (d) the placement before dataset_merge_method. I grepped the spec view for every repo-side localizer with word-boundary regexes: dataset.py, dataarray.py, merge.py, Dataset, DataArray, to_dataset, `_to_dataset_whole`, dataset_merge_method, merge_core, coerce_pandas_values, items, isinstance, xr, xarray, coords, coordinate, `_check_inplace`, `_construct_direct`, variable, and the line numbers 3604/3605 — ALL CLEAN, zero hits. The spec view is written entirely in de-refined vocabulary (Operand / is_mapping / 'mapping-shaped' / 'array-shaped' / as_mapping / 'named-entry interface' / 'label entries'), none of which is a repo symbol. A consumer reading it learns the abstract obligation 'normalise the second operand so every operand exposes named entries' — which is exactly what the PS's own traceback already states — but not which of the four candidate coercion routes to call nor where. Confirmed empirically that the route is genuinely underdetermined by the spec: `xr.Dataset({da.name: da})` also produces a mapping-shaped operand and does NOT share to_dataset()'s partiality (it succeeded on the collision input where to_dataset raised), so the spec view does not fingerprint the gold callee.

3. THE ONE SUBSTANTIVE CANDIDATE — the name_is_own_label / NormalisationUndefined partiality — INVESTIGATED AND ACQUITTED. This is the only content in the spec view that is not verbatim in the PS: the clause that normalisation is undefined when the single entry's name is also the name of one of the operand's own label entries (refined: DataArray.name in DataArray.coords -> `_to_dataset_whole` ValueError, dataarray.py:467-476). Concern: an unsolicited partiality can act as an edit fingerprint, pointing at the specific callee whose precondition it is. I tested this against the real repo in a worktree at base_commit ef6e6a7b and it does NOT leak, for two independent reasons:
  (a) PUBLICLY DERIVABLE. The PS asserts `ds.merge(da)` must behave like `xr.merge([ds, da])` ('works fine'), and prints the expected output of that call. I ran the PS's own public route on a name==own-coord array: `xr.merge([ds, da])` raises the IDENTICAL ValueError('cannot create a Dataset from a DataArray with the same name as one of its coordinates'). So a solver with only the PS can observe this partiality by running the very call the PS holds up as the target. Encoding it is faithfulness to a publicly-observable behaviour, not disclosure of a private one.
  (b) IT IS THE PARTIALITY OF AN UNCHANGED CALLEE, NOT OF THE EDIT. to_dataset/`_to_dataset_whole` are untouched by the gold patch (patch is a single added line in dataset.py). A domain restriction on a pre-existing callee tells the solver the operation is partial; it does not tell them which callee, since the spec view never names to_dataset and, per (2), an alternative coercion without that partiality also satisfies the contract. The parallel unnamed-array restriction (`Requires(o.name >= 0)`) is likewise a real pre-existing ValueError path.

4. NARRATION / DIAGNOSIS CHECK. The docstring reads as a forward behavioural contract ('The desired behaviour is that the produced operand sequence contains...'), never as bug->fix narration. It explicitly disclaims the edit framing on line 3 ('stated as desired behaviour, not as an edit'). No 'the pre-existing code failed to...' construction, no diagnosis of mechanism, no `_NARRATION` vocabulary (bug/fix/patch/previously/incorrectly/broken/regression). Lines 27-30 push the downstream MergeError explicitly OUT of scope rather than hinting at it. Comments justifying the postconditions ('closing the lossy-rebuild hole', 'see refinement.md B') reference a private doc by NAME only and disclose no repo-side content; per audit.py the mere string 'refinement.md' is not a bundle read. Line 1 carries the instance id 'pydata__xarray-3677' — this is the corpus-wide convention (verified YES on 40/40 sampled bundles) and the id is already agent-visible via the harness ({repo} in eval_common_rules.md plus the /testbed checkout), so it discloses nothing beyond the PS.

5. ADVERSARIAL RESIDUAL (recorded, not a finding). The strongest remaining argument for LEAKAGE is that the partiality in (3) is a signal the PS does not volunteer in prose — a solver must run code to see it. I judged this insufficient: G-LEAK's standard is the solver-VISIBLE problem statement, and a behaviour reachable by executing the PS's own reproducer against the checkout the solver is given is visible in that sense. It also fails the operative test: it does not narrow the gold edit, because the collision partiality does not distinguish to_dataset() from the Dataset({name: da}) alternative in the direction a solver would need.

OUT-OF-SCOPE OBSERVATION FOR G-INTEGRITY (not a leakage finding, flagging for the panel): meta.json region_hashes are STALE against the current model.py — computed impl/pre-conditions/post-conditions/spec_view hashes all MISMATCH the recorded ones (axioms and pure match). model.py mtime Aug 14 17:44 vs meta.json Aug 14 18:42, so the spec was edited without re-stamping, or meta was written from a different revision. This does not affect my verdict (I screened the ACTUAL current spec view, which is what a consumer would be served), but the recorded spec_view hash cf61da7c... no longer certifies the shipped artifact ffd616fb..., which weakens the freeze guarantee other gates rely on.

**SCOPE:** judged the machine-generated consumer spec view (markers.spec_view of model.py, nagini python flavor: both impl regions collapsed to '... # implementation elided'), against the SOLVER-VISIBLE problem_statement only. hints_text for this instance is EMPTY, so it could not have been used as an excuse; every acquittal below rests on the public PS. refinement.md / mapping.md / meta.json / conformance_check.py are private bundle artifacts and were NOT treated as consumer-visible (confirmed in eval/dataset.py: mode 1/2 pass only spec_view + meta.modeled_functions; audit.py flags bundle reads).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
