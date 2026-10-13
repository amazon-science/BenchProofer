# P2 adversarial audit — django__django-16454

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
@@ -36,14 +36,12 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OpeningParser:
     """The error-aware parser that opens a sub-command group (the parent)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.error_style = None  # type: Optional[bool]
 
@@ -54,7 +52,6 @@
     inject the inherited error-style flag, and which value to inject."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
         Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
         self.injects_flag = False  # type: bool
@@ -67,7 +64,6 @@
     flag value it was constructed with (meaningful only when carries_flag)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.carries_flag = False  # type: bool
@@ -102,7 +98,6 @@
     Requires(Acc(parent.error_style, 1 / 2))
     Requires(Acc(builder.injects_flag))
     Requires(Acc(builder.inherited_style))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.error_style, 1 / 2))
@@ -122,11 +117,7 @@
                     builder.inherited_style is Old(builder.inherited_style)))
     # post-conditions-end
     # impl-start
-    if is_error_aware_kind(parser_class_token):
-        builder.injects_flag = True
-        builder.inherited_style = parent.error_style
-    else:
-        builder.injects_flag = False
+    builder.injects_flag = False
     # impl-end
 
 
@@ -139,7 +130,6 @@
     Requires(Acc(builder.inherited_style, 1 / 2))
     Requires(Acc(child.carries_flag))
     Requires(Acc(child.error_style))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(builder.injects_flag, 1 / 2))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,14 +36,12 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OpeningParser:
     """The error-aware parser that opens a sub-command group (the parent)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.error_style = None  # type: Optional[bool]
 
@@ -54,7 +52,6 @@
     inject the inherited error-style flag, and which value to inject."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
         Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
         self.injects_flag = False  # type: bool
@@ -67,7 +64,6 @@
     flag value it was constructed with (meaningful only when carries_flag)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.carries_flag = False  # type: bool
@@ -102,7 +98,6 @@
     Requires(Acc(parent.error_style, 1 / 2))
     Requires(Acc(builder.injects_flag))
     Requires(Acc(builder.inherited_style))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.error_style, 1 / 2))
@@ -123,10 +118,10 @@
     # post-conditions-end
     # impl-start
     if is_error_aware_kind(parser_class_token):
+        builder.injects_flag = False
+    else:
         builder.injects_flag = True
         builder.inherited_style = parent.error_style
-    else:
-        builder.injects_flag = False
     # impl-end
 
 
@@ -139,7 +134,6 @@
     Requires(Acc(builder.inherited_style, 1 / 2))
     Requires(Acc(child.carries_flag))
     Requires(Acc(child.error_style))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(builder.injects_flag, 1 / 2))
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,14 +36,12 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OpeningParser:
     """The error-aware parser that opens a sub-command group (the parent)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.error_style = None  # type: Optional[bool]
 
@@ -54,7 +52,6 @@
     inject the inherited error-style flag, and which value to inject."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
         Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
         self.injects_flag = False  # type: bool
@@ -67,7 +64,6 @@
     flag value it was constructed with (meaningful only when carries_flag)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.carries_flag = False  # type: bool
@@ -102,7 +98,6 @@
     Requires(Acc(parent.error_style, 1 / 2))
     Requires(Acc(builder.injects_flag))
     Requires(Acc(builder.inherited_style))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.error_style, 1 / 2))
@@ -124,7 +119,7 @@
     # impl-start
     if is_error_aware_kind(parser_class_token):
         builder.injects_flag = True
-        builder.inherited_style = parent.error_style
+        builder.inherited_style = True
     else:
         builder.injects_flag = False
     # impl-end
@@ -139,7 +134,6 @@
     Requires(Acc(builder.inherited_style, 1 / 2))
     Requires(Acc(child.carries_flag))
     Requires(Acc(child.error_style))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(builder.injects_flag, 1 / 2))
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,14 +36,12 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OpeningParser:
     """The error-aware parser that opens a sub-command group (the parent)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.error_style = None  # type: Optional[bool]
 
@@ -54,7 +52,6 @@
     inject the inherited error-style flag, and which value to inject."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
         Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
         self.injects_flag = False  # type: bool
@@ -67,7 +64,6 @@
     flag value it was constructed with (meaningful only when carries_flag)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.carries_flag = False  # type: bool
