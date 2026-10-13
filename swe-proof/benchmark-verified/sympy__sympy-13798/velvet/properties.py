"""properties.py — G-PBT falsification battery for sympy__sympy-13798 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct resolveMulSeparators`` obligation survives with its header
intact) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a single optional-string input):

  resolveMulSeparators (sym : Option String)
      return (out : Except MulErr (String × String))
    ensures out = resolveSpec sym            -- THE load-bearing (and only) clause

with ``resolveSpec`` a fully-unfolded ``def`` in the ``pure`` region:

  resolveSpec sym = Except.ok (firstSep sym, numSep sym)

so the single clause pins THREE independent top-level facts about the result,
because the returned carrier has three independently-observable components:

  * TOTALITY — the outcome is always the resolved alternative (``Except.ok``);
    the ``MulErr.unresolved`` alternative is never produced, for ANY input.
  * FIRST COMPONENT (``firstSep sym``) — the standard separator of a recognized
    named choice, otherwise the supplied string used verbatim.
  * SECOND COMPONENT (``numSep sym``) — the standard separator for the
    falling-back lookup key when that key is recognized; otherwise the dot when
    the trimmed string is a spacing-only form, and the supplied string verbatim
    in every remaining case.

``resolveSpec`` is GROUNDED in the input (a total function of ``sym`` built from
``mulTable`` / ``numKey`` / ``spacingSyms`` / ``pyStrip``, all transparent
``def``s), NOT an opaque answer-key: the ``axioms`` region is EMPTY (mapping.md
§1, §3 — every impl op is R/I, validated wholesale by G-CONF). So there is no
ungrounded oracle to echo, and the ungrounded-oracle probe is replaced by honest
positive controls. The sole INPUT BINDER is ``sym``.

THE CARRIER IS FULLY TRANSPARENT. Every pure-region function computes on
``String`` / ``Option String`` / ``Char`` literals, so a witness reaches the
method contract through Velvet's own tester machinery and ``decide`` settles the
whole equality at a concrete input — no opaque leaf, so no witness binds a
hypothesis and there is no joint-satisfiability obligation. Measured while
authoring: every pure-region fact this battery relies on
(``pyStrip``/``spacingSyms``/``mulTable``/``numKey``/``firstSep``/``numSep``)
closes under a bare ``decide``; only the ``Except`` equality needed a
``DecidableEq`` instance, which each witness derives for itself (an instance, not
an assumption).

BINDER STRUCTURE (read before judging binder coverage). The postcondition
depends on the single binder ``sym``, but that binder has FIVE behaviourally
distinct sub-domains, and a rival can be wrong on any one of them alone. The
witnesses probe all five, at NINE distinct input points, so no rival is refuted
at the same value as another unless it fails there for the same reason:

  * the ABSENT choice (``none``) — the default resolution both components take
    when nothing is supplied;
  * a RECOGNIZED name (``some "dot"``) — the table-lookup arm of both components;
  * the EMPTY string (``some ""``) — falsy, so the second component's lookup key
    falls back, AND it is itself a spacing-only form (both routes reach the dot);
  * a SPACING-ONLY form (``some "\\,"``, ``some "\\;"``, ``some " "``,
    ``some " \\, "`` with ASCII surrounding whitespace, and
    ``some "\x0c\\,\x0c"`` with NON-ASCII surrounding whitespace) — the
    sub-domain where the two components DISAGREE: the first is the string
    verbatim, the second is the dot. This is the discriminating sub-domain of
    the modeled feature, so five of the nine witness points live here, each
    isolating a different defect;
  * an ARBITRARY non-spacing string (``some "*"``, ``some "x"``) — accepted
    verbatim by BOTH components.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION (nagini ``frame-mut-general-append`` /
    ``frame-mut-numeric-append``) — VACUOUS. The nagini sibling carries these as
    MANDATORY rivals because its selector input is held at a FRACTIONAL heap
    permission that an impl can illegally overwrite (an append needs the full
    predicate). Lean and Velvet are referentially transparent: ``sym`` is an
    immutable value, this bundle declares NO ``mut`` binder over any input, and
    there is no heap and no aliasing — so there is no read-only input to
    overwrite and no substitute probe to build. Not fabricated (per the porting
    map: this class is vacuous on Lean/Velvet).
  * PARTIAL-DOMAIN / VALUE — APPLIES; the heart of the port. Each nagini
    partial-domain rival re-expresses onto one component of the returned pair,
    plus four rivals ADDED for structure this carrier exposes and nagini's does
    not (see the accounting at the bottom).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no
    loop and no recursion), so there is no control flow here to make diverge: a
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
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A. ``resolveSpec`` is a total ``def`` over the
    method's own input and the ``axioms`` region is empty; there is no answer key
    to echo. Replaced by the honest positive controls.
  * ADMISSIBILITY (nagini ``admiss-general-thinspace`` /
    ``admiss-numeric-thinspace``) — RE-AIMED, not dropped. See below.
  * AXIOM lane (nagini's 2 ``trimmed`` probes) — DROPPED. The axiom lane is
    G-AX's job and this gate ignores ``AXIOM_TESTS`` regardless; this bundle
    declares no axiom at all (mapping.md §1: G-AX skips).

DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE SEMANTICS
against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` / ``if`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so
each witness reaches it through Velvet's tester machinery:
``resolveMulSeparatorsTester <sym> = false`` says the extracted program's result
violates the postcondition at that concrete input. The ``Except _ _`` post-image
needs a ``DecidableEq`` the tester does not synthesize, so each witness derives
it first. Checked in a file whose ``prove_correct`` block has been stripped (so
no tactic script can mask the verdict); there are no ``require`` clauses (the
pre-conditions region is empty), so every input reaches the postcondition. Both
halves were checked out-of-band with ``scripts/lean_verify.sh`` for every reject
case: the witness elaborates against the rival (exit 0) and fails against the
frozen solution (nonzero, ``decide`` reporting the proposition false).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13798"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct resolveMulSeparators
# header present.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the two independent component
# resolutions and the returned pair. Every rival and the two reshape positives
# replace it as a unit.
_IMPL = (
    "    -- Resolve each separator independently, mirroring the two resolution sites.\n"
    "    -- General separator: the standard separator of a recognized named symbol,\n"
    "    -- otherwise the supplied symbol used verbatim.\n"
    "    let first : String :=\n"
    "      match mulTable sym with\n"
    "      | some v => v\n"
    "      | none   => sym.getD \"\"\n"
    "    -- Numeric separator: the standard separator for the falling-back numeric key\n"
    "    -- when recognized; otherwise the dot for a spacing-only (trimmed) symbol, and\n"
    "    -- the supplied symbol verbatim in every remaining case.\n"
    "    let numbers : String :=\n"
    "      match mulTable (some (numKey sym)) with\n"
    "      | some v => v\n"
    "      | none   =>\n"
    "        if spacingSyms.contains (pyStrip (sym.getD \"\")) then \" \\\\cdot \" else sym.getD \"\"\n"
    "    -- The resolution is total: always a resolved pair.\n"
    "    return Except.ok (first, numbers)\n"
)

# The first line of the impl region — the admissibility variant prepends an
# in-region `assert` immediately before it, keeping the whole frozen body.
_FIRST_IMPL_LINE = (
    "    -- Resolve each separator independently, mirroring the two resolution sites.\n"
)

# The frozen prove_correct tactic body (unique in the file, elided from the spec
# view). Reject rivals keep it as-is — it fails to close the wrong impl, which is
# the intended rejection, but the WITNESS, not the tactic failure, is what the
# gate scores. The positives that reshape the impl retune it.
_PROOF = (
    "prove_correct resolveMulSeparators by\n"
    "  loom_solve\n"
    "  simp_all [resolveSpec, firstSep, numSep]\n"
)

# ---- reusable impl fragments -------------------------------------------------

# The frozen FIRST-component resolution (table lookup, else the string verbatim).
_GEN_OK = (
    "    let first : String :=\n"
    "      match mulTable sym with\n"
    "      | some v => v\n"
    "      | none   => sym.getD \"\"\n"
)

# The frozen SECOND-component resolution (falling-back key, else dot-for-spacing,
# else the string verbatim).
_NUM_OK = (
    "    let numbers : String :=\n"
    "      match mulTable (some (numKey sym)) with\n"
    "      | some v => v\n"
    "      | none   =>\n"
    "        if spacingSyms.contains (pyStrip (sym.getD \"\")) then \" \\\\cdot \" else sym.getD \"\"\n"
)

_RETURN_PAIR = "    return Except.ok (first, numbers)\n"


def _impl(body, proof=None):
    """Solution.lean with the impl body replaced (and optionally the proof)."""
    out = _swap(_BASE, _IMPL, body)
    if proof is not None:
        out = _swap(out, _PROOF, proof)
    return out


# ---- witness preamble --------------------------------------------------------
# Reach the method contract through Velvet's own tester machinery:
# `resolveMulSeparatorsTester <sym> = false` says the extracted program's result
# violates the postcondition at that concrete input. `deriving instance
# DecidableEq for Except` supplies the equality the tester needs on the
# `Except _ _` post-image — an INSTANCE, derived, not an assumption. Appended to
# BOTH the rival and the frozen file, so it exists on both sides by construction.
_WIT_PRE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for resolveMulSeparators\n"
    "prove_precondition_decidable_for resolveMulSeparators\n"
    "prove_postcondition_decidable_for resolveMulSeparators\n"
    "derive_tester_for resolveMulSeparators\n\n"
)


def _witness(sym):
    return _WIT_PRE + (
        f"example : resolveMulSeparatorsTester {sym} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the single
    # postcondition clause is over-fit to the frozen code SHAPE =>
    # SPEC-TOO-STRONG. (Nagini: pos-control-general-reorder /
    # pos-control-numeric-reorder, whose branch-reorder reshape re-expresses here
    # as a component-order swap and a lookup-key restructure.)
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest HONEST correct impl: return the grounded pure model directly.
        # `out` IS `resolveSpec sym`, so the clause holds on the whole domain and
        # the reproof is a bare `loom_solve` (nothing left to unfold).
        "module": _impl(
            "    return resolveSpec sym\n",
            proof="prove_correct resolveMulSeparators by\n  loom_solve\n"),
        "rationale": (
            "the post-image `resolveSpec sym` is GROUNDED in the input (a total "
            "function of `sym` built from transparent defs, no opaque answer key "
            "— the axioms region is empty), so `return resolveSpec sym` is the "
            "honest cheapest CORRECT impl. It MUST verify — the clause is "
            "literally `out = resolveSpec sym` — else SPEC-TOO-STRONG. It also "
            "doubles as proof the spec is not echo-vulnerable: any wrong "
            "constant or partial echo fails the whole-pair equality, as the eight "
            "rivals below demonstrate."),
    },
    {
        "id": "pos-control-component-order",
        "kind": "soundness",
        "expect": "verify",
        # Resolve the SECOND component first, then the first. The two resolutions
        # are independent, so evaluation order is immaterial; the frozen proof
        # script closes it unchanged.
        "module": _impl(_NUM_OK + _GEN_OK + _RETURN_PAIR),
        "rationale": (
            "structurally different CORRECT reshape: the two independent "
            "component resolutions are computed in the opposite order (numeric "
            "first, general second), the returned pair unchanged. Neither "
            "resolution reads the other, so `out = resolveSpec sym` still holds "
            "on the whole domain and the frozen proof closes with no retune. A "
            "faithful reorder that could NOT verify would mean the clause is "
            "over-fit to the statement order => SPEC-TOO-STRONG. (Nagini: "
            "pos-control-{general,numeric}-reorder — the branch-reorder reshape.)"),
    },
    {
        "id": "pos-control-inline-fallback-key",
        "kind": "soundness",
        "expect": "verify",
        # A DEEPER reshape: inline the falling-back lookup key so it falls back
        # ONLY for the absent choice, not for the empty string. Still correct —
        # the empty string is itself a spacing-only form, so both routes reach the
        # dot for it — but the equality now needs a genuine case split to prove,
        # which is why this positive gets a retuned script. Landing it is what
        # shows the clause is not over-fit to the frozen key expression.
        "module": _impl(
            _GEN_OK +
            "    let numbers : String :=\n"
            "      match mulTable (some (match sym with | none => \"dot\" | some s => s)) with\n"
            "      | some v => v\n"
            "      | none   =>\n"
            "        if spacingSyms.contains (pyStrip (sym.getD \"\")) then \" \\\\cdot \" else sym.getD \"\"\n"
            + _RETURN_PAIR,
            proof="prove_correct resolveMulSeparators by\n"
                  "  loom_solve\n"
                  "  all_goals (rcases sym with _ | s\n"
                  "             · simp_all [resolveSpec, firstSep, numSep, numKey]\n"
                  "             · rcases eq_or_ne s \"\" with rfl | hs <;>\n"
                  "               simp_all [resolveSpec, firstSep, numSep, numKey, mulTable,\n"
                  "                 pyStrip, spacingSyms, pyWhitespace])\n"),
        "rationale": (
            "a CORRECT but non-obviously-correct reshape: the second component's "
            "lookup key falls back only for the ABSENT choice, where the frozen "
            "form also falls back for the EMPTY string. Observationally identical "
            "— the empty string is itself one of the spacing-only forms, so the "
            "spacing branch reaches the same dot the fallback key would have — so "
            "`out = resolveSpec sym` still holds everywhere, but proving it needs "
            "a real case split (absent / empty / other), supplied in the retuned "
            "tactic body with the SAME obligation header. Authored as a rival and "
            "RECLASSIFIED: its witness at `some \"\"` failed to elaborate "
            "(`decide` proved the tester TRUE there), which is the carrier telling "
            "us the two forms agree — so it is not wrong on this carrier and ships "
            "as a positive. If a correct impl of this shape could not verify, the "
            "clause would be over-fit to the frozen key expression => "
            "SPEC-TOO-STRONG."),
    },

    # =====================================================================
    # ADMISSIBILITY — this bundle declares NO `require` clause (the
    # pre-conditions region is empty), so the nagini probe "an F2P-shaped input
    # satisfies the precondition" is degenerate here: every input is in-domain
    # by construction and there is no precondition to be too strong. Rather than
    # drop the lane, it is RE-AIMED at the residual total-domain risk — a
    # DEGENERATE post-image, i.e. a clause satisfiable by a constant because the
    # modeled resolution collapses to one value. An in-region `assert` pins four
    # concrete resolutions the spec must simultaneously deliver, spanning the
    # sub-domains where they DIFFER. Liveness verified out of band: a mirror
    # assert claiming a wrong second component for the spacing-only form leaves
    # `⊢ False`, so the assert is a real obligation, not decoration.
    # =====================================================================
    {
        "id": "admiss-nondegenerate-resolutions",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _FIRST_IMPL_LINE,
                "    assert (with_name_prefix `adm (\n"
                "      resolveSpec (some \"\\\\,\") = Except.ok (\"\\\\,\", \" \\\\cdot \") ∧\n"
                "      resolveSpec none = Except.ok (\" \", \" \\\\cdot \") ∧\n"
                "      resolveSpec (some \"dot\") = Except.ok (\" \\\\cdot \", \" \\\\cdot \") ∧\n"
                "      resolveSpec (some \"*\") = Except.ok (\"*\", \"*\")))\n"
                + _FIRST_IMPL_LINE),
            _PROOF,
            "prove_correct resolveMulSeparators by\n"
            "  loom_solve\n"
            "  all_goals simp_all [resolveSpec, firstSep, numSep, mulTable, numKey,\n"
            "    pyStrip, spacingSyms, pyWhitespace]\n"),
        "rationale": (
            "re-aimed admissibility probe. There is no `require` clause, so the "
            "nagini precondition-admits-a-normal-input probe is degenerate; the "
            "residual risk on a total domain is a DEGENERATE post-image. The "
            "in-region assert pins four resolutions the single clause must "
            "deliver at once, chosen to span the sub-domains where they differ: a "
            "spacing-only form (components DISAGREE — verbatim vs the dot), the "
            "absent choice (a single space vs the dot), a recognized name (both "
            "the same standard separator), and an arbitrary string (both "
            "verbatim). No constant pair satisfies all four, so the post-image "
            "provably distinguishes at least four points and the clause cannot be "
            "met by collapsing the resolution. The whole frozen body is kept "
            "verbatim (the assert precedes it) and the obligation header is "
            "unchanged; the tactic body gains the pure-region unfoldings needed "
            "to clear the assert VC. LIVENESS verified out of band: a mirror "
            "assert claiming the spacing-only form's second component is the "
            "string verbatim leaves `⊢ False`, so the assert is not vacuous. "
            "(Nagini: admiss-general-thinspace / admiss-numeric-thinspace, "
            "re-aimed — their fractional-permission content is vacuous here.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries a machine-checked refutation witness at
    # a concrete input (elaborates against the rival, fails against gold) and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test.
    # =====================================================================

    # ---- TOTALITY clause: refuse to resolve an unrecognized choice ----
    {
        "id": "weak-reject-unrecognized",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-image skeleton, narrowed to the first component: an
        # unrecognized choice yields the unresolved alternative instead of being
        # accepted. Attacks TOTALITY — the clause says the outcome is always
        # `Except.ok`.
        "module": _impl(
            "    let first : Except MulErr String :=\n"
            "      match mulTable sym with\n"
            "      | some v => Except.ok v\n"
            "      | none   => Except.error MulErr.unresolved\n"
            + _NUM_OK +
            "    let result : Except MulErr (String × String) := do\n"
            "      let a ← first\n"
            "      return (a, numbers)\n"
            "    return result\n"),
        "refinement": (
            "this is the pre-image behavior: an unrecognized choice is refused "
            "rather than accepted. The whole modeled feature is that the "
            "resolution be TOTAL — the public request is for an arbitrary, "
            "backwards-compatible choice to be honored — so a faithful "
            "counterpart that still refused an unrecognized choice would abort "
            "for exactly the thin-space choice the failing test exercises, and "
            "the two new assertions in that test would raise instead of "
            "comparing. It would NOT resolve. (Nagini: the same pre-image "
            "skeleton its partial-general-unrec-blank case attacks, expressed "
            "here as the refusal the pre-image actually performs on this carrier, "
            "since this bundle models the failure outcome explicitly.)"),
        "rationale": (
            "REJECT from `out = resolveSpec sym` (TOTALITY): `resolveSpec` is "
            "`Except.ok (…)` for EVERY input, so an impl producing "
            "`Except.error MulErr.unresolved` on any input contradicts the clause "
            "there. Refuted at the spacing-only thin-space form `some \"\\\\,\"`, "
            "which is not a recognized name — the rival returns the unresolved "
            "alternative, the spec requires the resolved pair. Varies `sym` to an "
            "unrecognized spacing-only string."),
        "witness": _witness('(some "\\\\,")'),
    },

    # ---- FIRST component: drop the verbatim passthrough ----
    {
        "id": "weak-general-blank-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # The first component resolves an unrecognized choice to a plain space
        # instead of the supplied string. Correct on every recognized name; wrong
        # on every unrecognized one.
        "module": _impl(
            "    let first : String :=\n"
            "      match mulTable sym with\n"
            "      | some v => v\n"
            "      | none   => \" \"\n"
            + _NUM_OK + _RETURN_PAIR),
        "refinement": (
            "resolving an unrecognized choice to a plain space discards the "
            "supplied string in the general position. The failing test pins the "
            "general separator for the thin-space choice to be that string "
            "verbatim between the symbolic factors; a faithful counterpart "
            "emitting a plain space there would print the factors separated by an "
            "ordinary space instead, so the first of the two new assertions would "
            "compare unequal and it would NOT resolve. (Nagini: "
            "partial-general-unrec-blank — the blank-instead-of-verbatim defect, "
            "which on this carrier is expressible without the pre-image's "
            "refusal.)"),
        "rationale": (
            "REJECT from `out = resolveSpec sym` (FIRST component): on the "
            "unrecognized arm `firstSep sym = sym.getD \"\"`, but the rival "
            "returns a plain space. Refuted at the arbitrary non-spacing string "
            "`some \"*\"`, where the spec's first component is `\"*\"` — a "
            "DIFFERENT sub-domain from the spacing-only forms the other rivals "
            "use, so the two components' verbatim behavior is probed where they "
            "AGREE and the defect cannot hide behind the dot fallback."),
        "witness": _witness('(some "*")'),
    },

    # ---- FIRST component: a recognized name gets the wrong standard separator --
    {
        "id": "weak-recognized-wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Every recognized name resolves to one fixed standard separator in the
        # first component. Correct on unrecognized strings and on the one name
        # whose separator it happens to be; wrong on the others.
        "module": _impl(
            "    let first : String :=\n"
            "      match mulTable sym with\n"
            "      | some _ => \" \\\\times \"\n"
            "      | none   => sym.getD \"\"\n"
            + _NUM_OK + _RETURN_PAIR),
        "refinement": (
            "collapsing every recognized name to one fixed standard separator "
            "breaks the long-standing behavior of the OTHER names, which the "
            "change must preserve — the feature is explicitly backwards "
            "compatible. A faithful counterpart would print the wrong separator "
            "for the named choices, so the existing assertion in the same failing "
            "test that pins the dot name's separator, and the whole "
            "already-passing test devoted to the named choices, would compare "
            "unequal. It would NOT resolve. (Nagini: "
            "partial-general-dot-as-times — the same swap of two recognized "
            "outputs.)"),
        "rationale": (
            "REJECT from `out = resolveSpec sym` (FIRST component, recognized "
            "arm): `firstSep` returns each name's OWN table value, so a fixed "
            "separator contradicts the clause at every name whose separator "
            "differs. Refuted at the recognized name `some \"dot\"` — the "
            "RECOGNIZED sub-domain, which no other rival probes, so the "
            "table-lookup arm is not left untested."),
        "witness": _witness('(some "dot")'),
    },

    # ---- SECOND component: drop the spacing-only dot fallback ----
    {
        "id": "weak-numeric-no-spacing-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # The second component resolves an unrecognized key to the supplied
        # string verbatim, skipping the spacing-only dot fallback entirely.
        # Correct on every non-spacing string; wrong on the spacing-only ones.
        "module": _impl(
            _GEN_OK +
            "    let numbers : String :=\n"
            "      match mulTable (some (numKey sym)) with\n"
            "      | some v => v\n"
            "      | none   => sym.getD \"\"\n"
            + _RETURN_PAIR),
        "refinement": (
            "dropping the spacing-only fallback means a bare spacing form is "
            "used verbatim between numeric factors, where the specified behavior "
            "substitutes the dot precisely because a bare spacing command is "
            "ambiguous between two numbers. The failing test's second new "
            "assertion pins exactly that: with the thin-space choice, adjacent "
            "numeric factors must be separated by the dot, not by the thin space. "
            "A faithful counterpart without the fallback would print the thin "
            "space there and NOT resolve. (Nagini: "
            "partial-numeric-no-spacing-fallback — the same dropped fall-back.)"),
        "rationale": (
            "REJECT from `out = resolveSpec sym` (SECOND component): for a "
            "spacing-only form `numSep sym` is the dot, but the rival returns the "
            "string verbatim. Refuted at `some \"\\\\;\"` — a spacing-only form "
            "DISTINCT from the thin space the totality rival uses, so the two "
            "rivals do not share an input and each demonstrates its own "
            "sub-domain."),
        # Raw literal: Lean receives `(some "\\;")`, i.e. the spacing form `\;`.
        "witness": _witness(r'(some "\\;")'),
    },

    # ---- SECOND component: drop the falling-back lookup key ----
    {
        "id": "weak-numeric-no-fallback-key",
        "kind": "uniqueness",
        "expect": "reject",
        # The second component looks the supplied choice up directly instead of
        # through the falling-back key. Correct on every non-falsy string; wrong
        # on the absent choice, whose direct lookup yields the general default.
        "module": _impl(
            _GEN_OK +
            "    let numbers : String :=\n"
            "      match mulTable sym with\n"
            "      | some v => v\n"
            "      | none   =>\n"
            "        if spacingSyms.contains (pyStrip (sym.getD \"\")) then \" \\\\cdot \" else sym.getD \"\"\n"
            + _RETURN_PAIR),
        "refinement": (
            "looking the supplied choice up directly, rather than through the "
            "key that falls back when nothing is supplied, gives numeric factors "
            "the same single space the general position gets by default — where "
            "the specified behavior separates numbers by the dot. Adjacent "
            "numeric factors are never juxtaposed with only a space; the failing "
            "test carries many already-passing assertions in which unsupplied "
            "numeric factors are printed with the dot, so a faithful counterpart "
            "without the fallback key would break them and NOT resolve. (Nagini: "
            "partial-numeric-none-blank — the same defect on the unset selector.)"),
        "rationale": (
            "REJECT from `out = resolveSpec sym` (SECOND component, fallback "
            "key): `numSep none` looks up the default key and yields the dot, but "
            "the rival's direct lookup yields the absent choice's own table "
            "value, a single space. Refuted at the ABSENT choice `none` — the one "
            "sub-domain where `sym` carries no string at all, which no other "
            "rival probes."),
        "witness": _witness("(none : Option String)"),
    },

    # ---- SECOND component: test the spacing set WITHOUT trimming ----
    {
        "id": "weak-numeric-untrimmed-spacing-test",
        "kind": "uniqueness",
        "expect": "reject",
        # The spacing-only membership test is applied to the supplied string as
        # given, not to its trimmed form. Correct on every already-trimmed
        # string; wrong on a spacing form carrying surrounding whitespace.
        "module": _impl(
            _GEN_OK +
            "    let numbers : String :=\n"
            "      match mulTable (some (numKey sym)) with\n"
            "      | some v => v\n"
            "      | none   =>\n"
            "        if spacingSyms.contains (sym.getD \"\") then \" \\\\cdot \" else sym.getD \"\"\n"
            + _RETURN_PAIR),
        "refinement": (
            "testing spacing-only membership on the untrimmed string misses a "
            "spacing form that carries surrounding whitespace, so such a choice "
            "is used verbatim between numeric factors instead of falling back to "
            "the dot. The specified behavior trims before testing, precisely so "
            "that a spacing command remains recognized as spacing when the user "
            "pads it. A faithful counterpart omitting the trim would print the "
            "padded spacing form between adjacent numbers, reintroducing the "
            "ambiguity the fallback exists to remove, so it would NOT resolve the "
            "numeric half of the failing test for any padded spacing choice. (No "
            "nagini counterpart: nagini's selector carrier is a code-point "
            "sequence and its sibling folds the trim into an axiomatized callee, "
            "so the trim is not separately attackable there; on this carrier the "
            "trim is a transparent pure-region function and IS attackable, so the "
            "rival is ADDED.)"),
        "rationale": (
            "REJECT from `out = resolveSpec sym` (SECOND component, trim): "
            "`numSep` tests membership of the TRIMMED string, so a padded spacing "
            "form still reaches the dot; the rival's untrimmed test misses it and "
            "returns the padded string. Refuted at `some \" \\\\, \"` — a "
            "spacing form WITH surrounding whitespace, an input no other rival "
            "uses and the only one on which the trim is observable."),
        "witness": _witness('(some " \\\\, ")'),
    },

    # ---- SECOND component: the trim's WHITESPACE SET is too narrow ----
    {
        "id": "weak-numeric-ascii-whitespace-set",
        "kind": "uniqueness",
        "expect": "reject",
        # The trim before the spacing-only membership test uses only the four
        # ASCII whitespace forms instead of the full whitespace set the spec
        # trims. A strictly HARDER near-miss than the untrimmed rival above: it
        # DOES trim, and agrees with the spec on every symbol padded with
        # ordinary spaces/tabs/newlines — the padded-thin-space input that
        # refutes the untrimmed rival is resolved correctly here. It diverges
        # only on a symbol padded with a whitespace character OUTSIDE the ASCII
        # four, which is the narrowest sub-domain any rival in this battery
        # attacks. Added by the audit: the untrimmed rival probes only WHETHER
        # the trim happens, leaving WHICH characters it removes unattacked,
        # and mapping.md §2 flags exactly that set as the modeling risk.
        # Written as in-region local bindings (not a helper `def`) so the
        # witness stays stated in vocabulary gold and the rival SHARE, and so
        # the claim remains kernel-reducible — a stdlib trim would leave
        # `decide` stuck rather than deciding, which discriminates nothing.
        "module": _impl(
            "    -- the four ASCII whitespace forms only, NOT the full set the\n"
            "    -- specified trim removes.\n"
            "    let asciiWs : Char → Bool := fun c =>\n"
            "      c = ' ' || c = '\\t' || c = '\\n' || c = '\\r'\n"
            "    let asciiStrip : String → String := fun s =>\n"
            "      String.mk (((s.toList.dropWhile asciiWs).reverse.dropWhile\n"
            "        asciiWs).reverse)\n"
            + _GEN_OK +
            "    let numbers : String :=\n"
            "      match mulTable (some (numKey sym)) with\n"
            "      | some v => v\n"
            "      | none   =>\n"
            "        if spacingSyms.contains (asciiStrip (sym.getD \"\")) then \" \\\\cdot \" else sym.getD \"\"\n"
            + _RETURN_PAIR),
        "refinement": (
            "trimming only the four ASCII whitespace forms leaves any OTHER "
            "whitespace character in place, so a spacing-only symbol padded "
            "with such a character is no longer recognized as spacing-only and "
            "is used verbatim between numeric factors instead of falling back "
            "to the dot. The specified behavior trims the full whitespace set, "
            "so the recognition survives any whitespace padding. A faithful "
            "counterpart with the narrow set would print the padded spacing "
            "form between adjacent numbers — reintroducing exactly the "
            "ambiguity between two numbers that the dot fallback exists to "
            "remove — for every symbol padded outside the ASCII four, so it "
            "would NOT resolve the numeric half of the failing test on that "
            "sub-domain. (No nagini counterpart, and for a sharper reason than "
            "the untrimmed rival: the sibling axiomatizes the trim as an "
            "unchanged callee, so WHICH characters it removes is assumed there "
            "rather than modeled, and is not attackable at all. Here the "
            "predicate is a transparent pure-region function, so the SET is "
            "attackable and is attacked. ADDED by the audit.)"),
        "rationale": (
            "REJECT from `out = resolveSpec sym` (SECOND component, the trim's "
            "CHARACTER SET — not merely whether a trim occurs): `numSep` tests "
            "membership of the string trimmed of the full whitespace set, so a "
            "spacing form padded with any whitespace character reaches the dot; "
            "the rival's ASCII-only trim leaves the padding in place, misses "
            "the membership, and returns the padded string. Refuted at "
            "`some \"\\x0c\\\\,\\x0c\"` — a thin space padded with a form feed, "
            "a whitespace character in the specified set but NOT among the "
            "ASCII four. That input is distinct from every other witness point "
            "and is the ONLY class on which the trim's set is observable: this "
            "rival agrees with the spec at `some \" \\\\, \"` (the "
            "untrimmed rival's point) and on every already-trimmed string, so "
            "it is the strictest near-miss in the battery and no other rival "
            "covers it."),
        "witness": _witness('(some "\\x0c\\\\,\\x0c")'),
    },

    # ---- SECOND component: always fall back to the dot ----
    {
        "id": "weak-numeric-always-dot",
        "kind": "uniqueness",
        "expect": "reject",
        # The second component resolves every unrecognized key to the dot,
        # skipping the verbatim case. The DUAL over-fix of the dropped fallback:
        # correct on spacing-only forms, wrong on every other string.
        "module": _impl(
            _GEN_OK +
            "    let numbers : String :=\n"
            "      match mulTable (some (numKey sym)) with\n"
            "      | some v => v\n"
            "      | none   => \" \\\\cdot \"\n"
            + _RETURN_PAIR),
        "refinement": (
            "the DUAL over-fix: substituting the dot for EVERY unrecognized "
            "choice, not only the spacing-only ones. The specified behavior "
            "substitutes the dot only where a bare spacing command would be "
            "ambiguous and otherwise honors the supplied choice in the numeric "
            "position too; the feature requested is that an arbitrary choice be "
            "honored. A faithful counterpart substituting the dot everywhere "
            "would silently override any non-spacing choice a user supplies "
            "between numeric factors — the very override the change exists to "
            "narrow — so it would not deliver the requested behavior and would "
            "NOT resolve. (No nagini counterpart: its sibling attacks the missing "
            "fallback but not the over-applied one; on this carrier both "
            "directions of the fallback condition are transparent, so the dual is "
            "ADDED.)"),
        "rationale": (
            "REJECT from `out = resolveSpec sym` (SECOND component, verbatim "
            "arm): for a non-spacing unrecognized string `numSep sym` is the "
            "string verbatim, but the rival returns the dot. Refuted at "
            "`some \"x\"` — an arbitrary non-spacing string, and a point distinct "
            "from the `some \"*\"` the first-component rival uses, so the two "
            "verbatim arms are probed separately."),
        "witness": _witness('(some "x")'),
    },

    # ---- STRUCTURE: the two components returned in the wrong positions ----
    {
        "id": "weak-swapped-components",
        "kind": "uniqueness",
        "expect": "reject",
        # Both components are computed EXACTLY as specified, then returned in the
        # opposite positions. Attacks the combination rather than either
        # resolution: wrong exactly where the two components differ.
        "module": _impl(
            _GEN_OK + _NUM_OK +
            "    return Except.ok (numbers, first)\n"),
        "refinement": (
            "the two separators occupy distinct roles — one is placed between "
            "symbolic factors, the other between numeric ones — and exchanging "
            "them mixes up which is used where. A faithful counterpart that "
            "assigned each computed separator to the other role would print the "
            "dot between the symbolic factors and the supplied string between the "
            "numeric ones: both new assertions of the failing test compare "
            "unequal simultaneously, so it would NOT resolve. (No nagini "
            "counterpart: nagini contracts the two separators as two SEPARATE "
            "functions, each with its own postcondition, so no single impl can "
            "exchange them. This bundle returns them as one pair, which makes the "
            "COMBINATION attackable — a genuinely new degree of freedom on this "
            "carrier, so the rival is ADDED.)"),
        "rationale": (
            "REJECT from `out = resolveSpec sym` (STRUCTURE of the returned "
            "pair): the clause pins the pair componentwise as "
            "`(firstSep sym, numSep sym)`, so exchanging them contradicts it "
            "wherever the two differ — note both resolutions are computed "
            "correctly, so no per-component rival covers this. Refuted at "
            "`some \" \"`, a bare space: the first component is that space "
            "verbatim and the second is the dot, so the exchange is observable. "
            "That input is distinct from every other witness point and is the "
            "shortest spacing-only form on which the components disagree."),
        "witness": _witness('(some " ")'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (2 soundness
# positives, 2 admissibility, 2 frame-mutation rivals, 4 partial-domain rivals)
# plus a 2-case AXIOM lane. It contracts TWO functions — one per separator — each
# with its own postcondition over a code-point-sequence selector; this bundle
# models the SAME purely-functional core as ONE method returning BOTH separators
# as a pair, over a value-level `Option String` (mapping.md §2). That narrowing
# is why the case count does not match in either direction: the two frame rivals
# and the two admissibility probes lose their fractional-permission content,
# while the paired return and the transparent trim expose structure nagini's
# carrier does not have.
#
#   sibling case                        -> here                          disposition
#   -------------------------------------------------------------------------------
#   pos-control-general-reorder         -> pos-control-component-order   PORTED
#   pos-control-numeric-reorder         -> pos-control-component-order   PORTED (merged)
#   (no sibling)                        -> pos-control-direct-model      ADDED
#   (no sibling)                        -> pos-control-inline-fallback-key ADDED
#   admiss-general-thinspace            -> admiss-nondegenerate-...      RE-AIMED
#   admiss-numeric-thinspace            -> admiss-nondegenerate-...      RE-AIMED (merged)
#   frame-mut-general-append            -> (none)                        VACUOUS
#   frame-mut-numeric-append            -> (none)                        VACUOUS
#   partial-general-unrec-blank         -> weak-reject-unrecognized      PORTED (split)
#                                       -> weak-general-blank-passthrough  PORTED (split)
#   partial-numeric-no-spacing-fallback -> weak-numeric-no-spacing-fallback PORTED
#   partial-general-dot-as-times        -> weak-recognized-wrong-separator PORTED
#   partial-numeric-none-blank          -> weak-numeric-no-fallback-key   PORTED
#   (no sibling)                        -> weak-numeric-untrimmed-...    ADDED
#   (no sibling)                        -> weak-numeric-ascii-whitespace-set ADDED (audit)
#   (no sibling)                        -> weak-numeric-always-dot       ADDED
#   (no sibling)                        -> weak-swapped-components       ADDED
#   (no sibling; authored as a rival)   -> pos-control-inline-fallback-key RECLASSIFIED
#   AXIOM_TESTS (2)                     -> (none)                        DROPPED (G-AX)
#   diverge-* / nonterm-*               -> (none)                        SPEC-CLOSED
#
# 6 ported (2 merged pairs collapsing 4 sibling cases), 6 added, 1 reclassified,
# 2 vacuous, 2 dropped = 13 SPEC cases (3 soundness, 1 admissibility,
# 9 uniqueness).
#
# PORTED (positives): the sibling's two branch-reorder controls reorder the three
#   recognized-name branches in each of its two functions. Here the recognized-name
#   lookup is a single `mulTable` match, not a branch chain, so the analogous
#   reshape is at the next structural level up — the ORDER of the two independent
#   component resolutions — and one case covers what the sibling needed two for
#   (both separators live in one method). Both merged positives verify.
# ADDED (2 positives): the direct grounded-model control (the sibling has no
#   equivalent because its oracles are @Pure helpers rather than the whole
#   post-image) and the inline-fallback-key reshape, which is the only positive
#   here whose proof needed real authoring — a three-way case split. Kept because
#   a positive that closes only under the frozen script tests less than one that
#   forces a reproof.
# PORTED (rivals): the sibling's four partial-domain rivals re-express onto the
#   two components of the returned pair; its unrecognized-selector rival SPLITS in
#   two here, because this bundle models the pre-image's refusal explicitly (an
#   `Except` alternative the sibling's carrier has no room for) as well as the
#   wrong-value defect. Every refinement argument carries over unchanged in
#   substance: a faithful counterpart with that defect prints the wrong separator
#   in the general position, in the numeric position, for a named choice, or for
#   the unsupplied default — each contradicting an assertion in the failing test.
# ADDED (4 rivals): the untrimmed spacing test, the trim's ASCII-only whitespace
#   SET, the over-applied dot, and the swapped components. All four attack
#   structure the sibling's carrier does not expose — the trim is a transparent
#   pure-region function here rather than an axiomatized callee, so both WHETHER
#   it happens and WHICH characters it removes are attackable; the fallback
#   condition is attackable in BOTH directions; and returning the two separators
#   as one pair makes their COMBINATION attackable, which two
#   separately-contracted functions cannot be.
# ADDED BY THE AUDIT (1): weak-numeric-ascii-whitespace-set. The port's
#   untrimmed rival probes only whether a trim occurs; the CHARACTER SET it
#   removes was left unattacked, though mapping.md §2 names that set as the
#   modeling risk (the stdlib trim is not a faithful model of the specified one).
#   The new rival trims the four ASCII forms and is refuted at a thin space
#   padded with a form feed — an input on which it diverges from the spec while
#   AGREEING with it at the untrimmed rival's point, so it is a strictly harder
#   near-miss and no existing case subsumes it. Its whitespace predicate is
#   written as in-region local bindings rather than a stdlib call, which keeps
#   the witness kernel-reducible: measured while auditing, the same rival built
#   on `String.trim` leaves `decide` STUCK ("did not reduce to isTrue or
#   isFalse") on the rival side, so it would have attested to nothing.
# RECLASSIFIED (1): the inline-fallback-key variant was authored as a rival
#   attacking the falling-back key on the EMPTY string. Its witness at
#   `some ""` did NOT elaborate — `decide` proved the tester TRUE there — because
#   the empty string is itself one of the spacing-only forms, so the spacing
#   branch reaches the same dot the fallback key would have. That is the carrier
#   collapsing a distinction, i.e. the variant is NOT wrong here, so per the
#   porting rules it was not shipped as a reject case with an undemonstrated
#   witness; it ships as a soundness positive with a proof that closes.
# VACUOUS (2 frame rivals): the sibling holds its selector at a FRACTIONAL heap
#   permission and mutates it, which must fail for insufficient permission before
#   any postcondition reasoning. Velvet is referentially transparent: `sym` is an
#   immutable value, no input is declared `mut`, and there is no heap and no
#   aliasing — there is no read-only input to overwrite. Not fabricated.
# RE-AIMED (2 admissibility probes): the sibling self-calls on an F2P-shaped
#   selector to show the fractional-permission precondition admits it. This
#   bundle has NO `require` clause, so every input is in-domain and that probe is
#   degenerate. Re-aimed at the residual total-domain risk (a degenerate
#   post-image) with a live in-region assert; merged into one case since one
#   method carries both separators.
# DROPPED (2 axiom probes): the sibling axiomatizes the trim as an A-reference.
#   This bundle declares NO axiom — the trim is modeled deeply as `pyStrip` /
#   `pyWhitespace` (mapping.md §1, §3.2, and G-AX records a skip for exactly this
#   reason) — and the axiom lane is G-AX's job regardless; this gate ignores
#   AXIOM_TESTS.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
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
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
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
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
# WITNESS POINTS (pts): nine DISTINCT inputs across the nine rivals —
#   `some "\\,"` (spacing-only thin space), `some "*"` (arbitrary non-spacing),
#   `some "dot"` (recognized name), `some "\\;"` (a second spacing-only form),
#   `none` (absent choice), `some " \\, "` (ASCII-padded spacing form),
#   `some "\x0c\\,\x0c"` (NON-ASCII-padded spacing form), `some "x"` (a
#   second arbitrary string), `some " "` (bare space). No two rivals share an
#   input, so no rival's claimed sub-domain rests on another's demonstration, and
#   the single binder `sym` is varied across all five of its behaviourally
#   distinct sub-domains. The near-miss families are separated deliberately: the
#   dropped-fallback and over-applied-dot rivals attack OPPOSITE directions of the
#   same condition and are refuted on opposite sides of it (`some "\\;"` vs
#   `some "x"`), and the two trim rivals form a strict chain — the untrimmed one
#   agrees with gold on every already-trimmed string, and the ASCII-set one
#   additionally agrees on every string the untrimmed rival gets wrong, so it is
#   the strictest near-miss in the battery and is refuted at the only input class
#   on which the trim's character set is observable at all.
