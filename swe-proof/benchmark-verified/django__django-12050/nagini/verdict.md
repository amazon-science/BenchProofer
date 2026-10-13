# P2 adversarial audit — django__django-12050

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,13 +83,13 @@
                                            Result().items[k] == normalise_item(value.items[k])))))
     # post-conditions-end
     # impl-start
-    out = Iterable(value.kind)
+    out = Iterable(1)
     i = 0
     while i < len(value.items):
         # invariants-start
         Invariant(Acc(value.kind, 1 / 2))
         Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
-        Invariant(Acc(out.kind) and out.kind == value.kind)
+        Invariant(Acc(out.kind) and out.kind == 1)
         Invariant(Acc(out.items) and Acc(list_pred(out.items)))
         Invariant(0 <= i and i <= len(value.items))
         Invariant(len(out.items) == i)
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
     # impl-start
     out = Iterable(value.kind)
     i = 0
-    while i < len(value.items):
+    while i < len(value.items) - 1:
         # invariants-start
         Invariant(Acc(value.kind, 1 / 2))
         Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -85,18 +85,18 @@
     # impl-start
     out = Iterable(value.kind)
     i = 0
-    while i < len(value.items):
+    n = len(value.items)
+    while i < n:
         # invariants-start
         Invariant(Acc(value.kind, 1 / 2))
         Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
         Invariant(Acc(out.kind) and out.kind == value.kind)
         Invariant(Acc(out.items) and Acc(list_pred(out.items)))
+        Invariant(n == len(value.items))
         Invariant(0 <= i and i <= len(value.items))
         Invariant(len(out.items) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                 out.items[k] == normalise_item(value.items[k])))))
         # invariants-end
-        out.items.append(normalise_item(value.items[i]))
+        out.items.append(normalise_item(value.items[n - 1 - i]))
         i = i + 1
     return out
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,13 +83,13 @@
                                            Result().items[k] == normalise_item(value.items[k])))))
     # post-conditions-end
     # impl-start
-    out = Iterable(value.kind)
+    out = Iterable(0)
     i = 0
     while i < len(value.items):
         # invariants-start
         Invariant(Acc(value.kind, 1 / 2))
         Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
-        Invariant(Acc(out.kind) and out.kind == value.kind)
+        Invariant(Acc(out.kind) and out.kind == 0)
         Invariant(Acc(out.items) and Acc(list_pred(out.items)))
         Invariant(0 <= i and i <= len(value.items))
         Invariant(len(out.items) == i)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -84,19 +84,5 @@
     # post-conditions-end
     # impl-start
     out = Iterable(value.kind)
-    i = 0
-    while i < len(value.items):
-        # invariants-start
-        Invariant(Acc(value.kind, 1 / 2))
-        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
-        Invariant(Acc(out.kind) and out.kind == value.kind)
-        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
-        Invariant(0 <= i and i <= len(value.items))
-        Invariant(len(out.items) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                 out.items[k] == normalise_item(value.items[k])))))
-        # invariants-end
-        out.items.append(normalise_item(value.items[i]))
-        i = i + 1
     return out
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,9 +94,9 @@
         Invariant(0 <= i and i <= len(value.items))
         Invariant(len(out.items) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                 out.items[k] == normalise_item(value.items[k])))))
+                                                 out.items[k] == value.items[k]))))
         # invariants-end
-        out.items.append(normalise_item(value.items[i]))
+        out.items.append(value.items[i])
         i = i + 1
     return out
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -83,7 +83,10 @@
                                            Result().items[k] == normalise_item(value.items[k])))))
     # post-conditions-end
     # impl-start
-    out = Iterable(value.kind)
+    if value.kind == 0:
+        out = Iterable(0)
+    else:
+        out = Iterable(1)
     i = 0
     while i < len(value.items):
         # invariants-start
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,7 +96,10 @@
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  out.items[k] == normalise_item(value.items[k])))))
         # invariants-end
-        out.items.append(normalise_item(value.items[i]))
+        if value.kind == 1:
+            out.items.append(normalise_item(value.items[i]))
+        else:
+            out.items.append(value.items[i])
         i = i + 1
     return out
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -83,13 +83,13 @@
                                            Result().items[k] == normalise_item(value.items[k])))))
     # post-conditions-end
     # impl-start
-    out = Iterable(value.kind)
+    out = Iterable(1 - value.kind)
     i = 0
     while i < len(value.items):
         # invariants-start
         Invariant(Acc(value.kind, 1 / 2))
         Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
