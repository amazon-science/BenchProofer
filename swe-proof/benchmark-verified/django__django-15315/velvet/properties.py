"""properties.py — G-PBT falsification battery for django__django-15315 (velvet).

NOT a Velvet module; a manifest of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct fieldHashMethod`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation. Each case is checked by the
real verifier: ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  fieldHashMethod (pyHash : HashKey → Int) (intrinsicId : Int)
      (modelAssoc : Option (List Char × List Char)) return (out : Int)
    ensures out = pyHash (fieldHashKey intrinsicId)                        (C1)
    ensures out = pyHash (fieldKeyAt intrinsicId modelAssoc)               (C2)
    ensures ∀ a, out = pyHash (fieldKeyAt intrinsicId a)                   (C3)

The operation returns the integer digest that places a value into hash-based
containers. The digest must be computed from the value's assignment-independent
intrinsic identity ALONE: the association metadata the value happens to carry at
the moment of hashing must not enter the key. C1 pins the digest to the digest of
the solo key built from ``intrinsicId``; C2 restates that at the CURRENT lifecycle
state; C3 universally quantifies the lifecycle state, which is the immutability
guarantee itself — the digest is the same at every state the value could be in.
There is no precondition (the ``pre-conditions`` region is empty), so the admitted
domain is total.

THREE INPUT BINDERS, and all three are load-bearing for the reject lane:

  * ``pyHash : HashKey → Int`` — the hashing primitive, a FREE INPUT. The spec
    claims nothing about which integers it returns, so it holds for EVERY hashing
    function. This is what makes the carrier attackable: see the CARRIER NOTE.
  * ``intrinsicId : Int`` — the intrinsic identity. It is the ONLY thing the key
    may be built from, so a rival that drops it, constant-folds it, or replaces it
    with something derived from the association is refutable.
  * ``modelAssoc : Option (List Char × List Char)`` — the association metadata at
    hash time (``none`` while standalone, ``some (app, name)`` once associated).
    The key must NOT consult it; it is not declared ``mut``, and no clause mentions
    it except through ``fieldKeyAt``, which discards it.

The reject witnesses move all three: ``modelAssoc`` across
{``none``, ``some (['a'],['b'])``, ``some (['x','y'],['z'])``, ``some (['m'],['n'])``};
``intrinsicId`` across {0, 3, 4, 7, 9, 11}; and ``pyHash`` across two DIFFERENT
separating primitives (a key-shape separator that is even on a solo key and odd on
a composite one, and an identity-on-the-identity-component primitive that ignores
the key shape entirely and exposes the ``intrinsicId`` argument instead). Six
distinct input points; no binder is held at one value across the whole lane, and
no witness relies on the same ``pyHash`` instantiation as every other.

AUDIT CORRECTION — the strength ORDER of the two primitives. An earlier revision
of this manifest claimed the two ``pyHash`` shapes were each necessary for their
own rival class: that a constructor-separating primitive could not see a
wrong-ARGUMENT error, so without the identity-exposing shape "a rival that kept
the solo constructor but hashed the wrong integer would sail through". That is
measurably BACKWARDS, and the audit measured it rather than reasoning about it.
``sepHash`` is ``.solo i => 2 * i``, which is INJECTIVE in the identity component,
so it separates the identity ARGUMENT as well as the CONSTRUCTOR: rebuilt at the
two wrong-argument rivals' own witness points it refutes both (exit 0 against
each rival, exit 1 with ``⊢ False`` against the frozen solution — a real
discrimination, not a shared failure). The blindness runs the OTHER way:
``idcHash`` collapses the two constructors, so it cannot see a wrong key SHAPE,
and rebuilding an ``idc``-instantiated witness against all four shape-folding
rivals leaves it unprovable in every case (four builds, exit 1 each).

So the true relation is: ``sepHash`` is a UNIVERSAL discriminator for this lane
and ``idcHash`` is STRICTLY WEAKER. The second shape is therefore not what keeps
the identity argument covered — ``sepHash`` already does that — and this manifest
no longer claims it is. It is retained because it is a genuinely INDEPENDENT
hashing function: the spec is quantified over every primitive, so resting the
whole reject lane on one concrete ``pyHash`` would leave the possibility that the
lane's refutations were an artifact of that single function's arithmetic rather
than of the spec. Two primitives of different strength, one of which suffices
alone, is a weaker claim than the original prose made and is the one that is
true.

Every one of C1/C2/C3 is attacked. C1 is the primary target of every rival (it is
the clause each witness literally states the negation of). C2 and C3 are not
independent conjuncts a rival can violate in isolation: ``fieldKeyAt_eq`` is a
frozen ``rfl`` lemma, so ``fieldKeyAt intrinsicId a`` is DEFINITIONALLY
``fieldHashKey intrinsicId`` for every ``a``, which makes C2 and C3 provably
equivalent to C1 on this carrier. Both facts are machine-checked, not argued: the
three implications C1 -> C2, C2 -> C1 and C1 -> C3 each close by
``simpa [fieldKeyAt, fieldHashKey]`` (exit 0), and every reject rival's build
leaves all three ``ensures`` goals unsolved together rather than one of them. So
no impl exists that satisfies one clause and violates another, and attacking C1
IS attacking C2 and C3; this is recorded rather than papered over with a rival
whose rationale would claim a clause-splitting it cannot actually exhibit.

CARRIER NOTE — WHY THE REJECT LANE IS EXPRESSIBLE AT ALL.

The postcondition is stated over ``pyHash``, about which the spec assumes nothing.
Read naively that looks like the OPAQUE-carrier wall: ``pyHash (composite …)`` and
``pyHash (solo …)`` are not provably distinct, so no rival's violation looks like a
theorem, and one might conclude the lane is inexpressible and ship positives-only.
That conclusion is WRONG here, and the reason is worth stating precisely, because
it is the cheapest of the four escape routes rather than the hardest:

``pyHash`` is not an ``opaque`` constant — it is a BINDER of the method. A witness
therefore does not need to condition on it by hypothesis (the "conditioning on the
carrier" technique); it can simply INSTANTIATE it at a concrete separating
function of the witness's own choosing. Because the spec must hold for EVERY
hashing function, a single instantiation at which a rival's digest differs from the
spec's is a complete refutation — and it is a fully ``decide``-able one, since the
witness's chosen primitive is a concrete ``def`` that reduces by computation.

So each witness picks a primitive that exposes the thing its rival got wrong:

  * a rival that folds ``modelAssoc`` into the key (the wrong key SHAPE) is
    refuted by a primitive that separates the two constructors — even on a solo
    key, odd on a composite one;
  * a rival that keeps the solo shape but hashes the wrong INTEGER is refuted by a
    primitive that reads the identity component through and ignores the shape.

These are the most DIRECT pairings, not the only working ones. The
constructor-separating primitive is ``2 * i`` on a solo key, hence injective in
the identity component, so it in fact refutes the wrong-INTEGER rivals too;
the identity-exposing one collapses the constructors and refutes only the
wrong-integer class. Both directions were rebuilt and measured during the audit
— see the AUDIT CORRECTION above, which replaced an earlier claim that each
primitive was necessary for its own class.

The witness reaches the impl through Velvet's EXTRACTOR rather than its tester
machinery. ``derive_tester_for`` is unavailable on this method: C3 is a
``∀ a : Option (List Char × List Char)`` over an infinite domain, so
``prove_postcondition_decidable_for`` cannot synthesise a ``Decidable`` instance
and leaves ``Decidable (∀ a, out = pyHash (fieldKeyAt intrinsicId a))`` as an
unsolved goal (measured — the tester never forms). ``extract_program_for`` does
work: ``fieldHashMethodExec f i a`` is ``NonDetT.run (fieldHashMethod f i a)``, and
``fieldHashMethodExec f i a ≠ DivM.res (f (fieldHashKey i))`` states that the
extracted program's digest contradicts C1 at that concrete point. The frozen impl
is straight-line, so this reduces on both sides and the discrimination is real,
not an artifact of one side getting stuck: against gold the goal becomes ``False``
(gold satisfies C1 there, so the ``≠`` is unprovable — the required FAIL) and
against each rival it closes. Both halves were run with ``scripts/lean_verify.sh``
for every case below; no witness is shipped on the strength of an argument alone.

Each witness's binders: NONE. Every refutation is stated at literal inputs with a
concrete ``pyHash``, so there are no hypotheses that could be jointly unsatisfiable
and the ``witness-inconsistent`` failure mode is structurally unreachable here.

ADVERSARIAL READ of the sibling's classes on this carrier. The nagini sibling
contracts ONE function (``located_value``) over a heap object with four
fractionally-permissioned fields and a ``@ContractOnly`` digest oracle; this
backend models the same single decision as ``fieldHashMethod`` over three
value-level binders. The VALUE surface carries across intact and is where the whole
reject lane lands. The PERMISSION surface and the TERMINATION surface do not exist
here in the same way, and they have OPPOSITE dispositions:

  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries two of these as
    MANDATORY: every field is held read-only at a fractional permission, so a rival
    that WRITES one (even a self-assignment) is rejected by the permission system
    rather than by the postcondition. Lean and Velvet are referentially
    transparent: ``pyHash``, ``intrinsicId`` and ``modelAssoc`` are immutable
    values, none is declared ``mut``, there is no heap, no aliasing and no
    fractional permission — so there is no read-only input to overwrite and no
    permission system to trip. The class has NO carrier analogue. Not ported, and
    deliberately not substituted: a fabricated stand-in would test nothing while
    attesting that the class was covered. Demonstrated rather than argued: writing
    either read-only binder in the impl region (``intrinsicId := intrinsicId``,
    the sibling's self-assignment shape, and ``modelAssoc := none``) is not a
    rival the SPEC rejects but a file that does not parse — ```intrinsicId` cannot
    be mutated, only variables declared using `let mut` can be mutated``, followed
    by ``Failed to parse an assertion without names: WPGen sorry``. The rejection
    comes from the surface syntax before any obligation is formed, so such a case
    could carry no witness and would attest to nothing about the spec.

  * UNGUARDED OWNER-ATTRIBUTE READ — VACUOUS, for the same reason plus one more.
    The sibling's sharpest case (its audited G-EQ attack shape) returns the RIGHT
    digest but reads an association-derived attribute UNCONDITIONALLY, which in the
    real program raises on a standalone value; the sibling rejects it because its
    precondition grants that read only under the attachment flag. Here the
    association metadata is a total ``Option``, not a possibly-absent heap
    attribute: reading ``modelAssoc`` cannot fail, and an impl that reads it and
    then ignores it is genuinely CORRECT on this carrier (``pos-read-assoc-ignore``
    below is exactly that impl, shipped as a positive — it must verify, and does).
    The distinction the sibling's permission system draws is one this abstraction
    does not keep, so the rival is not wrong here and is not shipped as a reject.
    Its guarded-read POSITIVE control does port, and did.

  * DIVERGENCE / NON-TERMINATION — NOT a spec hole on this bundle, and NOT
    shippable as a reject case either. The disposition is CLOSED-BY-SEMANTICS,
    and this is the one class whose correct reading depends on a ``set_option``
    line rather than on the contract, so it is stated against what the bundle
    actually sets.

    AUDIT CORRECTION (this bullet previously read the semantics BACKWARDS). An
    earlier revision recorded this class as a KNOWN SPEC HOLE on the stated
    ground that the bundle sets ``loom.semantics.termination "partial"``, under
    which a diverging impl satisfies C1/C2/C3 vacuously and VERIFIES; it further
    claimed to have MEASURED that a diverging impl returning the wrong constant
    ``0`` verifies with exit 0. The frozen solution sets

        set_option loom.semantics.termination "total"

    so both the premise and the claimed measurement were wrong. Under ``total``
    the verifier discharges a termination obligation, and the disposition
    INVERTS: a diverging rival is REJECTED, not admitted. Re-measured on this
    bundle rather than inherited — splicing ``while True do pure ()`` into the
    impl region and reducing the proof to a bare ``loom_solve`` gives exit 1,
    ``error: Decreasing annotations are required in total correctness
    semantics``, both when the body then returns the unambiguously wrong
    constant ``0`` and when it returns gold's own expression (two builds, exit 1
    each). Two further diverging shapes (``while 0 == 0``, and an increasing
    counter ``while n >= 0``) give the same error. And the sharper shape, which
    cannot be dismissed as merely missing the annotation, is refused too: a loop
    that CARRIES a measure which does not decrease
    (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``, body
    ``q := q``) is REJECTED on the measure's own goal - ``case «decreasing_1: q»``,
    residual ``⊢ q < q``. (An earlier version of this passage set the result against
    a corpus census from an internal findings doc, a ``partial`` majority admitting
    the rival against a ``total`` minority rejecting it. That census is withdrawn:
    all 500 velvet bundles set ``"total"``, so there is no split to be on a side of.)

    So there is no verify-does-not-imply-resolve break in this class here, and
    nothing to escalate. Neither is the class shippable as a reject case,
    because a reject case needs a witness that ELABORATES against the rival, and
    the termination error fires at the METHOD, before any witness in the file is
    elaborated. Demonstrated rather than argued: appending even the trivially
    true ``example : (1:Nat) + 1 = 2 := by decide`` to a witness file built
    against the diverging rival gives exit 1 with the decreasing-annotations
    error, while the identical file built against the frozen solution gives exit
    0. The rival is therefore not refutable by witness — it is refused by the
    surface obligation, the way the frame-mutation rivals above are refused by
    the surface syntax — so no case is dropped for difficulty and none is owed.

  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. C1 pins the
    digest to ``pyHash`` applied to a key built from the method's own
    ``intrinsicId`` binder; there is no value-free answer key for a wrong impl to
    echo. The cheapest way to satisfy the clause is to build the right key, which
    the positive controls cover.

  * PARTIAL-DOMAIN — PORTS, and carries part of the reject lane. Three rivals
    below are correct on a sub-domain and wrong off it. Two partition on the
    ASSOCIATION binder (one folds the association in only once it is present; one
    only once it is present AND non-degenerate), which is the sibling's
    ``partial-domain-attached`` argument re-expressed on this carrier. The third
    (``rej-fold-assoc-at-one-identity``) partitions on the IDENTITY binder
    instead, folding the association in at exactly one intrinsic identity — the
    sibling's ``partial-domain-order-zero``, which an earlier revision of this
    manifest dropped WITHOUT recording it and which the audit re-derived as
    expressible here, not inexpressible. Each of the three gets its OWN witness at
    the input that distinguishes it, rather than sharing one, so no rival's
    rationale claims a sub-domain the manifest never demonstrates. The identity
    partition matters independently of the association ones: a spec that pinned
    the digest only "generically" over the identity — rather than pointwise —
    would admit it while rejecting all four association-shaped rivals.

  * WRONG-ARGUMENT — PORTS. The sibling's ``wrong-arg-*`` rivals call the same
    digest oracle on the wrong argument. Here that becomes: keep ``pyHash`` and keep
    the solo key CONSTRUCTOR, but hand it an integer derived from the association
    rather than the intrinsic identity. This is the route the carrier note's
    second-escape-route covers, and it is the reason the witnesses vary ``pyHash``
    itself — refuting it needs a primitive that reads the identity component
    through.

  * AXIOM_TESTS — dropped per the porting map. This bundle axiomatizes nothing
    (the ``axioms`` region is empty and the digest primitive is a free input), so
    there is no axiom lane to drop from; G-AX is ``skip`` on this cell.
"""
from pathlib import Path

