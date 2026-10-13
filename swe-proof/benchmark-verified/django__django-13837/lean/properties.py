# properties.py — G-PBT falsification battery for django__django-13837 (lean lane).
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. Each SPEC_TESTS entry is a
# FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl
# region — and, for a positive that reproves, the proof body — differs), checked by
# variant_scope + the Lean verifier. Every expect="reject" case carries a refutation
# `witness`: a snippet that ELABORATES against the rival and FAILS on the frozen
# solution, so the rejection is attributable to the spec and not to a tactic script
# that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / refinement.md / instance):
#   implementation_getChildArguments
#     (executable : String) (warnoptions argv : List String)
#     (launchPackage : String) (scriptPresent : Bool)
#     (exeAlt scriptAlt : Option String) : Except String (List String)
#   ONE obligation, `theorem correct_getChildArguments`, and ONE postcondition
#   clause: `result = childArgsSpec executable warnoptions argv launchPackage
#   scriptPresent exeAlt scriptAlt`. A single equality, but `childArgsSpec` is a
#   TOTAL TRANSPARENT function of all seven inputs with four independently
#   observable arms plus a shared prefix, so the clause decomposes into five
#   independent sub-obligations, each attacked separately below:
#     (P) the prefix — the interpreter path followed by one `-W<opt>` token per
#         warning option, in order (`warnPrefix`);
#     (A) launchPackage ≠ ""  => prefix ++ ["-m", launchPackage] ++ argv.tail
#         — the bug-delta: re-invoke the module that was ACTUALLY launched, by its
#         own package label, and carry only the trailing program arguments;
#     (B) launchPackage = "" and scriptPresent => prefix ++ argv (verbatim replay,
#         whole argv, entry script kept);
#     (C) launchPackage = "" and ¬scriptPresent => the alternate-entrypoint
#         fallback chain: the executable alternate ALONE (no prefix) if present,
#         else prefix ++ [scriptAlternate] ++ argv.tail if present;
#     (D) neither alternate present => a diagnostic error, not a success — and the
#         diagnostic's TEXT is part of the clause, not just the `Except` shape:
#         the literal wording plus the script path rendered POSIX-normalized
#         (`posixStr`, per mapping.md). Split into (D-shape) and (D-text) below;
#         an earlier revision of this file claimed (D) whole while only ever
#         attacking the shape, which is what `weak-reworded-diagnostic` adds.
#         (D-text) itself has two independent halves, since the message is a
#         CONCATENATION: the literal wording (`weak-reworded-diagnostic`) and the
#         interpolated path (`weak-diagnostic-drops-path`). Neither reaches the
#         other's half — a length refutation that lets the shared `posixStr`
#         summand cancel is blind to that summand being dropped, so the path
#         component needed its own rival and a witness that pins the path length
#         by hypothesis.
#     (E) the fallback chain's PRECEDENCE: with BOTH alternates present the
#         executable one wins. Distinct from (C), which pins each arm's own shape;
#         no rival reached the point where the two arms compete until
#         `weak-fallback-precedence` below.
#     (F) the warning-option prefix is ORDER-preserving — `warnPrefix` maps over
#         `warnoptions` in order. Distinct from (P), which only pins that the
#         tokens are present at all; `weak-reverse-warnoptions` pins the order.
#
# CARRIER NOTE. The nagini sibling abstracted the same routine to
# `child_arguments(prefix, package_reported, launch_package, argv, script_exists)`
# over PSeq[PSeq[int]], with the interpreter/warning-option prefix PRE-COMPUTED into
# one opaque `prefix` argument and the whole Windows fallback chain collapsed to a
# single `windows_recovery()` sentinel. This backend's carrier is strictly WIDER: the
# prefix is built from `executable` + `warnoptions` inside the modeled function, and
# the fallback chain is spelled out over `exeAlt`/`scriptAlt : Option String`. So
# every nagini case has a counterpart here, and three of nagini's collapsed
# distinctions become newly attackable (see 'assessment'): the warning-option
# prefix, and the two arms of the fallback chain.
#
# Two `nagini` guard inputs fuse into one binder here. nagini carried
# `package_reported : bool` and `launch_package : PSeq[int]` with the guard
# `package_reported and len(launch_package) > 0`; this bundle reifies the same
# observation as the single `launchPackage : String` with the guard
# `launchPackage ≠ ""` (mapping.md derives the encoding). A nagini rival that
# mishandled only `package_reported` is therefore not expressible — there is no
# second toggle to mishandle — and `launchPackage = ""` is exactly that sub-domain,
# which the (B)/(C)/(D) rivals below all probe.
#
# LANES THAT DO NOT PORT (see 'assessment' for the full disposition):
#   * FRAME-MUTATION. Nagini-specific (fractional permissions). Lean is
#     referentially transparent, so a "write into a read-only input" rival is not
#     expressible: the class is genuinely VACUOUS here, not a gap.
#   * DIVERGENCE / non-termination. Also vacuous on lean, and for a structural
#     reason rather than a spec one: `implementation_getChildArguments` is a total
#     Lean `def`, so a diverging implementation cannot be written at all. (This is
#     NOT the velvet situation, where `loom.semantics.termination "partial"` admits
#     such a rival vacuously and it is a known spec hole — the corpus-wide termination-semantics finding.)
#   * ADMISSIBILITY. `correct_getChildArguments` binds all seven inputs with NO
#     precondition hypothesis — every tuple of the seven types is admissible — so
#     nothing here can be PRECOND-TOO-STRONG in the literal sense the nagini
#     sibling's `admiss-self-call` defended (`Requires(len(argv) >= 1)`; this
#     carrier has no such requirement, `argv.tail`/`argv.headD ""` being total on
#     the empty list). But the lane is NOT vacuous, and an earlier revision of this
#     file wrongly recorded it as N/A: the residual question a missing precondition
#     leaves open is whether the obligation is SATISFIABLE at a normal input at all
#     — a postcondition no impl can meet is the same defect one level down. That is
#     expressible here exactly as the astropy lean bundles express it, by
#     discharging the spec predicate at a concrete F2P-shaped tuple as a `have`
#     before the frozen tactic body runs verbatim, and `admiss-ground-module-launch`
#     below does so. (Verified: real build, exit 0.)
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them. There is no
#     consumed axiom and no opaque callee in this bundle anyway (axioms region empty,
#     every impl op R-tagged), so the whole carrier is transparent.
from pathlib import Path

