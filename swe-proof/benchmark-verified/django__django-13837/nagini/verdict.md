# P2 adversarial audit — django__django-13837

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
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,15 +86,6 @@
     # pre-conditions-start
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    # Total correctness: this method must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is input-dependent
-    # rather than the constant 2 because a caller may be child_arguments itself:
-    # a self-call needs a level strictly BELOW its caller's, which no constant
-    # can provide (2 > 2 is false). len(argv) >= 1 makes this always >= 2, so
-    # the level-2 guarantee is retained and there is room beneath the caller for
-    # a self-call on a shorter argument vector. This demands termination of every
-    # input the method already accepted -- no input is excluded.
-    Requires(MustTerminate(len(argv) + 1))
     # pre-conditions-end
     # post-conditions-start
     # (A) Module launch: re-invoke the launched package as a module. After the
@@ -117,8 +107,8 @@
                     Result() == windows_recovery()))
     # post-conditions-end
     # impl-start
-    if package_reported and len(launch_package) > 0:
-        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
+    if package_reported and launch_package == PSeq(100, 106, 97, 110, 103, 111):
+        return prefix + PSeq(dash_m(), PSeq(100, 106, 97, 110, 103, 111)) + argv.drop(1)
     elif not script_exists:
         return windows_recovery()
     else:
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,15 +86,6 @@
     # pre-conditions-start
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    # Total correctness: this method must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is input-dependent
-    # rather than the constant 2 because a caller may be child_arguments itself:
-    # a self-call needs a level strictly BELOW its caller's, which no constant
-    # can provide (2 > 2 is false). len(argv) >= 1 makes this always >= 2, so
-    # the level-2 guarantee is retained and there is room beneath the caller for
-    # a self-call on a shorter argument vector. This demands termination of every
-    # input the method already accepted -- no input is excluded.
-    Requires(MustTerminate(len(argv) + 1))
     # pre-conditions-end
     # post-conditions-start
     # (A) Module launch: re-invoke the launched package as a module. After the
@@ -117,7 +107,7 @@
                     Result() == windows_recovery()))
     # post-conditions-end
     # impl-start
-    if package_reported and len(launch_package) > 0:
+    if package_reported and len(launch_package) >= 0:
         return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
     elif not script_exists:
         return windows_recovery()
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,15 +86,6 @@
     # pre-conditions-start
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    # Total correctness: this method must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is input-dependent
-    # rather than the constant 2 because a caller may be child_arguments itself:
-    # a self-call needs a level strictly BELOW its caller's, which no constant
-    # can provide (2 > 2 is false). len(argv) >= 1 makes this always >= 2, so
-    # the level-2 guarantee is retained and there is room beneath the caller for
-    # a self-call on a shorter argument vector. This demands termination of every
-    # input the method already accepted -- no input is excluded.
-    Requires(MustTerminate(len(argv) + 1))
     # pre-conditions-end
     # post-conditions-start
     # (A) Module launch: re-invoke the launched package as a module. After the
@@ -117,10 +107,10 @@
                     Result() == windows_recovery()))
     # post-conditions-end
     # impl-start
-    if package_reported and len(launch_package) > 0:
+    if not script_exists:
+        return windows_recovery()
+    elif package_reported and len(launch_package) > 0:
         return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
-    elif not script_exists:
-        return windows_recovery()
     else:
         return prefix + argv
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,15 +86,6 @@
     # pre-conditions-start
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    # Total correctness: this method must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is input-dependent
-    # rather than the constant 2 because a caller may be child_arguments itself:
-    # a self-call needs a level strictly BELOW its caller's, which no constant
-    # can provide (2 > 2 is false). len(argv) >= 1 makes this always >= 2, so
-    # the level-2 guarantee is retained and there is room beneath the caller for
-    # a self-call on a shorter argument vector. This demands termination of every
-    # input the method already accepted -- no input is excluded.
-    Requires(MustTerminate(len(argv) + 1))
     # pre-conditions-end
     # post-conditions-start
     # (A) Module launch: re-invoke the launched package as a module. After the
@@ -118,7 +108,7 @@
     # post-conditions-end
     # impl-start
     if package_reported and len(launch_package) > 0:
