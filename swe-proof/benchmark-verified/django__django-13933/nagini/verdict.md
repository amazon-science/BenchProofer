# P2 adversarial audit — django__django-13933

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,18 @@
     Ensures(ToSeq(Result()) == interpolated(ToSeq(template), ToSeq(value)))
     # post-conditions-end
     # impl-start
-    return _render(ToSeq(template), value, 0)
+    result = []  # type: List[int]
+    k = len(template)
+    while k > 0:
+        Invariant(Acc(list_pred(template), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= k and k <= len(template))
+        Invariant(ToSeq(result) == ToSeq(template).drop(k))
+        c = template[k - 1]
+        Assert(ToSeq(template).drop(k - 1) == PSeq(c) + ToSeq(template).drop(k))
+        result = [c] + result
+        k = k - 1
+    return result
     # impl-end
 
 
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,18 @@
     Ensures(ToSeq(Result()) == interpolated(ToSeq(template), ToSeq(value)))
     # post-conditions-end
     # impl-start
-    return _render(ToSeq(template), value, 0)
+    result = []  # type: List[int]
+    k = len(value)
+    while k > 0:
+        Invariant(Acc(list_pred(value), 1 / 2))
+        Invariant(Acc(list_pred(result)))
+        Invariant(0 <= k and k <= len(value))
+        Invariant(ToSeq(result) == ToSeq(value).drop(k))
+        c = value[k - 1]
+        Assert(ToSeq(value).drop(k - 1) == PSeq(c) + ToSeq(value).drop(k))
+        result = [c] + result
+        k = k - 1
+    return result
     # impl-end
 
 
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,8 @@
     Ensures(ToSeq(Result()) == interpolated(ToSeq(template), ToSeq(value)))
     # post-conditions-end
     # impl-start
-    return _render(ToSeq(template), value, 0)
+    result = []  # type: List[int]
+    return result
     # impl-end
 
 
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,11 +98,11 @@
     if i == n:
         Assert(len(ts.drop(i)) == 0)
         return result
-    if i + 9 <= n and ts.drop(i).take(9) == placeholder():
+    if i + 8 <= n and ts.drop(i).take(9) == placeholder():
         Assert(starts_with_placeholder(ts.drop(i)))
-        Assert(ts.drop(i).drop(9) == ts.drop(i + 9))
-        result = _render(ts, value, i + 9)
-        Assert(ToSeq(result) == interpolated(ts.drop(i + 9), ToSeq(value)))
+        Assert(ts.drop(i).drop(9) == ts.drop(i + 8))
+        result = _render(ts, value, i + 8)
+        Assert(ToSeq(result) == interpolated(ts.drop(i + 8), ToSeq(value)))
         # Prepend the rejected value, element by element from its end.
         j = len(value)
         while j > 0:
@@ -111,7 +111,7 @@
             Invariant(Acc(list_pred(result)))
             Invariant(0 <= j and j <= len(value))
             Invariant(ToSeq(result) == ToSeq(value).drop(j)
-                      + interpolated(ts.drop(i + 9), ToSeq(value)))
+                      + interpolated(ts.drop(i + 8), ToSeq(value)))
             # invariants-end
             vj = value[j - 1]
             result = [vj] + result
@@ -119,9 +119,9 @@
             j = j - 1
         Assert(ToSeq(value).drop(0) == ToSeq(value))
         Assert(starts_with_placeholder(ts.drop(i)))
-        Assert(ts.drop(i).drop(9) == ts.drop(i + 9))
+        Assert(ts.drop(i).drop(9) == ts.drop(i + 8))
         Assert(interpolated(ts.drop(i), ToSeq(value))
-               == ToSeq(value) + interpolated(ts.drop(i + 9), ToSeq(value)))
+               == ToSeq(value) + interpolated(ts.drop(i + 8), ToSeq(value)))
         return result
     Assert(not starts_with_placeholder(ts.drop(i)))
     Assert(len(ts.drop(i)) >= 1)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -120,6 +120,14 @@
         Assert(ToSeq(value).drop(0) == ToSeq(value))
         Assert(starts_with_placeholder(ts.drop(i)))
         Assert(ts.drop(i).drop(9) == ts.drop(i + 9))