INSTANCE = "django__django-13837"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl-region anchors. Each lies ENTIRELY inside impl-start/impl-end and is
# unique in the file, so region surgery on it cannot touch the spec view.
# ---------------------------------------------------------------------------
_A_SIG = (
    "def implementation_getChildArguments\n"
    "    (executable : String) (warnoptions argv : List String)\n"
    "    (launchPackage : String) (scriptPresent : Bool)\n"
    "    (exeAlt scriptAlt : Option String) : Except String (List String) := Id.run do\n"
)
_A_INIT = "  let mut args : List String := [executable]\n"
_A_LOOP = '  for o in warnoptions do\n    args := args ++ ["-W" ++ o]\n'
_A_MODRET = '    return .ok (args ++ ["-m", launchPackage] ++ argv.tail)\n'
_A_GUARD = '  if launchPackage ≠ "" then\n' + _A_MODRET + "  else if ¬ scriptPresent then\n"
_A_EXE = "    | some exe => return .ok (exe :: argv.tail)\n"
_A_SCRIPT = "      | some sp => return .ok (args ++ [sp] ++ argv.tail)\n"
_A_ERR = ('      | none => return .error ("Script " ++ posixStr (argv.headD "")'
          ' ++ " does not exist.")\n')
_A_FALLBACK = ("    match exeAlt with\n" + _A_EXE + "    | none =>\n"
               "      match scriptAlt with\n" + _A_SCRIPT + _A_ERR)
_A_BODY = (_A_INIT + _A_LOOP + _A_GUARD + _A_FALLBACK
           + "  else\n    return .ok (args ++ argv)")

# The frozen tactic body of `theorem correct_getChildArguments` (inside
# proof-start/proof-end). Only a POSITIVE that reshapes the impl rewrites this; the
# theorem STATEMENT is never touched, so the obligation survives byte-identically.
_A_PROOF = (
    "  intro executable warnoptions argv launchPackage scriptPresent exeAlt scriptAlt\n"
    "  unfold problem_spec_getChildArguments implementation_getChildArguments childArgsSpec\n"
    "  simp only [Id.run, bind, getChildArguments_keyEq]\n"
    "  split <;> rfl"
)
# The frozen `intro` line alone: an admissibility case prepends a ground `have`
# in front of it, leaving the rest of the tactic body — and the STATEMENT — as is.
_A_INTRO = (
    "  intro executable warnoptions argv launchPackage scriptPresent exeAlt scriptAlt\n"
)
for _a in (_A_SIG, _A_INIT, _A_LOOP, _A_MODRET, _A_GUARD, _A_EXE, _A_SCRIPT,
           _A_ERR, _A_FALLBACK, _A_BODY, _A_PROOF, _A_INTRO):
    assert _BASE.count(_a) == 1, f"impl/proof anchor drifted: {_a[:50]!r}"


def _impl(old, new):
    """Rewrite one impl-region anchor, leaving spec AND proof untouched."""
    return _swap(_BASE, old, new)


def _pos(body, proof):
    """A positive control: a new impl body PLUS an honestly re-closed proof.

    The `theorem correct_getChildArguments` statement is never part of either
    anchor, so it stays byte-identical; only the tactic body is rewritten, and no
    new axiom / lemma / `sorry` / `native_decide` is introduced.
    """
    return _swap(_swap(_BASE, _A_SIG + _A_BODY, body), _A_PROOF, proof)


# ---------------------------------------------------------------------------
# Witnesses. The carrier is fully transparent for the four success arms, so a
# witness states the spec predicate at a CONCRETE seven-tuple and `simp` computes
# both sides after the reference description and its prefix helper are unfolded.
# ---------------------------------------------------------------------------
def _wit(args, note):
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_getChildArguments {args}\n"
        f"    (implementation_getChildArguments {args}) := by\n"
        f"  unfold problem_spec_getChildArguments implementation_getChildArguments\n"
        f"    childArgsSpec warnPrefix\n"
        f"  simp"
    )


