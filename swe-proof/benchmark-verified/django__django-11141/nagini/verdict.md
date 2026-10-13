# P2 adversarial audit — django__django-11141

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_13.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,6 +96,8 @@
                                       treat_empty_as_migrated))
     # post-conditions-end
     # impl-start
+    if not has_regular_file_marker:
+        return 0
     if not exposes_search_path:
         return 0
     if len(migration_names) > 0 or treat_empty_as_migrated:
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,5 @@
     # impl-start
     if not exposes_search_path:
         return 0
-    if len(migration_names) > 0 or treat_empty_as_migrated:
-        return 1
-    return 0
+    return 1
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,6 +98,9 @@
     # impl-start
     if not exposes_search_path:
         return 0
+    if (not has_regular_file_marker) and len(migration_names) > 0 and \
+            not treat_empty_as_migrated:
+        return 0
     if len(migration_names) > 0 or treat_empty_as_migrated:
         return 1
     return 0
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
     # impl-start
     if not exposes_search_path:
         return 0
-    if len(migration_names) > 0 or treat_empty_as_migrated:
+    if len(migration_names) > 1 or treat_empty_as_migrated:
         return 1
     return 0
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -98,7 +98,7 @@
     # impl-start
     if not exposes_search_path:
         return 0
-    if len(migration_names) > 0 or treat_empty_as_migrated:
+    if len(migration_names) > 0:
         return 1
     return 0
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,9 +96,10 @@
                                       treat_empty_as_migrated))
     # post-conditions-end
     # impl-start
+    migration_names.append(0)
     if not exposes_search_path:
         return 0
-    if len(migration_names) > 0 or treat_empty_as_migrated:
+    if len(migration_names) > 1 or treat_empty_as_migrated:
         return 1
     return 0
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -96,9 +96,6 @@
                                       treat_empty_as_migrated))
     # post-conditions-end
     # impl-start
-    if not exposes_search_path:
-        return 0
-    if len(migration_names) > 0 or treat_empty_as_migrated:
-        return 1
-    return 0
+    return migrated_code(exposes_search_path, len(migration_names),
+                         treat_empty_as_migrated)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -100,5 +100,7 @@
         return 0
     if len(migration_names) > 0 or treat_empty_as_migrated:
         return 1
+    if has_regular_file_marker:
+        return 1
     return 0
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,6 +96,9 @@
                                       treat_empty_as_migrated))
     # post-conditions-end
     # impl-start
+    i = 0
+    while i < 1:
+        i = i - 1
     if not exposes_search_path:
         return 0
     if len(migration_names) > 0 or treat_empty_as_migrated:
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -97,8 +97,8 @@
     # post-conditions-end
     # impl-start
     if not exposes_search_path:
+        return 1
+    if len(migration_names) > 0 or treat_empty_as_migrated:
         return 0
-    if len(migration_names) > 0 or treat_empty_as_migrated:
-        return 1
-    return 0
+    return 1
     # impl-end
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -100,5 +100,6 @@
         return 0
     if len(migration_names) > 0 or treat_empty_as_migrated:
         return 1
-    return 0
+    while True:
+        pass
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -100,5 +100,8 @@
         return 0
     if len(migration_names) > 0 or treat_empty_as_migrated:
         return 1
+    if has_regular_file_marker:
+        return is_migrated_app(has_regular_file_marker, exposes_search_path,
+                               migration_names, treat_empty_as_migrated)
     return 0
     # impl-end
```

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -96,9 +96,10 @@
                                       treat_empty_as_migrated))
     # post-conditions-end
     # impl-start
+    discovered = len(migration_names)
     if not exposes_search_path:
         return 0
-    if len(migration_names) > 0 or treat_empty_as_migrated:
+    if discovered > 0 or treat_empty_as_migrated:
         return 1
     return 0
     # impl-end
```

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

```diff
@@ -100,5 +100,5 @@
         return 0
     if len(migration_names) > 0 or treat_empty_as_migrated:
         return 1
-    return 0
+    raise ValueError("no migrations discovered")
     # impl-end
```

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

```diff
@@ -100,5 +100,7 @@
         return 0
     if len(migration_names) > 0 or treat_empty_as_migrated:
         return 1
-    return 0
+    zero = len(migration_names)
+    scratch = 1 // zero
+    return 0 * scratch
     # impl-end
```

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,6 +96,7 @@
                                       treat_empty_as_migrated))
     # post-conditions-end
     # impl-start
+    Assert(False)
     if not exposes_search_path:
         return 0
     if len(migration_names) > 0 or treat_empty_as_migrated:
```

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

```diff
@@ -96,9 +96,19 @@
                                       treat_empty_as_migrated))
     # post-conditions-end
     # impl-start