-        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
+        return prefix + PSeq(dash_m(), launch_package) + argv
     elif not script_exists:
         return windows_recovery()
     else:
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,15 +86,6 @@
     # pre-conditions-start
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    # Total correctness: this method must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is input-dependent
-    # rather than the constant 2 because a caller may be child_arguments itself:
-    # a self-call needs a level strictly BELOW its caller's, which no constant
-    # can provide (2 > 2 is false). len(argv) >= 1 makes this always >= 2, so
-    # the level-2 guarantee is retained and there is room beneath the caller for
-    # a self-call on a shorter argument vector. This demands termination of every
-    # input the method already accepted -- no input is excluded.
-    Requires(MustTerminate(len(argv) + 1))
     # pre-conditions-end
     # post-conditions-start
     # (A) Module launch: re-invoke the launched package as a module. After the
@@ -122,5 +112,5 @@
     elif not script_exists:
         return windows_recovery()
     else:
-        return prefix + argv
+        return windows_recovery()
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,15 +86,6 @@
     # pre-conditions-start
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    # Total correctness: this method must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is input-dependent
-    # rather than the constant 2 because a caller may be child_arguments itself:
-    # a self-call needs a level strictly BELOW its caller's, which no constant
-    # can provide (2 > 2 is false). len(argv) >= 1 makes this always >= 2, so
-    # the level-2 guarantee is retained and there is room beneath the caller for
-    # a self-call on a shorter argument vector. This demands termination of every
-    # input the method already accepted -- no input is excluded.
-    Requires(MustTerminate(len(argv) + 1))
     # pre-conditions-end
     # post-conditions-start
     # (A) Module launch: re-invoke the launched package as a module. After the
@@ -118,7 +108,7 @@
     # post-conditions-end
     # impl-start
     if package_reported and len(launch_package) > 0:
-        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
+        return prefix + PSeq(launch_package, dash_m()) + argv.drop(1)
     elif not script_exists:
         return windows_recovery()
     else:
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -87,15 +86,6 @@
     # pre-conditions-start
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    # Total correctness: this method must TERMINATE, not merely satisfy the
-    # postconditions on runs that reach the return. The level is input-dependent
-    # rather than the constant 2 because a caller may be child_arguments itself:
-    # a self-call needs a level strictly BELOW its caller's, which no constant
-    # can provide (2 > 2 is false). len(argv) >= 1 makes this always >= 2, so
-    # the level-2 guarantee is retained and there is room beneath the caller for
-    # a self-call on a shorter argument vector. This demands termination of every
-    # input the method already accepted -- no input is excluded.
-    Requires(MustTerminate(len(argv) + 1))
     # pre-conditions-end
     # post-conditions-start
     # (A) Module launch: re-invoke the launched package as a module. After the
@@ -118,7 +108,7 @@
     # post-conditions-end
     # impl-start
     if package_reported and len(launch_package) > 0:
-        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
+        return prefix + PSeq(dash_m(), launch_package) + argv.drop(2)
     elif not script_exists:
         return windows_recovery()
     else:
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-13837.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A development server, when it relaunches itself in a child process, must
  reconstruct the command line that started it. The reconstruction has to
  preserve HOW the program was started.

  When the program was started as a module -- i.e. with the interpreter's
  ``-m PACKAGE`` form -- the child command line must re-invoke that SAME
  package as a module: after the constant leading arguments (interpreter and
  warning options) it must contain the module-execution flag immediately
  followed by the package that was launched, and then the original program
  arguments (everything in the argument vector after the entry script). The
  package re-invoked must be the package that was actually launched -- whatever
  it is -- not a constant, built-in package name. A program is recognised as
  module-launched exactly when the launch reports a launch package AND that
  reported package name is non-empty; a launch that reports no package, or
  reports an empty package name (a plain script / directory launch), is not a
  module launch and is reconstructed by its argument vector as-is.

  When the program was NOT started as a module and its entry script still
  exists, the child command line is simply the leading arguments followed by
  the whole original argument vector (the entry script included). When the
  entry script no longer exists, a platform-specific recovery path applies;
  that path is unchanged here and is represented abstractly.

