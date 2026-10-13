# P2 adversarial audit — django__django-14771

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -134,7 +133,6 @@
              and len(opt_is_flag) == len(opt_vals))
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The forwarded implementation-option tokens: on the reference interpreter,
@@ -163,28 +161,7 @@
                     Result() == windows_recovery()))
     # post-conditions-end
     # impl-start
-    empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
-    options = empty
-    if is_reference_impl:
-        i = len(opt_keys)
-        while i > 0:
-            # invariants-start
-            Invariant(0 <= i and i <= len(opt_keys))
-            Invariant(len(opt_keys) == len(opt_is_flag)
-                      and len(opt_is_flag) == len(opt_vals))
-            Invariant(options == option_tokens(opt_keys.drop(i),
-                                                opt_is_flag.drop(i),
-                                                opt_vals.drop(i)))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
-            Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
-            Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
-            Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
-            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
-                               opt_vals[i - 1])
-            options = PSeq(tok) + options
-            i = i - 1
+    options = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
     leading = prefix + options
     if package_reported and len(launch_package) > 0:
         return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -134,7 +133,6 @@
              and len(opt_is_flag) == len(opt_vals))
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The forwarded implementation-option tokens: on the reference interpreter,
@@ -163,28 +161,9 @@
                     Result() == windows_recovery()))
     # post-conditions-end
     # impl-start
-    empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
-    options = empty
-    if is_reference_impl:
-        i = len(opt_keys)
-        while i > 0:
-            # invariants-start
-            Invariant(0 <= i and i <= len(opt_keys))
-            Invariant(len(opt_keys) == len(opt_is_flag)
-                      and len(opt_is_flag) == len(opt_vals))
-            Invariant(options == option_tokens(opt_keys.drop(i),
-                                                opt_is_flag.drop(i),
-                                                opt_vals.drop(i)))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
-            Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
-            Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
-            Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
-            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
-                               opt_vals[i - 1])
-            options = PSeq(tok) + options
-            i = i - 1
+    options = (option_tokens(opt_keys, opt_is_flag, opt_vals)
+               if is_reference_impl
+               else PSeq(PSeq(0)).take(0))  # type: PSeq[PSeq[int]]
     leading = prefix + options
     if package_reported and len(launch_package) > 0:
         return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -134,7 +133,6 @@
              and len(opt_is_flag) == len(opt_vals))
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The forwarded implementation-option tokens: on the reference interpreter,
@@ -167,20 +165,10 @@
     options = empty
     if is_reference_impl:
         i = len(opt_keys)
-        while i > 0:
-            # invariants-start
-            Invariant(0 <= i and i <= len(opt_keys))
+        while i > 1:
+            Invariant(1 <= i and i <= len(opt_keys) + 1)
             Invariant(len(opt_keys) == len(opt_is_flag)
                       and len(opt_is_flag) == len(opt_vals))
-            Invariant(options == option_tokens(opt_keys.drop(i),
-                                                opt_is_flag.drop(i),
-                                                opt_vals.drop(i)))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
-            Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
-            Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
-            Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
             tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
                                opt_vals[i - 1])
             options = PSeq(tok) + options
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -134,7 +133,6 @@
              and len(opt_is_flag) == len(opt_vals))
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The forwarded implementation-option tokens: on the reference interpreter,
@@ -168,16 +166,12 @@
     if is_reference_impl:
         i = len(opt_keys)
         while i > 0:
-            # invariants-start
             Invariant(0 <= i and i <= len(opt_keys))
             Invariant(len(opt_keys) == len(opt_is_flag)
                       and len(opt_is_flag) == len(opt_vals))
             Invariant(options == option_tokens(opt_keys.drop(i),
                                                 opt_is_flag.drop(i),
                                                 opt_vals.drop(i)))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
             Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
             Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
             Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
@@ -188,8 +182,6 @@
     leading = prefix + options
     if package_reported and len(launch_package) > 0:
         return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
-    elif not script_exists:
-        return windows_recovery()
     else:
         return leading + argv
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -134,7 +133,6 @@
              and len(opt_is_flag) == len(opt_vals))
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The forwarded implementation-option tokens: on the reference interpreter,
@@ -168,21 +166,10 @@
     if is_reference_impl:
         i = len(opt_keys)
         while i > 0:
-            # invariants-start
             Invariant(0 <= i and i <= len(opt_keys))
             Invariant(len(opt_keys) == len(opt_is_flag)
                       and len(opt_is_flag) == len(opt_vals))
-            Invariant(options == option_tokens(opt_keys.drop(i),
-                                                opt_is_flag.drop(i),
-                                                opt_vals.drop(i)))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
-            Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
-            Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
-            Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
-            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
-                               opt_vals[i - 1])
+            tok = dash_x() + opt_keys[i - 1]
             options = PSeq(tok) + options
             i = i - 1
     leading = prefix + options
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -134,7 +133,6 @@
              and len(opt_is_flag) == len(opt_vals))
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The forwarded implementation-option tokens: on the reference interpreter,
@@ -165,26 +163,21 @@
     # impl-start
     empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
     options = empty
-    if is_reference_impl:
-        i = len(opt_keys)
-        while i > 0:
-            # invariants-start
-            Invariant(0 <= i and i <= len(opt_keys))
-            Invariant(len(opt_keys) == len(opt_is_flag)
-                      and len(opt_is_flag) == len(opt_vals))
-            Invariant(options == option_tokens(opt_keys.drop(i),
-                                                opt_is_flag.drop(i),
-                                                opt_vals.drop(i)))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
-            Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
-            Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
-            Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
-            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
-                               opt_vals[i - 1])
-            options = PSeq(tok) + options
-            i = i - 1
+    i = len(opt_keys)
+    while i > 0:
+        Invariant(0 <= i and i <= len(opt_keys))
+        Invariant(len(opt_keys) == len(opt_is_flag)
+                  and len(opt_is_flag) == len(opt_vals))
+        Invariant(options == option_tokens(opt_keys.drop(i),
+                                            opt_is_flag.drop(i),
+                                            opt_vals.drop(i)))
+        Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
+        Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
+        Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
+        tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
+                           opt_vals[i - 1])
+        options = PSeq(tok) + options
+        i = i - 1
     leading = prefix + options
     if package_reported and len(launch_package) > 0:
         return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -134,7 +133,6 @@
              and len(opt_is_flag) == len(opt_vals))
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The forwarded implementation-option tokens: on the reference interpreter,
@@ -166,25 +164,14 @@
     empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
     options = empty
     if is_reference_impl:
-        i = len(opt_keys)
-        while i > 0:
-            # invariants-start
+        i = 0
+        while i < len(opt_keys):
             Invariant(0 <= i and i <= len(opt_keys))
             Invariant(len(opt_keys) == len(opt_is_flag)
                       and len(opt_is_flag) == len(opt_vals))
-            Invariant(options == option_tokens(opt_keys.drop(i),
-                                                opt_is_flag.drop(i),
-                                                opt_vals.drop(i)))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
-            Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
-            Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
-            Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
-            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
-                               opt_vals[i - 1])
+            tok = option_token(opt_keys[i], opt_is_flag[i], opt_vals[i])
             options = PSeq(tok) + options
-            i = i - 1
+            i = i + 1
     leading = prefix + options
     if package_reported and len(launch_package) > 0:
         return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -134,7 +133,6 @@
              and len(opt_is_flag) == len(opt_vals))
     # The argument vector always carries at least the entry script element.
     Requires(len(argv) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The forwarded implementation-option tokens: on the reference interpreter,
@@ -168,16 +166,12 @@
     if is_reference_impl:
         i = len(opt_keys)
         while i > 0:
-            # invariants-start
             Invariant(0 <= i and i <= len(opt_keys))
             Invariant(len(opt_keys) == len(opt_is_flag)
                       and len(opt_is_flag) == len(opt_vals))
             Invariant(options == option_tokens(opt_keys.drop(i),
                                                 opt_is_flag.drop(i),
                                                 opt_vals.drop(i)))
-            Invariant(MustTerminate(i + 1))
-            # invariants-end
-            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
             Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
             Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
             Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
@@ -185,11 +179,10 @@
                                opt_vals[i - 1])
             options = PSeq(tok) + options
             i = i - 1
-    leading = prefix + options
     if package_reported and len(launch_package) > 0:
-        return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
+        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1) + options
     elif not script_exists:
         return windows_recovery()
     else:
-        return leading + argv
+        return prefix + argv + options
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14771.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A development server, when it relaunches itself in a child process, must
  reconstruct the command line that started it so the child runs under the
  same interpreter configuration as the parent. Two kinds of interpreter-level
  options carried on the original command line have to be forwarded.

  After the interpreter path and the warning options, when the running
  interpreter is the reference C implementation, the reconstruction must also
  forward every interpreter implementation option that was supplied, in the
  order supplied. Each such option is a (name, value) pair and is forwarded as
  a single token built from the option flag and the name; when the value is the
  boolean-present sentinel (the option was given with no value) the token is
  just flag+name, and otherwise the token is flag+name+'='+value. When the
  running interpreter is NOT the reference C implementation, no such options are
  forwarded (the empty list). These forwarded option tokens are inserted into
  the leading arguments before the rest of the command line is appended, so
  they precede the entry script / module name and the program arguments in
  every reconstruction shape.

  The remaining reconstruction is unchanged: a module launch ('-m PACKAGE')
  re-invokes that package as a module followed by the program arguments; a
  plain launch whose entry script exists appends the whole argument vector; a
  launch whose entry script is gone takes a platform-specific recovery path
  represented abstractly here.

Strings are modelled as ``PSeq[int]`` of Unicode code points and the argument
vector / option lists as ``PSeq[PSeq[int]]`` of their elements (Nagini bans
``str`` indexing). The implementation-option pairs are carried by three
index-aligned pure sequences: the option NAMES ``opt_keys``, a per-option
boolean ``opt_is_flag`` (true iff the value is the present-with-no-value
sentinel), and the option VALUES ``opt_vals`` (meaningful only where
``opt_is_flag`` is false). All inputs are immutable pure-sequence values
(read-only inputs -- pure values cannot be mutated, so directive-5 read-only
safety holds by construction). The forwarded-option token list is modelled
deeply by the front-recursive pure fold ``option_tokens`` (one token per
option, per the flag/value rule above); no callee is axiomatized -- the
forwarding that the change is about is spelled out, not hidden behind an axiom,
and is validated against its real runtime semantics out-of-band by
axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The option-forwarding rule -- "on the reference
# interpreter, each supplied (name, value) implementation option becomes a
# flag+name token, or flag+name+'='+value when a value is present" -- and the
# guard that no options are forwarded on a non-reference interpreter are
# modelled deeply by `option_tokens` / `is_reference_impl` below; they are
# validated against the real interpreter-option and implementation-identity
# runtime semantics out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end


# pure-start
@Pure
def dash_x() -> PSeq[int]:
    # The implementation-option flag '-X'.
    return PSeq(45, 88)


@Pure
def eq() -> PSeq[int]:
    # The name/value separator '='.
    return PSeq(61)


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
    """A module launch is detected exactly when a launch package is reported
    and its name is non-empty (deep model of the unchanged module-launch
    predicate)."""
    return package_reported and len(launch_package) > 0


@Pure
def option_token(key: PSeq[int], is_flag: bool, val: PSeq[int]) -> PSeq[int]:
    """The single token forwarded for one implementation option (name, value):
    flag+name when the value is the present-with-no-value sentinel, else
    flag+name+'='+value."""
    if is_flag:
        return dash_x() + key
    return dash_x() + key + eq() + val


