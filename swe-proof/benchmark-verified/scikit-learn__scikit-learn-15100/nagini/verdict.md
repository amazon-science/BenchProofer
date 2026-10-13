# P2 adversarial audit — scikit-learn__scikit-learn-15100

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `model_ref.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,43 +129,30 @@
     Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))
     # post-conditions-end
     # impl-start
-    in_fixed_form = is_fixed_form_guard(s)
-    if in_fixed_form:
-        # Already-final-form input: canonically stable and mark-free, so its
-        # decomposition carries no combining marks and equals the input -- the
-        # fast path returns the input string unchanged (modelled as its
-        # code-point copy, str being immutable: returning s == returning a
-        # copy of s).
-        Assert(all_ascii(ToSeq(s)))
+    normalized = decompose(s)
+    if ToSeq(normalized) == ToSeq(s):
         out = []  # type: List[int]
         j = 0
         while j < len(s):
-            # invariants-start
             Invariant(Acc(list_pred(s), 1 / 2))
+            Invariant(Acc(list_pred(normalized)))
             Invariant(Acc(list_pred(out)))
             Invariant(0 <= j and j <= len(s))
-            Invariant(all_ascii(ToSeq(s)))
             Invariant(ToSeq(out) == ToSeq(s).take(j))
-            # invariants-end
             Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
             out = out + [s[j]]
             j = j + 1
         Assert(ToSeq(s).take(len(s)) == ToSeq(s))
-        Assert(all_ascii(ToSeq(s)))
-        lemma_ascii_is_fixed_point(ToSeq(s))
         return out
-    normalized = decompose(s)
     result = []  # type: List[int]
     i = len(normalized)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(s), 1 / 2))
         Invariant(Acc(list_pred(normalized)))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(normalized))
         Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
         Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
-        # invariants-end
         c = normalized[i - 1]
         Assert(ToSeq(normalized).drop(i - 1)[0] == c)
         Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,47 +129,17 @@
     Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))
     # post-conditions-end
     # impl-start
-    in_fixed_form = is_fixed_form_guard(s)
-    if in_fixed_form:
-        # Already-final-form input: canonically stable and mark-free, so its
-        # decomposition carries no combining marks and equals the input -- the
-        # fast path returns the input string unchanged (modelled as its
-        # code-point copy, str being immutable: returning s == returning a
-        # copy of s).
-        Assert(all_ascii(ToSeq(s)))
-        out = []  # type: List[int]
-        j = 0
-        while j < len(s):
-            # invariants-start
-            Invariant(Acc(list_pred(s), 1 / 2))
-            Invariant(Acc(list_pred(out)))
-            Invariant(0 <= j and j <= len(s))
-            Invariant(all_ascii(ToSeq(s)))
-            Invariant(ToSeq(out) == ToSeq(s).take(j))
-            # invariants-end
-            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
-            out = out + [s[j]]
-            j = j + 1
-        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
-        Assert(all_ascii(ToSeq(s)))
-        lemma_ascii_is_fixed_point(ToSeq(s))
-        return out
     normalized = decompose(s)
     result = []  # type: List[int]
     i = len(normalized)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(s), 1 / 2))
         Invariant(Acc(list_pred(normalized)))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(normalized))
         Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
-        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
-        # invariants-end
         c = normalized[i - 1]
-        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
-        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
-        if not is_combining(c):
+        if is_combining(c):
             result = [c] + result
         i = i - 1
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,46 +129,16 @@
     Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))
     # post-conditions-end
     # impl-start
-    in_fixed_form = is_fixed_form_guard(s)
-    if in_fixed_form:
-        # Already-final-form input: canonically stable and mark-free, so its
-        # decomposition carries no combining marks and equals the input -- the
-        # fast path returns the input string unchanged (modelled as its
-        # code-point copy, str being immutable: returning s == returning a
-        # copy of s).
-        Assert(all_ascii(ToSeq(s)))
-        out = []  # type: List[int]
-        j = 0
-        while j < len(s):
-            # invariants-start
-            Invariant(Acc(list_pred(s), 1 / 2))
-            Invariant(Acc(list_pred(out)))
-            Invariant(0 <= j and j <= len(s))
-            Invariant(all_ascii(ToSeq(s)))
-            Invariant(ToSeq(out) == ToSeq(s).take(j))
-            # invariants-end
-            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
-            out = out + [s[j]]
-            j = j + 1
-        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
-        Assert(all_ascii(ToSeq(s)))
-        lemma_ascii_is_fixed_point(ToSeq(s))
-        return out
     normalized = decompose(s)
     result = []  # type: List[int]
     i = len(normalized)
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(s), 1 / 2))
         Invariant(Acc(list_pred(normalized)))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(normalized))
+        Invariant(1 <= i and i <= len(normalized))
         Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
-        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
-        # invariants-end
         c = normalized[i - 1]
-        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
-        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
         if not is_combining(c):
             result = [c] + result
         i = i - 1
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,48 +129,6 @@
     Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))
     # post-conditions-end
     # impl-start
-    in_fixed_form = is_fixed_form_guard(s)
-    if in_fixed_form:
-        # Already-final-form input: canonically stable and mark-free, so its
-        # decomposition carries no combining marks and equals the input -- the
-        # fast path returns the input string unchanged (modelled as its
-        # code-point copy, str being immutable: returning s == returning a
-        # copy of s).
-        Assert(all_ascii(ToSeq(s)))
-        out = []  # type: List[int]
-        j = 0
-        while j < len(s):
-            # invariants-start
-            Invariant(Acc(list_pred(s), 1 / 2))
-            Invariant(Acc(list_pred(out)))
-            Invariant(0 <= j and j <= len(s))
-            Invariant(all_ascii(ToSeq(s)))
-            Invariant(ToSeq(out) == ToSeq(s).take(j))
-            # invariants-end
-            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
-            out = out + [s[j]]
-            j = j + 1
-        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
-        Assert(all_ascii(ToSeq(s)))
-        lemma_ascii_is_fixed_point(ToSeq(s))
-        return out
     normalized = decompose(s)
-    result = []  # type: List[int]
-    i = len(normalized)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(s), 1 / 2))
-        Invariant(Acc(list_pred(normalized)))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(normalized))
-        Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
-        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
-        # invariants-end
-        c = normalized[i - 1]
-        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
-        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
-        if not is_combining(c):
-            result = [c] + result
-        i = i - 1
-    return result
+    return normalized
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,48 +129,16 @@
     Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))
     # post-conditions-end
     # impl-start
-    in_fixed_form = is_fixed_form_guard(s)
-    if in_fixed_form:
-        # Already-final-form input: canonically stable and mark-free, so its
-        # decomposition carries no combining marks and equals the input -- the
-        # fast path returns the input string unchanged (modelled as its
-        # code-point copy, str being immutable: returning s == returning a
-        # copy of s).
-        Assert(all_ascii(ToSeq(s)))
-        out = []  # type: List[int]
-        j = 0
-        while j < len(s):
-            # invariants-start
-            Invariant(Acc(list_pred(s), 1 / 2))
-            Invariant(Acc(list_pred(out)))
-            Invariant(0 <= j and j <= len(s))
-            Invariant(all_ascii(ToSeq(s)))
-            Invariant(ToSeq(out) == ToSeq(s).take(j))
-            # invariants-end
-            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
-            out = out + [s[j]]
-            j = j + 1
-        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
-        Assert(all_ascii(ToSeq(s)))
-        lemma_ascii_is_fixed_point(ToSeq(s))
-        return out
-    normalized = decompose(s)
-    result = []  # type: List[int]
-    i = len(normalized)
-    while i > 0:
-        # invariants-start
+    out = []  # type: List[int]
+    j = 0
+    while j < len(s):
         Invariant(Acc(list_pred(s), 1 / 2))
-        Invariant(Acc(list_pred(normalized)))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(normalized))
-        Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
-        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
-        # invariants-end
-        c = normalized[i - 1]
-        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
-        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
-        if not is_combining(c):
-            result = [c] + result
-        i = i - 1
-    return result
+        Invariant(Acc(list_pred(out)))
+        Invariant(0 <= j and j <= len(s))
+        Invariant(ToSeq(out) == ToSeq(s).take(j))
+        Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
+        out = out + [s[j]]
+        j = j + 1
+    Assert(ToSeq(s).take(len(s)) == ToSeq(s))
+    return out
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,48 +129,6 @@
     Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))
     # post-conditions-end
     # impl-start
-    in_fixed_form = is_fixed_form_guard(s)
-    if in_fixed_form:
-        # Already-final-form input: canonically stable and mark-free, so its
-        # decomposition carries no combining marks and equals the input -- the
-        # fast path returns the input string unchanged (modelled as its
-        # code-point copy, str being immutable: returning s == returning a
-        # copy of s).
-        Assert(all_ascii(ToSeq(s)))
-        out = []  # type: List[int]
-        j = 0
-        while j < len(s):
-            # invariants-start
-            Invariant(Acc(list_pred(s), 1 / 2))
-            Invariant(Acc(list_pred(out)))
-            Invariant(0 <= j and j <= len(s))
-            Invariant(all_ascii(ToSeq(s)))
-            Invariant(ToSeq(out) == ToSeq(s).take(j))
-            # invariants-end
-            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
-            out = out + [s[j]]
-            j = j + 1
-        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
-        Assert(all_ascii(ToSeq(s)))
-        lemma_ascii_is_fixed_point(ToSeq(s))
-        return out
-    normalized = decompose(s)
     result = []  # type: List[int]
-    i = len(normalized)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(s), 1 / 2))
-        Invariant(Acc(list_pred(normalized)))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(normalized))
-        Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
-        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
-        # invariants-end
-        c = normalized[i - 1]
-        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
-        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
-        if not is_combining(c):
-            result = [c] + result
-        i = i - 1
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -129,48 +129,18 @@
     Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))
     # post-conditions-end
     # impl-start
-    in_fixed_form = is_fixed_form_guard(s)
-    if in_fixed_form:
-        # Already-final-form input: canonically stable and mark-free, so its
-        # decomposition carries no combining marks and equals the input -- the
-        # fast path returns the input string unchanged (modelled as its
-        # code-point copy, str being immutable: returning s == returning a
-        # copy of s).
-        Assert(all_ascii(ToSeq(s)))
-        out = []  # type: List[int]
-        j = 0
-        while j < len(s):
-            # invariants-start
-            Invariant(Acc(list_pred(s), 1 / 2))
-            Invariant(Acc(list_pred(out)))
-            Invariant(0 <= j and j <= len(s))
-            Invariant(all_ascii(ToSeq(s)))
-            Invariant(ToSeq(out) == ToSeq(s).take(j))
-            # invariants-end
-            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
-            out = out + [s[j]]
-            j = j + 1
-        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
-        Assert(all_ascii(ToSeq(s)))
-        lemma_ascii_is_fixed_point(ToSeq(s))
-        return out
     normalized = decompose(s)
     result = []  # type: List[int]
     i = len(normalized)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(s), 1 / 2))
         Invariant(Acc(list_pred(normalized)))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(normalized))
         Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
-        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
-        # invariants-end
         c = normalized[i - 1]
-        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
-        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
         if not is_combining(c):
-            result = [c] + result
+            result = result + [c]
         i = i - 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `model_ref.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-15100.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A text-normalisation routine maps an input string of Unicode code points to
  the string obtained by (1) decomposing it into its canonical decomposed form
  and then (2) dropping every combining mark. The result therefore contains no
  combining marks, regardless of the form the input arrived in: two inputs that
  are canonically equivalent (e.g. a precomposed accented letter and the same
  letter followed by a separate combining mark) yield the same output. In
  particular an input that is ALREADY in decomposed form but still carries
  combining marks must have those marks removed, not be returned untouched.

  When the input is provably already in final form (it carries no combining
  marks and is canonically stable), it may be returned unchanged via a
  behaviour-preserving fast path -- the same result the general transform
  would produce, not a different one.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]`.

Two unchanged library callees are axiomatized: the canonical decomposition
(`nfkd`, used to obtain the decomposed form) and the combining-mark classifier
(`is_combining`). The mark-dropping selection itself is the unchanged operation
and is modelled DEEPLY as a verified order-preserving filter (`strip_combining`)
over the decomposed code points. The axioms' soundness against the real callees
is checked out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def is_combining(c: int) -> bool:
    """Combining-mark classifier (the unchanged callee), as a pure predicate of
    a single code point: True iff the code point is a combining mark (a mark
    that attaches to a preceding base character). Weakest contract the proof
    needs: a code point below 128 is never a combining mark.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(c < 128, not Result()))

@Pure
@ContractOnly
def nfkd(s: PSeq[int]) -> PSeq[int]:
    """Canonical decomposition of a code-point sequence (the unchanged callee),
    as a pure function. Weakest contract the proof needs: a sequence consisting
    solely of code points below 128 is canonically stable, i.e. returned unchanged.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                                    s[k] < 128))),
                    Result() == s))

@ContractOnly
def decompose(s: List[int]) -> List[int]:
    """Runtime counterpart of `nfkd`: the actual decomposition call, returning
    the decomposed code points as a fresh list. Its observable content is
    `nfkd` of the input (the A-consumed axiom, same callee)."""
    Requires(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == nfkd(ToSeq(s)))

@ContractOnly
def is_fixed_form_guard(s: List[int]) -> bool:
    """Runtime guard for the unchanged-input fast path: returns whether `s` is
    provably already in its final form, so that returning it unchanged is
    behaviour-preserving. Its truth coincides with the structural property
    `all_ascii(s)` of the input carrier (see below)."""
    Requires(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Result() == all_ascii(ToSeq(s)))
# axioms-end

# pure-start
@Pure
def all_ascii(s: PSeq[int]) -> bool:
    """Every code point of the sequence is below 128."""
    return Forall(int, lambda k: (Implies(0 <= k and k < len(s), s[k] < 128)))

@Pure
def strip_combining(s: PSeq[int]) -> PSeq[int]:
    """The mark-dropping selection: the order-preserving sub-sequence of `s`
    obtained by removing every combining mark. Front-recursive so a single
    unfold is available per code point."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if is_combining(s[0]):
        return strip_combining(s.drop(1))
    return PSeq(s[0]) + strip_combining(s.drop(1))

def lemma_ascii_is_fixed_point(s: PSeq[int]) -> None:
    """Proof lemma: a sequence whose code points are all below 128 has no
    combining marks, so dropping combining marks leaves it unchanged. Proven by
    front-recursion; the inductive step uses the `is_combining` axiom
    (code point < 128 ⇒ not combining)."""
    Requires(all_ascii(s))
    Ensures(strip_combining(s) == s)
    if len(s) > 0:
        Assert(s[0] < 128)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(s.drop(1)),
                                               s.drop(1)[k] == s[k + 1]))))
        Assert(all_ascii(s.drop(1)))
        lemma_ascii_is_fixed_point(s.drop(1))
        Assert(PSeq(s[0]) + s.drop(1) == s)
# pure-end

def strip_marks(s: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the canonical decomposition of the input with every
    # combining mark removed -- independent of the form the input arrived in.
    Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))
    # post-conditions-end
    # impl-start
    in_fixed_form = is_fixed_form_guard(s)
    if in_fixed_form:
        # Already-final-form input: canonically stable and mark-free, so its
        # decomposition carries no combining marks and equals the input -- the
        # fast path returns the input string unchanged (modelled as its
        # code-point copy, str being immutable: returning s == returning a
        # copy of s).
        Assert(all_ascii(ToSeq(s)))
        out = []  # type: List[int]
        j = 0
        while j < len(s):
            # invariants-start
            Invariant(Acc(list_pred(s), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(s))
            Invariant(all_ascii(ToSeq(s)))
            Invariant(ToSeq(out) == ToSeq(s).take(j))
            # invariants-end
            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
            out = out + [s[j]]
            j = j + 1
        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
        Assert(all_ascii(ToSeq(s)))
        lemma_ascii_is_fixed_point(ToSeq(s))
        return out
    normalized = decompose(s)
    result = []  # type: List[int]
    i = len(normalized)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(Acc(list_pred(normalized)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(normalized))
        Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
        # invariants-end
        c = normalized[i - 1]
        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
        if not is_combining(c):
            result = [c] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for scikit-learn__scikit-learn-15100 nagini. Impl region (lines 132-175, between # impl-start/# impl-end) is the ONLY thing edited in every attack; axioms/@Pure/Requires/Ensures byte-identical.

POSITIVE CONTROL: bash scripts/nagini_verify.sh model_ref.py -> 'Verification successful' (13.61s), EXIT 0.

The postcondition Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s)))) fully pins the output to the grounded deep model strip_combining(nfkd(s)) -- no opaque oracle over Result(); a verifying impl must actually decompose then order-preservingly drop combining marks.

7 DISTINCT same-spec wrong impls, each run through `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-15100 <atk>` (weakness = same-spec AND verifies in one shot; exit 2 = not a counterexample). Runs done 3-at-a-time as background jobs. atk_1 (prepatch bug / partial-domain): re-introduces the removed guard `if ToSeq(normalized)==ToSeq(s): return copy(s)` -> weakness EXIT 2 (verification failed).

Reproduces the G-DIFF prepatch failure: on an already-decomposed input carrying combining marks (e.g. chr(110)+chr(771)) nfkd(s)==s so the guard fires and returns s, but strip_combining(s)!=s. prepatch_reproduced=true. atk_2 (boundary / test inversion): keeps c iff is_combining(c) (drops non-marks) -> EXIT 2. atk_3 (control-flow-effect / off-by-one): loop `while i>1` truncates index 0 -> EXIT 2. atk_4 (ungrounded-oracle echo): return decompose(s) without stripping marks -> EXIT 2. atk_5 (identity echo): copy-and-return input unconditionally -> EXIT 2. atk_6 (degenerate/partial): always return [] -> EXIT 2. atk_7 (order-corruption): backward walk but append kept elems (reverses order) -> EXIT 2. EVERY attack: `weakness` EXIT 2 => NOT-A-COUNTEREXAMPLE (attack does not verify) => the spec REJECTED it. same-spec confirmed EXIT 0 (SAME) for all 7 (atk_1,2,3,4,5,6,7). No attack came back a CANDIDATE, so there was NO verifying wrong-impl requiring a materialized faithful patch + run_resolve; patches={} accordingly (the resolve obligation is triggered only by a verifying candidate; none exists).

### REFINEMENT.MD A-LEG AUDIT (R/I legs deferred to G-CONF per instructions):
  - Leg 2 A-consumed is_fixed_form_guard <-> str.encode('ASCII','strict'): Ensures(Result()==all_ascii(ToSeq(s))) is a true equivalence to strict-ASCII encodability; G-AX (recorded pass) checks success<=>all(ord<128) on boundary+fuzz. Correspondence holds.
  - Legs 4/5 A-consumed nfkd/decompose <-> unicodedata.normalize('NFKD',.): weakest contract all_ascii(s)=>Result()==s is sound (NFKD is identity on 7-bit code points); decompose is the runtime carrier Ensures(ToSeq(Result())==nfkd(ToSeq(s))), same unchanged callee. Correspondence holds.
  - is_combining A-consumed <-> unicodedata.combining(c)!=0: weakest contract c<128=>not Result() sound (all 128 ASCII have class 0, checked exhaustively). Correspondence holds.
  - Legs 6/7 A-reference strip_combining deep model <-> comprehension [c for c in normalize(NFKD,s) if not combining(c)]: spelled out as @Pure front-recursive fold (NOT an axiom about the function under change); G-AX validates strip_combining(nfkd(s))==real transform over 25 boundary + 40000 fuzz, 0 mismatches, incl. F2P discriminators chr(110)+chr(771), 'o+diaeresis', combining-only strings. The postcondition is grounded in the input carrier s, not an opaque oracle -> no ungrounded echo can slip through (empirically confirmed by atk_4 EXIT 2).
  - NO kind-3 leg: the genuinely-changed op (the early-return guard) is modeled with the expressible predicate all_ascii backed by is_fixed_form_guard; the unchanged selection is modeled DEEPLY. Every leg is R / A-consumed / A-reference / I.

G-AX recorded pass (meta.json): exit 0, deep model sound on 25 boundary + 40000 fuzz. G-DIFF recorded pass (model_prepatch.py verification failed).

Verdict SOUND: 7 (>=5) distinct same-spec attacks run to completion (none timed out / INCONCLUSIVE), positive control verifies, prepatch reproduced, and no verifying wrong impl exists (so no resolve run could break the spec). The pinned deep-model postcondition + audited A-legs make verify => correct on this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `model_ref.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `model_ref.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-15100.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A text-normalisation routine maps an input string of Unicode code points to
  the string obtained by (1) decomposing it into its canonical decomposed form
  and then (2) dropping every combining mark. The result therefore contains no
  combining marks, regardless of the form the input arrived in: two inputs that
  are canonically equivalent (e.g. a precomposed accented letter and the same
  letter followed by a separate combining mark) yield the same output. In
  particular an input that is ALREADY in decomposed form but still carries
  combining marks must have those marks removed, not be returned untouched.

  When the input is provably already in final form (it carries no combining
  marks and is canonically stable), it may be returned unchanged via a
  behaviour-preserving fast path -- the same result the general transform
  would produce, not a different one.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]`.

