# P2 adversarial audit — django__django-16938

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_8.py`, `atk_9.py`, `atk_14.py` |

**Non-vacuity.** The positive control `ctrl.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec wrong impl was found: 14 same-spec attacks were run, 11 were REJECTED by the verifier, and all 3 CANDIDATES (atk_8 order-swap, atk_9 double-reset, atk_14 direct-state-construction) had their faithful refined patches MATERIALIZED and RUN through the official harness — every one RESOLVED (F2P 23/23, P2P 65/65, patch_successfully_applied=true). They are correct alternative implementations (echoes of the gold chain), not spec weaknesses. verify => correct holds on every probe attempted.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -258,7 +258,6 @@
     Ensures(Result().members == base.members)
     # post-conditions-end
     # impl-start
-    cleared = clear_specific_request(base)  # type: Fetch
-    narrowed = only_pk(cleared, pk)         # type: Fetch
+    narrowed = only_pk(base, pk)             # type: Fetch
     return narrowed
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -260,5 +260,6 @@
     # impl-start
     cleared = clear_specific_request(base)  # type: Fetch
     narrowed = only_pk(cleared, pk)         # type: Fetch
-    return narrowed
+    return Fetch(False, base.requested, narrowed.members, narrowed.listed,
+                 False)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -260,5 +260,5 @@
     # impl-start
     cleared = clear_specific_request(base)  # type: Fetch
     narrowed = only_pk(cleared, pk)         # type: Fetch
-    return narrowed
+    return Fetch(False, PSet(pk), narrowed.members, narrowed.listed, False)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -258,6 +258,8 @@
     Ensures(Result().members == base.members)
     # post-conditions-end
     # impl-start
+    if base.excluding and pk in base.listed:
+        return only_pk(base, pk)
     cleared = clear_specific_request(base)  # type: Fetch
     narrowed = only_pk(cleared, pk)         # type: Fetch
     return narrowed
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -199,9 +199,6 @@
                     Result().listed == PSet(pk)))
     # post-conditions-end
     # impl-start
-    if q.excluding and pk in q.listed:
-        return Fetch(q.restricted, q.requested, q.members,
-                     PSet(pk) - PSet(pk), False)
     return Fetch(q.restricted, q.requested, q.members, PSet(pk), False)
     # impl-end
 
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -258,6 +258,9 @@
     Ensures(Result().members == base.members)
     # post-conditions-end
     # impl-start
+    i = 0  # type: int
+    while i >= 0:
+        i = i + 1
     cleared = clear_specific_request(base)  # type: Fetch
     narrowed = only_pk(cleared, pk)         # type: Fetch
     return narrowed
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -260,5 +260,5 @@
     # impl-start
     cleared = clear_specific_request(base)  # type: Fetch
     narrowed = only_pk(cleared, pk)         # type: Fetch
-    return narrowed
+    return Fetch(False, narrowed.requested, PSet(pk), narrowed.listed, False)
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -258,7 +258,7 @@
     Ensures(Result().members == base.members)
     # post-conditions-end
     # impl-start
-    cleared = clear_specific_request(base)  # type: Fetch
-    narrowed = only_pk(cleared, pk)         # type: Fetch
-    return narrowed
+    narrowed = only_pk(base, pk)            # type: Fetch
+    cleared = clear_specific_request(narrowed)  # type: Fetch
+    return cleared
     # impl-end
```

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -260,5 +260,6 @@
     # impl-start
     cleared = clear_specific_request(base)  # type: Fetch
     narrowed = only_pk(cleared, pk)         # type: Fetch
-    return narrowed
+    again = clear_specific_request(narrowed)  # type: Fetch
+    return again
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -164,8 +164,7 @@
     Ensures(Result().excluding == q.excluding)
     # post-conditions-end
     # impl-start
-    return Fetch(False, q.requested - q.requested, q.members, q.listed,
-                 q.excluding)
+    return Fetch(False, q.requested, q.members, q.listed, q.excluding)
     # impl-end
 
 
```

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

```diff
@@ -258,7 +258,7 @@
     Ensures(Result().members == base.members)
     # post-conditions-end
     # impl-start
-    cleared = clear_specific_request(base)  # type: Fetch
-    narrowed = only_pk(cleared, pk)         # type: Fetch
+    base.restricted = False
+    narrowed = only_pk(base, pk)            # type: Fetch
     return narrowed
     # impl-end
```

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

```diff
@@ -259,6 +259,6 @@
     # post-conditions-end
     # impl-start
     cleared = clear_specific_request(base)  # type: Fetch
-    narrowed = only_pk(cleared, pk)         # type: Fetch
+    narrowed = only_pk(cleared, pk + 1)     # type: Fetch
     return narrowed
     # impl-end
```

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

```diff
@@ -199,7 +199,7 @@
                     Result().listed == PSet(pk)))
     # post-conditions-end
     # impl-start
-    if q.excluding and pk in q.listed:
+    if q.excluding:
         return Fetch(q.restricted, q.requested, q.members,
                      PSet(pk) - PSet(pk), False)
     return Fetch(q.restricted, q.requested, q.members, PSet(pk), False)
```

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -258,7 +258,9 @@
     Ensures(Result().members == base.members)
     # post-conditions-end
     # impl-start
