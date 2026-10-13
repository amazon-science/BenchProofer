"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9658 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds by
construction and the ``prove_correct renderReference`` obligation survives with
its header intact). ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE — ONE method, ONE obligation, FIVE clauses:

    method renderReference (modulePath : List Char) (createdName : List Char)
        return (out : List Char)
      ensures out = renderedReference modulePath createdName            -- (Q1)
      ensures modulePath = abbreviatedNamespace → createdName = aliasFactoryName →
          out = openMark ++ createdName ++ closeMark                    -- (Q2)
      ensures (modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB) →
          out = openMark ++ createdName ++ closeMark ++ elementListTail  -- (Q3)
      ensures modulePath = abbreviatedNamespace → createdName ≠ aliasFactoryName →
          out = openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ createdName
                  ++ closeMark                                          -- (Q4)
      ensures modulePath ≠ coreNamespaceA → modulePath ≠ coreNamespaceB →
          modulePath ≠ abbreviatedNamespace →
          out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark  -- (Q5)

There is NO ``require`` (the pre-conditions region is empty), so the domain is
total: every pair of character lists is admissible. The ``axioms`` region is
EMPTY — ``renderedReference`` and ``reportedName`` are concrete ``def``s over the
method's own arguments, fully transparent and ``DecidableEq``. So (Q1) is not an
answer key a wrong impl could echo: any impl satisfying it has actually performed
the renderer's four-rule dispatch, and (Q2)–(Q5) restate each of the four rules
explicitly, guard by guard, without the helper.

WHY FIVE CLAUSES AND NOT A SINGLE DOTTED JOIN (the shape this battery defends).
The renderer this method models does NOT treat every module path alike: it
consults the module path FIRST and selects one of four rules, and only the last
of the four is the plain dotted join. A single unconditional dotted-join
postcondition would therefore claim a law the renderer only obeys off the three
reserved paths — so (Q2)/(Q3)/(Q4) pin the three reserved rules and (Q5) pins the
general one under its own guard. ``weak-general-rule-everywhere`` is the rival
that applies the plain dotted join everywhere; it is REJECTED, which is what
establishes that the per-rule clauses are load-bearing rather than decoration.

Load-bearing behaviours inside the composition, each with its own attack:

  * REPORTED NAME — in EVERY one of the four rules the trailing segment is the
    name the placeholder was created to stand for
    (``reportedName createdName = createdName``), never the empty name. This is
    the discriminating behaviour: an empty reported name renders a reference whose
    trailing segment is dropped — the symptom the public issue reports (a base
    class listed as ``torch.nn.`` rather than ``torch.nn.Module``). Attacked by
    ``weak-empty-reported-name`` (all four rules) and, off-by-one, by
    ``weak-truncated-trailing-segment``.
  * RULE SELECTION — which of the four rules a module path selects, and that the
    two reserved core namespaces are BOTH reserved. Attacked by
    ``weak-general-rule-everywhere``, ``weak-one-core-namespace-only``.
  * PER-RULE SHAPE — the reserved rules DROP the module path where the general
    rule keeps it; the core rule appends the element-list tail; the abbreviated
    rule carries the abbreviation mark. Attacked by
    ``weak-core-namespace-keeps-path``, ``weak-missing-element-list-tail``,
    ``weak-missing-abbreviation-mark``, ``weak-alias-rule-keeps-path``.
  * MODULE PREFIX — where a rule renders the path, it renders the WHOLE dotted
    path, not a suffix of it and not nothing. Attacked by
    ``weak-drop-module-prefix``, ``weak-last-module-segment-only``.
  * SEPARATOR AND ORDER — exactly one ``'.'`` sits BETWEEN the module path and the
    reported name, in that order. Attacked by ``weak-missing-separator``,
    ``weak-transposed-segments``.
  * WRONG SOURCE — the reported simple name is the bare creation name, not the
    placeholder's whole display name. Attacked by
    ``weak-wrong-source-display-name``.

CARRIER — FULLY COMPUTABLE, so no conditioning is needed. All five spec clauses
reduce at literal ``List Char`` inputs, so each witness reaches the post-image
through Velvet's own tester machinery (``renderReferenceTester modulePath
createdName = false`` says the extracted program's result violates the method's
postcondition at that concrete input) and closes by ``decide``, checked in a file
whose ``prove_correct`` block has been stripped so no tactic script can mask the
verdict. Every witness head binds NOTHING (all arguments are literals, or the
frozen ``pure``-region constants, which are themselves closed literals), so there
are no hypotheses that could be jointly unsatisfiable.

WHY EACH REJECT IS ATTRIBUTABLE TO THE SPEC, not to a broken tactic script. Every
rival was built and read by hand: all fourteen fail with ``error: unsolved
goals`` on a named ``ensures`` case — the postcondition itself, unprovable because
the rival is wrong, not a ``loom_solve`` that lost its shape. Independently, every
witness was built the two required ways with ``scripts/lean_verify.sh``: it
elaborates green against its rival (exit 0) and FAILS against the frozen solution
(exit 1), i.e. gold SATISFIES the postcondition at that input.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. THREE CORRECT impls must verify, else
    the spec is over-fit to the frozen code shape (SPEC-TOO-STRONG). All three
    confirmed verifying. Two of them are required to be terms `rfl` does NOT
    identify with the frozen body: `++` is `infixl` here, so a "reshape" that
    merely binds a prefix first is the SAME TERM and is discharged without the
    spec being consulted. See the definitional-equality discipline note at the
    head of the positive-control block.
  * ADMISSIBILITY — RE-AIMED. This method has no ``require`` at all, so a
    precondition probe is vacuous — nothing could exclude any input. The residual
    admissibility risk on a total domain is a DEGENERATE post-image: a spec no
    impl distinguishes reads exactly like one every impl meets.
    ``admiss-nondegenerate`` discharges an in-region ``assert`` pinning nine facts
    spread across ALL FOUR rules, and was confirmed LIVE (falsifying one conjunct
    leaves ``⊢ False`` unsolved).
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. This backend is
    referentially transparent: ``modulePath`` and ``createdName`` are immutable
    ``List Char`` values declared read-only (neither is ``mut``), there is no heap,
    no aliasing, no fractional permission, no permission system to trip. There is
    no read-only input to overwrite and no frame clause to violate, so the class
    has no carrier analogue. NOT ported, and NOT substituted for.
  * DIVERGENCE / NON-TERMINATION — the spec REJECTS it, but the class is not
    shippable as a reject case for a TOOLING reason. Under
    ``loom.semantics.termination "total"`` (line 4) a diverging impl is REJECTED
    with ``error: Decreasing annotations are required in total correctness
    semantics``, so there is no vacuous-postcondition escape. But that error is
    FILE-LEVEL — it fires at the ``method`` declaration, which ``witness_file``
    keeps — so the witness file does not compile against the rival either, and the
    gate would record ``witness-unproven`` (inconclusive, forcing
    MALFORMED-TESTS). The blockage is the LOOP, not the divergence: a TERMINATING,
    properly-measured wrong loop also fails to carry a witness with ``Tactic
    `decide` failed ... did not reduce to `isTrue` or `isFalse``` on the tester,
    the gate's own ``reduction`` stuck-screen. So no loop-bearing rival of this
    method is witnessable on this carrier. No spec hole is claimed and no case is
    dropped for difficulty.
  * UNGROUNDED-ORACLE ECHO — the post-image is pinned to a transparent structural
    dispatch over the method's own arguments, so there is no opaque answer key to
    echo. Probed anyway against what the four-rule realignment introduced: a rival
    that decides the rule by a cheap SURROGATE of the module path (its LENGTH: 8 /
    11 / 6 characters, which the three reserved paths happen to have) rather than
    by testing which reserved path it actually is. REJECTED, ``unsolved goals`` on
    (Q1)/(Q3)/(Q4)/(Q5) — the clauses quantify over all paths of those lengths, so
    a length surrogate cannot satisfy them. Recorded as an audit probe below
    rather than shipped, because its witness duplicates
    ``weak-one-core-namespace-only``'s leg.
  * PARTIAL-DOMAIN / VALUE — carries the whole reject lane; see each rival.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9658"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, markers included. Every
