# P2 adversarial audit — sphinx-doc__sphinx-9698

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk6.py`, `atk7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -139,43 +139,29 @@
     result = []  # type: List[int]
     j = 0
     while j < len(methname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(methname))
         Invariant(ToSeq(result) == ToSeq(methname).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(methname) - j,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(methname) - j + 1))
-        # invariants-end
         result.append(methname[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(methname))
-    if is_callable_role(option):
-        result.append(40)
-        result.append(41)
+    # WRONG: emit the empty-call marker for EVERY role, including property.
+    result.append(40)
+    result.append(41)
     result.append(32)
     result.append(40)
-    Assert(ToSeq(result) == index_prefix(ToSeq(methname), option))
     k = 0
     while k < len(clsname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(clsname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(clsname))
         Invariant(ToSeq(result) ==
-                  (index_prefix(ToSeq(methname), option) + ToSeq(clsname).take(k)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(clsname) - k,
-        # discharging MustTerminate(2) from the precondition.
+                  (ToSeq(methname) + call_marker() + group_open() + ToSeq(clsname).take(k)))
         Invariant(MustTerminate(len(clsname) - k + 1))
-        # invariants-end
         result.append(clsname[k])
         k = k + 1
-    Assert(ToSeq(result) ==
-           (index_prefix(ToSeq(methname), option) + ToSeq(clsname)))
     if option == 1:
         result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
     elif option == 2:
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -139,43 +139,27 @@
     result = []  # type: List[int]
     j = 0
     while j < len(methname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(methname))
         Invariant(ToSeq(result) == ToSeq(methname).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(methname) - j,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(methname) - j + 1))
-        # invariants-end
         result.append(methname[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(methname))
-    if is_callable_role(option):
-        result.append(40)
-        result.append(41)
+    # WRONG: never emit the empty-call marker (callable roles drop '()').
     result.append(32)
     result.append(40)
-    Assert(ToSeq(result) == index_prefix(ToSeq(methname), option))
     k = 0
     while k < len(clsname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(clsname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(clsname))
         Invariant(ToSeq(result) ==
-                  (index_prefix(ToSeq(methname), option) + ToSeq(clsname).take(k)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(clsname) - k,
-        # discharging MustTerminate(2) from the precondition.
+                  (ToSeq(methname) + group_open() + ToSeq(clsname).take(k)))
         Invariant(MustTerminate(len(clsname) - k + 1))
-        # invariants-end
         result.append(clsname[k])
         k = k + 1
-    Assert(ToSeq(result) ==
-           (index_prefix(ToSeq(methname), option) + ToSeq(clsname)))
     if option == 1:
         result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
     elif option == 2:
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -139,47 +139,32 @@
     result = []  # type: List[int]
     j = 0
     while j < len(methname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(methname))
         Invariant(ToSeq(result) == ToSeq(methname).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(methname) - j,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(methname) - j + 1))
-        # invariants-end
         result.append(methname[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(methname))
     if is_callable_role(option):
         result.append(40)
         result.append(41)
     result.append(32)
     result.append(40)
-    Assert(ToSeq(result) == index_prefix(ToSeq(methname), option))
     k = 0
     while k < len(clsname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(clsname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(clsname))
         Invariant(ToSeq(result) ==
                   (index_prefix(ToSeq(methname), option) + ToSeq(clsname).take(k)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(clsname) - k,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(clsname) - k + 1))
-        # invariants-end
         result.append(clsname[k])
         k = k + 1
-    Assert(ToSeq(result) ==
-           (index_prefix(ToSeq(methname), option) + ToSeq(clsname)))
+    # WRONG: option 2 uses the plain-method role word instead of ' property)'.
     if option == 1:
         result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
-    elif option == 2:
-        result = result + [32, 112, 114, 111, 112, 101, 114, 116, 121, 41]
     elif option == 3:
         result = result + [32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41]
     else:
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -139,43 +139,30 @@
     result = []  # type: List[int]
     j = 0
     while j < len(methname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(methname))
         Invariant(ToSeq(result) == ToSeq(methname).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(methname) - j,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(methname) - j + 1))
-        # invariants-end
         result.append(methname[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(methname))
     if is_callable_role(option):
         result.append(40)
         result.append(41)
     result.append(32)
     result.append(40)
-    Assert(ToSeq(result) == index_prefix(ToSeq(methname), option))
     k = 0
-    while k < len(clsname):
-        # invariants-start
+    # WRONG: stop one short of len(clsname), dropping the final class code point.
+    while k < len(clsname) - 1:
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(clsname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(clsname))
         Invariant(ToSeq(result) ==
                   (index_prefix(ToSeq(methname), option) + ToSeq(clsname).take(k)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(clsname) - k,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(clsname) - k + 1))
-        # invariants-end
         result.append(clsname[k])
         k = k + 1
-    Assert(ToSeq(result) ==
-           (index_prefix(ToSeq(methname), option) + ToSeq(clsname)))
     if option == 1:
         result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
     elif option == 2:
```

Attack 5 — `atk5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -136,46 +136,34 @@
             (ToSeq(Result()).drop(len(methname)).take(2) == call_marker()))
     # post-conditions-end
     # impl-start
+    # Correct output built by a different control flow: class loop first offset,
+    # then a single combined tail. Semantically identical to the gold label.
     result = []  # type: List[int]
     j = 0
     while j < len(methname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(methname))
         Invariant(ToSeq(result) == ToSeq(methname).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(methname) - j,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(methname) - j + 1))
-        # invariants-end
         result.append(methname[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(methname))
-    if is_callable_role(option):
+    if option != 2:
         result.append(40)
         result.append(41)
     result.append(32)
     result.append(40)
-    Assert(ToSeq(result) == index_prefix(ToSeq(methname), option))
     k = 0
     while k < len(clsname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(clsname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(clsname))
         Invariant(ToSeq(result) ==
                   (index_prefix(ToSeq(methname), option) + ToSeq(clsname).take(k)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(clsname) - k,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(clsname) - k + 1))
-        # invariants-end
         result.append(clsname[k])
         k = k + 1
-    Assert(ToSeq(result) ==
-           (index_prefix(ToSeq(methname), option) + ToSeq(clsname)))
     if option == 1:
         result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
     elif option == 2:
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -139,49 +139,36 @@
     result = []  # type: List[int]
     j = 0
     while j < len(methname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= j and j <= len(methname))
         Invariant(ToSeq(result) == ToSeq(methname).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(methname) - j,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(methname) - j + 1))
-        # invariants-end
         result.append(methname[j])
         j = j + 1
-    Assert(ToSeq(result) == ToSeq(methname))
     if is_callable_role(option):
         result.append(40)
         result.append(41)
     result.append(32)
     result.append(40)
-    Assert(ToSeq(result) == index_prefix(ToSeq(methname), option))
     k = 0
     while k < len(clsname):
-        # invariants-start
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(clsname), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= k and k <= len(clsname))
         Invariant(ToSeq(result) ==
                   (index_prefix(ToSeq(methname), option) + ToSeq(clsname).take(k)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(clsname) - k,
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(clsname) - k + 1))
-        # invariants-end
         result.append(clsname[k])
         k = k + 1
-    Assert(ToSeq(result) ==
-           (index_prefix(ToSeq(methname), option) + ToSeq(clsname)))
+    # WRONG: classmethod (1) and staticmethod (3) role words swapped.
     if option == 1:
-        result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
+        result = result + [32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41]
     elif option == 2:
         result = result + [32, 112, 114, 111, 112, 101, 114, 116, 121, 41]
     elif option == 3:
-        result = result + [32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41]
+        result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
     else:
         result = result + [32, 109, 101, 116, 104, 111, 100, 41]
     return result
```

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

```diff
@@ -136,53 +136,15 @@
             (ToSeq(Result()).drop(len(methname)).take(2) == call_marker()))
     # post-conditions-end
     # impl-start
+    # Divergence probe: an unbounded loop that never returns. Under a
+    # partial-correctness reading this satisfies the value postconditions
+    # vacuously; MustTerminate(2) must reject it.
     result = []  # type: List[int]
-    j = 0
-    while j < len(methname):
-        # invariants-start
-        Invariant(Acc(list_pred(methname), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= j and j <= len(methname))
-        Invariant(ToSeq(result) == ToSeq(methname).take(j))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(methname) - j,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(methname) - j + 1))
-        # invariants-end
-        result.append(methname[j])
-        j = j + 1
-    Assert(ToSeq(result) == ToSeq(methname))
-    if is_callable_role(option):
-        result.append(40)
-        result.append(41)
-    result.append(32)
-    result.append(40)
-    Assert(ToSeq(result) == index_prefix(ToSeq(methname), option))
-    k = 0
-    while k < len(clsname):
-        # invariants-start
+    n = 0
+    while n >= 0:
         Invariant(Acc(list_pred(methname), 1 / 2))
         Invariant(Acc(list_pred(clsname), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= k and k <= len(clsname))
-        Invariant(ToSeq(result) ==
-                  (index_prefix(ToSeq(methname), option) + ToSeq(clsname).take(k)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure len(clsname) - k,
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(clsname) - k + 1))
-        # invariants-end
-        result.append(clsname[k])
-        k = k + 1
-    Assert(ToSeq(result) ==
-           (index_prefix(ToSeq(methname), option) + ToSeq(clsname)))
-    if option == 1:
-        result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
-    elif option == 2:
-        result = result + [32, 112, 114, 111, 112, 101, 114, 116, 121, 41]
-    elif option == 3:
-        result = result + [32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41]
-    else:
-        result = result + [32, 109, 101, 116, 104, 111, 100, 41]
+        n = n + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9698.

Behaviour under specification (stated as desired behaviour, not as an edit):

A class member, identified by its bare member name together with its qualifying
class name, is given a one-line index label. The member is classified by a
single descriptor selecting one of four mutually-exclusive roles. The label is
built by joining, in order:

  (1) the member name;
  (2) an empty-call marker `()` -- present for every role that denotes a
      CALLABLE member, and ABSENT for the one role that denotes a NON-callable
      attribute-like member;
  (3) a constant qualifier group ` (`, the qualifying class name, a single
      space, a role word, and a closing `)`.

The discriminating behaviour: the empty-call marker `()` follows the member name
for every callable role, and is omitted for the single non-callable role (a
value-like member that is read, never invoked). The qualifier group is otherwise
identical in shape across all roles and always names the qualifying class.

Type abstraction (refinement.md / mapping.md): each name is a `List[int]` of
Unicode code points (Nagini bans `str` indexing); the specification is carried
over `PSeq[int]`. The role descriptor is an integer selector. The four role
words and the structural separators are constant code-point sequences.

Label construction is a bounded computation (one step per name code point plus
constant-length literals) and MUST return its label — a total-correctness
obligation, carried as MustTerminate in the precondition. Nagini is a
partial-correctness verifier by default, so without this obligation a
non-terminating implementation (e.g. an endless loop that never returns)
satisfies every value postcondition vacuously yet would hang the index build
(and the F2P test) forever; the real labeller always returns.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. Translation lookup of the label template is the identity
# on the untranslated (reference) template, and the per-placeholder substitution
# of the member/class names is modelled deeply by sequence concatenation. There
# is no opaque callee whose Ensures the proof relies on.
# axioms-end


# pure-start
@Pure
def call_marker() -> PSeq[int]:
    # the empty-call marker '()'
    return PSeq(40, 41)


@Pure
def group_open() -> PSeq[int]:
    # the qualifier-group opening ' ('
    return PSeq(32, 40)


@Pure
def role_suffix(option: int) -> PSeq[int]:
    """The role word, with its leading space and trailing ')', for the role
    selected by `option`: 0 -> ' method)', 1 -> ' class method)',
    2 -> ' property)', 3 -> ' static method)'. The selector 2 is the single
    non-callable role."""
    if option == 1:
        # ' class method)'
        return PSeq(32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41)
    if option == 2:
        # ' property)'
        return PSeq(32, 112, 114, 111, 112, 101, 114, 116, 121, 41)
    if option == 3:
        # ' static method)'
        return PSeq(32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41)
    # ' method)'
    return PSeq(32, 109, 101, 116, 104, 111, 100, 41)


@Pure
def is_callable_role(option: int) -> bool:
    """True for every callable role; false for the single non-callable role
    (selector 2). The empty-call marker is emitted exactly for callable roles."""
    return option != 2


@Pure
def index_prefix(methname: PSeq[int], option: int) -> PSeq[int]:
    """The label prefix up to and including the qualifier-group opening: the
    member name, the empty-call marker iff callable, then ' ('. A proof helper
    for the class-name loop invariant."""
    if is_callable_role(option):
        return methname + call_marker() + group_open()
    return methname + group_open()


@Pure
def index_label(methname: PSeq[int], clsname: PSeq[int], option: int) -> PSeq[int]:
    """The full index label as a code-point sequence: the member name, then the
    empty-call marker iff the role is callable, then the qualifier group naming
    the class and the role word. Modelled deeply -- the label is the in-order
    concatenation of its parts, grounded in the actual name carriers."""
    return index_prefix(methname, option) + clsname + role_suffix(option)
# pure-end


def get_member_index_text(methname: List[int], clsname: List[int], option: int) -> List[int]:
    # pre-conditions-start
    # The member and class names are read-only inputs: fractional permission,
    # required AND ensured. `option` is the role selector (0..3).
    Requires(Acc(list_pred(methname), 1 / 2))
    Requires(Acc(list_pred(clsname), 1 / 2))
    Requires(0 <= option and option <= 3)
    # TERMINATION: the labeller must actually ANSWER — assembling the label is
    # a bounded computation (one step per name code point, plus constant
    # literals). Nagini is a partial-correctness verifier by default, so
    # without this obligation a non-terminating implementation (an endless
    # loop that never reaches its return) satisfies every value postcondition
    # vacuously; the real labeller always returns its label.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(methname), 1 / 2))
    Ensures(Acc(list_pred(clsname), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The label is exactly the in-order assembly of its parts.
    Ensures(ToSeq(Result()) == index_label(ToSeq(methname), ToSeq(clsname), option))
    # Structural discriminator, independent of the assembly helper: the label
    # begins with the member name, and the empty-call marker '()' follows the
    # member name EXACTLY for the callable roles -- i.e. it is present iff the
    # role is callable, and absent for the single non-callable role.
    Ensures(ToSeq(Result()).take(len(methname)) == ToSeq(methname))
    Ensures(is_callable_role(option) ==
            (ToSeq(Result()).drop(len(methname)).take(2) == call_marker()))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    while j < len(methname):
        # invariants-start
        Invariant(Acc(list_pred(methname), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(methname))
        Invariant(ToSeq(result) == ToSeq(methname).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(methname) - j,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(methname) - j + 1))
        # invariants-end
        result.append(methname[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(methname))
    if is_callable_role(option):
        result.append(40)
        result.append(41)
    result.append(32)
    result.append(40)
    Assert(ToSeq(result) == index_prefix(ToSeq(methname), option))
    k = 0
    while k < len(clsname):
        # invariants-start
        Invariant(Acc(list_pred(methname), 1 / 2))
        Invariant(Acc(list_pred(clsname), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(clsname))
        Invariant(ToSeq(result) ==
                  (index_prefix(ToSeq(methname), option) + ToSeq(clsname).take(k)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(clsname) - k,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(clsname) - k + 1))
        # invariants-end
        result.append(clsname[k])
        k = k + 1
    Assert(ToSeq(result) ==
           (index_prefix(ToSeq(methname), option) + ToSeq(clsname)))
    if option == 1:
        result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
    elif option == 2:
        result = result + [32, 112, 114, 111, 112, 101, 114, 116, 121, 41]
    elif option == 3:
        result = result + [32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41]
    else:
        result = result + [32, 109, 101, 116, 104, 111, 100, 41]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Host note: project root (prompt's path absent here). Ran via python with, SBU_BENCHMARK_DIR=.../benchmark-verified.

BASELINES: positive_control (==bundle model.py) same-spec SAME; verify VERIFIED 19.4s. atk_prepatch (==model_prepatch.py, emits () for property role) same-spec SAME; `adversary weakness` => NOT-A-COUNTEREXAMPLE 'does not verify' — spec rejects the prepatch bug (G-DIFF confirmed). prepatch_reproduced=true.

ALL 7 ATTACKS same-spec SAME (`adversary same-spec nagini sphinx-doc__sphinx-9698 <f>` exit 0). weakness command: `adversary weakness nagini sphinx-doc__sphinx-9698 <f>`.
- atk1 partial-domain (always emit () incl. property): weakness exit 2, does not verify -> REJECTED.
- atk2 partial-domain (never emit (), callable roles lose parens): weakness exit 2, does not verify -> REJECTED.
- atk3 boundary (property uses ' method)' role word): weakness exit 2, does not verify -> REJECTED.
- atk4 control-flow-effect (off-by-one: k<len(clsname)-1 drops last class cp): weakness exit 2, does not verify -> REJECTED.
- atk5 ungrounded-oracle echo (correct gold output via inlined option!=2 branch, different control flow): weakness exit 0 CANDIDATE, VERIFIES 17.4s. FAITHFUL REFINED PATCH MATERIALIZED (=gold one-line property template change) and RUN through official harness via harness.run_resolve: RESOLVED=True, COMPLETED=True, note='resolved'; FAIL_TO_PASS tests/test_domain_py.py::test_pymethod_options SUCCESS; 45/45 PASS_TO_PASS SUCCESS; 0 failures. => does NOT break the spec.
- atk6 boundary (classmethod<->staticmethod role words swapped): weakness exit 2, does not verify -> REJECTED.
- atk7 control-flow (while n>=0 non-terminating loop before correct return): weakness exit 2, does not verify -> MustTerminate(2) rejects the diverging impl (A9 closes the vacuous-satisfaction gap).

WHY SOUND: postcondition ToSeq(Result())==index_label(methname,clsname,option) pins the FULL output value for all option in {0..3} and all names; with MustTerminate(2) every verifying impl must terminate and emit exactly the gold label. Hence the only attainable 'verifying wrong impl' is a correct-output echo (atk5), and its faithful patch IS the gold change, which RESOLVES. No verifying impl has a non-resolving faithful patch. verify => correct holds.

A-LEG AUDIT (refinement.md/mapping.md): no consumed axiom (axioms region empty comment; no @ContractOnly). All legs are R / A-reference / I -- NO kind-3. Sole kind-A artefact is the A-reference A8: deep model index_label <-> patched role-branch of PyMethod.get_index_text (_('<template>') % (methname,clsname), _() identity in no-catalogue test env). axiom_check.py (G-AX) run: exit 0, 'index_label deep model == real label on cartesian boundary (20 names^2 x 4 roles) + 20000 fuzz; discriminator sound'. Correspondence holds (real-sphinx cross-check deferred: sphinx not importable on host, expected on pre-patch/no-sphinx host).

VERDICT: SOUND. >=5 distinct wrong-impl attacks run (prepatch + atk1-4,6,7 = 7 rejected across partial-domain/boundary/control-flow-effect/termination classes); the lone verifying candidate (atk5, ungrounded-oracle echo) had its faithful refined patch executed through run_resolve and RESOLVED. No verify-but-wrong impl exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk6.py`, `atk7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9698.

Behaviour under specification (stated as desired behaviour, not as an edit):

A class member, identified by its bare member name together with its qualifying
class name, is given a one-line index label. The member is classified by a
single descriptor selecting one of four mutually-exclusive roles. The label is
built by joining, in order:

  (1) the member name;
  (2) an empty-call marker `()` -- present for every role that denotes a
      CALLABLE member, and ABSENT for the one role that denotes a NON-callable
      attribute-like member;
  (3) a constant qualifier group ` (`, the qualifying class name, a single
      space, a role word, and a closing `)`.

The discriminating behaviour: the empty-call marker `()` follows the member name
for every callable role, and is omitted for the single non-callable role (a
value-like member that is read, never invoked). The qualifier group is otherwise
identical in shape across all roles and always names the qualifying class.

Type abstraction (refinement.md / mapping.md): each name is a `List[int]` of
Unicode code points (Nagini bans `str` indexing); the specification is carried
over `PSeq[int]`. The role descriptor is an integer selector. The four role
words and the structural separators are constant code-point sequences.

Label construction is a bounded computation (one step per name code point plus
constant-length literals) and MUST return its label — a total-correctness
obligation, carried as MustTerminate in the precondition. Nagini is a
partial-correctness verifier by default, so without this obligation a
non-terminating implementation (e.g. an endless loop that never returns)
satisfies every value postcondition vacuously yet would hang the index build
(and the F2P test) forever; the real labeller always returns.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. Translation lookup of the label template is the identity
# on the untranslated (reference) template, and the per-placeholder substitution
# of the member/class names is modelled deeply by sequence concatenation. There
# is no opaque callee whose Ensures the proof relies on.
# axioms-end


# pure-start
@Pure
def call_marker() -> PSeq[int]:
    # the empty-call marker '()'
    return PSeq(40, 41)


@Pure
def group_open() -> PSeq[int]:
    # the qualifier-group opening ' ('
    return PSeq(32, 40)


@Pure
def role_suffix(option: int) -> PSeq[int]:
    """The role word, with its leading space and trailing ')', for the role
    selected by `option`: 0 -> ' method)', 1 -> ' class method)',
    2 -> ' property)', 3 -> ' static method)'. The selector 2 is the single
    non-callable role."""
    if option == 1:
        # ' class method)'
        return PSeq(32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41)
    if option == 2:
        # ' property)'
        return PSeq(32, 112, 114, 111, 112, 101, 114, 116, 121, 41)
    if option == 3:
        # ' static method)'
        return PSeq(32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41)
    # ' method)'
    return PSeq(32, 109, 101, 116, 104, 111, 100, 41)


@Pure
def is_callable_role(option: int) -> bool:
    """True for every callable role; false for the single non-callable role
    (selector 2). The empty-call marker is emitted exactly for callable roles."""
    return option != 2


@Pure
def index_prefix(methname: PSeq[int], option: int) -> PSeq[int]:
    """The label prefix up to and including the qualifier-group opening: the
    member name, the empty-call marker iff callable, then ' ('. A proof helper
    for the class-name loop invariant."""
    if is_callable_role(option):
        return methname + call_marker() + group_open()
    return methname + group_open()


@Pure
def index_label(methname: PSeq[int], clsname: PSeq[int], option: int) -> PSeq[int]:
    """The full index label as a code-point sequence: the member name, then the
    empty-call marker iff the role is callable, then the qualifier group naming
    the class and the role word. Modelled deeply -- the label is the in-order
    concatenation of its parts, grounded in the actual name carriers."""
    return index_prefix(methname, option) + clsname + role_suffix(option)
# pure-end


def get_member_index_text(methname: List[int], clsname: List[int], option: int) -> List[int]:
    # pre-conditions-start
    # The member and class names are read-only inputs: fractional permission,
    # required AND ensured. `option` is the role selector (0..3).
    Requires(Acc(list_pred(methname), 1 / 2))
    Requires(Acc(list_pred(clsname), 1 / 2))
    Requires(0 <= option and option <= 3)
    # TERMINATION: the labeller must actually ANSWER — assembling the label is
    # a bounded computation (one step per name code point, plus constant
    # literals). Nagini is a partial-correctness verifier by default, so
    # without this obligation a non-terminating implementation (an endless
    # loop that never reaches its return) satisfies every value postcondition
    # vacuously; the real labeller always returns its label.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(methname), 1 / 2))
    Ensures(Acc(list_pred(clsname), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The label is exactly the in-order assembly of its parts.
    Ensures(ToSeq(Result()) == index_label(ToSeq(methname), ToSeq(clsname), option))
    # Structural discriminator, independent of the assembly helper: the label
    # begins with the member name, and the empty-call marker '()' follows the
    # member name EXACTLY for the callable roles -- i.e. it is present iff the
    # role is callable, and absent for the single non-callable role.
    Ensures(ToSeq(Result()).take(len(methname)) == ToSeq(methname))
    Ensures(is_callable_role(option) ==
            (ToSeq(Result()).drop(len(methname)).take(2) == call_marker()))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    while j < len(methname):
        # invariants-start
        Invariant(Acc(list_pred(methname), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(methname))
        Invariant(ToSeq(result) == ToSeq(methname).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(methname) - j,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(methname) - j + 1))
        # invariants-end
        result.append(methname[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(methname))
    if is_callable_role(option):
        result.append(40)
        result.append(41)
    result.append(32)
    result.append(40)
    Assert(ToSeq(result) == index_prefix(ToSeq(methname), option))
    k = 0
    while k < len(clsname):
        # invariants-start
        Invariant(Acc(list_pred(methname), 1 / 2))
        Invariant(Acc(list_pred(clsname), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(clsname))
        Invariant(ToSeq(result) ==
                  (index_prefix(ToSeq(methname), option) + ToSeq(clsname).take(k)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(clsname) - k,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(clsname) - k + 1))
        # invariants-end
        result.append(clsname[k])
        k = k + 1
    Assert(ToSeq(result) ==
           (index_prefix(ToSeq(methname), option) + ToSeq(clsname)))
    if option == 1:
        result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
    elif option == 2:
        result = result + [32, 112, 114, 111, 112, 101, 114, 116, 121, 41]
    elif option == 3:
        result = result + [32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41]
    else:
        result = result + [32, 109, 101, 116, 104, 111, 100, 41]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Host note: project root (prompt's path absent here). Ran via python with, SBU_BENCHMARK_DIR=.../benchmark-verified.

BASELINES: positive_control (==bundle model.py) same-spec SAME; verify VERIFIED 19.4s. atk_prepatch (==model_prepatch.py, emits () for property role) same-spec SAME; `adversary weakness` => NOT-A-COUNTEREXAMPLE 'does not verify' — spec rejects the prepatch bug (G-DIFF confirmed). prepatch_reproduced=true.

ALL 7 ATTACKS same-spec SAME (`adversary same-spec nagini sphinx-doc__sphinx-9698 <f>` exit 0). weakness command: `adversary weakness nagini sphinx-doc__sphinx-9698 <f>`.
- atk1 partial-domain (always emit () incl. property): weakness exit 2, does not verify -> REJECTED.
- atk2 partial-domain (never emit (), callable roles lose parens): weakness exit 2, does not verify -> REJECTED.
- atk3 boundary (property uses ' method)' role word): weakness exit 2, does not verify -> REJECTED.
- atk4 control-flow-effect (off-by-one: k<len(clsname)-1 drops last class cp): weakness exit 2, does not verify -> REJECTED.
- atk5 ungrounded-oracle echo (correct gold output via inlined option!=2 branch, different control flow): weakness exit 0 CANDIDATE, VERIFIES 17.4s. FAITHFUL REFINED PATCH MATERIALIZED (=gold one-line property template change) and RUN through official harness via harness.run_resolve: RESOLVED=True, COMPLETED=True, note='resolved'; FAIL_TO_PASS tests/test_domain_py.py::test_pymethod_options SUCCESS; 45/45 PASS_TO_PASS SUCCESS; 0 failures. => does NOT break the spec.
- atk6 boundary (classmethod<->staticmethod role words swapped): weakness exit 2, does not verify -> REJECTED.
- atk7 control-flow (while n>=0 non-terminating loop before correct return): weakness exit 2, does not verify -> MustTerminate(2) rejects the diverging impl (A9 closes the vacuous-satisfaction gap).

WHY SOUND: postcondition ToSeq(Result())==index_label(methname,clsname,option) pins the FULL output value for all option in {0..3} and all names; with MustTerminate(2) every verifying impl must terminate and emit exactly the gold label. Hence the only attainable 'verifying wrong impl' is a correct-output echo (atk5), and its faithful patch IS the gold change, which RESOLVES. No verifying impl has a non-resolving faithful patch. verify => correct holds.

A-LEG AUDIT (refinement.md/mapping.md): no consumed axiom (axioms region empty comment; no @ContractOnly). All legs are R / A-reference / I -- NO kind-3. Sole kind-A artefact is the A-reference A8: deep model index_label <-> patched role-branch of PyMethod.get_index_text (_('<template>') % (methname,clsname), _() identity in no-catalogue test env). axiom_check.py (G-AX) run: exit 0, 'index_label deep model == real label on cartesian boundary (20 names^2 x 4 roles) + 20000 fuzz; discriminator sound'. Correspondence holds (real-sphinx cross-check deferred: sphinx not importable on host, expected on pre-patch/no-sphinx host).

VERDICT: SOUND. >=5 distinct wrong-impl attacks run (prepatch + atk1-4,6,7 = 7 rejected across partial-domain/boundary/control-flow-effect/termination classes); the lone verifying candidate (atk5, ungrounded-oracle echo) had its faithful refined patch executed through run_resolve and RESOLVED. No verify-but-wrong impl exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No divergence found between the modeled function get_member_index_text/index_label and the real patched callee PyMethod.get_index_text (sphinx/domains/python.py:796-803). Evidence: (1) same-spec exit 0, model verifies in Nagini (18.3s); (2) the model's post-patch templates match the gold patch verbatim — property role drops '()' via is_callable_role(2)==False, other three callable roles keep '()'; (3) axiom_check.py validates index_label == real label over 1600 boundary + 20000 fuzz cases (exit 0); (4) independent 200k-case fuzz with '%','s','.','(',')' in names confirms positional '%s' %-substitution never diverges from the model's concatenation (no re-parse of inserted values); (5) MustTerminate(2) is faithful — the real callee is a straight-line splice that always returns, so the totality obligation adds no strength beyond real behavior; (6) the '()' -after-member-name discriminator postcondition matches the real branch dispatch for all four roles. The _() gettext lookup is the identity with no catalogue loaded (test env), matching the model's identity treatment. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py with impl region elided (confirmed via markers.spec_view). refinement.md/mapping.md are auditor-facing justification docs, not solver-visible spec view, so their verbatim gold-hunk quotes are out of scope. Mechanical G-LEAK screen (leakage.screen) PASSES with zero hard failures: no gold-patch line reproduced (template strings 'return _('%s() (%s property)')...' never appear — spec carries PSeq[int] code points, not the literal templates), no diff markers, no patched file path sphinx/domains/python.py, no patched module path, patched symbol 'get_index_text' never echoed in any spec-view identifier or comment, no bug/fix narration. Semantic check: the gold edit removes the '()' from the property role's index label; the PUBLIC problem_statement already states this exact behavior verbatim ('An index entry with parens was registered for py:method with :property: option. It should not have parens' / 'An index entry for the property should not have parens'). The spec's discriminating content — empty-call marker '()' present for callable roles, absent for the single non-callable role (property, selector 2) — coincides with the publicly stated expected behavior and does not disclose the edit beyond problem_statement. The four role words (method/class method/static method/property) are standard py:method domain vocabulary surfaced by the task itself. Behavior is stated as desired behavior, not as an edit (no pre/post framing, no narration). meta records relaxed_leakage=None (not a relaxed bundle). No leakage beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