Two unchanged library callees are axiomatized: the canonical decomposition
(`nfkd`, used to obtain the decomposed form) and the combining-mark classifier
(`is_combining`). The mark-dropping selection itself is the unchanged operation
and is modelled DEEPLY as a verified order-preserving filter (`strip_combining`)
over the decomposed code points. The axioms' soundness against the real callees
is checked out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def is_combining(c: int) -> bool:
    """Combining-mark classifier (the unchanged callee), as a pure predicate of
    a single code point: True iff the code point is a combining mark (a mark
    that attaches to a preceding base character). Weakest contract the proof
    needs: a code point below 128 is never a combining mark.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(c < 128, not Result()))

@Pure
@ContractOnly
def nfkd(s: PSeq[int]) -> PSeq[int]:
    """Canonical decomposition of a code-point sequence (the unchanged callee),
    as a pure function. Weakest contract the proof needs: a sequence consisting
    solely of code points below 128 is canonically stable, i.e. returned unchanged.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                                    s[k] < 128))),
                    Result() == s))

@ContractOnly
def decompose(s: List[int]) -> List[int]:
    """Runtime counterpart of `nfkd`: the actual decomposition call, returning
    the decomposed code points as a fresh list. Its observable content is
    `nfkd` of the input (the A-consumed axiom, same callee)."""
    Requires(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == nfkd(ToSeq(s)))

