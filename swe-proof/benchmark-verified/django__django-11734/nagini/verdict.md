# P2 adversarial audit — django__django-11734

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -122,7 +121,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() >= 0)
@@ -138,10 +136,9 @@
     if rhs_kind == kind_value():
         return 0
     if rhs_kind == kind_local():
-        # level +1 in inner must become level 0 -> one outward hop.
         return 1
-    # OuterRef: level 0 in inner must become level -1 -> one outward hop.
-    return 1
+    # BUG: OuterRef carried into inner subquery unchanged, no extra hop.
+    return 0
     # impl-end
 
 
@@ -153,7 +150,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Normalise iff the right-hand side is NOT a query expression.
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -122,7 +121,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() >= 0)
@@ -153,7 +151,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Normalise iff the right-hand side is NOT a query expression.
@@ -163,5 +160,5 @@
     Ensures(Result() == (rhs_kind == kind_value()))
     # post-conditions-end
     # impl-start
-    return not is_query_expression(rhs_kind)
+    return True
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -122,7 +121,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() >= 0)
@@ -136,11 +134,9 @@
     # post-conditions-end
     # impl-start
     if rhs_kind == kind_value():
-        return 0
+        return 1
     if rhs_kind == kind_local():
-        # level +1 in inner must become level 0 -> one outward hop.
         return 1
-    # OuterRef: level 0 in inner must become level -1 -> one outward hop.
     return 1
     # impl-end
 
@@ -153,7 +149,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Normalise iff the right-hand side is NOT a query expression.
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -122,7 +121,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() >= 0)
@@ -138,10 +136,9 @@
     if rhs_kind == kind_value():
         return 0
     if rhs_kind == kind_local():
-        # level +1 in inner must become level 0 -> one outward hop.
         return 1
-    # OuterRef: level 0 in inner must become level -1 -> one outward hop.
-    return 1
+    # over-anchored: two outward hops
+    return 2
     # impl-end
 
 
@@ -153,7 +150,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Normalise iff the right-hand side is NOT a query expression.
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -122,7 +121,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() >= 0)
@@ -153,7 +151,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Normalise iff the right-hand side is NOT a query expression.
@@ -163,5 +160,5 @@
     Ensures(Result() == (rhs_kind == kind_value()))
     # post-conditions-end
     # impl-start
-    return not is_query_expression(rhs_kind)
+    return is_query_expression(rhs_kind)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -122,7 +121,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() >= 0)
@@ -153,7 +151,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Normalise iff the right-hand side is NOT a query expression.
@@ -163,5 +160,5 @@
     Ensures(Result() == (rhs_kind == kind_value()))
     # post-conditions-end
     # impl-start
-    return not is_query_expression(rhs_kind)
+    return False
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -122,7 +121,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() >= 0)
@@ -137,11 +135,7 @@
     # impl-start
     if rhs_kind == kind_value():
         return 0
-    if rhs_kind == kind_local():
-        # level +1 in inner must become level 0 -> one outward hop.
-        return 1
-    # OuterRef: level 0 in inner must become level -1 -> one outward hop.
-    return 1
+    return 0
     # impl-end
 
 
@@ -153,7 +147,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Normalise iff the right-hand side is NOT a query expression.
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -122,7 +121,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() >= 0)
@@ -135,13 +133,10 @@
                     resolved_level_in_inner(rhs_kind) - Result() == target_level(rhs_kind)))
     # post-conditions-end
     # impl-start
-    if rhs_kind == kind_value():
-        return 0
-    if rhs_kind == kind_local():
-        # level +1 in inner must become level 0 -> one outward hop.
-        return 1
-    # OuterRef: level 0 in inner must become level -1 -> one outward hop.
-    return 1
+    lvl = target_level(rhs_kind)
+    if lvl < 0:
+        return -lvl
+    return lvl
     # impl-end
 
 
