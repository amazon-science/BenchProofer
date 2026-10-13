"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10614 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct buildLinkMap`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the discrimination subject — here an explicit ``witness_reference``, a
verifying loop-free impl of the same frozen spec, because gold's ``while`` fold
cannot decide anything under ``decide``; see WITNESS MECHANICS below).

DEFENDED SURFACE (one contracted method):

  buildLinkMap (refs : List DiagRef) (isSvg : Bool) (page : List Char)
      return (out : List (List Char × List Char))
    ensures out = linkMap isSvg page refs                       -- the WHOLE pin (C1)

The method walks a diagram's references in order and collects, for each, the
zero-or-one link-map entry it contributes. The entry a single reference
contributes is the pure ``def refEntry``; the whole map is the pure
front-recursive fold ``linkMap`` (``linkMap (c :: cs) = refEntry c ++ linkMap
cs``). Both are TRANSPARENT ``def``s over the method's own inputs — the only
callee, ``afterLastHash`` (the maximal suffix with no ``'#'``), is itself a
concrete ``def`` in the ``pure`` region, NOT an ``axiom`` (the ``axioms`` region
is empty; the stdlib split is a G-AX deep-model reference, not a consumed
contract). So C1 is a fully-grounded pin: there is no opaque answer key to echo.

WHICH DECISIONS C1 PINS. ``refEntry`` makes three independent, observable
decisions, and C1 pins each at every position of ``refs``:
  (a) with an explicit ``target``, the entry's URL is that target VERBATIM —
      never adorned with a leading relative-path prefix, never truncated;
  (b) with an explicit ``target``, the entry's KEY is recovered from the final
      ``'#'``-segment of the target URL when the reference resolves OUTSIDE the
      project, and is the reference's own ``name`` otherwise;
  (c) with no target but an ``anchor``, the URL is the fragment taken relative
      to the page (``page`` prepended) under the embedded-object (SVG) rendering
      and a bare fragment otherwise.
Every uniqueness rival below targets exactly one of (a)/(b)/(c), and the input
binders ``refs`` (its per-``DiagRef`` fields ``target``/``anchor``/``outside``/
``name``), ``isSvg``, and ``page`` are varied across the reject witnesses so no
binder is held at one value by every rival.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling's three
    ``frame-mut-*`` rivals write through a read-only (``Acc(.,1/2)``) reference
    to an input to fabricate the answer and are rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: every input here
    is an immutable value, this bundle declares no ``mut`` parameter, and there
    is no heap, aliasing, or permission system to subvert. There is no read-only
    input to overwrite, so the class is vacuous. No substitute probe is
    fabricated (see the footer).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. C1's post-image ``linkMap isSvg
    page refs`` is a transparent fold over the method's own arguments (and its
    only callee ``afterLastHash`` is a concrete ``def``, not an oracle); there is
    no answer key to echo. The honest cheapest CORRECT impl (``return linkMap
    isSvg page refs``) is carried as a POSITIVE control instead — it doubles as
    proof the spec is not echo-vulnerable, since any WRONG entry fails C1.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against C1. The
    nagini partial-domain rivals (drop the last element; return the whole URI as
    the key) and the two literal-bug rivals (the ``'../'`` over-climb on the
    target branch and on the fragment branch) port directly; three more rivals
    complete coverage of decisions (a)/(b)/(c).
  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS MECHANICS ON THIS BUNDLE. C1's carrier is fully transparent (no opaque
callee), so the refutation is stated directly on values. The tester+``decide``
path (``derive_tester_for`` → ``<name>Tester args = false``) is available in
principle, but the cleaner and already-validated route here is to EXTRACT the
executable program and refute C1 against the transparent ``linkMap``: each rival
is written LOOP-FREE (a ``refs.flatMap`` per-reference map), so its extracted
program ``buildLinkMapExec`` — the ``NonDetT``-run of the impl — REDUCES fully
under ``decide`` at a concrete input. Each witness states, at one concrete
``(refs, isSvg, page)``,

    (match buildLinkMapExec <refs> <isSvg> <page> with | DivM.res r => r | _ => [])
        ≠ linkMap <isSvg> <page> <refs>

i.e. the rival's own output DIFFERS from the post-image C1 demands — a direct C1
violation the elaborator sees.

