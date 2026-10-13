# P2 adversarial audit — pydata__xarray-6992

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
@@ -62,7 +62,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class State:
@@ -70,7 +69,6 @@
 
     def __init__(self, variables: PSet[int], coord_names: PSet[int],
                  indexes: PSet[int], index_repr: PSet[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.variables) and Acc(self.coord_names))  # type: ignore
         Ensures(Acc(self.indexes) and Acc(self.index_repr))  # type: ignore
         Ensures(self.variables is variables and self.coord_names is coord_names)  # type: ignore
@@ -144,7 +142,6 @@
     Requires(subset(promoted_names, new_index_vars))
     # The displaced pre-existing index coordinates are existing index names.
     Requires(subset(displaced_index_coords, indexes0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -203,7 +200,6 @@
     # have stored arrays in the result and are neither dropped nor converted.
     Requires(disjoint(new_index_vars, dropped_coords))
     Requires(disjoint(new_index_vars, converted_coords))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -240,6 +236,6 @@
     variables_out = (variables0 - dropped_coords) + new_index_vars
     # the coordinate set must DROP every name that lost its array, KEEP every
     # converted name, then take in any replacement index coordinate.
-    coord_names_out = (coord_names0 - dropped_coords) + new_index_vars
+    coord_names_out = coord_names0 + new_index_vars
     return State(variables_out, coord_names_out, indexes_out, index_repr_out)
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class State:
@@ -70,7 +69,6 @@
 
     def __init__(self, variables: PSet[int], coord_names: PSet[int],
                  indexes: PSet[int], index_repr: PSet[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.variables) and Acc(self.coord_names))  # type: ignore
         Ensures(Acc(self.indexes) and Acc(self.index_repr))  # type: ignore
         Ensures(self.variables is variables and self.coord_names is coord_names)  # type: ignore
@@ -144,7 +142,6 @@
     Requires(subset(promoted_names, new_index_vars))
     # The displaced pre-existing index coordinates are existing index names.
     Requires(subset(displaced_index_coords, indexes0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -203,7 +200,6 @@
     # have stored arrays in the result and are neither dropped nor converted.
     Requires(disjoint(new_index_vars, dropped_coords))
     Requires(disjoint(new_index_vars, converted_coords))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -237,9 +233,7 @@
     index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars
     # variables: only the dropped names lose their stored array; converted names
     # keep theirs. Take in the replacement index coordinates.
-    variables_out = (variables0 - dropped_coords) + new_index_vars
-    # the coordinate set must DROP every name that lost its array, KEEP every
-    # converted name, then take in any replacement index coordinate.
-    coord_names_out = (coord_names0 - dropped_coords) + new_index_vars
+    variables_out = ((variables0 - dropped_coords) - converted_coords) + new_index_vars
+    coord_names_out = ((coord_names0 - dropped_coords) - converted_coords) + new_index_vars
     return State(variables_out, coord_names_out, indexes_out, index_repr_out)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class State:
@@ -70,7 +69,6 @@
 
     def __init__(self, variables: PSet[int], coord_names: PSet[int],
                  indexes: PSet[int], index_repr: PSet[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.variables) and Acc(self.coord_names))  # type: ignore
         Ensures(Acc(self.indexes) and Acc(self.index_repr))  # type: ignore
         Ensures(self.variables is variables and self.coord_names is coord_names)  # type: ignore
@@ -144,7 +142,6 @@
     Requires(subset(promoted_names, new_index_vars))
     # The displaced pre-existing index coordinates are existing index names.
     Requires(subset(displaced_index_coords, indexes0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -203,7 +200,6 @@
     # have stored arrays in the result and are neither dropped nor converted.
     Requires(disjoint(new_index_vars, dropped_coords))
     Requires(disjoint(new_index_vars, converted_coords))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -234,7 +230,7 @@
     indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars
     # index-backed representation: dropped names lose their array; converted
     # names are re-stored as PLAIN arrays (leave the index-backed kind).
-    index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars
+    index_repr_out = (index_repr0 - dropped_coords) + new_index_vars
     # variables: only the dropped names lose their stored array; converted names
     # keep theirs. Take in the replacement index coordinates.
     variables_out = (variables0 - dropped_coords) + new_index_vars
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class State:
@@ -70,7 +69,6 @@
 
     def __init__(self, variables: PSet[int], coord_names: PSet[int],
                  indexes: PSet[int], index_repr: PSet[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.variables) and Acc(self.coord_names))  # type: ignore
         Ensures(Acc(self.indexes) and Acc(self.index_repr))  # type: ignore
         Ensures(self.variables is variables and self.coord_names is coord_names)  # type: ignore
@@ -144,7 +142,6 @@
     Requires(subset(promoted_names, new_index_vars))
     # The displaced pre-existing index coordinates are existing index names.
     Requires(subset(displaced_index_coords, indexes0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -203,7 +200,6 @@
     # have stored arrays in the result and are neither dropped nor converted.
     Requires(disjoint(new_index_vars, dropped_coords))
     Requires(disjoint(new_index_vars, converted_coords))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -231,7 +227,7 @@
     # impl-start
     # index status after teardown: surviving index coords are those neither
     # dropped nor converted, plus any freshly created replacement index.
-    indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars
+    indexes_out = (indexes0 - dropped_coords) + new_index_vars
     # index-backed representation: dropped names lose their array; converted
     # names are re-stored as PLAIN arrays (leave the index-backed kind).
     index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class State:
@@ -70,7 +69,6 @@
 
     def __init__(self, variables: PSet[int], coord_names: PSet[int],
                  indexes: PSet[int], index_repr: PSet[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.variables) and Acc(self.coord_names))  # type: ignore
         Ensures(Acc(self.indexes) and Acc(self.index_repr))  # type: ignore
         Ensures(self.variables is variables and self.coord_names is coord_names)  # type: ignore
@@ -144,7 +142,6 @@
     Requires(subset(promoted_names, new_index_vars))
     # The displaced pre-existing index coordinates are existing index names.
     Requires(subset(displaced_index_coords, indexes0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -178,8 +175,8 @@
     # index status after promotion: surviving old index coords (the displaced
     # ones lose their index), plus the new index's coordinates.
     indexes_out = (indexes0 - displaced_index_coords) + new_index_vars
-    # index-backed representation: the converted (re-added) coords leave it.
-    index_repr_out = (index_repr0 - readd) + new_index_vars
+    # BUG: leave displaced coords in the index-backed representation (no readd removal).
+    index_repr_out = index_repr0 + new_index_vars
     variables_out = (variables0 - drop_variables) + new_variables_all
     coord_names_out = (coord_names0 - drop_variables) + new_variables_all
     return State(variables_out, coord_names_out, indexes_out, index_repr_out)
@@ -203,7 +200,6 @@
     # have stored arrays in the result and are neither dropped nor converted.
     Requires(disjoint(new_index_vars, dropped_coords))
     Requires(disjoint(new_index_vars, converted_coords))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class State:
@@ -70,7 +69,6 @@
 
     def __init__(self, variables: PSet[int], coord_names: PSet[int],
                  indexes: PSet[int], index_repr: PSet[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.variables) and Acc(self.coord_names))  # type: ignore
         Ensures(Acc(self.indexes) and Acc(self.index_repr))  # type: ignore
         Ensures(self.variables is variables and self.coord_names is coord_names)  # type: ignore
@@ -144,7 +142,6 @@
     Requires(subset(promoted_names, new_index_vars))
     # The displaced pre-existing index coordinates are existing index names.
     Requires(subset(displaced_index_coords, indexes0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -203,7 +200,6 @@
     # have stored arrays in the result and are neither dropped nor converted.
     Requires(disjoint(new_index_vars, dropped_coords))
     Requires(disjoint(new_index_vars, converted_coords))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -231,9 +227,8 @@
     # impl-start
     # index status after teardown: surviving index coords are those neither
     # dropped nor converted, plus any freshly created replacement index.
-    indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars
-    # index-backed representation: dropped names lose their array; converted
-    # names are re-stored as PLAIN arrays (leave the index-backed kind).
+    # BUG: spuriously re-add converted_coords into the index set (they should leave).
+    indexes_out = (((indexes0 - dropped_coords) - converted_coords) + new_index_vars) + converted_coords
     index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars
     # variables: only the dropped names lose their stored array; converted names
     # keep theirs. Take in the replacement index coordinates.
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class State:
@@ -70,7 +69,6 @@
 
     def __init__(self, variables: PSet[int], coord_names: PSet[int],
                  indexes: PSet[int], index_repr: PSet[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.variables) and Acc(self.coord_names))  # type: ignore
         Ensures(Acc(self.indexes) and Acc(self.index_repr))  # type: ignore
         Ensures(self.variables is variables and self.coord_names is coord_names)  # type: ignore
@@ -144,7 +142,6 @@
     Requires(subset(promoted_names, new_index_vars))
     # The displaced pre-existing index coordinates are existing index names.
     Requires(subset(displaced_index_coords, indexes0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -174,7 +171,8 @@
     # that is neither promoted nor part of the new index is converted out of the
     # index-backed representation.
     readd = (drop_variables - new_index_vars) - promoted_names
-    new_variables_all = new_index_vars + readd
+    # BUG: forget to re-add the converted (readd) coords to variables.
+    new_variables_all = new_index_vars
     # index status after promotion: surviving old index coords (the displaced
     # ones lose their index), plus the new index's coordinates.
     indexes_out = (indexes0 - displaced_index_coords) + new_index_vars
@@ -203,7 +201,6 @@
     # have stored arrays in the result and are neither dropped nor converted.
     Requires(disjoint(new_index_vars, dropped_coords))
     Requires(disjoint(new_index_vars, converted_coords))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class State:
@@ -70,7 +69,6 @@
 
     def __init__(self, variables: PSet[int], coord_names: PSet[int],
                  indexes: PSet[int], index_repr: PSet[int]) -> None:
-        Requires(MustTerminate(1))
         Ensures(Acc(self.variables) and Acc(self.coord_names))  # type: ignore
         Ensures(Acc(self.indexes) and Acc(self.index_repr))  # type: ignore
         Ensures(self.variables is variables and self.coord_names is coord_names)  # type: ignore
@@ -144,7 +142,6 @@
     Requires(subset(promoted_names, new_index_vars))
     # The displaced pre-existing index coordinates are existing index names.
     Requires(subset(displaced_index_coords, indexes0))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
@@ -177,8 +174,8 @@
     new_variables_all = new_index_vars + readd
     # index status after promotion: surviving old index coords (the displaced
     # ones lose their index), plus the new index's coordinates.
-    indexes_out = (indexes0 - displaced_index_coords) + new_index_vars
-    # index-backed representation: the converted (re-added) coords leave it.
+    # BUG: keep displaced coords in the index set.
+    indexes_out = indexes0 + new_index_vars
     index_repr_out = (index_repr0 - readd) + new_index_vars
     variables_out = (variables0 - drop_variables) + new_variables_all
     coord_names_out = (coord_names0 - drop_variables) + new_variables_all
@@ -203,7 +200,6 @@
     # have stored arrays in the result and are neither dropped nor converted.
     Requires(disjoint(new_index_vars, dropped_coords))
     Requires(disjoint(new_index_vars, converted_coords))
-    Requires(MustTerminate(10))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for pydata__xarray-6992.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A labelled-array container tracks four name collections over a common universe
  of name identifiers:

    * ``variables``    -- names that have a stored array;
    * ``coord_names``  -- the coordinate names (a subset of ``variables``);
    * ``indexes``      -- the coordinate names that currently carry an index;
    * ``index_repr``   -- the coordinate names whose stored array uses the
                          index-backed representation (the "kind" of the array).

  A WELL-FORMED container satisfies, simultaneously,

      indexes  is a subset of  coord_names  is a subset of  variables,

  AND its stored representation never gets ahead of index status:

      index_repr  is a subset of  indexes

  -- no coordinate is left in the index-backed representation once it no longer
  carries an index. (The number of plain data names is
  ``len(variables) - len(coord_names)``; a coordinate name lacking a stored
  array would drive that count negative, which a real container can never do.
  A coordinate left in the index-backed representation without a live index is
  the dangling state the repr code likewise cannot tolerate.)

  Two reshaping operations are specified; each returns the four name collections
  of a new container that must be well-formed:

  (1) Promoting one or more existing names to be the index of a dimension. Any
      pre-existing index whose coordinates are displaced by the promotion loses
      its index. A displaced coordinate that is neither promoted nor part of the
      new index, yet remains a coordinate, must be CONVERTED out of the
      index-backed representation (re-added as a plain stored array) so that it
      is still a coordinate with a stored array and is no longer counted as
      index-backed. The exact resulting collections are pinned below.

  (2) Tearing down the index of one or more dimensions/levels. Each affected
      name takes one of THREE fates, and the result is pinned exactly under all
      three:
        * a DROPPED name loses its stored array entirely -- it leaves all four
          collections (it must be removed from the coordinate set too, so the
          result never names a coordinate that has no stored array);
        * a CONVERTED name keeps its stored array as a PLAIN array -- it stays a
          variable and a coordinate but is removed from the indexes and from the
          index-backed representation (converted out of the index-backed kind);
        * a freshly created REPLACEMENT index coordinate is added to all four
          collections.
      The exact resulting collections are pinned below over these three channels.

The four name collections are modelled as ``PSet[int]`` of integer name
identifiers (the only operations on names are set membership / union /
difference / equality, never any character-level operation). Each result is
returned as a ``State`` record of the four collections; the postconditions pin
every collection to an exact set expression OVER THE INPUT COLLECTIONS (so the
result must be PRODUCED by the modelled set algebra, not merely happen to be
well-formed) and additionally assert well-formedness.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class State:
    """The four name collections of a container (immutable record)."""

    def __init__(self, variables: PSet[int], coord_names: PSet[int],
                 indexes: PSet[int], index_repr: PSet[int]) -> None:
        Ensures(Acc(self.variables) and Acc(self.coord_names))  # type: ignore
        Ensures(Acc(self.indexes) and Acc(self.index_repr))  # type: ignore
        Ensures(self.variables is variables and self.coord_names is coord_names)  # type: ignore
        Ensures(self.indexes is indexes and self.index_repr is index_repr)  # type: ignore
        self.variables = variables  # type: ignore
        self.coord_names = coord_names  # type: ignore
        self.indexes = indexes  # type: ignore
        self.index_repr = index_repr  # type: ignore


# axioms-start
# (No axiomatized callees. The whole behaviour is the well-formedness-preserving
# recomputation of four name collections under set union / difference, modelled
# DEEPLY over PSet[int]. The set primitives are unchanged operations refined to
# PSet membership, not axioms the proof consumes -- see refinement.md /
# mapping.md.)
# axioms-end


# pure-start
@Pure
def subset(a: PSet[int], b: PSet[int]) -> bool:
    """Every member of ``a`` is a member of ``b``."""
    return Forall(int, lambda x: Implies(x in a, x in b))


@Pure
def disjoint(a: PSet[int], b: PSet[int]) -> bool:
    """``a`` and ``b`` share no member."""
    return Forall(int, lambda x: Implies(x in a, not (x in b)))


@Pure
def well_formed(variables: PSet[int], coord_names: PSet[int],
                indexes: PSet[int], index_repr: PSet[int]) -> bool:
    """A container is well-formed when its index names are coordinates, its
    coordinate names all have a stored array, and no coordinate is left in the
    index-backed representation once it no longer carries an index."""
    return (subset(indexes, coord_names)
            and subset(coord_names, variables)
            and subset(index_repr, indexes))


@Pure
def promote_dropped(promoted: PSet[int], displaced: PSet[int]) -> PSet[int]:
    """Names whose array is removed before the promotion result is rebuilt: the
    promoted names together with the displaced pre-existing index coordinates."""
    return promoted + displaced


@Pure
def promote_readd(promoted: PSet[int], displaced: PSet[int],
                  new_index_vars: PSet[int]) -> PSet[int]:
    """The displaced coordinates converted out of the index-backed
    representation: those dropped, that are neither part of the new index nor
    themselves being promoted."""
    return (promote_dropped(promoted, displaced) - new_index_vars) - promoted
# pure-end


def promote_to_index(
        variables0: PSet[int], coord_names0: PSet[int], indexes0: PSet[int],
        index_repr0: PSet[int], new_index_vars: PSet[int],
        promoted_names: PSet[int], displaced_index_coords: PSet[int]) -> State:
    # pre-conditions-start
    # The input container is well-formed.
    Requires(well_formed(variables0, coord_names0, indexes0, index_repr0))
    # The promoted names come from the input container (they have stored arrays)
    # and they all become coordinates of the new index.
    Requires(subset(promoted_names, variables0))
    Requires(subset(promoted_names, new_index_vars))
    # The displaced pre-existing index coordinates are existing index names.
    Requires(subset(displaced_index_coords, indexes0))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
    Ensures(Acc(Result().indexes, 1 / 2) and Acc(Result().index_repr, 1 / 2))  # type: ignore
    # Exact resulting collections, pinned over the input collections.
    Ensures(Result().indexes  # type: ignore
            == (indexes0 - displaced_index_coords) + new_index_vars)
    Ensures(Result().index_repr  # type: ignore
            == (index_repr0 - promote_readd(promoted_names, displaced_index_coords, new_index_vars))
            + new_index_vars)
    Ensures(Result().variables  # type: ignore
            == (variables0 - promote_dropped(promoted_names, displaced_index_coords))
            + (new_index_vars + promote_readd(promoted_names, displaced_index_coords, new_index_vars)))
    Ensures(Result().coord_names  # type: ignore
            == (coord_names0 - promote_dropped(promoted_names, displaced_index_coords))
            + (new_index_vars + promote_readd(promoted_names, displaced_index_coords, new_index_vars)))
    # The promotion produces a WELL-FORMED container: every coordinate still has
    # a stored array, and no coordinate is left index-backed without a live index.
    Ensures(well_formed(Result().variables, Result().coord_names,  # type: ignore
                        Result().indexes, Result().index_repr))
    # post-conditions-end
    # impl-start
    # drop_variables: names whose array is removed before the result is rebuilt
    # (the promoted names AND the displaced pre-existing index coordinates).
    drop_variables = promoted_names + displaced_index_coords
    # re-add deindexed coordinates AS PLAIN stored arrays: a displaced coordinate
    # that is neither promoted nor part of the new index is converted out of the
    # index-backed representation.
    readd = (drop_variables - new_index_vars) - promoted_names
    new_variables_all = new_index_vars + readd
    # index status after promotion: surviving old index coords (the displaced
    # ones lose their index), plus the new index's coordinates.
    indexes_out = (indexes0 - displaced_index_coords) + new_index_vars
    # index-backed representation: the converted (re-added) coords leave it.
    index_repr_out = (index_repr0 - readd) + new_index_vars
    variables_out = (variables0 - drop_variables) + new_variables_all
    coord_names_out = (coord_names0 - drop_variables) + new_variables_all
    return State(variables_out, coord_names_out, indexes_out, index_repr_out)
    # impl-end


def teardown_index(
        variables0: PSet[int], coord_names0: PSet[int], indexes0: PSet[int],
        index_repr0: PSet[int], new_index_vars: PSet[int],
        dropped_coords: PSet[int], converted_coords: PSet[int]) -> State:
    # pre-conditions-start
    # The input container is well-formed.
    Requires(well_formed(variables0, coord_names0, indexes0, index_repr0))
    # The names whose index is torn down are existing index coordinates. They
    # split into those whose array is DROPPED entirely and those whose array is
    # CONVERTED to a plain (non-index-backed) array; the two are disjoint.
    Requires(subset(dropped_coords, indexes0))
    Requires(subset(converted_coords, indexes0))
    Requires(disjoint(dropped_coords, converted_coords))
    # The freshly created replacement index coords (e.g. a reduced multi-index)
    # have stored arrays in the result and are neither dropped nor converted.
    Requires(disjoint(new_index_vars, dropped_coords))
    Requires(disjoint(new_index_vars, converted_coords))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
    Ensures(Acc(Result().indexes, 1 / 2) and Acc(Result().index_repr, 1 / 2))  # type: ignore
    # Exact resulting collections, pinned over the input collections, under the
    # three fates (dropped / converted / new replacement).
    # indexes and index_repr lose BOTH the dropped and the converted names (a
    # converted coordinate no longer carries an index nor an index-backed array),
    # then take in any replacement index coordinate.
    Ensures(Result().indexes  # type: ignore
            == ((indexes0 - dropped_coords) - converted_coords) + new_index_vars)
    Ensures(Result().index_repr  # type: ignore
            == ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars)
    # variables and coord_names lose ONLY the dropped names -- a converted
    # coordinate KEEPS its stored array and stays a coordinate -- then take in any
    # replacement index coordinate.
    Ensures(Result().variables  # type: ignore
            == (variables0 - dropped_coords) + new_index_vars)
    Ensures(Result().coord_names  # type: ignore
            == (coord_names0 - dropped_coords) + new_index_vars)
    # The teardown produces a WELL-FORMED container.
    Ensures(well_formed(Result().variables, Result().coord_names,  # type: ignore
                        Result().indexes, Result().index_repr))
    # post-conditions-end
    # impl-start
    # index status after teardown: surviving index coords are those neither
    # dropped nor converted, plus any freshly created replacement index.
    indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars
    # index-backed representation: dropped names lose their array; converted
    # names are re-stored as PLAIN arrays (leave the index-backed kind).
    index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars
    # variables: only the dropped names lose their stored array; converted names
    # keep theirs. Take in the replacement index coordinates.
    variables_out = (variables0 - dropped_coords) + new_index_vars
    # the coordinate set must DROP every name that lost its array, KEEP every
    # converted name, then take in any replacement index coordinate.
    coord_names_out = (coord_names0 - dropped_coords) + new_index_vars
    return State(variables_out, coord_names_out, indexes_out, index_repr_out)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT OF pydata__xarray-6992 nagini bundle (A-leg / model-correspondence focus).

SPEC SHAPE: model.py specifies two functions (promote_to_index = Dataset.set_index post-state recomputation; teardown_index = Dataset.reset_index). BOTH pin ALL FOUR output name-collections (variables/coord_names/indexes/index_repr) to EXACT set expressions over the inputs via Ensures ==, PLUS well_formed. No @ContractOnly axioms (meta.axioms==[]); the changed behaviour is modelled DEEPLY over PSet[int] and validated as an A-reference by axiom_check.py. Because every output is exactly pinned, there is no slack for a behaviorally-distinct verifying impl.

POSITIVE CONTROL: pos_control.py = gold model.py verbatim -> `adversary weakness` => CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (15.2s), exit 0. Confirms tooling+env sound.

8 DISTINCT SAME-SPEC WRONG IMPLS (only impl regions edited; same-spec exit 0 for all 8 confirmed byte-identical spec). Attack classes covered: teardown coord_names prepatch bug (atk_1: coord_names0+new_index_vars, no dropped subtraction -- the exact prepatch reproduction), converted-treated-as-dropped (atk_2, removes converted from variables/coord), leave-converted-index-backed (atk_3, index_repr keeps converted), converted-stays-in-indexes (atk_4), promote leave-displaced-index-backed (atk_5: the model_prepatch_2 A5 bug, index_repr=index_repr0+new), control-flow/ungrounded spurious re-add of converted into indexes (atk_6), promote partial re-add / boundary omit readd from variables (atk_7), promote keep displaced in indexes (atk_8).

RESULTS: `adversary weakness nagini pydata__xarray-6992 atk_N.py` => exit 2 (NOT-A-COUNTEREXAMPLE) for ALL 8. Direct `scripts/nagini_verify.sh` confirms each is a GENUINE postcondition violation (not timeout/tooling): atk_1 coord_names post @13.4s; atk_2 variables post @13.6s; atk_3 index_repr post @13.7s; atk_4 indexes post @14.1s; atk_5 promote index_repr post @13.8s; atk_6 indexes post @13.5s; atk_7 promote variables post @13.9s; atk_8 promote indexes post @13.7s. NO CANDIDATE emerged => no faithful patch to materialize/resolve (patches={}).

PREPATCH REPRODUCED: atk_1 = model_prepatch.py's teardown bug and atk_5 = model_prepatch_2.py's promote bug; both rejected -> the frozen spec senses both fixed behaviours (G-DIFF corroborated).

A-LEG / CORRESPONDENCE AUDIT: axiom_check.py's model_promote/model_teardown are a VERBATIM transcription of model.py's impl regions (identical difference/union operand order for all four collections). It derives the three teardown channels STRUCTURALLY from the real input/output (dropped=v_in-v_out; new_index_vars=i_out-i_in; converted=(i_in-i_out)-dropped-new_index_vars), asserts real result well-formed AND model==real on ALL FOUR collections for every F2P scenario -- no WF-only relaxation, no skip-guard. index_repr read via isinstance(v,IndexVariable) (direct structural read, no value proxy). meta gates: G-AX pass. refinement.md audit: no A-consumed rows (no axiom), all legs R / A-reference / I, no kind-3 (per §D); A-reference legs bind to real Dataset.set_index/reset_index correctly.

VERDICT: SOUND. 8 distinct same-spec wrong impls all genuinely fail to verify (specific pinned-collection postcondition each, ~13s, no timeouts); positive control verifies; prepatch bug reproduced+rejected; A-reference model correspondence holds. verify=>correct is not broken.

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
"""Twin-artifact model for pydata__xarray-6992.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A labelled-array container tracks four name collections over a common universe
  of name identifiers:

    * ``variables``    -- names that have a stored array;
    * ``coord_names``  -- the coordinate names (a subset of ``variables``);
    * ``indexes``      -- the coordinate names that currently carry an index;
    * ``index_repr``   -- the coordinate names whose stored array uses the
                          index-backed representation (the "kind" of the array).

  A WELL-FORMED container satisfies, simultaneously,

      indexes  is a subset of  coord_names  is a subset of  variables,

  AND its stored representation never gets ahead of index status:

      index_repr  is a subset of  indexes

  -- no coordinate is left in the index-backed representation once it no longer
  carries an index. (The number of plain data names is
  ``len(variables) - len(coord_names)``; a coordinate name lacking a stored
  array would drive that count negative, which a real container can never do.
  A coordinate left in the index-backed representation without a live index is
  the dangling state the repr code likewise cannot tolerate.)

  Two reshaping operations are specified; each returns the four name collections
  of a new container that must be well-formed:

  (1) Promoting one or more existing names to be the index of a dimension. Any
      pre-existing index whose coordinates are displaced by the promotion loses
      its index. A displaced coordinate that is neither promoted nor part of the
      new index, yet remains a coordinate, must be CONVERTED out of the
      index-backed representation (re-added as a plain stored array) so that it
      is still a coordinate with a stored array and is no longer counted as
      index-backed. The exact resulting collections are pinned below.

  (2) Tearing down the index of one or more dimensions/levels. Each affected
      name takes one of THREE fates, and the result is pinned exactly under all
      three:
        * a DROPPED name loses its stored array entirely -- it leaves all four
          collections (it must be removed from the coordinate set too, so the
          result never names a coordinate that has no stored array);
        * a CONVERTED name keeps its stored array as a PLAIN array -- it stays a
          variable and a coordinate but is removed from the indexes and from the
          index-backed representation (converted out of the index-backed kind);
        * a freshly created REPLACEMENT index coordinate is added to all four
          collections.
      The exact resulting collections are pinned below over these three channels.

The four name collections are modelled as ``PSet[int]`` of integer name
identifiers (the only operations on names are set membership / union /
difference / equality, never any character-level operation). Each result is
returned as a ``State`` record of the four collections; the postconditions pin
every collection to an exact set expression OVER THE INPUT COLLECTIONS (so the
result must be PRODUCED by the modelled set algebra, not merely happen to be
well-formed) and additionally assert well-formedness.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class State:
    """The four name collections of a container (immutable record)."""

    def __init__(self, variables: PSet[int], coord_names: PSet[int],
                 indexes: PSet[int], index_repr: PSet[int]) -> None:
        Ensures(Acc(self.variables) and Acc(self.coord_names))  # type: ignore
        Ensures(Acc(self.indexes) and Acc(self.index_repr))  # type: ignore
        Ensures(self.variables is variables and self.coord_names is coord_names)  # type: ignore
        Ensures(self.indexes is indexes and self.index_repr is index_repr)  # type: ignore
        self.variables = variables  # type: ignore
        self.coord_names = coord_names  # type: ignore
        self.indexes = indexes  # type: ignore
        self.index_repr = index_repr  # type: ignore


# axioms-start
# (No axiomatized callees. The whole behaviour is the well-formedness-preserving
# recomputation of four name collections under set union / difference, modelled
# DEEPLY over PSet[int]. The set primitives are unchanged operations refined to
# PSet membership, not axioms the proof consumes -- see refinement.md /
# mapping.md.)
# axioms-end


# pure-start
@Pure
def subset(a: PSet[int], b: PSet[int]) -> bool:
    """Every member of ``a`` is a member of ``b``."""
    return Forall(int, lambda x: Implies(x in a, x in b))


@Pure
def disjoint(a: PSet[int], b: PSet[int]) -> bool:
    """``a`` and ``b`` share no member."""
    return Forall(int, lambda x: Implies(x in a, not (x in b)))


@Pure
def well_formed(variables: PSet[int], coord_names: PSet[int],
                indexes: PSet[int], index_repr: PSet[int]) -> bool:
    """A container is well-formed when its index names are coordinates, its
    coordinate names all have a stored array, and no coordinate is left in the
    index-backed representation once it no longer carries an index."""
    return (subset(indexes, coord_names)
            and subset(coord_names, variables)
            and subset(index_repr, indexes))


@Pure
def promote_dropped(promoted: PSet[int], displaced: PSet[int]) -> PSet[int]:
    """Names whose array is removed before the promotion result is rebuilt: the
    promoted names together with the displaced pre-existing index coordinates."""
    return promoted + displaced


@Pure
def promote_readd(promoted: PSet[int], displaced: PSet[int],
                  new_index_vars: PSet[int]) -> PSet[int]:
    """The displaced coordinates converted out of the index-backed
    representation: those dropped, that are neither part of the new index nor
    themselves being promoted."""
    return (promote_dropped(promoted, displaced) - new_index_vars) - promoted
# pure-end


def promote_to_index(
        variables0: PSet[int], coord_names0: PSet[int], indexes0: PSet[int],
        index_repr0: PSet[int], new_index_vars: PSet[int],
        promoted_names: PSet[int], displaced_index_coords: PSet[int]) -> State:
    # pre-conditions-start
    # The input container is well-formed.
    Requires(well_formed(variables0, coord_names0, indexes0, index_repr0))
    # The promoted names come from the input container (they have stored arrays)
    # and they all become coordinates of the new index.
    Requires(subset(promoted_names, variables0))
    Requires(subset(promoted_names, new_index_vars))
    # The displaced pre-existing index coordinates are existing index names.
    Requires(subset(displaced_index_coords, indexes0))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
    Ensures(Acc(Result().indexes, 1 / 2) and Acc(Result().index_repr, 1 / 2))  # type: ignore
    # Exact resulting collections, pinned over the input collections.
    Ensures(Result().indexes  # type: ignore
            == (indexes0 - displaced_index_coords) + new_index_vars)
    Ensures(Result().index_repr  # type: ignore
            == (index_repr0 - promote_readd(promoted_names, displaced_index_coords, new_index_vars))
            + new_index_vars)
    Ensures(Result().variables  # type: ignore
            == (variables0 - promote_dropped(promoted_names, displaced_index_coords))
            + (new_index_vars + promote_readd(promoted_names, displaced_index_coords, new_index_vars)))
    Ensures(Result().coord_names  # type: ignore
            == (coord_names0 - promote_dropped(promoted_names, displaced_index_coords))
            + (new_index_vars + promote_readd(promoted_names, displaced_index_coords, new_index_vars)))
    # The promotion produces a WELL-FORMED container: every coordinate still has
    # a stored array, and no coordinate is left index-backed without a live index.
    Ensures(well_formed(Result().variables, Result().coord_names,  # type: ignore
                        Result().indexes, Result().index_repr))
    # post-conditions-end
    # impl-start
    # drop_variables: names whose array is removed before the result is rebuilt
    # (the promoted names AND the displaced pre-existing index coordinates).
    drop_variables = promoted_names + displaced_index_coords
    # re-add deindexed coordinates AS PLAIN stored arrays: a displaced coordinate
    # that is neither promoted nor part of the new index is converted out of the
    # index-backed representation.
    readd = (drop_variables - new_index_vars) - promoted_names
    new_variables_all = new_index_vars + readd
    # index status after promotion: surviving old index coords (the displaced
    # ones lose their index), plus the new index's coordinates.
    indexes_out = (indexes0 - displaced_index_coords) + new_index_vars
    # index-backed representation: the converted (re-added) coords leave it.
    index_repr_out = (index_repr0 - readd) + new_index_vars
    variables_out = (variables0 - drop_variables) + new_variables_all
    coord_names_out = (coord_names0 - drop_variables) + new_variables_all
    return State(variables_out, coord_names_out, indexes_out, index_repr_out)
    # impl-end


def teardown_index(
        variables0: PSet[int], coord_names0: PSet[int], indexes0: PSet[int],
        index_repr0: PSet[int], new_index_vars: PSet[int],
        dropped_coords: PSet[int], converted_coords: PSet[int]) -> State:
    # pre-conditions-start
    # The input container is well-formed.
    Requires(well_formed(variables0, coord_names0, indexes0, index_repr0))
    # The names whose index is torn down are existing index coordinates. They
    # split into those whose array is DROPPED entirely and those whose array is
    # CONVERTED to a plain (non-index-backed) array; the two are disjoint.
    Requires(subset(dropped_coords, indexes0))
    Requires(subset(converted_coords, indexes0))
    Requires(disjoint(dropped_coords, converted_coords))
    # The freshly created replacement index coords (e.g. a reduced multi-index)
    # have stored arrays in the result and are neither dropped nor converted.
    Requires(disjoint(new_index_vars, dropped_coords))
    Requires(disjoint(new_index_vars, converted_coords))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().variables, 1 / 2) and Acc(Result().coord_names, 1 / 2))  # type: ignore
    Ensures(Acc(Result().indexes, 1 / 2) and Acc(Result().index_repr, 1 / 2))  # type: ignore
    # Exact resulting collections, pinned over the input collections, under the
    # three fates (dropped / converted / new replacement).
    # indexes and index_repr lose BOTH the dropped and the converted names (a
    # converted coordinate no longer carries an index nor an index-backed array),
    # then take in any replacement index coordinate.
    Ensures(Result().indexes  # type: ignore
            == ((indexes0 - dropped_coords) - converted_coords) + new_index_vars)
    Ensures(Result().index_repr  # type: ignore
            == ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars)
    # variables and coord_names lose ONLY the dropped names -- a converted
    # coordinate KEEPS its stored array and stays a coordinate -- then take in any
    # replacement index coordinate.
    Ensures(Result().variables  # type: ignore
            == (variables0 - dropped_coords) + new_index_vars)
    Ensures(Result().coord_names  # type: ignore
            == (coord_names0 - dropped_coords) + new_index_vars)
    # The teardown produces a WELL-FORMED container.
    Ensures(well_formed(Result().variables, Result().coord_names,  # type: ignore
                        Result().indexes, Result().index_repr))
    # post-conditions-end
    # impl-start
    # index status after teardown: surviving index coords are those neither
    # dropped nor converted, plus any freshly created replacement index.
    indexes_out = ((indexes0 - dropped_coords) - converted_coords) + new_index_vars
    # index-backed representation: dropped names lose their array; converted
    # names are re-stored as PLAIN arrays (leave the index-backed kind).
    index_repr_out = ((index_repr0 - dropped_coords) - converted_coords) + new_index_vars
    # variables: only the dropped names lose their stored array; converted names
    # keep theirs. Take in the replacement index coordinates.
    variables_out = (variables0 - dropped_coords) + new_index_vars
    # the coordinate set must DROP every name that lost its array, KEEP every
    # converted name, then take in any replacement index coordinate.
    coord_names_out = (coord_names0 - dropped_coords) + new_index_vars
    return State(variables_out, coord_names_out, indexes_out, index_repr_out)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT OF pydata__xarray-6992 nagini bundle (A-leg / model-correspondence focus).

SPEC SHAPE: model.py specifies two functions (promote_to_index = Dataset.set_index post-state recomputation; teardown_index = Dataset.reset_index). BOTH pin ALL FOUR output name-collections (variables/coord_names/indexes/index_repr) to EXACT set expressions over the inputs via Ensures ==, PLUS well_formed. No @ContractOnly axioms (meta.axioms==[]); the changed behaviour is modelled DEEPLY over PSet[int] and validated as an A-reference by axiom_check.py. Because every output is exactly pinned, there is no slack for a behaviorally-distinct verifying impl.

POSITIVE CONTROL: pos_control.py = gold model.py verbatim -> `adversary weakness` => CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (15.2s), exit 0. Confirms tooling+env sound.

8 DISTINCT SAME-SPEC WRONG IMPLS (only impl regions edited; same-spec exit 0 for all 8 confirmed byte-identical spec). Attack classes covered: teardown coord_names prepatch bug (atk_1: coord_names0+new_index_vars, no dropped subtraction -- the exact prepatch reproduction), converted-treated-as-dropped (atk_2, removes converted from variables/coord), leave-converted-index-backed (atk_3, index_repr keeps converted), converted-stays-in-indexes (atk_4), promote leave-displaced-index-backed (atk_5: the model_prepatch_2 A5 bug, index_repr=index_repr0+new), control-flow/ungrounded spurious re-add of converted into indexes (atk_6), promote partial re-add / boundary omit readd from variables (atk_7), promote keep displaced in indexes (atk_8).

RESULTS: `adversary weakness nagini pydata__xarray-6992 atk_N.py` => exit 2 (NOT-A-COUNTEREXAMPLE) for ALL 8. Direct `scripts/nagini_verify.sh` confirms each is a GENUINE postcondition violation (not timeout/tooling): atk_1 coord_names post @13.4s; atk_2 variables post @13.6s; atk_3 index_repr post @13.7s; atk_4 indexes post @14.1s; atk_5 promote index_repr post @13.8s; atk_6 indexes post @13.5s; atk_7 promote variables post @13.9s; atk_8 promote indexes post @13.7s. NO CANDIDATE emerged => no faithful patch to materialize/resolve (patches={}).

PREPATCH REPRODUCED: atk_1 = model_prepatch.py's teardown bug and atk_5 = model_prepatch_2.py's promote bug; both rejected -> the frozen spec senses both fixed behaviours (G-DIFF corroborated).

A-LEG / CORRESPONDENCE AUDIT: axiom_check.py's model_promote/model_teardown are a VERBATIM transcription of model.py's impl regions (identical difference/union operand order for all four collections). It derives the three teardown channels STRUCTURALLY from the real input/output (dropped=v_in-v_out; new_index_vars=i_out-i_in; converted=(i_in-i_out)-dropped-new_index_vars), asserts real result well-formed AND model==real on ALL FOUR collections for every F2P scenario -- no WF-only relaxation, no skip-guard. index_repr read via isinstance(v,IndexVariable) (direct structural read, no value proxy). meta gates: G-AX pass. refinement.md audit: no A-consumed rows (no axiom), all legs R / A-reference / I, no kind-3 (per §D); A-reference legs bind to real Dataset.set_index/reset_index correctly.

VERDICT: SOUND. 8 distinct same-spec wrong impls all genuinely fail to verify (specific pinned-collection postcondition each, ~13s, no timeouts); positive control verifies; prepatch bug reproduced+rejected; A-reference model correspondence holds. verify=>correct is not broken.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pydata__xarray-6992 nagini bundle. Spec region confirmed byte-identical (same-spec exit 0 on the identity model). Model verifies non-vacuously (Nagini: Verification successful, 14.3s).

Model-vs-real-callee fuzzing at base_commit 45c0a114 (worktree): I transcribed the impl-region set algebra of promote_to_index and teardown_index and compared it against the REAL Dataset.set_index / Dataset.reset_index, deriving the model input channels structurally exactly as axiom_check.py does (promoted/displaced for set_index; dropped=v0-v1, new_index_vars=i1-i0, converted=(i0-i1)-dropped-new for reset_index). Across 772 in-domain cases (73 structured + 699 randomized: single-dim indexes, pandas MultiIndex of 2-3 levels, append=True/False, drop=True/False, multi-name promotion, drop/convert/rename mixes) I found ZERO divergences on all four name collections (variables, coord_names, indexes, index_repr). This corroborates G-CONF (100001 inputs, 0 disagreements) and G-AX (12 F2P scenarios exact).

Spec-too-strong probe: the only precondition failures observed (90) are the family set_index(x=[data_var]) where the target dim ALREADY exists as a dimension/coordinate name. There the real code renames the promoted variable to the existing dimension name, so promoted_names={d0} but the resulting index coord is {x} -> violates Requires(subset(promoted_names, new_index_vars)). This is OUTSIDE the modeled domain, not a within-domain disagreement: mapping.md explicitly states idx_vars is always a superset of the promoted names, which holds for promotion to a fresh dimension (the bug's scenario). Every FAIL_TO_PASS scenario satisfies the preconditions and the model matches the real callee exactly. All real inputs and results were well-formed (0 WF failures), so the well_formed postcondition is faithful to the DataVariables.__len__ invariant.

Conclusion: the modeled functions agree with the real repo callees on every input inside their precondition domain; no diverging input exists where the spec contradicts real behavior. The precondition scoping is an honest domain restriction (spec neither too strong to exclude F2P behavior nor drifting from the repo), so FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rendered the consumer spec view via markers.spec_view (nagini backend): both impl regions correctly collapse to '... # implementation elided', leaving only docstring + class State + pure region (subset/disjoint/well_formed/promote_dropped/promote_readd) + the two function signatures with pre/post-conditions. The entire view is abstract PSet[int] set-algebra over four name collections (variables, coord_names, indexes, index_repr). Mechanical screen leakage.screen() -> PASSED=True, zero hard failures. Distinctive patched symbols are {set_index, reset_index, keep_levels, drop_or_convert}; none appear in spec-view identifiers or comments (all carriers are renamed abstractions: promote_to_index/teardown_index/promoted_names/displaced_index_coords/new_index_vars). No diff markers, no patched file paths (xarray/core/dataset.py, indexes.py), no fix/bug/regression narration. Comments state desired behavior (DROPPED/CONVERTED/REPLACEMENT fates, the invariant indexes<=coord_names<=variables and index_repr<=indexes) rather than the gold edit. The public problem_statement already discloses more concrete edit-localizing info (names DataVariables, _coord_names, _variables, set_index, reset_index, __len__ line 368, and the ValueError). Not a relaxed bundle (relaxed_leakage=None, no RELAXED_LEAKAGE.md), so no G-PANEL-3 deferral needed. The spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
