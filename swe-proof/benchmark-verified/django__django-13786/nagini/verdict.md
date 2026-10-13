# P2 adversarial audit — django__django-13786

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     """
     Requires(Acc(dict_pred(a), 1 / 4))
     Requires(Acc(dict_pred(b), 1 / 4))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(a), 1 / 4))
     Ensures(Acc(dict_pred(b), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
@@ -95,7 +93,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 4))
-    Requires(MustTerminate(6))
     Ensures(Acc(dict_pred(d), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -155,7 +152,6 @@
                                            not isinstance(k, bool))))
     Requires(Forall(int, lambda k: Implies(k in operation_options,
                                            not isinstance(k, bool))))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -197,14 +193,6 @@
                                           k in self_options or k in operation_options)))
     # post-conditions-end
     # impl-start
-    # Step 1: merge -- the options step's values win over the creation step's.
     options = merge_options(self_options, operation_options)
-    # Step 2 (the new logic): clear every managed name the options step does not
-    # provide, so the options step's mapping is the complete set of managed
-    # options on the collapsed creation step.
-    if key_managed_a() not in operation_options:
-        options = without_key(options, key_managed_a())
-    if key_managed_b() not in operation_options:
-        options = without_key(options, key_managed_b())
     return options
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     """
     Requires(Acc(dict_pred(a), 1 / 4))
     Requires(Acc(dict_pred(b), 1 / 4))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(a), 1 / 4))
     Ensures(Acc(dict_pred(b), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
@@ -95,7 +93,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 4))
-    Requires(MustTerminate(6))
     Ensures(Acc(dict_pred(d), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -155,7 +152,6 @@
                                            not isinstance(k, bool))))
     Requires(Forall(int, lambda k: Implies(k in operation_options,
                                            not isinstance(k, bool))))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -197,14 +193,8 @@
                                           k in self_options or k in operation_options)))
     # post-conditions-end
     # impl-start
-    # Step 1: merge -- the options step's values win over the creation step's.
     options = merge_options(self_options, operation_options)
-    # Step 2 (the new logic): clear every managed name the options step does not
-    # provide, so the options step's mapping is the complete set of managed
-    # options on the collapsed creation step.
     if key_managed_a() not in operation_options:
         options = without_key(options, key_managed_a())
-    if key_managed_b() not in operation_options:
-        options = without_key(options, key_managed_b())
     return options
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     """
     Requires(Acc(dict_pred(a), 1 / 4))
     Requires(Acc(dict_pred(b), 1 / 4))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(a), 1 / 4))
     Ensures(Acc(dict_pred(b), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
@@ -95,7 +93,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 4))
-    Requires(MustTerminate(6))
     Ensures(Acc(dict_pred(d), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -155,7 +152,6 @@
                                            not isinstance(k, bool))))
     Requires(Forall(int, lambda k: Implies(k in operation_options,
                                            not isinstance(k, bool))))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -197,14 +193,8 @@
                                           k in self_options or k in operation_options)))
     # post-conditions-end
     # impl-start
-    # Step 1: merge -- the options step's values win over the creation step's.
     options = merge_options(self_options, operation_options)
-    # Step 2 (the new logic): clear every managed name the options step does not
-    # provide, so the options step's mapping is the complete set of managed
-    # options on the collapsed creation step.
-    if key_managed_a() not in operation_options:
-        options = without_key(options, key_managed_a())
-    if key_managed_b() not in operation_options:
-        options = without_key(options, key_managed_b())
+    options = without_key(options, key_managed_a())
+    options = without_key(options, key_managed_b())
     return options
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     """
     Requires(Acc(dict_pred(a), 1 / 4))
     Requires(Acc(dict_pred(b), 1 / 4))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(a), 1 / 4))
     Ensures(Acc(dict_pred(b), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
@@ -95,7 +93,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 4))
-    Requires(MustTerminate(6))
     Ensures(Acc(dict_pred(d), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -155,7 +152,6 @@
                                            not isinstance(k, bool))))
     Requires(Forall(int, lambda k: Implies(k in operation_options,
                                            not isinstance(k, bool))))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -197,14 +193,10 @@
                                           k in self_options or k in operation_options)))
     # post-conditions-end
     # impl-start
-    # Step 1: merge -- the options step's values win over the creation step's.
     options = merge_options(self_options, operation_options)
-    # Step 2 (the new logic): clear every managed name the options step does not
-    # provide, so the options step's mapping is the complete set of managed
-    # options on the collapsed creation step.
-    if key_managed_a() not in operation_options:
+    if key_managed_a() in operation_options:
         options = without_key(options, key_managed_a())
