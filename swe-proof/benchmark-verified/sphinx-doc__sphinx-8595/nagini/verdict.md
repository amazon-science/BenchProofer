# P2 adversarial audit — sphinx-doc__sphinx-8595

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously because this specification demanded no termination, which
> was true of it when that audit ran: Nagini proves partial correctness unless a
> precondition carries `MustTerminate`, so an implementation that never returns
> satisfied every `Ensures`. The specification now carries the obligation on its
> spec-surface methods, and because a rival must share the frozen preconditions
> it cannot drop it: a rival that diverges fails the obligation instead of
> verifying. No statement below that such a rival verifies, or that this
> specification has a divergence hole of that shape, describes the current
> artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -122,16 +122,12 @@
                                                        ToSeq(all_names))))
     # post-conditions-end
     # impl-start
-    if not all_present:
-        # for implicit module members, every discovered member is a candidate:
-        # none is excluded (the flags are already clear), and implicit
-        # membership is signalled.
+    if (not all_present) or len(all_names) == 0:
         return True
     else:
         seq = ToSeq(all_names)
         i = len(excluded)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(all_names), 1 / 2))
             Invariant(Acc(list_pred(member_names), 1 / 2))
             Invariant(Acc(list_pred(excluded)))
@@ -140,21 +136,12 @@
             Invariant(0 <= i and i <= len(excluded))
             Invariant(ToSeq(excluded).drop(i) ==
                       exclusion_flags(ToSeq(member_names).drop(i), seq))
-            # The loop consumes the termination obligation: `i` is the
-            # strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
             c = member_names[i - 1]
-            Assert(ToSeq(member_names).drop(i - 1)[0] == c)
-            Assert(ToSeq(member_names).drop(i - 1).drop(1) ==
-                   ToSeq(member_names).drop(i))
             if not contains(seq, c):
                 excluded[i - 1] = True
             else:
                 excluded[i - 1] = False
-            Assert(ToSeq(excluded)[i - 1] == (not contains(seq, c)))
-            Assert(ToSeq(excluded).drop(i - 1)[0] == ToSeq(excluded)[i - 1])
-            Assert(ToSeq(excluded).drop(i - 1).drop(1) == ToSeq(excluded).drop(i))
             i = i - 1
         return False
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,38 +123,23 @@
     # post-conditions-end
     # impl-start
     if not all_present:
-        # for implicit module members, every discovered member is a candidate:
-        # none is excluded (the flags are already clear), and implicit
-        # membership is signalled.
         return True
     else:
         seq = ToSeq(all_names)
         i = len(excluded)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(all_names), 1 / 2))
             Invariant(Acc(list_pred(member_names), 1 / 2))
             Invariant(Acc(list_pred(excluded)))
             Invariant(len(excluded) == len(member_names))
             Invariant(seq == ToSeq(all_names))
             Invariant(0 <= i and i <= len(excluded))
-            Invariant(ToSeq(excluded).drop(i) ==
-                      exclusion_flags(ToSeq(member_names).drop(i), seq))
-            # The loop consumes the termination obligation: `i` is the
-            # strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
             c = member_names[i - 1]
-            Assert(ToSeq(member_names).drop(i - 1)[0] == c)
-            Assert(ToSeq(member_names).drop(i - 1).drop(1) ==
-                   ToSeq(member_names).drop(i))
             if not contains(seq, c):
+                excluded[i - 1] = False
+            else:
                 excluded[i - 1] = True
-            else:
-                excluded[i - 1] = False
-            Assert(ToSeq(excluded)[i - 1] == (not contains(seq, c)))
-            Assert(ToSeq(excluded).drop(i - 1)[0] == ToSeq(excluded)[i - 1])
-            Assert(ToSeq(excluded).drop(i - 1).drop(1) == ToSeq(excluded).drop(i))
             i = i - 1
         return False
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,38 +123,7 @@
     # post-conditions-end
     # impl-start
     if not all_present:
-        # for implicit module members, every discovered member is a candidate:
-        # none is excluded (the flags are already clear), and implicit
-        # membership is signalled.
         return True
     else:
-        seq = ToSeq(all_names)
-        i = len(excluded)
-        while i > 0:
-            # invariants-start
-            Invariant(Acc(list_pred(all_names), 1 / 2))
-            Invariant(Acc(list_pred(member_names), 1 / 2))
-            Invariant(Acc(list_pred(excluded)))
-            Invariant(len(excluded) == len(member_names))
-            Invariant(seq == ToSeq(all_names))
-            Invariant(0 <= i and i <= len(excluded))
-            Invariant(ToSeq(excluded).drop(i) ==
-                      exclusion_flags(ToSeq(member_names).drop(i), seq))
-            # The loop consumes the termination obligation: `i` is the
-            # strictly decreasing, bounded-below measure.
-            Invariant(MustTerminate(i))
-            # invariants-end
-            c = member_names[i - 1]
-            Assert(ToSeq(member_names).drop(i - 1)[0] == c)
-            Assert(ToSeq(member_names).drop(i - 1).drop(1) ==
-                   ToSeq(member_names).drop(i))
-            if not contains(seq, c):
-                excluded[i - 1] = True
-            else:
-                excluded[i - 1] = False
-            Assert(ToSeq(excluded)[i - 1] == (not contains(seq, c)))
-            Assert(ToSeq(excluded).drop(i - 1)[0] == ToSeq(excluded)[i - 1])
-            Assert(ToSeq(excluded).drop(i - 1).drop(1) == ToSeq(excluded).drop(i))
-            i = i - 1
         return False
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,15 +123,11 @@
     # post-conditions-end
     # impl-start
     if not all_present:
-        # for implicit module members, every discovered member is a candidate:
-        # none is excluded (the flags are already clear), and implicit
-        # membership is signalled.
-        return True
+        return False
     else:
         seq = ToSeq(all_names)
         i = len(excluded)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(all_names), 1 / 2))
             Invariant(Acc(list_pred(member_names), 1 / 2))
             Invariant(Acc(list_pred(excluded)))
@@ -140,21 +136,12 @@
             Invariant(0 <= i and i <= len(excluded))
             Invariant(ToSeq(excluded).drop(i) ==
                       exclusion_flags(ToSeq(member_names).drop(i), seq))
-            # The loop consumes the termination obligation: `i` is the
-            # strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
             c = member_names[i - 1]
-            Assert(ToSeq(member_names).drop(i - 1)[0] == c)
-            Assert(ToSeq(member_names).drop(i - 1).drop(1) ==
-                   ToSeq(member_names).drop(i))
             if not contains(seq, c):
                 excluded[i - 1] = True
             else:
                 excluded[i - 1] = False
-            Assert(ToSeq(excluded)[i - 1] == (not contains(seq, c)))
-            Assert(ToSeq(excluded).drop(i - 1)[0] == ToSeq(excluded)[i - 1])
-            Assert(ToSeq(excluded).drop(i - 1).drop(1) == ToSeq(excluded).drop(i))
             i = i - 1
-        return False
+        return True
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,38 +123,23 @@
     # post-conditions-end
     # impl-start
     if not all_present:
-        # for implicit module members, every discovered member is a candidate:
-        # none is excluded (the flags are already clear), and implicit
-        # membership is signalled.
         return True
     else:
         seq = ToSeq(all_names)
-        i = len(excluded)
+        i = len(excluded) - 1
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(all_names), 1 / 2))
             Invariant(Acc(list_pred(member_names), 1 / 2))
             Invariant(Acc(list_pred(excluded)))
             Invariant(len(excluded) == len(member_names))
             Invariant(seq == ToSeq(all_names))
             Invariant(0 <= i and i <= len(excluded))
-            Invariant(ToSeq(excluded).drop(i) ==
-                      exclusion_flags(ToSeq(member_names).drop(i), seq))
-            # The loop consumes the termination obligation: `i` is the
-            # strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
             c = member_names[i - 1]
-            Assert(ToSeq(member_names).drop(i - 1)[0] == c)
-            Assert(ToSeq(member_names).drop(i - 1).drop(1) ==
-                   ToSeq(member_names).drop(i))
             if not contains(seq, c):
                 excluded[i - 1] = True
             else:
                 excluded[i - 1] = False
-            Assert(ToSeq(excluded)[i - 1] == (not contains(seq, c)))
-            Assert(ToSeq(excluded).drop(i - 1)[0] == ToSeq(excluded)[i - 1])
-            Assert(ToSeq(excluded).drop(i - 1).drop(1) == ToSeq(excluded).drop(i))
             i = i - 1
         return False
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,38 +123,17 @@
     # post-conditions-end
     # impl-start
     if not all_present:
-        # for implicit module members, every discovered member is a candidate:
-        # none is excluded (the flags are already clear), and implicit
-        # membership is signalled.
         return True
     else:
-        seq = ToSeq(all_names)
         i = len(excluded)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(all_names), 1 / 2))
             Invariant(Acc(list_pred(member_names), 1 / 2))
             Invariant(Acc(list_pred(excluded)))
             Invariant(len(excluded) == len(member_names))
-            Invariant(seq == ToSeq(all_names))
             Invariant(0 <= i and i <= len(excluded))
-            Invariant(ToSeq(excluded).drop(i) ==
-                      exclusion_flags(ToSeq(member_names).drop(i), seq))
-            # The loop consumes the termination obligation: `i` is the
-            # strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
-            c = member_names[i - 1]
-            Assert(ToSeq(member_names).drop(i - 1)[0] == c)
-            Assert(ToSeq(member_names).drop(i - 1).drop(1) ==
-                   ToSeq(member_names).drop(i))
-            if not contains(seq, c):
-                excluded[i - 1] = True
-            else:
-                excluded[i - 1] = False
-            Assert(ToSeq(excluded)[i - 1] == (not contains(seq, c)))
-            Assert(ToSeq(excluded).drop(i - 1)[0] == ToSeq(excluded)[i - 1])
-            Assert(ToSeq(excluded).drop(i - 1).drop(1) == ToSeq(excluded).drop(i))
+            excluded[i - 1] = True
             i = i - 1
         return False
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -123,38 +123,22 @@
     # post-conditions-end
     # impl-start
     if not all_present:
-        # for implicit module members, every discovered member is a candidate:
-        # none is excluded (the flags are already clear), and implicit
-        # membership is signalled.
         return True
     else:
         seq = ToSeq(all_names)
         i = len(excluded)
         while i > 0:
-            # invariants-start
             Invariant(Acc(list_pred(all_names), 1 / 2))
             Invariant(Acc(list_pred(member_names), 1 / 2))
             Invariant(Acc(list_pred(excluded)))
             Invariant(len(excluded) == len(member_names))
             Invariant(seq == ToSeq(all_names))
             Invariant(0 <= i and i <= len(excluded))
-            Invariant(ToSeq(excluded).drop(i) ==
-                      exclusion_flags(ToSeq(member_names).drop(i), seq))
-            # The loop consumes the termination obligation: `i` is the
-            # strictly decreasing, bounded-below measure.
             Invariant(MustTerminate(i))
-            # invariants-end
             c = member_names[i - 1]
-            Assert(ToSeq(member_names).drop(i - 1)[0] == c)
-            Assert(ToSeq(member_names).drop(i - 1).drop(1) ==
-                   ToSeq(member_names).drop(i))
             if not contains(seq, c):
                 excluded[i - 1] = True
             else:
                 excluded[i - 1] = False
-            Assert(ToSeq(excluded)[i - 1] == (not contains(seq, c)))
-            Assert(ToSeq(excluded).drop(i - 1)[0] == ToSeq(excluded)[i - 1])
-            Assert(ToSeq(excluded).drop(i - 1).drop(1) == ToSeq(excluded).drop(i))
-            i = i - 1
         return False
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8595.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When automatic documentation is asked to expand the full membership of a
  module, the module's optional explicit export list governs which members are
  retained. The two cases are distinguished by whether the export list is
  ABSENT versus merely EMPTY:

    (1) The export list is ABSENT (the module declares none). Then membership
        is implicit: the routine reports that every discovered member is a
        candidate (the implicit-membership flag is true) and leaves the
        discovered members untouched, marking none of them as excluded.

    (2) The export list is PRESENT — INCLUDING when it is the empty list. Then
        membership is explicit: the routine reports that membership is NOT
        implicit (the flag is false) and, for each discovered member, marks the
        member as excluded exactly when its name is NOT one of the listed
        export names. In particular, a present-but-empty export list excludes
        EVERY discovered member and retains none.

  The discovered members are always returned in full; their per-member
  exclusion flags carry which ones survive. The export list and the member
  names are read-only. The routine always ANSWERS: selecting against a finite
  member set and a finite export list is a bounded scan, so termination is a
  correctness obligation (carried as MustTerminate in the precondition).

