"""properties.py — G-PBT falsification battery for django__django-14311 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct relaunchCommand`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method assembling a relaunch argument vector):

  relaunchCommand (leadingArgs : List String) (moduleName : String)
      (parentPackage : String) (trailingArgs : List String)
      return (cmdline : List String)
    ensures cmdline =
      leadingArgs ++ ["-m", moduleToReexec moduleName parentPackage] ++ trailingArgs

``moduleToReexec`` is a total, fully-unfolded pure ``def`` of the two string
inputs (the ``axioms`` region is empty — there is NO opaque oracle to echo):

  moduleToReexec moduleName parentPackage =
    if ((moduleName == "__main__") || moduleName.endsWith ".__main__")
          && parentPackage ≠ ""
    then parentPackage else moduleName

The single top-level ``ensures`` clause pins two INDEPENDENT things, each
grounded in the actual inputs:

  (V) the CHOSEN dotted name element = ``moduleToReexec moduleName parentPackage``,
      whose decision has three behaviour sub-domains grounded in ``moduleName``
      and ``parentPackage``:
        (1) NOT a package-entry name              -> the name itself
        (2) package-entry name AND a parent present -> the parent package
        (3) package-entry name AND NO parent       -> the name itself (parent
            ignored, one-or-more not zero-or-more)
  (S) the ASSEMBLY structure: the chosen name is wrapped by the ``"-m"`` switch
      literal and framed verbatim by the read-only ``leadingArgs`` prefix and
      ``trailingArgs`` suffix.

FOUR input binders — ``leadingArgs``, ``moduleName``, ``parentPackage``,
``trailingArgs`` — all varied by the reject witnesses (see BINDER / POINT
COVERAGE). ``moduleName`` / ``parentPackage`` are the load-bearing binders (the
name choice under change); ``leadingArgs`` / ``trailingArgs`` are the read-only
surrounding carriers the assembly must forward verbatim.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY
    read-only frame rival (write into ``name`` held at ``Acc(list_pred(name),
    1/2)``) because a Viper impl can illegally overwrite a fractional-permission
    input. Lean and Velvet are referentially transparent: every parameter here is
    an immutable value, this bundle declares NO ``mut`` binder over any input,
    there is no heap and no aliasing — so there is no read-only input to overwrite
    and no permission system to trip. The class is vacuous; no substitute is
    fabricated (per the porting map).
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the heart of the port. The three
    nagini partial-domain rivals re-express directly onto the (V) name-choice
    sub-domains; a fourth (added by the audit) splits the package-entry
    classifier and attacks its dotted-sentinel DISJUNCT on its own. FOUR ADDED
    structural rivals attack the (S) assembly (the extra ``leadingArgs`` /
    ``trailingArgs`` / ``"-m"`` structure the nagini single-list model never
    carried) — three by deleting a part, one by transposing the carriers while
    keeping every element.
  * UNGROUNDED-ORACLE ECHO — N/A. ``moduleToReexec`` is a concrete ``def`` over
    the method's own inputs (no opaque answer key); the cheapest correct impl
    simply evaluates it, which the positive controls cover honestly. Any wrong
    constant/echo fails the sole clause.
  * DIVERGENCE / NON-TERMINATION - nothing to ship here, but NOT because the
    carrier cannot express it and NOT because the spec admits it. This slot has now
    been corrected twice, and the second correction is what is withdrawn.
    (i) The original port justified the omission with "a Velvet do-block cannot
    express a diverging computation over this carrier". That is false: a rival owns
    the whole impl region and can splice a loop of its own.
    (ii) The audit then accepted that but said this bundle sets
    ``loom.semantics.termination "partial"``, so a non-terminating impl satisfies
    every ``ensures`` VACUOUSLY and VERIFIES, and recorded an escalated hole in the
    frozen spec measured over a supposed ``partial`` cohort. Also false. Line 4 of the
    frozen ``Solution.lean`` reads ``"total"``, the file's only correctness ``open``
    is ``open TotalCorrectness DemonicChoice``, and the two cannot disagree because
    the ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). The census had no referent:
    all 500 velvet bundles set ``"total"``.
    What is true. Under ``total`` a postcondition is claimed of ALL runs, not only
    terminating ones, and the verifier demands a decreasing measure on every loop.
    Measured on this bundle with the proof reduced to a bare ``loom_solve``: an
    unmeasured spun loop is refused at elaboration (``Decreasing annotations are
    required in total correctness semantics``), and the sharper shape that CARRIES a
    measure which does not decrease (``while q > 0 / invariant 0 ≤ q /
    done_with q = 0 / decreasing q`` with body ``q := q``) is REJECTED on the
    measure's own goal - ``case «decreasing_1: q»``, residual ``⊢ q < q``. So a
    diverging rival DOES violate this spec, nothing is escalated, and the frozen
    artifact needs no change.
    Why still nothing ships. The obstruction is the WITNESS CONTRACT, not the spec:
    a reject case's witness must ELABORATE against its rival, and a rejected
    diverging rival's module does not compile at all (the obligation fails at the
    ``method`` itself, ahead of any appended tester), so the gate would return
    ``witness-unproven`` -> INCONCLUSIVE rather than a rejection. The nagini sibling
    That is the shape with NO measure. A rival that CARRIES a measure which
    does not decrease is refused at the ``prove_correct`` site instead, which
    the witness file strips, so that module does elaborate; but its post-image
    is then an unreduced ``forIn Lean.Loop.mk`` term carrying
    ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
    kernel will not normalise to a value a concrete-input tester can decide.
    Both shapes therefore land ``witness-unproven``.
    additionally carries no diverge-* / nonterm-* / weak-diverge case, so there was
    nothing to port either.

WITNESS PLACEMENT. Each reject rival carries a machine-checked refutation
``witness`` — a Velvet tester statement at ONE concrete input
(``relaunchCommandTester ... = false`` says the extracted program violates the
method's postcondition there), checked in a file whose ``prove_correct`` block
has been stripped so no tactic script can mask the verdict.

  * The name-choice sub-domains (1)/(3) and the four structural rivals use
    literal inputs the tester ``decide``s directly.
  * ``String.endsWith`` reduces under ``decide`` only for SHORT arguments on this
    carrier. SECOND-AUDIT MEASUREMENT (a matrix of literals x
    ``decide``/``decide +kernel``/``rfl``/``simp``): the underlying
    ``Substring`` equality gets stuck in the kernel past a length threshold, so
    ``"foo.bar.baz"`` and every ``<pkg>.__main__`` spelling stall, while
    ``"m"``, ``"a.b"``, ``"a.b.c"`` and ``"a.b.c.d"`` all decide. That threshold —
    not "endsWith is opaque" — is the real carrier fact, and it changes which
    witnesses need conditioning:
      - ``weak-prepatch`` (sub-domain (1)) is stated UNCONDITIONED, at the
        deeper dotted module ``"a.b.c"`` with parent ``"a.b"``. The first port
        conditioned this one on an ``endsWith`` hypothesis because its literal
        was long enough to stall; the second audit shortened the literal to an
        equally F2P-shaped point that decides, which is strictly stronger — there
        is no hypothesis left whose satisfiability has to be argued.
      - ``weak-drop-dotted-disjunct`` (the dotted disjunct) is the ONE witness
        that must still be CONDITIONED: its point is a NESTED package-entry name,
        so ``moduleName`` necessarily ends with the dotted sentinel, and every
        such spelling stalls (re-measured: ``".__main__"``, ``"a.__main__"``,
        ``"p.__main__"`` all stick at the ``Decidable`` instance, and supplying
        the step as a ``decide +kernel``/``simp`` rewrite does not close it
        either). It assumes the single TRUE ``endsWith`` fact ``h`` about its
        literal and rewrites with it before deciding the residual assembly goal.
        ``h`` is the ACTUAL truth about that string, so it is trivially
        satisfiable and the gate's inconsistency probe cannot derive ``False``
        from it (machine-checked: probe EXIT 1, ``simp_all made no progress``).

All eight witnesses probe eight DISTINCT input tuples; the two positive controls
defend the whole obligation and the admissibility case pins the name choice at
one input per (V) sub-domain. Each witness was machine-checked with two real
builds to ELABORATE against its rival and FAIL against the frozen solution —
re-run independently by two audits, the second of which additionally built the
FLIPPED claim of every witness against the frozen solution to prove gold's exit
code tracks the claim rather than the file (all eight flip to EXIT 0).

AXIOM lane: dropped (``AXIOM_TESTS = []``). The bundle consumes NO axiom —
``moduleToReexec`` is a deep model over primitive string ops, validated
out-of-band by G-CONF; there is no A-reference callee (mapping.md §3). The G-PBT
gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-14311"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen do-block body. Lies wholly inside
# ---- the single `-- impl-start`/`-- impl-end` region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap), so each edit keeps
# ---- markers.same_spec True by construction and leaves the frozen
# ---- `prove_correct relaunchCommand` statement byte-identical.
_IMPL = (
    "    let mut cmdline := leadingArgs\n"
    "    let name : String :=\n"
    "      if ((moduleName == \"__main__\") || moduleName.endsWith \".__main__\")\n"
    "            && parentPackage ≠ \"\"\n"
    "      then parentPackage\n"
    "      else moduleName\n"
    "    cmdline := cmdline ++ [\"-m\", name]\n"
    "    cmdline := cmdline ++ trailingArgs\n"
    "    return cmdline"
)
assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen impl.
# ---- A positive control that reshapes the impl into a straight-line assembly
# ---- retunes the tactic body; both the impl region and the `prove_correct` body
# ---- are elided from the spec view, so same_spec still holds and the obligation
# ---- survives with an identical statement. Unique in the file.
_PROOF = (
    "prove_correct relaunchCommand by\n"
    "  loom_solve\n"
    "  simp_all [moduleToReexec]"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced
    (frozen tactic script kept — used for reject rivals, expected NOT to
    verify)."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """Reshape the impl region AND retune the tactic body (soundness positive
    whose reshaped impl no longer matches the frozen script)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `relaunchCommandTester leadingArgs moduleName parentPackage trailingArgs
# ---- = false` says the extracted program's result violates the method's
# ---- postcondition at that concrete input. Checked in a file whose
# ---- `prove_correct` block has been stripped by the gate.
def _tester(body):
    return ("extract_program_for relaunchCommand\n"
            "prove_precondition_decidable_for relaunchCommand\n"
            "prove_postcondition_decidable_for relaunchCommand\n"
            "derive_tester_for relaunchCommand\n\n" + body)