-    if key_managed_b() not in operation_options:
+    if key_managed_b() in operation_options:
         options = without_key(options, key_managed_b())
     return options
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     """
     Requires(Acc(dict_pred(a), 1 / 4))
     Requires(Acc(dict_pred(b), 1 / 4))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(a), 1 / 4))
     Ensures(Acc(dict_pred(b), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
@@ -95,7 +93,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 4))
-    Requires(MustTerminate(6))
     Ensures(Acc(dict_pred(d), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -155,7 +152,6 @@
                                            not isinstance(k, bool))))
     Requires(Forall(int, lambda k: Implies(k in operation_options,
                                            not isinstance(k, bool))))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -197,14 +193,11 @@
                                           k in self_options or k in operation_options)))
     # post-conditions-end
     # impl-start
-    # Step 1: merge -- the options step's values win over the creation step's.
     options = merge_options(self_options, operation_options)
-    # Step 2 (the new logic): clear every managed name the options step does not
-    # provide, so the options step's mapping is the complete set of managed
-    # options on the collapsed creation step.
     if key_managed_a() not in operation_options:
         options = without_key(options, key_managed_a())
     if key_managed_b() not in operation_options:
         options = without_key(options, key_managed_b())
+    options = without_key(options, key_other())
     return options
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     """
     Requires(Acc(dict_pred(a), 1 / 4))
     Requires(Acc(dict_pred(b), 1 / 4))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(a), 1 / 4))
     Ensures(Acc(dict_pred(b), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
@@ -95,7 +93,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 4))
-    Requires(MustTerminate(6))
     Ensures(Acc(dict_pred(d), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -155,7 +152,6 @@
                                            not isinstance(k, bool))))
     Requires(Forall(int, lambda k: Implies(k in operation_options,
                                            not isinstance(k, bool))))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -197,11 +193,7 @@
                                           k in self_options or k in operation_options)))
     # post-conditions-end
     # impl-start
-    # Step 1: merge -- the options step's values win over the creation step's.
-    options = merge_options(self_options, operation_options)
-    # Step 2 (the new logic): clear every managed name the options step does not
-    # provide, so the options step's mapping is the complete set of managed
-    # options on the collapsed creation step.
+    options = merge_options(operation_options, self_options)
     if key_managed_a() not in operation_options:
         options = without_key(options, key_managed_a())
     if key_managed_b() not in operation_options:
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     """
     Requires(Acc(dict_pred(a), 1 / 4))
     Requires(Acc(dict_pred(b), 1 / 4))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(a), 1 / 4))
     Ensures(Acc(dict_pred(b), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
@@ -95,7 +93,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 4))
-    Requires(MustTerminate(6))
     Ensures(Acc(dict_pred(d), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -155,7 +152,6 @@
                                            not isinstance(k, bool))))
     Requires(Forall(int, lambda k: Implies(k in operation_options,
                                            not isinstance(k, bool))))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -197,14 +193,10 @@
                                           k in self_options or k in operation_options)))
     # post-conditions-end
     # impl-start
-    # Step 1: merge -- the options step's values win over the creation step's.
     options = merge_options(self_options, operation_options)
-    # Step 2 (the new logic): clear every managed name the options step does not
-    # provide, so the options step's mapping is the complete set of managed
-    # options on the collapsed creation step.
-    if key_managed_a() not in operation_options:
+    if key_managed_a() not in self_options:
         options = without_key(options, key_managed_a())
-    if key_managed_b() not in operation_options:
+    if key_managed_b() not in self_options:
         options = without_key(options, key_managed_b())
     return options
     # impl-end
```

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -58,7 +58,6 @@
 """
 from typing import Dict
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -72,7 +71,6 @@
     """
     Requires(Acc(dict_pred(a), 1 / 4))
     Requires(Acc(dict_pred(b), 1 / 4))
-    Requires(MustTerminate(2))
     Ensures(Acc(dict_pred(a), 1 / 4))
     Ensures(Acc(dict_pred(b), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
@@ -95,7 +93,6 @@
     check: mapping.md / axiom_check.py (G-AX).
     """
     Requires(Acc(dict_pred(d), 1 / 4))
-    Requires(MustTerminate(6))
     Ensures(Acc(dict_pred(d), 1 / 4))
     Ensures(Acc(dict_pred(Result())))
     Ensures(Result() is not None)
@@ -155,7 +152,6 @@
                                            not isinstance(k, bool))))
     Requires(Forall(int, lambda k: Implies(k in operation_options,
                                            not isinstance(k, bool))))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -197,14 +193,10 @@
                                           k in self_options or k in operation_options)))
     # post-conditions-end
     # impl-start
-    # Step 1: merge -- the options step's values win over the creation step's.
     options = merge_options(self_options, operation_options)
