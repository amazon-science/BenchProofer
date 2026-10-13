# P2 adversarial audit — django__django-12262

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,27 +141,16 @@
     seen = PSeq(0).take(0)  # type: PSeq[int]
     i = 0
     while i < len(supplied):
-        # invariants-start
         Invariant(Acc(list_pred(supplied), 1 / 2))
         Invariant(0 <= i and i <= len(supplied))
         Invariant(seen == ToSeq(supplied).take(i))
-        # The remaining computation from index `i` with the keywords bound so
-        # far equals the total outcome (no problematic keyword has been seen yet
-        # in indices < i, else the loop would have returned).
-        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),
-                          positional, keyword_only, catch_all) ==
-                  outcome(ToSeq(supplied).drop(i), seen,
-                          positional, keyword_only, catch_all))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(supplied) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(supplied) - i + 1))
-        # invariants-end
         name = supplied[i]
-        Assert(ToSeq(supplied).drop(i)[0] == name)
-        Assert(ToSeq(supplied).drop(i).drop(1) == ToSeq(supplied).drop(i + 1))
-        Assert(ToSeq(supplied).take(i + 1) == seen + PSeq(name))
-        if not acceptable(positional, keyword_only, catch_all, name):
+        still_required = (contains(keyword_only, name)
+                          and not contains(keyword_only_with_default, name)
+                          and not contains(seen, name))
+        known = catch_all or contains(positional, name) or still_required
+        if not known:
             return 1
         if contains(seen, name):
             return 2
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -138,34 +138,5 @@
                                 positional, keyword_only, catch_all))
     # post-conditions-end
     # impl-start
-    seen = PSeq(0).take(0)  # type: PSeq[int]
-    i = 0
-    while i < len(supplied):
-        # invariants-start
-        Invariant(Acc(list_pred(supplied), 1 / 2))
-        Invariant(0 <= i and i <= len(supplied))
-        Invariant(seen == ToSeq(supplied).take(i))
-        # The remaining computation from index `i` with the keywords bound so
-        # far equals the total outcome (no problematic keyword has been seen yet
-        # in indices < i, else the loop would have returned).
-        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),
-                          positional, keyword_only, catch_all) ==
-                  outcome(ToSeq(supplied).drop(i), seen,
-                          positional, keyword_only, catch_all))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(supplied) - i),
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(supplied) - i + 1))
-        # invariants-end
-        name = supplied[i]
-        Assert(ToSeq(supplied).drop(i)[0] == name)
-        Assert(ToSeq(supplied).drop(i).drop(1) == ToSeq(supplied).drop(i + 1))
-        Assert(ToSeq(supplied).take(i + 1) == seen + PSeq(name))
-        if not acceptable(positional, keyword_only, catch_all, name):
-            return 1
-        if contains(seen, name):
-            return 2
-        seen = seen + PSeq(name)
-        i = i + 1
     return 0
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -140,27 +140,12 @@
     # impl-start
     seen = PSeq(0).take(0)  # type: PSeq[int]
     i = 0
-    while i < len(supplied):
-        # invariants-start
+    while i < len(supplied) - 1:
         Invariant(Acc(list_pred(supplied), 1 / 2))
         Invariant(0 <= i and i <= len(supplied))
         Invariant(seen == ToSeq(supplied).take(i))
-        # The remaining computation from index `i` with the keywords bound so
-        # far equals the total outcome (no problematic keyword has been seen yet
-        # in indices < i, else the loop would have returned).
-        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),
-                          positional, keyword_only, catch_all) ==
-                  outcome(ToSeq(supplied).drop(i), seen,
-                          positional, keyword_only, catch_all))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(supplied) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(supplied) - i + 1))
-        # invariants-end
         name = supplied[i]
-        Assert(ToSeq(supplied).drop(i)[0] == name)
-        Assert(ToSeq(supplied).drop(i).drop(1) == ToSeq(supplied).drop(i + 1))
-        Assert(ToSeq(supplied).take(i + 1) == seen + PSeq(name))
         if not acceptable(positional, keyword_only, catch_all, name):
             return 1
         if contains(seen, name):
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,30 +141,15 @@
     seen = PSeq(0).take(0)  # type: PSeq[int]
     i = 0
     while i < len(supplied):
