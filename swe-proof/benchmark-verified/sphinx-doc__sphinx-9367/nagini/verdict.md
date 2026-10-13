# P2 adversarial audit — sphinx-doc__sphinx-9367

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -104,12 +104,14 @@
     Ensures(Result() == render_seq(ToSeq(elts)))
     # post-conditions-end
     # impl-start
+    # PRE-PATCH SKELETON: a non-empty member sequence (whatever its length) is
+    # rendered as the separator-joined members between parentheses; only the
+    # empty sequence gets a special form. A single-member sequence therefore
+    # renders as `(e0)` with NO trailing comma.
     es = ToSeq(elts)  # type: PSeq[PSeq[int]]
     n = len(elts)
     if n == 0:
         return PSeq(40, 41)
-    elif n == 1:
-        return PSeq(40) + es[0] + PSeq(44, 41)
     else:
         joined = empty_seq()  # type: PSeq[int]
         i = n
@@ -118,7 +120,7 @@
             Invariant(Acc(list_pred(elts), 1 / 2))
             Invariant(es == ToSeq(elts))
             Invariant(n == len(elts))
-            Invariant(n >= 2)
+            Invariant(n >= 1)
             Invariant(0 <= i and i <= n)
             Invariant(joined == join_sep(es.drop(i)))
             # The loop consumes the termination obligation: i is the strictly
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -107,24 +107,20 @@
     es = ToSeq(elts)  # type: PSeq[PSeq[int]]
     n = len(elts)
     if n == 0:
-        return PSeq(40, 41)
+        return PSeq(41, 40)
     elif n == 1:
         return PSeq(40) + es[0] + PSeq(44, 41)
     else:
         joined = empty_seq()  # type: PSeq[int]
         i = n
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(elts), 1 / 2))
             Invariant(es == ToSeq(elts))
             Invariant(n == len(elts))
             Invariant(n >= 2)
             Invariant(0 <= i and i <= n)
             Invariant(joined == join_sep(es.drop(i)))
-            # The loop consumes the termination obligation: i is the strictly
-            # decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
             e = es[i - 1]
             Assert(es.drop(i - 1)[0] == e)
             Assert(es.drop(i - 1).drop(1) == es.drop(i))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,22 +109,18 @@
     if n == 0:
         return PSeq(40, 41)
     elif n == 1:
-        return PSeq(40) + es[0] + PSeq(44, 41)
+        return PSeq(40) + es[0] + PSeq(41)
     else:
         joined = empty_seq()  # type: PSeq[int]
         i = n
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(elts), 1 / 2))
             Invariant(es == ToSeq(elts))
             Invariant(n == len(elts))
             Invariant(n >= 2)
             Invariant(0 <= i and i <= n)
             Invariant(joined == join_sep(es.drop(i)))
-            # The loop consumes the termination obligation: i is the strictly
-            # decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
             e = es[i - 1]
             Assert(es.drop(i - 1)[0] == e)
             Assert(es.drop(i - 1).drop(1) == es.drop(i))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -112,26 +112,8 @@
         return PSeq(40) + es[0] + PSeq(44, 41)
     else:
         joined = empty_seq()  # type: PSeq[int]
-        i = n
-        while i > 0:
-            # invariants-start
+        while True:
             Invariant(Acc(list_pred(elts), 1 / 2))
-            Invariant(es == ToSeq(elts))
-            Invariant(n == len(elts))
-            Invariant(n >= 2)
-            Invariant(0 <= i and i <= n)
-            Invariant(joined == join_sep(es.drop(i)))
-            # The loop consumes the termination obligation: i is the strictly
-            # decreasing, bounded-below measure.
-            Invariant(MustTerminate(i))
-            # invariants-end
-            e = es[i - 1]
-            Assert(es.drop(i - 1)[0] == e)
-            Assert(es.drop(i - 1).drop(1) == es.drop(i))
-            if i == n:
-                joined = e
-            else:
-                joined = e + sep() + joined
-            i = i - 1
+            joined = joined + empty_seq()
         return PSeq(40) + joined + PSeq(41)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -114,24 +114,14 @@
         joined = empty_seq()  # type: PSeq[int]
         i = n
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(elts), 1 / 2))
             Invariant(es == ToSeq(elts))
             Invariant(n == len(elts))
             Invariant(n >= 2)
             Invariant(0 <= i and i <= n)
-            Invariant(joined == join_sep(es.drop(i)))
-            # The loop consumes the termination obligation: i is the strictly
-            # decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
             e = es[i - 1]