-    # Step 2 (the new logic): clear every managed name the options step does not
-    # provide, so the options step's mapping is the complete set of managed
-    # options on the collapsed creation step.
+    if key_managed_b() not in operation_options:
+        options = without_key(options, key_managed_b())
     if key_managed_a() not in operation_options:
         options = without_key(options, key_managed_a())
-    if key_managed_b() not in operation_options:
-        options = without_key(options, key_managed_b())
     return options
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13786.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a model-creation step and a subsequent model-options step on the same
  model are collapsed into a single model-creation step, the options carried by
  the collapsed step must be EXACTLY the options the model would have after the
  options step is applied to the freshly-created model -- not merely the union
  of the two option mappings.

  The options step distinguishes two kinds of option name:

    * a MANAGED option name (one of the established family of metadata options
      the options step is allowed to set, compare, and clear); and
    * any OTHER option name (a setting outside that family).

  Applying the options step yields, for each option name k:

    (1) if k is provided by the options step, the value the options step gives
        it (the options step's value wins over the creation step's value);
    (2) else if k is a MANAGED option name, k is ABSENT from the result -- a
        managed option the creation step had but the options step does not
        provide is cleared, because the options step's mapping is the complete
        intended set of managed options;
    (3) else (k is an OTHER option name not provided by the options step), k
        keeps the creation step's value if the creation step had it, and is
        absent otherwise.

  The result carries no option name that neither the creation step nor the
  options step mentions. Clause (2) is the behaviour that matters: a managed
  option present on the creation step but omitted by the options step must NOT
  survive into the collapsed creation step.

Modelling choices (Nagini fragment):
  * An option mapping is a ``Dict[int, int]`` from an option-name token to an
    option-value token; only membership and per-name value are observed, so
    integer-keyed identity is the faithful carrier (mapping.md §2).
  * The managed-option family is the deep, definite predicate ``is_managed_
    option`` over a finite family of representative option-name tokens
    (mapping.md §2), not an opaque oracle. ``key_managed_a`` / ``key_managed_b``
    are managed names; ``key_other`` is a name outside the managed family.
    Behaviours (1)/(3) and the no-foreign-name closure are quantified over
    EVERY option name; behaviour (2) is stated per member of the (finite)
    managed family, which covers every managed name.
  * The two unchanged language primitives the step composes -- the mapping
    merge ``{**a, **b}`` and the removal of one name ``d.pop(k, None)`` /
    ``{kk: vv for kk, vv in d.items() if kk != k}`` -- are the axiomatised
    callees ``merge_options`` / ``without_key`` (A-consumed), validated against
    real Python out-of-band (axiom_check.py, G-AX). The NEW logic -- deciding
    which managed names to clear -- is spelled out deeply in the impl region.

Both input mappings are read-only here (the step allocates a fresh result and
never writes either input), so each is held at HALF permission (Required AND
Ensured); the axiomatised callees take only QUARTER permission so quantified
facts about the inputs are preserved across the calls. No string indexing is
used (Nagini bans it). Markers (machine-parsed) delimit the spec / proof /
impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
@ContractOnly
def merge_options(a: Dict[int, int], b: Dict[int, int]) -> Dict[int, int]:
    """Standard mapping merge ``{**a, **b}`` (an unchanged language primitive
    the step composes): a FRESH mapping holding every name of ``a`` and ``b``;
    ``b``'s value wins where both carry a name, otherwise ``a``'s value. The
    result is a new object, so neither input is mutated (both read-only).
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(a), 1 / 4))
    Requires(Acc(dict_pred(b), 1 / 4))
    Ensures(Acc(dict_pred(a), 1 / 4))
    Ensures(Acc(dict_pred(b), 1 / 4))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # b's value wins where b carries the name ...
    Ensures(Forall(int, lambda k: Implies(k in b, k in Result() and Result()[k] == b[k])))
    # ... a's value carries elsewhere ...
    Ensures(Forall(int, lambda k: Implies(k in a and k not in b,
                                          k in Result() and Result()[k] == a[k])))
    # ... and the result holds no name outside a's and b's names.
    Ensures(Forall(int, lambda k: Implies(k in Result(), k in a or k in b)))


@ContractOnly
def without_key(d: Dict[int, int], k: int) -> Dict[int, int]:
    """Standard removal of one name ``{kk: vv for kk, vv in d.items() if kk != k}``
    / ``d.pop(k, None)`` returning the residue (an unchanged language primitive):
    a FRESH mapping equal to ``d`` with the single name ``k`` removed. ``d`` is
    read-only (the result is a new object). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(d), 1 / 4))
    Ensures(Acc(dict_pred(d), 1 / 4))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # the removed name is gone ...
    Ensures(k not in Result())
    # ... every other name of d is carried through with its value ...
    Ensures(Forall(int, lambda j: Implies(j != k and j in d,
                                          j in Result() and Result()[j] == d[j])))
    # ... and the result introduces no name d did not have.
    Ensures(Forall(int, lambda j: Implies(j in Result(),
                                          j != k and j in d and Result()[j] == d[j])))
