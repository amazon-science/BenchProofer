# P2 adversarial audit — scikit-learn__scikit-learn-14710

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -102,16 +102,10 @@
                 ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                 [[ToSeq(result)[k]]])))
             # invariants-end
-            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
-            Assert(ToSeq(target)[i] == target[i])
-            Assert(0 <= target[i] and target[i] < len(labels))
-            old_seq = ToSeq(result)  # type: PSeq[int]
-            result = result + [labels[target[i]]]
-            # the append preserves every earlier element and sets index i
-            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
-            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
+            # PRE-PATCH BUG: the classifier target is forwarded WITHOUT being
+            # decoded back to the original class values, so the result holds the
+            # internal indices rather than labels[target[i]].
+            result = result + [target[i]]
             i = i + 1
         return result
     else:
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -102,16 +102,12 @@
                 ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                 [[ToSeq(result)[k]]])))
             # invariants-end
-            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
-            Assert(ToSeq(target)[i] == target[i])
-            Assert(0 <= target[i] and target[i] < len(labels))
-            old_seq = ToSeq(result)  # type: PSeq[int]
-            result = result + [labels[target[i]]]
-            # the append preserves every earlier element and sets index i
-            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
-            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
+            # PARTIAL-DOMAIN BUG: decode every index except i==0, which is
+            # forwarded raw (internal index) instead of labels[target[0]].
+            if i == 0:
+                result = result + [target[i]]
+            else:
+                result = result + [labels[target[i]]]
             i = i + 1
         return result
     else:
@@ -173,16 +169,12 @@
                 ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                 [[ToSeq(result)[k]]])))
             # invariants-end
-            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
-            Assert(ToSeq(target)[i] == target[i])
-            Assert(0 <= target[i] and target[i] < len(labels))
-            old_seq = ToSeq(result)  # type: PSeq[int]
-            result = result + [labels[target[i]]]
-            # the append preserves every earlier element and sets index i
-            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
-            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
+            # PARTIAL-DOMAIN BUG: decode every index except i==0, which is
+            # forwarded raw (internal index) instead of labels[target[0]].
+            if i == 0:
+                result = result + [target[i]]
+            else:
+                result = result + [labels[target[i]]]
             i = i + 1
         return result
     else:
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
     if is_clf:
         result = []  # type: List[int]
         i = 0
-        while i < len(target):
+        while i < len(target) - 1:
             # invariants-start
             Invariant(Acc(list_pred(labels), 1 / 2))
             Invariant(Acc(list_pred(target), 1 / 2))
@@ -102,16 +102,9 @@
                 ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                 [[ToSeq(result)[k]]])))
             # invariants-end
-            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
-            Assert(ToSeq(target)[i] == target[i])
-            Assert(0 <= target[i] and target[i] < len(labels))
-            old_seq = ToSeq(result)  # type: PSeq[int]
+            # OFF-BY-ONE BUG: append decoded value but the loop guard below
+            # stops one element early, so Result is one element short.
             result = result + [labels[target[i]]]
-            # the append preserves every earlier element and sets index i
-            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
-            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
             i = i + 1
         return result
     else:
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -102,16 +102,8 @@
                 ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                 [[ToSeq(result)[k]]])))
             # invariants-end
-            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
-            Assert(ToSeq(target)[i] == target[i])
-            Assert(0 <= target[i] and target[i] < len(labels))
-            old_seq = ToSeq(result)  # type: PSeq[int]
-            result = result + [labels[target[i]]]
-            # the append preserves every earlier element and sets index i
-            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
-            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
+            # SWAP BUG: classifier forwards the internal index (raw).
+            result = result + [target[i]]
             i = i + 1
         return result
     else:
@@ -125,9 +117,7 @@
             Invariant(0 <= j and j <= len(target))
             Invariant(ToSeq(out) == ToSeq(target).take(j))
             # invariants-end