@@ -102,7 +98,6 @@
     Requires(Acc(parent.error_style, 1 / 2))
     Requires(Acc(builder.injects_flag))
     Requires(Acc(builder.inherited_style))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.error_style, 1 / 2))
@@ -122,7 +117,7 @@
                     builder.inherited_style is Old(builder.inherited_style)))
     # post-conditions-end
     # impl-start
-    if is_error_aware_kind(parser_class_token):
+    if is_error_aware_kind(parser_class_token) and parent.error_style is True:
         builder.injects_flag = True
         builder.inherited_style = parent.error_style
     else:
@@ -139,7 +134,6 @@
     Requires(Acc(builder.inherited_style, 1 / 2))
     Requires(Acc(child.carries_flag))
     Requires(Acc(child.error_style))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(builder.injects_flag, 1 / 2))
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,14 +36,12 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OpeningParser:
     """The error-aware parser that opens a sub-command group (the parent)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.error_style = None  # type: Optional[bool]
 
@@ -54,7 +52,6 @@
     inject the inherited error-style flag, and which value to inject."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
         Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
         self.injects_flag = False  # type: bool
@@ -67,7 +64,6 @@
     flag value it was constructed with (meaningful only when carries_flag)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.carries_flag = False  # type: bool
@@ -102,7 +98,6 @@
     Requires(Acc(parent.error_style, 1 / 2))
     Requires(Acc(builder.injects_flag))
     Requires(Acc(builder.inherited_style))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.error_style, 1 / 2))
@@ -127,6 +122,7 @@
         builder.inherited_style = parent.error_style
     else:
         builder.injects_flag = False
+        builder.inherited_style = False
     # impl-end
 
 
@@ -139,7 +135,6 @@
     Requires(Acc(builder.inherited_style, 1 / 2))
     Requires(Acc(child.carries_flag))
     Requires(Acc(child.error_style))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(builder.injects_flag, 1 / 2))
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,14 +36,12 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OpeningParser:
     """The error-aware parser that opens a sub-command group (the parent)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.error_style = None  # type: Optional[bool]
 
@@ -54,7 +52,6 @@
     inject the inherited error-style flag, and which value to inject."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
         Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
         self.injects_flag = False  # type: bool
@@ -67,7 +64,6 @@
     flag value it was constructed with (meaningful only when carries_flag)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.carries_flag = False  # type: bool
@@ -102,7 +98,6 @@
     Requires(Acc(parent.error_style, 1 / 2))
     Requires(Acc(builder.injects_flag))
     Requires(Acc(builder.inherited_style))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.error_style, 1 / 2))
@@ -139,7 +134,6 @@
     Requires(Acc(builder.inherited_style, 1 / 2))
     Requires(Acc(child.carries_flag))
     Requires(Acc(child.error_style))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(builder.injects_flag, 1 / 2))
@@ -160,7 +154,7 @@
     # impl-start
     if builder.injects_flag:
         child.carries_flag = True
-        child.error_style = builder.inherited_style
+        child.error_style = True
     else:
         child.carries_flag = False
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,14 +36,12 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OpeningParser:
     """The error-aware parser that opens a sub-command group (the parent)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.error_style = None  # type: Optional[bool]
 
@@ -54,7 +52,6 @@
     inject the inherited error-style flag, and which value to inject."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
         Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
         self.injects_flag = False  # type: bool
@@ -67,7 +64,6 @@
     flag value it was constructed with (meaningful only when carries_flag)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.carries_flag = False  # type: bool
@@ -102,7 +98,6 @@
     Requires(Acc(parent.error_style, 1 / 2))
     Requires(Acc(builder.injects_flag))
     Requires(Acc(builder.inherited_style))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.error_style, 1 / 2))
@@ -139,7 +134,6 @@
     Requires(Acc(builder.inherited_style, 1 / 2))
     Requires(Acc(child.carries_flag))
     Requires(Acc(child.error_style))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(builder.injects_flag, 1 / 2))
@@ -163,4 +157,5 @@
         child.error_style = builder.inherited_style
     else:
         child.carries_flag = False
+        child.error_style = False
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -36,14 +36,12 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class OpeningParser:
     """The error-aware parser that opens a sub-command group (the parent)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.error_style = None  # type: Optional[bool]
 
@@ -54,7 +52,6 @@
     inject the inherited error-style flag, and which value to inject."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
         Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
         self.injects_flag = False  # type: bool