# axioms-end


# pure-start
@Pure
def key_managed_a() -> int:
    # A representative MANAGED option name (one the options step may set/clear).
    return 0


@Pure
def key_managed_b() -> int:
    # A second, distinct representative MANAGED option name.
    return 1


@Pure
def key_other() -> int:
    # A representative option name OUTSIDE the managed family (the options step
    # neither compares nor clears it).
    return 2


@Pure
def is_managed_option(k: int) -> bool:
    """The definite membership test for the managed-option family: exactly the
    representative managed names. A managed name omitted by the options step is
    the one that must be cleared from the collapsed result."""
    return k == key_managed_a() or k == key_managed_b()
# pure-end


def reduced_create_options(self_options: Dict[int, int],
                           operation_options: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    # Both inputs are read-only here: HALF permission, never written. (Held
    # read-only so the operation cannot satisfy its postcondition by overwriting
    # an input; the result is a fresh mapping.)
    Requires(Acc(dict_pred(self_options), 1 / 2))
    Requires(Acc(dict_pred(operation_options), 1 / 2))
    # Carrier integrity: an option-name token is a genuine int. (bool is a
    # subtype of int in Python; a bool key would be a distinct mapping key that
    # still compares int-equal to a name token, i.e. an object outside the
    # option-name carrier. Both inputs carry name tokens only.)
    Requires(Forall(int, lambda k: Implies(k in self_options,
                                           not isinstance(k, bool))))
    Requires(Forall(int, lambda k: Implies(k in operation_options,
                                           not isinstance(k, bool))))
    # pre-conditions-end
    # post-conditions-start
    # Inputs returned untouched at the same half permission.
    Ensures(Acc(dict_pred(self_options), 1 / 2))
    Ensures(Acc(dict_pred(operation_options), 1 / 2))
    # A fresh, full-permission result mapping.
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # The clauses below cover EVERY option name k (the managed family is
    # finite -- exactly the is_managed_option members -- so its clause is
    # stated pointwise per member; the others quantify over all names).
    # Together they pin Result() as a total function of the two inputs: for
    # each k exactly one clause's antecedent applies, so no behaviourally-
    # distinct implementation can satisfy them.
    # (1) EVERY name provided by the options step -> the options step's value
    #     wins over the creation step's value.
    Ensures(Forall(int, lambda k: Implies(k in operation_options,
                                          k in Result()
                                          and Result()[k] == operation_options[k])))
    # (2) EVERY MANAGED name NOT provided by the options step -> cleared, even
    #     if the creation step carried it. The managed family is exactly
    #     {key_managed_a, key_managed_b} (= is_managed_option), so these two
    #     clauses cover every managed name.
    Ensures(Implies(key_managed_a() not in operation_options,
                    key_managed_a() not in Result()))
    Ensures(Implies(key_managed_b() not in operation_options,
                    key_managed_b() not in Result()))
    # (3) EVERY OTHER (non-managed) name not provided by the options step but on
    #     the creation step -> the creation step's value is kept.
    Ensures(Forall(int, lambda k: Implies(not is_managed_option(k)
                                          and k not in operation_options
                                          and k in self_options,
                                          k in Result()
                                          and Result()[k] == self_options[k])))
    # No foreign name: the result mentions nothing neither step does (with (3),
    # this also gives: a name on neither step, or a non-managed name omitted by
    # the options step and absent from the creation step, is absent).
    Ensures(Forall(int, lambda k: Implies(k in Result(),
                                          k in self_options or k in operation_options)))
    # post-conditions-end
    # impl-start
    # Step 1: merge -- the options step's values win over the creation step's.
    options = merge_options(self_options, operation_options)
    # Step 2 (the new logic): clear every managed name the options step does not
    # provide, so the options step's mapping is the complete set of managed
    # options on the collapsed creation step.
    if key_managed_a() not in operation_options:
        options = without_key(options, key_managed_a())
    if key_managed_b() not in operation_options:
        options = without_key(options, key_managed_b())
    return options
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY (refinement fidelity, plan §4; A-legs focus). Bundle spec: reduced_create_options pins Result() TOTALLY on the int carrier {0=key_managed_a,1=key_managed_b managed; 2=key_other non-managed}: (1) k in operation_options -> Result[k]==operation_options[k]; (2a/2b) each managed key absent from op -> absent from Result; (3) non-managed self key absent from op -> kept; no-foreign closure. Every key's membership AND value is fixed, so any behaviourally-distinct impl is rejected.

TOOLING: python python; SBU_BENCHMARK_DIR=benchmark-verified. Ran from that root with the concurrent runs FSx-HOME env.

SAME-SPEC (python -m swebench_unified.adversary same-spec nagini django__django-13786 <f>): all 8 attacks + positive_control + prepatch = SAME (exit 0), so no attack cheats by weakening a contract.

WEAKNESS (python -m swebench_unified.adversary weakness nagini django__django-13786 <f>), run concurrently in 3 batches of <=3 (each a JVM+Z3):
  atk_1 prepatch/bare-merge (no clearing): NOT-A-COUNTEREXAMPLE, fails clause (2). Reproduces the recorded prepatch bug. exit 2.
  atk_2 partial-domain (clears only key_managed_a): fails, exit 2.
  atk_3 boundary (unconditional clear of BOTH managed, even when op provides): fails clause (1), exit 2.
  atk_4 control-flow-effect (inverted guard: clears when key IS in op): fails, exit 2.
  atk_5 over-clear (also drops key_other unconditionally): fails clause (3), exit 2.
  atk_6 wrong-merge-order (merge_options(op,self) => self wins overlap): fails clause (1) on overlap, exit 2.
  atk_7 ungrounded-guard (guards on self_options membership instead of operation_options): fails, exit 2.
  atk_8 correct ECHO (behaviourally identical to gold; clears the two managed keys in swapped order): CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 40.9s, exit 0).
