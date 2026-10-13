"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-10614 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant sharing the FROZEN spec byte-for-byte (region surgery:
only text inside ``-- impl-start``/``-- impl-end`` — and, for a case that
legitimately re-proves, inside ``-- proof-start``/``-- proof-end`` — is changed,
so ``markers.same_spec`` holds and the single ``theorem correct_buildUrls``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff the file
elaborates with the obligation closed and no new
``axiom``/``theorem``/``sorry``/``native_decide``; ``expect:"reject"`` passes iff
it does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a fresh battery.
The nagini bundle splits the modeled behavior into THREE pure value functions
over ``List[int]`` code points (a destination-URL identity, a
document-name-plus-anchor concatenation, and a trailing-component key
derivation), each with its own contract. This Lean bundle models the SAME
behavior as ONE function over a structured carrier: ``buildUrls`` maps a
format-selecting flag, the current document name, and an ordered list of
``Xref`` records to the ordered link map. The three nagini surfaces are the three
legs of ``entryFor`` here, so every nagini case carries over as an attack on one
of those legs, or as a correct positive; each case's own ``rationale`` names the
nagini case it ports, and the two nagini classes that are legitimately dropped
(the frame-mutation lane and the axiom lane) are dispositioned at the end of this
docstring.

DEFENDED SURFACE (one obligation, ``correct_buildUrls``).
``problem_spec_buildUrls isSVG currentFilename children result`` pins result to
``children.filterMap (entryFor isSVG currentFilename)`` — a single equation whose
right-hand side has FIVE independent behavioral commitments, each attacked below:

  * (C0 traversal) exactly the in-order per-reference contributions, one list
    entry per contributing reference, nothing added and nothing dropped — and in
    the references' OWN order, which the carrier records faithfully;
  * (C1 destination URL) a reference with a destination URI records that URI
    EXACTLY, for BOTH image formats — no prefix, and not some other string;
  * (C2 destination key) that entry is keyed by the reference title when the
    reference resolves inside this project, and by the trailing component of the
    URI after its final fragment separator when it targets a separate project;
  * (C3 anchor link) a reference with only an in-page anchor records the current
    document name followed by the anchor for the scalable-vector format, keyed by
    the reference TITLE (not by the anchor identifier);
  * (C4 format pivot) and a pure in-page anchor for the inline raster format;
  * (C5 empty contribution) a reference carrying neither field contributes
    nothing;
  * (C6 arm order) and the destination-URI leg WINS over the anchor leg when a
    reference carries both, so which link kind is recorded is pinned too.

BINDER STRUCTURE. The spec predicate binds ``isSVG``, ``currentFilename`` and
``children`` (whose element carrier binds ``refuri``, ``refid``, ``reftitle`` and
``internal``). All are load-bearing and all are VARIED across the reject
witnesses: ``isSVG`` is probed at BOTH values; ``currentFilename`` at
``"index.html"`` and at three distinct nested names; ``children`` at
length 1 and 2; ``internal`` at both values (including both within one input);
and ``refuri``/``refid`` at ``some`` and ``none`` INDEPENDENTLY — including the
combination where both are ``some``, which pins the arm order (C6). The thirteen
reject witnesses probe thirteen distinct input points; no two rivals are refuted
at the same input, so each ``rationale``'s claimed sub-domain is demonstrated at a
point of its own. See the POINT SPREAD table at the end of this file.

Two of those points are new in the second audit pass, which measured that two
independent commitments of the frozen equation were stated by the spec and
demonstrated by no rival. (i) The traversal's ORDER: every shipped multi-reference
witness separated its rival by list LENGTH, so a rival that keeps every entry and
merely reverses them was unattacked — ``reversed-traversal-order`` closes it.
(ii) The anchor entry's KEY: every shipped anchor rival edited the link STRING and
left the key alone, and every shipped anchor witness used a reference whose title
and anchor identifier are the SAME string, so nothing pinned the key to the title
rather than to the identifier — ``anchor-keyed-by-identifier`` closes it, at an
input where the two differ.

WITNESSES — and what the carrier does and does not compute. On a tactic-proof
backend "did not verify" is the DEFAULT outcome of reshaping an implementation
(the frozen proof is tuned to the frozen syntactic form), so a rejection alone
attributes nothing to the spec. Every ``expect="reject"`` case therefore carries
a Lean snippet stating the spec's negation at one concrete input, checked by two
real ``lake env lean`` builds to HOLD of its rival and to FAIL on the frozen
solution.

Ten witnesses close by ``decide``: the imperative ``Id.run do``/``for`` loop and
``List.filterMap`` both reduce at ground list literals, and ``String``
concatenation and equality are decidable, so the entire equation computes —
PROVIDED the key of every entry in play is a title rather than a derived trailing
component. Keeping a witness's references INTERNAL is what buys that, and it is
free: a rival that errs on the URL, the link shape, the anchor key, the arm order,
the traversal order or length, or the empty contribution is refutable at an
internal reference, because none of those legs depends on how a separate-project
key is derived. One further witness
is ground but must NOT use ``decide``: its input deliberately carries a
separate-project reference (the point is that the entry is DROPPED), so ``decide``
would get stuck on the irreducible key term and the gold-side build would fail
without deciding anything — a refutation that was never performed. It is closed by
a ``simp only`` set that reduces the loop and ``filterMap`` to normal form and
discharges the goal on the list's CONS structure, never evaluating the opaque key.