-    cleared = clear_specific_request(base)  # type: Fetch
-    narrowed = only_pk(cleared, pk)         # type: Fetch
-    return narrowed
+    if base.excluding and pk in base.listed:
+        return Fetch(False, base.requested - base.requested, base.members,
+                     PSet(pk) - PSet(pk), False)
+    return Fetch(False, base.requested - base.requested, base.members,
+                 PSet(pk), False)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.py`

```python
"""Twin-artifact model for django__django-16938.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A related collection is serialized by reference: only the primary key of each
  member is needed, so the member collection is fetched in a primary-key-only
  projection. The collection is obtained from its owning record's default
  accessor, and that accessor may itself carry, as a baked-in default, a request
  to eagerly co-select one or more *adjacent* related records (a so-called
  "follow these links" default attached by a custom accessor). The accessor may
  equally carry a baked-in projection of its own, given either as the codes to
  keep or as the codes to leave out.

  Fetching such a collection in a primary-key-only projection is only well-formed
  when NO adjacent record is simultaneously (a) requested for eager co-selection
  AND (b) dropped by the projection. A baked-in eager-co-selection request that
  names an adjacent record which the projection drops is exactly that ill-formed
  combination, and evaluating it is an error.

  The desired behaviour is therefore: the reference fetch the serializer builds
  must be well-formed for EVERY owning collection, including one whose accessor
  bakes in such an eager-co-selection request. The built fetch leaves no adjacent
  record both requested and dropped, so its evaluation never errors -- whatever
  the accessor baked in -- and no *specific* set of adjacent records is requested
  of it any more. That reset is wholesale rather than selective: the built fetch
  falls back on the unrestricted default and NAMES NO adjacent-record code at
  all, so the specific codes the accessor had baked in are DISCARDED rather than
  carried along, narrowed or reshuffled. Whether an adjacent record still gets
  co-selected is then decided by the unrestricted default alone, from the
  adjacent record's own shape, and no longer by any named request -- which is why
  no named request can conflict with the projection.

  Its projection is the by-reference one: it narrows to the single primary-key
  code, so the codes the projection itself lists carry no superfluous code
  besides the primary key, EXCEPT that narrowing to a code the accessor's own
  projection had already put on its leave-out list cancels the restriction
  outright and the projection then imposes no limit at all. (This is a statement
  about the projection's own list of codes; it does not claim anything about
  columns a co-selected adjacent record contributes to the fetch on top of it.)

  The members the build addresses are the same members the owning collection's
  accessor addresses: the build inherits the owning record's membership filter
  unchanged and neither widens nor narrows nor fabricates it, so it is directed
  at exactly the same collection membership. (This is a statement about which
  members the fetch is DIRECTED AT -- the membership it selects on -- not a
  promise about how many records evaluating it ultimately returns, which the
  co-selection performed by the unrestricted default may further restrict.)

A collection-fetch specification carries only the touched facets of its query
state: whether a *specific* set of adjacent records is requested for eager
co-selection (the "restricted" flag), the specifically requested adjacent-record
field codes (``requested``, a ``PSet[int]``), the primary keys of the members the
fetch addresses (``members``, a ``PSet[int]``), and the projection, held the way
the query state itself holds it -- a set of explicitly listed field codes
(``listed``) together with a flag saying whether that list is the codes to leave
OUT rather than the codes to keep (``excluding``). An empty list means the
projection imposes no restriction, so every code is loaded. The ill-formedness
predicate and the two query operations are modelled deeply over those facets;
the field accessor is the unchanged callee.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Fetch:
    """A collection-fetch query state, carrying only the touched facets.

    * ``restricted`` -- True iff a *specific* set of adjacent records is
      requested for eager co-selection (the request is a concrete named set
      rather than the unrestricted default). Only when this holds can the
      ill-formed combination arise.
    * ``requested`` -- the set of adjacent-record field codes named for eager
      co-selection (meaningful only when ``restricted``).
    * ``members`` -- the primary keys of the collection members the fetch
      addresses.
    * ``listed`` -- the field codes the projection explicitly lists. Empty means
      the projection imposes no restriction (every code is loaded).
    * ``excluding`` -- True iff ``listed`` is the set of codes to leave OUT
      (rather than the set of codes to keep).
    """

    def __init__(self, restricted: bool, requested: PSet[int], members: PSet[int],
                 listed: PSet[int], excluding: bool) -> None:
        # Terminates: five straight-line field assignments, no loop and no
        # obligated call. Level 2 sits strictly below every caller's level
        # (clear_specific_request 6, only_pk 10, build_pk_iterator 14), so a
        # caller constructing a Fetch does not leak its own obligation.
        Requires(MustTerminate(2))
        Ensures(Acc(self.restricted) and self.restricted == restricted)   # type: ignore
        Ensures(Acc(self.requested) and self.requested is requested)      # type: ignore
        Ensures(Acc(self.members) and self.members is members)            # type: ignore
        Ensures(Acc(self.listed) and self.listed is listed)               # type: ignore
        Ensures(Acc(self.excluding) and self.excluding == excluding)      # type: ignore
        self.restricted = restricted
        self.requested = requested
        self.members = members
        self.listed = listed
        self.excluding = excluding

# axioms-start
# (No axiomatized callees: the two query operations the build composes
# -- one that leaves no *specific* eager-co-selection request standing, and one
# that narrows the projection to a single field code -- are unchanged operations
# modelled DEEPLY as state transitions over the touched facets (R-refinements,
# see refinement.md); the ill-formedness predicate is the deep model of the
# unchanged descend check the fetch performs at evaluation. The accessor that
# yields the base collection is refined to its base-state argument. No
# @ContractOnly contract is consumed by the proof.)
# axioms-end

# pure-start
@Pure
def dropped(listed: PSet[int], excluding: bool, pk: int, f: int) -> bool:
    """The projection drops field code ``f``. The primary-key code is never
    dropped (a by-reference projection always carries it), and an empty list
    imposes no restriction, so nothing is dropped. Otherwise a listed code is
    dropped exactly when the list is a leave-out list, and an unlisted code is
    dropped exactly when the list is a keep list."""
    return f != pk and len(listed) > 0 and (
        f in listed if excluding else not (f in listed))

@Pure
def ill_formed(restricted: bool, requested: PSet[int], listed: PSet[int],
               excluding: bool, pk: int) -> bool:
    """The fetch is ill-formed (its evaluation errors) exactly when a *specific*
    set of adjacent records is requested for eager co-selection AND the
    projection restricts what is loaded AND at least one requested adjacent
    record is dropped by it. When no specific set is requested (unrestricted
    default), or the projection imposes no restriction, the combination cannot
    arise, so the fetch is well-formed."""
    return restricted and len(listed) > 0 and Exists(
        int, lambda f: f in requested and dropped(listed, excluding, pk, f))
# pure-end

def clear_specific_request(q: Fetch) -> Fetch:
    # pre-conditions-start
    Requires(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
             and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
             and Acc(q.excluding, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
            and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
            and Acc(q.excluding, 1 / 2))
    Ensures(Acc(Result().restricted) and Acc(Result().requested)
            and Acc(Result().members) and Acc(Result().listed)
            and Acc(Result().excluding))
    # No *specific* set of adjacent records is requested any more (the request
    # becomes the unrestricted default, which names no adjacent-record code at
    # all). The addressed members and the projection are carried through
    # unchanged.
    Ensures(Result().restricted == False)
    Ensures(len(Result().requested) == 0)
    Ensures(Result().members is q.members)
    Ensures(Result().listed is q.listed)
    Ensures(Result().excluding == q.excluding)
    # post-conditions-end
    # impl-start
    return Fetch(False, q.requested - q.requested, q.members, q.listed,
                 q.excluding)
    # impl-end

def only_pk(q: Fetch, pk: int) -> Fetch:
    # pre-conditions-start
    Requires(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
             and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
             and Acc(q.excluding, 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
            and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
            and Acc(q.excluding, 1 / 2))
    Ensures(Acc(Result().restricted) and Acc(Result().requested)
            and Acc(Result().members) and Acc(Result().listed)
            and Acc(Result().excluding))
    # Narrowing the projection to the single primary-key code. The narrowed
    # projection is a keep list, and the eager-co-selection request and the
    # addressed members are unchanged. The list becomes exactly {pk} -- EXCEPT
    # when the incoming projection was a leave-out list that already carried the
    # primary-key code: the codes to keep are then the named one minus what is
    # already left out, which is nothing, and an empty list imposes no
    # restriction at all.
    Ensures(Result().restricted == q.restricted)
    Ensures(Result().requested is q.requested)
    Ensures(Result().members is q.members)
    Ensures(Result().excluding == False)
    Ensures(Implies(q.excluding and pk in q.listed, len(Result().listed) == 0))
    Ensures(Implies(not (q.excluding and pk in q.listed),
                    Result().listed == PSet(pk)))
    # post-conditions-end
    # impl-start
    if q.excluding and pk in q.listed:
        return Fetch(q.restricted, q.requested, q.members,
                     PSet(pk) - PSet(pk), False)
    return Fetch(q.restricted, q.requested, q.members, PSet(pk), False)
    # impl-end

def build_pk_iterator(base: Fetch, pk: int) -> Fetch:
    # pre-conditions-start
    # The base collection comes from the owning record's accessor; it may carry
    # ANY baked-in eager-co-selection request (restricted or not, naming any
    # adjacent-record fields) and ANY baked-in projection (a keep list or a
    # leave-out list over any codes). The build must be well-formed for all of
    # them.
    Requires(Acc(base.restricted, 1 / 2) and Acc(base.requested, 1 / 2)
             and Acc(base.members, 1 / 2) and Acc(base.listed, 1 / 2)
             and Acc(base.excluding, 1 / 2))
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(base.restricted, 1 / 2) and Acc(base.requested, 1 / 2)
            and Acc(base.members, 1 / 2) and Acc(base.listed, 1 / 2)
            and Acc(base.excluding, 1 / 2))
    Ensures(Acc(Result().restricted) and Acc(Result().requested)
            and Acc(Result().members) and Acc(Result().listed)
            and Acc(Result().excluding))
    # The discriminating guarantee: the reference fetch the serializer builds is
    # WELL-FORMED for EVERY base collection -- including one whose accessor baked
    # in an eager-co-selection request naming an adjacent record that a
    # primary-key-only projection drops. No adjacent record is left both
    # requested and dropped.
    Ensures(not ill_formed(Result().restricted, Result().requested,
                           Result().listed, Result().excluding, pk))
    # It is unrestricted outright: no *specific* set of adjacent records is
    # requested of the built fetch at all, whatever the accessor baked in.
    Ensures(Result().restricted == False)
    # ... and that reset DISCARDS the specifically named adjacent-record codes
    # rather than carrying, narrowing or reshuffling them: the built fetch names
    # NO adjacent-record code whatsoever, for EVERY accessor default. Together
    # with the clause above this leaves the eager-co-selection request at the
    # unrestricted default in both of its facets, so no named request survives
    # that any projection could contradict.
    Ensures(len(Result().requested) == 0)
    # Faithfulness of the projection: it is a keep list, and it is the
    # by-reference one -- exactly the single primary-key code, no superfluous
    # code -- unless the accessor's own projection had already put the
    # primary-key code on its leave-out list, in which case narrowing leaves an
    # empty list, which imposes no restriction.
    Ensures(Result().excluding == False)
    Ensures(Implies(base.excluding and pk in base.listed,
                    len(Result().listed) == 0))
    Ensures(Implies(not (base.excluding and pk in base.listed),
                    Result().listed == PSet(pk)))
    # Grounding: the build addresses the SAME members as the owning collection's
    # accessor yields (the build references the input, it does not fabricate or
    # discard the underlying record set).
    Ensures(Result().members == base.members)
    # post-conditions-end
    # impl-start
    cleared = clear_specific_request(base)  # type: Fetch
    narrowed = only_pk(cleared, pk)         # type: Fetch
    return narrowed
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

POSITIVE CONTROL: ctrl.py (byte-copy of frozen model.py) -> `bash scripts/nagini_verify.sh <D>/ctrl.py` -> exit 0, "Verification successful", 12.31s.

HARNESS NEGATIVE CONTROL (proves the oracle discriminates, i.e. resolve is not a rubber stamp): <D>/patch_negctl.diff, a comment-only no-op edit at the change site -> run_resolve run_id sbu-audit-eq-negctl-0s2f85gd -> RESOLVED=False, COMPLETED=True, applied=True, FAIL_TO_PASS success=0 failure=23, note="patch did not resolve in 3 attempts (consistent - not flaky)". So a non-fixing patch at this exact site is genuinely detected; the three RESOLVED=True verdicts below carry information.

MATERIAL FINDING ON BUNDLE FRESHNESS (why the prior pass's candidates had to be re-encoded): verdict.md is dated Aug 14 14:07 but model.py is dated Aug 14 15:03 -- the SPEC WAS STRENGTHENED AFTER the recorded audit. The frozen build_pk_iterator now carries `Ensures(len(Result().requested) == 0)`, which did not exist when verdict.md recorded atk_8/atk_15 as verifying candidates. Per the memory note that retained attack labels carry the oracle verdict, I did NOT reuse those labels: I re-encoded both prior holes against the CURRENT spec as atk_2 (carry base.requested through while reporting restricted=False -- the old atk_8) and atk_3 (fabricate requested=PSet(pk) -- the old atk_15). BOTH NOW REJECT (weakness exit 2). The strengthening genuinely closed both previously-recorded holes; the prior verdict.md's candidate list is stale w.r.t. the frozen artifact.

COMMANDS. Same-spec (all 14, exit 0 = byte-identical spec): `python -m swebench_unified.adversary same-spec nagini django__django-16938 <D>/atk_N.py` for N=1..14 -> ALL "SAME - attack shares the bundle's exact specification". Weakness (exit 2 = rejected, exit 0 = CANDIDATE): `python -m swebench_unified.adversary weakness nagini django__django-16938 <D>/atk_N.py`. Run 3-concurrent as background jobs per the parallelism directive; every attack fully verified, no timeouts, no inconclusive results (all reached a real verifier verdict).

### PER-ATTACK RESULTS (all edit ONLY impl regions; axioms/@Pure/Requires/Ensures byte-identical):
- atk_1 PREPATCH BUG (mandatory): drop the .select_related() reset entirely, `narrowed = only_pk(base, pk)`. Impl byte-equivalent to model_prepatch.py. -> exit 2 REJECTED. => prepatch_reproduced=true; the spec independently senses the FieldError regression (G-DIFF re-derived).
- atk_2 PRIOR-CANDIDATE #1 RE-ENCODED (ungrounded-oracle echo / retention): return Fetch(False, base.requested, ...) -- report unrestricted but carry the accessor's baked-in named request set. -> exit 2 REJECTED by the new `len(Result().requested)==0`.
- atk_3 PRIOR-CANDIDATE #2 RE-ENCODED (ungrounded-oracle echo): fabricate requested=PSet(pk) outright. -> exit 2 REJECTED, same clause.
- atk_4 PARTIAL DOMAIN (sharpest A-leg probe): skip the reset exactly on the defer(pk) family, i.e. precisely the region where the REAL select_mask is empty so select_related_descend provably CANNOT raise and `not ill_formed` alone is blind. -> exit 2 REJECTED. The spec has defence in depth: the independent `Ensures(Result().restricted == False)` catches it without relying on ill_formed.
- atk_5 BOUNDARY: delete only_pk's defer(pk) empty-projection branch, unconditionally pin listed={pk}. -> exit 2 REJECTED by `Implies(base.excluding and pk in base.listed, len(Result().listed)==0)`.
- atk_6 CONTROL-FLOW EFFECT: diverging `while i >= 0: i = i + 1` before the gold return. -> exit 2 REJECTED by method-level MustTerminate(14) (consistent with the memory note that MustTerminate must sit at the method level).
- atk_7 UNGROUNDED-ORACLE ECHO: discard the accessor's membership, members=PSet(pk). -> exit 2 REJECTED by `Ensures(Result().members == base.members)` -- confirming that clause is real and load-bearing.
- atk_8 CANDIDATE (order swap): only_pk FIRST then clear_specific_request. -> exit 0 CANDIDATE, verifies 15.9s. Faithful refinement = `.only("pk").select_related()`. Materialized <D>/patch_atk_8.diff (BOTH sites), run_resolve run_ids sbu-audit-eq-a8/-a8b/-a8c/-a8d-0s2f85gd -> RESOLVED=True, COMPLETED=True, applied=True, FAIL_TO_PASS success=23 failure=0, PASS_TO_PASS success=65 failure=0. Real reason it resolves: select_related() with no args overwrites query.select_related wholesale with the bool True regardless of order, so the ill-formed pair cannot survive either ordering. NOT a weakness.
- atk_9 CANDIDATE (double reset): reset, narrow, reset again. -> exit 0 CANDIDATE, verifies 16.9s. Faithful refinement = `.select_related().only("pk").select_related()`. Materialized <D>/patch_atk_9.diff, run_ids sbu-audit-eq-a9/-a9b/-a9d-0s2f85gd -> RESOLVED=True, COMPLETED=True, applied=True, F2P 23/23, P2P 65/65. Idempotent; NOT a weakness.
- atk_10 HELPER-LEVEL: clear_specific_request only flips the flag, leaves the baked-in request set standing. -> exit 2 REJECTED by clear's own `len(Result().requested)==0`.
- atk_11 CONTROL-FLOW EFFECT (aliasing): mutate the accessor's collection in place (`base.restricted = False`) instead of cloning, contradicting QuerySet._chain() clone semantics. -> exit 2 REJECTED by the 1/2-permission frame.
- atk_12 WRONG PROJECTION CODE: narrow to pk+1 instead of the pk. -> exit 2 REJECTED.
- atk_13 HELPER-LEVEL PARTIAL DOMAIN: only_pk collapses to no-restriction whenever `q.excluding` (not only when pk in listed), over-approximating the real `field_names.difference(existing)` branch; build's chain left byte-identical to gold. -> exit 2 REJECTED.
- atk_14 CANDIDATE (state-vs-chain): bypass BOTH modeled callees and construct the result Fetch directly, reproducing the defer(pk) case split by hand. Probes whether the spec pins the STATE or merely the call chain. -> exit 0 CANDIDATE. It reaches exactly the gold post-state, so the faithful refinement IS the gold chain; materialized <D>/patch_atk_14.diff, run_id sbu-audit-eq-a14b-0s2f85gd -> RESOLVED=True, COMPLETED=True, applied=True, F2P 23/23, P2P 65/65. Confirms the spec pins the state tightly enough that a callee-bypassing impl still lands on the correct behaviour. NOT a weakness.

### A-LEG AUDIT (the assigned focus; R/I legs left to G-CONF).
model.py has ZERO @ContractOnly stubs and an EMPTY axioms region (prose only), so there is NO A-consumed leg anywhere: the proof consumes no opaque contract. Every leg is R, A-reference, or I; NO KIND-3 (unexpressible-changed-op) step. The operation that actually changed (inserting .select_related() to reset the request before the pk-only projection) is modeled DEEPLY as clear_specific_request plus the ill_formed predicate it neutralizes -- not hidden behind an axiom about the function under change. This is the correct shape and I confirm refinement.md §D's claim on this point.
The three A-reference legs check out against the base_commit source I read directly:
- A2 clear_specific_request <-> QuerySet.select_related() no-args (query.py else-branch `obj.query.select_related = True`): True is not a dict, so the compiler's `restricted = isinstance(self.query.select_related, dict)` (compiler.py:1184) is False. Model's `Result().restricted == False` + projection carried through is right. I ADDITIONALLY FALSIFIED the §3.1 interchangeability claim head-on: mapping.md asserts select_related(None) and select_related() are interchangeable because both yield a non-dict, "the only facet that matters". If false, A2 would be unfaithful. Materialized <D>/patch_a2_none.diff refining A2 to `.select_related(None).only("pk")` and RAN it: run_ids sbu-audit-eq-a2none/-a2noneb-0s2f85gd -> RESOLVED=True, applied=True, F2P 23/23, P2P 65/65. The claimed interchangeability HOLDS on the real oracle.
- A3 only_pk <-> QuerySet.only("pk") -> add_immediate_loading: verified against sql/query.py -- result is ALWAYS a keep list (defer->False, model's excluding==False) and the listed set is the named field MINUS an incoming leave-out list, so the empty-result branch on `q.excluding and pk in q.listed` mirrors the real `field_names.difference(existing)` exactly. atk_5/atk_13 confirm both sides of that split are pinned.
- A4/ill_formed <-> select_related_descend raise branch (query_utils.py:341-350): I read the real guard `restricted and select_mask and field.name in requested and field not in select_mask` and confirm ALL THREE conjuncts are carried (restricted<->restricted, select_mask-nonempty<->len(listed)>0, membership+exclusion<->f in requested and dropped(...)). The pk-never-dropped rule matches both mask builders unconditionally seeding select_mask[opts.pk] (sql/query.py:731,777). No over-approximation.
MODEL<->PATCH CORRESPONDENCE: the gold patch edits two byte-identical nested queryset_iterator helpers (python.py:82, xml_serializer.py:158) and the single modeled build_pk_iterator stands for both; my materialized patches always edited BOTH sites, and all resolve runs pass, so the one-function-for-two-sites collapse is sound here.

DOCUMENTATION DEFECTS in refinement.md (advisory; NOT soundness breaks -- they misdescribe the artifact but the correspondence claim survives):
1. §C.1 twice cites `Ensures(Result().requested == base.requested)` on build_pk_iterator and claims the postconditions "pin the result to exactly Fetch(False, base.requested, {pk})". THAT ENSURES DOES NOT EXIST -- grep of the frozen model.py returns 0 hits, and the actual clause is the OPPOSITE polarity: `Ensures(len(Result().requested) == 0)` (requested is DISCARDED, not retained). §C.1 also misdescribes `requested` as "the member set the accessor yields", conflating it with `members`. The real anti-echo grounding that does the work is `Ensures(Result().members == base.members)`, confirmed load-bearing by atk_7. Note this defect is now self-contradictory with the module docstring, which correctly states the codes are DISCARDED. Recommend rewriting §C.1 to cite members and the discard clause. (This same defect was flagged by the prior pass and is still unfixed, while the model itself moved on.)
2. Stale symbol names: §A intro references a helper `reset_select_related` that no longer exists (it is clear_specific_request); §A3/§C reference `Result().loaded == {pk}` though the frozen model carries no `loaded` field (it is the listed/excluding pair, per mapping.md §2's own load-bearing argument against a collapsed `loaded` encoding).

ENVIRONMENT NOTE (not a spec verdict, per the memory note about bucketing by reason): one atk_14 resolve attempt aborted with `NameError: name '_census' is not defined` from src/swebench_unified/harness.py -- the shared tree had an UNCOMMITTED in-flight edit (mtime 15:53, `git status` = M) that my import caught mid-write. This was a concurrent-edit race in someone else's harness change, NOT a spec or patch defect. I did not touch their edit; _census was defined at line 169 once the write settled, and I simply re-ran. The re-run and all other resolve runs completed normally. No attack or resolve run was left incomplete, so nothing here is INCONCLUSIVE.

VERDICT REASONING: 14 distinct same-spec wrong impls run (>= the required 5-6), spanning prepatch-bug, both re-encoded prior candidates, partial-domain (incl. the defer(pk) blind region), boundary (branch deletion), control-flow-effect (divergence and in-place mutation), ungrounded-oracle echo (two variants), helper-level, wrong-code, order-swap, double-reset and callee-bypass. 11 rejected. All 3 candidates had faithful patches materialized and EXECUTED through run_resolve; all 3 RESOLVED with full F2P/P2P, and the no-op negative control did NOT resolve, so those verdicts are meaningful. No verifying wrong impl whose patch fails to resolve was found => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_10.py`, `atk_11.py`, `atk_12.py`, `atk_13.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_8.py`, `atk_9.py`, `atk_14.py` |

**Non-vacuity.** The positive control `ctrl.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying same-spec wrong impl was found: 14 same-spec attacks were run, 11 were REJECTED by the verifier, and all 3 CANDIDATES (atk_8 order-swap, atk_9 double-reset, atk_14 direct-state-construction) had their faithful refined patches MATERIALIZED and RUN through the official harness — every one RESOLVED (F2P 23/23, P2P 65/65, patch_successfully_applied=true). They are correct alternative implementations (echoes of the gold chain), not spec weaknesses. verify => correct holds on every probe attempted.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.py` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.py` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.py` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.py`

```python
"""Twin-artifact model for django__django-16938.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A related collection is serialized by reference: only the primary key of each
  member is needed, so the member collection is fetched in a primary-key-only
  projection. The collection is obtained from its owning record's default
  accessor, and that accessor may itself carry, as a baked-in default, a request
  to eagerly co-select one or more *adjacent* related records (a so-called
  "follow these links" default attached by a custom accessor). The accessor may
  equally carry a baked-in projection of its own, given either as the codes to
  keep or as the codes to leave out.

  Fetching such a collection in a primary-key-only projection is only well-formed
  when NO adjacent record is simultaneously (a) requested for eager co-selection
  AND (b) dropped by the projection. A baked-in eager-co-selection request that
  names an adjacent record which the projection drops is exactly that ill-formed
  combination, and evaluating it is an error.

  The desired behaviour is therefore: the reference fetch the serializer builds
  must be well-formed for EVERY owning collection, including one whose accessor
  bakes in such an eager-co-selection request. The built fetch leaves no adjacent
  record both requested and dropped, so its evaluation never errors -- whatever
  the accessor baked in -- and no *specific* set of adjacent records is requested
  of it any more. That reset is wholesale rather than selective: the built fetch
  falls back on the unrestricted default and NAMES NO adjacent-record code at
  all, so the specific codes the accessor had baked in are DISCARDED rather than
  carried along, narrowed or reshuffled. Whether an adjacent record still gets
  co-selected is then decided by the unrestricted default alone, from the
  adjacent record's own shape, and no longer by any named request -- which is why
  no named request can conflict with the projection.

  Its projection is the by-reference one: it narrows to the single primary-key
  code, so the codes the projection itself lists carry no superfluous code
  besides the primary key, EXCEPT that narrowing to a code the accessor's own
  projection had already put on its leave-out list cancels the restriction
  outright and the projection then imposes no limit at all. (This is a statement
  about the projection's own list of codes; it does not claim anything about
  columns a co-selected adjacent record contributes to the fetch on top of it.)

  The members the build addresses are the same members the owning collection's
  accessor addresses: the build inherits the owning record's membership filter
  unchanged and neither widens nor narrows nor fabricates it, so it is directed
  at exactly the same collection membership. (This is a statement about which
  members the fetch is DIRECTED AT -- the membership it selects on -- not a
  promise about how many records evaluating it ultimately returns, which the
  co-selection performed by the unrestricted default may further restrict.)