Type abstraction (refinement.md / mapping.md): the optional export list
`Optional[Sequence[str]]` is carried by `(all_present: bool, all_names:
List[int])` — `all_present` is whether the list is declared (`None` ↦ False),
`all_names` the export name identifiers (empty when undeclared or declared
empty). The discovered members are two index-aligned carriers: a read-only
`List[int]` of member name identifiers and a mutable `List[bool]` of the
per-member exclusion flags, the latter cleared on entry (a freshly discovered
member is not excluded until proven so). String names are abstracted to integer
identifiers (equal ints == equal names). Membership and the per-member
exclusion vector are carried by a front-recursive pure sequence theory.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. The membership test and the absent-vs-empty distinction
# are pure structural logic, modelled deeply (`contains` / `exclusion_flags`).
# The discovery of the module member set is upstream of the modelled function
# and is not consumed here.
# axioms-end

# pure-start
@Pure
def contains(names: PSeq[int], v: int) -> bool:
    """True iff the export-name identifier `v` occurs in the export-name
    sequence `names`. Front-recursive so a single unfold is available per
    loop step. On the empty sequence it is uniformly false."""
    if len(names) == 0:
        return False
    return names[0] == v or contains(names.drop(1), v)

@Pure
def exclusion_flags(member_names: PSeq[int], all_names: PSeq[int]) -> PSeq[bool]:
    """The per-member exclusion vector against a PRESENT export list: member k
    is excluded (True) exactly when its name is not in `all_names`. Front-
    recursive, index-aligned with `member_names`. For an empty `all_names`
    every entry is True (nothing is exported)."""
    if len(member_names) == 0:
        return PSeq(False).take(0)
    return (PSeq(not contains(all_names, member_names[0])) +
            exclusion_flags(member_names.drop(1), all_names))
# pure-end

def select_module_members(member_names: List[int],
                          excluded: List[bool],
                          all_present: bool,
                          all_names: List[int]) -> bool:
    # pre-conditions-start
    # The export name list is read-only: fractional permission, required AND
    # ensured. (`all_names` is empty when the export list is undeclared.)
    Requires(Acc(list_pred(all_names), 1 / 2))
    # The discovered member names are read-only.
    Requires(Acc(list_pred(member_names), 1 / 2))
    # The per-member exclusion flags are written in place: full permission,
    # index-aligned with the member names, and cleared on entry (the default
    # state of a freshly discovered member).
    Requires(Acc(list_pred(excluded)))
    Requires(len(excluded) == len(member_names))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(excluded),
                                             ToSeq(excluded)[k] == False),
                                     [[ToSeq(excluded)[k]]])))
    # TERMINATION: the real routine scans the finite discovered-member set
    # against the finite export list and always returns. Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. a loop that never advances its
    # index) satisfies every Ensures vacuously; the real selection always
    # answers.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(all_names), 1 / 2))
    Ensures(Acc(list_pred(member_names), 1 / 2))
    Ensures(Acc(list_pred(excluded)))
    # The full member set is preserved (length unchanged).
    Ensures(len(excluded) == len(member_names))
    # (1) ABSENT export list: implicit membership signalled, nothing excluded.
    Ensures(Implies(not all_present, Result() == True))
    Ensures(Implies(not all_present,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(excluded),
                                                   ToSeq(excluded)[k] == False),
                                           [[ToSeq(excluded)[k]]]))))
    # (2) PRESENT export list (incl. empty): explicit membership signalled, and
    # each member is excluded exactly when its name is not an export name. For a
    # present-but-empty list `exclusion_flags` is uniformly True.
    Ensures(Implies(all_present, Result() == False))
    Ensures(Implies(all_present,
                    ToSeq(excluded) == exclusion_flags(ToSeq(member_names),
                                                       ToSeq(all_names))))
    # post-conditions-end
    # impl-start
    if not all_present:
        # for implicit module members, every discovered member is a candidate:
        # none is excluded (the flags are already clear), and implicit
        # membership is signalled.
        return True
    else:
        seq = ToSeq(all_names)
        i = len(excluded)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(all_names), 1 / 2))
            Invariant(Acc(list_pred(member_names), 1 / 2))
            Invariant(Acc(list_pred(excluded)))
            Invariant(len(excluded) == len(member_names))
            Invariant(seq == ToSeq(all_names))
            Invariant(0 <= i and i <= len(excluded))
            Invariant(ToSeq(excluded).drop(i) ==
                      exclusion_flags(ToSeq(member_names).drop(i), seq))
            # The loop consumes the termination obligation: `i` is the
            # strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(i))
            # invariants-end
            c = member_names[i - 1]
            Assert(ToSeq(member_names).drop(i - 1)[0] == c)
            Assert(ToSeq(member_names).drop(i - 1).drop(1) ==
                   ToSeq(member_names).drop(i))
            if not contains(seq, c):
                excluded[i - 1] = True
            else:
                excluded[i - 1] = False
            Assert(ToSeq(excluded)[i - 1] == (not contains(seq, c)))
            Assert(ToSeq(excluded).drop(i - 1)[0] == ToSeq(excluded)[i - 1])
            Assert(ToSeq(excluded).drop(i - 1).drop(1) == ToSeq(excluded).drop(i))
            i = i - 1
        return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for sphinx-doc__sphinx-8595 (nagini). env, SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE: the frozen spec pins EVERY observable output with no slack. Result() is fully determined in both branches (Implies(not all_present, Result()==True); Implies(all_present, Result()==False)); excluded is pinned all-False when absent and == exclusion_flags(member_names, all_names) when present; length preserved; and Requires(MustTerminate(2)) closes the classic partial-correctness vacuous-Ensures hole. An incorrect-but-verifying impl should therefore be impossible.