@ContractOnly
def is_fixed_form_guard(s: List[int]) -> bool:
    """Runtime guard for the unchanged-input fast path: returns whether `s` is
    provably already in its final form, so that returning it unchanged is
    behaviour-preserving. Its truth coincides with the structural property
    `all_ascii(s)` of the input carrier (see below)."""
    Requires(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Result() == all_ascii(ToSeq(s)))
# axioms-end

# pure-start
@Pure
def all_ascii(s: PSeq[int]) -> bool:
    """Every code point of the sequence is below 128."""
    return Forall(int, lambda k: (Implies(0 <= k and k < len(s), s[k] < 128)))

@Pure
def strip_combining(s: PSeq[int]) -> PSeq[int]:
    """The mark-dropping selection: the order-preserving sub-sequence of `s`
    obtained by removing every combining mark. Front-recursive so a single
    unfold is available per code point."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if is_combining(s[0]):
        return strip_combining(s.drop(1))
    return PSeq(s[0]) + strip_combining(s.drop(1))

def lemma_ascii_is_fixed_point(s: PSeq[int]) -> None:
    """Proof lemma: a sequence whose code points are all below 128 has no
    combining marks, so dropping combining marks leaves it unchanged. Proven by
    front-recursion; the inductive step uses the `is_combining` axiom
    (code point < 128 ⇒ not combining)."""
    Requires(all_ascii(s))
    Ensures(strip_combining(s) == s)
    if len(s) > 0:
        Assert(s[0] < 128)
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(s.drop(1)),
                                               s.drop(1)[k] == s[k + 1]))))
        Assert(all_ascii(s.drop(1)))
        lemma_ascii_is_fixed_point(s.drop(1))
        Assert(PSeq(s[0]) + s.drop(1) == s)
# pure-end

def strip_marks(s: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(s), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(s), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the canonical decomposition of the input with every
    # combining mark removed -- independent of the form the input arrived in.
    Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))))
    # post-conditions-end
    # impl-start
    in_fixed_form = is_fixed_form_guard(s)
    if in_fixed_form:
        # Already-final-form input: canonically stable and mark-free, so its
        # decomposition carries no combining marks and equals the input -- the
        # fast path returns the input string unchanged (modelled as its
        # code-point copy, str being immutable: returning s == returning a
        # copy of s).
        Assert(all_ascii(ToSeq(s)))
        out = []  # type: List[int]
        j = 0
        while j < len(s):
            # invariants-start
            Invariant(Acc(list_pred(s), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(s))
            Invariant(all_ascii(ToSeq(s)))
            Invariant(ToSeq(out) == ToSeq(s).take(j))
            # invariants-end
            Assert(ToSeq(s).take(j + 1) == ToSeq(s).take(j) + PSeq(s[j]))
            out = out + [s[j]]
            j = j + 1
        Assert(ToSeq(s).take(len(s)) == ToSeq(s))
        Assert(all_ascii(ToSeq(s)))
        lemma_ascii_is_fixed_point(ToSeq(s))
        return out
    normalized = decompose(s)
    result = []  # type: List[int]
    i = len(normalized)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(s), 1 / 2))
        Invariant(Acc(list_pred(normalized)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(normalized))
        Invariant(ToSeq(normalized) == nfkd(ToSeq(s)))
        Invariant(ToSeq(result) == strip_combining(ToSeq(normalized).drop(i)))
        # invariants-end
        c = normalized[i - 1]
        Assert(ToSeq(normalized).drop(i - 1)[0] == c)
        Assert(ToSeq(normalized).drop(i - 1).drop(1) == ToSeq(normalized).drop(i))
        if not is_combining(c):
            result = [c] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) for scikit-learn__scikit-learn-15100 nagini. Impl region (lines 132-175, between # impl-start/# impl-end) is the ONLY thing edited in every attack; axioms/@Pure/Requires/Ensures byte-identical.

POSITIVE CONTROL: bash scripts/nagini_verify.sh model_ref.py -> 'Verification successful' (13.61s), EXIT 0.

The postcondition Ensures(ToSeq(Result()) == strip_combining(nfkd(ToSeq(s)))) fully pins the output to the grounded deep model strip_combining(nfkd(s)) -- no opaque oracle over Result(); a verifying impl must actually decompose then order-preservingly drop combining marks.

7 DISTINCT same-spec wrong impls, each run through `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-15100 <atk>` (weakness = same-spec AND verifies in one shot; exit 2 = not a counterexample). Runs done 3-at-a-time as background jobs. atk_1 (prepatch bug / partial-domain): re-introduces the removed guard `if ToSeq(normalized)==ToSeq(s): return copy(s)` -> weakness EXIT 2 (verification failed).

Reproduces the G-DIFF prepatch failure: on an already-decomposed input carrying combining marks (e.g. chr(110)+chr(771)) nfkd(s)==s so the guard fires and returns s, but strip_combining(s)!=s. prepatch_reproduced=true. atk_2 (boundary / test inversion): keeps c iff is_combining(c) (drops non-marks) -> EXIT 2. atk_3 (control-flow-effect / off-by-one): loop `while i>1` truncates index 0 -> EXIT 2. atk_4 (ungrounded-oracle echo): return decompose(s) without stripping marks -> EXIT 2. atk_5 (identity echo): copy-and-return input unconditionally -> EXIT 2. atk_6 (degenerate/partial): always return [] -> EXIT 2. atk_7 (order-corruption): backward walk but append kept elems (reverses order) -> EXIT 2. EVERY attack: `weakness` EXIT 2 => NOT-A-COUNTEREXAMPLE (attack does not verify) => the spec REJECTED it. same-spec confirmed EXIT 0 (SAME) for all 7 (atk_1,2,3,4,5,6,7). No attack came back a CANDIDATE, so there was NO verifying wrong-impl requiring a materialized faithful patch + run_resolve; patches={} accordingly (the resolve obligation is triggered only by a verifying candidate; none exists).

### REFINEMENT.MD A-LEG AUDIT (R/I legs deferred to G-CONF per instructions):
  - Leg 2 A-consumed is_fixed_form_guard <-> str.encode('ASCII','strict'): Ensures(Result()==all_ascii(ToSeq(s))) is a true equivalence to strict-ASCII encodability; G-AX (recorded pass) checks success<=>all(ord<128) on boundary+fuzz. Correspondence holds.
  - Legs 4/5 A-consumed nfkd/decompose <-> unicodedata.normalize('NFKD',.): weakest contract all_ascii(s)=>Result()==s is sound (NFKD is identity on 7-bit code points); decompose is the runtime carrier Ensures(ToSeq(Result())==nfkd(ToSeq(s))), same unchanged callee. Correspondence holds.
  - is_combining A-consumed <-> unicodedata.combining(c)!=0: weakest contract c<128=>not Result() sound (all 128 ASCII have class 0, checked exhaustively). Correspondence holds.
  - Legs 6/7 A-reference strip_combining deep model <-> comprehension [c for c in normalize(NFKD,s) if not combining(c)]: spelled out as @Pure front-recursive fold (NOT an axiom about the function under change); G-AX validates strip_combining(nfkd(s))==real transform over 25 boundary + 40000 fuzz, 0 mismatches, incl. F2P discriminators chr(110)+chr(771), 'o+diaeresis', combining-only strings. The postcondition is grounded in the input carrier s, not an opaque oracle -> no ungrounded echo can slip through (empirically confirmed by atk_4 EXIT 2).
  - NO kind-3 leg: the genuinely-changed op (the early-return guard) is modeled with the expressible predicate all_ascii backed by is_fixed_form_guard; the unchanged selection is modeled DEEPLY. Every leg is R / A-consumed / A-reference / I.

G-AX recorded pass (meta.json): exit 0, deep model sound on 25 boundary + 40000 fuzz. G-DIFF recorded pass (model_prepatch.py verification failed).

Verdict SOUND: 7 (>=5) distinct same-spec attacks run to completion (none timed out / INCONCLUSIVE), positive control verifies, prepatch reproduced, and no verifying wrong impl exists (so no resolve run could break the spec). The pinned deep-model postcondition + audited A-legs make verify => correct on this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift check for the modeled strip_marks vs the real repo callee strip_accents_unicode (sklearn/feature_extraction/text.py, post-patch gold).

Spec region: byte-identical (same-spec toolkit returns SAME, exit 0). Model verifies under pinned Nagini (Verification successful, 14.14s).

The spec postcondition is `ToSeq(Result()) == strip_combining(nfkd(ToSeq(s)))`, i.e. Result = NFKD-decompose then drop every combining mark, UNCONDITIONALLY (independent of arrival form). I compared this modeled function against the real gold callee

  def strip_accents_unicode(s):
      try:
          s.encode('ASCII', errors='strict'); return s
      except UnicodeEncodeError:
          normalized = unicodedata.normalize('NFKD', s)
          return ''.join([c for c in normalized if not unicodedata.combining(c)])

over: (a) EVERY single code point chr(c) for c in 0..0x11000, and (b) 300,000 random fuzz strings drawn from an alphabet rich in combining marks (0x300-0x370), Latin-1/Greek/Cyrillic precomposed accents (0x80-0x600), and Latin-extended-additional (0x1E00+). Result: 0 mismatches.

The key point: on the gold's ASCII fast-path (`return s`) the input is pure-ASCII => NFKD is identity and there are no combining marks => strip_combining(nfkd(s)) == s, so the spec agrees. On non-ASCII the gold takes the except branch which is literally strip_combining(nfkd(s)). Thus spec == gold on all inputs; the spec does NOT over-strengthen or drift. It correctly captures the already-decomposed-with-combining-marks case (e.g. chr(110)+chr(771)) which the prepatch guard got wrong — that is a genuine behavior the gold fixes, not spec drift.

The axioms consumed are the weakest sufficient contracts (nfkd identity on ASCII; is_combining false below 128; encode-guard == all_ascii), all G-AX-checked against real stdlib. No input found where the modeled function disagrees with the real callee.

Verdict: FAITHFUL — no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: G-LEAK/G-PANEL-3 is judged over the screened SPEC VIEW of model.py (mapping.md and refinement.md are auditor docs, not part of the consumer view). Ran leakage.screen(model.py spec_view, nagini, gold_patch, problem_statement): PASSED with zero hard failures. No relaxed_leakage flag / RELAXED_LEAKAGE.md; spec region is byte-identical with model_prepatch.py (same_spec=True), so the guard change is not encoded in the frozen spec.

Gold edit: the early-return guard in strip_accents_unicode changes from `if normalized == s: return s` (NFKD-equality) to a strict-ASCII encodability test (`try: s.encode('ASCII', errors='strict'); return s / except UnicodeEncodeError: normalize+strip`). Distinctive gold content = 'use strict-ASCII encodability as the fast-path guard'.

Public problem_statement already discloses: the bug, the desired output (s1=chr(241) and s2=chr(110)+chr(771) both -> 'n'), the exact F2P discriminator s2=chr(110)+chr(771), and the words 'combining'/'nfkd'/'normalize'. It does NOT contain 'ascii', 'encode', '128', or 'below' (verified).

Semantic check of what the spec view adds beyond the problem statement:
- The constraining spec is the behavioral postcondition ToSeq(Result()) == strip_combining(nfkd(ToSeq(s))) — desired behaviour, form-independent, not the edit. Any impl (e.g. plain decompose+strip with no fast path) verifies against it; the ASCII fast path is OPTIONAL and the impl region is fully elided, so the spec does not compel gold reconstruction.
- The one item beyond the problem statement is the modeled guard axiom is_fixed_form_guard -> Result()==all_ascii(ToSeq(s)) (all_ascii = code point < 128). This reveals that the AVAILABLE guard is ASCII-based — a concept absent from the problem statement. However: (a) it is an abstractly-contracted modeled callee (docstrings say 'provably already in its final form / canonically stable', behavioural not editorial), (b) modeling a guard-change bug inherently requires modeling the guard — this is the unavoidable twin-artifact artifact, not a reproduction/narration of the gold, (c) it is offered as an optional fast path, not forced by the postcondition. This does not rise to leakage of the gold edit.

Lexical checks all clean: no verbatim gold line, no diff markers, no patched file/module path, no spec-view identifier echoing a patched repo symbol (the changed symbol strip_accents_unicode is not echoed; model uses strip_marks), no bug/fix narration in comments. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.