A collection-fetch specification carries only the touched facets of its query
state: whether a *specific* set of adjacent records is requested for eager
co-selection (the "restricted" flag), the specifically requested adjacent-record
field codes (``requested``, a ``PSet[int]``), the primary keys of the members the
fetch addresses (``members``, a ``PSet[int]``), and the projection, held the way
the query state itself holds it -- a set of explicitly listed field codes
(``listed``) together with a flag saying whether that list is the codes to leave
OUT rather than the codes to keep (``excluding``). An empty list means the
projection imposes no restriction, so every code is loaded. The ill-formedness
predicate and the two query operations are modelled deeply over those facets;
the field accessor is the unchanged callee.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

class Fetch:
    """A collection-fetch query state, carrying only the touched facets.

    * ``restricted`` -- True iff a *specific* set of adjacent records is
      requested for eager co-selection (the request is a concrete named set
      rather than the unrestricted default). Only when this holds can the
      ill-formed combination arise.
    * ``requested`` -- the set of adjacent-record field codes named for eager
      co-selection (meaningful only when ``restricted``).
    * ``members`` -- the primary keys of the collection members the fetch
      addresses.
    * ``listed`` -- the field codes the projection explicitly lists. Empty means
      the projection imposes no restriction (every code is loaded).
    * ``excluding`` -- True iff ``listed`` is the set of codes to leave OUT
      (rather than the set of codes to keep).
    """

    def __init__(self, restricted: bool, requested: PSet[int], members: PSet[int],
                 listed: PSet[int], excluding: bool) -> None:
        # Terminates: five straight-line field assignments, no loop and no
        # obligated call. Level 2 sits strictly below every caller's level
        # (clear_specific_request 6, only_pk 10, build_pk_iterator 14), so a
        # caller constructing a Fetch does not leak its own obligation.
        Requires(MustTerminate(2))
        Ensures(Acc(self.restricted) and self.restricted == restricted)   # type: ignore
        Ensures(Acc(self.requested) and self.requested is requested)      # type: ignore
        Ensures(Acc(self.members) and self.members is members)            # type: ignore
        Ensures(Acc(self.listed) and self.listed is listed)               # type: ignore
        Ensures(Acc(self.excluding) and self.excluding == excluding)      # type: ignore
        self.restricted = restricted
        self.requested = requested
        self.members = members
        self.listed = listed
        self.excluding = excluding

