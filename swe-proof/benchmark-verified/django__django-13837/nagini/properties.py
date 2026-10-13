# properties.py — PBT falsification battery for django__django-13837.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region; the runner checks each with Nagini verify +
# markers.same_spec. Region surgery on a single anchor GUARANTEES same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance):
#   child_arguments(prefix, package_reported, launch_package, argv, script_exists)
#     -> PSeq[PSeq[int]]   reconstructs the reloader child argument vector.
#   Three branches, pinned by three load-bearing postcondition clauses:
#     (A) is_module_launch(package_reported, launch_package)
#           => Result() == prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
#         -- the bug-delta: emit the LAUNCHED PACKAGE ITSELF (launch_package), not
#            a constant. Pre-patch emitted the literal 'django'; the F2P
#            test_run_as_non_django_module asserts '-m utils_tests.test_module'.
#     (B) not is_module_launch and script_exists
#           => Result() == prefix + argv          (whole argv, entry script kept)
#     (C) not is_module_launch and not script_exists
#           => Result() == windows_recovery()     (the unchanged recovery sentinel)
#   is_module_launch(reported, pkg) == reported and len(pkg) > 0; dash_m() and
#   windows_recovery() are @Pure. ALL THREE are GROUNDED in the inputs (functions
#   of package_reported/launch_package), not opaque answer-keys -- see 'assessment'
#   for why there is no wrong ungrounded-oracle echo and what stands in for it.
#
# Read-only inputs: there is NO Acc(x, 1/2) heap input in this bundle. prefix,
# launch_package, argv are immutable PURE SEQUENCE VALUES (PSeq) and
# package_reported/script_exists are bool; pure values cannot be mutated, so the
# FRAME-MUTATION class does not apply (directive-5 read-only safety holds by
# construction -- meta.json string_modeling says exactly this). See 'assessment'
# for what stands in for it. There are NO @ContractOnly axioms (axioms region
# empty; meta.json axioms == []), so AXIOM_TESTS = [].
#
# F2P: test_run_as_non_django_module (a NON-django -m PACKAGE launch must emit
#      '-m utils_tests.test_module', not '-m django').
# Key P2P: test_run_as_module (a -m django launch still emits '-m django'),
#      test_warnoptions / TestChildArguments script-launch cases (the non-module
#      branch returns the whole argv unchanged).

from pathlib import Path

