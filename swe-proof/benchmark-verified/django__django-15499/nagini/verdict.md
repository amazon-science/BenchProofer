# P2 adversarial audit — django__django-15499

**Backend:** `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # Follow-up step KIND tags (a stable integer per distinct MODELED step kind;
@@ -75,11 +74,6 @@
 
     def __init__(self, name: int, name_lower: int, fields: int, options: int,
                  bases: int, managers: int) -> None:
-        # Termination: the constructor is straight-line (six field writes, no
-        # loop, no call), so it terminates at the LOWEST level. Level 1 leaves
-        # room beneath every obligated caller (reduce_create at 6): a caller's
-        # level must be strictly greater than its callee's.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and self.name == name)
         Ensures(Acc(self.name_lower) and self.name_lower == name_lower)
         Ensures(Acc(self.fields) and self.fields == fields)
@@ -118,7 +112,6 @@
     # Domain restriction: only the two modeled facet-altering step kinds are
     # in-domain; the model states nothing about any other follow-up step kind.
     Requires(op_kind == KIND_ALTER_OPTIONS or op_kind == KIND_ALTER_MANAGERS)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(model.name, 1 / 2))
@@ -162,8 +155,5 @@
     if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
         return CreateModel(model.name, model.name_lower, model.fields,
                            op_options, model.bases, model.managers)
-    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
-        return CreateModel(model.name, model.name_lower, model.fields,
-                           model.options, model.bases, op_managers)
     return None
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # Follow-up step KIND tags (a stable integer per distinct MODELED step kind;
@@ -75,11 +74,6 @@
 
     def __init__(self, name: int, name_lower: int, fields: int, options: int,
                  bases: int, managers: int) -> None:
-        # Termination: the constructor is straight-line (six field writes, no
-        # loop, no call), so it terminates at the LOWEST level. Level 1 leaves
-        # room beneath every obligated caller (reduce_create at 6): a caller's
-        # level must be strictly greater than its callee's.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and self.name == name)
         Ensures(Acc(self.name_lower) and self.name_lower == name_lower)
         Ensures(Acc(self.fields) and self.fields == fields)
@@ -118,7 +112,6 @@
     # Domain restriction: only the two modeled facet-altering step kinds are
     # in-domain; the model states nothing about any other follow-up step kind.
     Requires(op_kind == KIND_ALTER_OPTIONS or op_kind == KIND_ALTER_MANAGERS)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(model.name, 1 / 2))
@@ -163,7 +156,7 @@
         return CreateModel(model.name, model.name_lower, model.fields,
                            op_options, model.bases, model.managers)
     elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
-        return CreateModel(model.name, model.name_lower, model.fields,
+        return CreateModel(model.name_lower, model.name_lower, model.fields,
                            model.options, model.bases, op_managers)
     return None
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # Follow-up step KIND tags (a stable integer per distinct MODELED step kind;
@@ -75,11 +74,6 @@
 
     def __init__(self, name: int, name_lower: int, fields: int, options: int,
                  bases: int, managers: int) -> None:
-        # Termination: the constructor is straight-line (six field writes, no
-        # loop, no call), so it terminates at the LOWEST level. Level 1 leaves
-        # room beneath every obligated caller (reduce_create at 6): a caller's
-        # level must be strictly greater than its callee's.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and self.name == name)
         Ensures(Acc(self.name_lower) and self.name_lower == name_lower)
         Ensures(Acc(self.fields) and self.fields == fields)
@@ -118,7 +112,6 @@
     # Domain restriction: only the two modeled facet-altering step kinds are
     # in-domain; the model states nothing about any other follow-up step kind.
     Requires(op_kind == KIND_ALTER_OPTIONS or op_kind == KIND_ALTER_MANAGERS)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(model.name, 1 / 2))
@@ -164,6 +157,6 @@
                            op_options, model.bases, model.managers)
     elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
         return CreateModel(model.name, model.name_lower, model.fields,
-                           model.options, model.bases, op_managers)
+                           model.options, model.bases, model.managers)
     return None
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # Follow-up step KIND tags (a stable integer per distinct MODELED step kind;
@@ -75,11 +74,6 @@
 
     def __init__(self, name: int, name_lower: int, fields: int, options: int,
                  bases: int, managers: int) -> None:
-        # Termination: the constructor is straight-line (six field writes, no
-        # loop, no call), so it terminates at the LOWEST level. Level 1 leaves
-        # room beneath every obligated caller (reduce_create at 6): a caller's
-        # level must be strictly greater than its callee's.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and self.name == name)
         Ensures(Acc(self.name_lower) and self.name_lower == name_lower)
         Ensures(Acc(self.fields) and self.fields == fields)
@@ -118,7 +112,6 @@
     # Domain restriction: only the two modeled facet-altering step kinds are
     # in-domain; the model states nothing about any other follow-up step kind.
     Requires(op_kind == KIND_ALTER_OPTIONS or op_kind == KIND_ALTER_MANAGERS)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(model.name, 1 / 2))
@@ -161,7 +154,7 @@
     # impl-start
     if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
         return CreateModel(model.name, model.name_lower, model.fields,
-                           op_options, model.bases, model.managers)
+                           model.options, model.bases, model.managers)
     elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
         return CreateModel(model.name, model.name_lower, model.fields,
                            model.options, model.bases, op_managers)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # Follow-up step KIND tags (a stable integer per distinct MODELED step kind;
@@ -75,11 +74,6 @@
 
     def __init__(self, name: int, name_lower: int, fields: int, options: int,
                  bases: int, managers: int) -> None:
-        # Termination: the constructor is straight-line (six field writes, no
-        # loop, no call), so it terminates at the LOWEST level. Level 1 leaves
-        # room beneath every obligated caller (reduce_create at 6): a caller's
-        # level must be strictly greater than its callee's.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and self.name == name)
         Ensures(Acc(self.name_lower) and self.name_lower == name_lower)
         Ensures(Acc(self.fields) and self.fields == fields)
@@ -118,7 +112,6 @@
     # Domain restriction: only the two modeled facet-altering step kinds are
     # in-domain; the model states nothing about any other follow-up step kind.
     Requires(op_kind == KIND_ALTER_OPTIONS or op_kind == KIND_ALTER_MANAGERS)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(model.name, 1 / 2))
@@ -159,11 +152,9 @@
                     and Result().options == model.options))
     # post-conditions-end
     # impl-start
-    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
+    if op_kind == KIND_ALTER_OPTIONS:
         return CreateModel(model.name, model.name_lower, model.fields,
                            op_options, model.bases, model.managers)
-    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
-        return CreateModel(model.name, model.name_lower, model.fields,
-                           model.options, model.bases, op_managers)
-    return None
+    return CreateModel(model.name, model.name_lower, model.fields,
+                       model.options, model.bases, op_managers)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # Follow-up step KIND tags (a stable integer per distinct MODELED step kind;
@@ -75,11 +74,6 @@
 
     def __init__(self, name: int, name_lower: int, fields: int, options: int,
                  bases: int, managers: int) -> None:
-        # Termination: the constructor is straight-line (six field writes, no
-        # loop, no call), so it terminates at the LOWEST level. Level 1 leaves
-        # room beneath every obligated caller (reduce_create at 6): a caller's
-        # level must be strictly greater than its callee's.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and self.name == name)
         Ensures(Acc(self.name_lower) and self.name_lower == name_lower)
         Ensures(Acc(self.fields) and self.fields == fields)
@@ -118,7 +112,6 @@
     # Domain restriction: only the two modeled facet-altering step kinds are
     # in-domain; the model states nothing about any other follow-up step kind.
     Requires(op_kind == KIND_ALTER_OPTIONS or op_kind == KIND_ALTER_MANAGERS)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(model.name, 1 / 2))
@@ -164,6 +157,6 @@
                            op_options, model.bases, model.managers)
     elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
         return CreateModel(model.name, model.name_lower, model.fields,
-                           model.options, model.bases, op_managers)
+                           op_managers, model.bases, model.options)
     return None
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,7 +54,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # Follow-up step KIND tags (a stable integer per distinct MODELED step kind;
@@ -75,11 +74,6 @@
 
     def __init__(self, name: int, name_lower: int, fields: int, options: int,
                  bases: int, managers: int) -> None:
-        # Termination: the constructor is straight-line (six field writes, no
-        # loop, no call), so it terminates at the LOWEST level. Level 1 leaves
-        # room beneath every obligated caller (reduce_create at 6): a caller's
-        # level must be strictly greater than its callee's.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.name) and self.name == name)
         Ensures(Acc(self.name_lower) and self.name_lower == name_lower)
         Ensures(Acc(self.fields) and self.fields == fields)
@@ -118,7 +112,6 @@
     # Domain restriction: only the two modeled facet-altering step kinds are
     # in-domain; the model states nothing about any other follow-up step kind.
     Requires(op_kind == KIND_ALTER_OPTIONS or op_kind == KIND_ALTER_MANAGERS)
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(model.name, 1 / 2))
@@ -159,11 +152,14 @@
                     and Result().options == model.options))
     # post-conditions-end
     # impl-start
-    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
+    if op_name == model.name_lower:
+        if op_kind == KIND_ALTER_MANAGERS:
+            new_managers = op_managers
+            new_options = model.options
+        else:
+            new_managers = model.managers
+            new_options = op_options
         return CreateModel(model.name, model.name_lower, model.fields,
-                           op_options, model.bases, model.managers)
-    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
-        return CreateModel(model.name, model.name_lower, model.fields,
-                           model.options, model.bases, op_managers)
+                           new_options, model.bases, new_managers)
     return None
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15499.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A model-creation step may be followed, during optimisation, by a step that
  alters one facet of that same model. When the follow-up step targets the very
  model just created (the two steps name the same model), the optimiser folds
  the pair into a single creation step that already carries the altered facet —
  there is no remaining need for a separate alter step.

  Two such facets are pinned here, each with its OWN folding rule:

    * a step that alters the model's declarative *option set* folds in by
      carrying the altered option set forward while every other facet (the
      collection of *managers*, the field list, the inheritance bases) is taken
      unchanged from the creation step;

    * a step that alters the model's collection of *managers* folds in
      SYMMETRICALLY: the resulting creation step carries the altered manager
      collection forward, while every other facet (the option set, the field
      list, the inheritance bases) is taken unchanged from the creation step.

  Name handling is two-sided and load-bearing. A created model carries BOTH a
  *display name* (the name as declared, case preserved) and a *lower-cased
  comparison key* derived from it; the follow-up step targets a model via the
  lower-cased key only. Whether the two steps name the same model is decided by
  comparing the follow-up step's key with the creation step's key — but the
  folded creation step keeps the creation step's DISPLAY name verbatim (case
  preserved), never the lower-cased key. When the follow-up step's key does NOT
  match the creation step's key, no folding occurs by these rules and the pair
  is left for later passes.

  MODELED SLICE: only the two facet-altering follow-up kinds above are within
  this model's domain. Every other follow-up step kind is dispatched to its own
  reduction rule elsewhere in the optimiser (each with its own folding
  behaviour) and is deliberately OUTSIDE the modeled slice — this model states
  nothing about those kinds.

Each model facet is modelled by an integer token (two facet values are the
"same" iff their tokens are equal); the created model is a minimal object
exposing only the touched facets (display name, lower-cased name key, field
list, option set, bases, manager collection). The display name and the
lower-cased key are DISTINCT tokens in general (they are different string
values whenever the declared name contains an upper-case letter). The incoming
follow-up step is modelled by an integer KIND tag (one of the two modeled
kinds, per the domain restriction above) plus the lower-cased name key it
targets and the facet token it would install. The optimiser outcome is
`Optional[CreateModel]`: a folded single creation step when the pair collapses,
otherwise the null token (the pair is not folded by these rules).

No callee is axiomatized: the folding is pure structural selection over the
two steps' own fields, modelled deeply. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

# Follow-up step KIND tags (a stable integer per distinct MODELED step kind;
# the precondition restricts the domain to exactly these two — any other step
# kind has its own reduction rule and is outside the modeled slice):
#   0 — alters the model's option set
#   1 — alters the model's manager collection
KIND_ALTER_OPTIONS = 0
KIND_ALTER_MANAGERS = 1

class CreateModel:
    """A model-creation step exposing only the touched facets, each an integer
    token: `name` (the display name, case preserved), `name_lower` (the
    lower-cased comparison key derived from the display name), `fields` (field
    list), `options` (option set), `bases` (inheritance bases), `managers`
    (manager collection)."""

    def __init__(self, name: int, name_lower: int, fields: int, options: int,
                 bases: int, managers: int) -> None:
        Ensures(Acc(self.name) and self.name == name)
        Ensures(Acc(self.name_lower) and self.name_lower == name_lower)
        Ensures(Acc(self.fields) and self.fields == fields)
        Ensures(Acc(self.options) and self.options == options)
        Ensures(Acc(self.bases) and self.bases == bases)
        Ensures(Acc(self.managers) and self.managers == managers)
        self.name = name  # type: int
        self.name_lower = name_lower  # type: int
        self.fields = fields  # type: int
        self.options = options  # type: int
        self.bases = bases  # type: int
        self.managers = managers  # type: int

# axioms-start
# axioms-end

# pure-start
# (no module-level pure helpers required: the folding decision is stated inline
# over the integer facet tokens and the step KIND tag.)
# pure-end

def reduce_create(model: CreateModel, op_kind: int, op_name: int,
                  op_options: int, op_managers: int) -> Optional[CreateModel]:
    # pre-conditions-start
    # The creation step is read-only (folding never mutates the input step):
    # fractional permission, required AND ensured (directive 5).
    Requires(Acc(model.name, 1 / 2))
    Requires(Acc(model.name_lower, 1 / 2))
    Requires(Acc(model.fields, 1 / 2))
    Requires(Acc(model.options, 1 / 2))
    Requires(Acc(model.bases, 1 / 2))
    Requires(Acc(model.managers, 1 / 2))
    # Domain restriction: only the two modeled facet-altering step kinds are
    # in-domain; the model states nothing about any other follow-up step kind.
    Requires(op_kind == KIND_ALTER_OPTIONS or op_kind == KIND_ALTER_MANAGERS)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(model.name, 1 / 2))
    Ensures(Acc(model.name_lower, 1 / 2))
    Ensures(Acc(model.fields, 1 / 2))
    Ensures(Acc(model.options, 1 / 2))
    Ensures(Acc(model.bases, 1 / 2))
    Ensures(Acc(model.managers, 1 / 2))
    # Folding happens EXACTLY when the follow-up step's lower-cased name key
    # matches the creation step's lower-cased key (both in-domain kinds fold on
    # a key match). Otherwise these rules leave the pair unfolded (null token).
    Ensures(Implies(Result() is not None, op_name == model.name_lower))
    Ensures(Implies(op_name == model.name_lower, Result() is not None))
    # A folded step is a creation step that keeps the original model's DISPLAY
    # name verbatim (case preserved) — NOT the lower-cased comparison key —
    # and the same derived lower-cased key.
    Ensures(Implies(Result() is not None, Acc(Result().name)))
    Ensures(Implies(Result() is not None, Acc(Result().name_lower)))
    Ensures(Implies(Result() is not None, Acc(Result().fields)))
    Ensures(Implies(Result() is not None, Acc(Result().options)))
    Ensures(Implies(Result() is not None, Acc(Result().bases)))
    Ensures(Implies(Result() is not None, Acc(Result().managers)))
    Ensures(Implies(Result() is not None, Result().name == model.name))
    Ensures(Implies(Result() is not None, Result().name_lower == model.name_lower))
    # The field list and the inheritance bases are ALWAYS carried unchanged from
    # the creation step (neither facet-altering kind touches them).
    Ensures(Implies(Result() is not None, Result().fields == model.fields))
    Ensures(Implies(Result() is not None, Result().bases == model.bases))
    # Option-alter folding: the altered option set is carried forward; the
    # manager collection is taken unchanged from the creation step.
    Ensures(Implies(Result() is not None and op_kind == KIND_ALTER_OPTIONS,
                    Result().options == op_options
                    and Result().managers == model.managers))
    # Manager-alter folding (symmetric): the altered manager collection is
    # carried forward; the option set is taken unchanged from the creation step.
    Ensures(Implies(Result() is not None and op_kind == KIND_ALTER_MANAGERS,
                    Result().managers == op_managers
                    and Result().options == model.options))
    # post-conditions-end
    # impl-start
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** The spec is a COMPLETE functional specification over its restricted domain (op_kind in {0,1}): both fold branches pin all six output facets exactly (name==model.name display-name, name_lower==model.name_lower, fields==model.fields, bases==model.bases; option-branch options==op_options & managers==model.managers; manager-branch managers==op_managers & options==model.options) plus a two-directional iff on the fold decision (Result()!=None <=> op_name==model.name_lower). No degrees of freedom are left un-pinned within the domain, so any verifying impl is behaviorally the gold on the modeled slice.

**A-LEG AUDIT:** the `# axioms-start/# axioms-end` region is EMPTY (verified). refinement.md §C and mapping.md §3 correctly declare NO @ContractOnly axioms — A-legs are legitimately vacuous, nothing to over-approximate. All refinement legs A1-A4 are R or R+I (no kind-3). A1 is load-bearing: display-name and lower-cased key are modeled as DISTINCT integer tokens; atk_2 (installs model.name_lower into the folded op's name slot — the recorded historical G-EQ break, the 'foo' vs 'Foo' bug) was REJECTED by the spec, confirming the two-token modeling is sound and load-bearing. axiom_check.py exercises the REAL CreateModel.reduce over real CreateModel/AlterModelManagers/AlterModelOptions (in-domain Django code, no third-party callee) — correspondence to the gold hunk holds slot-for-slot; sound in-domain G-AX artifact.