@Pure
def option_tokens(keys: PSeq[PSeq[int]],
                  flags: PSeq[bool],
                  vals: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The forwarded implementation-option tokens, one per option, in order.
    Front-recursive so a single unfold is available to callers per step."""
    Requires(len(keys) == len(flags) and len(flags) == len(vals))
    if len(keys) == 0:
        return PSeq(PSeq(0)).take(0)
    return PSeq(option_token(keys[0], flags[0], vals[0])) \
        + option_tokens(keys.drop(1), flags.drop(1), vals.drop(1))
# pure-end


def child_arguments(prefix: PSeq[PSeq[int]],
                    is_reference_impl: bool,
                    opt_keys: PSeq[PSeq[int]],
                    opt_is_flag: PSeq[bool],
                    opt_vals: PSeq[PSeq[int]],
                    package_reported: bool,
                    launch_package: PSeq[int],
                    argv: PSeq[PSeq[int]],
                    script_exists: bool) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # The three index-aligned option sequences describe the same options.
    Requires(len(opt_keys) == len(opt_is_flag)
             and len(opt_is_flag) == len(opt_vals))
    # The argument vector always carries at least the entry script element.
    Requires(len(argv) >= 1)
    # pre-conditions-end
    # post-conditions-start
    # The forwarded implementation-option tokens: on the reference interpreter,
    # one token per supplied option per the flag/value rule, in order; on any
    # other interpreter, none. Inserted into the leading arguments, before the
    # rest of the command line, in every reconstruction shape.
    # (A) Module launch: leading args (+ forwarded options) then the module
    # flag, the launched package ITSELF, then the program arguments.
    Ensures(Implies(is_module_launch(package_reported, launch_package),
                    Result() == prefix
                    + (option_tokens(opt_keys, opt_is_flag, opt_vals)
                       if is_reference_impl else PSeq(PSeq(0)).take(0))
                    + PSeq(dash_m(), launch_package)
                    + argv.drop(1)))
    # (B) Not a module launch, entry script present: leading args (+ forwarded
    # options) then the whole argument vector unchanged (entry script included).
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and script_exists,
                    Result() == prefix
                    + (option_tokens(opt_keys, opt_is_flag, opt_vals)
                       if is_reference_impl else PSeq(PSeq(0)).take(0))
                    + argv))
    # (C) Not a module launch, entry script absent: the unchanged recovery path.
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and not script_exists,
                    Result() == windows_recovery()))
    # post-conditions-end
    # impl-start
    empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    options = empty
    if is_reference_impl:
        i = len(opt_keys)
        while i > 0:
            # invariants-start
            Invariant(0 <= i and i <= len(opt_keys))
            Invariant(len(opt_keys) == len(opt_is_flag)
                      and len(opt_is_flag) == len(opt_vals))
            Invariant(options == option_tokens(opt_keys.drop(i),
                                                opt_is_flag.drop(i),
                                                opt_vals.drop(i)))
            # invariants-end
            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
            Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
            Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
            Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
                               opt_vals[i - 1])
            options = PSeq(tok) + options
            i = i - 1
    leading = prefix + options
    if package_reported and len(launch_package) > 0:
        return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
    elif not script_exists:
        return windows_recovery()
    else:
        return leading + argv
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY (G-EQ refinement-fidelity, adversarial). Bundle: nagini django__django-14771. verifier env swebench-nagini-verifier;

SPEC SHAPE: child_arguments postconditions are a TOTAL, MUTUALLY-EXCLUSIVE partition of the precondition domain — (A) is_module_launch; (B) not is_module_launch AND script_exists; (C) not is_module_launch AND NOT script_exists — and each clause pins Result() by an equality to the fully-spelled gold value (prefix + (option_tokens(...) if is_reference_impl else empty) + tail). No gap/overlap, so verify => unique gold output.

ATTACKS (all confirmed SAME-spec via `adversary same-spec`; each edits ONLY the impl region; weakness runs launched concurrently in batches of <=3 background jobs):
- atk_1 PREPATCH BUG (options always empty, never forwards): `weakness` exit 2, verification FAILED => prepatch reproduced (matches G-DIFF).
- atk_2 ECHO / ungrounded-oracle echo (options = ternary using the pure fold option_tokens, single assignment): `weakness` exit 0 = CANDIDATE (shares spec AND verifies, 12.5s). Its faithful refined patch is behaviourally the gold hunk; MATERIALIZED to atk_2.patch and RUN through the official harness: run_resolve('django__django-14771', patch) => resolved=True, completed=True. RESOLVES => NOT a weakness (fixed panel-1/eq policy: a resolving echo is not spec-too-weak).
- atk_3 PARTIAL-DOMAIN off-by-one (loop while i>1, drops last option): FAILED verify (exit 2).
- atk_4 CONTROL-FLOW-EFFECT (drops the `elif not script_exists: windows_recovery()` branch): FAILED verify (exit 2) — clause (C) rejects it.
- atk_5 UNGROUNDED-ORACLE (always flag form dash_x()+key, ignores is_flag): FAILED verify (exit 2).
- atk_6 GUARD OMISSION (forwards options regardless of is_reference_impl): FAILED verify (exit 2) — non-reference clause rejects it.
- atk_7 BOUNDARY/order (front-to-back index with prepend => reversed token order): FAILED verify (exit 2).
- atk_8 PLACEMENT (options appended AFTER argv/module tail instead of into leading args): FAILED verify (exit 2).
(Initial atk_2 draft hit a Nagini translation type-error `options already defined` — a non-semantic weak attack; rewritten to a clean single-assignment ternary which then verified as the CANDIDATE above.)

POSITIVE CONTROL: gold-faithful impl region (pos_control.py) VERIFIES (nagini_verify.sh, 12.2s, exit 0).

### EXACT COMMANDS (root, PY=swebench-lean/bin/python):
  PY -m swebench_unified.adversary same-spec nagini django__django-14771 <atk>  (all SAME)
  PY -m swebench_unified.adversary weakness  nagini django__django-14771 <atk>  (atk_2 exit0; others exit2)
  bash scripts/nagini_verify.sh pos_control.py  (Verification successful)
  run_resolve('django__django-14771', atk_2.patch) => resolved=True completed=True

REFINEMENT.MD / A-LEG AUDIT: axioms-start region contains NO consumed @ContractOnly axiom (confirmed by grep); every leg A1..A8 is R / A-reference / I — NO kind-3 (unexpressible-changed-op). The one genuinely changed op (the -X forwarding under the cpython guard) is modeled DEEPLY by option_token/option_tokens over opt_keys/opt_is_flag/opt_vals gated on is_reference_impl (A4/A5), not hidden behind an axiom. A-reference correspondence to the real callees holds: axiom_check.py (G-AX) drives the REAL generator `f'-X{key}' if value is True else f'-X{key}={value}'` over real dicts gated on sys.implementation.name=='cpython' on 16 boundary + 20000 fuzz cases and asserts == option_tokens; it also nails the decisive `value is True` IDENTITY edge (truthy string 'True' => -Xx=True, int 1 => -Xx=1, False => -Xx=False; only the bool True sentinel yields flag form) and the cpython guard. Re-ran axiom_check.py here: exit 0. mapping.md bindings (prefix, is_reference_impl, opt_*, launch_package, argv, script_exists, dash_x/eq/dash_m) match autoreload.py get_child_arguments post-patch. G-CONF (conformance_check.py, 107560 states, 0 disagreements) corroborates the shadow==real correspondence.

VERDICT: SOUND. 8 distinct same-spec attacks run to completion; 7 wrong impls rejected by the spec; the single verifying candidate (gold echo) has a faithful patch that RESOLVES under the official harness, so verify does not admit an incorrect (non-resolving) implementation here. No BROKEN evidence; no INCONCLUSIVE gaps (all needed verify + resolve runs completed).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-14771.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A development server, when it relaunches itself in a child process, must
  reconstruct the command line that started it so the child runs under the
  same interpreter configuration as the parent. Two kinds of interpreter-level
  options carried on the original command line have to be forwarded.

  After the interpreter path and the warning options, when the running
  interpreter is the reference C implementation, the reconstruction must also
  forward every interpreter implementation option that was supplied, in the
  order supplied. Each such option is a (name, value) pair and is forwarded as
  a single token built from the option flag and the name; when the value is the
  boolean-present sentinel (the option was given with no value) the token is
  just flag+name, and otherwise the token is flag+name+'='+value. When the
  running interpreter is NOT the reference C implementation, no such options are
  forwarded (the empty list). These forwarded option tokens are inserted into
  the leading arguments before the rest of the command line is appended, so
  they precede the entry script / module name and the program arguments in
  every reconstruction shape.

  The remaining reconstruction is unchanged: a module launch ('-m PACKAGE')
  re-invokes that package as a module followed by the program arguments; a
  plain launch whose entry script exists appends the whole argument vector; a
  launch whose entry script is gone takes a platform-specific recovery path
  represented abstractly here.

Strings are modelled as ``PSeq[int]`` of Unicode code points and the argument
vector / option lists as ``PSeq[PSeq[int]]`` of their elements (Nagini bans
``str`` indexing). The implementation-option pairs are carried by three
index-aligned pure sequences: the option NAMES ``opt_keys``, a per-option
boolean ``opt_is_flag`` (true iff the value is the present-with-no-value
sentinel), and the option VALUES ``opt_vals`` (meaningful only where
``opt_is_flag`` is false). All inputs are immutable pure-sequence values
(read-only inputs -- pure values cannot be mutated, so directive-5 read-only
safety holds by construction). The forwarded-option token list is modelled
deeply by the front-recursive pure fold ``option_tokens`` (one token per
option, per the flag/value rule above); no callee is axiomatized -- the
forwarding that the change is about is spelled out, not hidden behind an axiom,
and is validated against its real runtime semantics out-of-band by
axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms. The option-forwarding rule -- "on the reference
# interpreter, each supplied (name, value) implementation option becomes a
# flag+name token, or flag+name+'='+value when a value is present" -- and the
# guard that no options are forwarded on a non-reference interpreter are
# modelled deeply by `option_tokens` / `is_reference_impl` below; they are
# validated against the real interpreter-option and implementation-identity
# runtime semantics out-of-band by axiom_check.py (G-AX) as an A-reference, not
# consumed here.
# axioms-end


# pure-start
@Pure
def dash_x() -> PSeq[int]:
    # The implementation-option flag '-X'.
    return PSeq(45, 88)


@Pure
def eq() -> PSeq[int]:
    # The name/value separator '='.
    return PSeq(61)


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
    """A module launch is detected exactly when a launch package is reported
    and its name is non-empty (deep model of the unchanged module-launch
    predicate)."""
    return package_reported and len(launch_package) > 0


@Pure
def option_token(key: PSeq[int], is_flag: bool, val: PSeq[int]) -> PSeq[int]:
    """The single token forwarded for one implementation option (name, value):
    flag+name when the value is the present-with-no-value sentinel, else
    flag+name+'='+value."""
    if is_flag:
        return dash_x() + key
    return dash_x() + key + eq() + val


@Pure
def option_tokens(keys: PSeq[PSeq[int]],
                  flags: PSeq[bool],
                  vals: PSeq[PSeq[int]]) -> PSeq[PSeq[int]]:
    """The forwarded implementation-option tokens, one per option, in order.
    Front-recursive so a single unfold is available to callers per step."""
    Requires(len(keys) == len(flags) and len(flags) == len(vals))
    if len(keys) == 0:
        return PSeq(PSeq(0)).take(0)
    return PSeq(option_token(keys[0], flags[0], vals[0])) \
        + option_tokens(keys.drop(1), flags.drop(1), vals.drop(1))
# pure-end


def child_arguments(prefix: PSeq[PSeq[int]],
                    is_reference_impl: bool,
                    opt_keys: PSeq[PSeq[int]],
                    opt_is_flag: PSeq[bool],
                    opt_vals: PSeq[PSeq[int]],
                    package_reported: bool,
                    launch_package: PSeq[int],
                    argv: PSeq[PSeq[int]],
                    script_exists: bool) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # The three index-aligned option sequences describe the same options.
    Requires(len(opt_keys) == len(opt_is_flag)
             and len(opt_is_flag) == len(opt_vals))
    # The argument vector always carries at least the entry script element.
    Requires(len(argv) >= 1)
    # pre-conditions-end
    # post-conditions-start
    # The forwarded implementation-option tokens: on the reference interpreter,
    # one token per supplied option per the flag/value rule, in order; on any
    # other interpreter, none. Inserted into the leading arguments, before the
    # rest of the command line, in every reconstruction shape.
    # (A) Module launch: leading args (+ forwarded options) then the module
    # flag, the launched package ITSELF, then the program arguments.
    Ensures(Implies(is_module_launch(package_reported, launch_package),
                    Result() == prefix
                    + (option_tokens(opt_keys, opt_is_flag, opt_vals)
                       if is_reference_impl else PSeq(PSeq(0)).take(0))
                    + PSeq(dash_m(), launch_package)
                    + argv.drop(1)))
    # (B) Not a module launch, entry script present: leading args (+ forwarded
    # options) then the whole argument vector unchanged (entry script included).
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and script_exists,
                    Result() == prefix
                    + (option_tokens(opt_keys, opt_is_flag, opt_vals)
                       if is_reference_impl else PSeq(PSeq(0)).take(0))
                    + argv))
    # (C) Not a module launch, entry script absent: the unchanged recovery path.
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and not script_exists,
                    Result() == windows_recovery()))
    # post-conditions-end
    # impl-start
    empty = PSeq(PSeq(0)).take(0)  # type: PSeq[PSeq[int]]
    options = empty
    if is_reference_impl:
        i = len(opt_keys)
        while i > 0:
            # invariants-start
            Invariant(0 <= i and i <= len(opt_keys))
            Invariant(len(opt_keys) == len(opt_is_flag)
                      and len(opt_is_flag) == len(opt_vals))
            Invariant(options == option_tokens(opt_keys.drop(i),
                                                opt_is_flag.drop(i),
                                                opt_vals.drop(i)))
            # invariants-end
            Assert(opt_keys.drop(i - 1)[0] == opt_keys[i - 1])
            Assert(opt_keys.drop(i - 1).drop(1) == opt_keys.drop(i))
            Assert(opt_is_flag.drop(i - 1).drop(1) == opt_is_flag.drop(i))
            Assert(opt_vals.drop(i - 1).drop(1) == opt_vals.drop(i))
            tok = option_token(opt_keys[i - 1], opt_is_flag[i - 1],
                               opt_vals[i - 1])
            options = PSeq(tok) + options
            i = i - 1
    leading = prefix + options
    if package_reported and len(launch_package) > 0:
        return leading + PSeq(dash_m(), launch_package) + argv.drop(1)
    elif not script_exists:
        return windows_recovery()
    else:
        return leading + argv
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT SUMMARY (G-EQ refinement-fidelity, adversarial). Bundle: nagini django__django-14771. verifier env swebench-nagini-verifier;

SPEC SHAPE: child_arguments postconditions are a TOTAL, MUTUALLY-EXCLUSIVE partition of the precondition domain — (A) is_module_launch; (B) not is_module_launch AND script_exists; (C) not is_module_launch AND NOT script_exists — and each clause pins Result() by an equality to the fully-spelled gold value (prefix + (option_tokens(...) if is_reference_impl else empty) + tail). No gap/overlap, so verify => unique gold output.

ATTACKS (all confirmed SAME-spec via `adversary same-spec`; each edits ONLY the impl region; weakness runs launched concurrently in batches of <=3 background jobs):
- atk_1 PREPATCH BUG (options always empty, never forwards): `weakness` exit 2, verification FAILED => prepatch reproduced (matches G-DIFF).
- atk_2 ECHO / ungrounded-oracle echo (options = ternary using the pure fold option_tokens, single assignment): `weakness` exit 0 = CANDIDATE (shares spec AND verifies, 12.5s). Its faithful refined patch is behaviourally the gold hunk; MATERIALIZED to atk_2.patch and RUN through the official harness: run_resolve('django__django-14771', patch) => resolved=True, completed=True. RESOLVES => NOT a weakness (fixed panel-1/eq policy: a resolving echo is not spec-too-weak).
- atk_3 PARTIAL-DOMAIN off-by-one (loop while i>1, drops last option): FAILED verify (exit 2).
- atk_4 CONTROL-FLOW-EFFECT (drops the `elif not script_exists: windows_recovery()` branch): FAILED verify (exit 2) — clause (C) rejects it.
- atk_5 UNGROUNDED-ORACLE (always flag form dash_x()+key, ignores is_flag): FAILED verify (exit 2).
- atk_6 GUARD OMISSION (forwards options regardless of is_reference_impl): FAILED verify (exit 2) — non-reference clause rejects it.
- atk_7 BOUNDARY/order (front-to-back index with prepend => reversed token order): FAILED verify (exit 2).
- atk_8 PLACEMENT (options appended AFTER argv/module tail instead of into leading args): FAILED verify (exit 2).
(Initial atk_2 draft hit a Nagini translation type-error `options already defined` — a non-semantic weak attack; rewritten to a clean single-assignment ternary which then verified as the CANDIDATE above.)

POSITIVE CONTROL: gold-faithful impl region (pos_control.py) VERIFIES (nagini_verify.sh, 12.2s, exit 0).

### EXACT COMMANDS (root, PY=swebench-lean/bin/python):
  PY -m swebench_unified.adversary same-spec nagini django__django-14771 <atk>  (all SAME)
  PY -m swebench_unified.adversary weakness  nagini django__django-14771 <atk>  (atk_2 exit0; others exit2)
  bash scripts/nagini_verify.sh pos_control.py  (Verification successful)
  run_resolve('django__django-14771', atk_2.patch) => resolved=True completed=True

REFINEMENT.MD / A-LEG AUDIT: axioms-start region contains NO consumed @ContractOnly axiom (confirmed by grep); every leg A1..A8 is R / A-reference / I — NO kind-3 (unexpressible-changed-op). The one genuinely changed op (the -X forwarding under the cpython guard) is modeled DEEPLY by option_token/option_tokens over opt_keys/opt_is_flag/opt_vals gated on is_reference_impl (A4/A5), not hidden behind an axiom. A-reference correspondence to the real callees holds: axiom_check.py (G-AX) drives the REAL generator `f'-X{key}' if value is True else f'-X{key}={value}'` over real dicts gated on sys.implementation.name=='cpython' on 16 boundary + 20000 fuzz cases and asserts == option_tokens; it also nails the decisive `value is True` IDENTITY edge (truthy string 'True' => -Xx=True, int 1 => -Xx=1, False => -Xx=False; only the bool True sentinel yields flag form) and the cpython guard. Re-ran axiom_check.py here: exit 0. mapping.md bindings (prefix, is_reference_impl, opt_*, launch_package, argv, script_exists, dash_x/eq/dash_m) match autoreload.py get_child_arguments post-patch. G-CONF (conformance_check.py, 107560 states, 0 disagreements) corroborates the shadow==real correspondence.

VERDICT: SOUND. 8 distinct same-spec attacks run to completion; 7 wrong impls rejected by the spec; the single verifying candidate (gold echo) has a faithful patch that RESOLVES under the official harness, so verify does not admit an incorrect (non-resolving) implementation here. No BROKEN evidence; no INCONCLUSIVE gaps (all needed verify + resolve runs completed).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** No drift found. (1) Spec region byte-identical to bundle (same-spec: SAME). (2) model.py verifies (Nagini success, 11.7s). (3) G-AX axiom_check.py passes on 16 boundary + 20000 fuzz xoption dicts, confirming option_tokens deep model == real `f'-X{key}' if value is True else f'-X{key}={value}'` generator, the `value is True` IDENTITY selector (truthy string 'True' -> -Xx=True, not flag form; int 1 -> -Xx=1; False -> -Xx=False), and the cpython guard (non-reference interpreter forwards []). (4) Branch shapes match get_child_arguments() at base_commit 4884a87e: module-launch (args+=['-m',name]+sys.argv[1:]), script-present fall-through (args+=sys.argv, the test_xoptions branch), script-absent Windows recovery (unchanged, abstracted). Forwarded -X tokens inserted into leading args before branch dispatch in both. One modeling boundary examined: is_module_launch requires len(launch_package)>0 vs real `__spec__ is not None`; diverges only if __spec__ present with empty selected name, which spec.name/spec.parent never produce for a real module launch -> no reachable diverging input, and this is unchanged-behavior abstraction, not the changed -X forwarding. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring, axioms note, pure region, child_arguments signature, pre/post-conditions) describes only behavior already fully disclosed by the public problem_statement, which explicitly states 'Auto-reloader should pass -X options (for cpython implementation)', demonstrates `python -X utf8 manage.py runserver`, and links sys._xoptions docs. Thus the forwarding rule (flag+name vs flag+name+'='+value tokens, gated on the reference/CPython interpreter, inserted into leading args) is public, not leaked. Checks: patched path django/utils/autoreload.py absent from spec view; gold symbol get_child_arguments not embedded in any spec-view identifier or comment (model uses `child_arguments`); no gold-patch lines reproduced; no diff markers; no bug/fix narration terms. Mechanical leakage.screen (nagini backend) returns PASSED=True with zero hard failures, corroborating the semantic judgment. Not a relaxed bundle (no RELAXED_LEAKAGE.md / relaxed_leakage flag).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