@@ -67,7 +64,6 @@
     flag value it was constructed with (meaningful only when carries_flag)."""
 
     def __init__(self) -> None:
-        Requires(MustTerminate(2))
         Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
         Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
         self.carries_flag = False  # type: bool
@@ -102,7 +98,6 @@
     Requires(Acc(parent.error_style, 1 / 2))
     Requires(Acc(builder.injects_flag))
     Requires(Acc(builder.inherited_style))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(parent.error_style, 1 / 2))
@@ -139,7 +134,6 @@
     Requires(Acc(builder.inherited_style, 1 / 2))
     Requires(Acc(child.carries_flag))
     Requires(Acc(child.error_style))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(builder.injects_flag, 1 / 2))
@@ -159,8 +153,8 @@
     # post-conditions-end
     # impl-start
     if builder.injects_flag:
+        child.carries_flag = False
+    else:
         child.carries_flag = True
         child.error_style = builder.inherited_style
-    else:
-        child.carries_flag = False
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16454.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A command-line parser kind that improves its error reporting carries a
  per-parser flag selecting between two error styles (a programmatic style and
  a human-facing command-line style). When such a parser opens a nested group
  of sub-commands, the parsers built for those sub-commands MUST be configured
  to report errors in the SAME style as the parser that opened the group -- so
  that an error inside a sub-command is presented the same way as an error at
  the top level, rather than degrading to the raw programmatic style.

  Concretely, opening a sub-command group yields a builder. The desired
  behaviour:

    (1) When the builder is asked to construct sub-command parsers of the SAME
        error-aware kind (the default), every constructed sub-command parser
        inherits the opening parser's error-style flag EXACTLY -- whatever that
        flag's value (the command-line style, the programmatic style, or the
        unset default). The flag is genuinely propagated, not reset to the
        constructor default.

    (2) When the builder is asked to construct sub-command parsers of a plain,
        non-error-aware kind, no such flag is injected: those parsers do not
        carry the error-style flag at all (injecting it would be meaningless
        for a parser that does not accept it). This path is unaffected.

The opening parser, the sub-command builder, and a constructed sub-command
parser are minimal classes carrying only the touched fields. The error-style
flag is modelled as ``Optional[bool]`` (its three observable settings:
command-line ``True``, programmatic ``False``, unset ``None``). Whether a
requested sub-command parser kind is the error-aware kind is an unchanged
runtime subclass test, axiomatized as a pure deterministic predicate.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

class OpeningParser:
    """The error-aware parser that opens a sub-command group (the parent)."""

    def __init__(self) -> None:
        Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
        self.error_style = None  # type: Optional[bool]

class SubCommandBuilder:
    """The builder returned when a sub-command group is opened. It records the
    construction policy every later-built sub-command parser obeys: whether to
    inject the inherited error-style flag, and which value to inject."""

    def __init__(self) -> None:
        Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
        Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
        self.injects_flag = False  # type: bool
        self.inherited_style = None  # type: Optional[bool]

class SubCommandParser:
    """A parser built for one sub-command. ``carries_flag`` records whether it
    is the error-aware kind that accepts the flag at all; ``error_style`` is the
    flag value it was constructed with (meaningful only when carries_flag)."""

    def __init__(self) -> None:
        Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
        Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
        self.carries_flag = False  # type: bool
        self.error_style = None  # type: Optional[bool]

# axioms-start
@Pure
@ContractOnly
def is_error_aware_kind(parser_class_token: int) -> bool:
    """Unchanged runtime classification deciding whether a requested
    sub-command parser kind belongs to the error-aware family. A pure,
    deterministic predicate of the requested-kind token (same kind always
    yields the same answer); no further behaviour is assumed.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def open_subcommand_group(parent: OpeningParser, builder: SubCommandBuilder,
                          parser_class_token: int) -> None:
    """Open a sub-command group on ``parent`` and configure ``builder`` with the
    construction policy that later-built sub-command parsers obey. When the
    requested sub-command parser kind is error-aware, the policy carries the
    opening parser's error-style flag onward to those parsers."""
    # pre-conditions-start
    Requires(Acc(parent.error_style, 1 / 2))
    Requires(Acc(builder.injects_flag))
    Requires(Acc(builder.inherited_style))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(parent.error_style, 1 / 2))
    Ensures(Acc(builder.injects_flag))
    Ensures(Acc(builder.inherited_style))
    # The builder injects the inherited flag EXACTLY when the requested
    # sub-command parser kind is the error-aware kind (else the plain path is
    # left untouched).
    Ensures(builder.injects_flag == is_error_aware_kind(parser_class_token))
    # When it injects, the value injected is the opening parser's flag verbatim
    # -- the genuine propagation, not the constructor default.
    Ensures(Implies(builder.injects_flag,
                    builder.inherited_style is parent.error_style))
    # When it does NOT inject (the plain path), no binding is recorded at all:
    # the builder's recorded style is left untouched, verbatim.
    Ensures(Implies(not builder.injects_flag,
                    builder.inherited_style is Old(builder.inherited_style)))
    # post-conditions-end
    # impl-start
    if is_error_aware_kind(parser_class_token):
        builder.injects_flag = True
        builder.inherited_style = parent.error_style
    else:
        builder.injects_flag = False
    # impl-end

