"""properties.py — G-PBT falsification battery for django__django-13837 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates — the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method assembling the child-process re-launch
argument vector as a total function of the observed environment:

  buildChildArgs (interp warnOpts : ...) (entry : EntryDesc) (probe : ScriptProbe)
                 (argv : ...) (exePath scriptPath : ...)
      return (out : Except ArgErr (List (List Char)))
    ensures out = childArgsSpec interp warnOpts entry probe argv exePath scriptPath

The single ``ensures`` is grounded in the method's own inputs through the
transparent pure function ``childArgsSpec`` (a total ``match`` over the entry
descriptor and the on-disk probe outcome, built from ``baseArgs`` /
``warnFlags``). There is NO opaque answer key: ``childArgsSpec`` /
``baseArgs`` / ``warnFlags`` are fully-unfolded ``def``s spelled out as
closed-form concatenations of the inputs, so evaluating the post-image IS the
correct computation and a wrong impl has nothing to echo.

The behavioral pivot the clause pins: on the module-launch arm
(``entry = moduleEntry pkg``) the re-launch names THAT package
(``["-m", pkg] ++ argv.drop 1``), not a fixed predetermined one; the two
"not a module" descriptors fall through to the script-path assembly whose four
mutually-exclusive probe outcomes each select a distinct result shape. That is
the whole load-bearing surface, and every rival below gets exactly one part of
it wrong.

BINDER STRUCTURE (read before judging binder coverage). ``buildChildArgs`` has
SEVEN input binders: ``interp``, ``warnOpts``, ``entry``, ``probe``, ``argv``,
``exePath``, ``scriptPath``. The reject witnesses collectively VARY every one of
them — ``interp`` (``"py"`` vs ``"px"``), ``warnOpts`` (``[]`` vs ``["error"]``
vs ``["error", "ignore"]``), ``entry`` (``moduleEntry`` / ``notModule`` /
``pathEntry``), ``probe`` (all four of ``exists`` / ``exeEntry`` /
``scriptEntry`` / ``missing``), ``argv`` (contents), ``exePath`` (``"e"`` vs
``"ex"``), ``scriptPath`` (``"s"`` vs ``"sp"``) — so no binder is held at a
single value that a rival mishandling only that input could slip past.

A caution about reading ``probe`` coverage off the witness inputs, since it is
what a first pass of this battery got wrong. Five rivals are wrong only on the
MODULE arm, and that arm ignores ``probe`` altogether: their witnesses pass
``probe = .exists``, but what those witnesses discriminate is the module arm,
NOT what the ``exists`` outcome computes. So "some witness mentions ``.exists``"
is not coverage of the ``exists`` ARM. Arm coverage is by rival, and each of the
five post-image arms now has at least one rival that is observably wrong THERE
and gold-correct elsewhere: module (``weak-constant-package``,
``weak-keep-entry-arg``, ``weak-wrong-flag``, ``weak-drop-prefix``,
``weak-drop-warnflags-only``, ``weak-no-module-detection``), ``exists``
(``weak-exists-arm``), ``exeEntry`` (``weak-exe-arm``), ``scriptEntry``
(``weak-script-arm``), ``missing`` (``weak-missing-not-error``).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling notes this class
    does NOT apply there either (its inputs are immutable PSeq/bool values, no
    ``Acc(x, 1/2)`` heap input). It is equally vacuous here: Velvet is
    referentially transparent, every input is an immutable value, the method
    declares no ``mut`` binder, there is no heap and no aliasing. No read-only
    input to overwrite, no permission system to trip, no substitute probe. Not
    fabricated (per the porting map, legitimately vacuous on Lean/Velvet).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
    rather than faking it is refused even earlier, by the elaborator's own
    check (``Decreasing annotations are required in total correctness
    semantics``). So divergence neither applies to this impl nor discharges the
    ``ensures`` clauses vacuously if a rival introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A. The nagini sibling records the SAME: its
    branch values are grounded in the inputs (functions of
    package_reported/launch_package), not opaque answer keys. ``childArgsSpec``
    here is likewise a grounded closed form, so there is no wrong echo to build;
    the two positive controls cover the cheapest correct impl (evaluate the pure
    post-image directly) and a structurally reshaped one.
  * ADMISSIBILITY — PRESENT, and it was WRONG to omit. An earlier revision of
    this battery recorded the lane as vacuous because the method declares no
    ``require`` clause, so "a normal input satisfies the precondition" has
    nothing to check. That reason does not survive: on a TOTAL carrier the
    analogue is the obligation being unsatisfiable, or degenerate, at exactly an
    F2P-shaped input — which a positive that discharges the obligation AT that
    concrete input by evaluation, before closing the frozen obligation verbatim,
    tests directly. ``admiss-f2p-point-satisfiable`` does that, and its liveness
    is established by two negative controls that each make it fail.
  * PARTIAL-DOMAIN / VALUE-LEVEL — the heart of the port, exactly as in nagini.
    Each rival is correct on part of the domain and wrong on the sub-domain the
    F2P exercises: emit a constant package instead of the launched one; keep the
    entry script instead of slicing it off; a wrong flag token; drop the
    interpreter prefix; ignore module detection entirely; or mishandle one of the
    script-path probe outcomes.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method`` CONTRACT,
not a bare predicate, so a witness reaches the postcondition through Velvet's own
tester machinery: ``buildChildArgsTester <args> = false`` says the extracted
program's result violates the postcondition at that concrete input. The carrier
is FULLY TRANSPARENT — ``List Char`` / the two ``DecidableEq`` inductives /
``Except`` all compute on concrete literals — so every reject witness closes by
``decide`` over literal inputs; no witness binds a hypothesis, so there is no
joint-satisfiability obligation. The one wrinkle: the postcondition's result
carrier is ``Except ArgErr (List (List Char))``, for which the workspace
synthesizes no ``DecidableEq`` on its own, so each witness first
``deriving instance DecidableEq for Except`` — an INSTANCE, not an assumption
(no ``axiom`` / ``sorry`` / ``native_decide``; the frozen solution rejects the
witnesses all the same). Checked in a file whose ``prove_correct`` block is
stripped, so no tactic script can mask the verdict. Each witness was verified
out-of-band with two real ``lean_verify.sh`` builds: green against its rival
(``decide`` reduces the tester to ``false``), red against the frozen solution
(``decide`` proves the same proposition ``is false`` — genuine discrimination,
not a parse/tactic artifact).

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (mapping.md §3:
no callee whose behavior the proof assumes); this gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13837"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. The WHOLE executable body of buildChildArgs (between -- impl-start
# and -- impl-end), and the FULL frozen proof body. Both lie wholly inside a
# region the spec view elides and each is unique in Solution.lean; _swap asserts
# both facts at load, so editing only these keeps markers.same_spec True and the
# prove_correct statement byte-identical.
# ---------------------------------------------------------------------------
_IMPL = (
    "    -- impl-start\n"
    "    -- The leading interpreter+warning-flags prefix, assembled once.\n"
    "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
    "    -- The forwarded user arguments: everything after the invoking script path.\n"
    "    let userArgs : List (List Char) := argv.drop 1\n"
    "    -- The module package, when the entry descriptor names a non-empty one: this\n"
    "    -- is the documented test for \"started as a module\", and the package it\n"
    "    -- yields is what the module-execution re-launch must name.\n"
    "    let modPkg : Option (List Char) :=\n"
    "      match entry with\n"
    "      | .moduleEntry pkg => some pkg\n"
    "      | _                => none\n"
    "    let out : Except ArgErr (List (List Char)) :=\n"
    "      match modPkg with\n"
    "      | some pkg =>\n"
    "          Except.ok (prefixArgs ++ ([\"-m\".toList, pkg] ++ userArgs))\n"
    "      | none =>\n"
    "          match probe with\n"
    "          | .exists      => Except.ok (prefixArgs ++ argv)\n"
    "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
    "          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
    "          | .missing     => Except.error .scriptMissing\n"
    "    return out\n"
    "    -- impl-end"
)

_PROOF = (
    "prove_correct buildChildArgs by\n"
    "  loom_solve\n"
    "  cases entry <;> simp_all [childArgsSpec, baseArgs]"
)

assert _BASE.count(_IMPL) == 1, "impl region drifted"
assert _BASE.count(_PROOF) == 1, "proof drifted"

_PROOF_BARE = "prove_correct buildChildArgs by\n  loom_solve"


def _impl(body: str) -> str:
    """Replace ONLY the buildChildArgs impl body, keeping the marker lines."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


