"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9461 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` header survives) and swaps in a candidate implementation.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE — one contracted method, two Bool binders, three independent
top-level post-image clauses:

  assembleModifierTokens (firstFlag secondFlag : Bool) return (out : List String)
    (E1) out ≠ [] ∧ out.getLast! = "property"        -- the trailing token
    (E2) secondFlag = true → "class" ∈ out           -- the second flag's token
    (E3) out = annotationTokens firstFlag secondFlag -- the exact ordered list

There is NO ``require`` clause: the admitted domain is the whole two-element
boolean cube, so every rival below is refutable at a concrete literal input.

CARRIER — FULLY TRANSPARENT, FULLY DECIDABLE. ``annotationTokens`` is a
spelled-out ``if/then/else ++`` computation over the two binders in the ``pure``
region; the ``axioms`` region declares neither an ``axiom`` nor an ``opaque``
leaf. So there is no answer-key oracle a wrong impl could ECHO (SPEC_GUIDE
directive 8 is discharged by construction, and the ungrounded-echo rival class
is N/A — see the accounting note), and no opaque term to condition a witness on:
every reject witness below states its refutation at a fully concrete input and
closes by ``decide``. The whole input domain is FOUR points, and the battery's
five witnesses probe all four.

ADVERSARIAL READ of the sibling's classes:
  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the bulk of the battery: a rival
    right on part of the boolean cube and diverging on the rest.
  * TOKEN-ORDER — APPLIES: E3 is an exact ordered-list equality, so a rival can
    assemble the right multiset of tokens in the wrong order.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because
    an input may carry a fractional heap permission an impl can overwrite. This
    backend is referentially transparent, has no heap and no aliasing, and this
    bundle declares no ``mut`` binder at all — there is no read-only input to
    overwrite and no substitute probe to fabricate.
  * CAPABILITY / CONTROL-FLOW-EFFECT — VACUOUS on this carrier. The sibling
    gates its emission behind unforgeable body-less capability predicates, which
    are a heap-resource construct; this bundle models a pure value assembly with
    no gated effect and no capability to forge. See the accounting note.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``let`` / ``if`` over immutable values, no loop
    and no recursion), so there is no control flow here to make diverge: a
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

WITNESS PLACEMENT. The five reject witnesses sit at all FOUR points of the
input domain — (F,F), (T,F), (F,T), (T,T) — so both binders take both values and
neither is held fixed by the battery. Each of the three independent post-image
clauses is attacked: E1 by ``weak-trailing-token-first``, E2 by
``weak-drops-second-token``, E3 by all five. One point is shared by two rivals
(``weak-swapped-token-order`` and ``weak-trailing-token-first``, both at (T,T));
that is forced by pigeonhole (five rivals, a four-point domain) and is honest
there because at (T,T) both rivals emit exactly the correct token MULTISET in a
wrong ORDER — the same failure mode — and the near-miss of the pair
(``weak-swapped-token-order``, correct on three of the four points) has (T,T) as
its ONLY point of divergence, so its rationale claims no sub-domain the manifest
does not demonstrate. The broader rival additionally violates E1 there, which
its partner does not, so the shared point still separates what each one is
accused of.

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

AXIOM lane: ``AXIOM_TESTS`` dropped. The bundle consumes no ``axiom`` and
declares no deep-model reference (``meta.json``: ``axioms: []``,
``deep_model_references: []``, G-AX ``status=skip``, reason ``no-axioms``), so
there is nothing for an axiom probe to attack — and the axiom lane is G-AX's
job, which this gate ignores regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9461"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Both lie ENTIRELY inside a region the consumer spec view elides (the
# impl `do` block; the `prove_correct` tactic body) and both are unique in the
# file — asserted at load by `_swap`, so the manifest breaks loudly if the
# frozen solution ever drifts.
# ---------------------------------------------------------------------------
_IMPL_GOLD = (
    '    let mut toks : List String := []\n'
    '    if firstFlag then\n'
    '      toks := toks ++ ["abstract"]\n'
    '    if secondFlag then\n'
    '      toks := toks ++ ["class"]\n'
    '    toks := toks ++ ["property"]\n'
    '    return toks'
)
if _BASE.count(_IMPL_GOLD) != 1:
    raise AssertionError("impl anchor drift: assembleModifierTokens body")

