"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-25479 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes.
Each ``SPEC_TESTS`` case is a full ``Solution.lean`` variant produced by REGION
SURGERY: only text strictly inside one ``-- impl-start`` / ``-- impl-end``
region, or inside a ``prove_correct <name> by`` tactic body, is replaced. Both
are elided from the consumer spec view, so ``markers.same_spec`` holds by
construction and both ``prove_correct`` obligations survive; every rejection is
therefore attributable to the frozen contract, never to a tampered spec.

``expect="verify"`` passes iff (in scope AND verifies). ``expect="reject"``
passes iff (in scope AND does NOT verify AND its ``witness`` DISCRIMINATES: the
witness must ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE — two independent obligations, four input binders, four
top-level postcondition clauses.

  OBLIGATION 1 ``registeredColormap (cmap : Colormap) (name : String)
                  return (out : Colormap)``
    Which colormap ends up stored under a chosen registration name. Binders:
    ``cmap`` (itself three observable fields: the advertised name, the
    end-style, the colour lookup table) and ``name``. Three INDEPENDENT
    top-level clauses:

      (R1) ensures out.name = name                    the stored colormap
           advertises the name it was stored under, whatever name it advertised
           before — the load-bearing clause, and the one whose sub-domain is
           exactly ``cmap.name ≠ name``.
      (R2) ensures out.extendStyle = cmap.extendStyle  storing preserves the
           end-style.
      (R3) ensures out.lookupTable = cmap.lookupTable  storing preserves the
           colour lookup table, rows and order.

    R1 is a REPLACEMENT clause (its right-hand side is the ``name`` binder, so
    an impl must actually take it) while R2/R3 are PRESERVATION clauses (their
    right-hand sides are ``cmap`` fields). The two directions fail differently,
    so each gets its own rival, and each clause additionally carries a NEAR-MISS
    that agrees with the frozen impl on strictly more of the domain than the
    blanket rival does: R1's moves the guard rather than deleting it, R2's makes
    the preservation conditional on R1's guard, R3's keeps every row and gets
    only the order wrong.

  OBLIGATION 2 ``colormapsEqual (a : Colormap) (b : Colormap)
                  return (out : Bool)``
    Whether two colormaps are the same colormap value. Binders ``a`` and ``b``.
    ONE top-level clause over a FULLY TRANSPARENT pure predicate:

      (E) ensures out = colormapEqSpec a b
          where ``colormapEqSpec a b = decide (a.extendStyle = b.extendStyle)
                                       && decide (a.lookupTable = b.lookupTable)``

    (E) is grounded in the inputs — ``colormapEqSpec`` is spelled out in the
    frozen pure region as a decidable function of the two operands, with no
    opaque callee and no answer-key an impl could echo. So (E) has a UNIQUE
    satisfier and every rival below is refuted at a literal input by ``decide``:
    the carrier computes, and no conditioning is needed anywhere in this
    battery.
    The discriminating content of (E) is an ABSENCE — the advertised name does
    NOT appear — so the primary rival is the one that smuggles a name term back
    in, and it is refuted at a pair that differs ONLY in the advertised name.

WITNESS MECHANICS. The spec is a ``method`` contract, not a bare predicate, so a
witness reaches the post-image through Velvet's own tester machinery:
``<base>Tester <inputs> = false`` says the extracted program's result violates
the contract at that concrete input. Both methods are precondition-free, so a
tester verdict can never be the short-circuit ``true`` of an out-of-domain
input: ``false`` always means the postcondition is genuinely violated there.
Witnesses are checked in a file whose ``prove_correct`` blocks have been
stripped, so no tactic script can mask the verdict, and every impl in this
battery (frozen and rival alike) is loop-free, so every tester reduces under
``decide``. No banned token (``sorry`` / ``admit`` / ``native_decide`` /
``axiom``), no head binder, hence no consistency obligation to discharge.

ADVERSARIAL READ of the nagini sibling's classes (see 'assessment' in the
submitted payload for what was and was not ported):

  * FRAME / PERMISSION-MUTATION — VACUOUS on this carrier. The nagini sibling
    marks two such probes MANDATORY per function, because both operands are held
    there under HALF, read-only permission, so an impl that WRITES an input must
    be rejected for insufficient permission. This backend has no such lane: it
    is referentially transparent, every input here is an immutable VALUE
    parameter, and neither method declares a ``mut`` binder — there is no
    read-only reference to overwrite and no illegal store to attempt. Not
    fabricated, and no substitute invented.
  * DIVERGENCE / NON-TERMINATION — GENUINELY CLOSED on this bundle, and this is
    a property of the frozen spec, not of the carrier. This bundle sets
    ``loom.semantics.termination "total"``, under which a postcondition is claimed of
    ALL runs, not only terminating ones, and the verifier demands a decreasing
    measure on every loop. The option cannot drift from the file's
    ``open TotalCorrectness DemonicChoice``, because the ``set_option`` elaborator
    itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). (An earlier version of this
    bullet cited an internal findings doc for the claim that 401 of 500 velvet bundles
    set ``"partial"``, under which a non-terminating impl satisfies every ``ensures``
    clause VACUOUSLY and verifies, and called that an open unportable spec hole. That
    cohort no longer exists: all 500 velvet bundles set ``"total"``, so there is no
    such hole to be outside of.) The sharper diverging shape is refused as well: a
    loop CARRYING a measure that does not decrease
    (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``, body
    ``q := q``) is REJECTED on the measure's own goal - ``case «decreasing_1: q»``,
    residual ``⊢ q < q``. Measured here with a real build: splicing
    ``while true do spin := spin + 1`` ahead of the frozen body is REJECTED
    (``error: Decreasing annotations are required in total correctness
    semantics``), so the class is refuted by the spec itself. It is still not
    shipped as a reject case, because on a rejected-by-semantics rival the
    tester does not reduce (measured: ``decide`` gets stuck at
    ``registeredColormapPreDecidable``), so no discriminating witness exists to
    attribute the rejection with — and the manifest contract requires one. Not a
    hole, not vacuous: closed by the spec, unwitnessable by construction.
  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo, on both obligations. (E) is
    pinned to a transparent pure function of the operands and R1..R3 to the
    binders themselves; there is no opaque answer-key to echo, so the positive
    controls are honest reshapes rather than echo probes.
  * PARTIAL-DOMAIN / VALUE-DROP rivals — the whole battery. Each rival is
    CORRECT on a large sub-domain and wrong on the one the clause exists for,
    and each is refuted at the smallest input exposing it.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25479"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl bodies and proof blocks, captured VERBATIM. Each anchor lies