def _impl_bareproof(body: str) -> str:
    """Replace the impl body AND retune the frozen tactic tail to a bare
    `loom_solve` (used only for a loop-free / directly-evaluated positive
    control whose proof needs no `cases entry`; the tactic body is elided from
    the spec view, so this is a proof reshape, not a spec change)."""
    return _swap(_impl(body), _PROOF, _PROOF_BARE)


# The FROZEN impl body, verbatim (everything strictly between the two markers).
# The admissibility case keeps it untouched and only PREPENDS an `assert`, so the
# method's own `ensures` obligation still has to discharge on the real body: the
# probe is additive, never a substitute for the frozen obligation.
_FROZEN_BODY = _IMPL.split("-- impl-start\n", 1)[1].rsplit("\n    -- impl-end", 1)[0]

# The admissibility probe needs the assert VC AND the frozen postcondition goal
# closed in the same script; the frozen tail is applied to `all_goals` and
# `warnFlags` is added to the simp set (the assert VC reduces to a `warnFlags`
# unfolding step the frozen simp set does not carry). Tactic body only — elided
# from the spec view, so the statement is untouched.
_PROOF_ADMISS = (
    "prove_correct buildChildArgs by\n"
    "  loom_solve\n"
    "  all_goals (cases entry <;> simp_all [childArgsSpec, baseArgs, warnFlags])"
)


def _impl_admiss(probe: str) -> str:
    """Prepend an in-region `assert` to the FROZEN impl body and retune the
    tactic tail so both the assert VC and the frozen `ensures` goal close."""
    return _swap(_impl(probe + _FROZEN_BODY), _PROOF, _PROOF_ADMISS)


