# P2 adversarial audit — django__django-15127

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_prepatch.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -73,10 +72,6 @@
     """
 
     def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it sits at the bottom of the obligation order. Every obligated caller
-        # that allocates a result record must be at a strictly greater level.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.a) and self.a is a)  # type: ignore
         Ensures(Acc(self.b) and self.b is b)  # type: ignore
         Ensures(Acc(self.c) and self.c is c)  # type: ignore
@@ -135,7 +130,6 @@
     Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
     Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
     Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -175,11 +169,8 @@
     # post-conditions-end
     # impl-start
     if setting == setting_message_tags():
-        return Tags(merge_slot(defaults.a, override.a),
-                    merge_slot(defaults.b, override.b),
-                    merge_slot(defaults.c, override.c))
-    # Under any other identifier the result equals the in-force mapping: the
-    # returned record holds the same level-for-level slot values as ``current``
-    # (observationally the same mapping).
+        return Tags(merge_slot(override.a, defaults.a),
+                    merge_slot(override.b, defaults.b),
+                    merge_slot(override.c, defaults.c))
     return Tags(current.a, current.b, current.c)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -73,10 +72,6 @@
     """
 
     def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it sits at the bottom of the obligation order. Every obligated caller
-        # that allocates a result record must be at a strictly greater level.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.a) and self.a is a)  # type: ignore
         Ensures(Acc(self.b) and self.b is b)  # type: ignore
         Ensures(Acc(self.c) and self.c is c)  # type: ignore
@@ -135,7 +130,6 @@
     Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
     Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
     Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -175,11 +169,6 @@
     # post-conditions-end
     # impl-start
     if setting == setting_message_tags():
-        return Tags(merge_slot(defaults.a, override.a),
-                    merge_slot(defaults.b, override.b),
-                    merge_slot(defaults.c, override.c))
-    # Under any other identifier the result equals the in-force mapping: the
-    # returned record holds the same level-for-level slot values as ``current``
-    # (observationally the same mapping).
+        return Tags(override.a, override.b, override.c)
     return Tags(current.a, current.b, current.c)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -73,10 +72,6 @@
     """
 
     def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it sits at the bottom of the obligation order. Every obligated caller
-        # that allocates a result record must be at a strictly greater level.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.a) and self.a is a)  # type: ignore
         Ensures(Acc(self.b) and self.b is b)  # type: ignore
         Ensures(Acc(self.c) and self.c is c)  # type: ignore
@@ -135,7 +130,6 @@
     Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
     Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
     Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -176,10 +170,7 @@
     # impl-start
     if setting == setting_message_tags():
         return Tags(merge_slot(defaults.a, override.a),
-                    merge_slot(defaults.b, override.b),
+                    current.b,
                     merge_slot(defaults.c, override.c))
-    # Under any other identifier the result equals the in-force mapping: the
-    # returned record holds the same level-for-level slot values as ``current``
-    # (observationally the same mapping).
     return Tags(current.a, current.b, current.c)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -73,10 +72,6 @@
     """
 
     def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it sits at the bottom of the obligation order. Every obligated caller
-        # that allocates a result record must be at a strictly greater level.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.a) and self.a is a)  # type: ignore
         Ensures(Acc(self.b) and self.b is b)  # type: ignore
         Ensures(Acc(self.c) and self.c is c)  # type: ignore
@@ -135,7 +130,6 @@
     Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
     Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
     Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -174,12 +168,9 @@
                     and Result().c is current.c))
     # post-conditions-end
     # impl-start
-    if setting == setting_message_tags():
+    if setting != setting_message_tags():
         return Tags(merge_slot(defaults.a, override.a),
                     merge_slot(defaults.b, override.b),
                     merge_slot(defaults.c, override.c))
