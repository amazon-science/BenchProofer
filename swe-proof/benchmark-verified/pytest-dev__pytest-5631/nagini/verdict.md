# P2 adversarial audit — pytest-dev__pytest-5631

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -136,11 +136,11 @@
         c = kinds[i - 1]
         Assert(ToSeq(kinds).drop(i - 1)[0] == c)
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
-        # Total identity decision: kind 1 (identity match, no attribute name)
-        # counts; every other kind — including kind 3 (non-truth-evaluable
-        # equality) — does not, and is handled without failure.
-        if counts_as_mock(c):
-            count = count + 1
+        if c != 0:
+            if c == 3:
+                raise NonTruthEvaluableEquality()
+            if c == 1:
+                count = count + 1
         i = i - 1
     return count
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -121,26 +121,5 @@
     Ensures(0 <= Result() and Result() <= len(kinds))
     # post-conditions-end
     # impl-start
-    count = 0
-    i = len(kinds)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(kinds), 1 / 2))
-        Invariant(0 <= i and i <= len(kinds))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(kinds),
-                                                 0 <= kinds[k] and kinds[k] <= 3),
-                                          [[kinds[k]]])))
-        Invariant(count == count_sentinel_directives(ToSeq(kinds).drop(i)))
-        Invariant(0 <= count and count <= len(kinds) - i)
-        # invariants-end
-        c = kinds[i - 1]
-        Assert(ToSeq(kinds).drop(i - 1)[0] == c)
-        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
-        # Total identity decision: kind 1 (identity match, no attribute name)
-        # counts; every other kind — including kind 3 (non-truth-evaluable
-        # equality) — does not, and is handled without failure.
-        if counts_as_mock(c):
-            count = count + 1
-        i = i - 1
-    return count
+    return len(kinds)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -121,26 +121,5 @@
     Ensures(0 <= Result() and Result() <= len(kinds))
     # post-conditions-end
     # impl-start
-    count = 0
-    i = len(kinds)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(kinds), 1 / 2))
-        Invariant(0 <= i and i <= len(kinds))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(kinds),
-                                                 0 <= kinds[k] and kinds[k] <= 3),
-                                          [[kinds[k]]])))
-        Invariant(count == count_sentinel_directives(ToSeq(kinds).drop(i)))
-        Invariant(0 <= count and count <= len(kinds) - i)
-        # invariants-end
-        c = kinds[i - 1]
-        Assert(ToSeq(kinds).drop(i - 1)[0] == c)
-        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
-        # Total identity decision: kind 1 (identity match, no attribute name)
-        # counts; every other kind — including kind 3 (non-truth-evaluable
-        # equality) — does not, and is handled without failure.
-        if counts_as_mock(c):
-            count = count + 1
-        i = i - 1
-    return count
+    return 0
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -121,26 +121,5 @@
     Ensures(0 <= Result() and Result() <= len(kinds))
     # post-conditions-end
     # impl-start
-    count = 0
-    i = len(kinds)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(kinds), 1 / 2))
-        Invariant(0 <= i and i <= len(kinds))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(kinds),
-                                                 0 <= kinds[k] and kinds[k] <= 3),
-                                          [[kinds[k]]])))
-        Invariant(count == count_sentinel_directives(ToSeq(kinds).drop(i)))
-        Invariant(0 <= count and count <= len(kinds) - i)
-        # invariants-end
-        c = kinds[i - 1]
-        Assert(ToSeq(kinds).drop(i - 1)[0] == c)
-        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
-        # Total identity decision: kind 1 (identity match, no attribute name)
-        # counts; every other kind — including kind 3 (non-truth-evaluable
-        # equality) — does not, and is handled without failure.
-        if counts_as_mock(c):
-            count = count + 1
-        i = i - 1
-    return count
+    return count_sentinel_directives(ToSeq(kinds)) + 1
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -121,26 +121,5 @@
     Ensures(0 <= Result() and Result() <= len(kinds))
     # post-conditions-end
     # impl-start
