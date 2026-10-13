"""Twin-artifact model for django__django-14311.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a development process was launched by interpreting a module via the
  interpreter's module-execution mechanism, the relaunch command must name the
  SAME module that was originally run.  The launched unit is characterised by
  two code-point strings:

    * its fully-qualified import name ``name`` (e.g. ``pkg.sub.tool``);
    * its enclosing package name ``parent`` (e.g. ``pkg.sub``), empty when the
      unit is top level.

  Whether a qualified ``name`` denotes a package executed through its entry
  file (rather than a directly-named module) is decided by an opaque
  classifier ``marks_entry`` -- the module-execution machinery's own
  classification, modelled as an unchanged callee (axioms region).

  The module-name argument to reproduce is:

    * the enclosing package ``parent`` exactly when ``name`` denotes a package
      executed through its entry file (``marks_entry(name)``) AND a non-empty
      ``parent`` exists;
    * otherwise the qualified import name ``name`` itself.

  So a directly-named module ``pkg.sub.tool`` reproduces as ``pkg.sub.tool``
  (not its parent package ``pkg.sub``), while a package executed through its
  entry file reproduces as the package.

Strings are modelled as ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing); the specification is carried over the pure sequence theory
``PSeq[int]``.  The entry-file classification (``marks_entry``) is an unchanged
boundary callee modelled as a fully opaque ``@Pure @ContractOnly`` function (no
contract is consumed); its real implementation is validated out-of-band, code
point for code point, by axiom_check.py (G-AX) -- an A-reference the deep model
is checked against.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def marks_entry(name: PSeq[int]) -> bool:
    """Whether the qualified module name ``name`` denotes a package executed
    through its entry file (rather than a directly-named module).  This is the
    unchanged classification performed by the module-execution machinery; the
    selection logic under specification calls it but does not change it.

    The proof treats it as an entirely opaque boundary classifier (no contract
    is consumed).  The concrete classifier it stands in for is validated == the
    real selector code-point-for-code-point by axiom_check.py / G-AX -- an
    A-reference callee the deep model is checked against, not an axiom whose
    Ensures the proof relies on."""
    pass
# axioms-end


# pure-start
@Pure
def module_arg(name: PSeq[int], parent: PSeq[int]) -> PSeq[int]:
    """The module-name argument reproduced for the relaunch command."""
    if marks_entry(name) and len(parent) > 0:
        return parent
    return name
# pure-end


def select_module_name(name: List[int], parent: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(parent), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(parent), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reproduced argument is the qualified name itself unless the name
    # denotes a package executed through its entry file with a non-empty
    # enclosing package, in which case it is the enclosing package.
    Ensures(ToSeq(Result()) == module_arg(ToSeq(name), ToSeq(parent)))
    # Discriminating consequence: a directly-named module (name not an
    # entry-file package) reproduces as the name, NOT the parent package.
    Ensures(Implies(not marks_entry(ToSeq(name)),
                    ToSeq(Result()) == ToSeq(name)))
    # A package executed through its entry file reproduces as the package.
    Ensures(Implies(marks_entry(ToSeq(name)) and len(ToSeq(parent)) > 0,
                    ToSeq(Result()) == ToSeq(parent)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: the enclosing package was used unconditionally
    # whenever it was non-empty, regardless of whether the launched unit was a
    # directly-named module -- so a directly-named module was wrongly reproduced
    # as its parent package.
    result = []  # type: List[int]
    if len(parent) > 0:
        i = 0
        while i < len(parent):
            # invariants-start
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(parent))
            Invariant(len(parent) > 0)
            Invariant(ToSeq(result) == ToSeq(parent).take(i))
            Invariant(MustTerminate(len(parent) - i + 1))
            # invariants-end
            result = result + [parent[i]]
            i = i + 1
        Assert(ToSeq(parent).take(len(parent)) == ToSeq(parent))
    else:
        i = 0
        while i < len(name):
            # invariants-start
            Invariant(Acc(list_pred(name), 1 / 4))
            Invariant(Acc(list_pred(parent), 1 / 4))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(name))
            Invariant(ToSeq(result) == ToSeq(name).take(i))
            Invariant(MustTerminate(len(name) - i + 1))
            # invariants-end
            result = result + [name[i]]
            i = i + 1
        Assert(ToSeq(name).take(len(name)) == ToSeq(name))
    return result
    # impl-end