-        Invariant(Acc(out.kind) and out.kind == value.kind)
+        Invariant(Acc(out.kind) and out.kind == 1 - value.kind)
         Invariant(Acc(out.items) and Acc(list_pred(out.items)))
         Invariant(0 <= i and i <= len(value.items))
         Invariant(len(out.items) == i)
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -94,9 +94,9 @@
         Invariant(0 <= i and i <= len(value.items))
         Invariant(len(out.items) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-                                                 out.items[k] == normalise_item(value.items[k])))))
+                                                 out.items[k] == normalise_item(value.items[0])))))
         # invariants-end
-        out.items.append(normalise_item(value.items[i]))
+        out.items.append(normalise_item(value.items[0]))
         i = i + 1
     return out
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12050.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lookup right-hand side may be an *iterable* of items (an ordered list, or
  an ordered tuple). When such an iterable is normalised for use in a query,
  two things must hold of the normalised result:

    (1) each item is normalised independently and INDEPENDENT-of-position: the
        i-th item of the result is the per-item normalisation of the i-th input
        item, and the result has exactly as many items as the input; and

    (2) the result is an iterable of the SAME concrete iterable type as the
        input. An ordered list normalises to an ordered list; an ordered tuple
        normalises to an ordered tuple. The concrete container type is carried
        through unchanged, because downstream consumers whose behaviour depends
        on the exact iterable type (e.g. value-equality against a stored value)
        observe it.

The iterable is modelled as a minimal object exposing only the two touched
aspects: a `kind` tag distinguishing the two concrete iterable types (0 for an
ordered list, 1 for an ordered tuple) and `items: List[int]` carrying the
ordered item identities. `List[int]`/`PSeq` sequence reasoning carries the
per-item specification; an item is observed only through its normalised
identity.

