"""Twin-artifact model for pydata__xarray-7229.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A conditional-selection routine combines a condition with two data
  arguments. Asked to keep the attributes of its SECOND positional argument, it
  gives the output an attribute mapping at EACH level of the output's own
  structure -- a whole-object (top-level) mapping, one mapping per labelled
  coordinate, one mapping per named sub-variable -- and each of those mappings
  is the mapping the second argument carries at the CORRESPONDING level of its
  own structure, level by level and name by name:

    * the mapping of an output coordinate is the second argument's own mapping
      AT that coordinate's name;

    * the mapping of an output sub-variable is the second argument's own
      mapping AT that sub-variable's name;

    * the output's top-level mapping is the second argument's own whole-object
      mapping, when that is the mapping corresponding to the output's top
      level.

  "The second argument's own mapping AT A NAME" means: look that name up on the
  second argument itself, as a whole object -- not in a list of the levels it
  carries -- and take the mapping of whatever comes back. Ordinarily what comes
  back is the level of that name, and a name the second argument yields nothing
  for, or yields something carrying no mapping of its own for, contributes the
  empty mapping. A name it yields a DERIVED VIEW OF ITSELF for, however,
  contributes that view's mapping, which is the second argument's own
  whole-object mapping and is therefore NOT empty even though the second
  argument carries no coordinate and no sub-variable of that name. Such names
  exist, and those inputs are inside the behaviour specified here rather than
  excluded from it.

  Which names get asked about is itself part of the behaviour, and it differs
  between the two ways the second argument can relate to the output. The
  output's COORDINATE names are always asked about. The output's SUB-VARIABLE
  names are asked about only when the second argument's own whole-object mapping
  is the one corresponding to the output's top level; in the other case,
  described below, the second argument reaches a sub-variable of the output
  through its own NAME alone, and no name-to-mapping question is put to it at
  the sub-variable level at all.

  The behaviour above is specified for calls in which every name-to-mapping
  question that IS put is ANSWERED. Looking a name up on the second argument as
  a whole object is an interrogation that can, for some combinations of a name
  and a second argument, decline to answer at all -- neither naming a level, nor
  yielding a derived view, nor falling back to the empty mapping, but abandoning
  the call outright. A name that behaves that way on the second argument at hand
  puts the call OUTSIDE the behaviour specified here, PROVIDED the name is one
  the routine actually asks about: nothing is claimed about such a call, in
  particular not that a result is produced. A name that would decline if asked,
  but which the routine does not ask about at that level, excludes nothing --
  those calls remain inside the specified behaviour and every mapping above
  holds of them. Whether a given name answers is a property of the pair, not of
  the name alone -- the same name can answer for one second argument and decline
  for another whose contents are of a different sort.

  Likewise, the routine has to obtain the output's ROSTER of named
  sub-variables in order to visit them, and it obtains that roster by the same
  kind of whole-object interrogation of the OUTPUT, under the roster's own
  name, at a point where the output already carries the second argument's
  whole-object mapping. An output that is not of a sort keeping such a roster
  natively will answer that interrogation out of the mapping it now carries --
  so a second argument whose whole-object mapping happens to record an entry
  under the roster's own name can cause a bogus roster to be visited in place of
  the real one. The behaviour above is specified only for calls in which the
  roster is obtained AS a roster: an answer that can be walked, each of whose
  entries names a sub-variable the output actually carries. Calls in which the
  substituted answer cannot be walked, or names something the output does not
  carry, are outside the behaviour specified here, and again nothing is claimed
  about them -- in particular not that a result is produced. Where the
  substituted answer IS a walkable roster of names the output does carry, the
  call is inside the specified behaviour and every mapping above is as stated.

  All of the above presupposes that the three arguments COMBINE into an output
  carrying attribute levels at all. Whether they combine, and what shape the
  combination has, is settled before any attribute is carried over: it is the
  same question the routine answers when asked to keep NO attributes at all.
  Arguments that do not combine at that stage, or that combine into something
  holding no attribute mapping of any kind, leave no output whose levels the
  paragraphs above could speak of, and the behaviour specified here does not
  reach them either.

  The second argument need not be structured like the output:
  when the output carries a level of named sub-variables that the second
  argument does not, the mapping corresponding to the second argument's own
  whole-object mapping is that of the output sub-variable carrying its name,
  nothing of the second argument corresponds to the output's top level, and the
  output's top-level mapping is therefore the empty one. (The output's
  remaining sub-variables correspond to no level of the second argument at all;
  the contract below makes no claim about them.)

  On the calls the two paragraphs above leave inside the specified behaviour,
  this rebuilding is a TOTAL operation: for every such admissible input it runs
  to completion and hands back the output object described above. The attribute
  mappings above are therefore promised of EVERY such run, not merely of those
  runs that happen to reach a result -- a routine that walks its levels forever,
  never delivering an output, does not exhibit the behaviour above. Totality is
  a promise about that domain and is not a claim that a result exists for the
  interrogations described above as unanswered or as answered with a bogus
  roster; those calls are not admissible inputs and the promise does not reach
  them.

Attribute mappings are modelled as opaque integer identities (distinct mappings
have distinct identities; the empty mapping is the identity 0). The second
argument is read-only and is described by `x_attrs` (the identity of its own
whole-object mapping), `x_coord_attrs` (the identities of its mappings at the
output's coordinate names, in coordinate order, aligned positionally with the
output's coordinates) and `x_var_attrs` (the identities of its mappings at the
output's sub-variable names, aligned positionally with the output's
sub-variables) -- "its mapping at a name" in the sense given above, so a name it
yields nothing for contributes 0, while a name it yields a derived view of
itself for contributes `x_attrs` rather than 0. Only the LENGTH of
`x_var_attrs` carries information in the case where the second argument reaches
a sub-variable through its own name: no name-to-mapping question is put at that
level there, so what its entries hold is immaterial and the contract below reads
none of them. These carriers exist only for calls inside the domain described
above: a name that IS asked about and whose interrogation of the second argument
is declined has NO identity to contribute, so it is not that it contributes 0 --
there is no such call to describe, and the carriers below say nothing about it.
Equally, the sub-variable carriers are aligned against the output's REAL roster
of sub-variables, which presupposes that the roster was obtained as a roster; a
call in which a bogus roster was visited instead has no image among these
carriers at all. The
boolean `top_unmatched` records how the two structures relate: False when the
second argument's own whole-object mapping is the one corresponding to the
output's top level, True when the output carries a level of named sub-variables
that the second argument does not -- and then `named_slot` is the index of the
output sub-variable carrying the second argument's name (or -1 when the output
has no sub-variable of that name). The output is a freshly built object owning its own
`attrs` (top level), `coord_attrs` (per coordinate) and `var_attrs` (per
sub-variable) storage.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees: the behaviour under specification -- each level of
#  the output taking the mapping of the corresponding level of the source -- is
#  modelled deeply, not behind an axiom.)
# axioms-end


# pure-start
# (No pure helpers needed.)
# pure-end


class WhereResult:
    """The output of the conditional selection. The studied behaviour touches
    only its attribute mappings: `attrs` is the whole-object (top-level)
    mapping identity; `coord_attrs[i]` is the mapping identity of the i-th
    coordinate; `var_attrs[i]` is the mapping identity of the i-th
    sub-variable."""

    def __init__(self, attrs: int, coord_attrs: List[int],
                 var_attrs: List[int]) -> None:
        # pre-conditions-start
        Requires(Acc(list_pred(coord_attrs)))
        Requires(Acc(list_pred(var_attrs)))
        # Building the output object is itself a terminating step, so the
        # promises below are promises about every run of it.
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.attrs))
        Ensures(Acc(self.coord_attrs))
        Ensures(Acc(self.var_attrs))
        Ensures(Acc(list_pred(self.coord_attrs)))
        Ensures(Acc(list_pred(self.var_attrs)))
        Ensures(self.attrs == attrs)
        Ensures(self.coord_attrs is coord_attrs)
        Ensures(self.var_attrs is var_attrs)
        Ensures(ToSeq(self.coord_attrs) == Old(ToSeq(coord_attrs)))
        Ensures(ToSeq(self.var_attrs) == Old(ToSeq(var_attrs)))
        # post-conditions-end
        # impl-start
        self.attrs = attrs  # type: int
        self.coord_attrs = coord_attrs  # type: List[int]
        self.var_attrs = var_attrs  # type: List[int]
        # impl-end


def rebuild_attrs(x_attrs: int, x_coord_attrs: List[int],
                  x_var_attrs: List[int], top_unmatched: bool,
                  named_slot: int) -> WhereResult:
    # pre-conditions-start
    # The source (second argument) is read-only: it survives unchanged.
    Requires(Acc(list_pred(x_coord_attrs), 1 / 2))
    Requires(Acc(list_pred(x_var_attrs), 1 / 2))
    # When the output carries a level of named sub-variables the source does
    # not, `named_slot` is the in-range output sub-variable slot carrying the
    # source's name, or -1 when the output has no sub-variable of that name.
    Requires(Implies(top_unmatched, -1 <= named_slot and
                     named_slot < len(x_var_attrs)))
    # The rebuild is TOTAL: it runs to completion on every admissible input, so
    # the attribute mappings promised below are promised of every run rather than
    # only of runs that reach a result. The level sits strictly above the level
    # of building the output object, leaving room for intermediate helpers.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(x_coord_attrs), 1 / 2))
    Ensures(Acc(list_pred(x_var_attrs), 1 / 2))
    Ensures(ToSeq(x_coord_attrs) == Old(ToSeq(x_coord_attrs)))
    Ensures(ToSeq(x_var_attrs) == Old(ToSeq(x_var_attrs)))
    # The output is a freshly built object owning its own attribute storage.
    Ensures(Acc(Result().attrs))
    Ensures(Acc(Result().coord_attrs))
    Ensures(Acc(Result().var_attrs))
    Ensures(Acc(list_pred(Result().coord_attrs)))
    Ensures(Acc(list_pred(Result().var_attrs)))
    # top-level mapping: the source's own whole-object mapping when that is the
    # mapping corresponding to the output's top level; the empty mapping
    # (identity 0) when the source's whole-object mapping corresponds to an
    # output sub-variable instead, so nothing of the source corresponds to the
    # output's top level.
    Ensures(Implies(not top_unmatched, Result().attrs == x_attrs))
    Ensures(Implies(top_unmatched, Result().attrs == 0))
    # coordinate mappings (in every case): exactly one output coordinate slot
    # per source coordinate slot, and each output coordinate slot is the
    # SAME-INDEX source coordinate slot -- the source's own mapping for the
    # coordinate of that name.
    Ensures(len(Result().coord_attrs) == len(x_coord_attrs))
    Ensures(Forall(int, lambda k: (
        Implies(0 <= k and k < len(x_coord_attrs),
                Result().coord_attrs[k] == x_coord_attrs[k]),
        [[Result().coord_attrs[k]]])))
    # sub-variable mappings
    Ensures(len(Result().var_attrs) == len(x_var_attrs))
    # Each output sub-variable slot is the SAME-INDEX source sub-variable slot
    # -- the source's own mapping for the sub-variable of that name.
    Ensures(Implies(not top_unmatched, Forall(int, lambda k: (
        Implies(0 <= k and k < len(x_var_attrs),
                Result().var_attrs[k] == x_var_attrs[k]),
        [[Result().var_attrs[k]]]))))
    # When the source's own whole-object mapping corresponds to a sub-variable
    # of the output, it is the mapping of the slot carrying the source's name.
    # (With no such slot `named_slot == -1` and this rule governs nothing;
    # the contract makes no claim about the output's other sub-variable slots.)
    Ensures(Implies(top_unmatched and 0 <= named_slot,
                    Result().var_attrs[named_slot] == x_attrs))
    # post-conditions-end
    # impl-start
    coord_src = ToSeq(x_coord_attrs)  # type: PSeq[int]
    var_src = ToSeq(x_var_attrs)  # type: PSeq[int]
    # always fill coord attrs from the SAME source coordinate (every case)
    out_coords = []  # type: List[int]
    i = 0
    while i < len(x_coord_attrs):
        # invariants-start
        Invariant(Acc(list_pred(x_coord_attrs), 1 / 4))
        Invariant(Acc(list_pred(out_coords)))
        Invariant(ToSeq(x_coord_attrs) == coord_src)
        Invariant(0 <= i and i <= len(coord_src))
        Invariant(len(out_coords) == i)
        Invariant(ToSeq(out_coords) == coord_src.take(i))
        Invariant(Forall(int, lambda k: (
            Implies(0 <= k and k < i,
                    out_coords[k] == x_coord_attrs[k]),
            [[out_coords[k]]])))
        Invariant(MustTerminate(len(x_coord_attrs) - i + 1))
        # invariants-end
        out_coords.append(x_coord_attrs[i])
        i = i + 1
    Assert(coord_src.take(len(coord_src)) == coord_src)
    # fill sub-variable attrs per case (two cases, two loops -- each loop
    # carries a single per-element rule so the Forall trigger stays simple)
    out_vars = []  # type: List[int]
    if not top_unmatched:
        # each output sub-variable slot is the SAME-INDEX source sub-variable
        # slot.
        j = 0
        while j < len(x_var_attrs):
            # invariants-start
            Invariant(Acc(list_pred(x_var_attrs), 1 / 4))
            Invariant(Acc(list_pred(out_vars)))
            Invariant(ToSeq(x_var_attrs) == var_src)
            Invariant(0 <= j and j <= len(var_src))
            Invariant(len(out_vars) == j)
            Invariant(ToSeq(out_vars) == var_src.take(j))
            Invariant(Forall(int, lambda k: (
                Implies(0 <= k and k < j, out_vars[k] == x_var_attrs[k]),
                [[out_vars[k]]])))
            Invariant(MustTerminate(len(x_var_attrs) - j + 1))
            # invariants-end
            out_vars.append(x_var_attrs[j])
            j = j + 1
        Assert(var_src.take(len(var_src)) == var_src)
    else:
        # the sub-variable bearing the source's name takes the source's
        # WHOLE-OBJECT mapping; the other slots are left as the upstream
        # computation produced them (modelled here as the empty mapping -- the
        # contract makes no claim about them).
        j = 0
        while j < len(x_var_attrs):
            # invariants-start
            Invariant(Acc(list_pred(x_var_attrs), 1 / 4))
            Invariant(Acc(list_pred(out_vars)))
            Invariant(ToSeq(x_var_attrs) == var_src)
            Invariant(-1 <= named_slot and named_slot < len(var_src))
            Invariant(0 <= j and j <= len(var_src))
            Invariant(len(out_vars) == j)
            # the matching slot, once written, holds the source's top-level map
            Invariant(Implies(0 <= named_slot and named_slot < j,
                              out_vars[named_slot] == x_attrs))
            Invariant(MustTerminate(len(x_var_attrs) - j + 1))
            # invariants-end
            if j == named_slot:
                out_vars.append(x_attrs)
            else:
                out_vars.append(0)
            Assert(out_vars[j] == (x_attrs if j == named_slot else 0))
            j = j + 1
    if top_unmatched:
        top = 0
    else:
        top = x_attrs
    return WhereResult(top, out_coords, out_vars)
    # impl-end
