# P2 adversarial audit — django__django-12125

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py`, `atk_9.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Acc(list_pred(module), 1 / 2))
     Requires(Acc(list_pred(simple_name), 1 / 2))
     Requires(Acc(list_pred(qualified_name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(module), 1 / 2))
@@ -103,15 +101,14 @@
     # impl-start
     if module_is_builtin:
         frag = []                            # type: List[int]
-        frag = frag + simple_name            # the bare simple name
+        frag = frag + qualified_name         # WRONG: qualified not simple
         imp = []                             # type: List[int]
         return (frag, imp)
     else:
-        # frag = module + "." + qualified_name
         frag2 = []                           # type: List[int]
         frag2 = frag2 + module
-        frag2 = frag2 + [46]                 # '.'
+        frag2 = frag2 + [46]
         frag2 = frag2 + qualified_name
-        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+        imp2 = [105, 109, 112, 111, 114, 116, 32] + module
         return (frag2, imp2)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Acc(list_pred(module), 1 / 2))
     Requires(Acc(list_pred(simple_name), 1 / 2))
     Requires(Acc(list_pred(qualified_name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(module), 1 / 2))
@@ -103,15 +101,13 @@
     # impl-start
     if module_is_builtin:
         frag = []                            # type: List[int]
-        frag = frag + simple_name            # the bare simple name
+        frag = frag + simple_name
         imp = []                             # type: List[int]
         return (frag, imp)
     else:
-        # frag = module + "." + qualified_name
         frag2 = []                           # type: List[int]
         frag2 = frag2 + module
-        frag2 = frag2 + [46]                 # '.'
-        frag2 = frag2 + qualified_name
-        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+        frag2 = frag2 + qualified_name       # WRONG: no [46] dot
+        imp2 = [105, 109, 112, 111, 114, 116, 32] + module
         return (frag2, imp2)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Acc(list_pred(module), 1 / 2))
     Requires(Acc(list_pred(simple_name), 1 / 2))
     Requires(Acc(list_pred(qualified_name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(module), 1 / 2))
@@ -103,15 +101,14 @@
     # impl-start
     if module_is_builtin:
         frag = []                            # type: List[int]
-        frag = frag + simple_name            # the bare simple name
+        frag = frag + simple_name
         imp = []                             # type: List[int]
         return (frag, imp)
     else:
-        # frag = module + "." + qualified_name
         frag2 = []                           # type: List[int]
         frag2 = frag2 + module
-        frag2 = frag2 + [46]                 # '.'
+        frag2 = frag2 + [46]
         frag2 = frag2 + qualified_name
-        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+        imp2 = [105, 109, 112, 111, 114, 116] + module   # WRONG: dropped 32 space
         return (frag2, imp2)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Acc(list_pred(module), 1 / 2))
     Requires(Acc(list_pred(simple_name), 1 / 2))
     Requires(Acc(list_pred(qualified_name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(module), 1 / 2))
@@ -101,17 +99,17 @@
                     ToSeq(Result()[1]) == import_line(ToSeq(module))))
     # post-conditions-end
     # impl-start
-    if module_is_builtin:
-        frag = []                            # type: List[int]
-        frag = frag + simple_name            # the bare simple name
-        imp = []                             # type: List[int]
-        return (frag, imp)
-    else:
-        # frag = module + "." + qualified_name
+    if not module_is_builtin:
         frag2 = []                           # type: List[int]
         frag2 = frag2 + module
-        frag2 = frag2 + [46]                 # '.'
+        frag2 = frag2 + [46]
         frag2 = frag2 + qualified_name
-        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+        imp2 = [105, 109, 112, 111, 114, 116, 32] + module
         return (frag2, imp2)
