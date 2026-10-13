# P2 adversarial audit — django__django-16493

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # implementation is pinned on every input (no excluded corner admits
     # divergent behaviour).
     Requires(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The field is left exactly as it was (read-only).
@@ -123,12 +121,12 @@
     Ensures(Implies(self.has_producer, Result()[1] == self.producer_id))
     # post-conditions-end
     # impl-start
-    # Compute the value to report first (producer if present, else store),
-    # then decide inclusion from that same value.
+    # ATTACK1 (prepatch bug): inclusion decided from the concrete store, not
+    # from the reported value.
     if self.has_producer:
         value = self.producer_id
     else:
         value = self.store_id
-    included = value != default_store_id()
+    included = self.store_id != default_store_id()
     return (included, value)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # implementation is pinned on every input (no excluded corner admits
     # divergent behaviour).
     Requires(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The field is left exactly as it was (read-only).
@@ -123,12 +121,10 @@
     Ensures(Implies(self.has_producer, Result()[1] == self.producer_id))
     # post-conditions-end
     # impl-start
-    # Compute the value to report first (producer if present, else store),
-    # then decide inclusion from that same value.
+    # ATTACK2 (partial-domain / always-include): always report inclusion.
     if self.has_producer:
         value = self.producer_id
     else:
         value = self.store_id
-    included = value != default_store_id()
-    return (included, value)
+    return (True, value)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # implementation is pinned on every input (no excluded corner admits
     # divergent behaviour).
     Requires(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The field is left exactly as it was (read-only).
@@ -123,12 +121,11 @@
     Ensures(Implies(self.has_producer, Result()[1] == self.producer_id))
     # post-conditions-end
     # impl-start
-    # Compute the value to report first (producer if present, else store),
-    # then decide inclusion from that same value.
+    # ATTACK3 (boundary / flipped comparison): inclusion iff value IS default.
     if self.has_producer:
         value = self.producer_id
     else:
         value = self.store_id
-    included = value != default_store_id()
+    included = value == default_store_id()
     return (included, value)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # implementation is pinned on every input (no excluded corner admits
     # divergent behaviour).
     Requires(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The field is left exactly as it was (read-only).
@@ -123,12 +121,12 @@
     Ensures(Implies(self.has_producer, Result()[1] == self.producer_id))
     # post-conditions-end
     # impl-start
-    # Compute the value to report first (producer if present, else store),
-    # then decide inclusion from that same value.
+    # ATTACK4 (control-flow-effect / swapped branches): report store when a
+    # producer is held, producer otherwise.
     if self.has_producer:
+        value = self.store_id
+    else:
         value = self.producer_id
-    else:
-        value = self.store_id
     included = value != default_store_id()
     return (included, value)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # implementation is pinned on every input (no excluded corner admits
     # divergent behaviour).
     Requires(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The field is left exactly as it was (read-only).
@@ -123,12 +121,11 @@
     Ensures(Implies(self.has_producer, Result()[1] == self.producer_id))
     # post-conditions-end
     # impl-start
-    # Compute the value to report first (producer if present, else store),
-    # then decide inclusion from that same value.
+    # ATTACK5 (ungrounded-oracle echo / constant include-flag): compute the
+    # right value but hard-omit always.
     if self.has_producer:
         value = self.producer_id
     else:
         value = self.store_id
-    included = value != default_store_id()
-    return (included, value)
+    return (False, value)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import Optional, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -92,7 +91,6 @@
     # implementation is pinned on every input (no excluded corner admits
     # divergent behaviour).
     Requires(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The field is left exactly as it was (read-only).
@@ -123,12 +121,9 @@
     Ensures(Implies(self.has_producer, Result()[1] == self.producer_id))
     # post-conditions-end
     # impl-start
-    # Compute the value to report first (producer if present, else store),
-    # then decide inclusion from that same value.
-    if self.has_producer:
-        value = self.producer_id
-    else:
-        value = self.store_id
+    # ATTACK6 (partial-domain / ignore has_producer for value): always report
+    # the producer id.
+    value = self.producer_id
     included = value != default_store_id()
     return (included, value)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16493.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configurable file-store attribute on a field may be supplied either as a
  concrete store, or as a deferred producer (a callable) that is evaluated once
  at construction time to obtain the concrete store. When the field is later
  reduced to its reconstructible form, the store attribute must be reported
  faithfully so the field can be rebuilt identically:

    * if a deferred producer was supplied, the reconstructible form must carry
      the PRODUCER itself (so the deferral is preserved on rebuild), never the
      already-evaluated concrete store;
    * if no producer was supplied, the reconstructible form carries the
      concrete store directly.

  In either case the store attribute is OMITTED from the reconstructible form
  exactly when the value that WOULD be reported is the canonical default store
  (the one a freshly built field assumes when nothing is supplied) -- because
  that value is then redundant and is re-supplied automatically on rebuild.

  The decisive point: the include/omit test and the reported value must be
  taken from the SAME quantity -- the value that will actually be reported
  (the producer when one exists, else the concrete store). The specification
  is TOTAL: it pins the result on every field configuration and assumes
  nothing about which identities may coincide. In the real repository a held
  producer is never the canonical default store (a producer is a callable,
  the default store a concrete store instance), so on all reachable states a
  field built from a producer is always reported -- even when that producer
  happens to evaluate to the default store. The general include-iff-non-default
  rule specialises to exactly that behaviour there.

The reduction is read-only: it observes the field's attributes and does not
mutate them. Object identities (the canonical default store, the concrete
store, the producer) are modelled as integer identity tags; equality of tags
means object identity. The presence/absence of a producer is a boolean. No
callee is axiomatized: the behaviour is pure identity/decision logic, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional, Tuple
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the reduction is pure identity/decision logic (an
# attribute-presence lookup plus two object-identity comparisons), modelled
# deeply. There is no opaque library callee under specification here.
# axioms-end


# pure-start
@Pure
def default_store_id() -> int:
    """Identity tag of the canonical default store (the sentinel a field
    assumes when nothing is supplied). A single distinguished constant."""
    return 0


@Pure
def reported_value(has_producer: bool, producer_id: int, store_id: int) -> int:
    """The store identity that the reconstructible form reports: the deferred
    producer when one was supplied, otherwise the concrete store."""
    if has_producer:
        return producer_id
    return store_id
# pure-end


class FileBackedField:
    def __init__(self) -> None:
        # Constructor of the minimal field stand-in (no marked spec region: the
        # modeled changed behaviour is `deconstruct_storage` below). A freshly
        # built field with nothing supplied carries the canonical default store
        # and holds no producer.
        Ensures(Acc(self.store_id) and Acc(self.has_producer) and Acc(self.producer_id))  # type: ignore
        Ensures(self.store_id == default_store_id())  # type: ignore
        Ensures(self.has_producer == False)  # type: ignore
        Ensures(self.producer_id == default_store_id())  # type: ignore
        self.store_id = default_store_id()  # type: int
        self.has_producer = False  # type: bool
        self.producer_id = default_store_id()  # type: int


def deconstruct_storage(self: FileBackedField) -> Tuple[bool, int]:
    # pre-conditions-start
    # The field is read-only throughout the reduction: its attributes are
    # required (and ensured) only at fractional permission. The specification
    # is TOTAL: no field configuration is excluded, so a verifying
    # implementation is pinned on every input (no excluded corner admits
    # divergent behaviour).
    Requires(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The field is left exactly as it was (read-only).
    Ensures(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
    Ensures(self.store_id == Old(self.store_id))
    Ensures(self.has_producer == Old(self.has_producer))
    Ensures(self.producer_id == Old(self.producer_id))

    # The result is (included, value):
    #   `value` is the quantity that would be reported -- the producer when one
    #   was supplied, otherwise the concrete store -- and is meaningful whenever
    #   the store attribute is included.
    Ensures(Result()[1] == reported_value(self.has_producer, self.producer_id, self.store_id))
    #   the store attribute is included exactly when that SAME reported value is
    #   not the canonical default store. (Both the test and the value derive
    #   from the one reported quantity.)
    Ensures(Result()[0] == (reported_value(self.has_producer, self.producer_id, self.store_id) != default_store_id()))
    # Discriminating consequence (implied by the two clauses above; restated
    # for emphasis): whenever a producer is held, the producer itself is the
    # reported value, and -- since on every reachable real-world state a held
    # producer is a distinct object from the canonical default store -- the
    # field is then reported even when the producer evaluates to the default
    # store. Stated conditionally so the spec stays total and consistent on
    # ALL inputs, including the real-world-unreachable coincidence
    # producer == default store (where the general include-iff-non-default
    # rule above still pins the result exactly).
    Ensures(Implies(self.has_producer and self.producer_id != default_store_id(), Result()[0]))
    Ensures(Implies(self.has_producer, Result()[1] == self.producer_id))
    # post-conditions-end
    # impl-start
    # Compute the value to report first (producer if present, else store),
    # then decide inclusion from that same value.
    if self.has_producer:
        value = self.producer_id
    else:
        value = self.store_id
    included = value != default_store_id()
    return (included, value)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-16493 (nagini). Bundle spec pins Result() EXACTLY as a total function of the three field attributes via two equality postconditions:
  (P1) Result()[1] == reported_value(has_producer, producer_id, store_id)   [= producer_id if has_producer else store_id]
  (P2) Result()[0] == (reported_value(...) != default_store_id())
The only precondition is read-only fractional permission (Acc(...,1/2)) on the three attrs, so the domain is TOTAL — every (bool,int,int) triple is Requires-satisfying and no corner is excluded. P1+P2 therefore leave zero behavioural freedom for a verifying impl.

RUN LAYOUT: module driven with python -m swebench_unified.adversary and SBU_BENCHMARK_DIR=benchmark-verified (the nagini venv lacks the package; the lean venv carries swebench_unified). Attacks built by copying nagini/model.py and editing ONLY the impl region (lines 124-131); axioms/@Pure/Requires/Ensures left byte-identical — confirmed same-spec on all 6 (exit 0) and on pos_control.

atk_1.py PREPATCH BUG (inclusion from self.store_id, not reported value): same-spec YES; weakness -> NOT-A-COUNTEREXAMPLE, verification failed. Reproduces the pre-fix guard; spec rejects it (P2 violated on producer-returns-default). prepatch_reproduced=true.
- atk_2.py partial-domain / always-include (return (True, value)): rejected, verification failed (P2 violated when reported value == default).
- atk_3.py boundary / flipped comparison (included = value == default): rejected, verification failed (P2 negated).
- atk_4.py control-flow-effect / swapped branches (value = store when producer held, else producer): rejected, verification failed (P1 violated).
- atk_5.py ungrounded-oracle echo / constant flag (return (False, value)): rejected, verification failed (P2 violated on non-default).
- atk_6.py partial-domain / ignore has_producer (value = producer_id always): rejected, verification failed (P1 violated when !has_producer and producer_id != store_id).
POSITIVE CONTROL pos_control.py (gold impl region verbatim): weakness -> CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (12.9s) — confirms the harness/verifier are live and the correct impl does verify. (It is the gold, so it resolves; not a weakness.)

No attack came back a CANDIDATE (none shares-spec-AND-verifies), so there is no verifying wrong impl whose faithful refined patch needs to be materialized and run through run_resolve; patches={} accordingly. All >=5 falsification attempts completed with machine-checked results.

REFINEMENT.MD AUDIT: axioms region is empty (comment-only lines 46-50) — NO @ContractOnly callee. mapping.md §3 and refinement.md's closing section both confirm no axioms (G-AX vacuous). All 4 operation-correspondence legs are tagged R (leg 3 is R+I); NO A-consumed / A-reference legs to audit and NO kind-3 (unexpressible-changed-op) steps. Legs 2-3 encode the actual gold fix (reported value = getattr(self,'_storage_callable',self.storage); guard tested on that same value) and correspond faithfully to patch.diff's reorder at files.py:298-299. Totalization covers the real-world-unreachable corner (has_producer && producer_id==0) with the same include-iff-reported-value-non-default rule the gold computes there, adding no divergence and leaving no vacuous hiding corner.

VERDICT: SOUND. Spec is tight (exactly pins Result over a total domain); 6 distinct wrong impls (incl. the prepatch bug) all fail verification; positive control verifies; refinement.md is all-R/I with faithful correspondence and no axioms. verify -> correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16493.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configurable file-store attribute on a field may be supplied either as a
  concrete store, or as a deferred producer (a callable) that is evaluated once
  at construction time to obtain the concrete store. When the field is later
  reduced to its reconstructible form, the store attribute must be reported
  faithfully so the field can be rebuilt identically:

    * if a deferred producer was supplied, the reconstructible form must carry
      the PRODUCER itself (so the deferral is preserved on rebuild), never the
      already-evaluated concrete store;
    * if no producer was supplied, the reconstructible form carries the
      concrete store directly.

  In either case the store attribute is OMITTED from the reconstructible form
  exactly when the value that WOULD be reported is the canonical default store
  (the one a freshly built field assumes when nothing is supplied) -- because
  that value is then redundant and is re-supplied automatically on rebuild.

  The decisive point: the include/omit test and the reported value must be
  taken from the SAME quantity -- the value that will actually be reported
  (the producer when one exists, else the concrete store). The specification
  is TOTAL: it pins the result on every field configuration and assumes
  nothing about which identities may coincide. In the real repository a held
  producer is never the canonical default store (a producer is a callable,
  the default store a concrete store instance), so on all reachable states a
  field built from a producer is always reported -- even when that producer
  happens to evaluate to the default store. The general include-iff-non-default
  rule specialises to exactly that behaviour there.

The reduction is read-only: it observes the field's attributes and does not
mutate them. Object identities (the canonical default store, the concrete
store, the producer) are modelled as integer identity tags; equality of tags
means object identity. The presence/absence of a producer is a boolean. No
callee is axiomatized: the behaviour is pure identity/decision logic, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional, Tuple
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the reduction is pure identity/decision logic (an
# attribute-presence lookup plus two object-identity comparisons), modelled
# deeply. There is no opaque library callee under specification here.
# axioms-end


# pure-start
@Pure
def default_store_id() -> int:
    """Identity tag of the canonical default store (the sentinel a field
    assumes when nothing is supplied). A single distinguished constant."""
    return 0


@Pure
def reported_value(has_producer: bool, producer_id: int, store_id: int) -> int:
    """The store identity that the reconstructible form reports: the deferred
    producer when one was supplied, otherwise the concrete store."""
    if has_producer:
        return producer_id
    return store_id
# pure-end


class FileBackedField:
    def __init__(self) -> None:
        # Constructor of the minimal field stand-in (no marked spec region: the
        # modeled changed behaviour is `deconstruct_storage` below). A freshly
        # built field with nothing supplied carries the canonical default store
        # and holds no producer.
        Ensures(Acc(self.store_id) and Acc(self.has_producer) and Acc(self.producer_id))  # type: ignore
        Ensures(self.store_id == default_store_id())  # type: ignore
        Ensures(self.has_producer == False)  # type: ignore
        Ensures(self.producer_id == default_store_id())  # type: ignore
        self.store_id = default_store_id()  # type: int
        self.has_producer = False  # type: bool
        self.producer_id = default_store_id()  # type: int


def deconstruct_storage(self: FileBackedField) -> Tuple[bool, int]:
    # pre-conditions-start
    # The field is read-only throughout the reduction: its attributes are
    # required (and ensured) only at fractional permission. The specification
    # is TOTAL: no field configuration is excluded, so a verifying
    # implementation is pinned on every input (no excluded corner admits
    # divergent behaviour).
    Requires(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The field is left exactly as it was (read-only).
    Ensures(Acc(self.store_id, 1 / 2) and Acc(self.has_producer, 1 / 2) and Acc(self.producer_id, 1 / 2))
    Ensures(self.store_id == Old(self.store_id))
    Ensures(self.has_producer == Old(self.has_producer))
    Ensures(self.producer_id == Old(self.producer_id))

    # The result is (included, value):
    #   `value` is the quantity that would be reported -- the producer when one
    #   was supplied, otherwise the concrete store -- and is meaningful whenever
    #   the store attribute is included.
    Ensures(Result()[1] == reported_value(self.has_producer, self.producer_id, self.store_id))
    #   the store attribute is included exactly when that SAME reported value is
    #   not the canonical default store. (Both the test and the value derive
    #   from the one reported quantity.)
    Ensures(Result()[0] == (reported_value(self.has_producer, self.producer_id, self.store_id) != default_store_id()))
    # Discriminating consequence (implied by the two clauses above; restated
    # for emphasis): whenever a producer is held, the producer itself is the
    # reported value, and -- since on every reachable real-world state a held
    # producer is a distinct object from the canonical default store -- the
    # field is then reported even when the producer evaluates to the default
    # store. Stated conditionally so the spec stays total and consistent on
    # ALL inputs, including the real-world-unreachable coincidence
    # producer == default store (where the general include-iff-non-default
    # rule above still pins the result exactly).
    Ensures(Implies(self.has_producer and self.producer_id != default_store_id(), Result()[0]))
    Ensures(Implies(self.has_producer, Result()[1] == self.producer_id))
    # post-conditions-end
    # impl-start
    # Compute the value to report first (producer if present, else store),
    # then decide inclusion from that same value.
    if self.has_producer:
        value = self.producer_id
    else:
        value = self.store_id
    included = value != default_store_id()
    return (included, value)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-16493 (nagini). Bundle spec pins Result() EXACTLY as a total function of the three field attributes via two equality postconditions:
  (P1) Result()[1] == reported_value(has_producer, producer_id, store_id)   [= producer_id if has_producer else store_id]
  (P2) Result()[0] == (reported_value(...) != default_store_id())
The only precondition is read-only fractional permission (Acc(...,1/2)) on the three attrs, so the domain is TOTAL — every (bool,int,int) triple is Requires-satisfying and no corner is excluded. P1+P2 therefore leave zero behavioural freedom for a verifying impl.

RUN LAYOUT: module driven with python -m swebench_unified.adversary and SBU_BENCHMARK_DIR=benchmark-verified (the nagini venv lacks the package; the lean venv carries swebench_unified). Attacks built by copying nagini/model.py and editing ONLY the impl region (lines 124-131); axioms/@Pure/Requires/Ensures left byte-identical — confirmed same-spec on all 6 (exit 0) and on pos_control.

atk_1.py PREPATCH BUG (inclusion from self.store_id, not reported value): same-spec YES; weakness -> NOT-A-COUNTEREXAMPLE, verification failed. Reproduces the pre-fix guard; spec rejects it (P2 violated on producer-returns-default). prepatch_reproduced=true.
- atk_2.py partial-domain / always-include (return (True, value)): rejected, verification failed (P2 violated when reported value == default).
- atk_3.py boundary / flipped comparison (included = value == default): rejected, verification failed (P2 negated).
- atk_4.py control-flow-effect / swapped branches (value = store when producer held, else producer): rejected, verification failed (P1 violated).
- atk_5.py ungrounded-oracle echo / constant flag (return (False, value)): rejected, verification failed (P2 violated on non-default).
- atk_6.py partial-domain / ignore has_producer (value = producer_id always): rejected, verification failed (P1 violated when !has_producer and producer_id != store_id).
POSITIVE CONTROL pos_control.py (gold impl region verbatim): weakness -> CANDIDATE-COUNTEREXAMPLE, shares spec AND verifies (12.9s) — confirms the harness/verifier are live and the correct impl does verify. (It is the gold, so it resolves; not a weakness.)

No attack came back a CANDIDATE (none shares-spec-AND-verifies), so there is no verifying wrong impl whose faithful refined patch needs to be materialized and run through run_resolve; patches={} accordingly. All >=5 falsification attempts completed with machine-checked results.

REFINEMENT.MD AUDIT: axioms region is empty (comment-only lines 46-50) — NO @ContractOnly callee. mapping.md §3 and refinement.md's closing section both confirm no axioms (G-AX vacuous). All 4 operation-correspondence legs are tagged R (leg 3 is R+I); NO A-consumed / A-reference legs to audit and NO kind-3 (unexpressible-changed-op) steps. Legs 2-3 encode the actual gold fix (reported value = getattr(self,'_storage_callable',self.storage); guard tested on that same value) and correspond faithfully to patch.diff's reorder at files.py:298-299. Totalization covers the real-world-unreachable corner (has_producer && producer_id==0) with the same include-iff-reported-value-non-default rule the gold computes there, adding no divergence and leaving no vacuous hiding corner.

VERDICT: SOUND. Spec is tight (exactly pins Result over a total domain); 6 distinct wrong impls (incl. the prepatch bug) all fail verification; positive control verifies; refinement.md is all-R/I with faithful correspondence and no axioms. verify -> correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for django__django-16493 nagini bundle. The modeled function deconstruct_storage models FileField.deconstruct()'s storage-kwarg decision (post-patch): storage = getattr(self,'_storage_callable', self.storage); if storage is not default_storage: kwargs['storage']=storage. Confirmed model.py verifies (nagini_verify.sh exit 0, 10.8s) and its spec region is byte-identical to the bundle (same-spec exit 0). Verified the real repo at base_commit (files.py:293-300, __init__ 235-254). Under the mapping (store_id<->self.storage, has_producer<->hasattr _storage_callable, producer_id<->_storage_callable, default_store_id()==0<->default_storage), the modeled reported_value = producer_id if has_producer else store_id exactly matches getattr(self,'_storage_callable', self.storage), and included = reported_value != default matches 'is not default_storage'. Checked all four reachable configs + the unreachable corner (has_producer && producer_id==default): model gives (False,default), which is exactly what the gold callee computes on that hypothetical state (getattr->default, guard false, omit) -- so totalization adds NO divergence anywhere. The spec is total (only read-only fractional-permission precondition) so no vacuous corner exists; it agrees with the real callee on every input, including the discriminating F2P case test_deconstruction_storage_callable_default (producer that returns default_storage: model includes producer, matches fixed repo). No input found where the modeled function disagrees with the real post-patch callee. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, zero hard failures). Semantic review of the spec view (model.py, comments/docstrings included) confirms no leakage beyond the public problem_statement.

Public problem_statement already discloses: (a) the buggy method is `deconstruct` on FileField; (b) it wrongly omits `storage` when a callable returns default_storage; (c) root cause is testing `self.storage is not default_storage` where self.storage is the already-EVALUATED store; (d) expected behavior is to include a reference to the callable.

The spec view restates only this same desired behavior at an abstract level: a store may be supplied as a concrete store or a 'deferred producer' (callable); the reconstructible form must report the producer when one was supplied; omit when the reported value equals the canonical default store; and the include/omit test must derive from the SAME reported quantity. This 'same quantity' framing is a spec-level necessity that the problem statement itself surfaces (it explains the bug is that the guard tests the wrong quantity).

Crucially, the spec view does NOT reveal the gold EDIT mechanism, which lives only in the non-public hints_text ('use getattr(self, "_storage_callable", self.storage) in both lines'). model.py contains none of: `_storage_callable`, `getattr`, the patched file path `django/db/models/fields/files.py`, `kwargs`, or `is not default_storage`. No gold-patch line is reproduced (checked _patch_changed_lines vs view_norm), no diff markers, no patched module path. The only patch-touched def/class symbol is `deconstruct`, which is already present verbatim in the public problem_statement. Carriers are abstract identity tags (store_id/has_producer/producer_id/reported_value/default_store_id). No narration of the edit. Judged against problem_statement ONLY, not hints_text.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
