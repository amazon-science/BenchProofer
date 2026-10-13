"""properties.py — G-PBT falsification battery for django__django-14539 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct peelTrailingPunctuation`` obligation survives with an
identical statement). ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the subject — the frozen solution, or the case's ``witness_reference``
where the frozen impl cannot decide anything (see WITNESS SUBJECT below).

DEFENDED SURFACE. One contracted method over a token domain (``List Char``): it
peels the run of trailing sentence-punctuation characters off the end of a token
into an accumulated suffix. Two independent input binders — ``token`` (the
sequence being peeled) and ``tail`` (the suffix already accumulated) — and two
independent load-bearing postcondition clauses, both cut at the same boundary
``token.length - trailingPunctCount token``:

  C-core : res.core = token.take (token.length - trailingPunctCount token)
  C-tail : res.tail = token.drop (token.length - trailingPunctCount token) ++ tail

The method has NO precondition (the ``pre-conditions`` region is empty), so the
admitted input domain is total.

CARRIER NARROWING — the decisive fact of this port. The cut boundary is
``token.length - trailingPunctCount token``, and ``trailingPunctCount`` is
defined through an OPAQUE decoder (a standard-library entity decoder modeled as
an uninterpreted ``List Char → List Char``). Its value at any concrete token is
unknowable to the kernel, so:

  * the derived ``…Tester`` cannot be reduced by ``decide`` at any concrete
    input (verified empirically: reduction gets stuck on the opaque instance),
    so witnesses here reach the postcondition via the extracted ``…Exec``
    program and the spec's own take/drop image, not via the tester. The opacity
    reaches one step further than the tester, though, and it decides the witness
    SUBJECT rather than the witness shape: the frozen impl's ``if`` is guarded on
    the decoder, so its ``…Exec`` never normalises to a constructor and the
    carrier projection fails on the term's shape for every claim alike. That is
    what ``witness_reference`` is for here; see WITNESS SUBJECT below;
  * a rival that corrupts only the BOUNDARY INDEX cannot be refuted at a
    LITERAL point, because separating its boundary from the frozen one requires
    the opaque decoder to shorten the token and no literal can force that. This
    is NOT the same as being undiscriminable, and an earlier revision's
    conclusion that it was — dropping both sibling count rivals — was wrong. A
    witness may state its refutation at a point described by HYPOTHESIS
    (`hd : entityDecode <tok> = <lit>`), which supplies the decoded form no
    literal could and is satisfiable precisely BECAUSE the decoder is opaque.
    Both count rivals are shipped below on that technique, and pinning the
    decoder additionally makes the frozen impl's guard reduce, so those two need
    no `witness_reference` at all.

Two independent families of reject case therefore live here. The first violates a
COUNT-INDEPENDENT structural fact of a clause — one true for every value of the
opaque count, refutable without touching the decoder, but needing a
`witness_reference` because gold's guard does not reduce:

  * C-core forces ``res.core`` to be a PREFIX of ``token`` (a ``take`` of it):
    bounded by ``token.length`` and drawn only from ``token``'s elements. A
    rival whose core is longer than ``token`` (overshoot) or contains a
    character absent from ``token`` violates C-core regardless of the count.
  * C-tail forces ``res.tail`` to END WITH the accumulated ``tail``: at least
    ``tail.length`` long and carrying ``tail`` as its suffix. A rival that drops
    the accumulator violates C-tail regardless of the count.

The second family attacks the BOUNDARY INDEX itself, at a token pinned by
hypothesis: wrong index ORIGIN (measuring the cut on the decoded form instead of
from the end of the encoded token) and wrong COUNT (hardcoding a one-character
peel). Both clauses pin the exact index, and these are the two directions the
sibling battery probed it in.

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The class exists on
    nagini because a read-only input carries a fractional heap permission an
    impl can overwrite. Lean and Velvet are referentially transparent; this
    bundle declares no ``mut`` parameter, there is no heap and no aliasing, so
    there is no read-only input to mutate and no substitute probe to build. Not
    fabricated. (nagini frame-mut-middle / frame-mut-trail have no counterpart.)
  * UNGROUNDED-ORACLE ECHO — N/A. Both post-images are total take/drop functions
    of the method's own inputs; there is no opaque ANSWER KEY to echo (the
    opaque decoder only LOCATES the boundary, it is not the result). So there is
    no wrong echo to build; the positive control is an honest cheapest-reshape.
  * BOUNDARY / COUNT rivals — the heart of nagini's battery (the prepatch bug,
    the count==1 partial-domain). Both PORTED, on the hypothesis technique
    above; an earlier revision omitted them as undiscriminable, which was wrong.
  * PARTIAL-DOMAIN / VALUE and LOSSLESSNESS — carried by the count-independent
    rivals AND by weak-count-hardcoded-one, which is the partial-domain class
    proper (right on the single-punctuation sub-domain, wrong on longer runs).

WITNESS SUBJECT — why the three COUNT-INDEPENDENT reject cases name a
``witness_reference`` (the three BOUNDARY-INDEX cases do not, because pinning the
decoder by hypothesis makes gold's guard reduce; see _HD_PREAMBLE). The
frozen impl guards its assignment on ``decoded ≠ stripped``, whose scrutinee is
the OPAQUE decoder. So in a witness file built over the frozen impl, the
extracted ``…Exec`` term never normalises past that ``if``: it stays a
``NonDetT.run (if entityDecode … then … else …)`` application, which is not a
constructor, and every witness shape that projects the carrier — ``injection``,
``DivM.res.inj``, ``cases`` — fails on the SHAPE of that term before the claim is
ever consulted. Measured with the real verifier (18 builds): the shipped witness,
the SAME witness with its claim FLIPPED (``≠`` swapped for ``=``, i.e. asserting
the frozen impl is CORRECT at that input), and an absurd ``res.tail ≠ res.tail``
all fail against the frozen solution with a byte-identical
``Tactic `injection` failed: equality of constructor applications expected`` —
the three logs differ only in the echoed goal line, never in the failure reason.
A gold-side exit code that is invariant under negating the claim is evidence of
nothing, so refuting against the frozen impl would have made all three
rejections hollow (a witness asserting gold is CORRECT would have been recorded
as a refutation).

The repair is the subject, not the claim. ``witness_reference`` names an
UNCONDITIONAL impl of this same spec (``_REF_IMPL``, the pos-control's body,
which the gate independently checks shares the frozen spec and VERIFIES). It has
no guard, so its ``…Exec`` reduces to a literal ``Split`` constructor and the
projection goes through; what remains is the claim itself, over the still-opaque
count. An impl the verifier ACCEPTS cannot violate its own spec, so a genuine
refutation must still fail there — and now it fails for the claim. Re-measured:
each witness exits 1 against the reference with a SEMANTIC residue (weak-tail:
``omega could not prove the goal: No usable constraints``; weak-core-overshoots:
``unsolved goals … hlen : True ⊢ False``; weak-core-is-accumulator:
``unsolved goals … ⊢ 'x' ∈ List.take (1 - trailingPunctCount ['a']) ['a']``),
while each FLIPPED claim exits 0 against that same reference. The exit code
tracks the claim, which is the property that was missing.

WITNESS PLACEMENT. Each reject case is refuted at a concrete ``(token, tail)``
input via the spec's take/drop image, and the input points are chosen so the two
binders both MOVE across the battery rather than being pinned: the C-tail rival
is refuted at ``token=['a'], tail=['b']``; the C-core overshoot at
``token=[], tail=['x']`` (empty token, so the overshoot is pure ``tail``); the
C-core wrong-content at ``token=['a'], tail=['x','y']`` (a two-element
accumulator); and the three BOUNDARY-INDEX rivals at tokens the ``hd``
hypothesis pins — ``['a','.','!']`` with a two-character trailing run (count 2,
the multi-character sub-domain) for the hardcoded-count and no-peel rivals, and
``['&','l','t',';','!']`` decoding to two characters (count 1, the escaped-
sequence sub-domain) for the wrong-origin rival, both with ``tail=[]``. So
``token`` ranges over ``[]``, ``['a']``, a 3-character token and a 5-character
token, and ``tail`` over ``[]``, one- and two-element values.
"""
from pathlib import Path