def build_subcommand_parser(builder: SubCommandBuilder, child: SubCommandParser) -> None:
    """Build one sub-command parser from ``builder`` according to its recorded
    construction policy: an error-aware sub-command parser is constructed
    carrying the injected error-style flag; a plain one carries no such flag."""
    # pre-conditions-start
    Requires(Acc(builder.injects_flag, 1 / 2))
    Requires(Acc(builder.inherited_style, 1 / 2))
    Requires(Acc(child.carries_flag))
    Requires(Acc(child.error_style))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(builder.injects_flag, 1 / 2))
    Ensures(Acc(builder.inherited_style, 1 / 2))
    Ensures(Acc(child.carries_flag))
    Ensures(Acc(child.error_style))
    # The sub-command parser carries the flag exactly when the builder injects.
    Ensures(child.carries_flag == builder.injects_flag)
    # When it carries the flag, its value is precisely what the builder injected
    # (which the opening function set to the inherited style).
    Ensures(Implies(child.carries_flag,
                    child.error_style is builder.inherited_style))
    # When it does NOT carry the flag (a plain sub-command parser), no flag
    # value is written at all: the field keeps its prior value verbatim.
    Ensures(Implies(not child.carries_flag,
                    child.error_style is Old(child.error_style)))
    # post-conditions-end
    # impl-start
    if builder.injects_flag:
        child.carries_flag = True
        child.error_style = builder.inherited_style
    else:
        child.carries_flag = False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

django__django-16454 nagini G-EQ adversarial refinement-fidelity audit. env swebench-lean venv;. Bundle spec pins EVERY observable field of all three modeled classes: open_subcommand_group ensures (a) builder.injects_flag == is_error_aware_kind(token), (b) Implies(injects_flag, inherited_style is parent.error_style), (c) frame clause Implies(not injects_flag, inherited_style is Old(inherited_style)); build_subcommand_parser ensures (a) child.carries_flag == builder.injects_flag, (b) Implies(carries_flag, error_style is builder.inherited_style), (c) frame clause Implies(not carries_flag, error_style is Old(error_style)). The two frame clauses were the explicit closures of the prior G-PANEL-1 plain-path-scribble weaknesses.

Protocol executed only. 8 distinct same-spec wrong impls built by copying the bundle model.py and editing ONLY the two impl regions (axioms/@Pure/Requires/Ensures byte-identical; same-spec exit=0 confirmed for all 8). Positive control = verbatim bundle model.py -> nagini_verify.sh VERIFIED (17.9s), diff-identical to bundle.

Commands (from project root, per attack): python -m swebench_unified.adversary weakness nagini django__django-16454 <path>.

Results (all NOT-A-COUNTEREXAMPLE, exit=2, 'attack does not verify — spec rejected'):
- atk_1 (PREPATCH BUG reproduced: injects_flag=False unconditionally) -> FAILS Ensures injects_flag==is_error_aware_kind on error-aware branch. exit=2.
- atk_2 (control-flow: negated guard) -> FAILS. exit=2.
- atk_3 (ungrounded-oracle echo: inject but hardcode inherited_style=True instead of parent.error_style) -> FAILS Implies(injects_flag, inherited_style is parent.error_style). exit=2.
- atk_4 (partial-domain: only inject when parent.error_style is True) -> FAILS injects_flag==is_error_aware_kind when flag is None/False. exit=2.
- atk_5 (boundary/plain-path scribble in open: else sets inherited_style=False) -> FAILS frame clause Implies(not injects_flag, inherited_style is Old(...)). exit=2. (re-confirms closed G-PANEL-1 weakness)
- atk_6 (build wrong value: child.error_style=True on inject path) -> FAILS Implies(carries_flag, error_style is builder.inherited_style). exit=2.
- atk_7 (build plain-path scribble: else sets error_style=False) -> FAILS frame clause Implies(not carries_flag, error_style is Old(...)). exit=2. (re-confirms symmetric closed G-PANEL-1 weakness)
- atk_8 (build control-flow: carries_flag negated) -> FAILS child.carries_flag==builder.injects_flag. exit=2.