Only the two rivals whose error IS the key derivation must condition on the
carrier instead of computing it. The trailing-component helper is defined through
``String.splitOn``, whose worker ``String.splitOnAux`` is ``@[irreducible]`` in
this toolchain: measured here, ``decide``, ``decide +kernel``, ``rfl``,
``simp [String.splitOn]``, ``unseal String.splitOnAux`` and ``norm_num`` ALL fail
to evaluate even ``"a#b".splitOn "#"`` (``decide`` reports reduction "stuck at the
``Decidable`` instance"; ``simp`` loops to a ``whnf`` heartbeat timeout). So no
literal input decides the key-derivation leg. Rather than drop those two rivals,
each is refuted at a point described by ONE hypothesis separating the helper's
value from the constant its rival substitutes — a strictly stronger claim than any
single literal could make ("wherever the trailing component differs from the
title, the rival's key differs from the spec's"). Each such witness binds exactly
ONE hypothesis about ONE term, so its assumptions are trivially jointly
satisfiable; the gate's ``consistency_probe`` was run against both and failed to
derive ``False`` from either, as required.

A conditioned witness of this shape carries a trap that the gate's two builds
cannot see, and it is the reason the two ``simp only`` sets below carry
``if_false`` and ``Bool.false_eq_true``. The hypothesis is consumed by
``exact absurd h.symm hkey``, which requires the goal to have been normalised to
the bare key equation FIRST. If the ``internal`` conditional is left unreduced,
``hkey`` is matched against a goal still carrying the ``if`` and the script fails
on gold with an application type mismatch — a SYNTACTIC failure that looks exactly
like a refutation to the gate (rival 0, gold 1) while attesting to nothing. It was
measured: with the reducing lemmas omitted, a FORGERY asserting the rival is
correct at an agreement point fails with the byte-identical error, so the gold-side
exit code carried no information. Both key witnesses therefore reduce the
conditional explicitly, and the gold-side failure is a genuine ``h : True`` —
``simp`` PROVED the key equation for the frozen solution and could not for the
rival, which is the strongest gold-side evidence available.

REFINEMENT DISCIPLINE. Every reject case's ``refinement`` argues from the actual
observable pipeline, which was traced end-to-end for this port rather than
assumed. Two facts govern it and both PRUNED candidate rivals from this battery:
(a) for the scalable-vector format the emitted document is
written into the image directory and a downstream step re-expresses each RELATIVE
link so that it is resolved against that directory, so an extra leading ``../``
becomes a doubled climb that escapes the output tree entirely — which is exactly
what the F2P scalable-vector assertion detects when it requires each relative
link to name an existing document; and (b) a diagram node is matched against the
link map by its FULLY-QUALIFIED class name, while a reference sourced from a
separate project carries a title of the form ``(in <project> v<version>)`` — so a
key derived from the title never matches that node, it silently receives no link,
and the F2P assertion requiring the separate project's absolute URL to appear in
the rendered diagram fails. Every reject case's non-resolution argument rests on
(a), on (b), or on a link that names a document that does not exist.

DISPOSITION of every nagini case, so that "ported" is a checkable claim rather
than a summary. Ported: pos-control-destination and pos-control-external-key ->
the two ``soundness`` positives; admiss-external-key -> the admissibility case;
prefix-dotdot-destination -> svg-prefix-destination (and its both-formats
neighbour); prefix-dotdot-self-doc -> svg-prefix-anchor;
partial-domain-external-key-wholeuri -> whole-uri-key-separate-project (with
title-key-every-destination as its total-error neighbour).

Dropped, with the reason each drop is a fact about the carrier and not a
convenience:

  * frame-mut-destination, frame-mut-self-doc, frame-mut-external-key are
    INEXPRESSIBLE here, and the reason is visible in the rivals themselves: each
    differs from its correct sibling ONLY by a write to a parameter held at
    fractional permission (e.g. ``dest_uri[i] = dest_uri[i]``, a SELF-assignment
    that changes no value). Nagini rejects them on the permission discipline
    while every postcondition still holds. This carrier is referentially
    transparent — ``children`` is an immutable ``List Xref``, there is no
    permission to violate, and the corresponding Lean edit is literally a no-op
    that would ELABORATE, i.e. it could only be filed ``expect="verify"``, which
    attests to nothing. There is no analogue to port, so none is faked.

  * partial-domain-destination-dropslast is EXPRESSIBLE here and is NOT claimed
    otherwise: ``uri.dropRight 1`` reproduces its one-short loop literally, and
    it was built during the audit of this file — the rival fails to verify and a
    ground witness separates it from the frozen solution. It is nonetheless not
    shipped, because its refutation is subsumed: it errs on the recorded URL, the
    clause C1 that svg-prefix-destination, prefix-destination-both-formats and
    url-is-title already attack, and it is refuted by the same ground computation
    at an input those cases already occupy. What the nagini case contributes that
    is NOT otherwise covered is its partial-domain SHAPE (correct on short
    inputs, wrong on long ones), and that shape is ported — onto the binder this
    spec actually quantifies over — by first-reference-only, which is correct on
    every one-reference diagram and wrong beyond. Recorded here as a deliberate
    subsumption rather than an omission, so the choice can be reversed by anyone
    who disagrees.

DIVERGENCE lane: VACUOUS on this carrier, demonstrated rather than asserted. The
frozen solution sets no ``loom.semantics.termination`` option — it is a plain Lean
``def`` over a ``List``, so the elaborator itself discharges termination and there
is no partial-semantics escape. Measured: a rival whose loop body carries no
decreasing measure does not merely fail the frozen proof, it fails to DEFINE, with
``fail to show termination for implementation_buildUrls.spin`` — so the surgery
never produces a file in which the obligation is even stated, and no witness can
be built against it (the witness build against such a rival exits 1 on the
definition, not on the claim, which the gate would read as ``witness-unproven``).
The only way to obtain a diverging implementation here is ``partial def``, which
``variant_scope`` does not ban but which ``pbt_witness`` bans inside a witness, and
which in any case makes the rival's body opaque rather than non-terminating: the
frozen ``for`` over an immutable ``List Xref`` has no unbounded loop to corrupt.
That is a fact about the carrier and not about the difficulty of the proof, so this
class is recorded VACUOUS (the battery is complete without it), not as a known
hole.

AXIOM lane: EMPTY. ``meta.axioms == []``; the bundle declares no ``opaque``
callee and consumes no ``axiom`` (the string operations are modeled deeply), so
the nagini ``AXIOM_TESTS`` (ax-sound-deepmodels, ax-contain-deepmodels) have no
subject on this side. That lane is G-AX's job and this gate ignores it.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10614"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it edits and is unique in
# Solution.lean (both invariants are re-checked by _swap on every import, so the
# manifest breaks loudly if the frozen solution ever drifts).
# ---------------------------------------------------------------------------

# --- impl region -----------------------------------------------------------
# The destination-URI arm of the loop body: chooses the key, then records the
# entry. Load-bearing for C1 (the recorded URL) and C2 (the key).
_I_URI_ARM = """        let mut refname := child.reftitle
        if !child.internal then
          refname := uriTail uri
        urls := urls ++ [(refname, uri)]"""

# The in-page-anchor arm: the format pivot. Load-bearing for C3 and C4.
_I_ANCHOR_ARM = """            if isSVG then
              urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
            else
              urls := urls ++ [(child.reftitle, "#" ++ rid)]"""

# The arm for a reference carrying neither field. Load-bearing for C5.
_I_EMPTY_ARM = """        | none => pure ()"""

# The loop header, for a rival that changes the traversal itself (C0).
_I_LOOP_HEAD = """  let mut urls : List (String × String) := []
  for child in children do"""

# The WHOLE loop, for a rival that reorders the two arms rather than editing one
# (the arm-precedence attack: which leg wins when a reference carries both a
# destination URI and an in-page anchor).
_I_FULL_LOOP = """  let mut urls : List (String × String) := []
  for child in children do
    match child.refuri with
    | some uri =>
        let mut refname := child.reftitle
        if !child.internal then
          refname := uriTail uri
        urls := urls ++ [(refname, uri)]
    | none =>
        match child.refid with
        | some rid =>
            if isSVG then
              urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
            else
              urls := urls ++ [(child.reftitle, "#" ++ rid)]
        | none => pure ()
  return urls"""

# --- proof region ----------------------------------------------------------
# `desugar_to_foldl` states the loop body TWICE (once in `hbody`, once in the
# `suffices`), each time in the elaborator's normalized form. A positive whose
# impl reshapes that body must reshape both statements to match, so each is
# anchored with enough surrounding context to be unique.
_P_HBODY_URI = """      (fun (child : Xref) (r : List (String × String)) =>
          match child.refuri with
          | some uri =>
            if (!child.internal) = true then ForInStep.yield (r ++ [(uriTail uri, uri)])
            else ForInStep.yield (r ++ [(child.reftitle, uri)])"""
_P_SUFFICES_URI = """      (forIn (m := Id) children init fun child r =>
          match child.refuri with
          | some uri =>
            if (!child.internal) = true then ForInStep.yield (r ++ [(uriTail uri, uri)])
            else ForInStep.yield (r ++ [(child.reftitle, uri)])"""

_P_HBODY_ANCHOR = """            match child.refid with
            | some rid =>
              if isSVG = true then ForInStep.yield (r ++ [(child.reftitle, currentFilename ++ "#" ++ rid)])
              else ForInStep.yield (r ++ [(child.reftitle, "#" ++ rid)])
            | none => ForInStep.yield r)
        = (fun (child : Xref) (r : List (String × String)) =>"""
_P_SUFFICES_ANCHOR = """            match child.refid with
            | some rid =>
              if isSVG = true then ForInStep.yield (r ++ [(child.reftitle, currentFilename ++ "#" ++ rid)])
              else ForInStep.yield (r ++ [(child.reftitle, "#" ++ rid)])
            | none => ForInStep.yield r)
        = List.foldl"""

# The frozen proof's `intro` line, so the admissibility positive can prepend a
# ground `have` without touching the theorem STATEMENT or the spec view.
_P_INTRO = """  intro isSVG currentFilename children
  unfold problem_spec_buildUrls"""


# ===========================================================================
# 1. POSITIVE CONTROLS (soundness / admissibility, expect verify)
#
#    Structurally different but CORRECT implementations that keep the
#    obligation's STATEMENT byte-identical and re-prove it honestly. Ports the
#    nagini "local-variable reshape" positives (pos-control-destination,
#    pos-control-external-key), whose whole point there was that a reshaped-but-
#    correct implementation must still satisfy the contract. If one of these
#    fails => SPEC-TOO-STRONG.
# ===========================================================================

# pos-key-as-expression: the key is bound by a single conditional EXPRESSION
# rather than by a mutable local overwritten in a branch. Observationally
# identical; a genuinely different syntactic shape, so the frozen `desugar`
# bridge must be re-stated for the new loop body (done below, inside the proof
# region) — the proof closes for the NEW impl, it is not weakened.
POS_KEY_EXPR = {
    "id": "pos-key-as-expression",
    "kind": "soundness",
    "expect": "verify",
    "module": _swaps(
        _BASE,
        (_I_URI_ARM,
         """        let refname := if child.internal then child.reftitle else uriTail uri
        urls := urls ++ [(refname, uri)]"""),
        (_P_HBODY_URI,
         """      (fun (child : Xref) (r : List (String × String)) =>
          match child.refuri with
          | some uri =>
            ForInStep.yield (r ++ [((if child.internal then child.reftitle else uriTail uri), uri)])"""),
        (_P_SUFFICES_URI,
         """      (forIn (m := Id) children init fun child r =>
          match child.refuri with
          | some uri =>
            ForInStep.yield (r ++ [((if child.internal then child.reftitle else uriTail uri), uri)])"""),
    ),
    "rationale": (
        "SOUNDNESS. A structurally different but CORRECT implementation — the "
        "destination-URI arm selects its key with one conditional expression "
        "instead of writing a mutable local in a branch — must still satisfy "
        "the single postcondition equation, since it computes the same key for "
        "both values of `internal` and records the same URL. The obligation's "
        "STATEMENT is byte-identical and the proof is genuinely re-derived for "
        "the new loop body (the `desugar_to_foldl` bridge is re-stated to the "
        "reshaped body; no lemma is added, nothing is assumed). If this fails "
        "=> SPEC-TOO-STRONG: the spec would be pinning a syntactic shape rather "
        "than the behavior, and an honest consumer implementation would be "
        "rejected. Ports nagini's pos-control-destination local-variable "
        "reshape onto this carrier."),
}


# pos-anchor-shared-suffix: the in-page-anchor arm factors the format pivot into
# the PREFIX only, then appends the separator and identifier once for both
# formats — using that the raster form is the scalable-vector form with an empty
# document name. Correct, and a different branch structure.
POS_ANCHOR_PREFIX = {
    "id": "pos-anchor-shared-suffix",
    "kind": "soundness",
    "expect": "verify",
    "module": _swaps(
        _BASE,
        (_I_ANCHOR_ARM,
         """            let base := if isSVG then currentFilename else ""
            urls := urls ++ [(child.reftitle, base ++ "#" ++ rid)]"""),
        (_P_HBODY_ANCHOR,
         """            match child.refid with
            | some rid =>
              ForInStep.yield (r ++ [(child.reftitle, (if isSVG = true then currentFilename else "") ++ "#" ++ rid)])
            | none => ForInStep.yield r)
        = (fun (child : Xref) (r : List (String × String)) =>"""),
        (_P_SUFFICES_ANCHOR,
         """            match child.refid with
            | some rid =>
              ForInStep.yield (r ++ [(child.reftitle, (if isSVG = true then currentFilename else "") ++ "#" ++ rid)])
            | none => ForInStep.yield r)
        = List.foldl"""),
    ),
    "rationale": (
        "SOUNDNESS on the format-pivot legs (C3/C4). The anchor arm branches on "
        "the format flag for the PREFIX only and then appends the separator and "
        "the identifier once, exploiting that the inline-raster form is the "
        "scalable-vector form with an empty document name. Both legs are "
        "unchanged observationally, so both C3 and C4 must still hold; the "
        "obligation STATEMENT is byte-identical and the proof is re-derived for "
        "the reshaped body. If this fails => SPEC-TOO-STRONG on the pivot: the "
        "spec would forbid a correct factoring of the two arms. This is the "
        "second nagini local-variable-reshape positive "
        "(pos-control-external-key) re-expressed on the leg this bundle models "
        "as one function."),
}


# admiss-multi-reference-diagram: the gold implementation and gold proof, with a
# ground `have` prepended INSIDE the proof region that discharges the obligation
# at one normal F2P-shaped input — a diagram carrying both a destination-URI
# reference and an in-page-anchor reference, rendered in the scalable-vector
# format from a nested document. Confirms the modeled domain is inhabited by the
# shape the F2P test exercises.
ADMISS_MULTI = {
    "id": "admiss-multi-reference-diagram",
    "kind": "admissibility",
    "expect": "verify",
    "module": _swap(
        _BASE, _P_INTRO,
        """  -- admissibility: the obligation is inhabited at a normal, F2P-shaped
  -- multi-reference diagram — one reference resolving to another document and
  -- one resolving to an in-page anchor — rendered in the scalable-vector format
  -- from a nested document. A ground instance of the very statement below.
  have hInDomain : problem_spec_buildUrls true "subdir/index.html"
      [{ refuri := some "index.html#test.DocHere", refid := none,
         reftitle := "test.DocHere", internal := true },
       { refuri := none, refid := some "test.DocLowerLevel",
         reftitle := "test.DocLowerLevel", internal := true }]
      [("test.DocHere", "index.html#test.DocHere"),
       ("test.DocLowerLevel", "subdir/index.html#test.DocLowerLevel")] := by
    unfold problem_spec_buildUrls
    decide
  intro isSVG currentFilename children
  unfold problem_spec_buildUrls""",
    ),
    "rationale": (
        "ADMISSIBILITY. `correct_buildUrls` binds its inputs universally with NO "
        "narrowing hypothesis, so the analogue of nagini's "
        "Requires-admits-a-real-input check is that the obligation is "
        "SATISFIABLE at a normal input rather than only vacuously provable. The "
        "ground `have` discharges the spec, by computation, at an F2P-shaped "
        "two-reference diagram in the scalable-vector format from a nested "
        "document — exercising the destination-URI leg and the anchor leg "
        "together with a non-trivial `currentFilename`. It closes by `decide`, "
        "so it is a real computation, not an appeal to the theorem it precedes. "
        "If it could not be established => PRECOND-TOO-STRONG / the spec is "
        "unsatisfiable on the modeled domain. Ports nagini's "
        "admiss-external-key (a harmless in-domain assertion added inside the "
        "implementation region, all gold obligations kept)."),
}


# ===========================================================================
# 2. ATTACKS on C1 / C4 — the recorded destination URL (uniqueness, reject)
#
#    The nagini prefix-dotdot-destination and prefix-dotdot-self-doc rivals,
#    re-expressed on this carrier. On this backend the two nagini functions are
#    the two arms of one loop, so the prefix attack lands twice: once on the
#    destination URL and once on the anchor link.
# ===========================================================================

# svg-prefix-destination: prepend "../" to the destination URL in the
# scalable-vector format ONLY. The near-miss of the pair below: it agrees with
# the frozen behavior on the inline-raster format, so it is refuted at the
# scalable-vector point where it is actually wrong.
REJ_SVG_PREFIX_URI = {
    "id": "svg-prefix-destination",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_URI_ARM,
        """        let mut refname := child.reftitle
        if !child.internal then
          refname := uriTail uri
        if isSVG then
          urls := urls ++ [(refname, "../" ++ uri)]
        else
          urls := urls ++ [(refname, uri)]"""),
    "rationale": (
        "Attacks C1 (the recorded destination URL is that URI EXACTLY, for BOTH "
        "image formats) at the `isSVG = true` point. The rival records "
        "`\"../\" ++ uri`, so its entry differs from `entryFor`'s in the second "
        "component for every destination URI, and the single postcondition "
        "equation fails. Deliberately a NEAR-MISS: it agrees with the frozen "
        "behavior on the whole `isSVG = false` half of the domain, which is why "
        "its witness is stated at `isSVG = true` — the sub-domain the rationale "
        "claims — rather than shared with the unconditional variant below. If it "
        "verifies => SPEC-TOO-WEAK: the spec would not pin the URL for the "
        "scalable-vector format."),
    "refinement": (
        "A faithful patch that prefixes the scalable-vector destination link "
        "with `../` would NOT resolve. The emitted scalable-vector document is "
        "written into the image directory, and a downstream step re-expresses "
        "each RELATIVE link so that it resolves against that directory; a link "
        "that already carries a leading `../` is therefore climbed TWICE and "
        "names a path outside the output tree. The F2P scalable-vector test "
        "resolves every relative link it finds against the image directory and "
        "asserts the named document EXISTS, which a doubly-climbed path does "
        "not — the reported 404 symptom, reproduced as a test failure. So a "
        "verifying rival here would be a true verify-does-not-imply-resolve "
        "break."),
    "witness": r'''
-- The scalable-vector format, one reference resolving into this project by
-- title. Fully ground: the loop, `filterMap` and string equality all compute.
example : ¬ problem_spec_buildUrls true "index.html"
    [{ refuri := some "index.html#test.DocHere", refid := none,
       reftitle := "test.DocHere", internal := true }]
    (implementation_buildUrls true "index.html"
      [{ refuri := some "index.html#test.DocHere", refid := none,
         reftitle := "test.DocHere", internal := true }]) := by
  unfold problem_spec_buildUrls
  decide
''',
}


# prefix-destination-both-formats: prepend "../" to the destination URL for BOTH
# formats. Strictly wrong on more of the domain than the near-miss above, and
# refuted at an inline-raster, separate-project point — where the near-miss is
# CORRECT, so the two witnesses genuinely separate the two rivals.
REJ_PREFIX_URI_BOTH = {
    "id": "prefix-destination-both-formats",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_URI_ARM,
        """        let mut refname := child.reftitle
        if !child.internal then
          refname := uriTail uri
        urls := urls ++ [(refname, "../" ++ uri)]"""),
    "rationale": (
        "Attacks C1 again, but on the OTHER side of the format pivot: the rival "
        "prefixes unconditionally, so it is wrong at `isSVG = false` too — "
        "exactly where `svg-prefix-destination` agrees with the frozen "
        "behavior. Its witness is therefore stated at `isSVG = false` on a "
        "reference resolving INSIDE this project from a nested document, an "
        "input the other prefix rival satisfies; that separation is what makes "
        "each rival's claimed sub-domain demonstrated rather than merely "
        "asserted. The witness is fully GROUND: keeping the reference internal "
        "keys it by the title, so the trailing-component helper (which does not "
        "evaluate on this carrier — see the module docstring) never enters the "
        "goal and the whole equation computes. If it verifies => SPEC-TOO-WEAK: "
        "the spec would leave the recorded URL free of the input URI."),
    "refinement": (
        "The faithful patch prefixes every destination link, so it fails the "
        "F2P scalable-vector test for the same doubled-climb reason as the "
        "format-gated variant (the relative link is climbed once by the patch "
        "and again by the downstream re-expression, naming a document that does "
        "not exist). It additionally corrupts links whose destination is an "
        "ABSOLUTE URL into a project-relative path — the F2P test requires every "
        "link containing a scheme separator to begin with the separate "
        "project's absolute URL, and a `../`-prefixed absolute URL neither "
        "begins with it nor survives the relative-link re-expression. Wrong on "
        "strictly more of the F2P domain than the gated variant, and does not "
        "resolve."),
    "witness": r'''
-- The inline-raster format, a NESTED current document name, and a reference
-- resolving INSIDE this project: the point where `svg-prefix-destination` is
-- correct (it prefixes only the scalable-vector format) and this rival is not.
-- Keeping the reference internal keys it by the title, so the trailing-component
-- helper — the one term this carrier will not evaluate — never enters the goal
-- and the whole equation is decided by computation, no hypothesis needed.
example : ¬ problem_spec_buildUrls false "subdir/index.html"
    [{ refuri := some "index.html#test.DocHere", refid := none,
       reftitle := "test.DocHere", internal := true }]
    (implementation_buildUrls false "subdir/index.html"
      [{ refuri := some "index.html#test.DocHere", refid := none,
         reftitle := "test.DocHere", internal := true }]) := by
  unfold problem_spec_buildUrls
  decide
''',
}