-    count = 0
-    i = len(kinds)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(kinds), 1 / 2))
-        Invariant(0 <= i and i <= len(kinds))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(kinds),
-                                                 0 <= kinds[k] and kinds[k] <= 3),
-                                          [[kinds[k]]])))
-        Invariant(count == count_sentinel_directives(ToSeq(kinds).drop(i)))
-        Invariant(0 <= count and count <= len(kinds) - i)
-        # invariants-end
-        c = kinds[i - 1]
-        Assert(ToSeq(kinds).drop(i - 1)[0] == c)
-        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
-        # Total identity decision: kind 1 (identity match, no attribute name)
-        # counts; every other kind — including kind 3 (non-truth-evaluable
-        # equality) — does not, and is handled without failure.
-        if counts_as_mock(c):
-            count = count + 1
-        i = i - 1
-    return count
+    return len(kinds) - count_sentinel_directives(ToSeq(kinds))
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -121,26 +121,5 @@
     Ensures(0 <= Result() and Result() <= len(kinds))
     # post-conditions-end
     # impl-start
-    count = 0
-    i = len(kinds)
-    while i > 0:
-        # invariants-start
-        Invariant(Acc(list_pred(kinds), 1 / 2))
-        Invariant(0 <= i and i <= len(kinds))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(kinds),
-                                                 0 <= kinds[k] and kinds[k] <= 3),
-                                          [[kinds[k]]])))
-        Invariant(count == count_sentinel_directives(ToSeq(kinds).drop(i)))
-        Invariant(0 <= count and count <= len(kinds) - i)
-        # invariants-end
-        c = kinds[i - 1]
-        Assert(ToSeq(kinds).drop(i - 1)[0] == c)
-        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
-        # Total identity decision: kind 1 (identity match, no attribute name)
-        # counts; every other kind — including kind 3 (non-truth-evaluable
-        # equality) — does not, and is handled without failure.
-        if counts_as_mock(c):
-            count = count + 1
-        i = i - 1
-    return count
+    return 1
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -136,9 +136,6 @@
         c = kinds[i - 1]
         Assert(ToSeq(kinds).drop(i - 1)[0] == c)
         Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
-        # Total identity decision: kind 1 (identity match, no attribute name)
-        # counts; every other kind — including kind 3 (non-truth-evaluable
-        # equality) — does not, and is handled without failure.
         if counts_as_mock(c):
             count = count + 1
         i = i - 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-5631.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection-time helper counts how many of a callable's recorded
  replacement directives stand in for an argument that the test runner will
  supply itself (rather than binding a named attribute). A directive counts
  exactly when it binds no attribute name AND its replacement value is one of
  the framework's well-known replacement-placeholder singletons.

  The membership decision must be made by OBJECT IDENTITY against those
  placeholder singletons — i.e. "is this value that very singleton object" —
  never by value-equality. The reason is robustness: a replacement value may be
  an arbitrary user object whose equality test does not yield a usable boolean
  (for instance an object that, when compared for equality, produces a
  non-scalar or otherwise non-truth-evaluable answer). An identity decision is
  TOTAL: it yields a definite yes/no for every replacement value and can never
  fail on such an object, whereas a value-equality decision can.

  Consequences pinned here:
    * the count is the number of directives that bind no attribute name and
      whose replacement value IS (by identity) a placeholder singleton;
    * a directive that binds an attribute name never counts;
    * a directive whose replacement value is a non-placeholder is excluded;
    * the helper returns a count for EVERY well-formed input and never fails —
      in particular it never fails on a directive whose replacement value has a
      non-truth-evaluable equality.

The directive sequence is modelled as a `List[int]` of per-directive kind tags
(Nagini bans attribute reflection over heterogeneous objects); the kind records
exactly the three observables the helper reads: whether the directive binds an
attribute name, whether its replacement value is a placeholder singleton (by
identity), and whether its replacement value's equality is non-truth-evaluable.
The specification is phrased over `PSeq[int]` via `ToSeq`. The total identity
decision is modelled deeply (a per-tag classifier with no failure path); a
non-truth-evaluable equality is a user-defined exception class (a builtin
exception in an `Exsures` crashes the Nagini translator), and the spec forbids
the helper from ever surfacing it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NonTruthEvaluableEquality(Exception):
    """Raised when a replacement value is compared for VALUE-EQUALITY and the
    comparison does not yield a usable boolean (e.g. it produces a non-scalar
    answer). User-defined stand-in for that failure (a builtin exception in an
    `Exsures` crashes the Nagini translator; mapping.md §2). The desired
    behaviour FORBIDS the helper from ever surfacing this: the membership
    decision is by identity, which is total. The contract below carries no
    `Exsures`, so any implementation whose decision can raise this on an
    admissible input fails to verify."""
    pass