# ---- full-body variant replaces exactly this text, so each edit lies wholly
# ---- inside the one `-- impl-start` .. `-- impl-end` region and same_spec holds
# ---- by construction. Presence + uniqueness asserted at load, so the manifest
# ---- breaks loudly if the frozen solution ever changes.
_IMPL = """    -- impl-start
    -- The placeholder's reported simple name is the name it was created to stand
    -- for; the rendered reference places that name in the trailing position of
    -- whichever of the renderer's four rules the module path selects.
    let simpleName := createdName
    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then
      return openMark ++ simpleName ++ closeMark
    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then
      return openMark ++ simpleName ++ closeMark ++ elementListTail
    else if modulePath = abbreviatedNamespace then
      return openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName
               ++ closeMark
    else
      return openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique in the file); the admissibility case
# ---- inserts an in-region `assert` immediately after it and keeps the whole
# ---- frozen body, so the method's own obligation still discharges.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). Only
# ---- two cases retune it, each to clear a goal the frozen script leaves open.
_PROOF_GOLD = (
    "prove_correct renderReference by\n"
    "  loom_solve\n"
    "  <;> intros\n"
    "  <;> subst_vars\n"
    "  <;> simp_all [renderedReference, reportedName, coreNamespaceA, coreNamespaceB,\n"
    "                abbreviatedNamespace, aliasFactoryName]")
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- the frozen spec clauses, asserted so a silent weakening of any one of the
# ---- five `ensures` is caught at import rather than surviving into a gate run.
_CLAUSES = (
    "  ensures out = renderedReference modulePath createdName\n"
    "  ensures modulePath = abbreviatedNamespace → createdName = aliasFactoryName →\n"
    "      out = openMark ++ createdName ++ closeMark\n"
    "  ensures (modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB) →\n"
    "      out = openMark ++ createdName ++ closeMark ++ elementListTail\n"
    "  ensures modulePath = abbreviatedNamespace → createdName ≠ aliasFactoryName →\n"
    "      out = openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ createdName\n"
    "              ++ closeMark\n"
    "  ensures modulePath ≠ coreNamespaceA → modulePath ≠ coreNamespaceB →\n"
    "      modulePath ≠ abbreviatedNamespace →\n"
    "      out = openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark\n")
assert _BASE.count(_CLAUSES) == 1, "ensures-clause anchor drift — re-sync _CLAUSES"


def _impl(body):
    """`_BASE` with the frozen impl body replaced by `body` (markers re-emitted)."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end")


def _rules(comment, alias, core, abbrev, general):
    """A full four-rule dispatch body: `comment` then the renderer's four rules in
    the order the renderer tries them, each rule's returned expression supplied by
    the caller. A rival perturbs exactly one rule (or the reported name feeding all
    four), so what each rival changes is legible against the frozen body."""
    return (comment +
            "    let simpleName := createdName\n"
            "    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then\n"
            f"      return {alias}\n"
            "    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then\n"
            f"      return {core}\n"
            "    else if modulePath = abbreviatedNamespace then\n"
            f"      return {abbrev}\n"
            "    else\n"
            f"      return {general}\n")


# The four rules as the frozen body renders them, for rivals that perturb ONE.
_R_ALIAS = "openMark ++ simpleName ++ closeMark"
_R_CORE = "openMark ++ simpleName ++ closeMark ++ elementListTail"
_R_ABBREV = ("openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName"
             " ++ closeMark")
_R_GENERAL = "openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark"


def _reported(comment, expr):
    """A body that keeps all four rules intact but feeds them a WRONG reported
    simple name — the class of rival that is wrong on every rule at once."""
    return (comment +
            f"    let simpleName := {expr}\n"
            "    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then\n"
            f"      return {_R_ALIAS}\n"
            "    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then\n"
            f"      return {_R_CORE}\n"
            "    else if modulePath = abbreviatedNamespace then\n"
            f"      return {_R_ABBREV}\n"
            "    else\n"
            f"      return {_R_GENERAL}\n")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate, so
