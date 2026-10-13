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
from nagini_contracts.obligations import MustTerminate


class State:
    """The four name collections of a container (immutable record)."""

    def __init__(self, variables: PSet[int], coord_names: PSet[int],
                 indexes: PSet[int], index_repr: PSet[int]) -> None:
        Requires(MustTerminate(1))
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
    Requires(MustTerminate(6))
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
    Requires(MustTerminate(10))
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
    # PRE-PATCH BUG: the coordinate set is rebuilt by unioning the replacement
    # index onto the ORIGINAL coordinate names without removing the names whose
    # stored array was just dropped, so a torn-down coordinate is named with no
    # stored array (coord_names_out is no longer a subset of variables_out).
    coord_names_out = coord_names0 + new_index_vars
    return State(variables_out, coord_names_out, indexes_out, index_repr_out)
    # impl-end