-            Assert(es.drop(i - 1)[0] == e)
-            Assert(es.drop(i - 1).drop(1) == es.drop(i))
-            if i == n:
-                joined = e
-            else:
-                joined = e + sep() + joined
+            joined = e + joined
             i = i - 1
         return PSeq(40) + joined + PSeq(41)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -109,22 +109,18 @@
     if n == 0:
         return PSeq(40, 41)
     elif n == 1:
-        return PSeq(40) + es[0] + PSeq(44, 41)
+        return PSeq(40) + es[0] + sep() + PSeq(41)
     else:
         joined = empty_seq()  # type: PSeq[int]
         i = n
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(elts), 1 / 2))
             Invariant(es == ToSeq(elts))
             Invariant(n == len(elts))
             Invariant(n >= 2)
             Invariant(0 <= i and i <= n)
             Invariant(joined == join_sep(es.drop(i)))
-            # The loop consumes the termination obligation: i is the strictly
-            # decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
             e = es[i - 1]
             Assert(es.drop(i - 1)[0] == e)
             Assert(es.drop(i - 1).drop(1) == es.drop(i))
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -107,24 +107,20 @@
     es = ToSeq(elts)  # type: PSeq[PSeq[int]]
     n = len(elts)
     if n == 0:
-        return PSeq(40, 41)
+        return empty_seq()
     elif n == 1:
         return PSeq(40) + es[0] + PSeq(44, 41)
     else:
         joined = empty_seq()  # type: PSeq[int]
         i = n
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(elts), 1 / 2))
             Invariant(es == ToSeq(elts))
             Invariant(n == len(elts))
             Invariant(n >= 2)
             Invariant(0 <= i and i <= n)
             Invariant(joined == join_sep(es.drop(i)))
-            # The loop consumes the termination obligation: i is the strictly
-            # decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
             e = es[i - 1]
             Assert(es.drop(i - 1)[0] == e)
             Assert(es.drop(i - 1).drop(1) == es.drop(i))
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -104,34 +104,5 @@
     Ensures(Result() == render_seq(ToSeq(elts)))
     # post-conditions-end
     # impl-start
-    es = ToSeq(elts)  # type: PSeq[PSeq[int]]
-    n = len(elts)
-    if n == 0:
-        return PSeq(40, 41)
-    elif n == 1:
-        return PSeq(40) + es[0] + PSeq(44, 41)
-    else:
-        joined = empty_seq()  # type: PSeq[int]
-        i = n
-        while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(elts), 1 / 2))
-            Invariant(es == ToSeq(elts))
-            Invariant(n == len(elts))
-            Invariant(n >= 2)
-            Invariant(0 <= i and i <= n)
-            Invariant(joined == join_sep(es.drop(i)))
-            # The loop consumes the termination obligation: i is the strictly
-            # decreasing, bounded-below measure.
-            Invariant(MustTerminate(i))
-            # invariants-end
-            e = es[i - 1]
-            Assert(es.drop(i - 1)[0] == e)
-            Assert(es.drop(i - 1).drop(1) == es.drop(i))
-            if i == n:
-                joined = e
-            else:
-                joined = e + sep() + joined
-            i = i - 1
-        return PSeq(40) + joined + PSeq(41)
+    return render_seq(ToSeq(elts))
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9367.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A parenthesized expression sequence is rendered back to its source-like
  textual form from the textual renderings of its individual members. The
  rendering is delimited by an opening U+0028 `(` and a closing U+0029 `)`;
  the member renderings are separated from one another by the two-code-point
  sequence U+002C U+0020 (`, `).

  The number of members determines the surface form:
    * an empty sequence renders as the bare pair of parentheses `()`;
    * a sequence of exactly ONE member renders as that one member followed by a
      trailing U+002C `,` before the closing parenthesis, so the single-member
      form is textually distinguishable from a merely parenthesized expression;
    * a sequence of two or more members renders as the separator-joined members
      with no trailing separator.

The textual rendering of an individual member is produced by an unchanged
recursive helper; this model takes each member's rendering as a given
code-point sequence (the member renderings are the input carrier) and specifies
only the surrounding assembly, which is the behaviour under change.

