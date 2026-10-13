"""Twin-artifact model for django__django-13837.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A development server, when it relaunches itself in a child process, must
  reconstruct the command line that started it. The reconstruction has to
  preserve HOW the program was started.

  When the program was started as a module -- i.e. with the interpreter's
  ``-m PACKAGE`` form -- the child command line must re-invoke that SAME
  package as a module: after the constant leading arguments (interpreter and
  warning options) it must contain the module-execution flag immediately
  followed by the package that was launched, and then the original program
  arguments (everything in the argument vector after the entry script). The
  package re-invoked must be the package that was actually launched -- whatever
  it is -- not a constant, built-in package name. A program is recognised as
  module-launched exactly when the launch reports a launch package AND that
  reported package name is non-empty; a launch that reports no package, or
  reports an empty package name (a plain script / directory launch), is not a
  module launch and is reconstructed by its argument vector as-is.

  When the program was NOT started as a module and its entry script still
  exists, the child command line is simply the leading arguments followed by
  the whole original argument vector (the entry script included). When the
  entry script no longer exists, a platform-specific recovery path applies;
  that path is unchanged here and is represented abstractly.

Strings are modelled as ``PSeq[int]`` of Unicode code points and the argument
vector as ``PSeq[PSeq[int]]`` of its elements (Nagini bans ``str`` indexing).
The leading arguments, the argument vector, and the launch-package name are
immutable pure-sequence values (read-only inputs -- pure values cannot be
mutated, so directive-5 read-only safety holds by construction). Whether a
launch package was reported at all is the boolean ``package_reported``. The
module-launch test is modelled deeply by the pure predicate
``is_module_launch`` (a reported, non-empty launch package); no callee is
axiomatized -- the launch detection that the change is about is spelled out,
not hidden behind an axiom, and is validated against its real runtime
semantics out-of-band by axiom_check.py (G-AX) as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The launch-detection predicate -- "a module launch is one
# that reports a non-empty launch package" -- and the re-invocation of that very
# package are modelled deeply by `is_module_launch` and direct use of the
# reported package below; they are validated against the real
# `__main__.__spec__`/`.parent` runtime semantics out-of-band by axiom_check.py
# (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def dash_m() -> PSeq[int]:
    # The module-execution flag '-m'.
    return PSeq(45, 109)


@Pure
def windows_recovery() -> PSeq[PSeq[int]]:
    # Abstract sentinel for the unchanged platform-specific recovery path taken
    # when the entry script no longer exists. Distinct from any normally-built
    # argument vector (it carries the single recovery marker element [0]).
    return PSeq(PSeq(0))


@Pure
def is_module_launch(package_reported: bool, launch_package: PSeq[int]) -> bool:
    """The program was started as a module exactly when a launch package is
    reported and its name is non-empty (deep model of `__main__.__spec__ is not
    None and __main__.__spec__.parent`; validated == real runtime semantics by
    G-AX)."""
    return package_reported and len(launch_package) > 0
# pure-end


def child_arguments(prefix: PSeq[PSeq[int]],
                    package_reported: bool,
                    launch_package: PSeq[int],
                    argv: PSeq[PSeq[int]],
                    script_exists: bool) -> PSeq[PSeq[int]]:
    # pre-conditions-start
    # The argument vector always carries at least the entry script element.
    Requires(len(argv) >= 1)
    # Total correctness: this method must TERMINATE, not merely satisfy the
    # postconditions on runs that reach the return. The level is input-dependent
    # rather than the constant 2 because a caller may be child_arguments itself:
    # a self-call needs a level strictly BELOW its caller's, which no constant
    # can provide (2 > 2 is false). len(argv) >= 1 makes this always >= 2, so
    # the level-2 guarantee is retained and there is room beneath the caller for
    # a self-call on a shorter argument vector. This demands termination of every
    # input the method already accepted -- no input is excluded.
    Requires(MustTerminate(len(argv) + 1))
    # pre-conditions-end
    # post-conditions-start
    # (A) Module launch: re-invoke the launched package as a module. After the
    # leading arguments comes the module flag, then the launched package ITSELF,
    # then the original program arguments (argv minus the entry script). The
    # emitted package is grounded in the reported package -- not any constant.
    Ensures(Implies(is_module_launch(package_reported, launch_package),
                    Result() == prefix
                    + PSeq(dash_m(), launch_package)
                    + argv.drop(1)))
    # (B) Not a module launch, entry script present: leading args then the whole
    # argument vector unchanged (entry script included).
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and script_exists,
                    Result() == prefix + argv))
    # (C) Not a module launch, entry script absent: the unchanged recovery path.
    Ensures(Implies(not is_module_launch(package_reported, launch_package)
                    and not script_exists,
                    Result() == windows_recovery()))
    # post-conditions-end
    # impl-start
    if package_reported and len(launch_package) > 0:
        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
    elif not script_exists:
        return windows_recovery()
    else:
        return prefix + argv
    # impl-end
