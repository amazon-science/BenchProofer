# P2 adversarial audit — django__django-14238

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Cls:
@@ -67,7 +66,6 @@
     Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
     Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
     Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
@@ -82,9 +80,9 @@
                          or is_subtype(candidate, owner)))
     # post-conditions-end
     # impl-start
-    if is_subtype(candidate, base_one):
+    if candidate.cid == base_one.cid:  # type: ignore
         return True
-    if is_subtype(candidate, base_two):
+    if candidate.cid == base_two.cid:  # type: ignore
         return True
     return is_subtype(candidate, owner)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Cls:
@@ -67,7 +66,6 @@
     Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
     Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
     Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
@@ -84,7 +82,5 @@
     # impl-start
     if is_subtype(candidate, base_one):
         return True
-    if is_subtype(candidate, base_two):
-        return True
     return is_subtype(candidate, owner)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Cls:
@@ -67,7 +66,6 @@
     Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
     Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
     Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
@@ -82,9 +80,5 @@
                          or is_subtype(candidate, owner)))
     # post-conditions-end
     # impl-start
-    if is_subtype(candidate, base_one):
-        return True
-    if is_subtype(candidate, base_two):
-        return True
     return is_subtype(candidate, owner)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Cls:
@@ -67,7 +66,6 @@
     Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
     Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
     Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
@@ -82,9 +80,5 @@
                          or is_subtype(candidate, owner)))
     # post-conditions-end
     # impl-start
-    if is_subtype(candidate, base_one):
-        return True
-    if is_subtype(candidate, base_two):
-        return True
-    return is_subtype(candidate, owner)
+    return True
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Cls:
@@ -67,7 +66,6 @@
     Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
     Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
     Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
@@ -82,9 +80,7 @@
                          or is_subtype(candidate, owner)))
     # post-conditions-end
     # impl-start
-    if is_subtype(candidate, base_one):
-        return True
-    if is_subtype(candidate, base_two):
-        return True
-    return is_subtype(candidate, owner)
+    return (is_subtype(base_one, candidate)
+            or is_subtype(base_two, candidate)
+            or is_subtype(owner, candidate))
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Cls:
@@ -67,7 +66,6 @@
     Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
     Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
     Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
@@ -82,9 +80,7 @@
                          or is_subtype(candidate, owner)))
     # post-conditions-end
     # impl-start
-    if is_subtype(candidate, base_one):
-        return True
-    if is_subtype(candidate, base_two):
-        return True
-    return is_subtype(candidate, owner)
+    return (is_subtype(candidate, base_one)
+            and is_subtype(candidate, base_two)
+            and is_subtype(candidate, owner))
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Cls:
@@ -67,7 +66,6 @@
     Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
     Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
     Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
@@ -84,7 +82,5 @@
     # impl-start
     if is_subtype(candidate, base_one):
         return True
-    if is_subtype(candidate, base_two):
-        return True
-    return is_subtype(candidate, owner)
+    return is_subtype(candidate, base_two)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Cls:
@@ -67,7 +66,6 @@
     Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
     Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
     Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
@@ -82,9 +80,7 @@
                          or is_subtype(candidate, owner)))
     # post-conditions-end
     # impl-start
-    if is_subtype(candidate, base_one):
-        return True
-    if is_subtype(candidate, base_two):
-        return True
-    return is_subtype(candidate, owner)
+    return (candidate.cid == base_one.cid  # type: ignore
+            or candidate.cid == base_two.cid  # type: ignore
+            or candidate.cid == owner.cid)  # type: ignore
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14238.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A metaclass maintains a small, immutable family of registered "generated-key"
  base classes and answers the structural-subtype question for the type it is
  attached to.  Given a candidate class, the membership test must report TRUE
  exactly when the candidate stands in the subtype relation to AT LEAST ONE of
  the registered base classes, OR when the candidate is a subtype of the
  attached type itself by the ordinary class hierarchy.

  Crucially, this is a *subtype* relation, not an identity check: a candidate
  that derives (transitively) from one of the registered bases must be reported
  as a member even when the candidate is not itself one of those exact base
  classes.  Equivalently, the relation is reflexive and downward-closed under
  inheritance from the registered bases, so a user-defined class extending a
  registered base is recognised just as the base itself is.