INSTANCE = "django__django-14539"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The entire frozen `do` body (the text strictly
# ---- between the impl markers). Lies wholly inside the one impl region and is
# ---- unique in Solution.lean; both facts are asserted at load by _swap.
_GOLD_IMPL = (
    "    let decoded := entityDecode token\n"
    "    let stripped := stripTrailingPunct decoded\n"
    "    let punctuationCount := decoded.length - stripped.length\n"
    "    let mut core := token\n"
    "    let mut newTail := tail\n"
    "    if decoded ≠ stripped then\n"
    "      core := token.take (token.length - punctuationCount)\n"
    "      newTail := token.drop (token.length - punctuationCount) ++ tail\n"
    "    return { core := core, tail := newTail }"
)

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header is kept), so a positive control that
# ---- reshapes the impl into an unconditional form may retune the tactic script
# ---- to the new shape without touching the spec or dropping the obligation.
_GOLD_PROOF = (
    "  loom_solve\n"
    "  · -- if-true, tail clause: the inlined count equals `trailingPunctCount`\n"
    "    simp only [trailingPunctCount]\n"
    "  · -- if-true, core clause\n"
    "    simp only [trailingPunctCount]\n"
    "  · -- if-false, tail clause: decoded = stripped ⇒ count 0 ⇒ nothing peeled\n"
    "    rw [not_not] at if_neg\n"
    "    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,\n"
    "      List.drop_length, List.nil_append]\n"
    "  · -- if-false, core clause: count 0 ⇒ whole token kept\n"
    "    rw [not_not] at if_neg\n"
    "    simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,\n"
    "      List.take_length]"
)


# ---- impl-region OPENING marker. Inserting after it puts new text at the very
# ---- top of the impl region — inside it, so the consumer spec view still elides
# ---- the addition and same_spec holds.
_IMPL_START = "    -- impl-start\n"

# ---- the admissibility probe. Evaluates the spec's OWN post-image at a concrete
# ---- F2P-shaped token, and states it over the SPEC'S OWN BOUNDARY EXPRESSION
# ---- (`token.length - trailingPunctCount token`) rather than over a
# ---- pre-substituted literal index.
# ----
# ---- The distinction is the whole content of this case, and an earlier revision
# ---- got it wrong. That revision's assert read
# ----
# ----     (['a','b','!'] : List Char).take (3 - 1) = ['a','b'] ∧ …
# ----
# ---- i.e. literal `take`/`drop` at literal indices, mentioning neither
# ---- `trailingPunctCount` nor `.length`. That is a closed arithmetic fact about
# ---- `List.take` — TRUE of every spec, and of no spec in particular. Measured:
# ---- the same conjunction discharges by `decide` with the frozen obligation
# ---- present or absent, so it could not have detected a post-image that is
# ---- unsatisfiable or degenerate at this token; it detected only that
# ---- `['a','b','!'].take 2 = ['a','b']`. An admissibility positive whose assert
# ---- does not name the obligation's own binder is the total-carrier analogue of
# ---- a neutered precondition discharge.
# ----
# ---- The form below is stated over `trailingPunctCount` and is CONDITIONED on
# ---- its value, which is what makes it both non-trivial and provable on an
# ---- opaque carrier: nothing has to evaluate the decoder, the two implications
# ---- pin what the post-image DOES at this token in each of the two regimes the
# ---- count can be in. Together they establish, at exactly an F2P-shaped input
# ---- (a token ending in one punctuation character):
# ----   * count = 1 ⇒ the post-image is SATISFIABLE there and splits the token
# ----     as ['a','b'] / ['!'] — the peel actually happens;
# ----   * count = 1 ⇒ the count-1 core DIFFERS from the count-0 core, so the
# ----     post-image is NON-DEGENERATE across the count (it does not collapse to
# ----     the identity, the failure mode an opaque count could hide);
# ----   * count = 0 ⇒ the post-image keeps the whole token and peels nothing,
# ----     so the boundary is the count's own function and not a constant.
# ---- Every conjunct now mentions `trailingPunctCount` and the spec's `.length`,
# ---- so a degenerate post-image would show up here.
_ADMISS_TOKEN = "(['a','b','!'] : List Char)"
_ADMISS_ASSERT = (
    "    assert (with_name_prefix `admiss (\n"
    f"      (trailingPunctCount {_ADMISS_TOKEN} = 1 →\n"
    f"          {_ADMISS_TOKEN}.take"
    f" ({_ADMISS_TOKEN}.length - trailingPunctCount {_ADMISS_TOKEN}) = ['a','b']\n"
    f"        ∧ {_ADMISS_TOKEN}.drop"
    f" ({_ADMISS_TOKEN}.length - trailingPunctCount {_ADMISS_TOKEN})\n"
    "            ++ ([] : List Char) = ['!']\n"
    f"        ∧ {_ADMISS_TOKEN}.take"
    f" ({_ADMISS_TOKEN}.length - trailingPunctCount {_ADMISS_TOKEN})\n"
    f"            ≠ {_ADMISS_TOKEN}.take ({_ADMISS_TOKEN}.length - 0))\n"
    f"      ∧ (trailingPunctCount {_ADMISS_TOKEN} = 0 →\n"
    f"          {_ADMISS_TOKEN}.take"
    f" ({_ADMISS_TOKEN}.length - trailingPunctCount {_ADMISS_TOKEN})"
    " = ['a','b','!']\n"
    f"        ∧ {_ADMISS_TOKEN}.drop"
    f" ({_ADMISS_TOKEN}.length - trailingPunctCount {_ADMISS_TOKEN})\n"
    "            ++ ([] : List Char) = ([] : List Char))))\n"
)