@@ -153,7 +148,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Normalise iff the right-hand side is NOT a query expression.
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -42,7 +42,6 @@
 Markers (machine-parsed) delimit the spec / proof / impl regions.
 """
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -122,7 +121,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Result() >= 0)
@@ -135,13 +133,7 @@
                     resolved_level_in_inner(rhs_kind) - Result() == target_level(rhs_kind)))
     # post-conditions-end
     # impl-start
-    if rhs_kind == kind_value():
-        return 0
-    if rhs_kind == kind_local():
-        # level +1 in inner must become level 0 -> one outward hop.
-        return 1
-    # OuterRef: level 0 in inner must become level -1 -> one outward hop.
-    return 1
+    return resolved_level_in_inner(rhs_kind) - target_level(rhs_kind)
     # impl-end
 
 
@@ -153,7 +145,6 @@
     # pre-conditions-start
     Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
              or rhs_kind == kind_outer())
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Normalise iff the right-hand side is NOT a query expression.
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11734.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An ``exclude(...)`` (equivalently a negated ``~Q(...)``) over an N-to-many
  relation is realised by building a fresh, nested inner subquery and matching
  the outer rows against it. The right-hand side of the original condition may
  be one of three things:

    * a plain literal value (no query reference at all),
    * a local field reference, which means "the field of the row in the query
      that the condition was written against", or
    * an ``OuterRef``, which means "a field of a query one level further out
      than the query the condition was written against".

  When such a right-hand side is carried into the freshly generated inner
  subquery, the query level it ultimately refers to MUST be preserved. The
  inner subquery sits one nesting level deeper than the query the condition was
  written against, so any reference moved into it has to be re-anchored by
  exactly one extra outward hop to keep pointing at the same query as before:

    * a local field reference (level 0, the original query) becomes an
      ``OuterRef`` so that, resolved from inside the inner subquery, it again
      denotes the original query;
    * an ``OuterRef`` (level -1, one out from the original query) must be
      wrapped in a further ``OuterRef`` so that, resolved from inside the inner
      subquery, it still denotes that same outer-of-the-original query rather
      than collapsing onto the original query;
    * a plain value carries no reference and is left untouched.

  Separately, when the value supplied to a relational comparison is prepared,
  only a genuine concrete value is normalised through the relation's value
  coercion. Anything that is itself a query expression (i.e. carries the
  ability to be resolved against a query, such as an ``OuterRef`` or a field
  reference) must be passed through untouched, because it has no concrete value
  to coerce and will be resolved later against the appropriate query level.

The two decisions are pure integer/boolean logic over a small tagged domain
(no library callee is consumed): a reference's "kind" and its effective
resolution level are modelled as ints, so no axiom is required.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# (No library callee is axiomatized: both modelled behaviours are pure,
# fully expressible integer/boolean decisions.)
# axioms-end


# pure-start
# Right-hand-side kinds (a small tagged domain).
#   KIND_VALUE   -- a plain concrete value, no query reference.
#   KIND_LOCAL   -- a local field reference (resolves against the query it is
#                   added to).
#   KIND_OUTER   -- an OuterRef (resolves one level further out than the query
#                   it is added to).
@Pure
def kind_value() -> int:
    return 0


@Pure
def kind_local() -> int:
    return 1


@Pure
def kind_outer() -> int:
    return 2


@Pure
def is_query_expression(kind: int) -> bool:
    """A right-hand side is a query expression (can be resolved against a
    query) exactly when it is a local reference or an OuterRef; a plain value
    is not."""
    return kind == kind_local() or kind == kind_outer()


@Pure
def target_level(kind: int) -> int:
    """The query level a right-hand side ultimately denotes, measured relative
    to the query the original condition was written against (that query is
    level 0). A local reference denotes that query itself (0); an OuterRef
    denotes one level further out (-1). A plain value denotes no level; we use
    the sentinel level 0 for it since it is never re-anchored."""
    if kind == kind_outer():
        return -1
    return 0


@Pure
def resolved_level_in_inner(kind: int) -> int:
    """If a right-hand side of the given kind were carried UNCHANGED into the
    freshly generated inner subquery and then resolved, this is the query level
    it would denote, again relative to the original query (level 0).

    The inner subquery is one nesting level deeper (level +1). A local
    reference resolved there denotes the inner subquery itself (level +1). An
    OuterRef resolved there denotes one level out from the inner subquery,
    i.e. the original query (level 0). A plain value denotes no level (0)."""
    if kind == kind_local():
        return 1
    if kind == kind_outer():
        return 0
    return 0
# pure-end


def rebind_into_inner_subquery(rhs_kind: int) -> int:
    """Re-anchoring applied to the original condition's right-hand side when it
    is carried into the freshly generated inner subquery. Returns the number of
    additional outward (``OuterRef``) wrapping hops to apply.

    Behaviour required: after the re-anchoring, resolving the right-hand side
    from inside the inner subquery must denote the SAME query level it denoted
    before (``target_level``)."""
    # pre-conditions-start
    Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
             or rhs_kind == kind_outer())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() >= 0)
    # A plain value carries no reference: it is left untouched (no hops).
    Ensures(Implies(rhs_kind == kind_value(), Result() == 0))
    # A query-expression right-hand side is re-anchored so that, resolved from
    # inside the inner subquery, it denotes the same level as before.
    # Each added outward hop shifts the denoted level one step further out (-1).
    Ensures(Implies(is_query_expression(rhs_kind),
                    resolved_level_in_inner(rhs_kind) - Result() == target_level(rhs_kind)))
    # post-conditions-end
    # impl-start
    if rhs_kind == kind_value():
        return 0
    if rhs_kind == kind_local():
        # level +1 in inner must become level 0 -> one outward hop.
        return 1
    # OuterRef: level 0 in inner must become level -1 -> one outward hop.
    return 1
    # impl-end


def normalize_only_concrete_value(rhs_kind: int) -> bool:
    """Decision for preparing the value of a relational comparison: returns
    whether the right-hand side is normalised through the relation's value
    coercion. Only a genuine concrete value is normalised; any query expression
    is passed through untouched."""
    # pre-conditions-start
    Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
             or rhs_kind == kind_outer())
    # pre-conditions-end
    # post-conditions-start
    # Normalise iff the right-hand side is NOT a query expression.
    Ensures(Result() == (not is_query_expression(rhs_kind)))
    # Concretely: a plain value is normalised; a local reference and an
    # OuterRef are both passed through.
    Ensures(Result() == (rhs_kind == kind_value()))
    # post-conditions-end
    # impl-start
    return not is_query_expression(rhs_kind)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Both modeled functions are FULLY PINNED by their post-conditions over the entire precondition domain rhs_kind in {value(0),local(1),outer(2)}: rebind_into_inner_subquery -> {0,1,1} (value pinned by Ensures(...==0); local by resolved_level_in_inner(1)-Result==target_level(1) => 1-Result==0; outer by 0-Result==-1); normalize_only_concrete_value -> {True,False,False} pinned by Ensures(Result()==(rhs_kind==kind_value())). No verifying wrong impl can exist because the spec admits exactly one return vector per function.

same-spec: all 9 attacks + pos_control return exit 0 (spec byte-identical; only impl regions edited).

weakness/verify results:
- pos_control.py: VERIFIED (9.2s) — correct gold-equivalent impl verifies.
- atk_1.py (PREPATCH site-A bug: OuterRef carried in with ZERO hops, `return 0` in outer branch): NOT-A-COUNTEREXAMPLE, verification FAILED (exit 2). Reproduces model_prepatch.py; spec rejects. [prepatch reproduced]
- atk_2.py (PREPATCH site-B bug: normalize everything, `return True`): FAILED (exit 2). Reproduces model_prepatch_2.py; spec rejects.
- atk_3.py (boundary: value gets 1 hop instead of 0): FAILED (exit 2).
- atk_4.py (boundary: outer over-wrapped, 2 hops): FAILED (exit 2).
- atk_5.py (fn2 inverted: normalize iff query-expression): FAILED (exit 2).
- atk_6.py (fn2 constant False: never normalize): FAILED (exit 2).
- atk_7.py (control-flow-effect fn1: fall-through returns 0 for all kinds, local/outer lose hop): FAILED (exit 2).
- atk_8.py (ungrounded-oracle echo, WRONG variant: return abs(target_level) => value:0,local:0,outer:1 — wrong on local): FAILED (exit 2).
- atk_9.py (ungrounded-oracle echo, CORRECT variant: `return resolved_level_in_inner(rhs_kind) - target_level(rhs_kind)` => value:0,local:1,outer:1): CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 9.6s).

CANDIDATE atk_9 materialized + resolved (MANDATORY): atk_9 computes {value:0,local:1,outer:1}, behaviourally IDENTICAL to gold on the whole domain (fn2 unchanged/correct), so its faithful refined patch IS the gold patch (all three hunks). Ran through the official harness via swebench_unified.harness.run_resolve("django__django-11734", patch): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, flaky=False. F2P test test_subquery_exclude_outerref (queries.tests.ExcludeTests) PASSED; all PASS_TO_PASS green; no failures. Its faithful patch RESOLVES => does not break the spec. Log: resolve_atk_9.txt; patch: atk_9_faithful.patch.

No verifying wrong impl's faithful patch fails to resolve; the only CANDIDATE is behaviourally correct and resolves => verify does NOT admit an incorrect impl here.

REFINEMENT.MD LEG AUDIT: every leg is R / A-reference / I, NO kind-3. Site A: A1=R (object kind <-> int tag), A2=I/R (plain value untouched, 0 hops), A3=R (F re-anchored as OuterRef(name) = 1 hop), A4=R (OuterRef wrapped as OuterRef(filter_rhs) = 1 hop). Site B: B1=R, B2=R/A-reference (is_query_expression <-> hasattr(rhs,'resolve_expression')). Site C: C1=I (AutoField.get_prep_value removal, dead code made unreachable by site B). No @ContractOnly axiom consumed (section D confirms). A-reference correspondence to real callees HOLDS: (1) is_query_expression == hasattr(resolve_expression): True for F/OuterRef, False for plain value; pre-patch rhs_is_direct_value()=not hasattr(as_sql) misclassifies both (matches mapping.md §3.1, axiom_check.py samples). (2) level arithmetic == OuterRef.resolve_expression semantics: bare OuterRef -> ResolvedOuterRef (collapses one level), OuterRef(OuterRef(name)) -> inner unresolved OuterRef (preserves one level), F re-anchored as OuterRef(name) -> ResolvedOuterRef (matches mapping.md §3.2). Invariant resolved_level_in_inner(k)-hops(k)==target_level(k) holds: local 1-1=0, outer 0-1=-1. Correspondence sound.

VERDICT: SOUND. 8 distinct wrong impls (atk_1..atk_8, incl. both prepatch bugs) all same-spec and all fail verification; the sole verifying candidate (atk_9) is behaviourally correct and its materialized faithful patch RESOLVES under the official harness. No verify=>incorrect gap found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-11734.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An ``exclude(...)`` (equivalently a negated ``~Q(...)``) over an N-to-many
  relation is realised by building a fresh, nested inner subquery and matching
  the outer rows against it. The right-hand side of the original condition may
  be one of three things:

    * a plain literal value (no query reference at all),
    * a local field reference, which means "the field of the row in the query
      that the condition was written against", or
    * an ``OuterRef``, which means "a field of a query one level further out
      than the query the condition was written against".

  When such a right-hand side is carried into the freshly generated inner
  subquery, the query level it ultimately refers to MUST be preserved. The
  inner subquery sits one nesting level deeper than the query the condition was
  written against, so any reference moved into it has to be re-anchored by
  exactly one extra outward hop to keep pointing at the same query as before:

    * a local field reference (level 0, the original query) becomes an
      ``OuterRef`` so that, resolved from inside the inner subquery, it again
      denotes the original query;
    * an ``OuterRef`` (level -1, one out from the original query) must be
      wrapped in a further ``OuterRef`` so that, resolved from inside the inner
      subquery, it still denotes that same outer-of-the-original query rather
      than collapsing onto the original query;
    * a plain value carries no reference and is left untouched.

  Separately, when the value supplied to a relational comparison is prepared,
  only a genuine concrete value is normalised through the relation's value
  coercion. Anything that is itself a query expression (i.e. carries the
  ability to be resolved against a query, such as an ``OuterRef`` or a field
  reference) must be passed through untouched, because it has no concrete value
  to coerce and will be resolved later against the appropriate query level.

The two decisions are pure integer/boolean logic over a small tagged domain
(no library callee is consumed): a reference's "kind" and its effective
resolution level are modelled as ints, so no axiom is required.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# (No library callee is axiomatized: both modelled behaviours are pure,
# fully expressible integer/boolean decisions.)
# axioms-end


# pure-start
# Right-hand-side kinds (a small tagged domain).
#   KIND_VALUE   -- a plain concrete value, no query reference.
#   KIND_LOCAL   -- a local field reference (resolves against the query it is
#                   added to).
#   KIND_OUTER   -- an OuterRef (resolves one level further out than the query
#                   it is added to).
@Pure
def kind_value() -> int:
    return 0


@Pure
def kind_local() -> int:
    return 1


@Pure
def kind_outer() -> int:
    return 2


@Pure
def is_query_expression(kind: int) -> bool:
    """A right-hand side is a query expression (can be resolved against a
    query) exactly when it is a local reference or an OuterRef; a plain value
    is not."""
    return kind == kind_local() or kind == kind_outer()


@Pure
def target_level(kind: int) -> int:
    """The query level a right-hand side ultimately denotes, measured relative
    to the query the original condition was written against (that query is
    level 0). A local reference denotes that query itself (0); an OuterRef
    denotes one level further out (-1). A plain value denotes no level; we use
    the sentinel level 0 for it since it is never re-anchored."""
    if kind == kind_outer():
        return -1
    return 0


@Pure
def resolved_level_in_inner(kind: int) -> int:
    """If a right-hand side of the given kind were carried UNCHANGED into the
    freshly generated inner subquery and then resolved, this is the query level
    it would denote, again relative to the original query (level 0).

    The inner subquery is one nesting level deeper (level +1). A local
    reference resolved there denotes the inner subquery itself (level +1). An
    OuterRef resolved there denotes one level out from the inner subquery,
    i.e. the original query (level 0). A plain value denotes no level (0)."""
    if kind == kind_local():
        return 1
    if kind == kind_outer():
        return 0
    return 0
# pure-end


def rebind_into_inner_subquery(rhs_kind: int) -> int:
    """Re-anchoring applied to the original condition's right-hand side when it
    is carried into the freshly generated inner subquery. Returns the number of
    additional outward (``OuterRef``) wrapping hops to apply.

    Behaviour required: after the re-anchoring, resolving the right-hand side
    from inside the inner subquery must denote the SAME query level it denoted
    before (``target_level``)."""
    # pre-conditions-start
    Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
             or rhs_kind == kind_outer())
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() >= 0)
    # A plain value carries no reference: it is left untouched (no hops).
    Ensures(Implies(rhs_kind == kind_value(), Result() == 0))
    # A query-expression right-hand side is re-anchored so that, resolved from
    # inside the inner subquery, it denotes the same level as before.
    # Each added outward hop shifts the denoted level one step further out (-1).
    Ensures(Implies(is_query_expression(rhs_kind),
                    resolved_level_in_inner(rhs_kind) - Result() == target_level(rhs_kind)))
    # post-conditions-end
    # impl-start
    if rhs_kind == kind_value():
        return 0
    if rhs_kind == kind_local():
        # level +1 in inner must become level 0 -> one outward hop.
        return 1
    # OuterRef: level 0 in inner must become level -1 -> one outward hop.
    return 1
    # impl-end


def normalize_only_concrete_value(rhs_kind: int) -> bool:
    """Decision for preparing the value of a relational comparison: returns
    whether the right-hand side is normalised through the relation's value
    coercion. Only a genuine concrete value is normalised; any query expression
    is passed through untouched."""
    # pre-conditions-start
    Requires(rhs_kind == kind_value() or rhs_kind == kind_local()
             or rhs_kind == kind_outer())
    # pre-conditions-end
    # post-conditions-start
    # Normalise iff the right-hand side is NOT a query expression.
    Ensures(Result() == (not is_query_expression(rhs_kind)))
    # Concretely: a plain value is normalised; a local reference and an
    # OuterRef are both passed through.
    Ensures(Result() == (rhs_kind == kind_value()))
    # post-conditions-end
    # impl-start
    return not is_query_expression(rhs_kind)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Both modeled functions are FULLY PINNED by their post-conditions over the entire precondition domain rhs_kind in {value(0),local(1),outer(2)}: rebind_into_inner_subquery -> {0,1,1} (value pinned by Ensures(...==0); local by resolved_level_in_inner(1)-Result==target_level(1) => 1-Result==0; outer by 0-Result==-1); normalize_only_concrete_value -> {True,False,False} pinned by Ensures(Result()==(rhs_kind==kind_value())). No verifying wrong impl can exist because the spec admits exactly one return vector per function.

same-spec: all 9 attacks + pos_control return exit 0 (spec byte-identical; only impl regions edited).

weakness/verify results:
- pos_control.py: VERIFIED (9.2s) — correct gold-equivalent impl verifies.
- atk_1.py (PREPATCH site-A bug: OuterRef carried in with ZERO hops, `return 0` in outer branch): NOT-A-COUNTEREXAMPLE, verification FAILED (exit 2). Reproduces model_prepatch.py; spec rejects. [prepatch reproduced]
- atk_2.py (PREPATCH site-B bug: normalize everything, `return True`): FAILED (exit 2). Reproduces model_prepatch_2.py; spec rejects.
- atk_3.py (boundary: value gets 1 hop instead of 0): FAILED (exit 2).
- atk_4.py (boundary: outer over-wrapped, 2 hops): FAILED (exit 2).
- atk_5.py (fn2 inverted: normalize iff query-expression): FAILED (exit 2).
- atk_6.py (fn2 constant False: never normalize): FAILED (exit 2).
- atk_7.py (control-flow-effect fn1: fall-through returns 0 for all kinds, local/outer lose hop): FAILED (exit 2).
- atk_8.py (ungrounded-oracle echo, WRONG variant: return abs(target_level) => value:0,local:0,outer:1 — wrong on local): FAILED (exit 2).
- atk_9.py (ungrounded-oracle echo, CORRECT variant: `return resolved_level_in_inner(rhs_kind) - target_level(rhs_kind)` => value:0,local:1,outer:1): CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 9.6s).

CANDIDATE atk_9 materialized + resolved (MANDATORY): atk_9 computes {value:0,local:1,outer:1}, behaviourally IDENTICAL to gold on the whole domain (fn2 unchanged/correct), so its faithful refined patch IS the gold patch (all three hunks). Ran through the official harness via swebench_unified.harness.run_resolve("django__django-11734", patch): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, flaky=False. F2P test test_subquery_exclude_outerref (queries.tests.ExcludeTests) PASSED; all PASS_TO_PASS green; no failures. Its faithful patch RESOLVES => does not break the spec. Log: resolve_atk_9.txt; patch: atk_9_faithful.patch.

No verifying wrong impl's faithful patch fails to resolve; the only CANDIDATE is behaviourally correct and resolves => verify does NOT admit an incorrect impl here.

REFINEMENT.MD LEG AUDIT: every leg is R / A-reference / I, NO kind-3. Site A: A1=R (object kind <-> int tag), A2=I/R (plain value untouched, 0 hops), A3=R (F re-anchored as OuterRef(name) = 1 hop), A4=R (OuterRef wrapped as OuterRef(filter_rhs) = 1 hop). Site B: B1=R, B2=R/A-reference (is_query_expression <-> hasattr(rhs,'resolve_expression')). Site C: C1=I (AutoField.get_prep_value removal, dead code made unreachable by site B). No @ContractOnly axiom consumed (section D confirms). A-reference correspondence to real callees HOLDS: (1) is_query_expression == hasattr(resolve_expression): True for F/OuterRef, False for plain value; pre-patch rhs_is_direct_value()=not hasattr(as_sql) misclassifies both (matches mapping.md §3.1, axiom_check.py samples). (2) level arithmetic == OuterRef.resolve_expression semantics: bare OuterRef -> ResolvedOuterRef (collapses one level), OuterRef(OuterRef(name)) -> inner unresolved OuterRef (preserves one level), F re-anchored as OuterRef(name) -> ResolvedOuterRef (matches mapping.md §3.2). Invariant resolved_level_in_inner(k)-hops(k)==target_level(k) holds: local 1-1=0, outer 0-1=-1. Correspondence sound.

VERDICT: SOUND. 8 distinct wrong impls (atk_1..atk_8, incl. both prepatch bugs) all same-spec and all fail verification; the sole verifying candidate (atk_9) is behaviourally correct and its materialized faithful patch RESOLVES under the official harness. No verify=>incorrect gap found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift) on nagini django__django-11734. The bundle models two changed decisions over a small tagged int domain rhs_kind ∈ {0=value,1=local(F),2=outer(OuterRef)}: (A) rebind_into_inner_subquery returns extra OuterRef-wrapping hops applied when a condition's RHS is carried into the freshly generated inner subquery of Query.split_exclude; (B) normalize_only_concrete_value returns whether RelatedLookupMixin.get_prep_lookup routes the RHS through value coercion.

VERIFICATION METHOD: I created a genuine git worktree at base_commit 999891bd80, applied the three gold hunks by hand (query.py split_exclude OuterRef/F re-anchor; related_lookups.py hasattr('resolve_expression') guard; removal of AutoField.get_prep_value), then ran the bundle's conformance_check.py and axiom_check.py with — i.e. against the REAL patched repo callees, not a rigged shadow.
  - conformance_check.py: status=pass, 100070 inputs, 0 disagreements. It spies on the real Query.add_filter to capture the actually-re-anchored RHS produced by real split_exclude code, and wraps the real get_normalized_value to observe whether coercion ran.
  - axiom_check.py: G-AX OK against real F/OuterRef/ResolvedOuterRef.

INDEPENDENT PROBE: On real objects I confirmed get_prep_lookup coercion runs iff hasattr(rhs,'resolve_expression') is False — True only for a plain value (int 5 -> ran), and False for F, OuterRef, and even Value(5) (all query-expressions passed through). This matches normalize_only_concrete_value == (kind==value) exactly across the modeled domain. For site A, a bare OuterRef collapses to ResolvedOuterRef and OuterRef(OuterRef(..)) preserves the inner unresolved OuterRef, confirming the one-extra-outward-hop encoding (hops = 0 for value, 1 for local, 1 for outer).

DOMAIN CHECK: Requires admits exactly rhs_kind ∈ {0,1,2}, which is the full set of RHS kinds split_exclude/get_prep_lookup distinguish (OuterRef is a subclass of F; the gold checks isinstance OuterRef first then F; plain value hits neither). No modeled-domain input makes the model disagree with the real callee. The spec is neither too strong nor drifting — it agrees with the real repo on every admissible input. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures). Confirmed against the actual spec_view of model.py (proof/impl regions elided). The spec view names no patched repo file or symbol: gold-edit sites split_exclude, RelatedLookupMixin.get_prep_lookup, AutoField.get_prep_value, related_lookups.py appear ONLY in mapping.md/refinement.md (auditor-facing, not the screened consumer spec). Changed distinctive symbols {as_sql, get_db_prep_value, get_prep_value, split_exclude} do not appear in the spec view. All domain terms used in the spec (OuterRef, exclude, ~Q, subquery/outer-query reference) are already public in problem_statement, which literally shows the failing exclude()/~Q() OuterRef test and the 'reference to an outer query' error. The spec describes desired behavior abstractly over an integer-tagged domain (kinds, query levels, 'one extra outward hop'); the phrase 'an OuterRef must be wrapped in a further OuterRef' is a behavioral consequence stated in already-public vocabulary, not an edit-localization or diff narration, and is exactly what a faithful formal spec must state. No leakage beyond problem_statement (hints_text not consulted per policy). No RELAXED_LEAKAGE deferral required.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