# ---- Conditioned-witness tactic. For a non-empty argument, `String.endsWith`
# ---- does NOT reduce under `decide` (the underlying `Substring` equality is
# ---- stuck in the kernel), so the witness ASSUMES the single true `endsWith`
# ---- fact `h` about its concrete `moduleName` and rewrites with it, which frees
# ---- the residual assembly goal to `decide`.
_COND_TAC = (
    "  simp only [relaunchCommandTester, relaunchCommandExec, relaunchCommand,\n"
    "    moduleToReexec, h]\n"
    "  decide\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Both confirmed EXIT 0 (bash scripts/lean_verify.sh).
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: evaluate the whole assembly in one straight-line expression,
        # naming the chosen dotted name via the pure `moduleToReexec` directly
        # (no imperative `mut` accumulation). Trivially matches the sole clause;
        # the reshaped straight-line impl closes with a bare `loom_solve`.
        "module": _impl_proof(
            "    return leadingArgs ++ [\"-m\", moduleToReexec moduleName "
            "parentPackage] ++ trailingArgs",
            "prove_correct relaunchCommand by\n  loom_solve"),
        "rationale": (
            "a straight-line evaluation of the pinned assembly is the simplest "
            "correct impl and must satisfy the sole clause "
            "`cmdline = leadingArgs ++ [\"-m\", moduleToReexec ...] ++ "
            "trailingArgs` (covering both the (V) name choice and the (S) "
            "assembly). If it fails to verify the spec is SPEC-TOO-STRONG (a "
            "faithful correct impl rejected). Also shows the spec is not "
            "echo-vulnerable: any wrong constant/echo fails the equality."
        ),
    },
    {
        "id": "pos-control-single-append",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the inline name-choice `if`, but assemble the whole
        # command vector in ONE `++` chain bound to a local instead of two
        # sequential `mut` appends. Observationally identical; a distinct
        # executable surface that still matches the frozen tactic script.
        "module": _impl(
            "    let name : String :=\n"
            "      if ((moduleName == \"__main__\") || moduleName.endsWith \".__main__\")\n"
            "            && parentPackage ≠ \"\"\n"
            "      then parentPackage\n"
            "      else moduleName\n"
            "    let cmdline := leadingArgs ++ [\"-m\", name] ++ trailingArgs\n"
            "    return cmdline"),
        "rationale": (
            "assembling the command vector in a single `++` chain (rather than "
            "two sequential mutable appends) computes the same result, so the "
            "sole clause still holds under the frozen tactic script; a second "
            "structurally-different correct reshape defends the soundness "
            "surface. If it fails => SPEC-TOO-STRONG on impl shape."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — ADDED BY THE SECOND AUDIT. The method declares no `require`
    # clause, so the nagini sibling's "a normal input satisfies the precondition"
    # probe has no literal counterpart. That is NOT a reason to drop the lane: on
    # a total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
    # UNSATISFIABLE at an F2P-shaped input — a spec whose sole clause could not be
    # met there would read exactly like a live one, because the frozen impl is the
    # only thing that ever tries. This case discharges the obligation at three
    # concrete points BEFORE closing the frozen obligation verbatim: an in-region
    # `assert` pinning the chosen name at one input from EACH of the three (V)
    # sub-domains, by evaluation. The impl is the frozen body kept verbatim, so
    # the method's own `ensures` still discharges too; only the tactic body is
    # retuned to also close the assert VC (both regions elided from the spec view,
    # so same_spec holds — mechanically confirmed, scope_problems == []).
    #
    # The assert is a LIVE obligation, not decoration: the audit built two
    # negative controls falsifying one clause each (claiming the deeper dotted
    # module DOES collapse onto its parent; claiming the no-parent entry point
    # yields the empty name) and both FAILED, EXIT 1, "Tactic `decide` proved that
    # the proposition ... is false". So a spec that had gone degenerate at these
    # points could not pass this case.
    # =====================================================================
    {
        "id": "admiss-obligation-at-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (moduleToReexec \"a.b.c\" \"a.b\" = \"a.b.c\" ∧\n"
            "       moduleToReexec \"__main__\" \"a.b\" = \"a.b\" ∧\n"
            "       moduleToReexec \"__main__\" \"\" = \"__main__\"))\n" + _IMPL,
            "prove_correct relaunchCommand by\n"
            "  loom_solve\n"
            "  all_goals simp_all [moduleToReexec]\n"
            "  all_goals decide"),
        "rationale": (
            "the sole clause is SATISFIABLE, and non-degenerate, at an F2P-shaped "
            "input and at one point from each (V) sub-domain — discharged by "
            "EVALUATION as an in-region `assert` before the frozen obligation is "
            "closed verbatim: (1) a directly-named module three segments deep with "
            "its enclosing package present keeps its OWN full dotted name (the F2P "
            "shape — the spec must NOT collapse it onto the parent); (2) a "
            "package-entry sentinel with a parent present takes the parent; (3) the "
            "same sentinel with NO parent keeps the name. If the obligation could "
            "not be met at these points the spec would be PRECOND-TOO-STRONG in the "
            "form this total carrier admits — an obligation unsatisfiable exactly "
            "where the behaviour matters — and no rival would ever reveal it, since "
            "a reject case only shows some OTHER impl fails. Falsifying either the "
            "(1) or the (3) clause makes this case FAIL, so it is not vacuous."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- (V) name-choice sub-domain (2): always take the name (forgot the
    # ---- package-entry branch). ----
    {
        "id": "weak-always-name",
        "kind": "uniqueness",
        "expect": "reject",
        # Always choose the module's own reported dotted name, dropping the
        # package-entry branch entirely. Correct on sub-domains (1) and (3);
        # WRONG on (2) [package-entry name with a present parent], where the
        # choice must be the parent package.
        "module": _impl(
            "    let name : String := moduleName\n"
            "    return leadingArgs ++ [\"-m\", name] ++ trailingArgs"),
        "refinement": (
            "dropping the package-entry branch relaunches a package run through "
            "its entry-point sentinel (a package-entry name with a present "
            "parent) under that sentinel name instead of the parent package the "
            "user typed — so the relaunch targets a different module. A faithful "
            "counterpart built this way keeps the wrong target for exactly the "
            "package-entry-with-parent inputs the failing tests exercise, so it "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from the (V) sub-behaviour: `moduleToReexec` chooses the "
            "parent package on sub-domain (2) [package-entry name AND parent "
            "present], but this returns the name. If it verified the spec would "
            "be SPEC-TOO-WEAK (the package-entry branch unenforced). Refuted at a "
            "package-entry name with a present parent — the sub-domain the branch "
            "protects. Varies `moduleName`/`parentPackage`."
        ),
        "witness": _tester(
            "example : relaunchCommandTester [] \"__main__\" \"pkg\" [] = false := by\n"
            "  decide\n"),
    },

    # ---- (V) name-choice sub-domain (3): parent taken even when EMPTY (drop the
    # ---- `parentPackage ≠ ""` guard). ----
    {
        "id": "weak-parent-ignores-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Take the parent package whenever the name is a package-entry sentinel,
        # regardless of whether a parent is actually present (drops the
        # non-empty-parent guard). Correct on (1) and (2); WRONG on (3)
        # [package-entry name with NO parent], where the choice must be the name.
        "module": _impl(
            "    let name : String :=\n"
            "      if (moduleName == \"__main__\") || moduleName.endsWith \".__main__\"\n"
            "      then parentPackage\n"
            "      else moduleName\n"
            "    return leadingArgs ++ [\"-m\", name] ++ trailingArgs"),
        "refinement": (
            "dropping the present-parent guard relaunches a bare top-level entry "
            "point (a package-entry name with NO parent) under an EMPTY module "
            "name instead of its own genuine name — an empty relaunch target. A "
            "faithful counterpart that omitted the present-parent guard would "
            "relaunch the no-parent entry point wrongly, which the failing tests "
            "require to be handled, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the (V) sub-behaviour: `moduleToReexec` requires "
            "`parentPackage ≠ \"\"` to take the parent, so on sub-domain (3) "
            "[package-entry name, empty parent] it chooses the name, but this "
            "returns the empty parent. If it verified the spec would be "
            "SPEC-TOO-WEAK (the present-parent guard unpinned). Refuted at a "
            "package-entry name with an EMPTY parent — the one input the "
            "always-name rival never probes. Varies `parentPackage` to \"\"."
        ),
        "witness": _tester(
            "example : relaunchCommandTester [] \"__main__\" \"\" [] = false := by\n"
            "  decide\n"),
    },

    # ---- (V) name-choice sub-domain (1): the literal pre-patch — parent taken
    # ---- whenever present, ignoring the package-entry classifier entirely. ----
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch behaviour: take the parent package whenever one is
        # present, without testing whether the name is a package-entry sentinel.
        # Correct on (2) and on the empty-parent collapse of (3); WRONG on (1)
        # [a genuine deeper dotted module WITH a present parent], where the
        # choice must be the module's own name, not the parent.
        "module": _impl(
            "    let name : String :=\n"
            "      if parentPackage ≠ \"\" then parentPackage else moduleName\n"
            "    return leadingArgs ++ [\"-m\", name] ++ trailingArgs"),
        "refinement": (
            "this is the literal pre-patch: take the parent package whenever a "
            "parent is present. It relaunches a directly-named deeper module "
            "(genuine dotted name, present parent) under its parent package "
            "instead of its own name — collapsing the deeper target onto its "
            "parent. That is precisely the non-resolution the newly-added failing "
            "test asserts against (a directly-named non-package module must "
            "relaunch under its own full dotted name), so a counterpart built "
            "this way would NOT resolve."
        ),
        "rationale": (
            "REJECT from the (V) sub-behaviour: on sub-domain (1) [NOT a "
            "package-entry name, parent present] `moduleToReexec` keeps the "
            "module's own name, but this returns the parent. Refuted at a genuine "
            "deeper dotted module with a present parent — the exact F2P shape: a "
            "directly-named module three segments deep whose enclosing package is "
            "its first two, where the spec keeps the full dotted name and this "
            "rival collapses it onto the parent. Varies "
            "`moduleName`/`parentPackage`. The witness is UNCONDITIONED — the "
            "tester `decide`s this literal outright (see WITNESS PLACEMENT: "
            "`endsWith` stalls only past a length threshold this point stays "
            "under), so nothing is assumed and no consistency probe is needed."
        ),
        "witness": _tester(
            "example : relaunchCommandTester [] \"a.b.c\" \"a.b\" [] = false := by\n"
            "  decide\n"),
    },

    # ---- (S) assembly: drop the leading carrier prefix. ----
    {
        "id": "weak-drop-leading",
        "kind": "uniqueness",
        "expect": "reject",
        # Assemble the chosen name correctly but drop the read-only leading
        # carrier (interpreter executable + propagated flags). Correct name
        # choice; WRONG whole vector whenever leadingArgs is non-empty.
        "module": _impl(
            "    return [\"-m\", moduleToReexec moduleName parentPackage] "
            "++ trailingArgs"),
        "refinement": (
            "dropping the leading carrier omits the interpreter executable and "
            "any propagated flags from the relaunch command, so the assembled "
            "argument vector is missing its head — the relaunch would not run "
            "under the intended interpreter/flags. A faithful counterpart that "
            "dropped the leading carrier would build a truncated command the "
            "failing test's exact-vector assertion rejects, so it would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the (S) assembly: the clause pins `cmdline = leadingArgs "
            "++ ...`, but this drops `leadingArgs`, so the vectors differ "
            "whenever `leadingArgs` is non-empty. Attacks the `leadingArgs` "
            "binder specifically (held at [] by every name-choice rival). "
            "Refuted with a non-empty `leadingArgs`."
        ),
        "witness": _tester(
            "example : relaunchCommandTester [\"py\"] \"m\" \"\" [] = false := by\n"
            "  decide\n"),
    },

    # ---- (S) assembly: drop the trailing carrier suffix. ----
    {
        "id": "weak-drop-trailing",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror of drop-leading, attacking the `trailingArgs` binder: drop the
        # read-only trailing program arguments.
        "module": _impl(
            "    return leadingArgs ++ [\"-m\", moduleToReexec moduleName "
            "parentPackage]"),
        "refinement": (
            "dropping the trailing carrier omits the program arguments forwarded "
            "to the relaunched module, so the relaunch runs without the "
            "arguments the user passed. A faithful counterpart that dropped the "
            "trailing carrier would build a command missing its tail, which the "
            "failing test's exact-vector assertion (which carries a trailing "
            "argument) rejects, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the (S) assembly: the clause pins `... ++ trailingArgs`, "
            "but this drops `trailingArgs`, so the vectors differ whenever "
            "`trailingArgs` is non-empty. Attacks the `trailingArgs` binder "
            "specifically (held at [] by every other rival). Refuted with a "
            "non-empty `trailingArgs`."
        ),
        "witness": _tester(
            "example : relaunchCommandTester [] \"m\" \"\" [\"run\"] = false := by\n"
            "  decide\n"),
    },

    # ---- (S) assembly: drop the `"-m"` switch literal. ----
    {
        "id": "weak-drop-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # Assemble the chosen name and both carriers correctly but OMIT the
        # `"-m"` switch literal that must precede the name. Correct on the name
        # and carriers; WRONG on the assembly for every input.
        "module": _impl(
            "    return leadingArgs ++ [moduleToReexec moduleName parentPackage] "
            "++ trailingArgs"),
        "refinement": (
            "omitting the switch literal that introduces the chosen name emits "
            "the dotted name as a bare positional argument rather than under the "
            "module-invocation switch, so the relaunch would not run the module "
            "at all. A faithful counterpart that omitted the switch would build a "
            "command the failing test's exact-vector assertion (which contains "
            "the switch immediately before the name) rejects, so it would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the (S) assembly: the clause pins the `\"-m\"` literal "
            "immediately before the chosen name, but this omits it, so the "
            "vectors differ for every input. Refuted at the minimal input "
            "(empty carriers, empty parent) — the divergence is the missing "
            "literal alone, independent of the name-choice sub-domain."
        ),
        "witness": _tester(
            "example : relaunchCommandTester [] \"m\" \"\" [] = false := by\n"
            "  decide\n"),
    },

    # ---- (V) name-choice: the DOTTED sentinel disjunct alone. ADDED BY AUDIT.
    # ---- Every pre-existing name-choice rival is refuted at the top-level
    # ---- sentinel or at a non-sentinel name, so all three leave the
    # ---- `moduleName.endsWith ".__main__"` DISJUNCT of the classifier
    # ---- unattacked: a rival that keeps only the `== "__main__"` equality test
    # ---- is wrong exactly on the NESTED package-entry name, a point no other
    # ---- case visits. Confirmed rejected, witness rebuilt (rival EXIT 0, gold
    # ---- EXIT 1 by semantic refutation, consistency probe EXIT 1).
    {
        "id": "weak-drop-dotted-disjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Test only the bare top-level sentinel equality, dropping the dotted
        # `<pkg>.__main__` sentinel disjunct. Correct on a top-level entry name
        # and on non-sentinel names; WRONG on a NESTED package-entry name with a
        # present parent, where the choice must still be the parent package.
        "module": _impl(
            "    let name : String :=\n"
            "      if (moduleName == \"__main__\") && parentPackage ≠ \"\"\n"
            "      then parentPackage\n"
            "      else moduleName\n"
            "    return leadingArgs ++ [\"-m\", name] ++ trailingArgs"),
        "refinement": (
            "recognising only the bare top-level entry-point sentinel and not its "
            "dotted form relaunches a NESTED package entry point under its own "
            "sentinel-suffixed name instead of the parent package the user typed, "
            "so the relaunch targets a module that is not what was asked for. A "
            "faithful counterpart that tested only the bare equality keeps that "
            "wrong target for every nested package entry point, which the "
            "package-relaunch assertions require to be handled, so it would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the (V) name choice, aimed at the classifier's DOTTED "
            "disjunct specifically: `moduleToReexec` treats a name ENDING in the "
            "dotted sentinel as a package entry too, but this only tests the bare "
            "equality, so it returns the name where the parent is required. If it "
            "verified the spec would be SPEC-TOO-WEAK (half the package-entry "
            "classifier unenforced). Refuted at a nested package-entry name with a "
            "present parent — a sub-domain point no other rival visits (the "
            "sentinel-equality rivals sit at the bare `__main__`). Conditioned on "
            "the carrier for the same reason as `weak-prepatch`: `String.endsWith` "
            "does not reduce under `decide` for a non-empty argument, so the "
            "witness assumes the single TRUE `endsWith` fact about its concrete "
            "literal (satisfiable; the gate's inconsistency probe cannot derive "
            "`False` from it) and decides the residual goal."
        ),
        "witness": _tester(
            "example (h : (\"pkg.__main__\".endsWith \".__main__\") = true) :\n"
            "    relaunchCommandTester [] \"pkg.__main__\" \"pkg\" [] = false := by\n"
            + _COND_TAC),
    },

    # ---- (S) assembly: carrier ORDER. ADDED BY AUDIT. The three drop-* rivals
    # ---- each delete one part, so a rival that keeps every part but emits the
    # ---- two carriers in the wrong ORDER around the switch is unattacked;
    # ---- length and multiset of the vector are both preserved, so only the
    # ---- pinned sequence refutes it. Confirmed rejected, witness rebuilt
    # ---- (rival EXIT 0, gold EXIT 1 by semantic refutation).
    {
        "id": "weak-carriers-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit every required element — both carriers, the switch literal and the
        # correctly-chosen name — but frame the switch with the carriers
        # TRANSPOSED. Same length, same elements; wrong order.
        "module": _impl(
            "    return trailingArgs ++ [\"-m\", moduleToReexec moduleName "
            "parentPackage] ++ leadingArgs"),
        "refinement": (
            "transposing the two read-only carriers puts the forwarded program "
            "arguments ahead of the interpreter executable and its propagated "
            "flags, so the assembled vector no longer invokes the interpreter at "
            "all — the head of the command is a program argument. A faithful "
            "counterpart assembling the carriers in this order builds a vector "
            "the exact-vector assertions reject on every input where the two "
            "carriers differ, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the (S) assembly, attacking ORDER rather than presence: "
            "the clause pins `leadingArgs ++ [\"-m\", name] ++ trailingArgs` as a "
            "SEQUENCE, and this rival preserves every element and the total length "
            "while transposing the two carriers. The three drop-* rivals cannot "
            "sense this (each removes a part), so a spec pinning only length or "
            "membership would admit it. Refuted with both carriers non-empty and "
            "distinct — the only shape at which a transposition is observable."
        ),
        "witness": _tester(
            "example : relaunchCommandTester [\"py\"] \"m\" \"\" [\"run\"] = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The nagini sibling ships 8 SPEC cases (2 soundness
# positives, 1 admissibility, 1 MANDATORY frame-mutation rival, 4 uniqueness
# rivals) plus a 2-case AXIOM lane. This velvet bundle models the SAME core
# behaviour (which dotted name a `-m` relaunch is given, from the entry module's
# reported name and its parent package) but over a WIDER carrier: the velvet
# method assembles the WHOLE relaunch vector `leadingArgs ++ ["-m", name] ++
# trailingArgs` (four input binders), where the nagini function returns only the
# selected code-point sequence (two conceptual inputs, one modeled list). So the
# value/name-choice rivals port directly and three ADDED structural rivals cover
# the extra assembly binders.
#
#   nagini case                    -> here                        disposition
#   ---------------------------------------------------------------------------
#   pos-reorder                    -> pos-control-single-append    RE-SHAPED
#   pos-single-loop                -> pos-control-direct           RE-SHAPED
#   admiss-fresh-call              -> admiss-obligation-at-f2p     RE-AIMED (audit 2)
#   frame-mutate-name              -> (none)                       VACUOUS
#   partial-always-name            -> weak-always-name             PORTED
#   partial-parent-ignores-empty   -> weak-parent-ignores-empty    PORTED
#   partial-prepatch               -> weak-prepatch                PORTED
#   empty-always                   -> (subsumed)                   DROPPED (tripwire)
#   (no nagini counterpart)        -> weak-drop-leading            ADDED
#   (no nagini counterpart)        -> weak-drop-trailing           ADDED
#   (no nagini counterpart)        -> weak-drop-flag               ADDED
#   (no nagini counterpart)        -> weak-drop-dotted-disjunct    ADDED (audit)
#   (no nagini counterpart)        -> weak-carriers-swapped        ADDED (audit)
#   AXIOM_TESTS (2)                -> (none)                        DROPPED (G-AX)
#
# 3 name-choice rivals ported, 5 structural/classifier rivals added (3 by the
# port, 2 by audit 1), 2 positives re-shaped, 1 admissibility RE-AIMED (audit 2),
# 1 vacuous, 1 tripwire dropped-as-subsumed, 2 axiom cases dropped =
# 11 SPEC cases (2 soundness, 1 admissibility, 8 uniqueness).
#
# AUDIT ADDITIONS (independent adversarial audit; both machine-checked with the
#   real verifier — variant rejected, witness ELABORATES against the rival
#   [EXIT 0] and FAILS against the frozen solution by SEMANTIC refutation
#   [EXIT 1: "`decide` proved that the proposition ... is false"], and for the
#   conditioned one the inconsistency probe cannot derive `False` [EXIT 1]):
#   weak-drop-dotted-disjunct closes a genuine gap in the (V) lane — all three
#   ported name-choice rivals are refuted at the bare `__main__` sentinel or at a
#   non-sentinel name, leaving the classifier's DOTTED-sentinel disjunct
#   unattacked, so a rival keeping only the bare equality was unsensed.
#   weak-carriers-swapped closes the mirror gap in the (S) lane — the three
#   drop-* rivals each DELETE a part, so an assembly that keeps every element and
#   the exact length but transposes the two carriers was unsensed; only the
#   pinned SEQUENCE refutes it.
#   Two further audit rivals (a wrong switch literal `"-c"` in place of the
#   pinned one; the chosen name element DUPLICATED after the switch) were also
#   built and both were correctly REJECTED with discriminating witnesses, but are
#   not shipped: each is refuted at an input the drop-flag rival already visits
#   and adds no distinct sub-domain. Recorded here so the coverage claim below is
#   not read as untested.
#
# RE-SHAPED (positives): the nagini pos-reorder flips the branch ORDER of the two
#   take-loops and pos-single-loop binds the selected source to one alias and runs
#   a single copy loop. The velvet impl is a straight-line assembly with no copy
#   loop and no branch pair to reorder, so the ARGUMENT ("a structurally-different
#   faithful impl must verify, else SPEC-TOO-STRONG") is carried by the two
#   cheapest expressible reshapes: evaluate the whole pinned assembly in one
#   expression (retuning the tactic body to a bare `loom_solve`, elided from the
#   spec view), and assemble the vector in a single `++` chain instead of two
#   mutable appends (frozen tactic script unchanged). Both build EXIT 0.
# RE-AIMED (admiss-fresh-call -> admiss-obligation-at-f2p): the nagini
#   admissibility control allocates two fresh lists (an F2P-shaped input) and
#   self-calls to prove the fractional half-permission precondition
#   `Acc(list_pred(_),1/2)` admits them. This method declares NO `require` clause,
#   so the LITERAL case has no counterpart — but SECOND-AUDIT CORRECTION: the
#   first port concluded from that the whole lane was vacuous, and "the frozen
#   obligation has no precondition" is not a sufficient reason. The analogue of
#   PRECOND-TOO-STRONG on a total carrier is the obligation being UNSATISFIABLE at
#   an F2P-shaped input, and "the post-image is a total function, so it is
#   satisfiable everywhere by construction" is an ARGUMENT, not a machine check —
#   exactly the kind of prose this lane exists to replace with a build. The
#   admissibility case above now discharges the obligation at three concrete
#   points (one per (V) sub-domain, the F2P shape among them) by evaluation,
#   before closing the frozen obligation verbatim, and two negative controls
#   confirm the check is live rather than decorative. Lane restored:
#   PRECOND-TOO-STRONG is now actually tested rather than argued away.
# VACUOUS (frame-mutate-name): the nagini case is MANDATORY because `name` is held
#   at Acc(list_pred(name), 1/2) and a Viper impl can illegally write into it
#   (name[0] = parent[0]) to dodge the result allocation, rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent, declares no `mut`
#   binder over any input, and has no heap/aliasing — every parameter is an
#   immutable value, so there is no read-only input to overwrite and no permission
#   system to trip. The class is vacuous; no substitute is fabricated (per the
#   porting map).
#   AUDIT NOTE: demonstrated, not asserted. Making an input writable here requires
#   adding a `mut` binder to the method SIGNATURE, and the signature is part of the
#   consumer spec view: the audit built that variant and `variant_problems`
#   rejected it as `spec view differs (same_spec failed)`. So the mutation class
#   cannot be expressed by any in-scope variant of this bundle — it is a carrier
#   fact, mechanically confirmed, not an effort gap.
# PORTED (name-choice rivals): partial-always-name -> weak-always-name (drop the
#   package-entry branch; wrong on sub-domain (2)). partial-parent-ignores-empty
#   -> weak-parent-ignores-empty (drop the present-parent guard; wrong on
#   sub-domain (3), the empty-parent input). partial-prepatch -> weak-prepatch
#   (the literal pre-patch: take the parent whenever present; wrong on sub-domain
#   (1), the directly-named deeper module — the exact F2P shape). Each carries a
#   machine-checked witness that ELABORATES against the rival and FAILS against
#   the frozen solution. weak-prepatch's witness is UNCONDITIONED as of audit 2
#   (the first port conditioned it on an `endsWith` hypothesis because its literal
#   was long enough to stall the kernel; a shorter, equally F2P-shaped literal
#   decides outright, which removes the hypothesis instead of arguing it).
# ADDED (structural rivals): the velvet carrier assembles the whole relaunch
#   vector, so it exposes the `leadingArgs`, `trailingArgs`, and `"-m"`-literal
#   structure the nagini single-list model never had. weak-drop-leading /
#   weak-drop-trailing attack the two read-only carrier binders; weak-drop-flag
#   attacks the switch literal; weak-carriers-swapped (audit) attacks their
#   ORDER with every element present. Each is a real divergence a name-only
#   battery would never sense, with a discriminating witness.
# DROPPED (empty-always): the nagini supporting tripwire returns [] always
#   (fails clause (M) on any non-empty selection). Here that behaviour is
#   subsumed by the three structural rivals (any of which produces a vector
#   differing from the pinned assembly), so a bare "return []" adds no distinct
#   sub-domain. Recorded as a subsumed tripwire (a known, harmless gap), not a
#   case that would pass for the wrong reason.
#   AUDIT NOTE: this case is EXPRESSIBLE here, and the audit landed it to check —
#   `return []` is in scope, is correctly rejected, and a witness at
#   `["py"] "m" "" ["run"]` elaborates against it (EXIT 0) while failing on the
#   frozen solution by semantic refutation (EXIT 1). It is still not shipped, but
#   the reason is subsumption (it is refuted only at inputs where some carrier or
#   the switch is already missing, i.e. exactly what the drop-* rivals pin) and
#   NOT inexpressibility. The distinction matters: "subsumed" is a coverage
#   judgement, which the coverage block below supports (pts unchanged by adding
#   it); "inexpressible" would have been false.
# AXIOM_TESTS: dropped. The nagini lane probes the opaque @ContractOnly
#   classifier `marks_entry`. This bundle has NO axiomatized callee
#   (`moduleToReexec` is a deep model over primitive string ops, validated by
#   G-CONF, not a consumed axiom — mapping.md §3), and the G-PBT gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / POINT COVERAGE. Four input binders, all varied across the EIGHT reject
#   witnesses (eight DISTINCT input tuples):
#     leadingArgs   : {[], ["py"]}                (drop-leading / carriers-swapped)
#     moduleName    : {"__main__", "pkg.__main__", "a.b.c", "m"}
#                                     (always / dotted-disjunct / prepatch / rest)
#     parentPackage : {"pkg", "", "a.b"}
#                                     (always / parent-empty / prepatch)
#     trailingArgs  : {[], ["run"]}              (drop-trailing / carriers-swapped)
#   Clause coverage: the (V) name choice is attacked across all three behaviour
#   sub-domains (weak-always-name / weak-parent-ignores-empty / weak-prepatch) AND
#   on each DISJUNCT of the package-entry classifier separately — the bare
#   sentinel equality by the first two, the dotted-sentinel disjunct by
#   weak-drop-dotted-disjunct at the nested `pkg.__main__` point. The (S) assembly
#   is attacked on each of its three parts (weak-drop-leading / weak-drop-trailing
#   / weak-drop-flag) AND on their ORDER (weak-carriers-swapped, which preserves
#   every element and the length). Both positive controls defend both, and the
#   admissibility case pins the (V) choice at one input from EACH sub-domain by
#   evaluation. No two rivals are refuted at the same input, and each rival's
#   point is one where its own defect — not merely some defect — is observable.
# WITNESS DISCRIMINATION. Every reject case's builds were re-run INDEPENDENTLY by
#   BOTH audits with the real verifier, and the gold-side failure text was read in
#   each: all eight witnesses ELABORATE against their rival (EXIT 0) and FAIL
#   against the frozen solution (EXIT 1) with the SEMANTIC message
#   "Tactic `decide` proved that the proposition ... is false" — a refutation of
#   the concrete claim, never a missing identifier, a type error, or a stuck
#   reduction (which the gate would record as `witness-undecided`).
#   FORGERY TEST (audit 2, the check audit 1 did not run). Reading an error and
#   judging it "semantic" is not evidence; a gold-side exit code is admissible
#   only if it CHANGES when the claim changes. So for all EIGHT reject cases a
#   second file differing from the witness ONLY in what it CLAIMS — the flipped
#   assertion, `= true` in place of `= false`, i.e. asserting the frozen solution
#   is WRONG where it is right — was built against the frozen solution. All eight
#   flipped claims build EXIT 0. The gold-side exit code therefore tracks the
#   claim rather than the file, none of these rejections rests on a tactic
#   mismatch, and no case here is hollow in the way the corpus's two largest
#   signature classes were.
#   The ONE conditioned witness (weak-drop-dotted-disjunct) binds an `endsWith`
#   hypothesis that is the ACTUAL truth about its literal, and the inconsistency
#   probe fails (EXIT 1, `simp_all made no progress`) — so its refutation is not
#   proved from a contradiction. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears in any witness.
#   Carrier note, RE-MEASURED AND CORRECTED by audit 2: the blocker is a LENGTH
#   THRESHOLD, not opacity. `String.endsWith` unfolds to a `Substring` equality
#   that sticks in the kernel for long arguments but reduces for short ones —
#   measured across `decide`/`decide +kernel`/`rfl`/`simp`: `"m"`, `"a.b"`,
#   `"a.b.c"`, `"a.b.c.d"` all decide; `"foo.bar.baz"`,
#   `"utils_tests.test_module.main_module"` and every `<pkg>.__main__` spelling
#   stall. Audit 1 recorded the coarser claim ("does not reduce for a non-empty
#   argument") and conditioned two witnesses on that basis; only one of them
#   actually needed it, and the other has been strengthened to an unconditioned
#   claim at a shorter literal of the same shape. A conditioned witness is sound
#   but strictly weaker (its hypothesis has to be argued satisfiable), so where the
#   carrier does not force one it should not be used.
# SPEC PROBES (audit 2, attacks D and E; none shipped as cases). THREE further
#   wrong impls beyond audit 1's were built and the frozen spec REJECTED all three
#   (each EXIT 1): the classifier's sentinel suffix WEAKENED to the undotted
#   `"__main__"` (so `my__main__` would be misread as a package entry), the switch
#   literal and the chosen name TRANSPOSED (right elements, wrong order, inside the
#   pair rather than across the carriers), and `moduleToReexec`'s two arguments
#   SWAPPED at the call site. TWO further correct reshapes were built and both
#   VERIFY (EXIT 0): the cons-shaped assembly, and the guard split so the parent is
#   tested FIRST with the two sentinel disjuncts as separate nested `if`s. So on
#   these five new probes the spec is neither too weak nor too strong.
# SPEC PROBES (audit 1, attacks D and E; none shipped as cases). FOUR further wrong
#   impls were built to look for a spec hole — the bare-equality classifier, a
#   transposed pair of carriers, a wrong switch literal, and a duplicated name
#   element — and the frozen spec REJECTED all four, each with a discriminating
#   witness (the first two are now shipped above). THREE further CORRECT reshapes
#   were built to look for over-strength — a cons-shaped assembly
#   (`leadingArgs ++ "-m" :: name :: trailingArgs`), the guard NEGATED with its
#   branches flipped, and the guard split into two nested `if`s testing the parent
#   first — and all three VERIFY (EXIT 0) once the tactic body is retuned, which
#   the spec view elides. So the spec is neither too weak nor too strong on these
#   probes. NO hole is open. The divergence lane described at the top of this file
#   was recorded as one by an earlier revision, on the premise that the frozen
#   `set_option` reads "partial"; it reads "total", and a diverging rival is
#   REJECTED there -- unmeasured loops at elaboration, and a loop carrying a
#   non-decreasing measure on the measure's own goal (`case «decreasing_1: q»`,
#   residual `q < q`). Nothing is escalated and nothing is left for a later lane.
AXIOM_TESTS = []