# axioms-start
# (no axiomatized callee: the helper reads only the per-directive observables —
#  attribute-binding, identity-to-a-placeholder, and equality-truth-evaluability
#  — all modelled abstractly as integer kind tags. The membership decision is
#  the changed operation and is modelled DEEPLY (the total identity classifier
#  `counts_as_mock` below), not behind an axiom.)
# axioms-end


# pure-start
# Per-directive kind tags (the only observables the helper reads):
#   0 — binds an attribute name: never counts (and never inspects the value).
#   1 — binds no attribute name; replacement value IS a placeholder singleton
#       (identity match): counts.
#   2 — binds no attribute name; replacement value is a non-placeholder whose
#       equality is a usable boolean: does not count.
#   3 — binds no attribute name; replacement value is a non-placeholder whose
#       equality is NOT truth-evaluable (e.g. a non-scalar comparison result):
#       does not count. An identity decision handles it; a value-equality
#       decision would fail on it.

@Pure
def counts_as_mock(kind: int) -> bool:
    """Whether a single directive of the given kind contributes to the count.
    This is the TOTAL identity decision: it returns a definite boolean for
    EVERY kind, including kind 3 (the non-truth-evaluable-equality value), and
    has no failure path. A directive counts exactly when it binds no attribute
    name (kind != 0) and its replacement value is a placeholder singleton by
    identity (kind == 1)."""
    return kind == 1


@Pure
def count_sentinel_directives(s: PSeq[int]) -> int:
    """The number of directives in the sequence that count, by identity.
    Front-recursive so a single unfold is available to the loop per step."""
    if len(s) == 0:
        return 0
    return (1 if counts_as_mock(s[0]) else 0) + count_sentinel_directives(s.drop(1))
# pure-end


def count_mock_patch_args(kinds: List[int]) -> int:
    # pre-conditions-start
    # `kinds` is the directive sequence, each element a per-directive kind tag
    # in {0,1,2,3} (read-only: the helper does not mutate it).
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                            0 <= kinds[i] and kinds[i] <= 3),
                                     [[kinds[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    # Totality: the helper returns a count for EVERY well-formed input and never
    # surfaces a failure — in particular not on a kind-3 directive (a value with
    # non-truth-evaluable equality). The absence of any `Exsures` on this
    # contract pins that: no exceptional post-state is admissible.
    #
    # The count equals the number of directives that bind no attribute name and
    # whose replacement value is a placeholder singleton by identity (kind 1).
    Ensures(Result() == count_sentinel_directives(ToSeq(kinds)))
    # Soundness of the count as a count: it is non-negative and never exceeds the
    # number of directives (each directive contributes at most one).
    Ensures(0 <= Result() and Result() <= len(kinds))
    # post-conditions-end
    # impl-start
    count = 0
    i = len(kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(0 <= i and i <= len(kinds))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(kinds),
                                                 0 <= kinds[k] and kinds[k] <= 3),
                                          [[kinds[k]]])))
        Invariant(count == count_sentinel_directives(ToSeq(kinds).drop(i)))
        Invariant(0 <= count and count <= len(kinds) - i)
        # invariants-end
        c = kinds[i - 1]
        Assert(ToSeq(kinds).drop(i - 1)[0] == c)
        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
        # Total identity decision: kind 1 (identity match, no attribute name)
        # counts; every other kind — including kind 3 (non-truth-evaluable
        # equality) — does not, and is handled without failure.
        if counts_as_mock(c):
            count = count + 1
        i = i - 1
    return count
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is functionally EXACT: Ensures(Result()==count_sentinel_directives(ToSeq(kinds))) pins the return value pointwise, plus Ensures(0<=Result()<=len(kinds)) and NO Exsures (totality). Any verifying impl must be both pointwise-correct and total.