# ENTIRELY inside the region it names (strictly between that region's markers,
# or inside that obligation's tactic body) and is unique in the file, so a
# variant can only ever perturb the elided text. If the frozen solution is ever
# edited, every anchor below breaks LOUDLY at import time.
# ---------------------------------------------------------------------------
_REG_IMPL = (
    "    -- Take the colormap to be stored (a content copy, identity on the modeled\n"
    "    -- fields). When the colormap still advertises a name other than the chosen\n"
    "    -- registration name, update its advertised name to the registration name so\n"
    "    -- the two agree; its end-style and colour lookup table are left untouched.\n"
    "    let mut stored := cmap\n"
    "    if stored.name ≠ name then\n"
    "      stored := { stored with name := name }\n"
    "    return stored"
)

_EQ_IMPL = (
    "    -- The same colormap value iff the end-styles agree and the colour lookup\n"
    "    -- tables agree; the advertised names do not enter the comparison.\n"
    "    return (decide (a.extendStyle = b.extendStyle) && decide (a.lookupTable = b.lookupTable))"
)

_REG_PROOF = "prove_correct registeredColormap by\n  loom_solve"
_EQ_PROOF = ("prove_correct colormapsEqual by\n"
             "  loom_solve\n"
             "  simp_all [colormapEqSpec]")

for _a, _why in ((_REG_IMPL, "store-site impl"), (_EQ_IMPL, "equality-site impl"),
                 (_REG_PROOF, "store-site proof"), (_EQ_PROOF, "equality-site proof")):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift ({_why}): not present exactly once")


def _reg(body, proof=None):
    """Variant with ONLY the store-site impl body (and optionally its proof) changed."""
    out = _swap(_BASE, _REG_IMPL, body.rstrip("\n"))
    return _swap(out, _REG_PROOF, proof) if proof else out


def _eq(body, proof=None):
    """Variant with ONLY the equality-site impl body (and optionally its proof) changed."""
    out = _swap(_BASE, _EQ_IMPL, body.rstrip("\n"))
    return _swap(out, _EQ_PROOF, proof) if proof else out


# ---------------------------------------------------------------------------
# Witness preambles. `<base>Tester <inputs> = false` is the post-image verdict at
# a concrete input; both methods are precondition-free so `false` can only mean
# "the postcondition is violated here". Every witness reduces under `decide`
# (the carrier is fully transparent) and binds nothing, so none of them can be
# a refutation-from-a-contradiction.
# ---------------------------------------------------------------------------
def _w_reg(call):
    return ("extract_program_for registeredColormap\n"
            "prove_precondition_decidable_for registeredColormap\n"
            "prove_postcondition_decidable_for registeredColormap\n"
            "derive_tester_for registeredColormap\n\n"
            f"example : {call} = false := by\n  decide\n")


