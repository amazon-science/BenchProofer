"""properties.py — G-PBT falsification battery for django__django-15731 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct buildForwarderMeta`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over two read-only structure binders):

  buildForwarderMeta (forwarder target : CallableMeta) return (out : CallableMeta)
    ensures out.name = target.name        -- C1
    ensures out.doc  = target.doc          -- C2
    ensures out.sig  = target.sig          -- C3

``CallableMeta`` is the introspectable surface of a callable, restricted to the
three fields the desired behaviour constrains: its introspected ``name``, its
introspected ``doc``, and the string form of its call ``sig``. Building a
forwarding wrapper around ``target`` must, under introspection, present the
wrapper AS the target on ALL THREE observations — not merely its name and
documentation, but also its call signature, which must resolve to the target's
rather than the wrapper's own generic forwarding form. The three ``ensures`` are
INDEPENDENT top-level clauses, each pinning one observed field of the result to
the corresponding field of ``target``. The method carries NO ``require`` clause,
so the admitted domain is total: every ``(forwarder, target)`` pair is in scope.

WHICH CLAUSE CARRIES THE GRADED F2P. C3 (``out.sig = target.sig``) is the
load-bearing clause for the failing test: the pre-change wrapper propagates only
the name and documentation and leaves its own generic forwarding signature in
place, so the string form of its call signature is the forwarder's, not the
target's — the exact observable the failing test pins. C1/C2 are pinned because
the modeled propagation is the FULL standard wrapper-decorator effect on all
three observed fields (mapping.md §3.1), and the change ships an added attributes
test that asserts the wrapper's name and documentation equal the target's; a
patch that diverges on either is not the faithful change. Every clause is both
DEFENDED (the positives + admissibility discharge all three) and ATTACKED (one
rival per clause).

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-mutate-source-name`` / ``frame-mutate-source-sig`` rivals write
    through a read-only (``Acc(.,1/2)``) reference to the source and are rejected
    for INSUFFICIENT PERMISSION. Lean and Velvet are referentially transparent:
    ``forwarder`` and ``target`` are immutable values, this method declares no
    ``mut`` parameter, and there is no heap, aliasing, or permission system to
    subvert. There is no read-only input to overwrite, so the class is vacuous.
    No substitute probe is fabricated (see footer).
  * OWN-DECLARED-SIGNATURE FREE-FIELD rivals — COLLAPSED. The nagini spec split
    the reported signature (via a ``wrapped`` flag and a ``reported_signature``
    resolver over a separate ``target_sig`` field) from the proxy's OWN declared
    signature, and carried rivals against each internal field
    (``weak-own-sig-source``, ``weak-own-sig-arbitrary``). This carrier models
    ONLY the three OBSERVED fields (mapping.md §2): there is no ``wrapped`` flag,
    no ``target_sig``, and no separate own-declared signature — the single
    observable ``CallableMeta.sig`` IS what introspection reports. A rival that
    sets a field nothing observes is unexpressible here, and one that sets the
    OBSERVED sig to an arbitrary constant is exactly ``rival-arbitrary-sig``
    below. So these collapse onto the observable ``sig`` clause C3.
  * CONDITIONAL-RECORD — EXPRESSIBLE, and SHIPPED as
    ``rival-conditional-sig-propagation``. An earlier revision of this file
    folded the nagini ``weak-conditional-record`` into the COLLAPSED bucket above
    on the argument that this carrier has no ``wrapped`` flag for a conditional
    to abuse. That argument was wrong: what the nagini rival tests is the CONTROL
    SHAPE — propagation restricted to a sub-domain of sources — not the flag it
    happens to guard, and a guard over the observed ``sig`` expresses it directly
    here. It is the one rival shape the four straight-line record-build rivals
    cannot make, so it is now carried rather than dropped.
  * ALIASING / RETURN-THE-SOURCE — NOT WRONG on this carrier. The nagini
    ``weak-return-source`` rival returns the source itself and is rejected by the
    distinctness clause ``Result() is not source``. This carrier models a callable
    only through its three observed fields; object identity is neither modeled nor
    observed by the failing test, and a wrapper that presents the target's name,
    documentation, and signature IS introspection-faithful. ``return target``
    therefore satisfies all three ``ensures`` and correctly verifies — it is not a
    wrong implementation of the MODELED behaviour, so it is dropped, not shipped as
    a reject case (see footer).
  * PARTIAL-DOMAIN / VALUE — the reject surface here, spread across C1/C2/C3. A
    rival can leave one observed field un-propagated (the forwarder's own value
    survives), pin a field to an arbitrary constant (correct only on the sub-domain
    where the target happens to carry that constant), or cross-wire two fields
    (correct only where the two target fields coincide).
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line a single ``return`` over immutable values, no loop
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

WITNESS MECHANICS. The postcondition of this method is DECIDABLE — all three
clauses are ``String``/structure equalities over the transparent ``CallableMeta``
carrier, with no opaque callee (the ``axioms`` region is empty; ``propagate`` is a
transparent ``def``). So Velvet's tester machinery reaches the post-image
directly: ``extract_program_for`` / ``derive_tester_for`` yield
``buildForwarderMetaTester``, and every rival is loop-free, so its extracted
program reduces fully under ``decide`` at a concrete input. Each witness states,
at one concrete ``(forwarder, target)`` pair,

    buildForwarderMetaTester <forwarder> <target> = false

i.e. the rival's extracted program violates the method's postcondition at that
input — a direct clause violation the elaborator decides. Against the FROZEN
solution the same statement FAILS: gold satisfies the postcondition at every
input, so ``buildForwarderMetaTester <fwd> <tgt>`` is ``true`` there and ``decide``
cannot prove it ``= false`` — exactly the discrimination the gate requires. No
witness binds a hypothesis (every input is a concrete literal that decides the
clause), so no consistency probe is needed. No banned token (sorry / admit /
native_decide / axiom / opaque). Each witness was checked out-of-band with
scripts/lean_verify.sh: every one ELABORATES against its rival (exit 0) and FAILS
against gold (a ``decide`` error).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the introspection facility; the changed
behaviour is modeled DEEPLY here (no consumed ``axiom``), its soundness against
the real facility is G-AX's job (axiom_check.py / mapping.md), and the G-PBT gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15731"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body, everything strictly
# ---- BETWEEN the method's `-- impl-start` / `-- impl-end` markers. Every
# ---- variant replaces exactly this text, so each edit lies wholly inside the
# ---- one impl region and same_spec holds by construction (both facts asserted
# ---- at load by _swap). The frozen proof block is left untouched by every case:
# ---- both positives verify under the frozen `loom_solve <;> simp [propagate]`
# ---- as-is (measured, exit 0), and every rival's rejection is carried by its
# ---- WITNESS, not by the tactic script failing — which matters because on this
# ---- backend a merely reshaped CORRECT impl can also break the frozen script
# ---- (audit-measured: a guarded-but-observationally-gold reshape needs
# ---- `split` added to close). So "did not build" is never the evidence here.
_IMPL = (
    "    -- Propagate the full introspectable metadata of `target` onto the wrapper:\n"
    "    -- name, documentation, AND call signature (so introspection resolves through\n"
    "    -- to the target). `propagate` is the deep model of the standard facility.\n"
    "    return propagate forwarder target"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `buildForwarderMetaTester forwarder target = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. Every argument is a concrete literal
# ---- so `decide` reduces the (loop-free) extracted rival program without getting
# ---- stuck; against gold the same `decide` cannot prove `= false` and FAILS.
_M = "buildForwarderMeta"
_TESTER = (
    f"extract_program_for {_M}\n"
    f"prove_precondition_decidable_for {_M}\n"
    f"prove_postcondition_decidable_for {_M}\n"
    f"derive_tester_for {_M}\n\n"
)


def _meta(name, doc, sig):
    """A concrete CallableMeta literal for a witness input point."""
    return '{ name := "%s", doc := "%s", sig := "%s" }' % (name, doc, sig)


def _witness(forwarder, target):
    return _TESTER + (
        f"example : {_M}Tester ({forwarder}) ({target}) = false := by\n"
        "  decide\n"
    )


# A forwarder standing for the raw proxy: its own name is the generic inner
# callable name, its doc is empty, and its call signature is the generic
# variadic forwarding form — none of which must survive onto the result.
_FWD = _meta("manager_method", "", "(*args, **kwargs)")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen `return propagate …` code shape).
    # =====================================================================
    {
        "id": "pos-inline-record-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the result record inline (bypassing the pure helper) with
        # its three fields written in a DIFFERENT textual order. Same value flow —
        # every observed field is taken from `target` — so all three ensures
        # discharge and the frozen proof closes as-is. The postcondition pins
        # values, not field-write order, so rejecting this would be SPEC-TOO-STRONG.
        "module": _impl(
            "    return { sig := target.sig, name := target.name, doc := target.doc }"),
        "rationale": (
            "a correct impl that builds the result inline with reordered fields "
            "(same value flow: every observed field taken from `target`) must "
            "verify; C1/C2/C3 pin values, not statement order, so rejecting it "
            "would be SPEC-TOO-STRONG. Ports the nagini pos-control-reordered "
            "(straight-line reorder of the metadata assignments)."),
    },
    {
        "id": "pos-let-bind-result",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: stage the result in a typed local `out` before returning it.
        # Different control shape, identical value flow; the frozen proof closes
        # unchanged. A correct reshape must verify.
        "module": _impl(
            "    let out : CallableMeta := "
            "{ name := target.name, doc := target.doc, sig := target.sig }\n"
            "    return out"),
        "rationale": (
            "a correct impl with a different control shape (stage the result in a "
            "typed local before returning it) must verify; the value flow is "
            "unchanged so all three ensures discharge and the frozen proof closes "
            "as-is. Ports the nagini renamed-local reshape intent: else "
            "SPEC-TOO-STRONG (over-fit to the inline-return code form)."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-selfcall. That case
    # established the read-only fractional-permission precondition
    # (Acc(source.{name,doc,sig},1/2)) admits a normal F2P-shaped input. This
    # method carries NO `require` clause (the pre-conditions region is empty), so
    # nothing could exclude a normal input and the classic "a normal input is
    # admitted" probe is vacuous on this carrier. Re-aimed at the residual
    # admissibility risk on a total domain: that the three-clause post-image is
    # jointly SATISFIABLE by a gold-shaped computation. The frozen impl
    # discharging all three ensures IS that witness. MUST verify, else
    # SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the method carries no `require`, so the builder is total over every "
            "(forwarder, target) pair; the gold impl discharging all three ensures "
            "is the admissibility witness that the post-image (C1 name, C2 doc, C3 "
            "sig, all pinned to `target`) is jointly satisfiable. Near-trivial "
            "precisely because the precondition is empty. Re-aimed from the nagini "
            "admiss-selfcall, whose read-only fractional-permission half has no "
            "counterpart on this referentially-transparent carrier. Else "
            "SPEC-UNSATISFIABLE."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the argument that its faithful real counterpart would
    # NOT resolve. The two structure binders (forwarder, target) are varied
    # across the witnesses; every one of the three independent clauses (C1 name,
    # C2 doc, C3 sig) is attacked.
    # =====================================================================
    {
        "id": "rival-drop-sig-propagation",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour: propagate the name and documentation but leave
        # the wrapper's OWN generic forwarding signature in place (take sig from
        # the forwarder, not the target). This is the single behavioural defect the
        # failing test observes.
        "module": _impl(
            "    return { name := target.name, doc := target.doc, sig := forwarder.sig }"),
        "refinement": (
            "this is the pre-change builder: it propagates the name and "
            "documentation but leaves the wrapper's own generic forwarding "
            "signature in place, so introspecting the wrapper's call signature "
            "reports the generic variadic form instead of the target's parameter "
            "list. Its faithful real patch is the unpatched builder, whose wrapper "
            "renders the generic signature; the failing test pins the wrapper's "
            "rendered signature to the target's, which the generic form is not, so "
            "it would NOT resolve. This is the exact defect the fix corrects."),
        "rationale": (
            "REJECT from C3 (`out.sig = target.sig`): C3 pins the result's call "
            "signature to the TARGET's, so a rival that keeps the forwarder's own "
            "generic signature diverges from the post-image whenever the target's "
            "signature differs from the forwarding form. Refuted at a target whose "
            "sig differs from the forwarder's. If it verified => SPEC-TOO-WEAK "
            "(admits the bug)."),
        "witness": _witness(_FWD, _meta("bulk_create", "d", "(objs)")),
    },
    {
        "id": "rival-arbitrary-sig",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on C3: pin the result's call signature to an arbitrary
        # constant. Correct ONLY on the sub-domain where the target happens to
        # carry exactly that signature; wrong for every other target. Shows C3
        # pins the EXACT target signature, not merely "differs from the generic
        # forwarding form".
        "module": _impl(
            "    return { name := target.name, doc := target.doc, sig := \"(a, b)\" }"),
        "refinement": (
            "a builder that renders some fixed unrelated signature for the wrapper "
            "regardless of the target diverges from the modeled behaviour (the "
            "wrapper must present the TARGET's signature); the failing test pins "
            "the wrapper's rendered signature to the target's, so on every target "
            "whose signature is not that fixed constant it would NOT resolve. A "
            "partial-domain break — correct only where the target's signature "
            "coincides with the constant. Ports the nagini weak-wrapped-wrong-"
            "target / weak-own-sig-arbitrary intent (recording a wrong/arbitrary "
            "signature) onto the single observed sig field."),
        "rationale": (
            "REJECT from C3 (`out.sig = target.sig`): a fixed constant signature "
            "equals `target.sig` only on the sub-domain where the target carries "
            "that exact signature. Refuted at a target whose sig is neither the "
            "forwarding form nor the constant — a DISTINCT input point from "
            "rival-drop-sig-propagation, so the battery varies the sig binder. If "
            "it verified => SPEC-TOO-WEAK (domain-incomplete)."),
        "witness": _witness(_meta("mm", "x", "(*a)"),
                            _meta("count", "c", "(self)")),
    },
    {
        "id": "rival-name-doc-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain on C1: cross-wire the name from the target's
        # documentation. Signature and documentation handled correctly; the
        # wrapper's introspected name is the target's DOC. Correct ONLY on the
        # sub-domain where the target's name and documentation coincide.
        "module": _impl(
            "    return { name := target.doc, doc := target.doc, sig := target.sig }"),
        "refinement": (
            "the wrapper's introspected name would be the target's documentation "
            "string rather than its name; the change's added attributes test "
            "asserts the wrapper's introspected name equals the target's name, and "
            "on every target whose name and documentation differ this cross-wiring "
            "reports the wrong name, so a faithful patch of this shape is not the "
            "modeled change. A genuine partial-domain break — correct only where "
            "the target's name and documentation coincide. Ports the nagini "
            "weak-name-doc-swap."),
        "rationale": (
            "REJECT from C1 (`out.name = target.name`): C1 pins the result's name "
            "to the target's, so copying the target's doc into the name diverges "
            "whenever the target's name and doc differ. Refuted at a target with "
            "distinct name and doc — a distinct input point varying the target "
            "binder. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(_FWD, _meta("get", "g", "(pk)")),
    },
    {
        "id": "rival-drop-doc-propagation",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C2 specifically: propagate name and signature correctly but leave
        # the forwarder's own (empty) documentation in place. ADDED — the nagini
        # sibling leans on its @Pure oracle to catch a dropped doc implicitly;
        # here it is a concrete witnessable C2 divergence, so every one of the
        # three independent clauses is attacked by some rival.
        "module": _impl(
            "    return { name := target.name, doc := forwarder.doc, sig := target.sig }"),
        "refinement": (
            "the wrapper would keep the raw proxy's own (empty) documentation "
            "instead of the target's; the change's added attributes test asserts "
            "the wrapper's introspected documentation equals the target's, so on "
            "every target carrying a real documentation string this leaves the "
            "wrong documentation and a faithful patch of this shape is not the "
            "modeled change. It would NOT resolve. Covers the C2 clause the other "
            "rivals leave correct."),
        "rationale": (
            "REJECT from C2 (`out.doc = target.doc`): C2 pins the result's "
            "documentation to the target's, so keeping the forwarder's own "
            "documentation diverges whenever the target's documentation differs "
            "from the forwarder's. Refuted at a forwarder with empty doc and a "
            "target with a non-empty doc — the C2 clause no other rival attacks, "
            "varying the doc binder. If it verified => SPEC-TOO-WEAK."),
        "witness": _witness(_FWD, _meta("count", "c", "(self)")),
    },
    {
        "id": "rival-conditional-sig-propagation",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL-FLOW / sub-domain restriction on C3. Every field is propagated
        # correctly EXCEPT that the signature propagation is applied only on the
        # sub-domain where the target's rendered signature is non-empty; on the
        # complement the wrapper keeps its own generic forwarding signature. Both
        # branches individually look like propagation, so this is not a dropped
        # clause but a GUARDED one — a shape none of the other rivals has (they
        # are all unconditional straight-line record builds).
        #
        # AUDIT NOTE. An earlier revision of this file recorded the nagini
        # `weak-conditional-record` as COLLAPSED, on the argument that this
        # carrier has no `wrapped` flag for a conditional to abuse. That argument
        # is WRONG, and this case is the correction: what the nagini rival really
        # tests is not the flag but the CONTROL SHAPE — propagation restricted to
        # a sub-domain of targets — and a guard over the observed `sig` field
        # expresses exactly that here. Machine-checked: the frozen spec rejects
        # this rival at the C3 goal (the residual obligation is precisely the
        # guarded implication `target.sig = "" -> forwarder.sig = target.sig`,
        # i.e. the spec demands propagation on the branch this rival skips), and
        # the witness discriminates against gold semantically.
        "module": _impl(
            "    return { name := target.name, doc := target.doc,\n"
            "             sig := (if target.sig = \"\" then forwarder.sig "
            "else target.sig) }"),
        "refinement": (
            "a builder that confers the target's introspectable identity only on "
            "the targets whose rendered call signature is non-empty, and leaves "
            "the wrapper's own generic forwarding signature in place otherwise, "
            "diverges from the modeled behaviour: the propagation is "
            "UNCONDITIONAL — every proxied callable is made introspection-"
            "faithful, not just those in some sub-domain. The failing test pins "
            "the wrapper's rendered signature to the target's, so on any target "
            "falling in the skipped sub-domain a faithful patch of this shape "
            "reports the generic forwarding form and would NOT resolve. Ports "
            "the nagini weak-conditional-record intent (recording applied only "
            "on a sub-domain of sources) onto the single observed sig field."),
        "rationale": (
            "REJECT from C3 (`out.sig = target.sig`): C3 is a TOP-LEVEL clause "
            "over the whole (total) domain, so a guarded propagation leaves the "
            "residual obligation `target.sig = \"\" -> forwarder.sig = "
            "target.sig`, false for a forwarder whose own signature differs. "
            "Refuted at a target in the skipped sub-domain — a FIFTH distinct "
            "input point, and the only witness whose target.sig is empty, so it "
            "varies the sig binder into a region no other case reaches. This is "
            "the CONTROL-SHAPE attack the four unconditional rivals cannot make: "
            "if it verified => SPEC-TOO-WEAK (the spec would admit propagation "
            "restricted to a sub-domain of targets)."),
        "witness": _witness(_meta("mm", "x", "(*a)"), _meta("count", "c", "")),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling contracts `build_proxy(source) -> Func` over a five-field
# `Func` carrier under fractional-permission framing, with the reported signature
# resolved through a `wrapped` flag + `target_sig` field + a `reported_signature`
# @Pure axiom, and the proxy's OWN declared signature (`Func.sig`) modeled
# separately from what introspection reports. This bundle contracts the SAME
# behaviour as `buildForwarderMeta(forwarder, target)` over a THREE-field
# `CallableMeta` carrier (name, doc, sig — the only observed fields; mapping.md
# §2), referentially transparent, no `mut`, no heap, and NO `wrapped`/`target_sig`
# indirection: the single observable `sig` IS what introspection reports.
#
#   nagini case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-reordered       -> pos-inline-record-reordered      PORTED
#   admiss-selfcall             -> admiss-gold-total                RE-AIMED
#   frame-mutate-source-name    -> (none)                           VACUOUS
#   frame-mutate-source-sig     -> (none)                           VACUOUS
#   weak-prefix-no-record       -> rival-drop-sig-propagation       PORTED
#   weak-wrapped-wrong-target   -> rival-drop-sig-propagation       MERGED (C3)
#                                  (+ rival-arbitrary-sig, the partial-domain form)
#   weak-name-doc-swap          -> rival-name-doc-swap              PORTED
#   weak-own-sig-source         -> (none)                           COLLAPSED
#   weak-own-sig-arbitrary      -> rival-arbitrary-sig              RE-EXPRESSED
#   weak-conditional-record     -> rival-conditional-sig-propagation PORTED
#                                  (was COLLAPSED; corrected by audit)
#   weak-return-source          -> (none)                           NOT-WRONG (dropped)
#   (no sibling)                -> pos-let-bind-result              ADDED
#   (no sibling)                -> rival-drop-doc-propagation       ADDED
#   AXIOM_TESTS (2)             -> (none)                           DROPPED (G-AX lane)
#
# 8 velvet SPEC cases: 2 soundness, 1 admissibility, 5 uniqueness (3 attack C3
# sig — two unconditional, one GUARDED — 1 attacks C1 name, 1 attacks C2 doc; so
# every independent clause is attacked, and the sig clause is attacked in both
# the straight-line and the sub-domain-restricted control shape).
#
# PORTED (pos-inline-record-reordered): the nagini pos-control-reordered reorders
#   the straight-line metadata assignments of a correct impl. Here the correct
#   impl is a single record build; the reshape reorders its fields (same value
#   flow) — a structurally-different-but-correct impl over this carrier.
# ADDED (pos-let-bind-result): a second correct reshape (stage the result in a
#   typed local) so the positive lane exercises two distinct correct code shapes,
#   both verifying under the frozen proof.
# RE-AIMED (admiss-selfcall -> admiss-gold-total): the nagini case establishes the
#   read-only fractional-permission precondition on an F2P-shaped input via a
#   self-call. This method has no `require` and no heap permission, so that probe
#   is vacuous; re-aimed at the residual total-domain risk (three-clause post-image
#   joint satisfiability), witnessed by the frozen impl discharging all three
#   ensures.
# PORTED / MERGED / RE-EXPRESSED (the sig clause C3): the nagini
#   weak-prefix-no-record (pre-fix: name/doc only, reported signature is the
#   forwarding form) is the primary rival here — rival-drop-sig-propagation, the
#   exact defect the failing test observes. nagini's weak-wrapped-wrong-target
#   (record the forwarding sig as the "original") produced the SAME observable on
#   this carrier (reported sig = forwarding form), so it MERGES into that rival;
#   nagini's weak-own-sig-arbitrary (arbitrary own-signature code) RE-EXPRESSES as
#   rival-arbitrary-sig — a fixed constant reported signature, the partial-domain
#   form correct only where the target carries that constant.
# PORTED (rival-name-doc-swap): the nagini weak-name-doc-swap (copy doc into the
#   name) carries across intact onto the C1 name clause — correct only where the
#   target's name and doc coincide.
# ADDED (rival-drop-doc-propagation): the velvet spec pins documentation as an
#   INDEPENDENT clause C2; the nagini file caught a dropped doc only implicitly via
#   its @Pure oracle. This rival attacks C2 directly (name/sig correct, forwarder's
#   own empty doc kept), so all three independent clauses are attacked. A real
#   divergence with a machine-checked witness, not fabricated wrongness.
# COLLAPSED (weak-own-sig-source): the nagini spec models the proxy's OWN declared
#   signature (`Func.sig`) separately from the reported signature, and this rival
#   abuses that internal field. This carrier models ONLY the observed fields
#   (mapping.md §2): there is no own-declared signature distinct from the reported
#   one, so the rival has no distinct field to abuse. Setting the OBSERVED sig to
#   the source's is what GOLD does (and correctly verifies); setting it to an
#   arbitrary constant is rival-arbitrary-sig. Not fabricated as a separate case.
# PORTED, AUDIT-CORRECTED (weak-conditional-record -> rival-conditional-sig-
#   propagation): previously recorded here as COLLAPSED, on the argument that this
#   carrier has no `wrapped` flag for a conditional to abuse. That reason was
#   wrong. The nagini rival's content is the CONTROL SHAPE — the recording applied
#   only on the sub-domain where the source's signature differs from the
#   forwarding form — and that shape transliterates directly onto the observed
#   `sig` field as a guarded propagation, with no need for a flag. It is now
#   carried as a real reject case: the frozen spec rejects it at the C3 goal with
#   the residual obligation `target.sig = "" -> forwarder.sig = target.sig`
#   (i.e. C3 demands propagation on precisely the branch the rival skips), and its
#   witness elaborates against the rival and is refuted against gold by `decide`.
#   It is the only rival here whose impl is not a straight-line record build, so
#   it covers a control shape the other four cannot reach.
# NOT-WRONG / DROPPED (weak-return-source): the nagini rival returns the source
#   itself and is rejected by the distinctness clause `Result() is not source`.
#   This carrier models a callable only through its three observed fields; object
#   identity is neither modeled nor observed by the failing test, and a wrapper
#   presenting the target's name, doc, and signature IS introspection-faithful. So
#   `return target` satisfies all three ensures and correctly VERIFIES — it is not
#   a wrong implementation of the MODELED behaviour (its abstraction collapses the
#   identity distinction nagini's five-field carrier kept), so no reject case is
#   shipped for it. Confirmed with scripts/lean_verify.sh: `return target` verifies.
#   This is genuine carrier narrowing, NOT a spec hole: the F2P observable is the
#   rendered signature, which `return target` gets right.
# VACUOUS (frame-mutate-source-name, frame-mutate-source-sig): the nagini rivals
#   write through the half-permission source to satisfy the postcondition vacuously
#   and are rejected for insufficient permission. This backend is referentially
#   transparent and the method declares NO `mut` binder, so there is no read-only
#   input to overwrite and no substitute probe to build. Not fabricated.
# DIVERGENCE: no case shipped, and closed by the verifier rather than vacuous. The
#   nagini sibling carries no diverge-*/nonterm-*/weak-diverge case, so there is
#   nothing to port; the frozen impl and every rival THIS battery ships are
#   loop-free straight-line returns, so no divergence rival is written here. The
#   "even under `partial`" aside is withdrawn: no velvet bundle sets `partial` (all
#   500 set "total" and open `TotalCorrectness`), and a rival owning the whole impl
#   region could splice a loop that the frozen body lacks. Under `total` such a
#   loop owes a decreasing measure AND its descent, so it is rejected. No reject
#   case written, none claimed dropped.
# DROPPED (AXIOM_TESTS): the nagini file's axiom-soundness/containment probes over
#   the introspection facility are G-AX's job (axiom_check.py / mapping.md); the
#   changed behaviour is modeled deeply (no consumed `axiom` in the bundle) and the
#   G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The three independent top-level clauses are
#   C1 (`out.name = target.name`), C2 (`out.doc = target.doc`), C3 (`out.sig =
#   target.sig`). Each is attacked: C3 by rival-drop-sig-propagation (the pre-fix
#   defect, tied to the graded failing test) and rival-arbitrary-sig (partial-
#   domain constant); C1 by rival-name-doc-swap; C2 by rival-drop-doc-propagation.
#   All three clauses are defended by both positives and the admissibility case
#   (all three discharge on gold). The two structure binders are varied across the
#   witnesses: the `target` binder takes FIVE DISTINCT values — {bulk_create, d,
#   (objs)}, {count, c, (self)}, {get, g, (pk)}, a second {count, c, (self)} with a
#   distinct forwarder, and {count, c, ""} (the empty rendered signature, reached
#   only by the conditional rival) — and the `forwarder` binder is varied too (two
#   witnesses use {mm, x, (*a)} rather than the generic proxy). No binder field is
#   held fixed by every witness: target.name, target.doc, and target.sig each vary,
#   so a rival mishandling any single target field would be caught. pts = 5
#   distinct input points.
#
# AUDIT-MEASURED SPEC STRENGTH / WEAKNESS BOUNDS (attacks D and E; exit codes from
#   scripts/lean_verify.sh). Six FURTHER wrong impls beyond the shipped rivals were
#   built against the frozen spec and every one was REJECTED (exit 1), so no spec
#   hole was found on this surface: keep the forwarder's own name (C1); take sig
#   from target.name (a same-carrier cross-wire); return `forwarder` outright;
#   truncate the target's sig by one character (a NEAR-MISS on C3 — the spec pins
#   the exact string, not a prefix relation); guard the sig propagation on the
#   empty-signature sub-domain (now shipped as rival-conditional-sig-propagation);
#   and return `forwarder` on the sub-domain where the two signatures agree.
#   The last two are the informative ones: both are rejected with the residual
#   guarded goal shown, which is what confirms C3 is a total-domain obligation and
#   not satisfiable branch-wise.
# On the SOUNDNESS side, three further CORRECT reshapes were built and all VERIFY
#   (exit 0) under the frozen tactic unchanged: `return target`, `return propagate
#   target target`, and a `{ forwarder with ... }` record update overriding all
#   three fields. A fourth correct reshape — the guarded form that takes the sig
#   from `forwarder` only on the branch where the two signatures are EQUAL, hence
#   observationally gold — does NOT close under the frozen `loom_solve <;> simp
#   [propagate]` (the `if` blocks the simp), but DOES verify once the tactic is
#   retuned to `loom_solve <;> split <;> simp_all [propagate]` (exit 0). That is a
#   TACTIC-shape limit, not a spec one: the spec admits the reshape, so there is no
#   SPEC-TOO-STRONG finding. It is recorded here because the distinction is exactly
#   what a reject case must not be built on — and it is why the guarded REJECT case
#   above is justified by its witness rather than by its build failure.
#
# WITNESS MECHANICS: the postcondition is DECIDABLE (three String/structure
#   equalities over the transparent CallableMeta carrier; empty axioms region;
#   propagate is a transparent def), so the tester+`decide` path is LIVE here —
#   `derive_tester_for` yields a computable `buildForwarderMetaTester` and each
#   loop-free rival's extracted program reduces under `decide` at a concrete input,
#   deciding `…Tester fwd tgt = false`. Against gold the same `decide` cannot prove
#   `= false` (gold satisfies the postcondition everywhere) and FAILS — so the same
#   witness elaborates against the rival and fails against gold. No witness binds a
#   hypothesis, so no consistency probe is needed. All FIVE checked with
#   scripts/lean_verify.sh: rival exit 0, gold exit 1 — and the gold-side failure
#   is a SEMANTIC refutation in every case, `Tactic 'decide' proved that the
#   proposition ...Tester <fwd> <tgt> = false is false`, i.e. the kernel evaluated
#   the tester on gold, got `true`, and rejected the claim. Not a missing
#   identifier, not a type error, not a stuck/irreducible term, not a timeout —
#   the failure modes that would make an exit code attest to nothing.
AXIOM_TESTS = []