### ATTACKS (all same-spec confirmed via `adversary same-spec`, exit 0; weakness runs concurrently in batches of 3, JVM+Z3 each):
- atk_1 (prepatch bug, manager branch absent -> None): weakness exit=2 NOT-A-COUNTEREXAMPLE, does not verify. Reproduces the documented prepatch failure (postcondition Implies(op_name==model.name_lower, Result()!=None) violated). prepatch_reproduced=true.
- atk_2 (name<-name_lower swap in manager branch; historical 'foo' bug): weakness exit=2, does not verify (Result().name==model.name violated).
- atk_3 (manager branch keeps model.managers, drops altered managers): weakness exit=2, does not verify (manager-branch managers==op_managers violated).
- atk_4 (option branch installs model.options not op_options): weakness exit=2, does not verify (option-branch options==op_options violated).
- atk_5 (control-flow: always fold, ignores key match): weakness exit=2, does not verify (Implies(Result()!=None, op_name==model.name_lower) violated).
- atk_6 (swap options/managers slots in manager branch): weakness exit=2, does not verify.
- atk_7 (ECHO of gold: unified guard, dispatch facet by kind — behaviorally identical to gold over the modeled domain): weakness exit=0 CANDIDATE (shares spec AND verifies). Per protocol materialized its faithful refined patch (= the gold hunk adding the AlterModelManagers fold branch; the AlterModelOptions branch already realizes the option fold) and RAN it through the official harness: run_resolve('django__django-15499', patch) -> completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. A RESOLVING echo is NOT a weakness (G-CONF/G-EQ echo policy) — does not break the spec.