-    # Under any other identifier the result equals the in-force mapping: the
-    # returned record holds the same level-for-level slot values as ``current``
-    # (observationally the same mapping).
     return Tags(current.a, current.b, current.c)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -73,10 +72,6 @@
     """
 
     def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it sits at the bottom of the obligation order. Every obligated caller
-        # that allocates a result record must be at a strictly greater level.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.a) and self.a is a)  # type: ignore
         Ensures(Acc(self.b) and self.b is b)  # type: ignore
         Ensures(Acc(self.c) and self.c is c)  # type: ignore
@@ -135,7 +130,6 @@
     Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
     Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
     Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -175,11 +169,6 @@
     # post-conditions-end
     # impl-start
     if setting == setting_message_tags():
-        return Tags(merge_slot(defaults.a, override.a),
-                    merge_slot(defaults.b, override.b),
-                    merge_slot(defaults.c, override.c))
-    # Under any other identifier the result equals the in-force mapping: the
-    # returned record holds the same level-for-level slot values as ``current``
-    # (observationally the same mapping).
+        return Tags(defaults.a, defaults.b, defaults.c)
     return Tags(current.a, current.b, current.c)
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -73,10 +72,6 @@
     """
 
     def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it sits at the bottom of the obligation order. Every obligated caller
-        # that allocates a result record must be at a strictly greater level.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.a) and self.a is a)  # type: ignore
         Ensures(Acc(self.b) and self.b is b)  # type: ignore
         Ensures(Acc(self.c) and self.c is c)  # type: ignore