+    else:
+        # WRONG: builtin branch now emits an import
+        frag = []                            # type: List[int]
+        frag = frag + simple_name
+        imp = [105, 109, 112, 111, 114, 116, 32] + module
+        return (frag, imp)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Acc(list_pred(module), 1 / 2))
     Requires(Acc(list_pred(simple_name), 1 / 2))
     Requires(Acc(list_pred(qualified_name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(module), 1 / 2))
@@ -103,15 +101,14 @@
     # impl-start
     if module_is_builtin:
         frag = []                            # type: List[int]
-        frag = frag + simple_name            # the bare simple name
-        imp = []                             # type: List[int]
+        frag = frag + simple_name
+        imp = [105, 109, 112, 111, 114, 116, 32]  # WRONG: non-empty import
         return (frag, imp)
     else:
-        # frag = module + "." + qualified_name
         frag2 = []                           # type: List[int]
         frag2 = frag2 + module
-        frag2 = frag2 + [46]                 # '.'
+        frag2 = frag2 + [46]
         frag2 = frag2 + qualified_name
-        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+        imp2 = [105, 109, 112, 111, 114, 116, 32] + module
         return (frag2, imp2)
     # impl-end
```

Attack 6 — `atk_6.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Acc(list_pred(module), 1 / 2))
     Requires(Acc(list_pred(simple_name), 1 / 2))
     Requires(Acc(list_pred(qualified_name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(module), 1 / 2))
@@ -102,16 +100,9 @@
     # post-conditions-end
     # impl-start
     if module_is_builtin:
-        frag = []                            # type: List[int]
-        frag = frag + simple_name            # the bare simple name
-        imp = []                             # type: List[int]
-        return (frag, imp)
+        return (list(simple_name), [])
     else:
-        # frag = module + "." + qualified_name
-        frag2 = []                           # type: List[int]
-        frag2 = frag2 + module
-        frag2 = frag2 + [46]                 # '.'
-        frag2 = frag2 + qualified_name
-        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+        frag2 = (module + [46]) + qualified_name   # same value, different grouping
+        imp2 = list([105, 109, 112, 111, 114, 116, 32]) + module
         return (frag2, imp2)
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Acc(list_pred(module), 1 / 2))
     Requires(Acc(list_pred(simple_name), 1 / 2))
     Requires(Acc(list_pred(qualified_name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(module), 1 / 2))
@@ -101,17 +99,16 @@
                     ToSeq(Result()[1]) == import_line(ToSeq(module))))
     # post-conditions-end
     # impl-start
-    if module_is_builtin:
+    if not module_is_builtin:
+        frag2 = []                           # type: List[int]
+        frag2 = frag2 + module
+        frag2 = frag2 + [46]
+        frag2 = frag2 + qualified_name
+        imp2 = [105, 109, 112, 111, 114, 116, 32] + module
+        return (frag2, imp2)
+    else:
         frag = []                            # type: List[int]
-        frag = frag + simple_name            # the bare simple name
+        frag = frag + simple_name
         imp = []                             # type: List[int]
         return (frag, imp)