The unchanged per-item normalisation primitive is axiomatized (`normalise_item`):
it maps one item identity to its normalised identity and is independent of the
surrounding container. Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def normalise_item(item: int) -> int:
    """The unchanged per-item normalisation primitive applied to one item of
    the iterable. It depends only on the item itself, not on the container that
    holds it, so normalising an item yields the same identity whether the item
    sits in a list or a tuple. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Ensures(True)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

class Iterable:
    def __init__(self, kind: int) -> None:
        Requires(kind == 0 or kind == 1)
        Ensures(Acc(self.kind) and self.kind == kind)  # type: ignore
        Ensures(Acc(self.items) and Acc(list_pred(self.items)))  # type: ignore
        Ensures(len(self.items) == 0)
        self.kind = kind  # type: int
        self.items = []  # type: List[int]

def resolve_iterable_value(value: Iterable) -> Iterable:
    # pre-conditions-start
    Requires(Acc(value.kind, 1 / 2))
    Requires(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
    Requires(value.kind == 0 or value.kind == 1)
    # pre-conditions-end
    # post-conditions-start
    # the input is read-only (returned at the same fractional permission) ...
    Ensures(Acc(value.kind, 1 / 2))
    Ensures(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
    # ... the result is a fresh, fully-owned iterable ...
    Ensures(Acc(Result().kind) and Acc(Result().items) and Acc(list_pred(Result().items)))
    # (2) of the SAME concrete iterable type as the input.
    Ensures(Result().kind == value.kind)
    # (1) with exactly as many items, each the per-item normalisation of the
    # corresponding input item, in order.
    Ensures(len(Result().items) == len(value.items))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value.items),
                                           Result().items[k] == normalise_item(value.items[k])))))
    # post-conditions-end
    # impl-start
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Attacked the A-legs (axioms / deep-model refs) and the model<->patch correspondence per plan §4; R/I legs left to G-CONF.

SPEC SHAPE: resolve_iterable_value postconditions fully pin the abstract output over the modeled domain: Result().kind==value.kind (the deep-modeled fix), len(Result().items)==len(value.items), and Forall k: Result().items[k]==normalise_item(value.items[k]) with normalise_item an uninterpreted @Pure/@ContractOnly axiom (Ensures(True)). No per-item behavioral divergence is even expressible; the only discriminating content (type preservation) is modeled deeply, not axiomatized.

10 ATTACKS (all built by editing only the impl region of model.py; command per attack: `python -m swebench_unified.adversary weakness nagini django__django-12050 <path>` run in background batches of <=3):
- atk_1 (prepatch bug, always tuple kind=1): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). PREPATCH REPRODUCED.
- atk_2 (off-by-one, drops last item): rejected (exit 2).
- atk_3 (reversed item order): rejected (exit 2).
- atk_4 (always list kind=0): rejected (exit 2).
- atk_5 (control-flow-effect, empty loop body / no items appended): rejected (exit 2).
- atk_6 (ungrounded-oracle echo, appends raw value.items[i] not normalise_item): rejected (exit 2).
- atk_7 (branch-on-kind explicit if kind==0 Iterable(0) else Iterable(1); behaviorally CORRECT echo): CANDIDATE-COUNTEREXAMPLE exit 0 (shares spec AND verifies, 16.7s); same-spec confirmed byte-identical (exit 0).
- atk_8 (partial-domain: normalise only for kind==1, raw passthrough for kind==0): rejected (exit 2).
- atk_9 (kind-swap, out kind = 1 - value.kind): rejected (exit 2).
- atk_10 (dup-first, appends normalise_item(value.items[0]) for every i): rejected (exit 2).

CANDIDATE atk_7 -> MATERIALIZED FAITHFUL REFINED PATCH and RAN THROUGH OFFICIAL HARNESS (not speculated). Patch = same-kind branch translation of the impl (list->list(...) / tuple->tuple(...) via self.resolve_lookup_value recursion). Generated via git diff inside the frozen image (base 072ce1ccddc4), git apply --check clean. NOTE: run_resolve() wrapper returned 'no report at ... report.json' three times (image absent on first run; then a plumbing/short-circuit artifact) — this is a HARNESS-PLUMBING error, NOT a non-resolve, and was NOT treated as a verdict.

I ran the harness DIRECTLY: `cd experiments && python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path preds_atk7.json --max_workers 1 --run_id atk7manual --namespace swebench --instance_image_tag latest --cache_level env ----report_dir experiments/reports --instance_ids django__django-12050` => Instances resolved: 1. report.json: resolved=true, FAIL_TO_PASS test_iterable_lookup_value SUCCESS, all 10 PASS_TO_PASS success. GOLD control run concurrently under identical config resolved=true (harness healthy). So the sole verifying candidate is a resolving echo of the gold -> NOT a weakness (per resolved-echo policy).

POSITIVE CONTROL: bundle model.py verifies (nagini_verify.sh exit 0).

REFINEMENT.MD LEG AUDIT (A-focus): A1=R (Iterable{kind,items} carrier binding), A2=R+I (the one CHANGED op type(value)(...) modeled DEEPLY via verified postcondition Result().kind==value.kind, NOT hidden behind an axiom), A3=A-consumed (normalise_item abstracts the UNCHANGED per-item resolution; A-reference correspondence to real Query.resolve_lookup_value validated by axiom_check.py part A container-independence + part B real Django), A4=I (return). §C 'no kind-3' assertion VERIFIED — the changed op is deep-modeled, not axiomatized; the only consumed axiom covers unchanged per-item behaviour. All legs R/A-consumed/A-reference/I; A-leg correspondence holds. (axiom_check.py part B needs the Django module which is absent from the lean env — that runs under the Docker G-AX lane, out of scope for G-EQ; its logic is sound by inspection.)

CONCLUSION: >=5 distinct wrong impls run, all rejected by the spec; the single verifying candidate's materialized faithful patch RESOLVES under the official harness (executed, not speculated). verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12050.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lookup right-hand side may be an *iterable* of items (an ordered list, or
  an ordered tuple). When such an iterable is normalised for use in a query,
  two things must hold of the normalised result:

    (1) each item is normalised independently and INDEPENDENT-of-position: the
        i-th item of the result is the per-item normalisation of the i-th input
        item, and the result has exactly as many items as the input; and

    (2) the result is an iterable of the SAME concrete iterable type as the
        input. An ordered list normalises to an ordered list; an ordered tuple
        normalises to an ordered tuple. The concrete container type is carried
        through unchanged, because downstream consumers whose behaviour depends
        on the exact iterable type (e.g. value-equality against a stored value)
        observe it.

The iterable is modelled as a minimal object exposing only the two touched
aspects: a `kind` tag distinguishing the two concrete iterable types (0 for an
ordered list, 1 for an ordered tuple) and `items: List[int]` carrying the
ordered item identities. `List[int]`/`PSeq` sequence reasoning carries the
per-item specification; an item is observed only through its normalised
identity.

The unchanged per-item normalisation primitive is axiomatized (`normalise_item`):
it maps one item identity to its normalised identity and is independent of the
surrounding container. Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def normalise_item(item: int) -> int:
    """The unchanged per-item normalisation primitive applied to one item of
    the iterable. It depends only on the item itself, not on the container that
    holds it, so normalising an item yields the same identity whether the item
    sits in a list or a tuple. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Ensures(True)
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

class Iterable:
    def __init__(self, kind: int) -> None:
        Requires(kind == 0 or kind == 1)
        Ensures(Acc(self.kind) and self.kind == kind)  # type: ignore
        Ensures(Acc(self.items) and Acc(list_pred(self.items)))  # type: ignore
        Ensures(len(self.items) == 0)
        self.kind = kind  # type: int
        self.items = []  # type: List[int]