STEP 1 — 7 same-spec attacks (same-spec exit 0 for all; only impl region edited, axioms/@Pure/Requires/Ensures byte-identical):
 cmd: python -m swebench_unified.adversary weakness nagini pytest-dev__pytest-5631 <atk>
 run concurrently in batches of 3 (JVM+Z3 each).
 - atk_1 PREPATCH BUG (value-equality: raise NonTruthEvaluableEquality on kind 3): exit 2 NOT-A-COUNTEREXAMPLE (verification failed) => prepatch reproduced; spec senses the change via the totality/no-Exsures clause.
 - atk_2 over-count `return len(kinds)`: exit 2 (fails Result==fold).
 - atk_3 under-count `return 0`: exit 2.
 - atk_4 off-by-one `fold()+1`: exit 2 (fails Result==fold and upper bound).
 - atk_5 complement `len - fold`: exit 2 (wrong predicate).
 - atk_6 constant `return 1`: exit 2.
 - atk_7 ECHO of gold (impl uses total identity decision counts_as_mock(c)): exit 0 CANDIDATE (shares spec AND verifies, 11.9s).

STEP 2 — for the ONLY verifying candidate (atk_7), materialized its faithful refined patch and RAN it through the official harness:
 atk_7's impl is the total identity decision (counts kind==1, never raises) — behaviorally the gold identity membership. Faithful refinement = the gold identity patch (compat.py: `p.new in sentinels` -> `p.new is mock_sentinel or p.new is ut_mock_sentinel`).
 run_resolve('pytest-dev__pytest-5631', patch) => RESOLVED: True, note 'resolved'. So the verifying candidate RESOLVES — no verify⇏correct break. (Per current policy a resolving echo of the gold is NOT a weakness.)

Positive control: bash scripts/nagini_verify.sh positive_control.py (verbatim model.py) exit 0 (verifies).

STEP 3 — refinement.md leg audit: legs A1(R), A2(R+I), A3(A-reference), A4(R+I). No consumed @ContractOnly axiom; the CHANGED operation (value-equality -> identity membership) is modelled DEEPLY (counts_as_mock/count_sentinel_directives), not behind an axiom — no kind-3 (unexpressible-changed-op) leg. The single A-reference (A3) correspondence to the real callee num_mock_patch_args @ base_commit cb828ebe is validated out-of-band by axiom_check.py (G-AX): exit 0, 'identity decision total + exact on real unittest.mock.DEFAULT; value-equality membership raises on the NumPy-like value; deep-model count == real identity count over 7 boundary + 20000 fuzz populations.' mapping.md bindings (compat.py:62, patchings<->List[int] kind tags, DEFAULT sentinels) are consistent with patch.diff.

Conclusion: 6 distinct wrong impls (partial-domain: atk_2/3/6; boundary/off-by-one: atk_4; wrong-predicate/ungrounded: atk_5; control-flow-effect/prepatch: atk_1) are all REJECTED by the spec; the one verifying candidate (echo) RESOLVES; positive control verifies; prepatch reproduced; A-reference sound. No same-spec verifying impl whose faithful patch fails to resolve was found. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pytest-dev__pytest-5631.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection-time helper counts how many of a callable's recorded
  replacement directives stand in for an argument that the test runner will
  supply itself (rather than binding a named attribute). A directive counts
  exactly when it binds no attribute name AND its replacement value is one of
  the framework's well-known replacement-placeholder singletons.

  The membership decision must be made by OBJECT IDENTITY against those
  placeholder singletons — i.e. "is this value that very singleton object" —
  never by value-equality. The reason is robustness: a replacement value may be
  an arbitrary user object whose equality test does not yield a usable boolean
  (for instance an object that, when compared for equality, produces a
  non-scalar or otherwise non-truth-evaluable answer). An identity decision is
  TOTAL: it yields a definite yes/no for every replacement value and can never
  fail on such an object, whereas a value-equality decision can.

  Consequences pinned here:
    * the count is the number of directives that bind no attribute name and
      whose replacement value IS (by identity) a placeholder singleton;
    * a directive that binds an attribute name never counts;
    * a directive whose replacement value is a non-placeholder is excluded;
    * the helper returns a count for EVERY well-formed input and never fails —
      in particular it never fails on a directive whose replacement value has a
      non-truth-evaluable equality.