-            out = out + [target[j]]
-            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
-                   ToSeq(target).take(j + 1))
+            out = out + [decode_one(ToSeq(labels), target[j])]
             j = j + 1
         return out
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -125,9 +125,7 @@
             Invariant(0 <= j and j <= len(target))
             Invariant(ToSeq(out) == ToSeq(target).take(j))
             # invariants-end
-            out = out + [target[j]]
-            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
-                   ToSeq(target).take(j + 1))
+            out = out + [decode_one(ToSeq(labels), target[j])]
             j = j + 1
         return out
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -173,16 +173,10 @@
                 ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                 [[ToSeq(result)[k]]])))
             # invariants-end
-            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
-            Assert(ToSeq(target)[i] == target[i])
-            Assert(0 <= target[i] and target[i] < len(labels))
-            old_seq = ToSeq(result)  # type: PSeq[int]
-            result = result + [labels[target[i]]]
-            # the append preserves every earlier element and sets index i
-            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
-            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
+            # PRE-PATCH BUG: the held-out classifier target is forwarded WITHOUT
+            # being decoded back to the original class values, so the result
+            # holds the internal indices rather than labels[target[i]].
+            result = result + [target[i]]
             i = i + 1
         return result
     else:
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -102,16 +102,9 @@
                 ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                 [[ToSeq(result)[k]]])))
             # invariants-end
-            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
-            Assert(ToSeq(target)[i] == target[i])
-            Assert(0 <= target[i] and target[i] < len(labels))
-            old_seq = ToSeq(result)  # type: PSeq[int]
-            result = result + [labels[target[i]]]
-            # the append preserves every earlier element and sets index i
-            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
-            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
+            # CONSTANT BUG: every position gets labels[target[0]] instead of
+            # labels[target[i]] (ungrounded — ignores i).
+            result = result + [labels[target[0]]]
             i = i + 1
         return result
     else:
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -102,16 +102,8 @@
                 ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                 [[ToSeq(result)[k]]])))
             # invariants-end
-            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
-            Assert(ToSeq(target)[i] == target[i])
-            Assert(0 <= target[i] and target[i] < len(labels))
-            old_seq = ToSeq(result)  # type: PSeq[int]
-            result = result + [labels[target[i]]]
-            # the append preserves every earlier element and sets index i
-            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
-            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
-            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
+            # LENGTH BUG: append the decoded value twice (Result too long).
+            result = result + [labels[target[i]], labels[target[i]]]
             i = i + 1
         return result
     else:
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-14710.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an estimator monitors its own progress with a scorer, it must hand that
  scorer a target that lives in the SAME representation as the values the
  estimator's prediction routine produces. A classifying estimator stores its
  targets internally as integer indices `0 .. k-1` into a table `labels` of the
  distinct original class values, and its prediction routine emits the ORIGINAL
  class values (`labels[index]`). Therefore, before being scored, a classifier's
  internally-held target index `t` must be mapped back to the original value it
  addresses; element `i` of the target handed to the scorer equals
  `labels[target[i]]`. A non-classifying estimator holds and predicts targets in
  one and the same representation, so its target is handed to the scorer
  unchanged. The same rule applies to BOTH the always-present primary target and
  the optional secondary (held-out) target.

Targets and the label table are modelled as `List[int]` (Nagini bans rich
arrays); the index-into-table read is the element-wise gather `labels[target]`,
modelled DEEPLY (spelled out as the per-element `decode_one`); there is no
consumed axiom. The specification is carried over `PSeq[int]` via `ToSeq`.

Two structurally independent sites are specified (primary target, secondary
target); the per-function regions repeat, one set per site.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the only changed operation — the index-into-table
# decode — is modelled deeply by the per-element `decode_one` gather below and
# validated against the real callee by axiom_check.py / G-AX. There is no
# unchanged library callee whose contract the proof consumes.)
# axioms-end


