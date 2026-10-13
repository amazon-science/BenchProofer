# P2 adversarial audit — scikit-learn__scikit-learn-13142

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2_transient_return.py`, `atk_3_strict_gt_tie.py`, `atk_4_offbyone.py`, `atk_5_first_config.py`, `atk_6_wrong_label_source.py`, `atk_7_skip_persist.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -96,12 +96,7 @@
     # post-conditions-end
     # impl-start
     n = len(run_config)
-    # The transient configuration the object holds after the final trial is the
-    # final trial's configuration (may differ from the selected one).
     inst.config = run_config[n - 1]
-    # Select the highest-scoring (earliest-on-tie) configuration over all trials
-    # by scanning the trials from last to first; the running selection equals
-    # best_config / best_score over the already-scanned suffix.
     selected = run_config[n - 1]  # type: int
     selected_score = run_score[n - 1]  # type: int
     i = n
@@ -125,9 +120,7 @@
             selected = run_config[i - 2]
             selected_score = s
         i = i - 1
-    # Persist the selected configuration, THEN derive the labels from the
-    # persisted (retained) configuration.
     inst.config = selected
-    labels = labels_of(inst.config)
+    labels = labels_of(selected)
     return labels
     # impl-end
```

Attack 2 — `atk_2_transient_return.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,7 @@
     # post-conditions-end
     # impl-start
     n = len(run_config)
-    # The transient configuration the object holds after the final trial is the
-    # final trial's configuration (may differ from the selected one).
     inst.config = run_config[n - 1]
-    # Select the highest-scoring (earliest-on-tie) configuration over all trials
-    # by scanning the trials from last to first; the running selection equals
-    # best_config / best_score over the already-scanned suffix.
     selected = run_config[n - 1]  # type: int
     selected_score = run_score[n - 1]  # type: int
     i = n
@@ -125,9 +120,7 @@
             selected = run_config[i - 2]
             selected_score = s
         i = i - 1
-    # Persist the selected configuration, THEN derive the labels from the
-    # persisted (retained) configuration.
+    labels = labels_of(inst.config)
     inst.config = selected
-    labels = labels_of(inst.config)
     return labels
     # impl-end
```

Attack 3 — `atk_3_strict_gt_tie.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,7 @@
     # post-conditions-end
     # impl-start
     n = len(run_config)
-    # The transient configuration the object holds after the final trial is the
-    # final trial's configuration (may differ from the selected one).
     inst.config = run_config[n - 1]
-    # Select the highest-scoring (earliest-on-tie) configuration over all trials
-    # by scanning the trials from last to first; the running selection equals
-    # best_config / best_score over the already-scanned suffix.
     selected = run_config[n - 1]  # type: int
     selected_score = run_score[n - 1]  # type: int
     i = n
@@ -121,12 +116,10 @@
         Assert(ToSeq(run_score).drop(i - 2).drop(1) == ToSeq(run_score).drop(i - 1))
         Assert(ToSeq(run_config).drop(i - 2).drop(1) == ToSeq(run_config).drop(i - 1))
         s = run_score[i - 2]
-        if s >= selected_score:
+        if s > selected_score:
             selected = run_config[i - 2]
             selected_score = s
         i = i - 1
-    # Persist the selected configuration, THEN derive the labels from the
-    # persisted (retained) configuration.
     inst.config = selected
     labels = labels_of(inst.config)
     return labels
```

Attack 4 — `atk_4_offbyone.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,16 +96,11 @@
     # post-conditions-end
     # impl-start
     n = len(run_config)
-    # The transient configuration the object holds after the final trial is the
-    # final trial's configuration (may differ from the selected one).
     inst.config = run_config[n - 1]
-    # Select the highest-scoring (earliest-on-tie) configuration over all trials
-    # by scanning the trials from last to first; the running selection equals
-    # best_config / best_score over the already-scanned suffix.
     selected = run_config[n - 1]  # type: int
     selected_score = run_score[n - 1]  # type: int
     i = n
-    while i > 1:
+    while i > 0:
         # invariants-start
         Invariant(Acc(inst.config))
         Invariant(Acc(list_pred(run_config), 1 / 2))