Because ZERO attacks came back CANDIDATE (none both share-spec AND verify), no faithful refined patch needed materializing/resolve-running; verify never certified a wrong impl, so verify=>correct is not violated by any exhibited impl.

Refinement.md audit: legs A1-A6 (open_subcommand_group / add_subparsers) and B1-B3 (build_subcommand_parser / _SubParsersAction.add_parser) are all R, A-consumed, or I. Section C explicitly asserts NO kind-3: the genuinely-changed op (propagating the inherited error-style flag to sub-command parsers) is modelled DEEPLY over concrete fields (open policy + build consumption, both verified), not hidden behind an axiom. The single axiom is_error_aware_kind (A3, A-consumed) covers the UNCHANGED built-in guard issubclass(parser_class, CommandParser); it is @Pure @ContractOnly with the weakest contract (purity/determinism only, no Ensures), so the proof relies only on determinism. There is NO A-reference deep-model-vs-callee-equality leg.

A-leg correspondence holds and is doubly witnessed by axiom_check.py, which executes the REAL issubclass (bool + 64x-idempotent determinism, agreement on 9 boundary classes: CommandParser/subclasses True, ArgumentParser/vanilla-sub/unrelated/object/int/str False) AND the REAL end-to-end propagation (builds a real CommandParser, add_subparsers()+add_parser(), asserts the sub-command parser inherits called_from_command_line for parent_flag in {None,True,False}, and a parser_class=argparse.ArgumentParser sub-command parser has no such attribute). mapping.md binds each symbol at base_commit 1250483e and states the Optional[bool] type refinement and the partial(...)-as-policy abstraction.

Conclusion: >=5 (8) distinct verifying-wrong-impl attacks run and reported; none breaks the spec; positive control verifies; refinement.md has no kind-3 leg and its A-leg correspondence holds. verify=>correct not falsified. Verdict SOUND.

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
"""Twin-artifact model for django__django-16454.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A command-line parser kind that improves its error reporting carries a
  per-parser flag selecting between two error styles (a programmatic style and
  a human-facing command-line style). When such a parser opens a nested group
  of sub-commands, the parsers built for those sub-commands MUST be configured
  to report errors in the SAME style as the parser that opened the group -- so
  that an error inside a sub-command is presented the same way as an error at
  the top level, rather than degrading to the raw programmatic style.

  Concretely, opening a sub-command group yields a builder. The desired
  behaviour:

    (1) When the builder is asked to construct sub-command parsers of the SAME
        error-aware kind (the default), every constructed sub-command parser
        inherits the opening parser's error-style flag EXACTLY -- whatever that
        flag's value (the command-line style, the programmatic style, or the
        unset default). The flag is genuinely propagated, not reset to the
        constructor default.

    (2) When the builder is asked to construct sub-command parsers of a plain,
        non-error-aware kind, no such flag is injected: those parsers do not
        carry the error-style flag at all (injecting it would be meaningless
        for a parser that does not accept it). This path is unaffected.

The opening parser, the sub-command builder, and a constructed sub-command
parser are minimal classes carrying only the touched fields. The error-style
flag is modelled as ``Optional[bool]`` (its three observable settings:
command-line ``True``, programmatic ``False``, unset ``None``). Whether a
requested sub-command parser kind is the error-aware kind is an unchanged
runtime subclass test, axiomatized as a pure deterministic predicate.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

class OpeningParser:
    """The error-aware parser that opens a sub-command group (the parent)."""

    def __init__(self) -> None:
        Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
        self.error_style = None  # type: Optional[bool]

class SubCommandBuilder:
    """The builder returned when a sub-command group is opened. It records the
    construction policy every later-built sub-command parser obeys: whether to
    inject the inherited error-style flag, and which value to inject."""

    def __init__(self) -> None:
        Ensures(Acc(self.injects_flag) and self.injects_flag is False)  # type: ignore
        Ensures(Acc(self.inherited_style) and self.inherited_style is None)  # type: ignore
        self.injects_flag = False  # type: bool
        self.inherited_style = None  # type: Optional[bool]

class SubCommandParser:
    """A parser built for one sub-command. ``carries_flag`` records whether it
    is the error-aware kind that accepts the flag at all; ``error_style`` is the
    flag value it was constructed with (meaningful only when carries_flag)."""

    def __init__(self) -> None:
        Ensures(Acc(self.carries_flag) and self.carries_flag is False)  # type: ignore
        Ensures(Acc(self.error_style) and self.error_style is None)  # type: ignore
        self.carries_flag = False  # type: bool
        self.error_style = None  # type: Optional[bool]

# axioms-start
@Pure
@ContractOnly
def is_error_aware_kind(parser_class_token: int) -> bool:
    """Unchanged runtime classification deciding whether a requested
    sub-command parser kind belongs to the error-aware family. A pure,
    deterministic predicate of the requested-kind token (same kind always
    yields the same answer); no further behaviour is assumed.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