A class is modelled abstractly by its identity together with the set of the
identities of all the classes it derives from (its ancestry, which by the
reflexivity of the subtype relation contains its own identity).  The subtype
relation `is_subtype(c, b)` holds iff `b`'s identity lies in `c`'s ancestry —
exactly the semantics of the ordinary `issubclass` query, which the membership
test consults against each registered base.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Cls:
    """A class abstracted by its identity `cid` and the set `anc` of identities
    of all classes it derives from (its ancestry).  The subtype relation is
    reflexive, so `cid in anc` always holds."""

    def __init__(self, cid: int, anc: PSet[int]) -> None:
        Requires(cid in anc)
        Ensures(Acc(self.cid) and Acc(self.anc))  # type: ignore
        Ensures(self.cid == cid and self.anc is anc)  # type: ignore
        Ensures(self.cid in self.anc)  # type: ignore
        self.cid = cid  # type: ignore
        self.anc = anc  # type: ignore


# axioms-start
# (No axiomatized callees: the structural-subtype query is modelled deeply.)
# axioms-end


# pure-start
@Pure
def is_subtype(sub: Cls, base: Cls) -> bool:
    """The ordinary structural-subtype query: `sub` is a subtype of `base` iff
    `base`'s identity lies in `sub`'s ancestry.  Reflexive (every class is its
    own subtype) and transitive by construction of the ancestry set."""
    Requires(Acc(sub.cid, 1 / 8) and Acc(sub.anc, 1 / 8))  # type: ignore
    Requires(Acc(base.cid, 1 / 8) and Acc(base.anc, 1 / 8))  # type: ignore
    return base.cid in sub.anc  # type: ignore
# pure-end