Positive control (unmodified model.py) VERIFIED in 41.2s (adversary verify, exit 0).

MANDATORY RESOLVE ON THE ONLY CANDIDATE: atk_8's faithful refined patch (patch_atk8.diff; merge then `for key in reversed(operation.ALTER_OPTION_KEYS): if key not in operation.options: options.pop(key,None)` — reversed iteration mirrors the swapped clear order; pop over distinct keys is order-independent) was RUN through the official harness via swebench_unified.harness.run_resolve('django__django-13786', patch, timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. FAIL_TO_PASS test_create_model_and_remove_model_options PASS; all 33 PASS_TO_PASS PASS; no failures. So the sole verifying candidate is CORRECT (verify=>correct held) — NOT a weakness.

G-AX: axiom_check.py exit 0 (merge_options/without_key sound vs real {**a,**b} / dict.pop residue on 2 F2P + 10 boundary + int-carrier + 20000 fuzz; composition == gold reduce-options computation).

REFINEMENT.MD AUDIT: all legs R / A-consumed / I; no kind-3. Both axioms are A-consumed (unchanged language primitives the NEW clearing logic composes), each the weakest sufficient contract, each G-AX-checked against the real callee (mapping.md §3.1/§3.2). The genuinely-changed op (which managed keys to clear) is modeled DEEPLY in the impl (guarded clearing branches), not hidden behind an axiom. meta.json deep_model_references=[] => no A-reference legs. Symbol<->repo binding (mapping.md §1) and the int-token carrier (§2) are faithful.

VERDICT: SOUND. 8 distinct attacks run + positive control + prepatch reproduced; every behaviourally-wrong impl rejected by the total spec; the only verifying candidate is a correct echo whose faithful patch RESOLVES under the official harness. No verifying wrong impl exists => verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-13786.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a model-creation step and a subsequent model-options step on the same
  model are collapsed into a single model-creation step, the options carried by
  the collapsed step must be EXACTLY the options the model would have after the
  options step is applied to the freshly-created model -- not merely the union
  of the two option mappings.

  The options step distinguishes two kinds of option name:

    * a MANAGED option name (one of the established family of metadata options
      the options step is allowed to set, compare, and clear); and
    * any OTHER option name (a setting outside that family).

  Applying the options step yields, for each option name k:

    (1) if k is provided by the options step, the value the options step gives
        it (the options step's value wins over the creation step's value);
    (2) else if k is a MANAGED option name, k is ABSENT from the result -- a
        managed option the creation step had but the options step does not
        provide is cleared, because the options step's mapping is the complete
        intended set of managed options;
    (3) else (k is an OTHER option name not provided by the options step), k
        keeps the creation step's value if the creation step had it, and is
        absent otherwise.

  The result carries no option name that neither the creation step nor the
  options step mentions. Clause (2) is the behaviour that matters: a managed
  option present on the creation step but omitted by the options step must NOT
  survive into the collapsed creation step.