# svg-prefix-anchor: prepend "../" to the in-page-anchor link in the
# scalable-vector arm. The nagini prefix-dotdot-self-doc rival.
REJ_SVG_PREFIX_ANCHOR = {
    "id": "svg-prefix-anchor",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_ANCHOR_ARM,
        """            if isSVG then
              urls := urls ++ [(child.reftitle, "../" ++ currentFilename ++ "#" ++ rid)]
            else
              urls := urls ++ [(child.reftitle, "#" ++ rid)]"""),
    "rationale": (
        "Attacks C3 (the anchor link for the scalable-vector format is the "
        "current document name followed by the anchor). The rival records "
        "`\"../\" ++ currentFilename ++ \"#\" ++ rid`, which differs from the "
        "spec's entry for every input, so the postcondition fails. Its "
        "refutation DEPENDS on `currentFilename` (as does `format-pivot-swapped`'s: "
        "both rivals agree with the frozen behavior at the empty document name, "
        "measured), and it is "
        "stated at a NESTED document name (`\"subdir/index.html\"`) rather than "
        "a root one, so the binder is probed where the leading-prefix error is "
        "observable rather than at a value that would mask it. If it verifies => "
        "SPEC-TOO-WEAK: the spec would not pin the anchor link's prefix. Ports "
        "nagini's prefix-dotdot-self-doc."),
    "refinement": (
        "The faithful patch prefixes the in-page-anchor link for the "
        "scalable-vector format. That link is relative, so the downstream "
        "re-expression against the image directory climbs it a SECOND time and "
        "the result names a document above the output tree; the F2P "
        "scalable-vector test resolves each relative link against the image "
        "directory and asserts existence, which fails. This is the reported "
        "symptom for a reference resolving to an anchor in the document being "
        "rendered, and it is precisely what the F2P test was rewritten to "
        "detect — the faithful patch does not resolve."),
    "witness": r'''
-- The scalable-vector format, an in-page-anchor reference, and a NESTED current
-- document name — the only binder point at which this rival's prefix error is
-- distinguishable from a root-document one.
example : ¬ problem_spec_buildUrls true "subdir/index.html"
    [{ refuri := none, refid := some "test.DocLowerLevel",
       reftitle := "test.DocLowerLevel", internal := true }]
    (implementation_buildUrls true "subdir/index.html"
      [{ refuri := none, refid := some "test.DocLowerLevel",
         reftitle := "test.DocLowerLevel", internal := true }]) := by
  unfold problem_spec_buildUrls
  decide
''',
}