Strings are modelled as ``PSeq[int]`` of Unicode code points and the argument
vector as ``PSeq[PSeq[int]]`` of its elements (Nagini bans ``str`` indexing).
The leading arguments, the argument vector, and the launch-package name are
immutable pure-sequence values (read-only inputs -- pure values cannot be
mutated, so directive-5 read-only safety holds by construction). Whether a
launch package was reported at all is the boolean ``package_reported``. The
module-launch test is modelled deeply by the pure predicate
``is_module_launch`` (a reported, non-empty launch package); no callee is
axiomatized -- the launch detection that the change is about is spelled out,
not hidden behind an axiom, and is validated against its real runtime
semantics out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The launch-detection predicate -- "a module launch is one
# that reports a non-empty launch package" -- and the re-invocation of that very
# package are modelled deeply by `is_module_launch` and direct use of the
# reported package below; they are validated against the real
# `__main__.__spec__`/`.parent` runtime semantics out-of-band by axiom_check.py
# (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def dash_m() -> PSeq[int]:
    # The module-execution flag '-m'.
    return PSeq(45, 109)


@Pure
def windows_recovery() -> PSeq[PSeq[int]]:
    # Abstract sentinel for the unchanged platform-specific recovery path taken
    # when the entry script no longer exists. Distinct from any normally-built
    # argument vector (it carries the single recovery marker element [0]).
    return PSeq(PSeq(0))


@Pure
def is_module_launch(package_reported: bool, launch_package: PSeq[int]) -> bool:
    """The program was started as a module exactly when a launch package is
    reported and its name is non-empty (deep model of `__main__.__spec__ is not
    None and __main__.__spec__.parent`; validated == real runtime semantics by
    G-AX)."""
    return package_reported and len(launch_package) > 0
# pure-end


def child_arguments(prefix: PSeq[PSeq[int]],
                    package_reported: bool,
                    launch_package: PSeq[int],
                    argv: PSeq[PSeq[int]],
                    script_exists: bool) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # The argument vector always carries at least the entry script element.
    Requires(len(argv) >= 1)
    # pre-conditions-end
    # post-conditions-start
    # (A) Module launch: re-invoke the launched package as a module. After the
    # leading arguments comes the module flag, then the launched package ITSELF,
    # then the original program arguments (argv minus the entry script). The
    # emitted package is grounded in the reported package -- not any constant.
    Ensures(Implies(is_module_launch(package_reported, launch_package),
                    Result() == prefix
                    + PSeq(dash_m(), launch_package)
                    + argv.drop(1)))
    # (B) Not a module launch, entry script present: leading args then the whole
    # argument vector unchanged (entry script included).
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and script_exists,
                    Result() == prefix + argv))
    # (C) Not a module launch, entry script absent: the unchanged recovery path.
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and not script_exists,
                    Result() == windows_recovery()))
    # post-conditions-end
    # impl-start
    if package_reported and len(launch_package) > 0:
        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
    elif not script_exists:
        return windows_recovery()
    else:
        return prefix + argv
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PY=python (only this env has swebench_unified). Commands run from project root.

SPEC ANALYSIS: child_arguments has 3 postcondition Implies clauses over Requires domain len(argv)>=1: (A) is_module_launch -> Result==prefix+PSeq(dash_m(),launch_package)+argv.drop(1); (B) not module & script_exists -> Result==prefix+argv; (C) not module & not script_exists -> Result==windows_recovery(). is_module_launch = package_reported and len(launch_package)>0. The three guards are EXHAUSTIVE and MUTUALLY EXCLUSIVE over the domain, and each clause FULLY PINS Result. => spec is total & functional; any verifying impl is behaviourally identical to gold on every input, so there is no room for a verify-but-wrong impl.