**Positive control:** pos_control.py = bundle model.py verbatim, `bash scripts/nagini_verify.sh` -> Verification successful (11.4s), exit 0.

### Commands
- python -m swebench_unified.adversary same-spec nagini django__django-15499 atk_N.py  (all exit 0)
- python -m swebench_unified.adversary weakness nagini django__django-15499 atk_N.py    (atk_1..6 exit 2; atk_7 exit 0)
- bash scripts/nagini_verify.sh pos_control.py  (exit 0)
- python -c 'from swebench_unified.harness import run_resolve; ...' on patch_atk7.diff -> resolved=True

Every attack fully verified and reported; no verifying wrong-impl's faithful patch failed to resolve. The single verifying candidate (atk_7) is a gold-equivalent echo whose patch resolves. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15499.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A model-creation step may be followed, during optimisation, by a step that
  alters one facet of that same model. When the follow-up step targets the very
  model just created (the two steps name the same model), the optimiser folds
  the pair into a single creation step that already carries the altered facet —
  there is no remaining need for a separate alter step.

  Two such facets are pinned here, each with its OWN folding rule:

    * a step that alters the model's declarative *option set* folds in by
      carrying the altered option set forward while every other facet (the
      collection of *managers*, the field list, the inheritance bases) is taken
      unchanged from the creation step;

    * a step that alters the model's collection of *managers* folds in
      SYMMETRICALLY: the resulting creation step carries the altered manager
      collection forward, while every other facet (the option set, the field
      list, the inheritance bases) is taken unchanged from the creation step.

  Name handling is two-sided and load-bearing. A created model carries BOTH a
  *display name* (the name as declared, case preserved) and a *lower-cased
  comparison key* derived from it; the follow-up step targets a model via the
  lower-cased key only. Whether the two steps name the same model is decided by
  comparing the follow-up step's key with the creation step's key — but the
  folded creation step keeps the creation step's DISPLAY name verbatim (case
  preserved), never the lower-cased key. When the follow-up step's key does NOT
  match the creation step's key, no folding occurs by these rules and the pair
  is left for later passes.

  MODELED SLICE: only the two facet-altering follow-up kinds above are within
  this model's domain. Every other follow-up step kind is dispatched to its own
  reduction rule elsewhere in the optimiser (each with its own folding
  behaviour) and is deliberately OUTSIDE the modeled slice — this model states
  nothing about those kinds.