@@ -125,8 +120,6 @@
             selected = run_config[i - 2]
             selected_score = s
         i = i - 1
-    # Persist the selected configuration, THEN derive the labels from the
-    # persisted (retained) configuration.
     inst.config = selected
     labels = labels_of(inst.config)
     return labels
```

Attack 5 — `atk_5_first_config.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,38 +96,7 @@
     # post-conditions-end
     # impl-start
     n = len(run_config)
-    # The transient configuration the object holds after the final trial is the
-    # final trial's configuration (may differ from the selected one).
-    inst.config = run_config[n - 1]
-    # Select the highest-scoring (earliest-on-tie) configuration over all trials
-    # by scanning the trials from last to first; the running selection equals
-    # best_config / best_score over the already-scanned suffix.
-    selected = run_config[n - 1]  # type: int
-    selected_score = run_score[n - 1]  # type: int
-    i = n
-    while i > 1:
-        # invariants-start
-        Invariant(Acc(inst.config))
-        Invariant(Acc(list_pred(run_config), 1 / 2))
-        Invariant(Acc(list_pred(run_score), 1 / 2))
-        Invariant(len(run_config) == n and len(run_score) == n)
-        Invariant(1 <= i and i <= n)
-        Invariant(selected_score == best_score(ToSeq(run_score).drop(i - 1)))
-        Invariant(selected == best_config(ToSeq(run_config).drop(i - 1),
-                                          ToSeq(run_score).drop(i - 1)))
-        # invariants-end
-        Assert(ToSeq(run_score).drop(i - 2)[0] == run_score[i - 2])
-        Assert(ToSeq(run_config).drop(i - 2)[0] == run_config[i - 2])
-        Assert(ToSeq(run_score).drop(i - 2).drop(1) == ToSeq(run_score).drop(i - 1))
-        Assert(ToSeq(run_config).drop(i - 2).drop(1) == ToSeq(run_config).drop(i - 1))
-        s = run_score[i - 2]
-        if s >= selected_score:
-            selected = run_config[i - 2]
-            selected_score = s
-        i = i - 1
-    # Persist the selected configuration, THEN derive the labels from the
-    # persisted (retained) configuration.
-    inst.config = selected
+    inst.config = run_config[0]
     labels = labels_of(inst.config)
     return labels
     # impl-end
```

Attack 6 — `atk_6_wrong_label_source.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,7 @@
     # post-conditions-end
     # impl-start
     n = len(run_config)
-    # The transient configuration the object holds after the final trial is the
-    # final trial's configuration (may differ from the selected one).
     inst.config = run_config[n - 1]
-    # Select the highest-scoring (earliest-on-tie) configuration over all trials
-    # by scanning the trials from last to first; the running selection equals
-    # best_config / best_score over the already-scanned suffix.
     selected = run_config[n - 1]  # type: int
     selected_score = run_score[n - 1]  # type: int
     i = n
@@ -125,9 +120,7 @@
             selected = run_config[i - 2]
             selected_score = s
         i = i - 1
-    # Persist the selected configuration, THEN derive the labels from the
-    # persisted (retained) configuration.
     inst.config = selected
-    labels = labels_of(inst.config)
+    labels = labels_of(run_config[0])
     return labels
     # impl-end
```

Attack 7 — `atk_7_skip_persist.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,7 @@
     # post-conditions-end
     # impl-start
     n = len(run_config)
-    # The transient configuration the object holds after the final trial is the
-    # final trial's configuration (may differ from the selected one).
     inst.config = run_config[n - 1]
-    # Select the highest-scoring (earliest-on-tie) configuration over all trials
-    # by scanning the trials from last to first; the running selection equals
-    # best_config / best_score over the already-scanned suffix.
     selected = run_config[n - 1]  # type: int
     selected_score = run_score[n - 1]  # type: int
     i = n
@@ -125,9 +120,6 @@
             selected = run_config[i - 2]
             selected_score = s
         i = i - 1
-    # Persist the selected configuration, THEN derive the labels from the
-    # persisted (retained) configuration.
-    inst.config = selected
-    labels = labels_of(inst.config)
+    labels = labels_of(selected)
     return labels
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-13142.