# url-is-title: the recorded URL is the key rather than the destination URI. A
# blunt C1 attack that the identity clause must reject outright.
REJ_URL_IS_TITLE = {
    "id": "url-is-title",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_URI_ARM,
        """        let mut refname := child.reftitle
        if !child.internal then
          refname := uriTail uri
        urls := urls ++ [(refname, refname)]"""),
    "rationale": (
        "Attacks C1 at its root: the rival records the KEY as the URL, "
        "discarding the destination URI entirely. This is the analogue of "
        "nagini's identity-postcondition check "
        "(`ToSeq(Result()) == ToSeq(dest_uri)`) — the clause that says the "
        "recorded URL is the input URI and not some other string derived from "
        "the same reference. Refuted at an internal destination-URI reference "
        "with `isSVG = true`, an input point no other rival uses. If it verifies "
        "=> SPEC-TOO-WEAK: the recorded URL would be unconstrained by the input "
        "URI, which is the frame hole SPEC_GUIDE directive 5 warns about (an "
        "output component left free)."),
    "refinement": (
        "A faithful patch recording the reference title where the destination "
        "link belongs emits a link naming a bare class name. That is a relative "
        "link, so the F2P scalable-vector test resolves it against the image "
        "directory and asserts the named document exists; no document by that "
        "name exists, and the assertion fails. The patch does not resolve."),
    "witness": r'''
-- An internal reference resolving to another document, scalable-vector format:
-- the recorded URL and the key are DIFFERENT strings here, so collapsing them
-- is observable by computation.
example : ¬ problem_spec_buildUrls true "index.html"
    [{ refuri := some "subdir/index.html#test.DocLowerLevel", refid := none,
       reftitle := "test.DocLowerLevel", internal := true }]
    (implementation_buildUrls true "index.html"
      [{ refuri := some "subdir/index.html#test.DocLowerLevel", refid := none,
         reftitle := "test.DocLowerLevel", internal := true }]) := by
  unfold problem_spec_buildUrls
  decide
''',
}