+        j2 = len(value)
+        while j2 > 0:
+            Invariant(Acc(list_pred(value), 1 / 8))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= j2 and j2 <= len(value))
+            vj2 = value[j2 - 1]
+            result = [vj2] + result
+            j2 = j2 - 1
         Assert(interpolated(ts.drop(i), ToSeq(value))
                == ToSeq(value) + interpolated(ts.drop(i + 9), ToSeq(value)))
         return result
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -128,7 +128,7 @@
     head = ts[i]
     Assert(ts.drop(i).take(1) == PSeq(head))
     Assert(ts.drop(i).drop(1) == ts.drop(i + 1))
-    result = _render(ts, value, i + 1)
+    result = _render(ts, value, i + 2)
     result = [head] + result
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13933.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a single-object choice field rejects a submitted value that is not an
  available choice, the human-readable error it produces is derived from a
  configurable message template by interpolating the offending value into the
  template's named placeholder. The placeholder is the literal token
  ``%(value)s``. Interpolation replaces EVERY occurrence of that token by the
  string form of the rejected value; all other characters of the template pass
  through unchanged. A template that contains no placeholder is therefore
  rendered verbatim, while a template that contains the placeholder renders
  with the rejected value visible in its place (rather than the literal
  placeholder text surviving into the message shown to the user).

Strings (the message template, the rejected value, and the rendered message)
are modelled as ``List[int]`` of Unicode code points (Nagini bans ``str``
indexing). The pure sequence theory ``PSeq[int]`` carries the specification.

The named-mapping ``%``-interpolation performed by the message machinery is
modelled DEEPLY as a verified front-recursive substitution fold
(``interpolated``); its equality to the real ``str.__mod__`` named mapping is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom. There
are no consumed axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms: the interpolation is modelled deeply in the pure region
#  and validated against the real str %-mapping by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def placeholder() -> PSeq[int]:
    """The named placeholder token, ``%(value)s``, as code points."""
    # '%' '(' 'v' 'a' 'l' 'u' 'e' ')' 's'
    return PSeq(37, 40, 118, 97, 108, 117, 101, 41, 115)


@Pure
def starts_with_placeholder(s: PSeq[int]) -> bool:
    """True iff ``s`` begins with the ``%(value)s`` token."""
    return len(s) >= 9 and s.take(9) == placeholder()


@Pure
def interpolated(template: PSeq[int], value: PSeq[int]) -> PSeq[int]:
    """Named-mapping interpolation of ``value`` into ``template``: every
    occurrence of the ``%(value)s`` token is replaced by ``value``; every other
    code point passes through. Front-recursive so a single unfold is available
    to callers per processed token/character."""
    if len(template) == 0:
        return template
    if starts_with_placeholder(template):
        return value + interpolated(template.drop(9), value)
    return template.take(1) + interpolated(template.drop(1), value)
# pure-end


def render_invalid_choice(template: List[int], value: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(template), 1 / 2))
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(template), 1 / 2))
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered message is the named-mapping interpolation of the rejected
    # value into the template: every %(value)s token becomes the value, all
    # other code points pass through unchanged.
    Ensures(ToSeq(Result()) == interpolated(ToSeq(template), ToSeq(value)))
    # post-conditions-end
    # impl-start
    return _render(ToSeq(template), value, 0)
    # impl-end


