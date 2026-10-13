"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9367 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct renderSequence`` obligation survives with a
byte-identical statement) and swaps in a candidate impl; it is checked by the
real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  renderSequence (elts : List (List Char)) return (out : List Char)
    ensures out = renderTuple elts

The method renders the source form of a parenthesized comma-separated sequence
from the already-rendered text of its members, as a function of the member
count alone. The single load-bearing ``ensures`` pins ``out`` to the deep,
fully-unfolded ``renderTuple`` (the ``axioms`` region is EMPTY — no opaque
answer key to echo). ``renderTuple`` composes THREE independently-attackable
top-level clauses, keyed on the member count:

  * EMPTY (no members) ↦ the bare empty pair ``()``.
  * SINGLE (exactly one member) ↦ the member wrapped with a TRAILING COMMA,
    ``(m,)`` — the headline behaviour: the one-member sequence must stay
    distinct from the bare parenthesized member ``(m)``.
  * MANY (two or more members) ↦ the members joined by ``", "`` inside parens,
    ``(m₁, m₂, …)`` — the join separator is the two characters comma-space.

SOLE INPUT BINDER: ``elts : List (List Char)``. It is load-bearing through and
through: its LENGTH selects which of the three clauses fires and the returned
shape, and its element text is copied into the result. The six reject witnesses
drive it to inputs whose lengths span {0, 1, 2, 3} and whose member text spans
one- and multi-character members, so the manifest demonstrates the post-image's
dependence BOTH on the member count (the empty form, the single-member
trailing-comma form, the two-member separated form, and the ≥3-member form
beyond the first adjacency) and on the member TEXT being copied through
unmodified — not on a single pinned shape.

NOTE ON WITNESS SEPARATION (audited, measured): the member text is NOT what
separates the two single-member near-misses. Because the spec depends on member
content only by copying it through, ``weak-single-no-comma`` is refuted at
``[['x']]`` just as it is at ``[['1']]``, and ``weak-single-comma-space`` at
``[['1']]`` just as at ``[['x']]`` (both cross-checks built: rival exit 0). The
two length-1 points are therefore two SPELLINGS of one point, and what actually
separates those two rivals is the distinct WRONG VALUE each returns there, not
the input. The member text becomes load-bearing only at
``weak-single-copies-member-text``, whose rival agrees with gold at every
one-character member and is refuted only at a multi-character one.