# pure-start
@Pure
def in_index_range(labels: PSeq[int], t: PSeq[int]) -> bool:
    """Every internal target index addresses a real entry of the label table:
    `0 <= t[i] < len(labels)` for all `i`. This is the standing invariant of a
    label-encoded classification target."""
    return Forall(int, lambda i: (Implies(0 <= i and i < len(t),
                                          0 <= t[i] and t[i] < len(labels)),
                                  [[t[i]]]))


@Pure
def decode_one(labels: PSeq[int], x: int) -> int:
    """Decode a single internal index `x` to the original class value it
    addresses: `labels[x]` when `x` is a valid index. The out-of-range branch is
    never taken for a label-encoded target (see `in_index_range`); it only makes
    the gather total so it carries no precondition."""
    if 0 <= x and x < len(labels):
        return labels[x]
    return x
# pure-end


def primary_score_target(is_clf: bool, labels: List[int],
                         target: List[int]) -> List[int]:
    """The primary (always-scored) target, in the representation handed to the
    scorer."""
    # pre-conditions-start
    Requires(Acc(list_pred(labels), 1 / 2))
    Requires(Acc(list_pred(target), 1 / 2))
    # A classifier's stored targets are valid indices into its label table.
    Requires(Implies(is_clf, in_index_range(ToSeq(labels), ToSeq(target))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(labels), 1 / 2))
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The scored target has the same length as the stored target...
    Ensures(len(Result()) == len(target))
    # ...a classifier decodes each index back to the original class value it
    # addresses (labels[target[i]]); a non-classifier passes it through
    # unchanged. The decode is the SINGLE behaviour that distinguishes the two.
    Ensures(Implies(is_clf,
                    Forall(int, lambda i: (Implies(0 <= i and i < len(target),
                        ToSeq(Result())[i] == decode_one(ToSeq(labels),
                                                         ToSeq(target)[i])),
                        [[ToSeq(Result())[i]]]))))
    Ensures(Implies(not is_clf, ToSeq(Result()) == ToSeq(target)))
    # post-conditions-end
    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            result = result + [labels[target[i]]]
            # the append preserves every earlier element and sets index i
            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end