-    else:
-        # frag = module + "." + qualified_name
-        frag2 = []                           # type: List[int]
-        frag2 = frag2 + module
-        frag2 = frag2 + [46]                 # '.'
-        frag2 = frag2 + qualified_name
-        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
-        return (frag2, imp2)
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Acc(list_pred(module), 1 / 2))
     Requires(Acc(list_pred(simple_name), 1 / 2))
     Requires(Acc(list_pred(qualified_name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(module), 1 / 2))
@@ -103,15 +101,15 @@
     # impl-start
     if module_is_builtin:
         frag = []                            # type: List[int]
-        frag = frag + simple_name            # the bare simple name
+        frag = frag + simple_name
         imp = []                             # type: List[int]
         return (frag, imp)
     else:
-        # frag = module + "." + qualified_name
         frag2 = []                           # type: List[int]
         frag2 = frag2 + module
-        frag2 = frag2 + [46]                 # '.'
+        frag2 = frag2 + [46]
         frag2 = frag2 + qualified_name
-        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+        frag2 = frag2 + qualified_name       # WRONG: duplicated qualified_name
+        imp2 = [105, 109, 112, 111, 114, 116, 32] + module
         return (frag2, imp2)
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Acc(list_pred(module), 1 / 2))
     Requires(Acc(list_pred(simple_name), 1 / 2))
     Requires(Acc(list_pred(qualified_name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(module), 1 / 2))
@@ -103,15 +101,11 @@
     # impl-start
     if module_is_builtin:
         frag = []                            # type: List[int]
-        frag = frag + simple_name            # the bare simple name
+        frag = frag + simple_name
         imp = []                             # type: List[int]
         return (frag, imp)
     else:
-        # frag = module + "." + qualified_name
-        frag2 = []                           # type: List[int]
-        frag2 = frag2 + module
-        frag2 = frag2 + [46]                 # '.'
-        frag2 = frag2 + qualified_name
-        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
+        frag2 = [88]                         # WRONG: constant 'X', ignores inputs
+        imp2 = [105, 109, 112, 111, 114, 116, 32] + module
         return (frag2, imp2)
     # impl-end
```

Attack 10 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List, Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -79,7 +78,6 @@
     Requires(Acc(list_pred(module), 1 / 2))
     Requires(Acc(list_pred(simple_name), 1 / 2))
     Requires(Acc(list_pred(qualified_name), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(module), 1 / 2))
@@ -107,11 +105,14 @@
         imp = []                             # type: List[int]
         return (frag, imp)
     else:
-        # frag = module + "." + qualified_name
+        # PRE-PATCH (buggy): keys the rendering by the SIMPLE leaf name instead
+        # of the fully-qualified name, so a class nested inside an enclosing
+        # class is rendered as if it were a top-level attribute that merely
+        # shares the leaf name. frag = module + "." + simple_name.
         frag2 = []                           # type: List[int]
         frag2 = frag2 + module
         frag2 = frag2 + [46]                 # '.'
-        frag2 = frag2 + qualified_name
+        frag2 = frag2 + simple_name
         imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
         return (frag2, imp2)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12125.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A type (a class object) used as a value is rendered into a fragment of
  importable source code that — when later evaluated — must recover the SAME
  class object. The class carries three pieces of text and one flag:

    * the dotted path of the module the class is defined in;
    * its SIMPLE innermost name (the leaf attribute name on whatever directly
      encloses it);
    * its FULLY-QUALIFIED name within the module — the dotted chain of every
      enclosing scope down to the leaf (for a class declared at module top
      level this equals the simple name; for a class nested inside another
      class it additionally carries the dotted prefix of every enclosing
      class);
    * a flag telling whether the defining module is the built-in namespace.

  When the class lives in the built-in namespace, the fragment is just its
  simple name and there is no accompanying import (built-in types are reachable
  without importing anything and are never declared inside an enclosing class).

  Otherwise the fragment is the module path, a dot, then the FULLY-QUALIFIED
  name — so that a class declared inside another class is rendered with the
  complete enclosing chain and the evaluated fragment reaches the very same
  nested attribute (NOT a non-existent top-level attribute that merely shares
  the leaf name). Reading the texts as Unicode code-point sequences:

        module ++ "." ++ qualified_name.

  The single accompanying import statement is then the import of that module,
  and ONLY that.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification. The
two rendered forms are spelled out deeply as concatenations and validated ==
the real rendering output out-of-band by axiom_check.py (G-AX); nothing is
consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom. The whole rendering is the operation under
# change, so it is modelled DEEPLY in the `pure` region and the verified impl,
# and validated == the real rendering output by axiom_check.py / G-AX as
# A-references; nothing here is consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def dotted_path(module: PSeq[int], qualified_name: PSeq[int]) -> PSeq[int]:
    """The non-built-in rendering, keyed by the FULLY-QUALIFIED name:
    module ++ '.' ++ qualified_name. '.' == U+002E == 46."""
    return module + PSeq(46) + qualified_name


@Pure
def import_line(module: PSeq[int]) -> PSeq[int]:
    """The one accompanying import statement: "import " followed by the module
    path. "import " == U+0069 6D 70 6F 72 74 20."""
    return PSeq(105, 109, 112, 111, 114, 116, 32) + module
# pure-end


def serialize_type(module: List[int], simple_name: List[int],
                   qualified_name: List[int], module_is_builtin: bool
                   ) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All three texts are read-only inputs (fractional permission). `simple_name`
    # is supplied as the leaf name; for a non-built-in class the rendering MUST
    # be keyed by `qualified_name`, NOT by `simple_name` (the two differ exactly
    # when the class is nested inside an enclosing class).
    Requires(Acc(list_pred(module), 1 / 2))
    Requires(Acc(list_pred(simple_name), 1 / 2))
    Requires(Acc(list_pred(qualified_name), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(simple_name), 1 / 2))
    Ensures(Acc(list_pred(qualified_name), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # Built-in namespace: the fragment is the simple name, with no import.
    Ensures(Implies(module_is_builtin,
                    ToSeq(Result()[0]) == ToSeq(simple_name)))
    Ensures(Implies(module_is_builtin, len(Result()[1]) == 0))
    # Otherwise: the fragment is module ++ '.' ++ FULLY-QUALIFIED name, grounded
    # in the `qualified_name` carrier (the complete enclosing chain), and the
    # accompanying import is exactly the import of the module.
    Ensures(Implies(not module_is_builtin,
                    ToSeq(Result()[0]) ==
                    dotted_path(ToSeq(module), ToSeq(qualified_name))))
    Ensures(Implies(not module_is_builtin,
                    ToSeq(Result()[1]) == import_line(ToSeq(module))))
    # post-conditions-end
    # impl-start
    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        # frag = module + "." + qualified_name
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + [46]                 # '.'
        frag2 = frag2 + qualified_name
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) audit of django__django-12125 nagini bundle. Verdict: SOUND — no verifying wrong impl found whose faithful patch fails to resolve.

SPEC SHAPE (why it is tight): serialize_type's postconditions pin BOTH output lists EXACTLY, by ToSeq equality, in BOTH branches: built-in => ToSeq(Result()[0])==ToSeq(simple_name) AND len(Result()[1])==0; non-built-in => ToSeq(Result()[0])==dotted_path(ToSeq(module),ToSeq(qualified_name)) AND ToSeq(Result()[1])==import_line(ToSeq(module)). There is NO unconstrained output region — so any verifying impl is behaviorally identical to gold on the modeled domain (module/simple/qualified/is_builtin).

ATTACKS (10 distinct same-spec wrong-impls; each same-spec exit0, only impl region edited; cmd: `python -m swebench_unified.adversary weakness nagini django__django-12125 <path>`, run concurrently ≤3/batch):
- atk_1.py (wrong-attr/partial-domain: built-in returns qualified_name not simple_name) => weakness exit=2 (verification failed, spec rejects). GOOD.
- atk_2.py (boundary: non-built-in drops the '.' [46] separator) => exit=2. GOOD.
- atk_3.py (boundary: import prefix drops trailing space 32) => exit=2. GOOD.
- atk_4.py (control-flow-effect: swap branch bodies, built-in now emits an import) => exit=2. GOOD.
- atk_5.py (built-in emits non-empty import, violates len==0) => exit=2. GOOD.
- atk_6.py (echo written with list()/paren-grouping) => exit=2 but NOTE: cause is a Nagini translation limitation (Translation failed: generic.constructor.without.type at line 103, the `list(simple_name)` call), NOT a spec rejection. atk_7 covers the behaviorally-correct-echo case cleanly.
- atk_7.py (ECHO: negated guard `if not module_is_builtin` with branch bodies swapped to preserve semantics — behaviorally IDENTICAL to gold) => weakness exit=0 => CANDIDATE (shares spec AND verifies). MANDATORY resolve run performed (see below).
- atk_8.py (boundary/overlong: non-built-in appends qualified_name twice) => exit=2. GOOD.
- atk_9.py (ungrounded-oracle: non-built-in fragment hardcoded constant [88]='X' ignoring inputs) => exit=2. GOOD.
- atk_prepatch.py (the PREPATCH BUG, model_prepatch.py: non-built-in keyed by simple_name instead of qualified_name) => weakness exit=2, verification failed — prepatch bug REPRODUCED and REJECTED by the spec (confirms G-DIFF; the discriminating clause `ToSeq(Result()[0])==dotted_path(module,qualified_name)` fails when nested since simple_name != qualified_name).

CANDIDATE atk_7 — MATERIALIZED FAITHFUL PATCH + RESOLVE RUN (mandatory step):
atk_7's semantics: non-built-in => module ++ '.' ++ qualified_name with import 'import '++module; built-in => bare simple_name, empty import. This is exactly the gold post-patch behavior. Its faithful refined patch is therefore the gold __name__->__qualname__ edit at serializer.py:272. Materialized at atk_7_faithful_patch.diff and RUN through the official harness via swebench_unified.harness.run_resolve('django__django-12125', patch). OBSERVED RESULT (atk_7_resolve.json): {"resolved": true, "note": "resolved"}. => The verifying CANDIDATE RESOLVES, so it is NOT a counterexample; verify=>correct holds for it.

POSITIVE CONTROL: positive_control.py (= bundle model.py) verifies via scripts/nagini_verify.sh, exit 0, 13.99s (pc_verify.out).

### REFINEMENT.MD AUDIT (A-leg focus, R/I mechanically covered by G-CONF):
- All 5 legs are R / A-reference / I; NO kind-3 (unexpressible-changed-op) legs; NO consumed @ContractOnly axiom (axioms region empty).
- A1: R+I (str<->List[int]; branch bool identical; hasattr(__module__) guard + models.Model/type(None) special-cases are unchanged control-flow context, out of the modeled domain — every tested value has __module__). Correspondence OK.
- A2: I+R (unchanged built-in branch: bare name + empty import set()). Correspondence OK.
- A3: A-REFERENCE — dotted_path (module ++ PSeq(46) ++ qualified_name) corresponds to the real post-patch callee expression `"%s.%s" % (module, self.value.__qualname__)` (serializer.py:272). Validated EXECUTABLY by axiom_check.py/G-AX (recorded pass, exit 0) over explicit nested/top-level/enum/built-in classes + 20000 fuzz classes; the %s-splice of two whole strings around a literal '.' is exactly list + with [46]. Correspondence HOLDS.
- A4: A-REFERENCE — import_line ('import ' ++ module) corresponds to the singleton import set `{"import %s" % module}`. Validated by G-AX (exactly one element == import_line(module)). Correspondence HOLDS.
- A5: R (2-tuple (str,set) <-> Tuple[List[int],List[int]]; set wrapper identity on <=1 element). OK.
The discriminating content (key on fully-qualified vs bare leaf name) lives in A3 and is expressed by the spec (dotted_path keyed on qualified_name), which the prepatch violates (atk_prepatch rejected) — the spec senses the change.

Cross-check: G-AX recorded pass; G-CONF recorded pass (100030 inputs, 0 disagreements, seed 12125) — confirms the R/I legs (shadow contract-stripped impl == real patched serializer). mapping.md binds every symbol to serializer.py:259-272 @ base_commit 89d41cba, A-references' callee sources are the exact post-patch expressions.

CONCLUSION: >=5 (10) distinct same-spec wrong impls run through adversary weakness; every genuinely-wrong impl rejected by the spec; the sole verifying CANDIDATE (behavior-preserving rearrangement atk_7) had its faithful patch RUN through the official harness and it RESOLVED. Prepatch reproduced+rejected; positive control verifies; refinement A-legs sound with no kind-3. verify=>correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies (1 did not reach the verifier: the checker could not translate it, so it counts in neither tally)

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_8.py`, `atk_9.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → not a counterexample (the checker could not translate this program, so the spec never judged it)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-12125.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A type (a class object) used as a value is rendered into a fragment of
  importable source code that — when later evaluated — must recover the SAME
  class object. The class carries three pieces of text and one flag:

    * the dotted path of the module the class is defined in;
    * its SIMPLE innermost name (the leaf attribute name on whatever directly
      encloses it);
    * its FULLY-QUALIFIED name within the module — the dotted chain of every
      enclosing scope down to the leaf (for a class declared at module top
      level this equals the simple name; for a class nested inside another
      class it additionally carries the dotted prefix of every enclosing
      class);
    * a flag telling whether the defining module is the built-in namespace.

  When the class lives in the built-in namespace, the fragment is just its
  simple name and there is no accompanying import (built-in types are reachable
  without importing anything and are never declared inside an enclosing class).

  Otherwise the fragment is the module path, a dot, then the FULLY-QUALIFIED
  name — so that a class declared inside another class is rendered with the
  complete enclosing chain and the evaluated fragment reaches the very same
  nested attribute (NOT a non-existent top-level attribute that merely shares
  the leaf name). Reading the texts as Unicode code-point sequences:

        module ++ "." ++ qualified_name.

  The single accompanying import statement is then the import of that module,
  and ONLY that.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the pure sequence theory `PSeq[int]` carries the specification. The
two rendered forms are spelled out deeply as concatenations and validated ==
the real rendering output out-of-band by axiom_check.py (G-AX); nothing is
consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axiom. The whole rendering is the operation under
# change, so it is modelled DEEPLY in the `pure` region and the verified impl,
# and validated == the real rendering output by axiom_check.py / G-AX as
# A-references; nothing here is consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def dotted_path(module: PSeq[int], qualified_name: PSeq[int]) -> PSeq[int]:
    """The non-built-in rendering, keyed by the FULLY-QUALIFIED name:
    module ++ '.' ++ qualified_name. '.' == U+002E == 46."""
    return module + PSeq(46) + qualified_name


@Pure
def import_line(module: PSeq[int]) -> PSeq[int]:
    """The one accompanying import statement: "import " followed by the module
    path. "import " == U+0069 6D 70 6F 72 74 20."""
    return PSeq(105, 109, 112, 111, 114, 116, 32) + module
# pure-end


def serialize_type(module: List[int], simple_name: List[int],
                   qualified_name: List[int], module_is_builtin: bool
                   ) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All three texts are read-only inputs (fractional permission). `simple_name`
    # is supplied as the leaf name; for a non-built-in class the rendering MUST
    # be keyed by `qualified_name`, NOT by `simple_name` (the two differ exactly
    # when the class is nested inside an enclosing class).
    Requires(Acc(list_pred(module), 1 / 2))
    Requires(Acc(list_pred(simple_name), 1 / 2))
    Requires(Acc(list_pred(qualified_name), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(simple_name), 1 / 2))
    Ensures(Acc(list_pred(qualified_name), 1 / 2))
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # Built-in namespace: the fragment is the simple name, with no import.
    Ensures(Implies(module_is_builtin,
                    ToSeq(Result()[0]) == ToSeq(simple_name)))
    Ensures(Implies(module_is_builtin, len(Result()[1]) == 0))
    # Otherwise: the fragment is module ++ '.' ++ FULLY-QUALIFIED name, grounded
    # in the `qualified_name` carrier (the complete enclosing chain), and the
    # accompanying import is exactly the import of the module.
    Ensures(Implies(not module_is_builtin,
                    ToSeq(Result()[0]) ==
                    dotted_path(ToSeq(module), ToSeq(qualified_name))))
    Ensures(Implies(not module_is_builtin,
                    ToSeq(Result()[1]) == import_line(ToSeq(module))))
    # post-conditions-end
    # impl-start
    if module_is_builtin:
        frag = []                            # type: List[int]
        frag = frag + simple_name            # the bare simple name
        imp = []                             # type: List[int]
        return (frag, imp)
    else:
        # frag = module + "." + qualified_name
        frag2 = []                           # type: List[int]
        frag2 = frag2 + module
        frag2 = frag2 + [46]                 # '.'
        frag2 = frag2 + qualified_name
        imp2 = [105, 109, 112, 111, 114, 116, 32] + module   # "import " + module
        return (frag2, imp2)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity) audit of django__django-12125 nagini bundle. Verdict: SOUND — no verifying wrong impl found whose faithful patch fails to resolve.

SPEC SHAPE (why it is tight): serialize_type's postconditions pin BOTH output lists EXACTLY, by ToSeq equality, in BOTH branches: built-in => ToSeq(Result()[0])==ToSeq(simple_name) AND len(Result()[1])==0; non-built-in => ToSeq(Result()[0])==dotted_path(ToSeq(module),ToSeq(qualified_name)) AND ToSeq(Result()[1])==import_line(ToSeq(module)). There is NO unconstrained output region — so any verifying impl is behaviorally identical to gold on the modeled domain (module/simple/qualified/is_builtin).

ATTACKS (10 distinct same-spec wrong-impls; each same-spec exit0, only impl region edited; cmd: `python -m swebench_unified.adversary weakness nagini django__django-12125 <path>`, run concurrently ≤3/batch):
- atk_1.py (wrong-attr/partial-domain: built-in returns qualified_name not simple_name) => weakness exit=2 (verification failed, spec rejects). GOOD.
- atk_2.py (boundary: non-built-in drops the '.' [46] separator) => exit=2. GOOD.
- atk_3.py (boundary: import prefix drops trailing space 32) => exit=2. GOOD.
- atk_4.py (control-flow-effect: swap branch bodies, built-in now emits an import) => exit=2. GOOD.
- atk_5.py (built-in emits non-empty import, violates len==0) => exit=2. GOOD.
- atk_6.py (echo written with list()/paren-grouping) => exit=2 but NOTE: cause is a Nagini translation limitation (Translation failed: generic.constructor.without.type at line 103, the `list(simple_name)` call), NOT a spec rejection. atk_7 covers the behaviorally-correct-echo case cleanly.
- atk_7.py (ECHO: negated guard `if not module_is_builtin` with branch bodies swapped to preserve semantics — behaviorally IDENTICAL to gold) => weakness exit=0 => CANDIDATE (shares spec AND verifies). MANDATORY resolve run performed (see below).
- atk_8.py (boundary/overlong: non-built-in appends qualified_name twice) => exit=2. GOOD.
- atk_9.py (ungrounded-oracle: non-built-in fragment hardcoded constant [88]='X' ignoring inputs) => exit=2. GOOD.
- atk_prepatch.py (the PREPATCH BUG, model_prepatch.py: non-built-in keyed by simple_name instead of qualified_name) => weakness exit=2, verification failed — prepatch bug REPRODUCED and REJECTED by the spec (confirms G-DIFF; the discriminating clause `ToSeq(Result()[0])==dotted_path(module,qualified_name)` fails when nested since simple_name != qualified_name).

CANDIDATE atk_7 — MATERIALIZED FAITHFUL PATCH + RESOLVE RUN (mandatory step):
atk_7's semantics: non-built-in => module ++ '.' ++ qualified_name with import 'import '++module; built-in => bare simple_name, empty import. This is exactly the gold post-patch behavior. Its faithful refined patch is therefore the gold __name__->__qualname__ edit at serializer.py:272. Materialized at atk_7_faithful_patch.diff and RUN through the official harness via swebench_unified.harness.run_resolve('django__django-12125', patch). OBSERVED RESULT (atk_7_resolve.json): {"resolved": true, "note": "resolved"}. => The verifying CANDIDATE RESOLVES, so it is NOT a counterexample; verify=>correct holds for it.

POSITIVE CONTROL: positive_control.py (= bundle model.py) verifies via scripts/nagini_verify.sh, exit 0, 13.99s (pc_verify.out).

### REFINEMENT.MD AUDIT (A-leg focus, R/I mechanically covered by G-CONF):
- All 5 legs are R / A-reference / I; NO kind-3 (unexpressible-changed-op) legs; NO consumed @ContractOnly axiom (axioms region empty).
- A1: R+I (str<->List[int]; branch bool identical; hasattr(__module__) guard + models.Model/type(None) special-cases are unchanged control-flow context, out of the modeled domain — every tested value has __module__). Correspondence OK.
- A2: I+R (unchanged built-in branch: bare name + empty import set()). Correspondence OK.
- A3: A-REFERENCE — dotted_path (module ++ PSeq(46) ++ qualified_name) corresponds to the real post-patch callee expression `"%s.%s" % (module, self.value.__qualname__)` (serializer.py:272). Validated EXECUTABLY by axiom_check.py/G-AX (recorded pass, exit 0) over explicit nested/top-level/enum/built-in classes + 20000 fuzz classes; the %s-splice of two whole strings around a literal '.' is exactly list + with [46]. Correspondence HOLDS.
- A4: A-REFERENCE — import_line ('import ' ++ module) corresponds to the singleton import set `{"import %s" % module}`. Validated by G-AX (exactly one element == import_line(module)). Correspondence HOLDS.
- A5: R (2-tuple (str,set) <-> Tuple[List[int],List[int]]; set wrapper identity on <=1 element). OK.
The discriminating content (key on fully-qualified vs bare leaf name) lives in A3 and is expressed by the spec (dotted_path keyed on qualified_name), which the prepatch violates (atk_prepatch rejected) — the spec senses the change.

Cross-check: G-AX recorded pass; G-CONF recorded pass (100030 inputs, 0 disagreements, seed 12125) — confirms the R/I legs (shadow contract-stripped impl == real patched serializer). mapping.md binds every symbol to serializer.py:259-272 @ base_commit 89d41cba, A-references' callee sources are the exact post-patch expressions.

CONCLUSION: >=5 (10) distinct same-spec wrong impls run through adversary weakness; every genuinely-wrong impl rejected by the spec; the sole verifying CANDIDATE (behavior-preserving rearrangement atk_7) had its faithful patch RUN through the official harness and it RESOLVED. Prepatch reproduced+rejected; positive control verifies; refinement A-legs sound with no kind-3. verify=>correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift check for django__django-12125 (nagini). The modeled function serialize_type(module, simple_name, qualified_name, module_is_builtin) models TypeSerializer.serialize()'s type-rendering branch. Verified rigorously:

1. model.py verifies under the pinned Nagini verifier (Verification successful, 12.98s).
2. same-spec self-check passes (SAME), spec region byte-identical.
3. G-AX axiom_check.py passes over 20 explicit targets + 20000 fuzz classes.
4. Independent empirical probe against the REAL repo serializer:
   - At base_commit (pre-patch, uses __name__): model diverges on nested classes, which is EXPECTED because the model encodes the post-patch behavior — this is the bug the patch fixes, and G-DIFF confirms model_prepatch.py fails the discriminating postcondition.
   - After applying the gold patch (uses __qualname__): the model matches the real serializer on ALL in-domain inputs — built-ins (int/str/list/dict/object -> bare name, empty import), top-level classes (module.Name), and the central nested cases Outer.Inner / nested enum / nested IntEnum (module.Outer.Inner with {'import module'}), which are exactly the F2P shapes.

The spec is NOT too strong / does not drift: postconditions constrain output only in the two modeled branches (builtin -> simple_name, no import; non-builtin -> module ++ '.' ++ qualified_name and import_line(module)), and both agree with the post-patch callee code-point-for-code-point.

The one observed divergence, type(None) (real returns 'type(None)' via the special_cases short-circuit, model would produce 'NoneType'), is NOT a defect: type(None) is caught by the special_cases list BEFORE the module branch the function models, and mapping.md §1 / refinement.md §A1 explicitly scope the modeled function to values that reach the hasattr(__module__) branch. It is unchanged by the patch and outside the modeled domain, so it cannot be a required diverging input. No in-domain input where the spec disagrees with the real post-patch callee was found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit = `self.value.__name__` -> `self.value.__qualname__` in the non-builtin branch of TypeSerializer.serialize (render nested classes by their fully-qualified enclosing chain, not the bare leaf name). The public problem_statement ALREADY states this exact desired behavior: it reports that makemigrations emits `test1.models.Inner` when it 'should have been test1.models.Outer.Inner', and `test1.models.State` when it should be `test1.models.Thing.State`. So the simple-name-vs-qualified-name distinction is public.

Mechanical G-LEAK screen passes (rep.passed=True, no hard failures): spec view contains no diff markers, no patched file path (serializer.py) or dotted module path, no spec-view identifier or comment echoing a patched repo symbol, and no bug/fix narration. It never names the Python attributes __name__/__qualname__ nor the attribute-level edit.

The spec view (docstring + pre/post-conditions) describes the DESIRED behavior at the correct abstraction level: inputs carry both a SIMPLE innermost name and a FULLY-QUALIFIED name; the non-builtin fragment = module ++ '.' ++ qualified_name; nested classes are rendered with the complete enclosing chain 'NOT a non-existent top-level attribute that merely shares the leaf name'. This is a faithful behavioral spec of the outcome the public bug report demands (Inner vs Outer.Inner), not a disclosure of the gold edit beyond the problem_statement. Specifying already-public correct behavior is not leakage. Verified spec region byte-identical via spec_view projection; impl elided in the consumer view. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
