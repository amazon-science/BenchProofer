# P2 adversarial audit — django__django-15278

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ColumnSpec:
@@ -84,7 +83,6 @@
     Requires(Acc(col.primary_key, 1 / 2))
     Requires(Acc(col.unique, 1 / 2))
     Requires(Acc(col.nullable, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(col.primary_key, 1 / 2))
@@ -110,8 +108,7 @@
                     col.nullable and (not has_effective_default(col))))
     # post-conditions-end
     # impl-start
-    if (col.primary_key or col.unique or
-            (not col.nullable) or has_effective_default(col)):
+    if ((not col.nullable) or has_effective_default(col)):
         return 1
     else:
         return 0
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ColumnSpec:
@@ -84,7 +83,6 @@
     Requires(Acc(col.primary_key, 1 / 2))
     Requires(Acc(col.unique, 1 / 2))
     Requires(Acc(col.nullable, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(col.primary_key, 1 / 2))
@@ -110,8 +108,7 @@
                     col.nullable and (not has_effective_default(col))))
     # post-conditions-end
     # impl-start
-    if (col.primary_key or col.unique or
-            (not col.nullable) or has_effective_default(col)):
+    if (col.unique or (not col.nullable) or has_effective_default(col)):
         return 1
     else:
         return 0
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ColumnSpec:
@@ -84,7 +83,6 @@
     Requires(Acc(col.primary_key, 1 / 2))
     Requires(Acc(col.unique, 1 / 2))
     Requires(Acc(col.nullable, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(col.primary_key, 1 / 2))
@@ -110,8 +108,7 @@
                     col.nullable and (not has_effective_default(col))))
     # post-conditions-end
     # impl-start
-    if (col.primary_key or col.unique or
-            (not col.nullable) or has_effective_default(col)):
+    if (col.primary_key or (not col.nullable) or has_effective_default(col)):
         return 1
     else:
         return 0
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ColumnSpec:
@@ -84,7 +83,6 @@
     Requires(Acc(col.primary_key, 1 / 2))
     Requires(Acc(col.unique, 1 / 2))
     Requires(Acc(col.nullable, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(col.primary_key, 1 / 2))
@@ -112,7 +110,7 @@
     # impl-start
     if (col.primary_key or col.unique or
             (not col.nullable) or has_effective_default(col)):
+        return 0
+    else:
         return 1
-    else:
-        return 0
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ColumnSpec:
@@ -84,7 +83,6 @@
     Requires(Acc(col.primary_key, 1 / 2))
     Requires(Acc(col.unique, 1 / 2))
     Requires(Acc(col.nullable, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(col.primary_key, 1 / 2))
@@ -110,9 +108,5 @@
                     col.nullable and (not has_effective_default(col))))
     # post-conditions-end
     # impl-start
-    if (col.primary_key or col.unique or
-            (not col.nullable) or has_effective_default(col)):
-        return 1
-    else:
-        return 0
+    return 1
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ColumnSpec:
@@ -84,7 +83,6 @@
     Requires(Acc(col.primary_key, 1 / 2))
     Requires(Acc(col.unique, 1 / 2))
     Requires(Acc(col.nullable, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(col.primary_key, 1 / 2))
@@ -110,9 +108,5 @@
                     col.nullable and (not has_effective_default(col))))
     # post-conditions-end
     # impl-start
-    if (col.primary_key or col.unique or
-            (not col.nullable) or has_effective_default(col)):
-        return 1
-    else:
-        return 0
+    return 0
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ColumnSpec:
@@ -84,7 +83,6 @@
     Requires(Acc(col.primary_key, 1 / 2))
     Requires(Acc(col.unique, 1 / 2))
     Requires(Acc(col.nullable, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(col.primary_key, 1 / 2))
@@ -110,8 +108,7 @@
                     col.nullable and (not has_effective_default(col))))
     # post-conditions-end
     # impl-start