Modelling choices (Nagini fragment):
  * An option mapping is a ``Dict[int, int]`` from an option-name token to an
    option-value token; only membership and per-name value are observed, so
    integer-keyed identity is the faithful carrier (mapping.md §2).
  * The managed-option family is the deep, definite predicate ``is_managed_
    option`` over a finite family of representative option-name tokens
    (mapping.md §2), not an opaque oracle. ``key_managed_a`` / ``key_managed_b``
    are managed names; ``key_other`` is a name outside the managed family.
    Behaviours (1)/(3) and the no-foreign-name closure are quantified over
    EVERY option name; behaviour (2) is stated per member of the (finite)
    managed family, which covers every managed name.
  * The two unchanged language primitives the step composes -- the mapping
    merge ``{**a, **b}`` and the removal of one name ``d.pop(k, None)`` /
    ``{kk: vv for kk, vv in d.items() if kk != k}`` -- are the axiomatised
    callees ``merge_options`` / ``without_key`` (A-consumed), validated against
    real Python out-of-band (axiom_check.py, G-AX). The NEW logic -- deciding
    which managed names to clear -- is spelled out deeply in the impl region.

Both input mappings are read-only here (the step allocates a fresh result and
never writes either input), so each is held at HALF permission (Required AND
Ensured); the axiomatised callees take only QUARTER permission so quantified
facts about the inputs are preserved across the calls. No string indexing is
used (Nagini bans it). Markers (machine-parsed) delimit the spec / proof /
impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
@ContractOnly
def merge_options(a: Dict[int, int], b: Dict[int, int]) -> Dict[int, int]:
    """Standard mapping merge ``{**a, **b}`` (an unchanged language primitive
    the step composes): a FRESH mapping holding every name of ``a`` and ``b``;
    ``b``'s value wins where both carry a name, otherwise ``a``'s value. The
    result is a new object, so neither input is mutated (both read-only).
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(a), 1 / 4))
    Requires(Acc(dict_pred(b), 1 / 4))
    Ensures(Acc(dict_pred(a), 1 / 4))
    Ensures(Acc(dict_pred(b), 1 / 4))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # b's value wins where b carries the name ...
    Ensures(Forall(int, lambda k: Implies(k in b, k in Result() and Result()[k] == b[k])))
    # ... a's value carries elsewhere ...
    Ensures(Forall(int, lambda k: Implies(k in a and k not in b,
                                          k in Result() and Result()[k] == a[k])))
    # ... and the result holds no name outside a's and b's names.
    Ensures(Forall(int, lambda k: Implies(k in Result(), k in a or k in b)))


@ContractOnly
def without_key(d: Dict[int, int], k: int) -> Dict[int, int]:
    """Standard removal of one name ``{kk: vv for kk, vv in d.items() if kk != k}``
    / ``d.pop(k, None)`` returning the residue (an unchanged language primitive):
    a FRESH mapping equal to ``d`` with the single name ``k`` removed. ``d`` is
    read-only (the result is a new object). Provenance + executable soundness
    check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(dict_pred(d), 1 / 4))
    Ensures(Acc(dict_pred(d), 1 / 4))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # the removed name is gone ...
    Ensures(k not in Result())
    # ... every other name of d is carried through with its value ...
    Ensures(Forall(int, lambda j: Implies(j != k and j in d,
                                          j in Result() and Result()[j] == d[j])))
    # ... and the result introduces no name d did not have.
    Ensures(Forall(int, lambda j: Implies(j in Result(),
                                          j != k and j in d and Result()[j] == d[j])))
# axioms-end


# pure-start
@Pure
def key_managed_a() -> int:
    # A representative MANAGED option name (one the options step may set/clear).
    return 0


@Pure
def key_managed_b() -> int:
    # A second, distinct representative MANAGED option name.
    return 1


@Pure
def key_other() -> int:
    # A representative option name OUTSIDE the managed family (the options step
    # neither compares nor clears it).
    return 2


@Pure
def is_managed_option(k: int) -> bool:
    """The definite membership test for the managed-option family: exactly the
    representative managed names. A managed name omitted by the options step is
    the one that must be cleared from the collapsed result."""
    return k == key_managed_a() or k == key_managed_b()
# pure-end