+    count = 0
+    i = 0
+    while i < len(migration_names):
+        Invariant(Acc(list_pred(migration_names), 1 / 4))
+        Invariant(0 <= i and i <= len(migration_names))
+        Invariant(count >= 0 and count <= i)
+        Invariant(MustTerminate(len(migration_names) - i + 1))
+        if migration_names[i] != 0:
+            count = count + 1
+        i = i + 1
     if not exposes_search_path:
         return 0
-    if len(migration_names) > 0 or treat_empty_as_migrated:
+    if count > 0 or treat_empty_as_migrated:
         return 1
     return 0
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for django__django-11141.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the loader scans an installed application's migrations module after a
  successful import, it classifies that application into exactly one of two
  groups, encoded here as the result code:

      1  -> the application is treated as having migrations ("migrated")
      0  -> the application is treated as having no migrations ("unmigrated")

  The classification depends only on three observable facts about the imported
  module and one loader flag:

    * whether the module is a package, i.e. exposes a search path
      (``exposes_search_path``) — a plain module that is not a package, such as
      a single ``migrations.py`` file, exposes no search path and is always
      classified as unmigrated;

    * the collection of migration module names discovered on that search path
      (``migration_names``), already filtered down to the genuine migration
      modules — only how many were found bears on the classification;

    * whether the loader has been asked to tolerate the absence of any
      migrations (``treat_empty_as_migrated``).

  An application is classified as migrated exactly when its module exposes a
  search path AND it either has at least one discovered migration name OR the
  tolerate-empty flag is set; otherwise it is classified as unmigrated.

  Crucially, whether the package carries a conventional on-disk file marker
  (``has_regular_file_marker``) does NOT influence the classification at all: a
  package whose search path yields migration names is migrated regardless of
  that marker. Therefore a package directory that exposes its modules only
  through a search path and carries no file marker (an implicit namespace
  package) is classified identically to one that has a file marker.

The migrations module is a rich Python package object in the repository; here
the only fields that bear on the classification are modelled directly — two
booleans for "exposes a search path" / "carries a file marker", and the
discovered-name collection as a ``List[int]`` whose length is all that matters.
The discovered-name collection is read-only; the classification mutates nothing.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No axioms: the classification is modelled deeply over concrete booleans and
# the length of the discovered-name collection; nothing opaque is consumed.)
# axioms-end

# pure-start
@Pure
def migrated_code(exposes_search_path: bool, discovered_file_count: int,
                  treat_empty_as_migrated: bool) -> int:
    """The classification outcome as a result code: 1 ("migrated") exactly when
    the module exposes a search path AND either at least one migration name was
    discovered there or the tolerate-empty flag is set; otherwise 0
    ("unmigrated"). The on-disk file marker does not appear, so the outcome is
    independent of it by construction."""
    if exposes_search_path and (discovered_file_count > 0 or
                                treat_empty_as_migrated):
        return 1
    return 0
# pure-end

def is_migrated_app(
    has_regular_file_marker: bool,
    exposes_search_path: bool,
    migration_names: List[int],
    treat_empty_as_migrated: bool,
) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(migration_names), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(migration_names), 1 / 2))
    # The discovered-name collection is read-only: unchanged in length/content.
    Ensures(ToSeq(migration_names) == Old(ToSeq(migration_names)))
    # The result is one of the two classification codes.
    Ensures(Result() == 0 or Result() == 1)
    # The result is exactly the classification outcome over the search-path
    # flag, the number of discovered migration names, and the tolerate flag.
    # The on-disk file marker (has_regular_file_marker) does not appear on the
    # right-hand side, so the result is pinned independently of it: no verifying
    # implementation can let the marker change the classification.
    Ensures(Result() == migrated_code(exposes_search_path,
                                      len(migration_names),
                                      treat_empty_as_migrated))
    # post-conditions-end
    # impl-start
    ok = exposes_search_path and (len(migration_names) > 0 or
                                  treat_empty_as_migrated)
    if ok:
        return 1
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-11141/nagini. 17 same-spec attacks + 1 positive control encoded  by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; `same-spec` returned SAME for all 18). Weakness runs were batched 3-concurrent as background jobs (each Nagini check = JVM+Z3) via run_weakness.sh; verify logs are weak_atk_*.log next to each attack.

Command shape (per attack): `python -m swebench_unified.adversary weakness nagini django__django-11141 atk_N.py`