THE FROZEN IMPL CANNOT SERVE AS THE DISCRIMINATION SUBJECT, and every reject case
below therefore carries an explicit ``witness_reference``. Gold's body is the
backward ``while`` fold, whose ``…Exec`` elaborates through the loop's
``Classical.choice``; the kernel does not reduce it, so ``decide`` against gold
gets STUCK rather than deciding. Measured on all seven witnesses with
``scripts/lean_verify.sh``: the gold-side build fails (exit 1) with

    Tactic `decide` failed ... its `Decidable` instance instDecidableNot
    did not reduce to `isTrue` or `isFalse` ... stuck at ... `.hasDecEq`

A failure the kernel never evaluated attests to NOTHING — the identical error
appears for a TRUE claim about gold, so that exit code is not a refutation and
the gate screens it (``witness-undecided``; see ``gates/pbt.py``
``_STUCK_REDUCTION``). So each case names as its ``witness_reference`` the
loop-free positive ``_REF_LOOPFREE`` (the ``pos-control-direct`` impl): an impl
of this SAME frozen spec that the gate independently re-checks shares the spec
and VERIFIES, and whose ``…Exec`` DOES reduce. Against it the same seven
witnesses fail SEMANTICALLY (exit 1, ``Tactic `decide` proved that the
proposition ... is false``) — a real refutation of the concrete claim, which is
the discrimination the gate requires. The reference is stated explicitly rather
than left to the gate's positives-fallback so the subject is fixed by the
manifest instead of by manifest order.