### ATTACKS (all weakness -> exit 2 NOT-A-COUNTEREXAMPLE = fail verify; all confirmed same-spec exit 0):
- atk_1 ungrounded-oracle echo / prepatch-literal: guard launch_package==PSeq('django') + emit literal 'django'. same-spec=0, weakness exit=2 (fails clause A for non-django module).
- atk_2 boundary: len(launch_package)>=0 (empty pkg treated as module). same-spec=0, weakness exit=2.
- atk_3 control-flow reorder: test script_exists first. same-spec=0, weakness exit=2 (misroutes module launch when script absent).
- atk_4 control-flow-effect: emit argv (no drop(1)). same-spec=0, weakness exit=2 (fails clause A).
- atk_5 partial-domain: else returns windows_recovery(). same-spec=0, weakness exit=2 (fails clause B).
- atk_6 token-order swap: PSeq(launch_package,dash_m()). same-spec=0, weakness exit=2.
- atk_7 boundary: argv.drop(2). same-spec=0, weakness exit=2.
Command template: python -m swebench_unified.adversary weakness nagini django__django-13837 <atk>. Same-spec template: ... same-spec .... Run concurrently in batches of 3 (JVM+Z3). NO attack returned CANDIDATE, so NO faithful patch / resolve run was required.

POSITIVE CONTROL: pos_control.py = gold impl verbatim; `verify nagini` -> VERIFIED in 10.4s (exit 0).

PREPATCH: model_prepatch.py (django-literal guard) same-spec=0; nagini_verify -> Verification failed, postcondition of child_arguments (clause A, the is_module_launch implication) might not hold at 95:13 -> G-DIFF: spec senses the change.

A-LEG / REFINEMENT AUDIT: axioms region EMPTY -> NO A-consumed legs (verified model.py:46-53; refinement.md B confirms no consumed @ContractOnly axiom). Legs A2/A3/A4 = A-reference (deep model of __main__.__spec__/.parent). is_module_launch = package_reported and len(launch_package)>0 mirrors real `__spec__ is not None and __spec__.parent` (non-empty str truthy). G-AX axiom_check.py -> exit 0, 'OK ... over 16 reconstruction checks (6 -m packages, directory launch parent='', script launch spec=None); ModuleSpec.parent rule confirmed' — builds real importlib.machinery.ModuleSpec objects, correspondence holds. Legs A1/A5/A6 = R/I (G-CONF-covered). NO kind-3 legs: the single changed op (module detection + re-emitted package) is modeled deeply in A3/A4, not hidden behind an axiom. Correspondence to real callees holds.