ATTACKS: all 7 confirmed same-spec via `adversary same-spec` exit 0 (spec_signature byte-identical incl. axioms/@Pure/Requires/Ensures); each built by copying model.py and editing ONLY the impl region. Verified via `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8595 <path>` run in 3 background batches of <=3 (each spawns JVM+Z3): atk_1 PREPATCH BUG `(not all_present) or len(all_names)==0` -> FAILED (weakness exit 2). `adversary verify` detail: Postcondition Implies(all_present, Result()==False) might not hold @119 -> exactly refinement.md section B G-DIFF.

PREPATCH REPRODUCED. atk_2 FLAG-FLIP (invert exclusion assignment) -> FAILED exit 2; detail: Implies(all_present, ToSeq(excluded)==exclusion_flags(...)) might not hold @120. atk_3 PARTIAL-DOMAIN (present branch returns False, leaves flags clear, no loop) -> FAILED exit 2. atk_4 RESULT-SWAP (return False for absent / True for present) -> FAILED exit 2. atk_5 BOUNDARY off-by-one (loop starts at len-1) -> FAILED exit 2. atk_6 ALWAYS-EXCLUDE (present branch sets every flag True, ignores contains) -> FAILED exit 2. atk_7 CONTROL-FLOW / non-termination (present-branch loop never advances i) -> FAILED exit 2; detail: Obligation leak check failed, Loop might not keep promise to terminate @130 -> confirms MustTerminate closes the vacuous-Ensures hole. No attack returned CANDIDATE, so there are no faithful patches to materialize/resolve (patches={}).

POSITIVE CONTROL: model.py copied verbatim -> VERIFIED in 16.9s (exit 0). Same-spec exit 0.

A-LEG / model-correspondence audit (my mandated focus): refinement.md legs are A1=R, A2=R, A3=R+I, A4=A-reference+I, A5=I — every leg is R / A-reference / I; section C explicitly asserts NO kind-3 and NO consumed @ContractOnly axioms (confirmed against model.py axioms-start/-end: none). The two A-REFERENCE deep models are contains <-> Python `in` (mapping 3.1) and exclusion_flags <-> the repo `else`-branch skipping loop sphinx/ext/autodoc/__init__.py:1081-1086 (mapping 3.2), plus the fix distinction `self.__all__ is None` vs pre-patch truthiness `not self.__all__` (3.3). Ran axiom_check.py (G-AX): exit 0 — 'contains == Python `in` and exclusion_flags == repo skip loop over 21 boundary + 40000 fuzz cases; is-None-vs-truthiness distinction holds for None/[]/present lists.' Correspondence to the real callee holds. patch.diff (../patch.diff) is the gold verbatim, single-line change `not self.__all__` -> `self.__all__ is None`, matching refinement.md section A hunk exactly.