The directive sequence is modelled as a `List[int]` of per-directive kind tags
(Nagini bans attribute reflection over heterogeneous objects); the kind records
exactly the three observables the helper reads: whether the directive binds an
attribute name, whether its replacement value is a placeholder singleton (by
identity), and whether its replacement value's equality is non-truth-evaluable.
The specification is phrased over `PSeq[int]` via `ToSeq`. The total identity
decision is modelled deeply (a per-tag classifier with no failure path); a
non-truth-evaluable equality is a user-defined exception class (a builtin
exception in an `Exsures` crashes the Nagini translator), and the spec forbids
the helper from ever surfacing it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NonTruthEvaluableEquality(Exception):
    """Raised when a replacement value is compared for VALUE-EQUALITY and the
    comparison does not yield a usable boolean (e.g. it produces a non-scalar
    answer). User-defined stand-in for that failure (a builtin exception in an
    `Exsures` crashes the Nagini translator; mapping.md §2). The desired
    behaviour FORBIDS the helper from ever surfacing this: the membership
    decision is by identity, which is total. The contract below carries no
    `Exsures`, so any implementation whose decision can raise this on an
    admissible input fails to verify."""
    pass


# axioms-start
# (no axiomatized callee: the helper reads only the per-directive observables —
#  attribute-binding, identity-to-a-placeholder, and equality-truth-evaluability
#  — all modelled abstractly as integer kind tags. The membership decision is
#  the changed operation and is modelled DEEPLY (the total identity classifier
#  `counts_as_mock` below), not behind an axiom.)
# axioms-end


# pure-start
# Per-directive kind tags (the only observables the helper reads):
#   0 — binds an attribute name: never counts (and never inspects the value).
#   1 — binds no attribute name; replacement value IS a placeholder singleton
#       (identity match): counts.
#   2 — binds no attribute name; replacement value is a non-placeholder whose
#       equality is a usable boolean: does not count.
#   3 — binds no attribute name; replacement value is a non-placeholder whose
#       equality is NOT truth-evaluable (e.g. a non-scalar comparison result):
#       does not count. An identity decision handles it; a value-equality
#       decision would fail on it.

@Pure
def counts_as_mock(kind: int) -> bool:
    """Whether a single directive of the given kind contributes to the count.
    This is the TOTAL identity decision: it returns a definite boolean for
    EVERY kind, including kind 3 (the non-truth-evaluable-equality value), and
    has no failure path. A directive counts exactly when it binds no attribute
    name (kind != 0) and its replacement value is a placeholder singleton by
    identity (kind == 1)."""
    return kind == 1


@Pure
def count_sentinel_directives(s: PSeq[int]) -> int:
    """The number of directives in the sequence that count, by identity.
    Front-recursive so a single unfold is available to the loop per step."""
    if len(s) == 0:
        return 0
    return (1 if counts_as_mock(s[0]) else 0) + count_sentinel_directives(s.drop(1))
# pure-end


def count_mock_patch_args(kinds: List[int]) -> int:
    # pre-conditions-start
    # `kinds` is the directive sequence, each element a per-directive kind tag
    # in {0,1,2,3} (read-only: the helper does not mutate it).
    Requires(Acc(list_pred(kinds), 1 / 2))
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(kinds),
                                            0 <= kinds[i] and kinds[i] <= 3),
                                     [[kinds[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kinds), 1 / 2))
    # Totality: the helper returns a count for EVERY well-formed input and never
    # surfaces a failure — in particular not on a kind-3 directive (a value with
    # non-truth-evaluable equality). The absence of any `Exsures` on this
    # contract pins that: no exceptional post-state is admissible.
    #
    # The count equals the number of directives that bind no attribute name and
    # whose replacement value is a placeholder singleton by identity (kind 1).
    Ensures(Result() == count_sentinel_directives(ToSeq(kinds)))
    # Soundness of the count as a count: it is non-negative and never exceeds the
    # number of directives (each directive contributes at most one).
    Ensures(0 <= Result() and Result() <= len(kinds))
    # post-conditions-end
    # impl-start
    count = 0
    i = len(kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(kinds), 1 / 2))
        Invariant(0 <= i and i <= len(kinds))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(kinds),
                                                 0 <= kinds[k] and kinds[k] <= 3),
                                          [[kinds[k]]])))
        Invariant(count == count_sentinel_directives(ToSeq(kinds).drop(i)))
        Invariant(0 <= count and count <= len(kinds) - i)
        # invariants-end
        c = kinds[i - 1]
        Assert(ToSeq(kinds).drop(i - 1)[0] == c)
        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))
        # Total identity decision: kind 1 (identity match, no attribute name)
        # counts; every other kind — including kind 3 (non-truth-evaluable
        # equality) — does not, and is handled without failure.
        if counts_as_mock(c):
            count = count + 1
        i = i - 1
    return count
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is functionally EXACT: Ensures(Result()==count_sentinel_directives(ToSeq(kinds))) pins the return value pointwise, plus Ensures(0<=Result()<=len(kinds)) and NO Exsures (totality). Any verifying impl must be both pointwise-correct and total.