_PROOF_GOLD = "prove_correct assembleModifierTokens by\n  loom_solve"
if _BASE.count(_PROOF_GOLD) != 1:
    raise AssertionError("proof anchor drift")


def _impl(body):
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Witness preamble. The spec here is a `method` CONTRACT, not a bare predicate,
# so a witness reaches the post-image through Velvet's own tester machinery:
# `assembleModifierTokensTester a b = false` says the extracted program's result
# VIOLATES the method's postcondition at that concrete input. Checked in a file
# whose `prove_correct` block has been stripped, so the frozen tactic script
# cannot mask the verdict. Every argument is a Bool literal, so `decide` reduces
# with no opaque term in the way and no hypothesis to be inconsistent about.
# ---------------------------------------------------------------------------
_TESTER = (
    "extract_program_for assembleModifierTokens\n"
    "prove_precondition_decidable_for assembleModifierTokens\n"
    "prove_postcondition_decidable_for assembleModifierTokens\n"
    "derive_tester_for assembleModifierTokens\n\n"
)


def _witness(args):
    return (_TESTER
            + f"example : assembleModifierTokensTester {args} = false := by\n"
            + "  decide\n")


SPEC_TESTS = [

    # =====================================================================
    # SOUNDNESS / POSITIVE CONTROLS — structurally DIFFERENT but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Proofs are discharged by the frozen
    # `loom_solve` (kept verbatim); no case here needs proof authoring, so
    # none is dropped for an unclosable proof.
    # =====================================================================

    # Sibling counterpart: pos-prefix-reshape (the typed-intermediate-locals
    # reshape of the token assembly). Here the accumulator loop is replaced by
    # ONE pure `let` binding the whole assembly expression — same tokens, same
    # order, no mutable local at all.
    {
        "id": "pos-pure-assembly",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            '    let toks : List String :=\n'
            '      (if firstFlag then ["abstract"] else []) ++\n'
            '      (if secondFlag then ["class"] else []) ++ ["property"]\n'
            '    return toks'),
        "rationale": "a correct but structurally different assembly — one pure "
                     "`let` in place of the mutable accumulator, same tokens in "
                     "the same order — must satisfy E1, E2 and E3 pointwise on "
                     "all four inputs; else SPEC-TOO-STRONG on the choice of "
                     "accumulator shape.",
    },

    # Sibling counterpart: pos-disc-branch-reorder (a different control flow
    # reaching the same value). Here the assembly runs BACKWARD: seed with the
    # trailing token and PREPEND each optional token in reverse order, so the
    # branch order in the source is the mirror of the frozen one while the
    # produced list is identical.
    {
        "id": "pos-reverse-prepend",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            '    let mut toks : List String := ["property"]\n'
            '    if secondFlag then\n'
            '      toks := ["class"] ++ toks\n'
            '    if firstFlag then\n'
            '      toks := ["abstract"] ++ toks\n'
            '    return toks'),
        "rationale": "reversed control flow (seed the trailing token, prepend the "
                     "optional tokens in mirror order) yields the identical list, "
                     "so E1/E2/E3 all still hold; a correct reshape whose BRANCH "
                     "ORDER differs from the frozen one must verify, else "
                     "SPEC-TOO-STRONG on branch order rather than on behaviour.",
    },

    # AUDIT NOTE (measured, no case shipped). A fourth correct reshape —
    # assemble the list in the opposite order and `return toks.reverse` — is
    # NOT shipped, and the reason is a tactic gap rather than a spec one. The
    # frozen `loom_solve` leaves E1's four goals open in the form
    # `(["property"] ++ ["class"] ++ ["abstract"]).reverse.getLast! = "property"`:
    # every one is TRUE, `loom_solve` simply does not push `.reverse` through
    # `getLast!`. Appending `all_goals decide` to the tactic body verifies it
    # (exit 0). So the spec is not too strong on list orientation; a positive
    # here would only be testing the tactic script, which the three positives
    # above already discharge without extra tactics.
    # A third correct shape with no branching over an accumulator at all: a
    # fully enumerated nested case split naming each of the four outputs as a
    # literal list. This is the shape most distant from the frozen impl that is
    # still correct, so it is the strongest available SPEC-TOO-STRONG control:
    # if E3 were secretly pinned to the accumulator's syntactic form rather than
    # to the assembled value, this is the case that would expose it.
    {
        "id": "pos-enumerated-cases",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            '    let toks : List String :=\n'
            '      if firstFlag then\n'
            '        (if secondFlag then ["abstract", "class", "property"]\n'
            '         else ["abstract", "property"])\n'
            '      else\n'
            '        (if secondFlag then ["class", "property"] else ["property"])\n'
            '    return toks'),
        "rationale": "the four outputs written out as literal lists is correct on "
                     "every input and shares no syntactic structure with the "
                     "frozen accumulator; it must verify, else E3 is pinned to the "
                     "impl's SHAPE rather than to the assembled value "
                     "(SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's two admissibility cases both establish that
    # a capability PRECONDITION admits a normal in-domain member. This method
    # has NO `require` clause, so nothing could exclude any input and that probe
    # is vacuous here. Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is DEGENERATE at the interesting point — a
    # spec that cannot distinguish the inputs it is supposed to distinguish
    # reads like a spec every impl satisfies. This case discharges an in-region
    # `assert`, at concrete inputs, that the post-image genuinely SEPARATES both
    # binders: flipping either flag on its own changes the demanded output. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; only the tactic body is retuned to clear the extra goal
    # (allowed — it is elided from the spec view). The assert is LIVE, not
    # decoration: replacing it with the false claim that the second flag does
    # NOT change the output leaves `⊢ False` unsolved at `admiss_1`.
    # =====================================================================
    {
        "id": "admiss-both-binders-separate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_GOLD,
                '    assert (with_name_prefix `admiss\n'
                '      (annotationTokens false true ≠ annotationTokens false false ∧\n'
                '       annotationTokens true false ≠ annotationTokens false false))\n'
                + _IMPL_GOLD),
            _PROOF_GOLD,
            "prove_correct assembleModifierTokens by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp_all [annotationTokens]"),
        "rationale": "the post-image is satisfiable AND non-degenerate in BOTH "
                     "binders at concrete inputs: setting the second flag alone "
                     "changes the demanded output, and so does setting the first "
                     "flag alone. If either implication failed the corresponding "
                     "binder would be inert in the spec and a rival mishandling "
                     "only that input could never be refuted. The in-region "
                     "assert must discharge (else the obligation is degenerate) "
                     "and the frozen impl is kept so the ensures clauses "
                     "discharge too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries a machine-checked refutation witness
    # at a concrete input of the four-point domain (verified by hand: the
    # witness elaborates against the rival and FAILS against the frozen
    # solution), plus the refinement argument that its faithful real counterpart
    # would NOT resolve the failing tests.
    # =====================================================================

    # Sibling counterpart: weak-prefix-no-class (the pre-patch assembly). The
    # second flag contributes nothing, so the assembled list never carries its
    # token. Correct whenever the second flag is unset; wrong whenever it is
    # set. This is the ONLY rival that violates E2, and it is the one that moves
    # the second binder to `true` while holding the first at `false`.
    {
        "id": "weak-drops-second-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            '    let mut toks : List String := []\n'
            '    if firstFlag then\n'
            '      toks := toks ++ ["abstract"]\n'
            '    toks := toks ++ ["property"]\n'
            '    return toks'),
        "refinement": "this is the pre-patch behaviour: the second flag has no "
                      "branch and so contributes no token. An entity carrying "
                      "that flag is then annotated as though it did not, and "
                      "tests/test_domain_py.py::test_pyproperty asserts the "
                      "annotation for such an entity reads exactly `class "
                      "property ` (and the companion autodoc tests assert the "
                      "corresponding option line is emitted). With the token "
                      "silently dropped the assertion compares `property ` "
                      "against `class property ` and the F2P FAILS — the "
                      "faithful real counterpart does NOT resolve.",
        "rationale": "REJECT from E2 (`secondFlag = true → \"class\" ∈ out`) and "
                     "from E3: on `secondFlag = true` the assembled list omits "
                     "the second flag's token entirely, so it is not a member and "
                     "the list differs from `annotationTokens firstFlag true`. "
                     "Recorded rejection cites exactly ensures_2 and ensures_3. "
                     "Refuted at (firstFlag=false, secondFlag=true) — the point "
                     "that isolates the second binder's contribution with the "
                     "first binder held off.",
        "witness": _witness("false true"),
    },

    # Sibling counterpart: weak-prefix-swap-order. The two optional tokens are
    # contributed in the OPPOSITE order. The multiset of tokens is always
    # correct and E1 and E2 both still hold; only the ORDER is wrong, and only
    # when BOTH flags are set. The narrowest rival in the battery (correct on
    # three of the four inputs), which is why its witness must sit at its sole
    # point of divergence.
    {
        "id": "weak-swapped-token-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            '    let mut toks : List String := []\n'
            '    if secondFlag then\n'
            '      toks := toks ++ ["class"]\n'
            '    if firstFlag then\n'
            '      toks := toks ++ ["abstract"]\n'
            '    toks := toks ++ ["property"]\n'
            '    return toks'),
        "refinement": "this contributes the two optional tokens in the reverse "
                      "order. For an entity carrying BOTH flags the rendered "
                      "annotation reads `class abstract property ` where the "
                      "canonical rendering is `abstract class property `. The "
                      "failing tests assert the rendered annotation as an exact "
                      "string, so the ordering divergence is directly observed "
                      "and a faithful counterpart does NOT resolve; every "
                      "downstream consumer comparing the annotation text "
                      "diverges too.",
        "rationale": "REJECT from E3 alone (`out = annotationTokens firstFlag "
                     "secondFlag`), which is an exact ORDERED equality: on "
                     "(true, true) the impl yields the two optional tokens "
                     "transposed. E1 and E2 both still hold for it, so E3's "
                     "ordering content is the sole ground of the rejection "
                     "(recorded rejection cites exactly ensures_3 — the one "
                     "rival whose failure is confined to a single clause). "
                     "Refuted at (firstFlag=true, secondFlag=true), which is its "
                     "ONLY point of divergence: it agrees with the post-image on "
                     "the other three inputs, so no weaker point could "
                     "discriminate it.",
        "witness": _witness("true true"),
    },

    # No sibling counterpart — added for binder coverage in the OPPOSITE
    # direction. Every sibling rival under-emits; this one OVER-emits: the
    # second flag's token is contributed unconditionally, ignoring the binder.
    # It is the only rival refuted with BOTH flags off, and the only one that
    # demonstrates the post-image constrains what must be ABSENT as well as what
    # must be present — without it a rival that simply ignored the second binder
    # in the permissive direction would go uncaught by every other witness here.
    {
        "id": "weak-second-token-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            '    let mut toks : List String := []\n'
            '    if firstFlag then\n'
            '      toks := toks ++ ["abstract"]\n'
            '    toks := toks ++ ["class"]\n'
            '    toks := toks ++ ["property"]\n'
            '    return toks'),
        "refinement": "this contributes the second flag's token to EVERY entity, "
                      "whether or not the flag is set. An ordinary entity without "
                      "the flag is then annotated `class property ` instead of "
                      "`property `; the same failing test file asserts the "
                      "annotation for the flagless entity is exactly `property ` "
                      "(and, in the abstract case, `abstract property `), so "
                      "those assertions now fail where they previously passed. "
                      "The counterpart therefore does NOT resolve — it trades the "
                      "reported symptom for a regression on the untouched "
                      "entities, which the PASS_TO_PASS set covers as well.",
        "rationale": "REJECT from E3: the post-image contributes the second "
                     "token only under `secondFlag`, and the impl contributes it "
                     "unconditionally, so on `secondFlag = false` the assembled "
                     "list is strictly longer than `annotationTokens firstFlag "
                     "false`. (E1 and E2 are both satisfied by this rival — E2 is "
                     "only an implication and E1 only pins the tail — so E3's "
                     "exact-equality content is what refutes it; recorded "
                     "rejection cites ensures_3.) Refuted at "
                     "(firstFlag=false, secondFlag=false), the only witness "
                     "point where both binders are off, so it is what proves the "
                     "battery probes the second binder in BOTH directions rather "
                     "than only where its token is demanded.",
        "witness": _witness("false false"),
    },

    # Companion to weak-drops-second-token on the OTHER binder: the FIRST flag
    # contributes nothing. The sibling has no rival for this binder (its
    # pre-patch already handled the first flag), but without it no witness would
    # move the first binder to `true` with the second off, and a rival
    # mishandling only that input would verify unnoticed — the exact
    # binder-coverage hole the two known real failures had.
    {
        "id": "weak-drops-first-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            '    let mut toks : List String := []\n'
            '    if secondFlag then\n'
            '      toks := toks ++ ["class"]\n'
            '    toks := toks ++ ["property"]\n'
            '    return toks'),
        "refinement": "this drops the FIRST flag's token, so an entity carrying "
                      "it is annotated `property ` instead of `abstract "
                      "property `. tests/test_domain_py.py::test_pyproperty "
                      "asserts that annotation as an exact string for such an "
                      "entity, so the assertion fails and the counterpart does "
                      "NOT resolve. It also regresses behaviour that already "
                      "worked before the change, so it fails the PASS_TO_PASS "
                      "set on top of the F2P.",
        "rationale": "REJECT from E3: on `firstFlag = true` the assembled list "
                     "omits the first flag's token, so it differs from "
                     "`annotationTokens true secondFlag` (recorded rejection "
                     "cites ensures_3; E1 and E2 are unaffected, so this rival "
                     "isolates E3's dependence on the FIRST binder). Refuted at "
                     "(firstFlag=true, secondFlag=false) — the only witness point "
                     "with the first binder on and the second off, so it is what "
                     "moves the first binder independently of the second.",
        "witness": _witness("true false"),
    },

    # The only rival attacking E1 (`out ≠ [] ∧ out.getLast! = "property"`). The
    # always-present trailing token is contributed FIRST instead of last, so the
    # multiset is always right and the tail is wrong whenever any flag is set.
    # Shares its witness point with weak-swapped-token-order, which is forced by
    # pigeonhole (five rivals, four inputs); the sharing is honest because at
    # (T,T) BOTH rivals emit exactly the correct multiset in a wrong order — the
    # same failure mode — and this one is the broader of the two (wrong on three
    # of four inputs, so it claims no narrow sub-domain the point fails to
    # demonstrate), while its partner has (T,T) as its sole divergence and so
    # could not be moved. (T,T) is also the point where BOTH of this rival's
    # violated clauses fire at once.
    {
        "id": "weak-trailing-token-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            '    let mut toks : List String := ["property"]\n'
            '    if firstFlag then\n'
            '      toks := toks ++ ["abstract"]\n'
            '    if secondFlag then\n'
            '      toks := toks ++ ["class"]\n'
            '    return toks'),
        "refinement": "this seeds the always-present trailing token and appends "
                      "the optional tokens AFTER it, so an entity carrying either "
                      "flag is annotated `property abstract ` / `property class ` "
                      "instead of `abstract property ` / `class property `. The "
                      "failing tests assert the rendered annotation as an exact "
                      "string with the trailing token last, so a faithful "
                      "counterpart does NOT resolve — and it breaks the "
                      "already-working flagless-and-abstract renderings the "
                      "PASS_TO_PASS set covers.",
        "rationale": "REJECT from E1 (`out ≠ [] ∧ out.getLast! = \"property\"`) "
                     "and from E3: whenever any flag is set the last element is "
                     "an optional token rather than the always-present trailing "
                     "one, and the list order differs from `annotationTokens`. "
                     "This is the ONLY rival that violates E1, so without it the "
                     "trailing-token clause would be an unattacked independent "
                     "clause of the post-image (recorded rejection cites exactly "
                     "ensures_1 and ensures_3). Refuted at (firstFlag=true, "
                     "secondFlag=true), the point where both violated clauses "
                     "fire together.",
        "witness": _witness("true true"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The sibling battery ships 17 cases (4 soundness,
# 2 admissibility, 11 uniqueness) over FIVE contracted functions across three
# F2P-observable behaviours: the annotation assembly (its §A), the
# discovery decision plus its gated option-line emission (§B), and the
# member-retention decision plus its gated walk emission (§C).
#
# This bundle contracts ONE method, and it is the sibling's §A only. That is
# CARRIER NARROWING, recorded in mapping.md §3.2 and meta.json
# `additional_change_sites`: the recognition / docstring-extraction half of the
# change is live descriptor-protocol and MRO introspection over Python class
# objects, outside Velvet's expressible fragment and unsound to axiomatize
# (it is itself under change — SPEC_GUIDE directive 7). So the sibling's §B and
# §C have NO modeled counterpart here at all, and every case attached to them is
# legitimately omitted rather than re-aimed at a behaviour this bundle does not
# model. Chasing case-count parity would mean fabricating rivals against an
# unmodeled surface.
#
#   sibling case                     -> here
#   -------------------------------------------------------------------------
#   §A pos-prefix-reshape            -> pos-pure-assembly            PORTED
#                                    -> pos-reverse-prepend          PORTED (2nd shape)
#                                    -> pos-enumerated-cases         PORTED (3rd shape)
#   §A weak-prefix-no-class          -> weak-drops-second-token      PORTED
#   §A weak-prefix-swap-order        -> weak-swapped-token-order     PORTED
#   §B pos-disc-branch-reorder       -> (folded into pos-reverse-prepend)
#   §B admiss-gated-emit             -> (none)                       OMITTED (unmodeled §B)
#   §C admiss-walk-emit              -> (none)                       OMITTED (unmodeled §C)
#      [both re-aimed collectively   -> admiss-both-binders-separate RE-AIMED]
#   §B pos-popt-reshape              -> (none)                       OMITTED (unmodeled §B)
#   §C pos-retain-reshape            -> (none)                       OMITTED (unmodeled §C)
#   §B weak-disc-property-only       -> (none)                       OMITTED (unmodeled §B)
#   §B weak-disc-and-not-or          -> (none)                       OMITTED (unmodeled §B)
#   §B cflow-disc-no-establish       -> (none)                       VACUOUS (no capability)
#   §B cflow-disc-wrong-member       -> (none)                       VACUOUS (no capability)
#   §B weak-popt-no-classline        -> (none)                       OMITTED (unmodeled §B)
#   §B weak-popt-swap-order          -> (none)                       OMITTED (unmodeled §B)
#   §C weak-retain-drop-classlevel   -> (none)                       OMITTED (unmodeled §C)
#   §C cflow-retain-no-establish     -> (none)                       VACUOUS (no capability)
#   §C weak-wopt-no-classline        -> (none)                       OMITTED (unmodeled §C)
#   (no sibling counterpart)         -> weak-second-token-unconditional  ADDED
#   (no sibling counterpart)         -> weak-drops-first-token           ADDED
#   (no sibling counterpart)         -> weak-trailing-token-first        ADDED
#   AXIOM_TESTS (1)                  -> dropped (G-AX's lane)
#
# OMITTED — UNMODELED SURFACE (10 rows: the sibling's §B and §C rivals and
#   positives — 8 of them — plus its two admissibility cases, which have no
#   modeled gate to establish and are re-aimed collectively below).
#   Each attacks a decision (is this member documentable? is this
#   walked member retained?) or a gated option-line emission that has no symbol
#   in this Solution.lean. There is no clause of E1/E2/E3 they could be re-aimed
#   at without inventing a rival for a behaviour the bundle does not model, so
#   they are dropped. This is the carrier narrowing described above, not a
#   difficulty dodge: none was dropped because a proof would not close.
#
# VACUOUS — CAPABILITY / CONTROL-FLOW-EFFECT (3 cases: cflow-disc-no-establish,
#   cflow-disc-wrong-member, cflow-retain-no-establish). The sibling gates
#   emission behind body-less capability predicates minted by a sole producer,
#   and these rivals return the right VALUE while skipping the mint or minting
#   for the wrong member. That construction is a heap-resource one; this backend
#   is referentially transparent, and this bundle's obligation is a pure value
#   equality with no gated effect and no capability term to forge or misdirect.
#   Not fabricated a substitute for.
#
# VACUOUS — FRAME-MUTATION. The sibling records the class as N/A on its own
#   carrier already (no half-permission reference input). It is doubly vacuous
#   here: no heap, no aliasing, and no `mut` binder in this bundle.
#
# RE-AIMED — ADMISSIBILITY (sibling admiss-gated-emit + admiss-walk-emit ->
#   admiss-both-binders-separate). Both siblings establish that a capability
#   PRECONDITION admits a normal in-domain member. This method has no `require`
#   clause, so nothing could exclude any input and the probe is vacuous as
#   stated. Re-aimed at the residual total-domain risk: that the post-image is
#   DEGENERATE in a binder. The case discharges a concrete in-region assert that
#   flipping EITHER flag alone changes the demanded output, i.e. both binders are
#   live in the spec. Confirmed live: substituting the false claim (that the
#   second flag does not change the output) leaves `⊢ False` unsolved at
#   `admiss_1`, so the assert is real evidence and not decoration.
#
# ADDED (3, no sibling counterpart — all for binder / clause coverage):
#   * weak-second-token-unconditional. Every sibling rival under-emits; this one
#     over-emits. Without it nothing demonstrates the post-image constrains what
#     must be ABSENT, and it is the only witness with both binders off.
#   * weak-drops-first-token. The sibling has no rival on the FIRST binder (its
#     pre-patch already handled it). Without this rival no witness moves the
#     first binder on with the second off, so a rival mishandling only that input
#     would verify unnoticed — precisely the binder-coverage hole behind both
#     real failures found in correctly-narrowed ports so far.
#   * weak-trailing-token-first. The only attacker of E1; without it the
#     trailing-token clause is an unattacked independent top-level clause.
#
# DIVERGENCE (the sibling's MustTerminate lane) - the class is INAPPLICABLE to
#   this impl and CLOSED BY THE SEMANTICS against any rival that manufactures
#   it. The frozen impl is LOOP-FREE (straight-line ``let`` / ``if`` over
#   immutable values, no loop and no recursion), so there is no control flow
#   here to make diverge: a diverging rival cannot be obtained by mutating this
#   body, it has to bring a loop of its own. When it does, the semantics refuse
#   it. This bundle sets ``loom.semantics.termination "total"`` AND carries
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
# COVERAGE. Obligation: 1 (`prove_correct assembleModifierTokens`), defended by
#   3 soundness positives + 1 admissibility case and attacked by 5 rivals.
#   Independent top-level clauses attacked: E1 by weak-trailing-token-first,
#   E2 by weak-drops-second-token, E3 by all five — none left unattacked.
#   Binders moved by the reject witnesses: firstFlag {false, true},
#   secondFlag {false, true}; witness points {(F,F), (T,F), (F,T), (T,T)} =
#   pts 4, which is the ENTIRE input domain, so no binder is held at a fixed
#   value and the second binder is probed in both directions (token demanded and
#   token forbidden).
#
# AXIOM_TESTS: dropped. meta.json records `axioms: []` and
#   `deep_model_references: []`, and G-AX is `status=skip` / `no-axioms` — there
#   is no axiom-soundness obligation to probe, and this gate ignores the key
#   regardless.
AXIOM_TESTS = []