INSTANCE = "django__django-15315"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the frozen impl body. Lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap, so the manifest breaks loudly on drift).
_GOLD_IMPL = "    return pyHash (fieldHashKey intrinsicId)"
assert _BASE.count(_GOLD_IMPL) == 1, "impl region drifted from expected text"

# ---- the impl-start marker line (unique): the admissibility case inserts an
# ---- in-region `assert` right after it and keeps the whole frozen body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). One
# ---- positive control reshapes the impl to a form `loom_solve` alone no longer
# ---- closes and retunes this WITHOUT touching the spec and without dropping the
# ---- `prove_correct fieldHashMethod` obligation.
_GOLD_PROOF = "prove_correct fieldHashMethod by\n  loom_solve"
assert _BASE.count(_GOLD_PROOF) == 1, "proof anchor drift"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced
    (frozen tactic script kept verbatim)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, _GOLD_IMPL, new_body), _GOLD_PROOF, new_proof)


# ---------------------------------------------------------------------------
# Witness preamble and the two separating primitives.
#
# `derive_tester_for` is unavailable (C3 quantifies an infinite domain, so no
# `Decidable` instance synthesises — measured), so a witness reaches the impl
# through Velvet's EXTRACTOR: `fieldHashMethodExec f i a` is
# `NonDetT.run (fieldHashMethod f i a)`, and `≠ DivM.res (f (fieldHashKey i))`
# states that the extracted program's digest contradicts C1 at that point.
# Checked in a file whose `prove_correct` block has been stripped, so no tactic
# script can mask the verdict.
#
# `pyHash` is a METHOD BINDER, not an opaque constant, so each witness
# INSTANTIATES it at a concrete separating function rather than conditioning on
# it by hypothesis. The spec must hold for every hashing function, so one
# instantiation at which the rival's digest differs is a complete refutation —
# and a `decide`-able one, since the chosen primitive reduces by computation.
# Two shapes, picked to expose two DIFFERENT mistakes:
#
#   `sep*`  separates the key CONSTRUCTORS (even on solo, odd on composite).
#           Because its solo branch is `2 * i`, it is also injective in the
#           identity component, so it refutes BOTH the wrong-SHAPE and the
#           wrong-INTEGER rivals (measured on all six).
#   `idc*`  reads the identity component through and ignores the shape:
#           refutes a rival that keeps the solo shape but hashes the WRONG
#           integer, and is BLIND to a wrong key shape (measured: an
#           idc-instantiated witness is unprovable against all four
#           shape-folding rivals). Strictly weaker than `sep*`; retained so the
#           lane does not rest on a single concrete hashing function, since the
#           spec is quantified over every primitive.
#
# Each witness declares its primitive under a per-case name so the snippets stay
# independent (the gate appends one witness per build).
_EXTRACT = "extract_program_for fieldHashMethod\n\n"


