"""properties.py — PBT falsification manifest for django__django-11276 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the positive controls, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
The modeled function rewrites a text (as a list of code points) into its
HTML-safe form, one code point at a time:

    implementation_escape (s : List Char) : List Char

pinned by the single load-bearing clause

    result = escapeSeq s

`escapeSeq` is a FULLY TRANSPARENT deep model living in the spec view: it is the
in-order concatenation of the per-code-point encoding `escapeChar`, which maps
each of the five HTML-significant characters to its entity form and every other
character to itself. There is NO opaque callee, so every rival is refutable by
`decide` at a concrete input — no carrier conditioning is needed, and no witness
binds a hypothesis (nothing to be inconsistent).

The single clause pins the whole output to the input along several independent,
transparently-checkable axes, and the rivals attack each:

  * the SUBSTITUTION TABLE — each significant code point must map to its exact
    entity bytes. All five entries are attacked: `rival-apos-decimal` (emits
    legacy `&#39;` for the apostrophe), `rival-drop-quot` (double-quote passes
    through), `rival-drop-amp` (ampersand passes through), and `rival-swap-lt-gt`
    (the two angle-bracket entities are transposed);
  * the IDENTITY ARM — every code point that is NOT one of the five maps to
    ITSELF, so the clause forbids OVER-escaping just as firmly as it forbids
    under-escaping. Attacked by `rival-over-escape-bang`, which entity-encodes an
    ordinary character;
  * the CONCATENATION ORDER — the per-code-point encodings appear in input
    order. Attacked by `rival-order-reversed`, which folds in reverse;
  * DOMAIN COMPLETENESS — the clause pins EVERY position, not a sub-domain.
    Attacked by `partial-domain-apos-first`, which is correct everywhere except
    a leading apostrophe.

PORTING NOTES (which nagini cases port, which are omitted)
----------------------------------------------------------
The nagini sibling contracts the same per-code-point escaper plus five constant
round-trip clauses over a decoder and an axiom lane. This Lean bundle models
only the purely functional escaper core (`escapeSeq`), so the round-trip
constants and the decoder have no counterpart here; that is carrier narrowing,
not an omission to hide.

  * nagini `pos-control-reordered` / `pos-control-seg-local` (structurally
    different but correct impls) -> `pos-flatmap-form` and `pos-foldr-form`: two
    correct impls in shapes distinct from the frozen accumulating `for`-loop (a
    `List.flatMap`, and a right fold). Both proofs re-closed by induction. If
    either fails to verify the spec is over-fit to the loop shape
    (SPEC-TOO-STRONG).
  * nagini `echo-attempt-honest` -> `pos-echo-spec-model`. An earlier revision of
    this manifest recorded the echo class as having "no counterpart (nothing to
    echo)". That was WRONG and is corrected here: the echo IS expressible on this
    carrier, because `escapeSeq` is a spec-view `def` the impl region may name, so
    `implementation_escape s := escapeSeq s` is writable and (built, exit 0)
    verifies by `rfl`. What differs from nagini is only the VERDICT class, not the
    expressibility: nagini's @Pure `escaped_seq` has no executable
    materialization into a `list_pred` list, so there the echo could not even be
    written; here it can, and it is CORRECT rather than a cheat. That is the
    honest shape of the argument the old note gestured at — the pin is grounded
    in the input, so echoing it reproduces the real per-code-point work
    (extensionally) instead of dodging it. It is carried as an expect="verify"
    soundness case: an echo that FAILED to verify would mean the spec rejects its
    own model (SPEC-TOO-STRONG); it is not evidence of echo-immunity, and this
    battery makes no such claim.
  * nagini `rival-apos-decimal` -> `rival-apos-decimal` — emits the legacy
    decimal apostrophe entity at every position (the exact pre-patch behaviour);
    attacks the substitution table.
  * nagini `partial-domain-apos-first` -> `partial-domain-apos-first` — correct
    everywhere except a leading apostrophe; attacks domain completeness.
  * nagini `rival-drop-quot` -> `rival-drop-quot` — double-quote passes through.
  * added `rival-drop-amp` — ampersand passes through. (An earlier revision
    called the ampersand "the one significant character no ported rival otherwise
    touches". That was wrong: `<` and `>` were untouched by every rival AND every
    witness too — the audit measured it. Corrected by `rival-swap-lt-gt` below, so
    that all five table entries are now probed.)
  * added `rival-swap-lt-gt` — transposes the angle-bracket entries (`<` emits the
    gt entity and `>` emits the lt entity). Closes the coverage gap just named:
    without it a rival confusing exactly those two entries satisfied every case in
    the battery, since no shipped witness mentioned either character. Chosen as a
    TRANSPOSITION rather than a drop so it also survives any check keyed on output
    length — the wrong output is the same length as the right one.
  * added `rival-over-escape-bang` — attacks the IDENTITY ARM of the table (every
    non-significant code point maps to itself) by entity-encoding an ordinary
    character. Landed by a later independent audit, which measured that every
    shipped rival and every shipped witness moved only code points INSIDE the
    five-entry significant set: the whole battery was an under-escaping battery,
    so a rival that escaped MORE than the five was unattacked. Its refinement is
    F2P-grounded rather than hypothetical — the suite asserts the punctuation run
    `!$&...()*+,;=~:@,` passes through with only the `&` and `'` rewritten, so a
    patch entity-encoding `!` fails it.
  * added `rival-order-reversed` — attacks the concatenation ORDER (a purely
    structural clause independent of the table), a class nagini did not need
    because its sequence pin was over a PSeq; here it is the transparent
    ordering of the fold.
  * nagini `frame-mutate-text` (fractional-permission frame mutation) is
    VACUOUS on this carrier, and a later audit MEASURED that rather than asserting
    it. What the nagini case tests is whether the read-only 1/2 permission can be
    subverted, so that the pin is satisfied against a SELF-MUTATED input; the
    rejection there comes from the permission system, not from a value mismatch.
    There is no permission system here and no aliased write: `s` is an immutable
    value. The audit wrote the closest expressible analogue — an impl that takes a
    mutable LOCAL copy of `s`, overwrites it, and escapes the copy — and confirmed
    it collapses into an ordinary VALUE rival: it does not verify (exit 1) and its
    witness at `['&']` refutes it (rival exit 0, gold exit 1) exactly like every
    other wrong-value rival, because the spec keeps speaking of the original `s`.
    So the class is not merely hard here, it carries NO information the value
    rivals do not already carry, and no substitute is fabricated.
  * nagini `admiss-significant-input` -> `admiss-f2p-significant`. An earlier
    revision recorded this class as OMITTED because "the lean obligation has NO
    precondition hypothesis, so there is nothing to over/under-constrain". A third
    audit measured that reason to be WRONG, and landed the case. The analogue on a
    total carrier is not a precondition to weaken but the obligation being
    UNSATISFIABLE at exactly an F2P-shaped input, which a positive that discharges
    the pin at that concrete input tests directly. The case prepends, to the frozen
    tactic body, a ground `have` closing `problem_spec_escape p (implementation_escape p)`
    at the F2P-shaped significant-character input `p = ['\\'', '"', '<', '&', '>', 'a']`
    BY EVALUATION (`decide`), then closes the frozen obligation verbatim. Built:
    exit 0. Nothing is assumed — no new declaration, no axiom, the statement stays
    byte-identical, and the ground instance is a `have` inside the existing proof
    region. Had it failed, the modeled behaviour would be unsatisfiable at a normal
    F2P input, which is this carrier's PRECOND-TOO-STRONG.
  * divergence/non-termination lane: nothing to ship. The reason is TOTALITY, not
    referential transparency: `implementation_escape` is a total Lean `def`, and a
    non-terminating body is rejected by the equation compiler rather than admitted
    vacuously. The known spec hole in this class (`the corpus-wide termination-semantics finding`) is
    scoped to the 401 velvet bundles carrying
    `set_option loom.semantics.termination "partial"`; lean is measured unaffected
    there, so there is no hole to re-report here.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it.

Every reject case carries a `witness`: a Lean snippet negating the spec
predicate at one concrete input, checked in a file with the frozen obligation
removed. Each must (1) ELABORATE against the rival and (2) FAIL against the
frozen solution (a real discriminator, not a tautology). All witnesses below
were built BOTH ways with scripts/lean_verify.sh (rival exit 0, gold exit 1);
each gold build fails with ``Tactic `decide` proved that the proposition ¬(...) =
escapeSeq [...] is false`` — a SEMANTIC refutation of the concrete claim (gold
satisfies the spec at that input), never a missing identifier, type error, or
unfolding failure, which would make the gold-side failure worthless as evidence.
No witness binds a hypothesis (every one states its refutation at literal
inputs), so no consistency probe is reachable and the inconsistent-hypothesis
forgery has no foothold here.

Independently re-derived by adversarial audit: all witness pairs rebuilt (5+1
rivals, rival 0 / gold 1, gold-side failure text confirmed semantic in each
case); six NEW wrong impls beyond this battery tried against the frozen spec
(swapped angle brackets, dropped `<`, an already-encoded-input guard,
escape-first-only, doubled output, dropped last code point) — ALL rejected, so no
spec hole was found in the too-weak direction; four NEW correct reshapes tried
(map-then-flatten, reverse-then-left-fold, a tail-recursive accumulator with an
impl-region helper `def`, and the spec-model echo) — ALL verified, so none was
rejected and no hole was found in the too-strong direction either. The audit
landed two of its probes as permanent cases (`pos-echo-spec-model`,
`rival-swap-lt-gt`) and corrected three prose claims it measured to be false.

A SECOND independent audit re-ran the whole battery from the frozen file rather
than trusting the record above. Statement integrity: the `theorem correct_escape`
statement extracted from all cases is BYTE-IDENTICAL to the frozen one (no case
reformats or weakens it), and each variant's diff against `Solution.lean` touches
only the impl region plus, for the positives, the proof body. All six shipped
witnesses rebuilt both ways: rival exit 0, gold exit 1 in every case, and every
gold-side log is ``Tactic `decide` proved that the proposition ¬(...) = escapeSeq
[...] is false`` — a semantic refutation, never an unknown identifier, a type
error, or a stuck reduction (no `did not reduce to isTrue or isFalse` appears on
any side). No witness binds a binder, so `consistency_probe` is None for all six
and the inconsistent-hypothesis forgery is unreachable by construction rather
than by luck. Four MORE wrong impls were tried (over-escaping an ordinary
character; the UPPERCASE-hex apostrophe `&#X27;` [sic], a one-character near-miss on
the very entity this task turns on; a length-conditioned sub-domain correct only
for inputs of length <= 3; and the quot/apos table entries transposed) — all four
were REJECTED and all four witnesses discriminated, so no spec hole in the
too-weak direction. Three MORE correct reshapes were tried (a left fold with
`acc ++ escapeChar c`, `(s.map escapeChar).flatten`, and a tail-recursive
`escapeGo` accumulator declared as an impl-region helper) — all three VERIFIED,
so no hole in the too-strong direction. The deep model itself was re-validated
against the real stdlib escaper outside Lean: 200,000 fuzzed strings over the
five significant characters plus ordinary/astral code points, plus an exhaustive
single-code-point sweep of 0..0x3000, 0 mismatches. The one real defect it found
was a COVERAGE gap, now closed as `rival-over-escape-bang`: every shipped rival
and witness moved only code points inside the five-entry significant set, so the
battery attacked the table's entity arm from one side only and an OVER-escaping
rival satisfied all nine cases. It also re-derived the frame-mutation omission by
building it rather than arguing it (see that bullet above).

A THIRD independent adversarial audit re-derived every case from the frozen file
and found TWO real defects, both now fixed here. Statement integrity re-confirmed:
the `theorem correct_escape` statement extracted from all cases is BYTE-IDENTICAL
to the frozen one. All seven then-shipped witnesses rebuilt both ways (rival exit
0, gold exit 1 in every case). It also ran the FORGERY test on all seven, which the
two prior audits did not: for each witness it built a second file differing ONLY in
what it claims (the `¬` dropped, so the claim becomes "gold SATISFIES the spec
here") against the frozen solution. Every flipped claim built at exit 0 against
gold and exit 1 against its rival — the exact inverse of the witness pair. So each
gold-side exit code demonstrably TRACKS the claim rather than being a fixed
syntactic failure, which is what makes `decide`'s refutation admissible evidence.

The two defects:
  (1) the ADMISSIBILITY lane was absent, recorded as "vacuous because the
      obligation has no precondition" — a reason that does not survive contact with
      the carrier. Fixed by landing `admiss-f2p-significant` (built, exit 0); see
      that bullet above.
  (2) the `[]` point of the `s` binder was pinned by NO case: every rival and every
      witness stated its claim at a non-empty input, so a rival wrong only at the
      empty input satisfied the whole battery. Measured by building exactly that
      rival. Fixed by landing `rival-empty-nonempty` (rival exit 0, gold exit 1).

Six MORE wrong impls were tried against the frozen spec and ALL were REJECTED with
discriminating witnesses: the empty-input rival above; double-escaping the
ampersand's own entity (`&amp;amp;`, the idempotency arm); collapsing adjacent
duplicate code points; padding one extra code point onto the tail; the apostrophe
correct only on singleton inputs (an inverse partial domain); and dropping
non-BMP code points (witness at `Char.ofNat 0x1F600` — note a literal `'\\u{...}'`
is not valid Lean syntax and must be written this way). Three MORE correct reshapes
were tried and ALL VERIFIED: `(s.map escapeChar).flatten`; a left fold accumulating
REVERSED segments then reversing once at the end (proved via a generalized-over-the
-accumulator helper `have`); and direct structural recursion on the impl itself. So
neither direction shows a spec hole, and no finding was escalated against the
frozen artifact.
"""
from pathlib import Path