@@ -135,7 +130,6 @@
     Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
     Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
     Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -177,9 +171,6 @@
     if setting == setting_message_tags():
         return Tags(merge_slot(defaults.a, override.a),
                     merge_slot(defaults.b, override.b),
-                    merge_slot(defaults.c, override.c))
-    # Under any other identifier the result equals the in-force mapping: the
-    # returned record holds the same level-for-level slot values as ``current``
-    # (observationally the same mapping).
+                    override.c)
     return Tags(current.a, current.b, current.c)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -73,10 +72,6 @@
     """
 
     def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it sits at the bottom of the obligation order. Every obligated caller
-        # that allocates a result record must be at a strictly greater level.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.a) and self.a is a)  # type: ignore
         Ensures(Acc(self.b) and self.b is b)  # type: ignore
         Ensures(Acc(self.c) and self.c is c)  # type: ignore
@@ -135,7 +130,6 @@
     Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
     Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
     Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -178,8 +172,7 @@
         return Tags(merge_slot(defaults.a, override.a),
                     merge_slot(defaults.b, override.b),
                     merge_slot(defaults.c, override.c))
-    # Under any other identifier the result equals the in-force mapping: the
-    # returned record holds the same level-for-level slot values as ``current``
-    # (observationally the same mapping).
-    return Tags(current.a, current.b, current.c)
+    return Tags(merge_slot(defaults.a, override.a),
+                merge_slot(defaults.b, override.b),
+                merge_slot(defaults.c, override.c))
     # impl-end
```

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,6 @@
 """
 from typing import Optional
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -73,10 +72,6 @@
     """
 
     def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
-        # Level 1: this constructor is loop-free and calls nothing obligated, so
-        # it sits at the bottom of the obligation order. Every obligated caller
-        # that allocates a result record must be at a strictly greater level.
-        Requires(MustTerminate(1))
         Ensures(Acc(self.a) and self.a is a)  # type: ignore
         Ensures(Acc(self.b) and self.b is b)  # type: ignore
         Ensures(Acc(self.c) and self.c is c)  # type: ignore
@@ -135,7 +130,6 @@
     Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
     Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
     Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     # Inputs returned untouched at the same half permission.
@@ -174,12 +168,5 @@
                     and Result().c is current.c))
     # post-conditions-end
     # impl-start
-    if setting == setting_message_tags():
-        return Tags(merge_slot(defaults.a, override.a),
-                    merge_slot(defaults.b, override.b),
-                    merge_slot(defaults.c, override.c))
-    # Under any other identifier the result equals the in-force mapping: the
-    # returned record holds the same level-for-level slot values as ``current``
-    # (observationally the same mapping).
     return Tags(current.a, current.b, current.c)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15127.

Behaviour under specification (an abstract behavioural contract over the
function's inputs, NOT an edit or a diagnosis):

  A per-level tag mapping assigns, to each integer message level, the tag token
  to display for that level. It is derived from two value sources: a constant
  family of DEFAULT tags (one per built-in level) overlaid with a configurable
  OVERRIDE mapping. The derived mapping is exactly the default family with the
  override mapping merged on top -- per level: the override's value where the
  override carries the level, otherwise the default's value, and a level
  neither carries is absent.

  The function takes an identifier selecting which setting's value this call
  concerns (``setting``), the current override mapping (``override``), the
  default family (``defaults``), and the mapping presently in force
  (``current``); it returns the per-level mapping that should be in force given
  that input. The contract on the returned mapping, per level:

    * if the identifier is the message-tags identifier, the result equals the
      override merged onto the defaults (override wins where it carries the
      level, else the default value; a level only the override provides is
      present with the override's token, including a custom level the defaults
      never had);
    * if the identifier is any other identifier, the result equals the
      mapping presently in force, level for level.

  The level-tag read of a level is the mapping's token for that level if
  present, otherwise the empty tag token. The behaviour the contract pins:
  under the message-tags identifier, reading a level the override provides
  returns the override's token (not a stale value, and not the empty token for
  a custom level the defaults never had).

Modelling choices (Nagini fragment):
  * A tags mapping is observed only by membership-and-value at the levels that
    discriminate the behaviour: a built-in level the override re-tags, a
    built-in level the override omits, and a custom level the defaults never
    had. It is carried as a small record of ``Optional[int]`` slots (one per
    representative level; ``None`` = the level is absent from the mapping, else
    the tag token). This is the faithful finite abstraction of the real
    ``Dict[int, str]`` keyed by level (mapping.md §2) -- the merge and the
    read are pinned pointwise on each slot, so only the intended mapping
    satisfies the contract.
  * The mapping merge ``{**defaults, **override}`` is modelled DEEPLY (the
    per-slot override-wins choice spelled out in ``merge_slot``); the real
    Python merge is validated against this model out-of-band (axiom_check.py,
    G-AX, A-reference). The per-level derivation under the message-tags
    identifier is the impl region.
  * The level-tag read ``mapping.get(level, '')`` is the unchanged pure helper
    ``read_slot`` (a present slot reads its tag, an absent slot the empty tag).

The function allocates a fresh merged record and never writes its inputs, so
the read-only mapping records are immutable value carriers (their slots are
plain integers, no heap permission needed). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

# axioms-start
# (No @ContractOnly axioms consumed: the merge primitive is modelled deeply as
#  the pure record-level merge below and validated against real Python by G-AX.)
# axioms-end

# pure-start
class Tags:
    """A tags mapping observed at the three discriminating levels. Each slot is
    ``Optional[int]``: ``None`` means the level is absent from the mapping,
    otherwise the slot holds the level's tag token. An immutable value carrier.
    """

    def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
        Ensures(Acc(self.a) and self.a is a)  # type: ignore
        Ensures(Acc(self.b) and self.b is b)  # type: ignore
        Ensures(Acc(self.c) and self.c is c)  # type: ignore
        self.a = a  # built-in level the override re-tags
        self.b = b  # built-in level the override omits
        self.c = c  # custom level the defaults never had

@Pure
def setting_message_tags() -> int:
    # The token of the message-tags override setting (the one setting whose
    # change must re-derive the mapping). Any other token denotes a different
    # setting whose change leaves the mapping unchanged.
    return 1

@Pure
def empty_tag() -> int:
    # The empty tag token returned for a level the derived mapping lacks.
    return 0

@Pure
def slot_present(slot: Optional[int]) -> bool:
    # A slot denotes a present level iff it is not None.
    return slot is not None

@Pure
def read_slot(slot: Optional[int]) -> int:
    """The level-tag read of one slot (unchanged ``.get(level, '')``): the
    slot's tag token if the level is present, otherwise the empty tag token."""
    if slot is None:
        return empty_tag()
    return slot

@Pure
def merge_slot(d: Optional[int], o: Optional[int]) -> Optional[int]:
    """The per-level mapping merge ``{**defaults, **override}`` on one slot: the
    override's value wins where the override carries the level, otherwise the
    default's value. (Modelled deeply; validated == real Python by G-AX.)"""
    if o is not None:
        return o
    return d