def _w_eq(call):
    return ("extract_program_for colormapsEqual\n"
            "prove_precondition_decidable_for colormapsEqual\n"
            "prove_postcondition_decidable_for colormapsEqual\n"
            "derive_tester_for colormapsEqual\n\n"
            f"example : {call} = false := by\n  decide\n")


def _cm(name, ext, lut):
    return '{ name := "%s", extendStyle := %s, lookupTable := %s }' % (name, ext, lut)


# The admissibility probe's in-region claim: an F2P-shaped colormap pair. Live —
# flipping any conjunct to a false claim leaves an unsolved goal (measured while
# authoring: `⊢ False`), so this is not a no-op assert.
_ADM_A = _cm("advertised", "true", "[[1, 2], [3, 4]]")
_ADM_B = _cm("chosen", "true", "[[1, 2], [3, 4]]")
_ADM_B_FLIPPED = _cm("chosen", "false", "[[1, 2], [3, 4]]")
_ADM_B_SHORT = _cm("chosen", "true", "[[1, 2]]")

_ADM_ASSERT = (
    "    -- Admissibility probe: a normal, F2P-shaped input pair is IN-DOMAIN and the\n"
    "    -- post-image is NON-DEGENERATE there — a renamed content-identical duplicate\n"
    "    -- compares equal, while an end-style flip and a shortened lookup table each\n"
    "    -- compare unequal. If the contract could not be established for such a pair,\n"
    "    -- or if it collapsed to a constant verdict, this claim would not discharge.\n"
    "    assert (with_name_prefix `adm\n"
    f"      (colormapEqSpec {_ADM_A}\n"
    f"           {_ADM_B} = true\n"
    f"       ∧ colormapEqSpec {_ADM_B}\n"
    f"           {_ADM_B_FLIPPED} = false\n"
    f"       ∧ colormapEqSpec {_ADM_B}\n"
    f"           {_ADM_B_SHORT} = false))\n"
)