def reduced_create_options(self_options: Dict[int, int],
                           operation_options: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    # Both inputs are read-only here: HALF permission, never written. (Held
    # read-only so the operation cannot satisfy its postcondition by overwriting
    # an input; the result is a fresh mapping.)
    Requires(Acc(dict_pred(self_options), 1 / 2))
    Requires(Acc(dict_pred(operation_options), 1 / 2))
    # Carrier integrity: an option-name token is a genuine int. (bool is a
    # subtype of int in Python; a bool key would be a distinct mapping key that
    # still compares int-equal to a name token, i.e. an object outside the
    # option-name carrier. Both inputs carry name tokens only.)
    Requires(Forall(int, lambda k: Implies(k in self_options,
                                           not isinstance(k, bool))))
    Requires(Forall(int, lambda k: Implies(k in operation_options,
                                           not isinstance(k, bool))))
    # pre-conditions-end
    # post-conditions-start
    # Inputs returned untouched at the same half permission.
    Ensures(Acc(dict_pred(self_options), 1 / 2))
    Ensures(Acc(dict_pred(operation_options), 1 / 2))
    # A fresh, full-permission result mapping.
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # The clauses below cover EVERY option name k (the managed family is
    # finite -- exactly the is_managed_option members -- so its clause is
    # stated pointwise per member; the others quantify over all names).
    # Together they pin Result() as a total function of the two inputs: for
    # each k exactly one clause's antecedent applies, so no behaviourally-
    # distinct implementation can satisfy them.
    # (1) EVERY name provided by the options step -> the options step's value
    #     wins over the creation step's value.
    Ensures(Forall(int, lambda k: Implies(k in operation_options,
                                          k in Result()
                                          and Result()[k] == operation_options[k])))
    # (2) EVERY MANAGED name NOT provided by the options step -> cleared, even
    #     if the creation step carried it. The managed family is exactly
    #     {key_managed_a, key_managed_b} (= is_managed_option), so these two
    #     clauses cover every managed name.
    Ensures(Implies(key_managed_a() not in operation_options,
                    key_managed_a() not in Result()))
    Ensures(Implies(key_managed_b() not in operation_options,
                    key_managed_b() not in Result()))
    # (3) EVERY OTHER (non-managed) name not provided by the options step but on
    #     the creation step -> the creation step's value is kept.
    Ensures(Forall(int, lambda k: Implies(not is_managed_option(k)
                                          and k not in operation_options
                                          and k in self_options,
                                          k in Result()
                                          and Result()[k] == self_options[k])))
    # No foreign name: the result mentions nothing neither step does (with (3),
    # this also gives: a name on neither step, or a non-managed name omitted by
    # the options step and absent from the creation step, is absent).
    Ensures(Forall(int, lambda k: Implies(k in Result(),
                                          k in self_options or k in operation_options)))
    # post-conditions-end
    # impl-start
    # Step 1: merge -- the options step's values win over the creation step's.
    options = merge_options(self_options, operation_options)
    # Step 2 (the new logic): clear every managed name the options step does not
    # provide, so the options step's mapping is the complete set of managed
    # options on the collapsed creation step.
    if key_managed_a() not in operation_options:
        options = without_key(options, key_managed_a())
    if key_managed_b() not in operation_options:
        options = without_key(options, key_managed_b())
    return options
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY (refinement fidelity, plan §4; A-legs focus). Bundle spec: reduced_create_options pins Result() TOTALLY on the int carrier {0=key_managed_a,1=key_managed_b managed; 2=key_other non-managed}: (1) k in operation_options -> Result[k]==operation_options[k]; (2a/2b) each managed key absent from op -> absent from Result; (3) non-managed self key absent from op -> kept; no-foreign closure. Every key's membership AND value is fixed, so any behaviourally-distinct impl is rejected.

TOOLING: python python; SBU_BENCHMARK_DIR=benchmark-verified. Ran from that root with the concurrent runs FSx-HOME env.

SAME-SPEC (python -m swebench_unified.adversary same-spec nagini django__django-13786 <f>): all 8 attacks + positive_control + prepatch = SAME (exit 0), so no attack cheats by weakening a contract.

WEAKNESS (python -m swebench_unified.adversary weakness nagini django__django-13786 <f>), run concurrently in 3 batches of <=3 (each a JVM+Z3):
  atk_1 prepatch/bare-merge (no clearing): NOT-A-COUNTEREXAMPLE, fails clause (2). Reproduces the recorded prepatch bug. exit 2.
  atk_2 partial-domain (clears only key_managed_a): fails, exit 2.
  atk_3 boundary (unconditional clear of BOTH managed, even when op provides): fails clause (1), exit 2.
  atk_4 control-flow-effect (inverted guard: clears when key IS in op): fails, exit 2.
  atk_5 over-clear (also drops key_other unconditionally): fails clause (3), exit 2.
  atk_6 wrong-merge-order (merge_options(op,self) => self wins overlap): fails clause (1) on overlap, exit 2.
  atk_7 ungrounded-guard (guards on self_options membership instead of operation_options): fails, exit 2.
  atk_8 correct ECHO (behaviourally identical to gold; clears the two managed keys in swapped order): CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 40.9s, exit 0).
Positive control (unmodified model.py) VERIFIED in 41.2s (adversary verify, exit 0).