def subclass_check(owner: Cls, base_one: Cls, base_two: Cls, candidate: Cls) -> bool:
    # pre-conditions-start
    Requires(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
    Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
    Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
    Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
    Ensures(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
    Ensures(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
    Ensures(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
    # The decision is TRUE iff the candidate is a subtype of either registered
    # base or of the attached type itself.  Membership in the registered family
    # is by the subtype relation, NOT by identity with an exact base class.
    Ensures(Result() == (is_subtype(candidate, base_one)
                         or is_subtype(candidate, base_two)
                         or is_subtype(candidate, owner)))
    # post-conditions-end
    # impl-start
    if is_subtype(candidate, base_one):
        return True
    if is_subtype(candidate, base_two):
        return True
    return is_subtype(candidate, owner)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-14238 (nagini). The frozen spec's postcondition FULLY PINS Result() to the exact disjunction: Ensures(Result() == (is_subtype(candidate, base_one) or is_subtype(candidate, base_two) or is_subtype(candidate, owner))). This is a tight functional spec — any verifying impl must compute precisely that disjunction, leaving no room for a same-spec-but-wrong verifying impl.

PROTOCOL RUN (all; each attack edits ONLY the impl region, axioms/@Pure/Requires/Ensures byte-identical; same-spec exit=0 confirmed for all 8):
- atk_1 = prepatch bug (identity membership `candidate.cid==base_one.cid ...`) — the recorded G-DIFF counterexample re-encoded.
- atk_2 = partial-domain (drop base_two rung).
- atk_3 = boundary (owner-only; drop both registered bases).
- atk_4 = control-flow-effect (always `return True`).
- atk_5 = ungrounded-oracle echo (reversed is_subtype args: is_subtype(base,candidate)).
- atk_6 = conjunction instead of disjunction (and/and).
- atk_7 = dropped super/owner leg (base_one or base_two only).
- atk_8 = full identity (cid== for all three legs).

Commands:
  same-spec: python -m swebench_unified.adversary same-spec nagini django__django-14238 <atk_N.py> -> exit 0 for all 8 (byte-identical spec).
  weakness:  python -m swebench_unified.adversary weakness nagini django__django-14238 <atk_N.py> -> exit 2 for ALL 8 ('NOT-A-COUNTEREXAMPLE: attack does not verify (verification failed) — the spec rejected this impl'). Run concurrently in 3 batches of <=3 JVMs.
  positive control: bash scripts/nagini_verify.sh pos_control.py -> exit 0 (verifies).

No attack came back a CANDIDATE (no shares-spec-AND-verifies), so no faithful refined patch needed materializing/resolve-running; the verify=>correct implication is never triggered against a wrong impl.

A-LEG / correspondence audit (refinement.md): axioms region is EMPTY (no consumed @ContractOnly), so NO kind-3 legs. Legs are A1=R (Python class <-> Cls{cid,anc=MRO ids}), A2=A-reference (structural-subtype membership modeled deeply by is_subtype, validated ==issubclass via G-AX), A3=A-reference+I (super().__subclasscheck__ == is_subtype(candidate,owner), unchanged by patch), A4=I (short-circuit or ladder <-> pinned disjunction). Independently ran axiom_check.py (G-AX): exit 0, 'is_subtype deep model (== issubclass) sound on 289 ordered pairs; subclass_check decision (== real metaclass) sound on 17 candidates; F2P subclass scenarios decide TRUE'. The check correctly references type.__subclasscheck__ (the UNoverridden builtin) for the registered bases/owner — matching mapping.md's note that only AutoField/owner carries AutoFieldMeta while BigAutoField/SmallAutoField use the default metaclass, so issubclass == ordinary MRO membership == is_subtype. A-reference correspondence to the real callees holds.

VERDICT: SOUND. >=5 attacks (8 run) covering partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch bug; none verifies against the pinned spec; positive control verifies; G-AX independently confirms the deep-model A-references == real issubclass/type.__subclasscheck__. No verify-but-wrong impl exists to break verify=>correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14238.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A metaclass maintains a small, immutable family of registered "generated-key"
  base classes and answers the structural-subtype question for the type it is
  attached to.  Given a candidate class, the membership test must report TRUE
  exactly when the candidate stands in the subtype relation to AT LEAST ONE of
  the registered base classes, OR when the candidate is a subtype of the
  attached type itself by the ordinary class hierarchy.

  Crucially, this is a *subtype* relation, not an identity check: a candidate
  that derives (transitively) from one of the registered bases must be reported
  as a member even when the candidate is not itself one of those exact base
  classes.  Equivalently, the relation is reflexive and downward-closed under
  inheritance from the registered bases, so a user-defined class extending a
  registered base is recognised just as the base itself is.

A class is modelled abstractly by its identity together with the set of the
identities of all the classes it derives from (its ancestry, which by the
reflexivity of the subtype relation contains its own identity).  The subtype
relation `is_subtype(c, b)` holds iff `b`'s identity lies in `c`'s ancestry —
exactly the semantics of the ordinary `issubclass` query, which the membership
test consults against each registered base.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Cls:
    """A class abstracted by its identity `cid` and the set `anc` of identities
    of all classes it derives from (its ancestry).  The subtype relation is
    reflexive, so `cid in anc` always holds."""

    def __init__(self, cid: int, anc: PSet[int]) -> None:
        Requires(cid in anc)
        Ensures(Acc(self.cid) and Acc(self.anc))  # type: ignore
        Ensures(self.cid == cid and self.anc is anc)  # type: ignore
        Ensures(self.cid in self.anc)  # type: ignore
        self.cid = cid  # type: ignore
        self.anc = anc  # type: ignore


# axioms-start
# (No axiomatized callees: the structural-subtype query is modelled deeply.)
# axioms-end


# pure-start
@Pure
def is_subtype(sub: Cls, base: Cls) -> bool:
    """The ordinary structural-subtype query: `sub` is a subtype of `base` iff
    `base`'s identity lies in `sub`'s ancestry.  Reflexive (every class is its
    own subtype) and transitive by construction of the ancestry set."""
    Requires(Acc(sub.cid, 1 / 8) and Acc(sub.anc, 1 / 8))  # type: ignore
    Requires(Acc(base.cid, 1 / 8) and Acc(base.anc, 1 / 8))  # type: ignore
    return base.cid in sub.anc  # type: ignore
# pure-end


def subclass_check(owner: Cls, base_one: Cls, base_two: Cls, candidate: Cls) -> bool:
    # pre-conditions-start
    Requires(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
    Requires(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
    Requires(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
    Requires(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(owner.cid, 1 / 4) and Acc(owner.anc, 1 / 4))  # type: ignore
    Ensures(Acc(base_one.cid, 1 / 4) and Acc(base_one.anc, 1 / 4))  # type: ignore
    Ensures(Acc(base_two.cid, 1 / 4) and Acc(base_two.anc, 1 / 4))  # type: ignore
    Ensures(Acc(candidate.cid, 1 / 4) and Acc(candidate.anc, 1 / 4))  # type: ignore
    # The decision is TRUE iff the candidate is a subtype of either registered
    # base or of the attached type itself.  Membership in the registered family
    # is by the subtype relation, NOT by identity with an exact base class.
    Ensures(Result() == (is_subtype(candidate, base_one)
                         or is_subtype(candidate, base_two)
                         or is_subtype(candidate, owner)))
    # post-conditions-end
    # impl-start
    if is_subtype(candidate, base_one):
        return True
    if is_subtype(candidate, base_two):
        return True
    return is_subtype(candidate, owner)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle django__django-14238 (nagini). The frozen spec's postcondition FULLY PINS Result() to the exact disjunction: Ensures(Result() == (is_subtype(candidate, base_one) or is_subtype(candidate, base_two) or is_subtype(candidate, owner))). This is a tight functional spec — any verifying impl must compute precisely that disjunction, leaving no room for a same-spec-but-wrong verifying impl.

PROTOCOL RUN (all; each attack edits ONLY the impl region, axioms/@Pure/Requires/Ensures byte-identical; same-spec exit=0 confirmed for all 8):
- atk_1 = prepatch bug (identity membership `candidate.cid==base_one.cid ...`) — the recorded G-DIFF counterexample re-encoded.
- atk_2 = partial-domain (drop base_two rung).
- atk_3 = boundary (owner-only; drop both registered bases).
- atk_4 = control-flow-effect (always `return True`).
- atk_5 = ungrounded-oracle echo (reversed is_subtype args: is_subtype(base,candidate)).
- atk_6 = conjunction instead of disjunction (and/and).
- atk_7 = dropped super/owner leg (base_one or base_two only).
- atk_8 = full identity (cid== for all three legs).

Commands:
  same-spec: python -m swebench_unified.adversary same-spec nagini django__django-14238 <atk_N.py> -> exit 0 for all 8 (byte-identical spec).
  weakness:  python -m swebench_unified.adversary weakness nagini django__django-14238 <atk_N.py> -> exit 2 for ALL 8 ('NOT-A-COUNTEREXAMPLE: attack does not verify (verification failed) — the spec rejected this impl'). Run concurrently in 3 batches of <=3 JVMs.
  positive control: bash scripts/nagini_verify.sh pos_control.py -> exit 0 (verifies).

No attack came back a CANDIDATE (no shares-spec-AND-verifies), so no faithful refined patch needed materializing/resolve-running; the verify=>correct implication is never triggered against a wrong impl.

A-LEG / correspondence audit (refinement.md): axioms region is EMPTY (no consumed @ContractOnly), so NO kind-3 legs. Legs are A1=R (Python class <-> Cls{cid,anc=MRO ids}), A2=A-reference (structural-subtype membership modeled deeply by is_subtype, validated ==issubclass via G-AX), A3=A-reference+I (super().__subclasscheck__ == is_subtype(candidate,owner), unchanged by patch), A4=I (short-circuit or ladder <-> pinned disjunction). Independently ran axiom_check.py (G-AX): exit 0, 'is_subtype deep model (== issubclass) sound on 289 ordered pairs; subclass_check decision (== real metaclass) sound on 17 candidates; F2P subclass scenarios decide TRUE'. The check correctly references type.__subclasscheck__ (the UNoverridden builtin) for the registered bases/owner — matching mapping.md's note that only AutoField/owner carries AutoFieldMeta while BigAutoField/SmallAutoField use the default metaclass, so issubclass == ordinary MRO membership == is_subtype. A-reference correspondence to the real callees holds.

VERDICT: SOUND. >=5 attacks (8 run) covering partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch bug; none verifies against the pinned spec; positive control verifies; G-AX independently confirms the deep-model A-references == real issubclass/type.__subclasscheck__. No verify-but-wrong impl exists to break verify=>correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift/too-strong) check for django__django-14238 nagini bundle. Result: FAITHFUL — no input found where the modeled subclass_check disagrees with the real callee.

Evidence:
1. Spec byte-identical: `same-spec` on the gold model returns SAME (exit 0).
2. Model verifies: `nagini_verify.sh` -> Verification successful (11.2s).
3. G-AX axiom_check.py passes (exit 0): deep model `is_subtype` == real `type.__subclasscheck__` on all 289 ordered pairs; modeled `subclass_check` decision == real metaclass decision (`issubclass(cand,(b1,b2)) or super().__subclasscheck__(cand)`) on all 17 candidates; F2P subclass scenarios decide TRUE, non-members FALSE, pre-patch identity check would wrongly reject the user subclass.
4. Independent faithfulness probe (my own fresh replica of AutoFieldMeta carrying the POST-PATCH __subclasscheck__): compared the modeled disjunction against real `issubclass(cand, Auto)` over a diverse universe (registered bases, user subclasses, grandchildren, DIAMOND multi-base inheritance from both registered bases, owner-subclass, unrelated classes, and builtins object/int/type/bool/Exception). ZERO mismatches.

The abstraction is exact and not over-strengthened: class C <-> Cls(cid=id(C), anc={id(A) for A in C.__mro__}); is_subtype(c,b) := b.cid in c.anc is precisely MRO-membership = ordinary issubclass. Postcondition Result == is_subtype(cand,b1) or is_subtype(cand,b2) or is_subtype(cand,owner) mirrors the gold `issubclass(subclass,self._subclasses) or super().__subclasscheck__(subclass)` under CPython tuple semantics. Registered bases carry the default type metaclass (ordinary check) and only the owner carries the overriding metaclass whose super() leg is the ordinary type check — both modeled faithfully. The spec captures exactly the single F2P-observed behavioral change (proper subclasses of registered bases now recognized) with no drift toward being too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over spec_view of model.py) PASSES: no hard failures, no warnings. Not a relaxed bundle (relaxed_leakage=None, no RELAXED_LEAKAGE.md); recorded G-LEAK status = pass.

Semantic review of the spec view (module docstring + Cls + pure is_subtype + pre/post-conditions of subclass_check; impl region excluded):
- No gold-diff line reproduced. Gold edit is `subclass in self._subclasses` -> `issubclass(subclass, self._subclasses)` in AutoFieldMeta.__subclasscheck__. The spec view contains neither expression nor the repo symbols (__subclasscheck__, _subclasses, AutoFieldMeta, BigAutoField, SmallAutoField). It uses abstract model names (Cls, is_subtype, subclass_check, owner, base_one, base_two, candidate).
- No diff markers, no patched file path, no bug/fix narration (no 'bug'/'fix'/'pre-patch'/'wrong' etc.).
- The spec states the desired behaviour: membership is a *subtype* relation (issubclass semantics) rather than identity/membership. This does NOT exceed the PUBLIC problem_statement, which already names AutoFieldMeta.__subclasscheck__ and the _subclasses property and states the fix verbatim: 'This can be fixed in AutoFieldMeta.__subclasscheck__ by allowing subclasses of those classes in the _subclasses property.' The subtype-not-identity framing is exactly what the public statement already discloses.
- The word 'issubclass' appears in the docstring only as the correct-semantics anchor for the deep model; issubclass is the ordinary Python builtin the problem_statement's 'allowing subclasses' already points at, not a gold-patch-specific disclosure beyond the public statement.

Judged against solver-visible problem_statement only (not hints_text). The spec view reveals nothing about the gold edit beyond what the public problem_statement already provides.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, which ships in this bundle, so a reader can start there.