# ---- the frozen tactic script's four arms, plus an arm for the assert goal, as
# ---- an unordered `first` over `all_goals`. Every arm ends in `done` so a
# ---- partially-applied arm cannot swallow a goal it did not close — the frozen
# ---- obligation must still discharge on its own terms.
# ----
# ---- The assert arm introduces each implication's count hypothesis and rewrites
# ---- the OPAQUE count away with it (`simp only [hcnt]`) before deciding the
# ---- resulting literal take/drop facts. So the arm consumes the hypothesis it
# ---- was given, which is why a `decide` arm alone (the earlier revision's) does
# ---- not close this form and why this form is not a closed arithmetic identity.
_ADMISS_PROOF = (
    "  loom_solve\n"
    "  all_goals\n"
    "    first\n"
    "      | (constructor\n"
    "         · intro hcnt\n"
    "           simp only [hcnt]\n"
    "           exact ⟨by decide, by decide, by decide⟩\n"
    "         · intro hcnt\n"
    "           simp only [hcnt]\n"
    "           exact ⟨by decide, by decide⟩\n"
    "         done)\n"
    "      | (simp only [trailingPunctCount]; done)\n"
    "      | (rw [not_not] at if_neg\n"
    "         simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,\n"
    "           List.drop_length, List.nil_append]\n"
    "         done)\n"
    "      | (rw [not_not] at if_neg\n"
    "         simp only [trailingPunctCount, ← if_neg, Nat.sub_self, Nat.sub_zero,\n"
    "           List.take_length]\n"
    "         done)"
)