CARRIER NOTE — the carrier is FULLY COMPUTABLE. ``renderTuple`` and the
extracted program are concrete definitions over ``List (List Char)`` with
``DecidableEq``. So a witness reaches the post-image through Velvet's tester
machinery (``renderSequenceTester elts = false`` says the extracted program's
result violates the postcondition at that concrete input) and closes by
``decide``, checked in a file whose ``prove_correct`` block is stripped so no
tactic script can mask the verdict. Because both the extracted program and the
pure model reduce fully at a literal ``List (List Char)``, every witness here is
a plain literal input — no conditioning is needed. Each was built the two
required ways with ``scripts/lean_verify.sh``: the tester elaborates green
against its rival (``decide`` proves ``= false``) and FAILS against the frozen
solution (``decide`` proves the same proposition is *false*, i.e. gold satisfies
the postcondition at that input).

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally-different but
    behaviourally-identical correct impls (a direct return of the grounded
    model; a reorder of the count branches) must verify, else the spec is
    SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — RE-AIMED. The method has NO ``require`` (the pre-conditions
    region is empty), so the sibling's "a normal input satisfies the
    precondition" probe is degenerate: every input is admitted. The residual
    admissibility risk on a total domain is a DEGENERATE post-image — a spec no
    impl distinguishes reads exactly like one every impl meets.
    ``admiss-nondegenerate`` discharges an in-region ``assert`` pinning all
    THREE clauses at F2P-shaped inputs (empty ↦ ``()``, single ↦ ``(1,)`` with
    the comma, two ↦ ``(1, 2)`` fully separated) — three genuinely distinct
    values; the impl is kept verbatim so the method's own obligation still
    discharges. The assert is LIVE, not decoration: a false claim about the same
    point leaves an unsolved goal (checked by hand).
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries a
    MANDATORY frame rival that writes into the read-only member-rendering list
    held at ``Acc(list_pred(elts),1/2)``, rejected by Viper's permission system.
    Lean/Velvet are referentially transparent: ``elts`` is an immutable
    ``List (List Char)`` value declared read-only (not ``mut``), there is no
    heap, no aliasing, no fractional permission, no permission system. There is
    no read-only input to overwrite and no frame clause to violate, so the class
    has no carrier analogue. NOT ported (fabricating a substitute would test
    nothing). DEMONSTRATED rather than asserted (audit): the nearest expressible
    analogue of "the impl tampers with its read-only input" is to SHADOW the
    input binder in-region (``let elts := []``) and answer for the shadowed
    value. That variant is in scope and is REJECTED (exit 1, ``unsolved goals``
    with ``['(', ')'] = match elts with ...``), because the postcondition's
    ``elts`` is the METHOD PARAMETER and no in-region binding can rebind it — so
    the carrier gives the frame guarantee structurally, with nothing left for a
    frame rival to falsify. See the footer for the case-by-case accounting.
  * DIVERGENCE / NON-TERMINATION — the sibling carries ``w-diverge`` (an endless
    loop before the return, rejected on nagini by ``MustTerminate(2)``). The
    frozen file reads ``set_option loom.semantics.termination "total"`` (line 4),
    so this bundle is in the bucket that REJECTS the measure-less diverging
    rival, not the ``partial`` bucket that admits it. The nagini case's ATTACK is
    therefore ANSWERED here, by the same direction of obligation
    ``MustTerminate(2)`` supplies there — this is NOT a spec hole in the naive
    form, and it is NOT vacuous either.

    SECOND AUDIT CORRECTION (this is a re-derivation, not an inherited claim; the
    disposition tracks the termination option and must be re-measured if it ever
    moves). An earlier revision of this note recorded the class as a KNOWN SPEC
    HOLE on the ground that the bundle runs ``partial`` and a diverging impl
    "VERIFIES (exit 0)". That was accurate when written — the frozen file then
    read ``partial`` — and went STALE when the option was flipped to ``total``,
    which is the remediation the divergence lane needed. Re-measured
    directly against the artifact this file now ships beside, twice:
      * ``while True do pure ()`` spliced after ``-- impl-start`` ahead of gold's
        own body, proof reduced to a bare ``loom_solve``  ->  REJECTED, exit 1;
      * the same prefix returning an unambiguously wrong value (``"()"`` for
        every input)                                       ->  REJECTED, exit 1;
    both with ``error: Decreasing annotations are required in total correctness
    semantics`` — the total-correctness obligation, i.e. a rejection attributable
    to the spec, on the METHOD DECLARATION.

    It is still NOT shipped as a reject case, for a MECHANICAL reason that was
    measured rather than assumed. A velvet reject case needs a witness that
    ELABORATES against the rival, and that same missing-measure error is raised
    on the method declaration, which SURVIVES into the witness file (only the
    ``prove_correct`` block is stripped). Built it: the witness against the
    diverging rival exits 1 on the declaration error before reaching its claim,
    and additionally shows ``decide`` stuck — "``Tactic `decide` failed`` …
    ``did not reduce to `isTrue` or `isFalse``", reduction stuck at the
    ``Decidable`` instance. Witness half 1 is unmeetable, so such a case could
    only ever record ``witness-unproven`` / ``witness-undecided`` — a malformed
    case, not an attestation. Nor can a ``witness_reference`` rescue it: that
    hatch replaces the SECOND subject (the one the witness must fail against),
    and the half that fails here is the FIRST. Disposition: the class is closed
    by the frozen spec and unrepresentable in this manifest — nothing is owed and
    no hole is claimed in this form.

    NO RESIDUAL, and this paragraph RETRACTS the one a previous revision filed.
    That revision claimed the ``total`` obligation is discharged by ANY measure
    expression without proving it decreases, so that a constant-true guard with an
    omitted ``done_with`` launders a wrong answer through an unreachable exit, and
    reported ``while 0 < 1`` carrying ``decreasing (0 : Nat)`` and returning
    ``"()"`` for every input as VERIFYING at exit 0. RE-MEASURED on this bundle,
    that shape is REJECTED at exit 1 on the MEASURE's own descent goal:
    ``unsolved goals case «decreasing_1: (0 : Nat)» ... ⊢ 0 < 0``. The
    strict-decrease side condition IS proven, and the corpus-wide escalation is
    withdrawn here.
    THE MECHANISM, so the retraction does not rest on one build: both header lines
    select the total scope. ``set_option loom.semantics.termination "total"``
    itself opens ``TotalCorrectness`` (Loom, ``MonadAlgebras/WP/Options.lean``,
    the ``openScope `TotalCorrectness`` arm), line 7 of the frozen file opens it
    again explicitly, and ``TotalCorrectness.WPGen.forWithInvariantLoop`` takes
    the ``measure`` and emits ``⌜measure b' < measure b⌝`` as a goal the proof
    must discharge. Only the ``PartialCorrectness`` twin takes a measure and drops
    it. So the measure-carrying rival is rejected for the same reason the
    measure-less one is, and neither is shippable, for the MECHANICAL witness
    reason above rather than because the spec admits either.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``renderTuple
    elts``, a fully-unfolded ``def`` over the method's own argument; there is no
    answer-key term a wrong impl could echo. The cheapest correct impl computes
    the rendering honestly, which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (the single-member form without
    the trailing comma — the pre-patch bug; the single-member form with a stray
    comma-space; the empty form with a stray comma; the multi form with the
    separator dropped; plus two AUDIT ADDITIONS closing sub-domains the ported
    four left unattacked — the separator dropped only past the FIRST adjacency,
    refutable only at length ≥ 3, and the member's own TEXT permuted rather than
    copied through, refutable only at a member longer than one character).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The bundle declares no axiom
