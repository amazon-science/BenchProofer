# P2 adversarial audit — sphinx-doc__sphinx-9602

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,25 +138,18 @@
     Ensures(Implies(not is_str, ToSeq(Result()) == ToSeq(value)))
     # post-conditions-end
     # impl-start
-    if is_str:
-        result = [39] + value + [39]  # type: List[int]
-        return result
-    else:
-        out = []  # type: List[int]
-        i = len(value)
-        while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(value), 1 / 2))
-            Invariant(Acc(list_pred(out)))
-            Invariant(0 <= i and i <= len(value))
-            Invariant(ToSeq(out) == ToSeq(value).drop(i))
-            # the loop consumes the caller's termination obligation with the
-            # strictly decreasing, bounded-below measure i.
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            out = [value[i - 1]] + out
-            i = i - 1
-        return out
+    # PREPATCH: emit the value verbatim, no surrounding quotes for a string.
+    out = []  # type: List[int]
+    i = len(value)
+    while i > 0:
+        Invariant(Acc(list_pred(value), 1 / 2))
+        Invariant(Acc(list_pred(out)))
+        Invariant(0 <= i and i <= len(value))
+        Invariant(ToSeq(out) == ToSeq(value).drop(i))
+        Invariant(MustTerminate(i + 1))
+        out = [value[i - 1]] + out
+        i = i - 1
+    return out
     # impl-end
 
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -180,48 +180,33 @@
     Ensures(ToSeq(Result()) == resolve_seq(wrap_seq(ToSeq(kinds), is_literal)))
     # post-conditions-end
     # impl-start
-    # Wrap each text node iff this is an enumerated (Literal) subscript.
+    # PREPATCH: no enumeration-wrap; every non-blank text resolves to a xref.
     wrapped = []  # type: List[int]
     i = len(kinds)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(wrapped)))
         Invariant(0 <= i and i <= len(kinds))
         Invariant(len(wrapped) == len(kinds) - i)
-        # strictly decreasing, bounded-below measure i consumes the caller's
-        # termination obligation.
         Invariant(MustTerminate(i + 1))
-        Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds).drop(i), is_literal))
-        # invariants-end
+        Invariant(ToSeq(wrapped) == ToSeq(kinds).drop(i))
         k = kinds[i - 1]
         Assert(ToSeq(kinds).drop(i - 1)[0] == k)
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
-        if is_literal and k == 1:
-            wrapped = [4] + wrapped
-        else:
-            wrapped = [k] + wrapped
+        wrapped = [k] + wrapped
         i = i - 1
     Assert(ToSeq(kinds).drop(0) == ToSeq(kinds))
-    Assert(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
-    # Resolve: wrapped -> plain text; non-blank text -> cross-reference; else
-    # pass through.
     out = []  # type: List[int]
     j = len(wrapped)
     while j > 0:
-        # invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(wrapped)))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= j and j <= len(wrapped))
         Invariant(len(wrapped) == len(kinds))
-        # strictly decreasing, bounded-below measure j consumes the caller's
-        # termination obligation.
         Invariant(MustTerminate(j + 1))
         Invariant(len(out) == len(wrapped) - j)
-        Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
         Invariant(ToSeq(out) == resolve_seq(ToSeq(wrapped).drop(j)))
-        # invariants-end
         w = wrapped[j - 1]
         Assert(ToSeq(wrapped).drop(j - 1)[0] == w)
         Assert(ToSeq(wrapped).drop(j - 1).drop(1) == ToSeq(wrapped).drop(j))
@@ -232,7 +217,5 @@
         else:
             out = [w] + out
         j = j - 1
-    Assert(ToSeq(wrapped).drop(0) == ToSeq(wrapped))
-    Assert(ToSeq(out) == resolve_seq(ToSeq(wrapped)))
     return out
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -139,21 +139,20 @@
     # post-conditions-end
     # impl-start
     if is_str:
+        if len(value) == 0:
+            empty = []  # type: List[int]
+            return empty
         result = [39] + value + [39]  # type: List[int]
         return result
     else:
         out = []  # type: List[int]
         i = len(value)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(value), 1 / 2))
             Invariant(Acc(list_pred(out)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(out) == ToSeq(value).drop(i))
-            # the loop consumes the caller's termination obligation with the
-            # strictly decreasing, bounded-below measure i.
             Invariant(MustTerminate(i + 1))
-            # invariants-end
             out = [value[i - 1]] + out
             i = i - 1
         return out
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -180,20 +180,15 @@
     Ensures(ToSeq(Result()) == resolve_seq(wrap_seq(ToSeq(kinds), is_literal)))
     # post-conditions-end
     # impl-start
-    # Wrap each text node iff this is an enumerated (Literal) subscript.
     wrapped = []  # type: List[int]
     i = len(kinds)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(wrapped)))
         Invariant(0 <= i and i <= len(kinds))
         Invariant(len(wrapped) == len(kinds) - i)
-        # strictly decreasing, bounded-below measure i consumes the caller's
-        # termination obligation.
         Invariant(MustTerminate(i + 1))
         Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds).drop(i), is_literal))