def _wit_msglen_nopath(args, note, path_expr, path_len, whole_len):
    """A witness for the diagnostic's PATH component, refuted by message LENGTH.

    `_wit_msglen` below pins the diagnostic's WORDING with the normalized path
    still in place, so both sides carry the same opaque `posixStr` summand and it
    cancels. That leaves the path's PRESENCE unattacked: a rival that keeps the
    exact wording and drops the interpolated path is wrong at every input, and no
    length claim about the two literals alone can see it, because the difference
    IS the opaque term.

    So this witness supplies the path's length as a HYPOTHESIS rather than
    computing it (`posixStr` is not kernel-reducible — measured, 13 tactic
    spellings fail on `posixStr "a/" = "a"`), which makes the arithmetic closed on
    both sides: gold's payload is 7 + <path> + 16 and the rival's is a single
    literal. The hypothesis is TRUE at the chosen input (`posixStr "gone"` is
    `"gone"`, length 4), so the gate's consistency probe cannot derive `False`
    from it — the refutation rests on a satisfiable assumption, not a
    contradiction. Verified by the reveal probe: replacing the final `omega` with
    a deliberate type error prints `hl : True` on gold (simp PROVED the lengths
    equal) and `hl : 22 = 7 + 4 + 16` on the rival, so the error tracks the claim.
    """
    return (
        f"-- {note}\n"
        f"example (hp : (posixStr ({path_expr})).length = {path_len}) :\n"
        f"    ¬ problem_spec_getChildArguments {args}\n"
        f"    (implementation_getChildArguments {args}) := by\n"
        f"  unfold problem_spec_getChildArguments implementation_getChildArguments\n"
        f"    childArgsSpec warnPrefix\n"
        f"  intro hspec\n"
        f"  have hl := congrArg (fun e : Except String (List String) =>\n"
        f"    match e with | .error s => s.length | .ok _ => 0) hspec\n"
        f"  simp only [Id.run, bind, ne_eq, not_true_eq_false, reduceIte,\n"
        f"    Bool.not_eq_true, String.length_append, hp,\n"
        f'    show "Script ".length = 7 from by decide,\n'
        f'    show " does not exist.".length = 16 from by decide,\n'
        f"    show {whole_len[0]}.length = {whole_len[1]} from by decide] at hl\n"
        f"  omega"
    )


def _wit_msglen(args, note, lit_len, gold_len):
    """A witness for the DIAGNOSTIC-TEXT clause, refuted by message LENGTH.

    The error arm is the one place `simp` cannot compute both sides. `posixStr`
    is defined over `String.splitOn`, which the kernel will not reduce: `decide`
    reports `did not reduce to isTrue or isFalse` and `simp`/`rfl`/`norm_num`
    leave the `splitOn`/`startsWith` scrutinees intact (measured — every one of
    13 tactic spellings tried failed on `posixStr "a/" = "a"`). So a rival that
    changes only the message WORDING cannot be refuted by evaluating the strings.

    It can be refuted WITHOUT evaluating them: project the `Except` to the LENGTH
    of its error payload. The `posixStr (argv.headD "")` term is shared by rival
    and spec and cancels as an opaque summand, leaving an arithmetic claim about
    the two literal suffixes, which `decide` DOES settle (they are closed string
    literals, no `splitOn` in sight) and `omega` then closes. Gold's build fails
    because with the wording unchanged the two lengths agree and no contradiction
    is derivable — a semantic refutation, not a stuck reduction. Binds nothing,
    so no consistency probe is owed.
    """
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_getChildArguments {args}\n"
        f"    (implementation_getChildArguments {args}) := by\n"
        f"  unfold problem_spec_getChildArguments implementation_getChildArguments\n"
        f"    childArgsSpec warnPrefix\n"
        f"  intro hspec\n"
        f"  have hl := congrArg (fun e : Except String (List String) =>\n"
        f"    match e with | .error s => s.length | .ok _ => 0) hspec\n"
        f"  simp only [Id.run, bind, ne_eq, not_true_eq_false, reduceIte,\n"
        f"    Bool.not_eq_true, String.length_append,\n"
        f'    show {lit_len[0]}.length = {lit_len[1]} from by decide,\n'
        f'    show {gold_len[0]}.length = {gold_len[1]} from by decide] at hl\n'
        f"  omega"
    )