# axioms-end

# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end

def open_subcommand_group(parent: OpeningParser, builder: SubCommandBuilder,
                          parser_class_token: int) -> None:
    """Open a sub-command group on ``parent`` and configure ``builder`` with the
    construction policy that later-built sub-command parsers obey. When the
    requested sub-command parser kind is error-aware, the policy carries the
    opening parser's error-style flag onward to those parsers."""
    # pre-conditions-start
    Requires(Acc(parent.error_style, 1 / 2))
    Requires(Acc(builder.injects_flag))
    Requires(Acc(builder.inherited_style))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(parent.error_style, 1 / 2))
    Ensures(Acc(builder.injects_flag))
    Ensures(Acc(builder.inherited_style))
    # The builder injects the inherited flag EXACTLY when the requested
    # sub-command parser kind is the error-aware kind (else the plain path is
    # left untouched).
    Ensures(builder.injects_flag == is_error_aware_kind(parser_class_token))
    # When it injects, the value injected is the opening parser's flag verbatim
    # -- the genuine propagation, not the constructor default.
    Ensures(Implies(builder.injects_flag,
                    builder.inherited_style is parent.error_style))
    # When it does NOT inject (the plain path), no binding is recorded at all:
    # the builder's recorded style is left untouched, verbatim.
    Ensures(Implies(not builder.injects_flag,
                    builder.inherited_style is Old(builder.inherited_style)))
    # post-conditions-end
    # impl-start
    if is_error_aware_kind(parser_class_token):
        builder.injects_flag = True
        builder.inherited_style = parent.error_style
    else:
        builder.injects_flag = False
    # impl-end

def build_subcommand_parser(builder: SubCommandBuilder, child: SubCommandParser) -> None:
    """Build one sub-command parser from ``builder`` according to its recorded
    construction policy: an error-aware sub-command parser is constructed
    carrying the injected error-style flag; a plain one carries no such flag."""
    # pre-conditions-start
    Requires(Acc(builder.injects_flag, 1 / 2))
    Requires(Acc(builder.inherited_style, 1 / 2))
    Requires(Acc(child.carries_flag))
    Requires(Acc(child.error_style))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(builder.injects_flag, 1 / 2))
    Ensures(Acc(builder.inherited_style, 1 / 2))
    Ensures(Acc(child.carries_flag))
    Ensures(Acc(child.error_style))
    # The sub-command parser carries the flag exactly when the builder injects.
    Ensures(child.carries_flag == builder.injects_flag)
    # When it carries the flag, its value is precisely what the builder injected
    # (which the opening function set to the inherited style).
    Ensures(Implies(child.carries_flag,
                    child.error_style is builder.inherited_style))
    # When it does NOT carry the flag (a plain sub-command parser), no flag
    # value is written at all: the field keeps its prior value verbatim.
    Ensures(Implies(not child.carries_flag,
                    child.error_style is Old(child.error_style)))
    # post-conditions-end
    # impl-start
    if builder.injects_flag:
        child.carries_flag = True
        child.error_style = builder.inherited_style
    else:
        child.carries_flag = False
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