The assembly is a bounded, straight-line computation over finitely many
member renderings: it MUST terminate and return its rendered text (a
total-correctness obligation, carried as MustTerminate in the precondition).
An implementation that diverges before returning would satisfy the value
postcondition only vacuously and would never deliver the rendering.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); a sequence of member renderings is a `List[PSeq[int]]` whose pure
view is `PSeq[PSeq[int]]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the member renderings are inputs; the assembly under
# specification is modelled deeply by the pure region below.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def sep() -> PSeq[int]:
    """The member separator: U+002C U+0020 (`, `)."""
    return PSeq(44, 32)


@Pure
def join_sep(s: PSeq[PSeq[int]]) -> PSeq[int]:
    """Separator-joined concatenation of member renderings: between every two
    adjacent members a single `, ` is inserted, with none before the first or
    after the last. Front-recursive so a single unfold is available per loop
    step."""
    if len(s) == 0:
        return empty_seq()
    if len(s) == 1:
        return s[0]
    return s[0] + sep() + join_sep(s.drop(1))


@Pure
def render_seq(s: PSeq[PSeq[int]]) -> PSeq[int]:
    """The full parenthesized rendering of the member-rendering sequence `s`.

    Empty -> `()`; a single member -> that member with a trailing comma inside
    the parentheses; two or more members -> the separator-joined members inside
    the parentheses."""
    if len(s) == 0:
        return PSeq(40, 41)                        # '()'
    if len(s) == 1:
        return PSeq(40) + s[0] + PSeq(44, 41)      # '(' + e0 + ',)'
    return PSeq(40) + join_sep(s) + PSeq(41)       # '(' + join + ')'
# pure-end


def render_tuple(elts: List[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(elts), 1 / 2))
    # TERMINATION: the assembly must actually ANSWER — parenthesizing and
    # joining finitely many member renderings is a bounded computation
    # (str.join over a finite list plus concatenations). Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. an endless loop before the return)
    # satisfies the value postcondition vacuously while sharing the spec; the
    # real visit_Tuple always returns its rendered text.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elts), 1 / 2))
    # The result is exactly the parenthesized rendering of the member
    # renderings, with the empty / single / multi surface forms pinned.
    Ensures(Result() == render_seq(ToSeq(elts)))
    # post-conditions-end
    # impl-start
    es = ToSeq(elts)  # type: PSeq[PSeq[int]]
    n = len(elts)
    if n == 0:
        return PSeq(40, 41)
    elif n == 1:
        return PSeq(40) + es[0] + PSeq(44, 41)
    else:
        joined = empty_seq()  # type: PSeq[int]
        i = n
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(elts), 1 / 2))
            Invariant(es == ToSeq(elts))
            Invariant(n == len(elts))
            Invariant(n >= 2)
            Invariant(0 <= i and i <= n)
            Invariant(joined == join_sep(es.drop(i)))
            # The loop consumes the termination obligation: i is the strictly
            # decreasing, bounded-below measure.
            Invariant(MustTerminate(i))
            # invariants-end
            e = es[i - 1]
            Assert(es.drop(i - 1)[0] == e)
            Assert(es.drop(i - 1).drop(1) == es.drop(i))
            if i == n:
                joined = e
            else:
                joined = e + sep() + joined
            i = i - 1
        return PSeq(40) + joined + PSeq(41)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Adversarial G-EQ (refinement-fidelity) audit of sphinx-doc__sphinx-9367 nagini bundle.

SPEC SHAPE: render_tuple's postcondition pins the ENTIRE domain: Ensures(Result() == render_seq(ToSeq(elts))), with render_seq a closed-form deep model (empty->PSeq(40,41)='()'; single->PSeq(40)+e0+PSeq(44,41)='(e0,)'; multi->'('+join_sep+')'). Plus Requires(MustTerminate(2)) for total correctness. AXIOMS REGION IS EMPTY (model.py:41-44) -> there are NO A-consumed / A-reference legs to audit; the only callee self.visit is the unchanged input carrier (elts: List[PSeq[int]]), correctly NOT axiomatized (mapping.md §3, refinement.md §B).

REFINEMENT.MD AUDIT: All 5 §A legs are R or I (A1=R, A2=I/R, A3=R, A4=R single-member trailing-comma = the one behavioural change, A5=R join). §C certifies no kind-3 (the changed op — parenthesize/join assembly — is modeled deeply by render_seq/join_sep consumed in the postcondition, not hidden behind an axiom). Correspondence to patch.diff (visit_Tuple hunk) holds: A3/A4/A5 map exactly to the empty/single/multi return branches. No A-leg correspondence to check (none exist).

ATTACK BATTERY (8 same-spec wrong impls; all confirmed byte-identical spec via `adversary same-spec` exit 0; impl-region-only edits). Command per attack: python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9367 <file>.
atk_1 = prepatch bug (single-member falls into join branch -> '(e0)' no comma; copied model_prepatch.py): weakness EXIT=2, verification FAILED -> rejected (PREPATCH REPRODUCED).
atk_2 = boundary: empty returns PSeq(41,40)=')(' reversed parens: EXIT=2, FAILED.
atk_3 = boundary: single-member '(e0)' no trailing comma: EXIT=2, FAILED.
atk_4 = control-flow-effect: `while True` endless loop before return (partial-correctness trap): EXIT=2, FAILED — MustTerminate(2) obligation caught divergence.
atk_5 = wrong join: multi-member concatenated with NO separator: EXIT=2, FAILED.
atk_6 = single-member '(e0, )' with sep()+close instead of ',)': EXIT=2, FAILED.
atk_7 = empty returns empty_seq() (nothing) instead of '()': EXIT=2, FAILED.
atk_8 = ungrounded-oracle echo: impl region is exactly `return render_seq(ToSeq(elts))`: weakness EXIT=0 -> CANDIDATE (shares spec AND verifies).

MANDATORY RESOLVE STEP FOR CANDIDATE atk_8: materialized its faithful refined patch (atk_8.patch) — since render_seq's closed form is exactly empty->'()', single->'(e0,)', multi->join, the faithful real-code refinement IS the gold visit_Tuple hunk. Ran swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9367', patch): RESOLVED=True, COMPLETED=True, DETAIL='resolved'. F2P test_unparse[(1,)-(1,)] PASS; all 25 P2P PASS; 0 failures. So the sole verifying same-spec impl RESOLVES -> not a weakness (a benign resolving echo, per the 2026-08-06 G-PANEL-1 echo-attack policy: a resolving echo is NOT a spec weakness).

POSITIVE CONTROL: positive_control.py (copy of model.py) verifies via scripts/nagini_verify.sh: 'Verification successful' in 19.57s, EXIT=0.

CONCLUSION: 8 attacks run (>=5 satisfied), covering partial-domain, boundary (empty & single), control-flow-effect (non-termination), wrong-join, and ungrounded-oracle echo. All 7 genuinely-wrong impls are REJECTED by the verifier; the one verifying impl (echo) resolves. No verifying impl produces a non-resolving faithful patch. verify => correct holds on this spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-9367.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A parenthesized expression sequence is rendered back to its source-like
  textual form from the textual renderings of its individual members. The
  rendering is delimited by an opening U+0028 `(` and a closing U+0029 `)`;
  the member renderings are separated from one another by the two-code-point
  sequence U+002C U+0020 (`, `).

  The number of members determines the surface form:
    * an empty sequence renders as the bare pair of parentheses `()`;
    * a sequence of exactly ONE member renders as that one member followed by a
      trailing U+002C `,` before the closing parenthesis, so the single-member
      form is textually distinguishable from a merely parenthesized expression;
    * a sequence of two or more members renders as the separator-joined members
      with no trailing separator.

The textual rendering of an individual member is produced by an unchanged
recursive helper; this model takes each member's rendering as a given
code-point sequence (the member renderings are the input carrier) and specifies
only the surrounding assembly, which is the behaviour under change.

The assembly is a bounded, straight-line computation over finitely many
member renderings: it MUST terminate and return its rendered text (a
total-correctness obligation, carried as MustTerminate in the precondition).
An implementation that diverges before returning would satisfy the value
postcondition only vacuously and would never deliver the rendering.

Strings are modelled as `PSeq[int]` of Unicode code points (Nagini bans `str`
indexing); a sequence of member renderings is a `List[PSeq[int]]` whose pure
view is `PSeq[PSeq[int]]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the member renderings are inputs; the assembly under
# specification is modelled deeply by the pure region below.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def sep() -> PSeq[int]:
    """The member separator: U+002C U+0020 (`, `)."""
    return PSeq(44, 32)


