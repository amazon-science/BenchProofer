"""properties.py — G-PBT falsification battery for astropy__astropy-14598 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct recoverSegmentText`` obligation survives with a
byte-identical statement) and swaps in a candidate impl; it is checked by the
real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (``recoverSegmentText (field : List Char) return (out : Option
(List Char))``): the per-record literal-text recovery of one column-width record
of a value written across several such records. One ``ensures`` clause, pinned to
a fully-unfolded ``def`` over the method's own argument (the ``axioms`` region is
EMPTY — no opaque answer key to echo):

    ensures out = recovered field

where ``recovered field = (recordContent field).map (dropTrailingAmp ∘
rstripSpaces)`` composes independently-attackable transforms over the sole binder
``field``:

  * CONTENT — ``recordContent field`` reads the record's content off the
    record's own grammar: the content is bookended by delimiters, and the
    delimiter that CLOSES it is one past which the record holds nothing but
    padding and at most an annotation (``closesContent`` /
    ``onlyPaddingThenAnnotation``). Three things are load-bearing and each is
    attacked by a distinct rival: (a) which delimiter closes the content — a
    delimiter that merely happens to be followed by padding does NOT close it
    if real content follows; (b) the captured characters are taken VERBATIM — a
    doubled delimiter ``''`` stays doubled, i.e. the recovery does NOT collapse
    ``''`` → ``'`` on a single record (that collapse is
    ``collapseDoubledQuotes``, present only as a negative reference; the single
    whole-value collapse happens once downstream after all records are
    concatenated); and (c) text in which no delimiter closes a content is NOT a
    record, and yields ``none`` rather than a fabricated literal text.
  * PAD-STRIP — ``rstripSpaces`` removes the right column-width padding.
  * MARKER-STRIP — ``dropTrailingAmp`` removes one trailing continuation marker
    when present.

SOLE INPUT BINDER: ``field : List Char``. It is load-bearing through and through
— it selects which delimiter closes the content, whether the text is a record at
all, whether padding is present, and whether a trailing marker is present. The
seven reject witnesses drive it to SEVEN DISTINCT inputs (pts = 7) so the
manifest demonstrates the post-image's dependence on the closing-delimiter rule,
on the doubled-delimiter verbatim content, on a non-empty content, on the
trailing marker, on the trailing padding, on the record grammar being consulted
at all, and on non-records yielding ``none`` — not on a single pinned shape.

CARRIER NOTE — the carrier is FULLY COMPUTABLE. Every helper here
(``recordContent`` / ``closesContent`` / ``onlyPaddingThenAnnotation`` /
``firstPrefix`` / ``rstripSpaces`` / ``dropTrailingAmp`` / ``recovered``, and the
negative reference ``collapseDoubledQuotes``) is a concrete ``def`` over
``List Char`` with ``DecidableEq``. So a witness reaches the post-image through
Velvet's tester machinery (``recoverSegmentTextTester field = false`` says the
extracted program's result violates the postcondition at that concrete input) and
closes by ``decide``, checked in a file whose ``prove_correct`` block is stripped
so no tactic script can mask the verdict. Because both the extracted program and
the pure model reduce fully at a literal ``List Char``, every witness here is a
plain literal input — no conditioning is needed. Each was built the two required
ways with ``scripts/lean_verify.sh``: the tester elaborates green against its
rival (``decide`` proves ``= false``) and FAILS against the frozen solution
(``decide`` proves the same proposition is *false*, i.e. gold satisfies the
postcondition at that input).

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally-different but
    behaviourally-identical correct impls (a direct return of the grounded model;
    a reshape that names each transform through its helper ``def``) must verify,
    else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — RE-AIMED. The sibling self-asserts an F2P-shaped input
    satisfies its fractional-permission ``Requires``. This backend's method has
    NO ``require`` (the pre-conditions region is empty), so that probe is
    vacuous — every input is admitted, and the recovery's answer on a text that
    is not a record is part of the contract (``none``) rather than something a
    precondition excuses. The residual admissibility risk on a total domain is a
    DEGENERATE post-image: a spec no impl distinguishes reads exactly like one
    every impl meets. ``admiss-nondegenerate`` discharges an in-region ``assert``
    pinning four genuinely-distinct recovered values at F2P-shaped inputs (a
    doubled-delimiter tail kept verbatim, a padded value stripped, a trailing
    marker removed, an annotated record's content read correctly); the impl is
    kept verbatim so the method's own obligation still discharges.
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling carries TWO
    mandatory frame rivals (a write into the read-only ``segment`` held at
    ``Acc(.,1/2)``, and a write into the read-only ghost ``witness``). Lean/Velvet
    are referentially transparent: ``field`` is an immutable ``List Char`` value
    declared read-only (not ``mut``), there is no heap, no aliasing, no fractional
    permission. There is no read-only input to overwrite and no permission system
    to trip, so the class has no carrier analogue. NOT ported (fabricating a
    substitute would test nothing). See the footer for the case-by-case
    accounting.
  * DIVERGENCE / NON-TERMINATION: NONE in the sibling (it carries no
    ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case), so nothing to port,
    and no known hole either. Two things are worth separating, because an earlier
    version of this bullet ran them together. The frozen impl IS loop-free (a
    straight-line ``let`` chain), so THIS bundle ships no divergence reject case:
    there is no loop in the frozen body to make spin. But "a diverging impl cannot
    even be written" is withdrawn as a reason: a rival rewrites the whole impl
    region, so it can splice a loop that was not there. What refuses it is the
    verifier. This bundle sets ``loom.semantics.termination "total"``, under which
    a postcondition is claimed of ALL runs, not only terminating ones, so every
    loop owes a decreasing measure AND its descent; the option cannot drift from
    the file's ``open TotalCorrectness DemonicChoice`` because the ``set_option``
    elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Measured here with the proof
    reduced to a bare ``loom_solve``: a spliced
    ``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z`` whose body
    is ``z := z + 1`` is REJECTED on the measure's own goal,
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. So the class is closed by
    the descent obligation, and inapplicable to a shipped case only because the
    frozen impl has no loop.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``recovered field``,
    a fully-unfolded ``def`` over the method's own argument; there is no answer-key
    term a wrong impl could echo. The cheapest correct impl computes the recovery
    honestly, which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-domain (a doubled delimiter wrongly
    collapsed, the wrong delimiter taken to close the content, an empty content,
    a trailing marker not removed, trailing padding not removed, the record
    grammar not consulted at all, a non-record given a fabricated answer).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The bundle declares no axiom
(mapping.md §3: the changed op is modeled deeply and concretely, validated by
G-CONF, so G-AX is vacuous); the sibling's ``AXIOM_TESTS`` is likewise empty. The
G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14598"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (between and INCLUDING the
# ---- markers). Every full-body variant replaces exactly this text, so each edit
# ---- lies wholly inside the one -- impl-start .. -- impl-end region and
# ---- same_spec holds by construction. Presence + uniqueness asserted at load.
_IMPL = """    -- impl-start
    let out : Option (List Char) :=
      (recordContent field).map (fun content =>
        let trimmed : List Char := (content.reverse.dropWhile (· = spaceCh)).reverse
        if trimmed.getLast? = some '&' then trimmed.dropLast else trimmed)
    return out
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- rival that reshapes the impl retunes it without touching the spec or
# ---- dropping the `prove_correct recoverSegmentText` obligation.
_PROOF_GOLD = """prove_correct recoverSegmentText by
  loom_solve
  simp only [recovered, dropTrailingAmp, rstripSpaces]"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a flat proof body: when the impl returns the grounded model (or names each
# ---- transform through its helper `def`), `loom_solve` alone discharges the
# ---- equality. The reject rivals keep the gold proof (they are refuted by the
# ---- witness, not by whether the tuned script happens to close), so only the
# ---- soundness positives retune the proof.
_PROOF_FLAT = "prove_correct recoverSegmentText by\n  loom_solve"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `recoverSegmentTextTester field = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped, so no tactic
# ---- script can mask the verdict. Every argument is a concrete `List Char`
# ---- literal so `decide` reduces the extracted program fully (the carrier has
# ---- DecidableEq and every helper is a concrete def). ----
def _tester(body):
    return ("\n"
            "extract_program_for recoverSegmentText\n"
            "prove_precondition_decidable_for recoverSegmentText\n"
            "prove_postcondition_decidable_for recoverSegmentText\n"
            "derive_tester_for recoverSegmentText\n\n" + body)


def _witness(field_literal):
    return _tester(
        f"example : recoverSegmentTextTester {field_literal} = false := by\n"
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
        # no intermediate lets at all — maximally structurally different from the
        # gold let-chain. `out` IS `recovered field`, so the ensures holds
        # trivially; the reproof is a bare `loom_solve`. Also the honest
        # no-ungrounded-echo control: the model IS the real work, so a direct
        # return is correct, not a cheat.
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    return recovered field\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_FLAT),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`recovered field` directly (no intermediate lets). `out` IS that "
            "model, so `out = recovered field` holds on the whole domain; the "
            "reproof is `loom_solve`. If this fails to verify the spec is over-fit "
            "to the let-chain code shape (SPEC-TOO-STRONG). (Sibling: "
            "pos-recover-reshape / pos-unescape-reshape — a structurally-different "
            "correct impl.)"),
    },
    {
        "id": "pos-control-named-transforms",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the pad-strip and the marker-strip through their own
        # helper `def`s (rstripSpaces / dropTrailingAmp) instead of inlining the
        # reverse-dropWhile-reverse pad-strip and the getLast?/if marker-strip.
        # Every computed value is identical, so the ensures still holds on the
        # whole domain; the reproof is `loom_solve` (the helpers ARE the
        # definitional unfolding of `recovered`).
        "module": _swap(
            _swap(_BASE, _IMPL,
                  "    -- impl-start\n"
                  "    let out : Option (List Char) :=\n"
                  "      (recordContent field).map (fun content =>\n"
                  "        dropTrailingAmp (rstripSpaces content))\n"
                  "    return out\n"
                  "    -- impl-end"),
            _PROOF_GOLD, _PROOF_FLAT),
        "rationale": (
            "naming the pad-strip and marker-strip through their helper `def`s "
            "(rstripSpaces / dropTrailingAmp) computes the same values as the "
            "inlined gold body, so `out = recovered field` still holds on the whole "
            "domain. A correct reshape must verify, else the postcondition is "
            "SPEC-TOO-STRONG (rejects a faithful impl over the shape of the "
            "transform chain). (Sibling: pos-*-reshape, reshaped to a "
            "helper-named form.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The method has NO `require` (pre-conditions region
    # empty), so the sibling's "a normal input satisfies the precondition" probe
    # is vacuous: nothing could exclude an F2P-shaped input, and the answer on a
    # text that is not a record is part of the contract rather than excused. The
    # residual admissibility risk on a total domain is a DEGENERATE post-image — a
    # spec no impl distinguishes reads exactly like one every impl meets. This case
    # discharges an in-region `assert`, at four fully concrete F2P-shaped inputs,
    # that the recovery is NON-DEGENERATE: a doubled-delimiter tail is kept
    # VERBATIM (the headline behaviour, NOT collapsed), a padded value is stripped,
    # a trailing-marker value is stripped, and an ANNOTATED record's content is
    # read off the record grammar (the annotation is not swallowed into the
    # content) — four genuinely distinct recovered values that jointly exercise
    # every transform. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the proof gains a `decide` arm to clear the
    # assert goal. The assert is LIVE, not decoration: a false claim about the
    # same points leaves an unsolved goal (checked by hand).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      recovered ['\\'', 'a', '\\'', '\\'', '\\''] = some ['a', '\\'', '\\''] ∧\n"
                  "      recovered ['\\'', 'a', ' ', ' ', '\\''] = some ['a'] ∧\n"
                  "      recovered ['\\'', 'a', '&', '\\''] = some ['a'] ∧\n"
                  "      recovered ['\\'', 'a', '\\'', ' ', '/', ' ', 'c'] = some ['a']))\n"),
            _PROOF_GOLD,
            "prove_correct recoverSegmentText by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp only [recovered, dropTrailingAmp, rstripSpaces]\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at concrete "
            "F2P-shaped inputs: a doubled-delimiter tail must be kept VERBATIM "
            "(the record carrying `a''` recovers to some ['a','\\'','\\''], NOT the "
            "collapsed some ['a','\\'']), a space-padded record must be stripped to "
            "some ['a'], a trailing-marker record must be stripped to some ['a'], "
            "and an ANNOTATED record must have its content read off the record "
            "grammar (some ['a'], the annotation not swallowed) — four distinct "
            "recovered values exercising every transform. The in-region assert must "
            "discharge (else the obligation is degenerate); the impl is kept "
            "verbatim so `out = recovered field` still verifies. (Sibling: "
            "admiss-recover-fshape, re-aimed from precondition admissibility to "
            "post-image non-degeneracy since this backend's method carries no "
            "`require` and there is no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival breaks exactly
    # one composed transform of `recovered`; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-collapse-doubled-quote",
        "kind": "uniqueness",
        "expect": "reject",
        # Reintroduces the per-record doubled-delimiter collapse: after stripping,
        # rewrite each `''` → `'` a second time. Correct on every record WITHOUT a
        # surviving doubled delimiter; diverges exactly on a record carrying `''`.
        "module": _swap(_BASE, _IMPL,
                        "    -- impl-start\n"
                        "    let out : Option (List Char) :=\n"
                        "      (recordContent field).map (fun content =>\n"
                        "        let trimmed : List Char := (content.reverse.dropWhile (· = spaceCh)).reverse\n"
                        "        let collapsed : List Char := collapseDoubledQuotes trimmed\n"
                        "        if collapsed.getLast? = some '&' then collapsed.dropLast else collapsed)\n"
                        "    return out\n"
                        "    -- impl-end"),
        "refinement": (
            "the faithful counterpart keeps the per-record doubled-delimiter "
            "collapse that the single whole-value decode already performs once "
            "downstream. The duplicate collapse silently drops a delimiter whenever "
            "a doubled one straddles a fixed-width record boundary — exactly the "
            "position/length-dependent round-trip mismatch the issue reports; a "
            "value ending in a doubled delimiter comes back one delimiter short, so "
            "the round-trip assertion FAILS. It does NOT resolve."),
        "rationale": (
            "REJECT from `out = recovered field` via the VERBATIM-content part: the "
            "spec takes the record's content as-is, but this rival rewrites `''` → "
            "`'`. Verifying would be SPEC-TOO-WEAK (the no-per-record-collapse "
            "behaviour unpinned). Refuted on the surviving-doubled-delimiter "
            "sub-domain — the record carrying `a''`, where gold recovers "
            "some ['a','\\'','\\''] and the rival recovers some ['a','\\'']. "
            "(Sibling: partial-double-unescape.)"),
        "witness": _witness(r"['\'', 'a', '\'', '\'', '\'']"),
    },
    {
        "id": "weak-wrong-closing-delimiter",
        "kind": "uniqueness",
        "expect": "reject",
        # Takes the content to be closed by the FIRST delimiter whose very next
        # character is padding or the annotation introducer, instead of the one
        # past which only padding and at most an annotation follow — and then
        # treats every text as a record. Correct on every record whose content
        # holds no interior delimiter followed by more content; diverges on one
        # that does.
        "module": _swap(_BASE, _IMPL,
                        "    -- impl-start\n"
                        "    let closesEarly : List Char → Bool := fun rest =>\n"
                        "      match rest with\n"
                        "      | c :: more =>\n"
                        "          c == quoteCh &&\n"
                        "            (match more with\n"
                        "             | [] => true\n"
                        "             | d :: _ => d == spaceCh || d == annotCh)\n"
                        "      | [] => false\n"
                        "    let contentEarly : List Char → List Char := fun f =>\n"
                        "      match f with\n"
                        "      | [] => []\n"
                        "      | c :: rest =>\n"
                        "          if c == quoteCh then\n"
                        "            match firstPrefix closesEarly rest with\n"
                        "            | some content => content\n"
                        "            | none => []\n"
                        "          else []\n"
                        "    let out : Option (List Char) :=\n"
                        "      some (\n"
                        "        let content : List Char := contentEarly field\n"
                        "        let trimmed : List Char := (content.reverse.dropWhile (· = spaceCh)).reverse\n"
                        "        if trimmed.getLast? = some '&' then trimmed.dropLast else trimmed)\n"
                        "    return out\n"
                        "    -- impl-end"),
        "refinement": (
            "the faithful counterpart ends the record's content at a delimiter that "
            "merely happens to be followed by padding, losing everything past it. A "
            "value whose framing puts a delimiter before a space partway through a "
            "record loses that record's remaining text, so the round-trip assertion "
            "FAILS. It does NOT resolve."),
        "rationale": (
            "REJECT from `out = recovered field` via the CLOSING-DELIMITER rule: "
            "the spec's content ends at the delimiter past which the record holds "
            "only padding and at most an annotation, but this rival stops at the "
            "first delimiter followed by padding. Verifying would be SPEC-TOO-WEAK "
            "(which delimiter closes the content left unpinned). Refuted on the "
            "interior-delimiter-then-padding sub-domain — the record carrying "
            "`a' x` (`['\\'','a','\\'',' ','x','\\'']`), where gold keeps the "
            "tail and the rival drops it. This is the sub-domain the collapse rival "
            "agrees with gold on, so the two do NOT share a witness. (Sibling: "
            "partial-drop-last, re-aimed to the closing-delimiter rule.)"),
        "witness": _witness(r"['\'', 'a', '\'', ' ', 'x', '\'']"),
    },
    {
        "id": "weak-empty-capture",
        "kind": "uniqueness",
        "expect": "reject",
        # Cheapest impl ignoring the field: return an empty recovery. Trivially
        # wrong (recovered field ≠ some [] for any record with non-padding
        # content). Supporting near-miss on the content-nonempty behaviour.
        "module": _swap(_BASE, _IMPL,
                        "    -- impl-start\n"
                        "    return some ([] : List Char)\n"
                        "    -- impl-end"),
        "refinement": (
            "returning the empty recovery is no faithful patch of the content read; "
            "every non-trivial record's literal text is lost, so the round-trip "
            "assertion FAILS. It does NOT resolve. (Supporting near-miss; still "
            "carries a real refinement.)"),
        "rationale": (
            "REJECT from `out = recovered field`, which forces a non-empty result "
            "for a record with non-padding content. Refuted at the record carrying "
            "`a` (`['\\'','a','\\'']`), where gold recovers some ['a'] and the rival "
            "recovers some []. (Sibling: empty-recover.)"),
        "witness": _witness(r"['\'', 'a', '\'']"),
    },
    {
        "id": "weak-keep-trailing-marker",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the trailing-marker strip: return the padding-stripped content
        # without removing a trailing continuation marker. Correct on every record
        # WITHOUT a trailing marker; diverges on one that ends in the marker.
        "module": _swap(_BASE, _IMPL,
                        "    -- impl-start\n"
                        "    let out : Option (List Char) :=\n"
                        "      (recordContent field).map (fun content =>\n"
                        "        (content.reverse.dropWhile (· = spaceCh)).reverse)\n"
                        "    return out\n"
                        "    -- impl-end"),
        "refinement": (
            "a recovery that keeps the trailing continuation marker leaves the "
            "join glyph inside the per-record text, so the concatenated value "
            "carries a stray marker the original never had and the round-trip "
            "assertion FAILS. It does NOT resolve."),
        "rationale": (
            "REJECT from `out = recovered field` via the MARKER-STRIP part: the "
            "spec removes one trailing continuation marker when present, but this "
            "rival keeps it. Verifying would be SPEC-TOO-WEAK (the marker-strip "
            "unpinned). Refuted on the trailing-marker sub-domain — the record "
            "carrying `a&` (`['\\'','a','&','\\'']`), where gold recovers some ['a'] "
            "and the rival recovers some ['a','&']. (No direct sibling; this backend "
            "models the trailing-marker strip as a distinct transform of "
            "`recovered`, so it gets its own attack.)"),
        "witness": _witness(r"['\'', 'a', '&', '\'']"),
    },
    {
        "id": "weak-keep-trailing-padding",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the padding strip: read the content and remove a trailing marker,
        # but do NOT strip the trailing column-width padding. Correct on every
        # record without trailing padding; diverges on a padded one.
        "module": _swap(_BASE, _IMPL,
                        "    -- impl-start\n"
                        "    let out : Option (List Char) :=\n"
                        "      (recordContent field).map (fun content =>\n"
                        "        if content.getLast? = some '&' then content.dropLast else content)\n"
                        "    return out\n"
                        "    -- impl-end"),
        "refinement": (
            "a recovery that leaves the right column-width padding attaches trailing "
            "spaces to the per-record text, so the concatenated value carries "
            "padding the original never had and the round-trip assertion FAILS. It "
            "does NOT resolve."),
        "rationale": (
            "REJECT from `out = recovered field` via the PAD-STRIP part: the spec "
            "removes the trailing space padding, but this rival keeps it. Verifying "
            "would be SPEC-TOO-WEAK (the pad-strip unpinned). Refuted on the "
            "trailing-padding sub-domain — the record carrying `a  ` "
            "(`['\\'','a',' ',' ','\\'']`), where gold recovers some ['a'] and the "
            "rival recovers some ['a',' ',' ']. This is the sub-domain the marker "
            "rival agrees with gold on, so the two do NOT share a witness. (No "
            "direct sibling; this backend models the pad-strip as a distinct "
            "transform of `recovered`, so it gets its own attack.)"),
        "witness": _witness(r"['\'', 'a', ' ', ' ', '\'']"),
    },
    {
        "id": "weak-ignore-record-grammar",
        "kind": "uniqueness",
        "expect": "reject",
        # Never consults the record grammar at all: assume the record's final
        # character IS the closing delimiter, so the content is just the text
        # with its first and last characters removed, and every text is a record.
        # Correct on a record that ends exactly at its closing delimiter;
        # diverges on one that carries anything after it.
        "module": _swap(_BASE, _IMPL,
                        "    -- impl-start\n"
                        "    let out : Option (List Char) :=\n"
                        "      some (\n"
                        "        let content : List Char := field.tail.dropLast\n"
                        "        let trimmed : List Char := (content.reverse.dropWhile (· = spaceCh)).reverse\n"
                        "        if trimmed.getLast? = some '&' then trimmed.dropLast else trimmed)\n"
                        "    return out\n"
                        "    -- impl-end"),
        "refinement": (
            "the faithful counterpart assumes a record ends at its closing "
            "delimiter and simply drops the outer two characters. On a record that "
            "carries an annotation past that delimiter the annotation is swallowed "
            "into the literal text and the closing delimiter itself is kept, so the "
            "recovered value is corrupted wholesale and the round-trip assertion "
            "FAILS. It does NOT resolve."),
        "rationale": (
            "REJECT from `out = recovered field`, whose content is read off the "
            "record's GRAMMAR rather than off the record's length. Verifying would "
            "be SPEC-TOO-WEAK (a recovery that never locates the closing delimiter "
            "would satisfy the spec). Refuted on the annotated-record sub-domain — "
            "the record `'' / c` (`['\\'','\\'',' ','/',' ','c']`), whose content is "
            "empty so gold recovers some [], while the rival recovers "
            "some ['\\'',' ','/',' '] — it drops only the final `c` and keeps the "
            "interior delimiter and the annotation. This is the sub-domain every "
            "other rival agrees with gold on, so it shares no witness. (No sibling; "
            "this rival pins that the record grammar is consulted at all.)"),
        "witness": _witness(r"['\'', '\'', ' ', '/', ' ', 'c']"),
    },
    {
        "id": "weak-fabricate-on-non-record",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on every record, but claims a literal text (`some`) even for a
        # text in which no delimiter closes a content — where the spec says there
        # is none. Correct on the whole record sub-domain; diverges exactly on the
        # non-records.
        "module": _swap(_BASE, _IMPL,
                        "    -- impl-start\n"
                        "    let content : List Char := (recordContent field).getD []\n"
                        "    let trimmed : List Char := (content.reverse.dropWhile (· = spaceCh)).reverse\n"
                        "    let out : Option (List Char) :=\n"
                        "      some (if trimmed.getLast? = some '&' then trimmed.dropLast else trimmed)\n"
                        "    return out\n"
                        "    -- impl-end"),
        "refinement": (
            "the faithful counterpart answers a text that is no record at all with "
            "a fabricated empty literal text instead of reporting that there is "
            "none. The surrounding code hands such a text on UNCHANGED to a "
            "different path; a recovery that instead swallows it into an empty "
            "value destroys the text of every malformed record, and the round-trip "
            "assertion FAILS on any value containing one. It does NOT resolve."),
        "rationale": (
            "REJECT from `out = recovered field` via the NON-RECORD part: the spec "
            "says a text in which no delimiter closes a content has NO literal text "
            "(`none`), and this rival fabricates `some []`. Verifying would be "
            "SPEC-TOO-WEAK (the non-record answer unpinned, letting an impl silently "
            "absorb malformed input). Refuted at the non-record `abc` "
            "(`['a','b','c']`), where gold recovers none and the rival recovers "
            "some []. Every other rival agrees with gold here (they all keep the "
            "`recordContent` guard), so this witness is unshared. (No sibling; the "
            "sibling's method is total and has no none-answer to attack.)"),
        "witness": _witness(r"['a', 'b', 'c']"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
# The sibling battery ships 8 SPEC cases (2 soundness positives, 1 admissibility,
# 5 uniqueness rivals — two of which are MANDATORY frame-mutation rivals) plus an
# EMPTY axiom lane (AXIOM_TESTS = []). The sibling contracts TWO functions over
# full/half-permission `List[int]` code points — `recover_payload(segment)` (full
# copy) and `unescape_value(captured, witness)` (single un-escape + a round-trip
# witness clause). This velvet bundle models the SAME observable behaviour — the
# per-record literal-text recovery the round-trip test exercises — but DEEPLY and
# as ONE narrowed method `recoverSegmentText` whose post-image `recovered field`
# composes the record-grammar content read, the pad-strip, and the marker-strip.
# The nagini `unescape`'s doubled-delimiter collapse is present here only as the
# NEGATIVE reference `collapseDoubledQuotes`, and the carrier is referentially
# transparent, which reshapes the map:
#
#   sibling case              kind          -> here                            disposition
#   ---------------------------------------------------------------------------------------
#   pos-recover-reshape       soundness     -> pos-control-direct-model        RE-SHAPED
#   pos-unescape-reshape      soundness     -> pos-control-named-transforms    RE-SHAPED
#   admiss-recover-fshape     admissibility -> admiss-nondegenerate            RE-AIMED
#   frame-mutate-segment      uniqueness    -> (none)                          VACUOUS
#   frame-mutate-witness      uniqueness    -> (none)                          VACUOUS
#   partial-drop-last         uniqueness    -> weak-wrong-closing-delimiter    RE-AIMED
#   partial-double-unescape   uniqueness    -> weak-collapse-doubled-quote     PORTED
#   empty-recover             uniqueness    -> weak-empty-capture              PORTED
#   (no sibling)              uniqueness    -> weak-keep-trailing-marker       ADDED
#   (no sibling)              uniqueness    -> weak-keep-trailing-padding      ADDED
#   (no sibling)              uniqueness    -> weak-ignore-record-grammar      ADDED
#   (no sibling)              uniqueness    -> weak-fabricate-on-non-record    ADDED
#   AXIOM_TESTS (none)        axiom         -> (none)                          N/A (G-AX)
#
# 2 uniqueness ported/re-aimed from the value rivals + 4 added (the extra
# behaviours this carrier models explicitly), 1 admissibility re-aimed, 2
# soundness re-shaped; 2 frame rivals vacuous; axiom lane empty.
#
# RE-SHAPED (both positives): the sibling's positives are loop reshapes of the two
#   nagini functions (local-var capture; branch reorder). This carrier has no loop
#   — the modeled core is a straight-line transform chain — so the two
#   maximally-different-yet-correct shapes are a direct return of the grounded
#   model (pos-control-direct-model) and a helper-named transform chain
#   (pos-control-named-transforms). Both verify (`lake` builds confirmed).
# RE-AIMED (admiss-recover-fshape -> admiss-nondegenerate): the sibling asserts an
#   F2P-shaped escaped payload satisfies its no-'/' half-permission Requires. This
#   backend's method has no `require`, so that probe is vacuous; the sharper
#   residual risk is a DEGENERATE post-image, so the case is re-aimed to a live
#   in-region assert pinning four distinct recovered values (verbatim
#   doubled-delimiter tail / stripped padding / stripped marker / annotated record)
#   at F2P-shaped inputs — the assert is live (a false variant leaves an unsolved
#   goal, checked).
# PORTED (partial-double-unescape -> weak-collapse-doubled-quote): the sibling's
#   double-un-escape rival is exactly the per-record doubled-delimiter collapse
#   this bundle forbids; ported by reintroducing `collapseDoubledQuotes` in the
#   impl. Refuted on a record carrying a doubled delimiter.
# RE-AIMED (partial-drop-last -> weak-wrong-closing-delimiter): the sibling drops
#   the LAST code point. On this carrier the corresponding defect is more precisely
#   taking the WRONG delimiter to close the record's content (the first one merely
#   followed by padding, rather than the one past which only padding and at most an
#   annotation follow); re-aimed to that. Same clause (the content read), same
#   observable (a record's text past an interior delimiter is lost). Refuted on a
#   record whose content holds an interior delimiter followed by more content.
# PORTED (empty-recover -> weak-empty-capture): direct port of the empty-return
#   near-miss. Refuted on any non-empty content.
# ADDED (weak-keep-trailing-marker, weak-keep-trailing-padding): the nagini
#   `recover_payload` post is a pure full copy (`ToSeq(Result())==ToSeq(segment)`),
#   with no pad-strip or marker-strip clause to attack — those transforms live in
#   the untested surroundings on nagini. This velvet bundle models the recovery as
#   the FULL composition over the record content, so the pad-strip and marker-strip
#   are independent top-level behaviours of the sole `ensures`. Each is attacked by
#   a dedicated rival so every transform of `recovered` is defended — not
#   fabricated wrongness: each is a real F2P-relevant violation (stray padding /
#   stray join marker in the round-tripped value) with a machine-checked
#   discriminating witness.
# ADDED (weak-ignore-record-grammar, weak-fabricate-on-non-record): the recovery
#   reads its content off the record's GRAMMAR, not off the record's length, and it
#   reports that a text which is no record at all carries NO literal text. Both are
#   top-level behaviours of the sole `ensures` that no other rival probes: the
#   grammar rival is correct on every record ending exactly at its closing
#   delimiter and only diverges on an ANNOTATED record, and the non-record rival is
#   correct on the whole record sub-domain and only diverges off it. Each is a real
#   violation (an annotation swallowed into the value; a malformed record silently
#   absorbed) with a machine-checked discriminating witness.
# VACUOUS (frame-mutate-segment, frame-mutate-witness): the sibling's two MANDATORY
#   frame rivals write into read-only half-permission inputs (`Acc(segment,1/2)`,
#   `Acc(witness,1/2)`), rejected by Viper's permission system. This backend is
#   referentially transparent: `field` is an immutable `List Char` value declared
#   read-only (not `mut`), there is no heap, no aliasing, no fractional permission,
#   no permission system. There is no read-only input to overwrite and no frame
#   clause to violate, so the class has no carrier analogue. Omitted as a genuine
#   carrier fact, NOT fabricated (porting map: this class is vacuous on a
#   referentially-transparent backend). Also note the sibling's second contracted
#   function `unescape_value` takes a second `witness` binder with a round-trip
#   clause (B2); that binder and clause model the caller-held original the F2P
#   COMPARES against — an out-of-method observation this narrowed single-method
#   core does not carry, so there is no B2 counterpart to attack here.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = recovered field` has
#   ONE binder `field : List Char`, and `recovered` composes the record-content
#   read (itself carrying the closing-delimiter rule, the verbatim-content rule and
#   the non-record answer) with the pad-strip and the marker-strip. The seven
#   reject witnesses probe SEVEN DISTINCT input points (pts=7):
#     * weak-collapse-doubled-quote     ['\'','a','\'','\'','\'']       (a'')
#     * weak-wrong-closing-delimiter    ['\'','a','\'',' ','x','\'']    (a' x)
#     * weak-empty-capture              ['\'','a','\'']                 (a)
#     * weak-keep-trailing-marker       ['\'','a','&','\'']             (a&)
#     * weak-keep-trailing-padding      ['\'','a',' ',' ','\'']         (a  )
#     * weak-ignore-record-grammar      ['\'','\'',' ','/',' ','c']     ('' / c)
#     * weak-fabricate-on-non-record    ['a','b','c']                   (abc)
#   `field` ranges over seven genuinely different shapes (surviving doubled
#   delimiter / interior delimiter followed by more content / bare content /
#   trailing marker / trailing padding / annotated record / non-record), and each
#   behaviour of `recovered` is independently attacked: the CONTENT read by all
#   three of its load-bearing rules (weak-collapse-doubled-quote for verbatim
#   content, weak-wrong-closing-delimiter for which delimiter closes it,
#   weak-ignore-record-grammar for the grammar being consulted at all) plus the
#   non-record answer (weak-fabricate-on-non-record) and a total-failure near-miss
#   (weak-empty-capture); PAD-STRIP by weak-keep-trailing-padding; MARKER-STRIP by
#   weak-keep-trailing-marker. No binder shape is pinned across the reject set, and
#   each pair whose sub-domains overlap (collapse vs wrong-delimiter; marker vs
#   padding; grammar vs non-record) is separated at the input that distinguishes
#   them, so no two rivals share a witness for a near-miss it does not actually
#   fail at.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3: the changed op
#   is modeled deeply and concretely, validated by G-CONF, so G-AX is vacuous);
#   the sibling's AXIOM_TESTS is likewise empty. This gate ignores AXIOM_TESTS
#   regardless.
AXIOM_TESTS = []
