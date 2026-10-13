"""properties.py — G-PBT falsification battery for django__django-15731 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for the
admissibility case, inside ``-- proof-start`` / ``-- proof-end`` — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_delegateMetadata``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide``, no new ``axiom``/``theorem``); ``expect:"reject"`` passes iff
(in scope AND it does NOT verify AND the case's refutation ``witness`` holds of
the rival while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a fresh authoring:
the nagini sibling is the design document and its per-case ``rationale`` /
``refinement`` arguments are what carry over. The mechanics do not. The nagini
bundle models the construction as a HEAP operation — a mutable five-field
``Func`` object built under fractional permissions, with the reported call
signature resolved indirectly through a ``wrapped`` boolean plus a separate
recorded-signature field and a ``@Pure`` resolver oracle, and with the produced
object's OWN declared signature modeled as a field distinct from what
introspection reports. This bundle models the SAME behaviour as a pure function
``delegateMetadata (underlying rawDelegate : MethodMetadata) : MethodMetadata``
over a SIX-field transparent record: referentially transparent, no heap, no
aliasing, no permission system, and no ``wrapped``/recorded-signature
indirection — each of the six fields IS an observable, and the reported call
signature is one of them directly. So the nagini heap/permission class is
vacuous here while the observable surface is WIDER (six pinned attributes rather
than nagini's name/doc plus a resolved signature), which is where the added
rivals come from. Full case-by-case accounting in the footer.

DEFENDED SURFACE (one obligation; six independent top-level clauses).
``problem_spec_delegateMetadata underlying rawDelegate result`` is a conjunction
pinning EVERY observable introspection attribute of the produced delegating
method to the underlying method's corresponding attribute:

  * C1 ``result.name = underlying.name``
  * C2 ``result.qualname = underlying.qualname``
  * C3 ``result.module = underlying.module``
  * C4 ``result.doc = underlying.doc``
  * C5 ``result.annotations = underlying.annotations``
  * C6 ``result.signature = underlying.signature``

The six are INDEPENDENT conjuncts — no clause implies another — so each admits
its own rival, and every one is attacked below. There is no precondition: the
obligation is ``∀ (underlying rawDelegate : MethodMetadata), …``, so the admitted
domain is total and every metadata pair is in scope.

WHICH CLAUSE CARRIES THE GRADED FAILING TEST. C6 (the rendered call signature) is
load-bearing for the FAIL_TO_PASS observable: the bare forwarding wrapper's
intrinsic signature is the generic catch-all that accepts arbitrary arguments,
and the failing test pins the delegating method's rendered parameter list to the
underlying method's real one — which the catch-all is not. C1 and C4 are pinned
because the change ships an accompanying attributes assertion on the produced
method's reported name and documentation (PASS_TO_PASS). C2/C3/C5 are pinned
because the modeled propagation is the FULL introspectable-metadata bundle
(mapping.md): a construction that leaves any one of them at the bare wrapper's
placeholder is not the modeled behaviour. Every clause is DEFENDED (the three
positives + the admissibility case discharge all six, and one of the positives is
not definitionally equal to the frozen impl, so it re-proves all six rather than
re-spelling the frozen proof) and ATTACKED (a rival per clause, plus a second
rival on C6 and a control-flow rival that abandons a sub-domain of all six at
once).

BINDER STRUCTURE AND POINT SPREAD. The spec predicate has TWO input binders,
``underlying`` and ``rawDelegate``, each a six-field record — so 12 input
components in total. Both binders are varied across the nine reject witnesses,
and no component is held at one value by all of them: each witness uses a
DISTINCT ``underlying`` record and a DISTINCT ``rawDelegate`` record, so a rival
mishandling any single field would be caught by the witness that moves it. This
matters most for ``rawDelegate``: it is the binder the wrong implementations read
FROM (a dropped propagation leaves the bare wrapper's own value in place), so a
battery that pinned it to one record would not demonstrate that the spec depends
on it at all. ``pts = 9`` distinct input pairs. Two deliberate near-miss
placements: the C6 ``weak-signature-generic`` witness uses an ``underlying``
whose signature differs from the wrapper's while its other five fields COINCIDE
with the wrapper's, isolating the signature clause; and the
``weak-conditional-propagate`` witness sits at the one sub-domain that rival
abandons — an ``underlying`` whose own parameter list happens to coincide with
the generic catch-all — which no other witness probes.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's two MANDATORY
    rivals write through a half-permission reference to the source (overwriting
    its reported name, and forcing its recorded signature to the forwarding
    value so an unrecorded wrapper would satisfy the resolver clause vacuously);
    both are rejected for INSUFFICIENT PERMISSION rather than by a postcondition.
    Here ``underlying`` and ``rawDelegate`` are immutable values, the obligation
    binds no mutable parameter, and there is no heap, aliasing, or permission
    fraction to subvert — there is no read-only cell to overwrite, so the class
    is vacuous and no substitute probe is fabricated.

  * ALIASING / RETURN-THE-SOURCE — NOT WRONG here, dropped. See the footer: the
    nagini distinctness clause has no counterpart because object identity is not
    modeled, and returning the underlying metadata unchanged satisfies all six
    clauses. It is a correct implementation of the MODELED behaviour, so shipping
    it as a reject case would be fabricated wrongness.

  * ORACLE-ECHO — VACUOUS. The postcondition is GROUNDED in the inputs: each
    clause equates a result field to an ``underlying`` field. There is no opaque
    callee and no answer key to echo (the axioms region is empty), so producing
    each field from the input IS doing the work. In its place the battery ships
    honest positive controls that must verify.

  * PARTIAL-DOMAIN / VALUE — the reject surface here, and the one that widens.
    A rival can leave one attribute un-propagated (the bare wrapper's own value
    survives — correct only where the two inputs coincide on that field), pin an
    attribute to an arbitrary constant (correct only on the sub-domain where the
    underlying method carries that constant), cross-wire two attributes (correct
    only where those two underlying fields coincide), or propagate the whole
    bundle only on a SUB-DOMAIN of inputs.

  * DIVERGENCE — genuinely VACUOUS on this backend, and not a spec hole. The
    nagini sibling carries no ``diverge-*`` / ``nonterm-*`` / ``weak-diverge``
    case, so there is nothing to port; and independently ``implementation_*`` is a
    total Lean ``def``, so a non-terminating implementation cannot be written at
    all — unlike the velvet ``partial``-semantics hole of
    ``the corpus-wide termination-semantics finding``, where a diverging impl would satisfy every
    clause vacuously. No reject case is written for it and none is claimed
    dropped.

WITNESS MECHANICS. On a tactic-proof backend "did not verify" is the DEFAULT
outcome of reshaping an implementation — the frozen script
(``simp only [Id.run]; refine ⟨rfl, …⟩``) is tuned to the frozen impl's form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a witness that states the spec predicate's NEGATION directly at
one concrete input pair,

    example : ¬ problem_spec_delegateMetadata <underlying> <rawDelegate>
                 (implementation_delegateMetadata <underlying> <rawDelegate>) := by
      unfold problem_spec_delegateMetadata implementation_delegateMetadata
      decide

checked in a file whose ``proof`` region has been emptied, so no tactic script can
mask the verdict. The carrier is fully transparent (six ``String`` fields,
``deriving DecidableEq``, no opaque callee), so ``decide`` reduces the conjunction
at ground literals and needs no conditioning on the carrier: every witness binds
NOTHING in its head, hence there are no hypotheses whose joint satisfiability
could be in question and no consistency probe is needed. Each witness was checked
out-of-band with two real ``scripts/lean_verify.sh`` builds: it ELABORATES against
its rival (exit 0) and FAILS against the frozen solution — and the gold-side
failure is ``Tactic 'decide' proved that the proposition … is false``, i.e. gold
SATISFIES the spec at that point, so the witness discriminates on the spec rather
than on an incidental elaboration error. No banned token (no ``sorry`` /
``admit`` / ``native_decide`` / ``axiom`` / ``opaque``) appears in any witness.

AXIOM lane: DROPPED. ``AXIOM_TESTS = []``. The nagini file carries an
axiom-soundness probe and a containment probe over its ``@ContractOnly`` resolver
oracle, but this bundle declares no ``opaque`` callee and consumes no ``axiom``
(the changed operation is modeled deeply, so ``meta.json axioms = []`` and G-AX
skips); validating the deep model against the real facility is G-AX's job via
``axiom_check.py`` / ``conformance_check.py``, and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15731"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it names and is unique in
# the frozen file (both asserted at load by `_swap`, so the manifest breaks
# loudly rather than silently mis-editing if the frozen solution ever changes).
# ---------------------------------------------------------------------------

# The whole frozen impl body: everything strictly between `-- impl-start` and
# `-- impl-end` after the `def` header, so every variant's edit lands wholly
# inside the impl region and `same_spec` holds by construction.
_GOLD_IMPL = """  -- Start from the bare forwarding wrapper's intrinsic metadata, then propagate
  -- the underlying method's full introspectable metadata onto it so the produced
  -- method is indistinguishable under inspection.
  let mut md := rawDelegate
  md := { md with
    name := underlying.name,
    qualname := underlying.qualname,
    module := underlying.module,
    doc := underlying.doc,
    annotations := underlying.annotations,
    signature := underlying.signature }
  return md"""

# The whole frozen proof body (inside `-- proof-start` / `-- proof-end`). Only
# the admissibility case touches it, and only to PREPEND a ground `have`; the
# `theorem correct_delegateMetadata` STATEMENT is never edited, so the obligation
# survives byte-identically.
_GOLD_PROOF = """  intro underlying rawDelegate
  unfold problem_spec_delegateMetadata implementation_delegateMetadata
  simp only [Id.run]
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩"""

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted"
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof region drifted"

_FIELDS = ("name", "qualname", "module", "doc", "annotations", "signature")


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _proof(body):
    """Full Solution.lean variant with ONLY the proof tactic body replaced."""
    return _swap(_BASE, _GOLD_PROOF, body)


def _propagate(**overrides):
    """Impl body propagating each field from `underlying`, per `overrides`.

    A field mapped to ``rawDelegate.<f>`` is one the variant leaves at the bare
    wrapper's own intrinsic value; a field omitted from the record update
    entirely likewise keeps the wrapper's value (the accumulator starts there).
    """
    src = {f: f"underlying.{f}" for f in _FIELDS}
    src.update(overrides)
    keep = [f for f in _FIELDS if f in src]
    return ("  let mut md := rawDelegate\n  md := { md with\n"
            + ",\n".join(f"    {f} := {src[f]}" for f in keep)
            + " }\n  return md")


def _only(*fields):
    """Impl body propagating ONLY `fields`; the rest keep the wrapper's value."""
    return ("  let mut md := rawDelegate\n  md := { md with\n"
            + ",\n".join(f"    {f} := underlying.{f}" for f in fields)
            + " }\n  return md")