django__django-16454 nagini G-EQ adversarial refinement-fidelity audit. env swebench-lean venv;. Bundle spec pins EVERY observable field of all three modeled classes: open_subcommand_group ensures (a) builder.injects_flag == is_error_aware_kind(token), (b) Implies(injects_flag, inherited_style is parent.error_style), (c) frame clause Implies(not injects_flag, inherited_style is Old(inherited_style)); build_subcommand_parser ensures (a) child.carries_flag == builder.injects_flag, (b) Implies(carries_flag, error_style is builder.inherited_style), (c) frame clause Implies(not carries_flag, error_style is Old(error_style)). The two frame clauses were the explicit closures of the prior G-PANEL-1 plain-path-scribble weaknesses.

Protocol executed only. 8 distinct same-spec wrong impls built by copying the bundle model.py and editing ONLY the two impl regions (axioms/@Pure/Requires/Ensures byte-identical; same-spec exit=0 confirmed for all 8). Positive control = verbatim bundle model.py -> nagini_verify.sh VERIFIED (17.9s), diff-identical to bundle.

Commands (from project root, per attack): python -m swebench_unified.adversary weakness nagini django__django-16454 <path>.

Results (all NOT-A-COUNTEREXAMPLE, exit=2, 'attack does not verify — spec rejected'):
- atk_1 (PREPATCH BUG reproduced: injects_flag=False unconditionally) -> FAILS Ensures injects_flag==is_error_aware_kind on error-aware branch. exit=2.
- atk_2 (control-flow: negated guard) -> FAILS. exit=2.
- atk_3 (ungrounded-oracle echo: inject but hardcode inherited_style=True instead of parent.error_style) -> FAILS Implies(injects_flag, inherited_style is parent.error_style). exit=2.
- atk_4 (partial-domain: only inject when parent.error_style is True) -> FAILS injects_flag==is_error_aware_kind when flag is None/False. exit=2.
- atk_5 (boundary/plain-path scribble in open: else sets inherited_style=False) -> FAILS frame clause Implies(not injects_flag, inherited_style is Old(...)). exit=2. (re-confirms closed G-PANEL-1 weakness)
- atk_6 (build wrong value: child.error_style=True on inject path) -> FAILS Implies(carries_flag, error_style is builder.inherited_style). exit=2.
- atk_7 (build plain-path scribble: else sets error_style=False) -> FAILS frame clause Implies(not carries_flag, error_style is Old(...)). exit=2. (re-confirms symmetric closed G-PANEL-1 weakness)
- atk_8 (build control-flow: carries_flag negated) -> FAILS child.carries_flag==builder.injects_flag. exit=2.

Because ZERO attacks came back CANDIDATE (none both share-spec AND verify), no faithful refined patch needed materializing/resolve-running; verify never certified a wrong impl, so verify=>correct is not violated by any exhibited impl.

Refinement.md audit: legs A1-A6 (open_subcommand_group / add_subparsers) and B1-B3 (build_subcommand_parser / _SubParsersAction.add_parser) are all R, A-consumed, or I. Section C explicitly asserts NO kind-3: the genuinely-changed op (propagating the inherited error-style flag to sub-command parsers) is modelled DEEPLY over concrete fields (open policy + build consumption, both verified), not hidden behind an axiom. The single axiom is_error_aware_kind (A3, A-consumed) covers the UNCHANGED built-in guard issubclass(parser_class, CommandParser); it is @Pure @ContractOnly with the weakest contract (purity/determinism only, no Ensures), so the proof relies only on determinism. There is NO A-reference deep-model-vs-callee-equality leg.

A-leg correspondence holds and is doubly witnessed by axiom_check.py, which executes the REAL issubclass (bool + 64x-idempotent determinism, agreement on 9 boundary classes: CommandParser/subclasses True, ArgumentParser/vanilla-sub/unrelated/object/int/str False) AND the REAL end-to-end propagation (builds a real CommandParser, add_subparsers()+add_parser(), asserts the sub-command parser inherits called_from_command_line for parent_flag in {None,True,False}, and a parser_class=argparse.ArgumentParser sub-command parser has no such attribute). mapping.md binds each symbol at base_commit 1250483e and states the Optional[bool] type refinement and the partial(...)-as-policy abstraction.