def resolve_iterable_value(value: Iterable) -> Iterable:
    # pre-conditions-start
    Requires(Acc(value.kind, 1 / 2))
    Requires(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
    Requires(value.kind == 0 or value.kind == 1)
    # pre-conditions-end
    # post-conditions-start
    # the input is read-only (returned at the same fractional permission) ...
    Ensures(Acc(value.kind, 1 / 2))
    Ensures(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
    # ... the result is a fresh, fully-owned iterable ...
    Ensures(Acc(Result().kind) and Acc(Result().items) and Acc(list_pred(Result().items)))
    # (2) of the SAME concrete iterable type as the input.
    Ensures(Result().kind == value.kind)
    # (1) with exactly as many items, each the per-item normalisation of the
    # corresponding input item, in order.
    Ensures(len(Result().items) == len(value.items))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(value.items),
                                           Result().items[k] == normalise_item(value.items[k])))))
    # post-conditions-end
    # impl-start
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        # invariants-start
        Invariant(Acc(value.kind, 1 / 2))
        Invariant(Acc(value.items, 1 / 2) and Acc(list_pred(value.items), 1 / 2))
        Invariant(Acc(out.kind) and out.kind == value.kind)
        Invariant(Acc(out.items) and Acc(list_pred(out.items)))
        Invariant(0 <= i and i <= len(value.items))
        Invariant(len(out.items) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 out.items[k] == normalise_item(value.items[k])))))
        # invariants-end
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Attacked the A-legs (axioms / deep-model refs) and the model<->patch correspondence per plan §4; R/I legs left to G-CONF.

SPEC SHAPE: resolve_iterable_value postconditions fully pin the abstract output over the modeled domain: Result().kind==value.kind (the deep-modeled fix), len(Result().items)==len(value.items), and Forall k: Result().items[k]==normalise_item(value.items[k]) with normalise_item an uninterpreted @Pure/@ContractOnly axiom (Ensures(True)). No per-item behavioral divergence is even expressible; the only discriminating content (type preservation) is modeled deeply, not axiomatized.

10 ATTACKS (all built by editing only the impl region of model.py; command per attack: `python -m swebench_unified.adversary weakness nagini django__django-12050 <path>` run in background batches of <=3):
- atk_1 (prepatch bug, always tuple kind=1): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). PREPATCH REPRODUCED.
- atk_2 (off-by-one, drops last item): rejected (exit 2).
- atk_3 (reversed item order): rejected (exit 2).
- atk_4 (always list kind=0): rejected (exit 2).
- atk_5 (control-flow-effect, empty loop body / no items appended): rejected (exit 2).
- atk_6 (ungrounded-oracle echo, appends raw value.items[i] not normalise_item): rejected (exit 2).
- atk_7 (branch-on-kind explicit if kind==0 Iterable(0) else Iterable(1); behaviorally CORRECT echo): CANDIDATE-COUNTEREXAMPLE exit 0 (shares spec AND verifies, 16.7s); same-spec confirmed byte-identical (exit 0).
- atk_8 (partial-domain: normalise only for kind==1, raw passthrough for kind==0): rejected (exit 2).
- atk_9 (kind-swap, out kind = 1 - value.kind): rejected (exit 2).
- atk_10 (dup-first, appends normalise_item(value.items[0]) for every i): rejected (exit 2).

CANDIDATE atk_7 -> MATERIALIZED FAITHFUL REFINED PATCH and RAN THROUGH OFFICIAL HARNESS (not speculated). Patch = same-kind branch translation of the impl (list->list(...) / tuple->tuple(...) via self.resolve_lookup_value recursion). Generated via git diff inside the frozen image (base 072ce1ccddc4), git apply --check clean. NOTE: run_resolve() wrapper returned 'no report at ... report.json' three times (image absent on first run; then a plumbing/short-circuit artifact) — this is a HARNESS-PLUMBING error, NOT a non-resolve, and was NOT treated as a verdict.

I ran the harness DIRECTLY: `cd experiments && python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path preds_atk7.json --max_workers 1 --run_id atk7manual --namespace swebench --instance_image_tag latest --cache_level env ----report_dir experiments/reports --instance_ids django__django-12050` => Instances resolved: 1. report.json: resolved=true, FAIL_TO_PASS test_iterable_lookup_value SUCCESS, all 10 PASS_TO_PASS success. GOLD control run concurrently under identical config resolved=true (harness healthy). So the sole verifying candidate is a resolving echo of the gold -> NOT a weakness (per resolved-echo policy).