-        # invariants-start
         Invariant(Acc(list_pred(supplied), 1 / 2))
         Invariant(0 <= i and i <= len(supplied))
         Invariant(seen == ToSeq(supplied).take(i))
-        # The remaining computation from index `i` with the keywords bound so
-        # far equals the total outcome (no problematic keyword has been seen yet
-        # in indices < i, else the loop would have returned).
-        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),
-                          positional, keyword_only, catch_all) ==
-                  outcome(ToSeq(supplied).drop(i), seen,
-                          positional, keyword_only, catch_all))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(supplied) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(supplied) - i + 1))
-        # invariants-end
         name = supplied[i]
-        Assert(ToSeq(supplied).drop(i)[0] == name)
-        Assert(ToSeq(supplied).drop(i).drop(1) == ToSeq(supplied).drop(i + 1))
-        Assert(ToSeq(supplied).take(i + 1) == seen + PSeq(name))
+        if contains(seen, name):
+            return 2
         if not acceptable(positional, keyword_only, catch_all, name):
             return 1
-        if contains(seen, name):
-            return 2
         seen = seen + PSeq(name)
         i = i + 1
     return 0
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -138,34 +138,6 @@
                                 positional, keyword_only, catch_all))
     # post-conditions-end
     # impl-start
-    seen = PSeq(0).take(0)  # type: PSeq[int]
-    i = 0
-    while i < len(supplied):
-        # invariants-start
-        Invariant(Acc(list_pred(supplied), 1 / 2))
-        Invariant(0 <= i and i <= len(supplied))
-        Invariant(seen == ToSeq(supplied).take(i))
-        # The remaining computation from index `i` with the keywords bound so
-        # far equals the total outcome (no problematic keyword has been seen yet
-        # in indices < i, else the loop would have returned).
-        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),
-                          positional, keyword_only, catch_all) ==
-                  outcome(ToSeq(supplied).drop(i), seen,
-                          positional, keyword_only, catch_all))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(supplied) - i),
-        # discharging MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(len(supplied) - i + 1))
-        # invariants-end
-        name = supplied[i]
-        Assert(ToSeq(supplied).drop(i)[0] == name)
-        Assert(ToSeq(supplied).drop(i).drop(1) == ToSeq(supplied).drop(i + 1))
-        Assert(ToSeq(supplied).take(i + 1) == seen + PSeq(name))
-        if not acceptable(positional, keyword_only, catch_all, name):
-            return 1
-        if contains(seen, name):
-            return 2
-        seen = seen + PSeq(name)
-        i = i + 1
-    return 0
+    return outcome(ToSeq(supplied), PSeq(0).take(0),
+                   positional, keyword_only, catch_all)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,27 +141,13 @@
     seen = PSeq(0).take(0)  # type: PSeq[int]
     i = 0
     while i < len(supplied):
-        # invariants-start
         Invariant(Acc(list_pred(supplied), 1 / 2))
         Invariant(0 <= i and i <= len(supplied))
         Invariant(seen == ToSeq(supplied).take(i))
-        # The remaining computation from index `i` with the keywords bound so
-        # far equals the total outcome (no problematic keyword has been seen yet
-        # in indices < i, else the loop would have returned).
-        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),
-                          positional, keyword_only, catch_all) ==
-                  outcome(ToSeq(supplied).drop(i), seen,
-                          positional, keyword_only, catch_all))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(supplied) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(supplied) - i + 1))
-        # invariants-end
         name = supplied[i]
-        Assert(ToSeq(supplied).drop(i)[0] == name)
-        Assert(ToSeq(supplied).drop(i).drop(1) == ToSeq(supplied).drop(i + 1))
-        Assert(ToSeq(supplied).take(i + 1) == seen + PSeq(name))
-        if not acceptable(positional, keyword_only, catch_all, name):
+        ok = catch_all or contains(positional, name) or contains(keyword_only_with_default, name)
+        if not ok:
             return 1
         if contains(seen, name):
             return 2
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -141,27 +141,12 @@
     seen = PSeq(0).take(0)  # type: PSeq[int]
     i = 0
     while i < len(supplied):