# ---- witness preamble. `buildChildArgsTester <args> = false` reaches the
# ---- method postcondition through Velvet's tester machinery, checked in a file
# ---- whose `prove_correct` block has been stripped. `deriving instance
# ---- DecidableEq for Except` supplies the equality the postcondition's result
# ---- carrier needs (an instance, not an assumption). Every witness closes by
# ---- `decide` over concrete literals — no hypothesis is bound.
def _w(arg: str) -> str:
    return (
        "deriving instance DecidableEq for Except\n\n"
        "extract_program_for buildChildArgs\n"
        "prove_precondition_decidable_for buildChildArgs\n"
        "prove_postcondition_decidable_for buildChildArgs\n"
        "derive_tester_for buildChildArgs\n\n"
        f"example : buildChildArgsTester {arg} = false := by\n  decide\n"
    )


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================

    # The cheapest honest positive control: return the grounded post-image
    # directly. The whole branching computation collapses to the pure function
    # the `ensures` names; a loop-free shape, so the frozen `cases entry` tail is
    # retuned to a bare `loom_solve`. `childArgsSpec` is a fully-unfolded def, so
    # evaluating it IS the correct computation (no oracle to echo). Must verify.
    {
        "id": "pos-direct-spec",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_bareproof(
            "    return (childArgsSpec interp warnOpts entry probe argv exePath scriptPath)"),
        "rationale": "an impl that returns the grounded post-image "
        "`childArgsSpec …` directly must satisfy `out = childArgsSpec …`; the "
        "post-image is a fully-unfolded def over the inputs, not an opaque "
        "answer key, so evaluating it is the honest cheapest correct impl. If it "
        "fails => SPEC-TOO-STRONG.",
    },

    # A structurally-different CORRECT impl: drop the intermediate `modPkg`
    # Option and split on `entry` directly, spelling out BOTH "not a module"
    # descriptors (`notModule`, `pathEntry`) with the same probe assembly. Same
    # executable meaning, different control-flow shape; the frozen proof (which
    # `cases entry`) closes untouched. Must verify, else the clause is over-fit
    # to the impl FORM.
    {
        "id": "pos-inline-entry",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match entry with\n"
            "      | .moduleEntry pkg =>\n"
            "          Except.ok (prefixArgs ++ ([\"-m\".toList, pkg] ++ userArgs))\n"
            "      | .notModule =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (prefixArgs ++ argv)\n"
            "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
            "          | .missing     => Except.error .scriptMissing\n"
            "      | .pathEntry =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (prefixArgs ++ argv)\n"
            "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
            "          | .missing     => Except.error .scriptMissing\n"
            "    return out"),
        "rationale": "a reshape that drops the `modPkg` Option and splits on the "
        "entry descriptor directly (both 'not a module' cases spelled out with "
        "the same probe assembly) computes the identical result, so "
        "`out = childArgsSpec …` still holds and the frozen `cases entry` proof "
        "closes. A faithful reshape MUST verify, else SPEC-TOO-STRONG on impl "
        "form.",
    },

    # =====================================================================
    # ADMISSIBILITY — the third direction this gate tests (PRECOND-TOO-STRONG),
    # and it is NOT vacuous here just because the pre-conditions region is empty.
    # On a TOTAL carrier the analogue of "a normal input is admitted" is: the
    # obligation is SATISFIABLE, and non-degenerately so, at exactly an
    # F2P-shaped input. A post-image that were unsatisfiable at the interesting
    # point — or that collapsed the module-launch arm onto the fall-through arm
    # there — would read exactly like a live one, since every rival would be
    # rejected and every positive would verify for the wrong reason.
    #
    # This case discharges that BY EVALUATION, as an in-region `assert`, at the
    # F2P-shaped point (a module launch of a package that is NOT the framework's
    # own, with one forwarded user argument), and asserts two things about it:
    #   (1) the post-image at that input is a definite, concrete vector naming
    #       the LAUNCHED package after the module-execution flag — so the
    #       obligation is satisfiable there, and the value is the one the failing
    #       test demands rather than merely *some* value; and
    #   (2) the module-launch arm's value at that input DIFFERS from the
    #       fall-through arm's value at the same input — so the entry-descriptor
    #       pivot genuinely forks at the F2P point and is not degenerate.
    # The FROZEN impl body is kept verbatim after the assert, so the method's own
    # `ensures` obligation still discharges on the real body: this ADDS a live
    # obligation rather than replacing one.
    #
    # Liveness was machine-checked with two negative controls (not shipped, since
    # both must FAIL and a case must behave as declared): asserting the same shape
    # with a CONSTANT package literal in place of the launched one → exit 1, and
    # asserting the two arms are EQUAL (`=` for `≠`) → exit 1, while the case as
    # written → exit 0. So the assert is not a tautology the tactic would close
    # for any claim.
    # =====================================================================
    {
        "id": "admiss-f2p-point-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_admiss(
            "    assert (with_name_prefix `assert\n"
            "      (childArgsSpec \"py\".toList [] (.moduleEntry \"mypkg\".toList) .exists\n"
            "           [\"ep\".toList, \"u1\".toList] \"e\".toList \"s\".toList\n"
            "         = Except.ok [\"py\".toList, \"-m\".toList, \"mypkg\".toList, \"u1\".toList] ∧\n"
            "       childArgsSpec \"py\".toList [] (.moduleEntry \"mypkg\".toList) .exists\n"
            "           [\"ep\".toList, \"u1\".toList] \"e\".toList \"s\".toList\n"
            "         ≠ childArgsSpec \"py\".toList [] .notModule .exists\n"
            "           [\"ep\".toList, \"u1\".toList] \"e\".toList \"s\".toList))\n"),
        "rationale": "the obligation is SATISFIABLE and NON-DEGENERATE at an "
        "F2P-shaped input: at a module launch of a package that is not the "
        "framework's own, the post-image evaluates to a definite concrete vector "
        "that names THAT package after the module-execution flag (so there is a "
        "value discharging the clause there, and it is the value the failing test "
        "demands), and it DIFFERS from what the same input yields down the "
        "fall-through arm (so the entry-descriptor pivot really forks at that "
        "point). Both conjuncts are closed by evaluation over literals, and the "
        "frozen impl body is kept verbatim after the assert so the method's own "
        "`ensures` still discharges. If the assert cannot discharge, the "
        "obligation is unsatisfiable at exactly the input the change is about => "
        "PRECOND-TOO-STRONG (the total-carrier analogue). Liveness confirmed "
        "out-of-band: substituting a constant package for the launched one, or "
        "`=` for the `≠`, each makes this FAIL to verify.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input, and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================

    # ATTACK 1 (THE bug-delta). On the module branch, emit a CONSTANT package
    # literal "django" instead of the launched package itself. Correct iff the
    # launched package IS "django"; wrong for every other `-m PACKAGE` launch.
    {
        "id": "weak-constant-package",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let modPkg : Option (List Char) :=\n"
            "      match entry with\n"
            "      | .moduleEntry pkg => some pkg\n"
            "      | _                => none\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match modPkg with\n"
            "      | some _ =>\n"
            "          Except.ok (prefixArgs ++ ([\"-m\".toList, \"django\".toList] ++ userArgs))\n"
            "      | none =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (prefixArgs ++ argv)\n"
            "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
            "          | .missing     => Except.error .scriptMissing\n"
            "    return out"),
        "refinement": "emitting a fixed package name regardless of the launched "
        "package is exactly the pre-patch behaviour the change removes: it "
        "requests the framework's own package for EVERY module launch. The F2P "
        "launches a NON-framework module and asserts the child argv names THAT "
        "module by name; a patch emitting the fixed name produces the wrong "
        "`-m <name>` element and FAILS the F2P — it does NOT resolve (it IS the "
        "bug being fixed).",
        "rationale": "REJECT from `out = childArgsSpec …`: the module arm's "
        "post-image places the launched package `pkg` after `-m`, but the rival "
        "emits the constant, which differs whenever the launched package is not "
        "that constant. Partial-domain. Refuted at a module launch of "
        "`\"mypkg\"`.",
        "witness": _w('"py".toList [] (.moduleEntry "mypkg".toList) .exists '
                      '["a".toList, "b".toList] "e".toList "s".toList'),
    },

    # ATTACK 2 (value-level off-by-one on the argv slice). On the module branch
    # keep the WHOLE argv (invoking script path included) instead of the
    # forwarded arguments `argv.drop 1`. Package and flag correct; the entry
    # element is duplicated into the child's program arguments.
    {
        "id": "weak-keep-entry-arg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let modPkg : Option (List Char) :=\n"
            "      match entry with\n"
            "      | .moduleEntry pkg => some pkg\n"
            "      | _                => none\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match modPkg with\n"
            "      | some pkg =>\n"
            "          Except.ok (prefixArgs ++ ([\"-m\".toList, pkg] ++ argv))\n"
            "      | none =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (prefixArgs ++ argv)\n"
            "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
            "          | .missing     => Except.error .scriptMissing\n"
            "    return out"),
        "refinement": "forwarding the whole invocation vector instead of its "
        "tail duplicates the invoking-script element into the child's program "
        "arguments: the child sees an extra leading element that is not one of "
        "the forwarded user arguments. The F2P asserts the child argv is exactly "
        "the interpreter, `-m`, the package, and the forwarded arguments — with "
        "no extra element — so the surplus element FAILS the assertion; it does "
        "NOT resolve.",
        "rationale": "REJECT from `out = childArgsSpec …`: the module arm "
        "forwards `argv.drop 1`, but the rival forwards `argv` (one extra "
        "leading element on any non-empty argv). Value-level / off-by-one. "
        "Refuted at a module launch with argv `[\"m0\", \"m1\"]`.",
        "witness": _w('"py".toList [] (.moduleEntry "pkg".toList) .exists '
                      '["m0".toList, "m1".toList] "e".toList "s".toList'),
    },

    # ATTACK 3 (value-level, wrong flag token). Emit "-c" instead of "-m" before
    # the package. Package and slice correct; only the leading flag differs.
    {
        "id": "weak-wrong-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let modPkg : Option (List Char) :=\n"
            "      match entry with\n"
            "      | .moduleEntry pkg => some pkg\n"
            "      | _                => none\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match modPkg with\n"
            "      | some pkg =>\n"
            "          Except.ok (prefixArgs ++ ([\"-c\".toList, pkg] ++ userArgs))\n"
            "      | none =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (prefixArgs ++ argv)\n"
            "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
            "          | .missing     => Except.error .scriptMissing\n"
            "    return out"),
        "refinement": "emitting a different interpreter option before the "
        "package would re-launch the child with the wrong invocation mode (it "
        "would not re-run the package as a module at all). The F2P asserts the "
        "flag element is exactly the module-execution option; a different flag "
        "FAILS the assertion — it does NOT resolve.",
        "rationale": "REJECT from `out = childArgsSpec …`: the module arm's "
        "leading token is `\"-m\"`, but the rival emits `\"-c\"`, which differs "
        "in its second code point. Value-level (wrong flag token). Refuted at a "
        "module launch with interpreter `\"px\"` (a distinct binder value).",
        "witness": _w('"px".toList [] (.moduleEntry "pkg".toList) .exists '
                      '["a".toList, "b".toList] "e".toList "s".toList'),
    },

    # ATTACK 4 (value-level, drop the interpreter+warnflags prefix on the module
    # branch). Flag/package/slice correct; the always-present leading prefix
    # (interpreter path + warning-option flags) is omitted.
    {
        "id": "weak-drop-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let modPkg : Option (List Char) :=\n"
            "      match entry with\n"
            "      | .moduleEntry pkg => some pkg\n"
            "      | _                => none\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match modPkg with\n"
            "      | some pkg =>\n"
            "          Except.ok ([\"-m\".toList, pkg] ++ userArgs)\n"
            "      | none =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (prefixArgs ++ argv)\n"
            "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
            "          | .missing     => Except.error .scriptMissing\n"
            "    return out"),
        "refinement": "omitting the leading interpreter path and warning-option "
        "flags returns an argument vector with no interpreter to exec and none "
        "of the active warning options. The F2P (and the warning-option P2P) "
        "assert the child argv BEGINS with the interpreter path followed by the "
        "warning-option flags; dropping them FAILS the assertion — the child "
        "would be exec'd without an interpreter — so it does NOT resolve.",
        "rationale": "REJECT from `out = childArgsSpec …`: the module arm "
        "prepends `baseArgs interp warnOpts` (interpreter + `-W` flags), but the "
        "rival omits it entirely. Value-level near-miss. Refuted at a module "
        "launch carrying a warning option (`warnOpts = [\"error\"]`), so the "
        "dropped prefix is non-trivial — a distinct binder value.",
        "witness": _w('"py".toList ["error".toList] (.moduleEntry "pkg".toList) .exists '
                      '["a".toList, "b".toList] "e".toList "s".toList'),
    },

    # ATTACK 5 (partial-domain, drop module detection entirely). Ignore `entry`
    # and always take the script-path (probe) assembly. Correct on a genuine
    # non-module launch; wrong on any module launch (the entire point of the
    # change). The pre-pre-patch shape with no `-m` handling on this path.
    {
        "id": "weak-no-module-detection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match probe with\n"
            "      | .exists      => Except.ok (prefixArgs ++ argv)\n"
            "      | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "      | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
            "      | .missing     => Except.error .scriptMissing\n"
            "    return out"),
        "refinement": "ignoring the entry descriptor drops module detection "
        "altogether, so a module launch falls through to the script-path "
        "assembly (no `-m`, no package) instead of the module-execution form. "
        "The F2P asserts a module launch produces the module-execution argv; "
        "this returns the script-path shape instead — it FAILS the F2P and does "
        "NOT resolve (the framework-module P2P breaks too).",
        "rationale": "REJECT from `out = childArgsSpec …`: on a module launch "
        "the post-image takes the `moduleEntry` arm, but the rival takes a probe "
        "arm regardless of `entry`. Partial-domain (correct only on non-module "
        "launches). Refuted at a module launch whose probe outcome is "
        "`.exeEntry` — so the rival emits the exe-path shape where gold emits "
        "the module form.",
        "witness": _w('"py".toList [] (.moduleEntry "pkg".toList) .exeEntry '
                      '["a".toList, "b".toList] "e".toList "s".toList'),
    },

    # ATTACK 6 (non-module probe arm: exeEntry mishandled). On a non-module
    # launch whose script path resolves via the native-executable-suffix
    # fallback, return the plain script-run shape (`prefixArgs ++ argv`) instead
    # of exec'ing the executable sibling. Correct on the other three probe
    # outcomes; wrong only on `exeEntry`.
    {
        "id": "weak-exe-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let modPkg : Option (List Char) :=\n"
            "      match entry with\n"
            "      | .moduleEntry pkg => some pkg\n"
            "      | _                => none\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match modPkg with\n"
            "      | some pkg =>\n"
            "          Except.ok (prefixArgs ++ ([\"-m\".toList, pkg] ++ userArgs))\n"
            "      | none =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (prefixArgs ++ argv)\n"
            "          | .exeEntry    => Except.ok (prefixArgs ++ argv)\n"
            "          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
            "          | .missing     => Except.error .scriptMissing\n"
            "    return out"),
        "refinement": "collapsing the executable-suffix fallback onto the plain "
        "script-run shape re-launches the child through the interpreter on a "
        "path that does not exist as given (the reason that fallback exists), "
        "instead of directly exec'ing the resolved executable sibling. The "
        "executable-fallback P2P asserts the child argv is the resolved "
        "executable followed by the forwarded arguments; this returns the "
        "interpreter+argv shape instead — it FAILS that P2P and does NOT "
        "resolve.",
        "rationale": "REJECT from `out = childArgsSpec …`: on the non-module "
        "`exeEntry` outcome the post-image is `exePath :: argv.drop 1`, but the "
        "rival returns `prefixArgs ++ argv`. Partial-domain (only the `exeEntry` "
        "arm wrong). Refuted at `entry = notModule`, `probe = exeEntry`, so this "
        "exercises the `notModule` descriptor and a distinct `exePath` "
        "(`\"ex\"`).",
        "witness": _w('"py".toList [] .notModule .exeEntry '
                      '["a".toList, "b".toList] "ex".toList "s".toList'),
    },

    # ATTACK 7 (non-module probe arm: scriptEntry mishandled). On a non-module
    # launch resolved via the generated-launcher-script sibling, return the
    # plain script-run shape instead of running that sibling. Correct on the
    # other three probe outcomes; wrong only on `scriptEntry`. Uses the
    # `pathEntry` descriptor (the empty-package "not a module" case) so a rival
    # that only special-cased `notModule` is also exercised.
    {
        "id": "weak-script-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let modPkg : Option (List Char) :=\n"
            "      match entry with\n"
            "      | .moduleEntry pkg => some pkg\n"
            "      | _                => none\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match modPkg with\n"
            "      | some pkg =>\n"
            "          Except.ok (prefixArgs ++ ([\"-m\".toList, pkg] ++ userArgs))\n"
            "      | none =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (prefixArgs ++ argv)\n"
            "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "          | .scriptEntry => Except.ok (prefixArgs ++ argv)\n"
            "          | .missing     => Except.error .scriptMissing\n"
            "    return out"),
        "refinement": "collapsing the generated-launcher-script fallback onto "
        "the plain script-run shape re-launches through a path that does not "
        "exist as given, instead of substituting the launcher-script sibling the "
        "fallback resolved. The launcher-script P2P asserts the child argv "
        "carries the resolved sibling path in place of the invoking one; this "
        "returns the original path instead — it FAILS that P2P and does NOT "
        "resolve.",
        "rationale": "REJECT from `out = childArgsSpec …`: on the non-module "
        "`scriptEntry` outcome the post-image splices `scriptPath` before the "
        "forwarded arguments, but the rival returns `prefixArgs ++ argv`. "
        "Partial-domain (only the `scriptEntry` arm wrong). Refuted at "
        "`entry = pathEntry`, `probe = scriptEntry`, with `scriptPath = \"sp\"` "
        "— exercising the `pathEntry` descriptor and a distinct `scriptPath`.",
        "witness": _w('"py".toList [] .pathEntry .scriptEntry '
                      '["a".toList, "b".toList] "e".toList "sp".toList'),
    },

    # ATTACK 8 (non-module probe arm: missing mishandled). On a non-module launch
    # whose script path resolves to NONE of the candidates, return a success
    # value instead of the invalid-invocation failure. Correct on the other three
    # probe outcomes; wrong only on `missing`. Attacks the error arm of the
    # postcondition specifically (`Except.error` vs `Except.ok`).
    {
        "id": "weak-missing-not-error",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let modPkg : Option (List Char) :=\n"
            "      match entry with\n"
            "      | .moduleEntry pkg => some pkg\n"
            "      | _                => none\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match modPkg with\n"
            "      | some pkg =>\n"
            "          Except.ok (prefixArgs ++ ([\"-m\".toList, pkg] ++ userArgs))\n"
            "      | none =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (prefixArgs ++ argv)\n"
            "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
            "          | .missing     => Except.ok (prefixArgs ++ argv)\n"
            "    return out"),
        "refinement": "returning a success argument vector when the invoking "
        "script path names nothing executable suppresses the invalid-invocation "
        "error the routine must raise. The runtime-error P2P asserts that an "
        "unresolvable script path raises; a success value FAILS that P2P — it "
        "does NOT resolve.",
        "rationale": "REJECT from `out = childArgsSpec …`: on the non-module "
        "`missing` outcome the post-image is `Except.error .scriptMissing`, but "
        "the rival returns an `Except.ok`. This attacks the ERROR arm of the "
        "postcondition (ok vs error), the one no other rival touches. Refuted at "
        "`entry = notModule`, `probe = missing`.",
        "witness": _w('"py".toList [] .notModule .missing '
                      '["a".toList, "b".toList] "e".toList "s".toList'),
    },

    # ATTACK 9 (non-module probe arm: the `exists` outcome). On a non-module
    # launch whose script path exists AS GIVEN, forward only the tail
    # (`argv.drop 1`) instead of the whole invocation vector, so the invoking
    # script path itself is dropped from the child argv. Correct on the other
    # three probe outcomes and on every module launch; wrong only on `exists`.
    #
    # AUDIT NOTE (why this case exists). The eight rivals above leave the
    # non-module `exists` arm UNATTACKED. Five of them are wrong only on the
    # module arm, and although their witnesses all pass `probe = .exists`, the
    # module arm IGNORES `probe` entirely — so those witnesses discriminate the
    # module arm and say nothing about what `exists` computes. The remaining
    # three each mishandle one of `exeEntry` / `scriptEntry` / `missing`. So the
    # arm that carries the most-used real behaviour (a plain script launch) had
    # no rival that is observably wrong there. Re-derived with real builds: the
    # rival is rejected on a genuine unsolved `ensures` goal, its witness
    # elaborates against the rival (exit 0) and is refuted on the frozen
    # solution (exit 1, `decide` proving the same proposition IS FALSE).
    {
        "id": "weak-exists-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let prefixArgs : List (List Char) := baseArgs interp warnOpts\n"
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let modPkg : Option (List Char) :=\n"
            "      match entry with\n"
            "      | .moduleEntry pkg => some pkg\n"
            "      | _                => none\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match modPkg with\n"
            "      | some pkg =>\n"
            "          Except.ok (prefixArgs ++ ([\"-m\".toList, pkg] ++ userArgs))\n"
            "      | none =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (prefixArgs ++ userArgs)\n"
            "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "          | .scriptEntry => Except.ok (prefixArgs ++ ([scriptPath] ++ userArgs))\n"
            "          | .missing     => Except.error .scriptMissing\n"
            "    return out"),
        "refinement": "on the plain script-launch path the child must be given "
        "the script to run followed by the forwarded arguments; forwarding only "
        "the tail omits the script path itself, so the child would be exec'd "
        "with the interpreter and the user arguments but nothing to execute. "
        "The script-launch P2P (the warning-option one included) asserts the "
        "child argv carries the invoking script path between the interpreter "
        "prefix and the forwarded arguments; dropping it FAILS that assertion — "
        "it does NOT resolve.",
        "rationale": "REJECT from `out = childArgsSpec …`: on the non-module "
        "`exists` outcome the post-image is `baseArgs interp warnOpts ++ argv` "
        "(the WHOLE vector), but the rival appends only `argv.drop 1`, which "
        "differs on any non-empty argv. Partial-domain (only the `exists` arm "
        "wrong) — the one arm no other rival attacks. Refuted at "
        "`entry = pathEntry`, `probe = exists`, `warnOpts = [\"error\"]`.",
        "witness": _w('"py".toList ["error".toList] .pathEntry .exists '
                      '["ep".toList, "u1".toList] "e".toList "s".toList'),
    },

    # ATTACK 10 (value-level: the warning-option flags specifically). Keep the
    # interpreter path but drop the re-emitted `-W` flags on the module branch.
    # A strictly finer near-miss than `weak-drop-prefix`, which omits the whole
    # prefix: this one is correct whenever no warning option is active, so it
    # isolates the `warnFlags` half of `baseArgs` from the `interp` half.
    {
        "id": "weak-drop-warnflags-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let userArgs : List (List Char) := argv.drop 1\n"
            "    let modPkg : Option (List Char) :=\n"
            "      match entry with\n"
            "      | .moduleEntry pkg => some pkg\n"
            "      | _                => none\n"
            "    let out : Except ArgErr (List (List Char)) :=\n"
            "      match modPkg with\n"
            "      | some pkg =>\n"
            "          Except.ok (interp :: ([\"-m\".toList, pkg] ++ userArgs))\n"
            "      | none =>\n"
            "          match probe with\n"
            "          | .exists      => Except.ok (baseArgs interp warnOpts ++ argv)\n"
            "          | .exeEntry    => Except.ok (exePath :: userArgs)\n"
            "          | .scriptEntry => Except.ok (baseArgs interp warnOpts ++ ([scriptPath] ++ userArgs))\n"
            "          | .missing     => Except.error .scriptMissing\n"
            "    return out"),
        "refinement": "keeping the interpreter but discarding the re-emitted "
        "warning options means the restarted child no longer runs under the "
        "warning configuration the parent was started with, so warnings the "
        "operator asked to be raised silently stop being raised across a "
        "reload. The warning-option P2P asserts the active options reappear as "
        "flags in the child argv; dropping them FAILS that assertion — it does "
        "NOT resolve.",
        "rationale": "REJECT from `out = childArgsSpec …`: the module arm's "
        "post-image prepends `baseArgs interp warnOpts = interp :: warnFlags "
        "warnOpts`, but the rival prepends only `interp`, which differs "
        "whenever any warning option is active. Value-level near-miss that "
        "isolates the `warnFlags` half of the prefix (strictly finer than "
        "`weak-drop-prefix`, which drops both halves and is therefore never "
        "correct). Refuted at a module launch carrying TWO warning options.",
        "witness": _w('"py".toList ["error".toList, "ignore".toList] '
                      '(.moduleEntry "pkg".toList) .exists '
                      '["a".toList, "b".toList] "e".toList "s".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting.
#
# The nagini sibling has 9 SPEC cases (2 soundness positives, 1 admissibility,
# 6 uniqueness rivals) and an EMPTY axiom lane. This bundle models the SAME
# purely-functional core — the reconstruction of the reloader child argument
# vector as a total function of the observed environment — but over a RICHER
# carrier: nagini's single `script_exists : bool` becomes an `EntryDesc` (3
# observable entry-descriptor cases) crossed with a `ScriptProbe` (4
# mutually-exclusive, ordered script-path outcomes). The value/branch surface
# ports across intact; the extra probe arms give three MORE places a rival can
# be wrong than nagini's boolean had, and each is attacked.
#
#   nagini case                -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-reorder        -> pos-inline-entry              RE-EXPRESSED
#   pos-control-cheapest       -> pos-direct-spec               RE-EXPRESSED
#   admiss-self-call           -> admiss-f2p-point-satisfiable  RE-EXPRESSED
#   weak-constant-django       -> weak-constant-package         PORTED
#   weak-no-module-branch      -> weak-no-module-detection      PORTED
#   weak-keep-entry-script     -> weak-keep-entry-arg           PORTED
#   weak-wrong-flag            -> weak-wrong-flag               PORTED
#   weak-swap-nonmodule        -> weak-exe-arm / -script-arm /  RE-EXPRESSED
#                                 weak-missing-not-error /       (split per probe arm)
#                                 weak-exists-arm
#   weak-drop-prefix           -> weak-drop-prefix              PORTED
#                              -> weak-drop-warnflags-only      ADDED (audit)
#   AXIOM_TESTS (empty)        -> (none)                        N/A
#
# 13 SPEC cases (2 soundness, 1 admissibility, 10 uniqueness).
#
# ADDED BY AUDIT (two cases, both machine-checked with the three builds each):
#   weak-exists-arm — the non-module `exists` arm had NO rival that was
#     observably wrong on it (see the caution in the module docstring: the five
#     module rivals pass `probe = .exists` in their witnesses, but the module arm
#     ignores `probe`, so they discriminate the module arm and not that outcome).
#     This rival forwards `argv.drop 1` where the arm must forward the whole
#     `argv`, dropping the invoking script path from the child vector.
#   weak-drop-warnflags-only — `weak-drop-prefix` drops interpreter AND warning
#     flags together, so it is wrong at every input and never isolates the
#     `warnFlags` half of `baseArgs`. This finer rival keeps `interp` and drops
#     only the `-W` flags, so it is correct whenever no warning option is active
#     and pins the warning-option re-emission on its own.
#
# RE-EXPRESSED (positives): nagini's `pos-control-reorder` handles the
#   non-module cases first via a negated @Pure guard; the analogous
#   structurally-different reshape here (`pos-inline-entry`) drops the
#   intermediate `modPkg` Option and splits on the entry descriptor directly,
#   spelling out both "not a module" descriptors — same meaning, different shape,
#   frozen proof closes untouched. nagini's `pos-control-cheapest` binds each
#   grounded branch to a typed local; the cheapest honest control here
#   (`pos-direct-spec`) returns the grounded post-image `childArgsSpec …`
#   directly (proof retuned to a bare `loom_solve`, the tactic body being elided
#   from the spec view). Both were verified with a real build.
# PORTED (rivals): the four nagini partial-domain / value-level rivals
#   (`weak-constant-django`, `weak-no-module-branch`, `weak-keep-entry-script`,
#   `weak-wrong-flag`, `weak-drop-prefix`) re-express one-for-one, each with the
#   refinement argument carried over: emit a fixed package / forward the whole
#   argv / a wrong flag / drop the prefix / ignore module detection, all of which
#   make the assembled child argv disagree with what the F2P (or a P2P) asserts,
#   so the faithful patch does NOT resolve.
# RE-EXPRESSED (weak-swap-nonmodule): nagini swaps its TWO non-module outcomes
#   (script exists vs not). This carrier has FOUR non-module outcomes, so the
#   single swap becomes four arm-level rivals — `weak-exists-arm`,
#   `weak-exe-arm`, `weak-script-arm`, `weak-missing-not-error` — each
#   mishandling exactly ONE probe outcome (the plain script launch, the
#   executable-suffix fallback, the generated-launcher-script fallback, and the
#   invalid-invocation error), leaving the other three gold-correct. This is
#   carrier WIDENING, not fabrication: each rival's faithful patch breaks the P2P
#   for exactly that outcome. `weak-missing-not-error` is the only rival that
#   attacks the ERROR arm of the `Except` postcondition.
# RE-EXPRESSED (admiss-self-call -> admiss-f2p-point-satisfiable). nagini
#   self-calls child_arguments on an F2P-shaped input to show
#   `Requires(len(argv) >= 1)` admits it. Two earlier revisions of this file
#   recorded the lane VACUOUS because the velvet method declares no `require`
#   clause, and both were wrong to: "the frozen obligation has no precondition"
#   is not a demonstration of vacuity, it is a restatement of the carrier
#   difference. The lane's PURPOSE — can the obligation actually be met at the
#   input the change is about? — re-aims onto a total carrier as: is the
#   obligation SATISFIABLE, and non-degenerate, at an F2P-shaped point? That is
#   testable and now tested. The shipped case evaluates the post-image at a
#   module launch of a non-framework package and asserts (a) it equals the
#   definite concrete vector naming that launched package after the
#   module-execution flag, and (b) it differs from what the fall-through arm
#   yields at the same input, then closes the frozen obligation on the verbatim
#   frozen body. The "the two positive controls already witness it" argument the
#   earlier revision gave is also insufficient: both positives quantify over all
#   inputs and neither pins a VALUE at the F2P point, so neither would notice a
#   post-image that was degenerate exactly there.
# FRAME / PERMISSION-MUTATION: vacuous. nagini itself records this class as N/A
#   (its inputs are immutable PSeq/bool values, no half-permission heap input);
#   it is equally vacuous on this referentially-transparent carrier (no `mut`
#   binder, no heap, no aliasing). Not fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own ``decreasing_1`` goal. Dropping the clause
#   rather than faking it is refused even earlier, by the elaborator's own
#   check (``Decreasing annotations are required in total correctness
#   semantics``). So divergence neither applies to this impl nor discharges the
#   ``ensures`` clauses vacuously if a rival introduces it.
# AXIOM_TESTS: empty in nagini and here; the axioms region declares no `axiom`
#   (mapping.md §3), and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The single `ensures out = childArgsSpec …` clause is
#   attacked by all ten rivals. Its seven input binders are collectively VARIED
#   across the reject witnesses: `interp` (`"py"`/`"px"`), `warnOpts`
#   (`[]`/`["error"]`/`["error","ignore"]`), `entry`
#   (`moduleEntry`/`notModule`/`pathEntry`), `probe` (all four of `exists`,
#   `exeEntry`, `scriptEntry`, `missing`), `argv` (contents), `exePath`
#   (`"e"`/`"ex"`), `scriptPath` (`"s"`/`"sp"`). Each reject witness probes a
#   DISTINCT input point. So no binder is pinned to one value that a rival
#   mishandling only that input could slip past.
#
#   ARM coverage is counted BY RIVAL, not by which literals the witnesses
#   mention — the distinction an earlier revision of this file got wrong, since
#   the module arm ignores `probe` and the module rivals' `probe = .exists`
#   therefore attests nothing about the `exists` arm. Every arm of the post-image
#   now has ≥1 rival observably wrong THERE and gold-correct elsewhere: module
#   (six rivals), `exists` (`weak-exists-arm`), `exeEntry` (`weak-exe-arm`),
#   `scriptEntry` (`weak-script-arm`), `missing`/error arm
#   (`weak-missing-not-error`). Within the module arm the four value-level
#   components are separately pinned: the package (`weak-constant-package`), the
#   flag token (`weak-wrong-flag`), the argv slice (`weak-keep-entry-arg`), and
#   the two halves of the prefix (`weak-drop-prefix` for both,
#   `weak-drop-warnflags-only` for the `-W` flags alone).
# WITNESS DISCRIMINATION (re-derived by an independent audit with real builds —
#   three per reject case: rival module, witness-vs-rival, witness-vs-gold): each
#   witness ELABORATES against its rival (exit 0; the extracted tester `decide`s
#   to `false` at the probed input) and FAILS against the frozen solution (exit
#   1, `decide` proving the SAME proposition `is false`). That gold-side error is
#   a SEMANTIC refutation of the concrete claim — not an unknown identifier, type
#   error, unfolding failure or timeout — so it is a genuine discriminator rather
#   than a parse/tactic artifact. Each rival's own rejection was likewise
#   confirmed to be an unsolved `ensures_1` goal naming the offending arm, not
#   incidental tactic breakage. No witness binds a hypothesis (the carrier
#   computes on concrete literals), so there is no joint-satisfiability
#   obligation. No `sorry`/`admit`/`native_decide`/`axiom` appears; `deriving
#   instance DecidableEq for Except` supplies an instance the result carrier
#   needs, not an assumption.
# SPEC PROBES RUN BY THE AUDIT (not shipped as cases; recorded for the next
#   reader). Six further wrong impls were built and all six were REJECTED: drop
#   the script path on the `exists` arm; keep the whole argv on the `exeEntry`
#   arm; swap the `exeEntry`/`scriptEntry` results; keep `interp` but drop the
#   `-W` flags; make the module arm honour `probe = missing`; treat an
#   empty-package `moduleEntry` as not-a-module. Four further CORRECT reshapes
#   were built and all four VERIFIED: `argv.tail` for `argv.drop 1`; `warnOpts.map`
#   for the front-recursive `warnFlags`; the probe `match` hoisted outside the
#   module test; `"-m" :: pkg :: userArgs` for the `++` spelling. So the clause is
#   neither too weak nor over-fit to the frozen impl's syntactic form on these
#   probes. The spec's value was additionally confirmed by `decide` to equal the
#   exact vector each real test asserts, at all five arms.
#
# A LATER INDEPENDENT AUDIT re-derived every case from scratch (not trusting the
#   record) with 49 real builds, and adds these probes on top of the above.
#   SEVEN MORE wrong impls, all REJECTED on unsolved `ensures_1` goals: drop the
#   module-execution flag but keep the package; emit the warning flags BEFORE the
#   interpreter (prefix order); reverse the forwarded arguments; swap the flag and
#   package order; splice the launcher-script sibling but drop the forwarded
#   arguments; prepend the interpreter prefix to the executable-sibling arm; and
#   treat a path entry as a module launch with an EMPTY package name. FOUR MORE
#   correct reshapes, all VERIFIED: the probe `match` hoisted outside the module
#   test with the module case duplicated into all four probe arms (a fully
#   inverted branch order); `argv.tail`; `baseArgs` spelled out inline as
#   `interp :: warnFlags warnOpts`; and the `::` spelling on the module arm. So
#   attacks D and E remain clean under a second, differently-aimed pass.
#   FORGERY TEST (the one check the gate cannot do) run on ALL TEN reject
#   witnesses: each was rebuilt against the frozen solution with its claim FLIPPED
#   (`= true` for `= false`) and every flipped build then SUCCEEDS (exit 0) where
#   the witness itself fails (exit 1). Gold's exit code therefore tracks what the
#   witness CLAIMS rather than being a fixed artifact of the file, which is what
#   makes each rejection attributable to the spec.
AXIOM_TESTS = []