Each model facet is modelled by an integer token (two facet values are the
"same" iff their tokens are equal); the created model is a minimal object
exposing only the touched facets (display name, lower-cased name key, field
list, option set, bases, manager collection). The display name and the
lower-cased key are DISTINCT tokens in general (they are different string
values whenever the declared name contains an upper-case letter). The incoming
follow-up step is modelled by an integer KIND tag (one of the two modeled
kinds, per the domain restriction above) plus the lower-cased name key it
targets and the facet token it would install. The optimiser outcome is
`Optional[CreateModel]`: a folded single creation step when the pair collapses,
otherwise the null token (the pair is not folded by these rules).

No callee is axiomatized: the folding is pure structural selection over the
two steps' own fields, modelled deeply. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

# Follow-up step KIND tags (a stable integer per distinct MODELED step kind;
# the precondition restricts the domain to exactly these two — any other step
# kind has its own reduction rule and is outside the modeled slice):
#   0 — alters the model's option set
#   1 — alters the model's manager collection
KIND_ALTER_OPTIONS = 0
KIND_ALTER_MANAGERS = 1

class CreateModel:
    """A model-creation step exposing only the touched facets, each an integer
    token: `name` (the display name, case preserved), `name_lower` (the
    lower-cased comparison key derived from the display name), `fields` (field
    list), `options` (option set), `bases` (inheritance bases), `managers`
    (manager collection)."""

    def __init__(self, name: int, name_lower: int, fields: int, options: int,
                 bases: int, managers: int) -> None:
        Ensures(Acc(self.name) and self.name == name)
        Ensures(Acc(self.name_lower) and self.name_lower == name_lower)
        Ensures(Acc(self.fields) and self.fields == fields)
        Ensures(Acc(self.options) and self.options == options)
        Ensures(Acc(self.bases) and self.bases == bases)
        Ensures(Acc(self.managers) and self.managers == managers)
        self.name = name  # type: int
        self.name_lower = name_lower  # type: int
        self.fields = fields  # type: int
        self.options = options  # type: int
        self.bases = bases  # type: int
        self.managers = managers  # type: int