@Pure
def join_sep(s: PSeq[PSeq[int]]) -> PSeq[int]:
    """Separator-joined concatenation of member renderings: between every two
    adjacent members a single `, ` is inserted, with none before the first or
    after the last. Front-recursive so a single unfold is available per loop
    step."""
    if len(s) == 0:
        return empty_seq()
    if len(s) == 1:
        return s[0]
    return s[0] + sep() + join_sep(s.drop(1))


@Pure
def render_seq(s: PSeq[PSeq[int]]) -> PSeq[int]:
    """The full parenthesized rendering of the member-rendering sequence `s`.

    Empty -> `()`; a single member -> that member with a trailing comma inside
    the parentheses; two or more members -> the separator-joined members inside
    the parentheses."""
    if len(s) == 0:
        return PSeq(40, 41)                        # '()'
    if len(s) == 1:
        return PSeq(40) + s[0] + PSeq(44, 41)      # '(' + e0 + ',)'
    return PSeq(40) + join_sep(s) + PSeq(41)       # '(' + join + ')'
# pure-end


def render_tuple(elts: List[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(elts), 1 / 2))
    # TERMINATION: the assembly must actually ANSWER — parenthesizing and
    # joining finitely many member renderings is a bounded computation
    # (str.join over a finite list plus concatenations). Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. an endless loop before the return)
    # satisfies the value postcondition vacuously while sharing the spec; the
    # real visit_Tuple always returns its rendered text.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(elts), 1 / 2))
    # The result is exactly the parenthesized rendering of the member
    # renderings, with the empty / single / multi surface forms pinned.
    Ensures(Result() == render_seq(ToSeq(elts)))
    # post-conditions-end
    # impl-start
    es = ToSeq(elts)  # type: PSeq[PSeq[int]]
    n = len(elts)
    if n == 0:
        return PSeq(40, 41)
    elif n == 1:
        return PSeq(40) + es[0] + PSeq(44, 41)
    else:
        joined = empty_seq()  # type: PSeq[int]
        i = n
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(elts), 1 / 2))
            Invariant(es == ToSeq(elts))
            Invariant(n == len(elts))
            Invariant(n >= 2)
            Invariant(0 <= i and i <= n)
            Invariant(joined == join_sep(es.drop(i)))
            # The loop consumes the termination obligation: i is the strictly
            # decreasing, bounded-below measure.
            Invariant(MustTerminate(i))
            # invariants-end
            e = es[i - 1]
            Assert(es.drop(i - 1)[0] == e)
            Assert(es.drop(i - 1).drop(1) == es.drop(i))
            if i == n:
                joined = e
            else:
                joined = e + sep() + joined
            i = i - 1
        return PSeq(40) + joined + PSeq(41)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Adversarial G-EQ (refinement-fidelity) audit of sphinx-doc__sphinx-9367 nagini bundle.