MANDATORY RESOLVE ON THE ONLY CANDIDATE: atk_8's faithful refined patch (patch_atk8.diff; merge then `for key in reversed(operation.ALTER_OPTION_KEYS): if key not in operation.options: options.pop(key,None)` — reversed iteration mirrors the swapped clear order; pop over distinct keys is order-independent) was RUN through the official harness via swebench_unified.harness.run_resolve('django__django-13786', patch, timeout=1800): RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. FAIL_TO_PASS test_create_model_and_remove_model_options PASS; all 33 PASS_TO_PASS PASS; no failures. So the sole verifying candidate is CORRECT (verify=>correct held) — NOT a weakness.

G-AX: axiom_check.py exit 0 (merge_options/without_key sound vs real {**a,**b} / dict.pop residue on 2 F2P + 10 boundary + int-carrier + 20000 fuzz; composition == gold reduce-options computation).

REFINEMENT.MD AUDIT: all legs R / A-consumed / I; no kind-3. Both axioms are A-consumed (unchanged language primitives the NEW clearing logic composes), each the weakest sufficient contract, each G-AX-checked against the real callee (mapping.md §3.1/§3.2). The genuinely-changed op (which managed keys to clear) is modeled DEEPLY in the impl (guarded clearing branches), not hidden behind an axiom. meta.json deep_model_references=[] => no A-reference legs. Symbol<->repo binding (mapping.md §1) and the int-token carrier (§2) are faithful.

VERDICT: SOUND. 8 distinct attacks run + positive control + prepatch reproduced; every behaviourally-wrong impl rejected by the total spec; the only verifying candidate is a correct echo whose faithful patch RESOLVES under the official harness. No verifying wrong impl exists => verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for the modeled `reduced_create_options` (the AlterModelOptions branch of CreateModel.reduce, gold/post-patch behavior at base_commit bb64b99b). No divergence found; spec is faithful and not too strong.

Evidence:
1. Spec region byte-identical: `same-spec` returns SAME on the identity attack (exit 0).
2. Model verifies under pinned Nagini (Verification successful, 45s). axiom_check.py exit 0: axiomatized merge_options/without_key match real {**a,**b}/dict.pop, and their composition equals the gold reduce-options computation over F2P + boundary + int-carrier + 20k fuzz.
3. Spec vs real gold behavior: I derived the SPEC's unique satisfying function straight from the postconditions (clause1 op-wins; clause2 managed-omitted->absent for keys {0,1}; clause3 non-managed-omitted-but-in-self->kept; no-foreign-name), independent of the impl, and compared it against the real post-patch gold computation on the int carrier (managed={0,1}). 0 divergences over 6561 EXHAUSTIVE key/value pairs (keys {0,1,2,3}, vals {0,1}) + 200,000 randomized fuzz pairs (keys 0..6).
4. Abstraction soundness (11 real ALTER_OPTION_KEYS modeled by 2 representatives + 1 non-managed): verified the real repo behavior is strictly per-key independent — each key's fate is a pure function of (in-self?, self-val, in-op?, op-val, managed?) with no cross-key interaction — 0 violations over 300,000 fuzz pairs on the real string keys with all 11 managed keys + 5 non-managed. Therefore the finite-representative modeling with clauses (1)/(3)/closure quantified over every int and (2) stated per managed member loses no distinction; the spec pins exactly the gold function.

Conclusion: the modeled function agrees with the real repo callee (gold post-patch) on every abstracted input; spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (rep.passed=True, no hard failures): no diff markers, no gold-patch line reproduced (>=8 char normalized), no patched file path (django/db/migrations/operations/models.py) or dotted module path in the spec view, no spec-view identifier embedding the sole distinctive changed symbol 'reduce', and no bug/fix narration terms in comments/docstrings. Substantive judgment: the spec view discloses nothing about the gold edit beyond the PUBLIC problem_statement. The problem_statement already names the exact fix in the clear: it states CreateModel.reduce() sets options={**self.options, **operation.options} 'with no logic to remove options not found in operation.options as is found in AlterModelOptions.state_forwards()'. That IS the gold patch (merge, then pop each ALTER_OPTION_KEY not present in operation.options). The spec view merely restates the desired end behavior in abstracted form — a managed option name omitted by the options step must be cleared (clause 2), provided names win (1), other names kept (3), no foreign names — using neutral carriers (Dict[int,int], is_managed_option, key_managed_a/b, merge_options, without_key). It names neither the patched file, the changed method 'reduce', ALTER_OPTION_KEYS, nor state_forwards in the consumer-visible view (the state_forwards reference lives only in mapping.md, marked 'for the audit only -- not referenced from the consumer spec view'). A faithful spec must state the correct behavior; here that behavior is strictly a subset of what the public task already reveals, so there is no gold-reconstruction leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, which ships in this bundle, so a reader can start there.
