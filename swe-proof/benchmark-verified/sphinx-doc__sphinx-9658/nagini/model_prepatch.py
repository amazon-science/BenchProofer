"""Twin-artifact model for sphinx-doc__sphinx-9658.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A placeholder object that stands in for an attribute reached through a
  stand-in package carries two derived identifiers used by the documentation
  renderer:

    * the placeholder's SHORT identifier, which is the very attribute name it
      was reached by (e.g. the attribute reached as ``Class`` has short
      identifier ``Class``); and
    * the placeholder's DISPLAY identifier (its qualified name), which the
      renderer reads to compose a cross-reference.

  The required behaviour is that the display identifier of such a placeholder is
  its short identifier — i.e. the attribute name — NOT an empty string. The
  renderer composes the fully-qualified reference by joining the owning module
  path and the display identifier with a dot. Consequently, for a placeholder
  reached by a non-empty attribute name, the rendered reference ends in that
  attribute name (``<module>.<name>``) and never degenerates to a dangling
  ``<module>.`` with the trailing component dropped.

Identifiers are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried over ``PSeq[int]`` via
``ToSeq``. The renderer's dotted join is an unchanged operation, spelled out
deeply as the pure function ``render_qualified`` (a structural concatenation),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def dot() -> PSeq[int]:
    """The single-code-point separator ``.`` (U+002E)."""
    return PSeq(46)


@Pure
def render_qualified(module: PSeq[int], display: PSeq[int]) -> PSeq[int]:
    """The renderer's dotted join: the owning module path, a dot, then the
    placeholder's display identifier. This is the unchanged consuming operation
    (the documentation renderer reading the module path and the display
    identifier), spelled out structurally rather than axiomatized."""
    return module + dot() + display
# pure-end


def subclass_short_name(name: List[int]) -> List[int]:
    # pre-conditions-start
    # The attribute name by which the placeholder was reached (read-only).
    Requires(Acc(list_pred(name), 1 / 2))
    # The short identifier must actually be delivered: this termination
    # obligation forbids satisfying the value clause vacuously by never
    # returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The placeholder's SHORT identifier is exactly the attribute name it was
    # reached by.
    Ensures(ToSeq(Result()) == ToSeq(name))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(name):
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(name))
        Invariant(ToSeq(result) == ToSeq(name).take(i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(name) - i.
        Invariant(MustTerminate(len(name) - i))
        # invariants-end
        Assert(ToSeq(name).take(i + 1).drop(i) == PSeq(name[i]))
        result = result + [name[i]]
        i = i + 1
    Assert(ToSeq(name).take(len(name)) == ToSeq(name))
    return result
    # impl-end


def placeholder_display_name(short_name: List[int]) -> List[int]:
    # pre-conditions-start
    # The placeholder's short identifier (its attribute name); read-only.
    Requires(Acc(list_pred(short_name), 1 / 2))
    # The display identifier must actually be delivered: this termination
    # obligation forbids satisfying the value clause vacuously by never
    # returning.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(short_name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The placeholder's DISPLAY identifier (the qualified name the renderer
    # reads) is its short identifier -- the attribute name -- not an empty
    # string.
    Ensures(ToSeq(Result()) == ToSeq(short_name))
    # post-conditions-end
    # impl-start
    # PRE-PATCH: the display identifier was hard-set to the empty string,
    # ignoring the short identifier entirely.
    result = []  # type: List[int]
    return result
    # impl-end


def qualified_reference(name: List[int], module: List[int]) -> List[int]:
    # pre-conditions-start
    # `name`   : the attribute name by which the placeholder was reached.
    # `module` : the owning module path the placeholder belongs to.
    # Both read-only.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(module), 1 / 2))
    # The rendered reference must actually be delivered in finite time; the
    # measure leaves room to invoke the two identifier helpers (each of which
    # carries a smaller obligation).
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendered fully-qualified reference is the module path, a dot, and the
    # attribute name -- the trailing component is the attribute name itself, so
    # for a non-empty name the reference never degenerates to a dangling
    # `<module>.`.
    Ensures(ToSeq(Result()) == render_qualified(ToSeq(module), ToSeq(name)))
    Ensures(ToSeq(Result()) == ToSeq(module) + dot() + ToSeq(name))
    Ensures(Implies(len(name) > 0, len(Result()) > len(module) + 1))
    # post-conditions-end
    # impl-start
    short = subclass_short_name(name)
    display = placeholder_display_name(short)
    result = []  # type: List[int]
    i = 0
    while i < len(module):
        # invariants-start
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(display)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(module))
        Invariant(ToSeq(display) == ToSeq(name))
        Invariant(ToSeq(result) == ToSeq(module).take(i))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(module) - i.
        Invariant(MustTerminate(len(module) - i))
        # invariants-end
        Assert(ToSeq(module).take(i + 1).drop(i) == PSeq(module[i]))
        result = result + [module[i]]
        i = i + 1
    Assert(ToSeq(module).take(len(module)) == ToSeq(module))
    result = result + [46]
    result = result + display
    return result
    # impl-end