# ---- a witness reaches the post-image through Velvet's own tester machinery:
# ---- `renderReferenceTester modulePath createdName = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Every argument is a literal `List Char` or a closed `pure`-region
# ---- constant, so `decide` reduces both the extracted program and the pure model
# ---- fully — no opaque term, hence no conditioning and no head binders that
# ---- could be inconsistent.
def _witness(module_literal, name_literal):
    return ("extract_program_for renderReference\n"
            "prove_precondition_decidable_for renderReference\n"
            "prove_postcondition_decidable_for renderReference\n"
            "derive_tester_for renderReference\n\n"
            f"example : renderReferenceTester {module_literal} {name_literal}"
            " = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — CORRECT impls that MUST verify. If a
    # faithful correct impl cannot verify, the spec is SPEC-TOO-STRONG (over-fit
    # to the frozen code shape rather than to the behaviour).
    #
    # DEFINITIONAL-EQUALITY DISCIPLINE (the trap a positive control falls into on
    # this carrier). `++` is `infixl` in Lean 4, so the frozen body's
    # `openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark` ALREADY parses
    # fully left-associated. A "reshape" that merely binds a prefix first is
    # therefore the SAME TERM, and a positive whose returned term is `rfl`-equal to
    # the frozen one is discharged by the frozen tactic script without the spec
    # being consulted — it passes honestly while testing nothing. So two of the
    # three positives below are required to be terms `rfl` does NOT identify with
    # the frozen one, and that is stated per case.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest correct impl: return the grounded pure model
        # directly. Kept DELIBERATELY even though its returned term IS `rfl`-equal
        # to the frozen one — its job is not shape diversity but the
        # no-ungrounded-echo control (directive 8): `renderedReference` is a
        # transparent four-rule dispatch over the method's own arguments, so
        # returning it IS doing the work rather than echoing an answer key. The
        # shape-diversity job belongs to the two positives below.
        "module": _impl("    return renderedReference modulePath createdName\n"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`renderedReference modulePath createdName` directly. `out` IS that "
            "model, so clause (Q1) holds definitionally and (Q2)–(Q5) follow from "
            "the frozen `renderedReference_general`/`renderedReference_core` lemmas "
            "and the model's own guards. Because the model is a transparent "
            "dispatch over the two arguments — not an axiom — this is not an "
            "ungrounded echo: the impl performs the same rule selection the "
            "renderer does. Measured verifying (exit 0)."),
    },
    {
        "id": "pos-control-right-assoc",
        "kind": "soundness",
        "expect": "verify",
        # Genuinely right-associated: every separator is CONSED onto the reported
        # name and each rule's appends are re-bracketed to the right, so the build
        # is `openMark ++ (modulePath ++ ('.' :: (simpleName ++ closeMark)))` where
        # the frozen one is fully left-associated. `List.append` recurses on its
        # FIRST argument, so with a VARIABLE `modulePath` the frozen term is stuck
        # and the two are NOT definitionally equal; closing it needs
        # `List.append_assoc`, which `loom_solve` supplies itself (built with the
        # frozen proof body untouched: exit 0).
        "module": _impl(
            "    -- Same four rules, but every separator is CONSED onto the reported name so\n"
            "    -- each build is genuinely right-associated.\n"
            "    let simpleName := reportedName createdName\n"
            "    if modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName then\n"
            "      return openMark ++ (simpleName ++ closeMark)\n"
            "    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then\n"
            "      return openMark ++ (simpleName ++ (closeMark ++ elementListTail))\n"
            "    else if modulePath = abbreviatedNamespace then\n"
            "      return openMark ++ (abbreviationMark ++ (modulePath ++ ('.' :: (simpleName ++ closeMark))))\n"
            "    else\n"
            "      return openMark ++ (modulePath ++ ('.' :: (simpleName ++ closeMark)))\n"),
        "rationale": (
            "a CORRECT impl whose build is genuinely RIGHT-associated in all four "
            "rules: the separator is consed onto the reported simple name and the "
            "trailing appends are re-bracketed rightward, where the frozen body is "
            "fully left-associated (`++` is `infixl`). Because `List.append` "
            "recurses on its first argument, these are NOT definitionally equal at "
            "a variable `modulePath`, so verifying this case requires the "
            "association of each rule's composition to be DERIVED against the "
            "postcondition rather than matched syntactically. The same value is "
            "computed on every rule, so all five clauses hold on the whole domain; "
            "else SPEC-TOO-STRONG (the spec would be pinning the association of "
            "the build rather than the reference it renders). Measured exit 0."),
    },
    {
        "id": "pos-control-string-carrier",
        "kind": "soundness",
        "expect": "verify",
        # The sharpest available soundness probe: the reference is built on a
        # DIFFERENT intermediate carrier — the whole-string type, not the
        # per-code-point list — and only projected back to code points at the
        # return. The returned term is not even syntactically a list append, so
        # nothing about the frozen right-hand sides can be matched structurally;
        # each clause has to be re-derived through the projection. Retuned in the
        # tactic body only (elided from the spec view, so `same_spec` is
        # untouched) and confirmed verifying (exit 0).
        "module": _swap(
            _impl(
                "    -- Builds the reference on the whole-string carrier and projects back to code\n"
                "    -- points at the return.\n"
                "    let nm : String := String.mk (reportedName createdName)\n"
                "    let mp : String := String.mk modulePath\n"
                "    let op : String := String.mk openMark\n"
                "    let cl : String := String.mk closeMark\n"
                "    if modulePath = abbreviatedNamespace ∧ reportedName createdName = aliasFactoryName then\n"
                "      return (op ++ nm ++ cl).data\n"
                "    else if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then\n"
                "      return (op ++ nm ++ cl ++ String.mk elementListTail).data\n"
                "    else if modulePath = abbreviatedNamespace then\n"
                "      return (op ++ String.mk abbreviationMark ++ mp ++ \".\" ++ nm ++ cl).data\n"
                "    else\n"
                "      return (op ++ mp ++ \".\" ++ nm ++ cl).data\n"),
            _PROOF_GOLD,
            _PROOF_GOLD +
            "\n  all_goals simp [renderedReference, reportedName, List.append_assoc]"),
        "rationale": (
            "a CORRECT impl that builds the reference on a DIFFERENT carrier: each "
            "rule joins the module path, the marks and the reported simple name as "
            "whole strings and only projects back to code points at the return, so "
            "the returned term is not a list concatenation at all and cannot be "
            "matched against the frozen right-hand sides syntactically. Verifying "
            "requires all five clauses to be re-derived across the carrier "
            "projection. The bijection is the one mapping.md §2 fixes (a whole "
            "string ↔ its code points), so the computed value is identical on the "
            "whole domain; else SPEC-TOO-STRONG (the spec would be pinning the "
            "carrier the composition is built on rather than the reference it "
            "renders). Measured exit 0."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. This method has NO `require` (the pre-conditions
    # region is empty), so a precondition-admissibility probe is vacuous: nothing
    # could exclude any input. The residual admissibility risk on a total domain
    # is a DEGENERATE post-image — a spec no impl distinguishes reads exactly like
    # one every impl meets. This case discharges an in-region `assert`, at fully
    # concrete inputs, that the post-image is NON-DEGENERATE on ALL FOUR rules:
    # it names the exact rendered value on each rule; on the general rule it is
    # NOT the trailing-segment-dropped rendering; and on each of the three
    # value-bearing rules it separates two different created names. The frozen
    # impl is kept VERBATIM so the method's own obligation still discharges; the
    # proof body gains a `decide` arm only to clear the extra assert goal (the
    # tactic body is elided from the spec view).
    #
    # The assert is LIVE, not decoration — confirmed by hand: replacing the first
    # conjunct with the trailing-segment-dropped value leaves
    # `case «admiss_1: ...» ⊢ False` unsolved (exit 1).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      renderedReference ['p','k','g'] ['N'] = openMark ++ ['p','k','g','.','N'] ++ closeMark ∧\n"
                  "      renderedReference ['p','k','g'] ['N'] ≠ openMark ++ ['p','k','g','.'] ++ closeMark ∧\n"
                  "      renderedReference ['p','k','g'] ['N'] ≠ renderedReference ['p','k','g'] ['M'] ∧\n"
                  "      renderedReference ['p','k','g'] ['N'] ≠ renderedReference ['q'] ['N'] ∧\n"
                  "      renderedReference coreNamespaceB ['N'] = openMark ++ ['N'] ++ closeMark ++ elementListTail ∧\n"
                  "      renderedReference coreNamespaceB ['N'] ≠ renderedReference coreNamespaceB ['M'] ∧\n"
                  "      renderedReference abbreviatedNamespace ['N']\n"
                  "        = openMark ++ abbreviationMark ++ abbreviatedNamespace ++ ['.'] ++ ['N'] ++ closeMark ∧\n"
                  "      renderedReference abbreviatedNamespace ['N'] ≠ renderedReference abbreviatedNamespace ['M'] ∧\n"
                  "      renderedReference abbreviatedNamespace aliasFactoryName\n"
                  "        = openMark ++ aliasFactoryName ++ closeMark))\n"),
            _PROOF_GOLD,
            _PROOF_GOLD +
            "\n  all_goals first\n    | decide\n    | simp_all [renderedReference, reportedName]"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate on ALL FOUR of the "
            "renderer's rules. Nine facts are discharged in-region: on the general "
            "rule, the reference for a placeholder created for `N` under module "
            "path `pkg` is exactly `pkg.N` inside the marks, it is NOT the "
            "trailing-segment-dropped `pkg.` (the rendering the failing test "
            "forbids), and it differs both from a different created name under the "
            "same path and from the same created name under a different path; on "
            "the reserved core rule, the path is dropped and the element-list tail "
            "appended, and the value still depends on the created name; on the "
            "reserved abbreviated rule, the abbreviation mark is present and the "
            "value still depends on the created name; and on the reserved alias "
            "rule the path is dropped entirely. So the obligation genuinely "
            "depends on BOTH binders on every rule and pins the value the failing "
            "test demands, rather than being met by every impl. The frozen impl is "
            "kept verbatim so (Q1) still verifies; the assert is live (falsifying "
            "one conjunct leaves an unsolved `False` goal, checked)."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries a machine-checked refutation witness at a
    # DISTINCT concrete input, plus the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each was read at its failure
    # site: all fourteen fail with `unsolved goals` on a named `ensures` case,
    # i.e. on a postcondition, not on a tactic script that lost its shape.
    #
    # The lane is organised by WHAT the rival perturbs: the reported simple name
    # feeding all four rules (wrong on every input), the SELECTION among the four
    # rules, or the SHAPE of one rule.
    # =====================================================================

    # ---- (a) the reported simple name — wrong on all four rules at once --------
    {
        "id": "weak-empty-reported-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_reported(
            "    -- reported simple name left empty regardless of the creation name.\n",
            "([] : List Char)")),
        "rationale": (
            "THE pre-image rival: the reported simple name is the empty name on "
            "every rule, so every rendered reference drops its trailing segment — "
            "exactly the symptom the public issue reports (a base class listed as "
            "`torch.nn.` rather than `torch.nn.Module`). A real implementation "
            "behaving this way does NOT resolve the failing test. Violates (Q1) "
            "and, at the witness input, (Q5). Rejected with `unsolved goals`; the "
            "witness `(['u','n'], ['C'])` renders `un.` where gold renders "
            "`un.C`."),
        "witness": _witness("['u', 'n']", "['C']"),
    },
    {
        "id": "weak-truncated-trailing-segment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_reported(
            "    -- reported simple name truncated by its last character.\n",
            "createdName.take (createdName.length - 1)")),
        "rationale": (
            "the off-by-one near-miss of the same clause: the reported simple name "
            "loses its LAST character, so the rendered reference is wrong by one "
            "code point on every rule. Kept SEPARATE from "
            "`weak-empty-reported-name` precisely because it AGREES with gold "
            "where that rival does not — at a one-character created name the two "
            "coincide — so it is refuted at a TWO-character created name instead. "
            "Violates (Q1) and (Q5). Witness `(['t'], ['A','B'])` renders `t.A` "
            "where gold renders `t.AB`."),
        "witness": _witness("['t']", "['A', 'B']"),
    },
    {
        "id": "weak-wrong-source-display-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_reported(
            "    -- reported simple name taken as the placeholder's whole display name.\n",
            "modulePath ++ ['.'] ++ createdName")),
        "rationale": (
            "WRONG SOURCE: the reported simple name is taken to be the "
            "placeholder's whole display name (the module path joined to the "
            "creation name) rather than the bare creation name, so the general "
            "rule renders the module path TWICE. This is the most on-point wrong "
            "source available on this carrier — the placeholder does carry such a "
            "combined name, so an implementation could plausibly report it — and a "
            "real implementation doing so does not resolve the failing test. "
            "Violates (Q1) and (Q5). Witness `(['w','d'], ['N'])` renders "
            "`wd.wd.N` where gold renders `wd.N`."),
        "witness": _witness("['w', 'd']", "['N']"),
    },

    # ---- (b) SELECTION among the four rules ------------------------------------
    {
        "id": "weak-general-rule-everywhere",
        "kind": "uniqueness",
        "expect": "reject",
        # The load-bearing rival of the five-clause shape: it is the SINGLE
        # unconditional dotted-join law, i.e. exactly the postcondition a spec
        # would carry if the renderer's reserved-path dispatch were not modeled.
        # Its rejection is what establishes (Q2)/(Q3)/(Q4) are doing work.
        "module": _impl(
            "    -- applies the general dotted rule to every module path, ignoring the\n"
            "    -- renderer's reserved-path dispatch entirely.\n"
            "    return openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark\n"),
        "rationale": (
            "RULE SELECTION, and the rival that makes the per-rule clauses "
            "load-bearing: it applies the general dotted join to EVERY module "
            "path, ignoring that the renderer consults the module path first and "
            "selects a different rule for the three reserved paths. It is "
            "therefore correct on the general rule and wrong on all three reserved "
            "ones — precisely the behaviour an unconditional dotted-join "
            "postcondition would admit. A real implementation rendering this way "
            "disagrees with the renderer on every placeholder under a reserved "
            "path. Violates (Q1), (Q2), (Q3) and (Q4) (measured: `unsolved goals` "
            "on the `ensures_2`/`ensures_3`/`ensures_4`/`ensures_5` cases). "
            "Witness `(coreNamespaceB, ['C'])` — a reserved core namespace, where "
            "the rival renders the path and gold drops it and appends the "
            "element-list tail."),
        "witness": _witness("coreNamespaceB", "['C']"),
    },
    {
        "id": "weak-one-core-namespace-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_rules(
            "    -- honours only one of the two reserved core namespaces.\n",
            _R_ALIAS,
            _R_CORE,
            _R_ABBREV,
            _R_GENERAL).replace(
                "if modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB then",
                "if modulePath = coreNamespaceB then")),
        "rationale": (
            "RULE SELECTION, the near-miss of the rival above: it honours the "
            "reserved core rule for only ONE of the two reserved core namespaces, "
            "falling through to the general dotted rule for the other. Both names "
            "are reserved by the renderer, so this AGREES with gold on one of them "
            "and is wrong on the other — a partition no witness on the honoured "
            "namespace could expose, which is why the witness sits on the "
            "forgotten one. Violates (Q1) and (Q3). Witness `(coreNamespaceA, "
            "['Q'])`: the rival renders the dotted path, gold drops it and appends "
            "the element-list tail."),
        "witness": _witness("coreNamespaceA", "['Q']"),
    },

    # ---- (c) the SHAPE of one rule ---------------------------------------------
    {
        "id": "weak-core-namespace-keeps-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_rules(
            "    -- under a reserved core namespace the module path is kept instead of dropped.\n",
            _R_ALIAS,
            "openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark ++ elementListTail",
            _R_ABBREV, _R_GENERAL)),
        "rationale": (
            "PER-RULE SHAPE: the rival selects the reserved core rule correctly "
            "and appends its element-list tail, but KEEPS the module path that the "
            "rule drops. So it is wrong only on the reserved core paths, and only "
            "in the prefix — a rival that a spec pinning rule selection without "
            "pinning each rule's shape would admit. Violates (Q1) and (Q3). "
            "Witness `(coreNamespaceA, ['K'])`: the rival renders the dotted path "
            "before the name, gold renders the name alone."),
        "witness": _witness("coreNamespaceA", "['K']"),
    },
    {
        "id": "weak-missing-element-list-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_rules(
            "    -- under a reserved core namespace the element-list tail is not appended.\n",
            _R_ALIAS,
            "openMark ++ simpleName ++ closeMark",
            _R_ABBREV, _R_GENERAL)),
        "rationale": (
            "PER-RULE SHAPE, the complementary half of the rival above: the "
            "reserved core rule drops the module path correctly but omits the "
            "element-list tail the renderer appends there. Wrong only on the "
            "reserved core paths, and only in the suffix. Violates (Q1) and (Q3). "
            "Witness `(coreNamespaceB, ['E'])`: the rival stops at the closing "
            "mark, gold continues with the element-list tail."),
        "witness": _witness("coreNamespaceB", "['E']"),
    },
    {
        "id": "weak-missing-abbreviation-mark",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_rules(
            "    -- under the reserved abbreviated namespace the abbreviation mark is omitted.\n",
            _R_ALIAS, _R_CORE,
            "openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark",
            _R_GENERAL)),
        "rationale": (
            "PER-RULE SHAPE on the third rule: under the reserved abbreviated "
            "namespace the rival renders the dotted path correctly but omits the "
            "abbreviation mark the renderer places before it — collapsing that "
            "rule into the general one. Wrong only on that one reserved path. "
            "Violates (Q1) and (Q4). Witness `(abbreviatedNamespace, ['T'])`: the "
            "rival omits the mark gold emits."),
        "witness": _witness("abbreviatedNamespace", "['T']"),
    },
    {
        "id": "weak-alias-rule-keeps-path",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_rules(
            "    -- for the reserved simple name under the abbreviated namespace the module\n"
            "    -- path is kept instead of dropped.\n",
            _R_ABBREV, _R_CORE, _R_ABBREV, _R_GENERAL)),
        "rationale": (
            "PER-RULE SHAPE on the FIRST rule, the narrowest sub-domain in the "
            "battery: only when the module path is the reserved abbreviated "
            "namespace AND the reported simple name is the one reserved simple "
            "name does the renderer drop the path entirely, and this rival keeps "
            "it (collapsing that rule into the third). It agrees with gold on "
            "every other input in the whole domain, so it is the rival that shows "
            "(Q2) is not redundant with (Q4). Violates (Q1) and (Q2). Witness "
            "`(abbreviatedNamespace, aliasFactoryName)` — the only input class "
            "that reaches this rule."),
        "witness": _witness("abbreviatedNamespace", "aliasFactoryName"),
    },
    {
        "id": "weak-drop-module-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_rules(
            "    -- the general rule renders no module prefix at all.\n",
            _R_ALIAS, _R_CORE, _R_ABBREV,
            "openMark ++ ['.'] ++ simpleName ++ closeMark")),
        "rationale": (
            "MODULE PREFIX: the general rule renders the separator and the "
            "reported simple name but no module path at all, so a placeholder is "
            "referenced unqualified (`.Name`). Without this rival the `modulePath` "
            "binder would carry no obligation on the general rule that any rival "
            "tests. A real implementation doing this does not resolve the failing "
            "test. Violates (Q1) and (Q5). Witness `(['p','k','g'], ['N'])`: the "
            "rival renders `.N`, gold renders `pkg.N`."),
        "witness": _witness("['p', 'k', 'g']", "['N']"),
    },
    {
        "id": "weak-last-module-segment-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_rules(
            "    -- the general rule keeps only the module path's final dotted segment.\n",
            _R_ALIAS, _R_CORE, _R_ABBREV,
            "(modulePath.reverse.takeWhile (· ≠ '.')).reverse ++ ['.'] ++ simpleName ++ closeMark",
        ).replace(
            "      return (modulePath.reverse.takeWhile",
            "      return openMark ++ (modulePath.reverse.takeWhile")),
        "rationale": (
            "MODULE PREFIX, narrowed rather than dropped: the general rule keeps "
            "only the module path's FINAL dotted segment, flattening a nested "
            "lookup. This narrowing is INVISIBLE at an undotted module path — the "
            "shape every other witness in this battery uses — so it is refuted at "
            "a DOTTED one instead, which is also the shape the failing test "
            "exercises. Violates (Q1) and (Q5). Witness `(['u','.','s'], ['C'])`: "
            "the rival renders `s.C`, gold renders `u.s.C`."),
        "witness": _witness("['u', '.', 's']", "['C']"),
    },
    {
        "id": "weak-missing-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_rules(
            "    -- the general rule omits the separator between path and simple name.\n",
            _R_ALIAS, _R_CORE, _R_ABBREV,
            "openMark ++ modulePath ++ simpleName ++ closeMark")),
        "rationale": (
            "SEPARATOR: the general rule concatenates the module path and the "
            "reported simple name with no separator between them, so the two run "
            "together into one unresolvable name. Violates (Q1) and (Q5). Witness "
            "`(['a'], ['b'])`: the rival renders `ab`, gold renders `a.b`."),
        "witness": _witness("['a']", "['b']"),
    },
    {
        "id": "weak-transposed-segments",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_rules(
            "    -- the general rule renders the simple name first and the path last.\n",
            _R_ALIAS, _R_CORE, _R_ABBREV,
            "openMark ++ simpleName ++ ['.'] ++ modulePath ++ closeMark")),
        "rationale": (
            "ORDER: the general rule renders the reported simple name FIRST and "
            "the module path last, so both segments are present and exactly one "
            "separator sits between them — every count is right and only the order "
            "is wrong. A transposition is invisible when the two segments coincide, "
            "so it is refuted at segments of DIFFERENT lengths. Violates (Q1) and "
            "(Q5). Witness `(['x','y'], ['z'])`: the rival renders `z.xy`, gold "
            "renders `xy.z`."),
        "witness": _witness("['x', 'y']", "['z']"),
    },
    {
        "id": "weak-teach-to-the-test",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- special-cases one placeholder shape and drops the trailing segment elsewhere.\n"
            "    if modulePath = \"unknown.secret\".toList ∧ createdName = \"Class\".toList then\n"
            "      return openMark ++ modulePath ++ ['.'] ++ createdName ++ closeMark\n"
            "    else\n"
            "      return openMark ++ modulePath ++ ['.'] ++ ([] : List Char) ++ closeMark\n"),
        "rationale": (
            "TEACH-TO-THE-TEST: hard-codes the one placeholder shape the failing "
            "test names and drops the trailing segment on every other input, so it "
            "passes the F2P test while leaving the reported behaviour broken "
            "everywhere else. This is the rival that establishes the spec pins the "
            "behaviour on its whole domain rather than at the tested point. "
            "Violates all five clauses. Witness `(['t','t'], ['Z'])` — an input "
            "away from the hard-coded pair, where the rival renders `tt.` and gold "
            "renders `tt.Z`."),
        "witness": _witness("['t', 't']", "['Z']"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
# The sibling battery ships 9 SPEC cases (2 soundness positives, 1 admissibility,
# 6 uniqueness rivals — THREE of which are mandatory frame-mutation rivals) plus
# ONE axiom-lane probe. It contracts THREE functions over half/full-permission
# `List[int]` code points: a short-identifier site, a display-identifier site that
# propagates it, and a renderer that joins a module path to the propagated
# identifier.
#
# This velvet bundle models the SAME observable behaviour — the reference rendered
# for a stand-in placeholder symbol — but as ONE method `renderReference` over two
# `List Char` inputs, with the sibling's short- and display-identifier sites
# collapsed into the single transparent `def` `reportedName createdName =
# createdName`. That is carrier narrowing, not a thinner battery: the two
# intermediate sites are not separately observable here, so the three sibling
# rivals that each empty one of them are ONE rival on this carrier. Case-count
# parity is explicitly NOT the target; per-obligation, per-binder and per-clause
# coverage is (below).
#
#   sibling case                   kind          -> here                             disposition
#   --------------------------------------------------------------------------------------------
#   pos-control-qref-reshape       soundness     -> pos-control-right-assoc           RE-SHAPED
#   pos-control-short-reshape      soundness     -> pos-control-direct-model          RE-SHAPED
#   (no sibling)                   soundness     -> pos-control-string-carrier        ADDED
#   admiss-self-call               admissibility -> admiss-nondegenerate              RE-AIMED
#   frame-mutate-short-name        uniqueness    -> (none)                            VACUOUS
#   frame-mutate-qref-module       uniqueness    -> (none)                            VACUOUS
#   frame-mutate-qref-name         uniqueness    -> (none)                            VACUOUS
#   weak-dangling-dot              uniqueness    -> weak-empty-reported-name          MERGED
#   weak-display-empty             uniqueness    -> weak-empty-reported-name          MERGED
#   weak-short-empty               uniqueness    -> weak-empty-reported-name          MERGED
#   weak-truncated-display-tail    uniqueness    -> weak-truncated-trailing-segment   PORTED
#   weak-missing-dot               uniqueness    -> weak-missing-separator            PORTED
#   (no sibling)                   uniqueness    -> weak-wrong-source-display-name    ADDED
#   (no sibling)                   uniqueness    -> weak-drop-module-prefix           ADDED
#   (no sibling)                   uniqueness    -> weak-transposed-segments          ADDED
#   (no sibling)                   uniqueness    -> weak-last-module-segment-only     ADDED
#   (no sibling)                   uniqueness    -> weak-general-rule-everywhere      ADDED
#   (no sibling)                   uniqueness    -> weak-one-core-namespace-only      ADDED
#   (no sibling)                   uniqueness    -> weak-core-namespace-keeps-path    ADDED
#   (no sibling)                   uniqueness    -> weak-missing-element-list-tail    ADDED
#   (no sibling)                   uniqueness    -> weak-missing-abbreviation-mark    ADDED
#   (no sibling)                   uniqueness    -> weak-alias-rule-keeps-path        ADDED
#   (no sibling)                   uniqueness    -> weak-teach-to-the-test            ADDED
#   (no sibling)                   uniqueness    -> (none, REJECTED-BUT-UNWITNESSABLE) RECORDED
#   AXIOM_TESTS (1 A-reference)    axiom         -> (none)                            N/A (G-AX)
#
# 2 uniqueness ported + 3 merged into 1 + 10 added, 1 admissibility re-aimed, 2
# soundness re-shaped + 1 soundness added; 3 frame rivals vacuous; 1 divergence
# hole recorded; axiom lane dropped. 18 SPEC cases total (3 soundness,
# 1 admissibility, 14 uniqueness).
#
# WHY THE UNIQUENESS LANE IS LARGER THAN THE SIBLING'S. The renderer this method
#   models selects one of FOUR rules on the module path, and each rule has its own
#   shape. The sibling's carrier exposes only the general dotted join, so its lane
#   needs rivals for that one rule's parts (name, prefix, separator, order). Here
#   the SELECTION among the four rules and the SHAPE of each reserved rule are
#   additional load-bearing behaviours, each of which a wrong implementation can
#   get wrong independently — so the lane grows by six rivals aimed at the three
#   reserved rules and their selection, plus the unconditional-dotted-join rival
#   that is exactly what a spec without the per-rule clauses would admit. None of
#   the six is a reshuffle of another: each is refuted on a DIFFERENT rule or on a
#   different part of the same rule, and no two share a witness.
# RE-SHAPED / ADDED (the three positives): the sibling's positives are loop
#   reshapes of its code-point copy loops. This carrier has no loop — each rule is
#   a straight-line concatenation — so the reshape axis here is the ASSOCIATION and
#   the CARRIER of those concatenations, not a loop body.
#
#   The controlling constraint, measured rather than assumed: `++` is `infixl` in
#   Lean 4, so a positive whose returned term is `rfl`-equal to the frozen one is
#   closed by the frozen tactic script with the spec never consulted — it passes
#   honestly and tests nothing.
#     * pos-control-direct-model    — returns the grounded model directly.
#       `rfl`-equal to the frozen term and KEPT ON PURPOSE as the
#       no-ungrounded-echo control (directive 8); explicitly NOT counted as shape
#       diversity.
#     * pos-control-right-assoc     — conses each separator onto the reported name
#       and re-brackets each rule rightward, so the build is genuinely
#       right-associated and NOT `rfl`-equal (`List.append` recurses on its first
#       argument); `loom_solve` closes it with the frozen proof body untouched.
#     * pos-control-string-carrier  — builds on the whole-string carrier and
#       projects back to code points at the return, so the returned term is not a
#       list append at all and every clause must be re-derived across the
#       projection. Retuned in the tactic body only (elided from the spec view).
#   All three VERIFY. None weakens or removes the `prove_correct renderReference`
#   obligation, and no positive was dropped for a proof that would not close.
# RE-AIMED (admiss-self-call -> admiss-nondegenerate): the sibling self-calls its
#   three modeled functions to show each half-permission `Requires` is
#   establishable. This method has NO `require`, so there is no precondition to
#   admit anything and no permission to establish — the probe would assert
#   nothing. Re-aimed to the sharper residual risk on a total domain: a DEGENERATE
#   post-image. The in-region assert pins the exact rendered value on ALL FOUR
#   rules and its dependence on EACH binder separately. Confirmed live: falsifying
#   one conjunct leaves `⊢ False` unsolved.
# MERGED (weak-dangling-dot + weak-display-empty + weak-short-empty ->
#   weak-empty-reported-name): the sibling attacks the same behaviour at three
#   separately-contracted sites. This carrier collapses all three into
#   `reportedName`, a transparent `def` in the `pure` region, so all three rivals
#   become the SAME impl here. Shipping three copies of one rival would inflate
#   the case count without probing anything new, and all three would need the same
#   witness. The off-by-one variant of the same clause is kept SEPARATE
#   (weak-truncated-trailing-segment) precisely because it is a near-miss that
#   agrees with gold where this one does not.
# PORTED (weak-truncated-display-tail -> weak-truncated-trailing-segment;
#   weak-missing-dot -> weak-missing-separator): direct ports, re-expressed over
#   `List Char` and this backend's five `ensures` clauses.
# VACUOUS (frame-mutate-short-name, frame-mutate-qref-module, frame-mutate-qref-name):
#   the sibling's three MANDATORY frame rivals write into read-only inputs held at
#   half permission, and are rejected by the permission system rather than by a
#   value mismatch. This backend is referentially transparent: `modulePath` and
#   `createdName` are immutable `List Char` values declared read-only (neither is
#   `mut`), there is no heap, no aliasing, no fractional permission and no
#   permission system. There is no read-only input to overwrite and no frame
#   clause to violate, so the class has NO carrier analogue. Omitted as a genuine
#   carrier fact and deliberately NOT substituted for: the value-level rivals
#   attack the same binders on their own merits, not as stand-ins for a permission
#   check they do not perform.
# RECORDED, NOT PORTED — DIVERGENCE. Under `loom.semantics.termination "total"`
#   (Solution.lean line 4) a diverging rival is REJECTED — exit 1, `error:
#   Decreasing annotations are required in total correctness semantics`. Every loop
#   owes a decreasing measure, so there is no vacuous-postcondition escape and the
#   spec is NOT too weak on this class. The class is still not shippable as a
#   reject case, for a TOOLING reason rather than a difficulty one: the linter
#   error is FILE-LEVEL — it fires at the `method` declaration, which
#   `witness_file` preserves (it strips only `prove_correct` and `#`-commands) — so
#   the witness file fails to compile against the rival. That is the half of the
#   discrimination check that must SUCCEED, so the gate would record
#   `witness-unproven`: inconclusive, which forces MALFORMED-TESTS.
#   `witness_reference` cannot repair it: it replaces the SECOND subject (gold),
#   and is reached only once the rival build has already succeeded. The deeper
#   blockage is the LOOP, not the divergence — a TERMINATING wrong loop with a
#   valid measure also cannot carry a witness (`Tactic `decide` failed ... did not
#   reduce to `isTrue` or `isFalse`` on `renderReferenceTester`, the gate's
#   `reduction` stuck-screen) — so NO loop-bearing rival of this method is
#   witnessable on this carrier. Nor is the refusal merely the missing-annotation
#   linter: a loop CARRYING a measure that does not decrease is rejected on the
#   measure's own goal (`case «decreasing_1: q»`, residual `q < q`). Nothing is
#   claimed dropped for a hard proof and no spec hole is claimed.
#
# AUDIT PROBES — run against the frozen spec, NOT shipped as cases, recorded so
# the next reader need not re-derive them.
#   * UNGROUNDED-ORACLE ECHO, aimed at what the four-rule shape introduces: a
#     rival that selects the rule by a cheap SURROGATE of the module path — its
#     LENGTH (the three reserved paths have 11, 8 and 6 characters respectively) —
#     rather than by testing which reserved path it actually is. REJECTED (exit 1,
#     `unsolved goals` on the `ensures_1`/`ensures_3`/`ensures_4`/`ensures_5`
#     cases): the clauses quantify over ALL module paths, so the many other paths
#     of those lengths refute the surrogate. Not shipped because its witness
#     duplicates `weak-one-core-namespace-only`'s reserved-core leg.
#   * PARTIAL-DOMAIN SPLIT, aimed at the realignment from the other side: a rival
#     honouring all three reserved rules but dropping the trailing segment on the
#     GENERAL rule. REJECTED (exit 1, `unsolved goals`). Not shipped because
#     `weak-empty-reported-name` already refutes the same behaviour on the general
#     rule with the same witness shape.
#
# BINDER / CLAUSE COVERAGE (what replaces case-count parity).
#   OBLIGATION: one, `prove_correct renderReference`. DEFENDED by 3 soundness
#     positives + 1 admissibility case; ATTACKED by 14 uniqueness rivals. Of the
#     3 positives, 2 return terms `rfl` does NOT identify with the frozen body —
#     the count that actually bears on SPEC-TOO-STRONG.
#   CLAUSES: all five top-level `ensures`, and each is the named target of at
#     least one rival, so none is decoration:
#       * (Q1) `out = renderedReference modulePath createdName` — violated by all 14.
#       * (Q2) the reserved alias rule      — weak-alias-rule-keeps-path,
#              weak-general-rule-everywhere, weak-teach-to-the-test.
#       * (Q3) the reserved core rule       — weak-general-rule-everywhere,
#              weak-one-core-namespace-only, weak-core-namespace-keeps-path,
#              weak-missing-element-list-tail, weak-teach-to-the-test.
#       * (Q4) the reserved abbreviated rule — weak-missing-abbreviation-mark,
#              weak-general-rule-everywhere, weak-teach-to-the-test.
#       * (Q5) the general dotted rule      — weak-empty-reported-name,
#              weak-truncated-trailing-segment, weak-wrong-source-display-name,
#              weak-drop-module-prefix, weak-last-module-segment-only,
#              weak-missing-separator, weak-transposed-segments,
#              weak-teach-to-the-test.
#     No clause is left untested, and (Q2) is separated from (Q4) by
#     weak-alias-rule-keeps-path, whose sub-domain is the single input class where
#     the two rules disagree.
#   RULES: all FOUR of the renderer's rules carry a rival refuted ON that rule —
#     rule 1 (alias): weak-alias-rule-keeps-path; rule 2 (core):
#     weak-one-core-namespace-only, weak-core-namespace-keeps-path,
#     weak-missing-element-list-tail, weak-general-rule-everywhere; rule 3
#     (abbreviated): weak-missing-abbreviation-mark; rule 4 (general): the eight
#     listed under (Q5). So no rule is one a wrong implementation could get wrong
#     unnoticed — the failure mode the reserved-path dispatch created.
#   BINDERS: two, `modulePath` and `createdName`. Both are MOVED across the reject
#     set, and each is attacked in its own right:
#       * weak-empty-reported-name        (['u','n'],            ['C'])      createdName -> []
#       * weak-truncated-trailing-segment (['t'],                ['A','B'])  createdName truncated
#       * weak-wrong-source-display-name  (['w','d'],            ['N'])      wrong source
#       * weak-general-rule-everywhere    (coreNamespaceB,       ['C'])      rule selection
#       * weak-one-core-namespace-only    (coreNamespaceA,       ['Q'])      rule selection
#       * weak-core-namespace-keeps-path  (coreNamespaceA,       ['K'])      core rule prefix
#       * weak-missing-element-list-tail  (coreNamespaceB,       ['E'])      core rule suffix
#       * weak-missing-abbreviation-mark  (abbreviatedNamespace, ['T'])      abbreviated rule
#       * weak-alias-rule-keeps-path      (abbreviatedNamespace, aliasFactoryName) alias rule
#       * weak-drop-module-prefix         (['p','k','g'],        ['N'])      modulePath dropped
#       * weak-last-module-segment-only   (['u','.','s'],        ['C'])      modulePath narrowed
#       * weak-missing-separator          (['a'],                ['b'])      separator dropped
#       * weak-transposed-segments        (['x','y'],            ['z'])      order swapped
#       * weak-teach-to-the-test          (['t','t'],            ['Z'])      hard-coded input
#     FOURTEEN DISTINCT input points (pts=14). `modulePath` takes eleven distinct
#     values, including all three reserved paths, one genuinely DOTTED path (the
#     nested shape the failing test uses), and paths of five different lengths;
#     `createdName` takes ten. No binder is held at a fixed value by every witness,
#     so neither input is one a rival could mishandle unnoticed, and NO two rivals
#     share a witness. Each pair of rivals whose sub-domains overlap is separated
#     at the input that distinguishes them:
#       * empty-reported-name vs truncated-trailing-segment — the truncation is
#         invisible at a one-character created name, so it is refuted at a
#         two-character one instead.
#       * drop-module-prefix vs last-module-segment-only — narrowing to the last
#         segment is invisible at an undotted module path (every other general-rule
#         witness's shape), so it is refuted at a dotted one instead.
#       * transposed-segments — a transposition is invisible when the two segments
#         coincide, so it is refuted at segments of different lengths.
#       * general-rule-everywhere vs one-core-namespace-only — the second agrees
#         with gold on the reserved core namespace the first is refuted on, so the
#         two are refuted on the two DIFFERENT reserved core namespaces.
#       * core-namespace-keeps-path vs missing-element-list-tail — the two perturb
#         opposite ends of the same rule, and are refuted on the two different
#         reserved core namespaces so neither witness could close the other.
#       * alias-rule-keeps-path vs missing-abbreviation-mark — the alias rival is
#         wrong ONLY at the reserved simple name, where the abbreviation rival is
#         right, so their witnesses differ in the created name.
#
# AXIOM_TESTS: dropped, empty. The sibling ships one A-reference probe validating
#   its deep model against the real callee chain; that lane is G-AX's job and this
#   gate ignores AXIOM_TESTS. This bundle declares NO axiom at all (mapping.md §3:
#   the behaviour is a total function of the placeholder's own carried data, modeled
#   deeply in the `pure` region), so G-AX is skipped for it regardless.
AXIOM_TESTS = []