VERDICT: SOUND. >=5 (7) distinct same-spec wrong impls (prepatch, flag-flip, partial-domain, result-swap, boundary, always-exclude, non-terminating) all rejected by the pinned Nagini verifier with semantic (not infra/timeout) failures on the precise pinned clauses; positive control verifies; prepatch reproduced on exactly the G-DIFF clause; G-AX A-reference validation passes; all refinement legs R/A-reference/I with no kind-3. No verifying wrong impl exists, so verify=>correct holds for this spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for sphinx-doc__sphinx-8595.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When automatic documentation is asked to expand the full membership of a
  module, the module's optional explicit export list governs which members are
  retained. The two cases are distinguished by whether the export list is
  ABSENT versus merely EMPTY:

    (1) The export list is ABSENT (the module declares none). Then membership
        is implicit: the routine reports that every discovered member is a
        candidate (the implicit-membership flag is true) and leaves the
        discovered members untouched, marking none of them as excluded.

    (2) The export list is PRESENT — INCLUDING when it is the empty list. Then
        membership is explicit: the routine reports that membership is NOT
        implicit (the flag is false) and, for each discovered member, marks the
        member as excluded exactly when its name is NOT one of the listed
        export names. In particular, a present-but-empty export list excludes
        EVERY discovered member and retains none.

  The discovered members are always returned in full; their per-member
  exclusion flags carry which ones survive. The export list and the member
  names are read-only. The routine always ANSWERS: selecting against a finite
  member set and a finite export list is a bounded scan, so termination is a
  correctness obligation (carried as MustTerminate in the precondition).

Type abstraction (refinement.md / mapping.md): the optional export list
`Optional[Sequence[str]]` is carried by `(all_present: bool, all_names:
List[int])` — `all_present` is whether the list is declared (`None` ↦ False),
`all_names` the export name identifiers (empty when undeclared or declared
empty). The discovered members are two index-aligned carriers: a read-only
`List[int]` of member name identifiers and a mutable `List[bool]` of the
per-member exclusion flags, the latter cleared on entry (a freshly discovered
member is not excluded until proven so). String names are abstracted to integer
identifiers (equal ints == equal names). Membership and the per-member
exclusion vector are carried by a front-recursive pure sequence theory.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# No consumed axioms. The membership test and the absent-vs-empty distinction
# are pure structural logic, modelled deeply (`contains` / `exclusion_flags`).
# The discovery of the module member set is upstream of the modelled function
# and is not consumed here.
# axioms-end

# pure-start
@Pure
def contains(names: PSeq[int], v: int) -> bool:
    """True iff the export-name identifier `v` occurs in the export-name
    sequence `names`. Front-recursive so a single unfold is available per
    loop step. On the empty sequence it is uniformly false."""
    if len(names) == 0:
        return False
    return names[0] == v or contains(names.drop(1), v)

@Pure
def exclusion_flags(member_names: PSeq[int], all_names: PSeq[int]) -> PSeq[bool]:
    """The per-member exclusion vector against a PRESENT export list: member k
    is excluded (True) exactly when its name is not in `all_names`. Front-
    recursive, index-aligned with `member_names`. For an empty `all_names`
    every entry is True (nothing is exported)."""
    if len(member_names) == 0:
        return PSeq(False).take(0)
    return (PSeq(not contains(all_names, member_names[0])) +
            exclusion_flags(member_names.drop(1), all_names))
# pure-end

def select_module_members(member_names: List[int],
                          excluded: List[bool],
                          all_present: bool,
                          all_names: List[int]) -> bool:
    # pre-conditions-start
    # The export name list is read-only: fractional permission, required AND
    # ensured. (`all_names` is empty when the export list is undeclared.)
    Requires(Acc(list_pred(all_names), 1 / 2))
    # The discovered member names are read-only.
    Requires(Acc(list_pred(member_names), 1 / 2))
    # The per-member exclusion flags are written in place: full permission,
    # index-aligned with the member names, and cleared on entry (the default
    # state of a freshly discovered member).
    Requires(Acc(list_pred(excluded)))
    Requires(len(excluded) == len(member_names))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(excluded),
                                             ToSeq(excluded)[k] == False),
                                     [[ToSeq(excluded)[k]]])))
    # TERMINATION: the real routine scans the finite discovered-member set
    # against the finite export list and always returns. Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. a loop that never advances its
    # index) satisfies every Ensures vacuously; the real selection always
    # answers.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(all_names), 1 / 2))
    Ensures(Acc(list_pred(member_names), 1 / 2))
    Ensures(Acc(list_pred(excluded)))
    # The full member set is preserved (length unchanged).
    Ensures(len(excluded) == len(member_names))
    # (1) ABSENT export list: implicit membership signalled, nothing excluded.
    Ensures(Implies(not all_present, Result() == True))
    Ensures(Implies(not all_present,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(excluded),
                                                   ToSeq(excluded)[k] == False),
                                           [[ToSeq(excluded)[k]]]))))
    # (2) PRESENT export list (incl. empty): explicit membership signalled, and
    # each member is excluded exactly when its name is not an export name. For a
    # present-but-empty list `exclusion_flags` is uniformly True.
    Ensures(Implies(all_present, Result() == False))
    Ensures(Implies(all_present,
                    ToSeq(excluded) == exclusion_flags(ToSeq(member_names),
                                                       ToSeq(all_names))))
    # post-conditions-end
    # impl-start
    if not all_present:
        # for implicit module members, every discovered member is a candidate:
        # none is excluded (the flags are already clear), and implicit
        # membership is signalled.
        return True
    else:
        seq = ToSeq(all_names)
        i = len(excluded)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(all_names), 1 / 2))
            Invariant(Acc(list_pred(member_names), 1 / 2))
            Invariant(Acc(list_pred(excluded)))
            Invariant(len(excluded) == len(member_names))
            Invariant(seq == ToSeq(all_names))
            Invariant(0 <= i and i <= len(excluded))
            Invariant(ToSeq(excluded).drop(i) ==
                      exclusion_flags(ToSeq(member_names).drop(i), seq))
            # The loop consumes the termination obligation: `i` is the
            # strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(i))
            # invariants-end
            c = member_names[i - 1]
            Assert(ToSeq(member_names).drop(i - 1)[0] == c)
            Assert(ToSeq(member_names).drop(i - 1).drop(1) ==
                   ToSeq(member_names).drop(i))
            if not contains(seq, c):
                excluded[i - 1] = True
            else:
                excluded[i - 1] = False
            Assert(ToSeq(excluded)[i - 1] == (not contains(seq, c)))
            Assert(ToSeq(excluded).drop(i - 1)[0] == ToSeq(excluded)[i - 1])
            Assert(ToSeq(excluded).drop(i - 1).drop(1) == ToSeq(excluded).drop(i))
            i = i - 1
        return False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for sphinx-doc__sphinx-8595 (nagini). env, SBU_BENCHMARK_DIR=benchmark-verified.