VERDICT: SOUND. >=5 (7) distinct same-spec wrong impls run, none verifies; prepatch reproduced; positive control verifies; A-reference (G-AX) sound; no kind-3 legs. verify=>correct holds for this bundle.

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
"""Twin-artifact model for django__django-13837.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A development server, when it relaunches itself in a child process, must
  reconstruct the command line that started it. The reconstruction has to
  preserve HOW the program was started.

  When the program was started as a module -- i.e. with the interpreter's
  ``-m PACKAGE`` form -- the child command line must re-invoke that SAME
  package as a module: after the constant leading arguments (interpreter and
  warning options) it must contain the module-execution flag immediately
  followed by the package that was launched, and then the original program
  arguments (everything in the argument vector after the entry script). The
  package re-invoked must be the package that was actually launched -- whatever
  it is -- not a constant, built-in package name. A program is recognised as
  module-launched exactly when the launch reports a launch package AND that
  reported package name is non-empty; a launch that reports no package, or
  reports an empty package name (a plain script / directory launch), is not a
  module launch and is reconstructed by its argument vector as-is.

  When the program was NOT started as a module and its entry script still
  exists, the child command line is simply the leading arguments followed by
  the whole original argument vector (the entry script included). When the
  entry script no longer exists, a platform-specific recovery path applies;
  that path is unchanged here and is represented abstractly.

Strings are modelled as ``PSeq[int]`` of Unicode code points and the argument
vector as ``PSeq[PSeq[int]]`` of its elements (Nagini bans ``str`` indexing).
The leading arguments, the argument vector, and the launch-package name are
immutable pure-sequence values (read-only inputs -- pure values cannot be
mutated, so directive-5 read-only safety holds by construction). Whether a
launch package was reported at all is the boolean ``package_reported``. The
module-launch test is modelled deeply by the pure predicate
``is_module_launch`` (a reported, non-empty launch package); no callee is
axiomatized -- the launch detection that the change is about is spelled out,
not hidden behind an axiom, and is validated against its real runtime
semantics out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The launch-detection predicate -- "a module launch is one
# that reports a non-empty launch package" -- and the re-invocation of that very
# package are modelled deeply by `is_module_launch` and direct use of the
# reported package below; they are validated against the real
# `__main__.__spec__`/`.parent` runtime semantics out-of-band by axiom_check.py
# (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def dash_m() -> PSeq[int]:
    # The module-execution flag '-m'.
    return PSeq(45, 109)


@Pure
def windows_recovery() -> PSeq[PSeq[int]]:
    # Abstract sentinel for the unchanged platform-specific recovery path taken
    # when the entry script no longer exists. Distinct from any normally-built
    # argument vector (it carries the single recovery marker element [0]).
    return PSeq(PSeq(0))


@Pure
def is_module_launch(package_reported: bool, launch_package: PSeq[int]) -> bool:
    """The program was started as a module exactly when a launch package is
    reported and its name is non-empty (deep model of `__main__.__spec__ is not
    None and __main__.__spec__.parent`; validated == real runtime semantics by
    G-AX)."""
    return package_reported and len(launch_package) > 0
# pure-end


def child_arguments(prefix: PSeq[PSeq[int]],
                    package_reported: bool,
                    launch_package: PSeq[int],
                    argv: PSeq[PSeq[int]],
                    script_exists: bool) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # The argument vector always carries at least the entry script element.
    Requires(len(argv) >= 1)
    # pre-conditions-end
    # post-conditions-start
    # (A) Module launch: re-invoke the launched package as a module. After the
    # leading arguments comes the module flag, then the launched package ITSELF,
    # then the original program arguments (argv minus the entry script). The
    # emitted package is grounded in the reported package -- not any constant.
    Ensures(Implies(is_module_launch(package_reported, launch_package),
                    Result() == prefix
                    + PSeq(dash_m(), launch_package)
                    + argv.drop(1)))
    # (B) Not a module launch, entry script present: leading args then the whole
    # argument vector unchanged (entry script included).
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and script_exists,
                    Result() == prefix + argv))
    # (C) Not a module launch, entry script absent: the unchanged recovery path.
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and not script_exists,
                    Result() == windows_recovery()))
    # post-conditions-end
    # impl-start
    if package_reported and len(launch_package) > 0:
        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
    elif not script_exists:
        return windows_recovery()
    else:
        return prefix + argv
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

PY=python (only this env has swebench_unified). Commands run from project root.

SPEC ANALYSIS: child_arguments has 3 postcondition Implies clauses over Requires domain len(argv)>=1: (A) is_module_launch -> Result==prefix+PSeq(dash_m(),launch_package)+argv.drop(1); (B) not module & script_exists -> Result==prefix+argv; (C) not module & not script_exists -> Result==windows_recovery(). is_module_launch = package_reported and len(launch_package)>0. The three guards are EXHAUSTIVE and MUTUALLY EXCLUSIVE over the domain, and each clause FULLY PINS Result. => spec is total & functional; any verifying impl is behaviourally identical to gold on every input, so there is no room for a verify-but-wrong impl.

### ATTACKS (all weakness -> exit 2 NOT-A-COUNTEREXAMPLE = fail verify; all confirmed same-spec exit 0):
- atk_1 ungrounded-oracle echo / prepatch-literal: guard launch_package==PSeq('django') + emit literal 'django'. same-spec=0, weakness exit=2 (fails clause A for non-django module).
- atk_2 boundary: len(launch_package)>=0 (empty pkg treated as module). same-spec=0, weakness exit=2.
- atk_3 control-flow reorder: test script_exists first. same-spec=0, weakness exit=2 (misroutes module launch when script absent).
- atk_4 control-flow-effect: emit argv (no drop(1)). same-spec=0, weakness exit=2 (fails clause A).
- atk_5 partial-domain: else returns windows_recovery(). same-spec=0, weakness exit=2 (fails clause B).
- atk_6 token-order swap: PSeq(launch_package,dash_m()). same-spec=0, weakness exit=2.
- atk_7 boundary: argv.drop(2). same-spec=0, weakness exit=2.
Command template: python -m swebench_unified.adversary weakness nagini django__django-13837 <atk>. Same-spec template: ... same-spec .... Run concurrently in batches of 3 (JVM+Z3). NO attack returned CANDIDATE, so NO faithful patch / resolve run was required.

POSITIVE CONTROL: pos_control.py = gold impl verbatim; `verify nagini` -> VERIFIED in 10.4s (exit 0).

PREPATCH: model_prepatch.py (django-literal guard) same-spec=0; nagini_verify -> Verification failed, postcondition of child_arguments (clause A, the is_module_launch implication) might not hold at 95:13 -> G-DIFF: spec senses the change.

A-LEG / REFINEMENT AUDIT: axioms region EMPTY -> NO A-consumed legs (verified model.py:46-53; refinement.md B confirms no consumed @ContractOnly axiom). Legs A2/A3/A4 = A-reference (deep model of __main__.__spec__/.parent). is_module_launch = package_reported and len(launch_package)>0 mirrors real `__spec__ is not None and __spec__.parent` (non-empty str truthy). G-AX axiom_check.py -> exit 0, 'OK ... over 16 reconstruction checks (6 -m packages, directory launch parent='', script launch spec=None); ModuleSpec.parent rule confirmed' — builds real importlib.machinery.ModuleSpec objects, correspondence holds. Legs A1/A5/A6 = R/I (G-CONF-covered). NO kind-3 legs: the single changed op (module detection + re-emitted package) is modeled deeply in A3/A4, not hidden behind an axiom. Correspondence to real callees holds.

VERDICT: SOUND. >=5 (7) distinct same-spec wrong impls run, none verifies; prepatch reproduced; positive control verifies; A-reference (G-AX) sound; no kind-3 legs. verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No drift found. The spec (child_arguments postconditions + is_module_launch deep predicate) is behaviorally equivalent to the real gold callee get_child_arguments (post-patch django/utils/autoreload.py:213) across the entire modeled input domain. Confirmed: (1) model.py verifies (Nagini, 9.75s, exit 0); (2) axiom_check.py G-AX passes over 16 reconstruction checks against genuine importlib.machinery.ModuleSpec objects; (3) exhaustive model-vs-gold comparison over 12 launch shapes -- module launches (-m django / utils_tests.test_module / a.b.c / x), directory launch (parent=='' => non-module), script launch (spec None => non-module), each with script_exists True/False -- yields 0 divergences. The predicate is_module_launch == (package_reported and len(launch_package)>0) faithfully mirrors '__main__.__spec__ is not None and __main__.__spec__.parent' (a non-empty parent str is truthy; empty parent for directory/zip launches is falsy). Module branch re-emits launch_package ITSELF (not the constant 'django'), matching '-m' + __spec__.parent. The Windows recovery path is unchanged by the patch (PASS_TO_PASS) and abstracted identically on both sides via the windows_recovery() sentinel gated by script_exists -- not a modeled behavior, so not a drift source. The spec is not too strong: it does not constrain the recovery body and correctly classifies empty-parent/None-spec as non-module. No input exists where the modeled function disagrees with the real repo callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard_failures). Substantive gold-reconstruction check: the spec view (model.py + pure region + Requires/Ensures) discloses nothing about the gold edit beyond the public problem_statement, which is itself unusually explicit. The problem_statement already states: the fix uses `__main__.__spec__` as Python's documented way to detect `-m`; `__main__.__spec__ is not None` iff launched with `-m` (or a dir/zip); `__main__.__spec__.parent` is the empty string for a directory/zip launch; and 'Python was started with -m pkg if and only if __main__.__spec__.parent == "pkg"'; it also states the pre-patch bug (detects only `-m django`, uses __file__). The spec's discriminating content -- is_module_launch = (package_reported and non-empty launch_package), and re-emitting the launched package itself (`-m` + launch_package, not a constant) plus the empty-string/directory non-launch case -- is a direct restatement of that public text, not new information. axiom_check.py/mapping.md references to `__main__.__spec__`/`.parent` semantics are also public (they cite the same Python docs the problem_statement cites). The auditor-side refinement.md/mapping.md quote the raw diff (pre-patch `py_script == django.__main__.__file__`, literal 'django'), but (a) those are audit artifacts, not the solver-facing spec view judged by G-PANEL-3, and (b) even their content is disclosed in prose by the problem_statement. No spec-view line narrows the solution beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