def _render(ts: PSeq[int], value: List[int], i: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 4))
    Requires(0 <= i and i <= len(ts))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == interpolated(ts.drop(i), ToSeq(value)))
    # post-conditions-end
    # impl-start
    n = len(ts)
    result = []  # type: List[int]
    if i == n:
        Assert(len(ts.drop(i)) == 0)
        return result
    if i + 9 <= n and ts.drop(i).take(9) == placeholder():
        Assert(starts_with_placeholder(ts.drop(i)))
        Assert(ts.drop(i).drop(9) == ts.drop(i + 9))
        result = _render(ts, value, i + 9)
        Assert(ToSeq(result) == interpolated(ts.drop(i + 9), ToSeq(value)))
        # Prepend the rejected value, element by element from its end.
        j = len(value)
        while j > 0:
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 8))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(value))
            Invariant(ToSeq(result) == ToSeq(value).drop(j)
                      + interpolated(ts.drop(i + 9), ToSeq(value)))
            # invariants-end
            vj = value[j - 1]
            result = [vj] + result
            Assert(ToSeq(value).drop(j - 1) == PSeq(vj) + ToSeq(value).drop(j))
            j = j - 1
        Assert(ToSeq(value).drop(0) == ToSeq(value))
        Assert(starts_with_placeholder(ts.drop(i)))
        Assert(ts.drop(i).drop(9) == ts.drop(i + 9))
        Assert(interpolated(ts.drop(i), ToSeq(value))
               == ToSeq(value) + interpolated(ts.drop(i + 9), ToSeq(value)))
        return result
    Assert(not starts_with_placeholder(ts.drop(i)))
    Assert(len(ts.drop(i)) >= 1)
    head = ts[i]
    Assert(ts.drop(i).take(1) == PSeq(head))
    Assert(ts.drop(i).drop(1) == ts.drop(i + 1))
    result = _render(ts, value, i + 1)
    result = [head] + result
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle django__django-13933 (nagini). Spec structure: render_invalid_choice and its proof carrier _render both carry a TIGHT UNCONDITIONAL functional postcondition Ensures(ToSeq(Result()) == interpolated(ToSeq(template), ToSeq(value))). `interpolated` is a total, terminating @Pure front-recursive substitution fold (every %(value)s token -> value, else passthrough). Because the postcondition pins the entire output sequence for every input and the fold is total, any impl that verifies MUST compute exactly interpolated(template,value) — this structurally forecloses partial-domain / boundary / weakening tricks. There is NO consumed axiom (empty axioms region); the interpolation is modeled deeply and validated as an A-reference by G-AX.

Same-spec: all 6 attacks + positive control are byte-identical in spec signature (adversary same-spec => SAME for each). Attacks edit ONLY impl regions.

atk_1 PREPATCH verbatim-copy (returns template unchanged, no interpolation) -> NOT-A-COUNTEREXAMPLE, verification failed, EXIT=2 (this IS the prepatch bug reproduced; prepatch_reproduced=true).
atk_2 ungrounded-oracle echo (returns a copy of `value`, ignores template) -> verification failed, EXIT=2.
atk_3 control-flow-effect (returns empty list, never builds output) -> verification failed, EXIT=2.
atk_4 boundary/off-by-one (_render consumes 8 code points for the %(value)s token instead of 9) -> verification failed, EXIT=2.
atk_5 duplication (prepend value TWICE on each token) -> verification failed, EXIT=2.
atk_6 char-skip control-flow (non-placeholder tail recursion advances i+2, dropping a code point) -> verification failed, EXIT=2.
Every wrong impl was REJECTED by the spec (none verifies). Positive control pos_control.py (gold impl verbatim) VERIFIED in 17.1s (adversary verify, EXIT=0).

Zero CANDIDATE counterexamples (no impl shares-spec-AND-verifies except the correct one), therefore NO faithful refined patch needed materializing/run_resolve — verify=>correct is not breakable here. patches={}.