-    if (col.primary_key or col.unique or
-            (not col.nullable) or has_effective_default(col)):
+    if col.primary_key:
         return 1
     else:
         return 0
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ColumnSpec:
@@ -84,7 +83,6 @@
     Requires(Acc(col.primary_key, 1 / 2))
     Requires(Acc(col.unique, 1 / 2))
     Requires(Acc(col.nullable, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(col.primary_key, 1 / 2))
@@ -110,8 +108,8 @@
                     col.nullable and (not has_effective_default(col))))
     # post-conditions-end
     # impl-start
-    if (col.primary_key or col.unique or
-            (not col.nullable) or has_effective_default(col)):
+    if (col.primary_key and col.unique and
+            (not col.nullable) and has_effective_default(col)):
         return 1
     else:
         return 0
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -37,7 +37,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class ColumnSpec:
@@ -84,7 +83,6 @@
     Requires(Acc(col.primary_key, 1 / 2))
     Requires(Acc(col.unique, 1 / 2))
     Requires(Acc(col.nullable, 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(col.primary_key, 1 / 2))
@@ -110,8 +108,7 @@
                     col.nullable and (not has_effective_default(col))))
     # post-conditions-end
     # impl-start
-    if (col.primary_key or col.unique or
-            (not col.nullable) or has_effective_default(col)):
+    if (col.primary_key or col.unique or (not col.nullable)):
         return 1
     else:
         return 0
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15278.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a column is added to an existing table on a backend whose in-place
  column-append statement (ADD COLUMN) cannot express key, uniqueness, not-null
  or default-value constraints, the operation must choose between two routes:

    * the FULL-REBUILD route, which reconstructs the table and so can realise
      ANY column constraint; and
    * the in-place APPEND route, which is only valid for a column that carries
      NONE of those constraints.

  The required behaviour: the in-place APPEND route may be taken ONLY for a
  column that is

      * not a primary key, AND
      * not unique, AND
      * nullable, AND
      * has no effective database default;

  if the column violates ANY one of these four conditions — it is a primary
  key, OR it is unique, OR it is non-nullable, OR it carries an effective
  default — the FULL-REBUILD route MUST be chosen. In particular a nullable,
  defaultless column that nonetheless carries a uniqueness (or primary-key)
  constraint must NOT be appended in place.

The column descriptor is modelled as a minimal object carrying only the touched
flags: whether it is a primary key, whether it is unique, and whether it is
nullable. Whether the column has an effective database default is reported by
an unchanged backend helper, axiomatized as a pure boolean callee.

The chosen route is reported as an int: 1 = full-rebuild route, 0 = in-place
append route.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

class ColumnSpec:
    def __init__(self, primary_key: bool, unique: bool, nullable: bool) -> None:
        Ensures(Acc(self.primary_key, 1 / 2) and self.primary_key == primary_key)  # type: ignore
        Ensures(Acc(self.unique, 1 / 2) and self.unique == unique)  # type: ignore
        Ensures(Acc(self.nullable, 1 / 2) and self.nullable == nullable)  # type: ignore
        self.primary_key = primary_key
        self.unique = unique
        self.nullable = nullable

