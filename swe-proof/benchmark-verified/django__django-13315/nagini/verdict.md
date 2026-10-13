# P2 adversarial audit — django__django-13315

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_pre.py`, `atk_first.py`, `atk_empty.py`, `atk_drop.py`, `atk_invent.py`, `atk_invert.py`, `atk_offbyone.py` |

**Non-vacuity.** The positive control `atk_pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_pre.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # required AND ensured, so no caller can satisfy a postcondition vacuously by
     # overwriting the input.
     Requires(Acc(list_pred(matches), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(matches), 1 / 2))
@@ -98,27 +96,17 @@
     Ensures(ToSeq(Result()) == dedup(ToSeq(matches)))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `dedup` (one unfold per step).
     result = []  # type: List[int]
     i = len(matches)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(matches), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(matches))
-        Invariant(ToSeq(result) == dedup(ToSeq(matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
+        Invariant(ToSeq(result) == ToSeq(matches).drop(i))
         Assert(ToSeq(matches).drop(i - 1)[0] == matches[i - 1])
         Assert(ToSeq(matches).drop(i - 1).drop(1) == ToSeq(matches).drop(i))
         v = matches[i - 1]
-        # Keep this row only if it does not recur later in the stream, so a row
-        # matched along several join paths is offered exactly once.
-        if occurs(v, ToSeq(matches).drop(i)):
-            pass
-        else:
-            result = [v] + result
+        result = [v] + result
         i = i - 1
     return result
     # impl-end
```

Attack 2 — `atk_first.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # required AND ensured, so no caller can satisfy a postcondition vacuously by
     # overwriting the input.
     Requires(Acc(list_pred(matches), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(matches), 1 / 2))
@@ -98,27 +96,18 @@
     Ensures(ToSeq(Result()) == dedup(ToSeq(matches)))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `dedup` (one unfold per step).
+    # Forward scan keeping the FIRST occurrence of each value.
     result = []  # type: List[int]
-    i = len(matches)
-    while i > 0:
-        # invariants-start
+    i = 0
+    while i < len(matches):
         Invariant(Acc(list_pred(matches), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(matches))
-        Invariant(ToSeq(result) == dedup(ToSeq(matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(matches).drop(i - 1)[0] == matches[i - 1])
-        Assert(ToSeq(matches).drop(i - 1).drop(1) == ToSeq(matches).drop(i))
-        v = matches[i - 1]
-        # Keep this row only if it does not recur later in the stream, so a row
-        # matched along several join paths is offered exactly once.
-        if occurs(v, ToSeq(matches).drop(i)):
+        v = matches[i]
+        if occurs(v, ToSeq(result)):
             pass
         else:
-            result = [v] + result
-        i = i - 1
+            result = result + [v]
+        i = i + 1
     return result
     # impl-end
```

Attack 3 — `atk_empty.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # required AND ensured, so no caller can satisfy a postcondition vacuously by
     # overwriting the input.
     Requires(Acc(list_pred(matches), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(matches), 1 / 2))
@@ -98,27 +96,6 @@
     Ensures(ToSeq(Result()) == dedup(ToSeq(matches)))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `dedup` (one unfold per step).
     result = []  # type: List[int]
-    i = len(matches)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(matches), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(matches))
-        Invariant(ToSeq(result) == dedup(ToSeq(matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
-        Assert(ToSeq(matches).drop(i - 1)[0] == matches[i - 1])
-        Assert(ToSeq(matches).drop(i - 1).drop(1) == ToSeq(matches).drop(i))
-        v = matches[i - 1]
-        # Keep this row only if it does not recur later in the stream, so a row
-        # matched along several join paths is offered exactly once.
-        if occurs(v, ToSeq(matches).drop(i)):
-            pass
-        else:
-            result = [v] + result
-        i = i - 1
     return result
     # impl-end
```

Attack 4 — `atk_drop.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # required AND ensured, so no caller can satisfy a postcondition vacuously by
     # overwriting the input.
     Requires(Acc(list_pred(matches), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(matches), 1 / 2))
@@ -98,23 +96,15 @@
     Ensures(ToSeq(Result()) == dedup(ToSeq(matches)))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `dedup` (one unfold per step).
     result = []  # type: List[int]
     i = len(matches)
-    while i > 0:
-        # invariants-start
+    while i > 1:
         Invariant(Acc(list_pred(matches), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(matches))
-        Invariant(ToSeq(result) == dedup(ToSeq(matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
+        Invariant(1 <= i and i <= len(matches))
         Assert(ToSeq(matches).drop(i - 1)[0] == matches[i - 1])
         Assert(ToSeq(matches).drop(i - 1).drop(1) == ToSeq(matches).drop(i))
         v = matches[i - 1]
-        # Keep this row only if it does not recur later in the stream, so a row
-        # matched along several join paths is offered exactly once.
         if occurs(v, ToSeq(matches).drop(i)):
             pass
         else:
```

Attack 5 — `atk_invent.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # required AND ensured, so no caller can satisfy a postcondition vacuously by
     # overwriting the input.
     Requires(Acc(list_pred(matches), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(matches), 1 / 2))
@@ -98,23 +96,15 @@
     Ensures(ToSeq(Result()) == dedup(ToSeq(matches)))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `dedup` (one unfold per step).
-    result = []  # type: List[int]
+    result = [0]  # type: List[int]
     i = len(matches)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(matches), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(matches))
-        Invariant(ToSeq(result) == dedup(ToSeq(matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(ToSeq(matches).drop(i - 1)[0] == matches[i - 1])
         Assert(ToSeq(matches).drop(i - 1).drop(1) == ToSeq(matches).drop(i))
         v = matches[i - 1]
-        # Keep this row only if it does not recur later in the stream, so a row
-        # matched along several join paths is offered exactly once.
         if occurs(v, ToSeq(matches).drop(i)):
             pass
         else:
```

Attack 6 — `atk_invert.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # required AND ensured, so no caller can satisfy a postcondition vacuously by
     # overwriting the input.
     Requires(Acc(list_pred(matches), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(matches), 1 / 2))
@@ -98,27 +96,21 @@
     Ensures(ToSeq(Result()) == dedup(ToSeq(matches)))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `dedup` (one unfold per step).
+    # Inverted guard: keep the row only if it DOES recur later (drops the last
+    # occurrence, keeps earlier ones) -> wrong set/order.
     result = []  # type: List[int]
     i = len(matches)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(matches), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(matches))
-        Invariant(ToSeq(result) == dedup(ToSeq(matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(ToSeq(matches).drop(i - 1)[0] == matches[i - 1])
         Assert(ToSeq(matches).drop(i - 1).drop(1) == ToSeq(matches).drop(i))
         v = matches[i - 1]
-        # Keep this row only if it does not recur later in the stream, so a row
-        # matched along several join paths is offered exactly once.
         if occurs(v, ToSeq(matches).drop(i)):
+            result = [v] + result
+        else:
             pass
-        else:
-            result = [v] + result
         i = i - 1
     return result
     # impl-end
```

Attack 7 — `atk_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -85,7 +84,6 @@
     # required AND ensured, so no caller can satisfy a postcondition vacuously by
     # overwriting the input.
     Requires(Acc(list_pred(matches), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(matches), 1 / 2))
@@ -98,24 +96,16 @@
     Ensures(ToSeq(Result()) == dedup(ToSeq(matches)))
     # post-conditions-end
     # impl-start
-    # Scan back-to-front so each step peels the leading element of the suffix
-    # `drop(i-1)`, matching the front-recursive `dedup` (one unfold per step).
     result = []  # type: List[int]
     i = len(matches)
     while i > 0:
-        # invariants-start
         Invariant(Acc(list_pred(matches), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(matches))
-        Invariant(ToSeq(result) == dedup(ToSeq(matches).drop(i)))
-        Invariant(MustTerminate(i + 1))
-        # invariants-end
         Assert(ToSeq(matches).drop(i - 1)[0] == matches[i - 1])
         Assert(ToSeq(matches).drop(i - 1).drop(1) == ToSeq(matches).drop(i))
         v = matches[i - 1]
-        # Keep this row only if it does not recur later in the stream, so a row
-        # matched along several join paths is offered exactly once.
-        if occurs(v, ToSeq(matches).drop(i)):
+        if occurs(v, ToSeq(matches).drop(i - 1)):
             pass
         else:
             result = [v] + result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.py`

```python
"""Twin-artifact model for django__django-13315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A form field that offers a choice of related rows narrows its offered options
  by a restriction. When that restriction spans a relational join, a single
  offered row can be matched by the restriction along SEVERAL distinct join
  paths, so the raw matching pass yields the same row more than once. The
  options a user is offered must NOT contain such repeats: a row that satisfies
  the restriction is offered EXACTLY ONCE.

  The behaviour pinned here is the relationship between the raw stream of
  restriction matches (a row identifier appears once per join path that
  satisfies the restriction, hence possibly several times) and the options the
  field exposes. The offered options are the DUPLICATE-FREE image of the raw
  matching stream:

    * membership is preserved -- a row is offered if and only if the raw
      matching pass produced it at least once (no genuinely-matching row is
      dropped, and no row that never matched is invented); and
    * no row identifier is offered more than once, however many join paths
      matched it.

  This duplicate-free image is captured exactly by `dedup` below: it keeps one
  representative of every value occurring in the stream and discards every
  repeat, so by construction the result has no duplicate and preserves
  membership.

A queryset is modelled as a `List[int]` of row identifiers (primary keys). The
raw matching pass -- applying the restriction across the join -- is the input
`matches`, in which a row identifier may repeat once per satisfying join path.
The offered options are the returned `List[int]`. `List[int]`/`PSeq` sequence
reasoning carries the specification; Nagini bans richer object graphs, and the
only property the result is observed through is its multiset of row identifiers
collapsed to a set (which row identifiers are offered, each at most once).

No callee is axiomatized: the change is pure collection logic (duplicate
elimination over the matching stream), modelled deeply over `List[int]` as the
front-recursive fold `dedup`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly callees: the behaviour is the duplicate-free image of the
# raw matching stream, modelled deeply over List[int] as the front-recursive
# fold `dedup`; there is no unchanged library callee whose Ensures the proof
# must consume.)
# axioms-end


# pure-start
@Pure
def occurs(v: int, s: PSeq[int]) -> bool:
    """Whether the row identifier `v` appears somewhere in `s`. Front-recursive
    over the sequence so a single membership unfold is available per step."""
    if len(s) == 0:
        return False
    return s[0] == v or occurs(v, s.drop(1))


@Pure
def dedup(s: PSeq[int]) -> PSeq[int]:
    """The duplicate-free image of `s`: keep exactly one representative of each
    distinct value and discard every repeat. Front-recursive (one unfold per
    element): a head that recurs later in the sequence is dropped here and kept
    at its later occurrence, so the result carries no value twice while every
    value present in `s` remains present."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if occurs(s[0], s.drop(1)):
        return dedup(s.drop(1))
    return PSeq(s[0]) + dedup(s.drop(1))
# pure-end


def offered_options(matches: List[int]) -> List[int]:
    # pre-conditions-start
    # The raw matching stream is read-only here (the narrowing reads it to build
    # a fresh options list; it does not mutate it). Fractional permission,
    # required AND ensured, so no caller can satisfy a postcondition vacuously by
    # overwriting the input.
    Requires(Acc(list_pred(matches), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(matches), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The offered options are exactly the duplicate-free image of the raw
    # matching stream: every value present in `matches` is offered (membership
    # preserved) and none is offered twice (`dedup` is duplicate-free by
    # construction). Returning the matching stream unchanged -- repeats and all
    # -- violates this whenever a row matched along more than one join path.
    Ensures(ToSeq(Result()) == dedup(ToSeq(matches)))
    # post-conditions-end
    # impl-start
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `dedup` (one unfold per step).
    result = []  # type: List[int]
    i = len(matches)
    while i > 0:
        Invariant(Acc(list_pred(matches), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(matches))
        Invariant(ToSeq(result) == dedup(ToSeq(matches).drop(i)))
        Assert(ToSeq(matches).drop(i - 1)[0] == matches[i - 1])
        Assert(ToSeq(matches).drop(i - 1).drop(1) == ToSeq(matches).drop(i))
        v = matches[i - 1]
        if occurs(v, ToSeq(matches).drop(i)):
            pass
        else:
            result = [v] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-13315 (nagini).

SPEC SHAPE: offered_options ensures a TOTAL FUNCTIONAL EQUALITY to a GROUNDED (spelled-out, non-opaque) reference: Ensures(ToSeq(Result()) == dedup(ToSeq(matches))), where dedup is the front-recursive keep-last-occurrence fold in the @Pure region. Precondition is only Acc(list_pred(matches),1/2), so the postcondition pins the output exactly over the whole domain. There is NO @ContractOnly axiom (no A-consumed leg); the sole changed op (collapse duplicate join-match stream -> distinct set) is modelled DEEPLY as dedup (A-reference), validated == real semantics out-of-band by G-AX.

SAME-SPEC (all 8 files, exit 0 = spec byte-identical, impl region only differs): atk_pre, atk_first, atk_empty, atk_drop, atk_invent, atk_invert, atk_offbyone, atk_pc -> all SAME.

WEAKNESS runs (python -m swebench_unified.adversary weakness nagini django__django-13315 <path>), run concurrently in batches of <=3 JVMs:
- atk_pc.py (positive control = gold model impl, byte-identical impl region): EXIT=0 CANDIDATE = verifies (expected: it is the correct impl). Confirms spec is satisfiable.
- atk_pre.py (PREPATCH BUG: raw stream verbatim, invariant ToSeq(result)==ToSeq(matches).drop(i), no dedup): EXIT=2 does-not-verify -> spec REJECTS the bug (G-DIFF sensed). prepatch_reproduced=true.
- atk_first.py (keep-FIRST occurrence via forward scan; correct SET, wrong ORDER vs last-occurrence dedup): EXIT=2 rejected.
- atk_empty.py (ungrounded/partial-domain: return [] always; correct only when matches empty): EXIT=2 rejected.
- atk_drop.py (partial-domain / drops a genuinely-matching row: loop while i>1 skips element 0): EXIT=2 rejected.
- atk_invent.py (invents a non-matching row: seed result=[0]): EXIT=2 rejected.
- atk_invert.py (control-flow-effect: inverted keep-guard, keeps recurring earlier occurrences / drops last): EXIT=2 rejected.
- atk_offbyone.py (boundary/off-by-one: membership tested against drop(i-1) instead of drop(i)): EXIT=2 rejected.

RESULT: 0 of 7 wrong impls became a CANDIDATE (none both shares-spec AND verifies). Therefore NO materialized faithful patch / run_resolve was required (the protocol's resolve step triggers only on a verifying wrong impl; there were none). The grounded functional-equality postcondition cannot be echoed and admits exactly dedup(matches); every deviation on membership, multiplicity, or last-occurrence order fails Nagini verification.

A-LEG / correspondence audit (refinement.md): legs A1(R), A2(A-reference), A3(R+A-reference), A4(R), B(I) — all R / A-reference / I, NO kind-3 (unexpressible-changed-op). The single changed op (duplicate collapse) is A-reference modelled deeply (dedup/occurs), not hidden behind an axiom. G-AX axiom_check.py PASSES (exit 0): 'dedup deep model == real Exists()-distinct semantics (membership-preserving, duplicate-free) over 10 boundary + 50000 fuzz streams; occurs == real membership; pre-patch complex_filter raw stream carries the duplicates the gold path removes.' The A-reference correspondence (deep dedup <-> queryset.filter(Exists(_base_manager.filter(complex_filter & Q(pk=OuterRef('pk'))))) net effect = distinct matching rows) holds; observation is assertCountEqual (multiset/membership), order is unobserved, so dedup's last-occurrence ordering is a harmless strengthening on an unobserved dimension.

VERDICT: SOUND. >=5 distinct attacks (7) run and fully verified; none breaks the spec; positive control verifies; prepatch reproduced-and-rejected; G-AX passes; refinement legs clean (no kind-3).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_pre.py`, `atk_first.py`, `atk_empty.py`, `atk_drop.py`, `atk_invent.py`, `atk_invert.py`, `atk_offbyone.py` |

**Non-vacuity.** The positive control `atk_pc.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_pre.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_first.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_empty.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_drop.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_invent.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_invert.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_offbyone.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.py`

```python
"""Twin-artifact model for django__django-13315.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A form field that offers a choice of related rows narrows its offered options
  by a restriction. When that restriction spans a relational join, a single
  offered row can be matched by the restriction along SEVERAL distinct join
  paths, so the raw matching pass yields the same row more than once. The
  options a user is offered must NOT contain such repeats: a row that satisfies
  the restriction is offered EXACTLY ONCE.

  The behaviour pinned here is the relationship between the raw stream of
  restriction matches (a row identifier appears once per join path that
  satisfies the restriction, hence possibly several times) and the options the
  field exposes. The offered options are the DUPLICATE-FREE image of the raw
  matching stream:

    * membership is preserved -- a row is offered if and only if the raw
      matching pass produced it at least once (no genuinely-matching row is
      dropped, and no row that never matched is invented); and
    * no row identifier is offered more than once, however many join paths
      matched it.

  This duplicate-free image is captured exactly by `dedup` below: it keeps one
  representative of every value occurring in the stream and discards every
  repeat, so by construction the result has no duplicate and preserves
  membership.

A queryset is modelled as a `List[int]` of row identifiers (primary keys). The
raw matching pass -- applying the restriction across the join -- is the input
`matches`, in which a row identifier may repeat once per satisfying join path.
The offered options are the returned `List[int]`. `List[int]`/`PSeq` sequence
reasoning carries the specification; Nagini bans richer object graphs, and the
only property the result is observed through is its multiset of row identifiers
collapsed to a set (which row identifiers are offered, each at most once).

No callee is axiomatized: the change is pure collection logic (duplicate
elimination over the matching stream), modelled deeply over `List[int]` as the
front-recursive fold `dedup`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no @ContractOnly callees: the behaviour is the duplicate-free image of the
# raw matching stream, modelled deeply over List[int] as the front-recursive
# fold `dedup`; there is no unchanged library callee whose Ensures the proof
# must consume.)
# axioms-end


# pure-start
@Pure
def occurs(v: int, s: PSeq[int]) -> bool:
    """Whether the row identifier `v` appears somewhere in `s`. Front-recursive
    over the sequence so a single membership unfold is available per step."""
    if len(s) == 0:
        return False
    return s[0] == v or occurs(v, s.drop(1))


@Pure
def dedup(s: PSeq[int]) -> PSeq[int]:
    """The duplicate-free image of `s`: keep exactly one representative of each
    distinct value and discard every repeat. Front-recursive (one unfold per
    element): a head that recurs later in the sequence is dropped here and kept
    at its later occurrence, so the result carries no value twice while every
    value present in `s` remains present."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if occurs(s[0], s.drop(1)):
        return dedup(s.drop(1))
    return PSeq(s[0]) + dedup(s.drop(1))
# pure-end


def offered_options(matches: List[int]) -> List[int]:
    # pre-conditions-start
    # The raw matching stream is read-only here (the narrowing reads it to build
    # a fresh options list; it does not mutate it). Fractional permission,
    # required AND ensured, so no caller can satisfy a postcondition vacuously by
    # overwriting the input.
    Requires(Acc(list_pred(matches), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(matches), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The offered options are exactly the duplicate-free image of the raw
    # matching stream: every value present in `matches` is offered (membership
    # preserved) and none is offered twice (`dedup` is duplicate-free by
    # construction). Returning the matching stream unchanged -- repeats and all
    # -- violates this whenever a row matched along more than one join path.
    Ensures(ToSeq(Result()) == dedup(ToSeq(matches)))
    # post-conditions-end
    # impl-start
    # Scan back-to-front so each step peels the leading element of the suffix
    # `drop(i-1)`, matching the front-recursive `dedup` (one unfold per step).
    result = []  # type: List[int]
    i = len(matches)
    while i > 0:
        Invariant(Acc(list_pred(matches), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(matches))
        Invariant(ToSeq(result) == dedup(ToSeq(matches).drop(i)))
        Assert(ToSeq(matches).drop(i - 1)[0] == matches[i - 1])
        Assert(ToSeq(matches).drop(i - 1).drop(1) == ToSeq(matches).drop(i))
        v = matches[i - 1]
        if occurs(v, ToSeq(matches).drop(i)):
            pass
        else:
            result = [v] + result
        i = i - 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-13315 (nagini).

SPEC SHAPE: offered_options ensures a TOTAL FUNCTIONAL EQUALITY to a GROUNDED (spelled-out, non-opaque) reference: Ensures(ToSeq(Result()) == dedup(ToSeq(matches))), where dedup is the front-recursive keep-last-occurrence fold in the @Pure region. Precondition is only Acc(list_pred(matches),1/2), so the postcondition pins the output exactly over the whole domain. There is NO @ContractOnly axiom (no A-consumed leg); the sole changed op (collapse duplicate join-match stream -> distinct set) is modelled DEEPLY as dedup (A-reference), validated == real semantics out-of-band by G-AX.

SAME-SPEC (all 8 files, exit 0 = spec byte-identical, impl region only differs): atk_pre, atk_first, atk_empty, atk_drop, atk_invent, atk_invert, atk_offbyone, atk_pc -> all SAME.

WEAKNESS runs (python -m swebench_unified.adversary weakness nagini django__django-13315 <path>), run concurrently in batches of <=3 JVMs:
- atk_pc.py (positive control = gold model impl, byte-identical impl region): EXIT=0 CANDIDATE = verifies (expected: it is the correct impl). Confirms spec is satisfiable.
- atk_pre.py (PREPATCH BUG: raw stream verbatim, invariant ToSeq(result)==ToSeq(matches).drop(i), no dedup): EXIT=2 does-not-verify -> spec REJECTS the bug (G-DIFF sensed). prepatch_reproduced=true.
- atk_first.py (keep-FIRST occurrence via forward scan; correct SET, wrong ORDER vs last-occurrence dedup): EXIT=2 rejected.
- atk_empty.py (ungrounded/partial-domain: return [] always; correct only when matches empty): EXIT=2 rejected.
- atk_drop.py (partial-domain / drops a genuinely-matching row: loop while i>1 skips element 0): EXIT=2 rejected.
- atk_invent.py (invents a non-matching row: seed result=[0]): EXIT=2 rejected.
- atk_invert.py (control-flow-effect: inverted keep-guard, keeps recurring earlier occurrences / drops last): EXIT=2 rejected.
- atk_offbyone.py (boundary/off-by-one: membership tested against drop(i-1) instead of drop(i)): EXIT=2 rejected.

RESULT: 0 of 7 wrong impls became a CANDIDATE (none both shares-spec AND verifies). Therefore NO materialized faithful patch / run_resolve was required (the protocol's resolve step triggers only on a verifying wrong impl; there were none). The grounded functional-equality postcondition cannot be echoed and admits exactly dedup(matches); every deviation on membership, multiplicity, or last-occurrence order fails Nagini verification.

A-LEG / correspondence audit (refinement.md): legs A1(R), A2(A-reference), A3(R+A-reference), A4(R), B(I) — all R / A-reference / I, NO kind-3 (unexpressible-changed-op). The single changed op (duplicate collapse) is A-reference modelled deeply (dedup/occurs), not hidden behind an axiom. G-AX axiom_check.py PASSES (exit 0): 'dedup deep model == real Exists()-distinct semantics (membership-preserving, duplicate-free) over 10 boundary + 50000 fuzz streams; occurs == real membership; pre-patch complex_filter raw stream carries the duplicates the gold path removes.' The A-reference correspondence (deep dedup <-> queryset.filter(Exists(_base_manager.filter(complex_filter & Q(pk=OuterRef('pk'))))) net effect = distinct matching rows) holds; observation is assertCountEqual (multiset/membership), order is unobserved, so dedup's last-occurrence ordering is a harmless strengthening on an unobserved dimension.

VERDICT: SOUND. >=5 distinct attacks (7) run and fully verified; none breaks the spec; positive control verifies; prepatch reproduced-and-rejected; G-AX passes; refinement legs clean (no kind-3).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-13315 (nagini). Spec region byte-identical: same-spec EXIT=0. G-AX axiom_check.py passes here (dedup == independent exists_distinct reconstruction over 10 boundary + 50000 fuzz streams; occurs == real membership).

Spec: offered_options ensures ToSeq(Result()) == dedup(ToSeq(matches)); dedup keeps one representative per distinct value (last occurrence), membership-preserving and duplicate-free.

Real callee (verified at base_commit, django/forms/models.py:98 post-patch): apply_limit_choices_to_to_formfield narrows formfield.queryset via filter(Exists(model._base_manager.filter(complex_filter & Q(pk=OuterRef('pk'))))). Exists is a correlated boolean subquery (not an outer join), so a base row is offered iff >=1 join path satisfies limit_choices_to, and at most once -> the DISTINCT SET of matching rows.

Observation abstraction (mapping.md §2, confirmed by the F2P test test_limit_choices_to_no_duplicates at tests/model_forms/tests.py:2834): QuerySet rows -> List[int] of pks, observed only through assertCountEqual (multiset/membership equality, order-independent).

Divergence search:
- Membership: dedup(matches) = distinct values of matches = rows matching >=1 join path = real Exists() output set. Agree on every input.
- Multiplicity: both yield each matching row exactly once. Agree as multisets.
- Ordering: dedup pins a last-occurrence list order -- STRONGER than the real queryset's unspecified order -- but ordering is outside the observation (assertCountEqual is order-blind). A strengthening on an unobserved dimension is not a divergence on the observable equivalence.

No diverging input found across empty/single/multi-path/interleaved/all-distinct streams. The spec is not too strong on any OBSERVABLE dimension; it exactly captures 'distinct set of matching rows'. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen) passes: no diff markers, no reproduced gold-patch line, no patched file path (django/forms/models.py), no spec-view identifier embedding a patched symbol, no bug/fix narration. Bundle is NOT relaxed (no relaxed_leakage flag / RELAXED_LEAKAGE.md).

Public problem_statement already discloses the bug and its direct goal: 'limit_choices_to on a ForeignKey can render duplicate options in formfield' and 'if you pass a Q object ... involving a join, you may end up with duplicate options.' So the fact that duplicates arise from a join-spanning restriction, and that the desired behavior is to eliminate them, is already public.

The spec view (docstring + occurs/dedup pure region + offered_options contract) pins only the DESIRED BEHAVIOR any solver derives from that public bug: the offered options are the duplicate-free image of the raw matching stream (membership preserved, no repeats; Ensures ToSeq(Result()) == dedup(ToSeq(matches))). The 'matched along SEVERAL distinct join paths' account is the standard mechanistic explanation of why a join produces duplicates — understanding of the public problem, not the gold edit.

The actual gold edit is entirely withheld: no mention of Exists / OuterRef / Q / _base_manager / complex_filter, no 'Use Exists() to avoid potential duplicates' comment, no correlated-subquery strategy. The repo symbol apply_limit_choices_to_to_formfield is renamed to offered_options. The spec discloses WHAT (deduplicate) — already implied by the public statement — but not HOW (the Exists()-wrapping), which is the discriminating content of the gold patch. No leak beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