A-leg / model<->patch correspondence audit (the focus, R/I legs mechanically covered by G-CONF):
  - A1/A2 = R (str <-> List[int] code points; str(value) identity on F2P str input). Covered by conformance_check.py (G-CONF) shadow==oracle on real patched ModelChoiceField.to_python path.
  - A3 = A-reference: `interpolated` deep model validated == real `template % {'value': value}` by axiom_check.py (G-AX). Ran G-AX: 'G-AX OK ... 143 boundary + 40000 fuzz inputs; no consumed axioms', AX_EXIT=0. Independent adversarial cross-check (aref_probe.py) confirmed correspondence on the actual Django invalid_choice literals, back-to-back tokens %(value)s%(value)s, trailing near-token %(value)s(value)s, and pre/post embedding; the only divergence (bare '%' as in '%(value)') is CORRECTLY outside the declared domain (real % raises ValueError), and Django's invalid_choice templates contain only the %(value)s construct, so the model domain is exactly the relevant one — the domain restriction is sound, not spec-weakening.
  - B1 = I (internal proof carrier _render; no repo symbol; realizes interpolated constructively).
  - refinement.md §C: every leg is R / A-reference / I; NO kind-3 step, NO A-consumed, empty axioms region — audited and consistent. The one observably-changed operation (interpolating the value) lives in A3's postcondition, which the prepatch (atk_1) provably fails. Correspondence to the real callee str.__mod__ named mapping holds.

Verdict SOUND: >=5 distinct verifying-rejected attacks run (6), positive control verifies, prepatch bug reproduced and rejected by the spec, A-reference validated by G-AX + independent probe, refinement legs clean. No verifying wrong impl exists, so verify=>resolve holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13933.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a single-object choice field rejects a submitted value that is not an
  available choice, the human-readable error it produces is derived from a
  configurable message template by interpolating the offending value into the
  template's named placeholder. The placeholder is the literal token
  ``%(value)s``. Interpolation replaces EVERY occurrence of that token by the
  string form of the rejected value; all other characters of the template pass
  through unchanged. A template that contains no placeholder is therefore
  rendered verbatim, while a template that contains the placeholder renders
  with the rejected value visible in its place (rather than the literal
  placeholder text surviving into the message shown to the user).

Strings (the message template, the rejected value, and the rendered message)
are modelled as ``List[int]`` of Unicode code points (Nagini bans ``str``
indexing). The pure sequence theory ``PSeq[int]`` carries the specification.

The named-mapping ``%``-interpolation performed by the message machinery is
modelled DEEPLY as a verified front-recursive substitution fold
(``interpolated``); its equality to the real ``str.__mod__`` named mapping is
checked out-of-band by axiom_check.py (G-AX), not consumed as an axiom. There
are no consumed axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no consumed axioms: the interpolation is modelled deeply in the pure region
#  and validated against the real str %-mapping by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def placeholder() -> PSeq[int]:
    """The named placeholder token, ``%(value)s``, as code points."""
    # '%' '(' 'v' 'a' 'l' 'u' 'e' ')' 's'
    return PSeq(37, 40, 118, 97, 108, 117, 101, 41, 115)


@Pure
def starts_with_placeholder(s: PSeq[int]) -> bool:
    """True iff ``s`` begins with the ``%(value)s`` token."""
    return len(s) >= 9 and s.take(9) == placeholder()


@Pure
def interpolated(template: PSeq[int], value: PSeq[int]) -> PSeq[int]:
    """Named-mapping interpolation of ``value`` into ``template``: every
    occurrence of the ``%(value)s`` token is replaced by ``value``; every other
    code point passes through. Front-recursive so a single unfold is available
    to callers per processed token/character."""
    if len(template) == 0:
        return template
    if starts_with_placeholder(template):
        return value + interpolated(template.drop(9), value)
    return template.take(1) + interpolated(template.drop(1), value)
# pure-end