# ===========================================================================
# 3. ATTACKS on C2 — the destination-URI KEY (uniqueness, reject)
#
#    The nagini partial-domain-external-key-wholeuri rival and its neighbours.
#    This leg is the one the carrier will not compute (the trailing-component
#    helper is irreducible here), so all three witnesses condition on it.
# ===========================================================================

# title-key-every-destination: key EVERY destination URI by the reference title,
# dropping the separate-project distinction entirely.
REJ_TITLE_KEY_ALL = {
    "id": "title-key-every-destination",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_URI_ARM,
        """        let refname := child.reftitle
        urls := urls ++ [(refname, uri)]"""),
    "rationale": (
        "Attacks C2 (a reference targeting a SEPARATE project is keyed by the "
        "trailing component of its URI, not by its title). The rival ignores "
        "`internal` altogether and always keys by the title, so it is correct on "
        "the whole `internal = true` half and wrong on the other half — the "
        "partial-domain shape nagini's key rivals attack. `internal` is the "
        "binder this case exists to move: refuted at `internal = false`, where a "
        "rival that mishandled only this input would otherwise slip through. The "
        "trailing component does not evaluate on this carrier, so the refutation "
        "is conditioned on ONE hypothesis separating it from the title — a "
        "stronger claim than any literal: wherever the two differ, the rival's "
        "key differs from the spec's. If it verifies => SPEC-TOO-WEAK: the spec "
        "would not pin the separate-project key."),
    "refinement": (
        "The faithful patch keys every destination reference by its title. A "
        "diagram node is matched against the link map by its FULLY-QUALIFIED "
        "class name, while a reference resolved from a separate project carries "
        "a title of the form `(in <project> v<version>)` — never a class name. "
        "So the separate-project node matches nothing, receives no link at all, "
        "and the separate project's absolute URL never appears in the rendered "
        "diagram. The F2P scalable-vector test asserts that URL IS present "
        "whenever the diagram mentions the separate project, so the faithful "
        "patch does not resolve — it is the missing-link half of the reported "
        "issue."),
    "witness": r'''
-- A separate-project reference whose title is NOT its class name. One
-- hypothesis, about the one term the carrier will not evaluate: the trailing
-- component of this URI differs from this title. Wherever that holds, the
-- rival's key is wrong.
example (hkey : uriTail "https://example.org/foo.html#subdir.other.Bob"
                  ≠ "subdir.other.Bob (in subdir v1.0)") :
    ¬ problem_spec_buildUrls true "index.html"
      [{ refuri := some "https://example.org/foo.html#subdir.other.Bob",
         refid := none, reftitle := "subdir.other.Bob (in subdir v1.0)",
         internal := false }]
      (implementation_buildUrls true "index.html"
        [{ refuri := some "https://example.org/foo.html#subdir.other.Bob",
           refid := none, reftitle := "subdir.other.Bob (in subdir v1.0)",
           internal := false }]) := by
  unfold problem_spec_buildUrls implementation_buildUrls entryFor
  -- The `if_false`/`Bool.false_eq_true` pair is load-bearing, not decoration:
  -- without it the `internal`-conditional stays UNREDUCED on both sides, `hkey`
  -- is then matched against a goal still carrying the `if`, and the script fails
  -- with an application type mismatch on gold for a purely syntactic reason —
  -- a failure that is not a refutation and discriminates nothing.
  simp only [Id.run, List.forIn_cons, List.forIn_nil, List.nil_append,
    List.filterMap_cons, List.filterMap_nil, bind, pure, Id.instMonad,
    Bool.not_false, if_true, if_false, Bool.false_eq_true,
    List.cons.injEq, Prod.mk.injEq, and_true, not_and, ne_eq]
  intro h
  exact absurd h.symm hkey
''',
}


# whole-uri-key-separate-project: for a separate-project reference use the WHOLE
# URI as the key instead of its trailing component. The direct port of nagini's
# partial-domain-external-key-wholeuri (its model_prepatch_3 behavior).
REJ_WHOLE_URI_KEY = {
    "id": "whole-uri-key-separate-project",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_URI_ARM,
        """        let mut refname := child.reftitle
        if !child.internal then
          refname := uri
        urls := urls ++ [(refname, uri)]"""),
    "rationale": (
        "Attacks C2 at the point nagini's partial-domain rival attacks it: the "
        "separate-project branch IS taken (so `internal` is honoured, unlike "
        "`title-key-every-destination`) but the key is the whole URI rather than "
        "its trailing component. Correct exactly on URIs carrying no fragment "
        "separator, wrong on every URI that carries one — the partial-domain "
        "sub-domain. Refuted at `isSVG = false` on a nested document, an input "
        "point distinct from every other witness's; conditioned on the single "
        "irreducible term, asserting only that the trailing component of this "
        "URI differs from the whole URI. If it verifies => SPEC-TOO-WEAK: the "
        "spec would admit an unstripped key."),
    "refinement": (
        "The faithful patch registers the separate-project reference under its "
        "full absolute URL. Node matching is by fully-qualified class name, so a "
        "key that is a URL matches no node; the separate-project node receives "
        "no link and that project's absolute URL is absent from the rendered "
        "diagram, failing the F2P assertion that it be present. This is the "
        "pre-existing behavior for the separate-project reference the F2P test "
        "was rewritten to exercise, so the faithful patch does not resolve."),
    "witness": r'''
-- Inline-raster format, nested document, separate-project reference. The
-- hypothesis says only that this URI's trailing component is not the WHOLE URI
-- (true of any URI carrying a fragment separator) — the sub-domain claimed.
example (hkey : uriTail "https://example.org/foo.html#subdir.other.Bob"
                  ≠ "https://example.org/foo.html#subdir.other.Bob") :
    ¬ problem_spec_buildUrls false "subdir/index.html"
      [{ refuri := some "https://example.org/foo.html#subdir.other.Bob",
         refid := none, reftitle := "subdir.other.Bob (in subdir v1.0)",
         internal := false }]
      (implementation_buildUrls false "subdir/index.html"
        [{ refuri := some "https://example.org/foo.html#subdir.other.Bob",
           refid := none, reftitle := "subdir.other.Bob (in subdir v1.0)",
           internal := false }]) := by
  unfold problem_spec_buildUrls implementation_buildUrls entryFor
  simp only [Id.run, List.forIn_cons, List.forIn_nil, List.nil_append,
    List.filterMap_cons, List.filterMap_nil, bind, pure, Id.instMonad,
    Bool.not_false, if_true, List.cons.injEq, Prod.mk.injEq, and_true,
    not_and, ne_eq, if_false, Bool.false_eq_true]
  intro h
  exact absurd h.symm hkey
''',
}


# ===========================================================================
# 4. ATTACKS on C0 / C5 — the traversal and the empty contribution
#    (uniqueness, reject)
#
#    No nagini counterpart: nagini's three functions each compute ONE string,
#    so the "which references contribute, in what order, how many" commitment
#    exists only on this carrier, where the modeled value is the whole map.
#    Included because C0/C5 are independent top-level commitments of the frozen
#    equation and would otherwise go unattacked.
# ===========================================================================