Behaviour under specification (a self-standing behavioural contract):

  A labelling routine runs over several independent trials. Each trial yields a
  parameter configuration together with a score; the routine selects, across
  the trials, the configuration whose score is largest (the earliest such
  configuration when several tie for the largest score), and that selected
  configuration is the configuration the object holds when the routine returns.

  The labels the routine returns are the deterministic label assignment of the
  configuration the object holds on return — i.e. exactly the labels a
  subsequent labelling query against that same object would itself produce. So
  the labels obtained while fitting agree with the labels obtained by querying
  the fitted object, for every number of trials.

A parameter configuration is modelled by an integer identifier; a trial's score
is modelled by an integer (the selection depends only on the order of the
scores, not their magnitudes). The deterministic assignment of labels from a
configuration — the unchanged query primitive — is axiomatized as a pure
function of the configuration identifier (`labels_of`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

class Estimator:
    def __init__(self, config: int) -> None:
        Ensures(Acc(self.config) and self.config == config)  # type: ignore
        self.config = config

# axioms-start
@Pure
@ContractOnly
def labels_of(config: int) -> int:
    """Deterministic label assignment derived from a parameter configuration
    (the unchanged query primitive). It is a pure function of the configuration
    identifier alone: the same configuration always yields the same labels, so
    two evaluations against equal configurations agree. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
# axioms-end

# pure-start
@Pure
def best_score(score: PSeq[int]) -> int:
    """The largest score among a non-empty run of trials."""
    Requires(len(score) >= 1)
    if len(score) == 1:
        return score[0]
    rest = best_score(score.drop(1))
    if score[0] >= rest:
        return score[0]
    return rest

@Pure
def best_config(config: PSeq[int], score: PSeq[int]) -> int:
    """The configuration of the highest-scoring trial; on ties the earliest
    such trial wins. Front-recursive so a single unfold is available per step."""
    Requires(len(config) == len(score))
    Requires(len(score) >= 1)
    if len(score) == 1:
        return config[0]
    if score[0] >= best_score(score.drop(1)):
        return config[0]
    return best_config(config.drop(1), score.drop(1))
# pure-end

def fit_and_label(inst: Estimator, run_config: List[int],
                  run_score: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(inst.config))
    Requires(Acc(list_pred(run_config), 1 / 2))
    Requires(Acc(list_pred(run_score), 1 / 2))
    Requires(len(run_config) == len(run_score))
    Requires(len(run_config) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(inst.config))
    Ensures(Acc(list_pred(run_config), 1 / 2))
    Ensures(Acc(list_pred(run_score), 1 / 2))
    Ensures(len(run_config) == len(run_score) and len(run_config) >= 1)
    # On return the object holds the selected (highest-scoring,
    # earliest-on-tie) configuration.
    Ensures(inst.config == best_config(ToSeq(run_config), ToSeq(run_score)))
    # The returned labels are the deterministic label assignment of the
    # configuration the object holds on return, so a subsequent labelling query
    # against that object agrees with the labels returned here.
    Ensures(Result() == labels_of(inst.config))
    # post-conditions-end
    # impl-start
    n = len(run_config)
    # The transient configuration the object holds after the final trial is the
    # final trial's configuration (may differ from the selected one).
    inst.config = run_config[n - 1]
    # Select the highest-scoring (earliest-on-tie) configuration over all trials
    # by scanning the trials from last to first; the running selection equals
    # best_config / best_score over the already-scanned suffix.
    selected = run_config[n - 1]  # type: int
    selected_score = run_score[n - 1]  # type: int
    i = n
    while i > 1:
        # invariants-start
        Invariant(Acc(inst.config))
        Invariant(Acc(list_pred(run_config), 1 / 2))
        Invariant(Acc(list_pred(run_score), 1 / 2))
        Invariant(len(run_config) == n and len(run_score) == n)
        Invariant(1 <= i and i <= n)
        Invariant(selected_score == best_score(ToSeq(run_score).drop(i - 1)))
        Invariant(selected == best_config(ToSeq(run_config).drop(i - 1),
                                          ToSeq(run_score).drop(i - 1)))
        # invariants-end
        Assert(ToSeq(run_score).drop(i - 2)[0] == run_score[i - 2])
        Assert(ToSeq(run_config).drop(i - 2)[0] == run_config[i - 2])
        Assert(ToSeq(run_score).drop(i - 2).drop(1) == ToSeq(run_score).drop(i - 1))
        Assert(ToSeq(run_config).drop(i - 2).drop(1) == ToSeq(run_config).drop(i - 1))
        s = run_score[i - 2]
        if s >= selected_score:
            selected = run_config[i - 2]
            selected_score = s
        i = i - 1
    # Persist the selected configuration, THEN derive the labels from the
    # persisted (retained) configuration.
    inst.config = selected
    labels = labels_of(inst.config)
    return labels
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fit_and_label pins BOTH abstract outputs — Ensures(inst.config == best_config(ToSeq(run_config),ToSeq(run_score))) and Ensures(Result() == labels_of(inst.config)). The single consumed axiom labels_of is @Pure @ContractOnly of config alone (purity only, no value claim); best_config/best_score are a verified deep model (A-reference), not an axiom over the changed function. The gold change is a pure statement REORDER (persist-then-derive), modeled directly as impl statement order A5-before-A6.

BASELINE (same-spec exit 0 for all 9): positive_control.py VERIFIES (weakness exit 0); prepatch.py FAILS verification (weakness exit 2) precisely on Result()==labels_of(inst.config) — prepatch bug reproduced.

ATTACKS (all same-spec exit 0; cmd: `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-13142 <path>`): atk_1_echo (persist selected, return labels_of(selected)==labels_of(inst.config)) -> weakness exit 0 CANDIDATE. Behaviorally IDENTICAL to gold. MANDATORY resolve run executed on its faithful (=gold) patch via run_resolve: COMPLETED=True RESOLVED=True ATTEMPTS=1 FLAKY=False note='resolved'. Legitimate echo -> NOT a weakness. atk_2_transient_return (return labels_of(final-trial), then persist = prepatch bug re-encoded) -> weakness exit 2; direct verify fails 'Postcondition ... Result()==labels_of(inst.config) might not hold' (line 95).

REJECTED (good). atk_3_strict_gt_tie (backward scan uses strict '>' => keeps LATEST max on ties, != earliest-max best_config) -> weakness exit 2; verify fails loop invariant 'selected == best_config(...)'. REJECTED (good) — spec pins earliest-max selection. atk_4_offbyone (loop guard i>0, over-scan boundary) -> weakness exit 2. REJECTED. atk_5_first_config (partial-domain: always select run_config[0]) -> weakness exit 2. REJECTED. atk_6_wrong_label_source (persist correct best but return labels_of(run_config[0]) — ungrounded-oracle echo variant) -> weakness exit 2. REJECTED. atk_7_skip_persist (leave inst.config=final trial, return labels_of(selected)) -> weakness exit 2; verify fails 'inst.config == best_config(...) might not hold' (line 91). REJECTED (good) — spec pins persisted config.

Only the behaviorally-equivalent echo verified, and its materialized faithful patch (the gold patch verbatim) RESOLVES under the official harness. No verifying same-spec wrong impl exists. Every genuinely-wrong impl (partial-domain, boundary, control-flow/tie, ungrounded-oracle, transient-config, skip-persist) is rejected on a load-bearing functional postcondition/invariant.

REFINEMENT.MD A-LEG AUDIT: legs are R / A-consumed / A-reference / I — no kind-3. A4 (A-reference best_config/best_score): model '>=' front-recursion = earliest-max; real loop base.py:255-258 strict '>' forward-scan = earliest-max; agree; G-AX (axiom_check.py) checks retained params==best trial & order observable; atk_3 confirms spec enforces this. A6 (A-consumed labels_of): purity-only abstraction of the unchanged e-step/argmax query primitive; G-AX checks determinism + config-functionality + e-step==predict; atk_2/atk_6 confirm the spec binds Result to labels_of of the held config. A1-A3/A5 (R/I) covered mechanically by recorded G-CONF (100176 checks, 0 disagreements) and G-MUT (20/20). The one genuinely changed op (query ordering) is modeled directly as impl statement order (the exact thing the prepatch reverses). Correspondence holds.

VERDICT: SOUND — >=5 distinct wrong impls run, none breaks verify=>correct; the sole verifying candidate's faithful patch resolves.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2_transient_return.py`, `atk_3_strict_gt_tie.py`, `atk_4_offbyone.py`, `atk_5_first_config.py`, `atk_6_wrong_label_source.py`, `atk_7_skip_persist.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2_transient_return.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_strict_gt_tie.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_offbyone.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_first_config.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_wrong_label_source.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_skip_persist.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-13142.

Behaviour under specification (a self-standing behavioural contract):

  A labelling routine runs over several independent trials. Each trial yields a
  parameter configuration together with a score; the routine selects, across
  the trials, the configuration whose score is largest (the earliest such
  configuration when several tie for the largest score), and that selected
  configuration is the configuration the object holds when the routine returns.

  The labels the routine returns are the deterministic label assignment of the
  configuration the object holds on return — i.e. exactly the labels a
  subsequent labelling query against that same object would itself produce. So
  the labels obtained while fitting agree with the labels obtained by querying
  the fitted object, for every number of trials.

A parameter configuration is modelled by an integer identifier; a trial's score
is modelled by an integer (the selection depends only on the order of the
scores, not their magnitudes). The deterministic assignment of labels from a
configuration — the unchanged query primitive — is axiomatized as a pure
function of the configuration identifier (`labels_of`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

class Estimator:
    def __init__(self, config: int) -> None:
        Ensures(Acc(self.config) and self.config == config)  # type: ignore
        self.config = config

# axioms-start
@Pure
@ContractOnly
def labels_of(config: int) -> int:
    """Deterministic label assignment derived from a parameter configuration
    (the unchanged query primitive). It is a pure function of the configuration
    identifier alone: the same configuration always yields the same labels, so
    two evaluations against equal configurations agree. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
# axioms-end

# pure-start
@Pure
def best_score(score: PSeq[int]) -> int:
    """The largest score among a non-empty run of trials."""
    Requires(len(score) >= 1)
    if len(score) == 1:
        return score[0]
    rest = best_score(score.drop(1))
    if score[0] >= rest:
        return score[0]
    return rest

@Pure
def best_config(config: PSeq[int], score: PSeq[int]) -> int:
    """The configuration of the highest-scoring trial; on ties the earliest
    such trial wins. Front-recursive so a single unfold is available per step."""
    Requires(len(config) == len(score))
    Requires(len(score) >= 1)
    if len(score) == 1:
        return config[0]
    if score[0] >= best_score(score.drop(1)):
        return config[0]
    return best_config(config.drop(1), score.drop(1))
# pure-end

def fit_and_label(inst: Estimator, run_config: List[int],
                  run_score: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(inst.config))
    Requires(Acc(list_pred(run_config), 1 / 2))
    Requires(Acc(list_pred(run_score), 1 / 2))
    Requires(len(run_config) == len(run_score))
    Requires(len(run_config) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(inst.config))
    Ensures(Acc(list_pred(run_config), 1 / 2))
    Ensures(Acc(list_pred(run_score), 1 / 2))
    Ensures(len(run_config) == len(run_score) and len(run_config) >= 1)
    # On return the object holds the selected (highest-scoring,
    # earliest-on-tie) configuration.
    Ensures(inst.config == best_config(ToSeq(run_config), ToSeq(run_score)))
    # The returned labels are the deterministic label assignment of the
    # configuration the object holds on return, so a subsequent labelling query
    # against that object agrees with the labels returned here.
    Ensures(Result() == labels_of(inst.config))
    # post-conditions-end
    # impl-start
    n = len(run_config)
    # The transient configuration the object holds after the final trial is the
    # final trial's configuration (may differ from the selected one).
    inst.config = run_config[n - 1]
    # Select the highest-scoring (earliest-on-tie) configuration over all trials
    # by scanning the trials from last to first; the running selection equals
    # best_config / best_score over the already-scanned suffix.
    selected = run_config[n - 1]  # type: int
    selected_score = run_score[n - 1]  # type: int
    i = n
    while i > 1:
        # invariants-start
        Invariant(Acc(inst.config))
        Invariant(Acc(list_pred(run_config), 1 / 2))
        Invariant(Acc(list_pred(run_score), 1 / 2))
        Invariant(len(run_config) == n and len(run_score) == n)
        Invariant(1 <= i and i <= n)
        Invariant(selected_score == best_score(ToSeq(run_score).drop(i - 1)))
        Invariant(selected == best_config(ToSeq(run_config).drop(i - 1),
                                          ToSeq(run_score).drop(i - 1)))
        # invariants-end
        Assert(ToSeq(run_score).drop(i - 2)[0] == run_score[i - 2])
        Assert(ToSeq(run_config).drop(i - 2)[0] == run_config[i - 2])
        Assert(ToSeq(run_score).drop(i - 2).drop(1) == ToSeq(run_score).drop(i - 1))
        Assert(ToSeq(run_config).drop(i - 2).drop(1) == ToSeq(run_config).drop(i - 1))
        s = run_score[i - 2]
        if s >= selected_score:
            selected = run_config[i - 2]
            selected_score = s
        i = i - 1
    # Persist the selected configuration, THEN derive the labels from the
    # persisted (retained) configuration.
    inst.config = selected
    labels = labels_of(inst.config)
    return labels
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fit_and_label pins BOTH abstract outputs — Ensures(inst.config == best_config(ToSeq(run_config),ToSeq(run_score))) and Ensures(Result() == labels_of(inst.config)). The single consumed axiom labels_of is @Pure @ContractOnly of config alone (purity only, no value claim); best_config/best_score are a verified deep model (A-reference), not an axiom over the changed function. The gold change is a pure statement REORDER (persist-then-derive), modeled directly as impl statement order A5-before-A6.

BASELINE (same-spec exit 0 for all 9): positive_control.py VERIFIES (weakness exit 0); prepatch.py FAILS verification (weakness exit 2) precisely on Result()==labels_of(inst.config) — prepatch bug reproduced.

ATTACKS (all same-spec exit 0; cmd: `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-13142 <path>`): atk_1_echo (persist selected, return labels_of(selected)==labels_of(inst.config)) -> weakness exit 0 CANDIDATE. Behaviorally IDENTICAL to gold. MANDATORY resolve run executed on its faithful (=gold) patch via run_resolve: COMPLETED=True RESOLVED=True ATTEMPTS=1 FLAKY=False note='resolved'. Legitimate echo -> NOT a weakness. atk_2_transient_return (return labels_of(final-trial), then persist = prepatch bug re-encoded) -> weakness exit 2; direct verify fails 'Postcondition ... Result()==labels_of(inst.config) might not hold' (line 95).

REJECTED (good). atk_3_strict_gt_tie (backward scan uses strict '>' => keeps LATEST max on ties, != earliest-max best_config) -> weakness exit 2; verify fails loop invariant 'selected == best_config(...)'. REJECTED (good) — spec pins earliest-max selection. atk_4_offbyone (loop guard i>0, over-scan boundary) -> weakness exit 2. REJECTED. atk_5_first_config (partial-domain: always select run_config[0]) -> weakness exit 2. REJECTED. atk_6_wrong_label_source (persist correct best but return labels_of(run_config[0]) — ungrounded-oracle echo variant) -> weakness exit 2. REJECTED. atk_7_skip_persist (leave inst.config=final trial, return labels_of(selected)) -> weakness exit 2; verify fails 'inst.config == best_config(...) might not hold' (line 91). REJECTED (good) — spec pins persisted config.

Only the behaviorally-equivalent echo verified, and its materialized faithful patch (the gold patch verbatim) RESOLVES under the official harness. No verifying same-spec wrong impl exists. Every genuinely-wrong impl (partial-domain, boundary, control-flow/tie, ungrounded-oracle, transient-config, skip-persist) is rejected on a load-bearing functional postcondition/invariant.

REFINEMENT.MD A-LEG AUDIT: legs are R / A-consumed / A-reference / I — no kind-3. A4 (A-reference best_config/best_score): model '>=' front-recursion = earliest-max; real loop base.py:255-258 strict '>' forward-scan = earliest-max; agree; G-AX (axiom_check.py) checks retained params==best trial & order observable; atk_3 confirms spec enforces this. A6 (A-consumed labels_of): purity-only abstraction of the unchanged e-step/argmax query primitive; G-AX checks determinism + config-functionality + e-step==predict; atk_2/atk_6 confirm the spec binds Result to labels_of of the held config. A1-A3/A5 (R/I) covered mechanically by recorded G-CONF (100176 checks, 0 disagreements) and G-MUT (20/20). The one genuinely changed op (query ordering) is modeled directly as impl statement order (the exact thing the prepatch reverses). Correspondence holds.

VERDICT: SOUND — >=5 distinct wrong impls run, none breaks verify=>correct; the sole verifying candidate's faithful patch resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real callee) verdict for scikit-learn__scikit-learn-13142 (nagini).

SPEC INTEGRITY: same-spec toolkit exits 0 on model.py; the spec region (pre/post-conditions + pure best_config/best_score + labels_of axiom) is byte-identical to the bundle. model.py verifies non-vacuously (nagini_verify.sh: Verification successful, 13.65s). The byte-identical-spec prepatch (only A5/A6 order swapped) fails precisely on Ensures(Result()==labels_of(inst.config)), so the discriminating clause is real, not vacuous.

CHECKED AGAINST THE REAL PATCHED CALLEE (BaseMixture.fit_predict, sklearn/mixture/base.py, base_commit 1c8668b...; worktree created at the base commit and inspected):
1. Tie-breaking: real loop uses strict '>' (base.py:255 `if lower_bound > max_lower_bound`), retaining the EARLIEST largest-lower-bound trial. Spec best_config uses '>=' at the front-recursion head, which yields exactly earliest-max. Verified agreement on [5,5], [3,5], [5,5,3], [3,5,5] — no divergence.
2. labels_of is @Pure @ContractOnly with NO Ensures body: the proof consumes ONLY purity (same config => same labels). It does not claim any exact label value, so it cannot over-claim the real _e_step->argmax / predict primitive. This is the weakest sufficient contract, not too strong.
3. Type abstraction is observationally faithful: score int is order-only (the loop uses only '>'); config int <-> parameter-set with equality iff labels agree; label modeled as one opaque deterministic value of the held config for fixed X. None of these strengthen the spec beyond real behavior.
4. Postconditions match the PATCHED fit_predict: persist selected-best (base.py `_set_parameters(best_params)`) then derive labels from the persisted config (A5-before-A6). No postcondition asserts anything the real patched routine violates.

CORROBORATION: recorded G-AX pass (16 n_init>1 configs, order observable) and G-CONF pass (100176 injected+e2e checks, 0 disagreements, seed 13142, direct shadow). The worktree is source-only (not compiled) so I could not re-execute axiom_check.py/conformance_check.py here; both were run in Docker at construction and recorded exit 0. I found no input where the modeled function disagrees with the real callee.

VERDICT: FAITHFUL (no diverging input found; spec is neither too strong nor drifted from repo behavior).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: move the final label-deriving e-step (`_, log_resp = self._e_step(X)`) so it runs AFTER `self._set_parameters(best_params)`, so returned labels derive from the SELECTED-best params rather than the last-trial params (fixing fit_predict != predict when n_init>1).

Mechanical G-LEAK screen PASSES (leakage.screen over the nagini spec view: no hard failures). Verified independently.

Spec-view assessment: the consumer-visible spec view ELIDES the impl region (`...  # implementation elided`), so the ordering-load-bearing statements/comments (`inst.config = selected` then `labels = labels_of(inst.config)`, and the 'Persist selected config THEN derive labels' comment) are NOT visible. The visible parts — module docstring, Estimator, labels_of axiom, best_score/best_config pure selection helpers, and the pre/post-conditions — only formalize the property ALREADY public in problem_statement: fit_predict labels must equal a subsequent predict/query on the fitted object, for every n_init. The postcondition `Result() == labels_of(inst.config)` + `inst.config == best_config(...)` restates 'returned labels = labels of the config the object ends up holding = what predict would give', which is exactly the publicly-stated bug/requirement ('predict and fit_predict disagree when n_init>1'), not a disclosure of the edit site or mechanism.

No patched file path (sklearn/mixture/base.py), no patched repo symbols (fit_predict, _e_step, _set_parameters, _get_parameters, log_resp, best_params), no diff markers, no bug/fix narration appear in the spec view. The spec expresses the correctness property (as any spec must) without revealing the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).