# axioms-start
@Pure
@ContractOnly
def has_effective_default(col: ColumnSpec) -> bool:
    """Whether the unchanged backend helper reports an effective database
    default for this column (i.e. its effective default is not absent). A pure,
    side-effect-free observation of the column. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(col.primary_key, 1 / 8))
    Requires(Acc(col.unique, 1 / 8))
    Requires(Acc(col.nullable, 1 / 8))
# axioms-end

# pure-start
@Pure
def needs_full_rebuild(col: ColumnSpec) -> bool:
    """The in-place append route is valid ONLY for a column that is not a key,
    not unique, nullable, and carries no effective default; any other column
    requires the full-rebuild route."""
    Requires(Acc(col.primary_key, 1 / 4))
    Requires(Acc(col.unique, 1 / 4))
    Requires(Acc(col.nullable, 1 / 4))
    return (col.primary_key or col.unique or
            (not col.nullable) or has_effective_default(col))
# pure-end

def add_column(col: ColumnSpec) -> int:
    # pre-conditions-start
    Requires(Acc(col.primary_key, 1 / 2))
    Requires(Acc(col.unique, 1 / 2))
    Requires(Acc(col.nullable, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(col.primary_key, 1 / 2))
    Ensures(Acc(col.unique, 1 / 2))
    Ensures(Acc(col.nullable, 1 / 2))
    # The route is exactly the constraint-presence predicate: full rebuild iff
    # the column is a key, unique, non-nullable, or carries an effective
    # default; the in-place append route only for a column carrying none.
    Ensures(Result() == 1 or Result() == 0)
    Ensures((Result() == 1) == needs_full_rebuild(col))
    # A primary-key column always rebuilds.
    Ensures(Implies(col.primary_key, Result() == 1))
    # A unique column always rebuilds (this includes the nullable, defaultless
    # uniqueness-carrying column that must not be appended in place).
    Ensures(Implies(col.unique, Result() == 1))
    # A non-nullable column always rebuilds.
    Ensures(Implies(not col.nullable, Result() == 1))
    # A column with an effective default always rebuilds.
    Ensures(Implies(has_effective_default(col), Result() == 1))
    # The in-place append route is taken only when every constraint is absent.
    Ensures(Implies(Result() == 0,
                    (not col.primary_key) and (not col.unique) and
                    col.nullable and (not has_effective_default(col))))
    # post-conditions-end
    # impl-start
    if (col.primary_key or col.unique or
            (not col.nullable) or has_effective_default(col)):
        return 1
    else:
        return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-15278 (nagini). PROTOCOL: 9 distinct same-spec wrong impls built by editing ONLY the impl-start/impl-end region (axioms/@Pure/Requires/Ensures byte-identical vs model.py lines 1-109, diff-confirmed for all 9). All run via `python -m swebench_unified.adversary weakness nagini django__django-15278 <atk>` (env python; module missing from cluster default python). Concurrent background batches of 3 (each Nagini check = JVM+Z3). RESULTS: every attack exit=2 NOT-A-COUNTEREXAMPLE (spec rejected — verification failed); positive control (model.py verbatim) verifies exit=0 via scripts/nagini_verify.sh.

ZERO CANDIDATES -> no verifying wrong impl -> no faithful patch to materialize/resolve; the resolve step is vacuous by protocol (nothing verified-but-wrong exists to break the spec). Attack taxonomy: atk_1=prepatch bug (drop pk+unique disjuncts; wrong on nullable unique/pk col), atk_2=drop pk disjunct, atk_3=drop unique disjunct, atk_4=control-flow-effect (inverted branch labels: return 0 where gold rebuilds), atk_5=boundary constant return 1, atk_6=boundary constant return 0, atk_7=partial-domain (consult primary_key only), atk_8=logic corruption (and-chain instead of or-chain), atk_9=ungrounded-oracle echo variant (drop has_effective_default disjunct; wrong on defaulted col).

WHY TIGHT: postconditions `Result()==1 or Result()==0` + biconditional `(Result()==1)==needs_full_rebuild(col)` fully pin the return for every input, leaving no slack for any divergent routing to verify; the 4 Implies clauses are consequences of the biconditional. has_effective_default is @Pure/@ContractOnly with NO Ensures (weakest contract, cannot over-claim) and being @Pure is deterministic, so no ungrounded-oracle echo can satisfy the biconditional either. REFINEMENT.MD AUDIT (A-legs focus): steps A1-A4 R, A6 I, A7/A8 R, A5 A-consumed; NO kind-3 step (the changed routing predicate is modeled directly as the identical boolean disjunction, kind I, over refined boolean carriers). No A-reference leg claimed (correct).

A5 A-consumed correspondence: has_effective_default <-> `self.effective_default(field) is not None` is a genuinely UNCHANGED callee (byte-identical pre/post-patch; gold only prepends `field.primary_key or field.unique`), so it is a legitimate axiom, and axiom_check.py (G-AX, read) enforces its correspondence to the real Django SQLite backend over 14 field witnesses incl. the discriminating nullable defaultless OneToOneField, asserting determinism/side-effect-freedom AND real-predicate == model needs_full_rebuild over the four signals. Model<->patch correspondence (mapping.md) holds term-for-term against the gold patch.py diff (field.primary_key or field.unique or not field.null or effective_default(field) is not None). VERDICT: SOUND — >=5 diverse attacks (9 run), none is a candidate, so verify=>correct is not falsified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-15278.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a column is added to an existing table on a backend whose in-place
  column-append statement (ADD COLUMN) cannot express key, uniqueness, not-null
  or default-value constraints, the operation must choose between two routes:

    * the FULL-REBUILD route, which reconstructs the table and so can realise
      ANY column constraint; and
    * the in-place APPEND route, which is only valid for a column that carries
      NONE of those constraints.

  The required behaviour: the in-place APPEND route may be taken ONLY for a
  column that is

      * not a primary key, AND
      * not unique, AND
      * nullable, AND
      * has no effective database default;

  if the column violates ANY one of these four conditions — it is a primary
  key, OR it is unique, OR it is non-nullable, OR it carries an effective
  default — the FULL-REBUILD route MUST be chosen. In particular a nullable,
  defaultless column that nonetheless carries a uniqueness (or primary-key)
  constraint must NOT be appended in place.

The column descriptor is modelled as a minimal object carrying only the touched
flags: whether it is a primary key, whether it is unique, and whether it is
nullable. Whether the column has an effective database default is reported by
an unchanged backend helper, axiomatized as a pure boolean callee.

The chosen route is reported as an int: 1 = full-rebuild route, 0 = in-place
append route.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

class ColumnSpec:
    def __init__(self, primary_key: bool, unique: bool, nullable: bool) -> None:
        Ensures(Acc(self.primary_key, 1 / 2) and self.primary_key == primary_key)  # type: ignore
        Ensures(Acc(self.unique, 1 / 2) and self.unique == unique)  # type: ignore
        Ensures(Acc(self.nullable, 1 / 2) and self.nullable == nullable)  # type: ignore
        self.primary_key = primary_key
        self.unique = unique
        self.nullable = nullable

# axioms-start
@Pure
@ContractOnly
def has_effective_default(col: ColumnSpec) -> bool:
    """Whether the unchanged backend helper reports an effective database
    default for this column (i.e. its effective default is not absent). A pure,
    side-effect-free observation of the column. Provenance + executable
    soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(col.primary_key, 1 / 8))
    Requires(Acc(col.unique, 1 / 8))
    Requires(Acc(col.nullable, 1 / 8))
