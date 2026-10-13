"""Twin-artifact model for scikit-learn__scikit-learn-14141.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A diagnostic routine reports the installed version of each of the project's
  relevant runtime dependencies. It works from a predetermined roster of
  dependency module names; for every name on that roster it records, in the returned
  mapping, an entry keyed by that name whose value is the version observed for
  that module (a version marker, or the absent marker when the module cannot be
  imported). The returned mapping therefore has exactly one entry per name on
  the roster, and a name appears as a key of the result if and only if it is on
  the roster.

  The roster of relevant dependencies must include the parallel-execution
  dependency the project relies on at this version, alongside the package
  manager, the build/packaging helpers, the project itself, the numerical
  array library, the scientific-computing library, the compiled-extension
  toolchain, the dataframe library, and the plotting library. In particular the
  parallel-execution dependency's name must be reported among the result's keys,
  just as every other rostered dependency is.

Modelling choices (Nagini fragment):
  * A dependency module name is an `int` identity token; the nine roster tokens
    (the eight long-standing ones and the parallel-execution dependency) are
    module-level `@Pure` constants (mapping.md ss1). The tested behaviour only
    observes WHICH names appear as keys of the result, so integer identity is
    the faithful carrier (mapping.md ss2).
  * The roster is a `List[int]` of name tokens, built in the impl region exactly
    as the routine builds its dependency roster.
  * The observed version of a module is an unchanged opaque callee (importing
    the module and reading its version, or the absent marker on failure),
    axiomatised as `version_of` -- the value is not observed by the tested
    behaviour, only the presence of the key.
  * The result is a `Dict[int, int]` from a name token to its version marker.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.

Termination: the real routine is loop-free straight-line work (build a static
list, populate a dict, return), so every call returns. Nagini checks partial
correctness by default, so without a termination obligation a same-spec impl
that spins forever satisfies every Ensures vacuously while its real
counterpart would hang the F2P. `Requires(MustTerminate(2))` pins totality; it
adds no behaviour beyond what the real code already has, so it cannot exclude
a correct implementation.
"""
from typing import List, Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def version_of(name: int) -> int:
    """The version marker observed for a dependency module name: the imported
    module's reported version, or the absent marker when the module cannot be
    imported. An unchanged opaque callee (import + version read); its value is
    not part of the tested behaviour. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Ensures(True)
# axioms-end


# pure-start
@Pure
def name_pip() -> int:
    return 0


@Pure
def name_setuptools() -> int:
    return 1


@Pure
def name_sklearn() -> int:
    return 2


@Pure
def name_numpy() -> int:
    return 3


@Pure
def name_scipy() -> int:
    return 4


@Pure
def name_cython() -> int:
    return 5


@Pure
def name_pandas() -> int:
    return 6


@Pure
def name_matplotlib() -> int:
    return 7


@Pure
def name_parallel() -> int:
    # the parallel-execution dependency this version relies on
    return 8
# pure-end


def collect_deps_versions() -> Dict[int, int]:
    # pre-conditions-start
    # No inputs: the roster is predetermined and built internally.
    # Totality obligation: the real _get_deps_info() is loop-free straight-line
    # code — every call returns. Without this, a same-spec impl that diverges
    # (e.g. `while b: Invariant(True)`) verifies vacuously under Nagini's
    # partial-correctness default while its real counterpart hangs the F2P.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # Every pre-existing rostered dependency name is reported as a key of the
    # result, and carries the version observed for that module.
    Ensures(name_pip() in Result()
            and Result()[name_pip()] == version_of(name_pip()))
    Ensures(name_setuptools() in Result()
            and Result()[name_setuptools()] == version_of(name_setuptools()))
    Ensures(name_sklearn() in Result()
            and Result()[name_sklearn()] == version_of(name_sklearn()))
    Ensures(name_numpy() in Result()
            and Result()[name_numpy()] == version_of(name_numpy()))
    Ensures(name_scipy() in Result()
            and Result()[name_scipy()] == version_of(name_scipy()))
    Ensures(name_cython() in Result()
            and Result()[name_cython()] == version_of(name_cython()))
    Ensures(name_pandas() in Result()
            and Result()[name_pandas()] == version_of(name_pandas()))
    Ensures(name_matplotlib() in Result()
            and Result()[name_matplotlib()] == version_of(name_matplotlib()))
    # The discriminating clause: the parallel-execution dependency must also be
    # reported among the result's keys, carrying its observed version.
    Ensures(name_parallel() in Result()
            and Result()[name_parallel()] == version_of(name_parallel()))
    # No spurious keys: every key of the result is one of the rostered names.
    Ensures(Forall(int, lambda n: (Implies(n in Result(),
            n == name_pip() or n == name_setuptools() or n == name_sklearn()
            or n == name_numpy() or n == name_scipy() or n == name_cython()
            or n == name_pandas() or n == name_matplotlib()
            or n == name_parallel()))))
    # post-conditions-end
    # impl-start
    # The dependency roster, assembled exactly as the routine builds it: one
    # name token per relevant dependency, including the parallel-execution
    # dependency. Each rostered name becomes a key of the result mapped to the
    # version observed for that module. (The roster has constant, statically known
    # membership, so the per-name population is spelled out one entry per name;
    # refinement.md maps this to the routine's loop over the roster list.)
    deps = [
        name_pip(),
        name_setuptools(),
        name_sklearn(),
        name_numpy(),
        name_scipy(),
        name_cython(),
        name_pandas(),
        name_matplotlib(),
        name_parallel(),
    ]  # type: List[int]
    Assert(len(deps) == 9)
    deps_info = {}  # type: Dict[int, int]
    deps_info[name_pip()] = version_of(name_pip())
    deps_info[name_setuptools()] = version_of(name_setuptools())
    deps_info[name_sklearn()] = version_of(name_sklearn())
    deps_info[name_numpy()] = version_of(name_numpy())
    deps_info[name_scipy()] = version_of(name_scipy())
    deps_info[name_cython()] = version_of(name_cython())
    deps_info[name_pandas()] = version_of(name_pandas())
    deps_info[name_matplotlib()] = version_of(name_matplotlib())
    deps_info[name_parallel()] = version_of(name_parallel())
    return deps_info
    # impl-end