POSITIVE CONTROL: bundle model.py verifies (nagini_verify.sh exit 0).

REFINEMENT.MD LEG AUDIT (A-focus): A1=R (Iterable{kind,items} carrier binding), A2=R+I (the one CHANGED op type(value)(...) modeled DEEPLY via verified postcondition Result().kind==value.kind, NOT hidden behind an axiom), A3=A-consumed (normalise_item abstracts the UNCHANGED per-item resolution; A-reference correspondence to real Query.resolve_lookup_value validated by axiom_check.py part A container-independence + part B real Django), A4=I (return). §C 'no kind-3' assertion VERIFIED — the changed op is deep-modeled, not axiomatized; the only consumed axiom covers unchanged per-item behaviour. All legs R/A-consumed/A-reference/I; A-leg correspondence holds. (axiom_check.py part B needs the Django module which is absent from the lean env — that runs under the Docker G-AX lane, out of scope for G-EQ; its logic is sound by inspection.)

CONCLUSION: >=5 distinct wrong impls run, all rejected by the spec; the single verifying candidate's materialized faithful patch RESOLVES under the official harness (executed, not speculated). verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Model verifies (nagini_verify.sh exit 0, 11.5s); spec region byte-identical (same-spec exit 0). Modeled domain: value.kind∈{0,1} strict bijection kind==0⇔list, kind==1⇔tuple; items:List[int] opaque identities resolved by the UNINTERPRETED axiom normalise_item (Ensures(True)). Postconditions: Result().kind==value.kind, len(Result().items)==len(value.items), Result().items[k]==normalise_item(value.items[k]) in order. These faithfully mirror the real gold callee Query.resolve_lookup_value list/tuple branch: return type(value)(self.resolve_lookup_value(sub) for sub in value) — type-preserving (list->list, tuple->tuple), length-preserving, item i = per-item resolution of input i, in order.

Why not too strong: (a) items are opaque under an uninterpreted axiom, so NO per-item behavioral over-claim is even expressible; the only discriminating content is type-preservation, modeled deeply. (b) G-CONF re-ran 100,019 inputs (seed 12050) contract-stripped against the REAL per-item resolution with 0 disagreements. (c) G-AX validated container-independence over 7 boundary + 20000 fuzz sequences and drove the real Django callee (list->list, tuple->tuple).

Only boundary edge examined: tuple-subclass/namedtuple, where the real isinstance(value,(list,tuple)) guard admits subclasses and gold's type(value)(generator) raises TypeError while the model reports success. This is genuinely OUTSIDE the modeled domain — kind is a single bit distinguishing EXACTLY list vs tuple with no carrier for a subclass; SWE-bench F2P/tests only exercise plain lists/tuples. Un-representable input, not a within-domain disagreement, so it does not break verify(model)=>resolved. No diverging input exists within the spec's modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view computed via markers.spec_view(model.py, nagini): the impl region is ELIDED ('...  # implementation elided — supplied by the consumer'); only the docstring, axiom stub `normalise_item` (Ensures(True)), the `Iterable` carrier, and the pre/postconditions of `resolve_iterable_value` are visible. Mechanical G-LEAK screen (leakage.screen) PASSES clean (no diff markers, no gold-patch line reproduced, no patched file/module path, no bug/fix narration, no spec-view identifier embedding a patched symbol).

Gold-edit discriminator = 'preserve the input's concrete iterable type instead of coercing list→tuple', carried in the spec by postcondition `Result().kind == value.kind`. This is NOT a leak beyond problem_statement, because the PUBLIC problem_statement already states it verbatim: 'Query.resolve_lookup_value coerces value of type list to tuple breaking exact value queries... The expected iterable return type should match input iterable type.' The docstring's 'SAME concrete iterable type as the input' / 'ordered list normalises to an ordered list; an ordered tuple normalises to an ordered tuple' and the 'value-equality against a stored value (e.g. PickledField)' aside merely restate the public requirement (the problem statement explicitly names PickledField and matching input types).

Patched repo symbol `resolve_lookup_value` (the only distinctive changed symbol) itself appears in problem_statement, so it is public; the model renames the function `resolve_iterable_value`, which does not embed the patched symbol. Per-item resolution logic (the F/resolve_expression branch removed by the patch) is abstracted behind the opaque axiom `normalise_item(Ensures(True))` and is NOT revealed. No gold-specific construction detail (`type(value)(...)`, `tuple(resolved_values)`) appears in the spec view — those live only in refinement.md/mapping.md, which are audit artifacts, not the consumer spec view. Conclusion: the spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.