def render_invalid_choice(template: List[int], value: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(template), 1 / 2))
    Requires(Acc(list_pred(value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(template), 1 / 2))
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered message is the named-mapping interpolation of the rejected
    # value into the template: every %(value)s token becomes the value, all
    # other code points pass through unchanged.
    Ensures(ToSeq(Result()) == interpolated(ToSeq(template), ToSeq(value)))
    # post-conditions-end
    # impl-start
    return _render(ToSeq(template), value, 0)
    # impl-end


def _render(ts: PSeq[int], value: List[int], i: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 4))
    Requires(0 <= i and i <= len(ts))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == interpolated(ts.drop(i), ToSeq(value)))
    # post-conditions-end
    # impl-start
    n = len(ts)
    result = []  # type: List[int]
    if i == n:
        Assert(len(ts.drop(i)) == 0)
        return result
    if i + 9 <= n and ts.drop(i).take(9) == placeholder():
        Assert(starts_with_placeholder(ts.drop(i)))
        Assert(ts.drop(i).drop(9) == ts.drop(i + 9))
        result = _render(ts, value, i + 9)
        Assert(ToSeq(result) == interpolated(ts.drop(i + 9), ToSeq(value)))
        # Prepend the rejected value, element by element from its end.
        j = len(value)
        while j > 0:
            # invariants-start
            Invariant(Acc(list_pred(value), 1 / 8))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(value))
            Invariant(ToSeq(result) == ToSeq(value).drop(j)
                      + interpolated(ts.drop(i + 9), ToSeq(value)))
            # invariants-end
            vj = value[j - 1]
            result = [vj] + result
            Assert(ToSeq(value).drop(j - 1) == PSeq(vj) + ToSeq(value).drop(j))
            j = j - 1
        Assert(ToSeq(value).drop(0) == ToSeq(value))
        Assert(starts_with_placeholder(ts.drop(i)))
        Assert(ts.drop(i).drop(9) == ts.drop(i + 9))
        Assert(interpolated(ts.drop(i), ToSeq(value))
               == ToSeq(value) + interpolated(ts.drop(i + 9), ToSeq(value)))
        return result
    Assert(not starts_with_placeholder(ts.drop(i)))
    Assert(len(ts.drop(i)) >= 1)
    head = ts[i]
    Assert(ts.drop(i).take(1) == PSeq(head))
    Assert(ts.drop(i).drop(1) == ts.drop(i + 1))
    result = _render(ts, value, i + 1)
    result = [head] + result
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Bundle django__django-13933 (nagini). Spec structure: render_invalid_choice and its proof carrier _render both carry a TIGHT UNCONDITIONAL functional postcondition Ensures(ToSeq(Result()) == interpolated(ToSeq(template), ToSeq(value))). `interpolated` is a total, terminating @Pure front-recursive substitution fold (every %(value)s token -> value, else passthrough). Because the postcondition pins the entire output sequence for every input and the fold is total, any impl that verifies MUST compute exactly interpolated(template,value) — this structurally forecloses partial-domain / boundary / weakening tricks. There is NO consumed axiom (empty axioms region); the interpolation is modeled deeply and validated as an A-reference by G-AX.

Same-spec: all 6 attacks + positive control are byte-identical in spec signature (adversary same-spec => SAME for each). Attacks edit ONLY impl regions.

atk_1 PREPATCH verbatim-copy (returns template unchanged, no interpolation) -> NOT-A-COUNTEREXAMPLE, verification failed, EXIT=2 (this IS the prepatch bug reproduced; prepatch_reproduced=true).
atk_2 ungrounded-oracle echo (returns a copy of `value`, ignores template) -> verification failed, EXIT=2.
atk_3 control-flow-effect (returns empty list, never builds output) -> verification failed, EXIT=2.
atk_4 boundary/off-by-one (_render consumes 8 code points for the %(value)s token instead of 9) -> verification failed, EXIT=2.
atk_5 duplication (prepend value TWICE on each token) -> verification failed, EXIT=2.
atk_6 char-skip control-flow (non-placeholder tail recursion advances i+2, dropping a code point) -> verification failed, EXIT=2.
Every wrong impl was REJECTED by the spec (none verifies). Positive control pos_control.py (gold impl verbatim) VERIFIED in 17.1s (adversary verify, EXIT=0).

Zero CANDIDATE counterexamples (no impl shares-spec-AND-verifies except the correct one), therefore NO faithful refined patch needed materializing/run_resolve — verify=>correct is not breakable here. patches={}.