# separate-project-reference-dropped: a reference targeting a separate project
# contributes nothing.
REJ_DROP_EXTERNAL = {
    "id": "separate-project-reference-dropped",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_URI_ARM,
        """        if child.internal then
          urls := urls ++ [(child.reftitle, uri)]"""),
    "rationale": (
        "Attacks C0 (exactly the in-order per-reference contributions — nothing "
        "DROPPED) on the `internal = false` sub-domain, and C2 with it. The "
        "rival records an entry only for references resolving inside this "
        "project; `filterMap` drops only references carrying neither field, so "
        "the result list is short by one entry and the equation fails. Refuted "
        "at a TWO-reference diagram mixing both values of `internal` — the only "
        "witness of length 2 that varies `internal` within one input, so the "
        "case demonstrates the spec's dependence on the per-element flag and on "
        "list length together. If it verifies => SPEC-TOO-WEAK: the spec would "
        "not require every reference with a destination to be recorded."),
    "refinement": (
        "The faithful patch skips separate-project references entirely, so that "
        "node receives no link and the separate project's absolute URL is absent "
        "from the rendered diagram — the F2P scalable-vector test asserts it is "
        "present whenever the diagram mentions that project, and fails. Strictly "
        "worse than the mis-keying rivals (which at least register a key), and "
        "it does not resolve."),
    "witness": r'''
-- Two references in one diagram, one resolving inside this project and one
-- targeting a separate project. Refuted over the list SHAPE: gold contributes
-- two entries and the rival one, so the equation fails on the CONS structure
-- alone. Deliberately NOT `decide`: the separate-project entry's key is the
-- trailing component, which is irreducible on this carrier, so `decide` would
-- get stuck rather than decide — a gold-side failure that would attest to
-- nothing (the gate screens exactly this as `witness-undecided`). The `simp only`
-- set reduces the loop and `filterMap` to normal form and closes on the
-- constructor mismatch, never evaluating the opaque key.
example : ¬ problem_spec_buildUrls true "index.html"
    [{ refuri := some "subdir/index.html#test.DocLowerLevel", refid := none,
       reftitle := "test.DocLowerLevel", internal := true },
     { refuri := some "https://example.org/foo.html#subdir.other.Bob",
       refid := none, reftitle := "(in subdir v1.0)", internal := false }]
    (implementation_buildUrls true "index.html"
      [{ refuri := some "subdir/index.html#test.DocLowerLevel", refid := none,
         reftitle := "test.DocLowerLevel", internal := true },
       { refuri := some "https://example.org/foo.html#subdir.other.Bob",
         refid := none, reftitle := "(in subdir v1.0)", internal := false }]) := by
  unfold problem_spec_buildUrls implementation_buildUrls entryFor
  simp only [Id.run, List.forIn_cons, List.forIn_nil, List.nil_append,
    List.filterMap_cons, List.filterMap_nil, bind, pure, Id.instMonad,
    if_true, if_false, Bool.not_false, Bool.not_true, Bool.false_eq_true,
    List.cons_append, List.cons.injEq, reduceCtorEq, and_false, false_and,
    not_false_eq_true]
''',
}


# first-reference-only: record only the first contributing reference and skip
# the rest. Correct exactly on single-reference diagrams.
REJ_FIRST_ONLY = {
    "id": "first-reference-only",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_LOOP_HEAD,
        """  let mut urls : List (String × String) := []
  for child in children do
    if !urls.isEmpty then
      continue"""),
    "rationale": (
        "Attacks C0 (the traversal itself) on the length binder. The rival is "
        "correct on EVERY single-reference diagram and on the empty one, and "
        "wrong on every diagram with two or more contributing references — the "
        "partial-domain shape of nagini's "
        "partial-domain-destination-dropslast, whose loop likewise stopped one "
        "short, re-expressed against the list the spec pins rather than against "
        "a character sequence. Refuted at a two-reference diagram in the "
        "inline-raster format, an input point no other witness uses. If it "
        "verifies => SPEC-TOO-WEAK: the spec would not pin the number of "
        "entries, and a truncating implementation would satisfy it."),
    "refinement": (
        "A faithful patch that stops after the first entry leaves every "
        "subsequent node in the diagram unlinked. The diagrams the F2P test "
        "renders carry more than one node — including the one that mentions the "
        "separate project — so the separate project's absolute URL is absent "
        "from the rendered diagram whenever its node is not first, failing the "
        "F2P assertion that requires it; and the remaining nodes silently lose "
        "the links whose correctness the same test checks. The patch does not "
        "resolve."),
    "witness": r'''
-- Two contributing references, inline-raster format. The rival keeps only the
-- first, so the lists differ in LENGTH and the equation is refuted by
-- computation alone.
example : ¬ problem_spec_buildUrls false "index.html"
    [{ refuri := none, refid := some "test.DocHere",
       reftitle := "test.DocHere", internal := true },
     { refuri := some "index.html#test.Foo", refid := none,
       reftitle := "test.Foo", internal := true }]
    (implementation_buildUrls false "index.html"
      [{ refuri := none, refid := some "test.DocHere",
         reftitle := "test.DocHere", internal := true },
       { refuri := some "index.html#test.Foo", refid := none,
         reftitle := "test.Foo", internal := true }]) := by
  unfold problem_spec_buildUrls
  decide
''',
}


# anchor-arm-takes-precedence: when a reference carries BOTH a destination URI
# and an in-page anchor, consult the anchor first. Added by the audit lane: no
# other case in this battery puts both fields at `some` in one reference, so the
# ARM ORDER — which of the two mutually exclusive-looking legs wins when both
# apply — went unattacked while `entryFor` commits to it explicitly.
REJ_ARM_PRECEDENCE = {
    "id": "anchor-arm-takes-precedence",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_FULL_LOOP,
        """  let mut urls : List (String × String) := []
  for child in children do
    match child.refid with
    | some rid =>
        if isSVG then
          urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]
        else
          urls := urls ++ [(child.reftitle, "#" ++ rid)]
    | none =>
        match child.refuri with
        | some uri =>
            let mut refname := child.reftitle
            if !child.internal then
              refname := uriTail uri
            urls := urls ++ [(refname, uri)]
        | none => pure ()
  return urls"""),
    "rationale": (
        "Attacks the ARM ORDER that `entryFor` fixes: the destination-URI leg is "
        "matched FIRST, so a reference carrying both a destination URI and an "
        "in-page anchor is recorded as a document link, never as an anchor. The "
        "rival consults the anchor first, so it is correct on every reference "
        "that carries at most one of the two fields — which is every input the "
        "rest of this battery uses — and wrong exactly when both are present. "
        "That binder combination (`refuri` and `refid` both at `some`) is probed "
        "by NO other witness here, which is why this case exists: without it the "
        "spec's commitment to the leading arm is stated and never demonstrated. "
        "If it verifies => SPEC-TOO-WEAK: the spec would not pin which leg wins "
        "and an implementation could record the wrong kind of link entirely."),
    "refinement": (
        "A faithful patch that consults the anchor before the destination emits "
        "an in-page anchor for a reference that has a resolved destination in "
        "another document. The link then points at an identifier in the CURRENT "
        "page, which does not carry that node, so the cross-document link is "
        "silently replaced by a dead intra-page one; for the scalable-vector "
        "format the F2P test resolves each relative link against the image "
        "directory and asserts the named document exists, and a bare anchor "
        "naming no document fails it. The patch does not resolve."),
    "witness": r'''
-- One reference carrying BOTH a destination URI and an in-page anchor — the
-- binder combination no other witness in this battery reaches. Ground: the key
-- is the title (the reference is internal), so nothing irreducible appears.
example : ¬ problem_spec_buildUrls false "index.html"
    [{ refuri := some "index.html#test.Foo", refid := some "test.Foo",
       reftitle := "test.Foo", internal := true }]
    (implementation_buildUrls false "index.html"
      [{ refuri := some "index.html#test.Foo", refid := some "test.Foo",
         reftitle := "test.Foo", internal := true }]) := by
  unfold problem_spec_buildUrls
  decide
''',
}