Measured, per reject case: witness vs. rival exit 0; witness vs.
``_REF_LOOPFREE`` exit 1 by semantic refutation; witness vs. gold exit 1 by
stuck reduction (recorded here only to justify the reference). No witness binds
any hypothesis (every input is a concrete literal that decides C1), so no
consistency probe is needed. No banned token (sorry/admit/native_decide/axiom/
opaque). All three positives verify (exit 0).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the real stdlib string ops; that is G-AX's
job (axiom_check.py / mapping.md — ``afterLastHash == rsplit('#',1)[-1]``) and
the G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10614"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (backward `while` fold),
# ---- everything strictly BETWEEN the method's `-- impl-start` / `-- impl-end`.
# ---- Every variant replaces exactly this text, so each edit lies wholly inside
# ---- the one -- impl-start .. -- impl-end region and same_spec holds by
# ---- construction (both facts asserted at load by _swap).
_IMPL = (
    "    let mut acc : List (List Char × List Char) := []\n"
    "    let mut i := refs.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ refs.length\n"
    "      invariant acc = linkMap isSvg page (refs.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := refs[i - 1]!\n"
    "      acc := refEntry isSvg page c ++ acc\n"
    "      i := i - 1\n"
    "    return acc"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A loop-free reshape may retune THIS block (elided
# from the spec view); the loop-keeping positive leaves it as-is. Rivals leave
# it as-is too — the rejection is carried by the witness, not the tactic script.
_PROOF = (
    "prove_correct buildLinkMap by\n"
    "  loom_solve\n"
    "  rw [linkMap_drop_step isSvg page refs i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for a loop-free correct reshape,
    whose residual goal no longer needs the backward-fold step lemma)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- A loop-free rival: map each reference to its (possibly wrong) entry with a
# ---- per-reference `refs.flatMap`. Being loop-free, its extracted `…Exec`
# ---- reduces under `decide` so its witness discriminates; gold's `while`-loop
# ---- `…Exec` stays stuck at `.hasDecEq`.
def _flatmap(target_arm, anchor_arm):
    return (
        "    return (refs.flatMap (fun c =>\n"
        "      match c.target with\n"
        f"      | some uri => {target_arm}\n"
        "      | none =>\n"
        "        match c.anchor with\n"
        f"        | some aid => {anchor_arm}\n"
        "        | none => []))"
    )


# The gold per-reference arms, reused verbatim in a flatMap where the rival does
# not touch that branch (keeps the divergence confined to the attacked decision).
_GOLD_T = "[(if c.outside then afterLastHash uri else c.name, uri)]"
_GOLD_A = "[(c.name, (if isSvg then page else []) ++ ('#' :: aid))]"


# ---- witness preamble + builder. C1's carrier is transparent, so the witness
# ---- extracts the executable program and refutes C1 directly against the
# ---- transparent `linkMap`. Checked in a file whose `prove_correct` block is
# ---- stripped, so no tactic script can mask the verdict.
def _witness(refs, isSvg, page):
    return (
        "extract_program_for buildLinkMap\n\n"
        "example :\n"
        f"    (match buildLinkMapExec {refs} {isSvg} {page} with | DivM.res r => r | _ => [])\n"
        f"      ≠ linkMap {isSvg} {page} {refs} := by\n"
        "  decide\n"
    )


# ---- The discrimination SUBJECT for every reject witness (`witness_reference`).
# ---- Gold's `while` fold elaborates through `Classical.choice`, so `decide`
# ---- against it is STUCK for every claim, true or false, and its exit code
# ---- discriminates nothing. This loop-free impl of the SAME frozen spec (the
# ---- `pos-control-direct` body, carried as a positive above and so independently
# ---- required to verify) DOES reduce, so a witness refuted against it is refuted
# ---- semantically. The gate re-checks both properties before using it.
_REF_LOOPFREE = _impl_reproved(
    "    return linkMap isSvg page refs",
    "prove_correct buildLinkMap by\n  loom_solve")


def _ref(name, target="none", anchor="none", outside="false"):
    return ("{ name := " + name + ", target := " + target
            + ", anchor := " + anchor + ", outside := " + outside + " }")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the whole link map DIRECTLY via the transparent fold,
        # no per-reference loop. C1 is literally `out = linkMap isSvg page refs`,
        # so this is the cheapest HONEST correct impl — and, since the post-image
        # is GROUNDED in the arguments (not an opaque answer key), it doubles as
        # proof the spec is not echo-vulnerable. The loop is gone, so the frozen
        # proof's backward-fold step is unneeded and the residual goal closes
        # under `loom_solve` alone.
        "module": _impl_reproved(
            "    return linkMap isSvg page refs",
            "prove_correct buildLinkMap by\n  loom_solve"),
        "rationale": (
            "the post-image `linkMap isSvg page refs` is GROUNDED in the inputs "
            "(a total front-recursive fold; its only callee `afterLastHash` is a "
            "concrete def, no opaque answer key), so `return linkMap isSvg page "
            "refs` is the honest cheapest CORRECT impl; C1 is literally that "
            "equality, so it MUST verify, else C1 is SPEC-TOO-STRONG. Ports the "
            "nagini pos-control-external-key honest control (the materialized "
            "answer IS the correct one), showing the spec is not echo-vulnerable."),
    },
    {
        "id": "pos-control-entry-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward `while` fold but bind the per-reference entry
        # to a typed local `e` before prepending it. Same value flow
        # (`e = refEntry isSvg page c`), different control shape; the frozen proof
        # still closes unchanged (loop invariant and step lemma untouched).
        "module": _impl(
            "    let mut acc : List (List Char × List Char) := []\n"
            "    let mut i := refs.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ refs.length\n"
            "      invariant acc = linkMap isSvg page (refs.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let c := refs[i - 1]!\n"
            "      let e := refEntry isSvg page c\n"
            "      acc := e ++ acc\n"
            "      i := i - 1\n"
            "    return acc"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind the per-reference "
            "entry to a typed local before prepending it) must verify; the value "
            "flow is unchanged (`e = refEntry isSvg page c`) so C1 still discharges "
            "and the frozen loop proof closes as-is. Ports the nagini "
            "pos-control-destination local-variable reshape: if it fails => "
            "SPEC-TOO-STRONG (over-fit to the inline-prepend code form)."),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-external-key. That case
    # established the read-only fractional precondition on an F2P-shaped
    # '#'-bearing intersphinx input. This method carries NO `require` clause (the
    # pre-conditions region is empty), so nothing could exclude a normal input
    # and the classic "a normal input is admitted" probe is vacuous. Re-aimed at
    # the residual admissibility risk on a total domain: that C1's post-image is
    # SATISFIABLE by a gold-shaped computation. The frozen impl discharging C1 IS
    # that witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the map builder is total over "
            "every reference list; the gold impl discharging C1 is the "
            "admissibility witness that the post-image `linkMap isSvg page refs` "
            "is satisfiable by a gold-shaped computation. Near-trivial precisely "
            "because the precondition is empty. Re-aimed from the nagini "
            "admiss-external-key, whose read-only-precondition half has no "
            "counterpart on this referentially-transparent carrier. Else "
            "SPEC-UNSATISFIABLE."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. All attack C1; each targets exactly
    # one of decisions (a) target-URL-verbatim, (b) outside-key-recovery, or
    # (c) anchor-page-prefix, and the binders refs/isSvg/page are varied so no
    # binder is held at one value by every witness.
    # =====================================================================

    # ---- decision (a): target URL is emitted VERBATIM (no prefix, no truncation)
    {
        "id": "prefix-dotdot-target",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal reported bug on the target branch: under SVG rendering,
        # prepend a relative "../" prefix to the target URL.
        "module": _impl(_flatmap(
            "[(if c.outside then afterLastHash uri else c.name, "
            "(if isSvg then \"../\".toList ++ uri else uri))]",
            _GOLD_A)),
        "refinement": (
            "this is the literal reported bug: under the embedded-object (SVG) "
            "rendering the target URL is over-climbed with a leading relative "
            "prefix. For an absolute destination that produces a prefixed absolute "
            "URL the failing test explicitly forbids, and for a relative link it "
            "climbs one directory too far and 404s — exactly the reported "
            "behaviour. Its faithful real patch is the pre-fix source, which would "
            "NOT resolve."),
        "rationale": (
            "REJECT from C1: `linkMap` pins the target URL VERBATIM (decision a), "
            "so a rival prepending a relative prefix under SVG diverges from the "
            "post-image at every target reference. Refuted at a single in-project "
            "target reference with isSvg=true — varying the isSvg binder to true "
            "and the target field to `some`. If it verified => SPEC-TOO-WEAK "
            "(admits the reported bug)."),
        "witness_reference": _REF_LOOPFREE,
        "witness": _witness(
            "[" + _ref('"N".toList', target='some "u".toList') + "]",
            "true", "[]"),
    },
    {
        "id": "partial-drop-last-target",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one on the target branch: drop the final code point of the URL.
        # Correct only on empty URLs; wrong on every non-empty target.
        "module": _impl(_flatmap(
            "[(if c.outside then afterLastHash uri else c.name, uri.dropLast)]",
            _GOLD_A)),
        "refinement": (
            "dropping the final character of every target URL yields a truncated "
            "destination that is neither the intended absolute URL nor an existing "
            "relative file, so the SVG test's absolute-prefix and "
            "relative-existence checks both fail; a real patch of this shape would "
            "NOT resolve. Ports the nagini partial-domain-destination-dropslast."),
        "rationale": (
            "REJECT from C1: `linkMap` pins the target URL VERBATIM (decision a), "
            "so a rival emitting `uri.dropLast` is one code point short on every "
            "non-empty target and diverges from the post-image. Refuted at a "
            "target of length two (isSvg=false) — a length divergence the prefix "
            "rival does not produce, varying the target field's content. If it "
            "verified => SPEC-TOO-WEAK."),
        "witness_reference": _REF_LOOPFREE,
        "witness": _witness(
            "[" + _ref('"N".toList', target='some "ab".toList') + "]",
            "false", "[]"),
    },

    # ---- decision (b): the KEY of a target entry (outside -> URL tail; else name)
    {
        "id": "key-name-not-recovered",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix KEY behaviour: always key a target entry on the reference's
        # own name, never recovering the outside key from the URL tail. Correct on
        # every in-project reference; wrong on outside references.
        "module": _impl(_flatmap("[(c.name, uri)]", _GOLD_A)),
        "refinement": (
            "this is the pre-fix key behaviour: a target entry is always keyed on "
            "the reference's own name, so an OUTSIDE reference is never keyed by "
            "the recovered final segment of its destination URL. The diagram's "
            "class node then fails to match its outside destination and the "
            "expected external link never appears — the exact defect the fix "
            "corrects, so a real patch of this shape would NOT resolve."),
        "rationale": (
            "REJECT from C1: `linkMap` recovers the key of an OUTSIDE target from "
            "the URL tail (decision b, `afterLastHash uri`), not from `name`. "
            "Refuted at a single OUTSIDE reference whose name differs from the URL "
            "tail — varying the `outside` field to true. If it verified => "
            "SPEC-TOO-WEAK (admits the un-recovered key)."),
        "witness_reference": _REF_LOOPFREE,
        "witness": _witness(
            "[" + _ref('"N".toList', target='some "a#b".toList', outside="true") + "]",
            "false", "[]"),
    },
    {
        "id": "key-wholeuri-outside",
        "kind": "uniqueness",
        "expect": "reject",
        # A NEAR-MISS of key-name-not-recovered: it DOES special-case outside
        # references, but recovers the key as the WHOLE URL instead of its final
        # '#'-segment (the older un-stripped behaviour). Correct on outside URLs
        # with no '#'; wrong on '#'-bearing ones (the intersphinx case).
        "module": _impl(_flatmap(
            "[(if c.outside then uri else c.name, uri)]", _GOLD_A)),
        "refinement": (
            "recovering the outside key as the WHOLE destination URL instead of "
            "its final segment registers the class under the full URL, so the "
            "'#'-bearing intersphinx target's class node is not matched and the "
            "expected external link is missing; a real patch of this shape would "
            "NOT resolve. Ports the nagini partial-domain-external-key-wholeuri "
            "(the un-stripped key)."),
        "rationale": (
            "REJECT from C1: for an OUTSIDE target `linkMap` keys on the final "
            "'#'-segment (`afterLastHash uri`), not the whole URL (decision b). "
            "Refuted at an OUTSIDE '#'-bearing target whose NAME equals the URL "
            "tail — a DISTINCT point from key-name-not-recovered, where keying on "
            "name would AGREE with gold, so this near-miss is demonstrated on the "
            "sub-domain it alone abuses. If it verified => SPEC-TOO-WEAK."),
        "witness_reference": _REF_LOOPFREE,
        "witness": _witness(
            "[" + _ref('"b".toList', target='some "a#b".toList', outside="true") + "]",
            "false", "[]"),
    },
    {
        "id": "key-strip-inproject",
        "kind": "uniqueness",
        "expect": "reject",
        # The `outside` toggle abused from the OTHER direction: recover the key
        # from the URL tail even for IN-PROJECT references. Correct on outside
        # references; wrong on in-project ones whose name differs from the tail.
        "module": _impl(_flatmap("[(afterLastHash uri, uri)]", _GOLD_A)),
        "refinement": (
            "recovering the key from the URL tail for an IN-PROJECT reference "
            "(ignoring the `outside` flag) mis-keys documented in-project classes "
            "whose reference name is not the tail of their target URL, so those "
            "diagram nodes fail to resolve; a real patch of this shape would NOT "
            "resolve. No direct nagini sibling — added to attack the `outside` "
            "binder from the false side, completing decision (b)."),
        "rationale": (
            "REJECT from C1: for an IN-PROJECT target `linkMap` keys on `name`, "
            "not on the URL tail (decision b). Refuted at an IN-PROJECT reference "
            "whose name differs from `afterLastHash uri` — varying `outside` to "
            "false against key-name-not-recovered's true, so the `outside` binder "
            "is exercised on both sides. If it verified => SPEC-TOO-WEAK."),
        "witness_reference": _REF_LOOPFREE,
        "witness": _witness(
            "[" + _ref('"N".toList', target='some "a#b".toList', outside="false") + "]",
            "false", "[]"),
    },

    # ---- decision (c): the fragment URL of an anchor entry (page-relative iff SVG)
    {
        "id": "prefix-dotdot-anchor",
        "kind": "uniqueness",
        "expect": "reject",
        # The literal reported bug on the fragment branch: under SVG rendering,
        # prepend a relative "../" prefix IN FRONT of the page path.
        "module": _impl(_flatmap(
            _GOLD_T,
            "[(c.name, (if isSvg then \"../\".toList ++ page else []) "
            "++ ('#' :: aid))]")),
        "refinement": (
            "this is the literal reported bug on the fragment branch: under the "
            "embedded-object (SVG) rendering the page-relative fragment link is "
            "over-climbed with a leading relative prefix, so the link resolves "
            "above the intended directory and 404s — the reported behaviour for "
            "a nested page. Its faithful real patch is the pre-fix source, which "
            "would NOT resolve. Ports the nagini prefix-dotdot-self-doc."),
        "rationale": (
            "REJECT from C1: for an anchor entry under SVG, `linkMap` prepends the "
            "page path with NO relative prefix (decision c). Refuted at a "
            "fragment-only reference with isSvg=true and a non-empty page — "
            "varying the anchor field to `some` and page to a non-empty value. "
            "If it verified => SPEC-TOO-WEAK (admits the reported bug)."),
        "witness_reference": _REF_LOOPFREE,
        "witness": _witness(
            "[" + _ref('"N".toList', anchor='some "a".toList') + "]",
            "true", '"p".toList'),
    },
    {
        "id": "partial-anchor-drop-page",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: emit a BARE fragment for an anchor entry regardless of
        # the rendering mode (omit the page path even under SVG). Correct on the
        # non-SVG rendering; wrong under SVG.
        "module": _impl(_flatmap(_GOLD_T, "[(c.name, ('#' :: aid))]")),
        "refinement": (
            "emitting a bare fragment under SVG omits the page path the "
            "embedded-object rendering needs, so the fragment resolves against the "
            "wrong document and does not reach the intended page; a real patch of "
            "this shape would NOT resolve. No direct nagini sibling — added to "
            "attack the isSvg dependence of decision (c) as a genuine "
            "partial-domain break (correct on the non-SVG rendering)."),
        "rationale": (
            "REJECT from C1: for an anchor entry under SVG, `linkMap` prepends the "
            "page path (decision c); a rival emitting a bare fragment diverges "
            "under SVG. Refuted at a fragment-only reference with isSvg=true and a "
            "non-empty page `\"pg\"` — a DISTINCT point from prefix-dotdot-anchor "
            "(different page value and a different divergence: missing prefix vs. "
            "wrong prefix), varying the page binder. If it verified => "
            "SPEC-TOO-WEAK."),
        "witness_reference": _REF_LOOPFREE,
        "witness": _witness(
            "[" + _ref('"N".toList', anchor='some "x".toList') + "]",
            "true", '"pg".toList'),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                         -> here
#   -----------------------------------------------------------------------
#   pos-control-destination             -> pos-control-entry-local     PORTED (reshape)
#   pos-control-external-key            -> pos-control-direct           RE-EXPRESSED
#   admiss-external-key                 -> admiss-gold-total            RE-AIMED
#   frame-mut-destination               -> (none)                      VACUOUS
#   frame-mut-self-doc                  -> (none)                      VACUOUS
#   frame-mut-external-key              -> (none)                      VACUOUS
#   partial-domain-destination-dropslast-> partial-drop-last-target    PORTED
#   partial-domain-external-key-wholeuri-> key-wholeuri-outside         PORTED
#   prefix-dotdot-destination           -> prefix-dotdot-target         PORTED
#   prefix-dotdot-self-doc              -> prefix-dotdot-anchor         PORTED
#   (no sibling)                        -> key-name-not-recovered       ADDED
#   (no sibling)                        -> key-strip-inproject          ADDED
#   (no sibling)                        -> partial-anchor-drop-page     ADDED
#   AXIOM_TESTS (2)                     -> (none)                      DROPPED (G-AX lane)
#
# 10 velvet SPEC cases: 2 soundness, 1 admissibility, 7 uniqueness. Every nagini
# rival that attacks a modeled clause is ported; three added rivals complete
# per-decision coverage of the single obligation C1.
#
# CARRIER NARROWING. The nagini sibling contracts THREE functions
# (svg_url_for_destination = identity copy; svg_url_for_self_doc_anchor =
# cf ++ '#' ++ aid; external_key_for_destination = after_last_hash). This velvet
# bundle models the whole changed link-map construction as ONE method
# `buildLinkMap`, whose pure post-image `linkMap`/`refEntry` FOLDS all three
# behaviours into the per-reference entry: the target-URL-verbatim decision (a)
# is the old svg_url_for_destination identity minus the '../' bug; the
# outside-key-recovery decision (b) is the old external_key after_last_hash; the
# anchor-page-prefix decision (c) is the old svg_url_for_self_doc_anchor minus
# the '../' bug. So the nagini per-function rivals map onto per-DECISION rivals
# of the single `linkMap` clause, not onto separate methods — the port is a
# re-expression against a narrower (single-obligation) carrier, and case-count
# parity with the three-function sibling is not the target.
#
# RE-EXPRESSED (pos-control-external-key -> pos-control-direct): the nagini
#   honest control routed the final equality through a frozen carrier local that
#   held the materialized answer, arguing the grounded oracle makes the
#   materialized value the ONLY correct answer. On this carrier the post-image IS
#   the transparent `linkMap`, so the honest cheapest impl is `return linkMap
#   isSvg page refs` — the same argument (no wrong echo verifies; any wrong entry
#   fails C1) expressed as a loop-free correct impl.
# RE-AIMED (admiss-external-key -> admiss-gold-total): the nagini case witnessed
#   that the read-only fractional precondition admits a '#'-bearing intersphinx
#   URI. This method has no `require`, so that probe is vacuous; re-aimed at the
#   residual total-domain risk (C1's post-image joint satisfiability), witnessed
#   by the frozen impl discharging C1.
# PORTED (4): partial-drop-last-target (drop the final code point of the target
#   URL), key-wholeuri-outside (recover the outside key as the whole URL — the
#   un-stripped pre-patch key), prefix-dotdot-target and prefix-dotdot-anchor
#   (the literal '../' over-climb bug on the target and the fragment branches).
#   Each carries its nagini refinement argument (truncated/prefixed/un-stripped
#   link fails the same F2P assertion), now backed by a machine-checked witness.
# ADDED (3): key-name-not-recovered is the pre-fix KEY behaviour (always key a
#   target entry on the reference name, never recovering the outside key) — the
#   literal reported key defect, split out from the '../' url defect because on
#   this carrier the two pre-fix bugs on the target branch are independent
#   decisions. key-strip-inproject attacks the `outside` toggle from the false
#   side (recover the key even for in-project refs). partial-anchor-drop-page
#   attacks the isSvg dependence of decision (c) (bare fragment under SVG). All
#   three are real C1 divergences with machine-checked witnesses, not fabricated
#   wrongness — added to complete per-decision and per-binder coverage.
# FRAME-MUTATION (3 nagini cases): VACUOUS. Each nagini rival writes through a
#   read-only (1/2) reference to an input to fabricate the answer and is rejected
#   for insufficient permission. Velvet is referentially transparent, every input
#   is an immutable value, no `mut` binder, no heap, no aliasing, no permission
#   system. There is no read-only input to overwrite. No substitute fabricated.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# DROPPED (AXIOM_TESTS): the nagini file's axiom-soundness/containment probes over
#   the real stdlib string ops are G-AX's job (axiom_check.py / mapping.md:
#   afterLastHash == rsplit('#',1)[-1], a deep-model reference — the `axioms`
#   region is empty, no consumed contract); the G-PBT gate ignores AXIOM_TESTS.
#
# CLAUSE / BINDER / POINT COVERAGE. The single impl-constraining clause C1
#   (`out = linkMap isSvg page refs`) is attacked on ALL THREE of its decisions:
#   (a) target-URL-verbatim (prefix-dotdot-target, partial-drop-last-target),
#   (b) outside-key-recovery (key-name-not-recovered, key-wholeuri-outside,
#   key-strip-inproject), (c) anchor-page-prefix (prefix-dotdot-anchor,
#   partial-anchor-drop-page). The binders are varied so none is held at one
#   value by every witness: isSvg is true (prefix-dotdot-target,
#   prefix-dotdot-anchor, partial-anchor-drop-page) and false (the key/drop-last
#   rivals); the DiagRef `outside` field is true (key-name-not-recovered,
#   key-wholeuri-outside) and false (key-strip-inproject, the target/anchor
#   rivals); `target` is `some` on the (a)/(b) rivals and `none` on the (c)
#   rivals; `anchor` is `some` on the (c) rivals; `page` is non-empty and varied
#   ("p" vs "pg") on the (c) rivals. The seven reject witnesses probe seven
#   DISTINCT input points (pts=7); the near-miss key-wholeuri-outside is refuted
#   at a point (name == URL tail) where key-name-not-recovered would agree with
#   gold, so it is demonstrated on its own sub-domain.
#
# WITNESS MECHANICS: C1's carrier is fully transparent (no opaque callee), so
#   every witness extracts the executable program and refutes C1 directly against
#   the transparent `linkMap`. Each rival is loop-free (a `refs.flatMap`) so its
#   `…Exec` reduces under `decide`. Gold's backward `while`-loop `…Exec`
#   elaborates through the loop's `Classical.choice` and does NOT reduce, so
#   `decide` against gold is STUCK for every claim (true or false) and its exit
#   code discriminates NOTHING — the gate screens exactly that as
#   `witness-undecided`. Hence every reject case names an explicit
#   `witness_reference` (`_REF_LOOPFREE`, the verifying loop-free
#   `pos-control-direct` impl of the same frozen spec), against which the
#   witnesses fail SEMANTICALLY. No witness binds a hypothesis, so no consistency
#   probe is needed. All seven measured with scripts/lean_verify.sh: rival exit 0;
#   `_REF_LOOPFREE` exit 1 with "`decide` proved that the proposition ... is
#   false"; gold exit 1 with "did not reduce to `isTrue` or `isFalse`" (which is
#   why gold is not the subject). All three positives verify (exit 0).
AXIOM_TESTS = []