Conclusion: >=5 (8) distinct verifying-wrong-impl attacks run and reported; none breaks the spec; positive control verifies; refinement.md has no kind-3 leg and its A-leg correspondence holds. verify=>correct not falsified. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-16454 (nagini): does the spec drift from / over-strengthen the real repo behavior of the modeled callees (CommandParser.add_subparsers, the changed function, followed by the unchanged argparse._SubParsersAction.add_parser)? Verdict: FAITHFUL — no diverging input found.

SETUP VERIFIED: at base_commit 1250483ebf73f7a82ff820b94092c63ce4238264 with gold patch applied (add_subparsers override present at base.py:75; partial(parser_class, called_from_command_line=self.called_from_command_line) at :78-80; super().add_subparsers(**kwargs)). Spec region byte-identical: `same-spec nagini django__django-16454` on the verbatim model.py returns exit 0.

EMPIRICAL CHECKS against the REAL patched repo (django 5.0a0, asgiref):
1. Bundle conformance_check.py (direct contract-stripped shadow of impl region vs real add_subparsers + add_parser), run independently => G-CONF OK, 100306 inputs (306 boundary + 100000 fuzz, seed 16454), 0 disagreements. Every spec postcondition holds against the real code: injects_flag == is_error_aware_kind(token); inherited_style IS parent.error_style on inject; plain-path builder/child frame (no writes, prior value kept); child.carries_flag == builder.injects_flag; child.error_style IS builder.inherited_style; plain child carries no called_from_command_line attribute.
2. Independent adversarial probe crossing parent flag over {None, True, False, arbitrary object(), 'cli', 0, 1, list} (well beyond the model's Optional[bool] domain) with parser_class in {CommandParser (default kind), subclass, __init__-overriding subclass, argparse.ArgumentParser, vanilla ArgumentParser subclass}. Results: injection decision always == issubclass(cls, CommandParser); the injected/child value is the parent flag by IS-identity (partial keyword binding passes the object through unchanged); every plain (non-error-aware) parser_class yields a bare factory and a child with no called_from_command_line attribute. FAILS: NONE.

The spec's strong `is`-identity postconditions match the real partial-binding semantics exactly (the flag object is not copied/coerced), so they are NOT over-strengthened — the real repo satisfies them. The one axiom (is_error_aware_kind <-> issubclass(.., CommandParser)) is A-consumed asserting only purity/determinism (weakest contract); G-AX passes with a real end-to-end propagation witness. No modeling boundary where the modeled functions disagree with the real callees was found. Spec is faithful, not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Reviewed the consumer spec view (markers.spec_view over model.py for nagini; impl regions elided) against the public problem_statement and the gold patch. Mechanical G-LEAK screen passes (leakage.screen: passed=True, hard_failures=[]).

Judgment: the spec view discloses nothing about the gold edit beyond what problem_statement already states publicly. The problem statement itself says CommandParser's extra error-formatting args 'are not copied into subparsers, created via CommandParser.add_subparsers().add_parser()' and that the fix is to 'ensure that the subparser action returned by add_subparsers() copies the relevant arguments through to constructed subparsers.' The spec view re-expresses exactly this behavior in abstract modeling terms: an Optional[bool] error-style flag (OpeningParser.error_style) that must be propagated to sub-command parsers of the error-aware kind, while the plain non-error-aware path is left untouched. That is WHAT (the behavioral contract), matching the public description, not HOW.

None of the gold-patch mechanism/discriminators appear in the spec view: no 'partial'/'functools', no 'called_from_command_line', no 'issubclass', no 'super().add_subparsers', no 'add_parser', no 'kwargs["parser_class"]'. The subclass guard is presented only as an opaque @Pure @ContractOnly predicate is_error_aware_kind(token) with no Ensures — its real identity as issubclass(parser_class, CommandParser) lives only in mapping.md, which is NOT part of the spec view. The two lexical substring hits ('CommandParser' inside the model name 'SubCommandParser'; 'parser_class' inside the abstract token name 'parser_class_token') are coincidental substrings of abstract model identifiers, not the gold repo symbols, and do not reveal the edit.

The frame-clause postconditions (Implies(not injects_flag, inherited_style is Old(...)) etc.) tighten the spec against panel weaknesses but describe behavioral obligations, not the gold source. A consumer given this spec view would still have to discover the partial-binding / issubclass / super-delegation implementation themselves.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