# format-pivot-swapped: exchange the two anchor-arm branches. Added by the audit
# lane to attack C4 from the wrong side: every other anchor rival here leaves the
# inline-raster leg intact, so the commitment that the raster link is a PURE
# anchor — with no document name — had no rival of its own.
REJ_PIVOT_SWAPPED = {
    "id": "format-pivot-swapped",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_ANCHOR_ARM,
        """            if isSVG then
              urls := urls ++ [(child.reftitle, "#" ++ rid)]
            else
              urls := urls ++ [(child.reftitle, currentFilename ++ "#" ++ rid)]"""),
    "rationale": (
        "Attacks C4 (the inline-raster anchor link is a PURE in-page anchor, "
        "carrying no document name) together with C3, by exchanging the two "
        "branches of the format pivot. Every other anchor-arm rival here leaves "
        "the raster leg exactly right and errs only on the scalable-vector side, "
        "so C4's own commitment was asserted by the spec and demonstrated by no "
        "rival; this case supplies one. It is not a near-miss — it is wrong at "
        "BOTH values of `isSVG` whenever the document name is non-empty — and it "
        "is refuted on the INLINE-RASTER leg, which is the leg C4 is about and "
        "the leg no other rival here disturbs. Stating it on the raster side is "
        "load-bearing rather than cosmetic: refuted at the scalable-vector point "
        "this case would sit at the same input as `svg-prefix-anchor` and would "
        "add a rival without adding a probed point. If it verifies => "
        "SPEC-TOO-WEAK: the spec would pin the two link SHAPES without pinning "
        "which format receives which."),
    "refinement": (
        "A faithful patch that swaps the two branches gives the scalable-vector "
        "format a bare in-page anchor. That image lives in its own file beside "
        "the page, so an anchor with no document name resolves against the image "
        "rather than the rendered document and the link goes nowhere; the F2P "
        "scalable-vector assertion that each relative link name an existing "
        "document fails. Symmetrically the inline-raster page gains a document "
        "name it must not have, sending an in-page jump to a reloaded document. "
        "The patch does not resolve."),
    "witness": r'''
-- The INLINE-RASTER format, an anchor-only reference, at a document name used by
-- no other witness here: the swap gives the raster link a document name it must
-- not carry. Ground. Deliberately NOT stated at the scalable-vector point, which
-- `svg-prefix-anchor` already occupies; the shipped anchor rival SATISFIES this
-- input (measured), so the two cases are refuted at genuinely different places.
example : ¬ problem_spec_buildUrls false "subdir/other.html"
    [{ refuri := none, refid := some "test.DocLowerLevel",
       reftitle := "test.DocLowerLevel", internal := true }]
    (implementation_buildUrls false "subdir/other.html"
      [{ refuri := none, refid := some "test.DocLowerLevel",
         reftitle := "test.DocLowerLevel", internal := true }]) := by
  unfold problem_spec_buildUrls
  decide
''',
}


# empty-reference-fabricates-entry: a reference carrying NEITHER a destination
# URI nor an in-page anchor invents a document link.
REJ_EMPTY_FABRICATES = {
    "id": "empty-reference-fabricates-entry",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_EMPTY_ARM,
        """        | none => urls := urls ++ [(child.reftitle, child.reftitle ++ ".html")]"""),
    "rationale": (
        "Attacks C5 (a reference carrying neither field contributes NOTHING) — "
        "the one top-level commitment of the frozen equation that no other rival "
        "here touches, and the mirror image of "
        "`separate-project-reference-dropped`: an entry ADDED where the spec "
        "requires none, rather than dropped where it requires one. `filterMap` "
        "keeps only `some` results, so the rival's extra entry makes the lists "
        "differ. Refuted at the single input shape that reaches this arm — both "
        "`refuri` and `refid` at `none`, a binder combination no other witness "
        "probes. If it verifies => SPEC-TOO-WEAK: the spec would leave the "
        "no-contribution case free, and an implementation could invent links for "
        "references that have none."),
    "refinement": (
        "A faithful patch that fabricates a link for a reference with no "
        "destination and no anchor emits a relative link naming a document "
        "derived from the class name. The F2P scalable-vector test resolves "
        "every relative link it finds against the image directory and asserts "
        "the named document EXISTS; no such document is written, so the "
        "assertion fails. This arm is reachable in the F2P diagrams — a class "
        "that is not documented anywhere yields exactly such a reference, and "
        "under the frozen behavior it correctly receives no link at all. The "
        "patch does not resolve."),
    "witness": r'''
-- A reference with neither a destination URI nor an in-page anchor: the only
-- input shape reaching the arm C5 governs. Ground; the fabricated entry is a
-- length difference against the empty contribution.
example : ¬ problem_spec_buildUrls true "index.html"
    [{ refuri := none, refid := none, reftitle := "test.Foo", internal := true }]
    (implementation_buildUrls true "index.html"
      [{ refuri := none, refid := none, reftitle := "test.Foo",
         internal := true }]) := by
  unfold problem_spec_buildUrls
  decide
''',
}


# reversed-traversal-order: keep every contributing reference, but build the map
# back-to-front. Added by the second audit lane: `first-reference-only` and
# `separate-project-reference-dropped` are the only other C0 rivals here and BOTH
# are separated from the frozen behavior by list LENGTH, so the ORDER half of C0
# — that the entries appear in the references' own order — had no rival at all.
REJ_REVERSED_ORDER = {
    "id": "reversed-traversal-order",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_FULL_LOOP,
        """  let mut urls : List (String × String) := []
  for child in children do
    match child.refuri with
    | some uri =>
        let mut refname := child.reftitle
        if !child.internal then
          refname := uriTail uri
        urls := [(refname, uri)] ++ urls
    | none =>
        match child.refid with
        | some rid =>
            if isSVG then
              urls := [(child.reftitle, currentFilename ++ "#" ++ rid)] ++ urls
            else
              urls := [(child.reftitle, "#" ++ rid)] ++ urls
        | none => pure ()
  return urls"""),
    "rationale": (
        "Attacks the ORDER half of C0 — the entries appear in the references' "
        "own order — which no other rival in this battery reaches. The two other "
        "C0 rivals both differ from the frozen behavior in list LENGTH "
        "(`first-reference-only` drops entries, "
        "`separate-project-reference-dropped` drops one), so each is refuted by a "
        "cardinality mismatch and neither would notice a rival that records "
        "exactly the right entries in the wrong sequence. This rival prepends "
        "instead of appending: it computes the same MULTISET of entries as the "
        "frozen implementation and is correct on every diagram of at most one "
        "contributing reference, so it is a genuine near-miss on the length "
        "binder and is refuted only where order is observable. Both references "
        "in its witness are internal, so both keys are titles and the equation "
        "computes. If it verifies => SPEC-TOO-WEAK: the postcondition would pin "
        "which entries are recorded without pinning their sequence, and the "
        "carrier's ordered list would be doing no work over an unordered one."),
    "refinement": (
        "The ordered list models an insertion-ordered mapping, so a faithful "
        "patch that inserts in reverse changes which entry SURVIVES whenever two "
        "references in one diagram share a key: last-write-wins picks the other "
        "one. The surviving link is then the wrong one for that node — for a "
        "diagram mixing a reference into another document with one resolving to a "
        "separate project, the node can end up carrying the intra-project "
        "relative link in place of the separate project's absolute URL, and the "
        "F2P scalable-vector assertion that the separate project's URL appear in "
        "the rendered diagram fails. The patch does not resolve."),
    "witness": r'''
-- Two contributing references with DISTINCT entries, at a document name no other
-- witness here uses. The multiset of entries is the same for rival and frozen —
-- only the sequence differs — so this is the one input shape in the battery that
-- observes C0's order commitment rather than its cardinality. Ground: both
-- references are internal, so each key is a title and nothing irreducible enters.
example : ¬ problem_spec_buildUrls true "subdir/deep/index.html"
    [{ refuri := some "one.html#test.First", refid := none,
       reftitle := "test.First", internal := true },
     { refuri := some "two.html#test.Second", refid := none,
       reftitle := "test.Second", internal := true }]
    (implementation_buildUrls true "subdir/deep/index.html"
      [{ refuri := some "one.html#test.First", refid := none,
         reftitle := "test.First", internal := true },
       { refuri := some "two.html#test.Second", refid := none,
         reftitle := "test.Second", internal := true }]) := by
  unfold problem_spec_buildUrls
  decide
''',
}