SPEC SHAPE: the frozen spec pins EVERY observable output with no slack. Result() is fully determined in both branches (Implies(not all_present, Result()==True); Implies(all_present, Result()==False)); excluded is pinned all-False when absent and == exclusion_flags(member_names, all_names) when present; length preserved; and Requires(MustTerminate(2)) closes the classic partial-correctness vacuous-Ensures hole. An incorrect-but-verifying impl should therefore be impossible.

ATTACKS: all 7 confirmed same-spec via `adversary same-spec` exit 0 (spec_signature byte-identical incl. axioms/@Pure/Requires/Ensures); each built by copying model.py and editing ONLY the impl region. Verified via `python -m swebench_unified.adversary weakness nagini sphinx-doc__sphinx-8595 <path>` run in 3 background batches of <=3 (each spawns JVM+Z3): atk_1 PREPATCH BUG `(not all_present) or len(all_names)==0` -> FAILED (weakness exit 2). `adversary verify` detail: Postcondition Implies(all_present, Result()==False) might not hold @119 -> exactly refinement.md section B G-DIFF.

PREPATCH REPRODUCED. atk_2 FLAG-FLIP (invert exclusion assignment) -> FAILED exit 2; detail: Implies(all_present, ToSeq(excluded)==exclusion_flags(...)) might not hold @120. atk_3 PARTIAL-DOMAIN (present branch returns False, leaves flags clear, no loop) -> FAILED exit 2. atk_4 RESULT-SWAP (return False for absent / True for present) -> FAILED exit 2. atk_5 BOUNDARY off-by-one (loop starts at len-1) -> FAILED exit 2. atk_6 ALWAYS-EXCLUDE (present branch sets every flag True, ignores contains) -> FAILED exit 2. atk_7 CONTROL-FLOW / non-termination (present-branch loop never advances i) -> FAILED exit 2; detail: Obligation leak check failed, Loop might not keep promise to terminate @130 -> confirms MustTerminate closes the vacuous-Ensures hole. No attack returned CANDIDATE, so there are no faithful patches to materialize/resolve (patches={}).

POSITIVE CONTROL: model.py copied verbatim -> VERIFIED in 16.9s (exit 0). Same-spec exit 0.