-        # invariants-start
         Invariant(Acc(list_pred(supplied), 1 / 2))
         Invariant(0 <= i and i <= len(supplied))
         Invariant(seen == ToSeq(supplied).take(i))
-        # The remaining computation from index `i` with the keywords bound so
-        # far equals the total outcome (no problematic keyword has been seen yet
-        # in indices < i, else the loop would have returned).
-        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),
-                          positional, keyword_only, catch_all) ==
-                  outcome(ToSeq(supplied).drop(i), seen,
-                          positional, keyword_only, catch_all))
-        # the scan consumes the caller's termination obligation with a
-        # strictly decreasing, bounded-below measure (len(supplied) - i),
-        # discharging MustTerminate(2) from the precondition.
         Invariant(MustTerminate(len(supplied) - i + 1))
-        # invariants-end
         name = supplied[i]
-        Assert(ToSeq(supplied).drop(i)[0] == name)
-        Assert(ToSeq(supplied).drop(i).drop(1) == ToSeq(supplied).drop(i + 1))
-        Assert(ToSeq(supplied).take(i + 1) == seen + PSeq(name))
-        if not acceptable(positional, keyword_only, catch_all, name):
+        if not (contains(positional, name) or contains(keyword_only, name)):
             return 1
         if contains(seen, name):
             return 2
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12262.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A custom-tag argument binder consumes an ordered run of supplied keyword
  arguments, each identified by the name of the parameter it targets, and
  decides the outcome of the binding. The binder knows two static facts about
  the callable being bound:

    * the names of its positional parameters, and
    * the names of its keyword-only parameters

  and whether the callable also accepts arbitrary extra keyword arguments
  (a "catch-all" keyword parameter). A supplied keyword name is ACCEPTABLE iff
  it names one of the declared parameters -- positional OR keyword-only --
  REGARDLESS of whether that keyword-only parameter happens to carry a default
  value. (Whether a keyword-only parameter has a default governs only whether it
  is still *required*; it never makes an explicitly-supplied value for that
  parameter unacceptable.)

  Walking the supplied keywords front to back, the FIRST one that is problematic
  determines the outcome:

    * outcome UNEXPECTED -- the keyword names no declared parameter and the
      callable has no catch-all keyword parameter;
    * outcome DUPLICATE -- the keyword names a parameter for which a value has
      already been supplied earlier in the run (it is supplied a second time);
    * otherwise outcome OK -- every supplied keyword was acceptable and supplied
      at most once.

  The two problematic outcomes are distinct and must not be confused: supplying
  an acceptable keyword twice is a DUPLICATE, never an UNEXPECTED keyword.

  Binding is a bounded front-to-back scan of the supplied run: the binder MUST
  actually ANSWER with an outcome (a total-correctness obligation, carried as
  MustTerminate in the precondition). Nagini is a partial-correctness verifier
  by default, so without this obligation a diverging implementation (e.g.
  `while True: pass` inserted before the scan) would satisfy the value
  postcondition vacuously; the real binder always delivers its decision.

Parameter names are modelled as integer codes; the supplied-keyword run is a
`List[int]` of those codes. The declared positional and keyword-only parameter
name sets are `PSeq[int]`; the subset of keyword-only names that carry a default
value is also given (`keyword_only_with_default`, a sub-collection of the
keyword-only names); the catch-all flag is a bool. The outcome is the integer
code 0 (OK), 1 (UNEXPECTED), or 2 (DUPLICATE). The decision is pure membership/
duplication logic over the inputs, modelled deeply as a front-recursive fold;
no callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the binding decision is membership/duplication logic
# over the supplied-keyword run and the declared parameter-name sets, all
# modelled deeply below. The extraction of an individual keyword from a token
# and the compilation of its value are unchanged, independent of this decision,
# and unobserved by the behaviour pinned here.)
# axioms-end


# pure-start
@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff name code `x` occurs in sequence `s`. Front-recursive so a
    single unfold is available per fold/loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


@Pure
def acceptable(positional: PSeq[int], keyword_only: PSeq[int],
               catch_all: bool, name: int) -> bool:
    """A supplied keyword `name` is acceptable iff it names a declared
    parameter -- positional OR keyword-only -- or the callable has a catch-all
    keyword parameter. Membership in `keyword_only` is the full set of
    keyword-only names, independent of which of them carry defaults."""
    return catch_all or contains(positional, name) or contains(keyword_only, name)