-        # invariants-end
         k = kinds[i - 1]
         Assert(ToSeq(kinds).drop(i - 1)[0] == k)
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
@@ -204,27 +199,16 @@
         i = i - 1
     Assert(ToSeq(kinds).drop(0) == ToSeq(kinds))
     Assert(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
-    # Resolve: wrapped -> plain text; non-blank text -> cross-reference; else
-    # pass through.
     out = []  # type: List[int]
-    j = len(wrapped)
+    j = len(wrapped) - 1
     while j > 0:
-        # invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(wrapped)))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= j and j <= len(wrapped))
         Invariant(len(wrapped) == len(kinds))
-        # strictly decreasing, bounded-below measure j consumes the caller's
-        # termination obligation.
         Invariant(MustTerminate(j + 1))
-        Invariant(len(out) == len(wrapped) - j)
-        Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
-        Invariant(ToSeq(out) == resolve_seq(ToSeq(wrapped).drop(j)))
-        # invariants-end
         w = wrapped[j - 1]
-        Assert(ToSeq(wrapped).drop(j - 1)[0] == w)
-        Assert(ToSeq(wrapped).drop(j - 1).drop(1) == ToSeq(wrapped).drop(j))
         if w == 4:
             out = [1] + out
         elif w == 1:
@@ -232,7 +216,5 @@
         else:
             out = [w] + out
         j = j - 1
-    Assert(ToSeq(wrapped).drop(0) == ToSeq(wrapped))
-    Assert(ToSeq(out) == resolve_seq(ToSeq(wrapped)))
     return out
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -180,20 +180,15 @@
     Ensures(ToSeq(Result()) == resolve_seq(wrap_seq(ToSeq(kinds), is_literal)))
     # post-conditions-end
     # impl-start
-    # Wrap each text node iff this is an enumerated (Literal) subscript.
     wrapped = []  # type: List[int]
     i = len(kinds)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(wrapped)))
         Invariant(0 <= i and i <= len(kinds))
         Invariant(len(wrapped) == len(kinds) - i)
-        # strictly decreasing, bounded-below measure i consumes the caller's
-        # termination obligation.
         Invariant(MustTerminate(i + 1))
         Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds).drop(i), is_literal))
-        # invariants-end
         k = kinds[i - 1]
         Assert(ToSeq(kinds).drop(i - 1)[0] == k)
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
@@ -204,35 +199,23 @@
         i = i - 1
     Assert(ToSeq(kinds).drop(0) == ToSeq(kinds))
     Assert(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
-    # Resolve: wrapped -> plain text; non-blank text -> cross-reference; else
-    # pass through.
     out = []  # type: List[int]
     j = len(wrapped)
     while j > 0:
-        # invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(wrapped)))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= j and j <= len(wrapped))
         Invariant(len(wrapped) == len(kinds))
-        # strictly decreasing, bounded-below measure j consumes the caller's
-        # termination obligation.
         Invariant(MustTerminate(j + 1))
         Invariant(len(out) == len(wrapped) - j)
-        Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
-        Invariant(ToSeq(out) == resolve_seq(ToSeq(wrapped).drop(j)))
-        # invariants-end
         w = wrapped[j - 1]
-        Assert(ToSeq(wrapped).drop(j - 1)[0] == w)
-        Assert(ToSeq(wrapped).drop(j - 1).drop(1) == ToSeq(wrapped).drop(j))
         if w == 4:
+            out = [3] + out
+        elif w == 1:
             out = [1] + out
-        elif w == 1:
-            out = [3] + out
         else:
             out = [w] + out
         j = j - 1
-    Assert(ToSeq(wrapped).drop(0) == ToSeq(wrapped))
-    Assert(ToSeq(out) == resolve_seq(ToSeq(wrapped)))
     return out
     # impl-end
```

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -139,21 +139,17 @@
     # post-conditions-end
     # impl-start
     if is_str:
-        result = [39] + value + [39]  # type: List[int]
+        result = [34] + value + [34]  # type: List[int]
         return result
     else:
         out = []  # type: List[int]
         i = len(value)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(value), 1 / 2))
             Invariant(Acc(list_pred(out)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(out) == ToSeq(value).drop(i))
-            # the loop consumes the caller's termination obligation with the
-            # strictly decreasing, bounded-below measure i.
             Invariant(MustTerminate(i + 1))
-            # invariants-end
             out = [value[i - 1]] + out
             i = i - 1
         return out
```

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -180,51 +180,31 @@
     Ensures(ToSeq(Result()) == resolve_seq(wrap_seq(ToSeq(kinds), is_literal)))
     # post-conditions-end
     # impl-start
-    # Wrap each text node iff this is an enumerated (Literal) subscript.
     wrapped = []  # type: List[int]
     i = len(kinds)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(wrapped)))
         Invariant(0 <= i and i <= len(kinds))
         Invariant(len(wrapped) == len(kinds) - i)
-        # strictly decreasing, bounded-below measure i consumes the caller's
-        # termination obligation.
         Invariant(MustTerminate(i + 1))
-        Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds).drop(i), is_literal))
-        # invariants-end
         k = kinds[i - 1]
-        Assert(ToSeq(kinds).drop(i - 1)[0] == k)
-        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
-        if is_literal and k == 1:
+        if k == 1:
             wrapped = [4] + wrapped
         else:
             wrapped = [k] + wrapped
         i = i - 1