SPEC SHAPE: render_tuple's postcondition pins the ENTIRE domain: Ensures(Result() == render_seq(ToSeq(elts))), with render_seq a closed-form deep model (empty->PSeq(40,41)='()'; single->PSeq(40)+e0+PSeq(44,41)='(e0,)'; multi->'('+join_sep+')'). Plus Requires(MustTerminate(2)) for total correctness. AXIOMS REGION IS EMPTY (model.py:41-44) -> there are NO A-consumed / A-reference legs to audit; the only callee self.visit is the unchanged input carrier (elts: List[PSeq[int]]), correctly NOT axiomatized (mapping.md §3, refinement.md §B).

REFINEMENT.MD AUDIT: All 5 §A legs are R or I (A1=R, A2=I/R, A3=R, A4=R single-member trailing-comma = the one behavioural change, A5=R join). §C certifies no kind-3 (the changed op — parenthesize/join assembly — is modeled deeply by render_seq/join_sep consumed in the postcondition, not hidden behind an axiom). Correspondence to patch.diff (visit_Tuple hunk) holds: A3/A4/A5 map exactly to the empty/single/multi return branches. No A-leg correspondence to check (none exist).

ATTACK BATTERY (8 same-spec wrong impls; all confirmed byte-identical spec via `adversary same-spec` exit 0; impl-region-only edits). Command per attack: python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-9367 <file>.
atk_1 = prepatch bug (single-member falls into join branch -> '(e0)' no comma; copied model_prepatch.py): weakness EXIT=2, verification FAILED -> rejected (PREPATCH REPRODUCED).
atk_2 = boundary: empty returns PSeq(41,40)=')(' reversed parens: EXIT=2, FAILED.
atk_3 = boundary: single-member '(e0)' no trailing comma: EXIT=2, FAILED.
atk_4 = control-flow-effect: `while True` endless loop before return (partial-correctness trap): EXIT=2, FAILED — MustTerminate(2) obligation caught divergence.
atk_5 = wrong join: multi-member concatenated with NO separator: EXIT=2, FAILED.
atk_6 = single-member '(e0, )' with sep()+close instead of ',)': EXIT=2, FAILED.
atk_7 = empty returns empty_seq() (nothing) instead of '()': EXIT=2, FAILED.
atk_8 = ungrounded-oracle echo: impl region is exactly `return render_seq(ToSeq(elts))`: weakness EXIT=0 -> CANDIDATE (shares spec AND verifies).

