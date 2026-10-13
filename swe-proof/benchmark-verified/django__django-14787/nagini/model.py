"""Twin-artifact model for django__django-14787.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a function decorator is turned into a method decorator, the callable that
  is handed to that decorator (the per-instance bound callable assembled for the
  decorated method) must carry the same function-identity metadata as the
  original method. Concretely, the standard wrapper-identity attributes — the
  callable's name and its defining module — must be present on the assembled
  callable and equal to the original method's, rather than absent.

  A freshly assembled bound callable starts with NONE of these identity
  attributes (it is a plain partial application that exposes no function
  metadata). The desired behaviour copies, from the original method onto the
  assembled callable, each identity attribute that the method possesses, so a
  decorator inspecting the callable it receives observes the method's own name
  and module.

A callable's relevant identity is modelled as a minimal class carrying the two
touched, behaviour-bearing facets — its name and its defining module — each as
a presence flag (whether the attribute exists on the object) and a value. The
original method has both attributes present; the freshly assembled bound
callable has both absent. The identity-copying step is the unchanged
standard-library wrapper-update primitive; it is modelled DEEPLY here (the
per-attribute copy is spelled out) and validated equal to the real primitive
out-of-band by axiom_check.py (G-AX), not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class FuncIdentity:
    def __init__(self, has_name: bool, name: int, has_module: bool, module: int) -> None:
        # Level 1: this constructor is loop-free and calls nothing obligated, so
        # it needs no room beneath it; callers (level 6) sit strictly above.
        Requires(MustTerminate(1))
        Ensures(Acc(self.has_name) and self.has_name == has_name)      # type: ignore
        Ensures(Acc(self.name) and self.name == name)                  # type: ignore
        Ensures(Acc(self.has_module) and self.has_module == has_module)  # type: ignore
        Ensures(Acc(self.module) and self.module == module)            # type: ignore
        self.has_name = has_name
        self.name = name
        self.has_module = has_module
        self.module = module


# axioms-start
# (no consumed @ContractOnly axiom: the wrapper-identity copy is modelled
#  deeply below — see the impl — and validated == the real standard-library
#  primitive by axiom_check.py / G-AX as an A-reference, not consumed here.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def assemble_bound_callable(method: FuncIdentity) -> FuncIdentity:
    # pre-conditions-start
    Requires(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
    Requires(Acc(method.has_module, 1 / 2) and Acc(method.module, 1 / 2))
    # The original method carries its identity metadata (both attributes exist).
    Requires(method.has_name)
    Requires(method.has_module)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(method.has_name, 1 / 2) and Acc(method.name, 1 / 2))
    Ensures(Acc(method.has_module, 1 / 2) and Acc(method.module, 1 / 2))
    # The method is read-only: its identity is unchanged.
    Ensures(method.has_name == Old(method.has_name) and method.name == Old(method.name))
    Ensures(method.has_module == Old(method.has_module) and method.module == Old(method.module))
    # The assembled callable is a fresh object the caller fully owns.
    Ensures(Acc(Result().has_name) and Acc(Result().name))
    Ensures(Acc(Result().has_module) and Acc(Result().module))
    # The assembled callable carries the method's identity metadata: its name
    # and module attributes are present and equal to the method's own.
    Ensures(Result().has_name)
    Ensures(Result().has_module)
    Ensures(Result().name == method.name)
    Ensures(Result().module == method.module)
    # post-conditions-end
    # impl-start
    # The assembled callable is a plain partial application that on its own
    # exposes no function-identity metadata; the wrapper-update copies, from the
    # method onto it, each identity attribute the method possesses. The method
    # has both attributes (precondition), so the assembled callable ends up
    # carrying both — its name and module marked present and equal to the
    # method's own (the spelled-out per-attribute copy, collapsed to its result
    # for the contracted domain).
    has_name = method.has_name
    name = method.name
    has_module = method.has_module
    module = method.module
    bound = FuncIdentity(has_name, name, has_module, module)
    return bound
    # impl-end