SPEC_TESTS = [

    # ===================================================================
    # SOUNDNESS positives — structurally different CORRECT impls that MUST
    # verify, else the contract rejects its own faithful reshapes
    # (SPEC-TOO-STRONG). Both were confirmed with real builds while authoring.
    # ===================================================================

    # Ported from the nagini sibling's positive control B ("fold the relabel into
    # construction"). Instead of copying the colormap and then conditionally
    # updating its advertised name, build the stored value directly under the
    # chosen registration name, carrying the other two fields across. No
    # conditional at all — a genuinely different control-flow shape — and the
    # frozen tactic script still closes the byte-identical obligation.
    {
        "id": "pos-reg-construct-under-name",
        "kind": "soundness",
        "expect": "verify",
        "module": _reg(
            "    -- Build the stored colormap directly under the chosen registration\n"
            "    -- name, carrying the end-style and colour lookup table across, rather\n"
            "    -- than copying first and updating the advertised name afterwards.\n"
            "    let stored : Colormap :=\n"
            "      { name := name, extendStyle := cmap.extendStyle, lookupTable := cmap.lookupTable }\n"
            "    return stored"),
        "rationale": "a CORRECT impl with a different shape — the conditional update "
                     "is folded into construction, so there is no branch at all — must "
                     "verify. It satisfies R1 unconditionally (the stored name IS the "
                     "`name` binder) and R2/R3 by carrying the two other fields, on the "
                     "whole domain including the `cmap.name = name` sub-domain where the "
                     "frozen impl's guard does not fire. If this cannot verify, "
                     "R1..R3 are SPEC-TOO-STRONG: they would reject a reshape "
                     "observationally identical to the frozen one.",
    },

    # Ported from the nagini sibling's positive control A ("hoist the
    # extension-flag comparison into a local bool and branch on it"). Same
    # reshape, expressed over this carrier: bind the end-style comparison to a
    # local and branch, deciding the lookup table only on the matching arm. The
    # proof is retuned (the tactic body is elided from the spec view) because the
    # reshape splits the goal into two branch cases; the OBLIGATION statement is
    # untouched and both cases are discharged on the merits, not weakened.
    {
        "id": "pos-eq-branch-on-extend",
        "kind": "soundness",
        "expect": "verify",
        "module": _eq(
            "    -- Bind the end-style comparison to a local and branch on it: decide the\n"
            "    -- colour lookup table only when the end-styles already agree, and report\n"
            "    -- unequal otherwise. The advertised names still do not enter.\n"
            "    let extOk := decide (a.extendStyle = b.extendStyle)\n"
            "    if extOk then\n"
            "      return decide (a.lookupTable = b.lookupTable)\n"
            "    else\n"
            "      return false",
            "prove_correct colormapsEqual by\n"
            "  loom_solve\n"
            "  all_goals simp_all [colormapEqSpec]"),
        "rationale": "a CORRECT impl with a different executable shape — one conjunct "
                     "hoisted into a local and short-circuited through a branch instead "
                     "of a single boolean expression — must verify. Both arms agree with "
                     "(E) on the whole domain (the `false` arm is exactly where the "
                     "end-style conjunct of `colormapEqSpec` is false), so if this "
                     "cannot verify, (E) is SPEC-TOO-STRONG: it would pin the "
                     "SYNTACTIC form of the verdict rather than the verdict.",
    },

    # ===================================================================
    # ADMISSIBILITY — the nagini sibling's `admiss-eq-self-call` re-expressed.
    # There, the probe had to show the call site could ESTABLISH the callee's
    # permission-bearing precondition for a freshly built pair. Here both methods
    # are precondition-free, so that half is vacuous and the residual
    # admissibility risk is different: that the contract, though satisfiable, is
    # DEGENERATE at the shape the failing tests use. One in-region claim pins
    # both halves at an F2P-shaped pair: the verdict is `true` for a renamed
    # content-identical duplicate (so the contract does not forbid the very
    # behavior under test) and `false` for both an end-style flip and a
    # shortened lookup table (so it has not collapsed to a constant). The impl
    # is kept VERBATIM so the method's own obligation still discharges on its
    # own merits; only the tactic body is extended to clear the extra goal.
    # ===================================================================
    {
        "id": "admiss-eq-f2p-shaped-pair",
        "kind": "admissibility",
        "expect": "verify",
        "module": _eq(
            _ADM_ASSERT + _EQ_IMPL,
            "prove_correct colormapsEqual by\n"
            "  loom_solve\n"
            "  all_goals first | decide | simp_all [colormapEqSpec]"),
        "rationale": "the contract admits a normal, F2P-shaped input and is "
                     "NON-DEGENERATE there. (E) evaluates to `true` on a pair that "
                     "differs only in the advertised name — the exact situation the "
                     "failing tests exercise, so the contract does not rule it out — "
                     "and to `false` on both an end-style flip and a shortened lookup "
                     "table, so it is not a constant collapse. Were the claim "
                     "unsatisfiable it would be PRECOND-TOO-STRONG; were it a "
                     "tautology the surface would be untested. The impl is verbatim, so "
                     "(E) itself still discharges. The claim is LIVE: flipping any "
                     "conjunct leaves an unsolved goal.",
    },

    # ===================================================================
    # UNIQUENESS rivals — wrong impls sharing the FROZEN spec that MUST be
    # rejected. Each carries a witness AUTHOR-VERIFIED with two real builds to
    # ELABORATE against the rival and FAIL against the frozen solution, so the
    # rejection is attributed to the contract and not to the frozen tactic
    # script breaking on a reshaped body (which is the default outcome of ANY
    # reshape and therefore no evidence at all).
    # ===================================================================

    # ---- OBLIGATION 1, clause R1: the replacement clause ----------------

    # Ported from nagini `weak-reg-drop-relabel`. THE behavioural delta: store
    # the colormap as it stands, so the stored colormap keeps whatever name it
    # already advertised instead of adopting the chosen registration name.
    {
        "id": "weak-reg-keep-advertised-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    -- WRONG: store the colormap exactly as it stands, so it keeps whatever\n"
            "    -- name it already advertised instead of adopting the chosen one.\n"
            "    let stored := cmap\n"
            "    return stored"),
        "refinement": "this is the behaviour BEFORE the change: whatever is stored keeps "
                      "its own advertised name, so a later lookup that consults the "
                      "stored colormap's own advertised name disagrees with the name the "
                      "colormap is reachable by — precisely the confusion the public "
                      "issue reports. A faithful counterpart is refuted by the failing "
                      "test that stores a colormap advertising one name under a "
                      "DIFFERENT chosen name and then asserts the looked-up colormap "
                      "advertises the chosen name: it would still advertise the old one. "
                      "Does NOT resolve.",
        "rationale": "REJECT from R1 (`out.name = name`): the rival's result advertises "
                      "`cmap.name`, which is not provably equal to `name` — they are "
                      "independent binders. CORRECT on the whole `cmap.name = name` "
                      "sub-domain, so a true partial-domain attack on exactly the "
                      "sub-domain R1 exists for. Verifying would be SPEC-TOO-WEAK on "
                      "the load-bearing clause. Refuted at cmap advertising \"own\" "
                      "stored under \"chosen\" (end-style true, one two-column row): "
                      "R1 demands \"chosen\", the rival yields \"own\".",
        "witness": _w_reg(f'registeredColormapTester {_cm("own", "true", "[[4, 5]]")} "chosen"'),
    },

    # NEAR-MISS on R1 with no nagini counterpart — added because the rival above
    # deletes the update outright, which leaves untested whether R1 pins the
    # update's GUARD. This one keeps the update but narrows its condition to
    # "only when the colormap advertises no name at all", so it agrees with the
    # frozen impl on strictly more of the domain (every unnamed colormap, plus
    # every already-correctly-named one) and diverges only where a colormap
    # advertises some OTHER name — which is the whole point of the clause.
    {
        "id": "weak-reg-relabel-only-unnamed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    -- WRONG: adopt the chosen registration name only when the colormap\n"
            "    -- advertises no name at all, leaving any other advertised name in place.\n"
            "    let mut stored := cmap\n"
            "    if stored.name = \"\" then\n"
            "      stored := { stored with name := name }\n"
            "    return stored"),
        "refinement": "a counterpart that only filled in a MISSING advertised name would "
                      "look right on freshly built colormaps and on any colormap already "
                      "advertising the chosen name, but it leaves the reported case "
                      "untouched: the colormap in the issue advertises a perfectly good "
                      "name that merely differs from the one it is being stored under, so "
                      "the guard never fires and the stored colormap still advertises the "
                      "wrong name. The failing test uses exactly that shape. Does NOT "
                      "resolve.",
        "rationale": "REJECT from R1: on any colormap advertising a NON-EMPTY name other "
                      "than `name`, the guard does not fire and `out.name` is `cmap.name` "
                      "≠ `name`. A strictly nearer miss than "
                      "`weak-reg-keep-advertised-name` — it agrees with the frozen impl "
                      "wherever the advertised name is empty — so it gets its own witness "
                      "at the input that separates them: cmap advertising \"own\" "
                      "(non-empty) stored under \"other\", end-style FALSE and a "
                      "one-column row. The advertised name is deliberately held at "
                      "\"own\" — the same value the previous witness uses — because that "
                      "is what makes the point DISCRIMINATING for this rival (an empty "
                      "advertised name is exactly where it agrees with the frozen impl); "
                      "the `extendStyle` and `lookupTable` sub-fields and the `name` "
                      "binder all move away from the previous point.",
        "witness": _w_reg(f'registeredColormapTester {_cm("own", "false", "[[2]]")} "other"'),
    },

    # ---- OBLIGATION 1, clause R2: preservation of the end-style ---------

    # Ported from nagini `weak-reg-drop-extend`. The stored colormap is built
    # with a hardwired end-style instead of carrying the supplied one across,
    # while the name is adopted correctly — so R1 and R3 still hold and only R2
    # is attacked.
    {
        "id": "weak-reg-drop-extend",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    -- WRONG: the stored colormap is built with a hardwired end-style rather\n"
            "    -- than the supplied colormap's, though the chosen name is adopted\n"
            "    -- correctly and the colour lookup table is carried across.\n"
            "    let stored := { cmap with name := name, extendStyle := false }\n"
            "    return stored"),
        "refinement": "storing is content-preserving in the real behaviour, so a "
                      "counterpart that reset the end-style would silently drop the "
                      "special treatment of a colormap's out-of-range ends across "
                      "storage. The failing test stores a colormap whose ends HAVE been "
                      "given special treatment and then asserts the looked-up colormap "
                      "still compares equal to the original — and equality turns on the "
                      "end-style, so a reset end-style makes them unequal. Does NOT "
                      "resolve.",
        "rationale": "REJECT from R2 (`out.extendStyle = cmap.extendStyle`): the rival "
                      "pins the field to a constant, which is not provably equal to the "
                      "binder's field. CORRECT on the whole sub-domain where the supplied "
                      "end-style already matches that constant — a genuine value-drop "
                      "attack, not a blanket wrong impl. Refuted at cmap advertising "
                      "\"styled\" with end-style TRUE stored under \"renamed\" (so the "
                      "name update also fires, and R1/R3 are satisfied — the rejection "
                      "isolates R2).",
        "witness": _w_reg(f'registeredColormapTester {_cm("styled", "true", "[[6, 7, 8]]")} "renamed"'),
    },

    # NEAR-MISS on R2 with no nagini counterpart. Added by the audit: R2 was the
    # only top-level clause defended solely by a BLANKET rival (the hardwired
    # end-style above), while R1, R3 and (E) each carry a near-miss too. This one
    # keeps the end-style everywhere the frozen impl's relabel guard does NOT
    # fire and drops it only on the sub-domain where it does, i.e. it makes the
    # PRESERVATION clause R2 conditional on the REPLACEMENT clause R1's guard —
    # so it is correct on the whole `cmap.name = name` sub-domain, and wrong
    # exactly where the two clauses have to hold simultaneously.
    {
        "id": "weak-reg-drop-extend-only-when-relabelling",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    -- WRONG: the end-style is carried across only when the colormap already\n"
            "    -- advertises the chosen registration name; when the name has to be\n"
            "    -- adopted, the end-style is reset instead of preserved.\n"
            "    if cmap.name = name then\n"
            "      return cmap\n"
            "    else\n"
            "      return { cmap with name := name, extendStyle := false }"),
        "refinement": "storing is content-preserving REGARDLESS of whether the stored "
                      "colormap had to adopt a new advertised name — the two behaviours "
                      "are independent. A counterpart that reset the end-style on exactly "
                      "the storing paths that rename would look correct on every "
                      "already-correctly-named colormap and still drop the special "
                      "treatment of the out-of-range ends in the reported case, which is "
                      "the case where the chosen name differs. The failing test uses that "
                      "shape and then asserts the looked-up colormap still compares equal "
                      "to the original; equality turns on the end-style, so a reset "
                      "end-style makes them unequal. Does NOT resolve.",
        "rationale": "REJECT from R2 (`out.extendStyle = cmap.extendStyle`) on the "
                      "sub-domain `cmap.name ≠ name`. A strictly nearer miss than "
                      "`weak-reg-drop-extend`, which resets the end-style on the WHOLE "
                      "domain: this one is correct wherever the advertised name already "
                      "equals the chosen one, so it demonstrates that R2 is not merely a "
                      "clause about the no-rename path — R2 and R1 must hold together. "
                      "Measured while auditing: the residual goal is exactly "
                      "`false = cmap.extendStyle` under `¬cmap.name = name`, so the "
                      "rejection is attributable to R2 and to no other clause. Refuted at "
                      "cmap advertising \"orig\" with end-style TRUE and one two-column "
                      "row, stored under \"stored\": gold yields end-style true, the rival "
                      "false.",
        "witness": _w_reg(f'registeredColormapTester {_cm("orig", "true", "[[5, 6]]")} "stored"'),
    },

    # ---- OBLIGATION 1, clause R3: preservation of the lookup table ------

    # No nagini counterpart in the reject lane (the sibling's R5 goes unattacked
    # there). Added because R3 is an independent top-level clause and would
    # otherwise be defended by positives alone: a rival that discarded the
    # colour lookup table entirely while getting the name and end-style right
    # would go unnoticed.
    {
        "id": "weak-reg-drop-lookup-table",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    -- WRONG: the stored colormap is built with an empty colour lookup table\n"
            "    -- rather than the supplied one, though the chosen name is adopted and\n"
            "    -- the end-style carried across.\n"
            "    let stored := { cmap with name := name, lookupTable := [] }\n"
            "    return stored"),
        "refinement": "a counterpart that dropped the colour lookup table on storage "
                      "would leave the stored colormap unable to resolve any value at "
                      "all, so every later use of the stored colormap renders wrongly. "
                      "It also breaks the failing test's assertion that the looked-up "
                      "colormap compares equal to the original, since equality turns on "
                      "the lookup table. Does NOT resolve.",
        "rationale": "REJECT from R3 (`out.lookupTable = cmap.lookupTable`): the rival "
                      "returns a constant empty table, not provably equal to the "
                      "binder's. CORRECT only where the supplied table is already empty "
                      "— the degenerate edge — so this pins that R3 is a PRESERVATION "
                      "clause and not merely a well-formedness one. Refuted at cmap "
                      "advertising \"k\" with a single one-column row stored under "
                      "\"k2\" (end-style false; a fourth distinct `cmap`/`name` point).",
        "witness": _w_reg(f'registeredColormapTester {_cm("k", "false", "[[9]]")} "k2"'),
    },

    # NEAR-MISS on R3 with no nagini counterpart. The rival above empties the
    # table, which any length check would catch; this one PRESERVES every row and
    # the row count and gets only the ORDER wrong. It agrees with the frozen impl
    # on every palindromic table (including every table of fewer than two rows),
    # so it demonstrates that R3 pins the table as an ORDERED sequence.
    {
        "id": "weak-reg-reorder-lookup-table",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _reg(
            "    -- WRONG: the stored colormap carries the same lookup-table rows but in\n"
            "    -- reversed order, though the chosen name is adopted and the end-style\n"
            "    -- carried across.\n"
            "    let stored := { cmap with name := name, lookupTable := cmap.lookupTable.reverse }\n"
            "    return stored"),
        "refinement": "reversing the colour lookup table's rows preserves its size and "
                      "its multiset of rows but inverts which sample resolves to which "
                      "colour, so the stored colormap renders every value inverted. It "
                      "also fails the equality the failing test asserts between the "
                      "looked-up colormap and the original. Does NOT resolve.",
        "rationale": "REJECT from R3 via the ORDER sub-behaviour: `out.lookupTable` must "
                      "be `cmap.lookupTable` itself, and the reversal differs on any "
                      "non-palindromic table. A strictly nearer miss than "
                      "`weak-reg-drop-lookup-table` (it preserves length and content, so "
                      "any size-only reading of R3 would let it through), hence its own "
                      "witness at the smallest table exposing order: two distinct rows, "
                      "stored under a name EQUAL to the advertised one — the only "
                      "witness in this battery where R1's guard does NOT fire, so the "
                      "`name` binder is exercised on both sides of that branch.",
        "witness": _w_reg(f'registeredColormapTester {_cm("two", "false", "[[1, 0], [0, 1]]")} "two"'),
    },

    # ---- OBLIGATION 2, clause (E) ---------------------------------------

    # Ported from nagini `weak-eq-label-reintroduced`. THE behavioural delta on
    # this obligation, and the one the discriminating change is an ABSENCE of:
    # require the two advertised names to agree as well.
    {
        "id": "weak-eq-name-conjunct-reintroduced",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    -- WRONG: the verdict additionally requires the two advertised names to\n"
            "    -- agree, so a colormap and a renamed duplicate of it are reported as\n"
            "    -- different values.\n"
            "    return (decide (a.name = b.name) && decide (a.extendStyle = b.extendStyle)\n"
            "            && decide (a.lookupTable = b.lookupTable))"),
        "refinement": "this is the behaviour BEFORE the change: the advertised name "
                      "participates in the verdict. A faithful counterpart is refuted "
                      "directly by the failing test that takes a duplicate of a "
                      "colormap, gives the duplicate a different advertised name, and "
                      "asserts the two still compare EQUAL — with a name term present "
                      "they compare unequal. It also breaks the second failing test, "
                      "which asserts the looked-up stored colormap compares equal to the "
                      "original even though storing has renamed it. Does NOT resolve.",
        "rationale": "REJECT from (E): `colormapEqSpec` deliberately OMITS any term over "
                      "the advertised name, so on a pair differing only in that name the "
                      "rival returns `false` where (E) demands `true`. CORRECT on every "
                      "pair whose names already agree — the common case — so a true "
                      "partial-domain attack on exactly the sub-domain the clause's "
                      "absence creates. Refuted at two colormaps with the SAME end-style "
                      "and the SAME two-column row, advertising \"A\" and \"B\": the only "
                      "witness here that moves `a.name` against `b.name`.",
        "witness": _w_eq("colormapsEqualTester\n"
                         f"    {_cm('A', 'false', '[[1, 2]]')}\n"
                         f"    {_cm('B', 'false', '[[1, 2]]')}"),
    },

    # Ported from nagini `weak-eq-ignore-extend`. Decide on the colour lookup
    # table alone, dropping the end-style conjunct — the conjunct the change
    # KEEPS, so this checks that removing the name term did not license removing
    # its neighbour.
    {
        "id": "weak-eq-ignore-extend",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    -- WRONG: the verdict is decided on the colour lookup table alone; the\n"
            "    -- end-style is not consulted.\n"
            "    return (decide (a.lookupTable = b.lookupTable))"),
        "refinement": "the end-style genuinely participates in the real verdict. A "
                      "counterpart that ignored it would report two colormaps equal even "
                      "when they treat their out-of-range ends differently; the failing "
                      "test takes a duplicate, flips its end-style, and asserts the two "
                      "compare UNEQUAL. Does NOT resolve.",
        "rationale": "REJECT from (E)'s end-style conjunct: with equal lookup tables and "
                      "DIFFERING end-styles the rival returns `true` where "
                      "`colormapEqSpec` is `false`. CORRECT on every pair whose "
                      "end-styles already agree — which is every other witness point in "
                      "this battery — so this is the only rival that moves the "
                      "`extendStyle` sub-field of `a` against that of `b`, and the "
                      "binder would otherwise be held equal by every reject case. "
                      "Refuted at a same-named pair with one one-column row and "
                      "end-styles true vs false.",
        "witness": _w_eq("colormapsEqualTester\n"
                         f"    {_cm('v', 'true', '[[3]]')}\n"
                         f"    {_cm('v', 'false', '[[3]]')}"),
    },

    # Ported from nagini `weak-eq-truncate-tail` (the off-by-one tail probe),
    # re-expressed over this carrier: the lookup tables are compared row-count
    # plus all-rows-but-the-last, so the final row is never consulted. Keeps the
    # size comparison the sibling's length guard supplied, so it is correct
    # whenever the tables agree on their last row.
    {
        "id": "weak-eq-skip-last-lut-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    -- WRONG: the colour lookup tables are compared on their row count and on\n"
            "    -- every row but the last, so the final row is never consulted.\n"
            "    return (decide (a.extendStyle = b.extendStyle)\n"
            "            && decide (a.lookupTable.dropLast = b.lookupTable.dropLast)\n"
            "            && decide (a.lookupTable.length = b.lookupTable.length))"),
        "refinement": "the real verdict compares the WHOLE lookup table. A counterpart "
                      "that skipped its last row would report two colormaps equal when "
                      "they differ only in the row that resolves one end of the sampled "
                      "range — exactly the row a caller edits when giving a colormap's "
                      "out-of-range ends special treatment, which is what the failing "
                      "tests set up before comparing. Does NOT resolve.",
        "rationale": "REJECT from (E)'s lookup-table conjunct: (E) demands full table "
                      "equality, and the rival's weaker test passes on tables agreeing "
                      "everywhere except the last row, returning `true` where "
                      "`colormapEqSpec` is `false`. CORRECT on all differing-size pairs "
                      "(the count is still compared) and on every pair agreeing on its "
                      "last row, so a genuine off-by-one partial-domain attack. Refuted "
                      "at a same-named, same-end-style pair of TWO-row tables agreeing on "
                      "the first row and differing on the second.",
        "witness": _w_eq("colormapsEqualTester\n"
                         f"    {_cm('q', 'false', '[[0], [7]]')}\n"
                         f"    {_cm('q', 'false', '[[0], [8]]')}"),
    },

    # NEAR-MISS on (E) with no nagini counterpart. Compare each operand's lookup
    # table against the OTHER's reversed — length-preserving, content-preserving
    # as a multiset, and equal to the frozen verdict on every palindromic table
    # (so on every table of fewer than two rows). Distinct from
    # `weak-eq-skip-last-lut-row`: that rival is blind to the last row's CONTENT
    # while this one is blind to row ORDER, and neither subsumes the other.
    {
        "id": "weak-eq-lut-order-blind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _eq(
            "    -- WRONG: one operand's colour lookup table is compared against the\n"
            "    -- other's rows in reversed order, so row order does not affect the\n"
            "    -- verdict on a table that is its own reverse.\n"
            "    return (decide (a.extendStyle = b.extendStyle)\n"
            "            && decide (a.lookupTable = b.lookupTable.reverse))"),
        "refinement": "a counterpart blind to lookup-table row ORDER would report a "
                      "colormap and its colour-reversed counterpart as the same value, "
                      "so a caller could not distinguish a colormap from its reverse — "
                      "and the failing tests compare colormaps built by editing "
                      "particular rows of the table, where order is exactly what "
                      "distinguishes them. Does NOT resolve.",
        "rationale": "REJECT from (E)'s lookup-table conjunct via the ORDER "
                      "sub-behaviour: (E) compares the tables as ORDERED sequences, and "
                      "the rival compares one against the other reversed, so the two "
                      "verdicts differ on any pair whose tables are reverses of each "
                      "other without being equal. CORRECT on every palindromic table, "
                      "hence on every single-row table — a nearer miss than the "
                      "skip-last-row rival, which is why it carries its own witness. "
                      "Refuted at a same-named, same-end-style pair of two-row tables "
                      "that are each other's reverse: the rival says `true`, "
                      "`colormapEqSpec` says `false`.",
        "witness": _w_eq("colormapsEqualTester\n"
                         f"    {_cm('p', 'true', '[[1], [2]]')}\n"
                         f"    {_cm('p', 'true', '[[2], [1]]')}"),
    },
]