@Pure
def outcome(supplied: PSeq[int], seen: PSeq[int],
            positional: PSeq[int], keyword_only: PSeq[int],
            catch_all: bool) -> int:
    """Outcome of binding the supplied-keyword run `supplied`, given the names
    `seen` already bound earlier in the run. Front-recursive (one unfold per
    supplied keyword) so a forward impl loop can discharge it. Returns 0 (OK),
    1 (UNEXPECTED), or 2 (DUPLICATE) -- the FIRST problematic keyword wins."""
    if len(supplied) == 0:
        return 0
    name = supplied[0]
    if not acceptable(positional, keyword_only, catch_all, name):
        return 1
    if contains(seen, name):
        return 2
    return outcome(supplied.drop(1), seen + PSeq(name),
                   positional, keyword_only, catch_all)
# pure-end


def bind_keywords(supplied: List[int], positional: PSeq[int],
                  keyword_only: PSeq[int], keyword_only_with_default: PSeq[int],
                  catch_all: bool) -> int:
    # pre-conditions-start
    # The supplied-keyword run is read-only (the binder inspects it, it does not
    # mutate it): required AND ensured at fractional permission (directive 5).
    # `positional` / `keyword_only` / `keyword_only_with_default` are pure
    # sequence values (the declared parameter-name sets); `catch_all` is a plain
    # bool. Well-formedness: every keyword-only name that carries a default is
    # itself a keyword-only name (defaults are a sub-collection of the keyword-
    # only parameters), which holds for every real callable.
    Requires(Acc(list_pred(supplied), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(
        0 <= k and k < len(keyword_only_with_default),
        contains(keyword_only, keyword_only_with_default[k])))))
    # TERMINATION: the binder must actually ANSWER — deciding the outcome of a
    # finite supplied-keyword run is a bounded computation (one step per
    # keyword). Nagini is a partial-correctness verifier by default, so without
    # this obligation a non-terminating implementation (e.g. an endless loop
    # before returning) satisfies the value postcondition vacuously; the real
    # binder always returns or raises its decision.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(supplied), 1 / 2))
    # The returned outcome is exactly the front-to-back binding decision: 0 OK,
    # 1 UNEXPECTED (an unacceptable keyword), 2 DUPLICATE (an acceptable keyword
    # supplied twice); the first problematic keyword determines it. Starting
    # from no keyword bound (empty `seen`). This pins the discriminating
    # behaviour: an acceptable keyword carrying a default is NOT unexpected, and
    # a repeated acceptable keyword is a DUPLICATE rather than UNEXPECTED.
    Ensures(Result() == outcome(ToSeq(supplied), PSeq(0).take(0),
                                positional, keyword_only, catch_all))
    # post-conditions-end
    # impl-start
    seen = PSeq(0).take(0)  # type: PSeq[int]
    i = 0
    while i < len(supplied):
        # invariants-start
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(0 <= i and i <= len(supplied))
        Invariant(seen == ToSeq(supplied).take(i))
        # The remaining computation from index `i` with the keywords bound so
        # far equals the total outcome (no problematic keyword has been seen yet
        # in indices < i, else the loop would have returned).
        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),
                          positional, keyword_only, catch_all) ==
                  outcome(ToSeq(supplied).drop(i), seen,
                          positional, keyword_only, catch_all))
        # the scan consumes the caller's termination obligation with a
        # strictly decreasing, bounded-below measure (len(supplied) - i),
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(supplied) - i + 1))
        # invariants-end
        name = supplied[i]
        Assert(ToSeq(supplied).drop(i)[0] == name)
        Assert(ToSeq(supplied).drop(i).drop(1) == ToSeq(supplied).drop(i + 1))
        Assert(ToSeq(supplied).take(i + 1) == seen + PSeq(name))
        if not acceptable(positional, keyword_only, catch_all, name):
            return 1
        if contains(seen, name):
            return 2
        seen = seen + PSeq(name)
        i = i + 1
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is value-complete: Ensures(Result() == outcome(ToSeq(supplied), PSeq(0).take(0), positional, keyword_only, catch_all)) pins the int return to EXACT functional equality with the frozen deep-model fold `outcome` over the full precondition domain (only extra precond is well-formedness defaults ⊆ kwonly, which excludes no real callable). So verify ⇒ value-equal-to-gold-fold ⇒ (via A-reference axiom_check == real fixed parse_bits) ⇒ resolves.