# ---------------------------------------------------------------------------
# Witness helpers. A concrete `MethodMetadata` literal must stay on ONE line:
# Lean's whitespace sensitivity rejects a structure literal whose continuation
# lines are indented to the left of the enclosing application, and the resulting
# `unexpected identifier; expected '}'` breaks BOTH builds — which the gate would
# record as `witness-unproven` for a witness it never actually tried.
# ---------------------------------------------------------------------------

def _md(name, qualname, module, doc, annotations, signature):
    return ('{ name := "%s", qualname := "%s", module := "%s", doc := "%s", '
            'annotations := "%s", signature := "%s" }'
            % (name, qualname, module, doc, annotations, signature))


def _witness(underlying, raw_delegate):
    """`¬ problem_spec … (implementation …)` at one concrete input pair.

    Binds nothing in its head — every input is a ground literal and the carrier
    is transparent with `DecidableEq`, so `decide` settles the conjunction and no
    hypothesis is needed. Hence no assumption whose consistency could be probed.
    """
    return (
        "example : ¬ problem_spec_delegateMetadata\n"
        f"    {underlying}\n"
        f"    {raw_delegate}\n"
        "    (implementation_delegateMetadata\n"
        f"      {underlying}\n"
        f"      {raw_delegate}) := by\n"
        "  unfold problem_spec_delegateMetadata implementation_delegateMetadata\n"
        "  decide\n"
    )


# A bare forwarding wrapper's intrinsic metadata: its own internal name and
# qualified name, its own defining module, no documentation, no annotations, and
# the generic catch-all call signature that accepts arbitrary arguments. Each
# rival gets its OWN such record (so the `rawDelegate` binder is genuinely
# varied); this is the shape they all instantiate.
_ADM_UNDERLYING = _md("widen", "Outer.widen", "pkg.core",
                      "Widen the span.", "{'n': 'int'}", "(n, step=1)")
