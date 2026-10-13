# P2 adversarial audit — django__django-14765

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_echo.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,12 +99,11 @@
         empty = []  # type: List[int]
         return empty
     if not is_expected_kind:
+        # ATTACK (prior pass's BROKEN witness): unbounded self-recursion in
+        # place of the pinned raise. Partial correctness alone cannot see this.
+        spare = []  # type: List[int]
+        again = build_state(spare, present, is_expected_kind)
         raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
     result = []  # type: List[int]
     i = 0
     while i < len(real_apps):
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,12 +99,16 @@
         empty = []  # type: List[int]
         return empty
     if not is_expected_kind:
+        # ATTACK: diverge instead of raising, via a bare unbounded loop whose
+        # invariants region deliberately omits any MustTerminate measure.
+        spin = 0
+        while True:
+            # invariants-start
+            Invariant(Acc(list_pred(real_apps), 1 / 2))
+            Invariant(spin >= 0)
+            # invariants-end
+            spin = spin + 1
         raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
     result = []  # type: List[int]
     i = 0
     while i < len(real_apps):
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -100,11 +100,6 @@
         return empty
     if not is_expected_kind:
         raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
     result = []  # type: List[int]
     i = 0
     while i < len(real_apps):
@@ -113,10 +108,9 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(real_apps))
         Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
-        Invariant(MustTerminate(len(real_apps) - i + 1))
         # invariants-end
-        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
-        result.append(real_apps[i])
-        i = i + 1
+        # ATTACK: `i` is never incremented -> the store path diverges for every
+        # non-empty present-and-expected collection. No loop measure is stated.
+        Assert(0 <= i)
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,12 +99,12 @@
         empty = []  # type: List[int]
         return empty
     if not is_expected_kind:
-        raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
+        # ATTACK (partial domain): only a NON-EMPTY off-kind collection fails;
+        # an empty off-kind collection is quietly accepted as empty.
+        if len(real_apps) > 0:
+            raise OffKindCollection()
+        empty2 = []  # type: List[int]
+        return empty2
     result = []  # type: List[int]
     i = 0
     while i < len(real_apps):
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -100,14 +100,11 @@
         return empty
     if not is_expected_kind:
         raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
     result = []  # type: List[int]
     i = 0
-    while i < len(real_apps):
+    # ATTACK (boundary): stop one short -> the last supplied label is dropped
+    # from the stored collection.
+    while i + 1 < len(real_apps):
         # invariants-start
         Invariant(Acc(list_pred(real_apps), 1 / 2))
         Invariant(Acc(list_pred(result)))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,16 +95,14 @@
             Acc(list_pred(real_apps), 1 / 2) and present and not is_expected_kind)
     # post-conditions-end
     # impl-start
+    # ATTACK (control-flow effect): the kind test is applied unconditionally,
+    # i.e. the absent-collection guard is gone, so an ABSENT collection also
+    # fails instead of yielding the empty stored collection.
+    if not is_expected_kind:
+        raise OffKindCollection()
     if not present:
         empty = []  # type: List[int]
         return empty
-    if not is_expected_kind:
-        raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
     result = []  # type: List[int]
     i = 0
     while i < len(real_apps):
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,12 +99,10 @@
         empty = []  # type: List[int]
         return empty
     if not is_expected_kind:
-        raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
+        # ATTACK: silent coercion of the off-kind collection (the very thing
+        # the desired behaviour forbids) instead of the internal-contract
+        # violation -- a normal return carrying the coerced membership.
+        pass
     result = []  # type: List[int]
     i = 0
     while i < len(real_apps):
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -99,12 +99,9 @@
         empty = []  # type: List[int]
         return empty
     if not is_expected_kind:
-        raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
+        # ATTACK (exception type): fail with an exception the spec never pins,
+        # instead of the internal-contract violation OffKindCollection.
+        raise ValueError()
     result = []  # type: List[int]
     i = 0
     while i < len(real_apps):
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -100,20 +100,20 @@
         return empty
     if not is_expected_kind:
         raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
+    # A4 PROBE: build a FRESH collection with identical membership (exactly the
+    # 'copy' side of refinement.md A4). Restructured (append-then-advance split
+    # across an explicit bound) so this file is not byte-identical to model.py.
+    n = len(real_apps)
     result = []  # type: List[int]
     i = 0
-    while i < len(real_apps):
+    while i < n:
         # invariants-start
         Invariant(Acc(list_pred(real_apps), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(real_apps))
+        Invariant(n == len(real_apps))
+        Invariant(0 <= i and i <= n)
         Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
-        Invariant(MustTerminate(len(real_apps) - i + 1))
+        Invariant(MustTerminate(n - i + 1))
         # invariants-end
         Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
         result.append(real_apps[i])
```

Attack 10 — `atk_echo.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,28 +95,36 @@
             Acc(list_pred(real_apps), 1 / 2) and present and not is_expected_kind)
     # post-conditions-end
     # impl-start
+    if present and not is_expected_kind:
+        if len(real_apps) > 0:
+            shorter = []  # type: List[int]
+            j = 0
+            while j + 1 < len(real_apps):
+                # invariants-start
+                Invariant(Acc(list_pred(real_apps), 1 / 2))
+                Invariant(Acc(list_pred(shorter)))
+                Invariant(0 <= j and j <= len(real_apps))
+                Invariant(len(shorter) == j)
+                Invariant(MustTerminate(len(real_apps) - j + 1))
+                # invariants-end
+                shorter.append(real_apps[j])
+                j = j + 1
+            echoed = build_state(shorter, present, is_expected_kind)
+        raise OffKindCollection()
+    out = []  # type: List[int]
     if not present:
-        empty = []  # type: List[int]
-        return empty
-    if not is_expected_kind:
-        raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
-    result = []  # type: List[int]
-    i = 0
-    while i < len(real_apps):
+        return out
+    k = 0
+    while k < len(real_apps):
         # invariants-start
         Invariant(Acc(list_pred(real_apps), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(real_apps))
-        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
-        Invariant(MustTerminate(len(real_apps) - i + 1))
+        Invariant(Acc(list_pred(out)))
+        Invariant(0 <= k and k <= len(real_apps))
+        Invariant(ToSeq(out) == ToSeq(real_apps).take(k))
+        Invariant(MustTerminate(len(real_apps) - k + 1))
         # invariants-end
-        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
-        result.append(real_apps[i])
-        i = i + 1
-    return result
+        Assert(ToSeq(real_apps).take(k + 1).drop(k)[0] == real_apps[k])
+        out.append(real_apps[k])
+        k = k + 1
+    return out
     # impl-end
```

Attack 11 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -95,28 +95,23 @@
             Acc(list_pred(real_apps), 1 / 2) and present and not is_expected_kind)
     # post-conditions-end
     # impl-start
-    if not present:
-        empty = []  # type: List[int]
-        return empty
-    if not is_expected_kind:
-        raise OffKindCollection()
-    # Present-and-expected: the stored collection preserves the supplied
-    # membership unchanged. Materialised here as a same-membership sequence so
-    # the result carries full permission while the input stays read-only
-    # (refinement.md: the real store is by reference, contents preserved — an
-    # R-refinement of object identity to membership equality).
-    result = []  # type: List[int]
-    i = 0
-    while i < len(real_apps):
-        # invariants-start
-        Invariant(Acc(list_pred(real_apps), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(real_apps))
-        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
-        Invariant(MustTerminate(len(real_apps) - i + 1))
-        # invariants-end
-        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
-        result.append(real_apps[i])
-        i = i + 1
-    return result
+    # ATTACK = the PRE-PATCH behaviour: `if real_apps:` truthiness, then coerce
+    # an off-kind collection into the expected kind instead of failing.
+    if present and len(real_apps) > 0:
+        result = []  # type: List[int]
+        i = 0
+        while i < len(real_apps):
+            # invariants-start
+            Invariant(Acc(list_pred(real_apps), 1 / 2))
+            Invariant(Acc(list_pred(result)))
+            Invariant(0 <= i and i <= len(real_apps))
+            Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
+            Invariant(MustTerminate(len(real_apps) - i + 1))
+            # invariants-end
+            Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
+            result.append(real_apps[i])
+            i = i + 1
+        return result
+    empty = []  # type: List[int]
+    return empty
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14765.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A state container is constructed from an optional collection of auxiliary
  app labels. The collection is supplied through an internal construction API,
  so the container imposes a TYPE DISCIPLINE on it rather than silently
  accommodating any shape:

    * when the collection is ABSENT, the container holds an empty collection;
    * when the collection is PRESENT and is already the expected unordered
      collection kind (a set), the container holds exactly that collection,
      with its membership preserved unchanged — no copy or coercion alters it;
    * when the collection is PRESENT but is NOT the expected kind (for example
      an ordered list), construction must FAIL — the container does not quietly
      convert an off-kind collection into the expected kind. The failure is
      reported to the caller as an internal-contract violation.

  The behaviour pinned here is exactly that discipline: normal construction is
  reachable only for an absent collection or one that is already the expected
  kind, and the stored collection then equals (absent ⇒ empty; present-and-
  expected ⇒ the supplied membership). A present collection that is not the
  expected kind produces the failure and never a coerced result.

The auxiliary-app-label collection is modelled as a `List[int]` of label code
points together with a boolean `present` (absent ⟺ ``not present``, in which
case the list contents are irrelevant); Nagini bans `str` indexing, and the
discriminating observable is purely WHICH outcome construction produces and
WHAT membership it stores, not the labels' characters. A second boolean models
whether a present collection is already the expected kind (the runtime kind
test). The off-kind construction failure is a user-defined exception class (a
builtin exception in an `Exsures` crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class OffKindCollection(Exception):
    """Signals that a present auxiliary-app-label collection is NOT the expected
    unordered kind, so construction must fail rather than coerce it. User-defined
    stand-in for the internal-contract violation the desired behaviour raises; a
    builtin exception in an `Exsures` crashes the Nagini translator (mapping.md
    §2)."""

# axioms-start
# (no callee is axiomatized: the construction's decision and store are spelled
# out directly over the modelled collection; there is no unchanged library
# callee inside the changed operation.)
# axioms-end

# pure-start
# (no module-level pure helpers required: the stored membership is stated
# inline as the supplied sequence on the present-and-expected path and the
# empty sequence on the absent path.)
# pure-end

def build_state(real_apps: List[int], present: bool, is_expected_kind: bool) -> List[int]:
    # pre-conditions-start
    # The supplied collection is read-only here (construction stores it by
    # reference when it is the expected kind; it is never mutated). Fractional
    # permission, required and ensured, so no caller can satisfy a postcondition
    # vacuously by overwriting the input.
    Requires(Acc(list_pred(real_apps), 1 / 2))
    # Construction always COMPLETES: it reaches one of its two outcomes (a
    # normally-returned stored collection, or the internal-contract violation)
    # in finitely many steps, within a budget bounded by the size of the
    # supplied collection. It never diverges — neither outcome may be evaded by
    # running forever, on ANY admissible input (absent, present-and-expected, or
    # present-and-off-kind). Without this, a non-terminating construction would
    # discharge every clause below vacuously by never reaching an outcome.
    Requires(MustTerminate(len(real_apps) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(real_apps), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Normal construction is reachable ONLY for an absent collection or one that
    # is already the expected kind. A present off-kind collection must NOT
    # return normally (it raises below) — never a coerced result.
    Ensures((not present) or is_expected_kind)
    # Stored membership: absent ⇒ empty; present-and-expected ⇒ exactly the
    # supplied membership, preserved unchanged (no copy or coercion alters it).
    Ensures(Implies(not present, len(Result()) == 0))
    Ensures(Implies(present and is_expected_kind,
                    ToSeq(Result()) == ToSeq(real_apps)))
    # The pinned failure: a present collection that is not the expected kind
    # raises the internal-contract violation and ONLY that, for EVERY such
    # collection (whether empty or non-empty), never a coerced result.
    Exsures(OffKindCollection,
            Acc(list_pred(real_apps), 1 / 2) and present and not is_expected_kind)
    # post-conditions-end
    # impl-start
    if not present:
        empty = []  # type: List[int]
        return empty
    if not is_expected_kind:
        raise OffKindCollection()
    # Present-and-expected: the stored collection preserves the supplied
    # membership unchanged. Materialised here as a same-membership sequence so
    # the result carries full permission while the input stays read-only
    # (refinement.md: the real store is by reference, contents preserved — an
    # R-refinement of object identity to membership equality).
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) re-audit of django__django-14765/nagini. NOTE: meta.json carries a STALE G-EQ=fail/BROKEN verdict naming atk_1.py; model.py has since been REPAIRED (region_hashes impl/pre-conditions changed) by adding a METHOD-LEVEL `Requires(MustTerminate(len(real_apps) + 2))` plus `from nagini_contracts.obligations import MustTerminate` and a loop `Invariant(MustTerminate(len(real_apps) - i + 1))`. I re-encoded the prior counterexample verbatim and it is now REJECTED, so the repair closes the hole it named.

SETUP. Attacks generated by gen.py, which substitutes ONLY the text between `    # impl-start` and `    # impl-end`; docstring/imports/OffKindCollection/axioms/pure/Requires/Ensures/Exsures preserved byte-for-byte (verified: `diff` of lines 1-97 and of the tail vs base_model.py = identical).

SAME-SPEC (`python -m swebench_unified.adversary same-spec nagini django__django-14765 <f>`): all 11 attacks + pos_control => exit 0 (SAME, byte-identical spec signature).

WEAKNESS (`python -m swebench_unified.adversary weakness nagini django__django-14765 <f>`), run 3-at-a-time as background jobs (each spawns JVM+Z3); logs at $D/w_<name>.log:
- atk_1.py (A-leg/termination, PRIOR PASS'S NAMED COUNTEREXAMPLE re-encoded: unbounded SELF-RECURSION `build_state(spare, present, is_expected_kind)` on the present-off-kind path in place of the pinned raise): exit 2, DOES NOT VERIFY. The repair's method-level MustTerminate rejects it. This is the decisive regression check.
- atk_2.py (termination, other divergence encoding: `while True` on the off-kind path, fresh loop whose invariants region deliberately omits any measure): exit 2, does not verify.
- atk_3.py (CONTROL-FLOW-EFFECT / store-path divergence: copy loop never increments `i`, loop MustTerminate invariant deleted -- probes whether the METHOD-level measure alone rejects loop divergence, since the invariants region is attacker-owned): exit 2, does not verify.
- atk_4.py (PARTIAL-DOMAIN: raise pinned only for a NON-EMPTY off-kind collection; an empty off-kind `[]` quietly accepted as empty -- the exact residue of the pre-patch truthiness test): exit 2, does not verify.
- atk_5.py (BOUNDARY off-by-one: present-and-expected path drops the LAST label, `while i + 1 < len(...)`): exit 2, does not verify.
- atk_6.py (CONTROL-FLOW-EFFECT: absent-guard removed so the kind test also fires for the ABSENT input -> plain `ProjectState()` would assert): exit 2, does not verify.
- atk_7.py (UNGROUNDED-ORACLE ECHO analogue: off-kind collection SILENTLY COERCED and returned normally -- the pre-patch behaviour on the discriminating path only): exit 2, does not verify.
- atk_8.py (EXCEPTION-TYPE: off-kind path raises `ValueError()` instead of the pinned OffKindCollection, i.e. faithful patch raises a non-AssertionError the F2P `assertRaises(AssertionError)` would not catch): exit 2, does not verify.
- atk_prepatch.py (THE PRE-PATCH BUG re-encoded: `if present and len(real_apps) > 0: copy-and-return`): exit 2, DOES NOT VERIFY => PREPATCH REPRODUCED; `Ensures((not present) or is_expected_kind)` sees the fix (G-DIFF confirmed independently).
- atk_echo.py (intended echo control, fused decisions + bounded depth-1 self-call): exit 2, does not verify -- rejected for an OBLIGATION-LEAK reason, not a behavioural one: `bash scripts/nagini_verify.sh` gives `atk_echo.py:112: Obligation leak check failed. Callee build_state might not take all unsatisfied obligations from the caller.` That is a construction artifact of my own guarded self-call under the new method-level measure, not evidence about the spec; superseded by atk_9 as the echo control.
- atk_9.py (A4-LEG PROBE, the deep model<->patch correspondence step): restructured copy loop with an explicit bound `n = len(real_apps)`. Exit 0 = CANDIDATE (shares spec AND VERIFIES, 12.9s).

MANDATORY RESOLVE RUN for the one CANDIDATE. atk_9 exists to test refinement.md A4 / mapping.md section 2, the only non-trivial R/identity leg: model.py RETURNS A FRESH List[int] while the gold patch STORES BY REFERENCE (`self.real_apps = real_apps`), with A4 justifying that as "object identity refines to membership equality". atk_9's faithful patch is the LITERAL reading of that leg -- `self.real_apps = set(real_apps)`, a copy. Materialized at $D/patch_atk_9.diff; `git apply --check` at base_commit 4e8121e8e42a24acc3565851c9ef50ca8322b15c => rc=0.

Executed `run_resolve('django__django-14765', patch_atk_9.diff, run_id='sbu-eq-audit-d7po0y-atk9', timeout=1800)`; log $D/resolve_atk_9.log: completed=TRUE, resolved=TRUE, attempts=1, flaky=false, patch_successfully_applied=true, FAIL_TO_PASS success=['test_real_apps_non_set'], failure=[]; PASS_TO_PASS 63/63 success, 0 failures; PASS_TO_FAIL empty. So the ONLY verifying rival RESOLVES => it is a correct alternative implementation (an echo), NOT a spec weakness, per architecture.md section 6. This run also serves as the live proof that the resolve pipeline reaches real verdicts in this pass (the prior pass's INCONCLUSIVE risk was a hung runner).

POSITIVE CONTROL: `bash scripts/nagini_verify.sh $D/pos_control.py` (= model.py verbatim) => 'Verification successful', 11.32s, exit 0.

A-LEG / refinement.md AUDIT (my assigned focus). refinement.md sections B and mapping.md section 3 both declare NO axiomatized callee and NO deep-model reference; axioms and pure regions are comment-only; meta.json has axioms=[] and deep_model_references=[]; G-AX is a stamped skip with reason 'no axiom_check.py (no axioms in bundle)'. I confirmed this is correct rather than an evasion: the changed body is only Python control flow + `isinstance(real_apps, set)` + `assert` + an attribute store, none of which is an opaque callee. Modeling `isinstance` as the boolean `is_expected_kind` (A1/A3, tagged R) is the right call -- it is part of the decision UNDER CHANGE, so axiomatizing it would be assuming the thing to be proved; and it is not left ungrounded, since G-CONF drives the real `ProjectState.__init__` over the whole kind x membership domain (100021 inputs, 0 disagreements, incl. a `set` SUBCLASS, `frozenset`, tuple, dict, str, int, bare object). Every leg is R / R+I / I; there is no kind-3 step, and no leg is A-consumed or A-reference, so the 'no kind-3' claim in section B holds.

A4 correspondence, checked against the repo at base_commit (the one leg that could hide a defect): the model's copy-vs-gold's-alias gap is observationally sound because identity of the stored set is never observed. `git grep` over django/ and tests/ at base_commit finds (a) NO `real_apps is`/`id(real_apps)` identity test anywhere, and (b) NO in-place mutation of a stored set: zero hits for `real_apps.(add|remove|discard|update|clear|pop)`. All consumers observe MEMBERSHIP only -- `state.py:365,373` (`not in self.real_apps`), `:425` `StateApps(self.real_apps, ...)` which iterates and sorts, `:437` `__eq__` comparing by `==`, `:412` clone re-passing it, `autodetector.py:137,147` membership tests.

The one real behavioural difference the patch introduces in the aliasing dimension (pre-patch `if real_apps:` builds a FRESH set for an empty-set argument, post-patch stores the caller's object) is membership-identical and only observable through later caller-side mutation, which no call site does -- `loader.py` finishes populating `unmigrated_apps` (lines 77-102) BEFORE `executor.py:69` hands it to ProjectState. The empirical seal is atk_9: the copy patch resolves 64/64, so the copy/alias distinction is genuinely unobservable on the tested behaviour and A4's R-tag is honest, not a papered-over kind-3.

CONCLUSION: 11 same-spec attacks encoded and machine-verified; 10 wrong impls REJECTED by the spec (incl. the prior pass's BROKEN witness and the pre-patch bug); the single CANDIDATE (atk_9) had its faithful patch materialized and RUN through the official harness, where it RESOLVED (completed=true, resolved=true, F2P pass, 63/63 P2P) -- an echo, correctly not a weakness. Positive control verifies. No verifying wrong impl exists whose faithful patch fails to resolve. VERDICT: SOUND. Actionable side note for the runner, not a G-EQ defect: meta.json's recorded G-EQ (and G-PANEL-1/G-PANEL) verdicts predate the MustTerminate repair and now contradict the artifact; they should be re-derived from this pass.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_echo.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_echo.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14765.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A state container is constructed from an optional collection of auxiliary
  app labels. The collection is supplied through an internal construction API,
  so the container imposes a TYPE DISCIPLINE on it rather than silently
  accommodating any shape:

    * when the collection is ABSENT, the container holds an empty collection;
    * when the collection is PRESENT and is already the expected unordered
      collection kind (a set), the container holds exactly that collection,
      with its membership preserved unchanged — no copy or coercion alters it;
    * when the collection is PRESENT but is NOT the expected kind (for example
      an ordered list), construction must FAIL — the container does not quietly
      convert an off-kind collection into the expected kind. The failure is
      reported to the caller as an internal-contract violation.

  The behaviour pinned here is exactly that discipline: normal construction is
  reachable only for an absent collection or one that is already the expected
  kind, and the stored collection then equals (absent ⇒ empty; present-and-
  expected ⇒ the supplied membership). A present collection that is not the
  expected kind produces the failure and never a coerced result.

The auxiliary-app-label collection is modelled as a `List[int]` of label code
points together with a boolean `present` (absent ⟺ ``not present``, in which
case the list contents are irrelevant); Nagini bans `str` indexing, and the
discriminating observable is purely WHICH outcome construction produces and
WHAT membership it stores, not the labels' characters. A second boolean models
whether a present collection is already the expected kind (the runtime kind
test). The off-kind construction failure is a user-defined exception class (a
builtin exception in an `Exsures` crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class OffKindCollection(Exception):
    """Signals that a present auxiliary-app-label collection is NOT the expected
    unordered kind, so construction must fail rather than coerce it. User-defined
    stand-in for the internal-contract violation the desired behaviour raises; a
    builtin exception in an `Exsures` crashes the Nagini translator (mapping.md
    §2)."""

# axioms-start
# (no callee is axiomatized: the construction's decision and store are spelled
# out directly over the modelled collection; there is no unchanged library
# callee inside the changed operation.)
# axioms-end

# pure-start
# (no module-level pure helpers required: the stored membership is stated
# inline as the supplied sequence on the present-and-expected path and the
# empty sequence on the absent path.)
# pure-end

def build_state(real_apps: List[int], present: bool, is_expected_kind: bool) -> List[int]:
    # pre-conditions-start
    # The supplied collection is read-only here (construction stores it by
    # reference when it is the expected kind; it is never mutated). Fractional
    # permission, required and ensured, so no caller can satisfy a postcondition
    # vacuously by overwriting the input.
    Requires(Acc(list_pred(real_apps), 1 / 2))
    # Construction always COMPLETES: it reaches one of its two outcomes (a
    # normally-returned stored collection, or the internal-contract violation)
    # in finitely many steps, within a budget bounded by the size of the
    # supplied collection. It never diverges — neither outcome may be evaded by
    # running forever, on ANY admissible input (absent, present-and-expected, or
    # present-and-off-kind). Without this, a non-terminating construction would
    # discharge every clause below vacuously by never reaching an outcome.
    Requires(MustTerminate(len(real_apps) + 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(real_apps), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Normal construction is reachable ONLY for an absent collection or one that
    # is already the expected kind. A present off-kind collection must NOT
    # return normally (it raises below) — never a coerced result.
    Ensures((not present) or is_expected_kind)
    # Stored membership: absent ⇒ empty; present-and-expected ⇒ exactly the
    # supplied membership, preserved unchanged (no copy or coercion alters it).
    Ensures(Implies(not present, len(Result()) == 0))
    Ensures(Implies(present and is_expected_kind,
                    ToSeq(Result()) == ToSeq(real_apps)))
    # The pinned failure: a present collection that is not the expected kind
    # raises the internal-contract violation and ONLY that, for EVERY such
    # collection (whether empty or non-empty), never a coerced result.
    Exsures(OffKindCollection,
            Acc(list_pred(real_apps), 1 / 2) and present and not is_expected_kind)
    # post-conditions-end
    # impl-start
    if not present:
        empty = []  # type: List[int]
        return empty
    if not is_expected_kind:
        raise OffKindCollection()
    # Present-and-expected: the stored collection preserves the supplied
    # membership unchanged. Materialised here as a same-membership sequence so
    # the result carries full permission while the input stays read-only
    # (refinement.md: the real store is by reference, contents preserved — an
    # R-refinement of object identity to membership equality).
    result = []  # type: List[int]
    i = 0
    while i < len(real_apps):
        # invariants-start
        Invariant(Acc(list_pred(real_apps), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(real_apps))
        Invariant(ToSeq(result) == ToSeq(real_apps).take(i))
        Invariant(MustTerminate(len(real_apps) - i + 1))
        # invariants-end
        Assert(ToSeq(real_apps).take(i + 1).drop(i)[0] == real_apps[i])
        result.append(real_apps[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) re-audit of django__django-14765/nagini. NOTE: meta.json carries a STALE G-EQ=fail/BROKEN verdict naming atk_1.py; model.py has since been REPAIRED (region_hashes impl/pre-conditions changed) by adding a METHOD-LEVEL `Requires(MustTerminate(len(real_apps) + 2))` plus `from nagini_contracts.obligations import MustTerminate` and a loop `Invariant(MustTerminate(len(real_apps) - i + 1))`. I re-encoded the prior counterexample verbatim and it is now REJECTED, so the repair closes the hole it named.

SETUP. Attacks generated by gen.py, which substitutes ONLY the text between `    # impl-start` and `    # impl-end`; docstring/imports/OffKindCollection/axioms/pure/Requires/Ensures/Exsures preserved byte-for-byte (verified: `diff` of lines 1-97 and of the tail vs base_model.py = identical).

SAME-SPEC (`python -m swebench_unified.adversary same-spec nagini django__django-14765 <f>`): all 11 attacks + pos_control => exit 0 (SAME, byte-identical spec signature).

WEAKNESS (`python -m swebench_unified.adversary weakness nagini django__django-14765 <f>`), run 3-at-a-time as background jobs (each spawns JVM+Z3); logs at $D/w_<name>.log:
- atk_1.py (A-leg/termination, PRIOR PASS'S NAMED COUNTEREXAMPLE re-encoded: unbounded SELF-RECURSION `build_state(spare, present, is_expected_kind)` on the present-off-kind path in place of the pinned raise): exit 2, DOES NOT VERIFY. The repair's method-level MustTerminate rejects it. This is the decisive regression check.
- atk_2.py (termination, other divergence encoding: `while True` on the off-kind path, fresh loop whose invariants region deliberately omits any measure): exit 2, does not verify.
- atk_3.py (CONTROL-FLOW-EFFECT / store-path divergence: copy loop never increments `i`, loop MustTerminate invariant deleted -- probes whether the METHOD-level measure alone rejects loop divergence, since the invariants region is attacker-owned): exit 2, does not verify.
- atk_4.py (PARTIAL-DOMAIN: raise pinned only for a NON-EMPTY off-kind collection; an empty off-kind `[]` quietly accepted as empty -- the exact residue of the pre-patch truthiness test): exit 2, does not verify.
- atk_5.py (BOUNDARY off-by-one: present-and-expected path drops the LAST label, `while i + 1 < len(...)`): exit 2, does not verify.
- atk_6.py (CONTROL-FLOW-EFFECT: absent-guard removed so the kind test also fires for the ABSENT input -> plain `ProjectState()` would assert): exit 2, does not verify.
- atk_7.py (UNGROUNDED-ORACLE ECHO analogue: off-kind collection SILENTLY COERCED and returned normally -- the pre-patch behaviour on the discriminating path only): exit 2, does not verify.
- atk_8.py (EXCEPTION-TYPE: off-kind path raises `ValueError()` instead of the pinned OffKindCollection, i.e. faithful patch raises a non-AssertionError the F2P `assertRaises(AssertionError)` would not catch): exit 2, does not verify.
- atk_prepatch.py (THE PRE-PATCH BUG re-encoded: `if present and len(real_apps) > 0: copy-and-return`): exit 2, DOES NOT VERIFY => PREPATCH REPRODUCED; `Ensures((not present) or is_expected_kind)` sees the fix (G-DIFF confirmed independently).
- atk_echo.py (intended echo control, fused decisions + bounded depth-1 self-call): exit 2, does not verify -- rejected for an OBLIGATION-LEAK reason, not a behavioural one: `bash scripts/nagini_verify.sh` gives `atk_echo.py:112: Obligation leak check failed. Callee build_state might not take all unsatisfied obligations from the caller.` That is a construction artifact of my own guarded self-call under the new method-level measure, not evidence about the spec; superseded by atk_9 as the echo control.
- atk_9.py (A4-LEG PROBE, the deep model<->patch correspondence step): restructured copy loop with an explicit bound `n = len(real_apps)`. Exit 0 = CANDIDATE (shares spec AND VERIFIES, 12.9s).

MANDATORY RESOLVE RUN for the one CANDIDATE. atk_9 exists to test refinement.md A4 / mapping.md section 2, the only non-trivial R/identity leg: model.py RETURNS A FRESH List[int] while the gold patch STORES BY REFERENCE (`self.real_apps = real_apps`), with A4 justifying that as "object identity refines to membership equality". atk_9's faithful patch is the LITERAL reading of that leg -- `self.real_apps = set(real_apps)`, a copy. Materialized at $D/patch_atk_9.diff; `git apply --check` at base_commit 4e8121e8e42a24acc3565851c9ef50ca8322b15c => rc=0.

Executed `run_resolve('django__django-14765', patch_atk_9.diff, run_id='sbu-eq-audit-d7po0y-atk9', timeout=1800)`; log $D/resolve_atk_9.log: completed=TRUE, resolved=TRUE, attempts=1, flaky=false, patch_successfully_applied=true, FAIL_TO_PASS success=['test_real_apps_non_set'], failure=[]; PASS_TO_PASS 63/63 success, 0 failures; PASS_TO_FAIL empty. So the ONLY verifying rival RESOLVES => it is a correct alternative implementation (an echo), NOT a spec weakness, per architecture.md section 6. This run also serves as the live proof that the resolve pipeline reaches real verdicts in this pass (the prior pass's INCONCLUSIVE risk was a hung runner).

POSITIVE CONTROL: `bash scripts/nagini_verify.sh $D/pos_control.py` (= model.py verbatim) => 'Verification successful', 11.32s, exit 0.

A-LEG / refinement.md AUDIT (my assigned focus). refinement.md sections B and mapping.md section 3 both declare NO axiomatized callee and NO deep-model reference; axioms and pure regions are comment-only; meta.json has axioms=[] and deep_model_references=[]; G-AX is a stamped skip with reason 'no axiom_check.py (no axioms in bundle)'. I confirmed this is correct rather than an evasion: the changed body is only Python control flow + `isinstance(real_apps, set)` + `assert` + an attribute store, none of which is an opaque callee. Modeling `isinstance` as the boolean `is_expected_kind` (A1/A3, tagged R) is the right call -- it is part of the decision UNDER CHANGE, so axiomatizing it would be assuming the thing to be proved; and it is not left ungrounded, since G-CONF drives the real `ProjectState.__init__` over the whole kind x membership domain (100021 inputs, 0 disagreements, incl. a `set` SUBCLASS, `frozenset`, tuple, dict, str, int, bare object). Every leg is R / R+I / I; there is no kind-3 step, and no leg is A-consumed or A-reference, so the 'no kind-3' claim in section B holds.

A4 correspondence, checked against the repo at base_commit (the one leg that could hide a defect): the model's copy-vs-gold's-alias gap is observationally sound because identity of the stored set is never observed. `git grep` over django/ and tests/ at base_commit finds (a) NO `real_apps is`/`id(real_apps)` identity test anywhere, and (b) NO in-place mutation of a stored set: zero hits for `real_apps.(add|remove|discard|update|clear|pop)`. All consumers observe MEMBERSHIP only -- `state.py:365,373` (`not in self.real_apps`), `:425` `StateApps(self.real_apps, ...)` which iterates and sorts, `:437` `__eq__` comparing by `==`, `:412` clone re-passing it, `autodetector.py:137,147` membership tests.

The one real behavioural difference the patch introduces in the aliasing dimension (pre-patch `if real_apps:` builds a FRESH set for an empty-set argument, post-patch stores the caller's object) is membership-identical and only observable through later caller-side mutation, which no call site does -- `loader.py` finishes populating `unmigrated_apps` (lines 77-102) BEFORE `executor.py:69` hands it to ProjectState. The empirical seal is atk_9: the copy patch resolves 64/64, so the copy/alias distinction is genuinely unobservable on the tested behaviour and A4's R-tag is honest, not a papered-over kind-3.

CONCLUSION: 11 same-spec attacks encoded and machine-verified; 10 wrong impls REJECTED by the spec (incl. the prior pass's BROKEN witness and the pre-patch bug); the single CANDIDATE (atk_9) had its faithful patch materialized and RUN through the official harness, where it RESOLVED (completed=true, resolved=true, F2P pass, 63/63 P2P) -- an echo, correctly not a weakness. Positive control verifies. No verifying wrong impl exists whose faithful patch fails to resolve. VERDICT: SOUND. Actionable side note for the runner, not a G-EQ defect: meta.json's recorded G-EQ (and G-PANEL-1/G-PANEL) verdicts predate the MustTerminate repair and now contradict the artifact; they should be re-derived from this pass.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK GOAL: show the frozen spec is too strong / drifts from real post-patch `ProjectState.__init__` (django/db/migrations/state.py:91) — i.e. find an input where the modeled `build_state` disagrees with the real callee. NO SUCH INPUT FOUND.

**SETUP:** fresh worktree at base_commit 4e8121e8e42a24acc3565851c9ef50ca8322b15c, gold patch.diff applied. I changed nothing in the bundle: the 4 modified files in `git status` carry mtimes 20:28/20:29/20:49, identical to my pre-work listing, so they predate this role.

SPEC INTEGRITY: `adversary same-spec` = SAME on a byte copy; bundle model.py verifies (Verification successful, 12.79s) with the pinned verifier.

(1) STRUCTURED DIFFERENTIAL — 343 real inputs (None; set/set-subclass/frozenset/list/tuple/dict/generator/custom-collection at sizes 0-3 over 6 label strings; str; int; dup-bearing set and list; a `__bool__`-False set subclass) each mapped through mapping.md's refinement (present<->arg is not None, is_expected_kind<->isinstance(arg,set), Result()<->self.real_apps membership) and checked against EVERY post-condition clause (E1 normal-return=>(not present) or is_expected_kind; E2 absent=>empty; E3 present&expected=>membership preserved; X1 raise=>present&off-kind) plus 'no unlisted exception escapes'. **0 spec violations.**

(2) 100k RANDOMIZED DIFFERENTIAL — seed 20260813, 17 runtime kinds (incl. deque, OrderedDict, dict_keys, iterator, bytearray, range, bytes, set subclass) x sizes 0-5 over a 9-label pool incl. '', unicode, 40-char. **checked=100000 violations=0.**

(3) BOUNDARY TABLE — the place a too-strong Exsures would break is PRESENT-BUT-FALSY OFF-KIND, since the pre-patch guard was truthiness (`if real_apps:`) while the spec's Exsures demands a raise for EVERY present off-kind collection 'whether empty or non-empty'. Verified real post-patch behavior on `[]`, `()`, `{}`, `frozenset()`: all raise AssertionError, matching the spec exactly. Empty `set()` and empty set-subclass correctly RETURN empty. All 10 boundary rows agree.

(4) IDENTITY->MEMBERSHIP REFINEMENT (the one genuine abstraction gap) — real post-patch stores BY REFERENCE (`ps.real_apps is s` True; clone shares the object; later caller-side `s.add()` leaks into the state), while the model returns a fresh List[int] with equal membership. I audited whether aliasing is OBSERVABLE: grepped every `.real_apps` use in django/ — autodetector.py:137/147 (`not in`), state.py:366/374 (`not in`), :413 (pass-through to clone), :426 (StateApps iteration), :438 (`==`). All read-only; no `.add/.update/.discard/.remove/.pop/.clear` on any state's real_apps anywhere in django/ or tests/. Aliasing is therefore unobservable on the tested behavior, so the R-refinement is sound, not drift. Also confirmed the model's `Requires/Ensures Acc(list_pred(real_apps), 1/2)` read-only permission is the faithful encoding of this.

(5) HOSTILE isinstance PROBES — `__class__` property returning `set` (Liar) is ACCEPTED by the real assert and stored un-coerced, and `__class__` raising (Hostile) lets RuntimeError escape. Both are consistent with the spec rather than counterexamples: is_expected_kind is defined AS the runtime `isinstance` result (so Liar => is_expected_kind=True => spec demands normal return with preserved membership, which is what happens), and Hostile's RuntimeError is raised by the isinstance test itself, outside the modeled decision; likewise a `models=` object whose `__bool__` raises TypeError fails on the *preceding, unchanged* line `self.models = models or {}`, not in the modeled region. None of these are reachable from any repo caller (`real_apps` is only ever fed `loader.unmigrated_apps`, a genuine set, or None).

(6) `-O` / PYTHONOPTIMIZE — under `python -O` asserts vanish and 255/343 E1 checks 'fail'. Rejected as inadmissible: the harness never sets -O, and under -O the GOLD PATCH ITSELF fails its own F2P test (confirmed: `python -O runtests.py ...test_real_apps_non_set` => FAILED). So -O breaks the repo's intended behavior, not the spec's fidelity to it.

(7) INDEPENDENT ORACLES — bundle conformance_check.py: G-CONF OK, 100021 inputs, 0 disagreements. F2P `test_real_apps_non_set` + `test_real_apps` pass. Full `migrations` suite: Ran 582 tests, OK (skipped=1).

(8) NON-VACUITY (spec not trivially satisfiable) — model_prepatch.py is same-spec and FAILS verification precisely on `Assertion ((not present) or is_expected_kind) might not hold`, i.e. the spec genuinely senses the fixed bug rather than being satisfiable by the buggy behavior.

CONCLUSION: FAITHFUL. Across ~100.4k real-callee comparisons plus targeted adversarial and boundary probing, the modeled function never disagrees with the real post-patch callee on any admissible input. The Exsures is exactly as strong as the real `assert isinstance(real_apps, set)` (notably matching on the falsy-off-kind cases where the pre-patch differed), and the sole abstraction (object identity -> membership equality) is justified by the repo's read-only use of the stored attribute. No diverging input; no faithfulness defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: judged the consumer-visible spec view only (markers.spec_view over model.py), against problem_statement ONLY (hints_text excluded per gate rule).

WHAT THE CONSUMER SEES. Verified spec_view is well-formed and idempotent (spec_view(v)==v), regions parse clean (axioms 49-53, pure 56-60, pre 64-78, post 79-96, impl 97-122 with nested invariants 111-117). The impl region — including the invariants and the whole loop — collapses to `...  # implementation elided`. adapter.spec_view() additionally hard-guards that ELISION_IMPL is present before exposure. So the 99-line view = module docstring + imports + OffKindCollection class + empty axioms/pure notes + build_state signature + Requires/Ensures/Exsures.

MECHANICAL SCREEN: leakage.screen(model.py, nagini, gold_patch, problem_statement) => hard_failures=[] , warnings=[]. Independently re-derived each rule:
- L1 diff markers: none of ('@@','diff --git','+++ ','--- ','\nindex ') in view.
- L1 gold-line reproduction: all 7 changed lines checked normalized (len>=8); none in view_norm. Confirmed by direct token probe — 'isinstance', 'AssertionError', 'self.real_apps', 'is None', 'set(', 'assert' are ALL absent from the spec view. The view never names the runtime type test or the assert; it abstracts them to the booleans `present` / `is_expected_kind` and the user-defined OffKindCollection.
- L2 paths: 'django/db/migrations/state.py' absent; dotted 'django.db.migrations.state' absent. (mapping.md/refinement.md DO quote the gold hunk verbatim and cite state.py:91, but they are NOT in the consumer payload — eval/prompts.py builds the user turn from problem_statement + hints + _spec_block(spec_view) only; grep of eval/ shows no mapping.md/refinement.md ingestion. Same for meta.json's `carrier_type`/`repo_location`, which spell out the isinstance/AssertionError refinement: _spec_block renders only model_symbol (↔ repo_symbol) for nagini, not carrier_type/repo_location. repo_symbol = ProjectState.__init__, which is verbatim public in the problem statement title.)
- L2/L5 symbol collision: _patch_changed_symbols(gold) = {'ProjectState'} only ('__init__' is in _COMMON_NONDISTINCTIVE). 'projectstate' IS in problem_statement (title line), so it is public and short-circuits; and it does not appear in the view anyway. Model identifiers are build_state / real_apps / present / is_expected_kind / OffKindCollection — none embeds a patched def/class name.
- L3 narration: _NARRATION_RE finds no hit in any comment/docstring token. Checked the known false-positive vocabulary from prior waves: 'copy' appears ("no copy or coercion alters it") but 'copy' is NOT in _NARRATION; 'fix'/'fixed'/'bug'/'patch'/'previously'/'incorrectly'/'wrong' all absent. 'changed' in the axioms note ("inside the changed operation") is not a narration term.

SEMANTIC / GOLD-RECONSTRUCTION TEST (the part the lexer misses). The real question is whether the view hands over a discriminator the solver could not get from the issue. It does not — the problem statement is unusually explicit and states the edit in prose: "instead of checking that real_apps is a set and converting it to a set if not, it can just assert that it's a set when non-None." Mapping each disclosing spec clause to public text:
- `Ensures((not present) or is_expected_kind)` (normal return only for absent-or-set) <- "assert that it's a set when non-None".
- `Exsures(OffKindCollection, present and not is_expected_kind)` (present non-set must fail) <- same sentence; the assert IS the failure. 'assert' is in problem_statement.
- "never a coerced result" / "does not quietly convert an off-kind collection" <- "instead of ... converting it to a set if not".
- absent => empty collection <- the pre-existing else-branch semantics, and implied by "when non-None".
- "internal construction API" / "internal-contract violation" framing <- "the construction of new ProjectState objects is part of Django's internal API".
- "for example an ordered list" as the off-kind example: the canonical non-set collection implied by "converting it to a set"; discloses no test identity (test file/name/'contenttypes' literal all absent from the view).
So the spec view is a strict formalization of publicly stated behaviour; it discloses LESS than the issue (it never names the assert statement, AssertionError, isinstance, the file, or the attribute). Hints-only vocabulary (chris, amazed, folks, suggestion, review, accept...) is not echoed anywhere in the view — the pilot's hints-leak failure mode is clean.

No RELAXED_LEAKAGE.md and no relaxed flag in meta (meta.gates G-LEAK not 'relaxed'), so the pass is an unrelaxed pass — consistent.

OUT-OF-SCOPE OBSERVATION (not a leakage finding, flagging for the integrity/hygiene gate owner): meta.json region_hashes are STALE vs the current model.py. Live vs recorded: axioms/pure/post-conditions match, but pre-conditions (live b5f219bd115d vs meta 3a050799b489), invariants (d96c4ad3182e vs daee0929805c), impl (3ed1e00eff9a vs 2763fc644150) and spec_view (live f4e5ad3a3c38... vs meta 83b8f21f3082...) all differ — model.py/model_prepatch.py are dated Aug 13 20:28 while the docs are Aug 5. This does not create leakage (I audited the LIVE file, which is what a consumer would be served, and it is clean), but a recorded-hash mismatch means the frozen spec_view attestation no longer pins the shipped artifact and should be re-stamped. Separately, spec regions are byte-identical between model.py and model_prepatch.py (all four SPEC_REGIONS equal, spec_view identical), which is the correct same-spec property for the G-DIFF pair.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.