7 attacks built, ALL same-spec-confirmed (adversary same-spec exit 0 each). Verifications run concurrently in background batches of ≤3 (each spawns JVM+Z3). weakness command: `python -m swebench_unified.adversary weakness nagini django__django-12262 <atk>`:
- atk_1 prepatch bug (still_required/unhandled_kwargs): weakness exit 2 (does NOT verify) — spec catches the bug, matches G-DIFF. prepatch_reproduced=true.
- atk_2 constant return 0 (partial-domain): exit 2 (fails).
- atk_3 off-by-one boundary (skip last keyword): exit 2 (fails).
- atk_4 swapped guard order (duplicate before acceptability): exit 2 (fails).
- atk_5 ungrounded-oracle echo (return outcome(...) verbatim): exit 0 CANDIDATE (shares spec AND verifies).
- atk_6 acceptability wrongly requires a default (mis-models bug1): exit 2 (fails).
- atk_7 control-flow-effect ignore catch_all: exit 2 (fails).

MANDATORY candidate resolve: atk_5 returns exactly outcome(...) = the fixed gold decision, so its faithful refined patch is byte-identical to patch.diff (the `param not in kwonly` fix). Materialized as atk_5_faithful_patch.diff and RAN through the official harness (swebench_unified.run_evaluation, docker, run_id sbu-eq-atk5-loop1). Docker under heavy contention (heavy-250, 72-80 containers) forced several retries: initial run_resolve attempts hit Docker 60s client ReadTimeout in build_container and an images.list ImageNotFound race (both INFRA, not verdicts); resolved by monkeypatching docker.from_env timeout to 900s and looping. Report captured at report_final.json: resolved=true, 4/4 FAIL_TO_PASS pass (test_inclusion_tag_errors, test_inclusion_tags, test_simple_tag_errors, test_simple_tags), 18/18 PASS_TO_PASS pass. => atk_5 is a RESOLVING echo of the gold, NOT a weakness (per the G-EQ/G-PANEL-1 echo-attack policy: a same-spec verifying attack whose refined patch resolves is not a weakness).

Positive control: model.py verifies via scripts/nagini_verify.sh (exit 0, 15.6s).

refinement.md audit: every leg is R or I; ZERO consumed axioms (no A-consumed row — the changed op is a pure membership test modeled DEEPLY by outcome/acceptable/contains). One A-reference: the deep `outcome` model validated == the real fixed parse_bits keyword decision by axiom_check.py, which I ran (exit 0: 12 boundary + exhaustive small enumeration + 40000 fuzz inputs, prepatch differential confirmed on both issue witnesses). No kind-3 (unexpressible-changed-op) steps. A-reference correspondence HOLDS: axiom_check faithfully transcribes the post-patch condition `param not in params and param not in kwonly and varkw is None` including real unhandled_kwargs construction/consumption.

No verifying-but-incorrect impl found; the sole verifying candidate resolves. Gate SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12262.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A custom-tag argument binder consumes an ordered run of supplied keyword
  arguments, each identified by the name of the parameter it targets, and
  decides the outcome of the binding. The binder knows two static facts about
  the callable being bound:

    * the names of its positional parameters, and
    * the names of its keyword-only parameters

  and whether the callable also accepts arbitrary extra keyword arguments
  (a "catch-all" keyword parameter). A supplied keyword name is ACCEPTABLE iff
  it names one of the declared parameters -- positional OR keyword-only --
  REGARDLESS of whether that keyword-only parameter happens to carry a default
  value. (Whether a keyword-only parameter has a default governs only whether it
  is still *required*; it never makes an explicitly-supplied value for that
  parameter unacceptable.)

  Walking the supplied keywords front to back, the FIRST one that is problematic
  determines the outcome:

    * outcome UNEXPECTED -- the keyword names no declared parameter and the
      callable has no catch-all keyword parameter;
    * outcome DUPLICATE -- the keyword names a parameter for which a value has
      already been supplied earlier in the run (it is supplied a second time);
    * otherwise outcome OK -- every supplied keyword was acceptable and supplied
      at most once.

  The two problematic outcomes are distinct and must not be confused: supplying
  an acceptable keyword twice is a DUPLICATE, never an UNEXPECTED keyword.

  Binding is a bounded front-to-back scan of the supplied run: the binder MUST
  actually ANSWER with an outcome (a total-correctness obligation, carried as
  MustTerminate in the precondition). Nagini is a partial-correctness verifier
  by default, so without this obligation a diverging implementation (e.g.
  `while True: pass` inserted before the scan) would satisfy the value
  postcondition vacuously; the real binder always delivers its decision.