def _sep(tag):
    """A primitive separating the two key constructors."""
    return (f"def sepHash{tag} : HashKey → Int\n"
            f"  | .solo i => 2 * i\n"
            f"  | .composite i _ => 2 * i + 1\n\n")


def _idc(tag):
    """A primitive exposing the identity component, blind to the key shape."""
    return (f"def idcHash{tag} : HashKey → Int\n"
            f"  | .solo i => i\n"
            f"  | .composite i _ => i\n\n")


def _witness(prim, tag, ident, assoc):
    """`fieldHashMethodExec <prim> <ident> <assoc> ≠ DivM.res (<prim> (solo ident))`
    — the rival's digest contradicts C1 at this concrete point."""
    fn = f"{'sepHash' if prim == 'sep' else 'idcHash'}{tag}"
    decl = _sep(tag) if prim == "sep" else _idc(tag)
    return (
        _EXTRACT + decl +
        f"example : fieldHashMethodExec {fn} {ident} {assoc}\n"
        f"    ≠ DivM.res ({fn} (fieldHashKey {ident})) := by\n"
        "  unfold fieldHashMethodExec fieldHashMethod\n"
        f"  simp [NonDetT.run, pure, {fn}, fieldHashKey]\n")


SPEC_TESTS = [
    # =====================================================================
    # UNIQUENESS (expect="reject") — wrong impls sharing the frozen spec.
    #
    # Each was confirmed with real `scripts/lean_verify.sh` runs on THREE files:
    # the variant itself (must NOT verify — each fails all three `ensures` goals),
    # the witness against the rival (must elaborate), and the witness against the
    # frozen solution (must fail; the goal degenerates to `False`).
    #
    # Re-run independently during the audit, all six rivals: variant exit 1 with
    # three unsolved `ensures` goals carrying the rival's actual key expression;
    # witness-against-rival exit 0; witness-against-gold exit 1 with the goal
    # `⊢ False` in every case. That last detail is the one that matters for
    # discrimination: gold's failure is a SEMANTIC refutation — `simp` reduced both
    # sides and found them EQUAL, leaving `False` — not a missing identifier, a
    # type error, a stuck `decide`, or a timeout, any of which would make the
    # witness a non-discriminator the gate could not distinguish from a real one.
    # =====================================================================
    {
        # The sibling's `partial-domain-attached` / pre-fix shape, unconditional:
        # the key always folds in the association metadata. Wrong on every input,
        # including the standalone one — which is why its witness sits at
        # `modelAssoc = none`, the sub-domain where even the most charitable
        # reading of the rival has no excuse.
        "id": "rej-fold-assoc-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return pyHash (HashKey.composite intrinsicId modelAssoc)"),
        "refinement": (
            "The faithful real patch keys the digest on a composite of the "
            "intrinsic identity together with the association metadata. That is "
            "precisely the behaviour the issue reports as broken: the digest moves "
            "when the value becomes associated, so a value stored in a hash-based "
            "container before association can no longer be found in it afterwards. "
            "The F2P test takes the digest of a standalone value, associates it, "
            "and asserts the digest is UNCHANGED — with the association folded in, "
            "the two digests differ and the test stays RED. It does NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = pyHash (fieldHashKey intrinsicId)`), and "
            "equivalently C2/C3, on the `modelAssoc` binder: the impl builds a key "
            "the clause does not name. Witness instantiates `pyHash` at a "
            "constructor-separating primitive and refutes at `intrinsicId = 3`, "
            "`modelAssoc = none` — the standalone point, where the rival's "
            "composite key still differs from the solo key the clause pins. If it "
            "VERIFIES => SPEC-TOO-WEAK (the key shape is unconstrained)."),
        "witness": _witness("sep", "A", "3", "none"),
    },
    {
        # Partial-domain: correct while standalone, folds the association in once
        # it is present. This is the sibling's `partial-domain-attached` argument
        # verbatim — the branch structure of the pre-fix code — and it is a strict
        # NEAR-MISS of the rival above, agreeing with gold on the whole
        # `modelAssoc = none` sub-domain. So it gets its own witness at an
        # ASSOCIATED point rather than sharing the one above, which would refute it
        # at an input where it is in fact correct.
        "id": "rej-fold-assoc-once-present",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return pyHash (match modelAssoc with\n"
            "      | none => HashKey.solo intrinsicId\n"
            "      | some a => HashKey.composite intrinsicId (some a))"),
        "refinement": (
            "The faithful real patch keys on the intrinsic identity alone while "
            "the value is standalone and on a composite once it carries "
            "association metadata — i.e. it preserves exactly the lifecycle "
            "dependence the issue asks to remove. The F2P test hashes BEFORE "
            "association (this branch agrees with the desired digest) and AFTER "
            "(this branch does not), then asserts EQUALITY, so the two differ and "
            "the test stays RED. It does NOT resolve."),
        "rationale": (
            "REJECT from C1/C2/C3 on the `modelAssoc` binder, restricted to the "
            "associated sub-domain. Witness instantiates `pyHash` at a "
            "constructor-separating primitive and refutes at `intrinsicId = 7`, "
            "`modelAssoc = some (['a'], ['b'])` — an ASSOCIATED point, which is "
            "where this rival and the always-folding one above diverge from each "
            "other. If it VERIFIES => SPEC-TOO-WEAK (C3's universal quantification "
            "over the lifecycle state is not actually binding)."),
        "witness": _witness("sep", "B", "7", "(some (['a'], ['b']))"),
    },
    {
        # Deeper partial-domain: folds the association in only when it is present
        # AND its first component is non-degenerate. Agrees with gold on strictly
        # MORE of the domain than either rival above (all standalone inputs, plus
        # every associated input whose first component is empty), so it needs a
        # witness at an associated point with a non-empty first component.
        "id": "rej-fold-assoc-nondegenerate-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return pyHash (match modelAssoc with\n"
            "      | some (app, nm) =>\n"
            "          if app.isEmpty then HashKey.solo intrinsicId\n"
            "          else HashKey.composite intrinsicId (some (app, nm))\n"
            "      | none => HashKey.solo intrinsicId)"),
        "refinement": (
            "The faithful real patch folds the association metadata into the key "
            "only when that metadata is populated — a plausible 'be careful about "
            "empty components' shape that still leaves the digest dependent on the "
            "lifecycle state in the ordinary case. Real associations carry "
            "non-empty name components, so the F2P test's value takes this branch: "
            "its digest changes across association and the equality assertion "
            "stays RED. It does NOT resolve."),
        "rationale": (
            "REJECT from C1/C2/C3 on the `modelAssoc` binder, on the narrower "
            "associated-and-populated sub-domain — a strictly harder near-miss "
            "than the two rivals above, so it is witnessed separately. Witness "
            "refutes at `intrinsicId = 11`, `modelAssoc = some (['m'], ['n'])`. If "
            "it VERIFIES => SPEC-TOO-WEAK (C3 admits a lifecycle-dependent key on "
            "some sub-domain)."),
        "witness": _witness("sep", "H", "11", "(some (['m'], ['n']))"),
    },
    {
        # WRONG-ARGUMENT (the sibling's `wrong-arg-*` class): keep the digest
        # primitive AND the solo key constructor, but build the key from an
        # integer derived from the association instead of from the intrinsic
        # identity. This is the rival that makes the `intrinsicId` binder
        # load-bearing for the lane. It is witnessed with the identity-exposing
        # primitive, which reads the identity component through; NOTE (audit)
        # that the constructor-separating primitive ALSO refutes it — `2 * i` is
        # injective in `i` — so this witness's choice of primitive is a matter of
        # stating the error in its most direct form, not of necessity. See the
        # AUDIT CORRECTION in the module docstring.
        "id": "rej-wrong-arg-assoc-derived",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return pyHash (fieldHashKey (match modelAssoc with\n"
            "      | none => (0 : Int)\n"
            "      | some (app, nm) => Int.ofNat (app.length + nm.length)))"),
        "refinement": (
            "The faithful real patch hashes a quantity derived from the "
            "association metadata rather than the intrinsic identity. Two "
            "independent failures follow. First, the digest still moves across the "
            "association event, so the F2P equality assertion stays RED. Second, "
            "it discards the intrinsic identity entirely, so distinct values "
            "collide wholesale — a P2P test asserting that separately-created "
            "values of the same shape are distinguishable, and the ordering tests "
            "built on the intrinsic identity, observe the collapse. It does NOT "
            "resolve."),
        "rationale": (
            "REJECT from C1/C2/C3 on the `intrinsicId` binder: the key has the "
            "right SHAPE (solo) but the wrong ARGUMENT. Witness instantiates "
            "`pyHash` at a primitive that reads the identity component through "
            "and refutes at `intrinsicId = 9`, `modelAssoc = none`, where the "
            "rival keys on `0` and the clause pins `9`. If it VERIFIES => "
            "SPEC-TOO-WEAK (the key's identity argument is unconstrained). The "
            "constructor-separating primitive refutes this rival too (measured), "
            "so this case does not rest on its primitive being the only one that "
            "works — it rests on the clause being violated at this point."),
        "witness": _witness("idc", "I", "9", "none"),
    },
    {
        # Wrong-argument, off by the association's size: the key stays solo and
        # still mentions the intrinsic identity, but is perturbed by a quantity
        # derived from the association. The subtlest of the four — it agrees with
        # gold on every standalone input AND is injective in the identity, so it
        # breaks neither the collision property nor the standalone sub-domain.
        # Only the lifecycle-independence clause refutes it.
        "id": "rej-wrong-arg-perturbed-by-assoc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    return pyHash (fieldHashKey (intrinsicId +\n"
            "      (match modelAssoc with\n"
            "       | none => (0 : Int)\n"
            "       | some (app, nm) => Int.ofNat (app.length + nm.length))))"),
        "refinement": (
            "The faithful real patch perturbs the hashed identity by a quantity "
            "read off the association metadata. It keeps distinct values distinct "
            "(so the collision and ordering P2P tests still pass — this is why it "
            "is the subtlest of the rivals), but the digest of any given value "
            "still changes at the moment it becomes associated. The F2P test hashes "
            "before and after association and asserts equality, so it stays RED. It "
            "does NOT resolve."),
        "rationale": (
            "REJECT from C1/C2/C3 on the interaction of the `intrinsicId` and "
            "`modelAssoc` binders: the key is solo and identity-derived, so only "
            "the lifecycle-independence the clauses pin refutes it. Witness "
            "instantiates `pyHash` at the identity-exposing primitive and refutes "
            "at `intrinsicId = 4`, `modelAssoc = some (['x','y'], ['z'])`, where "
            "the rival keys on 7 and the clause pins 4 — a THIRD distinct "
            "`(intrinsicId, modelAssoc)` point, and the only witness whose "
            "association has a multi-character component. If it VERIFIES => "
            "SPEC-TOO-WEAK."),
        "witness": _witness("idc", "F", "4", "(some (['x', 'y'], ['z']))"),
    },
    {
        # AUDIT ADDITION — the port dropped the sibling's
        # `partial-domain-order-zero` without recording it as an omission, and it
        # is expressible here rather than inexpressible. Every rival above
        # partitions the domain on the ASSOCIATION binder (`modelAssoc`); this one
        # partitions on the IDENTITY binder instead, folding the association in at
        # exactly ONE intrinsic identity and behaving like gold at every other. It
        # is therefore the narrowest near-miss in the battery: it agrees with the
        # frozen impl on all but a single point of an infinite binder, so no
        # witness at any other identity refutes it, and none of the five witnesses
        # above sits at this point. Its own witness must be — and is — placed at
        # that identity.
        "id": "rej-fold-assoc-at-one-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if intrinsicId == 0 then\n"
            "      return pyHash (HashKey.composite intrinsicId modelAssoc)\n"
            "    else\n"
            "      return pyHash (fieldHashKey intrinsicId)"),
        "refinement": (
            "The faithful real patch special-cases a single intrinsic identity "
            "and keys that one value on a composite of its identity together with "
            "its association metadata, while every other value is keyed on its "
            "identity alone. The digest of that one value therefore still moves at "
            "the moment it becomes associated, so the F2P scenario — take the "
            "digest of a standalone value, associate it, assert the digest is "
            "UNCHANGED — stays RED whenever the value under test is the "
            "special-cased one. Since intrinsic identities are handed out in "
            "sequence from a counter that starts at zero, the special-cased "
            "identity is an ordinarily-reachable one, not an exotic input. It does "
            "NOT resolve."),
        "rationale": (
            "REJECT from C1 (`out = pyHash (fieldHashKey intrinsicId)`), and "
            "equivalently C2/C3, on the `intrinsicId` binder — the ONLY rival in "
            "this battery that partitions the domain on the identity rather than "
            "on the association, and the narrowest near-miss here: it agrees with "
            "the frozen impl at every identity but one. Witness instantiates "
            "`pyHash` at a constructor-separating primitive and refutes at "
            "`intrinsicId = 0`, `modelAssoc = none` — a SIXTH distinct input point, "
            "and the only one at which this rival is wrong, so no other witness in "
            "the lane would catch it. If it VERIFIES => SPEC-TOO-WEAK (C1 is not "
            "binding pointwise across the identity binder — a spec that pinned the "
            "digest only 'generically' would admit exactly this)."),
        "witness": _witness("sep", "Z", "0", "none"),
    },

    # =====================================================================
    # SOUNDNESS (expect="verify") — structurally DIFFERENT but CORRECT impls.
    # Each must verify or the spec is SPEC-TOO-STRONG on the shape of the impl.
    # All four were confirmed to build with real `scripts/lean_verify.sh` runs.
    # =====================================================================
    {
        # The sibling's `pos-control-local-bind`: same computation, bound through
        # typed locals. Cheapest possible reshape; the frozen tactic script still
        # closes it, so it isolates "the spec does not care about the impl's
        # syntactic form" from any proof-retuning question.
        "id": "pos-local-bind",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let k := fieldHashKey intrinsicId\n"
            "    let d := pyHash k\n"
            "    return d"),
        "rationale": (
            "A correct impl in a different syntactic shape (the key and the digest "
            "bound to locals rather than composed in one expression) must verify; "
            "else SPEC-TOO-STRONG. Frozen proof body kept verbatim."),
    },
    {
        # The sibling's `pos-control-branch-reorder`: an explicit branch on the
        # lifecycle state that returns the SAME digest either way. A correct impl
        # is allowed to LOOK association-dependent as long as it is not; this is
        # the positive that keeps the reject lane above from being satisfiable by
        # a spec that simply forbids mentioning `modelAssoc`.
        "id": "pos-vacuous-assoc-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    if modelAssoc.isSome then\n"
            "      return pyHash (fieldKeyAt intrinsicId modelAssoc)\n"
            "    else\n"
            "      return pyHash (fieldHashKey intrinsicId)"),
        "rationale": (
            "An impl that branches on the lifecycle state but returns the same "
            "digest on both branches is still correct (both arms discharge "
            "C1/C2/C3), so it must verify; else SPEC-TOO-STRONG — the spec would be "
            "constraining the impl's control flow rather than its digest."),
    },
    {
        # The port of the sibling's `pos-control-guarded-owner-read`, adapted to
        # what this carrier keeps. The sibling's version reads the association
        # attributes under the attachment guard and discards them; here reading
        # `modelAssoc` needs no guard (it is a total `Option`), so the meaningful
        # residue of that case is: an impl may CONSULT the association metadata as
        # long as the digest does not depend on it. Reaching the clause through
        # `fieldKeyAt` — which takes the metadata and discards it — is exactly
        # that. Must verify, else SPEC-TOO-STRONG.
        "id": "pos-read-assoc-ignore",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    return pyHash (fieldKeyAt intrinsicId modelAssoc)"),
        "rationale": (
            "An impl that passes the lifecycle state into the key builder — which "
            "discards it — computes the pinned digest and must verify; else "
            "SPEC-TOO-STRONG (the spec would forbid an impl from so much as "
            "MENTIONING the read-only input, which is a constraint on syntax, not "
            "on behaviour). This is the carrier's counterpart of the sibling's "
            "guarded-read positive control, whose faithful real patch resolves."),
    },
    {
        # Reshape to the underlying constructor: `fieldHashKey i` unfolds to
        # `.solo i` by definition, so this is the SAME computation stated one layer
        # down. It is the one positive whose reshape outruns the frozen tactic
        # script (`loom_solve` alone leaves all three `ensures` goals: measured),
        # so the tactic BODY is retuned by adding the definitional unfolding. The
        # `prove_correct fieldHashMethod` header and the spec are untouched; the
        # obligation is reproven, not weakened — no helper lemma, no `sorry`.
        "id": "pos-inline-key-constructor",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "    return pyHash (HashKey.solo intrinsicId)",
            "prove_correct fieldHashMethod by\n"
            "  loom_solve\n"
            "  all_goals simp [fieldHashKey]"),
        "rationale": (
            "Building the key with its constructor directly is definitionally the "
            "same computation as going through the key builder, so the impl is "
            "correct and must verify; else SPEC-TOO-STRONG. The frozen script is "
            "tuned to the builder-shaped impl and leaves three goals here, so the "
            "tactic body is retuned with the definitional unfolding — the "
            "obligation's statement is byte-identical and is genuinely reproven."),
    },

    # =====================================================================
    # ADMISSIBILITY (expect="verify") — the admitted domain is non-vacuous and
    # the pinned post-image is non-degenerate on it.
    # =====================================================================
    {
        # The sibling's `admiss-call-and-stability`, re-expressed. The sibling
        # asserts that an F2P-shaped input satisfies its fractional-permission
        # precondition and that the pinned value is stable across attachment. This
        # method has NO precondition (the region is empty) and no permission
        # surface, so the "is the input admitted" half is degenerate — every input
        # is in domain. The residual risk is a DEGENERATE post-image: if the pinned
        # key collapsed, the spec would be satisfiable without doing the work and
        # the reject lane above would be measuring nothing.
        #
        # AUDIT REPAIR (this case previously asserted the STABILITY conjuncts
        # only, while its id and rationale claimed non-degeneracy). Stability does
        # NOT imply non-degeneracy, and the gap is not rhetorical: the three
        # stability conjuncts are provable for an ARBITRARY key builder, including
        # the totally collapsed `fun _ => .solo 0` that discards the intrinsic
        # identity. Machine-checked: with `fieldKeyAt` derived from an arbitrary
        # `anyKey : Int → HashKey`, `⟨rfl, rfl, rfl⟩` closes all three conjuncts
        # (exit 0). So the shipped assert pinned only that the key IGNORES the
        # lifecycle state — which `fieldKeyAt`'s frozen `rfl` lemma already gives
        # for free — and pinned NOTHING about the post-image being non-degenerate,
        # which is the half the case's id promises and the half the reject lane's
        # meaningfulness actually rests on.
        #
        # So the assert now carries BOTH halves: the stability conjuncts as
        # before, PLUS non-degeneracy — a concrete separation (`fieldHashKey 3 ≠
        # fieldHashKey 4`) and injectivity of the key in the identity. Those are
        # exactly what a collapsed key refutes, so the assert can no longer be
        # discharged by a spec that pins nothing. The frozen impl body is kept
        # verbatim; the tactic body is retuned (`loom_solve` alone leaves the new
        # conjuncts: measured) without touching the spec or dropping the
        # `prove_correct fieldHashMethod` obligation, which discharges alongside.
        "id": "admiss-stability-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_START,
                _IMPL_START +
                "    assert (with_name_prefix `admiss (\n"
                "      fieldKeyAt intrinsicId none = fieldHashKey intrinsicId ∧\n"
                "      fieldKeyAt intrinsicId (some (['a'], ['b']))\n"
                "        = fieldHashKey intrinsicId ∧\n"
                "      pyHash (fieldKeyAt intrinsicId none)\n"
                "        = pyHash (fieldKeyAt intrinsicId (some (['a'], ['b']))) ∧\n"
                "      fieldHashKey 3 ≠ fieldHashKey 4 ∧\n"
                "      (∀ i j : Int, fieldHashKey i = fieldHashKey j → i = j)))\n"),
            _GOLD_PROOF,
            "prove_correct fieldHashMethod by\n"
            "  loom_solve\n"
            "  all_goals simp [fieldHashKey]"),
        "rationale": (
            "The admitted domain is total (the `pre-conditions` region is empty), "
            "so the sibling's precondition-admits-a-normal-input probe is "
            "degenerate here; the residual risk is a degenerate post-image. This "
            "case discharges an in-region assertion with BOTH halves. (a) "
            "STABILITY: the pinned key is the SAME at both F2P-shaped lifecycle "
            "states — standalone and associated — hence so is the digest, for an "
            "arbitrary hashing primitive; that is the property the scenario in the "
            "report turns on. (b) NON-DEGENERACY: the key SEPARATES distinct "
            "identities (`fieldHashKey 3 ≠ fieldHashKey 4`) and is injective in "
            "the identity. (b) is load-bearing and is not implied by (a): the "
            "stability conjuncts alone hold of a totally collapsed key builder "
            "that discards the identity (machine-checked), under which the spec "
            "would be satisfiable without doing the work and the reject lane would "
            "be measuring nothing. Impl body kept verbatim; the tactic body is "
            "retuned for the added conjuncts, so the method's own obligation "
            "discharges alongside. If this fails => PRECOND-TOO-STRONG or a "
            "degenerate post-image."),
    },
]