# anchor-keyed-by-identifier: the in-page-anchor entry is keyed by the ANCHOR
# IDENTIFIER instead of the reference title. Added by the second audit lane: every
# other anchor rival here edits the link STRING and leaves the key untouched, and
# every other anchor witness uses a reference whose title and identifier are the
# SAME string — so the anchor leg's key commitment was unobservable everywhere in
# the battery.
REJ_ANCHOR_KEY = {
    "id": "anchor-keyed-by-identifier",
    "kind": "uniqueness",
    "expect": "reject",
    "module": _swap(
        _BASE, _I_ANCHOR_ARM,
        """            if isSVG then
              urls := urls ++ [(rid, currentFilename ++ "#" ++ rid)]
            else
              urls := urls ++ [(rid, "#" ++ rid)]"""),
    "rationale": (
        "Attacks the KEY half of C3/C4: the anchor entry is keyed by the "
        "reference TITLE, not by the anchor identifier. Every other anchor rival "
        "in this battery (`svg-prefix-anchor`, `format-pivot-swapped`) edits the "
        "LINK component and leaves the key exactly right, and — the reason this "
        "clause was not merely unattacked but unobservable — every other anchor "
        "witness here uses a reference whose `reftitle` and `refid` are the same "
        "string, at which point the two candidate keys coincide and no rival "
        "could be caught confusing them. This case supplies both the rival and "
        "the input where they differ. It errs at BOTH values of `isSVG`, and is "
        "refuted on the scalable-vector leg at a root document name — a point no "
        "other witness occupies, since the two shipped anchor witnesses sit at "
        "nested names. If it verifies => SPEC-TOO-WEAK: the spec would pin the "
        "anchor entry's link while leaving its key free, so an implementation "
        "could register every in-page link under a name no diagram node carries."),
    "refinement": (
        "A faithful patch keying the in-page link by the anchor identifier "
        "registers it under a name that is not the fully-qualified class name a "
        "diagram node is matched by. The node therefore matches nothing and "
        "receives no link, while an entry nothing will ever look up is left in "
        "the map — the same missing-link failure mode as keying a "
        "separate-project reference by its title, and it strikes the "
        "intra-project anchor references instead. The F2P scalable-vector test "
        "checks the links the diagram actually carries, and a node that silently "
        "loses its link fails it. The patch does not resolve."),
    "witness": r'''
-- An anchor-only reference whose anchor IDENTIFIER and whose TITLE are different
-- strings, scalable-vector format, root document name. The distinction this
-- witness turns on is invisible at every other anchor input in this battery,
-- where the two fields carry the same string. Ground: the reference is internal
-- and carries no destination URI, so no trailing-component term appears.
example : ¬ problem_spec_buildUrls true "index.html"
    [{ refuri := none, refid := some "test.DocHere-anchor",
       reftitle := "test.DocHere", internal := true }]
    (implementation_buildUrls true "index.html"
      [{ refuri := none, refid := some "test.DocHere-anchor",
         reftitle := "test.DocHere", internal := true }]) := by
  unfold problem_spec_buildUrls
  decide
''',
}


SPEC_TESTS = [
    # positives (expect verify)
    POS_KEY_EXPR,
    POS_ANCHOR_PREFIX,
    ADMISS_MULTI,
    # C1 / C4 — the recorded URL
    REJ_SVG_PREFIX_URI,
    REJ_PREFIX_URI_BOTH,
    REJ_SVG_PREFIX_ANCHOR,
    REJ_URL_IS_TITLE,
    # C2 — the destination key
    REJ_TITLE_KEY_ALL,
    REJ_WHOLE_URI_KEY,
    # C0 / C5 — the traversal and the empty contribution
    REJ_DROP_EXTERNAL,
    REJ_FIRST_ONLY,
    # arm order and the format pivot (added by the audit lane)
    REJ_ARM_PRECEDENCE,
    REJ_PIVOT_SWAPPED,
    REJ_EMPTY_FABRICATES,
    # traversal ORDER and the anchor entry's KEY (added by the second audit lane)
    REJ_REVERSED_ORDER,
    REJ_ANCHOR_KEY,
]


# ---------------------------------------------------------------------------
# POINT SPREAD of the reject witnesses. Recorded explicitly because a battery
# whose rivals are all refuted at ONE input says nothing about the spec's
# dependence on any binder. Thirteen rivals, thirteen DISTINCT input points;
# `isSVG` is probed at both values, `currentFilename` at a root name and three
# different nested names, `children` at lengths 1 and 2, `internal` at both values
# (including both within a single input), and `refuri`/`refid` each at `some` and
# `none` INDEPENDENTLY — including the both-`some` combination that pins C6.
#
#  id                                  isSVG  currentFilename      len  shape
#  svg-prefix-destination              true   index.html            1   uri, internal
#  prefix-destination-both-formats     false  subdir/index.html     1   uri, internal
#  svg-prefix-anchor                   true   subdir/index.html     1   anchor
#  url-is-title                        true   index.html            1   uri, internal
#  title-key-every-destination         true   index.html            1   uri, separate
#  whole-uri-key-separate-project      false  subdir/index.html     1   uri, separate
#  separate-project-reference-dropped  true   index.html            2   uri x2, mixed
#  first-reference-only                false  index.html            2   anchor + uri
#  anchor-arm-takes-precedence         false  index.html            1   uri AND anchor
#  format-pivot-swapped                false  subdir/other.html     1   anchor
#  empty-reference-fabricates-entry    true   index.html            1   neither field
#  reversed-traversal-order            true   subdir/deep/index.html 2  uri x2, internal
#  anchor-keyed-by-identifier          true   index.html            1   anchor, refid != title
#
# The last two rows are what the second audit pass added, and the column that
# matters for each is not `isSVG` or `currentFilename` but the SHAPE. The
# `reversed-traversal-order` row is the only 2-reference input whose two entries
# are DISTINCT and whose rival keeps both, so it is the only point where C0's
# order commitment is observable rather than its cardinality: every other
# multi-reference witness here refutes by length. The `anchor-keyed-by-identifier`
# row is the only input where a reference's `refid` and `reftitle` differ; at every
# other anchor point in this table the two carry the same string, so the anchor
# entry's key and identifier coincide and no rival could be caught swapping them.
# A row is a probed point only if some binder value in it changes the spec's
# verdict, and for these two it is that shape column that does.
#
# The rows sharing a column pair still differ in the reference shape or in the
# value the rival gets wrong there, and each rival's witness sits inside the
# sub-domain its own `rationale` claims — checked pairwise for the near-miss
# pairs (the two prefix rivals, the two key rivals, and the two anchor rivals) by
# building each pair's witness against the OTHER pair member's module and
# confirming it is satisfied there.
#
# Two rows are worth reading together, because the pair is the reason the
# `format-pivot-swapped` row says `false  subdir/other.html` and not
# `true  subdir/index.html`. Stated at the scalable-vector point that rival would
# be refuted at the input `svg-prefix-anchor` already occupies — a second rival at
# an existing point, which grows the case count without growing the probed domain.
# On the inline-raster leg it is refuted where NO other rival is, and the anchor
# rival is satisfied there; that is what makes C4 demonstrated rather than merely
# asserted alongside C3.
# ---------------------------------------------------------------------------