Parameter names are modelled as integer codes; the supplied-keyword run is a
`List[int]` of those codes. The declared positional and keyword-only parameter
name sets are `PSeq[int]`; the subset of keyword-only names that carry a default
value is also given (`keyword_only_with_default`, a sub-collection of the
keyword-only names); the catch-all flag is a bool. The outcome is the integer
code 0 (OK), 1 (UNEXPECTED), or 2 (DUPLICATE). The decision is pure membership/
duplication logic over the inputs, modelled deeply as a front-recursive fold;
no callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the binding decision is membership/duplication logic
# over the supplied-keyword run and the declared parameter-name sets, all
# modelled deeply below. The extraction of an individual keyword from a token
# and the compilation of its value are unchanged, independent of this decision,
# and unobserved by the behaviour pinned here.)
# axioms-end


# pure-start
@Pure
def contains(s: PSeq[int], x: int) -> bool:
    """True iff name code `x` occurs in sequence `s`. Front-recursive so a
    single unfold is available per fold/loop step."""
    if len(s) == 0:
        return False
    return s[0] == x or contains(s.drop(1), x)


@Pure
def acceptable(positional: PSeq[int], keyword_only: PSeq[int],
               catch_all: bool, name: int) -> bool:
    """A supplied keyword `name` is acceptable iff it names a declared
    parameter -- positional OR keyword-only -- or the callable has a catch-all
    keyword parameter. Membership in `keyword_only` is the full set of
    keyword-only names, independent of which of them carry defaults."""
    return catch_all or contains(positional, name) or contains(keyword_only, name)


@Pure
def outcome(supplied: PSeq[int], seen: PSeq[int],
            positional: PSeq[int], keyword_only: PSeq[int],
            catch_all: bool) -> int:
    """Outcome of binding the supplied-keyword run `supplied`, given the names
    `seen` already bound earlier in the run. Front-recursive (one unfold per
    supplied keyword) so a forward impl loop can discharge it. Returns 0 (OK),
    1 (UNEXPECTED), or 2 (DUPLICATE) -- the FIRST problematic keyword wins."""
    if len(supplied) == 0:
        return 0
    name = supplied[0]
    if not acceptable(positional, keyword_only, catch_all, name):
        return 1
    if contains(seen, name):
        return 2
    return outcome(supplied.drop(1), seen + PSeq(name),
                   positional, keyword_only, catch_all)
# pure-end