def secondary_score_target(use_secondary: bool, is_clf: bool,
                           labels: List[int],
                           target: List[int]) -> List[int]:
    """The optional held-out target, in the representation handed to the scorer
    when the held-out path is taken. The decode rule is identical to the
    primary site."""
    # pre-conditions-start
    Requires(use_secondary)
    Requires(Acc(list_pred(labels), 1 / 2))
    Requires(Acc(list_pred(target), 1 / 2))
    Requires(Implies(is_clf, in_index_range(ToSeq(labels), ToSeq(target))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(labels), 1 / 2))
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(target))
    Ensures(Implies(is_clf,
                    Forall(int, lambda i: (Implies(0 <= i and i < len(target),
                        ToSeq(Result())[i] == decode_one(ToSeq(labels),
                                                         ToSeq(target)[i])),
                        [[ToSeq(Result())[i]]]))))
    Ensures(Implies(not is_clf, ToSeq(Result()) == ToSeq(target)))
    # post-conditions-end
    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            result = result + [labels[target[i]]]
            # the append preserves every earlier element and sets index i
            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 8 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`), all REJECTED by the spec (exit 2, none verifies) => no CANDIDATE => no faithful patch to resolve-run (the mandatory resolve step fires only for a verifying candidate; none exists). Positive control (verbatim model.py) VERIFIES (exit 0, 23.4s). G-AX (axiom_check.py) PASSES (exit 0).

env python; SBU_BENCHMARK_DIR=benchmark-verified. Commands: `python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-14710 <atk>` (all exit 0/SAME); `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-14710 <atk>` (all exit 2 NOT-A-COUNTEREXAMPLE: does not verify); `bash scripts/nagini_verify.sh positive_control.py` (exit 0). Weakness runs launched concurrently in 3 batches of <=3 JVMs.

Attack roster (all same-spec, all rejected):
- atk_1: prepatch site#1 repro (bundle model_prepatch.py) — classifier forwards raw index target[i] undecoded. REJECTED (reproduces the real pre-patch str-vs-float bug).
- atk_6: prepatch site#2 repro (bundle model_prepatch_2.py) — held-out target undecoded. REJECTED.
- atk_2: partial-domain — classifier decodes all indices EXCEPT i==0 (raw), both sites. REJECTED (postcond forces Result[0]==decode_one).
- atk_3: boundary/off-by-one control-flow — decoded body but loop guard `i < len(target)-1` drops last element (length short). REJECTED (len(Result)==len(target) fails).
- atk_4: branch-swap / ungrounded-oracle echo — classifier forwards raw, regressor decodes. REJECTED (both branch postconds fail).
- atk_5: control-flow-effect — non-classifier ALSO decodes (should be identity passthrough). REJECTED (Implies(not is_clf, Result==target) fails).
- atk_7: constant/ungrounded index — classifier emits labels[target[0]] for every position. REJECTED (element-wise decode_one(...,target[i]) fails).
- atk_8: length-inflation boundary — appends decoded value twice (Result too long). REJECTED (len fails).

Why no verifying-wrong-impl can exist: both function postconditions PIN Result() completely. Classifier branch: len(Result())==len(target) AND Forall i. Result()[i]==decode_one(ToSeq(labels),ToSeq(target)[i]); non-classifier branch: ToSeq(Result())==ToSeq(target). Every behavioural deviation violates a pinned postcondition, so the spec is tight (verify => equal to gold behaviour on the tested inputs).

Refinement audit (refinement.md): every leg is R (bool/List[int] carriers, is_classifier/classes_/y abstraction, .astype(int) identity on integral codes), I (identical no-ops: `if is_clf` dispatch A4, regressor passthrough A6, use_secondary guard), or A-reference (A5/B-A5: deep decode_one gather). NO kind-3 leg, NO consumed axiom (axioms region empty by design). The sole changed op (index->label gather) is modeled DEEPLY (per-element decode_one + verified loop), not behind an ungrounded oracle. A-reference correspondence to the real callee HOLDS: G-AX runs the REAL sklearn LabelEncoder + REAL numpy fancy-index over 6 boundary + 20000 fuzz gathers + string/numeric round trips (incl. the issue's ['x']*50+['y']*50), confirming decode_one-assembly == classes_[idx] element-wise AND classes_[encoded]==y (round-trip identity => scored target shares predict's original representation). numpy/sklearn 1.26.4/1.3.0.

prepatch_reproduced=true (atk_1 and atk_6 are the bundle's own two prepatch variants; both fail to verify, reproducing the real pre-patch integer-target-to-scorer bug).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

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

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-14710.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an estimator monitors its own progress with a scorer, it must hand that
  scorer a target that lives in the SAME representation as the values the
  estimator's prediction routine produces. A classifying estimator stores its
  targets internally as integer indices `0 .. k-1` into a table `labels` of the
  distinct original class values, and its prediction routine emits the ORIGINAL
  class values (`labels[index]`). Therefore, before being scored, a classifier's
  internally-held target index `t` must be mapped back to the original value it
  addresses; element `i` of the target handed to the scorer equals
  `labels[target[i]]`. A non-classifying estimator holds and predicts targets in
  one and the same representation, so its target is handed to the scorer
  unchanged. The same rule applies to BOTH the always-present primary target and
  the optional secondary (held-out) target.

Targets and the label table are modelled as `List[int]` (Nagini bans rich
arrays); the index-into-table read is the element-wise gather `labels[target]`,
modelled DEEPLY (spelled out as the per-element `decode_one`); there is no
consumed axiom. The specification is carried over `PSeq[int]` via `ToSeq`.

Two structurally independent sites are specified (primary target, secondary
target); the per-function regions repeat, one set per site.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the only changed operation — the index-into-table
# decode — is modelled deeply by the per-element `decode_one` gather below and
# validated against the real callee by axiom_check.py / G-AX. There is no
# unchanged library callee whose contract the proof consumes.)
# axioms-end


# pure-start
@Pure
def in_index_range(labels: PSeq[int], t: PSeq[int]) -> bool:
    """Every internal target index addresses a real entry of the label table:
    `0 <= t[i] < len(labels)` for all `i`. This is the standing invariant of a
    label-encoded classification target."""
    return Forall(int, lambda i: (Implies(0 <= i and i < len(t),
                                          0 <= t[i] and t[i] < len(labels)),
                                  [[t[i]]]))


@Pure
def decode_one(labels: PSeq[int], x: int) -> int:
    """Decode a single internal index `x` to the original class value it
    addresses: `labels[x]` when `x` is a valid index. The out-of-range branch is
    never taken for a label-encoded target (see `in_index_range`); it only makes
    the gather total so it carries no precondition."""
    if 0 <= x and x < len(labels):
        return labels[x]
    return x
# pure-end


def primary_score_target(is_clf: bool, labels: List[int],
                         target: List[int]) -> List[int]:
    """The primary (always-scored) target, in the representation handed to the
    scorer."""
    # pre-conditions-start
    Requires(Acc(list_pred(labels), 1 / 2))
    Requires(Acc(list_pred(target), 1 / 2))
    # A classifier's stored targets are valid indices into its label table.
    Requires(Implies(is_clf, in_index_range(ToSeq(labels), ToSeq(target))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(labels), 1 / 2))
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The scored target has the same length as the stored target...
    Ensures(len(Result()) == len(target))
    # ...a classifier decodes each index back to the original class value it
    # addresses (labels[target[i]]); a non-classifier passes it through
    # unchanged. The decode is the SINGLE behaviour that distinguishes the two.
    Ensures(Implies(is_clf,
                    Forall(int, lambda i: (Implies(0 <= i and i < len(target),
                        ToSeq(Result())[i] == decode_one(ToSeq(labels),
                                                         ToSeq(target)[i])),
                        [[ToSeq(Result())[i]]]))))
    Ensures(Implies(not is_clf, ToSeq(Result()) == ToSeq(target)))
    # post-conditions-end
    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            result = result + [labels[target[i]]]
            # the append preserves every earlier element and sets index i
            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end


def secondary_score_target(use_secondary: bool, is_clf: bool,
                           labels: List[int],
                           target: List[int]) -> List[int]:
    """The optional held-out target, in the representation handed to the scorer
    when the held-out path is taken. The decode rule is identical to the
    primary site."""
    # pre-conditions-start
    Requires(use_secondary)
    Requires(Acc(list_pred(labels), 1 / 2))
    Requires(Acc(list_pred(target), 1 / 2))
    Requires(Implies(is_clf, in_index_range(ToSeq(labels), ToSeq(target))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(labels), 1 / 2))
    Ensures(Acc(list_pred(target), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(target))
    Ensures(Implies(is_clf,
                    Forall(int, lambda i: (Implies(0 <= i and i < len(target),
                        ToSeq(Result())[i] == decode_one(ToSeq(labels),
                                                         ToSeq(target)[i])),
                        [[ToSeq(Result())[i]]]))))
    Ensures(Implies(not is_clf, ToSeq(Result()) == ToSeq(target)))
    # post-conditions-end
    # impl-start
    if is_clf:
        result = []  # type: List[int]
        i = 0
        while i < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(target))
            Invariant(len(result) == i)
            Invariant(in_index_range(ToSeq(labels), ToSeq(target)))
            Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == decode_one(ToSeq(labels), ToSeq(target)[k])),
                [[ToSeq(result)[k]]])))
            # invariants-end
            # in_index_range, instantiated at i, gives 0 <= target[i] < len(labels)
            Assert(ToSeq(target)[i] == target[i])
            Assert(0 <= target[i] and target[i] < len(labels))
            old_seq = ToSeq(result)  # type: PSeq[int]
            result = result + [labels[target[i]]]
            # the append preserves every earlier element and sets index i
            Assert(ToSeq(result) == old_seq + PSeq(labels[target[i]]))
            Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
            Assert(ToSeq(result)[i] == decode_one(ToSeq(labels), ToSeq(target)[i]))
            i = i + 1
        return result
    else:
        out = []  # type: List[int]
        j = 0
        while j < len(target):
            # invariants-start
            Invariant(Acc(list_pred(labels), 1 / 2))
            Invariant(Acc(list_pred(target), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(target))
            Invariant(ToSeq(out) == ToSeq(target).take(j))
            # invariants-end
            out = out + [target[j]]
            Assert(ToSeq(target).take(j) + PSeq(target[j]) ==
                   ToSeq(target).take(j + 1))
            j = j + 1
        return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 8 same-spec attacks (all confirmed byte-identical spec via `adversary same-spec`), all REJECTED by the spec (exit 2, none verifies) => no CANDIDATE => no faithful patch to resolve-run (the mandatory resolve step fires only for a verifying candidate; none exists). Positive control (verbatim model.py) VERIFIES (exit 0, 23.4s). G-AX (axiom_check.py) PASSES (exit 0).

env python; SBU_BENCHMARK_DIR=benchmark-verified. Commands: `python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-14710 <atk>` (all exit 0/SAME); `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-14710 <atk>` (all exit 2 NOT-A-COUNTEREXAMPLE: does not verify); `bash scripts/nagini_verify.sh positive_control.py` (exit 0). Weakness runs launched concurrently in 3 batches of <=3 JVMs.

Attack roster (all same-spec, all rejected):
- atk_1: prepatch site#1 repro (bundle model_prepatch.py) — classifier forwards raw index target[i] undecoded. REJECTED (reproduces the real pre-patch str-vs-float bug).
- atk_6: prepatch site#2 repro (bundle model_prepatch_2.py) — held-out target undecoded. REJECTED.
- atk_2: partial-domain — classifier decodes all indices EXCEPT i==0 (raw), both sites. REJECTED (postcond forces Result[0]==decode_one).
- atk_3: boundary/off-by-one control-flow — decoded body but loop guard `i < len(target)-1` drops last element (length short). REJECTED (len(Result)==len(target) fails).
- atk_4: branch-swap / ungrounded-oracle echo — classifier forwards raw, regressor decodes. REJECTED (both branch postconds fail).
- atk_5: control-flow-effect — non-classifier ALSO decodes (should be identity passthrough). REJECTED (Implies(not is_clf, Result==target) fails).
- atk_7: constant/ungrounded index — classifier emits labels[target[0]] for every position. REJECTED (element-wise decode_one(...,target[i]) fails).
- atk_8: length-inflation boundary — appends decoded value twice (Result too long). REJECTED (len fails).

Why no verifying-wrong-impl can exist: both function postconditions PIN Result() completely. Classifier branch: len(Result())==len(target) AND Forall i. Result()[i]==decode_one(ToSeq(labels),ToSeq(target)[i]); non-classifier branch: ToSeq(Result())==ToSeq(target). Every behavioural deviation violates a pinned postcondition, so the spec is tight (verify => equal to gold behaviour on the tested inputs).

Refinement audit (refinement.md): every leg is R (bool/List[int] carriers, is_classifier/classes_/y abstraction, .astype(int) identity on integral codes), I (identical no-ops: `if is_clf` dispatch A4, regressor passthrough A6, use_secondary guard), or A-reference (A5/B-A5: deep decode_one gather). NO kind-3 leg, NO consumed axiom (axioms region empty by design). The sole changed op (index->label gather) is modeled DEEPLY (per-element decode_one + verified loop), not behind an ungrounded oracle. A-reference correspondence to the real callee HOLDS: G-AX runs the REAL sklearn LabelEncoder + REAL numpy fancy-index over 6 boundary + 20000 fuzz gathers + string/numeric round trips (incl. the issue's ['x']*50+['y']*50), confirming decode_one-assembly == classes_[idx] element-wise AND classes_[encoded]==y (round-trip identity => scored target shares predict's original representation). numpy/sklearn 1.26.4/1.3.0.

prepatch_reproduced=true (atk_1 and atk_6 are the bundle's own two prepatch variants; both fail to verify, reproducing the real pre-patch integer-target-to-scorer bug).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same-spec nagini exit 0 on an identity copy of the bundle model) and model.py verifies under the pinned Nagini verifier (exit 0, 18.44s), so the spec is real and load-bearing.

Modeled callee = BaseHistGradientBoosting._check_early_stopping_scorer, inspected in the gold-patched worktree gradient_boosting.py:429-440:
  if is_classifier(self): y_small_train = self.classes_[y_small_train.astype(int)]  (train site)
  if self._use_validation_data: if is_classifier(self): y_val = self.classes_[y_val.astype(int)]  (val site)

Mapping: is_clf<->is_classifier(self); labels:List[int]<->self.classes_; target:List[int]<->the LabelEncoder-encoded integer index target; Result()<->the y handed to self.scorer_. Two functions model the two structurally independent sites; secondary site guarded by Requires(use_secondary)<->_use_validation_data.

No divergence within the spec's stated preconditions:
(1) Classifier path: Result()[i]==decode_one(labels,target[i])==labels[target[i]] under in_index_range equals numpy fancy-index classes_[idx] element-wise exactly.
(2) Regressor path: model passthrough (out==target) == the real no-op (gold does not touch the target when not a classifier).
(3) .astype(int) is the identity on the integral LabelEncoder codes; the model's target:List[int] is inherently integral, so no truncation/rounding drift is observable in-domain. G-CONF (recorded) confirms shadow==real patched-repo scored targets over 178,548 site-inputs, int64/float64/float32 carriers + int and string class tables, 0 disagreements, seed 14710.
(4) The is_clf=>in_index_range precondition is a DOMAIN RESTRICTION that matches reality (LabelEncoder always yields codes 0..k-1; _encode_y gradient_boosting.py:1031-1033), NOT an over-strong postcondition; it excludes no real input on which the callee is invoked.
(5) decode_one's out-of-range branch is unreachable under in_index_range, so it never affects the postcondition.

The modeled function agrees with the real callee on every input satisfying the preconditions. No diverging input exists; the spec is faithful (not too strong / no drift).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (extracted via markers.spec_view over model.py: module docstring + axioms/pure/pre/post regions, impl elided to '...') discloses nothing about the gold edit beyond the PUBLIC problem_statement. The problem_statement itself is maximally disclosing: it states the diagnosis verbatim ('y_true being integer while y_pred are original classes ... We need to encode y_true each time we compute the score') AND includes a 'Potential resolution' diff carrying the essentially-verbatim gold fix (y_small_train = self.classes_[y_small_train.astype(int)] and the y_val counterpart at both sites). The spec view is strictly MORE abstract than that: behavior is stated as desired behavior over neutral carriers (labels, target, is_clf, primary_score_target/secondary_score_target) with no diff markers, no patched file path (gradient_boosting.py appears only in off-view mapping.md/refinement.md, not the spec view), and no spec-view identifier echoing a patched repo symbol (classes_, y_small_train, y_val, is_classifier, _check_early_stopping_scorer never appear in the spec view). Mechanical leakage.screen(src, nagini, patch, problem_statement) returns passed=True with zero hard_failures. No narration terms (bug/fix/patch/etc.) in the spec view. The two-site structure (primary/secondary target) mirrors the two gold hunks but that decomposition is already fully visible in the public 'Potential resolution' diff. Nothing in the spec view reconstructs the gold beyond what the problem_statement already gives.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
