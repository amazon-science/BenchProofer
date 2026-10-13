# P2 adversarial audit — django__django-11820

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -156,56 +156,5 @@
     Ensures(Result() == walk_err(ToSeq(path), root, root, -1))
     # post-conditions-end
     # impl-start
-    whole = walk_err(ToSeq(path), root, root, -1)  # ghost: the target value
-    n = len(path)
-    i = 0
-    acc = False
-    model = root
-    fld_model = root
-    fld_name = -1
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(path), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(path))
-        Invariant(whole == walk_err(ToSeq(path), root, root, -1))
-        Invariant(whole == (acc or walk_err(ToSeq(path).drop(i), model, fld_model, fld_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        Assert(ToSeq(path).drop(i)[0] == path[i])
-        Assert(ToSeq(path).drop(i).drop(1) == ToSeq(path).drop(i + 1))
-        name = path[i]
-        if model == -1:
-            if fld_name == -1 or not transform_present(fld_model, fld_name, name):
-                acc = True
-            # model stays -1; fld unchanged
-        elif name == 0:
-            # pk alias: the field is found on the current model.
-            fld_model = model
-            fld_name = name
-            if pk_kind(model) == 1:
-                model = pk_target(model)
-            else:
-                model = -1
-        else:
-            k = resolve_kind(model, name)
-            if k == 0:
-                if fld_name == -1 or not transform_present(fld_model, fld_name, name):
-                    acc = True
-                # model and fld unchanged
-            elif k == 1:
-                fld_model = model
-                fld_name = name
-                model = relation_target(model, name)
-            else:
-                fld_model = model
-                fld_name = name
-                model = -1
-        i = i + 1
-    Assert(len(ToSeq(path).drop(n)) == 0)
-    Assert(walk_err(ToSeq(path).drop(n), model, fld_model, fld_name) == False)
-    return acc
+    return walk_err(ToSeq(path), root, root, -1)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -163,6 +163,7 @@
     model = root
     fld_model = root
     fld_name = -1
+    Assert(ToSeq(path).drop(0) == ToSeq(path))
     while i < n:
         # invariants-start
         Invariant(Acc(list_pred(path), 1 / 2))
@@ -182,14 +183,6 @@
             if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                 acc = True
             # model stays -1; fld unchanged
-        elif name == 0:
-            # pk alias: the field is found on the current model.
-            fld_model = model
-            fld_name = name
-            if pk_kind(model) == 1:
-                model = pk_target(model)
-            else:
-                model = -1
         else:
             k = resolve_kind(model, name)
             if k == 0:
@@ -203,7 +196,7 @@
             else:
                 fld_model = model
                 fld_name = name
-                model = -1
+                # model UNCHANGED after a non-relation field
         i = i + 1
     Assert(len(ToSeq(path).drop(n)) == 0)
     Assert(walk_err(ToSeq(path).drop(n), model, fld_model, fld_name) == False)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -163,6 +163,7 @@
     model = root
     fld_model = root
     fld_name = -1
+    Assert(ToSeq(path).drop(0) == ToSeq(path))
     while i < n:
         # invariants-start
         Invariant(Acc(list_pred(path), 1 / 2))
@@ -182,15 +183,9 @@
             if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                 acc = True
             # model stays -1; fld unchanged
-        elif name == 0:
-            # pk alias: the field is found on the current model.
-            fld_model = model
-            fld_name = name
-            if pk_kind(model) == 1:
-                model = pk_target(model)
-            else:
-                model = -1
         else:
+            # NO pk alias handling: ``pk`` (name 0) is resolved as an ordinary
+            # name, which resolves to nothing.
             k = resolve_kind(model, name)
             if k == 0:
                 if fld_name == -1 or not transform_present(fld_model, fld_name, name):
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -163,6 +163,7 @@
     model = root
     fld_model = root
     fld_name = -1
+    Assert(ToSeq(path).drop(0) == ToSeq(path))
     while i < n:
         # invariants-start
         Invariant(Acc(list_pred(path), 1 / 2))
@@ -203,7 +204,7 @@
             else:
                 fld_model = model
                 fld_name = name
-                model = -1
+                # model UNCHANGED after a non-relation field
         i = i + 1
     Assert(len(ToSeq(path).drop(n)) == 0)
     Assert(walk_err(ToSeq(path).drop(n), model, fld_model, fld_name) == False)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,6 +156,8 @@
     Ensures(Result() == walk_err(ToSeq(path), root, root, -1))
     # post-conditions-end
     # impl-start
+    if len(path) == 0:
+        return True
     whole = walk_err(ToSeq(path), root, root, -1)  # ghost: the target value
     n = len(path)
     i = 0
@@ -164,26 +166,19 @@
     fld_model = root
     fld_name = -1
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(path), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(path))
         Invariant(whole == walk_err(ToSeq(path), root, root, -1))
         Invariant(whole == (acc or walk_err(ToSeq(path).drop(i), model, fld_model, fld_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         Assert(ToSeq(path).drop(i)[0] == path[i])
         Assert(ToSeq(path).drop(i).drop(1) == ToSeq(path).drop(i + 1))
         name = path[i]
         if model == -1:
             if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                 acc = True
-            # model stays -1; fld unchanged
         elif name == 0:
-            # pk alias: the field is found on the current model.
             fld_model = model
             fld_name = name
             if pk_kind(model) == 1:
@@ -195,7 +190,6 @@
             if k == 0:
                 if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                     acc = True
-                # model and fld unchanged
             elif k == 1:
                 fld_model = model
                 fld_name = name
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -163,27 +163,20 @@
     model = root
     fld_model = root
     fld_name = -1
-    while i < n:
-        # invariants-start
+    while i < n - 1:
         Invariant(Acc(list_pred(path), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(path))
         Invariant(whole == walk_err(ToSeq(path), root, root, -1))
         Invariant(whole == (acc or walk_err(ToSeq(path).drop(i), model, fld_model, fld_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         Assert(ToSeq(path).drop(i)[0] == path[i])
         Assert(ToSeq(path).drop(i).drop(1) == ToSeq(path).drop(i + 1))
         name = path[i]
         if model == -1:
             if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                 acc = True
-            # model stays -1; fld unchanged
         elif name == 0:
-            # pk alias: the field is found on the current model.
             fld_model = model
             fld_name = name
             if pk_kind(model) == 1:
@@ -195,7 +188,6 @@
             if k == 0:
                 if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                     acc = True
-                # model and fld unchanged
             elif k == 1:
                 fld_model = model
                 fld_name = name
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,26 +164,18 @@
     fld_model = root
     fld_name = -1
     while i < n:
-        # invariants-start
         Invariant(Acc(list_pred(path), 1 / 2))
         Invariant(0 <= i and i <= n)
         Invariant(n == len(path))
         Invariant(whole == walk_err(ToSeq(path), root, root, -1))
         Invariant(whole == (acc or walk_err(ToSeq(path).drop(i), model, fld_model, fld_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - i, discharging
-        # MustTerminate(2) from the precondition.
         Invariant(MustTerminate(n - i + 1))
-        # invariants-end
         Assert(ToSeq(path).drop(i)[0] == path[i])
         Assert(ToSeq(path).drop(i).drop(1) == ToSeq(path).drop(i + 1))
         name = path[i]
         if model == -1:
-            if fld_name == -1 or not transform_present(fld_model, fld_name, name):
-                acc = True
-            # model stays -1; fld unchanged
+            acc = True
         elif name == 0:
-            # pk alias: the field is found on the current model.
             fld_model = model
             fld_name = name
             if pk_kind(model) == 1:
@@ -195,7 +187,6 @@
             if k == 0:
                 if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                     acc = True
-                # model and fld unchanged
             elif k == 1:
                 fld_model = model
                 fld_name = name
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -156,56 +156,5 @@
     Ensures(Result() == walk_err(ToSeq(path), root, root, -1))
     # post-conditions-end
     # impl-start
-    whole = walk_err(ToSeq(path), root, root, -1)  # ghost: the target value
-    n = len(path)
-    i = 0
-    acc = False
-    model = root
-    fld_model = root
-    fld_name = -1
-    while i < n:
-        # invariants-start
-        Invariant(Acc(list_pred(path), 1 / 2))
-        Invariant(0 <= i and i <= n)
-        Invariant(n == len(path))
-        Invariant(whole == walk_err(ToSeq(path), root, root, -1))
-        Invariant(whole == (acc or walk_err(ToSeq(path).drop(i), model, fld_model, fld_name)))
-        # The loop consumes the caller's termination obligation with the
-        # strictly decreasing, bounded-below measure n - i, discharging
-        # MustTerminate(2) from the precondition.
-        Invariant(MustTerminate(n - i + 1))
-        # invariants-end
-        Assert(ToSeq(path).drop(i)[0] == path[i])
-        Assert(ToSeq(path).drop(i).drop(1) == ToSeq(path).drop(i + 1))
-        name = path[i]
-        if model == -1:
-            if fld_name == -1 or not transform_present(fld_model, fld_name, name):
-                acc = True
-            # model stays -1; fld unchanged
-        elif name == 0:
-            # pk alias: the field is found on the current model.
-            fld_model = model
-            fld_name = name
-            if pk_kind(model) == 1:
-                model = pk_target(model)
-            else:
-                model = -1
-        else:
-            k = resolve_kind(model, name)
-            if k == 0:
-                if fld_name == -1 or not transform_present(fld_model, fld_name, name):
-                    acc = True
-                # model and fld unchanged
-            elif k == 1:
-                fld_model = model
-                fld_name = name
-                model = relation_target(model, name)
-            else:
-                fld_model = model
-                fld_name = name
-                model = -1
-        i = i + 1
-    Assert(len(ToSeq(path).drop(n)) == 0)
-    Assert(walk_err(ToSeq(path).drop(n), model, fld_model, fld_name) == False)
-    return acc
+    return not walk_err(ToSeq(path), root, root, -1)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11820.

Behaviour under specification (stated as desired behaviour, not as an edit):

A model declares an ordering by a sequence of lookup paths.  A *related* path
is a chain of names joined by the lookup separator, e.g. ``a __ b __ c``.  The
validator walks the chain one name at a time, starting from the declaring
model, and decides whether the whole path is a legitimate ordering target (no
error) or refers to something that does not exist (one validation error).

The walk maintains a "current model" and the "last field that was found":

  * Resolving a name against the current model yields one of three outcomes:
    the name is a RELATION field (the walk advances to the related model), the
    name is an ordinary NON-RELATION field, or the name resolves to nothing on
    the current model.

  * The primary-key alias.  The literal name ``pk`` is an alias that always
    designates the current model's primary-key field (it is NOT an ordinary
    field that name-resolution would find).  So a ``pk`` step is resolved
    against the model's primary key directly, yielding that field's
    relation/non-relation kind.

  * After a name resolves to a NON-RELATION field there is no model to continue
    from: the current model becomes "none".  Any subsequent name therefore
    resolves to nothing (there is nothing to resolve it against).

  * When a name resolves to nothing, the path is in error UNLESS the last field
    that was found admits that trailing name as a registered transform (a
    registered lookup such as ``__lower``), in which case the trailing name is
    a transform of that field and the path is acceptable.

The desired result is the single boolean: does walking this related path
produce a validation error.

The model graph (which name is which kind of field on which model, the related
target, the primary-key kind/target, and which trailing transforms a field
admits) is the unchanged name-resolution machinery, modelled as referentially
transparent pure functions over integer model/name identifiers.  Names are
modelled as ``int`` identifiers (Nagini bans ``str`` indexing); the reserved
identifier ``0`` denotes the literal alias name ``pk``.  The path is a
``List[int]`` of name identifiers; the specification is carried by ``PSeq[int]``
via ``ToSeq``.

The walk itself is modelled deeply as a front-recursive fold (`walk_err`) over
the path, so a single unfold is available per loop step.

Validation is a bounded computation: the walk visits each name of the finite
path once and MUST return its verdict (a total-correctness obligation, carried
as MustTerminate in the precondition). An implementation that diverges before
returning would satisfy the value postcondition only vacuously and would never
deliver a verdict to the caller.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def resolve_kind(model: int, name: int) -> int:
    """Outcome of resolving an ordinary (non-alias) name against a model:
    0 = resolves to nothing, 1 = a relation field, 2 = a non-relation field.
    Referentially transparent (the unchanged name-resolution machinery).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(0 <= Result() and Result() <= 2)

@Pure
@ContractOnly
def relation_target(model: int, name: int) -> int:
    """The model reached after stepping through a relation field `name` of
    `model` (the unchanged related-model lookup)."""
    Ensures(Result() >= 0)

@Pure
@ContractOnly
def pk_kind(model: int) -> int:
    """Kind of a model's primary-key field: 1 = relation, 2 = non-relation.
    A model always has a primary key, so this never resolves to nothing."""
    Ensures(Result() == 1 or Result() == 2)

@Pure
@ContractOnly
def pk_target(model: int) -> int:
    """The model reached after stepping through a relational primary key."""
    Ensures(Result() >= 0)

@Pure
@ContractOnly
def transform_present(field_model: int, field_name: int, name: int) -> bool:
    """Whether the field identified by (field_model, field_name) admits `name`
    as a registered trailing transform (the unchanged transform lookup)."""
# axioms-end

# pure-start
@Pure
def walk_err(path: PSeq[int], model: int, fld_model: int, fld_name: int) -> bool:
    """Does walking the remaining `path` from `model`, having last found the
    field (fld_model, fld_name) (with fld_name == -1 meaning "no field found
    yet"), produce a validation error.  Front-recursive: peels one name.

    Reserved name identifier 0 is the primary-key alias ``pk``; model identifier
    -1 is the "none" current model (nothing left to resolve against)."""
    if len(path) == 0:
        return False
    name = path[0]
    rest = path.drop(1)
    if model == -1:
        # Nothing to resolve the name against: in error unless the last field
        # that was found admits the name as a registered transform.
        return (fld_name == -1 or not transform_present(fld_model, fld_name, name)) \
            or walk_err(rest, -1, fld_model, fld_name)
    if name == 0:
        # The ``pk`` alias resolves to the model's primary-key field directly.
        if pk_kind(model) == 1:
            return walk_err(rest, pk_target(model), model, name)
        return walk_err(rest, -1, model, name)
    k = resolve_kind(model, name)
    if k == 0:
        # Resolves to nothing: error unless rescued by a transform on the last
        # field that was found (the current name was not assigned as a field).
        return (fld_name == -1 or not transform_present(fld_model, fld_name, name)) \
            or walk_err(rest, model, fld_model, fld_name)
    if k == 1:
        return walk_err(rest, relation_target(model, name), model, name)
    # k == 2: ordinary non-relation field; no model to continue from.
    return walk_err(rest, -1, model, name)
# pure-end

def check_related_path(path: List[int], root: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(root >= 0)
    # TERMINATION: the validator must actually ANSWER — walking a finite
    # related path is a bounded computation (one step per name). Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. an endless loop before returning)
    # satisfies the value postcondition vacuously; the real validator always
    # returns its per-path verdict.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(path), 1 / 2))
    # The result is exactly the deep walk: an error iff walking the related
    # path from the root model produces one.
    Ensures(Result() == walk_err(ToSeq(path), root, root, -1))
    # post-conditions-end
    # impl-start
    whole = walk_err(ToSeq(path), root, root, -1)  # ghost: the target value
    n = len(path)
    i = 0
    acc = False
    model = root
    fld_model = root
    fld_name = -1
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(path), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(path))
        Invariant(whole == walk_err(ToSeq(path), root, root, -1))
        Invariant(whole == (acc or walk_err(ToSeq(path).drop(i), model, fld_model, fld_name)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - i, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        Assert(ToSeq(path).drop(i)[0] == path[i])
        Assert(ToSeq(path).drop(i).drop(1) == ToSeq(path).drop(i + 1))
        name = path[i]
        if model == -1:
            if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                acc = True
            # model stays -1; fld unchanged
        elif name == 0:
            # pk alias: the field is found on the current model.
            fld_model = model
            fld_name = name
            if pk_kind(model) == 1:
                model = pk_target(model)
            else:
                model = -1
        else:
            k = resolve_kind(model, name)
            if k == 0:
                if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                    acc = True
                # model and fld unchanged
            elif k == 1:
                fld_model = model
                fld_name = name
                model = relation_target(model, name)
            else:
                fld_model = model
                fld_name = name
                model = -1
        i = i + 1
    Assert(len(ToSeq(path).drop(n)) == 0)
    Assert(walk_err(ToSeq(path).drop(n), model, fld_model, fld_name) == False)
    return acc
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit of nagini bundle django__django-11820. Ran the mandatory >=5 DISTINCT wrong-impl attacks plus the echo and the prepatch bug, all same-spec byte-identical (adversary same-spec exit 0 for all 8). Each edits ONLY the impl region; axioms/@Pure/walk_err/pre-post byte-identical.

KEY SPEC OBSERVATION: the postcondition is Ensures(Result() == walk_err(ToSeq(path), root, root, -1)) -- an UNCONDITIONAL exact functional equality to the FROZEN deep fold walk_err (in the byte-identical `pure` region). Any impl that verifies must return EXACTLY walk_err, leaving no room for a verifying-but-semantically-wrong impl. Confirmed empirically.

Commands (from repo root, env, SBU_BENCHMARK_DIR=.../benchmark-verified):
  python -m swebench_unified.adversary same-spec nagini django__django-11820 <atk>  (all 8 -> exit 0, SAME)
  python -m swebench_unified.adversary weakness  nagini django__django-11820 <atk>  (run concurrently, <=3 JVM at a time)

WEAKNESS results:
- pos_control.py (= bundle model.py): VERIFIES (exit 0). Positive control good.
- atk_1.py  echo `return walk_err(ToSeq(path), root, root, -1)`: CANDIDATE (same-spec AND verifies, exit 0). This is the CORRECT post-fix semantics. Materialized its faithful refined patch = the gold post-fix patch (pk-alias branch + non-relation _cls reset) at atk_1_patch.diff and RAN it through the official harness: run_resolve("django__django-11820", patch, timeout=1800, retries=1) -> RESOLVED: True | completed: True | note: resolved | flaky: False. A resolving echo of gold is NOT a weakness (per G-CONF/G-EQ policy: candidate fails the gate only if its faithful patch does NOT resolve). So atk_1 does not break the spec.
- atk_2.py  prepatch (BOTH pre-fix behaviours; = model_prepatch.py, the literal gold pre-image): does NOT verify (exit 2). PREPATCH BUG REPRODUCED -> spec rejects the buggy impl.
- atk_3.py  no pk-alias branch (routes 'pk' through resolve_kind; = model_prepatch_1.py): does NOT verify (exit 2). Spec SENSES the pk-alias fix (refinement A4).
- atk_4.py  non-relation reset removed (model UNCHANGED after non-relation field; = model_prepatch_2.py): does NOT verify (exit 2). Spec SENSES the reset fix (refinement A7).
- atk_5.py  partial-domain: `if len(path)==0: return True` then correct loop: does NOT verify (exit 2). walk_err on empty path == False, so True is wrong; spec rejects.
- atk_6.py  boundary off-by-one: `while i < n - 1` (skips last name): does NOT verify (exit 2).
- atk_7.py  control-flow-effect: drop the transform_present rescue guard in the model==-1 branch (over-report errors): does NOT verify (exit 2).
- atk_8.py  ungrounded-oracle echo: `return not walk_err(...)` (negated fold): does NOT verify (exit 2).

No verifying wrong impl exists: the ONLY CANDIDATE (atk_1) is correct and its materialized faithful patch RESOLVED. Therefore verify does not admit an incorrect impl here.

REFINEMENT.MD AUDIT (A-legs + correspondence): legs A1-A10 are all tagged R / A-reference / I; NO kind-3 (unexpressible-changed-op) and NO A-consumed value axioms. The TWO genuinely-changed operations -- the pk-alias resolution (A4) and the post-non-relation _cls reset (A7) -- are modeled DEEPLY as explicit branches in walk_err / the impl loop (`if name==0` -> pk_kind/pk_target; `k==2` -> continue with model=-1), NOT hidden behind an axiom; this is confirmed by atk_3/atk_4 failing verification exactly when those branches are removed.

The five @ContractOnly graph functions (resolve_kind, relation_target, pk_kind, pk_target, transform_present) are A-reference: they model UNCHANGED name-resolution callees (get_field/is_relation, get_path_info, _meta.pk, get_transform); the proof consumes only their return-range Ensures for branch totality. axiom_check.py (G-AX) binds walk_err_real to the REAL Django callees and asserts, per F2P/P2P/adversarial scenario, that the deep fold's verdict == real Model._check_ordering E015 verdict (real_check_emits_e015) -- so the A-reference correspondence to the real callees holds end-to-end. mapping.md §1-3 bind each symbol to its base_commit repo counterpart consistently.

VERDICT: SOUND. >=5 distinct wrong impls (plus echo + prepatch) all run and reported; every non-echo wrong impl is REJECTED by the exact-equality postcondition; the sole verifying CANDIDATE (echo) has a faithful patch that RESOLVED under the official harness. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_1.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11820.

Behaviour under specification (stated as desired behaviour, not as an edit):

A model declares an ordering by a sequence of lookup paths.  A *related* path
is a chain of names joined by the lookup separator, e.g. ``a __ b __ c``.  The
validator walks the chain one name at a time, starting from the declaring
model, and decides whether the whole path is a legitimate ordering target (no
error) or refers to something that does not exist (one validation error).

The walk maintains a "current model" and the "last field that was found":

  * Resolving a name against the current model yields one of three outcomes:
    the name is a RELATION field (the walk advances to the related model), the
    name is an ordinary NON-RELATION field, or the name resolves to nothing on
    the current model.

  * The primary-key alias.  The literal name ``pk`` is an alias that always
    designates the current model's primary-key field (it is NOT an ordinary
    field that name-resolution would find).  So a ``pk`` step is resolved
    against the model's primary key directly, yielding that field's
    relation/non-relation kind.

  * After a name resolves to a NON-RELATION field there is no model to continue
    from: the current model becomes "none".  Any subsequent name therefore
    resolves to nothing (there is nothing to resolve it against).

  * When a name resolves to nothing, the path is in error UNLESS the last field
    that was found admits that trailing name as a registered transform (a
    registered lookup such as ``__lower``), in which case the trailing name is
    a transform of that field and the path is acceptable.

The desired result is the single boolean: does walking this related path
produce a validation error.

The model graph (which name is which kind of field on which model, the related
target, the primary-key kind/target, and which trailing transforms a field
admits) is the unchanged name-resolution machinery, modelled as referentially
transparent pure functions over integer model/name identifiers.  Names are
modelled as ``int`` identifiers (Nagini bans ``str`` indexing); the reserved
identifier ``0`` denotes the literal alias name ``pk``.  The path is a
``List[int]`` of name identifiers; the specification is carried by ``PSeq[int]``
via ``ToSeq``.

The walk itself is modelled deeply as a front-recursive fold (`walk_err`) over
the path, so a single unfold is available per loop step.

Validation is a bounded computation: the walk visits each name of the finite
path once and MUST return its verdict (a total-correctness obligation, carried
as MustTerminate in the precondition). An implementation that diverges before
returning would satisfy the value postcondition only vacuously and would never
deliver a verdict to the caller.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# axioms-start
@Pure
@ContractOnly
def resolve_kind(model: int, name: int) -> int:
    """Outcome of resolving an ordinary (non-alias) name against a model:
    0 = resolves to nothing, 1 = a relation field, 2 = a non-relation field.
    Referentially transparent (the unchanged name-resolution machinery).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(0 <= Result() and Result() <= 2)

@Pure
@ContractOnly
def relation_target(model: int, name: int) -> int:
    """The model reached after stepping through a relation field `name` of
    `model` (the unchanged related-model lookup)."""
    Ensures(Result() >= 0)

@Pure
@ContractOnly
def pk_kind(model: int) -> int:
    """Kind of a model's primary-key field: 1 = relation, 2 = non-relation.
    A model always has a primary key, so this never resolves to nothing."""
    Ensures(Result() == 1 or Result() == 2)

@Pure
@ContractOnly
def pk_target(model: int) -> int:
    """The model reached after stepping through a relational primary key."""
    Ensures(Result() >= 0)

@Pure
@ContractOnly
def transform_present(field_model: int, field_name: int, name: int) -> bool:
    """Whether the field identified by (field_model, field_name) admits `name`
    as a registered trailing transform (the unchanged transform lookup)."""
# axioms-end

# pure-start
@Pure
def walk_err(path: PSeq[int], model: int, fld_model: int, fld_name: int) -> bool:
    """Does walking the remaining `path` from `model`, having last found the
    field (fld_model, fld_name) (with fld_name == -1 meaning "no field found
    yet"), produce a validation error.  Front-recursive: peels one name.

    Reserved name identifier 0 is the primary-key alias ``pk``; model identifier
    -1 is the "none" current model (nothing left to resolve against)."""
    if len(path) == 0:
        return False
    name = path[0]
    rest = path.drop(1)
    if model == -1:
        # Nothing to resolve the name against: in error unless the last field
        # that was found admits the name as a registered transform.
        return (fld_name == -1 or not transform_present(fld_model, fld_name, name)) \
            or walk_err(rest, -1, fld_model, fld_name)
    if name == 0:
        # The ``pk`` alias resolves to the model's primary-key field directly.
        if pk_kind(model) == 1:
            return walk_err(rest, pk_target(model), model, name)
        return walk_err(rest, -1, model, name)
    k = resolve_kind(model, name)
    if k == 0:
        # Resolves to nothing: error unless rescued by a transform on the last
        # field that was found (the current name was not assigned as a field).
        return (fld_name == -1 or not transform_present(fld_model, fld_name, name)) \
            or walk_err(rest, model, fld_model, fld_name)
    if k == 1:
        return walk_err(rest, relation_target(model, name), model, name)
    # k == 2: ordinary non-relation field; no model to continue from.
    return walk_err(rest, -1, model, name)
# pure-end

def check_related_path(path: List[int], root: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(path), 1 / 2))
    Requires(root >= 0)
    # TERMINATION: the validator must actually ANSWER — walking a finite
    # related path is a bounded computation (one step per name). Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. an endless loop before returning)
    # satisfies the value postcondition vacuously; the real validator always
    # returns its per-path verdict.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(path), 1 / 2))
    # The result is exactly the deep walk: an error iff walking the related
    # path from the root model produces one.
    Ensures(Result() == walk_err(ToSeq(path), root, root, -1))
    # post-conditions-end
    # impl-start
    whole = walk_err(ToSeq(path), root, root, -1)  # ghost: the target value
    n = len(path)
    i = 0
    acc = False
    model = root
    fld_model = root
    fld_name = -1
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(path), 1 / 2))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(path))
        Invariant(whole == walk_err(ToSeq(path), root, root, -1))
        Invariant(whole == (acc or walk_err(ToSeq(path).drop(i), model, fld_model, fld_name)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure n - i, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        Assert(ToSeq(path).drop(i)[0] == path[i])
        Assert(ToSeq(path).drop(i).drop(1) == ToSeq(path).drop(i + 1))
        name = path[i]
        if model == -1:
            if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                acc = True
            # model stays -1; fld unchanged
        elif name == 0:
            # pk alias: the field is found on the current model.
            fld_model = model
            fld_name = name
            if pk_kind(model) == 1:
                model = pk_target(model)
            else:
                model = -1
        else:
            k = resolve_kind(model, name)
            if k == 0:
                if fld_name == -1 or not transform_present(fld_model, fld_name, name):
                    acc = True
                # model and fld unchanged
            elif k == 1:
                fld_model = model
                fld_name = name
                model = relation_target(model, name)
            else:
                fld_model = model
                fld_name = name
                model = -1
        i = i + 1
    Assert(len(ToSeq(path).drop(n)) == 0)
    Assert(walk_err(ToSeq(path).drop(n), model, fld_model, fld_name) == False)
    return acc
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) audit of nagini bundle django__django-11820. Ran the mandatory >=5 DISTINCT wrong-impl attacks plus the echo and the prepatch bug, all same-spec byte-identical (adversary same-spec exit 0 for all 8). Each edits ONLY the impl region; axioms/@Pure/walk_err/pre-post byte-identical.

KEY SPEC OBSERVATION: the postcondition is Ensures(Result() == walk_err(ToSeq(path), root, root, -1)) -- an UNCONDITIONAL exact functional equality to the FROZEN deep fold walk_err (in the byte-identical `pure` region). Any impl that verifies must return EXACTLY walk_err, leaving no room for a verifying-but-semantically-wrong impl. Confirmed empirically.

Commands (from repo root, env, SBU_BENCHMARK_DIR=.../benchmark-verified):
  python -m swebench_unified.adversary same-spec nagini django__django-11820 <atk>  (all 8 -> exit 0, SAME)
  python -m swebench_unified.adversary weakness  nagini django__django-11820 <atk>  (run concurrently, <=3 JVM at a time)

WEAKNESS results:
- pos_control.py (= bundle model.py): VERIFIES (exit 0). Positive control good.
- atk_1.py  echo `return walk_err(ToSeq(path), root, root, -1)`: CANDIDATE (same-spec AND verifies, exit 0). This is the CORRECT post-fix semantics. Materialized its faithful refined patch = the gold post-fix patch (pk-alias branch + non-relation _cls reset) at atk_1_patch.diff and RAN it through the official harness: run_resolve("django__django-11820", patch, timeout=1800, retries=1) -> RESOLVED: True | completed: True | note: resolved | flaky: False. A resolving echo of gold is NOT a weakness (per G-CONF/G-EQ policy: candidate fails the gate only if its faithful patch does NOT resolve). So atk_1 does not break the spec.
- atk_2.py  prepatch (BOTH pre-fix behaviours; = model_prepatch.py, the literal gold pre-image): does NOT verify (exit 2). PREPATCH BUG REPRODUCED -> spec rejects the buggy impl.
- atk_3.py  no pk-alias branch (routes 'pk' through resolve_kind; = model_prepatch_1.py): does NOT verify (exit 2). Spec SENSES the pk-alias fix (refinement A4).
- atk_4.py  non-relation reset removed (model UNCHANGED after non-relation field; = model_prepatch_2.py): does NOT verify (exit 2). Spec SENSES the reset fix (refinement A7).
- atk_5.py  partial-domain: `if len(path)==0: return True` then correct loop: does NOT verify (exit 2). walk_err on empty path == False, so True is wrong; spec rejects.
- atk_6.py  boundary off-by-one: `while i < n - 1` (skips last name): does NOT verify (exit 2).
- atk_7.py  control-flow-effect: drop the transform_present rescue guard in the model==-1 branch (over-report errors): does NOT verify (exit 2).
- atk_8.py  ungrounded-oracle echo: `return not walk_err(...)` (negated fold): does NOT verify (exit 2).

No verifying wrong impl exists: the ONLY CANDIDATE (atk_1) is correct and its materialized faithful patch RESOLVED. Therefore verify does not admit an incorrect impl here.

REFINEMENT.MD AUDIT (A-legs + correspondence): legs A1-A10 are all tagged R / A-reference / I; NO kind-3 (unexpressible-changed-op) and NO A-consumed value axioms. The TWO genuinely-changed operations -- the pk-alias resolution (A4) and the post-non-relation _cls reset (A7) -- are modeled DEEPLY as explicit branches in walk_err / the impl loop (`if name==0` -> pk_kind/pk_target; `k==2` -> continue with model=-1), NOT hidden behind an axiom; this is confirmed by atk_3/atk_4 failing verification exactly when those branches are removed.

The five @ContractOnly graph functions (resolve_kind, relation_target, pk_kind, pk_target, transform_present) are A-reference: they model UNCHANGED name-resolution callees (get_field/is_relation, get_path_info, _meta.pk, get_transform); the proof consumes only their return-range Ensures for branch totality. axiom_check.py (G-AX) binds walk_err_real to the REAL Django callees and asserts, per F2P/P2P/adversarial scenario, that the deep fold's verdict == real Model._check_ordering E015 verdict (real_check_emits_e015) -- so the A-reference correspondence to the real callees holds end-to-end. mapping.md §1-3 bind each symbol to its base_commit repo counterpart consistently.

VERDICT: SOUND. >=5 distinct wrong impls (plus echo + prepatch) all run and reported; every non-echo wrong impl is REJECTED by the exact-equality postcondition; the sole verifying CANDIDATE (echo) has a faithful patch that RESOLVED under the official harness. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-11820 nagini bundle. The spec's postcondition is Result() == walk_err(ToSeq, root, root, -1), where walk_err is a deep front-recursive fold over the related ordering path modeling the post-patch inner loop of Model._check_ordering (django/db/models/base.py:1706-1723 at base_commit c2678e49, verified against). walk_err branches: None-model (error unless last-found field admits name as transform), pk-alias (name==0 -> pk_kind/pk_target), and resolve_kind k in {0 raise, 1 relation, 2 nonrelation}, with the k==2 non-relation reset to model=-1, error-accumulation via boolean OR with state unchanged on error.

Method: reconstructed a faithful Python mirror of walk_err (branch-for-branch identical to model.py) driven by the REAL Django callees (Options.get_field/is_relation, Options.pk, get_path_info, get_transform) and compared it to the real Model._check_ordering E015 verdict.
(1) Random fuzz: 500 randomly generated model graphs (1-3 models, random Char/Int/FK/self-FK fields) with random 2-4 part related paths drawn from a pool including 'pk', field names, missing names, and transform names -> 0 mismatches.
(2) Targeted edge cases (12): CharField __lower transform rescue (no error), bad lookup (error), fk__pk (valid), fk__pk__nope (error), int __lower invalid transform (error), pk(int)__nope (error), self__self__pk (valid), pk__parent (error), rel->nonrel->part multi-hop (error), char lower->upper chain, DateField __year transform (valid) and __year__nope (error). All 12 agreed (walk==real).

The modeled function does NOT disagree with the real callee on any tested input. The abstraction points (int-id names with 0='pk', None<->-1 model, field<->(model,name) pair, transform rescue keyed on last-found field) are all reproduced correctly against real Django. The spec is neither too strong nor drifted; it is a faithful model of the real repo behavior. No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (model.py projection) passes the mechanical G-LEAK screen cleanly (leakage.screen -> passed=True, no hard failures) and my manual audit agrees. Checks: (1) No diff markers, no gold-patch line reproduced (>=8 chars normalized), no patched file path django/db/models/base.py nor dotted module path in the spec view. (2) None of the real repo symbols the gold edit touches appear anywhere in the spec view: get_field, _meta, is_relation, get_path_info, to_opts, get_transform, _cls, _check_ordering, LOOKUP_SEP, E015, options.py. The abstraction is entirely over integer model/name identifiers (resolve_kind/relation_target/pk_kind/pk_target/transform_present/walk_err). The one shared token 'part' is a generic word, not an edit locator. (3) No narration terms (bug/fix/regression/previously/used to/no longer/pre-fix, etc.) — behavior is stated as DESIRED behavior, not as an edit. Changed symbol 'check_ordering' does not appear. (4) The two discriminating fixed behaviors — the 'pk' alias resolving to the model's primary key directly (not via ordinary name resolution) and the current-model becoming 'none' after a non-relation field — are described purely as target semantics of a faithful behavioral spec. The pk-of-related-field aspect is itself already public in problem_statement (models.E015 raised when Meta.ordering contains 'pk' of a related field). Fully specifying correct behavior in a spec is not gold-reconstruction; nothing reveals the gold edit's file/lines/before-after beyond the public problem_statement. relaxed_leakage flag is unset (meta G-LEAK status 'pass'), no RELAXED_LEAKAGE.md — no panel_3 deferral applies. Judged against problem_statement only, NOT hints_text.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.