def bind_keywords(supplied: List[int], positional: PSeq[int],
                  keyword_only: PSeq[int], keyword_only_with_default: PSeq[int],
                  catch_all: bool) -> int:
    # pre-conditions-start
    # The supplied-keyword run is read-only (the binder inspects it, it does not
    # mutate it): required AND ensured at fractional permission (directive 5).
    # `positional` / `keyword_only` / `keyword_only_with_default` are pure
    # sequence values (the declared parameter-name sets); `catch_all` is a plain
    # bool. Well-formedness: every keyword-only name that carries a default is
    # itself a keyword-only name (defaults are a sub-collection of the keyword-
    # only parameters), which holds for every real callable.
    Requires(Acc(list_pred(supplied), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(
        0 <= k and k < len(keyword_only_with_default),
        contains(keyword_only, keyword_only_with_default[k])))))
    # TERMINATION: the binder must actually ANSWER — deciding the outcome of a
    # finite supplied-keyword run is a bounded computation (one step per
    # keyword). Nagini is a partial-correctness verifier by default, so without
    # this obligation a non-terminating implementation (e.g. an endless loop
    # before returning) satisfies the value postcondition vacuously; the real
    # binder always returns or raises its decision.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(supplied), 1 / 2))
    # The returned outcome is exactly the front-to-back binding decision: 0 OK,
    # 1 UNEXPECTED (an unacceptable keyword), 2 DUPLICATE (an acceptable keyword
    # supplied twice); the first problematic keyword determines it. Starting
    # from no keyword bound (empty `seen`). This pins the discriminating
    # behaviour: an acceptable keyword carrying a default is NOT unexpected, and
    # a repeated acceptable keyword is a DUPLICATE rather than UNEXPECTED.
    Ensures(Result() == outcome(ToSeq(supplied), PSeq(0).take(0),
                                positional, keyword_only, catch_all))
    # post-conditions-end
    # impl-start
    seen = PSeq(0).take(0)  # type: PSeq[int]
    i = 0
    while i < len(supplied):
        # invariants-start
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(0 <= i and i <= len(supplied))
        Invariant(seen == ToSeq(supplied).take(i))
        # The remaining computation from index `i` with the keywords bound so
        # far equals the total outcome (no problematic keyword has been seen yet
        # in indices < i, else the loop would have returned).
        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),
                          positional, keyword_only, catch_all) ==
                  outcome(ToSeq(supplied).drop(i), seen,
                          positional, keyword_only, catch_all))
        # the scan consumes the caller's termination obligation with a
        # strictly decreasing, bounded-below measure (len(supplied) - i),
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(supplied) - i + 1))
        # invariants-end
        name = supplied[i]
        Assert(ToSeq(supplied).drop(i)[0] == name)
        Assert(ToSeq(supplied).drop(i).drop(1) == ToSeq(supplied).drop(i + 1))
        Assert(ToSeq(supplied).take(i + 1) == seen + PSeq(name))
        if not acceptable(positional, keyword_only, catch_all, name):
            return 1
        if contains(seen, name):
            return 2
        seen = seen + PSeq(name)
        i = i + 1
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is value-complete: Ensures(Result() == outcome(ToSeq(supplied), PSeq(0).take(0), positional, keyword_only, catch_all)) pins the int return to EXACT functional equality with the frozen deep-model fold `outcome` over the full precondition domain (only extra precond is well-formedness defaults ⊆ kwonly, which excludes no real callable). So verify ⇒ value-equal-to-gold-fold ⇒ (via A-reference axiom_check == real fixed parse_bits) ⇒ resolves.

7 attacks built, ALL same-spec-confirmed (adversary same-spec exit 0 each). Verifications run concurrently in background batches of ≤3 (each spawns JVM+Z3). weakness command: `python -m swebench_unified.adversary weakness nagini django__django-12262 <atk>`:
- atk_1 prepatch bug (still_required/unhandled_kwargs): weakness exit 2 (does NOT verify) — spec catches the bug, matches G-DIFF. prepatch_reproduced=true.
- atk_2 constant return 0 (partial-domain): exit 2 (fails).
- atk_3 off-by-one boundary (skip last keyword): exit 2 (fails).
- atk_4 swapped guard order (duplicate before acceptability): exit 2 (fails).
- atk_5 ungrounded-oracle echo (return outcome(...) verbatim): exit 0 CANDIDATE (shares spec AND verifies).
- atk_6 acceptability wrongly requires a default (mis-models bug1): exit 2 (fails).
- atk_7 control-flow-effect ignore catch_all: exit 2 (fails).

MANDATORY candidate resolve: atk_5 returns exactly outcome(...) = the fixed gold decision, so its faithful refined patch is byte-identical to patch.diff (the `param not in kwonly` fix). Materialized as atk_5_faithful_patch.diff and RAN through the official harness (swebench_unified.run_evaluation, docker, run_id sbu-eq-atk5-loop1). Docker under heavy contention (heavy-250, 72-80 containers) forced several retries: initial run_resolve attempts hit Docker 60s client ReadTimeout in build_container and an images.list ImageNotFound race (both INFRA, not verdicts); resolved by monkeypatching docker.from_env timeout to 900s and looping. Report captured at report_final.json: resolved=true, 4/4 FAIL_TO_PASS pass (test_inclusion_tag_errors, test_inclusion_tags, test_simple_tag_errors, test_simple_tags), 18/18 PASS_TO_PASS pass. => atk_5 is a RESOLVING echo of the gold, NOT a weakness (per the G-EQ/G-PANEL-1 echo-attack policy: a same-spec verifying attack whose refined patch resolves is not a weakness).