(mapping.md §3: the changed op is modeled deeply and concretely, validated by
G-CONF, so G-AX is vacuous); the sibling's ``AXIOM_TESTS`` is likewise empty.
The G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9367"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (between and INCLUDING the
# ---- markers). Full-body variants replace exactly this text, so each edit lies
# ---- wholly inside the one -- impl-start .. -- impl-end region and same_spec
# ---- holds by construction. Presence + uniqueness asserted at load.
_IMPL = ('    -- impl-start\n'
         '    let result : List Char := match elts with\n'
         '      | []  => "()".toList\n'
         '      | [e] => "(".toList ++ e ++ ",)".toList\n'
         '      | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList\n'
         '    return result\n'
         '    -- impl-end')
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the three count-clause branch lines, each wholly inside the impl region
# ---- and unique. The reject rivals reshape exactly one of these, so each edit
# ---- stays in-region and same_spec holds.
_EMPTY = '      | []  => "()".toList\n'
_SINGLE = '      | [e] => "(".toList ++ e ++ ",)".toList\n'
_MANY = '      | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList\n'
assert _BASE.count(_EMPTY) == 1, "empty-branch anchor drift"
assert _BASE.count(_SINGLE) == 1, "single-branch anchor drift"
assert _BASE.count(_MANY) == 1, "many-branch anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- rival that reshapes the impl retunes it without touching the spec or
# ---- dropping the `prove_correct renderSequence` obligation.
_PROOF_GOLD = "prove_correct renderSequence by\n  loom_solve\n  rfl"
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a flat proof body: when the impl returns the grounded model directly the
# ---- goal is `renderTuple elts = renderTuple elts`, which `loom_solve` alone
# ---- closes. The reject rivals keep the gold proof (they are refuted by the
# ---- witness, not by whether the tuned script happens to close), so only the
# ---- soundness positives retune the proof.
_PROOF_FLAT = "prove_correct renderSequence by\n  loom_solve"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `renderSequenceTester elts = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. Every argument is a concrete `List (List Char)`
# ---- literal so `decide` reduces the extracted program fully (the carrier has
# ---- DecidableEq and every helper is a concrete def). ----
def _tester(body):
    return ("\n"
            "extract_program_for renderSequence\n"
            "prove_precondition_decidable_for renderSequence\n"
            "prove_postcondition_decidable_for renderSequence\n"
            "derive_tester_for renderSequence\n\n" + body)


def _witness(elts_literal):
    return _tester(
        f"example : renderSequenceTester {elts_literal} = false := by\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no intermediate let/match at all — maximally structurally different
        # from the gold branch chain. `out` IS `renderTuple elts`, so the ensures
        # holds trivially; the reproof is a bare `loom_solve`. Also the honest
        # no-ungrounded-echo control: the model IS the real work, so a direct
        # return is correct, not a cheat. (Verified: exit 0.)
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    return renderTuple elts\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_FLAT),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`renderTuple elts` directly (no intermediate match). `out` IS that "
            "model, so `out = renderTuple elts` holds on the whole domain; the "
            "reproof is `loom_solve`. If this fails to verify the spec is over-fit "
            "to the branch-chain code shape (SPEC-TOO-STRONG). (Sibling: "
            "pos-control-direct-materialize — the grounded-model direct return.)"),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different: the SINGLE (n==1) match arm is tested before the
        # EMPTY (n==0) arm. Every arm body is byte-identical to gold, so the
        # computed value is identical for every input; only the executable order
        # of the two short-circuit arms changes. `rfl` no longer closes the
        # reordered match definitionally, so the proof is retuned to a case-split
        # (`rcases elts … <;> rfl`) that discharges each concrete arm. Must
        # verify, else SPEC-TOO-STRONG. (Verified: exit 0.)
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    let result : List Char := match elts with\n"
                  '      | [e] => "(".toList ++ e ++ ",)".toList\n'
                  '      | []  => "()".toList\n'
                  '      | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList\n'
                  "    return result\n"
                  "    -- impl-end"),
            _PROOF_GOLD,
            "prove_correct renderSequence by\n"
            "  loom_solve\n"
            "  rcases elts with _ | ⟨e, _ | ⟨f, rest⟩⟩ <;> rfl"),
        "rationale": (
            "reordering the two short-circuit count arms (single tested before "
            "empty) while keeping every arm body byte-identical computes the same "
            "value on every input, so `out = renderTuple elts` still holds on the "
            "whole domain; the reproof case-splits `elts` and closes each arm by "
            "`rfl`. A correct reshape must verify, else the postcondition is "
            "SPEC-TOO-STRONG (rejects a faithful impl over the shape of the match). "
            "(Sibling: pos-control-branch-reorder.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The method has NO `require` (pre-conditions region
    # empty), so the sibling's "a normal input satisfies the precondition" probe
    # is degenerate: nothing could exclude an F2P-shaped input. The residual
    # admissibility risk on a total domain is a DEGENERATE post-image — a spec no
    # impl distinguishes reads exactly like one every impl meets. This case
    # discharges an in-region `assert`, at three fully concrete F2P-shaped inputs,
    # that the rendering is NON-DEGENERATE: the empty sequence renders to `()`, a
    # ONE-member sequence renders to `(1,)` WITH the trailing comma (the headline
    # behaviour, NOT `(1)`), and a TWO-member sequence renders to `(1, 2)` fully
    # separated — three genuinely distinct values jointly exercising all three
    # count clauses. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the proof gains a `decide` arm to clear the
    # assert goal. The assert is LIVE, not decoration: a false claim about the same
    # points leaves an unsolved goal (checked by hand — a variant claiming the
    # one-member form renders `(1)` fails with an unsolved `renderTuple [['1']] =
    # ['(','1',')']` goal). (Verified: exit 0.)
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      renderTuple ([] : List (List Char)) = \"()\".toList ∧\n"
                  "      renderTuple [['1']] = ['(', '1', ',', ')'] ∧\n"
                  "      renderTuple [['1'], ['2']] = ['(', '1', ',', ' ', '2', ')']))\n"),
            _PROOF_GOLD,
            "prove_correct renderSequence by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | rfl\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at concrete "
            "F2P-shaped inputs: the empty sequence must render to `()`, a "
            "one-member sequence must render to `(1,)` WITH the trailing comma "
            "(NOT `(1)`), and a two-member sequence must render to `(1, 2)` fully "
            "separated — three distinct values exercising all three count clauses. "
            "The in-region assert must discharge (else the obligation is "
            "degenerate); the impl is kept verbatim so `out = renderTuple elts` "
            "still verifies. (Sibling: admiss-single-member-form, re-aimed from "
            "precondition admissibility to post-image non-degeneracy since this "
            "backend's method carries no `require` and there is no permission "
            "surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival breaks exactly
    # one count clause of `renderTuple`; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-single-no-comma",
        "kind": "uniqueness",
        "expect": "reject",
        # The SINGLE arm drops the trailing comma, rendering `(m)` instead of
        # `(m,)` — EXACTLY the pre-patch behaviour and the F2P failure. Correct on
        # empty and multi; diverges only on the one-member sub-domain.
        "module": _swap(_BASE, _SINGLE,
                        '      | [e] => "(".toList ++ e ++ ")".toList\n'),
        "refinement": (
            "this is the pre-change behaviour: a one-member sequence collapses to "
            "`(m)`, losing the trailing comma that keeps it distinct from a bare "
            "parenthesized member. The failing scenario that renders a one-element "
            "tuple asserts `(1,)`; rendering `(1)` fails that assertion exactly — "
            "it does NOT resolve. This is the discriminating F2P behaviour."),
        "rationale": (
            "REJECT from `out = renderTuple elts` via the SINGLE clause: the spec "
            "pins a one-member sequence to `(m,)` (with the comma), but this rival "
            "returns `(m)`. Verifying would be SPEC-TOO-WEAK (the trailing-comma "
            "behaviour unpinned). Refuted on the one-member sub-domain — the "
            "sequence `[['1']]`, where gold renders `(1,)` and the rival `(1)`. "
            "(Sibling: partial-domain-single-no-comma.)"),
        "witness": _witness("[['1']]"),
    },
    {
        "id": "weak-single-comma-space",
        "kind": "uniqueness",
        "expect": "reject",
        # The SINGLE arm renders `(m, )` (comma-space before the close paren) — a
        # plausible "reuse the member separator" slip. The trailing form must be a
        # bare comma then `)`, not comma-space-`)`. Correct on empty and multi;
        # diverges only on the one-member sub-domain, at a DIFFERENT wrong value
        # than weak-single-no-comma (so the two do not share a witness for a
        # near-miss neither actually fails at).
        "module": _swap(_BASE, _SINGLE,
                        '      | [e] => "(".toList ++ e ++ ", )".toList\n'),
        "refinement": (
            "a faithful counterpart that emitted `(m, )` (a stray space after the "
            "comma) would render a one-element tuple as `(1, )`; the failing "
            "scenario asserts the exact string `(1,)` with no space — it does NOT "
            "resolve. Correct on every empty and every multi-member sequence."),
        "rationale": (
            "REJECT from `out = renderTuple elts` via the SINGLE clause: the spec "
            "pins the one-member close to a bare comma then `)`, but this rival "
            "inserts a space. Verifying would be SPEC-TOO-WEAK (the exact "
            "trailing-comma form unpinned). Refuted on the one-member sub-domain — "
            "the sequence `[['x']]`, where gold renders `(x,)` and the rival "
            "`(x, )`. (Sibling: uniqueness-single-comma-space.)"),
        "witness": _witness("[['x']]"),
    },
    {
        "id": "weak-empty-stray-comma",
        "kind": "uniqueness",
        "expect": "reject",
        # The EMPTY arm renders `(,)` instead of `()`. Correct on single and
        # multi; diverges only on the empty sub-domain.
        "module": _swap(_BASE, _EMPTY,
                        '      | []  => "(,)".toList\n'),
        "refinement": (
            "a patch that emitted `(,)` for the empty sequence (e.g. an off-by-one "
            "that always appended a trailing comma) would render the empty tuple "
            "as `(,)`; the scenario that renders an empty tuple asserts `()` — it "
            "does NOT resolve. Correct on every one-member and every multi-member "
            "sequence."),
        "rationale": (
            "REJECT from `out = renderTuple elts` via the EMPTY clause: the spec "
            "pins the no-member case to `()`, but this rival returns `(,)`. "
            "Verifying would be SPEC-TOO-WEAK (the empty form unpinned). Refuted on "
            "the empty sub-domain — the sequence `[]`, where gold renders `()` and "
            "the rival `(,)`. This is the sub-domain length-1/length-2 rivals agree "
            "with gold on, so they do NOT share a witness. (Sibling: "
            "partial-domain-empty-stray-comma.)"),
        "witness": _witness("([] : List (List Char))"),
    },
    {
        "id": "weak-multi-missing-sep",
        "kind": "uniqueness",
        "expect": "reject",
        # The MANY arm joins with the EMPTY separator instead of `", "`, so a
        # multi-member sequence renders concatenated with no separators: `(12)`
        # instead of `(1, 2)`. Correct on empty and single; diverges on the
        # two-or-more sub-domain.
        "module": _swap(_BASE, _MANY,
                        '      | _   => "(".toList ++ List.intercalate [] elts ++ ")".toList\n'),
        "refinement": (
            "a join that omitted the comma-space separator (`\"\".join` rather than "
            "`\", \".join`) would render `(1, 2)` as `(12)`; the scenarios that "
            "render multi-member tuples assert the fully-separated form — it does "
            "NOT resolve. Correct on every empty and every one-member sequence."),
        "rationale": (
            "REJECT from `out = renderTuple elts` via the MANY clause: the spec "
            "joins two-or-more members by `\", \"` (comma-space), but this rival "
            "joins by the empty separator. Verifying would be SPEC-TOO-WEAK (the "
            "member separator unpinned). Refuted on the two-member sub-domain — the "
            "sequence `[['1'],['2']]`, where gold renders `(1, 2)` and the rival "
            "`(12)`. This drives the member count to ≥ 2, the only sub-domain the "
            "single/empty rivals do not touch. (Sibling: "
            "partial-domain-multi-missing-sep.)"),
        "witness": _witness("[['1'],['2']]"),
    },
    {
        "id": "weak-single-copies-member-text",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION. Every other rival attacks the WRAPPING (which literal
        # characters surround/separate the members); none attacks whether the
        # member text itself is copied through UNMODIFIED. This rival keeps the
        # trailing-comma wrapping exactly right and reverses the single member's
        # text instead. It is invisible at every one-character member — it agrees
        # with gold on all of `[]`, `[['1']]`, `[['x']]`, `[['1'],['2']]`, i.e.
        # at EVERY witness point the rest of the battery uses — so without this
        # case the clause "the member's own text is copied verbatim" is unprobed.
        # Refuted only at a MULTI-character member. (Built: rival exit 0, gold
        # exit 1 with "`decide` proved that the proposition renderSequenceTester
        # [['a', 'b']] = false is false".)
        "module": _swap(_BASE, _SINGLE,
                        '      | [e] => "(".toList ++ e.reverse ++ ",)".toList\n'),
        "refinement": (
            "a counterpart that transformed the member's own rendered text while "
            "wrapping it (e.g. assembling the one-member form from the member's "
            "characters in the wrong order) renders a one-member sequence whose "
            "member text is longer than one character incorrectly: a member "
            "rendered `ab` comes out `(ba,)` instead of `(ab,)`. Every scenario "
            "that renders a one-member sequence asserts the member's own text "
            "unchanged inside the wrapping — it does NOT resolve. Note it is "
            "correct at every SINGLE-character member, which is exactly why the "
            "count-shaped witnesses do not catch it."),
        "rationale": (
            "REJECT from `out = renderTuple elts` via the SINGLE clause's MEMBER "
            "TEXT rather than its wrapping: the spec pins the one-member form to "
            "`(` ++ e ++ `,)` for the member text `e` AS GIVEN, but this rival "
            "emits a permutation of `e`. Verifying would be SPEC-TOO-WEAK (the "
            "pass-through of member text unpinned, with only the punctuation "
            "constrained). Refuted at the two-character member `[['a','b']]`, "
            "where gold renders `(ab,)` and the rival `(ba,)`. This is the only "
            "case whose witness needs a member longer than one character; it is "
            "what makes the element-text half of the binder load-bearing. "
            "(Sibling: no direct analogue — the sibling's PSeq[int] member "
            "carrier made this class awkward to state; it is expressible here.)"),
        "witness": _witness("[['a','b']]"),
    },
    {
        "id": "weak-sep-dropped-past-first-adjacency",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION. `weak-multi-missing-sep` drops the separator for the
        # WHOLE many-clause, so it is already refuted at the shortest multi input
        # (length 2). That leaves the ≥3 sub-domain — where the join must place a
        # separator at EVERY adjacency, not just the first — unattacked. This
        # rival gets length 2 exactly right (hard-coded, correctly separated) and
        # drops the separator only from length 3 up, so it is refutable ONLY at
        # length ≥ 3. Drives `elts.length` to 3, a point no other case reaches.
        # (Built: rival exit 0, gold exit 1 with "`decide` proved that the
        # proposition renderSequenceTester [['1'], ['2'], ['3']] = false is
        # false".)
        "module": _swap(
            _BASE, _MANY,
            '      | [a, b] => "(".toList ++ a ++ ", ".toList ++ b ++ ")".toList\n'
            '      | _   => "(".toList ++ List.intercalate [] elts ++ ")".toList\n'),
        "refinement": (
            "a counterpart that separated only the first adjacent pair and "
            "concatenated the rest (e.g. joining the first two members with the "
            "separator and then appending the remainder raw) renders a "
            "two-member sequence correctly but a three-member one as `(123)` "
            "instead of `(1, 2, 3)`. A scenario that renders a three-member "
            "sequence asserts the fully-separated form — it does NOT resolve, "
            "while every empty, one-member and TWO-member scenario still passes, "
            "which is what makes it a distinct near-miss."),
        "rationale": (
            "REJECT from `out = renderTuple elts` via the MANY clause at length "
            "≥ 3: the spec places the comma-space separator at EVERY adjacency, "
            "but this rival places it only in the length-2 case it hard-codes. "
            "Verifying would be SPEC-TOO-WEAK (the join pinned only at the "
            "shortest multi input, leaving `intercalate`'s repetition across all "
            "adjacencies unconstrained). Refuted at `[['1'],['2'],['3']]`, where "
            "gold renders `(1, 2, 3)` and the rival `(123)`; it AGREES with gold "
            "at the length-2 point `weak-multi-missing-sep` uses, so the two do "
            "not share a witness. (Sibling: partial-domain-multi-missing-sep, "
            "whose backward loop dropped the separator on its LAST step only — "
            "that sibling's per-adjacency aim is recovered here, since the "
            "loop-free `intercalate` shape cannot express a per-step slip.)"),
        "witness": _witness("[['1'],['2'],['3']]"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The sibling battery ships 8 SPEC cases (2 soundness positives, 1
# admissibility, 4 uniqueness value/branch rivals, 1 MANDATORY frame-mutation
# rival, 1 divergence rival) plus an EMPTY axiom lane (AXIOM_TESTS = []). The
# sibling contracts `render_tuple(elts : List[PSeq[int]])` held at a half
# permission `Acc(list_pred(elts),1/2)`, pinned to a deep closed-form model
# `render_seq(ToSeq(elts))` with a `MustTerminate(2)` termination obligation and
# a multi-member backward loop carrying six invariants. This velvet bundle models
# the SAME rendering DEEPLY and CONCRETELY as one narrowed method `renderSequence`
# whose post-image `renderTuple elts` composes the three count clauses (empty /
# single-with-trailing-comma / many-joined-by-", "). The carrier is referentially
# transparent and the do-block is a straight-line match (no loop), which reshapes
# the map:
#
#   sibling case                     kind          -> here                          disposition
#   ---------------------------------------------------------------------------------------------
#   pos-control-direct-materialize   soundness     -> pos-control-direct-model      PORTED
#   pos-control-branch-reorder       soundness     -> pos-control-branch-reorder    PORTED
#   admiss-single-member-form        admissibility -> admiss-nondegenerate          RE-AIMED
#   frame-mutation-write-elts        uniqueness    -> (none)                        VACUOUS
#   partial-domain-single-no-comma   uniqueness    -> weak-single-no-comma          PORTED
#   partial-domain-empty-stray-comma uniqueness    -> weak-empty-stray-comma        PORTED
#   partial-domain-multi-missing-sep uniqueness    -> weak-multi-missing-sep        PORTED
#   uniqueness-single-comma-space    uniqueness    -> weak-single-comma-space       PORTED
#   w-diverge                        uniqueness    -> (none)                        CLOSED BY SPEC
#   AXIOM_TESTS (none)               axiom         -> (none)                        N/A (G-AX)
#   (no sibling analogue)            uniqueness    -> weak-single-copies-member-     AUDIT ADD
#                                                     text
#   (no sibling analogue)            uniqueness    -> weak-sep-dropped-past-first-   AUDIT ADD
#                                                     adjacency
#
# 4 uniqueness ported + 2 added by audit, 1 admissibility re-aimed, 2 soundness
# ported; 1 frame rival vacuous (demonstrated, see above); 1 divergence rival
# closed by the frozen spec's total-correctness obligation but unrepresentable as
# a manifest case (re-measured, see below); axiom lane empty.
#
# AUDIT ADDITIONS (independent adversarial re-derivation, attack D). The ported
#   four rivals all attack the WRAPPING punctuation, and three of the four are
#   refutable at a member of length 1. Two sub-domains were therefore unprobed,
#   and a wrong impl in either would have VERIFIED against nothing the battery
#   contained:
#     * weak-sep-dropped-past-first-adjacency — the join's REPETITION across
#       every adjacency. `weak-multi-missing-sep` drops the separator for the
#       whole many-clause, so it dies at length 2 and never reaches length 3.
#       A rival correct at length 2 and unseparated from length 3 up is refuted
#       only at `[['1'],['2'],['3']]` (built: rival 0, gold 1 by `decide`).
#     * weak-single-copies-member-text — the PASS-THROUGH of member text. The
#       spec reads member content only by copying it, so a rival that permutes
#       the member's characters agrees with gold at EVERY one-character member,
#       i.e. at every witness point the ported battery uses. Refuted only at
#       `[['a','b']]` (built: rival 0, gold 1 by `decide`).
#   Both were confirmed REJECTED by the frozen spec before being added, so
#   neither is a spec hole — they are battery gaps, now closed.
#
# PORTED (both positives): pos-control-direct-materialize ports directly — the
#   cheapest honest correct impl returns the grounded model `renderTuple elts`
#   directly (verified, exit 0). pos-control-branch-reorder ports directly — the
#   two short-circuit count arms are reordered (single before empty) with every
#   arm body byte-identical; `rfl` no longer closes the reordered match
#   definitionally, so the proof is retuned to `rcases elts … <;> rfl` (verified,
#   exit 0). The sibling kept the multi-loop+invariants byte-identical; on this
#   loop-free carrier the reorder is a pure match-arm reorder.
# RE-AIMED (admiss-single-member-form -> admiss-nondegenerate): the sibling
#   asserts a one-member input is admitted+pinned by its half-permission
#   precondition. This backend's method has no `require`, so that probe is
#   degenerate; the sharper residual risk is a DEGENERATE post-image, so the case
#   is re-aimed to a live in-region assert pinning all three count clauses
#   (empty ↦ `()`, single ↦ `(1,)`, two ↦ `(1, 2)`) at F2P-shaped inputs — the
#   assert is live (a false variant claiming `(1)` for the one-member form leaves
#   an unsolved goal, checked). Verified, exit 0.
# PORTED (the four value/branch rivals): partial-domain-single-no-comma ports to
#   weak-single-no-comma (the literal pre-patch shape — drop the trailing comma;
#   the F2P discriminator). partial-domain-empty-stray-comma ports to
#   weak-empty-stray-comma (`(,)` for the empty tuple). partial-domain-multi-
#   missing-sep ports to weak-multi-missing-sep (join by the empty separator so
#   `(1, 2)` renders `(12)`). uniqueness-single-comma-space ports to
#   weak-single-comma-space (`(m, )` with a stray space — refuted at a DIFFERENT
#   one-member value than weak-single-no-comma so the two near-misses do not share
#   a witness). All four witnesses discriminate: the tester elaborates green
#   against the rival and `decide` proves the same proposition false against gold
#   (confirmed with scripts/lean_verify.sh: rival exit 0, gold exit 1 with
#   "Tactic `decide` proved that the proposition renderSequenceTester … = false").
# VACUOUS (frame-mutation-write-elts): the sibling's MANDATORY frame rival writes
#   into the member-rendering list held at `Acc(list_pred(elts),1/2)` (setting the
#   same value back), rejected by Viper for insufficient permission. This backend
#   is referentially transparent: `elts` is an immutable `List (List Char)` value
#   declared read-only (not `mut`), there is no heap, no aliasing, no fractional
#   permission, no permission system. There is no read-only input to overwrite and
#   no frame clause to violate, so the class has no carrier analogue. Omitted as a
#   genuine carrier fact, NOT fabricated (porting map: this class is vacuous on a
#   referentially-transparent backend).
# CLOSED BY THE SPEC (w-diverge), and unrepresentable as a manifest case. The
#   sibling's divergence rival (endless loop before the return) is rejected on
#   nagini by `MustTerminate(2)`. It is rejected HERE too, by the analogous
#   obligation: line 4 of the frozen file reads
#   `set_option loom.semantics.termination "total"`, so this bundle sits in the
#   bucket that REJECTS the measure-less
#   diverging rival — not the `partial` bucket that admits it. So the nagini
#   case's attack is ANSWERED, and this lane is neither a spec hole in the naive
#   form nor a vacuous class.
#
#   NOT INHERITED — re-derived with the real verifier, because the disposition
#   INVERTS with the termination option and an earlier revision of this file got
#   it backwards. That revision recorded the class as a KNOWN SPEC HOLE, claiming
#   a diverging impl "VERIFIES (exit 0)" under `partial`. It was accurate when
#   written (the frozen file then read `partial`) and went STALE when the option
#   was flipped to `total`, which is exactly the remediation the divergence lane
#   needed. Measured against the artifact this file
#   now ships beside:
#     * `while True do pure ()` ahead of gold's own body, proof reduced to a bare
#       `loom_solve`                                            -> exit 1
#     * the same prefix returning an unambiguously wrong value   -> exit 1
#     both with `error: Decreasing annotations are required in total correctness
#     semantics` — the total-correctness obligation on the METHOD DECLARATION,
#     i.e. a rejection attributable to the spec.
#   The retracted secondary claim that a diverging impl "cannot even be written in
#   this shape" is also gone: it splices in-region fine and stays in scope
#   (`variant_problems` empty). It is simply REJECTED rather than accepted.
#
#   Still NOT shipped as a reject case, for a MECHANICAL reason that was measured:
#   a velvet reject case needs a witness that ELABORATES against the rival, and
#   the missing-measure error is raised on the method DECLARATION, which survives
#   into the witness file (only the `prove_correct` block is stripped). Built it —
#   the witness against the diverging rival exits 1 on that declaration error
#   before reaching its claim, and additionally shows `decide` stuck ("did not
#   reduce to `isTrue` or `isFalse`", stuck at the `Decidable` instance). Witness
#   half 1 is unmeetable, so the case could only ever record `witness-unproven` /
#   `witness-undecided` — a malformed case, not an attestation. A
#   `witness_reference` cannot rescue it either: that hatch substitutes the SECOND
#   subject (the impl the witness must FAIL against), whereas the half failing
#   here is the FIRST. Nothing is owed from this lane.
#
#   NO RESIDUAL, and this entry RETRACTS the one a previous revision filed. That
#   revision claimed the `total` obligation is discharged by ANY measure expression
#   without proving it decreases, so that a constant-true guard with an omitted
#   `done_with` launders a wrong answer through an unreachable exit, and reported
#   `while 0 < 1` carrying `decreasing (0 : Nat)` and returning `"()"` for every
#   input as VERIFYING (exit 0). RE-MEASURED on this cell, that shape is REJECTED
#   at exit 1 on the measure's own descent goal:
#       unsolved goals
#       case «decreasing_1: (0 : Nat)» ... |- 0 < 0
#   Mechanism: `set_option loom.semantics.termination "total"` (line 4) itself
#   opens the `TotalCorrectness` scope (Loom, `MonadAlgebras/WP/Options.lean`,
#   `openScope `TotalCorrectness`), line 7 opens it again, and
#   `TotalCorrectness.WPGen.forWithInvariantLoop` takes the `measure` and emits
#   `measure b' < measure b` as a goal; only the `PartialCorrectness` twin discards
#   it. The corpus-wide escalation is withdrawn on this cell, and the
#   measure-carrying rival is unshippable for the same MECHANICAL witness reason as
#   the measure-less one, not because the spec admits it.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = renderTuple elts` has
#   ONE binder `elts : List (List Char)`, and `renderTuple` composes THREE
#   independent count clauses (empty / single / many). The six reject witnesses
#   probe these input points:
#     * weak-single-no-comma                  [['1']]              (len 1)
#     * weak-single-comma-space               [['x']]              (len 1)
#     * weak-empty-stray-comma                []                   (len 0)
#     * weak-multi-missing-sep                [['1'],['2']]        (len 2)
#     * weak-sep-dropped-past-first-adjacency [['1'],['2'],['3']]  (len 3)
#     * weak-single-copies-member-text        [['a','b']]          (len 1, member
#                                                                   len 2)
#   `elts.length` ranges over {0, 1, 2, 3}, so each count clause is independently
#   attacked: EMPTY by weak-empty-stray-comma; SINGLE by weak-single-no-comma (the
#   discriminating behaviour), weak-single-comma-space (a distinct WRONG VALUE at
#   the same length) and weak-single-copies-member-text (the member-text
#   pass-through); MANY by weak-multi-missing-sep at the shortest multi input and
#   weak-sep-dropped-past-first-adjacency past the first adjacency.
#
#   HONEST ACCOUNTING of what separates what (audit, measured — the coverage
#   reporter counts distinct input POINTS and cannot see this). The two length-1
#   punctuation near-misses are NOT separated by their inputs: `[['1']]` and
#   `[['x']]` are two spellings of one point, because the spec touches member
#   content only by copying it. Cross-checked with real builds — the
#   no-comma rival is refuted at `[['x']]` and the comma-space rival at `[['1']]`
#   (both rival builds exit 0). What separates those two rivals is the distinct
#   wrong VALUE each returns at that one point, which is legitimate but is a
#   different claim than "distinct input sub-domains". Genuinely distinct
#   sub-domains in this set: len 0, len 1, len 2, len 3, and member-len ≥ 2.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3: the changed op
#   is modeled deeply and concretely, validated by G-CONF, so G-AX is vacuous);
#   the sibling's AXIOM_TESTS is likewise empty. This gate ignores AXIOM_TESTS
#   regardless.
AXIOM_TESTS = []