STEP 1 — 7 same-spec attacks (same-spec exit 0 for all; only impl region edited, axioms/@Pure/Requires/Ensures byte-identical):
 cmd: python -m swebench_unified.adversary weakness nagini pytest-dev__pytest-5631 <atk>
 run concurrently in batches of 3 (JVM+Z3 each).
 - atk_1 PREPATCH BUG (value-equality: raise NonTruthEvaluableEquality on kind 3): exit 2 NOT-A-COUNTEREXAMPLE (verification failed) => prepatch reproduced; spec senses the change via the totality/no-Exsures clause.
 - atk_2 over-count `return len(kinds)`: exit 2 (fails Result==fold).
 - atk_3 under-count `return 0`: exit 2.
 - atk_4 off-by-one `fold()+1`: exit 2 (fails Result==fold and upper bound).
 - atk_5 complement `len - fold`: exit 2 (wrong predicate).
 - atk_6 constant `return 1`: exit 2.
 - atk_7 ECHO of gold (impl uses total identity decision counts_as_mock(c)): exit 0 CANDIDATE (shares spec AND verifies, 11.9s).

STEP 2 — for the ONLY verifying candidate (atk_7), materialized its faithful refined patch and RAN it through the official harness:
 atk_7's impl is the total identity decision (counts kind==1, never raises) — behaviorally the gold identity membership. Faithful refinement = the gold identity patch (compat.py: `p.new in sentinels` -> `p.new is mock_sentinel or p.new is ut_mock_sentinel`).
 run_resolve('pytest-dev__pytest-5631', patch) => RESOLVED: True, note 'resolved'. So the verifying candidate RESOLVES — no verify⇏correct break. (Per current policy a resolving echo of the gold is NOT a weakness.)

Positive control: bash scripts/nagini_verify.sh positive_control.py (verbatim model.py) exit 0 (verifies).

STEP 3 — refinement.md leg audit: legs A1(R), A2(R+I), A3(A-reference), A4(R+I). No consumed @ContractOnly axiom; the CHANGED operation (value-equality -> identity membership) is modelled DEEPLY (counts_as_mock/count_sentinel_directives), not behind an axiom — no kind-3 (unexpressible-changed-op) leg. The single A-reference (A3) correspondence to the real callee num_mock_patch_args @ base_commit cb828ebe is validated out-of-band by axiom_check.py (G-AX): exit 0, 'identity decision total + exact on real unittest.mock.DEFAULT; value-equality membership raises on the NumPy-like value; deep-model count == real identity count over 7 boundary + 20000 fuzz populations.' mapping.md bindings (compat.py:62, patchings<->List[int] kind tags, DEFAULT sentinels) are consistent with patch.diff.

Conclusion: 6 distinct wrong impls (partial-domain: atk_2/3/6; boundary/off-by-one: atk_4; wrong-predicate/ungrounded: atk_5; control-flow-effect/prepatch: atk_1) are all REJECTED by the spec; the one verifying candidate (echo) RESOLVES; positive control verifies; prepatch reproduced; A-reference sound. No same-spec verifying impl whose faithful patch fails to resolve was found. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for pytest-dev__pytest-5631 (nagini). No divergence found between the modeled function and the real post-patch callee num_mock_patch_args (src/_pytest/compat.py, base_commit cb828ebe).