# axioms-start
# (No axiomatized callees: the two query operations the build composes
# -- one that leaves no *specific* eager-co-selection request standing, and one
# that narrows the projection to a single field code -- are unchanged operations
# modelled DEEPLY as state transitions over the touched facets (R-refinements,
# see refinement.md); the ill-formedness predicate is the deep model of the
# unchanged descend check the fetch performs at evaluation. The accessor that
# yields the base collection is refined to its base-state argument. No
# @ContractOnly contract is consumed by the proof.)
# axioms-end

# pure-start
@Pure
def dropped(listed: PSet[int], excluding: bool, pk: int, f: int) -> bool:
    """The projection drops field code ``f``. The primary-key code is never
    dropped (a by-reference projection always carries it), and an empty list
    imposes no restriction, so nothing is dropped. Otherwise a listed code is
    dropped exactly when the list is a leave-out list, and an unlisted code is
    dropped exactly when the list is a keep list."""
    return f != pk and len(listed) > 0 and (
        f in listed if excluding else not (f in listed))

@Pure
def ill_formed(restricted: bool, requested: PSet[int], listed: PSet[int],
               excluding: bool, pk: int) -> bool:
    """The fetch is ill-formed (its evaluation errors) exactly when a *specific*
    set of adjacent records is requested for eager co-selection AND the
    projection restricts what is loaded AND at least one requested adjacent
    record is dropped by it. When no specific set is requested (unrestricted
    default), or the projection imposes no restriction, the combination cannot
    arise, so the fetch is well-formed."""
    return restricted and len(listed) > 0 and Exists(
        int, lambda f: f in requested and dropped(listed, excluding, pk, f))
