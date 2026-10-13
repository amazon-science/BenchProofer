"""Twin-artifact model for django__django-15161.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A deconstructible expression node reports an import path for serialization.
  When the node declares a canonical import path and is exactly that declared
  type, the reported path is that canonical path verbatim. Otherwise the node
  falls back to the dotted qualified name `module "." name` derived from where
  its class happens to live.

  The expression nodes addressed here declare a canonical path rooted directly
  at the public `django.db.models` package (e.g. `django.db.models.Value`),
  rather than reporting the longer dotted name of whichever internal submodule
  they happen to be defined in. A path rooted at the public package is exactly
  the condition under which a migration serializer emits the short `models.X`
  reference (with a single `from django.db import models` import) instead of
  importing that internal submodule.

Strings (import paths, module, class name) are modelled as `List[int]` of
Unicode code points (Nagini bans `str` indexing); the specification is carried
by `PSeq[int]`. The path choice and the public-package-rooting check are
expressible directly, so they are modelled DEEPLY and verified — there are no
consumed axioms. The deep rooting model is validated == the real serializer
rooting test out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms: the modeled behaviour is fully expressible
#  over List[int]/PSeq[int]. The deep rooting model `serialized_module_rooted`
#  is an A-reference, validated == the real serializer by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def DOT() -> int:
    # ord('.')
    return 46


@Pure
def public_root() -> PSeq[int]:
    """The public package prefix INCLUDING its trailing dot:
    'django.db.models.' as code points. A reported path is short-form-eligible
    iff it equals this prefix followed by a single dot-free leaf name."""
    return PSeq(100, 106, 97, 110, 103, 111, 46, 100, 98, 46,
               109, 111, 100, 101, 108, 115, 46)


@Pure
def qualified(module: PSeq[int], name: PSeq[int]) -> PSeq[int]:
    """The dotted qualified-name fallback: `module "." name`."""
    return module + PSeq(DOT()) + name


@Pure
def no_dot(s: PSeq[int]) -> bool:
    """True iff `s` contains no '.' code point (a single path component)."""
    return Forall(int, lambda k: (Implies(0 <= k and k < len(s),
                                          s[k] != DOT())))


@Pure
def serialized_module_rooted(p: PSeq[int]) -> bool:
    """Deep model of the serializer's rooting test: `p` reduces to the short
    `models.<leaf>` form iff its component before the LAST dot is exactly the
    public `django.db.models` package. Equivalently: `p` begins with the
    `django.db.models.` prefix and the remaining leaf carries no further dot."""
    return (len(p) > len(public_root()) and
            p.take(len(public_root())) == public_root() and
            no_dot(p.drop(len(public_root()))))
# pure-end


def deconstruct_path(configured: List[int], exact: bool,
                     module: List[int], name: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(configured), 1 / 2))
    Requires(Acc(list_pred(module), 1 / 2))
    Requires(Acc(list_pred(name), 1 / 2))
    # The class name component carries no embedded dot (it is a single leaf).
    Requires(no_dot(ToSeq(name)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(configured), 1 / 2))
    Ensures(Acc(list_pred(module), 1 / 2))
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # When a canonical path is configured AND the node is exactly that type,
    # the reported path is that canonical path verbatim.
    Ensures(Implies(len(configured) > 0 and exact,
                    ToSeq(Result()) == ToSeq(configured)))
    # Otherwise it is the dotted qualified-name fallback.
    Ensures(Implies(not (len(configured) > 0 and exact),
                    ToSeq(Result()) == qualified(ToSeq(module), ToSeq(name))))
    # The reported path is short-form-eligible (rooted at the public package)
    # exactly as the chosen branch dictates.
    Ensures(serialized_module_rooted(ToSeq(Result())) ==
            (serialized_module_rooted(ToSeq(configured))
             if (len(configured) > 0 and exact)
             else serialized_module_rooted(qualified(ToSeq(module), ToSeq(name)))))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the node carries no configured canonical path, so the
    # reported path is ALWAYS the dotted qualified name derived from where the
    # class is defined (the internal submodule) — the configured path is never
    # consulted, even when one would be available for the exact type.
    result = []  # type: List[int]
    i = 0
    while i < len(module):
        # invariants-start
        Invariant(Acc(list_pred(configured), 1 / 2))
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(module))
        Invariant(ToSeq(result) == ToSeq(module).take(i))
        Invariant(MustTerminate(len(module) - i + 1))
        # invariants-end
        result = result + [module[i]]
        i = i + 1
    Assert(ToSeq(module).take(len(module)) == ToSeq(module))
    result = result + [DOT()]
    j = 0
    while j < len(name):
        # invariants-start
        Invariant(Acc(list_pred(configured), 1 / 2))
        Invariant(Acc(list_pred(module), 1 / 2))
        Invariant(Acc(list_pred(name), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(name))
        Invariant(ToSeq(result) == ToSeq(module) + PSeq(DOT()) + ToSeq(name).take(j))
        Invariant(MustTerminate(len(name) - j + 1))
        # invariants-end
        result = result + [name[j]]
        j = j + 1
    Assert(ToSeq(name).take(len(name)) == ToSeq(name))
    return result
    # impl-end