# pure-end

def derive_tags_for_setting(setting: int, override: Tags,
                            defaults: Tags, current: Tags) -> Tags:
    # ``setting`` is an identifier selecting which setting's value this call
    # concerns (it equals ``setting_message_tags()`` when it concerns the
    # message-tags identifier, any other value otherwise).
    # pre-conditions-start
    # The three mapping records are read-only value carriers (immutable slots).
    Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
    Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
    Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # Inputs returned untouched at the same half permission.
    Ensures(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
    Ensures(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
    Ensures(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
    # A fresh, full-permission result mapping (when derived from the merge) or
    # the unchanged in-force mapping; both yield full read access on the
    # result's slots.
    Ensures(Acc(Result().a) and Acc(Result().b) and Acc(Result().c))
    Ensures(Result() is not None)
    # Under the message-tags identifier the result equals the override merged
    # onto the defaults, pinned uniformly per level (override wins where it
    # carries the level, else the default value carries -- the merge_slot
    # primitive). This single clause per slot closes every merge case:
    #   * a built-in level the override re-tags -> the override's token;
    #   * a built-in level the override omits -> the default value survives;
    #   * a custom level only the override provides -> present with the
    #     override token (so the level-tag read is NOT the empty token).
    Ensures(Implies(setting == setting_message_tags(),
                    Result().a is merge_slot(defaults.a, override.a)))
    Ensures(Implies(setting == setting_message_tags(),
                    Result().b is merge_slot(defaults.b, override.b)))
    Ensures(Implies(setting == setting_message_tags(),
                    Result().c is merge_slot(defaults.c, override.c)))
    # The discriminating level-tag read (the unchanged ``.get(level, '')``): on
    # the result of the message-tags derivation, a level the override provides
    # reads the override's token, not the empty token.
    Ensures(Implies(setting == setting_message_tags() and slot_present(override.c),
                    read_slot(Result().c) == read_slot(override.c)))
    # Under any other identifier the result equals the in-force mapping, level
    # for level.
    Ensures(Implies(setting != setting_message_tags(),
                    Result().a is current.a
                    and Result().b is current.b
                    and Result().c is current.c))
    # post-conditions-end
    # impl-start
    if setting == setting_message_tags():
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    merge_slot(defaults.c, override.c))
    return Tags(current.a, current.b, current.c)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-15127 (nagini). SPEC UNDER TEST: derive_tags_for_setting pins, under the message-tags identifier, Result().{a,b,c} is merge_slot(defaults.X, override.X) for all three slots, plus read_slot(Result().c)==read_slot(override.c) when override.c present; under any other identifier Result().{a,b,c} is current.{a,b,c}. All slots pinned pointwise -> the spec fully determines the returned mapping on the 3-slot abstraction.

PROTOCOL RUN (all machine-checked, editing ONLY the impl region; axioms/@Pure/Requires/Ensures byte-identical, confirmed by same-spec exit 0 on all 9 files).

Positive control pos_control.py (gold impl) VERIFIES: `bash scripts/nagini_verify.sh .../pos_control.py` -> exit 0 (~8s). So the spec is satisfiable by the correct impl.

8 wrong impls, each same-spec (adversary same-spec exit 0) and each run through `python -m swebench_unified.adversary weakness nagini django__django-15127 .../atk_N.py`: atk_prepatch (prepatch bug: always returns stale current; never re-derives) -> weakness exit 2 NOT-A-COUNTEREXAMPLE, fails Result().a-merge clause (verify exit 1, 13.1s).

PREPATCH REPRODUCED (spec senses the change, G-DIFF). atk_1 (default-wins: merge_slot args swapped) -> exit 2, fails slot-a merge clause (13.8s). atk_2 (boundary: returns override.{a,b,c} directly; wrong when override slot None & default present) -> exit 2, fails slot-a clause (12.6s). atk_3 (partial-domain: slot b left = current.b) -> exit 2, fails slot-b merge clause (13.5s). atk_4 (control-flow: branches swapped, `if setting != ...`) -> exit 2, fails the other-setting=>current clause (14.3s). atk_5 (defaults-only: ignores override entirely in msg-tags branch) -> exit 2, fails slot-a clause (12.1s). atk_6 (ungrounded-oracle echo: slot c uses override.c directly; equiv only when defaults.c None) -> exit 2, fails slot-c merge clause (13.1s). atk_7 (control-flow-effect: non-msg-tags branch also returns the merge instead of current) -> exit 2, fails other-setting=>current clause (14.9s).

Every attack failed on PRECISELY the postcondition clause its behavioral deviation violates; all are genuine Z3 postcondition failures (12-15s, NOT timeouts/exit 124/infra errors). ZERO CANDIDATE-COUNTEREXAMPLES emerged (no wrong impl both shares the spec AND verifies), so NO faithful refined patch needed materializing / run_resolve (that step triggers only on a verifying candidate; none exists). The pointwise pinning of all three merge classes (re-tagged built-in, omitted built-in, custom-only level) plus the else=>current clause leaves no verifying-but-wrong impl room.

A-LEG / correspondence audit (refinement.md): A1,A2=R (token & Dict->Tags 3-slot abstraction, faithful/sufficient per mapping.md 2.1); A3,A5,A6=I (guard, else-branch, ready() wiring control-flow facts); A4=A-reference (merge_slot deep-models {**d,**o}; NO consumed @ContractOnly axiom). No kind-3 leg. G-AX executed: `python axiom_check.py` -> exit 0, 'merge_slot deep model (== real {**d,**o}) + read_slot (== real .get(level,'')) sound on 7 boundary + 20000 fuzz merges; F2P custom-level re-derivation verified' — the sole A-reference's correspondence to the real callee HOLDS.

VERDICT SOUND: >=5 distinct adversarial wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, default-wins, defaults-only, branch-swap) + the prepatch bug all run and NONE verifies against the frozen spec; positive control verifies; G-AX A-reference sound. verify=>correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py`, `atk_prepatch.py` |

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

Attack 8 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-15127.

Behaviour under specification (an abstract behavioural contract over the
function's inputs, NOT an edit or a diagnosis):

  A per-level tag mapping assigns, to each integer message level, the tag token
  to display for that level. It is derived from two value sources: a constant
  family of DEFAULT tags (one per built-in level) overlaid with a configurable
  OVERRIDE mapping. The derived mapping is exactly the default family with the
  override mapping merged on top -- per level: the override's value where the
  override carries the level, otherwise the default's value, and a level
  neither carries is absent.

  The function takes an identifier selecting which setting's value this call
  concerns (``setting``), the current override mapping (``override``), the
  default family (``defaults``), and the mapping presently in force
  (``current``); it returns the per-level mapping that should be in force given
  that input. The contract on the returned mapping, per level:

    * if the identifier is the message-tags identifier, the result equals the
      override merged onto the defaults (override wins where it carries the
      level, else the default value; a level only the override provides is
      present with the override's token, including a custom level the defaults
      never had);
    * if the identifier is any other identifier, the result equals the
      mapping presently in force, level for level.

  The level-tag read of a level is the mapping's token for that level if
  present, otherwise the empty tag token. The behaviour the contract pins:
  under the message-tags identifier, reading a level the override provides
  returns the override's token (not a stale value, and not the empty token for
  a custom level the defaults never had).

Modelling choices (Nagini fragment):
  * A tags mapping is observed only by membership-and-value at the levels that
    discriminate the behaviour: a built-in level the override re-tags, a
    built-in level the override omits, and a custom level the defaults never
    had. It is carried as a small record of ``Optional[int]`` slots (one per
    representative level; ``None`` = the level is absent from the mapping, else
    the tag token). This is the faithful finite abstraction of the real
    ``Dict[int, str]`` keyed by level (mapping.md §2) -- the merge and the
    read are pinned pointwise on each slot, so only the intended mapping
    satisfies the contract.
  * The mapping merge ``{**defaults, **override}`` is modelled DEEPLY (the
    per-slot override-wins choice spelled out in ``merge_slot``); the real
    Python merge is validated against this model out-of-band (axiom_check.py,
    G-AX, A-reference). The per-level derivation under the message-tags
    identifier is the impl region.
  * The level-tag read ``mapping.get(level, '')`` is the unchanged pure helper
    ``read_slot`` (a present slot reads its tag, an absent slot the empty tag).

The function allocates a fresh merged record and never writes its inputs, so
the read-only mapping records are immutable value carriers (their slots are
plain integers, no heap permission needed). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *

# axioms-start
# (No @ContractOnly axioms consumed: the merge primitive is modelled deeply as
#  the pure record-level merge below and validated against real Python by G-AX.)
# axioms-end

# pure-start
class Tags:
    """A tags mapping observed at the three discriminating levels. Each slot is
    ``Optional[int]``: ``None`` means the level is absent from the mapping,
    otherwise the slot holds the level's tag token. An immutable value carrier.
    """

    def __init__(self, a: Optional[int], b: Optional[int], c: Optional[int]) -> None:
        Ensures(Acc(self.a) and self.a is a)  # type: ignore
        Ensures(Acc(self.b) and self.b is b)  # type: ignore
        Ensures(Acc(self.c) and self.c is c)  # type: ignore
        self.a = a  # built-in level the override re-tags
        self.b = b  # built-in level the override omits
        self.c = c  # custom level the defaults never had

@Pure
def setting_message_tags() -> int:
    # The token of the message-tags override setting (the one setting whose
    # change must re-derive the mapping). Any other token denotes a different
    # setting whose change leaves the mapping unchanged.
    return 1

@Pure
def empty_tag() -> int:
    # The empty tag token returned for a level the derived mapping lacks.
    return 0

@Pure
def slot_present(slot: Optional[int]) -> bool:
    # A slot denotes a present level iff it is not None.
    return slot is not None

@Pure
def read_slot(slot: Optional[int]) -> int:
    """The level-tag read of one slot (unchanged ``.get(level, '')``): the
    slot's tag token if the level is present, otherwise the empty tag token."""
    if slot is None:
        return empty_tag()
    return slot

@Pure
def merge_slot(d: Optional[int], o: Optional[int]) -> Optional[int]:
    """The per-level mapping merge ``{**defaults, **override}`` on one slot: the
    override's value wins where the override carries the level, otherwise the
    default's value. (Modelled deeply; validated == real Python by G-AX.)"""
    if o is not None:
        return o
    return d
# pure-end

def derive_tags_for_setting(setting: int, override: Tags,
                            defaults: Tags, current: Tags) -> Tags:
    # ``setting`` is an identifier selecting which setting's value this call
    # concerns (it equals ``setting_message_tags()`` when it concerns the
    # message-tags identifier, any other value otherwise).
    # pre-conditions-start
    # The three mapping records are read-only value carriers (immutable slots).
    Requires(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
    Requires(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
    Requires(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # Inputs returned untouched at the same half permission.
    Ensures(Acc(override.a, 1 / 2) and Acc(override.b, 1 / 2) and Acc(override.c, 1 / 2))
    Ensures(Acc(defaults.a, 1 / 2) and Acc(defaults.b, 1 / 2) and Acc(defaults.c, 1 / 2))
    Ensures(Acc(current.a, 1 / 2) and Acc(current.b, 1 / 2) and Acc(current.c, 1 / 2))
    # A fresh, full-permission result mapping (when derived from the merge) or
    # the unchanged in-force mapping; both yield full read access on the
    # result's slots.
    Ensures(Acc(Result().a) and Acc(Result().b) and Acc(Result().c))
    Ensures(Result() is not None)
    # Under the message-tags identifier the result equals the override merged
    # onto the defaults, pinned uniformly per level (override wins where it
    # carries the level, else the default value carries -- the merge_slot
    # primitive). This single clause per slot closes every merge case:
    #   * a built-in level the override re-tags -> the override's token;
    #   * a built-in level the override omits -> the default value survives;
    #   * a custom level only the override provides -> present with the
    #     override token (so the level-tag read is NOT the empty token).
    Ensures(Implies(setting == setting_message_tags(),
                    Result().a is merge_slot(defaults.a, override.a)))
    Ensures(Implies(setting == setting_message_tags(),
                    Result().b is merge_slot(defaults.b, override.b)))
    Ensures(Implies(setting == setting_message_tags(),
                    Result().c is merge_slot(defaults.c, override.c)))
    # The discriminating level-tag read (the unchanged ``.get(level, '')``): on
    # the result of the message-tags derivation, a level the override provides
    # reads the override's token, not the empty token.
    Ensures(Implies(setting == setting_message_tags() and slot_present(override.c),
                    read_slot(Result().c) == read_slot(override.c)))
    # Under any other identifier the result equals the in-force mapping, level
    # for level.
    Ensures(Implies(setting != setting_message_tags(),
                    Result().a is current.a
                    and Result().b is current.b
                    and Result().c is current.c))
    # post-conditions-end
    # impl-start
    if setting == setting_message_tags():
        return Tags(merge_slot(defaults.a, override.a),
                    merge_slot(defaults.b, override.b),
                    merge_slot(defaults.c, override.c))
    return Tags(current.a, current.b, current.c)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-15127 (nagini). SPEC UNDER TEST: derive_tags_for_setting pins, under the message-tags identifier, Result().{a,b,c} is merge_slot(defaults.X, override.X) for all three slots, plus read_slot(Result().c)==read_slot(override.c) when override.c present; under any other identifier Result().{a,b,c} is current.{a,b,c}. All slots pinned pointwise -> the spec fully determines the returned mapping on the 3-slot abstraction.

PROTOCOL RUN (all machine-checked, editing ONLY the impl region; axioms/@Pure/Requires/Ensures byte-identical, confirmed by same-spec exit 0 on all 9 files).

Positive control pos_control.py (gold impl) VERIFIES: `bash scripts/nagini_verify.sh .../pos_control.py` -> exit 0 (~8s). So the spec is satisfiable by the correct impl.

8 wrong impls, each same-spec (adversary same-spec exit 0) and each run through `python -m swebench_unified.adversary weakness nagini django__django-15127 .../atk_N.py`: atk_prepatch (prepatch bug: always returns stale current; never re-derives) -> weakness exit 2 NOT-A-COUNTEREXAMPLE, fails Result().a-merge clause (verify exit 1, 13.1s).

PREPATCH REPRODUCED (spec senses the change, G-DIFF). atk_1 (default-wins: merge_slot args swapped) -> exit 2, fails slot-a merge clause (13.8s). atk_2 (boundary: returns override.{a,b,c} directly; wrong when override slot None & default present) -> exit 2, fails slot-a clause (12.6s). atk_3 (partial-domain: slot b left = current.b) -> exit 2, fails slot-b merge clause (13.5s). atk_4 (control-flow: branches swapped, `if setting != ...`) -> exit 2, fails the other-setting=>current clause (14.3s). atk_5 (defaults-only: ignores override entirely in msg-tags branch) -> exit 2, fails slot-a clause (12.1s). atk_6 (ungrounded-oracle echo: slot c uses override.c directly; equiv only when defaults.c None) -> exit 2, fails slot-c merge clause (13.1s). atk_7 (control-flow-effect: non-msg-tags branch also returns the merge instead of current) -> exit 2, fails other-setting=>current clause (14.9s).

Every attack failed on PRECISELY the postcondition clause its behavioral deviation violates; all are genuine Z3 postcondition failures (12-15s, NOT timeouts/exit 124/infra errors). ZERO CANDIDATE-COUNTEREXAMPLES emerged (no wrong impl both shares the spec AND verifies), so NO faithful refined patch needed materializing / run_resolve (that step triggers only on a verifying candidate; none exists). The pointwise pinning of all three merge classes (re-tagged built-in, omitted built-in, custom-only level) plus the else=>current clause leaves no verifying-but-wrong impl room.

A-LEG / correspondence audit (refinement.md): A1,A2=R (token & Dict->Tags 3-slot abstraction, faithful/sufficient per mapping.md 2.1); A3,A5,A6=I (guard, else-branch, ready() wiring control-flow facts); A4=A-reference (merge_slot deep-models {**d,**o}; NO consumed @ContractOnly axiom). No kind-3 leg. G-AX executed: `python axiom_check.py` -> exit 0, 'merge_slot deep model (== real {**d,**o}) + read_slot (== real .get(level,'')) sound on 7 boundary + 20000 fuzz merges; F2P custom-level re-derivation verified' — the sole A-reference's correspondence to the real callee HOLDS.

VERDICT SOUND: >=5 distinct adversarial wrong impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, default-wins, defaults-only, branch-swap) + the prepatch bug all run and NONE verifies against the frozen spec; positive control verifies; G-AX A-reference sound. verify=>correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-15127 nagini. The modeled function derive_tags_for_setting AGREES with the real patched callee update_level_tags on every input probed; no diverging input found.

Method: (1) Model verifies under pinned Nagini (exit 0, 10.6s) so the spec is non-vacuous. (2) Ran the bundle's own conformance_check.py (shadow = contract-stripped impl region) against the REAL patched repo at base_commit 9a6e2df3a8: 132,810 input vectors (31 boundary + 45,000 fuzz, seed 15127), 0 disagreements, exit 0. (3) Direct probing of each postcondition clause against the real update_level_tags / get_level_tags:
  - Under MESSAGE_TAGS: result == {**DEFAULT_TAGS, **MESSAGE_TAGS} for empty override, re-tag of built-in, re-tag to '', custom-only level {12:'custom'}, mixed empty+custom, and absent override -> all MATCH. This is exactly the postcondition Result().X is merge_slot(defaults.X, override.X) (override-wins-else-default) plus the custom-level read read_slot(Result().c)==read_slot(override.c).
  - Under non-MESSAGE_TAGS settings (DEBUG, USE_TZ, message_tags [case-sensitive], MESSAGE_TAGS2): base.LEVEL_TAGS stays untouched == current -> matches Result() is current per slot.

The 3-slot Optional[int] abstraction (None<->absent, 0<->'', distinct ints<->distinct tags) is a faithful finite model of Dict[int,str]: merge and read are pointwise, and the three representative levels instantiate exactly the three merge classes (re-tagged built-in, omitted built-in, custom override-only). No clause over-constrains the real behavior; the discriminating boundary cases (empty-string retag, custom-only level, case-sensitive setting name) all agree. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view leakage screen for django__django-15127 (nagini). Mechanical G-LEAK screen (leakage.screen over spec_view) passes clean: no diff markers, no reproduced gold-patch lines, no patched file/module path, no patched-symbol echo, no narration. No RELAXED_LEAKAGE.md present (strict).

Gold edit is in django/contrib/messages/apps.py: adds update_level_tags(setting, **kwargs) doing `if setting=='MESSAGE_TAGS': base.LEVEL_TAGS = get_level_tags()`, wired via MessagesConfig.ready() -> setting_changed.connect(...). Distinctive changed symbols: {ready, update_level_tags}.

Verified none of the gold mechanism leaks into the spec view: tokens 'level_tags','setting_changed','connect','ready','get_level_tags','override_settings','apps.py','signal','base.','default_tags' are ALL absent. Patched symbols ready/update_level_tags do not appear anywhere in the spec view.

The spec-view tokens that DO appear ('message-tags identifier', merge-of-override-onto-defaults, {**defaults,**override}, .get(level,'') read, custom-level-reads-empty-token) restate the public correctness behavior already disclosed in the problem_statement ('LEVEL_TAGS not updated when using @override_settings'; new MESSAGE_TAGS not picked up; Message.level_tag returns empty string for the new tags). That is the legitimate correctness spec, not a disclosure of the edit.

The spec abstracts the actual gold mechanism entirely (signals/setting_changed/connect/ready/get_level_tags/base.LEVEL_TAGS rebind/apps.py location are all hidden behind the abstract derive_tags_for_setting contract). A solver seeing only the spec view cannot reconstruct the gold's signal-wiring edit beyond what problem_statement already provides. No single spec-view line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).