# axioms-end

# pure-start
@Pure
def needs_full_rebuild(col: ColumnSpec) -> bool:
    """The in-place append route is valid ONLY for a column that is not a key,
    not unique, nullable, and carries no effective default; any other column
    requires the full-rebuild route."""
    Requires(Acc(col.primary_key, 1 / 4))
    Requires(Acc(col.unique, 1 / 4))
    Requires(Acc(col.nullable, 1 / 4))
    return (col.primary_key or col.unique or
            (not col.nullable) or has_effective_default(col))
# pure-end

def add_column(col: ColumnSpec) -> int:
    # pre-conditions-start
    Requires(Acc(col.primary_key, 1 / 2))
    Requires(Acc(col.unique, 1 / 2))
    Requires(Acc(col.nullable, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(col.primary_key, 1 / 2))
    Ensures(Acc(col.unique, 1 / 2))
    Ensures(Acc(col.nullable, 1 / 2))
    # The route is exactly the constraint-presence predicate: full rebuild iff
    # the column is a key, unique, non-nullable, or carries an effective
    # default; the in-place append route only for a column carrying none.
    Ensures(Result() == 1 or Result() == 0)
    Ensures((Result() == 1) == needs_full_rebuild(col))
    # A primary-key column always rebuilds.
    Ensures(Implies(col.primary_key, Result() == 1))
    # A unique column always rebuilds (this includes the nullable, defaultless
    # uniqueness-carrying column that must not be appended in place).
    Ensures(Implies(col.unique, Result() == 1))
    # A non-nullable column always rebuilds.
    Ensures(Implies(not col.nullable, Result() == 1))
    # A column with an effective default always rebuilds.
    Ensures(Implies(has_effective_default(col), Result() == 1))
    # The in-place append route is taken only when every constraint is absent.
    Ensures(Implies(Result() == 0,
                    (not col.primary_key) and (not col.unique) and
                    col.nullable and (not has_effective_default(col))))
    # post-conditions-end
    # impl-start
    if (col.primary_key or col.unique or
            (not col.nullable) or has_effective_default(col)):
        return 1
    else:
        return 0
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-15278 (nagini). PROTOCOL: 9 distinct same-spec wrong impls built by editing ONLY the impl-start/impl-end region (axioms/@Pure/Requires/Ensures byte-identical vs model.py lines 1-109, diff-confirmed for all 9). All run via `python -m swebench_unified.adversary weakness nagini django__django-15278 <atk>` (env python; module missing from cluster default python). Concurrent background batches of 3 (each Nagini check = JVM+Z3). RESULTS: every attack exit=2 NOT-A-COUNTEREXAMPLE (spec rejected — verification failed); positive control (model.py verbatim) verifies exit=0 via scripts/nagini_verify.sh.

ZERO CANDIDATES -> no verifying wrong impl -> no faithful patch to materialize/resolve; the resolve step is vacuous by protocol (nothing verified-but-wrong exists to break the spec). Attack taxonomy: atk_1=prepatch bug (drop pk+unique disjuncts; wrong on nullable unique/pk col), atk_2=drop pk disjunct, atk_3=drop unique disjunct, atk_4=control-flow-effect (inverted branch labels: return 0 where gold rebuilds), atk_5=boundary constant return 1, atk_6=boundary constant return 0, atk_7=partial-domain (consult primary_key only), atk_8=logic corruption (and-chain instead of or-chain), atk_9=ungrounded-oracle echo variant (drop has_effective_default disjunct; wrong on defaulted col).

WHY TIGHT: postconditions `Result()==1 or Result()==0` + biconditional `(Result()==1)==needs_full_rebuild(col)` fully pin the return for every input, leaving no slack for any divergent routing to verify; the 4 Implies clauses are consequences of the biconditional. has_effective_default is @Pure/@ContractOnly with NO Ensures (weakest contract, cannot over-claim) and being @Pure is deterministic, so no ungrounded-oracle echo can satisfy the biconditional either. REFINEMENT.MD AUDIT (A-legs focus): steps A1-A4 R, A6 I, A7/A8 R, A5 A-consumed; NO kind-3 step (the changed routing predicate is modeled directly as the identical boolean disjunction, kind I, over refined boolean carriers). No A-reference leg claimed (correct).

A5 A-consumed correspondence: has_effective_default <-> `self.effective_default(field) is not None` is a genuinely UNCHANGED callee (byte-identical pre/post-patch; gold only prepends `field.primary_key or field.unique`), so it is a legitimate axiom, and axiom_check.py (G-AX, read) enforces its correspondence to the real Django SQLite backend over 14 field witnesses incl. the discriminating nullable defaultless OneToOneField, asserting determinism/side-effect-freedom AND real-predicate == model needs_full_rebuild over the four signals. Model<->patch correspondence (mapping.md) holds term-for-term against the gold patch.py diff (field.primary_key or field.unique or not field.null or effective_default(field) is not None). VERDICT: SOUND — >=5 diverse attacks (9 run), none is a candidate, so verify=>correct is not falsified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-15278 nagini bundle.

SPEC INTEGRITY: The bundle spec (has_effective_default axiom + needs_full_rebuild pure predicate + add_column pre/postconditions) is byte-identical (same-spec identity copy -> SAME, exit 0).

### MODELED FUNCTION vs REAL CALLEE:
- Base worktree confirmed at base_commit 0ab58c120939093fea90822f376e1866fc714d1f. Real pre-patch add_field (django/db/backends/sqlite3/schema.py:330) = `if not field.null or self.effective_default(field) is not None:`; gold patch.diff prepends exactly `field.primary_key or field.unique`, yielding post-patch predicate `field.primary_key or field.unique or not field.null or self.effective_default(field) is not None`.
- The spec's needs_full_rebuild = `col.primary_key or col.unique or (not col.nullable) or has_effective_default(col)` is a STRUCTURAL IDENTITY (same operands, same order) to the real post-patch predicate, under the documented type refinement field.primary_key<->col.primary_key, field.unique<->col.unique, field.null<->col.nullable, and has_effective_default<->`effective_default(field) is not None`.
- has_effective_default is an UNCHANGED callee (clause byte-identical pre/post patch), modeled with the WEAKEST contract (@Pure @ContractOnly, NO Ensures, only fractional read permission) so it cannot over-claim the real value — the routing postconditions that mention it are all Implies guarded by the observed value, or the equation itself.

### EMPIRICAL CORROBORATION (the faithfulness question answered exhaustively):
- G-AX (recorded pass, exit 0): real Django SQLite backend over 14 field witnesses incl. the discriminating nullable defaultless OneToOneField (unique=True, null=True, pk=False, no default); effective_default(field) is-not-None is deterministic + non-mutating; real routing predicate == model needs_full_rebuild on all 14.
- G-CONF (recorded pass, exit 0): differential of the contract-stripped shadow impl (which delegates has_effective_default to the REAL editor.effective_default) vs the REAL patched add_field route recorder, over 100,035 inputs (35 boundary incl. all 16 pk/unique/null/default combos + auto_now/callable/blank cases, + 100000 fuzz draws, seed 15278) -> 0 disagreements.

DRIFT PROBES considered and rejected: (a) bool() coercion vs truthiness of flags is irrelevant under `or` disjunction routing; (b) short-circuit evaluation of effective_default introduces no observable difference (pure, side-effect-free per G-AX); (c) no library-flag dependency (e.g. html.escape quote=True style) affects the result — only backend=SQLite is pinned, which is the patch/F2P target.

The modeled function agrees with the real callee on every input; the spec is neither too strong nor drifted. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen passes (LeakageReport.passed=True, no hard failures); meta.json G-LEAK='pass', not relaxed (relaxed_leakage=None, no RELAXED_LEAKAGE.md), so no deferral path applies. Manual semantic review of the full spec view (docstring + spec/pure/axiom regions) confirms NO leakage of the gold edit beyond the public problem_statement:

- Gold edit = prepend `field.primary_key or field.unique` disjuncts to the SQLite add_field routing predicate in django/db/backends/sqlite3/schema.py. The spec view names NONE of the localizing artifacts: no patched file path (sqlite3/schema.py), no patched function name (add_field), no repo callees (effective_default, _remake_table, super().add_field). The only changed def-symbol the patch touches (delete_model, from the hunk header) does not appear anywhere. No diff markers, no reproduced gold-patch line, no bug/fix narration.
- The public problem_statement already reveals the discriminating case: a nullable OneToOneField (unique=True, null=True) crashes on SQLite with 'Cannot add a UNIQUE column' on ALTER TABLE ... ADD COLUMN. So the uniqueness discriminator is already public.
- The spec view states the desired behavior abstractly over a minimal ColumnSpec (primary_key/unique/nullable + an axiomatized has_effective_default): in-place append valid only for a not-key, not-unique, nullable, defaultless column; otherwise full rebuild. This IS the correctness specification a twin-artifact model must state; it does not disclose where/how to edit the repo. A solver still must localize to sqlite3/schema.py:add_field and implement. The primary-key/default conditions are standard SQLite ALTER-TABLE semantics, not a reproduction of the diff.

Conclusion: the spec view is a behavior specification, not a gold-edit reconstruction. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).