Positive control: model.py verifies via scripts/nagini_verify.sh (exit 0, 15.6s).

refinement.md audit: every leg is R or I; ZERO consumed axioms (no A-consumed row — the changed op is a pure membership test modeled DEEPLY by outcome/acceptable/contains). One A-reference: the deep `outcome` model validated == the real fixed parse_bits keyword decision by axiom_check.py, which I ran (exit 0: 12 boundary + exhaustive small enumeration + 40000 fuzz inputs, prepatch differential confirmed on both issue witnesses). No kind-3 (unexpressible-changed-op) steps. A-reference correspondence HOLDS: axiom_check faithfully transcribes the post-patch condition `param not in params and param not in kwonly and varkw is None` including real unhandled_kwargs construction/consumption.

No verifying-but-incorrect impl found; the sole verifying candidate resolves. Gate SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of nagini django__django-12262. Spec region verifies (Nagini, 16s). The worktree at base_commit 69331bb is post-patch (condition `param not in params and param not in kwonly and varkw is None`), matching what model.py's `outcome` fold models. I drove the REAL repo `django/template/library.py:parse_bits` directly (mocking token_kwargs to turn each 'bit' into a keyword, FakeParser.compile_filter, mapping raised TemplateSyntaxError messages -> outcome codes: 'unexpected keyword'->1, 'multiple values'->2, 'did not receive value'/no-error->0) and compared to the model's outcome over (a) the exhaustive small enumeration (params/kwonly/defaults subsets of {a,b,c}, supplied length 0-3 over {z,a,b,c,x}, catch_all both = 19968 cases) and (b) 20000 randomized fuzz inputs over an 8-name universe. ZERO divergences. The correspondence holds exactly: acceptable = catch_all(=varkw is not None) OR name in positional(=params) OR name in keyword_only(=kwonly); DUPLICATE via contains(seen,name) <-> param in kwargs (kwargs keys are str(param) and param is always a string for real templates, so membership matches); first-problematic-keyword-wins ordering (UNEXPECTED before DUPLICATE) mirrors the real elif chain. NOTE: an early harness bug using integer names produced spurious 'model=2 real=0' divergences because real code stores kwargs[str(param)] while the guard reads `param in kwargs`; with integers `2 in {'2':...}` is False. This is a harness artifact, NOT a spec defect — in real Django param is a string. Corrected harness shows full agreement. Bundle axiom_check.py (G-AX) also passes independently. The MustTerminate obligation faithfully mirrors the bounded `for bit in bits:` scan and only excludes non-terminating impls. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `param not in unhandled_kwargs` -> `param not in kwonly` in django/template/library.py:parse_bits (i.e. test membership in the FULL keyword-only set rather than the required subset; also the UNEXPECTED-vs-DUPLICATE distinction). The public problem_statement ALREADY discloses both discriminators: (1) keyword-only args with defaults wrongly raise 'unexpected keyword argument', and (2) supplying a keyword twice raises 'unexpected keyword argument' instead of 'received multiple values for keyword argument'. The spec view states this same behaviour ABSTRACTLY, as desired behaviour not an edit: ACCEPTABLE = names a declared parameter (positional OR keyword-only) 'REGARDLESS of whether that keyword-only parameter carries a default', and UNEXPECTED/DUPLICATE are distinct outcomes. Nothing in the spec view exceeds the public statement. Mechanical G-LEAK screen passes (rep.passed=True, zero hard failures). Confirmed absent from the spec view: patched file path (library.py), patched module path, any gold-patch line, and every patched repo symbol (parse_bits, unhandled_kwargs, kwonly, varkw, template) — all False. No diff markers, no bug/fix narration (spec is phrased 'stated as desired behaviour, not as an edit'). The keyword_only_with_default modeling merely encodes the 'defaults govern only required-ness, not acceptability' fact the problem_statement already makes public. No leak beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