INSTANCE = "django__django-11276"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE the impl region of Solution.lean).
# ---------------------------------------------------------------------------

# The whole gold impl body (Id.run do accumulating loop), unique in the file.
_GOLD_IMPL = (
    "def implementation_escape (s : List Char) : List Char := Id.run do\n"
    "  let mut acc : List Char := []\n"
    "  for c in s do\n"
    "    acc := acc ++ escapeChar c\n"
    "  return acc"
)

_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"


def _swap_proof(src: str, new_proof_body: str) -> str:
    """Replace everything strictly between the proof markers with
    `new_proof_body`. The `theorem correct_escape` STATEMENT is re-emitted
    byte-identically inside `new_proof_body`; only the tactic body (and the
    dropped helper lemma) change, which variant_scope permits."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_proof_body + "\n" + src[e:]


# The theorem statement, re-emitted verbatim so the obligation survives.
_THM_STMT = (
    "theorem correct_escape :\n"
    "    ∀ (s : List Char),\n"
    "      problem_spec_escape s (implementation_escape s) := by"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-flatmap-form) A structurally-different but CORRECT impl: the pure
# functional `List.flatMap escapeChar` (no imperative do-block / for / mut).
# Its proof closes by induction over the list (`List.flatMap_cons`), mirroring
# `escapeSeq`'s own recursion. If it fails to verify the spec is over-fit to
# the accumulating-loop shape => SPEC-TOO-STRONG.
_POS_FLATMAP_IMPL = (
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  s.flatMap escapeChar"
)
_POS_FLATMAP_PROOF = (
    _THM_STMT + "\n"
    "  intro s\n"
    "  unfold problem_spec_escape implementation_escape\n"
    "  induction s with\n"
    "  | nil => rfl\n"
    "  | cons c cs ih => simp [List.flatMap_cons, escapeSeq, ih]\n"
)
_POS_FLATMAP = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_FLATMAP_IMPL),
    _POS_FLATMAP_PROOF,
)

# (pos-foldr-form) A second correct impl in a different shape: a right fold that
# prepends each per-code-point encoding. Semantically identical, different
# source; the proof case-splits by induction (`List.foldr_cons`). If it fails to
# verify the spec is over-fit to one fold direction => SPEC-TOO-STRONG.
_POS_FOLDR_IMPL = (
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  s.foldr (fun c acc => escapeChar c ++ acc) []"
)
_POS_FOLDR_PROOF = (
    _THM_STMT + "\n"
    "  intro s\n"
    "  unfold problem_spec_escape implementation_escape\n"
    "  induction s with\n"
    "  | nil => rfl\n"
    "  | cons c cs ih => simp [List.foldr_cons, escapeSeq, ih]\n"
)
_POS_FOLDR = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_FOLDR_IMPL),
    _POS_FOLDR_PROOF,
)

# (pos-echo-spec-model) The ECHO shape: the impl names the spec-view model
# directly. This is the counterpart of nagini's `echo-attempt-honest`, and on this
# carrier it is WRITABLE (`escapeSeq` is a spec-view `def`, so the impl region may
# call it) and CORRECT — so it is a positive control, not a cheat to be rejected.
# It is the limiting case of "a different impl shape": the shape with no work in
# it at all. If it failed to verify, the spec would be rejecting its own model
# (SPEC-TOO-STRONG). Note what this case does NOT show: it is not evidence that
# the spec resists echoing, because here echoing is simply correct.
_POS_ECHO_IMPL = (
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  escapeSeq s"
)
_POS_ECHO_PROOF = (
    _THM_STMT + "\n"
    "  intro s\n"
    "  unfold problem_spec_escape implementation_escape\n"
    "  rfl\n"
)
_POS_ECHO = _swap_proof(
    _swap(_BASE, _GOLD_IMPL, _POS_ECHO_IMPL),
    _POS_ECHO_PROOF,
)

# (admiss-f2p-significant) ADMISSIBILITY. On a total carrier the frozen obligation
# carries no precondition to over-constrain, so the analogue of PRECOND-TOO-STRONG
# is the obligation being UNSATISFIABLE at exactly an F2P-shaped input. This case
# discharges the pin at one such concrete input BY EVALUATION as a ground `have`
# prepended to the frozen tactic body, then closes the frozen obligation verbatim
# and unchanged. The probe input is the F2P-shaped run of all five significant
# code points plus an ordinary one, so the ground instance exercises every table
# entry AND the identity arm at once. Nothing is assumed: no new declaration, no
# axiom, statement byte-identical, gold proof steps untouched below the `have`.
_ADMISS_PROBE = "['\\'', '\"', '<', '&', '>', 'a']"
_GOLD_PROOF_INTRO = (
    "  intro s\n"
    "  unfold problem_spec_escape implementation_escape\n"
    "  have h := forIn_escape_helper s []"
)
_ADMISS_HAVE = (
    "  intro s\n"
    f"  have _ground : problem_spec_escape {_ADMISS_PROBE}\n"
    f"      (implementation_escape {_ADMISS_PROBE}) := by\n"
    "    unfold problem_spec_escape implementation_escape\n"
    "    decide\n"
    "  unfold problem_spec_escape implementation_escape\n"
    "  have h := forIn_escape_helper s []"
)
_ADMISS = _swap(_BASE, _GOLD_PROOF_INTRO, _ADMISS_HAVE)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================
# Each rival reshapes ONLY the impl body; the gold proof body is kept verbatim
# (it fails to build against the reshaped impl — the default outcome of any
# reshape — which is why the reject verdict alone is not evidence, and each case
# carries a `witness` that has been SEEN to discriminate).

# (rival-apos-decimal) Emit the legacy decimal apostrophe entity `&#39;` at
# every position — the exact pre-patch behaviour the fix replaces with `&#x27;`.
_RIVAL_APOS = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  s.flatMap (fun c => if c = '\\'' then \"&#39;\".toList else escapeChar c)",
)

# (rival-drop-quot) Let the double-quote pass through unescaped.
_RIVAL_QUOT = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  s.flatMap (fun c => if c = '\"' then [c] else escapeChar c)",
)

# (rival-drop-amp) Let the ampersand pass through unescaped.
_RIVAL_AMP = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  s.flatMap (fun c => if c = '&' then [c] else escapeChar c)",
)

# (partial-domain-apos-first) Escape the apostrophe correctly (`&#x27;`)
# EVERYWHERE except when it is the FIRST code point of the input, where it emits
# legacy `&#39;`. Correct on every other input; the divergence is confined to
# inputs beginning with an apostrophe.
_RIVAL_PARTIAL = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  match s with\n"
    "  | [] => []\n"
    "  | c :: cs =>\n"
    "    (if c = '\\'' then \"&#39;\".toList else escapeChar c) ++ cs.flatMap escapeChar",
)

# (rival-swap-lt-gt) TRANSPOSE the two angle-bracket table entries: `<` emits the
# gt entity and `>` emits the lt entity. Both characters are still escaped, and
# the output length is IDENTICAL to gold's on every input, so only the identity of
# the substituted entity is wrong. Closes the audited coverage gap: before this
# case no rival and no witness mentioned either angle bracket.
_RIVAL_LTGT = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  s.flatMap (fun c => if c = '<' then \"&gt;\".toList\n"
    "    else if c = '>' then \"&lt;\".toList else escapeChar c)",
)

# (rival-over-escape-bang) OVER-escape: entity-encode an ordinary character
# (`!`) that the table leaves alone. Every other rival in this battery moves a
# code point INSIDE the five-entry significant set, so all of them attack the
# table's ENTITY arm; this one attacks its IDENTITY arm ("every other character
# maps to itself"), which is a separate half of the same clause and was
# unprobed. Note the direction: the output is LONGER than gold's here, where the
# drop rivals are shorter, so it also exercises the length pin upward.
_RIVAL_BANG = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  s.flatMap (fun c => if c = '!' then \"&#x21;\".toList else escapeChar c)",
)

# (rival-empty-nonempty) Return a NON-EMPTY output for the EMPTY input, and behave
# exactly like gold everywhere else. Attacks the `[]` boundary of the clause (the
# `escapeSeq [] = []` base case): every other rival and every other witness in this
# battery states its claim at a NON-EMPTY input, so the empty-list point of the `s`
# binder was pinned by no case here — a rival wrong only at `[]` satisfied all of
# them. This is a genuinely different sub-domain rather than a second spelling of an
# existing one, which is what the coverage reporter's "binder varies" needs to mean.
_RIVAL_EMPTY = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  match s with\n"
    "  | [] => ['x']\n"
    "  | cs => cs.flatMap escapeChar",
)

# (rival-order-reversed) Fold in REVERSE, prepending each encoding, so the
# per-code-point segments appear in reversed order. Correct segment CONTENTS,
# wrong concatenation ORDER.
_RIVAL_ORDER = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_escape (s : List Char) : List Char :=\n"
    "  s.foldl (fun acc c => escapeChar c ++ acc) []",
)


# --- witnesses (checked with the obligation removed) -----------------------
# Each negates the spec predicate at one concrete input; the carrier is
# transparent, so `decide` closes and no witness binds a hypothesis.

def _wit(input_list: str) -> str:
    return (
        f"example : ¬ problem_spec_escape {input_list} "
        f"(implementation_escape {input_list}) := by\n"
        "  unfold problem_spec_escape implementation_escape\n"
        "  decide"
    )


# leading (and only) apostrophe: gold => &#x27;, rival => &#39;.
_WIT_APOS = _wit("['\\'']")
# a bare double-quote: gold => &quot;, rival passes it through.
_WIT_QUOT = _wit("['\"']")
# a bare ampersand: gold => &amp;, rival passes it through.
_WIT_AMP = _wit("['&']")
# a bare `<`: gold => the lt entity, the transposing rival => the gt entity. Same
# length on both sides, so this discriminates on entity IDENTITY alone, and it is
# the first witness in the battery to mention an angle bracket at all.
_WIT_LTGT = _wit("['<']")
# a bare `!`: gold leaves it ALONE, the over-escaping rival emits an entity for
# it. The first witness in the battery to sit OUTSIDE the five significant code
# points, and the only one whose rival output is longer than gold's.
_WIT_BANG = _wit("['!']")
# TWO apostrophes: the leading one is the divergence, so this varies the `s`
# binder (length 2, leading-apostrophe sub-domain): gold => &#x27;&#x27;, the
# rival emits &#39; only for the FIRST => the sequences differ at index 0.
_WIT_PARTIAL = _wit("['\\'', '\\'']")
# the EMPTY input: gold => [], the rival => a one-character output. The only
# witness in the battery at the `[]` point of the `s` binder, and the only one whose
# gold side is the empty list.
_WIT_EMPTY = _wit("[]")
# two ordinary distinct code points: gold => ['a','b'], the reversed fold =>
# ['b','a'] — same multiset, wrong order. Varies `s` to a length-2 all-ordinary
# input, isolating the ORDER clause from the substitution table.
_WIT_ORDER = _wit("['a', 'b']")


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-flatmap-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FLATMAP,
     "rationale": "a structurally-different but correct impl: the pure functional "
                  "`List.flatMap escapeChar` (no imperative do-block / for / mut) whose "
                  "proof re-closes by induction (`List.flatMap_cons`), mirroring "
                  "escapeSeq's recursion. The carrier is transparent, so there is no "
                  "oracle to echo; this stands purely as a soundness positive of a "
                  "different impl form. If it fails to verify the spec is over-fit to the "
                  "accumulating-loop shape => SPEC-TOO-STRONG."},
    {"id": "pos-foldr-form", "kind": "soundness", "expect": "verify",
     "module": _POS_FOLDR,
     "rationale": "a second correct impl in a different shape: a right fold "
                  "(`List.foldr`, prepend each encoding). Semantically identical; the "
                  "equality clause is agnostic to fold direction. Proof re-closed by "
                  "induction (`List.foldr_cons`). If it fails to verify the spec is "
                  "over-fit to one fold shape => SPEC-TOO-STRONG."},
    {"id": "pos-echo-spec-model", "kind": "soundness", "expect": "verify",
     "module": _POS_ECHO,
     "rationale": "the ECHO shape, and the counterpart of nagini's "
                  "`echo-attempt-honest`: the impl names the spec-view model "
                  "(`escapeSeq s`) directly. Unlike nagini — where the @Pure oracle has "
                  "no executable materialization into a list_pred list, so this could "
                  "not be written — it IS writable here, and it is CORRECT, hence a "
                  "positive control rather than a rival. It is the limiting 'different "
                  "shape': the one with no work in it. If it failed to verify the spec "
                  "would be rejecting its own model => SPEC-TOO-STRONG. It is NOT "
                  "evidence of echo-resistance: on this carrier echoing a pin that is "
                  "grounded in the input just IS computing the answer."},

    {"id": "admiss-f2p-significant", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "ADMISSIBILITY, ported from nagini's `admiss-significant-input`. The "
                  "frozen obligation is total (`∀ s`, no precondition), so the analogue of "
                  "PRECOND-TOO-STRONG here is not a hypothesis to weaken but the pin being "
                  "UNSATISFIABLE at an F2P-shaped input. This discharges "
                  "`problem_spec_escape p (implementation_escape p)` at the concrete "
                  "F2P-shaped input p = all five significant code points plus an ordinary "
                  "one, BY EVALUATION (`decide`) as a ground `have`, and only then closes "
                  "the frozen obligation verbatim. Verifies (exit 0). If it FAILED, the "
                  "modeled behaviour would be unsatisfiable at exactly a normal F2P input. "
                  "Nothing is assumed: no new declaration, no axiom, the statement is "
                  "byte-identical and the gold tactic steps are untouched below the `have`. "
                  "An earlier revision recorded this lane as vacuous because the obligation "
                  "has no precondition; an audit measured that reason wrong and landed this."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-apos-decimal", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_APOS, "witness": _WIT_APOS,
     "refinement": "emits the legacy decimal apostrophe entity at every position — the "
                   "exact pre-patch behaviour; its faithful real patch is the pre-patch "
                   "escaper, which FAILS the F2P test that pins the apostrophe to the hex "
                   "entity (the single behavioural change of this task, asserted at every "
                   "position across the F2P suite), so it would NOT resolve.",
     "rationale": "attacks the SUBSTITUTION TABLE (the apostrophe entry). Witness at a "
                  "single apostrophe: gold => the hex entity, rival => the decimal "
                  "entity, so the sequences differ. Built both ways (rival exit 0, gold "
                  "exit 1 inside `decide`)."},
    {"id": "partial-domain-apos-first", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL, "witness": _WIT_PARTIAL,
     "refinement": "escapes the apostrophe correctly EVERYWHERE except when it is the "
                   "first code point, where it emits the legacy decimal entity. A "
                   "faithful real patch of this shape (special-casing position 0) would "
                   "still emit the wrong entity for any input beginning with an "
                   "apostrophe and so FAIL the F2P tests, which pin the apostrophe at "
                   "every position — it would NOT resolve.",
     "rationale": "attacks DOMAIN COMPLETENESS: the clause pins the WHOLE sequence "
                  "including index 0. Witness at TWO apostrophes (varies `s` to length 2, "
                  "leading-apostrophe sub-domain): gold => two hex entities, the rival "
                  "emits the decimal entity for the first only, so the sequences differ "
                  "at index 0. Built both ways (rival 0, gold 1 inside `decide`)."},
    {"id": "rival-drop-quot", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_QUOT, "witness": _WIT_QUOT,
     "refinement": "lets the double-quote pass through unescaped; a real patch doing "
                   "this would emit unsafe attribute markup and FAIL the F2P test that "
                   "pins the double-quote to its entity — it would NOT resolve.",
     "rationale": "attacks the SUBSTITUTION TABLE (the double-quote entry). Witness at a "
                  "bare double-quote: gold => the quot entity, rival => the bare "
                  "character. Built both ways (rival 0, gold 1 inside `decide`)."},
    {"id": "rival-drop-amp", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_AMP, "witness": _WIT_AMP,
     "refinement": "lets the ampersand pass through unescaped; a real patch doing this "
                   "would emit invalid/unsafe markup and FAIL the F2P tests that pin the "
                   "ampersand to its entity — it would NOT resolve.",
     "rationale": "attacks the SUBSTITUTION TABLE (the ampersand entry), the entry that "
                  "carries the most weight in real markup since it is the one the encoder "
                  "must rewrite FIRST for the whole-string replacement chain to agree with "
                  "the per-code-point map. Witness at a bare "
                  "ampersand: gold => the amp entity, rival => the bare character. Built "
                  "both ways (rival 0, gold 1 inside `decide`)."},
    {"id": "rival-swap-lt-gt", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_LTGT, "witness": _WIT_LTGT,
     "refinement": "transposes the two angle-bracket entries, so `<` renders as the gt "
                   "entity and `>` as the lt entity. A real patch doing this would emit "
                   "markup whose angle brackets decode back swapped, and it would FAIL "
                   "the F2P tests that pin each angle bracket to its own entity "
                   "(asserted for both characters, including inside the wrapping-character "
                   "and urlize cases) — it would NOT resolve.",
     "rationale": "attacks the SUBSTITUTION TABLE at the two entries the rest of the "
                  "battery left completely unprobed: before this case no rival and no "
                  "witness mentioned `<` or `>`, so a rival confusing exactly those two "
                  "satisfied every case here. A TRANSPOSITION rather than a drop, so the "
                  "output length matches gold on every input and only entity identity is "
                  "wrong. Witness at a bare `<` (rival exit 0; gold exit 1, `decide` "
                  "proving the negation false)."},
    {"id": "rival-over-escape-bang", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BANG, "witness": _WIT_BANG,
     "refinement": "entity-encodes an ordinary punctuation character that must pass "
                   "through untouched. A real patch doing this would corrupt every "
                   "ordinary character it named, and it FAILS the F2P tests directly: the "
                   "suite asserts a punctuation run (`!$&...()*+,;=~:@,`) survives with "
                   "ONLY the ampersand and the apostrophe rewritten, so an emitted entity "
                   "for `!` is a literal string mismatch there — it would NOT resolve.",
     "rationale": "attacks the IDENTITY ARM of the substitution table: the clause says "
                  "every code point OUTSIDE the five significant ones maps to ITSELF, so "
                  "OVER-escaping is as wrong as under-escaping. Every other rival here "
                  "moves a code point inside the significant set, which left this half of "
                  "the clause unprobed — a rival that escaped MORE than the five satisfied "
                  "the whole battery. Witness at a bare `!`: the first witness outside the "
                  "five, and the only one whose rival output is LONGER than gold's, so it "
                  "also pins length upward. Built both ways (rival exit 0; gold exit 1, "
                  "`decide` proving the negation false)."},
    {"id": "rival-empty-nonempty", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EMPTY, "witness": _WIT_EMPTY,
     "refinement": "emits a spurious one-character output for empty input while behaving "
                   "exactly like gold on every non-empty input. A real patch of this shape "
                   "would inject a stray character into every empty-text render and FAIL "
                   "the F2P assertions that escaping empty/absent text yields empty output "
                   "— it would NOT resolve.",
     "rationale": "attacks the `[]` BOUNDARY of the clause (`escapeSeq [] = []`). Every "
                  "other case in this battery states its claim at a NON-EMPTY input, so the "
                  "empty point of the `s` binder was pinned by no rival and no witness: a "
                  "rival wrong ONLY at `[]` satisfied the entire battery. Witness at `[]` "
                  "(rival exit 0; gold exit 1, `decide` proving the negation false), the "
                  "only witness here whose gold side is the empty list."},
    {"id": "rival-order-reversed", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ORDER, "witness": _WIT_ORDER,
     "refinement": "reverses the concatenation order of the per-code-point encodings; a "
                   "real patch doing this would emit the escaped text backwards and FAIL "
                   "every F2P test (all of which assert forward-ordered output) — it "
                   "would NOT resolve.",
     "rationale": "attacks the CONCATENATION ORDER, a purely structural clause "
                  "independent of the substitution table. Witness at two ordinary "
                  "distinct code points (isolates order from the table): gold => in "
                  "order, the reversed fold => reversed, so the sequences differ. Built "
                  "both ways (rival 0, gold 1 inside `decide`)."},
]