def _with_impl(new_body):
    """`_BASE` with the frozen impl body replaced (impl region only). The spec,
    the method signature and the `prove_correct` header/statement are untouched,
    so same_spec holds and the obligation survives."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


def _with_impl_and_proof(new_body, new_proof):
    """Reshape the impl AND retune the (elided) tactic body for the new shape."""
    return _swap(_swap(_BASE, _GOLD_IMPL, new_body), _GOLD_PROOF, new_proof)


# ---- witness preamble. `decide` on the derived tester is STUCK here (the
# ---- boundary lives behind the opaque decoder), so a witness cannot use the
# ---- tester. Instead it extracts the executable program and states, at a
# ---- concrete input, that the program's output CONTRADICTS the spec's own
# ---- take/drop image — a count-independent structural violation the kernel can
# ---- check without ever evaluating the opaque decoder. Checked in a file whose
# ---- `prove_correct` block has been stripped, so no tactic script interferes.
_EXTRACT = "extract_program_for peelTrailingPunctuation\n\n"


# ---- witness SUBJECT (see the docstring's WITNESS SUBJECT section). The frozen
# ---- impl's `if` is guarded on the opaque decoder, so its extracted program
# ---- never normalises to a constructor and no witness's carrier projection can
# ---- get past the term's SHAPE — the same failure appears for a claim and for
# ---- its negation, so the frozen solution's exit code discriminates nothing.
# ---- This unconditional impl of the SAME spec (the pos-control's body, which the
# ---- gate re-checks shares the frozen spec and VERIFIES) reduces to a literal
# ---- `Split`, so the projection succeeds and what is left to fail is the claim.
_REF_BODY = (
    "    let count := trailingPunctCount token\n"
    "    let boundary := token.length - count\n"
    "    return { core := token.take boundary,"
    " tail := token.drop boundary ++ tail }"
)
_REF_IMPL = _with_impl_and_proof(_REF_BODY, "  loom_solve")


# ---- BOUNDARY-INDEX witnesses: pinning the decoder by HYPOTHESIS.
# ----
# ---- The `witness_reference` mechanism above solves the SUBJECT problem, but it
# ---- leaves a second one untouched: a rival that corrupts only the boundary
# ---- INDEX agrees with the spec at every token whose decoded and encoded lengths
# ---- coincide, and no literal can make them differ, because the decoder is
# ---- opaque. An earlier revision concluded from this that the boundary dimension
# ---- is undiscriminable on this carrier and dropped both sibling count rivals.
# ---- That conclusion was WRONG, and the two cases below are the machine-checked
# ---- refutation of it.
# ----
# ---- Nothing has to COMPUTE the decoder: a witness may state its refutation at a
# ---- point described by hypothesis. `hd : entityDecode <tok> = <lit>` pins the
# ---- decoded form at one concrete token, which is enough to turn the boundary
# ---- into a literal (`have hcount : trailingPunctCount <tok> = k`) and — the part
# ---- that also fixes the subject — to make the FROZEN impl's guard reduce, so
# ---- these two witnesses are refuted against the frozen solution directly and
# ---- need no `witness_reference` at all. The hypothesis is satisfiable precisely
# ---- BECAUSE the decoder is opaque: no tactic can derive `False` from a value
# ---- assignment to an uninterpreted function, which the gate's own consistency
# ---- probe confirms (it exits 1 on both cases).
# ----
# ---- Gold's failure under this shape is the strongest signature available: the
# ---- goal reduces to `⊢ False`, i.e. `simp` PROVED the spec's equation for the
# ---- frozen impl and could not for the rival. Both directions measured per case.
_HD_PREAMBLE = (
    "  intro res h\n"
    "  simp only [peelTrailingPunctuationExec, peelTrailingPunctuation, hd] at h\n"
    "  injection h with h1\n"
    "  subst h1\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Ports nagini `pos-control-reshaped`.
    # =====================================================================
    {
        "id": "pos-unconditional-boundary",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the guard and the mutable accumulators; bind the count
        # and the cut boundary to plain locals and return both projections
        # inline as a single take/drop of the token. Observationally identical
        # to the frozen impl on both branches (when the count is 0 the take/drop
        # at `token.length - 0` returns the whole token / empty peel), so it
        # meets both clauses; the reproof collapses to `loom_solve`.
        # This is the same source the reject cases name as `witness_reference`,
        # so the gate's requirement that the reference VERIFY is exactly this
        # case's own assertion — one build, two jobs.
        "module": _REF_IMPL,
        "rationale": "a correct unconditional reshape (count and boundary bound "
                     "to locals, both projections returned as one take/drop of "
                     "the token) still meets C-core and C-tail pointwise for "
                     "every value of the opaque count, so it must verify; else "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. TWO witness techniques are
    # in play here and BOTH dimensions are covered (see the module docstring):
    # the first three rivals attack a COUNT-INDEPENDENT structural fact of a
    # clause — refutable without touching the decoder, but needing a
    # `witness_reference` because gold's guard does not reduce — and the last
    # three attack the BOUNDARY INDEX itself at a token pinned by HYPOTHESIS,
    # refuted against the FROZEN solution directly. An earlier revision's claim
    # that "the boundary index itself is not discriminable on this carrier" was
    # WRONG; it is retracted here rather than left standing next to the three
    # cases that refute it (see the _HD_PREAMBLE note and the footer).
    # =====================================================================

    # ---- C-tail: the accumulated suffix must be carried through ----
    {
        "id": "weak-tail-drops-accumulator",
        "kind": "uniqueness",
        "expect": "reject",
        # Computes the SAME boundary as gold and peels the correct suffix, but
        # returns it WITHOUT re-attaching the accumulator `tail`. Right on the
        # boundary, wrong on the accumulation — a pure attack on the `++ tail`
        # half of C-tail, and on the `tail` binder.
        "module": _with_impl(
            "    let count := trailingPunctCount token\n"
            "    let boundary := token.length - count\n"
            "    return { core := token.take boundary, tail := token.drop boundary }"),
        "refinement": "a faithful counterpart that peels the suffix but drops "
                      "the already-accumulated trailing text discards everything "
                      "collected on earlier passes over the token, so the "
                      "failing example — whose expected output keeps the "
                      "trailing text intact after the moved punctuation — still "
                      "observes the truncated accumulator and stays RED. It "
                      "would NOT resolve.",
        "rationale": "REJECT from C-tail (res.tail = … ++ tail): the post-image "
                     "requires the result to END WITH the accumulator `tail`, "
                     "which is at least `tail.length` long; the impl returns the "
                     "bare peeled suffix, dropping it. Refuted at "
                     "token=['a'], tail=['b'] by a length argument that never "
                     "touches the opaque count.",
        "witness": _EXTRACT +
                   "example : ∀ res : Split,\n"
                   "    (peelTrailingPunctuationExec ['a'] ['b']) = DivM.res res →\n"
                   "    res.tail ≠ ['a'].drop (['a'].length - trailingPunctCount ['a'])"
                   " ++ ['b'] := by\n"
                   "  intro res h\n"
                   "  simp only [peelTrailingPunctuationExec, peelTrailingPunctuation] at h\n"
                   "  injection h with h1\n"
                   "  subst h1\n"
                   "  intro hc\n"
                   "  have hlen := congrArg List.length hc\n"
                   "  simp only [List.length_append, List.length_cons,"
                   " List.length_nil] at hlen\n"
                   "  omega\n",
        # Refuted against the VERIFYING unconditional impl, not the frozen one:
        # the frozen impl's opaque guard blocks the carrier projection for EVERY
        # claim (WITNESS SUBJECT). Against the reference the witness exits 1 with
        # `omega could not prove the goal: No usable constraints found` — the
        # length identity the accumulator's absence makes unprovable — while the
        # same witness with `≠` flipped to `=` exits 0. Measured, both builds.
        "witness_reference": _REF_IMPL,
    },

    # ---- C-core: the retained core must be a bounded prefix of the token ----
    {
        "id": "weak-core-overshoots",
        "kind": "uniqueness",
        "expect": "reject",
        # Returns `token ++ tail` as the core: strictly longer than `token`
        # whenever `tail` is non-empty. C-core pins the core to a `take` of the
        # token, whose length can never exceed `token.length`, so this violates
        # C-core for every value of the count. Refuted at the EMPTY token so the
        # overshoot is purely the accumulator — a different input point from the
        # C-tail rival, and one that moves the `token` binder to `[]`.
        "module": _with_impl(
            "    let core := token ++ tail\n"
            "    return { core := core, tail := tail }"),
        "refinement": "a faithful counterpart that leaves the accumulated "
                      "trailing text glued onto the retained core never actually "
                      "peels anything off the token, so the failing example — "
                      "which expects the punctuation MOVED out of the core — "
                      "still sees it retained and stays RED. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C-core (res.core = token.take …): the "
                     "post-image bounds the core's length by `token.length`; "
                     "with a non-empty `tail` the impl returns a strictly longer "
                     "sequence. Refuted at token=[], tail=['x'] by a length "
                     "argument independent of the opaque count.",
        "witness": _EXTRACT +
                   "example : ∀ res : Split,\n"
                   "    (peelTrailingPunctuationExec [] ['x']) = DivM.res res →\n"
                   "    res.core ≠ ([] : List Char).take"
                   " (([] : List Char).length - trailingPunctCount []) := by\n"
                   "  intro res h\n"
                   "  simp only [peelTrailingPunctuationExec, peelTrailingPunctuation] at h\n"
                   "  injection h with h1\n"
                   "  subst h1\n"
                   "  intro hc\n"
                   "  have hlen := congrArg List.length hc\n"
                   "  simp at hlen\n",
        # See WITNESS SUBJECT. Against the reference the witness exits 1 with
        # `unsolved goals … hlen : True ⊢ False` — `simp` reduced the length
        # identity to `True` for the CORRECT impl (it holds there) and so left
        # `False` unprovable, which is precisely the discrimination; the flipped
        # claim exits 0 against the same reference. Measured, both builds.
        "witness_reference": _REF_IMPL,
    },
    {
        "id": "weak-core-is-accumulator",
        "kind": "uniqueness",
        "expect": "reject",
        # Returns the accumulator `tail` AS the core. C-core requires the core
        # to be a `take` of the token, whose every element comes from `token`;
        # a `tail` character absent from `token` can never appear there. A
        # wrong-CONTENT attack on C-core (distinct from the wrong-LENGTH
        # overshoot above), refuted at a two-element accumulator so `tail` moves
        # to a value no other witness uses.
        "module": _with_impl(
            "    let core := tail\n"
            "    return { core := core, tail := tail }"),
        "refinement": "a faithful counterpart that reports the accumulated "
                      "trailing text as the retained core replaces the token "
                      "body with unrelated characters, so every failing "
                      "assertion pinning the retained core still fails. It would "
                      "NOT resolve.",
        "rationale": "REJECT from C-core (res.core = token.take …): every "
                     "element of `token.take n` is an element of `token`; with a "
                     "`tail` character not in `token`, the impl's core cannot "
                     "equal any prefix of the token. Refuted at "
                     "token=['a'], tail=['x','y'] by a membership argument "
                     "independent of the opaque count.",
        "witness": _EXTRACT +
                   "example : ∀ res : Split,\n"
                   "    (peelTrailingPunctuationExec ['a'] ['x','y']) = DivM.res res →\n"
                   "    res.core ≠ ['a'].take (['a'].length - trailingPunctCount ['a'])"
                   " := by\n"
                   "  intro res h\n"
                   "  simp only [peelTrailingPunctuationExec, peelTrailingPunctuation] at h\n"
                   "  injection h with h1\n"
                   "  subst h1\n"
                   "  intro hc\n"
                   "  have hm : 'x' ∈ (['a'].take"
                   " (['a'].length - trailingPunctCount ['a'])) := by\n"
                   "    rw [← hc]; simp\n"
                   "  have h2 := (List.take_prefix _ _).subset hm\n"
                   "  simp at h2\n",
        # See WITNESS SUBJECT. Against the reference the witness exits 1 with
        # `unsolved goals … ⊢ 'x' ∈ List.take (1 - trailingPunctCount ['a']) ['a']`
        # — the membership the correct impl makes unprovable, stated over the
        # still-opaque count; the flipped claim exits 0 against the same
        # reference. Measured, both builds.
        "witness_reference": _REF_IMPL,
    },

    # ---- BOUNDARY INDEX: the exact cut position, at a token the decoder
    # ---- shortens. Both cases below were recorded by an earlier revision as
    # ---- "no discriminating witness exists on this carrier". They do exist; see
    # ---- the _HD_PREAMBLE note. Refuted against the FROZEN solution directly.
    {
        "id": "weak-decoded-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        # Cuts at the length of the STRIPPED DECODED form used as an index into
        # the still-encoded token, instead of measuring the peel from the END of
        # the encoded token. Agrees with the spec on every token whose decoded and
        # encoded lengths coincide, and diverges exactly where an escaped
        # character sequence makes the decoded form shorter — the sub-domain the
        # count-independent rivals above cannot reach. Ports the sibling's
        # `weak-prepatch-decoded-boundary`.
        "module": _with_impl(
            "    let decoded := entityDecode token\n"
            "    let stripped := stripTrailingPunct decoded\n"
            "    return { core := token.take stripped.length,\n"
            "             tail := token.drop stripped.length ++ tail }"),
        "refinement": "a faithful counterpart that indexes the encoded token by a "
                      "position measured on the DECODED form keeps, in the "
                      "retained core, the characters of any escaped sequence the "
                      "decoding collapsed — so on the failing example the "
                      "surplus characters leak across the split and the expected "
                      "output is not produced. It would NOT resolve.",
        "rationale": "REJECT from C-core (res.core = token.take (token.length - "
                     "trailingPunctCount token)): the post-image measures the peel "
                     "from the END of the encoded token, so the cut is at "
                     "token.length - count; this impl cuts at the decoded "
                     "stripped length. Refuted at a 5-character token whose "
                     "decoded form is 2 characters (count 1): the spec's cut is "
                     "at 4, the impl's at 1. The decoded form is supplied by "
                     "HYPOTHESIS (`hd`), which is what makes the boundary "
                     "dimension reachable at all — and satisfiable precisely "
                     "because the decoder is opaque.",
        "witness": _EXTRACT +
                   "example (hd : entityDecode ['&','l','t',';','!'] = ['<', '!']) :\n"
                   "    ∀ res : Split,\n"
                   "    (peelTrailingPunctuationExec ['&','l','t',';','!'] [])"
                   " = DivM.res res →\n"
                   "    res.core ≠ ['&','l','t',';','!'].take\n"
                   "      (['&','l','t',';','!'].length"
                   " - trailingPunctCount ['&','l','t',';','!']) := by\n"
                   "  have hcount : trailingPunctCount ['&','l','t',';','!'] = 1 := by\n"
                   "    simp [trailingPunctCount, hd, stripTrailingPunct,"
                   " isTrailingPunct]\n"
                   + _HD_PREAMBLE +
                   "  simp [hcount, hd, stripTrailingPunct, isTrailingPunct]\n",
    },
    {
        "id": "weak-count-hardcoded-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Hardcodes the peel length to exactly one character: correct on the
        # common sub-domain where the token ends in a single punctuation
        # character, wrong wherever the trailing run is longer. Ports the
        # sibling's `partial-domain-count1` — the PARTIAL-DOMAIN class, which no
        # other case here covers (a rival right on a realistic sub-domain is the
        # one a byte-fuzzer never separates from correct).
        "module": _with_impl(
            "    return { core := token.take (token.length - 1),\n"
            "             tail := token.drop (token.length - 1) ++ tail }"),
        "refinement": "a faithful counterpart that always moves exactly one "
                      "character passes the cases whose trailing run is a single "
                      "character but leaves every longer run partly in the "
                      "retained core, so the assertions covering multi-character "
                      "trailing runs stay RED. It would NOT resolve.",
        "rationale": "REJECT from C-core (res.core = token.take (token.length - "
                     "trailingPunctCount token)): the post-image pins the EXACT "
                     "count, and nothing in the (empty) precondition bounds it to "
                     "1. Refuted at a 3-character token whose trailing run is 2 "
                     "characters: the spec's cut is at 1, the impl's at 2. The "
                     "token decodes to itself, supplied by HYPOTHESIS (`hd`) "
                     "since the kernel cannot evaluate the opaque decoder even at "
                     "an entity-free literal.",
        "witness": _EXTRACT +
                   "example (hd : entityDecode ['a','.','!'] = ['a','.','!']) :\n"
                   "    ∀ res : Split,\n"
                   "    (peelTrailingPunctuationExec ['a','.','!'] []) = DivM.res res →\n"
                   "    res.core ≠ ['a','.','!'].take\n"
                   "      (['a','.','!'].length - trailingPunctCount ['a','.','!'])"
                   " := by\n"
                   "  have hcount : trailingPunctCount ['a','.','!'] = 2 := by\n"
                   "    simp [trailingPunctCount, hd, stripTrailingPunct,"
                   " isTrailingPunct]\n"
                   + _HD_PREAMBLE +
                   "  simp [trailingPunctCount, hd, stripTrailingPunct,"
                   " isTrailingPunct, List.dropWhile]\n",
    },

    {
        "id": "weak-no-peel-at-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Returns the token and the accumulator untouched: the peel never
        # happens. This is the COUNT-INDEPENDENT statement of the boundary
        # violation — it is wrong at every token whose trailing run is non-empty,
        # rather than only on a sub-domain. An earlier revision recorded it as
        # rejected-but-unattributable ("no witness could discriminate it"); that
        # was wrong for the same reason the two boundary cases above were wrongly
        # dropped, and this case is the machine-checked refutation of it: the
        # `hd` technique pins the decoder, the count becomes a literal, and the
        # frozen impl's guard reduces, so the witness is refuted against the
        # FROZEN solution directly with no `witness_reference`.
        "module": _with_impl("    return { core := token, tail := tail }"),
        "refinement": "a faithful counterpart that never moves the trailing run "
                      "off the token leaves the punctuation in the retained core "
                      "on every input, so the failing example — which expects it "
                      "moved into the accumulated suffix — observes the "
                      "unmodified token and stays RED. It would NOT resolve.",
        "rationale": "REJECT from C-core (res.core = token.take (token.length - "
                     "trailingPunctCount token)): whenever the count is non-zero "
                     "the post-image's cut is strictly inside the token, so the "
                     "whole token cannot be the core. Refuted at a 3-character "
                     "token whose trailing run is 2 characters (spec's cut at 1, "
                     "the impl keeps all 3), with the decoded form supplied by "
                     "HYPOTHESIS (`hd`) since the kernel cannot evaluate the "
                     "opaque decoder even at an entity-free literal.",
        "witness": _EXTRACT +
                   "example (hd : entityDecode ['a','.','!'] = ['a','.','!']) :\n"
                   "    ∀ res : Split,\n"
                   "    (peelTrailingPunctuationExec ['a','.','!'] []) = DivM.res res →\n"
                   "    res.core ≠ ['a','.','!'].take\n"
                   "      (['a','.','!'].length - trailingPunctCount ['a','.','!'])"
                   " := by\n"
                   "  have hcount : trailingPunctCount ['a','.','!'] = 2 := by\n"
                   "    simp [trailingPunctCount, hd, stripTrailingPunct,"
                   " isTrailingPunct]\n"
                   + _HD_PREAMBLE +
                   "  simp [trailingPunctCount, hd, stripTrailingPunct,"
                   " isTrailingPunct, List.dropWhile]\n",
    },

    # =====================================================================
    # ADMISSIBILITY — the lane the port dropped, restored. The method has NO
    # `require`, so the sibling's "a normal input satisfies the precondition"
    # probe has no precondition to discharge; but the analogue on a TOTAL
    # carrier is the obligation being UNSATISFIABLE, or degenerate, at exactly
    # an F2P-shaped input — a post-image no impl can meet, or one every impl
    # meets, reads from the outside just like a healthy spec. This case
    # discharges that by EVALUATION, as an in-region `assert`, at a concrete
    # F2P-shaped token (a three-character token ending in one punctuation
    # character, `['a','b','!']`), before closing the frozen obligation
    # verbatim. The four conjuncts pin: the post-image's core projection at
    # count 1 is `['a','b']`; its tail projection at count 1 is `['!']` (with an
    # empty accumulator, so the peel is exactly the moved character); the core
    # projection at count 0 is the WHOLE token; and the count-1 and count-0
    # cores DIFFER. So the post-image is satisfiable at an F2P-shaped input AND
    # non-degenerate across the count, which is what the total-carrier
    # admissibility risk actually is. The impl and the guard are kept verbatim
    # (only the assert is inserted), so the method's own obligation still
    # discharges; the tactic body gains a `decide` arm for the assert goal and
    # `done` guards so no arm can silently absorb an obligation goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START, _IMPL_START + _ADMISS_ASSERT),
            _GOLD_PROOF, _ADMISS_PROOF),
        "rationale": "the post-image is SATISFIABLE and NON-DEGENERATE at an "
                     "F2P-shaped input (a token ending in exactly one "
                     "punctuation character): the in-region assert states the "
                     "spec's OWN boundary expression `token.length - "
                     "trailingPunctCount token` at that token, conditioned on "
                     "each of the two regimes the opaque count can be in, and "
                     "pins core=['a','b'] / tail=['!'] when the count is 1, "
                     "core=the whole token and an empty peel when it is 0, and "
                     "the count-1 core DISTINCT from the count-0 core. The method "
                     "has no `require`, so this — not a precondition discharge "
                     "— is the total-carrier admissibility risk: an obligation "
                     "unsatisfiable, or collapsed to the identity across the "
                     "count, at exactly the shape the failing example has. If "
                     "the assert cannot discharge while the frozen obligation "
                     "still closes, the obligation is degenerate or "
                     "PRECOND-TOO-STRONG. Stated over `trailingPunctCount` "
                     "rather than over a pre-substituted literal index on "
                     "purpose: an assert that mentions neither the count nor "
                     "`.length` is a closed arithmetic fact about `List.take`, "
                     "true of every spec alike, and would discharge with the "
                     "frozen obligation absent — measured, and repaired.",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals) plus 2 AXIOM_TESTS. This
# bundle models the SAME single operation (the trailing-punctuation peel) but
# over an opaque-decoder carrier, so the count-dependent rivals collapse. Every
# sibling case is accounted for below.
#
#   sibling case (nagini)          -> here
#   ---------------------------------------------------------------------
#   pos-control-reshaped           -> pos-unconditional-boundary       PORTED
#   admiss-fshaped-input           -> admiss-nondegenerate-f2p-shape   RE-AIMED
#   weak-prepatch-decoded-boundary -> weak-decoded-boundary            PORTED
#   partial-domain-count1          -> weak-count-hardcoded-one         PORTED
#   frame-mut-middle               -> (none)                           VACUOUS
#   frame-mut-trail                -> (none)                           VACUOUS
#   AXIOM_TESTS (x2)               -> (none)                           DROPPED
#
# ADDED (4, no direct sibling counterpart, but faithful to the sibling's
# lossless / partial-domain SPIRIT on the discriminable part of this carrier):
#   weak-no-peel-at-all         — the count-INDEPENDENT statement of the boundary
#       violation (the peel never happens at all), refuted against the frozen
#       solution on the `hd` technique. Landed by the audit that also refuted the
#       claim it had previously been dropped under.
#   weak-tail-drops-accumulator — attacks C-tail's `++ tail` half (the `tail`
#       binder); the honest velvet analogue of nagini's frame-mut-trail
#       ARGUMENT (a faithful patch that fails to carry the accumulator through),
#       re-expressed as a value violation rather than a permission violation.
#   weak-core-overshoots        — attacks C-core's length bound (`token` binder
#       at `[]`); a partial-domain-style divergence refutable count-free.
#   weak-core-is-accumulator    — attacks C-core's content (`tail` binder at a
#       two-element value); wrong-content dual of the overshoot.
#
# NO LONGER OMITTED — the two boundary rivals, and why the earlier reason was
# wrong. An earlier revision dropped `weak-prepatch-decoded-boundary` and
# `partial-domain-count1` on the ground that "the kernel cannot be shown that any
# concrete literal decodes shorter, so no concrete input separates the boundary
# from the frozen one, and NO discriminating witness exists." The first clause is
# true and the conclusion does not follow: a witness never has to COMPUTE the
# opaque decoder, it may state its refutation at a point described by HYPOTHESIS.
# `hd : entityDecode <tok> = <lit>` supplies exactly the decoded form no literal
# could force, and it is satisfiable precisely BECAUSE the decoder is opaque — no
# tactic can derive `False` from a value assignment to an uninterpreted function,
# which is what the gate's consistency probe checks (it exits 1 for both cases,
# i.e. it cannot refute the hypothesis).
#
# Both are now shipped as `weak-decoded-boundary` and `weak-count-hardcoded-one`,
# refuted against the FROZEN solution — no `witness_reference` needed, because
# pinning the decoder also makes the frozen impl's guard reduce. The same
# hypothesis therefore closes BOTH holes at once: the subject problem the
# `witness_reference` cases work around, and the boundary dimension that was
# recorded as unreachable. Gold's residue is `⊢ False` in both cases (`simp`
# PROVED the spec's equation for the frozen impl and could not for the rival),
# and the flipped claim BUILDS against gold — so the exit code tracks the claim.
# This also restores the PARTIAL-DOMAIN class, which nothing else here covered.
#
#   (admiss-fshaped-input is NO LONGER omitted — see admiss-nondegenerate-f2p-
#   shape above. The earlier reasoning for dropping it was wrong in its second
#   step: "the frozen prove_correct verifies, so the post-image is satisfiable by
#   construction" proves satisfiability at SOME input, not at the F2P-shaped one,
#   and says nothing about the post-image being DEGENERATE — collapsing to the
#   identity across the count, which on this opaque carrier is exactly the failure
#   mode a reader cannot see. The re-aimed case discharges both at a concrete
#   F2P-shaped token by evaluation. The first step stands: there is genuinely no
#   `require` to violate, so the probe is re-aimed rather than transliterated.)
#
# ADMISSIBILITY ASSERT — REPAIRED BY AUDIT (the case passed, and tested nothing).
# The re-aimed case above was correct in its AIM and wrong in its STATEMENT. The
# revision that landed it wrote the assert as literal take/drop at literal
# indices:
#
#     (['a','b','!'] : List Char).take (3 - 1) = ['a','b'] ∧ …
#
# Nothing in that conjunction mentions `trailingPunctCount`, or `.length`, or any
# part of the frozen obligation. It is a closed arithmetic fact about `List.take`
# — true of every spec on this carrier and of no spec in particular — so it could
# not detect a post-image that is unsatisfiable or degenerate at this token; it
# detected that `['a','b','!'].take 2 = ['a','b']`. It also passed honestly,
# which is exactly what makes the defect invisible to the gate: the case was in
# scope, the assert discharged by `decide`, the frozen obligation still closed,
# and the lane counted as present. The rationale's claim that it "evaluates the
# spec's own take/drop image" was the false part — the spec's image is taken at
# `token.length - trailingPunctCount token`, and `3 - 1` is not that expression,
# it is the answer someone computed by hand and substituted in.
#
# Measured, three builds, before repairing anything: (a) the assert conjunction
# discharges by `decide` — it needs no hypothesis and no obligation; (b) the same
# assert with its last conjunct FALSIFIED fails, so the assert does generate its
# own goal (i.e. it was load-bearing for ITS OWN statement, which is what the
# previous audit's ADM-load-bearing probe established — a weaker property than
# being about the spec, and the two were conflated); (c) the goal Lean prints for
# the REPAIRED form names `entityDecode` and `stripTrailingPunct` in its
# turnstile, and the literal form's goal names neither.
#
# The repair states the same three facts over the spec's OWN boundary expression
# and conditions on the opaque count instead of pre-substituting its value, so
# the conjuncts are implications the proof must consume a hypothesis to close.
# Re-measured after the repair: the repaired case VERIFIES (exit 0); the same
# assert with the non-degeneracy conjunct falsified FAILS (exit 1); the assert
# inserted with the FROZEN tactic script unchanged FAILS (exit 1) on an unsolved
# `case «admiss_1: …»` whose turnstile is
# `(entityDecode ['a','b','!']).length - (stripTrailingPunct (entityDecode
# ['a','b','!'])).length = 1 → …`, which is the proof that the goal is stated over
# the obligation's own vocabulary and not over literals; and the repaired assert
# carried over a WRONG impl still FAILS (exit 1), so no `first` arm absorbs an
# obligation goal.
#
# VACUOUS (frame / permission-mutation): nagini's frame-mut-middle /
#   frame-mut-trail rely on a fractional heap permission an impl can overwrite.
#   This backend is referentially transparent and this bundle declares no `mut`
#   PARAMETER (the `let mut` locals in the frozen impl are function-local, not
#   inputs), so there is no read-only input to mutate. The ARGUMENT of
#   frame-mut-trail — a faithful patch that corrupts the accumulator instead of
#   carrying it through — is preserved as a VALUE violation by
#   weak-tail-drops-accumulator. No permission probe fabricated.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this gate ignores it.
# The one opaque callee here (`entityDecode`) is an A-reference validated by
# axiom_check.py, not a G-PBT concern.
#
# COVERAGE. Both spec clauses are attacked (C-tail by weak-tail-drops-
# accumulator; C-core by weak-core-overshoots and weak-core-is-accumulator),
# defended (pos-unconditional-boundary), and probed for degeneracy at an
# F2P-shaped input (admiss-nondegenerate-f2p-shape). All three lanes are present,
# so all three findings this gate exists to make — SPEC-TOO-WEAK,
# SPEC-TOO-STRONG, PRECOND-TOO-STRONG — are reachable. Both input binders move
# across the reject witnesses: `token` ranges over [], ['a'], a 3-character token
# with a 2-character trailing run, and a 5-character token whose decoded form is
# 2 characters; `tail` over [], ['b'], ['x'] and ['x','y']. The boundary-index
# dimension IS probed, in both directions the sibling probed it: wrong index
# origin (weak-decoded-boundary) and wrong count (weak-count-hardcoded-one).
#
# ADDITIONAL RIVALS TRIED (recorded so the gap is visible rather than implied).
# An earlier revision recorded three further wrong impls as "rejected but
# unattributable — none could carry a witness that discriminates", while stating
# two sentences later that the hypothesis technique could land any of them. Those
# two claims contradict each other, and the SECOND is the true one; the first has
# now been machine-refuted rather than reasoned about:
#   * no peel at all (core = token, tail = tail) — LANDED as `weak-no-peel-at-all`
#     above. Measured: witness elaborates against the rival (exit 0), fails against
#     the FROZEN solution (exit 1) with the semantic residue `hd : … hcount : … ⊢
#     False`, and the flipped claim BUILDS against gold (exit 0), so the exit code
#     tracks the claim. No `witness_reference` needed.
#   * projections SWAPPED (core gets the drop, tail gets the take) — REJECTED
#     (exit 1), and the SAME witness discriminates it too (rival exit 0). Not
#     shipped only because `weak-no-peel-at-all` now covers this dimension with a
#     measured witness; the omission is a redundancy call, not a carrier limit.
#   * peel from the FRONT (`token.drop count` / `token.take count`) — REJECTED
#     (exit 1). Same redundancy call.
# So the count-independent boundary dimension is NOT undiscriminable on this
# carrier, and nothing here rests on an "undiscriminable" claim any more.
#
# CORRECT RESHAPES probed for SPEC-TOO-STRONG (attack E). All SIX VERIFY (exit 0),
# so the spec rejects no faithful correct impl that was tried:
#   * `token.splitAt (token.length - count)`, returning the pair's projections.
#   * an explicit let-ladder binding `n`, `c`, `kept`, `moved` separately.
#   * a guard on `stripped.length < decoded.length` — a genuinely DIFFERENT
#     scrutinee from the frozen `decoded ≠ stripped`, so the spec is not over-fit
#     to the frozen guard's form.
#   * a guard whose two branches return the identical take/drop image.
#   * the take/drop pair bound as a tuple and projected.
#   * the REVERSE shape: `(token.reverse.drop count).reverse` for the core and
#     `(token.reverse.take count).reverse` for the peel — i.e. the cut expressed
#     from the END rather than as an index from the front. Closed with
#     `simp [List.drop_reverse, List.take_reverse]`. Worth recording that a first
#     attempt at this one hit a `whnf` heartbeat limit; that was a PROOF-effort
#     failure, not a spec rejection, and re-stating the proof closed it.
# WRONG impls probed for SPEC-TOO-WEAK beyond the shipped rivals (attack D). All
# TEN correctly REJECTED (exit 1), so no spec hole was found: projections swapped,
# core unpeeled with a correct tail, accumulator PREPENDED instead of appended,
# count measured on the RAW token instead of the decoded form, an off-by-one
# boundary (`- count - 1`), peel from the front, no peel at all, the tail's
# boundary hardcoded to 1 while the core's stays correct, the tail duplicating the
# whole token, and the count CLAMPED to at most 1 (`min count 1` — right wherever
# the trailing run is 0 or 1 characters, wrong on longer runs).
#
# SECOND AUDIT PASS — five more wrong impls and three more reshapes, aimed at
# what the above leaves unattacked. Wrong impls, all correctly REJECTED (exit 1),
# so still no spec hole: a rival guarded on `token.length < count` (aimed at the
# Nat-truncation trap, where the guard is infeasible on the real domain but the
# kernel cannot see that); the boundary reconstructed as
# `stripped.length + (token.length - decoded.length)` (arithmetically equal to the
# spec's cut whenever the decoder does not lengthen, so this one probes whether
# the spec is satisfied by a DEFINITIONALLY-equal reshape of the index or pins the
# expression — it is rejected, i.e. the clause is checked semantically, not
# syntactically); stripping the ENCODED token directly instead of the decoded form
# (the index-origin dimension from the other side); the accumulator duplicated
# (`++ tail ++ tail`); and the count taken of the ALREADY-STRIPPED token (which is
# 0 on entity-free tokens, a sub-domain-correct rival). Correct reshapes: a guard
# on `count ≠ 0` (VERIFIES, exit 0 — a third distinct scrutinee) and the count
# INLINED into the boundary with no intermediate locals at all (VERIFIES, exit 0).
# A third reshape, the frozen guard INVERTED (`if decoded = stripped then` with the
# peel in the fall-through), initially failed with `maximum recursion depth has
# been reached` inside `simp` and then VERIFIED (exit 0) once the arm was
# restated to rewrite the count through the equality — recorded because "it failed"
# would have been a false SPEC-TOO-STRONG report, and this is the second time on
# this cell that a proof-effort failure looked like one.
#
# DIVERGENCE (attack F′) — a KNOWN HOLE on this carrier, and the reason is a
# TOOLING one, not a semantic one. Read alongside the frozen file's
# `set_option loom.semantics.termination "total"`: under total semantics a rival
# whose loop carries no decreasing measure IS genuinely rejected, so the class is
# shippable in principle and this battery would be underported without an entry.
# It is not shippable in practice here, and that was measured rather than argued
# (5 builds):
#   * the diverging rival — the correct take/drop image behind `while i < 1 do
#     i := i` — is REJECTED (exit 1) with `Decreasing annotations are required in
#     total correctness semantics`, so the rejection is real and is attributable
#     to termination alone, not to either clause. It is the only rival considered
#     for this battery that a `partial`-semantics carrier would admit.
#   * but NO witness can be attached, because that error is raised on the METHOD
#     ITSELF and survives into the witness file, whose `prove_correct` block the
#     gate strips but whose `method` it necessarily keeps. Three witness shapes
#     were tried against the rival (the `hd`-pinned refutation this battery uses
#     elsewhere, a no-result claim over the extracted program, and one that simps
#     the loop away before projecting) and all three exit 1 — and so does
#     `example : (1:Nat) + 1 = 2 := by decide`, while that same trivial witness
#     exits 0 against the frozen solution. So the rival's module cannot host ANY
#     witness, true or false; the gate's rival-side build is the half that must
#     SUCCEED, so this case can only ever land as `witness-unproven`, which is an
#     inconclusive outcome and a gate ERROR rather than a pass.
# Disposition: KNOWN HOLE, recorded, not shipped — a case whose witness cannot
# elaborate against its own rival would fail the battery while attesting nothing.
# This is NOT the "vacuous class" disposition: the class is real here and the spec
# does reject it; what is missing is a way to WITNESS it, which is a limitation of
# the witness harness against a method-level linter error, not of the spec. Worth
# reporting upstream as such: a rival rejected by a method-level obligation is
# unwitnessable by construction under the current two-build protocol.
AXIOM_TESTS = []