SPEC_TESTS = [

    # ================================================================= soundness
    # Positive controls. Each is a structurally DIFFERENT but fully CORRECT impl
    # that must VERIFY; if one is rejected the postcondition is over-fit to the
    # frozen impl's syntactic form => SPEC-TOO-STRONG.
    {
        "id": "pos-map-prefix",
        "kind": "soundness",
        "expect": "verify",
        # The accumulator LOOP that builds the warning-option prefix is replaced by
        # a direct `map`, and the whole routine becomes a pure `let`/`if` expression
        # instead of an `Id.run do` block with early returns. Same value on every
        # input; a faithful patch could equally be written as a comprehension rather
        # than an append-in-a-loop (the real code uses a comprehension). Because the
        # loop is gone, the frozen proof's three fold/forIn lemmas are no longer
        # needed and the obligation closes by `rfl` — a genuine reproof, not a
        # weakening: the theorem statement is byte-identical and nothing is assumed.
        "module": _pos(
            "def implementation_getChildArguments\n"
            "    (executable : String) (warnoptions argv : List String)\n"
            "    (launchPackage : String) (scriptPresent : Bool)\n"
            "    (exeAlt scriptAlt : Option String) : Except String (List String) :=\n"
            '  let args : List String := executable :: warnoptions.map (fun o => "-W" ++ o)\n'
            '  if launchPackage ≠ "" then\n'
            '    .ok (args ++ ["-m", launchPackage] ++ argv.tail)\n'
            "  else if ¬ scriptPresent then\n"
            "    match exeAlt with\n"
            "    | some exe => .ok (exe :: argv.tail)\n"
            "    | none =>\n"
            "      match scriptAlt with\n"
            "      | some sp => .ok (args ++ [sp] ++ argv.tail)\n"
            '      | none => .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")\n'
            "  else\n"
            "    .ok (args ++ argv)",
            "  intro executable warnoptions argv launchPackage scriptPresent exeAlt scriptAlt\n"
            "  unfold problem_spec_getChildArguments implementation_getChildArguments\n"
            "    childArgsSpec warnPrefix\n"
            "  rfl",
        ),
        "rationale": "structurally-different CORRECT impl: the warning-option prefix "
        "is built by `map` rather than by an accumulating loop, and the body is a "
        "pure expression rather than `Id.run do` with early returns. Identical value "
        "on every seven-tuple, so the single postcondition clause (result = the "
        "reference description) must still hold; the proof is honestly re-closed by "
        "`rfl` with the theorem STATEMENT byte-identical and nothing assumed. If it "
        "FAILS => SPEC-TOO-STRONG (the clause would be over-fit to one prefix-"
        "construction form).",
    },
    {
        "id": "pos-reorder-branches",
        "kind": "soundness",
        "expect": "verify",
        # The branch TREE is restructured: the guard is stated positively
        # (`launchPackage = ""`) and the two non-module arms are handled FIRST, with
        # the module arm falling out last — the mirror image of the frozen order.
        # The prefix is also built by `map`. Same value on every input; only the
        # decision order changes. Re-closed with `grind`.
        "module": _pos(
            _A_SIG
            + _A_INIT
            + '  args := args ++ warnoptions.map (fun o => "-W" ++ o)\n'
            + '  if launchPackage = "" then\n'
            + "    if scriptPresent then\n"
            + "      return .ok (args ++ argv)\n"
            + "    else\n"
            + "      match exeAlt with\n"
            + "      | some exe => return .ok (exe :: argv.tail)\n"
            + "      | none =>\n"
            + "        match scriptAlt with\n"
            + "        | some sp => return .ok (args ++ [sp] ++ argv.tail)\n"
            + '        | none => return .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")\n'
            + "  else\n"
            + '    return .ok (args ++ ["-m", launchPackage] ++ argv.tail)',
            "  intro executable warnoptions argv launchPackage scriptPresent exeAlt scriptAlt\n"
            "  unfold problem_spec_getChildArguments implementation_getChildArguments\n"
            "    childArgsSpec warnPrefix\n"
            "  simp only [Id.run, bind, pure]\n"
            "  grind",
        ),
        "rationale": "structurally-different CORRECT impl: the module-launch guard is "
        "stated POSITIVELY and the two non-module arms are decided first, inverting "
        "the frozen branch order, with the prefix built by `map`. Every arm still "
        "returns the same value, so the postcondition clause must hold; the proof is "
        "honestly re-closed by `grind` with the theorem STATEMENT byte-identical and "
        "nothing assumed. Carries the nagini sibling's `pos-control-reorder` "
        "argument. If it FAILS => SPEC-TOO-STRONG (the clause would pin a branch "
        "ORDER rather than a value).",
    },

    {
        "id": "pos-cheapest-let-bound",
        "kind": "soundness",
        "expect": "verify",
        # Ports the nagini sibling's `pos-control-cheapest`, which an earlier
        # revision of this file dropped without a recorded reason. Each arm's
        # value is bound to an explicitly typed local and then returned, rather
        # than being returned directly — the cheapest correct impl that still does
        # the real work (emits `launchPackage` itself and tails argv). The frozen
        # tactic body is kept VERBATIM, which is the substance of the case: the
        # let-bindings are definitionally transparent, so the frozen proof must
        # still close, and if it did not the clause would be pinning a binding
        # STYLE rather than a value.
        "module": _swap(
            _BASE, _A_BODY,
            _A_INIT + _A_LOOP
            + '  if launchPackage ≠ "" then\n'
            + "    let emitted : Except String (List String) :=\n"
            + '      .ok (args ++ ["-m", launchPackage] ++ argv.tail)\n'
            + "    return emitted\n"
            + "  else if ¬ scriptPresent then\n"
            + "    match exeAlt with\n"
            + "    | some exe =>\n"
            + "      let r : Except String (List String) := .ok (exe :: argv.tail)\n"
            + "      return r\n"
            + "    | none =>\n"
            + "      match scriptAlt with\n"
            + "      | some sp =>\n"
            + "        let r : Except String (List String) :=\n"
            + "          .ok (args ++ [sp] ++ argv.tail)\n"
            + "        return r\n"
            + "      | none =>\n"
            + "        let r : Except String (List String) :=\n"
            + '          .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")\n'
            + "        return r\n"
            + "  else\n"
            + "    let whole : Except String (List String) := .ok (args ++ argv)\n"
            + "    return whole"),
        "rationale": "cheapest CORRECT impl: every arm's result is bound to an "
        "explicitly typed local before being returned, and the frozen tactic body is "
        "kept verbatim. Identical value on every seven-tuple, so the single "
        "postcondition clause must still hold. Ports nagini's "
        "`pos-control-cheapest`, the one nagini positive this file previously "
        "dropped. If it FAILS => SPEC-TOO-STRONG (the clause would pin how a branch "
        "result is BOUND rather than what it is).",
    },

    # ============================================================== admissibility
    # Ported from the nagini sibling's `admiss-self-call`, which an earlier revision
    # of this file wrongly recorded as an inexpressible lane (see the header). The
    # nagini case defended a literal `Requires`; this carrier has none, so what
    # survives the port is the residual question a missing precondition leaves open
    # — is the obligation SATISFIABLE at a normal input, or is the postcondition one
    # no impl can meet? Discharged the way the astropy lean bundles discharge it: a
    # ground instance of the spec predicate at an F2P-shaped tuple, proved as a
    # `have` PREPENDED to the frozen tactic body, which then runs verbatim. Nothing
    # is assumed — no new declaration, no axiom, statement byte-identical, and the
    # `have` is inside the existing proof rather than replacing any of it.
    {
        "id": "admiss-ground-module-launch",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _A_INTRO,
            '  have _ground : problem_spec_getChildArguments "py" [] ["m.py", "runserver"]\n'
            '      "utils.mod" true none none\n'
            '      (implementation_getChildArguments "py" [] ["m.py", "runserver"]\n'
            '        "utils.mod" true none none) := by\n'
            "    unfold problem_spec_getChildArguments implementation_getChildArguments\n"
            "      childArgsSpec warnPrefix\n"
            "    simp\n"
            + _A_INTRO),
        "rationale": "the obligation is discharged at a concrete F2P-shaped module "
        "launch of a package other than the built-in one (argv of length 2, no "
        "warning options, no alternates) as a `have`, then the frozen obligation is "
        "closed verbatim. Verifies — so the modeled behaviour is satisfiable at "
        "exactly a normal input and the single postcondition clause is not vacuously "
        "unmeetable. If it FAILED, the clause would be unsatisfiable at a normal "
        "input, which is the analogue of PRECOND-TOO-STRONG on a carrier with no "
        "precondition to weaken. Ports nagini's `admiss-self-call`.",
    },

    # ================================================================= uniqueness
    # Rivals. Each shares the frozen spec, edits only the impl region, and carries a
    # witness that ELABORATES against it and FAILS on gold. Grouped by the
    # sub-obligation of the single postcondition clause each one attacks.

    # ---- (A) the module-relaunch arm: the bug-delta itself ----
    {
        "id": "weak-constant-package",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_A_MODRET,
                        '    return .ok (args ++ ["-m", "django"] ++ argv.tail)\n'),
        "refinement": "this is the PRE-PATCH behaviour: the relaunch always names one "
        "fixed built-in package label instead of the one that was actually launched. "
        "The F2P test_run_as_non_django_module launches a module whose package label "
        "is `utils_tests.test_module` and asserts the child vector contains `'-m', "
        "'utils_tests.test_module'`; a patch emitting the fixed label produces `-m "
        "django` and FAILS the F2P — it does NOT resolve, because it IS the behaviour "
        "the change removes. Correct only on the sub-domain where the launched label "
        "happens to equal that one literal.",
        "rationale": "REJECTED by sub-obligation (A): the emitted label must be "
        "`launchPackage` ITSELF, and a constant differs at every module launch of any "
        "other package. Attacks the launchPackage binder on its non-empty sub-domain. "
        "If it VERIFIES => SPEC-TOO-WEAK (the whole point of the change would be "
        "unpinned).",
        # launchPackage = "pkg": gold emits "-m pkg", rival emits "-m django".
        "witness": _wit('"py" [] ["s.py", "runserver"] "pkg" true none none',
                        "module launch of a package other than the built-in one"),
    },
    {
        "id": "weak-no-module-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_A_GUARD, "  if ¬ scriptPresent then\n"),
        "refinement": "this deletes the module-relaunch arm entirely, so EVERY launch "
        "is treated as a plain script launch and falls through to verbatim replay. "
        "The F2P asserts the child vector is `[executable, '-m', "
        "'utils_tests.test_module', 'runserver']`; this yields `[executable, "
        "<entry script>, 'runserver']` instead, so it FAILS the F2P. The P2P "
        "test_run_as_module (the built-in module launch) breaks the same way. Does "
        "NOT resolve.",
        "rationale": "REJECTED by sub-obligation (A): on a module launch the result "
        "must be prefix ++ ['-m', launchPackage] ++ argv.tail, but this returns the "
        "(B) shape prefix ++ argv. Attacks the launchPackage binder's non-empty "
        "sub-domain from the other side (the arm is never taken at all). If it "
        "VERIFIES => SPEC-TOO-WEAK.",
        # A different executable, package label and script name from the case above,
        # so the two rivals are refuted at genuinely distinct points.
        "witness": _wit('"python3" [] ["m.py", "runserver"] "utils.mod" true none none',
                        "module launch: gold re-invokes the module, rival replays argv"),
    },
    {
        "id": "weak-keep-entry-script",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_A_MODRET,
                        '    return .ok (args ++ ["-m", launchPackage] ++ argv)\n'),
        "refinement": "this carries the WHOLE argument vector into the relaunch "
        "instead of only its trailing program arguments, so the entry script is "
        "duplicated after the module name: the child is invoked as `-m PKG "
        "<entry script> runserver` rather than `-m PKG runserver`. The F2P asserts "
        "exactly `[executable, '-m', 'utils_tests.test_module', 'runserver']` with no "
        "entry-script element, so the extra element FAILS the assertion. Does NOT "
        "resolve. A near-miss: the label and flag are right, only the tail is wrong, "
        "which is why it is refuted at its own input rather than sharing one.",
        "rationale": "REJECTED by sub-obligation (A): the tail must be `argv.tail`, "
        "but this passes `argv`, adding one extra element for every argv with a head. "
        "Attacks the argv binder (its head/tail split) on the module-launch arm, and "
        "varies warnoptions to a non-empty list so the prefix is live at the same "
        "time. If it VERIFIES => SPEC-TOO-WEAK.",
        # warnoptions non-empty here, so the '-W' prefix is exercised alongside the
        # off-by-one; gold => [py, -Werror, -m, pkg, runserver].
        "witness": _wit('"py" ["error"] ["e.py", "runserver"] "pkg" true none none',
                        "entry script duplicated into the relaunch tail"),
    },
    {
        "id": "weak-wrong-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_A_MODRET,
                        '    return .ok (args ++ ["-c", launchPackage] ++ argv.tail)\n'),
        "refinement": "this emits a different interpreter option before the package "
        "label. A faithful patch doing so would hand the child an option that does "
        "not run a package as a module at all, so the relaunched process would not "
        "start. Both the F2P and the P2P test_run_as_module assert the option is "
        "exactly `-m`, so a different one FAILS them. Does NOT resolve.",
        "rationale": "REJECTED by sub-obligation (A): the token preceding the label "
        "must be `\"-m\"`. Attacks the same arm at a DIFFERENT point from the other "
        "(A) rivals — a length-ONE argv (empty tail) and scriptPresent = false — "
        "which also demonstrates that the short-argv sub-domain is admissible rather "
        "than excluded by a precondition (the lane the nagini sibling's "
        "admissibility case defended). If it VERIFIES => SPEC-TOO-WEAK.",
        # argv length 1 => argv.tail = []; scriptPresent false is irrelevant on this
        # arm, which is exactly the point: the module arm must win regardless.
        "witness": _wit('"py" [] ["s.py"] "a" false none none',
                        "single-element argv, module launch: wrong option token"),
    },
    {
        "id": "weak-drop-prefix-on-module-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_A_MODRET,
                        '    return .ok (["-m", launchPackage] ++ argv.tail)\n'),
        "refinement": "this omits the interpreter-and-warning-option prefix on the "
        "relaunch arm, returning a vector that begins with the option token and has "
        "no interpreter path at all — the child could not be executed. The F2P and "
        "the P2P test_run_as_module both assert the vector STARTS with the "
        "interpreter path, so omitting it FAILS them. Does NOT resolve.",
        "rationale": "REJECTED by sub-obligations (P)+(A) jointly: the relaunch must "
        "be prefixed by `warnPrefix executable warnoptions`. Attacks the executable "
        "and warnoptions binders on the module arm, at a third distinct point (a "
        "different executable, a different warning option, a different trailing "
        "argument). If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _wit('"exe" ["all"] ["s.py", "x"] "p" true none none',
                        "relaunch without the interpreter/warning-option prefix"),
    },

    # ---- (P) the shared prefix. NEWLY attackable on this carrier: nagini received
    # the prefix pre-computed as one opaque argument, so no nagini rival could get
    # it wrong. Here it is built inside the modeled function from two binders.
    {
        "id": "weak-drop-warnoptions",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_A_LOOP, ""),
        "refinement": "this drops the per-warning-option tokens from the prefix, so "
        "the relaunched child loses the active warning configuration. The P2P "
        "test_warnoptions runs with one warning option active and asserts the child "
        "vector is `[executable, '-Werror', <script>, 'runserver']`; with the tokens "
        "gone the vector lacks `-Werror` and the assertion FAILS, so the instance "
        "does NOT resolve even though the F2P (which runs with no warning options "
        "active, where dropping them is a no-op) would still pass. That asymmetry is "
        "the point: it is correct on exactly the sub-domain the F2P probes and wrong "
        "off it.",
        "rationale": "REJECTED by sub-obligation (P): the prefix must be `executable "
        ":: warnoptions.map (fun o => \"-W\" ++ o)`, but this returns `[executable]` "
        "whenever warnoptions is non-empty. Attacks the warnoptions binder — the one "
        "the nagini carrier could not expose, since it received the prefix already "
        "assembled. If it VERIFIES => SPEC-TOO-WEAK.",
        # Non-empty warnoptions on the verbatim-replay arm, so only the prefix
        # differs: gold => [py, -Werror, t.py, runserver]; rival => [py, t.py, runserver].
        "witness": _wit('"py" ["error"] ["t.py", "runserver"] "" true none none',
                        "active warning option dropped from the prefix"),
    },

    # ---- (B)/(C) the non-module arms: which one fires on which input ----
    {
        "id": "weak-invert-script-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_A_GUARD,
                        '  if launchPackage ≠ "" then\n' + _A_MODRET
                        + "  else if scriptPresent then\n"),
        "refinement": "this inverts the presence test on the non-module path, so the "
        "two non-module outcomes swap: a launch whose entry script IS present takes "
        "the alternate-entrypoint fallback, and one whose script is ABSENT is "
        "replayed verbatim. Both directions break P2P tests — test_warnoptions "
        "launches a script that exists and asserts verbatim replay (this would "
        "instead go down the fallback chain), while test_exe_fallback and "
        "test_entrypoint_fallback launch a script that does not exist and assert the "
        "fallback result (this would instead replay). Does NOT resolve.",
        "rationale": "REJECTED by sub-obligations (B)+(C): on `launchPackage = \"\"` "
        "the arm is selected by `¬ scriptPresent`, and this selects on "
        "`scriptPresent`. Attacks the scriptPresent binder directly, and is the only "
        "rival that holds launchPackage empty while scriptPresent is true AND an "
        "executable alternate is present — so it also varies exeAlt away from `none` "
        "on an arm where gold must ignore it. Carries the nagini sibling's "
        "`weak-swap-nonmodule` argument. If it VERIFIES => SPEC-TOO-WEAK.",
        # scriptPresent = true with an executable alternate present: gold replays argv
        # verbatim (ignoring the alternate), the rival returns the alternate.
        "witness": _wit('"py" [] ["s.py", "runserver"] "" true (some "alt.exe") none',
                        "script present: gold replays verbatim, rival takes the fallback"),
    },
    {
        "id": "weak-exe-alt-with-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_A_EXE,
                        "    | some exe => return .ok (args ++ [exe] ++ argv.tail)\n"),
        "refinement": "the executable alternate must be invoked DIRECTLY, without the "
        "interpreter prefix — it is itself an executable. This prepends the prefix, "
        "so the child would be launched as `<interpreter> <alternate> ...`. The P2P "
        "test_exe_fallback asserts exactly `[<alternate>, 'runserver']` with no "
        "interpreter element, so the extra elements FAIL it. Does NOT resolve.",
        "rationale": "REJECTED by sub-obligation (C): the executable-alternate arm is "
        "`exe :: argv.tail`, with NO prefix, unlike the script-alternate arm which "
        "has one. Attacks the exeAlt binder on its `some` sub-domain, with "
        "warnoptions non-empty so the wrongly-added prefix is observable. This "
        "distinction is invisible on the nagini carrier, which collapsed both "
        "fallback arms into a single sentinel. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _wit('"py" ["error"] ["dj", "runserver"] "" false (some "dj.exe") none',
                        "executable alternate wrongly prefixed by the interpreter"),
    },
    {
        "id": "weak-script-alt-without-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_A_SCRIPT,
                        "      | some sp => return .ok (sp :: argv.tail)\n"),
        "refinement": "the mirror error: the script alternate is an ordinary script "
        "and must be run BY the interpreter, so its arm keeps the prefix. This drops "
        "it, yielding a vector with no interpreter path. The P2P "
        "test_entrypoint_fallback asserts `[executable, <alternate>, 'runserver']`, "
        "so dropping the interpreter FAILS it. Does NOT resolve.",
        "rationale": "REJECTED by sub-obligation (C): the script-alternate arm is "
        "prefix ++ [sp] ++ argv.tail. Attacks the scriptAlt binder on its `some` "
        "sub-domain, at the only input where that arm's own SHAPE is observable: "
        "exeAlt = none, so the script alternate is actually taken (the other rival "
        "that moves scriptAlt off `none`, weak-fallback-precedence, holds exeAlt at "
        "`some` and so tests arm ORDER rather than this arm's contents). "
        "Paired with weak-exe-alt-with-prefix this pins the prefix asymmetry between "
        "the two fallback arms in both directions. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _wit('"py3" [] ["dj", "runserver"] "" false none (some "dj-script.py")',
                        "script alternate wrongly stripped of the interpreter prefix"),
    },

    # ---- (D) the failure arm: an error, not a success ----
    {
        "id": "weak-no-diagnostic",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_A_ERR, "      | none => return .ok (args ++ argv)\n"),
        "refinement": "when the entry script is absent and NEITHER alternate exists, "
        "the routine must fail with a diagnostic. This silently succeeds instead, "
        "replaying an argument vector whose entry script is known not to exist — the "
        "reloader would spawn a child that immediately dies. The P2P "
        "test_raises_runtimeerror launches a non-existent script with no alternates "
        "and asserts the error is raised, so a patch that returns normally FAILS it. "
        "Does NOT resolve.",
        "rationale": "REJECTED by sub-obligation (D): the result must be an `error`, "
        "and this returns an `ok`. The only rival that attacks the SHAPE of the "
        "`Except` rather than the contents of a success; the other rivals refuted "
        "with scriptPresent = false and BOTH alternates `none` (weak-wrong-flag, "
        "weak-reworded-diagnostic) reach that input on a different clause — the "
        "module arm and the diagnostic TEXT respectively — so neither pins that the "
        "failure arm reports at all. If it VERIFIES => "
        "SPEC-TOO-WEAK (the routine could silently succeed where it must report).",
        "witness": _wit('"py" [] ["gone", "runserver"] "" false none none',
                        "no script and no alternates: gold reports, rival succeeds"),
    },
    {
        "id": "weak-reworded-diagnostic",
        "kind": "uniqueness",
        "expect": "reject",
        # (D-text). weak-no-diagnostic above pins only the Except SHAPE — that the
        # failure arm reports rather than succeeds. It says nothing about WHAT is
        # reported, so a rival keeping `.error` and changing the wording was
        # unattacked. This one keeps the arm, keeps the normalized path, and changes
        # only the trailing literal.
        "module": _impl(
            _A_ERR,
            '      | none => return .error ("Script " ++ posixStr (argv.headD "")'
            ' ++ " not found.")\n'),
        "refinement": "the diagnostic is a user-facing message with fixed wording. "
        "This reports the same path with a different trailing phrase. The P2P "
        "test_raises_runtimeerror matches the raised message, so a patch rewording "
        "it FAILS that assertion even though the failure is still signalled — the "
        "arm is reached, the error is raised, and only the text differs. Does NOT "
        "resolve. The strictest near-miss in the battery: everything about the "
        "control flow is right.",
        "rationale": "REJECTED by sub-obligation (D-text): the message must be "
        "exactly `\"Script \" ++ posixStr (argv.headD \"\") ++ \" does not exist.\"`, "
        "and this substitutes the final literal. Attacks the one part of the spec no "
        "other rival reaches — `weak-no-diagnostic` replaces the arm wholesale, so "
        "the CONTENT of the error was previously unpinned. If it VERIFIES => "
        "SPEC-TOO-WEAK (the diagnostic text would be unconstrained). Refuted by "
        "message length, since `posixStr` is not kernel-reducible; see _wit_msglen.",
        "witness": _wit_msglen(
            '"py" [] ["gone"] "" false none none',
            "failure arm reached, diagnostic reworded: refuted on message length",
            ('" not found."', 11), ('" does not exist."', 16)),
    },

    {
        "id": "weak-diagnostic-drops-path",
        "kind": "uniqueness",
        "expect": "reject",
        # (D-text), the PATH half. weak-reworded-diagnostic keeps the interpolated
        # path and changes the wording, so the two payloads share the opaque
        # `posixStr` summand and it cancels — which leaves the path's PRESENCE
        # unpinned. This rival keeps the wording exactly and drops the path, so it
        # is wrong at EVERY input reaching the failure arm, and no rival previously
        # in the battery could see it.
        "module": _impl(
            _A_ERR,
            '      | none => return .error "Script does not exist."\n'),
        "refinement": "the diagnostic must name the script it could not find; this "
        "reports a message with the path omitted entirely. The P2P "
        "test_raises_runtimeerror matches the raised message against one naming the "
        "missing script, so a patch that drops the path FAILS that assertion even "
        "though the failure is still signalled with the right surrounding wording. "
        "Does NOT resolve. Wrong on the whole failure sub-domain rather than a "
        "corner of it, and invisible to a length argument that lets the shared "
        "normalized path cancel.",
        "rationale": "REJECTED by sub-obligation (D-text): the message must be "
        "`\"Script \" ++ posixStr (argv.headD \"\") ++ \" does not exist.\"`, and this "
        "drops the middle summand. Attacks the argv binder's HEAD on the failure arm "
        "— the component `weak-reworded-diagnostic` structurally cannot reach, since "
        "its refutation depends on that summand cancelling. If it VERIFIES => "
        "SPEC-TOO-WEAK (the diagnostic need not say WHICH script is missing). "
        "Refuted on message length with the non-reducible path length supplied as a "
        "satisfiable hypothesis; see _wit_msglen_nopath.",
        "witness": _wit_msglen_nopath(
            '"py" [] ["gone"] "" false none none',
            "diagnostic path dropped: refuted on message length at a "
            "hypothesised path length",
            '["gone"].headD ""', 4, ('"Script does not exist."', 22)),
    },

    # ---- (E) the fallback chain's PRECEDENCE, where the two arms COMPETE ----
    {
        "id": "weak-fallback-precedence",
        "kind": "uniqueness",
        "expect": "reject",
        # The (C) rivals each reshape ONE arm, and each is refuted at an input where
        # only that arm is live (exeAlt some / scriptAlt none, or the reverse). So
        # neither reaches the input where BOTH alternates exist and the chain has to
        # choose. This rival keeps both arms byte-correct and only swaps the ORDER in
        # which they are consulted, so it is wrong on exactly that overlap.
        "module": _impl(
            _A_FALLBACK,
            "    match scriptAlt with\n"
            "    | some sp => return .ok (args ++ [sp] ++ argv.tail)\n"
            "    | none =>\n"
            "      match exeAlt with\n"
            "      | some exe => return .ok (exe :: argv.tail)\n"
            '      | none => return .error ("Script " ++ posixStr (argv.headD "")'
            ' ++ " does not exist.")\n'),
        "refinement": "the fallback chain probes the executable alternate FIRST and "
        "only then the script alternate; this reverses the two. When just one exists "
        "the behaviour is unchanged, which is why it survives the other fallback "
        "tests — but when BOTH exist the wrong entrypoint is chosen: the child is "
        "launched via the interpreter and the script alternate instead of running "
        "the executable one directly. The P2P test_exe_fallback asserts the "
        "executable alternate is the one taken, so a patch reversing the chain FAILS "
        "it on any launch where both entrypoints are installed side by side. Does "
        "NOT resolve.",
        "rationale": "REJECTED by sub-obligation (E): `childArgsSpec` matches on "
        "`exeAlt` in the OUTER position, so the executable alternate wins whenever "
        "both are present. Both arms here are individually correct — this is the "
        "only rival in the battery that is wrong purely about arm PRECEDENCE, and "
        "the only one refuted with both `exeAlt` and `scriptAlt` at `some`, an input "
        "no other case reaches. If it VERIFIES => SPEC-TOO-WEAK (the chain's order "
        "would be unpinned). This distinction is invisible on the nagini carrier, "
        "which collapsed the whole chain into one sentinel.",
        "witness": _wit(
            '"py" [] ["dj", "runserver"] "" false (some "a.exe") (some "b-script.py")',
            "both alternates present: gold takes the executable one, rival the script one"),
    },

    # ---- (F) the warning-option prefix is ORDER-preserving ----
    {
        "id": "weak-reverse-warnoptions",
        "kind": "uniqueness",
        "expect": "reject",
        # weak-drop-warnoptions pins that the tokens are PRESENT; it is refuted at a
        # single warning option, where presence and order are the same fact. This
        # rival emits every token, so it is correct on that whole sub-domain, and is
        # wrong only once two or more options are active.
        "module": _impl(
            _A_LOOP,
            '  for o in warnoptions.reverse do\n    args := args ++ ["-W" ++ o]\n'),
        "refinement": "the warning options are emitted in reverse. Order matters "
        "here: warning filters are applied in sequence and a later `-W` can override "
        "an earlier one, so reversing them can change which filter ultimately wins "
        "and hand the child a different warning configuration than the parent ran "
        "with. The P2P test_warnoptions runs with warning options active and asserts "
        "the child vector's `-W` tokens in order, so a patch reversing them FAILS it "
        "whenever more than one is active. Correct on the sub-domain of zero or one "
        "option — which is the only sub-domain the other prefix rival probes — and "
        "wrong off it. Does NOT resolve.",
        "rationale": "REJECTED by sub-obligation (F): `warnPrefix` is `executable :: "
        "warnoptions.map (fun o => \"-W\" ++ o)`, which preserves the input order, "
        "and this maps over `warnoptions.reverse`. The only rival refuted at TWO "
        "distinct warning options, so it is the only one that pins order rather than "
        "mere presence. If it VERIFIES => SPEC-TOO-WEAK (any permutation of the "
        "warning configuration would satisfy the spec).",
        "witness": _wit('"py" ["one", "two"] ["s.py"] "" true none none',
                        "two distinct warning options: gold keeps order, rival reverses"),
    },
]


# No @ContractOnly-style axioms and no opaque callees: the axioms region is empty
# and every impl op is an R-tagged concrete refinement, so the axiom lane is vacuous
# here and belongs to G-AX regardless.
AXIOM_TESTS = []