### RESULTS (exit 2 = NOT-A-COUNTEREXAMPLE / spec rejected; exit 0 = CANDIDATE):
- atk_1 (PREPATCH BUG re-encoded: reinstates the removed `if not has_regular_file_marker: return 0` guard ahead of the count check = model_prepatch.py's B1 defect) -> exit 2, verification failed. Prepatch reproduced and rejected.
- atk_2 (PREPATCH-2 re-encoded: any search-path package unconditionally `return 1`, the old unconditional migrated_apps.add = B2) -> exit 2.
- atk_3 (PARTIAL-DOMAIN, narrowed to the single F2P discriminating input: marker-less package that DOES hold migrations and no tolerate flag -> 0; correct everywhere else) -> exit 2. This is the prior pass's named counterexample class ("partial-domain-marker-dependence") re-encoded at minimum width; the marker-free postcondition still pins it.
- atk_4 (BOUNDARY / off-by-one: `len(migration_names) > 1`) -> exit 2.
- atk_5 (drops the tolerate-empty flag; count-only) -> exit 2.
- atk_6 (CONTROL-FLOW EFFECT / frame: `migration_names.append(0)` then classify off the inflated count) -> exit 2 — the `Acc(list_pred,1/2)` + `ToSeq == Old(ToSeq)` frame legs bite.
- atk_7 (UNGROUNDED-ORACLE ECHO: impl returns `migrated_code(...)` verbatim) -> exit 0 CANDIDATE (18.0s).
- atk_8 (marker dependence in the OTHER polarity: marker-bearing empty package -> 1) -> exit 2.
- atk_9 (DIVERGENCE: `while i < 1: i = i - 1` before classifying) -> exit 2 — MustTerminate(2) at the method level rejects it.
- atk_10 (INVERTED CODES) -> exit 2.
- atk_11 (CONDITIONAL divergence exactly on the empty/not-tolerated case that must be 0 — the partial-correctness escape) -> exit 2.
- atk_12 (GUARDED SELF-CALL on (marker, package, empty, not-tolerated): recurses instead of returning 0) -> exit 2; no vacuous acceptance.
- atk_13 (EVALUATION-ORDER: hoists the count READ above the search-path guard) -> exit 0 CANDIDATE (19.2s).
- atk_14 (EXCEPTIONAL exit instead of the unmigrated classification: `raise ValueError`) -> exit 2.
- atk_15 (postcondition-correct but with an unproven runtime op on the empty path: `1 // len(migration_names)`) -> exit 2 — Nagini demands the division be established.
- atk_16 (VACUITY CONTROL: `Assert(False)` at entry) -> exit 2. The obligation is genuinely reachable, so every rejection above is a real verdict, not an infeasible-guard artifact.
- atk_17 (ELEMENT-FILTERING attack on the cardinality-only abstraction A3/mapping.md §2: counts only names with `!= 0` under a MustTerminate'd loop) -> exit 2 — `len(...)` in the postcondition pins the cardinality, so no extra element predicate survives.
- atk_pos (positive control, restructured single-boolean correct impl) -> VERIFIES (16.5s).

MANDATORY RESOLVE RUNS for every CANDIDATE (materialized faithful refined patch, generated against `git show 5d9cf79ba...:django/db/migrations/loader.py`, `git apply --check` clean, `ast.parse` clean; run 3-concurrent in background via pw/run_resolves.sh -> `swebench_unified.harness.run_resolve('django__django-11141', <diff>, timeout=1800)`; raw JSON in pw/resolve_*.json):
- atk_7 -> pw/patch_atk_7.diff: completed=True, RESOLVED=True, attempts=1, F2P failures [], P2P failures []. The echo impl's faithful refinement carries the `hasattr(module,'__path__')` conjunct into the single classification expression; behaviourally the gold decision.
- atk_13 -> pw/patch_atk_13.diff: completed=True, RESOLVED=True, attempts=1, F2P failures [], P2P failures []. Hoisting the count READ (`discovered = len(migration_names)`) is a local binding; per refinement.md A3 the kind-I discovery callee stays at its own site.
- atk_pos -> pw/patch_atk_pos.diff: completed=True, RESOLVED=True, attempts=1. Positive control resolves.
No verifying same-spec impl's faithful patch failed to resolve => no verify-but-not-correct witness. verify => correct holds for every attack run.

FALSIFICATION PROBE (the one place I could bend atk_13 into a break, reported for completeness — it is an UNFAITHFUL refinement, not a spec defect): pw/patch_atk_13b.diff hoists the DISCOVERY CALL itself (`pkgutil.iter_modules(module.__path__)`) above the `hasattr(module,'__path__')` guard, as a naive "all parameters exist at entry" reading of the model might suggest. run_resolve: completed=True, RESOLVED=False, attempts=3 (consistent, not flaky), P2P failure ['test_load_module_file'] — a plain migrations.py has no `__path__`, so the hoisted discovery raises. This does NOT break the spec: refinement.md A3/A5 and mapping.md §3 explicitly tag the `iter_modules` discovery as kind-I at its own unchanged site and A5 as identical control flow (non-package short-circuits BEFORE discovery), so 13b is outside the declared refinement map. It is recorded because it is the sharpest thing the abstraction admits, and the map already excludes it in writing.

REFINEMENT.MD AUDIT (A-legs / kind-3): legs A1-A7 are tagged R, R, I+R, R, I, I+R, R. There is NO kind-3 leg, NO A-consumed leg and NO A-reference leg — consistent with model.py's empty axioms region (verified by grep: no `axiom`, no `@ContractOnly`, no `Assume` anywhere in the file, and the axioms region is comment-only) and with meta.json `axioms: []`, `deep_model_references: []`, G-AX = skip ("no axiom_check.py (no axioms in bundle)"). So the audit's assigned focus — the A legs' correspondence to real callees — is vacuous here BY CONSTRUCTION rather than by omission: there is no assumption surface to be unsound.

I checked the one thing that could have hidden an implicit axiom, the claim that the single library callee is unchanged: `grep -n iter_modules` on the base image and on the gold-patched image is byte-identical (`pkgutil.iter_modules(module.__path__)` plus the `not is_pkg and name[0] not in '_~'` filter), so treating the discovered-name collection as an opaque input is a genuine kind-I step, not an axiom in disguise. A2's negated-polarity binding (`has_regular_file_marker == not (getattr(module,'__file__',None) is None)`) is coherent and its whole role is to sit in the signature while being ABSENT from `migrated_code`'s argument list, which is what makes marker-independence machine-enforced — confirmed by atk_3 and atk_8 (both polarities of marker dependence rejected).

Model<->patch correspondence checked case-by-case against the post-patch image extracted here (wt/r after applying patch.diff): non-package->0, package+names>0->1, package+empty+tolerate->1, package+empty+no-tolerate->0; matches the model on all four.

**Verdict SOUND:** 17 same-spec attacks run (14 wrong impls rejected including both prepatch bugs, the prior pass's named counterexample, boundary, control-flow-effect, divergence, guarded-self-call, exception-exit, unproven-runtime-op and element-filter classes; vacuity control confirms non-vacuity), 3 CANDIDATEs each had their faithful patch materialized and RUN through the official harness, and all 3 RESOLVED.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 15 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py`, `atk_9.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_14.py`, `atk_15.py`, `atk_16.py`, `atk_17.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_7.py`, `atk_13.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

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

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.py` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.py` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.py` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for django__django-11141.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the loader scans an installed application's migrations module after a
  successful import, it classifies that application into exactly one of two
  groups, encoded here as the result code:

      1  -> the application is treated as having migrations ("migrated")
      0  -> the application is treated as having no migrations ("unmigrated")

  The classification depends only on three observable facts about the imported
  module and one loader flag:

    * whether the module is a package, i.e. exposes a search path
      (``exposes_search_path``) — a plain module that is not a package, such as
      a single ``migrations.py`` file, exposes no search path and is always
      classified as unmigrated;

    * the collection of migration module names discovered on that search path
      (``migration_names``), already filtered down to the genuine migration
      modules — only how many were found bears on the classification;

    * whether the loader has been asked to tolerate the absence of any
      migrations (``treat_empty_as_migrated``).

  An application is classified as migrated exactly when its module exposes a
  search path AND it either has at least one discovered migration name OR the
  tolerate-empty flag is set; otherwise it is classified as unmigrated.

  Crucially, whether the package carries a conventional on-disk file marker
  (``has_regular_file_marker``) does NOT influence the classification at all: a
  package whose search path yields migration names is migrated regardless of
  that marker. Therefore a package directory that exposes its modules only
  through a search path and carries no file marker (an implicit namespace
  package) is classified identically to one that has a file marker.

The migrations module is a rich Python package object in the repository; here
the only fields that bear on the classification are modelled directly — two
booleans for "exposes a search path" / "carries a file marker", and the
discovered-name collection as a ``List[int]`` whose length is all that matters.
The discovered-name collection is read-only; the classification mutates nothing.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
# (No axioms: the classification is modelled deeply over concrete booleans and
# the length of the discovered-name collection; nothing opaque is consumed.)
# axioms-end

# pure-start
@Pure
def migrated_code(exposes_search_path: bool, discovered_file_count: int,
                  treat_empty_as_migrated: bool) -> int:
    """The classification outcome as a result code: 1 ("migrated") exactly when
    the module exposes a search path AND either at least one migration name was
    discovered there or the tolerate-empty flag is set; otherwise 0
    ("unmigrated"). The on-disk file marker does not appear, so the outcome is
    independent of it by construction."""
    if exposes_search_path and (discovered_file_count > 0 or
                                treat_empty_as_migrated):
        return 1
    return 0
# pure-end

def is_migrated_app(
    has_regular_file_marker: bool,
    exposes_search_path: bool,
    migration_names: List[int],
    treat_empty_as_migrated: bool,
) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(migration_names), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(migration_names), 1 / 2))
    # The discovered-name collection is read-only: unchanged in length/content.
    Ensures(ToSeq(migration_names) == Old(ToSeq(migration_names)))
    # The result is one of the two classification codes.
    Ensures(Result() == 0 or Result() == 1)
    # The result is exactly the classification outcome over the search-path
    # flag, the number of discovered migration names, and the tolerate flag.
    # The on-disk file marker (has_regular_file_marker) does not appear on the
    # right-hand side, so the result is pinned independently of it: no verifying
    # implementation can let the marker change the classification.
    Ensures(Result() == migrated_code(exposes_search_path,
                                      len(migration_names),
                                      treat_empty_as_migrated))
    # post-conditions-end
    # impl-start
    ok = exposes_search_path and (len(migration_names) > 0 or
                                  treat_empty_as_migrated)
    if ok:
        return 1
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit, django__django-11141/nagini. 17 same-spec attacks + 1 positive control encoded  by copying model.py and editing ONLY the impl region (axioms/@Pure/Requires/Ensures byte-identical; `same-spec` returned SAME for all 18). Weakness runs were batched 3-concurrent as background jobs (each Nagini check = JVM+Z3) via run_weakness.sh; verify logs are weak_atk_*.log next to each attack.

Command shape (per attack): `python -m swebench_unified.adversary weakness nagini django__django-11141 atk_N.py`

### RESULTS (exit 2 = NOT-A-COUNTEREXAMPLE / spec rejected; exit 0 = CANDIDATE):
- atk_1 (PREPATCH BUG re-encoded: reinstates the removed `if not has_regular_file_marker: return 0` guard ahead of the count check = model_prepatch.py's B1 defect) -> exit 2, verification failed. Prepatch reproduced and rejected.
- atk_2 (PREPATCH-2 re-encoded: any search-path package unconditionally `return 1`, the old unconditional migrated_apps.add = B2) -> exit 2.
- atk_3 (PARTIAL-DOMAIN, narrowed to the single F2P discriminating input: marker-less package that DOES hold migrations and no tolerate flag -> 0; correct everywhere else) -> exit 2. This is the prior pass's named counterexample class ("partial-domain-marker-dependence") re-encoded at minimum width; the marker-free postcondition still pins it.
- atk_4 (BOUNDARY / off-by-one: `len(migration_names) > 1`) -> exit 2.
- atk_5 (drops the tolerate-empty flag; count-only) -> exit 2.
- atk_6 (CONTROL-FLOW EFFECT / frame: `migration_names.append(0)` then classify off the inflated count) -> exit 2 — the `Acc(list_pred,1/2)` + `ToSeq == Old(ToSeq)` frame legs bite.
- atk_7 (UNGROUNDED-ORACLE ECHO: impl returns `migrated_code(...)` verbatim) -> exit 0 CANDIDATE (18.0s).
- atk_8 (marker dependence in the OTHER polarity: marker-bearing empty package -> 1) -> exit 2.
- atk_9 (DIVERGENCE: `while i < 1: i = i - 1` before classifying) -> exit 2 — MustTerminate(2) at the method level rejects it.
- atk_10 (INVERTED CODES) -> exit 2.
- atk_11 (CONDITIONAL divergence exactly on the empty/not-tolerated case that must be 0 — the partial-correctness escape) -> exit 2.
- atk_12 (GUARDED SELF-CALL on (marker, package, empty, not-tolerated): recurses instead of returning 0) -> exit 2; no vacuous acceptance.
- atk_13 (EVALUATION-ORDER: hoists the count READ above the search-path guard) -> exit 0 CANDIDATE (19.2s).
- atk_14 (EXCEPTIONAL exit instead of the unmigrated classification: `raise ValueError`) -> exit 2.
- atk_15 (postcondition-correct but with an unproven runtime op on the empty path: `1 // len(migration_names)`) -> exit 2 — Nagini demands the division be established.
- atk_16 (VACUITY CONTROL: `Assert(False)` at entry) -> exit 2. The obligation is genuinely reachable, so every rejection above is a real verdict, not an infeasible-guard artifact.
- atk_17 (ELEMENT-FILTERING attack on the cardinality-only abstraction A3/mapping.md §2: counts only names with `!= 0` under a MustTerminate'd loop) -> exit 2 — `len(...)` in the postcondition pins the cardinality, so no extra element predicate survives.
- atk_pos (positive control, restructured single-boolean correct impl) -> VERIFIES (16.5s).

MANDATORY RESOLVE RUNS for every CANDIDATE (materialized faithful refined patch, generated against `git show 5d9cf79ba...:django/db/migrations/loader.py`, `git apply --check` clean, `ast.parse` clean; run 3-concurrent in background via pw/run_resolves.sh -> `swebench_unified.harness.run_resolve('django__django-11141', <diff>, timeout=1800)`; raw JSON in pw/resolve_*.json):
- atk_7 -> pw/patch_atk_7.diff: completed=True, RESOLVED=True, attempts=1, F2P failures [], P2P failures []. The echo impl's faithful refinement carries the `hasattr(module,'__path__')` conjunct into the single classification expression; behaviourally the gold decision.
- atk_13 -> pw/patch_atk_13.diff: completed=True, RESOLVED=True, attempts=1, F2P failures [], P2P failures []. Hoisting the count READ (`discovered = len(migration_names)`) is a local binding; per refinement.md A3 the kind-I discovery callee stays at its own site.
- atk_pos -> pw/patch_atk_pos.diff: completed=True, RESOLVED=True, attempts=1. Positive control resolves.
No verifying same-spec impl's faithful patch failed to resolve => no verify-but-not-correct witness. verify => correct holds for every attack run.

FALSIFICATION PROBE (the one place I could bend atk_13 into a break, reported for completeness — it is an UNFAITHFUL refinement, not a spec defect): pw/patch_atk_13b.diff hoists the DISCOVERY CALL itself (`pkgutil.iter_modules(module.__path__)`) above the `hasattr(module,'__path__')` guard, as a naive "all parameters exist at entry" reading of the model might suggest. run_resolve: completed=True, RESOLVED=False, attempts=3 (consistent, not flaky), P2P failure ['test_load_module_file'] — a plain migrations.py has no `__path__`, so the hoisted discovery raises. This does NOT break the spec: refinement.md A3/A5 and mapping.md §3 explicitly tag the `iter_modules` discovery as kind-I at its own unchanged site and A5 as identical control flow (non-package short-circuits BEFORE discovery), so 13b is outside the declared refinement map. It is recorded because it is the sharpest thing the abstraction admits, and the map already excludes it in writing.

REFINEMENT.MD AUDIT (A-legs / kind-3): legs A1-A7 are tagged R, R, I+R, R, I, I+R, R. There is NO kind-3 leg, NO A-consumed leg and NO A-reference leg — consistent with model.py's empty axioms region (verified by grep: no `axiom`, no `@ContractOnly`, no `Assume` anywhere in the file, and the axioms region is comment-only) and with meta.json `axioms: []`, `deep_model_references: []`, G-AX = skip ("no axiom_check.py (no axioms in bundle)"). So the audit's assigned focus — the A legs' correspondence to real callees — is vacuous here BY CONSTRUCTION rather than by omission: there is no assumption surface to be unsound.

I checked the one thing that could have hidden an implicit axiom, the claim that the single library callee is unchanged: `grep -n iter_modules` on the base image and on the gold-patched image is byte-identical (`pkgutil.iter_modules(module.__path__)` plus the `not is_pkg and name[0] not in '_~'` filter), so treating the discovered-name collection as an opaque input is a genuine kind-I step, not an axiom in disguise. A2's negated-polarity binding (`has_regular_file_marker == not (getattr(module,'__file__',None) is None)`) is coherent and its whole role is to sit in the signature while being ABSENT from `migrated_code`'s argument list, which is what makes marker-independence machine-enforced — confirmed by atk_3 and atk_8 (both polarities of marker dependence rejected).

Model<->patch correspondence checked case-by-case against the post-patch image extracted here (wt/r after applying patch.diff): non-package->0, package+names>0->1, package+empty+tolerate->1, package+empty+no-tolerate->0; matches the model on all four.

**Verdict SOUND:** 17 same-spec attacks run (14 wrong impls rejected including both prepatch bugs, the prior pass's named counterexample, boundary, control-flow-effect, divergence, guarded-self-call, exception-exit, unproven-runtime-op and element-filter classes; vacuity control confirms non-vacuity), 3 CANDIDATEs each had their faithful patch materialized and RUN through the official harness, and all 3 RESOLVED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No diverging input found. The modeled function is is_migrated_app(has_regular_file_marker, exposes_search_path, migration_names, treat_empty_as_migrated) -> int, bound per mapping.md to the per-application classification inside MigrationLoader.load_disk (django/db/migrations/loader.py) with patch.diff APPLIED (the correct reference per the task framing).

**SETUP:** cloned django_django.git  at base_commit 5d9cf79baf07fc4aed7ad1b06990532a65378155 and applied patch.diff cleanly; a second pristine base tree for the sensitivity control.

**IMPORTANT MEASUREMENT TRAP RULED OUT:** my first test run silently imported a different, stale Django than the one under audit, which the runner reported in its "Testing against Django installed in ..." line. I re-ran everything against the base_commit worktree and verified the provenance of the code I measured directly: loader.`__file__` == loader.py, '`__file__`' guard absent, 'if migration_names or self.ignore_no_migrations' present. All results below are against the intended tree; the earlier 2 failures were that stale copy, not a spec defect.

### EVIDENCE (all vs the PATCHED tree):
1. Bundle conformance_check.py: exit 0, 100048 inputs (48 boundary + 100000 fuzz, seed 11141), 0 disagreements.
2. Nagini verifier on model.py: "Verification successful" (18.2s). Both prepatches FAIL on exactly the target postcondition Result() == migrated_code(...) (model_prepatch.py:94, model_prepatch_2.py:94), so the spec bites on both modeled deltas rather than being vacuous.
3. same_spec (markers via get_backend('nagini')) True for model_prepatch.py and model_prepatch_2.py — spec regions byte-identical, only impl differs.
4. INDEPENDENT on-disk oracle (fs_oracle_11141.py): I distrusted the bundle harness because it monkeypatches import_module AND pkgutil.iter_modules, i.e. it never exercises real import/discovery. Mine builds REAL directories (regular pkg with `__init__`.py, implicit namespace pkg without, and a non-package migrations.py), REAL migration files, and lets the REAL patched load_disk import and discover them; only apps.get_app_configs/migrations_module are faked to name one synthetic app. Model params observed independently off the real module (hasattr `__path__`, getattr `__file__`, the real iter_modules+'_~' filter). 38/38 cases agree, incl. all namespace-package cases.
5. SENSITIVITY CONTROL (the check that makes "no divergence" meaningful): the same oracle run against the pristine BASE tree reports 18/38 divergences, and they split exactly along the two modeled deltas — namespace pkgs with migrations classified 0 by base where spec says 1 (the dropped `__file__` guard), and empty regular pkgs with ignore=False classified 1 by base where spec says 0 (the relocated migrated_apps.add). So the oracle demonstrably detects this patch's delta and finds none post-patch.
6. Randomized real-FS fuzz (fuzz_oracle_11141.py, 600 cases, seed 991141): adversarial names (dunder, tilde, unicode-ish, CAPS, digit-leading, very long), sub-packages, namespace sub-dirs, non-.py junk. 0 divergences. (One empty-.pyc case raised ImportError from the migration-LOADING loop, which runs strictly AFTER the classification add(); I read the classification anyway — downstream, not a spec divergence.)
7. Real PEP420 MULTI-PORTION test (nspkg_11141.py): the fuzz reported multiportion_cases=0, i.e. my 2-root setup never actually produced a multi-portion `__path__` — an untested hole I closed rather than ignored. Built synthpkg and synthpkg.migrations as genuine namespace packages across two sys.path roots (real 2-element `__path__`, `__file__` genuinely absent): 12 multi-portion runs, 0 divergences, incl. 1+1, 0+1, empty+empty, filtered-only, shadowed duplicate (real dedupe -> names=1), 2+1. Confirms the List[int]/len() carrier and the 'only cardinality matters' abstraction (mapping.md sec 2) hold against real set-dedupe semantics.
8. reload() branch (reload_11141.py): every harness above (and the bundle's) purges sys.modules, so was_loaded was ALWAYS False and refinement.md A5's "I-elided" reload(module) never actually ran. I pre-imported the module so reload() really executes, including `__init__`.py files that append to and even WIPE their own `__path__` on re-execution — the only way that elision could bite. 16/16 agree, 0 divergences; the elision is justified.
9. Gold resolves: with the test_patch applied, migrations.test_loader = 25 tests OK on the patched tree; F2P test_loading_namespace_package fails at base with NodeNotFoundError(('migrations','0001_initial')). Matches the modeled behavior change.

**SPEC-TOO-STRONG ANALYSIS:** the postcondition pins Result() == migrated_code(exposes_search_path, len(migration_names), treat_empty_as_migrated), omitting has_regular_file_marker so marker-independence is enforced. That is exactly the post-patch behavior: the patched code branches only on hasattr(module,'`__path__`'), bool(migration_names) and self.ignore_no_migrations, never on `__file__`. Verified empirically — for every (exposes, count, tolerate) triple, flipping marker True/False (regular vs real namespace pkg) leaves the real classification unchanged. Result() in {0,1} and ToSeq unchanged are also faithful: the real code performs exactly one of two mutually-exclusive set.add per app (my oracles assert single-valuedness on every case and it never tripped) and mutates no discovered-name collection. Requires is only an access permission plus MustTerminate(2), so it admits the whole input domain and does not narrow it. The non-package short-circuit (return 0) matches the real `if not hasattr(module,'__path__')` arm, confirmed by the modulefile cases.

**CONCLUSION:** FAITHFUL. Across ~100.7k monkeypatched inputs plus 692 real-filesystem cases (38 structured + 600 fuzz + 12 real multi-portion namespace + 16 reload-branch, plus 4 non-package), the modeled function never disagreed with the real patched callee, while the same oracles detect this patch's delta at base in 18/38 cases. No axioms are consumed (no axiom_check.py ships, correctly), so there is no axiom-soundness surface to break here.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `model.py`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** MY OWN MEASUREMENTS (not inherited). No relaxation in this bundle: no RELAXED_LEAKAGE.md, no `relaxed_leakage` flag, meta gates.G-LEAK.status = "pass" (grep -ri relaxed over the bundle = 0 hits). So I judged this as an ordinary strict no-leakage review. Also confirmed no bundle file addresses the reviewer or suggests a verdict: grepped model.py/refinement.md/mapping.md for attacker|panel|G-PANEL|verdict|reviewer|NO-LEAKAGE|submit_result = 0 hits. verdict.md only transcribes prior machine verdicts and explicitly labels the agent notes advisory; it does not instruct me. No embedded-instruction finding.

**SPEC REGION IDENTITY:** same-spec on an identity copy of model.py = exit 0 ("SAME"). Recomputed markers.region_hashes: live spec_view a00c183d94..., post-conditions df68060a49..., pure b51b04cfaf..., impl bd96cab608... — all match gates.G-HYGIENE.data.region_hashes exactly.

SPEC-VIEW SYMBOL SCAN (markers.spec_view, which includes the docstring + all comments): zero hits for loader.py, load_disk, `__file__`, `__path__`, ignore_no_migrations, migrated_apps, unmigrated_apps, pkgutil, iter_modules, `__init__`.py, getattr, hasattr, MigrationLoader, app_config, and the ticket ids #21015/#23406/#29091. Verbatim gold-diff-line check (every +/- line of length>8 from patch.diff tested for substring presence in the spec view): NONE present. Every carrier is an abstracted proxy under a renamed identifier (exposes_search_path~`__path__`, has_regular_file_marker~`__file__`, treat_empty_as_migrated~ignore_no_migrations, migration_names count~the discovered set), so the spec view does not let a consumer reconstruct which file/attribute/field to touch.

MECHANICAL SCREEN + LIVENESS CONTROL: leakage.screen(model.py, nagini backend, gold patch, problem_statement) -> passed=True, hard_failures=[], warnings=[]. I did NOT take that at face value — I ran a positive control by injecting the real fix narration into the docstring, and the screen correctly failed with 4 hard findings (patched path 'django/db/migrations/loader.py' x2, patched symbol 'load_disk', narration 'fix'). The screen is live on this bundle, not vacuously passing.

THE ONLY REAL LEAKAGE QUESTION — facet B2 (the empty-package / tolerate split). The problem_statement covers only facet B1 (drop the `__file__` check; namespace packages have no `__file__` but do have `__path__`), and phrases 'search path'/'file marker'/'migrated'/'unmigrated' are spec-view-only wording for concepts the PS states in its own words, so B1 is plainly public. B2 (empty package -> unmigrated unless the tolerate flag is set) is NOT in the problem_statement, and hints_text is EMPTY (len 0), so the prior panel's framing of it as a 'nuance not in the PS' is the crux.

I resolved it empirically rather than by argument: in a /tmp worktree at base_commit 5d9cf79 I applied the NAIVE problem-statement-only fix (deleted the 5-line `__file__` guard and nothing else) and ran the repo's own migrations.test_loader.LoaderTests -> test_load_empty_dir FAILS ("'migrations' not found in {'messages','staticfiles'}"). That test is PASS_TO_PASS and pre-exists at base_commit with a fixture directory carrying no `__init__`.py. Re-applying the gold patch -> 21/21 OK. I also dropped just the tolerate clause from the gold ('if migration_names or self.ignore_no_migrations' -> 'if migration_names') and ran the full migrations suite -> test_showmigrations_no_migrations FAILS.

CONCLUSION: B2 and the tolerate flag are forced by solver-visible repo state (the existing failing P2P test plus ignore_no_migrations already in loader.py `__init__` at base_commit), not by hidden gold internals. A solver who deletes only the guard is told by the repo's own test suite that empty packages must stay unmigrated. The spec view therefore discloses no discriminator a solver could not derive from public artifacts — this is the legitimate function of a behavioral contract, not a leak.

LOAD-BEARING / STRIP-NARRATION CHECK: I de-narrated model.py (module docstring reduced to one line, all explanatory comments stripped, @Pure docstring blanked) and re-ran the pinned verifier on all three impls. Denarrated gold: Verification successful (14.4s). Denarrated prepatch (reinstated marker guard): Verification failed on 'Result() == migrated_code(...)'. Denarrated prepatch_2 (unconditional migrated for any package): Verification failed on the same postcondition. So the discrimination lives entirely in the FORMAL postcondition, and the prose is not doing the work — meaning the narration could in principle be trimmed further, but what remains is behavioral and non-reconstructive, which is the standard directive 6 asks for.

**CORE GATES RE-CONFIRMED MYSELF:** gold model.py verifies under pinned Nagini (exit 0, 'Verification successful', 18.9s); both prepatch variants pass same-spec (exit 0) and are rejected by adversary weakness ('NOT-A-COUNTEREXAMPLE... the spec rejected this impl'), so G-DIFF/G-GOLD's recorded dispositions hold on re-measurement and the marker-independence postcondition is not vacuous (ToSeq == Old(ToSeq) at Acc 1/2 blocks the overwrite-the-input mode).

NON-BLOCKING BOOKKEEPING (no bearing on leakage, flagged for hygiene): meta.json's TOP-LEVEL region_hashes block is stale relative to the artifact — top-level pre-conditions bc8e0ca0d8 vs live 43156c9a53, and top-level spec_view 2b04d12e71 vs live a00c183d94. The G-HYGIENE gate's own nested copy matches live on all six regions, so the stamped gate verdict describes the current model.py; only the duplicated top-level block was not refreshed on the 2026-08-14 re-stamp. Worth a re-stamp so the two blocks agree, but it is not leakage and does not affect this verdict.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
