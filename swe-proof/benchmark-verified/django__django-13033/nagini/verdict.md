# P2 adversarial audit — django__django-13033

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # whole path token is never equal to its terminal segment alone (the
     # split-then-rejoin invariant of a multi-segment lookup path).
     Requires(Implies(len(path_segments) > 1, name != path_terminal(path_segments)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
@@ -93,7 +91,7 @@
     # post-conditions-end
     # impl-start
     if (points_to_relation and has_default_ordering
-            and relation_own_column != path_terminal(path_segments)
+            and relation_own_column != name
             and name != PK()):
         return 1
     return 0
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # whole path token is never equal to its terminal segment alone (the
     # split-then-rejoin invariant of a multi-segment lookup path).
     Requires(Implies(len(path_segments) > 1, name != path_terminal(path_segments)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
@@ -92,9 +90,5 @@
              and name != PK()))
     # post-conditions-end
     # impl-start
-    if (points_to_relation and has_default_ordering
-            and relation_own_column != path_terminal(path_segments)
-            and name != PK()):
-        return 1
     return 0
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # whole path token is never equal to its terminal segment alone (the
     # split-then-rejoin invariant of a multi-segment lookup path).
     Requires(Implies(len(path_segments) > 1, name != path_terminal(path_segments)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
@@ -93,8 +91,7 @@
     # post-conditions-end
     # impl-start
     if (points_to_relation and has_default_ordering
-            and relation_own_column != path_terminal(path_segments)
-            and name != PK()):
+            and relation_own_column != path_terminal(path_segments)):
         return 1
     return 0
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # whole path token is never equal to its terminal segment alone (the
     # split-then-rejoin invariant of a multi-segment lookup path).
     Requires(Implies(len(path_segments) > 1, name != path_terminal(path_segments)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
@@ -92,9 +90,10 @@
              and name != PK()))
     # post-conditions-end
     # impl-start
-    if (points_to_relation and has_default_ordering
-            and relation_own_column != path_terminal(path_segments)
-            and name != PK()):
-        return 1
+    if points_to_relation:
+        if has_default_ordering:
+            if path_segments[0] != relation_own_column:
+                if name != PK():
+                    return 1
     return 0
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # whole path token is never equal to its terminal segment alone (the
     # split-then-rejoin invariant of a multi-segment lookup path).
     Requires(Implies(len(path_segments) > 1, name != path_terminal(path_segments)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
@@ -92,9 +90,7 @@
              and name != PK()))
     # post-conditions-end
     # impl-start
-    if (points_to_relation and has_default_ordering
-            and relation_own_column != path_terminal(path_segments)
-            and name != PK()):
+    if points_to_relation:
         return 1
     return 0
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # whole path token is never equal to its terminal segment alone (the
     # split-then-rejoin invariant of a multi-segment lookup path).
     Requires(Implies(len(path_segments) > 1, name != path_terminal(path_segments)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
@@ -95,6 +93,6 @@
     if (points_to_relation and has_default_ordering
             and relation_own_column != path_terminal(path_segments)
             and name != PK()):
-        return 1
-    return 0
+        return 0
+    return 1
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -78,7 +77,6 @@
     # whole path token is never equal to its terminal segment alone (the
     # split-then-rejoin invariant of a multi-segment lookup path).
     Requires(Implies(len(path_segments) > 1, name != path_terminal(path_segments)))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() == 0 or Result() == 1)
@@ -92,7 +90,7 @@
              and name != PK()))
     # post-conditions-end
     # impl-start
-    if (points_to_relation and has_default_ordering
+    if (points_to_relation
             and relation_own_column != path_terminal(path_segments)
             and name != PK()):
         return 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13033.

Behavioural contract (the observable ORM behaviour under specification).

A queryset can be ordered by a lookup path: a sequence of one or more name
segments joined by the lookup separator (e.g. ``record__root`` or
``record__root_id``). When the path resolves to a field that is a relation to
another model, the resolver decides one of two outcomes:

  * ``mode == 1`` -- sort by the related model's own default sort order (this
    expands the related model's declared ordering, which can flip the
    direction and add a join to the related table); or
  * ``mode == 0`` -- sort directly by the named target column (ascending, with
    no extra join to the related table).

The contract pins exactly when each outcome is required. The related model's
default sort order is substituted (``mode == 1``) only when ALL of the
following hold:

  * the resolved target field points to another model, AND
  * the related model declares a default sort order, AND
  * the named target is NOT the related field's own column, AND
  * the named target is NOT the primary-key shortcut.

When the named target IS the related field's own column (the path's terminal
token names that column directly), the query must sort by that column directly
(``mode == 0``); the related model's default sort order is NOT applied -- so a
queryset ordered by a related field's own column sorts ascending by that
column with a single join, while a queryset ordered by the related field
itself adopts the related model's default sort order.

``relation_own_column`` is the related field's own column token; ``name`` is
the whole lookup path; ``path_segments`` is that path decomposed into its
segments, with ``path_terminal(path_segments)`` its terminal segment. Strings
are modelled as ``PSeq[int]`` of Unicode code points and the lookup path as
``PSeq[PSeq[int]]`` of its segments (Nagini bans ``str`` indexing).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The decisive predicate is modelled deeply over the
# segment sequence; the unchanged machinery it guards -- join/target trimming
# and recursive expansion over the related model's sort order -- is not part of
# the modelled predicate and is represented only by the abstract `mode`
# outcome.)
# axioms-end


# pure-start
@Pure
def PK() -> PSeq[int]:
    # 'pk' -- the primary-key shortcut token.
    return PSeq(112, 107)


@Pure
def path_terminal(path_segments: PSeq[PSeq[int]]) -> PSeq[int]:
    """The terminal segment of a non-empty lookup path."""
    Requires(len(path_segments) > 0)
    return path_segments[len(path_segments) - 1]
# pure-end


def ordering_mode(name: PSeq[int],
                  path_segments: PSeq[PSeq[int]],
                  relation_own_column: PSeq[int],
                  points_to_relation: bool,
                  has_default_ordering: bool) -> int:
    # pre-conditions-start
    # The lookup path has at least one segment.
    Requires(len(path_segments) > 0)
    # A multi-segment path carries separators and preceding segments, so the
    # whole path token is never equal to its terminal segment alone (the
    # split-then-rejoin invariant of a multi-segment lookup path).
    Requires(Implies(len(path_segments) > 1, name != path_terminal(path_segments)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == 0 or Result() == 1)
    # The related model's default sort order is substituted (mode 1) exactly
    # when the target points to a relation with a default sort order, the named
    # target is not the related field's own column, and is not the primary-key
    # shortcut.
    Ensures((Result() == 1) ==
            (points_to_relation and has_default_ordering
             and relation_own_column != path_terminal(path_segments)
             and name != PK()))
    # post-conditions-end
    # impl-start
    if (points_to_relation and has_default_ordering
            and relation_own_column != path_terminal(path_segments)
            and name != PK()):
        return 1
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: django__django-13033 nagini. Spec models ordering_mode: the related-default-ordering decision predicate in SQLCompiler.find_ordering_name (compiler.py:730). The postcondition is a STRICT BICONDITIONAL that fully pins Result: Ensures(Result()==0 or Result()==1) AND Ensures((Result()==1) == (points_to_relation and has_default_ordering and relation_own_column != path_terminal(path_segments) and name != PK())). Result is therefore a total function of the inputs over the ENTIRE precondition domain, so any verifying impl must equal gold on every precondition-satisfying input.

A-LEG / CORRESPONDENCE AUDIT (my focus): refinement.md declares NO A-consumed and NO A-reference axioms; confirmed by grep -> no @ContractOnly in model.py and the axioms-start/end block is empty. Every leg in refinement.md §A is R (type refinement str<->PSeq[int], bool identity, branch-outcome<->mode) or I (identical op); §C explicitly claims no kind-3, verified. The only reference-style obligation is the PRECONDITION split invariant Implies(len(path_segments)>1, name != path_terminal(path_segments)), grounded by mapping.md §3 as an always-true fact of real str.split('__'). axiom_check.py RE-RUN: SOUND, split invariant holds on 100018 observations of real CPython str.split('__') (boundary + 2x50000 fuzz), exit 0. Because the invariant is always-true it excludes NO reachable input -> there is no domain narrowing that could hide a divergence between the modeled predicate and the real callee. Correspondence A3 (the changed conjunct, operand name -> pieces[-1] == path_terminal) is modeled deeply and exactly; it holds.

ATTACKS (all run via `python -m swebench_unified.adversary weakness nagini django__django-13033 <path>` with, lean venv python which has swebench_unified installed; nagini_verify used internally). All 8 files confirmed same-spec (adversary same-spec exit 0). Positive control pos_control.py = verbatim model.py: VERIFIED in 14.1s (adversary verify exit 0).
  - atk_1 (prepatch bug: relation_own_column != name instead of != path_terminal): weakness -> NOT-A-COUNTEREXAMPLE, does not verify (exit 2). prepatch reproduced/rejected.
  - atk_2 (partial-domain: constant return 0): does not verify (exit 2).
  - atk_3 (boundary: drop `name != PK()` conjunct): does not verify (exit 2).
  - atk_4 (control-flow-effect: nested ifs comparing path_segments[0] instead of terminal): does not verify (exit 2).
  - atk_5 (ungrounded-oracle echo: return 1 iff points_to_relation): does not verify (exit 2).
  - atk_6 (inverted outcome): does not verify (exit 2).
  - atk_7 (drop has_default_ordering conjunct): does not verify (exit 2).

NO attack came back a CANDIDATE (none shares-spec-AND-verifies), so there was NO verifying wrong impl whose faithful refined patch needed materializing/resolving; run_resolve was correctly not required and none was skipped. The strict biconditional over an unnarrowed domain is exactly why no verify-but-wrong impl can exist. Verdict: SOUND (>=5 distinct wrong impls run, none breaks the spec; positive control verifies; axiom/precondition correspondence holds).

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
"""Twin-artifact model for django__django-13033.

Behavioural contract (the observable ORM behaviour under specification).

A queryset can be ordered by a lookup path: a sequence of one or more name
segments joined by the lookup separator (e.g. ``record__root`` or
``record__root_id``). When the path resolves to a field that is a relation to
another model, the resolver decides one of two outcomes:

  * ``mode == 1`` -- sort by the related model's own default sort order (this
    expands the related model's declared ordering, which can flip the
    direction and add a join to the related table); or
  * ``mode == 0`` -- sort directly by the named target column (ascending, with
    no extra join to the related table).

The contract pins exactly when each outcome is required. The related model's
default sort order is substituted (``mode == 1``) only when ALL of the
following hold:

  * the resolved target field points to another model, AND
  * the related model declares a default sort order, AND
  * the named target is NOT the related field's own column, AND
  * the named target is NOT the primary-key shortcut.

When the named target IS the related field's own column (the path's terminal
token names that column directly), the query must sort by that column directly
(``mode == 0``); the related model's default sort order is NOT applied -- so a
queryset ordered by a related field's own column sorts ascending by that
column with a single join, while a queryset ordered by the related field
itself adopts the related model's default sort order.

``relation_own_column`` is the related field's own column token; ``name`` is
the whole lookup path; ``path_segments`` is that path decomposed into its
segments, with ``path_terminal(path_segments)`` its terminal segment. Strings
are modelled as ``PSeq[int]`` of Unicode code points and the lookup path as
``PSeq[PSeq[int]]`` of its segments (Nagini bans ``str`` indexing).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms. The decisive predicate is modelled deeply over the
# segment sequence; the unchanged machinery it guards -- join/target trimming
# and recursive expansion over the related model's sort order -- is not part of
# the modelled predicate and is represented only by the abstract `mode`
# outcome.)
# axioms-end


# pure-start
@Pure
def PK() -> PSeq[int]:
    # 'pk' -- the primary-key shortcut token.
    return PSeq(112, 107)


@Pure
def path_terminal(path_segments: PSeq[PSeq[int]]) -> PSeq[int]:
    """The terminal segment of a non-empty lookup path."""
    Requires(len(path_segments) > 0)
    return path_segments[len(path_segments) - 1]
# pure-end


def ordering_mode(name: PSeq[int],
                  path_segments: PSeq[PSeq[int]],
                  relation_own_column: PSeq[int],
                  points_to_relation: bool,
                  has_default_ordering: bool) -> int:
    # pre-conditions-start
    # The lookup path has at least one segment.
    Requires(len(path_segments) > 0)
    # A multi-segment path carries separators and preceding segments, so the
    # whole path token is never equal to its terminal segment alone (the
    # split-then-rejoin invariant of a multi-segment lookup path).
    Requires(Implies(len(path_segments) > 1, name != path_terminal(path_segments)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == 0 or Result() == 1)
    # The related model's default sort order is substituted (mode 1) exactly
    # when the target points to a relation with a default sort order, the named
    # target is not the related field's own column, and is not the primary-key
    # shortcut.
    Ensures((Result() == 1) ==
            (points_to_relation and has_default_ordering
             and relation_own_column != path_terminal(path_segments)
             and name != PK()))
    # post-conditions-end
    # impl-start
    if (points_to_relation and has_default_ordering
            and relation_own_column != path_terminal(path_segments)
            and name != PK()):
        return 1
    return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: django__django-13033 nagini. Spec models ordering_mode: the related-default-ordering decision predicate in SQLCompiler.find_ordering_name (compiler.py:730). The postcondition is a STRICT BICONDITIONAL that fully pins Result: Ensures(Result()==0 or Result()==1) AND Ensures((Result()==1) == (points_to_relation and has_default_ordering and relation_own_column != path_terminal(path_segments) and name != PK())). Result is therefore a total function of the inputs over the ENTIRE precondition domain, so any verifying impl must equal gold on every precondition-satisfying input.

A-LEG / CORRESPONDENCE AUDIT (my focus): refinement.md declares NO A-consumed and NO A-reference axioms; confirmed by grep -> no @ContractOnly in model.py and the axioms-start/end block is empty. Every leg in refinement.md §A is R (type refinement str<->PSeq[int], bool identity, branch-outcome<->mode) or I (identical op); §C explicitly claims no kind-3, verified. The only reference-style obligation is the PRECONDITION split invariant Implies(len(path_segments)>1, name != path_terminal(path_segments)), grounded by mapping.md §3 as an always-true fact of real str.split('__'). axiom_check.py RE-RUN: SOUND, split invariant holds on 100018 observations of real CPython str.split('__') (boundary + 2x50000 fuzz), exit 0. Because the invariant is always-true it excludes NO reachable input -> there is no domain narrowing that could hide a divergence between the modeled predicate and the real callee. Correspondence A3 (the changed conjunct, operand name -> pieces[-1] == path_terminal) is modeled deeply and exactly; it holds.

ATTACKS (all run via `python -m swebench_unified.adversary weakness nagini django__django-13033 <path>` with, lean venv python which has swebench_unified installed; nagini_verify used internally). All 8 files confirmed same-spec (adversary same-spec exit 0). Positive control pos_control.py = verbatim model.py: VERIFIED in 14.1s (adversary verify exit 0).
  - atk_1 (prepatch bug: relation_own_column != name instead of != path_terminal): weakness -> NOT-A-COUNTEREXAMPLE, does not verify (exit 2). prepatch reproduced/rejected.
  - atk_2 (partial-domain: constant return 0): does not verify (exit 2).
  - atk_3 (boundary: drop `name != PK()` conjunct): does not verify (exit 2).
  - atk_4 (control-flow-effect: nested ifs comparing path_segments[0] instead of terminal): does not verify (exit 2).
  - atk_5 (ungrounded-oracle echo: return 1 iff points_to_relation): does not verify (exit 2).
  - atk_6 (inverted outcome): does not verify (exit 2).
  - atk_7 (drop has_default_ordering conjunct): does not verify (exit 2).

NO attack came back a CANDIDATE (none shares-spec-AND-verifies), so there was NO verifying wrong impl whose faithful refined patch needed materializing/resolving; run_resolve was correctly not required and none was skipped. The strict biconditional over an unnarrowed domain is exactly why no verify-but-wrong impl can exist. Verdict: SOUND (>=5 distinct wrong impls run, none breaks the spec; positive control verifies; axiom/precondition correspondence holds).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift/over-strength) analysis for django__django-13033 nagini bundle.

MODELED FUNCTION: ordering_mode models the related-default-ordering decision predicate inside SQLCompiler.find_ordering_name (django/db/models/sql/compiler.py:552 @ base_commit; the guarding `if`). The spec's postcondition pins mode==1 iff (points_to_relation and has_default_ordering and relation_own_column != path_terminal(path_segments) and name != PK()) — i.e. it models the GOLD-PATCHED predicate `field.is_relation and opts.ordering and getattr(field,'attname',None) != pieces[-1] and name != 'pk'`.

### Verification performed
1. Confirmed base_commit worktree (a59de6e8) predicate = pre-patch `...attname != name...`; created worktree at base_commit and applied the dataset gold patch, yielding the patched predicate with `pieces[-1]` and `name != 'pk'`.
2. Ran the bundle's conformance_check.py (SHADOW = model impl region verbatim, contracts stripped — which is byte-identical to the postcondition predicate; ORACLE = real patched find_ordering_name driven unbound with controlled stand-ins and a marker OrderBy to observe branch selection) against. Result: G-CONF OK, model shadow agrees with the real patched function branch selection on 100420 inputs (seed=13033), 0 disagreements.
3. Independent adversarial probe of the REAL patched find_ordering_name (correct 7-tuple _setup_joins) vs the spec predicate over hand-picked edge cases (pk shortcut, attname=None, multi-segment paths ending in the column token record__root_id/root_id, single-segment x, whole-path attname a__b, etc.): 0 mismatches. The subtle cases are all faithful: attname=None -> mode reflects vacuous inequality; multi-segment where attname==pieces[-1] -> mode 0; where attname==whole name -> mode 1 (the exact bug the patch fixes).
4. same-spec tooling confirms the model shares the bundle's exact spec (SAME).

ABSTRACTION FIDELITY: The str<->PSeq[int] code-point bijection and the attname=None -> sentinel-with-negative-entry carrier are exact for the predicate's boolean outcome. The split invariant precondition (Implies(len>1, name != terminal)) is a true theorem of str.split('__'), so it never over-constrains the real domain (conformance feeds only Requires-satisfying, real-split-derived inputs and still finds 0 disagreements). The unmodeled machinery inside each branch is unchanged by the patch and behaviour-preserving, so it is correctly out of the modeled delta.

CONCLUSION: The modeled function agrees with the real patched callee on all tested inputs (100k+ fuzz + boundary + adversarial edge cases). No diverging input found; the spec is neither too strong nor drifted. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = docstring + markers + PK()/path_terminal pure fns + ordering_mode signature/pre/post-conditions (impl elided). Lexical G-LEAK screen PASSES (no diff markers, no gold-patch line, no patched file path 'compiler.py', no patched-symbol echo, no narration). Semantic check: gold edit is a one-token operand swap `getattr(field,'attname',None) != name` -> `!= pieces[-1]` in django/db/models/sql/compiler.py:find_ordering_name. The spec view never names compiler.py, find_ordering_name, attname, is_relation, opts.ordering, or pieces; it uses only abstracted carriers (relation_own_column, points_to_relation, has_default_ordering, path_segments, path_terminal). The postcondition compares against path_terminal(path_segments) (terminal segment) rather than the whole `name` — this encodes the CORRECT behavior, but that behavior is already fully public in problem_statement, which contrasts order_by('record__root_id') (should be single-join ascending direct column, matching record__root__id) against order_by('record__root') (adopts default ordering). A faithful behavioral spec must encode the correct answer; doing so at an abstracted level does not localize or reveal the gold edit's mechanism/site beyond the public task. Localization details live only in refinement.md/mapping.md (audit docs, not the consumer spec view). No spec-view line leaks the gold edit beyond problem_statement (hints_text not considered).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