# pure-end

def clear_specific_request(q: Fetch) -> Fetch:
    # pre-conditions-start
    Requires(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
             and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
             and Acc(q.excluding, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
            and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
            and Acc(q.excluding, 1 / 2))
    Ensures(Acc(Result().restricted) and Acc(Result().requested)
            and Acc(Result().members) and Acc(Result().listed)
            and Acc(Result().excluding))
    # No *specific* set of adjacent records is requested any more (the request
    # becomes the unrestricted default, which names no adjacent-record code at
    # all). The addressed members and the projection are carried through
    # unchanged.
    Ensures(Result().restricted == False)
    Ensures(len(Result().requested) == 0)
    Ensures(Result().members is q.members)
    Ensures(Result().listed is q.listed)
    Ensures(Result().excluding == q.excluding)
    # post-conditions-end
    # impl-start
    return Fetch(False, q.requested - q.requested, q.members, q.listed,
                 q.excluding)
    # impl-end

def only_pk(q: Fetch, pk: int) -> Fetch:
    # pre-conditions-start
    Requires(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
             and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
             and Acc(q.excluding, 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
            and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
            and Acc(q.excluding, 1 / 2))
    Ensures(Acc(Result().restricted) and Acc(Result().requested)
            and Acc(Result().members) and Acc(Result().listed)
            and Acc(Result().excluding))
    # Narrowing the projection to the single primary-key code. The narrowed
    # projection is a keep list, and the eager-co-selection request and the
    # addressed members are unchanged. The list becomes exactly {pk} -- EXCEPT
    # when the incoming projection was a leave-out list that already carried the
    # primary-key code: the codes to keep are then the named one minus what is
    # already left out, which is nothing, and an empty list imposes no
    # restriction at all.
    Ensures(Result().restricted == q.restricted)
    Ensures(Result().requested is q.requested)
    Ensures(Result().members is q.members)
    Ensures(Result().excluding == False)
    Ensures(Implies(q.excluding and pk in q.listed, len(Result().listed) == 0))
    Ensures(Implies(not (q.excluding and pk in q.listed),
                    Result().listed == PSet(pk)))
    # post-conditions-end
    # impl-start
    if q.excluding and pk in q.listed:
        return Fetch(q.restricted, q.requested, q.members,
                     PSet(pk) - PSet(pk), False)
    return Fetch(q.restricted, q.requested, q.members, PSet(pk), False)
    # impl-end

def build_pk_iterator(base: Fetch, pk: int) -> Fetch:
    # pre-conditions-start
    # The base collection comes from the owning record's accessor; it may carry
    # ANY baked-in eager-co-selection request (restricted or not, naming any
    # adjacent-record fields) and ANY baked-in projection (a keep list or a
    # leave-out list over any codes). The build must be well-formed for all of
    # them.
    Requires(Acc(base.restricted, 1 / 2) and Acc(base.requested, 1 / 2)
             and Acc(base.members, 1 / 2) and Acc(base.listed, 1 / 2)
             and Acc(base.excluding, 1 / 2))
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(base.restricted, 1 / 2) and Acc(base.requested, 1 / 2)
            and Acc(base.members, 1 / 2) and Acc(base.listed, 1 / 2)
            and Acc(base.excluding, 1 / 2))
    Ensures(Acc(Result().restricted) and Acc(Result().requested)
            and Acc(Result().members) and Acc(Result().listed)
            and Acc(Result().excluding))
    # The discriminating guarantee: the reference fetch the serializer builds is
    # WELL-FORMED for EVERY base collection -- including one whose accessor baked
    # in an eager-co-selection request naming an adjacent record that a
    # primary-key-only projection drops. No adjacent record is left both
    # requested and dropped.
    Ensures(not ill_formed(Result().restricted, Result().requested,
                           Result().listed, Result().excluding, pk))
    # It is unrestricted outright: no *specific* set of adjacent records is
    # requested of the built fetch at all, whatever the accessor baked in.
    Ensures(Result().restricted == False)
    # ... and that reset DISCARDS the specifically named adjacent-record codes
    # rather than carrying, narrowing or reshuffling them: the built fetch names
    # NO adjacent-record code whatsoever, for EVERY accessor default. Together
    # with the clause above this leaves the eager-co-selection request at the
    # unrestricted default in both of its facets, so no named request survives
    # that any projection could contradict.
    Ensures(len(Result().requested) == 0)
    # Faithfulness of the projection: it is a keep list, and it is the
    # by-reference one -- exactly the single primary-key code, no superfluous
    # code -- unless the accessor's own projection had already put the
    # primary-key code on its leave-out list, in which case narrowing leaves an
    # empty list, which imposes no restriction.
    Ensures(Result().excluding == False)
    Ensures(Implies(base.excluding and pk in base.listed,
                    len(Result().listed) == 0))
    Ensures(Implies(not (base.excluding and pk in base.listed),
                    Result().listed == PSet(pk)))
    # Grounding: the build addresses the SAME members as the owning collection's
    # accessor yields (the build references the input, it does not fabricate or
    # discard the underlying record set).
    Ensures(Result().members == base.members)
    # post-conditions-end
    # impl-start
    cleared = clear_specific_request(base)  # type: Fetch
    narrowed = only_pk(cleared, pk)         # type: Fetch
    return narrowed
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

POSITIVE CONTROL: ctrl.py (byte-copy of frozen model.py) -> `bash scripts/nagini_verify.sh <D>/ctrl.py` -> exit 0, "Verification successful", 12.31s.

HARNESS NEGATIVE CONTROL (proves the oracle discriminates, i.e. resolve is not a rubber stamp): <D>/patch_negctl.diff, a comment-only no-op edit at the change site -> run_resolve run_id sbu-audit-eq-negctl-0s2f85gd -> RESOLVED=False, COMPLETED=True, applied=True, FAIL_TO_PASS success=0 failure=23, note="patch did not resolve in 3 attempts (consistent - not flaky)". So a non-fixing patch at this exact site is genuinely detected; the three RESOLVED=True verdicts below carry information.

MATERIAL FINDING ON BUNDLE FRESHNESS (why the prior pass's candidates had to be re-encoded): verdict.md is dated Aug 14 14:07 but model.py is dated Aug 14 15:03 -- the SPEC WAS STRENGTHENED AFTER the recorded audit. The frozen build_pk_iterator now carries `Ensures(len(Result().requested) == 0)`, which did not exist when verdict.md recorded atk_8/atk_15 as verifying candidates. Per the memory note that retained attack labels carry the oracle verdict, I did NOT reuse those labels: I re-encoded both prior holes against the CURRENT spec as atk_2 (carry base.requested through while reporting restricted=False -- the old atk_8) and atk_3 (fabricate requested=PSet(pk) -- the old atk_15). BOTH NOW REJECT (weakness exit 2). The strengthening genuinely closed both previously-recorded holes; the prior verdict.md's candidate list is stale w.r.t. the frozen artifact.

COMMANDS. Same-spec (all 14, exit 0 = byte-identical spec): `python -m swebench_unified.adversary same-spec nagini django__django-16938 <D>/atk_N.py` for N=1..14 -> ALL "SAME - attack shares the bundle's exact specification". Weakness (exit 2 = rejected, exit 0 = CANDIDATE): `python -m swebench_unified.adversary weakness nagini django__django-16938 <D>/atk_N.py`. Run 3-concurrent as background jobs per the parallelism directive; every attack fully verified, no timeouts, no inconclusive results (all reached a real verifier verdict).

### PER-ATTACK RESULTS (all edit ONLY impl regions; axioms/@Pure/Requires/Ensures byte-identical):
- atk_1 PREPATCH BUG (mandatory): drop the .select_related() reset entirely, `narrowed = only_pk(base, pk)`. Impl byte-equivalent to model_prepatch.py. -> exit 2 REJECTED. => prepatch_reproduced=true; the spec independently senses the FieldError regression (G-DIFF re-derived).
- atk_2 PRIOR-CANDIDATE #1 RE-ENCODED (ungrounded-oracle echo / retention): return Fetch(False, base.requested, ...) -- report unrestricted but carry the accessor's baked-in named request set. -> exit 2 REJECTED by the new `len(Result().requested)==0`.
- atk_3 PRIOR-CANDIDATE #2 RE-ENCODED (ungrounded-oracle echo): fabricate requested=PSet(pk) outright. -> exit 2 REJECTED, same clause.
- atk_4 PARTIAL DOMAIN (sharpest A-leg probe): skip the reset exactly on the defer(pk) family, i.e. precisely the region where the REAL select_mask is empty so select_related_descend provably CANNOT raise and `not ill_formed` alone is blind. -> exit 2 REJECTED. The spec has defence in depth: the independent `Ensures(Result().restricted == False)` catches it without relying on ill_formed.
- atk_5 BOUNDARY: delete only_pk's defer(pk) empty-projection branch, unconditionally pin listed={pk}. -> exit 2 REJECTED by `Implies(base.excluding and pk in base.listed, len(Result().listed)==0)`.
- atk_6 CONTROL-FLOW EFFECT: diverging `while i >= 0: i = i + 1` before the gold return. -> exit 2 REJECTED by method-level MustTerminate(14) (consistent with the memory note that MustTerminate must sit at the method level).
- atk_7 UNGROUNDED-ORACLE ECHO: discard the accessor's membership, members=PSet(pk). -> exit 2 REJECTED by `Ensures(Result().members == base.members)` -- confirming that clause is real and load-bearing.
- atk_8 CANDIDATE (order swap): only_pk FIRST then clear_specific_request. -> exit 0 CANDIDATE, verifies 15.9s. Faithful refinement = `.only("pk").select_related()`. Materialized <D>/patch_atk_8.diff (BOTH sites), run_resolve run_ids sbu-audit-eq-a8/-a8b/-a8c/-a8d-0s2f85gd -> RESOLVED=True, COMPLETED=True, applied=True, FAIL_TO_PASS success=23 failure=0, PASS_TO_PASS success=65 failure=0. Real reason it resolves: select_related() with no args overwrites query.select_related wholesale with the bool True regardless of order, so the ill-formed pair cannot survive either ordering. NOT a weakness.
- atk_9 CANDIDATE (double reset): reset, narrow, reset again. -> exit 0 CANDIDATE, verifies 16.9s. Faithful refinement = `.select_related().only("pk").select_related()`. Materialized <D>/patch_atk_9.diff, run_ids sbu-audit-eq-a9/-a9b/-a9d-0s2f85gd -> RESOLVED=True, COMPLETED=True, applied=True, F2P 23/23, P2P 65/65. Idempotent; NOT a weakness.
- atk_10 HELPER-LEVEL: clear_specific_request only flips the flag, leaves the baked-in request set standing. -> exit 2 REJECTED by clear's own `len(Result().requested)==0`.
- atk_11 CONTROL-FLOW EFFECT (aliasing): mutate the accessor's collection in place (`base.restricted = False`) instead of cloning, contradicting QuerySet._chain() clone semantics. -> exit 2 REJECTED by the 1/2-permission frame.
- atk_12 WRONG PROJECTION CODE: narrow to pk+1 instead of the pk. -> exit 2 REJECTED.
- atk_13 HELPER-LEVEL PARTIAL DOMAIN: only_pk collapses to no-restriction whenever `q.excluding` (not only when pk in listed), over-approximating the real `field_names.difference(existing)` branch; build's chain left byte-identical to gold. -> exit 2 REJECTED.
- atk_14 CANDIDATE (state-vs-chain): bypass BOTH modeled callees and construct the result Fetch directly, reproducing the defer(pk) case split by hand. Probes whether the spec pins the STATE or merely the call chain. -> exit 0 CANDIDATE. It reaches exactly the gold post-state, so the faithful refinement IS the gold chain; materialized <D>/patch_atk_14.diff, run_id sbu-audit-eq-a14b-0s2f85gd -> RESOLVED=True, COMPLETED=True, applied=True, F2P 23/23, P2P 65/65. Confirms the spec pins the state tightly enough that a callee-bypassing impl still lands on the correct behaviour. NOT a weakness.

### A-LEG AUDIT (the assigned focus; R/I legs left to G-CONF).
model.py has ZERO @ContractOnly stubs and an EMPTY axioms region (prose only), so there is NO A-consumed leg anywhere: the proof consumes no opaque contract. Every leg is R, A-reference, or I; NO KIND-3 (unexpressible-changed-op) step. The operation that actually changed (inserting .select_related() to reset the request before the pk-only projection) is modeled DEEPLY as clear_specific_request plus the ill_formed predicate it neutralizes -- not hidden behind an axiom about the function under change. This is the correct shape and I confirm refinement.md §D's claim on this point.
The three A-reference legs check out against the base_commit source I read directly:
- A2 clear_specific_request <-> QuerySet.select_related() no-args (query.py else-branch `obj.query.select_related = True`): True is not a dict, so the compiler's `restricted = isinstance(self.query.select_related, dict)` (compiler.py:1184) is False. Model's `Result().restricted == False` + projection carried through is right. I ADDITIONALLY FALSIFIED the §3.1 interchangeability claim head-on: mapping.md asserts select_related(None) and select_related() are interchangeable because both yield a non-dict, "the only facet that matters". If false, A2 would be unfaithful. Materialized <D>/patch_a2_none.diff refining A2 to `.select_related(None).only("pk")` and RAN it: run_ids sbu-audit-eq-a2none/-a2noneb-0s2f85gd -> RESOLVED=True, applied=True, F2P 23/23, P2P 65/65. The claimed interchangeability HOLDS on the real oracle.
- A3 only_pk <-> QuerySet.only("pk") -> add_immediate_loading: verified against sql/query.py -- result is ALWAYS a keep list (defer->False, model's excluding==False) and the listed set is the named field MINUS an incoming leave-out list, so the empty-result branch on `q.excluding and pk in q.listed` mirrors the real `field_names.difference(existing)` exactly. atk_5/atk_13 confirm both sides of that split are pinned.
- A4/ill_formed <-> select_related_descend raise branch (query_utils.py:341-350): I read the real guard `restricted and select_mask and field.name in requested and field not in select_mask` and confirm ALL THREE conjuncts are carried (restricted<->restricted, select_mask-nonempty<->len(listed)>0, membership+exclusion<->f in requested and dropped(...)). The pk-never-dropped rule matches both mask builders unconditionally seeding select_mask[opts.pk] (sql/query.py:731,777). No over-approximation.
MODEL<->PATCH CORRESPONDENCE: the gold patch edits two byte-identical nested queryset_iterator helpers (python.py:82, xml_serializer.py:158) and the single modeled build_pk_iterator stands for both; my materialized patches always edited BOTH sites, and all resolve runs pass, so the one-function-for-two-sites collapse is sound here.

DOCUMENTATION DEFECTS in refinement.md (advisory; NOT soundness breaks -- they misdescribe the artifact but the correspondence claim survives):
1. §C.1 twice cites `Ensures(Result().requested == base.requested)` on build_pk_iterator and claims the postconditions "pin the result to exactly Fetch(False, base.requested, {pk})". THAT ENSURES DOES NOT EXIST -- grep of the frozen model.py returns 0 hits, and the actual clause is the OPPOSITE polarity: `Ensures(len(Result().requested) == 0)` (requested is DISCARDED, not retained). §C.1 also misdescribes `requested` as "the member set the accessor yields", conflating it with `members`. The real anti-echo grounding that does the work is `Ensures(Result().members == base.members)`, confirmed load-bearing by atk_7. Note this defect is now self-contradictory with the module docstring, which correctly states the codes are DISCARDED. Recommend rewriting §C.1 to cite members and the discard clause. (This same defect was flagged by the prior pass and is still unfixed, while the model itself moved on.)
2. Stale symbol names: §A intro references a helper `reset_select_related` that no longer exists (it is clear_specific_request); §A3/§C reference `Result().loaded == {pk}` though the frozen model carries no `loaded` field (it is the listed/excluding pair, per mapping.md §2's own load-bearing argument against a collapsed `loaded` encoding).

ENVIRONMENT NOTE (not a spec verdict, per the memory note about bucketing by reason): one atk_14 resolve attempt aborted with `NameError: name '_census' is not defined` from src/swebench_unified/harness.py -- the shared tree had an UNCOMMITTED in-flight edit (mtime 15:53, `git status` = M) that my import caught mid-write. This was a concurrent-edit race in someone else's harness change, NOT a spec or patch defect. I did not touch their edit; _census was defined at line 169 once the write settled, and I simply re-ran. The re-run and all other resolve runs completed normally. No attack or resolve run was left incomplete, so nothing here is INCONCLUSIVE.

VERDICT REASONING: 14 distinct same-spec wrong impls run (>= the required 5-6), spanning prepatch-bug, both re-encoded prior candidates, partial-domain (incl. the defer(pk) blind region), boundary (branch deletion), control-flow-effect (divergence and in-place mutation), ungrounded-oracle echo (two variants), helper-level, wrong-code, order-swap, double-reset and callee-bypass. 11 rejected. All 3 candidates had faithful patches materialized and EXECUTED through run_resolve; all 3 RESOLVED with full F2P/P2P, and the no-op negative control did NOT resolve, so those verdicts are meaningful. No verifying wrong impl whose patch fails to resolve was found => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** ATTACK OUTCOME: no diverging input found. I attacked the spec as too-strong/drifting from real repo behavior and every avenue closed under machine-checked differential testing against the reference (base_commit 1136aa5005 + patch.diff APPLIED, per the mandated reference convention).

SETUP: built two worktrees from the upstream repository at base_commit under a mktemp -d in /tmp; applied the gold patch (both hunks: python.py queryset_iterator and xml_serializer.py queryset_iterator -> getattr(obj, field.name).select_related().only("pk").iterator()) to the reference worktree; left the second unpatched purely as the negative control. Worktrees removed after.

### PROBES RUN (all against the REAL ORM, callees executed not transliterated):
1. ill_formed vs real select_related_descend raise branch, on ARBITRARY (unbuilt) query states: 384 cases (select_related in {absent,noargs,None,every non-empty FK subset} x projection in {absent, only/defer over every subset of concrete fields}), compared model ill_formed against whether the real compiler.as_sql() raises FieldError. RESULT: 0/384 disagreements. All three real guard conjuncts (restricted, non-empty select_mask, requested-and-dropped) are present in the model; the len(listed)>0 conjunct is genuinely needed and genuinely there.
2. Full build_pk_iterator differential using the BUNDLE'S EXACT alpha (conformance_check.py:418-430) over 5952 cases, including CHAINED projection operations (only/defer composed twice) which the bundle's own G-CONF domain does NOT enumerate, plus non-null FKs and multi-FK models. Diffed listed, excluding, restricted, requested, effective loaded set (vs real get_select_mask), and ill_formed vs real raise. RESULT: 0 divergences.
3. Attacked the headline never-errors postcondition (not ill_formed(Result()...)) with shapes designed to reach the raise branch in unrestricted mode: multi-table-inheritance parent_link FKs, non-null FK chains of depth 2-3, self-referential non-null FKs, select_related('l2__l3'), select_related('parentm_ptr'). The built chain compiled cleanly in every configuration. RESULT: no error found; guarantee holds. (Mechanism confirmed sound: select_related() sets query.select_related = True, a bool, so compiler's restricted = isinstance(..., dict) is False and the raise branch is unreachable regardless of projection.)
4. Attacked the members == base.members clause end-to-end through the real patched serializer with custom managers baking in select_related/filter/distinct/order_by, capturing the built queryset at the unchanged QuerySet.iterator boundary. Membership preserved in every case. The one apparent mismatch (manager baking in .filter) is the ACCESSOR's own narrowing: base.members is [1,3] and built.members is [1,3] — the clause is relative to base, exactly as the spec text scopes it ("inherits the owning record's membership filter unchanged").
5. Attacked the only_pk defer(pk) case split, the family the bundle documents as historically mis-attributed. Confirmed the real asymmetry in add_immediate_loading (sql/query.py:2336-2358): it normalizes literal "pk" -> pk.name, while add_deferred_loading does NOT. So a defer("id") base yields built deferred_loading (set(), False) / empty mask / all columns, whereas a defer("pk") base yields ({'id'}, False) / mask {id}. The model's case split on (q.excluding and pk in q.listed) reproduces the defer(real-pk-name) branch correctly.

ONE FALSE POSITIVE I RAISED AND THEN KILLED (recorded for honesty): I initially found 5 divergences on defer("pk")-family bases where the model predicted no-restriction but the real built query restricted to {id}. This was MY OWN alpha bug, not a spec defect. I had invented an alpha collapsing literal "pk" and the real pk name "id" onto one code; the bundle's actual alpha maps field NAMES through CODE = {name: i for concrete_fields}, and literal "pk" is not in CODE, so a defer("pk") base abstracts to listed=[] — which is SOUND, because a defer("pk") base is itself an incoherent Django state (its own get_select_mask() raises FieldDoesNotExist: Tag has no field named 'pk'), and its built result is identical to a plain base's. Re-running the identical 43-case sweep under the bundle's real alpha gave 0 divergences. Per my own standing note, a measurement of spec weakness that is really my parse/bridge bug must not be reported as a finding.

GATES REPRODUCED INDEPENDENTLY: nagini_verify.sh on model.py -> "Verification successful" (14.1s, exit 0). axiom_check.py against base_commit -> G-AX OK. conformance_check.py against my own patched worktree -> pass, 100000 inputs, 0 disagreements, requested_keyset_mismatches 0. Negative control on the UNPATCHED base -> fail, 69870 disagreements dominated by well_formedness+restricted (52894): the gate is falsifiable, not vacuous. model_prepatch.py -> "Verification failed" on exactly the discriminating clause (pp.py:233 Postcondition ... not ill_formed(...) might not hold), so the spec senses the bug. same-spec harness sanity-checked SAME on an identity copy.

SPEC-STRENGTH ASSESSMENT: the spec is strong but not stronger than the real fixed behavior. Every postcondition is discharged by the real patched chain on all inputs I could construct. The reset is modeled as wholesale discard (len(requested)==0), which I verified is what the real select_related() does — it replaces the dict with the bool True, discarding the keys — so this clause is faithful, not over-strong.

MINOR DOCUMENTATION DEFECT (not a faithfulness break, does not change the verdict): refinement.md C.1 twice asserts the spec "Ensures(Result().requested == base.requested)" and reasons that this grounds the result by PRESERVING the requested set. model.py actually ensures len(Result().requested) == 0, i.e. the opposite (discard). The MODEL is the faithful one (real select_related() discards the keys — probe 13 confirms select_related={'master': {}} becomes select_related=True); the refinement.md C.1 prose is stale relative to the current model, and its "the two postconditions together pin the result to exactly Fetch(False, base.requested, {pk})" sentence is wrong on the requested facet. mapping.md's MODELING NOTE and the G-CONF section already describe the discard correctly, so this is an internal inconsistency in one document's prose, not in the verified artifact. Worth a doc fix; no bearing on soundness.

CONCLUSION: FAITHFUL. I could not exhibit any input on which the modeled function disagrees with the real patched callee. No diverging_input is claimed, so no defect is asserted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: leakage / gold-reconstruction only. Judged the EXACT shipped consumer view: derived spec_view(model.py) via swebench_unified.markers and confirmed byte-equality with what eval/adapter.py:spec_view() exposes (`judged view == adapter view: True`), with all 3 impl regions elided (`implementation elided` x3, no `PSet(pk) - PSet(pk)`, no `clear_specific_request(base)` composition visible). Baseline same-spec on an unmodified copy exits 0.

GOLD EDIT: insert `.select_related()` before `.only("pk")` in queryset_iterator, in BOTH django/core/serializers/python.py and xml_serializer.py.

MECHANICAL: leakage.screen(nagini flavor, gold patch + PS, no hints) => PASSED, 0 hard failures, 0 warnings. All five sub-rules clear: no diff marker; no gold changed line reproduced (checked all 8, incl. `getattr(obj, field.name).select_related().only("pk").iterator()`); neither patched path nor dotted module path present; patched symbols {m2m_value, handle_m2m} absent from identifiers AND comments (both are public in PS anyway via the traceback); no _NARRATION hit.

LEXICAL DE-COUPLING (manual, beyond the mechanical list): spec view contains NONE of select_related / selectrelated / .only / only( / iterator() / queryset_iterator / getattr / m2m / manytomany / prefetch / FieldError / deferred / defer( / manager / get_queryset / queryset / master / topic / 19e0587 / 33937. Notably the hints-ONLY tokens (pk-as-getattr, queryset_iterator, 'clear') are absent as repo vocabulary. Only snake/camel tokens in the view are model-local (Fetch, build_pk_iterator, clear_specific_request, only_pk, ill_formed, dropped) plus framework imports (nagini_contracts, MustTerminate, ContractOnly) and the instance-id header `django__django-16938`. 'serializ*' appears but 'Serialization of m2m relation fails' is the PS TITLE; 'django' appears only inside the instance id the consumer is already given. No edit-localization: no file path, no `.py:`, no 'xml', no hint that TWO sites change (the two byte-identical hunks are collapsed into one modeled function, and that fan-out lives in meta.json/mapping.md, not the spec view).

CLOSEST CALL (examined, judged NOT leakage): the docstring's 'That reset is wholesale rather than selective: the built fetch falls back on the unrestricted default and NAMES NO adjacent-record code at all, so the specific codes ... are DISCARDED rather than carried along, narrowed or reshuffled', backed by `Ensures(Result().restricted == False)` + `Ensures(len(Result().requested) == 0)`. This is semantically close to the hints_text suggestion ('Maybe we could clear select_related()').

I judge NO-LEAKAGE because (a) it is stated purely as the required POST-STATE of an abstracted 3-facet Fetch, i.e. the 'element i of the result is f(...)' contract style G-LEAK explicitly asks for, never as bug->fix mechanism, diagnosis, or edit; (b) it is de-lexicalized -- a solver must still discover WHICH API produces a wholesale reset, in WHICH function, in HOW MANY files; (c) the PS itself is unusually explicit (full traceback through select_related_descend, the FieldError text 'cannot be both deferred and traversed using select_related at the same time', the custom-manager select_related reproducer, and the 'set a simple default manager' workaround), so the conflict-to-be-avoided is already public -- the spec view adds no non-public diagnosis; (d) omitting the wholesale/discarding clause would gut spec strength and hand G-PANEL-1 a carry-along/narrow counterexample, so this precision is soundness-mandated, not lazy de-narration. No relaxed-leakage claim is needed: the spec is both faithful and non-leaking.

No LEAKAGE finding; no leaking_line to report.

OUT-OF-LANE OBSERVATION (not leakage, flagged for construction hygiene, NOT a G-PANEL-3 failure): meta.json region_hashes are STALE -- stored impl/pure/pre-conditions/post-conditions/spec_view hashes do not match live region_hashes(model.py) under either the backend or backend.language tables form (only 'axioms' matches); model_prepatch.py mismatches identically, so it is not a model/prepatch mix-up. Harmless for leakage because the shipped view is derived LIVE from model.py (which I verified directly), and adapter.spec_view() hard-guards elision independently of these hashes. Worth a hygiene re-stamp by whoever owns G-HYGIENE/G-INTEGRITY.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