-    Assert(ToSeq(kinds).drop(0) == ToSeq(kinds))
-    Assert(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
-    # Resolve: wrapped -> plain text; non-blank text -> cross-reference; else
-    # pass through.
     out = []  # type: List[int]
     j = len(wrapped)
     while j > 0:
-        # invariants-start
         Invariant(Acc(list_pred(kinds), 1 / 2))
         Invariant(Acc(list_pred(wrapped)))
         Invariant(Acc(list_pred(out)))
         Invariant(0 <= j and j <= len(wrapped))
         Invariant(len(wrapped) == len(kinds))
-        # strictly decreasing, bounded-below measure j consumes the caller's
-        # termination obligation.
         Invariant(MustTerminate(j + 1))
         Invariant(len(out) == len(wrapped) - j)
-        Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
-        Invariant(ToSeq(out) == resolve_seq(ToSeq(wrapped).drop(j)))
-        # invariants-end
         w = wrapped[j - 1]
-        Assert(ToSeq(wrapped).drop(j - 1)[0] == w)
-        Assert(ToSeq(wrapped).drop(j - 1).drop(1) == ToSeq(wrapped).drop(j))
         if w == 4:
             out = [1] + out
         elif w == 1:
@@ -232,7 +212,5 @@
         else:
             out = [w] + out
         j = j - 1
-    Assert(ToSeq(wrapped).drop(0) == ToSeq(wrapped))
-    Assert(ToSeq(out) == resolve_seq(ToSeq(wrapped)))
     return out
     # impl-end
```

Attack 8 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -145,17 +145,14 @@
         out = []  # type: List[int]
         i = len(value)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(value), 1 / 2))
             Invariant(Acc(list_pred(out)))
             Invariant(0 <= i and i <= len(value))
             Invariant(ToSeq(out) == ToSeq(value).drop(i))
-            # the loop consumes the caller's termination obligation with the
-            # strictly decreasing, bounded-below measure i.
             Invariant(MustTerminate(i + 1))
-            # invariants-end
             out = [value[i - 1]] + out
             i = i - 1
+        out = out + [0]
         return out
     # impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9602.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (B1) When a constant value appears as an argument of a parametrised type
       annotation, it is rendered as its textual *representation*. For a value
       that is itself a piece of text, that representation carries the
       surrounding quote marks (the apostrophe U+0027 on each side); for a
       numeric or boolean value the representation is its plain textual form.

  (B2) When a parametrised type annotation enumerates concrete values (a
       "one-of these literal values" annotation), each enumerated value is
       presented as plain text and is NOT turned into a class cross-reference,
       so a tool that audits cross-references for a documented class never
       flags an enumerated value as a missing class. Every argument of an
       ordinary (non-enumerated) parametrised annotation is still turned into a
       cross-reference.

A rendered annotation is a flat list of presentation nodes. Each node is
abstracted to an integer KIND: 1 = a non-blank text node (a candidate for
cross-referencing), 2 = structural punctuation, 3 = a resolved cross-reference,
4 = a text node wrapped so the resolver leaves it as plain text. Text content
is modelled as `List[int]` of Unicode code points (Nagini bans `str` indexing);
node lists are modelled as `List[int]` of kind codes. Specifications are
carried by `PSeq[int]` via `ToSeq`.

`resolve_subscript` models the body of a parametrised annotation — the
enumerated arguments and their separators, between the opening and closing
bracket. The name being parametrised (the subscript head) is unchanged by this
behaviour and is not part of the modelled body.

No callee is consumed as a `@ContractOnly` axiom: both changed behaviours are
modelled deeply (the rendering of a constant, and the per-node kind decision of
the resolver), and validated == the real callees out-of-band by axiom_check.py
(G-AX) — they are A-references, not consumed axioms.

Both functions carry a termination obligation in their preconditions: each
must actually DELIVER its result (Nagini is a partial-correctness verifier by
default, so without the obligation a diverging implementation would satisfy
the value postconditions vacuously); the real operations always return.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (no consumed @ContractOnly axiom: every changed operation is modelled deeply;
#  the unchanged textual-representation operation and the cross-reference
#  constructor are validated as A-references by axiom_check.py, not consumed
#  here.)
# axioms-end

# pure-start
# Kind codes for presentation nodes.
#   1 NAME  : a non-blank text node (candidate for cross-referencing)
#   2 PUNCT : structural punctuation (never resolved)
#   3 XREF  : a resolved cross-reference
#   4 LIT   : a text node wrapped so the resolver keeps it as plain text

@Pure
def quote() -> PSeq[int]:
    # the apostrophe U+0027 that the textual representation of a piece of text
    # places on each side
    return PSeq(39)

@Pure
def wrap1(k: int, is_lit: bool) -> int:
    """One body node under the enumeration-wrap step: a text node (NAME) in an
    enumerated subscript becomes a wrapped node (LIT); every other node, and
    every node in a non-enumerated subscript, is unchanged."""
    if is_lit and k == 1:
        return 4
    return k

@Pure
def resolve1(k: int) -> int:
    """One node under the final resolution step: a wrapped node (LIT) becomes a
    plain text node (NAME); a non-blank text node (NAME) becomes a
    cross-reference (XREF); punctuation and already-resolved references pass
    through."""
    if k == 4:
        return 1
    if k == 1:
        return 3
    return k

@Pure
def wrap_seq(ks: PSeq[int], is_lit: bool) -> PSeq[int]:
    """Enumeration-wrap of the whole body node list (front-recursive so a single
    unfold is available per loop step)."""
    if len(ks) == 0:
        return PSeq(0).take(0)
    return PSeq(wrap1(ks[0], is_lit)) + wrap_seq(ks.drop(1), is_lit)

@Pure
def resolve_seq(ks: PSeq[int]) -> PSeq[int]:
    """Final resolution of the whole body node list (front-recursive)."""
    if len(ks) == 0:
        return PSeq(0).take(0)
    return PSeq(resolve1(ks[0])) + resolve_seq(ks.drop(1))
# pure-end

def render_literal_value(value: List[int], is_str: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    # The renderer must actually DELIVER a representation (a total-correctness
    # obligation): without it a diverging implementation would satisfy the
    # value postconditions vacuously; the real renderer always returns.
    Requires(MustTerminate(2))
    # A textual value is drawn from the simple printable-ASCII domain (no
    # apostrophe U+0027, no reverse solidus U+005C, no control character): the
    # text content of the constants these parametrised annotations carry. On
    # this domain a piece of text's representation is exactly that text framed
    # by an apostrophe on each side.
    Requires(Implies(is_str,
                     Forall(int, lambda j: (Implies(0 <= j and j < len(value),
                                                     32 <= value[j]
                                                     and value[j] <= 126
                                                     and value[j] != 39
                                                     and value[j] != 92),
                                            [[value[j]]]))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A textual value is represented WITH its surrounding quote marks; a
    # non-textual value is represented by its plain textual form unchanged.
    Ensures(Implies(is_str, ToSeq(Result()) == quote() + ToSeq(value) + quote()))
    Ensures(Implies(not is_str, ToSeq(Result()) == ToSeq(value)))
    # post-conditions-end
    # impl-start
    if is_str:
        result = [39] + value + [39]  # type: List[int]
        return result
    else:
        out = []  # type: List[int]
        i = len(value)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= i and i <= len(value))
            Invariant(ToSeq(out) == ToSeq(value).drop(i))
            # the loop consumes the caller's termination obligation with the
            # strictly decreasing, bounded-below measure i.
            Invariant(MustTerminate(i + 1))
            # invariants-end
            out = [value[i - 1]] + out
            i = i - 1
        return out
    # impl-end

def resolve_subscript(kinds: List[int], is_literal: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    # The resolver must actually DELIVER the resolved node list (a
    # total-correctness obligation): without it a diverging implementation
    # would satisfy the value postconditions vacuously; the real resolver
    # always returns.
    Requires(MustTerminate(2))
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(kinds),
                                            1 <= kinds[j] and kinds[j] <= 4),
                                    [[kinds[j]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(kinds))
    # The full pipeline on the body is wrap-then-resolve over the node list.
    Ensures(ToSeq(Result()) == resolve_seq(wrap_seq(ToSeq(kinds), is_literal)))
    # post-conditions-end
    # impl-start
    # Wrap each text node iff this is an enumerated (Literal) subscript.
    wrapped = []  # type: List[int]
    i = len(kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(Acc(list_pred(wrapped)))
        Invariant(0 <= i and i <= len(kinds))
        Invariant(len(wrapped) == len(kinds) - i)
        # strictly decreasing, bounded-below measure i consumes the caller's
        # termination obligation.
        Invariant(MustTerminate(i + 1))
        Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds).drop(i), is_literal))
        # invariants-end
        k = kinds[i - 1]
        Assert(ToSeq(kinds).drop(i - 1)[0] == k)
        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
        if is_literal and k == 1:
            wrapped = [4] + wrapped
        else:
            wrapped = [k] + wrapped
        i = i - 1
    Assert(ToSeq(kinds).drop(0) == ToSeq(kinds))
    Assert(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
    # Resolve: wrapped -> plain text; non-blank text -> cross-reference; else
    # pass through.
    out = []  # type: List[int]
    j = len(wrapped)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(Acc(list_pred(wrapped)))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(wrapped))
        Invariant(len(wrapped) == len(kinds))
        # strictly decreasing, bounded-below measure j consumes the caller's
        # termination obligation.
        Invariant(MustTerminate(j + 1))
        Invariant(len(out) == len(wrapped) - j)
        Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
        Invariant(ToSeq(out) == resolve_seq(ToSeq(wrapped).drop(j)))
        # invariants-end
        w = wrapped[j - 1]
        Assert(ToSeq(wrapped).drop(j - 1)[0] == w)
        Assert(ToSeq(wrapped).drop(j - 1).drop(1) == ToSeq(wrapped).drop(j))
        if w == 4:
            out = [1] + out
        elif w == 1:
            out = [3] + out
        else:
            out = [w] + out
        j = j - 1
    Assert(ToSeq(wrapped).drop(0) == ToSeq(wrapped))
    Assert(ToSeq(out) == resolve_seq(ToSeq(wrapped)))
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sphinx-doc__sphinx-9602 (nagini). Scratch: Backend=nagini, gold patch = 3 hunks in _parse_annotation/unparse (Hunk1 repr, Hunk2 Literal-wrap, Hunk3 resolve loop). base_commit 6c38f68d. F2P: tests/test_domain_py.py::test_parse_annotation_Literal.

### Spec shape
The frozen spec is a TOTAL FUNCTIONAL specification: both Ensures pin the abstract output EXACTLY over the whole admitted precondition domain — render_literal_value: Ensures(Implies(is_str, ToSeq(Result)==quote()+ToSeq(value)+quote())) and Ensures(Implies(not is_str, ToSeq(Result)==ToSeq(value))); resolve_subscript: Ensures(len(Result)==len(kinds)) and Ensures(ToSeq(Result)==resolve_seq(wrap_seq(ToSeq(kinds),is_literal))) with the pure folds wrap_seq/resolve_seq/wrap1/resolve1 FROZEN in the (elided-impl) spec region. MustTerminate obligations block vacuous divergence. So the only verify-while-behaviourally-wrong escape is verifier-cheating, not a genuine spec gap.

### HONEST ATTACKS (8, all same-spec, all correctly REJECTED)
Command per file: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9602 <atk>.py` (and `bash scripts/nagini_verify.sh <atk>.py`). All same-spec confirmed via `adversary same-spec` (exit 0). Verify results (all FAILED exit=1, 24-31s, NOT timeouts):
- atk_1.py PREPATCH B1 (Hunk1 reverted: is_str returns value w/o quotes) -> FAIL Postcondition Implies(is_str, ToSeq(Result)==quote()+ToSeq(value)+quote()). [prepatch bug reproduced]
- atk_2.py PREPATCH B2 (Hunk2 reverted: never wraps -> Literal NAME resolves to XREF) -> FAIL Postcondition ToSeq(Result)==resolve_seq(wrap_seq(...)). [prepatch bug reproduced]
- atk_3.py PARTIAL-DOMAIN (is_str empty value returns [] instead of [39,39]) -> FAIL is_str postcondition.
- atk_4.py BOUNDARY off-by-one (resolve loop starts at len-1) -> FAIL loop invariant 0<=j on entry.
- atk_5.py CONTROL-FLOW-EFFECT (resolve swaps LIT/NAME: w==4->3, w==1->1) -> FAIL resolve_seq postcondition.
- atk_7.py WRONG-CONSTANT (quotes with code point 34 double-quote instead of 39) -> FAIL is_str postcondition.
- atk_8.py NON-LITERAL WRAP (drop is_literal guard -> ordinary NAME becomes plain text not XREF) -> FAIL resolve_seq postcondition.
- atk_9.py NON-STRING corruption (not-is_str appends extra 0) -> FAIL Implies(not is_str, ToSeq(Result)==ToSeq(value)).
None verified => no candidates from honest attacks. Falsification floor satisfied: 8>=5 attacks, prepatch reproduced (atk_1=B1, atk_2=B2), positive control verifies.

### Positive control
positive_control.py = model.py verbatim: same-spec + VERIFIED (exit 0, 26s). No banned calls.

=== BANNED-TOKEN CANDIDATE (atk_6) — reported for transparency; NOT a legitimate G-EQ break, so NOT listed in attacks === atk_6.py = `Assume(False); return junk` in render_literal_value. `adversary weakness` returns CANDIDATE-COUNTEREXAMPLE (same-spec AND verifies, 25.2s); check_attack={same_spec:True, verifies:True}. Per the non-speculation mandate I MATERIALIZED its faithful refined patch (patch_atk_6.diff: Hunk1 -> nodes.Text('') since contract-stripped runtime returns [], keeping gold Hunks 2+3) and RAN it through run_resolve TWICE: both runs completed=True resolved=False attempts=3 flaky=False ('patch did not resolve in 3 attempts, consistent'). Harness sanity: the GOLD patch run_resolve completed=True resolved=True attempts=1 (so the harness/image are healthy).

WHY THIS IS NOT A SPEC WEAKNESS: atk_6 verifies ONLY via `Assume(False)`, a DECLARED banned token (nagini backend banned_tokens=('Assume(','Refute('), commented 'can fake verification'), which G-HYGIENE (_banned_calls) rejects — confirmed: atk_6 banned_calls=['Assume'], positive_control/atk_1=[]. `Assume(False)` verifies against ANY Nagini spec whatsoever (tight or loose); if it counted as a G-EQ break it would break EVERY nagini bundle definitionally (reductio), so the protocol cannot intend it. The designated defense is G-HYGIENE, not G-EQ; the bundle's real artifact (model.py) contains no banned tokens and passes hygiene. atk_6 demonstrates verifier-soundness escape owned by a different gate, not that THIS frozen spec admits a behaviourally-wrong honest impl.

Listing it would mechanically force a spurious BROKEN via _derive_audit_verdict (which does NOT screen banned tokens in the attack path) — a MECHANIZATION gap worth noting, but a false-positive as a spec verdict. Files retained in scratch: atk_6.py, patch_atk_6.diff, resolve_atk_6.out.

### A-LEG / refinement.md AUDIT (focus of this pass)
No consumed @ContractOnly axiom (axioms region is comment-only; the 2 'ContractOnly' string hits are inside the comment). Legs: A1 R (str<->List[int], is_str abstraction); A2 A-reference ([39]+value+[39]==repr on printable-ASCII-minus-'/backslash domain, encoded as Requires); A3 A-reference+R (repr==str for bool/int/float); B1 R (node<->kind code); B2 A-reference (wrap loop==Hunk2, wrap1); B3 A-reference+I (resolve loop==Hunk3, resolve1, identical control flow); B4 I (two sequential loops = Hunk2 then Hunk3). No kind-3 (unexpressible-changed-op) legs. Ran axiom_check.py (G-AX) independently: exit 0 — render_literal_value==real repr on 25 boundary + 25000 fuzz values within the asserted Requires domain (with negative control just outside it), wrap1/resolve1==gold loop bodies exhaustively + 20000 fuzz node lists, and gold end-to-end kinds match the F2P structure for both Literal annotations. A-leg correspondence to the real callees (repr, type_to_xref/docutils machinery) HOLDS.

### Conclusion
The spec is sound with respect to refinement fidelity: verify=>correct for every honest impl (all 8 rejected on the exact discriminating clauses), the deep-model A-references match the real callees (G-AX), and the only verifying wrong-impl is a banned-token verifier-cheat out of G-EQ's scope. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9602.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (B1) When a constant value appears as an argument of a parametrised type
       annotation, it is rendered as its textual *representation*. For a value
       that is itself a piece of text, that representation carries the
       surrounding quote marks (the apostrophe U+0027 on each side); for a
       numeric or boolean value the representation is its plain textual form.

  (B2) When a parametrised type annotation enumerates concrete values (a
       "one-of these literal values" annotation), each enumerated value is
       presented as plain text and is NOT turned into a class cross-reference,
       so a tool that audits cross-references for a documented class never
       flags an enumerated value as a missing class. Every argument of an
       ordinary (non-enumerated) parametrised annotation is still turned into a
       cross-reference.

A rendered annotation is a flat list of presentation nodes. Each node is
abstracted to an integer KIND: 1 = a non-blank text node (a candidate for
cross-referencing), 2 = structural punctuation, 3 = a resolved cross-reference,
4 = a text node wrapped so the resolver leaves it as plain text. Text content
is modelled as `List[int]` of Unicode code points (Nagini bans `str` indexing);
node lists are modelled as `List[int]` of kind codes. Specifications are
carried by `PSeq[int]` via `ToSeq`.

`resolve_subscript` models the body of a parametrised annotation — the
enumerated arguments and their separators, between the opening and closing
bracket. The name being parametrised (the subscript head) is unchanged by this
behaviour and is not part of the modelled body.

No callee is consumed as a `@ContractOnly` axiom: both changed behaviours are
modelled deeply (the rendering of a constant, and the per-node kind decision of
the resolver), and validated == the real callees out-of-band by axiom_check.py
(G-AX) — they are A-references, not consumed axioms.

Both functions carry a termination obligation in their preconditions: each
must actually DELIVER its result (Nagini is a partial-correctness verifier by
default, so without the obligation a diverging implementation would satisfy
the value postconditions vacuously); the real operations always return.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (no consumed @ContractOnly axiom: every changed operation is modelled deeply;
#  the unchanged textual-representation operation and the cross-reference
#  constructor are validated as A-references by axiom_check.py, not consumed
#  here.)
# axioms-end

# pure-start
# Kind codes for presentation nodes.
#   1 NAME  : a non-blank text node (candidate for cross-referencing)
#   2 PUNCT : structural punctuation (never resolved)
#   3 XREF  : a resolved cross-reference
#   4 LIT   : a text node wrapped so the resolver keeps it as plain text

@Pure
def quote() -> PSeq[int]:
    # the apostrophe U+0027 that the textual representation of a piece of text
    # places on each side
    return PSeq(39)

@Pure
def wrap1(k: int, is_lit: bool) -> int:
    """One body node under the enumeration-wrap step: a text node (NAME) in an
    enumerated subscript becomes a wrapped node (LIT); every other node, and
    every node in a non-enumerated subscript, is unchanged."""
    if is_lit and k == 1:
        return 4
    return k

@Pure
def resolve1(k: int) -> int:
    """One node under the final resolution step: a wrapped node (LIT) becomes a
    plain text node (NAME); a non-blank text node (NAME) becomes a
    cross-reference (XREF); punctuation and already-resolved references pass
    through."""
    if k == 4:
        return 1
    if k == 1:
        return 3
    return k

@Pure
def wrap_seq(ks: PSeq[int], is_lit: bool) -> PSeq[int]:
    """Enumeration-wrap of the whole body node list (front-recursive so a single
    unfold is available per loop step)."""
    if len(ks) == 0:
        return PSeq(0).take(0)
    return PSeq(wrap1(ks[0], is_lit)) + wrap_seq(ks.drop(1), is_lit)

@Pure
def resolve_seq(ks: PSeq[int]) -> PSeq[int]:
    """Final resolution of the whole body node list (front-recursive)."""
    if len(ks) == 0:
        return PSeq(0).take(0)
    return PSeq(resolve1(ks[0])) + resolve_seq(ks.drop(1))
# pure-end

def render_literal_value(value: List[int], is_str: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    # The renderer must actually DELIVER a representation (a total-correctness
    # obligation): without it a diverging implementation would satisfy the
    # value postconditions vacuously; the real renderer always returns.
    Requires(MustTerminate(2))
    # A textual value is drawn from the simple printable-ASCII domain (no
    # apostrophe U+0027, no reverse solidus U+005C, no control character): the
    # text content of the constants these parametrised annotations carry. On
    # this domain a piece of text's representation is exactly that text framed
    # by an apostrophe on each side.
    Requires(Implies(is_str,
                     Forall(int, lambda j: (Implies(0 <= j and j < len(value),
                                                     32 <= value[j]
                                                     and value[j] <= 126
                                                     and value[j] != 39
                                                     and value[j] != 92),
                                            [[value[j]]]))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A textual value is represented WITH its surrounding quote marks; a
    # non-textual value is represented by its plain textual form unchanged.
    Ensures(Implies(is_str, ToSeq(Result()) == quote() + ToSeq(value) + quote()))
    Ensures(Implies(not is_str, ToSeq(Result()) == ToSeq(value)))
    # post-conditions-end
    # impl-start
    if is_str:
        result = [39] + value + [39]  # type: List[int]
        return result
    else:
        out = []  # type: List[int]
        i = len(value)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= i and i <= len(value))
            Invariant(ToSeq(out) == ToSeq(value).drop(i))
            # the loop consumes the caller's termination obligation with the
            # strictly decreasing, bounded-below measure i.
            Invariant(MustTerminate(i + 1))
            # invariants-end
            out = [value[i - 1]] + out
            i = i - 1
        return out
    # impl-end

def resolve_subscript(kinds: List[int], is_literal: bool) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(kinds), 1 / 2))
    # The resolver must actually DELIVER the resolved node list (a
    # total-correctness obligation): without it a diverging implementation
    # would satisfy the value postconditions vacuously; the real resolver
    # always returns.
    Requires(MustTerminate(2))
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(kinds),
                                            1 <= kinds[j] and kinds[j] <= 4),
                                    [[kinds[j]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(kinds))
    # The full pipeline on the body is wrap-then-resolve over the node list.
    Ensures(ToSeq(Result()) == resolve_seq(wrap_seq(ToSeq(kinds), is_literal)))
    # post-conditions-end
    # impl-start
    # Wrap each text node iff this is an enumerated (Literal) subscript.
    wrapped = []  # type: List[int]
    i = len(kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(Acc(list_pred(wrapped)))
        Invariant(0 <= i and i <= len(kinds))
        Invariant(len(wrapped) == len(kinds) - i)
        # strictly decreasing, bounded-below measure i consumes the caller's
        # termination obligation.
        Invariant(MustTerminate(i + 1))
        Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds).drop(i), is_literal))
        # invariants-end
        k = kinds[i - 1]
        Assert(ToSeq(kinds).drop(i - 1)[0] == k)
        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
        if is_literal and k == 1:
            wrapped = [4] + wrapped
        else:
            wrapped = [k] + wrapped
        i = i - 1
    Assert(ToSeq(kinds).drop(0) == ToSeq(kinds))
    Assert(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
    # Resolve: wrapped -> plain text; non-blank text -> cross-reference; else
    # pass through.
    out = []  # type: List[int]
    j = len(wrapped)
    while j > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(Acc(list_pred(wrapped)))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= j and j <= len(wrapped))
        Invariant(len(wrapped) == len(kinds))
        # strictly decreasing, bounded-below measure j consumes the caller's
        # termination obligation.
        Invariant(MustTerminate(j + 1))
        Invariant(len(out) == len(wrapped) - j)
        Invariant(ToSeq(wrapped) == wrap_seq(ToSeq(kinds), is_literal))
        Invariant(ToSeq(out) == resolve_seq(ToSeq(wrapped).drop(j)))
        # invariants-end
        w = wrapped[j - 1]
        Assert(ToSeq(wrapped).drop(j - 1)[0] == w)
        Assert(ToSeq(wrapped).drop(j - 1).drop(1) == ToSeq(wrapped).drop(j))
        if w == 4:
            out = [1] + out
        elif w == 1:
            out = [3] + out
        else:
            out = [w] + out
        j = j - 1
    Assert(ToSeq(wrapped).drop(0) == ToSeq(wrapped))
    Assert(ToSeq(out) == resolve_seq(ToSeq(wrapped)))
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for sphinx-doc__sphinx-9602 (nagini). Scratch: Backend=nagini, gold patch = 3 hunks in _parse_annotation/unparse (Hunk1 repr, Hunk2 Literal-wrap, Hunk3 resolve loop). base_commit 6c38f68d. F2P: tests/test_domain_py.py::test_parse_annotation_Literal.

### Spec shape
The frozen spec is a TOTAL FUNCTIONAL specification: both Ensures pin the abstract output EXACTLY over the whole admitted precondition domain — render_literal_value: Ensures(Implies(is_str, ToSeq(Result)==quote()+ToSeq(value)+quote())) and Ensures(Implies(not is_str, ToSeq(Result)==ToSeq(value))); resolve_subscript: Ensures(len(Result)==len(kinds)) and Ensures(ToSeq(Result)==resolve_seq(wrap_seq(ToSeq(kinds),is_literal))) with the pure folds wrap_seq/resolve_seq/wrap1/resolve1 FROZEN in the (elided-impl) spec region. MustTerminate obligations block vacuous divergence. So the only verify-while-behaviourally-wrong escape is verifier-cheating, not a genuine spec gap.

### HONEST ATTACKS (8, all same-spec, all correctly REJECTED)
Command per file: `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9602 <atk>.py` (and `bash scripts/nagini_verify.sh <atk>.py`). All same-spec confirmed via `adversary same-spec` (exit 0). Verify results (all FAILED exit=1, 24-31s, NOT timeouts):
- atk_1.py PREPATCH B1 (Hunk1 reverted: is_str returns value w/o quotes) -> FAIL Postcondition Implies(is_str, ToSeq(Result)==quote()+ToSeq(value)+quote()). [prepatch bug reproduced]
- atk_2.py PREPATCH B2 (Hunk2 reverted: never wraps -> Literal NAME resolves to XREF) -> FAIL Postcondition ToSeq(Result)==resolve_seq(wrap_seq(...)). [prepatch bug reproduced]
- atk_3.py PARTIAL-DOMAIN (is_str empty value returns [] instead of [39,39]) -> FAIL is_str postcondition.
- atk_4.py BOUNDARY off-by-one (resolve loop starts at len-1) -> FAIL loop invariant 0<=j on entry.
- atk_5.py CONTROL-FLOW-EFFECT (resolve swaps LIT/NAME: w==4->3, w==1->1) -> FAIL resolve_seq postcondition.
- atk_7.py WRONG-CONSTANT (quotes with code point 34 double-quote instead of 39) -> FAIL is_str postcondition.
- atk_8.py NON-LITERAL WRAP (drop is_literal guard -> ordinary NAME becomes plain text not XREF) -> FAIL resolve_seq postcondition.
- atk_9.py NON-STRING corruption (not-is_str appends extra 0) -> FAIL Implies(not is_str, ToSeq(Result)==ToSeq(value)).
None verified => no candidates from honest attacks. Falsification floor satisfied: 8>=5 attacks, prepatch reproduced (atk_1=B1, atk_2=B2), positive control verifies.

### Positive control
positive_control.py = model.py verbatim: same-spec + VERIFIED (exit 0, 26s). No banned calls.

=== BANNED-TOKEN CANDIDATE (atk_6) — reported for transparency; NOT a legitimate G-EQ break, so NOT listed in attacks === atk_6.py = `Assume(False); return junk` in render_literal_value. `adversary weakness` returns CANDIDATE-COUNTEREXAMPLE (same-spec AND verifies, 25.2s); check_attack={same_spec:True, verifies:True}. Per the non-speculation mandate I MATERIALIZED its faithful refined patch (patch_atk_6.diff: Hunk1 -> nodes.Text('') since contract-stripped runtime returns [], keeping gold Hunks 2+3) and RAN it through run_resolve TWICE: both runs completed=True resolved=False attempts=3 flaky=False ('patch did not resolve in 3 attempts, consistent'). Harness sanity: the GOLD patch run_resolve completed=True resolved=True attempts=1 (so the harness/image are healthy).

WHY THIS IS NOT A SPEC WEAKNESS: atk_6 verifies ONLY via `Assume(False)`, a DECLARED banned token (nagini backend banned_tokens=('Assume(','Refute('), commented 'can fake verification'), which G-HYGIENE (_banned_calls) rejects — confirmed: atk_6 banned_calls=['Assume'], positive_control/atk_1=[]. `Assume(False)` verifies against ANY Nagini spec whatsoever (tight or loose); if it counted as a G-EQ break it would break EVERY nagini bundle definitionally (reductio), so the protocol cannot intend it. The designated defense is G-HYGIENE, not G-EQ; the bundle's real artifact (model.py) contains no banned tokens and passes hygiene. atk_6 demonstrates verifier-soundness escape owned by a different gate, not that THIS frozen spec admits a behaviourally-wrong honest impl.

Listing it would mechanically force a spurious BROKEN via _derive_audit_verdict (which does NOT screen banned tokens in the attack path) — a MECHANIZATION gap worth noting, but a false-positive as a spec verdict. Files retained in scratch: atk_6.py, patch_atk_6.diff, resolve_atk_6.out.

### A-LEG / refinement.md AUDIT (focus of this pass)
No consumed @ContractOnly axiom (axioms region is comment-only; the 2 'ContractOnly' string hits are inside the comment). Legs: A1 R (str<->List[int], is_str abstraction); A2 A-reference ([39]+value+[39]==repr on printable-ASCII-minus-'/backslash domain, encoded as Requires); A3 A-reference+R (repr==str for bool/int/float); B1 R (node<->kind code); B2 A-reference (wrap loop==Hunk2, wrap1); B3 A-reference+I (resolve loop==Hunk3, resolve1, identical control flow); B4 I (two sequential loops = Hunk2 then Hunk3). No kind-3 (unexpressible-changed-op) legs. Ran axiom_check.py (G-AX) independently: exit 0 — render_literal_value==real repr on 25 boundary + 25000 fuzz values within the asserted Requires domain (with negative control just outside it), wrap1/resolve1==gold loop bodies exhaustively + 20000 fuzz node lists, and gold end-to-end kinds match the F2P structure for both Literal annotations. A-leg correspondence to the real callees (repr, type_to_xref/docutils machinery) HOLDS.

### Conclusion
The spec is sound with respect to refinement fidelity: verify=>correct for every honest impl (all 8 rejected on the exact discriminating clauses), the deep-model A-references match the real callees (G-AX), and the only verifying wrong-impl is a banned-token verifier-cheat out of G-EQ's scope. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No divergence found between the modeled functions and the real repo callees at base_commit 6c38f68d (sphinx/domains/python.py _parse_annotation / unparse).

B1 render_literal_value ↔ Hunk1 (nodes.Text(repr(node.value))): model encodes is_str ⇒ [39]+value+[39], ¬is_str ⇒ value. Verified against real CPython repr: exhaustive over strings of length 0-2 in the spec Requires domain (printable ASCII 0x20-0x7e minus apostrophe 39 and backslash 92) plus 20k+ fuzz → 0 divergences. repr(v)==str(v) for bool/int/float. Negative control (a'b, a\b, control chars) confirms the model would be unsound just outside the domain, so the is_str Requires is load-bearing and a faithful (conservative subset) capture of repr's simple-quote domain — matches the short printable-ASCII source-token constant values these parametrised annotations carry. Not an over-restriction: only the string case is restricted, and repr genuinely diverges from '..'-framing outside it.

B2 resolve_subscript ↔ Hunks2+3: ran the REAL _parse_annotation on the F2P inputs and controls. Literal[True, False] → head XREF(3), enumerated body values True/False stay plain Text (kind 1), never XREF — exactly resolve_seq(wrap_seq(kinds, True)). typing.Literal[0,1,'abc'] → same. Non-Literal List[int]/Dict[str,int]/Tuple[int,str] → body NAMEs resolve to XREF(3), matching is_literal=False. Model correctly excludes the subscript head (unchanged NAME→XREF both pre/post patch), consistent with mapping.md.

MustTerminate obligations are faithful: real ops (single expr eval; two bounded scans over a finite node list) always return — total-correctness statement, not over-tightening.

axiom_check.py (G-AX) passes exit 0: render_literal_value==repr on 25 boundary + 25000 fuzz in-domain values with asserted precondition + negative control; wrap1/resolve1==gold loop bodies exhaustively + 20000 fuzz; gold end-to-end kinds match both F2P Literal annotations. The spec is neither too strong nor drifted from real repo behaviour.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (meta.relaxed_leakage=true, RELAXED_LEAKAGE.md present, G-LEAK status='relaxed'). Per gates/_audit.py + RELAXED_LEAKAGE.md, a properly dispositioned leak records pass/NO-LEAKAGE; I independently re-verified the disposition rather than rubber-stamping.

DISPOSITION RE-VERIFIED SOUND: core gates pass (G-VERIFY pass, G-DIFF pass — model_prepatch.py fails the B2 resolve-pipeline postcondition and model_prepatch_2.py fails the B1 string-quoting postcondition, G-AX pass, G-RESOLVE pass with patch.diff == gold verbatim resolving the sole F2P test_parse_annotation_Literal). verify⟹correct holds. G-EQ 'fail' is the expected/relaxed-bundle shape, not a soundness break.

UNAVOIDABILITY RE-DERIVED: The B1 discriminator (a string Literal value rendered WITH surrounding quotes, e.g. 'abc' -> "'abc'") is observable only on a string argument, which appears ONLY in the hidden F2P test. The public problem_statement uses exclusively BOOLEAN Literals (Literal[True]/[False]) for which repr(True)==str(True)=='True' — the quoting is invisible. Confirmed repr(True)='True', repr(0)='0', repr('abc')="'abc'". A faithful spec must pin Ensures(Implies(is_str, ToSeq(Result())==quote()+ToSeq(value)+quote())) or a non-quoting impl would verify yet fail the F2P — so faithful+non-leaking is provably impossible for the B1 facet. B2 (enumerated value stays plain text, not a class xref) is directly PS-derivable ('values like Literal[True] end up failing because True is not a class') and leaks nothing.

LEXICAL RE-SCAN of the spec view (model.py minus impl regions) beyond the dispositioned B1 facet: NO new leak found. The spec view names NO patched file (python.py: 0 hits), NO patched function (_parse_annotation/unparse: 0), NO real callee identifier (type_to_xref/nodes.literal/pending_xref/desc_sig_punctuation/ast.Constant: 0), quotes NO diff line, and narrates NO fix mechanism. The 9 'repr' matches are the English word 'representation' describing the (dispositioned) B1 quoting; 'typing' is only `from typing import List`; 'sphinx' is only the instance-id docstring title; 'Literal'/'subscript' are abstract modeling vocabulary (Literal also appears in the public problem_statement) expressed via integer KIND codes, never the real docutils/node types. The known dispositioned B1 facet (quote() helper, the is_str quoting postcondition, and docstring sentences B1) is re-confirmed and no leak beyond it exists.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `model.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.