INSTANCE = "django__django-13837"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The whole frozen impl body (the only thing any rival edits; the trailing
# `# impl-end` marker is kept so the region boundary is never touched, which
# is what guarantees same_spec).
# ---------------------------------------------------------------------------
_IMPL = """    if package_reported and len(launch_package) > 0:
        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)
    elif not script_exists:
        return windows_recovery()
    else:
        return prefix + argv
    # impl-end"""


def _impl(new_body: str) -> str:
    """Replace ONLY the child_arguments impl body, keeping the # impl-end marker."""
    return _swap(_BASE, _IMPL, new_body + "\n    # impl-end")


# 'django' as a PSeq[int] of Unicode code points: d=100 j=106 a=97 n=110 g=103 o=111.
_DJANGO = "PSeq(100, 106, 97, 110, 103, 111)"


SPEC_TESTS = [

    # ===================================================================== soundness
    # POSITIVE CONTROL: a structurally-different but fully CORRECT impl. Branches
    # reordered (handle the non-module cases FIRST via the negated guard, fall
    # through to the module branch last) and the guard is expressed through the
    # @Pure helper is_module_launch instead of inlined. Same executable meaning;
    # no fold/induction lemma is needed (the postconditions are direct PSeq
    # equalities), so this MUST verify. If it cannot => SPEC-TOO-STRONG.
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if not is_module_launch(package_reported, launch_package):\n"
            "        if script_exists:\n"
            "            return prefix + argv\n"
            "        else:\n"
            "            return windows_recovery()\n"
            "    return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)"
        ),
        "rationale": "structurally-different CORRECT impl: non-module cases handled "
        "first via the negated @Pure guard, module branch last; same meaning. "
        "Postconditions are direct PSeq equalities (no fold lemma), so it must "
        "verify -- else SPEC-TOO-STRONG.",
    },

    # The honest cheapest positive control (stands in for the ungrounded-oracle
    # case, which does not apply here -- see 'assessment'). Bind the grounded
    # module-branch value to a typed local first, then return it; the non-module
    # branches likewise. This is the cheapest correct impl that does the real
    # work (emits launch_package itself, slices argv). Must verify.
    {
        "id": "pos-control-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if is_module_launch(package_reported, launch_package):\n"
            "        emitted = prefix + PSeq(dash_m(), launch_package) + argv.drop(1)  # type: PSeq[PSeq[int]]\n"
            "        return emitted\n"
            "    if not script_exists:\n"
            "        recovered = windows_recovery()  # type: PSeq[PSeq[int]]\n"
            "        return recovered\n"
            "    whole = prefix + argv  # type: PSeq[PSeq[int]]\n"
            "    return whole"
        ),
        "rationale": "cheapest correct impl: binds each grounded branch result to a "
        "typed local and returns it; emits launch_package ITSELF and slices argv. "
        "Grounded oracle => no wrong echo to build; this is the honest positive "
        "control.",
    },

    # ===================================================================== admissibility
    # The precondition is Requires(len(argv) >= 1) plus the termination obligation
    # Requires(MustTerminate(len(argv) + 1)). A self-call caller inside the impl
    # region constructs an F2P-shaped input -- a module launch of a NON-django
    # package, argv = [entry, 'runserver'] -- invokes child_arguments, and asserts a
    # postcondition consequence (the emitted package is launch_package itself, and
    # the program-arg tail is preserved). If the Requires cannot be met for a normal
    # input, or the post facts are not derivable => PRECOND-TOO-STRONG.
    # The probe is inserted at the TOP of the impl region, before any gold
    # obligation, so every following obligation is preserved verbatim.
    #
    # TERMINATION NOTE (why the `if len(argv) > len(av)` guard is here, and why it
    # is NOT a weakening of the probe): the obligation level is an ORDINAL that
    # orders calls, and Nagini requires a callee's level to be strictly BELOW its
    # caller's. This probe is a SELF-call, so caller and callee share the very same
    # precondition and therefore the very same level -- with the constant level 2
    # the check is `2 > 2`, which fails as
    #   "Obligation leak check failed. Callee child_arguments might not take all
    #    unsatisfied obligations from the caller."
    # and raising the constant cannot help, because it raises BOTH sides equally.
    # The spec's level is len(argv) + 1, so the guard establishes
    # len(av) + 1 < len(argv) + 1, discharging the ordering for this call. The guard
    # constrains only the PROBE's own reachability, never the specification or the
    # asserted post fact: inside the branch the full module-launch postcondition is
    # still proved for a genuine non-django launch. The branch is FEASIBLE, not
    # vacuous -- adding `Assert(False)` beside the existing Assert makes Nagini
    # report "Assertion False might not hold", so the call and its post fact really
    # are verified rather than skipped under an infeasible guard.
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE,
            "    # impl-start\n",
            "    # impl-start\n"
            "    # ADMISSIBILITY PROBE: an F2P-shaped module launch of a non-django\n"
            "    # package satisfies Requires(len(argv) >= 1); the call verifies and\n"
            "    # the module-launch postcondition is derivable. The guard supplies the\n"
            "    # strict level decrease MustTerminate(len(argv) + 1) demands of a\n"
            "    # self-call; the branch is feasible (Assert(False) there fails).\n"
            "    pkg = PSeq(97, 98)            # type: PSeq[int]\n"
            "    pre = PSeq(PSeq(112))         # type: PSeq[PSeq[int]]\n"
            "    av = PSeq(PSeq(115), PSeq(114))  # type: PSeq[PSeq[int]]\n"
            "    if len(argv) > len(av):\n"
            "        Assert(len(av) >= 1)\n"
            "        got = child_arguments(pre, True, pkg, av, True)  # type: PSeq[PSeq[int]]\n"
            "        Assert(got == pre + PSeq(dash_m(), pkg) + av.drop(1))\n",
        ),
        "rationale": "a positive-control caller invokes child_arguments on an "
        "F2P-shaped non-django module launch (argv length 2); Requires(len(argv)>=1) "
        "must admit it and the module-launch post fact must be derivable, else "
        "PRECOND-TOO-STRONG. The self-call additionally has to discharge "
        "MustTerminate(len(argv) + 1)'s strict-decrease ordering, which the "
        "len(argv) > len(av) guard supplies; the guarded branch is feasible.",
    },

    # ===================================================================== uniqueness
    # ATTACK 1 (partial-domain, THE bug-delta == model_prepatch.py). On the module
    # branch, emit a CONSTANT package literal 'django' instead of launch_package
    # itself. Correct iff launch_package == 'django'; WRONG for every other -m
    # PACKAGE launch. This is exactly the pre-patch behaviour the gold fix removes.
    {
        "id": "weak-constant-django",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if package_reported and len(launch_package) > 0:\n"
            "        return prefix + PSeq(dash_m(), " + _DJANGO + ") + argv.drop(1)\n"
            "    elif not script_exists:\n"
            "        return windows_recovery()\n"
            "    else:\n"
            "        return prefix + argv"
        ),
        "refinement": "this is the pre-patch `args += ['-m', 'django']`: it emits the "
        "fixed literal 'django' regardless of the launched package. The F2P "
        "test_run_as_non_django_module launches `-m utils_tests.test_module` and "
        "asserts the child argv is `[..., '-m', 'utils_tests.test_module', ...]`; a "
        "patch emitting 'django' produces `-m django` and FAILS the F2P -- it does "
        "NOT resolve (it IS the bug being fixed).",
        "rationale": "violates postcondition (A) Result() == prefix + "
        "PSeq(dash_m(), launch_package) + argv.drop(1): the emitted package must be "
        "launch_package ITSELF, but a constant differs whenever launch_package != "
        "'django'. Partial-domain (correct only on the launch_package=='django' "
        "sub-domain).",
    },

    # ATTACK 2 (partial-domain, drop the whole module detection). Treat EVERY
    # launch as non-module: never take the module branch. Correct on a genuine
    # script/directory launch; WRONG on any module launch (the entire point of the
    # change). This is the pre-pre-patch shape (no -m handling at all on this path).
    {
        "id": "weak-no-module-branch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if not script_exists:\n"
            "        return windows_recovery()\n"
            "    else:\n"
            "        return prefix + argv"
        ),
        "refinement": "this drops the `if __main__.__spec__ ... : args += ['-m', "
        "parent]; args += sys.argv[1:]` branch entirely, so a `-m PACKAGE` launch "
        "falls through to `args += sys.argv` (the whole argv, entry script kept, no "
        "-m). The F2P test_run_as_non_django_module asserts the child argv starts "
        "`[..., '-m', 'utils_tests.test_module', ...]`; this returns `[..., "
        "entry_script, 'runserver']` instead -- it FAILS the F2P and does NOT "
        "resolve. The P2P test_run_as_module (the -m django path) also breaks.",
        "rationale": "violates postcondition (A): on a module launch this returns "
        "prefix + argv (the (B) shape) instead of prefix + PSeq(dash_m(), "
        "launch_package) + argv.drop(1). Partial-domain (correct only on non-module "
        "launches).",
    },

    # ATTACK 3 (value-level off-by-one on the argv slice). On the module branch,
    # keep the WHOLE argv (entry script included) instead of dropping argv[0].
    # Correct in package name and flag; WRONG only in that the entry script is
    # duplicated into the child program arguments.
    {
        "id": "weak-keep-entry-script",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if package_reported and len(launch_package) > 0:\n"
            "        return prefix + PSeq(dash_m(), launch_package) + argv\n"
            "    elif not script_exists:\n"
            "        return windows_recovery()\n"
            "    else:\n"
            "        return prefix + argv"
        ),
        "refinement": "this emits `args += sys.argv` instead of `args += sys.argv[1:]` "
        "on the module branch, so the entry script (sys.argv[0]) is duplicated into "
        "the program arguments: the child sees `python -m PKG <entry_script> "
        "runserver` instead of `python -m PKG runserver`. The F2P "
        "test_run_as_non_django_module asserts exactly `[sys.executable, '-m', "
        "'utils_tests.test_module', 'runserver']` (no entry-script element) -- the "
        "extra element FAILS the F2P; it does NOT resolve.",
        "rationale": "violates postcondition (A): the tail must be argv.drop(1), but "
        "this returns argv (one extra leading element on every argv whose length "
        ">= 1). Value-level / off-by-one on the argv slice.",
    },

    # ATTACK 4 (value-level, wrong flag token). Emit a wrong leading flag instead
    # of dash_m() ('-m'). The package and argv slice are correct; only the flag is
    # wrong. dash_m() is a @Pure grounded token, so a faithful patch emitting a
    # different literal is observable.
    {
        "id": "weak-wrong-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if package_reported and len(launch_package) > 0:\n"
            "        return prefix + PSeq(PSeq(45, 99), launch_package) + argv.drop(1)\n"
            "    elif not script_exists:\n"
            "        return windows_recovery()\n"
            "    else:\n"
            "        return prefix + argv"
        ),
        "refinement": "this emits the flag '-c' (PSeq(45, 99)) instead of '-m' "
        "(PSeq(45, 109)): a faithful patch doing `args += ['-c', parent]` would "
        "re-launch the child with the wrong interpreter option (`python -c PKG ...`), "
        "which would not re-run the package as a module at all. The F2P / P2P "
        "(test_run_as_module, test_run_as_non_django_module) assert the flag is "
        "exactly '-m' -- a different flag FAILS them; it does NOT resolve.",
        "rationale": "violates postcondition (A): the first emitted token after the "
        "prefix must be dash_m() == PSeq(45, 109); PSeq(45, 99) differs in its "
        "second code point. Value-level (wrong flag token).",
    },

    # ATTACK 5 (partial-domain on the NON-module branches: swap (B) and (C)). When
    # NOT a module launch, return windows_recovery() when the script EXISTS and
    # prefix + argv when it does NOT -- the two non-module outcomes swapped.
    # Correct on the module branch; WRONG on both non-module sub-domains.
    {
        "id": "weak-swap-nonmodule",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if package_reported and len(launch_package) > 0:\n"
            "        return prefix + PSeq(dash_m(), launch_package) + argv.drop(1)\n"
            "    elif script_exists:\n"
            "        return windows_recovery()\n"
            "    else:\n"
            "        return prefix + argv"
        ),
        "refinement": "this swaps the script-exists guard on the non-module path: a "
        "normal script launch whose entry script EXISTS would take the Windows "
        "recovery path (`args += [exe_fixed, '-script.py']`) instead of `args += "
        "sys.argv`, and a missing entry script would (wrongly) replay sys.argv. The "
        "TestChildArguments script-launch P2P cases (existing entry script => whole "
        "argv) would get the recovery sentinel instead -- the faithful patch FAILS "
        "them; it does NOT resolve.",
        "rationale": "violates postconditions (B) and (C): on `not is_module_launch "
        "and script_exists` the result must be prefix + argv (here it is "
        "windows_recovery()), and on `not is_module_launch and not script_exists` it "
        "must be windows_recovery() (here it is prefix + argv). Partial-domain "
        "(both non-module sub-domains wrong, module sub-domain correct).",
    },

    # ATTACK 6 (supporting near-miss / value-level: emit the prefix wrong on the
    # module branch -- drop it). Correct flag/package/slice but omit the leading
    # interpreter+warnoptions arguments. A cheap supporting case, still carrying a
    # real refinement.
    {
        "id": "weak-drop-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if package_reported and len(launch_package) > 0:\n"
            "        return PSeq(dash_m(), launch_package) + argv.drop(1)\n"
            "    elif not script_exists:\n"
            "        return windows_recovery()\n"
            "    else:\n"
            "        return prefix + argv"
        ),
        "refinement": "this drops the leading `args = [sys.executable] + ['-W%s' % o "
        "for o in sys.warnoptions]` on the module branch, returning `['-m', PKG, "
        "...]` with no interpreter path. The F2P/P2P assert the child argv starts "
        "with sys.executable (and any -W options); omitting them FAILS the assertion "
        "-- the child would be exec'd without an interpreter -- so it does NOT "
        "resolve.",
        "rationale": "violates postcondition (A): the result must be prefix + "
        "PSeq(dash_m(), launch_package) + argv.drop(1), but this omits the prefix "
        "entirely. Supporting value-level near-miss (still a real refinement).",
    },
]


# No @ContractOnly axioms in this bundle (axioms region is empty; meta.json
# axioms == []). The single A-reference deep model is is_module_launch, and the
# bundle's axiom_check.py (G-AX) already EXECUTES the real importlib.machinery
# ModuleSpec objects -- the genuine type __main__.__spec__ is -- for -m PACKAGE
# (incl. the F2P 'utils_tests.test_module'), a directory launch (parent ''), and a
# script launch (spec None), asserting the predicate + emitted-package +
# child-argument reconstruction all agree with the real __main__.__spec__/.parent
# runtime semantics. There is nothing for the in-Docker axiom lane to add beyond
# that host-validated reference (the runtime rule is pure CPython import-system
# semantics, library-independent, fully exercised on the host). AXIOM_TESTS = [].
AXIOM_TESTS = []