# axioms-start
# axioms-end

# pure-start
# (no module-level pure helpers required: the folding decision is stated inline
# over the integer facet tokens and the step KIND tag.)
# pure-end

def reduce_create(model: CreateModel, op_kind: int, op_name: int,
                  op_options: int, op_managers: int) -> Optional[CreateModel]:
    # pre-conditions-start
    # The creation step is read-only (folding never mutates the input step):
    # fractional permission, required AND ensured (directive 5).
    Requires(Acc(model.name, 1 / 2))
    Requires(Acc(model.name_lower, 1 / 2))
    Requires(Acc(model.fields, 1 / 2))
    Requires(Acc(model.options, 1 / 2))
    Requires(Acc(model.bases, 1 / 2))
    Requires(Acc(model.managers, 1 / 2))
    # Domain restriction: only the two modeled facet-altering step kinds are
    # in-domain; the model states nothing about any other follow-up step kind.
    Requires(op_kind == KIND_ALTER_OPTIONS or op_kind == KIND_ALTER_MANAGERS)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(model.name, 1 / 2))
    Ensures(Acc(model.name_lower, 1 / 2))
    Ensures(Acc(model.fields, 1 / 2))
    Ensures(Acc(model.options, 1 / 2))
    Ensures(Acc(model.bases, 1 / 2))
    Ensures(Acc(model.managers, 1 / 2))
    # Folding happens EXACTLY when the follow-up step's lower-cased name key
    # matches the creation step's lower-cased key (both in-domain kinds fold on
    # a key match). Otherwise these rules leave the pair unfolded (null token).
    Ensures(Implies(Result() is not None, op_name == model.name_lower))
    Ensures(Implies(op_name == model.name_lower, Result() is not None))
    # A folded step is a creation step that keeps the original model's DISPLAY
    # name verbatim (case preserved) — NOT the lower-cased comparison key —
    # and the same derived lower-cased key.
    Ensures(Implies(Result() is not None, Acc(Result().name)))
    Ensures(Implies(Result() is not None, Acc(Result().name_lower)))
    Ensures(Implies(Result() is not None, Acc(Result().fields)))
    Ensures(Implies(Result() is not None, Acc(Result().options)))
    Ensures(Implies(Result() is not None, Acc(Result().bases)))
    Ensures(Implies(Result() is not None, Acc(Result().managers)))
    Ensures(Implies(Result() is not None, Result().name == model.name))
    Ensures(Implies(Result() is not None, Result().name_lower == model.name_lower))
    # The field list and the inheritance bases are ALWAYS carried unchanged from
    # the creation step (neither facet-altering kind touches them).
    Ensures(Implies(Result() is not None, Result().fields == model.fields))
    Ensures(Implies(Result() is not None, Result().bases == model.bases))
    # Option-alter folding: the altered option set is carried forward; the
    # manager collection is taken unchanged from the creation step.
    Ensures(Implies(Result() is not None and op_kind == KIND_ALTER_OPTIONS,
                    Result().options == op_options
                    and Result().managers == model.managers))
    # Manager-alter folding (symmetric): the altered manager collection is
    # carried forward; the option set is taken unchanged from the creation step.
    Ensures(Implies(Result() is not None and op_kind == KIND_ALTER_MANAGERS,
                    Result().managers == op_managers
                    and Result().options == model.options))
    # post-conditions-end
    # impl-start
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** The spec is a COMPLETE functional specification over its restricted domain (op_kind in {0,1}): both fold branches pin all six output facets exactly (name==model.name display-name, name_lower==model.name_lower, fields==model.fields, bases==model.bases; option-branch options==op_options & managers==model.managers; manager-branch managers==op_managers & options==model.options) plus a two-directional iff on the fold decision (Result()!=None <=> op_name==model.name_lower). No degrees of freedom are left un-pinned within the domain, so any verifying impl is behaviorally the gold on the modeled slice.