A-LEG / model-correspondence audit (my mandated focus): refinement.md legs are A1=R, A2=R, A3=R+I, A4=A-reference+I, A5=I — every leg is R / A-reference / I; section C explicitly asserts NO kind-3 and NO consumed @ContractOnly axioms (confirmed against model.py axioms-start/-end: none). The two A-REFERENCE deep models are contains <-> Python `in` (mapping 3.1) and exclusion_flags <-> the repo `else`-branch skipping loop sphinx/ext/autodoc/__init__.py:1081-1086 (mapping 3.2), plus the fix distinction `self.__all__ is None` vs pre-patch truthiness `not self.__all__` (3.3). Ran axiom_check.py (G-AX): exit 0 — 'contains == Python `in` and exclusion_flags == repo skip loop over 21 boundary + 40000 fuzz cases; is-None-vs-truthiness distinction holds for None/[]/present lists.' Correspondence to the real callee holds. patch.diff (../patch.diff) is the gold verbatim, single-line change `not self.__all__` -> `self.__all__ is None`, matching refinement.md section A hunk exactly.

VERDICT: SOUND. >=5 (7) distinct same-spec wrong impls (prepatch, flag-flip, partial-domain, result-swap, boundary, always-exclude, non-terminating) all rejected by the pinned Nagini verifier with semantic (not infra/timeout) failures on the precise pinned clauses; positive control verifies; prepatch reproduced on exactly the G-DIFF clause; G-AX A-reference validation passes; all refinement legs R/A-reference/I with no kind-3. No verifying wrong impl exists, so verify=>correct holds for this spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sphinx-doc__sphinx-8595 (nagini). Modeled function select_module_members models ModuleDocumenter.get_object_members's want_all=True path (gold patch: `if not self.__all__:` -> `if self.__all__ is None:`).

Spec decoded from the postconditions (strongest reading, which fully pins both Result and the excluded vector):
  - not all_present (self.__all__ is None): Result==True, excluded[k]==False for all k.
  - all_present (list/tuple incl. empty): Result==False, excluded[k]== (member_names[k] not in all_names).

Built an INDEPENDENT differential (not the bundle's conformance_check.py): computed the spec's determined output directly and diffed against the REAL patched repo callee driven through a minimal ModuleDocumenter subclass at base_commit b19bce97 + gold patch. Ran it with a docutils-capable venv.

Coverage: all boundary shapes (absent/empty-present/disjoint/overlap/superset/dup exports/tuple __all__), plus adversarial cases designed to break the truthiness/identity abstraction and the int-identifier abstraction: empty-string member names, falsy int name 0, falsy bool names, set-shaped and str-shaped __all__, and int-vs-bool equality (1 vs True). Plus 50,000 randomized fuzz inputs over both str and int name pools. TOTAL DIVERGENCES: 0.

Crucially the crux case (present-but-empty __all__ = [] / ()): spec gives Result==False and every member excluded; real patched callee agrees (empty list is present-by-identity so the else-branch excludes everything). No falsy-empty confusion: the model uses all_present (identity) not truthiness, matching `is None`.

The abstraction boundaries hold: (a) equal-names<->equal-ints is exact because the callee only observes name equality via `in`; (b) the member-set-preservation Ensures matches (real returns list(members.values()) unchanged, names/count preserved); (c) MustTerminate is a genuine obligation the real bounded scan satisfies, not a strengthening that excludes real behavior. G-AX, G-CONF (100021 inputs, 0 disagreements), G-DIFF, G-GOLD all pass and are consistent. same-spec confirms the bundle spec region is the frozen spec.

No input found where the modeled function disagrees with the real repo callee. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen over the projected spec_view) PASSES with zero hard_failures. Substantive review confirms no leak beyond the public problem_statement.

Gold edit: `if not self.__all__:` -> `if self.__all__ is None:` in ModuleDocumenter.get_object_members (sphinx/ext/autodoc/__init__.py). The insight is that an EMPTY __all__ must be treated as PRESENT (exclude every member), distinct from ABSENT (None).

The public problem_statement already fully discloses this WHAT: it is titled 'autodoc: empty __all__ attribute is ignored', shows the reproducer with `__all__ = []`, and states the expected behavior 'No entries should be shown because __all__ is empty.' So the absent-vs-empty distinction and the desired outcome are public via the task.

The spec view (verified: impl region elided to `...`) only restates this desired BEHAVIOUR abstractly over an Optional[Sequence[str]] carried by (all_present, all_names): absent => implicit membership, nothing excluded; present-incl-empty => explicit, exclude each member not in the export list. It does NOT: (a) name the patched file/module path, (b) name the patched repo symbols get_object_members/get_module_members (spec uses the neutral name select_module_members), (c) reproduce the gold diff line or the `is None`-vs-truthiness code mechanism, (d) contain bug/fix narration. The solver still must derive the code change (which condition, which file, which symbol). Nothing in the spec view exceeds the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