_ADM_RAW = _md("inner", "Maker.make.inner", "pkg.build", "", "",
               "(self, *a, **k)")


SPEC_TESTS = [

    # =====================================================================
    # SOUNDNESS — structurally different but CORRECT implementations that MUST
    # verify. Each needs its own closing proof for the NEW impl shape; both
    # shapes below were chosen so the frozen tactic script still discharges
    # them (the value flow is unchanged, so all six conjuncts stay `rfl` after
    # `simp only [Id.run]`), which keeps each case one cheap `lake` build. If a
    # faithful correct impl could not verify, the spec would be SPEC-TOO-STRONG
    # — over-fit to the frozen code shape rather than pinning behaviour.
    # =====================================================================
    {
        "id": "pos-direct-record",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the result record DIRECTLY from the underlying
        # method's metadata in a single expression, never staging the bare
        # wrapper's record in a mutable local at all. Different control shape
        # (no accumulator, no record-update), identical value flow.
        "module": _impl(
            "  -- Build the produced method's metadata directly from the underlying\n"
            "  -- method's, without staging the bare wrapper's record in a local.\n"
            "  return { name := underlying.name, qualname := underlying.qualname,\n"
            "           module := underlying.module, doc := underlying.doc,\n"
            "           annotations := underlying.annotations,\n"
            "           signature := underlying.signature }"),
        "rationale": (
            "a correct impl that constructs the result in one expression instead "
            "of accumulating record updates over a mutable local must verify: "
            "C1-C6 pin VALUES, not the construction shape, and the value flow is "
            "unchanged (every observable attribute still comes from `underlying`). "
            "Defends all six clauses at once. Rejecting it would be "
            "SPEC-TOO-STRONG. Ports the nagini pos-control-reordered, whose "
            "reshape was a reordered straight-line assignment sequence through a "
            "renamed local; on this carrier the correct impl is a record build, "
            "so the analogous reshape is to bypass the accumulator entirely."),
    },
    {
        "id": "pos-stepwise-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: propagate the attributes ONE AT A TIME, in the exact reverse
        # of the frozen order (signature first, reported name last), through six
        # successive record updates instead of one. This is the closest analogue
        # of the nagini reorder: same values, different statement order and a
        # different number of update steps.
        "module": _impl(
            "  -- Propagate the underlying method's attributes one at a time, in the\n"
            "  -- opposite order, through successive updates of the wrapper's record.\n"
            "  let mut md := rawDelegate\n"
            + "".join(f"  md := {{ md with {f} := underlying.{f} }}\n"
                      for f in reversed(_FIELDS))
            + "  return md"),
        "rationale": (
            "a correct impl that reorders the propagation (reverse field order, "
            "six successive single-field updates rather than one combined update) "
            "must verify: the postcondition pins the final values of all six "
            "observables, not the order or granularity of the writes. Directly "
            "ports the nagini pos-control-reordered reorder-the-assignments "
            "intent. Defends all six clauses. Else SPEC-TOO-STRONG."),
    },

    {
        "id": "pos-pointwise-agree",
        "kind": "soundness",
        "expect": "verify",
        # Reshape that is NOT definitionally equal to the frozen impl. The two
        # reshapes above both close under the FROZEN tactic script unchanged,
        # because each is defeq to the frozen value function — `rfl` proves
        # `implementation … u r = { name := u.name, … }` for all three. That
        # makes them honest but cheap: they re-run the frozen proof on a
        # re-spelled term rather than forcing the obligation to be RE-PROVEN.
        # This case closes that gap. It decides each field pointwise ("if the
        # wrapper already agrees, keep its value; else propagate"), which is
        # extensionally the same function — both branches return equal strings —
        # but is NOT defeq: the frozen script's `refine ⟨rfl, …⟩` cannot close
        # it (measured: `Tactic 'rfl' failed`, the `ite` does not reduce at an
        # open `underlying`/`rawDelegate`), so the case must supply its OWN
        # proof, discharging all six clauses by case analysis on each guard.
        # A spec over-fit to the frozen code SHAPE rather than to behaviour
        # would reject this; that it verifies is the real SPEC-TOO-STRONG
        # control the other two positives cannot provide.
        "module": _proof(
            "  intro underlying rawDelegate\n"
            "  unfold problem_spec_delegateMetadata implementation_delegateMetadata\n"
            "  simp only [Id.run, Id.pure_eq]\n"
            "  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;> split_ifs with h <;> simp_all"
        ).replace(_GOLD_IMPL,
            "  -- Decide each observable pointwise: where the bare wrapper already\n"
            "  -- carries the underlying method's value, keep it; otherwise propagate.\n"
            "  -- Extensionally the frozen function, but not definitionally equal to\n"
            "  -- it, so the obligation is genuinely re-proven for this shape.\n"
            "  let mut md := rawDelegate\n"
            "  md := { md with\n"
            + ",\n".join(
                f"    {f} := if underlying.{f} = rawDelegate.{f} then rawDelegate.{f}"
                f"\n           else underlying.{f}" for f in _FIELDS)
            + " }\n  return md", 1),
        "rationale": (
            "a correct impl that is NOT definitionally equal to the frozen one "
            "must still verify. Both other positives are defeq to the frozen "
            "value function (`rfl` closes `implementation … u r = { name := "
            "u.name, … }` for each), so they close under the frozen script "
            "unchanged and never force the obligation to be re-proven. This "
            "reshape decides each field pointwise against the wrapper's own "
            "value: the same function extensionally, but the frozen "
            "`refine ⟨rfl, …⟩` fails on it (the `ite` will not reduce at open "
            "inputs), so all six clauses are re-discharged by case analysis on "
            "the six guards. Defends C1-C6 on a genuinely different proof "
            "obligation. Rejecting it would be SPEC-TOO-STRONG — the spec would "
            "be pinning the frozen CODE SHAPE rather than the behaviour."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-selfcall. That case
    # discharged the nagini precondition (half-permission access to the source's
    # three read fields) by self-calling on a freshly built source, proving the
    # precondition admits a normal input. This obligation has NO precondition —
    # it is `∀ (underlying rawDelegate : MethodMetadata), …`, total over the
    # carrier — so "a normal input is admitted" is vacuous as stated. What
    # remains is the residual risk a total domain still carries: that the
    # six-clause post-image is jointly SATISFIABLE at a realistic input rather
    # than only provable in the abstract. So the case keeps the nagini shape —
    # discharge the spec at a concrete input first, then the general obligation
    # — by prepending a GROUND `have` at a failing-test-shaped point: an
    # underlying method with a real parameter list, documentation, and
    # annotations, against a bare wrapper carrying the generic catch-all
    # signature and no documentation. The `have` must close by `decide` on its
    # own, so the case fails if the six clauses are not jointly satisfiable
    # there. Edits ONLY the proof body; the theorem statement is untouched.
    # =====================================================================
    {
        "id": "admiss-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _proof(
            "  -- The post-image is jointly satisfiable at a concrete input of the\n"
            "  -- shape the graded observable exercises: an underlying method with a\n"
            "  -- real parameter list, documentation and annotations, against a bare\n"
            "  -- wrapper carrying the generic catch-all signature and no docs.\n"
            "  have hpoint : problem_spec_delegateMetadata\n"
            f"      {_ADM_UNDERLYING}\n"
            f"      {_ADM_RAW}\n"
            "      (implementation_delegateMetadata\n"
            f"        {_ADM_UNDERLYING}\n"
            f"        {_ADM_RAW}) := by\n"
            "    unfold problem_spec_delegateMetadata implementation_delegateMetadata\n"
            "    decide\n"
            + _GOLD_PROOF),
        "rationale": (
            "the obligation carries no precondition, so the builder is total over "
            "every metadata pair; what needs discharging is that the six-clause "
            "post-image is jointly satisfiable at a REALISTIC point, not merely in "
            "the abstract. The prepended `have` closes by `decide` at an input of "
            "the graded observable's shape (underlying method's real parameter "
            "list, documentation and annotations vs. the wrapper's generic "
            "catch-all and empty documentation), so the case fails if any clause "
            "conflicts with another there; the general obligation then closes as "
            "before. Re-aimed from the nagini admiss-selfcall, whose "
            "read-only-permission half has no counterpart on a referentially "
            "transparent carrier. Else PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals. Each is a WRONG implementation sharing
    # the frozen spec that MUST be rejected, carrying a machine-checked
    # refutation witness at a concrete input plus the argument that its faithful
    # real counterpart would NOT resolve. Every one of the six independent
    # clauses is attacked, and both input binders are varied across the
    # witnesses.
    # =====================================================================
    {
        "id": "weak-partial-name-doc-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour, and the primary port of the nagini
        # weak-prefix-no-record: propagate ONLY the reported name and the
        # documentation, leaving every other observable — the rendered call
        # signature, the qualified name, the defining module, the annotations —
        # at the bare wrapper's placeholder value.
        "module": _impl(
            "  -- Propagate only the reported name and the documentation; every other\n"
            "  -- observable keeps the bare wrapper's own placeholder value.\n"
            + _only("name", "doc")),
        "refinement": (
            "this is the pre-change construction: it propagates the reported name "
            "and the documentation and leaves every other introspectable "
            "attribute at the bare forwarding wrapper's placeholder, so the "
            "delegating method renders the generic catch-all parameter list "
            "instead of the underlying method's real one. Its faithful real "
            "counterpart is exactly the unpatched construction, and the "
            "FAIL_TO_PASS assertion pins the rendered parameter list of a "
            "delegating method to the underlying method's — which the catch-all "
            "form is not — so it would NOT resolve. This is the exact defect the "
            "change corrects; the bundle's own prepatch variant is this "
            "behaviour."),
        "rationale": (
            "REJECT from C6 (and simultaneously C2/C3/C5): four of the six "
            "conjuncts fail whenever the underlying method's signature, qualified "
            "name, module, or annotations differ from the bare wrapper's. Refuted "
            "at an input where all four differ. If it verified => SPEC-TOO-WEAK "
            "(the spec would admit the very behaviour the change fixes)."),
        "witness": _witness(
            _md("widen", "Outer.widen", "pkg.core", "Widen the span.",
                "{'n': 'int'}", "(n, step=1)"),
            _md("inner", "Maker.make.inner", "pkg.build", "", "",
                "(self, *a, **k)")),
    },
    {
        "id": "weak-signature-generic",
        "kind": "uniqueness",
        "expect": "reject",
        # ISOLATES C6, the graded clause: propagate all five OTHER observables
        # correctly and leave ONLY the rendered call signature at the bare
        # wrapper's generic catch-all. This is the minimal form of the defect —
        # a construction that looks fully faithful under every check except the
        # one the failing test makes.
        "module": _impl(
            "  -- Propagate every observable except the rendered call signature, which\n"
            "  -- keeps the bare wrapper's own generic catch-all form.\n"
            + _propagate(signature="rawDelegate.signature")),
        "refinement": (
            "a construction that mirrors the underlying method on every "
            "introspectable attribute EXCEPT the rendered call signature still "
            "presents the generic catch-all parameter list to inspection. The "
            "accompanying attributes assertion (reported name, documentation) "
            "would pass, so this rival is indistinguishable from the fix under "
            "PASS_TO_PASS, but the FAIL_TO_PASS assertion pins the rendered "
            "parameter list itself and would still fail on every underlying "
            "method whose real parameter list differs from the catch-all form. A "
            "faithful patch of this shape would NOT resolve — it is the residue "
            "of the bug after the attribute-copying half is fixed."),
        "rationale": (
            "REJECT from C6 alone (`result.signature = underlying.signature`): "
            "the other five clauses hold, so this rival isolates the graded "
            "clause. Refuted at a NEAR-MISS input built for it: the underlying "
            "record agrees with the wrapper on all five other fields and differs "
            "ONLY in the signature, so the refutation is attributable to C6 and "
            "to nothing else — a distinct input point from "
            "weak-partial-name-doc-only, which is refuted where four fields "
            "differ. If it verified => SPEC-TOO-WEAK (the spec would not see the "
            "graded observable)."),
        "witness": _witness(
            _md("shrink", "Outer.shrink", "pkg.core", "Shrink it.", "{}",
                "(sel, size=None)"),
            _md("shrink", "Outer.shrink", "pkg.core", "Shrink it.", "{}",
                "(self, *a, **k)")),
    },
    {
        "id": "weak-signature-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on C6: render some fixed unrelated parameter list
        # regardless of the underlying method. Correct ONLY on the sub-domain
        # where the underlying method happens to carry exactly that signature.
        # Re-expresses the nagini weak-wrapped-wrong-target /
        # weak-own-sig-arbitrary pair: those recorded a wrong signature (the
        # forwarding value, or an arbitrary code) as the "original", which on
        # this carrier is simply a wrong value in the one observable field.
        "module": _impl(
            "  -- Render a fixed parameter list regardless of the underlying method.\n"
            + _propagate(signature='"(x, y)"')),
        "refinement": (
            "a construction that renders some fixed unrelated parameter list for "
            "every delegating method diverges from the modeled behaviour, which "
            "renders the UNDERLYING method's own list. The FAIL_TO_PASS assertion "
            "pins the rendered list to the underlying method's real one, so on "
            "every underlying method whose parameter list is not that constant "
            "the assertion fails and a faithful patch of this shape would NOT "
            "resolve. A genuine partial-domain break: correct only where the "
            "underlying method's signature coincides with the constant, which is "
            "a measure-zero sub-domain of the methods being delegated."),
        "rationale": (
            "REJECT from C6 (`result.signature = underlying.signature`): a fixed "
            "constant equals `underlying.signature` only on the sub-domain where "
            "the underlying method carries that exact signature. Refuted at an "
            "input whose signature is NEITHER the catch-all form NOR the constant "
            "— and whose `rawDelegate` carries the constant, so the rival's answer "
            "cannot be excused as the wrapper's own value either. A third distinct "
            "point on the C6 clause, showing C6 pins the exact signature rather "
            "than merely 'differs from the catch-all'. Else SPEC-TOO-WEAK."),
        "witness": _witness(
            _md("tally", "Outer.tally", "pkg.count", "Tally rows.",
                "{'k': 'str'}", "(k, deep=False)"),
            _md("probe", "Maker.probe.inner", "pkg.gen", "", "", "(x, y)")),
    },
    {
        "id": "weak-name-from-doc",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN on C1, cross-wired: the reported name is taken from the
        # underlying method's DOCUMENTATION. Every other observable is handled
        # correctly. Correct only where those two underlying fields coincide.
        # Direct port of the nagini weak-name-doc-swap.
        "module": _impl(
            "  -- Take the reported name from the underlying method's documentation.\n"
            + _propagate(name="underlying.doc")),
        "refinement": (
            "the delegating method's reported name would be the underlying "
            "method's documentation string rather than its name. The change ships "
            "an accompanying PASS_TO_PASS assertion that the delegating method's "
            "reported name equals the underlying method's, and on every "
            "underlying method whose name and documentation differ this "
            "cross-wiring reports the wrong name — so a faithful patch of this "
            "shape is not the modeled change and would NOT resolve. A genuine "
            "partial-domain break: correct only where the underlying method's "
            "name and documentation coincide."),
        "rationale": (
            "REJECT from C1 (`result.name = underlying.name`): copying the "
            "documentation into the reported name diverges whenever the "
            "underlying method's name and documentation differ. Refuted at an "
            "input where they differ; the clause no signature rival touches. "
            "Directly ports the nagini weak-name-doc-swap. Else SPEC-TOO-WEAK."),
        "witness": _witness(
            _md("sift", "Outer.sift", "pkg.text", "Sift.", "{}", "(s, n=1)"),
            _md("wrapped", "Maker.wrap.wrapped", "pkg.wrap", "", "",
                "(self, *a, **k)")),
    },
    {
        "id": "weak-qualname-generic",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED for C2 — an observable this carrier pins that nagini's did not
        # model at all. Propagate everything except the reported qualified name,
        # which keeps the bare wrapper's own internal one.
        "module": _impl(
            "  -- Propagate every observable except the reported qualified name, which\n"
            "  -- keeps the bare wrapper's own internal one.\n"
            + _propagate(qualname="rawDelegate.qualname")),
        "refinement": (
            "the delegating method would report the bare forwarding wrapper's own "
            "internal qualified name — a name nested inside the constructing "
            "helper — rather than the underlying method's. The modeled behaviour "
            "is the propagation of the FULL introspectable metadata bundle "
            "(mapping.md), of which the reported qualified name is a member: it "
            "is one of the attributes the standard wrapper facility copies, so a "
            "construction that omits it is a partial hand-rolled copy rather than "
            "the modeled change, exactly the shape of defect the change replaces. "
            "Correct only on the sub-domain where the underlying method's "
            "qualified name coincides with the wrapper's internal one, which for "
            "a wrapper defined inside the constructing helper is never the case "
            "in the real code."),
        "rationale": (
            "REJECT from C2 (`result.qualname = underlying.qualname`): an "
            "independent conjunct no other rival attacks. Refuted at an input "
            "whose qualified names differ. Has NO nagini counterpart — nagini's "
            "carrier modeled only a name, a doc, and a signature, so this "
            "observable did not exist there; it is a real divergence on this "
            "wider carrier, not fabricated wrongness. Else SPEC-TOO-WEAK "
            "(a clause left entirely unattacked is a clause no rival tests)."),
        "witness": _witness(
            _md("graft", "Outer.graft", "pkg.tree", "Graft.", "{'t': 'Node'}",
                "(t)"),
            _md("relay", "Maker.relay.inner", "pkg.tree", "", "",
                "(self, *a, **k)")),
    },
    {
        "id": "weak-module-generic",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED for C3 — likewise unmodeled by nagini. Propagate everything
        # except the reported defining module.
        "module": _impl(
            "  -- Propagate every observable except the reported defining module,\n"
            "  -- which keeps the bare wrapper's own.\n"
            + _propagate(module="rawDelegate.module")),
        "refinement": (
            "the delegating method would report the bare wrapper's own defining "
            "module rather than the underlying method's, so tooling that groups "
            "or resolves a method by its defining module would attribute it to "
            "the wrong one. The reported defining module is a member of the "
            "introspectable bundle the modeled propagation copies (mapping.md), "
            "so omitting it is a partial hand-rolled copy — the class of defect "
            "the change eliminates — and diverges from the modeled behaviour on "
            "every underlying method defined outside the wrapper's own module, "
            "which is every method being delegated. It would NOT resolve as the "
            "faithful change."),
        "rationale": (
            "REJECT from C3 (`result.module = underlying.module`): an independent "
            "conjunct no other rival attacks. Refuted at an input whose modules "
            "differ. No nagini counterpart (the observable did not exist on that "
            "carrier). Else SPEC-TOO-WEAK."),
        "witness": _witness(
            _md("nudge", "Outer.nudge", "pkg.motion", "Nudge.", "{}",
                "(dx, dy)"),
            _md("hop", "Maker.hop.inner", "pkg.build", "(none)", "",
                "(self, **k)")),
    },
    {
        "id": "weak-annotations-generic",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED for C5 — likewise unmodeled by nagini. Propagate everything
        # except the parameter annotations.
        "module": _impl(
            "  -- Propagate every observable except the parameter annotations, which\n"
            "  -- keep the bare wrapper's own (absent) value.\n"
            + _propagate(annotations="rawDelegate.annotations")),
        "refinement": (
            "the delegating method would expose the bare wrapper's own (absent) "
            "parameter annotations instead of the underlying method's, so tooling "
            "that reads annotations off a delegating method sees none where the "
            "underlying method declares them. The annotations are a member of the "
            "introspectable bundle the modeled propagation copies (mapping.md); a "
            "construction that omits them is again the partial hand-rolled copy "
            "the change replaces, and diverges on every annotated underlying "
            "method. Not the faithful change, so it would NOT resolve."),
        "rationale": (
            "REJECT from C5 (`result.annotations = underlying.annotations`): an "
            "independent conjunct no other rival attacks. Refuted at an input "
            "where the underlying method declares annotations and the wrapper "
            "does not — note the witness's wrapper carries an EMPTY-RECORD "
            "annotations value distinct from the empty string, so the refutation "
            "cannot be read as an artifact of a shared default. No nagini "
            "counterpart. Else SPEC-TOO-WEAK."),
        "witness": _witness(
            _md("clamp", "Outer.clamp", "pkg.math", "Clamp.",
                "{'lo': 'int', 'hi': 'int'}", "(lo, hi)"),
            _md("stub", "Maker.stub.inner", "pkg.math", "", "{}",
                "(self, *a)")),
    },
    {
        "id": "weak-doc-not-propagated",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C4 in ISOLATION: propagate every observable except the
        # documentation, which keeps the bare wrapper's own. The nagini sibling
        # never dropped the doc while keeping the name (its rivals either
        # cross-wired the two or dropped both), so C4 needs its own rival here.
        "module": _impl(
            "  -- Propagate every observable except the documentation, which keeps the\n"
            "  -- bare wrapper's own.\n"
            + _propagate(doc="rawDelegate.doc")),
        "refinement": (
            "the delegating method would keep the bare wrapper's own "
            "documentation instead of the underlying method's. The change ships "
            "an accompanying PASS_TO_PASS assertion that a delegating method's "
            "documentation equals the underlying method's, so on every underlying "
            "method carrying real documentation this leaves the wrong string and a "
            "faithful patch of this shape would NOT resolve. Partial-domain: "
            "correct only where the two documentations coincide."),
        "rationale": (
            "REJECT from C4 (`result.doc = underlying.doc`): the clause the name "
            "and signature rivals leave correct. Refuted at an input where the "
            "wrapper carries a NON-EMPTY placeholder documentation differing from "
            "the underlying method's — chosen over an empty wrapper doc so the "
            "witness also demonstrates the clause is an equality to `underlying`, "
            "not merely a non-emptiness check. Else SPEC-TOO-WEAK."),
        "witness": _witness(
            _md("bundle", "Outer.bundle", "pkg.pack", "Bundle the rows.", "{}",
                "(self)"),
            _md("carry", "Maker.carry.inner", "pkg.pack", "(undocumented)", "",
                "(self, *a, **k)")),
    },
    {
        "id": "weak-conditional-propagate",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL-FLOW / sub-domain rival, porting the nagini
        # weak-conditional-record: propagate the full bundle ONLY when the
        # underlying method's parameter list differs from the wrapper's generic
        # catch-all, on the theory that when they coincide there is "nothing to
        # fix". All six clauses hold on the taken branch; on the abandoned
        # sub-domain the signature clause holds by coincidence while the OTHER
        # five silently fail. This is the rival the pinning half of the
        # postcondition exists to catch.
        "module": _impl(
            "  -- Propagate the full metadata bundle only when the underlying method's\n"
            "  -- parameter list differs from the bare wrapper's generic catch-all.\n"
            "  let mut md := rawDelegate\n"
            "  if underlying.signature ≠ rawDelegate.signature then\n"
            "    md := { md with\n"
            + ",\n".join(f"      {f} := underlying.{f}" for f in _FIELDS)
            + " }\n  return md"),
        "refinement": (
            "a construction that applies the metadata propagation CONDITIONALLY — "
            "only when the underlying method's rendered parameter list differs "
            "from the wrapper's generic catch-all — diverges from the modeled "
            "behaviour, which propagates unconditionally for every delegated "
            "method. The abandoned sub-domain is not empty and not exotic: an "
            "underlying method declared with the same variadic catch-all "
            "parameter list as the forwarding wrapper falls into it, and such "
            "methods exist among the delegated ones (the accompanying PASS_TO_PASS "
            "attributes assertion is made on methods of exactly that shape). For "
            "those the delegating method would report the wrapper's own internal "
            "name, qualified name, module and no documentation, so the attributes "
            "assertion fails and a faithful patch of this shape would NOT "
            "resolve."),
        "rationale": (
            "REJECT from C1/C2/C3/C4/C5 on the abandoned sub-domain: the guard "
            "makes C6 hold vacuously there (the two signatures are equal, so the "
            "wrapper's own value satisfies it), which is precisely why the other "
            "five conjuncts must be pinned unconditionally. Refuted at the one "
            "input class no other witness probes: an underlying method whose own "
            "parameter list COINCIDES with the wrapper's catch-all while its "
            "name, qualified name, module and documentation all differ. Ports the "
            "nagini weak-conditional-record. Else SPEC-TOO-WEAK (the spec would "
            "let the propagation be restricted to a sub-domain of inputs)."),
        # The wrapper's module is DELIBERATELY distinct from the underlying
        # method's here ("pkg.forward" vs "pkg.store"): the rationale claims the
        # abandoned sub-domain breaks C1/C2/C3/C4/C5, and C3 is only among them
        # if the two modules actually differ at this point. An earlier revision
        # of this witness held both at "pkg.store", which left C3 satisfied by
        # coincidence and made the five-clause claim overstated by one clause.
        "witness": _witness(
            _md("gather", "Outer.gather", "pkg.store", "Gather rows.",
                "{'k': 'str'}", "(self, *a, **k)"),
            _md("inner", "Maker.make.inner", "pkg.forward", "", "",
                "(self, *a, **k)")),
    },
]


# ===========================================================================
# NAGINI -> LEAN ACCOUNTING (which cases ported, which were omitted and why).
#
# The nagini sibling contracts `build_proxy(source) -> Func` over a mutable
# five-field `Func` object under fractional-permission framing, with the
# reported call signature resolved INDIRECTLY through a `wrapped` boolean plus a
# separately recorded signature field and a `@Pure @ContractOnly` resolver
# oracle, and with the produced object's OWN declared signature modeled as a
# field distinct from what introspection reports. This bundle contracts the SAME
# behaviour as a pure total function over a SIX-field transparent record — the
# six observables inspection reads (mapping.md) — with no heap, no aliasing, no
# permissions, no `wrapped` flag, no recorded-signature indirection, and no
# separate own-declared signature: each field IS an observable.
#
#   nagini case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-reordered       -> pos-stepwise-reordered           PORTED
#                                  (+ pos-direct-record, ADDED reshape)
#                                  (+ pos-pointwise-agree, ADDED non-defeq)
#   admiss-selfcall             -> admiss-f2p-point                 RE-AIMED
#   frame-mutate-source-name    -> (none)                           VACUOUS
#   frame-mutate-source-sig     -> (none)                           VACUOUS
#   weak-prefix-no-record       -> weak-partial-name-doc-only       PORTED
#   weak-wrapped-wrong-target   -> weak-signature-constant          MERGED/RE-EXPR
#   weak-name-doc-swap          -> weak-name-from-doc               PORTED
#   weak-own-sig-source         -> (none)                           COLLAPSED
#   weak-own-sig-arbitrary      -> weak-signature-constant          RE-EXPRESSED
#   weak-conditional-record     -> weak-conditional-propagate       PORTED
#   weak-return-source          -> (none)                           NOT-WRONG
#   (no sibling)                -> weak-signature-generic           ADDED (C6 iso)
#   (no sibling)                -> weak-qualname-generic            ADDED (C2)
#   (no sibling)                -> weak-module-generic              ADDED (C3)
#   (no sibling)                -> weak-annotations-generic         ADDED (C5)
#   (no sibling)                -> weak-doc-not-propagated          ADDED (C4)
#   AXIOM_TESTS (2)             -> (none)                           DROPPED
#
# 13 lean SPEC cases: 3 soundness, 1 admissibility, 9 uniqueness. Every one of
# the six independent clauses is attacked by a rival that isolates it, plus one
# rival for the pre-change behaviour and one control-flow rival for the
# sub-domain shape.
#
# PORTED (pos-stepwise-reordered): the nagini positive control reorders the
#   straight-line metadata assignments through a renamed local. Carried over
#   directly: reverse field order, one update per attribute. Its proof closes
#   under the frozen script because the value flow is unchanged.
# ADDED (pos-direct-record): a second correct reshape (single-expression record
#   build, no accumulator) so the positive lane exercises two genuinely distinct
#   correct code shapes rather than two spellings of one. Both were confirmed to
#   verify with real builds; neither needed proof retuning, so neither weakens
#   the obligation.
# ADDED (pos-pointwise-agree): both reshapes above are DEFINITIONALLY EQUAL to
#   the frozen value function — measured, `rfl` closes
#   `implementation_delegateMetadata u r = { name := u.name, … }` against each of
#   them and against the frozen file alike — so each closes under the frozen
#   tactic script UNCHANGED. That makes them honest positives but cheap ones:
#   they re-run the frozen proof on a re-spelled term rather than forcing the
#   obligation to be re-proven for a new shape, so on their own the positive lane
#   could not distinguish a spec that pins behaviour from one over-fit to the
#   frozen code shape. This third positive is extensionally the same function but
#   NOT defeq (it decides each field pointwise against the wrapper's own value):
#   the frozen `refine ⟨rfl, …⟩` fails on it (measured: `Tactic 'rfl' failed` —
#   the `ite` will not reduce at open inputs), so it carries its OWN proof, which
#   re-discharges all six clauses by case analysis on the six guards. It edits
#   the impl AND proof regions; the theorem statement stays byte-identical.
# RE-AIMED (admiss-selfcall -> admiss-f2p-point): the nagini case establishes
#   that its half-permission precondition admits a normal freshly-built input,
#   via a self-call. This obligation has no precondition at all, so that probe is
#   vacuous as stated. Rather than drop the class, it is re-aimed at the residual
#   risk a total domain still carries — joint satisfiability of the six-clause
#   post-image at a realistic point — keeping the nagini shape of discharging the
#   spec at a concrete input before the general obligation. Edits the proof body
#   only; the theorem statement is byte-identical, so the obligation is not
#   weakened (the prepended `have` is an ADDITIONAL burden closed by `decide`,
#   not a replacement for the conclusion).
# PORTED (weak-partial-name-doc-only): the nagini weak-prefix-no-record is the
#   pre-change behaviour (name and doc copied, nothing recorded, so the resolver
#   reports the forwarding signature). Carries over as propagating only the
#   reported name and documentation — the same defect, stated directly on the
#   observables rather than through the resolver indirection.
# MERGED / RE-EXPRESSED (weak-signature-constant): nagini's
#   weak-wrapped-wrong-target records the forwarding signature as the "original",
#   and weak-own-sig-arbitrary uses an arbitrary constant code; on this carrier
#   both are the same thing — a wrong constant in the one observable signature
#   field — so they merge into one rival, placed at the arbitrary-constant form
#   because it is the strictly stronger partial-domain statement. Its witness is
#   deliberately at a DIFFERENT point from the other two C6 rivals so the merge
#   does not cost a probed sub-domain.
# PORTED (weak-name-from-doc): the nagini weak-name-doc-swap carries over intact
#   onto C1.
# PORTED (weak-conditional-propagate): the nagini weak-conditional-record
#   restricts the recording to the sub-domain where the source's signature
#   differs from the forwarding value. Carries over as a guarded propagation of
#   the whole bundle, which is the stronger version of the same attack on this
#   carrier: the guard makes C6 hold vacuously on the abandoned sub-domain while
#   the other five clauses fail there, so the case demonstrates why the
#   non-signature clauses must be pinned unconditionally.
# COLLAPSED (weak-own-sig-source): the nagini spec models the proxy's OWN
#   declared signature as a field separate from what introspection reports, and
#   this rival puts the source's signature into that separate field while keeping
#   the reported-signature clause satisfied. This carrier has no such split — the
#   single `signature` field IS what inspection reports (mapping.md) — so the
#   rival has no distinct field to abuse and collapses onto C6, already attacked
#   by three rivals. Not fabricated as a separate case.
# NOT-WRONG / DROPPED (weak-return-source): the nagini rival returns the source
#   object itself and is rejected by a distinctness clause (`Result() is not
#   source`) plus the ownership permissions an aliased source cannot supply.
#   Neither has a counterpart here: object identity is not modeled, the carrier
#   is a value, and returning `underlying` unchanged satisfies all six clauses —
#   correctly, since a produced method presenting all six of the underlying
#   method's observables IS introspection-faithful, and the graded observable is
#   one of those six. So this is a CORRECT implementation of the modeled
#   behaviour on this carrier, and shipping it as a reject case would be
#   fabricated wrongness with no witness able to discriminate it. Genuine carrier
#   narrowing (the abstraction collapses an identity distinction nagini's heap
#   model kept), NOT a spec hole.
# VACUOUS (frame-mutate-source-name, frame-mutate-source-sig): the two MANDATORY
#   nagini frame rivals write through the half-permission source — one
#   overwriting its reported name to force the name clause, one forcing its
#   recorded signature to the forwarding value so an unrecorded proxy satisfies
#   the resolver clause vacuously — and both are rejected by the PERMISSION
#   system, not by a postcondition. This backend is referentially transparent:
#   `underlying` and `rawDelegate` are immutable values, the obligation binds no
#   mutable parameter, and there is no heap, aliasing, or permission fraction. So
#   there is no read-only input to overwrite and no substitute probe to build.
#   Not fabricated.
# DIVERGENCE: VACUOUS, and genuinely so rather than by omission. The nagini
#   sibling carries no diverge-*/nonterm-*/weak-diverge case, so there is nothing
#   to port; and independently `implementation_delegateMetadata` is a total Lean
#   `def`, so a non-terminating implementation cannot be expressed here at all.
#   This is NOT the velvet `partial`-semantics spec hole of
#   the corpus-wide termination-semantics finding — under that semantics a diverging impl satisfies
#   every clause vacuously and the frozen spec ADMITS it, which is a known hole
#   in the spec; on lean the rival is not writable, which is a property of the
#   carrier. No reject case is written for it (a reject case would need a witness
#   refuting a rival that cannot exist) and none is claimed dropped.
# DROPPED (AXIOM_TESTS): the nagini file's axiom-soundness probe (fuzzing the
#   real introspection facility against both branches of its resolver oracle) and
#   its containment probe (the reachable caller inputs lie inside the oracle's
#   domain) belong to the axiom lane. This bundle declares no `opaque` callee and
#   consumes no `axiom` — the changed operation is modeled deeply, so
#   `meta.json axioms = []` and G-AX skips — validating that deep model against
#   the real facility is `axiom_check.py` / `conformance_check.py`'s job, and the
#   G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE.
#   CLAUSES: all six independent conjuncts are attacked, each by a rival that
#     isolates it — C1 weak-name-from-doc, C2 weak-qualname-generic, C3
#     weak-module-generic, C4 weak-doc-not-propagated, C5
#     weak-annotations-generic, C6 weak-signature-generic — plus
#     weak-signature-constant (a second, partial-domain attack on the graded C6),
#     weak-partial-name-doc-only (the pre-change behaviour, C2/C3/C5/C6 at once)
#     and weak-conditional-propagate (C1-C5 on an abandoned sub-domain — its
#     witness moves the wrapper's module OFF the underlying method's so all five
#     claimed clauses genuinely break there rather than four breaking and C3
#     holding by coincidence). All six are defended by all three positives and by
#     the admissibility case, each of which discharges the full conjunction; and
#     pos-pointwise-agree does so on a non-defeq impl, so at least one positive
#     re-proves the conjunction instead of re-spelling the frozen proof.
#   BINDERS: both input binders are varied. `underlying` takes nine DISTINCT
#     records and `rawDelegate` nine DISTINCT records across the nine witnesses;
#     no field of either binder is held at a single value by every witness, so a
#     rival mishandling any one of the twelve input components would be caught.
#     `rawDelegate` is varied deliberately and not incidentally: it is the binder
#     the wrong impls read FROM, so holding it fixed would leave the spec's
#     dependence on it undemonstrated.
#   POINTS: pts = 9 distinct input pairs, one per rival — no two rivals share a
#     witness. The three C6 rivals are separated on purpose: the pre-change rival
#     is refuted where four fields differ, the isolating rival at a NEAR-MISS
#     where only the signature differs, and the constant rival at a point where
#     the signature is neither the catch-all nor the constant. So each rival's
#     rationale claims a sub-domain the manifest actually demonstrates, rather
#     than three rivals resting on one point.
#
# WITNESS MECHANICS. The carrier is fully transparent — six `String` fields,
#   `deriving DecidableEq`, an empty axioms region, no opaque callee — so a
#   witness states the spec predicate's negation at ground literals and `decide`
#   settles it. No witness conditions on the carrier and none binds anything in
#   its head, so there are no hypotheses whose joint satisfiability could be in
#   question and the gate's consistency probe has nothing to check. All nine were
#   verified out-of-band with two real `scripts/lean_verify.sh` builds each:
#   ELABORATES against its rival (exit 0) and FAILS against the frozen solution.
#   The gold-side failure is `Tactic 'decide' proved that the proposition … is
#   false` in every case — that is, gold SATISFIES the spec at that input — so
#   each witness discriminates on the spec itself and not on an incidental
#   elaboration error. All thirteen variants were also built directly: all three
#   positives and the admissibility case VERIFY (exit 0), and all nine rivals are
#   REJECTED, with every case reporting scope-ok.
#
# ADMISSIBILITY BURDEN, MEASURED. The prepended `have` in admiss-f2p-point is not
#   decorative: perturbing a single field of its spec-side `underlying` (leaving
#   the impl application intact) makes the case FAIL to build, with `decide`
#   reporting the perturbed proposition false. So the `have` really is an
#   additional obligation the case must discharge at that concrete point.
AXIOM_TESTS = []