**A-LEG AUDIT:** the `# axioms-start/# axioms-end` region is EMPTY (verified). refinement.md §C and mapping.md §3 correctly declare NO @ContractOnly axioms — A-legs are legitimately vacuous, nothing to over-approximate. All refinement legs A1-A4 are R or R+I (no kind-3). A1 is load-bearing: display-name and lower-cased key are modeled as DISTINCT integer tokens; atk_2 (installs model.name_lower into the folded op's name slot — the recorded historical G-EQ break, the 'foo' vs 'Foo' bug) was REJECTED by the spec, confirming the two-token modeling is sound and load-bearing. axiom_check.py exercises the REAL CreateModel.reduce over real CreateModel/AlterModelManagers/AlterModelOptions (in-domain Django code, no third-party callee) — correspondence to the gold hunk holds slot-for-slot; sound in-domain G-AX artifact.

### ATTACKS (all same-spec confirmed via `adversary same-spec`, exit 0; weakness runs concurrently in batches of 3, JVM+Z3 each):
- atk_1 (prepatch bug, manager branch absent -> None): weakness exit=2 NOT-A-COUNTEREXAMPLE, does not verify. Reproduces the documented prepatch failure (postcondition Implies(op_name==model.name_lower, Result()!=None) violated). prepatch_reproduced=true.
- atk_2 (name<-name_lower swap in manager branch; historical 'foo' bug): weakness exit=2, does not verify (Result().name==model.name violated).
- atk_3 (manager branch keeps model.managers, drops altered managers): weakness exit=2, does not verify (manager-branch managers==op_managers violated).
- atk_4 (option branch installs model.options not op_options): weakness exit=2, does not verify (option-branch options==op_options violated).
- atk_5 (control-flow: always fold, ignores key match): weakness exit=2, does not verify (Implies(Result()!=None, op_name==model.name_lower) violated).
- atk_6 (swap options/managers slots in manager branch): weakness exit=2, does not verify.
- atk_7 (ECHO of gold: unified guard, dispatch facet by kind — behaviorally identical to gold over the modeled domain): weakness exit=0 CANDIDATE (shares spec AND verifies). Per protocol materialized its faithful refined patch (= the gold hunk adding the AlterModelManagers fold branch; the AlterModelOptions branch already realizes the option fold) and RAN it through the official harness: run_resolve('django__django-15499', patch) -> completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. A RESOLVING echo is NOT a weakness (G-CONF/G-EQ echo policy) — does not break the spec.

**Positive control:** pos_control.py = bundle model.py verbatim, `bash scripts/nagini_verify.sh` -> Verification successful (11.4s), exit 0.

### Commands
- python -m swebench_unified.adversary same-spec nagini django__django-15499 atk_N.py  (all exit 0)
- python -m swebench_unified.adversary weakness nagini django__django-15499 atk_N.py    (atk_1..6 exit 2; atk_7 exit 0)
- bash scripts/nagini_verify.sh pos_control.py  (exit 0)
- python -c 'from swebench_unified.harness import run_resolve; ...' on patch_atk7.diff -> resolved=True

Every attack fully verified and reported; no verifying wrong-impl's faithful patch failed to resolve. The single verifying candidate (atk_7) is a gold-equivalent echo whose patch resolves. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for nagini django__django-15499. The modeled reduce_create abstracts CreateModel.reduce over the precondition-restricted domain {KIND_ALTER_OPTIONS=0, KIND_ALTER_MANAGERS=1}. Verified against the real gold-patched repo (base_commit d90e34c) on every in-domain scenario, no divergence found:
(1) same-name AlterModelManagers -> real returns single CreateModel with alter's managers, name/fields/options/bases from creation step == spec A3.

(2) same-name AlterModelOptions -> real returns single CreateModel with merged+ALTER_OPTION_KEYS-filtered options, managers unchanged; spec models the merged result as the free op_options token (mapping.md S2 documents op_options as the post-merge value, NOT raw operation.options), pinning only options==op_options & managers==model.options. Sound R-refinement.

(3) differing name (both kinds) -> real returns boolean True ('can optimize across'), correctly abstracted to the null token; spec iff (Result()!=None <-> op_name==model.name_lower) holds.

(4) display name is case-preserved (self.name 'Foo', not self.name_lower 'foo'); the two-token modeling (name vs name_lower distinct) matches the real attributes and is exercised case-sensitively by axiom_check.
Supporting facts: nagini_verify.sh on model.py -> Verification successful (10.42s); axiom_check.py against the real Django code -> exit 0 (G-AX OK); same-spec toolkit self-check -> SAME. The domain restriction is honest (all other operation kinds are excluded by Requires, not over-claimed). No spec-too-strong / drift defect: spec is FAITHFUL, gate PASSES.

(1) same-name AlterModelManagers -> real returns single CreateModel with alter's managers, name/fields/options/bases from creation step == spec A3.

(2) same-name AlterModelOptions -> real returns single CreateModel with merged+ALTER_OPTION_KEYS-filtered options, managers unchanged; spec models the merged result as the free op_options token (mapping.md S2 documents op_options as the post-merge value, NOT raw operation.options), pinning only options==op_options & managers==model.options. Sound R-refinement.

(3) differing name (both kinds) -> real returns boolean True ('can optimize across'), correctly abstracted to the null token; spec iff (Result()!=None <-> op_name==model.name_lower) holds.

(4) display name is case-preserved (self.name 'Foo', not self.name_lower 'foo'); the two-token modeling (name vs name_lower distinct) matches the real attributes and is exercised case-sensitively by axiom_check.
Supporting facts: nagini_verify.sh on model.py -> Verification successful (10.42s); axiom_check.py against the real Django code -> exit 0 (G-AX OK); same-spec toolkit self-check -> SAME. The domain restriction is honest (all other operation kinds are excluded by Requires, not over-claimed). No spec-too-strong / drift defect: spec is FAITHFUL, gate PASSES.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (no diff markers, no reproduced gold line, no patched file path/module, no patched-symbol echo, no narration). Semantic judgment: the spec view discloses nothing about the gold edit beyond the public problem_statement.

The public problem_statement already states verbatim: 'Optimize CreateModel + AlterModelManagers to CreateModel' and 'CreateModel + AlterModelOptions is reduced to just CreateModel, with the model options. Similarly, CreateModel + AlterModelManagers can become just CreateModel.' So the entire target behavior — the CreateModel+AlterModelManagers fold and its symmetry with the pre-existing AlterModelOptions fold — is public.

The spec view (model.py docstring + Nagini contracts) describes that same desired behavior, framed explicitly 'as desired behaviour, not as an edit.' Additional detail it carries is faithful behavioral specification, not edit-localization:
- display-name vs lower-cased comparison key (name/name_lower): this is pre-existing repo behavior of self.name/self.name_lower used by BOTH the old options branch and the new managers branch; it describes how the optimiser behaves, not what line was changed.
- the options-fold branch (KIND_ALTER_OPTIONS) is pre-existing code (models.py:156-172), modeled for spec tightness — not the gold change.
- the MODELED-SLICE / domain restriction states what is out of scope; it does not point at the added branch.

No file path (django/db/migrations/operations/models.py), no diff hunk, no 'newly added'/'pre-patch'/'fix' framing, no pre/post-patch contrast appears in the spec view. The only distinctive patched def-symbol, 'reduce', is already public via the problem statement's 'reduced', so 'reduce_create' does not leak. The spec is co-extensive with what the task already discloses. No single line hands over patch-specific localization beyond problem_statement (hints_text not considered per policy).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.