Real post-patch callee: patchings=getattr(function,'patchings',None); if not patchings: return 0; mock_sentinel=getattr(sys.modules.get('mock'),'DEFAULT',object()); ut_mock_sentinel=getattr(sys.modules.get('unittest.mock'),'DEFAULT',object()); return len([p for p in patchings if not p.attribute_name and (p.new is mock_sentinel or p.new is ut_mock_sentinel)]).

Machine facts:
- model.py verifies under pinned Nagini: exit 0, 11.02s.
- axiom_check.py (G-AX) passes: exit 0 over 7 boundary + 20000 fuzz populations; identity decision total+exact on real unittest.mock.DEFAULT, and pre-patch value-equality membership raises on NumpyLike while identity does not.
- Independent differential fuzz (my own, 300000 adversarial populations, inlined verbatim post-patch callee vs contract-stripped model over kind tags): ZERO divergence. Adversarial value pool included: real sentinels, NonTruthEvaluable (__eq__ raises), plain object(), an object whose __eq__ returns True for everything, an object whose __eq__ returns a non-bool list, um.sentinel.OTHER (distinct sentinel), empty-string attribute names, plus scalars. Model count == real identity count on every population, with 0<=count<=len.
- Totality check: post-patch uses `is` (identity), which never invokes __eq__ and never raises even on the NumpyLike/NonTruthEvaluable value; attribute_name is str|None (truth-evaluable). Confirmed no failure path over the modeled domain, so the contract carrying no Exsures is faithful (not spec-too-strong).

Abstraction fidelity (R-refinement patchings->List[int] kind tags): the partition {0,1,2,3} is total and exhaustive over real directives (0: attribute_name truthy, short-circuit, value not inspected; 1: no attr + p.new IS a sentinel by identity; 2: no attr + comparable non-sentinel; 3: no attr + non-truth-evaluable __eq__). Real count = #{kind==1} = count_sentinel_directives. The kind-1/kind-2 boundary is faithful: identity coincides with value-equality only for DEFAULT itself. Attribute-bound + sentinel value maps to kind 0 (short-circuit), which does not count -- consistent with `not p.attribute_name` short-circuit. Unloaded-module fallback (fresh object()) yields count 0, equivalent to no kind-1 directives.

Conclusion: the spec is an exact, faithful refinement of the gold post-patch behavior; no diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view rendered via markers.spec_view(nagini); impl+proof elided cleanly; same-spec on verbatim model returns exit 0 (SAME). hints_text is EMPTY, so comparison is only against the public problem_statement.

Public problem_statement already discloses (verbatim from dataset): the bug is `p.new in sentinels` (value-equality membership) raising `ValueError: The truth value of an array with more than one element is ambiguous` when p.new is a NumPy array; it names the exact traceback frame `_pytest/compat.py:93-94`, function `num_mock_patch_args`, the exact listcomp `if not p.attribute_name and p.new in sentinels`, links the introducing commit, and spells out the root cause ('p.new in sentinels returns an array of booleans instead of a boolean which causes the ValueError'). So value-equality membership on an array being the defect is already fully public, at the exact location.

Gold edit: `p.new in sentinels` -> `p.new is mock_sentinel or p.new is ut_mock_sentinel`.

Spec-view contents: fully abstracted over a `List[int]` of per-directive kind tags {0,1,2,3}. Carries NO repo identifiers (no compat.py, num_mock_patch_args, sys.modules, mock.DEFAULT, patchings, attribute_name) and no diff text. Fix-adjacent prose: 'The membership decision must be made by OBJECT IDENTITY ... never by value-equality' plus the totality clause 'never fails on a directive whose replacement value has a non-truth-evaluable equality.' Both are legitimate BEHAVIORAL semantics a spec must pin, and the never-raise-on-non-truth-evaluable-equality requirement is literally the problem_statement's own reported symptom restated as desired behavior.

No gold reconstruction: a solver seeing only the abstract spec view implements a count over integer kind tags; the abstraction strips all repo location/form info the compat.py diff needs, so nothing about the gold edit's location or form is recoverable beyond the public issue. Repo-specific bindings (compat.py, DEFAULT sentinels, patchings) live only in mapping.md / refinement.md, which are NOT part of the consumer spec view. Recorded G-PANEL-3 verdict confirmed sound.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