A-leg / model<->patch correspondence audit (the focus, R/I legs mechanically covered by G-CONF):
  - A1/A2 = R (str <-> List[int] code points; str(value) identity on F2P str input). Covered by conformance_check.py (G-CONF) shadow==oracle on real patched ModelChoiceField.to_python path.
  - A3 = A-reference: `interpolated` deep model validated == real `template % {'value': value}` by axiom_check.py (G-AX). Ran G-AX: 'G-AX OK ... 143 boundary + 40000 fuzz inputs; no consumed axioms', AX_EXIT=0. Independent adversarial cross-check (aref_probe.py) confirmed correspondence on the actual Django invalid_choice literals, back-to-back tokens %(value)s%(value)s, trailing near-token %(value)s(value)s, and pre/post embedding; the only divergence (bare '%' as in '%(value)') is CORRECTLY outside the declared domain (real % raises ValueError), and Django's invalid_choice templates contain only the %(value)s construct, so the model domain is exactly the relevant one — the domain restriction is sound, not spec-weakening.
  - B1 = I (internal proof carrier _render; no repo symbol; realizes interpolated constructively).
  - refinement.md §C: every leg is R / A-reference / I; NO kind-3 step, NO A-consumed, empty axioms region — audited and consistent. The one observably-changed operation (interpolating the value) lives in A3's postcondition, which the prepatch (atk_1) provably fails. Correspondence to the real callee str.__mod__ named mapping holds.

Verdict SOUND: >=5 distinct verifying-rejected attacks run (6), positive control verifies, prepatch bug reproduced and rejected by the spec, A-reference validated by G-AX + independent probe, refinement legs clean. No verifying wrong impl exists, so verify=>resolve holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled fn render_invalid_choice -> interpolated(template,value); real callee is the ValidationError-rendered message template % {'value': value} (post-patch params={'value': value}). Within the sound documented domain (templates whose only %-construct is the %(value)s token — exactly the form of Django's ModelChoiceField/ModelMultipleChoiceField invalid_choice templates and the F2P template), the deep model matches the real str %-mapping EXACTLY on every probe: no-placeholder verbatim, single/multiple %(value)s tokens, partial-token adjacency '%(value)s(value)s', values containing '%' or pseudo-tokens (Python applies the named mapping in one pass, no rescan — model matches). G-AX (axiom_check.py) passes: 143 boundary + 40000 fuzz inputs, 0 mismatch, incl. the literal Django templates. The domain restriction narrows the spec conservatively; it does not make the spec too strong nor let it accept/reject anything the real callee wouldn't on the inputs that actually reach this behavior. Spec region byte-identity not independently re-run here, but the modeling itself is faithful. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = model.py docstring + axioms/pure/spec regions (impl elided per spec_view). Mechanical G-LEAK screen passes clean: no diff markers, no gold-patch line reproduced (`params={'value': value}` absent), patched file path django/forms/models.py absent, patched symbol `to_python` not embedded in any spec-view identifier or comment, no narration terms. Semantically the spec view discloses only the desired observable behavior: interpolate the rejected value into the template's %(value)s placeholder (replace every occurrence, pass other chars through). Every discriminating element is already derivable from the PUBLIC problem_statement, which (a) quotes source containing the literal `%(value)s` token in the invalid_choice default_error_messages, (b) states the desired behavior ('does not show the value of the invalid choice'), and (c) states the fix mechanism ('Passing in parameters with the invalid value and modifying the default error message for the code invalid_choice should fix this'). The %(value)s placeholder and value-interpolation behavior are thus public. The spec view reveals nothing about the edit location/mechanism beyond the problem_statement. The auditor-only docs (refinement.md, mapping.md) do quote the gold hunk and file path, but those are NOT part of the solver-visible spec view and are out of scope for G-PANEL-3. meta G-LEAK recorded pass; relaxed_leakage not set. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