MANDATORY RESOLVE STEP FOR CANDIDATE atk_8: materialized its faithful refined patch (atk_8.patch) — since render_seq's closed form is exactly empty->'()', single->'(e0,)', multi->join, the faithful real-code refinement IS the gold visit_Tuple hunk. Ran swebench_unified.harness.run_resolve('sphinx-doc__sphinx-9367', patch): RESOLVED=True, COMPLETED=True, DETAIL='resolved'. F2P test_unparse[(1,)-(1,)] PASS; all 25 P2P PASS; 0 failures. So the sole verifying same-spec impl RESOLVES -> not a weakness (a benign resolving echo, per the 2026-08-06 G-PANEL-1 echo-attack policy: a resolving echo is NOT a spec weakness).

POSITIVE CONTROL: positive_control.py (copy of model.py) verifies via scripts/nagini_verify.sh: 'Verification successful' in 19.57s, EXIT=0.

CONCLUSION: 8 attacks run (>=5 satisfied), covering partial-domain, boundary (empty & single), control-flow-effect (non-termination), wrong-join, and ungrounded-oracle echo. All 7 genuinely-wrong impls are REJECTED by the verifier; the one verifying impl (echo) resolves. No verifying impl produces a non-resolving faithful patch. verify => correct holds on this spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit for sphinx-doc__sphinx-9367 (nagini). The modeled function render_tuple / render_seq matches the real post-patch _UnparseVisitor.visit_Tuple (sphinx/pycode/ast.py:215) on every input.

Evidence:
1. Spec region is byte-identical with the bundle (same-spec cmd exit 0); model verifies in Nagini (15.9s).
2. Base-commit behavior confirmed in worktree: visit_Tuple renders len==0 -> '()', len==1 -> '(%s,)' % e0, len>=2 -> '(' + ', '.join(...) + ')'.
3. Semantic exhaustive comparison: transcribed real post-patch visit_Tuple and the model's render_seq/join_sep (strings as PSeq[int] code points), compared over all member-rendering lists of length 0..4 drawn from an adversarial alphabet ('' , 'x','1','a, b',')','(',',','1, 2'). ZERO mismatches. The trailing-comma single-member form, the empty '()' form, and the separator-joined multi form all agree, including members that themselves contain commas/parens/spaces.
4. Abstraction fidelity: self.visit(e) is unchanged by the gold patch, so taking member renderings as the input carrier (elts: List[PSeq[int]]) is sound; nothing to over/under-approximate for the changed op, which is modeled deeply.
5. MustTerminate(2) is faithful, not spec-too-strong: the real assembly is a bounded join+concat that always returns, so the total-correctness obligation does not exclude any real-repo behavior.

No diverging input found; spec is neither too strong nor drifting from repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures). Manual review of the rendered spec view confirms no leak beyond the public problem_statement:

- Public problem_statement already discloses the exact discriminating change: '(1,) is rendered as (1), but should keep the trailing comma.' The single-member trailing-comma behavior IS the public task.
- Spec view describes the single-member form as 'that one member followed by a trailing , before the closing parenthesis' — this is precisely the publicly-requested behavior, not information beyond the statement.
- No diff markers, no gold-patch line reproduced (>=8 char normalized match), no patched file path 'sphinx/pycode/ast.py' or dotted module path in the view.
- No spec-view identifier echoes the patched repo symbol 'visit_Tuple' (spec identifiers: render_tuple, render_seq, join_sep, sep, empty_seq — none embed 'Tuple' as a distinctive symbol; note the patch's distinctive changed symbol set does not include a term that appears in spec identifiers).
- No narration terms (bug/fix/incorrectly/wrong/etc.) in spec-view comments/docstrings.
- The impl region is elided in the spec view ('implementation elided — supplied by the consumer'), so the concrete code edit (the elif len==1 branch) is not exposed.

The spec is a full functional postcondition (empty/single/multi surface forms all pinned), which is legitimate for a faithful spec; the only edit-discriminating content matches the public bug report. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
